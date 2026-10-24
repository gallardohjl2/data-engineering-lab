# DE-06 — Persistencia PostgreSQL, calidad, transacciones e idempotencia

**Guía para alumnos · versión 1.1 · unidad de carga full completada; bloque DE-06 en progreso**

> Esta guía describe el laboratorio ejecutado y verificado. Las cargas append, incremental, watermarks y control de lotes **no están implementadas todavía**. Los ejemplos de fallo intencional son solo para la base de pruebas.

## 1. Objetivos de aprendizaje

Al finalizar esta unidad el estudiante podrá:

- Identificar qué parte de un pipeline corresponde a extracción, calidad y persistencia.
- Crear tablas PostgreSQL adecuadas para datos aceptados y para registros problemáticos con evidencia original.
- Conectar Python a PostgreSQL mediante Psycopg 3 y variables de entorno.
- Explicar qué es una conexión, un cursor, una transacción y la diferencia entre `COMMIT` y `ROLLBACK`.
- Diferenciar atomicidad de idempotencia y carga full de append e incremental.
- Construir una carga full transaccional usando **una sola conexión** para limpiar y cargar ambas tablas.
- Registrar errores de base de datos con `logger.exception()` y propagarlos con `raise`.
- Verificar resultados con SQL y reproducir de forma segura una prueba de rollback.

## 2. Punto de partida: ¿por qué persistir?

Al terminar DE-05, el pipeline de `data/incoming/ventas.csv` genera tres salidas en memoria:

| Resultado | Registros | Destino en DE-06 |
|---|---:|---|
| `APTO` | 11 | `raw.ventas` |
| `RECHAZADO` | 5 | `raw.ventas_problemas` |
| `REVISION` | 2 | `raw.ventas_problemas` |

```text
ventas.csv
   ↓
extract_csv() y contrato estructural
   ↓
transform_ventas() → diagnóstico → política de calidad
   ↓
   ├── df_aptos_final ───────────────────→ raw.ventas
   ├── df_rechazados_final ──┐
   └── df_revision_final ────┴────────────→ raw.ventas_problemas
                                PostgreSQL: una conexión y una transacción
```

**Precisión de arquitectura:** aunque el esquema se llama `raw`, `raw.ventas` recibe registros **APTOS ya transformados**. No es una copia fiel de todos los bytes de origen. Los problemáticos conservan los valores originales en texto. Es una decisión pedagógica provisional que deberá revisarse al evolucionar el diseño del warehouse.

## 3. Infraestructura y estructura relevante

El laboratorio utiliza PostgreSQL `16-bookworm` en Docker, con base `warehouse`, esquema `raw` y volumen persistente. SQL Server y pgAdmin también están disponibles mediante Docker Compose.

- Python desde Windows: `localhost:5433` → PostgreSQL en Docker `5432`.
- pgAdmin ejecutado en Docker: servicio `postgres-warehouse`, puerto `5432`.
- La instancia de PostgreSQL instalada separadamente en Windows **no es** el destino de este laboratorio.
- pgAdmin se comprobó en `localhost:8080` durante el trabajo; el `compose.yaml` compartido muestra `5050:80`. Verificar el mapeo efectivo con `docker compose ps` y resolver esa discrepancia en el repositorio antes de enseñar la instalación desde cero.
- Schemas de la base: `raw`, `stage`, `warehouse`, `marts` y `public`.

```text
data-engineering-lab/
├── .env                            # secreto local; no versionar
├── compose.yaml
├── requirements.txt
├── postgres/init/
│   ├── 01-create-schemas.sql
│   ├── 02-create-raw-ventas.sql
│   └── 03-create-raw-ventas-problemas.sql
├── data/incoming/ventas.csv
├── src/
│   ├── main.py
│   ├── config/logging_config.py
│   ├── extract/csv_extractor.py
│   ├── transform/ventas_transformer.py
│   ├── quality/ventas_quality.py
│   ├── quality/ventas_policy.py
│   └── load/
│       ├── __init__.py
│       └── postgres_loader.py
└── docs/guides/DE06_postgresql_guia.md
```

En el Compose examinado no existe montaje de `postgres/init/` hacia `/docker-entrypoint-initdb.d`. Los scripts SQL se ejecutaron manualmente en pgAdmin. **Guardar scripts en esa carpeta no los ejecuta por sí solo.**

## 4. Contratos de destino: SQL

### 4.1 Registros aptos: `raw.ventas`

Guardar como `postgres/init/02-create-raw-ventas.sql` y ejecutar en Query Tool sobre `warehouse`:

```sql
CREATE TABLE IF NOT EXISTS raw.ventas (
    source_row_number BIGINT NOT NULL,
    estado_calidad TEXT NOT NULL,
    venta_id TEXT NOT NULL,
    linea_id TEXT NOT NULL,
    fecha DATE NOT NULL,
    cliente_id TEXT,
    producto_id TEXT,
    sucursal_id TEXT,
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    descuento_pct INTEGER NOT NULL
);
```

- `DATE`: los registros aptos poseen fecha válida y no necesitamos hora en esta unidad.
- `NUMERIC(12,2)`: contrato de destino para el precio; el DataFrame de esta unidad utiliza `float64` y convertimos a `float` al insertar. En escenarios monetarios exigentes convendría introducir `Decimal` y controles de precisión.
- `venta_id` y `linea_id` son `TEXT`: los códigos de negocio no deberían perder ceros iniciales.
- `source_row_number` señala la posición lógica en el archivo; **no** es un ID global entre archivos o lotes.
- Por ahora no hay clave primaria ni restricciones de unicidad; no asumir que `CREATE TABLE IF NOT EXISTS` valida la estructura de una tabla ya existente.

### 4.2 Registros con problemas: `raw.ventas_problemas`

Guardar como `postgres/init/03-create-raw-ventas-problemas.sql`:

```sql
CREATE TABLE IF NOT EXISTS raw.ventas_problemas (
    source_row_number BIGINT NOT NULL,
    motivos_calidad TEXT[] NOT NULL,
    tiene_problemas BOOLEAN NOT NULL,
    estado_calidad TEXT NOT NULL,
    venta_id TEXT,
    linea_id TEXT,
    fecha TEXT,
    cliente_id TEXT,
    producto_id TEXT,
    sucursal_id TEXT,
    cantidad TEXT,
    precio_unitario TEXT,
    descuento_pct TEXT,
    CONSTRAINT chk_estado_ventas_problemas
        CHECK (estado_calidad IN ('RECHAZADO', 'REVISION'))
);
```

Aquí `fecha`, `cantidad` y `precio_unitario` son `TEXT` deliberadamente: valores como `fecha_invalida`, `-1`, precio vacío o `ABC` se deben preservar para investigación. `motivos_calidad` es `TEXT[]`, un arreglo PostgreSQL que puede contener una o varias razones.

Ambas tablas se crearon y verificaron en pgAdmin. Evitar publicar credenciales; `.env` debe quedar fuera de Git. Comprobar con `git ls-files -- .env`.

## 5. Dependencias y conexión

Versiones observadas durante la unidad:

```text
pandas==3.0.6
psycopg[binary]==3.3.6
python-dotenv==1.2.4
```

Instalar en el entorno virtual:

```powershell
python -m pip install -r requirements.txt
```

En `src/load/postgres_loader.py`:

```python
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def conectar_postgres():
    """Establece una conexión con PostgreSQL."""
    dbname = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    if not all([dbname, user, password]):
        raise ValueError("Faltan variables de configuración para PostgreSQL.")

    conexion = psycopg.connect(
        host="localhost",
        port=5433,
        dbname=dbname,
        user=user,
        password=password,
    )
    return conexion
```

`__file__` identifica el archivo del módulo; `.parent.parent.parent` sube desde `src/load/` a la raíz del proyecto. `load_dotenv()` lee el archivo de variables, `os.getenv()` consulta sus nombres y `psycopg.connect()` crea la conexión. Los valores de host/puerto están fijados para Python ejecutado en Windows en este laboratorio.

Un cursor ejecuta SQL, `fetchone()` obtiene una fila (por ejemplo `(1,)` con `SELECT 1`) y `with conexion.cursor()` cierra el cursor al salir. **El cursor no es dueño de la transacción global.**

## 6. Cargadores con una conexión compartida

El diseño inicial abría una conexión dentro de `cargar_ventas_aptas()`. Se cambió porque eso impedía revertir juntas las cargas de aptos, rechazados y revisión si una operación posterior fallaba.

En la versión vigente, las funciones **reciben `conexion`**, ejecutan SQL parametrizado y no llaman a `commit()`, `rollback()` ni `close()`.

Agregar estas funciones debajo de `conectar_postgres()` en `src/load/postgres_loader.py`:

```python
def cargar_ventas_aptas(df_aptos, conexion):
    """Inserta los registros aptos en raw.ventas."""
    sql = """
        INSERT INTO raw.ventas (
            source_row_number, estado_calidad, venta_id, linea_id,
            fecha, cliente_id, producto_id, sucursal_id,
            cantidad, precio_unitario, descuento_pct
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    with conexion.cursor() as cursor:
        for fila in df_aptos.itertuples(index=False):
            valores = (
                int(fila.source_row_number),
                fila.estado_calidad,
                fila.venta_id,
                fila.linea_id,
                fila.fecha.date(),
                fila.cliente_id,
                fila.producto_id,
                fila.sucursal_id,
                int(fila.cantidad),
                float(fila.precio_unitario),
                int(fila.descuento_pct),
            )
            cursor.execute(sql, valores)


def cargar_ventas_problemas(df_problemas, conexion):
    """Inserta rechazados o revisión conservando valores originales."""
    sql = """
        INSERT INTO raw.ventas_problemas (
            source_row_number, motivos_calidad, tiene_problemas,
            estado_calidad, venta_id, linea_id, fecha,
            cliente_id, producto_id, sucursal_id,
            cantidad, precio_unitario, descuento_pct
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    with conexion.cursor() as cursor:
        for fila in df_problemas.itertuples(index=False):
            valores = (
                int(fila.source_row_number),
                fila.motivos_calidad,
                bool(fila.tiene_problemas),
                fila.estado_calidad,
                fila.venta_id,
                fila.linea_id,
                fila.fecha,
                fila.cliente_id,
                fila.producto_id,
                fila.sucursal_id,
                fila.cantidad,
                fila.precio_unitario,
                fila.descuento_pct,
            )
            cursor.execute(sql, valores)
```

- `itertuples(index=False)` itera filas sin agregar el índice de Pandas.
- `cursor.execute(sql, valores)` utiliza marcadores `%s` y evita concatenar datos dentro del SQL.
- Las fechas de aptos se convierten a `date`; los valores inválidos de problemáticos **no** se convierten.
- Psycopg adapta la lista Python `motivos_calidad` al arreglo `TEXT[]` de PostgreSQL; se comprobó expresamente la adaptación con `SELECT %s::TEXT[]`.
- Una inserción por fila favorece comprensión; para grandes volúmenes sería razonable evaluar `executemany()` o `COPY` mediante mediciones.

## 7. Carga full transaccional e idempotencia

### 7.1 Problema: los `INSERT` se acumulan

Sin estrategia de repetición, una segunda ejecución del mismo CSV insertaría otros 18 registros y produciría 36. No había restricciones de unicidad que lo impidieran.

- **Full/reemplazo:** vuelve a cargar todo el conjunto de datos.
- **Append:** agrega registros al destino; no implica detectar novedades por sí mismo.
- **Incremental:** selecciona solo los registros nuevos o modificados por algún criterio; puede utilizar `INSERT`, `UPDATE` o `UPSERT`.
- **Idempotencia:** repetir la misma operación con iguales entradas deja el mismo estado lógico final.
- **Atomicidad:** o se confirman todas las operaciones de una transacción o se revierten todas.

La decisión actual es **full transaccional** para dos tablas dedicadas a un único CSV de prueba. No confundir idempotencia con incrementalidad.

### 7.2 Añadir limpieza en el loader

```python
def limpiar_ventas(conexion):
    """Vacía las tablas de ventas antes de una carga full."""
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE raw.ventas, raw.ventas_problemas")
```

Esta función no abre ni confirma una transacción por su cuenta.

### 7.3 Coordinar todo desde `main.py`

Importar en `main.py`:

```python
import psycopg

from src.load.postgres_loader import (
    conectar_postgres,
    limpiar_ventas,
    cargar_ventas_aptas,
    cargar_ventas_problemas,
)
```

El pipeline **ya había** extraído, transformado, diagnosticado, clasificado y preparado `df_aptos_final`, `df_rechazados_final` y `df_revision_final`. En ese punto, dentro del `try` principal, utilizar:

```python
# Persistencia de todas las salidas en una única transacción
with conectar_postgres() as conexion:
    limpiar_ventas(conexion)
    cargar_ventas_aptas(df_aptos_final, conexion)
    cargar_ventas_problemas(df_rechazados_final, conexion)
    cargar_ventas_problemas(df_revision_final, conexion)

logger.info(
    "Persistencia completada: %s aptos, %s rechazados y %s en revisión.",
    len(df_aptos_final),
    len(df_rechazados_final),
    len(df_revision_final),
)
```

**La ubicación del mensaje importa:** se registra después del `with`, cuando ya pudo confirmarse la transacción. El `with` de Psycopg ejecuta `COMMIT` si no sale ninguna excepción y `ROLLBACK` si alguna sale. Si el SQL falla dentro del bloque, el error debe propagarse; capturarlo y ocultarlo **dentro** podría impedir el comportamiento esperado.

En el `try` principal de `main.py`, agregar a los `except FileNotFoundError` y `except ValueError` ya existentes:

```python
except psycopg.Error:
    logger.exception("Error durante la conexión o persistencia en PostgreSQL.")
    raise
```

`logger.exception()` guarda mensaje y traceback; `raise` relanza la excepción para que el pipeline no aparente éxito. `raise` aquí **no es** quien ejecuta el rollback: lo hace el administrador de contexto al salir con error. El `finally` existente registra el final de la ejecución, pero ese mensaje por sí solo no implica éxito.

**Límite:** este `except` cubre excepciones Psycopg; otros errores Python (`TypeError`, `AttributeError`, etc.) también provocan rollback si salen del `with`, aunque no queden registrados por ese `except` específico.

## 8. Ejecución y comprobación de la carga

Desde PowerShell, raíz del repositorio y entorno virtual activado:

```powershell
python -m src.main
```

`-m` ejecuta el módulo dentro de la estructura de paquetes. La carga final se verificó con:

```sql
SELECT 'APTO' AS estado, COUNT(*) AS total
FROM raw.ventas
UNION ALL
SELECT estado_calidad, COUNT(*)
FROM raw.ventas_problemas
GROUP BY estado_calidad;
```

| Estado | Resultado comprobado |
|---|---:|
| APTO | 11 |
| RECHAZADO | 5 |
| REVISION | 2 |
| **Total** | **18** |

Para inspeccionar la trazabilidad y la evidencia:

```sql
SELECT source_row_number, estado_calidad, motivos_calidad,
       venta_id, fecha, cantidad, precio_unitario
FROM raw.ventas_problemas
ORDER BY source_row_number;
```

Los siete registros observados incluyeron:

| Fila fuente | Estado | Motivo | Evidencia |
|---:|---|---|---|
| 8 | RECHAZADO | Fecha inválida | `fecha_invalida` |
| 11 | RECHAZADO | Cantidad inválida | `-1` |
| 12 | RECHAZADO | Precio inválido | vacío |
| 14 | RECHAZADO | Precio inválido | `ABC` |
| 15 | RECHAZADO | Descuento inválido | motivo conservado |
| 16 | REVISION | Clave duplicada | venta `1015` |
| 17 | REVISION | Clave duplicada | venta `1015` |

**Idempotencia comprobada:** el usuario ejecutó la carga full dos veces con el mismo CSV y después de la segunda ejecución los conteos se mantuvieron en 11/5/2. Esto verifica idempotencia básica **del contenido** con esos datos, no una garantía universal para otras fuentes o metadatos.

## 9. Transacciones, bloqueos y pruebas de rollback

### 9.1 `BEGIN`, Auto-commit, `COMMIT` y `ROLLBACK`

- Fuera de una transacción explícita, un cliente SQL con Auto-commit activado confirma cada operación exitosa.
- `BEGIN` inicia una transacción explícita que se cierra con `COMMIT` o `ROLLBACK`.
- PostgreSQL permite revertir `TRUNCATE` dentro de una transacción.
- `TRUNCATE` adquiere un bloqueo `ACCESS EXCLUSIVE`: otra sesión que intente leer la tabla puede quedarse esperando hasta que se confirme o revierta la transacción.

**Observación real:** al ejecutar `BEGIN; TRUNCATE ...;` desde pgAdmin, una consulta en otra sesión quedó esperando. Al finalizar la transacción se liberó el bloqueo. Esto no prueba por sí solo el estado del interruptor Auto-commit del cliente.

### 9.2 Prueba controlada: revertir solo el vaciado

En **una misma sesión** de Query Tool, sobre las tablas de laboratorio:

```sql
BEGIN;
TRUNCATE TABLE raw.ventas, raw.ventas_problemas;
SELECT COUNT(*) FROM raw.ventas;           -- 0 dentro de la transacción
SELECT COUNT(*) FROM raw.ventas_problemas; -- 0 dentro de la transacción
ROLLBACK;
```

La verificación posterior devolvió nuevamente 11 aptos y 7 problemáticos.

### 9.3 Prueba controlada: error después de insertar

Solo en este laboratorio, en una sesión dedicada:

```sql
BEGIN;
TRUNCATE TABLE raw.ventas, raw.ventas_problemas;

INSERT INTO raw.ventas (
    source_row_number, estado_calidad, venta_id, linea_id,
    fecha, cantidad, precio_unitario, descuento_pct
) VALUES (999, 'APTO', 'PRUEBA', '1', '2026-09-01', 1, 100, 0);

-- Fallo intencional: cantidad es NOT NULL
INSERT INTO raw.ventas (
    source_row_number, estado_calidad, venta_id, linea_id,
    fecha, cantidad, precio_unitario, descuento_pct
) VALUES (1000, 'APTO', 'PRUEBA_ERROR', '1', '2026-09-01', NULL, 100, 0);
```

La segunda inserción produjo un error de restricción `NOT NULL`. En la **misma conexión** se ejecutó `ROLLBACK;` y se verificó que los 18 registros anteriores seguían presentes y que `venta_id='PRUEBA'` no permaneció almacenado.

**Alcance de la evidencia:** esta prueba demuestra la atomicidad de PostgreSQL; no es una simulación de fallo insertando mediante `src.main` y su `except` integrado.

## 10. Pruebas del logger y propagación de errores

Se comprobó en una llamada independiente que una conexión con usuario y contraseña intencionalmente erróneos provocaba `psycopg.OperationalError` (autenticación rechazada). La conexión real del laboratorio no se modificó.

También se creó temporalmente `prueba_logger.py` para estudiar `logger.exception()` y `raise`:

```python
import logging
from pathlib import Path
import psycopg
from src.config.logging_config import setup_logging

setup_logging(Path(__file__).resolve().parent)
logger = logging.getLogger(__name__)

try:
    raise psycopg.OperationalError("Fallo simulado de conexión")
except psycopg.Error:
    logger.exception("Error durante la conexión o persistencia en PostgreSQL.")
    raise
```

El mensaje de error y traceback aparecieron en consola y en `logs/pipeline.log`. Que la traza aparezca dos veces en consola es coherente: una la imprime `logger.exception()` y otra el intérprete al propagarse la excepción no capturada. Las pruebas temporales `prueba_logger.py` y `prueba_rollback.py` fueron destinadas a eliminarse después de su uso, no forman parte del pipeline.

## 11. Errores y decisiones relevantes

| Situación | Causa / aprendizaje |
|---|---|
| `psycopg.OperationalError` por contraseña inválida | La conexión llega a PostgreSQL, pero falla la autenticación; revisar `.env` sin revelar secretos. |
| Error SQL `NOT NULL` | La base protege el contrato del destino; dentro de la transacción, ejecutar `ROLLBACK`. |
| Consulta en otra pestaña queda esperando | `TRUNCATE` mantiene bloqueo fuerte mientras su transacción sigue abierta. |
| `SyntaxError: unterminated string literal` en `python -c` | Combinación complicada de comillas de PowerShell y Python; para enseñar es más claro un script temporal. |
| Traceback duplicado en consola | `logger.exception()` y el intérprete muestran la misma excepción en momentos distintos. |
| Duplicados al repetir un `INSERT` simple | No había idempotencia: se incorporó limpieza full dentro de la misma transacción. |
| `TRUNCATE ... CASCADE` sobre tablas relacionadas | Puede vaciar tablas dependientes no previstas; no usar automáticamente en producción. |
| `CREATE TABLE IF NOT EXISTS` | No compara un esquema existente con el contrato esperado. |

**Límites de la estrategia actual:**

- `TRUNCATE` vacía **ambas tablas completas**. Solo es correcto si son destinos exclusivos del conjunto completo de datos que reponemos.
- Las tablas actuales no tienen claves foráneas. Con relaciones futuras será necesario revisar dependencias y evitar `CASCADE` indiscriminado.
- Una carga full de millones de registros puede ocasionar bloqueos largos, I/O y reprocesamiento innecesario. Alternativas futuras: cargas incrementales, staging e intercambio controlado según requisitos.
- La idempotencia actual es lógica y limitada al CSV completo del laboratorio. No hay seguimiento de archivo, `batch_id`, checksum, CDC, UPSERT ni watermark.
- No mezclar esta unidad con modelado dbt ni orquestación Airflow; aparecerán después.

## 12. Git y documentación

Flujo Git vigente para el laboratorio: rama local → cambios y verificación → `git status` → commit → merge local a `main` → `push origin main` → eliminar rama. No se dispone de evidencia de la rama, los commits o el merge correspondientes a DE-06: **no inventarlos ni considerar Git cerrado**.

Comprobaciones seguras antes de registrar los archivos:

```powershell
git status
git branch --show-current
git ls-files -- .env
```

Revisar especialmente `src/main.py`, `src/load/postgres_loader.py`, `requirements.txt`, los scripts `postgres/init/`, esta guía y `PROJECT_STATE.md`. El archivo `.env` y logs operativos no deben subirse.

## 13. Actividad de comprobación para los alumnos

El estudiante debería poder explicar:

1. ¿Por qué los problemáticos se almacenan con `fecha`, `cantidad` y `precio_unitario` como texto?
2. ¿Por qué las funciones del loader reciben la conexión y no ejecutan `COMMIT`?
3. ¿Qué problema evita que `limpiar_ventas()` esté **dentro** de la misma transacción que las inserciones?
4. ¿Qué diferencia hay entre atomicidad e idempotencia?
5. ¿Por qué dos ejecuciones con el mismo CSV terminan en 18 registros y no en 36?
6. ¿Por qué una consulta puede bloquearse al intentar leer tablas truncadas desde otra conexión?
7. ¿Qué añade `logger.exception()` a `logger.error()` y para qué sirve `raise`?
8. ¿Cuándo usaríamos append o incremental en vez de full?

## 14. Siguiente unidad de DE-06

La **carga full transaccional está implementada y verificada**. El bloque DE-06 general permanece abierto; la siguiente decisión didáctica es introducir un escenario de nuevos archivos o modificaciones que justifique append/incremental y diseñar un control explícito de repetición de lotes sin anticipar soluciones complejas. Revisar el estado del repositorio y concluir la documentación/Git antes de declarar cerrado el bloque.
