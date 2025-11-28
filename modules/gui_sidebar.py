# modules/gui_sidebar.py
"""
Módulo de Barra Lateral (Sidebar).

Este módulo gestiona los componentes de la barra lateral izquierda de la aplicación.
Incluye la carga de archivos, la gestión de perfiles de usuario, la configuración
(guardar/cargar estado) y la administración de listas de autocompletado.
"""

import streamlit as st
import json
import pandas as pd
from modules.translator import get_text, translate_column
from modules.utils import clear_state_and_prepare_reload
from modules.rules_service import get_default_rules, apply_priority_rules
from modules.audit_service import get_audit_log_excel

def _callback_open_rules_editor():
    """Callback simple para activar la bandera que muestra el editor de reglas."""
    st.session_state.show_rules_editor = True
    # ACTIVAR TRIGGER: Indicamos que hay una intención explícita de abrirlo
    st.session_state.rules_open_trigger = True 

def _clear_rules_editor_cache():
    """
    Limpia las variables temporales de la sesión utilizadas por el editor de reglas.
    Se llama al cargar una nueva configuración para evitar estados inconsistentes.
    """
    for key in ['rules_editor_temp_df', 'rules_editor_original_rules', 'rules_editor_data']:
        if key in st.session_state:
            del st.session_state[key]

def callback_process_config(file) -> bool:
    """Procesa un archivo de configuración JSON subido por el usuario.

    Restaura el estado completo de la aplicación (filtros, reglas, idioma, datos)
    desde un archivo de respaldo.

    Args:
        file: El objeto de archivo (UploadedFile) proporcionado por st.file_uploader.

    Returns:
        bool: True si la configuración se cargó exitosamente, False si hubo error.
    """
    if not file:
        return False
    try:
        d = json.load(file)
        
        # Restauración de variables de estado básicas
        st.session_state.filtros_activos = d.get("filtros_activos", [])
        st.session_state.columnas_visibles = d.get("columnas_visibles", st.session_state.columnas_visibles)
        st.session_state.language = d.get("language", "es")
        
        # Restauración del usuario activo
        usr = d.get("username", "")
        if usr:
            st.session_state.username = usr
            
        # Restauración de logs y reglas
        st.session_state.audit_log = d.get("audit_log", [])
        st.session_state.priority_rules = d.get("priority_rules", get_default_rules())
        st.session_state.autocomplete_options = d.get("autocomplete_options", st.session_state.get("autocomplete_options", {}))

        # Restauración de los datos (DataFrame)
        if "df_staging_data" in d and d["df_staging_data"]:
            # Si el JSON contiene los datos, se reconstruye el DataFrame
            st.session_state.df_staging = pd.DataFrame.from_records(json.loads(d["df_staging_data"]))
        elif st.session_state.df_staging is not None:
            # Si no hay datos en el JSON pero ya hay datos cargados, reaplicamos las reglas importadas
            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging.copy())

        # Sincronización del DataFrame original si se cargaron datos nuevos
        if st.session_state.df_staging is not None:
            st.session_state.df_original = st.session_state.df_staging.copy()
        
        # Limpieza de cachés y forzado de actualización de UI
        _clear_rules_editor_cache()
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        
        # Incrementamos la versión del editor para forzar un re-renderizado completo
        if 'editor_key_ver' in st.session_state:
            st.session_state.editor_key_ver += 1
            
        return True
    except Exception as e:
        st.error(f"Error config: {e}")
        return False

def render_sidebar(lang: str, df_loaded: bool, cols_ui: list, map_en: dict, cols_en: list):
    """Renderiza la interfaz gráfica de la barra lateral.

    Args:
        lang (str): Código de idioma actual ('es' o 'en').
        df_loaded (bool): True si hay un DataFrame cargado actualmente.
        cols_ui (list): Lista de nombres de columnas traducidos (para mostrar en UI).
        map_en (dict): Diccionario de mapeo {Nombre Traducido -> Nombre Real (Inglés)}.
        cols_en (list): Lista de nombres de columnas reales (en inglés/base de datos).

    Returns:
        list: Lista de archivos subidos (UploadedFile) si el usuario cargó nuevos archivos.
    """
    
    # --- DEFINICIÓN CRÍTICA DE VARIABLES ---
    # Recuperamos las opciones de autocompletado al inicio para usarlas en cualquier parte del sidebar
    auto_opts = st.session_state.autocomplete_options

    # --- Sección: Perfil y Auditoría ---
    st.sidebar.markdown("### 👤 Perfil & Auditoría")
    
    if st.session_state.username is None:
        st.session_state.username = ""
        
    # Input para el nombre de usuario (usado en los logs)
    st.session_state.username = st.sidebar.text_input(
        get_text(lang, 'user_active_label'), 
        value=st.session_state.username, 
        placeholder=get_text(lang, 'user_placeholder')
    )
    
    if not st.session_state.username: 
        st.sidebar.warning(get_text(lang, 'user_warning'))
    
    # Botón para descargar el log de auditoría
    log_data = get_audit_log_excel()
    st.sidebar.download_button(
        get_text(lang, 'audit_log_sidebar_btn'), 
        data=log_data, 
        file_name="log_auditoria_general.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.sidebar.markdown("---")
    
    # --- Sección: Selector de Idioma ---
    opts = {"Español": "es", "English": "en"}
    
    def cb_lang():
        """Callback interno para actualizar el idioma en sesión."""
        st.session_state.language = opts[st.session_state.language_selector_key]
        
    # Determinar la selección actual para el radio button
    curr = {v: k for k, v in opts.items()}.get(st.session_state.language, "Español")
    st.sidebar.radio(
        "Idioma / Language", 
        opts.keys(), 
        index=list(opts.keys()).index(curr), 
        key='language_selector_key', 
        on_change=cb_lang
    )

    st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")
    
    # --- Sección: Carga de Archivos ---
    # on_change=clear_state... asegura que se resetee todo al subir nuevos archivos
    up_files = st.sidebar.file_uploader(
        get_text(lang, 'uploader_label'), 
        type=["xlsx"], 
        accept_multiple_files=True, 
        on_change=clear_state_and_prepare_reload
    )

    # --- Lógica condicional: Solo si hay datos cargados ---
    if df_loaded:
        
        # 1. Filtro Especial por Regla de Prioridad
        if 'Priority_Reason' in st.session_state.df_staging.columns:
            st.sidebar.markdown("### 🔍 Filtrar por Regla")
            
            # Obtener razones únicas para el dropdown
            reasons = sorted(list(st.session_state.df_staging['Priority_Reason'].unique()))
            
            # Asegurar que "Sin Regla Asignada" aparezca primero para facilitar el flujo
            if "Sin Regla Asignada" in reasons:
                reasons.remove("Sin Regla Asignada")
                reasons = ["Sin Regla Asignada"] + reasons
                
            selected_rule = st.sidebar.selectbox(
                "Seleccione una regla aplicada:",
                ["(Todos)"] + reasons,
                key="filter_by_rule_select"
            )
            
            # Lógica para aplicar este filtro especial
            if selected_rule != "(Todos)":
                # Limpiamos filtros previos de 'Priority_Reason' para evitar duplicados
                st.session_state.filtros_activos = [f for f in st.session_state.filtros_activos if f['columna'] != 'Priority_Reason']
                st.session_state.filtros_activos.append({"columna": "Priority_Reason", "valor": selected_rule})
            else:
                # Si selecciona "Todos", eliminamos el filtro de la lista activa
                if any(f['columna'] == 'Priority_Reason' for f in st.session_state.filtros_activos):
                     st.session_state.filtros_activos = [f for f in st.session_state.filtros_activos if f['columna'] != 'Priority_Reason']
                     st.rerun()

        # 2. Filtros Estándar (RESTITUIDOS)
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        cols_visual = []
        
        # Generamos nombres visuales (con icono 📋 si tienen autocompletado)
        for col in cols_ui:
            col_en = map_en.get(col, col)
            if col_en in auto_opts and auto_opts[col_en]:
                cols_visual.append(f"{col} 📋") 
            else:
                cols_visual.append(col)

        # Selectores de columna y valor
        col_sel_visual = st.sidebar.selectbox(get_text(lang, 'column_select'), [""] + cols_visual, key='filter_col_select')
        col_sel_clean = col_sel_visual.replace(" 📋", "")
        col_en = map_en.get(col_sel_clean, col_sel_clean)
        
        # Determinar si mostramos dropdown (select) o campo de texto (input)
        available_opts = auto_opts.get(col_en, [])
        if available_opts:
            st.sidebar.selectbox(get_text(lang, 'column_select_value'), [""] + sorted(available_opts), key='filter_val_select')
        else:
            st.sidebar.text_input(get_text(lang, 'search_text'), key='filter_val_text')

        # Botón para añadir filtro
        if st.sidebar.button(get_text(lang, 'add_filter_button')):
            val = st.session_state.filter_val_select if available_opts else st.session_state.filter_val_text
            if col_sel_clean and val:
                st.session_state.filtros_activos.append({"columna": col_en, "valor": val})
                st.rerun()

        # 3. Gestión de Columnas Visibles
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")
        
        # Inicialización por defecto
        if st.session_state.columnas_visibles is None: 
            st.session_state.columnas_visibles = cols_en

        def cb_toggle_cols():
            """Alterna entre seleccionar todas las columnas o ninguna."""
            if len(st.session_state.columnas_visibles) == len(cols_en): 
                st.session_state.columnas_visibles = []
            else: 
                st.session_state.columnas_visibles = list(cols_en)
            # Sincroniza el multiselect visual
            st.session_state.visible_cols_multiselect = [translate_column(lang, c) for c in st.session_state.columnas_visibles if translate_column(lang, c) in cols_ui]

        st.sidebar.button(get_text(lang, 'visible_cols_toggle_button'), on_click=cb_toggle_cols)

        def cb_cols(): 
            """Callback al cambiar la selección manual de columnas."""
            selected_ui = st.session_state.visible_cols_multiselect
            st.session_state.columnas_visibles = [c for c in cols_en if translate_column(lang, c) in selected_ui]

        # Filtrar defaults para evitar errores si cols_ui cambia
        defaults_ui_validos = [translate_column(lang, c) for c in st.session_state.columnas_visibles if translate_column(lang, c) in cols_ui]
        
        st.sidebar.multiselect(
            get_text(lang, 'visible_cols_select'), 
            options=cols_ui, 
            default=defaults_ui_validos, 
            key='visible_cols_multiselect', 
            on_change=cb_cols
        )

        # 4. Gestión de Configuración (Guardar/Cargar JSON)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'config_header')}")
        
        # Serializamos el DataFrame a JSON para guardarlo en el archivo de config
        df_json = st.session_state.df_staging.to_json(orient="records") if st.session_state.df_staging is not None else None
        
        config_data = {
            "filtros_activos": st.session_state.filtros_activos,
            "columnas_visibles": st.session_state.columnas_visibles,
            "language": st.session_state.language,
            "username": st.session_state.username,
            "audit_log": st.session_state.audit_log,
            "priority_rules": st.session_state.priority_rules,
            "autocomplete_options": st.session_state.autocomplete_options,
            "df_staging_data": df_json # Guardamos los datos también
        }
        
        st.sidebar.download_button(
            get_text(lang, 'save_config_button'), 
            json.dumps(config_data, indent=2), 
            "config.json", 
            "application/json"
        )
        
        conf_up = st.sidebar.file_uploader(get_text(lang, 'load_config_label'), type=["json"], key="config_uploader")
        if conf_up and not st.session_state.config_file_processed:
            if callback_process_config(conf_up):
                st.session_state.config_file_processed = True
                st.rerun()

        if st.sidebar.button(get_text(lang, 'reset_config_button')):
            # Reseteo completo de la aplicación a valores de fábrica
            clear_state_and_prepare_reload()
            st.session_state.priority_rules = get_default_rules()
            _clear_rules_editor_cache()
            st.rerun()

        # 5. Botón para abrir el Editor de Reglas
        st.sidebar.markdown("---")
        st.sidebar.button(get_text(lang, 'rules_edit_button'), on_click=_callback_open_rules_editor)

        # 6. Gestor de Listas y Analizador de Valores
        st.sidebar.markdown("---")
        with st.sidebar.expander(get_text(lang, 'manage_lists_expander'), expanded=False):
            # Preparamos lista de columnas para el selector
            list_visual_all = []
            for c in cols_ui:
                cen = map_en.get(c, c)
                if cen in auto_opts and auto_opts[cen]: 
                    list_visual_all.append(f"{c} 📋")
                else:
                    list_visual_all.append(c)
            
            col_list_visual = st.selectbox(get_text(lang, 'select_column_to_edit'), sorted(list_visual_all), key="sel_list_edit")
            col_list_clean = col_list_visual.replace(" 📋", "")
            col_list_en = map_en.get(col_list_clean, col_list_clean)
            
            # Si la columna ya tiene opciones, permitimos editar
            if col_list_en in st.session_state.autocomplete_options and st.session_state.autocomplete_options[col_list_en]:
                curr_opts = st.session_state.autocomplete_options[col_list_en]
                st.success(f"✅ Autocompletado activo ({len(curr_opts)} opciones).")
                
                # Añadir nueva opción
                new_op = st.text_input(get_text(lang, 'add_option_label'), key="new_op_txt")
                if st.button(get_text(lang, 'add_option_btn')):
                    if new_op and new_op not in curr_opts:
                        curr_opts.append(new_op)
                        st.session_state.autocomplete_options[col_list_en] = sorted(curr_opts)
                        st.rerun()
                
                # Eliminar opciones existentes
                del_ops = st.multiselect(get_text(lang, 'remove_options_label'), curr_opts, key="del_ops_mul")
                if st.button(get_text(lang, 'remove_option_btn')):
                    st.session_state.autocomplete_options[col_list_en] = [x for x in curr_opts if x not in del_ops]
                    st.rerun()
            else:
                # Si no tiene opciones, ofrecemos analizar los datos existentes
                st.warning(get_text(lang, 'no_list_warning'))
                st.info(get_text(lang, 'analyze_info'))
                
                if st.button(get_text(lang, 'analyze_values_button')):
                    if st.session_state.df_staging is not None and col_list_en in st.session_state.df_staging.columns:
                        try:
                            # Extraemos valores únicos, ignorando nulos
                            unique_vals = st.session_state.df_staging[col_list_en].fillna("").astype(str).unique().tolist()
                            unique_vals = sorted([x for x in unique_vals if x.strip() != ""])
                            
                            if unique_vals:
                                st.session_state.autocomplete_options[col_list_en] = unique_vals
                                st.success(get_text(lang, 'analyze_success').format(n=len(unique_vals)))
                                st.rerun()
                            else:
                                st.warning(get_text(lang, 'analyze_empty'))
                        except Exception as e:
                            st.error(get_text(lang, 'analyze_error').format(e=e))

    return up_files