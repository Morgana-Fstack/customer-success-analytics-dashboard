# Customer Success Analytics Dashboard

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/github/actions/workflow/status/Morgana-Fstack/customer-success-analytics-dashboard/ci.yml?label=tests)](https://github.com/Morgana-Fstack/customer-success-analytics-dashboard/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An interactive dashboard that turns Customer Success portfolio data into clear retention and revenue decisions. It combines executive KPIs, a transparent customer health score, revenue movement analysis and a prioritized action queue.

> Portfolio project built with anonymized operational distributions and synthetic product and revenue data. No real customer names or identifying information are used.

## Business problem

Customer Success teams often have customer, product usage, support and revenue data in separate tools. This project brings the main signals together to answer practical questions:

- Which customers need attention first?
- How much revenue is exposed to risk?
- Which renewals are approaching with low customer health?
- Are expansion and retention offsetting churn?
- Where should a CSM focus today?

## Dashboard features

- Executive view of **MRR, ARR, NRR, GRR, logo churn and average health**
- CS operations view with **onboarding completion, churn target and active/cancelled customers**
- Onboarding impact comparison and churn breakdown by customer type, segment, plan or CSM
- Entry-cohort churn analysis and operational attention list
- Customer health segmentation: **Healthy, At risk and Critical**
- MRR evolution and monthly revenue waterfall
- Risk exposure by customer value and segment
- Prioritized action queue based on risk, MRR and renewal proximity
- Filters by segment, plan and CSM owner
- Searchable portfolio and CSV export
- Documented health-score methodology
- Backward-compatible CSV import with optional CS operations fields

## CSV portfolio import

Download the template directly from the dashboard. The original portfolio fields remain required, while the fields below enable the CS operations view:

| Field | Meaning |
|---|---|
| `entry_date` | Customer entry date in `YYYY-MM-DD` format |
| `cancellation_date` | Cancellation date; leave blank for active customers |
| `customer_type` | Customer category, such as Individual, Agency or Partner |
| `accounts` | Number of accounts associated with the customer |
| `onboarding_completed` | `Yes`/`No` or `Sim`/`Não` |
| `onboarding_date` | Onboarding completion date; leave blank when not completed |

Legacy CSV files without these optional fields continue to load normally; only the CS operations tab stays unavailable.

The demonstration portfolio contains **136 anonymized customers** and preserves the operational distribution of the reference CS analysis: 72 active customers, 64 cancellations, 163 accounts, and onboarding groups that make retention impact visible. Product usage, support and revenue values remain fully synthetic.

## Health score

The model is intentionally transparent and explainable:

| Dimension | Weight | Signal |
|---|---:|---|
| Product adoption | 35% | Monthly active users / contracted seats |
| Feature adoption | 25% | Percentage of strategic features used |
| Relationship | 20% | Days since the last CSM interaction |
| Support experience | 20% | CSAT adjusted by open ticket volume |

Scores are classified as **Healthy (70–100)**, **At risk (50–69)** or **Critical (0–49)**.

## Tech stack

- Python
- Pandas
- Streamlit
- Plotly
- Pytest and Ruff

## Run locally

```bash
git clone https://github.com/Morgana-Fstack/customer-success-analytics-dashboard.git
cd customer-success-analytics-dashboard
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Validate the project

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

Regenerate the synthetic dataset when needed:

```bash
python generate_data.py
```

## Project structure

```text
.
├── app.py                    # Streamlit interface
├── data/                     # Synthetic portfolio and history
├── generate_data.py          # Reproducible demo-data generator
├── src/data_loader.py        # CSV validation and normalization
├── src/metrics.py            # Health score, operational KPIs and filters
├── tests/                    # Data-validation and business-logic tests
└── .github/workflows/ci.yml  # Automated quality checks
```

---

## Versão em português

Dashboard interativo que transforma dados de uma carteira de Customer Success em decisões de retenção e receita. O projeto reúne indicadores executivos, health score explicável, análise da movimentação de receita e uma fila priorizada de clientes.

Ele responde perguntas como:

- Quais clientes precisam de atenção imediata?
- Quanto de receita está exposto a risco?
- Quais renovações estão próximas e com baixa saúde?
- Expansão e retenção estão compensando o churn?
- Onde o time de CS deve concentrar seus esforços?
- Qual é o impacto da conclusão do onboarding no churn?
- Quais safras e tipos de cliente apresentam maior cancelamento?

A aba **Operação de CS** acompanha clientes ativos e cancelados, total de contas, meta de churn, conclusão do onboarding, comparação com e sem onboarding, churn por safra e uma lista de clientes que exigem atenção. O modelo de CSV disponível no próprio dashboard já inclui os novos campos operacionais.

A carteira demonstrativa possui **136 clientes anonimizados**, 72 ativos, 64 cancelados e 163 contas. As distribuições operacionais preservam a lógica da análise de referência, enquanto nomes, receita, uso de produto e suporte são fictícios. O projeto pode ser executado localmente com os comandos apresentados acima.

## Author

**Morgana Petterle** — Customer Success professional building solutions at the intersection of customer experience, analytics and technology.

## License

Licensed under the [MIT License](LICENSE).
