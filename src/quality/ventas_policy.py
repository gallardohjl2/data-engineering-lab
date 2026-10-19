"""
Política de tratamiento de calidad para ventas.
"""

import pandas as pd


def clasificar_registro(motivos: list[str]) -> str:
    """
    Clasifica un registro según sus motivos de calidad.

    Prioridad:
    RECHAZADO > REVISION > APTO
    """

    reglas_bloqueantes = {
        "Cantidad inválida",
        "Precio inválido",
        "Descuento inválido",
        "Fecha inválida",
    }

    if any(motivo in reglas_bloqueantes for motivo in motivos):
        return "RECHAZADO"

    if "Clave duplicada" in motivos:
        return "REVISION"

    return "APTO"


def aplicar_politica_calidad(
    df_diagnostico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Agrega el estado de calidad a cada registro diagnosticado.
    """

    df_resultado = df_diagnostico.copy()

    df_resultado["estado_calidad"] = df_resultado["motivos_calidad"].apply(
        clasificar_registro
    )

    return df_resultado


def separar_por_estado(
    df_clasificado: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Separa los registros según su estado de calidad.
    """
    estados_permitidos = {"APTO", "RECHAZADO", "REVISION"}

    estados_encontrados = set(df_clasificado["estado_calidad"])

    estados_invalidos = estados_encontrados - estados_permitidos

    if estados_invalidos:
        raise ValueError(
            f"Se encontraron estados de calidad inválidos: {sorted(estados_invalidos)}"
        )

    df_aptos = df_clasificado.loc[df_clasificado["estado_calidad"] == "APTO"].copy()

    df_rechazados = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "RECHAZADO"
    ].copy()

    df_revision = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "REVISION"
    ].copy()

    return df_aptos, df_rechazados, df_revision


def preparar_aptos(
    df_ventas: pd.DataFrame,
    df_clasificado: pd.DataFrame,
) -> pd.DataFrame:
    """
    Recupera los datos transformados completos
    de los registros clasificados como aptos.
    """

    df_aptos = df_clasificado.loc[
        df_clasificado["estado_calidad"] == "APTO",
        ["source_row_number", "estado_calidad"],
    ].copy()

    df_resultado = df_aptos.merge(
        df_ventas,
        on="source_row_number",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    if not df_resultado["_merge"].eq("both").all():
        raise ValueError(
            "Existen registros aptos sin correspondencia en los datos transformados."
        )

    return df_resultado.drop(columns=["_merge"])
