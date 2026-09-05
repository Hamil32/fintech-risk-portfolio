"""
Módulo 04 — Validador KYC (Know Your Customer)
Antes de que un banco pueda operar con un cliente, debe "conocerlo":
verificar que sus datos sean completos y consistentes, y asignarle una
calificación de riesgo AML que determina cuánta supervisión recibe esa
relación (a mayor riesgo, más frecuente la revisión periódica).

Este script hace dos cosas:
  1. Validaciones de completitud/consistencia de datos (KYC "de formulario").
  2. Calificación de riesgo AML por cliente, combinando: segmento, alertas
     AML asociadas (de aml_rule_engine.py) y una señal de "huella chica,
     volumen grande" (proxy de empresa fachada).
"""

import os
import re
import sqlite3

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

PROVINCIAS_VALIDAS = {
    'CABA', 'Buenos Aires', 'Córdoba', 'Santa Fe', 'Mendoza',
    'Tucumán', 'Salta', 'Neuquén', 'Río Negro', 'Entre Ríos',
}
PATRON_DNI = re.compile(r'^\d{2}\.\d{3}\.\d{3}$')

conn = sqlite3.connect(DB_PATH)
clientes = pd.read_sql('SELECT * FROM clientes', conn)
cuentas = pd.read_sql('SELECT * FROM cuentas', conn)
transacciones = pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha'])
conn.close()

ruta_alertas = os.path.join(OUT_DIR, 'aml_alertas.csv')
alertas = pd.read_csv(ruta_alertas) if os.path.exists(ruta_alertas) else pd.DataFrame(
    columns=['cliente_id', 'tipologia', 'nivel_riesgo'])

print("=" * 65)
print("VALIDADOR KYC — Banco Río Digital")
print("=" * 65)

# ============================================================
# 1. VALIDACIONES DE COMPLETITUD / CONSISTENCIA (KYC "de formulario")
# ============================================================
clientes['kyc_dni_valido'] = clientes['dni'].apply(lambda d: bool(PATRON_DNI.match(str(d))))
clientes['kyc_edad_valida'] = clientes['edad'].between(18, 100)
clientes['kyc_provincia_valida'] = clientes['provincia'].isin(PROVINCIAS_VALIDAS)
clientes['kyc_score_valido'] = clientes['score_inicial'].between(300, 850)

clientes['kyc_completo'] = (
    clientes['kyc_dni_valido'] & clientes['kyc_edad_valida']
    & clientes['kyc_provincia_valida'] & clientes['kyc_score_valido']
)

n_incompletos = (~clientes['kyc_completo']).sum()
print(f"\n[1/2] Completitud de datos KYC:")
print(f"   Clientes con ficha KYC completa: {clientes['kyc_completo'].sum():,} / {len(clientes):,}")
print(f"   Clientes con datos incompletos/inconsistentes: {n_incompletos:,}")

# ============================================================
# 2. SEÑAL "HUELLA CHICA, VOLUMEN GRANDE" (proxy de empresa fachada)
# ============================================================
# Un cliente PYME/CORPORATIVO con muy pocas cuentas pero un volumen
# transaccional desproporcionadamente alto respecto a su propio segmento
# es una señal de alerta típica en AML: negocios de fachada suelen operar
# con una estructura societaria mínima pero mover mucho dinero.
volumen_cliente = transacciones.groupby('cliente_id')['monto'].sum().rename('volumen_total')
n_cuentas_cliente = cuentas.groupby('cliente_id').size().rename('n_cuentas')

perfil = clientes.merge(volumen_cliente, on='cliente_id', how='left').merge(
    n_cuentas_cliente, on='cliente_id', how='left')
perfil['volumen_total'] = perfil['volumen_total'].fillna(0)
perfil['n_cuentas'] = perfil['n_cuentas'].fillna(0)

# z-score del volumen DENTRO de cada segmento (comparar PYME contra PYME, no
# contra RETAIL, que tiene una escala de montos totalmente distinta)
stats_segmento = perfil.groupby('segmento')['volumen_total'].agg(['mean', 'std']).reset_index()
stats_segmento.columns = ['segmento', 'volumen_medio_segmento', 'volumen_std_segmento']
perfil = perfil.merge(stats_segmento, on='segmento')
perfil['z_volumen_segmento'] = (
    (perfil['volumen_total'] - perfil['volumen_medio_segmento'])
    / (perfil['volumen_std_segmento'].fillna(0) + 1)
)

perfil['flag_huella_chica_volumen_alto'] = (
    (perfil['n_cuentas'] <= 1) & (perfil['z_volumen_segmento'] > 2) &
    (perfil['segmento'].isin(['PYME', 'CORPORATIVO']))
).astype(int)

print(f"\n[2/2] Señal 'huella chica, volumen alto' (proxy de empresa fachada):")
print(f"   Clientes PYME/CORPORATIVO con 1 sola cuenta y volumen atípico para su segmento: "
      f"{perfil['flag_huella_chica_volumen_alto'].sum()}")

# ============================================================
# CALIFICACIÓN DE RIESGO AML POR CLIENTE
# ============================================================
alertas_por_cliente = alertas.groupby('cliente_id').agg(
    n_alertas=('tipologia', 'count'),
    tiene_alerta_alta=('nivel_riesgo', lambda s: (s == 'ALTO').any()),
).reset_index() if len(alertas) else pd.DataFrame(columns=['cliente_id', 'n_alertas', 'tiene_alerta_alta'])

perfil = perfil.merge(alertas_por_cliente, on='cliente_id', how='left')
perfil['n_alertas'] = perfil['n_alertas'].fillna(0)
perfil['tiene_alerta_alta'] = perfil['tiene_alerta_alta'].fillna(False)


def calificar_riesgo(row):
    """
    Calificación simple por reglas (en un banco real esto suele ser un
    scorecard KYC dedicado, con más variables — PEP, país de residencia,
    canal de alta, etc. — que no están disponibles en este dataset).
    """
    if row['tiene_alerta_alta'] or row['flag_huella_chica_volumen_alto']:
        return 'ALTO'
    if row['n_alertas'] > 0 or row['segmento'] in ('PYME', 'CORPORATIVO'):
        return 'MEDIO'
    return 'BAJO'


perfil['calificacion_riesgo_aml'] = perfil.apply(calificar_riesgo, axis=1)

print(f"\nDistribución de calificación de riesgo AML:")
print(perfil['calificacion_riesgo_aml'].value_counts().to_string())

# ============================================================
# GUARDAR RESULTADOS
# ============================================================
cols_salida = [
    'cliente_id', 'nombre', 'segmento', 'score_inicial', 'kyc_completo',
    'n_cuentas', 'volumen_total', 'z_volumen_segmento',
    'flag_huella_chica_volumen_alto', 'n_alertas', 'tiene_alerta_alta',
    'calificacion_riesgo_aml',
]
perfil[cols_salida].sort_values('calificacion_riesgo_aml').to_csv(
    os.path.join(OUT_DIR, 'kyc_customer_risk_rating.csv'), index=False)
print(f"\nArchivo guardado en: {os.path.join(OUT_DIR, 'kyc_customer_risk_rating.csv')}")
