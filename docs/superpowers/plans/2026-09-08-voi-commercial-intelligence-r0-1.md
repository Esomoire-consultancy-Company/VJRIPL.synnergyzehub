# VOI Commercial Intelligence R0.1 — As-Built Implementation and Verification Plan

Date: 2026-09-08
Status: Implemented on draft PR #8; two review rounds hardened
Branch: `feat/voi-commercial-intelligence-r0-1`
Base: `main`
Model: `VOI-CI-R0.1`
Spec: `docs/superpowers/specs/2026-09-08-voi-commercial-intelligence-r0-1-design.md`

## Goal

Build deterministic, evidence-linked VOI commercial-intelligence recommendations above `VOI-INVENTORY-EVIDENCE-001` without creating an operational write path.

R0.1 must not write to LOGIC ERP, Easycom, marketplaces, inventory, pricing, orders, payments, BNR, or ARK state.

## As-built flow

```text
VOI-INVENTORY-EVIDENCE-001
        ↓
cryptographic + shape validation
        ↓
Demand Matrix
        ↓
Ready Goods Routing
        ↓
Replenishment Advisory / Assortment Risks
        ↓
VOI-COMMERCIAL-INTELLIGENCE-001
        ↓
Warden / operator authorization boundary
```

## Governed files

- `voi_commercial_intelligence.py` — pure deterministic engine, no external I/O
- `commercial_intelligence_bridge.py` — read-only Streamlit edge
- `inventory_evidence_bridge.py` — retains exact validated bundle in session state
- `app.py` — Commercial Intelligence navigation
- `pyproject.toml` — package registration
- `.github/workflows/voi-evidence-bridge.yml` — governed CI gates
- `tests/test_voi_commercial_intelligence.py` — primary pure-logic suite
- `tests/test_voi_commercial_intelligence_review.py` — review regression suite
- existing `tests/test_voi_evidence_adapter.py` — evidence regression gate

## Verified public API

```python
validate_inventory_bundle(bundle: dict) -> dict
normalize_demand_signals(rows, *, inventory_bundle) -> list[dict]
build_demand_matrix(inventory_bundle, demand_signals=None) -> list[dict]
route_ready_goods(demand_matrix, *, target_days_cover=14) -> list[dict]
build_replenishment_recommendations(routes, *, target_days_cover=14) -> list[dict]
detect_assortment_risks(inventory_bundle, *, slow_stock_days=45) -> tuple[list[dict], dict]
build_recommendation_ledger(
    inventory_bundle,
    recommendations,
    risks,
    capability_state,
    *,
    model_version=MODEL_VERSION,
) -> dict
```

## Task 1 — Evidence and CI-001 signal contract

Implemented and review-hardened:

- evidence contract recognition
- canonical payload SHA-256 recomputation
- verification of `bundleId`, `integrity.digest`, algorithm, and canonical payload
- domain error normalization for malformed canonical JSON / `NaN`
- ISO-8601 string timestamp validation
- non-object snapshot rejection
- SKU must be an actual string
- all evidence references must be strings
- finite/non-negative numeric validation
- strict positive-integer `leadTimeDays`
- signal SKU/type/value/time validation
- UTF-8 CSV rejection path
- deterministic normalized ordering

## Task 2 — CI-002 demand matrix

### UNSCOPED

```text
rawIntent = baselineAvgDailyDemand × demandWindowDays
effectiveDailyDemand = baselineAvgDailyDemand
demandBasis = BUNDLE_AVG_DAILY_DEMAND
stockScope = AGGREGATE_UNSCOPED
```

### Regional

```text
rawIntent =
  0.05 × PRODUCT_VIEW
+ 0.25 × ADD_TO_CART
+ 1.00 × PURCHASE
+ 0.50 × STOCKOUT
- 1.00 × RETURN

effectiveDailyDemand = max(rawIntent, 0) / demandWindowDays
demandBasis = REGIONAL_SIGNAL_EQUIVALENT_DAILY_RATE
stockScope = SHARED_AGGREGATE
```

This prevents global historical SKU demand from leaking into unrelated regions.

Matrix rows preserve both `baselineAvgDailyDemand` and `effectiveDailyDemand`; the compatibility field `avgDailyDemand` equals the effective rate.

## Task 3 — CI-003 Ready Goods Router

```text
INVESTIGATE
  effective demand > 0 and available + inbound == 0

REPLENISH / LOW_DAYS_COVER_WITH_READY_GOODS
  effective demand > 0, cover below target, available > 0

REPLENISH / LOW_DAYS_COVER_WITH_INBOUND_ONLY
  effective demand > 0, cover below target, available == 0, inbound > 0

HOLD
  otherwise
```

`target_days_cover` is validated as a positive integer.

Routing is classification only; it does not allocate stock.

## Task 4 — CI-004 Replenishment recommendation

### UNSCOPED aggregate quantity

The aggregate bundle can support one aggregate quantity:

```text
targetStock = effectiveDailyDemand × targetDaysCover
recommendedQty = max(0, targetStock - available - confirmedInbound)
quantityState = QUANTIFIED_AGGREGATE_STOCK
```

### Regional shared-stock safeguard

The current evidence bundle does not contain location-level inventory. If the same SKU appears in multiple regional signal rows, the same global stock must not be independently subtracted for each region.

Therefore all regional recommendations emit:

```text
recommendedQty = null
quantityState = UNQUANTIFIED_SHARED_STOCK
```

Regional recommendations still expose demand score, effective demand, route class, target cover, and evidence refs, but numeric quantity waits for location-level stock evidence.

Every recommendation remains:

- `modelVersion: VOI-CI-R0.1`
- `authorityState: RECOMMENDED_ONLY`
- evidence-linked
- deterministic

## Task 5 — CI-005 assortment risk

Slow stock uses the historical evidence baseline. Broken-size detection requires explicit `styleId` + `size`; SKU strings are never parsed to invent lineage.

Without explicit lineage:

```text
brokenSizeDetection = INSUFFICIENT_STYLE_SIZE_EVIDENCE
```

## Task 6 — CI-006 ledger

Contract: `VOI-COMMERCIAL-INTELLIGENCE-001`.

- supplied `recommendationId` is removed before hashing
- computed recommendation ID is written after the sanitized business payload
- caller-controlled IDs cannot override the digest
- ledger ID is deterministic SHA-256 over the canonical ledger business payload
- wall-clock time is excluded

## Task 7 — Read-only UI

The Streamlit bridge:

- consumes a session bundle or uploaded JSON
- validates evidence before inference
- accepts optional UTF-8 demand-signal CSV
- displays demand, routes, recommendations, and risks
- exports the ledger JSON
- exposes no commerce execution controls

The pure commercial-intelligence test suite imports the Streamlit parser lazily so core test collection is not coupled to app dependencies.

## Review disposition

### Review round 1

| Finding | Resolution |
| --- | --- |
| `sha256:` prefix trusted without recomputation | Canonical payload digest verification added |
| Non-object snapshot could escape domain error | Object validation + regression |
| Fractional lead time truncated | Strict positive integer validation |
| Regional demand inherited global demand | Regional effective-demand derivation |
| Inbound-only low cover mislabeled `HOLD` | Dedicated replenishment rule |
| Recommendation lacked model version | `modelVersion` added |
| Non-UTF-8 signal file could crash | Domain validation path + regression |
| Design signatures diverged | Docs synchronized |

### Review round 2

| Finding | Resolution |
| --- | --- |
| Invalid typed bundle fields could leak built-in exceptions to UI | Validator normalizes timestamp/canonical JSON/type failures |
| Non-string timestamp | ISO-8601 string check |
| `NaN` canonicalization leaked `ValueError` | Canonical JSON errors normalized |
| Non-string snapshot SKU | Explicit string requirement |
| Non-string `evidenceRefs` | Element type validation |
| Regional recommendations double-count shared stock | Regional quantity set `null` / `UNQUANTIFIED_SHARED_STOCK` |
| Non-positive replenishment target | Positive integer gate |
| Caller ID could overwrite computed `recommendationId` | Input ID stripped; computed ID written last |
| Pure tests imported Streamlit/pandas at module load | Parser import moved inside parser tests |

## Verification commands / CI gates

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
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python tests/test_voi_evidence_adapter.py
uv run python tests/test_voi_commercial_intelligence.py
```

## Acceptance checklist

- [x] Evidence payload tampering rejected.
- [x] Invalid canonical JSON / NaN rejected via domain error.
- [x] Timestamps, SKUs, evidence refs, and lead times are type-validated.
- [x] Existing evidence adapter tests remain a hard regression gate.
- [x] Regional demand does not leak global demand.
- [x] Inbound-only low cover routes correctly.
- [x] Regional shared stock is not multiplied into multiple numeric quantities.
- [x] UNSCOPED aggregate quantity remains deterministic.
- [x] Target-cover parameters are positive integers.
- [x] Recommendation IDs cannot be caller-overridden.
- [x] Recommendations remain model-versioned, evidence-linked, and advisory.
- [x] Core engine has no external-I/O imports.
- [x] Dependency lock is unchanged and checked in CI.

## Promotion boundary

A green PR is not commercial execution authority.

```text
EVIDENCE_VALIDATED
→ RECOMMENDATION_GENERATED
→ REVIEWED
→ WARDEN / OPERATOR AUTHORIZATION (future)
→ EXECUTION (out of R0.1)
→ OUTCOME OBSERVATION (future)
```

Draft PR #8 must remain unmerged until an explicit integration decision is made.

## Out of scope

- automatic Warden approval
- direct ERP / OMS writes
- marketplace updates
- autonomous pricing
- location-level allocation without location-level evidence
- cross-store transfer execution
- production planning
- persistent intelligence database storage
- BNR/ARK mutation
