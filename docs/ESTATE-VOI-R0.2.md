# ESTATE-VOI-R0.2

## Purpose

Extend the R0.1 Possibility-to-Reality contract with an Alpha-grade persistent Estate registry and a first VOI Estate Board while preserving all existing operational authorities.

## New capabilities in R0.2

1. SQLite-backed local Possibility Registry.
2. Seeded VOI Capability Ledger.
3. External evidence-reference storage on possibilities.
4. Expiry/requalification discovery without deleting history.
5. Estimated contribution guardrail.
6. Working-capital guardrail.
7. Estate-local resource reservation conflict detection.
8. Channel templates for Myntra, Flipkart and Centro.
9. Estate Board portfolio metrics and local possibility intake.

## Alpha persistence semantics

`estate_registry.py` uses SQLite as an Alpha/local persistence mechanism only.

Default path:

`./.estate/estate_alpha.db`

The path may be overridden using `ESTATE_DB_PATH`.

The local database is intentionally ignored by Git.

This is not the production multi-user system of record. It exists to prove object identity, lifecycle persistence, commercial controls and UI behavior before shared infrastructure is admitted.

## Seeded VOI capability namespace

- `CAP-PRODUCT-DESIGN`
- `CAP-DENIM-MANUFACTURING`
- `CAP-WASHING`
- `CAP-WH-BLR`
- `CAP-ERP-LOGIC`
- `CAP-OMS-EASYCOM`
- `CAP-CHANNEL-MYNTRA`
- `CAP-CHANNEL-FLIPKART`
- `CAP-CHANNEL-CENTRO`
- `CAP-PHOTOGRAPHY`
- `CAP-CATALOGUE`
- `CAP-RETURNS`
- `CAP-REPLENISHMENT`

Capability availability in Estate is an Estate assertion, not final operational truth. A material commitment must still obtain current evidence from the authoritative source and pass the applicable authority gate.

## Commercial guardrails

A possibility intake may evaluate:

- estimated revenue/value,
- estimated contribution,
- working capital required,
- minimum contribution threshold,
- maximum working-capital threshold.

A case outside the configured commercial guardrail is recorded as `HOLD`, not rejected and not executed.

Passing these financial guardrails does not itself produce `QUALIFIED`. The six R0.1 gates still govern qualification:

1. demand,
2. executable capability,
3. economics,
4. delivery time,
5. authority,
6. measurable outcome.

## Expiry and requalification

Possibilities may carry `expires_at`.

When the expiry time passes:

- the record is retained,
- history is not deleted,
- the Estate Board surfaces it as requiring requalification,
- no external system state changes automatically.

## Estate reservation semantics

R0.2 introduces `EST-RES-*` style local reservation records through the registry API.

These reservations exist only to detect competing Estate plans for the same logical resource and overlapping time window.

They are **not**:

- Logic ERP stock reservations,
- Easycom allocations,
- warehouse pick reservations,
- factory production bookings,
- marketplace commitments,
- purchase orders,
- Warden authorization decisions.

A future operational adapter must receive authorization, request reservation from the authoritative system and return an acknowledgement/evidence receipt before Estate may represent the reservation as operationally effective.

## Channel templates

### Myntra

External posture: create incremental category business using relevant assortment, availability and replenishment.

Default capability composition includes Logic ERP, Easycom, Myntra channel capability, warehouse and catalogue.

### Flipkart

External posture: create incremental marketplace business using price, catalogue, availability and geographic demand signals.

Default capability composition includes Logic ERP, Easycom, Flipkart channel capability, warehouse and catalogue.

### Centro

External posture: create incremental physical-retail business through differentiated assortment, allocation and replenishment.

Default capability composition includes Logic ERP, Centro retail capability, warehouse, product design and replenishment.

## Estate Board boundary

The Estate Board may create and read Estate-local planning records.

It must not directly mutate:

- Logic ERP,
- Easycom,
- Myntra,
- Flipkart,
- Centro,
- warehouse inventory,
- factory production controls.

The existing VOI Inventory Evidence Bridge remains the approved read-only pattern for importing operational observations until governed provider APIs/service principals are admitted.

## Productionization gates after R0.2

Before promoting Estate persistence and reservations beyond Alpha, require:

1. governed shared database with concurrency controls and migrations,
2. DigitalMe principal identity on mutations,
3. Warden authorization/decision references,
4. River receipts and append-only transition evidence,
5. Logic/Easycom/provider API contracts or governed service principals,
6. authoritative operational reservation acknowledgements,
7. idempotency keys for all external effects,
8. reconciliation between Estate intent and operational state,
9. role-based commercial approval for pricing, credit, production and inventory commitment,
10. monitoring for stale capabilities, expired evidence and unresolved reservation conflicts.

## Next slice

R0.3 should connect qualified Estate possibilities to the existing read-only inventory evidence bundle, introduce explicit Proposition/Deal persistence, and add Warden/River reference fields to every state-changing record before any operational connector is enabled.
