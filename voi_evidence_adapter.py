from __future__ import annotations

import csv
import hashlib
import io
import json
import math
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
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceValidationError(f"{field} must be an ISO-8601 date or datetime: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_float(value: str, field: str, *, minimum: float | None = None) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} must be numeric: {value}") from exc
    if not math.isfinite(parsed):
        raise EvidenceValidationError(f"{field} must be finite: {value}")
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


def _read_csv(
    path: Path,
    source_name: str,
) -> tuple[list[dict[str, str]], SourceFileEvidence, list[str]]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise EvidenceValidationError(f"{source_name} has no header row")

    headers = [(header or "").strip() for header in reader.fieldnames]
    if any(not header for header in headers):
        raise EvidenceValidationError(f"{source_name} contains a blank column header")
    if len(set(headers)) != len(headers):
        raise EvidenceValidationError(f"{source_name} contains duplicate column headers")
    reader.fieldnames = headers

    rows: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise EvidenceValidationError(
                f"{source_name} row {row_number} contains more fields than the header"
            )
        normalized_row: dict[str, str] = {}
        for key, value in row.items():
            if isinstance(value, list):
                raise EvidenceValidationError(
                    f"{source_name} row {row_number} contains malformed extra fields"
                )
            normalized_row[key] = (value or "").strip()
        rows.append(normalized_row)

    return rows, SourceFileEvidence(source_name, path.name, digest, len(rows)), headers


def _require_columns(
    rows: list[dict[str, str]],
    headers: Iterable[str],
    columns: Iterable[str],
    source_name: str,
    *,
    allow_empty: bool = False,
) -> None:
    available = set(headers)
    missing = [column for column in columns if column not in available]
    if missing:
        raise EvidenceValidationError(f"{source_name} missing required columns: {', '.join(missing)}")
    if not rows and not allow_empty:
        raise EvidenceValidationError(f"{source_name} contains no data rows")


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

    inventory_rows, inventory_evidence, inventory_headers = _read_csv(inventory_path, "inventory")
    sales_rows, sales_evidence, sales_headers = _read_csv(sales_path, "sales")
    product_rows, product_evidence, product_headers = _read_csv(product_path, "product_master")
    order_rows: list[dict[str, str]] = []
    order_headers: list[str] = []
    order_evidence: SourceFileEvidence | None = None
    if orders_path:
        order_rows, order_evidence, order_headers = _read_csv(orders_path, "open_orders")

    _require_columns(
        inventory_rows,
        inventory_headers,
        ["sku", "available_qty", "observed_at"],
        "inventory",
    )
    _require_columns(
        sales_rows,
        sales_headers,
        ["sku", "units_sold", "sales_date"],
        "sales",
    )
    _require_columns(
        product_rows,
        product_headers,
        ["sku", "unit_cost", "lead_time_days"],
        "product_master",
    )
    if orders_path:
        _require_columns(
            order_rows,
            order_headers,
            ["sku", "inbound_qty", "expected_date"],
            "open_orders",
            allow_empty=True,
        )

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
    unique_observed_times = set(observed_times)
    if len(unique_observed_times) != 1:
        raise EvidenceValidationError(
            "inventory rows must share one observed_at timestamp; mixed snapshots cannot be summed"
        )
    observed_at = observed_times[0]

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
    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
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
