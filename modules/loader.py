"""
loader.py

Módulo encargado de la carga y validación de datos
desde un archivo Excel que contiene las facturas.
"""

import pandas as pd


def cargar_datos(ruta_archivo: str) -> pd.DataFrame:
    """
    Carga un archivo Excel que contiene las facturas.

    Args:
        ruta_archivo (str): Ruta completa del archivo Excel (ej. 'data/Header_Facturas.xlsx').

    Returns:
        pd.DataFrame: Un DataFrame con los datos cargados y limpiados.
                      Si hay error, devuelve un DataFrame vacío.
    """
    try:
        # Cargar el archivo Excel usando pandas
        # Usamos dtype=str para asegurar que todos los datos (como IDs) se lean como texto
        df = pd.read_excel(ruta_archivo, dtype=str)

        # Limpiar los encabezados de columnas (quitar espacios)
        df.columns = [col.strip() for col in df.columns]

        # Reemplazar valores nulos (NaN, NaT) por cadenas vacías
        df = df.fillna("")

        print(f" Archivo cargado correctamente con {len(df)} registros.")
        return df

    except FileNotFoundError:
        print(f" Error: No se encontró el archivo en la ruta: {ruta_archivo}")
        return pd.DataFrame()
    except Exception as e:
        # Esto capturará errores si el archivo no es un Excel válido
        print(f" Error al cargar el archivo Excel: {e}")
        return pd.DataFrame()