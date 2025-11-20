# modules/gui_chatbot.py
import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Interfaz del chatbot 6.0 con Historial Colapsable y Acciones Reales.
    """
    # Inicializar historial con estructura para gráficos y acciones
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        # Mensaje inicial (sin expander)
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "start_chat_msg", 
            "chart": None, 
            "actions": []
        })

    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # --- 1. RENDERIZADO DE HISTORIAL (Colapsable) ---
        # Lógica: Agrupar mensajes en bloques (Usuario + Asistente)
        # Los bloques antiguos van en expanders cerrados. El último bloque queda abierto.
        
        history = st.session_state.chat_history
        
        # Identificar índices de mensajes de usuario para agrupar
        user_indices = [i for i, msg in enumerate(history) if msg['role'] == 'user']
        
        # Renderizar mensaje inicial (siempre visible o en su propio bloque)
        if history and history[0]['role'] == 'assistant':
            # El mensaje de bienvenida no se colapsa o se pone al principio
            msg = history[0]
            content = msg.get("content", "")
            display_text = get_text(lang, content) if content == "start_chat_msg" else content
            with st.chat_message("assistant"):
                st.markdown(display_text)

        # Renderizar pares de interacción (Usuario -> Asistente)
        # Si hay mensajes de usuario, los procesamos
        if user_indices:
            last_user_idx = user_indices[-1]
            
            for i in user_indices:
                is_last_interaction = (i == last_user_idx)
                
                # Título del bloque
                user_msg_content = history[i]['content']
                short_title = (user_msg_content[:40] + '...') if len(user_msg_content) > 40 else user_msg_content
                expander_label = f"🗣️ {short_title}"
                
                # El último mensaje se muestra abierto (expanded=True), los anteriores cerrados
                with st.expander(expander_label, expanded=is_last_interaction):
                    
                    # 1. Mensaje Usuario
                    with st.chat_message("user"):
                        st.markdown(history[i]['content'])
                    
                    # 2. Mensaje(s) Asistente siguientes (hasta el próximo usuario)
                    # Normalmente es 1 respuesta, pero el código es robusto por si hay más
                    next_user = user_indices[user_indices.index(i) + 1] if user_indices.index(i) + 1 < len(user_indices) else len(history)
                    
                    for j in range(i + 1, next_user):
                        bot_msg = history[j]
                        if bot_msg['role'] == 'assistant':
                            with st.chat_message("assistant"):
                                st.markdown(bot_msg['content'])
                                
                                # Gráfico
                                if bot_msg.get("chart"):
                                    c_info = bot_msg["chart"]
                                    st.caption(f"📈 {c_info.get('title','')}")
                                    st.bar_chart(c_info["data"], color="#004A99")
                                
                                # ACCIONES (BOTONES REALES)
                                if bot_msg.get("actions"):
                                    for idx, act in enumerate(bot_msg["actions"]):
                                        # Clave única para el botón basada en el índice del mensaje
                                        btn_key = f"act_{j}_{idx}"
                                        if st.button(act['label'], key=btn_key):
                                            # EJECUTAR ACCIÓN
                                            if act['type'] == 'filter_numeric':
                                                # Caso especial para reglas manuales complejas como anomalías
                                                # Añadimos una "regla temporal" o un filtro avanzado
                                                # Por simplicidad, usamos el sistema de reglas de prioridad para marcar
                                                pass 
                                                # OJO: El sistema de filtros actual es simple (string contains).
                                                # Para soportar "> valor", necesitamos un truco o mejorar filtros.
                                                # TRUCO RÁPIDO: Crear una regla de prioridad temporal
                                                st.session_state.priority_rules.append({
                                                    "id": f"temp_{int(time.time())}",
                                                    "enabled": True, "order": 1, 
                                                    "priority": "🚩 Maxima Prioridad", 
                                                    "reason": "Filtro Anomalía Chatbot",
                                                    "conditions": [{"column": act['col'], "operator": act['op'], "value": act['val']}]
                                                })
                                                st.toast("✅ Filtro de anomalía aplicado como Regla de Prioridad.")
                                                st.rerun()
                                            
                                            elif act['type'] == 'filter_exact':
                                                st.session_state.filtros_activos.append({"columna": act['col'], "valor": act['val']})
                                                st.rerun()

        # --- 2. CHIPS / SUGERENCIAS RÁPIDAS ---
        st.divider()
        st.caption("Sugerencias de Análisis:")
        c1, c2, c3, c4, c5 = st.columns(5)
        suggestion = None
        
        # Botones de Gráficos por Columna (Lo que pediste)
        if c1.button("📈 Estatus", use_container_width=True): suggestion = "Gráfico de Estado"
        if c2.button("📈 Proveedor", use_container_width=True): suggestion = "Gráfico de Proveedores"
        if c3.button("📈 Prioridad", use_container_width=True): suggestion = "Gráfico de Prioridad"
        
        # Botones de Inteligencia
        if c4.button("🕵️ Anomalías", use_container_width=True): suggestion = "Detectar anomalías en montos"
        if c5.button("🔄 Reset", use_container_width=True): suggestion = "Resetear todo"

        # --- 3. INPUT USUARIO ---
        user_input = st.chat_input(get_text(lang, "chat_placeholder"))
        final_prompt = suggestion if suggestion else user_input

        if final_prompt:
            # Guardar usuario
            st.session_state.chat_history.append({"role": "user", "content": final_prompt})
            
            # Procesar (sin renderizar aquí, se renderiza en el rerun por el bucle de arriba)
            # Pero necesitamos mostrar el spinner una vez
            with st.chat_message("user"):
                st.markdown(final_prompt)
                
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    time.sleep(0.5)
                    
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    # Obtener respuesta con acciones
                    resp_txt, rerun, chart, actions = process_user_message(final_prompt, df_context, lang)
                    
                    # Guardar en historial
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": resp_txt, 
                        "chart": chart,
                        "actions": actions
                    })
            
            st.rerun()