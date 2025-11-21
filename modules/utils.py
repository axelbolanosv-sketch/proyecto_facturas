# modules/gui_utils.py
# VERSIÓN REPARADA:
# 1. Inicialización correcta de 'username' y 'audit_log' (Soluciona AttributeError)
# 2. Limpieza de texto suavizada (Soluciona celdas vacías en 'Asignado a')
# 3. Inclusión de Estados de Negocio Estandarizados

import streamlit as st
import pandas as pd
import io
import numpy as np 
from modules.translator import get_text
from modules.rules_service import get_default_rules # Necesario para inicializar reglas

# --- 1. Inicializar el 'Session State' ---
def initialize_session_state():
    """
    Define e inicializa el estado de la sesión de Streamlit.
    Se asegura de que todas las variables clave existan antes de renderizar la UI.
    """
    # --- Variables de Configuración General ---
    if 'filtros_activos' not in st.session_state:
        st.session_state.filtros_activos = []
    if 'language' not in st.session_state:
        st.session_state.language = 'es'
    if 'columnas_visibles' not in st.session_state:
        st.session_state.columnas_visibles = None 
    if 'columnas_visibles_estable' not in st.session_state:
        st.session_state.columnas_visibles_estable = None
        
    # --- Variables de Edición y Datos ---
    if 'editor_state' not in st.session_state:
        st.session_state.editor_state = None
    if 'current_data_hash' not in st.session_state:
        st.session_state.current_data_hash = None 
    if 'current_lang_hash' not in st.session_state:
        st.session_state.current_lang_hash = None 
    
    if 'df_pristine' not in st.session_state:
        st.session_state.df_pristine = None 
    if 'df_original' not in st.session_state:
        st.session_state.df_original = None 
    if 'df_staging' not in st.session_state:
        st.session_state.df_staging = None 
        
    if 'autocomplete_options' not in st.session_state:
        st.session_state.autocomplete_options = {} 
        
    # --- CORRECCIÓN: Inicialización de Usuario y Auditoría ---
    if 'username' not in st.session_state:
        st.session_state.username = "" # Inicializar vacío para evitar el error
        
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    if 'priority_rules' not in st.session_state:
        st.session_state.priority_rules = get_default_rules()
        
    if 'show_rules_editor' not in st.session_state:
        st.session_state.show_rules_editor = False
        
    if 'config_file_processed' not in st.session_state:
        st.session_state.config_file_processed = False
        
    # --- Variables del Chatbot ---
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "start_chat_msg", "chart": None, "actions": [], "custom_label": None}
        ]

# --- 2. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """
    Carga CSS personalizado para mejorar la UX visual.
    """
    st.markdown(
        """
        <style>
        /* --- CSS PARA RESALTAR CELDAS VACÍAS --- */
        [data-testid="stDataEditor"] [data-kind="cell"]:has(> .glide-cell-div:empty) {
            background-color: #FFF3B3 !important;
        }
        [data-testid="stDataEditor"] [data-kind="cell"] > .glide-cell-div > .glide-text-content[data-content="0"] {
            background-color: #FFF3B3 !important;
            color: #b0a06c;
        }

        /* --- CSS PARA RESALTAR FILA DE ALTA PRIORIDAD --- */
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

        /* --- VARIABLES DE COLOR GLOBALES --- */
        :root {
            --color-primario-azul: #004A99;
            --color-primario-rojo: #E30613;
            --color-primario-rojo-hover: #C0000A;
            --color-fondo: #F0F4F8;
            --color-fondo-tarjeta: #FFFFFF;
            --color-texto-principal: #0A1729;
            --color-borde: #D0D9E3;
            --color-naranja: #FFA500;
            --color-naranja-hover: #E69500;
            --color-verde: #008000;
            --color-verde-hover: #006400;
        }
        
        .stApp { background-color: var(--color-fondo); color: var(--color-texto-principal); }
        [data-testid="stSidebar"] { background-color: var(--color-fondo-tarjeta); border-right: 1px solid var(--color-borde); box-shadow: 2px 0px 10px rgba(0,0,0,0.05); }
        
        /* Botones */
        .stButton > button { background-color: var(--color-primario-rojo); color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: 600; transition: 0.2s ease; cursor: pointer; }
        .stButton > button:hover { background-color: var(--color-primario-rojo-hover); color: white; }
        
        .stButton[key*="commit_changes"] > button { background-color: var(--color-primario-azul); }
        .stButton[key*="commit_changes"] > button:hover { background-color: #003366; }
        .stButton[key*="reset_changes_button"] > button { background-color: var(--color-naranja); color: white; }
        .stButton[key*="reset_changes_button"] > button:hover { background-color: var(--color-naranja-hover); color: white; }
        .stButton[key*="restore_pristine"] > button { background-color: transparent; color: var(--color-primario-rojo); border: 1px solid var(--color-primario-rojo); }
        .stButton[key*="restore_pristine"] > button:hover { background-color: rgba(227, 6, 19, 0.05); color: var(--color-primario-rojo-hover); }
        
        /* Inputs */
        .stTextInput > div > div > input, .stSelectbox > div > div, .stFileUploader > div { border: 1px solid var(--color-borde); background-color: var(--color-fondo-tarjeta); border-radius: 5px; }
        .stTextInput > div > div > input:focus, .stSelectbox > div > div:focus-within { border-color: var(--color-primario-azul); box-shadow: 0 0 0 2px rgba(0, 74, 153, 0.3); }
        
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] { box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: none; border-radius: 8px; }
        .col-header { background-color: var(--color-primario-azul); color: white; font-weight: 600; }
        
        [data-testid="stDownloadButton"] > button { background-color: var(--color-verde); color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: 600; transition: 0.2s ease; cursor: pointer; }
        [data-testid="stDownloadButton"] > button:hover { background-color: var(--color-verde-hover); color: white; }
        
        [data-testid="stStatusWidget"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. FUNCIÓN AUXILIAR: Convertir a Excel ---
@st.cache_data
def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

# --- 4. FUNCIÓN DE CARGA Y PROCESAMIENTO DE DATOS ---
def load_and_process_files(uploaded_files, lang):
    """
    Orquesta la carga, limpieza y preparación de los datos.
    """
    try:
        lista_de_dataframes = []
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
        # 1. Carga de archivos
        for file in files_to_process:
            with st.spinner(f"Cargando {file.name}..."):
                df = pd.read_excel(file, engine="openpyxl", header=0)
            lista_de_dataframes.append(df)
        
        with st.spinner("Combinando y limpiando archivos (vectorizado)..."):
            # 2. Combinación
            df_processed = pd.concat(lista_de_dataframes, ignore_index=True)
            df_processed.columns = [col.strip() for col in df_processed.columns]
            columnas_originales = list(df_processed.columns)
            
            # 3. Tipado de columnas
            # Detectar columnas numéricas evitando errores con "Assignee" u otros textos
            numeric_cols = [col for col in columnas_originales if 
                            ('Total' in col or 'Amount' in col or 'Age' in col or 'Number' in col or 'ID' in col) 
                            and 'Assignee' not in col] # Excepción explícita
            
            date_cols = [col for col in columnas_originales if 'Date' in col and col not in numeric_cols]
            string_cols = [col for col in columnas_originales if col not in numeric_cols and col not in date_cols]

            if string_cols:
                df_processed[string_cols] = df_processed[string_cols].fillna("").astype(str)
            if numeric_cols:
                df_processed[numeric_cols] = df_processed[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            if date_cols:
                df_processed[date_cols] = df_processed[date_cols].apply(pd.to_datetime, errors='coerce')

            # Restaurar fechas limpias
            df_check = df_processed.astype(str).replace('NaT', '').replace('nan', '')
            if date_cols:
                for col in date_cols: df_processed[col] = df_check[col]

            # 4. Prioridad (Legacy)
            if 'Pay Group' in df_processed.columns:
                pay_group_searchable = df_processed['Pay Group'].astype(str).str.upper()
                mask_high = pay_group_searchable.str.contains('DIST|INTERCOMPANY|PAYROLL|RENTS|SCF', na=False)
                mask_low = pay_group_searchable.str.contains('PAYGROUP|PAY GROUP|GNTD', na=False)

                if 'Priority' not in df_processed.columns:
                    df_processed['Priority'] = "" 
            
                conditions = [mask_high, mask_low]
                choices = ["Maxima Prioridad", "Baja Prioridad"]
                df_processed['Priority'] = np.select(conditions, choices, default=df_processed['Priority'])
            
            # 5. Row Status
            blank_mask = (df_check == "") | (df_check == "0")
            incomplete_rows = blank_mask.any(axis=1)
            df_processed['Row Status'] = np.where(
                incomplete_rows, get_text(lang, 'status_incomplete'), get_text(lang, 'status_complete')
            )

            # 6. Guardado de Estados
            st.session_state.df_pristine = df_processed.copy()
            st.session_state.df_original = df_processed.copy()
            st.session_state.df_staging = df_processed.copy()
            
            # 7. Generación de Autocompletado (CORREGIDO: MENOS AGRESIVO)
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
                        # CORRECCIÓN: Usamos solo strip() para no borrar @, puntos, etc.
                        # Esto asegura que 'user@mail.com' coincida con la lista y se muestre.
                        series_cleaned = df_processed[col_en].astype(str).str.strip()
                        
                        if col_en == "Priority":
                            base_options = ["", "Zero", "Low", "Medium", "High"]
                            custom_options = ["Maxima Prioridad", "Baja Prioridad"]
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(list(set(base_options + custom_options + unique_vals)))
                        
                        elif col_en == "Status":
                            # --- ESTADOS DE NEGOCIO ESTANDARIZADOS ---
                            base_status_opts = [
                                "Imported to ERP", "Requester Approval", "Routed", "Fully Paid",
                                "Terminated", "AP Rejection", "AP Post Routing", 
                                "Imported to OIT", "Imported to ERP Failure"
                            ]
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(list(set(unique_vals + base_status_opts)))
                            
                        else:
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(unique_vals)
                        
                        # Filtro final de vacíos
                        opciones = [o for o in opciones if o.strip() != "" and o.strip() != "nan"]    
                        autocomplete_options[col_en] = opciones
                        
                    except Exception:
                        autocomplete_options[col_en] = [] 
            
            st.session_state.autocomplete_options = autocomplete_options
            
            # 8. Columnas Visibles
            columnas_iniciales = list(df_processed.columns)
            st.session_state.columnas_visibles = columnas_iniciales.copy()
            st.session_state.columnas_visibles_estable = columnas_iniciales.copy()

    except Exception as e:
        st.error(get_text(lang, 'error_critical').format(e=e))
        st.warning(get_text(lang, 'error_corrupt'))
        st.session_state.df_staging = None

# --- 5. LIMPIEZA DE ESTADO ---
def clear_state_and_prepare_reload():
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