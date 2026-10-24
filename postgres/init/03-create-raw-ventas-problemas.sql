-- ==========================================================
-- DATA ENGINEERING LAB
-- DE-06: Persistencia de registros problemáticos
-- ==========================================================

CREATE TABLE IF NOT EXISTS raw.ventas_problemas (
    source_row_number BIGINT NOT NULL,
    motivos_calidad TEXT[] NOT NULL,
    tiene_problemas BOOLEAN NOT NULL,
    estado_calidad TEXT NOT NULL,

    venta_id TEXT,
    linea_id TEXT,
    fecha TEXT,
    cliente_id TEXT,
    producto_id TEXT,
    sucursal_id TEXT,
    cantidad TEXT,
    precio_unitario TEXT,
    descuento_pct TEXT,

    CONSTRAINT chk_estado_ventas_problemas
        CHECK (estado_calidad IN ('RECHAZADO', 'REVISION'))
);