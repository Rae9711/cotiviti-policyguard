"""Rule-engine operator and safety tests for PolicyGuard v2."""

from __future__ import annotations

import pandas as pd

from src.catalog import get_change
from src.models import PolicyRule, RuleCondition
from src.rule_engine import apply_rule, summarize_claim_impact


def test_94662_post_deletion_flags():
    rule = get_change("NCCI-94662-RETIREMENT").rule_template
    claims = pd.DataFrame(
        [
            {
                "claim_id": "A",
                "date_of_service": "2026-01-01",
                "procedure_code": "94662",
                "paid_amount": 10,
                "provider_id": "P",
            },
            {
                "claim_id": "B",
                "date_of_service": "2025-12-31",
                "procedure_code": "94662",
                "paid_amount": 10,
                "provider_id": "P",
            },
        ]
    )
    out = apply_rule(claims, rule)
    assert bool(out.loc[out.claim_id == "A", "rule_matched"].iloc[0]) is True
    assert bool(out.loc[out.claim_id == "B", "rule_matched"].iloc[0]) is False


def test_kx_not_contains_and_threshold():
    rule = get_change("THERAPY-KX-THRESHOLD-2026").rule_template
    claims = pd.DataFrame(
        [
            {
                "claim_id": "A",
                "date_of_service": "2026-02-01",
                "therapy_category": "PT",
                "cumulative_therapy_spend_ytd": 2500,
                "modifier": "",
                "procedure_code": "97110",
                "paid_amount": 10,
                "provider_id": "P",
            },
            {
                "claim_id": "B",
                "date_of_service": "2026-02-01",
                "therapy_category": "PT",
                "cumulative_therapy_spend_ytd": 2500,
                "modifier": "KX",
                "procedure_code": "97110",
                "paid_amount": 10,
                "provider_id": "P",
            },
        ]
    )
    out = apply_rule(claims, rule)
    assert bool(out.loc[out.claim_id == "A", "rule_matched"].iloc[0]) is True
    assert bool(out.loc[out.claim_id == "B", "rule_matched"].iloc[0]) is False


def test_outside_tolerance():
    rule = get_change("TELEHEALTH-Q3014-FEE-2026").rule_template
    claims = pd.DataFrame(
        [
            {
                "claim_id": "A",
                "date_of_service": "2026-01-02",
                "procedure_code": "Q3014",
                "allowed_amount": 28.0,
                "paid_amount": 28,
                "provider_id": "P",
            },
            {
                "claim_id": "B",
                "date_of_service": "2026-01-02",
                "procedure_code": "Q3014",
                "allowed_amount": 31.85,
                "paid_amount": 31.85,
                "provider_id": "P",
            },
        ]
    )
    out = apply_rule(claims, rule)
    assert bool(out.loc[out.claim_id == "A", "rule_matched"].iloc[0]) is True
    assert bool(out.loc[out.claim_id == "B", "rule_matched"].iloc[0]) is False


def test_summary_careful_language():
    rule = PolicyRule(
        rule_id="R",
        name="t",
        conditions=[RuleCondition(field="procedure_code", operator="equals", value="X")],
        action="coding_configuration_review",
        reason="demo",
        severity="low",
    )
    claims = pd.DataFrame(
        [{"claim_id": "A", "procedure_code": "X", "paid_amount": 12.5, "provider_id": "P1"}]
    )
    summary = summarize_claim_impact(apply_rule(claims, rule))
    text = summary["narrative"].lower()
    assert "routed to review" in text or "flagged" in text
    assert "fraud" not in text
    assert "denied" not in text
    assert "savings" not in text
