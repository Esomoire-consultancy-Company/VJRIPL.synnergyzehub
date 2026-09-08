# Estate VOI R0.4 Controlled Effects Design

## Purpose

R0.4 is the first Estate slice that permits a bounded external effect, but only through an explicitly admitted sandbox provider adapter. It extends R0.3 from governed execution intent into controlled execution while preserving the separation between Estate commercial intent and operational system authority.

R0.4 must prove the full control loop before any Logic ERP, Easycom, Myntra, Flipkart, Centro, warehouse, factory, payment, or production credential is introduced.

## Architectural decision

Use a separate `estate_effect_runtime.py` module rather than continuing to grow `estate_registry.py`.

`estate_registry.py` remains responsible for commercial/governance records through `EST-EXEC`. `estate_effect_runtime.py` consumes an existing persisted execution intent and owns actor validation, Warden validation, River validation/journaling, provider admission, pre-effect verification, effect attempt, acknowledgement, post-effect observation, failure handling, and reconciliation.

This boundary is intentional: an Estate commercial record must never become an operational write merely because it exists in the registry.

## Canonical controlled-effect chain

`DigitalMe Actor -> EST-EXEC -> Warden validation -> River pre-effect validation -> provider admission -> pre-effect state verification -> effect attempt -> provider acknowledgement -> post-effect observation -> River post-effect journal -> reconciliation`

The successful terminal state is `RECONCILED`.

`RECONCILED` still does not mean `EST-REAL`. Reality remains a separate R0.1-R0.3 commercial outcome concept and requires observed business-outcome evidence.

## Scope

R0.4 permits exactly one class of executable adapter: an in-process sandbox provider.

R0.4 does not contain production credentials, production endpoints, production service principals, or production provider adapters.

A provider adapter whose registration is not explicitly marked `sandbox=True` must be rejected by the runtime.

## DigitalMe actor binding

Every controlled effect requires a `DigitalMeActor`:

- `actor_id`
- `principal_id`
- `active`

The actor becomes part of the effect record and is supplied to Warden validation.

An inactive actor must be blocked before provider state is read or changed.

R0.4 validates the actor contract locally. Production DigitalMe service validation is an R0.5+ concern.

## Warden validation contract

R0.4 defines a `WardenValidator` interface.

Input includes:

- actor
- execution intent
- provider ID
- operation
- Warden decision reference

Output is `WardenDecisionObservation` with:

- decision_ref
- allowed
- actor_id
- execution_intent_id
- provider_id
- operation
- reason

The runtime must reject the effect when the observation does not exactly match the requested actor, execution intent, provider, and operation, even if `allowed=True`.

A denied or mismatched decision creates a failure journal record and no provider effect.

R0.4 uses test/sandbox validators only. A real Warden network/service integration is not introduced here.

## River validation and journaling contract

R0.4 defines a `RiverGateway` interface with two responsibilities:

1. validate a supplied pre-effect receipt for the execution intent and event type `effect.pre_authorized`;
2. append a post-effect event after observation and return a River receipt reference.

The pre-effect receipt must validate against the current execution intent.

The post-effect event includes the effect ID, provider acknowledgement reference, observed state digest, and reconciliation outcome.

R0.4 uses a sandbox/in-memory River gateway in tests. A real RiverOS adapter remains outside this slice.

## Provider adapter admission

Each provider implements `ProviderAdapter` and exposes:

- `provider_id`
- `sandbox`
- `capabilities`
- `read_state(resource_id)`
- `apply(command)`
- `verify_effect(command, acknowledgement, observed_state)`

A provider must be registered with the runtime before use.

R0.4 accepts only `sandbox=True` adapters.

Capabilities are operation names. The first canonical sandbox operations are:

- `RESERVE_QUANTITY`
- `RELEASE_QUANTITY`

No adapter may receive an operation outside its registered capability set.

## Sandbox reservation provider

The first provider is `SandboxReservationProvider`.

It manages an in-memory logical resource state:

```json
{
  "available": 100,
  "reserved": 0
}
```

`RESERVE_QUANTITY` decreases `available` and increases `reserved`.

`RELEASE_QUANTITY` performs the reverse.

The provider enforces its own idempotency map. A repeated request with the same idempotency key returns the same acknowledgement rather than applying the effect twice.

The provider is not connected to Logic ERP, Easycom, a marketplace, warehouse, or factory.

## Effect command

`EffectCommand` contains:

- `effect_id` in `EST-EFFECT-*`
- `execution_intent_id`
- `provider_id`
- `operation`
- `resource_id`
- `parameters`
- `expected_pre_state_digest`
- `idempotency_key`

The runtime canonicalizes the provider state as stable JSON and computes SHA-256.

The effect is blocked when the actual pre-effect digest does not match `expected_pre_state_digest`.

This implements optimistic state verification and prevents an intent created against stale state from silently mutating newer state.

## Effect state machine

Normal path:

- `AUTHORIZATION_PENDING`
- `AUTHORIZED`
- `PRE_EFFECT_VERIFIED`
- `EFFECT_ATTEMPTED`
- `PROVIDER_ACKNOWLEDGED`
- `EFFECT_OBSERVED`
- `RECONCILED`

Side states:

- `DENIED`
- `BLOCKED`
- `FAILED`
- `UNKNOWN_EFFECT`
- `RECONCILIATION_REQUIRED`
- `REVOKED`

R0.4 persists the terminal and latest state for every attempt.

## Provider acknowledgement

A successful provider call returns `ProviderAcknowledgement`:

- `ack_id` in `EST-ACK-*`
- `provider_id`
- `provider_operation_id`
- `idempotency_key`
- `accepted`
- `message`

An acknowledgement is evidence that the provider accepted the request. It is not sufficient to establish success.

The runtime must read provider state again after acknowledgement.

## Post-effect observation

The post-effect read creates `EffectObservation`:

- `observation_id` in `EST-OBS-*`
- `effect_id`
- `resource_id`
- `state_digest`
- `state`

The adapter's `verify_effect()` determines whether the observed state is consistent with the requested command and provider acknowledgement.

If verification passes, reconciliation may become `RECONCILED`.

If verification fails, state becomes `RECONCILIATION_REQUIRED`.

## Reconciliation

`ReconciliationRecord` uses namespace `EST-REC-*` and stores:

- effect ID
- intended operation
- provider acknowledgement reference
- observed state digest
- outcome
- River post-effect receipt reference

Possible outcomes in R0.4:

- `RECONCILED`
- `RECONCILIATION_REQUIRED`
- `UNKNOWN_EFFECT`

The runtime never promotes a controlled effect directly to `EST-REAL`.

## Failure journal

Every denial, precondition mismatch, unsupported provider/capability, provider exception, unknown effect, or reconciliation failure creates `EffectFailureRecord` in `EST-FAIL-*`.

A failure record includes:

- effect ID
- execution intent ID
- stage
- state
- reason

Failures are append-only in R0.4.

## Unknown-effect rule

If the provider may have applied an effect but the client cannot determine whether it succeeded, the runtime records `UNKNOWN_EFFECT`.

The same idempotency key must not be blindly re-executed by the Estate runtime.

The next action is reconciliation against provider state/provider idempotency records.

The sandbox provider exposes a test hook that can simulate "apply then lose acknowledgement" so this behavior is covered by regression tests.

## Idempotency

R0.3 execution-intent idempotency and R0.4 effect idempotency are distinct but linked.

An R0.4 `EffectCommand.idempotency_key` must be unique within the effect runtime persistence layer.

A duplicate completed/reconciled effect key returns the existing effect result rather than creating a second provider effect.

A duplicate `UNKNOWN_EFFECT` key is blocked pending reconciliation.

The provider receives the same key.

## Persistence

`EstateEffectRuntime` uses the same SQLite database path as the R0.3 Estate registry but owns separate tables:

- `effect_actors`
- `effect_provider_adapters`
- `effect_attempts`
- `provider_acknowledgements`
- `effect_observations`
- `effect_reconciliations`
- `effect_failures`

The runtime must not depend on `EstateRegistry._conn` or other private internals. It may call the public `get_execution_intent()` method to prove the source intent exists.

SQLite remains Alpha-local persistence only.

## Runtime orchestration

`EstateEffectRuntime.execute()` performs these checks in order:

1. execution intent exists in Estate Registry;
2. actor is active;
3. provider is registered and sandbox-admitted;
4. provider capability admits requested operation;
5. effect idempotency key is not in an unsafe prior state;
6. Warden validation matches actor/intent/provider/operation and is allowed;
7. River pre-effect receipt validates;
8. provider pre-state is read and its digest equals the expected digest;
9. effect attempt is persisted as `PRE_EFFECT_VERIFIED`;
10. provider apply is called once;
11. acknowledgement is persisted;
12. provider state is re-read;
13. observation is persisted;
14. provider-specific effect verification runs;
15. River post-effect event is appended;
16. reconciliation record is persisted;
17. final state becomes `RECONCILED` or `RECONCILIATION_REQUIRED`.

Provider exceptions before the provider call is made become `FAILED`.

A provider `ProviderOutcomeUnknown` exception becomes `UNKNOWN_EFFECT`.

## Estate Board

R0.4 adds a read-only `Controlled Effects` section to the Estate Board.

It displays:

- effect ID
- execution intent ID
- DigitalMe actor
- provider
- operation
- effect state
- provider acknowledgement
- observation digest
- River post-effect receipt
- reconciliation outcome
- failure journal entries

The Board must not expose a production execute button.

A sandbox demo control may be added only if it is visibly labeled `SANDBOX` and only invokes `SandboxReservationProvider`.

For this slice, the initial implementation should remain read-only and use tests to exercise the sandbox effect runtime; a UI trigger is not necessary.

## Security and authority boundary

R0.4 introduces no secrets.

No provider credential is stored in the repository or local Estate database.

No production URL or API key is required.

A future real provider adapter must have a capability-scoped service principal, Warden admission, secrets isolation, provider-side idempotency/reconciliation semantics, and a separate production promotion decision.

## Testing requirements

Regression tests must prove at minimum:

1. inactive DigitalMe actor is blocked before effect;
2. Warden deny blocks effect;
3. mismatched Warden scope blocks effect;
4. invalid River pre-effect receipt blocks effect;
5. non-sandbox provider registration is rejected;
6. unsupported provider capability is rejected;
7. stale pre-state digest blocks effect;
8. successful sandbox reservation reaches `RECONCILED`;
9. provider acknowledgement alone does not bypass post-effect observation;
10. duplicate idempotency key does not apply the effect twice;
11. simulated apply-then-timeout produces `UNKNOWN_EFFECT` and a failure journal entry;
12. `UNKNOWN_EFFECT` cannot be blindly retried;
13. reconciliation failure produces `RECONCILIATION_REQUIRED`;
14. no existing R0.1-R0.3 or VOI evidence tests regress.

## Non-goals

R0.4 does not:

- connect to Logic ERP;
- connect to Easycom;
- connect to Myntra, Flipkart, Centro, AJIO, Amazon, or Shopify;
- alter warehouse stock;
- release production;
- alter prices;
- create purchase orders;
- move money;
- manage secrets;
- claim that a sandbox effect is a commercial Reality.

## Promotion boundary after R0.4

A later release may propose one real provider pilot only after the sandbox control loop is green and reviewed.

That future promotion must identify the exact provider, exact capability, exact service principal, exact Warden policy, exact pre/post-effect evidence, rollback/recovery semantics, and reconciliation SLA before production credentials are admitted.
