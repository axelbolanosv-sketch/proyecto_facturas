# modules/chatbot_logic.py
"""
Lógica del Chatbot 4.0: Ahora con CAPACIDAD VISUAL.
Devuelve datos estructurados para generar gráficos si el usuario lo pide.
"""

import streamlit as st
import pandas as pd
import unicodedata
import re
from difflib import get_close_matches
from modules.translator import get_text, translate_column

# --- 1. UTILIDADES ---

def normalize_token(text: str) -> str:
    """Limpia una palabra para comparación."""
    if not isinstance(text, str): return str(text).lower()
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def get_stopwords():
    return {
        "el", "la", "los", "las", "un", "una", "de", "del", "por", "para", "con", 
        "y", "o", "que", "en", "a", "al", "mis", "mi", "tu", "facturas", "datos", 
        "valor", "igual", "como", "donde", "sea", "tenga", "muestrame", "dame", 
        "ver", "quiero", "buscar", "filtrar", "filtra", "busca", "traeme", "show", 
        "grafica", "grafico", "distribucion", "plot", "chart" # Añadimos palabras de gráfico a stopwords para limpieza
    }

def find_value_in_data(tokens: list, data_dict: dict) -> tuple:
    """Busca coincidencias en el diccionario de datos."""
    lookup_map = {}
    for col, values in data_dict.items():
        for v in values:
            norm_v = normalize_token(str(v))
            if len(norm_v) > 2:
                lookup_map[norm_v] = (col, v)

    for token in tokens:
        if len(token) < 3: continue
        if token in lookup_map: return lookup_map[token]
        for key_val, (real_col, real_val) in lookup_map.items():
            if token in key_val: return (real_col, real_val)

    all_keys = list(lookup_map.keys())
    for token in tokens:
        if len(token) < 4: continue
        matches = get_close_matches(token, all_keys, n=1, cutoff=0.75)
        if matches: return lookup_map[matches[0]]

    return None, None

# --- 2. PROCESADOR PRINCIPAL ---

def process_user_message(message: str, df: pd.DataFrame, lang: str) -> tuple[str, bool, dict]:
    """
    Retorna: (Texto_Respuesta, Rerun_Needed, Datos_Grafico)
    Datos_Grafico es un dict o None: {'type': 'bar', 'data': pd.Series, 'title': str}
    """
    raw_msg = normalize_token(message)
    chart_data = None # Por defecto no hay gráfico

    # --- INTENCIÓN: GRÁFICOS (NUEVO) ---
    keywords_chart = ["grafica", "grafico", "distribucion", "chart", "plot", "visualiza", "barras", "pastel"]
    if any(k in raw_msg for k in keywords_chart):
        # Intentar deducir qué columna graficar
        # Prioridad: Status, Vendor, Priority, Pay Group
        target_col = None
        
        # Buscar si el usuario mencionó una columna explícita
        cols_map = {normalize_token(translate_column(lang, c)): c for c in df.columns}
        for col_norm, col_real in cols_map.items():
            if col_norm in raw_msg:
                target_col = col_real
                break
        
        # Si no mencionó columna, pero pide gráfico, sugerimos o usamos una por defecto interesante
        if not target_col:
            if "estado" in raw_msg or "status" in raw_msg: target_col = "Status"
            elif "proveedor" in raw_msg or "vendor" in raw_msg: target_col = "Vendor Name"
            elif "prioridad" in raw_msg or "priority" in raw_msg: target_col = "Priority"
        
        if target_col and target_col in df.columns:
            # Calcular distribución
            counts = df[target_col].value_counts().head(10) # Top 10 para no saturar
            chart_data = {
                "type": "bar",
                "data": counts,
                "title": f"Top 10 - {translate_column(lang, target_col)}",
                "x_label": translate_column(lang, target_col),
                "y_label": "Cantidad"
            }
            return f"📊 Aquí tienes la distribución por **{translate_column(lang, target_col)}**.", False, chart_data
        else:
            return "Para generar un gráfico, dime qué columna quieres ver (ej: 'Gráfico de Estado' o 'Distribución de Proveedores').", False, None

    # --- INTENCIONES BÁSICAS ---
    keywords_help = ["ayuda", "help", "hacer", "funciones", "hola", "manual", "opciones"]
    if any(k in raw_msg for k in keywords_help):
        return get_text(lang, "chat_help_message"), False, None

    keywords_reset = ["reset", "limpiar", "borrar", "quitar", "reiniciar", "inicio", "todo"]
    if any(k in raw_msg for k in keywords_reset):
        st.session_state.filtros_activos = []
        return get_text(lang, "chat_response_reset"), True, None

    keywords_count = ["cuantas", "cantidad", "numero", "total", "count", "size"]
    if any(k in raw_msg for k in keywords_count) and not "monto" in raw_msg:
        return get_text(lang, "chat_response_count").format(n=len(df)), False, None

    keywords_sum = ["suma", "sumar", "monto", "dinero", "amount", "precio", "costo"]
    if any(k in raw_msg for k in keywords_sum):
        col_total = "Total"
        total_val = 0.0
        if col_total in df.columns:
            total_val = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        return get_text(lang, "chat_response_total").format(n=f"{total_val:,.2f}"), False, None

    # --- FILTRADO ---
    stopwords = get_stopwords()
    words = message.split()
    clean_tokens = [normalize_token(w) for w in words if normalize_token(w) not in stopwords and len(normalize_token(w)) > 1]

    if not clean_tokens:
         return get_text(lang, "chat_response_unknown"), False, None

    data_dict = st.session_state.get('autocomplete_options', {})
    found_col, found_val = find_value_in_data(clean_tokens, data_dict)
    
    if found_col and found_val:
        exists = any(f['columna'] == found_col and f['valor'] == found_val for f in st.session_state.filtros_activos)
        if exists: return "⚠️ Ese filtro ya está aplicado.", False, None
        st.session_state.filtros_activos.append({"columna": found_col, "valor": found_val})
        col_ui = translate_column(lang, found_col)
        return get_text(lang, "chat_response_filter_applied").format(col=col_ui, val=found_val), True, None

    return get_text(lang, "chat_response_unknown"), False, None