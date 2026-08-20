import pandas as pd
import pytest

from src.data_loader import CustomerDataError, customer_template, prepare_uploaded_customers


def test_template_is_a_valid_upload() -> None:
    result = prepare_uploaded_customers(customer_template())
    assert len(result) == 1
    assert result.iloc[0]["customer_id"] == "CUST-0001"


def test_portuguese_status_is_normalized() -> None:
    data = customer_template()
    data.loc[0, "status"] = "Ativo"
    result = prepare_uploaded_customers(data)
    assert result.iloc[0]["status"] == "Active"


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


def test_duplicate_customer_id_is_rejected() -> None:
    data = pd.concat([customer_template(), customer_template()], ignore_index=True)
    with pytest.raises(CustomerDataError, match="duplicate_ids"):
        prepare_uploaded_customers(data)
