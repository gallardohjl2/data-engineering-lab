# Data Engineering Lab — Guía Maestra

## 1. Propósito del proyecto

Este repositorio contiene un proyecto didáctico de **Data Engineering** construido paso a paso para utilizarlo como laboratorio de clase.

La solución completa integrará:

- Excel y CSV como fuentes de archivos.
- SQL Server como fuente transaccional.
- Python puro para extracción y validación estructural.
- Pandas para conversiones, tipado, nulos, duplicados y calidad de datos.
- PostgreSQL como plataforma analítica.
- dbt para staging, transformación, pruebas, Data Warehouse y Data Marts.
- Apache Airflow para orquestación.
- Docker Compose para infraestructura.
- Power BI para visualización.
- Git y GitHub para control de versiones y trabajo con ramas.

---

# 2. Arquitectura objetivo

```text
                         FUENTES
                            │
              ┌─────────────┼─────────────┐
              ↓             ↓             ↓
        clientes.xlsx   ventas.csv    SQL Server
                                          │
                                   productos / sucursales
              └─────────────┼─────────────┘
                            ↓
                    EXTRACTORES PYTHON
                            │
                 validación estructural
                            │
                         list[dict]
                            │
                            ↓
                          Pandas
              tipos / nulos / conversiones
              duplicados / reglas / rechazo
                            │
               ┌────────────┴────────────┐
               ↓                         ↓
            VÁLIDOS                  RECHAZADOS
               │                         │
               ↓                         ↓
         estrategia carga            rejected
     full / append / incremental
               │
               ↓
              RAW
               ↓
             STAGE
               ↓
              dbt
               ↓
        DATA WAREHOUSE
               ↓
          DATA MARTS
               ↓
           POWER BI
               ↓
          DASHBOARD

Airflow orquestará el pipeline.
Docker Compose desplegará la infraestructura.
Git y GitHub versionarán el proyecto.
```

---

# 3. Principios del proyecto

## 3.1 Los datos no llegarán perfectos

Se utilizarán datos con errores controlados, por ejemplo:

- valores faltantes;
- duplicados;
- fechas inválidas;
- tipos incorrectos;
- columnas faltantes;
- columnas inesperadas;
- valores fuera de rango;
- categorías inconsistentes;
- registros rechazables.

El objetivo es aprender a construir un pipeline que detecte y gestione estos problemas.

## 3.2 Separación de responsabilidades

```text
Extractor Python puro
        ↓
estructura del archivo

Pandas
        ↓
tipos, conversiones y calidad

dbt
        ↓
transformaciones analíticas y reglas en el warehouse
```

## 3.3 Estrategias de carga contempladas

Durante el proyecto se implementarán progresivamente:

- Full Load
- Append
- Incremental Load
- Watermarks
- Checkpoints
- UPSERT
- control de lotes mediante `batch_id`
- control de archivos y checksum
- idempotencia

---

# 4. Actividad 0 — Preparación del entorno

## 4.1 Software principal

Se trabajará con:

- Visual Studio Code
- Git
- Docker Desktop
- Power BI Desktop

La mayor parte de la infraestructura se ejecutará en contenedores.

## 4.2 Verificar Docker

Desde la terminal integrada de VS Code:

```powershell
docker --version
docker compose version
docker info
```

### Propósito

- `docker --version`: verifica que el cliente Docker esté instalado.
- `docker compose version`: verifica Docker Compose.
- `docker info`: comprueba que el cliente puede comunicarse con Docker Engine.

## 4.3 Verificar Git

```powershell
git --version
git config --global user.name
git config --global user.email
```

Si la identidad no está configurada:

```powershell
git config --global user.name "José Luis"
git config --global user.email "TU_CORREO"
```

Verificar:

```powershell
git config --global --list
```

---

# 5. Crear el proyecto

Crear la carpeta:

```powershell
mkdir data-engineering-lab
cd data-engineering-lab
code .
```

El punto en:

```powershell
code .
```

significa **directorio actual**.

---

# 6. Inicializar Git

```powershell
git init
```

Verificar:

```powershell
git status
```

Si la rama aparece como `master`:

```powershell
git branch -M main
```

---

# 7. README inicial

Crear:

```text
README.md
```

Versión inicial:

```markdown
# Data Engineering Lab

Proyecto didáctico para implementar una arquitectura moderna de datos.

## Arquitectura general

Fuentes → Python → RAW → STAGE → dbt → Data Warehouse → Data Marts → Power BI

## Tecnologías

- Docker
- PostgreSQL
- SQL Server
- Python
- Pandas
- dbt
- Apache Airflow
- Power BI
- Git
- GitHub
```

Agregarlo a Git:

```powershell
git add README.md
git commit -m "docs: crear documentación inicial del proyecto"
```

Consultar historial:

```powershell
git log --oneline
```

---

# 8. Actividad 1 — Estructura base del proyecto

Crear inicialmente:

```text
data-engineering-lab/
│
├── data/
│   └── incoming/
│
├── src/
│
├── sqlserver/
│   └── init/
│
├── postgres/
│   └── init/
│
├── docs/
│
├── .env.example
├── .gitignore
└── README.md
```

En PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path data\incoming, src, sqlserver\init, postgres\init, docs
```

---

# 9. Crear `.gitignore`

Contenido inicial:

```gitignore
# ==========================================
# VARIABLES DE ENTORNO Y SECRETOS
# ==========================================

.env

# ==========================================
# PYTHON
# ==========================================

__pycache__/
*.py[cod]

.venv/
venv/

# ==========================================
# LOGS
# ==========================================

logs/
*.log

# ==========================================
# DATOS GENERADOS POR EL PIPELINE
# ==========================================

data/processed/
data/rejected/
data/temp/

# ==========================================
# DBT
# ==========================================

dbt/target/
dbt/logs/

# ==========================================
# AIRFLOW
# ==========================================

airflow/logs/

# ==========================================
# SISTEMA OPERATIVO
# ==========================================

.DS_Store
Thumbs.db
```

---

# 10. Variables de entorno

Crear:

```text
.env.example
```

Contenido:

```dotenv
# ==========================================
# SQL SERVER - FUENTE TRANSACCIONAL
# ==========================================

SQLSERVER_HOST=sqlserver-source
SQLSERVER_PORT=1433
SQLSERVER_DATABASE=VentasDB
SQLSERVER_USER=sa
SQLSERVER_PASSWORD=CAMBIAR_PASSWORD

# ==========================================
# POSTGRESQL - DATA WAREHOUSE
# ==========================================

POSTGRES_HOST=postgres-warehouse
POSTGRES_PORT=5432
POSTGRES_DATABASE=warehouse
POSTGRES_USER=warehouse_user
POSTGRES_PASSWORD=CAMBIAR_PASSWORD
```

Crear el archivo real:

```powershell
Copy-Item .env.example .env
```

Comprobar que Git lo ignora:

```powershell
git check-ignore -v .env
```

### Regla

```text
.env.example
    ↓
se versiona

.env
    ↓
NO se versiona
```

---

# 11. Modificación del README

Después de definir la arquitectura del laboratorio, el `README.md` se amplió a:

```markdown
# Data Engineering Lab

Proyecto didáctico para construir paso a paso una arquitectura moderna
de ingeniería de datos.

## Arquitectura general

Excel / CSV / SQL Server
        ↓
Python
        ↓
RAW
        ↓
dbt
        ↓
Data Warehouse
        ↓
Data Marts
        ↓
Power BI

Apache Airflow se utilizará para la orquestación del pipeline.

Docker Compose se utilizará para desplegar la infraestructura.

Git y GitHub se utilizarán para el control de versiones.

## Tecnologías principales

- Python
- Pandas
- SQL Server
- PostgreSQL
- dbt
- Apache Airflow
- Docker
- Docker Compose
- Power BI
- Git
- GitHub

## Objetivos del laboratorio

Implementar un pipeline que permita trabajar con:

- diferentes fuentes de datos;
- contratos estructurales;
- datos faltantes;
- conversiones de tipos;
- registros rechazados;
- logging;
- trazabilidad;
- cargas full;
- cargas append;
- cargas incrementales;
- watermarks;
- upserts;
- Data Warehouse;
- Data Marts;
- orquestación.
```

Después:

```powershell
git status
git add .
git commit -m "chore: crear estructura base y configuración del proyecto"
```

---

# 12. Conexión con GitHub

Crear en GitHub un repositorio vacío llamado:

```text
data-engineering-lab
```

No crear otro README ni otro `.gitignore`.

Agregar el remoto:

```powershell
git remote add origin URL_DEL_REPOSITORIO
```

Comprobar:

```powershell
git remote -v
```

Primer envío:

```powershell
git push -u origin main
```

---

# 13. Actividad 1.5 — Trabajo con ramas

## 13.1 Regla del proyecto

```text
main
    ↓
versión estable

feature/...
    ↓
nuevas funcionalidades

fix/...
    ↓
correcciones

docs/...
    ↓
documentación
```

No se utilizará inicialmente un Git Flow complejo con `develop`, `release` o `hotfix`.

## 13.2 Comprobar rama actual

```powershell
git branch
git status
```

Antes de crear una rama nueva:

```powershell
git switch main
git pull origin main
```

## 13.3 Crear rama

Ejemplo:

```powershell
git switch -c feature/docker-infra
```

Comprobar:

```powershell
git branch
```

---

# 14. Qué es HEAD

`HEAD` indica dónde estamos trabajando actualmente.

Ejemplo:

```text
HEAD
 ↓
feature/docker-infra
 ↓
commit actual
```

Al cambiar:

```powershell
git switch main
```

`HEAD` apunta a `main`.

---

# 15. Primer ejercicio con una rama

Crear:

```text
docs/git-workflow.md
```

Documentar ahí el flujo de ramas.

Agregar y confirmar:

```powershell
git add docs/git-workflow.md
git commit -m "docs: documentar flujo de trabajo con ramas"
```

Consultar:

```powershell
git log --oneline --decorate -5
```

---

# 16. Subir una rama

```powershell
git push -u origin feature/docker-infra
```

Mostrar todas las ramas:

```powershell
git branch -a
```

---

# 17. Pull Request

En GitHub:

```text
base: main
compare: feature/docker-infra
```

Flujo:

```text
feature
   ↓
push
   ↓
GitHub
   ↓
Pull Request
   ↓
revisión
   ↓
merge
   ↓
main
```

Revisar especialmente:

```text
Files changed
```

---

# 18. Diferencia entre merge, push y pull

## Merge

Integra historias de ramas.

Puede hacerse:

```powershell
git merge feature/...
```

o mediante un Pull Request en GitHub.

## Push

Envía cambios:

```text
computadora
    ↓
GitHub
```

Ejemplo:

```powershell
git push
```

## Pull

Trae cambios:

```text
GitHub
    ↓
computadora
```

Ejemplo:

```powershell
git pull origin main
```

### Caso utilizado en el laboratorio

Se hizo el merge mediante Pull Request en GitHub.

Por eso después:

```powershell
git switch main
git pull origin main
```

El `pull` actualiza el `main` local con el `main` que ya fue modificado en GitHub.

---

# 19. Merge local como alternativa

También sería válido:

```powershell
git switch main
git merge feature/docker-infra
git push origin main
```

En ese caso:

```text
feature local
     ↓
git merge
     ↓
main local
     ↓
git push
     ↓
main GitHub
```

---

# 20. Eliminar ramas terminadas

Norma del proyecto:

> Rama fusionada = rama eliminada.

Después del merge:

```powershell
git switch main
git pull origin main
git branch -d feature/docker-infra
```

Si la rama remota todavía existe:

```powershell
git push origin --delete feature/docker-infra
```

Limpiar referencias:

```powershell
git fetch --prune
```

No se pierde el trabajo: los commits y el Pull Request permanecen en el historial.

---

# 21. Flujo oficial de trabajo

A partir de ahora cada actividad importante seguirá:

```text
1. git switch main

2. git pull origin main

3. git switch -c feature/nombre

4. trabajar

5. git status

6. git add .

7. git commit

8. git push

9. Pull Request

10. revisión

11. merge

12. git switch main

13. git pull origin main

14. eliminar rama
```

---

# 22. Estado actual del proyecto

Hasta este momento se ha trabajado:

- preparación de VS Code;
- Docker y Git verificados;
- repositorio Git creado;
- rama principal `main`;
- README inicial;
- estructura base;
- `.gitignore`;
- `.env.example`;
- `.env` excluido del repositorio;
- README ampliado;
- conexión con GitHub;
- ramas `feature`;
- concepto de `HEAD`;
- commits;
- push;
- Pull Request;
- merge;
- pull;
- eliminación de ramas.

---

# 23. Siguiente actividad

La siguiente etapa será:

## Actividad 2 — Docker Compose desde cero

Se creará una nueva rama:

```powershell
git switch main
git pull origin main
git switch -c feature/docker-foundation
```

Se construirá inicialmente:

```text
Docker Compose
│
├── sqlserver-source
│   └── SQL Server / VentasDB
│
└── postgres-warehouse
    └── PostgreSQL / warehouse
```

Se estudiará paso a paso:

- `compose.yaml`;
- `services`;
- imágenes;
- contenedores;
- nombres;
- puertos;
- variables de entorno;
- volúmenes;
- persistencia;
- redes;
- DNS interno de Docker;
- healthchecks;
- comunicación entre contenedores.

---

# 24. Política de actualización de esta guía

Este archivo será el **documento maestro vivo del proyecto**.

Después de cada actividad se actualizarán:

1. objetivo de la actividad;
2. conceptos explicados;
3. estructura del proyecto;
4. archivos creados o modificados;
5. código y comandos utilizados;
6. explicación de cada comando;
7. verificaciones realizadas;
8. errores encontrados y solución;
9. commits realizados;
10. rama utilizada;
11. estado actual del proyecto;
12. siguiente actividad.

Los documentos Word y PDF se generarán únicamente cuando se necesite un corte formal para entrega o distribución.

---

**Documento vivo:** `GUIA_MAESTRA_DATA_ENGINEERING.md`


---

# 25. Actividad 2 — Docker Compose: infraestructura base

## 25.1 Objetivo

Construir la infraestructura inicial del laboratorio con Docker Compose utilizando:

- SQL Server como sistema transaccional de origen.
- PostgreSQL como plataforma analítica.
- pgAdmin como herramienta gráfica de administración.
- Named volumes para persistencia.
- Una red Docker para comunicación entre servicios.
- Variables de entorno para separar configuración y secretos.

Arquitectura obtenida:

```text
Docker Compose
│
├── sqlserver-source
│   └── SQL Server / VentasDB
│       ├── Productos
│       └── Sucursales
│
├── postgres-warehouse
│   └── PostgreSQL / warehouse
│       ├── raw
│       ├── stage
│       ├── warehouse
│       └── marts
│
└── pgadmin
    └── administración visual de PostgreSQL
```

## 25.2 Rama de trabajo

```powershell
git switch main
git pull origin main
git switch -c feature/docker-foundation
```

La actividad se desarrolló en:

```text
feature/docker-foundation
```

## 25.3 Conceptos estudiados en `compose.yaml`

- `services`
- `image`
- `container_name`
- `environment`
- `ports`
- `volumes`
- `networks`
- `restart`

SQL Server:

```yaml
sqlserver-source:
  image: mcr.microsoft.com/mssql/server:2025-CU8-ubuntu-24.04
  container_name: de-sqlserver-source
  restart: unless-stopped

  environment:
    ACCEPT_EULA: "Y"
    MSSQL_SA_PASSWORD: ${SQLSERVER_PASSWORD}
    MSSQL_PID: "Developer"

  ports:
    - "1433:1433"

  volumes:
    - sqlserver-data:/var/opt/mssql

  networks:
    - data-engineering-net
```

PostgreSQL:

```yaml
postgres-warehouse:
  image: postgres:16-bookworm
  container_name: de-postgres-warehouse
  restart: unless-stopped

  environment:
    POSTGRES_DB: ${POSTGRES_DATABASE}
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

  ports:
    - "5432:5432"

  volumes:
    - postgres-data:/var/lib/postgresql/data

  networks:
    - data-engineering-net
```

pgAdmin:

```yaml
pgadmin:
  image: dpage/pgadmin4
  container_name: de-pgadmin
  restart: unless-stopped

  environment:
    PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
    PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}

  ports:
    - "5050:80"

  networks:
    - data-engineering-net
```

## 25.4 Puertos: host vs contenedor

La sintaxis:

```yaml
ports:
  - "5433:5432"
```

significa:

```text
HOST : CONTENEDOR
5433 : 5432
```

Regla del laboratorio:

```text
Desde Windows
→ localhost:PUERTO_HOST

Entre contenedores
→ NOMBRE_SERVICIO:PUERTO_INTERNO
```

Ejemplos:

```text
SSMS en Windows
→ localhost,1433

pgAdmin en Docker
→ postgres-warehouse:5432

Futuro extractor Python
→ sqlserver-source:1433
→ postgres-warehouse:5432
```

## 25.5 `docker exec` vs `docker compose exec`

`docker exec` trabaja directamente con el contenedor:

```powershell
docker exec -it de-postgres-warehouse bash
```

`docker compose exec` trabaja con el servicio definido en Compose:

```powershell
docker compose exec postgres-warehouse bash
```

En este proyecto se preferirá `docker compose exec` para servicios administrados por Compose.

## 25.6 Redes Docker

SQL Server y PostgreSQL comparten inicialmente:

```text
data-engineering-net
```

Eso no significa que deban intercambiar datos directamente.

La red permitirá que futuros servicios alcancen ambos motores:

```text
SQL Server
     ↑
     │
Python / Airflow
     │
     ↓
PostgreSQL
```

Más adelante puede evolucionarse a:

```text
source-net
    │
SQL Server
    │
Python / Airflow
    │
warehouse-net
    │
PostgreSQL
```

## 25.7 Nombre lógico vs nombre real

Ejemplo:

```yaml
networks:
  backend:
    external: true
    name: data-engineering-net
```

```text
backend
→ nombre lógico dentro del Compose

data-engineering-net
→ nombre real en Docker
```

Lo mismo aplica a los volúmenes.

`external: true` indica que Compose debe reutilizar un recurso ya existente.

## 25.8 Named Volume vs Bind Mount

Named Volume:

```yaml
volumes:
  - sqlserver-data:/var/opt/mssql
```

Bind Mount:

```yaml
volumes:
  - ./postgres/init:/docker-entrypoint-initdb.d:ro
```

`ro` significa `read only`.

## 25.9 Persistencia

```powershell
docker compose down
```

elimina contenedores y red del proyecto, pero normalmente conserva los named volumes.

```powershell
docker compose down -v
```

también elimina los volúmenes administrados por Compose.

No utilizar `-v` cuando se desea conservar información.

## 25.10 `restart`

Se estudió:

```yaml
restart: unless-stopped
```

Permite reiniciar el contenedor cuando Docker Engine vuelve a iniciar, salvo que el usuario lo haya detenido explícitamente.

No sustituye a `docker compose up -d` si los contenedores fueron eliminados.

## 25.11 `depends_on`

`depends_on` controla dependencias de arranque.

```yaml
depends_on:
  postgres-warehouse:
    condition: service_healthy
```

Condiciones revisadas:

- `service_started`
- `service_healthy`
- `service_completed_successfully`

SQL Server y PostgreSQL no dependen uno del otro, por lo que no se agregó una dependencia artificial.

## 25.12 Docker Compose vs Airflow

```text
Docker Compose
→ orquesta infraestructura

Airflow
→ orquesta el pipeline de datos
```

## 25.13 Error real — imagen SQL Server

Error:

```text
failed to resolve reference
mcr.microsoft.com/mssql/server:2025-GA-ubuntu
```

Solución:

```text
mcr.microsoft.com/mssql/server:2025-CU8-ubuntu-24.04
```

Aprendizaje: utilizar etiquetas existentes y reproducibles.

## 25.14 Tamaño de imagen SQL Server

La imagen de SQL Server es considerable.

Docker reutiliza las capas descargadas después de la primera descarga.

Distribución manual:

```powershell
docker save -o sqlserver2025.tar mcr.microsoft.com/mssql/server:2025-CU8-ubuntu-24.04
```

Carga:

```powershell
docker load -i sqlserver2025.tar
```

## 25.15 Base PostgreSQL `warehouse`

La base fue creada mediante:

```yaml
POSTGRES_DB: ${POSTGRES_DATABASE}
```

En `.env`:

```dotenv
POSTGRES_DATABASE=warehouse
```

```text
POSTGRES_DATABASE
→ variable propia del proyecto

POSTGRES_DB
→ variable entendida por la imagen PostgreSQL
```

## 25.16 Sistema fuente SQL Server

```text
VentasDB
│
├── dbo.Productos
└── dbo.Sucursales
```

Scripts:

```text
01-create-database.sql
→ crea la estructura

02-seed-source-data.sql
→ agrega datos al sistema FUENTE
```

Los datos semilla no se cargan manualmente al Warehouse; posteriormente serán extraídos mediante Python.

Incluyen errores controlados:

- valores NULL;
- precios negativos;
- categorías inconsistentes;
- espacios adicionales;
- diferencias de mayúsculas/minúsculas;
- registros inactivos.

## 25.17 Capas PostgreSQL

Dentro de `warehouse`:

```text
raw
stage
warehouse
marts
```

```text
RAW
→ qué llegó

STAGE
→ tipado, limpieza y normalización

WAREHOUSE
→ modelo dimensional

MARTS
→ consumo analítico
```

Por ahora los schemas permanecen sin datos del pipeline.

## 25.18 Ejecución de scripts PostgreSQL con pipe

```powershell
Get-Content .\postgres\init\01-create-schemas.sql |
docker compose exec -T postgres-warehouse psql -U warehouse_user -d warehouse
```

`Get-Content` lee el archivo.

`|` envía la salida como entrada al siguiente comando.

`-T` deshabilita la pseudo-terminal.

## 25.19 pgAdmin

Acceso:

```text
http://localhost:5050
```

Conexión desde pgAdmin container:

```text
Host: postgres-warehouse
Port: 5432
Database: warehouse
User: warehouse_user
```

## 25.20 Error real — pgAdmin

Configuración incorrecta:

```text
Host: pgadmin
Port: 5433
```

Configuración correcta:

```text
Host: postgres-warehouse
Port: 5432
```

Aprendizaje:

```text
Windows
→ localhost:PUERTO_HOST

Contenedor
→ NOMBRE_SERVICIO:PUERTO_INTERNO
```

## 25.21 Estado final de la Actividad 2

```text
Docker Compose
│
├── SQL Server
│   └── VentasDB
│       ├── Productos
│       └── Sucursales
│
├── PostgreSQL
│   └── warehouse
│       ├── raw
│       ├── stage
│       ├── warehouse
│       └── marts
│
└── pgAdmin
```

SQL Server contiene datos fuente.

PostgreSQL tiene su estructura inicial pero todavía no contiene datos extraídos.

Todavía no existe transferencia entre ambos motores.

## 25.22 Cierre Git

Revisión:

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

Confirmar que `.env` NO esté incluido.

Commit recomendado:

```powershell
git commit -m "feat: agregar infraestructura base con SQL Server PostgreSQL y pgAdmin"
```

Subir:

```powershell
git push -u origin feature/docker-foundation
```

Pull Request:

```text
feature/docker-foundation
        ↓
main
```

Después del merge:

```powershell
git switch main
git pull origin main
git branch -d feature/docker-foundation
git fetch --prune
```

## 25.23 Siguiente actividad

Fuentes de archivos:

```text
data/
└── incoming/
    ├── ventas.csv
    └── clientes.xlsx
```

Contendrán errores intencionales para trabajar contratos, nulos, tipos, fechas, duplicados y registros rechazados.

Después:

```text
Fuente
   ↓
Extractor Python puro
   ↓
contrato estructural
   ↓
list[dict]
   ↓
Pandas
   ↓
tipos / nulos / conversiones / validaciones
   ↓
carga
   ↓
PostgreSQL RAW
```

Ramas previstas:

```text
feature/source-data
feature/python-ingestion
```
