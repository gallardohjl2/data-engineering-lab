# Flujo de trabajo con Git

Este proyecto utiliza ramas para desarrollar nuevas funcionalidades.

## Rama principal

`main`

Contiene la versión estable del proyecto.

## Ramas de funcionalidad

Formato:

`feature/nombre-funcionalidad`

Ejemplos:

- feature/docker-infra
- feature/csv-extractor
- feature/data-validation
- feature/dbt-models
- feature/airflow

## Flujo de trabajo

1. Actualizar main.
2. Crear una rama feature.
3. Realizar cambios.
4. Crear commits.
5. Subir la rama a GitHub.
6. Crear un Pull Request.
7. Revisar los cambios.
8. Fusionar con main.
9. Actualizar main local.
10. Eliminar la rama terminada.