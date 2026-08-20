from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import CustomerDataError, customer_template, prepare_uploaded_customers
from src.metrics import add_health_fields, filter_customers, portfolio_kpis

ROOT = Path(__file__).parent
HEALTH_ORDER = ["Healthy", "At risk", "Critical"]
HEALTH_COLORS = {"Healthy": "#22c55e", "At risk": "#f59e0b", "Critical": "#ef4444"}

TRANSLATIONS = {
    "pt": {
        "filters": "Filtros da carteira",
        "segment": "Segmento",
        "plan": "Plano",
        "csm": "Responsável CSM",
        "demo": "Carteira demonstrativa · Dados sintéticos",
        "title": "Análise de Customer Success",
        "subtitle": "Visão executiva da carteira para retenção, receita e ações proativas com clientes",
        "tabs": ["Visão executiva", "Risco e retenção", "Receita", "Carteira de clientes", "Metodologia"],
        "mrr": "Receita recorrente mensal",
        "arr": "Receita recorrente anual",
        "nrr": "Retenção líquida de receita",
        "logo_churn": "Churn de clientes",
        "average_health": "Saúde média",
        "mrr_evolution": "Evolução do MRR",
        "month": "Mês",
        "portfolio_health": "Saúde da carteira",
        "health_status": "Status de saúde",
        "healthy": "Saudável",
        "at_risk": "Em risco",
        "critical": "Crítico",
        "insights": "Insights para tomada de decisão",
        "critical_accounts": "contas críticas",
        "critical_detail": "de MRR requer atenção imediata.",
        "stale_accounts": "contas sem contato recente",
        "stale_detail": "O último contato do CSM ocorreu há mais de 30 dias.",
        "risky_renewals": "renovações em risco",
        "renewal_detail": "A renovação ocorrerá em até 60 dias e a saúde está abaixo de 70.",
        "risk_exposure": "Exposição ao risco por valor do cliente",
        "health_score": "Health score",
        "contracted_seats": "Licenças contratadas",
        "customer_name": "Cliente",
        "health_by_segment": "Distribuição da saúde por segmento",
        "customers": "Clientes",
        "action_queue": "Fila de ações priorizadas",
        "days_to_renewal": "Dias para renovação",
        "days_since_contact": "Dias desde o contato",
        "open_tickets": "Tickets abertos",
        "priority": "Prioridade",
        "current_mrr": "MRR atual da carteira",
        "risk_mrr": "MRR exposto a risco",
        "grr": "Retenção bruta de receita",
        "monthly_churn": "Churn do último mês",
        "opening_mrr": "MRR inicial",
        "new": "Novas receitas",
        "expansion": "Expansão",
        "contraction": "Contração",
        "churn": "Churn",
        "closing_mrr": "MRR final",
        "mrr_movement": "Movimentação do MRR no último mês",
        "search": "Buscar cliente",
        "search_placeholder": "Nome da empresa ou ID do cliente",
        "customer_id": "ID do cliente",
        "status": "Status",
        "renewal_days": "Dias para renovação",
        "download": "Baixar carteira filtrada",
        "data_source": "Fonte de dados",
        "upload": "Importar carteira em CSV",
        "upload_help": "Envie um arquivo baseado no modelo. CSV com vírgula ou ponto e vírgula é aceito.",
        "download_template": "Baixar modelo de CSV",
        "using_demo": "Usando a carteira demonstrativa",
        "upload_success": "clientes importados com sucesso",
        "upload_fallback": "O arquivo não foi importado. A carteira demonstrativa continua ativa.",
        "history_unavailable": (
            "O CSV contém uma fotografia atual da carteira. Envie um histórico mensal em uma evolução futura "
            "para gerar este gráfico sem misturar dados demonstrativos."
        ),
        "active_customers": "Clientes ativos",
        "upload_error_empty": "O arquivo está vazio.",
        "upload_error_missing_columns": "Colunas obrigatórias ausentes",
        "upload_error_empty_values": "Há valores vazios na coluna",
        "upload_error_duplicate_ids": "Existem IDs de clientes duplicados.",
        "upload_error_invalid_status": "Status inválido. Use Active/Ativo ou Churned/Cancelado",
        "upload_error_invalid_numeric": "Há um valor que não é numérico na coluna",
        "upload_error_negative_values": "Os campos numéricos não podem conter valores negativos.",
        "upload_error_invalid_feature_adoption": "A adoção de funcionalidades deve estar entre 0 e 100.",
        "upload_error_invalid_csat": "O CSAT deve estar entre 0 e 5.",
        "upload_error_invalid_seats": "Licenças contratadas deve ser igual ou maior que 1.",
        "upload_error_read": "Não foi possível ler o CSV. Verifique o formato e a codificação do arquivo.",
        "score_explainer_title": "Entenda o cálculo do health score",
        "methodology_title": "Como o health score funciona",
        "methodology": """
O health score combina quatro dimensões e gera uma nota de **0 a 100**:

1. **Uso do produto — 35%**  
   `mínimo(usuários ativos mensais ÷ licenças contratadas, 1) × 100`  
   Exemplo: 80 usuários ativos em 100 licenças geram 80 pontos nesta dimensão.

2. **Adoção de funcionalidades — 25%**  
   Usa diretamente o percentual de funcionalidades estratégicas adotadas, limitado entre 0 e 100.

3. **Relacionamento — 20%**  
   `100 − (dias desde o último contato × 2)`  
   Um contato hoje gera 100 pontos; há 25 dias, 50 pontos; há 50 dias ou mais, 0 ponto.

4. **Experiência com suporte — 20%**  
   `(CSAT ÷ 5 × 100) − (tickets abertos × 8)`  
   Cada ticket aberto reduz 8 pontos da nota de suporte. O resultado fica limitado entre 0 e 100.

**Nota final:** `uso × 35% + adoção × 25% + relacionamento × 20% + suporte × 20%`

**Saudável:** 70–100 · **Em risco:** 50–69 · **Crítico:** 0–49

A fila de ações combina risco, valor da conta e proximidade da renovação.
Todos os dados deste projeto são sintéticos e não contêm informações de clientes reais.

Os valores são exibidos em reais na interface em português e em dólares na interface em inglês.
Essa troca é apenas uma convenção de apresentação da demonstração, sem conversão cambial.
""",
        "active": "Ativo",
        "churned": "Cancelado",
    },
    "en": {
        "filters": "Portfolio filters",
        "segment": "Segment",
        "plan": "Plan",
        "csm": "CSM owner",
        "demo": "Demo portfolio · Synthetic data",
        "title": "Customer Success Analytics",
        "subtitle": "Executive portfolio visibility for retention, revenue and proactive customer action",
        "tabs": ["Executive overview", "Risk & retention", "Revenue", "Customer portfolio", "Methodology"],
        "mrr": "Monthly recurring revenue",
        "arr": "Annual recurring revenue",
        "nrr": "Net revenue retention",
        "logo_churn": "Logo churn",
        "average_health": "Average health",
        "mrr_evolution": "MRR evolution",
        "month": "Month",
        "portfolio_health": "Portfolio health",
        "health_status": "Health status",
        "healthy": "Healthy",
        "at_risk": "At risk",
        "critical": "Critical",
        "insights": "Decision-ready insights",
        "critical_accounts": "critical accounts",
        "critical_detail": "MRR requires immediate attention.",
        "stale_accounts": "accounts without recent contact",
        "stale_detail": "Last CSM touchpoint was over 30 days ago.",
        "risky_renewals": "risky renewals",
        "renewal_detail": "Renewal is within 60 days and health is below 70.",
        "risk_exposure": "Risk exposure by customer value",
        "health_score": "Health score",
        "contracted_seats": "Contracted seats",
        "customer_name": "Customer",
        "health_by_segment": "Health distribution by segment",
        "customers": "Customers",
        "action_queue": "Prioritized action queue",
        "days_to_renewal": "Days to renewal",
        "days_since_contact": "Days since contact",
        "open_tickets": "Open tickets",
        "priority": "Priority",
        "current_mrr": "Current portfolio MRR",
        "risk_mrr": "MRR exposed to risk",
        "grr": "Gross revenue retention",
        "monthly_churn": "Latest monthly churn",
        "opening_mrr": "Opening MRR",
        "new": "New",
        "expansion": "Expansion",
        "contraction": "Contraction",
        "churn": "Churn",
        "closing_mrr": "Closing MRR",
        "mrr_movement": "Latest month MRR movement",
        "search": "Search customer",
        "search_placeholder": "Company name or customer ID",
        "customer_id": "Customer ID",
        "status": "Status",
        "renewal_days": "Days to renewal",
        "download": "Download filtered portfolio",
        "data_source": "Data source",
        "upload": "Upload customer portfolio CSV",
        "upload_help": "Upload a file based on the template. Comma- and semicolon-separated CSV files are accepted.",
        "download_template": "Download CSV template",
        "using_demo": "Using the demo portfolio",
        "upload_success": "customers imported successfully",
        "upload_fallback": "The file was not imported. The demo portfolio remains active.",
        "history_unavailable": (
            "The CSV is a current portfolio snapshot. Add monthly history in a future iteration to generate "
            "this chart without mixing in demo data."
        ),
        "active_customers": "Active customers",
        "upload_error_empty": "The file is empty.",
        "upload_error_missing_columns": "Required columns are missing",
        "upload_error_empty_values": "There are empty values in column",
        "upload_error_duplicate_ids": "Duplicate customer IDs were found.",
        "upload_error_invalid_status": "Invalid status. Use Active/Ativo or Churned/Cancelado",
        "upload_error_invalid_numeric": "A non-numeric value was found in column",
        "upload_error_negative_values": "Numeric fields cannot contain negative values.",
        "upload_error_invalid_feature_adoption": "Feature adoption must be between 0 and 100.",
        "upload_error_invalid_csat": "CSAT must be between 0 and 5.",
        "upload_error_invalid_seats": "Contracted seats must be at least 1.",
        "upload_error_read": "The CSV could not be read. Check its format and encoding.",
        "score_explainer_title": "Understand the health score calculation",
        "methodology_title": "How the health score works",
        "methodology": """
The health score combines four dimensions into a **0–100** score:

1. **Product usage — 35%**  
   `min(monthly active users ÷ contracted seats, 1) × 100`  
   Example: 80 active users across 100 contracted seats produces 80 points for this dimension.

2. **Feature adoption — 25%**  
   Uses the percentage of strategic features adopted, capped between 0 and 100.

3. **Relationship — 20%**  
   `100 − (days since last contact × 2)`  
   Contact today produces 100 points; 25 days ago, 50 points; 50 days ago or more, 0 points.

4. **Support experience — 20%**  
   `(CSAT ÷ 5 × 100) − (open tickets × 8)`  
   Each open ticket subtracts 8 support points. The result is capped between 0 and 100.

**Final score:** `usage × 35% + adoption × 25% + relationship × 20% + support × 20%`

**Healthy:** 70–100 · **At risk:** 50–69 · **Critical:** 0–49

The action queue combines risk, account value and renewal proximity.
All data in this project is synthetic and contains no real customer information.

Values are displayed in Brazilian reais in Portuguese and US dollars in English.
This is a presentation convention for the demo, not a foreign-exchange conversion.
""",
        "active": "Active",
        "churned": "Churned",
    },
}

st.set_page_config(page_title="Customer Success Analytics | Análise de CS", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
      [data-testid="stSidebar"] {border-right:1px solid #d8dee8;}
      [data-testid="stMetric"] {
        background:#f4f6fa;
        border:1px solid #d8dee8;
        box-shadow:0 6px 18px rgba(51,65,85,.06);
        padding:16px;
        border-radius:14px;
      }
      [data-testid="stMetricLabel"] {color:#64748b;}
      .insight {
        background:#f4f6fa;
        border:1px solid #d8dee8;
        border-left:4px solid #6d5bd0;
        box-shadow:0 6px 18px rgba(51,65,85,.05);
        color:#334155;
        padding:14px 16px;
        border-radius:10px;
        margin:8px 0;
      }
      div[data-testid="stDataFrame"] {border-radius:12px; overflow:hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(ROOT / "data" / "customers.csv")
    history = pd.read_csv(ROOT / "data" / "monthly_history.csv", parse_dates=["month"])
    return add_health_fields(customers), history


def money(value: float, language: str) -> str:
    if language == "pt":
        return f"R$ {value:,.0f}".replace(",", ".")
    return f"${value:,.0f}"


demo_customers, history = load_data()
customers = demo_customers
using_uploaded_portfolio = False

with st.sidebar:
    language_label = st.radio("Idioma / Language", ["Português", "English"], horizontal=True)
    language = "pt" if language_label == "Português" else "en"
    text = TRANSLATIONS[language]

    st.subheader(text["data_source"])
    st.download_button(
        text["download_template"],
        customer_template().to_csv(index=False).encode("utf-8-sig"),
        "modelo_carteira_clientes.csv" if language == "pt" else "customer_portfolio_template.csv",
        "text/csv",
        use_container_width=True,
    )
    uploaded_file = st.file_uploader(text["upload"], type=["csv"], help=text["upload_help"])
    if uploaded_file is not None:
        try:
            uploaded_data = pd.read_csv(io.BytesIO(uploaded_file.getvalue()), sep=None, engine="python")
            customers = add_health_fields(prepare_uploaded_customers(uploaded_data))
            using_uploaded_portfolio = True
            st.success(f"{len(customers)} {text['upload_success']}")
        except CustomerDataError as error:
            message = text.get(f"upload_error_{error.code}", text["upload_error_read"])
            details = f": {error.details}" if error.details else ""
            st.error(f"{message}{details}\n\n{text['upload_fallback']}")
        except (OSError, UnicodeError, pd.errors.ParserError):
            st.error(f"{text['upload_error_read']}\n\n{text['upload_fallback']}")
    else:
        st.caption(text["using_demo"])

    st.divider()
    st.title(text["filters"])
    selected_segments = st.multiselect(text["segment"], sorted(customers["segment"].unique()))
    selected_plans = st.multiselect(text["plan"], sorted(customers["plan"].unique()))
    selected_csms = st.multiselect(text["csm"], sorted(customers["csm"].unique()))
    st.divider()
    st.caption(text["demo"])

health_labels = {"Healthy": text["healthy"], "At risk": text["at_risk"], "Critical": text["critical"]}
localized_colors = {health_labels[key]: value for key, value in HEALTH_COLORS.items()}
currency_prefix = "R$ " if language == "pt" else "$"
currency_format = "R$ %d" if language == "pt" else "$%d"

filtered = filter_customers(customers, selected_segments, selected_plans, selected_csms)
kpis = portfolio_kpis(filtered)
active = filtered[filtered["status"] == "Active"].copy()
active["health_status_display"] = active["health_status"].map(health_labels)

st.title(text["title"])
st.caption(text["subtitle"])
tabs = st.tabs(text["tabs"])

with tabs[0]:
    cols = st.columns(5)
    cols[0].metric(text["mrr"], money(kpis["mrr"], language))
    cols[1].metric(text["arr"], money(kpis["arr"], language))
    cols[2].metric(text["nrr"], f"{kpis['nrr']:.1%}")
    cols[3].metric(text["logo_churn"], f"{kpis['logo_churn']:.1%}")
    cols[4].metric(text["average_health"], f"{kpis['average_health']:.0f}/100")

    with st.expander(text["score_explainer_title"]):
        st.markdown(text["methodology"])

    left, right = st.columns([1.65, 1])
    with left:
        if using_uploaded_portfolio:
            st.subheader(text["mrr_evolution"])
            st.info(text["history_unavailable"])
        else:
            fig = px.area(
                history,
                x="month",
                y="mrr",
                title=text["mrr_evolution"],
                markers=True,
                labels={"month": text["month"], "mrr": "MRR"},
            )
            fig.update_traces(line_color="#8b5cf6", fillcolor="rgba(139,92,246,.18)")
            fig.update_layout(yaxis_tickprefix=currency_prefix, hovermode="x unified")
            fig.update_xaxes(tickformat="%m/%Y" if language == "pt" else "%b %Y")
            st.plotly_chart(fig, use_container_width=True)
    with right:
        health_counts = active["health_status"].value_counts().reindex(HEALTH_ORDER, fill_value=0)
        localized_health_counts = health_counts.rename(index=health_labels)
        fig = px.pie(
            values=localized_health_counts.values,
            names=localized_health_counts.index,
            hole=0.64,
            title=text["portfolio_health"],
            color=localized_health_counts.index,
            color_discrete_map=localized_colors,
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    critical = active[active["health_status"] == "Critical"]
    stale = active[active["days_since_last_contact"] > 30]
    renewal_risk = active[(active["renewal_days"] <= 60) & (active["health_score"] < 70)]
    st.subheader(text["insights"])
    insight_cols = st.columns(3)
    insight_cols[0].markdown(
        f'<div class="insight"><b>{len(critical)} {text["critical_accounts"]}</b><br>'
        f'{money(critical["mrr"].sum(), language)} {text["critical_detail"]}</div>',
        unsafe_allow_html=True,
    )
    insight_cols[1].markdown(
        f'<div class="insight"><b>{len(stale)} {text["stale_accounts"]}</b><br>{text["stale_detail"]}</div>',
        unsafe_allow_html=True,
    )
    insight_cols[2].markdown(
        f'<div class="insight"><b>{len(renewal_risk)} {text["risky_renewals"]}</b><br>'
        f'{text["renewal_detail"]}</div>',
        unsafe_allow_html=True,
    )

with tabs[1]:
    left, right = st.columns(2)
    with left:
        fig = px.scatter(
            active,
            x="health_score",
            y="mrr",
            size="contracted_seats",
            color="health_status_display",
            hover_name="customer_name",
            color_discrete_map=localized_colors,
            title=text["risk_exposure"],
            labels={
                "health_score": text["health_score"],
                "mrr": "MRR",
                "contracted_seats": text["contracted_seats"],
                "health_status_display": text["health_status"],
                "customer_name": text["customer_name"],
            },
        )
        fig.update_layout(yaxis_tickprefix=currency_prefix)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        segment_health = (
            active.groupby(["segment", "health_status_display"], observed=True)
            .size()
            .reset_index(name="customers")
        )
        fig = px.bar(
            segment_health,
            x="segment",
            y="customers",
            color="health_status_display",
            barmode="stack",
            title=text["health_by_segment"],
            color_discrete_map=localized_colors,
            labels={
                "segment": text["segment"],
                "customers": text["customers"],
                "health_status_display": text["health_status"],
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(text["action_queue"])
    queue = active[active["health_score"] < 70].sort_values("priority_score", ascending=False).copy()
    queue["health_status"] = queue["health_status"].map(health_labels)
    queue_columns = [
        "customer_name",
        "segment",
        "csm",
        "mrr",
        "health_score",
        "health_status",
        "renewal_days",
        "days_since_last_contact",
        "open_tickets",
        "priority_score",
    ]
    st.dataframe(
        queue[queue_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "customer_name": text["customer_name"],
            "segment": text["segment"],
            "csm": text["csm"],
            "mrr": st.column_config.NumberColumn("MRR", format=currency_format),
            "health_score": st.column_config.ProgressColumn(text["health_score"], min_value=0, max_value=100),
            "health_status": text["health_status"],
            "renewal_days": text["days_to_renewal"],
            "days_since_last_contact": text["days_since_contact"],
            "open_tickets": text["open_tickets"],
            "priority_score": st.column_config.NumberColumn(text["priority"], format="%.1f"),
        },
    )

with tabs[2]:
    cols = st.columns(4)
    cols[0].metric(text["current_mrr"], money(kpis["mrr"], language))
    cols[1].metric(text["risk_mrr"], money(kpis["at_risk_mrr"], language))
    cols[2].metric(text["grr"], f"{kpis['grr']:.1%}")
    if using_uploaded_portfolio:
        cols[3].metric(text["active_customers"], f"{kpis['active_customers']:.0f}")
        st.info(text["history_unavailable"])
    else:
        latest = history.iloc[-1]
        cols[3].metric(text["monthly_churn"], money(latest["churned_mrr"], language))
        waterfall = go.Figure(
            go.Waterfall(
                x=[
                    text["opening_mrr"],
                    text["new"],
                    text["expansion"],
                    text["contraction"],
                    text["churn"],
                    text["closing_mrr"],
                ],
                y=[
                    history.iloc[-2]["mrr"],
                    latest["new_mrr"],
                    latest["expansion_mrr"],
                    -latest["contraction_mrr"],
                    -latest["churned_mrr"],
                    0,
                ],
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                increasing={"marker": {"color": "#22c55e"}},
                decreasing={"marker": {"color": "#ef4444"}},
                totals={"marker": {"color": "#8b5cf6"}},
            )
        )
        waterfall.update_layout(title=text["mrr_movement"], yaxis_tickprefix=currency_prefix, showlegend=False)
        st.plotly_chart(waterfall, use_container_width=True)

with tabs[3]:
    search = st.text_input(text["search"], placeholder=text["search_placeholder"])
    table = filtered.copy()
    if search:
        name_match = table["customer_name"].str.contains(search, case=False, na=False)
        id_match = table["customer_id"].str.contains(search, case=False, na=False)
        table = table[name_match | id_match]

    table["health_status"] = table["health_status"].map(health_labels)
    table["status"] = table["status"].map({"Active": text["active"], "Churned": text["churned"]})
    portfolio_columns = [
        "customer_id",
        "customer_name",
        "segment",
        "plan",
        "csm",
        "status",
        "mrr",
        "health_score",
        "health_status",
        "renewal_days",
    ]
    column_labels = {
        "customer_id": text["customer_id"],
        "customer_name": text["customer_name"],
        "segment": text["segment"],
        "plan": text["plan"],
        "csm": text["csm"],
        "status": text["status"],
        "mrr": "MRR",
        "health_score": text["health_score"],
        "health_status": text["health_status"],
        "renewal_days": text["renewal_days"],
    }
    st.dataframe(
        table[portfolio_columns].sort_values("health_score"),
        use_container_width=True,
        hide_index=True,
        column_config={
            **column_labels,
            "mrr": st.column_config.NumberColumn("MRR", format=currency_format),
            "health_score": st.column_config.ProgressColumn(text["health_score"], min_value=0, max_value=100),
        },
    )
    export = table.rename(columns=column_labels)
    filename = "carteira_cs.csv" if language == "pt" else "cs_portfolio.csv"
    st.download_button(text["download"], export.to_csv(index=False), filename, "text/csv")

with tabs[4]:
    st.subheader(text["methodology_title"])
    st.markdown(text["methodology"])
