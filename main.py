"""
main.py

Archivo principal del buscador de facturas.
Controla la carga del archivo Excel, la aplicación de filtros,
y la exportación de resultados a un archivo JSON.
"""

import pandas as pd
from modules.loader import cargar_datos
from modules.filters import filtrar_facturas


def main():
    """
    Punto de entrada principal del programa.

    - Carga los datos de facturas desde un archivo Excel.
    - Permite al usuario ingresar filtros.
    - Aplica los filtros y muestra los resultados.
    - Exporta los resultados a un archivo JSON.
    """
    print("===  Buscador de Facturas ===\n")

    # Cargar el archivo Excel desde la carpeta 'data'
    df = cargar_datos("data/facturas.xlsx")

    if df.empty:
        print(" No se pudo cargar el archivo de facturas.")
        return

    # Solicitar filtros al usuario
    emisor = input("Ingrese el nombre del emisor (deje vacío si no aplica): ").strip()
    codigo = input("Ingrese el código de factura (deje vacío si no aplica): ").strip()
    monto_min = input("Ingrese el monto mínimo (deje vacío si no aplica): ").strip()
    fecha = input("Ingrese la fecha exacta (YYYY-MM-DD, deje vacío si no aplica): ").strip()

    # Convertir monto a número si aplica
    monto_min = float(monto_min) if monto_min else None

    # Aplicar filtro dinámico
    resultado = filtrar_facturas(
        df,
        emisor=emisor,
        codigo=codigo,
        monto_min=monto_min,
        fecha=fecha
    )

    print(f"\n Se encontraron {len(resultado)} facturas con los criterios seleccionados.\n")

    # Mostrar primeras 10 filas en consola
    print(resultado.head(10).to_string(index=False))

    # Exportar resultados a JSON
    json_resultado = resultado.to_json(orient="records", force_ascii=False, indent=4)
    with open("resultado.json", "w", encoding="utf-8") as f:
        f.write(json_resultado)

    print("\n Resultados exportados a 'resultado.json'")


if __name__ == "__main__":
    main()
