import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from estate_registry import (
    DealRecord,
    EstateRegistry,
    ExecutionIntentRecord,
    PossibilityRecord,
    PropositionRecord,
)


def make_bundle(*, tamper=False):
    payload = {
        "observedAt": "2026-09-08T04:00:00Z",
        "demandWindowDays": 14,
        "sources": [],
        "warnings": [],
        "snapshots": [
            {
                "sku": "VOI-TEST-001",
                "available": 100.0,
                "avgDailyDemand": 5.0,
                "confirmedInbound": 0.0,
                "leadTimeDays": 14,
                "unitCost": 500.0,
                "campaignUpliftPct": 0.0,
                "observedAt": "2026-09-08T04:00:00Z",
                "evidenceRefs": [],
            }
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
    bundle = {
        "schemaVersion": "1.0.0",
        "contract": "VOI-INVENTORY-EVIDENCE-001",
        "sourceMode": "READ_ONLY_EXPORT",
        "payload": payload,
        "integrity": {
            "algorithm": "SHA-256",
            "digest": digest,
            "canonicalPayload": canonical,
        },
        "bundleId": digest,
    }
    if tamper:
        bundle["payload"]["snapshots"][0]["available"] = 999.0
    return bundle


class EstateGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = EstateRegistry(Path(self.tmp.name) / "estate.db")
        self.registry.upsert_possibility(
            PossibilityRecord(
                possibility_id="EST-POS-000101",
                client_id="VOI-CLIENT-001",
                source="Myntra",
                opportunity="Qualified denim growth opportunity",
                owner="marketplace-desk",
                state="QUALIFIED",
                evidence_refs=("evidence:source:market-signal-001",),
            )
        )

    def tearDown(self):
        self.registry.close()
        self.tmp.cleanup()

    def test_register_inventory_evidence_bundle_verifies_integrity(self):
        bundle = make_bundle()

        record = self.registry.register_inventory_evidence_bundle(bundle)

        self.assertEqual(record.bundle_id, bundle["bundleId"])
        self.assertEqual(record.contract, "VOI-INVENTORY-EVIDENCE-001")
        self.assertEqual(record.source_mode, "READ_ONLY_EXPORT")

    def test_register_inventory_evidence_bundle_rejects_tampered_payload(self):
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.registry.register_inventory_evidence_bundle(make_bundle(tamper=True))

    def test_proposition_requires_qualified_persisted_possibility_and_registered_bundle(self):
        bundle = make_bundle()
        self.registry.register_inventory_evidence_bundle(bundle)

        proposition = self.registry.create_proposition(
            PropositionRecord(
                proposition_id="EST-PROP-000101",
                possibility_id="EST-POS-000101",
                partner="Myntra",
                success_criteria="Positive incremental contribution",
                evidence_bundle_id=bundle["bundleId"],
            )
        )

        self.assertEqual(proposition.possibility_id, "EST-POS-000101")
        self.assertEqual(self.registry.get_proposition("EST-PROP-000101"), proposition)

    def test_proposition_rejects_unqualified_possibility(self):
        self.registry.upsert_possibility(
            PossibilityRecord(
                possibility_id="EST-POS-000102",
                client_id="VOI-CLIENT-001",
                source="Flipkart",
                opportunity="Still qualifying",
                owner="marketplace-desk",
                state="QUALIFICATION",
            )
        )
        bundle = make_bundle()
        self.registry.register_inventory_evidence_bundle(bundle)

        with self.assertRaisesRegex(ValueError, "QUALIFIED"):
            self.registry.create_proposition(
                PropositionRecord(
                    proposition_id="EST-PROP-000102",
                    possibility_id="EST-POS-000102",
                    partner="Flipkart",
                    success_criteria="Positive contribution",
                    evidence_bundle_id=bundle["bundleId"],
                )
            )

    def test_deal_requires_acceptance_warden_and_river_references(self):
        bundle = make_bundle()
        self.registry.register_inventory_evidence_bundle(bundle)
        self.registry.create_proposition(
            PropositionRecord(
                proposition_id="EST-PROP-000103",
                possibility_id="EST-POS-000101",
                partner="Myntra",
                success_criteria="Positive contribution",
                evidence_bundle_id=bundle["bundleId"],
            )
        )

        with self.assertRaisesRegex(ValueError, "Warden"):
            self.registry.accept_deal(
                DealRecord(
                    deal_id="EST-DEAL-000101",
                    proposition_id="EST-PROP-000103",
                    acceptance_evidence_ref="river://acceptance/101",
                    warden_decision_ref="",
                    river_receipt_ref="river://transition/101",
                )
            )

    def test_execution_intent_requires_governance_and_idempotency_and_has_no_effect_state(self):
        bundle = make_bundle()
        self.registry.register_inventory_evidence_bundle(bundle)
        self.registry.create_proposition(
            PropositionRecord(
                proposition_id="EST-PROP-000104",
                possibility_id="EST-POS-000101",
                partner="Myntra",
                success_criteria="Positive contribution",
                evidence_bundle_id=bundle["bundleId"],
            )
        )
        deal = self.registry.accept_deal(
            DealRecord(
                deal_id="EST-DEAL-000102",
                proposition_id="EST-PROP-000104",
                acceptance_evidence_ref="river://acceptance/102",
                warden_decision_ref="warden://decision/102",
                river_receipt_ref="river://transition/102",
            )
        )

        with self.assertRaisesRegex(ValueError, "idempotency"):
            self.registry.create_execution_intent(
                ExecutionIntentRecord(
                    execution_intent_id="EST-EXEC-000101",
                    deal_id=deal.deal_id,
                    warden_decision_ref="warden://decision/exec-101",
                    river_receipt_ref="river://intent/101",
                    idempotency_key="",
                )
            )

        intent = self.registry.create_execution_intent(
            ExecutionIntentRecord(
                execution_intent_id="EST-EXEC-000102",
                deal_id=deal.deal_id,
                warden_decision_ref="warden://decision/exec-102",
                river_receipt_ref="river://intent/102",
                idempotency_key="estate-exec-102",
            )
        )

        self.assertEqual(intent.effect_state, "NO_EXTERNAL_EFFECT")
        self.assertEqual(self.registry.get_execution_intent(intent.execution_intent_id), intent)


if __name__ == "__main__":
    unittest.main()
