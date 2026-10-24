-- ==========================================================
-- DATA ENGINEERING LAB
-- DE-06: Tabla inicial de ventas aptas
-- ==========================================================

CREATE TABLE IF NOT EXISTS raw.ventas (
    source_row_number BIGINT NOT NULL,
    estado_calidad TEXT NOT NULL,
    venta_id TEXT NOT NULL,
    linea_id TEXT NOT NULL,
    fecha DATE NOT NULL,
    cliente_id TEXT,
    producto_id TEXT,
    sucursal_id TEXT,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    descuento_pct INTEGER NOT NULL
);