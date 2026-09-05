"""
Módulo 03 — Modelo supervisado de fraude
A diferencia de las reglas (fijas) y de Isolation Forest (no aprende de la
etiqueta), acá se entrena un clasificador supervisado que aprende
directamente de `es_fraude`. Es el enfoque que da mejor performance
cuando SÍ hay suficientes casos etiquetados de fraude confirmado — el
costo es que sólo aprende a reconocer los patrones que ya viste antes.

Se comparan dos modelos:
  - Regresión Logística (interpretable, rápida, buen baseline)
  - Random Forest (no lineal, generalmente más preciso, menos interpretable)
"""

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, classification_report, confusion_matrix,
    precision_recall_curve, roc_auc_score,
)
from sklearn.model_selection import train_test_split
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

X = df[FEATURES]
y = df['es_fraude']

# ============================================================
# TRAIN/TEST SPLIT ESTRATIFICADO
# ============================================================
# `stratify=y` asegura que la proporción de fraude (2%) sea la misma en
# train y test — con una clase tan minoritaria, un split aleatorio simple
# podría dejar por azar muy pocos casos de fraude en test.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("=" * 65)
print("MODELO SUPERVISADO DE FRAUDE")
print("=" * 65)
print(f"\nTrain: {len(X_train):,} transacciones ({y_train.sum()} fraudes, {y_train.mean()*100:.2f}%)")
print(f"Test:  {len(X_test):,} transacciones ({y_test.sum()} fraudes, {y_test.mean()*100:.2f}%)")


def evaluar_modelo(nombre, modelo, X_tr, X_te):
    modelo.fit(X_tr, y_train)
    y_pred = modelo.predict(X_te)
    y_proba = modelo.predict_proba(X_te)[:, 1]

    auc_roc = roc_auc_score(y_test, y_proba)
    # Average Precision (área bajo la curva Precision-Recall) es la métrica
    # recomendada por sobre AUC-ROC cuando la clase positiva es muy minoritaria
    # (como acá, ~2% fraude): el AUC-ROC puede verse "artificialmente alto"
    # porque hay muchísimos negativos fáciles de descartar.
    auc_pr = average_precision_score(y_test, y_proba)

    print(f"\n{'-'*65}\n{nombre}\n{'-'*65}")
    print(classification_report(y_test, y_pred, target_names=['NORMAL', 'FRAUDE'], digits=3))
    print(f"AUC-ROC: {auc_roc:.3f}   |   AUC-PR (Average Precision): {auc_pr:.3f}")

    cm = confusion_matrix(y_test, y_pred)
    print(f"Matriz de confusión:\n{cm}")

    return {'nombre': nombre, 'modelo': modelo, 'y_proba': y_proba, 'auc_roc': auc_roc, 'auc_pr': auc_pr}


# ============================================================
# MODELO 1: REGRESIÓN LOGÍSTICA (baseline interpretable)
# ============================================================
log_reg = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=RANDOM_STATE)
resultado_lr = evaluar_modelo("Regresión Logística (class_weight='balanced')", log_reg, X_train_scaled, X_test_scaled)

print("\nCoeficientes (impacto de cada variable en el log-odds de fraude):")
coefs = pd.Series(log_reg.coef_[0], index=FEATURES).sort_values(key=abs, ascending=False)
print(coefs.round(3).to_string())

# ============================================================
# MODELO 2: RANDOM FOREST
# ============================================================
rf = RandomForestClassifier(
    n_estimators=300, max_depth=8, class_weight='balanced',
    random_state=RANDOM_STATE, n_jobs=-1,
)
resultado_rf = evaluar_modelo("Random Forest (class_weight='balanced')", rf, X_train, X_test)

print("\nImportancia de variables (Random Forest):")
importancias = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(importancias.round(4).to_string())

# ============================================================
# COMPARACIÓN Y UMBRAL ÓPTIMO
# ============================================================
print(f"\n{'='*65}\nCOMPARACIÓN FINAL\n{'='*65}")
print(f"Regresión Logística  -> AUC-ROC: {resultado_lr['auc_roc']:.3f}  AUC-PR: {resultado_lr['auc_pr']:.3f}")
print(f"Random Forest         -> AUC-ROC: {resultado_rf['auc_roc']:.3f}  AUC-PR: {resultado_rf['auc_pr']:.3f}")

mejor = resultado_rf if resultado_rf['auc_pr'] >= resultado_lr['auc_pr'] else resultado_lr
print(f"\nMejor modelo por AUC-PR: {mejor['nombre']}")

# Curva Precision-Recall del mejor modelo: permite elegir el umbral según
# cuánto "presupuesto de revisión" tiene el equipo de fraude (más recall
# implica revisar más alertas, con menor precision).
precisions, recalls, thresholds = precision_recall_curve(y_test, mejor['y_proba'])
tabla_umbrales = pd.DataFrame({
    'threshold': list(thresholds) + [1.0],
    'precision': precisions,
    'recall': recalls,
})
# Muestra algunos puntos de la curva a intervalos parejos de recall
puntos_referencia = tabla_umbrales.iloc[::max(1, len(tabla_umbrales)//10)]
print("\nCurva Precision-Recall (muestra de puntos, mejor modelo):")
print(puntos_referencia.round(3).to_string(index=False))

# ============================================================
# GUARDAR RESULTADOS
# ============================================================
df_test_resultado = X_test.copy()
df_test_resultado['transaccion_id'] = df.loc[X_test.index, 'transaccion_id'].values
df_test_resultado['es_fraude'] = y_test.values
df_test_resultado['proba_fraude_rf'] = resultado_rf['y_proba']
df_test_resultado['proba_fraude_logreg'] = resultado_lr['y_proba']
df_test_resultado.to_csv(os.path.join(OUT_DIR, 'fraud_model_test_predictions.csv'), index=False)
tabla_umbrales.to_csv(os.path.join(OUT_DIR, 'fraud_model_precision_recall_curve.csv'), index=False)
importancias.to_csv(os.path.join(OUT_DIR, 'fraud_model_feature_importance.csv'))

print(f"\nArchivos guardados en: {OUT_DIR}")
print("   - fraud_model_test_predictions.csv")
print("   - fraud_model_precision_recall_curve.csv")
print("   - fraud_model_feature_importance.csv")
