# modules/gui_views.py (VERSIÓN FINAL CON MERGE A MASTER)
# Contiene la lógica para renderizar el contenido de la página principal.

import streamlit as st
import pandas as pd
import json 
import numpy as np
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel

# --- 1. RENDER FILTROS ACTIVOS ---
# (Esta función no cambia)
def render_active_filters(lang):
    """Muestra los filtros activos y permite eliminarlos."""
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied'))
    else:
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
# (Esta función no cambia)
def render_kpi_dashboard(lang, resultado_df):
    """Muestra el dashboard de KPIs."""
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    try:
        totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
    except KeyError:
        totales_numericos = pd.Series(dtype='float64')
        st.warning("No se encontró la columna 'Total' para los KPIs.")
    col1, col2, col3 = st.columns(3)
    col1.metric(label=get_text(lang, 'kpi_total_invoices'), value=len(resultado_df))
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
def render_detailed_view(lang, resultado_df, df_original, col_map_ui_to_en, todas_las_columnas_en):
    """Muestra la vista detallada con el editor de datos y botones de descarga."""
    
    if not st.session_state.columnas_visibles:
            st.warning(get_text(lang, 'visible_cols_warning'))
            return

    columnas_a_mostrar_en = st.session_state.columnas_visibles
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    # resultado_df tiene los índices correctos del df_original
    df_vista_detallada = resultado_df[columnas_finales]
    df_display = df_vista_detallada.copy()
    df_display.columns = [translate_column(lang, col) for col in df_display.columns]
    
    # --- Configuración de Columnas (Autorrellenado) ---
    configuracion_columnas = {}
    columnas_autocompletar_en = [
        "Vendor Name", "Status", "Assignee", 
        "Operating Unit Name", "Pay Status", "Document Type"
    ]
    for col_en in columnas_autocompletar_en:
        if col_en in df_original.columns:
            try:
                opciones = sorted(df_original[col_en].astype(str).unique())
                col_ui = translate_column(lang, col_en)
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
    current_view_hash = hash((filtros_json_string, columnas_tuple))

    # --- Lógica de Estado ---
    # Si los filtros cambian O es la primera carga, reseteamos el 'editor_state'.
    if 'editor_state' not in st.session_state or \
        st.session_state.current_view_hash != current_view_hash:
        
        st.session_state.editor_state = df_display.copy() # Estado para mostrar
        st.session_state.current_view_hash = current_view_hash
    
    # --- INICIO ARREGLO DE 'AÑADIR FILA' ---
    def callback_add_row():
        # Añadir la fila al 'editor_state'
        df_editado = st.session_state.editor_state
        
        # 1. Encontrar el índice único más alto para la nueva fila
        #    Usamos el índice de df_original como la "base de datos"
        max_index = df_original.index.max()
        if not df_editado.empty:
            max_index = max(max_index, df_editado.index.max())
        new_index = max_index + 1

        default_values = {}
        for col in df_editado.columns:
            col_en = col_map_ui_to_en.get(col, col)
            col_original_dtype = df_original[col_en].dtype if col_en in df_original.columns else 'object'
            if pd.api.types.is_numeric_dtype(col_original_dtype):
                default_values[col] = 0
            else:
                default_values[col] = ""
        
        # 2. Crear la fila nueva CON el índice único
        new_row_df = pd.DataFrame(default_values, index=[new_index])
        
        # 3. Concatenar SIN ignorar el índice
        st.session_state.editor_state = pd.concat(
            [new_row_df, df_editado], 
            ignore_index=False # <-- ESTE ES EL ARREGLO
        )
    # --- FIN ARREGLO DE 'AÑADIR FILA' ---
    
    # Layout para los botones de control
    col1_btn, col2_btn, col3_btn, col4_info = st.columns([0.25, 0.25, 0.25, 0.25])
    
    with col1_btn:
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True
        )

    with col2_btn:
        if st.button(
            get_text(lang, 'reset_changes_button'), 
            use_container_width=True
        ):
            # Reseteamos el 'editor_state' al 'display' original
            st.session_state.editor_state = df_display.copy()
            st.session_state.current_view_hash = current_view_hash
            st.rerun()
    
    with col3_btn:
        save_button_pressed = st.button(
            get_text(lang, 'save_changes_button'),
            use_container_width=True,
            type="primary"
        )
    
    with col4_info:
        st.info(get_text(lang, 'editor_info_help_save'))
    
    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- El Widget Data Editor ---
    editor_return_value = st.data_editor(
        st.session_state.editor_state,
        column_config=configuracion_columnas, 
        num_rows="dynamic",
        width='stretch', 
        height=600
    )
    
    # --- INICIO: LÓGICA DE GUARDADO MANUAL Y FUSIÓN CON MASTER ---
    if save_button_pressed:
        
        # 1. Get the edited view (UI names, mixed indices)
        df_edited_view_ui = editor_return_value.copy()
        
        # 2. Recalculate status (on the UI-named DF)
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
        
        # 3. Create a copy with EN names for merging
        df_to_merge_en = df_edited_view_ui.copy()
        df_to_merge_en.columns = [col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns]

        # 4. Get the master dataframe
        df_master = st.session_state.df_original.copy()

        # 5. Separate existing rows from new rows
        # El índice de df_master es la "base de datos"
        existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master.index)]
        new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master.index)]
        
        # 6. Merge changes
        # 6a. Actualizar filas existentes (in-place)
        df_master.update(existing_rows_en)
        
        # 6b. Añadir filas nuevas
        df_master = pd.concat([new_rows_en, df_master])
        
        # 7. Save the *updated master* back to session state
        st.session_state.df_original = df_master.copy()
        
        # 8. Save the *updated view* back to the editor state
        st.session_state.editor_state = df_edited_view_ui.copy()
        
        st.success(get_text(lang, 'save_success_message'))
        st.rerun()

    # --- FIN: LÓGICA DE GUARDADO MANUAL ---
    
    st.markdown("---")
    
    # --- Descarga de datos EDITADOS ---
    # Lee desde 'editor_state', que ahora está sincronizado
    df_para_descargar_editado = st.session_state.editor_state.copy()
    df_para_descargar_editado.columns = [
        col_map_ui_to_en.get(col_ui, col_ui) 
        for col_ui in df_para_descargar_editado.columns
    ]
    excel_data_editada = to_excel(df_para_descargar_editado)
    st.download_button(
        label=get_text(lang, 'download_excel_manual_edits_button'), 
        data=excel_data_editada,
        file_name="resultado_facturas_MODIFICADO.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_excel_editado"
    )
    
    # --- Descarga de datos FILTRADOS ---
    excel_data_filtrada = to_excel(df_vista_detallada)
    st.download_button(
        label=get_text(lang, 'download_excel_filtered_button'), 
        data=excel_data_filtrada,
        file_name="resultados_PostFiltro.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_excel_filtrado"
    )

# --- 4. RENDER VISTA AGRUPADA ---
# (Esta función no cambia)
def render_grouped_view(lang, resultado_df, col_map_es_to_en, todas_las_columnas_en):
    """Muestra la vista de análisis agrupado."""
    
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name", 
        "Pay Status", "Document Type", "Row Status"
    ]
    opciones_agrupables_ui = [translate_column(lang, col) for col in columnas_agrupables_en if col in todas_las_columnas_en]
    
    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables (ej. 'Vendor Name', 'Status') en su archivo.")
        return

    col_para_agrupar_ui = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    
    if col_para_agrupar_ui:
        col_para_agrupar_en = col_map_es_to_en.get(col_para_agrupar_ui, col_para_agrupar_ui)
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