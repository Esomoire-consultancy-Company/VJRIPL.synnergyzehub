# VJRIPL Legacy Provenance Classification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve Matter Issue #13 by classifying legacy prototype, research, configuration and attached-asset components without rewriting repository history or making unsupported ownership claims.

**Architecture:** Add a dedicated component-level provenance register stacked on the Matter envelope. Refine the IP and Benefit registers to reference the classification, while leaving all runtime/application files unchanged. Unknown binary/source provenance remains explicitly `UNCLASSIFIED_LEGACY` / `LEGACY_UNKNOWN` until separately evidenced.

**Tech Stack:** GitHub, Markdown, repository history and file-level evidence.

**Spec:** `docs/IP_BOUNDARY.md` and Matter Issue #13.

## Global Constraints

- Base this disposition on `governance/vjripl-matter-envelope`; do not bypass PR #12.
- Do not modify runtime/application code, dependencies, binaries, archives or attached assets.
- Do not infer legal title from repository location, filename, branding, authorship metadata, or a generated-agent commit.
- Treat explicit mock/generated/simulated content as prototype evidence, not production or business truth.
- Treat external market data, icons and libraries according to their external source/terms; do not relabel them as client-owned data.
- Keep binary/image/archive material with unverified provenance as `UNCLASSIFIED_LEGACY` / `LEGACY_UNKNOWN`.
- Preserve VOI-specific evidence and Estate work as separate post-legacy Matter capability; this review must not downgrade or mix those lineages.

---

### Task 1: Component-level provenance register

**Files:**
- Create: `docs/LEGACY_PROVENANCE_REGISTER.md`

**Interfaces:**
- Consumes: repository files/history, Issue #13, canonical IP/provenance classes.
- Produces: one auditable classification row per material legacy component/group with evidence and handling rule.

- [ ] Classify the portal shell, onboarding, product catalogue/detail, order booking/confirmation, merchandiser, retailer/stock analysis, visualization and production simulation.
- [ ] Classify the three task-master CSVs individually.
- [ ] Classify image assets as one bounded group while preserving all filenames in the register.
- [ ] Classify the DOCX and ZIP archives individually as uninspected binary legacy artifacts.
- [ ] Classify prototype environment configuration (`.replit`, `replit.nix`, `.streamlit/config.toml`).
- [ ] Record mixed status for `app.py`: legacy prototype shell plus later VOI evidence-bridge admission.

### Task 2: Refine IP boundary

**Files:**
- Modify: `docs/IP_BOUNDARY.md`

**Interfaces:**
- Consumes: `docs/LEGACY_PROVENANCE_REGISTER.md`.
- Produces: canonical interpretation of resolved Issue #13 classifications.

- [ ] Replace the broad pending-review wording with a reference to the file/component register.
- [ ] Preserve unknown binary/image assets as unresolved rather than guessing.
- [ ] State that prototype usefulness to VOI does not itself convert prototype content into production truth or client data.

### Task 3: Refine Benefit Register

**Files:**
- Modify: `docs/BENEFIT_REGISTER.md`

**Interfaces:**
- Consumes: provenance classifications from Task 1.
- Produces: benefit entries whose provenance no longer says merely `REVIEW_PENDING` for reviewed text/code components.

- [ ] Update BEN-VOI-001 through BEN-VOI-003 with the resolved prototype/public-source classifications and register reference.
- [ ] Keep their authority state non-production.
- [ ] Do not alter BEN-VOI-004 onward except where a cross-reference is needed.

### Task 4: Verification and proposed disposition

**Files:**
- Review only.

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: reviewable stacked PR resolving Issue #13 without runtime delta.

- [ ] Compare `governance/vjripl-matter-envelope...governance/vjripl-legacy-provenance` and confirm only documentation/plan files changed.
- [ ] Confirm every initial Issue #13 component has an explicit classification or explicit unresolved state.
- [ ] Confirm no application code, binary, dependency or asset changed.
- [ ] Open a draft PR targeting `governance/vjripl-matter-envelope`, link Issue #13, and keep it unmerged for review.
