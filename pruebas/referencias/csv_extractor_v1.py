"""
Extractor Generico de Archivos CSV (Comma Separated Values)

Responsabilidades:

1. Verificar que el archivo exista
2. Abrirlo
3. Leer encabezados
4. Validar el contrato
5. Leer Registros
6. Regresar list[dict]

No realiza todavia:

- Conversion de Tipos
- Validación de Fechas
- Tratamiento de nulos
- Reglas del negocio
- Eliminación de duplicados

"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# importamos el path por que el extractor no construye la ruta del proyecto, pero si recibe un
# objeto Path


# ======================= función que valida la exitencia de un archivo y que sea un archivo ======================================#


def validate_file(file_path: Path) -> None:
    """
    Valida que la ruta exista y sea un archivo
    """

    # file_path() -> esta en el paquete pathlib y verifica si el archivo existe
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    # is_file()-> esta en el paquete pathlib y verifica que el el csv sea un archivo
    if not file_path.is_file():
        raise ValueError(f"La ruta no corresponde a un archivo: {file_path}")

    # raise -> genera una excepción y detiene el flujo normal

    # ======================= función que valida las columnas ======================================#


def validate_columns(actual_columns: list[str], required_columns: list[str]) -> None:
    """
    Valida estrictamente la estructura del archivo
    """

    missing_columns = []
    unexpected_columns = []
    duplicated_columns = []

    # Este ciclo verifica si no faltan columnas, si faltan entonces las guarda en
    # la lista  de missing_columns
    for column in required_columns:
        if column not in actual_columns:
            missing_columns.append(column)

    for column in actual_columns:
        if column not in required_columns:
            unexpected_columns.append(column)

    for column in actual_columns:
        if actual_columns.count(column) > 1:
            if column not in duplicated_columns:
                duplicated_columns.append(column)

    if missing_columns or unexpected_columns or duplicated_columns:
        message = "El archivo no cumple con el contrato estructural"

        if missing_columns:
            message += f"\ncolumnas faltantes: {missing_columns}"

        if unexpected_columns:
            message += f"\nColumnas inesperadas: {unexpected_columns}"

        if duplicated_columns:
            message += f"\nColumnas duplicadas: {duplicated_columns}"

        raise ValueError(message)


def extract_csv(
    file_path: Path,
    required_columns: list[str],
) -> list[dict[str, str]]:
    """
    Extrae registros después de validar
    la estructura del CSV
    """

    logger.info(
        "Iniciando extracción del archivo: %s",
        file_path.name,
    )

    validate_file(file_path)

    logger.info("Archivo localizado correctamente: %s", file_path)

    with open(
        file_path,
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("El archivo CSV no contiene encabezados")

        actual_columns = []

        for column in reader.fieldnames:
            actual_columns.append(column.strip())

        validate_columns(actual_columns, required_columns)

        logger.info("Contracto estructural validado correctamente")

        records = list(reader)

        logger.info("Registros extraidos : %s", len(records))

        return records
