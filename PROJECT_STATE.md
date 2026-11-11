# PROJECT_STATE — Data Engineering Lab

**Actualizado:** 10 de noviembre de 2026

**Bloque activo:** DE-06 — Carga y persistencia en PostgreSQL
**Situación:** FULL y APPEND implementadas y verificadas. Pendiente cerrar la rama de APPEND con Git; INCREMENTAL aún no iniciada.

## 1. Propósito y arquitectura

Laboratorio didáctico: CSV / Excel / SQL Server → extracción y contrato estructural en Python → transformación, calidad y clasificación con Pandas → persistencia PostgreSQL → STAGE y modelos dbt → warehouse / marts → Power BI. Docker Compose aporta la infraestructura; Airflow se estudiará después como orquestador. Cada fase se construye y documenta paso a paso.

## 2. Bloques

- Preparación, Git y GitHub: terminado.
- Infraestructura Docker (SQL Server, PostgreSQL y pgAdmin): trabajada.
- Fuentes de datos: terminado.
- DE-04 (extracción, contrato estructural y logging): terminado.
- DE-05 (transformación y calidad con Pandas): terminado.
- **DE-06 FULL: implementada, probada, documentada y cerrada en Git.**
- **DE-06 APPEND: implementada y probada; documentación actualizada localmente según el usuario; cierre Git pendiente.**
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
- Documentación: `docs/guides/DE06_postgresql_guia.md` (FULL + APPEND, versión actualizada declarada por el usuario), `img/infografia_postgresql_full_vs_append.png` (confirmar ubicación/referencia exactas en el repositorio).
- Estado y configuración: `PROJECT_STATE.md`, `requirements.txt`, `compose.yaml`, `.gitignore`.
- Mantener fuera del commit de APPEND los cambios no relacionados en `docs/guides/DE05_pandas_guia.md`, `docs/guides/DE05_pandas_guia_revisada.md` y scripts personales bajo `pruebas/`.

## 7. Git — situación conocida

- DE-05: rama `transformacion-pandas`, commit `1756a15`, merge local `e8c32e9`; cerrada.
- DE-06 FULL: rama `feature/de06-postgresql`, commit `318341c`; merge a `main` `dbff254`; `origin/main` sincronizado y rama eliminada, según verificaciones previas.
- **DE-06 APPEND:** rama activa `feature/de06-append` (confirmada por `git branch --show-current`). Trabajo y pruebas terminados, **sin commit, merge ni push confirmados para APPEND**.
- Modificados observados: `src/main.py`, `src/load/postgres_loader.py`, `postgres/init/02-create-raw-ventas.sql`, `postgres/init/03-create-raw-ventas-problemas.sql`, cambio independiente en guía DE-05; `.gitignore` mostraba una línea `img` que se indicó retirar (verificar estado final).
- Untracked observados: `data/incoming/ventas_dia_2.csv`, archivos de prueba, guía revisada DE-05, infografía y scripts de `pruebas/`. El usuario indicó que reemplazó la guía DE-06 y mantuvo una única infografía; **revisar rutas reales antes de hacer staging**.
- Flujo acordado para esta unidad: revisar estado y diferencias → `git add` **selectivo** → commit en rama → push / PR si corresponde al flujo vigente → merge → actualizar `main` → eliminar rama. No incluir `.env`, logs ni pruebas ajenas.

## 8. Documentación y forma de enseñanza

- Guía didáctica FULL + APPEND: explicar ubicación **exacta** por archivo y función, código completo, comandos, significado de retornos, SQL y resultados esperados. El usuario quiere infografías equivalentes para las cargas siguientes.
- La guía de alumnos y `PROJECT_STATE.md` cumplen funciones distintas; no asumir que una versión descargada equivale automáticamente a su versión confirmada en el repositorio sin revisión.

## 9. Próximos pasos

1. Sustituir el contenido de `PROJECT_STATE.md` en el repositorio por este estado actualizado, tras revisarlo.
2. Verificar `git status --short`, `git diff --check`, guía FULL + APPEND, infografía y `.gitignore`; revisar que `requirements.txt` esté correcto y que el `.env` no esté versionado.
3. Seleccionar explícitamente los archivos de APPEND y documentación para el commit; no arrastrar cambios de DE-05 ni pruebas personales.
4. Cerrar Git de APPEND y actualizar este estado con commit, merge y push **solo después de confirmarlos**.
5. Continuar DE-06 con **INCREMENTAL**, definiendo primero el escenario de actualización, política de conflictos y eventual watermark/control de lotes, sin implementar todo de una vez.
