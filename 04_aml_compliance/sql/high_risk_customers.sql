-- ============================================================
-- Módulo 04 — Identificación de clientes de alto riesgo AML en SQL puro
-- Motor: SQLite (banco_rio_digital.db)
-- Combina señales disponibles directamente en la base (sin depender de
-- las alertas ya calculadas en Python) para armar una primera lista de
-- clientes a revisar — el tipo de query que un analista de compliance
-- corre para un barrido periódico de cartera.
-- ============================================================

-- 1) Perfil de riesgo por cliente: volumen transaccional, cantidad de
--    cuentas, mora crediticia y segmento — señales combinadas típicas de
--    un scorecard KYC simplificado.
WITH volumen AS (
    SELECT cliente_id, COUNT(*) AS cantidad_tx, SUM(monto) AS volumen_total,
           SUM(CASE WHEN tipo = 'EXTRACCION' THEN monto ELSE 0 END) AS volumen_efectivo
    FROM transacciones
    GROUP BY cliente_id
),
cuentas_cliente AS (
    SELECT cliente_id, COUNT(*) AS n_cuentas
    FROM cuentas
    GROUP BY cliente_id
),
mora_cliente AS (
    SELECT cliente_id, MAX(dias_mora) AS max_dias_mora, SUM(CASE WHEN dias_mora > 90 THEN 1 ELSE 0 END) AS prestamos_npl
    FROM prestamos
    GROUP BY cliente_id
),
stats_segmento AS (
    SELECT c.segmento, AVG(v.volumen_total) AS volumen_medio, AVG(v.volumen_total * v.volumen_total) - AVG(v.volumen_total) * AVG(v.volumen_total) AS varianza
    FROM clientes c
    JOIN volumen v ON v.cliente_id = c.cliente_id
    GROUP BY c.segmento
)
SELECT
    c.cliente_id,
    c.nombre,
    c.segmento,
    c.provincia,
    c.score_inicial,
    COALESCE(cu.n_cuentas, 0)                                            AS n_cuentas,
    COALESCE(v.cantidad_tx, 0)                                           AS cantidad_tx,
    COALESCE(v.volumen_total, 0)                                         AS volumen_total,
    COALESCE(v.volumen_efectivo, 0)                                      AS volumen_efectivo,
    ROUND(COALESCE(v.volumen_efectivo, 0) * 1.0 / NULLIF(v.volumen_total, 0) * 100, 1) AS pct_efectivo,
    COALESCE(m.max_dias_mora, 0)                                         AS max_dias_mora,
    ROUND((COALESCE(v.volumen_total, 0) - ss.volumen_medio)
          / (SQRT(MAX(ss.varianza, 0)) + 1), 2)                          AS z_volumen_segmento,
    CASE
        WHEN c.segmento IN ('PYME', 'CORPORATIVO') AND COALESCE(cu.n_cuentas, 0) <= 1
             AND (COALESCE(v.volumen_total, 0) - ss.volumen_medio) / (SQRT(MAX(ss.varianza, 0)) + 1) > 2
            THEN 'ALTO'
        WHEN c.segmento IN ('PYME', 'CORPORATIVO')
             OR COALESCE(v.volumen_efectivo, 0) * 1.0 / NULLIF(v.volumen_total, 0) > 0.5
            THEN 'MEDIO'
        ELSE 'BAJO'
    END                                                                  AS calificacion_riesgo_preliminar
FROM clientes c
LEFT JOIN volumen v ON v.cliente_id = c.cliente_id
LEFT JOIN cuentas_cliente cu ON cu.cliente_id = c.cliente_id
LEFT JOIN mora_cliente m ON m.cliente_id = c.cliente_id
LEFT JOIN stats_segmento ss ON ss.segmento = c.segmento
ORDER BY
    CASE calificacion_riesgo_preliminar WHEN 'ALTO' THEN 1 WHEN 'MEDIO' THEN 2 ELSE 3 END,
    volumen_total DESC
LIMIT 100;
