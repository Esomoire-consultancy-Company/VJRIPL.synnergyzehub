# MAT-VJRIPL-001 Publication and Confidentiality Policy

## 1. Purpose

This policy defines how material in Matter `MAT-VJRIPL-001` may be stored, reviewed, shared, licensed or published.

Its purpose is to preserve the complete attributable benefit of work performed for VJRIPL / VOI while preventing repository visibility, file placement, branch history or a public URL from silently becoming an IP transfer, confidentiality waiver, production authorization, data-sharing permission or cross-Matter licence.

This is a Matter-governance record. It does not replace an executed confidentiality agreement, IP assignment, technology licence, board/resolution-professional authority, data-processing agreement, third-party licence or legal advice.

## 2. Current factual state

At the time Issue #15 was opened, the GitHub repository was publicly visible and GitHub reported no declared repository-wide licence.

The repository also contains a mixture of:

- VJRIPL / VOI-attributable engineering;
- VOI-specific data/evidence contracts and business knowledge;
- reusable Synnergyze/platform concepts and mechanisms;
- third-party/public-source dependencies and prototype material;
- legacy assets whose provenance remains unresolved;
- draft and proposed governance material not yet accepted into `main`.

The historical fact that material has been publicly reachable is recorded as **prior public exposure**. It must not be rewritten as proof that publication was intended, that confidentiality was waived, that rights were transferred, or that reuse was licensed.

Likewise, making a repository private later cannot be treated as proof that earlier public access, clones, caches, downloads, screenshots, forks or other copies ceased to exist.

## 3. Prospective canonical posture

### 3.1 `RESTRICTED_WORKING_MATTER`

The complete working Matter is the canonical internal surface.

It may contain material that is unsuitable for public release, including client-specific configurations, evidence mappings, operational information, unresolved provenance, private commercial context, controlled-effect designs, implementation details, security-relevant information and working legal/governance records.

The default rule for the working Matter is:

> **Not public-qualified unless an explicit publication disposition says otherwise.**

`RESTRICTED_WORKING_MATTER` is a governance classification. A separate authorized repository-setting change is required to make GitHub enforce private visibility.

### 3.2 `PUBLIC_QUALIFIED_PROJECTION`

Public release should normally occur through a bounded projection rather than by exposing the entire working Matter.

A public-qualified projection must be intentionally prepared and should contain only the minimum material necessary for its public purpose, such as:

- public product documentation;
- approved demonstrations using synthetic/sample data;
- redacted architecture explanations;
- public API/interface specifications approved for release;
- open-source components whose rights and licence have been separately cleared;
- public case studies or metrics supported by publication authority and admitted evidence.

A public projection is not automatically the canonical working Matter and must not silently acquire confidential or operational content through merges or copied artifacts.

## 4. Publication states

Every material artifact intended for release should have one of these states:

- `RESTRICTED` — working/internal Matter material; public release not authorized.
- `REVIEW_REQUIRED` — publication may be possible, but provenance, confidentiality, authority, data or licence review is incomplete.
- `PUBLIC_QUALIFIED` — reviewed and approved for the stated public purpose and version.
- `WITHDRAWN_FROM_FUTURE_PUBLICATION` — should no longer be intentionally published going forward; prior exposure remains part of the historical record.

Absence of a publication state means `REVIEW_REQUIRED`, not public permission.

## 5. Class-specific rules

### `VOI_FOREGROUND`

Matter-attributable work may be published only when:

1. the artifact boundary is clear;
2. publication is compatible with the governing agreements and current VJRIPL authority context;
3. no protected VOI data/business knowledge is embedded unintentionally;
4. any reusable background technology is separately identified;
5. the intended licence or no-licence posture is explicit;
6. the release is approved by competent authority.

Matter attribution by itself is not publication authority.

### `VOI_DATA_KNOWLEDGE`

Default state: `RESTRICTED`.

Inventory, sales, product masters, orders, commercial terms, operational mappings, evidence bundles and uniquely identifying business information must not be published merely because code consuming those records is public.

Public release requires a separate data/publication basis and should prefer aggregation, anonymisation, synthetic substitution or redaction where appropriate.

### `SYNNERGYZE_BACKGROUND`

Default state: `REVIEW_REQUIRED`.

Reusable platform technology may be separately published or licensed only by the authority entitled to make that decision. Use inside the VOI Matter does not make the reusable mechanism VOI-owned; conversely, platform ownership does not authorize disclosure of embedded VOI-specific data or configurations.

### `THIRD_PARTY_PROTOTYPE`

Default state: `REVIEW_REQUIRED`.

Publication must respect the applicable upstream licence, provider terms, attribution requirements, data-source restrictions and content rights. Prototype presence in this repository is not permission to relicense third-party material.

Synthetic/mock values must remain clearly non-authoritative.

### `UNCLASSIFIED_LEGACY`

Default state: `RESTRICTED` for future intentional publication.

Unknown or unresolved images, DOCX files, ZIP archives, task-master files or other legacy objects must not be promoted, relicensed, exported to another Matter or intentionally republished until source, rights basis and sensitivity have been reviewed.

This does not erase their prior public exposure where it occurred.

## 6. Repository-wide licence posture

This policy does **not** add a repository-wide software licence.

No one should infer a new licence grant from:

- repository visibility;
- ability to clone or view through GitHub;
- the absence of a `LICENSE` file;
- Matter classification;
- a pull-request merge;
- a demonstration or screenshot;
- use of an open-source dependency inside the repository.

Any future licence decision must identify its exact scope and must not purport to license rights the decision-maker does not control.

Where different components require different licences or restrictions, prefer component-level boundaries over a misleading repository-wide licence.

## 7. Public release gate

Before an artifact becomes `PUBLIC_QUALIFIED`, record at minimum:

- `matter_id`;
- artifact/path/release identifier;
- exact version or commit;
- intended public purpose and audience;
- IP/provenance class;
- source/provenance review status;
- third-party licence/terms check where applicable;
- VOI-data review and redaction outcome;
- security/credential review;
- contractual/confidentiality review;
- approving authority;
- effective date;
- expiry/review date if time-bounded;
- public licence or explicit no-licence notice;
- evidence/reference for the approval.

A previous public version does not automatically qualify a later version.

## 8. Already-public material

Prior public exposure must be handled as a remediation problem, not by pretending it never occurred.

The remediation sequence is:

1. inventory what is currently or historically public;
2. classify each item by Matter/IP/provenance class;
3. identify confidential, client-specific, third-party, security-sensitive or unresolved content;
4. determine competent authority and contractual/legal restrictions;
5. decide whether future publication should continue, be redacted, be replaced by a public projection, or stop;
6. preserve evidence of the decision and exact affected commits/releases;
7. where necessary, assess history-rewrite or takedown options separately, recognizing that such actions do not guarantee removal of prior copies.

No destructive history rewrite is authorized by this policy.

## 9. Unresolved binary and archive assets

The following legacy categories identified by Issue #13 remain blocked from intentional republication until reviewed:

- image binaries under `attached_assets/`;
- legacy DOCX material;
- legacy ZIP archives;
- task-master CSV files with uncertain source/authority status.

They may be retained as Matter evidence/history while their provenance is unresolved.

## 10. Authority model

A repository administrator's technical ability to change GitHub settings is not, by itself, sufficient Matter authority to:

- waive confidentiality;
- assign or license IP;
- publish client data;
- publish third-party content;
- alter VJRIPL legal rights or obligations;
- override insolvency/process authority;
- transfer assets between Matters.

Material publication/licensing decisions require the competent authority applicable to the affected rights and current context.

## 11. No private evidence in public governance records

Public repository governance documents should record the **existence and outcome** of private contractual or authority review where necessary, but should not reproduce confidential agreements, signatures, personal data, privileged analysis, credentials or sensitive internal records merely to prove that review occurred.

Private evidence should be referenced through a controlled evidence register or durable identifier accessible to authorized reviewers.

## 12. Immediate prospective controls

Until Issue #15 is fully disposed and any required settings changes are separately authorized:

1. treat new Matter content as `REVIEW_REQUIRED` for publication;
2. do not add VOI operational exports or credentials to Git;
3. do not add new unresolved binaries/archives to the public branch;
4. do not add a repository-wide licence;
5. do not describe prototype data as operational truth;
6. do not copy private contractual evidence into public PRs/issues;
7. prepare public-facing material as bounded, reviewed projections;
8. record every proposed visibility/licence/publication change as a Matter disposition.

## 13. Issue #15 disposition status

This document proposes the governance policy requested by Issue #15.

It does **not** itself:

- change repository visibility;
- delete historical content;
- add a software licence;
- remove previously exposed copies;
- determine final legal ownership;
- establish that any private contractual draft is executed;
- close Issue #15.

Issue #15 should remain open until the required competent-authority decisions and any approved repository-setting, remediation or licensing actions have been executed and evidenced.
