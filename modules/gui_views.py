# modules/gui_views.py
# VERSIÓN 5.1: FIX CRÍTICO ARROW INVALID (INDICES MIXTOS), Fix Añadir Fila, Bulk Delete.

import streamlit as st
import pandas as pd
import json
import numpy as np
import warnings
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel
# Importar el motor de reglas
from modules.rules_service import apply_priority_rules

import streamlit_hotkeys as hotkeys

# --- 0. COMPONENTE MODAL DE EDICIÓN MASIVA ---
@st.dialog("✏️ Edición Masiva / Bulk Edit")
def modal_bulk_edit(indices_seleccionados: list, col_map_ui_to_en: dict, lang: str):
    """
    Muestra un diálogo modal para editar una columna específica en múltiples filas a la vez.

    Args:
        indices_seleccionados (list): Lista de índices de las filas que se van a editar.
        col_map_ui_to_en (dict): Diccionario de mapeo de nombres de columnas (UI -> Inglés).
        lang (str): Código del idioma actual ('es' o 'en').
    """
    st.markdown(f"Se editarán **{len(indices_seleccionados)}** facturas seleccionadas.")

    # Filtrar columnas no editables (Checkbox y ID interno)
    cols_disponibles = [
        col for col in col_map_ui_to_en.keys()
        if "Seleccionar" not in col and "ID" not in col
    ]
    col_ui_seleccionada = st.selectbox("¿Qué columna desea editar?", cols_disponibles)
    col_en_seleccionada = col_map_ui_to_en.get(col_ui_seleccionada, col_ui_seleccionada)

    # Obtener opciones de autocompletado si existen
    opciones_existentes = st.session_state.autocomplete_options.get(col_en_seleccionada, [])
    nuevo_valor = None

    if opciones_existentes and len(opciones_existentes) > 0:
        nuevo_valor = st.selectbox(
            f"Seleccione el nuevo valor para '{col_ui_seleccionada}':",
            options=opciones_existentes,
            index=None,
            placeholder="Seleccione un valor...",
            help="Puede seleccionar un valor existente de la lista."
        )
    else:
        nuevo_valor = st.text_input(f"Escriba el nuevo valor para '{col_ui_seleccionada}':")

    st.warning("⚠️ Esta acción no se puede deshacer fácilmente (tendrá que usar 'Revertir a Estable').")

    if st.button("Aplicar Cambios", type="primary"):
        if nuevo_valor is not None:
            try:
                # Copiar el DataFrame actual
                df_master = st.session_state.df_staging.copy()
                
                # [FIX CRÍTICO TIPOS]
                # Determinar tipo de dato destino para evitar mezclar String/Int en columnas numéricas
                val_to_set = nuevo_valor
                if col_en_seleccionada in df_master.columns:
                    col_dtype = df_master[col_en_seleccionada].dtype
                    if pd.api.types.is_numeric_dtype(col_dtype):
                        try:
                            val_to_set = pd.to_numeric(nuevo_valor)
                        except ValueError:
                            st.warning(f"Advertencia: Intentando guardar texto en columna numérica '{col_ui_seleccionada}'.")

                # Aplicar el cambio a todas las filas seleccionadas
                for idx in indices_seleccionados:
                    if idx in df_master.index:
                        df_master.at[idx, col_en_seleccionada] = val_to_set

                # Recalcular reglas de negocio (Prioridad) automáticamente
                df_master = apply_priority_rules(df_master)

                # Recalcular estado de la fila (Row Status)
                col_status_en = "Row Status"
                if col_status_en in df_master.columns:
                    cols_to_check = [
                        col for col in df_master.columns
                        if col != col_status_en and col != 'Priority_Reason'
                    ]
                    # Verificar si hay celdas vacías relevantes
                    df_check = df_master[cols_to_check].fillna("").astype(str)
                    blank_mask = (df_check == "") | (df_check == "0")
                    incomplete_rows = blank_mask.any(axis=1)

                    df_master[col_status_en] = np.where(
                        incomplete_rows,
                        get_text(lang, 'status_incomplete'),
                        get_text(lang, 'status_complete')
                    )

                # Guardar cambios en el estado y forzar recarga completa
                st.session_state.df_staging = df_master.copy()
                st.session_state.editor_state = None  # Limpiar estado del editor
                st.session_state.current_data_hash = None
                
                # Incrementar versión de clave para forzar repintado del editor
                if 'editor_key_ver' in st.session_state:
                    st.session_state.editor_key_ver += 1
                    
                st.success("¡Cambios aplicados con éxito!")
                st.rerun()

            except Exception as e:
                st.error(f"Error al aplicar cambios: {e}")
        else:
            st.error("Por favor ingrese o seleccione un valor.")


# --- 1. RENDER FILTROS ACTIVOS ---
def render_active_filters(lang: str):
    """
    Renderiza la sección de filtros activos con botones para eliminarlos individualmente.
    """
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    if not st.session_state.filtros_activos:
        st.info(get_text(lang, 'no_filters_applied'))
        return

    filtros_a_eliminar = -1
    num_filtros = len(st.session_state.filtros_activos)
    num_columnas = max(1, min(num_filtros, 5))
    cols_filtros = st.columns(num_columnas)

    for i, filtro in enumerate(st.session_state.filtros_activos):
        col_index = i % num_columnas
        with cols_filtros[col_index]:
            col_ui = translate_column(lang, filtro['columna'])
            label_boton = f"{col_ui}: {filtro['valor']}  ✕"
            if st.button(label_boton, key=f"quitar_{i}", help=f"Quitar filtro {i+1}", type="primary"):
                filtros_a_eliminar = i

    if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
        st.session_state.filtros_activos = []
        st.rerun()

    if filtros_a_eliminar > -1:
        st.session_state.filtros_activos.pop(filtros_a_eliminar)
        st.rerun()


# --- 2. RENDER KPIS ---
def render_kpi_dashboard(lang: str, resultado_df: pd.DataFrame):
    """
    Calcula y muestra los KPIs (Indicadores Clave de Desempeño) basados en los datos filtrados.
    """
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    try:
        # Convertir a numérico forzando errores a NaN y eliminándolos
        totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
    except KeyError:
        totales_numericos = pd.Series(dtype='float64')
        st.warning("No se encontró la columna 'Total' para los KPIs.")

    col1, col2, col3 = st.columns(3)
    
    col1.metric(label=get_text(lang, 'kpi_total_invoices'), value=len(resultado_df))
    
    col2.metric(
        label=get_text(lang, 'kpi_total_amount'),
        value=f"${totales_numericos.sum():,.2f}",
        help=get_text(lang, 'kpi_total_amount_help')
    )
    
    avg_value = totales_numericos.mean() if not totales_numericos.empty else 0.00
    col3.metric(
        label=get_text(lang, 'kpi_avg_amount'),
        value=f"${avg_value:,.2f}",
        help=get_text(lang, 'kpi_avg_amount_help')
    )


# --- 3. RENDER VISTA DETALLADA ---
def render_detailed_view(
    lang: str,
    resultado_df_filtrado: pd.DataFrame,
    df_master_copy: pd.DataFrame,
    col_map_ui_to_en: dict,
    todas_las_columnas_en: list
):
    """
    Renderiza la vista principal de edición de datos (Data Editor).
    """

    # --- 3.1. Validación de Columnas ---
    if not st.session_state.columnas_visibles:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return
    
    columnas_a_mostrar_en = st.session_state.columnas_visibles
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df_filtrado.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    # --- 3.2. Preparación del DataFrame para Visualización ---
    df_vista_detallada = resultado_df_filtrado[columnas_finales].copy()

    # Insertar columna de selección (Checkbox) al inicio
    col_sel_name = "Seleccionar"
    if col_sel_name not in df_vista_detallada.columns:
        df_vista_detallada.insert(0, col_sel_name, False)

    # Renombrar columnas para la UI
    df_display = df_vista_detallada.copy()
    df_display.columns = [
        translate_column(lang, col) if col != col_sel_name else col
        for col in df_display.columns
    ]

    # Marcar visualmente filas de Alta Prioridad en el índice
    if 'Priority' in resultado_df_filtrado.columns:
        try:
            is_max_priority = (resultado_df_filtrado['Priority'] == "Maxima Prioridad") | \
                              (resultado_df_filtrado['Priority'] == "🚩 Maxima Prioridad")
            new_index = np.where(
                is_max_priority,
                "🚩 " + df_display.index.astype(str),
                df_display.index.astype(str)
            )
            df_display.index = new_index
        except Exception as e:
            st.warning(f"No se pudo aplicar el indicador de prioridad: {e}")

    # --- 3.3. Configuración de Columnas (st.column_config) ---
    configuracion_columnas = {}
    date_format_help_text = get_text(lang, 'date_format_help')
    cached_options = st.session_state.get('autocomplete_options', {})

    # Configurar columna de Checkbox
    configuracion_columnas[col_sel_name] = st.column_config.CheckboxColumn(
        "☑️", help="Seleccione para edición masiva", default=False, width="small"
    )

    # Configurar columna de Razón de Prioridad (Solo lectura + Tooltip)
    col_razon_ui = translate_column(lang, "Priority_Reason")
    if col_razon_ui in df_display.columns:
        configuracion_columnas[col_razon_ui] = st.column_config.TextColumn(
            f"{col_razon_ui} 💡",
            help="Explica por qué una factura tiene su prioridad. (Solo lectura)",
            disabled=True
        )

    # Configurar resto de columnas
    for col_ui in df_display.columns:
        if col_ui == col_sel_name: continue
        if col_ui == col_razon_ui: continue

        col_en = col_map_ui_to_en.get(col_ui, col_ui)

        # Autocompletado (Selectbox)
        if col_en in cached_options and cached_options[col_en]:
            opciones_actuales = list(cached_options[col_en])

            if col_en == "Priority":
                estandares = [
                    "🚩 Maxima Prioridad", "Maxima Prioridad",
                    "Minima", "Media", "Alta",
                    "Baja Prioridad", "Low", "Medium", "High", "Zero"
                ]
                for std in estandares:
                    if std not in opciones_actuales:
                        opciones_actuales.append(std)

            configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                f"{col_ui} (Autocompletar)",
                help=get_text(lang, 'autocomplete_help'),
                options=sorted(opciones_actuales),
                required=False
            )
        # Formato de Texto para Fechas
        elif 'Date' in col_en and 'Age' not in col_en:
            configuracion_columnas[col_ui] = st.column_config.TextColumn(
                f"{col_ui}", help=date_format_help_text, required=False
            )

    # --- 3.4. Gestión del Estado del Editor (Caching) ---
    filtros_json_string = json.dumps(st.session_state.filtros_activos, sort_keys=True)
    columnas_tuple = tuple(st.session_state.columnas_visibles)
    priority_sort_state = st.session_state.get('priority_sort_order', None)
    
    current_data_hash = hash((filtros_json_string, columnas_tuple, priority_sort_state))
    current_lang_hash = hash(st.session_state.language)

    if 'editor_key_ver' not in st.session_state:
        st.session_state.editor_key_ver = 0

    # Si los datos base han cambiado, actualizar el estado del editor
    if ('editor_state' not in st.session_state or 
        st.session_state.current_data_hash != current_data_hash or 
        st.session_state.current_lang_hash != current_lang_hash):
        
        st.session_state.editor_state = df_display.copy()
        st.session_state.current_data_hash = current_data_hash
        st.session_state.current_lang_hash = current_lang_hash
        st.session_state.editor_key_ver += 1
        st.rerun()
        st.stop()

    # --- 3.5. Funciones Callback (Lógica de Botones) ---

    def callback_add_row():
        """
        Añade una nueva fila vacía al principio del editor.
        """
        df_editado = st.session_state.editor_state
        max_index = 0
        
        if not df_master_copy.empty:
             try:
                 idx_numeric = pd.to_numeric(df_master_copy.index, errors='coerce').fillna(0)
                 max_index = idx_numeric.max()
             except:
                 max_index = len(df_master_copy)

        if not df_editado.empty:
            indices_limpios = pd.Series(df_editado.index).astype(str).str.replace("🚩 ", "").str.strip()
            indices_numericos = pd.to_numeric(indices_limpios, errors='coerce').dropna()
            if not indices_numericos.empty:
                max_index = max(max_index, indices_numericos.max())
        
        new_index = int(max_index + 1)
        
        # Crear diccionario con valores por defecto
        default_values = {}
        for col in df_editado.columns:
            if col == col_sel_name:
                default_values[col] = False
                continue
            
            col_en = col_map_ui_to_en.get(col, col)
            col_original_dtype = 'object'
            
            if col_en in df_master_copy.columns:
                col_original_dtype = df_master_copy[col_en].dtype
            
            if pd.api.types.is_numeric_dtype(col_original_dtype):
                default_values[col] = 0
            else:
                default_values[col] = ""
        
        # [FIX CRÍTICO]: Forzar que el índice sea String para coincidir con el resto de la tabla
        new_row_df = pd.DataFrame([default_values], index=[str(new_index)])
        
        st.session_state.editor_state = pd.concat([new_row_df, df_editado], ignore_index=False)
        st.session_state.editor_key_ver += 1

    def _callback_toggle_selection(select_all: bool):
        if st.session_state.editor_state is not None and col_sel_name in st.session_state.editor_state.columns:
            st.session_state.editor_state[col_sel_name] = select_all
            st.session_state.editor_key_ver += 1
            st.rerun()

    def _callback_bulk_delete(indices_to_delete: list):
        if st.session_state.df_staging is not None:
            try:
                st.session_state.df_staging = st.session_state.df_staging.drop(indices_to_delete, errors='ignore')
                
                if st.session_state.editor_state is not None:
                    temp_df = st.session_state.editor_state.copy()
                    temp_df['temp_idx'] = pd.to_numeric(
                        temp_df.index.astype(str).str.replace("🚩 ", ""), errors='coerce'
                    )
                    mask_keep = ~temp_df['temp_idx'].isin(indices_to_delete)
                    st.session_state.editor_state = st.session_state.editor_state[mask_keep]
                    
                st.session_state.editor_key_ver += 1
                st.success(f"🗑️ {len(indices_to_delete)} filas eliminadas.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al eliminar filas: {e}")

    def _callback_guardar_borrador():
        try:
            df_edited_view_ui = editor_return_value.copy()
            
            if col_sel_name in df_edited_view_ui.columns:
                df_edited_view_ui = df_edited_view_ui.drop(columns=[col_sel_name])

            df_edited_view_ui.index = pd.to_numeric(
                df_edited_view_ui.index.astype(str).str.replace("🚩 ", "")
            )
            
            df_to_merge_en = df_edited_view_ui.copy()
            df_to_merge_en.columns = [
                col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns
            ]

            current_lang = st.session_state.language
            dayfirst = (current_lang == 'es')
            target_format = get_text(current_lang, 'date_format_es' if current_lang == 'es' else 'date_format_en')
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                for col_en in df_to_merge_en.columns:
                    if 'Date' in col_en and 'Age' not in col_en:
                        date_col = pd.to_datetime(df_to_merge_en[col_en], errors='coerce', dayfirst=dayfirst)
                        df_to_merge_en[col_en] = date_col.dt.strftime(target_format)
                        df_to_merge_en[col_en] = df_to_merge_en[col_en].astype(str).replace('NaT', '').replace('nan', '')

            df_master_staging = st.session_state.df_staging.copy()
            
            existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master_staging.index)]
            new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master_staging.index)]

            cols_to_update = [c for c in existing_rows_en.columns if c != 'Priority_Reason']
            df_master_staging.update(existing_rows_en[cols_to_update])
            df_master_staging = pd.concat([new_rows_en, df_master_staging])

            # Recalcular Prioridades y Estado
            df_master_staging = apply_priority_rules(df_master_staging)
            
            col_status_en = "Row Status"
            if col_status_en in df_master_staging.columns:
                cols_to_check_master = [
                    col for col in df_master_staging.columns
                    if col != col_status_en and col != 'Priority_Reason'
                ]
                df_check_master = df_master_staging[cols_to_check_master].fillna("").astype(str)
                blank_mask_master = (df_check_master == "") | (df_check_master == "0")
                incomplete_rows_master = blank_mask_master.any(axis=1)
                
                df_master_staging[col_status_en] = np.where(
                    incomplete_rows_master,
                    get_text(lang, 'status_incomplete'),
                    get_text(lang, 'status_complete')
                )

            # Asegurar tipos numéricos
            for col in df_master_staging.columns:
                if any(x in col for x in ['Total', 'Amount', 'Age', 'ID', 'Number']):
                     df_master_staging[col] = pd.to_numeric(df_master_staging[col], errors='coerce').fillna(0)

            df_master_staging = df_master_staging.sort_index(ascending=True)
            st.session_state.df_staging = df_master_staging.copy()
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            
            st.success(get_text(lang, 'save_success_message'))

        except Exception as e:
            st.error(f"Error al guardar el borrador: {e}")
            st.exception(e)

    def _callback_guardar_borrador_and_rerun():
        _callback_guardar_borrador()
        st.rerun()

    def _callback_guardar_estable():
        st.session_state.df_original = st.session_state.df_staging.copy()
        if st.session_state.columnas_visibles is not None:
            st.session_state.columnas_visibles_estable = st.session_state.columnas_visibles.copy()
        st.success(get_text(lang, 'commit_success_message'))

    def _callback_revertir_estable():
        if st.session_state.df_original is not None:
            st.session_state.df_staging = st.session_state.df_original.copy()
        if st.session_state.columnas_visibles_estable is not None:
            st.session_state.columnas_visibles = st.session_state.columnas_visibles_estable.copy()
        
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.session_state.editor_key_ver += 1

    # --- 3.6. Renderizado del Editor ---

    st.warning(get_text(lang, 'editor_manual_save_warning'))
    spinner_text = f"Cargando editor... {get_text(lang, 'hotkey_loading_warning')}"
    
    # Clave dinámica para forzar repintado (FIX AÑADIR FILA)
    current_ver = st.session_state.get('editor_key_ver', 0)
    editor_key = f"main_data_editor_{lang}_{current_ver}"

    # Controles de Selección Masiva
    col_sel1, col_sel2, _ = st.columns([0.15, 0.15, 0.7])
    with col_sel1:
        st.button("☑️ Marcar Todo", on_click=_callback_toggle_selection, args=(True,), help="Marcar todas las casillas", use_container_width=True)
    with col_sel2:
        st.button("⬜ Desmarcar", on_click=_callback_toggle_selection, args=(False,), help="Desmarcar todas las casillas", use_container_width=True)

    with st.spinner(spinner_text):
        editor_return_value = st.data_editor(
            st.session_state.editor_state,
            column_config=configuracion_columnas,
            num_rows="dynamic",
            width='stretch',
            height=600,
            key=editor_key,
            hide_index=False
        )

    # --- 3.7. Lógica de Acciones Masivas (Bulk Actions) ---
    indices_seleccionados = []
    
    if col_sel_name in editor_return_value.columns:
        filas_seleccionadas = editor_return_value[editor_return_value[col_sel_name] == True]
        if not filas_seleccionadas.empty:
            indices_raw = filas_seleccionadas.index.astype(str).str.replace("🚩 ", "")
            indices_seleccionados = pd.to_numeric(indices_raw, errors='coerce').dropna().unique()

    if len(indices_seleccionados) > 0:
        st.markdown("---")
        st.info(f"✅ **{len(indices_seleccionados)} filas seleccionadas.**")
        
        col_bulk_edit, col_bulk_del, _ = st.columns([0.2, 0.2, 0.6])
        
        with col_bulk_edit:
            if st.button(f"✏️ Editar {len(indices_seleccionados)} filas"):
                modal_bulk_edit(indices_seleccionados, col_map_ui_to_en, lang)
        
        with col_bulk_del:
             if st.button(f"🗑️ Eliminar {len(indices_seleccionados)} filas", type="primary"):
                 _callback_bulk_delete(indices_seleccionados)
        
        st.markdown("---")

    # --- 3.8. Botonera de Acciones Globales ---
    st.markdown(f"#### {get_text(lang, 'editor_actions_header')}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True,
            help=get_text(lang, 'add_row_help')
        )
    with col2:
        st.button(
            get_text(lang, 'save_changes_button'),
            on_click=_callback_guardar_borrador_and_rerun,
            use_container_width=True,
            help=get_text(lang, 'save_changes_help'),
            type="primary"
        )
    with col3:
        st.button(
            get_text(lang, 'commit_changes_button'),
            on_click=_callback_guardar_estable,
            use_container_width=True,
            help=get_text(lang, 'commit_changes_help'),
            key="commit_changes"
        )
    with col4:
        st.button(
            get_text(lang, 'reset_changes_button'),
            on_click=_callback_revertir_estable,
            use_container_width=True,
            help=get_text(lang, 'reset_changes_help'),
            key="reset_changes_button"
        )
        
    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- 3.9. Hotkeys ---
    if hotkeys.pressed("revert_stable", key='main_hotkeys'):
        _callback_revertir_estable()
        st.rerun()
    elif hotkeys.pressed("add_row", key='main_hotkeys'):
        callback_add_row()
        st.rerun()
    elif hotkeys.pressed("save_stable", key='main_hotkeys'):
        _callback_guardar_estable()
    elif hotkeys.pressed("save_draft", key='main_hotkeys'):
        _callback_guardar_borrador()
        st.rerun()

    # --- 3.10. Descargas ---
    st.markdown("---")
    col_dl1, col_dl2, col_restore = st.columns([0.3, 0.3, 0.4])
    
    with col_dl1:
        df_dl = editor_return_value.copy()
        if col_sel_name in df_dl.columns:
            df_dl = df_dl.drop(columns=[col_sel_name])
        df_dl.index = pd.to_numeric(df_dl.index.astype(str).str.replace("🚩 ", ""))
        df_dl.columns = [col_map_ui_to_en.get(c, c) for c in df_dl.columns]
        
        st.download_button(
            get_text(lang, 'download_excel_manual_edits_button'),
            to_excel(df_dl),
            "resultado_facturas_BORRADOR.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_editado",
            use_container_width=True
        )
        
    with col_dl2:
        st.download_button(
            get_text(lang, 'download_excel_filtered_button'),
            to_excel(df_vista_detallada),
            "resultados_Filtrados.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_filtrado",
            use_container_width=True
        )
        
    with col_restore:
        if st.button(
            get_text(lang, 'restore_pristine_button'),
            use_container_width=True,
            help=get_text(lang, 'restore_pristine_help'),
            key="restore_pristine"
        ):
            if st.session_state.df_pristine is not None:
                st.session_state.df_original = st.session_state.df_pristine.copy()
                st.session_state.df_staging = st.session_state.df_pristine.copy()
                st.session_state.columnas_visibles = list(st.session_state.df_pristine.columns)
                st.session_state.columnas_visibles_estable = list(st.session_state.df_pristine.columns)
            
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.session_state.editor_key_ver += 1
            st.rerun()


# --- 4. RENDER VISTA AGRUPADA ---
def render_grouped_view(
    lang: str,
    resultado_df: pd.DataFrame,
    col_map_ui_to_en: dict,
    todas_las_columnas_en: list
):
    """
    Renderiza una vista pivot/agrupada simple.
    """
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name",
        "Pay Status", "Document Type", "Row Status", "Priority", "Priority_Reason"
    ]
    opciones_agrupables_ui = [
        translate_column(lang, c) for c in columnas_agrupables_en
        if c in todas_las_columnas_en
    ]

    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables.")
        return

    col_para_agrupari = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    st.info(get_text(lang, 'group_view_blank_row_info'))

    if col_para_agrupari:
        col_en = col_map_ui_to_en.get(col_para_agrupari, col_para_agrupari)
        df_agg = resultado_df.copy()
        
        # Asegurar numéricos para agregación
        if 'Total' in df_agg.columns:
            df_agg['Total'] = pd.to_numeric(df_agg['Total'], errors='coerce')
        if 'Invoice Date Age' in df_agg.columns:
            df_agg['Invoice Date Age'] = pd.to_numeric(df_agg['Invoice Date Age'], errors='coerce')

        # Definir operaciones de agregación
        agg_ops = {'Total': ['sum', 'mean', 'min', 'max', 'count']}
        if 'Invoice Date Age' in df_agg.columns and pd.api.types.is_numeric_dtype(df_agg['Invoice Date Age']):
            agg_ops['Invoice Date Age'] = ['mean']

        try:
            df_res = df_agg.groupby(col_en).agg(agg_ops)
            
            # Nombres amigables para columnas agregadas
            cols_names = [
                get_text(lang, 'group_total_amount'),
                get_text(lang, 'group_avg_amount'),
                get_text(lang, 'group_min_amount'),
                get_text(lang, 'group_max_amount'),
                get_text(lang, 'group_invoice_count')
            ]
            if 'Invoice Date Age' in agg_ops:
                cols_names.append(get_text(lang, 'group_avg_age'))
            
            df_res.columns = cols_names

            st.dataframe(df_res.sort_values(by=get_text(lang, 'group_total_amount'), ascending=False))
            
            st.download_button(
                get_text(lang, 'download_excel_button'),
                to_excel(df_res),
                f"agrupado_por_{col_para_agrupari}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_agrupado"
            )
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.info("Seleccione una columna.")