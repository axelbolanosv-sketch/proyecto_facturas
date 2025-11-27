
-----

# 📄 PROYECTO: Buscador de Facturas Dinámico e Inteligente

## 1\. Descripción General

Esta aplicación es una herramienta de Inteligencia de Negocios (BI) y gestión operativa construida sobre **Python** y **Streamlit**. Su propósito principal es permitir la carga, análisis, depuración y priorización de grandes volúmenes de facturas en formato Excel (`.xlsx`).

A diferencia de un visor de Excel tradicional, este sistema incorpora un **Motor de Reglas de Negocio**, un **Chatbot Heurístico** para consultas en lenguaje natural y un sistema de **Auditoría** para trazar cada cambio realizado sobre los datos.

-----

## 2\. Tecnologías y Librerías Utilizadas

El proyecto se basa en un stack tecnológico robusto y eficiente. A continuación se detalla cada librería y la razón de su elección:

### 📦 Principales (Core)

  * **`streamlit` (v1.x):**
      * *Uso:* Framework principal para la interfaz de usuario (UI).
      * *Por qué:* Permite convertir scripts de datos en aplicaciones web interactivas rápidamente sin necesidad de saber HTML/CSS/JS. Maneja el ciclo de vida de la aplicación y el "Session State".
  * **`pandas`:**
      * *Uso:* Manipulación y análisis de datos.
      * *Por qué:* Es el estándar en ciencia de datos. Se utiliza para cargar el Excel, filtrar filas, calcular columnas nuevas (vectorización) y generar agregaciones (agrupar por).
  * **`numpy`:**
      * *Uso:* Operaciones numéricas de bajo nivel.
      * *Por qué:* Se utiliza dentro de los módulos de utilidades para realizar comparaciones vectorizadas (ej. `np.where`) que son mucho más rápidas que los bucles `for` tradicionales al procesar miles de filas.
  * **`openpyxl`:**
      * *Uso:* Motor de lectura/escritura de Excel.
      * *Por qué:* Pandas necesita este motor para interactuar con archivos `.xlsx` modernos, soportando tipos de datos complejos y fechas.

### 🛠️ Utilidades y UI

  * **`streamlit-hotkeys`:**
      * *Uso:* Atajos de teclado.
      * *Por qué:* Mejora la productividad del usuario avanzado permitiendo guardar (Ctrl+S), añadir filas (Ctrl+I) o deshacer cambios (Ctrl+Z) sin usar el mouse.
  * **`uuid` (Librería estándar):**
      * *Uso:* Generación de Identificadores Únicos.
      * *Por qué:* Cada regla de negocio creada recibe un ID único para poder ser editada o eliminada sin conflictos.
  * **`difflib` (Librería estándar):**
      * *Uso:* Comparación de secuencias.
      * *Por qué:* Es el cerebro detrás del reconocimiento "difuso" del Chatbot. Permite que el sistema entienda "Amszon" como "Amazon", corrigiendo errores tipográficos del usuario.
  * **`unicodedata` & `re` (Librerías estándar):**
      * *Uso:* Procesamiento de texto (NLP Básico).
      * *Por qué:* Se usan para normalizar el texto (quitar tildes, convertir a minúsculas) antes de que el chatbot intente entender la intención del usuario.

-----

## 3\. Arquitectura del Proyecto

El código sigue una arquitectura modular para facilitar el mantenimiento y la escalabilidad.

```text
/proyecto_facturas
│
├── app.py                  # Puntos de entrada (Main). Orquesta la UI principal.
├── requirements.txt        # Lista de dependencias para instalación.
│
├── modules/                # Lógica de negocio separada por responsabilidades
│   ├── audit_service.py    # Sistema de Logs: Registra quién hizo qué cambio.
│   ├── chatbot_logic.py    # Cerebro del Chatbot: NLP, detección de intenciones.
│   ├── filters.py          # Motor de Filtrado: Lógica AND/OR y operadores (>, <).
│   ├── gui_chatbot.py      # Interfaz visual del chat (burbujas, historial).
│   ├── gui_rules_editor.py # Modal para crear/editar reglas de negocio.
│   ├── gui_sidebar.py      # Barra lateral: Carga de archivos, usuario, config.
│   ├── gui_views.py        # Vistas principales: Tabla editable, KPIs, Gráficos.
│   ├── loader.py           # Carga segura de Excel y limpieza inicial.
│   ├── rules_service.py    # Motor de Reglas: Aplica lógica condicional a los datos.
│   ├── translator.py       # Internacionalización (Español/Inglés).
│   └── utils.py            # Gestión del Estado (Session State), CSS y exportación.
```

-----

## 4\. Funcionamiento Detallado

### A. Ciclo de Vida de los Datos (State Management)

El sistema maneja tres copias de los datos en memoria (`session_state`) para garantizar la integridad:

1.  **`df_pristine`**: Copia inmutable del archivo original subido. Permite "Restaurar de fábrica".
2.  **`df_original` (Stable):** El último punto de guardado confirmado ("Commit"). Es a donde se vuelve si se hace un "Revert".
3.  **`df_staging` (Draft):** El borrador de trabajo donde ocurren las ediciones en tiempo real.

### B. Motor de Reglas de Negocio (`rules_service.py`)

Permite automatizar la columna "Prioridad".

  * **Lógica:** Las reglas se evalúan en orden secuencial.
  * **Importante:** Implementa una lógica de **"Orden Inverso"**. Las reglas con número de orden *mayor* (ej. 100) se ejecutan primero, y las de orden *menor* (ej. 10) se ejecutan al final.
  * *¿Por qué?* Esto asegura que las reglas más críticas (orden bajo) sobrescriban a las reglas generales (orden alto).

### C. Chatbot "Actionable" (`chatbot_logic.py`)

No es una IA generativa (como GPT), sino un modelo heurístico determinista.

1.  **Normalización:** Limpia la entrada del usuario.
2.  **Detección de Intención:** Busca palabras clave ("filtrar", "graficar", "top").
3.  **Búsqueda Difusa:** Compara tokens con los datos reales del Excel para encontrar coincidencias de Proveedores o Estados.
4.  **Acción:** Puede ejecutar filtros, generar gráficos Altair o calcular estadísticas automáticamente.

-----

## 5\. Plan de Creación y Evolución

Este proyecto fue diseñado siguiendo fases evolutivas para asegurar funcionalidad en cada etapa:

### Fase 1: Cimiento y Visualización

  * **Objetivo:** Cargar un Excel y mostrarlo.
  * **Desarrollo:** Creación de `loader.py` y `app.py`. Uso de `st.dataframe` para visualización básica.

### Fase 2: Interactividad y Filtros

  * **Objetivo:** Dejar de ser un visor pasivo.
  * **Desarrollo:** Implementación de `filters.py` permitiendo lógica dinámica. Creación del Sidebar para gestionar filtros acumulativos.

### Fase 3: Edición y Control de Cambios (CRUD)

  * **Objetivo:** Permitir corregir datos erróneos.
  * **Desarrollo:** Transición a `st.data_editor`. Implementación de la lógica de 3 estados (Pristine/Original/Staging) en `utils.py` para permitir "Guardar Borrador", "Hacer Commit" y "Deshacer".

### Fase 4: Automatización (Reglas de Negocio)

  * **Objetivo:** Reducir el trabajo manual de priorización.
  * **Desarrollo:** Creación de `rules_service.py`. Diseño del modal gráfico `gui_rules_editor.py` para que usuarios no técnicos puedan programar lógica (ej: "Si el monto \> 10,000, Prioridad = Alta").

### Fase 5: Inteligencia Asistida (Chatbot)

  * **Objetivo:** Facilitar el análisis rápido.
  * **Desarrollo:** Implementación de `chatbot_logic.py` para detectar anomalías estadísticas (Outliers) y generar rankings "Top N" mediante comandos de texto.

### Fase 6: Auditoría y Profesionalización

  * **Objetivo:** Trazabilidad y Seguridad.
  * **Desarrollo:** Módulo `audit_service.py` para loguear cada acción (quién cambió qué celda). Internacionalización (Inglés/Español) y optimización de rendimiento (vectorización en pandas).

-----

## 6\. Instrucciones de Instalación y Ejecución

### Requisitos Previos

  * Python 3.9 o superior.

### Pasos

1.  **Crear entorno virtual (Recomendado):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Mac/Linux
    venv\Scripts\activate     # En Windows
    ```

2.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar la aplicación:**

    ```bash
    streamlit run app.py
    ```

-----

## 7\. Notas para el Desarrollador

  * **Hotkeys:** Al editar el código, ten en cuenta que `streamlit-hotkeys` inyecta JavaScript. Si cambias los IDs de los botones, verifica los bindings.
  * **Vectorización:** Evita iterar sobre filas (`for index, row in df.iterrows()`) en `utils.py` o `filters.py`. Usa siempre operaciones vectorizadas de Pandas o Numpy (ej. `df['col'] = np.where(...)`) para mantener el rendimiento con archivos grandes.
  * **Caché:** Se utiliza `@st.cache_data` en funciones pesadas como `to_excel`. Si modificas la estructura del Excel, recuerda limpiar la caché o reiniciar el servidor.