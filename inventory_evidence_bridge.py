from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from voi_evidence_adapter import EvidenceValidationError, build_inventory_evidence_bundle


TEMPLATES = {
    "inventory.csv": "sku,available_qty,observed_at\n",
    "sales.csv": "sku,units_sold,sales_date\n",
    "product_master.csv": "sku,unit_cost,lead_time_days,campaign_uplift_pct\n",
    "open_orders.csv": "sku,inbound_qty,expected_date\n",
}


def _persist_upload(root: Path, uploaded_file, source_slot: str) -> Path:
    safe_name = Path(uploaded_file.name).name
    if not safe_name.lower().endswith(".csv"):
        raise EvidenceValidationError(f"Only CSV exports are accepted: {safe_name}")
    destination = root / f"{source_slot}.csv"
    destination.write_bytes(uploaded_file.getvalue())
    return destination


def show_inventory_evidence_bridge():
    st.title("VOI Inventory Evidence Bridge")
    st.caption("Read-only LOGIC ERP / OMS export normalization for the Warden cognitive runtime")

    st.info(
        "This bridge does not connect with ERP credentials and cannot place orders, change inventory, or transfer funds. "
        "It converts operator-supplied CSV exports into an integrity-protected evidence bundle."
    )

    with st.expander("Source contract and blank templates", expanded=False):
        st.markdown("**VOI-LOGIC-EVIDENCE-PROFILE-001** uses report/export ingestion until a provider API contract and governed service principal are available.")
        st.code("inventory.csv: sku,available_qty,observed_at", language="text")
        st.code("sales.csv: sku,units_sold,sales_date", language="text")
        st.code("product_master.csv: sku,unit_cost,lead_time_days[,campaign_uplift_pct]", language="text")
        st.code("open_orders.csv (optional): sku,inbound_qty,expected_date", language="text")

        template_cols = st.columns(2)
        for index, (name, data) in enumerate(TEMPLATES.items()):
            with template_cols[index % 2]:
                st.download_button(
                    f"Download {name}",
                    data=data,
                    file_name=name,
                    mime="text/csv",
                    key=f"template_{name}",
                    use_container_width=True,
                )

    col1, col2 = st.columns(2)
    with col1:
        inventory_file = st.file_uploader("Inventory export", type=["csv"], key="voi_inventory_export")
        sales_file = st.file_uploader("Sales export", type=["csv"], key="voi_sales_export")
    with col2:
        product_file = st.file_uploader("Product master export", type=["csv"], key="voi_product_export")
        orders_file = st.file_uploader("Open orders export (optional)", type=["csv"], key="voi_orders_export")

    demand_window = st.number_input("Demand window (days)", min_value=1, max_value=90, value=14, step=1)

    ready = inventory_file is not None and sales_file is not None and product_file is not None
    if not ready:
        st.warning("Inventory, sales, and product master exports are required before an evidence bundle can be built.")
        return

    if not st.button("Build read-only evidence bundle", type="primary", use_container_width=True):
        return

    try:
        with tempfile.TemporaryDirectory(prefix="voi-evidence-") as tmp:
            root = Path(tmp)
            inventory_path = _persist_upload(root, inventory_file, "inventory")
            sales_path = _persist_upload(root, sales_file, "sales")
            product_path = _persist_upload(root, product_file, "product_master")
            orders_path = (
                _persist_upload(root, orders_file, "open_orders")
                if orders_file is not None
                else None
            )

            bundle = build_inventory_evidence_bundle(
                inventory_path,
                sales_path,
                product_path,
                orders_path,
                demand_window_days=int(demand_window),
            )
    except (EvidenceValidationError, OSError, UnicodeDecodeError) as exc:
        st.error(f"Evidence bundle rejected: {exc}")
        return

    payload = bundle["payload"]
    st.success("Evidence bundle validated and integrity-sealed.")

    metrics = st.columns(4)
    metrics[0].metric("SKUs", len(payload["snapshots"]))
    metrics[1].metric("Source files", len(payload["sources"]))
    metrics[2].metric("Warnings", len(payload["warnings"]))
    metrics[3].metric("Demand window", f"{payload['demandWindowDays']} days")

    st.markdown("### Bundle identity")
    st.code(bundle["bundleId"], language="text")
    st.caption("The bundle ID is the SHA-256 digest of the canonical normalized payload.")

    if payload["warnings"]:
        st.markdown("### Evidence warnings")
        for warning in payload["warnings"]:
            st.warning(warning)

    st.markdown("### Normalized inventory snapshots")
    snapshot_rows = []
    for snapshot in payload["snapshots"]:
        snapshot_rows.append(
            {
                "SKU": snapshot["sku"],
                "Available": snapshot["available"],
                "Avg daily demand": round(snapshot["avgDailyDemand"], 2),
                "Confirmed inbound": snapshot["confirmedInbound"],
                "Lead time (days)": snapshot["leadTimeDays"],
                "Campaign uplift %": snapshot["campaignUpliftPct"],
                "Observed at": snapshot["observedAt"],
            }
        )
    st.dataframe(pd.DataFrame(snapshot_rows), use_container_width=True, hide_index=True)

    with st.expander("Source evidence fingerprints", expanded=False):
        source_rows = [
            {
                "Source": source["name"],
                "File": source["path"],
                "Rows": source["rowCount"],
                "SHA-256": source["sha256"],
                "Evidence ref": source["evidenceRef"],
            }
            for source in payload["sources"]
        ]
        st.dataframe(pd.DataFrame(source_rows), use_container_width=True, hide_index=True)

    bundle_json = json.dumps(bundle, indent=2, sort_keys=True, allow_nan=False) + "\n"
    st.download_button(
        "Export Warden evidence JSON",
        data=bundle_json,
        file_name=f"voi_inventory_evidence_{bundle['bundleId'].split(':', 1)[1][:12]}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.caption(
        "Exporting this JSON does not authorize any action. The Warden runtime independently verifies evidence integrity, "
        "resolves mandate, and gates any material effect."
    )
