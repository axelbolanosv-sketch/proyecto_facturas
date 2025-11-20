# modules/gui_chatbot.py
"""
Módulo de interfaz gráfica para el Chatbot.
Renderiza el historial de chat y gestiona la entrada del usuario.
"""

import streamlit as st
import time
from modules.translator import get_text
from modules.chatbot_logic import process_user_message
from modules.filters import aplicar_filtros_dinamicos

def render_chatbot(lang: str, df_staging):
    """
    Renderiza la interfaz del chatbot en un expander.
    
    Args:
        lang (str): Idioma actual ('es' o 'en').
        df_staging (pd.DataFrame): DataFrame con los datos actuales.
    """
    # Inicializar historial si no existe (doble check de seguridad)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{"role": "assistant", "content": "start_chat_msg"}]

    # Usamos un expander para que el chat no ocupe espacio si no se usa
    with st.expander(get_text(lang, "chat_title"), expanded=False):
        
        # 1. Mostrar historial de mensajes previos
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                # Si es el mensaje de bienvenida (clave), lo traducimos. Si es texto normal, se muestra tal cual.
                content_display = get_text(lang, msg["content"]) if msg["content"] == "start_chat_msg" else msg["content"]
                st.markdown(content_display)

        # 2. Capturar nueva entrada del usuario
        if prompt := st.chat_input(get_text(lang, "chat_placeholder")):
            # A. Mostrar mensaje del usuario inmediatamente
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # B. Procesar respuesta del asistente
            with st.chat_message("assistant"):
                with st.spinner(get_text(lang, "chat_thinking")):
                    # Simulación de "pensamiento" para mejorar UX (Experiencia de Usuario)
                    time.sleep(0.8) 
                    
                    # Determinar el contexto de datos:
                    # Si hay filtros activos, la IA debe "ver" solo lo filtrado, no todo el dataset.
                    df_context = df_staging
                    if st.session_state.filtros_activos:
                        df_context = aplicar_filtros_dinamicos(df_staging, st.session_state.filtros_activos)

                    # Llamada al cerebro lógico
                    response_txt, rerun_needed = process_user_message(prompt, df_context, lang)
                    
                    # Mostrar y guardar respuesta
                    st.markdown(response_txt)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_txt})
            
            # C. Recargar si la IA aplicó un filtro o limpió datos
            if rerun_needed:
                st.rerun()