"""
Ejercicio 6 — Crear nuestra configuración

Ahora sí creamos:

logger_config.py
Estructura
ejercicio_06/
│
├── main.py
├── extractor.py
└── logger_config.py
logger_config.py
import logging


def configure_logging():

    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
main.py
import logging

from logger_config import configure_logging
from extractor import extraer_datos


configure_logging()

logger = logging.getLogger(__name__)


def main():

    logger.info("Iniciando pipeline")

    datos = extraer_datos()

    logger.info(
        "Recibidos %d registros",
        len(datos)
    )


if __name__ == "__main__":
    main()
extractor.py
import logging

logger = logging.getLogger(__name__)


def extraer_datos():

    logger.info("Extrayendo datos")

    datos = ["Juan", "Pedro", "Ana"]

    logger.info(
        "Extraídos %d registros",
        len(datos)
    )

    return datos

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
