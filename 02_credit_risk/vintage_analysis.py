"""
Módulo 02 — Vintage Analysis
Compara el comportamiento de mora de préstamos según la cohorte
(trimestre) en la que fueron otorgados. Permite responder: "¿las
cosechas de crédito más recientes están teniendo peor calidad que
las anteriores?" — una de las preguntas centrales del monitoreo de
cartera en cualquier banco.
"""

import os
import sqlite3

import matplotlib
matplotlib.use('Agg')  # backend sin ventana, para poder correr sin entorno gráfico
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql('SELECT * FROM prestamos', conn, parse_dates=['fecha_otorgamiento'])
conn.close()

# Cohorte = trimestre en el que se otorgó el préstamo
df['cohorte'] = df['fecha_otorgamiento'].dt.to_period('Q')

# "En mora" = cualquier préstamo con días de atraso > 0 (incluye MORA_30/60/90)
df['en_mora'] = df['dias_mora'] > 0
# "En NPL" = mora > 90 días, el umbral de incumplimiento (Basilea/BCRA)
df['en_npl'] = df['dias_mora'] > 90

vintage = df.groupby('cohorte').agg(
    total=('prestamo_id', 'count'),
    en_mora=('en_mora', 'sum'),
    en_npl=('en_npl', 'sum'),
    monto_total=('monto_original', 'sum'),
).reset_index()

vintage['tasa_mora'] = vintage['en_mora'] / vintage['total']
vintage['tasa_npl'] = vintage['en_npl'] / vintage['total']

print("=" * 65)
print("VINTAGE ANALYSIS — Banco Río Digital")
print("=" * 65)
print("\nTasa de mora y NPL por cohorte de originación (trimestre):")
print(vintage[['cohorte', 'total', 'en_mora', 'tasa_mora', 'tasa_npl']].to_string(index=False))

# ¿Tendencia? Comparamos la primera mitad de cohortes contra la segunda mitad.
n = len(vintage)
mitad = n // 2
tasa_mora_primera_mitad = vintage.iloc[:mitad]['tasa_mora'].mean()
tasa_mora_segunda_mitad = vintage.iloc[mitad:]['tasa_mora'].mean()
tendencia = "EMPEORANDO" if tasa_mora_segunda_mitad > tasa_mora_primera_mitad else "MEJORANDO/ESTABLE"

print(f"\nTasa de mora promedio — cohortes más antiguas: {tasa_mora_primera_mitad*100:.2f}%")
print(f"Tasa de mora promedio — cohortes más recientes: {tasa_mora_segunda_mitad*100:.2f}%")
print(f"Lectura de calidad de originación reciente: {tendencia}")

# ============================================================
# VISUALIZACIÓN
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].bar(vintage['cohorte'].astype(str), vintage['tasa_mora'] * 100, color='steelblue')
axes[0].set_xlabel('Cohorte de originación')
axes[0].set_ylabel('Tasa de mora (%)')
axes[0].set_title('Vintage Analysis — Tasa de mora por cohorte')
axes[0].tick_params(axis='x', rotation=45)

axes[1].bar(vintage['cohorte'].astype(str), vintage['tasa_npl'] * 100, color='indianred')
axes[1].set_xlabel('Cohorte de originación')
axes[1].set_ylabel('Tasa de NPL >90d (%)')
axes[1].set_title('Vintage Analysis — Tasa de NPL por cohorte')
axes[1].tick_params(axis='x', rotation=45)

plt.suptitle('Banco Río Digital — Calidad de originación por cosecha')
plt.tight_layout()
png_path = os.path.join(OUT_DIR, 'vintage_analysis.png')
plt.savefig(png_path, dpi=150)
print(f"\nGráfico guardado en: {png_path}")

vintage.to_csv(os.path.join(OUT_DIR, 'vintage_analysis.csv'), index=False)
print(f"Datos guardados en: {os.path.join(OUT_DIR, 'vintage_analysis.csv')}")
