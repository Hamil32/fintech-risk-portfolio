# Módulo 03 — Fraud Detection

**Objetivo:** construir un sistema de detección de fraude transaccional en 3 capas (reglas → anomalías no supervisadas → modelo supervisado) y un sistema de alertas que las combina y las prioriza, tal como funciona en un equipo de fraude real.

> 📘 Ver la explicación completa de cada técnica, sus fórmulas y los hallazgos del proceso en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#5-módulo-03--fraud-detection).

## Requisito previo

```bash
cd ../01_data_infrastructure
python generate_synthetic_data.py
```

## Cómo correr este módulo

```bash
cd 03_fraud_detection

python rule_engine.py         # Capa 1: motor de reglas (velocity, monto, horario, canal)
python anomaly_detection.py   # Capa 2: Isolation Forest (no supervisado)
python fraud_model.py         # Capa 3: modelo supervisado (Regresión Logística + Random Forest)
python alert_system.py        # Orquestación: combina las 3 señales en una cola de alertas priorizada
```

⚠️ `alert_system.py` depende de los CSV que generan `rule_engine.py` y `anomaly_detection.py` — correrlos primero.

## Archivos

| Archivo | Qué hace |
|---|---|
| `rule_engine.py` | 4 reglas: velocity (>5 tx/hora), monto atípico (z-score >3), horario sospechoso (1-5am), canal digital + monto alto |
| `anomaly_detection.py` | Isolation Forest + benchmark de z-score simple, sin usar la etiqueta de fraude para entrenar |
| `fraud_model.py` | Regresión Logística y Random Forest supervisados, con curva Precision-Recall |
| `alert_system.py` | Combina las 3 señales en niveles de prioridad (CRÍTICA/ALTA/MEDIA) + tabla de cobertura acumulada |
| `sql/fraud_patterns.sql` | Patrones de fraude por canal, horario, tipo y cliente, en SQL puro |
| `sql/velocity_checks.sql` | Velocity check vía self-join (SQLite no tiene rolling window de tiempo) |
| `sql/suspicious_transactions.sql` | Las reglas de monto atípico, horario y canal, en SQL puro |

## Resultados de esta corrida (resumen — detalle completo en la Bitácora)

| Técnica | Precision | Recall | F1 / AUC-PR |
|---|---|---|---|
| Motor de reglas | 50.7% | 36.2% | F1 = 0.42 |
| Isolation Forest (no supervisado) | 8.5% | 8.5% | F1 = 0.09 |
| Random Forest (supervisado) | 27.2% | 85.6% | AUC-PR = 0.57 |
| **Sistema de alertas combinado** | revisando solo el 4.0% del volumen (CRÍTICA+ALTA) | **captura 81.9% del fraude total** | — |

## Salidas (en `output/`, CSVs ignorados por git)

- `fraud_rules_output.csv`, `anomaly_detection_output.csv`
- `fraud_model_test_predictions.csv`, `fraud_model_precision_recall_curve.csv`, `fraud_model_feature_importance.csv`
- `alert_queue.csv` — la cola de alertas final, ordenada por prioridad

## KPIs para el Dashboard Power BI de este módulo

| Métrica | Visualización | Fuente |
|---|---|---|
| Tasa de fraude general | KPI card | `fraud_rules_output.csv` |
| Alertas por nivel de prioridad | Gráfico de barras | `alert_queue.csv` |
| Cobertura acumulada de fraude por prioridad | Línea / cascada | ver consola de `alert_system.py` |
| Fraude por canal y horario | Matrix / heatmap | `sql/fraud_patterns.sql` |
| Curva Precision-Recall del modelo | Línea | `fraud_model_precision_recall_curve.csv` |
| Importancia de variables | Barras horizontales | `fraud_model_feature_importance.csv` |

## Conceptos aplicados (detalle con fórmulas en la Bitácora Técnica)

- Velocity check, monto atípico (z-score), horario sospechoso, canal + monto
- Isolation Forest vs. z-score univariado — por qué uno captura más que el otro
- Precision / Recall / F1 / AUC-ROC / AUC-PR — y por qué AUC-PR es más informativo que AUC-ROC con clases desbalanceadas
- `cross_val_predict` para puntuar el 100% de una población sin sesgo optimista de entrenamiento
- Gains table / cobertura acumulada — cómo priorizar una cola de alertas con recursos limitados
