"""Catalog validation, abstention, and audit-safety tests."""

from __future__ import annotations

from pathlib import Path

from src.audit import assert_no_automatic_claim_action, record_review_decision
from src.catalog import load_catalog
from src.demo_data import generate_claims, portfolio_flag_summary
from src.models import PolicyCatalog


def test_catalog_validates():
    catalog = load_catalog()
    assert isinstance(catalog, PolicyCatalog)
    assert len(catalog.sources) == 9
    assert len(catalog.changes) == 5


def test_abstention_has_no_rule():
    catalog = load_catalog()
    abstain = next(c for c in catalog.changes if c.change_id == "THERAPY-SKILLED-VS-FITNESS")
    assert abstain.rule_template is None
    assert abstain.abstain_reason


def test_audit_hardcodes_no_automatic_action(tmp_path: Path):
    path = tmp_path / "audit.jsonl"
    record_review_decision(
        change_id="THERAPY-KX-THRESHOLD-2026",
        decision="escalate",
        reviewer_note="Needs coding review",
        path=path,
    )
    assert assert_no_automatic_claim_action(path)


def test_synthetic_dataset_shape_and_flag_rate():
    df = generate_claims()
    assert len(df) == 604
    assert set(["DEMO-94662", "DEMO-KX", "DEMO-Q3014", "DEMO-RTM"]).issubset(set(df["claim_id"]))
    summary = portfolio_flag_summary(df)
    assert summary["claims_evaluated"] == 604
    assert summary["unique_claims_flagged"] == 55
    assert abs(summary["flag_rate"] - 0.091) < 0.005
    assert summary["by_change"]["NCCI-94662-RETIREMENT"] == 18
    assert summary["by_change"]["THERAPY-KX-THRESHOLD-2026"] == 22
    assert summary["by_change"]["TELEHEALTH-Q3014-FEE-2026"] == 10
    assert summary["by_change"]["THERAPY-RTM-CODES-2026"] == 5
    assert summary["providers_in_scope"] == 33
    assert summary["beneficiaries_in_scope"] == 51
    assert abs(summary["paid_amount_in_scope"] - 5627.13) < 0.02
