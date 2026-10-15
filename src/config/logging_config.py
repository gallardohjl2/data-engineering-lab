"""
Configuración centralizada del sistema de logging.
"""

import logging
from pathlib import Path


def setup_logging(project_root: Path) -> None:
    """
    Configura el logging de la aplicación.

    Los mensajes se enviarán a:

    1. La consola.
    2. El archivo logs/pipeline.log.
    """

    log_directory = project_root / "logs"

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / "pipeline.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(logging.INFO)

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()

    console_handler.setLevel(logging.INFO)

    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.INFO)

    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    root_logger.addHandler(file_handler)
