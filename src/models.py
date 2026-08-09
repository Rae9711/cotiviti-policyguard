"""Pydantic models for PolicyGuard v2 declarative rules and catalog records.

Role in PolicyGuard
-------------------
Every rule proposal and curated change must validate against these models
before reaching the deterministic interpreter or appearing as executable
JSON in the UI. This is the safety boundary that prevents free-form text
from becoming payment logic.

Key constraints
---------------
* Operators are a closed vocabulary (no arbitrary Python/SQL).
* Actions describe review recommendations only — never deny/reprice.
* Abstaining changes carry ``rule_template=None`` plus ``abstain_reason``.
* Audit payloads always include ``automatic_claim_action=False``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


Operator = Literal[
    "equals",
    "not_equals",
    "in",
    "not_in",
    "before",
    "on_or_after",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "not_contains",
    "outside_tolerance",
    "missing",
    "not_missing",
]

ClaimField = Literal[
    "claim_id",
    "beneficiary_id",
    "provider_id",
    "provider_specialty",
    "state",
    "date_of_service",
    "procedure_code",
    "modifier",
    "therapy_category",
    "cumulative_therapy_spend_ytd",
    "allowed_amount",
    "billed_amount",
    "paid_amount",
    "policy_mapping_status",
    "line_of_business",
    "place_of_service",
    "diagnosis_group",
    "documentation_score",
    "source_system",
]

ReviewDecision = Literal["approve", "reject", "escalate"]


class RuleCondition(BaseModel):
    """One atomic predicate evaluated by the deterministic rule engine."""

    field: ClaimField
    operator: Operator
    value: Optional[Union[str, float, int, list[Any]]] = None
    tolerance: Optional[float] = None

    @field_validator("tolerance")
    @classmethod
    def _tolerance_only_for_outside(cls, v: Optional[float], info) -> Optional[float]:
        return v


class PolicyRule(BaseModel):
    """Validated declarative rule — JSON interpreted, never executed as code."""

    rule_id: str
    name: str
    logic: Literal["AND", "OR"] = "AND"
    conditions: list[RuleCondition]
    action: str
    reason: str
    severity: Literal["low", "medium", "high"] = "medium"
    requires_human_review: bool = True


class PolicySource(BaseModel):
    """Official source metadata stored in the curated catalog."""

    source_id: str
    organization: str
    title: str
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    source_type: str
    url: str
    locator: str
    used_for: str


class PolicyChange(BaseModel):
    """Curated before/after policy change with optional rule proposal."""

    change_id: str
    title: str
    domain: str
    change_type: str
    old_version: str
    new_version: str
    effective_date: date
    old_snapshot: str
    new_snapshot: str
    summary: str
    source_ids: list[str]
    codes_added: list[str] = Field(default_factory=list)
    codes_removed: list[str] = Field(default_factory=list)
    numeric_before: Optional[float] = None
    numeric_after: Optional[float] = None
    unit: Optional[str] = None
    materiality_score: int = Field(ge=0, le=100)
    automation_readiness: int = Field(ge=0, le=100)
    risk_tier: Literal["Low", "Medium", "High"]
    evidence_quality: Literal["Low", "Medium", "High"]
    rule_template: Optional[PolicyRule] = None
    abstain_reason: Optional[str] = None

    @property
    def abstains(self) -> bool:
        return self.rule_template is None


class WorkspaceMeta(BaseModel):
    name: str
    description: str
    as_of: date
    governance_note: str


class PolicyCatalog(BaseModel):
    workspace: WorkspaceMeta
    sources: list[PolicySource]
    changes: list[PolicyChange]


class ReviewEvent(BaseModel):
    """Structured reviewer decision for audit serialization."""

    change_id: str
    decision: ReviewDecision
    reviewer_note: str = ""
    timestamp: datetime
    rule_id: Optional[str] = None
    source_verified: bool = False
    automatic_claim_action: bool = False
