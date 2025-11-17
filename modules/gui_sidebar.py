# modules/gui_sidebar.py (VERSIÓN 2.5 - CORRECCIÓN DEFINITIVA DE RE-CARGA DE CONFIG)
# Contiene toda la lógica para renderizar la barra lateral.
#
# --- CORRECCIÓN DE BUG (v2.5 Nov 2025) ---
# Problema: La v2.4 fallaba porque el widget 'file_uploader' podía
# reportar 'None' brevemente durante un 'rerun', activando el
# 'else' que reseteaba la bandera 'config_file_processed' a 'False'.
#
# Solución: Se eliminó el bloque 'else'. La bandera ahora es "pegajosa".
# Solo se resetea a 'False' por acciones explícitas del usuario:
# 1. Al cargar un nuevo Excel (en 'clear_state_and_prepare_reload').
# 2. Al presionar "Restablecer Todo" (lógica añadida a ese botón).
# Esto previene que los filtros se sobrescriban en 'reruns' normales.
# -----------------------------------------------------------------

import streamlit as st
import json
from modules.translator import get_text, translate_column
from modules.utils import clear_state_and_prepare_reload
# (Línea de documentación interna)
# Importar el motor de reglas y las reglas por defecto.
from modules.rules_service import get_default_rules, apply_priority_rules

# (Línea de documentación interna)
# Callback para el botón 'on_click' que abre el modal de reglas.
def _callback_open_rules_editor():
    """
    Establece el estado 'show_rules_editor' en True.
    
    Esta función se llama exclusivamente por el 'on_click' del botón
    'show_rules_editor_btn' en la barra lateral.
    """
    st.session_state.show_rules_editor = True


def callback_process_config(file):
    """
    Callback para cargar y aplicar un archivo de configuración JSON.
    
    Esta función ahora es llamada manualmente por la lógica de
    renderizado para asegurar que se ejecute UNA SOLA VEZ.
    """
    if file is None: return False
    try:
        # (Línea de documentación interna)
        # Carga el contenido del archivo JSON (BytesIO)
        config_loaded = json.load(file)
        
        # (Línea de documentación interna)
        # Aplica los valores del JSON al st.session_state
        st.session_state.filtros_activos = config_loaded.get("filtros_activos", [])
        st.session_state.columnas_visibles = config_loaded.get("columnas_visibles", st.session_state.columnas_visibles)
        st.session_state.language = config_loaded.get("language", st.session_state.language)
        st.session_state.view_type_radio = config_loaded.get("view_type", get_text(st.session_state.language, 'view_type_detailed'))
        st.session_state.group_by_col_select = config_loaded.get("group_by_column", None)
        st.session_state.priority_sort_order = config_loaded.get("priority_sort_order", None)
        if "autocomplete_options" in config_loaded:
            st.session_state.autocomplete_options = config_loaded["autocomplete_options"]

        st.session_state.priority_rules = config_loaded.get("priority_rules", get_default_rules())
        st.session_state.audit_log = config_loaded.get("audit_log", [])

        # (Línea de documentación interna)
        # (Corrección v2.0) Aplica las reglas recién cargadas
        if st.session_state.df_staging is not None:
            df_staging_copy = st.session_state.df_staging.copy()
            st.session_state.df_staging = apply_priority_rules(df_staging_copy)
            st.session_state.current_data_hash = None
            st.session_state.editor_state = None
        
    except Exception as e:
        st.error(f"Error al cargar configuración: {e}")
        return False # Retorna Falso si falla
    
    return True # Retorna Verdadero si tiene éxito


def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    """
    Renderiza todo el contenido de la barra lateral.
    (Documentación de args/returns omitida por brevedad)
    """

    # --- 1. Selector de Idioma ---
    # (Sin cambios)
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
    # (Sin cambios)
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
        # (Sin cambios)
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        lista_columnas_ui = [""] + todas_las_columnas_ui

        columna_seleccionada_ui = st.selectbox(
            get_text(lang, 'column_select'),
            options=lista_columnas_ui,
            key='filter_col_select'
        )

        columna_en_filtro = col_map_es_to_en.get(columna_seleccionada_ui, columna_seleccionada_ui)
        autocomplete_cols = st.session_state.get('autocomplete_options', {})

        if columna_en_filtro in autocomplete_cols:
            opciones = [""] + sorted(autocomplete_cols[columna_en_filtro])
            st.selectbox(
                get_text(lang, 'column_select_value'),
                options=opciones,
                key='filter_val_select'
            )
        else:
            col_estado_traducida = translate_column(lang, "Row Status")
            placeholder_default = get_text(lang, 'search_text_placeholder_default')
            help_default = get_text(lang, 'search_text_help_default')

            if columna_seleccionada_ui == col_estado_traducida:
                placeholder_text = get_text(lang, 'search_text_placeholder_status')
                help_text = get_text(lang, 'search_text_help_status')
            else:
                placeholder_text = placeholder_default
                help_text = help_default

            st.text_input(
                get_text(lang, 'search_text'),
                key='filter_val_text',
                placeholder=placeholder_text,
                help=help_text
            )

        submitted = st.button(
            get_text(lang, 'add_filter_button'),
            key='add_filter_btn'
        )

        if submitted:
            col_val_ui = st.session_state.filter_col_select
            val_val = None
            col_en_para_guardar = col_map_es_to_en.get(col_val_ui, col_val_ui)

            if col_en_para_guardar in autocomplete_cols:
                val_val = st.session_state.filter_val_select
            else:
                val_val = st.session_state.filter_val_text

            if col_val_ui and val_val:
                nuevo_filtro = {"columna": col_en_para_guardar, "valor": val_val}
                if nuevo_filtro not in st.session_state.filtros_activos:
                    st.session_state.filtros_activos.append(nuevo_filtro)
                    st.rerun()
            else:
                st.sidebar.warning(get_text(lang, 'warning_no_filter'))

        # --- 3b. Selector de Columnas Visibles ---
        # (Sin cambios)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")

        if st.session_state.columnas_visibles is None:
             st.session_state.columnas_visibles = todas_las_columnas_en

        def callback_toggle_cols():
            if len(st.session_state.columnas_visibles) < len(todas_las_columnas_en):
                st.session_state.columnas_visibles = todas_las_columnas_en
            else:
                st.session_state.columnas_visibles = []
            st.session_state.visible_cols_multiselect = [translate_column(lang, col) for col in st.session_state.columnas_visibles]

        def callback_update_cols_from_multiselect():
            columnas_seleccionadas_ui = st.session_state.visible_cols_multiselect
            columnas_seleccionadas_en = [col_en for col_en in todas_las_columnas_en if translate_column(lang, col_en) in columnas_seleccionadas_ui]
            st.session_state.columnas_visibles = columnas_seleccionadas_en

        st.sidebar.button(get_text(lang, 'visible_cols_toggle_button'), key="toggle_cols_btn", on_click=callback_toggle_cols)
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

        config_data = {
            "filtros_activos": st.session_state.get('filtros_activos', []),
            "columnas_visibles": st.session_state.get('columnas_visibles', todas_las_columnas_en),
            "language": st.session_state.get('language', 'es'),
            "view_type": st.session_state.get('view_type_radio', get_text(lang, 'view_type_detailed')),
            "group_by_column": st.session_state.get('group_by_col_select', None),
            "priority_sort_order": st.session_state.get('priority_sort_order', None),
            "autocomplete_options": st.session_state.get('autocomplete_options', {}),
            "priority_rules": st.session_state.get('priority_rules', []),
            "audit_log": st.session_state.get('audit_log', [])
        }
        json_string = json.dumps(config_data, indent=2)

        st.sidebar.download_button(
            label=get_text(lang, 'save_config_button'),
            data=json_string,
            file_name="configuracion_facturas.json",
            mime="application/json",
            key="save_config_btn",
            use_container_width=True
        )


        # --- [INICIO] CORRECCIÓN (v2.5) ---
        # (Línea de documentación interna)
        # Renderiza el widget. 'on_change' se ha eliminado.
        config_file = st.sidebar.file_uploader(
            label=get_text(lang, 'load_config_label'),
            type=["json"],
            key="config_uploader", # La 'key' es usada para el estado del widget
            accept_multiple_files=False
            # on_change=... <-- LÍNEA ELIMINADA
        )

        # (Línea de documentación interna)
        # Nueva lógica de procesamiento manual que se ejecuta
        # en cada 'rerun' pero solo procesa el archivo UNA VEZ.
        if config_file is not None:
            # (Línea de documentación interna)
            # Se ha cargado un archivo. Comprobamos si ya lo hemos procesado.
            # Usamos la bandera (flag) 'config_file_processed'.
            if not st.session_state.config_file_processed:
                # (Línea de documentación interna)
                # Este es un archivo NUEVO (o el primero). Lo procesamos.
                success = callback_process_config(config_file)
                
                if success:
                    # (Línea de documentación interna)
                    # Marcamos la bandera como "procesado".
                    st.session_state.config_file_processed = True
                    
                    # (Línea de documentación interna)
                    # Forzamos un 'rerun' para que la app refleje
                    # la nueva configuración.
                    st.rerun()
        # --- [FIN] CORRECCIÓN (v2.5) ---
        # El 'else' que reseteaba la bandera ha sido eliminado.


        if st.sidebar.button(get_text(lang, 'reset_config_button'), use_container_width=True):
            st.session_state.filtros_activos = []
            st.session_state.columnas_visibles = todas_las_columnas_en
            st.session_state.priority_sort_order = None
            st.session_state.group_by_col_select = None
            st.success(get_text(lang, 'reset_config_success'))
            
            # --- [INICIO] CORRECCIÓN (v2.5) ---
            # (Línea de documentación interna)
            # Reseteamos la bandera explícitamente solo cuando
            # el usuario presiona "Restablecer Todo".
            st.session_state.config_file_processed = False
            if "config_uploader" in st.session_state:
                 del st.session_state.config_uploader
            # --- [FIN] CORRECCIÓN (v2.5) ---
            
            st.rerun()

        # --- SECCIÓN LÓGICA DE NEGOCIO ---
        # (Sin cambios)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'rules_header')}")

        st.sidebar.button(
            get_text(lang, 'rules_edit_button'),
            use_container_width=True,
            key="show_rules_editor_btn",
            on_click=_callback_open_rules_editor
        )
        
        # --- SECCIÓN GESTIÓN DE LISTAS (AUTOCOMPLETADO) ---
        # (Sin cambios)
        if st.session_state.get('autocomplete_options'):
            st.sidebar.markdown("---")
            with st.sidebar.expander(get_text(lang, 'manage_autocomplete_header'), expanded=False):
                st.info(get_text(lang, 'manage_autocomplete_info'))

                col_options_map = { translate_column(lang, k): k for k in st.session_state.autocomplete_options.keys() }
                col_ui_selected = st.selectbox(
                    get_text(lang, 'select_column_to_edit'),
                    options=sorted(list(col_options_map.keys())),
                    key="autocomplete_col_select"
                )

                if col_ui_selected:
                    col_en_selected = col_options_map[col_ui_selected]
                    current_opts = st.session_state.autocomplete_options.get(col_en_selected, [])

                    st.markdown(f"**{get_text(lang, 'current_options').format(n=len(current_opts))}**")
                    st.caption(", ".join(map(str, current_opts[:8])) + ("..." if len(current_opts) > 8 else ""))

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

    # (Línea de documentación interna)
    # Devuelve los archivos cargados al script principal 'app.py'
    return uploaded_files