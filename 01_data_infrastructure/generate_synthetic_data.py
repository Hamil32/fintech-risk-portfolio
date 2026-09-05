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
    fecha = fecha_base.replace(hour=hora, minute=random.randint(0, 59), second=random.randint(0, 59))

    transacciones.append({
        'transaccion_id': i + 1,
        'cuenta_id': cuenta_id_tx,
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
print(f"   -> {len(df_transacciones)} transacciones generadas")
print(f"   -> Transacciones fraudulentas: {df_transacciones['es_fraude'].sum()} "
      f"({df_transacciones['es_fraude'].mean()*100:.1f}%)")

# ============================================================
# 4. PRÉSTAMOS
# ============================================================
print("\n[4/5] Generando prestamos...")

# Solo el 40% de clientes tiene préstamos
clientes_con_prestamo = random.sample(range(1, N_CLIENTES + 1), int(N_CLIENTES * 0.40))
tipos_prestamo = ['PERSONAL', 'HIPOTECARIO', 'PRENDARIO']
pesos_prestamo = [0.60, 0.25, 0.15]


def asignar_estado_mora(score):
    """Distribución de estados de mora según el score del cliente."""
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
