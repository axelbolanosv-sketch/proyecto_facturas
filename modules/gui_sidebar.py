# modules/gui_sidebar.py (VERSIÓN CON BOTÓN OBSOLETO ELIMINADO)
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
    # 'lang_options': Define los idiomas disponibles y sus códigos.
    lang_options = {"Español": "es", "English": "en"}

    def callback_update_language():
        """
        Callback para el 'radio' de idioma.
        Actualiza el 'st.session_state.language' basado en la selección.
        """
        # 'st.session_state.language_selector_key': Obtiene la etiqueta seleccionada (ej. "Español").
        selected_label = st.session_state.language_selector_key
        # 'lang_code': Convierte la etiqueta al código (ej. "es").
        lang_code = lang_options[selected_label]
        # 'st.session_state.language': Almacena el nuevo idioma en el estado.
        st.session_state.language = lang_code
    
    # 'lang_code_to_label': Diccionario inverso para encontrar la etiqueta actual.
    lang_code_to_label = {v: k for k, v in lang_options.items()}
    # 'current_label': Obtiene la etiqueta del idioma actual (ej. "Español").
    current_label = lang_code_to_label.get(st.session_state.language, "Español")
    # 'current_lang_index': Encuentra el índice numérico de la etiqueta actual.
    current_lang_index = list(lang_options.keys()).index(current_label)

    # 'st.sidebar.radio': Renderiza el selector de idioma en la barra lateral.
    st.sidebar.radio(
        label="Idioma / Language",
        options=lang_options.keys(),
        index=current_lang_index,
        key='language_selector_key',
        on_change=callback_update_language
    )

    # 'st.sidebar.markdown': Renderiza el título del área de control.
    st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")

    # --- 2. Cargador de Archivos ---
    # 'uploader_label_es'/'en': Obtiene el texto en ambos idiomas.
    uploader_label_es = get_text('es', 'uploader_label')
    uploader_label_en = get_text('en', 'uploader_label')
    # 'static_uploader_label': Crea una etiqueta estática para que siempre sea legible.
    static_uploader_label = f"{uploader_label_es} / {uploader_label_en}"

    # 'st.sidebar.file_uploader': Renderiza el widget de carga de archivos.
    uploaded_files = st.sidebar.file_uploader(
        static_uploader_label,
        type=["xlsx"],
        key="main_uploader",
        accept_multiple_files=True,
        # 'on_change': Llama a la función de limpieza si los archivos cambian.
        on_change=clear_state_and_prepare_reload
    )
    
    # --- 3. Controles Dinámicos (Solo si hay datos) ---
    # 'if df_loaded': Solo muestra los filtros si 'df_staging' no es None.
    if df_loaded:
        
        # --- 3a. Creación de Filtros ---
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        # 'lista_columnas_ui': Añade una opción vacía al inicio de las columnas traducidas.
        lista_columnas_ui = [""] + todas_las_columnas_ui

        # 'st.sidebar.form': Agrupa los widgets de filtro.
        with st.sidebar.form(key='form_filtro'):
            # 'columna_seleccionada_ui': Dropdown para seleccionar la columna a filtrar.
            columna_seleccionada_ui = st.selectbox(
                get_text(lang, 'column_select'),
                options=lista_columnas_ui,
                key='filter_col_select'
            )
            
            # 'col_estado_traducida': Obtiene el nombre traducido de "Row Status".
            col_estado_traducida = translate_column(lang, "Row Status")
            # 'placeholder_default'/'help_default': Textos de ayuda estándar.
            placeholder_default = get_text(lang, 'search_text_placeholder_default')
            help_default = get_text(lang, 'search_text_help_default')
            
            # 'if columna_seleccionada_ui == ...': Lógica para cambiar el placeholder
            # si se selecciona la columna "Estado Fila".
            if columna_seleccionada_ui == col_estado_traducida:
                placeholder_text = get_text(lang, 'search_text_placeholder_status')
                help_text = get_text(lang, 'search_text_help_status')
            else:
                placeholder_text = placeholder_default
                help_text = help_default

            # 'valor_a_buscar': Campo de texto para el valor del filtro.
            valor_a_buscar = st.text_input(
                get_text(lang, 'search_text'),
                key='filter_val_input',
                placeholder=placeholder_text,
                help=help_text
            )
            
            # 'submitted': Botón de envío del formulario.
            submitted = st.form_submit_button(
                get_text(lang, 'add_filter_button'), 
                key='add_filter_btn'
            )

            # 'if submitted': Lógica que se ejecuta al presionar el botón.
            if submitted:
                # 'col_val'/'val_val': Obtiene los valores de los widgets.
                col_val = st.session_state.filter_col_select
                val_val = st.session_state.filter_val_input

                # 'if col_val and val_val': Si ambos campos están llenos.
                if col_val and val_val:
                    # 'columna_en_filtro': Traduce la columna de UI (ES) a EN.
                    columna_en_filtro = col_map_es_to_en.get(col_val, col_val)
                    # 'nuevo_filtro': Crea el diccionario del filtro.
                    nuevo_filtro = {"columna": columna_en_filtro, "valor": val_val}
                    
                    # 'if nuevo_filtro not in ...': Evita filtros duplicados.
                    if nuevo_filtro not in st.session_state.filtros_activos:
                        # 'st.session_state.filtros_activos.append': Añade el filtro a la lista.
                        st.session_state.filtros_activos.append(nuevo_filtro)
                        # 'st.rerun()': Recarga la página para aplicar el filtro.
                        st.rerun()
                else:
                    # 'st.sidebar.warning': Muestra advertencia si faltan datos.
                    st.sidebar.warning(get_text(lang, 'warning_no_filter'))
        
        # --- 3b. Selector de Columnas Visibles ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")
        
        # 'if st.session_state.columnas_visibles is None': Inicializa si es la primera vez.
        if st.session_state.columnas_visibles is None:
             st.session_state.columnas_visibles = todas_las_columnas_en

        def callback_toggle_cols():
            """Activa o desactiva todas las columnas visibles."""
            # 'if len(...)': Comprueba si están todas seleccionadas o no.
            if len(st.session_state.columnas_visibles) < len(todas_las_columnas_en):
                # 'st.session_state.columnas_visibles': Asigna la lista completa (EN).
                st.session_state.columnas_visibles = todas_las_columnas_en
            else:
                # 'st.session_state.columnas_visibles': Asigna una lista vacía.
                st.session_state.columnas_visibles = []
            
            # 'st.session_state.visible_cols_multiselect': Actualiza el widget
            # (con valores traducidos a UI) para reflejar el cambio.
            st.session_state.visible_cols_multiselect = [
                translate_column(lang, col) for col in st.session_state.columnas_visibles
            ]

        def callback_update_cols_from_multiselect():
            """
            Actualiza la lista de columnas visibles basado en la selección del
            multiselect, PERO preservando el orden original del archivo.
            """
            # 'columnas_seleccionadas_ui': Obtiene la lista de UI (ES) del widget.
            columnas_seleccionadas_ui = st.session_state.visible_cols_multiselect
            
            # 'columnas_seleccionadas_en': Re-crea la lista en Inglés (EN)
            # pero iterando sobre 'todas_las_columnas_en' (que tiene el orden original)
            # para preservar dicho orden.
            columnas_seleccionadas_en = [
                col_en for col_en in todas_las_columnas_en
                if translate_column(lang, col_en) in columnas_seleccionadas_ui
            ]
            
            # 'st.session_state.columnas_visibles': Guarda la lista ordenada (EN).
            st.session_state.columnas_visibles = columnas_seleccionadas_en

        # 'st.sidebar.button': Renderiza el botón de "Activar/Desactivar Todas".
        st.sidebar.button(
            get_text(lang, 'visible_cols_toggle_button'), 
            key="toggle_cols_btn",
            on_click=callback_toggle_cols
        )
        
        # 'defaults_ui': Prepara los valores por defecto (traducidos a UI) para el multiselect.
        defaults_ui = [translate_column(lang, col) for col in st.session_state.columnas_visibles]
        
        # 'st.sidebar.multiselect': Renderiza el selector múltiple de columnas.
        st.sidebar.multiselect(
            get_text(lang, 'visible_cols_select'),
            options=todas_las_columnas_ui, # Opciones en idioma UI
            default=defaults_ui, # Valores por defecto en idioma UI
            key='visible_cols_multiselect',
            on_change=callback_update_cols_from_multiselect 
        )
        
        # --- [INICIO] ELIMINACIÓN DE CÓDIGO OBSOLETO ---
        # Se elimina el 'st.sidebar.markdown("---")'
        # Se elimina la función 'callback_toggle_markers'
        # Se elimina el 'st.sidebar.button("toggle_priority_button")'
        # La funcionalidad de las banderas 🚩 en el índice ahora es automática
        # (manejada en gui_views.py) y no opcional.
        # --- [FIN] ELIMINACIÓN DE CÓDIGO OBSOLETO ---


    # 'return uploaded_files': Retorna los archivos para que app.py sepa si debe procesar.
    return uploaded_files