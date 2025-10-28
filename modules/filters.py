"""
filters.py

Módulo que contiene las funciones para filtrar facturas
según diferentes criterios.
"""

import pandas as pd


def filtrar_facturas(df: pd.DataFrame, **filtros) -> pd.DataFrame:
    """
    Aplica filtros dinámicos a las facturas según los parámetros proporcionados.

    Args:
        df (pd.DataFrame): DataFrame con las facturas.
        **filtros: Argumentos opcionales para filtrar los datos.
            - vendor_name (str): Nombre del proveedor (coincidencia parcial).
            - invoice_num (str): Número de factura (coincidencia parcial).
            - total_min (float): Monto mínimo de la factura.
            - invoice_date (str): Fecha exacta (formato YYYY-MM-DD).
            - status (str): Estado de la factura (coincidencia exacta, no sensible).
            - assignee (str): Asignado (coincidencia parcial).
            - po_number (str): Orden de compra (coincidencia parcial).
            - pay_status (str): Estado de pago (coincidencia exacta, no sensible).
            - doc_type (str): Tipo de documento (coincidencia exacta, no sensible).

    Returns:
        pd.DataFrame: Subconjunto del DataFrame original que cumple con los filtros.
    """

    resultado = df.copy()  # Copiamos para no alterar el original

    # --- Filtro por Vendor Name (antes Emisor) ---
    vendor_name = filtros.get("vendor_name")
    if vendor_name:
        resultado = resultado[resultado["Vendor Name"].str.contains(vendor_name, case=False, na=False)]

    # --- Filtro por Invoice # (antes CodigoFactura) ---
    invoice_num = filtros.get("invoice_num")
    if invoice_num:
        resultado = resultado[resultado["Invoice #"].str.contains(invoice_num, case=False, na=False)]

    # --- Filtro por Monto mínimo (ahora 'Total') ---
    total_min = filtros.get("total_min")
    if total_min is not None:
        # Convertimos 'Total' a numérico, 'coerce' pone NaN si falla
        resultado["Total_Num"] = pd.to_numeric(resultado["Total"], errors="coerce")
        # Filtramos los que no son NaN y son mayores o iguales
        resultado = resultado[resultado["Total_Num"].notna() & (resultado["Total_Num"] >= total_min)]
        resultado = resultado.drop(columns=["Total_Num"]) # Limpiamos columna auxiliar

    # --- Filtro por Fecha (ahora 'Invoice Date') ---
    invoice_date = filtros.get("invoice_date")
    if invoice_date:
        # Asegurarnos de que solo buscamos en fechas válidas (no cadenas vacías)
        resultado = resultado[resultado["Invoice Date"].str.startswith(invoice_date)]

    # --- NUEVOS FILTROS ---

    # --- Filtro por Status ---
    status = filtros.get("status")
    if status:
        # Usamos .lower() para comparación exacta no sensible a mayúsculas
        resultado = resultado[resultado["Status"].str.lower() == status.lower()]

    # --- Filtro por Assignee ---
    assignee = filtros.get("assignee")
    if assignee:
        resultado = resultado[resultado["Assignee"].str.contains(assignee, case=False, na=False)]

    # --- Filtro por PO Number ---
    po_number = filtros.get("po_number")
    if po_number:
        resultado = resultado[resultado["PO"].str.contains(po_number, case=False, na=False)]

    # --- Filtro por Pay Status ---
    pay_status = filtros.get("pay_status")
    if pay_status:
        resultado = resultado[resultado["Pay Status"].str.lower() == pay_status.lower()]

    # --- Filtro por Document Type ---
    doc_type = filtros.get("doc_type")
    if doc_type:
        resultado = resultado[resultado["Document Type"].str.lower() == doc_type.lower()]


    # --- Si no hay resultados, ofrecer una búsqueda más amplia (lógica anterior) ---
    if resultado.empty and vendor_name:
        print("\n No se encontraron coincidencias. Intentando búsqueda parcial por palabras...")
        sub_palabras = vendor_name.split(" ")
        temp_results = []
        for palabra in sub_palabras:
            if len(palabra) > 2: # Evitar palabras muy cortas
                temp = df[df["Vendor Name"].str.contains(palabra, case=False, na=False)]
                if not temp.empty:
                    print(f" Resultados parciales encontrados con '{palabra}'")
                    temp_results.append(temp)
        
        if temp_results:
            resultado = pd.concat(temp_results)
            # Eliminar duplicados si se aplicó búsqueda recursiva
            resultado = resultado.drop_duplicates(subset=["Invoice #"])

    return resultado