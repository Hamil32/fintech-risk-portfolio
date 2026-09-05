# Tipologías de Lavado de Dinero (AML) — Guía de estudio

Documento de referencia rápida sobre las tipologías implementadas en `aml_rule_engine.py`. Pensado para poder explicar cada una en una entrevista sin tener que mirar el código.

## Marco regulatorio a conocer

| Organismo/Norma | Rol |
|---|---|
| **GAFI / FATF** (Grupo de Acción Financiera Internacional) | Organismo intergubernamental que define los estándares globales AML/CFT (las "40 Recomendaciones") y publica reportes públicos de tipologías reales detectadas en distintos países — [fatf-gafi.org](https://www.fatf-gafi.org) |
| **UIF Argentina** (Unidad de Información Financiera) | Organismo regulador argentino. Recibe los **ROS** (Reporte de Operación Sospechosa) que están obligados a presentar bancos y otros sujetos obligados — [argentina.gob.ar/uif](https://www.argentina.gob.ar/uif) |
| **BCRA** | Regula a las entidades financieras, incluidas sus obligaciones de prevención de lavado de activos. Las comunicaciones específicas se actualizan con frecuencia — **verificá el número de comunicación vigente antes de citarlo en una entrevista**, no lo memorices de una fuente que puede estar desactualizada. |

## Las 4 tipologías implementadas

### 1. Structuring / Smurfing (fraccionamiento)

**Qué es:** dividir una operación grande en varias operaciones pequeñas, cada una por debajo del umbral que obliga a un reporte, para evitar que el banco/regulador la vea.

**Cómo se ve en los datos:** un mismo cliente hace **varias transacciones el mismo día**, cada una por debajo del umbral reportable, cuya **suma** sí sería reportable.

**Implementación:** `aml_rule_engine.py` → función de detección de structuring. Umbral usado: $10.000 🟨 (valor ilustrativo — los umbrales reales de reporte están fijados por norma y se actualizan periódicamente, no es una cifra que deba citarse como vigente).

### 2. Round-tripping (circuito de ida y vuelta)

**Qué es:** el dinero sale de una cuenta, pasa por una o más cuentas de terceros, y **vuelve** a una cuenta relacionada con el originante — al pasar por varias manos, "pierde" su origen aparente.

**Cómo se ve en los datos:** una cadena de transferencias A → B → C → A (o A → B → A) dentro de una ventana de tiempo corta, con montos similares (menos alguna "comisión" del circuito).

**Requisito de datos:** esto **no se puede detectar sin saber quién es el destinatario** de cada transferencia. Por eso el Módulo 01 se extendió para incluir `cuenta_destino_id`/`cliente_destino_id` en las transacciones de tipo TRANSFERENCIA (ver Bitácora Técnica, Módulo 04).

### 3. Actividad inusual (unusual activity)

**Qué es:** un cliente cuyo volumen transaccional se dispara muy por encima de su propio comportamiento histórico, sin una explicación de negocio evidente.

**Cómo se ve en los datos:** el volumen mensual transaccionado por un cliente se aleja más de 3 desvíos estándar de su propio promedio histórico (mismo concepto de z-score que en el Módulo 03, aplicado acá a nivel mensual/cliente en vez de a nivel transacción individual).

### 4. Actividad intensiva en efectivo (cash-intensive)

**Qué es:** depósitos/movimientos frecuentes de efectivo sin una justificación de negocio clara — típico de negocios que se usan como fachada para "mezclar" dinero ilícito con ingresos legítimos declarados en efectivo.

⚠️ **Adaptación al dataset:** el schema de este proyecto no modela un tipo de transacción "DEPÓSITO EN EFECTIVO" separado (los tipos son DEBITO/CREDITO/TRANSFERENCIA/PAGO/EXTRACCION). Se usa `EXTRACCION` (retiro de efectivo) de alta frecuencia y volumen por cajero/sucursal como proxy de esta tipología — es una adaptación razonable dado el schema disponible, no la definición textual de la tipología.

## Lo que NO hace este módulo (limitaciones honestas)

- No reemplaza un sistema real de AML (que integra listas de sanciones internacionales — OFAC, ONU —, verificación de identidad biométrica, y años de historia transaccional).
- Los umbrales usados son ilustrativos, no los umbrales normativos vigentes.
- Las tipologías se **inyectaron deliberadamente** en el dataset sintético (ver `generate_synthetic_data.py`) para poder demostrar la detección — en la realidad, encontrar estos patrones en millones de transacciones legítimas es mucho más difícil (más ruido, patrones más sutiles, actores que aprenden a evadir las reglas conocidas).

## Cómo se dice esto en una entrevista

> *"Implementé 4 tipologías AML alineadas a las categorías que publica GAFI: structuring, round-tripping, actividad inusual y actividad intensiva en efectivo. Para poder detectar round-tripping tuve que extender mi modelo de datos para registrar la contraparte de cada transferencia — sin eso, ningún análisis de flujo de fondos es posible. Uso un ROS (Reporte de Operación Sospechosa) simulado como salida, que es el instrumento real que un banco presenta a la UIF."*
