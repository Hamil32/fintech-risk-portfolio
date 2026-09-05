# Medidas DAX — Referencia de copy-paste

Todas estas medidas asumen las tablas generadas por `build_dashboard_dataset.py` (`dim_clientes`, `fact_prestamos`, `fact_transacciones`, `dim_vintage`, `fact_roll_rate`, `fact_alertas_aml`) ya cargadas en el modelo, con las relaciones descriptas en `power_bi_build_guide.md`.

Creá una tabla auxiliar vacía llamada **`_Medidas`** (Modelado > Nueva tabla > `_Medidas = {}` o simplemente una tabla en blanco) y pegá todas las medidas ahí — mantiene el panel de campos ordenado en vez de mezclar medidas con columnas de datos.

## Cartera de crédito

```dax
Cartera Total (EAD) = SUM(fact_prestamos[ead])

Cartera NPL = CALCULATE(SUM(fact_prestamos[monto_pendiente]), fact_prestamos[dias_mora] > 90)

NPL Ratio = DIVIDE([Cartera NPL], [Cartera Total (EAD)])

Expected Loss Total = SUM(fact_prestamos[expected_loss])

Expected Loss % = DIVIDE([Expected Loss Total], [Cartera Total (EAD)])

Cantidad de Préstamos = COUNTROWS(fact_prestamos)

PD Promedio Ponderada = DIVIDE(
    SUMX(fact_prestamos, fact_prestamos[pd_asignada] * fact_prestamos[ead]),
    [Cartera Total (EAD)]
)

Tasa de Mora = DIVIDE(
    CALCULATE(SUM(fact_prestamos[monto_pendiente]), fact_prestamos[dias_mora] > 0),
    [Cartera Total (EAD)]
)
```

## Fraude

```dax
Total Transacciones = COUNTROWS(fact_transacciones)

Transacciones Fraudulentas = CALCULATE(COUNTROWS(fact_transacciones), fact_transacciones[es_fraude] = 1)

Tasa de Fraude = DIVIDE([Transacciones Fraudulentas], [Total Transacciones])

Alertas Generadas = CALCULATE(COUNTROWS(fact_transacciones), fact_transacciones[prioridad] <> "SIN ALERTA")

Fraude Capturado (Crítica+Alta) = CALCULATE(
    [Transacciones Fraudulentas],
    fact_transacciones[prioridad] IN {"CRÍTICA", "ALTA"}
)

% Cobertura Crítica+Alta = DIVIDE([Fraude Capturado (Crítica+Alta)], [Transacciones Fraudulentas])

% Volumen Revisado Crítica+Alta = DIVIDE(
    CALCULATE([Total Transacciones], fact_transacciones[prioridad] IN {"CRÍTICA", "ALTA"}),
    [Total Transacciones]
)

Precision Motor de Reglas = DIVIDE(
    CALCULATE([Transacciones Fraudulentas], fact_transacciones[requiere_revision] = 1),
    CALCULATE([Total Transacciones], fact_transacciones[requiere_revision] = 1)
)
```

## AML / Compliance

```dax
Alertas AML Totales = COUNTROWS(fact_alertas_aml)

Alertas AML Alto Riesgo = CALCULATE(COUNTROWS(fact_alertas_aml), fact_alertas_aml[nivel_riesgo] = "ALTO")

Clientes Riesgo Alto (KYC) = CALCULATE(DISTINCTCOUNT(dim_clientes[cliente_id]), dim_clientes[calificacion_riesgo_aml] = "ALTO")

% Cartera de Clientes en Riesgo Alto = DIVIDE(
    [Clientes Riesgo Alto (KYC)],
    DISTINCTCOUNT(dim_clientes[cliente_id])
)
```

## Notas de uso

- Las medidas con `CALCULATE` respetan los filtros de cualquier segmentador (slicer) o filtro de página/visual que agregues — por eso conviene usar medidas y no columnas calculadas para todo lo que sea una agregación (SUM, COUNT, %). Las columnas calculadas se evalúan fila por fila UNA vez; las medidas se recalculan según el contexto de filtro cada vez que se usan en un visual.
- `DIVIDE(a, b)` en vez de `a / b`: devuelve `BLANK()` (en vez de error) si `b` es 0 — buena práctica siempre que dividas en DAX.
- Todas estas fórmulas son las MISMAS que ya calculamos en Python en los Módulos 02/03/04 — acá simplemente se reexpresan en DAX para que Power BI las recalcule dinámicamente al filtrar por segmento, provincia, fecha, etc.
