"""
Piensa en un set como una colección donde:

- No importa el orden
- no permiten duplicados
- es muy útil para responder preguntas de pertenencia
: ¿está estó?, ¿qué falta?, ¿qué sobra?
"""

columns = ["ventas_id", "fecha", "producto_id", "fecha"]
print(columns)
print(set(columns))

required_colums = ["venta_id", "fecha", "producto_id"]

actual_columns = ["venta_id", "producto_id"]


required_set = set(required_colums)
actual_set = set(actual_columns)

print(required_set - actual_set)
print(actual_set - required_set)


actual_columns = [
    "venta_id",
    "fecha",
    "producto_id",
    "comentario",
]

actual_set = set(actual_columns)

print(required_set - actual_set)
print(required_set - actual_set)
