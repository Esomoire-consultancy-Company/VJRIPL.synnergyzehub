# ESTATE-VOI-R0.1

## Purpose

Establish VOI/Voyej as Estate Client 001 and freeze the first executable Possibility-to-Reality contract.

Estate is the commercial discovery, composition, decision and orchestration layer above existing operational systems. It does not replace Logic ERP, Easycom, marketplace systems, warehouse systems, or factory systems.

## Canonical lifecycle

`SOURCE -> EST-POS -> QUALIFICATION -> CAPABILITY CHECK -> EST-PROP -> EST-DEAL -> EXECUTION -> EST-REAL`

## Canonical objects

- `EST-POS-*` Possibility Record
- `CAP-*` Capability Record
- `EST-PROP-*` Proposition Record
- `EST-DEAL-*` Deal Record
- `EST-REAL-*` Reality Record

## Qualification gates

A possibility may become `QUALIFIED` only when all six gates are true:

1. demand
2. executable capability
3. economics
4. delivery time
5. authority
6. measurable outcome

Otherwise it remains conditional, is placed on hold, or is rejected.

## System preservation

- Logic ERP remains transactional enterprise truth.
- Easycom remains OMS/channel execution capability.
- Factory and warehouse systems remain physical execution truth.
- Marketplace systems remain channel truth.
- Estate consumes evidence and coordinates decisions without inventing operational state.

The existing VOI Inventory Evidence Bridge is the current read-only pattern for Logic/OMS evidence ingestion until governed provider APIs/service principals are available.

## Commercial provisions implemented in this slice

1. Possibility admission with canonical IDs.
2. Source provenance via `source`.
3. VOI Client 001 identity via `client_id`.
4. Capability registration and availability checking.
5. Six-gate qualification.
6. No proposition before qualification.
7. No proposition where a required capability is missing/unavailable.
8. No Deal without commercial acceptance evidence.
9. No Reality without outcome evidence.
10. Reality can carry realized revenue and realized contribution.

## Initial capability namespace

Recommended first registrations:

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

## Initial five pilot possibilities

1. Myntra growth possibility.
2. Flipkart growth possibility.
3. Centro proposition.
4. Warehouse-stock recovery possibility.
5. Factory-capacity utilization possibility.

## Non-goals for R0.1

- No direct Logic ERP mutation.
- No direct Easycom mutation.
- No automated inventory reservation yet.
- No automatic pricing commitment.
- No production release.
- No Warden authority bypass.
- No claim that channel acceptance equals realized commercial outcome.

## Next implementation slice

R0.2 should add:

- persistent Possibility Registry storage,
- Capability Ledger seeded with VOI assets,
- expiry/requalification,
- margin and working-capital guardrails,
- inventory reservation conflict detection,
- Estate Board UI,
- evidence references wired to the existing VOI evidence bundle,
- channel-specific templates for Myntra, Flipkart and Centro.
