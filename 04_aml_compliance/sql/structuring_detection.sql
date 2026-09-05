-- ============================================================
-- Módulo 04 — Detección de Structuring (fraccionamiento) en SQL puro
-- Motor: SQLite (banco_rio_digital.db)
-- Replica la lógica de aml_rule_engine.py: un mismo cliente con >= 5
-- transacciones por debajo del umbral reportable en un mismo día, cuya
-- suma sí sería reportable.
-- ============================================================

-- Umbral de reporte (🟨 ilustrativo, no un valor normativo real)
-- Se repite como literal en la consulta porque SQLite no soporta variables.

-- 1) Casos de structuring detectados
SELECT
    cliente_id,
    date(fecha)                                    AS dia,
    COUNT(*)                                        AS cantidad_transacciones,
    SUM(monto)                                      AS monto_total_dia,
    ROUND(AVG(monto), 2)                            AS monto_promedio
FROM transacciones
WHERE monto < 10000
GROUP BY cliente_id, dia
HAVING COUNT(*) >= 5 AND SUM(monto) > 10000
ORDER BY monto_total_dia DESC;

-- 2) Mismo resultado, enriquecido con datos del cliente (para un analista)
SELECT
    s.cliente_id,
    c.nombre,
    c.segmento,
    s.dia,
    s.cantidad_transacciones,
    s.monto_total_dia
FROM (
    SELECT cliente_id, date(fecha) AS dia, COUNT(*) AS cantidad_transacciones, SUM(monto) AS monto_total_dia
    FROM transacciones
    WHERE monto < 10000
    GROUP BY cliente_id, dia
    HAVING COUNT(*) >= 5 AND SUM(monto) > 10000
) s
JOIN clientes c ON c.cliente_id = s.cliente_id
ORDER BY s.monto_total_dia DESC;

-- 3) Detalle de las transacciones que componen cada caso (para adjuntar
--    como evidencia al ROS)
SELECT t.*
FROM transacciones t
JOIN (
    SELECT cliente_id, date(fecha) AS dia
    FROM transacciones
    WHERE monto < 10000
    GROUP BY cliente_id, dia
    HAVING COUNT(*) >= 5 AND SUM(monto) > 10000
) casos ON casos.cliente_id = t.cliente_id AND casos.dia = date(t.fecha)
WHERE t.monto < 10000
ORDER BY t.cliente_id, t.fecha;
