-- ============================================================
-- Módulo 02 — Segmentación de mora por score y por antigüedad de mora
-- Motor: SQLite (banco_rio_digital.db)
-- ============================================================

-- 1) PD histórica por segmento de score (A-E), replicando pd_lgd_ead.py en SQL puro
SELECT
    CASE
        WHEN c.score_inicial >= 700 THEN 'A (Muy bajo riesgo)'
        WHEN c.score_inicial >= 600 THEN 'B (Riesgo bajo)'
        WHEN c.score_inicial >= 500 THEN 'C (Riesgo medio)'
        WHEN c.score_inicial >= 400 THEN 'D (Alto riesgo)'
        ELSE 'E (Muy alto riesgo)'
    END                                                          AS segmento_score,
    COUNT(*)                                                     AS total_prestamos,
    SUM(CASE WHEN p.estado IN ('MORA_90', 'INCOBRABLE') THEN 1 ELSE 0 END)   AS defaults,
    ROUND(100.0 * SUM(CASE WHEN p.estado IN ('MORA_90', 'INCOBRABLE') THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                         AS pd_historica_pct,
    SUM(p.monto_original)                                        AS monto_total
FROM prestamos p
JOIN clientes c ON c.cliente_id = p.cliente_id
GROUP BY segmento_score
ORDER BY pd_historica_pct DESC;

-- 2) Bucket de días de mora (0 / 1-30 / 31-60 / 61-90 / +90) — la clasificación
--    estándar de mora usada en banca (umbrales alineados a Basilea/BCRA)
SELECT
    CASE
        WHEN p.dias_mora = 0 THEN '0 - Al día'
        WHEN p.dias_mora BETWEEN 1 AND 30 THEN '1-30 días'
        WHEN p.dias_mora BETWEEN 31 AND 60 THEN '31-60 días'
        WHEN p.dias_mora BETWEEN 61 AND 90 THEN '61-90 días'
        ELSE '+90 días (NPL)'
    END                                             AS bucket_mora,
    COUNT(*)                                        AS cantidad_prestamos,
    SUM(p.monto_pendiente)                          AS monto_pendiente,
    ROUND(100.0 * SUM(p.monto_pendiente) /
          (SELECT SUM(monto_pendiente) FROM prestamos), 2)   AS pct_de_cartera
FROM prestamos p
GROUP BY bucket_mora
ORDER BY MIN(p.dias_mora);

-- 3) Mora por tipo de préstamo y segmento de cliente cruzados
SELECT
    p.tipo,
    c.segmento,
    COUNT(*)                                                                AS cantidad,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 0 THEN 1 ELSE 0 END) / COUNT(*), 2)  AS tasa_mora_pct,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 90 THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_npl_pct
FROM prestamos p
JOIN clientes c ON c.cliente_id = p.cliente_id
GROUP BY p.tipo, c.segmento
ORDER BY p.tipo, tasa_npl_pct DESC;

-- 4) Evolución mensual de mora (para el gráfico de línea de tiempo del dashboard)
-- Nota: usa fecha_otorgamiento como proxy de línea temporal de la cartera
-- (el dataset no tiene un snapshot mensual de mora por préstamo).
SELECT
    strftime('%Y-%m', p.fecha_otorgamiento)         AS anio_mes,
    COUNT(*)                                        AS prestamos_otorgados,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_mora_pct
FROM prestamos p
GROUP BY anio_mes
ORDER BY anio_mes;
