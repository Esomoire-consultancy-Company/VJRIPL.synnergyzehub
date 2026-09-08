# VOI Commercial Intelligence R0.1 — Design

Date: 2026-09-08
Status: Implemented in draft PR #8; verified contract
Repository: `Esomoire-consultancy-Company/VJRIPL.synnergyzehub`
Target branch: `feat/voi-commercial-intelligence-r0-1`
Model version: `VOI-CI-R0.1`

## 1. Purpose

VOI Commercial Intelligence R0.1 is the first governed recommendation layer above the existing read-only `VOI-INVENTORY-EVIDENCE-001` contract. It turns validated inventory/sales evidence and optional regional demand signals into deterministic demand, routing, replenishment, assortment-risk, and recommendation-ledger records.

R0.1 is recommendation-only. It does not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, payments, BNR, or ARK state.

The release contains six bounded capabilities:

- CI-001 Demand Signal Normalizer
- CI-002 SKU × Region Demand Matrix
- CI-003 Ready Goods Router
- CI-004 Store Replenishment Recommendation
- CI-005 Broken Size / Slow Stock Detection
- CI-006 Recommendation Ledger

## 2. Architectural boundary

```text
LOGIC / OMS exports
      ↓
VOI-INVENTORY-EVIDENCE-001
      ↓  cryptographic integrity verification
Commercial Intelligence R0.1
      ↓
Recommendation object
      ↓
Warden / operator authorization boundary
      ↓
Future execution adapter (out of scope)
      ↓
Outcome observation
```

Rules:

1. Evidence is input, never execution authority.
2. The commercial-intelligence module performs no external I/O.
3. Every recommendation is `RECOMMENDED_ONLY` and carries source evidence references and `modelVersion`.
4. Recommendation and ledger identifiers are deterministic SHA-256 digests of canonical business payloads.
5. Identical valid inputs produce identical canonical outputs; wall-clock generation time is excluded.
6. Missing geography is represented as `UNSCOPED`; missing style/size lineage is represented explicitly rather than guessed.

## 3. Components

### 3.1 `voi_commercial_intelligence.py`

Pure Python business-contract module. No Streamlit dependency and no external network, database, subprocess, or commerce-client I/O.

Verified public functions:

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

### 3.2 `commercial_intelligence_bridge.py`

Read-only Streamlit surface. It can consume the last validated evidence bundle from session state or a user-uploaded evidence JSON, optionally ingest a regional demand-signal CSV, display the derived outputs, and export the deterministic recommendation ledger JSON.

The bridge exposes no operational action control.

### 3.3 `inventory_evidence_bridge.py`

After successful evidence construction and validation, the exact bundle is retained at:

```python
st.session_state.voi_inventory_evidence_bundle
```

Failed or partial evidence is not retained.

### 3.4 `app.py`

Adds a `Commercial Intelligence` navigation entry under Market Intelligence. Existing portal flows remain unchanged.

## 4. Inventory evidence contract and integrity verification

Input must be `VOI-INVENTORY-EVIDENCE-001` and must contain a non-empty snapshot array. Required snapshot fields are:

- `sku`
- `available`
- `avgDailyDemand`
- `confirmedInbound`
- `leadTimeDays`
- `unitCost`
- `campaignUpliftPct`
- `observedAt`
- `evidenceRefs`

Before any recommendation logic is allowed to run, the commercial-intelligence module recomputes the canonical JSON of `payload` and its SHA-256 digest. Acceptance requires all of the following to agree:

```text
bundle.bundleId
bundle.integrity.digest
SHA-256(canonical_json(bundle.payload))
```

Additionally:

- `integrity.algorithm` must equal `SHA-256`;
- `integrity.canonicalPayload` must exactly equal the recomputed canonical payload;
- malformed snapshot entries are rejected with `CommercialIntelligenceValidationError`;
- numeric evidence must be finite and non-negative where applicable;
- `leadTimeDays` must be a finite positive integer and is never silently truncated.

A `sha256:` prefix alone is not evidence of integrity.

## 5. CI-001 — Demand Signal Normalizer

Optional demand-signal CSV columns:

```text
sku,region_id,signal_type,signal_value,observed_at
```

Allowed types:

- `PRODUCT_VIEW`
- `ADD_TO_CART`
- `PURCHASE`
- `RETURN`
- `STOCKOUT`

Validation rules:

- SKU must exist in the validated evidence bundle.
- `region_id` is mandatory.
- `signal_value` must be finite and non-negative.
- `observed_at` must be ISO-8601 and not later than the evidence observation time.
- unknown signal types are rejected.
- CSV input must decode as UTF-8.
- extra CSV fields are rejected.

Normalized object:

```json
{
  "sku": "VOI-SKU-001",
  "regionId": "BLR-NORTH",
  "signalType": "PURCHASE",
  "signalValue": 8.0,
  "observedAt": "2026-09-08T04:00:00Z"
}
```

## 6. CI-002 — SKU × Region Demand Matrix

R0.1 uses a transparent deterministic heuristic, not a predictive ML model.

For explicit regional signals:

```text
raw_intent =
  0.05 × PRODUCT_VIEW
+ 0.25 × ADD_TO_CART
+ 1.00 × PURCHASE
+ 0.50 × STOCKOUT
- 1.00 × RETURN
```

The result is clamped to zero.

Within each region, `demandScore` is scaled to `0..100` against the largest positive raw intent in that region.

### 6.1 Regional effective demand

Regional routing must not leak the bundle-wide historical demand of a SKU into every region. Therefore, when regional signals are supplied:

```text
effectiveDailyDemand = max(raw_intent, 0) / demandWindowDays
```

Rows with no signal-derived intent in that region receive `effectiveDailyDemand = 0`, even if the SKU has positive global historical demand.

The matrix records both:

- `baselineAvgDailyDemand` — the evidence-bundle historical rate;
- `effectiveDailyDemand` — the rate actually used by regional routing;
- `demandBasis` — `REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE` or `BUNDLE_AVG_DAILY_DEMAND`.

`avgDailyDemand` remains as a compatibility alias for `effectiveDailyDemand` in matrix rows.

### 6.2 UNSCOPED mode

When no regional signals are supplied, the engine creates the single `UNSCOPED` region:

```text
raw_intent = baselineAvgDailyDemand × demandWindowDays
effectiveDailyDemand = baselineAvgDailyDemand
demandBasis = BUNDLE_AVG_DAILY_DEMAND
```

### 6.3 Days cover

```text
daysCover = (available + confirmedInbound) / effectiveDailyDemand
```

If effective demand is zero, `daysCover` is `null` rather than infinity.

## 7. CI-003 — Ready Goods Router

Route classes:

- `REPLENISH`
- `HOLD`
- `INVESTIGATE`

Rules, in order:

1. `INVESTIGATE` when `effectiveDailyDemand > 0` and `available + confirmedInbound == 0`.
2. `REPLENISH` when `effectiveDailyDemand > 0` and `daysCover < target_days_cover`.
   - `LOW_DAYS_COVER_WITH_READY_GOODS` when `available > 0`.
   - `LOW_DAYS_COVER_WITH_INBOUND_ONLY` when `available == 0` and confirmed inbound stock is positive.
3. `HOLD` otherwise, with `SUFFICIENT_COVER_OR_NO_ACTIONABLE_DEMAND`.

The router classifies only; it never moves stock.

## 8. CI-004 — Replenishment Recommendation

For `REPLENISH` rows:

```text
target_stock = effectiveDailyDemand × target_days_cover
recommended_qty = max(0, target_stock - available - confirmedInbound)
```

Each standalone recommendation is self-describing:

```json
{
  "modelVersion": "VOI-CI-R0.1",
  "decisionClass": "REPLENISH",
  "sku": "VOI-SKU-001",
  "regionId": "BLR-NORTH",
  "recommendedQty": 18.0,
  "targetDaysCover": 14,
  "reason": {
    "rule": "LOW_DAYS_COVER_WITH_READY_GOODS",
    "daysCover": 4.3,
    "demandScore": 91.0,
    "demandBasis": "REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE",
    "effectiveDailyDemand": 2.0
  },
  "authorityState": "RECOMMENDED_ONLY",
  "evidenceRefs": ["evidence:..."]
}
```

No recommendation is approved, authorized, or executed by this module.

## 9. CI-005 — Assortment risks

### 9.1 Slow stock

Slow-stock detection uses the evidence-bundle historical demand baseline. A SKU is `SLOW_STOCK` when available stock is positive and either:

- baseline `avgDailyDemand == 0`; or
- historical days cover exceeds `slow_stock_days`.

### 9.2 Broken size

Broken-size detection is enabled only when every relevant snapshot contains explicit `styleId` and `size` lineage. The engine never derives style families from SKU text.

Without explicit lineage:

```text
capabilityState.brokenSizeDetection = INSUFFICIENT_STYLE_SIZE_EVIDENCE
```

With explicit lineage, missing sizes are identified only from those supplied fields.

## 10. CI-006 — Recommendation ledger

Contract:

```text
VOI-COMMERCIAL-INTELLIGENCE-001
```

Top-level shape:

```json
{
  "schemaVersion": "1.0.0",
  "contract": "VOI-COMMERCIAL-INTELLIGENCE-001",
  "modelVersion": "VOI-CI-R0.1",
  "sourceBundleId": "sha256:...",
  "evidenceObservedAt": "2026-09-08T04:30:00Z",
  "recommendations": [],
  "risks": [],
  "capabilityState": {},
  "integrity": {
    "algorithm": "SHA-256",
    "digest": "sha256:..."
  },
  "ledgerId": "sha256:..."
}
```

Each recommendation receives `recommendationId = SHA-256(canonical business payload + sourceBundleId + modelVersion)`.

`ledgerId` is the SHA-256 digest of the complete canonical ledger business payload. Wall-clock generation time is excluded, making the result byte-stable for identical inputs.

Outcome observation is a later additive record referencing `recommendationId`; R0.1 does not mutate recommendations into claims of successful execution.

## 11. Error contract

All commercial-intelligence validation failures use:

```python
CommercialIntelligenceValidationError(ValueError)
```

The module rejects, among other cases:

- wrong evidence contract;
- evidence digest/canonical-payload mismatch;
- malformed or non-object snapshots;
- non-finite or negative numeric values where forbidden;
- fractional, zero, negative, or malformed `leadTimeDays`;
- future-dated demand signals;
- unknown SKUs or signal types;
- non-UTF-8 demand-signal CSV uploads.

No error path performs an operational side effect.

## 12. UI behavior

The Commercial Intelligence page displays:

1. Demand Matrix
2. Ready Goods Routes
3. Replenishment Recommendations
4. Assortment Risks
5. Deterministic intelligence contract / ledger export

Boundary notice:

> Recommendations are advisory only. Warden/operator authorization is required before any inventory, pricing, order, or marketplace action.

## 13. Verification strategy

The regression suite covers:

- evidence contract validation and cryptographic tamper rejection;
- strict integer validation for lead time;
- malformed snapshot rejection;
- signal normalization and UTF-8 handling;
- regional demand scoring and global-demand leakage prevention;
- UNSCOPED demand fallback;
- zero-demand days-cover behavior;
- ready-stock and inbound-only replenishment routing;
- zero-stock investigation routing;
- self-describing recommendation records;
- slow-stock and explicit-lineage broken-size detection;
- deterministic recommendation and ledger IDs;
- no external-I/O imports in the core engine;
- existing evidence-adapter regression tests.

GitHub Actions additionally verifies:

```text
uv lock --check
uv sync --locked
python -m py_compile (all governed modules)
unittest discovery
direct evidence-adapter tests
direct commercial-intelligence tests
```

## 14. Acceptance criteria

R0.1 is acceptable for review when:

- cryptographic evidence integrity is verified before inference;
- existing evidence tests remain green;
- all commercial-intelligence and review-regression tests pass;
- regional signal routing uses only regional effective demand and does not leak global demand;
- inbound-only low-cover stock cannot be mislabeled sufficient-cover `HOLD`;
- every recommendation is evidence-linked, model-versioned, and `RECOMMENDED_ONLY`;
- canonical recommendation and ledger outputs are deterministic;
- no operational write integration exists;
- absent region or style/size evidence is represented explicitly.

## 15. Out of scope

- automatic Warden approval;
- direct LOGIC ERP or Easycom writes;
- marketplace inventory updates;
- autonomous pricing;
- production planning;
- fabric optimization;
- machine-learning training;
- cross-store transfer execution;
- persistent database storage;
- BNR/ARK membership mutation.

Those remain later releases after R0.1 establishes the governed evidence → recommendation → outcome contract.
