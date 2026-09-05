"""
Módulo 03 — Sistema de alertas (orquestación)
Ningún banco real usa UNA sola técnica antifraude — usa varias en capas,
porque cada una tiene un punto ciego distinto:
  - Reglas:            rígidas pero 100% explicables, no requieren etiqueta.
  - Isolation Forest:  detecta patrones nuevos, pero sin la etiqueta pierde
                        precisión (ver Módulo 03/anomaly_detection.py).
  - Modelo supervisado: el más preciso, pero solo aprende fraude que YA vio.

Este script combina las tres señales en un sistema de alertas priorizado
(como el que vería un analista de fraude en su cola de trabajo), y estima
el impacto operativo (cuántas alertas por día, cuánto fraude se captura a
cada nivel de prioridad).
"""

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
RANDOM_STATE = 42

# ============================================================
# 1. CARGAR LAS SALIDAS DE LOS DOS SCRIPTS ANTERIORES
# ============================================================
# Se reutilizan los resultados ya calculados por rule_engine.py y
# anomaly_detection.py en vez de recalcular su lógica acá — así el sistema
# de alertas se limita a ORQUESTAR señales que ya existen, que es
# justamente su rol (no vuelve a decidir qué es una regla o una anomalía).
ruta_reglas = os.path.join(OUT_DIR, 'fraud_rules_output.csv')
ruta_anomalias = os.path.join(OUT_DIR, 'anomaly_detection_output.csv')

if not (os.path.exists(ruta_reglas) and os.path.exists(ruta_anomalias)):
    raise SystemExit(
        "Faltan archivos de entrada. Corré primero:\n"
        "  python rule_engine.py\n"
        "  python anomaly_detection.py\n"
    )

reglas = pd.read_csv(ruta_reglas)[['transaccion_id', 'score_reglas', 'requiere_revision']]
anomalias = pd.read_csv(ruta_anomalias)[['transaccion_id', 'if_anomalia', 'if_score_anomalia']]

# ============================================================
# 2. SCORE DEL MODELO SUPERVISADO PARA EL 100% DE LAS TRANSACCIONES
# ============================================================
# fraud_model.py solo guarda las predicciones del 25% de test (para poder
# medir performance de forma honesta). Para el sistema de alertas hace
# falta un score de riesgo para TODAS las transacciones. Usar el modelo ya
# entrenado sobre datos que vio en entrenamiento daría un score
# artificialmente optimista, así que se usa `cross_val_predict`: entrena 5
# modelos en folds distintos y a cada transacción la puntúa con un modelo
# que NUNCA la vio en entrenamiento — el mismo principio de honestidad que
# el train/test split, pero aplicado a la población completa.
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha'])
conn.close()

df['hora'] = df['fecha'].dt.hour
df['log_monto'] = np.log1p(df['monto'])
cliente_stats = df.groupby('cliente_id')['monto'].agg(['mean', 'std']).reset_index()
cliente_stats.columns = ['cliente_id', 'monto_medio_cliente', 'monto_std_cliente']
df = df.merge(cliente_stats, on='cliente_id')
df['z_monto_cliente'] = (df['monto'] - df['monto_medio_cliente']) / (df['monto_std_cliente'].fillna(0) + 1)
df['es_horario_sospechoso'] = df['hora'].between(1, 5).astype(int)
df['es_canal_digital'] = df['canal'].isin(['APP', 'HOME_BANKING']).astype(int)
canal_dummies = pd.get_dummies(df['canal'], prefix='canal')
tipo_dummies = pd.get_dummies(df['tipo'], prefix='tipo')
df = pd.concat([df, canal_dummies, tipo_dummies], axis=1)

FEATURES = (['log_monto', 'hora', 'z_monto_cliente', 'es_horario_sospechoso', 'es_canal_digital']
            + list(canal_dummies.columns) + list(tipo_dummies.columns))
X, y = df[FEATURES], df['es_fraude']

rf = RandomForestClassifier(n_estimators=300, max_depth=8, class_weight='balanced',
                             random_state=RANDOM_STATE, n_jobs=-1)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
print("=" * 65)
print("SISTEMA DE ALERTAS — Orquestación de señales")
print("=" * 65)
print("\nCalculando score del modelo supervisado para el 100% de las "
      "transacciones (5-fold cross-validation, out-of-fold)...")
proba_oof = cross_val_predict(rf, X, y, cv=cv, method='predict_proba', n_jobs=-1)[:, 1]
df['proba_modelo'] = proba_oof

# ============================================================
# 3. CONSOLIDAR LAS 3 SEÑALES
# ============================================================
alertas = df[['transaccion_id', 'cliente_id', 'fecha', 'monto', 'canal', 'es_fraude', 'proba_modelo']]
alertas = alertas.merge(reglas, on='transaccion_id').merge(anomalias, on='transaccion_id')


def clasificar_prioridad(row):
    """
    Lógica de triage, igual a la que usaría un equipo de fraude para
    decidir en qué orden revisar su cola de alertas:
      - CRÍTICA: el modelo está muy confiado (>=70%) -> revisar ya.
      - ALTA: al menos 2 de las 3 señales coinciden -> alta confianza cruzada.
      - MEDIA: una sola señal se disparó -> vale la pena mirar, no urgente.
      - SIN ALERTA: ninguna señal.
    """
    señales_binarias = int(row['requiere_revision']) + int(row['if_anomalia']) + int(row['proba_modelo'] >= 0.3)

    if row['proba_modelo'] >= 0.70:
        return 'CRÍTICA'
    if señales_binarias >= 2:
        return 'ALTA'
    if señales_binarias == 1:
        return 'MEDIA'
    return 'SIN ALERTA'


alertas['prioridad'] = alertas.apply(clasificar_prioridad, axis=1)


def armar_motivo(row):
    motivos = []
    if row['requiere_revision']:
        motivos.append(f"reglas(score={int(row['score_reglas'])})")
    if row['if_anomalia']:
        motivos.append("anomalía(Isolation Forest)")
    if row['proba_modelo'] >= 0.3:
        motivos.append(f"modelo(p={row['proba_modelo']:.2f})")
    return " + ".join(motivos) if motivos else "sin señales"


alertas['motivo'] = alertas.apply(armar_motivo, axis=1)

# ============================================================
# 4. MÉTRICAS OPERATIVAS POR NIVEL DE PRIORIDAD
# ============================================================
orden_prioridad = ['CRÍTICA', 'ALTA', 'MEDIA', 'SIN ALERTA']
resumen = alertas.groupby('prioridad').agg(
    transacciones=('transaccion_id', 'count'),
    fraudes_reales=('es_fraude', 'sum'),
).reindex(orden_prioridad)
resumen['tasa_acierto_pct'] = (resumen['fraudes_reales'] / resumen['transacciones'] * 100).round(2)
resumen['pct_del_total'] = (resumen['transacciones'] / len(alertas) * 100).round(2)

print("\nDistribución de la cola de alertas por prioridad:")
print(resumen.to_string())

# Cobertura acumulada: si el equipo revisa CRÍTICA + ALTA, ¿qué % del
# fraude total se captura? (tabla de "ganancias" — gains table — estándar
# en la evaluación de sistemas de scoring/alertas)
total_fraudes = alertas['es_fraude'].sum()
acumulado = 0
print("\nCobertura acumulada de fraude por nivel de prioridad revisado:")
for nivel in orden_prioridad:
    if nivel not in resumen.index or pd.isna(resumen.loc[nivel, 'fraudes_reales']):
        continue
    acumulado += resumen.loc[nivel, 'fraudes_reales']
    print(f"   Revisando hasta '{nivel}': {acumulado:.0f}/{total_fraudes} fraudes "
          f"capturados ({acumulado/total_fraudes*100:.1f}%)")

# Estimación operativa: minutos de analista por alerta (valor ilustrativo
# razonable para una revisión manual de caso, no una cifra publicada).
MINUTOS_POR_ALERTA = 4
alertas_criticas_altas = resumen.loc[['CRÍTICA', 'ALTA'], 'transacciones'].sum()
horas_analista_dia = (alertas_criticas_altas * MINUTOS_POR_ALERTA / 60) / 365  # dataset cubre 1 año
print(f"\nEstimación operativa (revisando solo CRÍTICA + ALTA, {MINUTOS_POR_ALERTA} min/alerta):")
print(f"   {alertas_criticas_altas:,.0f} alertas/año -> ~{horas_analista_dia:.2f} horas de analista por día")
print("   (valor ilustrativo para dimensionar el equipo, no una cifra de la industria)")

# ============================================================
# 5. GUARDAR LA COLA DE ALERTAS
# ============================================================
alertas_a_revisar = alertas[alertas['prioridad'] != 'SIN ALERTA'].sort_values(
    ['prioridad', 'proba_modelo'], ascending=[True, False]
)
alertas_a_revisar.to_csv(os.path.join(OUT_DIR, 'alert_queue.csv'), index=False)
print(f"\nCola de alertas guardada en: {os.path.join(OUT_DIR, 'alert_queue.csv')}")
print(f"   ({len(alertas_a_revisar):,} transacciones a revisar de {len(alertas):,} totales)")
