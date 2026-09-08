# VOI Commercial Intelligence R0.1 — As-Built Implementation and Verification Plan

Date: 2026-09-08
Status: Implemented on draft PR #8; review corrections applied
Branch: `feat/voi-commercial-intelligence-r0-1`
Base: `main`
Spec: `docs/superpowers/specs/2026-09-08-voi-commercial-intelligence-r0-1-design.md`
Model: `VOI-CI-R0.1`

## Goal

Build a deterministic, evidence-linked commercial-intelligence layer above the existing read-only `VOI-INVENTORY-EVIDENCE-001` bundle without creating any operational write path.

The implementation must remain advisory only and must not write to:

- LOGIC ERP
- Easycom
- marketplaces
- inventory
- pricing
- orders
- payments
- BNR state
- ARK state

## Architecture

```text
VOI-INVENTORY-EVIDENCE-001
        ↓
cryptographic integrity verification
        ↓
VOI Commercial Intelligence R0.1
        ↓
Demand Matrix
Ready Goods Routes
Replenishment Recommendations
Assortment Risks
        ↓
VOI-COMMERCIAL-INTELLIGENCE-001
        ↓
Warden / operator authorization boundary
```

The core engine is pure Python and deterministic. Streamlit exists only at the read-only presentation/upload edge.

## Governed files

### Core

- `voi_commercial_intelligence.py`

Owns:

- evidence validation
- demand-signal normalization
- regional/UNSCOPED demand matrix construction
- ready-goods routing
- replenishment recommendation construction
- assortment-risk detection
- deterministic recommendation and ledger IDs

### UI edge

- `commercial_intelligence_bridge.py`

Owns:

- optional evidence JSON upload
- optional demand-signal CSV upload
- read-only rendering
- recommendation-ledger download

### Existing evidence bridge

- `inventory_evidence_bridge.py`

Additive change only: retain the exact successfully validated bundle at:

```python
st.session_state.voi_inventory_evidence_bundle
```

### Navigation

- `app.py`

Adds the Commercial Intelligence route under Market Intelligence.

### Packaging / CI

- `pyproject.toml`
- `.github/workflows/voi-evidence-bridge.yml`

### Tests

- `tests/test_voi_commercial_intelligence.py`
- `tests/test_voi_commercial_intelligence_review.py`
- existing `tests/test_voi_evidence_adapter.py`

## Verified public API

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

## Implementation sequence and evidence

### Task 1 — Evidence validation and CI-001 signal contract

Completed via TDD.

Implemented:

- `CommercialIntelligenceValidationError`
- evidence-contract recognition
- signal SKU validation
- signal-type validation
- signal timestamp validation
- finite/non-negative signal values
- deterministic normalized signal ordering

Review hardening subsequently added:

- cryptographic recomputation of canonical evidence payload
- verification of `bundleId`
- verification of `integrity.digest`
- verification of `integrity.canonicalPayload`
- strict `SHA-256` algorithm check
- non-object snapshot rejection through the domain validation error
- finite positive integer validation for `leadTimeDays` without truncation

### Task 2 — CI-002 demand matrix, CI-003 routing, CI-004 replenishment

Completed via TDD.

#### UNSCOPED mode

When regional demand signals are absent:

```text
rawIntent = baselineAvgDailyDemand × demandWindowDays
effectiveDailyDemand = baselineAvgDailyDemand
demandBasis = BUNDLE_AVG_DAILY_DEMAND
```

#### Regional mode

Raw regional intent is:

```text
0.05 × PRODUCT_VIEW
+ 0.25 × ADD_TO_CART
+ 1.00 × PURCHASE
+ 0.50 × STOCKOUT
- 1.00 × RETURN
```

Clamp negative raw intent to zero.

The reviewed regional-demand correction is:

```text
effectiveDailyDemand = max(rawIntent, 0) / demandWindowDays
```

This prevents global historical SKU demand from leaking into unrelated regions.

Every matrix row records:

- `baselineAvgDailyDemand`
- `effectiveDailyDemand`
- `demandBasis`
- compatibility alias `avgDailyDemand = effectiveDailyDemand`
- `daysCover` derived from effective demand

#### Routing

```text
INVESTIGATE
  when effective demand exists and available + inbound == 0

REPLENISH / LOW_DAYS_COVER_WITH_READY_GOODS
  when cover is below target and available > 0

REPLENISH / LOW_DAYS_COVER_WITH_INBOUND_ONLY
  when cover is below target, available == 0, and inbound > 0

HOLD
  otherwise
```

This closes the reviewed defect where inbound-only low-cover stock could be incorrectly labeled sufficient-cover `HOLD`.

#### Replenishment

```text
targetStock = effectiveDailyDemand × targetDaysCover
recommendedQty = max(0, targetStock - available - confirmedInbound)
```

Every recommendation includes:

- `modelVersion: VOI-CI-R0.1`
- `decisionClass`
- `sku`
- `regionId`
- `recommendedQty`
- `targetDaysCover`
- explicit reason/rule
- `demandBasis`
- `effectiveDailyDemand`
- `authorityState: RECOMMENDED_ONLY`
- evidence references

### Task 3 — CI-005 assortment risk and CI-006 deterministic ledger

Completed via TDD.

#### Slow stock

Uses evidence-bundle historical demand, not regional signal demand.

A SKU is slow stock when available stock is positive and either:

- baseline demand is zero; or
- historical stock cover exceeds the configured slow-stock threshold.

#### Broken size

Broken-size detection is permitted only when explicit `styleId` and `size` evidence exists. No SKU-text inference is allowed.

Without explicit lineage:

```text
brokenSizeDetection = INSUFFICIENT_STYLE_SIZE_EVIDENCE
```

#### Ledger

Contract:

```text
VOI-COMMERCIAL-INTELLIGENCE-001
```

Deterministic identifiers:

```text
recommendationId = SHA-256(canonical recommendation business payload + source bundle + model version)
ledgerId = SHA-256(canonical ledger business payload)
```

Wall-clock generation time is excluded from the canonical ledger.

### Task 4 — Read-only Streamlit bridge

Completed.

The bridge:

- consumes the last validated session bundle or uploaded evidence JSON;
- validates evidence integrity again before inference;
- accepts optional UTF-8 regional demand-signal CSV;
- rejects malformed headers, duplicate headers, extra fields, and non-UTF-8 input;
- displays demand matrix, routes, recommendations, and risks;
- exports the deterministic ledger JSON;
- displays a visible advisory-only authorization boundary.

No write or execution button is introduced.

### Task 5 — Packaging and CI

Completed.

`pyproject.toml` registers:

- `voi_commercial_intelligence`
- `commercial_intelligence_bridge`

No new dependency was required, so `uv.lock` remains governed by the existing dependency set.

CI verifies:

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

## Review-gate corrections

An independent review identified eight findings. Their disposition is:

| Finding | Disposition |
| --- | --- |
| Evidence bundle accepted solely on `sha256:` prefix | Fixed with canonical payload digest verification |
| Non-object snapshot could escape domain error | Already fixed; regression test added |
| Fractional `leadTimeDays` silently truncated | Fixed with strict finite integer validation |
| Regional signals did not drive routing correctly | Fixed with regional `effectiveDailyDemand` |
| Inbound-only low cover could route `HOLD` | Fixed with explicit inbound-only replenishment rule |
| Standalone recommendation omitted `modelVersion` | Fixed; every recommendation now self-describes model version |
| Non-UTF-8 signal CSV could escape UI validation | Already fixed; regression test added |
| Design API signatures diverged from implementation | Fixed by synchronizing design and this as-built plan |

## Verification checklist

The PR is reviewable only when all of the following remain true:

- [x] Existing evidence adapter regression suite passes.
- [x] Evidence payload tampering is rejected.
- [x] Fractional lead times are rejected.
- [x] Malformed snapshots produce `CommercialIntelligenceValidationError`.
- [x] Non-UTF-8 demand-signal CSV is rejected cleanly.
- [x] UNSCOPED demand behavior is deterministic.
- [x] Regional demand uses signal-derived effective demand without global leakage.
- [x] Zero-stock demand routes to `INVESTIGATE`.
- [x] Ready-stock low cover routes to `REPLENISH`.
- [x] Inbound-only low cover routes to `REPLENISH` with its own rule.
- [x] Recommendations carry `modelVersion` and `RECOMMENDED_ONLY`.
- [x] Broken-size detection requires explicit lineage.
- [x] Recommendation IDs and ledger ID are deterministic.
- [x] Core commercial-intelligence module has no external-I/O imports.
- [x] Governed modules compile under CI.
- [x] Dependency lock check passes.

## Promotion boundary

A green PR does **not** mean automatic commercial execution is admitted.

The correct state transition remains:

```text
EVIDENCE_VALIDATED
→ RECOMMENDATION_GENERATED
→ REVIEWED
→ WARDEN / OPERATOR AUTHORIZATION (future execution boundary)
→ EXECUTION (out of R0.1 scope)
→ OUTCOME OBSERVATION (future additive record)
```

R0.1 stops at governed recommendation generation and export.

## Out of scope

- automatic Warden approval
- direct LOGIC ERP writes
- direct Easycom writes
- marketplace updates
- autonomous pricing
- production planning
- fabric optimization
- ML training
- cross-store transfer execution
- persistent intelligence database storage
- BNR/ARK mutation

These remain later releases after the evidence → recommendation contract is accepted and separately admitted for execution.
