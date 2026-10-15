"""
Objetivo

Entender qué ocurre cuando main.py importa otro archivo.

Estructura
ejercicio_02/
│
├── main.py
└── extractor.py


Ejecutar
python main.py

Resultado:

Iniciando programa
Extrayendo datos...
['Juan', 'Pedro', 'Ana']


Preguntas
¿Quién ejecutó extraer_datos()?
¿extractor.py se ejecutó?
¿Qué significa import?
¿Qué significa from extractor import extraer_datos?

"""

from extractor import extraer_datos

print("Iniciando programa")

datos = extraer_datos()

print(datos)
