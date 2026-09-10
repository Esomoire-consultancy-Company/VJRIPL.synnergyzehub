# VJRIPL Matter Envelope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a repository-level Matter envelope for `VJRIPL.synnergyzehub` that preserves VOI/VJRIPL benefit while preventing implicit cross-matter, background-IP, prototype, or evidentiary contamination.

**Architecture:** Treat the repository as the durable Matter boundary and GitHub Issues/PRs/commits/releases as issue, disposition, record, and published-state objects. Add declarative matter identity, IP classification, provenance/import rules, benefit accounting, and contributor templates without changing runtime behavior or the existing Estate R0.1-R0.4 branch lineage.

**Tech Stack:** GitHub repository metadata, YAML, Markdown, GitHub issue forms/templates, pull-request template.

**Spec:** `docs/MATTER-DOCTRINE.md`

## Global Constraints

- Do not modify application/runtime code in this slice.
- Do not merge or retarget the existing Estate R0.1-R0.4 PR stack.
- Do not claim that repository location alone determines legal IP ownership.
- Do not treat prototype/demo/research material as VOI foreground IP without provenance classification.
- Cross-matter reuse must be explicit, source-bound, rights-basis-bound, and reviewable.
- Matter changes are additive unless an explicit supersession record says otherwise.

---

### Task 1: Canonical Matter Identity

**Files:**
- Create: `MATTER.yaml`
- Create: `docs/MATTER-DOCTRINE.md`

**Interfaces:**
- Consumes: repository identity and existing VOI Estate doctrine.
- Produces: canonical `matter_id`, beneficiary, scope, authority and lifecycle semantics used by later templates and ledgers.

- [ ] **Step 1:** Add `MATTER.yaml` with stable Matter identity, beneficiary, repository, status, scope, system boundaries, IP classes and cross-matter import policy.
- [ ] **Step 2:** Add `docs/MATTER-DOCTRINE.md` defining Repository= Matter, Issue = Matter Issue, PR = Proposed Disposition, Merge = Accepted Disposition, Release = Published Matter State.
- [ ] **Step 3:** Verify both files are valid text/YAML and contain no runtime configuration changes.
- [ ] **Step 4:** Commit as `docs: establish VJRIPL matter identity`.

### Task 2: IP and Provenance Boundary

**Files:**
- Create: `docs/IP_BOUNDARY.md`
- Create: `docs/PROVENANCE.md`

**Interfaces:**
- Consumes: `MATTER.yaml` IP classes.
- Produces: classification and cross-matter import rules applicable to every new issue/PR.

- [ ] **Step 1:** Define four canonical classes: `VOI_FOREGROUND`, `VOI_DATA_KNOWLEDGE`, `SYNNERGYZE_BACKGROUND`, `THIRD_PARTY_PROTOTYPE`.
- [ ] **Step 2:** Define explicit cross-matter import fields: source matter, source commit/object, imported object, rights basis, purpose, receiving matter, approving authority, effective date.
- [ ] **Step 3:** Classify legacy Buying House/ECG/mock merchandiser material as `UNCLASSIFIED_LEGACY` pending review rather than rewriting history.
- [ ] **Step 4:** Commit as `docs: define VJRIPL IP and provenance boundaries`.

### Task 3: Benefit Register

**Files:**
- Create: `docs/BENEFIT_REGISTER.md`

**Interfaces:**
- Consumes: Matter identity and IP classification.
- Produces: auditable mapping of VJRIPL-specific benefit to source artifacts without assigning unrelated platform technology.

- [ ] **Step 1:** Seed benefit entries for Inventory Evidence, Estate R0.1-R0.4, product/catalog/order prototypes, and commercial-intelligence work.
- [ ] **Step 2:** For each entry record status, Matter benefit, source artifact/PR, IP class, dependency, and production-authority state.
- [ ] **Step 3:** State that benefit attribution does not itself determine legal title, licence scope, confidentiality, or production authority.
- [ ] **Step 4:** Commit as `docs: add VJRIPL benefit register`.

### Task 4: Matter-Native GitHub Workflow

**Files:**
- Create: `.github/ISSUE_TEMPLATE/matter-issue.yml`
- Create: `.github/pull_request_template.md`

**Interfaces:**
- Consumes: `matter_id`, IP classes, provenance contract.
- Produces: required contributor metadata for future Matter Issues and Proposed Dispositions.

- [ ] **Step 1:** Add Issue fields for matter ID, issue class, beneficiary, problem/decision, evidence, IP class, cross-matter dependency, authority and acceptance criteria.
- [ ] **Step 2:** Add PR fields for Matter Issue linkage, disposition, affected IP classes, provenance/imports, evidence/tests, authority boundary, supersession and client benefit.
- [ ] **Step 3:** Require explicit `none` where no cross-matter import or supersession exists.
- [ ] **Step 4:** Commit as `chore: add matter-native GitHub templates`.

### Task 5: Review Gate

**Files:**
- Review only: all files above.

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: review-ready governance branch with no runtime delta.

- [ ] **Step 1:** Confirm no `.py`, dependency lock, runtime config, database, or Estate branch files changed.
- [ ] **Step 2:** Confirm all documents use the same `matter_id` and IP class names.
- [ ] **Step 3:** Confirm the envelope explicitly preserves R0.1-R0.4 lineage and does not assert legal ownership from repository placement.
- [ ] **Step 4:** Open a draft PR to `main` titled `Govern VJRIPL.synnergyzehub as Matter MAT-VJRIPL-001`.
