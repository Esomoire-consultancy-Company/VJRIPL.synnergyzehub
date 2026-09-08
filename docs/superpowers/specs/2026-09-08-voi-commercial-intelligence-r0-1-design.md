# VOI Commercial Intelligence R0.1 — Design

Date: 2026-09-08
Status: Implemented in draft PR #8; review-hardened contract
Repository: `Esomoire-consultancy-Company/VJRIPL.synnergyzehub`
Branch: `feat/voi-commercial-intelligence-r0-1`
Model version: `VOI-CI-R0.1`

## 1. Purpose

VOI Commercial Intelligence R0.1 is the first governed recommendation layer above the read-only `VOI-INVENTORY-EVIDENCE-001` contract. It converts validated evidence and optional regional demand signals into deterministic demand, routing, replenishment-advisory, assortment-risk, and recommendation-ledger records.

R0.1 is recommendation-only. It does not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, payments, BNR, or ARK state.

Capabilities:

- CI-001 Demand Signal Normalizer
- CI-002 SKU × Region Demand Matrix
- CI-003 Ready Goods Router
- CI-004 Replenishment Recommendation
- CI-005 Broken Size / Slow Stock Detection
- CI-006 Recommendation Ledger

## 2. Governing boundary

```text
LOGIC / OMS exports
      ↓
VOI-INVENTORY-EVIDENCE-001
      ↓  integrity verification
VOI Commercial Intelligence R0.1
      ↓
Demand / Route / Recommendation
      ↓
Warden / operator authorization boundary
      ↓
Future execution adapter (out of scope)
```

Rules:

1. Evidence never grants execution authority.
2. The core intelligence module performs no external I/O.
3. Every recommendation is `RECOMMENDED_ONLY`, evidence-linked, and model-versioned.
4. Recommendation and ledger IDs are deterministic SHA-256 digests.
5. Identical valid inputs produce identical canonical outputs; wall-clock time is excluded.
6. Geographic or assortment precision is never invented when evidence is absent.
7. Aggregate stock must never be double-counted as though it were independently available in multiple regions.

## 3. Verified public API

```python
validate_inventory_bundle(bundle: dict) -> dict

normalize_demand_signals(
    rows: list[dict[str, str]],
    *,
    inventory_bundle: dict,
) -> list[dict]

build_demand_matrix(
    inventory_bundle: dict,
    demand_signals: list[dict] | None = None,
) -> list[dict]

route_ready_goods(
    demand_matrix: list[dict],
    *,
    target_days_cover: int = 14,
) -> list[dict]

build_replenishment_recommendations(
    routes: list[dict],
    *,
    target_days_cover: int = 14,
) -> list[dict]

detect_assortment_risks(
    inventory_bundle: dict,
    *,
    slow_stock_days: int = 45,
) -> tuple[list[dict], dict]

build_recommendation_ledger(
    inventory_bundle: dict,
    recommendations: list[dict],
    risks: list[dict],
    capability_state: dict,
    *,
    model_version: str = MODEL_VERSION,
) -> dict
```

## 4. Evidence validation and integrity

Accepted evidence must use contract `VOI-INVENTORY-EVIDENCE-001` and contain a non-empty snapshot list.

Required snapshot fields:

- `sku`
- `available`
- `avgDailyDemand`
- `confirmedInbound`
- `leadTimeDays`
- `unitCost`
- `campaignUpliftPct`
- `observedAt`
- `evidenceRefs`

Before inference, the module recomputes the canonical payload and verifies:

```text
bundleId
== integrity.digest
== SHA-256(canonical_json(payload))
```

`integrity.algorithm` must be `SHA-256`, and `integrity.canonicalPayload` must exactly match the recomputed canonical payload.

Input-shape rules include:

- timestamps must be strings containing ISO-8601 values;
- non-finite values such as `NaN` are rejected through `CommercialIntelligenceValidationError`;
- snapshot SKU must be an actual non-empty string;
- every `evidenceRefs` element must be a string;
- `leadTimeDays` must be a finite positive integer and is never silently truncated;
- malformed snapshots use the commercial-intelligence domain error rather than leaking built-in exceptions.

A `sha256:` prefix by itself is not integrity evidence.

## 5. CI-001 — Demand Signal Normalizer

Optional CSV columns:

```text
sku,region_id,signal_type,signal_value,observed_at
```

Allowed types:

- `PRODUCT_VIEW`
- `ADD_TO_CART`
- `PURCHASE`
- `RETURN`
- `STOCKOUT`

Rules:

- SKU must exist in the validated evidence bundle.
- `region_id` is required.
- `signal_value` must be finite and non-negative.
- `observed_at` cannot be after the evidence observation time.
- unknown signal types are rejected.
- CSV must decode as UTF-8 and must use the expected header shape.

## 6. CI-002 — SKU × Region Demand Matrix

Raw regional intent:

```text
rawIntent =
  0.05 × PRODUCT_VIEW
+ 0.25 × ADD_TO_CART
+ 1.00 × PURCHASE
+ 0.50 × STOCKOUT
- 1.00 × RETURN
```

Clamp at zero. `demandScore` is scaled to `0..100` within each region.

### 6.1 Regional mode

Regional demand must not inherit the SKU's global historical demand:

```text
effectiveDailyDemand = max(rawIntent, 0) / demandWindowDays
```

Matrix rows record:

- `baselineAvgDailyDemand`
- `effectiveDailyDemand`
- `demandBasis = REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE`
- `stockScope = SHARED_AGGREGATE`
- `avgDailyDemand` compatibility alias equal to effective demand

The stock values visible on regional rows remain aggregate/shared evidence. They may support prioritization and routing signals, but they do not establish independently allocatable regional stock.

### 6.2 UNSCOPED mode

Without regional signals:

```text
rawIntent = baselineAvgDailyDemand × demandWindowDays
effectiveDailyDemand = baselineAvgDailyDemand
demandBasis = BUNDLE_AVG_DAILY_DEMAND
stockScope = AGGREGATE_UNSCOPED
```

### 6.3 Days cover

```text
daysCover = (available + confirmedInbound) / effectiveDailyDemand
```

Zero effective demand produces `daysCover = null`.

## 7. CI-003 — Ready Goods Router

Route classes:

- `REPLENISH`
- `HOLD`
- `INVESTIGATE`

Rules:

1. `INVESTIGATE` when effective demand exists and `available + confirmedInbound == 0`.
2. `REPLENISH` when effective demand exists and cover is below target.
   - `LOW_DAYS_COVER_WITH_READY_GOODS` if available stock is positive.
   - `LOW_DAYS_COVER_WITH_INBOUND_ONLY` if only inbound stock is present.
3. `HOLD` otherwise.

`target_days_cover` must be a positive integer.

Routing is advisory classification only; it does not allocate or move stock.

## 8. CI-004 — Replenishment Recommendation

### 8.1 UNSCOPED aggregate quantity

When `demandBasis = BUNDLE_AVG_DAILY_DEMAND`, the aggregate evidence supports an aggregate quantity calculation:

```text
targetStock = effectiveDailyDemand × targetDaysCover
recommendedQty = max(0, targetStock - available - confirmedInbound)
quantityState = QUANTIFIED_AGGREGATE_STOCK
```

### 8.2 Regional quantity boundary

When `demandBasis = REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE`, the current inventory evidence is shared aggregate stock and does not show how much is independently available in each region.

Therefore R0.1 emits:

```json
{
  "recommendedQty": null,
  "quantityState": "UNQUANTIFIED_SHARED_STOCK"
}
```

Regional demand may rank and route opportunities, but **numeric store/region replenishment quantities are withheld until location-level inventory evidence is admitted**. This prevents the same global stock from being subtracted or allocated multiple times across regions.

Every recommendation also includes:

- `modelVersion: VOI-CI-R0.1`
- `decisionClass`
- `sku`
- `regionId`
- `targetDaysCover`
- explicit reason/rule
- demand basis and effective demand
- `authorityState: RECOMMENDED_ONLY`
- source evidence references

## 9. CI-005 — Assortment risks

### Slow stock

Slow-stock detection uses the historical evidence-bundle baseline, not regional signal demand. A SKU is slow stock when available stock is positive and baseline demand is zero or historical stock cover exceeds the configured positive integer threshold.

### Broken size

Broken-size detection requires explicit `styleId` and `size` lineage. No SKU-text inference is permitted.

Without explicit lineage:

```text
brokenSizeDetection = INSUFFICIENT_STYLE_SIZE_EVIDENCE
```

## 10. CI-006 — Recommendation ledger

Contract:

```text
VOI-COMMERCIAL-INTELLIGENCE-001
```

Each recommendation receives a deterministic ID calculated from a sanitized recommendation business payload, source bundle ID, and model version.

Any caller-supplied `recommendationId` is removed before hashing and cannot override the computed digest.

The top-level `ledgerId` is the SHA-256 digest of the canonical ledger business payload. Wall-clock generation time is excluded.

## 11. UI boundary

`commercial_intelligence_bridge.py` is read-only. It:

- consumes a session bundle or uploaded evidence JSON;
- validates the bundle before inference;
- accepts optional demand-signal CSV;
- displays matrix, routes, recommendations, risks, and ledger identity;
- exports JSON only.

Boundary notice:

> Recommendations are advisory only. Warden/operator authorization is required before any inventory, pricing, order, or marketplace action.

## 12. Verification contract

The regression suite covers:

- cryptographic tamper rejection;
- malformed timestamp and canonical-JSON rejection;
- strict SKU, evidence-reference, and lead-time typing;
- regional demand leakage prevention;
- shared-stock regional quantity suppression;
- inbound-only routing;
- positive target-cover validation;
- recommendation-ID sanitization;
- UTF-8 signal handling;
- deterministic recommendation and ledger IDs;
- broken-size evidence requirements;
- absence of external-I/O imports in the core engine;
- all existing evidence-adapter regressions.

GitHub Actions gates:

```text
uv lock --check
uv sync --locked
compile all governed modules
full unittest discovery
direct evidence-adapter tests
direct commercial-intelligence tests
```

## 13. Acceptance criteria

R0.1 is reviewable only when:

- evidence integrity is reverified before inference;
- all known malformed-input paths fail through the domain validation contract;
- regional demand does not inherit unrelated global demand;
- aggregate inventory is never double-counted as multiple regional quantities;
- regional numeric quantities remain unquantified until location-level stock exists;
- recommendations are model-versioned, evidence-linked, deterministic, and `RECOMMENDED_ONLY`;
- no operational write integration exists;
- all governed CI gates pass.

## 14. Out of scope

- automatic Warden approval
- direct LOGIC ERP or Easycom writes
- marketplace inventory updates
- autonomous pricing
- location-level stock allocation without evidence
- cross-store transfer execution
- production planning
- fabric optimization
- ML training
- persistent intelligence database storage
- BNR/ARK mutation

R0.1 stops at trustworthy evidence → recommendation generation and export.
