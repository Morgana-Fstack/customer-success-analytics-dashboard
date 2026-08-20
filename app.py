from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.metrics import add_health_fields, filter_customers, portfolio_kpis

ROOT = Path(__file__).parent
COLORS = {"Healthy": "#22c55e", "At risk": "#f59e0b", "Critical": "#ef4444"}

st.set_page_config(page_title="Customer Success Analytics", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
      [data-testid="stMetric"] {background:#111827; border:1px solid #273244; padding:16px; border-radius:14px;}
      [data-testid="stMetricLabel"] {color:#a7b0c0;}
      .insight {background:#111827; border-left:4px solid #8b5cf6; padding:14px 16px; border-radius:8px; margin:8px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(ROOT / "data" / "customers.csv")
    history = pd.read_csv(ROOT / "data" / "monthly_history.csv", parse_dates=["month"])
    return add_health_fields(customers), history


def money(value: float) -> str:
    return f"${value:,.0f}"


customers, history = load_data()

with st.sidebar:
    st.title("Portfolio filters")
    selected_segments = st.multiselect("Segment", sorted(customers["segment"].unique()))
    selected_plans = st.multiselect("Plan", sorted(customers["plan"].unique()))
    selected_csms = st.multiselect("CSM owner", sorted(customers["csm"].unique()))
    st.divider()
    st.caption("Demo portfolio · Synthetic data")

filtered = filter_customers(customers, selected_segments, selected_plans, selected_csms)
kpis = portfolio_kpis(filtered)
active = filtered[filtered["status"] == "Active"]

st.title("Customer Success Analytics")
st.caption("Executive portfolio visibility for retention, revenue and proactive customer action")

tabs = st.tabs(["Executive overview", "Risk & retention", "Revenue", "Customer portfolio", "Methodology"])

with tabs[0]:
    cols = st.columns(5)
    cols[0].metric("Monthly recurring revenue", money(kpis["mrr"]))
    cols[1].metric("Annual recurring revenue", money(kpis["arr"]))
    cols[2].metric("Net revenue retention", f"{kpis['nrr']:.1%}")
    cols[3].metric("Logo churn", f"{kpis['logo_churn']:.1%}")
    cols[4].metric("Average health", f"{kpis['average_health']:.0f}/100")

    left, right = st.columns([1.65, 1])
    with left:
        fig = px.area(history, x="month", y="mrr", title="MRR evolution", markers=True)
        fig.update_traces(line_color="#8b5cf6", fillcolor="rgba(139,92,246,.18)")
        fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        health_counts = active["health_status"].value_counts().reindex(["Healthy", "At risk", "Critical"], fill_value=0)
        fig = px.pie(
            values=health_counts.values,
            names=health_counts.index,
            hole=0.64,
            title="Portfolio health",
            color=health_counts.index,
            color_discrete_map=COLORS,
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    critical = active[active["health_status"] == "Critical"]
    stale = active[active["days_since_last_contact"] > 30]
    renewal_risk = active[(active["renewal_days"] <= 60) & (active["health_score"] < 70)]
    st.subheader("Decision-ready insights")
    insight_cols = st.columns(3)
    insight_cols[0].markdown(
        f'<div class="insight"><b>{len(critical)} critical accounts</b><br>'
        f"{money(critical['mrr'].sum())} MRR requires immediate attention.</div>",
        unsafe_allow_html=True,
    )
    insight_cols[1].markdown(
        f'<div class="insight"><b>{len(stale)} accounts without recent contact</b><br>'
        "Last CSM touchpoint was over 30 days ago.</div>",
        unsafe_allow_html=True,
    )
    insight_cols[2].markdown(
        f'<div class="insight"><b>{len(renewal_risk)} risky renewals</b><br>'
        "Renewal is within 60 days and health is below 70.</div>",
        unsafe_allow_html=True,
    )

with tabs[1]:
    left, right = st.columns(2)
    with left:
        fig = px.scatter(
            active,
            x="health_score",
            y="mrr",
            size="contracted_seats",
            color="health_status",
            hover_name="customer_name",
            color_discrete_map=COLORS,
            title="Risk exposure by customer value",
            labels={"health_score": "Health score", "mrr": "MRR"},
        )
        fig.update_layout(yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        segment_health = (
            active.groupby(["segment", "health_status"], observed=True).size().reset_index(name="customers")
        )
        fig = px.bar(
            segment_health,
            x="segment",
            y="customers",
            color="health_status",
            barmode="stack",
            title="Health distribution by segment",
            color_discrete_map=COLORS,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Prioritized action queue")
    queue = active[active["health_score"] < 70].sort_values("priority_score", ascending=False)
    queue_columns = [
        "customer_name",
        "segment",
        "csm",
        "mrr",
        "health_score",
        "health_status",
        "renewal_days",
        "days_since_last_contact",
        "open_tickets",
        "priority_score",
    ]
    st.dataframe(
        queue[queue_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "mrr": st.column_config.NumberColumn("MRR", format="$%d"),
            "health_score": st.column_config.ProgressColumn("Health", min_value=0, max_value=100),
            "renewal_days": "Days to renewal",
            "days_since_last_contact": "Days since contact",
            "priority_score": st.column_config.NumberColumn("Priority", format="%.1f"),
        },
    )

with tabs[2]:
    cols = st.columns(4)
    latest = history.iloc[-1]
    cols[0].metric("Current portfolio MRR", money(kpis["mrr"]))
    cols[1].metric("MRR exposed to risk", money(kpis["at_risk_mrr"]))
    cols[2].metric("Gross revenue retention", f"{kpis['grr']:.1%}")
    cols[3].metric("Latest monthly churn", money(latest["churned_mrr"]))
    waterfall = go.Figure(
        go.Waterfall(
            x=["Opening MRR", "New", "Expansion", "Contraction", "Churn", "Closing MRR"],
            y=[
                history.iloc[-2]["mrr"],
                latest["new_mrr"],
                latest["expansion_mrr"],
                -latest["contraction_mrr"],
                -latest["churned_mrr"],
                0,
            ],
            measure=["absolute", "relative", "relative", "relative", "relative", "total"],
            increasing={"marker": {"color": "#22c55e"}},
            decreasing={"marker": {"color": "#ef4444"}},
            totals={"marker": {"color": "#8b5cf6"}},
        )
    )
    waterfall.update_layout(title="Latest month MRR movement", yaxis_tickprefix="$", showlegend=False)
    st.plotly_chart(waterfall, use_container_width=True)

with tabs[3]:
    search = st.text_input("Search customer", placeholder="Company name or customer ID")
    table = filtered.copy()
    if search:
        name_match = table["customer_name"].str.contains(search, case=False, na=False)
        id_match = table["customer_id"].str.contains(search, case=False, na=False)
        mask = name_match | id_match
        table = table[mask]
    portfolio_columns = [
        "customer_id",
        "customer_name",
        "segment",
        "plan",
        "csm",
        "status",
        "mrr",
        "health_score",
        "health_status",
        "renewal_days",
    ]
    st.dataframe(
        table[portfolio_columns].sort_values("health_score"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "mrr": st.column_config.NumberColumn("MRR", format="$%d"),
            "health_score": st.column_config.ProgressColumn("Health", min_value=0, max_value=100),
        },
    )
    st.download_button("Download filtered portfolio", table.to_csv(index=False), "cs_portfolio.csv", "text/csv")

with tabs[4]:
    st.subheader("How the health score works")
    st.markdown(
        """
        The health score is a transparent 0–100 weighted model:

        - **35% Product adoption:** monthly active users ÷ contracted seats
        - **25% Feature adoption:** percentage of strategic features used
        - **20% Relationship:** recency of the last CSM interaction
        - **20% Support experience:** CSAT adjusted by open ticket volume

        **Healthy:** 70–100 · **At risk:** 50–69 · **Critical:** 0–49

        The action queue combines risk, account value and renewal proximity.
        All data in this project is synthetic and contains no real customer information.
        """
    )
