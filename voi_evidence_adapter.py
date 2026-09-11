from __future__ import annotations

from pathlib import Path

from evidence_core import (
    EvidenceValidationError,
    SourceFileEvidence,
    canonical_json,
    parse_date,
    parse_datetime,
    parse_float,
    parse_int,
    read_csv,
    require_columns,
    sha256_text,
)


def _voi_evidence_ref(item: SourceFileEvidence) -> str:
    return f"evidence:voi-export:{item.source_name}:{item.sha256}"


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

    inventory_rows, inventory_evidence, inventory_headers = read_csv(
        inventory_path, "inventory"
    )
    sales_rows, sales_evidence, sales_headers = read_csv(sales_path, "sales")
    product_rows, product_evidence, product_headers = read_csv(
        product_path, "product_master"
    )
    order_rows: list[dict[str, str]] = []
    order_headers: list[str] = []
    order_evidence: SourceFileEvidence | None = None
    if orders_path:
        order_rows, order_evidence, order_headers = read_csv(
            orders_path, "open_orders"
        )

    require_columns(
        inventory_rows,
        inventory_headers,
        ["sku", "available_qty", "observed_at"],
        "inventory",
    )
    require_columns(
        sales_rows,
        sales_headers,
        ["sku", "units_sold", "sales_date"],
        "sales",
    )
    require_columns(
        product_rows,
        product_headers,
        ["sku", "unit_cost", "lead_time_days"],
        "product_master",
    )
    if orders_path:
        require_columns(
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
            "unitCost": parse_float(
                row["unit_cost"],
                f"product_master[{sku}].unit_cost",
                minimum=0,
            ),
            "leadTimeDays": parse_int(
                row["lead_time_days"],
                f"product_master[{sku}].lead_time_days",
                minimum=1,
            ),
            "campaignUpliftPct": parse_float(
                row.get("campaign_uplift_pct", "0") or "0",
                f"product_master[{sku}].campaign_uplift_pct",
                minimum=0,
            ),
        }

    observed_times = [
        parse_datetime(row["observed_at"], f"inventory[{idx}].observed_at")
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
            raise EvidenceValidationError(
                f"inventory sku not found in product_master: {sku}"
            )
        qty = parse_float(
            row["available_qty"],
            f"inventory[{idx}].available_qty",
            minimum=0,
        )
        available_by_sku[sku] = available_by_sku.get(sku, 0.0) + qty

    window_start = observed_at.date().toordinal() - demand_window_days + 1
    sold_by_sku: dict[str, float] = {sku: 0.0 for sku in available_by_sku}
    for idx, row in enumerate(sales_rows):
        sku = row["sku"]
        if sku not in product_by_sku:
            raise EvidenceValidationError(
                f"sales sku not found in product_master: {sku}"
            )
        units = parse_float(
            row["units_sold"],
            f"sales[{idx}].units_sold",
            minimum=0,
        )
        sale_date = parse_date(row["sales_date"], f"sales[{idx}].sales_date")
        if sale_date.date() > observed_at.date():
            raise EvidenceValidationError(
                f"sales[{idx}].sales_date is after inventory observation time"
            )
        if sale_date.date().toordinal() >= window_start:
            sold_by_sku[sku] = sold_by_sku.get(sku, 0.0) + units

    inbound_by_sku: dict[str, float] = {sku: 0.0 for sku in available_by_sku}
    warnings: list[str] = []
    for idx, row in enumerate(order_rows):
        sku = row["sku"]
        if sku not in product_by_sku:
            raise EvidenceValidationError(
                f"open_orders sku not found in product_master: {sku}"
            )
        qty = parse_float(
            row["inbound_qty"],
            f"open_orders[{idx}].inbound_qty",
            minimum=0,
        )
        expected = parse_date(
            row["expected_date"],
            f"open_orders[{idx}].expected_date",
        )
        if expected.date() < observed_at.date():
            warnings.append(
                f"overdue open order excluded from confirmed inbound: sku={sku} expected_date={row['expected_date']}"
            )
            continue
        inbound_by_sku[sku] = inbound_by_sku.get(sku, 0.0) + qty

    evidence_items = [inventory_evidence, sales_evidence, product_evidence]
    if order_evidence:
        evidence_items.append(order_evidence)

    evidence_refs = [_voi_evidence_ref(item) for item in evidence_items]
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
                "evidenceRef": _voi_evidence_ref(item),
            }
            for item in evidence_items
        ],
        "warnings": warnings,
        "snapshots": snapshots,
    }
    canonical_payload = canonical_json(payload)
    digest = sha256_text(canonical_payload)
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
