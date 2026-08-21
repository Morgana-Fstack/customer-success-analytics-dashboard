import pandas as pd
import pytest

from src.data_loader import (
    OPTIONAL_CS_COLUMNS,
    REQUIRED_CUSTOMER_COLUMNS,
    CustomerDataError,
    customer_template,
    prepare_uploaded_customers,
)


def test_template_matches_official_source_schema() -> None:
    template = customer_template()
    assert list(template.columns) == REQUIRED_CUSTOMER_COLUMNS
    assert len(template.columns) == 17
    assert not set(OPTIONAL_CS_COLUMNS).intersection(template.columns)


def test_template_is_a_valid_upload() -> None:
    result = prepare_uploaded_customers(customer_template())
    assert len(result) == 1
    assert result.iloc[0]["customer_id"] == "CUST-0001"


def test_sparse_production_style_row_is_accepted() -> None:
    data = customer_template()
    data.loc[0, "plan"] = None
    data.loc[0, "csm"] = None
    data.loc[0, "expansion_mrr"] = None
    data.loc[0, "contraction_mrr"] = None
    for column in ["feature_adoption_pct", "days_since_last_contact", "open_tickets", "csat_score"]:
        data.loc[0, column] = None

    result = prepare_uploaded_customers(data)

    assert result.iloc[0]["plan"] == "Não informado"
    assert result.iloc[0]["csm"] == "Não informado"
    assert result.iloc[0]["expansion_mrr"] == 0
    assert result.iloc[0]["contraction_mrr"] == 0
    assert pd.isna(result.iloc[0]["csat_score"])


def test_portuguese_status_is_normalized() -> None:
    data = customer_template()
    data.loc[0, "status"] = "Ativo"
    result = prepare_uploaded_customers(data)
    assert result.iloc[0]["status"] == "Active"


def test_operational_statuses_are_normalized() -> None:
    expected = {
        "Desistencia": "Churned",
        "Desistência": "Churned",
        "Inativo": "Churned",
        "Mensal": "Active",
    }
    for raw_status, normalized_status in expected.items():
        data = customer_template()
        data.loc[0, "status"] = raw_status
        result = prepare_uploaded_customers(data)
        assert result.iloc[0]["status"] == normalized_status


def test_missing_column_is_rejected() -> None:
    data = customer_template().drop(columns=["csat_score"])
    with pytest.raises(CustomerDataError, match="missing_columns"):
        prepare_uploaded_customers(data)


def test_invalid_numeric_value_is_rejected() -> None:
    data = customer_template()
    data["mrr"] = data["mrr"].astype(object)
    data.loc[0, "mrr"] = "not-a-number"
    with pytest.raises(CustomerDataError, match="invalid_numeric"):
        prepare_uploaded_customers(data)


def test_empty_revenue_movements_default_to_zero() -> None:
    data = customer_template()
    data["expansion_mrr"] = None
    data["contraction_mrr"] = "  "
    result = prepare_uploaded_customers(data)
    assert result.iloc[0]["expansion_mrr"] == 0
    assert result.iloc[0]["contraction_mrr"] == 0


def test_duplicate_customer_id_is_rejected() -> None:
    data = pd.concat([customer_template(), customer_template()], ignore_index=True)
    with pytest.raises(CustomerDataError, match="duplicate_ids"):
        prepare_uploaded_customers(data)


def test_utf8_bom_is_removed_from_first_header() -> None:
    data = customer_template().rename(columns={"customer_id": "\ufeffcustomer_id"})
    result = prepare_uploaded_customers(data)
    assert "customer_id" in result.columns


def test_optional_legacy_fields_remain_supported() -> None:
    data = customer_template().assign(
        entry_date="2026-01-15",
        cancellation_date="",
        customer_type="Individual",
        accounts=1,
        onboarding_completed="Sim",
        onboarding_date="2026-01-27",
    )
    result = prepare_uploaded_customers(data)
    assert result.iloc[0]["onboarding_completed"] == "Yes"
    assert result.iloc[0]["accounts"] == 1
    assert pd.api.types.is_datetime64_any_dtype(result["entry_date"])


def test_invalid_optional_date_is_rejected() -> None:
    data = customer_template().assign(entry_date="not-a-date")
    with pytest.raises(CustomerDataError, match="invalid_date"):
        prepare_uploaded_customers(data)
