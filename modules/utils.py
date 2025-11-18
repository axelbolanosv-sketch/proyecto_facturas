# modules/utils.py
import streamlit as st
import pandas as pd
import io
import numpy as np 
from modules.translator import get_text
# Importar solo lo necesario del motor de reglas
from modules.rules_service import apply_priority_rules, get_default_rules

def initialize_session_state():
    """Define el estado inicial de la sesión."""
    if 'filtros_activos' not in st.session_state: st.session_state.filtros_activos = []
    if 'language' not in st.session_state: st.session_state.language = 'es'
    if 'columnas_visibles' not in st.session_state: st.session_state.columnas_visibles = None 
    if 'columnas_visibles_estable' not in st.session_state: st.session_state.columnas_visibles_estable = None
    if 'editor_state' not in st.session_state: st.session_state.editor_state = None
    if 'current_data_hash' not in st.session_state: st.session_state.current_data_hash = None
    if 'current_lang_hash' not in st.session_state: st.session_state.current_lang_hash = None
    if 'df_pristine' not in st.session_state: st.session_state.df_pristine = None
    if 'df_original' not in st.session_state: st.session_state.df_original = None
    if 'df_staging' not in st.session_state: st.session_state.df_staging = None
    if 'autocomplete_options' not in st.session_state: st.session_state.autocomplete_options = {}
    if 'priority_sort_order' not in st.session_state: st.session_state.priority_sort_order = None
    
    if 'username' not in st.session_state: st.session_state.username = None
    if 'audit_log' not in st.session_state: st.session_state.audit_log = []
        
    if 'priority_rules' not in st.session_state: st.session_state.priority_rules = get_default_rules()
    if 'show_rules_editor' not in st.session_state: st.session_state.show_rules_editor = False
    if 'config_file_processed' not in st.session_state: st.session_state.config_file_processed = False

def load_custom_css():
    st.markdown("""
        <style>
        /* --- CSS GLOBAL MEJORADO PARA VISIBILIDAD --- */
        
        /* Inputs de Texto y Selectbox: Fondo blanco y bordes visibles */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #888888 !important;
            border-radius: 5px !important;
            font-weight: 500 !important;
        }
        
        /* Focus: Borde azul fuerte al seleccionar */
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
            border-color: #004A99 !important;
            box-shadow: 0 0 0 2px rgba(0, 74, 153, 0.2) !important;
        }

        /* Etiquetas (Labels): Texto oscuro y negrita */
        .stMarkdown label, .stTextInput label, .stSelectbox label {
            color: #0A1729 !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }

        /* --- ESTILOS DE TABLA --- */
        [data-testid="stDataEditor"] [data-kind="cell"]:has(> .glide-cell-div:empty) { background-color: #FFF3B3 !important; }
        [data-testid="stDataEditor"] [data-kind="cell"] > .glide-cell-div > .glide-text-content[data-content="0"] { background-color: #FFF3B3 !important; color: #b0a06c; }
        
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="Maxima Prioridad"]), 
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="🚩 Maxima Prioridad"]) { 
            background-image: linear-gradient(to right, #FFDDDD, #FFDDDD) !important; 
            color: #660000 !important; 
        }
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="Maxima Prioridad"]), 
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="🚩 Maxima Prioridad"]) { 
            font-weight: 800 !important; 
            background-color: #FFC0C0 !important; 
            color: black !important; 
        }
        
        /* --- COLORES GENERALES --- */
        :root { --color-primario-azul: #004A99; --color-primario-rojo: #E30613; --color-fondo: #F0F4F8; --color-fondo-tarjeta: #FFFFFF; --color-texto-principal: #0A1729; --color-borde: #D0D9E3; --color-verde: #008000; }
        .stApp { background-color: var(--color-fondo); color: var(--color-texto-principal); }
        [data-testid="stSidebar"] { background-color: var(--color-fondo-tarjeta); border-right: 1px solid var(--color-borde); }
        .stApp h1, .stApp h2, [data-testid="stSidebar"] h2 { color: var(--color-primario-azul); }
        
        .stButton > button { background-color: var(--color-primario-rojo); color: white; border-radius: 5px; font-weight: 600; border: none;}
        .stButton[key*="commit_changes"] > button { background-color: var(--color-primario-azul); }
        .stButton[key*="reset_changes_button"] > button { background-color: #FFA500; }
        [data-testid="stDownloadButton"] > button { background-color: var(--color-verde); color: white; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data
def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

def load_and_process_files(uploaded_files, lang):
    try:
        lista_de_dataframes = []
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
        for file in files_to_process:
            with st.spinner(f"Cargando {file.name}..."):
                df = pd.read_excel(file, engine="openpyxl", header=0)
            lista_de_dataframes.append(df)
        
        with st.spinner("Procesando archivos..."):
            df_processed = pd.concat(lista_de_dataframes, ignore_index=True)
            df_processed.columns = [col.strip() for col in df_processed.columns]
            
            cols_orig = list(df_processed.columns)
            num_cols = [c for c in cols_orig if any(x in c for x in ['Total', 'Amount', 'Age', 'ID', 'Number'])]
            date_cols = [c for c in cols_orig if 'Date' in c and c not in num_cols]
            str_cols = [c for c in cols_orig if c not in num_cols and c not in date_cols]
            
            if str_cols: df_processed[str_cols] = df_processed[str_cols].fillna("").astype(str)
            if num_cols: df_processed[num_cols] = df_processed[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            if date_cols: df_processed[date_cols] = df_processed[date_cols].apply(pd.to_datetime, errors='coerce')
            
            df_check = df_processed.astype(str).replace('NaT', '').replace('nan', '')
            if date_cols: 
                for c in date_cols: df_processed[c] = df_check[c]

            if 'Priority' not in df_processed.columns: df_processed['Priority'] = ""
            df_processed['Priority'] = df_processed['Priority'].astype(str)
            if 'Priority_Reason' not in df_processed.columns: df_processed['Priority_Reason'] = "Sin Regla Asignada"
            
            df_processed = apply_priority_rules(df_processed)
            
            cols_check = [c for c in df_check.columns if c not in ['Row Status', 'Priority_Reason']]
            blank = (df_check[cols_check] == "") | (df_check[cols_check] == "0")
            df_processed['Row Status'] = np.where(blank.any(axis=1), get_text(lang, 'status_incomplete'), get_text(lang, 'status_complete'))

            st.session_state.df_pristine = df_processed.copy()
            st.session_state.df_original = df_processed.copy()
            st.session_state.df_staging = df_processed.copy()
            
            # Autocompletado
            autocomplete_options = {}
            for col in ["Vendor Name", "Status", "Assignee", "Priority", "Pay Group", "Operating Unit Name", "Document Type"]:
                if col in df_processed.columns:
                    vals = sorted(list(df_processed[col].astype(str).unique()))
                    if col == "Priority": vals = sorted(list(set(vals + ["🚩 Maxima Prioridad", "Minima", "Media", "Alta"])))
                    autocomplete_options[col] = vals
            st.session_state.autocomplete_options = autocomplete_options
            
            st.session_state.columnas_visibles = list(df_processed.columns)
            st.session_state.columnas_visibles_estable = list(df_processed.columns)

    except Exception as e:
        st.error(f"Error crítico: {e}")
        st.session_state.df_staging = None

def clear_state_and_prepare_reload():
    st.session_state.filtros_activos = []
    st.session_state.columnas_visibles = None
    st.session_state.editor_state = None 
    st.session_state.current_data_hash = None
    st.session_state.df_staging = None
    st.session_state.audit_log = [] 
    st.session_state.config_file_processed = False