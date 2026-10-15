"""
Ejercicio 4 — Primer Logger

Ahora dejamos print() y comenzamos con logging.

Estructura
ejercicio_04/
└── main.py

Código

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

logging.info("Programa iniciado")
logging.warning("Esto es una advertencia")
logging.error("Ocurrió un error")

Ejecutar.

El alumno observará:

INFO - Programa iniciado
WARNING - Esto es una advertencia
ERROR - Ocurrió un error
Ahora probar
logging.debug("Mensaje de debug")

Preguntar:

¿Por qué no aparece?

Explicar:

DEBUG
INFO
WARNING
ERROR
CRITICAL

y que configuramos:

level=logging.INFO

Por lo tanto:

DEBUG       ❌
INFO        ✅
WARNING     ✅
ERROR       ✅
CRITICAL    ✅
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

logging.info("Programa iniciado")
logging.warning("Esto es una advertencia")
logging.error("Ocurrió un error")
