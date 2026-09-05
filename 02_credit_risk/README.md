# Módulo 02 — Credit Risk Analytics

**Objetivo:** calcular las métricas de riesgo crediticio que usa cualquier banco (PD, LGD, EAD, Expected Loss), analizar la calidad de la cartera por cosecha (vintage) y por migración de riesgo (roll rate), y construir un scorecard de crédito con la metodología estándar de la industria (WOE + regresión logística + escalado a puntos).

> 📘 Ver la explicación completa de cada fórmula, de dónde sale y por qué, en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#4-módulo-02--credit-risk-analytics).

## Requisito previo

Este módulo lee la base generada por el [Módulo 01](../01_data_infrastructure/). Antes de correr nada acá, asegurate de haber corrido:

```bash
cd ../01_data_infrastructure
python generate_synthetic_data.py
```

## Cómo correr este módulo

Desde la raíz del repo, con el entorno virtual activado:

```bash
cd 02_credit_risk

python pd_lgd_ead.py          # PD, LGD, EAD y Expected Loss por segmento/tipo
python vintage_analysis.py    # Tasa de mora/NPL por cohorte de originación
python roll_rate_matrix.py    # Matriz de transición de segmento de riesgo A-E
python credit_scorecard.py    # Scorecard de puntos (WOE + regresión logística)
```

Las queries SQL en [`sql/`](sql/) replican los mismos análisis directamente contra `banco_rio_digital.db` — útiles para practicar SQL y para alimentar Power BI vía "Get Data > SQLite" o import de CSV.

## Archivos

| Archivo | Qué calcula |
|---|---|
| `pd_lgd_ead.py` | PD histórica por segmento de score, LGD por tipo de garantía, EAD (saldo pendiente) y Expected Loss = PD×LGD×EAD |
| `vintage_analysis.py` | Tasa de mora y NPL por trimestre de originación (cohorte), con gráfico comparativo |
| `roll_rate_matrix.py` | Matriz de transición (Markov) de segmento de riesgo A-E entre trimestres consecutivos, con heatmap |
| `credit_scorecard.py` | WOE/IV por variable, regresión logística, y escalado a un scorecard de puntos con validación (AUC/Gini) |
| `sql/credit_portfolio_kpis.sql` | KPIs de cartera, distribución por estado/tipo, top clientes por exposición |
| `sql/mora_segmentation.sql` | PD por segmento y buckets de mora en SQL puro |
| `sql/vintage_query.sql` | Vintage analysis replicado en SQL puro |

## Salidas (en `output/`, ignorado por git salvo los `.png`)

- `credit_risk_pd_lgd_ead.csv` — detalle por préstamo con PD/LGD/EAD/EL, para Power BI
- `vintage_analysis.csv` / `vintage_analysis.png`
- `roll_rate_matrix.csv` / `roll_rate_matrix.png`
- `scorecard_puntos.csv` — la tabla de puntos del scorecard
- `scorecard_aplicado.csv` — score final calculado por préstamo

## KPIs que debe mostrar el Dashboard Power BI de este módulo

| Métrica | Tipo de visualización | Fuente |
|---|---|---|
| NPL Rate (% mora > 90 días) | Gauge / KPI card | `credit_risk_pd_lgd_ead.csv` |
| Expected Loss por segmento | Gráfico de barras | `expected_loss_por_segmento.csv` |
| PD por segmento de score | Gráfico de columnas | `pd_por_segmento.csv` |
| Distribución de cartera por tipo | Gráfico de torta | `expected_loss_por_tipo.csv` |
| Vintage analysis | Heatmap / líneas por cohorte | `vintage_analysis.csv` |
| Roll rate matrix | Matrix / heatmap | `roll_rate_matrix.csv` |

> ⚠️ El archivo `.pbix` de Power BI no se puede generar por código — hay que abrir Power BI Desktop, importar estos CSVs y armar las visualizaciones manualmente. Es la única parte de este módulo que requiere trabajo fuera de VS Code.

## Conceptos financieros aplicados

Ver el detalle completo con fórmulas en la Bitácora Técnica. Resumen:

- **PD, LGD, EAD, Expected Loss** — metodología IRB de Basilea II
- **NPL** — mora > 90 días, umbral internacional de Basilea
- **Vintage analysis** — comparación de calidad de originación por cosecha
- **Roll rate** — velocidad de migración entre segmentos de riesgo
- **WOE / IV** — transformación estándar de variables para scorecards y medida de poder predictivo
- **AUC / Gini** — métricas de validación de un modelo de scoring
