from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class GuardrailDecision(str, Enum):
    ADMIT = "ADMIT"
    HOLD = "HOLD"


@dataclass(frozen=True)
class GuardrailResult:
    decision: GuardrailDecision
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommercialCase:
    estimated_revenue: float
    estimated_contribution: float
    working_capital_required: float


@dataclass(frozen=True)
class CommercialGuardrails:
    minimum_contribution: float = 0
    maximum_working_capital: float | None = None

    def evaluate(self, case: CommercialCase) -> GuardrailResult:
        reasons: list[str] = []
        if case.estimated_contribution < self.minimum_contribution:
            reasons.append(
                f"Estimated contribution {case.estimated_contribution:.2f} is below minimum {self.minimum_contribution:.2f}"
            )
        if (
            self.maximum_working_capital is not None
            and case.working_capital_required > self.maximum_working_capital
        ):
            reasons.append(
                f"Working capital {case.working_capital_required:.2f} exceeds maximum {self.maximum_working_capital:.2f}"
            )
        if reasons:
            return GuardrailResult(GuardrailDecision.HOLD, tuple(reasons))
        return GuardrailResult(GuardrailDecision.ADMIT)


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    capability_type: str
    owner: str
    available: bool = True
    capacity: float | None = None
    cost: float | None = None
    lead_time_days: int | None = None
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class PossibilityRecord:
    possibility_id: str
    client_id: str
    source: str
    opportunity: str
    owner: str
    state: str = "DISCOVERED"
    estimated_value: float | None = None
    estimated_contribution: float | None = None
    working_capital_required: float | None = None
    required_capabilities: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    expires_at: datetime | None = None


@dataclass(frozen=True)
class ReservationRequest:
    reservation_id: str
    possibility_id: str
    resource_id: str
    quantity: float
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class EvidenceBundleRecord:
    bundle_id: str
    contract: str
    source_mode: str
    integrity_digest: str
    observed_at: str | None


@dataclass(frozen=True)
class PropositionRecord:
    proposition_id: str
    possibility_id: str
    partner: str
    success_criteria: str
    evidence_bundle_id: str


@dataclass(frozen=True)
class DealRecord:
    deal_id: str
    proposition_id: str
    acceptance_evidence_ref: str
    warden_decision_ref: str
    river_receipt_ref: str


@dataclass(frozen=True)
class ExecutionIntentRecord:
    execution_intent_id: str
    deal_id: str
    warden_decision_ref: str
    river_receipt_ref: str
    idempotency_key: str
    effect_state: str = "NO_EXTERNAL_EFFECT"


class EstateRegistry:
    """Alpha/local Estate registry.

    This repository stores Estate-local planning and governance records only.
    It does not reserve or mutate operational state in ERP, OMS, marketplace,
    warehouse, or factory systems.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def close(self) -> None:
        self._conn.close()

    def _initialize_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id TEXT PRIMARY KEY,
                capability_type TEXT NOT NULL,
                owner TEXT NOT NULL,
                available INTEGER NOT NULL,
                capacity REAL,
                cost REAL,
                lead_time_days INTEGER,
                constraints_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS possibilities (
                possibility_id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                source TEXT NOT NULL,
                opportunity TEXT NOT NULL,
                owner TEXT NOT NULL,
                state TEXT NOT NULL,
                estimated_value REAL,
                estimated_contribution REAL,
                working_capital_required REAL,
                required_capabilities_json TEXT NOT NULL,
                evidence_refs_json TEXT NOT NULL,
                expires_at TEXT
            );

            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                possibility_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                quantity REAL NOT NULL,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS evidence_bundles (
                bundle_id TEXT PRIMARY KEY,
                contract TEXT NOT NULL,
                source_mode TEXT NOT NULL,
                integrity_digest TEXT NOT NULL,
                observed_at TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS propositions (
                proposition_id TEXT PRIMARY KEY,
                possibility_id TEXT NOT NULL,
                partner TEXT NOT NULL,
                success_criteria TEXT NOT NULL,
                evidence_bundle_id TEXT NOT NULL,
                FOREIGN KEY(possibility_id) REFERENCES possibilities(possibility_id),
                FOREIGN KEY(evidence_bundle_id) REFERENCES evidence_bundles(bundle_id)
            );

            CREATE TABLE IF NOT EXISTS deals (
                deal_id TEXT PRIMARY KEY,
                proposition_id TEXT NOT NULL,
                acceptance_evidence_ref TEXT NOT NULL,
                warden_decision_ref TEXT NOT NULL,
                river_receipt_ref TEXT NOT NULL,
                FOREIGN KEY(proposition_id) REFERENCES propositions(proposition_id)
            );

            CREATE TABLE IF NOT EXISTS execution_intents (
                execution_intent_id TEXT PRIMARY KEY,
                deal_id TEXT NOT NULL,
                warden_decision_ref TEXT NOT NULL,
                river_receipt_ref TEXT NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                effect_state TEXT NOT NULL CHECK(effect_state = 'NO_EXTERNAL_EFFECT'),
                FOREIGN KEY(deal_id) REFERENCES deals(deal_id)
            );

            CREATE INDEX IF NOT EXISTS idx_reservations_resource_window
                ON reservations(resource_id, starts_at, ends_at);
            CREATE INDEX IF NOT EXISTS idx_possibilities_expiry
                ON possibilities(expires_at);
            CREATE INDEX IF NOT EXISTS idx_propositions_possibility
                ON propositions(possibility_id);
            CREATE INDEX IF NOT EXISTS idx_deals_proposition
                ON deals(proposition_id);
            CREATE INDEX IF NOT EXISTS idx_execution_intents_deal
                ON execution_intents(deal_id);
            """
        )
        self._conn.commit()

    def upsert_capability(self, capability: CapabilityRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO capabilities (
                capability_id, capability_type, owner, available, capacity,
                cost, lead_time_days, constraints_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(capability_id) DO UPDATE SET
                capability_type=excluded.capability_type,
                owner=excluded.owner,
                available=excluded.available,
                capacity=excluded.capacity,
                cost=excluded.cost,
                lead_time_days=excluded.lead_time_days,
                constraints_json=excluded.constraints_json
            """,
            (
                capability.capability_id,
                capability.capability_type,
                capability.owner,
                int(capability.available),
                capability.capacity,
                capability.cost,
                capability.lead_time_days,
                json.dumps(capability.constraints),
            ),
        )
        self._conn.commit()

    def list_capabilities(self) -> list[CapabilityRecord]:
        rows = self._conn.execute(
            "SELECT * FROM capabilities ORDER BY capability_id"
        ).fetchall()
        return [self._capability_from_row(row) for row in rows]

    def upsert_possibility(self, possibility: PossibilityRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO possibilities (
                possibility_id, client_id, source, opportunity, owner, state,
                estimated_value, estimated_contribution, working_capital_required,
                required_capabilities_json, evidence_refs_json, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(possibility_id) DO UPDATE SET
                client_id=excluded.client_id,
                source=excluded.source,
                opportunity=excluded.opportunity,
                owner=excluded.owner,
                state=excluded.state,
                estimated_value=excluded.estimated_value,
                estimated_contribution=excluded.estimated_contribution,
                working_capital_required=excluded.working_capital_required,
                required_capabilities_json=excluded.required_capabilities_json,
                evidence_refs_json=excluded.evidence_refs_json,
                expires_at=excluded.expires_at
            """,
            (
                possibility.possibility_id,
                possibility.client_id,
                possibility.source,
                possibility.opportunity,
                possibility.owner,
                possibility.state,
                possibility.estimated_value,
                possibility.estimated_contribution,
                possibility.working_capital_required,
                json.dumps(possibility.required_capabilities),
                json.dumps(possibility.evidence_refs),
                _datetime_to_text(possibility.expires_at),
            ),
        )
        self._conn.commit()

    def get_possibility(self, possibility_id: str) -> PossibilityRecord | None:
        row = self._conn.execute(
            "SELECT * FROM possibilities WHERE possibility_id = ?",
            (possibility_id,),
        ).fetchone()
        return self._possibility_from_row(row) if row else None

    def list_possibilities(self) -> list[PossibilityRecord]:
        rows = self._conn.execute(
            "SELECT * FROM possibilities ORDER BY possibility_id"
        ).fetchall()
        return [self._possibility_from_row(row) for row in rows]

    def list_expired_possibilities(self, observed_at: datetime) -> list[PossibilityRecord]:
        rows = self._conn.execute(
            """
            SELECT * FROM possibilities
            WHERE expires_at IS NOT NULL AND expires_at < ?
            ORDER BY expires_at, possibility_id
            """,
            (_datetime_to_text(observed_at),),
        ).fetchall()
        return [self._possibility_from_row(row) for row in rows]

    def reserve(self, request: ReservationRequest) -> None:
        if request.quantity <= 0:
            raise ValueError("Reservation quantity must be greater than zero")
        if request.starts_at >= request.ends_at:
            raise ValueError("Reservation start must be before end")

        conflict = self._conn.execute(
            """
            SELECT reservation_id FROM reservations
            WHERE resource_id = ?
              AND starts_at < ?
              AND ends_at > ?
            LIMIT 1
            """,
            (
                request.resource_id,
                _datetime_to_text(request.ends_at),
                _datetime_to_text(request.starts_at),
            ),
        ).fetchone()
        if conflict:
            raise ValueError(
                f"Estate reservation conflict for {request.resource_id}: {conflict['reservation_id']}"
            )

        self._conn.execute(
            """
            INSERT INTO reservations (
                reservation_id, possibility_id, resource_id, quantity, starts_at, ends_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.reservation_id,
                request.possibility_id,
                request.resource_id,
                request.quantity,
                _datetime_to_text(request.starts_at),
                _datetime_to_text(request.ends_at),
            ),
        )
        self._conn.commit()

    def list_reservations(self) -> list[ReservationRequest]:
        rows = self._conn.execute(
            "SELECT * FROM reservations ORDER BY starts_at, reservation_id"
        ).fetchall()
        return [
            ReservationRequest(
                reservation_id=row["reservation_id"],
                possibility_id=row["possibility_id"],
                resource_id=row["resource_id"],
                quantity=row["quantity"],
                starts_at=datetime.fromisoformat(row["starts_at"]),
                ends_at=datetime.fromisoformat(row["ends_at"]),
            )
            for row in rows
        ]

    def register_inventory_evidence_bundle(self, bundle: dict) -> EvidenceBundleRecord:
        contract = bundle.get("contract")
        source_mode = bundle.get("sourceMode")
        if contract != "VOI-INVENTORY-EVIDENCE-001":
            raise ValueError("Unsupported evidence contract")
        if source_mode != "READ_ONLY_EXPORT":
            raise ValueError("Unsupported evidence source mode")

        integrity = bundle.get("integrity") or {}
        if integrity.get("algorithm") != "SHA-256":
            raise ValueError("Evidence integrity algorithm must be SHA-256")
        payload = bundle.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("Evidence payload is required")

        canonical_payload = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        expected_digest = f"sha256:{hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()}"
        if integrity.get("canonicalPayload") != canonical_payload:
            raise ValueError("Evidence integrity canonical payload mismatch")
        if integrity.get("digest") != expected_digest:
            raise ValueError("Evidence integrity digest mismatch")
        if bundle.get("bundleId") != expected_digest:
            raise ValueError("Evidence integrity bundle ID mismatch")

        record = EvidenceBundleRecord(
            bundle_id=expected_digest,
            contract=contract,
            source_mode=source_mode,
            integrity_digest=expected_digest,
            observed_at=payload.get("observedAt"),
        )
        self._conn.execute(
            """
            INSERT INTO evidence_bundles (
                bundle_id, contract, source_mode, integrity_digest, observed_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(bundle_id) DO NOTHING
            """,
            (
                record.bundle_id,
                record.contract,
                record.source_mode,
                record.integrity_digest,
                record.observed_at,
                canonical_payload,
            ),
        )
        self._conn.commit()
        return record

    def create_proposition(self, proposition: PropositionRecord) -> PropositionRecord:
        possibility = self.get_possibility(proposition.possibility_id)
        if possibility is None:
            raise ValueError("Proposition requires a persisted possibility")
        if possibility.state != "QUALIFIED":
            raise ValueError("Proposition requires a QUALIFIED possibility")
        evidence = self._conn.execute(
            "SELECT bundle_id FROM evidence_bundles WHERE bundle_id = ?",
            (proposition.evidence_bundle_id,),
        ).fetchone()
        if evidence is None:
            raise ValueError("Proposition requires a registered evidence bundle")
        if not proposition.partner.strip() or not proposition.success_criteria.strip():
            raise ValueError("Proposition partner and success criteria are required")

        self._conn.execute(
            """
            INSERT INTO propositions (
                proposition_id, possibility_id, partner, success_criteria, evidence_bundle_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                proposition.proposition_id,
                proposition.possibility_id,
                proposition.partner,
                proposition.success_criteria,
                proposition.evidence_bundle_id,
            ),
        )
        self._conn.execute(
            "UPDATE possibilities SET state = 'PROPOSITION' WHERE possibility_id = ?",
            (proposition.possibility_id,),
        )
        self._conn.commit()
        return proposition

    def get_proposition(self, proposition_id: str) -> PropositionRecord | None:
        row = self._conn.execute(
            "SELECT * FROM propositions WHERE proposition_id = ?",
            (proposition_id,),
        ).fetchone()
        return self._proposition_from_row(row) if row else None

    def list_propositions(self) -> list[PropositionRecord]:
        rows = self._conn.execute(
            "SELECT * FROM propositions ORDER BY proposition_id"
        ).fetchall()
        return [self._proposition_from_row(row) for row in rows]

    def accept_deal(self, deal: DealRecord) -> DealRecord:
        proposition = self.get_proposition(deal.proposition_id)
        if proposition is None:
            raise ValueError("Deal requires a persisted proposition")
        if not deal.acceptance_evidence_ref.strip():
            raise ValueError("Commercial acceptance evidence is required")
        if not deal.warden_decision_ref.strip():
            raise ValueError("Warden decision reference is required")
        if not deal.river_receipt_ref.strip():
            raise ValueError("River receipt reference is required")

        self._conn.execute(
            """
            INSERT INTO deals (
                deal_id, proposition_id, acceptance_evidence_ref,
                warden_decision_ref, river_receipt_ref
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                deal.deal_id,
                deal.proposition_id,
                deal.acceptance_evidence_ref,
                deal.warden_decision_ref,
                deal.river_receipt_ref,
            ),
        )
        self._conn.execute(
            """
            UPDATE possibilities SET state = 'DEAL'
            WHERE possibility_id = (
                SELECT possibility_id FROM propositions WHERE proposition_id = ?
            )
            """,
            (deal.proposition_id,),
        )
        self._conn.commit()
        return deal

    def get_deal(self, deal_id: str) -> DealRecord | None:
        row = self._conn.execute(
            "SELECT * FROM deals WHERE deal_id = ?",
            (deal_id,),
        ).fetchone()
        return self._deal_from_row(row) if row else None

    def list_deals(self) -> list[DealRecord]:
        rows = self._conn.execute("SELECT * FROM deals ORDER BY deal_id").fetchall()
        return [self._deal_from_row(row) for row in rows]

    def create_execution_intent(
        self,
        intent: ExecutionIntentRecord,
    ) -> ExecutionIntentRecord:
        deal = self.get_deal(intent.deal_id)
        if deal is None:
            raise ValueError("Execution intent requires a persisted Deal")
        if not intent.warden_decision_ref.strip():
            raise ValueError("Warden decision reference is required")
        if not intent.river_receipt_ref.strip():
            raise ValueError("River receipt reference is required")
        if not intent.idempotency_key.strip():
            raise ValueError("Execution intent requires an idempotency key")
        if intent.effect_state != "NO_EXTERNAL_EFFECT":
            raise ValueError("Execution intent must remain NO_EXTERNAL_EFFECT in R0.3")

        try:
            self._conn.execute(
                """
                INSERT INTO execution_intents (
                    execution_intent_id, deal_id, warden_decision_ref,
                    river_receipt_ref, idempotency_key, effect_state
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    intent.execution_intent_id,
                    intent.deal_id,
                    intent.warden_decision_ref,
                    intent.river_receipt_ref,
                    intent.idempotency_key,
                    intent.effect_state,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if "idempotency_key" in str(exc):
                raise ValueError("Execution intent idempotency key already exists") from exc
            raise

        self._conn.execute(
            """
            UPDATE possibilities SET state = 'EXECUTION_INTENT'
            WHERE possibility_id = (
                SELECT p.possibility_id
                FROM propositions p
                JOIN deals d ON d.proposition_id = p.proposition_id
                WHERE d.deal_id = ?
            )
            """,
            (intent.deal_id,),
        )
        self._conn.commit()
        return intent

    def get_execution_intent(
        self,
        execution_intent_id: str,
    ) -> ExecutionIntentRecord | None:
        row = self._conn.execute(
            "SELECT * FROM execution_intents WHERE execution_intent_id = ?",
            (execution_intent_id,),
        ).fetchone()
        return self._execution_intent_from_row(row) if row else None

    def list_execution_intents(self) -> list[ExecutionIntentRecord]:
        rows = self._conn.execute(
            "SELECT * FROM execution_intents ORDER BY execution_intent_id"
        ).fetchall()
        return [self._execution_intent_from_row(row) for row in rows]

    @staticmethod
    def _capability_from_row(row: sqlite3.Row) -> CapabilityRecord:
        return CapabilityRecord(
            capability_id=row["capability_id"],
            capability_type=row["capability_type"],
            owner=row["owner"],
            available=bool(row["available"]),
            capacity=row["capacity"],
            cost=row["cost"],
            lead_time_days=row["lead_time_days"],
            constraints=tuple(json.loads(row["constraints_json"])),
        )

    @staticmethod
    def _possibility_from_row(row: sqlite3.Row) -> PossibilityRecord:
        return PossibilityRecord(
            possibility_id=row["possibility_id"],
            client_id=row["client_id"],
            source=row["source"],
            opportunity=row["opportunity"],
            owner=row["owner"],
            state=row["state"],
            estimated_value=row["estimated_value"],
            estimated_contribution=row["estimated_contribution"],
            working_capital_required=row["working_capital_required"],
            required_capabilities=tuple(json.loads(row["required_capabilities_json"])),
            evidence_refs=tuple(json.loads(row["evidence_refs_json"])),
            expires_at=(
                datetime.fromisoformat(row["expires_at"])
                if row["expires_at"] is not None
                else None
            ),
        )

    @staticmethod
    def _proposition_from_row(row: sqlite3.Row) -> PropositionRecord:
        return PropositionRecord(
            proposition_id=row["proposition_id"],
            possibility_id=row["possibility_id"],
            partner=row["partner"],
            success_criteria=row["success_criteria"],
            evidence_bundle_id=row["evidence_bundle_id"],
        )

    @staticmethod
    def _deal_from_row(row: sqlite3.Row) -> DealRecord:
        return DealRecord(
            deal_id=row["deal_id"],
            proposition_id=row["proposition_id"],
            acceptance_evidence_ref=row["acceptance_evidence_ref"],
            warden_decision_ref=row["warden_decision_ref"],
            river_receipt_ref=row["river_receipt_ref"],
        )

    @staticmethod
    def _execution_intent_from_row(row: sqlite3.Row) -> ExecutionIntentRecord:
        return ExecutionIntentRecord(
            execution_intent_id=row["execution_intent_id"],
            deal_id=row["deal_id"],
            warden_decision_ref=row["warden_decision_ref"],
            river_receipt_ref=row["river_receipt_ref"],
            idempotency_key=row["idempotency_key"],
            effect_state=row["effect_state"],
        )


def _datetime_to_text(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def seed_voi_capabilities(registry: EstateRegistry) -> None:
    capabilities = (
        CapabilityRecord("CAP-PRODUCT-DESIGN", "product", "VOI-product"),
        CapabilityRecord("CAP-DENIM-MANUFACTURING", "manufacturing", "VOI-factory"),
        CapabilityRecord("CAP-WASHING", "manufacturing", "VOI-wash"),
        CapabilityRecord("CAP-WH-BLR", "warehouse", "VOI-warehouse"),
        CapabilityRecord("CAP-ERP-LOGIC", "enterprise-system", "Logic ERP"),
        CapabilityRecord("CAP-OMS-EASYCOM", "commerce-system", "Easycom"),
        CapabilityRecord("CAP-CHANNEL-MYNTRA", "market-channel", "Myntra"),
        CapabilityRecord("CAP-CHANNEL-FLIPKART", "market-channel", "Flipkart"),
        CapabilityRecord("CAP-CHANNEL-CENTRO", "retail-channel", "Centro"),
        CapabilityRecord("CAP-PHOTOGRAPHY", "content", "VOI-content"),
        CapabilityRecord("CAP-CATALOGUE", "content", "VOI-commerce"),
        CapabilityRecord("CAP-RETURNS", "commerce-operations", "VOI-operations"),
        CapabilityRecord("CAP-REPLENISHMENT", "commerce-operations", "VOI-operations"),
    )
    for capability in capabilities:
        registry.upsert_capability(capability)
