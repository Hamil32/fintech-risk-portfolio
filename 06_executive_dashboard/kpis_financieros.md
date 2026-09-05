# Glosario de KPIs Financieros — Dashboard Ejecutivo

Cada KPI, su fórmula, qué responde desde el punto de vista de negocio, y el valor real que tiene hoy en el dataset de Banco Río Digital (corrida documentada en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md)).

## Cartera de crédito

| KPI | Fórmula | Qué responde | Valor actual |
|---|---|---|---|
| **Cartera Total (EAD)** | Σ saldo pendiente de todos los préstamos | ¿Cuánto dinero tiene el banco expuesto hoy en créditos? | $7.353.674.329 |
| **NPL Ratio** | Cartera con mora > 90 días / Cartera total | ¿Qué % de la cartera está en incumplimiento? | 6,38% |
| **Expected Loss (EL)** | Σ (PD × LGD × EAD) por préstamo | ¿Cuánto espera perder el banco de esta cartera, en promedio? | $409.675.120 (5,57% de la cartera) |
| **Tasa de Mora Total** | Cartera con algún día de mora / Cartera total | ¿Qué % de la cartera tiene AL MENOS un día de atraso (no solo NPL)? | Ver `output/pd_por_segmento.csv` |
| **PD promedio ponderada** | Σ(PD × EAD) / Σ EAD | ¿Cuál es la probabilidad de default "típica" de la cartera, pesada por el tamaño de cada préstamo? | Calculada en Power BI (medida DAX) |

## Fraude

| KPI | Fórmula | Qué responde | Valor actual |
|---|---|---|---|
| **Tasa de Fraude** | Transacciones fraudulentas / Total de transacciones | ¿Qué proporción del volumen transaccional es fraude? | 2,0% (por diseño del dataset sintético — en la realidad es muchísimo más bajo, ver Bitácora Módulo 03) |
| **Precision del motor de reglas** | Alertas que son fraude real / Total de alertas generadas | De cada 100 alertas que generan trabajo para un analista, ¿cuántas valen la pena? | 50,7% |
| **Recall del motor de reglas** | Fraudes detectados / Fraudes reales totales | ¿Qué % del fraude total se logra atrapar? | 36,2% |
| **AUC-PR del modelo supervisado** | Área bajo la curva Precision-Recall | ¿Qué tan bien ordena el modelo a las transacciones de más a menos riesgosas? | 0,568 (Random Forest) |
| **% Cobertura (Crítica+Alta)** | Fraude capturado revisando solo las alertas de mayor prioridad / Fraude total | Si el equipo solo tiene capacidad para revisar poco volumen, ¿cuánto fraude igual atrapa? | 81,9% revisando solo el 4,0% del volumen |

## AML / Compliance

| KPI | Fórmula | Qué responde | Valor actual |
|---|---|---|---|
| **Alertas AML generadas** | Cantidad de casos detectados por las 4 tipologías | ¿Cuánta actividad sospechosa se identificó en el período? | 42 (27 ALTO, 15 MEDIO) |
| **Clientes en riesgo ALTO (KYC)** | Clientes con calificación de riesgo AML = ALTO | ¿A cuántos clientes hay que monitorear de cerca? | 31 de 5.000 (0,62%) |
| **% Alertas escaladas a ROS** | Alertas de riesgo ALTO / Total de alertas | ¿Qué proporción de lo detectado amerita un reporte formal a la UIF? | 27/42 = 64,3% |

## Cómo se relacionan entre sí (la historia que cuenta el dashboard)

```
Data Infrastructure (M1)
        │
        ├──> Credit Risk (M2): ¿cuánto espero perder de la cartera actual?
        │         │
        │         └──> Decision Engine (M5): esa misma PD×LGD fija el
        │              precio de CADA préstamo nuevo que se origina
        │
        ├──> Fraud Detection (M3): ¿qué % de las transacciones son fraude,
        │         y cuánto de eso puedo atrapar con recursos limitados?
        │
        └──> AML/Compliance (M4): ¿hay patrones de lavado de dinero en
                  la cartera, y a qué clientes hay que reportar/vigilar?
```

El Dashboard Ejecutivo (M6) es la única pantalla donde un director de riesgo vería las 4 respuestas juntas, sin tener que abrir 4 herramientas distintas — esa es, literalmente, la razón de ser de un dashboard ejecutivo.
