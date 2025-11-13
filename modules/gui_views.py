# modules/gui_views.py (VERSIÓN CON FIX DE BANDERITA PEGADA)
# Contiene la lógica para renderizar el contenido de la página principal
# e implementa la funcionalidad de edición masiva mediante modales.

import streamlit as st
import pandas as pd
import json 
import numpy as np
import warnings
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel
import streamlit_hotkeys as hotkeys 

# --- 0. COMPONENTE MODAL DE EDICIÓN MASIVA ---
@st.dialog("✏️ Edición Masiva / Bulk Edit")
def modal_bulk_edit(indices_seleccionados, col_map_ui_to_en, lang):
    """
    Renderiza un modal (pop-up) para editar múltiples filas a la vez.
    """
    st.markdown(f"Se editarán **{len(indices_seleccionados)}** facturas seleccionadas.")
    
    # 1. Selector de Columna a Editar
    cols_disponibles = [col for col in col_map_ui_to_en.keys() if "Seleccionar" not in col and "ID" not in col]
    col_ui_seleccionada = st.selectbox("¿Qué columna desea editar?", cols_disponibles)
    
    col_en_seleccionada = col_map_ui_to_en.get(col_ui_seleccionada, col_ui_seleccionada)
    
    # 2. Input del Nuevo Valor
    opciones_existentes = st.session_state.autocomplete_options.get(col_en_seleccionada, [])
    
    nuevo_valor = None
    
    if opciones_existentes and len(opciones_existentes) > 0:
        nuevo_valor = st.selectbox(
            f"Seleccione el nuevo valor para '{col_ui_seleccionada}':",
            options=opciones_existentes,
            index=None,
            placeholder="Seleccione un valor...",
            help="Puede seleccionar un valor existente de la lista."
        )
    else:
        nuevo_valor = st.text_input(
            f"Escriba el nuevo valor para '{col_ui_seleccionada}':"
        )

    st.warning("⚠️ Esta acción no se puede deshacer fácilmente (tendrá que usar 'Revertir a Estable').")

    # 3. Botón de Confirmación
    if st.button("Aplicar Cambios", type="primary"):
        if nuevo_valor is not None:
            try:
                # Obtener el DF staging (Borrador)
                df_master = st.session_state.df_staging
                
                # Actualizar los valores en el DataFrame Maestro
                for idx in indices_seleccionados:
                    if idx in df_master.index:
                        df_master.at[idx, col_en_seleccionada] = nuevo_valor
                
                # Actualizar el estado de sesión
                st.session_state.df_staging = df_master.copy()
                
                # Forzar recarga del editor
                st.session_state.editor_state = None
                st.session_state.current_data_hash = None
                
                st.success("¡Cambios aplicados con éxito!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error al aplicar cambios: {e}")
        else:
            st.error("Por favor ingrese o seleccione un valor.")

# --- 1. RENDER FILTROS ACTIVOS ---
def render_active_filters(lang):
    """
    Muestra los filtros activos en la parte superior de la página.
    """
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied'))
        return 

    filtros_a_eliminar = -1
    num_filtros = len(st.session_state.filtros_activos)
    
    num_columnas = max(1, min(num_filtros, 5)) 
    cols_filtros = st.columns(num_columnas)
    
    for i, filtro in enumerate(st.session_state.filtros_activos):
        col_index = i % num_columnas
        with cols_filtros[col_index]:
            col_ui = translate_column(lang, filtro['columna']) 
            label_boton = f"{col_ui}: {filtro['valor']}  ✕"
            
            if st.button(label_boton, key=f"quitar_{i}", help=f"Quitar filtro {i+1}", type="primary"):
                filtros_a_eliminar = i
    
    if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
        st.session_state.filtros_activos = []
        st.rerun() 
    
    if filtros_a_eliminar > -1:
        st.session_state.filtros_activos.pop(filtros_a_eliminar)
        st.rerun() 

# --- 2. RENDER KPIS ---
def render_kpi_dashboard(lang, resultado_df):
    """
    Muestra el dashboard de KPIs.
    """
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    
    try:
        totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
    except KeyError:
        totales_numericos = pd.Series(dtype='float64')
        st.warning("No se encontró la columna 'Total' para los KPIs.")
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        label=get_text(lang, 'kpi_total_invoices'), 
        value=len(resultado_df)
    )
    col2.metric(
        label=get_text(lang, 'kpi_total_amount'), 
        value=f"${totales_numericos.sum():,.2f}",
        help=get_text(lang, 'kpi_total_amount_help')
    )
    col3.metric(
        label=get_text(lang, 'kpi_avg_amount'), 
        value=f"${totales_numericos.mean():,.2f}" if not totales_numericos.empty else "$0.00",
        help=get_text(lang, 'kpi_avg_amount_help')
    )

# --- 3. RENDER VISTA DETALLADA (EDITOR) ---
def render_detailed_view(lang, resultado_df_filtrado, df_master_copy, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista detallada principal con el editor de datos.
    """
    
    # --- Lógica de Hotkeys/Columnas ---
    if not st.session_state.columnas_visibles:
            st.warning(get_text(lang, 'visible_cols_warning'))
            return

    columnas_a_mostrar_en = st.session_state.columnas_visibles
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df_filtrado.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    df_vista_detallada = resultado_df_filtrado[columnas_finales].copy()
    
    # --- INYECTAR COLUMNA 'SELECCIONAR' ---
    col_sel_name = "Seleccionar"
    if col_sel_name not in df_vista_detallada.columns:
        df_vista_detallada.insert(0, col_sel_name, False)
    
    df_display = df_vista_detallada.copy()
    
    # Traducir columnas
    df_display.columns = [
        translate_column(lang, col) if col != col_sel_name else col 
        for col in df_display.columns
    ]
    
    # --- LÓGICA DE INDICADOR EN EL ÍNDICE ---
    if 'Priority' in resultado_df_filtrado.columns:
        try:
            is_max_priority = (resultado_df_filtrado['Priority'] == "Maxima Prioridad") | (resultado_df_filtrado['Priority'] == "🚩 Maxima Prioridad")
            
            new_index = np.where(
                is_max_priority, 
                "🚩 " + df_display.index.astype(str), 
                df_display.index.astype(str)           
            )
            df_display.index = new_index
        except Exception as e:
            st.warning(f"No se pudo aplicar el indicador de prioridad al índice: {e}")
    
    # --- Lógica de Configuración de Columnas ---
    configuracion_columnas = {}
    date_format_help_text = get_text(lang, 'date_format_help')
    cached_options = st.session_state.get('autocomplete_options', {})

    configuracion_columnas[col_sel_name] = st.column_config.CheckboxColumn(
        "☑️",
        help="Seleccione para edición masiva",
        default=False,
        width="small"
    )

    for col_ui in df_display.columns:
        if col_ui == col_sel_name:
            continue

        col_en = col_map_ui_to_en.get(col_ui, col_ui) 
        
        if col_en in cached_options and cached_options[col_en]:
            configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                f"{col_ui} (Autocompletar)",
                help=get_text(lang, 'autocomplete_help'),
                options=cached_options[col_en], 
                required=False 
            )
        
        elif 'Date' in col_en and 'Age' not in col_en:
            configuracion_columnas[col_ui] = st.column_config.TextColumn(
                f"{col_ui}",
                help=date_format_help_text,
                required=False
            )
    
    # --- Lógica de Hashing ---
    filtros_json_string = json.dumps(st.session_state.filtros_activos, sort_keys=True)
    columnas_tuple = tuple(st.session_state.columnas_visibles)
    priority_sort_state = st.session_state.get('priority_sort_order', None)
    
    current_data_hash = hash((filtros_json_string, columnas_tuple, priority_sort_state))
    current_lang_hash = hash(st.session_state.language)
    
    if 'editor_state' not in st.session_state or \
       st.session_state.current_data_hash != current_data_hash or \
       st.session_state.current_lang_hash != current_lang_hash:
        
        st.session_state.editor_state = df_display.copy() 
        st.session_state.current_data_hash = current_data_hash
        st.session_state.current_lang_hash = current_lang_hash
        st.rerun()
        st.stop()
        
    # --- Definición de 'callback_add_row' ---
    def callback_add_row():
        """
        Callback para el botón 'Añadir Fila' o hotkey 'Ctrl+I'.
        """
        df_editado = st.session_state.editor_state
        
        max_index = df_master_copy.index.max()
        if not df_editado.empty:
            clean_indices = pd.to_numeric(
                pd.Series(df_editado.index).astype(str).str.replace("🚩 ", ""),
                errors='coerce'
            ).dropna()
            
            if not clean_indices.empty:
                 max_index = max(max_index, clean_indices.max())

        new_index = int(max_index + 1) 

        default_values = {}
        for col in df_editado.columns:
            if col == col_sel_name:
                default_values[col] = False
                continue
                
            col_en = col_map_ui_to_en.get(col, col) 
            col_original_dtype = df_master_copy[col_en].dtype if col_en in df_master_copy.columns else 'object'
            if pd.api.types.is_numeric_dtype(col_original_dtype):
                default_values[col] = 0
            else:
                default_values[col] = ""
        
        new_row_df = pd.DataFrame(default_values, index=[new_index])
        
        st.session_state.editor_state = pd.concat(
            [new_row_df, df_editado], 
            ignore_index=False 
        )
    
    # --- 3. DEFINICIÓN DE CALLBACKS DE ACCIÓN (Guardar/Revertir) ---

    def _callback_guardar_borrador():
        """
        (Ctrl+S) Guarda el estado del editor en 'df_staging'.
        """
        
        try:
            # 1. Obtener datos del editor
            df_edited_view_ui = editor_return_value.copy()
            
            # ELIMINAR COLUMNA SELECCIONAR antes de procesar
            if col_sel_name in df_edited_view_ui.columns:
                df_edited_view_ui = df_edited_view_ui.drop(columns=[col_sel_name])

            # --- 2. LIMPIEZA DE ÍNDICE Y TRADUCCIÓN ---
            df_edited_view_ui.index = pd.to_numeric(
                df_edited_view_ui.index.astype(str).str.replace("🚩 ", "")
            )
            df_to_merge_en = df_edited_view_ui.copy()
            df_to_merge_en.columns = [col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns]

            # --- 3. Formatear Fechas ---
            current_lang = st.session_state.language
            dayfirst = (current_lang == 'es')
            target_format = get_text(current_lang, 'date_format_es' if current_lang == 'es' else 'date_format_en')
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                for col_en in df_to_merge_en.columns:
                    if 'Date' in col_en and 'Age' not in col_en:
                        date_col = pd.to_datetime(df_to_merge_en[col_en], errors='coerce', dayfirst=dayfirst)
                        df_to_merge_en[col_en] = date_col.dt.strftime(target_format)
                        df_to_merge_en[col_en] = df_to_merge_en[col_en].astype(str).replace('NaT', '').replace('nan', '')

            # --- 4. Actualizar Master Staging ---
            df_master_staging = st.session_state.df_staging.copy()
            existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master_staging.index)]
            new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master_staging.index)]
            df_master_staging.update(existing_rows_en)
            df_master_staging = pd.concat([new_rows_en, df_master_staging])
            
            # --- 5.A. Re-calcular 'Row Status' ---
            col_status_en = "Row Status"
            if col_status_en in df_master_staging.columns:
                cols_to_check_master = [col for col in df_master_staging.columns if col != col_status_en]
                df_check_master = df_master_staging[cols_to_check_master].fillna("").astype(str)
                blank_mask_master = (df_check_master == "") | (df_check_master == "0")
                incomplete_rows_master = blank_mask_master.any(axis=1)
                df_master_staging[col_status_en] = np.where(
                    incomplete_rows_master,
                    get_text(lang, 'status_incomplete'),
                    get_text(lang, 'status_complete')
                )

            # --- 5.B. Re-calcular 'Priority' (FIX DE ORDEN) ---
            if 'Pay Group' in df_master_staging.columns and 'Priority' in df_master_staging.columns:
                
                manual_priorities = ["Minima", "Media", "Alta"] 
                mask_manual = df_master_staging['Priority'].astype(str).isin(manual_priorities)
                
                pay_group_searchable = df_master_staging['Pay Group'].astype(str).str.upper()
                high_priority_terms = ["DIST", "INTERCOMPANY", "PAYROLL", "RENTS", "SCF"]
                low_priority_terms = ["PAYGROUP", "PAY GROUP", "GNTD"]
                mask_high = pay_group_searchable.str.contains('|'.join(high_priority_terms), na=False)
                mask_low = pay_group_searchable.str.contains('|'.join(low_priority_terms), na=False)

                mask_excel_maxima = (df_master_staging['Priority'] == "Maxima Prioridad") | (df_master_staging['Priority'] == "🚩 Maxima Prioridad")

                # --- [CORRECCIÓN AQUÍ] ---
                # Se ha cambiado el orden: 'mask_low' ahora se evalúa ANTES que 'mask_excel_maxima'.
                # Esto asegura que si el Pay Group es de baja prioridad, se limpie la bandera
                # aunque la celda tuviera "🚩 Maxima Prioridad" anteriormente.
                conditions = [
                    mask_manual,        # 1. Prioridad Manual (Min/Med/Alta) - Gana siempre
                    mask_high,          # 2. Pay Group Alto - Fuerza Máxima
                    mask_low,           # 3. Pay Group Bajo - Fuerza Mínima (ANTES: Estaba al final)
                    mask_excel_maxima   # 4. Mantiene Máxima si ya existía y no es Bajo (ANTES: Estaba 3ro)
                ]
                
                choices = [
                    df_master_staging['Priority'],    
                    "🚩 Maxima Prioridad",             
                    "Minima",                         
                    "🚩 Maxima Prioridad"              
                ]
                
                df_master_staging['Priority'] = np.select(conditions, choices, default=df_master_staging['Priority'])
            
            # --- 6. Forzar tipos numéricos ---
            for col in df_master_staging.columns:
                if 'Total' in col or 'Amount' in col or 'Age' in col or 'ID' in col or 'Number' in col:
                     df_master_staging[col] = pd.to_numeric(df_master_staging[col], errors='coerce').fillna(0)
            
            # --- 7. Ordenar y Guardar ---
            df_master_staging = df_master_staging.sort_index(ascending=True)
            st.session_state.df_staging = df_master_staging.copy()
            
            # --- 8. Resetear editor ---
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None 
            st.session_state.current_lang_hash = None
            
            st.success(get_text(lang, 'save_success_message'))

        except Exception as e:
            st.error(f"Error al guardar el borrador: {e}")
            st.exception(e)

    def _callback_guardar_borrador_and_rerun():
        """Función wrapper."""
        _callback_guardar_borrador()
        st.rerun()

    def _callback_guardar_estable():
        """(Ctrl+Shift+S) Copia Borrador a Estable."""
        st.session_state.df_original = st.session_state.df_staging.copy()
        if st.session_state.columnas_visibles is not None:
            st.session_state.columnas_visibles_estable = st.session_state.columnas_visibles.copy()
        st.success(get_text(lang, 'commit_success_message'))


    def _callback_revertir_estable():
        """(Ctrl+Z) Copia Estable a Borrador."""
        if st.session_state.df_original is not None:
            st.session_state.df_staging = st.session_state.df_original.copy()
            
        if st.session_state.columnas_visibles_estable is not None:
            st.session_state.columnas_visibles = st.session_state.columnas_visibles_estable.copy()
            
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.session_state.current_lang_hash = None

    # --- 4. RENDERIZADO DE BOTONES DE CONTROL ---
    
    st.warning(get_text(lang, 'editor_manual_save_warning'))
    
    spinner_text = f"Cargando editor... {get_text(lang, 'hotkey_loading_warning')}"
    with st.spinner(spinner_text):
        editor_return_value = st.data_editor(
            st.session_state.editor_state,
            column_config=configuracion_columnas, 
            num_rows="dynamic",
            width='stretch', 
            height=600,
            key="main_data_editor",
            hide_index=False 
        )
    
    # --- DETECCIÓN DE FILAS SELECCIONADAS Y BOTÓN DE MODAL ---
    if col_sel_name in editor_return_value.columns:
        filas_seleccionadas = editor_return_value[editor_return_value[col_sel_name] == True]
        
        if not filas_seleccionadas.empty:
            indices_raw = filas_seleccionadas.index.astype(str).str.replace("🚩 ", "")
            indices_seleccionados = pd.to_numeric(indices_raw, errors='coerce').dropna().unique()
            
            if len(indices_seleccionados) > 0:
                st.markdown("---")
                st.info(f"✅ **{len(indices_seleccionados)} filas seleccionadas.**")
                
                if st.button(f"✏️ Editar {len(indices_seleccionados)} facturas (Masivo)"):
                    modal_bulk_edit(indices_seleccionados, col_map_ui_to_en, lang)
                st.markdown("---")

    # --- ACCIONES DEL EDITOR ---
    st.markdown(f"#### {get_text(lang, 'editor_actions_header')}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True,
            help=get_text(lang, 'add_row_help') 
        )
    with col2:
        st.button(
            get_text(lang, 'save_changes_button'),
            on_click=_callback_guardar_borrador_and_rerun, 
            use_container_width=True,
            help=get_text(lang, 'save_changes_help'),
            type="primary" 
        )
    with col3:
        st.button(
            get_text(lang, 'commit_changes_button'),
            on_click=_callback_guardar_estable, 
            use_container_width=True,
            help=get_text(lang, 'commit_changes_help'),
            key="commit_changes" 
        )
    with col4:
        st.button(
            get_text(lang, 'reset_changes_button'),
            on_click=_callback_revertir_estable, 
            use_container_width=True,
            help=get_text(lang, 'reset_changes_help'),
            key="reset_changes_button"
        )
    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- 5. MANEJO DE EVENTOS (HOTKEYS) ---
    hk_add_row = hotkeys.pressed("add_row", key='main_hotkeys')
    hk_save_stable = hotkeys.pressed("save_stable", key='main_hotkeys')
    hk_save_draft = hotkeys.pressed("save_draft", key='main_hotkeys')
    hk_revert_stable = hotkeys.pressed("revert_stable", key='main_hotkeys')
    
    if hk_revert_stable: 
        _callback_revertir_estable() 
        st.rerun() 
        
    elif hk_add_row: 
        callback_add_row()
        st.rerun() 
        
    elif hk_save_stable: 
        _callback_guardar_estable() 
    
    elif hk_save_draft: 
        _callback_guardar_borrador() 
        st.rerun() 
            
    # --- Descargas y Restauración Original ---
    st.markdown("---")
    col_dl1, col_dl2, col_restore = st.columns([0.3, 0.3, 0.4])
    with col_dl1:
        df_para_descargar_editado = editor_return_value.copy()
        
        if col_sel_name in df_para_descargar_editado.columns:
            df_para_descargar_editado = df_para_descargar_editado.drop(columns=[col_sel_name])

        df_para_descargar_editado.index = pd.to_numeric(
            df_para_descargar_editado.index.astype(str).str.replace("🚩 ", "")
        )
        df_para_descargar_editado.columns = [
            col_map_ui_to_en.get(col_ui, col_ui) 
            for col_ui in df_para_descargar_editado.columns
        ]
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
        excel_data_filtrada = to_excel(df_vista_detallada)
        st.download_button(
            label=get_text(lang, 'download_excel_filtered_button'), 
            data=excel_data_filtrada,
            file_name="resultados_Filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_filtrado",
            use_container_width=True
        )
    with col_restore:
        if st.button(
            get_text(lang, 'restore_pristine_button'),
            use_container_width=True,
            help=get_text(lang, 'restore_pristine_help'),
            key="restore_pristine" 
        ):
            if st.session_state.df_pristine is not None:
                st.session_state.df_original = st.session_state.df_pristine.copy()
                st.session_state.df_staging = st.session_state.df_pristine.copy()
            
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.session_state.current_lang_hash = None
            
            if st.session_state.df_pristine is not None:
                columnas_originales = list(st.session_state.df_pristine.columns)
                st.session_state.columnas_visibles = columnas_originales.copy()
                st.session_state.columnas_visibles_estable = columnas_originales.copy()
                
            st.rerun() 

# --- 4. RENDER VISTA AGRUPADA ---
def render_grouped_view(lang, resultado_df, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista de análisis agrupado.
    """
    
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name", 
        "Pay Status", "Document Type", "Row Status", "Priority"
    ]
    opciones_agrupables_ui = [
        translate_column(lang, col) 
        for col in columnas_agrupables_en 
        if col in todas_las_columnas_en
    ]
    
    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables (ej. 'Vendor Name', 'Status') en su archivo.")
        return

    col_para_agrupari = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    
    st.info(get_text(lang, 'group_view_blank_row_info'))
    
    if col_para_agrupari:
        col_para_agrupar_en = col_map_ui_to_en.get(col_para_agrupari, col_para_agrupari)
        df_agrupado = resultado_df.copy() 
        
        if 'Total' in df_agrupado.columns:
            df_agrupado['Total'] = pd.to_numeric(df_agrupado['Total'], errors='coerce')
        if 'Invoice Date Age' in df_agrupado.columns:
            df_agrupado['Invoice Date Age'] = pd.to_numeric(df_agrupado['Invoice Date Age'], errors='coerce')

        agg_operations = {'Total': ['sum', 'mean', 'min', 'max', 'count']}
        
        if 'Invoice Date Age' in df_agrupado.columns and pd.api.types.is_numeric_dtype(df_agrupado['Invoice Date Age']):
            agg_operations['Invoice Date Age'] = ['mean']

        try: 
            df_agrupado_calculado = df_agrupado.groupby(col_para_agrupar_en).agg(agg_operations)
            
            col_names_grouped = [
                get_text(lang, 'group_total_amount'), get_text(lang, 'group_avg_amount'),
                get_text(lang, 'group_min_amount'), get_text(lang, 'group_max_amount'),
                get_text(lang, 'group_invoice_count')
            ]
            if 'Invoice Date Age' in agg_operations:
                col_names_grouped.append(get_text(lang, 'group_avg_age'))
            
            df_agrupado_calculado.columns = col_names_grouped
            
            st.dataframe(df_agrupado_calculado.sort_values(by=get_text(lang, 'group_total_amount'), ascending=False))
            
            excel_data = to_excel(df_agrupado_calculado)
            st.download_button(
                label=get_text(lang, 'download_excel_button'), 
                data=excel_data,
                file_name=f"agrupado_por_{col_para_agrupari}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_agrupado"
            )
        except Exception as group_error:
            st.error(f"Error al agrupar por '{col_para_agrupari}': {group_error}")
    else:
        st.info("Por favor, seleccione una columna para agrupar.")