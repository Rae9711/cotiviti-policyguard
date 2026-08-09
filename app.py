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
from src.evaluation_display import (
    WHAT_THIS_IS,
    abstention_checks_table,
    entity_checks_table,
    metric_cards,
    rule_checks_table,
)
from src.impact import dry_run_rule, review_burden_metrics, run_portfolio
from src.semantic_diff import compare_texts, extract_text_from_upload
from src.ui import (
    chart_why,
    inject_styles,
    kpi_row,
    monthly_trend_fig,
    opportunity_matrix_fig,
    optional_detail,
    provider_bubble_fig,
    q3014_hist_fig,
    render_hero,
    section_help,
    source_card,
    volume_bar_fig,
)

ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "data" / "audit_log.jsonl"
EVAL_RESULTS = ROOT / "evaluation" / "results.json"

# Recommended evaluator path
RECOMMENDED_CHANGE_ID = "THERAPY-KX-THRESHOLD-2026"
ABSTENTION_CHANGE_ID = "THERAPY-SKILLED-VS-FITNESS"
ALT_SCENARIO_ID = "NCCI-94662-RETIREMENT"


def _init_state() -> None:
    if "selected_change_id" not in st.session_state:
        st.session_state.selected_change_id = RECOMMENDED_CHANGE_ID
    if "guide_seen" not in st.session_state:
        st.session_state.guide_seen = False
    if "show_guide" not in st.session_state:
        st.session_state.show_guide = True
    if "simple_demo_mode" not in st.session_state:
        st.session_state.simple_demo_mode = True


def _dismiss_guide() -> None:
    """Callback: runs before widgets on the next run, so show_guide is safe to set."""
    st.session_state.guide_seen = True
    st.session_state.show_guide = False


def _render_demo_guide() -> None:
    """Interactive Evaluator / Demo Guide panel."""
    with st.expander(
        "Evaluator / Demo Guide",
        expanded=st.session_state.show_guide and not st.session_state.guide_seen,
    ):
        st.markdown(
            """
**Main function:** turn a public policy version change into source-grounded evidence,
a validated review rule (or an explicit abstention), a synthetic claim-impact preview,
and a human Approve / Reject / Escalate decision — **with no automatic claim action**.

### 60-second path
1. **01 · Executive overview** — portfolio of five policy patterns
2. **02 · Policy intelligence** — before/after + official source cards
3. **03 · Rule studio** — validated JSON proposal or abstention
4. **04 · Claim impact** — flagged-for-review volume + synthetic review-burden comparison (not fraud/savings)
5. **05 · Governance** — record a human decision + download audit

### What to look for on each tab
- **Executive:** five curated changes; one required abstention; opportunity matrix is supporting context
- **Policy intelligence:** highlighted deltas tied to official CMS locators
- **Rule studio:** declarative JSON for human review — not executable auto-denial code
- **Claim impact:** synthetic claims *flagged for review*; review-burden % vs all-claim screening; “paid amount in scope” ≠ savings
- **Governance:** Approve / Reject / Escalate with `automatic_claim_action=false`; demo checklist (not accuracy)

### Recommended scenarios
- Start with **Therapy KX threshold increased** (or **94662 retirement**)
- Then switch to **Skilled-therapy versus general-fitness** to see abstention as a feature

Charts and matrices are **supporting evidence**, not the point. The point is the
controlled workflow ending in a human gate.

Full write-up: [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) · demo script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
            """
        )
        # Must use on_click — assigning show_guide after the sidebar toggle
        # (same key) raises StreamlitAPIException.
        st.button(
            "Got it — hide coach marks",
            key="guide_dismiss_btn",
            on_click=_dismiss_guide,
        )


def _render_first_run_coach() -> None:
    if st.session_state.guide_seen:
        return
    st.info(
        "**Start here:** set Focus change to **Therapy KX threshold increased** "
        "(or **Ventilation management code 94662 retired**), walk tabs 01→05, "
        "then switch to **Skilled-therapy versus general-fitness** to see "
        "abstention — refusing to automate when claim fields are insufficient. "
        "Use the Evaluator / Demo Guide above for the 60-second path."
    )


def _sidebar(catalog, claims: pd.DataFrame) -> tuple[str, bool]:
    with st.sidebar:
        st.markdown("### PG  PolicyGuard")
        st.caption("CMS payment-policy intelligence pack")
        st.caption("Assessment build · v2.0")
        st.divider()

        simple_mode = st.toggle(
            "Simple demo mode",
            help="Emphasizes the recommended scenario and collapses secondary charts. "
            "Keep Approve/Reject/Escalate and abstention visible.",
            key="simple_demo_mode",
        )

        show_guide = st.toggle(
            "Show guide",
            help="Show or hide the Evaluator / Demo Guide panel.",
            key="show_guide",
        )

        st.divider()
        st.markdown("**Workspace**")
        st.write(catalog.workspace.name)
        titles = {c.change_id: c.title for c in catalog.changes}
        options = list(titles.keys())

        if simple_mode and RECOMMENDED_CHANGE_ID in options:
            st.caption(
                f"Recommended: **{titles[RECOMMENDED_CHANGE_ID]}** · "
                f"also try {titles.get(ALT_SCENARIO_ID, '94662')} · "
                f"then abstention: {titles.get(ABSTENTION_CHANGE_ID, 'skilled vs fitness')}"
            )
            # Put recommended first in the list for clarity
            options = [RECOMMENDED_CHANGE_ID] + [
                cid for cid in options if cid != RECOMMENDED_CHANGE_ID
            ]

        selected = st.selectbox(
            "Focus change",
            options=options,
            format_func=lambda cid: (
                f"★ {titles[cid]}" if cid == RECOMMENDED_CHANGE_ID and simple_mode else titles[cid]
            ),
            index=options.index(st.session_state.selected_change_id)
            if st.session_state.selected_change_id in options
            else 0,
            help="Select a curated CMS policy-change scenario. "
            "Therapy KX is the default evaluator path; skilled-vs-fitness shows abstention.",
            key="focus_change_select",
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
        st.caption("User guide: docs/USER_GUIDE.md")
    return selected, simple_mode


def page_executive(catalog, portfolio: dict, simple_mode: bool) -> None:
    st.subheader("Executive signal")
    st.caption("Policy materiality, automation readiness, and synthetic operational exposure.")
    section_help(
        "What is this?",
        "Portfolio view of curated CMS policy changes. Shows how many proposals "
        "are executable vs. required abstentions, and where materiality meets "
        "automation readiness. **This is context for the workflow — not the main demo.**",
    )

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
    st.caption(
        "Required abstentions are intentional: when structured claim fields cannot "
        "establish clinical purpose, PolicyGuard refuses to automate."
    )
    st.write("")

    with optional_detail("opportunity matrix & volume charts", simple_mode):
        left, right = st.columns(2)
        with left:
            st.markdown("**Policy opportunity matrix**")
            chart_why(
                "Why this chart exists: ranks changes by materiality vs. automation "
                "readiness so reviewers prioritize — it does not trigger claim action."
            )
            st.plotly_chart(
                opportunity_matrix_fig(portfolio["opportunity_matrix"]),
                use_container_width=True,
                key="exec_opportunity_matrix",
            )
        with right:
            st.markdown("**Synthetic review volume by change**")
            chart_why(
                "Why this chart exists: shows how many synthetic claims each rule "
                "would route to human review — volume for prioritization, not savings."
            )
            st.plotly_chart(
                volume_bar_fig(portfolio["per_change"]),
                use_container_width=True,
                key="exec_volume_bar",
            )
    st.caption(
        "Paid amount in scope is a synthetic aggregation for demonstration only — "
        "not an overpayment, recovery, or savings estimate."
    )


def page_policy_intelligence(catalog, change_id: str) -> None:
    change = get_change(change_id, catalog)
    st.subheader("Policy intelligence")
    st.caption("Source-grounded before/after comparison with entity extraction.")
    section_help(
        "What is this?",
        "Step **Compare → Evidence**. Side-by-side policy snapshots with highlighted "
        "deltas and official CMS source cards. Every proposed rule must be traceable "
        "to a locator — this tab proves the change is real before any rule is drafted.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Materiality", change.materiality_score, help="How operationally consequential this change appears.")
    c2.metric(
        "Automation readiness",
        change.automation_readiness,
        help="How cleanly claim fields alone can express the change.",
    )
    c3.metric("Risk tier", change.risk_tier, help="Review risk if automation were attempted prematurely.")
    c4.metric("Evidence quality", change.evidence_quality, help="Strength of official-source provenance.")

    st.markdown("**Before / after comparison**")
    chart_why(
        "Why this exists: evaluators should see the exact policy wording change "
        "before trusting any downstream rule."
    )
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
        st.caption("Codes, dates, currencies, and modifiers pulled from the text — not inferred.")
        st.dataframe(
            pd.DataFrame([d.__dict__ for d in deltas]),
            use_container_width=True,
            hide_index=True,
            key="pi_entity_deltas",
        )

    st.markdown("**Official source evidence**")
    st.caption("Each card includes organization, locator, and a link to the public CMS (or related) source.")
    for source in get_sources_for_change(change, catalog):
        source_card(source)

    st.download_button(
        "Download comparison JSON",
        data=json.dumps(comparison.to_dict(), indent=2),
        file_name=f"{change.change_id}_comparison.json",
        mime="application/json",
        key="pi_download_comparison",
        help="Export the comparison artifact for offline review.",
    )

    with st.expander("Compare local TXT/PDF uploads (in memory)"):
        st.caption("Optional: uploads stay in memory and are never persisted.")
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
    section_help(
        "What is this?",
        "Step **Rule / Abstain**. When the change is claim-field clear, PolicyGuard "
        "emits a schema-validated JSON **proposal for human review** — not executable "
        "auto-denial code. When clinical purpose is required, it **abstains** "
        "(refusing to automate is a feature).",
    )

    if change.abstains or change.rule_template is None:
        st.warning(
            "System abstention: clinical documentation and expert interpretation required. "
            "**Refusing to automate is a product feature**, not a failure."
        )
        st.info(change.abstain_reason or "No claim-level rule can be generated from structured fields alone.")
        section_help(
            "Why abstention matters",
            "Skilled therapy vs. general fitness (and similar language) depends on "
            "clinical purpose and documentation. Structured claim fields alone are "
            "insufficient, so PolicyGuard will not invent a claim-level rule.",
            expanded=True,
        )
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
    st.info(
        "This JSON is a **proposal for human review**, not executable auto-denial code. "
        "The engine interprets declarative conditions; it never executes generated Python/SQL."
    )
    def _display_value(value: object) -> str:
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return "" if value is None else str(value)

    conditions = pd.DataFrame(
        [
            {
                "field": c.field,
                "operator": c.operator,
                "value": _display_value(c.value),
                "tolerance": c.tolerance,
            }
            for c in rule.conditions
        ]
    )
    st.dataframe(
        conditions,
        use_container_width=True,
        hide_index=True,
        key="rule_conditions_df",
    )

    rule_json = rule.model_dump()
    st.download_button(
        "Download rule JSON",
        data=json.dumps(rule_json, indent=2, default=str),
        file_name=f"{rule.rule_id}.json",
        mime="application/json",
        key="rule_download_json",
        help="Download the validated proposal for offline governance review.",
    )

    with st.expander("Validated rule JSON", expanded=False):
        st.caption(
            "Proposal for human review — not executable auto-denial code. "
            "`automatic_claim_action` remains false downstream."
        )
        st.json(rule_json)

    st.markdown("**Dry-run on synthetic claims**")
    chart_why(
        "Why this exists: shows how many synthetic rows match the proposal so "
        "reviewers can sanity-check scope before any approval."
    )
    dry = dry_run_rule(claims, rule)
    st.metric("Dry-run matches", dry["matched_count"])
    st.caption("Deterministic interpreter only — no generated Python/SQL is executed.")
    if dry["matched_count"]:
        st.dataframe(
            dry["sample"],
            use_container_width=True,
            hide_index=True,
            key="rule_dry_run_sample",
        )


def _pct_display(rate: float, digits: int = 1) -> str:
    return f"{rate * 100:.{digits}f}%"


def page_claim_impact(portfolio: dict, simple_mode: bool, catalog, change_id: str) -> None:
    st.subheader("Claim impact")
    st.caption("Synthetic operational exposure for human review prioritization.")
    section_help(
        "What is this?",
        "Step **Impact**. Synthetic claims are **flagged for review** — not denied, "
        "not labeled fraud, and not counted as savings. “Paid amount in scope” is "
        "only the paid dollars on flagged synthetic rows. Review-burden percentages "
        "compare this HITL workflow to naive claim-by-claim screening on the "
        "synthetic pack — not production labor savings.",
    )

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
        "Claims are **flagged for review**. Paid amount in scope is **not** an "
        "overpayment, recovery, fraud, or savings figure."
    )

    burden = review_burden_metrics(
        portfolio, catalog=catalog, selected_change_id=change_id
    )
    st.markdown("**Synthetic review-burden comparison**")
    st.caption(
        "Baseline A: a reviewer would theoretically inspect every synthetic claim "
        "in scope to apply a new policy change. PolicyGuard: humans make a small "
        "number of rule-level decisions (approve / reject / escalate / abstain), "
        "then only flagged claims enter a review queue."
    )
    flagged_per = burden["flagged_per_executable_decision"]
    gates_per_100 = burden["gates_per_100_flagged"]
    flagged_per_label = f"{flagged_per:.1f}" if flagged_per is not None else "—"
    gates_caption = (
        f"{burden['unique_claims_flagged']} unique flagged / "
        f"{burden['executable_proposals']} executable proposals → "
        f"1 human rule decision per {flagged_per:.1f} queued claims"
        + (
            f" · {gates_per_100:.1f} rule-level gates per 100 flagged claims"
            if gates_per_100 is not None
            else ""
        )
        if flagged_per is not None
        else "No executable proposals in this catalog."
    )
    selected = burden["selected"]
    if selected and selected["abstains"]:
        selected_value = "1 → 0"
        selected_caption = (
            f"{selected['short_label']}: this curated change abstains — "
            "0 claim-level rule, so no noisy review queue is generated."
        )
    elif selected:
        selected_value = f"1 → {selected['flagged_claims']}"
        selected_caption = (
            f"{selected['short_label']}: one human rule-level gate covers "
            f"{selected['flagged_claims']} flagged-for-review matches on this "
            "synthetic pack."
        )
    else:
        selected_value = "—"
        selected_caption = "Select a focus change to see one-human-gate scope."

    kpi_row(
        [
            (
                "Review concentration",
                _pct_display(burden["review_concentration"]),
                (
                    f"{burden['unique_claims_flagged']} of {burden['claims_evaluated']} "
                    "synthetic claims flagged for review vs reviewing 100% of claims "
                    "after a policy change."
                ),
            ),
            (
                "Not flagged under these rules",
                _pct_display(burden["not_flagged_rate"]),
                (
                    "Not auto-paid or auto-denied — simply not flagged by the current "
                    "approved-for-testing proposals."
                ),
            ),
            (
                "Decision compression",
                _pct_display(burden["decision_compression"]),
                (
                    f"{burden['policy_decisions']} rule-level policy decisions "
                    f"({burden['executable_proposals']} executable + "
                    f"{burden['abstentions']} abstention) vs "
                    f"{burden['claims_evaluated']} claim-level interpretations."
                ),
            ),
        ]
    )
    kpi_row(
        [
            (
                "Flagged claims per rule-level gate",
                flagged_per_label,
                gates_caption,
            ),
            (
                "Selected change coverage",
                selected_value,
                selected_caption,
            ),
            (
                "Abstention share",
                _pct_display(burden["abstention_share"], digits=0),
                (
                    f"{burden['abstentions']} of {burden['curated_changes']} curated "
                    "changes abstain — prevents generating a noisy review queue when "
                    "evidence is insufficient."
                ),
            ),
        ]
    )

    st.info(
        "These percentages compare this HITL workflow to naive all-claim manual "
        "screening on the **synthetic** pack. They are not production labor savings "
        "or payment-accuracy lifts."
    )

    with optional_detail("trend & volume charts", simple_mode):
        t1, t2 = st.columns(2)
        with t1:
            st.markdown("**Monthly review-event trend**")
            chart_why(
                "Why this chart exists: shows when synthetic review events cluster "
                "across months of service — workload timing, not financial recovery."
            )
            st.plotly_chart(
                monthly_trend_fig(portfolio["monthly_trend"]),
                use_container_width=True,
                key="impact_monthly_trend",
            )
        with t2:
            st.markdown("**Policy-level review volume**")
            chart_why(
                "Why this chart exists: compares synthetic review volume across "
                "policy changes to prioritize human attention."
            )
            st.plotly_chart(
                volume_bar_fig(portfolio["per_change"]),
                use_container_width=True,
                key="impact_volume_bar",
            )

    with optional_detail("provider & fee-distribution charts", simple_mode):
        p1, p2 = st.columns(2)
        with p1:
            st.markdown("**Provider concentration**")
            chart_why(
                "Why this chart exists: highlights which synthetic providers accumulate "
                "the most review events — triage aid only."
            )
            st.plotly_chart(
                provider_bubble_fig(portfolio["provider_concentration"]),
                use_container_width=True,
                key="impact_provider_bubble",
            )
        with p2:
            st.markdown("**Q3014 fee-variance distribution**")
            chart_why(
                "Why this chart exists: illustrates fee-tolerance checks for the "
                "Q3014 scenario — configuration variance for review, not auto-reprice."
            )
            st.plotly_chart(
                q3014_hist_fig(portfolio["q3014_distribution"]),
                use_container_width=True,
                key="impact_q3014_hist",
            )

    st.markdown("**Prioritized reviewer queue**")
    st.caption(
        "Human worklist of synthetic claims flagged for review. "
        "Nothing here denies or adjusts payment."
    )
    queue = portfolio["queue"]
    st.dataframe(
        queue.head(40),
        use_container_width=True,
        hide_index=True,
        key="impact_reviewer_queue",
    )
    st.download_button(
        "Download reviewer queue CSV",
        data=queue.to_csv(index=False),
        file_name="reviewer_queue.csv",
        mime="text/csv",
        key="impact_download_queue",
        help="Export the prioritized synthetic review queue.",
    )


def page_governance(catalog, change_id: str) -> None:
    change = get_change(change_id, catalog)
    st.subheader("Governance")
    st.caption("Human approval with Cotiviti/NIST-inspired controls and exportable audit.")
    section_help(
        "What is this?",
        "Step **Human decision**. Approve, reject, or escalate a proposal. "
        "Every recorded event hard-codes `automatic_claim_action=false`. "
        "This is the mandatory human gate — the thesis ends here, not in auto-action.",
    )

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
        st.warning(
            "Selected change abstains from claim-level automation. "
            "You can still escalate to a policy / coding / clinical expert."
        )
        st.write(change.abstain_reason)

    st.markdown("**Record a human decision**")
    st.caption("Required for the demo thesis: no proposal becomes operational without a reviewer.")
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
            help="Human gate only — never triggers claim denial or reprice.",
        )
        note = st.text_area(
            "Rationale",
            placeholder="Document why this decision is appropriate.",
            help="Capture why Approve / Reject / Escalate is appropriate for this change.",
        )
        verified = st.checkbox(
            "I verified the official source locator(s)",
            value=False,
            help="Confirm you opened the official source evidence before deciding.",
        )
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

    st.markdown("**Audit trail**")
    st.caption("Exportable JSONL of human decisions — proof that claim action stayed off.")
    events = read_audit_events(AUDIT_PATH)
    if events:
        st.dataframe(
            pd.DataFrame(events),
            use_container_width=True,
            hide_index=True,
            key="gov_audit_trail",
        )
    else:
        st.info("No audit events yet. Record a decision to populate the trail.")

    st.download_button(
        "Download audit JSONL",
        data=audit_events_jsonl(AUDIT_PATH) or "",
        file_name="policyguard_audit.jsonl",
        mime="application/jsonl",
        key="gov_download_audit",
        help="Download the full audit log including automatic_claim_action=false.",
    )

    if EVAL_RESULTS.exists():
        _render_evaluation_results()

    st.caption(catalog.workspace.governance_note)


def _render_evaluation_results() -> None:
    """Governance panel for evaluation/results.json — tables, not 0/1 JSON keys."""
    payload = json.loads(EVAL_RESULTS.read_text(encoding="utf-8"))
    st.markdown("**Demo software checklist**")
    st.caption(
        "Not production model accuracy. Confirms the deterministic demo still "
        "behaves as designed on handcrafted fixtures."
    )
    section_help("What this is", WHAT_THIS_IS)
    kpi_row(metric_cards(payload))
    st.caption(
        f"Status: `{payload.get('status', 'unknown')}` · generated "
        f"{payload.get('generated_at_utc', '—')}. "
        f"{payload.get('scope_note', '')}"
    )

    st.markdown("**Rule assertions (synthetic claim cases)**")
    st.caption(
        "`Flag for review` means the claim matched the rule; `No flag` means it did not. "
        "Pass = expected outcome equals observed. Indices 0–7 are case numbers, not scores."
    )
    st.dataframe(
        rule_checks_table(payload),
        use_container_width=True,
        hide_index=True,
        key="gov_eval_rule_checks",
    )

    st.markdown("**Entity checks (snapshot extraction)**")
    st.caption(
        "Did comparison/entity extraction see the expected dates, dollars, and codes "
        "in the curated policy snapshots?"
    )
    st.dataframe(
        entity_checks_table(payload),
        use_container_width=True,
        hide_index=True,
        key="gov_eval_entity_checks",
    )

    st.markdown("**Abstention checks (clinical / fitness change)**")
    st.caption(
        "THERAPY-SKILLED-VS-FITNESS must not emit a claim-level rule template, "
        "and the abstention reason must be documented."
    )
    st.dataframe(
        abstention_checks_table(payload),
        use_container_width=True,
        hide_index=True,
        key="gov_eval_abstention_checks",
    )

    with st.expander("Raw JSON", expanded=False):
        st.caption(
            "Same file as `evaluation/results.json`. List keys 0, 1, 2… are array "
            "indices, not scores. See `evaluation/RESULTS_README.md`."
        )
        st.json(payload)


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
    change_id, simple_mode = _sidebar(catalog, claims)
    portfolio = run_portfolio(claims)

    render_hero()
    if st.session_state.show_guide:
        _render_demo_guide()
    _render_first_run_coach()

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
        page_executive(catalog, portfolio, simple_mode)
    with tabs[1]:
        page_policy_intelligence(catalog, change_id)
    with tabs[2]:
        page_rule_studio(catalog, claims, change_id)
    with tabs[3]:
        page_claim_impact(portfolio, simple_mode, catalog, change_id)
    with tabs[4]:
        page_governance(catalog, change_id)


if __name__ == "__main__":
    main()
