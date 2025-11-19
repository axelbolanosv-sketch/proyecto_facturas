# modules/gui_rules_editor.py
import streamlit as st
import pandas as pd
import uuid
import copy
from modules.audit_service import log_rule_changes
from modules.rules_service import apply_priority_rules, get_default_rules

def _get_operator_labels(lang: str) -> dict:
    """
    Devuelve un diccionario con las etiquetas descriptivas de los operadores
    según el idioma seleccionado. Incluye explicación de funcionamiento.
    """
    if lang == "en":
        return {
            "contains": "🔍 Contains (Partial) | Finds text inside cell (e.g. 'Apple' in 'Apple Inc')",
            "is": "🟰 Is equal to (Exact) | Full match (Case insensitive)",
            "is_not": "🚫 Is not equal to | Everything except this value",
            "starts_with": "🔤 Starts with | Cell starts with this text",
            ">": "📈 Greater than (>) | Mathematical comparison (Numbers)",
            "<": "📉 Less than (<) | Mathematical comparison (Numbers)",
            ">=": "📐 Greater or equal (>=) | Mathematical comparison",
            "<=": "📏 Less or equal (<=) | Mathematical comparison"
        }
    else: # Default to Spanish
        return {
            "contains": "🔍 Contiene (Parcial) | Busca el texto dentro (Ej. 'Sol' en 'Girasol')",
            "is": "🟰 Es igual a (Exacto) | Coincidencia completa (No distingue Mayús/Minús)",
            "is_not": "🚫 No es igual a | Todo lo que NO sea este valor",
            "starts_with": "🔤 Empieza con | La celda inicia con este texto",
            ">": "📈 Mayor que (>) | Comparación numérica",
            "<": "📉 Menor que (<) | Comparación numérica",
            ">=": "📐 Mayor o igual (>=) | Comparación numérica",
            "<=": "📏 Menor o igual (<=) | Comparación numérica"
        }

def _reset_builder_state():
    """Reinicia las variables temporales del constructor de reglas."""
    st.session_state.new_rule_conditions = []
    st.session_state.new_rule_name = ""
    st.session_state.new_rule_priority = "Alta"
    st.session_state.new_rule_order = 50

@st.dialog("Editor de Reglas de Negocio", width="large")
def render_rules_editor(cols, auto_opts):
    """
    Interfaz gráfica para crear y gestionar reglas complejas.
    Divide la pantalla en 'Constructor' (Izquierda) y 'Lista' (Derecha).
    """
    # Inicialización de estado local si no existe
    if "new_rule_conditions" not in st.session_state:
        _reset_builder_state()
        
    if "priority_rules" not in st.session_state:
        st.session_state.priority_rules = get_default_rules()
        
    # Backup para auditoría
    rules_bkp = copy.deepcopy(st.session_state.priority_rules)
    lang = st.session_state.get('language', 'es')

    st.markdown("### 🛠️ Constructor de Reglas")
    st.info("Cree reglas combinando condiciones. Una regla se aplica solo si **TODAS** sus condiciones se cumplen (Lógica Y).")

    # --- LAYOUT: DOS COLUMNAS ---
    col_builder, col_list = st.columns([0.45, 0.55], gap="large")

    # =============================
    # COLUMNA IZQUIERDA: CONSTRUCTOR
    # =============================
    with col_builder:
        st.markdown("#### 1. Definición")
        
        # A. Datos de la Regla
        r_name = st.text_input("Nombre/Razón", value=st.session_state.new_rule_name, placeholder="Ej. Facturas Proveedor ACME > 10k")
        st.session_state.new_rule_name = r_name
        
        c1, c2 = st.columns(2)
        r_prio = c1.selectbox("Prioridad a Asignar", ["🚩 Maxima Prioridad", "Alta", "Media", "Minima"], index=1)
        r_order = c2.number_input("Orden", min_value=1, value=50, help="Reglas con número mayor se ejecutan después y pueden sobrescribir a las anteriores.")
        
        st.markdown("#### 2. Condiciones")
        
        # B. Selector de Condiciones
        # Filtramos columnas técnicas que no deberían usarse en reglas
        ignore_cols = ['Seleccionar', 'Priority', 'Priority_Reason', 'Row Status']
        cols_valid = [c for c in cols if c not in ignore_cols]
        
        cond_col = st.selectbox("Columna", cols_valid, key="builder_col")
        
        # B.1 Selector de Operador con Descripciones Dinámicas
        op_labels = _get_operator_labels(lang)
        op_keys = list(op_labels.keys())
        
        cond_op = st.selectbox(
            "Operador", 
            options=op_keys, 
            format_func=lambda x: op_labels.get(x, x), # Muestra el texto bonito
            key="builder_op"
        )
        
        # B.2 Input de Valor (Dinámico)
        # Si la columna tiene autocompletado y NO es una operación matemática, mostrar selectbox
        current_opts = auto_opts.get(cond_col, [])
        if current_opts and cond_op not in [">", "<", ">=", "<="]:
            cond_val = st.selectbox("Valor", current_opts, key="builder_val_sel")
        else:
            cond_val = st.text_input("Valor", key="builder_val_txt")

        # Botón añadir condición temporal
        if st.button("➕ Agregar Condición", use_container_width=True):
            if str(cond_val).strip():
                st.session_state.new_rule_conditions.append({
                    "column": cond_col,
                    "operator": cond_op,
                    "value": cond_val
                })
            else:
                st.warning("El valor no puede estar vacío.")

        # C. Visualización de Condiciones Pendientes
        if st.session_state.new_rule_conditions:
            st.divider()
            st.caption("Condiciones Agregadas:")
            
            for i, cond in enumerate(st.session_state.new_rule_conditions):
                # Mostrar operador traducido en la lista también
                op_display = op_labels.get(cond['operator'], cond['operator']).split("|")[0].strip() # Solo la parte corta
                
                col_txt, col_del = st.columns([0.85, 0.15])
                col_txt.markdown(f"**{i+1}.** `{cond['column']}` {op_display} `{cond['value']}`")
                if col_del.button("❌", key=f"del_cond_{i}"):
                    st.session_state.new_rule_conditions.pop(i)
                    st.rerun()
            
            st.divider()
            # Botón Guardar Final
            if st.button("💾 Guardar Regla Completa", type="primary", use_container_width=True):
                if not r_name:
                    st.error("Debe asignar un nombre o razón a la regla.")
                else:
                    # Construir objeto final
                    new_rule = {
                        "id": uuid.uuid4().hex,
                        "enabled": True,
                        "order": r_order,
                        "priority": r_prio,
                        "reason": r_name,
                        "conditions": copy.deepcopy(st.session_state.new_rule_conditions)
                    }
                    # Persistir
                    st.session_state.priority_rules.append(new_rule)
                    
                    # Log y Recálculo
                    log_rule_changes(f"Crear: {r_name}", rules_bkp, st.session_state.priority_rules)
                    if st.session_state.df_staging is not None:
                        st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                    
                    st.success("Regla guardada correctamente.")
                    _reset_builder_state()
                    st.rerun()

    # =============================
    # COLUMNA DERECHA: LISTA REGLAS
    # =============================
    with col_list:
        st.markdown("#### 📋 Reglas Existentes")
        
        # Ordenar para visualización (por orden de ejecución)
        display_rules = sorted(st.session_state.priority_rules, key=lambda x: x.get('order', 0))
        
        if not display_rules:
            st.info("No hay reglas configuradas actualmente.")
        
        for i, rule in enumerate(display_rules):
            # Iconografía de estado
            is_on = rule.get('enabled', True)
            icon = "🟢" if is_on else "⚪"
            
            # Título del Expander
            title = f"{icon} [{rule.get('order')}] {rule.get('reason', 'Sin Nombre')}"
            
            with st.expander(title, expanded=False):
                c_desc, c_btn = st.columns([0.7, 0.3])
                
                with c_desc:
                    st.markdown(f"**Prioridad:** `{rule.get('priority')}`")
                    st.caption("Condiciones:")
                    for c in rule.get('conditions', []):
                        # Traducir operador para lectura fácil
                        op_nice = op_labels.get(c['operator'], c['operator']).split("|")[0].strip()
                        st.text(f"- {c['column']} {op_nice} {c['value']}")

                with c_btn:
                    # Botón Activar/Desactivar
                    lbl_tog = "Desactivar" if is_on else "Activar"
                    if st.button(lbl_tog, key=f"tog_{rule['id']}", use_container_width=True):
                        rule['enabled'] = not is_on
                        log_rule_changes(f"Toggle: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                        if st.session_state.df_staging is not None:
                            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                        st.rerun()
                    
                    # Botón Eliminar
                    if st.button("🗑️ Eliminar", key=f"del_{rule['id']}", use_container_width=True):
                        st.session_state.priority_rules.pop(i) # i es seguro porque iteramos sobre lista ordenada/filtrada igual al state? Cuidado: 
                        # Mejor buscar por ID para evitar errores de índice si el sort cambia
                        st.session_state.priority_rules = [r for r in st.session_state.priority_rules if r['id'] != rule['id']]
                        
                        log_rule_changes(f"Borrar: {rule['reason']}", rules_bkp, st.session_state.priority_rules)
                        if st.session_state.df_staging is not None:
                            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
                        st.rerun()

    st.divider()
    if st.button("Cerrar Editor", use_container_width=True):
        st.session_state.show_rules_editor = False
        st.rerun()