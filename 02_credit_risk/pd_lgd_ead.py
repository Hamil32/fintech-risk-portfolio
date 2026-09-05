"""
Módulo 02 — Cálculo de PD, LGD, EAD y Expected Loss
Metodología: enfoque IRB (Internal Ratings-Based) de Basilea II.

EL (Expected Loss) = PD × LGD × EAD

- PD  (Probability of Default): probabilidad de que el cliente incumpla.
- LGD (Loss Given Default): % del monto expuesto que se pierde si incumple
  (depende del tipo de garantía del préstamo).
- EAD (Exposure at Default): monto expuesto al momento del default
  (acá, el saldo pendiente de pago).
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# CARGA DE DATOS
# ============================================================
conn = sqlite3.connect(DB_PATH)
prestamos = pd.read_sql('SELECT * FROM prestamos', conn)
clientes = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

df = prestamos.merge(clientes[['cliente_id', 'score_inicial', 'segmento']], on='cliente_id')

# ============================================================
# 1. PD (Probability of Default) — PD HISTÓRICA por segmento de score
# ============================================================
# Default = préstamo en MORA_90 (>90 días de atraso, umbral NPL de Basilea)
# o INCOBRABLE (ya dado de baja como pérdida).
df['es_default'] = df['estado'].isin(['MORA_90', 'INCOBRABLE']).astype(int)

bins = [0, 400, 500, 600, 700, 850]
labels = ['E (Muy alto riesgo)', 'D (Alto riesgo)', 'C (Riesgo medio)', 'B (Riesgo bajo)', 'A (Muy bajo riesgo)']
df['segmento_score'] = pd.cut(df['score_inicial'], bins=bins, labels=labels)

pd_por_segmento = df.groupby('segmento_score', observed=True).agg(
    total_prestamos=('es_default', 'count'),
    defaults=('es_default', 'sum'),
    pd_historica=('es_default', 'mean'),
    monto_total=('monto_original', 'sum')
).round(4)
pd_por_segmento['pd_porcentaje'] = (pd_por_segmento['pd_historica'] * 100).round(2)

print("=" * 65)
print("ANÁLISIS DE RIESGO CREDITICIO — Banco Río Digital")
print("=" * 65)
print("\n[PD] PROBABILIDAD DE DEFAULT HISTÓRICA POR SEGMENTO DE SCORE:")
print(pd_por_segmento[['total_prestamos', 'defaults', 'pd_porcentaje']].to_string())

# PD "asignada": la PD histórica observada en ESTE dataset por segmento se usa
# también como PD prospectiva para calcular el Expected Loss más abajo.
# (En un banco real, la PD asignada a cada segmento surge de un modelo de
# scoring validado y calibrado contra varios años de historia — acá usamos
# la PD histórica del propio dataset como proxy razonable.)
pd_map = pd_por_segmento['pd_historica'].to_dict()
# .map() sobre una columna Categorical (creada con pd.cut) puede devolver
# dtype "category" en vez de float — se fuerza a float explícitamente para
# poder operar aritméticamente (PD × LGD × EAD) más abajo.
df['pd_asignada'] = df['segmento_score'].map(pd_map).astype(float)

# ============================================================
# 2. LGD (Loss Given Default) — según tipo de garantía
# ============================================================
# A menor garantía real, mayor pérdida esperada si el cliente no paga.
# HIPOTECARIO: garantía real (el inmueble) -> recupero alto -> LGD bajo.
# PRENDARIO:   garantía real pero de menor valor de reventa (vehículo) -> LGD medio.
# PERSONAL:    sin garantía -> recupero bajo -> LGD alto.
LGD_POR_TIPO = {
    'HIPOTECARIO': 0.25,
    'PRENDARIO': 0.45,
    'PERSONAL': 0.75,
}
df['lgd'] = df['tipo'].map(LGD_POR_TIPO)

print("\n[LGD] LOSS GIVEN DEFAULT ASUMIDO POR TIPO DE GARANTÍA:")
for tipo, lgd in LGD_POR_TIPO.items():
    print(f"   {tipo:<12} LGD = {lgd:.0%}  (recupero estimado = {1 - lgd:.0%})")

# ============================================================
# 3. EAD (Exposure at Default)
# ============================================================
# Simplificación estándar en carteras de cuota fija: el EAD es el saldo
# pendiente de pago al momento del análisis (no el monto original).
df['ead'] = df['monto_pendiente']

# ============================================================
# 4. EXPECTED LOSS = PD × LGD × EAD
# ============================================================
df['expected_loss'] = df['pd_asignada'] * df['lgd'] * df['ead']

total_cartera = df['monto_pendiente'].sum()
total_el = df['expected_loss'].sum()
npl = df[df['dias_mora'] > 90]['monto_pendiente'].sum()
tasa_npl = npl / total_cartera

print("\n[KPIs] KPIs DE CARTERA:")
print(f"   Cartera total (EAD):        ${total_cartera:,.0f}")
print(f"   NPL (mora > 90 días):       ${npl:,.0f}  ({tasa_npl*100:.2f}% de la cartera)")
print(f"   Expected Loss total:        ${total_el:,.0f}  ({total_el/total_cartera*100:.2f}% de la cartera)")

# Expected Loss por segmento de score (para el gráfico de barras del dashboard)
el_por_segmento = df.groupby('segmento_score', observed=True).agg(
    expected_loss=('expected_loss', 'sum'),
    cartera=('monto_pendiente', 'sum'),
    n_prestamos=('prestamo_id', 'count'),
).round(2)
el_por_segmento['el_pct_cartera'] = (el_por_segmento['expected_loss'] / el_por_segmento['cartera'] * 100).round(2)

print("\n[EL] EXPECTED LOSS POR SEGMENTO DE SCORE:")
print(el_por_segmento.to_string())

# Expected Loss por tipo de préstamo
el_por_tipo = df.groupby('tipo').agg(
    expected_loss=('expected_loss', 'sum'),
    cartera=('monto_pendiente', 'sum'),
    lgd_asumido=('lgd', 'first'),
).round(2)
el_por_tipo['el_pct_cartera'] = (el_por_tipo['expected_loss'] / el_por_tipo['cartera'] * 100).round(2)

print("\n[EL] EXPECTED LOSS POR TIPO DE PRÉSTAMO:")
print(el_por_tipo.to_string())

# ============================================================
# GUARDAR RESULTADOS
# ============================================================
df.to_csv(os.path.join(OUT_DIR, 'credit_risk_pd_lgd_ead.csv'), index=False)
pd_por_segmento.to_csv(os.path.join(OUT_DIR, 'pd_por_segmento.csv'))
el_por_segmento.to_csv(os.path.join(OUT_DIR, 'expected_loss_por_segmento.csv'))
el_por_tipo.to_csv(os.path.join(OUT_DIR, 'expected_loss_por_tipo.csv'))

print(f"\nArchivos guardados en: {OUT_DIR}")
print("   - credit_risk_pd_lgd_ead.csv       (detalle por préstamo, para Power BI)")
print("   - pd_por_segmento.csv")
print("   - expected_loss_por_segmento.csv")
print("   - expected_loss_por_tipo.csv")
