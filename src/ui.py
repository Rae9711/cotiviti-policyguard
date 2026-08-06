"""Shared Streamlit presentation helpers for PolicyGuard v2.

Keeps visual styling, KPI cards, and Plotly chart factories in one place
so the five workspaces stay consistent with the design system shown in
``assets/ui_preview.png``.
"""

from __future__ import annotations

import html
from contextlib import nullcontext
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Design tokens aligned with the interface preview
COLORS = {
    "ink": "#1a1f36",
    "muted": "#5b647a",
    "accent": "#5b4cdb",
    "accent2": "#7c6cff",
    "sidebar": "#14182b",
    "danger": "#d64545",
    "warn": "#e09a2d",
    "ok": "#1f9d6a",
    "surface": "#f5f6fb",
}

RISK_COLORS = {"High": "#d64545", "Medium": "#e09a2d", "Low": "#1f9d6a"}


def inject_styles() -> None:
    """Apply the PolicyGuard v2 visual theme."""
    st.markdown(
        f"""
        <style>
        :root {{
            --pg-ink: {COLORS["ink"]};
            --pg-muted: {COLORS["muted"]};
            --pg-accent: {COLORS["accent"]};
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #14182b 0%, #1c2240 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: #e8eaf4 !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox label {{
            color: #b8bfd8 !important;
        }}
        .pg-hero {{
            background: linear-gradient(120deg, #14182b 0%, #2a2460 55%, #4b3bb8 100%);
            color: white;
            padding: 1.35rem 1.5rem 1.25rem 1.5rem;
            border-radius: 18px;
            margin-bottom: 1rem;
            box-shadow: 0 10px 30px rgba(28, 24, 70, 0.18);
        }}
        .pg-hero h1 {{
            margin: 0 0 0.35rem 0;
            font-size: 1.85rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        .pg-hero > p {{
            margin: 0;
            opacity: 0.92;
            max-width: 52rem;
            line-height: 1.45;
        }}
        .pg-narrative {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 1rem;
        }}
        @media (max-width: 900px) {{
            .pg-narrative {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        @media (max-width: 520px) {{
            .pg-narrative {{
                grid-template-columns: 1fr;
            }}
        }}
        .pg-narrative-block {{
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 12px;
            padding: 0.7rem 0.8rem;
            min-width: 0;
        }}
        .pg-narrative-block .label {{
            display: block;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            opacity: 0.78;
            margin-bottom: 0.3rem;
        }}
        .pg-narrative-block p {{
            margin: 0;
            font-size: 0.8rem;
            line-height: 1.4;
            opacity: 0.95;
        }}
        .pg-narrative-block code {{
            font-size: 0.74rem;
            background: rgba(0,0,0,0.25);
            padding: 0.05rem 0.28rem;
            border-radius: 4px;
        }}
        .pg-constraints {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.75rem;
        }}
        .pg-constraint {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            opacity: 0.85;
        }}
        .pg-kpi {{
            background: white;
            border: 1px solid #e6e8f2;
            border-radius: 14px;
            padding: 0.9rem 1rem;
            box-shadow: 0 1px 2px rgba(20,24,43,0.04);
        }}
        .pg-kpi .label {{
            color: {COLORS["muted"]};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .pg-kpi .value {{
            color: {COLORS["ink"]};
            font-size: 1.65rem;
            font-weight: 700;
            margin-top: 0.15rem;
        }}
        .pg-card {{
            background: white;
            border: 1px solid #e6e8f2;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.75rem;
        }}
        .pg-card h4 {{
            margin: 0 0 0.35rem 0;
            color: {COLORS["ink"]};
        }}
        .pg-muted {{ color: {COLORS["muted"]}; font-size: 0.9rem; }}
        mark.pg-del {{
            background: #ffd6d6;
            color: #7a1f1f;
            padding: 0 0.15rem;
            border-radius: 3px;
        }}
        mark.pg-ins {{
            background: #d8f5e5;
            color: #145c38;
            padding: 0 0.15rem;
            border-radius: 3px;
        }}
        .pg-removed {{ background: #fff1f1; padding: 0.4rem 0.55rem; border-radius: 8px; }}
        .pg-added {{ background: #eefaf3; padding: 0.4rem 0.55rem; border-radius: 8px; }}
        .pg-status-dot {{
            display: inline-block;
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 50%;
            background: #2ecc87;
            margin-right: 0.4rem;
        }}
        .pg-why {{
            color: {COLORS["muted"]};
            font-size: 0.85rem;
            margin: -0.15rem 0 0.55rem 0;
        }}
        div[data-testid="stMetricValue"] {{
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Presentation-ready hero banner with Problem / Approach / Result / Cotiviti fit."""
    st.markdown(
        """
        <div class="pg-hero">
          <h1>PolicyGuard Intelligence Studio</h1>
          <p>From authoritative policy change to a source-grounded, testable review
          workflow—without autonomous claim denial or clinical decision-making.</p>
          <div class="pg-narrative">
            <div class="pg-narrative-block">
              <span class="label">Problem</span>
              <p>Healthcare payment policies change; translating written policy into
              consistent, auditable review logic is slow and error-prone—and unsafe
              automation can over-claim denials.</p>
            </div>
            <div class="pg-narrative-block">
              <span class="label">Approach</span>
              <p>Compare authoritative policy versions, attach source evidence, propose
              Pydantic-validated declarative rules (or abstain), simulate impact on
              synthetic claims, require human approve/reject/escalate.</p>
            </div>
            <div class="pg-narrative-block">
              <span class="label">Result</span>
              <p>Speeds policy-change intake into a reviewable workflow, improves
              auditability with source-grounded proposals, and raises safety by
              abstaining when automation would be unjustified—demonstrated on
              synthetic claims with human-gated decisions.</p>
            </div>
            <div class="pg-narrative-block">
              <span class="label">Cotiviti fit</span>
              <p>Aligns with Cotiviti’s payment-accuracy / Payment Policy Management need
              to tailor, test, and execute policies with transparency and
              accountability—not a generic chatbot demo.</p>
            </div>
          </div>
          <div class="pg-constraints">
            <span class="pg-constraint">Public CMS sources</span>
            <span class="pg-constraint">Synthetic claims only</span>
            <span class="pg-constraint">No automatic claim denial</span>
            <span class="pg-constraint">Human approval required</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_help(title: str, body: str, *, expanded: bool = False) -> None:
    """Collapsible per-block explainer for evaluators."""
    with st.expander(title, expanded=expanded):
        st.markdown(body)


def chart_why(sentence: str) -> None:
    """One-line purpose under a chart title."""
    st.markdown(f'<p class="pg-why">{html.escape(sentence)}</p>', unsafe_allow_html=True)


def optional_detail(label: str, simple_mode: bool):
    """Collapse secondary charts when Simple demo mode is on."""
    if simple_mode:
        return st.expander(f"Optional detail · {label}", expanded=False)
    return nullcontext()


def kpi_row(items: list[tuple[str, str]]) -> None:
    """Render a horizontal row of KPI cards."""
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div class="pg-kpi">
                  <div class="label">{html.escape(label)}</div>
                  <div class="value">{html.escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def source_card(source: Any) -> None:
    """Render an official-source evidence card."""
    pub = source.publication_date.isoformat() if source.publication_date else "—"
    eff = source.effective_date.isoformat() if source.effective_date else "—"
    st.markdown(
        f"""
        <div class="pg-card">
          <h4>{html.escape(source.title)}</h4>
          <div class="pg-muted">{html.escape(source.organization)} · {html.escape(source.source_type)}</div>
          <p style="margin:0.55rem 0 0.25rem 0;"><strong>Locator:</strong> {html.escape(source.locator)}</p>
          <p style="margin:0.15rem 0;"><strong>Used for:</strong> {html.escape(source.used_for)}</p>
          <p style="margin:0.15rem 0;" class="pg-muted">Published {html.escape(pub)} · Effective {html.escape(eff)}</p>
          <p style="margin:0.45rem 0 0 0;"><a href="{html.escape(source.url)}" target="_blank">Open official source</a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def opportunity_matrix_fig(matrix: pd.DataFrame) -> go.Figure:
    """Bubble chart: materiality vs automation readiness."""
    frame = matrix.copy()
    frame["size"] = 28
    fig = px.scatter(
        frame,
        x="automation_readiness",
        y="materiality_score",
        text="bubble_label",
        color="risk_tier",
        color_discrete_map=RISK_COLORS,
        size="size",
        hover_data=["title", "change_id"],
        labels={
            "automation_readiness": "Automation readiness",
            "materiality_score": "Materiality",
        },
    )
    fig.update_traces(textposition="middle center", marker=dict(line=dict(width=1, color="white")))
    fig.add_vline(x=50, line_dash="dash", line_color="#c5c9d8")
    fig.add_hline(y=50, line_dash="dash", line_color="#c5c9d8")
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        xaxis=dict(range=[0, 105], title="Automation readiness"),
        yaxis=dict(range=[0, 105], title="Materiality"),
        legend_title_text="Risk tier",
    )
    return fig


def volume_bar_fig(per_change: list[dict[str, Any]]) -> go.Figure:
    frame = pd.DataFrame(per_change)
    frame = frame.sort_values("flagged_claims", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=frame["flagged_claims"],
            y=frame["short_label"],
            orientation="h",
            marker=dict(
                color=frame["flagged_claims"],
                colorscale=[[0, "#a99cff"], [1, "#5b4cdb"]],
                showscale=False,
            ),
            text=frame["flagged_claims"],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=30, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
        xaxis_title="Synthetic claims routed to review",
        yaxis_title="",
    )
    return fig


def monthly_trend_fig(trend: pd.DataFrame) -> go.Figure:
    fig = px.area(
        trend,
        x="month",
        y="review_events",
        markers=True,
        labels={"month": "Month of service", "review_events": "Review events"},
    )
    fig.update_traces(line_color=COLORS["accent"], fillcolor="rgba(91,76,219,0.18)")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10))
    return fig


def provider_bubble_fig(providers: pd.DataFrame) -> go.Figure:
    if providers.empty:
        fig = go.Figure()
        fig.update_layout(height=340, title="No provider concentration data")
        return fig
    fig = px.scatter(
        providers.head(40),
        x="review_events",
        y="paid_amount_in_scope",
        size="changes",
        color="specialty" if "specialty" in providers.columns else None,
        hover_name="provider_id",
        labels={
            "review_events": "Review events",
            "paid_amount_in_scope": "Paid amount in scope ($)",
        },
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10))
    return fig


def q3014_hist_fig(dist: pd.DataFrame) -> go.Figure:
    if dist.empty:
        fig = go.Figure()
        fig.update_layout(height=340, title="No Q3014 rows in scope")
        return fig
    fig = px.histogram(
        dist,
        x="allowed_amount",
        color="outside_tolerance",
        nbins=16,
        labels={"allowed_amount": "Allowed amount ($)", "outside_tolerance": "Outside ±$0.50"},
        color_discrete_map={True: COLORS["danger"], False: COLORS["ok"]},
    )
    fig.add_vline(x=31.85, line_dash="dash", line_color=COLORS["accent"])
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=10))
    return fig
