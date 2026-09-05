-- ============================================================
-- Módulo 02 — Vintage Analysis en SQL puro
-- Motor: SQLite (banco_rio_digital.db)
-- ============================================================

-- 1) Vintage por trimestre de originación: tasa de mora y NPL por cohorte
SELECT
    strftime('%Y', p.fecha_otorgamiento) || '-Q' ||
        ((CAST(strftime('%m', p.fecha_otorgamiento) AS INTEGER) - 1) / 3 + 1)   AS cohorte,
    COUNT(*)                                                                    AS total_prestamos,
    SUM(CASE WHEN p.dias_mora > 0 THEN 1 ELSE 0 END)                            AS en_mora,
    SUM(CASE WHEN p.dias_mora > 90 THEN 1 ELSE 0 END)                           AS en_npl,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 0 THEN 1 ELSE 0 END) / COUNT(*), 2)  AS tasa_mora_pct,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 90 THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_npl_pct,
    SUM(p.monto_original)                                                       AS monto_originado
FROM prestamos p
GROUP BY cohorte
ORDER BY cohorte;

-- 2) Vintage cruzado por cohorte y tipo de préstamo — para detectar si el
--    deterioro de calidad viene de un producto específico
SELECT
    strftime('%Y', p.fecha_otorgamiento) || '-Q' ||
        ((CAST(strftime('%m', p.fecha_otorgamiento) AS INTEGER) - 1) / 3 + 1)   AS cohorte,
    p.tipo,
    COUNT(*)                                                                    AS total_prestamos,
    ROUND(100.0 * SUM(CASE WHEN p.dias_mora > 0 THEN 1 ELSE 0 END) / COUNT(*), 2)  AS tasa_mora_pct
FROM prestamos p
GROUP BY cohorte, p.tipo
ORDER BY cohorte, p.tipo;

-- 3) Comparación cohortes antiguas vs. recientes (mitad y mitad) —
--    responde: "¿la originación reciente es de peor calidad?"
WITH cohortes AS (
    SELECT
        p.prestamo_id,
        p.dias_mora,
        strftime('%Y', p.fecha_otorgamiento) || '-Q' ||
            ((CAST(strftime('%m', p.fecha_otorgamiento) AS INTEGER) - 1) / 3 + 1) AS cohorte
    FROM prestamos p
),
cohortes_ordenadas AS (
    SELECT DISTINCT cohorte FROM cohortes ORDER BY cohorte
),
con_orden AS (
    SELECT cohorte, ROW_NUMBER() OVER (ORDER BY cohorte) AS rn, COUNT(*) OVER () AS total_cohortes
    FROM cohortes_ordenadas
)
SELECT
    CASE WHEN co.rn <= co.total_cohortes / 2 THEN 'Cohortes antiguas' ELSE 'Cohortes recientes' END AS grupo,
    COUNT(*)                                                                    AS total_prestamos,
    ROUND(100.0 * SUM(CASE WHEN c.dias_mora > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS tasa_mora_pct
FROM cohortes c
JOIN con_orden co ON co.cohorte = c.cohorte
GROUP BY grupo;
