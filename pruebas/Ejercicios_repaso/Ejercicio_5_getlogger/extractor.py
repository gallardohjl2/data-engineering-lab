import logging

logger = logging.getLogger(__name__)


def extraer_datos():
    logger.info("Iniciando extracción")

    datos = ["Juan", "Pedro", "Ana"]

    logger.info("Se obtuvieron %d registros", len(datos))

    return datos
