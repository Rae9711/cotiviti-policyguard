# PolicyGuard

> **Disclaimer:** PolicyGuard is a human-in-the-loop proof of concept that compares healthcare policy versions, extracts source-grounded changes, proposes validated declarative rules, and tests approved rules against synthetic claims. It does not make autonomous clinical, payment, or claim-denial decisions.

**Topic 3 — Content Management in Health Care** (Cotiviti Generative AI Research Intern assessment)

One-sentence: PolicyGuard compares two versions of a healthcare billing policy, identifies material changes with source evidence, converts an approved change into a validated declarative rule, and tests that rule against synthetic claims.

---

## One-command startup

```bash
cd cotiviti-policyguard
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

**No API key is required.** The demo uses deterministic change analysis and a cached/known-path rule builder for the EXAMPLE1 effective-date revision. Ambiguous integral-language changes abstain and request expert interpretation.

### Tests and evaluation

```bash
pytest -q
python -m evaluation.run_evaluation
```

Optional regenerators:

```bash
python scripts/build_report.py    # report/*.docx + *.md (uses evaluation results)
python scripts/build_slides.py    # slides/PolicyGuard_Presentation.pptx
```

---

## How the code works

End-to-end pipeline:

1. **Diff** — `src/policy_diff.py` uses `difflib.ndiff` for additions/deletions.  
2. **Analyze** — `src/change_analyzer.py` builds source-grounded changes and proposes Pydantic rules (or abstains).  
3. **Constrain** — `src/schema.py` allows only `flag_for_review` / `no_action` (never denial).  
4. **Review** — Streamlit HITL buttons: Approve / Reject / Request Expert Interpretation.  
5. **Apply** — `src/rule_engine.py` deterministically flags synthetic claims after Approve.  
6. **Audit** — `src/audit_log.py` appends JSONL events.

**Docs for evaluators:**

- [docs/CODE_WALKTHROUGH.md](docs/CODE_WALKTHROUGH.md) — full system narrative  
- [docs/FUNCTION_REFERENCE.md](docs/FUNCTION_REFERENCE.md) — every function in plain English  

Claim-impact language is careful only: *potentially affected*, *flagged for review*, *requires expert validation*, *insufficient evidence*, *no automated action taken*.

---

## Architecture overview

```text
app.py (Streamlit HITL UI)
   ├─ policy_diff.compare_policy_versions
   ├─ change_analyzer.analyze_policy_changes
   │     ├─ EXAMPLE1 → PolicyRule (JSON)
   │     └─ ambiguous integral → abstain
   ├─ rule_engine.apply_rule  (after Approve)
   └─ audit_log.append_audit_event
evaluation/run_evaluation.py → results.json / results.md
```

---

## Deliverables map (assessment package)

| Cotiviti deliverable | Path |
| --- | --- |
| Hackathon POC (Streamlit app) | `app.py`, `src/`, `data/` |
| Written report (≈2 pages + bibliography) | `report/PolicyGuard_Report.docx`, `report/PolicyGuard_Report.md` |
| Slide presentation | `slides/PolicyGuard_Presentation.pptx` |
| Video (candidate must record on camera) | `video/SCRIPT.md`, `video/RECORDING_CHECKLIST.md`, `video/PLACEHOLDER.md` — **MP4 not included until you record** |
| Resume | `resume/Haorui_Wang_Resume_2027.pdf` (and ML variant) |
| Evaluation | `evaluation/gold_set.json`, `evaluation/results.md`, `evaluation/results.json` |
| Screenshots | `screenshots/` |
| Code documentation | `docs/CODE_WALKTHROUGH.md`, `docs/FUNCTION_REFERENCE.md` |

Submission reminder (human steps): upload all files to a **public GitHub** repo (including the MP4 in-repo—no Drive/YouTube links), share with `jesus.hurtado@cotiviti.com`, and email that address with subject  
`INTERN - [Position Applied For] - [Full Name] - [University Name]`.

---

## Evaluation

Manually labeled gold set for the demo passages; metrics computed by `evaluation/run_evaluation.py`:

- Change-detection precision / recall  
- Effective-date extraction accuracy  
- Source-citation coverage  
- Rule-test pass rate  
- Abstention correctness  
- Simulated reviewer acceptance  

See `evaluation/results.md` for measured values. **Methodology is POC-scale** (tiny demo set)—not a production performance claim.

---

## Ethics, PHI, and source manifest

- Claims are **synthetic**; no PHI or real patient data.  
- Policy files are **minimal synthetic demonstration excerpts** inspired by CMS Medicare NCCI Policy Manual Chapter XI *style*. They are **not** a republication of full CMS NCCI manuals or CPT content.  
- Conceptual citations and local adaptation notes: `data/source_manifest.csv`.

---

## Project layout

```text
cotiviti-policyguard/
├── README.md
├── requirements.txt
├── app.py
├── data/
│   ├── policy_2025.txt
│   ├── policy_2026.txt
│   ├── synthetic_claims.csv
│   ├── source_manifest.csv
│   └── fixtures/sample_audit.jsonl
├── src/
│   ├── policy_diff.py
│   ├── change_analyzer.py
│   ├── schema.py
│   ├── rule_engine.py
│   └── audit_log.py
├── evaluation/
├── tests/
├── docs/
├── report/
├── slides/
├── video/
├── resume/
├── screenshots/
└── scripts/
```
