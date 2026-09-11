# MAT-VJRIPL-001 Component IP / Provenance Register

## 1. Purpose

This register implements Issue #17 by classifying the initial VJRIPL / VOI engineering stack at sub-file/component level.

The governing rule is:

> **Separate mechanism from client configuration, data/knowledge and third-party dependency.**

A file may contain more than one class. This register therefore does not assign entire files to one owner bucket merely because the file sits in this repository or contains a client name.

This is an engineering/provenance classification record. It does not determine legal title, assignment, licence scope, confidentiality waiver, employment ownership, insolvency authority or publication permission.

## 2. Classification vocabulary

- `VOI_FOREGROUND` — implementation, configuration, policy application or business logic specifically attributable to MAT-VJRIPL-001.
- `VOI_DATA_KNOWLEDGE` — VOI-specific operational/commercial/product/channel knowledge or evidence content.
- `SYNNERGYZE_BACKGROUND` — reusable/general platform mechanism, protocol, control pattern, registry primitive or tooling.
- `THIRD_PARTY_PROTOTYPE` — external libraries, provider/public-source dependencies, samples/demos or externally licensed material.
- `UNCLASSIFIED_LEGACY` — unresolved historical material; not used for the reviewed components below unless specifically stated.

Authority states used here:

- `ENGINEERING_CLASSIFICATION_ONLY`
- `LEGAL_TITLE_UNRESOLVED`
- `REUSE_REQUIRES_RIGHTS_BASIS`
- `VOI_DATA_EXPORT_RESTRICTED`
- `NO_PRODUCTION_AUTHORITY`
- `SANDBOX_ONLY`
- `DESIGN_ONLY`

## 3. Controlled evidence status

Controlled agreement/IP material has been reviewed outside the public repository. It supports keeping client/data rights, reusable platform rights and confidentiality separately governed, but the available records do not justify treating repository placement as a completed legal assignment or licence.

Private agreement text, signatures, personal data and sensitive source records are intentionally not copied into this public register.

## 4. Component register

| Component ID | Path / object | Functional component | Current engineering classification | VOI-specific boundary / benefit | Reusable background boundary | Data / third-party boundary | Reuse / export rule | Authority / unresolved point | Recommended future technical separation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CMP-EVID-001` | `voi_evidence_adapter.py` | Generic CSV parsing, datatype/timestamp validation, canonical JSON and SHA-256 integrity mechanics | `SYNNERGYZE_BACKGROUND` + `VOI_FOREGROUND` mixed | VOI contract shape, source names, field requirements, demand window semantics, VOI evidence refs and inventory snapshot schema are Matter-specific | CSV normalization, finite/non-negative validation, canonical serialization, source hashing and digest construction are reusable evidence primitives | Runtime source rows become `VOI_DATA_KNOWLEDGE`; Python stdlib dependencies are external/runtime platform dependencies | Reuse only after extracting generic evidence functions from VOI field/schema constants; no source rows or VOI mappings exported | `ENGINEERING_CLASSIFICATION_ONLY`; `LEGAL_TITLE_UNRESOLVED`; `NO_PRODUCTION_AUTHORITY` | Extract generic `evidence_core` primitives; keep `voi_inventory_contract` profile/config separate |
| `CMP-EVID-002` | `VOI-INVENTORY-EVIDENCE-001` return structure in `voi_evidence_adapter.py` | VOI inventory evidence contract | `VOI_FOREGROUND` + `VOI_DATA_KNOWLEDGE` | Contract ID, snapshot fields, demand-window semantics, source/evidence naming and current business meaning are specific to VOI | Digest/canonical-payload convention may be generalized separately | Payload instances contain VOI operational evidence | Do not copy payload/schema into another client Matter without explicit rights basis; generalized integrity envelope may be separately extracted | `VOI_DATA_EXPORT_RESTRICTED`; `LEGAL_TITLE_UNRESOLVED` | Define generic evidence-envelope schema plus VOI profile schema |
| `CMP-EVID-003` | `registry/voi-logic-evidence-profile.json` | LOGIC ERP / OMS read-only evidence profile | `VOI_FOREGROUND` + `VOI_DATA_KNOWLEDGE` | LOGIC system role, export names, required columns, expected grain, provider-live transition requirements and Warden boundary are VJRIPL/VOI-specific mappings | Profile/adapter admission pattern is reusable | Provider names, operational source semantics and future credential/service-principal requirements are client/provider context | Export blocked by default as client/provider configuration; reuse only by creating a new client profile | `VOI_DATA_EXPORT_RESTRICTED`; `NO_PRODUCTION_AUTHORITY`; provider contract still required for live mode | Keep profiles in client-specific registry; expose generic profile schema from platform layer |
| `CMP-EVID-004` | `inventory_evidence_bridge.py` | Streamlit evidence upload/review/export surface | `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` + `THIRD_PARTY_PROTOTYPE` | VOI labels, template column sets, LOGIC profile reference, snapshot presentation and Warden evidence wording are Matter-specific | Safe upload-slot handling, temporary-file isolation, read-only presentation and JSON export patterns are reusable UI mechanisms | `streamlit` / `pandas` are third-party dependencies; uploaded operational files are `VOI_DATA_KNOWLEDGE` during use | Generic UI pattern may be reused only after removing VOI schema/labels/data; never export uploaded client files | `ENGINEERING_CLASSIFICATION_ONLY`; `VOI_DATA_EXPORT_RESTRICTED`; `NO_PRODUCTION_AUTHORITY` | Split generic upload/evidence viewer from VOI evidence-form configuration |
| `CMP-EVID-005` | `export_voi_inventory_evidence.py` | CLI evidence exporter | `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` | Command naming, required VOI export types and contract-specific invocation are Matter-specific | Generic file-to-canonical-evidence CLI wrapper pattern is reusable | Input/output files may contain `VOI_DATA_KNOWLEDGE` | Reuse wrapper only after parameterizing contract/profile; no VOI examples/data copied | `ENGINEERING_CLASSIFICATION_ONLY`; `NO_PRODUCTION_AUTHORITY` | Create generic evidence CLI entrypoint driven by profile; keep VOI command/profile separate |
| `CMP-EVID-006` | `tests/test_voi_evidence_adapter.py`, `.github/workflows/voi-evidence-bridge.yml` | Regression and CI gates for evidence contract | `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` + `THIRD_PARTY_PROTOTYPE` | VOI edge cases, expected contract behavior and source-field tests are client/application-specific | CI pattern, compile/test gating and generic integrity-test techniques are reusable | GitHub Actions marketplace actions and Python packages are third-party dependencies | Reuse CI harness generically; do not assume VOI test fixtures/expected business semantics transfer | `ENGINEERING_CLASSIFICATION_ONLY` | Separate generic evidence-contract conformance suite from VOI profile regression tests |
| `CMP-CI-001` | `voi_commercial_intelligence.py` validation/canonicalization helpers | Deterministic validation, canonical JSON and digest helpers | `SYNNERGYZE_BACKGROUND` + `VOI_FOREGROUND` | `MODEL_VERSION`, `EVIDENCE_CONTRACT`, required VOI snapshot fields and domain errors bind the helpers to this Matter | Finite-number validation, canonical JSON, digest generation and deterministic-ID pattern are reusable | Input bundles contain `VOI_DATA_KNOWLEDGE` | Extract helpers without VOI constants/data; do not export source bundle contents | `ENGINEERING_CLASSIFICATION_ONLY`; `LEGAL_TITLE_UNRESOLVED` | Move generic deterministic validation/hash helpers to platform utility module |
| `CMP-CI-002` | `voi_commercial_intelligence.py` signal normalization + `SIGNAL_WEIGHTS` | Demand signal model | `VOI_FOREGROUND` + possible future `SYNNERGYZE_BACKGROUND` framework | Allowed signal vocabulary, weighting values, temporal rule and linkage to VOI inventory evidence are attributable VOI commercial logic | Generic weighted-signal normalization framework could be reusable once weights/types are externalized | Demand signals and regional activity are `VOI_DATA_KNOWLEDGE` | Do not reuse exact weights/rules for another client by default; general engine may be reused with new client policy/config | `ENGINEERING_CLASSIFICATION_ONLY`; `VOI_DATA_EXPORT_RESTRICTED` | Externalize signal taxonomy/weights as VOI policy/config consumed by generic signal engine |
| `CMP-CI-003` | `voi_commercial_intelligence.py` demand matrix / router / replenishment / risk functions | VOI demand, routing, replenishment and assortment decision logic | `VOI_FOREGROUND` + `VOI_DATA_KNOWLEDGE` with reusable algorithmic primitives | shared-stock protections, target-cover application, `RECOMMENDED_ONLY`, broken-size evidence requirement, routing classes and current business rules are client/application-specific | Generic matrix construction, policy evaluation, recommendation object construction and risk-engine pattern are reusable abstractions | Inventory/sales/assortment values and regional signals are `VOI_DATA_KNOWLEDGE` | Exact VOI rules/configuration not transferable by default; reusable engine requires policy/config separation | `VOI_DATA_EXPORT_RESTRICTED`; `NO_PRODUCTION_AUTHORITY` | Introduce generic recommendation engine + VOI policy pack for routing/cover/risk rules |
| `CMP-CI-004` | `build_recommendation_ledger()` / `VOI-COMMERCIAL-INTELLIGENCE-001` | Deterministic recommendation ledger | `SYNNERGYZE_BACKGROUND` + `VOI_FOREGROUND` | VOI contract/model IDs, evidence linkage and recommendation business fields are foreground | deterministic record-ID, canonical ledger and integrity-envelope mechanics are reusable | Ledger instances may encode `VOI_DATA_KNOWLEDGE`; no operational write authority | Generic ledger mechanism reusable after schema/profile separation; client ledger records restricted | `ENGINEERING_CLASSIFICATION_ONLY`; `NO_PRODUCTION_AUTHORITY` | Generic decision-ledger envelope + VOI commercial-intelligence profile |
| `CMP-CI-005` | `commercial_intelligence_bridge.py` | Read-only CI presentation/export surface | `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` + `THIRD_PARTY_PROTOTYPE` | VOI workflow, headings, evidence source linkage and recommendation presentation are foreground application integration | generic advisory-dashboard and JSON-export interaction pattern is reusable | Streamlit/pandas are third-party; uploaded signals/evidence are `VOI_DATA_KNOWLEDGE` | UI shell can be generalized only with VOI data/schema removed | `NO_PRODUCTION_AUTHORITY`; `VOI_DATA_EXPORT_RESTRICTED` | Separate generic advisory viewer from VOI CI presentation/configuration |
| `CMP-EST-001` | `estate_contract.py` | Possibility → qualification → proposition → deal → reality domain model | `SYNNERGYZE_BACKGROUND` applied to `VOI_FOREGROUND` Matter | VOI use of the lifecycle, qualification policy and client benefit are Matter-specific | state model, six-gate interface, capability gating, evidence-before-deal/reality pattern are reusable Estate primitives | Current object instances may contain client commercial knowledge | Reuse domain primitives only; client object instances/configuration remain in Matter | `ENGINEERING_CLASSIFICATION_ONLY`; `LEGAL_TITLE_UNRESOLVED` | Keep generic Estate domain package separate from client policy/seeds |
| `CMP-EST-002` | `seed_voi_capabilities()` in `estate_registry.py` | VOI capability ledger seed | `VOI_FOREGROUND` + `VOI_DATA_KNOWLEDGE` | capability IDs and mappings for product design, manufacturing, washing, warehouse, LOGIC, Easycom, Myntra, Flipkart, Centro, content, returns and replenishment describe VOI operating context | capability-record data model is reusable background | Provider/channel/system names and client capability mapping are client knowledge | No silent cross-client export; create new capability seed per Matter | `VOI_DATA_EXPORT_RESTRICTED` | Move seed to VOI-specific configuration module/data file; leave registry generic |
| `CMP-EST-003` | `_CHANNEL_TEMPLATES`, intake source choices and `client_id="VOI-CLIENT-001"` in `estate_board.py` | VOI channel propositions and Estate intake configuration | `VOI_FOREGROUND` + `VOI_DATA_KNOWLEDGE` | Myntra/Flipkart/Centro objectives, success criteria, capability requirements and client ID are specifically VJRIPL/VOI | generic template renderer/intake form/board-summary mechanism is reusable | channel strategy and commercial mapping are client knowledge | Keep configuration in VOI Matter; generic board may consume a client policy pack | `VOI_DATA_EXPORT_RESTRICTED`; `NO_PRODUCTION_AUTHORITY` | Extract `voi_estate_config` from reusable Estate Board UI |
| `CMP-EST-004` | `EstateRegistry`, SQLite schemas, guardrail/reservation primitives in `estate_registry.py` R0.2 | Local persistence, guardrails and advisory reservation registry | `SYNNERGYZE_BACKGROUND` with Matter-specific use | field population, records, guardrail thresholds and capability values are VOI-specific when instantiated | SQLite registry pattern, generic guardrail evaluation, expiry and conflict detection are reusable | persisted client records may contain `VOI_DATA_KNOWLEDGE` | Reusable registry code may transfer only without VOI records/configuration | `ENGINEERING_CLASSIFICATION_ONLY`; `NO_PRODUCTION_AUTHORITY` | Package generic Estate registry; inject client schemas/seeds/policies at boundary |
| `CMP-EST-005` | R0.3 additions in `estate_registry.py` | Evidence-bound proposition/deal/execution-intent governance | `SYNNERGYZE_BACKGROUND` + `VOI_FOREGROUND` | hard binding to `VOI-INVENTORY-EVIDENCE-001` and current Estate application is VOI-specific | generic evidence registration, Warden/River reference requirements, no-external-effect intent, persistence and idempotency are reusable control primitives | referenced evidence/deal content may contain client data/knowledge | Generalize contract admission through profile/interface; never transfer VOI records | `NO_PRODUCTION_AUTHORITY`; stored Warden/River refs are not live validation | Extract generic governance-chain registry and inject allowed evidence contracts/client policy |
| `CMP-EST-006` | R0.3 `estate_board.py` governance-chain view | Read-only inspection of propositions, deals and execution intents | `VOI_FOREGROUND` + `SYNNERGYZE_BACKGROUND` | labels, VOI Estate placement and current client records are foreground | generic governance-chain viewer pattern reusable | displayed records may contain `VOI_DATA_KNOWLEDGE`; Streamlit/pandas third-party | Reuse shell only with new Matter projection/data source | `NO_PRODUCTION_AUTHORITY` | Generalize read-only governance-chain component with tenant/Matter adapter |
| `CMP-EST-007` | PR #10 R0.4 controlled-effects design | Actor/Warden/River/provider/idempotency/observation/reconciliation control-loop design | primarily `SYNNERGYZE_BACKGROUND` with `VOI_FOREGROUND` application constraints | VOI Estate lineage, named excluded operational systems, first application of sandbox effect chain and production-promotion gates are Matter-specific | DigitalMe actor contract, Warden validation interface, River gateway, provider admission, state digest, effect lifecycle, idempotency, unknown-effect and reconciliation design are reusable platform/control primitives | future real provider integrations will introduce third-party/provider terms and potentially client data | No implementation or production reuse claim beyond design; any extraction/promotion separately governed | `DESIGN_ONLY`; `SANDBOX_ONLY`; `LEGAL_TITLE_UNRESOLVED`; `NO_PRODUCTION_AUTHORITY` | Implement reusable effect-runtime package separately, then bind VOI-specific providers/policies only through explicit adapters |
| `CMP-APP-001` | `app.py` | Mixed legacy portal shell + governed VOI route integration | `THIRD_PARTY_PROTOTYPE` + bounded `VOI_FOREGROUND` | VOI Inventory Evidence and later governed feature routes/integration are attributable Matter additions | generic navigation/routing patterns may be reusable but remain entangled with legacy prototype shell | legacy content remains governed by `LEGACY_PROVENANCE_REGISTER.md`; Streamlit is third-party | Do not treat whole file as foreground; future separation should move governed VOI surface into dedicated app/router | `ENGINEERING_CLASSIFICATION_ONLY`; legacy provenance rules remain controlling | Create dedicated governed VOI application entrypoint; leave/archive legacy prototype shell separately |
| `CMP-GOV-001` | `MATTER.yaml`, Matter/IP/provenance/publication templates/doctrine | Matter governance mechanism applied to VJRIPL | `SYNNERGYZE_BACKGROUND` + `VOI_FOREGROUND` manifest/configuration | MAT-VJRIPL-001 IDs, beneficiary, operational truth boundaries, issue rules, benefit entries and publication posture are Matter-specific | Matter semantics, provenance fields, authority/evidence separation and publication-control patterns are reusable governance background | private supporting evidence is not part of public repo; third-party GitHub platform governs hosting | Reuse governance schema/pattern only; create new Matter manifest/register for each client | `ENGINEERING_CLASSIFICATION_ONLY`; legal effect depends on governing instruments | Maintain reusable Matter schema/templates separately from client manifests/registers |

## 5. Key engineering conclusions

### 5.1 Evidence layer

The strongest separation is **evidence engine vs VOI evidence profile**:

```text
Reusable evidence mechanics
  canonicalize / validate / hash / fingerprint / seal
                    +
VOI profile and configuration
  LOGIC/OMS exports / field dictionary / contract IDs / client semantics
                    +
VOI evidence instances
  inventory / sales / product master / open orders / derived snapshots
```

The first layer is a candidate `SYNNERGYZE_BACKGROUND` mechanism. The second is `VOI_FOREGROUND`; the third is `VOI_DATA_KNOWLEDGE`.

### 5.2 Commercial Intelligence

The preferred separation is **deterministic recommendation engine vs VOI commercial policy pack**:

```text
Reusable mechanism
  deterministic transforms / canonical IDs / policy execution / ledger envelope
                    +
VOI policy/configuration
  signal taxonomy + weights / cover targets / routing rules / risk rules / model-contract identity
                    +
VOI evidence and signals
```

No other Matter should inherit VOI signal weights, channel assumptions or shared-stock decisions merely because the algorithm is reusable.

### 5.3 Estate

The preferred separation is **Estate domain/control substrate vs VJRIPL Estate configuration**:

```text
Reusable Estate substrate
  possibility lifecycle / registry / guardrails / idempotency / Warden+River interfaces / effect-runtime design
                    +
VJRIPL / VOI configuration
  client ID / capability seed / channel templates / evidence-contract admission / policy thresholds
                    +
VJRIPL / VOI records
  possibilities / commercial cases / evidence refs / deals / intents / outcomes
```

### 5.4 R0.4 status

PR #10 is currently a controlled-effects **design**, not an implemented production runtime. Classification of the reusable control loop therefore does not imply working code, provider credentials, live Warden/River integration or any external-effect authority.

## 6. Third-party dependency rule

Third-party packages/services remain governed by their own licences/terms. Use of Streamlit, pandas, Plotly, GitHub Actions or other external packages does not convert those dependencies into VOI or Synnergyze-owned IP.

Where externally supplied provider data or interfaces are introduced later, provider terms and data rights must be recorded separately.

## 7. VOI data/knowledge rule

`VOI_DATA_KNOWLEDGE` includes, where present or instantiated:

- inventory and stock observations;
- sales and demand history;
- product master and commercial parameters;
- open orders/inbound data;
- channel demand signals;
- channel objectives and capability mappings;
- VOI capability/warehouse/factory/system mappings;
- commercial cases, opportunities, guardrails, propositions, deals and outcome evidence;
- derived client-specific evidence and recommendation records.

The existence of generalized code around this information does not authorize its export. Client data/knowledge should be removed or substituted with synthetic data before any generalized component is extracted or published.

## 8. Reuse / extraction protocol

A future extraction of candidate `SYNNERGYZE_BACKGROUND` from this Matter should use this sequence:

`IDENTIFY SUBCOMPONENT -> REMOVE VOI DATA -> PARAMETERIZE CLIENT POLICY -> VERIFY THIRD-PARTY TERMS -> ESTABLISH RIGHTS BASIS -> CROSS-MATTER EXPORT RECORD -> REVIEW -> EXTRACT`

The receiving component must not carry:

- VOI source records;
- client IDs;
- LOGIC/Easycom/channel-specific credentials or private configuration;
- VOI commercial weights/rules unless explicitly licensed/admitted;
- private contractual evidence;
- unresolved legacy assets.

## 9. Legal / contractual status

This register deliberately stops at engineering/provenance classification.

Before any assignment, licence, open-source publication, repository transfer or commercial reuse, establish the applicable authority using executed agreements, employment/consultancy records, board/RP or other competent approvals where relevant, and applicable law.

If legal evidence conflicts with this engineering classification, the legal/authority record controls and this register must be amended additively with an explicit supersession record.

## 10. Proposed next technical refactors — not authorized here

The classification suggests the following future refactors, each requiring its own Matter Issue / reviewed disposition:

1. generic evidence-core package + VOI evidence profile;
2. generic deterministic recommendation/ledger engine + VOI CI policy pack;
3. generic Estate domain/registry package + `voi_estate_config`;
4. reusable controlled-effect runtime implementation + VOI-specific provider/policy adapters;
5. dedicated governed VOI application entrypoint separated from the legacy portal shell;
6. reusable Matter-governance schema/templates separated from MAT-VJRIPL-001 manifests/registers.

No refactor, code movement or licence is authorized by this register itself.
