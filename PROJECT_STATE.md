# PROJECT_STATE — Data Engineering Lab

> Documento operativo de continuidad entre chats.

## 1. Propósito

Construir paso a paso un proyecto didáctico de Data Engineering reproducible con alumnos y progresivamente cercano a escenarios reales, evitando complejidad antes de que exista una necesidad concreta.

## 2. Arquitectura objetivo

```text
Excel / CSV / SQL Server
          ↓
   Extractores Python
          ↓
 Validación estructural
          ↓
        Pandas
 tipos / nulos / calidad
          ↓
 válidos / rechazados
          ↓
         RAW
          ↓
        STAGE
          ↓
         dbt
          ↓
  Data Warehouse
          ↓
     Data Marts
          ↓
      Power BI
```

Airflow orquestará el pipeline y Docker Compose desplegará la infraestructura.

## 3. Principios vigentes

- Avance incremental y didáctico.
- Explicar primero la necesidad; implementar después.
- Evitar sobreingeniería.
- Python puro para extracción y validación estructural.
- Pandas para tipado, conversiones, nulos, duplicados y calidad.
- dbt para transformaciones y pruebas en la plataforma analítica.
- No inventar contenido de archivos existentes.

## 4. Flujo Git vigente

A partir de DE-05 se trabajará directamente sobre `main`.

```text
main local
   ↓
desarrollar el bloque
   ↓
verificar
   ↓
git status
   ↓
git add / git commit
   ↓
al cerrar el bloque
   ↓
git push origin main
```

No se utilizarán Pull Requests por defecto en este laboratorio individual.

DE-04 se desarrolló en `feature/python-ingestion` y debe cerrarse mediante merge local a `main`, push de `main` y eliminación de la rama.

## 5. Bloques completados

### Preparación, Git y GitHub
Estado: TERMINADO

### Infraestructura Docker
Estado: TRABAJADO

Incluye SQL Server, PostgreSQL, pgAdmin, redes, volúmenes, puertos, persistencia y healthchecks.

### Fuentes de datos
Estado: TERMINADO

Fuentes principales:

```text
data/incoming/clientes.xlsx
data/incoming/ventas.csv
SQL Server: productos / sucursales
```

### DE-04 — Pipeline Python: extracción, validación y logging
Estado: TERMINADO

Se trabajó:

- `csv.DictReader`;
- salida `list[dict]`;
- rutas con `pathlib.Path`;
- `__file__`, `resolve()` y `parent`;
- módulos y `python -m`;
- contrato estructural;
- `set` para columnas faltantes;
- detección de encabezados duplicados;
- normalización de encabezados con `strip()`;
- excepciones;
- logging básico centralizado a consola;
- pruebas correctas e incorrectas.

## 6. Decisiones técnicas de DE-04

### Contrato de columnas

- Las columnas obligatorias deben existir.
- Una columna obligatoria faltante detiene el pipeline.
- Un encabezado duplicado detiene el pipeline.
- Las columnas adicionales se permiten.
- Una columna adicional puede permanecer en los registros extraídos; su destino final se decidirá después.

### Responsabilidades

```text
src/main.py
→ coordina el pipeline y maneja errores generales

src/extract/csv_extractor.py
→ extracción CSV y validación estructural

src/contracts/ventas_contract.py
→ declara columnas obligatorias

src/config/logging_config.py
→ configuración mínima de logging
```

### Logging

- Configuración centralizada.
- Salida a consola.
- `logging.getLogger(__name__)` por módulo.
- `FileHandler`, rotación y observabilidad avanzada quedan para una etapa posterior.

### Material de apoyo

```text
data/test_cases/
→ CSV creados para probar casos estructurales

pruebas/referencias/csv_extractor_v1.py
→ versión anterior del extractor conservada como referencia

pruebas/Ejercicios_repaso/
→ ejercicios personales/didácticos

pruebas/validacion_columnas/
→ ejercicios de sets y validación
```

`docs/notas.md` es una nota personal local y está ignorada por Git.

## 7. Archivos relevantes

```text
src/main.py
src/extract/csv_extractor.py
src/contracts/ventas_contract.py
src/config/logging_config.py

data/incoming/ventas.csv
data/incoming/clientes.xlsx
data/test_cases/

pruebas/Ejercicios_repaso/
pruebas/validacion_columnas/
pruebas/referencias/csv_extractor_v1.py
```

## 8. Ejecución actual

Desde la raíz:

```powershell
python -m src.main
```

## 9. Verificaciones realizadas en DE-04

- CSV correcto.
- Archivo inexistente.
- Columna obligatoria faltante.
- Columna adicional permitida.
- Encabezado duplicado.
- Normalización de encabezados.
- Logging en éxito y error.

## 10. Bloque activo

### DE-05 — Transformación inicial con Pandas

Objetivo:

Tomar los `list[dict]` producidos por el extractor y comenzar a trabajar el contenido de los datos con Pandas.

Secuencia prevista:

1. explicar por qué `list[dict]` deja de ser suficiente;
2. crear un `DataFrame`;
3. inspeccionar columnas, tipos y contenido;
4. conversiones y tipado;
5. fechas;
6. nulos;
7. duplicados;
8. primeras reglas de calidad;
9. preparar la separación entre válidos y rechazados.

No introducir todavía carga a RAW, watermarks, idempotencia, Airflow o dbt.

## 11. Próximo paso inmediato

Cerrar Git de DE-04:

```text
commit en feature/python-ingestion
→ merge local a main
→ push origin main
→ eliminar feature/python-ingestion
```

Después abrir el chat:

**DE-05 — Transformación inicial con Pandas**
