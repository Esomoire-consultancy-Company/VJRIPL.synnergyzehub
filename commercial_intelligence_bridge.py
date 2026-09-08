from __future__ import annotations

import csv
import io
import json

import pandas as pd
import streamlit as st

from voi_commercial_intelligence import (
    CommercialIntelligenceValidationError,
    MODEL_VERSION,
    build_demand_matrix,
    build_recommendation_ledger,
    build_replenishment_recommendations,
    detect_assortment_risks,
    normalize_demand_signals,
    route_ready_goods,
    validate_inventory_bundle,
)


SIGNAL_COLUMNS = {
    "sku",
    "region_id",
    "signal_type",
    "signal_value",
    "observed_at",
}


def _parse_signal_csv_bytes(data: bytes) -> list[dict[str, str]]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CommercialIntelligenceValidationError(
            "demand signals CSV must be UTF-8"
        ) from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames:
        raise CommercialIntelligenceValidationError(
            "demand signals CSV requires a header row"
        )

    headers = [(name or "").strip() for name in reader.fieldnames]
    if len(set(headers)) != len(headers):
        raise CommercialIntelligenceValidationError(
            "demand signals CSV contains duplicate column headers"
        )
    if not SIGNAL_COLUMNS.issubset(set(headers)):
        raise CommercialIntelligenceValidationError(
            "demand signals CSV requires "
            "sku,region_id,signal_type,signal_value,observed_at"
        )
    reader.fieldnames = headers

    rows: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise CommercialIntelligenceValidationError(
                f"demand signals CSV row {row_number} contains extra fields"
            )
        rows.append(
            {
                key: (value or "").strip()
                for key, value in row.items()
            }
        )
    return rows


def show_commercial_intelligence_bridge() -> None:
    st.title("VOI Commercial Intelligence R0.1")
    st.caption(
        "Evidence-linked demand, ready-goods and replenishment recommendations"
    )
    st.warning(
        "Recommendations are advisory only. Warden/operator authorization is "
        "required before any inventory, pricing, order, or marketplace action."
    )

    source_bundle = st.session_state.get("voi_inventory_evidence_bundle")
    bundle_upload = st.file_uploader(
        "Validated VOI inventory evidence JSON (optional)",
        type=["json"],
        key="voi_ci_bundle",
    )
    signal_upload = st.file_uploader(
        "Demand signals CSV (optional)",
        type=["csv"],
        key="voi_ci_signals",
    )

    if bundle_upload is not None:
        try:
            source_bundle = json.loads(bundle_upload.getvalue().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            st.error(f"Evidence JSON rejected: {exc}")
            return

    if source_bundle is None:
        st.info(
            "Build an Inventory Evidence Bridge bundle first, or upload a "
            "validated evidence JSON bundle here."
        )
        return

    try:
        validate_inventory_bundle(source_bundle)
        signals = None
        if signal_upload is not None:
            signals = normalize_demand_signals(
                _parse_signal_csv_bytes(signal_upload.getvalue()),
                inventory_bundle=source_bundle,
            )

        matrix = build_demand_matrix(source_bundle, signals)
        routes = route_ready_goods(matrix)
        recommendations = build_replenishment_recommendations(routes)
        risks, capability_state = detect_assortment_risks(source_bundle)
        ledger = build_recommendation_ledger(
            source_bundle,
            recommendations,
            risks,
            capability_state,
        )
    except CommercialIntelligenceValidationError as exc:
        st.error(f"Commercial intelligence rejected: {exc}")
        return

    st.markdown("### Demand Matrix")
    st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)

    st.markdown("### Ready Goods Routes")
    st.dataframe(pd.DataFrame(routes), use_container_width=True, hide_index=True)

    st.markdown("### Replenishment Recommendations")
    st.dataframe(
        pd.DataFrame(recommendations),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Assortment Risks")
    st.dataframe(pd.DataFrame(risks), use_container_width=True, hide_index=True)

    st.markdown("### Intelligence Contract")
    st.code(ledger["ledgerId"], language="text")
    st.caption(
        f"Model: {MODEL_VERSION} | Source: {ledger['sourceBundleId']}"
    )

    payload = json.dumps(ledger, indent=2, sort_keys=True, allow_nan=False) + "\n"
    st.download_button(
        "Export recommendation ledger JSON",
        data=payload,
        file_name=(
            "voi_commercial_intelligence_"
            f"{ledger['ledgerId'].split(':', 1)[1][:12]}.json"
        ),
        mime="application/json",
        use_container_width=True,
    )
    st.caption(
        "Exporting this recommendation ledger does not authorize or execute "
        "any operational action."
    )
