"""
Módulo 06 — Consolidación del dataset para el Dashboard Ejecutivo
Junta las salidas de los Módulos 01-04 (que hoy viven repartidas en 4
carpetas distintas) en un set limpio de tablas tipo "estrella" (hechos +
dimensiones) en data/, listo para apuntar Power BI a UNA sola carpeta en
vez de cuatro.

⚠️ Requiere haber corrido antes, al menos una vez, los scripts de los
Módulos 01 a 04 (cada uno deja sus outputs en su propia carpeta output/).
Este script solo LEE esos outputs y los reorganiza — no recalcula nada.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE_DIR, '..')
OUT_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(OUT_DIR, exist_ok=True)

M1 = os.path.join(ROOT, '01_data_infrastructure', 'data', 'processed')
M2 = os.path.join(ROOT, '02_credit_risk', 'output')
M3 = os.path.join(ROOT, '03_fraud_detection', 'output')
M4 = os.path.join(ROOT, '04_aml_compliance', 'output')

REQUERIDOS = {
    'vista_360_cliente.csv': M1,
    'credit_risk_pd_lgd_ead.csv': M2,
    'scorecard_aplicado.csv': M2,
    'vintage_analysis.csv': M2,
    'roll_rate_matrix.csv': M2,
    'fraud_rules_output.csv': M3,
    'alert_queue.csv': M3,
    'aml_alertas.csv': M4,
    'kyc_customer_risk_rating.csv': M4,
}
faltantes = [f"{carpeta}/{archivo}" for archivo, carpeta in REQUERIDOS.items()
             if not os.path.exists(os.path.join(carpeta, archivo))]
if faltantes:
    print("Faltan estos archivos — corré primero los scripts de los Módulos 01-04:")
    for f in faltantes:
        print(f"   {f}")
    raise SystemExit(1)

print("=" * 65)
print("CONSOLIDACIÓN DEL DASHBOARD EJECUTIVO — Banco Río Digital")
print("=" * 65)

# ============================================================
# DIM_CLIENTES — vista 360 (Módulo 01) + calificación de riesgo AML (Módulo 04)
# ============================================================
vista_360 = pd.read_csv(os.path.join(M1, 'vista_360_cliente.csv'))
kyc = pd.read_csv(os.path.join(M4, 'kyc_customer_risk_rating.csv'))[
    ['cliente_id', 'n_alertas', 'tiene_alerta_alta', 'calificacion_riesgo_aml']
]

dim_clientes = vista_360.merge(kyc, on='cliente_id', how='left')
dim_clientes['n_alertas'] = dim_clientes['n_alertas'].fillna(0)
dim_clientes['tiene_alerta_alta'] = dim_clientes['tiene_alerta_alta'].fillna(False)
dim_clientes['calificacion_riesgo_aml'] = dim_clientes['calificacion_riesgo_aml'].fillna('BAJO')

dim_clientes.to_csv(os.path.join(OUT_DIR, 'dim_clientes.csv'), index=False)
print(f"\n[dim_clientes] {len(dim_clientes):,} filas -> dim_clientes.csv")

# ============================================================
# FACT_PRESTAMOS — PD/LGD/EAD/EL (Módulo 02) + score final del scorecard
# ============================================================
prestamos_riesgo = pd.read_csv(os.path.join(M2, 'credit_risk_pd_lgd_ead.csv'))
scorecard = pd.read_csv(os.path.join(M2, 'scorecard_aplicado.csv'))[['prestamo_id', 'score_final']]

fact_prestamos = prestamos_riesgo.merge(scorecard, on='prestamo_id', how='left')
fact_prestamos.to_csv(os.path.join(OUT_DIR, 'fact_prestamos.csv'), index=False)
print(f"[fact_prestamos] {len(fact_prestamos):,} filas -> fact_prestamos.csv")

# ============================================================
# FACT_TRANSACCIONES — reglas de fraude (Módulo 03, 100% de las tx) +
# prioridad de alerta / score del modelo (solo están en alert_queue las
# que dispararon alguna señal — el resto queda como "SIN ALERTA")
# ============================================================
reglas = pd.read_csv(os.path.join(M3, 'fraud_rules_output.csv'))
cola_alertas = pd.read_csv(os.path.join(M3, 'alert_queue.csv'))[
    ['transaccion_id', 'proba_modelo', 'if_anomalia', 'prioridad']
]

fact_transacciones = reglas.merge(cola_alertas, on='transaccion_id', how='left')
fact_transacciones['prioridad'] = fact_transacciones['prioridad'].fillna('SIN ALERTA')
fact_transacciones['if_anomalia'] = fact_transacciones['if_anomalia'].fillna(0)
fact_transacciones['proba_modelo'] = fact_transacciones['proba_modelo'].fillna(0)

fact_transacciones.to_csv(os.path.join(OUT_DIR, 'fact_transacciones.csv'), index=False)
print(f"[fact_transacciones] {len(fact_transacciones):,} filas -> fact_transacciones.csv")

# ============================================================
# DIM_VINTAGE — cohortes de originación (Módulo 02)
# ============================================================
vintage = pd.read_csv(os.path.join(M2, 'vintage_analysis.csv'))
vintage.to_csv(os.path.join(OUT_DIR, 'dim_vintage.csv'), index=False)
print(f"[dim_vintage] {len(vintage):,} filas -> dim_vintage.csv")

# ============================================================
# FACT_ROLL_RATE — matriz de transición (Módulo 02), en formato LARGO
# (desde, hacia, porcentaje) — el formato que necesita un visual Matrix
# de Power BI para pivotear correctamente.
# ============================================================
roll_rate_ancho = pd.read_csv(os.path.join(M2, 'roll_rate_matrix.csv'))
fact_roll_rate = roll_rate_ancho.melt(id_vars='desde', var_name='hacia', value_name='porcentaje')
fact_roll_rate.to_csv(os.path.join(OUT_DIR, 'fact_roll_rate.csv'), index=False)
print(f"[fact_roll_rate] {len(fact_roll_rate):,} filas -> fact_roll_rate.csv")

# ============================================================
# FACT_ALERTAS_AML — alertas por tipología (Módulo 04)
# ============================================================
aml = pd.read_csv(os.path.join(M4, 'aml_alertas.csv'))
aml.to_csv(os.path.join(OUT_DIR, 'fact_alertas_aml.csv'), index=False)
print(f"[fact_alertas_aml] {len(aml):,} filas -> fact_alertas_aml.csv")

print("\n" + "=" * 65)
print(f"Consolidación completa. Archivos en: {OUT_DIR}")
print("=" * 65)
print("\nApuntá Power BI Desktop a esta carpeta (Obtener datos > Carpeta,")
print("o Obtener datos > Texto/CSV archivo por archivo) y seguí")
print("power_bi_build_guide.md para armar las 4 páginas del dashboard.")
