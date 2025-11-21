# modules/filters.py
"""
Módulo de Filtrado Dinámico (Filters).

Contiene la lógica de filtrado dinámico, agrupando filtros de la misma columna
con lógica 'OR' y entre columnas diferentes con lógica 'AND'.
"""

import pandas as pd
from collections import defaultdict
import numpy as np 

def aplicar_filtros_dinamicos(df: pd.DataFrame, filtros: list) -> pd.DataFrame:
    """
    Aplica una lista de filtros al DataFrame con lógica 'OR' y 'AND'.

    Lógica:
    - Lógica "Y" (AND): Se usa cuando se filtra por COLUMNAS diferentes.
      (Ej. Assignee: "Anggie" Y Status: "Pending")
    - Lógica "O" (OR): Se usa cuando se añaden varios filtros para la MISMA columna.
      (Ej. Assignee: "Anggie" O Assignee: "Kendall")

    Args:
        df (pd.DataFrame): El DataFrame original (ej. df_staging).
        filtros (list): La lista de filtros de st.session_state.
                        Ej: [{'columna': 'Assignee', 'valor': 'Anggie'}, ...]

    Returns:
        pd.DataFrame: El DataFrame filtrado.
    """

    # Optimización: Si no hay filtros, devuelve copia del original.
    if not filtros:
        return df.copy()

    # --- 1. Agrupar Filtros por Columna ---
    # Estructura objetivo: {'Assignee': ['Anggie', 'Kendall'], 'Status': ['Pending']}
    filtros_agrupados = defaultdict(list)
    for filtro in filtros:
        filtros_agrupados[filtro['columna']].append(filtro['valor'])

    # Copia para trabajo
    resultado = df.copy()

    # --- 2. Aplicar Lógica AND (exterior) y OR (interior) ---
    
    # Bucle exterior (Lógica AND): Itera sobre cada columna distinta.
    for columna, valores in filtros_agrupados.items():
        
        try:
            # --- Bucle interior (Lógica OR) ---
            # Inicializa máscara base en Falso
            mascara_or_columna = pd.Series([False] * len(resultado), index=resultado.index)

            # Convierte columna a string para búsquedas de texto robustas
            columna_como_str = resultado[columna].astype(str)

            for valor in valores:
                # Crea máscara parcial para el valor actual
                mascara_parcial = columna_como_str.str.contains(valor, case=False, na=False)
                
                # Acumula con OR (|)
                mascara_or_columna = mascara_or_columna | mascara_parcial

            # --- Aplicación del Filtro ---
            # Aplica la máscara combinada al DataFrame, reduciéndolo para la siguiente iteración (AND)
            resultado = resultado[mascara_or_columna]

        except Exception as e:
            # Manejo de errores no bloqueante (si columna no existe, ignora filtro)
            print(f"Error al aplicar filtro en '{columna}' con valores '{valores}': {e}")
            pass
    
    return resultado