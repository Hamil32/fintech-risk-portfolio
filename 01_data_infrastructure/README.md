# Módulo 01 — Data Infrastructure

**Objetivo:** construir la base de datos sintética de "Banco Río Digital" que alimenta a todos los módulos siguientes del portfolio (Credit Risk, Fraud Detection, AML/Compliance, Decision Engine, Executive Dashboard).

## Qué genera

Un banco ficticio con:

- **5.000 clientes** (RETAIL / PYME / CORPORATIVO) con score inicial 300–850
- **~9.000 cuentas** (CC, CA, TARJETA) distribuidas entre los clientes
- **50.000 transacciones** en 2023, con ~2% marcadas como fraude
- **2.000 préstamos** (PERSONAL, HIPOTECARIO, PRENDARIO) con estados de mora
- **Scoring histórico trimestral** por cliente (score, PD estimada, segmento de riesgo A–E)

## Modelo de datos

Ver [`schema.sql`](schema.sql) para el DDL completo. Relación entre tablas:

```
clientes 1───N cuentas 1───N transacciones
clientes 1───N prestamos
clientes 1───N scoring_historico
```

## Cómo correr este módulo

Desde la raíz del repo, con el entorno virtual activado:

```bash
cd 01_data_infrastructure

# 1. Generar el dataset sintético (clientes, cuentas, transacciones, préstamos, scoring)
python generate_synthetic_data.py

# 2. Validar la calidad de los datos generados
python data_quality_checks.py

# 3. Correr el ETL: deriva columnas y arma la vista_360_cliente para análisis/Power BI
python etl_pipeline.py
```

## Archivos

| Archivo | Descripción |
|---|---|
| `schema.sql` | Modelo de datos financiero (DDL) |
| `generate_synthetic_data.py` | Genera clientes, cuentas, transacciones, préstamos y scoring histórico |
| `data_quality_checks.py` | Valida unicidad de PKs, integridad referencial, rangos de negocio y consistencia mora/estado |
| `etl_pipeline.py` | Extrae de SQLite, deriva columnas (mora, NPL, horario hábil) y construye `vista_360_cliente` |
| `data/processed/` | Salida: `banco_rio_digital.db` + CSVs (ignorado por git — no se sube data) |

## Salidas

- `data/processed/banco_rio_digital.db` — base SQLite con las 5 tablas
- `data/processed/*.csv` — export de cada tabla + `vista_360_cliente.csv` (un registro por cliente con agregados de cuentas, transacciones y préstamos), lista para Power BI

## Conceptos financieros aplicados

- Tipos de clientes bancarios: retail, pyme, corporativo
- Productos: cuenta corriente, caja de ahorro, tarjeta de crédito, préstamo personal/hipotecario/prendario
- Ciclo de vida de un préstamo: otorgamiento → repago → mora (30/60/90) → incobrable/cancelado
- Categorías de transacciones: débito, crédito, transferencia, pago de servicios, extracción ATM
