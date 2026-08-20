import pandas as pd

from src.metrics import add_health_fields, calculate_health_score, filter_customers, portfolio_kpis


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
