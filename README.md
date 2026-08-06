# PolicyGuard Intelligence Studio

**From policy version change to defensible operational review.**

PolicyGuard is a human-in-the-loop healthcare policy intelligence proof of concept. It curates versioned public policy evidence, detects material changes, translates clear changes into schema-validated review rules, simulates claim impact on synthetic data, and records expert decisions. It never denies, reprices, adjudicates, or makes a clinical decision.

![PolicyGuard interface preview](assets/ui_preview.png)

> **Assessment scope:** public CMS policy sources and deterministic synthetic claims only. No PHI, proprietary claims, payer contracts, or employer data are included.

## Why this version is stronger

| Earlier baseline | PolicyGuard v2 |
|---|---|
| One hard-coded `EXAMPLE1` scenario | Five distinct CMS policy-change patterns |
| Simple line diff | Hybrid sentence matching, word highlighting, and code/date/currency/modifier extraction |
| One claim filter | Four validated rules executed as a portfolio |
| Minimal output table | Executive matrix, time trend, provider concentration, fee distribution, and prioritized reviewer queue |
| Rule output only | Evidence → change → rule → impact → approval → audit workflow |
| Every example becomes a rule | Explicit abstention when claim fields cannot establish clinical purpose |
| API-style demo dependency | Fully functional offline core; no API key required |
| Static toy dataset | 604 deterministic synthetic claims with four named demonstration cases |

## Live demo scenarios

1. **NCCI code retirement:** code `94662` appears in CY 2025 references and is identified by CMS as deleted effective January 1, 2026. The rule routes post-effective-date occurrences to coding-configuration review.
2. **Therapy KX threshold:** the demonstration compares the CY 2025 threshold of `$2,410` with the CY 2026 threshold of `$2,480`, then checks synthetic therapy claims above the current threshold without `KX`.
3. **Telehealth facility fee:** the Q3014 originating-site facility fee changes from `$31.01` to `$31.85`; a tolerance-based rule surfaces possible configuration variance.
4. **New therapy RTM codes:** codes `98979`, `98984`, and `98985` are checked for synthetic policy-mapping status.
5. **Required abstention:** skilled therapy versus general fitness depends on clinical purpose and documentation, so PolicyGuard refuses to generate a claim-level rule.

The public-source metadata, locators, concise paraphrases, and rule proposals are in [`data/policies/policy_catalog.json`](data/policies/policy_catalog.json).

## Product workflow

![PolicyGuard architecture](assets/architecture.svg)

The architecture is intentionally controlled rather than agent-heavy:

- **Evidence:** curated source manifest with version, effective date, and locator
- **Compare:** local semantic and entity-aware change analysis
- **Structure:** Pydantic-validated declarative rules
- **Simulate:** deterministic execution on synthetic claims
- **Review:** approve, reject, or escalate with rationale
- **Audit:** downloadable JSONL decision record with `automatic_claim_action=false`

## Quick start

Python 3.11 or later is recommended.

```bash
git clone https://github.com/Rae9711/cotiviti-policyguard.git
cd cotiviti-policyguard

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/demo_data.py
python scripts/run_evaluation.py
pytest -q
streamlit run app.py
```

The application opens at `http://localhost:8501` by default.

No `.env` file, model key, database, Docker daemon, or external service is required.

## Best five-minute route

Evaluator user guide (in-app coaching + careful language): [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md). Spoken demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

**Thesis:** Policy change → source-grounded evidence → validated rule (or abstain) → synthetic claim review → human approval. No automatic claim action.

1. **Executive overview:** explain the five policy patterns and opportunity matrix.
2. **Policy intelligence:** select the therapy KX threshold and show source-grounded before/after evidence.
3. **Rule studio:** show the validated JSON and dry-run output.
4. **Claim impact:** show review volume, provider concentration, and reviewer queue.
5. **Governance:** switch to the skilled-therapy example, demonstrate abstention, and record an escalation.

In the app: leave **Simple demo mode** on, open **Evaluator / Demo Guide**, and follow tabs 01→05.

## Synthetic run

The committed dataset contains 604 synthetic claim rows. The current deterministic portfolio produces:

| Metric | Result |
|---|---:|
| Claims evaluated | 604 |
| Unique claims routed to review | 55 |
| Review events | 55 |
| Synthetic providers in scope | 33 |
| Synthetic paid amount associated with flagged claims | $5,627.13 |
| Flag rate | 9.1% |

“Paid amount in scope” is not an overpayment, recovery, or savings estimate. It is only a demonstration aggregation over synthetic records.

## Evaluation

Run:

```bash
python scripts/run_evaluation.py
pytest -q
```

Current local checks:

- **8/8** handcrafted rule assertions passed
- **6/6** entity-delta checks passed
- **5/5** change records include source provenance
- **2/2** abstention assertions passed
- **9/9** automated tests passed

These are software and synthetic-fixture checks—not production model accuracy. Full results are written to [`evaluation/results.json`](evaluation/results.json).

## Interface

### 1. Executive overview

A portfolio-level view of materiality, automation readiness, risk, review volume, and synthetic paid-amount exposure.

### 2. Policy intelligence

- highlighted before/after comparison
- semantic similarity
- code, date, currency, modifier, and percentage deltas
- official source cards with locators
- optional local TXT/PDF comparison and downloadable JSON

### 3. Rule studio

- validated condition table
- downloadable declarative rule JSON
- deterministic dry run
- no execution of generated code
- explicit abstention path

### 4. Claim impact

- unique claims and providers in scope
- monthly review trend
- policy-level volume
- provider concentration bubble chart
- Q3014 fee-variance distribution
- prioritized, downloadable reviewer queue

### 5. Governance

- Cotiviti/NIST-inspired control mapping
- reviewer approval, rejection, and escalation
- exportable JSONL audit trail
- transparent synthetic evaluation and limitations

## Repository structure

```text
.
├── app.py                         # Streamlit interface
├── assets/                        # Architecture and interface preview
├── data/
│   ├── policies/policy_catalog.json
│   ├── source_manifest.csv
│   └── synthetic_claims.csv
├── docs/                          # Demo, design, source, migration, and data notes
├── evaluation/results.json        # Transparent local benchmark
├── resume/Haorui_Wang_Resume.pdf
├── scripts/run_evaluation.py
├── src/
│   ├── audit.py
│   ├── catalog.py
│   ├── demo_data.py
│   ├── impact.py
│   ├── models.py
│   ├── rule_engine.py
│   ├── semantic_diff.py
│   └── ui.py
├── tests/
├── report/                        # Final Word report belongs here
├── slides/                        # Final PowerPoint belongs here
└── video/                         # Final MP4 belongs here
```

## Source governance

The repository stores concise paraphrases and metadata, not complete policy manuals. The source pack uses official pages and documents from:

- [CMS Medicare NCCI Policy Manual](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-policy-manual)
- [CMS Medicare Physician Fee Schedule resources](https://www.cms.gov/medicare/payment/fee-schedules/physician)
- [CMS Therapy Services](https://www.cms.gov/medicare/coding-billing/therapy-services)
- [CMS Telehealth Services](https://www.cms.gov/medicare/coverage/telehealth/list-services)
- [Cotiviti Responsible AI](https://www.cotiviti.com/about/responsible-ai-use)
- [NIST AI RMF Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)

See [`docs/SOURCE_METHOD.md`](docs/SOURCE_METHOD.md) and [`data/source_manifest.csv`](data/source_manifest.csv).

## Safety boundaries

PolicyGuard is not a claims-adjudication engine, coding authority, legal interpretation, clinical decision-support system, or production payment-integrity model. It does not establish coverage, medical necessity, overpayment, fraud, abuse, or provider intent.

Every output is a review recommendation. Production use would require licensed content, credentialed experts, security controls, access governance, retrospective validation, monitoring, rollback, and integration testing.

## Assessment deliverables

Before submission, confirm the public repository directly contains:

- final two-page Microsoft Word report plus bibliography page
- final Microsoft PowerPoint
- working POC and source code
- MP4 recording no longer than five minutes, with the presenter on camera
- current resume

The application upgrade does not automatically replace an existing report, slide deck, or video. Use [`docs/MIGRATION_GUIDE.md`](docs/MIGRATION_GUIDE.md) to merge it safely.
