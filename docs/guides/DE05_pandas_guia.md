# DE-05 — Transformación inicial con Pandas


**Guía reproducible para alumnos — de `list[dict]` a salidas de calidad con trazabilidad**

**Estado técnico:** implementación y pruebas funcionales completadas hasta el 18 de octubre de 2026. **Cierre de repositorio pendiente:** revisión final de Git, commit e integración.


## 1. Objetivos


Al terminar esta práctica, el alumno podrá:


- Explicar por qué leer correctamente un CSV no equivale a validar su contenido.

- Instalar y registrar una dependencia externa en un entorno virtual.

- Convertir los registros de `csv.DictReader` en un `pandas.DataFrame`.

- Inspeccionar filas, tipos y nulos sin modificar el origen.

- Distinguir `DataFrame`, `Series`, índice, `dtype` y `dtypes`.

- Convertir números con `pd.to_numeric` y comparar `errors="raise"` frente a `errors="coerce"`.

- Detectar nulos, filtrar filas y distinguir valores vacíos de texto no convertible.

- Comprobar una regla inicial de negocio: `cantidad > 0`.

- Reconocer por qué hay que conservar evidencia del valor original y por qué conviene sacar experimentos de `main.py`.


## 2. Punto de partida


En DE-04 ya funciona:


```text

ventas.csv → extract_csv(Path, REQUIRED_COLUMNS) → list[dict]

```


El extractor verifica estructura: archivo, encabezados obligatorios, duplicados y normalización con `strip()`. **No valida aún los valores**. `main.py` configura logging, invoca el extractor y maneja errores generales. Ejecutamos desde la raíz con `python -m src.main`.


Las fuentes `clientes.xlsx` y SQL Server (productos/sucursales) se integrarán después. Pandas se usará aquí para contenido, y dbt posteriormente para modelos analíticos en PostgreSQL.


## 3. Archivos utilizados


```text

data-engineering-lab/

├── data/

│   ├── incoming/ventas.csv              # NO modificar para los ejercicios

│   └── test_cases/

│       └── ventas_cantidad_invalida.csv # copia de prueba

├── src/

│   ├── main.py

│   ├── extract/csv_extractor.py

│   ├── contracts/ventas_contract.py

│   └── config/logging_config.py

├── requirements.txt

└── .gitignore

```


A lo largo de la guía se incorporan `src/transform/ventas_transformer.py`, `src/quality/ventas_quality.py` y `src/quality/ventas_policy.py`, integrados desde `main.py`.


## 4. Preparar el entorno (PowerShell)


Desde la raíz del proyecto:


```powershell

python -m venv .venv

.\\.venv\Scripts\Activate.ps1

python -m pip install pandas==3.0.6

python -m pip show pandas

```


Se utilizó Python 3.13 en Windows y se confirmó Pandas **3.0.6**. El archivo `requirements.txt` debe contener:


```text

pandas==3.0.6

```


De ahora en adelante, en otra computadora, la instalación se puede hacer con:


```powershell

python -m pip install -r requirements.txt

```


Añadir `.venv/` a `.gitignore` (sin borrar reglas existentes). Subimos `requirements.txt` a Git, **no** la carpeta `.venv`. `logging`, `pathlib` y `csv` son módulos estándar; no se ponen en requirements. Pandas instala dependencias transitivas como NumPy, `python-dateutil` y `tzdata`. Fijar solo Pandas **no bloquea todas** las versiones transitivas; más adelante puede utilizarse un lockfile.


## 5. Práctica incremental


\> **Regla didáctica:** hacer un paso, ejecutar, interpretar el resultado y pasar al siguiente. Los `print()` siguientes son experimentos temporales, no el código definitivo del pipeline.


### Paso 1 — Obtener un DataFrame


Agregar a los imports de `src/main.py`:


```python

import pandas as pd

```


En el bloque `if records:` después de `extract_csv(...)`:


```python

df_ventas = pd.DataFrame(records)

print("\nPrimeras filas del DataFrame:")

print(df_ventas.head())

```


- `pd` es el alias convencional de Pandas.

- `DataFrame(records)` usa cada diccionario como fila y las claves como columnas.

- `head()` devuelve las primeras cinco filas; no modifica el original.

- El índice de Pandas empieza en `0`; no es `venta_id`.

- `...` en la representación indica columnas ocultas **solo en pantalla**.


En el escenario real se extrajeron **18 registros** de **9 columnas**.


### Paso 2 — Inspeccionar antes de transformar


```python

print(df_ventas.dtypes)

df_ventas.info()

print(df_ventas.columns)

```


- `dtypes` es el atributo con los tipos de **todas las columnas**.

- `info()` es un método que imprime número de filas, columnas, valores reconocidos como no nulos y memoria estimada; no se requiere `print(info())`.

- `columns` lista las etiquetas de columnas.

- Una columna obtenida con `df_ventas["cantidad"]` es una **Series**; su tipo se consulta con `.dtype` (singular).


**Resultado observado:** 18 filas, 9 columnas, todas inicialmente `str` en Pandas 3.0.6. `csv.DictReader` había leído los campos como texto. El `dtype: object` que aparece al final de la salida de `df_ventas.dtypes` describe la **Series de tipos**, no contradice los `str` listados.


**Cuidado:** `18 non-null` no prueba que haya 18 cantidades útiles: la cadena vacía `""` puede contarse como no nula si el DataFrame nace de diccionarios de cadenas.


### Paso 3 — Conversión numérica correcta


Primero experimentar sin modificar la columna:


```python

cantidades_numericas = pd.to_numeric(df_ventas["cantidad"])

print(cantidades_numericas.head())

print(cantidades_numericas.dtype)

```


Con el archivo limpio, el resultado observado fue `int64`.


Después practicar la asignación al DataFrame:


```python

df_ventas["cantidad"] = pd.to_numeric(df_ventas["cantidad"])

print(df_ventas.dtypes)

```


El **lado derecho** convierte; el **izquierdo** reemplaza la columna en memoria. El CSV en disco no cambia.


### Paso 4 — Crear un caso de prueba que falle


Copiar `data/incoming/ventas.csv` a `data/test_cases/ventas_cantidad_invalida.csv`. Sin cambiar los encabezados, modificar la cantidad de `venta_id=1001` a `abc`.


Temporalmente seleccionar ese archivo en `main.py`:


```python

\# VENTAS_FILE = PROJECT_ROOT / "data" / "incoming" / "ventas.csv"

VENTAS_FILE = PROJECT_ROOT / "data" / "test_cases" / "ventas_cantidad_invalida.csv"

```


Al ejecutar `pd.to_numeric(df_ventas["cantidad"])` con el comportamiento predeterminado `errors="raise"`, se observó:


```text

Error de estructura: Unable to parse string "abc" at position 0

```


**Diagnóstico:** el extractor pasó la validación estructural. El problema era de **contenido**. El `except ValueError` de `main.py` lo etiquetó equivocadamente como estructural, pues captura ambos errores. Hay que mejorar esa distinción al refactorizar.


### Paso 5 — Conversión tolerante y valores faltantes


Reemplazar la conversión por:


```python

df_ventas["cantidad"] = pd.to_numeric(

    df_ventas["cantidad"],

    errors="coerce",

)

print(df_ventas["cantidad"].head())

print(df_ventas["cantidad"].dtype)

```


`errors="coerce"` convierte texto imposible (`"abc"`) en un valor faltante (`NaN`) en lugar de lanzar el error. En la prueba apareció `float64` y cantidades `2.0`, `1.0`. **No significa corregir** el dato: lo representa como faltante para poder investigarlo.


### Paso 6 — Detectar, contar y filtrar nulos


```python

print(df_ventas["cantidad"].isna())

print(df_ventas["cantidad"].isna().sum())


registros_con_cantidad_nula = df_ventas.loc[

    df_ventas["cantidad"].isna()

]

registros_sin_cantidad_nula = df_ventas.loc[

    df_ventas["cantidad"].notna()

]

print(registros_con_cantidad_nula)

print(len(registros_sin_cantidad_nula))

```


- `isna()` devuelve una Series booleana con `True` para valores faltantes.

- `.sum()` cuenta `True` como 1 y `False` como 0.

- `loc[condicion]` filtra filas; `notna()` es la condición complementaria.

- `len(DataFrame)` cuenta filas.


En la primera prueba (`1001=abc`), el conteo fue **1 nulo y 17 no nulos**. **No** se deben llamar «17 válidos»: solo pasaron **una** comprobación.


### Paso 7 — Conservar el valor original


**Antes de convertir**, copiar la columna:


```python

df_ventas["cantidad_original"] = df_ventas["cantidad"].copy()

```


**Después** de convertir:


```python

print(df_ventas[["venta_id", "cantidad_original", "cantidad"]].head())

```


- `.copy()` crea una copia de la Series para preservar los valores previos a la conversión.

- Los **dos pares de corchetes** seleccionan varias columnas a partir de una lista de etiquetas.

- Esta columna es una **técnica de experimentación**, no la política definitiva de trazabilidad.


### Paso 8 — Distinguir cadena vacía de texto no numérico


En la **copia de prueba**, poner vacía la cantidad de `venta_id=1002`, conservando `1001=abc`.


```python

cantidad_vacia = df_ventas["cantidad_original"] == ""


cantidad_no_numerica = (

    df_ventas["cantidad"].isna()

    & ~cantidad_vacia

)


print(df_ventas.loc[cantidad_vacia])

print(df_ventas.loc[cantidad_no_numerica])

```


- `==` compara, no asigna.

- `&` combina dos Series booleanas con «Y» lógico; `~` invierte la condición.

- `cantidad_vacia` seleccionó `venta_id=1002`.

- `cantidad_no_numerica` seleccionó `venta_id=1001`.

- Se observaron **2 nulos tras la conversión y 16 cantidades no nulas**.


**Limitación deliberada:** `== ""` detecta exactamente cadena vacía, no cadenas solo de espacios ni otras representaciones de ausencia; se ampliará al introducir reglas de calidad.


### Paso 9 — Calidad de negocio: valores numéricos no positivos


En la **copia de prueba**, cambiar `venta_id=1003` de `1` a `-5`. Conservar las otras dos anomalías.


```python

cantidad_no_positiva = df_ventas["cantidad"] <= 0

print(df_ventas.loc[cantidad_no_positiva])

```


- `<= 0` devuelve `True` para cero y cantidades negativas.

- Un `NaN` no se identifica mediante esta comparación, para ello usamos `isna()`.

- **Regla didáctica provisional:** una cantidad de venta debe ser `> 0`; revisar esta decisión si se modelan devoluciones o cancelaciones.


**Resultado realmente observado:** aparecen `venta_id=1003` con `-5` **y `venta_id=1010` con `-1`**. El segundo caso ya estaba presente en los datos de prueba: por tanto **no es correcto afirmar que el archivo solo contiene las tres anomalías que acabamos de introducir**.


## 6. Resultados de la exploración inicial (antes de refactorizar)


La copia `data/test_cases/ventas_cantidad_invalida.csv` conserva nueve columnas y 18 filas. En las prácticas se identificaron: `cantidad="abc"` (venta 1001), cantidad vacía (1002), cantidades negativas (1003, 1010), fecha `fecha_invalida` (1007), precio vacío (1011), precio `ABC` (1013), descuento 150 (1014) y la clave de línea repetida en las filas con índices 14 y 15 (venta 1015). Son datos observados durante los ejercicios, no un inventario exhaustivo de todas las posibles anomalías.


Se probó que `pd.to_numeric(..., errors="raise")` lanza `ValueError` con `"abc"`. Con `errors="coerce"`, la misma entrada se convierte en `NaN`. `isna()` identifica las posiciones faltantes; `isna().sum()` las cuenta; `df.loc[mascara]` selecciona filas. Una copia temporal de `cantidad_original` permitió distinguir `"abc"` de `""`. Esta copia fue un **experimento didáctico**, no una decisión definitiva de persistencia.


## 7. Refactorización: salir de los experimentos en main.py


### Paso 10 — Crear el paquete de transformación


Problema: `main.py` acumulaba `print()`, exploraciones, conversiones y filtros. Una vez aprendidas esas operaciones, debían salir del coordinador.


Crear `src/transform/__init__.py` (vacío) y `src/transform/ventas_transformer.py`. La primera implementación fue:


```python

import pandas as pd


def transform_ventas(records: list[dict]) -> pd.DataFrame:

    df_ventas = pd.DataFrame(records)

    return df_ventas

```


`records: list[dict]` expresa el tipo de entrada esperado; `-> pd.DataFrame` documenta el retorno; `return` entrega el objeto al llamador (a diferencia de `print()`, que solo lo muestra). Son anotaciones, no validaciones automáticas en tiempo de ejecución.


En `main.py`, reemplazar el import directo de Pandas por:


```python

from src.transform.ventas_transformer import transform_ventas

```


Y reemplazar el código experimental dentro de `if records:` por la llamada `df_ventas = transform_ventas(records)`, inicialmente seguida de una visualización `head()` para comprobar la refactorización. Una vez verificada, retirar esa impresión temporal.


### Paso 11 — Convertir cuatro columnas, una a una


Agregar progresivamente al transformador las conversiones de `cantidad`, `precio_unitario`, `descuento_pct` y `fecha`, ejecutando y comprobando cada cambio. El **contenido final conocido** de `src/transform/ventas_transformer.py` es:


```python

"""

Transformaciones de los datos de ventas.

"""


import pandas as pd


def transform_ventas(records: list[dict]) -> pd.DataFrame:

    """

    Convierte los registros extraídos en un DataFrame

    y realiza las conversiones iniciales de tipos de ventas.

    """

    df_ventas = pd.DataFrame(records)


    df_ventas["cantidad"] = pd.to_numeric(

        df_ventas["cantidad"], errors="coerce"

    )

    df_ventas["precio_unitario"] = pd.to_numeric(

        df_ventas["precio_unitario"], errors="coerce"

    )

    df_ventas["descuento_pct"] = pd.to_numeric(

        df_ventas["descuento_pct"], errors="coerce"

    )

    df_ventas["fecha"] = pd.to_datetime(

        df_ventas["fecha"], format="%Y-%m-%d", errors="coerce"

    )

    return df_ventas

```


**Explicación:** `to_numeric` interpreta números; `to_datetime` interpreta fechas. El formato `%Y-%m-%d` exige año de cuatro cifras, mes y día. `errors="coerce"` transforma errores numéricos en valores faltantes (`NaN`) y errores temporales en `NaT`, en vez de detener el proceso. Esta decisión posibilita diagnosticar filas problemáticas, **pero puede ocultar el valor de origen en el DataFrame devuelto**, por lo que queda pendiente una estrategia de trazabilidad.


Comprobaciones reales con Pandas 3.0.6 y el archivo de prueba:


\| Columna | `dtype` observado | Nota |

\|---|---|---|

\| `cantidad` | `float64` | Contiene `NaN` para `abc` y vacío |

\| `precio_unitario` | `float64` | Contiene `NaN` para vacío y `ABC` |

\| `descuento_pct` | `int64` | El 150 se convierte, pero incumple calidad |

\| `fecha` | `datetime64[us]` | La fecha inválida se convierte en `NaT` |


El tipo temporal `datetime64[us]` usa microsegundos; no es un error. Para dinero, `float64` sirve en esta exploración, pero la precisión decimal exacta requiere una decisión posterior (por ejemplo, `NUMERIC` en PostgreSQL).


### Paso 12 — Inspección sin llenar main.py


Ejecutar pruebas puntuales desde la raíz con una consola interactiva (`python`):


```python

from src.main import VENTAS_FILE

from src.extract.csv_extractor import extract_csv

from src.contracts.ventas_contract import REQUIRED_COLUMNS

from src.transform.ventas_transformer import transform_ventas


records = extract_csv(VENTAS_FILE, REQUIRED_COLUMNS)

df = transform_ventas(records)

print(df[["cantidad", "precio_unitario", "descuento_pct"]].dtypes)

print(df[["venta_id", "fecha"]].head(8))

```


En una sesión persistente, Python puede conservar módulos previamente importados. Si se edita `ventas_transformer.py` u otro módulo mientras la consola permanece abierta, **reiniciar la consola** y volver a importar para probar la nueva versión. `python -m src.main` inicia normalmente un proceso nuevo y carga el código actual.


## 8. Reglas de calidad: del experimento a funciones


### Paso 13 — Separar transformación de validación


**Conversión:** `"-5"` → `-5.0` es correcta. **Regla de negocio:** cantidad debe ser estrictamente positiva; `-5.0` no es válido. Las funciones de validación devuelven máscaras booleanas (`pd.Series`), no DataFrames ni archivos de rechazados.


Se crearon primero las funciones junto al transformador para practicar y luego se movieron, sin cambiar su lógica, a `src/quality/ventas_quality.py`, con un `src/quality/__init__.py` vacío. El módulo de calidad consolidado quedó así:


```python

"""Reglas de calidad para los datos de ventas."""


import pandas as pd


def validar_cantidad(df_ventas: pd.DataFrame) -> pd.Series:

    """Identifica cantidades nulas o menores o iguales a cero."""

    return df_ventas["cantidad"].isna() | (df_ventas["cantidad"] <= 0)


def validar_precio(df_ventas: pd.DataFrame) -> pd.Series:

    """Identifica precios unitarios nulos o menores o iguales a cero."""

    return df_ventas["precio_unitario"].isna() | (df_ventas["precio_unitario"] <= 0)


def validar_descuento(df_ventas: pd.DataFrame) -> pd.Series:

    """Identifica descuentos nulos o fuera del rango de 0 a 100."""

    return (

        df_ventas["descuento_pct"].isna()

        | (df_ventas["descuento_pct"] < 0)

        | (df_ventas["descuento_pct"] > 100)

    )


def validar_fecha(df_ventas: pd.DataFrame) -> pd.Series:

    """Identifica fechas nulas o que no pudieron convertirse."""

    return df_ventas["fecha"].isna()


def validar_duplicados(df_ventas: pd.DataFrame) -> pd.Series:

    """Marca todas las filas con clave (venta_id, linea_id) repetida."""

    return df_ventas.duplicated(

        subset=["venta_id", "linea_id"], keep=False

    )


def diagnosticar_calidad(df_ventas: pd.DataFrame) -> pd.Series:

    """Marca registros que incumplen al menos una regla de ventas."""

    return (

        validar_cantidad(df_ventas)

        | validar_precio(df_ventas)

        | validar_descuento(df_ventas)

        | validar_fecha(df_ventas)

        | validar_duplicados(df_ventas)

    )

```


**Lectura de las condiciones:** `.isna()` detecta `NaN` y `NaT`; `|` combina condiciones con OR por fila; `<=`, `<`, `>` comparan con umbrales. `descuento_pct=0` es válido y `150` no. La clave lógica de una línea de venta se toma provisionalmente como `(venta_id, linea_id)`: varias líneas de una misma venta son legítimas. `duplicated(..., keep=False)` marca **todas** las filas con clave repetida, no solo las ocurrencias posteriores. No se usa `drop_duplicates()`.


### Paso 14 — Entender el contrato de retorno de calidad


```python

mascara = diagnosticar_calidad(df)  # pandas.Series con True/False

filas = df.loc[mascara, ["venta_id", "cantidad"]]  # pandas.DataFrame

```


La función devuelve una Series de booleanos. **`.loc` sobre el DataFrame** aplica la máscara y selecciona filas; con la lista de columnas devuelve un DataFrame. `.loc` no siempre devuelve DataFrame: `df.loc[0]` devuelve Series, `df.loc[[0]]` devuelve DataFrame y `df.loc[0, "cantidad"]` devuelve el valor de esa celda.


### Paso 15 — Diagnóstico agregado


Combinar las máscaras con OR para identificar filas que incumplen **una o más** reglas. El número de incumplimientos por regla no debe confundirse con la cantidad de filas distintas afectadas.


\| Regla | Filas marcadas en el CSV de prueba |

\|---|---:|

\| Cantidad nula/no positiva | 4 |

\| Precio nulo/no positivo | 2 |

\| Descuento faltante/fuera de rango | 1 |

\| Fecha inválida/faltante | 1 |

\| Clave duplicada con `keep=False` | 2 |

\| **Unión: registros con al menos un problema** | **10** |

\| **Registros sin problemas detectados por estas reglas** | **8** |


Las dos filas de la venta 1015 tienen la misma clave de línea, por lo que hay **dos filas involucradas** en un conflicto de duplicidad, no dos duplicaciones adicionales. No se detectó superposición entre los diez casos observados. Los ocho restantes **no son una certificación completa de validez**; solo cumplen las cinco reglas implementadas.

## 9. Diagnóstico detallado y trazabilidad

### Paso 16 — Conservar la referencia a la fila de origen

El extractor recorre cada registro de `csv.DictReader` con `enumerate(reader, start=2)`; la cabecera ocupa la primera línea lógica. Tras comprobar que ninguna fila contenga más o menos campos que el encabezado, agrega `record["source_row_number"] = row_number` y conserva los registros originales en la lista `records`. Antes de hacerlo, rechaza un encabezado de entrada llamado `source_row_number`, porque es un campo técnico reservado.

- `source_row_number` permite localizar el registro dentro del archivo procesado. **No es una clave global:** puede repetirse en otros archivos o lotes.
- El índice de Pandas no es una referencia estable de procedencia después de filtrar o reordenar filas.
- Para este laboratorio, la numeración se refiere a registros lógicos; un CSV con campos multilínea no siempre coincide con la línea física del editor.
- El contrato sigue exigiendo las nueve columnas de negocio y permitiendo columnas adicionales.

### Paso 17 — Explicar todos los motivos de calidad

En `src/quality/ventas_quality.py` se añaden dos funciones después de las cinco validaciones iniciales:

```python
def obtener_motivos(registro: pd.Series) -> list[str]:
    motivos = []
    if registro["error_cantidad"]:
        motivos.append("Cantidad inválida")
    if registro["error_precio"]:
        motivos.append("Precio inválido")
    if registro["error_descuento"]:
        motivos.append("Descuento inválido")
    if registro["error_fecha"]:
        motivos.append("Fecha inválida")
    if registro["error_duplicado"]:
        motivos.append("Clave duplicada")
    return motivos


def diagnosticar_calidad_detallada(df_ventas: pd.DataFrame) -> pd.DataFrame:
    df_diagnostico = df_ventas[
        ["venta_id", "linea_id", "source_row_number"]
    ].copy()
    df_diagnostico["error_cantidad"] = validar_cantidad(df_ventas)
    df_diagnostico["error_precio"] = validar_precio(df_ventas)
    df_diagnostico["error_descuento"] = validar_descuento(df_ventas)
    df_diagnostico["error_fecha"] = validar_fecha(df_ventas)
    df_diagnostico["error_duplicado"] = validar_duplicados(df_ventas)
    df_diagnostico["motivos_calidad"] = df_diagnostico.apply(
        obtener_motivos, axis=1
    )
    df_diagnostico["tiene_problemas"] = df_diagnostico[
        "motivos_calidad"
    ].apply(bool)
    return df_diagnostico
```

`apply(..., axis=1)` pasa cada **fila** como `Series` a `obtener_motivos()`. Usamos cinco `if` independientes en lugar de `elif`: una venta puede incumplir varias reglas simultáneamente. `.apply(bool)` produce `False` para una lista vacía y `True` para una lista con al menos un motivo. Comparamos el resultado contra la máscara agregada original para verificar consistencia: **10 registros problemáticos y 8 sin problemas detectados**.

### Paso 18 — Recuperar valores originales para investigar

La conversión tolerante cambia `"abc"` a `NaN`, `"fecha_invalida"` a `NaT`, etc. La vista de investigación no debe perder esas evidencias. Por eso se une el diagnóstico de las filas problemáticas con la lista original `records`:

```python
def construir_vista_investigacion(
    records: list[dict], df_diagnostico: pd.DataFrame
) -> pd.DataFrame:
    df_original = pd.DataFrame(records)
    diagnostico_problemas = df_diagnostico.loc[
        df_diagnostico["tiene_problemas"],
        ["source_row_number", "motivos_calidad", "tiene_problemas", "estado_calidad"],
    ].copy()
    df_investigacion = diagnostico_problemas.merge(
        df_original,
        on="source_row_number",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not df_investigacion["_merge"].eq("both").all():
        raise ValueError(
            "Existen registros diagnosticados sin correspondencia en el origen."
        )
    return df_investigacion.drop(columns=["_merge"])
```

**Orden importante:** esta función recibe un DataFrame **ya clasificado**, porque necesita `estado_calidad`. `merge(..., validate="one_to_one")` comprueba la unicidad de la clave de unión en ambos lados; `indicator=True` incorpora `_merge` para detectar filas sin correspondencia. Se comprobó la conservación de `"abc"`, `"fecha_invalida"` y campos originales vacíos.

## 10. Política de calidad y destinos lógicos

### Paso 19 — Separar diagnóstico de decisión

**Diagnóstico** significa describir qué falla; **política** significa decidir qué hacer con esos motivos. En `src/quality/ventas_policy.py`:

```python
import pandas as pd


def clasificar_registro(motivos: list[str]) -> str:
    reglas_bloqueantes = {
        "Cantidad inválida",
        "Precio inválido",
        "Descuento inválido",
        "Fecha inválida",
    }
    if any(motivo in reglas_bloqueantes for motivo in motivos):
        return "RECHAZADO"
    if "Clave duplicada" in motivos:
        return "REVISION"
    return "APTO"


def aplicar_politica_calidad(df_diagnostico: pd.DataFrame) -> pd.DataFrame:
    df_resultado = df_diagnostico.copy()
    df_resultado["estado_calidad"] = df_resultado[
        "motivos_calidad"
    ].apply(clasificar_registro)
    return df_resultado
```

Una fila con cualquier causa bloqueante queda `RECHAZADO`, aunque tenga además duplicidad. Una fila cuya única incidencia sea duplicidad queda `REVISION`: no elegimos arbitrariamente cuál conservar. Una fila sin motivos queda `APTO` **según las reglas implementadas**, no según todas las reglas imaginables.

### Paso 20 — Separar por estado y detectar estados desconocidos

```python
def separar_por_estado(
    df_clasificado: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    estados_permitidos = {"APTO", "RECHAZADO", "REVISION"}
    estados_encontrados = set(df_clasificado["estado_calidad"])
    estados_invalidos = estados_encontrados - estados_permitidos
    if estados_invalidos:
        raise ValueError(
            f"Se encontraron estados de calidad inválidos: {sorted(estados_invalidos)}"
        )
    df_aptos = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "APTO"
    ].copy()
    df_rechazados = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "RECHAZADO"
    ].copy()
    df_revision = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "REVISION"
    ].copy()
    return df_aptos, df_rechazados, df_revision
```

Se comprobó tanto la clasificación **8 APTO / 8 RECHAZADO / 2 REVISION**, como que los grupos no se solapan y cubren las 18 filas originales. También se probó que `PENDIENTE` provoca `ValueError`.

### Paso 21 — Preparar datos completos para aptos

La tabla de diagnóstico no contiene todos los campos necesarios para una carga posterior. Recuperamos los datos transformados de los aptos por su referencia de origen:

```python
def preparar_aptos(
    df_ventas: pd.DataFrame,
    df_clasificado: pd.DataFrame,
) -> pd.DataFrame:
    df_aptos = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "APTO",
        ["source_row_number", "estado_calidad"],
    ].copy()
    df_resultado = df_aptos.merge(
        df_ventas,
        on="source_row_number",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not df_resultado["_merge"].eq("both").all():
        raise ValueError(
            "Existen registros aptos sin correspondencia en los datos transformados."
        )
    return df_resultado.drop(columns=["_merge"])
```

Las salidas de este bloque **son DataFrames en memoria**, no tablas persistentes ni archivos de rechazados. Los ocho registros aptos mantienen las columnas transformadas; los ocho rechazados y dos en revisión llevan valores originales y motivos para investigar.

## 11. Integración final en `main.py`

`src/main.py` es el **coordinador**, no el lugar para colocar reglas Pandas ni experimentos de impresión. A continuación se muestra el flujo verificado, usando la configuración de logging de DE-04 restaurada al finalizar la revisión del repositorio:

```python
"""Punto de entrada principal del pipeline."""

import logging
from pathlib import Path

from src.config.logging_config import setup_logging
from src.contracts.ventas_contract import REQUIRED_COLUMNS
from src.extract.csv_extractor import extract_csv
from src.quality.ventas_quality import (
    diagnosticar_calidad_detallada,
    construir_vista_investigacion,
)
from src.quality.ventas_policy import (
    aplicar_politica_calidad,
    separar_por_estado,
    preparar_aptos,
)
from src.transform.ventas_transformer import transform_ventas

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENTAS_FILE = PROJECT_ROOT / "data" / "test_cases" / "ventas_cantidad_invalida.csv"
logger = logging.getLogger(__name__)


def main() -> None:
    """Coordina la extracción, transformación y calidad de las ventas."""
    setup_logging(PROJECT_ROOT)
    logger.info("Inicio del pipeline.")
    try:
        records = extract_csv(VENTAS_FILE, REQUIRED_COLUMNS)
        logger.info("Extracción finalizada correctamente.")
        if records:
            df_ventas = transform_ventas(records)
            logger.info("Transformación inicial de ventas finalizada correctamente.")
            df_diagnostico = diagnosticar_calidad_detallada(df_ventas)
            df_clasificado = aplicar_politica_calidad(df_diagnostico)

            df_aptos_final = preparar_aptos(df_ventas, df_clasificado)
            df_investigacion = construir_vista_investigacion(
                records, df_clasificado
            )
            _, df_rechazados_final, df_revision_final = separar_por_estado(
                df_investigacion
            )

            total_registros = len(df_diagnostico)
            total_con_problemas = int(df_diagnostico["tiene_problemas"].sum())
            logger.info(
                "Diagnóstico de calidad: %s registros analizados, "
                "%s con problemas y %s sin problemas detectados.",
                total_registros,
                total_con_problemas,
                total_registros - total_con_problemas,
            )
            conteo_estados = df_clasificado["estado_calidad"].value_counts()
            logger.info(
                "Clasificación de calidad: %s aptos, %s rechazados y %s en revisión.",
                int(conteo_estados.get("APTO", 0)),
                int(conteo_estados.get("RECHAZADO", 0)),
                int(conteo_estados.get("REVISION", 0)),
            )
            logger.info(
                "Salidas preparadas: %s aptos transformados, "
                "%s rechazados y %s en revisión con valores originales.",
                len(df_aptos_final),
                len(df_rechazados_final),
                len(df_revision_final),
            )
        else:
            logger.warning(
                "El archivo fue extraído correctamente, pero no contiene registros."
            )
    except FileNotFoundError as error:
        logger.error("Error de archivo: %s", error)
        raise
    except ValueError as error:
        logger.error("Error durante el procesamiento: %s", error)
        raise
    finally:
        logger.info("Fin de la ejecución.")


if __name__ == "__main__":
    main()
```

No debe repetirse `aplicar_politica_calidad()` ni ejecutar una separación inicial cuyo resultado vaya a descartarse. El caso `if records` evita ejecutar conversiones con un CSV sin filas. La llamada `setup_logging(PROJECT_ROOT)` preserva el `FileHandler` del módulo de DE-04 y el registro en `logs/pipeline.log`.

`raise` vuelve a lanzar la excepción capturada: se conserva el traceback y el proceso finaliza con un código distinto de cero. La frase «Fin de la ejecución» del `finally` significa que la ejecución **terminó**, no necesariamente que haya tenido éxito.

## 12. Ejecución y comprobaciones finales

Desde la raíz del repositorio, con `.venv` activado:

```powershell
python -m src.main
$LASTEXITCODE
Get-Content logs/pipeline.log -Tail 10
```

En el archivo de prueba con 18 registros, se verificaron:

| Métrica | Resultado |
|---|---:|
| Registros extraídos y diagnosticados | 18 |
| Registros con problemas | 10 |
| Registros sin problemas detectados | 8 |
| Aptos finales | 8 |
| Rechazados finales | 8 |
| En revisión finales | 2 |
| Código de salida normal | `0` |

### Casos de fallo y bordes

| Escenario | Conducta esperada y verificada |
|---|---|
| `ventas_cantidad_invalida.csv` | Termina normalmente; identifica problemas de contenido y clasifica 8/8/2; código `0` |
| Archivo inexistente | `FileNotFoundError`, log de error, traceback y código `1` |
| `ventas_estructura_invalida.csv` (fila 3 incompleta) | `ValueError`, no se transforma; código `1` |
| `ventas_sin_registros.csv` con encabezados válidos | 0 registros, advertencia y código `0` |
| Fila con campos de más | Comprobado directamente en el extractor; **no** se reportó prueba completa de código de salida desde `main.py` |
| Estado no contemplado `PENDIENTE` | Comprobado directamente en `separar_por_estado`: `ValueError` |

La política de este laboratorio permite archivos vacíos sin error. Esa decisión es **contextual**: una fuente diaria obligatoria podría necesitar detener el procesamiento si no entrega registros.

## 13. Estructura relevante al concluir las implementaciones

```text
data-engineering-lab/
├── data/
│   ├── incoming/ventas.csv
│   └── test_cases/
│       ├── ventas_cantidad_invalida.csv
│       ├── ventas_estructura_invalida.csv
│       └── ventas_sin_registros.csv
├── docs/guides/DE05_pandas_guia.md
├── src/
│   ├── main.py
│   ├── extract/csv_extractor.py
│   ├── contracts/ventas_contract.py
│   ├── config/logging_config.py
│   ├── transform/
│   │   ├── __init__.py
│   │   └── ventas_transformer.py
│   └── quality/
│       ├── __init__.py
│       ├── ventas_quality.py
│       └── ventas_policy.py
└── requirements.txt
```

No creamos módulos adicionales de persistencia, calidad avanzada ni orquestación: no hacen falta para resolver el problema actual.

## 14. Errores frecuentes, aprendizajes y decisiones

- **Confundir transformación con calidad:** convertir `-5` a número es válido técnicamente; aprobar `-5` como cantidad de venta no lo es bajo esta regla.
- **Perder el valor original con `coerce`:** mantener `records` y relacionar por `source_row_number` permite recuperar la evidencia.
- **Llamar «válidas» a las filas sin nulos:** la calidad involucra más reglas que una conversión o ausencia de valores faltantes.
- **Eliminar duplicados por defecto:** `keep=False` permite identificar todas las filas involucradas y enviarlas a revisión.
- **Confundir `logger.error` con fallo del proceso:** sin `raise`, un error capturado puede terminar con código `0`.
- **Simplificar accidentalmente el logger:** durante DE-05 se detectó que una configuración con `logging.basicConfig()` había reemplazado el registro a consola **y** archivo. Se restauró la configuración con `setup_logging(PROJECT_ROOT)` y `FileHandler`.
- **Usar el índice de Pandas para rastrear el CSV:** preferir una referencia explícita que sobreviva a filtros y uniones; en un entorno con múltiples lotes hará falta contextualizarla por archivo/lote.
- **Guardar múltiples `main` operativos:** los experimentos de `main_pandas_inicial.py` quedan documentados en las secciones 5 a 7; la versión oficial es `src/main.py`.
- **Trabajar con un módulo antiguo importado:** reiniciar el intérprete interactivo al editar archivos de módulos.

## 15. Cierre verificado del bloque (18 de octubre de 2026)

**DE-05: terminado e integrado en `main`.** En `data/incoming/ventas.csv` se verificaron 18 registros: **11 aptos, 5 rechazados y 2 en revisión**, con salida `0`. Con `data/test_cases/ventas_cantidad_invalida.csv` se observaron 18 registros: **8 aptos, 8 rechazados y 2 en revisión**.

Pruebas adicionales: archivo inexistente → `FileNotFoundError` y código `1`; fila con menos campos → `ValueError` y código `1`; CSV con encabezados válidos pero sin registros → `WARNING` y código `0`. La comprobación de campos sobrantes fue validada durante el trabajo del extractor.

Se conservó el logger centralizado de DE-04 con escritura en consola y `logs/pipeline.log` mediante `setup_logging(PROJECT_ROOT)`; los errores críticos se registran y se vuelven a lanzar con `raise`. Se utiliza `data/incoming/ventas.csv` como ruta habitual del pipeline. Las tres salidas se preparan **en memoria**, sin cargar aún PostgreSQL.

**Git:** rama `transformacion-pandas`; commit funcional `1756a15`; merge local a `main` `e8c32e9`; `origin/main` sincronizado; rama local eliminada. Por ahora, el laboratorio usa ramas y merge local sin Pull Request.

**Documentación operativa pendiente de versionar:** actualizar `PROJECT_STATE.md` y registrar ese cambio en el repositorio. Esta guía documenta el código y las pruebas de DE-05; el estado operativo es un documento distinto.

**Siguiente bloque propuesto:** DE-06 — Carga y persistencia inicial en PostgreSQL. Introducir gradualmente destinos RAW y tratamiento de rechazados/revisión; después, cuando exista la necesidad, estudiar estrategias de carga, trazabilidad entre lotes e idempotencia.
