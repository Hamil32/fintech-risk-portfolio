"""
Módulo 01 — ETL Pipeline
Extrae de banco_rio_digital.db, transforma (tipado, columnas derivadas,
agregados por cliente) y carga vistas curadas en data/processed/ listas
para ser consumidas por los módulos 02-06 y por Power BI.
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'banco_rio_digital.db')
OUT_DIR = os.path.join(BASE_DIR, 'data', 'processed')


def extract():
    conn = sqlite3.connect(DB_PATH)
    tablas = {
        'clientes': pd.read_sql('SELECT * FROM clientes', conn),
        'cuentas': pd.read_sql('SELECT * FROM cuentas', conn),
        'transacciones': pd.read_sql('SELECT * FROM transacciones', conn, parse_dates=['fecha']),
        'prestamos': pd.read_sql('SELECT * FROM prestamos', conn,
                                  parse_dates=['fecha_otorgamiento', 'fecha_vencimiento']),
        'scoring_historico': pd.read_sql('SELECT * FROM scoring_historico', conn, parse_dates=['fecha']),
    }
    conn.close()
    return tablas


def transform(tablas):
    clientes = tablas['clientes'].copy()
    cuentas = tablas['cuentas'].copy()
    transacciones = tablas['transacciones'].copy()
    prestamos = tablas['prestamos'].copy()

    # --- Columnas derivadas de transacciones ---
    transacciones['anio_mes'] = transacciones['fecha'].dt.to_period('M').astype(str)
    transacciones['hora'] = transacciones['fecha'].dt.hour
    transacciones['es_horario_habil'] = transacciones['hora'].between(8, 20)

    # --- Columnas derivadas de préstamos ---
    prestamos['en_mora'] = prestamos['dias_mora'] > 0
    prestamos['es_npl'] = prestamos['dias_mora'] > 90  # Non-Performing Loan

    # --- Vista 360: un registro por cliente con agregados de todas las tablas ---
    saldo_por_cliente = cuentas.groupby('cliente_id')['saldo'].sum().rename('saldo_total')

    tx_agg = transacciones.groupby('cliente_id').agg(
        tx_total=('transaccion_id', 'count'),
        tx_monto_total=('monto', 'sum'),
        tx_fraude_count=('es_fraude', 'sum'),
    )

    prestamo_agg = prestamos.groupby('cliente_id').agg(
        prestamos_total=('prestamo_id', 'count'),
        deuda_pendiente=('monto_pendiente', 'sum'),
        prestamos_en_mora=('en_mora', 'sum'),
        prestamos_npl=('es_npl', 'sum'),
    )

    vista_360 = (
        clientes.set_index('cliente_id')
        .join(saldo_por_cliente, how='left')
        .join(tx_agg, how='left')
        .join(prestamo_agg, how='left')
        .reset_index()
    )

    # Clientes sin transacciones/préstamos -> completar con 0 en vez de NaN
    cols_fill_zero = ['saldo_total', 'tx_total', 'tx_monto_total', 'tx_fraude_count',
                       'prestamos_total', 'deuda_pendiente', 'prestamos_en_mora', 'prestamos_npl']
    vista_360[cols_fill_zero] = vista_360[cols_fill_zero].fillna(0)

    return {
        'transacciones_curadas': transacciones,
        'prestamos_curados': prestamos,
        'vista_360_cliente': vista_360,
    }


def load(curadas):
    os.makedirs(OUT_DIR, exist_ok=True)
    for nombre, df in curadas.items():
        path = os.path.join(OUT_DIR, f'{nombre}.csv')
        df.to_csv(path, index=False)
        print(f"   -> {nombre}: {len(df):,} filas -> {path}")


def main():
    print("=" * 60)
    print("ETL PIPELINE — Banco Río Digital")
    print("=" * 60)

    print("\n[1/3] Extract: leyendo tablas desde SQLite...")
    tablas = extract()
    for nombre, df in tablas.items():
        print(f"   -> {nombre}: {len(df):,} filas")

    print("\n[2/3] Transform: derivando columnas y construyendo vista_360_cliente...")
    curadas = transform(tablas)

    print("\n[3/3] Load: exportando vistas curadas a data/processed/...")
    load(curadas)

    print("\n" + "=" * 60)
    print("ETL completado exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    main()
