# PROJECT_STATE — Data Engineering Lab

**Actualizado:** 10 de noviembre de 2026
**Bloque activo:** DE-06 — Carga y persistencia en PostgreSQL
**Situación:** FULL y APPEND implementadas, verificadas, documentadas e integradas en `main` y GitHub. Pendiente confirmar el commit de la ampliación didáctica Git/GitHub de la guía y este cierre de estado; INCREMENTAL aún no iniciada.

## 1. Propósito y arquitectura

Laboratorio didáctico: CSV / Excel / SQL Server → extracción y contrato estructural en Python → transformación, calidad y clasificación con Pandas → persistencia PostgreSQL → STAGE y modelos dbt → warehouse / marts → Power BI. Docker Compose aporta la infraestructura; Airflow se estudiará después como orquestador. Cada fase se construye y documenta paso a paso.

## 2. Bloques

- Preparación, Git y GitHub: terminado.
- Infraestructura Docker (SQL Server, PostgreSQL y pgAdmin): trabajada.
- Fuentes de datos: terminado.
- DE-04 (extracción, contrato estructural y logging): terminado.
- DE-05 (transformación y calidad con Pandas): terminado.
- **DE-06 FULL: implementada, probada, documentada y cerrada en Git.**
- **DE-06 APPEND: implementada, probada, documentada e integrada en `main` y GitHub.**
- **DE-06 INCREMENTAL: pendiente.**

## 3. Estado funcional confirmado

- `src/main.py`: `main(archivo: Path = VENTAS_FILE, modo_carga: str = "full")`; admite `full` y `append`, coordina extracción, SHA-256, transformación, calidad, persistencia y logging. `python -m src.main` ejecuta FULL con archivo predeterminado; para APPEND se ha usado una invocación `python -c` con argumentos explícitos. Aún no hay interfaz CLI `--archivo/--modo`.
- `src/extract/csv_extractor.py`: `extract_csv()` con `csv.DictReader`, contrato de columnas y `source_row_number` (posición lógica dentro del CSV).
- `src/transform/ventas_transformer.py`: transformaciones de tipos con Pandas.
- `src/quality/ventas_quality.py` y `src/quality/ventas_policy.py`: diagnóstico, motivos, política APTO / RECHAZADO / REVISION; duplicados de clave de negocio detectados en el archivo se conservan para revisión. Investigación retiene los valores originales.
- `src/config/logging_config.py`: consola y `logs/pipeline.log`.
- `src/load/postgres_loader.py`: `conectar_postgres()`, `limpiar_ventas(conexion)`, `cargar_ventas_aptas(df_aptos, conexion) -> int` y `cargar_ventas_problemas(df_problemas, conexion, archivo_origen, hash_archivo) -> int`. Las funciones de carga suman `cursor.rowcount` para contar insertados efectivos y no confirman transacciones por su cuenta.
- `main.py` calcula `hashlib.sha256(archivo.read_bytes()).hexdigest()` después de la extracción, lo registra en logger y pasa `archivo.name` y `hash_archivo` al loader de problemáticos.
- El bloque `with conectar_postgres() as conexion:` contiene el `TRUNCATE` **solo si el modo es FULL** y las tres inserciones. Psycopg confirma al salir sin excepción o revierte si se propaga una excepción; `main.py` registra errores `psycopg.Error` con `logger.exception()` y `raise`.
- Los logs distinguen clasificados/procesados, insertados reales y omitidos por conflictos, en aptos, rechazados y revisión. Se corrigió el mensaje `Persistencia completada` para mostrar inserciones reales.
- PostgreSQL en Docker: host `localhost:5433`, contenedor puerto `5432`, base `warehouse`; pgAdmin probado en `localhost:8080`. Variables de conexión en `.env` (no versionar).
- Dependencias utilizadas: `pandas==3.0.6`, `psycopg[binary]==3.3.6`, `python-dotenv==1.2.4`.

## 4. Contratos de persistencia y decisiones de arquitectura

### `raw.ventas` — aptos transformados

- Una fila por combinación de negocio `(venta_id, linea_id)` mediante `uq_raw_ventas_clave UNIQUE (venta_id, linea_id)`.
- Loader utiliza `ON CONFLICT (venta_id, linea_id) DO NOTHING`.
- Si la misma clave llega corregida con valores diferentes, APPEND **la omite**, no actualiza: decisión pendiente para INCREMENTAL / UPSERT.
- El nombre `raw` es provisional: esta tabla contiene datos aptos transformados, no una copia de los bytes de origen.

### `raw.ventas_problemas` — evidencia original

- Estados `RECHAZADO` y `REVISION` con `motivos_calidad TEXT[]`, datos problemáticos en texto y `source_row_number`.
- `archivo_origen TEXT` documenta el nombre de origen; `hash_archivo CHAR(64) NOT NULL` identifica el contenido completo del CSV mediante SHA-256.
- `uq_ventas_problemas_archivo_fila UNIQUE (hash_archivo, source_row_number)` y `ON CONFLICT (hash_archivo, source_row_number) DO NOTHING` evitan insertar de nuevo la misma observación de la misma versión.
- **Se conservan** observaciones distintas con la misma clave de negocio, como las filas 16 y 17 de `venta_id=1015` (ambas en REVISION).
- Archivo idéntico con otro nombre → mismo hash, no duplica. Mismo nombre con contenido cambiado → nuevo hash y posible nueva observación. Un cambio mínimo en el archivo cambia la identidad de toda la versión; no representa necesariamente una modificación de negocio.
- `UNIQUE` más `ON CONFLICT` protegen la inserción por clave; no equivalen aún a gestión de lotes, recepciones, correcciones o reconciliación entre versiones.

### FULL vs APPEND

- **FULL:** `limpiar_ventas()` hace `TRUNCATE raw.ventas, raw.ventas_problemas`; luego vuelve a insertar las tres salidas dentro de una única transacción. Solo adecuada si ambas tablas son destinos exclusivos del conjunto que se está reemplazando. `TRUNCATE` genera bloqueos `ACCESS EXCLUSIVE`; no usar `CASCADE` indiscriminadamente.
- **APPEND:** no vacía; inserta nuevos aptos y nuevas observaciones problemáticas, omitiendo conflictos por sus claves correspondientes. Reprocesar contenido ya cargado no aumenta las filas.
- Mantener separadas las reglas de calidad del origen y las restricciones de persistencia. `APTO` significa cumplimiento de las reglas implementadas, no certificación universal.

## 5. Resultados y pruebas verificadas

- `data/incoming/ventas.csv`: 18 registros → 11 APTO, 5 RECHAZADO, 2 REVISION.
- `data/incoming/ventas_dia_2.csv`: 5 APTO, 0 problemáticos; al añadirse a la carga original → **16 aptos, 5 rechazados, 2 revisión (23 registros)**.
- Reejecución APPEND del mismo CSV: 0 inserciones para observaciones previamente almacenadas y contadores de omitidos coherentes.
- Prueba `ventas_prueba_problemas.csv` (venta `3001` con cantidad negativa): rechazo insertado con `archivo_origen` y SHA-256; al reprocesarlo, 0 insertados y 1 omitido.
- Archivo renombrado sin cambiar contenido: mismo hash y omisión correcta. Archivo con cantidad modificada: hash distinto y segunda observación de prueba almacenada. Registros de prueba `3001` retirados después.
- Prueba FINAL de APPEND con `ventas.csv`: 11 aptos, 5 rechazados y 2 revisión **procesados**; cero **insertados**; totales permanecieron 16/5/2.
- Prueba de FULL tras introducir SHA-256 y restricciones: volvió a 11/5/2. Posterior APPEND con `ventas_dia_2.csv` restauró **16/5/2**, confirmado por el usuario.
- Pruebas anteriores de FULL: `BEGIN; TRUNCATE; ROLLBACK`, fallo SQL `NOT NULL` con rollback, conexión incorrecta, logging y propagación de excepciones. **No hay evidencia de fallo de inserción generado desde el pipeline integrado completo.**
- Se verificó que no había duplicados por `(hash_archivo, source_row_number)` antes de crear `UNIQUE`; se asignó el hash histórico de `ventas.csv` a siete filas y se agregó `NOT NULL` tras comprobar ausencia de nulos. Esto supone que el contenido original no había cambiado.

## 6. Archivos relevantes

- Código: `src/main.py`, `src/load/postgres_loader.py`, `src/extract/csv_extractor.py`, `src/contracts/ventas_contract.py`, `src/transform/ventas_transformer.py`, `src/quality/ventas_quality.py`, `src/quality/ventas_policy.py`, `src/config/logging_config.py`.
- SQL: `postgres/init/02-create-raw-ventas.sql`, `postgres/init/03-create-raw-ventas-problemas.sql` (restricciones ya incorporadas en scripts y PostgreSQL).
- Datos: `data/incoming/ventas.csv`, `data/incoming/ventas_dia_2.csv`. `ventas_prueba_problemas.csv` y `ventas_renombrado.csv` fueron usados para pruebas: **no incluir automáticamente en el commit**.
- Documentación: `docs/guides/DE06_postgresql_guia.md` (FULL + APPEND + procedimiento didáctico Git/GitHub, versión 2.1 reemplazada localmente según el usuario), `img/infografia_postgresql_full_vs_append.png` (confirmar ubicación/referencia exactas en el repositorio).
- Estado y configuración: `PROJECT_STATE.md`, `requirements.txt`, `compose.yaml`, `.gitignore`.
- Mantener fuera del commit de APPEND los cambios no relacionados en `docs/guides/DE05_pandas_guia.md`, `docs/guides/DE05_pandas_guia_revisada.md` y scripts personales bajo `pruebas/`.

## 7. Git — cierre confirmado

- DE-05: rama `transformacion-pandas`, commit `1756a15`, merge `e8c32e9`; cerrada.
- DE-06 FULL: commit `318341c` en `feature/de06-postgresql`; merge `dbff254` en `main`.
- DE-06 APPEND: commit `b0e59af` (`feat: implementar carga append idempotente en PostgreSQL`), merge `58de9ee` (`Merge branch 'feature/de06-append'`). `main` y `origin/main` apuntaban ambos a `58de9ee` según salida verificada; rama local `feature/de06-append` eliminada, quedando solo `main`.
- Antes del merge se protegieron cambios independientes con `git stash push -u`; se recuperaron en `main` con `git stash apply`. El usuario confirmó que `git stash list` quedó vacío.
- **Cambios locales ajenos al cierre conservados:** `docs/guides/DE05_pandas_guia.md`, `docs/guides/DE05_pandas_guia_revisada.md`, `data/incoming/ventas_prueba_problemas.csv`, `data/incoming/ventas_renombrado.csv` y archivos de `pruebas/`. No usar `git add .` para el commit documental.
- **Nueva documentación después del merge:** el usuario confirmó que sustituyó `docs/guides/DE06_postgresql_guia.md` por la versión 2.1 con la secuencia completa de Git y GitHub. Esta actualización aún **no tiene commit ni push confirmados**. Este `PROJECT_STATE.md` también debe incorporarse en un commit documental selectivo.

## 8. Documentación y forma de enseñanza

- Guía didáctica FULL + APPEND: explicar ubicación **exacta** por archivo y función, código completo, comandos, significado de retornos, SQL y resultados esperados. El usuario quiere infografías equivalentes para las cargas siguientes.
- La guía de alumnos y `PROJECT_STATE.md` cumplen funciones distintas; no asumir que una versión descargada equivale automáticamente a su versión confirmada en el repositorio sin revisión.

## 9. Próximos pasos

1. Guardar este `PROJECT_STATE.md` y comprobar el estado real de Git con `git status --short` y `git diff --check`.
2. Preparar **solo** `docs/guides/DE06_postgresql_guia.md` y `PROJECT_STATE.md` para un commit de documentación; revisar con `git diff --cached --stat` y `git diff --cached --check`. No incluir DE-05 ni archivos de ejercicios/pruebas.
3. Crear y publicar el commit documental en el flujo Git acordado; anotar su hash real aquí cuando esté confirmado. No afirmarlo antes.
4. Siguiente chat recomendado: **DE-06 — Carga incremental, watermarks y control de lotes**. Comenzar por un escenario concreto de cambios de registros, distinguir APPEND vs INCREMENTAL y decidir el criterio mínimo antes de escribir código.
