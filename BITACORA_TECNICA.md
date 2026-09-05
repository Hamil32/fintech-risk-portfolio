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
5. [Módulo 03 — Fraud Detection](#5-módulo-03--fraud-detection)
6. [Módulo 04 — AML / Compliance](#6-módulo-04--aml--compliance)
7. [Módulo 05 — Decision Engine](#7-módulo-05--decision-engine)
8. [Módulo 06 — Executive Dashboard](#8-módulo-06--executive-dashboard)
9. [Glosario acumulado](#9-glosario-acumulado)
10. [Cómo revisar vos mismo cada módulo](#10-cómo-revisar-vos-mismo-cada-módulo)
11. [Fuentes y referencias](#11-fuentes-y-referencias)
12. [Registro de cambios](#12-registro-de-cambios)

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
| **Semilla aleatoria re-fijada al inicio de cada sección** (`reseed()` en `generate_synthetic_data.py`) | Cada sección (clientes, cuentas, transacciones, préstamos, scoring) resetea `random`/`numpy` a un offset propio de la semilla base, en vez de dejar correr una única secuencia continua. Así, si el día de mañana se edita la lógica de UNA sección, las demás no cambian sus resultados por efecto colateral — encontramos este problema en la práctica (ver [sección 5.6](#56-hallazgo-el-modelo-de-fraude-daba-100-de-precisión-y-eso-era-una-mala-señal)) y lo corregimos para que no vuelva a pasar. |

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
| **transacciones** | Cada movimiento de dinero | `es_fraude` es el "ground truth" (la etiqueta real) que en Módulo 03 se va a usar para *evaluar* qué tan bueno es el motor de detección — en la vida real esta etiqueta la generan las disputas/chargebacks confirmados, acá la simulamos nosotros. `cuenta_destino_id`/`cliente_destino_id` (solo en TRANSFERENCIA) se agregaron más adelante, para el Módulo 04 — ver sección 6.2. |
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
Cuentas:             7.691
Transacciones:       50.000  (1.000 marcadas como fraude, 2.0%)
Préstamos:           2.000
  VIGENTE:      885 (44.2%)
  CANCELADO:    357 (17.8%)
  MORA_90:      263 (13.2%)
  MORA_30:      212 (10.6%)
  MORA_60:      169 (8.5%)
  INCOBRABLE:   114 (5.7%)
Scoring histórico:   20.000  (4 trimestres × 5.000 clientes)

Data quality checks: 20/20 OK
```

> Nota: estos números cambiaron dos veces desde la primera corrida documentada, por dos correcciones distintas hechas mientras se construían los módulos siguientes: (1) el fix de `asignar_estado_mora()` — ver [sección 3.9](#39-hallazgo-la-pd-no-salía-monótona-y-cómo-se-corrigió) — y (2) el fix de solapamiento de fraude y el desacople de semillas por sección — ver [sección 5.6](#56-hallazgo-el-modelo-de-fraude-daba-100-de-precisión-y-eso-era-una-mala-señal) en el Módulo 03. Estos son los valores vigentes después de ambos fixes.

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
Cartera total (EAD):        $7.353.674.329
NPL (mora > 90 días):       $468.799.457   (6.38% de la cartera)
Expected Loss total:        $409.675.120   (5.57% de la cartera)

PD histórica por segmento:      Expected Loss como % de esa cartera:
  E (muy alto riesgo):  46.4%     15.92%
  D (alto riesgo):      38.4%     11.21%
  C (riesgo medio):     23.4%      6.87%
  B (riesgo bajo):       9.4%      2.71%
  A (muy bajo riesgo):   4.0%      1.19%

Expected Loss por tipo de préstamo (% de esa cartera):
  PERSONAL:     14.17%  (LGD alto, sin garantía)
  PRENDARIO:     9.81%
  HIPOTECARIO:   4.70%  (LGD bajo, con garantía real)
```

Todo monótono y consistente con la teoría: a peor segmento, mayor % de Expected Loss sobre su propia cartera; y el tipo de préstamo sin garantía concentra proporcionalmente más pérdida esperada aunque tenga menor PD asignada individual, porque su LGD es mucho más alto.

### 4.4 `vintage_analysis.py` — Vintage Analysis

Agrupa los préstamos por **trimestre de originación** (`fecha_otorgamiento`) y calcula, para cada cohorte, qué porcentaje terminó en mora o en NPL:

```
tasa_mora_cohorte = (# préstamos en mora de esa cohorte) / (# préstamos totales de esa cohorte)
```

🟦 **Real:** esta es la pregunta que cualquier área de riesgo de admisión se hace constantemente: *"¿la política de originación de los últimos trimestres está produciendo peores créditos que antes?"*. Si la tasa de mora sube de forma sostenida en las cohortes más recientes, es una señal de alerta temprana (antes incluso de que esos préstamos lleguen a mora avanzada, porque se los compara "a la misma edad" contra cohortes anteriores — en un análisis más completo se compararía a igual cantidad de meses desde el otorgamiento, no a fecha de corte fija; acá se simplifica comparando el estado actual de cada cohorte).

**Resultado de esta corrida:** tasa de mora promedio de las cohortes más antiguas 36.7% vs. 37.7% en las más recientes. La diferencia es de ~1 punto porcentual — **dentro del ruido muestral esperable** para una cartera de 2.000 préstamos repartidos en 13 cohortes trimestrales (algunas con menos de 120 casos). El script compara solo dos promedios sin ningún test de significancia estadística, así que la lectura honesta acá es *"no hay evidencia de deterioro real de la originación reciente"*, no *"la cartera está empeorando"* — en un caso real, esta comparación se haría con un test de proporciones (ej. test Z de dos proporciones) antes de sacar una conclusión de negocio.

### 4.5 `roll_rate_matrix.py` — Roll Rate Matrix

Mide qué porcentaje de clientes en un segmento de riesgo (A-E) migra a otro segmento entre un trimestre y el siguiente. Se construye una **matriz de transición de Markov de primer orden**: para cada par de trimestres consecutivos, se cruza el segmento "desde" contra el segmento "hacia", y se calcula el porcentaje de fila:

```
%(desde=X, hacia=Y) = (# clientes que estaban en X y pasaron a Y) / (# clientes totales que estaban en X)
```

⚠️ **Adaptación metodológica importante:** el roll rate clásico de la industria se calcula sobre **buckets de mora de un préstamo puntual** (0 días → 30 → 60 → 90) mes a mes. Este dataset no tiene un historial mensual de mora por préstamo — tiene un historial **trimestral del segmento de riesgo del cliente** (`scoring_historico`). Se aplicó el mismo concepto matemático (matriz de transición de Markov) sobre esa serie disponible. La lógica de negocio es análoga (cuantifica flujo hacia mejor/peor riesgo), pero es importante poder explicar esta diferencia si te preguntan por el detalle — no es el roll rate "de manual" pero sí una aplicación correcta y honesta del mismo concepto sobre los datos que el dataset realmente tiene.

**Resultado de esta corrida** (matriz promedio entre los 4 trimestres del dataset):

```
hacia →   A      B      C      D      E
desde A  91.2%   8.8%   0.0%   0.0%   0.0%
desde B   4.3%  88.6%   7.1%   0.0%   0.0%
desde C   0.0%   6.3%  88.6%   5.1%   0.0%
desde D   0.0%   0.0%   8.1%  88.3%   3.5%
desde E   0.0%   0.0%   0.0%  11.9%  88.1%
```

- 89.0% de los clientes se mantiene en el mismo segmento de riesgo de un trimestre a otro.
- 6.1% mejora de segmento ("roll-back").
- 4.9% empeora de segmento ("roll-forward").
- Ningún cliente salta más de un segmento en un trimestre (ej: nadie pasa de A a C directamente) — comportamiento esperable de un score que cambia gradualmente (recordá que `scoring_historico` se generó como un random walk de a un paso, ver sección 3.4 — la matriz de transición está, en parte, confirmando el propio mecanismo con el que se generaron los datos).

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
| Score inicial | 0.687 | "Sospechosa" según la regla — **y acá es donde hay que ser honesto**: en este dataset, el score *es* literalmente la variable que se usó para generar la probabilidad de default (ver sección 3.9). Un IV así de alto en un banco real dispararía una revisión por fuga de datos (el modelo "ve" el resultado antes de tiempo); acá es esperable porque el mecanismo causal es así por diseño. En una entrevista, esto es una excelente oportunidad para demostrar que entendés qué es fuga de datos y por qué hay que sospechar de un IV extremo. |
| Segmento (RETAIL/PYME/CORPORATIVO) | 0.130 | Predictiva media — consistente con que el segmento influye en el score inicial pero no lo determina. |
| Edad | 0.039 | Predictiva débil — la edad no tuvo ningún rol causal en la generación del riesgo del cliente (ver Módulo 01), así que este valor bajo es puramente ruido de muestreo, no una señal real. |
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

**Resultado de esta corrida:** AUC = 0.729 (Gini = 0.458) — un scorecard con capacidad de discriminación aceptable según el estándar de la industria. Score promedio de clientes buenos: 541 pts vs. 519 pts en clientes malos — el scorecard sí separa a ambos grupos, aunque la diferencia no es enorme porque, además del score inicial (la variable dominante), se mezclaron variables con poco poder predictivo real (edad, tipo de préstamo) a propósito, para poder mostrar cómo se lee un IV bajo.

### 4.7 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Qué es el Expected Loss y cómo se calcula?" | "PD × LGD × EAD — la probabilidad de que el cliente no pague, multiplicada por el porcentaje que se pierde si no paga, multiplicada por el monto expuesto. Es el marco central del enfoque IRB de Basilea II." |
| "¿Por qué el LGD varía según el tipo de préstamo?" | "Por la garantía: un hipotecario tiene el inmueble como colateral, así que el banco recupera la mayor parte del monto ejecutando la garantía — LGD bajo. Un préstamo personal no tiene garantía, así que si el cliente no paga, se pierde casi todo — LGD alto." |
| "¿Qué es un roll rate?" | "Mide qué porcentaje de clientes migra de un segmento de riesgo (o bucket de mora) a otro entre dos períodos. Lo modelé como una matriz de transición de Markov sobre el historial trimestral de segmento de riesgo del cliente." |
| "¿Qué es WOE y para qué sirve?" | "Weight of Evidence: transforma cualquier variable (numérica o categórica) en un solo número que mide qué tan 'buena' o 'mala' es cada categoría comparada contra el promedio de la cartera. Es el paso previo estándar antes de entrenar la regresión logística de un scorecard." |
| "¿Qué es el Information Value y qué significa un IV muy alto?" | "Mide el poder predictivo total de una variable. Un IV > 0.5 generalmente es sospechoso — puede indicar que la variable tiene fuga de información (ej: conoce el resultado antes de tiempo). En mi caso, el score tiene un IV de 0.69 porque literalmente generé el dataset sintético usando el score para definir la probabilidad de default, así que es un IV alto *esperado*, no un error — y sé explicar la diferencia entre ambos casos." |
| "¿Cómo validaste el scorecard?" | "Con AUC y Gini — miden qué tan bien el score ordena a los clientes por riesgo. Obtuve un AUC de 0.73, dentro del rango aceptable para un scorecard real (0.7-0.8)." |

---

## 5. Módulo 03 — Fraud Detection

### 5.1 Qué problema de negocio resuelve

Un banco no puede revisar manualmente el 100% de sus transacciones — con 50.000 transacciones al año en este dataset (multiplicado por miles en un banco real), hace falta un sistema que **filtre automáticamente** cuáles merecen la atención de un analista humano. Este módulo construye ese sistema en capas, tal como existe en la industria: reglas (rápidas, explicables), un modelo no supervisado (detecta lo nuevo, sin etiqueta) y un modelo supervisado (el más preciso, si hay etiqueta), combinados en un sistema de alertas priorizado.

### 5.2 Qué se construyó

| Archivo | Rol |
|---|---|
| [`03_fraud_detection/rule_engine.py`](03_fraud_detection/rule_engine.py) | Capa 1: motor de reglas |
| [`03_fraud_detection/anomaly_detection.py`](03_fraud_detection/anomaly_detection.py) | Capa 2: Isolation Forest (no supervisado) |
| [`03_fraud_detection/fraud_model.py`](03_fraud_detection/fraud_model.py) | Capa 3: modelo supervisado (Regresión Logística + Random Forest) |
| [`03_fraud_detection/alert_system.py`](03_fraud_detection/alert_system.py) | Orquestación: combina las 3 señales en una cola de alertas priorizada |
| [`03_fraud_detection/sql/`](03_fraud_detection/sql/) | Las mismas reglas y patrones en SQL puro |

### 5.3 `rule_engine.py` — Motor de reglas

Cuatro reglas, cada una con su propia lógica:

| Regla | Fórmula / condición | Por qué es una señal de fraude |
|---|---|---|
| **Velocity** | Más de 5 transacciones del mismo cliente en 1 hora | Un atacante que toma control de una cuenta suele hacer varias operaciones seguidas, rápido, antes de que el banco reaccione |
| **Monto atípico** | `z = (monto - media_cliente) / (desvío_cliente + 1) > 3` | Un monto muy alejado del comportamiento histórico del propio cliente es sospechoso — el "+1" en el denominador evita dividir por cero en clientes con desvío ≈0 |
| **Horario sospechoso** | Hora entre 1am y 5am | Menor actividad legítima en ese rango, y es cuando suele operar el fraude automatizado |
| **Canal digital + monto alto** | Canal ∈ {APP, Home Banking} y monto > $20.000 | Los canales digitales son el vector más común de toma de cuenta (no requieren la tarjeta física) |

🟦 **Real:** las cuatro son señales genuinas que usan sistemas antifraude reales — no inventadas para este proyecto. `score_reglas` (cuántas reglas se dispararon) y el umbral operativo (`≥ 2` reglas → revisión) son la forma estándar de combinar reglas simples en un sistema de puntaje compuesto.

📝 **Nota de implementación — velocity check eficiente:** el instructivo original proponía calcular esto con `.expanding().apply()` (evalúa la ventana completa desde el inicio para cada fila, con complejidad O(n²) — con 50.000 filas esto es visiblemente lento e innecesario). Se reemplazó por un *rolling window basado en tiempo* (`.rolling('1h', on='fecha')`), que le pide a pandas contar directamente cuántas filas cayeron en la última hora — mismo resultado, muchísimo más eficiente y es la forma idiomática de resolver esto en pandas.

⚠️ **Limitación reconocida (z-score con data leakage):** el promedio y desvío de cada cliente se calculan sobre *todas* sus transacciones (pasadas y futuras respecto a la transacción evaluada). En producción esto debe calcularse solo con historial *anterior*. Se mantiene así por simplicidad, pero es importante poder señalar la diferencia.

**Resultado de esta corrida:**

```
Flags generados (score_reglas >= 2): 714 de 50.000 (1.43%)
  flag_velocity:              72   (0.14%)
  flag_monto_atipico:        516   (1.03%)
  flag_horario_sospechoso: 2.315   (4.63%)
  flag_digital_monto_alto: 3.362   (6.72%)

Precision: 0.507  (de cada 100 alertas, 50.7 son fraude real)
Recall:    0.362  (detecta el 36.2% de los fraudes reales)
F1-Score:  0.422
```

> Nota: estos números (y los de `anomaly_detection.py`/`fraud_model.py`/`alert_system.py` más abajo) se recalcularon después de extender el Módulo 01 para el Módulo 04 — algunas transacciones legítimas se reasignaron a patrones AML (montos grandes de round-tripping, ráfagas de cash-intensive), lo que mueve levemente algunos falsos positivos de las reglas de fraude. El cambio es menor (±1-2 puntos porcentuales) y no afecta ninguna conclusión.

### 5.4 `anomaly_detection.py` — Isolation Forest

A diferencia de las reglas, este modelo **no usa la etiqueta `es_fraude` para entrenar** — aprende qué combinación de variables (monto, hora, canal, z-score) es "normal" y aísla lo que se desvía. Isolation Forest funciona construyendo muchos árboles de decisión aleatorios: una observación anómala, al ser distinta del resto, se puede aislar con **menos particiones** (queda sola en una rama del árbol mucho más rápido que una observación típica) — el "score de anomalía" es, en esencia, el promedio de cuántas particiones hicieron falta para aislar cada punto en todos los árboles.

🟦 **Real:** es un algoritmo genuino de la librería scikit-learn, ampliamente usado en detección de fraude/anomalías en la industria por su eficiencia (no necesita calcular distancias entre todos los pares de puntos, como otros métodos).

🟨 **Ilustrativo:** el parámetro `contamination=0.02` (la proporción esperada de anomalías) se fijó igual a la tasa de fraude conocida del dataset sintético. En un caso real, **no se conoce la tasa real de fraude de antemano** — este parámetro se calibra según cuántas alertas puede procesar el equipo por día, no contra una "respuesta correcta".

**Resultado de esta corrida:**

```
Isolation Forest  -> Precision: 0.085  Recall: 0.085  F1: 0.085
Z-score simple     -> Precision: 0.047  Recall: 0.047  F1: 0.047
```

Un resultado **modesto y honesto**: sin la etiqueta, el modelo tiene mucho más trabajo para encontrar el patrón de fraude que las reglas (F1=0.42) o el modelo supervisado (ver 5.5). Esto **no es una falla del código** — es la realidad de la detección de anomalías: funciona mejor para encontrar patrones *nuevos* que nadie etiquetó todavía, no para igualar la precisión de un modelo que sí conoce la respuesta. Vale la pena decir esto exactamente así en una entrevista: demuestra que entendés el trade-off real entre ambos enfoques, en vez de mostrar solo el número más lindo.

### 5.5 `fraud_model.py` — Modelo supervisado

Se entrenan y comparan dos modelos sobre un **split estratificado** 75/25 (`stratify=y`, para que la proporción de fraude sea igual en train y test pese a ser una clase minoritaria del 2%):

- **Regresión Logística** (`class_weight='balanced'`): rápida, interpretable — se puede leer el coeficiente de cada variable directamente.
- **Random Forest** (`class_weight='balanced'`): no lineal, generalmente más preciso.

🟦 **`class_weight='balanced'`:** con una clase tan minoritaria (2% fraude), un modelo sin este ajuste tiende a "ignorar" la clase rara para maximizar accuracy general (con solo predecir "nunca es fraude" ya se acierta el 98%). Este parámetro penaliza más los errores sobre la clase minoritaria durante el entrenamiento — técnica estándar para datasets desbalanceados.

🟦 **AUC-PR (Average Precision) por sobre AUC-ROC:** con clases muy desbalanceadas, el AUC-ROC puede verse artificialmente alto (hay muchísimos negativos "fáciles" que cualquier modelo descarta bien). El AUC-PR es más informativo porque se enfoca en qué tan bien el modelo distingue los positivos raros — es la métrica recomendada por la literatura de machine learning para este escenario.

**Resultado de esta corrida:**

| Modelo | AUC-ROC | AUC-PR | Precision (fraude) | Recall (fraude) |
|---|---|---|---|---|
| Regresión Logística | 0.941 | 0.450 | 19.2% | 83.6% |
| **Random Forest** | **0.957** | **0.568** | 27.2% | 85.6% |

La variable más importante en ambos modelos es la hora (`hora` + `es_horario_sospechoso` juntas explican ~60% de la importancia en Random Forest) — consistente con que el patrón de fraude inyectado en el Módulo 01 depende fuertemente del horario.

### 5.6 Hallazgo: el modelo de fraude daba 100% de precisión, y eso era una mala señal

Al entrenar por primera vez el modelo supervisado, el resultado fue:

```
FRAUDE   precision=1.000  recall=1.000  f1-score=1.000
AUC-ROC: 1.000   AUC-PR: 1.000
```

**Un clasificador perfecto en un problema de fraude real NO existe.** Esto es una señal de alarma exactamente igual a la del IV sospechoso del scorecard (sección 4.6) — hay que desconfiar de un resultado "demasiado bueno" en vez de festejarlo sin revisar.

**Causa raíz:** en el Módulo 01, las transacciones fraudulentas se generaban con rangos **completamente disjuntos** de las legítimas: fraude solo en horario 1am-5am (legítimas nunca en ese rango), fraude solo por canal APP/Home Banking (legítimas podían ser cualquier canal, pero el solapamiento con fraude en monto+horario ya alcanzaba). Con la hora sola alcanzaba para separar el 100% de los casos — el modelo no estaba "aprendiendo" fraude, estaba memorizando una frontera perfecta que existía por construcción del dataset, no por parecido a la realidad.

**La corrección**, en `generate_synthetic_data.py`:

- El fraude ahora tiene **80% de probabilidad** de ser "vaciado de cuenta" (monto alto) y **20%** de ser *"card testing"* (montos chicos, $50-$2.000 — un patrón real: probar que una tarjeta/cuenta robada funciona antes de un cargo grande).
- **75%** ocurre de madrugada, **25%** en cualquier horario — el fraude también pasa de día.
- **85%** por canal digital, **15%** por canal físico (POS/ATM — tarjeta clonada, retiro forzado).
- Del lado legítimo, se agregó que un **4% de las transacciones normales** también ocurra de madrugada (gente que opera de noche) — así el horario nocturno deja de ser, por sí solo, una señal perfecta.
- Se inyectó además un patrón de **ráfaga real** (ver `TAMANIO_RAFAGA` en el código): 1 de cada 4 grupos de 5 transacciones fraudulentas se reasigna a un mismo cliente en una ventana de pocos minutos, simulando una toma de cuenta real — sin esto, la regla de `velocity` (5.3) nunca tenía nada que detectar.

**Resultado después del fix:** Random Forest AUC-PR = 0.568 (en vez de 1.000) — un resultado realista, con un trade-off claro entre precision y recall visible en la curva Precision-Recall, exactamente como pasaría con datos reales.

**Efecto colateral encontrado y corregido:** al modificar la sección de transacciones, los resultados de préstamos y scoring (secciones posteriores del mismo script) cambiaron *sin que nadie tocara esa lógica* — porque todas las secciones compartían una única secuencia de números aleatorios. Se corrigió agregando `reseed()` al inicio de cada sección (ver sección 2), para que cada una sea independiente. Este es el motivo por el que los números del Módulo 01 y 02 en este documento se actualizaron una vez más (ver el registro de cambios).

**Cómo contarlo en una entrevista:** *"Cuando mi modelo de fraude dio 100% de precisión y recall, no lo tomé como un éxito — un resultado perfecto en un problema de fraude real es prácticamente siempre una señal de fuga de datos o de un dataset poco realista. Investigué, encontré que mi generador de datos sintéticos creaba una frontera perfectamente separable entre fraude y no-fraude, y lo corregí agregando solapamiento realista entre ambas clases. Después de eso, obtuve un modelo con un AUC-PR de 0.65, mucho más creíble."* Este tipo de escepticismo ante resultados "demasiado buenos" es exactamente lo que se espera de un analista senior.

### 5.7 `alert_system.py` — Orquestación y sistema de alertas

Combina las tres señales (reglas, Isolation Forest, modelo supervisado) en niveles de prioridad, replicando cómo un equipo de fraude organiza su cola de trabajo:

- **CRÍTICA:** el modelo supervisado da probabilidad ≥ 70% → revisar de inmediato.
- **ALTA:** al menos 2 de las 3 señales coinciden → alta confianza cruzada.
- **MEDIA:** exactamente 1 señal se disparó → vale la pena mirar, no urgente.
- **SIN ALERTA:** ninguna señal.

🟦 **`cross_val_predict` para puntuar el 100% de la población:** el modelo de `fraud_model.py` solo predice sobre su 25% de test (para poder medir su performance de forma honesta). Para darle un score a **todas** las transacciones sin el sesgo optimista de "ya las vio en entrenamiento", se usa `cross_val_predict` con 5 folds: cada transacción es puntuada por un modelo que nunca la vio durante su entrenamiento (el mismo principio del train/test split, aplicado a toda la población). Esta es la forma correcta y estándar de generar un score de producción para el 100% de un dataset histórico.

**Resultado de esta corrida — tabla de cobertura acumulada** (equivalente a una *gains table*, técnica estándar para evaluar sistemas de scoring/alertas):

| Prioridad revisada (acumulado) | % del volumen total | % del fraude capturado |
|---|---|---|
| CRÍTICA | 3.6% | 81.7% |
| CRÍTICA + ALTA | 4.0% | 81.9% |
| CRÍTICA + ALTA + MEDIA | 12.1% | 92.4% |
| Todo | 100% | 100% |

**Lectura de negocio:** revisando solo el 4.0% del volumen de transacciones (las de prioridad CRÍTICA + ALTA), el equipo de fraude capturaría el 81.9% del fraude total — esto es exactamente el tipo de argumento con el que un analista de riesgo/fraude justifica el dimensionamiento de su equipo frente a la gerencia: no hace falta revisar todo, hace falta revisar bien lo priorizado.

### 5.8 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Por qué combinar reglas, anomalías y un modelo supervisado en vez de usar solo el mejor?" | "Porque cada uno cubre un punto ciego distinto: las reglas no necesitan etiqueta y son 100% explicables (útil para justificar un rechazo), Isolation Forest detecta patrones nuevos que ningún modelo supervisado vio antes, y el modelo supervisado es el más preciso pero solo aprende lo que ya está etiquetado. En producción se combinan, no se reemplazan entre sí." |
| "¿Por qué no confiar en un modelo con 100% de precisión?" | "Porque en un problema real de fraude eso casi nunca pasa — es señal de fuga de datos o de que el dataset de entrenamiento no representa bien la superposición real entre fraude y comportamiento legítimo. Me pasó exactamente eso construyendo este proyecto, lo investigué y corregí el dataset sintético para que tuviera solapamiento realista." |
| "¿Por qué usaste AUC-PR en vez de solo accuracy?" | "Porque con una clase tan minoritaria (2% fraude), un modelo que nunca predice fraude ya tiene 98% de accuracy sin ser útil. AUC-PR (y precision/recall) reflejan mejor qué tan bien se identifica específicamente la clase rara que importa." |
| "¿Cómo armarías la cola de trabajo de un analista de fraude con recursos limitados?" | "Priorizando por score combinado de varias señales, no revisando todo por igual. En mi caso, con el 4% del volumen de mayor prioridad se captura el 82% del fraude total — es el argumento para dimensionar el equipo según ese trade-off." |

---

## 6. Módulo 04 — AML / Compliance

### 6.1 Qué problema de negocio resuelve

Un banco está obligado por ley a monitorear su cartera en busca de señales de lavado de activos, y a reportar lo sospechoso a la UIF (en Argentina) mediante un ROS. Este módulo construye ese monitoreo: detecta 4 tipologías reconocidas por GAFI, califica el riesgo AML de cada cliente (un proceso llamado KYC — *Know Your Customer*), y genera el borrador del documento que un analista de Compliance presentaría.

### 6.2 Extensión al modelo de datos: por qué hizo falta tocar el Módulo 01 otra vez

Antes de escribir una sola línea de detección, hubo que resolver un problema de datos: **round-tripping y layering son patrones de flujo de fondos entre cuentas** — por definición, involucran más de una parte. La tabla `transacciones` del Módulo 01 no tenía ningún campo para saber **a quién** iba una transferencia, solo de quién salía. Sin esa información, es matemáticamente imposible reconstruir una cadena A→B→C→A.

**Solución:** se agregaron dos columnas nuevas a `transacciones` — `cuenta_destino_id` y `cliente_destino_id` — pobladas únicamente para transacciones de tipo `TRANSFERENCIA` (NULL en el resto, que no tienen una "contraparte" identificable en este modelo). El 25% de las transferencias van a otra cuenta del mismo cliente (movimiento legítimo entre productos propios); el resto, a un cliente elegido al azar. Ver el detalle completo (y por qué directamente se decidió esto, en vez de dejarlo como limitación) en `aml_typologies.md`.

🟦 **Real:** este es exactamente el tipo de campo que cualquier core bancario real tiene modelado desde el día uno (una transferencia SIEMPRE tiene cuenta origen y cuenta destino) — la limitación original era una simplificación del dataset sintético, no una limitación real de cómo se estructuran los datos bancarios.

**Patrones inyectados deliberadamente** (mismo criterio que en el Módulo 03: sin inyectarlos, la probabilidad de que aparezcan por azar con ~10 transacciones/cliente/año es prácticamente nula):

| Patrón | Cómo se construyó |
|---|---|
| **Structuring** | 15 casos: un cliente con 6 transacciones de $7.000-$9.800 el mismo día |
| **Round-tripping** | 12 anillos de 3 clientes (A→B→C→A) en una ventana de días, con el monto reduciéndose 3-10% en cada salto ("comisión" del circuito) |
| **Cash-intensive** | 10 casos: un cliente con 9 extracciones de $60.000-$120.000 en una ventana de 30 días |
| **Actividad inusual** | No se inyectó — emerge naturalmente del z-score sobre datos generados sin intervención (5 casos encontrados) |

### 6.3 `aml_rule_engine.py` — Las 4 tipologías

**Structuring:** igual lógica que en el instructivo original — agrupar transacciones por cliente y día, quedarse con los grupos de ≥5 transacciones bajo el umbral ($10.000 🟨 ilustrativo) cuya suma sí lo supere.

**Round-tripping — la parte técnicamente más interesante del módulo:** se arma con **2 self-joins encadenados** sobre la tabla de transferencias:

```
e1: A -> B (transacción 1)
e2: B -> C (transacción 2, con B = destino de e1, fecha >= fecha de e1)
e3: C -> A (transacción 3, cierra el círculo: destino de e2 = origen de e1)
```

Con la restricción de que las 3 transacciones caigan dentro de una ventana de 10 días. 🟦 **Real:** esto es, en esencia, una **detección de ciclos en un grafo dirigido** (cada cliente es un nodo, cada transferencia una arista) restringida a ciclos de longitud 3 — el mismo principio que usan herramientas de análisis de grafos AML más sofisticadas (que en la industria se implementan con motores de grafos dedicados como Neo4j, no con self-joins de SQL/pandas, pero la lógica conceptual es la misma). Con solo 3 nodos por ciclo y una ventana de tiempo acotada, resolverlo con self-joins es perfectamente viable y mucho más simple de mantener.

**Actividad inusual:** mismo z-score mensual por cliente que ya se usó en el Módulo 03 (z-score de volumen sobre el propio historial) — el mismo concepto estadístico reaparece porque, en el fondo, "esto es raro para este cliente" es la pregunta central de casi todo el análisis de riesgo/fraude/AML.

**Cash-intensive:** 🟨 **adaptación reconocida:** el schema no modela depósitos en efectivo como un tipo de transacción separado, así que se usa `EXTRACCION` (retiro) de alta frecuencia (≥8 en 30 días) y monto (>$500.000) como proxy — ver `aml_typologies.md` para la aclaración completa de esta limitación.

**Resultado de esta corrida:** los 4 detectores encuentran **exactamente** los casos inyectados (15/15 structuring, 12/12 round-tripping, 10/10 cash-intensive) más 5 casos de actividad inusual que emergieron sin inyección — la mejor prueba posible de que la lógica de detección es correcta: recupera al 100% lo que se sabe que está ahí.

```
Total alertas: 42
  STRUCTURING:        15
  ROUND_TRIPPING:     12
  CASH_INTENSIVE:     10
  ACTIVIDAD_INUSUAL:   5

Por nivel de riesgo: ALTO=27, MEDIO=15
Por segmento: RETAIL=36, PYME=4, CORPORATIVO=2
```

### 6.4 `kyc_validator.py` — Completitud KYC y calificación de riesgo

Dos partes:

1. **Completitud de datos** ("KYC de formulario"): formato de DNI, edad en rango legal, provincia válida, score en rango. En este dataset sintético dio 100% completo (5.000/5.000) porque se generó sin errores deliberados — 🟨 en un dataset real, este chequeo casi nunca da 100%, y es habitual encontrar entre 2-5% de fichas con algún dato faltante o inconsistente.

2. **Señal "huella chica, volumen alto":** un cliente PYME/CORPORATIVO con **una sola cuenta** pero un volumen transaccional muy por encima del promedio de su propio segmento (z-score > 2, comparado *dentro* del segmento, no contra toda la cartera — comparar una PYME contra RETAIL no tendría sentido, las escalas de monto son completamente distintas). 🟦 **Real:** esta es una señal genuina de AML — las empresas de fachada suelen tener una estructura societaria/operativa mínima pero mover mucho dinero, precisamente porque su función es "lavar", no operar un negocio real.

**Calificación final** (regla simple, combinando alertas + señal de huella chica + segmento):

```
BAJO:   3.955 clientes
MEDIO:  1.014 clientes
ALTO:      31 clientes
```

### 6.5 `sar_report_generator.py` — Borradores de ROS

Toma los 27 casos de riesgo ALTO y genera un documento markdown con la estructura narrativa estándar de un ROS: identificación del sujeto, tipología GAFI aplicable, descripción de la operación, fundamento de la sospecha y recomendación. 🟦 **Real:** esta es la estructura conceptual que sigue cualquier ROS — identificación, hechos, tipología, fundamento, recomendación — aunque el formulario formal de la UIF tiene sus propios campos específicos que este borrador no reemplaza (el script lo dice explícitamente en su docstring: es un acelerador del trabajo del analista, no un reemplazo del circuito de aprobación interno).

### 6.6 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Cómo detectarías round-tripping?" | "Es un problema de detección de ciclos en un grafo de transferencias: modelo cada cliente como nodo y cada transferencia como arista dirigida, y busco ciclos cortos (A→B→C→A) dentro de una ventana de tiempo acotada. Lo implementé con self-joins encadenados en pandas/SQL, aunque en una escala más grande se resolvería con un motor de grafos dedicado." |
| "¿Qué es el ROS y cuándo se presenta?" | "Reporte de Operación Sospechosa — el documento que un sujeto obligado presenta a la UIF cuando detecta una operación que no puede justificar con el perfil conocido del cliente. Automaticé la generación del borrador narrativo a partir de las alertas detectadas, aunque la decisión final de presentarlo es de Compliance, no del sistema." |
| "¿Qué es KYC?" | "Know Your Customer — el proceso de verificar la identidad y el perfil de riesgo de un cliente antes y durante la relación comercial. Implementé validaciones de completitud de datos y una calificación de riesgo AML combinando señales como alertas asociadas y desproporción entre huella operativa (cantidad de cuentas) y volumen transaccional." |
| "¿Por qué tuviste que modificar el generador de datos del Módulo 01 para este módulo?" | "Porque round-tripping requiere saber la contraparte de cada transferencia, y mi modelo de datos original no la registraba — es una limitación real que encontré al intentar implementar la detección, así que extendí el schema con `cuenta_destino_id`/`cliente_destino_id` antes de seguir." |

---

## 7. Módulo 05 — Decision Engine

### 7.1 Qué problema de negocio resuelve

Hasta acá, todo el portfolio analizaba cartera **existente** (riesgo, fraude, AML sobre datos ya generados). Este módulo cierra el círculo: construye el sistema que **origina** un préstamo nuevo — la API que un canal digital (app, sucursal, comercio aliado) llamaría en el momento en que un cliente pide un crédito, para decidir en segundos si se aprueba, se rechaza, o pasa a revisión humana.

### 7.2 Qué se construyó

| Archivo | Rol |
|---|---|
| [`05_decision_engine/decision_rules.json`](05_decision_engine/decision_rules.json) | Reglas y parámetros de pricing externalizados |
| [`05_decision_engine/scoring_engine.py`](05_decision_engine/scoring_engine.py) | Toda la lógica de negocio (sin FastAPI) |
| [`05_decision_engine/api.py`](05_decision_engine/api.py) | Capa FastAPI sobre `scoring_engine.py` |
| [`05_decision_engine/test_api.py`](05_decision_engine/test_api.py) | 11 tests con `TestClient` |

### 7.3 Decisión de diseño: consultar el riesgo, no pedirlo

El instructivo original pedía que el propio solicitante incluyera su `score` y sus `dias_mora_actual` en el request HTTP. Esto tiene un problema serio: **le estaría pidiendo al cliente que autoevalúe su propio riesgo**, algo que ningún banco real haría (equivale a dejar que alguien complete su propia planilla de aprobación). Se rediseñó para que el motor reciba solo `cliente_id` + lo que el banco genuinamente no puede saber de antemano (monto, plazo, ingreso declarado), y **consulte** el resto directamente en la base del Módulo 01 (`obtener_perfil_cliente()`):

- `score`: de la tabla `clientes`
- `dias_mora_actual`: el máximo `dias_mora` entre los préstamos NO cancelados del cliente
- `defaults_historicos`: cuántos préstamos de ese cliente llegaron alguna vez a `MORA_90`/`INCOBRABLE` (mismo criterio de "default" del Módulo 02)

🟦 **Real:** en un banco real, el motor de decisión consulta el buró de crédito interno/externo — jamás confía en un dato de riesgo autoreportado por el solicitante.

### 7.4 Pricing basado en riesgo — reutilizando todo el portfolio anterior

```
tasa_anual = tasa_libre_riesgo + (PD × LGD) + margen_operativo
```

Esta es la pieza más importante del módulo, porque **no inventa nada nuevo**: reutiliza exactamente la curva de PD del Módulo 01 (`calcular_pd_score`, la misma función logística) y el LGD por tipo de préstamo del Módulo 02, ambos cargados desde `decision_rules.json`. La prima de riesgo (`PD × LGD`) es, literalmente, la **Expected Loss** ya calculada en el Módulo 02 — solo que ahí se usaba para medir la pérdida de una cartera existente, y acá se usa para **poner precio a un préstamo que todavía no existe**. Es el mismo concepto financiero, aplicado en los dos extremos del ciclo de vida de un crédito: originación (acá) y monitoreo (Módulo 02).

🟦 **Real:** este es el principio de *risk-based pricing* — a mayor riesgo esperado, mayor tasa — que usa cualquier scoring de admisión real.

🟨 **Ilustrativo:** `tasa_libre_riesgo=40%` y `margen_operativo=5%` son valores de orden de magnitud razonables para el contexto argentino (tasas nominales altas), no una tasa de mercado vigente a una fecha específica — se actualizaría contra una tasa de referencia real (BADLAR, tasa de política monetaria) en un sistema en producción.

⚠️ **Simplificación reconocida:** un pricing de Basilea "completo" también cubre un cargo de capital por la pérdida NO esperada (*Unexpected Loss*) — acá se omite, solo se cubre la pérdida esperada.

### 7.5 Cuota — sistema francés

```
cuota = monto × [ i × (1+i)^n ] / [ (1+i)^n − 1 ]
```

con `i` = tasa mensual (`tasa_anual / 12`) y `n` = cantidad de cuotas. 🟦 **Real:** es la fórmula estándar de amortización de cuota fija (sistema francés), la que efectivamente usa la inmensa mayoría de préstamos personales/hipotecarios. `scoring_engine.py` también implementa la fórmula **inversa** (`monto_maximo_por_capacidad_pago`): dado el máximo que un cliente puede pagar de cuota, ¿cuál es el monto máximo que se le puede otorgar? — se despeja `monto` de la misma ecuación.

### 7.6 Reglas de rechazo, aprobación y DTI

- **Rechazo automático** (primera regla que se cumple, rechaza): score < 400, mora activa > 90 días, o más de 1 default histórico.
- **DTI (Debt-to-Income):** si la cuota calculada supera el 40% del ingreso declarado, se recalcula el monto máximo viable; si ese monto cubre al menos el 50% de lo pedido, se aprueba ajustado — si no, se deriva a **revisión manual** (el sistema no rechaza de plano los casos límite, los escala a un humano).
- **Aprobación automática:** segmento A (score ≥700) sin mora activa, si además pasa el DTI.

Todas las reglas son literales de `decision_rules.json`, no están hardcodeadas en el código — se pueden ajustar sin tocar `scoring_engine.py`.

### 7.7 Resultados de esta corrida

11/11 tests pasan. Casos verificados manualmente contra la API real:

| Caso | Cliente (score) | Resultado |
|---|---|---|
| Buen cliente, capacidad holgada | 791, sin mora | `APROBADO` — tasa 45.97%, cuota/ingreso 17.6% |
| Mora activa >90 días | 548, NPL | `RECHAZADO` — "mora activa mayor a 90 días" |
| Score bajo | 376 | `RECHAZADO` — "score por debajo del segmento D" |
| Ingreso insuficiente para el monto pedido | 791, ingreso bajo | `APROBADO` con monto ajustado ($800k pedidos → $568k aprobados) |
| Relación cuota/ingreso extrema (211%) | 791, ingreso muy bajo | `REVISION_MANUAL` |
| Cliente inexistente | — | HTTP 404 |
| Tipo de préstamo inválido | — | HTTP 422 (validación de Pydantic) |

### 7.8 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Por qué el cliente no manda su propio score en el request?" | "Porque dejar que el solicitante autoreporte su propio riesgo es un hueco de seguridad — el motor consulta el score y la mora directamente en la base interna a partir del cliente_id, como haría un banco real contra su buró de crédito." |
| "¿Cómo se calcula la tasa de interés?" | "Con pricing basado en riesgo: tasa base + PD×LGD + margen. La parte de PD×LGD es literalmente la Expected Loss que calculé en el Módulo 02, reutilizada acá para poner precio a un crédito nuevo en vez de medir la pérdida de uno existente." |
| "¿Qué pasa si el cliente no puede pagar la cuota completa?" | "El sistema recalcula el monto máximo que sí puede pagar con la fórmula inversa de amortización francesa. Si ese monto cubre al menos la mitad de lo pedido, se aprueba ajustado; si no, se deriva a revisión manual en vez de rechazar de plano." |
| "¿Cómo testeaste la API?" | "Con pytest y el TestClient de FastAPI, sin necesidad de levantar un servidor real. Los clientes de prueba se buscan dinámicamente en la base según la condición que necesito (score alto, mora NPL, etc.), no están hardcodeados — así los tests siguen siendo válidos si el dataset se regenera." |

---

## 8. Módulo 06 — Executive Dashboard

### 8.1 Qué problema de negocio resuelve

Ningún director de riesgo abre 4 carpetas de Python para ver cómo está la cartera — quiere **una pantalla**. Este módulo cierra el portfolio consolidando lo que generaron los Módulos 01-04 en un dashboard de Power BI de 4 páginas.

### 8.2 Por qué esta es la única parte que no se generó 100% por código

Un archivo `.pbix` es un formato binario propietario de Microsoft — no existe forma de "escribirlo" con un script de la misma manera que se genera un CSV o un `.py`. Lo que sí se puede automatizar (y se hizo) es **todo lo previo**: dejar los datos ya consolidados y curados en un esquema listo para importar, y documentar exactamente qué medida DAX y qué visual va en cada página, para que armar el `.pbix` a mano sea un ejercicio de seguir instrucciones, no de empezar de cero.

### 8.3 Qué se construyó

| Archivo | Rol |
|---|---|
| [`06_executive_dashboard/build_dashboard_dataset.py`](06_executive_dashboard/build_dashboard_dataset.py) | Consolida las salidas de los Módulos 01-04 en un esquema tipo estrella |
| [`06_executive_dashboard/power_bi_build_guide.md`](06_executive_dashboard/power_bi_build_guide.md) | Guía paso a paso: importar, relacionar, y qué visual va en cada página |
| [`06_executive_dashboard/dax_measures.md`](06_executive_dashboard/dax_measures.md) | Todas las medidas DAX |
| [`06_executive_dashboard/kpis_financieros.md`](06_executive_dashboard/kpis_financieros.md) | Glosario de KPIs con fórmula y valor actual |
| [`06_executive_dashboard/portfolio_presentation.md`](06_executive_dashboard/portfolio_presentation.md) | Resumen ejecutivo de los 5 módulos |

### 8.4 Decisión de diseño: esquema en estrella + medidas DAX, no números precalculados

Se podría haber generado un solo CSV con los KPIs ya calculados en Python (ej. una fila con "NPL: 6.38%, EL: 5.57%, ..."), y que Power BI solo los muestre. **Se descartó esa opción a propósito.** En cambio, `build_dashboard_dataset.py` deja tablas de **hechos y dimensiones** (`fact_prestamos`, `fact_transacciones`, `dim_clientes`, etc.) al nivel de detalle más granular posible, y todas las métricas (NPL, Expected Loss, tasa de fraude) se calculan con **medidas DAX** dentro de Power BI.

🟦 **Por qué esto es lo correcto:** con números precalculados en un CSV, el dashboard queda **estático** — no se puede filtrar por segmento, por fecha, ni cruzar con ningún otro campo, porque el número ya "vino calculado". Con medidas DAX sobre datos de detalle, cualquier segmentador (slicer) que agregues (por provincia, por tipo de préstamo, por rango de fechas) **recalcula automáticamente** cada KPI — es la diferencia entre un reporte y un dashboard de verdad. Este es exactamente el motivo por el que un analista de BI real casi nunca precalcula KPIs en la fuente: pierde toda la interactividad que es la razón de ser de una herramienta como Power BI.

### 8.5 El esquema de datos

```
        dim_clientes (5.000 filas)
               │
    ┌──────────┼──────────────┐
    │          │              │
fact_prestamos │      fact_alertas_aml
 (2.000)       │           (42)
               │
     fact_transacciones (50.000)

dim_vintage (13) y fact_roll_rate (25) — sin relación,
ya vienen agregados por cohorte/segmento, no por cliente.
```

🟦 **Real:** este es un **esquema en estrella** (star schema) — el patrón de modelado estándar para BI/data warehousing: una tabla de dimensión central rodeada de tablas de hechos, en vez de un único CSV ancho con todo mezclado. Facilita enormemente que Power BI optimice las consultas y que las relaciones sean claras.

`fact_roll_rate` se generó con `.melt()` de pandas (formato ancho → largo): la matriz de transición del Módulo 02 viene como una tabla de 5×5 (una columna por segmento de destino), pero el visual **Matrix** de Power BI necesita tres columnas (`desde`, `hacia`, `porcentaje`) para poder pivotear él mismo — es el mismo concepto de "tidy data" que dicta cuándo una tabla está en el formato correcto para análisis.

### 8.6 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Por qué no generaste el .pbix directamente?" | "Porque es un formato binario propietario, no se puede generar por script. Automaticé todo lo anterior: la consolidación de datos y la definición exacta de qué medida y qué visual va en cada página, para que armar el dashboard sea mecánico." |
| "¿Por qué calculás los KPIs con DAX y no en Python?" | "Porque un número precalculado en un CSV congela el dashboard — no se puede filtrar ni cruzar. Con medidas DAX sobre datos de detalle, cualquier segmentador que agregue recalcula el KPI automáticamente. Es la diferencia entre un reporte estático y un dashboard interactivo real." |
| "¿Qué es un esquema en estrella?" | "Un modelo de datos con una tabla de dimensión central (en mi caso, clientes) rodeada de tablas de hechos (préstamos, transacciones, alertas) — el patrón estándar de modelado para BI, porque hace que las relaciones sean claras y las consultas eficientes." |

---

## 9. Glosario acumulado

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
| **Velocity check** | Regla que detecta muchas operaciones del mismo cliente en poco tiempo — señal típica de una cuenta comprometida |
| **Isolation Forest** | Algoritmo de detección de anomalías: aísla cada observación con árboles aleatorios; las anómalas se aíslan con menos particiones que las normales |
| **Clase desbalanceada** | Cuando una de las clases a predecir es mucho más rara que la otra (ej: 2% fraude vs 98% normal) — requiere métricas y técnicas de entrenamiento distintas a un problema balanceado |
| **`class_weight='balanced'`** | Parámetro de scikit-learn que penaliza más los errores sobre la clase minoritaria durante el entrenamiento, para que el modelo no la ignore |
| **Precision** | De todo lo que el modelo marcó como positivo, qué % realmente lo era (`TP / (TP+FP)`) |
| **Recall** | De todo lo que realmente era positivo, qué % el modelo logró detectar (`TP / (TP+FN)`) |
| **AUC-PR (Average Precision)** | Área bajo la curva Precision-Recall — métrica recomendada por sobre AUC-ROC cuando la clase positiva es muy minoritaria |
| **`cross_val_predict`** | Técnica de scikit-learn para obtener una predicción "fuera de muestra" (out-of-fold) para cada fila de un dataset completo, sin el sesgo optimista de haber sido vista en entrenamiento |
| **Gains table (tabla de ganancias)** | Tabla que muestra qué % de los casos positivos totales se captura revisando el X% superior de un ranking de score — usada para dimensionar equipos de revisión/cobranza/fraude |
| **AML (Anti-Money Laundering)** | Prevención de lavado de activos — el conjunto de controles que un banco debe tener para detectar y reportar operaciones sospechosas |
| **Structuring / Smurfing** | Fraccionar una operación grande en varias chicas, cada una bajo el umbral de reporte, para evitar que sea detectada |
| **Round-tripping** | Circuito de transferencias que sale de una cuenta, pasa por terceros, y vuelve al originante — oculta el origen aparente de los fondos |
| **Layering** | Múltiples transferencias entre cuentas para dificultar el rastreo del origen del dinero (concepto relacionado con round-tripping, con cadenas más largas/complejas) |
| **ROS (Reporte de Operación Sospechosa)** | Documento formal que un banco presenta a la UIF cuando detecta una operación que no puede justificar con el perfil conocido del cliente |
| **UIF (Unidad de Información Financiera)** | Organismo regulador argentino que recibe los ROS y coordina la prevención de lavado de activos a nivel nacional |
| **GAFI / FATF** | Grupo de Acción Financiera Internacional — organismo que define los estándares globales AML y publica tipologías de referencia |
| **KYC (Know Your Customer)** | Proceso de verificar la identidad y el perfil de riesgo de un cliente, tanto al inicio de la relación como durante toda su vigencia |
| **Detección de ciclos en un grafo** | Técnica para encontrar cadenas cerradas (A→B→C→A) en una red de relaciones dirigidas — la base algorítmica del round-tripping/layering |
| **Risk-based pricing (pricing basado en riesgo)** | Fijar la tasa/precio de un producto financiero en función del riesgo esperado del cliente — a mayor riesgo, mayor tasa |
| **DTI (Debt-to-Income)** | Relación entre la cuota de un préstamo y el ingreso del solicitante — mide capacidad de pago |
| **Sistema francés (amortización)** | Método de amortización de cuota fija: la cuota no cambia mes a mes, pero varía la proporción entre interés y capital que la componen |
| **Unexpected Loss (pérdida no esperada)** | La variabilidad de la pérdida por sobre la Expected Loss — el motivo por el que los bancos deben mantener capital regulatorio, no solo provisionar la pérdida esperada |
| **API REST** | Interfaz que expone funcionalidad de un sistema a través de peticiones HTTP (GET/POST/etc.), con respuestas típicamente en JSON |
| **Pydantic** | Librería de Python que valida y tipa automáticamente los datos de entrada/salida de una API (usada por FastAPI) |
| **`TestClient`** | Utilidad de FastAPI/Starlette para testear una API llamándola en memoria, sin levantar un servidor HTTP real |
| **Esquema en estrella (star schema)** | Modelo de datos de BI con una tabla de dimensión central rodeada de tablas de hechos — el patrón estándar para modelar datos analíticos |
| **DAX (Data Analysis Expressions)** | El lenguaje de fórmulas de Power BI, usado para definir medidas que se recalculan según el contexto de filtro vigente |
| **Medida vs. columna calculada (Power BI)** | Una medida se recalcula dinámicamente según los filtros activos (segmentadores, página); una columna calculada se evalúa una sola vez, fila por fila, al cargar los datos |
| **Tidy data (dato ordenado)** | Formato de tabla donde cada fila es una observación y cada columna una variable — el formato "largo" que necesitan la mayoría de las herramientas de análisis/BI para pivotear correctamente |

---

## 10. Cómo revisar vos mismo cada módulo

Checklist genérico para cualquier módulo nuevo que agreguemos:

1. Leé el `README.md` de la carpeta del módulo — explica qué hace y cómo correrlo.
2. Corré los scripts en el orden indicado (normalmente: generar/leer datos → analizar → exportar resultado).
3. Mirá los `print()` de consola — cada script imprime sus resultados clave para que puedas verificarlos sin abrir el CSV.
4. Volvé a esta bitácora y comparalo con la sección del módulo — cada fórmula debería tener su explicación acá.
5. Preguntate: *"¿podría explicar esto en una entrevista sin mirar el código?"* Si la respuesta es no, releé la sección de "conceptos a estudiar" del instructivo original.

---

## 11. Fuentes y referencias

- **Escala de credit score 300–850:** convención de la industria, popularizada por FICO (Fair Isaac Corporation), ampliamente adaptada por scorecards de bancos y fintechs a nivel global, incluida Latinoamérica.
- **Umbral de 90 días para NPL:** convención del Acuerdo de Basilea (Basel II/III) y ampliamente usada por reguladores bancarios, incluido el marco de clasificación de deudores de BCRA (que categoriza situación crediticia según días de atraso).
- **PD / LGD / EAD / Expected Loss:** metodología del enfoque IRB (Internal Ratings-Based) de Basilea II. Libro de referencia: *"Credit Risk Management: Basic Concepts"* — Van Gestel & Baesens.
- **Scorecard (WOE / IV / regresión logística / escalado a puntos / PDO):** metodología estándar descripta en Naeem Siddiqi, *"Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring"* — incluye el ejemplo canónico de escalado (600 pts = odds 50:1, PDO=20) adoptado en el Módulo 02.
- **AUC / Gini como métricas de validación de scorecards:** práctica estándar de la industria de riesgo crediticio y de machine learning para modelos de clasificación binaria.
- **Distribución Log-Normal para montos financieros:** práctica estándar en econometría financiera para variables monetarias no negativas con asimetría positiva.
- **Función logística para modelar PD en función del score:** misma familia matemática que usa un modelo de regresión logística real — estándar en modelos de credit scoring.
- **Isolation Forest:** algoritmo publicado por Liu, Ting & Zhou (2008), implementado en scikit-learn (`sklearn.ensemble.IsolationForest`) — ampliamente usado en detección de fraude y anomalías en la industria.
- **Precision / Recall / AUC-ROC / AUC-PR / `class_weight` para clases desbalanceadas:** métricas y técnicas estándar de machine learning para clasificación binaria con clases minoritarias, documentadas en la referencia oficial de scikit-learn.
- **Velocity check, monto atípico, horario sospechoso, canal + monto como señales de fraude:** patrones de detección genuinos usados por sistemas antifraude reales (no inventados para este proyecto).
- **GAFI / UIF:** Grupo de Acción Financiera Internacional (FATF) — tipologías públicas de lavado de dinero, [fatf-gafi.org](https://www.fatf-gafi.org); Unidad de Información Financiera de Argentina (organismo regulador AML local), [argentina.gob.ar/uif](https://www.argentina.gob.ar/uif).
- **Structuring, round-tripping, actividad inusual, cash-intensive:** tipologías de lavado de dinero públicamente documentadas por GAFI y por informes de tipologías de UIF — no inventadas para este proyecto.
- **Detección de ciclos en grafos dirigidos:** fundamento algorítmico estándar de ciencia de la computación (teoría de grafos), aplicado acá a un caso de uso AML mediante self-joins en vez de una librería de grafos dedicada.
- **Sistema francés de amortización (cuota fija):** método estándar de amortización de préstamos, el más usado en préstamos personales e hipotecarios.
- **Risk-based pricing (tasa = costo de fondeo + PD×LGD + margen):** principio estándar de la industria financiera para poner precio a un crédito nuevo en función de su riesgo esperado.
- **FastAPI / Pydantic / TestClient:** documentación oficial de FastAPI ([fastapi.tiangolo.com](https://fastapi.tiangolo.com)) — framework y prácticas estándar para construir y testear APIs REST en Python.
- **Esquema en estrella / modelado dimensional:** práctica estándar de data warehousing y BI, documentada extensamente en la literatura de Kimball (*The Data Warehouse Toolkit*).
- **DAX y buenas prácticas de medidas vs. columnas calculadas:** documentación oficial de Microsoft Power BI ([learn.microsoft.com/power-bi](https://learn.microsoft.com/power-bi)).
- Todo lo demás (parámetros exactos de las distribuciones, pesos de las categorías) es una **aproximación razonada por mí** para producir un dataset sintético realista, no una cifra tomada de una fuente oficial — se marca como 🟨 en cada sección para que quede explícito.

---

## 12. Registro de cambios

| Fecha | Módulo | Cambio |
|---|---|---|
| 2026-09-05 | 01 — Data Infrastructure | Documento creado. Módulo 01 completado: schema, generación de datos, data quality checks, ETL. Mejora sobre el instructivo original: se agregó generación de `cuentas` y `scoring_historico` (estaban en el schema pero no en el script original), y se corrigió la asignación de `cuenta_id` en transacciones para que referencie una cuenta real del cliente. |
| 2026-09-05 | 01 — Data Infrastructure | **Fix post-Módulo 02:** se reemplazó la asignación de estado de mora por umbrales discretos (2-3 baldes) por una función logística continua de PD en función del score. Causa: la PD calculada en el Módulo 02 no era monótona respecto al score (ver sección 3.9). Dataset regenerado; los resultados del Módulo 01 en este documento reflejan la corrida posterior al fix. |
| 2026-09-05 | 02 — Credit Risk Analytics | Módulo completado: `pd_lgd_ead.py`, `vintage_analysis.py`, `roll_rate_matrix.py`, `credit_scorecard.py` (WOE/IV + regresión logística + escalado a puntos + validación AUC/Gini) y 3 archivos SQL. Todos corridos y validados contra la base real. |
| 2026-09-05 | 03 — Fraud Detection | Módulo completado: `rule_engine.py`, `anomaly_detection.py`, `fraud_model.py`, `alert_system.py` y 3 archivos SQL. |
| 2026-09-05 | 01 — Data Infrastructure | **Fix post-Módulo 03:** se detectó que el modelo supervisado de fraude daba 100% de precisión/recall — señal de dataset poco realista (fronteras perfectamente separables entre fraude y no-fraude). Se corrigió `generate_synthetic_data.py` para que el fraude tenga solapamiento realista con transacciones legítimas (monto, horario, canal) y se inyectó un patrón de ráfaga (velocity) real (ver sección 5.6). Se agregó también `reseed()` por sección para desacoplar la aleatoriedad entre secciones del generador (ver sección 2). Dataset regenerado; los resultados de los Módulos 01 y 02 en este documento reflejan la corrida posterior a este fix. |
| 2026-09-05 | 04 — AML / Compliance | Módulo completado: `aml_rule_engine.py` (structuring, round-tripping vía self-joins, actividad inusual, cash-intensive), `kyc_validator.py`, `sar_report_generator.py`, `aml_typologies.md`, `compliance_report_template.md` y 3 archivos SQL. |
| 2026-09-05 | 01 — Data Infrastructure | **Extensión para Módulo 04:** se agregaron las columnas `cuenta_destino_id`/`cliente_destino_id` a `transacciones` (solo pobladas en TRANSFERENCIA) — sin ellas no se puede detectar round-tripping/layering, que son patrones de flujo de fondos entre partes (ver sección 6.2). Se inyectaron además patrones deliberados de structuring (15 casos), round-tripping (12 anillos) y cash-intensive (10 casos). Dataset regenerado; los números de los Módulos 01-03 en este documento reflejan la corrida posterior a esta extensión (cambios menores, ±1-2 puntos porcentuales en las métricas del Módulo 03). |
| 2026-09-05 | 05 — Decision Engine | Módulo completado: `scoring_engine.py`, `api.py` (FastAPI), `test_api.py` (11 tests), `decision_rules.json`, `business_rules.md`, `api_documentation.md`. Rediseño respecto al instructivo original: el motor consulta el riesgo del cliente en la base (Módulo 01) en vez de aceptarlo autoreportado en el request, y la tasa de interés se calcula con pricing basado en riesgo (PD del Módulo 01 × LGD del Módulo 02) en vez de una tabla de tasas fija. |
| 2026-09-05 | 06 — Executive Dashboard | Módulo completado: `build_dashboard_dataset.py` (consolida los Módulos 01-04 en un esquema en estrella), `power_bi_build_guide.md`, `dax_measures.md`, `kpis_financieros.md`, `portfolio_presentation.md`. El `.pbix` en sí queda pendiente de construcción manual en Power BI Desktop por parte del usuario, siguiendo la guía — es la única entrega del portfolio que no se genera por código. Portfolio de 6 módulos completo. |

