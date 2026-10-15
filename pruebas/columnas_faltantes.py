# Caso 1


def validate_columns(
    actual_columns: list[str],
    required_columns: list[str],
) -> None:

    actual_set = set(actual_columns)
    required_set = set(required_columns)

    missing_columns = required_set - actual_set

    if missing_columns:
        raise ValueError(f"Columnas obligatorias faltantes: {sorted(missing_columns)}")


required_columns = [
    "venta_id",
    "fecha",
    "producto_id",
]

actual_columns = [
    "venta_id",
    "fecha",
    "producto_id",
]

validate_columns(
    actual_columns,
    required_columns,
)

print("Estructura correcta")

print("========================= Caso 2 ===================================")

actual_columns = [
    "venta_id",
    "producto_id",
]


validate_columns(
    actual_columns,
    required_columns,
)

print("Estructura correcta")


print("========================= Caso 3 ===================================")

actual_columns = [
    "venta_id",
    "fecha",
    "producto_id",
    "comentario",
]

validate_columns(
    actual_columns,
    required_columns,
)

print("Estructura correcta")
