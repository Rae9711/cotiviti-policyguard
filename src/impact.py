"""Portfolio-level claim impact analytics for PolicyGuard v2.

Role in PolicyGuard
-------------------
Aggregates deterministic rule dry-runs into executive KPIs, time trends,
provider concentration, fee-variance distributions, and a prioritized
reviewer queue. All monetary figures are labeled "paid amount in scope"
and must never be presented as overpayment, recovery, or savings.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.catalog import executable_rules, load_catalog
from src.models import PolicyCatalog, PolicyChange, PolicyRule
from src.rule_engine import apply_rule


PRIORITY_WEIGHTS = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}


def run_portfolio(claims: pd.DataFrame) -> dict[str, Any]:
    """Execute all executable catalog rules and return analytics bundles."""
    load_catalog()
    event_frames: list[pd.DataFrame] = []
    per_change: list[dict[str, Any]] = []

    for change, rule in executable_rules():
        result = apply_rule(claims, rule)
        matched = result.loc[result["rule_matched"]].copy()
        matched["change_id"] = change.change_id
        matched["change_title"] = change.title
        matched["rule_id"] = rule.rule_id
        matched["severity"] = rule.severity
        matched["action"] = rule.action
        matched["domain"] = change.domain
        event_frames.append(matched)
        paid = float(matched["paid_amount"].sum()) if len(matched) else 0.0
        per_change.append(
            {
                "change_id": change.change_id,
                "title": change.title,
                "short_label": _short_label(change),
                "flagged_claims": int(len(matched)),
                "providers": int(matched["provider_id"].nunique()) if len(matched) else 0,
                "paid_amount_in_scope": round(paid, 2),
                "materiality_score": change.materiality_score,
                "automation_readiness": change.automation_readiness,
                "risk_tier": change.risk_tier,
                "severity": rule.severity,
            }
        )

    events = (
        pd.concat(event_frames, ignore_index=True)
        if event_frames
        else claims.iloc[0:0].copy()
    )
    unique_ids = set(events["claim_id"].astype(str)) if len(events) else set()
    unique = claims[claims["claim_id"].astype(str).isin(unique_ids)].copy()

    kpis = {
        "claims_evaluated": int(len(claims)),
        "unique_claims_flagged": int(len(unique_ids)),
        "review_events": int(len(events)),
        "providers_in_scope": int(unique["provider_id"].nunique()) if len(unique) else 0,
        "beneficiaries_in_scope": int(unique["beneficiary_id"].nunique()) if len(unique) else 0,
        "paid_amount_in_scope": round(float(unique["paid_amount"].sum()), 2) if len(unique) else 0.0,
        "flag_rate": round(len(unique_ids) / len(claims), 4) if len(claims) else 0.0,
    }

    return {
        "kpis": kpis,
        "per_change": per_change,
        "events": events,
        "unique_claims": unique,
        "monthly_trend": _monthly_trend(events),
        "provider_concentration": _provider_concentration(events),
        "q3014_distribution": _q3014_distribution(claims),
        "queue": build_review_queue(events),
        "opportunity_matrix": _opportunity_matrix(),
    }


def review_burden_metrics(
    portfolio: dict[str, Any],
    *,
    catalog: PolicyCatalog | None = None,
    selected_change_id: str | None = None,
) -> dict[str, Any]:
    """Compare HITL rule-level review to naive all-claim screening.

    All rates are synthetic-pack ratios (flagged / evaluated, policy
    decisions / claims). They are not production labor savings, FTE
    reduction, fraud, recovery, or payment-accuracy lifts.
    """
    cat = catalog or load_catalog()
    kpis = portfolio["kpis"]
    claims_evaluated = int(kpis["claims_evaluated"])
    unique_flagged = int(kpis["unique_claims_flagged"])
    executable = sum(1 for change in cat.changes if not change.abstains)
    abstentions = sum(1 for change in cat.changes if change.abstains)
    curated = len(cat.changes)
    policy_decisions = executable + abstentions

    concentration = (unique_flagged / claims_evaluated) if claims_evaluated else 0.0
    not_flagged_rate = (1.0 - concentration) if claims_evaluated else 0.0
    compression = (
        1.0 - (policy_decisions / claims_evaluated) if claims_evaluated else 0.0
    )
    flagged_per_gate = (unique_flagged / executable) if executable else None
    gates_per_100_flagged = (
        (executable / unique_flagged) * 100.0 if unique_flagged else None
    )
    abstention_share = (abstentions / curated) if curated else 0.0

    selected: dict[str, Any] | None = None
    if selected_change_id:
        by_id = {row["change_id"]: row for row in portfolio.get("per_change", [])}
        change = next((c for c in cat.changes if c.change_id == selected_change_id), None)
        if change is not None:
            row = by_id.get(selected_change_id)
            selected = {
                "change_id": selected_change_id,
                "title": change.title,
                "short_label": _short_label(change),
                "abstains": change.abstains,
                "flagged_claims": (
                    0 if change.abstains else int(row["flagged_claims"]) if row else 0
                ),
            }

    return {
        "claims_evaluated": claims_evaluated,
        "unique_claims_flagged": unique_flagged,
        "executable_proposals": executable,
        "abstentions": abstentions,
        "curated_changes": curated,
        "policy_decisions": policy_decisions,
        "review_concentration": concentration,
        "not_flagged_rate": not_flagged_rate,
        "decision_compression": compression,
        "flagged_per_executable_decision": flagged_per_gate,
        "gates_per_100_flagged": gates_per_100_flagged,
        "abstention_share": abstention_share,
        "selected": selected,
    }


def _short_label(change: PolicyChange) -> str:
    mapping = {
        "NCCI-94662-RETIREMENT": "94662 retirement",
        "THERAPY-KX-THRESHOLD-2026": "Therapy KX threshold",
        "TELEHEALTH-Q3014-FEE-2026": "Q3014 fee update",
        "THERAPY-RTM-CODES-2026": "RTM code mapping",
        "THERAPY-SKILLED-VS-FITNESS": "Skilled vs fitness",
    }
    return mapping.get(change.change_id, change.title[:28])


def _monthly_trend(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["month", "review_events", "paid_amount_in_scope"])
    frame = events.copy()
    frame["month"] = pd.to_datetime(frame["date_of_service"]).dt.to_period("M").astype(str)
    grouped = (
        frame.groupby("month", as_index=False)
        .agg(review_events=("claim_id", "count"), paid_amount_in_scope=("paid_amount", "sum"))
        .sort_values("month")
    )
    grouped["paid_amount_in_scope"] = grouped["paid_amount_in_scope"].round(2)
    return grouped


def _provider_concentration(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(
            columns=["provider_id", "review_events", "paid_amount_in_scope", "changes"]
        )
    grouped = (
        events.groupby("provider_id", as_index=False)
        .agg(
            review_events=("claim_id", "count"),
            paid_amount_in_scope=("paid_amount", "sum"),
            changes=("change_id", "nunique"),
            specialty=("provider_specialty", "first"),
        )
        .sort_values("review_events", ascending=False)
    )
    grouped["paid_amount_in_scope"] = grouped["paid_amount_in_scope"].round(2)
    return grouped


def _q3014_distribution(claims: pd.DataFrame) -> pd.DataFrame:
    subset = claims[
        (claims["procedure_code"].astype(str) == "Q3014")
        & (pd.to_datetime(claims["date_of_service"]) >= "2026-01-01")
    ].copy()
    if subset.empty:
        return subset
    subset["fee_delta"] = (subset["allowed_amount"].astype(float) - 31.85).round(2)
    subset["outside_tolerance"] = subset["fee_delta"].abs() > 0.5
    return subset[
        [
            "claim_id",
            "provider_id",
            "date_of_service",
            "allowed_amount",
            "fee_delta",
            "outside_tolerance",
            "paid_amount",
        ]
    ]


def build_review_queue(events: pd.DataFrame) -> pd.DataFrame:
    """Prioritize review events by severity, paid amount, and documentation risk."""
    if events.empty:
        return pd.DataFrame()
    queue = events.copy()
    queue["severity_weight"] = queue["severity"].map(PRIORITY_WEIGHTS).fillna(1.0)
    queue["doc_risk"] = 1.0 - queue["documentation_score"].astype(float).clip(0, 1)
    queue["priority_score"] = (
        queue["severity_weight"] * 40
        + queue["paid_amount"].astype(float).clip(0, 500) / 5
        + queue["doc_risk"] * 25
    ).round(2)
    queue = queue.sort_values("priority_score", ascending=False)
    cols = [
        "priority_score",
        "claim_id",
        "change_title",
        "rule_id",
        "action",
        "severity",
        "provider_id",
        "date_of_service",
        "procedure_code",
        "modifier",
        "paid_amount",
        "documentation_score",
        "policy_mapping_status",
    ]
    existing = [c for c in cols if c in queue.columns]
    return queue[existing].reset_index(drop=True)


def _opportunity_matrix() -> pd.DataFrame:
    """Materiality × automation readiness for all curated changes (incl. abstain)."""
    catalog = load_catalog()
    rows = []
    for change in catalog.changes:
        rows.append(
            {
                "change_id": change.change_id,
                "title": change.title,
                "short_label": _short_label(change),
                "materiality_score": change.materiality_score,
                "automation_readiness": change.automation_readiness,
                "risk_tier": change.risk_tier,
                "abstains": change.abstains,
                "bubble_label": "ABSTAIN" if change.abstains else _matrix_code(change.change_id),
            }
        )
    return pd.DataFrame(rows)


def _matrix_code(change_id: str) -> str:
    return {
        "NCCI-94662-RETIREMENT": "NCCI",
        "THERAPY-KX-THRESHOLD-2026": "KX",
        "TELEHEALTH-Q3014-FEE-2026": "Q3014",
        "THERAPY-RTM-CODES-2026": "RTM",
        "THERAPY-SKILLED-VS-FITNESS": "ABSTAIN",
    }.get(change_id, change_id[:8])


def dry_run_rule(claims: pd.DataFrame, rule: PolicyRule) -> dict[str, Any]:
    """Dry-run a single rule and return matched sample + summary."""
    result = apply_rule(claims, rule)
    matched = result.loc[result["rule_matched"]].copy()
    sample_cols = [
        c
        for c in [
            "claim_id",
            "date_of_service",
            "procedure_code",
            "modifier",
            "therapy_category",
            "cumulative_therapy_spend_ytd",
            "allowed_amount",
            "policy_mapping_status",
            "provider_id",
            "paid_amount",
        ]
        if c in matched.columns
    ]
    return {
        "matched_count": int(len(matched)),
        "sample": matched[sample_cols].head(12),
        "result": result,
    }
