# Function reference (PolicyGuard v2)

## Catalog and models

- ``src.catalog.load_catalog`` — validate and cache ``policy_catalog.json``
- ``src.catalog.get_change`` / ``get_sources_for_change`` — evidence lookup
- ``src.models.PolicyRule`` / ``RuleCondition`` — closed operator schema

## Comparison and rules

- ``src.semantic_diff.compare_texts`` — TF-IDF + entity deltas + HTML highlights
- ``src.semantic_diff.extract_text_from_upload`` — in-memory TXT/PDF extract
- ``src.rule_engine.apply_rule`` — deterministic interpreter
- ``src.rule_engine.summarize_claim_impact`` — careful-language summary

## Data and impact

- ``src.demo_data.generate_claims`` / ``write_claims`` — 604-row synthetic set
- ``src.impact.run_portfolio`` — KPIs, charts inputs, prioritized queue
- ``src.impact.review_burden_metrics`` — synthetic HITL vs all-claim screening ratios
- ``src.audit.record_review_decision`` — JSONL with ``automatic_claim_action=false``

## App entry points

- ``app.main`` — Streamlit orchestration for the five workspaces
- ``scripts/run_evaluation.py`` — writes ``evaluation/results.json``
- ``make verify`` — data + evaluation + pytest
