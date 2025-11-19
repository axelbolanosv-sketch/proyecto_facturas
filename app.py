# app.py
# VERSIÓN FINAL: COORDINADOR PRINCIPAL

import streamlit as st
import pandas as pd
from modules.utils import initialize_session_state, load_custom_css, load_and_process_files, clear_state_and_prepare_reload
from modules.gui_sidebar import render_sidebar
from modules.gui_views import render_active_filters, render_kpi_dashboard, render_detailed_view, render_grouped_view
from modules.gui_rules_editor import render_rules_editor
from modules.filters import aplicar_filtros_dinamicos
from modules.translator import get_text, translate_column
import streamlit_hotkeys as hotkeys

# Inicialización
initialize_session_state()
lang = st.session_state.language
st.set_page_config(layout="wide", page_title="Gestor de Facturas")
load_custom_css()

# Hotkeys Globales
# AQUI ESTABA EL ERROR: Faltaba registrar el combo con Shift
hotkeys.activate([
    hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True),
    hotkeys.hk("commit_changes", "s", ctrl=True, shift=True, prevent_default=True), # <--- NUEVO
    hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True),
    hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True)
])

st.title(f"🔎 {get_text(lang, 'title')}")

# Modal Reglas
if st.session_state.get('show_rules_editor', False):
    render_rules_editor(
        st.session_state.columnas_visibles or [], 
        st.session_state.autocomplete_options
    )
    st.session_state.show_rules_editor = False

# Preparar datos para Sidebar
cols_ui = []
map_en = {}
cols_en = []
if st.session_state.df_staging is not None:
    cols_en = list(st.session_state.df_staging.columns)
    cols_ui = [translate_column(lang, c) for c in cols_en]
    map_en = {translate_column(lang, c): c for c in cols_en}

# Render Sidebar
uploaded = render_sidebar(lang, st.session_state.df_staging is not None, cols_ui, map_en, cols_en)

# Lógica Carga
if uploaded and st.session_state.df_staging is None:
    load_and_process_files(uploaded, lang)
    st.rerun()

# Lógica Principal
if st.session_state.df_staging is not None:
    try:
        # 1. Filtros
        render_active_filters(lang)
        df_res = aplicar_filtros_dinamicos(st.session_state.df_staging, st.session_state.filtros_activos)
        
        # 2. KPIs
        render_kpi_dashboard(lang, df_res)
        st.markdown("---")

        # 3. Selector Vista
        view = st.radio("Vista:", [get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')], horizontal=True)

        if view == get_text(lang, 'view_type_detailed'):
            render_detailed_view(lang, df_res, st.session_state.df_staging, map_en, cols_en)
        else:
            render_grouped_view(lang, df_res, map_en, cols_en)

    except Exception as e:
        st.error(f"Error inesperado: {e}")
        # Opcional: st.exception(e) para debug
else:
    st.info("Por favor cargue un archivo Excel para comenzar.")