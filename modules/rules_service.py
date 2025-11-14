# modules/rules_service.py (NUEVO ARCHIVO)
# Contiene el motor de reglas de negocio y el servicio de auditoría.

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

def get_default_rules():
    """
    Define las reglas de prioridad por defecto que el sistema
    usará al iniciar por primera vez.
    """
    return [
        {
            "id": "rule_001",
            "enabled": True,
            "order": 10,
            "type": "Pay Group",
            "value": "DIST",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Default: Pagos Intercompany"
        },
        {
            "id": "rule_002",
            "enabled": True,
            "order": 11,
            "type": "Pay Group",
            "value": "INTERCOMPANY",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Default: Pagos Intercompany"
        },
        {
            "id": "rule_003",
            "enabled": True,
            "order": 12,
            "type": "Pay Group",
            "value": "PAYROLL",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Default: Nómina"
        },
        {
            "id": "rule_004",
            "enabled": True,
            "order": 13,
            "type": "Pay Group",
            "value": "RENTS",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Default: Alquileres"
        },
        {
            "id": "rule_005",
            "enabled": True,
            "order": 14,
            "type": "Pay Group",
            "value": "SCF",
            "priority": "🚩 Maxima Prioridad",
            "reason": "Regla Default: SCF"
        },
        {
            "id": "rule_006",
            "enabled": True,
            "order": 20,
            "type": "Pay Group",
            "value": "PAYGROUP",
            "priority": "Minima",
            "reason": "Regla Default: Pagos agrupados"
        },
        {
            "id": "rule_007",
            "enabled": True,
            "order": 21,
            "type": "Pay Group",
            "value": "GNTD",
            "priority": "Minima",
            "reason": "Regla Default: GNTD"
        }
    ]

def apply_priority_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el motor de reglas dinámicas al DataFrame.
    Esta función REEMPLAZA la lógica estática (hard-coded).
    
    El orden de prioridad es:
    1. Una prioridad manual (Alta, Media, Minima) escrita en la celda.
    2. Reglas dinámicas (leídas de st.session_state.priority_rules).
    3. Valor por defecto (si no hay manual y no hay regla).
    """
    if 'Priority' not in df.columns or 'Pay Group' not in df.columns:
        return df

    # 1. Cargar reglas activas y ordenarlas
    rules = st.session_state.get('priority_rules', get_default_rules())
    active_rules = sorted(
        [r for r in rules if r.get('enabled', False)], 
        key=lambda x: x.get('order', 99)
    )
    
    # 2. Definir prioridades manuales (estas tienen precedencia)
    manual_priorities = ["Minima", "Media", "Alta", "Baja Prioridad", "Low", "Medium", "High", "Zero"]
    
    # 3. Inicializar columnas de resultado
    # 'Priority_Reason' es la columna que explica el "por qué" (el "tooltip")
    df['Priority_Reason'] = "Ingreso Manual" # Default si se edita a mano
    df['Priority_Calculated'] = df['Priority'] # Empezar con el valor existente
    
    # Crear máscaras base
    mask_manual = df['Priority'].isin(manual_priorities)
    mask_excel_maxima = (df['Priority'] == "Maxima Prioridad") | (df['Priority'] == "🚩 Maxima Prioridad")

    # 4. Iterar Reglas Dinámicas
    # Iteramos por las reglas (ordenadas por 'order')
    for rule in active_rules:
        rule_type = rule.get('type')
        rule_value = rule.get('value')
        rule_priority = rule.get('priority')
        rule_reason = rule.get('reason', f"Regla: {rule_type} es {rule_value}")

        if not all([rule_type, rule_value, rule_priority]):
            continue # Regla mal configurada

        # Crear máscara para esta regla
        try:
            # Solo aplicar si la columna existe y no es manual o máxima del excel
            if rule_type in df.columns:
                mask_rule = (
                    df[rule_type].fillna("").astype(str).str.contains(rule_value, case=False, na=False)
                )
                
                # Aplicar regla SOLO si NO es manual y NO es Maxima (del Excel)
                # Las reglas dinámicas tienen menos prioridad que la edición manual
                apply_mask = mask_rule & ~mask_manual & ~mask_excel_maxima
                
                df.loc[apply_mask, 'Priority_Calculated'] = rule_priority
                df.loc[apply_mask, 'Priority_Reason'] = rule_reason
        except Exception:
            pass # Ignorar reglas rotas (ej. columna no existe)

    # 5. Manejar casos que no cayeron en reglas
    # Si no es manual y no es Maxima (Excel), y no cayó en regla, es "Default" (vacío)
    mask_default = ~mask_manual & ~mask_excel_maxima & (df['Priority_Calculated'] == df['Priority'])
    df.loc[mask_default, 'Priority_Reason'] = "Sin Regla Asignada"

    # 6. Asignar la nueva prioridad calculada
    df['Priority'] = df['Priority_Calculated']
    
    # Limpiar columnas temporales
    df = df.drop(columns=['Priority_Calculated'])
    
    return df

def log_change(reason: str, old_rules: list, new_rules: list):
    """
    Compara dos listas de reglas y registra las diferencias
    en el log de auditoría.
    """
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    timestamp = datetime.now().isoformat()
    # Simple placeholder. En un sistema real, se obtendría del login.
    user = "finance_user" 

    # Convertir listas a diccionarios por ID para fácil comparación
    old_map = {r['id']: r for r in old_rules}
    new_map = {r['id']: r for r in new_rules}

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
            for key in old_rule:
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
    """
    log_df = pd.DataFrame(st.session_state.get('audit_log', []))
    
    # Reordenar columnas para legibilidad
    if not log_df.empty:
        cols_order = [
            "timestamp", "user", "reason_for_change", 
            "action", "rule_id", "change_summary"
        ]
        # Asegurarse de que todas las columnas existan
        for col in cols_order:
            if col not in log_df.columns:
                log_df[col] = np.nan
        log_df = log_df[cols_order]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        log_df.to_excel(writer, index=False, sheet_name='Audit_Log_Prioridad')
    return output.getvalue()