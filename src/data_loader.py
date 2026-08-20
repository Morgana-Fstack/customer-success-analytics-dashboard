from __future__ import annotations

import pandas as pd

REQUIRED_CUSTOMER_COLUMNS = [
    "customer_id",
    "customer_name",
    "segment",
    "plan",
    "csm",
    "status",
    "starting_mrr",
    "mrr",
    "expansion_mrr",
    "contraction_mrr",
    "contracted_seats",
    "monthly_active_users",
    "feature_adoption_pct",
    "days_since_last_contact",
    "open_tickets",
    "csat_score",
    "renewal_days",
]

NUMERIC_CUSTOMER_COLUMNS = [
    "starting_mrr",
    "mrr",
    "expansion_mrr",
    "contraction_mrr",
    "contracted_seats",
    "monthly_active_users",
    "feature_adoption_pct",
    "days_since_last_contact",
    "open_tickets",
    "csat_score",
    "renewal_days",
]

STATUS_ALIASES = {
    "active": "Active",
    "ativo": "Active",
    "churned": "Churned",
    "cancelado": "Churned",
}


class CustomerDataError(ValueError):
    def __init__(self, code: str, details: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.details = details


def customer_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "customer_id": "CUST-0001",
                "customer_name": "Empresa Exemplo",
                "segment": "Mid-market",
                "plan": "Growth",
                "csm": "Ana Costa",
                "status": "Active",
                "starting_mrr": 2500,
                "mrr": 2750,
                "expansion_mrr": 250,
                "contraction_mrr": 0,
                "contracted_seats": 50,
                "monthly_active_users": 38,
                "feature_adoption_pct": 72,
                "days_since_last_contact": 12,
                "open_tickets": 1,
                "csat_score": 4.5,
                "renewal_days": 90,
            }
        ],
        columns=REQUIRED_CUSTOMER_COLUMNS,
    )


def prepare_uploaded_customers(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        raise CustomerDataError("empty")

    result = data.copy()
    result.columns = result.columns.str.strip()
    missing = [column for column in REQUIRED_CUSTOMER_COLUMNS if column not in result.columns]
    if missing:
        raise CustomerDataError("missing_columns", ", ".join(missing))

    result = result[REQUIRED_CUSTOMER_COLUMNS].copy()
    text_columns = ["customer_id", "customer_name", "segment", "plan", "csm", "status"]
    for column in text_columns:
        result[column] = result[column].astype(str).str.strip()
        if result[column].eq("").any():
            raise CustomerDataError("empty_values", column)

    if result["customer_id"].duplicated().any():
        raise CustomerDataError("duplicate_ids")

    normalized_status = result["status"].str.casefold().map(STATUS_ALIASES)
    if normalized_status.isna().any():
        invalid = sorted(result.loc[normalized_status.isna(), "status"].unique())
        raise CustomerDataError("invalid_status", ", ".join(invalid))
    result["status"] = normalized_status

    for column in NUMERIC_CUSTOMER_COLUMNS:
        converted = pd.to_numeric(result[column], errors="coerce")
        if converted.isna().any():
            raise CustomerDataError("invalid_numeric", column)
        result[column] = converted

    if (result[NUMERIC_CUSTOMER_COLUMNS] < 0).any().any():
        raise CustomerDataError("negative_values")
    if not result["feature_adoption_pct"].between(0, 100).all():
        raise CustomerDataError("invalid_feature_adoption")
    if not result["csat_score"].between(0, 5).all():
        raise CustomerDataError("invalid_csat")
    if (result["contracted_seats"] < 1).any():
        raise CustomerDataError("invalid_seats")

    return result
