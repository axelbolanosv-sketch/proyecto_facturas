# app.py (VERSIÓN CON LÓGICA DE DOBLE GUARDADO Y SIN BUCLE)
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
    clear_state_and_prepare_reload # Importamos esta función
)
from modules.gui_sidebar import render_sidebar
from modules.gui_views import (
    render_active_filters,
    render_kpi_dashboard,
    render_detailed_view,
    render_grouped_view
)

# --- 2. Configuración Inicial ---
# Inicializar el estado de la sesión ANTES de cualquier otra cosa
initialize_session_state()

# Obtener el idioma actual
lang = st.session_state.language

# Configurar la página
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)

# Cargar el CSS personalizado
load_custom_css()

# --- 3. Títulos Principales ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))


# --- 4. LÓGICA DE REORDENAMIENTO ---
# Preparamos las variables de mapas de columnas.
# Si el DF está cargado, las calculamos ANTES de llamar a la sidebar.

todas_las_columnas_ui = None
col_map_es_to_en = None
todas_las_columnas_en = None
df_staging_copy = None # Lo definimos aquí

# Usar 'df_staging' como la fuente de verdad
if st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    todas_las_columnas_en = list(df_staging_copy.columns)
    col_map_es_to_en = {translate_column('es', col): col for col in todas_las_columnas_en}
    todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])

# --- 5. Renderizar Barra Lateral ---
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_es_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos ---
# Si se cargan nuevos archivos Y el DF *aún* no está en sesión...
if uploaded_files and st.session_state.df_staging is None:
    # (Esto se ejecutará en el rerun causado por el 'on_change')
    load_and_process_files(uploaded_files, lang)
    
    # --- CORRECCIÓN: ELIMINADO 'st.rerun()' ---
    # Eliminar st.rerun() de aquí rompe el bucle infinito.
    # El rerun del 'on_change' es suficiente.
    # El script continuará y cargará los datos en esta misma ejecución.

# --- 7. Lógica Principal (Solo si hay un DF cargado) ---

# --- MODIFICACIÓN: Actualizar la copia de staging por si se cargó arriba ---
if df_staging_copy is None and st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    # Recalcular mapas si se cargó en este mismo run
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        col_map_es_to_en = {translate_column('es', col): col for col in todas_las_columnas_en}
        todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])


if df_staging_copy is not None:
    try:
        col_map_en_to_es = {v: k for k, v in col_map_es_to_en.items()}

        # --- 7b. Renderizar Filtros Activos ---
        render_active_filters(lang)

        # --- 7c. Aplicar Filtros ---
        # Los filtros se aplican al DataFrame de 'staging'
        resultado_df = aplicar_filtros_dinamicos(
            df_staging_copy,
            st.session_state.filtros_activos
        )
        
        # --- 7d. Renderizar KPIs ---
        render_kpi_dashboard(lang, resultado_df)
        
        st.markdown("---")

        # --- 7e. Selector de Vista (Detallada / Agrupada) ---
        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )
        
        # --- 7f. Renderizar la Vista seleccionada ---
        if view_type == get_text(lang, 'view_type_detailed'):
            col_map_ui_to_en = {ui: en for en, ui in col_map_en_to_es.items()}
            
            with st.spinner("Cargando editor..."):
                render_detailed_view(
                    lang=lang, 
                    resultado_df_filtrado=resultado_df, 
                    df_master_copy=df_staging_copy, 
                    col_map_ui_to_en=col_map_ui_to_en, 
                    todas_las_columnas_en=todas_las_columnas_en
                )
            
        else:
            render_grouped_view(
                lang, 
                resultado_df, 
                col_map_es_to_en, 
                todas_las_columnas_en
            )

    except Exception as e:
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        clear_state_and_prepare_reload()
        st.rerun()

else:
    # --- 8. Estado Inicial (Si df_staging es None) ---
    if not uploaded_files: 
        st.info(get_text(lang, 'info_upload'))
    
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None