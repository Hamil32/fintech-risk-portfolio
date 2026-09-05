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
4. [Glosario acumulado](#4-glosario-acumulado)
5. [Cómo revisar vos mismo cada módulo](#5-cómo-revisar-vos-mismo-cada-módulo)
6. [Fuentes y referencias](#6-fuentes-y-referencias)
7. [Registro de cambios](#7-registro-de-cambios)

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
  VIGENTE:    1.124 (56.2%)
  MORA_30:      285 (14.2%)
  CANCELADO:    249 (12.4%)
  MORA_60:      203 (10.2%)
  MORA_90:       76 (3.8%)
  INCOBRABLE:    63 (3.1%)
Scoring histórico:   20.000  (4 trimestres × 5.000 clientes)

Data quality checks: 20/20 OK
```

### 3.8 Lo que te pueden preguntar sobre este módulo

| Pregunta | Cómo responder |
|---|---|
| "¿Estos son datos reales?" | "No, es un dataset sintético que generé yo mismo con Python (Faker + numpy) para poder construir y demostrar toda la metodología de riesgo/fraude/AML sin depender de acceso a datos bancarios reales, que por regulación no están disponibles públicamente." |
| "¿Por qué SQLite y no una base más 'seria'?" | "Porque para el volumen del dataset (decenas de miles de filas) es suficiente y portable — el diseño del schema y las queries SQL son idénticas a las que escribiría contra Oracle o SQL Server en un banco real." |
| "¿Cómo garantizás la calidad de los datos?" | "Con un script de data quality checks que corre 20 validaciones: integridad referencial, unicidad de claves, rangos de negocio y consistencia entre campos relacionados (ej: días de mora vs. estado del préstamo)." |
| "¿Por qué el score va de 300 a 850?" | "Es la escala convencional de credit scoring, popularizada por FICO, que uso como referencia estándar de la industria — no es la escala oficial de BCRA (que no publica una única escala nacional), pero es ampliamente reconocida." |

---

## 4. Glosario acumulado

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

---

## 5. Cómo revisar vos mismo cada módulo

Checklist genérico para cualquier módulo nuevo que agreguemos:

1. Leé el `README.md` de la carpeta del módulo — explica qué hace y cómo correrlo.
2. Corré los scripts en el orden indicado (normalmente: generar/leer datos → analizar → exportar resultado).
3. Mirá los `print()` de consola — cada script imprime sus resultados clave para que puedas verificarlos sin abrir el CSV.
4. Volvé a esta bitácora y comparalo con la sección del módulo — cada fórmula debería tener su explicación acá.
5. Preguntate: *"¿podría explicar esto en una entrevista sin mirar el código?"* Si la respuesta es no, releé la sección de "conceptos a estudiar" del instructivo original.

---

## 6. Fuentes y referencias

- **Escala de credit score 300–850:** convención de la industria, popularizada por FICO (Fair Isaac Corporation), ampliamente adaptada por scorecards de bancos y fintechs a nivel global, incluida Latinoamérica.
- **Umbral de 90 días para NPL:** convención del Acuerdo de Basilea (Basel II/III) y ampliamente usada por reguladores bancarios, incluido el marco de clasificación de deudores de BCRA (que categoriza situación crediticia según días de atraso).
- **PD / LGD / EAD / Expected Loss (se detalla en Módulo 02):** metodología del enfoque IRB (Internal Ratings-Based) de Basilea II. Libro de referencia: *"Credit Risk Management: Basic Concepts"* — Van Gestel & Baesens.
- **Distribución Log-Normal para montos financieros:** práctica estándar en econometría financiera para variables monetarias no negativas con asimetría positiva.
- **GAFI / UIF (se detalla en Módulo 04):** Grupo de Acción Financiera Internacional (FATF) — tipologías públicas de lavado de dinero; Unidad de Información Financiera de Argentina (organismo regulador AML local).
- Todo lo demás (parámetros exactos de las distribuciones, pesos de las categorías) es una **aproximación razonada por mí** para producir un dataset sintético realista, no una cifra tomada de una fuente oficial — se marca como 🟨 en cada sección para que quede explícito.

---

## 7. Registro de cambios

| Fecha | Módulo | Cambio |
|---|---|---|
| 2026-09-05 | 01 — Data Infrastructure | Documento creado. Módulo 01 completado: schema, generación de datos, data quality checks, ETL. Mejora sobre el instructivo original: se agregó generación de `cuentas` y `scoring_historico` (estaban en el schema pero no en el script original), y se corrigió la asignación de `cuenta_id` en transacciones para que referencie una cuenta real del cliente. |

