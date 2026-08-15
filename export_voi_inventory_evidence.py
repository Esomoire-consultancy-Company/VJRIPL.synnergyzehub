from __future__ import annotations

import argparse
import json
from pathlib import Path

from voi_evidence_adapter import build_inventory_evidence_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only VOI inventory evidence bundle from ERP/OMS CSV exports.")
    parser.add_argument("--inventory", required=True, help="Inventory CSV: sku,available_qty,observed_at")
    parser.add_argument("--sales", required=True, help="Sales CSV: sku,units_sold,sales_date")
    parser.add_argument("--product-master", required=True, help="Product CSV: sku,unit_cost,lead_time_days[,campaign_uplift_pct]")
    parser.add_argument("--open-orders", help="Optional open orders CSV: sku,inbound_qty,expected_date")
    parser.add_argument("--demand-window-days", type=int, default=14)
    parser.add_argument("--out", required=True, help="Destination JSON file")
    args = parser.parse_args()

    bundle = build_inventory_evidence_bundle(
        args.inventory,
        args.sales,
        args.product_master,
        args.open_orders,
        demand_window_days=args.demand_window_days,
    )
    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {bundle['contract']} {bundle['bundleId']} with {len(bundle['snapshots'])} snapshots to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
