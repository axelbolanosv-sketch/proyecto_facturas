# modules/gui_views.py
# VERSIÓN 8.0: BUSCAR Y REEMPLAZAR CON FILTROS AVANZADOS
# - Se añade sección de filtros opcionales en el modal de Buscar y Reemplazar.
# - Permite restringir el reemplazo basándose en valores de otras columnas.

import streamlit as st
import pandas as pd
import json
import numpy as np
import warnings
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel
from modules.rules_service import apply_priority_rules
from modules.audit_service import log_general_change
import streamlit_hotkeys as hotkeys

# --- MODAL BUSCAR Y REEMPLAZAR (MEJORADO) ---
@st.dialog("🔍 Buscar y Reemplazar")
def modal_find_replace(col_map, lang):
    st.markdown("Esta herramienta buscará y reemplazará valores en la **Columna Objetivo**.")
    
    # 1. Preparar listas visuales
    cols_raw = [c for c in col_map.keys() if "Seleccionar" not in c]
    cols_vis = []
    auto_opts = st.session_state.autocomplete_options
    
    for c in cols_raw:
        cen = col_map.get(c, c)
        cols_vis.append(f"{c} 📋" if cen in auto_opts and auto_opts[cen] else c)
        
    # 2. Selector de Columna Objetivo
    col_sel_vis = st.selectbox("Columna Objetivo (Donde se hará el cambio):", cols_vis)
    col_sel_ui = col_sel_vis.replace(" 📋", "")
    col_en = col_map.get(col_sel_ui, col_sel_ui)
    
    st.markdown("---")
    
    # 3. Inputs de Búsqueda Principal
    c1, c2 = st.columns(2)
    with c1:
        find_txt = st.text_input("Buscar (Valor actual):")
    with c2:
        # Lógica Híbrida: Lista o Manual
        opts = auto_opts.get(col_en, [])
        replace_val = ""
        if opts:
            use_manual = st.checkbox("✍️ Manual", value=False, help="Escribir valor fuera de lista.")
            if use_manual:
                replace_val = st.text_input("Reemplazar con:")
            else:
                replace_val = st.selectbox("Reemplazar con:", [""] + sorted(opts))
        else:
            replace_val = st.text_input("Reemplazar con:")

    # 4. FILTROS ADICIONALES (NUEVO)
    active_filters = {}
    with st.expander("🎯 Filtros Adicionales (Opcional)", expanded=False):
        st.caption("Restringe el cambio a las filas que cumplan estas condiciones extra.")
        
        # Excluir la columna objetivo para no filtrar por la misma que editamos
        filter_opts = [c for c in cols_vis if c != col_sel_vis]
        sel_filters = st.multiselect("Agregar condición en columna:", filter_opts)
        
        if sel_filters:
            for f_vis in sel_filters:
                f_ui = f_vis.replace(" 📋", "")
                f_en = col_map.get(f_ui, f_ui)
                
                # Input dinámico para el filtro
                f_opts_list = auto_opts.get(f_en, [])
                if f_opts_list:
                    # Si es lista, asumimos coincidencia exacta deseada
                    val_f = st.selectbox(f"'{f_ui}' es igual a:", f_opts_list, key=f"fil_{f_en}")
                    if val_f: active_filters[f_en] = {"val": val_f, "type": "exact"}
                else:
                    # Si es texto, asumimos búsqueda parcial
                    val_f = st.text_input(f"'{f_ui}' contiene:", key=f"fil_{f_en}")
                    if val_f: active_filters[f_en] = {"val": val_f, "type": "contains"}

    # 5. Modo de Búsqueda Principal
    st.markdown("---")
    mode = st.radio("Modo de Búsqueda Principal:", ["Coincidencia Exacta", "Contiene (Parcial)"], horizontal=True)
    
    if st.button("🚀 Reemplazar", type="primary", use_container_width=True):
        if not find_txt:
            st.error("Escriba qué buscar.")
        else:
            df = st.session_state.df_staging.copy()
            
            if col_en in df.columns:
                # A. Máscara Principal (Búsqueda)
                mask_main = None
                if mode == "Coincidencia Exacta":
                    mask_main = (df[col_en].astype(str) == find_txt)
                else:
                    mask_main = (df[col_en].astype(str).str.contains(find_txt, case=False, na=False))
                
                # B. Máscara de Filtros (Adicionales)
                mask_filters = pd.Series(True, index=df.index)
                filter_desc = []
                
                for f_col, f_data in active_filters.items():
                    if f_col in df.columns:
                        f_val = f_data["val"]
                        if f_data["type"] == "exact":
                            mask_filters &= (df[f_col].astype(str) == str(f_val))
                            filter_desc.append(f"{f_col}={f_val}")
                        else:
                            mask_filters &= (df[f_col].astype(str).str.contains(str(f_val), case=False, na=False))
                            filter_desc.append(f"{f_col}~{f_val}")

                # C. Máscara Final
                final_mask = mask_main & mask_filters
                count = final_mask.sum()
                
                if count > 0:
                    # Fix tipos numéricos
                    final_val_typed = replace_val
                    if pd.api.types.is_numeric_dtype(df[col_en].dtype):
                        try: final_val_typed = pd.to_numeric(replace_val)
                        except: pass
                    
                    # Aplicar
                    df.loc[final_mask, col_en] = final_val_typed
                    
                    # Fix Autocompletado (Si agregamos un valor nuevo a una lista)
                    if col_en in st.session_state.autocomplete_options:
                        v_str = str(final_val_typed)
                        c_opts = st.session_state.autocomplete_options[col_en]
                        if v_str not in c_opts:
                            c_opts.append(v_str)
                            st.session_state.autocomplete_options[col_en] = sorted(c_opts)

                    # Log
                    filters_str = f" | Filtros: {', '.join(filter_desc)}" if filter_desc else ""
                    log_general_change("Find/Replace", "Bulk Replace", f"En '{col_en}': '{find_txt}' -> '{final_val_typed}' ({count} filas){filters_str}")
                    
                    # Guardar
                    st.session_state.df_staging = apply_priority_rules(df)
                    
                    # Recalcular Row Status
                    col_stat = "Row Status"
                    if col_stat in st.session_state.df_staging.columns:
                        chk = st.session_state.df_staging.drop(columns=[col_stat, 'Priority_Reason'], errors='ignore').fillna("").astype(str)
                        inc = (chk == "") | (chk == "0")
                        st.session_state.df_staging[col_stat] = np.where(inc.any(axis=1), get_text(lang, 'status_incomplete'), get_text(lang, 'status_complete'))
                    
                    st.session_state.editor_state = None
                    st.session_state.current_data_hash = None
                    if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
                    
                    st.success(f"✅ {count} filas actualizadas.")
                    st.rerun()
                else:
                    st.warning("No se encontraron coincidencias con esos criterios.")
            else:
                st.error("Columna no encontrada.")


# --- 0. EDICIÓN MASIVA ---
@st.dialog("✏️ Edición Masiva / Bulk Edit")
def modal_bulk_edit(indices_seleccionados: list, col_map_ui_to_en: dict, lang: str):
    st.markdown(f"Se editarán **{len(indices_seleccionados)}** facturas seleccionadas.")

    cols_raw = [c for c in col_map_ui_to_en.keys() if "Seleccionar" not in c and "ID" not in c]
    cols_vis = []
    auto_opts = st.session_state.autocomplete_options
    
    for c_ui in cols_raw:
        c_en = col_map_ui_to_en.get(c_ui, c_ui)
        if c_en in auto_opts and auto_opts[c_en]:
            cols_vis.append(f"{c_ui} 📋")
        else:
            cols_vis.append(c_ui)

    col_ui_visual = st.selectbox("¿Qué columna desea editar?", cols_vis)
    col_ui = col_ui_visual.replace(" 📋", "")
    col_en = col_map_ui_to_en.get(col_ui, col_ui)

    opts = auto_opts.get(col_en, [])
    nuevo_valor = None
    
    if opts:
        use_manual = st.checkbox("✍️ Ingresar manualmente", value=False, key="chk_manual_bulk")
        if use_manual:
            nuevo_valor = st.text_input(f"Valor manual para '{col_ui}':")
        else:
            nuevo_valor = st.selectbox(f"Valor para '{col_ui}':", opts, index=None, placeholder="Seleccione...")
    else:
        nuevo_valor = st.text_input(f"Valor para '{col_ui}':")

    st.warning("⚠️ Esta acción requiere 'Guardar Borrador' posteriormente para persistir cambios complejos.")

    if st.button("Aplicar Cambios", type="primary"):
        if nuevo_valor is not None:
            try:
                df = st.session_state.df_staging.copy()
                val_final = nuevo_valor
                
                if col_en in df.columns and pd.api.types.is_numeric_dtype(df[col_en].dtype):
                    try: val_final = pd.to_numeric(nuevo_valor)
                    except: st.warning("Guardando texto en columna numérica.")

                count = 0
                for idx in indices_seleccionados:
                    if idx in df.index:
                        df.at[idx, col_en] = val_final
                        count += 1
                    elif str(idx) in df.index:
                        df.at[str(idx), col_en] = val_final
                        count += 1
                
                if count > 0:
                    log_general_change("Bulk Edit Modal", "Cell Edit (Bulk)", f"Editadas {count} filas en {col_en} a '{val_final}'")
                    
                    if col_en in st.session_state.autocomplete_options:
                        val_str = str(val_final)
                        current_opts = st.session_state.autocomplete_options[col_en]
                        if val_str not in current_opts:
                            current_opts.append(val_str)
                            st.session_state.autocomplete_options[col_en] = sorted(current_opts)

                    st.session_state.df_staging = apply_priority_rules(df)
                    
                    col_stat = "Row Status"
                    if col_stat in st.session_state.df_staging.columns:
                        chk_cols = [c for c in st.session_state.df_staging.columns if c not in [col_stat, 'Priority_Reason']]
                        chk = st.session_state.df_staging[chk_cols].fillna("").astype(str)
                        inc = (chk == "") | (chk == "0")
                        st.session_state.df_staging[col_stat] = np.where(inc.any(axis=1), get_text(lang, 'status_incomplete'), get_text(lang, 'status_complete'))

                    st.session_state.editor_state = None
                    st.session_state.current_data_hash = None
                    if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
                    st.success("¡Cambios aplicados!")
                    st.rerun()
                else:
                    st.warning("No se encontraron las filas seleccionadas.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Ingrese un valor.")

# --- 1. FILTROS ACTIVOS ---
def render_active_filters(lang: str):
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied'))
        return

    cols = st.columns(len(st.session_state.filtros_activos))
    for i, f in enumerate(st.session_state.filtros_activos):
        lbl = f"{translate_column(lang, f['columna'])}: {f['valor']} ✕"
        if cols[i].button(lbl, key=f"btn_del_filter_{i}"):
            st.session_state.filtros_activos.pop(i)
            st.rerun()
    
    if st.button(get_text(lang, 'clear_all_button')):
        st.session_state.filtros_activos = []
        st.rerun()

# --- 2. KPIS ---
def render_kpi_dashboard(lang: str, df: pd.DataFrame):
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    total_col = pd.to_numeric(df['Total'], errors='coerce').fillna(0)
    c1, c2, c3 = st.columns(3)
    c1.metric(get_text(lang, 'kpi_total_invoices'), len(df))
    c2.metric(get_text(lang, 'kpi_total_amount'), f"${total_col.sum():,.2f}")
    avg = total_col.mean() if not df.empty else 0
    c3.metric(get_text(lang, 'kpi_avg_amount'), f"${avg:,.2f}")

# --- 3. VISTA DETALLADA ---
def render_detailed_view(lang: str, df_filtered: pd.DataFrame, df_master: pd.DataFrame, col_map: dict, all_cols_en: list):
    
    cols_visibles = [c for c in st.session_state.columnas_visibles if c in df_filtered.columns]
    if not cols_visibles:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    priority_map = {"🚩 Maxima Prioridad": 4, "Maxima Prioridad": 4, "Alta": 3, "Media": 2, "Minima": 1}
    sort_opt = st.radio("Ordenar por:", ["Original", "🔼 Maxima a Minima", "🔽 Minima a Maxima"], horizontal=True, key="radio_sort_priority")
    st.markdown("---")

    df_view = df_filtered.copy()
    if sort_opt != "Original" and 'Priority' in df_view.columns:
        asc = (sort_opt == "🔽 Minima a Maxima")
        df_view['_sort_temp'] = df_view['Priority'].map(priority_map).fillna(0)
        sort_cols = ['_sort_temp']
        sort_ascs = [asc]
        if 'Invoice Date Age' in df_view.columns:
            sort_cols.append('Invoice Date Age')
            sort_ascs.append(False)
        df_view = df_view.sort_values(by=sort_cols, ascending=sort_ascs)
        df_view = df_view.drop(columns=['_sort_temp'])

    df_view = df_view[cols_visibles].copy()
    col_sel_name = "Seleccionar"
    if col_sel_name not in df_view.columns: df_view.insert(0, col_sel_name, False)
    
    df_display = df_view.copy()
    df_display.columns = [translate_column(lang, c) if c != col_sel_name else c for c in df_display.columns]
    
    if 'Priority' in df_filtered.columns:
        is_high = df_filtered.loc[df_display.index, 'Priority'].astype(str).str.contains("Maxima")
        new_idx = np.where(is_high, "🚩 " + df_display.index.astype(str), df_display.index.astype(str))
        df_display.index = new_idx

    col_config = {col_sel_name: st.column_config.CheckboxColumn("☑️", width="small")}
    for col_ui in df_display.columns:
        if col_ui == col_sel_name: continue
        col_en = col_map.get(col_ui, col_ui)
        if col_en in st.session_state.autocomplete_options:
            opts = sorted(st.session_state.autocomplete_options[col_en])
            col_config[col_ui] = st.column_config.SelectboxColumn(f"{col_ui} 🔽", options=opts, required=False)
        elif "Date" in col_en and "Age" not in col_en:
             col_config[col_ui] = st.column_config.TextColumn(f"{col_ui}", help="YYYY-MM-DD")

    state_hash = hash((json.dumps(st.session_state.filtros_activos, sort_keys=True), tuple(st.session_state.columnas_visibles), sort_opt, lang))
    if 'editor_key_ver' not in st.session_state: st.session_state.editor_key_ver = 0
    if 'editor_state' not in st.session_state or st.session_state.current_data_hash != state_hash:
        st.session_state.editor_state = df_display.copy()
        st.session_state.current_data_hash = state_hash
        st.session_state.editor_key_ver += 1
        st.rerun()

    def cb_add_row(do_log=True):
        idxs = pd.to_numeric(st.session_state.df_staging.index, errors='coerce').fillna(0)
        new_idx = int(idxs.max() + 1)
        row_data = {c: False if c == col_sel_name else "" for c in st.session_state.editor_state.columns}
        for c in st.session_state.editor_state.columns:
             if c != col_sel_name:
                 cen = col_map.get(c, c)
                 if cen in st.session_state.df_staging.columns and pd.api.types.is_numeric_dtype(st.session_state.df_staging[cen].dtype):
                     row_data[c] = 0

        new_df = pd.DataFrame([row_data], index=[str(new_idx)])
        st.session_state.editor_state = pd.concat([new_df, st.session_state.editor_state])
        st.session_state.editor_key_ver += 1
        if do_log: log_general_change("UI Button", "Row Added", f"Fila {new_idx} añadida.")

    def cb_select_all(val):
        if st.session_state.editor_state is not None:
            st.session_state.editor_state[col_sel_name] = val
            st.session_state.editor_key_ver += 1

    def cb_bulk_delete(idxs_raw):
        try:
            df_stg = st.session_state.df_staging
            idxs_str = [str(i) for i in idxs_raw]
            to_drop = [i for i in idxs_str if i in df_stg.index]
            if len(to_drop) < len(idxs_raw):
                idxs_int = [int(float(i)) for i in idxs_raw if str(i).replace('.','',1).isdigit()]
                to_drop_int = [i for i in idxs_int if i in df_stg.index]
                if len(to_drop_int) > len(to_drop): st.session_state.df_staging = df_stg.drop(to_drop_int, errors='ignore')
                else: st.session_state.df_staging = df_stg.drop(to_drop, errors='ignore')
            else:
                st.session_state.df_staging = df_stg.drop(to_drop, errors='ignore')

            log_general_change("Bulk Action", "Row Deleted", f"Eliminadas {len(idxs_raw)} filas.")
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.session_state.editor_key_ver += 1
            st.success("Filas eliminadas.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al eliminar: {e}")

    def cb_save_draft(do_log=True):
        try:
            edited = editor_val.copy()
            if col_sel_name in edited.columns: del edited[col_sel_name]
            edited.index = edited.index.astype(str).str.replace("🚩 ", "")
            edited.columns = [col_map.get(c, c) for c in edited.columns]
            
            if do_log: log_general_change("Save Button", "Draft Saved", "Se guardaron cambios en el borrador.")

            st.session_state.df_staging.index = st.session_state.df_staging.index.astype(str)
            st.session_state.df_staging.update(edited)
            new_rows_idx = edited.index.difference(st.session_state.df_staging.index)
            if not new_rows_idx.empty:
                st.session_state.df_staging = pd.concat([st.session_state.df_staging, edited.loc[new_rows_idx]])

            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.success("Borrador guardado.")
            st.rerun()
        except Exception as e:
            st.error(f"Error guardando: {e}")

    def cb_revert(do_log=True):
        st.session_state.df_staging = st.session_state.df_original.copy()
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.session_state.editor_key_ver += 1
        if do_log: log_general_change("Revert Button", "Revert", "Revertido a estable.")
        st.rerun()

    def cb_commit():
        st.session_state.df_original = st.session_state.df_staging.copy()
        log_general_change("Commit Button", "Commit", "Guardado punto estable.")
        st.success("Punto estable actualizado.")

    st.warning(get_text(lang, 'editor_manual_save_warning'))
    c_sel1, c_sel2, _ = st.columns([0.2, 0.2, 0.6])
    c_sel1.button("☑️ Marcar Todo", on_click=cb_select_all, args=(True,), use_container_width=True)
    c_sel2.button("⬜ Desmarcar", on_click=cb_select_all, args=(False,), use_container_width=True)

    with st.spinner("Cargando editor..."):
        editor_val = st.data_editor(
            st.session_state.editor_state,
            column_config=col_config,
            num_rows="dynamic",
            key=f"main_editor_{st.session_state.editor_key_ver}",
            height=600,
            use_container_width=True
        )

    filas_sel = []
    if col_sel_name in editor_val.columns:
        filas_sel = editor_val[editor_val[col_sel_name] == True].index.astype(str).str.replace("🚩 ", "").tolist()
    
    if filas_sel:
        st.info(f"✅ {len(filas_sel)} filas seleccionadas.")
        c_edit, c_del, c_find = st.columns([0.2, 0.2, 0.6])
        if c_edit.button(f"✏️ Editar {len(filas_sel)}"):
            modal_bulk_edit(filas_sel, col_map, lang)
        if c_del.button(f"🗑️ Borrar {len(filas_sel)}", type="primary"):
            cb_bulk_delete(filas_sel)
        st.markdown("---")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.button(get_text(lang, 'add_row_button'), on_click=cb_add_row, use_container_width=True)
    c2.button(get_text(lang, 'save_changes_button'), on_click=cb_save_draft, type="primary", use_container_width=True)
    c3.button(get_text(lang, 'commit_changes_button'), on_click=cb_commit, use_container_width=True)
    c4.button(get_text(lang, 'reset_changes_button'), on_click=cb_revert, use_container_width=True)
    if c5.button("🔍 Buscar/Reemplazar", use_container_width=True):
        modal_find_replace(col_map, lang)

    if hotkeys.pressed("save_draft", key="hk_main"): cb_save_draft(do_log=False)
    if hotkeys.pressed("add_row", key="hk_main"): cb_add_row(do_log=False)
    if hotkeys.pressed("revert_stable", key="hk_main"): cb_revert(do_log=False)

    st.markdown("---")
    st.download_button("Descargar Excel (Filtrado)", to_excel(editor_val), "filtro.xlsx")

def render_grouped_view(lang: str, df: pd.DataFrame, col_map: dict, all_cols: list):
    st.markdown(f"## {get_text(lang, 'group_by_header')}")
    opts = [translate_column(lang, c) for c in ["Vendor Name", "Status", "Pay Group", "Priority"] if c in all_cols]
    grp_col_ui = st.selectbox(get_text(lang, 'group_by_select'), opts)
    grp_col_en = col_map.get(grp_col_ui, grp_col_ui)
    
    if grp_col_en:
        try:
            df_grp = df.copy()
            for c in ['Total', 'Invoice Date Age']:
                if c in df_grp.columns: df_grp[c] = pd.to_numeric(df_grp[c], errors='coerce')
            aggs = {'Total': ['sum', 'count', 'mean']}
            if 'Invoice Date Age' in df_grp.columns: aggs['Invoice Date Age'] = ['mean']
            
            res = df_grp.groupby(grp_col_en).agg(aggs)
            res.columns = ['_'.join(col).strip() for col in res.columns.values]
            st.dataframe(res, use_container_width=True)
            st.download_button("Descargar Agrupado", to_excel(res), "agrupado.xlsx")
        except Exception as e:
            st.error(f"Error agrupando: {e}")