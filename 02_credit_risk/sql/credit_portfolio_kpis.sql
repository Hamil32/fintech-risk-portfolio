-- ============================================================
-- Módulo 02 — KPIs de cartera de crédito
-- Motor: SQLite (banco_rio_digital.db)
-- ============================================================

-- 1) KPIs generales de la cartera
SELECT
    COUNT(*)                                                   AS total_prestamos,
    SUM(monto_original)                                        AS monto_originado_total,
    SUM(monto_pendiente)                                       AS cartera_vigente_total,
    ROUND(100.0 * SUM(CASE WHEN dias_mora > 90 THEN monto_pendiente ELSE 0 END)
          / SUM(monto_pendiente), 2)                           AS tasa_npl_pct,
    ROUND(100.0 * SUM(CASE WHEN dias_mora > 0 THEN monto_pendiente ELSE 0 END)
          / SUM(monto_pendiente), 2)                           AS tasa_mora_total_pct,
    ROUND(AVG(tasa_anual) * 100, 2)                             AS tasa_anual_promedio_pct
FROM prestamos;

-- 2) Distribución de cartera por estado (vigente, mora, cancelado, incobrable)
SELECT
    estado,
    COUNT(*)                                            AS cantidad_prestamos,
    SUM(monto_pendiente)                                AS monto_pendiente_total,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM prestamos), 2)          AS pct_cantidad,
    ROUND(100.0 * SUM(monto_pendiente) /
          (SELECT SUM(monto_pendiente) FROM prestamos), 2)                AS pct_monto
FROM prestamos
GROUP BY estado
ORDER BY monto_pendiente_total DESC;

-- 3) Distribución de cartera por tipo de préstamo
SELECT
    tipo,
    COUNT(*)                                            AS cantidad_prestamos,
    SUM(monto_original)                                 AS monto_originado,
    SUM(monto_pendiente)                                AS monto_pendiente,
    ROUND(AVG(tasa_anual) * 100, 2)                     AS tasa_promedio_pct,
    ROUND(100.0 * SUM(CASE WHEN dias_mora > 90 THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_npl_pct
FROM prestamos
GROUP BY tipo
ORDER BY monto_pendiente DESC;

-- 4) Top 10 clientes por exposición crediticia (para la tabla del dashboard ejecutivo)
SELECT
    c.cliente_id,
    c.nombre,
    c.segmento,
    c.score_inicial,
    COUNT(p.prestamo_id)           AS cantidad_prestamos,
    SUM(p.monto_pendiente)         AS exposicion_total,
    MAX(p.dias_mora)               AS max_dias_mora
FROM clientes c
JOIN prestamos p ON p.cliente_id = c.cliente_id
GROUP BY c.cliente_id, c.nombre, c.segmento, c.score_inicial
ORDER BY exposicion_total DESC
LIMIT 10;

-- 5) Cartera y NPL por segmento de cliente (RETAIL / PYME / CORPORATIVO)
SELECT
    c.segmento,
    COUNT(p.prestamo_id)                                            AS cantidad_prestamos,
    SUM(p.monto_pendiente)                                          AS cartera,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 90 THEN p.monto_pendiente ELSE 0 END)
          / SUM(p.monto_pendiente), 2)                              AS tasa_npl_pct
FROM clientes c
JOIN prestamos p ON p.cliente_id = c.cliente_id
GROUP BY c.segmento
ORDER BY cartera DESC;
