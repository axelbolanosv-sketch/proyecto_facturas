# modules/gui_views.py (VERSIÓN CORREGIDA PARA PRESERVAR ESTADO AL CAMBIAR IDIOMA)
# Contiene la lógica para renderizar el contenido de la página principal.

import streamlit as st
import pandas as pd
import json 
import numpy as np
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel
import streamlit_hotkeys as hotkeys 

# --- 1. RENDER FILTROS ACTIVOS ---
def render_active_filters(lang):
    """
    Muestra los filtros activos en la parte superior de la página.
    Permite a los usuarios eliminar filtros individualmente o todos a la vez.
    
    Args:
        lang (str): El código de idioma actual (ej. 'es', 'en').
    """
    # Renderiza el título de la sección
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    
    # Si no hay filtros, muestra un mensaje informativo
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied'))
        return 

    # Variable para rastrear si un filtro debe ser eliminado
    filtros_a_eliminar = -1
    num_filtros = len(st.session_state.filtros_activos)
    
    # Organiza los filtros en hasta 5 columnas para ahorrar espacio
    num_columnas = max(1, min(num_filtros, 5)) 
    cols_filtros = st.columns(num_columnas)
    
    # Itera sobre cada filtro activo y crea un botón para eliminarlo
    for i, filtro in enumerate(st.session_state.filtros_activos):
        col_index = i % num_columnas
        with cols_filtros[col_index]:
            # Traduce el nombre de la columna para mostrarlo en la UI
            col_ui = translate_column(lang, filtro['columna']) 
            label_boton = f"{col_ui}: {filtro['valor']}  ✕"
            
            # Si se hace clic en un botón de filtro, marca su índice para eliminarlo
            if st.button(label_boton, key=f"quitar_{i}", help=f"Quitar filtro {i+1}", type="primary"):
                filtros_a_eliminar = i
    
    # Botón para limpiar *todos* los filtros activos
    if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
        st.session_state.filtros_activos = []
        st.rerun() # Re-ejecuta el script para refrescar la vista
    
    # Lógica para eliminar el filtro individual marcado
    if filtros_a_eliminar > -1:
        st.session_state.filtros_activos.pop(filtros_a_eliminar)
        st.rerun() # Re-ejecuta el script para refrescar la vista

# --- 2. RENDER KPIS ---
def render_kpi_dashboard(lang, resultado_df):
    """
    Muestra el dashboard de KPIs (Total Facturas, Monto Total, Monto Promedio).
    
    Args:
        lang (str): El código de idioma actual.
        resultado_df (pd.DataFrame): El DataFrame (ya filtrado) para calcular los KPIs.
    """
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    
    try:
        # Intenta convertir la columna 'Total' a numérico para los cálculos.
        # errors='coerce' convierte los no-numéricos en NaT, que dropna() elimina.
        totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
    except KeyError:
        # Fallback si la columna 'Total' no existe en el archivo cargado
        totales_numericos = pd.Series(dtype='float64')
        st.warning("No se encontró la columna 'Total' para los KPIs.")
    
    # Define 3 columnas para mostrar los KPIs
    col1, col2, col3 = st.columns(3)
    
    # KPI 1: Total de Facturas (conteo de filas)
    col1.metric(
        label=get_text(lang, 'kpi_total_invoices'), 
        value=len(resultado_df)
    )
    # KPI 2: Monto Total (suma de 'Total')
    col2.metric(
        label=get_text(lang, 'kpi_total_amount'), 
        value=f"${totales_numericos.sum():,.2f}",
        help=get_text(lang, 'kpi_total_amount_help')
    )
    # KPI 3: Monto Promedio (media de 'Total')
    col3.metric(
        label=get_text(lang, 'kpi_avg_amount'), 
        value=f"${totales_numericos.mean():,.2f}" if not totales_numericos.empty else "$0.00",
        help=get_text(lang, 'kpi_avg_amount_help')
    )

# --- 3. RENDER VISTA DETALLADA (EDITOR) ---
def render_detailed_view(lang, resultado_df_filtrado, df_master_copy, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista detallada principal con el editor de datos (st.data_editor).
    Esta función contiene la lógica más compleja para manejar el estado del editor,
    los cambios de idioma, y las acciones de guardar (Borrador, Estable, Revertir).
    
    Args:
        lang (str): Código de idioma actual.
        resultado_df_filtrado (pd.DataFrame): El DataFrame filtrado para *mostrar* inicialmente.
        df_master_copy (pd.DataFrame): Una copia del 'df_staging' (borrador) completo.
        col_map_ui_to_en (dict): Mapeo {'Nombre UI': 'Nombre EN'} para traducir columnas.
        todas_las_columnas_en (list): Lista de todos los nombres de columnas originales (EN).
    """
    
    # Activa los atajos de teclado (hotkeys) para las acciones del editor
    hotkeys.activate([
        hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"), 
        hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
        hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
        hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+Z)"),
    ],
        key='main_hotkeys'
    )

    # Validación: Si no hay columnas visibles seleccionadas, no mostrar el editor
    if not st.session_state.columnas_visibles:
            st.warning(get_text(lang, 'visible_cols_warning'))
            return

    # Determina las columnas finales a mostrar en el editor
    columnas_a_mostrar_en = st.session_state.columnas_visibles
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df_filtrado.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    # Crea el DataFrame para la vista detallada (solo filas filtradas, columnas seleccionadas)
    df_vista_detallada = resultado_df_filtrado[columnas_finales].copy()
    
    # Crea el DataFrame para *mostrar* en la UI, traduciendo los nombres de las columnas
    df_display = df_vista_detallada.copy()
    df_display.columns = [translate_column(lang, col) for col in df_display.columns]
    
    # --- Configuración de Columnas (Autocompletar) ---
    configuracion_columnas = {}
    
    # Lee las opciones pre-calculadas en 'gui_utils.py'
    if 'autocomplete_options' in st.session_state:
        for col_en, opciones in st.session_state.autocomplete_options.items():
            if not opciones: # Omitir si las opciones fallaron en generarse
                continue
                
            # Traduce el nombre de la columna EN al idioma UI actual
            col_ui = translate_column(lang, col_en)
            
            # Aplica la configuración de SelectboxColumn para el autocompletado
            configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                f"{col_ui} (Autocompletar)",
                help=get_text(lang, 'autocomplete_help'),
                options=opciones,
                required=False 
            )
    
    # --- Lógica de Hash y Estado (para preservar cambios al cambiar idioma) ---
    
    # 1. Crear hashes separados para DATOS (filtros/columnas) e IDIOMA
    filtros_json_string = json.dumps(st.session_state.filtros_activos, sort_keys=True)
    columnas_tuple = tuple(st.session_state.columnas_visibles)
    current_data_hash = hash((filtros_json_string, columnas_tuple))
    current_lang_hash = hash(st.session_state.language)

    # 2. Lógica de Estado
    if 'editor_state' not in st.session_state or \
       st.session_state.current_data_hash != current_data_hash:
        
        # --- CASO 1: Carga inicial o filtros/columnas cambiados ---
        # Recargar el editor desde los datos "guardados" (df_staging)
        # Se usa 'df_display' que es la vista filtrada y traducida
        st.session_state.editor_state = df_display.copy() 
        st.session_state.current_data_hash = current_data_hash
        st.session_state.current_lang_hash = current_lang_hash # Guardar hash de idioma

    elif st.session_state.current_lang_hash != current_lang_hash:
        
        # --- CASO 2: Solo cambió el idioma ---
        # ¡Preservar los cambios del editor!
        # 'st.session_state.editor_state' tiene los datos correctos (gracias a la corrección
        # de más abajo), pero los encabezados están en el idioma *antiguo*.
        
        df_actual = st.session_state.editor_state.copy()
        
        # 'df_display' tiene la *nueva* estructura (columnas traducidas al nuevo idioma)
        # Ambas DFs (actual y display) deben tener el mismo número de columnas
        
        if len(df_actual.columns) == len(df_display.columns):
            # Asumir que el orden es el mismo.
            # Crear un mapa de {nombre_antiguo: nombre_nuevo}
            column_rename_map = dict(zip(df_actual.columns, df_display.columns))
            # Renombrar las columnas del estado guardado
            df_actual = df_actual.rename(columns=column_rename_map)
            # Guardar el estado con las columnas renombradas
            st.session_state.editor_state = df_actual.copy()
        else:
            # Fallback: si algo sale mal (ej. cambiaron columnas Y idioma),
            # recargar para evitar un crash.
            st.session_state.editor_state = df_display.copy()
        
        # Actualizar el hash de idioma
        st.session_state.current_lang_hash = current_lang_hash

    # --- FIN DE LÓGICA DE ESTADO ---
    
    # --- LÓGICA DE AÑADIR FILA (Callback) ---
    def callback_add_row():
        """
        Callback para el botón 'Añadir Fila' o hotkey 'Ctrl+I'.
        Añade una fila vacía al 'editor_state' con un índice único.
        """
        df_editado = st.session_state.editor_state
        
        # Encuentra el índice máximo actual para crear uno nuevo
        max_index = df_master_copy.index.max()
        if not df_editado.empty:
            max_index = max(max_index, df_editado.index.max())
        new_index = max_index + 1

        # Define los valores por defecto (0 para numérico, "" para texto)
        default_values = {}
        for col in df_editado.columns:
            # Traduce la columna UI a EN para verificar su tipo original
            col_en = col_map_ui_to_en.get(col, col) 
            col_original_dtype = df_master_copy[col_en].dtype if col_en in df_master_copy.columns else 'object'
            # Asigna 0 si es numérico, "" si es cualquier otra cosa
            if pd.api.types.is_numeric_dtype(col_original_dtype):
                default_values[col] = 0
            else:
                default_values[col] = ""
        
        # Crea la nueva fila como un DataFrame
        new_row_df = pd.DataFrame(default_values, index=[new_index])
        
        # Concatena la nueva fila (arriba) y el estado editado (abajo)
        st.session_state.editor_state = pd.concat(
            [new_row_df, df_editado], 
            ignore_index=False 
        )
    
    # --- [INICIO] SOLUCIÓN AL PROBLEMA DE PÉRDIDA DE DATOS ---
    
    # 1. Advertencia al Usuario (Solución de UI)
    # Explica la limitación de Streamlit: las ediciones "en vuelo" (sin 'Enter') se pierden.
    st.warning("⚠️ **Importante:** Para guardar una edición en una celda, **presione 'Enter'** o haga clic fuera de ella *antes* de cambiar filtros, idioma o guardar.")
    
    # 2. Renderizar el Data Editor
    # 'st.session_state.editor_state' tiene los datos (posiblemente de un 'rerun' anterior)
    editor_return_value = st.data_editor(
        st.session_state.editor_state,
        column_config=configuracion_columnas, 
        num_rows="dynamic",
        width='stretch', 
        height=600,
        key="main_data_editor"
    )

    # 3. Corrección de Código (Solución de Lógica de Estado)
    # Esta es la línea clave. *Inmediatamente después* de que el editor se renderiza,
    # 'editor_return_value' contiene cualquier cambio que el usuario *acaba de enviar* (con Enter).
    # Actualizamos 'st.session_state.editor_state' con este nuevo valor.
    # Ahora, si el usuario presiona 'Enter' y LUEGO cambia el idioma, la lógica
    # del "CASO 2" (cambio de idioma) usará este estado actualizado y preservará el cambio.
    st.session_state.editor_state = editor_return_value.copy()
    
    # --- [FIN] SOLUCIÓN AL PROBLEMA DE PÉRDIDA DE DATOS ---


    # --- 3. DEFINICIÓN DE CALLBACKS DE ACCIÓN (Guardar/Revertir) ---
    # Estos se definen aquí para que tengan acceso a 'editor_return_value'

    def _callback_guardar_borrador():
        """
        (Ctrl+S) Guarda el estado del editor en 'df_staging' (Archivo 2: Borrador).
        Esta función se llama con on_click, por lo que 'editor_return_value'
        está garantizado que contiene los datos más recientes del editor.
        """
        # 1. Obtiene los datos actuales del editor
        df_edited_view_ui = editor_return_value.copy()
        
        # 2. Lógica para recalcular "Row Status" (Completa/Incompleta)
        col_status_en = "Row Status"
        col_status_ui = translate_column(lang, col_status_en)
        if col_status_ui in df_edited_view_ui.columns:
            # Revisa todas las columnas excepto el propio estado
            cols_to_check = [col for col in df_edited_view_ui.columns if col != col_status_ui]
            df_check = df_edited_view_ui[cols_to_check].fillna("").astype(str)
            # Una fila está incompleta si tiene "" o "0"
            blank_mask = (df_check == "") | (df_check == "0")
            incomplete_rows = blank_mask.any(axis=1)
            # Asigna el estado (traducido)
            df_edited_view_ui[col_status_ui] = np.where(
                incomplete_rows,
                get_text(lang, 'status_incomplete'),
                get_text(lang, 'status_complete')
            )
        
        # 3. Traduce las columnas de la vista (UI) de nuevo a Inglés (EN)
        df_to_merge_en = df_edited_view_ui.copy()
        df_to_merge_en.columns = [col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns]

        # 4. Carga el 'df_staging' (Borrador) actual
        df_master_staging = st.session_state.df_staging.copy()

        # 5. Separa filas nuevas (índice no existe en staging) de filas existentes
        existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master_staging.index)]
        new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master_staging.index)]
        
        # 6. Actualiza las filas existentes (sobrescribe)
        df_master_staging.update(existing_rows_en)
        # 7. Concatena las filas nuevas (añade)
        df_master_staging = pd.concat([new_rows_en, df_master_staging])
        
        # 8. Reordena por índice para mantener consistencia
        df_master_staging = df_master_staging.sort_index(ascending=True)
        
        # 9. Guarda el resultado en 'df_staging' (Archivo 2)
        st.session_state.df_staging = df_master_staging.copy()
        
        # 10. Actualiza el 'editor_state' para reflejar los cambios (ej. el Row Status)
        # Esto es crucial para que el editor no se revierta después de guardar.
        st.session_state.editor_state = df_edited_view_ui.copy()
        
        # 11. Muestra mensaje de éxito
        st.success(get_text(lang, 'save_success_message'))
        # No se necesita st.rerun() aquí, on_click lo maneja.

    def _callback_guardar_estable():
        """
        (Ctrl+Shift+S) Copia 'df_staging' (Borrador) a 'df_original' (Estable).
        Esto crea el punto de restauración "Estable".
        """
        st.session_state.df_original = st.session_state.df_staging.copy()
        st.success(get_text(lang, 'commit_success_message'))

    def _callback_revertir_estable():
        """
        (Ctrl+Z) Copia 'df_original' (Estable) a 'df_staging' (Borrador).
        Descarta los cambios del borrador y vuelve al último estable.
        """
        if st.session_state.df_original is not None:
            # Restaura el borrador (staging) desde el estable (original)
            st.session_state.df_staging = st.session_state.df_original.copy()
        
        # Limpia el estado del editor y los hashes.
        # Esto forzará al 'CASO 1' a ejecutarse en el próximo rerun,
        # recargando el editor desde el 'df_staging' recién revertido.
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.session_state.current_lang_hash = None
        # No se necesita st.rerun() aquí, on_click lo maneja.

    # --- 4. RENDERIZADO DE BOTONES DE CONTROL ---
    
    st.markdown(f"#### {get_text(lang, 'editor_actions_header')}")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Botón Añadir Fila
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True,
            help=get_text(lang, 'add_row_help') 
        )

    with col2:
        # Botón Guardar Borrador
        st.button(
            get_text(lang, 'save_changes_button'),
            on_click=_callback_guardar_borrador, # Usa el callback
            use_container_width=True,
            help=get_text(lang, 'save_changes_help'),
            type="primary" 
        )
    
    with col3:
        # Botón Guardar Estable
        st.button(
            get_text(lang, 'commit_changes_button'),
            on_click=_callback_guardar_estable, # Usa el callback
            use_container_width=True,
            help=get_text(lang, 'commit_changes_help'),
            key="commit_changes" 
        )
        
    with col4:
        # Botón Revertir a Estable
        st.button(
            get_text(lang, 'reset_changes_button'),
            on_click=_callback_revertir_estable, # Usa el callback
            use_container_width=True,
            help=get_text(lang, 'reset_changes_help'),
            key="reset_changes_button"
        )

    # Advertencia sobre cómo funciona 'Añadir Fila'
    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- 5. MANEJO DE EVENTOS (HOTKEYS) ---
    # La lógica de los botones ya está en 'on_click'.
    # Este bloque *solo* maneja los atajos de teclado.
    
    hk_add_row = hotkeys.pressed("add_row", key='main_hotkeys')
    hk_save_stable = hotkeys.pressed("save_stable", key='main_hotkeys')
    hk_save_draft = hotkeys.pressed("save_draft", key='main_hotkeys')
    hk_revert_stable = hotkeys.pressed("revert_stable", key='main_hotkeys')
    
    # El if/elif previene que se ejecuten múltiples hotkeys a la vez
    if hk_revert_stable: 
        _callback_revertir_estable() 
        st.rerun() # Hotkeys necesitan un rerun explícito
        
    elif hk_add_row: 
        callback_add_row()
        st.rerun() # Hotkeys necesitan un rerun explícito
        
    elif hk_save_stable: 
        _callback_guardar_estable() 
        # No se necesita rerun, el mensaje de éxito aparecerá
        
    elif hk_save_draft: 
        _callback_guardar_borrador() 
        st.rerun() # Hotkeys necesitan un rerun explícito
            
    # --- FIN DE LA LÓGICA DE MANEJO DE EVENTOS ---
    
    
    # --- Descargas y Restauración Original ---
    st.markdown("---")
    col_dl1, col_dl2, col_restore = st.columns([0.3, 0.3, 0.4])

    with col_dl1:
        # Descarga de datos EDITADOS (Borrador)
        # Usa 'editor_return_value' para descargar exactamente lo que el usuario ve
        df_para_descargar_editado = editor_return_value.copy()
        # Traduce las columnas de UI a EN antes de guardar
        df_para_descargar_editado.columns = [
            col_map_ui_to_en.get(col_ui, col_ui) 
            for col_ui in df_para_descargar_editado.columns
        ]
        # Convierte a Excel en memoria
        excel_data_editada = to_excel(df_para_descargar_editado)
        st.download_button(
            label=get_text(lang, 'download_excel_manual_edits_button'), 
            data=excel_data_editada,
            file_name="resultado_facturas_BORRADOR.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_editado",
            use_container_width=True
        )
    
    with col_dl2:
        # Descarga de datos FILTRADOS (Borrador)
        # Usa 'df_vista_detallada' (el DF *antes* de entrar al editor)
        excel_data_filtrada = to_excel(df_vista_detallada)
        st.download_button(
            label=get_text(lang, 'download_excel_filtered_button'), 
            data=excel_data_filtrada,
            file_name="resultados_Filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_filtrado",
            use_container_width=True
        )

    # Botón 4: Restaurar Archivo Original (Peligro)
    with col_restore:
        # Restaura TODO al estado original del archivo Excel cargado
        if st.button(
            get_text(lang, 'restore_pristine_button'),
            use_container_width=True,
            help=get_text(lang, 'restore_pristine_help'),
            key="restore_pristine" 
        ):
            if st.session_state.df_pristine is not None:
                # Restaura AMBOS, el estable (original) y el borrador (staging)
                st.session_state.df_original = st.session_state.df_pristine.copy()
                st.session_state.df_staging = st.session_state.df_pristine.copy()
            
            # Limpia el estado del editor para forzar una recarga completa
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.session_state.current_lang_hash = None
            st.rerun() # Forzar rerun


# --- 4. RENDER VISTA AGRUPADA ---
def render_grouped_view(lang, resultado_df, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista de análisis agrupado.
    
    Args:
        lang (str): Código de idioma actual.
        resultado_df (pd.DataFrame): El DataFrame (ya filtrado) para agrupar.
        col_map_ui_to_en (dict): Mapeo {'Nombre UI': 'Nombre EN'} para traducir columnas.
        todas_las_columnas_en (list): Lista de todos los nombres de columnas originales (EN).
    """
    
    # Define las columnas categóricas que tienen sentido para agrupar
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name", 
        "Pay Status", "Document Type", "Row Status"
    ]
    # Filtra y traduce las opciones al idioma de la UI
    opciones_agrupables_ui = [
        translate_column(lang, col) 
        for col in columnas_agrupables_en 
        if col in todas_las_columnas_en
    ]
    
    # Si no hay columnas agrupables, no mostrar nada
    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables (ej. 'Vendor Name', 'Status') en su archivo.")
        return

    # Selectbox para que el usuario elija por cuál columna agrupar
    col_para_agrupar_ui = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    
    # Muestra la nota informativa sobre la fila (en blanco)
    st.info(get_text(lang, 'group_view_blank_row_info'))
    
    if col_para_agrupar_ui:
        # Traduce la columna de UI a EN para el backend de pandas
        col_para_agrupar_en = col_map_ui_to_en.get(col_para_agrupar_ui, col_para_agrupar_ui)
        df_agrupado = resultado_df.copy() 
        
        # Asegura que las columnas 'Total' y 'Age' sean numéricas
        if 'Total' in df_agrupado.columns:
            df_agrupado['Total'] = pd.to_numeric(df_agrupado['Total'], errors='coerce')
        if 'Invoice Date Age' in df_agrupado.columns:
            df_agrupado['Invoice Date Age'] = pd.to_numeric(df_agrupado['Invoice Date Age'], errors='coerce')

        # Define las operaciones de agregación (suma, media, min, max, conteo)
        agg_operations = {'Total': ['sum', 'mean', 'min', 'max', 'count']}
        
        # Añade la antigüedad promedio si existe
        if 'Invoice Date Age' in df_agrupado.columns and pd.api.types.is_numeric_dtype(df_agrupado['Invoice Date Age']):
            agg_operations['Invoice Date Age'] = ['mean']

        try: 
            # Ejecuta el groupby y agg de pandas
            df_agrupado_calculado = df_agrupado.groupby(col_para_agrupar_en).agg(agg_operations)
            
            # Define los nombres de las columnas traducidos para la tabla final
            col_names_grouped = [
                get_text(lang, 'group_total_amount'), get_text(lang, 'group_avg_amount'),
                get_text(lang, 'group_min_amount'), get_text(lang, 'group_max_amount'),
                get_text(lang, 'group_invoice_count')
            ]
            if 'Invoice Date Age' in agg_operations:
                col_names_grouped.append(get_text(lang, 'group_avg_age'))
            
            df_agrupado_calculado.columns = col_names_grouped
            
            # Muestra el dataframe agrupado, ordenado por Monto Total
            st.dataframe(df_agrupado_calculado.sort_values(by=get_text(lang, 'group_total_amount'), ascending=False))
            
            # Botón de descarga para la vista agrupada
            excel_data = to_excel(df_agrupado_calculado)
            st.download_button(
                label=get_text(lang, 'download_excel_button'), 
                data=excel_data,
                file_name=f"agrupado_por_{col_para_agrupar_ui}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_agrupado"
            )
        except Exception as group_error:
            # Captura errores si, por ejemplo, la columna de agrupación falla
            st.error(f"Error al agrupar por '{col_para_agrupar_ui}': {group_error}")
    else:
        # Pide al usuario que seleccione una columna si no lo ha hecho
        st.info("Por favor, seleccione una columna para agrupar.")
