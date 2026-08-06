"""Tests for deterministic rule engine (assessment: Stage 5 claim impact).

Proves AND-matching, date operators, ``flag_for_review`` vs ``no_action``,
and careful-language impact summaries — without any denial semantics.
"""

from datetime import date

import pandas as pd

from src.rule_engine import apply_rule, summarize_claim_impact
from src.schema import PolicyRule, RuleCondition


def _sample_claims() -> pd.DataFrame:
    """Minimal three-row claim fixture for engine unit tests."""
    return pd.DataFrame(
        [
            {
                "claim_id": "CLM-A",
                "date_of_service": "2025-12-15",
                "procedure_code": "EXAMPLE1",
                "modifier": "",
                "provider_id": "PRV-1",
                "paid_amount": 100.0,
            },
            {
                "claim_id": "CLM-B",
                "date_of_service": "2026-01-15",
                "procedure_code": "EXAMPLE1",
                "modifier": "",
                "provider_id": "PRV-1",
                "paid_amount": 100.0,
            },
            {
                "claim_id": "CLM-C",
                "date_of_service": "2026-02-01",
                "procedure_code": "EXAMPLE2",
                "modifier": "59",
                "provider_id": "PRV-2",
                "paid_amount": 90.0,
            },
        ]
    )


def test_apply_rule_flags_example1_on_or_after_effective_date():
    """EXAMPLE1 on/after 2026-01-01 is flagged; earlier DOS and other codes are not."""
    rule = PolicyRule(
        rule_id="RULE-EXAMPLE1-2026",
        source_document="CMS NCCI 2026 Demo",
        source_section="XI.D",
        effective_date=date(2026, 1, 1),
        change_type="revision",
        conditions=[
            RuleCondition(
                field="procedure_code", operator="equals", value="EXAMPLE1"
            ),
            RuleCondition(
                field="date_of_service",
                operator="on_or_after",
                value="2026-01-01",
            ),
        ],
        action="flag_for_review",
        evidence_text="EXAMPLE1 flagged on/after 2026-01-01",
        requires_human_review=True,
        confidence=0.9,
    )

    result = apply_rule(_sample_claims(), rule)
    matched = result.set_index("claim_id")["rule_matched"]
    actions = result.set_index("claim_id")["rule_action"]

    assert matched["CLM-A"] is False or matched["CLM-A"] == False
    assert matched["CLM-B"] is True or matched["CLM-B"] == True
    assert matched["CLM-C"] is False or matched["CLM-C"] == False
    assert actions["CLM-B"] == "flag_for_review"
    assert actions["CLM-A"] == "no_action"


def test_apply_rule_no_action_does_not_flag():
    """When action is no_action, matches are recorded but not flagged for review."""
    rule = PolicyRule(
        rule_id="RULE-NOOP",
        source_document="demo",
        source_section="XI.D",
        effective_date=date(2026, 1, 1),
        change_type="addition",
        conditions=[
            RuleCondition(
                field="procedure_code", operator="equals", value="EXAMPLE1"
            ),
        ],
        action="no_action",
        evidence_text="no-op",
        confidence=0.5,
    )
    result = apply_rule(_sample_claims(), rule)
    assert result["rule_matched"].sum() == 2
    assert (result["rule_action"] == "no_action").all()


def test_summarize_claim_impact_uses_careful_language():
    """Impact narrative must use careful wording and never denial/fraud terms."""
    rule = PolicyRule(
        rule_id="RULE-EXAMPLE1-2026",
        source_document="demo",
        source_section="XI.D",
        effective_date=date(2026, 1, 1),
        change_type="revision",
        conditions=[
            RuleCondition(
                field="procedure_code", operator="equals", value="EXAMPLE1"
            ),
            RuleCondition(
                field="date_of_service",
                operator="on_or_after",
                value="2026-01-01",
            ),
        ],
        action="flag_for_review",
        evidence_text="evidence",
        confidence=0.9,
    )
    result = apply_rule(_sample_claims(), rule)
    summary = summarize_claim_impact(result)
    narrative = summary["narrative"].lower()
    assert "flagged for review" in narrative
    assert "potentially affected" in narrative
    assert "fraud" not in narrative
    assert "denied" not in narrative
    assert "deny" not in narrative
