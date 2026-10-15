"""
Ejercicio 5 — getLogger(__name__)

Ahora introducimos la pieza que acabamos de discutir.

Estructura
ejercicio_05/
│
├── main.py
└── extractor.py
extractor.py
import logging

logger = logging.getLogger(__name__)


def extraer_datos():
    logger.info("Iniciando extracción")

    datos = ["Juan", "Pedro", "Ana"]

    logger.info("Se obtuvieron %d registros", len(datos))

    return datos
main.py
import logging

from extractor import extraer_datos

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():

    logger.info("Iniciando programa")

    datos = extraer_datos()

    logger.info(
        "Se recibieron %d registros",
        len(datos)
    )


if __name__ == "__main__":
    main()

Resultado:

INFO - __main__ - Iniciando programa
INFO - extractor - Iniciando extracción
INFO - extractor - Se obtuvieron 3 registros
INFO - __main__ - Se recibieron 3 registros
Aquí hacer una pausa

Preguntar:

¿Por qué aparece extractor?

Porque:

logging.getLogger(__name__)

en extractor.py equivale a:

logging.getLogger("extractor")

Mientras que en main.py:

__name__

vale:

__main__
"""

import logging

from extractor import extraer_datos

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

logger = logging.getLogger(__name__)


def main():

    logger.info("Iniciando programa")

    datos = extraer_datos()

    logger.info("Se recibieron %d registros", len(datos))


if __name__ == "__main__":
    main()
