# modules/gui_rules_editor.py
import streamlit as st
import pandas as pd
import uuid
import copy
from modules.audit_service import log_rule_changes
from modules.rules_service import apply_priority_rules, get_default_rules

def _get_operator_labels(lang: str) -> dict:
    """
    Devuelve las etiquetas descriptivas de los operadores.
    Muestra el símbolo y una explicación para que el usuario no se pierda.
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
            "starts_with": "🔤 Empieza con | El texto inicia con...",
            ">": "📈 Mayor que (>) | Comparación numérica",
            "<": "📉 Menor que (<) | Comparación numérica",
            ">=": "📐 Mayor o igual (>=) | Comparación numérica",
            "<=": "📏 Menor o igual (<=) | Comparación numérica"
        }

def _reset_builder_state():
    """Reinicia el constructor."""
    st.session_state.new_rule_conditions = []
    st.session_state.new_rule_name = ""
    st.session_state.new_rule_priority = "Alta"
    st.session_state.new_rule_order = 50

@st.dialog("Editor de Reglas de Negocio", width="large")
def render_rules_editor(cols, auto_opts):
    """
    Renderiza el editor con 'Entradas Inteligentes' que cambian de formato
    según el operador seleccionado.
    """
    if "new_rule_conditions" not in st.session_state:
        _reset_builder_state()
        
    if "priority_rules" not in st.session_state:
        st.session_state.priority_rules = get_default_rules()
        
    rules_bkp = copy.deepcopy(st.session_state.priority_rules)
    lang = st.session_state.get('language', 'es')

    st.markdown("### 🛠️ Constructor de Reglas")
    st.info("Defina reglas lógicas. El sistema detectará automáticamente si necesita ingresar un número o texto.")

    col_builder, col_list = st.columns([0.45, 0.55], gap="large")

    # --- IZQUIERDA: CONSTRUCTOR ---
    with col_builder:
        st.markdown("#### 1. Definición de la Regla")
        
        r_name = st.text_input("Nombre (Razón)", value=st.session_state.new_rule_name, placeholder="Ej. Facturas > 10k")
        st.session_state.new_rule_name = r_name
        
        c1, c2 = st.columns(2)
        r_prio = c1.selectbox("Prioridad", ["🚩 Maxima Prioridad", "Alta", "Media", "Minima"], index=1)
        r_order = c2.number_input("Orden", min_value=1, value=50, help="Mayor número = Se ejecuta al final.")
        
        st.markdown("#### 2. Agregar Condiciones")
        
        # -- Selección de Columna --
        ignore_cols = ['Seleccionar', 'Priority', 'Priority_Reason', 'Row Status']
        cols_valid = [c for c in cols if c not in ignore_cols]
        cond_col = st.selectbox("Columna", cols_valid, key="builder_col")
        
        # -- Selección de Operador (Con descripciones bonitas) --
        op_labels = _get_operator_labels(lang)
        cond_op = st.selectbox(
            "Operador", 
            options=list(op_labels.keys()), 
            format_func=lambda x: op_labels.get(x, x),
            key="builder_op"
        )
        
        # -- INPUT DE VALOR INTELIGENTE (Aquí está el cambio clave) --
        # Detectamos si es una operación matemática
        is_math_op = cond_op in [">", "<", ">=", "<="]
        
        cond_val = None
        
        if is_math_op:
            # CASO 1: Operador Matemático -> Mostramos Input Numérico
            # Esto "autorellena" el formato (0.00) y evita errores de texto.
            st.caption("🔢 Ingrese el valor numérico:")
            cond_val = st.number_input(
                "Valor Numérico", 
                value=0.0, 
                format="%.2f",  # Formato visual bonito (ej. 1500.00)
                label_visibility="collapsed",
                help="Escriba solo el número. El sistema se encarga de la comparación matemática.",
                key="builder_val_num"
            )
        else:
            # CASO 2: Operador de Texto -> Mostramos Select o Texto con Placeholder
            current_opts = auto_opts.get(cond_col, [])
            
            if current_opts:
                # Si hay lista de opciones (ej. Proveedores), usamos Selectbox
                st.caption("📋 Seleccione de la lista:")
                cond_val = st.selectbox(
                    "Valor", 
                    current_opts, 
                    label_visibility="collapsed", 
                    key="builder_val_sel"
                )
            else:
                # Si es texto libre, usamos placeholder dinámico para guiar
                ph_map = {
                    "contains": "Ej. 'Servicios' (Buscará texto parcial)",
                    "starts_with": "Ej. 'INV-' (Debe empezar así)",
                    "is": "Ej. Valor exacto"
                }
                placeholder_txt = ph_map.get(cond_op, "Escriba el valor...")
                
                st.caption("✍️ Escriba el texto:")
                cond_val = st.text_input(
                    "Valor Texto", 
                    placeholder=placeholder_txt,
                    label_visibility="collapsed",
                    key="builder_val_txt"
                )

        # Botón para añadir la condición al borrador
        if st.button("➕ Agregar Condición", use_container_width=True):
            # Validar que no esté vacío (el 0.0 en numérico cuenta como valor, así que chequeamos string si no es numérico)
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
                st.warning("Ingrese un valor válido.")

        # Lista de condiciones pendientes
        if st.session_state.new_rule_conditions:
            st.divider()
            st.markdown("**Condiciones (Y):**")
            for i, cond in enumerate(st.session_state.new_rule_conditions):
                # Mostrar de forma legible
                op_nice = op_labels.get(cond['operator'], cond['operator']).split("|")[0].strip()
                val_disp = f"{cond['value']:.2f}" if isinstance(cond['value'], float) else f"'{cond['value']}'"
                
                c_txt, c_del = st.columns([0.85, 0.15])
                c_txt.markdown(f"`{cond['column']}` {op_nice} {val_disp}")
                if c_del.button("❌", key=f"del_{i}"):
                    st.session_state.new_rule_conditions.pop(i)
                    st.rerun()
            
            if st.button("💾 Guardar Regla", type="primary", use_container_width=True):
                if not r_name:
                    st.error("Falta el nombre de la regla.")
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
                    
                    st.success("¡Guardada!")
                    _reset_builder_state()
                    st.rerun()

    # --- DERECHA: LISTA DE REGLAS ---
    with col_list:
        st.markdown("#### 📋 Reglas Activas")
        display_rules = sorted(st.session_state.priority_rules, key=lambda x: x.get('order', 0))
        
        if not display_rules: st.info("Sin reglas.")
        
        for i, rule in enumerate(display_rules):
            icon = "🟢" if rule.get('enabled', True) else "⚪"
            title = f"{icon} [{rule.get('order')}] {rule.get('reason', 'Sin Nombre')}"
            
            with st.expander(title, expanded=False):
                st.markdown(f"**Prioridad:** `{rule.get('priority')}`")
                st.caption("Condiciones:")
                for c in rule.get('conditions', []):
                    op_nice = op_labels.get(c['operator'], c['operator']).split("|")[0].strip()
                    st.text(f"- {c['column']} {op_nice} {c['value']}")
                
                c_act, c_del = st.columns(2)
                if c_act.button("Activar/Desactivar", key=f"tg_{rule['id']}"):
                    rule['enabled'] = not rule.get('enabled', True)
                    log_rule_changes(f"Toggle: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    st.rerun()
                
                if c_del.button("Eliminar", key=f"dl_{rule['id']}"):
                    st.session_state.priority_rules = [r for r in st.session_state.priority_rules if r['id'] != rule['id']]
                    log_rule_changes(f"Borrar: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    st.rerun()

    st.divider()
    if st.button("Cerrar Editor", use_container_width=True):
        st.session_state.show_rules_editor = False
        st.rerun()