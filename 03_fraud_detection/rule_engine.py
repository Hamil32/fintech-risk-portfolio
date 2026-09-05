"""
Módulo 03 — Motor de reglas antifraude
Las reglas son el primer nivel de detección en cualquier sistema antifraude
real: simples, rápidas de calcular, 100% explicables (un analista puede ver
exactamente por qué se disparó una alerta) y no requieren entrenar ningún
modelo. Su contracara: son rígidas y fáciles de "esquivar" una vez que se
conocen los umbrales.
"""

import os
import sqlite3

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha'])
conn.close()

df = df.sort_values(['cliente_id', 'fecha']).reset_index(drop=True)

flags = pd.DataFrame({'transaccion_id': df['transaccion_id']})

# ============================================================
# REGLA 1: VELOCITY — más de 5 transacciones del mismo cliente en 1 hora
# ============================================================
# Se usa un rolling window basado en TIEMPO (no en cantidad de filas) sobre
# cada cliente por separado: para cada transacción, cuenta cuántas
# transacciones de ESE cliente cayeron en la última hora (incluida ella
# misma). Esto es lo que en producción se llama un "velocity check" —
# muchas operaciones en poco tiempo es la señal clásica de una cuenta
# comprometida (alguien probando límites antes de que el banco reaccione).
conteo_1h = (
    df.groupby('cliente_id')
    .rolling('1h', on='fecha')['transaccion_id']
    .count()
    .reset_index(level=0, drop=True)
)
df['count_1h'] = conteo_1h.values
flags['flag_velocity'] = (df['count_1h'] > 5).astype(int)

# ============================================================
# REGLA 2: MONTO ATÍPICO — más de 3 desvíos estándar sobre el propio
# comportamiento histórico del cliente
# ============================================================
# ⚠️ Simplificación deliberada: el promedio/desvío de cada cliente se
# calcula sobre TODAS sus transacciones del dataset (pasadas Y futuras
# respecto a cada transacción evaluada). En un sistema en producción real
# este cálculo debe hacerse solo con el historial ANTERIOR a la transacción
# que se evalúa (si no, hay data leakage: el modelo "ve" transacciones que
# todavía no pasaron). Acá se simplifica así porque no cambia el objetivo
# didáctico de la regla, pero es importante saber señalar la diferencia.
cliente_stats = df.groupby('cliente_id')['monto'].agg(['mean', 'std']).reset_index()
cliente_stats.columns = ['cliente_id', 'monto_medio', 'monto_std']
df = df.merge(cliente_stats, on='cliente_id')
df['z_score'] = (df['monto'] - df['monto_medio']) / (df['monto_std'].fillna(0) + 1)
flags['flag_monto_atipico'] = (df['z_score'] > 3).astype(int)

# ============================================================
# REGLA 3: HORARIO SOSPECHOSO — madrugada (1am–5am)
# ============================================================
df['hora'] = df['fecha'].dt.hour
flags['flag_horario_sospechoso'] = df['hora'].between(1, 5).astype(int)

# ============================================================
# REGLA 4: CANAL DIGITAL + MONTO ALTO — APP/Home Banking con monto > $20.000
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
# Umbral operativo: con 2 o más reglas activadas, la transacción pasa a revisión.
flags['requiere_revision'] = (flags['score_reglas'] >= 2).astype(int)

resultado = df[['transaccion_id', 'cliente_id', 'fecha', 'monto', 'canal', 'es_fraude']].merge(
    flags, on='transaccion_id'
)

# ============================================================
# EVALUACIÓN DEL MOTOR DE REGLAS CONTRA EL GROUND TRUTH (es_fraude)
# ============================================================
print("=" * 65)
print("MOTOR DE REGLAS ANTIFRAUDE — Evaluación")
print("=" * 65)
print(f"\nTransacciones analizadas: {len(resultado):,}")
print(f"Flags generados (score_reglas >= 2): {resultado['requiere_revision'].sum():,} "
      f"({resultado['requiere_revision'].mean()*100:.2f}%)")

print("\nDisparos por regla individual:")
for col in flag_cols:
    print(f"   {col:<28} {resultado[col].sum():>6,}  ({resultado[col].mean()*100:.2f}%)")

tp = ((resultado['requiere_revision'] == 1) & (resultado['es_fraude'] == 1)).sum()
fp = ((resultado['requiere_revision'] == 1) & (resultado['es_fraude'] == 0)).sum()
fn = ((resultado['requiere_revision'] == 0) & (resultado['es_fraude'] == 1)).sum()
tn = ((resultado['requiere_revision'] == 0) & (resultado['es_fraude'] == 0)).sum()

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"\nMatriz de confusión (umbral: score_reglas >= 2):")
print(f"   TP (fraude detectado):        {tp:>6,}")
print(f"   FP (falsa alarma):             {fp:>6,}")
print(f"   FN (fraude no detectado):      {fn:>6,}")
print(f"   TN (transacción normal, OK):   {tn:>6,}")

print(f"\nMétricas del motor de reglas:")
print(f"   Precision:  {precision:.3f}  (de cada 100 alertas, {precision*100:.1f} son fraude real)")
print(f"   Recall:     {recall:.3f}  (detecta el {recall*100:.1f}% de los fraudes reales)")
print(f"   F1-Score:   {f1:.3f}")

resultado.to_csv(os.path.join(OUT_DIR, 'fraud_rules_output.csv'), index=False)
print(f"\nResultados guardados en: {os.path.join(OUT_DIR, 'fraud_rules_output.csv')}")
