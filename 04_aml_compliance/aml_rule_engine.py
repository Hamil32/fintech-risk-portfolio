"""
Módulo 04 — Motor de detección AML
Identifica comportamientos alineados a 4 tipologías de lavado de dinero
(GAFI/UIF): structuring, round-tripping, actividad inusual y actividad
intensiva en efectivo. Ver aml_typologies.md para el detalle conceptual
de cada una.
"""

import os
import sqlite3

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

UMBRAL_REPORTE = 10_000       # 🟨 ilustrativo, no un umbral normativo real
VENTANA_ROUND_TRIPPING = 10   # días
VENTANA_CASH_INTENSIVE = 30   # días

conn = sqlite3.connect(DB_PATH)
df_tx = pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha'])
df_cli = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

alertas = []

# ============================================================
# TIPOLOGÍA 1: STRUCTURING — transacciones fraccionadas el mismo día
# ============================================================
df_tx['fecha_dia'] = df_tx['fecha'].dt.date

structuring = df_tx[df_tx['monto'] < UMBRAL_REPORTE].groupby(['cliente_id', 'fecha_dia']).agg(
    count=('transaccion_id', 'count'),
    monto_total=('monto', 'sum'),
).reset_index()
structuring = structuring[(structuring['count'] >= 5) & (structuring['monto_total'] > UMBRAL_REPORTE)]

for _, row in structuring.iterrows():
    alertas.append({
        'cliente_id': row['cliente_id'],
        'tipologia': 'STRUCTURING',
        'descripcion': f"{row['count']} transacciones < ${UMBRAL_REPORTE:,.0f} en un día, "
                        f"total: ${row['monto_total']:,.0f}",
        'nivel_riesgo': 'ALTO',
        'fecha_deteccion': row['fecha_dia'],
    })

print("=" * 65)
print("SISTEMA AML — Motor de detección de tipologías")
print("=" * 65)
print(f"\n[STRUCTURING] {len(structuring)} casos detectados")

# ============================================================
# TIPOLOGÍA 2: ROUND-TRIPPING — A -> B -> C -> A en una ventana corta
# ============================================================
# Se arma con 2 self-joins encadenados sobre las transferencias entre
# clientes distintos (se excluyen las transferencias entre cuentas propias,
# que no son un flujo de fondos entre partes).
transferencias = df_tx[
    (df_tx['tipo'] == 'TRANSFERENCIA') & (df_tx['cliente_id'] != df_tx['cliente_destino_id'])
][['transaccion_id', 'cliente_id', 'cliente_destino_id', 'fecha', 'monto']]

e1 = transferencias.rename(columns={
    'cliente_id': 'A', 'cliente_destino_id': 'B', 'fecha': 'fecha_1', 'monto': 'monto_1', 'transaccion_id': 'tx_1'
})
e2 = transferencias.rename(columns={
    'cliente_id': 'B', 'cliente_destino_id': 'C', 'fecha': 'fecha_2', 'monto': 'monto_2', 'transaccion_id': 'tx_2'
})
e3 = transferencias.rename(columns={
    'cliente_id': 'C', 'cliente_destino_id': 'A_vuelta', 'fecha': 'fecha_3', 'monto': 'monto_3', 'transaccion_id': 'tx_3'
})

ventana = pd.Timedelta(days=VENTANA_ROUND_TRIPPING)

paso12 = e1.merge(e2, on='B')
paso12 = paso12[
    (paso12['fecha_2'] >= paso12['fecha_1']) &
    (paso12['fecha_2'] <= paso12['fecha_1'] + ventana) &
    (paso12['A'] != paso12['C'])
]

anillos = paso12.merge(e3, on='C')
anillos = anillos[
    (anillos['A_vuelta'] == anillos['A']) &
    (anillos['fecha_3'] >= anillos['fecha_2']) &
    (anillos['fecha_3'] <= anillos['fecha_1'] + ventana)
]
# Cada anillo real puede aparecer más de una vez si hay transacciones
# adicionales que calzan por azar en la ventana — nos quedamos con el
# primer cierre de ciclo detectado por cada trío (A, tx_1) para no duplicar.
anillos = anillos.sort_values('fecha_3').drop_duplicates(subset=['A', 'tx_1'])

print(f"[ROUND-TRIPPING] {len(anillos)} circuitos A->B->C->A detectados")

for _, row in anillos.iterrows():
    alertas.append({
        'cliente_id': row['A'],
        'tipologia': 'ROUND_TRIPPING',
        'descripcion': (
            f"Circuito {int(row['A'])} -> {int(row['B'])} -> {int(row['C'])} -> {int(row['A'])} en "
            f"{(row['fecha_3'] - row['fecha_1']).days} días. "
            f"Montos: ${row['monto_1']:,.0f} / ${row['monto_2']:,.0f} / ${row['monto_3']:,.0f}"
        ),
        'nivel_riesgo': 'ALTO',
        'fecha_deteccion': row['fecha_1'].date(),
    })

# ============================================================
# TIPOLOGÍA 3: ACTIVIDAD INUSUAL — volumen mensual >> historial del cliente
# ============================================================
mensual = df_tx.groupby(['cliente_id', df_tx['fecha'].dt.to_period('M')]).agg(
    monto_mes=('monto', 'sum')
).reset_index()
mensual.columns = ['cliente_id', 'mes', 'monto_mes']

stats_cliente = mensual.groupby('cliente_id')['monto_mes'].agg(['mean', 'std']).reset_index()
stats_cliente.columns = ['cliente_id', 'promedio_mensual', 'std_mensual']
mensual = mensual.merge(stats_cliente, on='cliente_id')
mensual['z_score'] = (mensual['monto_mes'] - mensual['promedio_mensual']) / (mensual['std_mensual'].fillna(0) + 1)

actividad_inusual = mensual[mensual['z_score'] > 3]
print(f"[ACTIVIDAD INUSUAL] {len(actividad_inusual)} casos detectados")

for _, row in actividad_inusual.iterrows():
    alertas.append({
        'cliente_id': row['cliente_id'],
        'tipologia': 'ACTIVIDAD_INUSUAL',
        'descripcion': f"Volumen {row['mes']}: ${row['monto_mes']:,.0f} ({row['z_score']:.1f}σ sobre su promedio)",
        'nivel_riesgo': 'MEDIO',
        'fecha_deteccion': str(row['mes']),
    })

# ============================================================
# TIPOLOGÍA 4: ACTIVIDAD INTENSIVA EN EFECTIVO (proxy: EXTRACCION)
# ============================================================
extracciones = df_tx[df_tx['tipo'] == 'EXTRACCION'].sort_values(['cliente_id', 'fecha'])
conteo_30d = (
    extracciones.groupby('cliente_id')
    .rolling(f'{VENTANA_CASH_INTENSIVE}D', on='fecha')['monto']
    .agg(['count', 'sum'])
    .reset_index()
)
# Umbral: clientes con muchas extracciones (>=8) y monto total alto (>$500.000)
# en una ventana de 30 días — 🟨 valores ilustrativos.
cash_intensive = conteo_30d[(conteo_30d['count'] >= 8) & (conteo_30d['sum'] > 500_000)]
cash_intensive = cash_intensive.sort_values('fecha').drop_duplicates(subset=['cliente_id'], keep='first')

print(f"[CASH-INTENSIVE] {len(cash_intensive)} casos detectados")

for _, row in cash_intensive.iterrows():
    alertas.append({
        'cliente_id': row['cliente_id'],
        'tipologia': 'CASH_INTENSIVE',
        'descripcion': f"{int(row['count'])} extracciones en {VENTANA_CASH_INTENSIVE} días, "
                        f"total: ${row['sum']:,.0f}",
        'nivel_riesgo': 'MEDIO',
        'fecha_deteccion': row['fecha'].date(),
    })

# ============================================================
# CONSOLIDAR Y REPORTAR
# ============================================================
df_alertas = pd.DataFrame(alertas)
df_alertas = df_alertas.merge(df_cli[['cliente_id', 'nombre', 'segmento', 'score_inicial']], on='cliente_id')

print(f"\n{'='*65}\nTotal alertas generadas: {len(df_alertas)}")
print(f"\nPor tipología:\n{df_alertas['tipologia'].value_counts().to_string()}")
print(f"\nPor nivel de riesgo:\n{df_alertas['nivel_riesgo'].value_counts().to_string()}")
print(f"\nPor segmento de cliente:\n{df_alertas['segmento'].value_counts().to_string()}")

df_alertas.to_csv(os.path.join(OUT_DIR, 'aml_alertas.csv'), index=False)
print(f"\nAlertas guardadas en: {os.path.join(OUT_DIR, 'aml_alertas.csv')}")
