"""Deterministic application of declarative PolicyRule objects to claims.

Role in PolicyGuard
-------------------
After a human reviewer **approves** a Pydantic-validated rule, this engine
evaluates synthetic claims row-by-row using only the rule's conditions and
action. Matching is pure Python/pandas — no LLM, no ``eval``, no generated
code execution.

Why not execute LLM-generated Python?
-------------------------------------
Executing model-authored code would create injection and auditability
risks inappropriate for payment-integrity workflows. PolicyGuard stores
rules as constrained JSON (field / operator / value) and interprets them
here with a fixed operator vocabulary.

Governance / safety
-------------------
* Supported actions are ``flag_for_review`` and ``no_action`` only.
* There is no ``deny``, ``reject_claim``, or ``fraud`` action in the schema
  or this engine.
* Output language for downstream UI must remain careful: "flagged for
  review", "potentially affected", never "fraud detected" or "claim denied".
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from src.schema import PolicyRule, RuleCondition


def _parse_date(value: Any) -> date:
    """Normalize a claim or condition value into a ``date``.

    Parameters
    ----------
    value:
        A ``date``, ``datetime``, or ISO date string (``YYYY-MM-DD``;
        longer timestamps are truncated to the first 10 characters).

    Returns
    -------
    date
        Parsed calendar date.

    Raises
    ------
    ValueError
        If the string cannot be parsed as an ISO date.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _condition_matches(row: pd.Series, condition: RuleCondition) -> bool:
    """Evaluate a single rule condition against one claim row.

    Parameters
    ----------
    row:
        Claim record with columns matching ``RuleCondition.field``.
    condition:
        Declarative condition (field, operator, value).

    Returns
    -------
    bool
        True if the condition holds for this row.

    Notes
    -----
    Date operators (``before``, ``on_or_after``, ``equals``, ``not_equals``)
    apply only when ``field == "date_of_service"``. For other fields,
    only string equality operators are supported; date-order operators
    return False (fail closed for unsupported combinations).
    """
    field_value = row[condition.field]
    op = condition.operator
    expected = condition.value

    if condition.field == "date_of_service":
        actual_date = _parse_date(field_value)
        expected_date = _parse_date(expected)
        if op == "equals":
            return actual_date == expected_date
        if op == "not_equals":
            return actual_date != expected_date
        if op == "before":
            return actual_date < expected_date
        if op == "on_or_after":
            return actual_date >= expected_date
        return False

    actual = "" if pd.isna(field_value) else str(field_value)
    if op == "equals":
        return actual == expected
    if op == "not_equals":
        return actual != expected
    # before / on_or_after only apply to dates — fail closed
    return False


def apply_rule(claims: pd.DataFrame, rule: PolicyRule) -> pd.DataFrame:
    """Apply an approved declarative rule to a claims DataFrame.

    Matching requires **all** conditions to be true (logical AND). When
    ``rule.action`` is ``no_action``, matched rows still record
    ``rule_matched=True`` but ``rule_action`` remains ``no_action`` so
    they are not presented as flagged for review.

    Parameters
    ----------
    claims:
        Synthetic claims with at least the columns referenced by
        ``rule.conditions`` (demo CSV includes ``date_of_service``,
        ``procedure_code``, ``modifier``, ``provider_id``).
    rule:
        Validated :class:`~src.schema.PolicyRule`.

    Returns
    -------
    pd.DataFrame
        Copy of ``claims`` with added columns:

        * ``rule_matched`` (bool)
        * ``rule_action`` (``flag_for_review`` or ``no_action``)
        * ``rule_id`` (str)

    Safety
    ------
    Does not modify payment amounts, deny claims, or write audit events;
    callers (UI) decide how to present "potentially affected" rows and
    whether to append an audit record.
    """
    result = claims.copy()
    matched: list[bool] = []
    actions: list[str] = []

    for _, row in result.iterrows():
        is_match = all(_condition_matches(row, c) for c in rule.conditions)
        matched.append(is_match)
        if is_match and rule.action == "flag_for_review":
            actions.append("flag_for_review")
        else:
            actions.append("no_action")

    result["rule_matched"] = matched
    result["rule_action"] = actions
    result["rule_id"] = rule.rule_id
    return result


def summarize_claim_impact(result: pd.DataFrame) -> dict[str, int | str]:
    """Build a careful-language summary of rule application results.

    Parameters
    ----------
    result:
        Output of :func:`apply_rule`.

    Returns
    -------
    dict
        Counts and a narrative string using only approved phrasing
        (``potentially affected``, ``flagged for review``, etc.).
    """
    total = len(result)
    flagged = int((result["rule_action"] == "flag_for_review").sum())
    matched = int(result["rule_matched"].sum())
    narrative = (
        f"{flagged} of {total} synthetic claims are potentially affected "
        f"and flagged for review under the approved rule "
        f"({matched} matched all conditions). "
        "No automated denial or payment action was taken; "
        "results require expert validation before operational use."
    )
    return {
        "total_claims": total,
        "matched_conditions": matched,
        "flagged_for_review": flagged,
        "narrative": narrative,
    }
