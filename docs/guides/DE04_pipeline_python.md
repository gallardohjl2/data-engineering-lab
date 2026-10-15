# Guía DE-04 — Pipeline Python: extracción, validación y logging

## 1. Objetivo de aprendizaje

Al finalizar este bloque, el estudiante podrá:

- extraer un CSV con `csv.DictReader`;
- producir `list[dict]`;
- construir rutas con `pathlib.Path`;
- comprender `__file__`, `.resolve()` y `.parent`;
- ejecutar el pipeline con `python -m`;
- validar un contrato estructural;
- usar `set` para detectar columnas faltantes;
- detectar encabezados duplicados;
- distinguir problemas estructurales de problemas de contenido;
- manejar excepciones con `raise`, `try`, `except` y `finally`;
- configurar logging básico centralizado.

## 2. Contexto dentro del pipeline

```text
ventas.csv
    ↓
Extractor Python
    ↓
Validación estructural
    ↓
list[dict]
    ↓
Pandas
```

Python puro se utiliza aquí para extracción y estructura. Pandas se reservará para tipos, conversiones, nulos, duplicados y calidad.

## 3. Estructura relevante

```text
data-engineering-lab/
├── data/
│   ├── incoming/
│   │   ├── ventas.csv
│   │   └── clientes.xlsx
│   └── test_cases/
│       ├── ventas_adicional.csv
│       ├── ventas_duplicada.csv
│       └── ventas_mal.csv
├── pruebas/
│   ├── Ejercicios_repaso/
│   ├── validacion_columnas/
│   └── referencias/
│       └── csv_extractor_v1.py
└── src/
    ├── main.py
    ├── config/
    │   └── logging_config.py
    ├── contracts/
    │   └── ventas_contract.py
    └── extract/
        └── csv_extractor.py
```

## 4. Responsabilidades

```text
src/main.py
→ coordina el pipeline y maneja errores generales

src/extract/csv_extractor.py
→ abre, lee y valida estructuralmente el CSV

src/contracts/ventas_contract.py
→ declara las columnas obligatorias

src/config/logging_config.py
→ configura logging
```

## 5. Contrato estructural

Política acordada:

```text
Falta columna obligatoria → ERROR
Encabezado duplicado      → ERROR
Columna adicional         → PERMITIDA
```

Una columna adicional puede permanecer en los diccionarios devueltos por `DictReader`. Tolerarla no significa que necesariamente llegue al warehouse.

## 6. `list` y `set`

Para encontrar columnas faltantes:

```python
actual_set = set(actual_columns)
required_set = set(required_columns)

missing_columns = required_set - actual_set
```

La resta significa: columnas requeridas que no aparecen en el archivo.

Para detectar duplicados no basta convertir todo a `set`, porque el conjunto elimina repeticiones. Se recorre la lista original:

```python
seen_columns: set[str] = set()
duplicated_columns: set[str] = set()

for column in actual_columns:
    if column in seen_columns:
        duplicated_columns.add(column)
    else:
        seen_columns.add(column)
```

## 7. Extractor CSV

El extractor:

1. valida que la ruta exista;
2. comprueba que sea un archivo;
3. abre el CSV;
4. crea un `DictReader`;
5. valida encabezados;
6. normaliza encabezados con `strip()`;
7. devuelve `list[dict]`.

La normalización se aplica también al lector:

```python
reader.fieldnames = actual_columns
```

para que las claves de los registros coincidan con las columnas validadas.

## 8. Rutas con `Path`

En `main.py`:

```python
PROJECT_ROOT = Path(__file__).resolve().parent.parent

VENTAS_FILE = PROJECT_ROOT / "data" / "incoming" / "ventas.csv"
```

Conceptualmente:

```text
src/main.py
   ↓ .parent
src/
   ↓ .parent
data-engineering-lab/
```

El extractor recibe un objeto `Path`; no construye por sí mismo la raíz del proyecto.

## 9. Módulos y ejecución

Desde la raíz:

```powershell
python -m src.main
```

`src.main` representa `src/main.py`.

El patrón:

```python
if __name__ == "__main__":
    main()
```

hace que `main()` se ejecute cuando ese módulo actúa como punto de entrada.

## 10. Excepciones

El extractor detecta y lanza errores:

```text
archivo inexistente → FileNotFoundError
estructura inválida → ValueError
```

`main.py` maneja el flujo general:

```python
try:
    ...
except FileNotFoundError as error:
    ...
except ValueError as error:
    ...
finally:
    ...
```

No se devuelve una lista vacía ante un error real, porque podría confundirse con una extracción válida sin registros.

## 11. Logging

Configuración mínima:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

Cada módulo obtiene su logger:

```python
logger = logging.getLogger(__name__)
```

Ejemplos:

```text
src.main
src.extract.csv_extractor
```

En DE-04 el logging se mantiene en consola. `FileHandler`, rotación y observabilidad avanzada se dejan para una etapa posterior.

## 12. Casos probados

- CSV correcto.
- Archivo inexistente.
- Columna obligatoria faltante.
- Columna adicional permitida.
- Encabezado duplicado.
- Encabezados con espacios.
- Archivo válido sin registros.
- Logging en ejecución correcta y en error.

## 13. Problemas de contenido que NO se resuelven aquí

- fechas inválidas;
- valores numéricos inválidos;
- nulos;
- cantidades negativas;
- duplicados de registros;
- reglas de negocio.

Esos problemas justifican el siguiente bloque con Pandas.

## 14. Git

DE-04 se desarrolló en:

```text
feature/python-ingestion
```

Cierre previsto:

```text
commit
↓
merge local a main
↓
push origin main
↓
eliminar feature/python-ingestion
```

A partir de DE-05 se trabajará directamente en `main`, con commits locales y `push origin main` al cerrar cada bloque.

## 15. Siguiente paso

**DE-05 — Transformación inicial con Pandas**

La nueva necesidad es trabajar el contenido de los registros: tipos, fechas, nulos, duplicados y primeras reglas de calidad.
