"""
Ejercicio 1 — Path.cwd() y __file__
Objetivo

Que el alumno entienda la diferencia entre:

Path.cwd()

y

Path(__file__)

"""

from pathlib import Path

print("Directorio actual:")
print(Path.cwd())

print("\nArchivo actual:")
print(__file__)

print("\nDirectorio del archivo:")
print(Path(__file__).resolve().parent)


"""
Preguntas para los alumnos

¿Qué devuelve Path.cwd()?
¿Qué contiene __file__?
¿Son exactamente lo mismo?
¿Qué devuelve .parent?
¿Qué diferencia hay entre "dónde ejecuté Python" y "dónde está el archivo"?


Reto

Ejecutar:

cd ..
python ejercicio_01/main.py


Concepto que deben aprender

Path.cwd()
     ↓
¿Desde dónde ejecuté Python?

__file__
     ↓
¿Dónde está este archivo?

"""
