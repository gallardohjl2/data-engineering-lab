"""
Reglas de calidad para los datos de ventas.
"""

import pandas as pd


def validar_cantidad(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica cantidades nulas o menores o iguales a cero.
    """

    return df_ventas["cantidad"].isna() | (df_ventas["cantidad"] <= 0)


def validar_precio(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica precios unitarios nulos o menores
    o iguales a cero.
    """

    return df_ventas["precio_unitario"].isna() | (df_ventas["precio_unitario"] <= 0)


def validar_descuento(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica descuentos nulos o fuera del rango de 0 a 100.
    """

    return (
        df_ventas["descuento_pct"].isna()
        | (df_ventas["descuento_pct"] < 0)
        | (df_ventas["descuento_pct"] > 100)
    )


def validar_fecha(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica fechas nulas o que no pudieron convertirse.
    """

    return df_ventas["fecha"].isna()


def validar_duplicados(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica todas las filas que comparten
    una misma combinación de venta_id y linea_id.
    """

    return df_ventas.duplicated(
        subset=["venta_id", "linea_id"],
        keep=False,
    )


def diagnosticar_calidad(df_ventas: pd.DataFrame) -> pd.Series:
    """
    Identifica los registros que incumplen
    al menos una regla de calidad de ventas.
    """

    return (
        validar_cantidad(df_ventas)
        | validar_precio(df_ventas)
        | validar_descuento(df_ventas)
        | validar_fecha(df_ventas)
        | validar_duplicados(df_ventas)
    )


def obtener_motivos(registro: pd.Series) -> list[str]:
    """
    Convierte los indicadores booleanos de calidad
    de un registro en una lista de motivos descriptivos.
    """

    motivos = []

    if registro["error_cantidad"]:
        motivos.append("Cantidad inválida")

    if registro["error_precio"]:
        motivos.append("Precio inválido")

    if registro["error_descuento"]:
        motivos.append("Descuento inválido")

    if registro["error_fecha"]:
        motivos.append("Fecha inválida")

    if registro["error_duplicado"]:
        motivos.append("Clave duplicada")

    return motivos


def diagnosticar_calidad_detallada(
    df_ventas: pd.DataFrame,
) -> pd.DataFrame:
    """
    Construye un diagnóstico detallado de calidad
    para cada registro de ventas.
    """

    df_diagnostico = df_ventas[["venta_id", "linea_id", "source_row_number"]].copy()

    df_diagnostico["error_cantidad"] = validar_cantidad(df_ventas)
    df_diagnostico["error_precio"] = validar_precio(df_ventas)
    df_diagnostico["error_descuento"] = validar_descuento(df_ventas)
    df_diagnostico["error_fecha"] = validar_fecha(df_ventas)
    df_diagnostico["error_duplicado"] = validar_duplicados(df_ventas)

    df_diagnostico["motivos_calidad"] = df_diagnostico.apply(
        obtener_motivos,
        axis=1,
    )

    df_diagnostico["tiene_problemas"] = df_diagnostico["motivos_calidad"].apply(bool)

    return df_diagnostico


def construir_vista_investigacion(
    records: list[dict[str, str | int]],
    df_diagnostico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Relaciona los registros con problemas de calidad
    con sus valores originales.
    """

    df_original = pd.DataFrame(records)

    diagnostico_problemas = df_diagnostico.loc[
        df_diagnostico["tiene_problemas"],
        [
            "source_row_number",
            "motivos_calidad",
            "tiene_problemas",
            "estado_calidad",
        ],
    ].copy()

    df_investigacion = diagnostico_problemas.merge(
        df_original,
        on="source_row_number",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if not df_investigacion["_merge"].eq("both").all():
        raise ValueError(
            "Existen registros diagnosticados sin correspondencia en el origen."
        )

    return df_investigacion.drop(columns=["_merge"])
