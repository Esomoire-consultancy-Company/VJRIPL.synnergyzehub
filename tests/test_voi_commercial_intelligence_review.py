import copy
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voi_commercial_intelligence import (
    MODEL_VERSION,
    CommercialIntelligenceValidationError,
    build_demand_matrix,
    build_recommendation_ledger,
    build_replenishment_recommendations,
    detect_assortment_risks,
    normalize_demand_signals,
    route_ready_goods,
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

    def test_rejects_non_object_snapshot_with_contract_error(self):
        bundle = _sealed_bundle()
        bundle["payload"]["snapshots"] = ["not-an-object"]
        _reseal(bundle)

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "snapshot\\[0\\] must be an object",
        ):
            validate_inventory_bundle(bundle)

    def test_rejects_non_utf8_signal_csv_with_contract_error(self):
        from commercial_intelligence_bridge import _parse_signal_csv_bytes

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "must be UTF-8",
        ):
            _parse_signal_csv_bytes(b"\xff\xfe\xfa")

    def test_regional_signals_drive_effective_demand_without_global_leakage(self):
        bundle = _sealed_bundle()
        blue = bundle["payload"]["snapshots"][0]
        blue["available"] = 5.0
        blue["avgDailyDemand"] = 0.0

        black = copy.deepcopy(blue)
        black["sku"] = "VOI-BLACK-34"
        black["available"] = 5.0
        black["avgDailyDemand"] = 10.0
        black["evidenceRefs"] = ["evidence:voi-export:inventory:def"]
        bundle["payload"]["snapshots"].append(black)
        _reseal(bundle)

        signals = normalize_demand_signals(
            [
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "28",
                    "observed_at": "2026-09-08T04:00:00Z",
                }
            ],
            inventory_bundle=bundle,
        )
        matrix = build_demand_matrix(bundle, signals)
        routes = route_ready_goods(matrix, target_days_cover=14)

        blue_row = next(row for row in routes if row["sku"] == "VOI-BLUE-32")
        black_row = next(row for row in routes if row["sku"] == "VOI-BLACK-34")

        self.assertEqual(blue_row["baselineAvgDailyDemand"], 0.0)
        self.assertEqual(blue_row["effectiveDailyDemand"], 2.0)
        self.assertEqual(blue_row["demandBasis"], "REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE")
        self.assertEqual(blue_row["routeClass"], "REPLENISH")

        self.assertEqual(black_row["baselineAvgDailyDemand"], 10.0)
        self.assertEqual(black_row["effectiveDailyDemand"], 0.0)
        self.assertEqual(black_row["routeClass"], "HOLD")

    def test_inbound_only_low_cover_routes_to_replenish(self):
        bundle = _sealed_bundle()
        snapshot = bundle["payload"]["snapshots"][0]
        snapshot["available"] = 0.0
        snapshot["confirmedInbound"] = 2.0
        snapshot["avgDailyDemand"] = 1.0
        _reseal(bundle)

        route = route_ready_goods(
            build_demand_matrix(bundle),
            target_days_cover=14,
        )[0]
        self.assertEqual(route["routeClass"], "REPLENISH")
        self.assertEqual(route["routeRule"], "LOW_DAYS_COVER_WITH_INBOUND_ONLY")

    def test_replenishment_recommendation_is_self_describing(self):
        routes = route_ready_goods(build_demand_matrix(_sealed_bundle()))
        recommendation = build_replenishment_recommendations(routes)[0]
        self.assertEqual(recommendation["modelVersion"], MODEL_VERSION)

    def test_rejects_non_string_timestamp_with_contract_error(self):
        bundle = _sealed_bundle()
        bundle["payload"]["observedAt"] = 12345
        _reseal(bundle)

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "payload.observedAt must be an ISO-8601 string",
        ):
            validate_inventory_bundle(bundle)

    def test_rejects_nan_payload_with_contract_error(self):
        bundle = _sealed_bundle()
        bundle["payload"]["snapshots"][0]["available"] = math.nan

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "canonical JSON",
        ):
            validate_inventory_bundle(bundle)

    def test_rejects_non_string_snapshot_sku(self):
        bundle = _sealed_bundle()
        bundle["payload"]["snapshots"][0]["sku"] = 123
        _reseal(bundle)

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "snapshot\\[0\\].sku must be a string",
        ):
            validate_inventory_bundle(bundle)

    def test_rejects_non_string_evidence_reference(self):
        bundle = _sealed_bundle()
        bundle["payload"]["snapshots"][0]["evidenceRefs"] = [123]
        _reseal(bundle)

        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "evidenceRefs must contain strings",
        ):
            validate_inventory_bundle(bundle)

    def test_regional_recommendations_do_not_double_count_shared_stock(self):
        bundle = _sealed_bundle()
        signals = normalize_demand_signals(
            [
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "56",
                    "observed_at": "2026-09-08T04:00:00Z",
                },
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-SOUTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "56",
                    "observed_at": "2026-09-08T04:00:00Z",
                },
            ],
            inventory_bundle=bundle,
        )
        routes = route_ready_goods(build_demand_matrix(bundle, signals))
        recommendations = build_replenishment_recommendations(routes)

        self.assertEqual(len(recommendations), 2)
        for recommendation in recommendations:
            self.assertIsNone(recommendation["recommendedQty"])
            self.assertEqual(
                recommendation["quantityState"],
                "UNQUANTIFIED_SHARED_STOCK",
            )

    def test_replenishment_rejects_non_positive_target_cover(self):
        routes = route_ready_goods(build_demand_matrix(_sealed_bundle()))
        with self.assertRaisesRegex(
            CommercialIntelligenceValidationError,
            "target_days_cover must be >= 1",
        ):
            build_replenishment_recommendations(routes, target_days_cover=0)

    def test_ledger_overrides_supplied_recommendation_id(self):
        bundle = _sealed_bundle()
        routes = route_ready_goods(build_demand_matrix(bundle))
        recommendations = build_replenishment_recommendations(routes)
        recommendations[0]["recommendationId"] = "sha256:attacker-controlled"
        risks, capability = detect_assortment_risks(bundle)

        ledger = build_recommendation_ledger(
            bundle,
            recommendations,
            risks,
            capability,
        )
        emitted_id = ledger["recommendations"][0]["recommendationId"]
        self.assertNotEqual(emitted_id, "sha256:attacker-controlled")
        self.assertTrue(emitted_id.startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
