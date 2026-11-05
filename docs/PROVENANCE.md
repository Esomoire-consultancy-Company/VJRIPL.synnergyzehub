# MAT-VJRIPL-001 Provenance and Cross-Matter Import Contract

## Principle

No material enters or leaves this Matter implicitly.

Similarity of code, shared actors, shared architecture, common vendors or common terminology is not sufficient provenance. Reuse must be attributable to an identified source and an identified rights/authority basis.

## Required import record

Every deliberate cross-Matter import should record:

```yaml
import_id: XMI-MAT-VJRIPL-001-0001
source_matter_id: MAT-...
source_object_or_commit: <commit, tag, release, file, package or record>
imported_object: <precise artifact/interface/schema>
rights_basis: <contract, licence, permission, public licence, internal background-IP rule>
purpose: <why this Matter needs the object>
receiving_matter_id: MAT-VJRIPL-001
approving_authority: <decision/authority reference>
effective_date: YYYY-MM-DD
ip_classes:
  - SYNNERGYZE_BACKGROUND
contains_client_data: false
evidence_refs:
  - <source/destination commit or receipt>
```

Where no cross-Matter import exists, Issues and PRs should state `none` explicitly.

## Export record

Exports from this Matter use the same structure with `MAT-VJRIPL-001` as `source_matter_id` and the receiving Matter identified explicitly.

An export must not silently include `VOI_DATA_KNOWLEDGE`. If client-specific material is required, the record must state the applicable rights basis and approving authority.

## Provenance classes

- `ORIGINAL_THIS_MATTER` — originated in this Matter.
- `CROSS_MATTER_IMPORT` — deliberately admitted from another governed Matter.
- `SYNNERGYZE_BACKGROUND_ADMISSION` — reusable platform/background object deliberately admitted for use here.
- `THIRD_PARTY` — governed by third-party rights/terms.
- `PUBLIC_SOURCE_REFERENCE` — public information referenced as evidence/research, not claimed as original IP.
- `LEGACY_UNKNOWN` — existing material for which the source record is insufficient.

## Evidence requirements

A provenance record should point to the narrowest durable evidence available: source commit SHA, package version, release, document revision, contract reference, licence version, or immutable evidence receipt.

A chat, memory, issue comment or verbal instruction can explain intent but should not be the sole durable provenance record when a source artifact exists.

## No silent fork rule

Copy-paste reuse across repositories without a provenance record is prohibited for governed work. If a copy already exists historically, classify it as `LEGACY_UNKNOWN` until reconciled.

## Supersession

Provenance records are additive. A correction does not erase the old record. It must identify:

- the record being corrected or superseded;
- why;
- scope;
- effective date;
- authority;
- evidence supporting the correction.

## Matter-to-platform extraction

When a generalized capability emerges from VOI-specific work, extraction to a reusable Synnergyze/background component should be treated as an explicit export decision, not an automatic consequence of implementation.

The export should separate, wherever practical:

`VOI-specific requirements/configuration/data` from `generalized reusable mechanism`.

This allows VOI to retain attributable Matter benefit while keeping reusable platform technology cleanly bounded.

## Matter-to-matter admission sequence

Canonical flow:

`DISCOVER -> CLASSIFY -> MINIMIZE -> ESTABLISH RIGHTS BASIS -> APPROVE -> IMPORT -> VERIFY -> RECORD BENEFIT`

No imported artifact becomes authoritative merely because it compiles or passes tests. Authority and evidentiary fitness remain separate checks.
