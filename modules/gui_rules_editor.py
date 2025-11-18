# modules/gui_rules_editor.py
import streamlit as st
import pandas as pd
from modules.translator import get_text
from modules.audit_service import log_rule_changes
from modules.rules_service import apply_priority_rules, get_default_rules
import uuid
import copy

@st.dialog("Editor de Reglas")
def render_rules_editor(cols, auto_opts):
    st.info("Edite las reglas de negocio aquí. El orden importa: reglas con mayor número (ej. 100) se aplican al final.")
    
    if "rules_tmp" not in st.session_state:
        current = st.session_state.get('priority_rules', get_default_rules())
        st.session_state.rules_tmp = pd.DataFrame(current)
        st.session_state.rules_bkp = copy.deepcopy(current)

    edited = st.data_editor(
        st.session_state.rules_tmp, 
        num_rows="dynamic", 
        key="rules_grid",
        column_config={
            "order": st.column_config.NumberColumn("Orden (Ej. 20 Sistema, 100 Usuario)", min_value=1),
            "priority": st.column_config.SelectboxColumn("Prioridad", options=["🚩 Maxima Prioridad", "Alta", "Media", "Minima"])
        }
    )

    # Añadir regla CON ICONOS VISUALES
    with st.expander("Añadir Nueva Regla"):
        # 1. Preparar lista visual
        cols_visual = []
        for c in cols:
            if c in auto_opts and auto_opts[c]:
                cols_visual.append(f"{c} 📋")
            else:
                cols_visual.append(c)

        c_type_visual = st.selectbox("Columna", [""] + cols_visual)
        c_type = c_type_visual.replace(" 📋", "") # Limpiar
        
        # 2. Mostrar input adecuado
        opts = auto_opts.get(c_type, [])
        if opts:
             c_val = st.selectbox("Valor (Contiene...)", opts)
        else:
             c_val = st.text_input("Valor (Contiene...)")
             
        c_prio = st.selectbox("Asignar Prioridad", ["🚩 Maxima Prioridad", "Alta", "Media", "Minima"])
        c_reas = st.text_input("Razón (Explicación)")
        
        if st.button("Agregar Regla"):
            if c_type and c_val and c_prio and c_reas:
                new_r = {
                    "id": uuid.uuid4().hex, 
                    "enabled": True, 
                    "order": 100, 
                    "type": c_type, 
                    "value": c_val, 
                    "priority": c_prio, 
                    "reason": c_reas
                }
                st.session_state.rules_tmp = pd.concat([edited, pd.DataFrame([new_r])], ignore_index=True)
                st.rerun()
            else:
                st.error("Complete todos los campos.")

    st.markdown("---")
    reason = st.text_area("Razón del cambio (para auditoría)")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Guardar Cambios", type="primary", use_container_width=True):
            if not reason:
                st.error("Ingrese una razón para el cambio.")
            else:
                new_list = edited.to_dict('records')
                log_rule_changes(reason, st.session_state.rules_bkp, new_list)
                st.session_state.priority_rules = new_list
                
                if st.session_state.df_staging is not None:
                    st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                
                del st.session_state.rules_tmp
                del st.session_state.rules_bkp
                st.session_state.show_rules_editor = False
                st.rerun()

    with c2:
        if st.button("Cancelar", use_container_width=True):
            if "rules_tmp" in st.session_state: del st.session_state.rules_tmp
            if "rules_bkp" in st.session_state: del st.session_state.rules_bkp
            st.session_state.show_rules_editor = False
            st.rerun()