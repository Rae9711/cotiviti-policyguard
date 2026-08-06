# PolicyGuard Code Walkthrough

This document explains the end-to-end system for evaluators reading the repository. PolicyGuard is a **human-in-the-loop** proof of concept for Topic 3 (Content Management in Health Care): compare policy versions → ground material changes → propose validated declarative rules → test approved rules on synthetic claims → audit reviewer decisions.

> **Disclaimer:** PolicyGuard does not make autonomous clinical, payment, or claim-denial decisions.

For a function-by-function index, see [FUNCTION_REFERENCE.md](FUNCTION_REFERENCE.md).

---

## Pipeline (one picture)

```text
policy_2025.txt ─┐
                 ├─► policy_diff.compare_policy_versions (difflib)
policy_2026.txt ─┘              │
                                ▼
                 change_analyzer.analyze_policy_changes
                    ├─ machine-clear → PolicyRule (Pydantic JSON)
                    └─ ambiguous    → abstain (no rule)
                                │
                                ▼
                 Streamlit HITL: Approve / Reject / Request Expert Interpretation
                                │
                    (only on Approve + non-abstain)
                                ▼
                 rule_engine.apply_rule(synthetic_claims.csv)
                                │
                                ▼
                 audit_log.append_audit_event → data/audit_log.jsonl
```

---

## How `app.py` orchestrates the UI

`app.py` is the Streamlit entrypoint. Section comments in the file mark each assessment stage:

| Stage | What the UI does |
| --- | --- |
| 0 | Branding + **prominent governance disclaimer** |
| 1 | Select old/new policy pair from `POLICY_OPTIONS` |
| 2 | Show side-by-side texts + difflib additions/deletions |
| 3–4 | Source-grounded change cards (document, section, effective date, evidence) + proposed JSON rule |
| HITL | Approve / Reject / Request Expert Interpretation buttons |
| 5 | On Approve: deterministic claim impact with careful language only |
| 6 | Audit trail JSON preview |
| Optional | Evaluation panel from `evaluation/results.json` |

Session state stores reviewer decisions and impact DataFrames so reruns remain coherent. Runtime audit lines append to `data/audit_log.jsonl` (gitignored); fixtures live in `data/fixtures/`.

**No API key is required.** Rule proposals come from the deterministic analyzer for known demo patterns.

---

## How `policy_diff.py` works

- Splits each policy on newlines.
- Runs `difflib.ndiff`.
- Collects lines prefixed `+ ` as **additions** and `- ` as **deletions**.
- Ignores unchanged (`  `) and hint (`? `) lines.

This stage is intentionally dumb and auditable: it does not interpret payment meaning. Interpretation happens next.

---

## How `change_analyzer.py` works

Takes old/new text (and optional precomputed diff) and emits `SourceGroundedChange` objects:

1. **CHG-EXAMPLE1-EFFECTIVE-DATE** — detects EXAMPLE1 date-threshold language; extracts `2026-01-01`; builds `RULE-EXAMPLE1-DOS-2026` via `build_example1_rule`.
2. **CHG-EXAMPLE2-INTEGRAL-AMBIGUOUS** — detects “generally considered integral” / ambiguous markers; sets `abstain=True`; **no** `proposed_rule`.
3. **CHG-EXAMPLE2-SCREENING-DELETE** — informational deletion; no claim predicate rule.

Abstention is a first-class product behavior: ambiguous policy must not become silent automation.

---

## How `schema.py` constrains proposals

Pydantic models define a **closed vocabulary**:

- Condition `field` / `operator` enums only.
- Rule `action` ∈ {`flag_for_review`, `no_action`} — **never** deny/fraud/reject_claim.
- `SourceGroundedChange.abstain` blocks runnable proposals for ambiguous items.

Rules are JSON-serializable data, not Python source. That is deliberate: payment-integrity systems should not `eval` model-generated code.

---

## How `rule_engine.py` applies rules

`apply_rule(claims, rule)`:

- Evaluates **all** conditions with logical AND.
- Date fields support `before` / `on_or_after` / equality.
- Writes `rule_matched`, `rule_action`, `rule_id` columns.
- `summarize_claim_impact` emits careful phrasing (“potentially affected”, “flagged for review”, “no automated denial…”).

---

## How `audit_log.py` records decisions

Append-only JSONL:

```json
{"timestamp":"...Z","event_type":"review_decision","payload":{...}}
```

Event types used in the demo: `change_detected` / `rule_proposed`, `review_decision`, `claim_impact_run`, `abstention`. Helpers `read_audit_events` and `count_decisions_by_type` support the UI and evaluation.

---

## How evaluation works

`python -m evaluation.run_evaluation` (or `evaluation/run_evaluation.py`):

1. Loads `evaluation/gold_set.json` (hand-labeled demo expectations).
2. Runs the live analyzer + rule engine on demo data.
3. Computes precision/recall, date accuracy, citation coverage, abstention correctness, rule-test pass rate, simulated reviewer rates.
4. Writes `evaluation/results.json` and `evaluation/results.md`.

**Honesty:** the gold set is tiny and demo-specific. Metrics show instrumentation quality, not production readiness.

---

## Data files

| Path | Role |
| --- | --- |
| `data/policy_2025.txt` | Synthetic prior-year NCCI-style excerpt |
| `data/policy_2026.txt` | Synthetic newer excerpt (EXAMPLE1 change + ambiguous integral language) |
| `data/synthetic_claims.csv` | ~25 fictional claims; no PHI |
| `data/source_manifest.csv` | Conceptual CMS citations + local adaptation notes |
| `data/fixtures/sample_audit.jsonl` | Sample audit events for evaluation / demos |
| `data/audit_log.jsonl` | Runtime log (gitignored) |

Policy files are **minimal synthetic adaptations** for assessment — not full CMS NCCI or CPT republication.

---

## Safety language (UI + engine)

Allowed: potentially affected, flagged for review, requires expert validation, insufficient evidence, no automated action taken.

Forbidden in product copy: fraud detected, claim denied, abusive provider, automatic rejection.
