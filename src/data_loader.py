from __future__ import annotations

import pandas as pd

REQUIRED_CUSTOMER_COLUMNS = [
    "customer_id", "customer_name", "segment", "plan", "csm", "status",
    "starting_mrr", "mrr", "expansion_mrr", "contraction_mrr",
    "contracted_seats", "monthly_active_users", "feature_adoption_pct",
    "days_since_last_contact", "open_tickets", "csat_score", "renewal_days",
]

OPTIONAL_CS_COLUMNS = [
    "entry_date", "cancellation_date", "customer_type", "accounts",
    "onboarding_completed", "onboarding_date",
]

NUMERIC_CUSTOMER_COLUMNS = [
    "starting_mrr", "mrr", "expansion_mrr", "contraction_mrr",
    "contracted_seats", "monthly_active_users", "feature_adoption_pct",
    "days_since_last_contact", "open_tickets", "csat_score", "renewal_days",
]

REQUIRED_NUMERIC_VALUES = [
    "starting_mrr", "mrr", "contracted_seats", "monthly_active_users", "renewal_days",
]

SPARSE_ANALYTICS_COLUMNS = [
    "feature_adoption_pct", "days_since_last_contact", "open_tickets", "csat_score",
]

ZERO_DEFAULT_NUMERIC_COLUMNS = ["expansion_mrr", "contraction_mrr"]

STATUS_ALIASES = {
    "active": "Active", "ativo": "Active", "mensal": "Active",
    "churned": "Churned", "cancelado": "Churned", "desistencia": "Churned",
    "desistência": "Churned", "inativo": "Churned",
}

ONBOARDING_ALIASES = {
    "yes": "Yes", "sim": "Yes", "true": "Yes", "1": "Yes", "completed": "Yes",
    "concluido": "Yes", "concluído": "Yes", "no": "No", "nao": "No", "não": "No",
    "false": "No", "0": "No", "pending": "No", "pendente": "No", "unknown": "Unknown",
    "not informed": "Unknown", "nao informado": "Unknown", "não informado": "Unknown",
}


class CustomerDataError(ValueError):
    def __init__(self, code: str, details: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.details = details


def customer_template() -> pd.DataFrame:
    return pd.DataFrame([{
        "customer_id": "CUST-0001", "customer_name": "Empresa Exemplo", "segment": "Agência",
        "plan": "Mensal", "csm": "Não informado", "status": "Ativo", "starting_mrr": 2500,
        "mrr": 2750, "expansion_mrr": 250, "contraction_mrr": 0, "contracted_seats": 50,
        "monthly_active_users": 38, "feature_adoption_pct": 72, "days_since_last_contact": 12,
        "open_tickets": 1, "csat_score": 4.5, "renewal_days": 90,
    }], columns=REQUIRED_CUSTOMER_COLUMNS)


def _normalize_renewal_days(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    unresolved = numeric.isna() & values.notna() & values.astype(str).str.strip().ne("")
    if unresolved.any():
        parsed_dates = pd.to_datetime(values[unresolved], errors="coerce", dayfirst=True)
        if parsed_dates.isna().any():
            raise CustomerDataError("invalid_numeric", "renewal_days")
        today = pd.Timestamp.today().normalize()
        numeric.loc[unresolved] = (parsed_dates.dt.normalize() - today).dt.days.clip(lower=0)
    return numeric


def prepare_uploaded_customers(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        raise CustomerDataError("empty")

    result = data.copy()
    result.columns = result.columns.str.strip().str.lstrip("\ufeff")
    missing = [column for column in REQUIRED_CUSTOMER_COLUMNS if column not in result.columns]
    if missing:
        raise CustomerDataError("missing_columns", ", ".join(missing))

    optional_columns = [column for column in OPTIONAL_CS_COLUMNS if column in result.columns]
    result = result[REQUIRED_CUSTOMER_COLUMNS + optional_columns].copy()

    for column in ["customer_id", "customer_name", "segment", "status"]:
        result[column] = result[column].fillna("").astype(str).str.strip()
        if result[column].eq("").any():
            raise CustomerDataError("empty_values", column)

    for column in ["plan", "csm"]:
        result[column] = result[column].fillna("").astype(str).str.strip().replace("", "Não informado")

    if result["customer_id"].duplicated().any():
        raise CustomerDataError("duplicate_ids")

    normalized_status = result["status"].str.casefold().map(STATUS_ALIASES)
    if normalized_status.isna().any():
        invalid = sorted(result.loc[normalized_status.isna(), "status"].unique())
        raise CustomerDataError("invalid_status", ", ".join(invalid))
    result["status"] = normalized_status

    for column in ZERO_DEFAULT_NUMERIC_COLUMNS:
        empty = result[column].isna() | result[column].astype(str).str.strip().eq("")
        result.loc[empty, column] = 0

    for column in NUMERIC_CUSTOMER_COLUMNS:
        converted = (
            _normalize_renewal_days(result[column])
            if column == "renewal_days"
            else pd.to_numeric(result[column], errors="coerce")
        )
        if column in REQUIRED_NUMERIC_VALUES and converted.isna().any():
            raise CustomerDataError("invalid_numeric", column)
        result[column] = converted

    if (result[REQUIRED_NUMERIC_VALUES + ZERO_DEFAULT_NUMERIC_COLUMNS] < 0).any().any():
        raise CustomerDataError("negative_values")
    for column in SPARSE_ANALYTICS_COLUMNS:
        if (result[column].dropna() < 0).any():
            raise CustomerDataError("negative_values")
    if not result["feature_adoption_pct"].dropna().between(0, 100).all():
        raise CustomerDataError("invalid_feature_adoption")
    if not result["csat_score"].dropna().between(0, 5).all():
        raise CustomerDataError("invalid_csat")
    if (result["contracted_seats"] < 1).any():
        raise CustomerDataError("invalid_seats")

    if "accounts" in result.columns:
        accounts = pd.to_numeric(result["accounts"], errors="coerce")
        if accounts.isna().any() or (accounts < 1).any():
            raise CustomerDataError("invalid_accounts")
        result["accounts"] = accounts.astype(int)
    if "customer_type" in result.columns:
        result["customer_type"] = result["customer_type"].fillna("").astype(str).str.strip().replace("", "Not informed")
    if "onboarding_completed" in result.columns:
        raw = result["onboarding_completed"].fillna("Unknown").astype(str).str.strip()
        normalized = raw.str.casefold().map(ONBOARDING_ALIASES)
        if normalized.isna().any():
            invalid = sorted(raw[normalized.isna()].unique())
            raise CustomerDataError("invalid_onboarding", ", ".join(invalid))
        result["onboarding_completed"] = normalized
    for column in ["entry_date", "cancellation_date", "onboarding_date"]:
        if column in result.columns:
            raw_dates = result[column].replace("", pd.NA)
            parsed = pd.to_datetime(raw_dates, errors="coerce")
            if (raw_dates.notna() & parsed.isna()).any():
                raise CustomerDataError("invalid_date", column)
            result[column] = parsed

    return result
