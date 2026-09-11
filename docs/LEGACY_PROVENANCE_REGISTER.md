# MAT-VJRIPL-001 Legacy Provenance Register

## Purpose

This register is the component-level disposition for Matter Issue #13. It classifies legacy prototype, research, configuration and attached-asset material so useful historical work can remain available to VJRIPL / VOI without silently becoming production truth, client data, reusable Synnergyze background IP, or a legal ownership determination.

This is an engineering/provenance classification. Legal title, assignment, licence scope, confidentiality and third-party terms remain governed by applicable agreements and law.

## Classification method

The review uses the Matter IP classes from `docs/IP_BOUNDARY.md` and the following provenance states:

- `ORIGINAL_THIS_MATTER` — repository history shows the artifact was created or materially developed in this Matter, without determining legal title.
- `PUBLIC_SOURCE_REFERENCE` — content or data depends materially on public/external sources.
- `THIRD_PARTY` — third-party software, service, library, content or terms materially apply.
- `VOI_MATTER_ADMISSION` — a later, specifically VOI-bound capability was admitted into a legacy shell.
- `LEGACY_UNKNOWN` — available repository evidence is insufficient to make a reliable provenance claim.

An artifact may have more than one IP/provenance class.

## Component register

| Component | Current classification | Provenance | Evidence / reason | Handling rule |
| --- | --- | --- | --- | --- |
| `app.py` — generic Buying House shell/navigation | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Legacy Streamlit shell identifies itself as “Buying House Portal”; historical buying-house work was introduced in commit `a6a036403b98d5dfa7235964bd88f8d66bfd8fb8`. | Retain as historical interaction prototype. Do not treat generic shell copy/state as production VOI truth. |
| `app.py` — Inventory Evidence Bridge route/caption | `VOI_FOREGROUND` candidate, with reusable mechanics potentially `SYNNERGYZE_BACKGROUND` | `VOI_MATTER_ADMISSION` | Current `app.py` imports and exposes `inventory_evidence_bridge`; the governed VOI evidence work was merged through commit `0091c9f643a57cf422cc103229f2feda6cb2c2fb`. | Keep this bounded from the legacy portal classification. VOI evidence remains read-only and separately governed. |
| `onboarding.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER`; `THIRD_PARTY` for referenced Feather icons | Generic Buying House onboarding, generic bulk-order claims and externally hosted icon references. | Prototype UX only. Any production copy, promises or process steps require VOI-specific validation. |
| `product_catalog.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER`; `THIRD_PARTY` for referenced Feather icons | File explicitly labels product records as “Mock product data for demonstration”; contains sample prices, MOQs, trends and product attributes rather than admitted VOI master data. | Useful interaction/product-model prototype; never treat sample SKUs, prices, MOQs or trend values as VOI data/evidence. |
| `product_detail.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Operates on the catalogue’s mock product records and presents generic customization, sizing and timeline assumptions. | Prototype configuration/order UX. Production commercial terms require separately admitted VOI evidence and authority. |
| `order_booking.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Generic company/order form, fixed production-time assumptions, generic Incoterms/payment options and `BH-*` inquiry ID. No production backend or VOI execution authority is established. | Treat as inquiry-flow prototype only; do not interpret selected payment/incoterm values as accepted VOI commercial terms. |
| `order_confirmation.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Generates an estimated timeline from current date and presents `orders@buyinghouse.com` / `+1-800-555-0123`; these are prototype contact values, not admitted operational identities. | Demonstrator only. No generated timeline/contact/order status is production evidence. |
| `merchandiser_agent.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Commit `5438c5ff05351d7943fc5cfd7b812526dd2b0ba2` introduced the merchandiser feature. The implementation assigns sample personas, `@buyinghouse.com` contacts, canned responses and random expertise/order metrics. | Preserve interaction concepts; never present personas, contact details, schedules, scores or response metrics as real VOI staff/evidence. |
| `retailer_analysis.py` | `THIRD_PARTY_PROTOTYPE` + external research dependency | `ORIGINAL_THIS_MATTER` + `PUBLIC_SOURCE_REFERENCE` + `THIRD_PARTY` | Legacy commits `b30d1fe4d6cb262b1205970dc40b6f73d9226bcc` and `98577d0c4ea03811b2be831f0a045e4473c893ca` branded the surface “ECG Market Health Check”; code uses `yfinance` and public-company/market information. Branding alone does not convert external market data into client-owned data. | Research/advisory prototype. Validate source freshness, provider terms and factual claims before reuse. Do not treat “proprietary” presentation wording as proof of ownership over source market data. |
| `stock_analysis.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` + `PUBLIC_SOURCE_REFERENCE` + `THIRD_PARTY` | Generic equity analysis using `yfinance`; examples include Apple, Microsoft, Amazon, Google, Tesla, Netflix and Meta. | External-market research utility only; subject to source/provider terms and freshness. |
| `visualization.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Visualization helper associated with the legacy stock/retailer analysis surfaces. | Reusable only after dependency/licence review; no market observation generated by it is itself VOI evidence. |
| `production_dashboard.py` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` | Commit `d7ed154a0db2168d3b8417901c54a2a8c9313f49` created the module. It explicitly simulates production by generating `random.randint(1, 100)` data points and local notification/status values. | Simulation only. Never treat generated production values, delivery status or notifications as factory/warehouse truth. |
| `attached_assets/Buying_House_Task_Master.csv` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Contains generic Buying House operations tasks (order verification, costing, vendor POs, production monitoring, dispatch, payment tracking and compliance). Available history reviewed here does not establish whether these are VOI-approved procedures. | Retain; do not promote to VOI SOP/authority until source, owner and approval basis are evidenced. |
| `attached_assets/CA_Governance_Task_Master.csv` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Contains generic CA/governance, fee, reconciliation, compliance and audit tasks. No reliable admission record was identified in this review. | Retain as legacy planning material only; not an authoritative finance/compliance procedure. |
| `attached_assets/Marketplace_Task_Master.csv` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Contains generic marketplace onboarding, listing, sales, returns, commission, compliance and reporting tasks. | Retain as legacy planning material only; not admitted marketplace policy or VOI operating truth. |
| `attached_assets/IMG_*.jpeg` image set listed below | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Repository contains image binaries without a sufficient source/rights description in the current Matter record. Binary content/metadata was not used to infer ownership. | Do not export, publish, relabel or reuse across Matters until subject/source/rights are reviewed. Retention in history is unaffected. |
| `attached_assets/buying house website.docx` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Legacy binary document; content/rights basis was not established from the text-based repository evidence available in this classification pass. | Quarantine for provenance review before reuse or publication. |
| `attached_assets/SynergyHub.zip` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Legacy binary archive; nested content and rights boundaries are not established by repository naming alone. | Do not import into another Matter or treat as canonical source until unpacked and reviewed in a separately evidenced disposition. |
| `attached_assets/SynergyzeGovernance.zip` | `UNCLASSIFIED_LEGACY` | `LEGACY_UNKNOWN` | Legacy binary archive; name alone is insufficient to classify nested governance/platform/client material. | Do not import into another Matter or generalize as Synnergyze background until separately reviewed. |
| `.replit` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` + `THIRD_PARTY` | Replit-oriented project/runtime configuration associated with the prototype development environment. | Tooling/config only; no client IP or authority inference from platform configuration. |
| `replit.nix` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` + `THIRD_PARTY` | Replit/Nix environment configuration. | Tooling/config only; preserve applicable third-party platform/package terms. |
| `.streamlit/config.toml` | `THIRD_PARTY_PROTOTYPE` | `ORIGINAL_THIS_MATTER` + `THIRD_PARTY` | Presentation/runtime configuration for the Streamlit prototype surface. | Presentation configuration only; not business or operational evidence. |

## Image asset set covered by this register

The following twenty image files are classified together as `UNCLASSIFIED_LEGACY` / `LEGACY_UNKNOWN` pending source-and-rights review:

- `IMG_0359.jpeg`
- `IMG_0360.jpeg`
- `IMG_0361.jpeg`
- `IMG_0362.jpeg`
- `IMG_0363.jpeg`
- `IMG_0364.jpeg`
- `IMG_0372.jpeg`
- `IMG_0376.jpeg`
- `IMG_0377.jpeg`
- `IMG_0378.jpeg`
- `IMG_0379.jpeg`
- `IMG_0380.jpeg`
- `IMG_2FDECC39-6FE4-4097-B876-D40F6DD092A9.jpeg`
- `IMG_56E62987-FECF-4ADA-895E-AE091BB2BC6D.jpeg`
- `IMG_7D40FC57-64EC-4723-9062-C21736BA8F43.jpeg`
- `IMG_7D75CB84-BABF-4D37-AA5F-FA4133A1FFAB.jpeg`
- `IMG_8ADC813E-0040-4F96-8F66-02851516F1FE.jpeg`
- `IMG_8B30CBE8-0299-4ECB-92EA-1CFDDCDA15D3.jpeg`
- `IMG_A55AD1CA-BC37-453C-8451-85862D7BAA81.jpeg`
- `IMG_D8EAC43D-4A06-4924-87E5-D5A55C6C8012.jpeg`

## Explicit non-legacy boundary

The following current Matter capabilities are **not** downgraded by this legacy review:

- `voi_evidence_adapter.py`
- `inventory_evidence_bridge.py`
- `export_voi_inventory_evidence.py`
- `registry/voi-logic-evidence-profile.json`
- `tests/test_voi_evidence_adapter.py`
- `.github/workflows/voi-evidence-bridge.yml`
- the Estate R0.1-R0.4 branch/PR lineage
- VOI Commercial Intelligence R0.1

Those capabilities remain governed by their own evidence, branch, PR, authority and IP-boundary records.

## Reclassification rule

A future reclassification of any `UNCLASSIFIED_LEGACY` item must record at minimum:

1. exact artifact/blob/commit;
2. source and creator/custodian evidence where available;
3. rights or permission basis;
4. whether the artifact contains VOI data/knowledge;
5. intended use and receiving Matter if exported;
6. approving authority;
7. effective date and superseded classification.

Until those fields exist, uncertainty is preserved rather than guessed.
