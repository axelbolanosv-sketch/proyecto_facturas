# modules/gui_rules_editor.py
# VERSIÓN 14.0: ARCHIVO COMPLETO Y RESTAURADO
import streamlit as st
import pandas as pd
import uuid
import copy
from modules.audit_service import log_rule_changes
from modules.rules_service import apply_priority_rules, get_default_rules
from modules.translator import get_text

def _get_operator_labels(lang: str) -> dict:
    """
    Devuelve las etiquetas descriptivas de los operadores.
    """
    if lang == "en":
        return {
            "contains": "🔍 Contains | Partial match (e.g. 'Apple' in 'Apple Inc')",
            "is": "🟰 Is equal to | Exact match",
            "is_not": "🚫 Is not equal to | Everything except this",
            "starts_with": "🔤 Starts with | Text starting with...",
            ">": "📈 Greater than (>) | Number is strictly higher",
            "<": "📉 Less than (<) | Number is strictly lower",
            ">=": "📐 Greater or equal (>=) | Number is higher or equal",
            "<=": "📏 Less or equal (<=) | Number is lower or equal"
        }
    else: # Default Español
        return {
            "contains": "🔍 Contiene | Búsqueda parcial (Ej. 'Sol' en 'Girasol')",
            "is": "🟰 Es igual a | Coincidencia exacta",
            "is_not": "🚫 No es igual a | Todo menos este valor",
            "starts_with": "🔤 Empieza con | La celda inicia con...",
            ">": "📈 Mayor que (>) | Comparación numérica",
            "<": "📉 Menor que (<) | Comparación numérica",
            ">=": "📐 Mayor o igual (>=) | Comparación numérica",
            "<=": "📏 Menor o igual (<=) | Comparación numérica"
        }

def _reset_builder_state():
    st.session_state.new_rule_conditions = []
    st.session_state.new_rule_name = ""
    st.session_state.new_rule_priority = "Alta"
    st.session_state.new_rule_order = 50

@st.dialog("Editor de Reglas", width="large") 
def render_rules_editor(cols, auto_opts):
    """
    Renderiza el editor con textos traducidos.
    """
    if "new_rule_conditions" not in st.session_state:
        _reset_builder_state()
        
    if "priority_rules" not in st.session_state:
        st.session_state.priority_rules = get_default_rules()
        
    rules_bkp = copy.deepcopy(st.session_state.priority_rules)
    lang = st.session_state.get('language', 'es')

    st.markdown(f"### 🛠️ {get_text(lang, 'rules_editor_title_dialog')}")
    st.info(get_text(lang, 'rules_editor_info_msg'))

    col_builder, col_list = st.columns([0.45, 0.55], gap="large")

    # --- IZQUIERDA: CONSTRUCTOR ---
    with col_builder:
        st.markdown(f"#### {get_text(lang, 'rules_builder_title')}")
        
        r_name = st.text_input(get_text(lang, 'rule_name_lbl'), value=st.session_state.new_rule_name, placeholder=get_text(lang, 'rule_name_ph'))
        st.session_state.new_rule_name = r_name
        
        c1, c2 = st.columns(2)
        r_prio = c1.selectbox(get_text(lang, 'rule_prio_lbl'), ["🚩 Maxima Prioridad", "Alta", "Media", "Minima"], index=1)
        r_order = c2.number_input(get_text(lang, 'rule_order_lbl'), min_value=1, value=50, help=get_text(lang, 'help_order'))
        
        st.markdown(f"#### {get_text(lang, 'rules_step_cond')}")
        
        # -- Selección de Columna --
        ignore_cols = ['Seleccionar', 'Priority', 'Priority_Reason', 'Row Status']
        cols_valid = [c for c in cols if c not in ignore_cols]
        cond_col = st.selectbox(get_text(lang, 'rule_col_lbl'), cols_valid, key="builder_col")
        
        # -- Selección de Operador --
        op_labels = _get_operator_labels(lang)
        cond_op = st.selectbox(
            get_text(lang, 'rule_op_lbl'), 
            options=list(op_labels.keys()), 
            format_func=lambda x: op_labels.get(x, x),
            key="builder_op"
        )
        
        # -- INPUT DE VALOR INTELIGENTE --
        is_math_op = cond_op in [">", "<", ">=", "<="]
        cond_val = None
        
        if is_math_op:
            st.caption(f"🔢 {get_text(lang, 'rule_val_num_lbl')}:")
            cond_val = st.number_input(
                get_text(lang, 'rule_val_num_lbl'), 
                value=0.0, 
                format="%.2f",
                label_visibility="collapsed",
                help=get_text(lang, 'help_num_val'),
                key="builder_val_num"
            )
        else:
            current_opts = auto_opts.get(cond_col, [])
            if current_opts:
                st.caption(get_text(lang, 'rule_sel_list_cap'))
                cond_val = st.selectbox(
                    get_text(lang, 'rule_val_lbl'), 
                    current_opts, 
                    label_visibility="collapsed", 
                    key="builder_val_sel"
                )
            else:
                ph_map = {
                    "contains": get_text(lang, 'rule_ph_contains'),
                    "starts_with": get_text(lang, 'rule_ph_starts'),
                    "is": get_text(lang, 'rule_ph_exact')
                }
                placeholder_txt = ph_map.get(cond_op, get_text(lang, 'rule_ph_generic'))
                
                st.caption(get_text(lang, 'rule_write_txt_cap'))
                cond_val = st.text_input(
                    get_text(lang, 'rule_val_txt_lbl'), 
                    placeholder=placeholder_txt,
                    label_visibility="collapsed",
                    key="builder_val_txt"
                )

        if st.button(get_text(lang, 'btn_add_cond'), use_container_width=True):
            valid = True
            if not is_math_op and not str(cond_val).strip():
                valid = False
                
            if valid:
                st.session_state.new_rule_conditions.append({
                    "column": cond_col,
                    "operator": cond_op,
                    "value": cond_val
                })
            else:
                st.warning(get_text(lang, 'warn_no_val'))

        if st.session_state.new_rule_conditions:
            st.divider()
            st.markdown(f"**{get_text(lang, 'lbl_conds_added')}**")
            for i, cond in enumerate(st.session_state.new_rule_conditions):
                op_nice = op_labels.get(cond['operator'], cond['operator']).split("|")[0].strip()
                val_disp = f"{cond['value']:.2f}" if isinstance(cond['value'], float) else f"'{cond['value']}'"
                
                c_txt, c_del = st.columns([0.85, 0.15])
                c_txt.markdown(f"`{cond['column']}` {op_nice} {val_disp}")
                if c_del.button("❌", key=f"del_{i}"):
                    st.session_state.new_rule_conditions.pop(i)
                    st.rerun()
            
            if st.button(get_text(lang, 'btn_save_rule'), type="primary", use_container_width=True):
                if not r_name:
                    st.error(get_text(lang, 'warn_no_name'))
                else:
                    new_rule = {
                        "id": uuid.uuid4().hex,
                        "enabled": True,
                        "order": r_order,
                        "priority": r_prio,
                        "reason": r_name,
                        "conditions": copy.deepcopy(st.session_state.new_rule_conditions)
                    }
                    st.session_state.priority_rules.append(new_rule)
                    log_rule_changes(f"Crear: {r_name}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    
                    st.success(get_text(lang, 'success_saved'))
                    _reset_builder_state()
                    st.rerun()

    # --- DERECHA: LISTA DE REGLAS ---
    with col_list:
        st.markdown(f"#### {get_text(lang, 'rules_active_list')}")
        display_rules = sorted(st.session_state.priority_rules, key=lambda x: x.get('order', 0))
        
        if not display_rules: st.info(get_text(lang, 'info_no_rules'))
        
        for i, rule in enumerate(display_rules):
            icon = "🟢" if rule.get('enabled', True) else "⚪"
            title = f"{icon} [{rule.get('order')}] {rule.get('reason', 'Sin Nombre')}"
            
            with st.expander(title, expanded=False):
                st.markdown(f"**{get_text(lang, 'rule_prio_lbl')}:** `{rule.get('priority')}`")
                
                for c in rule.get('conditions', []):
                    op_nice = op_labels.get(c['operator'], c['operator']).split("|")[0].strip()
                    st.text(f"- {c['column']} {op_nice} {c['value']}")
                
                c_act, c_del = st.columns(2)
                if c_act.button(get_text(lang, 'btn_toggle_rule'), key=f"tg_{rule['id']}"):
                    rule['enabled'] = not rule.get('enabled', True)
                    log_rule_changes(f"Toggle: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    st.rerun()
                
                if c_del.button(get_text(lang, 'btn_delete_rule'), key=f"dl_{rule['id']}"):
                    st.session_state.priority_rules = [r for r in st.session_state.priority_rules if r['id'] != rule['id']]
                    log_rule_changes(f"Borrar: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    st.rerun()

    st.divider()
    if st.button(get_text(lang, 'btn_close_editor'), use_container_width=True):
        st.session_state.show_rules_editor = False
        st.rerun()