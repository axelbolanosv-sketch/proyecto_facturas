"""
main.py

Archivo principal del buscador de facturas.
Controla la carga del archivo, la aplicación de filtros,
y la exportación de resultados a un archivo JSON.
"""

import pandas as pd
from modules.loader import cargar_datos
from modules.filters import filtrar_facturas
import os # Importamos 'os' para verificar que la ruta existe


def main():
    """
    Punto de entrada principal del programa.

    - Carga los datos de facturas desde un archivo Excel.
    - Permite al usuario ingresar filtros.
    - Aplica los filtros y muestra los resultados.
    - Exporta los resultados a un archivo JSON.
    """
    print("===  Buscador de Facturas (Formato Actualizado) ===\n")

    # --- INICIO DE CAMBIO: Input dinámico de RUTA COMPLETA ---
    
    print("--- Carga de Archivo ---")
    print("Por favor, ingrese la RUTA COMPLETA de su archivo Excel.")
    print(r"(Ej: C:\Users\TuUsuario\Desktop\Facturas_Octubre.xlsx)")
    ruta_del_archivo = input("Ruta: ").strip()

    # 1. Quitar comillas si el usuario las pegó (común en Windows)
    if ruta_del_archivo.startswith('"') and ruta_del_archivo.endswith('"'):
        ruta_del_archivo = ruta_del_archivo[1:-1]

    # 2. Validar que la ruta existe ANTES de intentar cargarla
    if not os.path.exists(ruta_del_archivo):
        print(f"\n[Error] No se pudo encontrar ningún archivo en la ruta:")
        print(f"{ruta_del_archivo}")
        print("Verifique la ruta o si el archivo fue movido.")
        return

    # 3. Validar que sea un archivo Excel
    if not ruta_del_archivo.endswith((".xlsx", ".xls")):
        print(f"\n[Error] El archivo '{os.path.basename(ruta_del_archivo)}' no parece ser un archivo Excel (.xlsx o .xls).")
        return

    print(f"\nCargando archivo: {ruta_del_archivo}...")
    
    # 4. Cargar el archivo usando la ruta dinámica
    df = cargar_datos(ruta_del_archivo)
    
    # --- FIN DE CAMBIO ---

    if df.empty:
        # 'cargar_datos' ya imprime el error específico si falla la lectura
        print("No se pudo iniciar el programa.")
        return

    # --- Solicitar filtros al usuario (esto sigue igual) ---

    print("\n--- Ingrese los criterios de búsqueda (deje vacío si no aplica) ---")

    emisor = input("Ingrese el Vendor Name (antes Emisor): ").strip()
    codigo = input("Ingrese el Invoice # (antes Código): ").strip()
    monto_min = input("Ingrese el Total mínimo (antes Monto): ").strip()
    fecha = input("Ingrese la Invoice Date (YYYY-MM-DD): ").strip()
    status = input("Ingrese el Status (e.g., Completed, Pending): ").strip()
    assignee = input("Ingrese el Assignee (email o nombre): ").strip()
    po_number = input("Ingrese el PO Number: ").strip()
    pay_status = input("Ingrese el Pay Status (e.g., Paid, Overdue): ").strip()
    doc_type = input("Ingrese el Document Type (e.g., Invoice, Credit Memo): ").strip()

    # Convertir monto a número si aplica
    monto_min = float(monto_min) if monto_min else None

    # Aplicar filtro dinámico
    resultado = filtrar_facturas(   
        df,
        vendor_name=emisor,
        invoice_num=codigo,
        total_min=monto_min,
        invoice_date=fecha,
        status=status,
        assignee=assignee,
        po_number=po_number,
        pay_status=pay_status,
        doc_type=doc_type
    )

    print(f"\n Se encontraron {len(resultado)} facturas con los criterios seleccionados.\n")

    if not resultado.empty:
        
        # Define las columnas clave que quieres ver en la consola
        columnas_a_mostrar = [
            "Invoice #",
            "Vendor Name",
            "Invoice Date",
            "Total",
            "Status",
            "Pay Status",
            "Assignee",
            "PO"
        ]
        
        columnas_existentes = [col for col in columnas_a_mostrar if col in resultado.columns]
        preview_df = resultado[columnas_existentes]

        print("--- Vista Previa de Resultados (primeros 10) ---")
        print(preview_df.head(10).to_string(index=False))

        # Exportar resultados a JSON (CON TODAS LAS COLUMNAS)
        json_resultado = resultado.to_json(orient="records", force_ascii=False, indent=4)
        with open("resultado.json", "w", encoding="utf-8") as f:
            f.write(json_resultado)

        print("\n Resultados completos (con todas las columnas) exportados a 'resultado.json'")
    else:
        print(" No se encontraron resultados con esos filtros.")


if __name__ == "__main__":
    main()