"""
Módulo 05 — Tests de la API del motor de decisión
Usa el TestClient de FastAPI (sobre httpx), que llama a la app en proceso
sin necesidad de levantar un servidor real — estándar para testear APIs
FastAPI.

Los clientes usados en cada test se buscan dinámicamente en la base (no
se hardcodea un cliente_id fijo), para que los tests sigan siendo válidos
si el dataset sintético se regenera.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

import scoring_engine as se
from api import app

client = TestClient(app)


def _buscar_cliente(condicion_sql: str):
    """Helper: devuelve el primer cliente_id que cumple una condición SQL."""
    conn = sqlite3.connect(se.DB_PATH)
    try:
        fila = conn.execute(condicion_sql).fetchone()
    finally:
        conn.close()
    if fila is None:
        pytest.skip("No se encontró un cliente que cumpla la condición para este test en el dataset actual")
    return fila[0]


@pytest.fixture(scope="module")
def cliente_score_alto_sin_mora():
    return _buscar_cliente(
        "SELECT c.cliente_id FROM clientes c "
        "WHERE c.score_inicial >= 750 "
        "AND c.cliente_id NOT IN (SELECT cliente_id FROM prestamos WHERE estado NOT IN ('CANCELADO')) "
        "LIMIT 1"
    )


@pytest.fixture(scope="module")
def cliente_score_bajo():
    return _buscar_cliente("SELECT cliente_id FROM clientes WHERE score_inicial < 400 LIMIT 1")


@pytest.fixture(scope="module")
def cliente_con_mora_npl():
    return _buscar_cliente("SELECT cliente_id FROM prestamos WHERE dias_mora > 90 LIMIT 1")


# ============================================================
# TESTS
# ============================================================
def test_health_check():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"


def test_decision_rules_expone_configuracion():
    resp = client.get("/decision-rules")
    assert resp.status_code == 200
    body = resp.json()
    assert "reglas_rechazo_automatico" in body
    assert "curva_pd" in body


def test_perfil_riesgo_cliente_inexistente_devuelve_404():
    resp = client.get("/clientes/999999999/perfil-riesgo")
    assert resp.status_code == 404


def test_perfil_riesgo_cliente_existente(cliente_score_alto_sin_mora):
    resp = client.get(f"/clientes/{cliente_score_alto_sin_mora}/perfil-riesgo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["cliente_id"] == cliente_score_alto_sin_mora
    assert 0 <= body["pd"] <= 1
    assert body["dias_mora_actual"] == 0


def test_evaluar_credito_cliente_inexistente_devuelve_404():
    resp = client.post("/evaluar-credito", json={
        "cliente_id": 999999999, "monto_solicitado": 100000, "cuotas": 12,
        "ingreso_mensual": 100000, "tipo_prestamo": "PERSONAL",
    })
    assert resp.status_code == 404


def test_evaluar_credito_tipo_prestamo_invalido_devuelve_422():
    resp = client.post("/evaluar-credito", json={
        "cliente_id": 1, "monto_solicitado": 100000, "cuotas": 12,
        "ingreso_mensual": 100000, "tipo_prestamo": "CRIPTO",  # no es un tipo válido
    })
    assert resp.status_code == 422  # falla la validación de Pydantic (Literal)


def test_evaluar_credito_score_bajo_se_rechaza(cliente_score_bajo):
    resp = client.post("/evaluar-credito", json={
        "cliente_id": cliente_score_bajo, "monto_solicitado": 100000, "cuotas": 12,
        "ingreso_mensual": 150000, "tipo_prestamo": "PERSONAL",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "RECHAZADO"
    assert body["monto_aprobado"] == 0


def test_evaluar_credito_mora_npl_se_rechaza(cliente_con_mora_npl):
    resp = client.post("/evaluar-credito", json={
        "cliente_id": cliente_con_mora_npl, "monto_solicitado": 100000, "cuotas": 12,
        "ingreso_mensual": 150000, "tipo_prestamo": "PERSONAL",
    })
    assert resp.status_code == 200
    assert resp.json()["decision"] == "RECHAZADO"


def test_evaluar_credito_buen_cliente_capacidad_holgada_se_aprueba(cliente_score_alto_sin_mora):
    resp = client.post("/evaluar-credito", json={
        "cliente_id": cliente_score_alto_sin_mora, "monto_solicitado": 500000, "cuotas": 12,
        "ingreso_mensual": 500000, "tipo_prestamo": "PERSONAL",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "APROBADO"
    assert body["monto_aprobado"] == 500000
    assert body["cuota_mensual"] > 0
    assert 0 < body["relacion_cuota_ingreso"] <= 0.40


def test_evaluar_credito_ingreso_insuficiente_ajusta_o_revisa(cliente_score_alto_sin_mora):
    resp = client.post("/evaluar-credito", json={
        "cliente_id": cliente_score_alto_sin_mora, "monto_solicitado": 5_000_000, "cuotas": 12,
        "ingreso_mensual": 50000, "tipo_prestamo": "PERSONAL",
    })
    assert resp.status_code == 200
    body = resp.json()
    # Con un ingreso tan bajo frente a un monto tan alto, no puede salir
    # aprobado por el monto pleno solicitado.
    assert body["decision"] in ("APROBADO", "REVISION_MANUAL")
    if body["decision"] == "APROBADO":
        assert body["monto_aprobado"] < 5_000_000


def test_pricing_es_mayor_para_peor_score(cliente_score_alto_sin_mora, cliente_score_bajo):
    """A menor score, mayor PD, y por lo tanto mayor tasa (pricing basado en riesgo)."""
    perfil_bueno = se.obtener_perfil_cliente(cliente_score_alto_sin_mora)
    perfil_malo = se.obtener_perfil_cliente(cliente_score_bajo)

    tasa_bueno = se.calcular_tasa_anual(perfil_bueno.score, "PERSONAL")["tasa_anual"]
    tasa_malo = se.calcular_tasa_anual(perfil_malo.score, "PERSONAL")["tasa_anual"]

    assert tasa_malo > tasa_bueno
