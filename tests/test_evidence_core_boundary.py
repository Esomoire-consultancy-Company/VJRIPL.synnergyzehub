import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voi_evidence_adapter import build_inventory_evidence_bundle


class EvidenceCoreBoundaryTests(unittest.TestCase):
    GOLDEN_MINIMAL_BUNDLE_ID = (
        "sha256:b91c926657c36ec6ba8dc19fe4d3fe11cbee082211b3e5e8742d2e1f92e10c02"
    )

    def _write(self, root: Path, name: str, content: str) -> Path:
        path = root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_generic_evidence_core_exists(self):
        self.assertTrue(
            (ROOT / "evidence_core.py").is_file(),
            "Issue #19 requires an internal client-neutral evidence_core.py module",
        )

    def test_voi_adapter_delegates_generic_mechanics_to_core(self):
        source = (ROOT / "voi_evidence_adapter.py").read_text(encoding="utf-8")
        self.assertIn("from evidence_core import", source)

    def test_generic_core_contains_no_client_or_provider_constants(self):
        path = ROOT / "evidence_core.py"
        self.assertTrue(path.is_file(), "evidence_core.py must exist before neutrality can be proven")
        source = path.read_text(encoding="utf-8").lower()
        forbidden = (
            "voi",
            "logic",
            "easycom",
            "myntra",
            "flipkart",
            "centro",
            "evidence:voi-export",
            "voi-inventory-evidence-001",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_minimal_voi_bundle_digest_is_contract_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
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

            bundle = build_inventory_evidence_bundle(inventory, sales, products)
            self.assertEqual(bundle["contract"], "VOI-INVENTORY-EVIDENCE-001")
            self.assertEqual(bundle["sourceMode"], "READ_ONLY_EXPORT")
            self.assertEqual(bundle["bundleId"], self.GOLDEN_MINIMAL_BUNDLE_ID)
            self.assertEqual(bundle["integrity"]["digest"], self.GOLDEN_MINIMAL_BUNDLE_ID)


if __name__ == "__main__":
    unittest.main()
