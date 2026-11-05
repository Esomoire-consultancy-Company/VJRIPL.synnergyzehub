# MAT-VJRIPL-001 IP Boundary

## Purpose

This document classifies repository material for Matter governance. It is designed to preserve VJRIPL / VOI's attributable benefit while preventing accidental claims over unrelated platform, third-party, prototype or cross-Matter material.

This is an engineering and provenance classification document, not a substitute for executed IP assignment, licence, employment, consultancy, confidentiality or other legal agreements.

## Canonical classes

### `VOI_FOREGROUND`

Use for work specifically created, configured or materially adapted for the VJRIPL / VOI Matter.

Typical examples include:

- VOI-specific commercial workflows and decision logic;
- VOI-specific channel, SKU, warehouse, product or capability mappings;
- VOI-specific evidence schemas and validation profiles;
- client-specific dashboards, reports and tests;
- VOI-specific Estate records, policies and configurations;
- implementations whose material value depends on VOI-specific requirements or knowledge.

Classification means the artifact is attributable to this Matter. Legal title and licence scope still depend on the governing agreements and applicable law.

### `VOI_DATA_KNOWLEDGE`

Use for data or business knowledge supplied by, generated from, or uniquely describing VJRIPL / VOI operations.

Examples include inventory, product masters, orders, sales, commercial terms, operational mappings, process observations and VOI-specific derived evidence.

Do not move this class to another Matter without an explicit rights and authority basis.

### `SYNNERGYZE_BACKGROUND`

Use for reusable platform technology that is not uniquely attributable to VJRIPL / VOI.

Examples can include generalized orchestration patterns, Matter-management primitives, DigitalMe actor contracts, Warden authorization interfaces, River evidence patterns, generic idempotency/reconciliation machinery, reusable schemas and tooling.

A VOI implementation may depend on this class and still deliver substantial `VOI_FOREGROUND` benefit. Dependency does not collapse the two classes into one.

### `THIRD_PARTY_PROTOTYPE`

Use for third-party, externally licensed, public-source, research, mock, sample, demonstrator or evaluation material.

Examples include third-party libraries, public financial-market data integrations, sample personas, mock contact details, generic demonstrations and externally sourced datasets or content.

The applicable third-party licence, terms or permission remain controlling.

### `UNCLASSIFIED_LEGACY`

Use for pre-doctrine repository material whose provenance or intended IP status has not yet been reviewed.

This class is deliberately neutral. It does not mean the material is unowned, public domain, disposable or third-party. It means this Matter has not yet made a reliable classification.

## Initial legacy classification

Pending file-by-file review, the following categories should be treated as `UNCLASSIFIED_LEGACY` rather than presumed `VOI_FOREGROUND`:

- the generic Buying House Portal presentation layer;
- ECG Market Health Check / retailer-analysis material;
- JC Penney and comparable public-market analysis;
- fictional or generated merchandiser personas and contact details;
- randomized expertise, satisfaction and production-monitoring values;
- generic sample ordering, pricing, MOQ and payment-response content;
- prototype assets whose source or rights basis is not evident from the repository record.

This classification preserves history and prevents unsupported attribution. It does not require deletion.

## Existing VOI-specific candidates

The following are strong candidates for `VOI_FOREGROUND` or mixed `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` classification, subject to the governing legal agreements:

- `VOI-INVENTORY-EVIDENCE-001` implementation and VOI evidence profile;
- VOI-specific inventory/source validation and evidence export flows;
- Estate VOI R0.1-R0.4 client-specific records, capability seeds, channel templates and governed transitions;
- VOI Commercial Intelligence client-specific recommendation logic, presentation and evidence binding;
- VOI-specific product, channel and operational mappings.

Where a generalized mechanism is reusable beyond VOI, classify the generalized mechanism separately from the VOI configuration or implementation.

## Mixed-artifact rule

A file or PR may contain more than one class. When practical, separate classes into distinct modules, data files or commits. When separation is not practical, record all affected classes in the PR and identify the boundary explicitly.

## No contamination by naming

Neither a repository name, directory name, branch name, package name nor client identifier alone determines IP ownership or rights.

Likewise, use of generalized Synnergyze, Genesis, Warden, DigitalMe, RiverOS or SILK terminology inside this Matter does not by itself transfer unrelated platform rights into the Matter.

## Cross-Matter export rule

Before exporting or reusing Matter material elsewhere, determine:

1. the artifact's IP/provenance class;
2. whether it contains `VOI_DATA_KNOWLEDGE`;
3. the rights basis for reuse;
4. the receiving Matter;
5. the minimum necessary exported object;
6. the approving authority;
7. the evidence/commit establishing what was exported.

Prefer reusable interfaces or generalized background components rather than copying VOI-specific data or client logic into another Matter.
