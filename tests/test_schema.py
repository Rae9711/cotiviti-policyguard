"""Tests for Pydantic schema validation (assessment: constrained rule JSON).

Proves that invalid actions/fields/operators are rejected and that valid
demo rules serialize cleanly — supporting the 'not executable Python' design.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from src.schema import PolicyRule, RuleCondition, SourceGroundedChange


def test_policy_rule_accepts_flag_for_review_action():
    """Happy path: flag_for_review rule with dual conditions validates."""
    rule = PolicyRule(
        rule_id="RULE-OK",
        source_document="demo",
        source_section="XI.D",
        effective_date=date(2026, 1, 1),
        change_type="revision",
        conditions=[
            RuleCondition(field="procedure_code", operator="equals", value="EXAMPLE1"),
        ],
        action="flag_for_review",
        evidence_text="passage",
        confidence=0.8,
    )
    assert rule.action == "flag_for_review"
    assert rule.requires_human_review is True


def test_policy_rule_rejects_deny_action():
    """Governance: schema must not allow claim-denial style actions."""
    with pytest.raises(ValidationError):
        PolicyRule(
            rule_id="RULE-BAD",
            source_document="demo",
            source_section="XI.D",
            effective_date=date(2026, 1, 1),
            change_type="revision",
            conditions=[
                RuleCondition(
                    field="procedure_code", operator="equals", value="EXAMPLE1"
                ),
            ],
            action="deny",  # type: ignore[arg-type]
            evidence_text="passage",
            confidence=0.8,
        )


def test_rule_condition_rejects_unknown_field():
    """Closed field enum rejects arbitrary claim columns / injection vectors."""
    with pytest.raises(ValidationError):
        RuleCondition(field="sql_injection", operator="equals", value="x")  # type: ignore[arg-type]


def test_source_grounded_change_abstain_without_rule():
    """Ambiguous changes may abstain with no proposed_rule attached."""
    change = SourceGroundedChange(
        change_id="CHG-AMB",
        document="demo",
        section="XI.D",
        effective_date=None,
        change_type="ambiguous",
        evidence_passage="generally considered integral",
        summary="insufficient evidence",
        confidence=0.3,
        abstain=True,
        abstain_reason="requires expert interpretation",
        proposed_rule=None,
    )
    assert change.abstain is True
    assert change.proposed_rule is None


def test_confidence_bounds():
    """Confidence outside [0, 1] must fail validation."""
    with pytest.raises(ValidationError):
        SourceGroundedChange(
            change_id="CHG-X",
            document="demo",
            section="XI.D",
            effective_date=None,
            change_type="addition",
            evidence_passage="x",
            summary="x",
            confidence=1.5,
        )
