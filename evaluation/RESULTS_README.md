# Evaluation results (`results.json`)

This file is a **software/fixture checklist** for the deterministic PolicyGuard demo.
It is **not** model accuracy, precision/recall on real claims, or a production benchmark.

Regenerate with:

```bash
python scripts/run_evaluation.py
```

The Streamlit **05 · Governance** tab renders these checks as labeled tables.
Raw JSON is available there under a collapsed expander for evaluators who want the file.

## Metrics

| Field | Typical value | Meaning |
|---|---|---|
| `rule_assertions_passed` | 8/8 | Eight handcrafted synthetic claim cases (2 per executable rule) |
| `entity_checks_passed` | 6/6 | Comparison engine found expected dates, dollars, and codes |
| `source_coverage` | 1.0 | All 5 curated changes have official source provenance |
| `abstention_checks_passed` | 2/2 | Clinical/fitness change has no rule template + documented reason |

## `rule_checks` indices 0–7

Streamlit's `st.json` labels list items `0`, `1`, `2`… Those numbers are **array indices**, not scores.
`expected` / `observed` `true` = claim matches the rule (flag for review); `false` = no flag.
`passed` = `expected == observed`.

| # | `change_id` | `case` | Meaning |
|---|---|---|---|
| 0 | NCCI-94662-RETIREMENT | 94662 post deletion | After 2026-01-01, code 94662 **should flag** |
| 1 | NCCI-94662-RETIREMENT | 94662 prior year | Before effective date, **should not flag** |
| 2 | THERAPY-KX-THRESHOLD-2026 | KX missing over threshold | Over $2,480 without KX **should flag** |
| 3 | THERAPY-KX-THRESHOLD-2026 | KX present over threshold | Over threshold with KX **should not flag** |
| 4 | TELEHEALTH-Q3014-FEE-2026 | Q3014 outside tolerance | Fee drift beyond tolerance **should flag** |
| 5 | TELEHEALTH-Q3014-FEE-2026 | Q3014 within tolerance | Small variance **should not flag** |
| 6 | THERAPY-RTM-CODES-2026 | RTM unmapped | New RTM code unmapped **should flag** |
| 7 | THERAPY-RTM-CODES-2026 | RTM mapped | Mapped RTM **should not flag** |

## `entity_checks` indices 0–5

Did semantic/entity extraction see the expected snapshot deltas ($2,480 added, $2,410 removed, January 1 2026, Q3014 fees, code 98984, etc.)?

## `abstention_checks`

| # | Check | Meaning |
|---|---|---|
| 0 | no rule template | Clinical/fitness change generated no claim-level rule |
| 1 | reason documented | Abstention reason is written for reviewers |
