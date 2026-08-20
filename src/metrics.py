from __future__ import annotations

import pandas as pd

HEALTH_WEIGHTS = {
    "product_adoption": 0.35,
    "engagement": 0.25,
    "relationship": 0.20,
    "support_experience": 0.20,
}


def calculate_health_score(customers: pd.DataFrame) -> pd.Series:
    """Calculate a transparent 0–100 customer health score."""
    adoption = customers["monthly_active_users"].div(customers["contracted_seats"].clip(lower=1)).clip(upper=1) * 100
    engagement = customers["feature_adoption_pct"].clip(0, 100)
    relationship = (100 - customers["days_since_last_contact"] * 2).clip(0, 100)
    support = (customers["csat_score"].div(5).mul(100) - customers["open_tickets"].mul(8)).clip(0, 100)

    score = (
        adoption * HEALTH_WEIGHTS["product_adoption"]
        + engagement * HEALTH_WEIGHTS["engagement"]
        + relationship * HEALTH_WEIGHTS["relationship"]
        + support * HEALTH_WEIGHTS["support_experience"]
    )
    return score.round().astype(int)


def add_health_fields(customers: pd.DataFrame) -> pd.DataFrame:
    result = customers.copy()
    result["health_score"] = calculate_health_score(result)
    result["health_status"] = pd.cut(
        result["health_score"],
        bins=[-1, 49, 69, 100],
        labels=["Critical", "At risk", "Healthy"],
    ).astype(str)
    result["priority_score"] = (
        (100 - result["health_score"]) * 0.65
        + result["mrr"].rank(pct=True).mul(100) * 0.25
        + result["renewal_days"].le(60).astype(int) * 10
    ).round(1)
    return result


def portfolio_kpis(customers: pd.DataFrame) -> dict[str, float]:
    active = customers[customers["status"] == "Active"]
    starting_mrr = customers["starting_mrr"].sum()
    churned_mrr = customers.loc[customers["status"] == "Churned", "starting_mrr"].sum()
    current_mrr = active["mrr"].sum()
    expansion = active["expansion_mrr"].sum()
    contraction = active["contraction_mrr"].sum()

    gross_revenue_retention = (starting_mrr - churned_mrr - contraction) / starting_mrr if starting_mrr else 0
    net_revenue_retention = (starting_mrr - churned_mrr - contraction + expansion) / starting_mrr if starting_mrr else 0
    return {
        "active_customers": float(len(active)),
        "mrr": float(current_mrr),
        "arr": float(current_mrr * 12),
        "logo_churn": float((customers["status"] == "Churned").mean()),
        "grr": float(gross_revenue_retention),
        "nrr": float(net_revenue_retention),
        "at_risk_mrr": float(active.loc[active["health_score"] < 70, "mrr"].sum()),
        "average_health": float(active["health_score"].mean()) if len(active) else 0,
    }


def filter_customers(
    customers: pd.DataFrame,
    segments: list[str] | None = None,
    plans: list[str] | None = None,
    csms: list[str] | None = None,
) -> pd.DataFrame:
    result = customers.copy()
    if segments:
        result = result[result["segment"].isin(segments)]
    if plans:
        result = result[result["plan"].isin(plans)]
    if csms:
        result = result[result["csm"].isin(csms)]
    return result
