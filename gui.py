# gui.py (Versión Corregida - Solución de Unificación de Estado + Fix de CSS)
#
# OBJETIVO DE ESTA VERSIÓN:
# 1. (CRÍTICO) Arreglar el bug de "Descargar" que no guardaba los cambios.
#    - Solución: Volver al modo "no controlado" (sin 'key=' ni 'on_change=').
#      El estado se guarda en CADA acción, lo que arregla la descarga.
# 2. (Visual) Arreglar el estilo CSS de los botones de descarga.
#    - Solución: Añadir reglas CSS explícitas.
# 3. (Visual) Arreglar las etiquetas de los botones (que mostraban código).
#    - Solución: Usar las claves nuevas (ver translator.py).

import streamlit as st
import pandas as pd
import io
from modules.filters import aplicar_filtros_dinamicos
from modules.translator import get_text, translate_column

# --- 1. Inicializar el 'Session State' ---
if 'filtros_activos' not in st.session_state:
    st.session_state.filtros_activos = []
if 'df_original' not in st.session_state:
    st.session_state.df_original = None
if 'language' not in st.session_state:
    st.session_state.language = 'es'
if 'columnas_visibles' not in st.session_state:
    st.session_state.columnas_visibles = None 
if 'editor_state' not in st.session_state:
    st.session_state.editor_state = None
if 'current_view_hash' not in st.session_state:
    st.session_state.current_view_hash = None

# --- 2. Configuración de la Página ---
st.set_page_config(
    layout="wide",
    page_title=get_text(st.session_state.language, 'title')
)

# --- 3. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """ Carga CSS personalizado y oculta spinner """
    st.markdown(
        """
        <style>
        /* ... (CSS principal) ... */
        :root {
            --color-primario-azul: #004A99;
            --color-primario-rojo: #E30613;
            --color-primario-rojo-hover: #C0000A;
            --color-fondo: #F0F4F8;
            --color-fondo-tarjeta: #FFFFFF;
            --color-texto-principal: #0A1729;
            --color-texto-secundario: #5A6D;
            --color-borde: #D0D9E3;
        }
        .stApp { background-color: var(--color-fondo); color: var(--color-texto-principal); }
        [data-testid="stSidebar"] { background-color: var(--color-fondo-tarjeta); border-right: 1px solid var(--color-borde); box-shadow: 2px 0px 10px rgba(0,0,0,0.05); }
        .stApp h1 { color: var(--color-primario-azul); font-weight: 800; }
        .stApp h2 { color: var(--color-primario-azul); border-bottom: 2px solid var(--color-borde); padding-bottom: 5px; }
        .stApp h3, [data_testid="stSidebar"] h3 { color: var(--color-texto-principal); font-weight: 600; }
        [data-testid="stSidebar"] h2 { color: var(--color-primario-azul); border-bottom: none; }
        .stButton > button { background-color: var(--color-primario-rojo); color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: 600; transition: 0.2s ease; cursor: pointer; }
        .stButton > button:hover { background-color: var(--color-primario-rojo-hover); color: white; }
        .stButton > button:focus { box-shadow: 0 0 0 3px rgba(227, 6, 19, 0.4); }
        
        .stButton[key*="quitar_"] > button {
            background-color: #e0eaf3;
            color: #004A99;
            padding: 3px 10px;
            border-radius: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
            display: inline-block;
            font-size: 0.9em;
            border: 1px solid #c0d3e8;
            font-weight: 400;
        }
        .stButton[key*="quitar_"] > button:hover {
            background-color: #c0d3e8;
            color: #004A99;
            border-color: #004A99;
        }

        .stButton[key*="limpiar_"] > button { background-color: transparent; color: var(--color-primario-rojo); border: 1px solid var(--color-primario-rojo); }
        .stButton[key*="limpiar_"] > button:hover { background-color: rgba(227, 6, 19, 0.05); color: var(--color-primario-rojo-hover); }
        .stTextInput > div > div > input, .stSelectbox > div > div, .stFileUploader > div { border: 1px solid var(--color-borde); background-color: var(--color-fondo-tarjeta); border-radius: 5px; }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div:focus-within { border-color: var(--color-primario-azul); box-shadow: 0 0 0 2px rgba(0, 74, 153, 0.3); }
        [data-testid="stVerticalBlock"]:has(>[data-testid="stVerticalBlockBorderWrapper"] [key*="quitar_"]) { 
            background-color: transparent;
            border-radius: 0;
            padding: 0;
            box-shadow: none;
            border: none; 
        }
        
        [data-testid="stDataFrame"] { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: none; border-radius: 8px; }
        [data-testid="stDataEditor"] { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: none; border-radius: 8px; } 
        
        [data-testid="stDataFrame"] .col-header { background-color: var(--color-primario-azul); color: white; font-weight: 600; }
        .stDataEditor .col-header { background-color: var(--color-primario-azul); color: white; font-weight: 600; }
        
        .stAlert[data-testid="stInfo"] { background-color: var(--color-fondo-tarjeta); border: 1px dashed var(--color-borde); color: var(--color-texto-secundario); border-radius: 8px; }
        
        /* ############################################################### */
        /* ############# INICIO DE LA SOLUCIÓN (CSS Botones) ############# */
        /* ############################################################### */
        
        /* Regla explícita para forzar el estilo rojo en los botones de descarga */
        .stButton[key*="download_excel"] > button {
            background-color: var(--color-primario-rojo);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
            font-weight: 600;
            transition: 0.2s ease;
            cursor: pointer;
        }
        .stButton[key*="download_excel"] > button:hover {
            background-color: var(--color-primario-rojo-hover);
            color: white;
        }
        
        /* ############################################################### */
        /* ############# FIN DE LA SOLUCIÓN (CSS Botones) ################ */
        /* ############################################################### */

        .stButton[key*="toggle_cols"] > button { background-color: transparent; color: var(--color-primario-azul); border: 1px solid var(--color-primario-azul); }
        .stButton[key*="toggle_cols"] > button:hover { background-color: rgba(0, 74, 153, 0.05); }
        [data-testid="stMetricHelpIcon"] { cursor: help; }
        [data-testid="stStatusWidget"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 4. FUNCIÓN AUXILIAR: Convertir a Excel ---
@st.cache_data
def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# --- 5. Cargar el CSS ---
load_custom_css()

# --- 6. Barra Lateral (Continuación) ---
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

lang = st.session_state.language
st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")

def clear_state_and_prepare_reload():
    st.session_state.df_original = None
    st.session_state.filtros_activos = []
    st.session_state.columnas_visibles = None
    st.session_state.editor_state = None 
    st.session_state.current_view_hash = None

uploader_label_es = get_text('es', 'uploader_label')
uploader_label_en = get_text('en', 'uploader_label')
static_uploader_label = f"{uploader_label_es} / {uploader_label_en}"

uploaded_file = st.sidebar.file_uploader(
    static_uploader_label,
    type=["xlsx"],
    key="main_uploader",
    accept_multiple_files=True,
    on_change=clear_state_and_prepare_reload
)


# --- 7. Títulos Principales ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))

# --- 8. LÓGICA PRINCIPAL (REFACTORIZADA) ---

# --- PASO 1: Cargar el DF en memoria si es necesario ---
if uploaded_file and st.session_state.df_original is None:
    try:
        lista_de_dataframes = []
        files_to_process = uploaded_file if isinstance(uploaded_file, list) else [uploaded_file]
        
        for file in files_to_process:
            with st.spinner(f"Cargando {file.name}..."):
                df = pd.read_excel(file, engine="openpyxl", header=0)
            lista_de_dataframes.append(df)
        
        with st.spinner("Combinando y limpiando archivos..."):
            df_original = pd.concat(lista_de_dataframes, ignore_index=True)
            df_original.columns = [col.strip() for col in df_original.columns]

            for col in df_original.columns:
                if 'Total' in col or 'Amount' in col or 'Age' in col or 'ID' in col or 'Number' in col:
                    df_original[col] = pd.to_numeric(df_original[col], errors='coerce')
                    df_original[col] = df_original[col].fillna(0)
                elif 'Date' in col:
                    df_original[col] = pd.to_datetime(df_original[col], errors='coerce')
                    df_original[col] = df_original[col].fillna("").astype(str)
                    df_original[col] = df_original[col].replace('NaT', '')
                else:
                    df_original[col] = df_original[col].fillna("").astype(str)
            
            st.session_state.df_original = df_original
            st.session_state.columnas_visibles = list(df_original.columns)

    except Exception as e:
        st.error(get_text(lang, 'error_critical').format(e=e))
        st.warning(get_text(lang, 'error_corrupt'))
        st.session_state.df_original = None
        st.session_state.columnas_visibles = None
        st.session_state.filtros_activos = []


# --- PASO 2: Lógica de la Aplicación (Solo si hay un DF cargado) ---
if st.session_state.df_original is not None:
    try:
        df_original = st.session_state.df_original.copy()
        
        todas_las_columnas_en = list(df_original.columns)
        col_map_es_to_en = {translate_column('es', col): col for col in todas_las_columnas_en}
        col_map_en_to_es = {col: es for es, col in col_map_es_to_en.items()}
        todas_las_columnas_ui = sorted([translate_column(lang, col) for col in todas_las_columnas_en])

        # --- Interfaz de Creación de Filtros (Sidebar) ---
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
        

        # --- Selector de Columnas Visibles (Sidebar) con Callbacks ---
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

        # --- Mostrar Filtros Activos (Main) ---
        st.markdown(f"## {get_text(lang, 'active_filters_header')}")
        if not st.session_state.filtros_activos:
            st.info(get_text(lang, 'no_filters_applied'))
        else:
            filtros_a_eliminar = -1
            cols_filtros = st.columns(max(1, len(st.session_state.filtros_activos))) 
            
            for i, filtro in enumerate(st.session_state.filtros_activos):
                 with cols_filtros[i]:
                    col_ui = translate_column(lang, filtro['columna']) 

                    label_boton = f"{col_ui}: {filtro['valor']}  ✕"

                    if st.button(label_boton, key=f"quitar_{i}", help=f"Quitar filtro {i+1}", type="primary"):
                           filtros_a_eliminar = i

            if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
                st.session_state.filtros_activos = []
                st.rerun() 
            if filtros_a_eliminar > -1:
                st.session_state.filtros_activos.pop(filtros_a_eliminar)
                st.rerun() 

        # --- Aplicar Filtros (Main) ---
        resultado_df = aplicar_filtros_dinamicos(
            df_original,
            st.session_state.filtros_activos
        )
        
        # --- Dashboard de KPIs (Main) ---
        st.markdown(f"## {get_text(lang, 'kpi_header')}")
        try:
            totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
        except KeyError:
            totales_numericos = pd.Series(dtype='float64')
            st.warning("No se encontró la columna 'Total' para los KPIs.")
        col1, col2, col3 = st.columns(3)
        col1.metric(label=get_text(lang, 'kpi_total_invoices'), value=len(resultado_df))
        col2.metric(
            label=get_text(lang, 'kpi_total_amount'), 
            value=f"${totales_numericos.sum():,.2f}",
            help=get_text(lang, 'kpi_total_amount_help')
        )
        col3.metric(
            label=get_text(lang, 'kpi_avg_amount'), 
            value=f"${totales_numericos.mean():,.2f}" if not totales_numericos.empty else "$0.00",
            help=get_text(lang, 'kpi_avg_amount_help')
        )
        
        st.markdown("---")

        # --- Selector de Vista (Detallada / Agrupada) ---
        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        view_type = st.radio(
            label=get_text(lang, 'view_type_header'),
            options=[get_text(lang, 'view_type_detailed'), get_text(lang, 'view_type_grouped')],
            horizontal=True,
            label_visibility="collapsed",
            key='view_type_radio'
        )
        
        # --- VISTA DETALLADA (EDICIÓN) ---
        if view_type == get_text(lang, 'view_type_detailed'):
            
            if not st.session_state.columnas_visibles:
                 st.warning(get_text(lang, 'visible_cols_warning'))
            else:
                columnas_a_mostrar_en = st.session_state.columnas_visibles
                columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df.columns]
                # Este es el DF de "solo filtros"
                df_vista_detallada = resultado_df[columnas_finales]
                
                df_display = df_vista_detallada.copy()
                df_display.columns = [translate_column(lang, col) for col in df_display.columns]
                
                # --- Lógica de Autorrellenado (Column Config) ---
                configuracion_columnas = {}
                columnas_autocompletar_en = [
                    "Vendor Name", "Status", "Assignee", 
                    "Operating Unit Name", "Pay Status", "Document Type"
                ]
                for col_en in columnas_autocompletar_en:
                    if col_en in df_original.columns:
                        try:
                            opciones = sorted(df_original[col_en].astype(str).unique())
                            col_ui = translate_column(lang, col_en)
                            configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                                f"{col_ui} (Autocompletar)",
                                help=get_text(lang, 'autocomplete_help'),
                                options=opciones,
                                required=False
                            )
                        except Exception as e:
                            st.warning(f"No se pudo generar autorrellenado para '{col_en}': {e}")
                
                # --- Gestión de Estado del Editor ---
                current_view_hash = hash((
                    str(st.session_state.filtros_activos),
                    tuple(st.session_state.columnas_visibles)
                ))

                if st.session_state.editor_state is None or \
                   st.session_state.current_view_hash != current_view_hash:
                    
                    st.session_state.editor_state = df_display.copy()
                    st.session_state.current_view_hash = current_view_hash
                
                def callback_add_row():
                    """
                    Añade una fila vacía al PRINCIPIO del 'editor_state'.
                    """
                    df_editado = st.session_state.editor_state
                    
                    default_values = {}
                    for col in df_editado.columns:
                        if pd.api.types.is_numeric_dtype(df_editado[col]):
                            default_values[col] = 0
                        else:
                            default_values[col] = ""

                    new_row_df = pd.DataFrame(default_values, index=[0])
                            
                    st.session_state.editor_state = pd.concat(
                        [new_row_df, df_editado], 
                        ignore_index=True
                    )
                
                # (ELIMINADO) El 'callback_sync_editor_state' ya no es necesario.

                # Layout para los botones de control
                col1_btn, col2_btn, col3_info = st.columns([0.25, 0.25, 0.5])
                
                with col1_btn:
                    st.button(
                        get_text(lang, 'add_row_button'),
                        on_click=callback_add_row,
                        use_container_width=True,
                        type="primary"
                    )

                with col2_btn:
                    if st.button(
                        get_text(lang, 'reset_changes_button'), 
                        use_container_width=True
                    ):
                        st.session_state.editor_state = df_display.copy()
                        st.session_state.current_view_hash = current_view_hash
                        st.rerun()
                
                with col3_info:
                    st.info(get_text(lang, 'editor_info_help_add_row'))
                
                # Este 'warning' es ahora MUY IMPORTANTE, ya que
                # es la única forma de mitigar el bug de "reversión de celda".
                st.warning("⚠️ **Aviso:** Para evitar perder cambios, presione 'Enter' o haga clic fuera de una celda después de editarla y antes de editar otra.")

                # ###############################################################
                # ############# INICIO DE LA SOLUCIÓN (Estado No Controlado) ###
                # ###############################################################
                
                # --- El Widget Data Editor (SOLUCIÓN) ---
                # 1. 'data' se alimenta de nuestra ÚNICA fuente de verdad.
                # 2. El 'key=' y 'on_change=' han sido ELIMINADOS.
                # 3. El valor de retorno (el DF modificado) se guarda
                #    inmediatamente de vuelta en la ÚNICA fuente de verdad.
                
                edited_df = st.data_editor(
                    st.session_state.editor_state,
                    # (key=... ELIMINADO)
                    column_config=configuracion_columnas, 
                    num_rows="dynamic",
                    width='stretch', 
                    height=600
                    # (on_change=... ELIMINADO)
                )
                
                # Este bucle es la solución.
                # El estado es AHORA el DF que acaba de retornar el widget.
                # Esto arregla el bug de descarga.
                st.session_state.editor_state = edited_df
                
                # ###############################################################
                # ############# FIN DE LA SOLUCIÓN #############################
                # ###############################################################
                
                st.markdown("---")
                
                # --- Descarga de datos EDITADOS ---
                col_map_ui_to_en = {
                    translate_column(lang, col_en): col_en 
                    for col_en in todas_las_columnas_en
                }
                
                # 'editor_state' ahora está 100% actualizado con las ediciones
                # porque lo acabamos de asignar en la línea 725.
                df_para_descargar_editado = st.session_state.editor_state.copy()
                df_para_descargar_editado.columns = [
                    col_map_ui_to_en.get(col_ui, col_ui) 
                    for col_ui in df_para_descargar_editado.columns
                ]

                excel_data_editada = to_excel(df_para_descargar_editado)
                
                st.download_button(
                    # Usamos la nueva clave del translator.py
                    label=get_text(lang, 'download_excel_manual_edits_button'), 
                    data=excel_data_editada,
                    file_name="resultado_facturas_MODIFICADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_editado" # El 'key' puede ser el que sea
                )
                
                # --- Descarga de datos FILTRADOS ---
                # 'df_vista_detallada' (definido en la línea 567)
                # sigue siendo el DF de "solo filtros", sin ediciones manuales.
                excel_data_filtrada = to_excel(df_vista_detallada)
                
                st.download_button(
                    # Usamos la nueva clave del translator.py
                    label=get_text(lang, 'download_excel_filtered_button'), 
                    data=excel_data_filtrada,
                    file_name="resultado_facturas_FILTRADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel_filtrado" # El 'key' puede ser el que sea
                )
        
        # --- VISTA AGRUPADA ---
        else:
            columnas_agrupables_en = ["Vendor Name", "Status", "Assignee", "Operating Unit Name", "Pay Status", "Document Type"]
            opciones_agrupables_ui = [translate_column(lang, col) for col in columnas_agrupables_en if col in todas_las_columnas_en]
            
            col_para_agrupar_ui = st.selectbox(
                get_text(lang, 'group_by_select'),
                options=opciones_agrupables_ui,
                key='group_by_col_select'
            )
            
            if col_para_agrupar_ui:
                col_para_agrupar_en = col_map_es_to_en.get(col_para_agrupar_ui, col_para_agrupar_ui)
                df_agrupado = resultado_df.copy()
                
                if 'Total' in df_agrupado.columns:
                    df_agrupado['Total'] = pd.to_numeric(df_agrupado['Total'], errors='coerce')
                if 'Invoice Date Age' in df_agrupado.columns:
                    df_agrupado['Invoice Date Age'] = pd.to_numeric(df_agrupado['Invoice Date Age'], errors='coerce')

                agg_operations = {'Total': ['sum', 'mean', 'min', 'max', 'count']}
                if 'Invoice Date Age' in df_agrupado.columns and pd.api.types.is_numeric_dtype(df_agrupado['Invoice Date Age']):
                    agg_operations['Invoice Date Age'] = ['mean']

                try: 
                    df_agrupado_calculado = df_agrupado.groupby(col_para_agrupar_en).agg(agg_operations)
                    col_names_grouped = [
                        get_text(lang, 'group_total_amount'), get_text(lang, 'group_avg_amount'),
                        get_text(lang, 'group_min_amount'), get_text(lang, 'group_max_amount'),
                        get_text(lang, 'group_invoice_count')
                    ]
                    if 'Invoice Date Age' in agg_operations:
                        col_names_grouped.append(get_text(lang, 'group_avg_age'))
                    df_agrupado_calculado.columns = col_names_grouped
                    
                    st.dataframe(df_agrupado_calculado.sort_values(by=get_text(lang, 'group_total_amount'), ascending=False))
                    
                    excel_data = to_excel(df_agrupado_calculado)
                    st.download_button(
                        label=get_text(lang, 'download_excel_button'), 
                        data=excel_data,
                        file_name=f"agrupado_por_{col_para_agrupar_ui}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_excel_agrupado"
                    )
                except Exception as group_error:
                    st.error(f"Error al agrupar por '{col_para_agrupar_ui}': {group_error}")
            else:
                st.info("Por favor, seleccione una columna para agrupar.")

    except Exception as e:
        st.error(f"Error inesperado en la aplicación: {e}")
        st.exception(e) 
        st.session_state.filtros_activos = []
        st.session_state.columnas_visibles = None 

else:
    # --- PASO 3: Estado Inicial (Solo si df_original es None) ---
    st.info(get_text(lang, 'info_upload'))
    if st.session_state.df_original is not None:
        st.session_state.df_original = None
    if st.session_state.filtros_activos:
        st.session_state.filtros_activos = []
    if st.session_state.columnas_visibles is not None:
        st.session_state.columnas_visibles = None