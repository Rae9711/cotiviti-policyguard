"""Fixture-checklist evaluation is documented and not framed as accuracy."""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation_display import (
    WHAT_THIS_IS,
    abstention_checks_table,
    entity_checks_table,
    metric_cards,
    rule_checks_table,
)

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evaluation" / "results.json"


def test_results_json_is_fixture_checklist_not_accuracy():
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    note = payload["scope_note"].lower()
    assert "production accuracy" in note or "do not estimate production" in note
    metrics = payload["metrics"]
    assert metrics["rule_assertions_passed"] == metrics["rule_assertions_total"] == 8
    assert metrics["entity_checks_passed"] == metrics["entity_checks_total"] == 6
    assert metrics["abstention_checks_passed"] == metrics["abstention_checks_total"] == 2
    assert metrics["source_coverage"] == 1.0
    assert all(row.get("meaning") for row in payload["rule_checks"])
    assert all(row.get("meaning") for row in payload["entity_checks"])
    assert all(row.get("meaning") for row in payload["abstention_checks"])


def test_rule_table_uses_flag_labels_not_bare_indices_as_scores():
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    frame = rule_checks_table(payload)
    assert list(frame.columns) == [
        "Case",
        "Change",
        "Scenario",
        "Meaning",
        "Expected flag",
        "Observed",
        "Pass",
    ]
    assert len(frame) == 8
    assert set(frame["Expected flag"]) <= {"Flag for review", "No flag"}
    assert set(frame["Observed"]) <= {"Flag for review", "No flag"}
    assert "should flag" in frame.loc[0, "Meaning"].lower()
    assert frame.loc[0, "Change"] == "NCCI-94662-RETIREMENT"


def test_entity_and_abstention_tables_are_labeled():
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    entities = entity_checks_table(payload)
    absents = abstention_checks_table(payload)
    assert len(entities) == 6
    assert "$2,480" in set(entities["Entity"])
    assert len(absents) == 2
    assert "no rule template" in set(absents["Assertion"])


def test_metric_cards_and_what_this_is_reject_accuracy_framing():
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    cards = metric_cards(payload)
    labels = {c[0] for c in cards}
    values = {c[1] for c in cards}
    assert labels == {
        "Rule assertions",
        "Entity checks",
        "Source coverage",
        "Abstention checks",
    }
    assert "8/8" in values
    assert "6/6" in values
    assert "2/2" in values
    assert "not" in WHAT_THIS_IS.lower() and "accuracy" in WHAT_THIS_IS.lower()
