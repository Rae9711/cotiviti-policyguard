"""Tests for change analysis / abstention (assessment: Stages 3–4 + ambiguous path).

Proves deterministic EXAMPLE1 rule proposal, ambiguous integral abstention,
and that abstaining changes never emit a runnable rule.
"""

from datetime import date
from pathlib import Path

from src.change_analyzer import (
    analyze_policy_changes,
    extract_effective_dates,
    propose_rules_from_changes,
)


DATA = Path("data")


def _demo_texts() -> tuple[str, str]:
    """Load the assessment demo policy pair from disk."""
    old = (DATA / "policy_2025.txt").read_text(encoding="utf-8")
    new = (DATA / "policy_2026.txt").read_text(encoding="utf-8")
    return old, new


def test_extract_effective_dates_finds_iso_dates():
    """ISO dates embedded in evidence passages are parsed in order."""
    dates = extract_effective_dates("Effective on 2026-01-01 and again 2026-06-15.")
    assert dates == [date(2026, 1, 1), date(2026, 6, 15)]


def test_analyze_demo_proposes_example1_rule():
    """Machine-clear EXAMPLE1 revision must propose RULE-EXAMPLE1-DOS-2026."""
    old, new = _demo_texts()
    changes = analyze_policy_changes(old, new)
    by_id = {c.change_id: c for c in changes}
    assert "CHG-EXAMPLE1-EFFECTIVE-DATE" in by_id
    chg = by_id["CHG-EXAMPLE1-EFFECTIVE-DATE"]
    assert chg.abstain is False
    assert chg.proposed_rule is not None
    assert chg.proposed_rule.rule_id == "RULE-EXAMPLE1-DOS-2026"
    assert chg.effective_date == date(2026, 1, 1)
    assert chg.proposed_rule.action == "flag_for_review"
    assert "deny" not in chg.proposed_rule.action


def test_analyze_demo_abstains_on_ambiguous_integral_language():
    """Ambiguous 'integral' addition must abstain with no proposed rule."""
    old, new = _demo_texts()
    changes = analyze_policy_changes(old, new)
    by_id = {c.change_id: c for c in changes}
    assert "CHG-EXAMPLE2-INTEGRAL-AMBIGUOUS" in by_id
    amb = by_id["CHG-EXAMPLE2-INTEGRAL-AMBIGUOUS"]
    assert amb.abstain is True
    assert amb.proposed_rule is None
    assert amb.change_type == "ambiguous"
    assert amb.abstain_reason is not None
    assert "expert" in amb.abstain_reason.lower() or "interpretation" in amb.abstain_reason.lower()


def test_propose_rules_skips_abstaining_changes():
    """Helper collects only non-abstaining proposed rules for the review queue."""
    old, new = _demo_texts()
    changes = analyze_policy_changes(old, new)
    rules = propose_rules_from_changes(changes)
    assert len(rules) >= 1
    assert all(r.rule_id for r in rules)
    assert all(c.proposed_rule in rules or c.abstain or c.proposed_rule is None for c in changes)


def test_evidence_passages_are_non_empty():
    """Source grounding requires non-empty evidence for each detected change."""
    old, new = _demo_texts()
    for change in analyze_policy_changes(old, new):
        assert change.evidence_passage.strip()
        assert change.document.strip()
        assert change.section.strip()
