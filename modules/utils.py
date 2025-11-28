# modules/utils.py
"""
Módulo de Utilidades Generales y Gestión de Estado.

Este módulo agrupa funciones esenciales para el ciclo de vida de la aplicación,
incluyendo:
1. Inicialización y gestión del estado de sesión (Session State).
2. Carga de estilos visuales (CSS) compatible con Modo Oscuro.
3. Procesamiento masivo de archivos Excel (lectura, limpieza y normalización).
4. Lógica auxiliar para actualización de estados de fila.
"""

import streamlit as st
import pandas as pd
import io
import numpy as np 
from modules.translator import get_text
# --- CAMBIO: Importamos el motor de reglas para usarlo en la carga inicial ---
from modules.rules_service import get_default_rules, apply_priority_rules 

# --- 1. Inicializar el 'Session State' ---
def initialize_session_state():
    """Define e inicializa el estado de la sesión de Streamlit.
    
    Verifica la existencia de cada clave necesaria en st.session_state.
    Si no existe, la crea con un valor por defecto seguro. Esto evita
    errores de tipo 'KeyError' durante la ejecución.
    """
    if 'filtros_activos' not in st.session_state:
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
        
    if 'username' not in st.session_state:
        st.session_state.username = ""
        
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    if 'priority_rules' not in st.session_state:
        try:
            # Intenta cargar reglas por defecto desde el servicio
            from modules.rules_service import get_default_rules 
            st.session_state.priority_rules = get_default_rules()
        except ImportError:
            st.session_state.priority_rules = []
        
    if 'show_rules_editor' not in st.session_state:
        st.session_state.show_rules_editor = False
        
    if 'config_file_processed' not in st.session_state:
        st.session_state.config_file_processed = False
        
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "start_chat_msg", "chart": None, "actions": [], "custom_label": None}
        ]

# --- 2. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """Carga e inyecta el CSS personalizado en la aplicación Streamlit.
    
    MEJORA DARK MODE:
    Utiliza variables CSS nativas de Streamlit (var(--text-color), etc.) para 
    adaptarse automáticamente al tema claro/oscuro del usuario.
    """
    st.markdown(
        """
        <style>
        /* --- VARIABLES DE TEMA ADAPTATIVAS --- */
        :root {
            /* Colores fijos de marca */
            --brand-blue: #004A99;
            --brand-red: #E30613;
            --brand-red-hover: #C0000A;
            --brand-green: #008000;
            --brand-green-hover: #006400;
            --brand-orange: #FFA500;
            
            /* Variables que se adaptan al tema (Usando variables de Streamlit) */
            --bg-color: var(--background-color);
            --text-color: var(--text-color);
            --card-bg: var(--secondary-background-color);
            --border-color: rgba(49, 51, 63, 0.2); 
        }

        /* --- CSS PARA RESALTAR CELDAS VACÍAS --- */
        [data-testid="stDataEditor"] [data-kind="cell"]:has(> .glide-cell-div:empty) {
            background-color: rgba(255, 243, 179, 0.4) !important; /* Amarillo translúcido */
        }
        
        /* Resalta ceros explícitos */
        [data-testid="stDataEditor"] [data-kind="cell"] > .glide-cell-div > .glide-text-content[data-content="0"] {
            background-color: rgba(255, 243, 179, 0.4) !important;
            color: var(--text-color); 
            opacity: 0.7;
        }

        /* --- CSS PARA RESALTAR FILA DE ALTA PRIORIDAD --- */
        /* Detecta texto 'Maxima Prioridad'.
           IMPORTANTE: Forzamos color negro en el texto para asegurar contraste
           sobre el fondo rojo, incluso en Dark Mode. */
        
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="Maxima Prioridad"]),
        [data-testid="stDataEditor"] [data-kind="row"]:has(div[data-content="🚩 Maxima Prioridad"]) {
            background-color: rgba(255, 221, 221, 0.3) !important; /* Rojo muy suave translúcido */
        }

        /* Celda específica de prioridad */
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="Maxima Prioridad"]), 
        [data-testid="stDataEditor"] [data-kind="cell"]:has(div[data-content="🚩 Maxima Prioridad"]) {
            font-weight: 800 !important;
            background-color: #FFC0C0 !important; /* Rojo sólido */
            color: black !important; /* Texto negro forzado para legibilidad */
        }

        /* --- ESTILOS GENERALES --- */
        
        /* Títulos */
        .stApp h1, .stApp h2 { color: var(--brand-blue) !important; }
        .stApp h3 { color: var(--text-color); }
        
        /* Botones Estándar (Rojos) */
        .stButton > button { 
            background-color: var(--brand-red); 
            color: white; 
            border: none; 
            border-radius: 5px; 
            transition: 0.2s ease; 
        }
        .stButton > button:hover { background-color: var(--brand-red-hover); color: white; }

        /* Botones de Acción Especial (Azul para Commit) */
        .stButton[key*="commit_changes"] > button { background-color: var(--brand-blue); }
        .stButton[key*="commit_changes"] > button:hover { background-color: #003366; }
        
        /* Botones de Reset (Naranja) */
        .stButton[key*="reset_changes_button"] > button { background-color: var(--brand-orange); color: white; }
        
        /* Botones de Restauración (Borde) */
        .stButton[key*="restore_pristine"] > button { 
            background-color: transparent; 
            color: var(--brand-red); 
            border: 1px solid var(--brand-red); 
        }
        
        /* Botones Pequeños (Chips de filtros) */
        .stButton[key*="quitar_"] > button { 
            background-color: var(--card-bg); 
            color: var(--brand-blue); 
            padding: 3px 10px; 
            border-radius: 12px; 
            border: 1px solid var(--border-color); 
            font-size: 0.9em;
        }
        
        /* Inputs de formulario - Usar variables nativas */
        .stTextInput > div > div > input, .stSelectbox > div > div { 
            border-radius: 5px; 
        }
        
        /* Botón de Descarga (Verde) */
        [data-testid="stDownloadButton"] > button { background-color: var(--brand-green); color: white; border: none; }
        [data-testid="stDownloadButton"] > button:hover { background-color: var(--brand-green-hover); color: white; }
        
        /* Ocultar Widget de estado de Streamlit (arriba derecha) */
        [data-testid="stStatusWidget"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. FUNCIÓN AUXILIAR: Convertir a Excel ---
@st.cache_data
def to_excel(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a un archivo Excel en memoria.
    
    Utiliza el motor 'openpyxl'.
    
    Args:
        df (pd.DataFrame): El DataFrame a exportar.
        
    Returns:
        bytes: El contenido binario del archivo Excel listo para descarga.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    return output.getvalue()

# --- 4. FUNCIÓN NUEVA: RECALCULAR ESTADO DE FILA ---
def recalculate_row_status(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Recalcula la columna 'Row Status' basada en si la fila tiene celdas vacías.

    Args:
        df (pd.DataFrame): El DataFrame a evaluar.
        lang (str): Idioma actual para los textos de estado.

    Returns:
        pd.DataFrame: El DataFrame con la columna 'Row Status' actualizada.
    """
    if df is None or df.empty:
        return df

    # Columnas que NO cuentan para determinar si la fila está incompleta
    cols_to_exclude = ['Row Status', 'Priority', 'Priority_Reason', 'Seleccionar']
    cols_to_check = [c for c in df.columns if c not in cols_to_exclude]
    
    if not cols_to_check:
        return df
    
    # Crear copia temporal para validación, tratando NaT/NaN como string vacío
    df_check = df[cols_to_check].astype(str).replace(['NaT', 'nan', 'None', '<NA>'], '')
    
    # Máscara de incompletitud: Vacío ("") o Cero ("0") se consideran incompletos
    blank_mask = (df_check == "") | (df_check == "0")
    incomplete_rows = blank_mask.any(axis=1)
    
    # Asignación vectorizada del estado
    df['Row Status'] = np.where(
        incomplete_rows,
        get_text(lang, 'status_incomplete'),
        get_text(lang, 'status_complete')
    )
    
    return df

# --- 5. FUNCIÓN DE CARGA Y PROCESAMIENTO DE DATOS ---
def load_and_process_files(uploaded_files, lang):
    """
    Toma los archivos cargados, los combina, limpia (usando vectorización), 
    guarda las 3 copias (pristine, original, staging) y pre-calcula las 
    opciones de autocompletar.
    
    Args:
        uploaded_files: Un archivo o lista de archivos (UploadedFile).
        lang (str): Idioma actual.
    """
    try:
        lista_de_dataframes = []
        # Normalizar entrada a lista
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
        for file in files_to_process:
            with st.spinner(f"Cargando {file.name}..."):
                # Lectura directa
                df = pd.read_excel(file, engine="openpyxl", header=0)
            lista_de_dataframes.append(df)
        
        with st.spinner("Combinando y limpiando archivos (vectorizado)..."):
            # Concatenación de todos los Excels
            df_processed = pd.concat(lista_de_dataframes, ignore_index=True)
            
            # Limpieza de nombres de columna
            df_processed.columns = [col.strip() for col in df_processed.columns]
            columnas_originales = list(df_processed.columns)
            
            # Detección automática de tipos de columna basada en nombre
            numeric_cols = [col for col in columnas_originales if 
                            ('Total' in col or 'Amount' in col or 'Age' in col or 'Number' in col or 'ID' in col) 
                            and 'Assignee' not in col]
            
            date_cols = [col for col in columnas_originales if 'Date' in col and col not in numeric_cols]
            string_cols = [col for col in columnas_originales if col not in numeric_cols and col not in date_cols]

            # Conversión de tipos Vectorizada (Más rápida que bucles)
            if string_cols:
                df_processed[string_cols] = df_processed[string_cols].fillna("").astype(str)
            if numeric_cols:
                df_processed[numeric_cols] = df_processed[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            if date_cols:
                df_processed[date_cols] = df_processed[date_cols].apply(pd.to_datetime, errors='coerce')

            # Limpieza adicional para columnas de fecha que fallaron conversión
            df_check = df_processed.astype(str).replace('NaT', '').replace('nan', '')
            if date_cols:
                for col in date_cols: df_processed[col] = df_check[col]

            # --- CORRECCIÓN: Aplicar Motor de Reglas en la carga inicial ---
            # Esto asegura que Priority_Reason se cree desde el principio y el filtro del sidebar no "parpadee"
            df_processed = apply_priority_rules(df_processed)
            
            # 5. Cálculo inicial de estado de fila
            df_processed = recalculate_row_status(df_processed, lang)

            # 6. Inicialización de los 3 estados de datos
            st.session_state.df_pristine = df_processed.copy() # Intocable (Backup carga)
            st.session_state.df_original = df_processed.copy() # Punto de control (Commit)
            st.session_state.df_staging = df_processed.copy()  # Trabajo activo (Draft)
            
            # 7. Generación de Opciones de Autocompletado
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
                        series_cleaned = df_processed[col_en].astype(str).str.strip()
                        
                        # Lógica específica para listas predefinidas + valores encontrados
                        if col_en == "Priority":
                            base_options = ["", "Zero", "Low", "Medium", "High"]
                            custom_options = ["Maxima Prioridad", "Baja Prioridad"]
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(list(set(base_options + custom_options + unique_vals)))
                        elif col_en == "Status":
                            base_status_opts = [
                                "Imported to ERP", "Requester Approval", "Routed", "Fully Paid",
                                "Terminated", "AP Rejection", "AP Post Routing", 
                                "Imported to OIT", "Imported to ERP Failure"
                            ]
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(list(set(unique_vals + base_status_opts)))
                        else:
                            # Por defecto: solo valores únicos encontrados
                            unique_vals = series_cleaned.unique().tolist()
                            opciones = sorted(unique_vals)
                        
                        # Limpieza de opciones vacías
                        opciones = [o for o in opciones if o.strip() != "" and o.strip() != "nan"]    
                        autocomplete_options[col_en] = opciones
                    except Exception:
                        autocomplete_options[col_en] = [] 
            
            st.session_state.autocomplete_options = autocomplete_options
            columnas_iniciales = list(df_processed.columns)
            
            # Inicialización de columnas visibles (todas por defecto)
            st.session_state.columnas_visibles = columnas_iniciales.copy()
            st.session_state.columnas_visibles_estable = columnas_iniciales.copy()

    except Exception as e:
        st.error(get_text(lang, 'error_critical').format(e=e))
        st.warning(get_text(lang, 'error_corrupt'))
        st.session_state.df_staging = None

# --- 6. LIMPIEZA DE ESTADO ---
def clear_state_and_prepare_reload():
    """
    Resetea el estado de la sesión al cargar nuevos archivos.
    Limpia las tres copias del DataFrame y configuraciones de vista.
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