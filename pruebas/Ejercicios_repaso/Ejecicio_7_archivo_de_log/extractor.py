import logging

logger = logging.getLogger(__name__)


def extraer_datos():

    logger.info("Extrayendo datos")

    datos = ["Juan", "Pedro", "Ana"]

    logger.info("Extraídos %d registros", len(datos))

    return datos
