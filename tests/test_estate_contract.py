import unittest

from estate_contract import (
    Capability,
    Possibility,
    PossibilityState,
    QualificationDecision,
    QualificationGate,
    accept_deal,
    confirm_reality,
    promote_to_proposition,
    qualify_possibility,
)


class EstateContractTests(unittest.TestCase):
    def make_possibility(self, possibility_id="EST-POS-000001", required_capabilities=()):
        return Possibility(
            possibility_id=possibility_id,
            client_id="VOI-CLIENT-001",
            source="Myntra",
            opportunity="Incremental denim growth opportunity",
            owner="marketplace-desk",
            required_capabilities=required_capabilities,
        )

    def qualify(self, possibility):
        gate = QualificationGate(True, True, True, True, True, True)
        self.assertEqual(
            qualify_possibility(possibility, gate),
            QualificationDecision.QUALIFIED,
        )

    def test_qualification_is_conditional_when_any_gate_is_missing(self):
        possibility = self.make_possibility()
        gate = QualificationGate(
            demand=True,
            capability=True,
            economics=True,
            delivery_time=True,
            authority=False,
            measurable_outcome=True,
        )

        decision = qualify_possibility(possibility, gate)

        self.assertEqual(decision, QualificationDecision.CONDITIONAL)
        self.assertEqual(possibility.state, PossibilityState.QUALIFICATION)

    def test_qualified_possibility_can_be_promoted_to_proposition(self):
        possibility = self.make_possibility("EST-POS-000002")
        self.qualify(possibility)

        proposition = promote_to_proposition(
            possibility,
            proposition_id="EST-PROP-000001",
            partner="Myntra",
            success_criteria="Incremental positive contribution",
        )

        self.assertEqual(possibility.state, PossibilityState.PROPOSITION)
        self.assertEqual(proposition.possibility_id, possibility.possibility_id)

    def test_unqualified_possibility_cannot_be_promoted(self):
        possibility = self.make_possibility("EST-POS-000003")

        with self.assertRaisesRegex(ValueError, "QUALIFIED"):
            promote_to_proposition(
                possibility,
                proposition_id="EST-PROP-000002",
                partner="Flipkart",
                success_criteria="Positive contribution",
            )

    def test_required_capability_must_be_available_before_proposition(self):
        possibility = self.make_possibility(
            "EST-POS-000004",
            required_capabilities=("CAP-WH-BLR", "CAP-CHANNEL-MYNTRA"),
        )
        self.qualify(possibility)
        capabilities = [
            Capability("CAP-WH-BLR", "warehouse", True, capacity=10000),
            Capability("CAP-CHANNEL-MYNTRA", "marketplace", False),
        ]

        with self.assertRaisesRegex(ValueError, "unavailable=CAP-CHANNEL-MYNTRA"):
            promote_to_proposition(
                possibility,
                proposition_id="EST-PROP-000003",
                partner="Myntra",
                success_criteria="Sell-through improves",
                capabilities=capabilities,
            )

    def test_deal_requires_commercial_acceptance_evidence(self):
        possibility = self.make_possibility("EST-POS-000005")
        self.qualify(possibility)
        proposition = promote_to_proposition(
            possibility,
            proposition_id="EST-PROP-000004",
            partner="Centro",
            success_criteria="Exclusive range accepted",
        )

        with self.assertRaisesRegex(ValueError, "acceptance evidence"):
            accept_deal(
                possibility,
                proposition,
                deal_id="EST-DEAL-000001",
                acceptance_evidence_ref=" ",
            )

    def test_reality_requires_outcome_evidence(self):
        possibility = self.make_possibility("EST-POS-000006")
        self.qualify(possibility)
        proposition = promote_to_proposition(
            possibility,
            proposition_id="EST-PROP-000005",
            partner="Flipkart",
            success_criteria="Ready goods produce contribution",
        )
        deal = accept_deal(
            possibility,
            proposition,
            deal_id="EST-DEAL-000002",
            acceptance_evidence_ref="river://acceptance/EST-DEAL-000002",
        )

        with self.assertRaisesRegex(ValueError, "Outcome evidence"):
            confirm_reality(
                possibility,
                deal,
                reality_id="EST-REAL-000001",
                outcome_evidence_ref="",
            )


if __name__ == "__main__":
    unittest.main()
