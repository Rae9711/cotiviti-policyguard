"""Tests for audit logging (assessment: Stage 6 accountability trail).

Proves append/read round-trip, decision counting, and that missing files
are handled safely for a fresh demo session.
"""

import json
from pathlib import Path

from src.audit_log import (
    append_audit_event,
    count_decisions_by_type,
    read_audit_events,
)


def test_append_and_read_audit_event(tmp_path: Path):
    """Appending a review_decision writes one JSONL record readable back."""
    path = tmp_path / "audit.jsonl"
    record = append_audit_event(
        "review_decision",
        {
            "change_id": "CHG-EXAMPLE1-EFFECTIVE-DATE",
            "decision": "approve",
            "rule_id": "RULE-EXAMPLE1-DOS-2026",
        },
        path=path,
    )
    assert "timestamp" in record
    assert record["event_type"] == "review_decision"
    events = read_audit_events(path)
    assert len(events) == 1
    assert events[0]["payload"]["decision"] == "approve"
    # file is valid JSONL
    raw = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(raw) == 1
    json.loads(raw[0])


def test_read_missing_audit_returns_empty(tmp_path: Path):
    """Missing audit file yields [] so the UI can start without setup."""
    assert read_audit_events(tmp_path / "missing.jsonl") == []


def test_count_decisions_by_type(tmp_path: Path):
    """Decision counter groups review_decision events for evaluation proxies."""
    path = tmp_path / "audit.jsonl"
    append_audit_event(
        "review_decision",
        {"change_id": "A", "decision": "approve"},
        path=path,
    )
    append_audit_event(
        "review_decision",
        {"change_id": "B", "decision": "request_expert_interpretation"},
        path=path,
    )
    append_audit_event(
        "claim_impact_run",
        {"change_id": "A", "flagged_for_review": 1},
        path=path,
    )
    counts = count_decisions_by_type(path)
    assert counts.get("approve") == 1
    assert counts.get("request_expert_interpretation") == 1
    assert "claim_impact_run" not in counts


def test_sample_fixture_audit_is_readable():
    """Repo fixture audit log remains valid JSONL for evaluation demos."""
    events = read_audit_events(Path("data/fixtures/sample_audit.jsonl"))
    assert len(events) >= 3
    decisions = [e for e in events if e["event_type"] == "review_decision"]
    assert any(d["payload"]["decision"] == "approve" for d in decisions)
    assert any(
        d["payload"]["decision"] == "request_expert_interpretation" for d in decisions
    )
