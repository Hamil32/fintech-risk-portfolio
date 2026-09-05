"""
Módulo 02 — Roll Rate Matrix
Mide qué porcentaje de clientes "migra" de un segmento de riesgo a otro
de un período al siguiente (ej: cuántos de los que estaban en B pasan
a C, cuántos mejoran a A, cuántos se mantienen).

⚠️ Nota metodológica: el roll rate clásico de la industria se calcula
sobre buckets de MORA de un préstamo específico (0 días -> 30 -> 60 -> 90)
mes a mes. Este dataset no tiene un historial mensual de mora por
préstamo, pero sí tiene un historial TRIMESTRAL del segmento de riesgo
(A-E) de cada CLIENTE en `scoring_historico`. Aplicamos el mismo
concepto (una matriz de transición de Markov de primer orden) sobre esa
serie: es un "roll rate de score/segmento de riesgo" en vez de un roll
rate de mora de un préstamo puntual. La lógica y la lectura de negocio
son las mismas: cuantifica el flujo de clientes hacia mejor o peor
riesgo entre dos períodos consecutivos.
"""

import os
import sqlite3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

ORDEN_SEGMENTOS = ['A', 'B', 'C', 'D', 'E']  # de mejor a peor riesgo

conn = sqlite3.connect(DB_PATH)
scoring = pd.read_sql('SELECT * FROM scoring_historico', conn, parse_dates=['fecha'])
conn.close()

scoring = scoring.sort_values(['cliente_id', 'fecha'])
scoring['periodo'] = scoring['fecha'].dt.to_period('Q')
periodos = sorted(scoring['periodo'].unique())

print("=" * 65)
print("ROLL RATE MATRIX — Migración de segmento de riesgo (A-E)")
print("=" * 65)
print(f"\nPeríodos disponibles: {[str(p) for p in periodos]}")

# ============================================================
# Construir, para cada cliente, la secuencia de segmentos por período
# ============================================================
pivot = scoring.pivot_table(index='cliente_id', columns='periodo', values='segmento_riesgo', aggfunc='first')

# ============================================================
# Matriz de transición promedio entre períodos consecutivos
# ============================================================
matrices = []
for i in range(len(periodos) - 1):
    p_actual, p_siguiente = periodos[i], periodos[i + 1]
    pares = pivot[[p_actual, p_siguiente]].dropna()
    pares.columns = ['desde', 'hacia']

    matriz_conteo = pd.crosstab(pares['desde'], pares['hacia'])
    matriz_conteo = matriz_conteo.reindex(index=ORDEN_SEGMENTOS, columns=ORDEN_SEGMENTOS, fill_value=0)
    matriz_pct = matriz_conteo.div(matriz_conteo.sum(axis=1), axis=0).fillna(0)
    matrices.append(matriz_pct)

    print(f"\nTransición {p_actual} -> {p_siguiente}  (% de clientes que estaban en 'desde')")
    print((matriz_pct * 100).round(1).to_string())

# Matriz promedio a lo largo de todos los trimestres: la "matriz de roll rate" resumen
matriz_promedio = sum(matrices) / len(matrices)

print("\n" + "-" * 65)
print("MATRIZ DE ROLL RATE PROMEDIO (todos los trimestres)")
print("Filas = segmento de origen | Columnas = segmento de destino | valores en %")
print("-" * 65)
print((matriz_promedio * 100).round(1).to_string())

# ============================================================
# Métricas resumen: % que mejora, empeora o se mantiene
# ============================================================
idx_map = {s: i for i, s in enumerate(ORDEN_SEGMENTOS)}
pct_estable, pct_mejora, pct_empeora = 0.0, 0.0, 0.0
for origen in ORDEN_SEGMENTOS:
    for destino in ORDEN_SEGMENTOS:
        valor = matriz_promedio.loc[origen, destino] / len(ORDEN_SEGMENTOS)  # peso igual por fila
        if idx_map[destino] == idx_map[origen]:
            pct_estable += matriz_promedio.loc[origen, destino]
        elif idx_map[destino] > idx_map[origen]:
            pct_empeora += matriz_promedio.loc[origen, destino]
        else:
            pct_mejora += matriz_promedio.loc[origen, destino]

n_filas = len(ORDEN_SEGMENTOS)
print(f"\nResumen (promedio simple entre segmentos de origen):")
print(f"   Se mantiene en el mismo segmento: {pct_estable/n_filas*100:.1f}%")
print(f"   Mejora de segmento (roll-back):   {pct_mejora/n_filas*100:.1f}%")
print(f"   Empeora de segmento (roll-forward): {pct_empeora/n_filas*100:.1f}%")

# ============================================================
# VISUALIZACIÓN (heatmap manual con matplotlib, sin seaborn)
# ============================================================
fig, ax = plt.subplots(figsize=(6.5, 5.5))
im = ax.imshow(matriz_promedio.values * 100, cmap='RdYlGn_r', vmin=0, vmax=100)

ax.set_xticks(range(n_filas))
ax.set_xticklabels(ORDEN_SEGMENTOS)
ax.set_yticks(range(n_filas))
ax.set_yticklabels(ORDEN_SEGMENTOS)
ax.set_xlabel('Segmento de destino (t+1)')
ax.set_ylabel('Segmento de origen (t)')
ax.set_title('Roll Rate Matrix promedio — Banco Río Digital\n(% de clientes que migran de segmento por trimestre)')

for i in range(n_filas):
    for j in range(n_filas):
        valor = matriz_promedio.values[i, j] * 100
        color = 'white' if valor > 50 else 'black'
        ax.text(j, i, f"{valor:.1f}%", ha='center', va='center', color=color, fontsize=9)

fig.colorbar(im, ax=ax, label='% de clientes')
plt.tight_layout()
png_path = os.path.join(OUT_DIR, 'roll_rate_matrix.png')
plt.savefig(png_path, dpi=150)
print(f"\nHeatmap guardado en: {png_path}")

matriz_promedio.to_csv(os.path.join(OUT_DIR, 'roll_rate_matrix.csv'))
print(f"Matriz guardada en: {os.path.join(OUT_DIR, 'roll_rate_matrix.csv')}")
