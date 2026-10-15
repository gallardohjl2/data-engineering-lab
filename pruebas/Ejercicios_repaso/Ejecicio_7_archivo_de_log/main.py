"""
Ejercicio 7 — Guardar el log en un archivo

Ahora incorporamos Path.

logger_config.py
from pathlib import Path
import logging


BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


def configure_logging():

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    console_handler = logging.StreamHandler()

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

Al ejecutar:

python main.py

tendremos:

ejercicio_07/
│
├── main.py
├── extractor.py
├── logger_config.py
│
└── logs/
    └── pipeline.log

Y tendremos los mensajes:

En consola:

2026-10-07 10:30:10 - INFO - __main__ - Iniciando pipeline
2026-10-07 10:30:10 - INFO - extractor - Extrayendo datos
2026-10-07 10:30:10 - INFO - extractor - Extraídos 3 registros

Y en pipeline.log:

2026-10-07 10:30:10 - INFO - __main__ - Iniciando pipeline
2026-10-07 10:30:10 - INFO - extractor - Extrayendo datos
2026-10-07 10:30:10 - INFO - extractor - Extraídos 3 registros

"""

import logging

from logger_config import configure_logging
from extractor import extraer_datos


configure_logging()

logger = logging.getLogger(__name__)


def main():

    logger.info("Iniciando pipeline")

    datos = extraer_datos()

    logger.info("Recibidos %d registros", len(datos))


if __name__ == "__main__":
    main()
