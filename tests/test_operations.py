import pandas as pd

from src.data_loader import customer_template, prepare_uploaded_customers
from src.operations import churn_breakdown, churn_by_cohort, cs_operations_kpis, has_cs_operations_data


def operational_portfolio() -> pd.DataFrame:
    rows = []
    for customer_id, status, onboarding, customer_type, entry_date, accounts in [
        ("CUST-0001", "Active", "Yes", "Individual", "2026-01-10", 1),
        ("CUST-0002", "Churned", "No", "Agency", "2026-01-18", 2),
        ("CUST-0003", "Active", "No", "Agency", "2026-02-05", 3),
        ("CUST-0004", "Churned", "Yes", "Individual", "2026-02-20", 1),
    ]:
        row = customer_template().iloc[0].copy()
        row["customer_id"] = customer_id
        row["status"] = status
        row["onboarding_completed"] = onboarding
        row["customer_type"] = customer_type
        row["entry_date"] = entry_date
        row["accounts"] = accounts
        rows.append(row)
    return prepare_uploaded_customers(pd.DataFrame(rows))


def test_has_cs_operations_data_requires_operational_columns() -> None:
    portfolio = operational_portfolio()
    assert has_cs_operations_data(portfolio)
    assert not has_cs_operations_data(portfolio.drop(columns=["onboarding_completed"]))


def test_cs_operations_kpis_calculate_portfolio_rates() -> None:
    result = cs_operations_kpis(operational_portfolio())

    assert result["total_customers"] == 4
    assert result["active_customers"] == 2
    assert result["churned_customers"] == 2
    assert result["total_accounts"] == 7
    assert result["active_rate"] == 0.5
    assert result["churn_rate"] == 0.5
    assert result["onboarding_rate"] == 0.5


def test_churn_breakdown_groups_by_dimension() -> None:
    result = churn_breakdown(operational_portfolio(), "customer_type")
    agency = result[result["customer_type"] == "Agency"].iloc[0]
    individual = result[result["customer_type"] == "Individual"].iloc[0]

    assert agency["total"] == 2
    assert agency["churned"] == 1
    assert agency["churn_rate"] == 0.5
    assert individual["total"] == 2
    assert individual["churned"] == 1


def test_churn_by_cohort_uses_entry_month() -> None:
    result = churn_by_cohort(operational_portfolio())

    january = result[result["cohort"] == "2026-01"].iloc[0]
    february = result[result["cohort"] == "2026-02"].iloc[0]
    assert january["total"] == 2
    assert january["churn_rate"] == 0.5
    assert february["total"] == 2
    assert february["churn_rate"] == 0.5


def test_breakdowns_return_empty_frames_when_dimension_or_dates_are_missing() -> None:
    portfolio = operational_portfolio()

    missing_dimension = churn_breakdown(portfolio, "missing_column")
    missing_dates = churn_by_cohort(portfolio.drop(columns=["entry_date"]))

    assert missing_dimension.empty
    assert missing_dates.empty
