# gui.py (Versión Corporativa con Descarga Excel)

import streamlit as st
import pandas as pd
import io  # <-- AÑADIDO: Para manejar el archivo en memoria
from modules.filters import aplicar_filtros_dinamicos
from modules.translator import get_text

# --- 1. Inicializar el 'Session State' ---
if 'filtros_activos' not in st.session_state:
    st.session_state.filtros_activos = []
if 'df_original' not in st.session_state:
    st.session_state.df_original = None
if 'language' not in st.session_state:
    st.session_state.language = 'es'

# --- 2. Configuración de la Página ---
st.set_page_config(
    layout="wide", 
    page_title=get_text(st.session_state.language, 'title')
)

# --- 3. FUNCIÓN DE DISEÑO (CSS) ---
def load_custom_css():
    """
    Carga el CSS personalizado para un tema corporativo (Azul/Rojo/Gris).
    """
    st.markdown(
        """
        <style>
        /* --- Paleta de Colores Inspirada en "Bimbo" --- */
        :root {
            --color-primario-azul: #004A99;      /* Azul corporativo */
            --color-primario-rojo: #E30613;      /* Rojo de acento */
            --color-primario-rojo-hover: #C0000A; /* Rojo más oscuro para hover */
            --color-fondo: #F0F4F8;             /* Fondo principal (gris azulado) */
            --color-fondo-tarjeta: #FFFFFF;     /* Fondo de widgets y tarjetas (blanco) */
            --color-texto-principal: #0A1729;    /* Texto principal (casi negro) */
            --color-texto-secundario: #5A6A7D;  /* Texto gris */
            --color-borde: #D0D9E3;             /* Borde sutil */
        }
        /* ... (El resto de tu CSS de diseño se mantiene igual) ... */
        
        /* --- Estructura Principal --- */
        .stApp {
            background-color: var(--color-fondo);
            color: var(--color-texto-principal);
        }

        /* Barra lateral */
        [data-testid="stSidebar"] {
            background-color: var(--color-fondo-tarjeta);
            border-right: 1px solid var(--color-borde);
            box-shadow: 2px 0px 10px rgba(0,0,0,0.05);
        }
        
        /* Título de la App (H1) */
        .stApp h1 {
            color: var(--color-primario-azul);
            font-weight: 800; /* Letra más gruesa */
        }

        /* Encabezados (H2, H3) */
        .stApp h2 {
            color: var(--color-primario-azul);
            border-bottom: 2px solid var(--color-borde); /* Línea divisoria */
            padding-bottom: 5px;
        }
        .stApp h3, [data-testid="stSidebar"] h3 {
            color: var(--color-texto-principal);
            font-weight: 600;
        }
        
        /* Encabezado de la barra lateral */
        [data-testid="stSidebar"] h2 {
             color: var(--color-primario-azul);
             border-bottom: none;
        }

        /* --- Botones --- */
        
        /* Botón Primario (Rojo de Acento) */
        .stButton > button {
            background-color: var(--color-primario-rojo);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
            font-weight: 600;
            transition: 0.2s ease;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: var(--color-primario-rojo-hover);
            color: white;
        }
        .stButton > button:focus {
            box-shadow: 0 0 0 3px rgba(227, 6, 19, 0.4);
        }

        /* Botón Secundario (Quitar) */
        .stButton[key*="quitar_"] > button {
            background-color: transparent;
            color: var(--color-primario-azul);
            border: 1px solid var(--color-primario-azul);
            padding: 0.2rem 0.5rem;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .stButton[key*="quitar_"] > button:hover {
            background-color: rgba(0, 74, 153, 0.05); /* Tinte azul */
            color: var(--color-primario-azul);
        }
        
        /* Botón "Limpiar todos" */
        .stButton[key*="limpiar_"] > button {
            background-color: transparent;
            color: var(--color-primario-rojo);
            border: 1px solid var(--color-primario-rojo);
        }
        .stButton[key*="limpiar_"] > button:hover {
            background-color: rgba(227, 6, 19, 0.05); /* Tinte rojo */
            color: var(--color-primario-rojo-hover);
        }

        /* --- Widgets --- */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stFileUploader > div {
            border: 1px solid var(--color-borde);
            background-color: var(--color-fondo-tarjeta);
            border-radius: 5px;
        }
        /* Al seleccionar un widget */
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div:focus-within {
            border-color: var(--color-primario-azul);
            box-shadow: 0 0 0 2px rgba(0, 74, 153, 0.3);
        }

        /* --- Contenedores (Tarjetas) --- */
        
        /* Contenedor de "Filtros Activos" */
        [data-testid="stVerticalBlock"]:has(>[data-testid="stVerticalBlockBorderWrapper"] [key*="quitar_"]) {
            background-color: var(--color-fondo-tarjeta);
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid var(--color-borde);
        }

        /* Tabla de Datos (DataFrame) */
        [data-testid="stDataFrame"] {
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: none;
            border-radius: 8px;
        }
        
        /* Encabezado de la tabla */
        [data-testid="stDataFrame"] .col-header {
            background-color: var(--color-primario-azul);
            color: white;
            font-weight: 600;
        }
        
        /* Texto de información (No hay filtros, cargue archivo) */
        .stAlert[data-testid="stInfo"] {
            background-color: var(--color-fondo-tarjeta);
            border: 1px dashed var(--color-borde);
            color: var(--color-texto-secundario);
            border-radius: 8px;
        }
        
        /* Estilo del botón de descarga Excel (para que sea primario) */
        .stButton[key*="download_excel"] > button {
             /* Hereda el estilo primario (rojo) */
        }

        </style>
        """,
        unsafe_allow_html=True
    )

# --- 4. NUEVA FUNCIÓN AUXILIAR: Convertir a Excel ---
@st.cache_data # Usamos cache para no regenerar el archivo si no cambian los datos
def to_excel(df: pd.DataFrame):
    """
    Convierte un DataFrame a un archivo Excel en memoria (bytes).
    """
    output = io.BytesIO()
    # Usamos 'with' para asegurar que el 'writer' se cierre correctamente
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    # Obtenemos el valor en bytes del buffer
    processed_data = output.getvalue()
    return processed_data

# --- 5. Cargar el CSS ---
load_custom_css()

# --- 6. Barra Lateral (Continuación) ---
lang_options = {"Español": "es", "English": "en"}
lang_choice = st.sidebar.radio(
    label="Idioma / Language",
    options=lang_options.keys(),
    index=0 if st.session_state.language == 'es' else 1
)
st.session_state.language = lang_options[lang_choice]
lang = st.session_state.language

st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")

uploaded_file = st.sidebar.file_uploader(
    get_text(lang, 'uploader_label'),
    type=["xlsx"],
    key="main_uploader"
)

# --- 7. Títulos Principales ---
st.markdown(f"<h1>🔎 {get_text(lang, 'title')}</h1>", unsafe_allow_html=True)
st.write(get_text(lang, 'subtitle'))

# --- 8. Área Principal (Lógica y Resultados) ---
if uploaded_file is not None:
    try:
        if st.session_state.df_original is None:
            df = pd.read_excel(uploaded_file, dtype=str, engine="openpyxl", header=0)
            df.columns = [col.strip() for col in df.columns]
            df = df.fillna("")
            st.session_state.df_original = df
            st.session_state.filtros_activos = [] 
        
        df_original = st.session_state.df_original
        
        # --- Interfaz de Creación de Filtros ---
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        
        lista_columnas = [""] + list(df_original.columns)
        columna_seleccionada = st.sidebar.selectbox(
            get_text(lang, 'column_select'),
            options=lista_columnas
        )

        valor_a_buscar = st.sidebar.text_input(get_text(lang, 'search_text'))

        if st.sidebar.button(get_text(lang, 'add_filter_button')):
            if columna_seleccionada and valor_a_buscar:
                st.session_state.filtros_activos.append({
                    "columna": columna_seleccionada,
                    "valor": valor_a_buscar
                })
            else:
                st.sidebar.warning(get_text(lang, 'warning_no_filter'))
        
        # --- Mostrar Filtros Activos ---
        st.markdown(f"## {get_text(lang, 'active_filters_header')}")
        
        if not st.session_state.filtros_activos:
            st.info(get_text(lang, 'no_filters_applied'))
        else:
            with st.container():
                filtros_a_eliminar = -1
                for i, filtro in enumerate(st.session_state.filtros_activos):
                    col1, col2 = st.columns([4, 1])
                    texto_filtro = get_text(lang, 'filter_display').format(
                        columna=filtro['columna'], 
                        valor=filtro['valor']
                    )
                    col1.markdown(f"• {texto_filtro}")
                    
                    if col2.button(get_text(lang, 'remove_button'), key=f"quitar_{i}"):
                        filtros_a_eliminar = i

                if filtros_a_eliminar > -1:
                    st.session_state.filtros_activos.pop(filtros_a_eliminar)
                    st.rerun()
                
                st.markdown("---") 
                
                if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
                    st.session_state.filtros_activos = []
                    st.rerun()

        # --- Aplicar Filtros y Mostrar Tabla ---
        resultado_df = aplicar_filtros_dinamicos(
            df_original,
            st.session_state.filtros_activos
        )

        st.markdown(f"## {get_text(lang, 'results_header').format(num_filas=len(resultado_df))}")
        st.dataframe(resultado_df)
        
        # --- SECCIÓN DE DESCARGA (MODIFICADA) ---
        
        # 1. (OBJETIVO 2) Preparamos los datos JSON (la funcionalidad sigue ahí)
        json_resultado = resultado_df.to_json(orient="records", force_ascii=False, indent=4)
        
        # 2. (OBJETIVO 1) El botón de JSON está "comentado" (desaparece)
        # st.download_button(
        #     label=get_text(lang, 'download_json_button'),
        #     data=json_resultado,
        #     file_name="resultado_facturas.json",
        #     mime="application/json",
        #     key="download_json"
        # )

        # 3. (OBJETIVOS 3 y 4) Preparamos y mostramos el botón de Excel
        excel_data = to_excel(resultado_df)
        
        st.download_button(
            label=get_text(lang, 'download_excel_button'),
            data=excel_data,
            file_name="resultado_facturas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )

    except Exception as e:
        st.error(get_text(lang, 'error_critical').format(e=e))
        st.warning(get_text(lang, 'error_corrupt'))
        st.session_state.df_original = None

else:
    st.info(get_text(lang, 'info_upload'))
    st.session_state.df_original = None
    st.session_state.filtros_activos = []