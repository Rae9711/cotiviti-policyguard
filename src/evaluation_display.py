"""Human-readable views of ``evaluation/results.json``.

The raw file is a software/fixture checklist for the deterministic demo.
Streamlit's ``st.json`` labels list items ``0``, ``1``, ``2``… which look
like mysterious scores — they are only array indices. This module names
cases and flag outcomes for the Governance panel.

These numbers are **not** production model accuracy on real claims.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# Fallback copy if an older results.json lacks ``meaning`` fields.
_RULE_MEANING = {
    ("NCCI-94662-RETIREMENT", "94662 post deletion"): (
        "After 2026-01-01, code 94662 should flag"
    ),
    ("NCCI-94662-RETIREMENT", "94662 prior year"): (
        "Before effective date, should not flag"
    ),
    ("THERAPY-KX-THRESHOLD-2026", "KX missing over threshold"): (
        "Over $2,480 without KX should flag"
    ),
    ("THERAPY-KX-THRESHOLD-2026", "KX present over threshold"): (
        "Over threshold with KX should not flag"
    ),
    ("TELEHEALTH-Q3014-FEE-2026", "Q3014 outside tolerance"): (
        "Fee drift beyond tolerance should flag"
    ),
    ("TELEHEALTH-Q3014-FEE-2026", "Q3014 within tolerance"): (
        "Small variance should not flag"
    ),
    ("THERAPY-RTM-CODES-2026", "RTM unmapped"): (
        "New RTM code unmapped should flag"
    ),
    ("THERAPY-RTM-CODES-2026", "RTM mapped"): "Mapped RTM should not flag",
}

_ENTITY_MEANING = {
    ("NCCI-94662-RETIREMENT", "January 1, 2026"): (
        "Effective date appears in the new policy snapshot"
    ),
    ("THERAPY-KX-THRESHOLD-2026", "$2,480"): "New KX dollar threshold added",
    ("THERAPY-KX-THRESHOLD-2026", "$2,410"): "Prior KX dollar threshold removed",
    ("TELEHEALTH-Q3014-FEE-2026", "$31.85"): "New Q3014 fee appears",
    ("TELEHEALTH-Q3014-FEE-2026", "$31.01"): "Prior Q3014 fee removed",
    ("THERAPY-RTM-CODES-2026", "98984"): "New RTM code 98984 appears",
}

_ABSTENTION_MEANING = {
    "no rule template": (
        "Clinical/fitness change has no claim-level rule template"
    ),
    "reason documented": "Abstention reason is documented for reviewers",
}

WHAT_THIS_IS = (
    "This is a **software/fixture checklist** that the deterministic demo still "
    "behaves as designed — **not** model accuracy on real claims. Eight synthetic "
    "claim cases (two per executable rule), six entity/date/dollar extractions, "
    "source provenance on all five curated changes, and two abstention assertions "
    "for the clinical/fitness scenario."
)


def flag_label(matched: bool) -> str:
    """``True`` means the claim matched the rule (flag for review)."""
    return "Flag for review" if matched else "No flag"


def pass_label(passed: bool) -> str:
    return "Pass" if passed else "Fail"


def metric_cards(payload: dict[str, Any]) -> list[tuple[str, str, str]]:
    """KPI triples: label, value, caption — never framed as production accuracy."""
    m = payload["metrics"]
    rule_p, rule_t = m["rule_assertions_passed"], m["rule_assertions_total"]
    ent_p, ent_t = m["entity_checks_passed"], m["entity_checks_total"]
    abs_p, abs_t = m["abstention_checks_passed"], m["abstention_checks_total"]
    coverage = m["source_coverage"]
    return [
        (
            "Rule assertions",
            f"{rule_p}/{rule_t}",
            "Eight handcrafted synthetic claim cases (2 per executable rule).",
        ),
        (
            "Entity checks",
            f"{ent_p}/{ent_t}",
            "Comparison engine found expected dates, dollars, and codes.",
        ),
        (
            "Source coverage",
            f"{coverage:.1f}",
            "All 5 curated changes have official source provenance.",
        ),
        (
            "Abstention checks",
            f"{abs_p}/{abs_t}",
            "Clinical/fitness change has no rule template + documented reason.",
        ),
    ]


def rule_checks_table(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for i, check in enumerate(payload.get("rule_checks", [])):
        change_id = check["change_id"]
        case = check["case"]
        meaning = check.get("meaning") or _RULE_MEANING.get((change_id, case), "")
        rows.append(
            {
                "Case": i,
                "Change": change_id,
                "Scenario": case,
                "Meaning": meaning,
                "Expected flag": flag_label(bool(check["expected"])),
                "Observed": flag_label(bool(check["observed"])),
                "Pass": pass_label(bool(check["passed"])),
            }
        )
    return pd.DataFrame(rows)


def entity_checks_table(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for i, check in enumerate(payload.get("entity_checks", [])):
        change_id = check["change_id"]
        entity = check["entity"]
        meaning = check.get("meaning") or _ENTITY_MEANING.get((change_id, entity), "")
        rows.append(
            {
                "Check": i,
                "Change": change_id,
                "Category": check["category"],
                "Entity": entity,
                "Direction": check["direction"],
                "Meaning": meaning,
                "Pass": pass_label(bool(check["passed"])),
            }
        )
    return pd.DataFrame(rows)


def abstention_checks_table(payload: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for i, check in enumerate(payload.get("abstention_checks", [])):
        name = check["check"]
        meaning = check.get("meaning") or _ABSTENTION_MEANING.get(name, "")
        rows.append(
            {
                "Check": i,
                "Assertion": name,
                "Meaning": meaning,
                "Pass": pass_label(bool(check["passed"])),
            }
        )
    return pd.DataFrame(rows)
