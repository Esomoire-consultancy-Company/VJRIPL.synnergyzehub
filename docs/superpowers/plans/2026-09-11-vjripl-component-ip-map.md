# VJRIPL Component IP Map Implementation Plan

> **Execution:** Build the component-level engineering/provenance map for Issue #17. This plan creates classification records only; it does not move, license, publish, delete, or assign code.

**Goal:** Separate VJRIPL / VOI-specific foreground and data/knowledge from reusable Synnergyze background mechanisms at the smallest practical component boundary.

**Base:** `governance/vjripl-publication-confidentiality` / draft PR #16.

## Constraints

- Repository/file placement does not determine legal title.
- Prefer mechanism/configuration separation over whole-file ownership assumptions.
- Preserve `VOI_DATA_KNOWLEDGE` as non-exportable by default.
- Third-party/provider rights remain controlling.
- Controlled contractual evidence may inform authority status but must not be copied into this public repository.
- Unresolved legal-title/licence questions remain explicitly unresolved.
- No code movement or repository visibility/licence change in this slice.

## Tasks

### 1. Evidence layer
- Classify generic parsing, validation, canonicalization and SHA-256 sealing mechanisms.
- Separate VOI contract IDs, LOGIC/OMS schemas, source semantics and client evidence mappings.
- Classify UI/CLI wrappers and test/CI boundaries.

### 2. Commercial Intelligence
- Separate deterministic recommendation/ledger mechanisms from VOI-specific signal types, weights, routing rules, evidence contract and model identity.
- Preserve aggregate/shared-stock and authority-state rules as attributable VOI application logic unless generalized by a later explicit extraction.

### 3. Estate R0.1-R0.4
- Separate generic possibility/deal/reality, registry, idempotency, Warden/River and controlled-effect mechanisms from VOI Client 001, channel templates, capability seeds, operational mappings and VOI-specific policy applications.
- Record R0.4 as design-only in the current stack.

### 4. Mixed surfaces
- Preserve the legacy/prototype boundary in `app.py` while identifying the bounded VOI routes as foreground application integration.
- Record Matter governance primitives as reusable background applied through VJRIPL-specific manifests/registers.

### 5. Register and linkage
- Create `docs/COMPONENT_IP_REGISTER.md`.
- Update `docs/IP_BOUNDARY.md` to make the register canonical for component classification.
- Update `docs/BENEFIT_REGISTER.md` with a component-boundary benefit entry.

### 6. Verification
- Compare only against `governance/vjripl-publication-confidentiality`.
- Confirm no runtime/source/dependency/workflow/binary files changed.
- Open a draft stacked PR linked to Issue #17.
- Keep Issue #17 open because legal title/licence execution and any physical code extraction remain separately authority-gated.
