"""Deterministic interpreter for Pydantic-validated declarative rules.

Role in PolicyGuard
-------------------
After a human reviewer approves (or dry-runs) a schema-validated rule,
this engine evaluates synthetic claims row-by-row using only the closed
operator vocabulary. Matching is pure Python/pandas — no LLM, no
``eval``, no generated code execution.

Governance / safety
-------------------
* Actions describe review recommendations (configuration, modifier,
  fee-schedule, or mapping review). There is no deny/reprice action.
* Output language for downstream UI must remain careful: "flagged for
  review", "paid amount in scope" — never fraud, denial, or savings.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from src.models import PolicyRule, RuleCondition


def _parse_date(value: Any) -> date:
    """Normalize a claim or condition value into a ``date``."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value)[:10]
    return datetime.strptime(text, "%Y-%m-%d").date()


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _as_float(value: Any) -> float:
    return float(value)


def _as_str(value: Any) -> str:
    if _is_missing(value):
        return ""
    return str(value)


def _condition_matches(row: pd.Series, condition: RuleCondition) -> bool:
    """Evaluate a single rule condition against one claim row.

    Unsupported combinations fail closed (return False).
    """
    field = condition.field
    op = condition.operator
    expected = condition.value
    field_value = row[field] if field in row.index else None

    if op == "missing":
        return _is_missing(field_value)
    if op == "not_missing":
        return not _is_missing(field_value)

    if field == "date_of_service" or op in {"before", "on_or_after"}:
        if field != "date_of_service":
            # Date-order operators only apply to date_of_service in this POC.
            if op in {"before", "on_or_after"}:
                return False
        try:
            actual_date = _parse_date(field_value)
            expected_date = _parse_date(expected)
        except (TypeError, ValueError):
            return False
        if op == "equals":
            return actual_date == expected_date
        if op == "not_equals":
            return actual_date != expected_date
        if op == "before":
            return actual_date < expected_date
        if op == "on_or_after":
            return actual_date >= expected_date

    if op in {
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "outside_tolerance",
    }:
        try:
            actual_num = _as_float(field_value)
            expected_num = _as_float(expected)
        except (TypeError, ValueError):
            return False
        if op == "greater_than":
            return actual_num > expected_num
        if op == "greater_than_or_equal":
            return actual_num >= expected_num
        if op == "less_than":
            return actual_num < expected_num
        if op == "less_than_or_equal":
            return actual_num <= expected_num
        if op == "outside_tolerance":
            tol = 0.0 if condition.tolerance is None else float(condition.tolerance)
            return abs(actual_num - expected_num) > tol

    actual = _as_str(field_value)

    if op == "equals":
        return actual == str(expected)
    if op == "not_equals":
        return actual != str(expected)
    if op == "in":
        values = [str(v) for v in (expected or [])]
        return actual in values
    if op == "not_in":
        values = [str(v) for v in (expected or [])]
        return actual not in values
    if op == "contains":
        return str(expected) in actual
    if op == "not_contains":
        return str(expected) not in actual

    return False


def apply_rule(claims: pd.DataFrame, rule: PolicyRule) -> pd.DataFrame:
    """Apply a validated rule to a claims DataFrame.

    Matching uses AND or OR according to ``rule.logic``. Any match with a
    non-empty review ``action`` is recorded as flagged for human review;
    the specific action string is preserved for the queue and audit trail.
    """
    result = claims.copy()
    matched: list[bool] = []
    actions: list[str] = []

    for _, row in result.iterrows():
        outcomes = [_condition_matches(row, c) for c in rule.conditions]
        if not outcomes:
            is_match = False
        elif rule.logic == "OR":
            is_match = any(outcomes)
        else:
            is_match = all(outcomes)
        matched.append(is_match)
        actions.append(rule.action if is_match else "no_action")

    result["rule_matched"] = matched
    result["rule_action"] = actions
    result["rule_id"] = rule.rule_id
    result["change_flagged"] = matched
    return result


def flagged_subset(result: pd.DataFrame) -> pd.DataFrame:
    """Return rows flagged for human review."""
    if "rule_matched" not in result.columns:
        return result.iloc[0:0].copy()
    return result.loc[result["rule_matched"]].copy()


def summarize_claim_impact(result: pd.DataFrame) -> dict[str, Any]:
    """Build a careful-language summary of rule application results."""
    total = len(result)
    flagged = int(result["rule_matched"].sum()) if total else 0
    paid_in_scope = float(result.loc[result["rule_matched"], "paid_amount"].sum()) if flagged else 0.0
    providers = (
        int(result.loc[result["rule_matched"], "provider_id"].nunique()) if flagged else 0
    )
    narrative = (
        f"{flagged} of {total} synthetic claims are potentially affected "
        f"and routed to review under the proposed rule. "
        f"Synthetic paid amount in scope is ${paid_in_scope:,.2f} across "
        f"{providers} providers. "
        "No automated denial or payment action was taken; "
        "results require expert validation before operational use."
    )
    return {
        "total_claims": total,
        "matched_conditions": flagged,
        "flagged_for_review": flagged,
        "providers_in_scope": providers,
        "paid_amount_in_scope": round(paid_in_scope, 2),
        "narrative": narrative,
    }
