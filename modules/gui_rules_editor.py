# modules/gui_rules_editor.py (VERSIÓN 3.2 - CORREGIDO APIException)
# Renderiza el editor modal (st.dialog) para las reglas de negocio.
# - Soluciona el bug de StreamlitAPIException al limpiar el formulario.

import streamlit as st
import pandas as pd
from modules.translator import get_text
from modules.rules_service import (
    log_change, 
    apply_priority_rules, 
    get_audit_log_excel,
    get_default_rules
)
import uuid
import copy

@st.dialog(get_text("es", "rules_editor_title"))
def render_rules_editor(all_columns_en: list, autocomplete_options: dict):
    """
    Renderiza el modal para editar las reglas de prioridad.
    
    Args:
        all_columns_en (list): Lista de TODAS las columnas (en inglés) del DataFrame.
        autocomplete_options (dict): Diccionario de opciones de autocompletado.
    """
    lang = st.session_state.language
    st.info(get_text(lang, "rules_editor_info"))

    # --- 1. GESTIÓN DE REGLAS EXISTENTES (CON DATA_EDITOR) ---
    
    st.markdown(f"**{get_text(lang, 'rules_editor_header')}**")
    
    rules_list = st.session_state.get('priority_rules')
    if rules_list is None:
        rules_list = get_default_rules()
    
    if 'rules_editor_original_rules' not in st.session_state:
        st.session_state.rules_editor_original_rules = copy.deepcopy(rules_list)

    def _callback_rules_editor_changed():
        """Guarda los cambios del editor en el estado para que persistan."""
        st.session_state.priority_rules = st.session_state.rules_editor_data.to_dict('records')
        
        # [FIX] Aplicar reglas inmediatamente al editar la tabla
        if st.session_state.df_staging is not None:
            df_staging_copy = st.session_state.df_staging.copy()
            st.session_state.df_staging = apply_priority_rules(df_staging_copy)

    edited_df = st.data_editor(
        pd.DataFrame(rules_list),
        key="rules_editor_data",
        num_rows="dynamic",
        on_change=_callback_rules_editor_changed,
        column_config={
            "id": st.column_config.TextColumn("Rule ID", disabled=True),
            "enabled": st.column_config.CheckboxColumn("Activada"),
            "order": st.column_config.NumberColumn("Orden", min_value=1),
            "type": st.column_config.SelectboxColumn(
                "Tipo de Columna",
                options=all_columns_en,
                required=True
            ),
            "value": st.column_config.TextColumn("Valor (Contiene)", required=True),
            "priority": st.column_config.SelectboxColumn(
                "Asignar Prioridad",
                options=["🚩 Maxima Prioridad", "Alta", "Media", "Minima"],
                required=True
            ),
            "reason": st.column_config.TextColumn("Razón (para el log)", required=True)
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")

    # --- 2. AÑADIR NUEVA REGLA (SIN FORMULARIO) ---
    
    with st.expander(get_text(lang, "rules_add_new_header"), expanded=True):
        st.markdown(f"**{get_text(lang, 'rules_add_new_subheader')}**")
        
        col_type = st.selectbox(
            get_text(lang, 'rules_add_col_type'), 
            options=[""] + all_columns_en,
            key="add_rule_type"
        )
        
        col_type_from_state = st.session_state.get("add_rule_type", "")
        
        if col_type_from_state and col_type_from_state in autocomplete_options:
            options = [""] + sorted(autocomplete_options[col_type_from_state])
            st.selectbox(
                get_text(lang, 'rules_add_col_value_select'),
                options=options,
                key="add_rule_value_select"
            )
        else:
            st.text_input(
                get_text(lang, 'rules_add_col_value_text'),
                key="add_rule_value_text"
            )
        
        st.selectbox(
            get_text(lang, 'rules_add_priority'),
            options=["", "🚩 Maxima Prioridad", "Alta", "Media", "Minima"],
            key="add_rule_priority"
        )
        st.text_input(
            get_text(lang, 'rules_add_reason'),
            placeholder=get_text(lang, 'rules_add_reason_placeholder'),
            key="add_rule_reason"
        )
        
        message_placeholder = st.empty()
        
        submitted = st.button(get_text(lang, 'rules_add_new_btn'), key="add_rule_submit_btn")
        
        if submitted:
            col_type = st.session_state.add_rule_type
            col_priority = st.session_state.add_rule_priority
            col_reason = st.session_state.add_rule_reason
            
            final_value = None
            if col_type and col_type in autocomplete_options:
                final_value = st.session_state.add_rule_value_select
            else:
                final_value = st.session_state.add_rule_value_text
            
            if not col_type or not final_value or not col_priority or not col_reason:
                message_placeholder.error(get_text(lang, 'rules_add_error_all_fields'))
            else:
                new_rule = {
                    "id": f"rule_{uuid.uuid4().hex[:6]}",
                    "enabled": True,
                    "order": 100, # Por defecto es 100, se puede editar en la tabla
                    "type": col_type,
                    "value": final_value,
                    "priority": col_priority,
                    "reason": col_reason
                }
                
                current_rules = st.session_state.get('priority_rules', get_default_rules())
                current_rules.append(new_rule)
                st.session_state.priority_rules = current_rules
                
                if st.session_state.df_staging is not None:
                    df_staging_copy = st.session_state.df_staging.copy()
                    st.session_state.df_staging = apply_priority_rules(df_staging_copy)
                
                message_placeholder.success(get_text(lang, 'rules_add_success').format(val=final_value))
                
                # --- [INICIO] CORRECCIÓN StreamlitAPIException ---
                # En lugar de "st.session_state.add_rule_type = ''"
                # Borramos las claves. Streamlit las recreará en el rerun.
                keys_to_delete = [
                    "add_rule_type", "add_rule_value_select", "add_rule_value_text", 
                    "add_rule_priority", "add_rule_reason"
                ]
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                # --- [FIN] CORRECCIÓN StreamlitAPIException ---
                
                st.rerun() 

    st.markdown("---")
    
    # --- 3. AUDITORÍA Y GUARDADO FINAL ---
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
                new_rules = st.session_state.get('priority_rules', get_default_rules())
                old_rules = st.session_state.rules_editor_original_rules
                
                log_change(reason_for_change, old_rules, new_rules)
                
                st.session_state.priority_rules = new_rules
                
                if st.session_state.df_staging is not None:
                    df_staging_copy = st.session_state.df_staging.copy()
                    st.session_state.df_staging = apply_priority_rules(df_staging_copy)
                
                st.session_state.show_rules_editor = False
                del st.session_state.rules_editor_original_rules
                
                st.toast(get_text(lang, "rules_editor_save_success"), icon="✅")
                
                st.rerun()

    with col_cancel:
        if st.button(get_text(lang, "rules_editor_cancel_btn"), use_container_width=True):
            st.session_state.show_rules_editor = False
            # Revertir cambios no guardados
            st.session_state.priority_rules = st.session_state.rules_editor_original_rules
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