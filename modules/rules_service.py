# modules/rules_service.py
"""
Servicio de Reglas de Negocio (Rules Service).

Motor de reglas de negocio (Versión 2.1 - Prioridad Inversa).
Permite evaluar reglas complejas con múltiples condiciones y operadores lógicos
para asignar prioridades automáticamente.

NOTA IMPORTANTE:
Para evitar que reglas generales sobrescriban a reglas específicas de alta prioridad,
el sistema ahora aplica las reglas en orden INVERSO de su número de 'Orden'.
- Primero se ejecutan las reglas de orden alto (ej. 100).
- Al final se ejecutan las reglas de orden bajo (ej. 1).
De esta forma, la regla con el número más pequeño es la que "gana" al final.
"""

import streamlit as st
import pandas as pd
import numpy as np

def get_default_rules():
    """
    Define las reglas por defecto del sistema.
    
    Returns:
        list: Lista de diccionarios con la configuración de reglas.
    """
    return [
        {
            "id": "rule_sys_001",
            "enabled": True,
            "order": 10,
            "priority": "🚩 Maxima Prioridad",
            "reason": "Sistema: Pay Group Crítico",
            "conditions": [
                {"column": "Pay Group", "operator": "is", "value": "DIST"}
            ]
        },
        {
            "id": "rule_sys_002",
            "enabled": True,
            "order": 20,
            "priority": "Alta",
            "reason": "Sistema: Monto Alto (> 10k)",
            "conditions": [
                {"column": "Total", "operator": ">", "value": 10000}
            ]
        }
    ]

def _evaluate_condition(df: pd.DataFrame, condition: dict) -> pd.Series:
    """
    Evalúa una sola condición contra el DataFrame de forma vectorizada.
    
    Args:
        df (pd.DataFrame): DataFrame a evaluar.
        condition (dict): Diccionario con keys 'column', 'operator', 'value'.
        
    Returns:
        pd.Series: Serie booleana (True donde se cumple la condición).
    """
    col = condition.get("column")
    op = condition.get("operator")
    val = condition.get("value")

    if col not in df.columns:
        return pd.Series(False, index=df.index)

    # Normalización de la columna base
    series = df[col]
    
    # --- Lógica Numérica (Operadores Matemáticos) ---
    if op in [">", "<", ">=", "<="]:
        # Convertir columna a número forzosamente, errores a 0
        series_numeric = pd.to_numeric(series, errors='coerce').fillna(0)
        try:
            val_numeric = float(val)
        except (ValueError, TypeError):
            val_numeric = 0.0
            
        if op == ">": return series_numeric > val_numeric
        if op == "<": return series_numeric < val_numeric
        if op == ">=": return series_numeric >= val_numeric
        if op == "<=": return series_numeric <= val_numeric

    # --- Lógica de Texto (Operadores de String) ---
    # Convertir todo a string para evitar errores de tipo
    series_str = series.fillna("").astype(str)
    val_str = str(val)

    if op == "contains":
        return series_str.str.contains(val_str, case=False, na=False)
    elif op == "is":
        # Comparación exacta insensible a mayúsculas
        return series_str.str.lower() == val_str.lower()
    elif op == "is_not":
        return series_str.str.lower() != val_str.lower()
    elif op == "starts_with":
        return series_str.str.lower().str.startswith(val_str.lower())
    
    return pd.Series(False, index=df.index)

def apply_priority_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica el motor de reglas multi-condición al DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame de entrada.
        
    Returns:
        pd.DataFrame: DataFrame con las columnas 'Priority' y 'Priority_Reason' actualizadas.
    """
    if 'Priority' not in df.columns:
        return df

    # 1. Obtener reglas del estado o cargar defaults
    rules = st.session_state.get('priority_rules')
    if not rules or not isinstance(rules, list):
        rules = get_default_rules()
        st.session_state.priority_rules = rules
        
    # --- CORRECCIÓN CRÍTICA: ORDEN INVERSO ---
    # Ordenar por campo 'order'. Usamos reverse=True para que las reglas con
    # números ALTOS se ejecuten primero, y las de números BAJOS (más importantes)
    # se ejecuten al final, sobrescribiendo el resultado.
    active_rules = sorted(
        [r for r in rules if r.get('enabled', True)],
        key=lambda x: x.get('order', 99),
        reverse=True 
    )
    
    # 2. Inicializar columnas temporales de cálculo
    df['Priority_Calculated'] = "Sin Regla Asignada"
    df['Priority_Reason'] = "Sin Regla Asignada"
    
    # 3. Procesar cada regla
    for rule in active_rules:
        conditions = rule.get('conditions', [])
        if not conditions:
            continue
            
        try:
            # Comenzar con una máscara donde TODO es True (para lógica AND)
            final_mask = pd.Series(True, index=df.index)
            
            # Intersección de máscaras (AND) de cada condición
            for cond in conditions:
                cond_mask = _evaluate_condition(df, cond)
                final_mask = final_mask & cond_mask
            
            # Aplicar cambios si hay coincidencias
            if final_mask.any():
                r_prio = rule.get('priority', 'Media')
                r_reason = rule.get('reason', 'Regla Personalizada')
                
                df.loc[final_mask, 'Priority_Calculated'] = r_prio
                df.loc[final_mask, 'Priority_Reason'] = r_reason
                
        except Exception as e:
            print(f"Error aplicando regla {rule.get('id')}: {e}")
            continue

    # 4. Preservar ingresos manuales (Override del Usuario)
    # Si el motor NO asignó regla, pero el usuario tenía un valor manual válido, restaurarlo.
    manual_priorities = [
        "Minima", "Media", "Alta", "🚩 Maxima Prioridad",  # Español
        "Low", "Medium", "High", "🚩 Max Priority"         # Inglés
    ]
    
    mask_no_rule_applied = (df['Priority_Reason'] == "Sin Regla Asignada")
    mask_had_manual_value = df['Priority'].isin(manual_priorities) & (df['Priority'] != "")
    
    mask_restore_manual = mask_no_rule_applied & mask_had_manual_value
    
    if mask_restore_manual.any():
        df.loc[mask_restore_manual, 'Priority_Calculated'] = df.loc[mask_restore_manual, 'Priority']
        df.loc[mask_restore_manual, 'Priority_Reason'] = "Ingreso Manual"
    
    # 5. Finalizar y limpiar
    df['Priority'] = df['Priority_Calculated']
    
    return df.drop(columns=['Priority_Calculated'], errors='ignore')