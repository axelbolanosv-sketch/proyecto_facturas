# gui.py (Versión Refactorizada y Modular - CORREGIDA)
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


# --- 4. LÓGICA DE REORDENAMIENTO (LA SOLUCIÓN) ---
# Primero, preparamos las variables de mapas de columnas.
# Si el DF está cargado, las calculamos ANTES de llamar a la sidebar.

todas_las_columnas_ui = None
col_map_es_to_en = None
todas_las_columnas_en = None
df_original = None # Lo definimos aquí

if st.session_state.df_original is not None:
    # El DF está cargado, así que calculamos los mapas AHORA.
    df_original = st.session_state.df_original.copy()
    todas_las_columnas_en = list(df_original.columns)
    col_map_es_to_en = {translate_column('es', col): col for col in todas_las_columnas_en}
    todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])

# --- 5. Renderizar Barra Lateral ---
# Ahora llamamos a la sidebar, pasando las variables
# (que serán 'None' en la primera carga, o listas/dicts poblados en recargas)
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_original is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_es_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos ---
# Si se cargan nuevos archivos Y el DF *aún* no está en sesión...
if uploaded_files and st.session_state.df_original is None:
    # (Esto solo se ejecutará en la "Run 2")
    load_and_process_files(uploaded_files, lang)
    st.rerun() # Forzar un rerun para que la "Run 3" tenga los datos

# --- 7. Lógica Principal (Solo si hay un DF cargado) ---
# Usamos el 'df_original' que definimos en el paso 4
if df_original is not None:
    try:
        # Los mapas de columnas ya están calculados (paso 4).
        # Solo necesitamos el mapa inverso.
        col_map_en_to_es = {v: k for k, v in col_map_es_to_en.items()}

        # --- 7b. Renderizar Filtros Activos ---
        render_active_filters(lang)

        # --- 7c. Aplicar Filtros ---
        resultado_df = aplicar_filtros_dinamicos(
            df_original,
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
            render_detailed_view(
                lang, 
                resultado_df, 
                df_original, 
                col_map_ui_to_en, 
                todas_las_columnas_en
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
        # En caso de error, limpiar el estado para evitar bucles
        clear_state_and_prepare_reload()
        st.rerun()

else:
    # --- 8. Estado Inicial (Si df_original es None) ---
    # Esto se ejecutará en la "Run 1" y "Run 2", pero no en la "Run 3"
    if not uploaded_files: # Solo muestra "cargue" si no estamos procesando
        st.info(get_text(lang, 'info_upload'))
    
    # Limpiar estado por si acaso (ya lo hace on_change, pero es seguro)
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None