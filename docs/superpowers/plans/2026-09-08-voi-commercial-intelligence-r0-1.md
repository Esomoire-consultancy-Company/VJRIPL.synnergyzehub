# VOI Commercial Intelligence R0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build deterministic, evidence-linked VOI commercial-intelligence recommendations from the existing read-only `VOI-INVENTORY-EVIDENCE-001` bundle without creating any operational write path.

**Architecture:** Add a pure-Python intelligence module above the existing evidence adapter, then expose it through a read-only Streamlit bridge. The core module validates evidence and optional demand signals, derives demand/routing/replenishment/assortment outputs, and emits a canonical SHA-256 recommendation ledger. Existing evidence parsing remains unchanged and authoritative.

**Tech Stack:** Python 3.11+, standard library, Streamlit 1.44+, pandas 2.2+, `unittest`, uv/`uv.lock`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-08-voi-commercial-intelligence-r0-1-design.md`

## Global Constraints

- R0.1 is recommendation-only; it must not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, payments, BNR, or ARK state.
- Consume only the existing `VOI-INVENTORY-EVIDENCE-001` contract; do not duplicate CSV evidence parsing in the intelligence engine.
- All intelligence heuristics are deterministic and versioned as `VOI-CI-R0.1`.
- Every recommendation must carry source evidence references and `authorityState: RECOMMENDED_ONLY`.
- The canonical intelligence output must be byte-stable for identical inputs; wall-clock generation time is excluded.
- Missing region evidence is represented as `UNSCOPED`; missing style/size evidence is represented explicitly and never inferred from SKU strings.
- Existing evidence-adapter tests remain a hard regression gate.

---

## File Structure

- Create `voi_commercial_intelligence.py` — pure intelligence contract and algorithms; no Streamlit and no external I/O.
- Create `commercial_intelligence_bridge.py` — read-only Streamlit UI and optional CSV signal upload parsing.
- Create `tests/test_voi_commercial_intelligence.py` — all R0.1 contract and algorithm tests in existing `unittest` style.
- Modify `inventory_evidence_bridge.py` — retain the exact validated evidence bundle in session state after successful validation.
- Modify `app.py` — add Commercial Intelligence navigation and routing.
- Modify `pyproject.toml` — register the two new Python modules for packaging.
- Modify `.github/workflows/voi-evidence-bridge.yml` — compile the new modules and prove both direct test entrypoints.

---

### Task 1: Evidence Contract Validation and CI-001 Demand Signal Normalizer

**Files:**
- Create: `voi_commercial_intelligence.py`
- Create: `tests/test_voi_commercial_intelligence.py`

**Interfaces:**
- Consumes: an in-memory `dict` produced by `build_inventory_evidence_bundle(...)`.
- Produces:
  - `CommercialIntelligenceValidationError(ValueError)`
  - `validate_inventory_bundle(bundle: dict) -> dict`
  - `normalize_demand_signals(rows: list[dict[str, str]], *, inventory_bundle: dict) -> list[dict]`

- [ ] **Step 1: Write the failing validation and signal tests**

Add the shared fixture and first tests:

```python
import copy
import math
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
        with self.assertRaisesRegex(CommercialIntelligenceValidationError, "VOI-INVENTORY-EVIDENCE-001"):
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
        with self.assertRaisesRegex(CommercialIntelligenceValidationError, "after evidence observation time"):
            normalize_demand_signals(
                [{
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "1",
                    "observed_at": "2026-09-08T05:00:00Z",
                }],
                inventory_bundle=self._bundle(),
            )

    def test_rejects_unknown_signal_type(self):
        with self.assertRaisesRegex(CommercialIntelligenceValidationError, "unknown signal type"):
            normalize_demand_signals(
                [{
                    "sku": "VOI-BLUE-32",
                    "region_id": "BLR-NORTH",
                    "signal_type": "LIKE",
                    "signal_value": "1",
                    "observed_at": "2026-09-08T04:00:00Z",
                }],
                inventory_bundle=self._bundle(),
            )

    def test_rejects_unknown_sku_signal(self):
        with self.assertRaisesRegex(CommercialIntelligenceValidationError, "unknown sku"):
            normalize_demand_signals(
                [{
                    "sku": "VOI-UNKNOWN",
                    "region_id": "BLR-NORTH",
                    "signal_type": "PURCHASE",
                    "signal_value": "1",
                    "observed_at": "2026-09-08T04:00:00Z",
                }],
                inventory_bundle=self._bundle(),
            )
```

- [ ] **Step 2: Run the new test file and verify RED**

Run:

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: import failure because `voi_commercial_intelligence.py` does not yet exist.

- [ ] **Step 3: Implement minimal validation and normalization**

Create `voi_commercial_intelligence.py` with standard-library imports only:

```python
from __future__ import annotations

import math
from datetime import datetime, timezone


MODEL_VERSION = "VOI-CI-R0.1"
EVIDENCE_CONTRACT = "VOI-INVENTORY-EVIDENCE-001"
ALLOWED_SIGNAL_TYPES = {
    "PRODUCT_VIEW",
    "ADD_TO_CART",
    "PURCHASE",
    "RETURN",
    "STOCKOUT",
}
REQUIRED_SNAPSHOT_FIELDS = {
    "sku",
    "available",
    "avgDailyDemand",
    "confirmedInbound",
    "leadTimeDays",
    "unitCost",
    "campaignUpliftPct",
    "observedAt",
    "evidenceRefs",
}


class CommercialIntelligenceValidationError(ValueError):
    pass


def _parse_datetime(value: str, field: str) -> datetime:
    text = (value or "").strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CommercialIntelligenceValidationError(f"{field} must be ISO-8601: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite_non_negative(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CommercialIntelligenceValidationError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise CommercialIntelligenceValidationError(f"{field} must be finite and non-negative")
    return number


def validate_inventory_bundle(bundle: dict) -> dict:
    if not isinstance(bundle, dict) or bundle.get("contract") != EVIDENCE_CONTRACT:
        raise CommercialIntelligenceValidationError(f"expected contract {EVIDENCE_CONTRACT}")
    payload = bundle.get("payload")
    if not isinstance(payload, dict):
        raise CommercialIntelligenceValidationError("payload is required")
    if not isinstance(bundle.get("bundleId"), str) or not bundle["bundleId"].startswith("sha256:"):
        raise CommercialIntelligenceValidationError("bundleId must be a sha256 digest")
    observed_at = payload.get("observedAt")
    _parse_datetime(observed_at, "payload.observedAt")
    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise CommercialIntelligenceValidationError("payload.snapshots must be a non-empty list")
    seen = set()
    for index, snapshot in enumerate(snapshots):
        missing = REQUIRED_SNAPSHOT_FIELDS - set(snapshot)
        if missing:
            raise CommercialIntelligenceValidationError(
                f"snapshot[{index}] missing required fields: {', '.join(sorted(missing))}"
            )
        sku = str(snapshot["sku"]).strip()
        if not sku or sku in seen:
            raise CommercialIntelligenceValidationError(f"duplicate or blank snapshot sku: {sku}")
        seen.add(sku)
        for field in ("available", "avgDailyDemand", "confirmedInbound", "unitCost", "campaignUpliftPct"):
            _finite_non_negative(snapshot[field], f"snapshot[{sku}].{field}")
        if int(snapshot["leadTimeDays"]) < 1:
            raise CommercialIntelligenceValidationError(f"snapshot[{sku}].leadTimeDays must be >= 1")
        _parse_datetime(snapshot["observedAt"], f"snapshot[{sku}].observedAt")
        if not isinstance(snapshot["evidenceRefs"], list):
            raise CommercialIntelligenceValidationError(f"snapshot[{sku}].evidenceRefs must be a list")
    return bundle


def normalize_demand_signals(rows: list[dict[str, str]], *, inventory_bundle: dict) -> list[dict]:
    validate_inventory_bundle(inventory_bundle)
    evidence_time = _parse_datetime(inventory_bundle["payload"]["observedAt"], "payload.observedAt")
    known_skus = {item["sku"] for item in inventory_bundle["payload"]["snapshots"]}
    normalized = []
    for index, row in enumerate(rows):
        sku = (row.get("sku") or "").strip()
        region = (row.get("region_id") or "").strip()
        signal_type = (row.get("signal_type") or "").strip().upper()
        if sku not in known_skus:
            raise CommercialIntelligenceValidationError(f"unknown sku: {sku}")
        if not region:
            raise CommercialIntelligenceValidationError(f"signal[{index}].region_id is required")
        if signal_type not in ALLOWED_SIGNAL_TYPES:
            raise CommercialIntelligenceValidationError(f"unknown signal type: {signal_type}")
        signal_value = _finite_non_negative(row.get("signal_value"), f"signal[{index}].signal_value")
        signal_time = _parse_datetime(row.get("observed_at"), f"signal[{index}].observed_at")
        if signal_time > evidence_time:
            raise CommercialIntelligenceValidationError("signal observed_at is after evidence observation time")
        normalized.append({
            "sku": sku,
            "regionId": region,
            "signalType": signal_type,
            "signalValue": signal_value,
            "observedAt": signal_time.isoformat().replace("+00:00", "Z"),
        })
    return sorted(normalized, key=lambda item: (item["regionId"], item["sku"], item["signalType"], item["observedAt"], item["signalValue"]))
```

- [ ] **Step 4: Run Task 1 tests and verify GREEN**

Run:

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: all Task 1 tests pass.

- [ ] **Step 5: Run existing evidence regression tests**

Run:

```bash
uv run python tests/test_voi_evidence_adapter.py
```

Expected: existing evidence tests remain green.

- [ ] **Step 6: Commit Task 1**

```bash
git add voi_commercial_intelligence.py tests/test_voi_commercial_intelligence.py
git commit -m "feat: add VOI demand signal contract"
```

---

### Task 2: CI-002 Demand Matrix, CI-003 Ready Goods Router, CI-004 Replenishment Recommendations

**Files:**
- Modify: `voi_commercial_intelligence.py`
- Modify: `tests/test_voi_commercial_intelligence.py`

**Interfaces:**
- Consumes:
  - `validate_inventory_bundle(bundle: dict) -> dict`
  - normalized signal rows from `normalize_demand_signals(...)`
- Produces:
  - `build_demand_matrix(inventory_bundle: dict, demand_signals: list[dict] | None = None) -> list[dict]`
  - `route_ready_goods(demand_matrix: list[dict], *, target_days_cover: int = 14) -> list[dict]`
  - `build_replenishment_recommendations(routes: list[dict], *, target_days_cover: int = 14) -> list[dict]`

- [ ] **Step 1: Add failing matrix, routing, and recommendation tests**

Append:

```python
from voi_commercial_intelligence import (
    build_demand_matrix,
    build_replenishment_recommendations,
    route_ready_goods,
)


def test_placeholder():
    pass
```

Replace the placeholder with these methods inside `CommercialIntelligenceTests`:

```python
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
                {"sku": "VOI-BLUE-32", "region_id": "BLR-NORTH", "signal_type": "PRODUCT_VIEW", "signal_value": "100", "observed_at": "2026-09-08T04:00:00Z"},
                {"sku": "VOI-BLUE-32", "region_id": "BLR-NORTH", "signal_type": "PURCHASE", "signal_value": "10", "observed_at": "2026-09-08T04:00:00Z"},
                {"sku": "VOI-BLACK-34", "region_id": "BLR-NORTH", "signal_type": "PURCHASE", "signal_value": "5", "observed_at": "2026-09-08T04:00:00Z"},
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
        self.assertEqual(blue["routeRule"], "DEMAND_WITHOUT_READY_OR_INBOUND_STOCK")

    def test_builds_replenishment_quantity_without_claiming_authority(self):
        routes = route_ready_goods(build_demand_matrix(self._bundle()), target_days_cover=14)
        recommendations = build_replenishment_recommendations(routes, target_days_cover=14)
        blue = next(item for item in recommendations if item["sku"] == "VOI-BLUE-32")
        self.assertEqual(blue["recommendedQty"], 36.0)
        self.assertEqual(blue["authorityState"], "RECOMMENDED_ONLY")
        self.assertEqual(blue["decisionClass"], "REPLENISH")
        self.assertEqual(blue["evidenceRefs"], ["evidence:voi-export:inventory:abc"])
```

- [ ] **Step 2: Run the targeted test file and verify RED**

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: failures/import errors for the three new public functions.

- [ ] **Step 3: Implement the demand scoring helpers and matrix**

Add constants and functions:

```python
SIGNAL_WEIGHTS = {
    "PRODUCT_VIEW": 0.05,
    "ADD_TO_CART": 0.25,
    "PURCHASE": 1.0,
    "RETURN": -1.0,
    "STOCKOUT": 0.5,
}


def _snapshot_by_sku(inventory_bundle: dict) -> dict[str, dict]:
    return {item["sku"]: item for item in inventory_bundle["payload"]["snapshots"]}


def _days_cover(snapshot: dict) -> float | None:
    demand = float(snapshot["avgDailyDemand"])
    if demand == 0:
        return None
    return (float(snapshot["available"]) + float(snapshot["confirmedInbound"])) / demand


def build_demand_matrix(inventory_bundle: dict, demand_signals: list[dict] | None = None) -> list[dict]:
    validate_inventory_bundle(inventory_bundle)
    snapshots = _snapshot_by_sku(inventory_bundle)
    raw_by_region_sku: dict[tuple[str, str], float] = {}

    if demand_signals:
        for signal in demand_signals:
            key = (signal["regionId"], signal["sku"])
            raw_by_region_sku[key] = raw_by_region_sku.get(key, 0.0) + SIGNAL_WEIGHTS[signal["signalType"]] * float(signal["signalValue"])
        regions = sorted({signal["regionId"] for signal in demand_signals})
        for region in regions:
            for sku in snapshots:
                raw_by_region_sku.setdefault((region, sku), 0.0)
    else:
        window = int(inventory_bundle["payload"]["demandWindowDays"])
        for sku, snapshot in snapshots.items():
            raw_by_region_sku[("UNSCOPED", sku)] = float(snapshot["avgDailyDemand"]) * window

    clamped = {key: max(0.0, value) for key, value in raw_by_region_sku.items()}
    maxima: dict[str, float] = {}
    for (region, _sku), value in clamped.items():
        maxima[region] = max(maxima.get(region, 0.0), value)

    rows = []
    for (region, sku), raw in sorted(clamped.items()):
        snapshot = snapshots[sku]
        maximum = maxima[region]
        rows.append({
            "sku": sku,
            "regionId": region,
            "rawIntent": raw,
            "demandScore": (raw / maximum * 100.0) if maximum > 0 else 0.0,
            "available": float(snapshot["available"]),
            "confirmedInbound": float(snapshot["confirmedInbound"]),
            "avgDailyDemand": float(snapshot["avgDailyDemand"]),
            "leadTimeDays": int(snapshot["leadTimeDays"]),
            "daysCover": _days_cover(snapshot),
            "evidenceRefs": sorted(set(snapshot["evidenceRefs"])),
        })
    return rows
```

- [ ] **Step 4: Implement routing and advisory replenishment**

```python
def route_ready_goods(demand_matrix: list[dict], *, target_days_cover: int = 14) -> list[dict]:
    if target_days_cover <= 0:
        raise CommercialIntelligenceValidationError("target_days_cover must be positive")
    routes = []
    for row in demand_matrix:
        route = dict(row)
        total_stock = float(row["available"]) + float(row["confirmedInbound"])
        if float(row["avgDailyDemand"]) > 0 and total_stock == 0:
            route_class = "INVESTIGATE"
            rule = "DEMAND_WITHOUT_READY_OR_INBOUND_STOCK"
        elif (
            float(row["avgDailyDemand"]) > 0
            and row["daysCover"] is not None
            and float(row["daysCover"]) < target_days_cover
            and float(row["available"]) > 0
        ):
            route_class = "REPLENISH"
            rule = "LOW_DAYS_COVER_WITH_READY_GOODS"
        else:
            route_class = "HOLD"
            rule = "SUFFICIENT_COVER_OR_NO_ACTIONABLE_DEMAND"
        route["routeClass"] = route_class
        route["routeRule"] = rule
        routes.append(route)
    return routes


def build_replenishment_recommendations(routes: list[dict], *, target_days_cover: int = 14) -> list[dict]:
    recommendations = []
    for row in routes:
        if row["routeClass"] != "REPLENISH":
            continue
        target_stock = float(row["avgDailyDemand"]) * target_days_cover
        quantity = max(0.0, target_stock - float(row["available"]) - float(row["confirmedInbound"]))
        recommendations.append({
            "decisionClass": "REPLENISH",
            "sku": row["sku"],
            "regionId": row["regionId"],
            "recommendedQty": quantity,
            "targetDaysCover": target_days_cover,
            "reason": {
                "rule": row["routeRule"],
                "daysCover": row["daysCover"],
                "demandScore": row["demandScore"],
            },
            "authorityState": "RECOMMENDED_ONLY",
            "evidenceRefs": sorted(set(row["evidenceRefs"])),
        })
    return sorted(recommendations, key=lambda item: (item["regionId"], item["sku"]))
```

- [ ] **Step 5: Run Task 2 tests and full new test file**

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: all Task 1 and Task 2 tests pass.

- [ ] **Step 6: Commit Task 2**

```bash
git add voi_commercial_intelligence.py tests/test_voi_commercial_intelligence.py
git commit -m "feat: add VOI demand routing and replenishment"
```

---

### Task 3: CI-005 Assortment Risks and CI-006 Deterministic Recommendation Ledger

**Files:**
- Modify: `voi_commercial_intelligence.py`
- Modify: `tests/test_voi_commercial_intelligence.py`

**Interfaces:**
- Produces:
  - `detect_assortment_risks(inventory_bundle: dict, *, slow_stock_days: int = 45) -> tuple[list[dict], dict]`
  - `build_recommendation_ledger(inventory_bundle: dict, recommendations: list[dict], risks: list[dict], capability_state: dict, *, model_version: str = MODEL_VERSION) -> dict`

- [ ] **Step 1: Add failing risk and ledger tests**

Append methods:

```python
    def test_detects_zero_demand_stock_as_slow_stock(self):
        bundle = self._bundle()
        bundle["payload"]["snapshots"][0]["avgDailyDemand"] = 0.0
        risks, capability = detect_assortment_risks(bundle)
        blue = next(item for item in risks if item["sku"] == "VOI-BLUE-32")
        self.assertEqual(blue["riskType"], "SLOW_STOCK")
        self.assertEqual(capability["brokenSizeDetection"], "INSUFFICIENT_STYLE_SIZE_EVIDENCE")

    def test_does_not_infer_broken_sizes_from_sku_text(self):
        risks, capability = detect_assortment_risks(self._bundle())
        self.assertFalse(any(item["riskType"] == "BROKEN_SIZE" for item in risks))
        self.assertEqual(capability["brokenSizeDetection"], "INSUFFICIENT_STYLE_SIZE_EVIDENCE")

    def test_detects_broken_sizes_only_with_explicit_lineage(self):
        bundle = self._bundle()
        bundle["payload"]["snapshots"] = [
            {**bundle["payload"]["snapshots"][0], "sku": "S32", "styleId": "STYLE-1", "size": "32", "available": 10.0},
            {**bundle["payload"]["snapshots"][0], "sku": "S34", "styleId": "STYLE-1", "size": "34", "available": 0.0},
            {**bundle["payload"]["snapshots"][0], "sku": "S36", "styleId": "STYLE-1", "size": "36", "available": 12.0},
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
        first = build_recommendation_ledger(bundle, recommendations, risks, capability)
        second = build_recommendation_ledger(copy.deepcopy(bundle), copy.deepcopy(recommendations), copy.deepcopy(risks), copy.deepcopy(capability))
        self.assertEqual(first, second)
        self.assertEqual(first["contract"], "VOI-COMMERCIAL-INTELLIGENCE-001")
        self.assertEqual(first["modelVersion"], "VOI-CI-R0.1")
        self.assertEqual(first["sourceBundleId"], bundle["bundleId"])
        self.assertEqual(first["evidenceObservedAt"], bundle["payload"]["observedAt"])
        self.assertNotIn("generatedAt", first)
        self.assertEqual(first["integrity"]["digest"], first["ledgerId"])
        for recommendation in first["recommendations"]:
            self.assertTrue(recommendation["recommendationId"].startswith("sha256:"))
            self.assertEqual(recommendation["authorityState"], "RECOMMENDED_ONLY")
            self.assertTrue(recommendation["evidenceRefs"])
```

Add imports:

```python
from voi_commercial_intelligence import detect_assortment_risks, build_recommendation_ledger
```

- [ ] **Step 2: Run tests and verify RED**

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: missing function failures.

- [ ] **Step 3: Implement slow-stock and explicit broken-size detection**

Add `hashlib` and `json` imports, then:

```python
def detect_assortment_risks(inventory_bundle: dict, *, slow_stock_days: int = 45) -> tuple[list[dict], dict]:
    validate_inventory_bundle(inventory_bundle)
    if slow_stock_days <= 0:
        raise CommercialIntelligenceValidationError("slow_stock_days must be positive")
    snapshots = inventory_bundle["payload"]["snapshots"]
    risks = []

    for snapshot in snapshots:
        available = float(snapshot["available"])
        demand = float(snapshot["avgDailyDemand"])
        cover = _days_cover(snapshot)
        if available > 0 and (demand == 0 or (cover is not None and cover > slow_stock_days)):
            risks.append({
                "riskType": "SLOW_STOCK",
                "sku": snapshot["sku"],
                "daysCover": cover,
                "available": available,
                "evidenceRefs": sorted(set(snapshot["evidenceRefs"])),
            })

    lineage_ready = all("styleId" in item and "size" in item for item in snapshots)
    capability = {
        "brokenSizeDetection": "AVAILABLE" if lineage_ready else "INSUFFICIENT_STYLE_SIZE_EVIDENCE"
    }
    if lineage_ready:
        by_style: dict[str, list[dict]] = {}
        for snapshot in snapshots:
            by_style.setdefault(str(snapshot["styleId"]), []).append(snapshot)
        for style_id, items in sorted(by_style.items()):
            present = sorted(str(item["size"]) for item in items if float(item["available"]) > 0)
            missing = sorted(str(item["size"]) for item in items if float(item["available"]) == 0)
            if present and missing:
                evidence_refs = sorted({ref for item in items for ref in item["evidenceRefs"]})
                risks.append({
                    "riskType": "BROKEN_SIZE",
                    "styleId": style_id,
                    "presentSizes": present,
                    "missingSizes": missing,
                    "evidenceRefs": evidence_refs,
                })

    risks.sort(key=lambda item: (item["riskType"], item.get("styleId", ""), item.get("sku", "")))
    return risks, capability
```

- [ ] **Step 4: Implement deterministic recommendation and ledger digests**

```python
def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_id(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def build_recommendation_ledger(
    inventory_bundle: dict,
    recommendations: list[dict],
    risks: list[dict],
    capability_state: dict,
    *,
    model_version: str = MODEL_VERSION,
) -> dict:
    validate_inventory_bundle(inventory_bundle)
    source_bundle_id = inventory_bundle["bundleId"]

    with_ids = []
    for recommendation in recommendations:
        business_payload = {
            "modelVersion": model_version,
            "sourceBundleId": source_bundle_id,
            "recommendation": recommendation,
        }
        with_ids.append({
            "recommendationId": _sha256_id(business_payload),
            **recommendation,
        })

    canonical = {
        "schemaVersion": "1.0.0",
        "contract": "VOI-COMMERCIAL-INTELLIGENCE-001",
        "modelVersion": model_version,
        "sourceBundleId": source_bundle_id,
        "evidenceObservedAt": inventory_bundle["payload"]["observedAt"],
        "recommendations": sorted(with_ids, key=lambda item: item["recommendationId"]),
        "risks": sorted(risks, key=lambda item: _canonical_json(item)),
        "capabilityState": dict(sorted(capability_state.items())),
    }
    ledger_id = _sha256_id(canonical)
    return {
        **canonical,
        "integrity": {"algorithm": "SHA-256", "digest": ledger_id},
        "ledgerId": ledger_id,
    }
```

- [ ] **Step 5: Add a no-external-I/O guard test**

Add:

```python
    def test_commercial_intelligence_module_has_no_external_io_imports(self):
        source = (ROOT / "voi_commercial_intelligence.py").read_text(encoding="utf-8")
        forbidden = ["requests", "httpx", "urllib.request", "subprocess", "socket", "sqlalchemy", "psycopg"]
        for token in forbidden:
            self.assertNotIn(token, source)
```

- [ ] **Step 6: Run all commercial-intelligence tests**

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: all tests pass.

- [ ] **Step 7: Run all repository tests**

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: existing evidence suite plus new commercial-intelligence suite pass.

- [ ] **Step 8: Commit Task 3**

```bash
git add voi_commercial_intelligence.py tests/test_voi_commercial_intelligence.py
git commit -m "feat: add VOI intelligence risk and ledger contracts"
```

---

### Task 4: Read-Only Streamlit Commercial Intelligence Bridge

**Files:**
- Create: `commercial_intelligence_bridge.py`
- Modify: `inventory_evidence_bridge.py`
- Modify: `app.py`
- Modify: `tests/test_voi_commercial_intelligence.py`

**Interfaces:**
- Consumes the exact validated object in `st.session_state.voi_inventory_evidence_bundle` or a user-uploaded evidence JSON.
- Produces a downloadable `VOI-COMMERCIAL-INTELLIGENCE-001` JSON ledger only; no operational actions.

- [ ] **Step 1: Add helper tests for signal CSV parsing and validated bundle retention**

Add a pure helper to `commercial_intelligence_bridge.py` named `_parse_signal_csv_bytes(data: bytes) -> list[dict[str, str]]` and test it without rendering Streamlit:

```python
from commercial_intelligence_bridge import _parse_signal_csv_bytes

    def test_signal_csv_parser_returns_source_rows(self):
        rows = _parse_signal_csv_bytes(
            b"sku,region_id,signal_type,signal_value,observed_at\nVOI-BLUE-32,BLR-NORTH,PURCHASE,2,2026-09-08T04:00:00Z\n"
        )
        self.assertEqual(rows[0]["region_id"], "BLR-NORTH")
        self.assertEqual(rows[0]["signal_value"], "2")
```

- [ ] **Step 2: Run the new helper test and verify RED**

```bash
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: import failure because the bridge does not exist.

- [ ] **Step 3: Create the Streamlit bridge with no write actions**

Create `commercial_intelligence_bridge.py` with:

```python
from __future__ import annotations

import csv
import io
import json

import pandas as pd
import streamlit as st

from voi_commercial_intelligence import (
    CommercialIntelligenceValidationError,
    MODEL_VERSION,
    build_demand_matrix,
    build_recommendation_ledger,
    build_replenishment_recommendations,
    detect_assortment_risks,
    normalize_demand_signals,
    route_ready_goods,
    validate_inventory_bundle,
)


def _parse_signal_csv_bytes(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    required = {"sku", "region_id", "signal_type", "signal_value", "observed_at"}
    if not reader.fieldnames or not required.issubset({(name or "").strip() for name in reader.fieldnames}):
        raise CommercialIntelligenceValidationError(
            "demand signals CSV requires sku,region_id,signal_type,signal_value,observed_at"
        )
    return [
        {key: (value or "").strip() for key, value in row.items() if key is not None}
        for row in reader
    ]


def show_commercial_intelligence_bridge():
    st.title("VOI Commercial Intelligence R0.1")
    st.caption("Evidence-linked demand, ready-goods and replenishment recommendations")
    st.warning(
        "Recommendations are advisory only. Warden/operator authorization is required before any inventory, pricing, order, or marketplace action."
    )

    source_bundle = st.session_state.get("voi_inventory_evidence_bundle")
    bundle_upload = st.file_uploader("Validated VOI inventory evidence JSON (optional)", type=["json"], key="voi_ci_bundle")
    signal_upload = st.file_uploader("Demand signals CSV (optional)", type=["csv"], key="voi_ci_signals")

    if bundle_upload is not None:
        try:
            source_bundle = json.loads(bundle_upload.getvalue().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            st.error(f"Evidence JSON rejected: {exc}")
            return

    if source_bundle is None:
        st.info("Build an Inventory Evidence Bridge bundle first, or upload a validated evidence JSON bundle here.")
        return

    try:
        validate_inventory_bundle(source_bundle)
        signals = None
        if signal_upload is not None:
            signals = normalize_demand_signals(
                _parse_signal_csv_bytes(signal_upload.getvalue()),
                inventory_bundle=source_bundle,
            )
        matrix = build_demand_matrix(source_bundle, signals)
        routes = route_ready_goods(matrix)
        recommendations = build_replenishment_recommendations(routes)
        risks, capability = detect_assortment_risks(source_bundle)
        ledger = build_recommendation_ledger(source_bundle, recommendations, risks, capability)
    except CommercialIntelligenceValidationError as exc:
        st.error(f"Commercial intelligence rejected: {exc}")
        return

    st.markdown("### Demand Matrix")
    st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
    st.markdown("### Ready Goods Routes")
    st.dataframe(pd.DataFrame(routes), use_container_width=True, hide_index=True)
    st.markdown("### Replenishment Recommendations")
    st.dataframe(pd.DataFrame(recommendations), use_container_width=True, hide_index=True)
    st.markdown("### Assortment Risks")
    st.dataframe(pd.DataFrame(risks), use_container_width=True, hide_index=True)

    st.markdown("### Intelligence Contract")
    st.code(ledger["ledgerId"], language="text")
    st.caption(f"Model: {MODEL_VERSION} | Source: {ledger['sourceBundleId']}")
    payload = json.dumps(ledger, indent=2, sort_keys=True, allow_nan=False) + "\n"
    st.download_button(
        "Export recommendation ledger JSON",
        data=payload,
        file_name=f"voi_commercial_intelligence_{ledger['ledgerId'].split(':', 1)[1][:12]}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("Exporting this recommendation ledger does not authorize or execute any operational action.")
```

- [ ] **Step 4: Retain successful evidence bundles in session state**

In `inventory_evidence_bridge.py`, immediately after successful `build_inventory_evidence_bundle(...)` and before rendering metrics, add:

```python
st.session_state.voi_inventory_evidence_bundle = bundle
```

Do not persist failed or partially parsed bundles.

- [ ] **Step 5: Add navigation and route in `app.py`**

Add import:

```python
from commercial_intelligence_bridge import show_commercial_intelligence_bridge
```

Under Market Intelligence after Inventory Evidence Bridge:

```python
if st.button("🧠 Commercial Intelligence", use_container_width=True):
    st.session_state.page = "commercial_intelligence"

st.caption("Convert validated evidence into advisory demand and replenishment recommendations.")
```

Add route:

```python
elif st.session_state.page == "commercial_intelligence":
    show_commercial_intelligence_bridge()
```

- [ ] **Step 6: Run helper and full unit tests**

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

Expected: all tests pass.

- [ ] **Step 7: Compile all affected modules**

```bash
uv run python -m py_compile \
  voi_evidence_adapter.py \
  export_voi_inventory_evidence.py \
  inventory_evidence_bridge.py \
  voi_commercial_intelligence.py \
  commercial_intelligence_bridge.py \
  app.py
```

Expected: exit code 0.

- [ ] **Step 8: Commit Task 4**

```bash
git add commercial_intelligence_bridge.py inventory_evidence_bridge.py app.py tests/test_voi_commercial_intelligence.py
git commit -m "feat: expose VOI commercial intelligence bridge"
```

---

### Task 5: Packaging, CI Gate, Full Verification and Draft PR

**Files:**
- Modify: `pyproject.toml`
- Modify: `.github/workflows/voi-evidence-bridge.yml`

**Interfaces:**
- CI must verify dependency lock unchanged, compile both new modules, run all test discovery, and prove both direct test files.

- [ ] **Step 1: Register new modules in packaging**

Update `[tool.setuptools].py-modules` to:

```toml
[tool.setuptools]
py-modules = [
    "voi_evidence_adapter",
    "export_voi_inventory_evidence",
    "inventory_evidence_bridge",
    "voi_commercial_intelligence",
    "commercial_intelligence_bridge",
]
```

No dependency additions are required; therefore `uv.lock` must remain unchanged.

- [ ] **Step 2: Extend the compile gate**

Change the workflow compile step to:

```yaml
      - name: Compile governed VOI modules
        run: |
          uv run python -m py_compile \
            voi_evidence_adapter.py \
            export_voi_inventory_evidence.py \
            inventory_evidence_bridge.py \
            voi_commercial_intelligence.py \
            commercial_intelligence_bridge.py \
            app.py
```

- [ ] **Step 3: Prove both direct test entrypoints**

Replace the existing final direct-test step with:

```yaml
      - name: Prove direct governed test entrypoints
        run: |
          uv run python tests/test_voi_evidence_adapter.py
          uv run python tests/test_voi_commercial_intelligence.py
```

Keep the existing discovery step unchanged:

```yaml
      - name: Run evidence contract regression suite
        run: uv run python -m unittest discover -s tests -p 'test_*.py' -v
```

- [ ] **Step 4: Run lock and compile checks locally**

```bash
uv lock --check
uv sync --locked
uv run python -m py_compile \
  voi_evidence_adapter.py \
  export_voi_inventory_evidence.py \
  inventory_evidence_bridge.py \
  voi_commercial_intelligence.py \
  commercial_intelligence_bridge.py \
  app.py
```

Expected: all commands exit 0 and `uv.lock` is unchanged.

- [ ] **Step 5: Run the complete test suite**

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python tests/test_voi_evidence_adapter.py
uv run python tests/test_voi_commercial_intelligence.py
```

Expected: all tests pass.

- [ ] **Step 6: Verify no write integration was introduced**

Run:

```bash
grep -RInE 'requests\.|httpx\.|urllib\.request|subprocess|psycopg|sqlalchemy|INSERT |UPDATE |DELETE |Easycom|Myntra|Flipkart' \
  voi_commercial_intelligence.py commercial_intelligence_bridge.py
```

Expected: no runtime write/client integration; display copy mentioning marketplaces is acceptable only if it is the boundary notice and not an API client.

- [ ] **Step 7: Commit packaging and CI changes**

```bash
git add pyproject.toml .github/workflows/voi-evidence-bridge.yml
git commit -m "ci: gate VOI commercial intelligence contracts"
```

- [ ] **Step 8: Create a draft pull request**

Title:

```text
Add VOI Commercial Intelligence R0.1
```

Body:

```markdown
## Summary
- add deterministic CI-001..CI-006 commercial-intelligence contracts above the existing read-only VOI evidence bundle
- add advisory Streamlit demand/replenishment surface
- preserve evidence provenance and deterministic SHA-256 recommendation ledger IDs
- retain explicit Warden/operator authorization boundary; no operational write path is introduced

## Verification
- `uv lock --check`
- compile all governed modules
- full `unittest` discovery
- direct evidence-adapter tests
- direct commercial-intelligence tests

## Safety / governance boundary
This PR is recommendation-only. It does not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, payments, BNR, or ARK state.
```

Create as **draft** against `main` so CI evidence can be reviewed before readiness promotion.

---

## Plan Self-Review

- Spec coverage: CI-001 through CI-006, read-only UI, deterministic output, evidence provenance, missing-region and missing-style/size behavior, packaging, and CI are all mapped to explicit tasks.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: public function names and return shapes are consistent across Tasks 1–5 and the Streamlit bridge.
- Scope: no Warden auto-approval, direct ERP/OMS writes, marketplace execution, pricing, production planning, fabric optimization, database persistence, or BNR/ARK mutation enters this release.
