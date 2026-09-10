# MAT-VJRIPL-001 Matter Doctrine

## Purpose

This repository is governed as a **Matter**, not merely as a software project. The Matter boundary exists to preserve attribution, evidence, client benefit, decision history and issue resolution without silently mixing unrelated work, rights, obligations or authority.

`MAT-VJRIPL-001` is the canonical engineering/governance identifier for the VJRIPL / VOI Synnergyze Hub Matter.

This doctrine is not, by itself, a legal assignment, licence, confidentiality agreement or ownership determination. Legal rights remain governed by applicable law and the relevant executed agreements. The doctrine records how this repository is to be operated and interpreted technically.

## Canonical GitHub semantics

| GitHub object | Matter meaning | Rule |
| --- | --- | --- |
| Repository | Matter | Durable boundary for one governed body of work. |
| Issue | Matter Issue | A question, defect, risk, decision, obligation, claim or work item requiring disposition. |
| Branch | Working Position | A non-authoritative proposed state or investigation path. |
| Commit | Matter Record | Immutable record of a change within a working or accepted position. |
| Pull Request | Proposed Disposition | Proposed resolution or advancement of one or more Matter Issues. |
| Review | Examination | Concurrence, objection, requested change or evidentiary review. |
| Merge | Accepted Disposition | Acceptance into the target branch; not production authority unless separately granted. |
| Tag | Matter Checkpoint | Named state for evidentiary or release reference. |
| Release | Published Matter State | Versioned state intentionally published as a Matter checkpoint. |
| Action artifact | Procedural Evidence | Test, build, validation or other machine-produced evidence. |

## Matter rule

A repository may contain many Issues, but an Issue belongs to one Matter unless an explicit cross-Matter relationship is recorded.

No Issue, commit, PR or file is presumed to carry rights, authority, evidence or obligations from another Matter merely because similar technology, terminology or actors are involved.

## Client-benefit rule

VJRIPL / VOI should receive the attributable benefit of work performed for this Matter. "Benefit" may include client-specific functionality, configurations, models, schemas, workflows, integrations, evidence contracts, analysis, tests, documentation and operational improvements.

Benefit attribution is distinct from legal title. A benefit record must therefore identify the relevant IP/provenance class and any dependency on reusable platform or third-party technology.

## IP/provenance classes

The canonical classifications are:

- `VOI_FOREGROUND` — Matter-specific work attributable to VOI/VJRIPL, subject to governing contracts and applicable law.
- `VOI_DATA_KNOWLEDGE` — VOI/VJRIPL-specific data, records and business knowledge.
- `SYNNERGYZE_BACKGROUND` — reusable platform architecture, protocols, engines, tooling and patterns not uniquely attributable to this Matter.
- `THIRD_PARTY_PROTOTYPE` — third-party, externally licensed, research, sample, mock or demonstrator material.
- `UNCLASSIFIED_LEGACY` — legacy material pending a provenance review; no foreground-IP presumption applies.

A single Proposed Disposition may touch more than one class, but each affected class must be disclosed.

## Cross-Matter isolation

Implicit cross-Matter import is prohibited.

When work is reused from another Matter, the Proposed Disposition must record:

`source_matter_id -> source_object_or_commit -> imported_object -> rights_basis -> purpose -> receiving_matter_id -> approving_authority -> effective_date`

This record exists to prevent accidental contamination of client data, confidential information, legal positions, evidentiary assertions, obligations and IP claims.

Cross-Matter reuse should prefer interfaces, packages, specifications or deliberately exported artifacts over ad hoc copying.

## Existing VOI Estate lineage

The current Estate work is preserved as an existing versioned lineage:

`R0.1 -> R0.2 -> R0.3 -> R0.4`

This Matter envelope does not retarget, flatten, merge or supersede that stack. It adds a repository-level governance boundary around it.

Future supersession must identify the exact record being superseded, the scope of supersession, effective date, approving authority and evidence. Silence is not supersession.

## Authority doctrine

A Matter record is not automatically execution authority.

A merged PR establishes an accepted repository disposition only. Production execution, credential admission, data disclosure, external-system mutation, financial commitment or other material effect requires whatever separate authority the relevant system and policy demand.

Evidence is likewise distinct from authorization. A receipt, test result, provider acknowledgement or evidence reference can support a decision but does not itself grant authority.

## Operational-system preservation

The existing VOI Estate doctrine remains applicable:

- Logic ERP remains transactional enterprise truth.
- Easycom remains OMS/channel execution capability.
- Marketplace systems remain channel truth.
- Warehouse and factory systems remain physical execution truth.

Matter components may consume evidence, model opportunities and coordinate decisions. They must not silently invent operational truth or authority.

## Legacy-material rule

The repository predates this doctrine. Older Buying House, ECG Market Health Check, mock-persona, generated-statistic, research and demonstrator material therefore requires provenance classification before it is relied upon as VOI foreground IP or production evidence.

The initial state for such material is `UNCLASSIFIED_LEGACY`, not deletion and not retrospective rewriting of history.

## Issue lifecycle

A Matter Issue should progress through:

`OPEN -> EVIDENCE_GATHERING -> PROPOSED_DISPOSITION -> REVIEW -> ACCEPTED | REJECTED | WITHDRAWN -> VERIFIED -> CLOSED`

Not every Issue requires code. A Matter Issue may be resolved by evidence, a decision record, a contract interpretation, documentation, configuration, operational action, or a deliberately recorded decision not to act.

## Proposed Disposition minimums

Every material PR should state:

1. the Matter Issue(s) being addressed;
2. the proposed disposition;
3. affected IP/provenance classes;
4. evidence and validation;
5. cross-Matter imports or `none`;
6. authority boundary;
7. supersession or `none`;
8. attributable client benefit.

## Matter-maintenance objective

The objective is not simply to close Issues quickly. It is to maintain a coherent, attributable and reviewable Matter while resolving Issues so that future participants can determine:

- what was known;
- what was proposed;
- what evidence supported it;
- who or what had authority;
- what was accepted;
- what remained unresolved;
- what was superseded;
- what benefit accrued to this Matter; and
- whether anything came from or moved to another Matter.
