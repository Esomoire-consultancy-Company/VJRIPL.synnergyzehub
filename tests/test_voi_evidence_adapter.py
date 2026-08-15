import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from export_voi_inventory_evidence import main as export_main
from inventory_evidence_bridge import _persist_upload
from voi_evidence_adapter import EvidenceValidationError, build_inventory_evidence_bundle


class FakeUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


class EvidenceAdapterTests(unittest.TestCase):
    def _write(self, root: Path, name: str, content: str) -> Path:
        path = root / name
        path.write_text(content, encoding="utf-8")
        return path

    def _minimal_sources(self, root: Path):
        inventory = self._write(
            root,
            "inventory.csv",
            "sku,available_qty,observed_at\nVOI-RED-M,300,2026-08-15T06:20:00Z\n",
        )
        sales = self._write(
            root,
            "sales.csv",
            "sku,units_sold,sales_date\nVOI-RED-M,70,2026-08-15\n",
        )
        products = self._write(
            root,
            "product.csv",
            "sku,unit_cost,lead_time_days\nVOI-RED-M,450,10\n",
        )
        return inventory, sales, products

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
            inventory, _, products = self._minimal_sources(root)
            sales = self._write(
                root,
                "future_sales.csv",
                "sku,units_sold,sales_date\nVOI-RED-M,70,2026-08-16\n",
            )
            with self.assertRaisesRegex(EvidenceValidationError, "after inventory observation time"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_rejects_unknown_sku(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(
                root,
                "inventory.csv",
                "sku,available_qty,observed_at\nVOI-UNKNOWN,10,2026-08-15T06:20:00Z\n",
            )
            sales = self._write(
                root,
                "sales.csv",
                "sku,units_sold,sales_date\nVOI-UNKNOWN,1,2026-08-15\n",
            )
            products = self._write(
                root,
                "product.csv",
                "sku,unit_cost,lead_time_days\nVOI-RED-M,450,10\n",
            )
            with self.assertRaisesRegex(EvidenceValidationError, "inventory sku not found"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_bundle_id_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory, sales, products = self._minimal_sources(root)
            first = build_inventory_evidence_bundle(inventory, sales, products)
            second = build_inventory_evidence_bundle(inventory, sales, products)
            self.assertEqual(first["bundleId"], second["bundleId"])
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_rejects_non_finite_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(
                root,
                "inventory.csv",
                "sku,available_qty,observed_at\nVOI-RED-M,nan,2026-08-15T06:20:00Z\n",
            )
            _, sales, products = self._minimal_sources(root)
            with self.assertRaisesRegex(EvidenceValidationError, "must be finite"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_rejects_mixed_inventory_observation_times(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(root, "inventory.csv", """sku,available_qty,observed_at
VOI-RED-M,100,2026-08-15T06:20:00Z
VOI-RED-M,200,2026-08-15T06:25:00Z
""")
            _, sales, products = self._minimal_sources(root)
            with self.assertRaisesRegex(EvidenceValidationError, "must share one observed_at timestamp"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_timezone_offsets_are_converted_to_utc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(
                root,
                "inventory.csv",
                "sku,available_qty,observed_at\nVOI-RED-M,300,2026-08-15T20:00:00Z\n",
            )
            sales = self._write(
                root,
                "sales.csv",
                "sku,units_sold,sales_date\nVOI-RED-M,70,2026-08-16T00:30:00+05:30\n",
            )
            products = self._write(
                root,
                "product.csv",
                "sku,unit_cost,lead_time_days\nVOI-RED-M,450,10\n",
            )
            bundle = build_inventory_evidence_bundle(inventory, sales, products)
            snapshot = bundle["payload"]["snapshots"][0]
            self.assertAlmostEqual(snapshot["avgDailyDemand"], 5.0)

    def test_embedded_newline_in_quoted_field_is_preserved_by_csv_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory, sales, _ = self._minimal_sources(root)
            products = self._write(
                root,
                "product.csv",
                'sku,unit_cost,lead_time_days,note\nVOI-RED-M,450,10,"line one\nline two"\n',
            )
            bundle = build_inventory_evidence_bundle(inventory, sales, products)
            self.assertEqual(len(bundle["payload"]["snapshots"]), 1)

    def test_rejects_extra_csv_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = self._write(
                root,
                "inventory.csv",
                "sku,available_qty,observed_at\nVOI-RED-M,300,2026-08-15T06:20:00Z,EXTRA\n",
            )
            _, sales, products = self._minimal_sources(root)
            with self.assertRaisesRegex(EvidenceValidationError, "more fields than the header"):
                build_inventory_evidence_bundle(inventory, sales, products)

    def test_validates_headers_for_empty_open_orders_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory, sales, products = self._minimal_sources(root)
            orders = self._write(root, "orders.csv", "sku,inbound_qty\n")
            with self.assertRaisesRegex(EvidenceValidationError, "missing required columns: expected_date"):
                build_inventory_evidence_bundle(inventory, sales, products, orders)

    def test_same_upload_filename_uses_distinct_source_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory = _persist_upload(root, FakeUpload("export.csv", b"inventory"), "inventory")
            sales = _persist_upload(root, FakeUpload("export.csv", b"sales"), "sales")
            self.assertNotEqual(inventory, sales)
            self.assertEqual(inventory.read_bytes(), b"inventory")
            self.assertEqual(sales.read_bytes(), b"sales")

    def test_cli_export_completes_and_writes_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inventory, sales, products = self._minimal_sources(root)
            destination = root / "bundle.json"
            argv = [
                "export_voi_inventory_evidence.py",
                "--inventory",
                str(inventory),
                "--sales",
                str(sales),
                "--product-master",
                str(products),
                "--out",
                str(destination),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(export_main(), 0)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["payload"]["snapshots"]), 1)


if __name__ == "__main__":
    unittest.main()
