# 📘 Bitácora Técnica — FINTECH Risk Portfolio

**Propósito de este documento:** explicar, módulo por módulo, **qué se construyó, cómo, con qué lógica/fórmula, y de dónde sale cada criterio** — separando siempre dos cosas que suelen mezclarse en un dataset sintético:

- 🟦 **Metodología real** → conceptos, fórmulas y convenciones que se usan de verdad en la industria financiera (Basel, BCRA, prácticas de riesgo/fraude). Esto es lo que tenés que poder explicar en una entrevista con total seguridad.
- 🟨 **Parámetro ilustrativo** → un número concreto (una media, un peso, un umbral) que elegí para que el dataset sintético se vea realista, pero que **no está calibrado contra una estadística oficial publicada**. Importante decirlo así en una entrevista: *"el criterio es real, el número exacto es una aproximación razonable para la simulación"*.

Este documento se actualiza a medida que avanzamos de módulo. No reemplaza al [`FINTECH_RISK_PORTFOLIO_INSTRUCTIVO.md`](FINTECH_RISK_PORTFOLIO_INSTRUCTIVO.md) (que es el plan), sino que registra **la implementación real** — qué se hizo distinto al plan, qué se corrigió, y por qué.

---

## Índice

1. [Cómo leer este documento](#1-cómo-leer-este-documento)
2. [Decisiones de arquitectura general](#2-decisiones-de-arquitectura-general)
3. [Módulo 01 — Data Infrastructure](#3-módulo-01--data-infrastructure)
4. [Módulo 02 — Credit Risk Analytics](#4-módulo-02--credit-risk-analytics)
5. [Glosario acumulado](#5-glosario-acumulado)
6. [Cómo revisar vos mismo cada módulo](#6-cómo-revisar-vos-mismo-cada-módulo)
7. [Fuentes y referencias](#7-fuentes-y-referencias)
8. [Registro de cambios](#8-registro-de-cambios)

---

## 1. Cómo leer este documento

Cada módulo tiene la misma estructura:

1. **Qué problema de negocio resuelve** (por qué existe este módulo en un banco real)
2. **Qué se construyó** (archivos, con link)
3. **Cómo funciona, paso a paso** (la lógica del código, explicada en lenguaje simple)
4. **Fórmulas usadas** — con el detalle 🟦 metodología real / 🟨 parámetro ilustrativo
5. **Resultados obtenidos** al correrlo (números reales de esta ejecución, no inventados)
6. **Qué te van a preguntar en una entrevista sobre esto** y cómo contestar

---

## 2. Decisiones de arquitectura general

| Decisión | Por qué |
|---|---|
| **SQLite** como base de datos | No requiere instalar un servidor, el archivo `.db` es portable, y es más que suficiente para 5.000–50.000 filas. En un banco real esto sería Oracle/SQL Server/Teradata, pero la lógica SQL que vas a escribir es la misma. |
| **Un `venv` por proyecto** | Aísla las librerías de este proyecto de cualquier otra cosa que tengas instalada en tu Python global. Es la práctica estándar en cualquier equipo de datos. |
| **`data/raw/` y `data/processed/` ignorados por git** | Los datos (aunque sean sintéticos) no se versionan en git — son grandes, se regeneran con un script, y esa es la práctica real en la industria (los datasets no van al repo, sí el código que los genera/procesa). Por eso `.gitignore` excluye `*.csv`, `*.db` y las carpetas `data/raw/` y `data/processed/` en cualquier módulo. |
| **Un módulo = una carpeta con su propio README** | Cada módulo se puede leer, correr y evaluar de forma independiente — así un reclutador (o vos en 6 meses) puede entrar a `02_credit_risk/` sin tener que entender todo el repo primero. |
| **`Faker('es_AR')`** | Genera nombres, DNIs y textos con formato argentino, para que el dataset "se sienta" local. Es un generador de datos ficticios — no usa ni se conecta a ninguna base de datos real de personas. |

---

## 3. Módulo 01 — Data Infrastructure

### 3.1 Qué problema de negocio resuelve

Todo análisis de riesgo, fraude o AML necesita datos: clientes, cuentas, movimientos, préstamos. En un banco real estos datos viven en sistemas core bancarios (core banking) y datawarehouses. Como no tengo acceso a datos reales de un banco (por razones obvias de confidencialidad y porque no trabajé en uno), este módulo **construye un banco ficticio completo** ("Banco Río Digital") con datos sintéticos pero **estructuralmente realistas**: mismas tablas, mismas relaciones, mismos tipos de campos que un banco real usaría.

Esto es lo que en la industria se llama un **dataset sintético para desarrollo/testing** — una práctica genuina (los bancos también generan datos sintéticos para probar modelos sin exponer datos reales de clientes, por regulaciones de protección de datos).

### 3.2 Qué se construyó

| Archivo | Rol |
|---|---|
| [`01_data_infrastructure/schema.sql`](01_data_infrastructure/schema.sql) | Define las 5 tablas y sus relaciones (DDL) |
| [`01_data_infrastructure/generate_synthetic_data.py`](01_data_infrastructure/generate_synthetic_data.py) | Genera los datos y los guarda en SQLite + CSV |
| [`01_data_infrastructure/data_quality_checks.py`](01_data_infrastructure/data_quality_checks.py) | Valida que los datos generados sean consistentes |
| [`01_data_infrastructure/etl_pipeline.py`](01_data_infrastructure/etl_pipeline.py) | Transforma los datos crudos en vistas curadas para análisis |

### 3.3 El modelo de datos (`schema.sql`)

```
clientes (1) ──< (N) cuentas (1) ──< (N) transacciones
clientes (1) ──< (N) prestamos
clientes (1) ──< (N) scoring_historico
```

| Tabla | Qué representa | Por qué estos campos |
|---|---|---|
| **clientes** | La persona/empresa titular de la relación con el banco | `segmento` (RETAIL/PYME/CORPORATIVO) es la primera variable que cualquier banco usa para diferenciar política de riesgo — un corporativo se evalúa distinto que una persona física. `score_inicial` (300–850) es el score crediticio base del cliente. |
| **cuentas** | Los productos transaccionales del cliente | `tipo_cuenta` distingue CC (cuenta corriente, típicamente pymes/empresas), CA (caja de ahorro, retail) y TARJETA (línea de crédito revolving, con saldo negativo = deuda consumida). |
| **transacciones** | Cada movimiento de dinero | `es_fraude` es el "ground truth" (la etiqueta real) que en Módulo 03 se va a usar para *evaluar* qué tan bueno es el motor de detección — en la vida real esta etiqueta la generan las disputas/chargebacks confirmados, acá la simulamos nosotros. |
| **prestamos** | Cada línea de crédito otorgada | `estado` y `dias_mora` son el corazón del Módulo 02 (riesgo crediticio): de acá sale el cálculo de PD, NPL, vintage, etc. |
| **scoring_historico** | La evolución del score de cada cliente en el tiempo | Sin esto no se podría hacer un análisis de *cómo cambia el riesgo de un cliente*, algo que todo banco monitorea (re-scoring periódico). |

🟦 **Metodología real:** la escala de score **300–850** es la escala clásica de credit scoring (popularizada por FICO en EE.UU.), y es el estándar de facto que la mayoría de scorecards del mundo —incluidos muchos desarrollados en fintechs argentinas— adaptan aunque no usen "FICO" textualmente. BCRA no publica un score único con esta escala (cada entidad tiene su propio modelo interno), pero usar 300–850 es una convención ampliamente entendida en la industria y válida para un portfolio demostrativo.

### 3.4 `generate_synthetic_data.py`, paso a paso

**Paso 1 — Clientes.** Por cada cliente se sortea un segmento (`RETAIL` 80% / `PYME` 15% / `CORPORATIVO` 5%) y, según el segmento, un score con **distribución Normal**:

```
score = clip( Normal(μ, σ), min, max )

CORPORATIVO:  μ=720, σ=60   → clip(500, 850)
PYME:         μ=640, σ=80   → clip(400, 820)
RETAIL:       μ=580, σ=100  → clip(300, 800)
```

- 🟦 **Real:** usar una distribución Normal para modelar un score es estándar en estadística — los scores de crédito, cuando se agregan muchos clientes, tienden a distribuirse aproximadamente así. Y el hecho de que **corporativo > pyme > retail** en score promedio también es real: las empresas grandes tienen balances auditados, más colateral y más historial verificable, por eso los bancos las consideran (en promedio) de menor riesgo relativo.
- 🟨 **Ilustrativo:** los valores exactos de μ y σ (720/60, 640/80, 580/100) son una aproximación razonable mía, no salen de una publicación de BCRA con la distribución real de scores del sistema financiero argentino (esa información no es pública a ese nivel de detalle).
- El `clip(...)` (recortar el valor a un rango) asegura que ningún score generado quede fuera de la escala 300–850, aunque la distribución Normal en teoría puede generar valores extremos.

Los pesos de `provincias` (CABA 35%, Buenos Aires 30%, etc.) son 🟨 ilustrativos: buscan reflejar que la actividad bancaria en Argentina está concentrada en CABA/GBA, sin ser una cifra tomada de un censo o reporte de BCRA.

**Paso 2 — Cuentas.** Cada cliente tiene entre 1 y 3 cuentas (55% / 35% / 10%), con tipo elegido según su segmento (un corporativo tiene más chance de tener cuenta corriente que caja de ahorro). El saldo se genera con **distribución Log-Normal**:

```
saldo = LogNormal(μ, σ)
```

- 🟦 **Real:** los montos de dinero (saldos, montos de transacción, ingresos) casi nunca se distribuyen de forma Normal — se distribuyen con **cola larga a la derecha** (muchas cuentas con saldo bajo/moderado, pocas cuentas con saldo muy alto). La distribución Log-Normal es la elección estándar en econometría y en modelado financiero para este tipo de variable, precisamente porque nunca es negativa y tiene esa cola larga.
- El saldo de `TARJETA` se genera en negativo — representa la deuda consumida de la línea de crédito, no una "plata a favor" del cliente.

**Paso 3 — Transacciones.** Se generan 50.000 transacciones. El 2% (1.000) se marcan como fraudulentas *a propósito*, con un patrón distinto al resto:

| | Transacción normal | Transacción fraude (simulada) |
|---|---|---|
| Monto | `LogNormal(8, 1.5)` → mayormente bajo, algunos altos | Uniforme entre $5.000 y $50.000 (más alto en promedio) |
| Canal | Distribución realista entre APP/Home Banking/POS/ATM/Sucursal | Concentrado en APP/Home Banking (canales digitales, típico en fraude de toma de cuenta) |
| Horario | 8am–10pm (horario habitual de actividad) | Madrugada (1am–5am) |

- 🟦 **Real:** estos tres patrones (monto más alto, canal digital, horario de madrugada) son señales genuinas que usan los motores antifraude reales — no me los inventé, son los mismos que vas a implementar como reglas en el Módulo 03 (`velocity check`, `amount anomaly`, `horario sospechoso`).
- 🟨 **Ilustrativo:** la **tasa de fraude del 2%** es deliberadamente alta comparada con la realidad. En el mundo real, la tasa de fraude en transacciones con tarjeta suele estar muy por debajo del 1% (según reportes de redes de tarjetas, del orden de 0.1%–0.3%). Se usa 2% acá **a propósito**, porque con una tasa real tan baja el dataset tendría muy pocos casos positivos para poder entrenar/evaluar un modelo de forma didáctica. Esta es la misma razón por la que datasets públicos de fraude (como el de Kaggle "Credit Card Fraud Detection") también sobre-representan el fraude respecto a la tasa real. **Esto hay que decirlo explícitamente en una entrevista** si preguntan por la tasa de fraude del dataset.

**Paso 4 — Préstamos.** Solo el 40% de los clientes tiene un préstamo. Según el score del cliente, se sortea un estado de mora con esta lógica:

```python
if score >= 700:  # buen score
    estados = [VIGENTE 75%, CANCELADO 20%, MORA_30 5%]
elif score >= 550:  # score medio
    estados = [VIGENTE 60%, CANCELADO 20%, MORA_30 13%, MORA_60 7%]
else:  # score bajo
    estados = [VIGENTE 40%, MORA_30 20%, MORA_60 18%, MORA_90 12%, INCOBRABLE 10%]
```

- 🟦 **Real, y es el concepto más importante del dataset:** esto codifica la relación fundamental de todo modelo de riesgo crediticio — **a menor score, mayor probabilidad de mora/default**. Un score de crédito *se construye* precisamente para que tenga esa relación monotónica con el riesgo de impago. Todo lo que vas a calcular en el Módulo 02 (PD, Expected Loss) depende de que esta relación exista en los datos, igual que existe en la cartera real de cualquier banco.
- Los **umbrales de días de mora** (30 / 60 / 90) 🟦 sí son una convención real, no inventada: BCRA (y Basel a nivel internacional) clasifican a los deudores en categorías de riesgo crecientes según los días de atraso en el pago, y **90 días** es el umbral internacionalmente aceptado (Basel) para considerar un préstamo como **NPL — Non-Performing Loan** (préstamo en incumplimiento). Vas a ver este mismo umbral de 90 días reaparecer en el Módulo 02 al calcular la tasa de NPL de la cartera.
- 🟨 **Ilustrativo:** los porcentajes exactos (75%/20%/5%, etc.) son una aproximación razonable mía para que la cartera simulada "se comporte bien" en los análisis siguientes, no son la tasa de mora real y pública del sistema financiero argentino (que además varía mucho según el año — la Argentina tuvo períodos con mora muy alta y otros muy baja).
- Las tasas de interés y montos por tipo de préstamo (`PERSONAL` 15–30% anual y $50k–$2M; `PRENDARIO` 12–20% y $500k–$5M; `HIPOTECARIO` 8–15% y $5M–$50M) codifican un principio real de pricing por riesgo: **a menor garantía, mayor tasa** — un préstamo personal no tiene colateral (si el cliente no paga, el banco pierde casi todo), por eso su tasa es la más alta; un hipotecario tiene como garantía el inmueble, por eso es el más barato. Esto es literalmente el concepto de **LGD** (Loss Given Default) que vas a formalizar con números en el Módulo 02.

**Paso 5 — Scoring histórico.** Para cada cliente se genera un score por trimestre, como un "paseo aleatorio" (random walk) partiendo del score inicial:

```
score_t = clip( score_(t-1) + Normal(0, 15), 300, 850 )
```

- 🟦 **Real:** modelar la evolución de un score como un random walk (variación aleatoria pequeña alrededor del valor anterior, sin tendencia forzada) es la forma más simple y honesta de simular que el riesgo de un cliente **no es estático** — mejora o empeora levemente con el tiempo, sin necesidad de inventar una causa específica.
- 🟨 **Ilustrativo:** la magnitud de la variación (`σ=15` puntos por trimestre) es un valor razonable elegido por mí, no calibrado contra datos reales de volatilidad de score.

**Paso 6 — Persistencia.** Todo se guarda en `data/processed/banco_rio_digital.db` (SQLite, para SQL) y en CSVs equivalentes (para Power BI, que no lee SQLite de forma nativa cómoda).

### 3.5 `data_quality_checks.py` — por qué importa

En cualquier banco real, antes de que un dato "crudo" se use para calcular riesgo, pasa por controles de calidad — esto no es opcional, es parte de lo que se llama **gobierno de datos** (data governance), y reguladores como BCRA exigen a las entidades poder demostrar la integridad de los datos usados en sus modelos de riesgo.

El script corre 20 chequeos divididos en 4 categorías:

| Categoría | Qué valida | Por qué importa en un banco real |
|---|---|---|
| **Unicidad de PK** | Que `cliente_id`, `dni`, `cuenta_id`, etc. no tengan duplicados | Un DNI duplicado significaría que hay dos "clientes" que en realidad son la misma persona — rompe cualquier cálculo de exposición total por cliente. |
| **Nulos en campos críticos** | Que campos como `score_inicial` o `monto` no tengan nulos | Un score nulo no se puede clasificar en ningún segmento de riesgo — silenciosamente desaparecería del análisis o rompería el cálculo. |
| **Integridad referencial** | Que toda `cliente_id` en `transacciones`/`prestamos`/`cuentas` exista en `clientes` | Si una transacción apunta a un cliente que no existe, es un dato huérfano — típicamente señal de un bug en el ETL de origen. |
| **Rangos y consistencia de negocio** | Score entre 300–850, montos > 0, `dias_mora` coherente con el `estado` (ej: no puede estar en `MORA_90` con solo 5 días de atraso) | Estas son las reglas de negocio del dominio — un chequeo puramente técnico (¿es nulo? ¿es único?) no las detecta, hace falta codificar el conocimiento del negocio. |

**Resultado de la última corrida:** 20/20 chequeos en **OK**, 0 warnings, 0 errores.

### 3.6 `etl_pipeline.py` — Extract, Transform, Load

Este script toma los datos "crudos" recién generados y los deja listos para análisis:

- **Extract:** lee las 5 tablas desde SQLite.
- **Transform:**
  - Deriva `anio_mes` y `hora` de cada transacción (para poder agrupar por período/horario en Power BI sin recalcular esto en cada dashboard).
  - Deriva `en_mora` y `es_npl` (`dias_mora > 90`) en préstamos — formaliza el umbral de NPL mencionado arriba como una columna reutilizable.
  - Construye **`vista_360_cliente`**: un registro por cliente con todo lo relevante agregado (saldo total, cantidad de transacciones, monto transaccionado, cantidad de fraudes asociados, deuda pendiente, préstamos en mora/NPL).
- **Load:** exporta `transacciones_curadas.csv`, `prestamos_curados.csv` y `vista_360_cliente.csv`.

🟦 **Real:** la "vista 360 del cliente" es un concepto genuino y muy usado en banca — es la tabla que consultan las áreas de riesgo, cobranzas y comercial para ver *todo* lo que un banco sabe de un cliente en una sola fila, en vez de tener que hacer joins manuales cada vez.

### 3.7 Resultados obtenidos (corrida real, no simulada en este documento)

```
Clientes:            5.000   (score promedio: 594)
Cuentas:             7.714
Transacciones:       50.000  (1.000 marcadas como fraude, 2.0%)
Préstamos:           2.000
  VIGENTE:      845 (42.2%)
  CANCELADO:    364 (18.2%)
  MORA_90:      247 (12.3%)
  MORA_30:      237 (11.8%)
  MORA_60:      176 (8.8%)
  INCOBRABLE:   131 (6.6%)
Scoring histórico:   20.000  (4 trimestres × 5.000 clientes)

Data quality checks: 20/20 OK
```

> Nota: estos números difieren de la primera corrida (documentada originalmente) porque, al construir el Módulo 02, se detectó y corrigió un bug en `asignar_estado_mora()` — ver el hallazgo completo en la [sección 3.9](#39-hallazgo-la-pd-no-salía-monótona-y-cómo-se-corrigió). El dataset se regeneró después del fix, así que estos son los valores vigentes.

### 3.8 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Estos son datos reales?" | "No, es un dataset sintético que generé yo mismo con Python (Faker + numpy) para poder construir y demostrar toda la metodología de riesgo/fraude/AML sin depender de acceso a datos bancarios reales, que por regulación no están disponibles públicamente." |
| "¿Por qué SQLite y no una base más 'seria'?" | "Porque para el volumen del dataset (decenas de miles de filas) es suficiente y portable — el diseño del schema y las queries SQL son idénticas a las que escribiría contra Oracle o SQL Server en un banco real." |
| "¿Cómo garantizás la calidad de los datos?" | "Con un script de data quality checks que corre 20 validaciones: integridad referencial, unicidad de claves, rangos de negocio y consistencia entre campos relacionados (ej: días de mora vs. estado del préstamo)." |
| "¿Por qué el score va de 300 a 850?" | "Es la escala convencional de credit scoring, popularizada por FICO, que uso como referencia estándar de la industria — no es la escala oficial de BCRA (que no publica una única escala nacional), pero es ampliamente reconocida." |

### 3.9 Hallazgo: la PD no salía monótona, y cómo se corrigió

Esto es un ejemplo real de algo que pasa constantemente en un trabajo de riesgo: **el dato no se comporta como debería, y hay que investigar por qué antes de seguir**. Vale la pena documentarlo porque el proceso de encontrarlo es tan importante como el resultado.

**Sospecha inicial:** al calcular la PD histórica por segmento de score en el Módulo 02, el resultado fue:

| Segmento | PD histórica (antes del fix) |
|---|---|
| E (muy alto riesgo) | 11.1% |
| D (alto riesgo) | 20.5% |
| C (riesgo medio) | 10.1% |
| B (riesgo bajo) | 0.0% |
| A (muy bajo riesgo) | 0.0% |

Esto **no tiene sentido de negocio**: el segmento E (el peor score) mostraba *menos* default que el D, y B/A mostraban 0% — algo está mal, porque la premisa de todo el proyecto es justamente que a peor score, peor comportamiento de pago.

**Causa raíz:** la función original `asignar_estado_mora()` (Módulo 01) usaba solo **dos umbrales discretos** (score ≥ 700 y score ≥ 550) para decidir qué estados de mora eran *posibles* para un préstamo:

- Con score ≥ 700 → solo podía terminar en `VIGENTE`, `CANCELADO` o `MORA_30`. **Nunca** en `MORA_90`/`INCOBRABLE`.
- Con score entre 550 y 699 → tampoco podía llegar a `MORA_90`/`INCOBRABLE`.
- Con score < 550 → sí podía llegar a default, pero con **la misma probabilidad sin importar si el score era 549 o 300**.

Esto generaba dos problemas: (1) los segmentos B y A del Módulo 02 (score 600-850) caían enteramente en el rango "nunca default" → 0% siempre, sin importar los datos; y (2) dentro del rango <550, un cliente con score 549 y uno con score 300 tenían exactamente la misma probabilidad de terminar incobrable — por eso el segmento E (muy pocos clientes, ~54) mostraba una PD más baja que D solo por variabilidad de muestra pequeña, no por una relación real.

**La corrección:** se reemplazaron los 2-3 umbrales discretos por una **función logística continua** que mapea score → probabilidad de default:

```
PD(score) = PD_min + (PD_max - PD_min) / (1 + e^((score - score_mid) / escala))
```

con `PD_min=0.5%`, `PD_max=45%`, `score_mid=550`, `escala=60`. Esta es la misma familia de función que usa un modelo real de regresión logística para convertir un score en una probabilidad — no es un truco, es la forma estándar de modelar esta relación (🟦 metodología real). El préstamo cae en default (`MORA_90`/`INCOBRABLE`) con esa probabilidad exacta según el score puntual del cliente, sin escalones. Se aplicó la misma lógica para decidir mora temprana (`MORA_30`/`MORA_60`) con una segunda curva logística.

**Resultado después del fix:**

| Segmento | PD histórica (después del fix) |
|---|---|
| E (muy alto riesgo) | 50.0% |
| D (alto riesgo) | 39.7% |
| C (riesgo medio) | 24.1% |
| B (riesgo bajo) | 8.3% |
| A (muy bajo riesgo) | 2.4% |

Ahora sí es **monótona decreciente** — exactamente lo que se espera de un score bien construido, y lo que necesitábamos para que el resto del Módulo 02 (Expected Loss, scorecard) tuviera sentido. El código corregido está en [`generate_synthetic_data.py`](01_data_infrastructure/generate_synthetic_data.py), función `calcular_pd_score()` / `calcular_pd_mora_temprana()` / `asignar_estado_mora()`.

**Cómo contarlo en una entrevista:** *"Al calcular la PD por segmento me di cuenta de que no era monótona — investigué y encontré que la lógica de generación de mora usaba umbrales discretos que no eran consistentes con la segmentación de score que estaba usando para el análisis. Lo corregí modelando la PD como una función logística continua del score, y validé que el resultado final sí fuera monótono antes de seguir."* Esto demuestra exactamente el tipo de control de calidad que se espera de un analista de riesgo.

---

## 4. Módulo 02 — Credit Risk Analytics

### 4.1 Qué problema de negocio resuelve

Un banco no puede simplemente "sentir" que su cartera de crédito es riesgosa — necesita **cuantificar cuánto espera perder**, para: (a) constituir previsiones/provisiones contables acordes, (b) fijar el precio (tasa) de cada crédito según su riesgo, y (c) decidir a quién prestarle. Ese es exactamente el problema que resuelve este módulo: tomar la cartera de préstamos del Módulo 01 y calcular las métricas estándar de riesgo crediticio (PD, LGD, EAD, Expected Loss), analizar cómo evoluciona la calidad de la cartera en el tiempo (vintage, roll rate), y construir la herramienta que decide el riesgo de un cliente nuevo: el **scorecard**.

### 4.2 Qué se construyó

| Archivo | Rol |
|---|---|
| [`02_credit_risk/pd_lgd_ead.py`](02_credit_risk/pd_lgd_ead.py) | PD histórica, LGD asumido, EAD y Expected Loss por préstamo |
| [`02_credit_risk/vintage_analysis.py`](02_credit_risk/vintage_analysis.py) | Tasa de mora/NPL por cohorte de originación |
| [`02_credit_risk/roll_rate_matrix.py`](02_credit_risk/roll_rate_matrix.py) | Matriz de transición de segmento de riesgo entre trimestres |
| [`02_credit_risk/credit_scorecard.py`](02_credit_risk/credit_scorecard.py) | Scorecard de puntos: WOE/IV + regresión logística + escalado |
| [`02_credit_risk/sql/`](02_credit_risk/sql/) | Las mismas métricas replicadas en SQL puro |

### 4.3 `pd_lgd_ead.py` — PD, LGD, EAD y Expected Loss

**PD (Probability of Default) histórica por segmento:** se agrupan los préstamos por el mismo bin de score A-E usado en el Módulo 01 (300-400-500-600-700-850), y se calcula la proporción de préstamos en default (`MORA_90` o `INCOBRABLE`, es decir, mora > 90 días — el umbral NPL de Basilea) dentro de cada segmento:

```
PD_segmento = (# préstamos en default en el segmento) / (# préstamos totales en el segmento)
```

🟦 **Real:** usar la PD *histórica observada* de la propia cartera como estimador de la PD "a futuro" de ese segmento es exactamente el enfoque que siguen los bancos bajo el modelo IRB de Basilea — la PD de un segmento/rating se calibra contra el comportamiento histórico real de los préstamos de ese segmento (con varios años de historia, idealmente un ciclo económico completo). Acá se usa un solo año porque es el horizonte del dataset sintético, pero la lógica de cálculo es la misma.

📝 *Nota de implementación:* la versión original del instructivo proponía valores de PD fijos e inventados por segmento (25%/15%/8%/3%/1%). Se cambió por la PD histórica calculada directamente del dataset, porque es más honesto metodológicamente: la PD asignada a un segmento debe **surgir de los datos**, no inventarse a mano.

**LGD (Loss Given Default) por tipo de garantía:**

| Tipo de préstamo | LGD asumido | Por qué |
|---|---|---|
| HIPOTECARIO | 25% | Garantía real (el inmueble) → alto recupero |
| PRENDARIO | 45% | Garantía real pero de menor valor de reventa (vehículo) |
| PERSONAL | 75% | Sin garantía → bajo recupero |

🟦 **Real:** la relación "a menor garantía, mayor LGD" es un principio central de la gestión de riesgo crediticio y de Basilea II — el colateral es lo que el banco puede recuperar (ejecutando la garantía) si el cliente no paga. 🟨 **Ilustrativo:** los porcentajes exactos (25%/45%/75%) son valores de referencia razonables para el mercado argentino, no una cifra oficial publicada por BCRA para estos productos específicos.

**EAD (Exposure at Default):** se usa el `monto_pendiente` (saldo actual de la deuda) como proxy del monto que estaría expuesto si el cliente cae en default hoy. 🟦 Esta es la simplificación estándar para carteras de cuota fija (a diferencia de líneas revolving como tarjetas de crédito, donde el EAD requiere un factor de conversión de crédito — *Credit Conversion Factor* — porque el cliente podría seguir consumiendo el límite disponible antes de caer en default).

**Expected Loss:**

```
EL = PD × LGD × EAD
```

🟦 Esta es *la* fórmula central del enfoque IRB de Basilea II — no tiene componente ilustrativo, es la definición formal de pérdida esperada.

**Resultados de esta corrida:**

```
Cartera total (EAD):        $6.517.181.548
NPL (mora > 90 días):       $488.932.897   (7.50% de la cartera)
Expected Loss total:        $385.435.888   (5.91% de la cartera)

PD histórica por segmento:      Expected Loss como % de esa cartera:
  E (muy alto riesgo):  50.0%     14.63%
  D (alto riesgo):      39.7%     11.66%
  C (riesgo medio):     24.1%      7.32%
  B (riesgo bajo):       8.3%      2.46%
  A (muy bajo riesgo):   2.4%      0.73%

Expected Loss por tipo de préstamo (% de esa cartera):
  PERSONAL:     14.83%  (LGD alto, sin garantía)
  PRENDARIO:     8.88%
  HIPOTECARIO:   4.97%  (LGD bajo, con garantía real)
```

Todo monótono y consistente con la teoría: a peor segmento, mayor % de Expected Loss sobre su propia cartera; y el tipo de préstamo sin garantía concentra proporcionalmente más pérdida esperada aunque tenga menor PD asignada individual, porque su LGD es mucho más alto.

### 4.4 `vintage_analysis.py` — Vintage Analysis

Agrupa los préstamos por **trimestre de originación** (`fecha_otorgamiento`) y calcula, para cada cohorte, qué porcentaje terminó en mora o en NPL:

```
tasa_mora_cohorte = (# préstamos en mora de esa cohorte) / (# préstamos totales de esa cohorte)
```

🟦 **Real:** esta es la pregunta que cualquier área de riesgo de admisión se hace constantemente: *"¿la política de originación de los últimos trimestres está produciendo peores créditos que antes?"*. Si la tasa de mora sube de forma sostenida en las cohortes más recientes, es una señal de alerta temprana (antes incluso de que esos préstamos lleguen a mora avanzada, porque se los compara "a la misma edad" contra cohortes anteriores — en un análisis más completo se compararía a igual cantidad de meses desde el otorgamiento, no a fecha de corte fija; acá se simplifica comparando el estado actual de cada cohorte).

**Resultado de esta corrida:** tasa de mora promedio de las cohortes más antiguas 39.95% vs. 38.89% en las más recientes → lectura: cartera **estable/levemente mejor** en originación reciente, sin señales de deterioro.

### 4.5 `roll_rate_matrix.py` — Roll Rate Matrix

Mide qué porcentaje de clientes en un segmento de riesgo (A-E) migra a otro segmento entre un trimestre y el siguiente. Se construye una **matriz de transición de Markov de primer orden**: para cada par de trimestres consecutivos, se cruza el segmento "desde" contra el segmento "hacia", y se calcula el porcentaje de fila:

```
%(desde=X, hacia=Y) = (# clientes que estaban en X y pasaron a Y) / (# clientes totales que estaban en X)
```

⚠️ **Adaptación metodológica importante:** el roll rate clásico de la industria se calcula sobre **buckets de mora de un préstamo puntual** (0 días → 30 → 60 → 90) mes a mes. Este dataset no tiene un historial mensual de mora por préstamo — tiene un historial **trimestral del segmento de riesgo del cliente** (`scoring_historico`). Se aplicó el mismo concepto matemático (matriz de transición de Markov) sobre esa serie disponible. La lógica de negocio es análoga (cuantifica flujo hacia mejor/peor riesgo), pero es importante poder explicar esta diferencia si te preguntan por el detalle — no es el roll rate "de manual" pero sí una aplicación correcta y honesta del mismo concepto sobre los datos que el dataset realmente tiene.

**Resultado de esta corrida** (matriz promedio entre los 4 trimestres del dataset):

- 89.1% de los clientes se mantiene en el mismo segmento de riesgo de un trimestre a otro.
- 6.1% mejora de segmento ("roll-back").
- 4.8% empeora de segmento ("roll-forward").
- Ningún cliente salta más de un segmento en un trimestre (ej: nadie pasa de A a C directamente) — comportamiento esperable de un score que cambia gradualmente.

### 4.6 `credit_scorecard.py` — Scorecard de crédito (WOE + Regresión Logística + Puntos)

Esta es la pieza más avanzada del módulo. Sigue la metodología descripta en el libro de referencia de la industria: **Naeem Siddiqi, *Credit Risk Scorecards*** — el mismo proceso que usan los bancos para construir su scorecard de admisión.

**Paso 1 — Binning:** las variables continuas se agrupan en clases (`score_inicial` en A-E, `edad` en rangos de 10 años); las categóricas (`segmento`, `tipo` de préstamo) se usan tal cual.

**Paso 2 — WOE (Weight of Evidence) por bin:**

```
WOE_bin = ln( %Buenos_en_el_bin / %Malos_en_el_bin )
```

donde "Bueno" = préstamo que no cayó en default, "Malo" = préstamo en default. 🟦 **Real:** esta transformación es el estándar de la industria para preparar variables antes de una regresión logística de scoring, porque: (1) convierte cualquier variable (numérica o categórica) a una misma escala numérica interpretable, y (2) un WOE positivo significa "este bin es más seguro que el promedio de la cartera", uno negativo "más riesgoso" — se puede leer directamente.

**Paso 3 — IV (Information Value) por variable:** mide cuánto poder predictivo aporta *toda* la variable (no un bin puntual):

```
IV = Σ_bins (%Buenos_bin - %Malos_bin) × WOE_bin
```

Con la regla de interpretación estándar de la industria:

| IV | Interpretación |
|---|---|
| < 0.02 | No predictiva |
| 0.02 – 0.10 | Predictiva débil |
| 0.10 – 0.30 | Predictiva media |
| 0.30 – 0.50 | Predictiva fuerte |
| > 0.50 | Sospechosamente fuerte — revisar fuga de información |

**Resultado de esta corrida:**

| Variable | IV | Lectura |
|---|---|---|
| Score inicial | 0.895 | "Sospechosa" según la regla — **y acá es donde hay que ser honesto**: en este dataset, el score *es* literalmente la variable que se usó para generar la probabilidad de default (ver sección 3.9). Un IV así de alto en un banco real dispararía una revisión por fuga de datos (el modelo "ve" el resultado antes de tiempo); acá es esperable porque el mecanismo causal es así por diseño. En una entrevista, esto es una excelente oportunidad para demostrar que entendés qué es fuga de datos y por qué hay que sospechar de un IV extremo. |
| Segmento (RETAIL/PYME/CORPORATIVO) | 0.107 | Predictiva media — consistente con que el segmento influye en el score inicial pero no lo determina. |
| Edad | 0.005 | No predictiva — por diseño, la edad no tuvo ningún rol en la generación del riesgo del cliente. |
| Tipo de préstamo | 0.003 | No predictiva individualmente (su efecto en la pérdida está en el LGD, no en la PD). |

**Paso 4 — Regresión logística sobre las variables en escala WOE:** se entrena `LogisticRegression` prediciendo "es buen pagador" a partir de las 4 variables ya transformadas a WOE. El coeficiente (`beta`) de cada variable indica cuánto pesa esa variable en el modelo final.

**Paso 5 — Escalado a puntos:**

```
Score = Offset + Factor × ln(Odds_bueno)
donde  ln(Odds_bueno) = Intercepto + Σ Beta_i × WOE_i

Factor = PDO / ln(2)
Offset = Score_base - Factor × ln(Odds_base)
```

- **PDO** (*Points to Double the Odds*): cuántos puntos hacen falta para duplicar la relación de momios buenos:malos.
- Se usó `Score_base = 600`, `Odds_base = 50` (es decir, "a 600 puntos, 50 clientes buenos por cada malo") y `PDO = 20`. 🟨 **Estos tres números son el ejemplo canónico del libro de Siddiqi** — cualquier entidad puede elegir su propia escala base, pero estos valores son los que se usan universalmente como ejemplo de referencia en la literatura de scorecards, por eso se adoptaron acá.
- Los puntos de cada bin se calculan repartiendo el offset entre las 4 variables y sumando el aporte propio de cada WOE — así el score final de un cliente es simplemente la **suma de los puntos de cada uno de sus atributos** (el formato clásico de una tarjeta de scoring: "score inicial: +196 pts, edad: +132 pts, segmento: +133 pts, tipo de préstamo: +131 pts → total 592 pts").

**Paso 6 — Validación del modelo (AUC / Gini):**

```
AUC = Área bajo la curva ROC
Gini = 2 × AUC - 1
```

🟦 **Real:** el AUC y el Gini son las métricas estándar de la industria para validar un scorecard — miden qué tan bien el score ordena a los clientes de mejor a peor riesgo (no si predice el valor exacto, sino si *ordena* correctamente). Interpretación de referencia: AUC 0.5 = azar puro, > 0.7 aceptable para un scorecard real, > 0.8 muy bueno, > 0.9 sospechoso (posible fuga).

**Resultado de esta corrida:** AUC = 0.738 (Gini = 0.477) — un scorecard con capacidad de discriminación aceptable según el estándar de la industria. Score promedio de clientes buenos: 543 pts vs. 518 pts en clientes malos — el scorecard sí separa a ambos grupos, aunque la diferencia no es enorme porque, además del score inicial (la variable dominante), se mezclaron variables con poco poder predictivo real (edad, tipo de préstamo) a propósito, para poder mostrar cómo se lee un IV bajo.

### 4.7 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Qué es el Expected Loss y cómo se calcula?" | "PD × LGD × EAD — la probabilidad de que el cliente no pague, multiplicada por el porcentaje que se pierde si no paga, multiplicada por el monto expuesto. Es el marco central del enfoque IRB de Basilea II." |
| "¿Por qué el LGD varía según el tipo de préstamo?" | "Por la garantía: un hipotecario tiene el inmueble como colateral, así que el banco recupera la mayor parte del monto ejecutando la garantía — LGD bajo. Un préstamo personal no tiene garantía, así que si el cliente no paga, se pierde casi todo — LGD alto." |
| "¿Qué es un roll rate?" | "Mide qué porcentaje de clientes migra de un segmento de riesgo (o bucket de mora) a otro entre dos períodos. Lo modelé como una matriz de transición de Markov sobre el historial trimestral de segmento de riesgo del cliente." |
| "¿Qué es WOE y para qué sirve?" | "Weight of Evidence: transforma cualquier variable (numérica o categórica) en un solo número que mide qué tan 'buena' o 'mala' es cada categoría comparada contra el promedio de la cartera. Es el paso previo estándar antes de entrenar la regresión logística de un scorecard." |
| "¿Qué es el Information Value y qué significa un IV muy alto?" | "Mide el poder predictivo total de una variable. Un IV > 0.5 generalmente es sospechoso — puede indicar que la variable tiene fuga de información (ej: conoce el resultado antes de tiempo). En mi caso, el score tiene un IV de 0.89 porque literalmente generé el dataset sintético usando el score para definir la probabilidad de default, así que es un IV alto *esperado*, no un error — y sé explicar la diferencia entre ambos casos." |
| "¿Cómo validaste el scorecard?" | "Con AUC y Gini — miden qué tan bien el score ordena a los clientes por riesgo. Obtuve un AUC de 0.74, dentro del rango aceptable para un scorecard real (0.7-0.8)." |

---

## 5. Glosario acumulado

| Término | Definición |
|---|---|
| **PK (Primary Key)** | Campo que identifica de forma única cada fila de una tabla (ej: `cliente_id`) |
| **Integridad referencial** | Regla que garantiza que una clave foránea (ej: `cliente_id` en `prestamos`) siempre apunte a una fila que realmente existe en la tabla referenciada (`clientes`) |
| **NPL (Non-Performing Loan)** | Préstamo con mora mayor a 90 días — el umbral estándar internacional (Basel) para considerarlo "en incumplimiento" |
| **Distribución Normal** | Distribución de probabilidad simétrica en forma de campana, definida por su media (μ) y desvío estándar (σ) |
| **Distribución Log-Normal** | Distribución con cola larga a la derecha, siempre positiva — la elección estándar para modelar montos de dinero |
| **Random walk (paseo aleatorio)** | Serie donde cada valor es el anterior más una variación aleatoria — forma simple de simular evolución en el tiempo sin una tendencia forzada |
| **ETL** | Extract, Transform, Load — el proceso de tomar datos de origen, transformarlos/limpiarlos, y dejarlos listos para análisis |
| **Data governance (gobierno de datos)** | El conjunto de procesos que garantizan que los datos usados por una organización sean confiables, consistentes y bien documentados |
| **Vista 360 del cliente** | Tabla que agrega, en un solo registro, toda la información relevante de un cliente proveniente de distintas fuentes |
| **PD (Probability of Default)** | Probabilidad de que un cliente/préstamo incumpla en un horizonte determinado |
| **LGD (Loss Given Default)** | % del monto expuesto que se pierde si el cliente incumple, tras intentar recuperar vía garantías/cobranza |
| **EAD (Exposure at Default)** | Monto que está expuesto al momento del default |
| **Expected Loss (EL)** | PD × LGD × EAD — la pérdida promedio esperada de un préstamo o cartera |
| **IRB (Internal Ratings-Based)** | Enfoque de Basilea II donde el propio banco calibra sus modelos internos de PD/LGD/EAD (en vez de usar ponderadores fijos del regulador) |
| **Vintage Analysis** | Comparación del comportamiento de mora de préstamos según la cohorte (período) en que fueron otorgados |
| **Roll Rate** | % de clientes/préstamos que migran de un segmento de riesgo o bucket de mora a otro entre dos períodos |
| **Matriz de transición (Markov)** | Tabla que muestra, para cada estado de origen, la probabilidad de terminar en cada estado de destino en el período siguiente |
| **WOE (Weight of Evidence)** | `ln(%Buenos / %Malos)` de un bin — transforma cualquier variable a una escala que indica qué tan segura o riesgosa es cada categoría |
| **IV (Information Value)** | Suma ponderada de los WOE de todos los bins de una variable — mide el poder predictivo total de esa variable |
| **Scorecard** | Tabla de puntos por variable/bin que, sumados, dan el score final de un cliente |
| **PDO (Points to Double the Odds)** | Cuántos puntos de score hacen falta para duplicar la relación de momios buenos:malos — parámetro de escalado de un scorecard |
| **AUC (Area Under the ROC Curve)** | Métrica de 0 a 1 que mide qué tan bien un modelo ordena a los casos de mejor a peor riesgo (0.5 = azar, 1 = perfecto) |
| **Gini** | `2×AUC - 1` — otra forma de expresar el poder discriminante de un modelo, común en scorecards |
| **Fuga de datos (data leakage)** | Cuando una variable usada para entrenar un modelo contiene información que en la práctica no estaría disponible al momento de la predicción (o que ya "conoce" el resultado) — infla artificialmente el poder predictivo aparente |

---

## 6. Cómo revisar vos mismo cada módulo

Checklist genérico para cualquier módulo nuevo que agreguemos:

1. Leé el `README.md` de la carpeta del módulo — explica qué hace y cómo correrlo.
2. Corré los scripts en el orden indicado (normalmente: generar/leer datos → analizar → exportar resultado).
3. Mirá los `print()` de consola — cada script imprime sus resultados clave para que puedas verificarlos sin abrir el CSV.
4. Volvé a esta bitácora y comparalo con la sección del módulo — cada fórmula debería tener su explicación acá.
5. Preguntate: *"¿podría explicar esto en una entrevista sin mirar el código?"* Si la respuesta es no, releé la sección de "conceptos a estudiar" del instructivo original.

---

## 7. Fuentes y referencias

- **Escala de credit score 300–850:** convención de la industria, popularizada por FICO (Fair Isaac Corporation), ampliamente adaptada por scorecards de bancos y fintechs a nivel global, incluida Latinoamérica.
- **Umbral de 90 días para NPL:** convención del Acuerdo de Basilea (Basel II/III) y ampliamente usada por reguladores bancarios, incluido el marco de clasificación de deudores de BCRA (que categoriza situación crediticia según días de atraso).
- **PD / LGD / EAD / Expected Loss:** metodología del enfoque IRB (Internal Ratings-Based) de Basilea II. Libro de referencia: *"Credit Risk Management: Basic Concepts"* — Van Gestel & Baesens.
- **Scorecard (WOE / IV / regresión logística / escalado a puntos / PDO):** metodología estándar descripta en Naeem Siddiqi, *"Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring"* — incluye el ejemplo canónico de escalado (600 pts = odds 50:1, PDO=20) adoptado en el Módulo 02.
- **AUC / Gini como métricas de validación de scorecards:** práctica estándar de la industria de riesgo crediticio y de machine learning para modelos de clasificación binaria.
- **Distribución Log-Normal para montos financieros:** práctica estándar en econometría financiera para variables monetarias no negativas con asimetría positiva.
- **Función logística para modelar PD en función del score:** misma familia matemática que usa un modelo de regresión logística real — estándar en modelos de credit scoring.
- **GAFI / UIF (se detalla en Módulo 04):** Grupo de Acción Financiera Internacional (FATF) — tipologías públicas de lavado de dinero; Unidad de Información Financiera de Argentina (organismo regulador AML local).
- Todo lo demás (parámetros exactos de las distribuciones, pesos de las categorías) es una **aproximación razonada por mí** para producir un dataset sintético realista, no una cifra tomada de una fuente oficial — se marca como 🟨 en cada sección para que quede explícito.

---

## 8. Registro de cambios

| Fecha | Módulo | Cambio |
|---|---|---|
| 2026-09-05 | 01 — Data Infrastructure | Documento creado. Módulo 01 completado: schema, generación de datos, data quality checks, ETL. Mejora sobre el instructivo original: se agregó generación de `cuentas` y `scoring_historico` (estaban en el schema pero no en el script original), y se corrigió la asignación de `cuenta_id` en transacciones para que referencie una cuenta real del cliente. |
| 2026-09-05 | 01 — Data Infrastructure | **Fix post-Módulo 02:** se reemplazó la asignación de estado de mora por umbrales discretos (2-3 baldes) por una función logística continua de PD en función del score. Causa: la PD calculada en el Módulo 02 no era monótona respecto al score (ver sección 3.9). Dataset regenerado; los resultados del Módulo 01 en este documento reflejan la corrida posterior al fix. |
| 2026-09-05 | 02 — Credit Risk Analytics | Módulo completado: `pd_lgd_ead.py`, `vintage_analysis.py`, `roll_rate_matrix.py`, `credit_scorecard.py` (WOE/IV + regresión logística + escalado a puntos + validación AUC/Gini) y 3 archivos SQL. Todos corridos y validados contra la base real. |

