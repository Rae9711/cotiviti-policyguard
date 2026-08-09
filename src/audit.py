"""Append-only JSONL audit log with explicit non-automation guarantee.

Role in PolicyGuard
-------------------
Records human-in-the-loop decisions (approve / reject / escalate) and
related system events. Every persisted review payload hard-codes
``automatic_claim_action: false`` so exports cannot be misread as
autonomous claim denial or repricing.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.models import ReviewDecision

DEFAULT_AUDIT_PATH = Path("data") / "audit_log.jsonl"


def append_audit_event(
    event_type: str,
    payload: dict[str, Any],
    path: Path | str = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    """Append one JSON audit event to a JSONL file."""
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    safe_payload = dict(payload)
    if event_type in {"review_decision", "governance_decision"}:
        safe_payload["automatic_claim_action"] = False
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": safe_payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def record_review_decision(
    change_id: str,
    decision: ReviewDecision,
    reviewer_note: str = "",
    rule_id: str | None = None,
    source_verified: bool = False,
    path: Path | str = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    """Persist a governance decision with the required safety flag."""
    payload = {
        "change_id": change_id,
        "decision": decision,
        "reviewer_note": reviewer_note,
        "rule_id": rule_id,
        "source_verified": source_verified,
        "automatic_claim_action": False,
    }
    return append_audit_event("review_decision", payload, path=path)


def read_audit_events(path: Path | str = DEFAULT_AUDIT_PATH) -> list[dict[str, Any]]:
    """Load all audit events from a JSONL file."""
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


def audit_events_jsonl(path: Path | str = DEFAULT_AUDIT_PATH) -> str:
    """Return the raw JSONL contents for download."""
    log_path = Path(path)
    if not log_path.exists():
        return ""
    return log_path.read_text(encoding="utf-8")


def assert_no_automatic_claim_action(path: Path | str = DEFAULT_AUDIT_PATH) -> bool:
    """Return True when every review event forbids automatic claim action."""
    for event in read_audit_events(path):
        if event.get("event_type") != "review_decision":
            continue
        if event.get("payload", {}).get("automatic_claim_action") is not False:
            return False
    return True
