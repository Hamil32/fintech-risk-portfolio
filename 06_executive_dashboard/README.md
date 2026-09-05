# Módulo 06 — Executive Dashboard

**Objetivo:** consolidar el análisis de los Módulos 01-04 en un dashboard ejecutivo de 4 páginas en Power BI, y cerrar el portfolio con un resumen ejecutivo presentable.

✅ **El modelo de datos (tablas, relaciones y 20 medidas DAX) ya está construido** — se armó directamente contra Power BI Desktop usando el [Power BI Modeling MCP Server](https://github.com/microsoft/powerbi-modeling-mcp) de Microsoft, conectado a esta sesión de Claude Code. Cada número se validó contra los valores ya documentados en los Módulos 02-04. Ver el proceso completo (y los 3 bugs que aparecieron en el camino) en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#8-módulo-06--executive-dashboard).

⚠️ **Lo único que sigue siendo manual:** las páginas del **reporte** (los visuales que ves en pantalla) — el MCP opera sobre el modelo semántico, no sobre el layout del reporte. Ese es el objetivo de `power_bi_build_guide.md`.

> 📘 Ver el KPI de cada módulo explicado con su fórmula en [`kpis_financieros.md`](kpis_financieros.md).
> 📄 Ver el resumen ejecutivo de todo el portfolio en [`portfolio_presentation.md`](portfolio_presentation.md).

## Requisito previo

Corré los Módulos 01 a 04 al menos una vez (en orden) antes de este:

```bash
cd 01_data_infrastructure && python generate_synthetic_data.py && python etl_pipeline.py
cd ../02_credit_risk && python pd_lgd_ead.py && python vintage_analysis.py && python roll_rate_matrix.py && python credit_scorecard.py
cd ../03_fraud_detection && python rule_engine.py && python anomaly_detection.py && python fraud_model.py && python alert_system.py
cd ../04_aml_compliance && python aml_rule_engine.py && python kyc_validator.py
```

## Cómo correr este módulo

```bash
cd 06_executive_dashboard
python build_dashboard_dataset.py    # Consolida todo en data/ (6 CSVs)
```

El modelo ya construido vive en el `.pbix` guardado localmente (no se sube a git — es un archivo binario grande y específico de esta máquina). Si necesitás reconstruirlo desde cero, `build_dashboard_dataset.py` deja los CSVs listos y el proceso vía MCP es 100% reproducible (ver Bitácora Técnica).

Abrí el `.pbix` en Power BI Desktop y seguí [`power_bi_build_guide.md`](power_bi_build_guide.md) para armar los visuales de las 4 páginas.

## Archivos

| Archivo | Rol |
|---|---|
| `build_dashboard_dataset.py` | Consolida las salidas de los Módulos 01-04 en 6 tablas tipo estrella (hechos + dimensiones) |
| `power_bi_build_guide.md` | Guía completa: importar datos, armar relaciones, y qué visual poner en cada una de las 4 páginas |
| `dax_measures.md` | Todas las medidas DAX listas para copiar y pegar |
| `kpis_financieros.md` | Glosario de KPIs financieros con fórmula y valor actual de cada uno |
| `portfolio_presentation.md` | Resumen ejecutivo de los 5 módulos, para usar en una entrevista |

## Salida de `build_dashboard_dataset.py` (en `data/`, ignorado por git)

| Archivo | Filas | Contenido |
|---|---|---|
| `dim_clientes.csv` | 5.000 | Vista 360 del cliente (Módulo 01) + calificación de riesgo AML (Módulo 04) |
| `fact_prestamos.csv` | 2.000 | PD/LGD/EAD/Expected Loss (Módulo 02) + score final del scorecard |
| `fact_transacciones.csv` | 50.000 | Flags de reglas de fraude (Módulo 03) + prioridad de alerta + score del modelo |
| `dim_vintage.csv` | 13 | Tasa de mora/NPL por cohorte trimestral (Módulo 02) |
| `fact_roll_rate.csv` | 25 | Matriz de transición de segmento de riesgo, en formato largo (Módulo 02) |
| `fact_alertas_aml.csv` | 42 | Las 4 tipologías AML detectadas (Módulo 04) |

## Las 4 páginas del dashboard

1. **Resumen Ejecutivo** — KPIs de un vistazo de los 4 módulos de análisis
2. **Cartera de Crédito** — NPL, Expected Loss, vintage, roll rate, top clientes por exposición
3. **Fraude** — tasa de fraude, cobertura del sistema de alertas, patrones por canal/horario
4. **AML / Compliance** — alertas por tipología, calificación de riesgo de la cartera de clientes

## Después de armarlo

Si querés que lo revise: pasame una captura de pantalla de cada página, o el DAX que hayas escrito si no coincide con algo de esta guía, y lo repasamos juntos.
