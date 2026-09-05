"""
Módulo 05 — Motor de scoring y decisión crediticia
Contiene toda la lógica de negocio (sin FastAPI), para que se pueda probar
y reusar de forma independiente de la API. `api.py` es una capa delgada
que solo expone estas funciones por HTTP.

Diferencia deliberada respecto al instructivo original: en vez de pedirle
al solicitante que "auto-reporte" su propio score y su mora (lo cual sería
un control de seguridad inaceptable en un banco real — el cliente nunca
debería poder declarar su propio riesgo), el motor CONSULTA el perfil de
riesgo del cliente directamente en la base del Módulo 01 a partir de su
`cliente_id`. Solo se le pide al llamador lo que un banco no puede conocer
de antemano: el monto solicitado, el ingreso declarado y el plazo.
"""

import json
import math
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '01_data_infrastructure', 'data', 'processed', 'banco_rio_digital.db')
REGLAS_PATH = os.path.join(BASE_DIR, 'decision_rules.json')

with open(REGLAS_PATH, 'r', encoding='utf-8') as f:
    REGLAS = json.load(f)

TIPOS_PRESTAMO_VALIDOS = list(REGLAS['lgd_por_tipo'].keys())


# ============================================================
# EXCEPCIONES DE DOMINIO
# ============================================================
class ClienteNoEncontrado(Exception):
    pass


class TipoPrestamoInvalido(Exception):
    pass


# ============================================================
# ACCESO A DATOS: perfil de riesgo del cliente
# ============================================================
@dataclass
class PerfilCliente:
    cliente_id: int
    nombre: str
    score: int
    segmento_cliente: str
    dias_mora_actual: int
    defaults_historicos: int


def obtener_perfil_cliente(cliente_id: int) -> PerfilCliente:
    """
    Consulta el score vigente del cliente y reconstruye su historial de
    riesgo a partir de la tabla `prestamos`:
      - dias_mora_actual: el máximo dias_mora entre sus préstamos VIGENTES
        (un cliente sin préstamos activos en mora tiene 0).
      - defaults_historicos: cantidad de préstamos que en algún momento
        llegaron a MORA_90 o INCOBRABLE (el mismo criterio de "default"
        usado en el Módulo 02).
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cliente = conn.execute(
            "SELECT cliente_id, nombre, score_inicial, segmento FROM clientes WHERE cliente_id = ?",
            (cliente_id,)
        ).fetchone()
        if cliente is None:
            raise ClienteNoEncontrado(f"No existe un cliente con cliente_id={cliente_id}")

        mora_actual = conn.execute(
            "SELECT COALESCE(MAX(dias_mora), 0) FROM prestamos "
            "WHERE cliente_id = ? AND estado NOT IN ('CANCELADO')",
            (cliente_id,)
        ).fetchone()[0]

        defaults = conn.execute(
            "SELECT COUNT(*) FROM prestamos WHERE cliente_id = ? AND estado IN ('MORA_90', 'INCOBRABLE')",
            (cliente_id,)
        ).fetchone()[0]
    finally:
        conn.close()

    return PerfilCliente(
        cliente_id=cliente[0], nombre=cliente[1], score=cliente[2], segmento_cliente=cliente[3],
        dias_mora_actual=mora_actual, defaults_historicos=defaults,
    )


# ============================================================
# PD, SEGMENTO Y LGD (reutilizan las MISMAS fórmulas del Módulo 01/02)
# ============================================================
def calcular_pd(score: int) -> float:
    """Misma función logística que calcular_pd_score() en generate_synthetic_data.py."""
    c = REGLAS['curva_pd']
    exponente = (score - c['score_mid']) / c['escala']
    return c['pd_min'] + (c['pd_max'] - c['pd_min']) / (1 + math.exp(exponente))


def calcular_segmento_score(score: int) -> str:
    bins = REGLAS['segmentacion_score']['bins']
    labels = REGLAS['segmentacion_score']['labels']
    for i in range(len(bins) - 1):
        if bins[i] < score <= bins[i + 1]:
            return labels[i]
    return labels[0] if score <= bins[0] else labels[-1]


def obtener_lgd(tipo_prestamo: str) -> float:
    if tipo_prestamo not in REGLAS['lgd_por_tipo']:
        raise TipoPrestamoInvalido(
            f"Tipo de préstamo '{tipo_prestamo}' inválido. Opciones: {TIPOS_PRESTAMO_VALIDOS}"
        )
    return REGLAS['lgd_por_tipo'][tipo_prestamo]


# ============================================================
# PRICING BASADO EN RIESGO
# ============================================================
def calcular_tasa_anual(score: int, tipo_prestamo: str) -> dict:
    """
    tasa_anual = tasa_libre_riesgo + (PD × LGD) + margen_operativo

    La prima de riesgo es, literalmente, la Expected Loss (PD×LGD) del
    Módulo 02 expresada como una tasa — el mismo concepto de "pérdida
    esperada por unidad de exposición" que ya se calculó ahí, ahora usado
    para fijar el precio de un préstamo NUEVO en vez de medir la pérdida
    de una cartera existente.
    """
    pd = calcular_pd(score)
    lgd = obtener_lgd(tipo_prestamo)
    prima_riesgo = pd * lgd
    pricing = REGLAS['pricing']
    tasa = pricing['tasa_libre_riesgo'] + prima_riesgo + pricing['margen_operativo']
    return {
        'pd': round(pd, 4),
        'lgd': lgd,
        'prima_riesgo': round(prima_riesgo, 4),
        'tasa_anual': round(tasa, 4),
    }


def calcular_cuota_frances(monto: float, tasa_anual: float, cuotas: int) -> float:
    """Sistema francés (cuota fija): la fórmula estándar de amortización de préstamos."""
    tasa_mensual = tasa_anual / 12
    if tasa_mensual == 0:
        return round(monto / cuotas, 2)
    cuota = monto * (tasa_mensual * (1 + tasa_mensual) ** cuotas) / ((1 + tasa_mensual) ** cuotas - 1)
    return round(cuota, 2)


def monto_maximo_por_capacidad_pago(cuota_maxima: float, tasa_anual: float, cuotas: int) -> float:
    """Inversa de calcular_cuota_frances: dado el máximo que el cliente puede pagar
    de cuota, ¿cuál es el monto máximo que se le puede otorgar?"""
    tasa_mensual = tasa_anual / 12
    if tasa_mensual == 0:
        return round(cuota_maxima * cuotas, 2)
    monto = cuota_maxima * ((1 + tasa_mensual) ** cuotas - 1) / (tasa_mensual * (1 + tasa_mensual) ** cuotas)
    return round(monto, 2)


# ============================================================
# EVALUACIÓN DE REGLAS (rechazo / aprobación automática)
# ============================================================
OPERADORES = {
    '<': lambda a, b: a < b,
    '<=': lambda a, b: a <= b,
    '>': lambda a, b: a > b,
    '>=': lambda a, b: a >= b,
    '=': lambda a, b: a == b,
    '!=': lambda a, b: a != b,
}


def _evaluar_reglas(perfil: PerfilCliente, reglas: list) -> Optional[dict]:
    """Devuelve la PRIMERA regla que se cumple, o None si ninguna aplica."""
    valores = {'score': perfil.score, 'dias_mora_actual': perfil.dias_mora_actual,
               'defaults_historicos': perfil.defaults_historicos}
    for regla in reglas:
        valor_actual = valores[regla['campo']]
        operador = OPERADORES[regla['operador']]
        if operador(valor_actual, regla['valor']):
            return regla
    return None


# ============================================================
# ORQUESTACIÓN: EVALUAR UNA SOLICITUD DE CRÉDITO COMPLETA
# ============================================================
@dataclass
class DecisionCredito:
    cliente_id: int
    nombre: str
    decision: str            # APROBADO, RECHAZADO, REVISION_MANUAL
    motivo: str
    score: int
    segmento_score: str
    pd: float
    lgd: float
    tasa_anual: float
    monto_solicitado: float
    monto_aprobado: float
    cuotas: int
    cuota_mensual: float
    relacion_cuota_ingreso: Optional[float] = None


def evaluar_credito(cliente_id: int, monto_solicitado: float, cuotas: int,
                     ingreso_mensual: float, tipo_prestamo: str) -> DecisionCredito:
    perfil = obtener_perfil_cliente(cliente_id)
    segmento_score = calcular_segmento_score(perfil.score)

    # 1) Reglas de rechazo automático — la primera que se cumpla, rechaza.
    regla_rechazo = _evaluar_reglas(perfil, REGLAS['reglas_rechazo_automatico'])
    if regla_rechazo:
        pricing = calcular_tasa_anual(perfil.score, tipo_prestamo)
        return DecisionCredito(
            cliente_id=cliente_id, nombre=perfil.nombre, decision='RECHAZADO',
            motivo=regla_rechazo['descripcion'], score=perfil.score, segmento_score=segmento_score,
            pd=pricing['pd'], lgd=pricing['lgd'], tasa_anual=pricing['tasa_anual'],
            monto_solicitado=monto_solicitado, monto_aprobado=0.0, cuotas=cuotas, cuota_mensual=0.0,
        )

    # 2) Pricing basado en riesgo (PD del score actual × LGD del tipo de préstamo)
    pricing = calcular_tasa_anual(perfil.score, tipo_prestamo)
    tasa_anual = pricing['tasa_anual']
    cuota = calcular_cuota_frances(monto_solicitado, tasa_anual, cuotas)
    relacion_ci = cuota / ingreso_mensual

    # 3) Chequeo de capacidad de pago (DTI — debt-to-income)
    dti_max = REGLAS['relacion_cuota_ingreso_max']
    if relacion_ci > dti_max:
        monto_maximo = monto_maximo_por_capacidad_pago(ingreso_mensual * dti_max, tasa_anual, cuotas)
        cuota_ajustada = ingreso_mensual * dti_max
        # Si el monto máximo que puede pagar es razonablemente cercano a lo
        # pedido (>=50%), se aprueba ese monto ajustado; si no, revisión manual.
        if monto_maximo >= monto_solicitado * 0.50:
            return DecisionCredito(
                cliente_id=cliente_id, nombre=perfil.nombre, decision='APROBADO',
                motivo=f"Monto ajustado por capacidad de pago (relación cuota/ingreso máxima: {dti_max:.0%})",
                score=perfil.score, segmento_score=segmento_score,
                pd=pricing['pd'], lgd=pricing['lgd'], tasa_anual=tasa_anual,
                monto_solicitado=monto_solicitado, monto_aprobado=round(monto_maximo, 2),
                cuotas=cuotas, cuota_mensual=round(cuota_ajustada, 2), relacion_cuota_ingreso=dti_max,
            )
        else:
            return DecisionCredito(
                cliente_id=cliente_id, nombre=perfil.nombre, decision='REVISION_MANUAL',
                motivo=f"Capacidad de pago insuficiente para el monto solicitado "
                       f"(relación cuota/ingreso: {relacion_ci:.0%}, máximo: {dti_max:.0%})",
                score=perfil.score, segmento_score=segmento_score,
                pd=pricing['pd'], lgd=pricing['lgd'], tasa_anual=tasa_anual,
                monto_solicitado=monto_solicitado, monto_aprobado=0.0,
                cuotas=cuotas, cuota_mensual=cuota, relacion_cuota_ingreso=round(relacion_ci, 4),
            )

    # 4) Aprobación directa (capacidad de pago OK)
    regla_aprobacion = _evaluar_reglas(perfil, REGLAS['reglas_aprobacion_automatica'])
    motivo = (
        f"Aprobación automática — {regla_aprobacion['descripcion']}" if regla_aprobacion
        else f"Aprobado — segmento {segmento_score}, capacidad de pago dentro de política"
    )
    return DecisionCredito(
        cliente_id=cliente_id, nombre=perfil.nombre, decision='APROBADO', motivo=motivo,
        score=perfil.score, segmento_score=segmento_score,
        pd=pricing['pd'], lgd=pricing['lgd'], tasa_anual=tasa_anual,
        monto_solicitado=monto_solicitado, monto_aprobado=monto_solicitado,
        cuotas=cuotas, cuota_mensual=cuota, relacion_cuota_ingreso=round(relacion_ci, 4),
    )
