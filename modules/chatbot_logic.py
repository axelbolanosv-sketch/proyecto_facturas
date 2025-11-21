# modules/chatbot_logic.py
"""
Lógica del Chatbot 6.0: ACCIONABLE Y VISUAL.
Devuelve acciones concretas (filtros automáticos) y gráficos bajo demanda.
VERSION ACTUALIZADA: RESPUESTAS MULTILINGÜES
"""

import streamlit as st
import pandas as pd
import unicodedata
import re
from difflib import get_close_matches
from modules.translator import get_text, translate_column
import numpy as np

# --- 1. UTILIDADES ---

def normalize_token(text: str) -> str:
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
        "grafica", "grafico", "distribucion", "plot", "chart", "analiza", "analisis",
        "top", "ranking", "mejores", "mayores", "resumen", "informe", "give", "me", "an", "executive"
    }

def find_value_in_data(tokens: list, data_dict: dict) -> tuple:
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

# --- 2. FUNCIONES DE INTELIGENCIA DE NEGOCIO ---

def analyze_anomalies(df: pd.DataFrame, lang: str):
    """
    Detecta valores atípicos y devuelve una ACCIÓN para filtrarlos.
    """
    if 'Total' not in df.columns or df.empty:
        return get_text(lang, "logic_msg_anomalies_error"), None, []
    
    totals = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    
    # Lógica Estadística (Media + 2 Desviaciones)
    mean = totals.mean()
    std_dev = totals.std()
    threshold = mean + 2 * std_dev
    
    if std_dev == 0 or threshold <= mean: 
        threshold = totals.quantile(0.95)
        
    if threshold <= 0: 
        return get_text(lang, "logic_msg_anomalies_none"), None, []
    
    anomalies = df[totals > threshold]
    count = len(anomalies)
    
    msg = get_text(lang, "logic_msg_anomalies_found").format(count=count, threshold=threshold)
    
    chart_data = {
        "type": "bar",
        "data": anomalies['Total'].head(10),
        "title": get_text(lang, "logic_chart_anomalies_title").format(t=f"{threshold:,.0f}"),
        "x_label": "ID",
        "y_label": "Total"
    }
    
    actions = [{
        "label": get_text(lang, "logic_action_filter_anomalies").format(n=count),
        "type": "filter_numeric", 
        "col": "Total",
        "op": ">",
        "val": threshold
    }]
    
    return msg, chart_data, actions

def generate_top_vendors(df: pd.DataFrame, lang: str):
    if 'Vendor Name' not in df.columns or 'Total' not in df.columns:
        return get_text(lang, "logic_msg_top_error"), None, []

    df_calc = df.copy()
    df_calc['Total'] = pd.to_numeric(df_calc['Total'], errors='coerce').fillna(0)
    top_5 = df_calc.groupby('Vendor Name')['Total'].sum().nlargest(5)
    
    if top_5.empty: return get_text(lang, "logic_msg_top_none"), None, []
    
    top_name = top_5.index[0]
    top_val = top_5.iloc[0]
    
    msg = get_text(lang, "logic_msg_top_found").format(name=top_name, val=top_val)
    
    chart_data = {
        "type": "bar",
        "data": top_5,
        "title": get_text(lang, "logic_chart_top_title"),
        "x_label": "Vendor",
        "y_label": "Total"
    }
    
    actions = [{
        "label": get_text(lang, "logic_action_filter_top").format(name=top_name),
        "type": "filter_exact",
        "col": "Vendor Name",
        "val": top_name
    }]
    
    return msg, chart_data, actions

def generate_smart_summary(df: pd.DataFrame, lang: str):
    if df.empty: return get_text(lang, "logic_msg_summary_empty"), None, []
    
    total_recs = len(df)
    col_total = 'Total'
    total_amt = 0
    if col_total in df.columns:
        total_amt = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        
    msg = get_text(lang, "logic_msg_summary").format(n=total_recs, amt=total_amt)
    
    return msg, None, []

# --- 3. PROCESADOR PRINCIPAL ---

def process_user_message(message: str, df: pd.DataFrame, lang: str) -> tuple:
    """
    Retorna: (Texto, Rerun_Needed, Chart_Data, Suggested_Actions)
    """
    raw_msg = normalize_token(message)
    
    # --- A. INTENCIONES ANALÍTICAS ---
    if any(k in raw_msg for k in ["anomalia", "raro", "atipico", "alerta", "investiga", "outlier", "anomalies"]):
        msg, chart, acts = analyze_anomalies(df, lang) # Pasamos 'lang'
        return msg, False, chart, acts

    if any(k in raw_msg for k in ["top", "ranking", "mejor", "mayor", "mas caro"]):
        msg, chart, acts = generate_top_vendors(df, lang) # Pasamos 'lang'
        return msg, False, chart, acts

    if any(k in raw_msg for k in ["resumen", "informe", "describe", "situacion", "summary"]):
        msg, chart, acts = generate_smart_summary(df, lang) # Pasamos 'lang'
        return msg, False, chart, acts

    # --- B. INTENCIÓN: GRÁFICOS ---
    keywords_chart = ["grafica", "grafico", "distribucion", "chart", "plot", "visualiza", "barras", "pastel"]
    if any(k in raw_msg for k in keywords_chart):
        target_col = None
        cols_map = {normalize_token(translate_column(lang, c)): c for c in df.columns}
        for col_norm, col_real in cols_map.items():
            if col_norm in raw_msg:
                target_col = col_real
                break
        
        if not target_col:
            if "estado" in raw_msg or "status" in raw_msg: target_col = "Status"
            elif "proveedor" in raw_msg or "vendor" in raw_msg: target_col = "Vendor Name"
            elif "prioridad" in raw_msg or "priority" in raw_msg: target_col = "Priority"
            elif "grupo" in raw_msg or "pay" in raw_msg: target_col = "Pay Group"
        
        if target_col and target_col in df.columns:
            counts = df[target_col].value_counts().head(10)
            col_ui = translate_column(lang, target_col)
            chart_data = {
                "type": "bar", "data": counts,
                "title": f"Distribución - {col_ui}",
                "x_label": col_ui, "y_label": "Cantidad"
            }
            return get_text(lang, "logic_msg_chart_ok").format(col=col_ui), False, chart_data, []
        else:
            return get_text(lang, "logic_msg_chart_fail"), False, None, []

    # --- C. INTENCIONES BÁSICAS ---
    if any(k in raw_msg for k in ["ayuda", "help", "hacer", "opciones"]):
        return get_text(lang, "chat_help_message"), False, None, []

    if any(k in raw_msg for k in ["reset", "limpiar", "borrar", "inicio"]):
        st.session_state.filtros_activos = []
        return get_text(lang, "chat_response_reset"), True, None, []

    if any(k in raw_msg for k in ["cuantas", "cantidad", "numero", "count"]) and not "monto" in raw_msg:
        return get_text(lang, "chat_response_count").format(n=len(df)), False, None, []

    if any(k in raw_msg for k in ["suma", "monto", "total", "dinero"]):
        col_total = "Total"
        total_val = 0.0
        if col_total in df.columns:
            total_val = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        return get_text(lang, "chat_response_total").format(n=f"{total_val:,.2f}"), False, None, []

    # --- D. FILTRADO ---
    stopwords = get_stopwords()
    words = message.split()
    clean_tokens = [normalize_token(w) for w in words if normalize_token(w) not in stopwords and len(normalize_token(w)) > 1]

    if not clean_tokens:
         return get_text(lang, "chat_response_unknown"), False, None, []

    data_dict = st.session_state.get('autocomplete_options', {})
    found_col, found_val = find_value_in_data(clean_tokens, data_dict)
    
    if found_col and found_val:
        exists = any(f['columna'] == found_col and f['valor'] == found_val for f in st.session_state.filtros_activos)
        if exists: return get_text(lang, "logic_msg_filter_exists"), False, None, []
        st.session_state.filtros_activos.append({"columna": found_col, "valor": found_val})
        col_ui = translate_column(lang, found_col)
        return get_text(lang, "chat_response_filter_applied").format(col=col_ui, val=found_val), True, None, []

    return get_text(lang, "chat_response_unknown"), False, None, []