"""Compute PolicyGuard evaluation metrics against the demo gold set.

Purpose
-------
Produces honest POC-scale metrics for the assessment package:

* change-detection precision / recall (by change_id)
* effective-date extraction accuracy
* source-citation coverage
* rule-test pass rate on synthetic claims
* abstention correctness
* reviewer acceptance (from simulated decisions + optional audit fixture)

Outputs
-------
Writes ``evaluation/results.json`` and ``evaluation/results.md``.

Methodology honesty
-------------------
The gold set is tiny and hand-labeled for the demo excerpts only. Metrics
demonstrate evaluation *instrumentation*, not production performance.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.audit_log import count_decisions_by_type
from src.change_analyzer import analyze_policy_changes, build_example1_rule
from src.rule_engine import apply_rule

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EVAL_DIR = Path(__file__).resolve().parent
GOLD_PATH = EVAL_DIR / "gold_set.json"
RESULTS_JSON = EVAL_DIR / "results.json"
RESULTS_MD = EVAL_DIR / "results.md"
FIXTURE_AUDIT = DATA / "fixtures" / "sample_audit.jsonl"


def _load_gold() -> dict[str, Any]:
    """Load the manually labeled gold set JSON.

    Returns
    -------
    dict
        Parsed gold set with expected changes and rule-test expectations.
    """
    return json.loads(GOLD_PATH.read_text(encoding="utf-8"))


def _load_policies() -> tuple[str, str]:
    """Load demo 2025/2026 policy excerpts.

    Returns
    -------
    tuple[str, str]
        ``(old_text, new_text)``.
    """
    old = (DATA / "policy_2025.txt").read_text(encoding="utf-8")
    new = (DATA / "policy_2026.txt").read_text(encoding="utf-8")
    return old, new


def _safe_div(num: float, den: float) -> float | None:
    """Return ``num/den`` or ``None`` when the denominator is zero."""
    if den == 0:
        return None
    return num / den


def evaluate_change_detection(
    predicted_ids: set[str],
    gold_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute precision/recall for change detection by ``change_id``.

    Parameters
    ----------
    predicted_ids:
        Change IDs emitted by the analyzer.
    gold_changes:
        Gold-set expected change records (``should_detect`` true entries
        are treated as relevant).

    Returns
    -------
    dict
        Counts plus precision/recall/F1 (null if undefined).
    """
    relevant = {g["change_id"] for g in gold_changes if g.get("should_detect")}
    tp = len(predicted_ids & relevant)
    fp = len(predicted_ids - relevant)
    fn = len(relevant - predicted_ids)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted_ids": sorted(predicted_ids),
        "gold_ids": sorted(relevant),
    }


def evaluate_effective_dates(
    changes_by_id: dict[str, Any],
    gold_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score effective-date extraction where gold specifies a date.

    Parameters
    ----------
    changes_by_id:
        Mapping change_id → SourceGroundedChange (or object with
        ``effective_date``).
    gold_changes:
        Gold records; those with ``expected_effective_date`` are scored.

    Returns
    -------
    dict
        Accuracy and per-item detail.
    """
    scored = 0
    correct = 0
    details: list[dict[str, Any]] = []
    for g in gold_changes:
        expected = g.get("expected_effective_date")
        if expected is None and g.get("should_abstain"):
            # For abstaining ambiguous items, correct if predicted date is None
            cid = g["change_id"]
            pred = changes_by_id.get(cid)
            pred_date = (
                pred.effective_date.isoformat()
                if pred and pred.effective_date
                else None
            )
            scored += 1
            ok = pred_date is None
            correct += int(ok)
            details.append(
                {
                    "change_id": cid,
                    "expected": None,
                    "predicted": pred_date,
                    "correct": ok,
                }
            )
            continue
        if expected is None:
            continue
        cid = g["change_id"]
        pred = changes_by_id.get(cid)
        pred_date = (
            pred.effective_date.isoformat() if pred and pred.effective_date else None
        )
        scored += 1
        ok = pred_date == expected
        correct += int(ok)
        details.append(
            {
                "change_id": cid,
                "expected": expected,
                "predicted": pred_date,
                "correct": ok,
            }
        )
    return {
        "scored": scored,
        "correct": correct,
        "accuracy": _safe_div(correct, scored),
        "details": details,
    }


def evaluate_source_citation(
    changes_by_id: dict[str, Any],
    gold_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure whether detected changes include non-empty evidence + source fields.

    Parameters
    ----------
    changes_by_id:
        Predicted grounded changes keyed by id.
    gold_changes:
        Gold entries with ``requires_source_citation``.

    Returns
    -------
    dict
        Coverage rate among gold items that require citation.
    """
    required = [g for g in gold_changes if g.get("requires_source_citation")]
    covered = 0
    details: list[dict[str, Any]] = []
    for g in required:
        cid = g["change_id"]
        pred = changes_by_id.get(cid)
        ok = bool(
            pred
            and pred.evidence_passage.strip()
            and pred.document.strip()
            and pred.section.strip()
        )
        covered += int(ok)
        details.append({"change_id": cid, "cited": ok})
    return {
        "required": len(required),
        "covered": covered,
        "coverage": _safe_div(covered, len(required)),
        "details": details,
    }


def evaluate_abstention(
    changes_by_id: dict[str, Any],
    gold_changes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Check abstention / rule-proposal flags against gold labels.

    Correct when:
    * gold ``should_abstain`` matches predicted ``abstain``
    * gold ``should_propose_rule`` matches presence of ``proposed_rule``

    Returns
    -------
    dict
        Accuracy over gold change rows.
    """
    scored = 0
    correct = 0
    details: list[dict[str, Any]] = []
    for g in gold_changes:
        cid = g["change_id"]
        pred = changes_by_id.get(cid)
        if pred is None:
            details.append({"change_id": cid, "correct": False, "reason": "missing"})
            scored += 1
            continue
        abstain_ok = bool(pred.abstain) == bool(g.get("should_abstain"))
        propose_ok = (pred.proposed_rule is not None) == bool(
            g.get("should_propose_rule")
        )
        ok = abstain_ok and propose_ok
        scored += 1
        correct += int(ok)
        details.append(
            {
                "change_id": cid,
                "abstain_ok": abstain_ok,
                "propose_ok": propose_ok,
                "correct": ok,
            }
        )
    return {
        "scored": scored,
        "correct": correct,
        "accuracy": _safe_div(correct, scored),
        "details": details,
    }


def evaluate_rule_tests(gold: dict[str, Any]) -> dict[str, Any]:
    """Run the EXAMPLE1 rule on synthetic claims and score against gold IDs.

    Parameters
    ----------
    gold:
        Full gold set including ``rule_test_expectations``.

    Returns
    -------
    dict
        Pass rate and mismatch lists.
    """
    exp = gold["rule_test_expectations"]
    claims = pd.read_csv(DATA / "synthetic_claims.csv", comment="#")
    rule = build_example1_rule(
        evidence="evaluation fixture evidence",
        effective=date(2026, 1, 1),
    )
    result = apply_rule(claims, rule)
    flagged = set(
        result.loc[result["rule_action"] == "flag_for_review", "claim_id"].astype(str)
    )
    expected = set(exp["flagged_claim_ids"])
    not_flagged = set(exp["not_flagged_examples"])
    missing = sorted(expected - flagged)
    unexpected = sorted(flagged - expected)
    # also ensure example non-flagged are not flagged
    wrongly_flagged_examples = sorted(not_flagged & flagged)
    total_checks = len(expected) + len(not_flagged)
    passed_checks = (
        len(expected) - len(missing) + len(not_flagged) - len(wrongly_flagged_examples)
    )
    return {
        "expected_flagged_count": len(expected),
        "actual_flagged_count": len(flagged),
        "missing_flagged": missing,
        "unexpected_flagged": unexpected,
        "wrongly_flagged_examples": wrongly_flagged_examples,
        "pass_rate": _safe_div(passed_checks, total_checks),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
    }


def evaluate_reviewer_acceptance(gold: dict[str, Any]) -> dict[str, Any]:
    """Compare simulated reviewer decisions to fixture audit log (if present).

    Also reports the gold simulated decision distribution as the primary
    acceptance proxy for this POC.

    Returns
    -------
    dict
        Simulated rates plus fixture counts when available.
    """
    simulated = gold["simulated_reviewer_decisions"]
    total = len(simulated)
    approve = sum(1 for d in simulated if d["decision"] == "approve")
    reject = sum(1 for d in simulated if d["decision"] == "reject")
    expert = sum(
        1 for d in simulated if d["decision"] == "request_expert_interpretation"
    )
    fixture_counts = (
        count_decisions_by_type(FIXTURE_AUDIT) if FIXTURE_AUDIT.exists() else {}
    )
    return {
        "simulated_total": total,
        "simulated_approve_rate": _safe_div(approve, total),
        "simulated_reject_rate": _safe_div(reject, total),
        "simulated_expert_rate": _safe_div(expert, total),
        "simulated_decisions": simulated,
        "fixture_audit_counts": fixture_counts,
        "note": (
            "Reviewer acceptance is simulated from gold labels for the demo; "
            "fixture audit counts are illustrative of log schema only."
        ),
    }


def _fmt_pct(value: float | None) -> str:
    """Format a ratio as a percentage string for Markdown tables."""
    if value is None:
        return "n/a"
    return f"{100.0 * value:.1f}%"


def write_results_markdown(results: dict[str, Any], path: Path) -> None:
    """Write a human-readable metrics report.

    Parameters
    ----------
    results:
        Full metrics dictionary from :func:`run_evaluation`.
    path:
        Destination Markdown path.
    """
    cd = results["change_detection"]
    ed = results["effective_date_extraction"]
    sc = results["source_citation"]
    ab = results["abstention"]
    rt = results["rule_tests"]
    ra = results["reviewer_acceptance"]
    lines = [
        "# PolicyGuard Evaluation Results",
        "",
        "> **Methodology:** Manually labeled gold set over the synthetic demo",
        "> policy excerpts only (n = "
        f"{len(results['gold_change_ids'])}"
        "). Metrics demonstrate evaluation instrumentation for the internship",
        "> assessment POC. They are **not** claims of production performance.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Change-detection precision | {_fmt_pct(cd['precision'])} |",
        f"| Change-detection recall | {_fmt_pct(cd['recall'])} |",
        f"| Change-detection F1 | {_fmt_pct(cd['f1'])} |",
        f"| Effective-date extraction accuracy | {_fmt_pct(ed['accuracy'])} |",
        f"| Source-citation coverage | {_fmt_pct(sc['coverage'])} |",
        f"| Abstention / proposal correctness | {_fmt_pct(ab['accuracy'])} |",
        f"| Rule-test pass rate | {_fmt_pct(rt['pass_rate'])} |",
        f"| Simulated approve rate | {_fmt_pct(ra['simulated_approve_rate'])} |",
        f"| Simulated expert-interpretation rate | {_fmt_pct(ra['simulated_expert_rate'])} |",
        "",
        "## Notes",
        "",
        results["methodology_note"],
        "",
        f"Generated artifacts: `{RESULTS_JSON.name}`, `{RESULTS_MD.name}`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_evaluation() -> dict[str, Any]:
    """Execute the full evaluation suite and persist JSON + Markdown results.

    Returns
    -------
    dict
        Complete metrics payload (also written to disk).
    """
    gold = _load_gold()
    old_text, new_text = _load_policies()
    changes = analyze_policy_changes(old_text, new_text)
    by_id = {c.change_id: c for c in changes}
    predicted_ids = set(by_id)

    results: dict[str, Any] = {
        "methodology_note": gold.get("methodology_note", ""),
        "gold_change_ids": [g["change_id"] for g in gold["expected_changes"]],
        "change_detection": evaluate_change_detection(
            predicted_ids, gold["expected_changes"]
        ),
        "effective_date_extraction": evaluate_effective_dates(
            by_id, gold["expected_changes"]
        ),
        "source_citation": evaluate_source_citation(
            by_id, gold["expected_changes"]
        ),
        "abstention": evaluate_abstention(by_id, gold["expected_changes"]),
        "rule_tests": evaluate_rule_tests(gold),
        "reviewer_acceptance": evaluate_reviewer_acceptance(gold),
    }

    RESULTS_JSON.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    write_results_markdown(results, RESULTS_MD)
    return results


if __name__ == "__main__":
    out = run_evaluation()
    print(json.dumps({k: out[k] for k in out if k != "methodology_note"}, indent=2))
    print(f"\nWrote {RESULTS_JSON} and {RESULTS_MD}")
