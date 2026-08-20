from __future__ import annotations

import pandas as pd

HEALTH_WEIGHTS = {
    "product_adoption": 0.35,
    "engagement": 0.25,
    "relationship": 0.20,
    "support_experience": 0.20,
}

CS_OPERATIONS_COLUMNS = {
    "entry_date",
    "customer_type",
    "accounts",
    "onboarding_completed",
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


def has_cs_operations_data(customers: pd.DataFrame) -> bool:
    """Return whether the portfolio contains the fields used by the CS operations view."""
    return CS_OPERATIONS_COLUMNS.issubset(customers.columns)


def cs_operations_kpis(customers: pd.DataFrame) -> dict[str, float]:
    """Calculate operational portfolio, onboarding and churn indicators."""
    total = len(customers)
    active = int(customers["status"].eq("Active").sum())
    churned = int(customers["status"].eq("Churned").sum())
    completed_onboarding = int(customers["onboarding_completed"].eq("Yes").sum())
    total_accounts = pd.to_numeric(customers["accounts"], errors="coerce").fillna(1).sum()

    return {
        "total_customers": float(total),
        "active_customers": float(active),
        "churned_customers": float(churned),
        "total_accounts": float(total_accounts),
        "active_rate": active / total if total else 0.0,
        "churn_rate": churned / total if total else 0.0,
        "onboarding_rate": completed_onboarding / total if total else 0.0,
    }


def churn_breakdown(customers: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Group total customers and churn rate by one operational dimension."""
    if dimension not in customers.columns:
        return pd.DataFrame(columns=[dimension, "total", "active", "churned", "churn_rate"])

    values = customers[dimension].fillna("Not informed").astype(str).replace("", "Not informed")
    grouped = (
        customers.assign(_dimension=values)
        .groupby("_dimension", dropna=False)["status"]
        .agg(
            total="size",
            active=lambda status: status.eq("Active").sum(),
            churned=lambda status: status.eq("Churned").sum(),
        )
        .reset_index()
        .rename(columns={"_dimension": dimension})
    )
    grouped["churn_rate"] = grouped["churned"].div(grouped["total"]).fillna(0)
    return grouped.sort_values("churn_rate", ascending=False).reset_index(drop=True)


def churn_by_cohort(customers: pd.DataFrame) -> pd.DataFrame:
    """Calculate churn by customer entry month, excluding missing entry dates."""
    if "entry_date" not in customers.columns:
        return pd.DataFrame(columns=["cohort", "total", "active", "churned", "churn_rate"])

    dated = customers.dropna(subset=["entry_date"]).copy()
    if dated.empty:
        return pd.DataFrame(columns=["cohort", "total", "active", "churned", "churn_rate"])

    dated["cohort"] = pd.to_datetime(dated["entry_date"]).dt.to_period("M").astype(str)
    grouped = (
        dated.groupby("cohort")["status"]
        .agg(
            total="size",
            active=lambda status: status.eq("Active").sum(),
            churned=lambda status: status.eq("Churned").sum(),
        )
        .reset_index()
    )
    grouped["churn_rate"] = grouped["churned"].div(grouped["total"]).fillna(0)
    return grouped


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
