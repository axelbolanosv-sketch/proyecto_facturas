# modules/gui_chatbot.py
import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Interfaz del chatbot con Chips de Innovación (Anomalías, Top, Resumen).
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": "start_chat_msg", "chart": None}]

    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # 1. Historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                content = msg.get("content", "")
                # Traducción simple solo para mensajes de sistema conocidos
                display_text = get_text(lang, content) if content == "start_chat_msg" else content
                st.markdown(display_text)
                
                if msg.get("chart"):
                    chart_info = msg["chart"]
                    if chart_info["type"] == "bar":
                        st.caption(f"📈 {chart_info.get('title', '')}")
                        st.bar_chart(chart_info["data"], color="#004A99")

        # 2. Botones de Sugerencia (Chips) - ACTUALIZADOS PARA INNOVACIÓN
        st.markdown("###### 💡 Análisis Inteligente:")
        c1, c2, c3, c4 = st.columns(4)
        suggestion = None
        
        # Botón 1: La función "Forensic" (Lo más innovador)
        if c1.button("🕵️ Anomalías", key="chip_anom", use_container_width=True, help="Detectar montos inusuales automáticamente"):
            suggestion = "Analiza anomalías en los montos"
            
        # Botón 2: La función "Pareto" (Valor de negocio)
        if c2.button("🏆 Top Proveedores", key="chip_top", use_container_width=True, help="Ranking de proveedores por gasto"):
            suggestion = "Muestrame el Top de proveedores"
            
        # Botón 3: La función "Narrativa" (Ahorro de tiempo)
        if c3.button("📝 Resumen", key="chip_summary", use_container_width=True, help="Generar un resumen ejecutivo del estado actual"):
            suggestion = "Dame un resumen ejecutivo"
            
        # Botón 4: Gestión
        if c4.button("🔄 Resetear", key="chip_reset", use_container_width=True):
            suggestion = "Resetear todo"

        # 3. Input del Usuario
        user_input = st.chat_input(get_text(lang, "chat_placeholder"))
        final_prompt = suggestion if suggestion else user_input

        if final_prompt:
            # A. Usuario
            st.session_state.chat_history.append({"role": "user", "content": final_prompt, "chart": None})
            with st.chat_message("user"):
                st.markdown(final_prompt)

            # B. IA
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    time.sleep(0.6) 
                    
                    # Contexto de datos actual
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    # Procesamiento
                    response_txt, rerun_needed, chart_data = process_user_message(final_prompt, df_context, lang)
                    
                    # Respuesta
                    st.markdown(response_txt)
                    if chart_data:
                        st.caption(f"📈 {chart_data.get('title', '')}")
                        st.bar_chart(chart_data["data"], color="#004A99")
                    
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response_txt, 
                        "chart": chart_data
                    })
            
            if rerun_needed:
                st.rerun()