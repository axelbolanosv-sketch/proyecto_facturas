# modules/gui_sidebar.py (VERSIÓN CON GESTIÓN DE LISTAS Y CONFIGURACIÓN AMIGABLE)
# Contiene toda la lógica para renderizar la barra lateral.

import streamlit as st
import json 
from modules.translator import get_text, translate_column
from modules.gui_utils import clear_state_and_prepare_reload

def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    """
    Renderiza todo el contenido de la barra lateral.
    
    Args:
        lang (str): Código de idioma actual ('es' o 'en').
        df_loaded (bool): True si hay datos cargados en st.session_state.
        todas_las_columnas_ui (list): Lista de nombres de columnas para la UI.
        col_map_es_to_en (dict): Mapa de traducción inversa (UI -> Inglés).
        todas_las_columnas_en (list): Lista de nombres de columnas originales (Inglés).

    Returns:
        list: Lista de archivos Excel cargados (uploaded_files).
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

    # --- 2. Cargador de Archivos (Excel) ---
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
            
            col_estado_traducida = translate_column(lang, "Row Status")
            placeholder_default = get_text(lang, 'search_text_placeholder_default')
            help_default = get_text(lang, 'search_text_help_default')
            
            if columna_seleccionada_ui == col_estado_traducida:
                placeholder_text = get_text(lang, 'search_text_placeholder_status')
                help_text = get_text(lang, 'search_text_help_status')
            else:
                placeholder_text = placeholder_default
                help_text = help_default

            valor_a_buscar = st.text_input(
                get_text(lang, 'search_text'),
                key='filter_val_input',
                placeholder=placeholder_text,
                help=help_text
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
            
            st.session_state.visible_cols_multiselect = [
                translate_column(lang, col) for col in st.session_state.columnas_visibles
            ]

        def callback_update_cols_from_multiselect():
            columnas_seleccionadas_ui = st.session_state.visible_cols_multiselect
            
            columnas_seleccionadas_en = [
                col_en for col_en in todas_las_columnas_en
                if translate_column(lang, col_en) in columnas_seleccionadas_ui
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
        
        # --- SECCIÓN GESTIÓN DE CONFIGURACIÓN (VISUAL) ---
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'config_header')}")
        st.sidebar.caption(get_text(lang, 'config_help_text'))
        
        # Recolectar datos actuales de la configuración
        config_data = {
            "filtros_activos": st.session_state.get('filtros_activos', []),
            "columnas_visibles": st.session_state.get('columnas_visibles', todas_las_columnas_en),
            "language": st.session_state.get('language', 'es'),
            "view_type": st.session_state.get('view_type_radio', get_text(lang, 'view_type_detailed')),
            "group_by_column": st.session_state.get('group_by_col_select', None),
            "priority_sort_order": st.session_state.get('priority_sort_order', None),
            # Opcional: Guardar también las listas personalizadas
            "autocomplete_options": st.session_state.get('autocomplete_options', {})
        }
        json_string = json.dumps(config_data, indent=2)

        # 1. Botón de Guardar (Descarga)
        st.sidebar.download_button(
            label=get_text(lang, 'save_config_button'),
            data=json_string,
            file_name="configuracion_facturas.json",
            mime="application/json",
            key="save_config_btn",
            use_container_width=True
        )

        # 2. Lógica de Carga (Upload)
        def callback_process_config():
            file = st.session_state.config_uploader
            if file is None: return

            try:
                config_loaded = json.load(file)
                
                st.session_state.filtros_activos = config_loaded.get("filtros_activos", [])
                st.session_state.columnas_visibles = config_loaded.get("columnas_visibles", todas_las_columnas_en)
                st.session_state.language = config_loaded.get("language", st.session_state.language)
                st.session_state.view_type_radio = config_loaded.get("view_type", get_text(lang, 'view_type_detailed'))
                st.session_state.group_by_col_select = config_loaded.get("group_by_column", None)
                st.session_state.priority_sort_order = config_loaded.get("priority_sort_order", None)
                
                # Cargar también las listas personalizadas si existen
                if "autocomplete_options" in config_loaded:
                    st.session_state.autocomplete_options = config_loaded["autocomplete_options"]

                st.rerun()
            except Exception as e:
                st.error(f"Error al cargar configuración: {e}")

        # Widget de Carga
        st.sidebar.file_uploader(
            label=get_text(lang, 'load_config_label'),
            type=["json"],
            key="config_uploader",
            accept_multiple_files=False,
            on_change=callback_process_config 
        )
        
        # 3. Botón de Restablecer
        if st.sidebar.button(get_text(lang, 'reset_config_button'), use_container_width=True):
            st.session_state.filtros_activos = []
            st.session_state.columnas_visibles = todas_las_columnas_en
            st.session_state.priority_sort_order = None
            st.session_state.group_by_col_select = None
            st.success(get_text(lang, 'reset_config_success'))
            st.rerun()

        # --- [NUEVO] SECCIÓN GESTIÓN DE LISTAS (AUTOCOMPLETADO) ---
        # Permite al usuario modificar las opciones de los selectbox en la tabla.
        
        if st.session_state.get('autocomplete_options'):
            st.sidebar.markdown("---")
            # Usamos un expander para mantener la interfaz limpia
            with st.sidebar.expander(get_text(lang, 'manage_autocomplete_header'), expanded=False):
                st.info(get_text(lang, 'manage_autocomplete_info'))
                
                # 1. Selector de Columna
                # Mapeamos nombres UI (Español/Inglés) -> Claves internas (Inglés)
                col_options_map = {
                    translate_column(lang, k): k 
                    for k in st.session_state.autocomplete_options.keys()
                }
                
                col_ui_selected = st.selectbox(
                    get_text(lang, 'select_column_to_edit'),
                    options=sorted(list(col_options_map.keys())),
                    key="autocomplete_col_select"
                )
                
                if col_ui_selected:
                    # Recuperamos la clave interna y la lista actual
                    col_en_selected = col_options_map[col_ui_selected]
                    current_opts = st.session_state.autocomplete_options.get(col_en_selected, [])
                    
                    # Mostramos un resumen visual
                    st.markdown(f"**{get_text(lang, 'current_options').format(n=len(current_opts))}**")
                    st.caption(", ".join(map(str, current_opts[:8])) + ("..." if len(current_opts) > 8 else ""))
                    
                    # 2. Añadir Opción
                    col_add1, col_add2 = st.columns([0.7, 0.3])
                    with col_add1:
                        new_option_val = st.text_input(
                            get_text(lang, 'add_option_label'), 
                            label_visibility="collapsed",
                            placeholder=get_text(lang, 'add_option_placeholder'),
                            key=f"add_opt_input_{col_en_selected}" 
                        )
                    with col_add2:
                        if st.button(get_text(lang, 'add_option_btn'), key=f"btn_add_{col_en_selected}"):
                            if new_option_val and new_option_val not in current_opts:
                                current_opts.append(str(new_option_val))
                                current_opts.sort()
                                st.session_state.autocomplete_options[col_en_selected] = current_opts
                                st.success(get_text(lang, 'option_added_success').format(val=new_option_val, col=col_ui_selected))
                                st.rerun()
                    
                    # 3. Eliminar Opciones
                    opts_to_remove = st.multiselect(
                        get_text(lang, 'remove_options_label'),
                        options=current_opts,
                        key=f"remove_opt_multi_{col_en_selected}"
                    )
                    
                    if st.button(get_text(lang, 'remove_option_btn'), key=f"btn_rem_{col_en_selected}"):
                        if opts_to_remove:
                            new_list = [x for x in current_opts if x not in opts_to_remove]
                            st.session_state.autocomplete_options[col_en_selected] = new_list
                            st.success(get_text(lang, 'options_removed_success').format(n=len(opts_to_remove), col=col_ui_selected))
                            st.rerun()

    return uploaded_files