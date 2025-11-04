# app.py (VERSIÓN CORREGIDA Y COMPLETA)
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
import streamlit_hotkeys as hotkeys # Importar hotkeys aquí si es necesario

# --- 2. Configuración Inicial ---
initialize_session_state()
lang = st.session_state.language
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)
load_custom_css()

# --- 3. Títulos Principales ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))


# --- 4. LÓGICA DE REORDENAMIENTO ---
todas_las_columnas_ui = None
col_map_ui_to_en = None # <-- RENOMBRADO
todas_las_columnas_en = None
df_staging_copy = None 

if st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    todas_las_columnas_en = list(df_staging_copy.columns)
    
    # --- INICIO DE LA CORRECCIÓN (BUGS 3 y 4) ---
    # El mapa AHORA se crea usando el idioma actual ('lang')
    # Esto asegura que el mapa de UI -> EN sea correcto para CUALQUIER idioma.
    col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
    # --- FIN DE LA CORRECCIÓN ---
    
    todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])

# --- 5. Renderizar Barra Lateral ---
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_ui_to_en, # Pasamos el mapa correcto (aunque el nombre del arg sea 'es')
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos ---
if uploaded_files and st.session_state.df_staging is None:
    load_and_process_files(uploaded_files, lang)

# --- 7. Lógica Principal (Solo si hay un DF cargado) ---
if df_staging_copy is None and st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        # Recalcular mapas si se cargó en este mismo run
        col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
        todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])


if df_staging_copy is not None:
    try:
        # Ya no necesitamos 'col_map_en_to_es'
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
            
            # Advertencia sobre hotkeys durante la carga
            st.warning(get_text(lang, 'hotkey_loading_warning'))
            
            # col_map_ui_to_en ya está calculado y es correcto
            with st.spinner("Cargando editor..."):
                render_detailed_view(
                    lang=lang, 
                    resultado_df_filtrado=resultado_df, 
                    df_master_copy=df_staging_copy, 
                    col_map_ui_to_en=col_map_ui_to_en, # <-- Pasamos el mapa corregido
                    todas_las_columnas_en=todas_las_columnas_en
                )
            
        else:
            render_grouped_view(
                lang, 
                resultado_df, 
                col_map_ui_to_en, # <-- Pasamos el mapa corregido
                todas_las_columnas_en
            )
    
    # --- ESTE ES EL BLOQUE QUE FALTABA ---
    except Exception as e:
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        clear_state_and_prepare_reload()
        st.rerun()
    # --- FIN DEL BLOQUE CORREGIDO ---

else:
    if not uploaded_files: 
        st.info(get_text(lang, 'info_upload'))
    
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None