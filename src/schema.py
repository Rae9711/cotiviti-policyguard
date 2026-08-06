"""Pydantic models constraining declarative, human-reviewed policy rules.

Role in PolicyGuard
-------------------
All proposed rules and grounded changes must validate against these models
before they appear in the UI or reach the rule engine. This is the safety
boundary that prevents free-form LLM (or heuristic) output from becoming
executable payment logic.

Key constraints
---------------
* ``RuleCondition.field`` / ``operator`` are closed enums — not arbitrary
  Python expressions.
* ``PolicyRule.action`` allows only ``flag_for_review`` or ``no_action``
  (never deny / fraud / auto-reject).
* ``SourceGroundedChange.abstain`` marks changes that require expert
  interpretation and must not produce runnable rules.

These models serialize to JSON for display, audit, and evaluation.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    """One atomic predicate in a declarative policy rule.

    Attributes
    ----------
    field:
        Claim column to evaluate. Limited to demo claim schema fields.
    operator:
        Comparison operator. Date-order operators are only meaningful for
        ``date_of_service`` (enforced at evaluation time in the engine).
    value:
        Expected value as a string (ISO dates for date fields).
    """

    field: Literal["date_of_service", "procedure_code", "modifier", "provider_id"]
    operator: Literal["equals", "not_equals", "before", "on_or_after"]
    value: str


class PolicyRule(BaseModel):
    """Validated declarative rule — JSON, not executable Python.

    Attributes
    ----------
    rule_id:
        Stable identifier for audit and claim-impact join keys.
    source_document / source_section:
        Provenance for human reviewers and citation coverage metrics.
    effective_date:
        Policy effective date associated with the change.
    change_type:
        Nature of the underlying policy edit; ``ambiguous`` rules should
        not normally be proposed (analyzer abstains instead).
    conditions:
        AND-combined predicates evaluated by :mod:`src.rule_engine`.
    action:
        ``flag_for_review`` marks potentially affected claims; ``no_action``
        records matches without flagging. No denial actions exist.
    evidence_text:
        Source passage grounding the rule proposal.
    requires_human_review:
        Always True for this POC — governance default.
    confidence:
        Heuristic confidence in [0, 1]; low values should drive abstention
        upstream rather than silent automation.
    """

    rule_id: str
    source_document: str
    source_section: str
    effective_date: date
    change_type: Literal["addition", "deletion", "revision", "ambiguous"]
    conditions: list[RuleCondition]
    action: Literal["flag_for_review", "no_action"]
    evidence_text: str
    requires_human_review: bool = True
    confidence: float = Field(ge=0.0, le=1.0)


class SourceGroundedChange(BaseModel):
    """A detected policy change with source evidence for human review.

    Attributes
    ----------
    change_id:
        Stable id used in the UI and audit log.
    document / section:
        Source grounding metadata.
    effective_date:
        Extracted date when available; ``None`` if insufficient evidence.
    change_type:
        Classification of the edit.
    evidence_passage:
        Verbatim (or near-verbatim) demo excerpt supporting the finding.
    summary:
        Careful-language description for reviewers.
    confidence:
        Analyzer confidence; low for ambiguous / incomplete extractions.
    abstain:
        If True, no rule should be applied; expert interpretation needed.
    abstain_reason:
        Human-readable justification when abstaining.
    proposed_rule:
        Optional validated rule for machine-clear changes.
    """

    change_id: str
    document: str
    section: str
    effective_date: Optional[date] = None
    change_type: Literal["addition", "deletion", "revision", "ambiguous"]
    evidence_passage: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    abstain: bool = False
    abstain_reason: Optional[str] = None
    proposed_rule: Optional[PolicyRule] = None


ReviewDecision = Literal["approve", "reject", "request_expert_interpretation"]


class ReviewEvent(BaseModel):
    """Structured reviewer decision for audit serialization.

    Attributes
    ----------
    change_id:
        Which grounded change was reviewed.
    decision:
        Approve, reject, or request expert interpretation.
    reviewer_note:
        Optional free-text note (no PHI expected in this POC).
    timestamp:
        Decision time (UTC recommended at write time).
    rule_id:
        Associated rule if a proposal existed.
    """

    change_id: str
    decision: ReviewDecision
    reviewer_note: str = ""
    timestamp: datetime
    rule_id: Optional[str] = None
