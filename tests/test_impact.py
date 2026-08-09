"""Portfolio impact and synthetic review-burden metric tests."""

from __future__ import annotations

from src.demo_data import load_claims
from src.impact import review_burden_metrics, run_portfolio


def test_review_burden_metrics_default_portfolio():
    portfolio = run_portfolio(load_claims())
    metrics = review_burden_metrics(
        portfolio, selected_change_id="THERAPY-KX-THRESHOLD-2026"
    )

    claims = metrics["claims_evaluated"]
    flagged = metrics["unique_claims_flagged"]
    assert claims == 604
    assert flagged == 55
    assert metrics["executable_proposals"] == 4
    assert metrics["abstentions"] == 1
    assert metrics["curated_changes"] == 5
    assert metrics["policy_decisions"] == 5

    assert abs(metrics["review_concentration"] - flagged / claims) < 1e-12
    assert abs(metrics["not_flagged_rate"] - (1 - flagged / claims)) < 1e-12
    assert abs(metrics["decision_compression"] - (1 - 5 / claims)) < 1e-12
    assert abs(metrics["flagged_per_executable_decision"] - flagged / 4) < 1e-12
    assert abs(metrics["gates_per_100_flagged"] - (4 / flagged) * 100) < 1e-12
    assert abs(metrics["abstention_share"] - 0.2) < 1e-12

    # Display rounding used on Claim Impact (default KX focus).
    assert f"{metrics['review_concentration'] * 100:.1f}%" == "9.1%"
    assert f"{metrics['not_flagged_rate'] * 100:.1f}%" == "90.9%"
    assert f"{metrics['decision_compression'] * 100:.1f}%" == "99.2%"
    assert f"{metrics['flagged_per_executable_decision']:.1f}" == "13.8"
    assert f"{metrics['gates_per_100_flagged']:.1f}" == "7.3"
    assert f"{metrics['abstention_share'] * 100:.0f}%" == "20%"

    selected = metrics["selected"]
    assert selected is not None
    assert selected["abstains"] is False
    assert selected["flagged_claims"] == 22


def test_review_burden_selected_abstention_has_zero_queue():
    portfolio = run_portfolio(load_claims())
    metrics = review_burden_metrics(
        portfolio, selected_change_id="THERAPY-SKILLED-VS-FITNESS"
    )
    selected = metrics["selected"]
    assert selected is not None
    assert selected["abstains"] is True
    assert selected["flagged_claims"] == 0


def test_review_burden_per_change_volumes():
    portfolio = run_portfolio(load_claims())
    by_id = {row["change_id"]: row["flagged_claims"] for row in portfolio["per_change"]}
    assert by_id["THERAPY-KX-THRESHOLD-2026"] == 22
    assert by_id["NCCI-94662-RETIREMENT"] == 18
    assert by_id["TELEHEALTH-Q3014-FEE-2026"] == 10
    assert by_id["THERAPY-RTM-CODES-2026"] == 5
