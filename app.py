# app.py (VERSIÓN CORREGIDA Y COMPLETA - FIX DE HOTKEYS)
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
# 'import streamlit_hotkeys': Se importa aquí (ya estaba)
import streamlit_hotkeys as hotkeys 

# --- 2. Configuración Inicial ---
# 'initialize_session_state()': Inicializa todas las variables de estado.
initialize_session_state()
lang = st.session_state.language
# 'st.set_page_config': Configura la página para que ocupe toda la pantalla.
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)
# 'load_custom_css()': Carga el estilo CSS personalizado.
load_custom_css()

# --- [INICIO] CORRECCIÓN DE HOTKEYS ---
# Se activa el componente de hotkeys aquí, en el script principal (app.py).
# Esto asegura que se registre *una sola vez* y de forma estable,
# evitando el conflicto con la lógica st.rerun()/st.stop() de gui_views.py.
hotkeys.activate([
    hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"), 
    hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
    hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
    hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+Z)"),
],
    # 'key='main_hotkeys'': Se usa la misma clave que en gui_views.py
    key='main_hotkeys' 
)
# --- [FIN] CORRECCIÓN DE HOTKEYS ---

# --- 3. Títulos Principales ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))


# --- 4. LÓGICA DE REORDENAMIENTO ---
todas_las_columnas_ui = None
col_map_ui_to_en = None
todas_las_columnas_en = None
df_staging_copy = None 

# 'if st.session_state.df_staging is not None': Si hay datos cargados...
if st.session_state.df_staging is not None:
    # 'df_staging_copy': Se crea una copia para trabajar.
    df_staging_copy = st.session_state.df_staging.copy()
    # 'todas_las_columnas_en': Lista de columnas en inglés (orden original).
    todas_las_columnas_en = list(df_staging_copy.columns)
    
    # 'col_map_ui_to_en': Mapa de traducción (ej. {'Estado': 'Status'}).
    col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
    
    # 'todas_las_columnas_ui': Lista de columnas traducidas (ES) en el orden original.
    # Se eliminó sorted() para preservar el orden del archivo.
    todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]

# --- 5. Renderizar Barra Lateral ---
# 'uploaded_files': Renderiza la sidebar y captura si se cargaron nuevos archivos.
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_ui_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos ---
# 'if uploaded_files and ...': Si se cargó un archivo Y no hay datos en staging.
if uploaded_files and st.session_state.df_staging is None:
    # 'load_and_process_files': Procesa los archivos y los guarda en el estado.
    load_and_process_files(uploaded_files, lang)
    # 'st.rerun()': Se fuerza un rerun para actualizar la UI con los datos.
    st.rerun()

# --- 7. Lógica Principal (Solo si hay un DF cargado) ---
# 'if df_staging_copy is None and ...': Si la copia está vacía pero el estado SÍ tiene datos.
# (Esto ocurre en el rerun justo después de la carga).
if df_staging_copy is None and st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        # 'col_map_ui_to_en': Recalcula los mapas de traducción.
        col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
        # 'todas_las_columnas_ui': Recalcula la lista de UI (ordenada).
        todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]


# 'if df_staging_copy is not None': Si finalmente SÍ tenemos datos para mostrar.
if df_staging_copy is not None:
    try:
        # 'render_active_filters': Muestra los filtros activos.
        render_active_filters(lang)

        # 'resultado_df': Aplica los filtros al DataFrame.
        resultado_df = aplicar_filtros_dinamicos(
            df_staging_copy,
            st.session_state.filtros_activos
        )
        
        # 'render_kpi_dashboard': Muestra los KPIs.
        render_kpi_dashboard(lang, resultado_df)
        
        st.markdown("---")

        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        
        # 'view_type': Radio para elegir entre vista detallada o agrupada.
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )
        
        # 'if view_type == ...': Si se elige "Detallada".
        if view_type == get_text(lang, 'view_type_detailed'):
            
            # 'st.warning': Muestra la advertencia sobre hotkeys.
            st.warning(get_text(lang, 'hotkey_loading_warning'))
            
            # 'with st.spinner': Muestra "Cargando" mientras se renderiza el editor.
            with st.spinner("Cargando editor..."):
                # 'render_detailed_view': Renderiza el editor de datos.
                render_detailed_view(
                    lang=lang, 
                    resultado_df_filtrado=resultado_df, 
                    df_master_copy=df_staging_copy, 
                    col_map_ui_to_en=col_map_ui_to_en,
                    todas_las_columnas_en=todas_las_columnas_en
                )
            
        else:
            # 'render_grouped_view': Renderiza la vista agrupada.
            render_grouped_view(
                lang, 
                resultado_df, 
                col_map_ui_to_en,
                todas_las_columnas_en
            )
    
    except Exception as e:
        # 'st.error': Captura de error general.
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        clear_state_and_prepare_reload()
        st.rerun()

else:
    # 'if not uploaded_files': Si no hay datos Y no se han subido archivos.
    if not uploaded_files: 
        st.info(get_text(lang, 'info_upload'))
    
    # 'if st.session_state...': Limpieza de estado si se eliminan los archivos.
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None