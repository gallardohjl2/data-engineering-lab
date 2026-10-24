PROJECT_STATE — Data Engineering Lab
Última actualización: 23 de octubre de 2026
Bloque activo: DE-06 — Carga y persistencia en PostgreSQL
Situación: unidad de carga full transaccional completada y verificada; DE-06 continúa abierto.
Propósito y arquitectura
Laboratorio didáctico incremental: CSV / Excel / SQL Server → extracción Python y contrato estructural → transformación y calidad con Pandas → persistencia en PostgreSQL → STAGE y modelos dbt → warehouse y marts → Power BI. La infraestructura utiliza Docker Compose; Airflow se introducirá posteriormente cuando corresponda la orquestación.
Bloques
- Preparación, Git y GitHub: terminado.
- Infraestructura Docker con SQL Server, PostgreSQL y pgAdmin: trabajada.
- Fuentes de datos: terminado.
- DE-04 — extracción, contrato estructural y logging: terminado.
- DE-05 — transformación y calidad con Pandas: terminado.
- DE-06 — carga y persistencia PostgreSQL: en progreso. Carga full transaccional e idempotencia básica verificadas.
- Pendiente de DE-06: cierre Git de esta unidad y posterior tratamiento didáctico de append/incremental con un escenario justificado.
Estado funcional confirmado
- src/main.py: coordina extracción CSV, transformación Pandas, diagnóstico y política de calidad, preparación de tres DataFrames y persistencia en PostgreSQL.
- Fuente principal data/incoming/ventas.csv: 18 registros → 11 APTO, 5 RECHAZADO, 2 REVISION.
- src/extract/csv_extractor.py: extracción con csv.DictReader, contrato estructural y source_row_number por registro.
- src/transform/ventas_transformer.py: conversión de tipos con Pandas.
- src/quality/ventas_quality.py y src/quality/ventas_policy.py: diagnóstico, motivos, clasificación y conservación de los valores originales para investigación.
- src/config/logging_config.py: salida a consola y logs/pipeline.log.
- src/load/postgres_loader.py: conectar_postgres(), limpiar_ventas(conexion), cargar_ventas_aptas(df, conexion) y cargar_ventas_problemas(df, conexion).
- La limpieza de ambas tablas y las tres inserciones se realizan con una sola conexión y una transacción administrada desde main.py; las funciones del loader no hacen commit() independiente.
- main.py registra errores de PostgreSQL con logger.exception() y los propaga mediante raise; conserva el manejo de FileNotFoundError y ValueError.
- Destinos existentes: raw.ventas (aptos tipados) y raw.ventas_problemas (rechazados y revisión con motivos_calidad TEXT[] y campos originales TEXT). En esta etapa no tienen PK ni claves foráneas.
- PostgreSQL Docker: puerto host 5433 → contenedor 5432, base warehouse. pgAdmin: puerto host 8080 → contenedor 80.
- Dependencias utilizadas: pandas==3.0.6, psycopg[binary]==3.3.6 y python-dotenv==1.2.4. Verificar antes del commit que requirements.txt contenga únicamente estas especificaciones, sin comandos de terminal.
Resultados y pruebas DE-06
- Carga exitosa: 11 aptos en raw.ventas y 7 problemáticos en raw.ventas_problemas (5 rechazados y 2 en revisión).
- Valores originales preservados para investigación: fecha_invalida, cantidad -1, precio vacío, precio ABC y dos filas con clave duplicada de venta 1015 clasificadas como REVISION.
- Idempotencia básica demostrada: dos ejecuciones del mismo CSV con carga full transaccional; después de la segunda se mantuvieron los conteos 11/5/2, sin acumular filas.
- Reversión SQL demostrada: BEGIN; TRUNCATE; ROLLBACK; restauró las filas anteriores. Otra prueba con TRUNCATE, un INSERT correcto y un INSERT fallido por restricción NOT NULL terminó con ROLLBACK, conservando los 18 registros anteriores.
- Prueba independiente con Psycopg: reversión de una inserción ante una excepción simulada.
- Prueba de conexión fallida: psycopg.OperationalError con credenciales deliberadamente incorrectas.
- Prueba independiente del logger: logger.exception() registró mensaje y traceback en consola y logs/pipeline.log; raise propagó la excepción.
- No se ha probado todavía un fallo real de inserción invocando el pipeline completo desde main.py; las comprobaciones SQL, Psycopg y logger se realizaron por separado.
- Los archivos temporales prueba_rollback.py y prueba_logger.py no forman parte de la implementación final ni deben incorporarse al commit.
Decisiones de arquitectura
- Diferenciar contrato estructural de origen (Python) y calidad de contenido (Pandas).
- Conservar los valores originales y motivos de rechazados/revisión; no reemplazarlos por NaN o NaT transformados.
- Las claves duplicadas aisladas se envían a revisión, no se descartan automáticamente.
- APTO indica que un registro cumple las reglas de calidad implementadas, no que esté universalmente certificado.
- source_row_number identifica la posición lógica dentro del archivo; para múltiples fuentes y lotes se necesitará una identidad de archivo/lote.
- La tabla raw.ventas recibe registros aptos ya transformados: se reconoce como uso provisional de la capa RAW, no como una copia fiel del archivo de origen.
- Para el CSV completo actual se eligió full transaccional: TRUNCATE de ambos destinos seguido de inserciones en la misma transacción.
- TRUNCATE adquiere bloqueos ACCESS EXCLUSIVE y elimina todas las filas de las tablas indicadas. No aplicar automáticamente esta estrategia a tablas relacionadas, compartidas, voluminosas o con concurrencia sin analizar el diseño.
- La idempotencia validada aplica al CSV completo y a las reglas actuales; todavía no existen batch_id, watermark, UPSERT ni identidad global de registros.
- Postergar control de lotes, cargas incrementales, Airflow y dbt hasta que exista una necesidad didáctica y técnica concreta.
Archivos relevantes
PROJECT_STATE.md
compose.yaml
requirements.txt
src/main.py
src/contracts/ventas_contract.py
src/config/logging_config.py
src/extract/csv_extractor.py
src/transform/ventas_transformer.py
src/quality/ventas_quality.py
src/quality/ventas_policy.py
src/load/__init__.py
src/load/postgres_loader.py
data/incoming/ventas.csv
postgres/init/02-create-raw-ventas.sql
postgres/init/03-create-raw-ventas-problemas.sql
docs/guides/DE05_pandas_guia.md
docs/guides/DE06_postgresql_guia.md
También existen archivos de prueba de DE-05 en data/test_cases/. Los archivos no relacionados de pruebas/guia_loc/ quedan fuera del commit de DE-06.
Git
DE-05 — Cerrado
- Rama: transformacion-pandas.
- Commit: 1756a15.
- Merge local a main: e8c32e9.
- origin/main sincronizado y rama de trabajo eliminada al cerrar DE-05.
DE-06 — En progreso
- Los cambios se desarrollaron inicialmente en main, sin commit.
- Se indicó crear la rama feature/de06-postgresql; confirmar la rama activa con git branch --show-current antes del commit.
- Archivos de DE-06 modificados o nuevos: .gitignore, PROJECT_STATE.md, compose.yaml, requirements.txt, src/main.py, loader, scripts SQL y guía DE-06.
- Cambio verificado en compose.yaml: pgAdmin expuesto en 8080:80.
- Cambio verificado en .gitignore: patrón NEXT_CHAT_DE*.md.
- Archivos ajenos a este bloque: pruebas/guia_loc/loc.py y pruebas/guia_loc/mascaras_booleanas.py; no incluirlos en el commit de DE-06.
- Pendientes: revisar archivos nuevos y cambios finales, git add selectivo, commit, merge local en main, push origin main y eliminación de rama. No se han confirmado commits ni push de DE-06.
- Flujo Git vigente: rama local → verificación → commit → merge local en main → push de main → eliminación de rama; sin PR en esta etapa.
Documentación
- Guía de alumnos: docs/guides/DE06_postgresql_guia.md, versión 1.1, cubre PostgreSQL, Psycopg, SQL, persistencia, transacciones, logging, full, idempotencia y pruebas.
- PROJECT_STATE.md es el estado operativo para continuidad entre chats; no reemplaza las guías didácticas.
Siguiente paso
1. Confirmar la rama activa y que requirements.txt contiene solo dependencias.
2. Revisar el contenido de los archivos nuevos de DE-06 y preparar un commit selectivo, excluyendo pruebas/guia_loc/.
3. Completar el flujo Git para la unidad de carga full, sin declarar todo DE-06 cerrado.
4. Continuar DE-06 con un escenario de datos que justifique append e incremental; elegir la estrategia antes de escribir código nuevo.