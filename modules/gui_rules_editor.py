# modules/gui_rules_editor.py (CORREGIDO)
# Renderiza el editor modal (st.dialog) para las reglas de negocio.

import streamlit as st
import pandas as pd
from modules.translator import get_text
# --- [INICIO] MODIFICACIÓN ---
# Importamos las reglas por defecto y el motor de reglas
from modules.rules_service import (
    log_change, 
    apply_priority_rules, 
    get_audit_log_excel,
    get_default_rules # <--- Importar la función de reglas por defecto
)
# --- [FIN] MODIFICACIÓN ---
import uuid # Para crear IDs de reglas únicas

@st.dialog(get_text("es", "rules_editor_title"))
def render_rules_editor():
    """
    Renderiza el modal para editar las reglas de prioridad.
    """
    lang = st.session_state.language
    
    st.info(get_text(lang, "rules_editor_info"))
    
    rule_types = ["Pay Group", "Vendor Name", "Status", "Assignee"]
    priority_values = ["🚩 Maxima Prioridad", "Alta", "Media", "Minima"]

    # --- [INICIO] CORRECCIÓN DEL BUG ---
    # Si 'priority_rules' no está en el estado (o es None),
    # NO usar una lista vacía []. Usar las reglas por defecto.
    rules_list = st.session_state.get('priority_rules')
    if rules_list is None:
        rules_list = get_default_rules()
        st.session_state.priority_rules = rules_list # Asegurarse de que el estado se inicialice
    # --- [FIN] CORRECCIÓN DEL BUG ---
        
    rules_df = pd.DataFrame(rules_list)

    if 'rules_editor_original_rules' not in st.session_state:
        st.session_state.rules_editor_original_rules = rules_list.copy()

    st.markdown(f"**{get_text(lang, 'rules_editor_header')}**")
    
    edited_df = st.data_editor(
        rules_df,
        key="rules_editor_data",
        num_rows="dynamic",
        column_config={
            "id": st.column_config.TextColumn(
                "Rule ID", 
                disabled=True, 
                default=f"rule_{uuid.uuid4().hex[:6]}"
            ),
            "enabled": st.column_config.CheckboxColumn(
                "Activada",
                default=True
            ),
            "order": st.column_config.NumberColumn(
                "Orden",
                help=get_text(lang, "rules_editor_order_help"),
                default=100,
                min_value=1,
                max_value=999
            ),
            "type": st.column_config.SelectboxColumn(
                "Tipo de Columna",
                options=rule_types,
                required=True
            ),
            "value": st.column_config.TextColumn(
                "Valor (Contiene)",
                required=True
            ),
            "priority": st.column_config.SelectboxColumn(
                "Asignar Prioridad",
                options=priority_values,
                required=True
            ),
            "reason": st.column_config.TextColumn(
                "Razón (para el log)",
                help=get_text(lang, "rules_editor_reason_help"),
                required=True
            )
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")
    
    st.markdown(f"**{get_text(lang, 'rules_editor_audit_header')}**")
    
    reason_for_change = st.text_area(
        get_text(lang, "rules_editor_reason_input"),
        key="rules_editor_reason_text",
        placeholder=get_text(lang, "rules_editor_reason_placeholder")
    )

    col_save, col_cancel = st.columns(2)

    with col_save:
        if st.button(get_text(lang, "rules_editor_save_btn"), type="primary", use_container_width=True):
            if not reason_for_change:
                st.error(get_text(lang, "rules_editor_reason_error"))
            else:
                new_rules = edited_df.to_dict('records')
                old_rules = st.session_state.rules_editor_original_rules
                
                log_change(reason_for_change, old_rules, new_rules)
                
                st.session_state.priority_rules = new_rules
                
                if st.session_state.df_staging is not None:
                    # Aplicamos las reglas y sobrescribimos el df_staging
                    df_staging_copy = st.session_state.df_staging.copy()
                    st.session_state.df_staging = apply_priority_rules(df_staging_copy)
                
                st.session_state.show_rules_editor = False
                del st.session_state.rules_editor_original_rules
                st.toast(get_text(lang, "rules_editor_save_success"), icon="✅")
                st.rerun()

    with col_cancel:
        if st.button(get_text(lang, "rules_editor_cancel_btn"), use_container_width=True):
            st.session_state.show_rules_editor = False
            del st.session_state.rules_editor_original_rules
            st.rerun()

    st.markdown("---")
    st.markdown(f"**{get_text(lang, 'audit_log_header')}**")
    st.info(get_text(lang, "audit_log_info"))
    
    log_data = get_audit_log_excel()
    st.download_button(
        label=get_text(lang, "audit_log_download_btn"),
        data=log_data,
        file_name="log_auditoria_prioridad.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )