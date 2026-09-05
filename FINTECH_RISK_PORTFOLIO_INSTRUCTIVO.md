# 🏦 FINTECH Risk Portfolio — Instructivo Completo
**Repositorio:** `hamil32 / fintech-risk-portfolio`  
**Objetivo:** Construir un portfolio técnico-financiero que reemplace la falta de experiencia bancaria formal y permita competir por posiciones de Riesgo, Fraude, Compliance y BI en bancos y fintechs argentinas.  
**Salario objetivo:** $3.000.000 – $3.500.000 brutos mensuales  
**Duración estimada:** 15 semanas (trabajo part-time, 5–8 hs/semana)

---

## 📋 Índice

1. [Contexto y estrategia](#1-contexto-y-estrategia)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Configuración inicial del entorno](#3-configuración-inicial-del-entorno)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Módulo 01 — Data Infrastructure](#módulo-01--data-infrastructure)
6. [Módulo 02 — Credit Risk Analytics](#módulo-02--credit-risk-analytics)
7. [Módulo 03 — Fraud Detection](#módulo-03--fraud-detection)
8. [Módulo 04 — AML / Compliance](#módulo-04--aml--compliance)
9. [Módulo 05 — Decision Engine](#módulo-05--decision-engine)
10. [Módulo 06 — Executive Dashboard](#módulo-06--executive-dashboard)
11. [Cronograma semana a semana](#11-cronograma-semana-a-semana)
12. [Cómo presentar el proyecto en entrevistas](#12-cómo-presentar-el-proyecto-en-entrevistas)
13. [Actualización del CV y LinkedIn](#13-actualización-del-cv-y-linkedin)
14. [Recursos y materiales de estudio](#14-recursos-y-materiales-de-estudio)

---

## 1. Contexto y estrategia

### Tu situación actual

| Lo que tenés | Lo que falta |
|---|---|
| SQL, Python, Power BI avanzados | Experiencia laboral en banca |
| ETL, Data Warehouse, automatización | Conocimiento profundo de métricas financieras |
| Desarrollo de aplicaciones reales | Portfolio visible en el sector |
| Carrera de Gestión Bancaria (falta 1 materia) | Proyectos que demuestren aplicación financiera |

### ¿Por qué este portfolio resuelve el problema?

El mercado bancario argentino busca perfiles **híbridos**: gente que entienda finanzas Y sepa trabajar con datos. Ese perfil es escaso. Vos ya tenés la parte técnica. Este proyecto construye la parte financiera de manera **demostrable y pública**.

Cuando llegues a una entrevista, no vas a decir "sé de riesgo crediticio". Vas a decir: **"acá está mi repositorio, construí esto."**

### Posicionamiento objetivo

```
ANTES:  Analista de Datos con conocimientos de banca
DESPUÉS: Data & Risk Analyst | Financial Services
         Python · SQL · Power BI · Process Automation
```

### Roles a los que vas a poder aplicar al terminar

- **Risk Data Analyst** (Santander, BBVA, Itaú)
- **Fraud Data Analyst** (Naranja X, Ualá, MercadoPago)
- **AML / Compliance Analyst** (bancos regulados por BCRA)
- **Credit Risk Analyst** (fintechs de crédito: Prex, Moni, Brubank)
- **Decisioning Analyst** (motores de scoring crediticio)
- **BI Analyst Financial Services** (entrada al sector, para pivotar después)

---

## 2. Stack tecnológico

### Lenguajes y librerías Python

| Librería | Uso en el proyecto |
|---|---|
| `pandas` | Manipulación y transformación de datos |
| `numpy` | Cálculos numéricos y estadísticos |
| `scikit-learn` | Modelos de scoring y detección de anomalías |
| `faker` | Generación de datos sintéticos bancarios |
| `sqlalchemy` | Conexión Python ↔ base de datos |
| `matplotlib` / `seaborn` | Gráficos de análisis exploratorio |
| `plotly` | Gráficos interactivos en notebooks |
| `fastapi` | API REST del motor de decisiones |
| `uvicorn` | Servidor ASGI para FastAPI |
| `jupyter` | Notebooks de análisis documentado |

### Bases de datos

| Motor | Uso |
|---|---|
| `SQLite` | Base local simple para desarrollo (sin instalación extra) |
| `MySQL` | Opcional si ya lo tenés configurado localmente |

### Visualización

| Herramienta | Uso |
|---|---|
| Power BI Desktop | Dashboards de riesgo, fraude y executive view |
| Jupyter Notebooks | Análisis exploratorio con gráficos inline |

### Control de versiones y entorno

| Herramienta | Uso |
|---|---|
| Git | Control de versiones local |
| GitHub | Repositorio público (portfolio visible) |
| VS Code | IDE principal |
| Python Virtual Environment (venv) | Entorno aislado |

---

## 3. Configuración inicial del entorno

### Paso 1: Crear el repositorio en GitHub

1. Entrá a [github.com](https://github.com) con tu cuenta `hamil32`
2. Click en **New repository**
3. Nombre: `fintech-risk-portfolio`
4. Descripción: `Portfolio profesional de análisis de riesgo, fraude, AML y BI para el sector financiero argentino`
5. Visibilidad: **Public** (es fundamental para que lo vean reclutadores)
6. Marcá la opción **Add a README file**
7. Click en **Create repository**

### Paso 2: Clonar localmente en VS Code

Abrí una terminal en VS Code (`Ctrl + `` ` ```) y ejecutá:

```bash
# Elegí una carpeta donde trabajar, por ejemplo:
cd C:\Users\TuUsuario\Proyectos

# Clonar el repositorio
git clone https://github.com/hamil32/fintech-risk-portfolio.git

# Entrar a la carpeta
cd fintech-risk-portfolio

# Abrir en VS Code
code .
```

### Paso 3: Crear el entorno virtual Python

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno (Windows)
venv\Scripts\activate

# Verificar que está activo (deberías ver "(venv)" al inicio del prompt)
```

### Paso 4: Instalar todas las dependencias

```bash
pip install pandas numpy scikit-learn faker sqlalchemy matplotlib seaborn plotly fastapi uvicorn jupyter ipykernel
```

### Paso 5: Crear el archivo requirements.txt

```bash
pip freeze > requirements.txt
```

> **Importante:** Cada vez que instales una librería nueva, repetí `pip freeze > requirements.txt` para mantenerlo actualizado.

### Paso 6: Configurar .gitignore

Creá un archivo `.gitignore` en la raíz del proyecto con este contenido:

```
# Entorno virtual
venv/
env/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Jupyter
.ipynb_checkpoints/

# Datos (no subir datos grandes ni sensibles)
*.csv
*.xlsx
data/raw/

# Variables de entorno
.env

# VS Code
.vscode/

# Power BI (los .pbix son binarios, subir solo si son livianos)
# *.pbix
```

### Paso 7: Primer commit

```bash
git add .
git commit -m "feat: initial project setup with requirements and gitignore"
git push origin main
```

> **Convención de commits a usar en todo el proyecto:**
> - `feat:` — nueva funcionalidad
> - `fix:` — corrección de errores
> - `docs:` — cambios en documentación
> - `data:` — cambios relacionados a datos
> - `analysis:` — análisis exploratorio

---

## 4. Estructura del repositorio

```
fintech-risk-portfolio/
│
├── README.md                          ← Presentación principal del portfolio
├── requirements.txt                   ← Dependencias Python
├── .gitignore
│
├── 01_data_infrastructure/            ← MÓDULO 1: Base de datos y ETL
│   ├── README.md
│   ├── generate_synthetic_data.py     ← Genera clientes, transacciones, préstamos
│   ├── etl_pipeline.py                ← Extracción, transformación y carga
│   ├── data_quality_checks.py         ← Validaciones de calidad
│   ├── schema.sql                     ← Modelo de datos financiero
│   └── data/
│       ├── raw/                       ← Datos sin procesar (ignorado por git)
│       └── processed/                 ← Datos limpios
│
├── 02_credit_risk/                    ← MÓDULO 2: Riesgo crediticio
│   ├── README.md
│   ├── exploratory_analysis.ipynb     ← Análisis exploratorio documentado
│   ├── credit_scorecard.py            ← Scorecard de crédito
│   ├── pd_lgd_ead.py                  ← Cálculo de métricas de riesgo
│   ├── vintage_analysis.py            ← Análisis de cosechas
│   ├── roll_rate_matrix.py            ← Matrices de transición de mora
│   ├── sql/
│   │   ├── credit_portfolio_kpis.sql
│   │   ├── mora_segmentation.sql
│   │   └── vintage_query.sql
│   └── credit_risk_dashboard.pbix     ← Dashboard Power BI
│
├── 03_fraud_detection/                ← MÓDULO 3: Detección de fraude
│   ├── README.md
│   ├── fraud_eda.ipynb                ← Análisis exploratorio de fraude
│   ├── rule_engine.py                 ← Motor de reglas (velocity, importes, geo)
│   ├── anomaly_detection.py           ← Isolation Forest + z-score
│   ├── fraud_model.py                 ← Clasificador supervisado
│   ├── alert_system.py                ← Sistema de alertas automáticas
│   ├── sql/
│   │   ├── fraud_patterns.sql
│   │   ├── velocity_checks.sql
│   │   └── suspicious_transactions.sql
│   └── fraud_dashboard.pbix           ← Dashboard Power BI
│
├── 04_aml_compliance/                 ← MÓDULO 4: AML / KYC
│   ├── README.md
│   ├── aml_typologies.md              ← Tipologías de lavado estudiadas
│   ├── aml_rule_engine.py             ← Detección de patrones AML
│   ├── kyc_validator.py               ← Validador KYC automatizado
│   ├── sar_report_generator.py        ← Generador de reportes ROS
│   ├── sql/
│   │   ├── structuring_detection.sql
│   │   ├── round_tripping.sql
│   │   └── high_risk_customers.sql
│   └── compliance_report_template.md
│
├── 05_decision_engine/                ← MÓDULO 5: Motor de decisión
│   ├── README.md
│   ├── scoring_engine.py              ← Lógica de scoring
│   ├── decision_rules.json            ← Reglas configurables en JSON
│   ├── api.py                         ← API REST con FastAPI
│   ├── test_api.py                    ← Tests de la API
│   └── docs/
│       ├── api_documentation.md
│       └── business_rules.md
│
└── 06_executive_dashboard/            ← MÓDULO 6: Dashboard ejecutivo
    ├── README.md
    ├── executive_dashboard.pbix        ← Dashboard consolidado
    ├── kpis_financieros.md             ← Glosario de KPIs bancarios
    └── portfolio_presentation.md       ← Resumen ejecutivo del portfolio
```

---

## Módulo 01 — Data Infrastructure

**Duración:** Semanas 1–2  
**Objetivo:** Crear la base de datos sintética que alimentará todos los módulos siguientes.

### ¿Qué se construye?

Un dataset simulado de un banco ficticio llamado **"Banco Río Digital"** con:
- 5.000 clientes con perfiles variados
- 50.000 transacciones en 12 meses
- 2.000 solicitudes de préstamos (aprobados, rechazados, en mora)
- Historial crediticio de clientes

### Conceptos financieros a aprender en este módulo

Antes de codear, estudiar brevemente estos conceptos (30–60 min):

- **Tipos de clientes bancarios:** retail, pyme, corporativo
- **Productos:** cuenta corriente, caja de ahorro, tarjeta de crédito, préstamo personal, hipotecario
- **Ciclo de vida de un préstamo:** solicitud → evaluación → aprobación/rechazo → desembolso → repago → cancelación/mora
- **Categorías de transacciones:** débito, crédito, transferencia, pago de servicios, extracción ATM

### Archivos a crear

#### `schema.sql` — Modelo de datos

```sql
-- CLIENTES
CREATE TABLE clientes (
    cliente_id      INTEGER PRIMARY KEY,
    nombre          TEXT,
    dni             TEXT UNIQUE,
    edad            INTEGER,
    provincia       TEXT,
    segmento        TEXT,         -- RETAIL, PYME, CORPORATIVO
    score_inicial   INTEGER,      -- 300–850
    fecha_alta      DATE,
    activo          BOOLEAN DEFAULT 1
);

-- CUENTAS
CREATE TABLE cuentas (
    cuenta_id       INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    tipo_cuenta     TEXT,         -- CC, CA, TARJETA
    moneda          TEXT DEFAULT 'ARS',
    saldo           DECIMAL(15,2),
    fecha_apertura  DATE
);

-- TRANSACCIONES
CREATE TABLE transacciones (
    transaccion_id  INTEGER PRIMARY KEY,
    cuenta_id       INTEGER REFERENCES cuentas(cuenta_id),
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    fecha           DATETIME,
    monto           DECIMAL(15,2),
    tipo            TEXT,         -- DEBITO, CREDITO, TRANSFERENCIA, PAGO, EXTRACCION
    canal           TEXT,         -- HOME_BANKING, APP, ATM, SUCURSAL, POS
    comercio        TEXT,
    ciudad          TEXT,
    es_fraude       BOOLEAN DEFAULT 0,
    flag_revision   BOOLEAN DEFAULT 0
);

-- PRÉSTAMOS
CREATE TABLE prestamos (
    prestamo_id     INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    tipo            TEXT,         -- PERSONAL, HIPOTECARIO, PRENDARIO, TARJETA
    monto_original  DECIMAL(15,2),
    monto_pendiente DECIMAL(15,2),
    tasa_anual      DECIMAL(5,2),
    cuotas_total    INTEGER,
    cuotas_pagadas  INTEGER DEFAULT 0,
    fecha_otorgamiento DATE,
    fecha_vencimiento  DATE,
    estado          TEXT,         -- VIGENTE, CANCELADO, MORA_30, MORA_60, MORA_90, INCOBRABLE
    dias_mora       INTEGER DEFAULT 0
);

-- SCORING HISTÓRICO
CREATE TABLE scoring_historico (
    id              INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    fecha           DATE,
    score           INTEGER,
    pd_estimada     DECIMAL(5,4),  -- Probabilidad de Default
    segmento_riesgo TEXT           -- A, B, C, D, E
);
```

#### `generate_synthetic_data.py` — Generador de datos

```python
"""
Módulo 01 — Generación de datos sintéticos bancarios
Banco Río Digital — Dataset de desarrollo y análisis
"""

import pandas as pd
import numpy as np
from faker import Faker
from faker.providers import bank
import sqlite3
from datetime import datetime, timedelta
import random

# Configuración
fake = Faker('es_AR')
np.random.seed(42)
random.seed(42)
N_CLIENTES = 5000
N_TRANSACCIONES = 50000
FECHA_INICIO = datetime(2023, 1, 1)
FECHA_FIN = datetime(2023, 12, 31)

print("=" * 60)
print("BANCO RÍO DIGITAL — Generador de datos sintéticos")
print("=" * 60)

# ============================================================
# 1. CLIENTES
# ============================================================
print("\n[1/4] Generando clientes...")

provincias = ['CABA', 'Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza',
              'Tucumán', 'Salta', 'Neuquén', 'Río Negro', 'Entre Ríos']
pesos_provincias = [0.35, 0.30, 0.10, 0.08, 0.05, 0.03, 0.02, 0.02, 0.02, 0.03]
segmentos = ['RETAIL', 'PYME', 'CORPORATIVO']
pesos_segmentos = [0.80, 0.15, 0.05]

clientes = []
for i in range(1, N_CLIENTES + 1):
    segmento = np.random.choice(segmentos, p=pesos_segmentos)
    # Clientes corporativos tienen mejores scores en promedio
    if segmento == 'CORPORATIVO':
        score = int(np.clip(np.random.normal(720, 60), 500, 850))
    elif segmento == 'PYME':
        score = int(np.clip(np.random.normal(640, 80), 400, 820))
    else:
        score = int(np.clip(np.random.normal(580, 100), 300, 800))

    clientes.append({
        'cliente_id': i,
        'nombre': fake.name(),
        'dni': fake.numerify('##.###.###'),
        'edad': random.randint(18, 75),
        'provincia': np.random.choice(provincias, p=pesos_provincias),
        'segmento': segmento,
        'score_inicial': score,
        'fecha_alta': fake.date_between(start_date='-5y', end_date='-1y'),
        'activo': 1
    })

df_clientes = pd.DataFrame(clientes)
print(f"   → {len(df_clientes)} clientes generados")
print(f"   → Score promedio: {df_clientes['score_inicial'].mean():.0f}")
print(f"   → Distribución: {df_clientes['segmento'].value_counts().to_dict()}")

# ============================================================
# 2. TRANSACCIONES
# ============================================================
print("\n[2/4] Generando transacciones...")

tipos = ['DEBITO', 'CREDITO', 'TRANSFERENCIA', 'PAGO', 'EXTRACCION']
pesos_tipos = [0.30, 0.20, 0.25, 0.15, 0.10]
canales = ['APP', 'HOME_BANKING', 'POS', 'ATM', 'SUCURSAL']
pesos_canales = [0.35, 0.25, 0.20, 0.12, 0.08]

transacciones = []
# 2% de transacciones fraudulentas
n_fraude = int(N_TRANSACCIONES * 0.02)
ids_fraude = set(random.sample(range(N_TRANSACCIONES), n_fraude))

for i in range(N_TRANSACCIONES):
    cliente_id = random.randint(1, N_CLIENTES)
    es_fraude = i in ids_fraude
    tipo = np.random.choice(tipos, p=pesos_tipos)

    # Las transacciones fraudulentas tienen patrones específicos
    if es_fraude:
        monto = round(random.uniform(5000, 50000), 2)
        canal = np.random.choice(['APP', 'HOME_BANKING'], p=[0.6, 0.4])
        hora = random.randint(1, 5)  # Madrugada
    else:
        monto = round(abs(np.random.lognormal(8, 1.5)), 2)
        canal = np.random.choice(canales, p=pesos_canales)
        hora = random.randint(8, 22)

    fecha_base = FECHA_INICIO + timedelta(days=random.randint(0, 364))
    fecha = fecha_base.replace(hour=hora, minute=random.randint(0, 59))

    transacciones.append({
        'transaccion_id': i + 1,
        'cuenta_id': random.randint(1, N_CLIENTES),
        'cliente_id': cliente_id,
        'fecha': fecha,
        'monto': monto,
        'tipo': tipo,
        'canal': canal,
        'comercio': fake.company() if tipo in ['DEBITO', 'PAGO'] else None,
        'ciudad': fake.city(),
        'es_fraude': int(es_fraude),
        'flag_revision': 0
    })

df_transacciones = pd.DataFrame(transacciones)
print(f"   → {len(df_transacciones)} transacciones generadas")
print(f"   → Transacciones fraudulentas: {df_transacciones['es_fraude'].sum()} ({df_transacciones['es_fraude'].mean()*100:.1f}%)")

# ============================================================
# 3. PRÉSTAMOS
# ============================================================
print("\n[3/4] Generando préstamos...")

# Solo el 40% de clientes tiene préstamos
clientes_con_prestamo = random.sample(range(1, N_CLIENTES + 1), int(N_CLIENTES * 0.40))
tipos_prestamo = ['PERSONAL', 'HIPOTECARIO', 'PRENDARIO']
pesos_prestamo = [0.60, 0.25, 0.15]

# Distribución de estados según score del cliente
def asignar_estado_mora(score):
    if score >= 700:
        estados = ['VIGENTE', 'CANCELADO', 'MORA_30']
        pesos = [0.75, 0.20, 0.05]
    elif score >= 550:
        estados = ['VIGENTE', 'CANCELADO', 'MORA_30', 'MORA_60']
        pesos = [0.60, 0.20, 0.13, 0.07]
    else:
        estados = ['VIGENTE', 'MORA_30', 'MORA_60', 'MORA_90', 'INCOBRABLE']
        pesos = [0.40, 0.20, 0.18, 0.12, 0.10]
    return np.random.choice(estados, p=pesos)

prestamos = []
for idx, cliente_id in enumerate(clientes_con_prestamo):
    score = df_clientes.loc[df_clientes['cliente_id'] == cliente_id, 'score_inicial'].values[0]
    tipo = np.random.choice(tipos_prestamo, p=pesos_prestamo)

    if tipo == 'HIPOTECARIO':
        monto = round(random.uniform(5_000_000, 50_000_000), 2)
        cuotas = random.choice([120, 180, 240])
        tasa = round(random.uniform(0.08, 0.15), 4)
    elif tipo == 'PRENDARIO':
        monto = round(random.uniform(500_000, 5_000_000), 2)
        cuotas = random.choice([24, 36, 48])
        tasa = round(random.uniform(0.12, 0.20), 4)
    else:
        monto = round(random.uniform(50_000, 2_000_000), 2)
        cuotas = random.choice([6, 12, 24, 36])
        tasa = round(random.uniform(0.15, 0.30), 4)

    estado = asignar_estado_mora(score)
    cuotas_pagadas = random.randint(1, cuotas - 1) if estado != 'CANCELADO' else cuotas
    dias_mora_map = {'VIGENTE': 0, 'CANCELADO': 0, 'MORA_30': random.randint(1, 30),
                     'MORA_60': random.randint(31, 60), 'MORA_90': random.randint(61, 90),
                     'INCOBRABLE': random.randint(91, 365)}

    fecha_oto = fake.date_between(start_date='-3y', end_date='-6m')

    prestamos.append({
        'prestamo_id': idx + 1,
        'cliente_id': cliente_id,
        'tipo': tipo,
        'monto_original': monto,
        'monto_pendiente': round(monto * (1 - cuotas_pagadas / cuotas), 2),
        'tasa_anual': tasa,
        'cuotas_total': cuotas,
        'cuotas_pagadas': cuotas_pagadas,
        'fecha_otorgamiento': fecha_oto,
        'fecha_vencimiento': fecha_oto + timedelta(days=cuotas * 30),
        'estado': estado,
        'dias_mora': dias_mora_map[estado]
    })

df_prestamos = pd.DataFrame(prestamos)
print(f"   → {len(df_prestamos)} préstamos generados")
print(f"   → Distribución de estados:")
for estado, count in df_prestamos['estado'].value_counts().items():
    pct = count / len(df_prestamos) * 100
    print(f"      {estado}: {count} ({pct:.1f}%)")

# ============================================================
# 4. GUARDAR EN BASE DE DATOS
# ============================================================
print("\n[4/4] Guardando en base de datos SQLite...")

conn = sqlite3.connect('data/processed/banco_rio_digital.db')

df_clientes.to_sql('clientes', conn, if_exists='replace', index=False)
df_transacciones.to_sql('transacciones', conn, if_exists='replace', index=False)
df_prestamos.to_sql('prestamos', conn, if_exists='replace', index=False)

conn.close()
print("   → Base de datos guardada en: data/processed/banco_rio_digital.db")

# También guardar como CSV para Power BI
df_clientes.to_csv('data/processed/clientes.csv', index=False)
df_transacciones.to_csv('data/processed/transacciones.csv', index=False)
df_prestamos.to_csv('data/processed/prestamos.csv', index=False)
print("   → CSVs exportados para Power BI")

print("\n" + "=" * 60)
print("✅ Generación completada exitosamente")
print("=" * 60)
print(f"\nResumen final:")
print(f"  Clientes:       {len(df_clientes):,}")
print(f"  Transacciones:  {len(df_transacciones):,}")
print(f"  Préstamos:      {len(df_prestamos):,}")
```

### Commit al terminar el módulo

```bash
git add 01_data_infrastructure/
git commit -m "feat: complete data infrastructure module - synthetic banking dataset"
git push origin main
```

---

## Módulo 02 — Credit Risk Analytics

**Duración:** Semanas 3–5  
**Objetivo:** Construir análisis de riesgo crediticio con métricas reales usadas por los bancos.

### Conceptos financieros CLAVE a estudiar primero (2–3 horas)

Antes de codear este módulo, dominar estos conceptos. Serán preguntados en entrevistas.

| Concepto | Definición simple |
|---|---|
| **PD (Probability of Default)** | % de probabilidad de que un cliente no pague |
| **LGD (Loss Given Default)** | % del monto que se pierde si el cliente no paga |
| **EAD (Exposure at Default)** | Monto total expuesto al momento del default |
| **Expected Loss (EL)** | `PD × LGD × EAD` — pérdida esperada por cada préstamo |
| **NPL (Non-Performing Loan)** | Préstamos con mora > 90 días |
| **Vintage Analysis** | Comparar el comportamiento de mora por cohorte de origen |
| **Roll Rate** | % de clientes que "empeoran" de categoría de mora (ej: 0 → 30 días) |
| **Scorecard** | Tabla de puntos por variable que determina el score de un cliente |
| **Mora** | Incumplimiento en el pago de una cuota |

**Recursos para estudiar estos conceptos:**
- Buscar en YouTube: "riesgo crediticio PD LGD EAD explicado"
- Buscar en YouTube: "vintage analysis credit risk"
- BCRA: publicaciones sobre gestión de riesgo crediticio (bcra.gob.ar)

### Archivos a crear

#### `pd_lgd_ead.py` — Métricas de riesgo

```python
"""
Módulo 02 — Cálculo de PD, LGD, EAD y Expected Loss
Basado en metodología Basilea II
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns

# Cargar datos
conn = sqlite3.connect('../01_data_infrastructure/data/processed/banco_rio_digital.db')
prestamos = pd.read_sql('SELECT * FROM prestamos', conn)
clientes = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

df = prestamos.merge(clientes[['cliente_id', 'score_inicial', 'segmento']], on='cliente_id')

# ============================================================
# CÁLCULO DE PD (Probabilidad de Default)
# ============================================================
# Default = clientes en MORA_90 + INCOBRABLE
df['es_default'] = df['estado'].isin(['MORA_90', 'INCOBRABLE']).astype(int)

# PD por segmento de score
bins = [0, 400, 500, 600, 700, 850]
labels = ['E (Muy alto riesgo)', 'D (Alto riesgo)', 'C (Riesgo medio)', 'B (Riesgo bajo)', 'A (Muy bajo riesgo)']
df['segmento_score'] = pd.cut(df['score_inicial'], bins=bins, labels=labels)

pd_por_segmento = df.groupby('segmento_score', observed=True).agg(
    total_prestamos=('es_default', 'count'),
    defaults=('es_default', 'sum'),
    pd_historica=('es_default', 'mean'),
    monto_total=('monto_original', 'sum')
).round(4)

pd_por_segmento['pd_porcentaje'] = (pd_por_segmento['pd_historica'] * 100).round(2)

print("=" * 60)
print("ANÁLISIS DE RIESGO CREDITICIO — Banco Río Digital")
print("=" * 60)
print("\n📊 PROBABILIDAD DE DEFAULT (PD) POR SEGMENTO DE SCORE:")
print(pd_por_segmento[['total_prestamos', 'defaults', 'pd_porcentaje']].to_string())

# ============================================================
# CÁLCULO DE LGD (Loss Given Default)
# ============================================================
# Simplificación: LGD según tipo de garantía
lgd_por_tipo = {
    'HIPOTECARIO': 0.25,   # Garantía real — recupero alto
    'PRENDARIO': 0.45,     # Garantía parcial
    'PERSONAL': 0.75       # Sin garantía — recupero bajo
}
df['lgd'] = df['tipo'].map(lgd_por_tipo)

# ============================================================
# CÁLCULO DE EAD (Exposure at Default)
# ============================================================
df['ead'] = df['monto_pendiente']  # Saldo al momento del análisis

# ============================================================
# EXPECTED LOSS (EL = PD × LGD × EAD)
# ============================================================
# Asignar PD según segmento de score
pd_map = {
    'E (Muy alto riesgo)': 0.25,
    'D (Alto riesgo)': 0.15,
    'C (Riesgo medio)': 0.08,
    'B (Riesgo bajo)': 0.03,
    'A (Muy bajo riesgo)': 0.01
}
df['pd_asignada'] = df['segmento_score'].map(pd_map)
df['expected_loss'] = df['pd_asignada'] * df['lgd'] * df['ead']

# KPIs de cartera
total_cartera = df['monto_pendiente'].sum()
total_el = df['expected_loss'].sum()
npl = df[df['dias_mora'] > 90]['monto_pendiente'].sum()
tasa_npl = npl / total_cartera

print(f"\n💰 KPIs DE CARTERA:")
print(f"   Cartera total:          ${total_cartera:,.0f}")
print(f"   NPL (mora > 90 días):   ${npl:,.0f} ({tasa_npl*100:.2f}%)")
print(f"   Expected Loss total:    ${total_el:,.0f} ({total_el/total_cartera*100:.2f}%)")

# Guardar resultados
df.to_csv('output_credit_risk_analysis.csv', index=False)
print(f"\n✅ Análisis guardado en output_credit_risk_analysis.csv")
```

#### `vintage_analysis.py` — Análisis de cosechas

```python
"""
Vintage Analysis: compara el comportamiento de mora 
de préstamos otorgados en distintos períodos (cohortes)
"""
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect('../01_data_infrastructure/data/processed/banco_rio_digital.db')
df = pd.read_sql('SELECT * FROM prestamos', conn)
conn.close()

# Crear cohorte (trimestre de otorgamiento)
df['fecha_otorgamiento'] = pd.to_datetime(df['fecha_otorgamiento'])
df['cohorte'] = df['fecha_otorgamiento'].dt.to_period('Q')

# Calcular mora por cohorte
df['en_mora'] = df['dias_mora'] > 0

vintage = df.groupby('cohorte').agg(
    total=('prestamo_id', 'count'),
    en_mora=('en_mora', 'sum'),
    monto_total=('monto_original', 'sum'),
    monto_en_mora=('monto_pendiente', lambda x: x[df.loc[x.index, 'en_mora']].sum())
).reset_index()

vintage['tasa_mora'] = vintage['en_mora'] / vintage['total']
vintage['tasa_mora_monto'] = vintage['monto_en_mora'] / vintage['monto_total']

print("\n📊 VINTAGE ANALYSIS — Tasa de mora por cohorte de originación:")
print(vintage[['cohorte', 'total', 'en_mora', 'tasa_mora']].to_string(index=False))

# Visualización
plt.figure(figsize=(12, 5))
plt.bar(vintage['cohorte'].astype(str), vintage['tasa_mora'] * 100, color='steelblue')
plt.xlabel('Cohorte de originación')
plt.ylabel('Tasa de mora (%)')
plt.title('Vintage Analysis — Banco Río Digital\nTasa de mora por trimestre de otorgamiento')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('vintage_analysis.png', dpi=150)
plt.show()
print("✅ Gráfico guardado en vintage_analysis.png")
```

### KPIs que debe mostrar el Dashboard Power BI (Módulo 02)

Cuando conectes Power BI al CSV `output_credit_risk_analysis.csv`, crear visualizaciones para:

| Métrica | Tipo de visualización |
|---|---|
| NPL Rate (% mora > 90 días) | Gauge / KPI card |
| Expected Loss por segmento | Gráfico de barras |
| PD por segmento de score | Gráfico de columnas |
| Distribución de cartera por tipo | Gráfico de torta |
| Vintage analysis | Mapa de calor |
| Evolución de mora mensual | Línea de tiempo |

---

## Módulo 03 — Fraud Detection

**Duración:** Semanas 6–8  
**Objetivo:** Construir un sistema de detección de fraude con reglas y modelos estadísticos.

### Conceptos a estudiar antes de codear (2 horas)

| Concepto | Descripción |
|---|---|
| **Velocity check** | Muchas transacciones en poco tiempo desde el mismo cliente |
| **Geolocation anomaly** | Transacciones en ciudades imposibles para el cliente |
| **Amount anomaly** | Monto muy diferente al comportamiento histórico del cliente |
| **False positive** | Transacción legítima marcada como fraude (costo operativo alto) |
| **Precision / Recall** | Métricas de evaluación de modelos de fraude |
| **Chargeback** | Reversión de una transacción reclamada como fraudulenta |
| **Isolation Forest** | Algoritmo de ML para detectar anomalías sin datos etiquetados |

### `rule_engine.py` — Motor de reglas

```python
"""
Motor de reglas antifraude
Las reglas son el primer nivel de detección: simples, rápidas y configurables
"""
import pandas as pd
import numpy as np
import sqlite3

conn = sqlite3.connect('../01_data_infrastructure/data/processed/banco_rio_digital.db')
df = pd.read_sql('SELECT * FROM transacciones ORDER BY cliente_id, fecha', conn)
conn.close()

df['fecha'] = pd.to_datetime(df['fecha'])
df = df.sort_values(['cliente_id', 'fecha'])

flags = pd.DataFrame({'transaccion_id': df['transaccion_id']})

# ============================================================
# REGLA 1: Velocity — Más de 5 transacciones en 1 hora
# ============================================================
df['count_1h'] = df.groupby('cliente_id')['fecha'].transform(
    lambda x: x.expanding().apply(
        lambda d: ((d.iloc[-1] - d) < pd.Timedelta('1h')).sum()
    )
)
flags['flag_velocity'] = (df['count_1h'] > 5).astype(int)

# ============================================================
# REGLA 2: Monto atípico — Mayor a 3 desviaciones estándar del cliente
# ============================================================
cliente_stats = df.groupby('cliente_id')['monto'].agg(['mean', 'std']).reset_index()
cliente_stats.columns = ['cliente_id', 'monto_medio', 'monto_std']
df = df.merge(cliente_stats, on='cliente_id')
df['z_score'] = (df['monto'] - df['monto_medio']) / (df['monto_std'] + 1)
flags['flag_monto_atipico'] = (df['z_score'] > 3).astype(int)

# ============================================================
# REGLA 3: Horario sospechoso — Madrugada (1am - 5am)
# ============================================================
df['hora'] = df['fecha'].dt.hour
flags['flag_horario_sospechoso'] = df['hora'].between(1, 5).astype(int)

# ============================================================
# REGLA 4: Canal + Monto alto — APP con monto > $20.000
# ============================================================
flags['flag_digital_monto_alto'] = (
    (df['canal'].isin(['APP', 'HOME_BANKING'])) &
    (df['monto'] > 20000)
).astype(int)

# ============================================================
# SCORE COMPUESTO DE REGLAS
# ============================================================
flag_cols = [c for c in flags.columns if c.startswith('flag_')]
flags['score_reglas'] = flags[flag_cols].sum(axis=1)
flags['nivel_riesgo'] = pd.cut(
    flags['score_reglas'],
    bins=[-1, 0, 1, 2, 10],
    labels=['SIN RIESGO', 'RIESGO BAJO', 'RIESGO MEDIO', 'RIESGO ALTO']
)
flags['requiere_revision'] = (flags['score_reglas'] >= 2).astype(int)

# Combinar con datos originales
resultado = df[['transaccion_id', 'cliente_id', 'fecha', 'monto', 'canal', 'es_fraude']].merge(flags, on='transaccion_id')

# Evaluar el motor de reglas
print("=" * 60)
print("MOTOR DE REGLAS ANTIFRAUDE — Evaluación")
print("=" * 60)
print(f"\nTransacciones analizadas: {len(resultado):,}")
print(f"Flags generados: {resultado['requiere_revision'].sum():,} ({resultado['requiere_revision'].mean()*100:.2f}%)")

# Calcular precision y recall contra la realidad (es_fraude)
tp = ((resultado['requiere_revision'] == 1) & (resultado['es_fraude'] == 1)).sum()
fp = ((resultado['requiere_revision'] == 1) & (resultado['es_fraude'] == 0)).sum()
fn = ((resultado['requiere_revision'] == 0) & (resultado['es_fraude'] == 1)).sum()

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"\n📊 Métricas del motor de reglas:")
print(f"   Precision:  {precision:.3f}  (de cada 100 alertas, {precision*100:.1f} son fraude real)")
print(f"   Recall:     {recall:.3f}  (detecta el {recall*100:.1f}% de los fraudes reales)")
print(f"   F1-Score:   {f1:.3f}")

resultado.to_csv('output_fraud_rules.csv', index=False)
print("\n✅ Resultados guardados en output_fraud_rules.csv")
```

---

## Módulo 04 — AML / Compliance

**Duración:** Semanas 9–10  
**Objetivo:** Detectar patrones de lavado de dinero y generar reportes de cumplimiento.

### Conceptos a estudiar (2–3 horas)

| Tipología AML | Descripción |
|---|---|
| **Structuring (Smurfing)** | Dividir grandes montos en pequeñas transacciones para evitar reportes |
| **Round-tripping** | Enviar dinero al exterior y recibirlo de vuelta "lavado" |
| **Layering** | Múltiples transferencias entre cuentas propias para ocultar origen |
| **Cash-intensive** | Depósitos frecuentes de efectivo sin justificación |

**Marco regulatorio argentino a conocer:**
- **UIF:** Unidad de Información Financiera (organismo regulador)
- **ROS:** Reporte de Operación Sospechosa (obligación del banco)
- **GAFI:** Grupo de Acción Financiera Internacional (estándares globales)
- **BCRA Com. A 6212:** Normas de prevención de lavado en entidades financieras

### `aml_rule_engine.py` — Detección de patrones AML

```python
"""
Motor de detección AML
Identifica comportamientos alineados a tipologías de lavado de dinero (UIF/GAFI)
"""
import pandas as pd
import sqlite3

conn = sqlite3.connect('../01_data_infrastructure/data/processed/banco_rio_digital.db')
df_tx = pd.read_sql('SELECT * FROM transacciones', conn)
df_cli = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

df_tx['fecha'] = pd.to_datetime(df_tx['fecha'])

alertas = []

# ============================================================
# PATRÓN 1: STRUCTURING — Transacciones fraccionadas
# Múltiples transacciones < $10.000 en el mismo día (umbral reportable)
# ============================================================
UMBRAL_REPORTE = 10000
df_tx['fecha_dia'] = df_tx['fecha'].dt.date

structuring = df_tx[df_tx['monto'] < UMBRAL_REPORTE].groupby(
    ['cliente_id', 'fecha_dia']
).agg(
    count=('transaccion_id', 'count'),
    monto_total=('monto', 'sum')
).reset_index()

structuring = structuring[
    (structuring['count'] >= 5) &
    (structuring['monto_total'] > UMBRAL_REPORTE)
]

for _, row in structuring.iterrows():
    alertas.append({
        'cliente_id': row['cliente_id'],
        'tipologia': 'STRUCTURING',
        'descripcion': f"{row['count']} transacciones < $10.000 en un día, total: ${row['monto_total']:,.0f}",
        'nivel_riesgo': 'ALTO',
        'fecha_deteccion': row['fecha_dia']
    })

# ============================================================
# PATRÓN 2: ACTIVIDAD INUSUAL — Volumen mensual >> historial
# ============================================================
mensual = df_tx.groupby(['cliente_id', df_tx['fecha'].dt.to_period('M')]).agg(
    monto_mes=('monto', 'sum')
).reset_index()
mensual.columns = ['cliente_id', 'mes', 'monto_mes']

stats_cliente = mensual.groupby('cliente_id')['monto_mes'].agg(['mean', 'std']).reset_index()
stats_cliente.columns = ['cliente_id', 'promedio_mensual', 'std_mensual']
mensual = mensual.merge(stats_cliente, on='cliente_id')
mensual['z_score'] = (mensual['monto_mes'] - mensual['promedio_mensual']) / (mensual['std_mensual'] + 1)

actividad_inusual = mensual[mensual['z_score'] > 3]
for _, row in actividad_inusual.iterrows():
    alertas.append({
        'cliente_id': row['cliente_id'],
        'tipologia': 'ACTIVIDAD_INUSUAL',
        'descripcion': f"Volumen {row['mes']}: ${row['monto_mes']:,.0f} ({row['z_score']:.1f}σ sobre su promedio)",
        'nivel_riesgo': 'MEDIO',
        'fecha_deteccion': str(row['mes'])
    })

# Generar reporte
df_alertas = pd.DataFrame(alertas)
df_alertas = df_alertas.merge(df_cli[['cliente_id', 'nombre', 'segmento']], on='cliente_id')

print("=" * 60)
print("SISTEMA AML — Reporte de Alertas")
print("=" * 60)
print(f"\nTotal alertas generadas: {len(df_alertas)}")
print(f"\nPor tipología:")
print(df_alertas['tipologia'].value_counts().to_string())
print(f"\nPor nivel de riesgo:")
print(df_alertas['nivel_riesgo'].value_counts().to_string())

df_alertas.to_csv('output_aml_alertas.csv', index=False)
print("\n✅ Alertas guardadas en output_aml_alertas.csv")
```

---

## Módulo 05 — Decision Engine

**Duración:** Semanas 11–13  
**Objetivo:** Construir una API REST que simule un motor de decisión crediticia en tiempo real.

### ¿Qué hace un motor de decisión?

```
CLIENTE SOLICITA CRÉDITO
         ↓
    Datos del cliente (score, ingresos, historial)
         ↓
    REGLAS DE NEGOCIO (configurables)
         ↓
    SCORING ENGINE
         ↓
    DECISIÓN: APROBADO / RECHAZADO / REVISIÓN MANUAL
         ↓
    Condiciones: monto, tasa, cuotas
```

### `decision_rules.json` — Reglas de negocio configurables

```json
{
  "reglas_rechazo_automatico": [
    {"campo": "score", "operador": "<", "valor": 400, "descripcion": "Score mínimo no alcanzado"},
    {"campo": "dias_mora_actual", "operador": ">", "valor": 90, "descripcion": "En mora crítica activa"},
    {"campo": "defaults_historicos", "operador": ">", "valor": 2, "descripcion": "Más de 2 defaults previos"}
  ],
  "reglas_aprobacion_automatica": [
    {"campo": "score", "operador": ">=", "valor": 700},
    {"campo": "dias_mora_actual", "operador": "=", "valor": 0},
    {"campo": "relacion_deuda_ingreso", "operador": "<", "valor": 0.35}
  ],
  "tabla_tasas": [
    {"segmento": "A", "score_min": 700, "score_max": 850, "tasa_anual": 0.12},
    {"segmento": "B", "score_min": 600, "score_max": 699, "tasa_anual": 0.18},
    {"segmento": "C", "score_min": 500, "score_max": 599, "tasa_anual": 0.25},
    {"segmento": "D", "score_min": 400, "score_max": 499, "tasa_anual": 0.35}
  ]
}
```

### `api.py` — API REST con FastAPI

```python
"""
Motor de Decisión Crediticia — API REST
Endpoint: POST /evaluar-credito
"""
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(
    title="Banco Río Digital — Motor de Decisión Crediticia",
    description="API para evaluación automática de solicitudes de crédito",
    version="1.0.0"
)

with open('decision_rules.json', 'r') as f:
    REGLAS = json.load(f)

class SolicitudCredito(BaseModel):
    cliente_id: int
    nombre: str
    score: int
    dias_mora_actual: int
    defaults_historicos: int
    ingreso_mensual: float
    monto_solicitado: float
    cuotas: int

class DecisionCredito(BaseModel):
    cliente_id: int
    decision: str          # APROBADO, RECHAZADO, REVISION_MANUAL
    motivo: str
    score: int
    segmento: str
    monto_aprobado: float
    tasa_anual: float
    cuota_mensual: float

@app.post("/evaluar-credito", response_model=DecisionCredito)
def evaluar_credito(solicitud: SolicitudCredito):
    # 1. Verificar rechazos automáticos
    for regla in REGLAS['reglas_rechazo_automatico']:
        valor_cliente = getattr(solicitud, regla['campo'])
        if regla['operador'] == '<' and valor_cliente < regla['valor']:
            return DecisionCredito(
                cliente_id=solicitud.cliente_id,
                decision='RECHAZADO',
                motivo=regla['descripcion'],
                score=solicitud.score,
                segmento='X',
                monto_aprobado=0,
                tasa_anual=0,
                cuota_mensual=0
            )

    # 2. Determinar segmento y tasa
    segmento, tasa = 'D', 0.35
    for t in REGLAS['tabla_tasas']:
        if t['score_min'] <= solicitud.score <= t['score_max']:
            segmento = t['segmento']
            tasa = t['tasa_anual']
            break

    # 3. Calcular cuota mensual
    tasa_mensual = tasa / 12
    cuota = solicitud.monto_solicitado * (tasa_mensual * (1 + tasa_mensual)**solicitud.cuotas) / \
            ((1 + tasa_mensual)**solicitud.cuotas - 1)

    # 4. Verificar relación cuota/ingreso
    relacion_ci = cuota / solicitud.ingreso_mensual
    if relacion_ci > 0.40:
        # Ajustar monto para que la cuota sea <= 40% del ingreso
        monto_maximo = solicitud.ingreso_mensual * 0.40 * ((1 + tasa_mensual)**solicitud.cuotas - 1) / \
                       (tasa_mensual * (1 + tasa_mensual)**solicitud.cuotas)
        cuota = solicitud.ingreso_mensual * 0.40
        monto_aprobado = monto_maximo
        decision = 'APROBADO' if monto_aprobado > solicitud.monto_solicitado * 0.50 else 'REVISION_MANUAL'
        motivo = f"Monto ajustado a ${monto_aprobado:,.0f} por capacidad de pago"
    else:
        monto_aprobado = solicitud.monto_solicitado
        decision = 'APROBADO'
        motivo = f"Solicitud aprobada. Segmento {segmento}"

    return DecisionCredito(
        cliente_id=solicitud.cliente_id,
        decision=decision,
        motivo=motivo,
        score=solicitud.score,
        segmento=segmento,
        monto_aprobado=round(monto_aprobado, 2),
        tasa_anual=tasa,
        cuota_mensual=round(cuota, 2)
    )

@app.get("/")
def health_check():
    return {"status": "OK", "servicio": "Motor de Decisión Crediticia v1.0"}
```

### Cómo correr la API

```bash
cd 05_decision_engine
uvicorn api:app --reload

# La API queda disponible en:
# http://127.0.0.1:8000
# Documentación automática: http://127.0.0.1:8000/docs
```

---

## Módulo 06 — Executive Dashboard

**Duración:** Semanas 14–15  
**Objetivo:** Consolidar todo el análisis en un dashboard ejecutivo que cuente una historia financiera.

### KPIs financieros que debe mostrar el dashboard

Estos son los indicadores que cualquier director de riesgo de un banco quiere ver:

| KPI | Fórmula | Interpretación |
|---|---|---|
| **NPL Ratio** | Cartera mora >90 / Cartera total | Salud de la cartera |
| **Tasa de fraude** | Transacciones fraudulentas / Total | Exposición a fraude |
| **Coverage Ratio** | Provisiones / NPL | Cobertura de pérdidas |
| **Expected Loss** | PD × LGD × EAD | Pérdida esperada |
| **Tasa de detección** | Fraudes detectados / Fraudes reales | Efectividad del sistema |
| **False Positive Rate** | Alertas falsas / Total alertas | Costo operativo del sistema |

### Estructura del dashboard en Power BI

**Página 1 — Cartera de Crédito**
- KPI: NPL Ratio (gauge)
- KPI: Expected Loss total (card)
- Gráfico: Distribución de cartera por segmento (donut)
- Gráfico: Vintage analysis (heat map)
- Tabla: Top 10 clientes por exposición

**Página 2 — Fraude**
- KPI: Tasa de fraude (card)
- KPI: Alertas generadas (card)
- Gráfico: Fraude por canal y horario (matrix)
- Gráfico: Evolución de fraude mensual (línea)

**Página 3 — AML**
- KPI: Alertas AML activas (card)
- Tabla: Tipologías detectadas con nivel de riesgo
- Gráfico: Alertas por segmento de cliente

---

## 11. Cronograma semana a semana

| Semana | Módulo | Actividad principal |
|---|---|---|
| 1 | 01 | Configurar repo, venv, estructura de carpetas |
| 2 | 01 | `generate_synthetic_data.py` + `schema.sql` + README |
| 3 | 02 | Estudiar PD/LGD/EAD + análisis exploratorio |
| 4 | 02 | `pd_lgd_ead.py` + `vintage_analysis.py` |
| 5 | 02 | Dashboard Power BI Credit Risk |
| 6 | 03 | Estudiar fraude + `rule_engine.py` |
| 7 | 03 | `anomaly_detection.py` + `fraud_model.py` |
| 8 | 03 | Dashboard Power BI Fraud + commits |
| 9 | 04 | Estudiar AML/KYC/BCRA + `aml_rule_engine.py` |
| 10 | 04 | `kyc_validator.py` + `sar_report_generator.py` |
| 11 | 05 | `decision_rules.json` + `scoring_engine.py` |
| 12 | 05 | `api.py` (FastAPI) + tests |
| 13 | 05 | README del módulo + documentación técnica |
| 14 | 06 | Dashboard ejecutivo Power BI (consolidado) |
| 15 | 06 | README.md principal del repo + pulir todo |

> **Tip:** Al final de cada semana, hacer commit y push. Los commits regulares demuestran proceso de trabajo, no solo el resultado final.

---

## 12. Cómo presentar el proyecto en entrevistas

### Frase de apertura (memorizar)

> *"Desarrollé un portfolio de proyectos aplicados al sector financiero. Diseñé un dataset sintético de un banco ficticio y construí sobre él un sistema de scoring crediticio con PD/LGD/EAD, un motor de detección de fraude con reglas y anomalías, un módulo AML con tipologías GAFI, y una API REST de decisión crediticia. El código está en GitHub y los dashboards en Power BI."*

### Preguntas técnicas que te van a hacer y cómo responder

| Pregunta | Respuesta que demuestra profundidad |
|---|---|
| "¿Qué es el PD?" | "Es la Probabilidad de Default, el porcentaje de clientes que se espera que no pague. En mi proyecto la calculé históricamente por segmento de score y la usé para calcular la Expected Loss de la cartera." |
| "¿Cómo manejaste los falsos positivos en fraude?" | "El motor de reglas tiene un threshold configurable. Medí precision y recall. Con un score_reglas ≥ 2, precision fue X% y recall Y%. Para producción, el umbral óptimo dependería del costo del falso positivo vs el costo del fraude no detectado." |
| "¿Qué es vintage analysis?" | "Compara el comportamiento de mora de préstamos según cuándo fueron otorgados. Permite identificar si las cosechas recientes tienen peor calidad crediticia que las anteriores." |
| "¿Qué sabés de AML?" | "Apliqué las tres tipologías más comunes según GAFI: structuring, actividad inusual y layering. Generé alertas con nivel de riesgo y un reporte tipo ROS para la UIF." |

### Lo que NO hay que decir

❌ "Hice un proyecto personal porque me falta experiencia"  
✅ "Desarrollé un sistema de análisis financiero para aplicar lo que estudio en Gestión Bancaria con herramientas reales del mercado"

---

## 13. Actualización del CV y LinkedIn

### Cuando termines, agregar en el CV (sección "Proyectos")

```
FINTECH Risk Portfolio — Proyecto personal · 2024–2025
github.com/hamil32/fintech-risk-portfolio

Sistema de análisis financiero completo para el sector bancario:
• Scorecard de crédito con cálculo de PD, LGD, EAD y Expected Loss (Basilea II)
• Motor de detección de fraude transaccional (reglas + Isolation Forest)
• Sistema AML/KYC con tipologías GAFI y generación de alertas regulatorias
• API REST de decisión crediticia con FastAPI (scoring automático)
• Dashboards ejecutivos en Power BI con KPIs de cartera y riesgo
Stack: Python · SQL · Power BI · FastAPI · scikit-learn · SQLite · Git
```

### Headline de LinkedIn a actualizar

```
Risk & Fraud Data Analyst | Python · SQL · Power BI | AML · Credit Risk · Decisioning
Gestión Bancaria — UCaSal · Finanzas + Datos + Automatización
```

### Posts de LinkedIn a publicar durante el proyecto

Publicar 1 post por módulo terminado:
- "Terminé el módulo de Credit Risk: así calculé PD, LGD y EAD en Python 📊"
- "Armé un motor de detección de fraude desde cero: precision 87%, recall 72% 🔍"
- "Implementé un sistema AML con tipologías GAFI en Python ✅"

Cada post: 3–5 párrafos técnicos, imagen del dashboard o snippet de código, link al GitHub.

---

## 14. Recursos y materiales de estudio

### Para módulo de Riesgo Crediticio
- **Libros:** "Credit Risk Management" — Gestel & Baesens
- **YouTube:** "Credit Risk Analytics Tutorial" (buscar en inglés y español)
- **Web:** bcra.gob.ar → Regulaciones → Gestión de riesgo crediticio

### Para módulo de Fraude
- **Kaggle datasets:** "IEEE-CIS Fraud Detection", "Credit Card Fraud Detection"
- **YouTube:** "Fraud Detection Machine Learning Python"
- **Papers:** "XGBoost for fraud detection" (Google Scholar)

### Para módulo AML
- **Web:** uif.gob.ar → Resoluciones → Tipologías de lavado
- **Web:** fatf-gafi.org → Typologies Reports (en inglés, muy completo)
- **YouTube:** "AML Compliance tutorial explained"

### Para FastAPI
- **Documentación oficial:** fastapi.tiangolo.com (muy buena, en español disponible)
- **YouTube:** "FastAPI tutorial Python" — hay varios tutoriales de 1–2 horas

### Datasets públicos para complementar
- **Kaggle:** kaggle.com/datasets → buscar "banking fraud", "credit risk"
- **UCI ML Repository:** archive.ics.uci.edu → "Default of credit card clients"
- **BCRA:** estadisticasbcra.com → datos macro del sistema financiero argentino

---

## 📌 Notas finales

1. **No esperes a terminar inglés para postularte.** Santander acepta explícitamente estudiantes avanzados de carreras afines para roles de Risk Data Analyst.

2. **Cada commit cuenta.** Los reclutadores técnicos miran el historial de GitHub. Un repositorio con 30 commits regulares durante 3 meses dice mucho más que uno con 1 commit con todo el código.

3. **El README principal es tu carta de presentación técnica.** Cuando alguien entre al repo, los primeros 30 segundos definen si sigue leyendo. Dedicarle tiempo al README del proyecto raíz.

4. **No hace falta que sea perfecto.** Un proyecto "en proceso" es mejor que uno que nunca se empezó. El mercado no espera perfección, espera evidencia de que podés hacer el trabajo.

5. **Consultá este instructivo regularmente.** Cada vez que empieces un módulo nuevo, releer la sección correspondiente y los conceptos financieros antes de codear.

---

*Instructivo elaborado para: Hamil Mauricio Selim Flores Balverdi*  
*Objetivo salarial: $3.000.000 – $3.500.000 ARS brutos mensuales*  
*Repositorio: github.com/hamil32/fintech-risk-portfolio*
