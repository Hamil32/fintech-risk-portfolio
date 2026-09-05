"""
Módulo 01 — Validaciones de calidad de datos
Corre un set de chequeos sobre la base generada y reporta OK / WARNING / ERROR.
Pensado para correrse después de generate_synthetic_data.py y antes de
avanzar a los módulos de análisis.
"""

import os
import sqlite3
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'banco_rio_digital.db')

resultados = []  # (nivel, chequeo, detalle)


def check(nivel, nombre, condicion_ok, detalle=""):
    estado = "OK" if condicion_ok else nivel
    resultados.append((estado, nombre, detalle))


def main():
    if not os.path.exists(DB_PATH):
        print(f"No se encontró la base de datos en {DB_PATH}")
        print("Corré primero: python generate_synthetic_data.py")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    clientes = pd.read_sql('SELECT * FROM clientes', conn)
    cuentas = pd.read_sql('SELECT * FROM cuentas', conn)
    transacciones = pd.read_sql('SELECT * FROM transacciones', conn)
    prestamos = pd.read_sql('SELECT * FROM prestamos', conn)
    scoring = pd.read_sql('SELECT * FROM scoring_historico', conn)
    conn.close()

    print("=" * 60)
    print("DATA QUALITY CHECKS — Banco Río Digital")
    print("=" * 60)

    # --- Unicidad de claves primarias ---
    check("ERROR", "clientes.cliente_id sin duplicados",
          clientes['cliente_id'].is_unique)
    check("ERROR", "clientes.dni sin duplicados",
          clientes['dni'].is_unique)
    check("ERROR", "cuentas.cuenta_id sin duplicados",
          cuentas['cuenta_id'].is_unique)
    check("ERROR", "transacciones.transaccion_id sin duplicados",
          transacciones['transaccion_id'].is_unique)
    check("ERROR", "prestamos.prestamo_id sin duplicados",
          prestamos['prestamo_id'].is_unique)

    # --- Nulos en columnas críticas ---
    for df_name, df, cols in [
        ("clientes", clientes, ['cliente_id', 'dni', 'score_inicial']),
        ("cuentas", cuentas, ['cuenta_id', 'cliente_id', 'tipo_cuenta']),
        ("transacciones", transacciones, ['transaccion_id', 'cliente_id', 'monto', 'fecha']),
        ("prestamos", prestamos, ['prestamo_id', 'cliente_id', 'monto_original', 'estado']),
    ]:
        nulos = df[cols].isnull().sum().sum()
        check("ERROR", f"{df_name}: sin nulos en columnas críticas {cols}",
              nulos == 0, f"{nulos} nulos encontrados")

    # --- Integridad referencial ---
    clientes_validos = set(clientes['cliente_id'])
    check("ERROR", "cuentas.cliente_id referencia clientes existentes",
          set(cuentas['cliente_id']).issubset(clientes_validos))
    check("ERROR", "transacciones.cliente_id referencia clientes existentes",
          set(transacciones['cliente_id']).issubset(clientes_validos))
    check("ERROR", "transacciones.cuenta_id referencia cuentas existentes",
          set(transacciones['cuenta_id']).issubset(set(cuentas['cuenta_id'])))
    check("ERROR", "prestamos.cliente_id referencia clientes existentes",
          set(prestamos['cliente_id']).issubset(clientes_validos))
    check("ERROR", "scoring_historico.cliente_id referencia clientes existentes",
          set(scoring['cliente_id']).issubset(clientes_validos))

    # cuenta_destino_id / cliente_destino_id solo aplican a TRANSFERENCIA
    # (NULL en el resto) — se valida solo el subconjunto no nulo.
    destinos = transacciones.dropna(subset=['cliente_destino_id'])
    check("ERROR", "transacciones.cliente_destino_id (no nulo) referencia clientes existentes",
          set(destinos['cliente_destino_id']).issubset(clientes_validos))
    check("ERROR", "transacciones.cuenta_destino_id (no nulo) referencia cuentas existentes",
          set(destinos['cuenta_destino_id']).issubset(set(cuentas['cuenta_id'])))
    check("WARNING", "cuenta_destino_id/cliente_destino_id solo están presentes en TRANSFERENCIA",
          transacciones.loc[transacciones['tipo'] != 'TRANSFERENCIA', 'cliente_destino_id'].isna().all())

    # --- Rangos de negocio ---
    check("WARNING", "clientes.score_inicial en rango [300, 850]",
          clientes['score_inicial'].between(300, 850).all())
    check("WARNING", "clientes.edad en rango [18, 100]",
          clientes['edad'].between(18, 100).all())
    check("WARNING", "transacciones.monto > 0",
          (transacciones['monto'] > 0).all())
    check("WARNING", "prestamos.monto_pendiente <= monto_original",
          (prestamos['monto_pendiente'] <= prestamos['monto_original'] + 0.01).all())
    check("WARNING", "prestamos.cuotas_pagadas <= cuotas_total",
          (prestamos['cuotas_pagadas'] <= prestamos['cuotas_total']).all())

    # --- Consistencia estado / mora ---
    mora_map = {
        'VIGENTE': (0, 0), 'CANCELADO': (0, 0),
        'MORA_30': (1, 30), 'MORA_60': (31, 60),
        'MORA_90': (61, 90), 'INCOBRABLE': (91, 10_000),
    }
    inconsistentes = 0
    for estado, (lo, hi) in mora_map.items():
        sub = prestamos[prestamos['estado'] == estado]
        inconsistentes += ((sub['dias_mora'] < lo) | (sub['dias_mora'] > hi)).sum()
    check("ERROR", "prestamos.dias_mora coherente con prestamos.estado",
          inconsistentes == 0, f"{inconsistentes} filas inconsistentes")

    # --- Reporte final ---
    print(f"\n{'ESTADO':<8} {'CHEQUEO':<55} DETALLE")
    print("-" * 90)
    n_error, n_warning = 0, 0
    for estado, nombre, detalle in resultados:
        print(f"{estado:<8} {nombre:<55} {detalle}")
        if estado == "ERROR":
            n_error += 1
        elif estado == "WARNING":
            n_warning += 1

    print("\n" + "=" * 60)
    print(f"Total chequeos: {len(resultados)} | OK: {len(resultados) - n_error - n_warning} "
          f"| WARNING: {n_warning} | ERROR: {n_error}")
    print("=" * 60)

    if n_error > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
