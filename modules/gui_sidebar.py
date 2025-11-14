# modules/gui_sidebar.py (CORREGIDO Y DOCUMENTADO)
# Contiene toda la lógica para renderizar la barra lateral.
#
# --- CORRECCIÓN DE BUG DE REAPARICIÓN (Nov 2025) ---
# Se modificó el botón 'rules_edit_button' para usar 'on_click'.
# Anteriormente, estaba envuelto en un 'if st.sidebar.button(...)'.
# Ese método (usar 'if') puede causar que el botón se "reactive"
# erróneamente durante un 'rerun' de Streamlit que fue iniciado
# por *otro* control (ej. 'Guardar Borrador' en gui_views.py).
# Al usar 'on_click', nos aseguramos que el callback
# '_callback_open_rules_editor' SOLO se ejecute cuando el usuario
# presiona físicamente ese botón específico, resolviendo el bug
# de la reaparición del modal.
# --------------------------------------------------------

import streamlit as st
import json
from modules.translator import get_text, translate_column
from modules.utils import clear_state_and_prepare_reload
# --- [NUEVO] Importar las reglas por defecto ---
from modules.rules_service import get_default_rules

# --- [INICIO] CORRECCIÓN: Callback para abrir el editor ---
# Se define esta función de callback para estandarizar el manejo del estado.
# 'on_click' es la forma preferida de manejar cambios de estado
# que se inician por botones en aplicaciones complejas de Streamlit.
def _callback_open_rules_editor():
    """
    Establece el estado 'show_rules_editor' en True.
    
    Esta función se llama exclusivamente por el 'on_click' del botón
    'show_rules_editor_btn' en la barra lateral.
    """
    st.session_state.show_rules_editor = True
# --- [FIN] CORRECCIÓN ---


def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    """
    Renderiza todo el contenido de la barra lateral.

    Args:
        lang (str): Código de idioma actual (ej. 'es', 'en').
        df_loaded (bool): True si hay un DataFrame cargado en st.session_state.
        todas_las_columnas_ui (list, optional): Lista de nombres de columnas
                                                traducidas para la UI.
        col_map_es_to_en (dict, optional): Mapeo de nombres de columnas
                                           traducidos a nombres en inglés.
        todas_las_columnas_en (list, optional): Lista de nombres de columnas
                                                originales (inglés).

    Returns:
        list: La lista de archivos cargados (de st.sidebar.file_uploader).
    """

    # --- 1. Selector de Idioma ---
    # (Sin cambios)
    lang_options = {"Español": "es", "English": "en"}

    def callback_update_language():
        """
        Callback para actualizar el idioma en st.session_state
        cuando el radio button cambia.
        """
        # (Línea de documentación interna)
        # Obtiene la etiqueta seleccionada (ej. "Español")
        selected_label = st.session_state.language_selector_key
        # (Línea de documentación interna)
        # Convierte la etiqueta al código (ej. "es")
        lang_code = lang_options[selected_label]
        # (Línea de documentación interna)
        # Almacena el código en el estado de la sesión
        st.session_state.language = lang_code

    # (Línea de documentación interna)
    # Mapeo inverso para encontrar la etiqueta actual (ej. "es" -> "Español")
    lang_code_to_label = {v: k for k, v in lang_options.items()}
    current_label = lang_code_to_label.get(st.session_state.language, "Español")
    # (Línea de documentación interna)
    # Encontrar el índice de la opción actual para 'st.radio'
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
    # (Línea de documentación interna)
    # Etiqueta estática bilingüe para el cargador de archivos
    static_uploader_label = f"{uploader_label_es} / {uploader_label_en}"

    uploaded_files = st.sidebar.file_uploader(
        static_uploader_label,
        type=["xlsx"],
        key="main_uploader",
        accept_multiple_files=True,
        on_change=clear_state_and_prepare_reload # Limpia el estado al cargar
    )

    # --- 3. Controles Dinámicos (Solo si hay datos) ---
    # (Línea de documentación interna)
    # Esta sección solo aparece si 'df_staging' existe
    if df_loaded:

        # --- 3a. Creación de Filtros (Sin formulario) ---
        # (Sin cambios)
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        lista_columnas_ui = [""] + todas_las_columnas_ui

        columna_seleccionada_ui = st.selectbox(
            get_text(lang, 'column_select'),
            options=lista_columnas_ui,
            key='filter_col_select'
        )

        # (Línea de documentación interna)
        # Traduce la columna seleccionada en la UI a su nombre original (inglés)
        columna_en_filtro = col_map_es_to_en.get(columna_seleccionada_ui, columna_seleccionada_ui)
        autocomplete_cols = st.session_state.get('autocomplete_options', {})

        # (Línea de documentación interna)
        # Lógica para mostrar Selectbox (si hay opciones) o Textbox
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

            # (Línea de documentación interna)
            # Lógica para cambiar el placeholder si se filtra por 'Row Status'
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

        # (Línea de documentación interna)
        # Lógica de envío del filtro (sin 'on_click' porque es un form simple)
        submitted = st.button(
            get_text(lang, 'add_filter_button'),
            key='add_filter_btn'
        )

        if submitted:
            col_val_ui = st.session_state.filter_col_select
            val_val = None
            col_en_para_guardar = col_map_es_to_en.get(col_val_ui, col_val_ui)

            # (Línea de documentación interna)
            # Determina si el valor viene de un selectbox o un text_input
            if col_en_para_guardar in autocomplete_cols:
                val_val = st.session_state.filter_val_select
            else:
                val_val = st.session_state.filter_val_text

            if col_val_ui and val_val:
                nuevo_filtro = {"columna": col_en_para_guardar, "valor": val_val}

                # (Línea de documentation interna)
                # Añade el filtro solo si no es un duplicado
                if nuevo_filtro not in st.session_state.filtros_activos:
                    st.session_state.filtros_activos.append(nuevo_filtro)
                    st.rerun() # Recarga la app para aplicar el filtro
            else:
                st.sidebar.warning(get_text(lang, 'warning_no_filter'))

        # --- 3b. Selector de Columnas Visibles ---
        # (Sin cambios)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")

        # (Línea de documentación interna)
        # Inicializa las columnas visibles si es la primera vez
        if st.session_state.columnas_visibles is None:
             st.session_state.columnas_visibles = todas_las_columnas_en

        def callback_toggle_cols():
            """
            Callback para el botón 'Activar/Desactivar Todas'.
            Si hay menos columnas visibles que el total, las activa todas.
            Si no, las desactiva todas (lista vacía).
            """
            if len(st.session_state.columnas_visibles) < len(todas_las_columnas_en):
                st.session_state.columnas_visibles = todas_las_columnas_en
            else:
                st.session_state.columnas_visibles = []
            # (Línea de documentación interna)
            # Actualiza el multiselect para reflejar el cambio
            st.session_state.visible_cols_multiselect = [translate_column(lang, col) for col in st.session_state.columnas_visibles]

        def callback_update_cols_from_multiselect():
            """
            Callback para actualizar 'columnas_visibles' (nombres en inglés)
            cuando el 'multiselect' (nombres traducidos) cambia.
            """
            columnas_seleccionadas_ui = st.session_state.visible_cols_multiselect
            # (Línea de documentación interna)
            # Mapeo inverso: de UI (traducido) de vuelta a 'en' (original)
            columnas_seleccionadas_en = [col_en for col_en in todas_las_columnas_en if translate_column(lang, col_en) in columnas_seleccionadas_ui]
            st.session_state.columnas_visibles = columnas_seleccionadas_en

        st.sidebar.button(get_text(lang, 'visible_cols_toggle_button'), key="toggle_cols_btn", on_click=callback_toggle_cols)
        # (Línea de documentación interna)
        # Define los valores por defecto del multiselect (traducidos)
        defaults_ui = [translate_column(lang, col) for col in st.session_state.columnas_visibles]
        st.sidebar.multiselect(
            get_text(lang, 'visible_cols_select'),
            options=todas_las_columnas_ui,
            default=defaults_ui,
            key='visible_cols_multiselect',
            on_change=callback_update_cols_from_multiselect
        )

        # --- SECCIÓN GESTIÓN DE CONFIGURACIÓN (VISUAL) ---
        # (Sin cambios)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'config_header')}")
        st.sidebar.caption(get_text(lang, 'config_help_text'))

        # (Línea de documentación interna)
        # Recopila todo el estado relevante en un diccionario
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
        # (Línea de documentación interna)
        # Convierte el diccionario a un string JSON formateado
        json_string = json.dumps(config_data, indent=2)

        st.sidebar.download_button(
            label=get_text(lang, 'save_config_button'),
            data=json_string,
            file_name="configuracion_facturas.json",
            mime="application/json",
            key="save_config_btn",
            use_container_width=True
        )

        def callback_process_config():
            """
            Callback para cargar y aplicar un archivo de configuración JSON.
            """
            file = st.session_state.config_uploader
            if file is None: return
            try:
                # (Línea de documentación interna)
                # Carga el contenido del archivo JSON
                config_loaded = json.load(file)
                # (Línea de documentación interna)
                # Aplica los valores del JSON al st.session_state
                st.session_state.filtros_activos = config_loaded.get("filtros_activos", [])
                st.session_state.columnas_visibles = config_loaded.get("columnas_visibles", todas_las_columnas_en)
                st.session_state.language = config_loaded.get("language", st.session_state.language)
                st.session_state.view_type_radio = config_loaded.get("view_type", get_text(lang, 'view_type_detailed'))
                st.session_state.group_by_col_select = config_loaded.get("group_by_column", None)
                st.session_state.priority_sort_order = config_loaded.get("priority_sort_order", None)
                if "autocomplete_options" in config_loaded:
                    st.session_state.autocomplete_options = config_loaded["autocomplete_options"]

                # (Línea de documentación interna)
                # Carga las reglas y el log de auditoría
                st.session_state.priority_rules = config_loaded.get("priority_rules", get_default_rules())
                st.session_state.audit_log = config_loaded.get("audit_log", [])

                st.rerun() # Recarga la app para aplicar la configuración
            except Exception as e:
                st.error(f"Error al cargar configuración: {e}")

        st.sidebar.file_uploader(
            label=get_text(lang, 'load_config_label'),
            type=["json"],
            key="config_uploader",
            accept_multiple_files=False,
            on_change=callback_process_config
        )

        if st.sidebar.button(get_text(lang, 'reset_config_button'), use_container_width=True):
            # (Línea de documentación interna)
            # Resetea los filtros y columnas a su estado por defecto
            st.session_state.filtros_activos = []
            st.session_state.columnas_visibles = todas_las_columnas_en
            st.session_state.priority_sort_order = None
            st.session_state.group_by_col_select = None
            st.success(get_text(lang, 'reset_config_success'))
            st.rerun()

        # --- SECCIÓN LÓGICA DE NEGOCIO ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'rules_header')}")

        # --- [INICIO] CORRECCIÓN DEL BUG DE REAPARICIÓN ---
        # Se elimina el 'if' que envolvía este botón.
        # Ahora, usamos 'on_click' para llamar al callback
        # '_callback_open_rules_editor' definido al inicio del archivo.
        # Esto previene que el modal se abra en 'reruns'
        # no deseados.
        st.sidebar.button(
            get_text(lang, 'rules_edit_button'),
            use_container_width=True,
            key="show_rules_editor_btn", # La 'key' sigue siendo importante
            on_click=_callback_open_rules_editor # <-- ESTA ES LA CORRECCIÓN
        )
        # --- [FIN] CORRECCIÓN DEL BUG DE REAPARICIÓN ---
        
        # --- SECCIÓN GESTIÓN DE LISTAS (AUTOCOMPLETADO) ---
        # (Sin cambios)
        if st.session_state.get('autocomplete_options'):
            st.sidebar.markdown("---")
            with st.sidebar.expander(get_text(lang, 'manage_autocomplete_header'), expanded=False):
                st.info(get_text(lang, 'manage_autocomplete_info'))

                # (Línea de documentación interna)
                # Mapeo de UI (traducido) a 'en' (original) para el selectbox
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
                    # (Línea de documentación interna)
                    # Muestra un resumen de las opciones actuales
                    st.caption(", ".join(map(str, current_opts[:8])) + ("..." if len(current_opts) > 8 else ""))

                    col_add1, col_add2 = st.columns([0.7, 0.3])
                    with col_add1:
                        new_option_val = st.text_input(
                            get_text(lang, 'add_option_label'),
                            label_visibility="collapsed",
                            placeholder=get_text(lang, 'add_option_placeholder'),
                            key=f"add_opt_input_{col_en_selected}" # Key dinámica
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
                        key=f"remove_opt_multi_{col_en_selected}" # Key dinámica
                    )

                    if st.button(get_text(lang, 'remove_option_btn'), key=f"btn_rem_{col_en_selected}"):
                        if opts_to_remove:
                            # (Línea de documentación interna)
                            # Re-crea la lista excluyendo las opciones seleccionadas
                            new_list = [x for x in current_opts if x not in opts_to_remove]
                            st.session_state.autocomplete_options[col_en_selected] = new_list
                            st.success(get_text(lang, 'options_removed_success').format(n=len(opts_to_remove), col=col_ui_selected))
                            st.rerun()

    # (Línea de documentación interna)
    # Devuelve los archivos cargados al script principal 'app.py'
    return uploaded_files

