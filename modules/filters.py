# modules/filters.py (VERSIÓN CON LÓGICA OR/AND INTELIGENTE)
# Contiene la lógica de filtrado dinámico, agrupando filtros
# de la misma columna con 'OR' y entre columnas con 'AND'.

import pandas as pd
from collections import defaultdict
import numpy as np # Necesario para crear la máscara base

def aplicar_filtros_dinamicos(df: pd.DataFrame, filtros: list) -> pd.DataFrame:
    """
    Aplica una lista de filtros al DataFrame con lógica 'OR' y 'AND'.

    - Lógica "Y" (AND): Se usa cuando se filtra por COLUMNAS diferentes.
      (Ej. Assignee: "Anggie" Y Status: "Pending")
    - Lógica "O" (OR): Se usa cuando se añaden varios filtros para la MISMA columna.
      (Ej. Assignee: "Anggie" O Assignee: "Kendall")

    Args:
        df (pd.DataFrame): El DataFrame original (ej. df_staging).
        filtros (list): La lista de filtros de st.session_state (ej.
                        [{'columna': 'Assignee', 'valor': 'Anggie'},
                         {'columna': 'Assignee', 'valor': 'Kendall'}])

    Returns:
        pd.DataFrame: El DataFrame filtrado.
    """

    # Si no hay filtros, devuelve el DataFrame original sin procesar.
    if not filtros:
        return df.copy()

    # --- 1. Agrupar Filtros por Columna ---
    # Se usa defaultdict(list) para que la estructura sea:
    # {'Assignee': ['Anggie', 'Kendall'], 'Status': ['Pending']}
    filtros_agrupados = defaultdict(list)
    for filtro in filtros:
        # 'filtro['columna']' (ej. 'Assignee') es la clave.
        # 'filtro['valor']' (ej. 'Anggie') se añade a la lista.
        filtros_agrupados[filtro['columna']].append(filtro['valor'])

    # Copia el DataFrame para no modificar el original en 'staging'.
    resultado = df.copy()

    # --- 2. Aplicar Lógica AND (exterior) y OR (interior) ---
    
    # Bucle exterior (Lógica AND): Itera sobre cada columna que tiene filtros.
    # (ej. 'Assignee', luego 'Status')
    for columna, valores in filtros_agrupados.items():
        
        try:
            # --- Bucle interior (Lógica OR) ---
            # 'mascara_or_columna': Crea una máscara de Pandas (una Serie de booleanos)
            # inicialmente llena de 'False', con el mismo índice que el DataFrame.
            mascara_or_columna = pd.Series([False] * len(resultado), index=resultado.index)

            # Convierte la columna del DataFrame a string para búsquedas .str
            # Esto asegura que la búsqueda funcione incluso en columnas numéricas/fecha.
            columna_como_str = resultado[columna].astype(str)

            # Itera sobre cada valor para ESTA columna (ej. 'Anggie', luego 'Kendall')
            for valor in valores:
                # 'mascara_parcial': Crea un filtro para este valor específico.
                # (ej. todas las filas donde 'Assignee' contiene 'Anggie')
                mascara_parcial = columna_como_str.str.contains(valor, case=False, na=False)
                
                # 'mascara_or_columna | mascara_parcial': Combina la máscara
                # principal con la máscara parcial usando el operador 'OR' (|).
                # La máscara ahora es (Falso... O ...Contiene 'Anggie')
                # En la siguiente iteración será: (...Contiene 'Anggie' O ...Contiene 'Kendall')
                mascara_or_columna = mascara_or_columna | mascara_parcial

            # --- Fin Bucle OR ---

            # 'resultado = resultado[mascara_or_columna]': Aplica el filtro 'OR'
            # combinado al DataFrame.
            # Esto reduce el DataFrame ANTES de pasar a la siguiente columna (AND).
            resultado = resultado[mascara_or_columna]

        except Exception as e:
            # 'pass': Si la columna no existe (ej. error en el nombre) o falla 
            # .str.contains, simplemente se ignora este filtro y se continúa.
            print(f"Error al aplicar filtro en '{columna}' con valores '{valores}': {e}")
            pass
    
    # 'return resultado': Devuelve el DataFrame final filtrado.
    return resultado