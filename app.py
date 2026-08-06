"""PolicyGuard Streamlit application — end-to-end HITL demo.

Orchestration overview
----------------------
1. Select old/new policy version pair (demo excerpts on disk).
2. Run difflib comparison (:mod:`src.policy_diff`).
3. Analyze material changes + propose declarative rules
   (:mod:`src.change_analyzer`) — works without an API key.
4. Display source-grounded evidence and reviewer controls
   (Approve / Reject / Request Expert Interpretation).
5. On Approve of a non-abstaining rule, run the deterministic
   :mod:`src.rule_engine` against synthetic claims.
6. Append audit events via :mod:`src.audit_log`.
7. Optional evaluation metrics panel (reads ``evaluation/`` outputs).

Governance disclaimer is shown prominently; claim language stays careful
(no fraud / denial / abusive-provider wording).
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from src.audit_log import append_audit_event, read_audit_events
from src.change_analyzer import analyze_policy_changes
from src.policy_diff import compare_policy_versions, format_diff_summary
from src.rule_engine import apply_rule, summarize_claim_impact
from src.schema import SourceGroundedChange

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
EVAL_RESULTS = ROOT / "evaluation" / "results.json"
AUDIT_PATH = DATA / "audit_log.jsonl"

# ---------------------------------------------------------------------------
# Policy version catalog (extend here for additional demo pairs)
# ---------------------------------------------------------------------------
POLICY_OPTIONS = {
    "CMS NCCI 2025 Demo → CMS NCCI 2026 Demo": {
        "old_label": "CMS NCCI Policy Manual 2025 (demo excerpt)",
        "new_label": "CMS NCCI Policy Manual 2026 (demo excerpt)",
        "old_path": DATA / "policy_2025.txt",
        "new_path": DATA / "policy_2026.txt",
    },
}


def load_text(path: Path) -> str:
    """Read a UTF-8 text file from disk.

    Parameters
    ----------
    path:
        Absolute or relative path to a policy excerpt.

    Returns
    -------
    str
        Full file contents.
    """
    return path.read_text(encoding="utf-8")


def load_claims() -> pd.DataFrame:
    """Load synthetic claims CSV (skips comment lines beginning with ``#``).

    Returns
    -------
    pd.DataFrame
        Demo claims with no PHI.
    """
    return pd.read_csv(DATA / "synthetic_claims.csv", comment="#")


def _init_session_state() -> None:
    """Initialize Streamlit session keys for reviewer decisions and impact."""
    if "decisions" not in st.session_state:
        st.session_state.decisions = {}
    if "impact_frames" not in st.session_state:
        st.session_state.impact_frames = {}
    if "impact_summaries" not in st.session_state:
        st.session_state.impact_summaries = {}


def _inject_styles() -> None:
    """Apply a clean healthcare / payment-integrity visual theme.

    Avoids generic purple AI aesthetics; uses teal accent on cool neutrals.
    """
    st.markdown(
        """
        <style>
        :root {
            --pg-ink: #1a2332;
            --pg-muted: #5c6b7a;
            --pg-surface: #f4f6f8;
            --pg-accent: #0d6e6e;
            --pg-add: #1b5e3b;
            --pg-del: #8b2e2e;
            --pg-warn: #8a6d1d;
        }
        .stApp {
            background: linear-gradient(180deg, #e8eef2 0%, #f5f7f9 45%, #ffffff 100%);
        }
        h1, h2, h3 { color: var(--pg-ink) !important; letter-spacing: 0.02em; }
        .pg-disclaimer {
            color: var(--pg-ink);
            font-size: 0.95rem;
            border-left: 4px solid var(--pg-accent);
            padding: 0.75rem 1rem;
            background: rgba(13, 110, 110, 0.08);
            margin-bottom: 1.25rem;
            line-height: 1.45;
        }
        .pg-meta { color: var(--pg-muted); font-size: 0.85rem; margin-bottom: 1rem; }
        .pg-diff-box {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.82rem;
            white-space: pre-wrap;
            background: #fff;
            border: 1px solid #d5dde5;
            border-radius: 2px;
            padding: 0.75rem 1rem;
            max-height: 280px;
            overflow-y: auto;
        }
        .pg-add { border-left: 4px solid var(--pg-add); }
        .pg-del { border-left: 4px solid var(--pg-del); }
        .pg-card {
            background: #fff;
            border: 1px solid #d5dde5;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }
        .pg-abstain {
            border-left: 4px solid var(--pg-warn);
            background: #fffbeb;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0 1rem 0;
        }
        .pg-careful {
            color: var(--pg-muted);
            font-size: 0.9rem;
            font-style: italic;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _record_decision(
    change: SourceGroundedChange,
    decision: str,
    note: str = "",
) -> None:
    """Persist a reviewer decision to session state and the audit log.

    Parameters
    ----------
    change:
        The grounded change under review.
    decision:
        ``approve``, ``reject``, or ``request_expert_interpretation``.
    note:
        Optional reviewer note.
    """
    st.session_state.decisions[change.change_id] = decision
    append_audit_event(
        "review_decision",
        {
            "change_id": change.change_id,
            "decision": decision,
            "rule_id": change.proposed_rule.rule_id if change.proposed_rule else None,
            "abstain": change.abstain,
            "reviewer_note": note,
        },
        path=AUDIT_PATH,
    )

    # On approve of a runnable rule, compute claim impact immediately.
    if (
        decision == "approve"
        and change.proposed_rule is not None
        and not change.abstain
    ):
        claims = load_claims()
        impact = apply_rule(claims, change.proposed_rule)
        summary = summarize_claim_impact(impact)
        st.session_state.impact_frames[change.change_id] = impact
        st.session_state.impact_summaries[change.change_id] = summary
        append_audit_event(
            "claim_impact_run",
            {
                "change_id": change.change_id,
                "rule_id": change.proposed_rule.rule_id,
                "flagged_for_review": summary["flagged_for_review"],
                "total_claims": summary["total_claims"],
            },
            path=AUDIT_PATH,
        )
    elif decision == "request_expert_interpretation":
        append_audit_event(
            "abstention",
            {
                "change_id": change.change_id,
                "reason": change.abstain_reason
                or "Reviewer requested expert interpretation",
            },
            path=AUDIT_PATH,
        )


def _render_change_card(change: SourceGroundedChange) -> None:
    """Render one source-grounded change with evidence, rule, and HITL buttons.

    Parameters
    ----------
    change:
        Analyzer output for a single material (or ambiguous) change.
    """
    st.markdown(f"#### {change.change_id}")
    st.markdown(
        f'<div class="pg-card">'
        f"<strong>Document:</strong> {html.escape(change.document)}<br/>"
        f"<strong>Section:</strong> {html.escape(change.section)}<br/>"
        f"<strong>Effective date:</strong> "
        f"{change.effective_date.isoformat() if change.effective_date else 'insufficient evidence'}<br/>"
        f"<strong>Change type:</strong> {html.escape(change.change_type)} · "
        f"<strong>Confidence:</strong> {change.confidence:.2f}<br/>"
        f"<strong>Summary:</strong> {html.escape(change.summary)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Evidence passage**")
    st.code(change.evidence_passage, language=None)

    if change.abstain:
        reason = change.abstain_reason or (
            "Insufficient evidence for a declarative rule. No automated action taken."
        )
        st.markdown(
            '<div class="pg-abstain"><strong>Abstain — requires expert interpretation</strong><br/>'
            f"{html.escape(reason)}</div>",
            unsafe_allow_html=True,
        )

    if change.proposed_rule is not None:
        st.markdown("**Proposed declarative rule (validated JSON — not executable Python)**")
        st.json(json.loads(change.proposed_rule.model_dump_json()))
    else:
        st.caption("No rule proposed for this change.")

    prior = st.session_state.decisions.get(change.change_id)
    if prior:
        st.info(f"Reviewer decision recorded: **{prior}**")

    # --- Reviewer controls (HITL gate) ------------------------------------
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            "Approve",
            key=f"approve_{change.change_id}",
            disabled=change.abstain and change.proposed_rule is None,
            help="Approve proposed rule for claim-impact flagging only",
        ):
            if change.abstain and change.proposed_rule is None:
                st.warning(
                    "Cannot approve a runnable rule — this change abstains. "
                    "Use Request Expert Interpretation."
                )
            else:
                _record_decision(change, "approve")
                st.rerun()
    with c2:
        if st.button("Reject", key=f"reject_{change.change_id}"):
            _record_decision(change, "reject")
            st.rerun()
    with c3:
        if st.button(
            "Request Expert Interpretation",
            key=f"expert_{change.change_id}",
        ):
            _record_decision(change, "request_expert_interpretation")
            st.rerun()

    # --- Claim impact (careful language only) -----------------------------
    if change.change_id in st.session_state.impact_summaries:
        summary = st.session_state.impact_summaries[change.change_id]
        st.markdown("##### Claim impact summary")
        st.markdown(
            f'<p class="pg-careful">{html.escape(str(summary["narrative"]))}</p>',
            unsafe_allow_html=True,
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Synthetic claims", summary["total_claims"])
        m2.metric("Matched conditions", summary["matched_conditions"])
        m3.metric("Flagged for review", summary["flagged_for_review"])
        impact_df = st.session_state.impact_frames[change.change_id]
        flagged = impact_df[impact_df["rule_action"] == "flag_for_review"]
        st.caption(
            "Rows below are potentially affected and flagged for review. "
            "No automated denial action was taken."
        )
        st.dataframe(flagged, use_container_width=True)


def main() -> None:
    """Streamlit entrypoint: configure page and run the full HITL workflow."""
    st.set_page_config(
        page_title="PolicyGuard",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session_state()
    _inject_styles()

    # ======================================================================
    # STAGE 0 — Branding + governance disclaimer (always visible)
    # ======================================================================
    st.title("POLICYGUARD")
    st.subheader("Source-Grounded Policy Change and Rule Validation")
    st.markdown(
        '<div class="pg-disclaimer">'
        "<strong>Disclaimer:</strong> PolicyGuard is a human-in-the-loop proof of concept "
        "that compares healthcare policy versions, extracts source-grounded changes, "
        "proposes validated declarative rules, and tests approved rules against synthetic "
        "claims. It does not make autonomous clinical, payment, or claim-denial decisions. "
        "Policy excerpts and claims are synthetic demonstration data for assessment use "
        "only—not official CMS republication and not PHI."
        "</div>",
        unsafe_allow_html=True,
    )

    # ======================================================================
    # STAGE 1 — Select old / new policy versions
    # ======================================================================
    with st.sidebar:
        st.markdown("### Demo controls")
        st.caption("No API key required. Deterministic analyzer + rule builder.")
        show_eval = st.checkbox("Show evaluation panel", value=False)
        st.markdown("---")
        st.markdown("### Audit log")
        events = read_audit_events(AUDIT_PATH)
        st.caption(f"{len(events)} event(s) in session log")
        if st.button("Refresh audit view"):
            st.rerun()

    selection = st.selectbox(
        "Policy version pair",
        options=list(POLICY_OPTIONS.keys()),
        help="Demo excerpts inspired by CMS Medicare NCCI Policy Manual Chapter XI style.",
    )
    pair = POLICY_OPTIONS[selection]
    old_text = load_text(pair["old_path"])
    new_text = load_text(pair["new_path"])

    # ======================================================================
    # STAGE 2 — Detect additions / deletions (difflib)
    # ======================================================================
    diff = compare_policy_versions(old_text, new_text)

    st.markdown(
        f'<p class="pg-meta">Comparing <strong>{html.escape(pair["old_label"])}</strong> '
        f'to <strong>{html.escape(pair["new_label"])}</strong></p>',
        unsafe_allow_html=True,
    )

    col_old, col_new = st.columns(2)
    with col_old:
        st.markdown(f"**Old policy — {pair['old_label']}**")
        st.text_area(
            "old_policy",
            value=old_text,
            height=320,
            disabled=True,
            label_visibility="collapsed",
        )
    with col_new:
        st.markdown(f"**New policy — {pair['new_label']}**")
        st.text_area(
            "new_policy",
            value=new_text,
            height=320,
            disabled=True,
            label_visibility="collapsed",
        )

    st.markdown("---")
    st.markdown("### Detected line-level changes")
    st.caption(format_diff_summary(diff) + " (difflib.ndiff)")

    col_add, col_del = st.columns(2)
    with col_add:
        st.markdown("**Additions** (present in newer version only)")
        add_body = html.escape(
            "\n".join(diff["additions"]) if diff["additions"] else "(none)"
        )
        st.markdown(
            f'<div class="pg-diff-box pg-add">{add_body}</div>',
            unsafe_allow_html=True,
        )
    with col_del:
        st.markdown("**Deletions** (present in older version only)")
        del_body = html.escape(
            "\n".join(diff["deletions"]) if diff["deletions"] else "(none)"
        )
        st.markdown(
            f'<div class="pg-diff-box pg-del">{del_body}</div>',
            unsafe_allow_html=True,
        )

    # ======================================================================
    # STAGE 3–4 — Source-grounded changes + proposed validated rules
    # ======================================================================
    st.markdown("---")
    st.markdown("### Source-grounded material changes")
    st.caption(
        "Deterministic analyzer maps known demo patterns to grounded changes "
        "and Pydantic-validated JSON rules. Ambiguous language abstains."
    )
    changes = analyze_policy_changes(old_text, new_text, diff=diff)

    if not changes:
        st.warning("No patterned material changes detected in this pair.")
    else:
        for change in changes:
            # Log proposal / abstention once per change id per session view
            if f"logged_{change.change_id}" not in st.session_state:
                append_audit_event(
                    "rule_proposed" if change.proposed_rule else "change_detected",
                    {
                        "change_id": change.change_id,
                        "abstain": change.abstain,
                        "rule_id": (
                            change.proposed_rule.rule_id
                            if change.proposed_rule
                            else None
                        ),
                        "change_type": change.change_type,
                        "timestamp_viewed": datetime.now(timezone.utc).isoformat(),
                    },
                    path=AUDIT_PATH,
                )
                st.session_state[f"logged_{change.change_id}"] = True
            _render_change_card(change)
            st.markdown("---")

    # ======================================================================
    # STAGE 5 — Audit trail preview
    # ======================================================================
    st.markdown("### Audit trail (JSONL)")
    recent = read_audit_events(AUDIT_PATH)[-15:]
    if recent:
        st.json(recent)
    else:
        st.caption("No audit events yet — review a change to populate the log.")

    # ======================================================================
    # STAGE 6 (optional) — Evaluation metrics from gold-set run
    # ======================================================================
    if show_eval and EVAL_RESULTS.exists():
        st.markdown("### Evaluation panel (POC-scale gold set)")
        st.caption(
            "Metrics from evaluation/ — small manually labeled demo set; "
            "not production performance claims."
        )
        st.json(json.loads(EVAL_RESULTS.read_text(encoding="utf-8")))
    elif show_eval:
        st.info(
            "Run `python -m evaluation.run_evaluation` to generate "
            "evaluation/results.json for this panel."
        )


if __name__ == "__main__":
    main()
