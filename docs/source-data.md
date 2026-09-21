# Fuentes de datos

El laboratorio utiliza tres tipos de fuentes.

## Excel

Archivo:

`data/incoming/clientes.xlsx`

Contrato estructural esperado:

- cliente_id
- nombre
- ciudad
- estado
- email
- fecha_registro
- activo

## CSV

Archivo:

`data/incoming/ventas.csv`

Contrato estructural esperado:

- venta_id
- linea_id
- fecha
- cliente_id
- producto_id
- sucursal_id
- cantidad
- precio_unitario
- descuento_pct

Grano esperado:

Una fila representa una línea de producto dentro de una venta.

La combinación:

`venta_id + linea_id`

identifica una línea de venta.

## SQL Server

Base:

`VentasDB`

Tablas fuente:

- dbo.Productos
- dbo.Sucursales

## Consideraciones

Las fuentes contienen errores controlados de calidad.

El pipeline deberá detectar y gestionar:

- valores faltantes;
- tipos inválidos;
- fechas inválidas;
- duplicados;
- espacios innecesarios;
- inconsistencias de texto;
- referencias inexistentes;
- valores fuera de rango.

Los extractores no asumirán que los datos de origen son correctos.