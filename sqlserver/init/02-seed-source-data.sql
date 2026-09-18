INSERT INTO Productos
(
    producto_id,
    nombre,
    categoria,
    precio,
    activo,
    updated_at
)
VALUES

(101, 'Laptop Lenovo', 'Computo', 15000.00, 1, '2026-09-15 09:00:00'),

(102, 'Mouse Logitech', 'computo', 350.00, 1, '2026-09-15 09:05:00'),

(103, 'Teclado Mecánico', 'CÓMPUTO', 850.00, 1, '2026-09-15 09:10:00'),

(104, NULL, 'Accesorios', 100.00, 1, '2026-09-15 09:15:00'),

(105, 'Monitor 24 pulgadas', 'Computo', -2500.00, 1, '2026-09-15 09:20:00'),

(106, 'Cable HDMI', ' accesorios ', 180.00, 1, '2026-09-15 09:25:00'),

(107, 'Webcam', 'PERIFERICOS', NULL, 1, '2026-09-15 09:30:00'),

(108, 'Producto descontinuado', 'Otros', 300.00, 0, '2026-09-15 09:35:00');
GO

INSERT INTO Sucursales
(
    sucursal_id,
    nombre,
    ciudad,
    estado,
    updated_at
)
VALUES

(1, 'Tula Centro', 'Tula de Allende', 'Hidalgo', '2026-09-15 10:00:00'),

(2, 'Pachuca Centro', 'Pachuca', 'Hidalgo', '2026-09-15 10:05:00'),

(3, 'Querétaro', 'Queretaro', 'QUERETARO', '2026-09-15 10:10:00'),

(4, 'Sucursal Norte', NULL, 'Hidalgo', '2026-09-15 10:15:00'),

(5, 'Sucursal Sur', '  Tula  ', 'hidalgo', '2026-09-15 10:20:00');
GO