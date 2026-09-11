# MAT-VJRIPL-001 Benefit Register

## Purpose

The Benefit Register records what practical value accrues to the VJRIPL / VOI Matter from work performed here. It is deliberately separate from legal title, licence scope, confidentiality status, production authority and accounting recognition.

A benefit entry may depend on reusable Synnergyze background technology, third-party technology or external operational systems. That dependency does not erase the client-specific benefit; it must simply remain visible.

## Status values

- `LEGACY_PROTOTYPE` — useful historical/prototype work, not yet admitted as production Matter capability.
- `MATTER_CAPABILITY` — accepted as attributable Matter capability.
- `REVIEW_PENDING` — candidate benefit awaiting provenance/technical review.
- `SANDBOX_ONLY` — validated only in sandbox/non-production conditions.
- `PRODUCTION_ADMISSION_REQUIRED` — technically useful but not authorized for live external effects.

## Seed register

| Benefit ID | Capability / artifact | Matter benefit | Source | IP / provenance class | Authority state | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BEN-VOI-001 | Buying-house product/catalog/order portal | Demonstrates product discovery, product-detail, cart/order-booking and order-confirmation interaction patterns that can inform a VOI buyer/customer operating surface. | `app.py`, `onboarding.py`, `product_catalog.py`, `product_detail.py`, `order_booking.py`, `order_confirmation.py`; classified in `docs/LEGACY_PROVENANCE_REGISTER.md` | `THIRD_PARTY_PROTOTYPE` for the legacy demonstrator shell/flows; bounded later VOI evidence-bridge integration in `app.py` remains separately VOI-attributable | No live operational authority; sample SKUs, prices, MOQs, terms and timelines are not admitted VOI truth | `LEGACY_PROTOTYPE` |
| BEN-VOI-002 | Merchandiser interaction prototype | Demonstrates assisted merchandising, chat, meeting, task and order-support interaction concepts. | `merchandiser_agent.py`; classified in `docs/LEGACY_PROVENANCE_REGISTER.md` | `THIRD_PARTY_PROTOTYPE`; sample personas, mock contacts, canned responses and randomized metrics | No production identity, staffing, communication or KPI authority | `LEGACY_PROTOTYPE` |
| BEN-VOI-003 | Retailer / market-health analysis surface | Demonstrates external-market research, stock-analysis and comparative retailer-analysis presentation. | `retailer_analysis.py`, `stock_analysis.py`, `visualization.py`; classified in `docs/LEGACY_PROVENANCE_REGISTER.md` | `THIRD_PARTY_PROTOTYPE` + `PUBLIC_SOURCE_REFERENCE` / `THIRD_PARTY` dependencies for external market data | Research/advisory only; source freshness and provider terms require validation | `LEGACY_PROTOTYPE` |
| BEN-VOI-004 | VOI Inventory Evidence Contract | Converts operator-supplied ERP/OMS exports into validated, canonical, integrity-protected inventory evidence with source fingerprints and bundle identity. | `VOI-INVENTORY-EVIDENCE-001`, `voi_evidence_adapter.py`, evidence profile and bridge | Strong candidate `VOI_FOREGROUND` with reusable evidence mechanics potentially `SYNNERGYZE_BACKGROUND` | Read-only; evidence is not execution authority | `MATTER_CAPABILITY` |
| BEN-VOI-005 | VOI Commercial Intelligence R0.1 | Produces governed demand, routing, replenishment, assortment-risk and recommendation intelligence while preserving shared-stock and write-authority boundaries. | PR #8 / `feat/voi-commercial-intelligence-r0-1` | Mixed `VOI_FOREGROUND` + possible `SYNNERGYZE_BACKGROUND` primitives | Recommendation only; no operational write authority | `MATTER_CAPABILITY` |
| BEN-VOI-006 | Estate VOI R0.1 | Establishes VOI Client 001 possibility-to-reality lifecycle, qualification gates, capability checks and outcome-evidence requirements. | PR #6 / `estate-voi-r0-1-possibility-contract` | Mixed `VOI_FOREGROUND` + reusable Estate doctrine potentially `SYNNERGYZE_BACKGROUND` | No automatic ERP/OMS/production mutation | `MATTER_CAPABILITY` |
| BEN-VOI-007 | Estate VOI R0.2 | Adds persistent possibility registry, VOI capability ledger, commercial guardrails, advisory reservation-conflict detection and Estate Board. | PR #7 / `estate-voi-r0-2-registry` | Mixed `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` | Alpha-local/advisory; no operational reservation authority | `MATTER_CAPABILITY` |
| BEN-VOI-008 | Estate VOI R0.3 | Adds evidence-bound propositions/deals, Warden/River references, governed execution-intent records and read-only governance-chain view. | PR #9 / `estate-voi-r0-3-governed-transitions` | Mixed `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` | `NO_EXTERNAL_EFFECT`; references are not live authority validation | `MATTER_CAPABILITY` |
| BEN-VOI-009 | Estate VOI R0.4 controlled-effects design | Defines the bounded control loop for DigitalMe actor, Warden validation, River validation, sandbox provider admission, idempotency, observation, reconciliation and failure journal. | PR #10 / `estate-voi-r0-4-controlled-effects` | VOI-specific controlled-effect application + substantial reusable control-loop background design | Sandbox only; real providers and credentials excluded | `SANDBOX_ONLY` |
| BEN-VOI-010 | Matter governance envelope | Preserves VJRIPL benefit, provenance, IP classification, issue resolution and cross-Matter isolation at repository level. | `MATTER.yaml`, Matter/IP/provenance doctrine and GitHub templates | `SYNNERGYZE_BACKGROUND` governance pattern applied to this Matter; VJRIPL-specific manifest is Matter-specific | Governance metadata only | `MATTER_CAPABILITY` |
| BEN-VOI-011 | Legacy provenance classification | Converts ambiguous historical repository material into an explicit component-level record: reviewed prototypes are identified as prototypes; unknown binaries/assets remain explicitly unknown; VOI evidence capability stays separate. | Issue #13, `docs/LEGACY_PROVENANCE_REGISTER.md` | Matter-specific governance record using the reusable Matter/IP classification model | Classification only; no deletion, relicensing, publication, production effect or ownership determination | `MATTER_CAPABILITY` |
| BEN-VOI-012 | Publication and confidentiality governance | Gives VJRIPL / VOI a bounded publication model that separates the complete working Matter from public-qualified projections, protects client/data/provenance boundaries, records prior public exposure as a remediation condition, and prevents repository visibility from becoming silent publication/licensing authority. | Issue #15, `docs/PUBLICATION_CONFIDENTIALITY_POLICY.md`, `README.md`, `MATTER.yaml` publication policy | Matter-specific governance record using reusable Matter/publication controls; does not determine underlying legal title | Policy/proposed disposition only; no repository visibility, licence, deletion, takedown or history-rewrite authority | `MATTER_CAPABILITY` |
| BEN-VOI-013 | Component-level VOI foreground / Synnergyze background map | Preserves VJRIPL / VOI's complete attributable benefit while making reusable mechanisms separable from VOI contracts, policies, mappings and data/knowledge. It reduces the risk that future platform reuse silently exports VOI business logic/data, or that reusable platform mechanisms are accidentally treated as wholly client-specific merely because they were implemented in this Matter. | Issue #17, `docs/COMPONENT_IP_REGISTER.md`, updated `docs/IP_BOUNDARY.md` | Mixed Matter-specific classification record: `VOI_FOREGROUND`, `VOI_DATA_KNOWLEDGE`, `SYNNERGYZE_BACKGROUND`, `THIRD_PARTY_PROTOTYPE`; legal title remains separately evidenced | Classification and separation recommendations only; no code movement, assignment, licence, public release, cross-Matter export or production authority | `MATTER_CAPABILITY` |

## Benefit interpretation

A `MATTER_CAPABILITY` entry means this Matter can reliably point to the capability and its provenance as attributable work. It does **not** mean:

- all underlying IP is legally owned by VJRIPL / VOI;
- all reusable platform components are assigned to this Matter;
- third-party rights are displaced;
- confidential information may be disclosed;
- production credentials or system-write authority exist;
- a proposed branch or draft PR has been accepted into `main`.

A `LEGACY_PROTOTYPE` may still provide substantial design and learning value. It simply cannot be treated as production truth, admitted client data or operational authority without a later governed admission.

The component-level register further means that client benefit and reusable mechanism can coexist inside the same file. A reusable mechanism does not erase VJRIPL's attributable foreground/configuration benefit, and VJRIPL-specific use does not by itself assign unrelated reusable platform rights to the Matter.

## Benefit update rule

Every material Proposed Disposition should answer:

**What additional benefit does MAT-VJRIPL-001 receive if this disposition is accepted?**

If the answer is no new client benefit, the PR should explain why the change is nevertheless necessary for Matter integrity, risk reduction, evidence quality, maintenance or compliance.

## Future benefit accounting

Later versions may extend entries with measurable outcomes such as:

- incremental revenue or contribution;
- working-capital release;
- stock recovery;
- return reduction;
- lead-time reduction;
- conversion improvement;
- error/reconciliation reduction;
- production-capacity utilization;
- evidence completeness;
- issue-resolution cycle time.

Such metrics should be recorded only when supported by admitted evidence. Forecasts and recommendations must remain distinguishable from realized outcomes.
