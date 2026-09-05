"""
Módulo 04 — Generador de Reportes de Operación Sospechosa (ROS)
Un ROS es el documento que un sujeto obligado (banco) presenta a la UIF
cuando detecta una operación que no puede justificar con el perfil
transaccional conocido del cliente. Este script toma las alertas de
nivel ALTO (aml_rule_engine.py) y genera un borrador de ROS por caso,
en el formato narrativo estándar que usa un analista de compliance.

⚠️ Esto es un BORRADOR automático para acelerar el trabajo del analista,
no un reemplazo del criterio profesional ni del circuito de aprobación
interno que todo ROS real requiere antes de presentarse a la UIF.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

DESCRIPCION_TIPOLOGIA = {
    'STRUCTURING': (
        'Fraccionamiento de operaciones (Structuring/Smurfing): el cliente realizó múltiples '
        'transacciones de bajo monto el mismo día, cada una por debajo del umbral de reporte, '
        'cuya suma agregada sí superaría dicho umbral.'
    ),
    'ROUND_TRIPPING': (
        'Circuito de ida y vuelta (Round-tripping): se identificó una cadena de transferencias '
        'entre 3 clientes que retorna al originante en una ventana de tiempo corta, con montos '
        'decrecientes consistentes con comisiones del circuito — patrón típico de intento de '
        'ocultamiento del origen de los fondos.'
    ),
    'ACTIVIDAD_INUSUAL': (
        'Actividad inusual: el volumen transaccional mensual del cliente se apartó '
        'significativamente (más de 3 desvíos estándar) de su comportamiento histórico, sin '
        'una justificación de negocio evidente en el perfil declarado.'
    ),
    'CASH_INTENSIVE': (
        'Actividad intensiva en efectivo: se detectó una concentración inusual de extracciones '
        'de efectivo en una ventana de 30 días, en volumen y frecuencia no consistentes con el '
        'perfil transaccional habitual del cliente.'
    ),
}

conn = sqlite3.connect(DB_PATH)
clientes = pd.read_sql('SELECT * FROM clientes', conn)
conn.close()

ruta_alertas = os.path.join(OUT_DIR, 'aml_alertas.csv')
if not os.path.exists(ruta_alertas):
    raise SystemExit("Falta output/aml_alertas.csv. Corré primero: python aml_rule_engine.py")

alertas = pd.read_csv(ruta_alertas)
casos_altos = alertas[alertas['nivel_riesgo'] == 'ALTO'].sort_values(['cliente_id', 'fecha_deteccion'])

print("=" * 65)
print("GENERADOR DE ROS (Reporte de Operación Sospechosa) — Borradores")
print("=" * 65)
print(f"\nCasos de riesgo ALTO a documentar: {len(casos_altos)}")

lineas = [
    "# Borradores de ROS — Banco Río Digital",
    f"\n*Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')} — "
    "requiere revisión y aprobación de Compliance antes de su presentación a la UIF.*\n",
    "---\n",
]

for n, (_, caso) in enumerate(casos_altos.iterrows(), start=1):
    cliente = clientes[clientes['cliente_id'] == caso['cliente_id']].iloc[0]
    tipologia_desc = DESCRIPCION_TIPOLOGIA.get(caso['tipologia'], caso['tipologia'])

    lineas.append(f"## ROS Borrador N° {n:03d} — Caso {caso['tipologia']}")
    lineas.append("")
    lineas.append("**1. Identificación del sujeto reportado**")
    lineas.append(f"- Cliente ID: {cliente['cliente_id']}")
    lineas.append(f"- Nombre: {cliente['nombre']}")
    lineas.append(f"- DNI: {cliente['dni']}")
    lineas.append(f"- Segmento: {cliente['segmento']}")
    lineas.append(f"- Provincia: {cliente['provincia']}")
    lineas.append(f"- Score crediticio: {cliente['score_inicial']}")
    lineas.append("")
    lineas.append("**2. Tipología GAFI/UIF aplicable**")
    lineas.append(f"- {caso['tipologia']}: {tipologia_desc}")
    lineas.append("")
    lineas.append("**3. Descripción de la operación detectada**")
    lineas.append(f"- {caso['descripcion']}")
    lineas.append(f"- Fecha de detección: {caso['fecha_deteccion']}")
    lineas.append("")
    lineas.append("**4. Fundamento de la sospecha**")
    lineas.append(
        "- El patrón detectado no es consistente con el perfil transaccional declarado del "
        "cliente y coincide con una tipología conocida de lavado de activos según los "
        "estándares GAFI."
    )
    lineas.append("")
    lineas.append("**5. Recomendación**")
    lineas.append(
        "- Elevar a Compliance para revisión manual, solicitar documentación respaldatoria "
        "adicional al cliente, y evaluar la presentación formal de ROS ante la UIF según "
        "corresponda tras la revisión."
    )
    lineas.append("\n---\n")

reporte = "\n".join(lineas)
ruta_salida = os.path.join(OUT_DIR, 'ros_borradores.md')
with open(ruta_salida, 'w', encoding='utf-8') as f:
    f.write(reporte)

# Índice tabular de los casos, para el dashboard/seguimiento de compliance
casos_altos.to_csv(os.path.join(OUT_DIR, 'ros_indice_casos.csv'), index=False)

print(f"\nBorradores de ROS guardados en: {ruta_salida}")
print(f"Índice de casos guardado en: {os.path.join(OUT_DIR, 'ros_indice_casos.csv')}")
