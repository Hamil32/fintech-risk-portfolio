# Módulo 04 — AML / Compliance

**Objetivo:** detectar 4 tipologías de lavado de dinero (structuring, round-tripping, actividad inusual, cash-intensive) alineadas a los estándares GAFI/UIF, calificar el riesgo AML de cada cliente (KYC) y generar borradores de Reporte de Operación Sospechosa (ROS).

> 📘 Ver la explicación completa de cada tipología, sus fórmulas y el porqué de la extensión del modelo de datos en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#6-módulo-04--aml--compliance).
> 📖 Ver [`aml_typologies.md`](aml_typologies.md) para el marco conceptual/regulatorio antes de leer el código.

## Requisito previo

```bash
cd ../01_data_infrastructure
python generate_synthetic_data.py
```

Este módulo depende de los campos `cuenta_destino_id`/`cliente_destino_id` en `transacciones`, agregados específicamente para poder detectar round-tripping — asegurate de tener el dataset regenerado con la versión actual del script.

## Cómo correr este módulo

```bash
cd 04_aml_compliance

python aml_rule_engine.py         # Detecta las 4 tipologías, genera output/aml_alertas.csv
python kyc_validator.py           # Completitud KYC + calificación de riesgo por cliente
python sar_report_generator.py    # Genera borradores de ROS a partir de los casos ALTO
```

⚠️ `sar_report_generator.py` depende del CSV que genera `aml_rule_engine.py` — correrlo primero.

## Archivos

| Archivo | Qué hace |
|---|---|
| `aml_typologies.md` | Marco conceptual: qué es cada tipología y de dónde sale (leer antes del código) |
| `aml_rule_engine.py` | Detecta structuring, round-tripping (self-joins encadenados), actividad inusual y cash-intensive |
| `kyc_validator.py` | Valida completitud de datos y califica el riesgo AML de cada cliente (BAJO/MEDIO/ALTO) |
| `sar_report_generator.py` | Genera un borrador de ROS por cada caso de riesgo ALTO |
| `compliance_report_template.md` | Plantilla de reporte periódico para un comité de Compliance |
| `sql/structuring_detection.sql` | Structuring en SQL puro |
| `sql/round_tripping.sql` | Round-tripping en SQL puro (2 self-joins encadenados) |
| `sql/high_risk_customers.sql` | Barrido de cartera combinando volumen, efectivo, mora y segmento |

## Resultados de esta corrida

| Tipología | Casos detectados |
|---|---|
| Structuring | 15 |
| Round-tripping | 12 |
| Actividad inusual | 5 |
| Cash-intensive | 10 |
| **Total alertas** | **42** (27 ALTO / 15 MEDIO) |

| Calificación de riesgo AML (KYC) | Clientes |
|---|---|
| ALTO | 31 |
| MEDIO | 1.014 |
| BAJO | 3.955 |

## Salidas (en `output/`)

- `aml_alertas.csv` — todas las alertas por tipología
- `kyc_customer_risk_rating.csv` — calificación de riesgo por cliente
- `ros_borradores.md` — un borrador de ROS narrativo por cada caso ALTO
- `ros_indice_casos.csv` — índice tabular de los casos escalados

## Conceptos aplicados (detalle en la Bitácora Técnica)

- Structuring/Smurfing, Round-tripping, Actividad inusual, Cash-intensive (tipologías GAFI)
- Detección de ciclos en un grafo de transferencias mediante self-joins encadenados
- Z-score de volumen mensual/segmento, igual principio que en Módulos 02 y 03
- KYC (Know Your Customer) y calificación de riesgo de cliente
- ROS (Reporte de Operación Sospechosa) — el instrumento real que se presenta a la UIF
