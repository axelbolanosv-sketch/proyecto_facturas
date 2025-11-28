# modules/gui_chatbot.py
"""
Módulo de Interfaz Gráfica del Chatbot (Versión UX Mejorada).

Cambios:
1. "Clean UI": El historial antiguo se agrupa en un solo bloque colapsable.
2. Solo la interacción actual se muestra abierta por defecto.
3. Botones de acción y feedback visual mejorado.
"""

import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """Renderiza la interfaz del Chatbot."""
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": get_text(lang, "start_chat_msg"),
            "chart": None, "actions": []
        })

    # --- CONTENEDOR PRINCIPAL ---
    with st.container():
        st.markdown(f"### {get_text(lang, 'chat_title')}")
        
        # 1. HISTORIAL (Colapsado para no molestar)
        if len(st.session_state.chat_history) > 2:
            with st.expander("📜 Historial de conversación (Clic para ver)", expanded=False):
                # Mostramos todos menos los últimos 2 (la última Q y A)
                for msg in st.session_state.chat_history[:-2]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        if msg.get("chart"):
                            st.caption(f"📊 {msg['chart'].get('title')}")
                            st.bar_chart(msg["chart"]["data"])

        # 2. INTERACCIÓN ACTUAL (Siempre visible)
        # Tomamos los últimos mensajes para mostrarlos frescos
        recent_msgs = st.session_state.chat_history[-2:] if len(st.session_state.chat_history) >= 2 else st.session_state.chat_history
        
        for msg in recent_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Renderizar Gráficos si existen
                if msg.get("chart"):
                    chart_data = msg["chart"]
                    st.caption(f"📈 {chart_data.get('title', 'Gráfico')}")
                    # Soporte simple para tipos
                    if chart_data.get("type") == "line":
                        st.line_chart(chart_data["data"])
                    else:
                        st.bar_chart(chart_data["data"])

                # Renderizar Botones de Acción
                if msg.get("actions"):
                    cols = st.columns(len(msg["actions"]))
                    for idx, act in enumerate(msg["actions"]):
                        if cols[idx].button(act['label'], key=f"btn_{len(st.session_state.chat_history)}_{idx}"):
                            if act['type'] == 'filter_exact':
                                st.session_state.filtros_activos.append({
                                    "columna": act['col'], "valor": act['val']
                                })
                                st.rerun()
                            elif act['type'] == 'filter_numeric':
                                st.session_state.filtros_activos.append({
                                    "columna": act['col'], "valor": act['val'], "operator": act['op']
                                })
                                st.rerun()

    st.divider()

    # --- 3. INPUT Y SUGERENCIAS ---
    # Chips de sugerencia rápida
    s1, s2, s3, s4 = st.columns(4)
    if s1.button("🔍 Anomalías", use_container_width=True):
        prompt = "Analiza anomalías en los montos"
    elif s2.button("🏆 Top Proveedores", use_container_width=True):
        prompt = "Muestrame el Top de proveedores"
    elif s3.button("📊 Resumen", use_container_width=True):
        prompt = "Dame un resumen ejecutivo"
    elif s4.button("🧹 Limpiar Filtros", use_container_width=True):
        prompt = "Borrar filtros"
    else:
        prompt = None

    # Input de texto
    user_input = st.chat_input(get_text(lang, "chat_placeholder"))
    
    if prompt: user_input = prompt # Si usó botón, sobrescribimos

    if user_input:
        # Añadir usuario al historial
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Procesar con IA
        with st.spinner("🤖 Analizando..."):
            # Contexto de datos filtrados
            df_context = df_staging
            if st.session_state.filtros_activos:
                df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

            # Llamada al cerebro
            resp_txt, rerun, chart, actions = process_user_message(user_input, df_context, lang)
            
            # Añadir respuesta al historial
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": resp_txt, 
                "chart": chart, 
                "actions": actions
            })
            
            if rerun:
                st.rerun()
            else:
                # Forzar actualización pequeña para mostrar el nuevo mensaje
                time.sleep(0.1)
                st.rerun()