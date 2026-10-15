"""
Extractor genérico de archivos CSV (Comma Separated Values).

Responsabilidades:

1. Verificar que el archivo exista.
2. Abrirlo.
3. Leer encabezados.
4. Validar el contrato estructural.
5. Leer registros.
6. Regresar list[dict].

No realiza todavía:

- conversión de tipos;
- validación de fechas;
- tratamiento de nulos;
- reglas de negocio;
- eliminación de duplicados de registros.
"""

import csv
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def validate_file(file_path: Path) -> None:
    """
    Valida que la ruta exista y corresponda a un archivo.
    """

    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"La ruta no corresponde a un archivo: {file_path}")


def validate_columns(
    actual_columns: list[str],
    required_columns: list[str],
) -> None:
    """
    Valida la estructura obligatoria del archivo.

    El archivo es inválido cuando:

    - falta una columna obligatoria;
    - existe un encabezado duplicado.

    Las columnas adicionales están permitidas.
    """

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


def extract_csv(
    file_path: Path,
    required_columns: list[str],
) -> list[dict[str, str]]:
    """
    Extrae registros después de validar
    la estructura del CSV.
    """

    logger.info(
        "Iniciando extracción del archivo: %s",
        file_path.name,
    )

    validate_file(file_path)

    with open(
        file_path,
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("El archivo CSV no contiene encabezados.")

        actual_columns: list[str] = []

        for column in reader.fieldnames:
            actual_columns.append(column.strip())

        validate_columns(
            actual_columns,
            required_columns,
        )

        reader.fieldnames = actual_columns

        logger.info("Contrato estructural validado correctamente.")

        records = list(reader)

    logger.info(
        "Registros extraídos: %s",
        len(records),
    )

    return records
