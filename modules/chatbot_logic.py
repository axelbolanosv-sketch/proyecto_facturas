# modules/chatbot_logic.py
"""
Lógica del Chatbot 12.0: AGENTE TOTAL (Vista + Edición Masiva).

Nuevas Capacidades:
1. GESTIÓN DE VISTA: Ahora sí expuesta en TOOLS_SCHEMA (Ocultar/Mostrar columnas).
2. EDICIÓN BULK: Capacidad de modificar múltiples filas por ID o Rango.
3. ESTABILIDAD: Mantiene validación de datos y autocompletado.
"""

import streamlit as st
import pandas as pd
import json
import uuid
from difflib import get_close_matches
from modules.azure_service import AzureBotClient
from modules.translator import get_text, translate_column
from modules.rules_service import apply_priority_rules
# Importamos utilidad para recalcular estado de fila tras edición
from modules.utils import recalculate_row_status

try:
    AZURE_ENDPOINT = st.secrets["AZURE_ENDPOINT"]
    AZURE_API_KEY = st.secrets["AZURE_KEY"]
    DEPLOYMENT_NAME = "gpt-4-1-preview"
except Exception:
    # Fallback para desarrollo local si no hay secrets.toml (pero SIN poner la clave real aquí)
    st.error("⚠️ Configura tus credenciales en .streamlit/secrets.toml")
    st.stop()

# --- DEFINICIÓN DE HERRAMIENTAS (SCHEMA) ---
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "examinar_datos_reales",
            "description": "LEE las primeras filas para entender datos.",
            "parameters": {
                "type": "object",
                "properties": {"filas_maximas": {"type": "integer"}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gestionar_vista",
            "description": "Oculta o muestra columnas en la tabla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["show_only", "hide", "show", "reset"], "description": "reset=mostrar todo"},
                    "columnas": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "modificar_datos_masivo",
            "description": "Edita valores en la tabla por lista de IDs o rango de filas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "columna": {"type": "string", "description": "Columna a editar"},
                    "valor_nuevo": {"type": "string", "description": "Valor a escribir"},
                    "ids_especificos": {"type": "array", "items": {"type": "string"}, "description": "Lista de IDs (índices) a modificar"},
                    "rango_inicio": {"type": "integer", "description": "Fila inicial (1-based)"},
                    "rango_fin": {"type": "integer", "description": "Fila final (1-based)"}
                },
                "required": ["columna", "valor_nuevo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_filtro",
            "description": "Aplica filtro visual. Para comparar usa valor='A|B'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "columna": {"type": "string"},
                    "valor": {"type": "string"},
                    "operador": {"type": "string", "enum": ["contains", "equals", ">", "<"], "default": "contains"}
                },
                "required": ["columna", "valor"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico",
            "description": "Genera gráficos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["bar", "line", "pie", "scatter"]},
                    "eje_x": {"type": "string"},
                    "eje_y": {"type": "string"},
                    "titulo": {"type": "string"}
                },
                "required": ["tipo", "eje_x"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_regla_prioridad",
            "description": "Crea regla de negocio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prioridad": {"type": "string", "enum": ["Maxima Prioridad", "Alta", "Media", "Minima"]},
                    "razon": {"type": "string"},
                    "condiciones": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "columna": {"type": "string"},
                                "operador": {"type": "string"},
                                "valor": {"type": "string"}
                            },
                            "required": ["columna", "operador", "valor"]
                        }
                    }
                },
                "required": ["prioridad", "razon", "condiciones"]
            }
        }
    }
]

# --- UTILIDADES DE VALIDACIÓN ---

def find_best_match(value: str, options: list) -> str:
    """Encuentra el valor real en la lista de opciones (Fuzzy Match)."""
    if not value or not options: return None
    str_options = [str(o) for o in options]
    lower_opts = {o.lower(): o for o in str_options}
    if str(value).lower() in lower_opts: return lower_opts[str(value).lower()]
    matches = get_close_matches(str(value), str_options, n=1, cutoff=0.6)
    return matches[0] if matches else None

def validate_column_and_value(df, col_name, val_value):
    """Corrige nombre de columna y valor usando datos reales."""
    real_col = next((c for c in df.columns if c.lower() == col_name.lower()), None)
    if not real_col:
        real_col = find_best_match(col_name, df.columns.tolist())
    
    if not real_col: return None, val_value
        
    real_val = val_value
    options_source = []
    if 'autocomplete_options' in st.session_state and real_col in st.session_state.autocomplete_options:
        options_source = st.session_state.autocomplete_options[real_col]
    
    if not options_source and real_col in df.columns:
        # Muestreo rápido si no hay caché
        options_source = df[real_col].astype(str).unique().tolist()[:500]
        
    if options_source:
        match = find_best_match(val_value, options_source)
        if match: real_val = match
            
    return real_col, real_val

def _generar_contexto_valores(df):
    if df.empty: return ""
    cols = ['Vendor Name', 'Status', 'Pay Group', 'Assignee']
    ctx = []
    for c in df.columns:
        if c in cols:
            vals = df[c].dropna().astype(str).unique()
            ctx.append(f"- {c}: {', '.join(vals[:15])}...")
    return "\n".join(ctx)

# --- PROCESADOR PRINCIPAL ---

def process_user_message(message: str, df: pd.DataFrame, lang: str) -> tuple:
    client = AzureBotClient(AZURE_ENDPOINT, AZURE_API_KEY, DEPLOYMENT_NAME)
    info_vals = _generar_contexto_valores(df)
    
    system_message = {
        "role": "system",
        "content": f"""
        Eres un analista experto en una app de Facturas.
        Tienes acceso a datos y herramientas.
        COLUMNAS DISPONIBLES: {', '.join(df.columns)}
        EJEMPLOS DE VALORES: {info_vals}
        
        INSTRUCCIONES:
        1. Para ocultar/mostrar columnas, usa 'gestionar_vista'.
        2. Para editar datos (ej. "cambia a Pagado las facturas 10, 20"), usa 'modificar_datos_masivo'.
        3. Para filtrar, usa 'ejecutar_filtro'. Si mencionan una persona, busca en 'Assignee'.
        4. Si dudas del nombre, usa 'examinar_datos_reales'.
        """
    }
    
    messages = [system_message, {"role": "user", "content": message}]
    
    final_text = ""
    rerun = False
    chart = None
    actions = []

    try:
        response = client.chat_completion(messages, tools=TOOLS_SCHEMA)
        response_msg = response.choices[0].message
        
        if response_msg.tool_calls:
            messages.append(response_msg)
            
            for tool_call in response_msg.tool_calls:
                fn_name = tool_call.function.name
                try: args = json.loads(tool_call.function.arguments)
                except: args = {}
                
                tool_output = "Hecho."
                
                # --- HERRAMIENTA: LECTURA ---
                if fn_name == "examinar_datos_reales":
                    preview = df.head(args.get("filas_maximas", 5)).to_csv(index=False)
                    tool_output = f"DATOS:\n{preview}"
                
                # --- HERRAMIENTA: GESTIONAR VISTA (COLUMNAS) ---
                elif fn_name == "gestionar_vista":
                    accion = args.get("accion")
                    cols_solicitadas = args.get("columnas", [])
                    all_cols = df.columns.tolist()
                    
                    # Validar nombres de columnas
                    target_cols = []
                    for c in cols_solicitadas:
                        match = find_best_match(c, all_cols)
                        if match: target_cols.append(match)
                    
                    current_vis = st.session_state.get('columnas_visibles', all_cols) or all_cols
                    
                    if accion == "reset":
                        st.session_state.columnas_visibles = all_cols
                        tool_output = "Vista restablecida (Todas las columnas)."
                        rerun = True
                    elif accion == "show_only":
                        if target_cols:
                            st.session_state.columnas_visibles = target_cols
                            tool_output = f"Vista cambiada. Solo veo: {target_cols}"
                            rerun = True
                        else: tool_output = "No encontré esas columnas."
                    elif accion == "hide":
                        new_vis = [c for c in current_vis if c not in target_cols]
                        if new_vis:
                            st.session_state.columnas_visibles = new_vis
                            tool_output = f"Ocultadas: {target_cols}"
                            rerun = True
                        else: tool_output = "No puedo ocultar todo."
                    elif accion == "show":
                        new_vis = list(set(current_vis + target_cols))
                        # Mantener orden original
                        st.session_state.columnas_visibles = [c for c in all_cols if c in new_vis]
                        tool_output = f"Mostrando: {target_cols}"
                        rerun = True

                # --- HERRAMIENTA: MODIFICACIÓN MASIVA (BULK EDIT) ---
                elif fn_name == "modificar_datos_masivo":
                    col_raw = args.get("columna")
                    val_new = args.get("valor_nuevo")
                    ids = args.get("ids_especificos", [])
                    r_start = args.get("rango_inicio")
                    r_end = args.get("rango_fin")
                    
                    # 1. Validar columna y valor (Auto-corrección)
                    target_col, target_val = validate_column_and_value(df, col_raw, val_new)
                    
                    if target_col:
                        count_mod = 0
                        # Modificar el DF en Session State directamente
                        df_edit = st.session_state.df_staging
                        
                        # A. Por IDs Específicos
                        if ids:
                            for i in ids:
                                # Intentamos limpiar el ID por si viene con comillas o espacios
                                clean_id = str(i).strip()
                                if clean_id in df_edit.index:
                                    df_edit.at[clean_id, target_col] = target_val
                                    count_mod += 1
                        
                        # B. Por Rango Numérico (1-based)
                        elif r_start is not None and r_end is not None:
                            # Convertimos a 0-based para iloc
                            start_idx = max(0, r_start - 1)
                            end_idx = min(len(df_edit), r_end)
                            
                            # Usamos iloc para posicion y obtenemos los indices reales
                            indices_to_mod = df_edit.iloc[start_idx:end_idx].index
                            for idx in indices_to_mod:
                                df_edit.at[idx, target_col] = target_val
                                count_mod += 1
                        
                        if count_mod > 0:
                            # Recalcular lógica de negocio tras edición
                            df_edit = apply_priority_rules(df_edit)
                            df_edit = recalculate_row_status(df_edit, lang)
                            st.session_state.df_staging = df_edit
                            
                            tool_output = f"✅ Modificadas {count_mod} filas. '{target_col}' ahora es '{target_val}'."
                            rerun = True
                        else:
                            tool_output = "⚠️ No encontré las filas especificadas (IDs o Rango inválido)."
                    else:
                        tool_output = f"❌ Error: La columna '{col_raw}' no existe."

                # --- HERRAMIENTA: FILTRO ---
                elif fn_name == "ejecutar_filtro":
                    raw_col = args.get("columna")
                    raw_val = args.get("valor")
                    
                    real_col, real_val = validate_column_and_value(df, raw_col, raw_val)
                    
                    if real_col:
                        st.session_state.filtros_activos.append({"columna": real_col, "valor": real_val})
                        rerun = True
                        actions.append({"label": f"Filtro: {real_val}", "type": "filter_exact", "col": real_col, "val": real_val})
                        tool_output = f"Filtro aplicado: {real_col} = '{real_val}'"
                    else:
                        tool_output = f"Error: Columna '{raw_col}' no encontrada."

                # --- HERRAMIENTA: GRÁFICO ---
                elif fn_name == "generar_grafico":
                    tipo = args.get("tipo", "bar")
                    col_x = args.get("eje_x")
                    col_y = args.get("eje_y")
                    
                    real_x, _ = validate_column_and_value(df, col_x, "")
                    real_y = None
                    if col_y: real_y, _ = validate_column_and_value(df, col_y, "")
                    
                    if real_x:
                        if real_y and real_y in df.columns:
                            df_copy = df.copy()
                            df_copy[real_y] = pd.to_numeric(df_copy[real_y], errors='coerce').fillna(0)
                            data = df_copy.groupby(real_x)[real_y].sum()
                            lbl_y = real_y
                        else:
                            data = df[real_x].value_counts().head(15)
                            lbl_y = "Cantidad"
                        
                        chart = {"type": tipo, "data": data, "title": f"Gráfico {real_x}", "x_label": real_x, "y_label": lbl_y}
                        tool_output = "Gráfico generado."
                    else:
                        tool_output = f"Error: Columna {col_x} no existe."

                # --- HERRAMIENTA: REGLAS ---
                elif fn_name == "crear_regla_prioridad":
                    clean_conds = []
                    for c in args.get("condiciones", []):
                        r_col, r_val = validate_column_and_value(df, c["columna"], c["valor"])
                        if r_col:
                            clean_conds.append({
                                "column": r_col,
                                "operator": c.get("operador", "contains"),
                                "value": r_val
                            })
                    
                    if clean_conds:
                        new_rule = {
                            "id": str(uuid.uuid4()), "enabled": True, "order": 5,
                            "priority": args.get("prioridad"), "reason": args.get("razon"),
                            "conditions": clean_conds
                        }
                        if 'priority_rules' not in st.session_state: st.session_state.priority_rules = []
                        st.session_state.priority_rules.append(new_rule)
                        
                        if st.session_state.df_staging is not None:
                            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                        
                        rerun = True
                        tool_output = f"Regla creada: {args.get('razon')}"
                    else:
                        tool_output = "Error validando columnas de la regla."

                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": fn_name, "content": str(tool_output)})

            final = client.chat_completion(messages, tools=None)
            final_text = final.choices[0].message.content
        else:
            final_text = response_msg.content

    except Exception as e:
        final_text = f"Error: {str(e)}"

    return final_text, rerun, chart, actions