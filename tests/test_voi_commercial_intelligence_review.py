import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voi_commercial_intelligence import (
    CommercialIntelligenceValidationError,
    validate_inventory_bundle,
)


def _reseal(bundle: dict) -> dict:
    canonical = json.dumps(
        bundle["payload"],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    digest = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    bundle["integrity"] = {
        "algorithm": "SHA-256",
        "digest": digest,
        "canonicalPayload": canonical,
    }
    bundle["bundleId"] = digest
    return bundle


def _sealed_bundle() -> dict:
    bundle = {
        "schemaVersion": "1.0.0",
        "contract": "VOI-INVENTORY-EVIDENCE-001",
        "sourceMode": "READ_ONLY_EXPORT",
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
                }
            ],
        },
    }
    return _reseal(bundle)


class ReviewRegressionTests(unittest.TestCase):
    def test_rejects_payload_tampering_even_with_sha256_prefixed_bundle_id(self):
        bundle = _sealed_bundle()
        tampered = copy.deepcopy(bundle)
        tampered["payload"]["snapshots"][0]["available"] = 9999.0

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "integrity digest mismatch",
        ):
            validate_inventory_bundle(tampered)

    def test_rejects_fractional_lead_time_days(self):
        bundle = _sealed_bundle()
        bundle["payload"]["snapshots"][0]["leadTimeDays"] = 1.9
        _reseal(bundle)

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "leadTimeDays must be an integer",
        ):
            validate_inventory_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
