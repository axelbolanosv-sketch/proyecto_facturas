# modules/gui_views.py (VERSIÓN CON HOTKEY Ctrl+I PARA AÑADIR FILA)
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
    """Muestra los filtros activos y permite eliminarlos. (Sin cambios)"""
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
    """Muestra el dashboard de KPIs. (Sin cambios)"""
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
# --- CORRECCIÓN: Firma de función actualizada ---
def render_detailed_view(lang, resultado_df_filtrado, df_master_copy, col_map_ui_to_en, todas_las_columnas_en):
    """Muestra la vista detallada con el editor de datos y botones de descarga.

    Args:
        lang (str): El código de idioma actual (ej. 'es').
        resultado_df_filtrado (pd.DataFrame): El DF 'staging' ya filtrado.
        df_master_copy (pd.DataFrame): La copia completa de 'st.session_state.df_staging'.
        col_map_ui_to_en (dict): Mapeo de nombres UI -> nombres EN (CORREGIDO).
        todas_las_columnas_en (list): Lista de todos los nombres de columnas EN.
    """
    
    # --- INICIO DE MODIFICACIÓN 1: Cambiar hotkey a 'Ctrl+I' ---
    hotkeys.activate([
        # --- LÍNEA MODIFICADA ---
        hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"), 
        hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
        hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
        hotkeys.hk("revert_stable", "r", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+R)"),
    ],
        key='main_hotkeys'
    )
    # --- FIN DE MODIFICACIÓN 1 ---

    if not st.session_state.columnas_visibles:
            st.warning(get_text(lang, 'visible_cols_warning'))
            return

    columnas_a_mostrar_en = st.session_state.columnas_visibles
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df_filtrado.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    df_vista_detallada = resultado_df_filtrado[columnas_finales].copy()
    
    df_display = df_vista_detallada.copy()
    # Los encabezados se traducen usando el 'lang' actual
    df_display.columns = [translate_column(lang, col) for col in df_display.columns]
    
    # --- Configuración de Columnas (Autorrellenado) ---
    configuracion_columnas = {}
    
    columnas_autocompletar_en = [
        "Vendor Name", "Status", "Assignee", 
        "Operating Unit Name", "Pay Status", "Document Type",
        "Currency Code", "Vendor Type", "Payment Method", 
        "Priority", "Pay Group"
    ]
    
    for col_en in columnas_autocompletar_en:
        if col_en in df_master_copy.columns:
            try:
                opciones = []
                if col_en == "Priority":
                    opciones = ["", "Zero", "Low", "Medium", "High"]
                else:
                    opciones = sorted(df_master_copy[col_en].astype(str).unique())

                # --- CORRECCIÓN (BUG 4) ---
                # Traduce el nombre EN al nombre UI actual
                col_ui = translate_column(lang, col_en)
                
                # Aplica la configuración a la columna con el nombre UI
                # Esto ahora funciona en inglés Y español
                configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                    f"{col_ui} (Autocompletar)",
                    help=get_text(lang, 'autocomplete_help'),
                    options=opciones,
                    required=False 
                )
            except Exception as e:
                st.warning(f"No se pudo generar autorrellenado para '{col_en}': {e}")
    
    # --- Lógica de Hash Estable ---
    filtros_json_string = json.dumps(st.session_state.filtros_activos, sort_keys=True)
    columnas_tuple = tuple(st.session_state.columnas_visibles)
    
    # --- CORRECCIÓN (BUGS 1 y 3) ---
    # Añadimos el idioma al hash. Si el idioma cambia, el hash cambia.
    current_view_hash = hash((filtros_json_string, columnas_tuple, st.session_state.language))

    # --- Lógica de Estado ---
    if 'editor_state' not in st.session_state or \
        st.session_state.current_view_hash != current_view_hash:
        
        # Si el hash es diferente (ej. cambió el idioma),
        # recargamos el editor_state desde df_display (que tiene los encabezados traducidos)
        st.session_state.editor_state = df_display.copy() 
        st.session_state.current_view_hash = current_view_hash
    
    # --- LÓGICA DE AÑADIR FILA ---
    def callback_add_row():
        """
        Callback para el botón 'Añadir Fila' o hotkey 'Ctrl+I'.
        Añade una fila al 'editor_state' con un índice único.
        """
        df_editado = st.session_state.editor_state
        
        max_index = df_master_copy.index.max()
        if not df_editado.empty:
            max_index = max(max_index, df_editado.index.max())
        new_index = max_index + 1

        default_values = {}
        for col in df_editado.columns:
            # El mapa 'col_map_ui_to_en' ahora es correcto para cualquier idioma
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
    
    # --- El Widget Data Editor ---
    editor_return_value = st.data_editor(
        st.session_state.editor_state,
        column_config=configuracion_columnas, 
        num_rows="dynamic",
        width='stretch', 
        height=600,
        key="main_data_editor"
    )

    # --- 3. DEFINICIÓN DE CALLBACKS DE ACCIÓN ---

    def _callback_guardar_borrador():
        """
        (Ctrl+S) Guarda el estado del editor en 'df_staging' (Archivo 2).
        """
        df_edited_view_ui = editor_return_value.copy()
        
        col_status_en = "Row Status"
        col_status_ui = translate_column(lang, col_status_en)
        if col_status_ui in df_edited_view_ui.columns:
            cols_to_check = [col for col in df_edited_view_ui.columns if col != col_status_ui]
            df_check = df_edited_view_ui[cols_to_check].fillna("").astype(str)
            blank_mask = (df_check == "") | (df_check == "0")
            incomplete_rows = blank_mask.any(axis=1)
            df_edited_view_ui[col_status_ui] = np.where(
                incomplete_rows,
                get_text(lang, 'status_incomplete'),
                get_text(lang, 'status_complete')
            )
        
        df_to_merge_en = df_edited_view_ui.copy()
        # El mapa 'col_map_ui_to_en' ahora es correcto
        df_to_merge_en.columns = [col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns]

        df_master_staging = st.session_state.df_staging.copy()

        existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master_staging.index)]
        new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master_staging.index)]
        
        df_master_staging.update(existing_rows_en)
        df_master_staging = pd.concat([new_rows_en, df_master_staging])
        
        df_master_staging = df_master_staging.sort_index(ascending=True)
        
        st.session_state.df_staging = df_master_staging.copy()
        
        st.session_state.editor_state = df_edited_view_ui.copy()
        
        st.success(get_text(lang, 'save_success_message'))
        st.rerun()

    def _callback_guardar_estable():
        """
        (Ctrl+Shift+S) Copia 'df_staging' (Archivo 2) a 'df_original' (Archivo 1).
        """
        st.session_state.df_original = st.session_state.df_staging.copy()
        st.success(get_text(lang, 'commit_success_message'))

    def _callback_revertir_estable():
        """
        (Ctrl+R) Copia 'df_original' (Archivo 1) a 'df_staging' (Archivo 2).
        """
        if st.session_state.df_original is not None:
            st.session_state.df_staging = st.session_state.df_original.copy()
        
        st.session_state.editor_state = None
        st.session_state.current_view_hash = None
        st.rerun()

    # --- 4. RENDERIZADO DE BOTONES DE CONTROL ---
    st.markdown("#### Acciones del Editor")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True
        )

    with col2:
        save_button_pressed = st.button(
            get_text(lang, 'save_changes_button'),
            use_container_width=True,
            help=get_text(lang, 'save_changes_help'),
            type="primary" 
        )
    
    with col3:
        commit_button_pressed = st.button(
            get_text(lang, 'commit_changes_button'),
            use_container_width=True,
            help=get_text(lang, 'commit_changes_help'),
            key="commit_changes" 
        )
        
    with col4:
        revert_button_pressed = st.button(
            get_text(lang, 'reset_changes_button'),
            use_container_width=True,
            help=get_text(lang, 'reset_changes_help'),
            key="reset_changes_button"
        )

    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- 5. MANEJO DE EVENTOS (BOTONES Y HOTKEYS) ---
    
    if save_button_pressed:
        _callback_guardar_borrador()

    elif commit_button_pressed:
        _callback_guardar_estable()

    elif revert_button_pressed:
        _callback_revertir_estable()

    # --- INICIO DE MODIFICACIÓN 2: El 'elif' para 'add_row' no cambia ---
    # Sigue funcionando porque "add_row" es el nombre lógico de la hotkey.
    # Ahora se activará con 'Ctrl+I' en lugar de 'Ctrl+N'.
    elif hotkeys.pressed("add_row", key='main_hotkeys'):
        callback_add_row()
        st.rerun() # Forzar el refresco para mostrar la nueva fila
    # --- FIN DE MODIFICACIÓN 2 ---

    elif hotkeys.pressed("save_stable", key='main_hotkeys'):
        _callback_guardar_estable()
    elif hotkeys.pressed("save_draft", key='main_hotkeys'):
        _callback_guardar_borrador()
    elif hotkeys.pressed("revert_stable", key='main_hotkeys'):
        _callback_revertir_estable()
    
    
    # --- Descargas y Restauración Original ---
    st.markdown("---")
    col_dl1, col_dl2, col_restore = st.columns([0.3, 0.3, 0.4])

    with col_dl1:
        # Descarga de datos EDITADOS (Borrador)
        df_para_descargar_editado = editor_return_value.copy()
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
        # Descarga de datos FILTRADOS (Borrador)
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
            st.session_state.current_view_hash = None
            st.rerun()


# --- 4. RENDER VISTA AGRUPADA ---
# --- CORRECCIÓN: Firma de función actualizada ---
def render_grouped_view(lang, resultado_df, col_map_ui_to_en, todas_las_columnas_en):
    """Muestra la vista de análisis agrupado.

    Args:
        lang (str): El código de idioma actual (ej. 'es').
        resultado_df (pd.DataFrame): El DataFrame filtrado (del 'staging').
        col_map_ui_to_en (dict): Mapeo de nombres UI -> nombres EN (CORREGIDO).
        todas_las_columnas_en (list): Lista de todos los nombres de columnas EN.
    """
    
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name", 
        "Pay Status", "Document Type", "Row Status"
    ]
    opciones_agrupables_ui = [
        translate_column(lang, col) 
        for col in columnas_agrupables_en 
        if col in todas_las_columnas_en
    ]
    
    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables (ej. 'Vendor Name', 'Status') en su archivo.")
        return

    col_para_agrupar_ui = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    
    if col_para_agrupar_ui:
        # El mapa 'col_map_ui_to_en' ahora es correcto
        col_para_agrupar_en = col_map_ui_to_en.get(col_para_agrupar_ui, col_para_agrupar_ui)
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
                file_name=f"agrupado_por_{col_para_agrupar_ui}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_agrupado"
            )
        except Exception as group_error:
            st.error(f"Error al agrupar por '{col_para_agrupar_ui}': {group_error}")
    else:
        st.info("Por favor, seleccione una columna para agrupar.")