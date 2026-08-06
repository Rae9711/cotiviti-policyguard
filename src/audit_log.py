"""Append-only JSONL audit log for reviewer decisions and system events.

Role in PolicyGuard
-------------------
Creates a durable, timestamped trail of human-in-the-loop decisions
(Approve / Reject / Request Expert Interpretation) and related events
such as rule proposals and claim-impact runs. Supports accountability
aligned with payment-policy governance expectations.

Format
------
Each line is one JSON object::

    {"timestamp": "<ISO-8601 UTC>", "event_type": "...", "payload": {...}}

Runtime logs default to ``data/audit_log.jsonl`` (gitignored). Sample
fixtures for evaluation live under ``data/fixtures/``.

Governance
----------
Audit entries record *what was decided*, not clinical judgments. They
never themselves deny claims.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = Path("data") / "audit_log.jsonl"


def append_audit_event(
    event_type: str,
    payload: dict[str, Any],
    path: Path | str = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    """Append one JSON audit event to a JSONL file.

    Parameters
    ----------
    event_type:
        Short machine key, e.g. ``review_decision``, ``rule_proposed``,
        ``claim_impact_run``, ``abstention``.
    payload:
        JSON-serializable context (change_id, decision, rule_id, notes).
    path:
        Destination JSONL path; parent directories are created as needed.

    Returns
    -------
    dict
        The full record that was written (includes UTC timestamp).

    Edge cases
    ----------
    * Non-serializable payload values will raise ``TypeError`` from
      ``json.dumps`` — callers should pass plain dict/list/str/number.
    """
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def read_audit_events(path: Path | str = DEFAULT_AUDIT_PATH) -> list[dict[str, Any]]:
    """Load all audit events from a JSONL file.

    Parameters
    ----------
    path:
        JSONL file to read.

    Returns
    -------
    list[dict]
        Parsed records in file order. Missing files yield an empty list
        (convenient for fresh demos). Blank lines are skipped.
    """
    log_path = Path(path)
    if not log_path.exists():
        return []
    events: list[dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def count_decisions_by_type(
    path: Path | str = DEFAULT_AUDIT_PATH,
) -> dict[str, int]:
    """Count ``review_decision`` events grouped by decision value.

    Used by evaluation (reviewer-acceptance proxy) and the optional
    Streamlit evaluation panel.

    Parameters
    ----------
    path:
        Audit JSONL path (runtime or fixture).

    Returns
    -------
    dict[str, int]
        Mapping of decision string → count (e.g. ``approve``, ``reject``,
        ``request_expert_interpretation``).
    """
    counts: dict[str, int] = {}
    for event in read_audit_events(path):
        if event.get("event_type") != "review_decision":
            continue
        decision = str(event.get("payload", {}).get("decision", "unknown"))
        counts[decision] = counts.get(decision, 0) + 1
    return counts
