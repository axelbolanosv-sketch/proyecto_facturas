# modules/gui_chatbot.py
import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Interfaz del chatbot 7.0:
    - Historial Renombrable
    - Chips de Análisis (Incluyendo Top Global)
    - Acciones de Anomalías
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "start_chat_msg", 
            "chart": None, 
            "actions": [],
            "custom_label": None # Nuevo campo para el nombre personalizado
        })

    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # --- 1. RENDERIZADO DE HISTORIAL (Editable y Colapsable) ---
        history = st.session_state.chat_history
        user_indices = [i for i, msg in enumerate(history) if msg['role'] == 'user']
        
        # Mensaje inicial
        if history and history[0]['role'] == 'assistant':
            msg = history[0]
            content = msg.get("content", "")
            display_text = get_text(lang, content) if content == "start_chat_msg" else content
            with st.chat_message("assistant"):
                st.markdown(display_text)

        # Bloques de interacción
        if user_indices:
            last_user_idx = user_indices[-1]
            
            for i in user_indices:
                is_last_interaction = (i == last_user_idx)
                
                # Lógica del Título del Expander
                user_msg = history[i]
                if user_msg.get("custom_label"):
                    expander_label = f"📂 {user_msg['custom_label']}"
                else:
                    content_preview = user_msg['content'][:40] + "..." if len(user_msg['content']) > 40 else user_msg['content']
                    expander_label = f"🗣️ {content_preview}"
                
                # Renderizar Expander
                with st.expander(expander_label, expanded=is_last_interaction):
                    
                    # --- NUEVO: CAMPO PARA RENOMBRAR ---
                    c_edit, _ = st.columns([0.7, 0.3])
                    new_label = c_edit.text_input(
                        "🏷️ Renombrar esta consulta:", 
                        value=user_msg.get("custom_label", ""), 
                        placeholder="Ej: Análisis de Anomalías",
                        key=f"rename_{i}"
                    )
                    
                    if new_label != user_msg.get("custom_label", ""):
                        history[i]["custom_label"] = new_label
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # 1. Mensaje Usuario
                    with st.chat_message("user"):
                        st.markdown(user_msg['content'])
                    
                    # 2. Respuestas del Asistente
                    next_user = user_indices[user_indices.index(i) + 1] if user_indices.index(i) + 1 < len(user_indices) else len(history)
                    
                    for j in range(i + 1, next_user):
                        bot_msg = history[j]
                        if bot_msg['role'] == 'assistant':
                            with st.chat_message("assistant"):
                                st.markdown(bot_msg['content'])
                                
                                if bot_msg.get("chart"):
                                    c_info = bot_msg["chart"]
                                    st.caption(f"📈 {c_info.get('title','')}")
                                    st.bar_chart(c_info["data"], color="#004A99")
                                
                                if bot_msg.get("actions"):
                                    for idx, act in enumerate(bot_msg["actions"]):
                                        btn_key = f"act_{j}_{idx}"
                                        if st.button(act['label'], key=btn_key):
                                            if act['type'] == 'filter_numeric':
                                                # Crea una regla de prioridad para filtrar
                                                new_rule_id = f"auto_{int(time.time())}"
                                                st.session_state.priority_rules.append({
                                                    "id": new_rule_id,
                                                    "enabled": True, "order": 5, 
                                                    "priority": "🚩 Maxima Prioridad", 
                                                    "reason": "Filtro Anomalía Chatbot", # Nombre clave para el filtro
                                                    "conditions": [{"column": act['col'], "operator": act['op'], "value": act['val']}]
                                                })
                                                st.toast("✅ Regla de anomalía aplicada. Usa el filtro lateral para verla.")
                                                st.rerun()
                                            
                                            elif act['type'] == 'filter_exact':
                                                st.session_state.filtros_activos.append({"columna": act['col'], "valor": act['val']})
                                                st.rerun()

        # --- 2. CHIPS / BOTONES (Restaurados y Mejorados) ---
        st.divider()
        st.markdown("###### 💡 Acciones Rápidas:")
        
        # Fila 1: Análisis (Incluye tu Top Global)
        c1, c2, c3 = st.columns(3)
        suggestion = None
        
        if c1.button("🕵️ Detectar Anomalías", use_container_width=True):
            suggestion = "Analiza anomalías en los montos"
        
        # ¡AQUÍ ESTÁ TU BOTÓN DE TOP GLOBAL!
        if c2.button("🏆 Top Proveedores", use_container_width=True):
            suggestion = "Muestrame el Top de proveedores"
            
        if c3.button("📝 Resumen Ejecutivo", use_container_width=True):
            suggestion = "Dame un resumen ejecutivo"

        # Fila 2: Gráficos y Gestión
        c4, c5, c6, c7 = st.columns(4)
        if c4.button("📈 Estatus", use_container_width=True): suggestion = "Gráfico de Estado"
        if c5.button("📈 Prioridad", use_container_width=True): suggestion = "Gráfico de Prioridad"
        if c6.button("🔄 Reset", use_container_width=True): suggestion = "Resetear todo"
        # Un botón extra útil
        if c7.button("❓ Ayuda", use_container_width=True): suggestion = "Ayuda"

        # --- 3. INPUT USUARIO ---
        user_input = st.chat_input(get_text(lang, "chat_placeholder"))
        final_prompt = suggestion if suggestion else user_input

        if final_prompt:
            st.session_state.chat_history.append({"role": "user", "content": final_prompt, "custom_label": None})
            
            with st.chat_message("user"):
                st.markdown(final_prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    time.sleep(0.5)
                    
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    resp_txt, rerun, chart, actions = process_user_message(final_prompt, df_context, lang)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": resp_txt, 
                        "chart": chart,
                        "actions": actions
                    })
            st.rerun()