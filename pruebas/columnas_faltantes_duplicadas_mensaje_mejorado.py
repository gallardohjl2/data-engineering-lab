# Caso 1


def validate_columns(
    actual_columns: list[str],
    required_columns: list[str],
) -> None:

    actual_set = set(actual_columns)
    required_set = set(required_columns)

    missing_columns = required_set - actual_set

    seen_columns: set[str] = set()
    duplicated_columns: set[str] = set()

    for column in actual_columns:
        if column in seen_columns:
            duplicated_columns.add(column)
        else:
            seen_columns.add(column)

    if missing_columns or duplicated_columns:
        message = "El archivo no cumple con el contrato estructural."

        if missing_columns:
            message += f"\nColumnas faltantes: {sorted(missing_columns)}"

        if duplicated_columns:
            message += f"\nColumnas duplicadas: {sorted(duplicated_columns)}"

        raise ValueError(message)


print("========================= Caso 1 ===================================")
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
validate_columns(actual_columns, required_columns)


print("Estructura correcta")

print(
    "========================= Caso 2 columna duplicada ==================================="
)

actual_columns = [
    "venta_id",
    "fecha",
    "producto_id",
    "fecha",
]

validate_columns(actual_columns, required_columns)


print("Estructura correcta")
