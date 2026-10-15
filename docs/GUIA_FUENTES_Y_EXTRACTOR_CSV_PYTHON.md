# Guía de laboratorio — Fuentes de datos y extractor CSV con Python puro

## Proyecto: Data Engineering Lab

Esta guía reúne dos bloques consecutivos del proyecto:

1. **Preparación de las fuentes de datos**
2. **Construcción del primer extractor CSV con Python puro**

La intención es que el alumno no reciba únicamente código terminado, sino que comprenda por qué se diseña cada componente y cómo se conecta con una arquitectura de Ingeniería de Datos.

---

# PARTE I — PREPARACIÓN DE LAS FUENTES DE DATOS

## 1. Objetivo del bloque

Construir un escenario didáctico con varias fuentes de datos que simule una arquitectura real de integración.

Las fuentes serán:

```text
                    FUENTES

        ┌──────────────┼───────────────┐
        ↓              ↓               ↓
 clientes.xlsx     ventas.csv      SQL Server
                                     │
                               VentasDB
                                ├── Productos
                                └── Sucursales
```

Posteriormente todas estas fuentes serán procesadas mediante Python.

El objetivo no es trabajar con datos perfectos.

Queremos fuentes que permitan estudiar:

- contratos estructurales;
- valores faltantes;
- tipos incorrectos;
- fechas inválidas;
- duplicados;
- inconsistencias de texto;
- referencias inexistentes;
- datos fuera de rango;
- trazabilidad;
- registros válidos y rechazados;
- cargas full e incrementales.

---

## 2. ¿Por qué usar varias fuentes?

En un sistema real los datos rara vez provienen de un solo lugar.

Una organización puede recibir información desde:

```text
ERP
CRM
Excel
CSV
APIs
bases SQL
sistemas heredados
archivos externos
```

Por eso el laboratorio utiliza tecnologías distintas:

```text
clientes.xlsx
→ archivo Excel

ventas.csv
→ archivo CSV

SQL Server
→ base transaccional
```

Esto permitirá que el alumno experimente problemas de integración entre fuentes heterogéneas.

---

## 3. Papel de cada fuente

### `clientes.xlsx`

Simula información mantenida por un área administrativa o comercial en Excel.

Contendrá:

- datos de clientes;
- valores faltantes;
- diferencias de mayúsculas/minúsculas;
- espacios innecesarios;
- correos inválidos;
- fechas inválidas;
- duplicados.

### `ventas.csv`

Simula una exportación transaccional de ventas.

Contendrá:

- identificadores;
- fecha;
- cliente;
- producto;
- sucursal;
- cantidad;
- precio histórico de venta;
- descuento.

También incluirá errores controlados.

### SQL Server

Simula un sistema transaccional corporativo.

Base:

```text
VentasDB
```

Tablas:

```text
dbo.Productos
dbo.Sucursales
```

Posteriormente Python leerá SQL Server y combinará esos datos con los archivos.

---

## 4. Regla fundamental: estructura correcta, contenido imperfecto

Durante este primer escenario queremos separar dos conceptos:

```text
ESTRUCTURA
vs
CONTENIDO
```

Nuestros archivos inicialmente tendrán las columnas correctas.

Por ejemplo:

```text
ventas.csv
```

sí tendrá exactamente los nombres esperados.

Pero algunas filas contendrán valores incorrectos.

Esto permite estudiar primero:

```text
¿el archivo cumple el contrato?
```

y después:

```text
¿los datos de cada fila son válidos?
```

Ejemplo:

```csv
venta_id,fecha,cantidad
1001,2026-09-01,2
1002,fecha_invalida,-5
```

La estructura es correcta:

```text
venta_id
fecha
cantidad
```

pero el segundo registro contiene errores de calidad.

Esta separación será central en el pipeline.

---

## 5. Rama de trabajo para las fuentes

Partiendo de `main`:

```powershell
git switch main
git pull origin main
git switch -c feature/source-data
```

Comprobar:

```powershell
git branch
```

Resultado esperado:

```text
* feature/source-data
  main
```

---

## 6. Estructura de archivos

La estructura debe incluir:

```text
data-engineering-lab/
│
├── data/
│   └── incoming/
│       ├── ventas.csv
│       └── clientes.xlsx
│
├── sqlserver/
│   └── init/
│       ├── 01-create-database.sql
│       └── 02-seed-source-data.sql
│
├── postgres/
│   └── init/
│       └── 01-create-schemas.sql
│
├── docs/
│
└── compose.yaml
```

---

## 7. Crear `ventas.csv`

Ruta:

```text
data/incoming/ventas.csv
```

Contenido:

```csv
venta_id,linea_id,fecha,cliente_id,producto_id,sucursal_id,cantidad,precio_unitario,descuento_pct
1001,1,2026-09-01,1,101,1,1,15000.00,0
1002,1,2026-09-01,2,102,2,2,350.00,5
1003,1,2026-09-02,3,103,3,1,850.00,0
1004,1,2026-09-02,4,106,1,3,180.00,10
1005,1,2026-09-03,5,101,5,1,14950.00,5
1006,1,2026-09-03,,102,2,1,350.00,0
1007,1,fecha_invalida,6,103,4,1,850.00,0
1008,1,2026-09-04,7,104,1,2,100.00,0
1009,1,2026-09-04,8,999,3,1,500.00,0
1010,1,2026-09-05,1,105,1,-1,2500.00,0
1011,1,2026-09-05,2,107,2,1,,0
1012,1,2026-09-06,3,106,99,2,180.00,0
1013,1,2026-09-06,4,102,1,1,ABC,0
1014,1,2026-09-07,5,103,5,1,850.00,150
1015,1,2026-09-07,6,108,4,1,300.00,0
1015,1,2026-09-07,6,108,4,1,300.00,0
1016,1,2026-09-08,1,101,1,1,15000.00,0
1016,2,2026-09-08,1,102,1,2,350.00,0
```

Guardar como UTF-8.

---

## 8. Contrato estructural de `ventas.csv`

Las columnas esperadas son:

```text
venta_id
linea_id
fecha
cliente_id
producto_id
sucursal_id
cantidad
precio_unitario
descuento_pct
```

En esta etapa el archivo tiene una estructura válida.

Los errores están dentro de las filas.

---

## 9. Errores intencionales en `ventas.csv`

El archivo permite estudiar distintos casos.

### Cliente faltante

```text
venta_id = 1006
cliente_id vacío
```

### Fecha inválida

```text
venta_id = 1007
fecha = fecha_invalida
```

### Producto inexistente

```text
venta_id = 1009
producto_id = 999
```

No existe en la tabla `Productos`.

### Cantidad negativa

```text
venta_id = 1010
cantidad = -1
```

### Precio faltante

```text
venta_id = 1011
precio_unitario vacío
```

### Sucursal inexistente

```text
venta_id = 1012
sucursal_id = 99
```

### Precio no numérico

```text
venta_id = 1013
precio_unitario = ABC
```

### Descuento fuera de rango

```text
venta_id = 1014
descuento_pct = 150
```

### Registro duplicado

La venta:

```text
1015,1
```

aparece dos veces de forma idéntica.

---

## 10. Grano de la fuente de ventas

Un concepto fundamental en Ingeniería de Datos es el **grano**.

El grano responde:

```text
¿Qué representa exactamente una fila?
```

En este laboratorio:

```text
una fila
=
una línea de producto dentro de una venta
```

Por eso:

```text
venta_id
```

por sí solo no identifica una fila.

La combinación:

```text
venta_id + linea_id
```

representa una línea de venta.

Ejemplo:

```text
venta 1016
│
├── línea 1 → producto 101
└── línea 2 → producto 102
```

Por tanto:

```text
1016,1
1016,2
```

NO son duplicados.

Este concepto será muy importante cuando diseñemos la tabla de hechos.

---

## 11. ¿Por qué `precio_unitario` aparece en ventas si Productos ya tiene precio?

La tabla `Productos` contiene un precio que puede representar:

```text
precio actual del producto
```

pero la venta necesita conservar:

```text
precio al que realmente se vendió
```

Ejemplo:

```text
Precio actual:
$15,000

Precio histórico de una venta:
$14,950
```

No debemos reconstruir una venta histórica utilizando automáticamente el precio actual del catálogo.

Por eso:

```text
Productos.precio
```

y:

```text
ventas.precio_unitario
```

representan cosas diferentes.

Más adelante esto ayudará a distinguir:

```text
atributo dimensional
vs
medida transaccional
```

---

## 12. Crear `clientes.xlsx`

Ruta:

```text
data/incoming/clientes.xlsx
```

Crear una hoja con las columnas:

```text
cliente_id
nombre
ciudad
estado
email
fecha_registro
activo
```

Datos sugeridos:

| cliente_id | nombre | ciudad | estado | email | fecha_registro | activo |
|---:|---|---|---|---|---|---|
| 1 | Ana López | Tula de Allende | Hidalgo | ana.lopez@example.com | 2026-01-10 | ACTIVO |
| 2 | Carlos Pérez | Pachuca | Hidalgo | carlos.perez@example.com | 2026-01-12 | ACTIVO |
| 3 | Laura Gómez | Querétaro | Querétaro | laura.gomez@example.com | 2026-02-01 | ACTIVO |
| 4 | José Martínez | Tula de Allende | HIDALGO | jose.martinez@example.com | 2026-02-11 | ACTIVO |
| 5 | Fernanda Ruiz | `  Tula de Allende  ` | hidalgo | fernanda.ruiz@example.com | 2026-02-20 | ACTIVO |
| 6 | Miguel Torres | *(vacío)* | Hidalgo | miguel.torres@example.com | 2026-03-02 | ACTIVO |
| 7 | *(vacío)* | Tepeji del Río | Hidalgo | correo_invalido | 2026-03-10 | ACTIVO |
| 8 | Patricia Sánchez | Pachuca | Hidalgo | patricia.sanchez@example.com | fecha_invalida | ACTIVO |
| 9 | Luis Hernández | Tula | Hidalgo | *(vacío)* | 2026-03-15 | INACTIVO |
| 4 | José Martínez | Tula de Allende | HIDALGO | jose.martinez@example.com | 2026-02-11 | ACTIVO |

---

## 13. Errores intencionales en `clientes.xlsx`

Se incluyen deliberadamente:

```text
Hidalgo
HIDALGO
hidalgo
```

para enseñar normalización de texto.

También:

```text
"  Tula de Allende  "
```

para estudiar `TRIM`.

Además:

- ciudad vacía;
- nombre vacío;
- email inválido;
- fecha inválida;
- email faltante;
- cliente duplicado.

No deben corregirse manualmente antes de ejecutar el pipeline.

El objetivo es que el proceso de datos los detecte.

---

## 14. Fuente SQL Server

El sistema fuente SQL Server utiliza:

```text
VentasDB
```

con:

```text
dbo.Productos
dbo.Sucursales
```

### Productos

Ejemplos de problemas intencionales:

- nombre nulo;
- categorías con distinto uso de mayúsculas;
- espacios;
- precio negativo;
- precio nulo;
- producto inactivo.

### Sucursales

Ejemplos:

- ciudad nula;
- diferencias de mayúsculas/minúsculas;
- espacios en texto.

---

## 15. ¿Por qué los datos fuente contienen errores?

Porque una solución de Ingeniería de Datos no debe asumir:

```text
la fuente siempre está bien
```

Un pipeline robusto debe poder:

```text
detectar
registrar
rechazar
normalizar
trazar
```

problemas de calidad.

Si todas las fuentes fueran perfectas, no podríamos practicar estos escenarios.

---

## 16. ¿Dónde deben existir los datos semilla?

Los datos semilla se colocan únicamente en los sistemas fuente.

Ejemplo:

```text
SQL Server
→ sí contiene Productos y Sucursales
```

```text
ventas.csv
→ sí contiene ventas
```

```text
clientes.xlsx
→ sí contiene clientes
```

Pero:

```text
PostgreSQL RAW
→ todavía vacío
```

Esto es importante.

No debemos insertar manualmente esos datos en RAW.

RAW deberá llenarse mediante el pipeline.

---

## 17. Estado antes de construir Python

Debe existir:

```text
FUENTES
│
├── ventas.csv
├── clientes.xlsx
└── SQL Server
    ├── Productos
    └── Sucursales
```

Mientras PostgreSQL permanece:

```text
warehouse
│
├── raw
├── stage
├── warehouse
└── marts
```

sin datos transferidos.

Todavía NO existe:

```text
SQL Server → PostgreSQL
CSV → PostgreSQL
Excel → PostgreSQL
```

El movimiento de datos será responsabilidad del pipeline.

---

## 18. Documentar las fuentes

Crear:

```text
docs/source-data.md
```

Contenido sugerido:

```markdown
# Fuentes de datos

## Excel

Archivo:

`data/incoming/clientes.xlsx`

Contrato esperado:

- cliente_id
- nombre
- ciudad
- estado
- email
- fecha_registro
- activo

## CSV

Archivo:

`data/incoming/ventas.csv`

Contrato esperado:

- venta_id
- linea_id
- fecha
- cliente_id
- producto_id
- sucursal_id
- cantidad
- precio_unitario
- descuento_pct

Grano:

Una fila representa una línea de producto dentro de una venta.

La combinación:

`venta_id + linea_id`

identifica una línea de venta.

## SQL Server

Base:

`VentasDB`

Tablas:

- dbo.Productos
- dbo.Sucursales

## Calidad de datos

Las fuentes contienen errores controlados:

- valores faltantes;
- fechas inválidas;
- tipos incorrectos;
- duplicados;
- espacios innecesarios;
- inconsistencias de texto;
- referencias inexistentes;
- valores fuera de rango.
```

---

## 19. Documentación humana vs contrato ejecutable

`docs/source-data.md` sirve para que una persona comprenda:

```text
qué esperamos recibir
```

Posteriormente tendremos código como:

```text
src/contracts/ventas_contract.py
```

que permitirá a Python verificar:

```text
qué llegó realmente
```

Por tanto:

```text
DOCUMENTACIÓN HUMANA
source-data.md
```

y:

```text
CONTRATO EJECUTABLE
ventas_contract.py
```

son complementarios.

---

## 20. Verificar archivos con Git

Ejecutar:

```powershell
git status
```

Deben aparecer:

```text
data/incoming/ventas.csv
data/incoming/clientes.xlsx
docs/source-data.md
```

Comprobar que Git NO los está ignorando:

```powershell
git check-ignore -v data/incoming/ventas.csv
```

y:

```powershell
git check-ignore -v data/incoming/clientes.xlsx
```

Si no aparece ninguna salida, no están ignorados.

---

## 21. ¿Por qué estos datos sí pueden subirse a Git?

En este laboratorio son:

```text
ficticios
pequeños
didácticos
sin información personal real
```

Por eso pueden formar parte del repositorio.

En un entorno empresarial real no deberíamos versionar automáticamente:

```text
información personal
datos confidenciales
exports productivos
datasets enormes
credenciales
```

---

## 22. Comprobar el número de líneas del CSV

En PowerShell:

```powershell
(Get-Content .\data\incoming\ventas.csv).Count
```

Resultado esperado:

```text
19
```

porque existen:

```text
1 encabezado
+
18 registros
=
19 líneas
```

Después Python devolverá:

```python
len(records)
```

igual a:

```text
18
```

porque el encabezado no se considera un registro de datos.

---

## 23. Cierre de la rama `feature/source-data`

Revisar:

```powershell
git status
git diff
```

Preparar:

```powershell
git add .
git status
git diff --staged
```

Comprobar que `.env` no esté preparado.

Commit:

```powershell
git commit -m "feat: agregar fuentes de datos CSV y Excel"
```

Subir rama:

```powershell
git push -u origin feature/source-data
```

Crear Pull Request:

```text
feature/source-data
        ↓
main
```

Después del merge:

```powershell
git switch main
git pull origin main
git branch -d feature/source-data
```

Eliminar la rama remota si no se eliminó desde GitHub:

```powershell
git push origin --delete feature/source-data
```

Limpiar referencias obsoletas:

```powershell
git fetch --prune
```

Comprobar:

```powershell
git branch -a
```

---

## 24. Transición al siguiente bloque

Con las fuentes preparadas, el siguiente componente será:

```text
ventas.csv
    ↓
Extractor Python puro
    ↓
contrato estructural
    ↓
list[dict]
```

Todavía no utilizaremos Pandas.

La razón es pedagógica:

```text
primero entender extracción
↓
después transformación
```

---

# PARTE II — EXTRACTOR CSV CON PYTHON PURO

# 1. Arquitectura del bloque

```text
ventas.csv
    ↓
Path dinámico
    ↓
with open()
    ↓
csv.DictReader
    ↓
validación estructural
    ↓
¿faltan columnas?
¿sobran columnas?
¿hay encabezados duplicados?
    ↓
si hay error → excepción
    ↓
si es correcto → list[dict]
    ↓
logging
    ├── consola
    └── logs/pipeline.log
```

Posteriormente:

```text
list[dict]
    ↓
Pandas
    ↓
tipos / fechas / nulos / calidad
```

---

## 2. Objetivos de aprendizaje

Al finalizar, el alumno podrá:

- diferenciar extracción y transformación;
- leer un CSV con Python puro;
- usar `csv.DictReader`;
- utilizar `pathlib.Path`;
- construir rutas dinámicas;
- validar un contrato estructural estricto;
- detectar columnas faltantes, inesperadas y duplicadas;
- usar `raise`, `try`, `except` y `finally`;
- ejecutar un módulo con `python -m`;
- comprender `__file__`, `.resolve()`, `.parent` y `__name__`;
- configurar logging a consola y archivo;
- entender la función de `__pycache__`.

---

## 3. Requisitos previos

La estructura inicial debe incluir:

```text
data-engineering-lab/
│
├── data/
│   └── incoming/
│       └── ventas.csv
│
├── src/
├── .gitignore
└── ...
```

El archivo `ventas.csv` debe conservar errores de contenido intencionales como:

- fechas inválidas;
- nulos;
- precios no numéricos;
- cantidades negativas;
- referencias inexistentes;
- descuentos fuera de rango;
- filas duplicadas.

Esos errores no se validarán todavía. En este bloque solo revisamos la **estructura**.

---

## 4. Crear la rama de trabajo

```powershell
git switch main
git pull origin main
git switch -c feature/python-ingestion
```

Comprobar:

```powershell
git branch
```

Resultado esperado:

```text
* feature/python-ingestion
  main
```

---

## 5. Entorno virtual

Crear:

```powershell
python -m venv .venv
```

Activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Comprobar:

```powershell
python --version
where.exe python
```

La ruta debe apuntar al entorno `.venv`.

---

## 6. ¿Qué significa `python -m`?

Ejecutar:

```powershell
python archivo.py
```

significa ejecutar directamente un archivo.

Ejecutar:

```powershell
python -m src.main
```

significa ejecutar el módulo `src.main`, que corresponde a:

```text
src/
└── main.py
```

La notación con puntos representa paquetes y módulos:

```text
src.extract.csv_extractor
```

corresponde a:

```text
src/
└── extract/
    └── csv_extractor.py
```

Para este proyecto ejecutaremos desde la raíz:

```powershell
python -m src.main
```

---

## 7. Estructura Python

Crear:

```text
src/
│
├── __init__.py
├── main.py
├── config/
│   ├── __init__.py
│   └── logging_config.py
├── contracts/
│   ├── __init__.py
│   └── ventas_contract.py
└── extract/
    ├── __init__.py
    └── csv_extractor.py
```

Los archivos `__init__.py` pueden estar vacíos.

---

## 8. Contrato estructural de ventas

Archivo:

```text
src/contracts/ventas_contract.py
```

Código:

```python
"""
Contrato estructural de la fuente ventas.csv.
"""

REQUIRED_COLUMNS = [
    "venta_id",
    "linea_id",
    "fecha",
    "cliente_id",
    "producto_id",
    "sucursal_id",
    "cantidad",
    "precio_unitario",
    "descuento_pct",
]
```

El contrato define **qué esperamos**, mientras que el extractor define **cómo leemos un CSV**.

---

## 9. Política del contrato

El contrato será estricto:

```text
falta una columna
→ ERROR

aparece una columna desconocida
→ ERROR

hay un encabezado duplicado
→ ERROR
```

Pero estos casos todavía pueden pasar:

```text
fecha_invalida
ABC
cantidad negativa
NULL
```

porque son problemas de contenido, no de estructura.

---

## 10. Crear el extractor

Archivo:

```text
src/extract/csv_extractor.py
```

Encabezado:

```python
"""
Extractor genérico de archivos CSV.

Responsabilidades:
1. Verificar que el archivo exista.
2. Abrirlo.
3. Leer encabezados.
4. Validar el contrato.
5. Leer registros.
6. Regresar list[dict].

No realiza todavía:
- conversiones de tipos;
- validación de fechas;
- tratamiento de nulos;
- reglas de negocio;
- eliminación de duplicados de datos.
"""

import csv
import logging
from pathlib import Path


logger = logging.getLogger(__name__)
```

---

## 11. ¿Por qué importar `Path` en el extractor?

El extractor no construye la ruta del proyecto, pero sí recibe un objeto `Path`:

```python
def validate_file(file_path: Path) -> None:
```

y usa métodos como:

```python
file_path.exists()
file_path.is_file()
file_path.name
```

Por eso necesita:

```python
from pathlib import Path
```

---

## 12. Validar el archivo

Agregar:

```python
def validate_file(file_path: Path) -> None:
    """Valida que la ruta exista y sea un archivo."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {file_path}"
        )
```

`raise` genera una excepción y detiene el flujo normal.

---

## 13. Validar columnas sin usar `set`

Agregar:

```python
def validate_columns(
    actual_columns: list[str],
    required_columns: list[str],
) -> None:
    """
    Valida estrictamente la estructura del archivo.
    """

    missing_columns = []
    unexpected_columns = []
    duplicated_columns = []

    for column in required_columns:
        if column not in actual_columns:
            missing_columns.append(column)

    for column in actual_columns:
        if column not in required_columns:
            unexpected_columns.append(column)

    for column in actual_columns:
        if actual_columns.count(column) > 1:
            if column not in duplicated_columns:
                duplicated_columns.append(column)

    if (
        missing_columns
        or unexpected_columns
        or duplicated_columns
    ):

        message = (
            "El archivo no cumple con "
            "el contrato estructural."
        )

        if missing_columns:
            message += (
                "\nColumnas faltantes: "
                f"{missing_columns}"
            )

        if unexpected_columns:
            message += (
                "\nColumnas inesperadas: "
                f"{unexpected_columns}"
            )

        if duplicated_columns:
            message += (
                "\nColumnas duplicadas: "
                f"{duplicated_columns}"
            )

        raise ValueError(message)
```

### Interpretación

Para detectar faltantes:

```text
por cada columna requerida
        ↓
¿está en las columnas recibidas?
        ↓
no
        ↓
agregar a missing_columns
```

Para detectar adicionales:

```text
por cada columna recibida
        ↓
¿forma parte del contrato?
        ↓
no
        ↓
agregar a unexpected_columns
```

---

## 14. Función de extracción

Agregar al mismo archivo:

```python
def extract_csv(
    file_path: Path,
    required_columns: list[str],
) -> list[dict[str, str]]:
    """
    Extrae registros después de validar
    la estructura del CSV.
    """

    logger.info(
        "Iniciando extracción del archivo: %s",
        file_path.name,
    )

    validate_file(file_path)

    logger.info(
        "Archivo localizado correctamente: %s",
        file_path,
    )

    with open(
        file_path,
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError(
                "El archivo CSV no contiene encabezados."
            )

        actual_columns = []

        for column in reader.fieldnames:
            actual_columns.append(
                column.strip()
            )

        validate_columns(
            actual_columns,
            required_columns,
        )

        logger.info(
            "Contrato estructural validado correctamente."
        )

        records = list(reader)

    logger.info(
        "Registros extraídos: %d",
        len(records),
    )

    return records
```

---

## 15. ¿Qué hace `with open`?

```python
with open(...) as csv_file:
```

abre el archivo y lo cierra automáticamente cuando termina el bloque.

Parámetros:

```python
mode="r"
```

lectura.

```python
encoding="utf-8-sig"
```

permite manejar correctamente UTF-8 con BOM.

```python
newline=""
```

permite que el módulo `csv` administre los saltos de línea.

---

## 16. ¿Qué hace `csv.DictReader`?

Dado:

```csv
venta_id,fecha,cantidad
1001,2026-09-01,2
```

produce aproximadamente:

```python
{
    "venta_id": "1001",
    "fecha": "2026-09-01",
    "cantidad": "2",
}
```

Los valores siguen siendo `str`.

Esto es correcto: el extractor extrae, no transforma.

---

## 17. Configuración de logging

Archivo:

```text
src/config/logging_config.py
```

Código:

```python
"""
Configuración centralizada del sistema de logging.
"""

import logging
from pathlib import Path


def setup_logging(project_root: Path) -> None:
    """Configura salida a consola y archivo."""

    log_directory = project_root / "logs"

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_directory / "pipeline.log"

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
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
```

---

## 18. Niveles de logging

```text
DEBUG
→ detalle técnico

INFO
→ operación normal

WARNING
→ situación anormal que permite continuar

ERROR
→ operación fallida

CRITICAL
→ problema grave
```

En este bloque usamos principalmente `INFO` y `ERROR`.

---

## 19. Crear `main.py`

Archivo:

```text
src/main.py
```

Código:

```python
"""
Punto de entrada principal del pipeline.
"""

import logging
from pathlib import Path

from src.config.logging_config import setup_logging
from src.contracts.ventas_contract import REQUIRED_COLUMNS
from src.extract.csv_extractor import extract_csv


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

VENTAS_FILE = (
    PROJECT_ROOT
    / "data"
    / "incoming"
    / "ventas.csv"
)


def main() -> None:
    """Ejecuta el proceso de extracción."""

    setup_logging(PROJECT_ROOT)

    logger = logging.getLogger(__name__)

    logger.info(
        "Inicio del pipeline."
    )

    try:

        records = extract_csv(
            file_path=VENTAS_FILE,
            required_columns=REQUIRED_COLUMNS,
        )

        logger.info(
            "Extracción finalizada correctamente."
        )

        print("\nPrimer registro extraído:")
        print(records[0])

    except FileNotFoundError as error:

        logger.error(
            "Error de archivo: %s",
            error,
        )

    except ValueError as error:

        logger.error(
            "Error de estructura: %s",
            error,
        )

    finally:

        logger.info(
            "Fin de la ejecución."
        )


if __name__ == "__main__":
    main()
```

---

## 20. Entender `Path(__file__).resolve().parent.parent`

Supongamos:

```text
C:\proyectos\data-engineering-lab\src\main.py
```

`__file__`:

```text
C:\proyectos\data-engineering-lab\src\main.py
```

`Path(__file__)` convierte ese texto en un objeto de ruta.

`.resolve()` obtiene la ruta absoluta.

Primer `.parent`:

```text
C:\proyectos\data-engineering-lab\src
```

Segundo `.parent`:

```text
C:\proyectos\data-engineering-lab
```

Por eso:

```python
PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)
```

representa la raíz del proyecto.

---

## 21. Construcción dinámica de `VENTAS_FILE`

```python
VENTAS_FILE = (
    PROJECT_ROOT
    / "data"
    / "incoming"
    / "ventas.csv"
)
```

El operador `/` en `Path` une componentes de ruta.

```text
PROJECT_ROOT
    ↓
data
    ↓
incoming
    ↓
ventas.csv
```

Esto evita rutas absolutas dependientes de cada computadora.

---

## 22. `__file__` vs `Path.cwd()`

`Path.cwd()` responde:

```text
¿Desde qué carpeta ejecuté Python?
```

`Path(__file__).resolve()` responde:

```text
¿Dónde está físicamente este archivo Python?
```

Para localizar la raíz del proyecto usamos `__file__`.

---

## 23. `if __name__ == "__main__"`

Cuando ejecutamos:

```powershell
python -m src.main
```

Python asigna:

```python
__name__ = "__main__"
```

y entonces:

```python
main()
```

se ejecuta.

Si otro módulo importara `src.main`, `main()` no se ejecutaría automáticamente.

---

## 24. Ejecutar el pipeline

Desde la raíz del proyecto:

```powershell
python -m src.main
```

Resultado esperado aproximado:

```text
INFO | __main__ | Inicio del pipeline.
INFO | src.extract.csv_extractor | Iniciando extracción del archivo: ventas.csv
INFO | src.extract.csv_extractor | Archivo localizado correctamente...
INFO | src.extract.csv_extractor | Contrato estructural validado correctamente.
INFO | src.extract.csv_extractor | Registros extraídos: 18
INFO | __main__ | Extracción finalizada correctamente.
INFO | __main__ | Fin de la ejecución.
```

Además:

```text
logs/
└── pipeline.log
```

---

## 25. Revisar el log

```powershell
Get-Content .\logs\pipeline.log
```

Últimas líneas:

```powershell
Get-Content .\logs\pipeline.log -Tail 20
```

---

## 26. `.gitignore`

Debe incluir:

```gitignore
.venv/
__pycache__/
*.py[cod]
logs/
*.log
```

Comprobar:

```powershell
git status
```

`logs/pipeline.log` no debe aparecer.

---

## 27. ¿Qué es `__pycache__`?

Python puede crear:

```text
__pycache__/
```

con archivos como:

```text
csv_extractor.cpython-313.pyc
```

Interpretación:

```text
.py
→ código fuente

.pyc
→ bytecode compilado

__pycache__
→ carpeta del bytecode
```

No se edita ni se versiona.

---

## 28. Pruebas del laboratorio

### Prueba A — Ejecución correcta

```powershell
python -m src.main
```

Esperado:

```text
Contrato estructural validado correctamente.
Registros extraídos: 18
```

### Prueba B — Archivo inexistente

Cambiar temporalmente:

```python
/ "ventas.csv"
```

por:

```python
/ "archivo_no_existe.csv"
```

Esperado:

```text
ERROR | Error de archivo: No existe el archivo...
```

Restaurar `ventas.csv`.

### Prueba C — Columna faltante y columna inesperada

Crear una copia:

```text
ventas_error.csv
```

Cambiar el encabezado:

```text
precio_unitario
```

por:

```text
precio
```

Esperado:

```text
Columnas faltantes: ['precio_unitario']
Columnas inesperadas: ['precio']
```

### Prueba D — Encabezado duplicado

Crear un encabezado como:

```csv
venta_id,linea_id,fecha,cliente_id,producto_id,sucursal_id,cantidad,cantidad,descuento_pct
```

Esperado:

```text
Columnas duplicadas: ['cantidad']
```

---

## 29. ¿Por qué `ABC` no se rechaza todavía?

Si tenemos:

```text
precio_unitario = ABC
```

la columna `precio_unitario` sí existe.

Por tanto:

```text
estructura
→ válida
```

Pero:

```text
ABC no es un precio válido
```

es un problema de calidad de datos.

Se revisará en la etapa de Pandas.

---

## 30. Separación de responsabilidades

```text
ventas_contract.py
→ define qué columnas esperamos

csv_extractor.py
→ abre, valida estructura y extrae

logging_config.py
→ configura el sistema de logs

main.py
→ coordina la ejecución
```

Esta separación evita concentrar toda la lógica en un solo archivo.

---

## 31. Flujo completo

```text
python -m src.main
        ↓
main.py
        ↓
setup_logging()
        ↓
extract_csv()
        ↓
validate_file()
        ↓
with open()
        ↓
csv.DictReader
        ↓
validate_columns()
        ↓
¿estructura válida?
    ┌───────────┴───────────┐
    ↓                       ↓
   NO                       SÍ
    ↓                       ↓
 raise                  list(reader)
    ↓                       ↓
 except                 list[dict]
    ↓                       ↓
logger.error()          logger.info()
    └───────────┬───────────┘
                ↓
             finally
                ↓
       Fin de ejecución
```

---

## 32. Preguntas para discusión

1. ¿Por qué no conviene escribir rutas absolutas?
2. ¿Cuál es la diferencia entre `__file__` y `Path.cwd()`?
3. ¿Por qué el extractor importa `Path` si no construye la ruta?
4. ¿Cuál es la diferencia entre estructura y calidad de datos?
5. ¿Por qué una columna extra puede ser importante?
6. ¿Por qué no se crea automáticamente una columna faltante?
7. ¿Por qué `ABC` puede pasar esta fase?
8. ¿Qué diferencia existe entre `raise` y `except`?
9. ¿Qué ventaja ofrece `python -m src.main`?
10. ¿Para qué sirve `__name__ == "__main__"`?
11. ¿Por qué los logs no deben versionarse?
12. ¿Por qué aparece `__pycache__`?

---

## 33. Evidencia sugerida

El alumno puede entregar:

- captura de la estructura del proyecto;
- captura de ejecución correcta;
- captura de una prueba con error estructural;
- fragmento de `pipeline.log`;
- explicación de `Path`, `__file__` y `.parent`;
- conclusión breve.

---

## 34. Estado al terminar el bloque

```text
data-engineering-lab/
│
├── data/
│   └── incoming/
│       └── ventas.csv
├── logs/
│   └── pipeline.log
└── src/
    ├── __init__.py
    ├── main.py
    ├── config/
    │   ├── __init__.py
    │   └── logging_config.py
    ├── contracts/
    │   ├── __init__.py
    │   └── ventas_contract.py
    └── extract/
        ├── __init__.py
        └── csv_extractor.py
```

El pipeline ya puede:

```text
localizar archivo
↓
abrirlo
↓
leer encabezados
↓
validar contrato
↓
detectar errores estructurales
↓
extraer registros
↓
registrar eventos
```

Todavía no realiza:

```text
tipado
limpieza
validación de fechas
tratamiento de NULL
deduplicación
válidos / rechazados
```

---

## 35. Siguiente bloque

La arquitectura evolucionará hacia:

```text
CSV
 ↓
Extractor Python puro
 ↓
list[dict]
 ↓
metadata
 ↓
Pandas
 ↓
tipado y calidad
 ↓
válidos / rechazados
 ↓
PostgreSQL RAW
```
