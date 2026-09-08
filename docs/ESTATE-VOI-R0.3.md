# ESTATE-VOI-R0.3

## Purpose

R0.3 introduces governed commercial transitions between a qualified Estate possibility and any future operational execution path.

The objective is to prove that commercial intent can be persisted, evidence-bound and authority-bound before an external system is ever allowed to act.

## Canonical chain

`EST-POS -> EST-PROP -> EST-DEAL -> EST-EXEC (NO_EXTERNAL_EFFECT) -> future governed connector -> operational acknowledgement -> EST-REAL`

R0.3 stops at `EST-EXEC` and does not enable the governed connector step.

## Evidence binding

A Proposition may be persisted only when:

1. its `EST-POS-*` possibility exists,
2. that possibility is currently `QUALIFIED`,
3. a `VOI-INVENTORY-EVIDENCE-001` bundle has been registered,
4. the bundle uses `READ_ONLY_EXPORT`,
5. the SHA-256 digest, canonical payload and bundle ID all agree.

The Estate registry recomputes the canonical payload digest from the supplied payload. It does not trust a supplied bundle ID without verification.

## Proposition Record

Canonical namespace: `EST-PROP-*`

Required fields:

- `proposition_id`
- `possibility_id`
- `partner`
- `success_criteria`
- `evidence_bundle_id`

Persisting a Proposition advances the Estate-local possibility projection from `QUALIFIED` to `PROPOSITION`.

This transition has no external operational effect.

## Deal Record

Canonical namespace: `EST-DEAL-*`

Required fields:

- `deal_id`
- `proposition_id`
- `acceptance_evidence_ref`
- `warden_decision_ref`
- `river_receipt_ref`

A Deal cannot be recorded solely because a salesperson or marketplace contact says the proposal was accepted. Commercial acceptance evidence and governance references must both exist.

Persisting a Deal advances the Estate-local possibility projection to `DEAL`.

This transition does not create an ERP order, allocate stock, publish a listing, book capacity or release production.

## Governed Execution Intent

Canonical namespace: `EST-EXEC-*`

Required fields:

- `execution_intent_id`
- `deal_id`
- `warden_decision_ref`
- `river_receipt_ref`
- `idempotency_key`
- `effect_state = NO_EXTERNAL_EFFECT`

An execution intent means:

> Estate has a commercially accepted and governance-bound instruction that may become eligible for execution after a separately admitted operational adapter confirms authority, current state and provider acceptance.

It does **not** mean execution occurred.

R0.3 enforces `NO_EXTERNAL_EFFECT` at the database boundary. An intent cannot be persisted with another effect state.

## Idempotency

Every execution intent requires a non-empty idempotency key.

The local Alpha registry enforces uniqueness of that key so the same intended effect cannot be represented as multiple independent execution instructions merely because a request was retried.

Future external adapters must carry the same or a derived governed idempotency identity into the provider transaction.

## Warden and River semantics

R0.3 stores references; it does not pretend to be Warden or River.

- `warden_decision_ref` points to the authority decision governing the transition.
- `river_receipt_ref` points to the evidence receipt for the transition.
- Estate does not synthesize either as proof of external authorization.

A production version must validate these references against admitted Warden/River services rather than treating non-empty strings as sufficient.

## Estate Board Governance Chain

The Estate Board now exposes a read-only governance view for:

- Propositions,
- accepted Deals,
- governed execution intents,
- evidence bundle identity,
- Warden decision references,
- River receipt references,
- idempotency keys,
- effect state.

There is intentionally no operational execute control in R0.3.

## Preserved external-system boundaries

R0.3 does not mutate:

- Logic ERP,
- Easycom,
- Myntra,
- Flipkart,
- Centro,
- warehouse inventory,
- factory production controls,
- payment systems.

The existing VOI Inventory Evidence Bridge remains a read-only evidence source.

## R0.4 productionization gates

Before any execution intent may cause an external effect, the next slice must provide at minimum:

1. DigitalMe actor/principal identity on every material transition,
2. live Warden decision validation rather than opaque-reference presence only,
3. River append-only receipt validation and transition journaling,
4. admitted provider adapters for Logic/Easycom/channel systems,
5. capability-scoped service principals and secrets isolation,
6. provider-side idempotency or reconciliation keys,
7. pre-effect current-state verification,
8. post-effect observation and provider acknowledgement,
9. exception/failure journal,
10. reconciliation between Estate intent and operational truth,
11. explicit promotion rules from `EST-EXEC` to an externally effective execution state,
12. no automatic promotion to `EST-REAL`; Reality still requires observed commercial outcome evidence.

## Non-goal

R0.3 is not an automation release.

It is the governance and evidence bridge that must exist **before** Estate is permitted to automate commercial execution.
