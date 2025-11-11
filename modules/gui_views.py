# modules/gui_views.py (VERSIÓN CON LÓGICA DE 🚩 LIMPIA Y CORREGIDA)
# Contiene la lógica para renderizar el contenido de la página principal.

import streamlit as st
import pandas as pd
import json 
import numpy as np
import warnings
from modules.translator import get_text, translate_column
from modules.gui_utils import to_excel
import streamlit_hotkeys as hotkeys 

# --- 1. RENDER FILTROS ACTIVOS ---
def render_active_filters(lang):
    """
    Muestra los filtros activos en la parte superior de la página.
    Permite a los usuarios eliminar filtros individualmente o todos a la vez.
    """
    # 'st.markdown': Escribe el título de la sección.
    st.markdown(f"## {get_text(lang, 'active_filters_header')}")
    
    # 'st.session_state.filtros_activos': Lista de filtros (dicts).
    if not st.session_state.filtros_activos:
        # 'st.info': Mensaje si no hay filtros.
        st.info(get_text(lang, 'no_filters_applied'))
        return 

    # 'filtros_a_eliminar': Índice del filtro a borrar (-1 = ninguno).
    filtros_a_eliminar = -1
    # 'num_filtros': Total de filtros.
    num_filtros = len(st.session_state.filtros_activos)
    
    # 'num_columnas': Organiza los filtros en hasta 5 columnas.
    num_columnas = max(1, min(num_filtros, 5)) 
    # 'cols_filtros': Crea las columnas de Streamlit.
    cols_filtros = st.columns(num_columnas)
    
    # 'i': Itera sobre los filtros para mostrarlos.
    for i, filtro in enumerate(st.session_state.filtros_activos):
        # 'col_index': Asigna el filtro a una columna.
        col_index = i % num_columnas
        with cols_filtros[col_index]:
            # 'col_ui': Traduce el nombre de la columna (ej. 'Status' -> 'Estado').
            col_ui = translate_column(lang, filtro['columna']) 
            # 'label_boton': Texto del botón (ej. "Estado: Pending ✕").
            label_boton = f"{col_ui}: {filtro['valor']}  ✕"
            
            # 'st.button': Muestra el botón de filtro.
            if st.button(label_boton, key=f"quitar_{i}", help=f"Quitar filtro {i+1}", type="primary"):
                # 'filtros_a_eliminar': Si se presiona, marca este filtro para borrar.
                filtros_a_eliminar = i
    
    # 'st.button': Botón para limpiar todos los filtros.
    if st.button(get_text(lang, 'clear_all_button'), key="limpiar_todos"):
        st.session_state.filtros_activos = []
        # 'st.rerun()': Recarga la página para aplicar el cambio.
        st.rerun() 
    
    # 'pop()': Si se marcó un filtro, se elimina de la lista.
    if filtros_a_eliminar > -1:
        st.session_state.filtros_activos.pop(filtros_a_eliminar)
        st.rerun() 

# --- 2. RENDER KPIS ---
def render_kpi_dashboard(lang, resultado_df):
    """
    Muestra el dashboard de KPIs (Total Facturas, Monto Total, Monto Promedio).
    
    Args:
        lang (str): Idioma actual.
        resultado_df (pd.DataFrame): El DataFrame *filtrado* sobre el cual calcular KPIs.
    """
    st.markdown(f"## {get_text(lang, 'kpi_header')}")
    
    try:
        # 'totales_numericos': Extrae la columna 'Total', la convierte a número 
        # (errores = NaN), y elimina los NaN.
        totales_numericos = pd.to_numeric(resultado_df['Total'], errors='coerce').dropna()
    except KeyError:
        # 'KeyError': Fallback si la columna 'Total' no existe.
        totales_numericos = pd.Series(dtype='float64')
        st.warning("No se encontró la columna 'Total' para los KPIs.")
    
    # 'st.columns': Divide la sección en 3 columnas para los KPIs.
    col1, col2, col3 = st.columns(3)
    
    # 'col1.metric': KPI 1 - Total de Facturas (conteo de filas).
    col1.metric(
        label=get_text(lang, 'kpi_total_invoices'), 
        value=len(resultado_df)
    )
    # 'col2.metric': KPI 2 - Monto Total (suma).
    col2.metric(
        label=get_text(lang, 'kpi_total_amount'), 
        value=f"${totales_numericos.sum():,.2f}",
        help=get_text(lang, 'kpi_total_amount_help')
    )
    # 'col3.metric': KPI 3 - Monto Promedio (media).
    col3.metric(
        label=get_text(lang, 'kpi_avg_amount'), 
        value=f"${totales_numericos.mean():,.2f}" if not totales_numericos.empty else "$0.00",
        help=get_text(lang, 'kpi_avg_amount_help')
    )

# --- 3. RENDER VISTA DETALLADA (EDITOR) ---
def render_detailed_view(lang, resultado_df_filtrado, df_master_copy, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista detallada principal con el editor de datos (st.data_editor).
    
    --- MODIFICACIÓN VISUAL ---
    Añade un indicador 🚩 al *índice* de la fila (columna congelada)
    si la fila es de "Maxima Prioridad" para visibilidad instantánea.
    """
    
    # 'hotkeys.activate': Registra los atajos de teclado (Ctrl+I, Ctrl+S, etc.).
    hotkeys.activate([
        hotkeys.hk("add_row", "i", ctrl=True, prevent_default=True, help="Insertar Fila (Ctrl+I)"), 
        hotkeys.hk("save_draft", "s", ctrl=True, prevent_default=True, help="Guardar Borrador (Ctrl+S)"),
        hotkeys.hk("save_stable", "s", ctrl=True, shift=True, prevent_default=True, help="Guardar Estable (Ctrl+Shift+S)"),
        hotkeys.hk("revert_stable", "z", ctrl=True, prevent_default=True, help="Revertir a Estable (Ctrl+Z)"),
    ],
        key='main_hotkeys'
    )

    # 'st.session_state.columnas_visibles': Verifica que el usuario tenga columnas seleccionadas.
    if not st.session_state.columnas_visibles:
            st.warning(get_text(lang, 'visible_cols_warning'))
            return

    # 'columnas_a_mostrar_en': Lista de columnas (EN) a mostrar.
    columnas_a_mostrar_en = st.session_state.columnas_visibles
    # 'columnas_finales': Intersección de columnas deseadas vs. columnas existentes.
    columnas_finales = [col for col in columnas_a_mostrar_en if col in resultado_df_filtrado.columns]
    
    if not columnas_finales:
        st.warning(get_text(lang, 'visible_cols_warning'))
        return

    # 'df_vista_detallada': Sub-DataFrame solo con las columnas visibles.
    df_vista_detallada = resultado_df_filtrado[columnas_finales].copy()
    
    # 'df_display': Copia para modificar (traducir encabezados).
    df_display = df_vista_detallada.copy()
    # 'df_display.columns': Traduce los encabezados (ej. 'Status' -> 'Estado').
    df_display.columns = [translate_column(lang, col) for col in df_display.columns]
    
    # --- [INICIO] LÓGICA DE INDICADOR EN EL ÍNDICE ---
    # Comprueba la prioridad de las filas *filtradas*
    if 'Priority' in resultado_df_filtrado.columns:
        try:
            # 'is_max_priority': Crea una máscara booleana (ej. [False, True, False])
            # [CORRECCIÓN 1/3]: Se busca el texto limpio "Maxima Prioridad" (o el texto con bandera,
            # por retrocompatibilidad, por si acaso) en la *columna* de datos.
            is_max_priority = (resultado_df_filtrado['Priority'] == "Maxima Prioridad") | (resultado_df_filtrado['Priority'] == "🚩 Maxima Prioridad")
            
            # 'np.where': Usa np.where para crear el nuevo índice
            new_index = np.where(
                is_max_priority, 
                "🚩 " + df_display.index.astype(str), # E.j: "🚩 123"
                df_display.index.astype(str)           # E.j: "124"
            )
            
            # 'df_display.index': Asigna el nuevo índice (que ahora contiene strings) al DataFrame
            df_display.index = new_index
        except Exception as e:
            st.warning(f"No se pudo aplicar el indicador de prioridad al índice: {e}")
    # --- [FIN] LÓGICA DE INDICADOR EN EL ÍNDICE ---

    # 'configuracion_columnas': Diccionario para configurar el data_editor.
    configuracion_columnas = {}
    
    # 'date_format_help_text': Ayuda para columnas de fecha.
    date_format_help_text = get_text(lang, 'date_format_help')
    # 'cached_options': Opciones de autocompletado (pre-calculadas).
    cached_options = st.session_state.get('autocomplete_options', {})

    # 'col_ui': Itera sobre las columnas *traducidas* (las que ve el usuario).
    for col_ui in df_display.columns:
        # 'col_en': Obtiene el nombre original en inglés.
        col_en = col_map_ui_to_en.get(col_ui, col_ui) 
        
        # 'st.column_config.SelectboxColumn': Si la columna está en 'cached_options', 
        # la convierte en un dropdown.
        if col_en in cached_options and cached_options[col_en]:
            configuracion_columnas[col_ui] = st.column_config.SelectboxColumn(
                f"{col_ui} (Autocompletar)",
                help=get_text(lang, 'autocomplete_help'),
                options=cached_options[col_en], 
                required=False 
            )
        
        # 'st.column_config.TextColumn': Si es fecha, añade ayuda de formato.
        elif 'Date' in col_en and 'Age' not in col_en:
            configuracion_columnas[col_ui] = st.column_config.TextColumn(
                f"{col_ui}",
                help=date_format_help_text,
                required=False
            )
    
    # 'filtros_json_string': Serializa los filtros.
    filtros_json_string = json.dumps(st.session_state.filtros_activos, sort_keys=True)
    # 'columnas_tuple': Convierte la lista de columnas en tupla (necesario para hash).
    columnas_tuple = tuple(st.session_state.columnas_visibles)
    # 'current_data_hash': Hash de los filtros y columnas.
    current_data_hash = hash((filtros_json_string, columnas_tuple))
    # 'current_lang_hash': Hash del idioma.
    current_lang_hash = hash(st.session_state.language)
    
    # --- [INICIO] LÓGICA DE ESTADO (CON FIX DE "ACTUALIZACIÓN INSTANTÁNEA") ---
    # Esta lógica decide si el estado del editor debe ser reseteado.
    if 'editor_state' not in st.session_state or \
       st.session_state.current_data_hash != current_data_hash or \
       st.session_state.current_lang_hash != current_lang_hash:
        
        # 'st.session_state.editor_state': Establece el estado del editor 
        # (con las banderas 🚩 ya en el índice).
        st.session_state.editor_state = df_display.copy() 
        # 'st.session_state.current_data_hash': Guarda el hash actual.
        st.session_state.current_data_hash = current_data_hash
        # 'st.session_state.current_lang_hash': Guarda el hash de idioma.
        st.session_state.current_lang_hash = current_lang_hash
        
        # --- [INICIO] FIX DEL PARPADEO (st.rerun + st.stop) ---
        # 'st.rerun()': Pone en cola el "parpadeo" (Run 3).
        st.rerun()
        
        # 'st.stop()': Detiene ESTE script (Run 2) AHORA.
        # Esto evita que st.data_editor() se renderice
        # con un estado "sucio" (que aún no "ve").
        st.stop()
        # --- [FIN] FIX DEL PARPADEO ---
        
    # --- [FIN] LÓGICA DE ESTADO (CON FIX DE "ACTUALIZACIÓN INSTANTÁNEA") ---


    def callback_add_row():
        """
        Callback para el botón 'Añadir Fila' o hotkey 'Ctrl+I'.
        Añade una fila vacía al 'editor_state' con un índice único.
        """
        # 'df_editado': Obtiene el estado actual del editor.
        df_editado = st.session_state.editor_state
        
        # 'max_index': Busca el índice máximo en el DF maestro.
        max_index = df_master_copy.index.max()
        if not df_editado.empty:
            # 'clean_indices': Limpia las banderas 🚩 del índice del editor.
            clean_indices = pd.to_numeric(
                pd.Series(df_editado.index).astype(str).str.replace("🚩 ", ""),
                errors='coerce'
            ).dropna()
            
            # 'max()': Compara el máx. del master vs. máx. del editor.
            if not clean_indices.empty:
                 max_index = max(max_index, clean_indices.max())

        # 'new_index': Asigna un nuevo índice numérico.
        new_index = int(max_index + 1) 

        # 'default_values': Crea un dict para la nueva fila (0 para números, "" para texto).
        default_values = {}
        for col in df_editado.columns:
            col_en = col_map_ui_to_en.get(col, col) 
            col_original_dtype = df_master_copy[col_en].dtype if col_en in df_master_copy.columns else 'object'
            if pd.api.types.is_numeric_dtype(col_original_dtype):
                default_values[col] = 0
            else:
                default_values[col] = ""
        
        # 'new_row_df': Crea un mini-DataFrame para la nueva fila.
        new_row_df = pd.DataFrame(default_values, index=[new_index])
        
        # 'st.session_state.editor_state': Añade la nueva fila al inicio del estado.
        st.session_state.editor_state = pd.concat(
            [new_row_df, df_editado], 
            ignore_index=False 
        )
    
    # 'st.warning': Mensaje importante sobre el guardado manual.
    st.warning(get_text(lang, 'editor_manual_save_warning'))
    
    # 'editor_return_value': Renderiza el editor y captura sus datos actuales.
    # Esta línea ahora solo se ejecutará en un "Run limpio" (Run 3).
    editor_return_value = st.data_editor(
        st.session_state.editor_state,
        column_config=configuracion_columnas, 
        num_rows="dynamic",
        width='stretch', 
        height=600,
        key="main_data_editor",
        hide_index=False 
    )

    # --- 3. DEFINICIÓN DE CALLBACKS DE ACCIÓN (Guardar/Revertir) ---

    def _callback_guardar_borrador():
        """
        (Ctrl+S) Guarda el estado del editor en 'df_staging' (Archivo 2: Borrador).
        
        --- MODIFICACIÓN ---
        Limpia el indicador 🚩 del índice antes de procesar
        y re-calcula la prioridad (AHORA SIN 🚩) en cada guardado.
        """
        
        try:
            # 1. 'df_edited_view_ui': Obtiene los datos del editor.
            df_edited_view_ui = editor_return_value.copy()
            
            # --- [INICIO] LIMPIEZA DE ÍNDICE ---
            # 'df_edited_view_ui.index': Limpia cualquier bandera 🚩 del índice.
            df_edited_view_ui.index = pd.to_numeric(
                df_edited_view_ui.index.astype(str).str.replace("🚩 ", "")
            )
            # --- [FIN] LIMPIEZA DE ÍNDICE ---

            # 2. 'df_to_merge_en': Traduce columnas de UI (ES) a Inglés (EN).
            df_to_merge_en = df_edited_view_ui.copy()
            df_to_merge_en.columns = [col_map_ui_to_en.get(col_ui, col_ui) for col_ui in df_to_merge_en.columns]

            # 3. Formatear Fechas (antes de fusionar).
            current_lang = st.session_state.language
            dayfirst = (current_lang == 'es')
            target_format = get_text(current_lang, 'date_format_es' if current_lang == 'es' else 'date_format_en')

            # 'warnings.catch_warnings': Suprime warnings de formato de fecha.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                
                for col_en in df_to_merge_en.columns:
                    if 'Date' in col_en and 'Age' not in col_en:
                        # 'pd.to_datetime': Parsea la fecha (ej. 'DD-MM-AAAA').
                        date_col = pd.to_datetime(df_to_merge_en[col_en], errors='coerce', dayfirst=dayfirst)
                        # 'dt.strftime': La formatea al estándar (ej. '%d-%m-%Y').
                        df_to_merge_en[col_en] = date_col.dt.strftime(target_format)
                        # 'replace('NaT', '')': Limpia fechas inválidas.
                        df_to_merge_en[col_en] = df_to_merge_en[col_en].astype(str).replace('NaT', '').replace('nan', '')

            # 4. 'df_master_staging': Carga el DataFrame de "borrador" completo.
            df_master_staging = st.session_state.df_staging.copy()

            # 'existing_rows_en': Filas que ya existían.
            existing_rows_en = df_to_merge_en[df_to_merge_en.index.isin(df_master_staging.index)]
            # 'new_rows_en': Filas nuevas (añadidas con 'Ctrl+I').
            new_rows_en = df_to_merge_en[~df_to_merge_en.index.isin(df_master_staging.index)]
            
            # 'df_master_staging.update': Actualiza las filas existentes.
            df_master_staging.update(existing_rows_en)
            # 'pd.concat': Añade las filas nuevas.
            df_master_staging = pd.concat([new_rows_en, df_master_staging])
            
            # 5.A. Re-calcular 'Row Status'
            col_status_en = "Row Status"
            if col_status_en in df_master_staging.columns:
                cols_to_check_master = [col for col in df_master_staging.columns if col != col_status_en]
                df_check_master = df_master_staging[cols_to_check_master].fillna("").astype(str)
                blank_mask_master = (df_check_master == "") | (df_check_master == "0")
                incomplete_rows_master = blank_mask_master.any(axis=1)
                df_master_staging[col_status_en] = np.where(
                    incomplete_rows_master,
                    get_text(lang, 'status_incomplete'),
                    get_text(lang, 'status_complete')
                )

            # --- [INICIO] LÓGICA DE PRIORIDAD (CORREGIDA) ---
            # 5.B. Re-calcular 'Priority'
            if 'Pay Group' in df_master_staging.columns and 'Priority' in df_master_staging.columns:
                
                # 'df_master_staging['Priority']': Asegura que sea string
                df_master_staging['Priority'] = df_master_staging['Priority'].astype(str)

                # 1. 'manual_priorities': Define prioridades "manuales"
                manual_priorities = ["Zero", "Low", "Medium", "High"]
                mask_manual = df_master_staging['Priority'].isin(manual_priorities)

                # 2. 'pay_group_searchable': Define prioridades automáticas (Pay Group)
                pay_group_searchable = df_master_staging['Pay Group'].astype(str).str.upper()
                high_priority_terms = ["DIST", "INTERCOMPANY", "PAYROLL", "RENTS", "SCF"]
                low_priority_terms = ["PAYGROUP", "PAY GROUP", "GNTD"]
                mask_high = pay_group_searchable.str.contains('|'.join(high_priority_terms), na=False)
                mask_low = pay_group_searchable.str.contains('|'.join(low_priority_terms), na=False)

                # 3. 'mask_excel_maxima': Define la máscara para "Maxima Prioridad" (con o sin 🚩)
                #    Esto es por retrocompatibilidad, por si el dato 'viejo' aún tiene la bandera.
                mask_excel_maxima = (df_master_staging['Priority'] == "Maxima Prioridad") | (df_master_staging['Priority'] == "🚩 Maxima Prioridad")

                # 4. 'conditions': Aplica las reglas en orden
                conditions = [
                    mask_manual,                      # 1. Si es manual, se queda como está.
                    mask_high,                        # 2. Si Pay Group es high -> Poner "Maxima Prioridad"
                    mask_excel_maxima,                # 3. Si se escribió "Maxima Prioridad" (con o sin 🚩) -> Poner "Maxima Prioridad"
                    mask_low                          # 4. Si Pay Group es low -> Poner "Baja Prioridad"
                ]
                
                # [CORRECCIÓN 2/3]: Se guarda el texto limpio "Maxima Prioridad" (sin bandera) en los datos.
                choices = [
                    df_master_staging['Priority'],    # 1.
                    "Maxima Prioridad",               # 2.
                    "Maxima Prioridad",               # 3.
                    "Baja Prioridad"                  # 4.
                ]
                
                # 'np.select': El default es mantener el valor original
                df_master_staging['Priority'] = np.select(conditions, choices, default=df_master_staging['Priority'])
            
            # --- [FIN] LÓGICA DE PRIORIDAD (CORREGIDA) ---
            
            # 6. Forzar tipos numéricos.
            for col in df_master_staging.columns:
                if 'Total' in col or 'Amount' in col or 'Age' in col or 'ID' in col or 'Number' in col:
                     df_master_staging[col] = pd.to_numeric(df_master_staging[col], errors='coerce').fillna(0)
            
            # 7. 'sort_index': Ordena y guarda en 'staging'.
            df_master_staging = df_master_staging.sort_index(ascending=True)
            # 'st.session_state.df_staging': Guarda el borrador actualizado.
            st.session_state.df_staging = df_master_staging.copy()
            
            # 8. Actualizar el 'editor_state' (la vista)
            
            columnas_visibles_en = st.session_state.columnas_visibles
            columnas_a_usar = [col for col in columnas_visibles_en if col in df_master_staging.columns]

            # 'df_updated_view_en': Toma solo las filas y columnas visibles del DF maestro.
            df_updated_view_en = df_master_staging[
                df_master_staging.index.isin(df_to_merge_en.index) # Solo filas en la vista
            ][columnas_a_usar] # TODAS las columnas visibles
            
            col_map_en_to_ui_full = {v: k for k, v in col_map_ui_to_en.items()}
            
            # 'df_updated_view_ui': Traduce los encabezados a UI (ES).
            df_updated_view_ui = df_updated_view_en.copy()
            df_updated_view_ui.columns = [col_map_en_to_ui_full.get(col_en, col_en) for col_en in df_updated_view_ui.columns]
            
            # --- [INICIO] RE-APLICAR INDICADOR 🚩 AL ÍNDICE DEL EDITOR ---
            if 'Priority' in df_updated_view_en.columns: # Usa el DF en inglés (limpio)
                
                # [CORRECCIÓN 3/3]: Se lee el texto limpio "Maxima Prioridad" (o el texto con bandera,
                # por retrocompatibilidad) para volver a poner la bandera en el índice.
                is_max_priority_editor = (df_updated_view_en['Priority'] == "Maxima Prioridad") | (df_updated_view_en['Priority'] == "🚩 Maxima Prioridad")
                
                new_index_editor = np.where(
                    is_max_priority_editor, 
                    "🚩 " + df_updated_view_ui.index.astype(str), 
                    df_updated_view_ui.index.astype(str)
                )
                df_updated_view_ui.index = new_index_editor
            # --- [FIN] RE-APLICAR INDICADOR 🚩 AL ÍNDICE DEL EDITOR ---
            
            # 'st.session_state.editor_state': Actualiza el estado del editor.
            st.session_state.editor_state = df_updated_view_ui
            
            # 'st.success': Mensaje de éxito.
            st.success(get_text(lang, 'save_success_message'))

        except Exception as e:
            st.error(f"Error al guardar el borrador: {e}")
            st.exception(e)

    def _callback_guardar_borrador_and_rerun():
        """
        Función wrapper que ejecuta el guardado Y LUEGO un rerun.
        Esto restaura el "parpadeo" que actualiza los KPIs.
        """
        _callback_guardar_borrador()
        st.rerun()

    def _callback_guardar_estable():
        """
        (Ctrl+Shift+S) Copia 'df_staging' (Borrador) a 'df_original' (Estable).
        """
        # 'df_original': Sobrescribe el "Estable" con el "Borrador" actual.
        st.session_state.df_original = st.session_state.df_staging.copy()
        if st.session_state.columnas_visibles is not None:
            # 'columnas_visibles_estable': Guarda también el estado de las columnas.
            st.session_state.columnas_visibles_estable = st.session_state.columnas_visibles.copy()
        st.success(get_text(lang, 'commit_success_message'))


    def _callback_revertir_estable():
        """
        (Ctrl+Z) Copia 'df_original' (Estable) a 'df_staging' (Borrador).
        """
        if st.session_state.df_original is not None:
            # 'df_staging': Restaura el "Borrador" desde el "Estable".
            st.session_state.df_staging = st.session_state.df_original.copy()
            
        if st.session_state.columnas_visibles_estable is not None:
            # 'columnas_visibles': Restaura el estado de las columnas.
            st.session_state.columnas_visibles = st.session_state.columnas_visibles_estable.copy()
            
        # 'st.session_state.editor_state = None': Fuerza al editor a recargarse 
        # (y activar el st.rerun() + st.stop() de nuestro fix).
        st.session_state.editor_state = None
        st.session_state.current_data_hash = None
        st.session_state.current_lang_hash = None

    # --- 4. RENDERIZADO DE BOTONES DE CONTROL ---
    
    st.markdown(f"#### {get_text(lang, 'editor_actions_header')}")
    
    col1, col2, col3, col4 = st.columns(4)

    # 'col1': Botón Añadir Fila
    with col1:
        st.button(
            get_text(lang, 'add_row_button'),
            on_click=callback_add_row,
            use_container_width=True,
            help=get_text(lang, 'add_row_help') 
        )

    # 'col2': Botón Guardar Borrador
    with col2:
        st.button(
            get_text(lang, 'save_changes_button'),
            on_click=_callback_guardar_borrador_and_rerun, 
            use_container_width=True,
            help=get_text(lang, 'save_changes_help'),
            type="primary" 
        )
    
    # 'col3': Botón Guardar Estable
    with col3:
        st.button(
            get_text(lang, 'commit_changes_button'),
            on_click=_callback_guardar_estable, 
            use_container_width=True,
            help=get_text(lang, 'commit_changes_help'),
            key="commit_changes" 
        )
        
    # 'col4': Botón Revertir a Estable
    with col4:
        st.button(
            get_text(lang, 'reset_changes_button'),
            on_click=_callback_revertir_estable, 
            use_container_width=True,
            help=get_text(lang, 'reset_changes_help'),
            key="reset_changes_button"
        )

    st.warning(get_text(lang, 'editor_info_help_add_row'))

    # --- 5. MANEJO DE EVENTOS (HOTKEYS) ---
    
    hk_add_row = hotkeys.pressed("add_row", key='main_hotkeys')
    hk_save_stable = hotkeys.pressed("save_stable", key='main_hotkeys')
    hk_save_draft = hotkeys.pressed("save_draft", key='main_hotkeys')
    hk_revert_stable = hotkeys.pressed("revert_stable", key='main_hotkeys')
    
    # 'hk_revert_stable': Si se presiona Ctrl+Z...
    if hk_revert_stable: 
        _callback_revertir_estable() 
        st.rerun() 
        
    # 'hk_add_row': Si se presiona Ctrl+I...
    elif hk_add_row: 
        callback_add_row()
        st.rerun() 
        
    # 'hk_save_stable': Si se presiona Ctrl+Shift+S...
    elif hk_save_stable: 
        _callback_guardar_estable() 
    
    # 'hk_save_draft': Si se presiona Ctrl+S...
    elif hk_save_draft: 
        _callback_guardar_borrador() 
        st.rerun() 
            
    # --- Descargas y Restauración Original ---
    st.markdown("---")
    col_dl1, col_dl2, col_restore = st.columns([0.3, 0.3, 0.4])

    # 'col_dl1': Botón Descargar Borrador (con ediciones)
    with col_dl1:
        df_para_descargar_editado = editor_return_value.copy()
        
        # 'df_para_descargar_editado.index': Limpia el índice (quita 🚩) antes de descargar.
        df_para_descargar_editado.index = pd.to_numeric(
            df_para_descargar_editado.index.astype(str).str.replace("🚩 ", "")
        )
        # 'df_para_descargar_editado.columns': Traduce columnas a EN antes de descargar.
        df_para_descargar_editado.columns = [
            col_map_ui_to_en.get(col_ui, col_ui) 
            for col_ui in df_para_descargar_editado.columns
        ]
        # 'excel_data_editada': Convierte el DF a bytes.
        excel_data_editada = to_excel(df_para_descargar_editado)
        # 'st.download_button': Botón de descarga.
        st.download_button(
            label=get_text(lang, 'download_excel_manual_edits_button'), 
            data=excel_data_editada,
            file_name="resultado_facturas_BORRADOR.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_editado",
            use_container_width=True
        )
    
    # 'col_dl2': Botón Descargar Vista Filtrada (sin ediciones)
    with col_dl2:
        # 'excel_data_filtrada': Usa 'df_vista_detallada' (el DF filtrado original).
        excel_data_filtrada = to_excel(df_vista_detallada)
        st.download_button(
            label=get_text(lang, 'download_excel_filtered_button'), 
            data=excel_data_filtrada,
            file_name="resultados_Filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel_filtrado",
            use_container_width=True
        )

    # 'col_restore': Botón Restaurar Original (Peligroso)
    with col_restore:
        if st.button(
            get_text(lang, 'restore_pristine_button'),
            use_container_width=True,
            help=get_text(lang, 'restore_pristine_help'),
            key="restore_pristine" 
        ):
            # 'st.session_state.df_pristine': Carga la Copia 0 (Original).
            if st.session_state.df_pristine is not None:
                # 'df_original', 'df_staging': Resetea Estable y Borrador a la Copia 0.
                st.session_state.df_original = st.session_state.df_pristine.copy()
                st.session_state.df_staging = st.session_state.df_pristine.copy()
            
            # 'st.session_state.editor_state = None': Resetea el editor.
            st.session_state.editor_state = None
            st.session_state.current_data_hash = None
            st.session_state.current_lang_hash = None
            
            if st.session_state.df_pristine is not None:
                # 'columnas_originales': Resetea las columnas visibles.
                columnas_originales = list(st.session_state.df_pristine.columns)
                st.session_state.columnas_visibles = columnas_originales.copy()
                st.session_state.columnas_visibles_estable = columnas_originales.copy()
                
            st.rerun() 

# --- 4. RENDER VISTA AGRUPADA ---
def render_grouped_view(lang, resultado_df, col_map_ui_to_en, todas_las_columnas_en):
    """
    Muestra la vista de análisis agrupado.
    
    Args:
        lang (str): Idioma actual.
        resultado_df (pd.DataFrame): DF filtrado para agrupar.
        col_map_ui_to_en (dict): Mapa de traducción.
        todas_las_columnas_en (list): Lista de todas las columnas.
    """
    
    # 'columnas_agrupables_en': Lista de columnas (EN) permitidas para agrupar.
    columnas_agrupables_en = [
        "Vendor Name", "Status", "Assignee", "Operating Unit Name", 
        "Pay Status", "Document Type", "Row Status", "Priority"
    ]
    # 'opciones_agrupables_ui': Lista traducida (ES) de columnas disponibles.
    opciones_agrupables_ui = [
        translate_column(lang, col) 
        for col in columnas_agrupables_en 
        if col in todas_las_columnas_en
    ]
    
    if not opciones_agrupables_ui:
        st.warning("No hay columnas agrupables (ej. 'Vendor Name', 'Status') en su archivo.")
        return

    # 'st.selectbox': Dropdown para seleccionar por qué columna agrupar.
    col_para_agrupari = st.selectbox(
        get_text(lang, 'group_by_select'),
        options=opciones_agrupables_ui,
        key='group_by_col_select'
    )
    
    st.info(get_text(lang, 'group_view_blank_row_info'))
    
    if col_para_agrupari:
        # 'col_para_agrupar_en': Traduce la selección a EN.
        col_para_agrupar_en = col_map_ui_to_en.get(col_para_agrupari, col_para_agrupari)
        df_agrupado = resultado_df.copy() 
        
        # 'pd.to_numeric': Asegura que 'Total' y 'Age' sean numéricas.
        if 'Total' in df_agrupado.columns:
            df_agrupado['Total'] = pd.to_numeric(df_agrupado['Total'], errors='coerce')
        if 'Invoice Date Age' in df_agrupado.columns:
            df_agrupado['Invoice Date Age'] = pd.to_numeric(df_agrupado['Invoice Date Age'], errors='coerce')

        # 'agg_operations': Define las operaciones de agregación (suma, media, etc.).
        agg_operations = {'Total': ['sum', 'mean', 'min', 'max', 'count']}
        
        if 'Invoice Date Age' in df_agrupado.columns and pd.api.types.is_numeric_dtype(df_agrupado['Invoice Date Age']):
            agg_operations['Invoice Date Age'] = ['mean']

        try: 
            # 'df.groupby().agg()': Ejecuta la agrupación.
            df_agrupado_calculado = df_agrupado.groupby(col_para_agrupar_en).agg(agg_operations)
            
            # 'col_names_grouped': Nombres traducidos para la tabla de resultados.
            col_names_grouped = [
                get_text(lang, 'group_total_amount'), get_text(lang, 'group_avg_amount'),
                get_text(lang, 'group_min_amount'), get_text(lang, 'group_max_amount'),
                get_text(lang, 'group_invoice_count')
            ]
            if 'Invoice Date Age' in agg_operations:
                col_names_grouped.append(get_text(lang, 'group_avg_age'))
            
            df_agrupado_calculado.columns = col_names_grouped
            
            # 'st.dataframe': Muestra la tabla agrupada.
            st.dataframe(df_agrupado_calculado.sort_values(by=get_text(lang, 'group_total_amount'), ascending=False))
            
            # 'excel_data': Prepara la tabla para descargar.
            excel_data = to_excel(df_agrupado_calculado)
            st.download_button(
                label=get_text(lang, 'download_excel_button'), 
                data=excel_data,
                file_name=f"agrupado_por_{col_para_agrupari}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_agrupado"
            )
        except Exception as group_error:
            st.error(f"Error al agrupar por '{col_para_agrupari}': {group_error}")
    else:
        st.info("Por favor, seleccione una columna para agrupar.")