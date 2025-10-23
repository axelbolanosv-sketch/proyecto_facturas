"""
filters.py

Módulo que contiene las funciones para filtrar facturas
según diferentes criterios: emisor, código, monto y fecha.
Permite búsquedas recursivas y combinadas.
"""

import pandas as pd


def filtrar_facturas(df: pd.DataFrame, **filtros) -> pd.DataFrame:
    """
    Aplica filtros dinámicos a las facturas según los parámetros proporcionados.

    Args:
        df (pd.DataFrame): DataFrame con las facturas.
        **filtros: Argumentos opcionales para filtrar los datos.
            - emisor (str): Nombre del emisor (coincidencia parcial, no sensible a mayúsculas).
            - codigo (str): Código de la factura (coincidencia parcial).
            - monto_min (float): Monto mínimo de la factura.
            - fecha (str): Fecha exacta (formato YYYY-MM-DD).

    Returns:
        pd.DataFrame: Subconjunto del DataFrame original que cumple con los filtros.
    """

    resultado = df.copy()  # Copiamos para no alterar el original

    # --- Filtro por Emisor ---
    emisor = filtros.get("emisor")
    if emisor:
        resultado = resultado[resultado["Emisor"].str.contains(emisor, case=False, na=False)]

    # --- Filtro por Código ---
    codigo = filtros.get("codigo")
    if codigo:
        resultado = resultado[resultado["CodigoFactura"].str.contains(codigo, case=False, na=False)]

    # --- Filtro por Monto mínimo ---
    monto_min = filtros.get("monto_min")
    if monto_min:
        resultado = resultado[pd.to_numeric(resultado["Monto"], errors="coerce") >= monto_min]

    # --- Filtro por Fecha ---
    fecha = filtros.get("fecha")
    if fecha:
        resultado = resultado[resultado["Fecha"] == fecha]

    # --- Si no hay resultados, ofrecer una búsqueda más amplia ---
    if resultado.empty and emisor:
        print("\n No se encontraron coincidencias exactas. Intentando búsqueda parcial recursiva...")
        sub_palabras = emisor.split(" ")
        for palabra in sub_palabras:
            temp = df[df["Emisor"].str.contains(palabra, case=False, na=False)]
            if not temp.empty:
                print(f" Resultados parciales encontrados con '{palabra}'")
                resultado = pd.concat([resultado, temp])

    # Eliminar duplicados si se aplicó búsqueda recursiva
    resultado = resultado.drop_duplicates(subset=["CodigoFactura"])

    return resultado
