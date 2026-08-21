from __future__ import annotations

import pandas as pd

CS_OPERATIONS_COLUMNS = {
    "entry_date",
    "customer_type",
    "accounts",
    "onboarding_completed",
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
