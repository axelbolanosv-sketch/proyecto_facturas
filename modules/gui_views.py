# modules/gui_views.py
"""
Módulo de Vistas Principales y Modales.

Este módulo contiene la lógica de renderizado de:
1. Diálogos Modales (Buscar/Reemplazar, Edición Masiva).
2. Dashboard de KPIs.
3. Editor de Datos Principal (Fragmento optimizado).
4. Vistas Detallada y Agrupada.
"""

import streamlit as st
import pandas as pd
import json
import numpy as np
from modules.translator import get_text, translate_column
from modules.utils import to_excel, recalculate_row_status
from modules.rules_service import apply_priority_rules
from modules.audit_service import log_general_change
import streamlit_hotkeys as hotkeys

# Límite para desactivar tooltips y mejorar rendimiento en tablas grandes
MAX_ROWS_FOR_TOOLTIPS = 1500 

# --- MODAL BUSCAR Y REEMPLAZAR ---
@st.dialog("🔍 Buscar y Reemplazar")
def modal_find_replace(col_map, lang):
    """Renderiza el diálogo modal para buscar y reemplazar valores en una columna.

    Args:
        col_map (dict): Mapeo de nombres de columnas (UI -> Real).
        lang (str): Idioma actual.
    """
    st.markdown("Esta herramienta buscará y reemplazará valores en la **Columna Objetivo**.")
    
    # Preparar lista de columnas
    cols_raw = [c for c in col_map.keys() if "Seleccionar" not in c]
    cols_vis = []
    auto_opts = st.session_state.autocomplete_options
    
    for c in cols_raw:
        cen = col_map.get(c, c)
        # Añadir icono si tiene autocompletado
        cols_vis.append(f"{c} 📋" if cen in auto_opts and auto_opts[cen] else c)
        
    col_sel_vis = st.selectbox("Columna Objetivo:", cols_vis)
    col_sel_ui = col_sel_vis.replace(" 📋", "")
    col_en = col_map.get(col_sel_ui, col_sel_ui)
    
    st.markdown("---")
    opts = auto_opts.get(col_en, [])

    # Controles de Búsqueda y Reemplazo (Dual: Manual o Selectbox)
    c1, c2 = st.columns(2)
    with c1:
        find_txt = ""
        if opts:
            use_manual_find = st.checkbox("✍️ Manual (Buscar)", key="chk_mf")
            find_txt = st.text_input("Buscar:") if use_manual_find else st.selectbox("Buscar:", [""] + sorted(opts), key="sel_find")
        else:
            find_txt = st.text_input("Buscar:")

    with c2:
        replace_val = ""
        if opts:
            use_manual_rep = st.checkbox("✍️ Manual (Reemplazar)", key="chk_mr")
            replace_val = st.text_input("Reemplazar:") if use_manual_rep else st.selectbox("Reemplazar:", [""] + sorted(opts), key="sel_rep")
        else:
            replace_val = st.text_input("Reemplazar:")

    # Filtros adicionales opcionales
    active_filters = {}
    with st.expander("🎯 Filtros Adicionales", expanded=False):
        filter_opts = [c for c in cols_vis if c != col_sel_vis]
        sel_filters = st.multiselect("Condiciones:", filter_opts)
        for f_vis in sel_filters:
            f_ui = f_vis.replace(" 📋", "")
            f_en = col_map.get(f_ui, f_ui)
            f_opts = auto_opts.get(f_en, [])
            if f_opts:
                val = st.selectbox(f"'{f_ui}' ==", f_opts, key=f"f_{f_en}")
                if val: active_filters[f_en] = {"val": val, "type": "exact"}
            else:
                val = st.text_input(f"'{f_ui}' contiene:", key=f"f_{f_en}")
                if val: active_filters[f_en] = {"val": val, "type": "contains"}

    st.markdown("---")
    mode = st.radio("Modo:", ["Coincidencia Exacta", "Contiene"], horizontal=True)
    
    # Acción de Reemplazo
    if st.button("🚀 Reemplazar", type="primary", use_container_width=True):
        if not find_txt:
            st.error("Ingrese valor a buscar.")
        else:
            df = st.session_state.df_staging.copy()
            if col_en in df.columns:
                # 1. Crear Máscara Principal (Búsqueda)
                if mode == "Coincidencia Exacta":
                    mask_main = (df[col_en].astype(str) == str(find_txt)) 
                else:
                    mask_main = (df[col_en].astype(str).str.contains(str(find_txt), case=False, na=False))
                
                # 2. Aplicar Filtros Adicionales (AND)
                mask_filters = pd.Series(True, index=df.index)
                for f_col, f_data in active_filters.items():
                    if f_col in df.columns:
                        if f_data["type"] == "exact": 
                            mask_filters &= (df[f_col].astype(str) == str(f_data["val"]))
                        else: 
                            mask_filters &= (df[f_col].astype(str).str.contains(str(f_data["val"]), case=False, na=False))

                final_mask = mask_main & mask_filters
                count = final_mask.sum()
                
                if count > 0:
                    # 3. Ejecutar Reemplazo
                    final_val = replace_val
                    # Intentar mantener tipo numérico si aplica
                    if pd.api.types.is_numeric_dtype(df[col_en].dtype):
                        try: final_val = pd.to_numeric(replace_val)
                        except: pass
                    
                    df.loc[final_mask, col_en] = final_val
                    
                    # 4. Actualizar Autocompletado (Aprender nuevo valor)
                    if col_en in st.session_state.autocomplete_options:
                        v_str = str(final_val)
                        c_opts = st.session_state.autocomplete_options[col_en]
                        if v_str not in c_opts:
                            c_opts.append(v_str)
                            st.session_state.autocomplete_options[col_en] = sorted(c_opts)

                    # 5. Auditoría y Recálculo
                    log_general_change("Find/Replace", "Bulk Replace", f"Editadas {count} filas en '{col_en}'")
                    
                    df = apply_priority_rules(df)
                    df = recalculate_row_status(df, lang) # Recalcular estado tras edición
                    st.session_state.df_staging = df
                    
                    # Limpiar estado del editor para forzar refresco
                    st.session_state.editor_state = None
                    st.session_state.current_data_hash = None
                    if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
                    
                    st.success(f"✅ {count} cambios.")
                    st.rerun()
                else:
                    st.warning("Sin coincidencias.")
            else:
                st.error("Error columna.")

# --- MODAL EDICIÓN MASIVA ---
@st.dialog("✏️ Edición Masiva")
def modal_bulk_edit(indices, col_map, lang):
    """Renderiza el diálogo modal para editar múltiples filas seleccionadas a la vez.

    Args:
        indices (list): Lista de índices (IDs de fila) seleccionados.
        col_map (dict): Mapeo de columnas UI -> Real.
        lang (str): Idioma.
    """
    st.markdown(f"Editando **{len(indices)}** filas.")
    cols_vis = []
    auto = st.session_state.autocomplete_options
    
    # Preparar lista de columnas editables
    for c in col_map.keys():
        if "Seleccionar" not in c and "ID" not in c:
            cen = col_map[c]
            cols_vis.append(f"{c} 📋" if cen in auto and auto[cen] else c)

    c_sel_vis = st.selectbox("Columna:", cols_vis)
    c_ui = c_sel_vis.replace(" 📋", "")
    c_en = col_map.get(c_ui, c_ui)
    
    # Control de valor (Dropdown o Texto)
    opts = auto.get(c_en, [])
    val = None
    if opts:
        man = st.checkbox("✍️ Manual", key="bm")
        val = st.text_input("Valor:") if man else st.selectbox("Valor:", opts, index=None)
    else:
        val = st.text_input("Valor:")

    if st.button("Aplicar", type="primary"):
        if val is not None:
            try:
                df = st.session_state.df_staging.copy()
                final = val
                # Manejo de tipos numéricos
                if c_en in df.columns and pd.api.types.is_numeric_dtype(df[c_en].dtype):
                    try: final = pd.to_numeric(val)
                    except: pass
                
                # Aplicación de cambios fila por fila (seguro)
                cnt = 0
                for i in indices:
                    if i in df.index: 
                        df.at[i, c_en] = final; cnt+=1
                    elif str(i) in df.index: 
                        df.at[str(i), c_en] = final; cnt+=1
                
                if cnt > 0:
                    # Actualizar autocompletado
                    if c_en in st.session_state.autocomplete_options:
                        v_str = str(final)
                        curr = st.session_state.autocomplete_options[c_en]
                        if v_str not in curr:
                            curr.append(v_str)
                            st.session_state.autocomplete_options[c_en] = sorted(curr)

                    # Auditoría y Recálculo
                    log_general_change("Bulk", "Edit", f"{cnt} filas en {c_en}")
                    
                    df = apply_priority_rules(df)
                    df = recalculate_row_status(df, lang)
                    st.session_state.df_staging = df
                    
                    # Refresco de UI
                    st.session_state.editor_state = None
                    st.session_state.current_data_hash = None
                    if 'editor_key_ver' in st.session_state: st.session_state.editor_key_ver += 1
                    st.success("Hecho.")
                    st.rerun()
            except Exception as e: st.error(e)
        else: st.error("Ingrese valor.")

# --- VISTAS AUXILIARES ---
def render_active_filters(lang):
    """Muestra los chips de filtros activos en la parte superior y permite cerrarlos."""
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied')); return
        
    # Grid de filtros
    cols = st.columns(len(st.session_state.filtros_activos))
    for i, f in enumerate(st.session_state.filtros_activos):
        # Botón para quitar filtro individual
        if cols[i].button(f"{translate_column(lang, f['columna'])}: {f['valor']} ✕", key=f"rem_{i}"):
            st.session_state.filtros_activos.pop(i); st.rerun()
            
    # Botón para limpiar todo
    if st.button(get_text(lang, 'clear_all_button')):
        st.session_state.filtros_activos = []; st.rerun()

def render_kpi_dashboard(lang, df):
    """Calcula y muestra métricas clave (Total Facturas, Monto Total, Promedio)."""
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    
    # Cálculo robusto del total
    tot = pd.to_numeric(df['Total'], errors='coerce').fillna(0).sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric(get_text(lang, 'kpi_total_invoices'), len(df))
    c2.metric(get_text(lang, 'kpi_total_amount'), f"${tot:,.2f}")
    # Evitar división por cero
    c3.metric(get_text(lang, 'kpi_avg_amount'), f"${(tot/len(df) if len(df) else 0):,.2f}")

# --- FRAGMENTO OPTIMIZADO (Lógica del Editor Principal) ---
@st.fragment
def render_editor_fragment(df_disp, col_map, lang, cc, h_data, original_staging_df):
    """
    Renderiza la tabla editable principal. Utiliza @st.fragment para aislar 
    su re-renderizado del resto de la aplicación.

    Maneja: Edición de celdas, Selección de filas, Tooltips, Botones CRUD (Add/Del/Save).
    """
    
    if 'editor_key_ver' not in st.session_state: st.session_state.editor_key_ver = 0
    
    # Control de caché manual: Si el hash de datos cambia, reseteamos el editor state
    if 'editor_state' not in st.session_state or st.session_state.current_data_hash != h_data:
        st.session_state.editor_state = df_disp.copy()
        st.session_state.current_data_hash = h_data
        st.session_state.editor_key_ver += 1
        st.session_state.pending_selection = None 
        st.rerun()

    # Lógica para "Seleccionar Todos / Ninguno"
    if st.session_state.get("pending_selection") is not None:
        val = st.session_state.pop("pending_selection")
        df_disp["Seleccionar"] = val
        st.session_state.editor_state = df_disp.copy()

    # Preparación de Tooltips (solo si < MAX_ROWS para performance)
    styled_data = df_disp 
    use_tooltips = len(df_disp) <= MAX_ROWS_FOR_TOOLTIPS
    
    if use_tooltips:
        try:
            tt_df = pd.DataFrame("", index=df_disp.index, columns=df_disp.columns)
            col_prio_ui = translate_column(lang, "Priority")
            if col_prio_ui in df_disp.columns:
                # Limpiar banderas visuales para buscar en el dataframe maestro
                clean_idxs = df_disp.index.astype(str).str.replace("🚩 ", "")
                master = original_staging_df
                if not master.empty:
                    target_idxs = clean_idxs
                    # Ajuste de tipo de índice (numérico vs string)
                    if pd.api.types.is_numeric_dtype(master.index):
                        target_idxs = pd.to_numeric(clean_idxs, errors='coerce')
                    # Obtener razones de prioridad
                    reasons = master.reindex(target_idxs)['Priority_Reason'].fillna("Sin información")
                    tt_df[col_prio_ui] = reasons.values
            styled_data = df_disp.style.set_tooltips(tt_df)
        except:
            # Fallback seguro si falla el estilado
            styled_data = df_disp
    else:
        st.caption(get_text(lang, 'perf_mode_tooltips_off').format(n=MAX_ROWS_FOR_TOOLTIPS))

    # Botones de selección masiva
    c_sel_all, c_desel_all, _ = st.columns([0.15, 0.15, 0.7])
    
    if c_sel_all.button(get_text(lang, 'select_all_btn'), help="Select All"):
        st.session_state.pending_selection = True
        st.session_state.editor_key_ver += 1
        st.rerun()
        
    if c_desel_all.button(get_text(lang, 'deselect_all_btn'), help="Select None"):
        st.session_state.pending_selection = False
        st.session_state.editor_key_ver += 1
        st.rerun()

    # --- DATA EDITOR PRINCIPAL ---
    edited = st.data_editor(
        styled_data, 
        column_config=cc,
        num_rows="dynamic",
        key=f"ed_{st.session_state.editor_key_ver}",
        height=600,
        use_container_width=True
    )

    # --- Callbacks de Acciones CRUD ---
    def cb_add():
        """Añade una fila vacía al final."""
        idx = int(pd.to_numeric(st.session_state.df_staging.index, errors='coerce').max() + 1)
        row = {c: False if c=="Seleccionar" else "" for c in st.session_state.editor_state.columns}
        st.session_state.editor_state = pd.concat([pd.DataFrame([row], index=[str(idx)]), st.session_state.editor_state])
        st.session_state.editor_key_ver += 1
        log_general_change("UI", "Add Row", f"Fila {idx}")
        st.rerun()

    def cb_del(idxs):
        """Borra las filas seleccionadas."""
        df = st.session_state.df_staging
        drop = [str(i) for i in idxs if str(i) in df.index.astype(str)]
        st.session_state.df_staging = df.drop(drop, errors='ignore')
        log_general_change("UI", "Del Row", f"{len(drop)} filas")
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.success("Borrado."); st.rerun()

    def cb_save():
        """Guarda cambios del borrador al Staging, aplica reglas y recalcula estados."""
        try:
            ed = edited.copy()
            if "Seleccionar" in ed: del ed["Seleccionar"]
            
            # Limpiar índices visuales
            ed.index = ed.index.astype(str).str.replace("🚩 ", "")
            # Restaurar nombres de columnas al inglés (Real)
            ed.columns = [col_map.get(c,c) for c in ed.columns]
            
            st.session_state.df_staging.index = st.session_state.df_staging.index.astype(str)
            st.session_state.df_staging.update(ed)
            
            # Detectar filas nuevas añadidas en el editor
            new = ed.index.difference(st.session_state.df_staging.index)
            if not new.empty: 
                st.session_state.df_staging = pd.concat([st.session_state.df_staging, ed.loc[new]])
            
            # --- ACTUALIZACIÓN CRÍTICA ---
            st.session_state.df_staging = apply_priority_rules(st.session_state.df_staging)
            st.session_state.df_staging = recalculate_row_status(st.session_state.df_staging, lang)
            
            log_general_change("UI", "Save", "Borrador guardado")
            st.session_state.editor_state = None; st.session_state.current_data_hash = None
            st.success("Guardado."); st.rerun()
        except Exception as e: st.error(e)

    def cb_rev():
        """Revierte cambios al último estado estable (Original/Commit)."""
        st.session_state.df_staging = st.session_state.df_original.copy()
        st.session_state.editor_state = None; st.session_state.current_data_hash = None
        log_general_change("UI", "Revert", "Revertido")
        st.rerun()

    def cb_com():
        """Hace commit del estado actual como el nuevo punto de restauración."""
        st.session_state.df_original = st.session_state.df_staging.copy()
        log_general_change("UI", "Commit", "Estable guardado")
        st.success("Hecho.")

    # Detección de filas seleccionadas
    sel_idxs = []
    if "Seleccionar" in edited.columns:
        # Extraer índices reales limpiando banderas visuales
        sel_idxs = pd.to_numeric(edited[edited["Seleccionar"]].index.astype(str).str.replace("🚩 ", ""), errors='coerce').dropna().unique()

    # Barra de acciones para selección
    if len(sel_idxs) > 0:
        st.info(f"✅ {len(sel_idxs)} seleccionados.")
        c1, c2, _ = st.columns([0.2,0.2,0.6])
        if c1.button("✏️ Editar"): modal_bulk_edit(sel_idxs, col_map, lang)
        if c2.button("🗑️ Borrar", type="primary"): cb_del(sel_idxs)
        st.markdown("---")

    # Botonera Inferior Principal
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.button(get_text(lang, 'add_row_button'), on_click=cb_add)
    c2.button(get_text(lang, 'save_changes_button'), on_click=cb_save, type="primary")
    c3.button(get_text(lang, 'commit_changes_button'), on_click=cb_com)
    c4.button(get_text(lang, 'reset_changes_button'), on_click=cb_rev)
    if c5.button("🔍 Buscar/Reemplazar"): modal_find_replace(col_map, lang)

    # Atajos de Teclado (Hotkeys)
    if hotkeys.pressed("save_draft"): cb_save()
    if hotkeys.pressed("commit_changes"): cb_com()
    if hotkeys.pressed("add_row"): cb_add()
    if hotkeys.pressed("revert_stable"): cb_rev()

    st.markdown("---")
    # Descarga de lo que se ve en pantalla
    st.download_button(get_text(lang, 'download_excel_simple'), to_excel(edited), "filtro.xlsx")


def render_detailed_view(lang, df_filtered, df_master, col_map, all_cols):
    """Prepara los datos y configuraciones para la Vista Detallada."""
    cols_show = [c for c in st.session_state.columnas_visibles if c in df_filtered.columns]
    if not cols_show: st.warning(get_text(lang, 'warning_select_cols')); return 

    # Mapeo para ordenamiento
    prio_map = {"🚩 Maxima Prioridad": 4, "Maxima Prioridad": 4, "Alta": 3, "Media": 2, "Minima": 1}
    
    # Opciones de ordenamiento
    opts = [get_text(lang, 'sort_opt_original'), get_text(lang, 'sort_opt_max_min'), get_text(lang, 'sort_opt_min_max')]
    sort_opt = st.radio(get_text(lang, 'sort_label'), opts, horizontal=True)
    st.markdown("---")

    # Aplicar ordenamiento
    df_v = df_filtered.copy()
    if sort_opt != get_text(lang, 'sort_opt_original') and 'Priority' in df_v.columns:
        asc = (sort_opt == get_text(lang, 'sort_opt_min_max'))
        df_v['_s'] = df_v['Priority'].map(prio_map).fillna(0)
        scols = ['_s']
        sascs = [asc]
        if 'Invoice Date Age' in df_v.columns: scols.append('Invoice Date Age'); sascs.append(False)
        df_v = df_v.sort_values(by=scols, ascending=sascs).drop(columns=['_s'])

    # Preparar columnas visibles
    df_v = df_v[cols_show].copy()
    if "Seleccionar" not in df_v.columns: df_v.insert(0, "Seleccionar", False)
    
    # Traducir columnas para visualización
    df_disp = df_v.copy()
    df_disp.columns = [translate_column(lang, c) if c != "Seleccionar" else c for c in df_disp.columns]
    
    # Marcar visualmente filas de alta prioridad en el índice
    if 'Priority' in df_filtered.columns:
        hi = df_filtered.loc[df_disp.index, 'Priority'].astype(str).str.contains("Maxima")
        df_disp.index = np.where(hi, "🚩 " + df_disp.index.astype(str), df_disp.index.astype(str))

    # Configuración de tipos de columna (Column Config)
    cc = {"Seleccionar": st.column_config.CheckboxColumn("☑️", width="small")}
    for cui in df_disp.columns:
        if cui == "Seleccionar": continue
        cen = col_map.get(cui, cui)
        # Si tiene autocompletado, usar Selectbox
        if cen in st.session_state.autocomplete_options:
            cc[cui] = st.column_config.SelectboxColumn(f"{cui} 🔽", options=sorted(st.session_state.autocomplete_options[cen]))
        # Si parece fecha, forzar texto para evitar conversiones erróneas
        elif "Date" in cen and "Age" not in cen:
            cc[cui] = st.column_config.TextColumn(f"{cui}", help="YYYY-MM-DD")

    # Generar hash único para estado del editor
    h_data = hash((json.dumps(st.session_state.filtros_activos, default=str), tuple(st.session_state.columnas_visibles), sort_opt))

    # Renderizar fragmento
    render_editor_fragment(df_disp, col_map, lang, cc, h_data, st.session_state.df_staging)


def render_grouped_view(lang, df, col_map, all_cols):
    """Renderiza la tabla pivotada/agrupada de resumen."""
    st.markdown(f"## {get_text(lang, 'group_by_header')}")
    
    # Opciones de agrupación
    opts = [translate_column(lang, c) for c in ["Vendor Name", "Status", "Pay Group", "Priority"] if c in all_cols]
    gui = st.selectbox(get_text(lang, 'group_by_select'), opts)
    gen = col_map.get(gui, gui)
    
    if gen:
        d = df.copy()
        # Asegurar tipos numéricos para agregación
        for c in ['Total', 'Invoice Date Age']: 
            if c in d: d[c] = pd.to_numeric(d[c], errors='coerce')
            
        agg = {'Total': ['sum','count','mean']}
        if 'Invoice Date Age' in d: agg['Invoice Date Age'] = ['mean']
        
        # Crear agrupación
        res = d.groupby(gen).agg(agg)
        res.columns = ['_'.join(c).strip() for c in res.columns]
        
        st.dataframe(res, use_container_width=True)
        st.download_button(get_text(lang, 'download_button_short'), to_excel(res), "agrupado.xlsx")