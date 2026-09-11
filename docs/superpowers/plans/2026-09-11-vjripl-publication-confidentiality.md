# VJRIPL Publication and Confidentiality Disposition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the prospective publication, confidentiality and licensing posture for MAT-VJRIPL-001 without changing repository visibility, deleting history, or granting a software licence in this slice.

**Architecture:** Preserve this repository as a Matter record while distinguishing the restricted working Matter from any publication-qualified projection. Record the already-public state as a historical exposure condition rather than pretending later controls can make prior publication confidential, and require explicit authority before any repository-setting, licensing, relocation or redaction action.

**Tech Stack:** GitHub repository governance, YAML, Markdown.

**Spec:** `docs/PUBLICATION_CONFIDENTIALITY_POLICY.md`

## Global Constraints

- Do not change GitHub repository visibility in this slice.
- Do not add an open-source or proprietary software licence in this slice.
- Do not delete or rewrite Git history.
- Do not publish private agreements, client data, credentials or unresolved legacy asset contents.
- Public visibility is not treated as a licence grant or proof of ownership.
- Making a repository private later cannot erase or retract prior public access, clones, forks, caches or copies.
- Material publication actions require competent authority and a reviewed Matter disposition.

---

### Task 1: Publication and confidentiality doctrine

**Files:**
- Create: `docs/PUBLICATION_CONFIDENTIALITY_POLICY.md`

- [ ] Record the current factual repository posture: public, no declared repository licence, working Matter content present.
- [ ] Define `RESTRICTED_WORKING_MATTER` as the prospective canonical posture.
- [ ] Define `PUBLIC_QUALIFIED_PROJECTION` as the only default route for future public release.
- [ ] Define class-specific publication rules for all Matter IP/provenance classes.
- [ ] Define handling for already-public history and unresolved binaries/assets.
- [ ] Define authority gates before changing visibility/licence/publication settings.

### Task 2: Repository-facing notice

**Files:**
- Create: `README.md`

- [ ] Identify the repository as Matter `MAT-VJRIPL-001`.
- [ ] State that the repository currently contains working/prototype/governed Matter material and must not be treated as an authoritative production system.
- [ ] State that no repository-wide software licence is declared by this disposition.
- [ ] Point to the Matter, IP, provenance and publication doctrine.
- [ ] Avoid publishing private source evidence or contract text.

### Task 3: Bind policy into the Matter manifest

**Files:**
- Modify: `MATTER.yaml`

- [ ] Add `publication_policy` with current posture, target working posture, public-projection rule, licence state and authority requirement.
- [ ] Record prior public exposure as a condition requiring remediation, not as authorization.

### Task 4: Record client benefit

**Files:**
- Modify: `docs/BENEFIT_REGISTER.md`

- [ ] Add a benefit entry for publication/confidentiality governance.
- [ ] State that the benefit is risk reduction and Matter isolation, not an ownership or licence determination.

### Task 5: Verification and proposed disposition

- [ ] Compare against `governance/vjripl-legacy-provenance`.
- [ ] Confirm only governance/notice files changed.
- [ ] Open a draft PR stacked on PR #14 and link Issue #15.
- [ ] Keep Issue #15 open because repository-setting/licensing action remains separately gated.
