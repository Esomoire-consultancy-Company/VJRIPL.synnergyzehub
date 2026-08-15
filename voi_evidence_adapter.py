from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


class EvidenceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SourceFileEvidence:
    source_name: str
    path: str
    sha256: str
    row_count: int

    @property
    def evidence_ref(self) -> str:
        return f"evidence:voi-export:{self.source_name}:{self.sha256}"


def _parse_datetime(value: str, field: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise EvidenceValidationError(f"{field} is required")
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{field} must be ISO-8601: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_date(value: str, field: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise EvidenceValidationError(f"{field} is required")
    try:
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise EvidenceValidationError(f"{field} must be YYYY-MM-DD: {value}") from exc


def _parse_float(value: str, field: str, *, minimum: float | None = None) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} must be numeric: {value}") from exc
    if minimum is not None and parsed < minimum:
        raise EvidenceValidationError(f"{field} must be >= {minimum}: {value}")
    return parsed


def _parse_int(value: str, field: str, *, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} must be an integer: {value}") from exc
    if minimum is not None and parsed < minimum:
        raise EvidenceValidationError(f"{field} must be >= {minimum}: {value}")
    return parsed


def _read_csv(path: Path, source_name: str) -> tuple[list[dict[str, str]], SourceFileEvidence]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    if not reader.fieldnames:
        raise EvidenceValidationError(f"{source_name} has no header row")
    rows = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    return rows, SourceFileEvidence(source_name, str(path), digest, len(rows))


def _require_columns(rows: list[dict[str, str]], columns: Iterable[str], source_name: str) -> None:
    if not rows:
        raise EvidenceValidationError(f"{source_name} contains no data rows")
    available = set(rows[0])
    missing = [column for column in columns if column not in available]
    if missing:
        raise EvidenceValidationError(f"{source_name} missing required columns: {', '.join(missing)}")


def build_inventory_evidence_bundle(
    inventory_csv: str | Path,
    sales_csv: str | Path,
    product_master_csv: str | Path,
    open_orders_csv: str | Path | None = None,
    *,
    demand_window_days: int = 14,
) -> dict:
    """Convert read-only ERP/OMS exports into the VSR inventory evidence contract."""
    if demand_window_days <= 0:
        raise EvidenceValidationError("demand_window_days must be positive")

    inventory_path = Path(inventory_csv)
    sales_path = Path(sales_csv)
    product_path = Path(product_master_csv)
    orders_path = Path(open_orders_csv) if open_orders_csv else None

    inventory_rows, inventory_evidence = _read_csv(inventory_path, "inventory")
    sales_rows, sales_evidence = _read_csv(sales_path, "sales")
    product_rows, product_evidence = _read_csv(product_path, "product_master")
    order_rows: list[dict[str, str]] = []
    order_evidence: SourceFileEvidence | None = None
    if orders_path:
        order_rows, order_evidence = _read_csv(orders_path, "open_orders")

    _require_columns(inventory_rows, ["sku", "available_qty", "observed_at"], "inventory")
    _require_columns(sales_rows, ["sku", "units_sold", "sales_date"], "sales")
    _require_columns(product_rows, ["sku", "unit_cost", "lead_time_days"], "product_master")
    if order_rows:
        _require_columns(order_rows, ["sku", "inbound_qty", "expected_date"], "open_orders")

    product_by_sku: dict[str, dict] = {}
    for row in product_rows:
        sku = row["sku"]
        if not sku:
            raise EvidenceValidationError("product_master sku is required")
        if sku in product_by_sku:
            raise EvidenceValidationError(f"duplicate product_master sku: {sku}")
        product_by_sku[sku] = {
            "unitCost": _parse_float(row["unit_cost"], f"product_master[{sku}].unit_cost", minimum=0),
            "leadTimeDays": _parse_int(row["lead_time_days"], f"product_master[{sku}].lead_time_days", minimum=1),
            "campaignUpliftPct": _parse_float(
                row.get("campaign_uplift_pct", "0") or "0",
                f"product_master[{sku}].campaign_uplift_pct",
                minimum=0,
            ),
        }

    observed_times = [
        _parse_datetime(row["observed_at"], f"inventory[{idx}].observed_at")
        for idx, row in enumerate(inventory_rows)
    ]
    observed_at = max(observed_times)
    available_by_sku: dict[str, float] = {}
    for idx, row in enumerate(inventory_rows):
        sku = row["sku"]
        if sku not in product_by_sku:
            raise EvidenceValidationError(f"inventory sku not found in product_master: {sku}")
        qty = _parse_float(row["available_qty"], f"inventory[{idx}].available_qty", minimum=0)
        available_by_sku[sku] = available_by_sku.get(sku, 0.0) + qty

    window_start = observed_at.date().toordinal() - demand_window_days + 1
    sold_by_sku: dict[str, float] = {sku: 0.0 for sku in available_by_sku}
    for idx, row in enumerate(sales_rows):
        sku = row["sku"]
        if sku not in product_by_sku:
            raise EvidenceValidationError(f"sales sku not found in product_master: {sku}")
        units = _parse_float(row["units_sold"], f"sales[{idx}].units_sold", minimum=0)
        sale_date = _parse_date(row["sales_date"], f"sales[{idx}].sales_date")
        if sale_date.date() > observed_at.date():
            raise EvidenceValidationError(f"sales[{idx}].sales_date is after inventory observation time")
        if sale_date.date().toordinal() >= window_start:
            sold_by_sku[sku] = sold_by_sku.get(sku, 0.0) + units

    inbound_by_sku: dict[str, float] = {sku: 0.0 for sku in available_by_sku}
    warnings: list[str] = []
    for idx, row in enumerate(order_rows):
        sku = row["sku"]
        if sku not in product_by_sku:
            raise EvidenceValidationError(f"open_orders sku not found in product_master: {sku}")
        qty = _parse_float(row["inbound_qty"], f"open_orders[{idx}].inbound_qty", minimum=0)
        expected = _parse_date(row["expected_date"], f"open_orders[{idx}].expected_date")
        if expected.date() < observed_at.date():
            warnings.append(
                f"overdue open order excluded from confirmed inbound: sku={sku} expected_date={row['expected_date']}"
            )
            continue
        inbound_by_sku[sku] = inbound_by_sku.get(sku, 0.0) + qty

    evidence_items = [inventory_evidence, sales_evidence, product_evidence]
    if order_evidence:
        evidence_items.append(order_evidence)

    evidence_refs = [item.evidence_ref for item in evidence_items]
    snapshots = []
    for sku in sorted(available_by_sku):
        product = product_by_sku[sku]
        snapshots.append(
            {
                "sku": sku,
                "available": available_by_sku[sku],
                "avgDailyDemand": sold_by_sku.get(sku, 0.0) / demand_window_days,
                "confirmedInbound": inbound_by_sku.get(sku, 0.0),
                "leadTimeDays": product["leadTimeDays"],
                "unitCost": product["unitCost"],
                "campaignUpliftPct": product["campaignUpliftPct"],
                "observedAt": observed_at.isoformat().replace("+00:00", "Z"),
                "evidenceRefs": evidence_refs,
            }
        )

    payload = {
        "observedAt": observed_at.isoformat().replace("+00:00", "Z"),
        "demandWindowDays": demand_window_days,
        "sources": [
            {
                "name": item.source_name,
                "path": item.path,
                "sha256": item.sha256,
                "rowCount": item.row_count,
                "evidenceRef": item.evidence_ref,
            }
            for item in evidence_items
        ],
        "warnings": warnings,
        "snapshots": snapshots,
    }
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = f"sha256:{hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()}"
    return {
        "schemaVersion": "1.0.0",
        "contract": "VOI-INVENTORY-EVIDENCE-001",
        "sourceMode": "READ_ONLY_EXPORT",
        "payload": payload,
        "integrity": {
            "algorithm": "SHA-256",
            "digest": digest,
            "canonicalPayload": canonical_payload,
        },
        "bundleId": digest,
    }
