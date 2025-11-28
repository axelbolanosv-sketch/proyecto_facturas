"""
Servicio de Auditoría y Trazabilidad.

Centraliza el registro de eventos (logs) de la aplicación. Permite rastrear
quién hizo qué, cuándo y por qué, cubriendo cambios en celdas, aplicación
de reglas y modificaciones estructurales (filas).
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import copy

def _get_current_user() -> str:
    """Recupera el usuario activo de la sesión para atribuir los cambios.

    Returns:
        str: Nombre del usuario o 'Usuario Desconocido' si no hay sesión iniciada.
    """
    return st.session_state.get('username', 'Usuario Desconocido') or 'Usuario Desconocido'

def log_general_change(reason: str, action: str, change_summary: str, rule_id: str = None, row_id: str = None):
    """Registra un evento genérico en el historial de auditoría.

    Args:
        reason (str): Categoría o razón del cambio (ej. "Manual Edit", "Rule Update").
        action (str): Acción específica realizada (ej. "Cell Update", "Row Deleted").
        change_summary (str): Descripción legible del cambio para humanos.
        rule_id (str, optional): ID de la regla afectada (si aplica).
        row_id (str, optional): ID de la fila afectada (si aplica).
    """
    if 'audit_log' not in st.session_state:
        st.session_state.audit_log = []
        
    timestamp = datetime.now().isoformat()
    user = _get_current_user()

    entry = {
        "timestamp": timestamp,
        "user": user,
        "reason_for_change": reason,
        "action": action,
        "rule_id": rule_id if rule_id else "",
        "row_id": row_id if row_id else "",
        "change_summary": change_summary
    }
    
    st.session_state.audit_log.append(entry)

def _format_conditions(conditions: list) -> str:
    """Convierte una lista de objetos de condición en un string legible.

    Helper interno para formatear logs de reglas.

    Args:
        conditions (list): Lista de diccionarios de condiciones.

    Returns:
        str: Representación en texto (ej. "[Total > 1000] Y [Vendor is ACME]").
    """
    if not conditions:
        return "Sin condiciones"
    
    descriptions = []
    for c in conditions:
        col = c.get('column', '?')
        op = c.get('operator', '?')
        val = c.get('value', '?')
        descriptions.append(f"[{col} {op} {val}]")
    
    return " Y ".join(descriptions)

def log_rule_changes(reason: str, old_rules: list, new_rules: list):
    """Analiza y registra diferencias (deltas) entre dos estados de reglas.

    Compara el estado anterior y el nuevo de la lista de reglas para determinar
    si se crearon, borraron o modificaron reglas, generando logs detallados.

    Args:
        reason (str): Razón proporcionada por el usuario para el cambio.
        old_rules (list): Lista de reglas antes de la edición.
        new_rules (list): Lista de reglas después de la edición.
    """
    old_map = {r['id']: r for r in copy.deepcopy(old_rules)}
    new_map = {r['id']: r for r in copy.deepcopy(new_rules)}

    # 1. Detección de Creaciones
    for rule_id in new_map:
        if rule_id not in old_map:
            rule = new_map[rule_id]
            conds_str = _format_conditions(rule.get('conditions', []))
            
            log_general_change(
                reason=reason,
                action="Rule Created",
                rule_id=rule_id,
                change_summary=f"Nueva regla: {rule.get('reason', 'Sin nombre')} (Prio: {rule.get('priority')}, Conds: {conds_str})"
            )

    # 2. Detección de Eliminaciones
    for rule_id in old_map:
        if rule_id not in new_map:
            rule = old_map[rule_id]
            log_general_change(
                reason=reason,
                action="Rule Deleted",
                rule_id=rule_id,
                change_summary=f"Regla eliminada: {rule.get('reason', 'Sin nombre')}"
            )

    # 3. Detección de Modificaciones (Diff)
    for rule_id in new_map:
        if rule_id in old_map:
            old_rule = old_map[rule_id]
            new_rule = new_map[rule_id]
            changes = []
            
            # Atributos críticos a monitorear
            keys_to_compare = ["enabled", "order", "priority", "reason", "conditions"]
            
            for key in keys_to_compare:
                val_old = str(old_rule.get(key, ""))
                val_new = str(new_rule.get(key, ""))
                
                if val_old != val_new:
                    changes.append(f"{key}: '{val_old}' -> '{val_new}'")
            
            if changes:
                log_general_change(
                    reason=reason,
                    action="Rule Modified",
                    rule_id=rule_id,
                    change_summary=f"Regla '{new_rule.get('reason')}' modif: " + "; ".join(changes)
                )

def get_audit_log_excel() -> bytes:
    """Genera un archivo Excel en memoria con todo el historial de auditoría.

    Returns:
        bytes: El contenido binario del archivo Excel (.xlsx), listo para
            ser usado en un botón de descarga de Streamlit.
    """
    log_df = pd.DataFrame(st.session_state.get('audit_log', []))
    
    if not log_df.empty:
        # Normalización de columnas para asegurar estructura consistente
        cols_order = ["timestamp", "user", "action", "reason_for_change", "row_id", "rule_id", "change_summary"]
        for col in cols_order:
            if col not in log_df.columns:
                log_df[col] = np.nan
        
        log_df = log_df[cols_order]
        # Formato legible de fecha
        log_df['timestamp'] = pd.to_datetime(log_df['timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        log_df = log_df.fillna("")
        # Orden descendente (más reciente primero)
        log_df = log_df.sort_values(by="timestamp", ascending=False)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        log_df.to_excel(writer, index=False, sheet_name='Audit_Log_General')
    return output.getvalue()