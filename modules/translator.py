# modules/translator.py (Actualizado con claves de descarga claras)

# --- MAPA DE TRADUCCIÓN DE COLUMNAS ---
COLUMN_TRANSLATIONS = {
    "Invoice #": "Nº Factura",
    "Header ID": "ID Encabezado",
    "Status": "Estado",
    "Assignee": "Asignado a",
    "Vendor Name": "Proveedor",
    "Vendor Number": "Nº Proveedor",
    "Invoice Date": "Fecha Factura",
    "Total": "Total",
    "Intake Date": "Fecha Recepción",
    "Operating Unit Name": "Unidad Operativa",
    "Assigned Date": "Fecha Asignación",
    "PO": "Orden de Compra",
    "Description": "Descripción",
    "Pay Group": "Grupo de Pago",
    "Due Date": "Fecha Vencimiento",
    "Pay Status": "Estado de Pago",
    "WEC Email Inbox": "Email Recepción",
    "Sender Email": "Email Remitente",
    "System Invoice #": "Nº Factura (Sistema)",
    "Priority": "Prioridad",
    "Invoice Date Age": "Antigüedad (Días)",
    "Document Type": "Tipo de Documento",
    "Terms Date": "Fecha de Términos",
    "GL Date": "Fecha Contable",
    "Updated Date": "Fecha Actualización",
    "Vendor Site Name": "Sitio Proveedor",
    "Vendor Site ID": "ID Sitio Proveedor",
    "Title": "Título",
    "Currency Code": "Moneda",
    "Operating Unit": "Unidad Operativa (ID)",
    "Acquired By": "Adquirido Por",
    "Requesters": "Solicitantes",
    "Buyers": "Compradores",
    "Intake Date Age": "Antigüedad Recepción",
    "Payment Method": "Método de Pago",
    "Payment Terms": "Términos de Pago",
    "Vendor Type": "Tipo de Proveedor",
    "Matching Status": "Estado de Cruce",
    "Batch Matching Date": "Fecha Cruce (Lote)"
    
}

# --- DICCIONARIO DE TEXTOS DE LA UI ---
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
        "download_json_button": "Descargar resultados como JSON",
        "download_excel_button": "Descargar resultados como Excel",
        "error_critical": "Error Crítico al procesar el archivo: {e}",
        "error_corrupt": "El archivo puede estar corrupto o tener un formato inesperado.",
        "info_upload": "Por favor, cargue un archivo .xlsx para comenzar.",

        "kpi_header": "Resumen de la Búsqueda",
        "kpi_total_invoices": "Total de Facturas",
        "kpi_total_amount": "Monto Total Filtrado",
        "kpi_avg_amount": "Monto Promedio",
        "kpi_total_amount_help": "Suma total de la columna 'Total' para todas las facturas filtradas. Mide la materialidad y el impacto financiero.",
        "kpi_avg_amount_help": "Monto promedio por factura (Total / Nº Facturas). Útil para detectar anomalías y el tamaño 'típico' de una transacción.",
        
        "group_by_header": "Análisis Agrupado",
        "group_by_select": "¿Agrupar resultados por?",
        "group_total_amount": "Monto Total",
        "group_avg_amount": "Monto Promedio",
        "group_invoice_count": "Cantidad de Facturas",
        "group_min_amount": "Monto Mínimo",
        "group_max_amount": "Monto Máximo",
        "group_avg_age": "Antigüedad Prom. (Días)",
        
        "detailed_results_header": "Resultados Detallados",
        
        "visible_cols_header": "Columnas Visibles",
        "visible_cols_select": "Seleccione las columnas que desea ver:",
        "visible_cols_toggle_button": "Activar/Desactivar Todas",
        "visible_cols_warning": "Por favor, seleccione al menos una columna para mostrar.",
        
        "view_type_header": "Tipo de Vista",
        "view_type_detailed": "Detallada",
        "view_type_grouped": "Agrupada",
        
        'autocomplete_help': 'Seleccione un valor existente o escriba para filtrar. Esto ayuda a mantener la consistencia.',
        'editor_info_help': 'Está en modo de edición. Haga doble clic en una celda para modificarla. Puede añadir o eliminar filas usando los botones (+) y (x) al final.',
        'reset_changes_button': 'Descartar cambios en la tabla',
        'add_row_button': '➕ Añadir  Fila al Principio',
        'editor_info_help_add_row': 'Haga clic en "Añadir Fila" para insertar una nueva fila en la parte superior. También puede editar o borrar filas existentes.',
        
        # ###############################################################
        # ############# INICIO DE LA SOLUCIÓN (Etiquetas Claras) ########
        # ###############################################################
        # (Claves antiguas eliminadas/renombradas)
        'download_excel_manual_edits_button': 'Descargar Datos MODIFICADOS (Excel)',
        'download_excel_filtered_button': 'Descargar Datos FILTRADOS (Excel)',
        # ###############################################################
        # ############# FIN DE LA SOLUCIÓN #############################
        # ###############################################################
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
        "download_json_button": "Download results as JSON",
        "download_excel_button": "Download results as Excel",
        "error_critical": "Critical Error while processing file: {e}",
        "error_corrupt": "The file might be corrupt or in an unexpected format.",
        "info_upload": "Please upload an .xlsx file to begin.",

        "kpi_header": "Search Summary",
        "kpi_total_invoices": "Total Invoices",
        "kpi_total_amount": "Total Filtered Amount",
        "kpi_avg_amount": "Average Amount",
        "kpi_total_amount_help": "Total sum of the 'Total' column for all filtered invoices. Measures materiality and financial impact.",
        "kpi_avg_amount_help": "Average amount per invoice (Total / # Invoices). Useful for detecting anomalies and the 'typical' transaction size.",

        "group_by_header": "Grouped Analysis",
        "group_by_select": "Group results by?",
        "group_total_amount": "Total Amount",
        "group_avg_amount": "Average Amount",
        "group_invoice_count": "Invoice Count",
        "group_min_amount": "Min Amount",
        "group_max_amount": "Max Amount",
        "group_avg_age": "Avg. Age (Days)",

        "detailed_results_header": "Detailed Results",
        
        "visible_cols_header": "Visible Columns",
        "visible_cols_select": "Select columns to display:",
        "visible_cols_toggle_button": "Select/Deselect All",
        "visible_cols_warning": "Please select at least one column to display.",
        
        "view_type_header": "View Type",
        "view_type_detailed": "Detailed",
        "view_type_grouped": "Grouped",
        
        'autocomplete_help': 'Select an existing value or type to filter. This helps maintain consistency.',
        'editor_info_help': 'You are in edit mode. Double-click a cell to modify it. You can add or delete rows using the (+) and (x) buttons at the bottom.',
        'reset_changes_button': 'Discard changes in table',
        'add_row_button': '➕ Add Row to Top',
        'editor_info_help_add_row': 'Click "Add Row" to insert a new row at the top. You can also edit or delete existing rows.',
        
        # ###############################################################
        # ############# INICIO DE LA SOLUCIÓN (Etiquetas Claras) ########
        # ###############################################################
        # (Claves antiguas eliminadas/renombradas)
        'download_excel_manual_edits_button': 'Download MODIFIED Data (Excel)',
        'download_excel_filtered_button': 'Download FILTERED Data (Excel)',
        # ###############################################################
        # ############# FIN DE LA SOLUCIÓN #############################
        # ###############################################################
    }
}

def get_text(language, key):
    """
    Obtiene el texto traducido de la UI.
    Si no se encuentra la clave, devuelve la clave misma (lo que causa el bug visual).
    """
    return LANGUAGES.get(language, {}).get(key, key)

def translate_column(language, column_name):
    """
    Traduce un nombre de columna de inglés a español.
    Si el idioma es 'en' o no se encuentra traducción, devuelve el original.
    """
    if language == 'es':
        return COLUMN_TRANSLATIONS.get(column_name, column_name)
    return column_name
