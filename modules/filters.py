# modules/filters.py
"""
Módulo de Filtrado Dinámico (Filters).

Contiene la lógica de filtrado dinámico.
Versión Mejorada: Soporta operadores lógicos (>, <, =, contains) para filtrado numérico y de texto.
"""

import pandas as pd
from collections import defaultdict
import numpy as np 

def aplicar_filtros_dinamicos(df: pd.DataFrame, filtros: list) -> pd.DataFrame:
    """
    Aplica una lista de filtros al DataFrame con lógica 'OR' y 'AND'.

    Args:
        df (pd.DataFrame): El DataFrame original.
        filtros (list): Lista de diccionarios. 
                        Ej: [{'columna': 'Total', 'valor': 1000, 'operator': '>'}, ...]

    Returns:
        pd.DataFrame: El DataFrame filtrado.
    """
    if not filtros:
        return df.copy()

    # 1. Agrupar Filtros por Columna (conservando el objeto filtro completo)
    filtros_agrupados = defaultdict(list)
    for f in filtros:
        # Soporte retrocompatible: si no tiene 'columna', lo ignoramos
        if 'columna' in f:
            filtros_agrupados[f['columna']].append(f)

    resultado = df.copy()

    # 2. Aplicar Lógica
    for columna, lista_filtros in filtros_agrupados.items():
        if columna not in resultado.columns:
            continue
            
        try:
            # Preparar datos de la columna para comparación rápida
            series = resultado[columna]
            
            # Versión numérica (forzando conversión, errores a NaN)
            series_num = pd.to_numeric(series, errors='coerce')
            # Versión string (para búsquedas de texto)
            series_str = series.astype(str)

            # Máscara acumulativa para la columna (Lógica OR entre valores de la misma columna)
            # Empezamos con todo Falso, para ir sumando coincidencias.
            mascara_or_columna = pd.Series([False] * len(resultado), index=resultado.index)

            for f in lista_filtros:
                val = f.get('valor')
                op = f.get('operator', 'contains') # Por defecto 'contains' (texto)
                
                mask_filtro = None

                # --- Lógica Numérica ---
                if op in ['>', '<', '>=', '<=']:
                    try:
                        val_num = float(val)
                        if op == '>': mask_filtro = series_num > val_num
                        elif op == '<': mask_filtro = series_num < val_num
                        elif op == '>=': mask_filtro = series_num >= val_num
                        elif op == '<=': mask_filtro = series_num <= val_num
                    except (ValueError, TypeError):
                        # Si el valor no es numérico, este filtro falla silenciosamente (todo False)
                        mask_filtro = pd.Series([False] * len(resultado), index=resultado.index)

                # --- Lógica Exacta ---
                elif op == '==':
                    # Intentamos match exacto string, o numérico si aplica
                    mask_filtro = series_str == str(val)

                # --- Lógica Texto (Default) ---
                else: # contains
                    mask_filtro = series_str.str.contains(str(val), case=False, na=False)

                # Acumular con OR (|)
                if mask_filtro is not None:
                    mascara_or_columna = mascara_or_columna | mask_filtro.fillna(False)

            # Aplicar la máscara de esta columna al resultado (Lógica AND entre columnas)
            resultado = resultado[mascara_or_columna]

        except Exception as e:
            print(f"Error filtro en '{columna}': {e}")
            pass
    
    return resultado