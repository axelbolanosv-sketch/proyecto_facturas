# modules/gui_rules_editor.py (VERSIÓN 4.0 - CORREGIDO BUG LÓGICO DE ESTADO)
# Renderiza el editor modal (st.dialog) para las reglas de negocio.
#
# --- CORRECCIÓN DE BUG LÓGICO (v4.0) ---
# Problema: Al editar (ej. un checkbox) o eliminar una fila y LUEGO
# presionar "Añadir Nueva Regla" (que causa un 'st.rerun()'),
# el 'st.data_editor' se recargaba con los datos de
# 'st.session_state.rules_editor_temp_df' (el estado original),
# perdiendo todas las ediciones y eliminaciones que no se habían guardado.
#
# Solución: La lógica de "Añadir Nueva Regla" ahora es más inteligente.
# 1. El 'st.data_editor' (fuente) es 'rules_editor_temp_df'.
# 2. El valor de retorno del editor es 'edited_df' (estado visual actual).
# 3. Al "Añadir Nueva Regla", el código toma 'edited_df' (que ya
#    contiene todas las ediciones/eliminaciones) como base.
# 4. Concatena la nueva fila a 'edited_df'.
# 5. Guarda este DataFrame combinado de nuevo en
#    'st.session_state.rules_editor_temp_df'.
# 6. Llama a 'st.rerun()'.
#
# Resultado: El editor se recarga con un estado que preserva
# las ediciones, las eliminaciones Y la nueva fila añadida.
# ---------------------------------------------------------------------

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
        all_columns_en (list): Lista de TODAS las columnas (en inglés)
                               del DataFrame.
        autocomplete_options (dict): Diccionario de opciones de autocompletado.
    """
    # (Línea de documentación interna)
    # Obtiene el idioma actual del estado de la sesión.
    lang = st.session_state.language
    
    # (Línea de documentación interna)
    # Muestra el texto de información/ayuda en la parte superior del modal.
    st.info(get_text(lang, "rules_editor_info"))

    # --- 1. GESTIÓN DE REGLAS EXISTENTES (CON DATA_EDITOR) ---
    
    st.markdown(f"**{get_text(lang, 'rules_editor_header')}**")
    
    # [INICIO] LÓGICA DE ESTADO (v3.8 - v4.0)
    
    # (Línea de documentación interna)
    # Comprueba si el estado temporal del editor ('rules_editor_temp_df') NO existe.
    if "rules_editor_temp_df" not in st.session_state:
        # (Línea de documentación interna)
        # Si no existe, es la primera vez que se abre el modal.
        # Carga las reglas desde el estado principal ('priority_rules').
        rules_list = st.session_state.get('priority_rules')
        if rules_list is None:
            rules_list = get_default_rules()
        
        # (Línea de documentación interna)
        # Crea el estado 'rules_editor_temp_df' como un DataFrame.
        # Este es el DataFrame que "alimentará" al editor.
        st.session_state.rules_editor_temp_df = pd.DataFrame(rules_list)
        
        # (Línea de documentación interna)
        # Almacena una copia de seguridad de las reglas originales
        # para la función "Cancelar".
        if 'rules_editor_original_rules' not in st.session_state:
            st.session_state.rules_editor_original_rules = copy.deepcopy(rules_list)

    # (Línea de documentación interna)
    # El 'st.data_editor' usa 'st.session_state.rules_editor_temp_df'
    # como su fuente de datos (argumento 'data').
    # Usa 'key="rules_editor_data"' para su gestión de estado interna.
    edited_df = st.data_editor(
        st.session_state.rules_editor_temp_df, # <-- DATO FUENTE
        key="rules_editor_data",               # <-- CLAVE DEL WIDGET
        num_rows="dynamic",
        column_config={
            "id": st.column_config.TextColumn("Rule ID", disabled=True),
            "enabled": st.column_config.CheckboxColumn("Activada"),
            "order": st.column_config.NumberColumn(
                "Orden",
                min_value=1,
                help=get_text(lang, 'rules_editor_order_help')
            ),
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
            "reason": st.column_config.TextColumn(
                "Razón (para el log)",
                required=True,
                help=get_text(lang, 'rules_editor_reason_help')
            )
        },
        hide_index=True,
        use_container_width=True
    )
    # [FIN] LÓGICA DE ESTADO

    st.markdown("---")

    # --- 2. AÑADIR NUEVA REGLA (SIN FORMULARIO) ---
    with st.expander(get_text(lang, "rules_add_new_header"), expanded=True):
        st.markdown(f"**{get_text(lang, 'rules_add_new_subheader')}**")
        
        # (Línea de documentación interna)
        # ... (Renderizado de inputs no cambia) ...
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
        submitted = st.button(
            get_text(lang, 'rules_add_new_btn'),
            key="add_rule_submit_btn"
        )
        
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
                    "order": 100,
                    "type": col_type,
                    "value": final_value,
                    "priority": col_priority,
                    "reason": col_reason
                }
                
                # [INICIO] CORRECCIÓN LÓGICA (v4.0)
                
                # (Línea de documentación interna)
                # Convierte la nueva regla (dict) en un DataFrame de una fila.
                new_rule_df = pd.DataFrame([new_rule])
                
                # (Línea de documentación interna)
                # 'edited_df' es el valor de retorno del data_editor.
                # Contiene TODAS las ediciones actuales (checks, deletes).
                # Usamos este DF como la base para concatenar.
                st.session_state.rules_editor_temp_df = pd.concat(
                    [edited_df, new_rule_df],
                    ignore_index=True
                )
                # [FIN] CORRECCIÓN LÓGICA
                
                message_placeholder.success(
                    get_text(lang, 'rules_add_success').format(val=final_value)
                )
                
                # (Línea de documentación interna)
                # Limpia los campos de "Añadir Nueva Regla".
                keys_to_delete = [
                    "add_rule_type", "add_rule_value_select", "add_rule_value_text",
                    "add_rule_priority", "add_rule_reason"
                ]
                for key in keys_to_delete:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # (Línea de documentación interna)
                # 'st.rerun()' recargará el modal. El editor leerá
                # 'rules_editor_temp_df', que ahora contiene
                # las ediciones, las eliminaciones Y la nueva fila.
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
        # (Línea de documentación interna)
        # Botón de Guardar (acción principal).
        if st.button(
            get_text(lang, "rules_editor_save_btn"),
            type="primary",
            use_container_width=True
        ):
            if not reason_for_change:
                st.error(get_text(lang, "rules_editor_reason_error"))
            else:
                
                # (Línea de documentación interna)
                # 'edited_df' es el valor de retorno del data_editor,
                # contiene el estado final con todas las ediciones.
                new_rules = edited_df.to_dict('records')
                
                old_rules = st.session_state.rules_editor_original_rules
                
                log_change(reason_for_change, old_rules, new_rules)
                
                # (Línea de documentación interna)
                # Guarda el estado del editor en el estado principal.
                st.session_state.priority_rules = new_rules
                
                # (Línea de documentación interna)
                # Recalcula el DataFrame principal.
                if st.session_state.df_staging is not None:
                    df_staging_copy = st.session_state.df_staging.copy()
                    st.session_state.df_staging = apply_priority_rules(
                        df_staging_copy
                    )
                
                # [INICIO] LIMPIEZA DE ESTADO (v3.8)
                st.session_state.show_rules_editor = False
                del st.session_state.rules_editor_original_rules
                del st.session_state.rules_editor_temp_df
                if "rules_editor_data" in st.session_state:
                    del st.session_state.rules_editor_data
                # [FIN] LIMPIEZA DE ESTADO
                
                st.toast(
                    get_text(lang, "rules_editor_save_success"),
                    icon="✅"
                )
                
                st.rerun()

    with col_cancel:
        # (Línea de documentación interna)
        # Botón para cancelar y descartar cambios.
        if st.button(
            get_text(lang, "rules_editor_cancel_btn"),
            use_container_width=True
        ):
            st.session_state.show_rules_editor = False
            
            # (Línea de documentación interna)
            # Revierte el estado principal a la copia de seguridad.
            st.session_state.priority_rules = (
                st.session_state.rules_editor_original_rules
            )
            
            # [INICIO] LIMPIEZA DE ESTADO (v3.8)
            del st.session_state.rules_editor_original_rules
            if 'rules_editor_temp_df' in st.session_state:
                del st.session_state.rules_editor_temp_df
            if 'rules_editor_data' in st.session_state:
                del st.session_state.rules_editor_data
            # [FIN] LIMPIEZA DE ESTADO
            
            st.rerun()

    # --- 4. DESCARGA DE LOG DE AUDITORÍA ---
    # (Esta sección no requería cambios)
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
