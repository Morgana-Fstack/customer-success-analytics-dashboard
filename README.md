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
- Customer health segmentation: **Healthy, At risk and Critical**
- MRR evolution and monthly revenue waterfall
- Risk exposure by customer value and segment
- Prioritized action queue based on risk, MRR and renewal proximity
- Filters by segment, plan and CSM owner
- Searchable portfolio and CSV export
- Documented health-score methodology
- CSV import aligned with the operational source schema
- Backward compatibility for optional operational fields used in earlier project iterations

## CSV portfolio import

The downloadable CSV template mirrors the source portfolio exactly and contains **17 columns**:

| Field | Meaning |
|---|---|
| `customer_id` | Unique customer identifier |
| `customer_name` | Customer name |
| `segment` | Customer segment, such as Agency or Partner/Affiliate |
| `plan` | Contracted plan |
| `csm` | Customer Success Manager responsible for the customer |
| `status` | Customer status |
| `starting_mrr` | MRR at the start of the analyzed period |
| `mrr` | Current MRR |
| `expansion_mrr` | Expansion revenue |
| `contraction_mrr` | Contraction revenue |
| `contracted_seats` | Contracted seats |
| `monthly_active_users` | Monthly active users |
| `feature_adoption_pct` | Feature adoption percentage |
| `days_since_last_contact` | Days since the last customer contact |
| `open_tickets` | Open support tickets |
| `csat_score` | Customer satisfaction score |
| `renewal_days` | Days until renewal |

Accepted status values are normalized by the importer. Examples include `Active`, `Ativo` and `Mensal` for active customers, and `Churned`, `Cancelado`, `Desistencia`, `Desistência` and `Inativo` for churned customers.

Blank values in `expansion_mrr` and `contraction_mrr` are interpreted as zero. The remaining numeric fields are validated before the portfolio is loaded.

Earlier project versions supported additional fields such as onboarding dates, customer type and account counts. These fields remain accepted when present for backward compatibility, but **they are not part of the official source schema and are not required by the downloadable template**.

The demonstration portfolio contains anonymized customers and synthetic product, support and revenue values for portfolio presentation purposes.

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
├── src/metrics.py            # Health score, portfolio KPIs and filters
├── src/operations.py         # Additional CS operations metrics
├── tests/                    # Data-validation and business-logic tests
└── .github/workflows/ci.yml  # Automated quality checks
```

---

## Versão em português

Dashboard interativo que transforma dados de uma carteira de Customer Success em decisões de retenção e receita. O projeto reúne indicadores executivos, health score explicável, análise da movimentação de receita e uma fila priorizada de clientes.

### Estrutura da base

O CSV oficial utilizado para importação possui **17 variáveis**:

- `customer_id` — identificador único do cliente
- `customer_name` — nome do cliente
- `segment` — segmento, como Agência ou Parceiro/Afiliado
- `plan` — plano contratado
- `csm` — Customer Success Manager responsável
- `status` — situação do cliente
- `starting_mrr` — MRR no início
- `mrr` — MRR atual
- `expansion_mrr` — receita de expansão
- `contraction_mrr` — receita de contração
- `contracted_seats` — assentos contratados
- `monthly_active_users` — usuários ativos no mês
- `feature_adoption_pct` — percentual de adoção de features
- `days_since_last_contact` — dias desde o último contato
- `open_tickets` — tickets abertos
- `csat_score` — nota de satisfação do cliente
- `renewal_days` — dias até a renovação

O importador normaliza os status operacionais usados na base. `Ativo` e `Mensal`, por exemplo, são tratados como clientes ativos; `Cancelado`, `Desistencia`, `Desistência` e `Inativo` são tratados como churn.

Valores vazios de expansão e contração são convertidos para zero. Os demais campos numéricos são validados antes da carga.

Campos de onboarding, data de entrada, quantidade de contas e tipo de cliente que apareceram em versões anteriores do projeto continuam aceitos por compatibilidade, mas **não fazem parte da fonte oficial e não são exigidos no modelo CSV**.

A partir dessas 17 variáveis, o dashboard calcula health score, exposição de receita em risco, churn, retenção, uso do produto, relacionamento, suporte e prioridades de atuação do time de CS.

## Author

**Morgana Petterle** — Customer Success professional building solutions at the intersection of customer experience, analytics and technology.

## License

Licensed under the [MIT License](LICENSE).