from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).parent / "data"
RNG = np.random.default_rng(42)


def build_customers(size: int = 180) -> pd.DataFrame:
    plans = RNG.choice(["Starter", "Growth", "Scale"], size=size, p=[0.43, 0.39, 0.18])
    segments = np.select([plans == "Starter", plans == "Growth"], ["SMB", "Mid-market"], default="Enterprise")
    starting_mrr = np.array(
        [
            RNG.integers(300, 900)
            if p == "Starter"
            else RNG.integers(900, 3500)
            if p == "Growth"
            else RNG.integers(3500, 12000)
            for p in plans
        ]
    )
    seats = np.array(
        [
            RNG.integers(5, 25) if p == "Starter" else RNG.integers(20, 100) if p == "Growth" else RNG.integers(80, 400)
            for p in plans
        ]
    )
    adoption = RNG.beta(4, 2.2, size)
    mau = np.maximum(1, (seats * adoption * RNG.uniform(0.8, 1.1, size)).astype(int))
    feature_adoption = np.clip((adoption * 100 + RNG.normal(0, 9, size)), 5, 100).round(1)
    last_contact = np.maximum(1, (RNG.gamma(2.2, 9, size) + (1 - adoption) * 24).astype(int))
    tickets = RNG.poisson(1.4 + (1 - adoption) * 2.4, size)
    csat = np.clip(3.1 + adoption * 1.8 + RNG.normal(0, 0.35, size), 1, 5).round(1)
    onboarding_completed = RNG.random(size) < (0.62 + adoption * 0.32)
    churn_probability = (
        0.03
        + (1 - adoption) * 0.12
        + (~onboarding_completed) * 0.35
        + (last_contact > 35) * 0.10
        + (csat < 3.6) * 0.08
    )
    status = np.where(RNG.random(size) < churn_probability, "Churned", "Active")
    expansion = np.where(
        (adoption > 0.78) & (status == "Active"),
        (starting_mrr * RNG.uniform(0.05, 0.25, size)).astype(int),
        0,
    )
    contraction = np.where(
        (adoption < 0.38) & (status == "Active"),
        (starting_mrr * RNG.uniform(0.05, 0.18, size)).astype(int),
        0,
    )
    mrr = np.where(status == "Active", starting_mrr + expansion - contraction, 0)
    entry_date = pd.to_datetime("2024-01-01") + pd.to_timedelta(RNG.integers(0, 883, size), unit="D")
    cancellation_delay = pd.to_timedelta(RNG.integers(45, 540, size), unit="D")
    cancellation_date = pd.Series(pd.NaT, index=range(size), dtype="datetime64[ns]")
    cancellation_date.loc[status == "Churned"] = (
        pd.Series(entry_date)[status == "Churned"] + cancellation_delay[status == "Churned"]
    ).clip(upper=pd.Timestamp("2026-08-01"))
    onboarding_date = pd.Series(pd.NaT, index=range(size), dtype="datetime64[ns]")
    onboarding_date.loc[onboarding_completed] = (
        pd.Series(entry_date)[onboarding_completed]
        + pd.to_timedelta(RNG.integers(3, 31, onboarding_completed.sum()), unit="D")
    )
    customer_type = RNG.choice(
        ["Individual", "Agency", "Partner", "Multi-account", "VIP"],
        size=size,
        p=[0.55, 0.16, 0.10, 0.12, 0.07],
    )
    accounts = np.where(customer_type == "Multi-account", RNG.integers(2, 8, size), 1)

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:04d}" for i in range(1, size + 1)],
            "customer_name": [f"Company {i:03d}" for i in range(1, size + 1)],
            "segment": segments,
            "plan": plans,
            "csm": RNG.choice(["Ana Costa", "Bruno Lima", "Carla Souza", "Diego Alves"], size),
            "status": status,
            "starting_mrr": starting_mrr,
            "mrr": mrr,
            "expansion_mrr": expansion,
            "contraction_mrr": contraction,
            "contracted_seats": seats,
            "monthly_active_users": mau,
            "feature_adoption_pct": feature_adoption,
            "days_since_last_contact": last_contact,
            "open_tickets": tickets,
            "csat_score": csat,
            "renewal_days": RNG.integers(7, 366, size),
            "tenure_months": RNG.integers(2, 49, size),
            "entry_date": pd.Series(entry_date).dt.date.astype(str),
            "cancellation_date": cancellation_date.dt.date.astype("string").fillna(""),
            "customer_type": customer_type,
            "accounts": accounts,
            "onboarding_completed": np.where(onboarding_completed, "Yes", "No"),
            "onboarding_date": onboarding_date.dt.date.astype("string").fillna(""),
        }
    )


def build_monthly_history(customers: pd.DataFrame) -> pd.DataFrame:
    months = pd.date_range("2025-01-01", periods=18, freq="MS")
    initial = customers["starting_mrr"].sum() * 0.76
    rows: list[dict[str, object]] = []
    mrr = initial
    active = int(len(customers) * 0.78)
    for index, month in enumerate(months):
        new_mrr = int(RNG.integers(9000, 19000) * (1 + index / 60))
        expansion = int(RNG.integers(3000, 10000))
        churn = int(RNG.integers(2500, 8500))
        contraction = int(RNG.integers(800, 3500))
        mrr = max(0, mrr + new_mrr + expansion - churn - contraction)
        new_customers = int(RNG.integers(5, 13))
        churned_customers = int(RNG.integers(1, 7))
        active += new_customers - churned_customers
        rows.append(
            {
                "month": month.date().isoformat(),
                "mrr": round(mrr),
                "new_mrr": new_mrr,
                "expansion_mrr": expansion,
                "churned_mrr": churn,
                "contraction_mrr": contraction,
                "active_customers": active,
                "new_customers": new_customers,
                "churned_customers": churned_customers,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    customer_data = build_customers()
    customer_data.to_csv(OUTPUT_DIR / "customers.csv", index=False)
    build_monthly_history(customer_data).to_csv(OUTPUT_DIR / "monthly_history.csv", index=False)
    print(f"Generated {len(customer_data)} customers and 18 months of history.")
