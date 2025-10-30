# modules/gui_sidebar.py (VERSIÓN LIMPIA)
# Contiene toda la lógica para renderizar la barra lateral.

import streamlit as st
from modules.translator import get_text, translate_column
from modules.gui_utils import clear_state_and_prepare_reload

def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    """
    Renderiza todo el contenido de la barra lateral.
    Los controles de filtro/columna solo aparecen si df_loaded es True.
    """
    
    # --- 1. Selector de Idioma ---
    lang_options = {"Español": "es", "English": "en"}

    def callback_update_language():
        selected_label = st.session_state.language_selector_key
        lang_code = lang_options[selected_label]
        st.session_state.language = lang_code
    
    lang_code_to_label = {v: k for k, v in lang_options.items()}
    current_label = lang_code_to_label.get(st.session_state.language, "Español")
    current_lang_index = list(lang_options.keys()).index(current_label)

    st.sidebar.radio(
        label="Idioma / Language",
        options=lang_options.keys(),
        index=current_lang_index,
        key='language_selector_key',
        on_change=callback_update_language
    )

    st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")

    # --- 2. Cargador de Archivos ---
    uploader_label_es = get_text('es', 'uploader_label')
    uploader_label_en = get_text('en', 'uploader_label')
    static_uploader_label = f"{uploader_label_es} / {uploader_label_en}"

    uploaded_files = st.sidebar.file_uploader(
        static_uploader_label,
        type=["xlsx"],
        key="main_uploader",
        accept_multiple_files=True,
        on_change=clear_state_and_prepare_reload
    )
    
    # --- 3. Controles Dinámicos (Solo si hay datos) ---
    if df_loaded:
        
        # --- 3a. Creación de Filtros ---
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        lista_columnas_ui = [""] + todas_las_columnas_ui

        with st.sidebar.form(key='form_filtro'):
            columna_seleccionada_ui = st.selectbox(
                get_text(lang, 'column_select'),
                options=lista_columnas_ui,
                key='filter_col_select'
            )
            valor_a_buscar = st.text_input(
                get_text(lang, 'search_text'),
                key='filter_val_input',
                help="Escriba su búsqueda y presione 'Enter' o el botón 'Añadir'"
            )
            
            submitted = st.form_submit_button(
                get_text(lang, 'add_filter_button'), 
                key='add_filter_btn'
            )

            if submitted:
                col_val = st.session_state.filter_col_select
                val_val = st.session_state.filter_val_input

                if col_val and val_val:
                    columna_en_filtro = col_map_es_to_en.get(col_val, col_val)
                    nuevo_filtro = {"columna": columna_en_filtro, "valor": val_val}
                    
                    if nuevo_filtro not in st.session_state.filtros_activos:
                        st.session_state.filtros_activos.append(nuevo_filtro)
                        st.rerun()
                else:
                    st.sidebar.warning(get_text(lang, 'warning_no_filter'))
        
        # --- 3b. Selector de Columnas Visibles ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")
        
        if st.session_state.columnas_visibles is None:
             st.session_state.columnas_visibles = todas_las_columnas_en

        def callback_toggle_cols():
            if len(st.session_state.columnas_visibles) < len(todas_las_columnas_en):
                st.session_state.columnas_visibles = todas_las_columnas_en
            else:
                st.session_state.columnas_visibles = []
            # Actualizar el widget multiselect para reflejar el cambio
            st.session_state.visible_cols_multiselect = [
                translate_column(lang, col) for col in st.session_state.columnas_visibles
            ]

        def callback_update_cols_from_multiselect():
            columnas_seleccionadas_ui = st.session_state.visible_cols_multiselect
            columnas_seleccionadas_en = [
                col_map_es_to_en.get(col_ui, col_ui) 
                for col_ui in columnas_seleccionadas_ui
            ]
            st.session_state.columnas_visibles = columnas_seleccionadas_en

        st.sidebar.button(
            get_text(lang, 'visible_cols_toggle_button'), 
            key="toggle_cols_btn",
            on_click=callback_toggle_cols
        )
        defaults_ui = [translate_column(lang, col) for col in st.session_state.columnas_visibles]
        st.sidebar.multiselect(
            get_text(lang, 'visible_cols_select'),
            options=todas_las_columnas_ui,
            default=defaults_ui,
            key='visible_cols_multiselect',
            on_change=callback_update_cols_from_multiselect
        )

    # Retornamos los archivos cargados para que el gui.py principal sepa si debe procesar.
    return uploaded_files