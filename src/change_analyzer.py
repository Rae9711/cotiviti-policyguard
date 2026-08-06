"""Deterministic change analysis and declarative rule proposals.

Role in PolicyGuard
-------------------
Sits between raw difflib output and the Streamlit reviewer UI. Converts
line-level additions/deletions into :class:`~src.schema.SourceGroundedChange`
objects with document/section/effective-date/evidence metadata, and
proposes validated :class:`~src.schema.PolicyRule` JSON for machine-clear
changes.

Why deterministic (no API key)
------------------------------
The demo path recognizes known patterns in the synthetic CMS NCCI–style
excerpts (EXAMPLE1 effective-date revision; ambiguous "integral" language)
and builds Pydantic-validated rules without calling an LLM. An optional
LLM path may be added later as a non-required enhancement with cached
fallback; the main assessment demo must work offline.

Governance
----------
* Ambiguous language → ``abstain=True``; no rule is proposed for execution.
* Proposed rules use ``action="flag_for_review"`` only — never claim denial.
* Humans must Approve / Reject / Request Expert Interpretation before
  any claim-impact summary is treated as actionable.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable, List, Optional

from src.policy_diff import PolicyDiffResult, compare_policy_versions
from src.schema import PolicyRule, RuleCondition, SourceGroundedChange

# ISO date pattern used in demo policies and for extraction accuracy metrics.
_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

# Phrases that indicate insufficient specificity for automated rule building.
_AMBIGUOUS_MARKERS = (
    "generally considered integral",
    "ambiguous",
    "requires human review",
    "does not specify",
    "exhaustive list",
)

DEMO_SOURCE_DOCUMENT = "CMS NCCI Policy Manual Chapter XI (demo excerpt)"
DEMO_SOURCE_SECTION = "XI.D — Demo Procedure Reporting Guidance"


def extract_effective_dates(text: str) -> List[date]:
    """Extract ISO ``YYYY-MM-DD`` dates from a passage.

    Parameters
    ----------
    text:
        Policy passage or evidence string.

    Returns
    -------
    list[date]
        Parsed dates in appearance order (may be empty). Invalid calendar
        dates in the regex match set are skipped.

    Notes
    -----
    Used both for grounding changes and for evaluation of date-extraction
    accuracy against the gold set.
    """
    found: List[date] = []
    for match in _DATE_RE.findall(text):
        try:
            found.append(date.fromisoformat(match))
        except ValueError:
            continue
    return found


def _join_relevant_lines(lines: Iterable[str], keywords: tuple[str, ...]) -> str:
    """Join lines that contain any of the given keywords (case-insensitive).

    Parameters
    ----------
    lines:
        Candidate policy lines (typically additions or deletions).
    keywords:
        Substrings that mark relevance (e.g. ``EXAMPLE1``).

    Returns
    -------
    str
        Newline-joined matching lines, or empty string if none match.
    """
    matched = [
        line for line in lines if any(k.lower() in line.lower() for k in keywords)
    ]
    return "\n".join(matched)


def _is_ambiguous_passage(text: str) -> bool:
    """Return True if the passage contains known abstention markers.

    Safety: ambiguous passages must not produce executable rules.
    """
    lower = text.lower()
    return any(marker in lower for marker in _AMBIGUOUS_MARKERS)


def build_example1_rule(evidence: str, effective: date) -> PolicyRule:
    """Build the validated declarative rule for the EXAMPLE1 demo change.

    The rule flags EXAMPLE1 claims with date of service on or after the
    extracted effective date for human review. It does **not** deny payment.

    Parameters
    ----------
    evidence:
        Source passage supporting the rule (stored for auditability).
    effective:
        Effective date extracted from the policy text.

    Returns
    -------
    PolicyRule
        Pydantic-validated JSON-serializable rule (not executable Python).
    """
    return PolicyRule(
        rule_id="RULE-EXAMPLE1-DOS-2026",
        source_document=DEMO_SOURCE_DOCUMENT,
        source_section=DEMO_SOURCE_SECTION,
        effective_date=effective,
        change_type="revision",
        conditions=[
            RuleCondition(
                field="procedure_code",
                operator="equals",
                value="EXAMPLE1",
            ),
            RuleCondition(
                field="date_of_service",
                operator="on_or_after",
                value=effective.isoformat(),
            ),
        ],
        action="flag_for_review",
        evidence_text=evidence.strip()[:2000],
        requires_human_review=True,
        confidence=0.92,
    )


def analyze_policy_changes(
    old_text: str,
    new_text: str,
    *,
    diff: Optional[PolicyDiffResult] = None,
) -> List[SourceGroundedChange]:
    """Detect source-grounded material changes from two policy versions.

    Primary demo behaviors
    ----------------------
    1. **EXAMPLE1 effective-date revision** — machine-clear; proposes a
       validated ``PolicyRule`` with ``flag_for_review``.
    2. **Ambiguous integral-language addition** — abstains; requests expert
       interpretation; no rule proposed.

    Parameters
    ----------
    old_text, new_text:
        Full prior and newer policy texts.
    diff:
        Optional precomputed diff; if omitted, computed via
        :func:`~src.policy_diff.compare_policy_versions`.

    Returns
    -------
    list[SourceGroundedChange]
        Ordered list of grounded changes for the UI reviewer queue.
        May be empty if no patterned material changes are found.

    Edge cases
    ----------
    * If EXAMPLE1 date language is present but no ISO date parses, the
      change is returned with ``effective_date=None``, lower confidence,
      and no proposed rule (insufficient evidence).
    * Ambiguous changes always set ``abstain=True`` and ``proposed_rule=None``.
    """
    if diff is None:
        diff = compare_policy_versions(old_text, new_text)

    changes: List[SourceGroundedChange] = []
    additions = diff["additions"]
    deletions = diff["deletions"]

    # --- Change 1: EXAMPLE1 machine-actionable revision -------------------
    example1_add = _join_relevant_lines(
        additions, ("EXAMPLE1", "2026-01-01", "MACHINE-ACTIONABLE")
    )
    example1_del = _join_relevant_lines(deletions, ("EXAMPLE1",))
    if example1_add and (
        "2026-01-01" in example1_add
        or "flagged for additional" in example1_add.lower()
        or "machine-actionable" in example1_add.lower()
    ):
        evidence_parts = []
        if example1_del:
            evidence_parts.append(f"[Prior language]\n{example1_del}")
        evidence_parts.append(f"[New language]\n{example1_add}")
        evidence = "\n\n".join(evidence_parts)
        dates = extract_effective_dates(example1_add)
        effective = dates[0] if dates else None
        proposed: Optional[PolicyRule] = None
        confidence = 0.55
        abstain = False
        abstain_reason: Optional[str] = None
        summary = (
            "EXAMPLE1 reporting guidance revised with a date-of-service "
            "threshold; potentially material for claim review workflows."
        )
        if effective is not None:
            proposed = build_example1_rule(evidence, effective)
            confidence = 0.92
        else:
            abstain = True
            abstain_reason = (
                "Insufficient evidence: EXAMPLE1 change detected but no "
                "parseable effective date — requires expert validation."
            )
            confidence = 0.4

        changes.append(
            SourceGroundedChange(
                change_id="CHG-EXAMPLE1-EFFECTIVE-DATE",
                document=DEMO_SOURCE_DOCUMENT,
                section=DEMO_SOURCE_SECTION,
                effective_date=effective,
                change_type="revision",
                evidence_passage=evidence,
                summary=summary,
                confidence=confidence,
                abstain=abstain,
                abstain_reason=abstain_reason,
                proposed_rule=proposed,
            )
        )

    # --- Change 2: ambiguous integral language → abstain ------------------
    ambiguous_add = _join_relevant_lines(
        additions, ("integral", "AMBIGUOUS", "Related services")
    )
    if ambiguous_add and _is_ambiguous_passage(ambiguous_add):
        changes.append(
            SourceGroundedChange(
                change_id="CHG-EXAMPLE2-INTEGRAL-AMBIGUOUS",
                document=DEMO_SOURCE_DOCUMENT,
                section=DEMO_SOURCE_SECTION,
                effective_date=None,
                change_type="ambiguous",
                evidence_passage=ambiguous_add,
                summary=(
                    "New related-services language uses qualitative "
                    "'integral' wording without an exhaustive edit list — "
                    "insufficient evidence for a declarative rule."
                ),
                confidence=0.35,
                abstain=True,
                abstain_reason=(
                    "Ambiguous policy language: 'generally considered integral' "
                    "requires expert interpretation before any rule is proposed. "
                    "No automated action taken."
                ),
                proposed_rule=None,
            )
        )

    # --- Change 3: screening-language deletion (informational) ------------
    screening_del = _join_relevant_lines(deletions, ("screening",))
    if screening_del and not any(
        c.change_id == "CHG-EXAMPLE2-SCREENING-DELETE" for c in changes
    ):
        # Only surface if it is a distinct deletion not already covered.
        if "screening" in screening_del.lower():
            changes.append(
                SourceGroundedChange(
                    change_id="CHG-EXAMPLE2-SCREENING-DELETE",
                    document=DEMO_SOURCE_DOCUMENT,
                    section=DEMO_SOURCE_SECTION,
                    effective_date=None,
                    change_type="deletion",
                    evidence_passage=screening_del,
                    summary=(
                        "Prior EXAMPLE2 screening-purpose language removed "
                        "from the 2026 demo excerpt; flagged for review of "
                        "whether payer operational guidance changed."
                    ),
                    confidence=0.7,
                    abstain=False,
                    abstain_reason=None,
                    proposed_rule=None,  # informational — no claim predicate
                )
            )

    return changes


def propose_rules_from_changes(
    changes: List[SourceGroundedChange],
) -> List[PolicyRule]:
    """Collect non-abstaining proposed rules from analyzed changes.

    Parameters
    ----------
    changes:
        Output of :func:`analyze_policy_changes`.

    Returns
    -------
    list[PolicyRule]
        Rules that were proposed and are ready for human Approve/Reject.
        Abstaining changes contribute nothing.
    """
    rules: List[PolicyRule] = []
    for change in changes:
        if change.abstain or change.proposed_rule is None:
            continue
        rules.append(change.proposed_rule)
    return rules
