# VOI Commercial Intelligence R0.1 — Design

Date: 2026-09-08
Status: Design approved for specification; implementation pending spec review
Repository: `Esomoire-consultancy-Company/VJRIPL.synnergyzehub`
Target branch: `feat/voi-commercial-intelligence-r0-1`

## 1. Purpose

Add the first governed commercial-intelligence layer above the existing read-only VOI inventory evidence bridge. R0.1 converts validated evidence into deterministic recommendations and outcome-ready ledger records. It does not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, or payments.

The initial release implements six bounded capabilities:

- CI-001 Demand Signal Normalizer
- CI-002 SKU × Region Demand Matrix
- CI-003 Ready Goods Router
- CI-004 Store Replenishment Recommendation
- CI-005 Broken Size / Slow Stock Detection
- CI-006 Recommendation → Outcome Ledger

## 2. Existing substrate

The repository already contains `VOI-INVENTORY-EVIDENCE-001`, implemented by `voi_evidence_adapter.py`, plus a Streamlit ingestion surface in `inventory_evidence_bridge.py` and regression coverage in `tests/test_voi_evidence_adapter.py`.

That contract remains authoritative and unchanged. R0.1 consumes its validated output rather than duplicating ERP/OMS parsing.

## 3. Architectural boundary

The flow is:

```text
LOGIC / OMS exports
      ↓
VOI-INVENTORY-EVIDENCE-001
      ↓
Commercial Intelligence R0.1
      ↓
Recommendation object
      ↓
Warden / operator approval boundary
      ↓
Future execution adapter (out of scope)
      ↓
Outcome observation
```

Rules:

1. Evidence is input, not authority to execute.
2. Commercial Intelligence emits recommendations only.
3. No R0.1 function may call external commerce systems or mutate operational inventory.
4. Every recommendation carries source evidence references and a model version.
5. Recommendation IDs are deterministic digests of canonical recommendation payloads.
6. All heuristics are explicit and versioned; no hidden stochastic behavior is permitted in R0.1.

## 4. Considered approaches

### A. Extend the existing evidence adapter directly

Pros: fewer files.

Cons: mixes evidence normalization and commercial inference, weakens the read-only evidence boundary, and makes future model changes harder to audit.

Rejected.

### B. Create a separate commercial-intelligence module consuming evidence bundles

Pros: preserves the existing contract, isolates inference logic, supports deterministic testing, and allows the recommendation engine to evolve independently.

Selected.

### C. Build a new service/API immediately

Pros: clean deployment boundary.

Cons: unnecessary operational surface before the business rules are proven; introduces authentication, persistence, and deployment concerns prematurely.

Deferred until after R0.1 proves the decision contracts.

## 5. Components

### 5.1 `voi_commercial_intelligence.py`

Pure Python module with no Streamlit dependency and no external I/O. It owns validation, scoring, routing, recommendation construction, and canonical ledger serialization.

Public functions:

```python
normalize_demand_signals(rows, *, observed_at) -> list[dict]
build_demand_matrix(inventory_bundle, demand_signals=None) -> list[dict]
route_ready_goods(demand_matrix, *, target_days_cover=14) -> list[dict]
build_replenishment_recommendations(routes, inventory_bundle) -> list[dict]
detect_assortment_risks(inventory_bundle, *, slow_stock_days=45) -> list[dict]
build_recommendation_ledger(recommendations, *, model_version) -> dict
```

Function names may be adjusted for existing repository naming conventions, but responsibilities must remain separated.

### 5.2 `commercial_intelligence_bridge.py`

Streamlit read-only surface. It:

- consumes the last validated inventory evidence bundle from session state or accepts a validated bundle JSON upload;
- accepts an optional demand-signal CSV;
- displays SKU/region demand, ready-goods routes, replenishment recommendations, and assortment risks;
- exports a canonical recommendation ledger JSON;
- explicitly states that export does not authorize execution.

### 5.3 `inventory_evidence_bridge.py`

Small additive change only: after a bundle validates, retain it in `st.session_state.voi_inventory_evidence_bundle` so the intelligence page can consume the exact validated object without re-parsing source CSVs.

### 5.4 `app.py`

Add a `Commercial Intelligence` navigation item and route. No other application flow changes are required.

### 5.5 Tests

Add `tests/test_voi_commercial_intelligence.py` using the repository's existing `unittest` style.

## 6. Input contracts

### 6.1 Inventory evidence

Input must satisfy the existing `VOI-INVENTORY-EVIDENCE-001` shape. The commercial module must reject malformed or unrecognized contracts instead of silently interpreting them.

Required snapshot fields used in R0.1:

- `sku`
- `available`
- `avgDailyDemand`
- `confirmedInbound`
- `leadTimeDays`
- `unitCost`
- `campaignUpliftPct`
- `observedAt`
- `evidenceRefs`

### 6.2 Optional demand signals

CSV columns:

```text
sku,region_id,signal_type,signal_value,observed_at
```

Allowed R0.1 signal types:

- `PRODUCT_VIEW`
- `ADD_TO_CART`
- `PURCHASE`
- `RETURN`
- `STOCKOUT`

Validation rules:

- SKU must exist in the inventory evidence bundle.
- `region_id` is required and non-empty.
- `signal_value` must be finite and non-negative.
- `observed_at` must be ISO-8601 and may not be after the inventory evidence observation time.
- Unknown signal types are rejected.

If no regional signals are provided, the engine creates a single `UNSCOPED` region from existing inventory/sales evidence. This preserves usefulness without inventing geographic precision.

## 7. CI-001 — Demand Signal Normalizer

Normalized signal object:

```json
{
  "sku": "VOI-SKU-001",
  "regionId": "BLR-NORTH",
  "signalType": "PURCHASE",
  "signalValue": 8.0,
  "observedAt": "2026-09-08T04:30:00Z"
}
```

The normalizer must be deterministic and preserve no unvalidated source fields.

## 8. CI-002 — SKU × Region Demand Matrix

R0.1 is a transparent heuristic baseline, not a predictive ML model.

For explicit regional signals, calculate a raw intent score:

```text
raw_intent =
  0.05 × PRODUCT_VIEW
+ 0.25 × ADD_TO_CART
+ 1.00 × PURCHASE
+ 0.50 × STOCKOUT
- 1.00 × RETURN
```

Clamp the raw score at zero.

Within each region, scale positive raw scores to a `0..100` `demandScore` using the largest raw score in that region. If every score is zero, all demand scores are zero.

For `UNSCOPED`, derive `raw_intent` from `avgDailyDemand × demandWindowDays` and scale across SKUs in the same way.

Each matrix row also carries:

- `available`
- `confirmedInbound`
- `avgDailyDemand`
- `leadTimeDays`
- `daysCover`
- `evidenceRefs`

`daysCover` is:

```text
(available + confirmedInbound) / avgDailyDemand
```

When demand is zero, `daysCover` is represented as `null`, not infinity.

## 9. CI-003 — Ready Goods Router

The router classifies each SKU/region row without executing movement.

R0.1 route classes:

- `REPLENISH`
- `HOLD`
- `INVESTIGATE`

Rules:

1. `REPLENISH` when `avgDailyDemand > 0`, `daysCover < target_days_cover`, and `available > 0`.
2. `INVESTIGATE` when demand exists but `available + confirmedInbound == 0`.
3. `HOLD` otherwise.

The router records the rule that fired so operators can audit why a recommendation exists.

## 10. CI-004 — Store Replenishment Recommendation

For `REPLENISH` rows, calculate a target quantity:

```text
target_stock = avgDailyDemand × target_days_cover
recommended_qty = max(0, target_stock - confirmedInbound)
```

The R0.1 recommendation is advisory. It does not infer a source warehouse or execute a transfer because the current evidence contract does not contain location-level source stock.

Recommendation object:

```json
{
  "decisionClass": "REPLENISH",
  "sku": "VOI-SKU-001",
  "regionId": "BLR-NORTH",
  "recommendedQty": 18.0,
  "targetDaysCover": 14,
  "reason": {
    "rule": "LOW_DAYS_COVER_WITH_READY_GOODS",
    "daysCover": 4.3,
    "demandScore": 91.0
  },
  "authorityState": "RECOMMENDED_ONLY",
  "evidenceRefs": []
}
```

No recommendation is represented as approved, authorized, or executed.

## 11. CI-005 — Broken Size / Slow Stock Detection

### Slow stock

A SKU is `SLOW_STOCK` when:

- available stock is positive; and
- `avgDailyDemand == 0`, or calculated stock cover exceeds `slow_stock_days`.

### Broken size

Broken-size detection requires style/size lineage that the current evidence contract does not provide. R0.1 therefore supports broken-size detection only when optional snapshot fields `styleId` and `size` are present in a future/additive evidence bundle. The commercial module must not infer style families from SKU strings.

When those fields are absent, the detector returns no broken-size finding and records capability state `INSUFFICIENT_STYLE_SIZE_EVIDENCE` in the intelligence summary.

This keeps R0.1 truthful rather than fabricating assortment relationships.

## 12. CI-006 — Recommendation → Outcome Ledger

Ledger contract: `VOI-COMMERCIAL-INTELLIGENCE-001`.

Top-level fields:

```json
{
  "schemaVersion": "1.0.0",
  "contract": "VOI-COMMERCIAL-INTELLIGENCE-001",
  "modelVersion": "VOI-CI-R0.1",
  "sourceBundleId": "sha256:...",
  "generatedAt": "...",
  "recommendations": [],
  "risks": [],
  "capabilityState": {},
  "integrity": {
    "algorithm": "SHA-256",
    "digest": "sha256:..."
  }
}
```

Each recommendation receives a deterministic `recommendationId` calculated from its canonical business payload plus `sourceBundleId` and `modelVersion`.

Outcome fields are initially absent or `null`. A later observer may append a separate outcome record referencing `recommendationId`; R0.1 must not mutate the original recommendation into a claim of success.

## 13. Error handling

Introduce `CommercialIntelligenceValidationError` for contract and signal failures.

Reject:

- wrong evidence contract;
- malformed evidence bundle;
- non-finite numeric values;
- negative stock or signals;
- demand signals after evidence observation time;
- unknown SKUs;
- unknown signal types;
- duplicate or contradictory source keys where deterministic aggregation is not possible.

No exception path may trigger operational side effects.

## 14. UI behavior

The Commercial Intelligence page shows four primary sections:

1. Demand Matrix
2. Ready Goods Routes
3. Replenishment Recommendations
4. Assortment Risks

A fifth section exposes bundle identity, source evidence references, model version, and downloadable JSON.

Every page includes a visible boundary notice:

> Recommendations are advisory only. Warden/operator authorization is required before any inventory, pricing, order, or marketplace action.

## 15. Test strategy

Minimum tests:

1. rejects wrong evidence contract;
2. produces deterministic intelligence ledger IDs;
3. normalizes valid regional signals;
4. rejects future-dated signals;
5. rejects unknown signal types;
6. rejects unknown SKU signals;
7. builds UNSCOPED demand matrix without regional signals;
8. scales regional demand scores deterministically;
9. returns null days cover for zero demand;
10. routes low-cover ready goods to REPLENISH;
11. routes zero-stock demand to INVESTIGATE;
12. builds replenishment quantity without claiming authorization;
13. detects zero-demand stock as SLOW_STOCK;
14. does not infer broken sizes without style/size evidence;
15. detects broken sizes when explicit style/size evidence is present;
16. preserves source evidence references in recommendation records;
17. commercial intelligence module performs no external I/O;
18. existing 12 evidence-adapter regression tests continue to pass.

## 16. Acceptance criteria

R0.1 is acceptable when:

- the existing evidence contract and tests remain green;
- all new intelligence tests pass;
- output is deterministic for identical evidence and signals;
- no operational write integration exists;
- the UI can consume a validated evidence bundle and export a recommendation ledger;
- every recommendation is evidence-linked and `RECOMMENDED_ONLY`;
- absent regional or style/size evidence is represented explicitly rather than guessed.

## 17. Out of scope

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

Those become later releases after R0.1 establishes trustworthy evidence → recommendation → outcome contracts.
