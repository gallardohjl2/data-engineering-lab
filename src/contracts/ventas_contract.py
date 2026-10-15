"""
Contrato estructural de la fuente ventas.csv.

Política del contrato:

- Falta una columna obligatoria -> ERROR
- Hay un encabezado duplicado -> ERROR
- Aparece una columna adicional -> PERMITIDO

Los siguientes casos pueden pasar:

- fecha inválida
- precio_unitario -> "ABC"
- cantidad negativa
- NULL

Estos son problemas de contenido, no de estructura.
Se validarán posteriormente en la etapa correspondiente.
"""

REQUIRED_COLUMNS = [
    "venta_id",
    "linea_id",
    "fecha",
    "cliente_id",
    "producto_id",
    "sucursal_id",
    "cantidad",
    "precio_unitario",
    "descuento_pct",
]

# El contrato define qué esperamos.
# El extractor define cómo obtenemos los datos.
