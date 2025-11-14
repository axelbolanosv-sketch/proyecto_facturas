# app.py (VERSIÓN CON HOOK PARA EDITOR DE REGLAS)
# Este archivo actúa como el "director de orquesta", coordinando
# los módulos de UI y utilidades.

import streamlit as st
import pandas as pd
from modules.filters import aplicar_filtros_dinamicos
from modules.translator import get_text, translate_column

# --- 1. Importar Módulos de GUI ---
from modules.gui_utils import (
    initialize_session_state,
    load_custom_css,
    load_and_process_files,
    clear_state_and_prepare_reload 
)
from modules.gui_sidebar import render_sidebar
from modules.gui_views import (
    render_active_filters,
    render_kpi_dashboard,
    render_detailed_view,
    render_grouped_view
)
# --- [NUEVO] Importar el editor de reglas ---
from modules.gui_rules_editor import render_rules_editor

import streamlit_hotkeys as hotkeys 

# --- 2. Configuración Inicial ---
# (Se llama a initialize_session_state() PRIMERO)
initialize_session_state()
lang = st.session_state.language
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)
load_custom_css()

# --- 3. Hotkeys (Sin Cambios) ---
hotkeys.activate([
    hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"), 
    hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
    hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
    hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+Z)"),
],
    key='main_hotkeys' 
)

# --- [NUEVO] Renderizar el Editor de Reglas (si está activo) ---
if st.session_state.get('show_rules_editor', False):
    render_rules_editor()
# --- [FIN] ---

# --- 4. Títulos y Lógica de Columnas (Sin Cambios) ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))

todas_las_columnas_ui = None
col_map_ui_to_en = None
todas_las_columnas_en = None
df_staging_copy = None 

if st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    todas_las_columnas_en = list(df_staging_copy.columns)
    col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
    todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]

# --- 5. Renderizar Barra Lateral ---
# (Sin cambios)
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_ui_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos (Excel) ---
# (Sin cambios)
if uploaded_files and st.session_state.df_staging is None:
    load_and_process_files(uploaded_files, lang)
    st.rerun()

# --- 7. Lógica Principal (Renderizado de Página) ---
# (Casi sin cambios, solo un fallback)
if df_staging_copy is None and st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
        todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]


if df_staging_copy is not None:
    try:
        render_active_filters(lang)

        resultado_df = aplicar_filtros_dinamicos(
            df_staging_copy,
            st.session_state.filtros_activos
        )
        
        render_kpi_dashboard(lang, resultado_df)
        
        st.markdown("---")

        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )
        
        if view_type == get_text(lang, 'view_type_detailed'):
            
            # --- LÓGICA DE ORDENAMIENTO (Sin Cambios) ---
            priority_map = {
                "🚩 Maxima Prioridad": 4, 
                "Maxima Prioridad": 4, 
                "Alta": 3,
                "Media": 2,
                "Minima": 1,
            }
            op_default = "Default (Sin Orden)" 
            op_desc = "🔼 Maxima a Minima"
            op_asc = "🔽 Minima a Maxima"
            radio_options = [op_default, op_desc, op_asc]
            
            current_sort_val = st.session_state.get('priority_sort_order', None)
            
            if current_sort_val == 'DESC':
                current_index = 1
            elif current_sort_val == 'ASC':
                current_index = 2
            else:
                current_index = 0
            
            selected_option = st.radio(
                "Ordenar por:", 
                options=radio_options,
                index=current_index,
                horizontal=True,
                key='priority_sort_radio'
            )
            
            st.markdown("---")

            new_sort_val = None
            if selected_option == op_desc:
                new_sort_val = 'DESC'
            elif selected_option == op_asc:
                new_sort_val = 'ASC'
            
            st.session_state.priority_sort_order = new_sort_val

            age_col_exists = 'Invoice Date Age' in resultado_df.columns
            
            if new_sort_val is not None and 'Priority' in resultado_df.columns:
                try:
                    ascending_flag_priority = (new_sort_val == 'ASC')
                    resultado_df['_sort_key'] = resultado_df['Priority'].map(priority_map).fillna(0)
                    
                    sort_by_cols = ['_sort_key']
                    sort_ascending_flags = [ascending_flag_priority]
                    
                    if age_col_exists:
                        sort_by_cols.append('Invoice Date Age')
                        sort_ascending_flags.append(False)
                    
                    resultado_df = resultado_df.sort_values(
                        by=sort_by_cols,
                        ascending=sort_ascending_flags,
                        kind='stable'
                    )
                    
                    resultado_df = resultado_df.drop(columns=['_sort_key'])

                except Exception as e:
                    st.warning(f"No se pudo aplicar el ordenamiento por prioridad y antigüedad: {e}")
            
            # --- Renderizado de Vista (Sin Cambios) ---
            render_detailed_view(
                lang=lang, 
                resultado_df_filtrado=resultado_df,
                df_master_copy=df_staging_copy, 
                col_map_ui_to_en=col_map_ui_to_en,
                todas_las_columnas_en=todas_las_columnas_en
            )
            
        else: # (Si la vista es Agrupada)
            render_grouped_view(
                lang, 
                resultado_df, 
                col_map_ui_to_en,
                todas_las_columnas_en
            )
    
    except Exception as e:
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        clear_state_and_prepare_reload()
        st.rerun()

else:
    # (Lógica 'else' sin cambios)
    if not uploaded_files: 
        st.info(get_text(lang, 'info_upload'))
    
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None