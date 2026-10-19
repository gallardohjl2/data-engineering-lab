"""
Transformaciones de los datos de ventas.
"""

import pandas as pd


def transform_ventas(records: list[dict]) -> pd.DataFrame:
    """
    Convierte los registros extraídos en un DataFrame
    y realiza las conversiones iniciales de tipos de ventas.
    """

    df_ventas = pd.DataFrame(records)

    df_ventas["cantidad"] = pd.to_numeric(
        df_ventas["cantidad"],
        errors="coerce",
    )

    df_ventas["precio_unitario"] = pd.to_numeric(
        df_ventas["precio_unitario"],
        errors="coerce",
    )

    df_ventas["descuento_pct"] = pd.to_numeric(
        df_ventas["descuento_pct"],
        errors="coerce",
    )

    df_ventas["fecha"] = pd.to_datetime(
        df_ventas["fecha"],
        format="%Y-%m-%d",
        errors="coerce",
    )

    return df_ventas
