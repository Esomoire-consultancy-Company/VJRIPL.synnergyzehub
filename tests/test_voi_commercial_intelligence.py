import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from commercial_intelligence_bridge import _parse_signal_csv_bytes
from voi_commercial_intelligence import (
    CommercialIntelligenceValidationError,
    build_demand_matrix,
    build_recommendation_ledger,
    build_replenishment_recommendations,
    detect_assortment_risks,
    normalize_demand_signals,
    route_ready_goods,
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

    def test_builds_unscoped_demand_matrix_without_regional_signals(self):
        matrix = build_demand_matrix(self._bundle())
        self.assertEqual({row["regionId"] for row in matrix}, {"UNSCOPED"})
        blue = next(row for row in matrix if row["sku"] == "VOI-BLUE-32")
        black = next(row for row in matrix if row["sku"] == "VOI-BLACK-34")
        self.assertEqual(blue["rawIntent"], 56.0)
        self.assertEqual(blue["demandScore"], 100.0)
        self.assertEqual(black["rawIntent"], 14.0)
        self.assertEqual(black["demandScore"], 25.0)
        self.assertEqual(blue["daysCover"], 5.0)

    def test_scales_regional_demand_scores_deterministically(self):
        signals = normalize_demand_signals(
            [
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PRODUCT_VIEW",
                    "signal_value": "100",
                    "observed_at": "2026-09-08T04:00:00Z",
                },
                {
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "10",
                    "observed_at": "2026-09-08T04:00:00Z",
                },
                {
                    "sku": "VOI-BLACK-34",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "5",
                    "observed_at": "2026-09-08T04:00:00Z",
                },
            ],
            inventory_bundle=self._bundle(),
        )
        matrix = build_demand_matrix(self._bundle(), signals)
        blue = next(row for row in matrix if row["sku"] == "VOI-BLUE-32")
        black = next(row for row in matrix if row["sku"] == "VOI-BLACK-34")
        self.assertEqual(blue["rawIntent"], 15.0)
        self.assertEqual(blue["demandScore"], 100.0)
        self.assertAlmostEqual(black["demandScore"], 33.33333333333333)

    def test_zero_demand_has_null_days_cover(self):
        bundle = self._bundle()
        bundle["payload"]["snapshots"][0]["avgDailyDemand"] = 0.0
        matrix = build_demand_matrix(bundle)
        blue = next(row for row in matrix if row["sku"] == "VOI-BLUE-32")
        self.assertIsNone(blue["daysCover"])

    def test_routes_low_cover_ready_goods_to_replenish(self):
        matrix = build_demand_matrix(self._bundle())
        routes = route_ready_goods(matrix, target_days_cover=14)
        blue = next(row for row in routes if row["sku"] == "VOI-BLUE-32")
        self.assertEqual(blue["routeClass"], "REPLENISH")
        self.assertEqual(blue["routeRule"], "LOW_DAYS_COVER_WITH_READY_GOODS")

    def test_routes_zero_stock_demand_to_investigate(self):
        bundle = self._bundle()
        bundle["payload"]["snapshots"][0]["available"] = 0.0
        bundle["payload"]["snapshots"][0]["confirmedInbound"] = 0.0
        routes = route_ready_goods(build_demand_matrix(bundle))
        blue = next(row for row in routes if row["sku"] == "VOI-BLUE-32")
        self.assertEqual(blue["routeClass"], "INVESTIGATE")
        self.assertEqual(
            blue["routeRule"],
            "DEMAND_WITHOUT_READY_OR_INBOUND_STOCK",
        )

    def test_builds_replenishment_quantity_without_claiming_authority(self):
        routes = route_ready_goods(
            build_demand_matrix(self._bundle()),
            target_days_cover=14,
        )
        recommendations = build_replenishment_recommendations(
            routes,
            target_days_cover=14,
        )
        blue = next(
            item for item in recommendations if item["sku"] == "VOI-BLUE-32"
        )
        self.assertEqual(blue["recommendedQty"], 36.0)
        self.assertEqual(blue["authorityState"], "RECOMMENDED_ONLY")
        self.assertEqual(blue["decisionClass"], "REPLENISH")
        self.assertEqual(
            blue["evidenceRefs"],
            ["evidence:voi-export:inventory:abc"],
        )

    def test_detects_zero_demand_stock_as_slow_stock(self):
        bundle = self._bundle()
        bundle["payload"]["snapshots"][0]["avgDailyDemand"] = 0.0
        risks, capability = detect_assortment_risks(bundle)
        blue = next(item for item in risks if item["sku"] == "VOI-BLUE-32")
        self.assertEqual(blue["riskType"], "SLOW_STOCK")
        self.assertEqual(
            capability["brokenSizeDetection"],
            "INSUFFICIENT_STYLE_SIZE_EVIDENCE",
        )

    def test_does_not_infer_broken_sizes_from_sku_text(self):
        risks, capability = detect_assortment_risks(self._bundle())
        self.assertFalse(any(item["riskType"] == "BROKEN_SIZE" for item in risks))
        self.assertEqual(
            capability["brokenSizeDetection"],
            "INSUFFICIENT_STYLE_SIZE_EVIDENCE",
        )

    def test_detects_broken_sizes_only_with_explicit_lineage(self):
        bundle = self._bundle()
        base = bundle["payload"]["snapshots"][0]
        bundle["payload"]["snapshots"] = [
            {
                **base,
                "sku": "S32",
                "styleId": "STYLE-1",
                "size": "32",
                "available": 10.0,
            },
            {
                **base,
                "sku": "S34",
                "styleId": "STYLE-1",
                "size": "34",
                "available": 0.0,
            },
            {
                **base,
                "sku": "S36",
                "styleId": "STYLE-1",
                "size": "36",
                "available": 12.0,
            },
        ]
        risks, capability = detect_assortment_risks(bundle)
        broken = next(item for item in risks if item["riskType"] == "BROKEN_SIZE")
        self.assertEqual(broken["styleId"], "STYLE-1")
        self.assertEqual(broken["missingSizes"], ["34"])
        self.assertEqual(capability["brokenSizeDetection"], "AVAILABLE")

    def test_intelligence_ledger_is_deterministic_and_evidence_linked(self):
        bundle = self._bundle()
        routes = route_ready_goods(build_demand_matrix(bundle))
        recommendations = build_replenishment_recommendations(routes)
        risks, capability = detect_assortment_risks(bundle)
        first = build_recommendation_ledger(
            bundle,
            recommendations,
            risks,
            capability,
        )
        second = build_recommendation_ledger(
            copy.deepcopy(bundle),
            copy.deepcopy(recommendations),
            copy.deepcopy(risks),
            copy.deepcopy(capability),
        )
        self.assertEqual(first, second)
        self.assertEqual(first["contract"], "VOI-COMMERCIAL-INTELLIGENCE-001")
        self.assertEqual(first["modelVersion"], "VOI-CI-R0.1")
        self.assertEqual(first["sourceBundleId"], bundle["bundleId"])
        self.assertEqual(
            first["evidenceObservedAt"],
            bundle["payload"]["observedAt"],
        )
        self.assertNotIn("generatedAt", first)
        self.assertEqual(first["integrity"]["digest"], first["ledgerId"])
        for recommendation in first["recommendations"]:
            self.assertTrue(recommendation["recommendationId"].startswith("sha256:"))
            self.assertEqual(recommendation["authorityState"], "RECOMMENDED_ONLY")
            self.assertTrue(recommendation["evidenceRefs"])

    def test_commercial_intelligence_module_has_no_external_io_imports(self):
        source = (ROOT / "voi_commercial_intelligence.py").read_text(
            encoding="utf-8"
        )
        forbidden = [
            "requests",
            "httpx",
            "urllib.request",
            "subprocess",
            "socket",
            "sqlalchemy",
            "psycopg",
        ]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_signal_csv_parser_returns_source_rows(self):
        rows = _parse_signal_csv_bytes(
            b"sku,region_id,signal_type,signal_value,observed_at\n"
            b"VOI-BLUE-32,BLR-NORTH,PURCHASE,2,2026-09-08T04:00:00Z\n"
        )
        self.assertEqual(rows[0]["region_id"], "BLR-NORTH")
        self.assertEqual(rows[0]["signal_value"], "2")


if __name__ == "__main__":
    unittest.main()
