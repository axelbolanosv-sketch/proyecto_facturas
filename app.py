# app.py (VERSIÓN CON CORRECCIÓN DE "MODAL FANTASMA")
# Este archivo actúa como el "director de orquesta", coordinando
# los módulos de UI y utilidades.
#
# --- CORRECCIÓN DE BUG "MODAL FANTASMA" (Nov 2025) ---
# El problema: Si el usuario cerraba el modal de reglas usando la 'x'
# de la esquina en lugar de los botones "Guardar" o "Cancelar",
# el estado 'st.session_state.show_rules_editor' NUNCA se
# ponía en 'False'.
#
# Esto causaba que, en el siguiente 'rerun' (provocado por cualquier
# otro botón como "Guardar Borrador"), el modal reapareciera
# inesperadamente ("fantasma").
#
# La solución: Se añade 'st.session_state.show_rules_editor = False'
# INMEDIATAMENTE DESPUÉS de la llamada a 'render_rules_editor()'.
#
# Por qué funciona:
# 1. Si el modal se llama y el usuario usa "Guardar" o "Cancelar",
#    esos botones ya ponen el estado en 'False' y llaman a 'st.rerun()'.
#    La ejecución de 'render_rules_editor' se detiene, por lo que la
#    línea de 'False' en 'app.py' no se ejecuta ese ciclo.
# 2. Si el modal se llama y el usuario presiona la 'x', la función
#    'render_rules_editor' termina de ejecutarse y retorna 'None'.
#    La ejecución de 'app.py' continúa, y la siguiente línea que
#    se ejecuta es 'st.session_state.show_rules_editor = False'.
#
# Esto "congela" (resetea) el estado del modal tan pronto como
# se cierra por cualquier vía no controlada (la 'x'), asegurando
# que no vuelva a aparecer hasta que se pida manualmente.
# -----------------------------------------------------------------

import streamlit as st
import pandas as pd
from modules.filters import aplicar_filtros_dinamicos
from modules.translator import get_text, translate_column

# --- 1. Importar Módulos de GUI ---

# [INICIO] CORRECCIÓN DE IMPORTACIÓN
# Se cambió 'modules.gui_utils' por 'modules.utils'.
# El archivo 'modules/utils.py' (tu archivo número 37) contiene
# la lógica de inicialización de estado correcta (incluyendo 'priority_rules').
# El archivo 'modules/gui_utils.py' (tu archivo 38) es una versión
# antigua que no debe usarse.
from modules.utils import (
    initialize_session_state,
    load_custom_css,
    load_and_process_files,
    clear_state_and_prepare_reload
)
# [FIN] CORRECCIÓN DE IMPORTACIÓN

from modules.gui_sidebar import render_sidebar
from modules.gui_views import (
    render_active_filters,
    render_kpi_dashboard,
    render_detailed_view,
    render_grouped_view
)
from modules.gui_rules_editor import render_rules_editor

import streamlit_hotkeys as hotkeys

# --- 2. Configuración Inicial ---
# (Línea de documentación interna)
# Llama a la función de 'utils.py' que inicializa todo en st.session_state
initialize_session_state()  # Esta ahora es la función correcta de utils.py
lang = st.session_state.language
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)
load_custom_css()

# --- 3. Hotkeys (Sin Cambios) ---
# (Línea de documentación interna)
# Activa los atajos de teclado globales para la aplicación
hotkeys.activate([
    hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"),
    hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
    hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
    hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+Z)"),
],
    key='main_hotkeys'
)

# --- 4. Títulos y Lógica de Columnas (Sin Cambios) ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))

# (Línea de documentación interna)
# Inicializa variables de mapeo de columnas
todas_las_columnas_ui = None
col_map_ui_to_en = None
todas_las_columnas_en = [] # Empezar con lista vacía
df_staging_copy = None

# (Línea de documentación interna)
# Si el DataFrame principal (staging) existe, crea los mapeos de traducción
if st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    todas_las_columnas_en = list(df_staging_copy.columns)
    col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
    todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]

# --- [INICIO] MODIFICACIÓN: Renderizar el Editor de Reglas ---
# (Línea de documentación interna)
# Comprueba el estado 'show_rules_editor' al inicio de cada script run
if st.session_state.get('show_rules_editor', False):
    # (Línea de documentación interna)
    # Si es True, llama a la función @st.dialog para mostrar el modal
    render_rules_editor(
        all_columns_en=todas_las_columnas_en,
        autocomplete_options=st.session_state.get('autocomplete_options', {})
    )
    
    # --- [INICIO] CORRECCIÓN DE BUG "GHOST MODAL" ---
    # Esta es la línea clave de la corrección.
    # Se ejecuta *después* de que 'render_rules_editor' retorna.
    # Si el usuario cerró el modal con la 'x', la función retorna
    # y esta línea "congela" (resetea) el estado a 'False',
    # previniendo que el modal reaparezca en el siguiente rerun.
    st.session_state.show_rules_editor = False
    # --- [FIN] CORRECCIÓN DE BUG "GHOST MODAL" ---

# --- 5. Renderizar Barra Lateral ---
# (Sin cambios)
# (Línea de documentación interna)
# Llama a la función que dibuja toda la barra lateral
uploaded_files = render_sidebar(
    lang,
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_ui_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos (Excel) ---
# (Sin cambios)
# (Línea de documentación interna)
# Si se cargaron archivos Y el DataFrame de staging está vacío
if uploaded_files and st.session_state.df_staging is None:
    # (Línea de documentación interna)
    # Llama a la función de procesamiento en 'utils.py'
    load_and_process_files(uploaded_files, lang)
    # (Línea de documentación interna)
    # Recarga la app para mostrar los datos procesados
    st.rerun()

# --- 7. Lógica Principal (Renderizado de Página) ---
# (Sin cambios)
# (Línea de documentación interna)
# Esta lógica solo se ejecuta si un DataFrame está cargado
if df_staging_copy is None and st.session_state.df_staging is not None:
    # (Línea de documentación interna)
    # (Doble chequeo por si el primer bloque if no se ejecutó)
    df_staging_copy = st.session_state.df_staging.copy()
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
        todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]


if df_staging_copy is not None:
    try:
        # (Línea de documentación interna)
        # Renderiza la sección "Filtros Activos"
        render_active_filters(lang)

        # (Línea de documentación interna)
        # Aplica los filtros del estado de sesión al DataFrame
        resultado_df = aplicar_filtros_dinamicos(
            df_staging_copy,
            st.session_state.filtros_activos
        )

        # (Línea de documentación interna)
        # Renderiza los KPIs (Monto Total, etc.)
        render_kpi_dashboard(lang, resultado_df)

        st.markdown("---")

        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")

        # (Línea de documentación interna)
        # Selector de Vista (Detallada vs. Agrupada)
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )

        if view_type == get_text(lang, 'view_type_detailed'):

            # --- LÓGICA DE ORDENAMIENTO (Sin Cambios) ---
            # (Línea de documentación interna)
            # Mapeo de prioridades a números para ordenar
            priority_map = {
                "🚩 Maxima Prioridad": 4,
                "Maxima Prioridad": 4,
                "Alta": 3,
                "Media": 2,
                "Minima": 1,
            }
            op_default = "Default (Sin Orden)"
            op_desc = "🔼 Maxima a Minima"
            op_asc = "🔽 Minima a Maxima"
            radio_options = [op_default, op_desc, op_asc]

            current_sort_val = st.session_state.get('priority_sort_order', None)

            # (Línea de documentación interna)
            # Determina el índice del radio button basado en el estado guardado
            if current_sort_val == 'DESC':
                current_index = 1
            elif current_sort_val == 'ASC':
                current_index = 2
            else:
                current_index = 0

            selected_option = st.radio(
                "Ordenar por:",
                options=radio_options,
                index=current_index,
                horizontal=True,
                key='priority_sort_radio'
            )

            st.markdown("---")

            # (Línea de documentación interna)
            # Actualiza el estado de ordenamiento basado en la selección
            new_sort_val = None
            if selected_option == op_desc:
                new_sort_val = 'DESC'
            elif selected_option == op_asc:
                new_sort_val = 'ASC'

            st.session_state.priority_sort_order = new_sort_val

            age_col_exists = 'Invoice Date Age' in resultado_df.columns

            # (Línea de documentación interna)
            # Si se seleccionó un orden, aplica el sort al DataFrame
            if new_sort_val is not None and 'Priority' in resultado_df.columns:
                try:
                    ascending_flag_priority = (new_sort_val == 'ASC')
                    # (Línea de documentación interna)
                    # Crea una columna temporal de ordenamiento
                    resultado_df['_sort_key'] = resultado_df['Priority'].map(priority_map).fillna(0)

                    sort_by_cols = ['_sort_key']
                    sort_ascending_flags = [ascending_flag_priority]

                    # (Línea de documentación interna)
                    # Añade Antigüedad como segundo criterio de orden
                    if age_col_exists:
                        sort_by_cols.append('Invoice Date Age')
                        sort_ascending_flags.append(False) # Siempre descendente

                    resultado_df = resultado_df.sort_values(
                        by=sort_by_cols,
                        ascending=sort_ascending_flags,
                        kind='stable' # Mantiene el orden original si los valores son iguales
                    )

                    resultado_df = resultado_df.drop(columns=['_sort_key'])

                except Exception as e:
                    st.warning(f"No se pudo aplicar el ordenamiento por prioridad y antigüedad: {e}")

            # --- Renderizado de Vista (Sin Cambios) ---
            # (Línea de documentación interna)
            # Llama a la función que renderiza el 'st.data_editor'
            render_detailed_view(
                lang=lang,
                resultado_df_filtrado=resultado_df,
                df_master_copy=df_staging_copy,
                col_map_ui_to_en=col_map_ui_to_en,
                todas_las_columnas_en=todas_las_columnas_en
            )

        else: # (Si la vista es Agrupada)
            # (Línea de documentación interna)
            # Llama a la función que renderiza la vista de 'groupby'
            render_grouped_view(
                lang,
                resultado_df,
                col_map_ui_to_en,
                todas_las_columnas_en
            )

    except Exception as e:
        # (Línea de documentación interna)
        # Captura de error general para evitar que la app se rompa
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e)
        clear_state_and_prepare_reload() # Limpia todo
        st.rerun()

else:
    # (Lógica 'else' sin cambios)
    # (Línea de documentación interna)
    # Pantalla de bienvenida si no hay archivos cargados
    if not uploaded_files:
        st.info(get_text(lang, 'info_upload'))

    # (Línea de documentación interna)
    # Limpieza de estado por si acaso
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None