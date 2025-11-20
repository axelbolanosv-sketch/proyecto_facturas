# modules/chatbot_logic.py
"""
Lógica del Chatbot 5.0: MODO ANALISTA (Innovación).
Incluye detección de anomalías, rankings y resúmenes ejecutivos.
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
        "grafica", "grafico", "distribucion", "plot", "chart", "analiza", "analisis",
        "top", "ranking", "mejores", "mayores", "resumen", "informe"
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

# --- 2. FUNCIONES DE INTELIGENCIA DE NEGOCIO ---

def analyze_anomalies(df: pd.DataFrame):
    """Detecta valores atípicos (Outliers) en el monto."""
    if 'Total' not in df.columns or df.empty:
        return "No puedo analizar anomalías sin una columna 'Total' numérica.", None
    
    # Convertir a numérico
    totals = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    
    # Definir anomalía: Mayor al percentil 95 (Top 5% más caro)
    threshold = totals.quantile(0.95)
    
    if threshold == 0: return "Los montos son todos cero o no detecto variaciones.", None
    
    anomalies = df[totals > threshold]
    count = len(anomalies)
    
    msg = (f"🕵️ **Análisis de Anomalías:**\n\n"
           f"He detectado **{count} facturas** con montos inusualmente altos (superiores a **${threshold:,.2f}**).\n"
           f"Esto representa el top 5% de tus gastos actuales. ¿Deseas filtrarlas?")
    
    # Preparamos un gráfico de dispersión simple o histograma
    chart_data = {
        "type": "bar",
        "data": anomalies['Total'].head(10), # Top 10 anomalías
        "title": f"Top Anomalías (> ${threshold:,.0f})",
        "x_label": "Índice",
        "y_label": "Monto Total"
    }
    return msg, chart_data

def generate_top_vendors(df: pd.DataFrame):
    """Genera un ranking de los proveedores que más dinero consumen."""
    if 'Vendor Name' not in df.columns or 'Total' not in df.columns:
        return "Me faltan columnas (Vendor Name o Total) para hacer este ranking.", None

    # Agrupar y sumar
    # Asegurar numérico
    df_calc = df.copy()
    df_calc['Total'] = pd.to_numeric(df_calc['Total'], errors='coerce').fillna(0)
    
    top_5 = df_calc.groupby('Vendor Name')['Total'].sum().nlargest(5)
    
    if top_5.empty: return "No hay datos suficientes para el ranking.", None
    
    top_name = top_5.index[0]
    top_val = top_5.iloc[0]
    
    msg = (f"🏆 **Ranking de Proveedores:**\n\n"
           f"El proveedor #1 es **{top_name}** con un total de **${top_val:,.2f}**.\n"
           f"Aquí tienes el Top 5 visualizado:")
    
    chart_data = {
        "type": "bar",
        "data": top_5,
        "title": "Top 5 Proveedores por Monto ($)",
        "x_label": "Proveedor",
        "y_label": "Monto Total"
    }
    return msg, chart_data

def generate_smart_summary(df: pd.DataFrame):
    """Crea una narrativa escrita sobre el estado actual de los datos."""
    if df.empty: return "La vista actual está vacía.", None
    
    total_recs = len(df)
    col_total = 'Total'
    total_amt = 0
    if col_total in df.columns:
        total_amt = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        
    # Moda de estado
    status_txt = ""
    if 'Status' in df.columns:
        top_status = df['Status'].mode()
        if not top_status.empty:
            status_counts = df['Status'].value_counts(normalize=True)
            pct = status_counts.iloc[0] * 100
            status_txt = f"La mayoría de las facturas (**{pct:.0f}%**) están en estado **'{top_status.iloc[0]}'**."

    # Moda de proveedor
    vendor_txt = ""
    if 'Vendor Name' in df.columns:
        top_vendor = df['Vendor Name'].mode()
        if not top_vendor.empty:
            vendor_txt = f"El proveedor más frecuente es **{top_vendor.iloc[0]}**."

    msg = (f"📝 **Resumen Ejecutivo:**\n\n"
           f"Actualmente estás analizando **{total_recs} registros** con un valor total de **${total_amt:,.2f}**.\n\n"
           f"• {status_txt}\n"
           f"• {vendor_txt}\n"
           f"\n¿Te gustaría profundizar en algún proveedor?")
    
    return msg, None

# --- 3. PROCESADOR PRINCIPAL ---

def process_user_message(message: str, df: pd.DataFrame, lang: str) -> tuple[str, bool, dict]:
    """
    Retorna: (Texto_Respuesta, Rerun_Needed, Datos_Grafico)
    """
    raw_msg = normalize_token(message)
    chart_data = None 

    # --- A. INTENCIONES ANALÍTICAS (INNOVACIÓN) ---
    
    # 1. ANOMALÍAS
    if any(k in raw_msg for k in ["anomalia", "raro", "atipico", "alerta", "investiga", "strange", "outlier"]):
        msg, chart = analyze_anomalies(df)
        return msg, False, chart

    # 2. TOP / RANKING
    if any(k in raw_msg for k in ["top", "ranking", "mejor", "mayor", "mas caro", "expensive", "best"]):
        msg, chart = generate_top_vendors(df)
        return msg, False, chart

    # 3. RESUMEN / INFORME
    if any(k in raw_msg for k in ["resumen", "informe", "describe", "situacion", "overview", "summary", "reporte"]):
        msg, chart = generate_smart_summary(df)
        return msg, False, chart

    # --- B. INTENCIÓN: GRÁFICOS ESTÁNDAR ---
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
        
        if target_col and target_col in df.columns:
            counts = df[target_col].value_counts().head(10)
            chart_data = {
                "type": "bar",
                "data": counts,
                "title": f"Distribución - {translate_column(lang, target_col)}",
                "x_label": translate_column(lang, target_col),
                "y_label": "Cantidad"
            }
            return f"📊 Aquí tienes la distribución por **{translate_column(lang, target_col)}**.", False, chart_data
        else:
            return "Dime qué columna quieres graficar (ej: 'Gráfico de Estado').", False, None

    # --- C. INTENCIONES BÁSICAS ---
    if any(k in raw_msg for k in ["ayuda", "help", "hacer", "opciones"]):
        return get_text(lang, "chat_help_message"), False, None

    if any(k in raw_msg for k in ["reset", "limpiar", "borrar", "inicio"]):
        st.session_state.filtros_activos = []
        return get_text(lang, "chat_response_reset"), True, None

    if any(k in raw_msg for k in ["cuantas", "cantidad", "numero", "count"]) and not "monto" in raw_msg:
        return get_text(lang, "chat_response_count").format(n=len(df)), False, None

    if any(k in raw_msg for k in ["suma", "monto", "total", "dinero"]):
        col_total = "Total"
        total_val = 0.0
        if col_total in df.columns:
            total_val = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        return get_text(lang, "chat_response_total").format(n=f"{total_val:,.2f}"), False, None

    # --- D. FILTRADO INTELIGENTE ---
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