"""
Punto de entrada principal del pipeline.
"""

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
    """
    Coordina la extracción, transformación y calidad de las ventas.
    """

    setup_logging(PROJECT_ROOT)

    logger.info("Inicio del pipeline.")

    try:
        if modo_carga not in ("full", "append"):
            raise ValueError(
                f"Modo de carga no válido: {modo_carga}. "
                "Los valores permitidos son 'full' y 'append'."
            )
        # Extracción del csv
        records = extract_csv(
            file_path=archivo,
            required_columns=REQUIRED_COLUMNS,
        )

        # NUEVO: calcular el hash del archivo
        hash_archivo = hashlib.sha256(archivo.read_bytes()).hexdigest()

        logger.info("SHA-256 del archivo: %s", hash_archivo)

        logger.info("Extracción finalizada correctamente.")

        if records:
            df_ventas = transform_ventas(records)
            logger.info("Transformación inicial de ventas finalizada correctamente.")

            # 1. Diagnosticar la calidad de los registros
            df_diagnostico = diagnosticar_calidad_detallada(df_ventas)

            # 2. Aplicar la política de calidad
            df_clasificado = aplicar_politica_calidad(df_diagnostico)

            # 3. Preparar registros aptos con datos transformados
            df_aptos_final = preparar_aptos(
                df_ventas,
                df_clasificado,
            )

            # 4. Recuperar registros problemáticos con sus valores originales
            df_investigacion = construir_vista_investigacion(
                records,
                df_clasificado,
            )

            # 5. Separar rechazados y registros en revisión
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

            # Persistencia de las tres salidas en una sola transacción
            with conectar_postgres() as conexion:
                if modo_carga == "full":
                    limpiar_ventas(conexion)

                aptos_insertados = cargar_ventas_aptas(
                    df_aptos_final,
                    conexion,
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
                "Persistencia completada: %s aptos, %s rechazados y %s en revisión insertados.",
                aptos_insertados,
                rechazados_insertados,
                revision_insertados,
            )

            logger.info(
                "Carga de aptos: %s procesados, %s insertados y %s omitidos por duplicidad.",
                len(df_aptos_final),
                aptos_insertados,
                aptos_omitidos,
            )

            logger.info(
                "Carga de rechazados: %s procesados, %s insertados y %s omitidos por duplicidad.",
                len(df_rechazados_final),
                rechazados_insertados,
                rechazados_omitidos,
            )

            logger.info(
                "Carga de revisión: %s procesados, %s insertados y %s omitidos por duplicidad.",
                len(df_revision_final),
                revision_insertados,
                revision_omitidos,
            )

        else:
            logger.warning(
                "El archivo fue extraído correctamente, pero no contiene registros."
            )

    except FileNotFoundError as error:
        logger.error(
            "Error de archivo: %s",
            error,
        )
        raise

    except ValueError as error:
        logger.error(
            "Error durante el procesamiento: %s",
            error,
        )
        raise

    except psycopg.Error:
        logger.exception("Error durante la conexión o persistencia en PostgreSQL.")
        raise

    finally:
        logger.info("Fin de la ejecución.")


if __name__ == "__main__":
    main()
