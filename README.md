# 🏦 FINTECH Risk Portfolio

Portfolio técnico-financiero de análisis de **riesgo crediticio, detección de fraude, AML/Compliance y BI** sobre un banco ficticio ("Banco Río Digital"), construido con Python, SQL y Power BI.

> 📄 Ver el instructivo completo del proyecto en [`FINTECH_RISK_PORTFOLIO_INSTRUCTIVO.md`](FINTECH_RISK_PORTFOLIO_INSTRUCTIVO.md).
> 📘 Ver el paso a paso técnico (qué se hizo, cómo, con qué fórmulas y de dónde sale cada criterio) en [`BITACORA_TECNICA.md`](BITACORA_TECNICA.md).

## Qué incluye

| Módulo | Contenido | Estado |
|---|---|---|
| [01 — Data Infrastructure](01_data_infrastructure/) | Dataset sintético bancario (clientes, cuentas, transacciones, préstamos, scoring) + ETL + data quality checks | ✅ |
| [02 — Credit Risk Analytics](02_credit_risk/) | PD / LGD / EAD / Expected Loss, vintage analysis, roll rate, scorecard (WOE + regresión logística) | ✅ |
| [03 — Fraud Detection](03_fraud_detection/) | Motor de reglas, Isolation Forest, modelo supervisado, sistema de alertas priorizado | ✅ |
| [04 — AML / Compliance](04_aml_compliance/) | Tipologías GAFI (structuring, round-tripping, actividad inusual, cash-intensive), KYC, borradores de ROS | ✅ |
| [05 — Decision Engine](05_decision_engine/) | API REST (FastAPI) de scoring y decisión crediticia en tiempo real, con pricing basado en riesgo | ✅ |
| 06 — Executive Dashboard | Dashboard consolidado en Power BI con KPIs de cartera, fraude y AML | 🔜 |

## Stack

Python (pandas, numpy, scikit-learn, faker, sqlalchemy, fastapi) · SQL (SQLite) · Power BI · Git

## Cómo correr el proyecto

```bash
git clone https://github.com/Hamil32/fintech-risk-portfolio.git
cd fintech-risk-portfolio

python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

cd 01_data_infrastructure
python generate_synthetic_data.py
python data_quality_checks.py
python etl_pipeline.py
```

## Sobre el proyecto

Desarrollado para aplicar herramientas de análisis de datos (Python, SQL, Power BI) al dominio financiero-bancario: scoring crediticio bajo metodología tipo Basilea II (PD/LGD/EAD), detección de fraude transaccional, prevención de lavado de dinero (AML/GAFI) y motores de decisión automatizados.

---
*Autor: Hamil Mauricio Selim Flores Balverdi*
