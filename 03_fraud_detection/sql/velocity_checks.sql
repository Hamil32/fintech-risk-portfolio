-- ============================================================
-- Módulo 03 — Velocity checks en SQL puro
-- Motor: SQLite (banco_rio_digital.db)
--
-- SQLite no soporta ventanas de tiempo (RANGE BETWEEN INTERVAL) en sus
-- funciones de ventana, así que el "más de 5 transacciones en 1 hora" se
-- resuelve con un self-join: por cada transacción, se cuentan las
-- transacciones DEL MISMO CLIENTE ocurridas en la hora previa (incluida
-- ella misma). Es más lento que un rolling window de pandas para datasets
-- grandes, pero es la forma correcta de expresarlo en SQL estándar.
-- ============================================================

-- Índice recomendado antes de correr esta consulta sobre datasets grandes:
CREATE INDEX IF NOT EXISTS idx_transacciones_cliente_fecha ON transacciones(cliente_id, fecha);

-- 1) Transacciones con más de 5 operaciones del mismo cliente en la última hora
SELECT
    t1.transaccion_id,
    t1.cliente_id,
    t1.fecha,
    t1.monto,
    t1.canal,
    t1.es_fraude,
    COUNT(t2.transaccion_id)                                        AS transacciones_ultima_hora
FROM transacciones t1
JOIN transacciones t2
    ON t2.cliente_id = t1.cliente_id
   AND t2.fecha <= t1.fecha
   AND t2.fecha > datetime(t1.fecha, '-1 hours')
GROUP BY t1.transaccion_id, t1.cliente_id, t1.fecha, t1.monto, t1.canal, t1.es_fraude
HAVING COUNT(t2.transaccion_id) > 5
ORDER BY transacciones_ultima_hora DESC, t1.fecha;

-- 2) Validación del velocity check contra el ground truth: ¿cuántas de las
--    transacciones marcadas por esta regla son fraude real?
WITH velocity AS (
    SELECT
        t1.transaccion_id,
        t1.es_fraude,
        COUNT(t2.transaccion_id) AS transacciones_ultima_hora
    FROM transacciones t1
    JOIN transacciones t2
        ON t2.cliente_id = t1.cliente_id
       AND t2.fecha <= t1.fecha
       AND t2.fecha > datetime(t1.fecha, '-1 hours')
    GROUP BY t1.transaccion_id, t1.es_fraude
)
SELECT
    COUNT(*)                                                        AS total_marcadas,
    SUM(es_fraude)                                                  AS fraudes_reales,
    ROUND(100.0 * SUM(es_fraude) / COUNT(*), 2)                     AS precision_pct
FROM velocity
WHERE transacciones_ultima_hora > 5;

-- 3) Clientes con más ráfagas de actividad (agrupando por día, para no
--    tener que materializar el self-join completo sobre todo el dataset)
SELECT
    cliente_id,
    date(fecha)                                                     AS dia,
    COUNT(*)                                                        AS transacciones_en_el_dia
FROM transacciones
GROUP BY cliente_id, dia
HAVING COUNT(*) >= 5
ORDER BY transacciones_en_el_dia DESC
LIMIT 20;
