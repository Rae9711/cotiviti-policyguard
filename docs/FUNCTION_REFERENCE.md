# PolicyGuard Function Reference

Plain-English index of public and non-trivial helpers. Full parameter/return detail lives in module docstrings.

## `src/policy_diff.py`

| Function | What it does |
| --- | --- |
| `compare_policy_versions(old_text, new_text)` | Line-level difflib additions/deletions between two policy texts. |
| `format_diff_summary(diff)` | Short “N addition · M deletion” string for UI captions. |

## `src/change_analyzer.py`

| Function | What it does |
| --- | --- |
| `extract_effective_dates(text)` | Finds ISO `YYYY-MM-DD` dates in a passage. |
| `build_example1_rule(evidence, effective)` | Builds the validated EXAMPLE1 `flag_for_review` declarative rule. |
| `analyze_policy_changes(old_text, new_text, diff=None)` | Produces source-grounded changes; abstains on ambiguous integral language. |
| `propose_rules_from_changes(changes)` | Collects non-abstaining proposed rules only. |
| `_join_relevant_lines(lines, keywords)` | Filters diff lines by keyword relevance. |
| `_is_ambiguous_passage(text)` | True when abstention marker phrases are present. |

## `src/schema.py`

| Symbol | What it does |
| --- | --- |
| `RuleCondition` | One field/operator/value predicate (closed enums). |
| `PolicyRule` | Validated declarative rule JSON (no executable Python). |
| `SourceGroundedChange` | Evidence-backed change object for HITL review. |
| `ReviewEvent` | Structured reviewer decision for audits. |

## `src/rule_engine.py`

| Function | What it does |
| --- | --- |
| `apply_rule(claims, rule)` | Deterministically AND-matches conditions; flags for review only. |
| `summarize_claim_impact(result)` | Careful-language counts + narrative (no denial wording). |
| `_parse_date(value)` | Normalizes claim/condition values to `date`. |
| `_condition_matches(row, condition)` | Evaluates one condition; fails closed on unsupported ops. |

## `src/audit_log.py`

| Function | What it does |
| --- | --- |
| `append_audit_event(event_type, payload, path=...)` | Appends one JSONL audit record; returns the written dict. |
| `read_audit_events(path=...)` | Loads JSONL events (empty list if missing). |
| `count_decisions_by_type(path=...)` | Counts `review_decision` payloads by decision value. |

## `app.py`

| Function | What it does |
| --- | --- |
| `load_text(path)` | Reads a policy file as UTF-8. |
| `load_claims()` | Loads synthetic claims CSV (skips `#` comments). |
| `_init_session_state()` | Ensures decision/impact session keys exist. |
| `_inject_styles()` | Applies payment-integrity visual theme. |
| `_record_decision(change, decision, note="")` | Writes HITL decision + optional claim-impact run to audit log. |
| `_render_change_card(change)` | Renders evidence, rule JSON, buttons, impact table. |
| `main()` | Full Streamlit workflow entrypoint. |

## `evaluation/run_evaluation.py`

| Function | What it does |
| --- | --- |
| `evaluate_change_detection(...)` | Precision/recall/F1 by `change_id`. |
| `evaluate_effective_dates(...)` | Date extraction accuracy vs gold. |
| `evaluate_source_citation(...)` | Evidence/document/section coverage. |
| `evaluate_abstention(...)` | Abstain + propose-rule correctness. |
| `evaluate_rule_tests(gold)` | Claim flagging vs gold claim IDs. |
| `evaluate_reviewer_acceptance(gold)` | Simulated reviewer rates (+ fixture counts). |
| `write_results_markdown(results, path)` | Writes `results.md`. |
| `run_evaluation()` | Runs all metrics; writes JSON + Markdown. |
