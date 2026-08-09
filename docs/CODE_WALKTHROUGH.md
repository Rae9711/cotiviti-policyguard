# Code walkthrough (PolicyGuard v2)

## Runtime path

1. ``app.py`` loads the curated catalog and synthetic claims.
2. Sidebar selects the focus change; five tabs tell the demo story.
3. ``src/semantic_diff.py`` compares before/after snapshots (and optional uploads).
4. ``src/models.py`` + ``src/rule_engine.py`` validate and interpret rules.
5. ``src/impact.py`` builds portfolio KPIs, charts, and the reviewer queue.
6. ``src/audit.py`` records approve/reject/escalate with ``automatic_claim_action=false``.

## Module map

| Module | Responsibility |
|---|---|
| ``catalog.py`` | Load/validate ``policy_catalog.json`` |
| ``demo_data.py`` | Deterministic 604-row synthetic claims |
| ``semantic_diff.py`` | TF-IDF / entity-aware local comparison |
| ``rule_engine.py`` | Closed-operator interpreter |
| ``impact.py`` | Portfolio analytics + queue |
| ``audit.py`` | JSONL governance trail |
| ``ui.py`` | Shared styling and Plotly charts |
| ``models.py`` | Pydantic safety boundary |

## What not to look for

There is no multi-agent orchestrator, no generated-code execution, and no
automatic claim denial path. The POC is intentionally controlled for a
reliable ≤5 minute demonstration.
