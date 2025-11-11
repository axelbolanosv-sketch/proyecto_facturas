# modules/translator.py (VERSIÓN CON TEXTO OBSOLETO ELIMINADO)

# --- MAPA DE TRADUCCIÓN DE COLUMNAS ---
# (Esta sección no tiene cambios)
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
    "Batch Matching Date": "Fecha Cruce (Lote)",
    "Row Status": "Estado Fila"
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
        
        "group_view_blank_row_info": "ℹ️ **Nota:** Una fila sin nombre (en blanco) en esta tabla agrupa todas las facturas que no tenían un valor (estaban vacías) en la columna de agrupación seleccionada (ej. un 'Estado de Pago' en blanco).",
        
        "detailed_results_header": "Resultados Detallados",
        
        "visible_cols_header": "Columnas Visibles",
        "visible_cols_select": "Seleccione las columnas que desea ver:",
        "visible_cols_toggle_button": "Activar/Desactivar Todas",
        "visible_cols_warning": "Por favor, seleccione al menos una columna para mostrar.",
        
        # --- [INICIO] ELIMINACIÓN DE TEXTO OBSOLETO ---
        # 'toggle_priority_button': '🚦 Mostrar/Ocultar Marcas de Prioridad',
        # --- [FIN] ELIMINACIÓN DE TEXTO OBSOLETO ---
        
        "view_type_header": "Tipo de Vista",
        "view_type_detailed": "Detallada",
        "view_type_grouped": "Agrupada",
        
        'hotkey_loading_warning': '⚠️ **Atención:** Por favor, no use atajos de teclado (ej. Ctrl+S) mientras se esté cargando el editor de datos.',
        
        'autocomplete_help': 'Seleccione un valor existente o escriba para filtrar. Esto ayuda a mantener la consistencia.',
        'editor_info_help': 'Está en modo de edición. Haga doble clic en una celda para modificarla. Puede añadir o eliminar filas usando los botones (+) y (x) al final.',
        
        'reset_changes_button': 'Revertir a Estable',
        'reset_changes_help': 'Descarta los cambios del borrador y restaura el último punto de guardado estable. (Ctrl+Z)',
        'add_row_button': '➕ Añadir Fila',
        'add_row_help': 'Haga clic para añadir una fila (o use el atajo Ctrl+I).',
        'editor_info_help_add_row': '⚠️ Presione "Guardar Borrador" después de editar para actualizar el estado de las filas.',
        'save_changes_button': 'Guardar Borrador',
        'save_changes_help': 'Guarda los cambios en el borrador de trabajo. Los KPIs se actualizarán. (Ctrl+S)',
        'commit_changes_button': 'Guardar Estable',
        'commit_changes_help': 'Guarda el borrador actual como el nuevo punto de restauración estable. (Ctrl+Shift+S)',
        'restore_pristine_button': 'Restaurar Original',
        'restore_pristine_help': '¡PELIGRO! Borra TODOS los cambios (borrador y estable) y restaura los datos del archivo Excel original.',
        'commit_success_message': '¡Punto de restauración estable guardado con éxito!',
        
        'editor_actions_header': 'Acciones del Editor',
        
        'download_excel_manual_edits_button': 'Descargar Borrador Actual (Excel)',
        'download_excel_filtered_button': 'Descargar Vista Filtrada (Excel)',

        "status_incomplete": "Fila Incompleta",
        "status_complete": "Fila Completa",
        "search_text_placeholder_default": "Escriba su búsqueda...",
        "search_text_placeholder_status": "Ej: Fila Completa",
        "search_text_help_default": "Escriba su búsqueda y presione 'Enter' o el botón 'Añadir'",
        "search_text_help_status": "Escriba 'Fila Completa' o 'Fila Incompleta' y presione 'Enter'",

        "editor_info_help_save": "Haga clic en 'Guardar Borrador' para actualizar el estado.",
        "save_success_message": "¡Borrador guardado y estado actualizado con éxito!",
        
        "editor_manual_save_warning": "⚠️ **Importante:** Sus cambios **no se guardan automáticamente** (ni con 'Enter'). Puede editar múltiples celdas. Haga clic en **'Guardar Borrador' (o Ctrl+S)** para guardar. Si cambia de idioma, filtros, o vista *antes* de guardar, sus ediciones se perderán.",
        
        "date_format_help": "Formato de guardado: DD-MM-AAAA. Se intentará analizar otros formatos (ej. 20220309).",
        "date_format_es": "%d-%m-%Y", # Formato Día-Mes-Año
        "date_format_en": "%m-%d-%Y"  # Formato Mes-Día-Año
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
        
        "group_view_blank_row_info": "ℹ️ **Note:** A row with no name (blank) in this table groups all invoices that did not have a value (were empty) in the selected grouping column (e.g., a blank 'Pay Status').",

        "detailed_results_header": "Detailed Results",
        
        "visible_cols_header": "Visible Columns",
        "visible_cols_select": "Select columns to display:",
        "visible_cols_toggle_button": "Select/Deselect All",
        "visible_cols_warning": "Please select at least one column to display.",
        
        # --- [INICIO] ELIMINACIÓN DE TEXTO OBSOLETO ---
        # 'toggle_priority_button': '🚦 Show/Hide Priority Markers',
        # --- [FIN] ELIMINACIÓN DE TEXTO OBSOLETO ---

        "view_type_header": "View Type",
        "view_type_detailed": "Detailed",
        "view_type_grouped": "Grouped",
        
        'hotkey_loading_warning': '⚠️ **Attention:** Please do not use keyboard shortcuts (e.g., Ctrl+S) while the data editor is loading.',
        
        'autocomplete_help': 'Select an existing value or type to filter. This helps maintain consistency.',
        'editor_info_help': 'You are in edit mode. Double-click a cell to modify it. You can add or delete rows using the (+) and (x) buttons at the bottom.',
        
        'reset_changes_button': 'Revert to Stable',
        'reset_changes_help': 'Discards draft changes and restores the last stable save point. (Ctrl+Z)',
        'add_row_button': '➕ Add Row',
        'add_row_help': 'Click to add a new row (or use shortcut Ctrl+I).',
        'editor_info_help_add_row': '⚠️ Press "Save Draft" after editing to update row status.',
        'save_changes_button': 'Save Draft',
        'save_changes_help': 'Saves changes to the working draft. KPIs will update. (Ctrl+S)',
        'commit_changes_button': 'Save Stable',
        'commit_changes_help': 'Saves the current draft as the new stable restore point. (Ctrl+Shift+S)',
        'restore_pristine_button': 'Restore Original File',
        'restore_pristine_help': 'DANGER! Deletes ALL changes (draft and stable) and restores data from the original Excel file.',
        'commit_success_message': 'Stable restore point saved successfully!',
        
        'editor_actions_header': 'Editor Actions',
        
        'download_excel_manual_edits_button': 'Download Current Draft (Excel)',
        'download_excel_filtered_button': 'Descargar Vista Filtrada (Excel)',
        
        "status_incomplete": "Row Incomplete",
        "status_complete": "Row Complete",
        "search_text_placeholder_default": "Type your search...",
        "search_text_placeholder_status": "Ej: Row Complete",
        "search_text_help_default": "Type your search and press 'Enter' or the 'Add' button",
        "search_text_help_status": "Type 'Row Complete' or 'Row Incomplete' and press 'Enter'",

        "editor_info_help_save": "Click 'Save Draft' to update row status.",
        "save_success_message": "Draft saved and status updated successfully!",
        
        "editor_manual_save_warning": "⚠️ **Importante:** Your changes are **not saved automatically** (ni con 'Enter'). You can edit multiple cells. Click **'Guardar Borrador' (o Ctrl+S)** to save. If you change the language, filters, or view *before* saving, your edits will be lost.",
        
        "date_format_help": "Save format: MM-DD-AAAA. Other formats (e.g., 20220309) will be auto-parsed.",
        "date_format_es": "%d-%m-%Y", # Formato Día-Mes-Año
        "date_format_en": "%m-%d-%Y"  # Formato Mes-Día-Año
    }
}

def get_text(language, key):
    """
    Obtiene el texto traducido de la UI.
    Si no se encuentra la clave, devuelve la clave misma.
    """
    # 'LANGUAGES.get(language, {})': Obtiene el diccionario del idioma, o uno vacío si no existe.
    # '.get(key, key)': Obtiene el texto de la clave, o devuelve la clave misma si no se encuentra.
    return LANGUAGES.get(language, {}).get(key, key)

def translate_column(language, column_name):
    """
    Traduce un nombre de columna de inglés a español.
    Si el idioma es 'en' o no se encuentra traducción, devuelve el original.
    """
    # 'if language == 'es'': Solo traduce si el idioma es español.
    if language == 'es':
        # 'COLUMN_TRANSLATIONS.get(...)': Busca en el mapa; si no encuentra, devuelve el nombre original.
        return COLUMN_TRANSLATIONS.get(column_name, column_name)
    # 'return column_name': Devuelve el nombre original (inglés) si el idioma es 'en'.
    return column_name