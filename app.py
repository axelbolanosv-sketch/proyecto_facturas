# app.py (VERSIÓN CON ORDENAMIENTO POR RADIO-BUTTON)
# Este archivo actúa como el "director de orquesta", coordinando
# los módulos de UI y utilidades.

import streamlit as st
import pandas as pd
# 'import json': Ya no es necesario aquí.
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
import streamlit_hotkeys as hotkeys 

# --- 2. Configuración Inicial ---
# (Se llama a initialize_session_state() PRIMERO,
#  lo que soluciona el 'AttributeError' en futuros reinicios)
initialize_session_state()
lang = st.session_state.language
st.set_page_config(
    layout="wide",
    page_title=get_text(lang, 'title')
)
load_custom_css()

# --- 3. Hotkeys (Sin Cambios) ---
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

todas_las_columnas_ui = None
col_map_ui_to_en = None
todas_las_columnas_en = None
df_staging_copy = None 

if st.session_state.df_staging is not None:
    df_staging_copy = st.session_state.df_staging.copy()
    todas_las_columnas_en = list(df_staging_copy.columns)
    col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
    todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]

# --- 5. Renderizar Barra Lateral ---
# (Sin cambios)
uploaded_files = render_sidebar(
    lang, 
    df_loaded=(st.session_state.df_staging is not None),
    todas_las_columnas_ui=todas_las_columnas_ui,
    col_map_es_to_en=col_map_ui_to_en,
    todas_las_columnas_en=todas_las_columnas_en
)

# --- 6. Lógica de Carga de Archivos (Excel) ---
# (Sin cambios)
if uploaded_files and st.session_state.df_staging is None:
    load_and_process_files(uploaded_files, lang)
    st.rerun()

# --- 7. Lógica Principal (Renderizado de Página) ---
if df_staging_copy is None and st.session_state.df_staging is not None:
    # (Lógica de 'fallback' sin cambios)
    df_staging_copy = st.session_state.df_staging.copy()
    if todas_las_columnas_en is None:
        todas_las_columnas_en = list(df_staging_copy.columns)
        col_map_ui_to_en = {translate_column(lang, col): col for col in todas_las_columnas_en}
        todas_las_columnas_ui = [translate_column(lang, col) for col in todas_las_columnas_en]


if df_staging_copy is not None:
    try:
        # (Renderizado de filtros activos y KPIs sin cambios)
        render_active_filters(lang)

        resultado_df = aplicar_filtros_dinamicos(
            df_staging_copy,
            st.session_state.filtros_activos
        )
        
        render_kpi_dashboard(lang, resultado_df)
        
        st.markdown("---")

        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        
        # (Radio button de 'view_type' sin cambios)
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )
        
        if view_type == get_text(lang, 'view_type_detailed'):
            
            # --- [INICIO] NUEVA LÓGICA DE ORDENAMIENTO (CON RADIO) ---
            
            # 1. Definir el mapa de ordenamiento lógico
            #    Se asignan valores numéricos a las prioridades.
            priority_map = {
                "🚩 Maxima Prioridad": 4, # (Valor más alto)
                "Maxima Prioridad": 4, # (Por si el usuario la escribe sin bandera)
                "Alta": 3,
                "Media": 2,
                "Minima": 1,
                # (Cualquier otra cosa, como "", será 0 por el .fillna(0) más abajo)
            }
            
            # 2. Definir las opciones del radio button
            op_default = "Default (Sin Orden)"
            op_desc = "🔼 Maxima a Minima"
            op_asc = "🔽 Minima a Maxima"
            radio_options = [op_default, op_desc, op_asc]
            
            # 3. Mapear el estado actual a la opción del radio
            #    'st.session_state.get()': Usamos .get() para leer de forma segura.
            current_sort_val = st.session_state.get('priority_sort_order', None)
            
            if current_sort_val == 'DESC':
                current_index = 1 # 'op_desc'
            elif current_sort_val == 'ASC':
                current_index = 2 # 'op_asc'
            else:
                current_index = 0 # 'op_default'
            
            # 4. Renderizar el st.radio
            #    Este widget reemplaza los 3 botones anteriores.
            selected_option = st.radio(
                "Ordenar por Prioridad:",
                options=radio_options,
                index=current_index,
                horizontal=True,
                key='priority_sort_radio'
            )
            
            st.markdown("---") # Separador visual

            # 5. Convertir la opción seleccionada a un valor de estado
            new_sort_val = None
            if selected_option == op_desc:
                new_sort_val = 'DESC'
            elif selected_option == op_asc:
                new_sort_val = 'ASC'
            # (Si es 'op_default', new_sort_val permanece como None)
            
            # 6. Guardar el nuevo estado en la sesión
            #    Esto persiste la elección del usuario.
            st.session_state.priority_sort_order = new_sort_val

            # 7. Aplicar el ordenamiento al DataFrame (si se seleccionó)
            if new_sort_val is not None and 'Priority' in resultado_df.columns:
                try:
                    # 'ascending_flag': Determina la dirección (ASC o DESC)
                    ascending_flag = (new_sort_val == 'ASC')
                    
                    # '_sort_key': Crea una columna temporal usando el mapa
                    resultado_df['_sort_key'] = resultado_df['Priority'].map(priority_map).fillna(0)
                    
                    # 'sort_values': Ordena el DataFrame por la clave numérica
                    resultado_df = resultado_df.sort_values(
                        by='_sort_key', 
                        ascending=ascending_flag, 
                        kind='stable' # 'kind='stable'': Mantiene el orden relativo de filas con la misma prioridad
                    )
                    
                    # 'drop': Elimina la columna temporal
                    resultado_df = resultado_df.drop(columns=['_sort_key'])

                except Exception as e:
                    st.warning(f"No se pudo aplicar el ordenamiento por prioridad: {e}")

            # --- [FIN] NUEVA LÓGICA DE ORDENAMIENTO (CON RADIO) ---

            # 8. Renderizar la vista
            # (El 'resultado_df' que se pasa aquí ahora está ordenado
            #  según la selección del radio button)
            render_detailed_view(
                lang=lang, 
                resultado_df_filtrado=resultado_df, # <--- Este DF ahora está ordenado
                df_master_copy=df_staging_copy, 
                col_map_ui_to_en=col_map_ui_to_en,
                todas_las_columnas_en=todas_las_columnas_en
            )
            
        else: # (Si la vista es Agrupada)
            render_grouped_view(
                lang, 
                resultado_df, 
                col_map_ui_to_en,
                todas_las_columnas_en
            )
    
    except Exception as e:
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        clear_state_and_prepare_reload()
        st.rerun()

else:
    # (Lógica 'else' sin cambios)
    if not uploaded_files: 
        st.info(get_text(lang, 'info_upload'))
    
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None