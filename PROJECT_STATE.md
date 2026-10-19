# PROJECT_STATE — Data Engineering Lab

> Estado operativo actualizado con la información confirmada al cierre de DE-05 (18 de octubre de 2026). Sustituir el contenido de `PROJECT_STATE.md` del repositorio después de revisarlo.

## Propósito y arquitectura

Laboratorio didáctico incremental: CSV / Excel / SQL Server → extracción Python y contrato estructural → Pandas (tipos, calidad, clasificación) → persistencia RAW / rechazados en PostgreSQL → STAGE y modelos dbt → warehouse y marts → Power BI. Docker Compose proporciona infraestructura; Airflow se introducirá después como orquestador.

## Bloques

- Preparación, Git y GitHub: terminado.
- Infraestructura Docker con SQL Server, PostgreSQL y pgAdmin: trabajada.
- Fuentes de datos (CSV, Excel y SQL Server): terminado.
- DE-04 extracción, validación estructural y logging: terminado.
- **DE-05 transformación y calidad con Pandas: TERMINADO.**
- **Siguiente: DE-06 — Carga y persistencia inicial en PostgreSQL (RAW y destinos de calidad), por diseñar incrementalmente.**

## Estado funcional confirmado

- `src/extract/csv_extractor.py`: extrae `list[dict]` con `csv.DictReader`; valida archivo, encabezados requeridos y duplicados, permite columnas extra y detecta filas con más o menos campos; reserva `source_row_number` y lo genera por registro (posición lógica, no necesariamente número de línea física en CSV multilínea).
- `src/transform/ventas_transformer.py`: convierte `cantidad`, `precio_unitario`, `descuento_pct` y `fecha` usando Pandas y `errors="coerce"`.
- `src/quality/ventas_quality.py`: valida cantidad y precio positivos, descuento 0–100, fecha válida y duplicados de `(venta_id, linea_id)` con `keep=False`; produce motivos de calidad, diagnóstico detallado y vista de investigación con datos originales.
- `src/quality/ventas_policy.py`: clasifica `APTO`, `RECHAZADO`, `REVISION`; problemas de cantidad, precio, descuento o fecha son bloqueantes; duplicidad aislada pasa a revisión. Prepara aptos completos transformados y separa salidas problemáticas.
- `src/main.py`: coordina extracción → transformación → diagnóstico → clasificación → preparación en memoria de tres salidas; ruta habitual `data/incoming/ventas.csv`. No persiste todavía los resultados.
- `src/config/logging_config.py`: se conservó la versión de DE-04, con consola y `logs/pipeline.log`; `main.py` llama a `setup_logging(PROJECT_ROOT)`.
- Errores críticos `FileNotFoundError` y `ValueError` se registran y se propagan con `raise`, para obtener código de salida no cero. Archivo con encabezados válidos y cero registros: advertencia y salida 0 por decisión actual.

## Resultados y verificaciones

- `data/incoming/ventas.csv`: 18 registros, **11 APTO, 5 RECHAZADO, 2 REVISION**; código de salida 0.
- `data/test_cases/ventas_cantidad_invalida.csv`: 18 registros, **8 APTO, 8 RECHAZADO, 2 REVISION**.
- Archivo inexistente: `FileNotFoundError`, código 1.
- Fila estructural con menos campos: `ValueError` y código 1.
- Archivo con encabezado pero sin filas: warning, código 0.
- La condición de cantidad de campos sobrantes y los estados desconocidos también se comprobaron a nivel de función.

## Decisiones que deben mantenerse

- Diferenciar validación estructural (Python) de calidad de contenido (Pandas).
- Conservar origen y motivos en rechazados/revisión; no sustituirlos por valores convertidos a `NaN` / `NaT`.
- La trazabilidad `source_row_number` es local al archivo; para múltiples fuentes o ejecuciones hará falta identidad de archivo/lote.
- No descartar automáticamente claves duplicadas: enviarlas a revisión, salvo reglas bloqueantes adicionales.
- No interpretar `APTO` como certificación universal de calidad: expresa cumplimiento de las reglas implementadas.
- No introducir carga, lotes, watermarks, idempotencia, Airflow ni dbt hasta que su problema concreto se estudie.
- Flujo Git **adoptado en DE-05**: desarrollar en rama local, verificar, commit, merge local a `main`, `push origin main`, eliminar rama; **sin Pull Request y sin necesidad de publicar la rama de trabajo** en este laboratorio por ahora. Esto reemplaza la indicación antigua de trabajar directamente en `main`.

## Archivos relevantes

```text
src/main.py
src/extract/csv_extractor.py
src/contracts/ventas_contract.py
src/config/logging_config.py
src/transform/__init__.py
src/transform/ventas_transformer.py
src/quality/__init__.py
src/quality/ventas_quality.py
src/quality/ventas_policy.py
requirements.txt
data/incoming/ventas.csv
data/incoming/clientes.xlsx
data/test_cases/ventas_cantidad_invalida.csv
data/test_cases/ventas_estructura_invalida.csv
data/test_cases/ventas_sin_registros.csv
docs/guides/DE05_pandas_guia.md
```

## Git confirmado

- Rama de trabajo `transformacion-pandas`, commit `1756a15` (`feat: implementar transformacion y calidad de ventas con pandas`).
- Merge local en `main`: `e8c32e9` (`Merge branch 'transformacion-pandas'`).
- `origin/main` sincronizado y árbol limpio, comprobados por el usuario.
- Rama local `transformacion-pandas` eliminada correctamente.
- La actualización de este archivo de estado **aún debe copiarse al repositorio y registrarse en un commit adicional**; no está incluida en `e8c32e9`.

## Siguiente paso (DE-06)

1. Revisar estructura actual, `compose.yaml`, esquemas PostgreSQL y configuración real disponible, sin inventar archivos ni conexiones.
2. Explicar qué significa persistir las salidas de DE-05 y distinguir RAW de destinos de rechazados/revisión.
3. Diseñar únicamente el primer contrato de destino y una carga inicial simple, después probarla; dejar estrategias full/append/incremental y controles de lote para cuando correspondan.
4. No confundir la transformación inicial con dbt ni introducir orquestación prematuramente.
