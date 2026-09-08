from __future__ import annotations

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


class EstateRegistry:
    """Alpha/local Estate registry.

    This repository stores Estate-local planning records only. It does not
    reserve or mutate operational state in ERP, OMS, marketplace, warehouse,
    or factory systems.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
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

            CREATE INDEX IF NOT EXISTS idx_reservations_resource_window
                ON reservations(resource_id, starts_at, ends_at);
            CREATE INDEX IF NOT EXISTS idx_possibilities_expiry
                ON possibilities(expires_at);
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
