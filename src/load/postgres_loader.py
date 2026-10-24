import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def conectar_postgres():
    """
    Establece una conexión con PostgreSQL.
    """

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


def cargar_ventas_aptas(df_aptos, conexion):
    """
    Inserta los registros aptos en raw.ventas.
    """

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
    """
    Inserta registros rechazados o en revisión,
    conservando sus valores originales.
    """

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
            descuento_pct
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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


def limpiar_ventas(conexion):
    """
    Vacía las tablas de ventas antes de una carga full.
    """
    with conexion.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE raw.ventas, raw.ventas_problemas")
