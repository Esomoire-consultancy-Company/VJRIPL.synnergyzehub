import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voi_commercial_intelligence import (
    CommercialIntelligenceValidationError,
    normalize_demand_signals,
    validate_inventory_bundle,
)


class CommercialIntelligenceTests(unittest.TestCase):
    def _bundle(self) -> dict:
        return {
            "schemaVersion": "1.0.0",
            "contract": "VOI-INVENTORY-EVIDENCE-001",
            "sourceMode": "READ_ONLY_EXPORT",
            "bundleId": "sha256:" + "a" * 64,
            "integrity": {
                "algorithm": "SHA-256",
                "digest": "sha256:" + "a" * 64,
                "canonicalPayload": "{}",
            },
            "payload": {
                "observedAt": "2026-09-08T04:30:00Z",
                "demandWindowDays": 14,
                "sources": [],
                "warnings": [],
                "snapshots": [
                    {
                        "sku": "VOI-BLUE-32",
                        "available": 20.0,
                        "avgDailyDemand": 4.0,
                        "confirmedInbound": 0.0,
                        "leadTimeDays": 7,
                        "unitCost": 500.0,
                        "campaignUpliftPct": 0.0,
                        "observedAt": "2026-09-08T04:30:00Z",
                        "evidenceRefs": ["evidence:voi-export:inventory:abc"],
                    },
                    {
                        "sku": "VOI-BLACK-34",
                        "available": 80.0,
                        "avgDailyDemand": 1.0,
                        "confirmedInbound": 10.0,
                        "leadTimeDays": 10,
                        "unitCost": 520.0,
                        "campaignUpliftPct": 0.0,
                        "observedAt": "2026-09-08T04:30:00Z",
                        "evidenceRefs": ["evidence:voi-export:inventory:def"],
                    },
                ],
            },
        }

    def test_rejects_wrong_evidence_contract(self):
        bundle = self._bundle()
        bundle["contract"] = "OTHER-CONTRACT"
        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "VOI-INVENTORY-EVIDENCE-001",
        ):
            validate_inventory_bundle(bundle)

    def test_normalizes_valid_regional_signals(self):
        signals = normalize_demand_signals(
            [
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "8",
                    "observed_at": "2026-09-08T04:00:00Z",
                    "ignored": "drop-me",
                }
            ],
            inventory_bundle=self._bundle(),
        )
        self.assertEqual(
            signals,
            [
                {
                    "sku": "VOI-BLUE-32",
                    "regionId": "BLR-NORTH",
                    "signalType": "PURCHASE",
                    "signalValue": 8.0,
                    "observedAt": "2026-09-08T04:00:00Z",
                }
            ],
        )

    def test_rejects_future_dated_signal(self):
        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "after evidence observation time",
        ):
            normalize_demand_signals(
                [
                    {
                        "sku": "VOI-BLUE-32",
                        "region_id": "BLR-NORTH",
                        "signal_type": "PURCHASE",
                        "signal_value": "1",
                        "observed_at": "2026-09-08T05:00:00Z",
                    }
                ],
                inventory_bundle=self._bundle(),
            )

    def test_rejects_unknown_signal_type(self):
        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "unknown signal type",
        ):
            normalize_demand_signals(
                [
                    {
                        "sku": "VOI-BLUE-32",
                        "region_id": "BLR-NORTH",
                        "signal_type": "LIKE",
                        "signal_value": "1",
                        "observed_at": "2026-09-08T04:00:00Z",
                    }
                ],
                inventory_bundle=self._bundle(),
            )

    def test_rejects_unknown_sku_signal(self):
        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "unknown sku",
        ):
            normalize_demand_signals(
                [
                    {
                        "sku": "VOI-UNKNOWN",
                        "region_id": "BLR-NORTH",
                        "signal_type": "PURCHASE",
                        "signal_value": "1",
                        "observed_at": "2026-09-08T04:00:00Z",
                    }
                ],
                inventory_bundle=self._bundle(),
            )


if __name__ == "__main__":
    unittest.main()
