# modules/gui_chatbot.py
"""
Módulo de Interfaz Gráfica del Chatbot.

Renderiza el asistente virtual en la interfaz de usuario.
Características:
1. Historial de chat persistente y editable (renombrar consultas).
2. Renderizado de gráficos embebidos en el chat.
3. Botones de "Acción Rápida" (Chips) para comandos comunes.
4. Ejecución de acciones sugeridas (ej. aplicar filtros automáticos).
"""

import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Renderiza la interfaz completa del Chatbot.

    Args:
        lang (str): Idioma actual de la aplicación.
        df_staging (pd.DataFrame): DataFrame actual para el contexto de las respuestas.
    """
    # Inicialización segura del historial
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "start_chat_msg", 
            "chart": None, 
            "actions": [],
            "custom_label": None 
        })

    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # --- 1. RENDERIZADO DE HISTORIAL ---
        history = st.session_state.chat_history
        user_indices = [i for i, msg in enumerate(history) if msg['role'] == 'user']
        
        # Mensaje inicial (Bienvenida)
        if history and history[0]['role'] == 'assistant':
            msg = history[0]
            content = msg.get("content", "")
            # Traducir mensaje de bienvenida si es la clave por defecto
            display_text = get_text(lang, content) if content == "start_chat_msg" else content
            with st.chat_message("assistant"):
                st.markdown(display_text)

        # Renderizado de Bloques de Interacción (Usuario + Respuesta Bot)
        if user_indices:
            last_user_idx = user_indices[-1]
            
            for i in user_indices:
                is_last_interaction = (i == last_user_idx)
                user_msg = history[i]
                
                # Título del Expander (Personalizado o Preview del mensaje)
                if user_msg.get("custom_label"):
                    expander_label = f"📂 {user_msg['custom_label']}"
                else:
                    content_preview = user_msg['content'][:40] + "..." if len(user_msg['content']) > 40 else user_msg['content']
                    expander_label = f"🗣️ {content_preview}"
                
                # Cada interacción se agrupa en un expander para mantener limpieza visual
                with st.expander(expander_label, expanded=is_last_interaction):
                    # Feature: Renombrar historial
                    c_edit, _ = st.columns([0.7, 0.3])
                    new_label = c_edit.text_input(
                        get_text(lang, "chat_rename_label"), 
                        value=user_msg.get("custom_label", ""), 
                        placeholder=get_text(lang, "chat_rename_placeholder"),
                        key=f"rename_{i}_{lang}" # Key dinámica para forzar redibujado al cambiar idioma
                    )
                    
                    if new_label != user_msg.get("custom_label", ""):
                        history[i]["custom_label"] = new_label
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # Mensaje del Usuario
                    with st.chat_message("user"):
                        st.markdown(user_msg['content'])
                    
                    # Encontrar las respuestas del bot asociadas a este mensaje de usuario
                    next_user = user_indices[user_indices.index(i) + 1] if user_indices.index(i) + 1 < len(user_indices) else len(history)
                    
                    for j in range(i + 1, next_user):
                        bot_msg = history[j]
                        if bot_msg['role'] == 'assistant':
                            with st.chat_message("assistant"):
                                st.markdown(bot_msg['content'])
                                
                                # Renderizar Gráfico si existe
                                if bot_msg.get("chart"):
                                    c_info = bot_msg["chart"]
                                    st.caption(f"📈 {c_info.get('title','')}")
                                    st.bar_chart(c_info["data"], color="#004A99")
                                
                                # Renderizar Botones de Acción si existen
                                if bot_msg.get("actions"):
                                    for idx, act in enumerate(bot_msg["actions"]):
                                        btn_key = f"act_{j}_{idx}_{lang}"
                                        if st.button(act['label'], key=btn_key):
                                            # Acción: Crear regla automática
                                            if act['type'] == 'filter_numeric':
                                                new_rule_id = f"auto_{int(time.time())}"
                                                st.session_state.priority_rules.append({
                                                    "id": new_rule_id, "enabled": True, "order": 5, 
                                                    "priority": "🚩 Maxima Prioridad", 
                                                    "reason": "Filtro Chatbot", 
                                                    "conditions": [{"column": act['col'], "operator": act['op'], "value": act['val']}]
                                                })
                                                st.toast("✅ Regla aplicada.")
                                                st.rerun()
                                            # Acción: Aplicar filtro simple
                                            elif act['type'] == 'filter_exact':
                                                st.session_state.filtros_activos.append({"columna": act['col'], "valor": act['val']})
                                                st.rerun()

        # --- 2. CHIPS / BOTONES RÁPIDOS (ACCIONES PREDEFINIDAS) ---
        st.divider()
        st.markdown(f"###### {get_text(lang, 'chat_actions_header')}")
        
        c1, c2, c3 = st.columns(3)
        suggestion = None
        
        # Botones de primera fila (Análisis)
        if c1.button(get_text(lang, "chip_anomalies"), key=f"chip_ano_{lang}", use_container_width=True):
            suggestion = get_text(lang, "prompt_anomalies")
        
        if c2.button(get_text(lang, "chip_top_vendors"), key=f"chip_top_{lang}", use_container_width=True):
            suggestion = get_text(lang, "prompt_top_vendors")
            
        if c3.button(get_text(lang, "chip_summary"), key=f"chip_sum_{lang}", use_container_width=True):
            suggestion = get_text(lang, "prompt_summary")

        # Botones de segunda fila (Gráficos y Utilidad)
        c4, c5, c6, c7 = st.columns(4)
        if c4.button(get_text(lang, "chip_status"), key=f"chip_sta_{lang}", use_container_width=True): 
            suggestion = get_text(lang, "prompt_chart_status")
        if c5.button(get_text(lang, "chip_priority"), key=f"chip_prio_{lang}", use_container_width=True): 
            suggestion = get_text(lang, "prompt_chart_prio")
        if c6.button(get_text(lang, "chip_reset"), key=f"chip_rst_{lang}", use_container_width=True): 
            suggestion = get_text(lang, "prompt_reset")
        if c7.button(get_text(lang, "chip_help"), key=f"chip_hlp_{lang}", use_container_width=True): 
            suggestion = get_text(lang, "prompt_help")

        # --- 3. INPUT DE USUARIO ---
        user_input = st.chat_input(get_text(lang, "chat_placeholder"))
        final_prompt = suggestion if suggestion else user_input

        # Procesamiento del input
        if final_prompt:
            st.session_state.chat_history.append({"role": "user", "content": final_prompt, "custom_label": None})
            
            # Feedback visual inmediato
            with st.chat_message("user"):
                st.markdown(final_prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    time.sleep(0.5) # Simulación de pensamiento (UX)
                    
                    # Determinar el contexto de datos (¿Usamos filtros activos?)
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    # Llamada a la lógica del bot
                    resp_txt, rerun, chart, actions = process_user_message(final_prompt, df_context, lang)
                    
                    # Guardar respuesta en historial
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": resp_txt, "chart": chart, "actions": actions
                    })
            st.rerun()