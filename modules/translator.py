# modules/translator.py (VERSIÓN ACTUALIZADA CON TEXTOS DE REGLAS V2)

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

        "status_incomplete": "Fila Incompleta",
        "status_complete": "Fila Completa",
        "search_text_placeholder_default": "Escriba su búsqueda...",
        "search_text_placeholder_status": "Ej: Fila Completa",
        "search_text_help_default": "Escriba su búsqueda y presione 'Enter' o el botón 'Añadir'",
        "search_text_help_status": "Escriba 'Fila Completa' o 'Fila Incompleta' y presione 'Enter'",

        "editor_info_help_save": "Haga clic en 'Guardar Borrador' para actualizar el estado.",
        "save_success_message": "¡Borrador guardado y estado actualizado con éxito!",
        
        "editor_manual_save_warning": "⚠️ **Importante:** Sus cambios **no se guardan automáticamente** (ni con 'Enter'). Puede editar múltiples celdas. Haga clic en **'Guardar Borrador' (o Ctrl+S)** para guardar. Si cambia de idioma, filtros, o vista *antes* de guardar, sus ediciones se perderán.",
        
        "config_header": "Gestión de Configuración",
        "config_help_text": "Guarde su vista actual (filtros, columnas, orden) para usarla después, o cargue una guardada previamente.",
        "save_config_button": "💾 Guardar Configuración",
        "load_config_label": "📂 Cargar Configuración",
        "reset_config_button": "🔄 Restablecer Todo (Limpiar)",
        "reset_config_success": "¡Configuración restablecida a valores por defecto!",
        
        "manage_autocomplete_header": "📋 Gestión de Listas (Autocompletado)",
        "manage_autocomplete_info": "Añada o elimine opciones en los desplegables de la tabla (ej. nuevos proveedores).",
        "select_column_to_edit": "Seleccione la columna a editar:",
        "current_options": "Opciones Actuales ({n}):",
        "add_option_label": "Nuevo Elemento",
        "add_option_placeholder": "Escriba nueva opción...",
        "add_option_btn": "➕ Añadir",
        "remove_options_label": "Seleccionar para Eliminar:",
        "remove_option_btn": "🗑️ Eliminar Seleccionados",
        "option_added_success": "✅ ¡Opción '{val}' añadida a '{col}'!",
        "options_removed_success": "✅ ¡{n} opciones eliminadas de '{col}'!",
        
        "date_format_help": "Formato de guardado: DD-MM-AAAA. Se intentará analizar otros formatos (ej. 20220309).",
        "date_format_es": "%d-%m-%Y",
        "date_format_en": "%m-%d-%Y",
        
        # --- [MODIFICADO] Textos del Editor de Reglas y Auditoría ---
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
        # (Se omiten las traducciones al inglés por brevedad,
        #  pero se añadirían de forma análoga)
        "title": "Dynamic Invoice Search",
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