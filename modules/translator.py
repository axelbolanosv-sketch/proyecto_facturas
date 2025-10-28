# modules/translator.py (Actualizado)

# Diccionario de traducciones
LANGUAGES = {
    "es": {
        "title": "Buscador de Facturas Dinámico",
        "subtitle": "Cargue CUALQUIER archivo Excel (.xlsx) y añada múltiples filtros.",
        "lang_selector": "Idioma",
        "control_area": "Área de Control",
        "uploader_label": "Cargue su archivo de facturas",
        "add_filter_header": "Añadir Filtro",
        "column_select": "Seleccione una columna:",
        "search_text": "Texto a buscar (coincidencia parcial)",
        "add_filter_button": "Añadir Filtro",
        "warning_no_filter": "Debe seleccionar una columna y escribir un valor.",
        "active_filters_header": "Filtros Activos",
        "no_filters_applied": "No hay filtros aplicados. Se muestra la tabla completa.",
        "filter_display": "Columna **{columna}** contiene **'{valor}'**",
        "remove_button": "Quitar",
        "clear_all_button": "Limpiar todos los filtros",
        "results_header": "Resultados ({num_filas} filas encontradas)",
        "download_json_button": "Descargar resultados como JSON", # Clave renombrada
        "download_excel_button": "Descargar resultados como Excel", # <-- NUEVA CLAVE
        "error_critical": "Error Crítico al procesar el archivo: {e}",
        "error_corrupt": "El archivo puede estar corrupto o tener un formato inesperado.",
        "info_upload": "Por favor, cargue un archivo .xlsx para comenzar.",
        "error_missing_cols": "Error: No se pudieron encontrar las columnas requeridas.",
        "warning_missing_cols": "El script esperaba: **{columnas}**",
        "info_check_excel": "Asegúrese de que su Excel tenga columnas que se parezcan a 'Emisor', 'Código Factura', 'Monto', y 'Fecha'.",
        "info_headers_found": "Encabezados encontrados en el archivo (antes de normalizar):"
    },
    "en": {
        "title": "Dynamic Invoice Search",
        "subtitle": "Upload ANY Excel file (.xlsx) and add multiple filters.",
        "lang_selector": "Language",
        "control_area": "Control Panel",
        "uploader_label": "Upload your invoice file",
        "add_filter_header": "Add Filter",
        "column_select": "Select a column:",
        "search_text": "Text to search (partial match)",
        "add_filter_button": "Add Filter",
        "warning_no_filter": "You must select a column and enter a value.",
        "active_filters_header": "Active Filters",
        "no_filters_applied": "No filters applied. Showing full table.",
        "filter_display": "Column **{columna}** contains **'{valor}'**",
        "remove_button": "Remove",
        "clear_all_button": "Clear All Filters",
        "results_header": "Results ({num_filas} rows found)",
        "download_json_button": "Download results as JSON", # Clave renombrada
        "download_excel_button": "Download results as Excel", # <-- NUEVA CLAVE
        "error_critical": "Critical Error while processing file: {e}",
        "error_corrupt": "The file might be corrupt or in an unexpected format.",
        "info_upload": "Please upload an .xlsx file to begin.",
        "error_missing_cols": "Error: Could not find the required columns.",
        "warning_missing_cols": "The script expected: **{columnas}**",
        "info_check_excel": "Please ensure your Excel file has columns similar to 'Vendor Name', 'Invoice #', 'Total', and 'Invoice Date'.",
        "info_headers_found": "Headers found in file (before normalization):"
    }
}

def get_text(language, key):
    """
    Obtiene el texto traducido para una clave y un idioma dados.
    Si no se encuentra, devuelve la clave misma.
    """
    return LANGUAGES.get(language, {}).get(key, key)