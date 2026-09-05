"""
Módulo 05 — Motor de Decisión Crediticia — API REST
Capa delgada sobre scoring_engine.py: expone la lógica de negocio por
HTTP, valida el request/response con Pydantic, y traduce las excepciones
de dominio a códigos de estado HTTP apropiados.
"""

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import scoring_engine as se

app = FastAPI(
    title="Banco Río Digital — Motor de Decisión Crediticia",
    description=(
        "API para evaluación automática de solicitudes de crédito. "
        "Consulta el perfil de riesgo del cliente en la base del Módulo 01 "
        "y aplica pricing basado en riesgo (PD × LGD) del Módulo 02."
    ),
    version="1.0.0",
)


class SolicitudCredito(BaseModel):
    cliente_id: int = Field(..., description="ID del cliente en la base de Banco Río Digital", gt=0)
    monto_solicitado: float = Field(..., description="Monto solicitado en ARS", gt=0)
    cuotas: int = Field(..., description="Cantidad de cuotas mensuales", gt=0, le=240)
    ingreso_mensual: float = Field(..., description="Ingreso mensual declarado en ARS", gt=0)
    tipo_prestamo: Literal["PERSONAL", "HIPOTECARIO", "PRENDARIO"]

    model_config = {
        "json_schema_extra": {
            "example": {
                "cliente_id": 14,
                "monto_solicitado": 500000,
                "cuotas": 12,
                "ingreso_mensual": 300000,
                "tipo_prestamo": "PERSONAL",
            }
        }
    }


class DecisionCreditoResponse(BaseModel):
    cliente_id: int
    nombre: str
    decision: Literal["APROBADO", "RECHAZADO", "REVISION_MANUAL"]
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


class PerfilRiesgoResponse(BaseModel):
    cliente_id: int
    nombre: str
    score: int
    segmento_score: str
    segmento_cliente: str
    pd: float
    dias_mora_actual: int
    defaults_historicos: int


@app.get("/", tags=["Salud"])
def health_check():
    return {"status": "OK", "servicio": "Motor de Decisión Crediticia v1.0"}


@app.get("/decision-rules", tags=["Configuración"])
def obtener_reglas_vigentes():
    """Expone las reglas de negocio actualmente configuradas — transparencia
    y auditabilidad: cualquiera puede ver bajo qué criterios se decide."""
    return se.REGLAS


@app.get("/clientes/{cliente_id}/perfil-riesgo", response_model=PerfilRiesgoResponse, tags=["Clientes"])
def obtener_perfil_riesgo(cliente_id: int):
    """Consulta el perfil de riesgo de un cliente sin evaluar ninguna solicitud —
    útil para que un oficial de crédito revise el caso antes de una decisión."""
    try:
        perfil = se.obtener_perfil_cliente(cliente_id)
    except se.ClienteNoEncontrado as e:
        raise HTTPException(status_code=404, detail=str(e))

    segmento = se.calcular_segmento_score(perfil.score)
    pd = se.calcular_pd(perfil.score)

    return PerfilRiesgoResponse(
        cliente_id=perfil.cliente_id, nombre=perfil.nombre, score=perfil.score,
        segmento_score=segmento, segmento_cliente=perfil.segmento_cliente, pd=round(pd, 4),
        dias_mora_actual=perfil.dias_mora_actual, defaults_historicos=perfil.defaults_historicos,
    )


@app.post("/evaluar-credito", response_model=DecisionCreditoResponse, tags=["Decisión"])
def evaluar_credito(solicitud: SolicitudCredito):
    """Evalúa una solicitud de crédito: consulta el riesgo del cliente,
    aplica reglas de rechazo/aprobación automática, calcula pricing basado
    en riesgo y valida la capacidad de pago (DTI)."""
    try:
        decision = se.evaluar_credito(
            cliente_id=solicitud.cliente_id,
            monto_solicitado=solicitud.monto_solicitado,
            cuotas=solicitud.cuotas,
            ingreso_mensual=solicitud.ingreso_mensual,
            tipo_prestamo=solicitud.tipo_prestamo,
        )
    except se.ClienteNoEncontrado as e:
        raise HTTPException(status_code=404, detail=str(e))
    except se.TipoPrestamoInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))

    return DecisionCreditoResponse(**decision.__dict__)
