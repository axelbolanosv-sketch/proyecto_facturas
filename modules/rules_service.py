# modules/rules_service.py (CORREGIDO - LÓGICA DE JERARQUÍA ARREGLADA v4)
# Contiene el motor de reglas de negocio y el servicio de auditoría.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import copy # Importar para copias profundas

def get_default_rules():
    """
    Define las reglas de prioridad por defecto.
    (Sin cambios)
    """
    return [
        {
            "id": "rule_001",
            "enabled": True,
            "order": 20, # Orden más alto (menor prioridad)
            "type": "Pay Group",
            "value": "DIST",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Sistema: PayGroup DIST"
        },
        {
            "id": "rule_002",
            "enabled": True,
            "order": 20,
            "type": "Pay Group",
            "value": "INTERCOMPANY",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Sistema: PayGroup INTERCOMPANY"
        },
        {
            "id": "rule_003",
            "enabled": True,
            "order": 20,
            "type": "Pay Group",
            "value": "PAYROLL",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Sistema: PayGroup PAYROLL (Nómina)"
        },
        {
            "id": "rule_004",
            "enabled": True,
            "order": 20,
            "type": "Pay Group",
            "value": "RENTS",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Sistema: PayGroup RENTS (Alquileres)"
        },
        {
            "id": "rule_005",
            "enabled": True,
            "order": 20,
            "type": "Pay Group",
            "value": "SCF",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Sistema: PayGroup SCF"
        },
        {
            "id": "rule_006",
            "enabled": True,
            "order": 30, # Orden más alto (menor prioridad)
            "type": "Pay Group",
            "value": "PAYGROUP",
            "priority": "Minima",
            "reason": "Regla Sistema: PayGroup PAYGROUP (Baja)"
        },
        {
            "id": "rule_007",
            "enabled": True,
            "order": 30,
            "type": "Pay Group",
            "value": "GNTD",
            "priority": "Minima",
            "reason": "Regla Sistema: PayGroup GNTD (Baja)"
        }
    ]

def apply_priority_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el motor de reglas dinámicas al DataFrame.
    
    --- LÓGICA DE JERARQUÍA CORREGIDA (v4) ---
    Se corrigió el ordenamiento. Ahora 'reverse=False', para que
    las reglas se ejecuten en el orden numérico correcto (10, 20, 30, 100).
    Esto cumple con la ayuda "Número más bajo se ejecuta primero"
    y permite que las reglas más altas (como la tuya en 100)
    sobrescriban a las reglas base (como GNTD en 30).
    """
    if 'Priority' not in df.columns:
        return df

    # --- [INICIO] CORRECCIÓN DE JERARQUÍA ---

    # 1. Cargar reglas activas y ordenarlas
    rules = st.session_state.get('priority_rules')
    if rules is None:
        rules = get_default_rules()
        st.session_state.priority_rules = rules
        
    # [INICIO] CORRECIÓN DEL BUG DE ORDENAMIENTO
    # Se cambió 'reverse=True' por 'reverse=False'.
    # Ahora el orden de ejecución será 20, 30, 100 (tu regla), etc.
    # Esto asegura que tu regla (100) se ejecute al final y
    # sobrescriba la regla GNTD (30).
    active_rules = sorted(
        [r for r in rules if r.get('enabled', False)],
        key=lambda x: x.get('order', 99),
        reverse=False # <-- ¡ESTA ES LA CORRECCIÓN!
    )
    # [FIN] CORRECIÓN DEL BUG DE ORDENAMIENTO
    
    # 2. Inicializar columnas de resultado
    df['Priority_Calculated'] = "Sin Regla Asignada"
    df['Priority_Reason'] = "Sin Regla Asignada"
    
    # 3. Iterar Reglas Dinámicas (Paso 1: Las Reglas mandan)
    for rule in active_rules:
        rule_type = rule.get('type')
        rule_value = rule.get('value')
        rule_priority = rule.get('priority')
        rule_reason = rule.get('reason', f"Regla: {rule_type} es {rule_value}")

        if not all([rule_type, rule_value, rule_priority]):
            continue

        try:
            if rule_type in df.columns:
                mask_rule = (
                    df[rule_type].fillna("").astype(str).str.contains(rule_value, case=False, na=False)
                )
                # Ahora que el bucle está ordenado (20, 30, 100),
                # tu regla de Anggie (100) se aplicará al final,
                # sobrescribiendo 'Minima' de GNTD (30).
                df.loc[mask_rule, 'Priority_Calculated'] = rule_priority
                df.loc[mask_rule, 'Priority_Reason'] = rule_reason
        except Exception:
            pass 

    # 4. Aplicar Prioridad Manual (Paso 2: Rellenar "huecos")
    # (Esta lógica de la v3 es correcta y se mantiene)
    manual_priorities = [
        "Minima", "Media", "Alta", "Baja Prioridad",
        "Low", "Medium", "High", "Zero"
    ]
    
    mask_input_is_manual = df['Priority'].isin(manual_priorities)
    mask_rule_found_nothing = (df['Priority_Reason'] == "Sin Regla Asignada")
    
    mask_apply_manual = mask_input_is_manual & mask_rule_found_nothing
    
    df.loc[mask_apply_manual, 'Priority_Calculated'] = df['Priority']
    df.loc[mask_apply_manual, 'Priority_Reason'] = "Ingreso Manual"
    
    # --- [FIN] LÓGICA DE CORRECCIÓN DE JERARQUÍA ---
    
    # 5. Asignar la nueva prioridad calculada
    df['Priority'] = df['Priority_Calculated']
    
    return df

# --- (El resto del archivo: log_change y get_audit_log_excel) ---
# --- (No tienen cambios y se omiten por brevedad) ---

def log_change(reason: str, old_rules: list, new_rules: list):
    """
    Compara dos listas de reglas y registra las diferencias
    en el log de auditoría.
    (Sin cambios)
    """
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    timestamp = datetime.now().isoformat()
    user = "finance_user" 

    old_map = {r['id']: r for r in copy.deepcopy(old_rules)}
    new_map = {r['id']: r for r in copy.deepcopy(new_rules)}

    # 1. Nuevas Reglas
    for rule_id in new_map:
        if rule_id not in old_map:
            st.session_state.audit_log.append({
                "timestamp": timestamp,
                "user": user,
                "reason_for_change": reason,
                "action": "Rule Created",
                "rule_id": rule_id,
                "change_summary": f"Nueva regla: {new_map[rule_id]['reason']}"
            })

    # 2. Reglas Eliminadas
    for rule_id in old_map:
        if rule_id not in new_map:
            st.session_state.audit_log.append({
                "timestamp": timestamp,
                "user": user,
                "reason_for_change": reason,
                "action": "Rule Deleted",
                "rule_id": rule_id,
                "change_summary": f"Regla eliminada: {old_map[rule_id]['reason']}"
            })

    # 3. Reglas Modificadas
    for rule_id in new_map:
        if rule_id in old_map:
            old_rule = old_map[rule_id]
            new_rule = new_map[rule_id]
            
            changes = []
            keys_to_compare = ["enabled", "order", "type", "value", "priority", "reason"]
            for key in keys_to_compare:
                if old_rule.get(key) != new_rule.get(key):
                    changes.append(f"{key}: '{old_rule.get(key)}' -> '{new_rule.get(key)}'")
            
            if changes:
                st.session_state.audit_log.append({
                    "timestamp": timestamp,
                    "user": user,
                    "reason_for_change": reason,
                    "action": "Rule Modified",
                    "rule_id": rule_id,
                    "change_summary": "; ".join(changes)
                })

def get_audit_log_excel():
    """
    Convierte el log de auditoría en memoria a un archivo Excel
    listo para descargar.
    (Sin cambios)
    """
    log_df = pd.DataFrame(st.session_state.get('audit_log', []))
    
    if not log_df.empty:
        cols_order = [
            "timestamp", "user", "reason_for_change", 
            "action", "rule_id", "change_summary"
        ]
        for col in cols_order:
            if col not in log_df.columns:
                log_df[col] = np.nan
        log_df = log_df[cols_order]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        log_df.to_excel(writer, index=False, sheet_name='Audit_Log_Prioridad')
    return output.getvalue()