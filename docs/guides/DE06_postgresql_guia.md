# DE-06 — Persistencia PostgreSQL, calidad, transacciones e idempotencia

**Guía para alumnos · versión 2.1 · FULL y APPEND implementadas, verificadas y publicadas en GitHub; INCREMENTAL pendiente**

> Esta versión conserva las pruebas de FULL de la guía 1.1 e incorpora los cambios reales de APPEND. INCREMENTAL, watermarks, control formal de lotes y reconciliación de correcciones **continúan pendientes**. Los ejemplos de fallo intencional se realizan solamente en el laboratorio.

## 1. Objetivos de aprendizaje

Al finalizar esta unidad el estudiante podrá:

- Identificar qué parte de un pipeline corresponde a extracción, calidad y persistencia.
- Crear tablas PostgreSQL adecuadas para datos aceptados y para registros problemáticos con evidencia original.
- Conectar Python a PostgreSQL mediante Psycopg 3 y variables de entorno.
- Explicar qué es una conexión, un cursor, una transacción y la diferencia entre `COMMIT` y `ROLLBACK`.
- Diferenciar atomicidad de idempotencia y carga full de append e incremental.
- Construir una carga FULL transaccional usando **una sola conexión** para limpiar y cargar ambas tablas.
- Construir APPEND con claves de unicidad diferenciadas y protección frente a reprocesamiento por SHA-256.
- Explicar los parámetros, resultados y ubicación exacta de cada función de carga.
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
├── data/incoming/ventas_dia_2.csv
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

## 4. Contratos de destino: SQL (versión actual)

**Ubicación exacta:** `postgres/init/02-create-raw-ventas.sql`. Copiar el siguiente bloque como contenido completo del script para una **instalación nueva**. En la base existente la restricción se agregó con `ALTER TABLE`; `CREATE TABLE IF NOT EXISTS` no modifica tablas existentes.

### 4.1 `raw.ventas`: datos aptos

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
    descuento_pct INTEGER NOT NULL,

    CONSTRAINT uq_raw_ventas_clave
        UNIQUE (venta_id, linea_id)
);
```

`venta_id` y `linea_id` son códigos, por eso se almacenan como `TEXT`. `UNIQUE (venta_id, linea_id)` evita duplicar una línea de venta entre registros aptos: `venta_id` puede repetirse con otra `linea_id`. `DATE` exige fecha válida y `NUMERIC(12,2)` es el contrato de precio. En este laboratorio la conversión actual de precio usa `float`; para dinero en producción convendría evaluar `Decimal`.

**Ubicación:** pgAdmin, base `warehouse`, Query Tool, **solo sobre una tabla que exista sin esta restricción** (fue ejecutado en el laboratorio):

```sql
ALTER TABLE raw.ventas
ADD CONSTRAINT uq_raw_ventas_clave
UNIQUE (venta_id, linea_id);
```

### 4.2 `raw.ventas_problemas`: evidencia e identidad de observación

**Ubicación exacta:** `postgres/init/03-create-raw-ventas-problemas.sql`. Contenido completo del script para una instalación nueva:

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
    archivo_origen TEXT,
    hash_archivo CHAR(64) NOT NULL,

    CONSTRAINT chk_estado_ventas_problemas
        CHECK (estado_calidad IN ('RECHAZADO', 'REVISION')),

    CONSTRAINT uq_ventas_problemas_archivo_fila
        UNIQUE (hash_archivo, source_row_number)
);
```

Aquí `fecha`, `cantidad` y `precio_unitario` son `TEXT` para conservar valores originales inválidos. `motivos_calidad` almacena una lista de motivos como `TEXT[]`. **No** se utiliza `(venta_id, linea_id)` como clave única en esta tabla: las filas originales 16 y 17 de la venta 1015 deben conservarse ambas. La identidad usada para evitar reprocesamiento es `(hash_archivo, source_row_number)`.

**Evolución aplicada a la base ya existente**, en este orden: primero se agregó `archivo_origen TEXT`; los siete registros históricos se actualizaron a `ventas.csv`; luego se agregó `hash_archivo CHAR(64)` (inicialmente nullable); se completó el hash original y se comprobaron nulos y duplicados antes de activar restricciones. No ejecutar nuevamente esos `ALTER TABLE` si la base ya tiene las columnas.

```sql
-- Paso histórico 1 (solo cuando NO existe la columna)
ALTER TABLE raw.ventas_problemas
ADD COLUMN archivo_origen TEXT;

-- Paso histórico 2: completar el origen conocido
UPDATE raw.ventas_problemas
SET archivo_origen = 'ventas.csv'
WHERE archivo_origen IS NULL;

-- Paso histórico 3 (solo cuando NO existe la columna)
ALTER TABLE raw.ventas_problemas
ADD COLUMN hash_archivo CHAR(64);

-- Paso histórico 4: completar la identidad si el CSV NO cambió desde su carga
UPDATE raw.ventas_problemas
SET hash_archivo = '5b4c753290accf7c8326f9e0e4b10e9e59db4faf1923a7c5b7af8c6b7a327c28'
WHERE archivo_origen = 'ventas.csv'
  AND hash_archivo IS NULL;
```

El SHA-256 anterior se **obtuvo en el laboratorio**, no es un valor universal. Si el archivo cambió tras la carga inicial, **no se debe asignar** a registros históricos sin evidencia del contenido original. Antes de imponer `NOT NULL` y `UNIQUE` se verificó:

```sql
SELECT COUNT(*) AS registros_sin_hash
FROM raw.ventas_problemas
WHERE hash_archivo IS NULL;

SELECT hash_archivo, source_row_number, COUNT(*) AS repeticiones
FROM raw.ventas_problemas
GROUP BY hash_archivo, source_row_number
HAVING COUNT(*) > 1;
```

Después de obtener **cero nulos y cero duplicados**, en la base existente se ejecutaron:

```sql
ALTER TABLE raw.ventas_problemas
ALTER COLUMN hash_archivo SET NOT NULL;

ALTER TABLE raw.ventas_problemas
ADD CONSTRAINT uq_ventas_problemas_archivo_fila
UNIQUE (hash_archivo, source_row_number);
```

**Precisión:** las restricciones de una tabla creada desde cero y las modificaciones a una tabla ya creada son procedimientos alternativos, no una secuencia para ejecutar ambos sin revisar el estado. Guardar scripts en `postgres/init/` tampoco los ejecuta automáticamente en el Docker Compose revisado: en nuestro laboratorio se ejecutaron por pgAdmin.

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

## 6. Loaders definitivos con conexión compartida

**Archivo:** `src/load/postgres_loader.py`. **Ubicación exacta:** mantener los imports y `conectar_postgres()` de la sección 5; colocar estas funciones **debajo** de `conectar_postgres()` en el mismo archivo. Es código de la implementación FULL + APPEND verificada.

```python
def limpiar_ventas(conexion):
    """Vacía ambas tablas al iniciar una carga FULL."""
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE raw.ventas, raw.ventas_problemas")


def cargar_ventas_aptas(df_aptos, conexion):
    """Inserta ventas aptas que no existan por clave de negocio."""
    sql = """
        INSERT INTO raw.ventas (
            source_row_number,
            estado_calidad,
            venta_id,
            linea_id,
            fecha,
            cliente_id,
            producto_id,
            sucursal_id,
            cantidad,
            precio_unitario,
            descuento_pct
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (venta_id, linea_id)
        DO NOTHING
    """
    registros_insertados = 0
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
            registros_insertados += cursor.rowcount
    return registros_insertados


def cargar_ventas_problemas(
    df_problemas,
    conexion,
    archivo_origen,
    hash_archivo,
):
    """Inserta rechazados/revisión con valores originales y trazabilidad."""
    sql = """
        INSERT INTO raw.ventas_problemas (
            source_row_number,
            motivos_calidad,
            tiene_problemas,
            estado_calidad,
            venta_id,
            linea_id,
            fecha,
            cliente_id,
            producto_id,
            sucursal_id,
            cantidad,
            precio_unitario,
            descuento_pct,
            archivo_origen,
            hash_archivo
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (hash_archivo, source_row_number)
        DO NOTHING
    """
    registros_insertados = 0
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
                archivo_origen,
                hash_archivo,
            )
            cursor.execute(sql, valores)
            registros_insertados += cursor.rowcount
    return registros_insertados
```

**Qué recibe y devuelve cada función:**

| Función | Parámetros | Retorno | Responsabilidad |
|---|---|---|---|
| `conectar_postgres` | Ninguno | Conexión Psycopg | Abrir PostgreSQL con `.env` |
| `limpiar_ventas` | `conexion` | `None` implícito | Vaciar ambos destinos solo en FULL |
| `cargar_ventas_aptas` | `df_aptos`, `conexion` | `int` | Insertados reales de aptos |
| `cargar_ventas_problemas` | `df_problemas`, `conexion`, `archivo_origen`, `hash_archivo` | `int` | Insertados reales de problemas |

`itertuples(index=False)` itera registros sin el índice de Pandas. Cada `%s` es un marcador seguro de Psycopg: la lista de columnas, marcadores y valores debe tener la misma longitud (11 o 15). `ON CONFLICT DO NOTHING` no reemplaza registros existentes. `cursor.rowcount` suma **1 si se insertó y 0 si se omitió**. Ninguna función del loader hace `commit()`, `rollback()` ni `close()`: `main.py` gestiona toda la transacción. La adaptación de `motivos_calidad` desde lista Python a `TEXT[]` fue verificada previamente. Para grandes volúmenes se evaluarán técnicas por lotes o `COPY` cuando haga falta.

## 7. Carga full transaccional e idempotencia

### 7.1 Problema: los `INSERT` se acumulan

En el diseño **inicial**, sin limpieza ni reglas de unicidad, una segunda ejecución insertaba otros 18 registros. Este fue el problema que motivó implementar FULL y, posteriormente, APPEND. La versión actual sí incorpora restricciones `UNIQUE`.

- **Full/reemplazo:** vuelve a cargar todo el conjunto de datos.
- **Append:** agrega registros al destino; no implica detectar novedades por sí mismo.
- **Incremental:** selecciona solo los registros nuevos o modificados por algún criterio; puede utilizar `INSERT`, `UPDATE` o `UPSERT`.
- **Idempotencia:** repetir la misma operación con iguales entradas deja el mismo estado lógico final.
- **Atomicidad:** o se confirman todas las operaciones de una transacción o se revierten todas.

FULL transaccional fue la primera solución didáctica; posteriormente se añadió APPEND idempotente. No confundir idempotencia con incrementalidad.

### 7.2 Añadir limpieza en el loader

```python
def limpiar_ventas(conexion):
    """Vacía las tablas de ventas antes de una carga full."""
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE raw.ventas, raw.ventas_problemas")
```

Esta función no abre ni confirma una transacción por su cuenta.

### 7.3 Integrar la carga desde `main.py`

**Archivo exacto:** `src/main.py`. **Ubicación:** dentro de `main()`, en el bloque `try` y después de producir `df_aptos_final`, `df_rechazados_final` y `df_revision_final` (ver código integral de la sección 15). Reemplazar el bloque antiguo de persistencia simple por:

```python
# Persistencia de las tres salidas en una sola transacción
with conectar_postgres() as conexion:
    if modo_carga == "full":
        limpiar_ventas(conexion)

    aptos_insertados = cargar_ventas_aptas(df_aptos_final, conexion)

    rechazados_insertados = cargar_ventas_problemas(
        df_rechazados_final,
        conexion,
        archivo_origen=archivo.name,
        hash_archivo=hash_archivo,
    )
    revision_insertados = cargar_ventas_problemas(
        df_revision_final,
        conexion,
        archivo_origen=archivo.name,
        hash_archivo=hash_archivo,
    )
```

Solo FULL llama a `limpiar_ventas`. En APPEND los registros que ya existen son omitidos. Psycopg confirma `COMMIT` al salir normalmente del `with`; si una excepción sale de ese bloque, revierte la transacción. **Los logs de éxito van después del `with`**. El comportamiento `FULL` reemplaza todas las filas de ambas tablas, por lo que se utiliza solo cuando el CSV representa el conjunto completo que debe permanecer.

## 8. Ejecutar FULL y APPEND y comprobar resultados

**Lugar:** terminal PowerShell en la raíz de `data-engineering-lab`, con `.venv` activado. En la versión actual `python -m src.main` ejecuta `main()` con valores por defecto: `archivo=VENTAS_FILE`, `modo_carga="full"`. **Precaución:** esto ejecuta `TRUNCATE` y no debe hacerse accidentalmente en una base compartida.

```powershell
# FULL del archivo por defecto, solo en este laboratorio
python -m src.main

# FULL explícito
python -c "from pathlib import Path; from src.main import main; main(archivo=Path('data/incoming/ventas.csv'), modo_carga='full')"

# APPEND con el segundo archivo
python -c "from pathlib import Path; from src.main import main; main(archivo=Path('data/incoming/ventas_dia_2.csv'), modo_carga='append')"
```

**Archivo:** `data/incoming/ventas_dia_2.csv`. Contenido completo utilizado en la práctica:

```csv
venta_id,linea_id,fecha,cliente_id,producto_id,sucursal_id,cantidad,precio_unitario,descuento_pct
2001,1,2026-09-08,1,101,1,2,450.00,0
2002,1,2026-09-08,2,102,2,1,1200.00,5
2003,1,2026-09-08,3,103,1,3,300.00,10
2004,1,2026-09-08,4,104,2,1,850.00,0
2005,1,2026-09-08,5,105,1,2,600.00,5
```

**Consulta en pgAdmin / `warehouse`**, después de cada ejecución:

```sql
SELECT 'APTO' AS estado, COUNT(*) AS total
FROM raw.ventas
UNION ALL
SELECT estado_calidad, COUNT(*) AS total
FROM raw.ventas_problemas
GROUP BY estado_calidad;
```

| Secuencia | APTO | RECHAZADO | REVISION | Total |
|---|---:|---:|---:|---:|
| FULL `ventas.csv` | 11 | 5 | 2 | 18 |
| Después: APPEND `ventas_dia_2.csv` | 16 | 5 | 2 | 23 |
| Repetir APPEND del mismo archivo | 16 | 5 | 2 | 23 |
| Repetir APPEND de `ventas.csv` sobre esos 23 | 16 | 5 | 2 | 23 |
| Volver a ejecutar FULL `ventas.csv` | 11 | 5 | 2 | 18 |
| Restaurar con APPEND `ventas_dia_2.csv` | 16 | 5 | 2 | 23 |

La secuencia se realizó y se comprobó con logs y consultas SQL. La tabla `raw.ventas` almacena 16 ventas aptas; `raw.ventas_problemas` almacena las 7 originales tras retirar las pruebas temporales.

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

## 11. Errores, decisiones y límites

| Situación | Aprendizaje |
|---|---|
| `psycopg.OperationalError` | Problema de conexión/autenticación; registrar la excepción sin mostrar secretos. |
| Error por columna `NOT NULL` | PostgreSQL protege el contrato; fuera del `with` se habrá efectuado rollback. |
| Otra sesión bloqueada durante TRUNCATE | `TRUNCATE` mantiene bloqueo fuerte hasta terminar la transacción. |
| `TypeError: ... missing ... archivo_origen` | Los argumentos se agregaron por error a `cargar_ventas_aptas`; se corrigió la firma y el INSERT, y se aplicó la trazabilidad únicamente a problemáticos. |
| Cantidad de `%s` incorrecta | Debe coincidir con el número de columnas y valores: 11 para aptos y 15 para problemáticos. |
| Encabezado del CSV con línea en blanco | La extracción identificó columnas faltantes; se quitó la línea vacía inicial del segundo archivo. |
| Reprocesamiento APPEND | Se omite la misma clave apta y la misma observación problemática sin error. |
| `CREATE TABLE IF NOT EXISTS` | No agrega restricciones a una tabla existente; se utilizaron `ALTER TABLE` y actualizaciones controladas. |

**Límites declarados:**

- `raw.ventas` omite una venta con igual `(venta_id, linea_id)` aunque el precio u otro dato haya sido corregido. En INCREMENTAL necesitaremos una política explícita de actualización/revisión; `DO NOTHING` no significa que el contenido sea igual.
- El hash SHA-256 identifica **bytes del archivo completo**, no una venta. Si cambia un solo byte, toda la versión recibe otro hash; observaciones problemáticas sin cambios también podrían conservarse otra vez bajo una versión nueva. Esto es una decisión de trazabilidad por versión.
- Archivo y hash se calculan en **lecturas separadas** (`extract_csv` y `archivo.read_bytes()`). Para producción deberá evitarse que el archivo cambie entre ambas lecturas (p. ej., entregas atómicas o snapshot estable).
- El nombre alternativo de un archivo renombrado pero idéntico **no se registra** en una nueva fila cuando el `ON CONFLICT` omite el registro. El hash sí permite reconocer el reprocesamiento.
- No hay tabla de control de lotes, watermark, reconciliación de correcciones ni interfaz CLI con argumentos `--modo` o `--archivo` todavía.
- FULL trunca ambas tablas enteras y toma bloqueos fuertes. Solo es adecuado para estos destinos dedicados del laboratorio. No introducir `TRUNCATE CASCADE` indiscriminadamente.
- El esquema `raw` para aptos contiene datos transformados; es una decisión provisional del laboratorio.

## 12. Git y GitHub: antecedentes de FULL

En este laboratorio se ha seguido un flujo sencillo por funcionalidad: actualizar `main`, crear una rama, implementar y verificar, preparar un commit selectivo, integrar la rama en `main`, publicar `main` y eliminar la rama terminada. No se aplicó Git Flow complejo ni se abrió Pull Request en este cierre: el merge fue **local** y se publicó después.

**Historial de FULL realmente registrado:**

| Hito | Referencia observada |
|---|---|
| Rama de FULL | `feature/de06-postgresql` |
| Commit de implementación FULL | `318341c` — `feat: implementar carga full transaccional en PostgreSQL` |
| Merge de FULL en `main` | `dbff254` — `Merge branch 'feature/de06-postgresql'` |

La siguiente sección de Git (18) reconstruye **todo el recorrido práctico de APPEND**, con comandos, explicaciones, verificaciones y errores encontrados. Se conserva esta sección para mostrar que FULL fue una unidad independiente y que APPEND evolucionó sobre su base.

**Higiene del repositorio:** `.env`, credenciales y logs no deben versionarse. Comprobar si `.env` está seguido por Git mediante `git ls-files -- .env`; una salida vacía es la esperada. Esta comprobación no sustituye la revisión general de secretos antes de publicar.

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
9. ¿Por qué cambia el hash cuando se modifica solo una fila?
10. ¿Por qué una venta con clave ya existente pero precio corregido no se actualiza con `DO NOTHING`?

## 14. APPEND — problema, diseño y evolución incremental de la solución

### 14.1 ¿Qué resuelve APPEND?

FULL reemplaza todos los registros de ambas tablas. Si llega otro CSV con cinco ventas nuevas, no queremos eliminar las 18 observaciones ya cargadas. APPEND **no ejecuta `limpiar_ventas()`** y utiliza restricciones de unicidad para incorporar solo filas nuevas según cada regla.

### 14.2 Identidades diferentes según destino

| Destino | Clave `UNIQUE` | Por qué |
|---|---|---|
| `raw.ventas` | `(venta_id, linea_id)` | Una sola línea de venta apta por clave de negocio |
| `raw.ventas_problemas` | `(hash_archivo, source_row_number)` | Varias observaciones pueden compartir la clave de negocio; conservar evidencia sin duplicar una misma fila de una versión |

La venta `1015`, línea `1`, aparece dos veces en las posiciones 16 y 17 del CSV. Ambas fueron clasificadas `REVISION`, se conservaron en problemas y **no** fueron insertadas como aptas. La restricción de aptos protege la unicidad de negocio; la de problemas protege la identidad de observación.

### 14.3 Introducir `modo_carga` y elegir el archivo

**Archivo:** `src/main.py`. **Ubicación:** firma de `main` (reemplazar la firma anterior); la validación va al comienzo del `try`, **antes** de extraer:

```python
def main(archivo: Path = VENTAS_FILE, modo_carga: str = "full") -> None:
    setup_logging(PROJECT_ROOT)
    logger.info("Inicio del pipeline.")
    try:
        if modo_carga not in ("full", "append"):
            raise ValueError(
                f"Modo de carga no válido: {modo_carga}. "
                "Los valores permitidos son 'full' y 'append'."
            )
        records = extract_csv(
            file_path=archivo,
            required_columns=REQUIRED_COLUMNS,
        )
        # A partir de aquí continúa la transformación existente.
```

`main()` recibe la ruta y el modo. La llamada por defecto sigue siendo FULL; con `modo_carga="append"` se conserva lo ya almacenado. El uso de `Path` ayuda a obtener `archivo.name` y a leer sus bytes para el hash.

### 14.4 Calcular SHA-256

**Archivo:** `src/main.py`. **Ubicación exacta:** `import hashlib` al principio con los imports estándar. Dentro de `main()`, justo **después de `extract_csv(...)`** y antes de `if records:`:

```python
hash_archivo = hashlib.sha256(
    archivo.read_bytes()
).hexdigest()

logger.info("SHA-256 del archivo: %s", hash_archivo)
logger.info("Extracción finalizada correctamente.")
```

`read_bytes()` lee bytes; `hashlib.sha256(...)` produce un digest de 256 bits y `hexdigest()` lo representa como 64 caracteres hexadecimales. Mismo contenido exacto → mismo hash, aunque cambie el nombre. Mismo nombre y contenido diferente → nuevo hash. También cambia si cambian los saltos de línea o la codificación. En archivos grandes leeríamos por bloques.

Práctica desde la raíz del repositorio:

```powershell
python -c "import hashlib; from pathlib import Path; archivo = Path('data/incoming/ventas.csv'); print(hashlib.sha256(archivo.read_bytes()).hexdigest())"
```

En la práctica el resultado fue:

```text
5b4c753290accf7c8326f9e0e4b10e9e59db4faf1923a7c5b7af8c6b7a327c28
```

La huella histórica solo es válida para los bytes originales de aquel archivo.

### 14.5 Conectar el hash al loader

**Archivo:** `src/load/postgres_loader.py`. Reemplazar la firma de `cargar_ventas_problemas` para recibir `archivo_origen` y `hash_archivo`, añadir esas dos columnas al `INSERT`, sumar sus `%s` y valores, y añadir `ON CONFLICT (hash_archivo, source_row_number) DO NOTHING`. **El código completo y definitivo está en la sección 6**; no modificar `cargar_ventas_aptas` para este cambio.

**Archivo:** `src/main.py`. Dentro del `with conectar_postgres() as conexion:`, llamar al loader dos veces con argumentos nombrados:

```python
rechazados_insertados = cargar_ventas_problemas(
    df_rechazados_final,
    conexion,
    archivo_origen=archivo.name,
    hash_archivo=hash_archivo,
)
revision_insertados = cargar_ventas_problemas(
    df_revision_final,
    conexion,
    archivo_origen=archivo.name,
    hash_archivo=hash_archivo,
)
```

`archivo_origen=archivo.name` usa un argumento con nombre: a la izquierda está el parámetro declarado en el loader; a la derecha, la expresión que devuelve el nombre del archivo. Lo mismo ocurre con `hash_archivo=hash_archivo`.

### 14.6 Contar insertados y omitidos

**Archivo:** `src/load/postgres_loader.py`. Las dos funciones de carga inicializan `registros_insertados = 0`, suman `cursor.rowcount` tras cada ejecución y devuelven el resultado con `return` (ver sección 6).

**Archivo:** `src/main.py`. **Ubicación exacta:** inmediatamente después del bloque de conexión:

```python
aptos_omitidos = len(df_aptos_final) - aptos_insertados
rechazados_omitidos = len(df_rechazados_final) - rechazados_insertados
revision_omitidos = len(df_revision_final) - revision_insertados

logger.info(
    "Persistencia completada: %s aptos, %s rechazados y %s en revisión insertados.",
    aptos_insertados,
    rechazados_insertados,
    revision_insertados,
)
logger.info(
    "Carga de aptos: %s procesados, %s insertados y %s omitidos por duplicidad.",
    len(df_aptos_final), aptos_insertados, aptos_omitidos,
)
logger.info(
    "Carga de rechazados: %s procesados, %s insertados y %s omitidos por duplicidad.",
    len(df_rechazados_final), rechazados_insertados, rechazados_omitidos,
)
logger.info(
    "Carga de revisión: %s procesados, %s insertados y %s omitidos por duplicidad.",
    len(df_revision_final), revision_insertados, revision_omitidos,
)
```

**Interpretación:** procesados = filas clasificadas en el DataFrame; insertados = `rowcount` real; omitidos = procesados menos insertados. El mensaje `Persistencia completada` informa **insertados**, no solo clasificados.

### 14.7 Pruebas de reenvío y versiones

Para la prueba se creó `data/incoming/ventas_prueba_problemas.csv`:

```csv
venta_id,linea_id,fecha,cliente_id,producto_id,sucursal_id,cantidad,precio_unitario,descuento_pct
3001,1,2026-09-09,1,101,1,-2,450.00,0
```

Se ejecutó por APPEND, se verificó la fila 3001 y se repitió sin modificar el CSV: log `1 procesado, 0 insertados y 1 omitido`. Luego se copió como `ventas_renombrado.csv` sin cambios de contenido: mismo hash, 0 insertados. Por último se cambió `cantidad` de `-2` a `-3` en el CSV copiado: hash diferente, 1 nueva observación insertada. Se retiraron después las dos filas de prueba para conservar los 7 problemáticos del conjunto original.

Comandos empleados:

```powershell
python -c "from pathlib import Path; from src.main import main; main(archivo=Path('data/incoming/ventas_prueba_problemas.csv'), modo_carga='append')"
Copy-Item 'data/incoming/ventas_prueba_problemas.csv' 'data/incoming/ventas_renombrado.csv'
python -c "from pathlib import Path; from src.main import main; main(archivo=Path('data/incoming/ventas_renombrado.csv'), modo_carga='append')"
```

Consultas de comprobación:

```sql
SELECT venta_id, source_row_number, archivo_origen, hash_archivo, cantidad
FROM raw.ventas_problemas
WHERE venta_id = '3001';

-- Limpieza únicamente de las dos observaciones didácticas
DELETE FROM raw.ventas_problemas
WHERE venta_id = '3001'
  AND archivo_origen IN ('ventas_prueba_problemas.csv', 'ventas_renombrado.csv')
RETURNING venta_id, cantidad, archivo_origen;
```

Para validar que no quedan duplicados por identidad de observación:

```sql
SELECT hash_archivo, source_row_number, COUNT(*) AS repeticiones
FROM raw.ventas_problemas
GROUP BY hash_archivo, source_row_number
HAVING COUNT(*) > 1;
```

Resultado esperado: **ninguna fila**. La prueba comprobó también FULL + APPEND y restauró los conteos: 16 aptos, 5 rechazados, 2 en revisión.

## 15. `src/main.py` — código completo del punto de entrada de FULL y APPEND

**Ubicación:** reemplazar/actualizar cuidadosamente el contenido de `src/main.py` **solo si se está reconstruyendo el laboratorio desde cero**, conservando los módulos de extracción, transformación y calidad trabajados en DE-04/DE-05. Este bloque se reconstruyó a partir del `main.py` compartido durante el desarrollo y sus modificaciones verificadas de logging. No es una implementación de los módulos importados.

```python
"""Punto de entrada principal del pipeline."""

import hashlib
import logging
from pathlib import Path

import psycopg

from src.config.logging_config import setup_logging
from src.contracts.ventas_contract import REQUIRED_COLUMNS
from src.extract.csv_extractor import extract_csv
from src.transform.ventas_transformer import transform_ventas
from src.quality.ventas_quality import (
    diagnosticar_calidad_detallada,
    construir_vista_investigacion,
)
from src.quality.ventas_policy import (
    aplicar_politica_calidad,
    separar_por_estado,
    preparar_aptos,
)
from src.load.postgres_loader import (
    conectar_postgres,
    cargar_ventas_aptas,
    cargar_ventas_problemas,
    limpiar_ventas,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENTAS_FILE = PROJECT_ROOT / "data" / "incoming" / "ventas.csv"
logger = logging.getLogger(__name__)


def main(
    archivo: Path = VENTAS_FILE,
    modo_carga: str = "full",
) -> None:
    """Coordina extracción, calidad y persistencia de ventas."""
    setup_logging(PROJECT_ROOT)
    logger.info("Inicio del pipeline.")

    try:
        if modo_carga not in ("full", "append"):
            raise ValueError(
                f"Modo de carga no válido: {modo_carga}. "
                "Los valores permitidos son 'full' y 'append'."
            )

        # Extracción
        records = extract_csv(
            file_path=archivo,
            required_columns=REQUIRED_COLUMNS,
        )

        # Identidad del contenido
        hash_archivo = hashlib.sha256(
            archivo.read_bytes()
        ).hexdigest()
        logger.info("SHA-256 del archivo: %s", hash_archivo)
        logger.info("Extracción finalizada correctamente.")

        if records:
            df_ventas = transform_ventas(records)
            logger.info("Transformación inicial de ventas finalizada correctamente.")

            df_diagnostico = diagnosticar_calidad_detallada(df_ventas)
            df_clasificado = aplicar_politica_calidad(df_diagnostico)
            df_aptos_final = preparar_aptos(df_ventas, df_clasificado)
            df_investigacion = construir_vista_investigacion(
                records, df_clasificado,
            )
            _, df_rechazados_final, df_revision_final = separar_por_estado(
                df_investigacion
            )

            total_registros = len(df_diagnostico)
            total_con_problemas = int(df_diagnostico["tiene_problemas"].sum())
            total_sin_problemas = total_registros - total_con_problemas
            logger.info(
                "Diagnóstico de calidad: %s registros analizados, "
                "%s con problemas y %s sin problemas detectados.",
                total_registros,
                total_con_problemas,
                total_sin_problemas,
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

            # Una conexión: un COMMIT o un ROLLBACK para las tres salidas
            with conectar_postgres() as conexion:
                if modo_carga == "full":
                    limpiar_ventas(conexion)

                aptos_insertados = cargar_ventas_aptas(
                    df_aptos_final, conexion,
                )
                rechazados_insertados = cargar_ventas_problemas(
                    df_rechazados_final,
                    conexion,
                    archivo_origen=archivo.name,
                    hash_archivo=hash_archivo,
                )
                revision_insertados = cargar_ventas_problemas(
                    df_revision_final,
                    conexion,
                    archivo_origen=archivo.name,
                    hash_archivo=hash_archivo,
                )

            aptos_omitidos = len(df_aptos_final) - aptos_insertados
            rechazados_omitidos = len(df_rechazados_final) - rechazados_insertados
            revision_omitidos = len(df_revision_final) - revision_insertados

            logger.info(
                "Persistencia completada: %s aptos, %s rechazados "
                "y %s en revisión insertados.",
                aptos_insertados, rechazados_insertados, revision_insertados,
            )
            logger.info(
                "Carga de aptos: %s procesados, %s insertados "
                "y %s omitidos por duplicidad.",
                len(df_aptos_final), aptos_insertados, aptos_omitidos,
            )
            logger.info(
                "Carga de rechazados: %s procesados, %s insertados "
                "y %s omitidos por duplicidad.",
                len(df_rechazados_final), rechazados_insertados, rechazados_omitidos,
            )
            logger.info(
                "Carga de revisión: %s procesados, %s insertados "
                "y %s omitidos por duplicidad.",
                len(df_revision_final), revision_insertados, revision_omitidos,
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
    except psycopg.Error:
        logger.exception("Error durante la conexión o persistencia en PostgreSQL.")
        raise
    finally:
        logger.info("Fin de la ejecución.")


if __name__ == "__main__":
    main()
```

**Diferencia entre definir y ejecutar:** `def main(...)` crea la función. `if __name__ == "__main__": main()` la llama si se usa `python -m src.main`, por defecto en FULL. En desarrollo APPEND se ejecutó mediante `python -c` importando `main` y pasando argumentos; en producción lo habitual es que un programador u orquestador (p. ej., Airflow cuando toque esa unidad) invoque un proceso parametrizado. Una CLI con `--archivo` y `--modo` es una **mejora propuesta, aún no implementada**.

**Límite de la gestión de errores:** `logger.exception` captura específicamente `psycopg.Error`; otros fallos Python también hacen rollback si salen del `with`, aunque pueden mostrarse sin ese mensaje particular. Si `records` está vacío, el diseño actual registra advertencia y no hace FULL: ese caso deberá discutirse como política antes de automatizar reemplazos.

## 16. Tabla-resumen de métodos y salidas

| Método / instrucción | Entrada principal | Resultado o efecto |
|---|---|---|
| `main(archivo, modo_carga)` | Ruta `Path`, modo `str` | Coordina el flujo, retorna `None` |
| `setup_logging(PROJECT_ROOT)` | Raíz del proyecto | Configura logging |
| `extract_csv(...)` | CSV y contrato | `records`: lista de diccionarios |
| `hashlib.sha256(...).hexdigest()` | Bytes del CSV | `hash_archivo`: `str` de 64 caracteres |
| `transform_ventas(records)` | Datos extraídos | `df_ventas` |
| `diagnosticar_calidad_detallada(df_ventas)` | DataFrame transformado | `df_diagnostico` |
| `aplicar_politica_calidad(df_diagnostico)` | Diagnóstico | `df_clasificado` |
| `preparar_aptos(...)` | Ventas + clasificación | `df_aptos_final` |
| `construir_vista_investigacion(...)` | Datos originales + estados | `df_investigacion` |
| `separar_por_estado(df_investigacion)` | Vista de investigación | Tupla: aptos de vista, rechazados, revisión |
| `conectar_postgres()` | Variables `.env` | Conexión Psycopg |
| `limpiar_ventas(conexion)` | Conexión | TRUNCATE, solo FULL |
| `cargar_ventas_aptas(...)` | APTOS y conexión | `int` insertados |
| `cargar_ventas_problemas(...)` | Problemáticos + conexión + identidad | `int` insertados |
| `cursor.rowcount` | Último INSERT de cursor | 1 insertado, 0 omitido (en este caso) |
| Salida de `with conectar_postgres()` | Resultado de las cargas | COMMIT al éxito / ROLLBACK ante excepción |

## 17. Infografía comparativa FULL y APPEND

**Archivo previsto dentro del repositorio:** `img/infografia_postgresql_full_vs_append.png`. La imagen se prepara como recurso didáctico del bloque; antes del commit comprobar su ubicación y que `.gitignore` no excluya `img/`.

![Infografía comparativa de la carga FULL y APPEND](../../img/infografia_postgresql_full_vs_append.png)

**Lectura sugerida:** primero identificar las salidas de extracción/calidad, luego observar que FULL ejecuta `TRUNCATE` y APPEND no, y finalmente comprobar que ambas comparten los mismos loaders, las claves de unicidad y una única transacción.

## 18. Git y GitHub — cierre reproducible de APPEND (caso real)

### 18.1 Objetivo didáctico y punto de partida

**Problema:** no basta con que la carga funcione en nuestra computadora; necesitamos un historial que permita identificar la funcionalidad, compartirla, repetir el laboratorio y no arrastrar ejercicios personales al repositorio remoto.

Antes de este cierre, FULL ya estaba integrado en `main` mediante `dbff254`. APPEND se desarrolló en la rama `feature/de06-append`. Había archivos propios de APPEND **y** modificaciones ajenas al bloque: un cambio en la guía DE-05, CSV usados como pruebas y scripts en `pruebas/`. Se acordó conservarlos localmente, pero **no incluirlos** en el commit de APPEND.

**Dónde ejecutar los comandos:** terminal PowerShell de VS Code, ubicada en la raíz `data-engineering-lab/`. Los resultados indicados como observados pertenecen al cierre real del proyecto; al reproducir la clase, cada estudiante tendrá hashes de commit distintos.

**Distinciones esenciales:**

- **Directorio de trabajo:** archivos y modificaciones visibles en el disco.
- **Staging area / índice:** selección para el próximo commit, controlada mediante `git add`.
- **Commit:** instantánea local registrada en una rama.
- **Rama local:** referencia que permite desarrollar APPEND sin alterar inmediatamente `main`.
- **`origin/main`:** referencia local del estado remoto conocido; se actualiza al traer/publicar cambios.
- **Stash:** almacenamiento temporal de cambios que todavía no queremos confirmar; no es un commit de la funcionalidad y no es un respaldo remoto.

### 18.2 Revisar los cambios antes de preparar el commit

```powershell
git branch --show-current
git status --short
git diff --check
```

`git branch --show-current` muestra en qué rama se trabaja (aquí, `feature/de06-append`). `git status --short` indica qué está modificado (`M`) y qué no sigue Git (`??`). `git diff --check` revisa problemas de espacios en los **cambios no preparados**. No prueba el código ni verifica el contenido funcional.

**Archivos detectados de APPEND:**

```text
 M PROJECT_STATE.md
 M docs/guides/DE06_postgresql_guia.md
 M postgres/init/02-create-raw-ventas.sql
 M postgres/init/03-create-raw-ventas-problemas.sql
 M src/load/postgres_loader.py
 M src/main.py
?? data/incoming/ventas_dia_2.csv
?? img/infografia_postgresql_full_vs_append.png
```

También existían cambios ajenos: `docs/guides/DE05_pandas_guia.md`, `docs/guides/DE05_pandas_guia_revisada.md`, `ventas_prueba_problemas.csv`, `ventas_renombrado.csv` y cinco archivos bajo `pruebas/`. Esos archivos se dejaron fuera del commit.

**Advertencias reales de `git diff --check`:**

| Aviso | Causa | Cómo se resolvió |
|---|---|---|
| `PROJECT_STATE.md:3` y `:5: trailing whitespace` | Dos espacios al final de líneas Markdown | Se eliminaron los espacios sobrantes; se conservó el texto |
| `02-create-raw-ventas.sql:17: trailing whitespace` | Espacio después de `descuento_pct INTEGER NOT NULL,` | Se eliminó únicamente el espacio final, **no la coma** |
| `DE06_postgresql_guia.md:989: new blank line at EOF` | Línea vacía adicional al final del archivo | Se eliminó la línea extra |
| `03-create-raw-ventas-problemas.sql:30: new blank line at EOF` | Línea vacía adicional al final | Se eliminó la línea extra |

Git reporta los números de línea de cada versión; al editar el documento pueden cambiar. En VS Code puede activarse **View → Appearance → Render Whitespace**. Tras guardar, `git diff --check` no mostró mensajes: esa es la comprobación esperada.

### 18.3 Preparar exclusivamente los ocho archivos de APPEND

```powershell
git add PROJECT_STATE.md
git add docs/guides/DE06_postgresql_guia.md
git add postgres/init/02-create-raw-ventas.sql
git add postgres/init/03-create-raw-ventas-problemas.sql
git add src/load/postgres_loader.py
git add src/main.py
git add data/incoming/ventas_dia_2.csv
git add img/infografia_postgresql_full_vs_append.png
```

Cada `git add <ruta>` coloca en staging el estado actual del archivo indicado. **No se usó `git add .`**: hacerlo habría incorporado ejercicios y CSV de prueba que no pertenecían a la funcionalidad. Antes de confirmar, revisar:

```powershell
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
git status
```

`--cached` (también llamado `--staged`) inspecciona **lo preparado**. `--stat` muestra un resumen; `--name-only`, la lista; `--check`, advertencias de espacios en staging. Es recomendable inspeccionar también `git diff --cached` para revisar el código y SQL si se está enseñando una revisión de cambios.

**Resumen observado:**

```text
 PROJECT_STATE.md                                 | 188 +++---
 data/incoming/ventas_dia_2.csv                   |   6 +
 docs/guides/DE06_postgresql_guia.md              | 748 +++++++++++++++++++----
 img/infografia_postgresql_full_vs_append.png     | Bin 0 -> 2102552 bytes
 postgres/init/02-create-raw-ventas.sql           |   4 +-
 postgres/init/03-create-raw-ventas-problemas.sql |   7 +-
 src/load/postgres_loader.py                      |  33 +-
 src/main.py                                      |  62 +-
 8 files changed, 815 insertions(+), 233 deletions(-)
```

La imagen binaria figura como archivo nuevo. Ocho archivos es el alcance aprobado de este commit, **no una cantidad obligatoria** para otros repositorios.

### 18.4 Confirmar la funcionalidad mediante un commit

```powershell
git commit -m "feat: implementar carga append idempotente en PostgreSQL"
git log -1 --oneline
git status
```

`git commit -m` registra en la rama actual lo que estaba en staging; `-m` aporta el mensaje. La palabra `feat` comunica una nueva funcionalidad, según una convención de mensajes sencilla.

**Salida observada:**

```text
[feature/de06-append b0e59af] feat: implementar carga append idempotente en PostgreSQL
 8 files changed, 815 insertions(+), 233 deletions(-)
 create mode 100644 data/incoming/ventas_dia_2.csv
 create mode 100644 img/infografia_postgresql_full_vs_append.png
```

Después de este commit, `git status` **no estaba limpio** porque seguían existiendo los archivos personales no preparados. Eso era correcto: `git commit` no confirma automáticamente todos los archivos de la carpeta.

### 18.5 Proteger los cambios locales ajenos a APPEND con `git stash`

Para cambiar de rama sin arriesgar ni mezclar esas modificaciones, se ejecutó:

```powershell
git stash push -u -m "WIP: ejercicios y cambios personales pendientes"
git stash list
git status
```

- `stash push`: guarda los cambios locales sin confirmar y los retira temporalmente del directorio de trabajo.
- `-u`: incluye archivos **no rastreados** (`??`), además de cambios en archivos rastreados; no incluye por defecto archivos ignorados.
- `-m`: pone una descripción que permita reconocer el conjunto.
- `stash list`: permite verificar que la entrada existe.

**Resultados observados:**

```text
Saved working directory and index state On feature/de06-append: WIP: ejercicios y cambios personales pendientes
stash@{0}: On feature/de06-append: WIP: ejercicios y cambios personales pendientes
On branch feature/de06-append
nothing to commit, working tree clean
```

Durante la operación también apareció: `LF will be replaced by CRLF the next time Git touches it` para la guía revisada de DE-05. **No fue un error ni impidió el stash**: describe una conversión posible de finales de línea. Es útil explicar la diferencia entre LF (Unix) y CRLF (Windows) sin cambiar automáticamente la configuración del repositorio por una sola advertencia.

**Advertencia pedagógica:** `stash` no equivale a publicar o respaldar permanentemente archivos. Si se trabaja en otra máquina, los archivos guardados en el stash local no viajan mediante `git push`.

### 18.6 Cambiar a `main` y actualizarla desde GitHub

```powershell
git switch main
git pull --ff-only origin main
git status
git log -1 --oneline
```

`git switch main` cambia a la rama principal. `git pull --ff-only origin main` trae e integra el estado remoto **solo si puede hacerlo mediante fast-forward**, sin crear un merge inesperado. Si hay divergencia, detiene la operación para revisar el caso.

**Estado observado:**

```text
Already up to date.
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean

dbff254 (HEAD -> main, origin/main, origin/HEAD) Merge branch 'feature/de06-postgresql'
```

La rama `main` aún contenía FULL, pero **no** APPEND. De este modo comprobamos que el merge siguiente tenía un propósito claro.

### 18.7 Integrar APPEND en `main` mediante un merge local

```powershell
git merge --no-ff feature/de06-append
git status
git log --oneline --graph --decorate -5
```

`git merge` integra los commits de la rama de trabajo a la rama actual (`main`). `--no-ff` fuerza un **commit de merge**, incluso si era posible mover directamente el puntero. Se eligió para que el historial muestre la unidad didáctica APPEND como una rama integrada.

**Verificación observada:**

```text
On branch main
Your branch is ahead of 'origin/main' by 2 commits.
nothing to commit, working tree clean
```

```text
*   58de9ee (HEAD -> main) Merge branch 'feature/de06-append'
|\
| * b0e59af (feature/de06-append) feat: implementar carga append idempotente en PostgreSQL
|/
*   dbff254 (origin/main, origin/HEAD) Merge branch 'feature/de06-postgresql'
```

Estar *ahead by 2 commits* significaba que el commit funcional `b0e59af` **y** el merge `58de9ee` eran locales y faltaba publicarlos. No indicaba un error. Si Git abre el historial en un visor con `(END)`, se sale pulsando `q`.

### 18.8 Publicar `main` en GitHub y comprobar la sincronización

```powershell
git push origin main
git status
git log --oneline --graph --decorate -5
```

`git push origin main` envía los commits de la rama local `main` al remoto llamado `origin`. No publica el stash ni todos los archivos locales, solo los commits que forman parte de la rama enviada.

**Resultados finales observados:**

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

```text
*   58de9ee (HEAD -> main, origin/main, origin/HEAD) Merge branch 'feature/de06-append'
|\
| * b0e59af (feature/de06-append) feat: implementar carga append idempotente en PostgreSQL
|/
*   dbff254 Merge branch 'feature/de06-postgresql'
|\
| * 318341c feat: implementar carga full transaccional en PostgreSQL
|/
* 2c885db docs: cerrar DE05 y actualizar estado del proyecto
```

La coincidencia de `main` y `origin/main` en `58de9ee` evidencia la sincronización local/remota observada. En GitHub puede abrirse el historial de `main` para señalar a los alumnos los dos commits funcionales y sus merges.

### 18.9 Recuperar ejercicios y retirar el stash tras verificar

Una vez publicado APPEND, se recuperaron los archivos personales sin mezclarlos en el commit:

```powershell
git stash list
git stash apply "stash@{0}"
git status
```

Se usó `apply` y no `pop`: **`apply` conserva el stash** como copia temporal mientras verificamos que reaparecieron los archivos. Las comillas hacen inequívoco el argumento en PowerShell. La aplicación de un stash en otra rama puede producir conflictos si allí cambiaron las mismas líneas; en ese caso hay que resolverlos antes de considerar recuperado el trabajo.

**Estado recuperado observado:**

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
        modified:   docs/guides/DE05_pandas_guia.md

Untracked files:
        data/incoming/ventas_prueba_problemas.csv
        data/incoming/ventas_renombrado.csv
        docs/guides/DE05_pandas_guia_revisada.md
        pruebas/guia_loc/groupby.py
        pruebas/guia_loc/loc.py
        pruebas/guia_loc/mascaras_booleanas.py
        pruebas/prueba_loader_problemas.py
        pruebas/prueba_merge.py
```

Se comprobó que eran los mismos archivos personales anteriores. **Solo después de recuperar y revisar** se eliminó la entrada del stash:

```powershell
git stash list
git stash drop "stash@{0}"
git stash list
```

**Resultado final comunicado:** `git stash list` ya no mostró entradas. `stash drop` elimina el respaldo temporal, pero **no borra** los cambios que ya fueron aplicados al directorio de trabajo. Si hubiera varias entradas en la lista, se debe verificar la identidad de cada una antes de eliminarla.

### 18.10 Eliminar la rama local ya integrada

```powershell
git branch -d feature/de06-append
git branch
git status
```

`git branch -d` elimina la referencia local de una rama integrada; a diferencia de `-D`, no fuerza el borrado cuando Git considera que no está fusionada. No elimina los commits de APPEND que ya forman parte de `main`. Tampoco elimina una rama remota: en este recorrido no se registró publicación de una rama remota `feature/de06-append`, por lo que **no hay evidencia de que hubiera una rama remota que eliminar**.

**Verificación observada:**

```text
* main
```

`git status` continuó mostrando los cambios personales recuperados, lo cual es esperado. **Un cierre correcto de una funcionalidad no exige borrar o confirmar archivos ajenos a ella.**

### 18.11 Resumen de evidencias del cierre real

| Elemento | Evidencia |
|---|---|
| FULL: commit funcional | `318341c` |
| FULL: merge a `main` | `dbff254` |
| APPEND: rama de trabajo | `feature/de06-append` (eliminada localmente al cerrar) |
| APPEND: commit funcional | `b0e59af` |
| APPEND: merge a `main` | `58de9ee` |
| Sincronización remota final | `HEAD -> main, origin/main, origin/HEAD` en `58de9ee` |
| Archivos confirmados en APPEND | 8, seleccionados por ruta |
| Archivos personales | Recuperados desde stash; permanecen sin confirmar |
| Stash al cierre | Lista vacía, verificada por el usuario |
| Pull Request | No se realizó; merge local y push de `main` |

### 18.12 Errores habituales y actividad para alumnos

| Problema | Explicación / acción recomendable |
|---|---|
| `git diff --check` reporta `trailing whitespace` | Localizar espacios al final de línea, corregir y repetir la verificación |
| `git diff --check` no muestra nada | Bien: no detecta problemas de espacios, pero **no** garantiza que el código funcione |
| Se usa `git add .` con ejercicios personales | Revisar staging mediante `git diff --cached --name-only`; retirar archivos no deseados del índice antes del commit |
| Git impide cambiar de rama | Revisar cambios pendientes; guardar mediante commit apropiado o stash antes de cambiar |
| El usuario interpreta `ahead by 2 commits` como error | Son commits locales pendientes de publicar; comprobar con `git log` y luego `git push` |
| `LF will be replaced by CRLF` | Advertencia de finales de línea; verificar la configuración, no asumir fallo funcional |
| `git log` muestra `(END)` | Presionar `q` para salir del visor |
| `stash apply` produce conflictos | No eliminar el stash; resolver primero y verificar los archivos recuperados |
| Se intenta eliminar la rama con `-D` sin necesidad | Preferir `git branch -d` tras comprobar que se integró |

**Actividad reproducible:** en parejas, pedir al alumnado que identifique qué ocho archivos pertenecen a APPEND, explique por qué los CSV de prueba no entran en el commit, ubique el commit funcional y el merge en `git log --graph`, y demuestre la diferencia entre `stash apply` y `stash pop`. En una reproducción nueva, no deben copiar los hashes reales de esta guía como si fueran sus propios resultados.

**Nota para docentes:** si se desea practicar Pull Requests en GitHub en otro grupo, se puede adaptar el flujo a `push` de rama + PR + revisión + merge remoto. Este caso documenta lo que **efectivamente se ejecutó**: merge local y posterior `push origin main`.

## 19. Qué sigue después de APPEND

**INCREMENTAL** permanece pendiente. Habrá que definir qué hacer cuando una venta apta ya existente llegue corregida, cuándo se actualiza, cuál será el watermark o criterio de cambio y cómo garantizar reintentos; después se abordarán control de lotes y orquestación cuando existan esas necesidades. Hasta decidir esas políticas, no extender `ON CONFLICT DO NOTHING` como si resolviera toda actualización de datos.
