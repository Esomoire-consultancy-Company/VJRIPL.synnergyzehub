import json
import tempfile
import unittest
from pathlib import Path

from voi_evidence_adapter import EvidenceValidationError, build_inventory_evidence_bundle


class EvidenceAdapterTests(unittest.TestCase):
    def _write(self, root: Path, name: str, content: str) -> Path:
        path = root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_builds_read_only_inventory_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(root, "inventory.csv", """sku,available_qty,observed_at
VOI-RED-M,300,2026-08-15T06:20:00Z
VOI-BLUE-L,120,2026-08-15T06:20:00Z
""")
            sales = self._write(root, "sales.csv", """sku,units_sold,sales_date
VOI-RED-M,70,2026-08-15
VOI-RED-M,56,2026-08-14
VOI-BLUE-L,28,2026-08-15
""")
            products = self._write(root, "product.csv", """sku,unit_cost,lead_time_days,campaign_uplift_pct
VOI-RED-M,450,10,38
VOI-BLUE-L,500,7,0
""")
            orders = self._write(root, "orders.csv", """sku,inbound_qty,expected_date
VOI-RED-M,100,2026-08-20
VOI-BLUE-L,50,2026-08-14
""")

            bundle = build_inventory_evidence_bundle(inventory, sales, products, orders)
            self.assertEqual(bundle["contract"], "VOI-INVENTORY-EVIDENCE-001")
            self.assertEqual(bundle["sourceMode"], "READ_ONLY_EXPORT")
            self.assertTrue(bundle["bundleId"].startswith("sha256:"))
            self.assertEqual(bundle["integrity"]["algorithm"], "SHA-256")
            self.assertEqual(bundle["integrity"]["digest"], bundle["bundleId"])
            self.assertEqual(len(bundle["payload"]["sources"]), 4)
            self.assertEqual(len(bundle["payload"]["snapshots"]), 2)
            red = next(item for item in bundle["payload"]["snapshots"] if item["sku"] == "VOI-RED-M")
            blue = next(item for item in bundle["payload"]["snapshots"] if item["sku"] == "VOI-BLUE-L")
            self.assertEqual(red["available"], 300)
            self.assertEqual(red["confirmedInbound"], 100)
            self.assertAlmostEqual(red["avgDailyDemand"], 9.0)
            self.assertEqual(red["leadTimeDays"], 10)
            self.assertEqual(red["campaignUpliftPct"], 38)
            self.assertEqual(blue["confirmedInbound"], 0)
            self.assertEqual(len(bundle["payload"]["warnings"]), 1)
            self.assertIn("overdue open order excluded", bundle["payload"]["warnings"][0])
            for source in bundle["payload"]["sources"]:
                self.assertTrue(source["evidenceRef"].startswith("evidence:voi-export:"))
                self.assertEqual(len(source["sha256"]), 64)

    def test_rejects_future_sales(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(root, "inventory.csv", """sku,available_qty,observed_at
VOI-RED-M,300,2026-08-15T06:20:00Z
""")
            sales = self._write(root, "sales.csv", """sku,units_sold,sales_date
VOI-RED-M,70,2026-08-16
""")
            products = self._write(root, "product.csv", """sku,unit_cost,lead_time_days
VOI-RED-M,450,10
""")
            with self.assertRaisesRegex(EvidenceValidationError, "after inventory observation time"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_rejects_unknown_sku(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(root, "inventory.csv", """sku,available_qty,observed_at
VOI-UNKNOWN,10,2026-08-15T06:20:00Z
""")
            sales = self._write(root, "sales.csv", """sku,units_sold,sales_date
VOI-UNKNOWN,1,2026-08-15
""")
            products = self._write(root, "product.csv", """sku,unit_cost,lead_time_days
VOI-RED-M,450,10
""")
            with self.assertRaisesRegex(EvidenceValidationError, "inventory sku not found"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_bundle_id_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(root, "inventory.csv", """sku,available_qty,observed_at
VOI-RED-M,300,2026-08-15T06:20:00Z
""")
            sales = self._write(root, "sales.csv", """sku,units_sold,sales_date
VOI-RED-M,70,2026-08-15
""")
            products = self._write(root, "product.csv", """sku,unit_cost,lead_time_days
VOI-RED-M,450,10
""")
            first = build_inventory_evidence_bundle(inventory, sales, products)
            second = build_inventory_evidence_bundle(inventory, sales, products)
            self.assertEqual(first["bundleId"], second["bundleId"])
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
