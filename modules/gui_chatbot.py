# modules/gui_chatbot.py
import streamlit as st
import time
import pandas as pd
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Interfaz del chatbot con soporte para Gráficos y Sugerencias Rápidas.
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": "start_chat_msg", "chart": None}]

    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # 1. Historial
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                # Texto
                content = msg.get("content", "")
                display_text = get_text(lang, content) if content == "start_chat_msg" else content
                st.markdown(display_text)
                
                # Gráfico (si existe en el mensaje)
                if msg.get("chart"):
                    chart_info = msg["chart"]
                    if chart_info["type"] == "bar":
                        st.caption(f"📈 {chart_info.get('title', '')}")
                        st.bar_chart(chart_info["data"], color="#004A99") # Azul corporativo

        # 2. Botones de Sugerencia (Chips) - Usamos columnas para simular chips
        # Esto hace que la demo sea muy fluida, el jefe solo hace clic
        st.markdown("###### Sugerencias rápidas:")
        c1, c2, c3, c4 = st.columns(4)
        suggestion = None
        
        if c1.button("📊 Gráfico Estatus", key="chip_status", use_container_width=True):
            suggestion = "Grafica la distribución por Estado"
        if c2.button("💰 Total Monto", key="chip_total", use_container_width=True):
            suggestion = "Dame la suma total del monto"
        if c3.button("🔢 Conteo", key="chip_count", use_container_width=True):
            suggestion = "¿Cuántas facturas hay?"
        if c4.button("🔄 Resetear", key="chip_reset", use_container_width=True):
            suggestion = "Borrar todos los filtros"

        # 3. Input del Usuario (Texto o Click de Botón)
        user_input = st.chat_input(get_text(lang, "chat_placeholder"))
        
        # Prioridad: Si hizo clic en un botón, usamos eso. Si no, lo que escribió.
        final_prompt = suggestion if suggestion else user_input

        if final_prompt:
            # A. Mostrar Usuario
            st.session_state.chat_history.append({"role": "user", "content": final_prompt, "chart": None})
            with st.chat_message("user"):
                st.markdown(final_prompt)

            # B. Procesar Asistente
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    time.sleep(0.6) # Pequeño delay para efecto
                    
                    # Contexto de datos
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    # LLAMADA LÓGICA (Ahora desempaquetamos 3 valores)
                    response_txt, rerun_needed, chart_data = process_user_message(final_prompt, df_context, lang)
                    
                    # Mostrar Texto
                    st.markdown(response_txt)
                    
                    # Mostrar Gráfico (si aplica)
                    if chart_data:
                        st.caption(f"📈 {chart_data.get('title', '')}")
                        st.bar_chart(chart_data["data"], color="#004A99")
                    
                    # Guardar en historial
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response_txt, 
                        "chart": chart_data # Guardamos el objeto de datos del gráfico
                    })
            
            if rerun_needed:
                st.rerun()