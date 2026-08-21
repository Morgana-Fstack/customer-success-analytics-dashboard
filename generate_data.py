from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).parent / "data"
RNG = np.random.default_rng(42)


def _repeat_counts(counts: dict[str, int]) -> list[str]:
    return [label for label, count in counts.items() for _ in range(count)]


def build_cs_operations_data(size: int) -> dict[str, object]:
    """Build an anonymized operational portfolio based on the reference CS workbook."""
    if size != 136:
        raise ValueError("The CS operations reference portfolio contains 136 customers.")

    status = np.array(["Active"] * 72 + ["Churned"] * 64)

    active_types = _repeat_counts(
        {
            "Not informed": 4,
            "Agency": 5,
            "Individual": 36,
            "Internal": 7,
            "Mentorship": 3,
            "Multi-account": 1,
            "Partner/Affiliate": 5,
            "Potential multi-account": 4,
            "VIP": 7,
        }
    )
    churned_types = _repeat_counts(
        {
            "Not informed": 33,
            "Agency": 2,
            "Individual": 20,
            "Mentorship": 4,
            "Multi-account": 2,
            "Partner/Affiliate": 1,
            "Potential multi-account": 1,
            "VIP": 1,
        }
    )
    RNG.shuffle(active_types)
    RNG.shuffle(churned_types)
    customer_type = np.array(active_types + churned_types)

    active_onboarding = ["Yes"] * 54 + ["No"] * 18
    churned_onboarding = ["Yes"] * 25 + ["No"] * 37 + ["Unknown"] * 2
    RNG.shuffle(active_onboarding)
    RNG.shuffle(churned_onboarding)
    onboarding_completed = np.array(active_onboarding + churned_onboarding)

    cohorts = [(1, 6, 1), (2, 16, 11), (3, 24, 19), (4, 25, 17), (5, 27, 12), (6, 24, 3), (7, 12, 1)]

    def cohort_dates(churned: bool) -> list[pd.Timestamp]:
        dates: list[pd.Timestamp] = []
        for month, total, churn_count in cohorts:
            count = churn_count if churned else total - churn_count
            start = pd.Timestamp(year=2026, month=month, day=1)
            dates.extend(start + pd.to_timedelta(RNG.integers(0, 28, count), unit="D"))
        return dates

    active_entry_dates = cohort_dates(churned=False) + [pd.NaT, pd.NaT]
    churned_entry_dates = cohort_dates(churned=True)
    entry_date = pd.Series(active_entry_dates + churned_entry_dates, dtype="datetime64[ns]")

    cancellation_date = pd.Series(pd.NaT, index=range(size), dtype="datetime64[ns]")
    churned_mask = status == "Churned"
    cancellation_date.loc[churned_mask] = (
        entry_date[churned_mask] + pd.to_timedelta(RNG.integers(7, 91, churned_mask.sum()), unit="D")
    ).clip(upper=pd.Timestamp("2026-08-01"))

    onboarding_date = pd.Series(pd.NaT, index=range(size), dtype="datetime64[ns]")
    completed_mask = (onboarding_completed == "Yes") & entry_date.notna().to_numpy()
    onboarding_date.loc[completed_mask] = entry_date[completed_mask] + pd.to_timedelta(
        RNG.integers(3, 31, completed_mask.sum()), unit="D"
    )

    accounts = np.ones(size, dtype=int)
    account_candidates = np.flatnonzero(
        np.isin(customer_type, ["Agency", "Multi-account", "Potential multi-account"])
    )
    for index, increment in zip(account_candidates, [11, 3, 3, 3, 2, 2, 1, 1, 1], strict=False):
        accounts[index] += increment

    permutation = RNG.permutation(size)
    return {
        "status": status[permutation],
        "customer_type": customer_type[permutation],
        "accounts": accounts[permutation],
        "onboarding_completed": onboarding_completed[permutation],
        "entry_date": entry_date.iloc[permutation].reset_index(drop=True),
        "cancellation_date": cancellation_date.iloc[permutation].reset_index(drop=True),
        "onboarding_date": onboarding_date.iloc[permutation].reset_index(drop=True),
    }


def build_customers(size: int = 136) -> pd.DataFrame:
    operations = build_cs_operations_data(size)
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
    status = operations["status"]
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
            "entry_date": operations["entry_date"].dt.date.astype("string").fillna(""),
            "cancellation_date": operations["cancellation_date"].dt.date.astype("string").fillna(""),
            "customer_type": operations["customer_type"],
            "accounts": operations["accounts"],
            "onboarding_completed": operations["onboarding_completed"],
            "onboarding_date": operations["onboarding_date"].dt.date.astype("string").fillna(""),
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
