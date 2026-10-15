"""
Punto de entrada principal del pipeline.
"""

import logging
from pathlib import Path

from src.config.logging_config import setup_logging
from src.contracts.ventas_contract import REQUIRED_COLUMNS
from src.extract.csv_extractor import extract_csv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

VENTAS_FILE = PROJECT_ROOT / "data" / "incoming" / "ventas.csv"

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Ejecuta la extracción del archivo de ventas.
    """

    setup_logging()

    logger.info("Inicio del pipeline.")

    try:
        records = extract_csv(
            file_path=VENTAS_FILE,
            required_columns=REQUIRED_COLUMNS,
        )

        logger.info("Extracción finalizada correctamente.")

        if records:
            print("\nPrimer registro extraído:")
            print(records[0])
        else:
            logger.warning(
                "El archivo fue extraído correctamente, pero no contiene registros."
            )

    except FileNotFoundError as error:
        logger.error(
            "Error de archivo: %s",
            error,
        )

    except ValueError as error:
        logger.error(
            "Error de estructura: %s",
            error,
        )

    finally:
        logger.info("Fin de la ejecución.")


if __name__ == "__main__":
    main()
