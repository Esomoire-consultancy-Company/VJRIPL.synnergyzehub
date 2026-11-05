from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class PossibilityState(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUALIFICATION = "QUALIFICATION"
    QUALIFIED = "QUALIFIED"
    PROPOSITION = "PROPOSITION"
    DEAL = "DEAL"
    EXECUTION = "EXECUTION"
    REALITY = "REALITY"
    HOLD = "HOLD"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class QualificationDecision(str, Enum):
    QUALIFIED = "QUALIFIED"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"
    HOLD = "HOLD"


@dataclass(frozen=True)
class QualificationGate:
    demand: bool
    capability: bool
    economics: bool
    delivery_time: bool
    authority: bool
    measurable_outcome: bool

    @property
    def complete(self) -> bool:
        return all(
            (
                self.demand,
                self.capability,
                self.economics,
                self.delivery_time,
                self.authority,
                self.measurable_outcome,
            )
        )


@dataclass
class Possibility:
    possibility_id: str
    client_id: str
    source: str
    opportunity: str
    owner: str
    required_capabilities: tuple[str, ...] = ()
    estimated_value: float | None = None
    state: PossibilityState = PossibilityState.DISCOVERED
    qualification: QualificationDecision | None = None


@dataclass(frozen=True)
class Capability:
    capability_id: str
    owner: str
    available: bool
    capacity: float | None = None
    cost: float | None = None
    lead_time_days: int | None = None
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class Proposition:
    proposition_id: str
    possibility_id: str
    partner: str
    success_criteria: str


@dataclass(frozen=True)
class Deal:
    deal_id: str
    proposition_id: str
    acceptance_evidence_ref: str


@dataclass(frozen=True)
class Reality:
    reality_id: str
    deal_id: str
    outcome_evidence_ref: str
    realized_revenue: float | None = None
    realized_contribution: float | None = None


def qualify_possibility(
    possibility: Possibility,
    gate: QualificationGate,
    *,
    reject: bool = False,
    hold: bool = False,
) -> QualificationDecision:
    if reject and hold:
        raise ValueError("A possibility cannot be rejected and held simultaneously")

    if reject:
        decision = QualificationDecision.REJECTED
        possibility.state = PossibilityState.REJECTED
    elif hold:
        decision = QualificationDecision.HOLD
        possibility.state = PossibilityState.HOLD
    elif gate.complete:
        decision = QualificationDecision.QUALIFIED
        possibility.state = PossibilityState.QUALIFIED
    else:
        decision = QualificationDecision.CONDITIONAL
        possibility.state = PossibilityState.QUALIFICATION

    possibility.qualification = decision
    return decision


def assert_capabilities_available(
    required_capabilities: Iterable[str],
    capabilities: Iterable[Capability],
) -> None:
    indexed = {capability.capability_id: capability for capability in capabilities}
    missing = [cap for cap in required_capabilities if cap not in indexed]
    unavailable = [
        cap
        for cap in required_capabilities
        if cap in indexed and not indexed[cap].available
    ]
    if missing or unavailable:
        details = []
        if missing:
            details.append(f"missing={','.join(sorted(missing))}")
        if unavailable:
            details.append(f"unavailable={','.join(sorted(unavailable))}")
        raise ValueError("Capability availability gate failed: " + "; ".join(details))


def promote_to_proposition(
    possibility: Possibility,
    *,
    proposition_id: str,
    partner: str,
    success_criteria: str,
    capabilities: Iterable[Capability] = (),
) -> Proposition:
    if possibility.qualification != QualificationDecision.QUALIFIED:
        raise ValueError("Only QUALIFIED possibilities may become propositions")

    if possibility.required_capabilities:
        assert_capabilities_available(possibility.required_capabilities, capabilities)

    possibility.state = PossibilityState.PROPOSITION
    return Proposition(
        proposition_id=proposition_id,
        possibility_id=possibility.possibility_id,
        partner=partner,
        success_criteria=success_criteria,
    )


def accept_deal(
    possibility: Possibility,
    proposition: Proposition,
    *,
    deal_id: str,
    acceptance_evidence_ref: str,
) -> Deal:
    if possibility.state != PossibilityState.PROPOSITION:
        raise ValueError("A deal requires an active proposition")
    if proposition.possibility_id != possibility.possibility_id:
        raise ValueError("Proposition does not belong to the possibility")
    if not acceptance_evidence_ref.strip():
        raise ValueError("Commercial acceptance evidence is required")

    possibility.state = PossibilityState.DEAL
    return Deal(
        deal_id=deal_id,
        proposition_id=proposition.proposition_id,
        acceptance_evidence_ref=acceptance_evidence_ref,
    )


def confirm_reality(
    possibility: Possibility,
    deal: Deal,
    *,
    reality_id: str,
    outcome_evidence_ref: str,
    realized_revenue: float | None = None,
    realized_contribution: float | None = None,
) -> Reality:
    if possibility.state not in {PossibilityState.DEAL, PossibilityState.EXECUTION}:
        raise ValueError("Reality confirmation requires an accepted deal or execution state")
    if not outcome_evidence_ref.strip():
        raise ValueError("Outcome evidence is required before a possibility becomes reality")

    possibility.state = PossibilityState.REALITY
    return Reality(
        reality_id=reality_id,
        deal_id=deal.deal_id,
        outcome_evidence_ref=outcome_evidence_ref,
        realized_revenue=realized_revenue,
        realized_contribution=realized_contribution,
    )
