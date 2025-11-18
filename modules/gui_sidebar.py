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
    if not file: return False
    try:
        d = json.load(file)
        st.session_state.filtros_activos = d.get("filtros_activos", [])
        st.session_state.columnas_visibles = d.get("columnas_visibles", st.session_state.columnas_visibles)
        st.session_state.language = d.get("language", "es")
        
        usr = d.get("username", "")
        if usr: st.session_state.username = usr
            
        st.session_state.audit_log = d.get("audit_log", [])
        st.session_state.priority_rules = d.get("priority_rules", get_default_rules())
        st.session_state.autocomplete_options = d.get("autocomplete_options", st.session_state.get("autocomplete_options", {}))

        if "df_staging_data" in d and d["df_staging_data"]:
            st.session_state.df_staging = pd.DataFrame.from_records(json.loads(d["df_staging_data"]))
        elif st.session_state.df_staging is not None:
            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging.copy())

        if st.session_state.df_staging is not None:
            st.session_state.df_original = st.session_state.df_staging.copy()
        
        _clear_rules_editor_cache()
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
        return True
    except Exception as e:
        st.error(f"Error config: {e}")
        return False

def render_sidebar(lang, df_loaded, cols_ui, map_en, cols_en):
    st.sidebar.markdown("### 👤 Perfil & Auditoría")
    
    if st.session_state.username is None: st.session_state.username = ""
    st.session_state.username = st.sidebar.text_input("Usuario Activo", value=st.session_state.username, placeholder="Ej. Juan Perez")
    
    if not st.session_state.username: 
        st.sidebar.warning("Ingrese usuario para registrar acciones.")
    
    log_data = get_audit_log_excel()
    st.sidebar.download_button("📥 Descargar Log de Auditoría", data=log_data, file_name="log_auditoria_general.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.sidebar.markdown("---")
    opts = {"Español": "es", "English": "en"}
    def cb_lang(): st.session_state.language = opts[st.session_state.language_selector_key]
    curr = {v: k for k, v in opts.items()}.get(st.session_state.language, "Español")
    st.sidebar.radio("Idioma / Language", opts.keys(), index=list(opts.keys()).index(curr), key='language_selector_key', on_change=cb_lang)

    st.sidebar.markdown(f"## {get_text(lang, 'control_area')}")
    up_files = st.sidebar.file_uploader("Cargar Excel / Upload Excel", type=["xlsx"], accept_multiple_files=True, on_change=clear_state_and_prepare_reload)

    if df_loaded:
        # --- FILTROS ---
        st.sidebar.markdown(f"### {get_text(lang, 'add_filter_header')}")
        auto_opts = st.session_state.autocomplete_options
        cols_visual = []
        
        for col in cols_ui:
            col_en = map_en.get(col, col)
            if col_en in auto_opts and auto_opts[col_en]:
                cols_visual.append(f"{col} 📋") 
            else:
                cols_visual.append(col)

        col_sel_visual = st.selectbox(get_text(lang, 'column_select'), [""] + cols_visual, key='filter_col_select')
        col_sel_clean = col_sel_visual.replace(" 📋", "")
        col_en = map_en.get(col_sel_clean, col_sel_clean)
        
        available_opts = auto_opts.get(col_en, [])
        if available_opts:
            st.selectbox(get_text(lang, 'column_select_value'), [""] + sorted(available_opts), key='filter_val_select')
        else:
            st.text_input(get_text(lang, 'search_text'), key='filter_val_text')

        if st.button(get_text(lang, 'add_filter_button')):
            val = st.session_state.filter_val_select if available_opts else st.session_state.filter_val_text
            if col_sel_clean and val:
                st.session_state.filtros_activos.append({"columna": col_en, "valor": val})
                st.rerun()

        # --- Columnas Visibles ---
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {get_text(lang, 'visible_cols_header')}")
        if st.session_state.columnas_visibles is None: st.session_state.columnas_visibles = cols_en

        def cb_toggle_cols():
            if len(st.session_state.columnas_visibles) == len(cols_en): st.session_state.columnas_visibles = []
            else: st.session_state.columnas_visibles = list(cols_en)
            st.session_state.visible_cols_multiselect = [translate_column(lang, c) for c in st.session_state.columnas_visibles if translate_column(lang, c) in cols_ui]

        st.sidebar.button(get_text(lang, 'visible_cols_toggle_button'), on_click=cb_toggle_cols)

        def cb_cols(): 
            selected_ui = st.session_state.visible_cols_multiselect
            st.session_state.columnas_visibles = [c for c in cols_en if translate_column(lang, c) in selected_ui]

        defaults_ui_validos = [translate_column(lang, c) for c in st.session_state.columnas_visibles if translate_column(lang, c) in cols_ui]
        st.sidebar.multiselect(get_text(lang, 'visible_cols_select'), options=cols_ui, default=defaults_ui_validos, key='visible_cols_multiselect', on_change=cb_cols)

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
                # 1. Lista Visual
                list_visual = []
                for c in cols_ui:
                    cen = map_en.get(c, c)
                    if cen in auto_opts: list_visual.append(f"{c} 📋")
                
                col_list_visual = st.selectbox("Editar lista de:", sorted(list_visual), key="sel_list_edit")
                col_list_clean = col_list_visual.replace(" 📋", "")
                col_list_en = map_en.get(col_list_clean, col_list_clean)
                
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