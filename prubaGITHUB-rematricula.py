# ========================================
# === IMPORTACIONES NECESARIAS ==========
# ========================================
import os
import re
import sys
import unicodedata
import base64
from pathlib import Path
from collections import defaultdict

import pandas as pd
from textblob import TextBlob

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import matplotlib.pyplot as plt
import streamlit as st




# ========================================
# === CONFIGURACIÓN DE STREAMLIT PAGE ===
# ========================================
st.set_page_config(layout="wide")


# ========================================
# === RUTAS A IMÁGENES ===================
# ========================================
carpetaImagenes = Path(r"C:\Users\juan_garnicac\OneDrive - Corporación Unificada Nacional de Educación Superior - CUN\Imágenes")
logoCun = carpetaImagenes / "CUN-1200X1200.png"


# ========================================
# === RUTAS A ARCHIVOS DE DATOS =========
# ========================================
# Define el directorio base RELATIVO dentro del repositorio en GitHub.
# Esto asume que la carpeta 'TranscribirAudios' está en el mismo nivel
# que tu script Python principal (prubaGITHUB-rematricula.py) en el repo.
directorio_principal = Path("TranscribirAudios")

# Ahora define las rutas de los archivos Excel usando el directorio_principal relativo
ruta_archivo_reporte_puntaje = directorio_principal / "reporte_llamadas_asesores.xlsx"
ruta_archivo_sentimientos = directorio_principal / "sentimientos_textblob.xlsx"

# Corregir la ruta de resumen_llamadas.xlsx para que también use directorio_principal
resumen_llamadita = directorio_principal / "resumen_llamadas.xlsx"

# Asegúrate de que estos nombres de archivo coincidan exactamente con los que subiste a GitHub
nombre_archivo_reporte_acordeon = "acordon1.xlsx"
nombre_archivo_resultado_llamada_directo = "resultados_llamadas_directo.xlsx"

ruta_archivo_reporte_acordeon = directorio_principal / nombre_archivo_reporte_acordeon # Debería ser acordon1.xlsx
puntejeAcordeoneros = directorio_principal / nombre_archivo_resultado_llamada_directo # Debería ser resultados_llamadas_directo.xlsx

# Nota: Hay una inconsistencia en tu código original donde puntejeAcordeoneros y
# ruta_archivo_reporte_puntaje apuntan a archivos diferentes pero parecen usarse
# para propósitos similares (puntajes/acordeones). Asegúrate de que las variables
# y los archivos que cargan sean los correctos según la lógica de tu app.
# Sin embargo, el error que ves ahora es solo por la RUTA.






# ========================================
# === FUNCIONES DE SOPORTE ==============
# ========================================
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None
def insetCodigo():
    # Creamos tres columnas para el logo, el título y el emoji
    col1, col2, col3 = st.columns(3)

    # Definimos una altura común para el logo y el emoji
    # Ajusta este valor si quieres que sean más grandes o pequeños
    header_item_height = "180px"

    # Estilo para el logo (se centra y mantiene la proporción)
    img_style = f"height: {header_item_height}; width: auto; object-fit: contain; margin-left: auto; margin-right: auto; display: block;"

    # Estilo para el título (se centra en su columna y ajusta el tamaño de fuente)
    title_style = "font-size:48px; text-align:center; font-weight:bold;" # Ajusté el font-size del título un poco

    # Estilo para el emoji (se centra en su columna y su font-size coincide con la altura del logo)
    emoji_style = f"font-size: {header_item_height}; text-align:center; line-height: 1;" # line-height: 1 ayuda a la alineación vertical

    with col1:
        # Columna para el Logo CUN
        img1_base64 = get_image_base64(logoCun)
        if img1_base64:
            st.markdown(f'<img src="data:image/png;base64,{img1_base64}" style="{img_style}"/>', unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Logo CUN no encontrado en: {logoCun}")

    with col2:
        # Columna para el Título Central
        st.markdown(
            f"<div style='{title_style}'>Análisis Llamadas rematrícula</div>",
            unsafe_allow_html=True
        )

    with col3:
        # Columna para el Emoji
        st.markdown(f'<div style="{emoji_style}">🎯</div>', unsafe_allow_html=True)


def corregir_nombre(nombre):
    correcciones = {
        "DanielaLancheros": "Daniela Lancheros",
        "EdwinMiranda": "Edwin Miranda",
        "LuisaReyes": "Luisa Reyes",
        "MayerlyAcero": "Mayerly Acero",
        "NancyMoreno": "Nancy Moreno",
        "NicolasTovar": "Nicolas Tovar",
        "johan": "Johan",
        "NoseEntiendelenombredelasesor": "Desconocido",
        "NoSeEscucha": "Desconocido",
        "NotieneNombre": "Desconocido"
    }
    nombre_str = str(nombre).strip() if pd.notna(nombre) else ''
    return correcciones.get(nombre_str, nombre_str)


# ========================================
# === CARGA DE DATAFRAMES ===============
# ========================================
try:
    df_puntajeAsesores = pd.read_excel(ruta_archivo_reporte_puntaje)
    # Aplicar corrección de nombre inmediatamente después de cargar
    if 'asesor' in df_puntajeAsesores.columns:
        df_puntajeAsesores['asesor'] = df_puntajeAsesores['asesor'].apply(corregir_nombre)
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo de Puntajes: {ruta_archivo_reporte_puntaje}")
    df_puntajeAsesores = pd.DataFrame()
except Exception as e:
    st.error(f"❌ Error al cargar puntajes desde '{ruta_archivo_reporte_puntaje}': {e}")
    df_puntajeAsesores = pd.DataFrame()

try:
    df_POlaVssub = pd.read_excel(ruta_archivo_sentimientos)
    # Aplicar corrección de nombre inmediatamente después de cargar
    if 'asesor' in df_POlaVssub.columns:
        df_POlaVssub['asesor'] = df_POlaVssub['asesor'].apply(corregir_nombre)

    if 'sentimiento_promedio_polaridad' in df_POlaVssub.columns:
         df_POlaVssub.rename(columns={'sentimiento_promedio_polaridad': 'polarity'}, inplace=True)
         if 'subjectivity' not in df_POlaVssub.columns:
             df_POlaVssub['subjectivity'] = 0.5
    elif 'polarity' not in df_POlaVssub.columns:
         st.error(f"❌ El archivo '{ruta_archivo_sentimientos.name}' no tiene las columnas de polaridad esperadas.")
         df_POlaVssub = pd.DataFrame()
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo de Sentimientos: {ruta_archivo_sentimientos}")
    df_POlaVssub = pd.DataFrame()
except Exception as e:
    st.error(f"❌ Error al cargar sentimientos desde '{ruta_archivo_sentimientos}': {e}")
    df_POlaVssub = pd.DataFrame()

try:
    df_acordeon = pd.read_excel(puntejeAcordeoneros)
    # Aplicar corrección de nombre inmediatamente después de cargar
    if 'asesor' in df_acordeon.columns:
         df_acordeon['asesor'] = df_acordeon['asesor'].apply(corregir_nombre)
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo de Acordeon: {puntejeAcordeoneros}. Asegúrate de que el merge se haya ejecutado y guardado correctamente.")
    df_acordeon = pd.DataFrame()
except Exception as e:
    st.error(f"❌ Error al cargar acordeon desde '{puntejeAcordeoneros}': {e}")
    df_acordeon = pd.DataFrame()


# Ruta al archivo
resumen_llamadita = Path(
    r"C:\Users\juan_garnicac\OneDrive - Corporación Unificada Nacional de Educación Superior - CUN\Documentos\Rematricula-20250509T184654Z-001\TranscribirAudios\resumen_llamadas.xlsx"
)

# Intentamos leer el archivo y mostrar sus columnas
try:
    df_resumen = pd.read_excel(resumen_llamadita)
    df_resumen['asesor'] = df_resumen['asesor'].apply(corregir_nombre)
except Exception as e:
    st.error(f"⚠️ Ocurrió un error al leer el archivo: {e}")

# --- Importar resultados_llamadas_directo ---
try:
    resultados_llamadas_directo = pd.read_excel(ruta_archivo_reporte_puntaje)
    print(f"Archivo {ruta_archivo_reporte_puntaje.name} importado correctamente.")
    print(tabulate(resultados_llamadas_directo.head(), headers='keys', tablefmt='psql'))
except FileNotFoundError:
    print(f"No se encontró el archivo: {ruta_archivo_reporte_puntaje}")
    resultados_llamadas_directo = pd.DataFrame()
except Exception as e:
    print(f"Error al importar el archivo {ruta_archivo_reporte_puntaje.name}: {e}")
    resultados_llamadas_directo = pd.DataFrame()

# --- Importar acordeonYesid ---
try:
    acordeonYesid = pd.read_excel(ruta_archivo_reporte_acordeon)
    st.success(f"Archivo {nombre_archivo_reporte_acordeon} cargado correctamente.")
except Exception as e:
    st.error(f"Error cargando {nombre_archivo_reporte_acordeon}: {e}")



# ========================================
# === GRÁFICAS ===========================
# ========================================
def graficar_puntaje_total(df):
    if df is None or df.empty or 'asesor' not in df.columns or 'puntaje_total' not in df.columns:
        st.warning("⚠️ Datos incompletos para la gráfica de puntaje total.")
        return
    df['asesor'] = df['asesor'].apply(corregir_nombre)    
    df['puntaje_total'] = pd.to_numeric(df['puntaje_total'], errors='coerce')
    df_cleaned = df.dropna(subset=['asesor', 'puntaje_total'])
    if df_cleaned.empty:
        st.warning("⚠️ No hay datos válidos de asesor o puntaje total para graficar.")
        return
    fig = px.bar(
        df_cleaned.sort_values("puntaje_total", ascending=False),
        x="asesor",
        y="puntaje_total",
        text="puntaje_total",
        color="puntaje_total",
        color_continuous_scale="Greens",
        title="🎯 Puntaje Total Ponderado por Asesor",
        labels={"puntaje_total": "Puntaje Total Ponderado", "asesor": "Asesor"}
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        height=700, # Misma altura para todas las gráficas
        xaxis_tickangle=-45, plot_bgcolor="white",
        font=dict(family="Arial", size=12), # Tamaño de fuente original del código proporcionado
        title_x=0.5
    )
    # --- Inicia Gráfico: Puntaje Total ---
    st.plotly_chart(fig, use_container_width=True)
    # --- Fin Gráfico: Puntaje Total ---


def graficar_asesores_metricas_heatmap(df):
    if df is None or df.empty or 'asesor' not in df.columns:
        st.warning("⚠️ Datos incompletos o faltan columnas necesarias ('asesor') para la gráfica heatmap.")
        return
    metric_cols = [col for col in df.columns if '%' in col]
    if not metric_cols:
        st.warning("⚠️ No se encontraron columnas con '%' en el DataFrame para graficar el heatmap.")
        st.info(f"📋 Columnas disponibles: {df.columns.tolist()}")
        return
    df['asesor'] = df['asesor'].apply(corregir_nombre)       
    df_heatmap_data = df[['asesor'] + metric_cols].copy()
    df_heatmap_data = df_heatmap_data.set_index('asesor')
    df_heatmap_data = df_heatmap_data.apply(pd.to_numeric, errors='coerce').fillna(0)
    if df_heatmap_data.empty:
        st.warning("⚠️ Después de limpiar, el DataFrame para el heatmap está vacío.")
        return
    fig = go.Figure(data=go.Heatmap(
        z=df_heatmap_data.values, x=df_heatmap_data.columns, y=df_heatmap_data.index,
        colorscale='Greens',
        colorbar=dict(title=dict(text="Valor (%)", font=dict(size=24)), tickfont=dict(size=24)), # Corregido sintaxis, mantiene tamaño original
        hovertemplate='Asesor: %{y}<br>Métrica: %{x}<br>Valor: %{z:.2f}%<extra></extra>'
    ))
    fig.update_layout(
        title="Heatmap: Asesor vs. Métricas con Porcentaje (%)",
        xaxis_title="Métrica (%)", yaxis_title="Asesor",
        font=dict(family="Arial", size=12), # Tamaño de fuente original del código proporcionado
        height=700, # Misma altura para todas las gráficas
        title_x=0.5, plot_bgcolor='white'
    )
    # --- Inicia Gráfico: Heatmap Métricas ---
    st.plotly_chart(fig, use_container_width=True)
    # --- Fin Gráfico: Heatmap Métricas ---


def graficar_polaridad_subjetividad_gauges(df):
    if df is None or df.empty:
        st.warning("⚠️ El DataFrame de Sentimientos está vacío o no fue cargado correctamente para los gauges.")
        return
    if 'polarity' not in df.columns:
         st.error("❌ El DataFrame de Sentimientos no contiene la columna 'polarity' necesaria para el gauge de polaridad.")
         st.info(f"📋 Columnas disponibles: {df.columns.tolist()}")
         has_polarity = False
    else:
         has_polarity = True
    if 'subjectivity' not in df.columns:
        st.warning("⚠️ El DataFrame de Sentimientos no contiene la columna 'subjectivity'. El gauge de subjetividad no se mostrará.")
        st.info(f"📋 Columnas disponibles: {df.columns.tolist()}")
        has_subjectivity = False
    else:
         has_subjectivity = True
    if not has_polarity and not has_subjectivity:
         st.error("❌ No hay columnas válidas ('polarity', 'subjectivity') en el DataFrame de Sentimientos para generar ningún gauge.")
         return

    if has_polarity:
        df['asesor'] = df['asesor'].apply(corregir_nombre)   
        df['polarity'] = pd.to_numeric(df['polarity'], errors='coerce')
        polaridad_total = df['polarity'].mean()
        if pd.isna(polaridad_total): polaridad_total = 0
    else: polaridad_total = 0

    if has_subjectivity:
        df['asesor'] = df['asesor'].apply(corregir_nombre)   
        df['subjectivity'] = pd.to_numeric(df['subjectivity'], errors='coerce')
        subjetividad_total = df['subjectivity'].mean()
        if pd.isna(subjetividad_total): subjetividad_total = 0.5
    else: subjetividad_total = 0.5

    col1, col2 = st.columns(2)

    # --- Inicia Gráfico: Gauges Sentimiento General ---
    if has_polarity:
        with col1:
            df['asesor'] = df['asesor'].apply(corregir_nombre)   
            fig_polaridad = go.Figure(go.Indicator(
                mode="gauge+number", value=polaridad_total,
                gauge=dict(
                    axis=dict(range=[-1, 1]), # Configuración original de axis
                    bar=dict(color='darkgreen'), # Color original de la barra
                    steps=[
                        # PASOS Y COLORES ESPECIFICADOS POR TI AHORA para Polaridad
                        {'range': [-1, -0.3], 'color': '#c7e9c0'},
                        {'range': [-0.3, 0.3], 'color': '#a1d99b'},
                        {'range': [0.3, 1], 'color': '#31a354'}
                    ],
                    threshold={'line': {'color': "red", 'width': 4}, 'thickness': 0.75,'value': 0 }
                ),
                title={'text': "Polaridad Promedio General", 'font': {'size': 18}}, # Tamaño de fuente original
                number={'font': {'size': 24}} # Tamaño de fuente original
            ))
            fig_polaridad.update_layout(
                 height=700, # Misma altura para todas las gráficas
                 margin=dict(l=10, r=10, t=40, b=10),
                 font=dict(family="Arial", size=12) # Tamaño de fuente base original
            )
            st.plotly_chart(fig_polaridad, use_container_width=True)
    else:
         with col1: st.info("Gauge de Polaridad no disponible.")

    if has_subjectivity:
        with col2:
            fig_subjetividad = go.Figure(go.Indicator(
                mode="gauge+number", value=subjetividad_total,
                gauge=dict(
                    # --- CORRECCIÓN DE SINTAXIS AQUÍ (axis definition) ---
                    axis=dict(range=[0, 1]), # Corregido sintaxis, configuración original
                    # --- FIN CORRECCIÓN ---
                    bar={'color': 'darkblue'}, # Color original de la barra de subjetividad
                    steps=[
                         # Pasos y colores originales del gauge de subjetividad (del código que me diste antes de la confusión de colores)
                         {'range': [0.0, 0.3], 'color': '#e5f5e0'},
                         {'range': [0.3, 0.7], 'color': '#a1d99b'},
                         {'range': [0.7, 1.0], 'color': '#31a354'}
                    ],
                    threshold={'line': {'color': "red", 'width': 4}, 'thickness': 0.75,'value': 0.5}
                ),
                title={'text': "Subjetividad Promedio General", 'font': {'size': 18}}, # Tamaño de fuente original
                number={'font': {'size': 24}} # Tamaño de fuente original
            ))
            fig_subjetividad.update_layout(
                 height=700, # Misma altura para todas las gráficas
                 margin=dict(l=10, r=10, t=40, b=10),
                 font=dict(family="Arial", size=12) # Tamaño de fuente base original
            )
            st.plotly_chart(fig_subjetividad, use_container_width=True)
    else:
         with col2: st.info("Gauge de Subjetividad no disponible.")
    # --- Fin Gráfico: Gauges Sentimiento General ---


import streamlit as st
import pandas as pd
import plotly.express as px

def graficar_polaridad_por_asesor_barras_horizontales(df):
    if df is None or df.empty:
        st.warning("⚠️ El DataFrame para la gráfica de Polaridad está vacío o no fue cargado correctamente.")
        return
    if 'asesor' not in df.columns or 'polarity' not in df.columns:
        st.error("❌ El DataFrame no contiene las columnas necesarias: 'asesor' y 'polarity'.")
        st.info(f"📋 Columnas disponibles: {df.columns.tolist()}")
        return

    # Corregir nombres de asesores y convertir a numérico
    df['asesor'] = df['asesor'].apply(corregir_nombre)
    df['polarity'] = pd.to_numeric(df['polarity'], errors='coerce')
    df_cleaned = df.dropna(subset=['asesor', 'polarity'])

    if df_cleaned.empty:
        st.warning("⚠️ No hay datos válidos para graficar.")
        return

    # Agrupar por asesor y calcular promedio de polaridad
    df_polaridad_avg = df_cleaned.groupby('asesor', as_index=False)['polarity'].mean()
    df_polaridad_avg = df_polaridad_avg.sort_values('polarity', ascending=True)

    # Crear gráfico de barras verticales
    fig = px.bar(
        df_polaridad_avg,
        x='asesor',
        y='polarity',
        title='Polaridad Promedio por Asesor',
        labels={'polarity': 'Polaridad Promedio', 'asesor': 'Asesor'},
        color_discrete_sequence=['green']
    )

    # Ajustes de layout
    fig.update_layout(
        yaxis_range=[-1, 1],
        xaxis_title="Asesor",
        yaxis_title="Polaridad Promedio",
        plot_bgcolor="black",
        height=700,
        font=dict(family="Arial", size=12),
        title_x=0.5
    )

    st.plotly_chart(fig, use_container_width=True)
# ========================================
# === ANALISIS DETALLADO POR ASESOR (ACORDEONES) ===
# ========================================
def mostrar_acordeones(df):
    import streamlit as st
    import pandas as pd
    if df is None or df.empty:
        st.warning("⚠️ El DataFrame para los acordeones está vacío o no fue cargado correctamente.")
        return
    if 'asesor' not in df.columns:
        st.error("❌ El DataFrame para los acordeones no contiene la columna esencial: 'asesor'.")
        st.info(f"📋 Columnas disponibles: {df.columns.tolist()}")
        return

    # --- Inicia sección Detalle Completo por Asesor (Letra Más Grande) ---
    st.markdown("<h3 style='text-align: center;'>🔍 Detalle Completo por Asesor</h3>", unsafe_allow_html=True)
    # --- Fin sección Detalle Completo por Asesor ---

    for index, fila in df.iterrows():
        nombre_asesor = fila.get('asesor', f"Asesor Desconocido {index}")
        with st.expander(f"🧑 Detalle de: **{nombre_asesor}**"):
            columnas_a_mostrar = [col for col in df.columns if col != 'asesor']
            if not columnas_a_mostrar:
                st.info(f"ℹ️ No hay columnas para mostrar en el detalle de {nombre_asesor}.")
                continue
            for col_name in columnas_a_mostrar:
                value = fila[col_name]
                if pd.isna(value): display_value = "N/A"
                elif isinstance(value, (int, float)):
                    try:
                        # Mantener el formato de visualización del código original
                        display_value = f"{value:.1f}" # Formato original

                        # Ajustes según nombre de columna (basado en el código original)
                        if '%' in col_name or '_porcentaje' in col_name.lower():
                             display_value += "%"
                        elif 'puntaje' in col_name.lower():
                             display_value = f"{value:.1f}" # Puntaje original con .1f
                        elif value == int(value):
                            display_value = str(int(value)) # Enteros sin decimales
                        # Note: El código original para polaridad/sentimiento/subjetividad usaba .3f
                        elif 'polaridad' in col_name.lower() or 'sentimiento' in col_name.lower() or 'subjetividad' in col_name.lower():
                             display_value = f"{value:.3f}" # Sentimiento/Polaridad con 3 decimales
                        else: # Si no coincide con las reglas anteriores, usar .1f
                            display_value = f"{value:.1f}"


                    except ValueError: display_value = str(value)
                else: display_value = str(value)

                emoji = "🔹"
                if 'saludo' in col_name.lower(): emoji = "👋"
                elif 'presentacion' in col_name.lower(): emoji = "🏢"
                elif 'politica' in col_name.lower(): emoji = "🔊"
                elif 'valor' in col_name.lower(): emoji = "💡"
                elif 'costos' in col_name.lower(): emoji = "💰"
                elif 'cierre' in col_name.lower(): emoji = "✅"
                elif 'normativo' in col_name.lower(): emoji = "📜"
                elif 'puntaje' in col_name.lower(): emoji = "⭐"
                elif 'sentimiento' in col_name.lower() or 'polaridad' in col_name.lower() or 'subjetividad' in col_name.lower(): emoji = "😊"
                elif 'total_llamadas' in col_name.lower(): emoji = "📞"
                elif 'archivo' in col_name.lower(): emoji = "📄"

                st.markdown(f"{emoji} **{col_name.replace('_', ' ').capitalize()}:** {display_value}")

#000000000000000000000000000000000000000
#0000000 acordeon Yesid
##################################

# ========================================
# === ANALISIS DETALLADO POR ASESOR (ACORDEONES) ===
# ========================================
# Asegúrate de que la función corregir_nombre esté definida antes en el script
# Asegúrate de que las importaciones principales (pandas, streamlit) estén al inicio del script
# Si prefieres importar dentro de la función, mantén las líneas de importación aquí

import streamlit as st
import pandas as pd

def mostrar_acordeones_simple(df):
    if df is None or df.empty:
        st.warning("⚠️ El DataFrame está vacío o no fue cargado correctamente.")
        return
    if 'asesor' not in df.columns:
        st.error("❌ El DataFrame no contiene la columna 'asesor'.")
        return

    st.markdown("### 🔍 Detalle Completo por Asesor")

    df['asesor'] = df['asesor'].astype(str)
    unique_asesores = df['asesor'].dropna().unique()

    for nombre_asesor in unique_asesores:
        df_asesor = df[df['asesor'] == nombre_asesor]

        with st.expander(f"🧑 Detalle de: **{nombre_asesor}**"):
            for index, row in df_asesor.iterrows():
                filename = row.get('archivo', 'Archivo desconocido')
                st.write(f"Analizando: **{filename}**")

                # Detectar automáticamente las columnas *_conteo
                columnas_conteo = [col for col in df.columns if col.endswith('_conteo')]

                for col in columnas_conteo:
                    categoria = col.replace('_conteo', '')
                    conteo = row.get(col, 'N/A')

                    # Mostrar ✅ o ❌ basado en conteo
                    cumple = '✅' if pd.notna(conteo) and conteo >= 1 else '❌'
                    st.write(f"  🔹 {categoria.replace('_', ' ').capitalize()}: {conteo} {cumple} (mínimo 1)")

                # Mostrar puntaje y resultado final
                puntaje = row.get('puntaje_final_%', None)
                if pd.notna(puntaje):
                    resultado = 'Llamada efectiva' if puntaje >= 80 else 'No efectiva'
                    emoji = '✅' if puntaje >= 80 else '❌'
                    st.write(f"🎯 Resultado: {emoji} {resultado} — Puntaje: {puntaje:.1f}%")
                else:
                    st.write("🎯 Resultado: ? Resultado desconocido — Puntaje: N/A")

                if len(df_asesor) > 1 and index < len(df_asesor) - 1:
                    st.markdown("---")

# ========================================
# === FUNCIÓN PRINCIPAL STREAMLIT =======
# ========================================
def main():

    # --- Inicia Titulo de la Aplicación (Letra Más Grande) ---
    st.title("📊 Reporte de Llamadas y Sentimiento por Asesor")
    # --- Fin Titulo de la Aplicación ---

    insetCodigo()

    # --- Separa un grafico ---
    st.markdown("---")
    # --- Fin separación ---

    # --- Inicia sección Gráficos Resumen (Letra Más Grande) ---
    st.header("📈 Gráficos Resumen")
    # --- Fin sección Gráficos Resumen ---

    # --- Inicia Gráfico: Puntaje Total ---
    graficar_puntaje_total(df_puntajeAsesores)
    # --- Fin Gráfico: Puntaje Total ---

    # --- Separa un grafico ---
    st.markdown("---")
    # --- Fin separación ---

    # --- Inicia Gráfico: Heatmap Métricas ---
    graficar_asesores_metricas_heatmap(df_puntajeAsesores)
    # --- Fin Gráfico: Heatmap Métricas ---

    # --- Separa un grafico ---
    st.markdown("---")
    # --- Fin separación ---

    # --- Inicia Gráfico: Gauges Sentimiento General ---
    graficar_polaridad_subjetividad_gauges(df_POlaVssub)
    # --- Fin Gráfico: Gauges Sentimiento General ---

    # --- Separa un grafico ---
    st.markdown("---")
    # --- Fin separación ---
    graficar_polaridad_por_asesor_barras_horizontales(df_resumen)



    # --- Separa un grafico ---
    st.markdown("---")
    # --- Fin separación ---

    # --- Inicia sección Detalle por Asesor ---
    mostrar_acordeones(df_acordeon)
    # --- Fin sección Detalle por Asesor ---
    mostrar_acordeones_simple(df_acordeon)


# ========================================
# === EJECUCIÓN DEL PROGRAMA ============
# ========================================
if __name__ == '__main__':
    main()
