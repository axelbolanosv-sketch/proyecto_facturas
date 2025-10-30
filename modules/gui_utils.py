# modules/gui_utils.py (VERSIÓN LIMPIA)
# Contiene todas las funciones auxiliares para la GUI.

import streamlit as st
import pandas as pd
import io
from modules.translator import get_text

# --- 1. Inicializar el 'Session State' ---
def initialize_session_state():
    """Define el estado inicial de la sesión."""
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

# --- 2. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """ Carga CSS personalizado y oculta spinner """
    # Esta es la parte del CSS original de tu archivo gui.py
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
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# --- 4. FUNCIÓN DE CARGA Y PROCESAMIENTO DE DATOS ---
def load_and_process_files(uploaded_files, lang):
    """
    Toma los archivos cargados, los combina, limpia y los guarda en 
    el estado de la sesión.
    """
    try:
        lista_de_dataframes = []
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
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

# --- 5. CALLBACK PARA LIMPIAR ESTADO ---
def clear_state_and_prepare_reload():
    """Resetea el estado al cargar nuevos archivos."""
    st.session_state.df_original = None
    st.session_state.filtros_activos = []
    st.session_state.columnas_visibles = None
    st.session_state.editor_state = None 
    st.session_state.current_view_hash = None