"""
Módulo 01 — Generación de datos sintéticos bancarios
Banco Río Digital — Dataset de desarrollo y análisis

Genera 5 tablas relacionadas (clientes, cuentas, transacciones, préstamos,
scoring_historico), las persiste en SQLite (data/processed/banco_rio_digital.db)
y exporta CSVs para consumo desde Power BI / pandas.
"""

import os
import random
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ============================================================
# CONFIGURACIÓN
# ============================================================
fake = Faker('es_AR')
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
Faker.seed(SEED)


def reseed(offset):
    """
    Re-fija la semilla antes de cada sección (con un offset distinto por
    sección) para que sean independientes entre sí: si mañana se edita la
    lógica de UNA sección (ej. transacciones), no se corre silenciosamente
    la secuencia de números aleatorios de las secciones siguientes
    (préstamos, scoring) y sus resultados ya documentados no cambian sin
    que nos demos cuenta.
    """
    np.random.seed(SEED + offset)
    random.seed(SEED + offset)

N_CLIENTES = 5000
N_TRANSACCIONES = 50000
FECHA_INICIO = datetime(2023, 1, 1)
FECHA_FIN = datetime(2023, 12, 31)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, 'data', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 60)
print("BANCO RÍO DIGITAL — Generador de datos sintéticos")
print("=" * 60)

# ============================================================
# 1. CLIENTES
# ============================================================
print("\n[1/5] Generando clientes...")

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
print(f"   -> {len(df_clientes)} clientes generados")
print(f"   -> Score promedio: {df_clientes['score_inicial'].mean():.0f}")
print(f"   -> Distribucion: {df_clientes['segmento'].value_counts().to_dict()}")

# ============================================================
# 2. CUENTAS
# ============================================================
print("\n[2/5] Generando cuentas...")
reseed(2)

tipos_cuenta_por_segmento = {
    'RETAIL': (['CC', 'CA', 'TARJETA'], [0.20, 0.50, 0.30]),
    'PYME': (['CC', 'CA', 'TARJETA'], [0.55, 0.30, 0.15]),
    'CORPORATIVO': (['CC', 'CA', 'TARJETA'], [0.70, 0.20, 0.10]),
}

cuentas = []
cuenta_id = 1
cuentas_por_cliente = {}  # cliente_id -> [cuenta_id, ...]

for _, cliente in df_clientes.iterrows():
    n_cuentas = np.random.choice([1, 2, 3], p=[0.55, 0.35, 0.10])
    tipos_posibles, pesos = tipos_cuenta_por_segmento[cliente['segmento']]
    tipos_elegidos = np.random.choice(tipos_posibles, size=n_cuentas, replace=True, p=pesos)

    ids_cliente = []
    for tipo_cuenta in tipos_elegidos:
        if tipo_cuenta == 'CC':
            saldo = round(np.random.lognormal(10, 1.3), 2)
        elif tipo_cuenta == 'CA':
            saldo = round(np.random.lognormal(9, 1.2), 2)
        else:  # TARJETA -> saldo negativo representa deuda consumida
            saldo = -round(np.random.lognormal(8.5, 1.0), 2)

        cuentas.append({
            'cuenta_id': cuenta_id,
            'cliente_id': cliente['cliente_id'],
            'tipo_cuenta': tipo_cuenta,
            'moneda': 'ARS',
            'saldo': saldo,
            'fecha_apertura': cliente['fecha_alta'],
        })
        ids_cliente.append(cuenta_id)
        cuenta_id += 1

    cuentas_por_cliente[cliente['cliente_id']] = ids_cliente

df_cuentas = pd.DataFrame(cuentas)
print(f"   -> {len(df_cuentas)} cuentas generadas para {N_CLIENTES} clientes")
print(f"   -> Distribucion por tipo: {df_cuentas['tipo_cuenta'].value_counts().to_dict()}")

# ============================================================
# 3. TRANSACCIONES
# ============================================================
print("\n[3/5] Generando transacciones...")
reseed(3)

tipos = ['DEBITO', 'CREDITO', 'TRANSFERENCIA', 'PAGO', 'EXTRACCION']
pesos_tipos = [0.30, 0.20, 0.25, 0.15, 0.10]
canales = ['APP', 'HOME_BANKING', 'POS', 'ATM', 'SUCURSAL']
pesos_canales = [0.35, 0.25, 0.20, 0.12, 0.08]

# 2% de transacciones fraudulentas
n_fraude = int(N_TRANSACCIONES * 0.02)
ids_fraude = set(random.sample(range(N_TRANSACCIONES), n_fraude))

transacciones = []
for i in range(N_TRANSACCIONES):
    cliente_id = random.randint(1, N_CLIENTES)
    cuenta_id_tx = random.choice(cuentas_por_cliente[cliente_id])
    es_fraude = i in ids_fraude
    tipo = np.random.choice(tipos, p=pesos_tipos)

    # Las transacciones fraudulentas tienen patrones MÁS PROBABLES, no
    # reglas absolutas — así como en el fraude real, hay solapamiento con
    # el comportamiento legítimo (si no, cualquier regla simple lo
    # detectaría al 100%, lo cual no pasa en la vida real).
    if es_fraude:
        # 80% "vaciado de cuenta" (monto alto), 20% "card testing"
        # (montos chicos para probar que la tarjeta/cuenta funciona
        # antes de un cargo grande) — un patrón de fraude real conocido.
        if random.random() < 0.80:
            monto = round(random.uniform(5000, 50000), 2)
        else:
            monto = round(random.uniform(50, 2000), 2)

        # 75% de madrugada, 25% en cualquier horario del día
        hora = random.randint(0, 5) if random.random() < 0.75 else random.randint(0, 23)

        # 85% por canal digital (típico de toma de cuenta), 15% físico
        # (tarjeta clonada en POS, retiro forzado en ATM)
        if random.random() < 0.85:
            canal = np.random.choice(['APP', 'HOME_BANKING'], p=[0.6, 0.4])
        else:
            canal = np.random.choice(['POS', 'ATM'], p=[0.5, 0.5])
    else:
        monto = round(abs(np.random.lognormal(8, 1.5)), 2)
        canal = np.random.choice(canales, p=pesos_canales)
        # 4% de las transacciones legítimas también ocurre de madrugada
        # (gente que opera de noche) — el horario nocturno por sí solo no
        # puede ser una señal perfecta de fraude, como pasa en la realidad.
        hora = random.randint(0, 5) if random.random() < 0.04 else random.randint(6, 23)

    fecha_base = FECHA_INICIO + timedelta(days=random.randint(0, 364))
    fecha = fecha_base.replace(hour=hora, minute=random.randint(0, 59), second=random.randint(0, 59))

    # Las TRANSFERENCIA son las únicas transacciones con una contraparte
    # identificable (cuenta/cliente destino) — sin esto no se puede detectar
    # de verdad ningún patrón AML de flujo de fondos (round-tripping,
    # layering), que por definición involucran MÁS de una cuenta.
    cuenta_destino_id, cliente_destino_id = None, None
    if tipo == 'TRANSFERENCIA':
        opciones_propias = [c for c in cuentas_por_cliente[cliente_id] if c != cuenta_id_tx]
        # 25% transferencia entre cuentas propias del mismo cliente (legítimo:
        # mover plata de la CA a la tarjeta, por ejemplo)
        if opciones_propias and random.random() < 0.25:
            cuenta_destino_id = random.choice(opciones_propias)
            cliente_destino_id = cliente_id
        else:
            cliente_destino_id = random.randint(1, N_CLIENTES)
            cuenta_destino_id = random.choice(cuentas_por_cliente[cliente_destino_id])

    transacciones.append({
        'transaccion_id': i + 1,
        'cuenta_id': cuenta_id_tx,
        'cliente_id': cliente_id,
        'cuenta_destino_id': cuenta_destino_id,
        'cliente_destino_id': cliente_destino_id,
        'fecha': fecha,
        'monto': monto,
        'tipo': tipo,
        'canal': canal,
        'comercio': fake.company() if tipo in ['DEBITO', 'PAGO'] else None,
        'ciudad': fake.city(),
        'es_fraude': int(es_fraude),
        'flag_revision': 0
    })

# Inyectar patrón de "velocity" (ráfaga) en una porción del fraude: agrupa
# transacciones fraudulentas ya generadas en grupos de 5, y a 1 de cada 4
# grupos los reasigna a UN MISMO cliente en una ventana de pocos minutos —
# simula una toma de cuenta real (varias operaciones seguidas antes de que
# el banco reaccione). Sin esto, el fraude queda disperso en el tiempo y la
# regla de velocity (Módulo 03) nunca tendría nada que detectar.
fraude_idx_ordenados = sorted(ids_fraude)
TAMANIO_RAFAGA = 7  # > 5 para que supere el umbral "más de 5 en 1 hora" de la regla de velocity
for inicio in range(0, len(fraude_idx_ordenados), TAMANIO_RAFAGA * 4):
    grupo = fraude_idx_ordenados[inicio: inicio + TAMANIO_RAFAGA]
    if len(grupo) < 6:
        continue
    cliente_rafaga = random.randint(1, N_CLIENTES)
    cuentas_cliente_rafaga = cuentas_por_cliente[cliente_rafaga]
    fecha_base_rafaga = FECHA_INICIO + timedelta(days=random.randint(0, 364), hours=random.randint(0, 5))
    for offset, idx in enumerate(grupo):
        transacciones[idx]['cliente_id'] = cliente_rafaga
        transacciones[idx]['cuenta_id'] = random.choice(cuentas_cliente_rafaga)
        # Espaciado corto (2-8 min) para que TODO el grupo quede dentro de
        # la misma ventana de 1 hora, incluso el último respecto al primero.
        transacciones[idx]['fecha'] = fecha_base_rafaga + timedelta(minutes=offset * random.randint(2, 8))

# ============================================================
# Inyección de patrones AML (Módulo 04): structuring y round-tripping
# ============================================================
# Se reutilizan transacciones YA generadas (fuera del pool de fraude) para
# no alterar el total de filas ni la tasa de fraude ya fijada. Sin esta
# inyección, un patrón de varios pasos coordinados (varias transacciones
# chicas el mismo día, o una cadena A->B->C->A) es estadísticamente casi
# imposible que aparezca por azar puro con solo ~10 transacciones/cliente
# al año — y el motor de reglas AML del Módulo 04 no tendría nada real que
# detectar.
indices_disponibles_aml = [i for i in range(N_TRANSACCIONES) if i not in ids_fraude]
random.shuffle(indices_disponibles_aml)
puntero_aml = 0

# --- STRUCTURING (smurfing): un cliente fracciona un monto grande en varias
# transacciones, todas por debajo del umbral reportable ($10.000), el mismo
# día — la tipología más clásica de evasión de reportes UIF/GAFI.
N_CASOS_STRUCTURING = 15
TAMANIO_STRUCTURING = 6
for _ in range(N_CASOS_STRUCTURING):
    grupo = indices_disponibles_aml[puntero_aml: puntero_aml + TAMANIO_STRUCTURING]
    puntero_aml += TAMANIO_STRUCTURING
    if len(grupo) < TAMANIO_STRUCTURING:
        break
    cliente_structuring = random.randint(1, N_CLIENTES)
    cuentas_cliente_structuring = cuentas_por_cliente[cliente_structuring]
    dia_structuring = FECHA_INICIO + timedelta(days=random.randint(0, 364))
    for idx in grupo:
        transacciones[idx]['cliente_id'] = cliente_structuring
        transacciones[idx]['cuenta_id'] = random.choice(cuentas_cliente_structuring)
        transacciones[idx]['cuenta_destino_id'] = None
        transacciones[idx]['cliente_destino_id'] = None
        transacciones[idx]['tipo'] = 'DEBITO'
        transacciones[idx]['monto'] = round(random.uniform(7000, 9800), 2)
        transacciones[idx]['fecha'] = dia_structuring.replace(
            hour=random.randint(9, 20), minute=random.randint(0, 59), second=random.randint(0, 59)
        )

# --- ROUND-TRIPPING: 3 clientes forman un anillo A->B->C->A. La plata sale
# de A, pasa por B y C, y vuelve a A en menos de una semana — "lavada" de
# origen al haber pasado por varias cuentas de terceros. El monto se reduce
# levemente en cada salto (simula comisiones/pérdidas del circuito).
N_ANILLOS = 12
for _ in range(N_ANILLOS):
    grupo = indices_disponibles_aml[puntero_aml: puntero_aml + 3]
    puntero_aml += 3
    if len(grupo) < 3:
        break
    clientes_anillo = random.sample(range(1, N_CLIENTES + 1), 3)
    fecha_base_anillo = FECHA_INICIO + timedelta(days=random.randint(0, 358))
    monto_actual = round(random.uniform(2_000_000, 8_000_000), 2)
    for salto, idx in enumerate(grupo):
        origen = clientes_anillo[salto]
        destino = clientes_anillo[(salto + 1) % 3]
        transacciones[idx]['cliente_id'] = origen
        transacciones[idx]['cuenta_id'] = random.choice(cuentas_por_cliente[origen])
        transacciones[idx]['cliente_destino_id'] = destino
        transacciones[idx]['cuenta_destino_id'] = random.choice(cuentas_por_cliente[destino])
        transacciones[idx]['tipo'] = 'TRANSFERENCIA'
        transacciones[idx]['canal'] = np.random.choice(['HOME_BANKING', 'APP'])
        transacciones[idx]['comercio'] = None
        transacciones[idx]['monto'] = round(monto_actual, 2)
        transacciones[idx]['fecha'] = fecha_base_anillo + timedelta(
            days=salto * 2, hours=random.randint(0, 12)
        )
        monto_actual *= random.uniform(0.90, 0.97)  # "comisión"/pérdida del circuito

# --- CASH-INTENSIVE: un cliente concentra muchas extracciones de efectivo
# en una ventana corta, por un monto total alto — proxy de negocio usado
# para "mezclar" efectivo de origen no declarado (ver aml_typologies.md).
N_CASOS_CASH = 10
TAMANIO_CASH = 9
for _ in range(N_CASOS_CASH):
    grupo = indices_disponibles_aml[puntero_aml: puntero_aml + TAMANIO_CASH]
    puntero_aml += TAMANIO_CASH
    if len(grupo) < TAMANIO_CASH:
        break
    cliente_cash = random.randint(1, N_CLIENTES)
    cuentas_cliente_cash = cuentas_por_cliente[cliente_cash]
    dia_inicio_cash = FECHA_INICIO + timedelta(days=random.randint(0, 335))  # deja margen de 30 días
    for idx in grupo:
        transacciones[idx]['cliente_id'] = cliente_cash
        transacciones[idx]['cuenta_id'] = random.choice(cuentas_cliente_cash)
        transacciones[idx]['cuenta_destino_id'] = None
        transacciones[idx]['cliente_destino_id'] = None
        transacciones[idx]['tipo'] = 'EXTRACCION'
        transacciones[idx]['canal'] = np.random.choice(['ATM', 'SUCURSAL'])
        transacciones[idx]['comercio'] = None
        transacciones[idx]['monto'] = round(random.uniform(60000, 120000), 2)
        transacciones[idx]['fecha'] = dia_inicio_cash + timedelta(
            days=random.randint(0, 29), hours=random.randint(8, 20)
        )

df_transacciones = pd.DataFrame(transacciones)
print(f"   -> {len(df_transacciones)} transacciones generadas")
print(f"   -> Transacciones fraudulentas: {df_transacciones['es_fraude'].sum()} "
      f"({df_transacciones['es_fraude'].mean()*100:.1f}%)")

# ============================================================
# 4. PRÉSTAMOS
# ============================================================
print("\n[4/5] Generando prestamos...")
reseed(4)

# Solo el 40% de clientes tiene préstamos
clientes_con_prestamo = random.sample(range(1, N_CLIENTES + 1), int(N_CLIENTES * 0.40))
tipos_prestamo = ['PERSONAL', 'HIPOTECARIO', 'PRENDARIO']
pesos_prestamo = [0.60, 0.25, 0.15]


def calcular_pd_score(score, pd_min=0.005, pd_max=0.45, score_mid=550, escala=60):
    """
    PD (probabilidad de default) en función continua del score, mediante una
    curva logística — la misma familia de función que usa un modelo real de
    regresión logística para traducir un score en una probabilidad. Esto
    garantiza que la PD sea monótona decreciente en todo el rango de score
    (a diferencia de usar 2-3 umbrales discretos, que dejan "escalones" y
    pueden romper la monotonicidad dentro de un mismo escalón).
    """
    exponente = (score - score_mid) / escala
    return pd_min + (pd_max - pd_min) / (1 + np.exp(exponente))


def calcular_pd_mora_temprana(score, pd_min=0.05, pd_max=0.40, score_mid=620, escala=50):
    """Probabilidad de estar en mora temprana (30/60 días) DADO que el
    préstamo no cayó en default. Misma lógica que calcular_pd_score pero
    con un punto medio más alto: la mora temprana es más frecuente que el
    default en cualquier nivel de score."""
    exponente = (score - score_mid) / escala
    return pd_min + (pd_max - pd_min) / (1 + np.exp(exponente))


def asignar_estado_mora(score):
    """
    Asigna el estado del préstamo en dos pasos, cada uno con su propia
    probabilidad dependiente del score (en vez de 2-3 baldes discretos):
      1. ¿Cae en default? (MORA_90 / INCOBRABLE) — probabilidad = calcular_pd_score(score)
      2. Si no cae en default, ¿está en mora temprana? (MORA_30 / MORA_60)
      3. Si no, está limpio (VIGENTE / CANCELADO)
    """
    if np.random.random() < calcular_pd_score(score):
        return np.random.choice(['MORA_90', 'INCOBRABLE'], p=[0.65, 0.35])

    if np.random.random() < calcular_pd_mora_temprana(score):
        return np.random.choice(['MORA_30', 'MORA_60'], p=[0.60, 0.40])

    return np.random.choice(['VIGENTE', 'CANCELADO'], p=[0.70, 0.30])


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
    dias_mora_map = {
        'VIGENTE': 0, 'CANCELADO': 0,
        'MORA_30': random.randint(1, 30),
        'MORA_60': random.randint(31, 60),
        'MORA_90': random.randint(61, 90),
        'INCOBRABLE': random.randint(91, 365),
    }

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
print(f"   -> {len(df_prestamos)} prestamos generados")
print("   -> Distribucion de estados:")
for estado, count in df_prestamos['estado'].value_counts().items():
    pct = count / len(df_prestamos) * 100
    print(f"      {estado}: {count} ({pct:.1f}%)")

# ============================================================
# 5. SCORING HISTÓRICO
# ============================================================
print("\n[5/5] Generando scoring historico...")
reseed(5)

bins = [0, 400, 500, 600, 700, 850]
labels_riesgo = ['E', 'D', 'C', 'B', 'A']
pd_por_segmento = {'E': 0.25, 'D': 0.15, 'C': 0.08, 'B': 0.03, 'A': 0.01}

scoring_historico = []
score_id = 1
meses = pd.period_range(FECHA_INICIO, FECHA_FIN, freq='Q')

for _, cliente in df_clientes.iterrows():
    score_actual = cliente['score_inicial']
    for periodo in meses:
        # pequeña deriva trimestral del score (mejora o empeora levemente)
        score_actual = int(np.clip(score_actual + np.random.normal(0, 15), 300, 850))
        segmento_riesgo = pd.cut([score_actual], bins=bins, labels=labels_riesgo)[0]
        scoring_historico.append({
            'id': score_id,
            'cliente_id': cliente['cliente_id'],
            'fecha': periodo.end_time.date(),
            'score': score_actual,
            'pd_estimada': pd_por_segmento[segmento_riesgo],
            'segmento_riesgo': segmento_riesgo,
        })
        score_id += 1

df_scoring = pd.DataFrame(scoring_historico)
print(f"   -> {len(df_scoring)} registros de scoring historico ({len(meses)} trimestres x {N_CLIENTES} clientes)")

# ============================================================
# 6. GUARDAR EN BASE DE DATOS
# ============================================================
print("\n[Guardando] Persistiendo en SQLite y CSV...")

db_path = os.path.join(OUT_DIR, 'banco_rio_digital.db')
conn = sqlite3.connect(db_path)

df_clientes.to_sql('clientes', conn, if_exists='replace', index=False)
df_cuentas.to_sql('cuentas', conn, if_exists='replace', index=False)
df_transacciones.to_sql('transacciones', conn, if_exists='replace', index=False)
df_prestamos.to_sql('prestamos', conn, if_exists='replace', index=False)
df_scoring.to_sql('scoring_historico', conn, if_exists='replace', index=False)

conn.close()
print(f"   -> Base de datos guardada en: {db_path}")

df_clientes.to_csv(os.path.join(OUT_DIR, 'clientes.csv'), index=False)
df_cuentas.to_csv(os.path.join(OUT_DIR, 'cuentas.csv'), index=False)
df_transacciones.to_csv(os.path.join(OUT_DIR, 'transacciones.csv'), index=False)
df_prestamos.to_csv(os.path.join(OUT_DIR, 'prestamos.csv'), index=False)
df_scoring.to_csv(os.path.join(OUT_DIR, 'scoring_historico.csv'), index=False)
print("   -> CSVs exportados para Power BI en data/processed/")

print("\n" + "=" * 60)
print("Generacion completada exitosamente")
print("=" * 60)
print("\nResumen final:")
print(f"  Clientes:            {len(df_clientes):,}")
print(f"  Cuentas:             {len(df_cuentas):,}")
print(f"  Transacciones:       {len(df_transacciones):,}")
print(f"  Prestamos:           {len(df_prestamos):,}")
print(f"  Scoring historico:   {len(df_scoring):,}")
