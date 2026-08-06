"""PolicyGuard Intelligence Studio — Streamlit application (v2).

Five focused workspaces
-----------------------
1. Executive Overview — portfolio materiality and exposure
2. Policy Intelligence — source-grounded before/after comparison
3. Rule Studio — validated declarative rules and dry runs
4. Claim Impact — trends, concentration, prioritized queue
5. Governance — approve / reject / escalate with audit export

Safety
------
This application never denies, reprices, or adjudicates claims. Every
rule output is a review recommendation. Audit events hard-code
``automatic_claim_action: false``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.audit import audit_events_jsonl, read_audit_events, record_review_decision
from src.catalog import get_change, get_sources_for_change, load_catalog
from src.demo_data import load_claims
from src.impact import dry_run_rule, run_portfolio
from src.semantic_diff import compare_texts, extract_text_from_upload
from src.ui import (
    inject_styles,
    kpi_row,
    monthly_trend_fig,
    opportunity_matrix_fig,
    provider_bubble_fig,
    q3014_hist_fig,
    render_hero,
    source_card,
    volume_bar_fig,
)

ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "data" / "audit_log.jsonl"
EVAL_RESULTS = ROOT / "evaluation" / "results.json"


def _init_state() -> None:
    if "selected_change_id" not in st.session_state:
        st.session_state.selected_change_id = "THERAPY-KX-THRESHOLD-2026"


def _sidebar(catalog, claims: pd.DataFrame) -> str:
    with st.sidebar:
        st.markdown("### PG  PolicyGuard")
        st.caption("CMS payment-policy intelligence pack")
        st.caption("Assessment build · v2.0")
        st.divider()
        st.markdown("**Workspace**")
        st.write(catalog.workspace.name)
        titles = {c.change_id: c.title for c in catalog.changes}
        selected = st.selectbox(
            "Focus change",
            options=list(titles.keys()),
            format_func=lambda cid: titles[cid],
            index=list(titles.keys()).index(st.session_state.selected_change_id)
            if st.session_state.selected_change_id in titles
            else 0,
        )
        st.session_state.selected_change_id = selected
        st.divider()
        st.metric("Synthetic claims", f"{len(claims):,}")
        st.caption("No PHI · deterministic seed")
        st.markdown(
            '<p><span class="pg-status-dot"></span><strong>Review recommendation only</strong></p>',
            unsafe_allow_html=True,
        )
        st.caption("Does not perform autonomous claim denial.")
    return selected


def page_executive(catalog, portfolio: dict) -> None:
    st.subheader("Executive signal")
    st.caption("Policy materiality, automation readiness, and synthetic operational exposure.")
    k = portfolio["kpis"]
    executable = sum(1 for c in catalog.changes if not c.abstains)
    abstentions = sum(1 for c in catalog.changes if c.abstains)
    kpi_row(
        [
            ("Official Sources", str(len(catalog.sources))),
            ("Curated Changes", str(len(catalog.changes))),
            ("Executable Proposals", str(executable)),
            ("Required Abstentions", str(abstentions)),
            ("Synthetic Flag Rate", f"{k['flag_rate'] * 100:.1f}%"),
        ]
    )
    st.write("")
    left, right = st.columns(2)
    with left:
        st.markdown("**Policy opportunity matrix**")
        st.plotly_chart(
            opportunity_matrix_fig(portfolio["opportunity_matrix"]),
            use_container_width=True,
        )
    with right:
        st.markdown("**Synthetic review volume by change**")
        st.plotly_chart(volume_bar_fig(portfolio["per_change"]), use_container_width=True)
    st.caption(
        "Paid amount in scope is a synthetic aggregation for demonstration only — "
        "not an overpayment, recovery, or savings estimate."
    )


def page_policy_intelligence(catalog, change_id: str) -> None:
    change = get_change(change_id, catalog)
    st.subheader("Policy intelligence")
    st.caption("Source-grounded before/after comparison with entity extraction.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Materiality", change.materiality_score)
    c2.metric("Automation readiness", change.automation_readiness)
    c3.metric("Risk tier", change.risk_tier)
    c4.metric("Evidence quality", change.evidence_quality)

    comparison = compare_texts(change.old_snapshot, change.new_snapshot)
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Before — {html.escape(change.old_version)}**")
        st.markdown(
            f'<div class="pg-card">{comparison.old_highlighted_html}</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(f"**After — {html.escape(change.new_version)}**")
        st.markdown(
            f'<div class="pg-card">{comparison.new_highlighted_html}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**Semantic similarity:** `{comparison.similarity:.2%}`")
    st.write(change.summary)

    deltas = [d for d in comparison.entity_deltas if d.direction != "shared"]
    if deltas:
        st.markdown("**Extracted entity deltas**")
        st.dataframe(
            pd.DataFrame([d.__dict__ for d in deltas]),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("**Official source evidence**")
    for source in get_sources_for_change(change, catalog):
        source_card(source)

    st.download_button(
        "Download comparison JSON",
        data=json.dumps(comparison.to_dict(), indent=2),
        file_name=f"{change.change_id}_comparison.json",
        mime="application/json",
    )

    with st.expander("Compare local TXT/PDF uploads (in memory)"):
        u1, u2 = st.columns(2)
        old_file = u1.file_uploader("Prior version", type=["txt", "pdf"], key="old_up")
        new_file = u2.file_uploader("New version", type=["txt", "pdf"], key="new_up")
        if old_file and new_file:
            old_txt = extract_text_from_upload(old_file.name, old_file.getvalue())
            new_txt = extract_text_from_upload(new_file.name, new_file.getvalue())
            local = compare_texts(old_txt, new_txt)
            st.metric("Local similarity", f"{local.similarity:.2%}")
            a, b = st.columns(2)
            a.markdown(local.old_highlighted_html, unsafe_allow_html=True)
            b.markdown(local.new_highlighted_html, unsafe_allow_html=True)


def page_rule_studio(catalog, claims: pd.DataFrame, change_id: str) -> None:
    change = get_change(change_id, catalog)
    st.subheader("Rule studio")
    st.caption("Pydantic-validated declarative rules — interpreted, never executed as code.")

    if change.abstains or change.rule_template is None:
        st.warning("System abstention: clinical documentation and expert interpretation required")
        st.info(change.abstain_reason or "No claim-level rule can be generated from structured fields alone.")
        st.json(
            {
                "change_id": change.change_id,
                "rule_template": None,
                "abstain_reason": change.abstain_reason,
            }
        )
        return

    rule = change.rule_template
    st.markdown(f"**{rule.name}** · `{rule.rule_id}`")
    st.write(rule.reason)
    conditions = pd.DataFrame(
        [
            {
                "field": c.field,
                "operator": c.operator,
                "value": c.value,
                "tolerance": c.tolerance,
            }
            for c in rule.conditions
        ]
    )
    st.dataframe(conditions, use_container_width=True, hide_index=True)

    rule_json = rule.model_dump()
    st.download_button(
        "Download rule JSON",
        data=json.dumps(rule_json, indent=2, default=str),
        file_name=f"{rule.rule_id}.json",
        mime="application/json",
    )

    with st.expander("Validated rule JSON", expanded=False):
        st.json(rule_json)

    dry = dry_run_rule(claims, rule)
    st.metric("Dry-run matches", dry["matched_count"])
    st.caption("Deterministic interpreter only — no generated Python/SQL is executed.")
    if dry["matched_count"]:
        st.dataframe(dry["sample"], use_container_width=True, hide_index=True)


def page_claim_impact(portfolio: dict) -> None:
    st.subheader("Claim impact")
    st.caption("Synthetic operational exposure for human review prioritization.")
    k = portfolio["kpis"]
    kpi_row(
        [
            ("Claims evaluated", f"{k['claims_evaluated']:,}"),
            ("Unique claims routed", f"{k['unique_claims_flagged']:,}"),
            ("Review events", f"{k['review_events']:,}"),
            ("Providers in scope", f"{k['providers_in_scope']:,}"),
            ("Paid amount in scope", f"${k['paid_amount_in_scope']:,.2f}"),
        ]
    )
    st.caption(
        f"Flag rate {k['flag_rate'] * 100:.1f}%. "
        "Paid amount in scope is not an overpayment, recovery, or savings figure."
    )

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("**Monthly review-event trend**")
        st.plotly_chart(monthly_trend_fig(portfolio["monthly_trend"]), use_container_width=True)
    with t2:
        st.markdown("**Policy-level review volume**")
        st.plotly_chart(volume_bar_fig(portfolio["per_change"]), use_container_width=True)

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**Provider concentration**")
        st.plotly_chart(
            provider_bubble_fig(portfolio["provider_concentration"]),
            use_container_width=True,
        )
    with p2:
        st.markdown("**Q3014 fee-variance distribution**")
        st.plotly_chart(q3014_hist_fig(portfolio["q3014_distribution"]), use_container_width=True)

    st.markdown("**Prioritized reviewer queue**")
    queue = portfolio["queue"]
    st.dataframe(queue.head(40), use_container_width=True, hide_index=True)
    st.download_button(
        "Download reviewer queue CSV",
        data=queue.to_csv(index=False),
        file_name="reviewer_queue.csv",
        mime="text/csv",
    )


def page_governance(catalog, change_id: str) -> None:
    change = get_change(change_id, catalog)
    st.subheader("Governance")
    st.caption("Human approval with Cotiviti/NIST-inspired controls and exportable audit.")

    st.markdown(
        """
        | Control theme | How PolicyGuard operationalizes it |
        |---|---|
        | Accuracy | Source locators, schema validation, deterministic rules |
        | Transparency | Before/after evidence, downloadable JSON, careful metrics language |
        | Security | Local offline core; no PHI; uploads stay in memory |
        | Accountability | Approve / reject / escalate with JSONL audit |
        | NIST Govern/Map/Measure/Manage | Catalog provenance, risk tiers, evaluation harness, human gate |
        """
    )

    if change.abstains:
        st.warning("Selected change abstains from claim-level automation.")
        st.write(change.abstain_reason)

    with st.form("governance_form"):
        decision = st.radio(
            "Reviewer decision",
            options=["approve", "reject", "escalate"],
            format_func=lambda d: {
                "approve": "Approve for controlled testing",
                "reject": "Reject proposal",
                "escalate": "Escalate to policy / coding / clinical expert",
            }[d],
            horizontal=True,
        )
        note = st.text_area("Rationale", placeholder="Document why this decision is appropriate.")
        verified = st.checkbox("I verified the official source locator(s)", value=False)
        submitted = st.form_submit_button("Record decision")

    if submitted:
        rule_id = change.rule_template.rule_id if change.rule_template else None
        record = record_review_decision(
            change_id=change.change_id,
            decision=decision,  # type: ignore[arg-type]
            reviewer_note=note,
            rule_id=rule_id,
            source_verified=verified,
            path=AUDIT_PATH,
        )
        st.success(
            f"Recorded `{decision}` with automatic_claim_action="
            f"{record['payload']['automatic_claim_action']}"
        )

    events = read_audit_events(AUDIT_PATH)
    st.markdown("**Audit trail**")
    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet. Record a decision to populate the trail.")

    st.download_button(
        "Download audit JSONL",
        data=audit_events_jsonl(AUDIT_PATH) or "",
        file_name="policyguard_audit.jsonl",
        mime="application/jsonl",
    )

    if EVAL_RESULTS.exists():
        with st.expander("Synthetic evaluation results"):
            st.json(json.loads(EVAL_RESULTS.read_text(encoding="utf-8")))

    st.caption(catalog.workspace.governance_note)


def main() -> None:
    st.set_page_config(
        page_title="PolicyGuard Intelligence Studio",
        page_icon="PG",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_state()
    inject_styles()
    catalog = load_catalog()
    claims = load_claims()
    change_id = _sidebar(catalog, claims)
    portfolio = run_portfolio(claims)

    render_hero()
    tabs = st.tabs(
        [
            "01 · Executive overview",
            "02 · Policy intelligence",
            "03 · Rule studio",
            "04 · Claim impact",
            "05 · Governance",
        ]
    )
    with tabs[0]:
        page_executive(catalog, portfolio)
    with tabs[1]:
        page_policy_intelligence(catalog, change_id)
    with tabs[2]:
        page_rule_studio(catalog, claims, change_id)
    with tabs[3]:
        page_claim_impact(portfolio)
    with tabs[4]:
        page_governance(catalog, change_id)


if __name__ == "__main__":
    main()
