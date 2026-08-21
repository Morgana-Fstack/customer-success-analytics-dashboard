from generate_data import build_customers


def test_demo_portfolio_matches_cs_operations_reference() -> None:
    customers = build_customers()

    assert len(customers) == 136
    assert customers["status"].value_counts().to_dict() == {"Active": 72, "Churned": 64}
    assert customers["accounts"].sum() == 163
    assert customers["onboarding_completed"].value_counts().to_dict() == {"Yes": 79, "No": 55, "Unknown": 2}

    onboarding_churn = customers.groupby("onboarding_completed")["status"].apply(
        lambda status: status.eq("Churned").sum()
    )
    assert onboarding_churn.to_dict() == {"No": 37, "Unknown": 2, "Yes": 25}


def test_demo_customer_names_are_anonymized() -> None:
    customers = build_customers()
    assert customers["customer_name"].str.fullmatch(r"Company \d{3}").all()
