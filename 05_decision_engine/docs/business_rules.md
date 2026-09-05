# Reglas de Negocio — Motor de Decisión Crediticia

Documento de referencia de negocio (no técnico) sobre cómo decide el motor. Todas las reglas viven en [`../decision_rules.json`](../decision_rules.json) — este documento las explica en lenguaje simple.

## Flujo de decisión

```
1. Se consulta el perfil de riesgo del cliente (score, mora activa, defaults históricos)
        ↓
2. ¿Cumple alguna regla de RECHAZO AUTOMÁTICO?
        SÍ → RECHAZADO (fin)
        NO → sigue
        ↓
3. Se calcula el pricing basado en riesgo: tasa = tasa base + (PD × LGD) + margen
        ↓
4. Se calcula la cuota mensual (sistema francés) para el monto y plazo solicitados
        ↓
5. ¿La cuota supera el 40% del ingreso declarado?
        SÍ → ¿el monto máximo que sí puede pagar es al menos el 50% de lo pedido?
              SÍ → APROBADO (monto ajustado)
              NO → REVISIÓN MANUAL
        NO → APROBADO (monto pleno)
```

## 1. Reglas de rechazo automático

| Regla | Por qué existe |
|---|---|
| Score < 400 (segmento E) | Política de admisión: no se otorga crédito a clientes en el segmento de mayor riesgo |
| Mora activa > 90 días (NPL) | Un cliente en incumplimiento activo no puede tomar deuda nueva |
| Más de 1 default histórico | Historial de incumplimiento reiterado — riesgo de recurrencia |

## 2. Pricing basado en riesgo

```
tasa_anual = tasa_libre_riesgo + (PD × LGD) + margen_operativo
```

- **`tasa_libre_riesgo`** (40% 🟨 ilustrativo): representa el costo de fondeo del banco — a qué tasa el banco consigue el dinero que después presta. En un contexto real se referenciaría contra una tasa de mercado vigente (ej. BADLAR, tasa de política monetaria), que en Argentina es altamente volátil — el valor acá es una aproximación de orden de magnitud, no una tasa vigente a una fecha específica.
- **`PD × LGD`** (la prima de riesgo): es literalmente la **Expected Loss** del Módulo 02, expresada como tasa en vez de como monto. Un cliente con más riesgo de no pagar (PD alta) y/o un producto con menos garantía (LGD alto) paga una tasa más alta — es el mismo principio que "a mayor riesgo, mayor prima" de cualquier seguro.
- **`margen_operativo`** (5% 🟨 ilustrativo): cubre costos operativos y margen de rentabilidad del banco.

⚠️ **Simplificación reconocida:** un pricing de Basilea "completo" también debería cubrir un cargo de capital por la **pérdida NO esperada** (Unexpected Loss) — el capital que el banco debe inmovilizar como colchón regulatorio. Este motor solo cubre la pérdida esperada; se omite el cargo de capital por simplicidad.

## 3. Capacidad de pago (DTI — Debt to Income)

- Umbral: la cuota mensual no puede superar el **40%** del ingreso mensual declarado (🟨 valor ilustrativo, práctica común en la industria pero no una cifra normativa fija).
- Si se supera: se recalcula el **monto máximo** que sí respeta ese 40%, usando la fórmula inversa de amortización francesa.
- Si ese monto máximo cubre al menos el 50% de lo solicitado, se aprueba ese monto reducido.
- Si no, el caso pasa a **revisión manual** (el sistema no rechaza directamente casos "límite" — los deriva a un analista humano).

## 4. Reglas de aprobación automática

Un cliente en **segmento A** (score ≥ 700) **sin mora activa** que además pasa el chequeo de capacidad de pago, se aprueba de forma 100% automática, sin pasar por revisión.

## Glosario rápido

| Término | Significado |
|---|---|
| PD | Probabilidad de Default — ver Módulo 02 |
| LGD | Loss Given Default — % que se pierde si el cliente no paga |
| DTI | Debt-to-Income — relación entre la cuota y el ingreso del solicitante |
| Sistema francés | Método de amortización de cuota fija (la cuota no cambia mes a mes, varía la proporción interés/capital) |
