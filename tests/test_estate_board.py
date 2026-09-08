import unittest
from datetime import datetime, timedelta, timezone

from estate_board import build_board_summary, channel_template
from estate_registry import PossibilityRecord


class EstateBoardTests(unittest.TestCase):
    def test_myntra_template_requires_logic_easycom_and_myntra_channel(self):
        template = channel_template("Myntra")

        self.assertEqual(template.partner, "Myntra")
        self.assertIn("CAP-ERP-LOGIC", template.required_capabilities)
        self.assertIn("CAP-OMS-EASYCOM", template.required_capabilities)
        self.assertIn("CAP-CHANNEL-MYNTRA", template.required_capabilities)
        self.assertIn("incremental", template.objective.lower())

    def test_flipkart_template_uses_flipkart_channel(self):
        template = channel_template("Flipkart")

        self.assertEqual(template.partner, "Flipkart")
        self.assertIn("CAP-CHANNEL-FLIPKART", template.required_capabilities)

    def test_centro_template_uses_retail_channel(self):
        template = channel_template("Centro")

        self.assertEqual(template.partner, "Centro")
        self.assertIn("CAP-CHANNEL-CENTRO", template.required_capabilities)
        self.assertIn("assortment", template.objective.lower())

    def test_board_summary_counts_value_contribution_and_expiry(self):
        now = datetime.now(timezone.utc)
        possibilities = [
            PossibilityRecord(
                possibility_id="EST-POS-000301",
                client_id="VOI-CLIENT-001",
                source="Myntra",
                opportunity="A",
                owner="desk-a",
                estimated_value=1_000_000,
                estimated_contribution=200_000,
                expires_at=now + timedelta(days=10),
            ),
            PossibilityRecord(
                possibility_id="EST-POS-000302",
                client_id="VOI-CLIENT-001",
                source="Centro",
                opportunity="B",
                owner="desk-b",
                estimated_value=500_000,
                estimated_contribution=50_000,
                expires_at=now - timedelta(days=1),
            ),
        ]

        summary = build_board_summary(possibilities, observed_at=now)

        self.assertEqual(summary.possibility_count, 2)
        self.assertEqual(summary.estimated_value, 1_500_000)
        self.assertEqual(summary.estimated_contribution, 250_000)
        self.assertEqual(summary.expired_count, 1)


if __name__ == "__main__":
    unittest.main()
