# Módulo 05 — Decision Engine

**Objetivo:** una API REST que evalúa solicitudes de crédito en tiempo real, consultando el riesgo real del cliente (Módulo 01) y aplicando pricing basado en riesgo (PD × LGD, Módulos 01/02) en vez de una tabla de tasas fija.

> 📘 Ver la explicación completa de las fórmulas y decisiones de diseño en [`../BITACORA_TECNICA.md`](../BITACORA_TECNICA.md#7-módulo-05--decision-engine).
> 📖 Ver [`docs/business_rules.md`](docs/business_rules.md) para las reglas de negocio y [`docs/api_documentation.md`](docs/api_documentation.md) para el detalle de la API.

## Requisito previo

```bash
cd ../01_data_infrastructure
python generate_synthetic_data.py
```

## Cómo correr este módulo

```bash
cd 05_decision_engine

# Levantar la API
uvicorn api:app --reload
# -> http://127.0.0.1:8000        (health check)
# -> http://127.0.0.1:8000/docs   (documentación interactiva Swagger)

# Correr los tests (en otra terminal, no requiere el server levantado)
pytest test_api.py -v
```

## Diferencia clave respecto al instructivo original

El instructivo pedía que el solicitante **auto-reporte** su propio score y mora en el request — un control de seguridad inaceptable en un banco real (nadie puede declarar su propio riesgo). Este motor en cambio recibe solo `cliente_id` + los datos que el banco *no puede conocer de antemano* (monto, plazo, ingreso), y **consulta** el score/mora/defaults directamente en la base del Módulo 01.

## Archivos

| Archivo | Rol |
|---|---|
| `decision_rules.json` | Reglas de negocio y parámetros de pricing, externalizados (reutiliza la curva de PD del Módulo 01 y el LGD del Módulo 02) |
| `scoring_engine.py` | Toda la lógica de negocio: perfil de riesgo, PD, pricing, cuota (sistema francés), reglas de rechazo/aprobación, DTI |
| `api.py` | Capa FastAPI: expone `scoring_engine.py` por HTTP |
| `test_api.py` | 11 tests con `TestClient`, usando clientes reales buscados dinámicamente en la base |
| `docs/business_rules.md` | Reglas de negocio explicadas para una audiencia no técnica |
| `docs/api_documentation.md` | Documentación de los 3 endpoints con ejemplos `curl` |

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/decision-rules` | Expone la configuración de reglas vigente |
| `GET` | `/clientes/{cliente_id}/perfil-riesgo` | Perfil de riesgo de un cliente (score, PD, mora, defaults) |
| `POST` | `/evaluar-credito` | Evalúa una solicitud de crédito completa |

## Fórmula de pricing (el corazón del módulo)

```
tasa_anual = tasa_libre_riesgo + (PD × LGD) + margen_operativo
```

La prima de riesgo (`PD × LGD`) es literalmente la Expected Loss del Módulo 02, ahora usada para **fijar precio a un préstamo nuevo** en vez de medir la pérdida de una cartera existente — el mismo concepto, aplicado en el otro extremo del ciclo de vida del crédito (originación vs. monitoreo).

## Resultado de esta corrida

11/11 tests pasan, cubriendo: aprobación automática, rechazo por score bajo, rechazo por mora NPL, ajuste de monto por capacidad de pago, revisión manual, cliente inexistente (404), tipo de préstamo inválido (422), y que el pricing efectivamente cobre más a peor score.
