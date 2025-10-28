"""
filters.py (Versión Dinámica y Multi-filtro)

Módulo que aplica una lista de filtros dinámicos a un DataFrame.
"""

import pandas as pd

def aplicar_filtros_dinamicos(df: pd.DataFrame, filtros: list) -> pd.DataFrame:
    """
    Aplica una lista de filtros al DataFrame.
    Cada filtro es un diccionario: {'columna': 'NombreCol', 'valor': 'ValorBuscar'}

    Args:
        df (pd.DataFrame): El DataFrame original.
        filtros (list): Una lista de diccionarios de filtros.

    Returns:
        pd.DataFrame: El DataFrame filtrado.
    """
    
    # Empezamos con una copia del DataFrame completo
    resultado = df.copy()

    # Iteramos sobre cada filtro que el usuario añadió a la lista
    for filtro in filtros:
        columna = filtro['columna']
        valor = filtro['valor']
        
        # Si el filtro es válido, lo aplicamos
        if not valor or not columna:
            continue
            
        # Intentamos aplicar el filtro
        # Usamos .astype(str) para asegurarnos de que podamos buscar
        # texto parcial en cualquier columna (incluso en las numéricas)
        try:
            resultado = resultado[
                resultado[columna].astype(str).str.contains(valor, case=False, na=False)
            ]
        except Exception as e:
            # Si la columna no existiera (algo raro), lo reportamos
            print(f"Error al aplicar filtro en '{columna}' con valor '{valor}': {e}")
            pass

    return resultado