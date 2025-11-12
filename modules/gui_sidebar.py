# modules/gui_sidebar.py (VERSIÓN CON REVERSIÓN ESTABLE AL QUITAR JSON)
# Contiene toda la lógica para renderizar la barra lateral.

import streamlit as st
import json 
from modules.translator import get_text, translate_column
from modules.gui_utils import clear_state_and_prepare_reload

def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    """
    Renderiza todo el contenido de la barra lateral.
    Retorna:
    - uploaded_files (list): Lista de archivos Excel cargados.
    """
    
    # --- 1. Selector de Idioma ---
    # (Esta sección no tiene cambios)
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
    # (Esta sección no tiene cambios)
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
        # (Esta sección no tiene cambios)
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
        # (Esta sección no tiene cambios)
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
        
        # --- [INICIO] SECCIÓN GUARDAR/CARGAR VISTA (MODIFICADA) ---
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'config_header')}")
        
        # 1. Widget de Descarga (Guardar Vista)
        # (Lógica sin cambios)
        config_data = {
            "filtros_activos": st.session_state.get('filtros_activos', []),
            "columnas_visibles": st.session_state.get('columnas_visibles', todas_las_columnas_en),
            "language": st.session_state.get('language', 'es'),
            "view_type": st.session_state.get('view_type_radio', get_text(lang, 'view_type_detailed')),
            "group_by_column": st.session_state.get('group_by_col_select', None)
        }
        json_string = json.dumps(config_data, indent=2)

        st.sidebar.download_button(
            label=get_text(lang, 'save_config_button'),
            data=json_string,
            file_name="mi_vista_facturas.json",
            mime="application/json",
            key="save_config_btn",
            use_container_width=True
        )

        # 2. Lógica de Carga (Callback)
        def callback_process_config():
            """
            Se llama cuando el st.file_uploader 'config_uploader' detecta
            un CAMBIO (archivo cargado O archivo eliminado).
            """
            # 'file': Obtiene el archivo (si existe) desde el estado.
            file = st.session_state.config_uploader
            
            # --- [INICIO] LÓGICA DE REVERSIÓN ESTABLE ---
            if file is None:
                # 'file is None' significa que el usuario hizo clic en la 'X'
                # para eliminar el archivo JSON.
                # Se activa la lógica de "Revertir a Estable" (como Ctrl+Z).
                
                # 1. Revertir datos a 'df_original' (Estable)
                if st.session_state.df_original is not None:
                    st.session_state.df_staging = st.session_state.df_original.copy()
                
                # 2. Revertir columnas visibles a 'columnas_visibles_estable'
                if st.session_state.columnas_visibles_estable is not None:
                    st.session_state.columnas_visibles = st.session_state.columnas_visibles_estable.copy()
                elif todas_las_columnas_en is not None:
                    # Fallback si 'estable' no existe, usar todas.
                    st.session_state.columnas_visibles = todas_las_columnas_en.copy()
                
                # 3. Limpiar filtros activos
                st.session_state.filtros_activos = []
                
                # 4. Resetear el editor (para forzar recarga)
                # Esta lógica es la misma que en _callback_revertir_estable
                st.session_state.editor_state = None
                st.session_state.current_data_hash = None
                st.session_state.current_lang_hash = None
                
                # 'return': Termina la función. Streamlit hará un rerun.
                return
            # --- [FIN] LÓGICA DE REVERSIÓN ESTABLE ---

            # Si 'file' NO es None, significa que se cargó un nuevo JSON.
            # Se procede a cargar la configuración del archivo.
            try:
                # 'config_data': Carga el contenido del archivo JSON.
                config_data = json.load(file)
                
                # 'st.session_state.filtros_activos': Restaura los filtros.
                st.session_state.filtros_activos = config_data.get("filtros_activos", [])
                
                # 'st.session_state.columnas_visibles': Restaura las columnas.
                st.session_state.columnas_visibles = config_data.get(
                    "columnas_visibles", todas_las_columnas_en
                )
                
                # 'st.session_state.language': Restaura el idioma.
                st.session_state.language = config_data.get(
                    "language", st.session_state.language
                )
                
                # 'st.session_state.view_type_radio': Restaura la vista.
                st.session_state.view_type_radio = config_data.get(
                    "view_type", get_text(lang, 'view_type_detailed')
                )
                
                # 'st.session_state.group_by_col_select': Restaura la agrupación.
                st.session_state.group_by_col_select = config_data.get(
                    "group_by_column", None
                )

                # 'st.rerun()': Se fuerza un rerun para aplicar todo.
                st.rerun()

            except Exception as e:
                # 'st.error': Muestra un error si el JSON es inválido.
                st.error(f"Error al cargar el archivo de configuración: {e}")
                # (No es necesario limpiar el uploader,
                #  el callback lo hará si el usuario carga otro archivo)

        # 3. Widget de Carga (Cargar Vista)
        st.sidebar.file_uploader(
            label=get_text(lang, 'load_config_label'),
            type=["json"],
            key="config_uploader",
            accept_multiple_files=False,
            on_change=callback_process_config # Asigna el callback
        )
        # --- [FIN] SECCIÓN MODIFICADA ---

    # 'return uploaded_files': Solo retorna los archivos Excel.
    return uploaded_files
