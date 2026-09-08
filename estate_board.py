from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

from estate_registry import (
    CommercialCase,
    CommercialGuardrails,
    DealRecord,
    EstateRegistry,
    ExecutionIntentRecord,
    GuardrailDecision,
    PossibilityRecord,
    PropositionRecord,
    seed_voi_capabilities,
)


@dataclass(frozen=True)
class ChannelTemplate:
    partner: str
    objective: str
    success_criteria: str
    required_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class BoardSummary:
    possibility_count: int
    estimated_value: float
    estimated_contribution: float
    expired_count: int


@dataclass(frozen=True)
class GovernanceSummary:
    proposition_count: int
    deal_count: int
    execution_intent_count: int
    all_intents_no_external_effect: bool


_CHANNEL_TEMPLATES = {
    "Myntra": ChannelTemplate(
        partner="Myntra",
        objective="Create incremental category business through relevant assortment, availability and replenishment.",
        success_criteria="Incremental sell-through and contribution with returns inside the agreed guardrail.",
        required_capabilities=(
            "CAP-ERP-LOGIC",
            "CAP-OMS-EASYCOM",
            "CAP-CHANNEL-MYNTRA",
            "CAP-WH-BLR",
            "CAP-CATALOGUE",
        ),
    ),
    "Flipkart": ChannelTemplate(
        partner="Flipkart",
        objective="Create incremental marketplace business using price, catalogue, availability and geographic demand signals.",
        success_criteria="Positive incremental contribution with acceptable fulfilment and return performance.",
        required_capabilities=(
            "CAP-ERP-LOGIC",
            "CAP-OMS-EASYCOM",
            "CAP-CHANNEL-FLIPKART",
            "CAP-WH-BLR",
            "CAP-CATALOGUE",
        ),
    ),
    "Centro": ChannelTemplate(
        partner="Centro",
        objective="Create incremental retail business through differentiated assortment, allocation and replenishment.",
        success_criteria="Accepted assortment converts to profitable retail sell-through and repeat replenishment.",
        required_capabilities=(
            "CAP-ERP-LOGIC",
            "CAP-CHANNEL-CENTRO",
            "CAP-WH-BLR",
            "CAP-PRODUCT-DESIGN",
            "CAP-REPLENISHMENT",
        ),
    ),
}


def channel_template(partner: str) -> ChannelTemplate:
    try:
        return _CHANNEL_TEMPLATES[partner]
    except KeyError as exc:
        raise ValueError(f"Unsupported Estate channel template: {partner}") from exc


def build_board_summary(
    possibilities: Iterable[PossibilityRecord],
    *,
    observed_at: datetime,
) -> BoardSummary:
    records = list(possibilities)
    estimated_value = sum(item.estimated_value or 0 for item in records)
    estimated_contribution = sum(item.estimated_contribution or 0 for item in records)
    expired_count = sum(
        1
        for item in records
        if item.expires_at is not None and item.expires_at < observed_at
    )
    return BoardSummary(
        possibility_count=len(records),
        estimated_value=estimated_value,
        estimated_contribution=estimated_contribution,
        expired_count=expired_count,
    )


def build_governance_summary(
    propositions: Iterable[PropositionRecord],
    deals: Iterable[DealRecord],
    execution_intents: Iterable[ExecutionIntentRecord],
) -> GovernanceSummary:
    proposition_records = list(propositions)
    deal_records = list(deals)
    intent_records = list(execution_intents)
    return GovernanceSummary(
        proposition_count=len(proposition_records),
        deal_count=len(deal_records),
        execution_intent_count=len(intent_records),
        all_intents_no_external_effect=all(
            item.effect_state == "NO_EXTERNAL_EFFECT" for item in intent_records
        ),
    )


def _registry_path() -> Path:
    configured = os.getenv("ESTATE_DB_PATH")
    path = Path(configured) if configured else Path(".estate") / "estate_alpha.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@st.cache_resource
def _registry() -> EstateRegistry:
    registry = EstateRegistry(_registry_path())
    seed_voi_capabilities(registry)
    return registry


def show_estate_board() -> None:
    registry = _registry()
    possibilities = registry.list_possibilities()
    propositions = registry.list_propositions()
    deals = registry.list_deals()
    execution_intents = registry.list_execution_intents()
    now = datetime.now(timezone.utc)
    summary = build_board_summary(possibilities, observed_at=now)
    governance = build_governance_summary(propositions, deals, execution_intents)

    st.title("Estate Board")
    st.caption("VOI / Voyej — Estate Client 001 | Possibility → Reality commercial operating layer")
    st.info(
        "Alpha boundary: this board writes only Estate-local planning records. It does not mutate Logic ERP, Easycom, "
        "Myntra, Flipkart, Centro, warehouse inventory, or factory controls."
    )

    metrics = st.columns(4)
    metrics[0].metric("Possibilities", summary.possibility_count)
    metrics[1].metric("Estimated value", f"₹{summary.estimated_value:,.0f}")
    metrics[2].metric("Estimated contribution", f"₹{summary.estimated_contribution:,.0f}")
    metrics[3].metric("Needs requalification", summary.expired_count)

    portfolio_tab, intake_tab, capability_tab, governance_tab = st.tabs(
        ["Possibility Portfolio", "Create Possibility", "Capability Ledger", "Governance Chain"]
    )

    with portfolio_tab:
        _show_portfolio(possibilities, now)

    with intake_tab:
        _show_possibility_intake(registry)

    with capability_tab:
        _show_capability_ledger(registry)

    with governance_tab:
        _show_governance_chain(propositions, deals, execution_intents, governance)


def _show_portfolio(possibilities: list[PossibilityRecord], now: datetime) -> None:
    if not possibilities:
        st.info("No Estate possibilities have been admitted yet.")
        return

    rows = []
    for item in possibilities:
        rows.append(
            {
                "Possibility": item.possibility_id,
                "Source": item.source,
                "Opportunity": item.opportunity,
                "Owner": item.owner,
                "State": item.state,
                "Estimated value": item.estimated_value,
                "Estimated contribution": item.estimated_contribution,
                "Working capital": item.working_capital_required,
                "Expiry": item.expires_at.isoformat() if item.expires_at else None,
                "Requalify": bool(item.expires_at and item.expires_at < now),
                "Evidence refs": "\n".join(item.evidence_refs),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Expiry marks a possibility for requalification; it does not delete the record or alter external system state."
    )


def _show_possibility_intake(registry: EstateRegistry) -> None:
    capabilities = registry.list_capabilities()
    capability_ids = [item.capability_id for item in capabilities if item.available]

    source = st.selectbox(
        "Possibility source",
        ["Myntra", "Flipkart", "Centro", "Warehouse", "Factory", "Management", "Customer behaviour"],
    )
    template = _CHANNEL_TEMPLATES.get(source)
    if template:
        st.markdown(f"**External growth objective:** {template.objective}")
        st.caption(f"Default success criterion: {template.success_criteria}")

    with st.form("estate_possibility_intake", clear_on_submit=False):
        possibility_id = st.text_input("Possibility ID", placeholder="EST-POS-000001")
        opportunity = st.text_area("Opportunity", placeholder="Describe the business possibility in concrete terms")
        owner = st.text_input("Estate owner", placeholder="marketplace-desk / inventory-desk / factory-desk")

        finance_cols = st.columns(3)
        estimated_value = finance_cols[0].number_input("Estimated revenue/value ₹", min_value=0.0, step=10_000.0)
        estimated_contribution = finance_cols[1].number_input(
            "Estimated contribution ₹", step=10_000.0
        )
        working_capital = finance_cols[2].number_input(
            "Working capital required ₹", min_value=0.0, step=10_000.0
        )

        guardrail_cols = st.columns(2)
        minimum_contribution = guardrail_cols[0].number_input(
            "Minimum contribution gate ₹", value=0.0, step=10_000.0
        )
        maximum_working_capital = guardrail_cols[1].number_input(
            "Maximum working-capital gate ₹", min_value=0.0, value=5_000_000.0, step=100_000.0
        )

        default_caps = list(template.required_capabilities) if template else []
        required_capabilities = st.multiselect(
            "Required Estate capabilities",
            capability_ids,
            default=[item for item in default_caps if item in capability_ids],
        )
        evidence_text = st.text_area(
            "Evidence references",
            placeholder="One per line, e.g. river://voi/inventory/<bundle-id>",
        )
        validity_days = st.number_input("Commercial validity (days)", min_value=1, max_value=180, value=30)

        submitted = st.form_submit_button("Admit Possibility", type="primary", use_container_width=True)

    if not submitted:
        return

    if not possibility_id.strip() or not opportunity.strip() or not owner.strip():
        st.error("Possibility ID, opportunity and owner are required.")
        return
    if not possibility_id.strip().startswith("EST-POS-"):
        st.error("Possibility ID must use the EST-POS-* namespace.")
        return

    commercial_case = CommercialCase(
        estimated_revenue=float(estimated_value),
        estimated_contribution=float(estimated_contribution),
        working_capital_required=float(working_capital),
    )
    result = CommercialGuardrails(
        minimum_contribution=float(minimum_contribution),
        maximum_working_capital=float(maximum_working_capital),
    ).evaluate(commercial_case)

    evidence_refs = tuple(
        line.strip() for line in evidence_text.splitlines() if line.strip()
    )
    state = "DISCOVERED" if result.decision == GuardrailDecision.ADMIT else "HOLD"
    record = PossibilityRecord(
        possibility_id=possibility_id.strip(),
        client_id="VOI-CLIENT-001",
        source=source,
        opportunity=opportunity.strip(),
        owner=owner.strip(),
        state=state,
        estimated_value=float(estimated_value),
        estimated_contribution=float(estimated_contribution),
        working_capital_required=float(working_capital),
        required_capabilities=tuple(required_capabilities),
        evidence_refs=evidence_refs,
        expires_at=datetime.now(timezone.utc) + timedelta(days=int(validity_days)),
    )
    registry.upsert_possibility(record)

    if result.decision == GuardrailDecision.ADMIT:
        st.success(f"{record.possibility_id} admitted to Estate discovery.")
    else:
        st.warning(f"{record.possibility_id} recorded on HOLD: {'; '.join(result.reasons)}")
    st.caption("No external operational action was taken.")


def _show_capability_ledger(registry: EstateRegistry) -> None:
    capabilities = registry.list_capabilities()
    rows = [
        {
            "Capability": item.capability_id,
            "Type": item.capability_type,
            "Owner / external system": item.owner,
            "Available": item.available,
            "Capacity": item.capacity,
            "Cost": item.cost,
            "Lead time days": item.lead_time_days,
            "Constraints": "; ".join(item.constraints),
        }
        for item in capabilities
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(
        "Availability here is an Estate capability assertion. Before any material commitment, the relevant operational "
        "system must provide current evidence and the applicable authority gate must still be satisfied."
    )


def _show_governance_chain(
    propositions: list[PropositionRecord],
    deals: list[DealRecord],
    execution_intents: list[ExecutionIntentRecord],
    summary: GovernanceSummary,
) -> None:
    st.subheader("Governed Commercial Chain")
    st.caption(
        "Read-only inspection of persisted Estate governance records. This surface cannot execute an order, reserve ERP "
        "inventory, publish to a marketplace, or release factory work."
    )

    metrics = st.columns(4)
    metrics[0].metric("Propositions", summary.proposition_count)
    metrics[1].metric("Accepted deals", summary.deal_count)
    metrics[2].metric("Execution intents", summary.execution_intent_count)
    metrics[3].metric(
        "External effects",
        "None" if summary.all_intents_no_external_effect else "Policy breach",
    )

    if propositions:
        st.markdown("### Propositions")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Proposition": item.proposition_id,
                        "Possibility": item.possibility_id,
                        "Partner": item.partner,
                        "Evidence bundle": item.evidence_bundle_id,
                        "Success criteria": item.success_criteria,
                    }
                    for item in propositions
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if deals:
        st.markdown("### Deals")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Deal": item.deal_id,
                        "Proposition": item.proposition_id,
                        "Acceptance evidence": item.acceptance_evidence_ref,
                        "Warden decision": item.warden_decision_ref,
                        "River receipt": item.river_receipt_ref,
                    }
                    for item in deals
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if execution_intents:
        st.markdown("### Governed execution intents")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Execution intent": item.execution_intent_id,
                        "Deal": item.deal_id,
                        "Warden decision": item.warden_decision_ref,
                        "River receipt": item.river_receipt_ref,
                        "Idempotency key": item.idempotency_key,
                        "Effect state": item.effect_state,
                    }
                    for item in execution_intents
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    if not propositions and not deals and not execution_intents:
        st.info("No governed Proposition, Deal or Execution Intent records exist yet.")

    st.warning(
        "R0.3 execution intent is documentary and non-executing. Any future external effect requires an admitted connector, "
        "current Warden authorization, provider acknowledgement and River evidence."
    )
