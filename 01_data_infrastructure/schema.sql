-- ============================================================
-- Banco Río Digital — Modelo de datos financiero
-- Módulo 01: Data Infrastructure
-- ============================================================

-- CLIENTES
CREATE TABLE clientes (
    cliente_id      INTEGER PRIMARY KEY,
    nombre          TEXT,
    dni             TEXT UNIQUE,
    edad            INTEGER,
    provincia       TEXT,
    segmento        TEXT,         -- RETAIL, PYME, CORPORATIVO
    score_inicial   INTEGER,      -- 300–850
    fecha_alta      DATE,
    activo          BOOLEAN DEFAULT 1
);

-- CUENTAS
CREATE TABLE cuentas (
    cuenta_id       INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    tipo_cuenta     TEXT,         -- CC, CA, TARJETA
    moneda          TEXT DEFAULT 'ARS',
    saldo           DECIMAL(15,2),
    fecha_apertura  DATE
);

-- TRANSACCIONES
CREATE TABLE transacciones (
    transaccion_id  INTEGER PRIMARY KEY,
    cuenta_id       INTEGER REFERENCES cuentas(cuenta_id),
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    fecha           DATETIME,
    monto           DECIMAL(15,2),
    tipo            TEXT,         -- DEBITO, CREDITO, TRANSFERENCIA, PAGO, EXTRACCION
    canal           TEXT,         -- HOME_BANKING, APP, ATM, SUCURSAL, POS
    comercio        TEXT,
    ciudad          TEXT,
    es_fraude       BOOLEAN DEFAULT 0,
    flag_revision   BOOLEAN DEFAULT 0
);

-- PRÉSTAMOS
CREATE TABLE prestamos (
    prestamo_id     INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    tipo            TEXT,         -- PERSONAL, HIPOTECARIO, PRENDARIO, TARJETA
    monto_original  DECIMAL(15,2),
    monto_pendiente DECIMAL(15,2),
    tasa_anual      DECIMAL(5,2),
    cuotas_total    INTEGER,
    cuotas_pagadas  INTEGER DEFAULT 0,
    fecha_otorgamiento DATE,
    fecha_vencimiento  DATE,
    estado          TEXT,         -- VIGENTE, CANCELADO, MORA_30, MORA_60, MORA_90, INCOBRABLE
    dias_mora       INTEGER DEFAULT 0
);

-- SCORING HISTÓRICO
CREATE TABLE scoring_historico (
    id              INTEGER PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(cliente_id),
    fecha           DATE,
    score           INTEGER,
    pd_estimada     DECIMAL(5,4),  -- Probabilidad de Default
    segmento_riesgo TEXT           -- A, B, C, D, E
);
