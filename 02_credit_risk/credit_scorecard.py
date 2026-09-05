"""
Módulo 02 — Credit Scorecard
Construye un scorecard de puntos siguiendo la metodología estándar de la
industria (Weight of Evidence + Regresión Logística + escalado a puntos),
tal como se describe en el libro de referencia de la industria:
Naeem Siddiqi, "Credit Risk Scorecards: Developing and Implementing
Intelligent Credit Scoring".

Pasos:
1. Binning de variables (agrupar valores continuos/categóricos en clases)
2. WOE (Weight of Evidence) e IV (Information Value) por variable
3. Regresión logística sobre las variables transformadas a WOE
4. Escalado de los coeficientes a una escala de puntos (Score = Offset + Factor × ln(odds))
5. Validación del scorecard resultante (AUC / Gini)
"""

import os
import sqlite3

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# Constantes de escalado del scorecard (convención estándar de la industria,
# el mismo ejemplo numérico usado en el libro de Siddiqi):
#   - a "BASE_SCORE" puntos, la relación de momios buenos:malos es "BASE_ODDS" a 1
#   - "PDO" (Points to Double the Odds): cuántos puntos hacen falta para
#     duplicar la relación de momios buenos:malos
BASE_SCORE = 600
BASE_ODDS = 50
PDO = 20

EPS = 1e-4  # para evitar log(0) en bins sin casos de una clase

# ============================================================
# CARGA DE DATOS
# ============================================================
conn = sqlite3.connect(DB_PATH)
prestamos = pd.read_sql('SELECT * FROM prestamos', conn)
clientes = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

df = prestamos.merge(clientes[['cliente_id', 'score_inicial', 'segmento', 'edad']], on='cliente_id')

# Target: "malo" = default (mora > 90 días o incobrable), igual definición
# que en pd_lgd_ead.py para que todo el módulo sea consistente.
df['es_malo'] = df['estado'].isin(['MORA_90', 'INCOBRABLE']).astype(int)
df['es_bueno'] = 1 - df['es_malo']

# ============================================================
# 1. BINNING de variables predictoras
# ============================================================
bins_score = [0, 400, 500, 600, 700, 850]
labels_score = ['E', 'D', 'C', 'B', 'A']
df['bin_score'] = pd.cut(df['score_inicial'], bins=bins_score, labels=labels_score)

bins_edad = [17, 25, 35, 45, 55, 65, 100]
labels_edad = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
df['bin_edad'] = pd.cut(df['edad'], bins=bins_edad, labels=labels_edad)

# segmento y tipo de préstamo ya son categóricos, se usan tal cual como "bins"
df['bin_segmento'] = df['segmento']
df['bin_tipo'] = df['tipo']

VARIABLES = ['bin_score', 'bin_edad', 'bin_segmento', 'bin_tipo']
NOMBRES = {'bin_score': 'Score inicial', 'bin_edad': 'Edad',
           'bin_segmento': 'Segmento', 'bin_tipo': 'Tipo de préstamo'}


# ============================================================
# 2. WOE (Weight of Evidence) e IV (Information Value)
# ============================================================
def calcular_woe_iv(data, feature, target_malo='es_malo'):
    """
    WOE = ln( %Buenos_en_el_bin / %Malos_en_el_bin )
    Un WOE positivo indica un bin más seguro que el promedio de la cartera;
    un WOE negativo indica un bin más riesgoso.

    IV = Σ (%Buenos - %Malos) × WOE  →  mide cuánto poder predictivo aporta
    la variable completa. Regla de interpretación estándar de la industria:
        < 0.02        no predictiva
        0.02 - 0.10    predictiva débil
        0.10 - 0.30    predictiva media
        0.30 - 0.50    predictiva fuerte
        > 0.50         sospechosamente fuerte (revisar fuga de información)
    """
    grp = data.groupby(feature, observed=True)[target_malo].agg(['count', 'sum'])
    grp.columns = ['total', 'malos']
    grp['buenos'] = grp['total'] - grp['malos']

    total_buenos = grp['buenos'].sum()
    total_malos = grp['malos'].sum()

    grp['pct_buenos'] = (grp['buenos'] / total_buenos).replace(0, EPS)
    grp['pct_malos'] = (grp['malos'] / total_malos).replace(0, EPS)
    grp['woe'] = np.log(grp['pct_buenos'] / grp['pct_malos'])
    grp['iv_bin'] = (grp['pct_buenos'] - grp['pct_malos']) * grp['woe']

    iv_total = grp['iv_bin'].sum()
    return grp, iv_total


print("=" * 70)
print("CREDIT SCORECARD — Banco Río Digital")
print("=" * 70)

tablas_woe = {}
iv_por_variable = {}
for var in VARIABLES:
    tabla, iv = calcular_woe_iv(df, var)
    tablas_woe[var] = tabla
    iv_por_variable[var] = iv

    print(f"\n[{NOMBRES[var]}] Information Value = {iv:.4f}")
    print(tabla[['total', 'buenos', 'malos', 'woe']].round(4).to_string())

    # Mapear el WOE de vuelta al dataframe original como nueva columna
    df[f'woe_{var}'] = df[var].map(tabla['woe'])

print("\nRanking de poder predictivo (Information Value):")
iv_ranking = pd.Series(iv_por_variable).sort_values(ascending=False)
for var, iv in iv_ranking.items():
    interpretacion = (
        'no predictiva' if iv < 0.02 else
        'débil' if iv < 0.10 else
        'media' if iv < 0.30 else
        'fuerte' if iv < 0.50 else
        'sospechosa (posible fuga de datos)'
    )
    print(f"   {NOMBRES[var]:<20} IV = {iv:.4f}  ({interpretacion})")

# ============================================================
# 3. REGRESIÓN LOGÍSTICA sobre variables en escala WOE
# ============================================================
woe_cols = [f'woe_{v}' for v in VARIABLES]
X = df[woe_cols].values
y = df['es_bueno'].values  # target = 1 si es buen pagador

modelo = LogisticRegression()
modelo.fit(X, y)

beta = modelo.coef_[0]
intercepto = modelo.intercept_[0]

print("\n" + "-" * 70)
print("REGRESIÓN LOGÍSTICA (sobre variables en escala WOE)")
print("-" * 70)
print(f"Intercepto: {intercepto:.4f}")
for var, b in zip(VARIABLES, beta):
    print(f"   Beta [{NOMBRES[var]}]: {b:.4f}")

# ============================================================
# 4. ESCALADO A PUNTOS
# ============================================================
# Score = Offset + Factor × ln(Odds_bueno)
# donde ln(Odds_bueno) = Intercepto + Σ Beta_i × WOE_i
FACTOR = PDO / np.log(2)
OFFSET = BASE_SCORE - FACTOR * np.log(BASE_ODDS)
N_VARS = len(VARIABLES)

print(f"\nEscalado: Factor = {FACTOR:.3f} | Offset = {OFFSET:.3f} "
      f"(base: {BASE_SCORE} pts = odds {BASE_ODDS}:1, PDO = {PDO})")

# Puntos de cada bin de cada variable: se reparte el offset + factor*intercepto
# en partes iguales entre las N variables, y se le suma el aporte propio del bin.
scorecard_rows = []
for var in VARIABLES:
    beta_var = beta[VARIABLES.index(var)]
    tabla = tablas_woe[var]
    for bin_valor, fila in tabla.iterrows():
        puntos = FACTOR * beta_var * fila['woe'] + (OFFSET + FACTOR * intercepto) / N_VARS
        scorecard_rows.append({
            'variable': NOMBRES[var],
            'bin': bin_valor,
            'woe': round(fila['woe'], 4),
            'puntos': round(puntos, 1),
        })

scorecard = pd.DataFrame(scorecard_rows)
print("\n" + "-" * 70)
print("SCORECARD FINAL (puntos por variable y bin)")
print("-" * 70)
print(scorecard.to_string(index=False))

# ============================================================
# 5. CALCULAR EL SCORE TOTAL DE CADA PRÉSTAMO Y VALIDAR EL MODELO
# ============================================================
puntos_por_bin = {var: dict(zip(scorecard[scorecard['variable'] == NOMBRES[var]]['bin'],
                                 scorecard[scorecard['variable'] == NOMBRES[var]]['puntos']))
                   for var in VARIABLES}

df['score_final'] = sum(df[var].map(puntos_por_bin[var]).astype(float) for var in VARIABLES)

# Validación: el score final predicho por el scorecard, ¿ordena bien el riesgo?
prob_bueno = modelo.predict_proba(X)[:, 1]
auc = roc_auc_score(y, prob_bueno)
gini = 2 * auc - 1

print("\n" + "-" * 70)
print("VALIDACIÓN DEL SCORECARD")
print("-" * 70)
print(f"AUC (Area Under the ROC Curve): {auc:.4f}")
print(f"Gini (2×AUC - 1):               {gini:.4f}")
print("   Referencia: AUC 0.5 = no discrimina nada (azar). AUC > 0.7 se considera")
print("   aceptable para un scorecard, > 0.8 muy bueno, > 0.9 sospechoso (revisar fuga).")

score_medio_buenos = df.loc[df['es_bueno'] == 1, 'score_final'].mean()
score_medio_malos = df.loc[df['es_bueno'] == 0, 'score_final'].mean()
print(f"\nScore promedio de clientes BUENOS (no default): {score_medio_buenos:.0f} pts")
print(f"Score promedio de clientes MALOS  (default):     {score_medio_malos:.0f} pts")
print("   (un scorecard útil debe mostrar una diferencia clara entre ambos grupos)")

# ============================================================
# GUARDAR RESULTADOS
# ============================================================
scorecard.to_csv(os.path.join(OUT_DIR, 'scorecard_puntos.csv'), index=False)
df[['prestamo_id', 'cliente_id', 'segmento', 'score_inicial', 'edad', 'tipo',
    'estado', 'es_malo', 'score_final']].to_csv(
    os.path.join(OUT_DIR, 'scorecard_aplicado.csv'), index=False)

print(f"\nArchivos guardados en: {OUT_DIR}")
print("   - scorecard_puntos.csv       (la tabla de puntos del scorecard)")
print("   - scorecard_aplicado.csv     (score final calculado por préstamo)")
