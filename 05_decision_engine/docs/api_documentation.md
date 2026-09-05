# API Documentation — Motor de Decisión Crediticia

**Base URL (desarrollo local):** `http://127.0.0.1:8000`
**Documentación interactiva automática (Swagger):** `http://127.0.0.1:8000/docs`

## Cómo levantar la API

```bash
cd 05_decision_engine
uvicorn api:app --reload
```

## Endpoints

### `GET /`

Health check.

```bash
curl http://127.0.0.1:8000/
```

```json
{"status": "OK", "servicio": "Motor de Decisión Crediticia v1.0"}
```

---

### `GET /decision-rules`

Devuelve la configuración de reglas de negocio vigente (`decision_rules.json`) — transparencia y auditabilidad de bajo qué criterios se está decidiendo en este momento.

```bash
curl http://127.0.0.1:8000/decision-rules
```

---

### `GET /clientes/{cliente_id}/perfil-riesgo`

Consulta el perfil de riesgo de un cliente sin evaluar ninguna solicitud de crédito.

```bash
curl http://127.0.0.1:8000/clientes/14/perfil-riesgo
```

**Respuesta 200:**
```json
{
  "cliente_id": 14,
  "nombre": "Ema Rojas Gomez",
  "score": 791,
  "segmento_score": "A",
  "segmento_cliente": "CORPORATIVO",
  "pd": 0.0129,
  "dias_mora_actual": 0,
  "defaults_historicos": 0
}
```

**Respuesta 404** (cliente inexistente):
```json
{"detail": "No existe un cliente con cliente_id=999999"}
```

---

### `POST /evaluar-credito`

Evalúa una solicitud de crédito completa.

**Request body:**

| Campo | Tipo | Descripción |
|---|---|---|
| `cliente_id` | int | ID del cliente en la base de Banco Río Digital |
| `monto_solicitado` | float | Monto solicitado en ARS |
| `cuotas` | int | Cantidad de cuotas mensuales (1-240) |
| `ingreso_mensual` | float | Ingreso mensual declarado en ARS |
| `tipo_prestamo` | string | `PERSONAL`, `HIPOTECARIO` o `PRENDARIO` |

```bash
curl -X POST http://127.0.0.1:8000/evaluar-credito \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": 14,
    "monto_solicitado": 500000,
    "cuotas": 12,
    "ingreso_mensual": 300000,
    "tipo_prestamo": "PERSONAL"
  }'
```

**Respuesta 200 — Aprobado:**
```json
{
  "cliente_id": 14,
  "nombre": "Ema Rojas Gomez",
  "decision": "APROBADO",
  "motivo": "Aprobación automática — Score en segmento A (muy bajo riesgo)",
  "score": 791,
  "segmento_score": "A",
  "pd": 0.0129,
  "lgd": 0.75,
  "tasa_anual": 0.4597,
  "monto_solicitado": 500000.0,
  "monto_aprobado": 500000.0,
  "cuotas": 12,
  "cuota_mensual": 52754.47,
  "relacion_cuota_ingreso": 0.1758
}
```

**Posibles valores de `decision`:**

| Valor | Cuándo ocurre |
|---|---|
| `APROBADO` | Pasa las reglas de rechazo y la capacidad de pago es suficiente (monto pleno o ajustado) |
| `RECHAZADO` | Se cumple alguna regla de rechazo automático (score, mora, defaults) |
| `REVISION_MANUAL` | La capacidad de pago es tan baja que ni siquiera un monto reducido (≥50% de lo pedido) es viable — se deriva a un analista |

**Errores:**

| Código | Causa |
|---|---|
| `404` | `cliente_id` no existe en la base |
| `422` | `tipo_prestamo` no es uno de los valores válidos, o falta/tipo incorrecto algún campo del request |

## Notas de diseño

- El motor **no** le pide al solicitante que reporte su propio score o mora — los consulta directamente en la base del Módulo 01 a partir del `cliente_id`. Ver `../scoring_engine.py` para el detalle.
- La tasa de interés se calcula con pricing basado en riesgo (`PD × LGD` como prima de riesgo), reutilizando las mismas fórmulas del Módulo 01 (curva de PD) y del Módulo 02 (LGD por tipo de garantía) — ver `business_rules.md`.
