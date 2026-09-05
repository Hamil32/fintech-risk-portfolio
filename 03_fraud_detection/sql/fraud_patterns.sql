-- ============================================================
-- Módulo 03 — Patrones de fraude
-- Motor: SQLite (banco_rio_digital.db)
-- ============================================================

-- 1) Tasa de fraude por canal y franja horaria
SELECT
    canal,
    CAST(strftime('%H', fecha) AS INTEGER)                          AS hora,
    COUNT(*)                                                        AS total,
    SUM(es_fraude)                                                  AS fraudes,
    ROUND(100.0 * SUM(es_fraude) / COUNT(*), 2)                     AS tasa_fraude_pct
FROM transacciones
GROUP BY canal, hora
HAVING total >= 20
ORDER BY tasa_fraude_pct DESC
LIMIT 20;

-- 2) Comparación de monto: fraude vs. legítimo
SELECT
    CASE WHEN es_fraude = 1 THEN 'FRAUDE' ELSE 'LEGÍTIMA' END       AS tipo,
    COUNT(*)                                                        AS total,
    ROUND(AVG(monto), 2)                                            AS monto_promedio,
    ROUND(MIN(monto), 2)                                            AS monto_min,
    ROUND(MAX(monto), 2)                                            AS monto_max
FROM transacciones
GROUP BY es_fraude;

-- 3) Tasa de fraude por tipo de transacción
SELECT
    tipo,
    COUNT(*)                                                        AS total,
    SUM(es_fraude)                                                  AS fraudes,
    ROUND(100.0 * SUM(es_fraude) / COUNT(*), 2)                     AS tasa_pct
FROM transacciones
GROUP BY tipo
ORDER BY tasa_pct DESC;

-- 4) Clientes con más de una transacción fraudulenta (posible cuenta comprometida)
SELECT
    cliente_id,
    COUNT(*)                                                        AS transacciones_fraudulentas,
    SUM(monto)                                                      AS monto_total_fraude,
    MIN(fecha)                                                      AS primera_deteccion,
    MAX(fecha)                                                      AS ultima_deteccion
FROM transacciones
WHERE es_fraude = 1
GROUP BY cliente_id
HAVING COUNT(*) > 1
ORDER BY transacciones_fraudulentas DESC, monto_total_fraude DESC;

-- 5) Evolución mensual de la tasa de fraude (para el dashboard de fraude)
SELECT
    strftime('%Y-%m', fecha)                                        AS anio_mes,
    COUNT(*)                                                        AS total,
    SUM(es_fraude)                                                  AS fraudes,
    ROUND(100.0 * SUM(es_fraude) / COUNT(*), 3)                     AS tasa_fraude_pct
FROM transacciones
GROUP BY anio_mes
ORDER BY anio_mes;
