# modules/gui_utils.py (VERSIÓN CON LÓGICA DE 🚩 HOMOLOGADA y 4 NIVELES + ESTADO DE ORDEN)
# Contiene todas las funciones auxiliares para la GUI.

import streamlit as st
import pandas as pd
import io
import numpy as np 
from modules.translator import get_text

# --- 1. Inicializar el 'Session State' ---
def initialize_session_state():
    """
    Define el estado inicial de la sesión de Streamlit.
    (Esta función es llamada al inicio de app.py)
    """
    # 'if 'filtros_activos' not in st.session_state:': Comprueba si la clave existe
    if 'filtros_activos' not in st.session_state:
        # 'st.session_state.filtros_activos = []': Si no existe, la inicializa
        st.session_state.filtros_activos = []
    if 'language' not in st.session_state:
        st.session_state.language = 'es'
    if 'columnas_visibles' not in st.session_state:
        st.session_state.columnas_visibles = None 
        
    if 'columnas_visibles_estable' not in st.session_state:
        st.session_state.columnas_visibles_estable = None
        
    if 'editor_state' not in st.session_state:
        st.session_state.editor_state = None
    
    if 'current_data_hash' not in st.session_state:
        st.session_state.current_data_hash = None # Para filtros y columnas
    if 'current_lang_hash' not in st.session_state:
        st.session_state.current_lang_hash = None # Para el idioma
    
    if 'df_pristine' not in st.session_state:
        st.session_state.df_pristine = None # Archivo 0: Original
    if 'df_original' not in st.session_state:
        st.session_state.df_original = None # Archivo 1: Estable
    if 'df_staging' not in st.session_state:
        st.session_state.df_staging = None # Archivo 2: Borrador de trabajo
        
    if 'autocomplete_options' not in st.session_state:
        st.session_state.autocomplete_options = {}

    # --- [INICIO] CAMBIO: Añadir estado de ordenamiento ---
    # 'if 'priority_sort_order' not in st.session_state:':
    # Esta es la línea que soluciona el 'AttributeError'.
    # Inicializa el estado de ordenamiento personalizado.
    if 'priority_sort_order' not in st.session_state:
        # 'st.session_state.priority_sort_order = None':
        # Puede ser 'DESC' (Maxima a Minima), 'ASC' (Minima a Maxima), o None (default).
        st.session_state.priority_sort_order = None
    # --- [FIN] CAMBIO ---

# --- 2. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """
    Carga CSS personalizado en la aplicación Streamlit.
    (Incluye el resaltado rojo para 'Maxima Prioridad')
    """
    # (Esta función no tiene cambios respecto a la versión anterior)
    st.markdown(
        """
        <style>
        /* --- CSS PARA RESALTAR CELDAS VACÍAS --- */
        [data-testid="stDataEditor"] [data-kind="cell"]:has(> .glide-cell-div:empty) {
            background-color: #FFF3B3 !important; /* Amarillo pálido */
        }
        
        [data-testid="stDataEditor"] [data-kind="cell"] > .glide-cell-div > .glide-text-content[data-content="0"] {
            background-color: #FFF3B3 !important;
            color: #b0a06c; /* Color de texto más claro para el '0' */
        }

        /* --- CSS PARA RESALTAR FILA DE ALTA PRIORIDAD --- */
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="Maxima Prioridad"]) {
            background-image: linear-gradient(to right, #FFDDDD, #FFDDDD) !important;
            color: #660000 !important; /* Oscurecer el texto para legibilidad */
        }
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="🚩 Maxima Prioridad"]) {
            background-image: linear-gradient(to right, #FFDDDD, #FFDDDD) !important;
            color: #660000 !important; /* Oscurecer el texto para legibilidad */
        }
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="Maxima Prioridad"]) {
            font-weight: 800 !important;
            background-color: #FFC0C0 !important;
            color: black !important;
        }
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="🚩 Maxima Prioridad"]) {
            font-weight: 800 !important;
            background-color: #FFC0C0 !important;
            color: black !important;
        }
        /* --- [FIN] CSS --- */

        :root {
            --color-primario-azul: #004A99;
            --color-primario-rojo: #E30613;
            --color-primario-rojo-hover: #C0000A;
            --color-fondo: #F0F4F8;
            --color-fondo-tarjeta: #FFFFFF;
            --color-texto-principal: #0A1729;
            --color-texto-secundario: #5A6D;
            --color-borde: #D0D9E3;
            --color-naranja: #FFA500;
            --color-naranja-hover: #E69500;
            --color-verde: #008000; /* Verde para descargas */
            --color-verde-hover: #006400; /* Verde oscuro */
        }
        .stApp { background-color: var(--color-fondo); color: var(--color-texto-principal); }
        [data-testid="stSidebar"] { background-color: var(--color-fondo-tarjeta); border-right: 1px solid var(--color-borde); box-shadow: 2px 0px 10px rgba(0,0,0,0.05); }
        .stApp h1 { color: var(--color-primario-azul); font-weight: 800; }
        .stApp h2 { color: var(--color-primario-azul); border-bottom: 2px solid var(--color-borde); padding-bottom: 5px; }
        .stApp h3, [data_testid="stSidebar"] h3 { color: var(--color-texto-principal); font-weight: 600; }
        [data-testid="stSidebar"] h2 { color: var(--color-primario-azul); border-bottom: none; }
        
        /* ... (Resto de tu CSS sin cambios) ... */
        
        .stButton > button { background-color: var(--color-primario-rojo); color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: 600; transition: 0.2s ease; cursor: pointer; }
        .stButton > button:hover { background-color: var(--color-primario-rojo-hover); color: white; }
        .stButton > button:focus { box-shadow: 0 0 0 3px rgba(227, 6, 19, 0.4); }
        .stButton[key*="commit_changes"] > button { background-color: var(--color-primario-azul); }
        .stButton[key*="commit_changes"] > button:hover { background-color: #003366; }
        .stButton[key*="reset_changes_button"] > button { background-color: var(--color-naranja); color: white; }
        .stButton[key*="reset_changes_button"] > button:hover { background-color: var(--color-naranja-hover); color: white; }
        .stButton[key*="restore_pristine"] > button { background-color: transparent; color: var(--color-primario-rojo); border: 1px solid var(--color-primario-rojo); }
        .stButton[key*="restore_pristine"] > button:hover { background-color: rgba(227, 6, 19, 0.05); color: var(--color-primario-rojo-hover); }
        .stButton[key*="quitar_"] > button { background-color: #e0eaf3; color: #004A99; padding: 3px 10px; border-radius: 12px; margin-right: 5px; margin-bottom: 5px; display: inline-block; font-size: 0.9em; border: 1px solid #c0d3e8; font-weight: 400; }
        .stButton[key*="quitar_"] > button:hover { background-color: #c0d3e8; color: #004A99; border-color: #004A99; }
        .stButton[key*="limpiar_"] > button { background-color: transparent; color: var(--color-primario-rojo); border: 1px solid var(--color-primario-rojo); }
        .stButton[key*="limpiar_"] > button:hover { background-color: rgba(227, 6, 19, 0.05); color: var(--color-primario-rojo-hover); }
        .stTextInput > div > div > input, .stSelectbox > div > div, .stFileUploader > div { border: 1px solid var(--color-borde); background-color: var(--color-fondo-tarjeta); border-radius: 5px; }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div:focus-within { border-color: var(--color-primario-azul); box-shadow: 0 0 0 2px rgba(0, 74, 153, 0.3); }
        [data-testid="stVerticalBlock"]:has(>[data-testid="stVerticalBlockBorderWrapper"] [key*="quitar_"]) { background-color: transparent; border-radius: 0; padding: 0; box-shadow: none; border: none; }
        [data-testid="stDataFrame"] { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: none; border-radius: 8px; }
        [data-testid="stDataEditor"] { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: none; border-radius: 8px; } 
        [data-testid="stDataFrame"] .col-header { background-color: var(--color-primario-azul); color: white; font-weight: 600; }
        .stDataEditor .col-header { background-color: var(--color-primario-azul); color: white; font-weight: 600; }
        .stAlert[data-testid="stInfo"] { background-color: var(--color-fondo-tarjeta); border: 1px dashed var(--color-borde); color: var(--color-texto-secundario); border-radius: 8px; }
        [data-testid="stDownloadButton"] > button { background-color: var(--color-verde); color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: 600; transition: 0.2s ease; cursor: pointer; }
        [data-testid="stDownloadButton"] > button:hover { background-color: var(--color-verde-hover); color: white; }
        [data-testid="stDownloadButton"] > button:focus { box-shadow: 0 0 0 3px rgba(0, 128, 0, 0.4); }
        .stButton[key*="toggle_cols"] > button { background-color: transparent; color: var(--color-primario-azul); border: 1px solid var(--color-primario-azul); }
        .stButton[key*="toggle_cols"] > button:hover { background-color: rgba(0, 74, 153, 0.05); }
        [data-testid="stMetricHelpIcon"] { cursor: help; }
        [data-testid="stStatusWidget"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. FUNCIÓN AUXILIAR: Convertir a Excel ---
@st.cache_data
def to_excel(df: pd.DataFrame):
    """Convierte un DataFrame a un archivo Excel en memoria."""
    # (Función sin cambios)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# --- 4. FUNCIÓN DE CARGA Y PROCESAMIENTO DE DATOS ---
def load_and_process_files(uploaded_files, lang):
    """
    Toma los archivos cargados, los combina, limpia (usando vectorización), 
    guarda las 3 copias y pre-calcula las opciones de autocompletar.
    """
    # (Esta función es idéntica a la versión anterior de 4 niveles)
    try:
        lista_de_dataframes = []
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
        for file in files_to_process:
            with st.spinner(f"Cargando {file.name}..."):
                df = pd.read_excel(file, engine="openpyxl", header=0)
            lista_de_dataframes.append(df)
        
        with st.spinner("Combinando y limpiando archivos (vectorizado)..."):
            df_processed = pd.concat(lista_de_dataframes, ignore_index=True)
            
            df_processed.columns = [col.strip() for col in df_processed.columns]
            columnas_originales = list(df_processed.columns)
            
            # --- [INICIO] OPTIMIZACIÓN: LIMPIEZA VECTORIZADA ---
            
            numeric_cols = [col for col in columnas_originales if 'Total' in col or 'Amount' in col or 'Age' in col or 'ID' in col or 'Number' in col]
            date_cols = [col for col in columnas_originales if 'Date' in col and col not in numeric_cols]
            string_cols = [col for col in columnas_originales if col not in numeric_cols and col not in date_cols]

            if string_cols:
                df_processed[string_cols] = df_processed[string_cols].fillna("").astype(str)

            if numeric_cols:
                df_processed[numeric_cols] = df_processed[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

            if date_cols:
                df_processed[date_cols] = df_processed[date_cols].apply(pd.to_datetime, errors='coerce')

            df_check = df_processed.astype(str).replace('NaT', '').replace('nan', '')

            if date_cols:
                for col in date_cols:
                    df_processed[col] = df_check[col]
            
            # --- [FIN] OPTIMIZACIÓN: LIMPIEZA VECTORIZADA ---

            # --- [INICIO] LÓGICA DE PRIORIDAD (CORREGIDA Y HOMOLOGADA CON 4 NIVELES) ---
            
            if 'Pay Group' in df_processed.columns:
                
                if 'Priority' not in df_processed.columns:
                    df_processed['Priority'] = "" 
                    columnas_originales.append('Priority') 
                df_processed['Priority'] = df_processed['Priority'].astype(str)

                manual_priorities = ["Minima", "Media", "Alta"] 
                mask_manual = df_processed['Priority'].isin(manual_priorities)
                
                pay_group_searchable = df_processed['Pay Group'].astype(str).str.upper()
                high_priority_terms = ["DIST", "INTERCOMPANY", "PAYROLL", "RENTS", "SCF"] 
                low_priority_terms = ["PAYGROUP", "PAY GROUP", "GNTD"] 
                mask_high = pay_group_searchable.str.contains('|'.join(high_priority_terms), na=False)
                mask_low = pay_group_searchable.str.contains('|'.join(low_priority_terms), na=False)

                mask_excel_maxima = (df_processed['Priority'] == "Maxima Prioridad") | (df_processed['Priority'] == "🚩 Maxima Prioridad")

                conditions = [
                    mask_manual,                      
                    mask_high,                        
                    mask_excel_maxima,                
                    mask_low                          
                ]
                
                choices = [
                    df_processed['Priority'],         
                    "🚩 Maxima Prioridad",             
                    "🚩 Maxima Prioridad",             
                    "Minima"                          
                ]
                
                df_processed['Priority'] = np.select(conditions, choices, default=df_processed['Priority'])
            
            # --- [FIN] LÓGICA DE PRIORIDAD (CORREGIDA Y HOMOLOGADA) ---
            
            # --- Cálculo de 'Row Status' (basado en df_check) ---
            blank_mask = (df_check == "") | (df_check == "0")
            incomplete_rows = blank_mask.any(axis=1)
            
            df_processed['Row Status'] = np.where(
                incomplete_rows, 
                get_text(lang, 'status_incomplete'),
                get_text(lang, 'status_complete')
            )

            # --- Guardar las tres copias en el estado de la sesión ---
            st.session_state.df_pristine = df_processed.copy()
            st.session_state.df_original = df_processed.copy()
            st.session_state.df_staging = df_processed.copy()
            
            # --- Pre-calcular opciones de autocompletar ---
            autocomplete_options = {}
            columnas_autocompletar_en = [
                "Vendor Name", "Status", "Assignee", 
                "Operating Unit Name", "Pay Status", "Document Type",
                "Currency Code", "Vendor Type", "Payment Method", 
                "Priority", "Pay Group"
            ]
            
            for col_en in columnas_autocompletar_en:
                if col_en in df_processed.columns:
                    try:
                        if col_en == "Priority":
                            base_options = ["", "Minima", "Media", "Alta"]
                            custom_options = ["Maxima Prioridad", "🚩 Maxima Prioridad"]
                            actual_options = df_processed[col_en].astype(str).unique()
                            opciones = sorted(list(set(base_options + custom_options + list(actual_options))))
                        else:
                            opciones = sorted(list(df_processed[col_en].astype(str).unique()))
                        autocomplete_options[col_en] = opciones
                    except Exception:
                        autocomplete_options[col_en] = [] # Fallback
            
            st.session_state.autocomplete_options = autocomplete_options
            
            # --- Guardar estado de columnas ---
            columnas_iniciales = list(df_processed.columns)
            st.session_state.columnas_visibles = columnas_iniciales.copy()
            st.session_state.columnas_visibles_estable = columnas_iniciales.copy()

    except Exception as e:
        st.error(get_text(lang, 'error_critical').format(e=e))
        st.warning(get_text(lang, 'error_corrupt'))
        st.session_state.df_pristine = None
        st.session_state.df_original = None
        st.session_state.df_staging = None
        st.session_state.columnas_visibles = None
        st.session_state.columnas_visibles_estable = None
        st.session_state.filtros_activos = []
        st.session_state.autocomplete_options = {}

# --- 5. CALLBACK PARA LIMPIAR ESTADO ---
def clear_state_and_prepare_reload():
    """
    Resetea el estado de la sesión al cargar nuevos archivos.
    Limpia las tres copias del DataFrame.
    """
    st.session_state.filtros_activos = []
    st.session_state.columnas_visibles = None
    st.session_state.columnas_visibles_estable = None
    st.session_state.editor_state = None 
    st.session_state.current_data_hash = None
    st.session_state.current_lang_hash = None
    st.session_state.df_pristine = None
    st.session_state.df_original = None
    st.session_state.df_staging = None
    st.session_state.autocomplete_options = {}
    
    # --- [INICIO] CAMBIO: Resetear el estado de ordenamiento ---
    # 'st.session_state.priority_sort_order': Asegura que el orden se limpie
    # al cargar un nuevo archivo.
    st.session_state.priority_sort_order = None
    # --- [FIN] CAMBIO ---