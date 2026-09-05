# FINTECH Risk Portfolio — Resumen Ejecutivo

**Repositorio:** [github.com/Hamil32/fintech-risk-portfolio](https://github.com/Hamil32/fintech-risk-portfolio)

## Qué es

Un sistema de análisis de riesgo, fraude, AML y decisión crediticia construido de punta a punta sobre un banco ficticio ("Banco Río Digital"): 5.000 clientes, 50.000 transacciones, 2.000 préstamos — generados sintéticamente, pero con la misma estructura, las mismas métricas y las mismas fórmulas que usa un banco real.

## Los 5 módulos, en una frase cada uno

| # | Módulo | En una frase |
|---|---|---|
| 01 | Data Infrastructure | Construí el banco ficticio: schema relacional, datos sintéticos con patrones de riesgo/fraude/AML inyectados deliberadamente, y validaciones de calidad de datos (23 chequeos). |
| 02 | Credit Risk Analytics | Calculé PD, LGD, EAD y Expected Loss por préstamo, y armé un scorecard de crédito completo (WOE + regresión logística + escalado a puntos), validado con AUC/Gini. |
| 03 | Fraud Detection | Construí 3 capas de detección (reglas, Isolation Forest, modelo supervisado) y un sistema de alertas que prioriza: con el 4% del volumen se captura el 82% del fraude. |
| 04 | AML / Compliance | Detecté 4 tipologías de lavado (GAFI/UIF), incluyendo round-tripping vía detección de ciclos en un grafo de transferencias, y generé borradores de ROS. |
| 05 | Decision Engine | Una API REST que decide créditos en tiempo real, con pricing basado en riesgo (reutilizando la PD y el LGD de los módulos anteriores). |

## Los 3 números que más importan

- **Expected Loss de la cartera: 5,57%** ($409,7M sobre una cartera de $7.353,7M) — calculado con PD histórica real del dataset, no con valores inventados.
- **81,9% del fraude capturado revisando solo el 4,0% del volumen** — el argumento con el que se justifica el dimensionamiento de un equipo de fraude.
- **AUC del scorecard de crédito: 0,73** (Gini 0,46) — dentro del rango que la industria considera aceptable (0,7-0,8) para un modelo de admisión real.

## Lo que este portfolio demuestra que sé hacer

- Diseñar un modelo de datos relacional y mantenerlo consistente a través de 5 módulos que dependen entre sí.
- Aplicar metodología real de riesgo crediticio (Basilea II / IRB): PD, LGD, EAD, Expected Loss, vintage analysis, roll rate, scorecards con WOE/IV.
- Construir y comparar 3 enfoques de detección de fraude (reglas, no supervisado, supervisado), sabiendo explicar el trade-off de cada uno.
- Detectar tipologías AML reales (structuring, round-tripping) modelando el problema correctamente — incluyendo extender el modelo de datos cuando encontré que era necesario.
- Construir y testear una API REST (FastAPI + pytest) que conecta el análisis de riesgo a una decisión operativa real.
- **Encontrar y corregir mis propios errores de forma metódica**: un scorecard con IV sospechoso, una PD no monótona, un modelo de fraude con 100% de precisión (señal de fuga de datos, no de éxito) — documentados en detalle en la Bitácora Técnica, porque ese proceso de detectar y corregir es tan valioso como el resultado final.

## Cómo navegar el repositorio

```
fintech-risk-portfolio/
├── README.md                      ← Punto de entrada
├── BITACORA_TECNICA.md            ← El paso a paso completo: qué se hizo,
│                                     cómo, con qué fórmulas y por qué
├── 01_data_infrastructure/
├── 02_credit_risk/
├── 03_fraud_detection/
├── 04_aml_compliance/
├── 05_decision_engine/
└── 06_executive_dashboard/        ← Este módulo
```

Cada carpeta de módulo tiene su propio README con instrucciones de cómo correrlo.

## Frase de apertura para una entrevista

> *"Construí un portfolio de análisis de riesgo financiero sobre un banco ficticio que armé yo mismo, con datos sintéticos pero metodológicamente reales. Cubre riesgo crediticio (PD/LGD/EAD, scorecard), detección de fraude en 3 capas, tipologías AML (incluyendo detección de round-tripping como un problema de ciclos en un grafo), y una API que conecta todo eso a una decisión de crédito en tiempo real con pricing basado en riesgo. Documenté todo el proceso — incluyendo los errores que encontré y cómo los corregí — en una bitácora técnica de acceso público."*

## Stack técnico

Python (pandas, numpy, scikit-learn, faker, sqlalchemy, FastAPI, pytest) · SQL (SQLite) · Power BI · Git/GitHub
