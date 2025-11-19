# modules/translator.py
# VERSIÓN ACTUALIZADA: NUEVAS CLAVES PARA SIDEBAR Y BOTONES

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
    "Priority_Reason": "Prioridad (Razón)",
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
        "column_select_value": "Seleccione un valor:", 
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
        "download_excel_simple": "Descargar Excel",
        "download_button_short": "Descargar",

        "status_incomplete": "Fila Incompleta",
        "status_complete": "Fila Completa",
        "search_text_placeholder_default": "Escriba su búsqueda...",
        "search_text_placeholder_status": "Ej: Fila Completa",
        "search_text_help_default": "Escriba su búsqueda y presione 'Enter' o el botón 'Añadir'",
        "search_text_help_status": "Escriba 'Fila Completa' o 'Fila Incompleta' y presione 'Enter'",

        "editor_info_help_save": "Haga clic en 'Guardar Borrador' para actualizar el estado.",
        "save_success_message": "¡Borrador guardado y estado actualizado con éxito!",
        
        "editor_manual_save_warning": "⚠️ **Importante:** Sus cambios **no se guardan automáticamente** (ni con 'Enter'). Puede editar múltiples celdas. Haga clic en **'Guardar Borrador' (o Ctrl+S)** para guardar. Si cambia de idioma, filtros, o vista *antes* de guardar, sus ediciones se perderán.",
        
        # --- CLAVES SIDEBAR ---
        "user_active_label": "Usuario Activo",
        "user_placeholder": "Ej. Juan Perez",
        "user_warning": "Ingrese usuario para registrar acciones.",
        "audit_log_sidebar_btn": "📥 Descargar Log de Auditoría",
        
        "config_header": "Gestión de Configuración",
        "config_help_text": "Guarde su vista actual (filtros, columnas, orden) para usarla después, o cargue una guardada previamente.",
        "save_config_button": "💾 Guardar Configuración",
        "load_config_label": "📂 Cargar Configuración",
        "reset_config_button": "🔄 Resetear Todo",
        "reset_config_success": "¡Configuración restablecida a valores por defecto!",
        
        "manage_autocomplete_header": "📋 Gestión de Listas / Analizar",
        "manage_lists_expander": "📋 Gestión de Listas / Analizar",
        "manage_autocomplete_info": "Añada o elimine opciones en los desplegables de la tabla (ej. nuevos proveedores).",
        "select_column_to_edit": "Seleccione la columna a editar:",
        "current_options": "Opciones Actuales ({n}):",
        "add_option_label": "Nueva opción:",
        "add_option_placeholder": "Escriba nueva opción...",
        "add_option_btn": "➕ Añadir",
        "remove_options_label": "Borrar opciones:",
        "remove_option_btn": "🗑️ Borrar Seleccionados",
        "analyze_values_button": "🔄 Analizar Valores Únicos",
        "analyze_success": "¡Análisis completo! {n} opciones encontradas.",
        "analyze_empty": "La columna está vacía.",
        "analyze_error": "Error al analizar: {e}",
        "no_list_warning": "⚠️ Esta columna NO tiene lista de valores guardada.",
        "analyze_info": "Puede analizar la columna para extraer todos los valores únicos actuales y convertirlos en una lista desplegable.",
        "option_added_success": "✅ ¡Opción '{val}' añadida a '{col}'!",
        "options_removed_success": "✅ ¡{n} opciones eliminadas de '{col}'!",
        
        "date_format_help": "Formato de guardado: DD-MM-AAAA. Se intentará analizar otros formatos (ej. 20220309).",
        "date_format_es": "%d-%m-%Y",
        "date_format_en": "%m-%d-%Y",
        
        "rules_header": "Lógica de Negocio",
        "rules_edit_button": "⚙️ Editar Reglas de Prioridad",
        "rules_editor_title": "Editor de Reglas de Prioridad",
        "rules_editor_info": "Aquí puede cambiar la lógica de negocio. Las reglas se aplican en orden (columna 'Orden'). La edición manual en la tabla siempre tiene la máxima prioridad.",
        "rules_editor_header": "Reglas Actuales (Editar/Eliminar)",
        "rules_editor_order_help": "Número más bajo se ejecuta primero (ej. 10 es antes que 20).",
        "rules_editor_reason_help": "La descripción de la regla (ej. 'Alto volumen Nov 2025'). Se mostrará en la columna 'Prioridad (Razón)'.",
        
        "rules_add_new_header": "➕ Añadir Nueva Regla",
        "rules_add_new_subheader": "Crear una nueva regla de negocio",
        "rules_add_col_type": "1. Condición (Columna)",
        "rules_add_col_value_select": "2. Condición (Valor)",
        "rules_add_col_value_text": "2. Condición (Valor contiene...)",
        "rules_add_priority": "3. Acción (Asignar Prioridad)",
        "rules_add_reason": "4. Razón (para el log)",
        "rules_add_reason_placeholder": "Ej: Proveedor ACME es prioritario",
        "rules_add_new_btn": "Añadir Regla a la lista",
        "rules_add_error_all_fields": "Todos los campos son obligatorios para añadir una regla.",
        "rules_add_success": "✅ ¡Regla para '{val}' añadida! Revísela en la tabla y guarde.",
        
        "rules_editor_audit_header": "Auditoría (Trazabilidad)",
        "rules_editor_reason_input": "Razón del Cambio (Obligatorio para guardar)",
        "rules_editor_reason_placeholder": "Ej: Se añade al proveedor 'ACME' como Alta Prioridad por inicio de contrato.",
        "rules_editor_reason_error": "Debe proveer una razón para el cambio.",
        "rules_editor_save_btn": "Guardar Cambios y Recalcular",
        "rules_editor_cancel_btn": "Cancelar",
        "rules_editor_save_success": "¡Reglas actualizadas y log de auditoría guardado!",
        "audit_log_header": "Descargar Log de Auditoría",
        "audit_log_info": "Descargue el historial completo de todos los cambios a las reglas en formato Excel.",
        "audit_log_download_btn": "Descargar Log (Excel)"
    },
    "en": {
        "title": "Dynamic Invoice Search",
        "subtitle": "Upload ANY Excel file (.xlsx) and add multiple filters.",
        "lang_selector": "Language",
        "control_area": "Control Area",
        "uploader_label": "Upload your invoice file",
        "add_filter_header": "Add Filter",
        "column_select": "Select a column:",
        "column_select_value": "Select a value:", 
        "search_text": "Search text (partial match)",
        "add_filter_button": "Add Filter",
        "warning_no_filter": "You must select a column and enter a value.",
        "active_filters_header": "Active Filters",
        "no_filters_applied": "No filters applied. Showing full table.",
        "filter_display": "Column **{columna}** contains **'{valor}'**",
        "remove_button": "Remove",
        "clear_all_button": "Clear all filters",
        "results_header": "Results ({num_filas} rows found)",
        "download_json_button": "Download results as JSON",
        "download_excel_button": "Download results as Excel",
        "error_critical": "Critical Error processing file: {e}",
        "error_corrupt": "File may be corrupt or have an unexpected format.",
        "info_upload": "Please upload an .xlsx file to start.",

        "kpi_header": "Search Summary",
        "kpi_total_invoices": "Total Invoices",
        "kpi_total_amount": "Total Amount Filtered",
        "kpi_avg_amount": "Average Amount",
        "kpi_total_amount_help": "Total sum of 'Total' column for all filtered invoices. Measures materiality and financial impact.",
        "kpi_avg_amount_help": "Average amount per invoice (Total / No. Invoices). Useful for detecting anomalies and 'typical' transaction size.",
        
        "group_by_header": "Grouped Analysis",
        "group_by_select": "Group results by?",
        "group_total_amount": "Total Amount",
        "group_avg_amount": "Average Amount",
        "group_invoice_count": "Invoice Count",
        "group_min_amount": "Min Amount",
        "group_max_amount": "Max Amount",
        "group_avg_age": "Avg. Age (Days)",
        
        "group_view_blank_row_info": "ℹ️ **Note:** A blank row in this table groups all invoices that had no value (were empty) in the selected grouping column (e.g., a blank 'Pay Status').",
        
        "detailed_results_header": "Detailed Results",
        
        "visible_cols_header": "Visible Columns",
        "visible_cols_select": "Select columns to view:",
        "visible_cols_toggle_button": "Toggle All",
        "visible_cols_warning": "Please select at least one column to display.",
        
        "view_type_header": "View Type",
        "view_type_detailed": "Detailed",
        "view_type_grouped": "Grouped",
        
        'hotkey_loading_warning': '⚠️ **Attention:** Please do not use keyboard shortcuts (e.g. Ctrl+S) while the data editor is loading.',
        
        'autocomplete_help': 'Select an existing value or type to filter. This helps maintain consistency.',
        'editor_info_help': 'You are in edit mode. Double-click a cell to modify it. You can add or remove rows using the (+) and (x) buttons at the end.',
        
        'reset_changes_button': 'Revert to Stable',
        'reset_changes_help': 'Discirds draft changes and restores the last stable save point. (Ctrl+Z)',
        'add_row_button': '➕ Add Row',
        'add_row_help': 'Click to add a row (or use Ctrl+I).',
        'editor_info_help_add_row': '⚠️ Press "Save Draft" after editing to update row status.',
        'save_changes_button': 'Save Draft',
        'save_changes_help': 'Saves changes to the working draft. KPIs will update. (Ctrl+S)',
        'commit_changes_button': 'Save Stable',
        'commit_changes_help': 'Saves the current draft as the new stable restore point. (Ctrl+Shift+S)',
        'restore_pristine_button': 'Restore Original',
        'restore_pristine_help': 'DANGER! Deletes ALL changes (draft and stable) and restores data from the original Excel file.',
        'commit_success_message': 'Stable restore point saved successfully!',
        
        'editor_actions_header': 'Editor Actions',
        
        'download_excel_manual_edits_button': 'Download Current Draft (Excel)',
        'download_excel_filtered_button': 'Download Filtered View (Excel)',
        "download_excel_simple": "Download Excel",
        "download_button_short": "Download",

        "status_incomplete": "Incomplete Row",
        "status_complete": "Complete Row",
        "search_text_placeholder_default": "Type your search...",
        "search_text_placeholder_status": "E.g.: Complete Row",
        "search_text_help_default": "Type your search and press 'Enter' or the 'Add' button",
        "search_text_help_status": "Type 'Complete Row' or 'Incomplete Row' and press 'Enter'",

        "editor_info_help_save": "Click 'Save Draft' to update status.",
        "save_success_message": "Draft saved and status updated successfully!",
        
        "editor_manual_save_warning": "⚠️ **Important:** Your changes are **not saved automatically** (not even with 'Enter'). You can edit multiple cells. Click **'Save Draft' (or Ctrl+S)** to save. If you change language, filters, or view *before* saving, your edits will be lost.",
        
        # --- CLAVES SIDEBAR EN ---
        "user_active_label": "Active User",
        "user_placeholder": "E.g. John Doe",
        "user_warning": "Enter user to log actions.",
        "audit_log_sidebar_btn": "📥 Download Audit Log",
        
        "config_header": "Configuration Management",
        "config_help_text": "Save your current view (filters, columns, order) to use later, or load a previously saved one.",
        "save_config_button": "💾 Save Configuration",
        "load_config_label": "📂 Load Configuration",
        "reset_config_button": "🔄 Reset All",
        "reset_config_success": "Configuration reset to default values!",
        
        "manage_autocomplete_header": "📋 Manage Lists / Analyze",
        "manage_lists_expander": "📋 Manage Lists / Analyze",
        "manage_autocomplete_info": "Add or remove options in table dropdowns (e.g., new vendors).",
        "select_column_to_edit": "Select column to edit:",
        "current_options": "Current Options ({n}):",
        "add_option_label": "New Option:",
        "add_option_placeholder": "Type new option...",
        "add_option_btn": "➕ Add",
        "remove_options_label": "Remove options:",
        "remove_option_btn": "🗑️ Remove Selected",
        "analyze_values_button": "🔄 Analyze Unique Values",
        "analyze_success": "Analysis complete! {n} options found.",
        "analyze_empty": "Column is empty.",
        "analyze_error": "Analysis error: {e}",
        "no_list_warning": "⚠️ This column has NO saved value list.",
        "analyze_info": "You can analyze the column to extract all current unique values and turn them into a dropdown list.",
        "option_added_success": "✅ Option '{val}' added to '{col}'!",
        "options_removed_success": "✅ {n} options removed from '{col}'!",
        
        "date_format_help": "Save format: DD-MM-YYYY. Will attempt to parse other formats (e.g. 20220309).",
        "date_format_es": "%d-%m-%Y",
        "date_format_en": "%m-%d-%Y",

        "rules_header": "Business Logic",
        "rules_edit_button": "⚙️ Edit Priority Rules",
        "rules_editor_title": "Priority Rules Editor",
        "rules_editor_info": "Here you can change business logic. Rules are applied in order (column 'Order'). Manual edits in the grid always have the highest priority.",
        "rules_editor_header": "Current Rules (Edit/Delete)",
        "rules_editor_order_help": "Lowest number runs first (e.g., 10 runs before 20).",
        "rules_editor_reason_help": "The rule description (e.g., 'High volume Nov 2025'). This will be shown in the 'Priority (Reason)' column.",
        
        "rules_add_new_header": "➕ Add New Rule",
        "rules_add_new_subheader": "Create a new business rule",
        "rules_add_col_type": "1. Condition (Column)",
        "rules_add_col_value_select": "2. Condition (Value)",
        "rules_add_col_value_text": "2. Condition (Value contains...)",
        "rules_add_priority": "3. Action (Assign Priority)",
        "rules_add_reason": "4. Reason (for log)",
        "rules_add_reason_placeholder": "e.g., ACME vendor is high priority",
        "rules_add_new_btn": "Add Rule to list",
        "rules_add_error_all_fields": "All fields are required to add a rule.",
        "rules_add_success": "✅ Rule for '{val}' added! Review it in the table and save.",
        
        "rules_editor_audit_header": "Audit (Traceability)",
        "rules_editor_reason_input": "Reason for Change (Required to save)",
        "rules_editor_reason_placeholder": "e.g., Added 'ACME' vendor as High Priority due to new contract.",
        "rules_editor_reason_error": "You must provide a reason for the change.",
        "rules_editor_save_btn": "Save Changes & Recalculate",
        "rules_editor_cancel_btn": "Cancel",
        "rules_editor_save_success": "Rules updated and audit log saved!",
        "audit_log_header": "Download Audit Log",
        "audit_log_info": "Download the complete history of all rule changes in Excel format.",
        "audit_log_download_btn": "Download Log (Excel)"
    }
}

def get_text(language, key):
    """
    Obtiene el texto traducido de la UI.
    Si no se encuentra la clave, devuelve la clave misma.
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