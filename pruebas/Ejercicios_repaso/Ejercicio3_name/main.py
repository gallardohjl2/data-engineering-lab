"""
Entender __name__

Aquí es donde conviene hacerlo muy visual.

Estructura
ejercicio_03/
│
├── main.py
└── extractor.py

Ejecutamos:

python main.py

El alumno verá algo parecido a:

Dentro de main.py
Dentro de extractor.py
__name__ = extractor


Ahora modificar extractor.py
print("Dentro de extractor.py")
print("__name__ =", __name__)

if __name__ == "__main__":
    print("Estoy ejecutando extractor directamente")

Ahora ejecutar:

python main.py

Verán:

Dentro de main.py
Dentro de extractor.py
__name__ = extractor

Pero si ejecutamos:

python extractor.py

verán:

Dentro de extractor.py
__name__ = __main__
Estoy ejecutando extractor directamente
Concepto clave
python extractor.py
        ↓
__name__ = "__main__"


import extractor
        ↓
__name__ = "extractor"


Reto

Agregar:

def extraer_datos():
    print("Extrayendo datos...")

y hacer que solamente se ejecute cuando:

extractor.py

sea ejecutado directamente.

"""

print("Dentro de main.py")

from extractor import *
