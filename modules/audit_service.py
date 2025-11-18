# modules/audit_service.py
"""
Servicio de log de auditoría generalizado (Celdas, Reglas, Filas, Usuario).
Centraliza la lógica de registro de cambios para toda la aplicación.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import copy

def _get_current_user() -> str:
    """Obtiene el nombre de usuario de la sesión o un valor por defecto."""
    return st.session_state.get('username', 'Usuario Desconocido') or 'Usuario Desconocido'

def log_general_change(reason: str, action: str, change_summary: str, rule_id: str = None, row_id: str = None):
    """
    Registra un cambio en el log de auditoría general.
    """
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    timestamp = datetime.now().isoformat()
    user = _get_current_user()

    st.session_state.audit_log.append({
        "timestamp": timestamp,
        "user": user,
        "reason_for_change": reason,
        "action": action,
        "rule_id": rule_id if rule_id else "",
        "row_id": row_id if row_id else "",
        "change_summary": change_summary
    })

def log_rule_changes(reason: str, old_rules: list, new_rules: list):
    """
    Registra cambios específicos en las reglas (comparando antes y después).
    """
    old_map = {r['id']: r for r in copy.deepcopy(old_rules)}
    new_map = {r['id']: r for r in copy.deepcopy(new_rules)}

    # 1. Nuevas Reglas
    for rule_id in new_map:
        if rule_id not in old_map:
            log_general_change(
                reason=reason,
                action="Rule Created",
                rule_id=rule_id,
                change_summary=f"Nueva regla: {new_map[rule_id]['reason']} (Orden: {new_map[rule_id]['order']}, Valor: {new_map[rule_id]['value']})"
            )

    # 2. Reglas Eliminadas
    for rule_id in old_map:
        if rule_id not in new_map:
            log_general_change(
                reason=reason,
                action="Rule Deleted",
                rule_id=rule_id,
                change_summary=f"Regla eliminada: {old_map[rule_id]['reason']}"
            )

    # 3. Reglas Modificadas
    for rule_id in new_map:
        if rule_id in old_map:
            old_rule = old_map[rule_id]
            new_rule = new_map[rule_id]
            changes = []
            keys_to_compare = ["enabled", "order", "type", "value", "priority", "reason"]
            for key in keys_to_compare:
                if str(old_rule.get(key, "")) != str(new_rule.get(key, "")):
                    changes.append(f"{key}: '{old_rule.get(key)}' -> '{new_rule.get(key)}'")
            
            if changes:
                log_general_change(
                    reason=reason,
                    action="Rule Modified",
                    rule_id=rule_id,
                    change_summary=f"Regla '{new_rule['reason']}': " + "; ".join(changes)
                )

def get_audit_log_excel() -> bytes:
    """Convierte el log a Excel para descargar."""
    log_df = pd.DataFrame(st.session_state.get('audit_log', []))
    
    if not log_df.empty:
        cols_order = ["timestamp", "user", "action", "reason_for_change", "row_id", "rule_id", "change_summary"]
        # Asegurar columnas
        for col in cols_order:
            if col not in log_df.columns:
                log_df[col] = np.nan
        
        log_df = log_df[cols_order]
        # Formatear fecha
        log_df['timestamp'] = pd.to_datetime(log_df['timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        log_df = log_df.fillna("")
        log_df = log_df.sort_values(by="timestamp", ascending=False)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        log_df.to_excel(writer, index=False, sheet_name='Audit_Log_General')
    return output.getvalue()