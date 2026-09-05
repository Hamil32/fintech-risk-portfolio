# Guía de construcción — Dashboard Ejecutivo en Power BI Desktop

**El modelo de datos ya está armado.** Las 6 tablas, las 3 relaciones y las 20 medidas DAX se crearon directamente contra el motor de Power BI Desktop usando el **Power BI Modeling MCP Server** (la extensión oficial de Microsoft) conectado a esta sesión de Claude Code — sin pasar por la UI de "Obtener datos" ni escribir DAX a mano. Ver el detalle completo de cómo se hizo (y los problemas que aparecieron en el camino) en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#8-módulo-06--executive-dashboard).

Lo único que queda — y es lo único que **no** se puede automatizar por MCP/código — es armar los **visuales de las 4 páginas del reporte**. Esta guía te lleva página por página.

## Antes de empezar

Abrí el archivo `.pbix` guardado (ver README del módulo para el nombre/ubicación exacta) y confirmá que el modelo ya esté ahí:

1. Panel **Datos** (a la derecha) → deberías ver 7 tablas: `dim_clientes`, `fact_prestamos`, `fact_transacciones`, `dim_vintage`, `fact_roll_rate`, `fact_alertas_aml`, y `_Medidas` (con las 20 medidas adentro, ícono de calculadora).
2. Vista **Modelo** (ícono de la izquierda) → deberían verse 3 relaciones conectando `dim_clientes` con las 3 tablas de hechos.

Si por algún motivo el modelo no está, avisame y lo reconstruyo — el proceso es 100% reproducible.

## Las 4 páginas del dashboard

### Página 1 — Resumen Ejecutivo

La portada: lo primero que ve alguien que abre el archivo.

| Visual | Campo/Medida | Tipo |
|---|---|---|
| Cartera Total (EAD) | `[Cartera Total (EAD)]` | Tarjeta (Card) |
| NPL Ratio | `[NPL Ratio]` | Tarjeta con formato % |
| Expected Loss % | `[Expected Loss %]` | Tarjeta con formato % |
| Tasa de Fraude | `[Tasa de Fraude]` | Tarjeta con formato % |
| Alertas AML Alto Riesgo | `[Alertas AML Alto Riesgo]` | Tarjeta |
| % Cobertura Crítica+Alta | `[% Cobertura Crítica+Alta]` | Tarjeta — destacar con una nota "revisando solo X% del volumen" |
| Cartera por segmento de score | `fact_prestamos[segmento_score]` (eje) × `[Cartera Total (EAD)]` (valor) | Gráfico de dona |
| Alertas por tipología AML | `fact_alertas_aml[tipologia]` (eje) × conteo de filas | Gráfico de barras |

**Tip de diseño:** poné las 6 tarjetas en una fila arriba, y los 2 gráficos abajo. Usá el mismo color para "riesgo alto" en todas las páginas (ej. rojo/naranja) para que el ojo lo reconozca sin leer la etiqueta.

### Página 2 — Cartera de Crédito

| Visual | Campo/Medida | Tipo |
|---|---|---|
| NPL Ratio | `[NPL Ratio]` | Medidor (Gauge) — target sugerido: 5-8% |
| Expected Loss Total | `[Expected Loss Total]` | Tarjeta |
| Cartera por tipo de préstamo | `fact_prestamos[tipo]` × `[Cartera Total (EAD)]` | Gráfico de torta |
| Cartera y EL por segmento de score | `fact_prestamos[segmento_score]` × `[Cartera Total (EAD)]` y `[Expected Loss %]` | Gráfico de columnas (eje secundario para el %) |
| Vintage analysis | `dim_vintage[cohorte]` (eje) × `dim_vintage[tasa_mora]`, `dim_vintage[tasa_npl]` | Gráfico de líneas |
| Roll rate matrix | `fact_roll_rate[desde]` (filas) × `fact_roll_rate[hacia]` (columnas) × `fact_roll_rate[porcentaje]` (valores) | Matrix, con **formato condicional** (escala de color rojo-verde invertida: 100% en la diagonal se ve "bien" en verde) |
| Top 10 clientes por exposición | `dim_clientes[nombre]`, `dim_clientes[segmento]` (filas) × `SUM(fact_prestamos[monto_pendiente])` (valor) | Tabla, con **filtro Top N = 10** ordenado descendente |

### Página 3 — Fraude

| Visual | Campo/Medida | Tipo |
|---|---|---|
| Tasa de Fraude | `[Tasa de Fraude]` | Tarjeta |
| Alertas Generadas | `[Alertas Generadas]` | Tarjeta |
| % Cobertura Crítica+Alta | `[% Cobertura Crítica+Alta]` | Tarjeta |
| Fraude por canal y horario | `fact_transacciones[canal]` (filas) × `HOUR(fact_transacciones[fecha])` (columnas, ver nota abajo) × `[Tasa de Fraude]` | Matrix |
| Evolución mensual de fraude | `fact_transacciones[fecha]` (jerarquía de fecha, nivel Mes) × `[Tasa de Fraude]` | Gráfico de líneas |
| Distribución de alertas por prioridad | `fact_transacciones[prioridad]` × conteo | Gráfico de barras (ordenar manualmente CRÍTICA, ALTA, MEDIA, SIN ALERTA) |

**Nota — columna de hora:** `fact_transacciones[fecha]` viene con fecha y hora completas. Para poder agrupar por franja horaria, creá una **columna calculada** en Power Query o DAX:
```dax
Hora = HOUR(fact_transacciones[fecha])
```

### Página 4 — AML / Compliance

| Visual | Campo/Medida | Tipo |
|---|---|---|
| Alertas AML Totales | `[Alertas AML Totales]` | Tarjeta |
| Alertas AML Alto Riesgo | `[Alertas AML Alto Riesgo]` | Tarjeta |
| Clientes Riesgo Alto (KYC) | `[Clientes Riesgo Alto (KYC)]` | Tarjeta |
| Alertas por tipología y nivel de riesgo | `fact_alertas_aml[tipologia]` (filas) × `fact_alertas_aml[nivel_riesgo]` (columnas) × conteo | Tabla o Matrix |
| Alertas por segmento de cliente | `fact_alertas_aml[segmento]` × conteo | Gráfico de barras |
| Distribución de calificación de riesgo AML | `dim_clientes[calificacion_riesgo_aml]` × `DISTINCTCOUNT(dim_clientes[cliente_id])` | Gráfico de torta (BAJO=verde, MEDIO=amarillo, ALTO=rojo) |

## Para llevarlo más lejos (opcional)

- **Segmentadores (slicers) globales** en cada página: `dim_clientes[segmento]` y un rango de fechas — así el dashboard deja de ser estático y se puede explorar.
- **Tabla de fechas dedicada:** para que las medidas de tiempo (evolución mensual) funcionen perfecto con Time Intelligence de DAX, creá:
  ```dax
  Dim_Fecha = CALENDAR(DATE(2023,1,1), DATE(2023,12,31))
  ```
  y marcala como "Tabla de fechas" (botón derecho > Marcar como tabla de fechas). No es obligatorio para lo que pide este módulo, pero es la práctica correcta si vas a seguir iterando el dashboard.
- **Publicar a Power BI Service:** `Archivo > Publicar > Publicar en Power BI` (necesita una cuenta, la versión gratis alcanza para portfolio personal) — te da un link para compartir el dashboard sin que la otra persona necesite tener Power BI Desktop instalado.

## Checklist final antes de mostrarlo en una entrevista

- [ ] Las 4 páginas cargan sin errores de relación (fijate que no haya líneas punteadas raras en la vista Modelo)
- [ ] Todas las tarjetas de % están formateadas como porcentaje, no como decimal (0.06 vs 6%)
- [ ] El roll rate matrix tiene formato condicional aplicado
- [ ] Podés explicar, para cada número en pantalla, de qué script de Python salió el dato de base — practicá esto, es lo que te van a preguntar
