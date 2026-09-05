-- ============================================================
-- Módulo 03 — Transacciones sospechosas (motor de reglas en SQL puro)
-- Motor: SQLite (banco_rio_digital.db)
-- Replica la lógica de rule_engine.py (reglas 2, 3 y 4) usando SQL puro.
-- La regla de velocity (1) está en velocity_checks.sql por separado, ya
-- que requiere un self-join distinto.
-- ============================================================

-- Estadísticas de monto por cliente (media y desvío estándar poblacional),
-- necesarias para el z-score de monto atípico.
WITH stats_cliente AS (
    SELECT
        cliente_id,
        AVG(monto)                                   AS monto_medio,
        SQRT(MAX(AVG(monto * monto) - AVG(monto) * AVG(monto), 0)) AS monto_std
    FROM transacciones
    GROUP BY cliente_id
),
flags AS (
    SELECT
        t.transaccion_id,
        t.cliente_id,
        t.fecha,
        t.monto,
        t.canal,
        t.es_fraude,
        CASE WHEN CAST(strftime('%H', t.fecha) AS INTEGER) BETWEEN 1 AND 5
             THEN 1 ELSE 0 END                                          AS flag_horario_sospechoso,
        CASE WHEN t.canal IN ('APP', 'HOME_BANKING') AND t.monto > 20000
             THEN 1 ELSE 0 END                                          AS flag_digital_monto_alto,
        CASE WHEN (t.monto - s.monto_medio) / (s.monto_std + 1) > 3
             THEN 1 ELSE 0 END                                          AS flag_monto_atipico
    FROM transacciones t
    JOIN stats_cliente s ON s.cliente_id = t.cliente_id
)
SELECT
    *,
    (flag_horario_sospechoso + flag_digital_monto_alto + flag_monto_atipico) AS score_reglas
FROM flags
WHERE (flag_horario_sospechoso + flag_digital_monto_alto + flag_monto_atipico) >= 2
ORDER BY score_reglas DESC, monto DESC;

-- Nota: esta consulta replica solo 3 de las 4 reglas de rule_engine.py
-- (sin velocity), por lo que sus totales y su precision/recall no son
-- directamente comparables 1 a 1 contra el resultado de Python — el
-- objetivo es mostrar la misma lógica de negocio expresada en SQL puro.
