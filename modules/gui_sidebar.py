# modules/gui_sidebar.py
import streamlit as st
import json
import pandas as pd
from modules.translator import get_text, translate_column
from modules.utils import clear_state_and_prepare_reload
from modules.rules_service import get_default_rules, apply_priority_rules
from modules.audit_service import get_audit_log_excel

def _callback_open_rules_editor(): st.session_state.show_rules_editor = True

def _clear_rules_editor_cache():
    for key in ['rules_editor_temp_df', 'rules_editor_original_rules', 'rules_editor_data']:
        if key in st.session_state: del st.session_state[key]

def callback_process_config(file):
    if file is None: return False
    try:
        conf = json.load(file)
        
        # Cargar configuraciones básicas
        st.session_state.filtros_activos = conf.get("filtros_activos", [])
        st.session_state.columnas_visibles = conf.get("columnas_visibles", st.session_state.columnas_visibles)
        st.session_state.language = conf.get("language", st.session_state.language)
        
        # Protección del Usuario
        usuario_cargado = conf.get("username", "")
        if usuario_cargado:
            st.session_state.username = usuario_cargado
            
        # Cargar Log y Reglas
        st.session_state.audit_log = conf.get("audit_log", [])
        st.session_state.priority_rules = conf.get("priority_rules", get_default_rules())
        st.session_state.autocomplete_options = conf.get("autocomplete_options", st.session_state.get("autocomplete_options", {}))
        
        # Cargar Datos y ESTABLECER COMO NUEVO PUNTO ESTABLE
        if "df_staging_data" in conf and conf["df_staging_data"]:
            st.session_state.df_staging = pd.DataFrame.from_records(json.loads(conf["df_staging_data"]))
        elif st.session_state.df_staging is not None:
            # Si solo se cargan reglas sobre datos existentes, recalcular
            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging.copy())

        # [FIX CRÍTICO]: Actualizar df_original para que sea igual al staging cargado.
        # Esto evita que Ctrl+Z revierta a un estado anterior sin las reglas/banderas de la config.
        if st.session_state.df_staging is not None:
            st.session_state.df_original = st.session_state.df_staging.copy()

        _clear_rules_editor_cache()
        st.session_state.current_data_hash = None
        st.session_state.editor_state = None
        if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
    except Exception as e:
        st.error(f"Error config: {e}")
        return False
    return True

def render_sidebar(lang, df_loaded, todas_las_columnas_ui=None, col_map_es_to_en=None, todas_las_columnas_en=None):
    # --- SECCIÓN PERFIL Y LOG ---
    st.sidebar.markdown("### 👤 Perfil & Auditoría")
    
    if st.session_state.username is None: st.session_state.username = ""
    st.session_state.username = st.sidebar.text_input("Usuario Activo", value=st.session_state.username, placeholder="Ej. Juan Perez")
    
    if not st.session_state.username: 
        st.sidebar.warning("Ingrese usuario para registrar acciones.")
    
    log_data = get_audit_log_excel()
    st.sidebar.download_button(
        label="📥 Descargar Log de Auditoría",
        data=log_data,
        file_name="log_auditoria_general.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Descarga el historial completo de cambios (Excel)."
    )

    st.sidebar.markdown("---")

    # --- IDIOMA ---
    opts = {"Español": "es", "English": "en"}
    def cb_lang(): st.session_state.language = opts[st.session_state.language_selector_key]
    curr = {v: k for k, v in opts.items()}.get(st.session_state.language, "Español")
    st.sidebar.radio("Idioma / Language", opts.keys(), index=list(opts.keys()).index(curr), key='language_selector_key', on_change=cb_lang)

    st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")
    up_files = st.sidebar.file_uploader("Cargar Excel / Upload Excel", type=["xlsx"], accept_multiple_files=True, on_change=clear_state_and_prepare_reload)

    if df_loaded:
        # --- Filtros ---
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        col_sel = st.selectbox(get_text(lang, 'column_select'), [""] + todas_las_columnas_ui, key='filter_col_select')
        col_en = col_map_es_to_en.get(col_sel, col_sel)
        
        if col_en in st.session_state.autocomplete_options:
            st.selectbox(get_text(lang, 'column_select_value'), [""] + sorted(st.session_state.autocomplete_options[col_en]), key='filter_val_select')
        else:
            st.text_input(get_text(lang, 'search_text'), key='filter_val_text')

        if st.button(get_text(lang, 'add_filter_button')):
            val = st.session_state.filter_val_select if col_en in st.session_state.autocomplete_options else st.session_state.filter_val_text
            if col_sel and val:
                st.session_state.filtros_activos.append({"columna": col_en, "valor": val})
                st.rerun()

        # --- Columnas Visibles ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")
        if st.session_state.columnas_visibles is None: st.session_state.columnas_visibles = todas_las_columnas_en

        def cb_cols(): 
            selected_ui = st.session_state.visible_cols_multiselect
            st.session_state.columnas_visibles = [c for c in todas_las_columnas_en if translate_column(lang, c) in selected_ui]

        defaults_ui_validos = [
            translate_column(lang, c) 
            for c in st.session_state.columnas_visibles 
            if translate_column(lang, c) in todas_las_columnas_ui
        ]

        st.sidebar.multiselect(
            get_text(lang, 'visible_cols_select'),
            options=todas_las_columnas_ui,
            default=defaults_ui_validos,
            key='visible_cols_multiselect',
            on_change=cb_cols
        )

        # --- Configuración ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'config_header')}")
        
        df_json = st.session_state.df_staging.to_json(orient="records") if st.session_state.df_staging is not None else None
        config_data = {
            "filtros_activos": st.session_state.filtros_activos,
            "columnas_visibles": st.session_state.columnas_visibles,
            "language": st.session_state.language,
            "username": st.session_state.username,
            "audit_log": st.session_state.audit_log,
            "priority_rules": st.session_state.priority_rules,
            "autocomplete_options": st.session_state.autocomplete_options,
            "df_staging_data": df_json
        }
        st.sidebar.download_button("💾 Guardar Configuración", json.dumps(config_data, indent=2), "config.json", "application/json")
        
        conf_up = st.sidebar.file_uploader("📂 Cargar Configuración", type=["json"], key="config_uploader")
        if conf_up and not st.session_state.config_file_processed:
            if callback_process_config(conf_up):
                st.session_state.config_file_processed = True
                st.rerun()

        if st.sidebar.button("🔄 Resetear Todo"):
            clear_state_and_prepare_reload()
            st.session_state.priority_rules = get_default_rules()
            _clear_rules_editor_cache()
            st.rerun()

        # --- Reglas ---
        st.sidebar.markdown("---")
        st.sidebar.button(get_text(lang, 'rules_edit_button'), on_click=_callback_open_rules_editor)

        # --- Gestor de Listas ---
        if st.session_state.autocomplete_options:
            st.sidebar.markdown("---")
            with st.sidebar.expander("📋 Gestionar Listas", expanded=False):
                col_list_ui = st.selectbox("Editar lista de:", sorted(todas_las_columnas_ui), key="sel_list_edit")
                col_list_en = col_map_es_to_en.get(col_list_ui, col_list_ui)
                
                if col_list_en in st.session_state.autocomplete_options:
                    curr_opts = st.session_state.autocomplete_options[col_list_en]
                    st.write(f"**{len(curr_opts)} opciones.**")
                    
                    new_op = st.text_input("Nueva opción:", key="new_op_txt")
                    if st.button("➕ Añadir"):
                        if new_op and new_op not in curr_opts:
                            curr_opts.append(new_op)
                            st.session_state.autocomplete_options[col_list_en] = sorted(curr_opts)
                            st.rerun()
                    
                    del_ops = st.multiselect("Borrar opciones:", curr_opts, key="del_ops_mul")
                    if st.button("🗑️ Borrar Seleccionados"):
                        st.session_state.autocomplete_options[col_list_en] = [x for x in curr_opts if x not in del_ops]
                        st.rerun()

    return up_files