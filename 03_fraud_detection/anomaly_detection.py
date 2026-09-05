"""
Módulo 03 — Detección de anomalías (no supervisada)
A diferencia del motor de reglas (Módulo 03/rule_engine.py), que necesita
que un humano defina umbrales fijos, un modelo de detección de anomalías
aprende qué es "normal" a partir de los datos y señala lo que se aleja de
ese patrón — sin necesidad de que la transacción esté etiquetada como
fraude. Esto es clave en fraude real: la mayoría de los patrones nuevos de
fraude NO están etiquetados todavía cuando aparecen por primera vez.

Se usan dos técnicas complementarias:
  1. Isolation Forest — algoritmo de ensamble que aísla observaciones
     anómalas con menos particiones que las observaciones normales.
  2. Z-score multivariado simple, como comparación.
"""

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

RANDOM_STATE = 42

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha'])
conn.close()

df = df.sort_values(['cliente_id', 'fecha']).reset_index(drop=True)
df['hora'] = df['fecha'].dt.hour

# ============================================================
# FEATURE ENGINEERING
# ============================================================
# El monto se pasa a escala logarítmica antes de estandarizar: como se
# generó con una distribución log-normal (ver Módulo 01), su histograma
# original es muy asimétrico y eso confunde a Isolation Forest (que separa
# por umbrales); log1p lo acerca a una distribución simétrica.
df['log_monto'] = np.log1p(df['monto'])

# Desvío del comportamiento propio del cliente (mismo z-score que en
# rule_engine.py, ver la nota de leakage ahí).
cliente_stats = df.groupby('cliente_id')['monto'].agg(['mean', 'std']).reset_index()
cliente_stats.columns = ['cliente_id', 'monto_medio_cliente', 'monto_std_cliente']
df = df.merge(cliente_stats, on='cliente_id')
df['z_monto_cliente'] = (df['monto'] - df['monto_medio_cliente']) / (df['monto_std_cliente'].fillna(0) + 1)

canal_dummies = pd.get_dummies(df['canal'], prefix='canal')
df = pd.concat([df, canal_dummies], axis=1)

FEATURES = ['log_monto', 'hora', 'z_monto_cliente'] + list(canal_dummies.columns)
X = df[FEATURES].values
X_scaled = StandardScaler().fit_transform(X)

# ============================================================
# MODELO 1: ISOLATION FOREST
# ============================================================
# `contamination` = proporción esperada de anomalías. En un caso real NO
# se conoce la tasa real de fraude de antemano — acá se usa la tasa
# conocida del dataset sintético (2%) como punto de partida razonable,
# dejando explícito que en producción este parámetro se calibra con
# validación de negocio (cuántas alertas puede procesar el equipo por día),
# no con la respuesta "correcta".
CONTAMINATION = 0.02

modelo_if = IsolationForest(
    n_estimators=200,
    contamination=CONTAMINATION,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
df['if_prediccion'] = modelo_if.fit_predict(X_scaled)  # -1 = anomalía, 1 = normal
df['if_anomalia'] = (df['if_prediccion'] == -1).astype(int)
# decision_function: más negativo = más anómalo. Se invierte el signo para
# que "más alto = más sospechoso", más intuitivo para un ranking de alertas.
df['if_score_anomalia'] = -modelo_if.decision_function(X_scaled)

print("=" * 65)
print("DETECCIÓN DE ANOMALÍAS — Isolation Forest")
print("=" * 65)
print(f"\nTransacciones analizadas: {len(df):,}")
print(f"Marcadas como anomalía: {df['if_anomalia'].sum():,} ({df['if_anomalia'].mean()*100:.2f}%)")

# Validación contra el ground truth (es_fraude) — SOLO posible porque este
# es un dataset sintético con etiqueta conocida. En producción, un modelo
# no supervisado se valida con revisión manual de una muestra de alertas,
# no con una etiqueta perfecta disponible de antemano.
precision_if = precision_score(df['es_fraude'], df['if_anomalia'])
recall_if = recall_score(df['es_fraude'], df['if_anomalia'])
f1_if = f1_score(df['es_fraude'], df['if_anomalia'])
print(f"\nValidación contra es_fraude (ground truth del dataset sintético):")
print(f"   Precision: {precision_if:.3f}")
print(f"   Recall:    {recall_if:.3f}")
print(f"   F1-Score:  {f1_if:.3f}")

# ============================================================
# MODELO 2: Z-SCORE MULTIVARIADO (comparación simple)
# ============================================================
# Combina el z-score de monto propio del cliente con un z-score de "hora
# inusual" simple (distancia a las horas más frecuentes del canal). Sirve
# como benchmark ingenuo para poner en contexto qué tanto mejor es
# Isolation Forest.
df['z_combinado'] = np.abs(df['z_monto_cliente'])
umbral_z = df['z_combinado'].quantile(1 - CONTAMINATION)
df['z_anomalia'] = (df['z_combinado'] > umbral_z).astype(int)

precision_z = precision_score(df['es_fraude'], df['z_anomalia'])
recall_z = recall_score(df['es_fraude'], df['z_anomalia'])
f1_z = f1_score(df['es_fraude'], df['z_anomalia'])
print(f"\nBenchmark — solo z-score de monto (umbral top {CONTAMINATION*100:.0f}%):")
print(f"   Precision: {precision_z:.3f}")
print(f"   Recall:    {recall_z:.3f}")
print(f"   F1-Score:  {f1_z:.3f}")

print(f"\nComparación: Isolation Forest F1={f1_if:.3f} vs. Z-score simple F1={f1_z:.3f}")
if f1_if > f1_z:
    print("   -> Isolation Forest captura patrones (canal, horario, monto combinados)")
    print("      que el z-score univariado de monto no puede ver por sí solo.")
else:
    print("   -> En este dataset, el z-score simple es competitivo — señal de que el")
    print("      patrón de fraude inyectado es mayormente uni-dimensional (monto).")

# ============================================================
# GUARDAR RESULTADOS
# ============================================================
cols_salida = ['transaccion_id', 'cliente_id', 'fecha', 'monto', 'canal', 'hora',
               'z_monto_cliente', 'if_score_anomalia', 'if_anomalia', 'z_anomalia', 'es_fraude']
df[cols_salida].sort_values('if_score_anomalia', ascending=False).to_csv(
    os.path.join(OUT_DIR, 'anomaly_detection_output.csv'), index=False)
print(f"\nResultados guardados en: {os.path.join(OUT_DIR, 'anomaly_detection_output.csv')}")
