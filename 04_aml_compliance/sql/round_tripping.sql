-- ============================================================
-- Módulo 04 — Detección de Round-tripping en SQL puro
-- Motor: SQLite (banco_rio_digital.db)
-- Busca cadenas A -> B -> C -> A de transferencias entre clientes
-- distintos, dentro de una ventana de 10 días, mediante 2 self-joins
-- encadenados sobre la propia tabla de transacciones.
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_transacciones_destino ON transacciones(cliente_destino_id, fecha);

WITH transferencias AS (
    SELECT transaccion_id, cliente_id AS origen, cliente_destino_id AS destino, fecha, monto
    FROM transacciones
    WHERE tipo = 'TRANSFERENCIA' AND cliente_id != cliente_destino_id
)
SELECT
    e1.origen                                       AS cliente_A,
    e1.destino                                       AS cliente_B,
    e2.destino                                       AS cliente_C,
    e1.fecha                                         AS fecha_paso_1,
    e2.fecha                                         AS fecha_paso_2,
    e3.fecha                                         AS fecha_paso_3,
    e1.monto                                         AS monto_paso_1,
    e2.monto                                         AS monto_paso_2,
    e3.monto                                         AS monto_paso_3,
    CAST(julianday(e3.fecha) - julianday(e1.fecha) AS INTEGER) AS dias_totales
FROM transferencias e1
JOIN transferencias e2
    ON e2.origen = e1.destino
   AND e2.fecha >= e1.fecha
   AND e2.fecha <= datetime(e1.fecha, '+10 days')
   AND e2.destino != e1.origen               -- evita contar un ida-y-vuelta simple (A->B->A) como triángulo
JOIN transferencias e3
    ON e3.origen = e2.destino
   AND e3.destino = e1.origen                -- cierra el círculo: vuelve al cliente A
   AND e3.fecha >= e2.fecha
   AND e3.fecha <= datetime(e1.fecha, '+10 days')
ORDER BY e1.fecha;

-- Nota: esta consulta puede devolver el mismo circuito más de una vez si
-- hay transacciones adicionales que también calzan en la ventana de
-- tiempo — en Python (aml_rule_engine.py) se deduplica quedándose con el
-- primer cierre de ciclo por cliente de origen. Para un análisis rápido en
-- SQL, agregar `GROUP BY cliente_A` y quedarse con el mínimo `fecha_paso_1`
-- logra el mismo efecto.
