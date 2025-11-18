# modules/rules_service.py
"""
Motor de reglas de negocio.
Nota: La lógica de auditoría se ha movido a modules/audit_service.py
"""

import streamlit as st
import pandas as pd
import numpy as np

def get_default_rules():
    """Define las reglas por defecto."""
    return [
        {"id": "rule_001", "enabled": True, "order": 20, "type": "Pay Group", "value": "DIST", "priority": "🚩 Maxima Prioridad", "reason": "Regla Sistema: PayGroup DIST"},
        {"id": "rule_002", "enabled": True, "order": 20, "type": "Pay Group", "value": "INTERCOMPANY", "priority": "🚩 Maxima Prioridad", "reason": "Regla Sistema: PayGroup INTERCOMPANY"},
        {"id": "rule_003", "enabled": True, "order": 20, "type": "Pay Group", "value": "PAYROLL", "priority": "🚩 Maxima Prioridad", "reason": "Regla Sistema: PayGroup PAYROLL"},
        {"id": "rule_004", "enabled": True, "order": 20, "type": "Pay Group", "value": "RENTS", "priority": "🚩 Maxima Prioridad", "reason": "Regla Sistema: PayGroup RENTS"},
        {"id": "rule_005", "enabled": True, "order": 20, "type": "Pay Group", "value": "SCF", "priority": "🚩 Maxima Prioridad", "reason": "Regla Sistema: PayGroup SCF"},
        {"id": "rule_006", "enabled": True, "order": 30, "type": "Pay Group", "value": "PAYGROUP", "priority": "Minima", "reason": "Regla Sistema: PayGroup PAYGROUP (Baja)"},
        {"id": "rule_007", "enabled": True, "order": 30, "type": "Pay Group", "value": "GNTD", "priority": "Minima", "reason": "Regla Sistema: PayGroup GNTD (Baja)"}
    ]

def apply_priority_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el motor de reglas.
    IMPORTANTE: Elimina columnas temporales para evitar ensuciar el DataFrame final.
    """
    if 'Priority' not in df.columns:
        return df

    # 1. Obtener reglas
    rules = st.session_state.get('priority_rules')
    if rules is None:
        rules = get_default_rules()
        st.session_state.priority_rules = rules
        
    # Ordenar: menor número primero (ej. 10), luego mayores (ej. 100).
    # reverse=False asegura que el 100 (regla usuario) se ejecute AL FINAL y sobrescriba al 30.
    active_rules = sorted(
        [r for r in rules if r.get('enabled', False)],
        key=lambda x: x.get('order', 99),
        reverse=False 
    )
    
    # 2. Columnas temporales
    df.loc[:, 'Priority_Calculated'] = "Sin Regla Asignada"
    df.loc[:, 'Priority_Reason'] = "Sin Regla Asignada"
    
    # 3. Aplicar Reglas
    for rule in active_rules:
        r_type = rule.get('type')
        r_val = rule.get('value')
        r_prio = rule.get('priority')
        r_reason = rule.get('reason', f"Regla: {r_type} contiene {r_val}")

        if not all([r_type, r_val, r_prio]): continue

        try:
            if r_type in df.columns:
                mask = df[r_type].fillna("").astype(str).str.contains(r_val, case=False, na=False)
                df.loc[mask, 'Priority_Calculated'] = r_prio
                df.loc[mask, 'Priority_Reason'] = r_reason
        except Exception:
            pass

    # 4. Preservar ingresos manuales si no hubo regla
    manual_priorities = ["Minima", "Media", "Alta", "Baja Prioridad", "Low", "Medium", "High", "Zero"]
    mask_manual = df['Priority'].isin(manual_priorities)
    mask_no_rule = (df['Priority_Reason'] == "Sin Regla Asignada")
    
    mask_keep_manual = mask_manual & mask_no_rule
    df.loc[mask_keep_manual, 'Priority_Calculated'] = df['Priority']
    df.loc[mask_keep_manual, 'Priority_Reason'] = "Ingreso Manual"
    
    # 5. Finalizar
    df.loc[:, 'Priority'] = df['Priority_Calculated']
    
    # IMPORTANTE: Eliminar la columna temporal 'Priority_Calculated' 
    # para que no aparezca en el selector de columnas y cause errores.
    return df.drop(columns=['Priority_Calculated'], errors='ignore')