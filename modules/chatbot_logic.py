# modules/chatbot_logic.py
"""
Lógica del Chatbot 3.0: Enfoque de "Escaneo de Datos".
En lugar de analizar gramática, escaneamos la frase buscando coincidencias
directas con los valores únicos existentes en el DataFrame.
"""

import streamlit as st
import pandas as pd
import unicodedata
import re
from difflib import get_close_matches
from modules.translator import get_text, translate_column

# --- 1. UTILIDADES DE LIMPIEZA ---

def normalize_token(text: str) -> str:
    """Limpia una palabra para comparación (minúsculas, sin acentos)."""
    if not isinstance(text, str): return str(text).lower()
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9]', '', text) # Solo alfanuméricos
    return text

def get_stopwords():
    """Palabras que el bot debe ignorar completamente."""
    return {
        "el", "la", "los", "las", "un", "una", "de", "del", "por", "para", "con", 
        "y", "o", "que", "en", "a", "al", "se", "es", "son", "mis", "mi", "tu", 
        "facturas", "factura", "datos", "registros", "filas", "valor", "igual", 
        "como", "donde", "sea", "tenga", "muestrame", "dame", "ver", "quiero", 
        "buscar", "filtrar", "filtra", "busca", "traeme", "show", "filter", "get",
        "find", "search", "invoice", "invoices", "list", "lista", "tabla"
    }

# --- 2. CEREBRO DE BÚSQUEDA ---

def find_value_in_data(tokens: list, data_dict: dict) -> tuple:
    """
    Recorre los tokens del mensaje y busca si alguno coincide con un valor real
    en nuestras opciones de autocompletado.
    
    Returns: (Columna_Encontrada, Valor_Real_Encontrado) o (None, None)
    """
    best_match_score = 0.0
    best_col = None
    best_val = None

    # Aplanamos el diccionario para búsqueda rápida: { "valor_normalizado": ("Columna", "ValorReal") }
    # Esto es intensivo, pero con <10k facturas es instantáneo.
    lookup_map = {}
    for col, values in data_dict.items():
        for v in values:
            norm_v = normalize_token(str(v))
            if len(norm_v) > 2: # Ignorar valores muy cortos
                # Guardamos tupla: (ColumnaReal, ValorReal)
                # Ojo: Si un valor existe en 2 columnas, esto sobrescribe (generalmente aceptable)
                lookup_map[norm_v] = (col, v)

    # 1. Búsqueda Exacta o Parcial (substring)
    for token in tokens:
        if len(token) < 3: continue # Saltar palabras cortas
        
        # Caso A: Coincidencia Exacta
        if token in lookup_map:
            return lookup_map[token]
            
        # Caso B: Coincidencia Parcial (ej: "barcel" en "barcel s.a.")
        for key_val, (real_col, real_val) in lookup_map.items():
            if token in key_val: # Si el usuario escribió "barcel" y existe "grupo barcel"
                return (real_col, real_val)

    # 2. Búsqueda Difusa (Fuzzy) si no hubo exacta
    # Juntamos los tokens clave en una frase para ver si se parece a algo
    # (Esto ayuda si el usuario escribió "pendient" en lugar de "pendiente")
    all_keys = list(lookup_map.keys())
    for token in tokens:
        if len(token) < 4: continue
        matches = get_close_matches(token, all_keys, n=1, cutoff=0.75)
        if matches:
            return lookup_map[matches[0]]

    return None, None

# --- 3. PROCESADOR PRINCIPAL ---

def process_user_message(message: str, df: pd.DataFrame, lang: str) -> tuple[str, bool]:
    """
    Procesa el mensaje con lógica de escaneo de datos.
    """
    # 1. Normalización Inicial
    raw_msg = normalize_token(message)
    
    # 2. Detección de Comandos Básicos (Hardcoded Intents)
    keywords_help = ["ayuda", "help", "hacer", "funciones", "hola", "manual", "opciones"]
    if any(k in raw_msg for k in keywords_help):
        return get_text(lang, "chat_help_message"), False

    keywords_reset = ["reset", "limpiar", "borrar", "quitar", "reiniciar", "inicio", "todo"]
    if any(k in raw_msg for k in keywords_reset):
        st.session_state.filtros_activos = []
        return get_text(lang, "chat_response_reset"), True

    keywords_count = ["cuantas", "cantidad", "numero", "total", "count", "size"] # "total" es ambiguo, cuidado
    # Si dice "total monto" es suma, si dice "total facturas" es conteo.
    # Simplificación: si dice "cuantas" o "numero" es count.
    if any(k in raw_msg for k in ["cuantas", "cantidad", "numero", "count"]):
        return get_text(lang, "chat_response_count").format(n=len(df)), False

    keywords_sum = ["suma", "sumar", "monto", "dinero", "amount", "precio", "costo"]
    if any(k in raw_msg for k in keywords_sum):
        col_total = "Total"
        total_val = 0.0
        if col_total in df.columns:
            total_val = pd.to_numeric(df[col_total], errors='coerce').fillna(0).sum()
        return get_text(lang, "chat_response_total").format(n=f"{total_val:,.2f}"), False

    # --- 3. LÓGICA DE FILTRADO (DATA DRIVEN) ---
    
    # Tokenizamos el mensaje original para mantener estructura
    # Normalizamos cada palabra y quitamos stopwords
    stopwords = get_stopwords()
    words = message.split()
    clean_tokens = []
    
    for w in words:
        norm_w = normalize_token(w)
        if norm_w not in stopwords and len(norm_w) > 1:
            clean_tokens.append(norm_w)
            
    if not clean_tokens:
         return get_text(lang, "chat_response_unknown"), False

    # Buscamos en el diccionario de datos
    data_dict = st.session_state.get('autocomplete_options', {})
    found_col, found_val = find_value_in_data(clean_tokens, data_dict)
    
    if found_col and found_val:
        # Verificar si ya existe el filtro
        exists = any(f['columna'] == found_col and f['valor'] == found_val for f in st.session_state.filtros_activos)
        if exists:
            return "⚠️ Ese filtro ya está aplicado.", False
            
        st.session_state.filtros_activos.append({"columna": found_col, "valor": found_val})
        # Traducir nombre de columna para respuesta amigable
        col_ui = translate_column(lang, found_col)
        return get_text(lang, "chat_response_filter_applied").format(col=col_ui, val=found_val), True

    # Si llegamos aquí, no entendimos nada
    return get_text(lang, "chat_response_unknown"), False