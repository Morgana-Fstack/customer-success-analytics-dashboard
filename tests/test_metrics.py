import pandas as pd

from src.metrics import (
    add_health_fields,
    calculate_health_score,
    filter_customers,
    portfolio_kpis,
)
from src.operations import churn_breakdown, churn_by_cohort, cs_operations_kpis, has_cs_operations_data


def sample_customers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_name": ["Healthy Co", "Risky Co", "Lost Co"],
            "segment": ["SMB", "Enterprise", "SMB"],
            "plan": ["Starter", "Scale", "Starter"],
            "csm": ["Ana", "Bruno", "Ana"],
            "status": ["Active", "Active", "Churned"],
            "starting_mrr": [1000, 3000, 500],
            "mrr": [1200, 2700, 0],
            "expansion_mrr": [200, 0, 0],
            "contraction_mrr": [0, 300, 0],
            "contracted_seats": [10, 100, 10],
            "monthly_active_users": [10, 20, 2],
            "feature_adoption_pct": [90, 30, 20],
            "days_since_last_contact": [5, 50, 80],
            "open_tickets": [0, 5, 4],
            "csat_score": [5.0, 2.5, 2.0],
            "renewal_days": [100, 30, 200],
        }
    )


def test_health_score_stays_within_range() -> None:
    score = calculate_health_score(sample_customers())
    assert score.between(0, 100).all()


def test_healthy_customer_scores_higher_than_risky_customer() -> None:
    scored = add_health_fields(sample_customers())
    assert scored.iloc[0]["health_score"] > scored.iloc[1]["health_score"]
    assert scored.iloc[0]["health_status"] == "Healthy"


def test_portfolio_kpis_use_only_active_mrr() -> None:
    scored = add_health_fields(sample_customers())
    kpis = portfolio_kpis(scored)
    assert kpis["active_customers"] == 2
    assert kpis["mrr"] == 3900
    assert kpis["arr"] == 46800


def test_filters_can_be_combined() -> None:
    result = filter_customers(sample_customers(), segments=["SMB"], csms=["Ana"])
    assert len(result) == 2
    assert set(result["segment"]) == {"SMB"}


def operational_customers() -> pd.DataFrame:
    data = sample_customers()
    data["entry_date"] = pd.to_datetime(["2026-01-10", "2026-01-20", "2026-02-05"])
    data["customer_type"] = ["Individual", "Agency", "Individual"]
    data["accounts"] = [1, 2, 1]
    data["onboarding_completed"] = ["Yes", "No", "No"]
    return data


def test_cs_operations_kpis_reconcile_portfolio() -> None:
    customers = operational_customers()
    assert has_cs_operations_data(customers)
    kpis = cs_operations_kpis(customers)
    assert kpis["total_customers"] == 3
    assert kpis["active_customers"] == 2
    assert kpis["churned_customers"] == 1
    assert kpis["total_accounts"] == 4
    assert kpis["onboarding_rate"] == 1 / 3


def test_churn_breakdown_keeps_all_onboarding_groups() -> None:
    breakdown = churn_breakdown(operational_customers(), "onboarding_completed")
    assert breakdown["total"].sum() == 3
    no_onboarding = breakdown.loc[breakdown["onboarding_completed"] == "No"].iloc[0]
    assert no_onboarding["churn_rate"] == 0.5


def test_churn_by_cohort_excludes_missing_entry_dates() -> None:
    customers = operational_customers()
    customers.loc[2, "entry_date"] = pd.NaT
    cohort = churn_by_cohort(customers)
    assert cohort["total"].sum() == 2
    assert cohort.iloc[0]["cohort"] == "2026-01"
