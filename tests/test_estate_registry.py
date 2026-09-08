import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from estate_registry import (
    CommercialCase,
    CommercialGuardrails,
    EstateRegistry,
    GuardrailDecision,
    PossibilityRecord,
    ReservationRequest,
    seed_voi_capabilities,
)


class EstateRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="estate-registry-")
        self.db_path = Path(self.tmp.name) / "estate.db"
        self.registry = EstateRegistry(self.db_path)

    def tearDown(self):
        self.registry.close()
        self.tmp.cleanup()

    def test_seed_voi_capabilities_is_idempotent(self):
        seed_voi_capabilities(self.registry)
        seed_voi_capabilities(self.registry)

        capabilities = self.registry.list_capabilities()

        self.assertGreaterEqual(len(capabilities), 13)
        ids = {cap.capability_id for cap in capabilities}
        self.assertIn("CAP-ERP-LOGIC", ids)
        self.assertIn("CAP-OMS-EASYCOM", ids)
        self.assertIn("CAP-CHANNEL-MYNTRA", ids)
        self.assertIn("CAP-CHANNEL-FLIPKART", ids)
        self.assertIn("CAP-CHANNEL-CENTRO", ids)
        self.assertEqual(len(ids), len(capabilities))

    def test_possibility_round_trips_with_external_evidence_reference(self):
        expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        record = PossibilityRecord(
            possibility_id="EST-POS-000101",
            client_id="VOI-CLIENT-001",
            source="Myntra",
            opportunity="Expand ready-goods relaxed denim assortment",
            owner="marketplace-desk",
            state="DISCOVERED",
            estimated_value=1_800_000,
            estimated_contribution=420_000,
            working_capital_required=600_000,
            required_capabilities=("CAP-ERP-LOGIC", "CAP-CHANNEL-MYNTRA"),
            evidence_refs=("river://voi/inventory/bundle-001",),
            expires_at=expires_at,
        )

        self.registry.upsert_possibility(record)
        loaded = self.registry.get_possibility(record.possibility_id)

        self.assertEqual(loaded, record)

    def test_expired_possibility_is_detected_without_deleting_history(self):
        record = PossibilityRecord(
            possibility_id="EST-POS-000102",
            client_id="VOI-CLIENT-001",
            source="Warehouse",
            opportunity="Recover ageing inventory",
            owner="inventory-desk",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        self.registry.upsert_possibility(record)

        expired = self.registry.list_expired_possibilities(datetime.now(timezone.utc))

        self.assertEqual([item.possibility_id for item in expired], [record.possibility_id])
        self.assertIsNotNone(self.registry.get_possibility(record.possibility_id))

    def test_guardrails_hold_negative_contribution_case(self):
        case = CommercialCase(
            estimated_revenue=1_000_000,
            estimated_contribution=-10_000,
            working_capital_required=200_000,
        )
        guardrails = CommercialGuardrails(
            minimum_contribution=0,
            maximum_working_capital=1_000_000,
        )

        result = guardrails.evaluate(case)

        self.assertEqual(result.decision, GuardrailDecision.HOLD)
        self.assertIn("contribution", " ".join(result.reasons).lower())

    def test_guardrails_hold_case_above_working_capital_limit(self):
        case = CommercialCase(
            estimated_revenue=2_000_000,
            estimated_contribution=300_000,
            working_capital_required=1_500_000,
        )
        guardrails = CommercialGuardrails(
            minimum_contribution=100_000,
            maximum_working_capital=1_000_000,
        )

        result = guardrails.evaluate(case)

        self.assertEqual(result.decision, GuardrailDecision.HOLD)
        self.assertIn("working capital", " ".join(result.reasons).lower())

    def test_guardrails_admit_case_within_limits(self):
        case = CommercialCase(
            estimated_revenue=2_000_000,
            estimated_contribution=300_000,
            working_capital_required=500_000,
        )
        guardrails = CommercialGuardrails(
            minimum_contribution=100_000,
            maximum_working_capital=1_000_000,
        )

        result = guardrails.evaluate(case)

        self.assertEqual(result.decision, GuardrailDecision.ADMIT)
        self.assertEqual(result.reasons, ())

    def test_overlapping_reservation_for_same_resource_is_rejected(self):
        now = datetime.now(timezone.utc)
        first = ReservationRequest(
            reservation_id="EST-RES-000001",
            possibility_id="EST-POS-000201",
            resource_id="SKU:VOI-READY-001",
            quantity=100,
            starts_at=now,
            ends_at=now + timedelta(days=5),
        )
        second = ReservationRequest(
            reservation_id="EST-RES-000002",
            possibility_id="EST-POS-000202",
            resource_id="SKU:VOI-READY-001",
            quantity=50,
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=4),
        )

        self.registry.reserve(first)

        with self.assertRaisesRegex(ValueError, "reservation conflict"):
            self.registry.reserve(second)

    def test_non_overlapping_reservation_for_same_resource_is_allowed(self):
        now = datetime.now(timezone.utc)
        first = ReservationRequest(
            reservation_id="EST-RES-000003",
            possibility_id="EST-POS-000203",
            resource_id="CAP:FACTORY-LINE-01",
            quantity=1,
            starts_at=now,
            ends_at=now + timedelta(days=5),
        )
        second = ReservationRequest(
            reservation_id="EST-RES-000004",
            possibility_id="EST-POS-000204",
            resource_id="CAP:FACTORY-LINE-01",
            quantity=1,
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=10),
        )

        self.registry.reserve(first)
        self.registry.reserve(second)

        self.assertEqual(len(self.registry.list_reservations()), 2)


if __name__ == "__main__":
    unittest.main()
