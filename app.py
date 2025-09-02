import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import time
import os
import hashlib
import logging
from supabase import create_client, Client
import qrcode
from PIL import Image
import fpdf
from fpdf import FPDF
import base64
import io
import tempfile
import re
import sqlite3
from typing import Dict, List, Optional, Tuple, Any, Union

# Configuración de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================
# Configuración de Supabase
# ================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# Funciones de utilidad
# ================================
def validar_fecha(fecha_str: str) -> bool:
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_numero_positivo(valor: float) -> bool:
    return isinstance(valor, (int, float)) and valor >= 0

def productividad_hora(cantidad: float, horas: float) -> float:
    return cantidad / horas if horas > 0 else 0

# ================================
# Funciones de acceso a datos (Supabase)
# ================================
def obtener_trabajadores() -> pd.DataFrame:
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                       "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias"] * 8
        })
    try:
        response = supabase.from_('trabajadores').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return df[['nombre', 'equipo']]
        return pd.DataFrame(columns=['nombre', 'equipo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores: {e}", exc_info=True)
        return pd.DataFrame(columns=['nombre', 'equipo'])

def cargar_datos_fecha(fecha: str) -> Dict[str, Any]:
    """Carga datos ya guardados para una fecha específica."""
    if supabase is None:
        return {}
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return df.set_index('nombre').T.to_dict()
        return {}
    except Exception as e:
        logger.error(f"Error al cargar datos para {fecha}: {e}")
        return {}

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    try:
        registros = []
        for nombre, info in datos.items():
            if not all([
                validar_fecha(fecha),
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                continue
            registro = {
                "fecha": fecha,
                "nombre": nombre,
                "actividad": info.get("actividad", ""),
                "cantidad": float(info.get("cantidad", 0)),
                "meta": float(info.get("meta", 0)),
                "eficiencia": float(info.get("eficiencia", 0)),
                "productividad": float(info.get("productividad", 0)),
                "comentario": info.get("comentario", ""),
                "meta_mensual": float(info.get("meta_mensual", 0)),
                "horas_trabajo": float(info.get("horas_trabajo", 0)),
                "equipo": info.get("equipo", "")
            }
            registros.append(registro)
        if registros:
            supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
            logger.info(f"Datos guardados para {fecha}")
            return True
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}", exc_info=True)
    return False

def cargar_historico_db(fecha_inicio: str = None, fecha_fin: str = None, trabajador: str = None) -> pd.DataFrame:
    if supabase is None:
        return pd.DataFrame()
    try:
        query = supabase.from_('daily_kpis').select('*')
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador and trabajador != "Todos":
            query = query.eq('nombre', trabajador)
        query = query.order('fecha', desc=False)
        response = query.execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar histórico: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# Obtener logo desde Supabase Storage
# ================================
@st.cache_data(ttl=3600)
def obtener_logo_url(nombre_imagen: str) -> str:
    try:
        # URL pública del archivo en Supabase Storage
        url = f"{SUPABASE_URL}/storage/v1/object/public/images/{nombre_imagen}"
        # Verificar que el archivo exista
        response = supabase.storage.from_('images').get_public_url(nombre_imagen)
        return response if response else url
    except Exception as e:
        logger.error(f"Error al obtener logo {nombre_imagen}: {e}")
        return ""

# ================================
# Panel: Ingreso de Datos con Edición
# ================================
def mostrar_ingreso_datos_kpis():
    st.markdown("<h1 class='header-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a Supabase.</div>", unsafe_allow_html=True)
        return

    fecha_seleccionada = st.date_input("Selecciona una fecha:", value=datetime.now().date())
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")

    # Cargar datos existentes
    datos_existentes = cargar_datos_fecha(fecha_str)
    trabajadores = obtener_trabajadores()
    if trabajadores.empty:
        st.warning("No hay trabajadores registrados.")
        return

    trabajadores_por_equipo = trabajadores.groupby('equipo')['nombre'].apply(list).to_dict()

    # Formulario de ingreso/editado
    with st.form("form_ingreso_kpis"):
        datos_guardar = {}
        for equipo, miembros in trabajadores_por_equipo.items():
            st.markdown(f"### 🧑‍💼 {equipo}")
            cols = st.columns(len(miembros) if len(miembros) <= 3 else 3)
            for idx, trabajador in enumerate(miembros):
                with cols[idx % len(cols)]:
                    # Cargar valores existentes si los hay
                    datos_trab = datos_existentes.get(trabajador, {})
                    cantidad = st.number_input(f"{trabajador} - Unidades", 
                                               value=float(datos_trab.get("cantidad", 0)), 
                                               min_value=0.0, step=1.0, key=f"{trabajador}_cantidad")
                    meta = st.number_input(f"Meta diaria", 
                                           value=float(datos_trab.get("meta", 50)), 
                                           min_value=0.0, step=1.0, key=f"{trabajador}_meta")
                    horas = st.number_input(f"Horas trabajadas", 
                                            value=float(datos_trab.get("horas_trabajo", 8)), 
                                            min_value=0.0, step=0.5, key=f"{trabajador}_horas")
                    comentario = st.text_input(f"Comentario", 
                                               value=datos_trab.get("comentario", ""), 
                                               key=f"{trabajador}_comentario")

                    eficiencia = (cantidad / meta * 100) if meta > 0 else 0
                    productividad = productividad_hora(cantidad, horas)

                    datos_guardar[trabajador] = {
                        "actividad": "General",
                        "cantidad": cantidad,
                        "meta": meta,
                        "eficiencia": eficiencia,
                        "productividad": productividad,
                        "comentario": comentario,
                        "meta_mensual": 0,
                        "horas_trabajo": horas,
                        "equipo": equipo
                    }

        submitted = st.form_submit_button("Guardar Datos")
        if submitted:
            if guardar_datos_db(fecha_str, datos_guardar):
                st.success("✅ Datos guardados correctamente.")
            else:
                st.error("❌ Error al guardar datos.")

# ================================
# Panel: Crear Guías (con logos desde Supabase)
# ================================
def mostrar_generacion_guias():
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    if supabase is None:
        st.error("Conexión a Supabase no disponible.")
        return

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(obtener_logo_url("Fashion.jpg"), width=150, caption="Fashion Club")
        st.image(obtener_logo_url("Tempo.jpg"), width=150, caption="Tempo")

    with col2:
        st.write("Genera guías de envío para tiendas online.")
        tienda = st.text_input("Nombre de la tienda")
        marca = st.selectbox("Empresa", ["Fashion", "Tempo"])
        url_pedido = st.text_area("URL del pedido")
        remitente = st.text_input("Remitente")

        if st.button("Generar Guía"):
            if guardar_guia(tienda, marca, url_pedido, remitente):
                st.success("✅ Guía generada y guardada.")
            else:
                st.error("❌ Error al generar guía.")

# ================================
# Panel: Dashboard de KPIs (con resumen y cubo de agua)
# ================================
def mostrar_dashboard_kpis():
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    if supabase is None:
        st.error("Sin conexión a Supabase.")
        return

    df = cargar_historico_db()
    if df.empty:
        st.info("No hay datos históricos disponibles.")
        return

    # Filtro de rango
    rango = st.selectbox("Seleccionar rango de tiempo:", ["Día", "Semana", "Mes", "Año"])
    hoy = datetime.now()
    if rango == "Día":
        fecha_fin = hoy.date()
        fecha_inicio = fecha_fin
    elif rango == "Semana":
        fecha_fin = hoy.date()
        fecha_inicio = (hoy - timedelta(days=6)).date()
    elif rango == "Mes":
        fecha_fin = hoy.date()
        fecha_inicio = date(hoy.year, hoy.month, 1)
    else:  # Año
        fecha_fin = hoy.date()
        fecha_inicio = date(hoy.year, 1, 1)

    df_filtrado = df[(df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)]

    if df_filtrado.empty:
        st.warning("No hay datos para el rango seleccionado.")
        return

    # Resumen ejecutivo
    st.markdown("### 📊 Resumen Ejecutivo")
    total_unidades = int(df_filtrado['cantidad'].sum())
    eficiencia_promedio = df_filtrado['eficiencia'].mean()
    colaboradores = df_filtrado['nombre'].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Unidades Totales", f"{total_unidades:,}")
    col2.metric("Eficiencia Promedio", f"{eficiencia_promedio:.1f}%")
    col3.metric("Colaboradores", colaboradores)

    # Gráfico de cubo de agua (acumulado por día del mes)
    df_mes = df[df['fecha'].dt.to_period('M') == pd.Period(hoy.strftime("%Y-%m"))]
    df_mes['dia'] = df_mes['fecha'].dt.day
    acumulado = df_mes.groupby('dia')['cantidad'].sum().cumsum().reset_index()

    fig = go.Figure(go.Waterfall(
        name="Progreso",
        orientation="v",
        x=acumulado['dia'],
        y=acumulado['cantidad'],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        text=[f"{val:,}" for val in acumulado['cantidad']],
        decreasing={"marker": {"color": "#4CAF50"}},
        increasing={"marker": {"color": "#2196F3"}},
        totals={"marker": {"color": "#FF9800"}}
    ))
    fig.update_layout(
        title=f"Progreso Mensual (Acumulado por día)",
        xaxis_title="Día del mes",
        yaxis_title="Unidades acumuladas",
        xaxis=dict(tickmode='linear')
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de rendimiento
    st.markdown("### 🏆 Rendimiento por Colaborador")
    resumen = df_filtrado.groupby('nombre').agg({
        'cantidad': 'sum',
        'eficiencia': 'mean',
        'horas_trabajo': 'sum'
    }).round(2)
    resumen.columns = ['Unidades', 'Eficiencia (%)', 'Horas']
    st.dataframe(resumen.style.format({"Eficiencia (%)": "{:.1f}%"}))

# ================================
# Otras funciones (sin cambios relevantes para las mejoras)
# ================================
def mostrar_analisis_historico_kpis():
    st.markdown("<h1 class='header-title animate-fade-in'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    df = cargar_historico_db()
    if df.empty:
        st.info("No hay datos históricos.")
        return
    st.dataframe(df)

def mostrar_gestion_trabajadores():
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    st.info("Funcionalidad básica de gestión.")

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    try:
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        }
        supabase.from_('guide_logs').insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Error al guardar guía: {e}")
        return False

# ================================
# Menú principal
# ================================
PAGES = {
    "Dashboard de KPIs": mostrar_dashboard_kpis,
    "Ingreso de Datos": mostrar_ingreso_datos_kpis,
    "Crear Guías": mostrar_generacion_guias,
    "Análisis Histórico": mostrar_analisis_historico_kpis,
    "Gestión de Trabajadores": mostrar_gestion_trabajadores
}

def main():
    st.set_page_config(page_title="Sistema de KPIs", layout="wide")
    st.markdown("""
        <style>
        .header-title { color: #1f77b4; font-size: 2.5em; font-weight: bold; }
        .section-title { color: #2c3e50; font-size: 1.5em; margin-top: 1em; }
        .error-box { background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 5px; }
        .warning-box { background-color: #fff8e1; color: #f57f17; padding: 10px; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("Menú")
    selection = st.sidebar.radio("Ir a", list(PAGES.keys()))

    page = PAGES[selection]
    page()

    # Footer
    st.markdown("""
        <div class="footer" style="text-align:center; margin-top: 3em; color: #7f8c8d;">
            Sistema de KPIs Aeropostale v2.1 | © 2025 Todos los derechos reservados.<br>
            Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com">Wilson Pérez</a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
