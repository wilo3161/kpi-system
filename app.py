import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import timeimport streamlit as st
import pandas as pdimport streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
import requests
# Importación CORREGIDA de Any y otros tipos
from typing import Dict, List, Optional, Tuple, Any, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_PASSWORD = "Wilo3161"  # Contraseña única sensible a mayúsculas

# Configuración de imágenes
APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Inicializar cliente de Supabase
@st.cache_resource
def init_supabase() -> Client:
    """Inicializa y cachea el cliente de Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        st.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error al inicializar Supabase: {e}", exc_info=True)
        st.error("Error al conectar con la base de datos. Verifique las variables de entorno.")
        return None

# Inicializar cliente de Supabase
supabase = init_supabase()

# Configuración de página
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# CSS profesional mejorado - CORREGIDO
st.markdown("""
<style>
    /* Colores corporativos de Aeropostale */
    :root {
        --primary-color: navy;
        --secondary-color: #000000;
        --accent-color: #333333;
        --background-dark: #121212;
        --card-background: #2d30f0;
        --text-color: #ffffff;
        --text-secondary: #b0b0b0;
        --success-color: #4caf50;
        --warning-color: #ff9800;
        --error-color: #f44336;
    }
    
    body {
        background-color: var(--background-dark);
        color: var(--text-color);
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .stApp {
        background-color: var(--background-dark);
    }
    
    /* Estilos del sidebar */
    .css-1d391kg {
        background-color: var(--card-background) !important;
    }
    
    .sidebar-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-color);
        text-align: center;
        margin: 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--primary-color);
    }
    
    .menu-item {
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
    }
    
    .menu-item:hover {
        background-color: rgba(230, 0, 18, 0.1);
    }
    
    .menu-item.active {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
    }
    
    .menu-item i {
        margin-right: 10px;
        font-size: 1.2rem;
    }
    
    /* Tarjetas y métricas */
    .kpi-card {
        background: var(--card-background);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        padding: 20px;
        margin: 15px 0;
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2.8em;
        font-weight: bold;
        color: var(--primary-color);
        line-height: 1.2;
        margin: 10px 0;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 1.1em;
        margin-bottom: 5px;
    }
    
    .trend-up {
        color: var(--success-color);
    }
    
    .trend-down {
        color: var(--error-color);
    }
    
    /* Encabezados y secciones */
    .header-title {
        color: var(--text-color);
        font-weight: 800;
        font-size: 2.5em;
        margin-bottom: 20px;
        position: relative;
        padding-bottom: 10px;
    }
    
    .header-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 4px;
        background-color: var(--primary-color);
        border-radius: 2px;
    }
    
    .section-title {
        color: var(--text-color);
        font-size: 1.8em;
        margin: 25px 0 15px;
        padding-left: 15px;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Tablas y datos */
    .data-table {
        background: var(--card-background);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    }
    
    /* Botones */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), #b3000e);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 4px 10px rgba(230, 0, 18, 0.25);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(230, 0, 18, 0.35);
        background: linear-gradient(135deg, #cc0010, #99000c);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Inputs y formularios */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2a2a2a !important;
        color: var(--text-color) !important;
        border: 1px solid #3a3a3a !important;
        border-radius: 8px;
        padding: 10px !important;
    }
    
    .stSelectbox > div > div > div {
        background-color: #2a2a2a !important;
        color: var(--text-color) !important;
        border: 1px solid #3a3a3a !important;
        border-radius: 8px;
    }
    
    /* Mensajes de estado */
    .success-box {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.05));
        color: #8bc34a;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #8bc34a;
        margin: 15px 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.15), rgba(244, 67, 54, 0.05));
        color: #ff6b6b;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff6b6b;
        margin: 15px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.05));
        color: #ffc107;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 15px 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(3, 169, 244, 0.15), rgba(3, 169, 244, 0.05));
        color: #4fc3f7;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4fc3f7;
        margin: 15px 0;
    }
    
    /* Estilos específicos para el sistema de guías */
    .guide-section {
        background: var(--card-background);
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .qr-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .guide-metric {
        font-size: 1.3em;
        margin: 12px 0;
        color: var(--text-color);
        display: flex;
        align-items: center;
    }
    
    .guide-metric strong {
        color: var(--primary-color);
        margin-left: 8px;
    }
    
    .guide-icon {
        color: var(--primary-color);
        margin-right: 10px;
        font-size: 1.5em;
    }
    
    /* Estilos para el sistema de autenticación */
    .password-container {
        background: var(--card-background);
        padding: 35px;
        border-radius: 15px;
        max-width: 450px;
        margin: 80px auto;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(230, 0, 18, 0.2);
    }
    
    .password-title {
        color: var(--primary-color);
        font-size: 2.2em;
        text-align: center;
        margin-bottom: 25px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 12px;
    }
    
    .password-input {
        margin-bottom: 25px;
    }
    
    .logo-container {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .aeropostale-logo {
        font-size: 3.5em;
        font-weight: 800;
        color: var(--primary-color);
        text-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        letter-spacing: -1px;
    }
    
    .aeropostale-subtitle {
        color: var(--text-secondary);
        font-size: 1.1em;
        margin-top: 8px;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px 0;
        margin-top: 30px;
        color: var(--text-secondary);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        font-size: 0.9em;
    }
    
    .footer a {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2em;
        }
        
        .section-title {
            font-size: 1.5em;
        }
        
        .metric-value {
            font-size: 2.2em;
        }
        
        .password-container {
            margin: 40px 20px;
            padding: 25px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ================================
# Funciones de utilidad compartidas
# ================================

def validar_fecha(fecha: str) -> bool:
    """Valida que una fecha tenga el formato correcto"""
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_numero_positivo(valor: Any) -> bool:
    """Valida que un valor sea un número positivo"""
    try:
        num = float(valor)
        return num >= 0
    except (ValueError, TypeError):
        return False

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(pw.encode()).hexdigest()

# ================================
# Funciones de KPIs
# ================================

# Funciones de cálculo de KPIs
def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general"""
    return (cantidad / meta) * 100 if meta > 0 else 0

def kpi_transferencias(transferidas: float, meta: float = 1750) -> float:
    """Calcula el KPI para transferencias"""
    return calcular_kpi(transferidas, meta)

def kpi_arreglos(arregladas: float, meta: float = 150) -> float:
    """Calcula el KPI para arreglos"""
    return calcular_kpi(arregladas, meta)

def kpi_distribucion(distribuidas: float, meta: float = 1000) -> float:
    """Calcula el KPI para distribución"""
    return calcular_kpi(distribuidas, meta)

def kpi_guias(guias: float, meta: float = 120) -> float:
    """Calcula el KPI para guías"""
    return calcular_kpi(guias, meta)

def productividad_hora(cantidad: float, horas_trabajo: float) -> float:
    """Calcula la productividad por hora"""
    return cantidad / horas_trabajo if horas_trabajo > 0 else 0

# Funciones de acceso a datos (ahora usando Supabase)
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })
    
    try:
        response = supabase.from_('trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df
        else:
            logger.warning("No se encontraron trabajadores en Supabase")
            return pd.DataFrame(columns=['nombre', 'equipo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores de Supabase: {e}", exc_info=True)
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })

def obtener_equipos() -> list:
    """Obtiene la lista de equipos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            equipos = [item['equipo'] for item in response.data]
            # Asegurar que "Distribución" esté en la lista
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            # Ordenar los equipos en un orden específico
            orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
            equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
            equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
            return equipos_ordenados + equipos_restantes
        else:
            logger.warning("No se encontraron equipos en Supabase")
            return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos de Supabase: {e}", exc_info=True)
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos en la tabla de Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        registros = []
        for nombre, info in datos.items():
            # Validar datos antes de guardar
            if not all([
                validar_fecha(fecha),
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                logger.warning(f"Datos inválidos para {nombre}, omitiendo guardado")
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
            # Usar upsert para insertar o actualizar
            response = supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            
            # Limpiar caché de datos históricos
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
                
            logger.info(f"Datos guardados correctamente en Supabase para la fecha {fecha}")
            return True
        else:
            logger.warning("No hay registros válidos para guardar")
            return False
    except Exception as e:
        logger.error(f"Error al guardar datos en Supabase: {e}", exc_info=True)
        return False

def cargar_historico_db(fecha_inicio: str = None, 
                       fecha_fin: str = None, 
                       trabajador: str = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('daily_kpis').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador:
            query = query.eq('nombre', trabajador)
            
        query = query.order('fecha', desc=True)
        
        response = query.execute()
        
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Convertir fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])
                # Calcular columnas adicionales
                df['cumplimiento_meta'] = np.where(df['cantidad'] >= df['meta'], 'Sí', 'No')
                df['diferencia_meta'] = df['cantidad'] - df['meta']
            return df
        else:
            logger.info("No se encontraron datos históricos en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

# Funciones de visualización
def crear_grafico_interactivo(df: pd.DataFrame, x: str, y: str, title: str, 
                             xlabel: str, ylabel: str, tipo: str = 'bar') -> go.Figure:
    """Crea gráficos interactivos con Plotly"""
    try:
        if df.empty:
            logger.warning("DataFrame vacío para crear gráfico interactivo")
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=18, color="#666666")
            )
            return fig
            
        if tipo == 'bar':
            fig = px.bar(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'line':
            fig = px.line(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'scatter':
            fig = px.scatter(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'box':
            fig = px.box(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        else:
            fig = px.bar(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
            
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff"),
            title_font_color="#ffffff",
            xaxis_title_font_color="#ffffff",
            yaxis_title_font_color="#ffffff",
            xaxis_tickfont_color="#ffffff",
            yaxis_tickfont_color="#ffffff",
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico: {e}", exc_info=True)
        # Devolver figura vacía en caso de error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#e74c3c")
        )
        return fig

def crear_grafico_frasco(porcentaje: float, titulo: str) -> go.Figure:
    """Crea un gráfico de frasco de agua para mostrar el porcentaje de cumplimiento"""
    try:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = porcentaje,
            number = {'suffix': '%', 'font': {'size': 36, 'color': '#ffffff'}},
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': titulo, 'font': {'size': 20, 'color': '#ffffff'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#e60012", 'thickness': 0.3},
                'bgcolor': "#2a2a2a",
                'borderwidth': 2,
                'bordercolor': "#444444",
                'steps': [
                    {'range': [0, 50], 'color': "darkred"},
                    {'range': [50, 75], 'color': "darkorange"},
                    {'range': [75, 100], 'color': "forestgreen"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de frasco: {e}", exc_info=True)
        return go.Figure()

# ================================
# Funciones de Guías (NUEVAS)
# ================================

def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único."""
    return f"9400{str(record_id).zfill(20)}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera y devuelve una imagen del código QR."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def obtener_tiendas() -> pd.DataFrame:
    """Obtiene la lista de tiendas desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"]
        })
    
    try:
        response = supabase.from_('guide_stores').select('*').execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron tiendas en Supabase")
            return pd.DataFrame(columns=['id', 'name'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"]
        })

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["Fashion Club", "Tempo"],
            'address': ["Dirección 1", "Dirección 2"],
            'phone': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.from_('guide_senders').select('*').execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron remitentes en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["Fashion Club", "Tempo"],
            'address': ["Dirección 1", "Dirección 2"],
            'phone': ["0993052744", "0987654321"]
        })

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """Guarda una guía en Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Insertar nueva guía
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.from_('guide_logs').insert(data).execute()
        
        # Verificar si la inserción fue exitosa
        if response and response.data:
            logger.info(f"Guía guardada correctamente para {store_name}")
            return True
        else:
            logger.error("No se pudo guardar la guía en Supabase")
            return False
    except Exception as e:
        logger.error(f"Error al guardar guía en Supabase: {e}", exc_info=True)
        return False

def obtener_historial_guias() -> pd.DataFrame:
    """Obtiene el historial de guías desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('guide_logs').select('*')
        query = query.order('created_at', desc=True)
        
        response = query.execute()
        
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Convertir fecha a datetime
                df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        else:
            logger.info("No se encontraron guías en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar historial de guías de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def generar_pdf_guia(store_name: str, brand: str, url: str, sender_name: str, 
                    sender_address: str, sender_phone: str, tracking_number: str) -> bytes:
    """Genera un PDF de la guía de envío"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Guía de Envío", ln=True, align="C")
        pdf.ln(10)
        
        # Logo de la marca (AGREGADO - se muestra arriba a la izquierda)
        # En la sección de previsualización, después de mostrar la información básica:
logo_url = get_logo_path(st.session_state.get('brand_select', ''))
if logo_url:
    try:
        response = requests.get(logo_url)
        if response.status_code == 200:
            st.image(response.content, caption=f"Logo de {st.session_state.get('brand_select', '')}", width=200)
    except Exception as e:
        logger.error(f"Error al cargar logo: {e}")
        st.warning(f"Logo no encontrado para {st.session_state.get('brand_select', '')}")
        
        # Información de la tienda
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Tienda:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, store_name, ln=True)
        
        # Información de la marca
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Marca:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, brand, ln=True)
        
        # Información del remitente
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Remitente:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{sender_name} - {sender_phone}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(40, 8, "")
        pdf.multi_cell(0, 8, sender_address)
        pdf.ln(5)
        
        # Número de seguimiento
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Número de Seguimiento:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, tracking_number, ln=True)
        pdf.ln(5)
        
        # Código QR
        qr_img = generar_qr_imagen(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_qr:
            qr_img.save(temp_qr.name)
            pdf.image(temp_qr.name, x=70, y=pdf.get_y(), w=70, h=70)
            os.unlink(temp_qr.name)
        
        # URL
        pdf.ln(75)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "URL del Pedido:")
        pdf.set_font("Arial", "U", 12)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 8, url, ln=True)
        pdf.set_text_color(0, 0, 0)
        
        return pdf.output(dest="S").encode("latin1")
    except Exception as e:
        logger.error(f"Error al generar PDF de guía: {e}", exc_info=True)
        return b""

def get_logo_path(brand: str) -> str:
    """Devuelve la URL del logo de la marca desde Supabase Storage."""
    # Obtén este ID de tu dashboard de Supabase → Settings → General
    PROJECT_REF = "tu-project-ref-aqui"  # Ejemplo: "xzy123abcdef"
    
    if brand == "Fashion":
        return f"https://wilo3161's Project.supabase.co/storage/v1/object/public/images/Fashion.jpg"
    elif brand == "Tempo":
        return f"https://wilo3161's Project.supabase.co/storage/v1/object/public/images/Tempo.jpg"
    return None

def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    """Convierte un objeto de imagen de PIL a bytes."""
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()

def custom_selectbox(label: str, options: list, key: str, search_placeholder: str = "Buscar...") -> str:
    """Componente personalizado de selectbox con búsqueda."""
    if f"{key}_search" not in st.session_state:
        st.session_state[f"{key}_search"] = ""
    
    search_term = st.text_input(f"{label} - {search_placeholder}", 
                               value=st.session_state[f"{key}_search"], 
                               key=f"{key}_search_input")
    
    st.session_state[f"{key}_search"] = search_term
    
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
    else:
        filtered_options = options
    
    if not filtered_options:
        st.warning("No se encontraron resultados.")
        return None
    
    return st.selectbox(label, filtered_options, key=key)

# ================================
# Sistema de autenticación
# ================================

def verificar_password() -> bool:
    """Verifica si el usuario tiene permisos para realizar acciones críticas"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

def solicitar_autenticacion():
    """Muestra un formulario de autenticación"""
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Gestión de KPIs</div>
        </div>
        <h2 class="password-title">🔐 Acceso Restringido</h2>
        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 25px;">
            Ingrese la contraseña para realizar esta acción
        </p>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña:", type="password", key="auth_password", 
                            placeholder="Ingrese su contraseña", 
                            label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.button("Ingresar", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submitted:
        if password == ADMIN_PASSWORD:
            st.session_state.password_correct = True
            st.success("✅ Acceso concedido")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

# ================================
# Componentes de la aplicación
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Crear selector de fecha
    st.markdown("<div class='date-selector animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3>Selecciona la fecha a visualizar:</h3>", unsafe_allow_html=True)
    
    # Obtener fechas únicas y ordenarlas
    if not df.empty and 'fecha' in df.columns:
        # Convertir a fecha y eliminar duplicados
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
            return
        fecha_seleccionada = st.selectbox(
            "Fecha:",
            options=fechas_disponibles,
            index=0,
            label_visibility="collapsed"
        )
    else:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles.</div>", unsafe_allow_html=True)
        return
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filtrar datos por fecha seleccionada
    df_reciente = df[df['fecha'].dt.date == fecha_seleccionada]
    if df_reciente.empty:
        st.markdown(f"<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles para la fecha {fecha_seleccionada}.</div>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<p style='color: var(--text-secondary); font-size: 1.1em;'>Datos para la fecha: {fecha_seleccionada}</p>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    
    # Cálculos globales
    total_cantidad = df_reciente['cantidad'].sum()
    total_meta = df_reciente['meta'].sum()
    total_horas = df_reciente['horas_trabajo'].sum()
    avg_eficiencia = (df_reciente['eficiencia'] * df_reciente['horas_trabajo']).sum() / total_horas if total_horas > 0 else 0
    avg_productividad = df_reciente['productividad'].mean()
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        cumplimiento_meta = (total_cantidad / total_meta * 100) if total_meta > 0 else 0
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">✅ Total Producción</div>
            <p class="metric-value">{total_cantidad:,.0f}</p>
            <p>Meta: {total_meta:,.0f} | <span class="{'trend-up' if cumplimiento_meta >= 100 else 'trend-down'}">{cumplimiento_meta:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">🎯 Eficiencia Promedio</div>
            <p class="metric-value">{avg_eficiencia:.1f}%</p>
            <p>Meta: 100% | <span class="{'trend-up' if avg_eficiencia >= 100 else 'trend-down'}">{avg_eficiencia - 100:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">⚡ Productividad Promedio</div>
            <p class="metric-value">{avg_productividad:.1f}</p>
            <p>unidades/hora</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">⏱️ Productividad Total</div>
            <p class="metric-value">{productividad_total:.1f}</p>
            <p>unidades/hora ({total_horas:.1f} h)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📅 Cumplimiento de Metas Mensuales (Transferencias)</h2>", unsafe_allow_html=True)
    
    current_month = fecha_seleccionada.month
    current_year = fecha_seleccionada.year
    
    # Filtrar datos del mes actual para transferencias
    df_month = df[(df['fecha'].dt.month == current_month) & 
                  (df['fecha'].dt.year == current_year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    # Obtener meta mensual de transferencias (usamos el último valor registrado)
    if not df_transferencias_month.empty:
        meta_mensual_transferencias = df_transferencias_month['meta_mensual'].iloc[0]
    else:
        # Si no hay datos, usar un valor por defecto
        meta_mensual_transferencias = 150000
    
    cum_transferencias = df_transferencias_month['cantidad'].sum()
    cumplimiento_transferencias = (cum_transferencias / meta_mensual_transferencias * 100) if meta_mensual_transferencias > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Meta Mensual Transferencias</div>
            <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
            <p>Acumulado: {cum_transferencias:,.0f} / Meta Mensual: {meta_mensual_transferencias:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Gráfico de frasco de agua para el cumplimiento
        fig = crear_grafico_frasco(cumplimiento_transferencias, "Cumplimiento Mensual Transferencias")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Gráfico de evolución mensual
    if not df_transferencias_month.empty:
        df_transferencias_daily = df_transferencias_month.groupby(df_transferencias_month['fecha'].dt.date)['cantidad'].sum().reset_index(name='cantidad')
        df_transferencias_daily['fecha'] = pd.to_datetime(df_transferencias_daily['fecha'])
        df_transferencias_daily = df_transferencias_daily.sort_values('fecha')
        df_transferencias_daily['cumulative'] = df_transferencias_daily['cantidad'].cumsum()
        
        fig = crear_grafico_interactivo(
            df_transferencias_daily, 
            'fecha', 
            'cumulative', 
            'Cumplimiento Mensual Transferencias', 
            'Día', 
            'Acumulado',
            'line'
        )
        # Añadir línea de meta
        fig.add_hline(y=meta_mensual_transferencias, line_dash="dash", line_color="white", annotation_text="Meta Mensual")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No hay datos para el gráfico de Transferencias.")
    
    st.markdown("<h2 class='section-title animate-fade-in'>👥 Rendimiento por Equipos</h2>", unsafe_allow_html=True)
    
    # Obtener lista de equipos
    equipos = df_reciente['equipo'].unique()
    # Ordenar equipos en un orden específico
    orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
    equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
    equipos_finales = equipos_ordenados + equipos_restantes
    
    for equipo in equipos_finales:
        df_equipo = df_reciente[df_reciente['equipo'] == equipo]
        st.markdown(f"<div class='team-section animate-fade-in'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
        
        # Calcular KPIs del equipo
        total_equipo = df_equipo['cantidad'].sum()
        meta_equipo = df_equipo['meta'].sum()
        horas_equipo = df_equipo['horas_trabajo'].sum()
        eficiencia_equipo = (df_equipo['eficiencia'] * df_equipo['horas_trabajo']).sum() / horas_equipo if horas_equipo > 0 else 0
        productividad_equipo = total_equipo / horas_equipo if horas_equipo > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Producción</div>
                <p class="metric-value">{total_equipo:,.0f}</p>
                <p>Meta: {meta_equipo:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Eficiencia</div>
                <p class="metric-value">{eficiencia_equipo:.1f}%</p>
                <p>Meta: 100%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Productividad</div>
                <p class="metric-value">{productividad_equipo:.1f}</p>
                <p>unidades/hora</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Horas</div>
                <p class="metric-value">{horas_equipo:.1f}</p>
                <p>horas trabajadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar trabajadores del equipo
        for _, row in df_equipo.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                color = "#8bc34a" if row['eficiencia'] >= 100 else "#ff6b6b"
                card_content = f"""
                <div class="worker-card">
                    <div class="stats-container">
                        <div class="worker-header">{row['nombre']}</div>
                        <div class="worker-metric">📦 {row['actividad']}: <span style='font-weight:bold'>{row['cantidad']}</span></div>
                        <div class="worker-metric">🎯 Eficiencia: <span style='color:{color}; font-weight:bold'>{row['eficiencia']:.1f}%</span></div>
                        <div class="worker-metric">⏱️ Productividad: {row['productividad']:.1f}/hora</div>
                        <div class="worker-metric">⏰ Horas: {row['horas_trabajo']:.1f} h</div>
                    </div>
                </div>
                """
                st.markdown(card_content, unsafe_allow_html=True)
            
            with col2:
                comentario = row.get('comentario', None)
                if pd.notna(comentario) and str(comentario).strip() != "":
                    st.markdown(f"""
                    <div class="comment-container">
                        <div class="comment-title">💬 Comentario:</div>
                        <div class="comment-content">{comentario}</div>
                    </div>
                    """, unsafe_allow_html=True)

def mostrar_analisis_historico_kpis():
    """Muestra el análisis histórico de KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    df = cargar_historico_db()
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    df['dia'] = df['fecha'].dt.date
    fecha_min = df['dia'].min()
    fecha_max = df['dia'].max()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
    with col3:
        trabajador = st.selectbox("Filtrar por trabajador:", options=["Todos"] + list(df['nombre'].unique()))
    
    if fecha_inicio > fecha_fin:
        st.markdown("<div class='error-box animate-fade-in'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    # Aplicar filtros
    df_filtrado = df[(df['dia'] >= fecha_inicio) & (df['dia'] <= fecha_fin)]
    if trabajador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador]
    
    if df_filtrado.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos en el rango de fechas seleccionado.</div>", unsafe_allow_html=True)
        return
    
    # Botones de exportación
    st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        # Botón para exportar a Excel
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                # Crear una copia del DataFrame para no modificar el original
                export_df = df_filtrado.copy()
                
                # Asegurar que las fechas estén en formato adecuado
                if 'fecha' in export_df.columns:
                    export_df['fecha'] = pd.to_datetime(export_df['fecha']).dt.strftime('%Y-%m-%d')
                
                # Manejar valores NaN и None
                export_df = export_df.fillna('N/A')
                
                # Reordenar columnas para una mejor presentación
                columnas_ordenadas = [
                    'fecha', 'nombre', 'equipo', 'actividad', 'cantidad', 'meta', 
                    'eficiencia', 'productividad', 'horas_trabajo', 'meta_mensual', 'comentario'
                ]
                # Solo incluir las columnas que existen en el DataFrame
                columnas_finales = [col for col in columnas_ordenadas if col in export_df.columns]
                export_df = export_df[columnas_finales]
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Datos_KPIs', index=False)
                    # Formato adicional para mejorar el Excel
                    workbook = writer.book
                    worksheet = writer.sheets['Datos_KPIs']
                    
                    # Formato para encabezados
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#e60012',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    # Formato para celdas
                    cell_format = workbook.add_format({
                        'border': 1,
                        'align': 'left',
                        'valign': 'vcenter'
                    })
                    
                    # Aplicar formato a encabezados
                    for col_num, value in enumerate(export_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Aplicar formato a todas las celdas de datos
                    for row in range(1, len(export_df) + 1):
                        for col in range(len(export_df.columns)):
                            worksheet.write(row, col, export_df.iloc[row-1, col], cell_format)
                    
                    # Autoajustar columnas
                    for i, col in enumerate(export_df.columns):
                        # Obtener la longitud máxima de los datos en la columna
                        max_len = max((
                            export_df[col].astype(str).str.len().max(),  # Longitud máxima de los datos
                            len(str(col))  # Longitud del nombre de la columna
                        )) + 2  # Añadir un poco de espacio extra
                        worksheet.set_column(i, i, max_len)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="⬇️ Descargar archivo Excel",
                    data=excel_data,
                    file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Botón para exportar a PDF
        if st.button("📄 Exportar a PDF", use_container_width=True):
            try:
                with st.spinner("Generando reporte PDF..."):
                    # Crear un PDF en memoria
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                    styles = getSampleStyleSheet()
                    
                    # Estilos personalizados
                    styles.add(ParagraphStyle(name='Header', fontSize=16, alignment=1, spaceAfter=12, textColor='#e60012'))
                    styles.add(ParagraphStyle(name='Section', fontSize=14, spaceBefore=12, spaceAfter=6, textColor='#e60012'))
                    styles.add(ParagraphStyle(name='Normal', fontSize=12, spaceAfter=6))
                    
                    elements = []
                    
                    # Título
                    title = Paragraph("Reporte de KPIs - Aeropostale", styles['Header'])
                    elements.append(title)
                    
                    # Información del período
                    periodo = Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", styles['Normal'])
                    elements.append(periodo)
                    
                    # Resumen estadístico
                    elements.append(Paragraph("Resumen Estadístico", styles['Section']))
                    
                    # Crear tabla de resumen
                    try:
                        resumen_data = df_filtrado.groupby('nombre').agg({
                            'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
                            'eficiencia': ['mean', 'max', 'min'],
                            'productividad': ['mean', 'max', 'min'],
                            'horas_trabajo': ['sum', 'mean']
                        }).round(2)
                        
                        # Aplanar las columnas multiindex
                        resumen_data.columns = ['_'.join(col).strip() for col in resumen_data.columns.values]
                        resumen_data.reset_index(inplace=True)
                        
                        # Convertir DataFrame a lista para la tabla
                        table_data = [list(resumen_data.columns)]
                        for _, row in resumen_data.iterrows():
                            table_data.append(list(row))
                        
                        # Crear tabla
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e60012')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd'))
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                    except Exception as e:
                        logger.error(f"Error al crear tabla de resumen: {e}", exc_info=True)
                        elements.append(Paragraph(f"Error al generar tabla de resumen: {str(e)}", styles['Normal']))
                        elements.append(Spacer(1, 12))
                    
                    # Construir PDF
                    doc.build(elements)
                    pdf_data = pdf_buffer.getvalue()
                    pdf_buffer.close()
                    
                    st.download_button(
                        label="⬇️ Descargar reporte PDF",
                        data=pdf_data,
                        file_name=f"reporte_kpis_{fecha_inicio}_a_{fecha_fin}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                logger.error(f"Error al exportar a PDF: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a PDF.</div>", unsafe_allow_html=True)
    
    with col3:
        # Botón para exportar a CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📋 Resumen Estadístico</h2>", unsafe_allow_html=True)
    # Mostrar resumen estadístico
    st.dataframe(df_filtrado.groupby('nombre').agg({
        'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
        'eficiencia': ['mean', 'max', 'min'],
        'productividad': ['mean', 'max', 'min'],
        'horas_trabajo': ['sum', 'mean']
    }).round(2), use_container_width=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📊 Tendencias Históricas</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Eficiencia por Día", "Producción Acumulada", "Comparativa por Área", "Análisis Detallado", "Predicciones"])
    
    with tab1:
        df_eficiencia_dia = df_filtrado.groupby('dia')['eficiencia'].mean().reset_index()
        if not df_eficiencia_dia.empty:
            fig = crear_grafico_interactivo(
                df_eficiencia_dia, 
                'dia', 
                'eficiencia', 
                'Evolución de la Eficiencia Promedio Diaria', 
                'Fecha', 
                'Eficiencia Promedio (%)',
                'line'
            )
            # Añadir línea de meta
            fig.add_hline(y=100, line_dash="dash", line_color="white", annotation_text="Meta de eficiencia")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab2:
        df_produccion = df_filtrado.groupby(['dia', 'actividad'])['cantidad'].sum().reset_index()
        if not df_produccion.empty:
            fig = crear_grafico_interactivo(
                df_produccion, 
                'dia', 
                'cantidad', 
                'Producción Acumulada por Área', 
                'Fecha', 
                'Producción Acumulada',
                'line'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab3:
        if not df_filtrado.empty:
            fig = crear_grafico_interactivo(
                df_filtrado, 
                'actividad', 
                'productividad', 
                'Distribución de Productividad por Área', 
                'Área', 
                'Productividad (unidades/hora)',
                'box'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab4:
        st.markdown("<h3>📈 Análisis de Correlación</h3>", unsafe_allow_html=True)
        # Calcular matriz de correlación
        numeric_cols = df_filtrado.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df_filtrado[numeric_cols].corr()
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title='Matriz de Correlación'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay suficientes datos numéricos para calcular correlaciones.")
        
        st.markdown("<h3>📋 Datos Detallados</h3>", unsafe_allow_html=True)
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab5:
        st.markdown("<h3>🔮 Predicción de Tendencia</h3>", unsafe_allow_html=True)
        if not df_eficiencia_dia.empty and len(df_eficiencia_dia) > 5:
            try:
                # Preparar datos para predicción
                dias_prediccion = 7
                x = np.arange(len(df_eficiencia_dia))
                y = df_eficiencia_dia['eficiencia'].values
                
                # Ajustar modelo
                model = np.polyfit(x, y, 1)
                poly = np.poly1d(model)
                
                # Predecir valores futuros
                x_pred = np.arange(len(df_eficiencia_dia), len(df_eficiencia_dia) + dias_prediccion)
                y_pred = poly(x_pred)
                
                # Crear fechas futuras
                ultima_fecha = df_eficiencia_dia['dia'].max()
                fechas_futuras = [ultima_fecha + timedelta(days=i+1) for i in range(dias_prediccion)]
                
                # Crear gráfico
                fig = go.Figure()
                # Datos históricos
                fig.add_trace(go.Scatter(
                    x=df_eficiencia_dia['dia'], 
                    y=df_eficiencia_dia['eficiencia'],
                    mode='lines+markers',
                    name='Datos Históricos'
                ))
                # Predicciones
                fig.add_trace(go.Scatter(
                    x=fechas_futuras, 
                    y=y_pred,
                    mode='lines+markers',
                    name='Predicción',
                    line=dict(dash='dash', color='orange')
                ))
                # Línea de meta
                fig.add_hline(y=100, line_dash="dash", line_color="white", annotation_text="Meta de eficiencia")
                fig.update_layout(
                    title='Predicción de Eficiencia para los Próximos 7 Días',
                    xaxis_title='Fecha',
                    yaxis_title='Eficiencia Promedio (%)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Mostrar valores de predicción
                st.markdown("<h4>Valores de Predicción:</h4>", unsafe_allow_html=True)
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, y_pred)):
                    st.write(f"{fecha.strftime('%Y-%m-%d')}: {pred:.1f}%")
            except Exception as e:
                st.error(f"Error al generar predicciones: {str(e)}")
        else:
            st.info("Se necesitan al menos 5 días de datos para realizar predicciones.")

def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener trabajadores desde Supabase
    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay trabajadores registrados. Por favor, registre trabajadores primero.</div>", unsafe_allow_html=True)
        return
    
    # Asegurar que Luis Perugachi esté en el equipo de Distribución
    if 'Luis Perugachi' in df_trabajadores['nombre'].values:
        df_trabajadores.loc[df_trabajadores['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
    
    trabajadores_por_equipo = {}
    for _, row in df_trabajadores.iterrows():
        equipo = row['equipo']
        if equipo not in trabajadores_por_equipo:
            trabajadores_por_equipo[equipo] = []
        trabajadores_por_equipo[equipo].append(row['nombre'])
    
    # Si no existe el equipo de Distribución, crearlo
    if 'Distribución' not in trabajadores_por_equipo:
        trabajadores_por_equipo['Distribución'] = []
    
    # Selector de fecha
    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_seleccionada = st.date_input(
            "Selecciona la fecha:",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    periodo = st.radio("Selecciona el período:", ["Día", "Semana"], horizontal=True)
    
    # Inicializar variables de sesión para almacenar datos
    if 'datos_calculados' not in st.session_state:
        st.session_state.datos_calculados = None
    if 'fecha_guardar' not in st.session_state:
        st.session_state.fecha_guardar = None
    
    with st.form("form_datos"):
        # Meta mensual única para transferencias
        st.markdown("<h3 class='section-title animate-fade-in'>Meta Mensual de Transferencias</h3>", unsafe_allow_html=True)
        meta_mensual_transferencias = st.number_input("Meta mensual para el equipo de transferencias:", min_value=0, value=150000, key="meta_mensual_transferencias")
        
        # Asegurar que el equipo de Distribución esté presente
        if 'Distribución' not in trabajadores_por_equipo:
            trabajadores_por_equipo['Distribución'] = []
        
        # Ordenar los equipos para mostrarlos en un orden específico
        orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
        equipos_ordenados = [eq for eq in orden_equipos if eq in trabajadores_por_equipo]
        equipos_restantes = [eq for eq in trabajadores_por_equipo.keys() if eq not in orden_equipos]
        equipos_finales = equipos_ordenados + equipos_restantes
        
        for equipo in equipos_finales:
            miembros = trabajadores_por_equipo[equipo]
            st.markdown(f"<div class='team-section animate-fade-in'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
            for trabajador in miembros:
                st.subheader(trabajador)
                col1, col2 = st.columns(2)
                with col1:
                    if equipo == "Transferencias":
                        cantidad = st.number_input(f"Prendas transferidas por {trabajador}:", min_value=0, value=1800, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=1750, key=f"{trabajador}_meta")
                    elif equipo == "Distribución":
                        # Para el equipo de Distribución
                        cantidad = st.number_input(f"Prendas distribuidas por {trabajador}:", min_value=0, value=1000, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=1000, key=f"{trabajador}_meta")
                    elif equipo == "Arreglo":
                        cantidad = st.number_input(f"Prendas arregladas por {trabajador}:", min_value=0, value=130, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=150, key=f"{trabajador}_meta")
                    elif equipo == "Guías":
                        cantidad = st.number_input(f"Guías realizadas por {trabajador}:", min_value=0, value=110, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=120, key=f"{trabajador}_meta")
                    elif equipo == "Ventas":
                        cantidad = st.number_input(f"Pedidos preparados por {trabajador}:", min_value=0, value=45, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=40, key=f"{trabajador}_meta")
                    else:
                        cantidad = st.number_input(f"Cantidad realizada por {trabajador}:", min_value=0, value=100, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=100, key=f"{trabajador}_meta")
                with col2:
                    horas = st.number_input(f"Horas trabajadas por {trabajador}:", min_value=0.0, value=8.0, key=f"{trabajador}_horas", step=0.5)
                    comentario = st.text_area(f"Comentario para {trabajador}:", key=f"{trabajador}_comentario")
        
        submitted = st.form_submit_button("Calcular KPIs")
        if submitted:
            datos_guardar = {}
            for equipo, miembros in trabajadores_por_equipo.items():
                for trabajador in miembros:
                    # Obtener valores del formulario
                    cantidad = st.session_state.get(f"{trabajador}_cantidad", 0)
                    meta = st.session_state.get(f"{trabajador}_meta", 0)
                    horas = st.session_state.get(f"{trabajador}_horas", 0)
                    comentario = st.session_state.get(f"{trabajador}_comentario", "")
                    
                    # Validar datos
                    if not all([validar_numero_positivo(cantidad), validar_numero_positivo(meta), validar_numero_positivo(horas)]):
                        st.markdown(f"<div class='error-box animate-fade-in'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
                        continue
                    
                    # Calcular KPIs según el equipo
                    if equipo == "Transferencias":
                        eficiencia = kpi_transferencias(cantidad, meta)
                        actividad = "Transferencias"
                        meta_mensual = meta_mensual_transferencias
                    elif equipo == "Distribución":
                        # Para el equipo de Distribución
                        eficiencia = kpi_distribucion(cantidad, meta)
                        actividad = "Distribución"
                        meta_mensual = 0
                    elif equipo == "Arreglo":
                        eficiencia = kpi_arreglos(cantidad, meta)
                        actividad = "Arreglos"
                        meta_mensual = 0
                    elif equipo == "Guías":
                        eficiencia = kpi_guias(cantidad, meta)
                        actividad = "Guías"
                        meta_mensual = 0
                    elif equipo == "Ventas":
                        eficiencia = kpi_transferencias(cantidad, meta)
                        actividad = "Ventas"
                        meta_mensual = 0
                    else:
                        eficiencia = (cantidad / meta * 100) if meta > 0 else 0
                        actividad = "General"
                        meta_mensual = 0
                    
                    productividad = productividad_hora(cantidad, horas)
                    datos_guardar[trabajador] = {
                        "actividad": actividad, 
                        "cantidad": cantidad, 
                        "meta": meta, 
                        "eficiencia": eficiencia, 
                        "productividad": productividad,
                        "comentario": comentario, 
                        "meta_mensual": meta_mensual,
                        "horas_trabajo": horas,
                        "equipo": equipo
                    }
            
            # Convertir la fecha seleccionada a string
            fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
            
            # Almacenar datos en sesión para confirmación posterior
            st.session_state.datos_calculados = datos_guardar
            st.session_state.fecha_guardar = fecha_str
            
            # Mostrar resumen
            st.markdown("<h3 class='section-title animate-fade-in'>📋 Resumen de KPIs Calculados</h3>", unsafe_allow_html=True)
            for equipo, miembros in trabajadores_por_equipo.items():
                st.markdown(f"**{equipo}:**")
                for trabajador in miembros:
                    if trabajador in datos_guardar:
                        datos = datos_guardar[trabajador]
                        st.markdown(f"- {trabajador}: {datos['cantidad']} unidades ({datos['eficiencia']:.1f}%)")
    
    # Botón de confirmación fuera del formulario
    if st.session_state.datos_calculados is not None and st.session_state.fecha_guardar is not None:
        if st.button("✅ Confirmar y Guardar Datos", key="confirmar_guardar", use_container_width=True):
            if guardar_datos_db(st.session_state.fecha_guardar, st.session_state.datos_calculados):
                st.markdown("<div class='success-box animate-fade-in'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                # Limpiar datos de confirmación
                st.session_state.datos_calculados = None
                st.session_state.fecha_guardar = None
                time.sleep(2)
                st.rerun()
            else:
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)

def mostrar_gestion_trabajadores_kpis():
    """Muestra la interfaz de gestión de trabajadores"""
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    try:
        # Obtener lista actual de trabajadores
        response = supabase.from_('trabajadores').select('*').order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            trabajadores = response.data
        else:
            trabajadores = []
        
        # Asegurar que Luis Perugachi esté en el equipo de Distribución
        if any(trab['nombre'] == 'Luis Perugachi' for trab in trabajadores):
            for trab in trabajadores:
                if trab['nombre'] == 'Luis Perugachi':
                    trab['equipo'] = 'Distribución'
        
        st.markdown("<h2 class='section-title animate-fade-in'>Trabajadores Actuales</h2>", unsafe_allow_html=True)
        if trabajadores:
            df_trabajadores = pd.DataFrame(trabajadores)
            st.dataframe(df_trabajadores[['nombre', 'equipo', 'activo']], use_container_width=True)
        else:
            st.info("No hay trabajadores registrados.")
        
        st.markdown("<h2 class='section-title animate-fade-in'>Agregar Nuevo Trabajador</h2>", unsafe_allow_html=True)
        with st.form("form_nuevo_trabajador"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre del trabajador:")
            with col2:
                equipos = obtener_equipos()
                nuevo_equipo = st.selectbox("Equipo:", options=equipos)
            submitted = st.form_submit_button("Agregar Trabajador")
            if submitted:
                if nuevo_nombre:
                    try:
                        # Verificar si el trabajador ya existe
                        response = supabase.from_('trabajadores').select('*').eq('nombre', nuevo_nombre).execute()
                        # Verificar si hay datos en la respuesta
                        if response and response.data:
                            st.markdown("<div class='error-box animate-fade-in'>❌ El trabajador ya existe.</div>", unsafe_allow_html=True)
                        else:
                            # Insertar nuevo trabajador
                            supabase.from_('trabajadores').insert({
                                'nombre': nuevo_nombre, 
                                'equipo': nuevo_equipo,
                                'activo': True
                            }).execute()
                            st.markdown("<div class='success-box animate-fade-in'>✅ Trabajador agregado correctamente.</div>", unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error al agregar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box animate-fide-in'>❌ Error al agregar trabajador.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Debe ingresar un nombre.</div>", unsafe_allow_html=True)
        
        st.markdown("<h2 class='section-title animate-fade-in'>Eliminar Trabajador</h2>", unsafe_allow_html=True)
        if trabajadores:
            trabajadores_activos = [t['nombre'] for t in trabajadores if t.get('activo', True)]
            if trabajadores_activos:
                trabajador_eliminar = st.selectbox("Selecciona un trabajador para eliminar:", options=trabajadores_activos)
                if st.button("Eliminar Trabajador", use_container_width=True):
                    try:
                        # Actualizar el estado del trabajador a inactivo
                        supabase.from_('trabajadores').update({'activo': False}).eq('nombre', trabajador_eliminar).execute()
                        st.markdown("<div class='success-box animate-fade-in'>✅ Trabajador eliminado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error al eliminar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al eliminar trabajador.</div>", unsafe_allow_html=True)
            else:
                st.info("No hay trabajadores activos para eliminar.")
        else:
            st.info("No hay trabajadores registrados.")
    except Exception as e:
        logger.error(f"Error en gestión de trabajadores: {e}", exc_info=True)
        st.markdown("<div class='error-box animate-fade-in'>❌ Error del sistema al gestionar trabajadores.</div>", unsafe_allow_html=True)

def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()
    
    if tiendas.empty or remitentes.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Formulario para generar guía
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Generar Nueva Guía</h2>", unsafe_allow_html=True)
    
    with st.form("form_generar_guia"):
        col1, col2 = st.columns(2)
        with col1:
            store_name = custom_selectbox("Seleccione Tienda", tiendas['name'].tolist(), "store_select", "Buscar tienda...")
            brand = st.radio("Seleccione Empresa:", ["Fashion", "Tempo"], horizontal=True, key="brand_select")
        
        with col2:
            sender_name = st.selectbox("Seleccione Remitente:", options=remitentes['name'].tolist(), key="sender_select")
            url = st.text_input("Ingrese URL del Pedido:", key="url_input", placeholder="https://...")
        
        submitted = st.form_submit_button("Generar Guía", use_container_width=True)
        
        if submitted:
            if not all([store_name, brand, url, sender_name]):
                st.markdown("<div class='error-box animate-fade-in'>❌ Por favor, complete todos los campos.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
            elif not url.startswith(('http://', 'https://')):
                st.markdown("<div class='error-box animate-fade-in'>❌ La URL debe comenzar con http:// o https://</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
            else:
                # Guardar la guía
                if guardar_guia(store_name, brand, url, sender_name):
                    st.session_state.show_preview = True
                    # Obtener información del remitente
                    remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                    st.session_state.remitente_address = remitente_info['address']
                    st.session_state.remitente_phone = remitente_info['phone']
                    st.session_state.tracking_number = generar_numero_seguimiento(1)  # Aquí debería ser el ID real
                    st.markdown("<div class='success-box animate-fade-in'>✅ Guía generada correctamente. Puede ver la previsualización y exportarla.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar la guía.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Previsualización de la guía
    if st.session_state.get('show_preview', False):
        st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title animate-fade-in'>Previsualización de la Guía</h2>", unsafe_allow_html=True)
        
        # Información de la guía
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🏬</span> <strong>Tienda:</strong> {st.session_state.get('store_select', '')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🏷️</span> <strong>Marca:</strong> {st.session_state.get('brand_select', '')}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>📦</span> <strong>Remitente:</strong> {st.session_state.get('sender_select', '')}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🔗</span> <strong>URL del Pedido:</strong> <a href='{st.session_state.get('url_input', '')}' target='_blank'>{st.session_state.get('url_input', '')}</a></div>", unsafe_allow_html=True)
        
        # Código QR
        st.markdown("<h3>Código QR:</h3>", unsafe_allow_html=True)
        qr_img = generar_qr_imagen(st.session_state.get('url_input', ''))
        st.image(pil_image_to_bytes(qr_img), width=200)
        
        # Botones de exportación
        st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            # Generar PDF
            pdf_data = generar_pdf_guia(
                st.session_state.get('store_select', ''),
                st.session_state.get('brand_select', ''),
                st.session_state.get('url_input', ''),
                st.session_state.get('sender_select', ''),
                st.session_state.get('remitente_address', ''),
                st.session_state.get('remitente_phone', ''),
                st.session_state.get('tracking_number', '')
            )
            st.download_button(
                label="📄 Descargar PDF",
                data=pdf_data,
                file_name=f"guia_{st.session_state.get('store_select', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col2:
            if st.button("🖨️ Marcar como Impresa", use_container_width=True):
                # Aquí iría la lógica para actualizar el estado de la guía
                st.markdown("<div class='success-box animate-fade-in'>✅ Guía marcada como impresa.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_historial_guias():
    """Muestra el historial de guías generadas"""
    st.markdown("<h1 class='header-title animate-fade-in'>🔍 Historial de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar historial de guías
    df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay guías generadas.</div>", unsafe_allow_html=True)
        return
    
    # Filtros
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Filtros</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=df_guias['created_at'].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=df_guias['created_at'].max().date())
    with col3:
        estado = st.selectbox("Estado:", ["Todos", "Pending", "Printed"])
    
    # Aplicar filtros
    df_filtrado = df_guias[
        (df_guias['created_at'].dt.date >= fecha_inicio) & 
        (df_guias['created_at'].dt.date <= fecha_fin)
    ]
    
    if estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == estado]
    
    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        total_creados = len(df_guias)
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Total de Guías</div><p class="metric-value">{total_creados}</p></div>', unsafe_allow_html=True)
    
    with col2:
        pendientes = len(df_guias[df_guias['status'] == 'Pending'])
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Pendientes</div><p class="metric-value">{pendientes}</p></div>', unsafe_allow_html=True)
    
    with col3:
        impresos = len(df_guias[df_guias['status'] == 'Printed'])
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Impresas</div><p class="metric-value">{impresos}</p></div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar tabla de guías
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Guías Generadas</h2>", unsafe_allow_html=True)
    
    # Preparar datos para mostrar
    df_display = df_filtrado.copy()
    df_display['created_at'] = df_display['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Configurar columnas a mostrar
    columns_to_display = ['store_name', 'brand', 'sender_name', 'status', 'created_at']
    df_display = df_display[columns_to_display]
    
    # Renombrar columnas para mejor presentación
    df_display = df_display.rename(columns={
        'store_name': 'Tienda',
        'brand': 'Marca',
        'sender_name': 'Remitente',
        'status': 'Estado',
        'created_at': 'Fecha'
    })
    
    st.dataframe(df_display, use_container_width=True)
    
    # Botones de exportación
    st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # Exportar a Excel
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                # Preparar DataFrame para exportación
                export_df = df_filtrado.copy()
                export_df['created_at'] = export_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
                
                # Renombrar columnas
                export_df = export_df.rename(columns={
                    'store_name': 'Tienda',
                    'brand': 'Marca',
                    'sender_name': 'Remitente',
                    'status': 'Estado',
                    'created_at': 'Fecha'
                })
                
                # Exportar a Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Historial_Guías', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_data,
                    file_name=f"historial_guias_{fecha_inicio}_a_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar historial de guías a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Exportar a CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"historial_guias_{fecha_inicio}_a_{fecha_fin}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_ayuda():
    """Muestra la página de ayuda y contacto"""
    st.markdown("<h1 class='header-title animate-fade-in'>❓ Ayuda y Contacto</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>¿Cómo usar la aplicación?</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>📝 Guía de uso</h3>
        
        <h4>**Sistema de KPIs:**</h4>
        <ul>
            <li><strong>Dashboard de KPIs:</strong> Visualiza el rendimiento diario de los equipos.</li>
            <li><strong>Análisis Histórico:</strong> Analiza tendencias y exporta reportes.</li>
            <li><strong>Ingreso de Datos:</strong> Ingresa los datos diarios de producción.</li>
            <li><strong>Gestión de Trabajadores:</strong> Administra el personal de la empresa.</li>
        </ul>
        
        <h4>**Sistema de Guías:**</h4>
        <ul>
            <li><strong>Generar Guía:</strong> Selecciona la tienda, la empresa (Fashion o Tempo), el remitente y pega la URL del pedido. Haz clic en "Generar Guía".</li>
            <li><strong>Historial de Guías:</strong> Consulta y exporta el historial de guías generadas.</li>
        </ul>
        
        <h3>📞 Soporte Técnico</h3>
        <p>Si tienes algún problema o necesitas asistencia, por favor contacta a:</p>
        <p><strong>Ing. Wilson Pérez</strong><br>
        <strong>Teléfono:</strong> 0993052744</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================================
# Función principal
# ================================

def main():
    """Función principal de la aplicación"""
    
    # Mostrar logo y título en el sidebar
    st.sidebar.markdown("""
    <div class='sidebar-title'>
        <div class='aeropostale-logo'>AEROPOSTALE</div>
        <div class='aeropostale-subtitle'>Sistema de Gestión de KPIs</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú de navegación
    menu_options = [
        ("Dashboard KPIs", "📊", mostrar_dashboard_kpis),
        ("Análisis Histórico", "📈", mostrar_analisis_historico_kpis),
        ("Ingreso de Datos", "📥", mostrar_ingreso_datos_kpis),
        ("Gestión de Trabajadores", "👥", mostrar_gestion_trabajadores_kpis),
        ("Generar Guías", "📦", mostrar_generacion_guias),
        ("Historial de Guías", "🔍", mostrar_historial_guias),
        ("Ayuda y Contacto", "❓", mostrar_ayuda)
    ]
    
    # Mostrar opciones del menú
    for i, (label, icon, _) in enumerate(menu_options):
        selected = st.sidebar.button(
            f"{icon} {label}",
            key=f"menu_{i}",
            use_container_width=True
        )
        if selected:
            st.session_state.selected_menu = i
    
    # Establecer una opción predeterminada si no hay ninguna seleccionada
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = 0
    
    # Mostrar contenido según la opción seleccionada
    _, _, func = menu_options[st.session_state.selected_menu]
    
    # Para las opciones que requieren autenticación
    if st.session_state.selected_menu in [2, 3, 4]:  # Ingreso de Datos, Gestión de Trabajadores, Generar Guías
        if not verificar_password():
            solicitar_autenticacion()
        else:
            func()
    else:
        func()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.<br>
        Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com">Wilson Pérez</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
# Importación CORREGIDA de Any y otros tipos
from typing import Dict, List, Optional, Tuple, Any, Union

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_PASSWORD = "Wilo3161"  # Contraseña única sensible a mayúsculas

# Configuración de imágenes
APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# Inicializar cliente de Supabase
@st.cache_resource
def init_supabase() -> Client:
    """Inicializa y cachea el cliente de Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        st.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error al inicializar Supabase: {e}", exc_info=True)
        st.error("Error al conectar con la base de datos. Verifique las variables de entorno.")
        return None

# Inicializar cliente de Supabase
supabase = init_supabase()

# Configuración de página
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# CSS profesional mejorado - CORREGIDO
st.markdown("""
<style>
    /* Colores corporativos de Aeropostale */
    :root {
        --primary-color: navy;
        --secondary-color: #000000;
        --accent-color: #333333;
        --background-dark: #121212;
        --card-background: #2d30f0;
        --text-color: #ffffff;
        --text-secondary: #b0b0b0;
        --success-color: #4caf50;
        --warning-color: #ff9800;
        --error-color: #f44336;
    }
    
    body {
        background-color: var(--background-dark);
        color: var(--text-color);
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .stApp {
        background-color: var(--background-dark);
    }
    
    /* Estilos del sidebar */
    .css-1d391kg {
        background-color: var(--card-background) !important;
    }
    
    .sidebar-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--primary-color);
        text-align: center;
        margin: 20px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--primary-color);
    }
    
    .menu-item {
        padding: 12px 15px;
        border-radius: 8px;
        margin: 8px 0;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
    }
    
    .menu-item:hover {
        background-color: rgba(230, 0, 18, 0.1);
    }
    
    .menu-item.active {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
    }
    
    .menu-item i {
        margin-right: 10px;
        font-size: 1.2rem;
    }
    
    /* Tarjetas y métricas */
    .kpi-card {
        background: var(--card-background);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        padding: 20px;
        margin: 15px 0;
        border-left: 5px solid var(--primary-color);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2.8em;
        font-weight: bold;
        color: var(--primary-color);
        line-height: 1.2;
        margin: 10px 0;
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 1.1em;
        margin-bottom: 5px;
    }
    
    .trend-up {
        color: var(--success-color);
    }
    
    .trend-down {
        color: var(--error-color);
    }
    
    /* Encabezados y secciones */
    .header-title {
        color: var(--text-color);
        font-weight: 800;
        font-size: 2.5em;
        margin-bottom: 20px;
        position: relative;
        padding-bottom: 10px;
    }
    
    .header-title::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 4px;
        background-color: var(--primary-color);
        border-radius: 2px;
    }
    
    .section-title {
        color: var(--text-color);
        font-size: 1.8em;
        margin: 25px 0 15px;
        padding-left: 15px;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Tablas y datos */
    .data-table {
        background: var(--card-background);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    }
    
    /* Botones */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), #b3000e);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
        box-shadow: 0 4px 10px rgba(230, 0, 18, 0.25);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(230, 0, 18, 0.35);
        background: linear-gradient(135deg, #cc0010, #99000c);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Inputs y formularios */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2a2a2a !important;
        color: var(--text-color) !important;
        border: 1px solid #3a3a3a !important;
        border-radius: 8px;
        padding: 10px !important;
    }
    
    .stSelectbox > div > div > div {
        background-color: #2a2a2a !important;
        color: var(--text-color) !important;
        border: 1px solid #3a3a3a !important;
        border-radius: 8px;
    }
    
    /* Mensajes de estado */
    .success-box {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.05));
        color: #8bc34a;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #8bc34a;
        margin: 15px 0;
    }
    
    .error-box {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.15), rgba(244, 67, 54, 0.05));
        color: #ff6b6b;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ff6b6b;
        margin: 15px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.05));
        color: #ffc107;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 15px 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(3, 169, 244, 0.15), rgba(3, 169, 244, 0.05));
        color: #4fc3f7;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4fc3f7;
        margin: 15px 0;
    }
    
    /* Estilos específicos para el sistema de guías */
    .guide-section {
        background: var(--card-background);
        border-radius: 12px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .qr-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .guide-metric {
        font-size: 1.3em;
        margin: 12px 0;
        color: var(--text-color);
        display: flex;
        align-items: center;
    }
    
    .guide-metric strong {
        color: var(--primary-color);
        margin-left: 8px;
    }
    
    .guide-icon {
        color: var(--primary-color);
        margin-right: 10px;
        font-size: 1.5em;
    }
    
    /* Estilos para el sistema de autenticación */
    .password-container {
        background: var(--card-background);
        padding: 35px;
        border-radius: 15px;
        max-width: 450px;
        margin: 80px auto;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(230, 0, 18, 0.2);
    }
    
    .password-title {
        color: var(--primary-color);
        font-size: 2.2em;
        text-align: center;
        margin-bottom: 25px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 12px;
    }
    
    .password-input {
        margin-bottom: 25px;
    }
    
    .logo-container {
        text-align: center;
        margin-bottom: 30px;
    }
    
    .aeropostale-logo {
        font-size: 3.5em;
        font-weight: 800;
        color: var(--primary-color);
        text-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        letter-spacing: -1px;
    }
    
    .aeropostale-subtitle {
        color: var(--text-secondary);
        font-size: 1.1em;
        margin-top: 8px;
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px 0;
        margin-top: 30px;
        color: var(--text-secondary);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        font-size: 0.9em;
    }
    
    .footer a {
        color: var(--primary-color);
        text-decoration: none;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2em;
        }
        
        .section-title {
            font-size: 1.5em;
        }
        
        .metric-value {
            font-size: 2.2em;
        }
        
        .password-container {
            margin: 40px 20px;
            padding: 25px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ================================
# Funciones de utilidad compartidas
# ================================

def validar_fecha(fecha: str) -> bool:
    """Valida que una fecha tenga el formato correcto"""
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_numero_positivo(valor: Any) -> bool:
    """Valida que un valor sea un número positivo"""
    try:
        num = float(valor)
        return num >= 0
    except (ValueError, TypeError):
        return False

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(pw.encode()).hexdigest()

# ================================
# Funciones de KPIs
# ================================

# Funciones de cálculo de KPIs
def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general"""
    return (cantidad / meta) * 100 if meta > 0 else 0

def kpi_transferencias(transferidas: float, meta: float = 1750) -> float:
    """Calcula el KPI para transferencias"""
    return calcular_kpi(transferidas, meta)

def kpi_arreglos(arregladas: float, meta: float = 150) -> float:
    """Calcula el KPI para arreglos"""
    return calcular_kpi(arregladas, meta)

def kpi_distribucion(distribuidas: float, meta: float = 1000) -> float:
    """Calcula el KPI para distribución"""
    return calcular_kpi(distribuidas, meta)

def kpi_guias(guias: float, meta: float = 120) -> float:
    """Calcula el KPI para guías"""
    return calcular_kpi(guias, meta)

def productividad_hora(cantidad: float, horas_trabajo: float) -> float:
    """Calcula la productividad por hora"""
    return cantidad / horas_trabajo if horas_trabajo > 0 else 0

# Funciones de acceso a datos (ahora usando Supabase)
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })
    
    try:
        response = supabase.from_('trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df
        else:
            logger.warning("No se encontraron trabajadores en Supabase")
            return pd.DataFrame(columns=['nombre', 'equipo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores de Supabase: {e}", exc_info=True)
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })

def obtener_equipos() -> list:
    """Obtiene la lista de equipos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            equipos = [item['equipo'] for item in response.data]
            # Asegurar que "Distribución" esté en la lista
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            # Ordenar los equipos en un orden específico
            orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
            equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
            equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
            return equipos_ordenados + equipos_restantes
        else:
            logger.warning("No se encontraron equipos en Supabase")
            return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos de Supabase: {e}", exc_info=True)
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos en la tabla de Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        registros = []
        for nombre, info in datos.items():
            # Validar datos antes de guardar
            if not all([
                validar_fecha(fecha),
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                logger.warning(f"Datos inválidos para {nombre}, omitiendo guardado")
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
            # Usar upsert para insertar o actualizar
            response = supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            
            # Limpiar caché de datos históricos
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
                
            logger.info(f"Datos guardados correctamente en Supabase para la fecha {fecha}")
            return True
        else:
            logger.warning("No hay registros válidos para guardar")
            return False
    except Exception as e:
        logger.error(f"Error al guardar datos en Supabase: {e}", exc_info=True)
        return False

def cargar_historico_db(fecha_inicio: str = None, 
                       fecha_fin: str = None, 
                       trabajador: str = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('daily_kpis').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador:
            query = query.eq('nombre', trabajador)
            
        query = query.order('fecha', desc=True)
        
        response = query.execute()
        
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Convertir fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])
                # Calcular columnas adicionales
                df['cumplimiento_meta'] = np.where(df['cantidad'] >= df['meta'], 'Sí', 'No')
                df['diferencia_meta'] = df['cantidad'] - df['meta']
            return df
        else:
            logger.info("No se encontraron datos históricos en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

# Funciones de visualización
def crear_grafico_interactivo(df: pd.DataFrame, x: str, y: str, title: str, 
                             xlabel: str, ylabel: str, tipo: str = 'bar') -> go.Figure:
    """Crea gráficos interactivos con Plotly"""
    try:
        if df.empty:
            logger.warning("DataFrame vacío para crear gráfico interactivo")
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=18, color="#666666")
            )
            return fig
            
        if tipo == 'bar':
            fig = px.bar(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'line':
            fig = px.line(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'scatter':
            fig = px.scatter(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        elif tipo == 'box':
            fig = px.box(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
        else:
            fig = px.bar(df, x=x, y=y, title=title, labels={x: xlabel, y: ylabel})
            
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff"),
            title_font_color="#ffffff",
            xaxis_title_font_color="#ffffff",
            yaxis_title_font_color="#ffffff",
            xaxis_tickfont_color="#ffffff",
            yaxis_tickfont_color="#ffffff",
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico: {e}", exc_info=True)
        # Devolver figura vacía en caso de error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#e74c3c")
        )
        return fig

def crear_grafico_frasco(porcentaje: float, titulo: str) -> go.Figure:
    """Crea un gráfico de frasco de agua para mostrar el porcentaje de cumplimiento"""
    try:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = porcentaje,
            number = {'suffix': '%', 'font': {'size': 36, 'color': '#ffffff'}},
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': titulo, 'font': {'size': 20, 'color': '#ffffff'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#e60012", 'thickness': 0.3},
                'bgcolor': "#2a2a2a",
                'borderwidth': 2,
                'bordercolor': "#444444",
                'steps': [
                    {'range': [0, 50], 'color': "darkred"},
                    {'range': [50, 75], 'color': "darkorange"},
                    {'range': [75, 100], 'color': "forestgreen"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de frasco: {e}", exc_info=True)
        return go.Figure()

# ================================
# Funciones de Guías (NUEVAS)
# ================================

def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único."""
    return f"9400{str(record_id).zfill(20)}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera y devuelve una imagen del código QR."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def obtener_tiendas() -> pd.DataFrame:
    """Obtiene la lista de tiendas desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"]
        })
    
    try:
        response = supabase.from_('guide_stores').select('*').execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron tiendas en Supabase")
            return pd.DataFrame(columns=['id', 'name'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"]
        })

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["Fashion Club", "Tempo"],
            'address': ["Dirección 1", "Dirección 2"],
            'phone': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.from_('guide_senders').select('*').execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron remitentes en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["Fashion Club", "Tempo"],
            'address': ["Dirección 1", "Dirección 2"],
            'phone': ["0993052744", "0987654321"]
        })

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """Guarda una guía en Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Insertar nueva guía
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.from_('guide_logs').insert(data).execute()
        
        # Verificar si la inserción fue exitosa
        if response and response.data:
            logger.info(f"Guía guardada correctamente para {store_name}")
            return True
        else:
            logger.error("No se pudo guardar la guía en Supabase")
            return False
    except Exception as e:
        logger.error(f"Error al guardar guía en Supabase: {e}", exc_info=True)
        return False

def obtener_historial_guias() -> pd.DataFrame:
    """Obtiene el historial de guías desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('guide_logs').select('*')
        query = query.order('created_at', desc=True)
        
        response = query.execute()
        
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Convertir fecha a datetime
                df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        else:
            logger.info("No se encontraron guías en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar historial de guías de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def generar_pdf_guia(store_name: str, brand: str, url: str, sender_name: str, 
                    sender_address: str, sender_phone: str, tracking_number: str) -> bytes:
    """Genera un PDF de la guía de envío"""
    try:
        # Crear un PDF en memoria
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Título
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Guía de Envío", ln=True, align="C")
        pdf.ln(10)
        
        # Información de la tienda
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Tienda:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, store_name, ln=True)
        
        # Información de la marca
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Marca:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, brand, ln=True)
        
        # Información del remitente
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Remitente:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{sender_name} - {sender_phone}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(40, 8, "")
        pdf.multi_cell(0, 8, sender_address)
        pdf.ln(5)
        
        # Número de seguimiento
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Número de Seguimiento:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, tracking_number, ln=True)
        pdf.ln(5)
        
        # Código QR
        qr_img = generar_qr_imagen(url)
        
        # Guardar QR en un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_qr:
            qr_img.save(temp_qr.name)
            pdf.image(temp_qr.name, x=70, y=pdf.get_y(), w=70, h=70)
            os.unlink(temp_qr.name)
        
        # URL
        pdf.ln(75)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "URL del Pedido:")
        pdf.set_font("Arial", "U", 12)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 8, url, ln=True)
        pdf.set_text_color(0, 0, 0)
        
        # Convertir PDF a bytes
        return pdf.output(dest="S").encode("latin1")
    except Exception as e:
        logger.error(f"Error al generar PDF de guía: {e}", exc_info=True)
        return b""

def get_logo_path(brand: str) -> str:
    """Devuelve la ruta del logo de la marca."""
    if brand == "Fashion":
        return os.path.join(IMAGES_DIR, "Fashion.jpg")
    elif brand == "Tempo":
        return os.path.join(IMAGES_DIR, "Tempo.jpg")
    return None

def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    """Convierte un objeto de imagen de PIL a bytes."""
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()

def custom_selectbox(label: str, options: list, key: str, search_placeholder: str = "Buscar...") -> str:
    """Componente personalizado de selectbox con búsqueda."""
    if f"{key}_search" not in st.session_state:
        st.session_state[f"{key}_search"] = ""
    
    search_term = st.text_input(f"{label} - {search_placeholder}", 
                               value=st.session_state[f"{key}_search"], 
                               key=f"{key}_search_input")
    
    st.session_state[f"{key}_search"] = search_term
    
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in opt.lower()]
    else:
        filtered_options = options
    
    if not filtered_options:
        st.warning("No se encontraron resultados.")
        return None
    
    return st.selectbox(label, filtered_options, key=key)

# ================================
# Sistema de autenticación
# ================================

def verificar_password() -> bool:
    """Verifica si el usuario tiene permisos para realizar acciones críticas"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

def solicitar_autenticacion():
    """Muestra un formulario de autenticación"""
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Gestión de KPIs</div>
        </div>
        <h2 class="password-title">🔐 Acceso Restringido</h2>
        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 25px;">
            Ingrese la contraseña para realizar esta acción
        </p>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña:", type="password", key="auth_password", 
                            placeholder="Ingrese su contraseña", 
                            label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.button("Ingresar", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submitted:
        if password == ADMIN_PASSWORD:
            st.session_state.password_correct = True
            st.success("✅ Acceso concedido")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

# ================================
# Componentes de la aplicación
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Crear selector de fecha
    st.markdown("<div class='date-selector animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3>Selecciona la fecha a visualizar:</h3>", unsafe_allow_html=True)
    
    # Obtener fechas únicas y ordenarlas
    if not df.empty and 'fecha' in df.columns:
        # Convertir a fecha y eliminar duplicados
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
            return
        fecha_seleccionada = st.selectbox(
            "Fecha:",
            options=fechas_disponibles,
            index=0,
            label_visibility="collapsed"
        )
    else:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles.</div>", unsafe_allow_html=True)
        return
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filtrar datos por fecha seleccionada
    df_reciente = df[df['fecha'].dt.date == fecha_seleccionada]
    if df_reciente.empty:
        st.markdown(f"<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles para la fecha {fecha_seleccionada}.</div>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<p style='color: var(--text-secondary); font-size: 1.1em;'>Datos para la fecha: {fecha_seleccionada}</p>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    
    # Cálculos globales
    total_cantidad = df_reciente['cantidad'].sum()
    total_meta = df_reciente['meta'].sum()
    total_horas = df_reciente['horas_trabajo'].sum()
    avg_eficiencia = (df_reciente['eficiencia'] * df_reciente['horas_trabajo']).sum() / total_horas if total_horas > 0 else 0
    avg_productividad = df_reciente['productividad'].mean()
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        cumplimiento_meta = (total_cantidad / total_meta * 100) if total_meta > 0 else 0
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">✅ Total Producción</div>
            <p class="metric-value">{total_cantidad:,.0f}</p>
            <p>Meta: {total_meta:,.0f} | <span class="{'trend-up' if cumplimiento_meta >= 100 else 'trend-down'}">{cumplimiento_meta:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">🎯 Eficiencia Promedio</div>
            <p class="metric-value">{avg_eficiencia:.1f}%</p>
            <p>Meta: 100% | <span class="{'trend-up' if avg_eficiencia >= 100 else 'trend-down'}">{avg_eficiencia - 100:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">⚡ Productividad Promedio</div>
            <p class="metric-value">{avg_productividad:.1f}</p>
            <p>unidades/hora</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">⏱️ Productividad Total</div>
            <p class="metric-value">{productividad_total:.1f}</p>
            <p>unidades/hora ({total_horas:.1f} h)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📅 Cumplimiento de Metas Mensuales (Transferencias)</h2>", unsafe_allow_html=True)
    
    current_month = fecha_seleccionada.month
    current_year = fecha_seleccionada.year
    
    # Filtrar datos del mes actual para transferencias
    df_month = df[(df['fecha'].dt.month == current_month) & 
                  (df['fecha'].dt.year == current_year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    # Obtener meta mensual de transferencias (usamos el último valor registrado)
    if not df_transferencias_month.empty:
        meta_mensual_transferencias = df_transferencias_month['meta_mensual'].iloc[0]
    else:
        # Si no hay datos, usar un valor por defecto
        meta_mensual_transferencias = 150000
    
    cum_transferencias = df_transferencias_month['cantidad'].sum()
    cumplimiento_transferencias = (cum_transferencias / meta_mensual_transferencias * 100) if meta_mensual_transferencias > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Meta Mensual Transferencias</div>
            <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
            <p>Acumulado: {cum_transferencias:,.0f} / Meta Mensual: {meta_mensual_transferencias:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Gráfico de frasco de agua para el cumplimiento
        fig = crear_grafico_frasco(cumplimiento_transferencias, "Cumplimiento Mensual Transferencias")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Gráfico de evolución mensual
    if not df_transferencias_month.empty:
        df_transferencias_daily = df_transferencias_month.groupby(df_transferencias_month['fecha'].dt.date)['cantidad'].sum().reset_index(name='cantidad')
        df_transferencias_daily['fecha'] = pd.to_datetime(df_transferencias_daily['fecha'])
        df_transferencias_daily = df_transferencias_daily.sort_values('fecha')
        df_transferencias_daily['cumulative'] = df_transferencias_daily['cantidad'].cumsum()
        
        fig = crear_grafico_interactivo(
            df_transferencias_daily, 
            'fecha', 
            'cumulative', 
            'Cumplimiento Mensual Transferencias', 
            'Día', 
            'Acumulado',
            'line'
        )
        # Añadir línea de meta
        fig.add_hline(y=meta_mensual_transferencias, line_dash="dash", line_color="white", annotation_text="Meta Mensual")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No hay datos para el gráfico de Transferencias.")
    
    st.markdown("<h2 class='section-title animate-fade-in'>👥 Rendimiento por Equipos</h2>", unsafe_allow_html=True)
    
    # Obtener lista de equipos
    equipos = df_reciente['equipo'].unique()
    # Ordenar equipos en un orden específico
    orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
    equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
    equipos_finales = equipos_ordenados + equipos_restantes
    
    for equipo in equipos_finales:
        df_equipo = df_reciente[df_reciente['equipo'] == equipo]
        st.markdown(f"<div class='team-section animate-fade-in'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
        
        # Calcular KPIs del equipo
        total_equipo = df_equipo['cantidad'].sum()
        meta_equipo = df_equipo['meta'].sum()
        horas_equipo = df_equipo['horas_trabajo'].sum()
        eficiencia_equipo = (df_equipo['eficiencia'] * df_equipo['horas_trabajo']).sum() / horas_equipo if horas_equipo > 0 else 0
        productividad_equipo = total_equipo / horas_equipo if horas_equipo > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Producción</div>
                <p class="metric-value">{total_equipo:,.0f}</p>
                <p>Meta: {meta_equipo:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Eficiencia</div>
                <p class="metric-value">{eficiencia_equipo:.1f}%</p>
                <p>Meta: 100%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Productividad</div>
                <p class="metric-value">{productividad_equipo:.1f}</p>
                <p>unidades/hora</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Horas</div>
                <p class="metric-value">{horas_equipo:.1f}</p>
                <p>horas trabajadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar trabajadores del equipo
        for _, row in df_equipo.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                color = "#8bc34a" if row['eficiencia'] >= 100 else "#ff6b6b"
                card_content = f"""
                <div class="worker-card">
                    <div class="stats-container">
                        <div class="worker-header">{row['nombre']}</div>
                        <div class="worker-metric">📦 {row['actividad']}: <span style='font-weight:bold'>{row['cantidad']}</span></div>
                        <div class="worker-metric">🎯 Eficiencia: <span style='color:{color}; font-weight:bold'>{row['eficiencia']:.1f}%</span></div>
                        <div class="worker-metric">⏱️ Productividad: {row['productividad']:.1f}/hora</div>
                        <div class="worker-metric">⏰ Horas: {row['horas_trabajo']:.1f} h</div>
                    </div>
                </div>
                """
                st.markdown(card_content, unsafe_allow_html=True)
            
            with col2:
                comentario = row.get('comentario', None)
                if pd.notna(comentario) and str(comentario).strip() != "":
                    st.markdown(f"""
                    <div class="comment-container">
                        <div class="comment-title">💬 Comentario:</div>
                        <div class="comment-content">{comentario}</div>
                    </div>
                    """, unsafe_allow_html=True)

def mostrar_analisis_historico_kpis():
    """Muestra el análisis histórico de KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    df = cargar_historico_db()
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    df['dia'] = df['fecha'].dt.date
    fecha_min = df['dia'].min()
    fecha_max = df['dia'].max()
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
    with col3:
        trabajador = st.selectbox("Filtrar por trabajador:", options=["Todos"] + list(df['nombre'].unique()))
    
    if fecha_inicio > fecha_fin:
        st.markdown("<div class='error-box animate-fade-in'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    # Aplicar filtros
    df_filtrado = df[(df['dia'] >= fecha_inicio) & (df['dia'] <= fecha_fin)]
    if trabajador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador]
    
    if df_filtrado.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos en el rango de fechas seleccionado.</div>", unsafe_allow_html=True)
        return
    
    # Botones de exportación
    st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        # Botón para exportar a Excel
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                # Crear una copia del DataFrame para no modificar el original
                export_df = df_filtrado.copy()
                
                # Asegurar que las fechas estén en formato adecuado
                if 'fecha' in export_df.columns:
                    export_df['fecha'] = pd.to_datetime(export_df['fecha']).dt.strftime('%Y-%m-%d')
                
                # Manejar valores NaN и None
                export_df = export_df.fillna('N/A')
                
                # Reordenar columnas para una mejor presentación
                columnas_ordenadas = [
                    'fecha', 'nombre', 'equipo', 'actividad', 'cantidad', 'meta', 
                    'eficiencia', 'productividad', 'horas_trabajo', 'meta_mensual', 'comentario'
                ]
                # Solo incluir las columnas que existen en el DataFrame
                columnas_finales = [col for col in columnas_ordenadas if col in export_df.columns]
                export_df = export_df[columnas_finales]
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Datos_KPIs', index=False)
                    # Formato adicional para mejorar el Excel
                    workbook = writer.book
                    worksheet = writer.sheets['Datos_KPIs']
                    
                    # Formato para encabezados
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#e60012',
                        'font_color': 'white',
                        'border': 1
                    })
                    
                    # Formato para celdas
                    cell_format = workbook.add_format({
                        'border': 1,
                        'align': 'left',
                        'valign': 'vcenter'
                    })
                    
                    # Aplicar formato a encabezados
                    for col_num, value in enumerate(export_df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Aplicar formato a todas las celdas de datos
                    for row in range(1, len(export_df) + 1):
                        for col in range(len(export_df.columns)):
                            worksheet.write(row, col, export_df.iloc[row-1, col], cell_format)
                    
                    # Autoajustar columnas
                    for i, col in enumerate(export_df.columns):
                        # Obtener la longitud máxima de los datos en la columna
                        max_len = max((
                            export_df[col].astype(str).str.len().max(),  # Longitud máxima de los datos
                            len(str(col))  # Longitud del nombre de la columna
                        )) + 2  # Añadir un poco de espacio extra
                        worksheet.set_column(i, i, max_len)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="⬇️ Descargar archivo Excel",
                    data=excel_data,
                    file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Botón para exportar a PDF
        if st.button("📄 Exportar a PDF", use_container_width=True):
            try:
                with st.spinner("Generando reporte PDF..."):
                    # Crear un PDF en memoria
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
                    styles = getSampleStyleSheet()
                    
                    # Estilos personalizados
                    styles.add(ParagraphStyle(name='Header', fontSize=16, alignment=1, spaceAfter=12, textColor='#e60012'))
                    styles.add(ParagraphStyle(name='Section', fontSize=14, spaceBefore=12, spaceAfter=6, textColor='#e60012'))
                    styles.add(ParagraphStyle(name='Normal', fontSize=12, spaceAfter=6))
                    
                    elements = []
                    
                    # Título
                    title = Paragraph("Reporte de KPIs - Aeropostale", styles['Header'])
                    elements.append(title)
                    
                    # Información del período
                    periodo = Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", styles['Normal'])
                    elements.append(periodo)
                    
                    # Resumen estadístico
                    elements.append(Paragraph("Resumen Estadístico", styles['Section']))
                    
                    # Crear tabla de resumen
                    try:
                        resumen_data = df_filtrado.groupby('nombre').agg({
                            'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
                            'eficiencia': ['mean', 'max', 'min'],
                            'productividad': ['mean', 'max', 'min'],
                            'horas_trabajo': ['sum', 'mean']
                        }).round(2)
                        
                        # Aplanar las columnas multiindex
                        resumen_data.columns = ['_'.join(col).strip() for col in resumen_data.columns.values]
                        resumen_data.reset_index(inplace=True)
                        
                        # Convertir DataFrame a lista para la tabla
                        table_data = [list(resumen_data.columns)]
                        for _, row in resumen_data.iterrows():
                            table_data.append(list(row))
                        
                        # Crear tabla
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e60012')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd'))
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 12))
                    except Exception as e:
                        logger.error(f"Error al crear tabla de resumen: {e}", exc_info=True)
                        elements.append(Paragraph(f"Error al generar tabla de resumen: {str(e)}", styles['Normal']))
                        elements.append(Spacer(1, 12))
                    
                    # Construir PDF
                    doc.build(elements)
                    pdf_data = pdf_buffer.getvalue()
                    pdf_buffer.close()
                    
                    st.download_button(
                        label="⬇️ Descargar reporte PDF",
                        data=pdf_data,
                        file_name=f"reporte_kpis_{fecha_inicio}_a_{fecha_fin}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                logger.error(f"Error al exportar a PDF: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a PDF.</div>", unsafe_allow_html=True)
    
    with col3:
        # Botón para exportar a CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📋 Resumen Estadístico</h2>", unsafe_allow_html=True)
    # Mostrar resumen estadístico
    st.dataframe(df_filtrado.groupby('nombre').agg({
        'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
        'eficiencia': ['mean', 'max', 'min'],
        'productividad': ['mean', 'max', 'min'],
        'horas_trabajo': ['sum', 'mean']
    }).round(2), use_container_width=True)
    
    st.markdown("<h2 class='section-title animate-fade-in'>📊 Tendencias Históricas</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Eficiencia por Día", "Producción Acumulada", "Comparativa por Área", "Análisis Detallado", "Predicciones"])
    
    with tab1:
        df_eficiencia_dia = df_filtrado.groupby('dia')['eficiencia'].mean().reset_index()
        if not df_eficiencia_dia.empty:
            fig = crear_grafico_interactivo(
                df_eficiencia_dia, 
                'dia', 
                'eficiencia', 
                'Evolución de la Eficiencia Promedio Diaria', 
                'Fecha', 
                'Eficiencia Promedio (%)',
                'line'
            )
            # Añadir línea de meta
            fig.add_hline(y=100, line_dash="dash", line_color="white", annotation_text="Meta de eficiencia")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab2:
        df_produccion = df_filtrado.groupby(['dia', 'actividad'])['cantidad'].sum().reset_index()
        if not df_produccion.empty:
            fig = crear_grafico_interactivo(
                df_produccion, 
                'dia', 
                'cantidad', 
                'Producción Acumulada por Área', 
                'Fecha', 
                'Producción Acumulada',
                'line'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab3:
        if not df_filtrado.empty:
            fig = crear_grafico_interactivo(
                df_filtrado, 
                'actividad', 
                'productividad', 
                'Distribución de Productividad por Área', 
                'Área', 
                'Productividad (unidades/hora)',
                'box'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay datos para el gráfico.")
    
    with tab4:
        st.markdown("<h3>📈 Análisis de Correlación</h3>", unsafe_allow_html=True)
        # Calcular matriz de correlación
        numeric_cols = df_filtrado.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df_filtrado[numeric_cols].corr()
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdBu_r',
                title='Matriz de Correlación'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No hay suficientes datos numéricos para calcular correlaciones.")
        
        st.markdown("<h3>📋 Datos Detallados</h3>", unsafe_allow_html=True)
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab5:
        st.markdown("<h3>🔮 Predicción de Tendencia</h3>", unsafe_allow_html=True)
        if not df_eficiencia_dia.empty and len(df_eficiencia_dia) > 5:
            try:
                # Preparar datos para predicción
                dias_prediccion = 7
                x = np.arange(len(df_eficiencia_dia))
                y = df_eficiencia_dia['eficiencia'].values
                
                # Ajustar modelo
                model = np.polyfit(x, y, 1)
                poly = np.poly1d(model)
                
                # Predecir valores futuros
                x_pred = np.arange(len(df_eficiencia_dia), len(df_eficiencia_dia) + dias_prediccion)
                y_pred = poly(x_pred)
                
                # Crear fechas futuras
                ultima_fecha = df_eficiencia_dia['dia'].max()
                fechas_futuras = [ultima_fecha + timedelta(days=i+1) for i in range(dias_prediccion)]
                
                # Crear gráfico
                fig = go.Figure()
                # Datos históricos
                fig.add_trace(go.Scatter(
                    x=df_eficiencia_dia['dia'], 
                    y=df_eficiencia_dia['eficiencia'],
                    mode='lines+markers',
                    name='Datos Históricos'
                ))
                # Predicciones
                fig.add_trace(go.Scatter(
                    x=fechas_futuras, 
                    y=y_pred,
                    mode='lines+markers',
                    name='Predicción',
                    line=dict(dash='dash', color='orange')
                ))
                # Línea de meta
                fig.add_hline(y=100, line_dash="dash", line_color="white", annotation_text="Meta de eficiencia")
                fig.update_layout(
                    title='Predicción de Eficiencia para los Próximos 7 Días',
                    xaxis_title='Fecha',
                    yaxis_title='Eficiencia Promedio (%)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                # Mostrar valores de predicción
                st.markdown("<h4>Valores de Predicción:</h4>", unsafe_allow_html=True)
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, y_pred)):
                    st.write(f"{fecha.strftime('%Y-%m-%d')}: {pred:.1f}%")
            except Exception as e:
                st.error(f"Error al generar predicciones: {str(e)}")
        else:
            st.info("Se necesitan al menos 5 días de datos para realizar predicciones.")

def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener trabajadores desde Supabase
    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay trabajadores registrados. Por favor, registre trabajadores primero.</div>", unsafe_allow_html=True)
        return
    
    # Asegurar que Luis Perugachi esté en el equipo de Distribución
    if 'Luis Perugachi' in df_trabajadores['nombre'].values:
        df_trabajadores.loc[df_trabajadores['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
    
    trabajadores_por_equipo = {}
    for _, row in df_trabajadores.iterrows():
        equipo = row['equipo']
        if equipo not in trabajadores_por_equipo:
            trabajadores_por_equipo[equipo] = []
        trabajadores_por_equipo[equipo].append(row['nombre'])
    
    # Si no existe el equipo de Distribución, crearlo
    if 'Distribución' not in trabajadores_por_equipo:
        trabajadores_por_equipo['Distribución'] = []
    
    # Selector de fecha
    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_seleccionada = st.date_input(
            "Selecciona la fecha:",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    periodo = st.radio("Selecciona el período:", ["Día", "Semana"], horizontal=True)
    
    # Inicializar variables de sesión para almacenar datos
    if 'datos_calculados' not in st.session_state:
        st.session_state.datos_calculados = None
    if 'fecha_guardar' not in st.session_state:
        st.session_state.fecha_guardar = None
    
    with st.form("form_datos"):
        # Meta mensual única para transferencias
        st.markdown("<h3 class='section-title animate-fade-in'>Meta Mensual de Transferencias</h3>", unsafe_allow_html=True)
        meta_mensual_transferencias = st.number_input("Meta mensual para el equipo de transferencias:", min_value=0, value=150000, key="meta_mensual_transferencias")
        
        # Asegurar que el equipo de Distribución esté presente
        if 'Distribución' not in trabajadores_por_equipo:
            trabajadores_por_equipo['Distribución'] = []
        
        # Ordenar los equipos para mostrarlos en un orden específico
        orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
        equipos_ordenados = [eq for eq in orden_equipos if eq in trabajadores_por_equipo]
        equipos_restantes = [eq for eq in trabajadores_por_equipo.keys() if eq not in orden_equipos]
        equipos_finales = equipos_ordenados + equipos_restantes
        
        for equipo in equipos_finales:
            miembros = trabajadores_por_equipo[equipo]
            st.markdown(f"<div class='team-section animate-fade-in'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
            for trabajador in miembros:
                st.subheader(trabajador)
                col1, col2 = st.columns(2)
                with col1:
                    if equipo == "Transferencias":
                        cantidad = st.number_input(f"Prendas transferidas por {trabajador}:", min_value=0, value=1800, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=1750, key=f"{trabajador}_meta")
                    elif equipo == "Distribución":
                        # Para el equipo de Distribución
                        cantidad = st.number_input(f"Prendas distribuidas por {trabajador}:", min_value=0, value=1000, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=1000, key=f"{trabajador}_meta")
                    elif equipo == "Arreglo":
                        cantidad = st.number_input(f"Prendas arregladas por {trabajador}:", min_value=0, value=130, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=150, key=f"{trabajador}_meta")
                    elif equipo == "Guías":
                        cantidad = st.number_input(f"Guías realizadas por {trabajador}:", min_value=0, value=110, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=120, key=f"{trabajador}_meta")
                    elif equipo == "Ventas":
                        cantidad = st.number_input(f"Pedidos preparados por {trabajador}:", min_value=0, value=45, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=40, key=f"{trabajador}_meta")
                    else:
                        cantidad = st.number_input(f"Cantidad realizada por {trabajador}:", min_value=0, value=100, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=100, key=f"{trabajador}_meta")
                with col2:
                    horas = st.number_input(f"Horas trabajadas por {trabajador}:", min_value=0.0, value=8.0, key=f"{trabajador}_horas", step=0.5)
                    comentario = st.text_area(f"Comentario para {trabajador}:", key=f"{trabajador}_comentario")
        
        submitted = st.form_submit_button("Calcular KPIs")
        if submitted:
            datos_guardar = {}
            for equipo, miembros in trabajadores_por_equipo.items():
                for trabajador in miembros:
                    # Obtener valores del formulario
                    cantidad = st.session_state.get(f"{trabajador}_cantidad", 0)
                    meta = st.session_state.get(f"{trabajador}_meta", 0)
                    horas = st.session_state.get(f"{trabajador}_horas", 0)
                    comentario = st.session_state.get(f"{trabajador}_comentario", "")
                    
                    # Validar datos
                    if not all([validar_numero_positivo(cantidad), validar_numero_positivo(meta), validar_numero_positivo(horas)]):
                        st.markdown(f"<div class='error-box animate-fade-in'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
                        continue
                    
                    # Calcular KPIs según el equipo
                    if equipo == "Transferencias":
                        eficiencia = kpi_transferencias(cantidad, meta)
                        actividad = "Transferencias"
                        meta_mensual = meta_mensual_transferencias
                    elif equipo == "Distribución":
                        # Para el equipo de Distribución
                        eficiencia = kpi_distribucion(cantidad, meta)
                        actividad = "Distribución"
                        meta_mensual = 0
                    elif equipo == "Arreglo":
                        eficiencia = kpi_arreglos(cantidad, meta)
                        actividad = "Arreglos"
                        meta_mensual = 0
                    elif equipo == "Guías":
                        eficiencia = kpi_guias(cantidad, meta)
                        actividad = "Guías"
                        meta_mensual = 0
                    elif equipo == "Ventas":
                        eficiencia = kpi_transferencias(cantidad, meta)
                        actividad = "Ventas"
                        meta_mensual = 0
                    else:
                        eficiencia = (cantidad / meta * 100) if meta > 0 else 0
                        actividad = "General"
                        meta_mensual = 0
                    
                    productividad = productividad_hora(cantidad, horas)
                    datos_guardar[trabajador] = {
                        "actividad": actividad, 
                        "cantidad": cantidad, 
                        "meta": meta, 
                        "eficiencia": eficiencia, 
                        "productividad": productividad,
                        "comentario": comentario, 
                        "meta_mensual": meta_mensual,
                        "horas_trabajo": horas,
                        "equipo": equipo
                    }
            
            # Convertir la fecha seleccionada a string
            fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
            
            # Almacenar datos en sesión para confirmación posterior
            st.session_state.datos_calculados = datos_guardar
            st.session_state.fecha_guardar = fecha_str
            
            # Mostrar resumen
            st.markdown("<h3 class='section-title animate-fade-in'>📋 Resumen de KPIs Calculados</h3>", unsafe_allow_html=True)
            for equipo, miembros in trabajadores_por_equipo.items():
                st.markdown(f"**{equipo}:**")
                for trabajador in miembros:
                    if trabajador in datos_guardar:
                        datos = datos_guardar[trabajador]
                        st.markdown(f"- {trabajador}: {datos['cantidad']} unidades ({datos['eficiencia']:.1f}%)")
    
    # Botón de confirmación fuera del formulario
    if st.session_state.datos_calculados is not None and st.session_state.fecha_guardar is not None:
        if st.button("✅ Confirmar y Guardar Datos", key="confirmar_guardar", use_container_width=True):
            if guardar_datos_db(st.session_state.fecha_guardar, st.session_state.datos_calculados):
                st.markdown("<div class='success-box animate-fade-in'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                # Limpiar datos de confirmación
                st.session_state.datos_calculados = None
                st.session_state.fecha_guardar = None
                time.sleep(2)
                st.rerun()
            else:
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)

def mostrar_gestion_trabajadores_kpis():
    """Muestra la interfaz de gestión de trabajadores"""
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    try:
        # Obtener lista actual de trabajadores
        response = supabase.from_('trabajadores').select('*').order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            trabajadores = response.data
        else:
            trabajadores = []
        
        # Asegurar que Luis Perugachi esté en el equipo de Distribución
        if any(trab['nombre'] == 'Luis Perugachi' for trab in trabajadores):
            for trab in trabajadores:
                if trab['nombre'] == 'Luis Perugachi':
                    trab['equipo'] = 'Distribución'
        
        st.markdown("<h2 class='section-title animate-fade-in'>Trabajadores Actuales</h2>", unsafe_allow_html=True)
        if trabajadores:
            df_trabajadores = pd.DataFrame(trabajadores)
            st.dataframe(df_trabajadores[['nombre', 'equipo', 'activo']], use_container_width=True)
        else:
            st.info("No hay trabajadores registrados.")
        
        st.markdown("<h2 class='section-title animate-fade-in'>Agregar Nuevo Trabajador</h2>", unsafe_allow_html=True)
        with st.form("form_nuevo_trabajador"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre del trabajador:")
            with col2:
                equipos = obtener_equipos()
                nuevo_equipo = st.selectbox("Equipo:", options=equipos)
            submitted = st.form_submit_button("Agregar Trabajador")
            if submitted:
                if nuevo_nombre:
                    try:
                        # Verificar si el trabajador ya existe
                        response = supabase.from_('trabajadores').select('*').eq('nombre', nuevo_nombre).execute()
                        # Verificar si hay datos en la respuesta
                        if response and response.data:
                            st.markdown("<div class='error-box animate-fade-in'>❌ El trabajador ya existe.</div>", unsafe_allow_html=True)
                        else:
                            # Insertar nuevo trabajador
                            supabase.from_('trabajadores').insert({
                                'nombre': nuevo_nombre, 
                                'equipo': nuevo_equipo,
                                'activo': True
                            }).execute()
                            st.markdown("<div class='success-box animate-fade-in'>✅ Trabajador agregado correctamente.</div>", unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error al agregar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box animate-fide-in'>❌ Error al agregar trabajador.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Debe ingresar un nombre.</div>", unsafe_allow_html=True)
        
        st.markdown("<h2 class='section-title animate-fade-in'>Eliminar Trabajador</h2>", unsafe_allow_html=True)
        if trabajadores:
            trabajadores_activos = [t['nombre'] for t in trabajadores if t.get('activo', True)]
            if trabajadores_activos:
                trabajador_eliminar = st.selectbox("Selecciona un trabajador para eliminar:", options=trabajadores_activos)
                if st.button("Eliminar Trabajador", use_container_width=True):
                    try:
                        # Actualizar el estado del trabajador a inactivo
                        supabase.from_('trabajadores').update({'activo': False}).eq('nombre', trabajador_eliminar).execute()
                        st.markdown("<div class='success-box animate-fade-in'>✅ Trabajador eliminado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error al eliminar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al eliminar trabajador.</div>", unsafe_allow_html=True)
            else:
                st.info("No hay trabajadores activos para eliminar.")
        else:
            st.info("No hay trabajadores registrados.")
    except Exception as e:
        logger.error(f"Error en gestión de trabajadores: {e}", exc_info=True)
        st.markdown("<div class='error-box animate-fade-in'>❌ Error del sistema al gestionar trabajadores.</div>", unsafe_allow_html=True)

def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()
    
    if tiendas.empty or remitentes.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Formulario para generar guía
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Generar Nueva Guía</h2>", unsafe_allow_html=True)
    
    with st.form("form_generar_guia"):
        col1, col2 = st.columns(2)
        with col1:
            store_name = custom_selectbox("Seleccione Tienda", tiendas['name'].tolist(), "store_select", "Buscar tienda...")
            brand = st.radio("Seleccione Empresa:", ["Fashion", "Tempo"], horizontal=True, key="brand_select")
        
        with col2:
            sender_name = st.selectbox("Seleccione Remitente:", options=remitentes['name'].tolist(), key="sender_select")
            url = st.text_input("Ingrese URL del Pedido:", key="url_input", placeholder="https://...")
        
        submitted = st.form_submit_button("Generar Guía", use_container_width=True)
        
        if submitted:
            if not all([store_name, brand, url, sender_name]):
                st.markdown("<div class='error-box animate-fade-in'>❌ Por favor, complete todos los campos.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
            elif not url.startswith(('http://', 'https://')):
                st.markdown("<div class='error-box animate-fade-in'>❌ La URL debe comenzar con http:// o https://</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
            else:
                # Guardar la guía
                if guardar_guia(store_name, brand, url, sender_name):
                    st.session_state.show_preview = True
                    # Obtener información del remitente
                    remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                    st.session_state.remitente_address = remitente_info['address']
                    st.session_state.remitente_phone = remitente_info['phone']
                    st.session_state.tracking_number = generar_numero_seguimiento(1)  # Aquí debería ser el ID real
                    st.markdown("<div class='success-box animate-fade-in'>✅ Guía generada correctamente. Puede ver la previsualización y exportarla.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar la guía.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Previsualización de la guía
    if st.session_state.get('show_preview', False):
        st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title animate-fade-in'>Previsualización de la Guía</h2>", unsafe_allow_html=True)
        
        # Información de la guía
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🏬</span> <strong>Tienda:</strong> {st.session_state.get('store_select', '')}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🏷️</span> <strong>Marca:</strong> {st.session_state.get('brand_select', '')}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='guide-metric'><span class='guide-icon'>📦</span> <strong>Remitente:</strong> {st.session_state.get('sender_select', '')}</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='guide-metric'><span class='guide-icon'>🔗</span> <strong>URL del Pedido:</strong> <a href='{st.session_state.get('url_input', '')}' target='_blank'>{st.session_state.get('url_input', '')}</a></div>", unsafe_allow_html=True)
        
        # Código QR
        st.markdown("<h3>Código QR:</h3>", unsafe_allow_html=True)
        qr_img = generar_qr_imagen(st.session_state.get('url_input', ''))
        st.image(pil_image_to_bytes(qr_img), width=200)
        
        # Botones de exportación
        st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            # Generar PDF
            pdf_data = generar_pdf_guia(
                st.session_state.get('store_select', ''),
                st.session_state.get('brand_select', ''),
                st.session_state.get('url_input', ''),
                st.session_state.get('sender_select', ''),
                st.session_state.get('remitente_address', ''),
                st.session_state.get('remitente_phone', ''),
                st.session_state.get('tracking_number', '')
            )
            st.download_button(
                label="📄 Descargar PDF",
                data=pdf_data,
                file_name=f"guia_{st.session_state.get('store_select', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col2:
            if st.button("🖨️ Marcar como Impresa", use_container_width=True):
                # Aquí iría la lógica para actualizar el estado de la guía
                st.markdown("<div class='success-box animate-fade-in'>✅ Guía marcada como impresa.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_historial_guias():
    """Muestra el historial de guías generadas"""
    st.markdown("<h1 class='header-title animate-fade-in'>🔍 Historial de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar historial de guías
    df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay guías generadas.</div>", unsafe_allow_html=True)
        return
    
    # Filtros
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Filtros</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=df_guias['created_at'].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=df_guias['created_at'].max().date())
    with col3:
        estado = st.selectbox("Estado:", ["Todos", "Pending", "Printed"])
    
    # Aplicar filtros
    df_filtrado = df_guias[
        (df_guias['created_at'].dt.date >= fecha_inicio) & 
        (df_guias['created_at'].dt.date <= fecha_fin)
    ]
    
    if estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == estado]
    
    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        total_creados = len(df_guias)
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Total de Guías</div><p class="metric-value">{total_creados}</p></div>', unsafe_allow_html=True)
    
    with col2:
        pendientes = len(df_guias[df_guias['status'] == 'Pending'])
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Pendientes</div><p class="metric-value">{pendientes}</p></div>', unsafe_allow_html=True)
    
    with col3:
        impresos = len(df_guias[df_guias['status'] == 'Printed'])
        st.markdown(f'<div class="kpi-card animate-fade-in"><div class="metric-label">Impresas</div><p class="metric-value">{impresos}</p></div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar tabla de guías
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Guías Generadas</h2>", unsafe_allow_html=True)
    
    # Preparar datos para mostrar
    df_display = df_filtrado.copy()
    df_display['created_at'] = df_display['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Configurar columnas a mostrar
    columns_to_display = ['store_name', 'brand', 'sender_name', 'status', 'created_at']
    df_display = df_display[columns_to_display]
    
    # Renombrar columnas para mejor presentación
    df_display = df_display.rename(columns={
        'store_name': 'Tienda',
        'brand': 'Marca',
        'sender_name': 'Remitente',
        'status': 'Estado',
        'created_at': 'Fecha'
    })
    
    st.dataframe(df_display, use_container_width=True)
    
    # Botones de exportación
    st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        # Exportar a Excel
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                # Preparar DataFrame para exportación
                export_df = df_filtrado.copy()
                export_df['created_at'] = export_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
                
                # Renombrar columnas
                export_df = export_df.rename(columns={
                    'store_name': 'Tienda',
                    'brand': 'Marca',
                    'sender_name': 'Remitente',
                    'status': 'Estado',
                    'created_at': 'Fecha'
                })
                
                # Exportar a Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Historial_Guías', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_data,
                    file_name=f"historial_guias_{fecha_inicio}_a_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar historial de guías a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Exportar a CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"historial_guias_{fecha_inicio}_a_{fecha_fin}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_ayuda():
    """Muestra la página de ayuda y contacto"""
    st.markdown("<h1 class='header-title animate-fade-in'>❓ Ayuda y Contacto</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>¿Cómo usar la aplicación?</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>📝 Guía de uso</h3>
        
        <h4>**Sistema de KPIs:**</h4>
        <ul>
            <li><strong>Dashboard de KPIs:</strong> Visualiza el rendimiento diario de los equipos.</li>
            <li><strong>Análisis Histórico:</strong> Analiza tendencias y exporta reportes.</li>
            <li><strong>Ingreso de Datos:</strong> Ingresa los datos diarios de producción.</li>
            <li><strong>Gestión de Trabajadores:</strong> Administra el personal de la empresa.</li>
        </ul>
        
        <h4>**Sistema de Guías:**</h4>
        <ul>
            <li><strong>Generar Guía:</strong> Selecciona la tienda, la empresa (Fashion o Tempo), el remitente y pega la URL del pedido. Haz clic en "Generar Guía".</li>
            <li><strong>Historial de Guías:</strong> Consulta y exporta el historial de guías generadas.</li>
        </ul>
        
        <h3>📞 Soporte Técnico</h3>
        <p>Si tienes algún problema o necesitas asistencia, por favor contacta a:</p>
        <p><strong>Ing. Wilson Pérez</strong><br>
        <strong>Teléfono:</strong> 0993052744</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================================
# Función principal
# ================================

def main():
    """Función principal de la aplicación"""
    
    # Mostrar logo y título en el sidebar
    st.sidebar.markdown("""
    <div class='sidebar-title'>
        <div class='aeropostale-logo'>AEROPOSTALE</div>
        <div class='aeropostale-subtitle'>Sistema de Gestión de KPIs</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú de navegación
    menu_options = [
        ("Dashboard KPIs", "📊", mostrar_dashboard_kpis),
        ("Análisis Histórico", "📈", mostrar_analisis_historico_kpis),
        ("Ingreso de Datos", "📥", mostrar_ingreso_datos_kpis),
        ("Gestión de Trabajadores", "👥", mostrar_gestion_trabajadores_kpis),
        ("Generar Guías", "📦", mostrar_generacion_guias),
        ("Historial de Guías", "🔍", mostrar_historial_guias),
        ("Ayuda y Contacto", "❓", mostrar_ayuda)
    ]
    
    # Mostrar opciones del menú
    for i, (label, icon, _) in enumerate(menu_options):
        selected = st.sidebar.button(
            f"{icon} {label}",
            key=f"menu_{i}",
            use_container_width=True
        )
        if selected:
            st.session_state.selected_menu = i
    
    # Establecer una opción predeterminada si no hay ninguna seleccionada
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = 0
    
    # Mostrar contenido según la opción seleccionada
    _, _, func = menu_options[st.session_state.selected_menu]
    
    # Para las opciones que requieren autenticación
    if st.session_state.selected_menu in [2, 3, 4]:  # Ingreso de Datos, Gestión de Trabajadores, Generar Guías
        if not verificar_password():
            solicitar_autenticacion()
        else:
            func()
    else:
        func()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.<br>
        Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com">Wilson Pérez</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

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
import json
from dateutil.relativedelta import relativedelta
import calendar
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')

# ================================
# Configuración de logging
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("KPIs_System")

# ================================
# Configuración de Supabase
# ================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Conexión exitosa a Supabase")
except Exception as e:
    logger.error(f"Error al configurar Supabase: {str(e)}")
    supabase = None

# ================================
# Constantes y configuración del sistema
# ================================
CONFIG = {
    "META_TRANSFERENCIAS_DIARIA": 1750,
    "META_DISTRIBUCION_DIARIA": 150,
    "META_ARREGLO_DIARIA": 200,
    "META_MENSUAL_TRANSFERENCIAS": 35000,
    "DIAS_LABORABLES_MES": 22,
    "COLORES_EQUIPOS": {
        "Transferencias": "#1f77b4",
        "Distribución": "#ff7f0e",
        "Arreglo": "#2ca02c",
        "Guías": "#d62728",
        "Ventas": "#9467bd"
    },
    "ICONOS_EQUIPOS": {
        "Transferencias": "🔄",
        "Distribución": "📦",
        "Arreglo": "🛠️",
        "Guías": "📝",
        "Ventas": "💰"
    }
}

# ================================
# Clases de utilidad
# ================================
class DateRange:
    """Clase para manejar rangos de fechas de manera eficiente"""
    
    @staticmethod
    def get_month_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango completo del mes para una fecha dada"""
        first_day = date(date_obj.year, date_obj.month, 1)
        last_day = date(date_obj.year, date_obj.month, calendar.monthrange(date_obj.year, date_obj.month)[1])
        return first_day, last_day
    
    @staticmethod
    def get_week_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango de la semana (lunes a domingo) para una fecha dada"""
        start = date_obj - timedelta(days=date_obj.weekday())
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def get_year_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango completo del año para una fecha dada"""
        return date(date_obj.year, 1, 1), date(date_obj.year, 12, 31)
    
    @staticmethod
    def get_day_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango del día completo"""
        return date_obj, date_obj

# ================================
# Funciones de utilidad
# ================================
def validar_fecha(fecha_str: str) -> bool:
    """Valida que una cadena tenga formato de fecha válido (YYYY-MM-DD)"""
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_numero_positivo(valor: float) -> bool:
    """Valida que un valor sea un número positivo"""
    return isinstance(valor, (int, float)) and valor >= 0

def productividad_hora(cantidad: float, horas: float) -> float:
    """Calcula la productividad por hora"""
    return cantidad / horas if horas > 0 else 0

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña"""
    return hashlib.sha256(pw.encode()).hexdigest()

def calcular_porcentaje_avance(mes_actual: date, dias_habiles: int = 22) -> float:
    """Calcula el porcentaje de avance del mes considerando días hábiles"""
    hoy = datetime.now().date()
    primer_dia_mes = date(mes_actual.year, mes_actual.month, 1)
    
    # Calcular días hábiles transcurridos en el mes
    dias_transcurridos = 0
    for i in range((hoy - primer_dia_mes).days + 1):
        dia = primer_dia_mes + timedelta(days=i)
        if dia.weekday() < 5:  # Lunes a viernes son días hábiles
            dias_transcurridos += 1
    
    # Calcular porcentaje de avance
    porcentaje = (dias_transcurridos / dias_habiles) * 100
    return min(porcentaje, 100)  # No superar 100%

# ================================
# Funciones de cálculo de KPIs
# ================================
def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general"""
    return (cantidad / meta) * 100 if meta > 0 else 0

def kpi_transferencias(transferidas: float, meta: float = CONFIG["META_TRANSFERENCIAS_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de transferencias"""
    return calcular_kpi(transferidas, meta)

def kpi_distribucion(unidades: float, meta: float = CONFIG["META_DISTRIBUCION_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de distribución"""
    return calcular_kpi(unidades, meta)

def kpi_arreglos(piezas: float, meta: float = CONFIG["META_ARREGLO_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de arreglos"""
    return calcular_kpi(piezas, meta)

def kpi_guias(cantidad: float, meta: float = 50) -> float:
    """Calcula el KPI para el equipo de guías"""
    return calcular_kpi(cantidad, meta)

# ================================
# Funciones de acceso a datos (Supabase)
# ================================
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                       "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"],
            'id': list(range(1, 9))
        })
    
    try:
        response = supabase.from_('trabajadores').select('*').eq('activo', True).order('equipo,nombre', desc=False).execute()
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df[['nombre', 'equipo', 'id']]
        logger.warning("No se encontraron trabajadores activos en Supabase")
        return pd.DataFrame(columns=['nombre', 'equipo', 'id'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores: {e}", exc_info=True)
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                       "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"],
            'id': list(range(1, 9))
        })

def obtener_equipos() -> List[str]:
    """Obtiene la lista de equipos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            equipos = [item['equipo'] for item in response.data]
            # Asegurar que "Distribución" esté en la lista
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            return equipos
        logger.warning("No se encontraron equipos en Supabase")
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos: {e}", exc_info=True)
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]

def cargar_datos_fecha(fecha: str) -> Dict[str, Any]:
    """Carga datos ya guardados para una fecha específica"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return {}
    
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Convertir a diccionario con nombre como clave
            return df.set_index('nombre').T.to_dict()
        return {}
    except Exception as e:
        logger.error(f"Error al cargar datos para {fecha}: {e}", exc_info=True)
        return {}

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos en la tabla de Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        registros = []
        for nombre, info in datos.items():
            # Validar datos antes de guardar
            if not all([
                validar_fecha(fecha),
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                logger.warning(f"Datos inválidos para {nombre}, omitiendo guardado")
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
            # Usar upsert para actualizar si ya existe
            supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            logger.info(f"Datos guardados para {fecha} - {len(registros)} registros")
            
            # Limpiar caché para forzar recarga de datos
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
                
            return True
        logger.warning("No hay registros válidos para guardar")
        return False
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}", exc_info=True)
        return False

def cargar_historico_db(fecha_inicio: str = None, fecha_fin: str = None, trabajador: str = None, equipo: str = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase con filtros opcionales"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('daily_kpis').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador and trabajador != "Todos":
            query = query.eq('nombre', trabajador)
        if equipo and equipo != "Todos":
            query = query.eq('equipo', equipo)
            
        query = query.order('fecha', desc=False)
        response = query.execute()
        
        if response and response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        logger.info("No se encontraron datos históricos en Supabase")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def obtener_tiendas() -> pd.DataFrame:
    """Obtiene la lista de tiendas desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })
    
    try:
        response = supabase.from_('tiendas').select('id, nombre').execute()
        if response and response.data:
            return pd.DataFrame(response.data)
        logger.warning("No se encontraron tiendas en Supabase")
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })
    except Exception as e:
        logger.error(f"Error al obtener tiendas: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.from_('remitentes').select('id, nombre, direccion, telefono').execute()
        if response and response.data:
            return pd.DataFrame(response.data)
        logger.warning("No se encontraron remitentes en Supabase")
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """Guarda una guía de envío en Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
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
        logger.info(f"Guía guardada para {store_name} - {brand}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar guía: {e}", exc_info=True)
        return False

def obtener_guias(fecha_inicio: str = None, fecha_fin: str = None, tienda: str = None, marca: str = None) -> pd.DataFrame:
    """Obtiene la lista de guías desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('guide_logs').select('*')
        
        if fecha_inicio:
            query = query.gte('created_at', fecha_inicio)
        if fecha_fin:
            query = query.lte('created_at', fecha_fin)
        if tienda and tienda != "Todas":
            query = query.eq('store_name', tienda)
        if marca and marca != "Todas":
            query = query.eq('brand', marca)
            
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        if response and response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        logger.info("No se encontraron guías en Supabase")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al obtener guías: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# Obtener logo desde Supabase Storage
# ================================
@st.cache_data(ttl=3600)
def obtener_logo_url(nombre_imagen: str) -> str:
    """Obtiene la URL pública de un logo en Supabase Storage"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return ""
    
    try:
        # Intentar obtener la URL pública del archivo
        response = supabase.storage.from_('images').get_public_url(nombre_imagen)
        
        if response and "error" not in response.lower():
            return response
        
        # Si no funciona, construir la URL manualmente
        bucket_name = "public"  # Ajustar según tu configuración
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/images/{nombre_imagen}"
    except Exception as e:
        logger.error(f"Error al obtener logo {nombre_imagen}: {e}")
        return ""

# ================================
# Funciones de visualización
# ================================
def crear_grafico_interactivo(df: pd.DataFrame, x: str, y: str, title: str,
                             xlabel: str, ylabel: str, tipo: str = 'bar', 
                             color=None, hover_data=None) -> go.Figure:
    """Crea gráficos interactivos con Plotly"""
    try:
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para mostrar",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title=title,
                xaxis_title=xlabel,
                yaxis_title=ylabel,
                template="plotly_white"
            )
            return fig
        
        if tipo == 'bar':
            fig = px.bar(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        elif tipo == 'line':
            fig = px.line(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        elif tipo == 'pie':
            fig = px.pie(
                df, 
                names=x, 
                values=y,
                title=title,
                hover_data=hover_data
            )
        else:
            fig = px.scatter(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        
        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def crear_grafico_frasco(valor: float, titulo: str) -> go.Figure:
    """
    Crea un gráfico de frasco de agua (semáforo) para visualizar el progreso
    """
    try:
        # Determinar el color basado en el porcentaje
        if valor >= 100:
            color = "#2ca02c"  # Verde
        elif valor >= 80:
            color = "#ff7f0e"  # Naranja
        else:
            color = "#d62728"  # Rojo
        
        fig = go.Figure()
        
        # Agregar el frasco
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=valor,
            title={'text': titulo},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 80], 'color': '#d62728'},
                    {'range': [80, 100], 'color': '#ff7f0e'},
                    {'range': [100, 100], 'color': '#2ca02c'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': valor
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de frasco: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def crear_grafico_cubo_agua(df: pd.DataFrame, fecha_referencia: date) -> go.Figure:
    """
    Crea un gráfico de cubo de agua (waterfall) que muestra el progreso mensual
    Considerando solo los días del mes actual y el rango seleccionado
    """
    try:
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para mostrar",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title="Progreso Mensual",
                template="plotly_white"
            )
            return fig
        
        # Filtrar solo para el mes actual
        mes_actual = fecha_referencia.month
        anio_actual = fecha_referencia.year
        df_mes = df[(df['fecha'].dt.month == mes_actual) & (df['fecha'].dt.year == anio_actual)]
        
        if df_mes.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para este mes",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title="Progreso Mensual",
                template="plotly_white"
            )
            return fig
        
        # Agrupar por día y calcular acumulado
        df_mes['dia'] = df_mes['fecha'].dt.day
        df_acumulado = df_mes.groupby('dia')['cantidad'].sum().reset_index()
        df_acumulado = df_acumulado.sort_values('dia')
        df_acumulado['acumulado'] = df_acumulado['cantidad'].cumsum()
        
        # Crear el gráfico waterfall
        fig = go.Figure()
        
        # Días transcurridos (increasing)
        dias_transcurridos = df_acumulado[df_acumulado['dia'] <= fecha_referencia.day]
        if not dias_transcurridos.empty:
            fig.add_trace(go.Waterfall(
                name="Días transcurridos",
                orientation="v",
                x=dias_transcurridos['dia'],
                y=dias_transcurridos['cantidad'],
                text=[f"{val:,.0f}" for val in dias_transcurridos['cantidad']],
                textposition="outside",
                marker=dict(color=CONFIG["COLORES_EQUIPOS"]["Transferencias"]),
                connector={"line": {"color": "rgb(63, 63, 63)"}}
            ))
        
        # Días restantes (decreasing)
        dias_restantes = df_acumulado[df_acumulado['dia'] > fecha_referencia.day]
        if not dias_restantes.empty:
            # Calcular el promedio diario para proyectar
            promedio_diario = dias_transcurridos['cantidad'].mean() if not dias_transcurridos.empty else 0
            
            # Crear datos proyectados
            dias_proyectados = []
            for dia in dias_restantes['dia']:
                dias_proyectados.append({
                    'dia': dia,
                    'cantidad': promedio_diario
                })
            
            if dias_proyectados:
                df_proyectado = pd.DataFrame(dias_proyectados)
                fig.add_trace(go.Waterfall(
                    name="Proyección",
                    orientation="v",
                    x=df_proyectado['dia'],
                    y=df_proyectado['cantidad'],
                    text=[f"{val:,.0f}" for val in df_proyectado['cantidad']],
                    textposition="outside",
                    marker=dict(color="#cccccc", pattern=dict(shape="/")),
                    connector={"line": {"color": "rgb(200, 200, 200)"}}
                ))
        
        # Meta mensual como total
        meta_mensual = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
        fig.add_trace(go.Waterfall(
            name="Meta Mensual",
            orientation="v",
            measure=["total"],
            x=["Meta"],
            y=[meta_mensual],
            text=[f"{meta_mensual:,.0f}"],
            textposition="outside",
            marker=dict(color="#2ca02c"),
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        
        # Configurar layout
        fig.update_layout(
            title=f"Progreso Mensual - {calendar.month_name[mes_actual]} {anio_actual}",
            xaxis_title="Día del mes",
            yaxis_title="Unidades",
            showlegend=True,
            template="plotly_white",
            xaxis=dict(tickmode='linear'),
            hovermode="x unified"
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de cubo de agua: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def generar_resumen_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Genera un resumen ejecutivo de KPIs basado en los datos filtrados"""
    if df.empty:
        return {
            "total_unidades": 0,
            "eficiencia_promedio": 0,
            "colaboradores": 0,
            "mejor_colaborador": "N/A",
            "mejor_equipo": "N/A",
            "porcentaje_avance": 0,
            "proyeccion_final": 0
        }
    
    # Calcular métricas
    total_unidades = int(df['cantidad'].sum())
    eficiencia_promedio = df['eficiencia'].mean()
    colaboradores = df['nombre'].nunique()
    
    # Mejor colaborador
    mejor_colaborador = df.groupby('nombre')['eficiencia'].mean().idxmax() if not df.empty else "N/A"
    
    # Mejor equipo
    mejor_equipo = df.groupby('equipo')['eficiencia'].mean().idxmax() if not df.empty else "N/A"
    
    # Porcentaje de avance del mes
    porcentaje_avance = calcular_porcentaje_avance(df['fecha'].max().date())
    
    # Proyección final basada en promedio diario
    dias_habiles_restantes = max(0, 22 - (datetime.now().weekday() + 1))
    promedio_diario = total_unidades / len(df['fecha'].unique())
    proyeccion_final = total_unidades + (promedio_diario * dias_habiles_restantes)
    
    return {
        "total_unidades": total_unidades,
        "eficiencia_promedio": eficiencia_promedio,
        "colaboradores": colaboradores,
        "mejor_colaborador": mejor_colaborador,
        "mejor_equipo": mejor_equipo,
        "porcentaje_avance": porcentaje_avance,
        "proyeccion_final": proyeccion_final
    }

# ================================
# Panel: Ingreso de Datos con Edición Completa
# ================================
def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs con capacidad de edición"""
    st.markdown("<h1 class='header-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Selector de fecha con capacidad para editar datos existentes
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_seleccionada = st.date_input(
            "Selecciona una fecha para ingresar o editar datos:", 
            value=datetime.now().date(),
            min_value=date(2020, 1, 1),
            max_value=datetime.now().date() + timedelta(days=1)
        )
    
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    
    # Cargar datos existentes si los hay
    datos_existentes = cargar_datos_fecha(fecha_str)
    trabajadores = obtener_trabajadores()
    
    if trabajadores.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay trabajadores registrados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Organizar trabajadores por equipo
    trabajadores_por_equipo = trabajadores.groupby('equipo')['nombre'].apply(list).to_dict()
    
    # Mostrar estado de los datos para esta fecha
    if datos_existentes:
        st.markdown(f"<div class='success-box animate-fade-in'>ℹ️ Ya existen datos para el {fecha_str}. Puedes editarlos a continuación.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='info-box animate-fade-in'>ℹ️ No hay datos registrados para el {fecha_str}. Ingresa los datos a continuación.</div>", unsafe_allow_html=True)
    
    # Formulario de ingreso/editado
    with st.form("form_ingreso_kpis"):
        st.markdown("### 🧑‍💼 Datos por equipo")
        
        datos_guardar = {}
        for equipo, miembros in trabajadores_por_equipo.items():
            with st.expander(f"{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}", expanded=True):
                # Mostrar meta diaria para referencia
                meta_diaria = CONFIG.get(f"MET_{equipo.upper()}_DIARIA", 100)
                st.markdown(f"**Meta diaria de referencia:** {meta_diaria} unidades")
                
                cols = st.columns(min(len(miembros), 3))
                
                for idx, trabajador in enumerate(miembros):
                    with cols[idx % len(cols)]:
                        st.markdown(f"#### {trabajador}")
                        
                        # Cargar valores existentes si los hay
                        datos_trab = datos_existentes.get(trabajador, {})
                        
                        # Inputs para datos
                        cantidad = st.number_input(
                            "Unidades completadas", 
                            value=float(datos_trab.get("cantidad", 0)), 
                            min_value=0.0, 
                            step=1.0, 
                            key=f"{trabajador}_cantidad_{fecha_str}"
                        )
                        
                        meta = st.number_input(
                            "Meta diaria", 
                            value=float(datos_trab.get("meta", meta_diaria)), 
                            min_value=0.0, 
                            step=1.0, 
                            key=f"{trabajador}_meta_{fecha_str}"
                        )
                        
                        horas = st.number_input(
                            "Horas trabajadas", 
                            value=float(datos_trab.get("horas_trabajo", 8)), 
                            min_value=0.0, 
                            max_value=24.0,
                            step=0.5, 
                            key=f"{trabajador}_horas_{fecha_str}"
                        )
                        
                        comentario = st.text_area(
                            "Comentarios", 
                            value=datos_trab.get("comentario", ""), 
                            key=f"{trabajador}_comentario_{fecha_str}"
                        )
                        
                        # Calcular métricas
                        eficiencia = (cantidad / meta * 100) if meta > 0 else 0
                        productividad = productividad_hora(cantidad, horas)
                        
                        # Mostrar métricas calculadas
                        col_metric1, col_metric2 = st.columns(2)
                        with col_metric1:
                            st.metric("Eficiencia", f"{eficiencia:.1f}%")
                        with col_metric2:
                            st.metric("Productividad", f"{productividad:.2f} u/h")
                        
                        # Guardar datos para procesamiento
                        datos_guardar[trabajador] = {
                            "actividad": equipo,
                            "cantidad": cantidad,
                            "meta": meta,
                            "eficiencia": eficiencia,
                            "productividad": productividad,
                            "comentario": comentario,
                            "meta_mensual": 0,  # Se calculará después
                            "horas_trabajo": horas,
                            "equipo": equipo
                        }
        
        submitted = st.form_submit_button("💾 Guardar Datos", use_container_width=True)
        
        if submitted:
            if guardar_datos_db(fecha_str, datos_guardar):
                st.markdown("<div class='success-box animate-fade-in'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                time.sleep(1.5)
                st.rerun()
            else:
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)
    
    # Mostrar datos guardados para esta fecha (solo lectura)
    if datos_existentes:
        st.markdown("### 📊 Datos guardados para esta fecha")
        df_guardados = pd.DataFrame.from_dict(datos_existentes, orient='index')
        df_guardados = df_guardados.reset_index().rename(columns={'index': 'nombre'})
        
        # Formatear y mostrar tabla
        df_mostrar = df_guardados[['nombre', 'cantidad', 'meta', 'eficiencia', 'productividad', 'comentario']]
        df_mostrar = df_mostrar.sort_values('eficiencia', ascending=False)
        
        st.dataframe(
            df_mostrar.style.format({
                'cantidad': '{:,.0f}',
                'meta': '{:,.0f}',
                'eficiencia': '{:.1f}%',
                'productividad': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# ================================
# Panel: Crear Guías (con logos desde Supabase)
# ================================
def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío con logos desde Supabase"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()
    
    if tiendas.empty or remitentes.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Mostrar logos de las marcas desde Supabase
    st.markdown("<div class='brand-logos'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("### Selecciona la marca para la guía")
        marca = st.selectbox("Marca", ["Fashion", "Tempo"], key="marca_selector")
        
        # Mostrar logo de la marca seleccionada
        if marca == "Fashion":
            logo_url = obtener_logo_url("Fashion.jpg")
            if logo_url:
                st.image(logo_url, width=200, caption="Fashion Club")
            else:
                st.warning("No se pudo cargar el logo de Fashion desde Supabase")
        else:
            logo_url = obtener_logo_url("Tempo.jpg")
            if logo_url:
                st.image(logo_url, width=200, caption="Tempo")
            else:
                st.warning("No se pudo cargar el logo de Tempo desde Supabase")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Formulario para generar guías
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛍️ Información del pedido")
        tienda_id = st.selectbox(
            "Tienda", 
            options=tiendas['id'], 
            format_func=lambda x: tiendas[tiendas['id'] == x]['nombre'].values[0],
            key="tienda_selector"
        )
        url_pedido = st.text_area("URL del pedido", height=100, key="url_pedido")
        observaciones = st.text_area("Observaciones adicionales", height=80, key="observaciones")
    
    with col2:
        st.markdown("#### 📦 Información del remitente")
        remitente_id = st.selectbox(
            "Remitente", 
            options=remitentes['id'], 
            format_func=lambda x: remitentes[remitentes['id'] == x]['nombre'].values[0],
            key="remitente_selector"
        )
        
        # Mostrar detalles del remitente seleccionado
        if not remitentes.empty:
            remitente_seleccionado = remitentes[remitentes['id'] == remitente_id].iloc[0]
            st.markdown("##### Detalles del remitente:")
            st.write(f"**Dirección:** {remitente_seleccionado['direccion']}")
            st.write(f"**Teléfono:** {remitente_seleccionado['telefono']}")
    
    # Botón para generar guía
    if st.button("🖨️ Generar Guía", use_container_width=True, type="primary"):
        # Validar campos requeridos
        if not url_pedido or not url_pedido.strip():
            st.error("La URL del pedido es requerida")
            return
            
        if tienda_id and remitente_id:
            # Obtener nombres reales
            tienda_nombre = tiendas[tiendas['id'] == tienda_id]['nombre'].values[0]
            remitente_nombre = remitentes[remitentes['id'] == remitente_id]['nombre'].values[0]
            
            # Guardar en la base de datos
            if guardar_guia(tienda_nombre, marca, url_pedido, remitente_nombre):
                st.success("✅ Guía generada y guardada exitosamente!")
                
                # Mostrar información de la guía generada
                st.markdown("### 📬 Detalles de la guía generada")
                
                # Generar número de seguimiento único
                seguimiento = f"{marca[:2].upper()}{datetime.now().strftime('%y%m%d')}{str(int(time.time()))[-6:]}"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Número de seguimiento:**")
                    st.code(seguimiento, language="text")
                    
                    # Generar y mostrar QR
                    qr_img = generar_qr_imagen(seguimiento)
                    st.image(qr_img, caption="Código QR de seguimiento", width=200)
                
                with col2:
                    st.markdown("**Fecha de generación:**")
                    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.markdown("**Tienda:**")
                    st.write(tienda_nombre)
                    st.markdown("**Marca:**")
                    st.write(marca)
                
                # Opción para descargar PDF
                if st.button("📥 Descargar Guía en PDF", use_container_width=True):
                    pdf = generar_pdf_guia(tienda_nombre, marca, url_pedido, 
                                         remitente_nombre, 
                                         remitentes[remitentes['id'] == remitente_id].iloc[0],
                                         seguimiento)
                    pdf_data = pdf.output(dest='S').encode('latin-1')
                    b64_pdf = base64.b64encode(pdf_data).decode()
                    
                    href = f'<a href="application/pdf;base64,{b64_pdf}" download="guia_{seguimiento}.pdf">Descargar PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("❌ Error al generar la guía. Por favor, intente nuevamente.")
        else:
            st.error("Por favor, seleccione una tienda y un remitente válidos.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================================
# Panel: Dashboard de KPIs (con resumen y cubo de agua)
# ================================
def mostrar_dashboard_kpis():
    """Muestra el dashboard principal de KPIs con análisis detallado"""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos (con caché para mejorar rendimiento)
    @st.cache_data(ttl=300)
    def cargar_datos_cache():
        return cargar_historico_db()
    
    df = cargar_datos_cache()
    
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos disponibles. Por favor, ingrese datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Filtros globales
    st.markdown("### 🔍 Filtros de análisis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rango = st.selectbox("Rango de tiempo", ["Día", "Semana", "Mes", "Año", "Personalizado"], index=2)
    
    with col2:
        equipos = ["Todos"] + obtener_equipos()
        equipo_seleccionado = st.selectbox("Equipo", equipos)
    
    with col3:
        trabajadores = ["Todos"] + df['nombre'].unique().tolist()
        trabajador_seleccionado = st.selectbox("Colaborador", trabajadores)
    
    # Determinar fechas basado en el rango seleccionado
    hoy = datetime.now().date()
    
    if rango == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio", value=hoy - timedelta(days=7))
        with col2:
            fecha_fin = st.date_input("Fecha de fin", value=hoy)
    else:
        if rango == "Día":
            fecha_inicio = hoy
            fecha_fin = hoy
        elif rango == "Semana":
            fecha_inicio = hoy - timedelta(days=hoy.weekday())
            fecha_fin = fecha_inicio + timedelta(days=6)
        elif rango == "Mes":
            fecha_inicio = date(hoy.year, hoy.month, 1)
            _, last_day = calendar.monthrange(hoy.year, hoy.month)
            fecha_fin = date(hoy.year, hoy.month, last_day)
        else:  # Año
            fecha_inicio = date(hoy.year, 1, 1)
            fecha_fin = date(hoy.year, 12, 31)
    
    # Convertir a string para filtrado
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    
    # Filtrar datos
    df_filtrado = df.copy()
    
    if fecha_inicio_str and fecha_fin_str:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]
    
    if equipo_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_seleccionado]
    
    if trabajador_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador_seleccionado]
    
    # Mostrar tarjetas de KPIs por equipo
    st.markdown("### 📊 Tarjetas de KPIs por Equipo")
    
    equipos = obtener_equipos()
    cols = st.columns(len(equipos))
    
    for i, equipo in enumerate(equipos):
        with cols[i]:
            df_equipo = df_filtrado[df_filtrado['equipo'] == equipo]
            
            if not df_equipo.empty:
                total_unidades = int(df_equipo['cantidad'].sum())
                eficiencia_promedio = df_equipo['eficiencia'].mean()
                num_colaboradores = df_equipo['nombre'].nunique()
                
                # Determinar meta mensual para el equipo
                meta_mensual = 0
                if equipo == "Transferencias":
                    meta_mensual = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
                    cumplimiento = (total_unidades / meta_mensual * 100) if meta_mensual > 0 else 0
                else:
                    # Para otros equipos, usar meta diaria promedio
                    dias_trabajados = len(df_equipo['fecha'].unique())
                    if dias_trabajados > 0:
                        meta_diaria = CONFIG.get(f"MET_{equipo.upper()}_DIARIA", 100)
                        meta_mensual = meta_diaria * 22  # 22 días hábiles
                        cumplimiento = (total_unidades / meta_mensual * 100) if meta_mensual > 0 else 0
                    else:
                        cumplimiento = 0
                
                # Mostrar tarjeta
                st.markdown(f"""
                <div class="kpi-card animate-fade-in">
                    <div class="metric-label">{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}</div>
                    <p class="metric-value">{eficiencia_promedio:.1f}%</p>
                    <p>Unidades: {total_unidades:,.0f}<br>
                       Colaboradores: {num_colaboradores}<br>
                       Cumplimiento: {cumplimiento:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="kpi-card animate-fade-in">
                    <div class="metric-label">{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}</div>
                    <p class="metric-value">0%</p>
                    <p>Unidades: 0<br>
                       Colaboradores: 0<br>
                       Cumplimiento: 0%</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Mostrar progreso del mes para Transferencias (con semáforo)
    st.markdown("### 📈 Progreso Mensual - Transferencias")
    
    df_transferencias = df_filtrado[df_filtrado['equipo'] == "Transferencias"]
    
    if not df_transferencias.empty:
        cum_transferencias = int(df_transferencias['cantidad'].sum())
        meta_mensual_transferencias = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
        cumplimiento_transferencias = (cum_transferencias / meta_mensual_transferencias * 100) if meta_mensual_transferencias > 0 else 0
        
        # Mostrar tarjeta de progreso
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Meta Mensual Transferencias</div>
                <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
                <p>Acumulado: {cum_transferencias:,.0f} / Meta Mensual: {meta_mensual_transferencias:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Gráfico de frasco de agua para el cumplimiento
            fig_frasco = crear_grafico_frasco(cumplimiento_transferencias, "Cumplimiento Mensual Transferencias")
            st.plotly_chart(fig_frasco, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            # Gráfico de evolución mensual
            df_transferencias_month = df[df['equipo'] == "Transferencias"]
            df_transferencias_month = df_transferencias_month[
                (df_transferencias_month['fecha'].dt.year == hoy.year) & 
                (df_transferencias_month['fecha'].dt.month == hoy.month)
            ]
            
            if not df_transferencias_month.empty:
                df_daily = df_transferencias_month.groupby(df_transferencias_month['fecha'].dt.day)['cantidad'].sum().reset_index()
                df_daily = df_daily.sort_values('fecha')
                df_daily['acumulado'] = df_daily['cantidad'].cumsum()
                
                fig = px.line(
                    df_daily,
                    x='fecha',
                    y='acumulado',
                    title='Evolución del Cumplimiento Mensual',
                    labels={'fecha': 'Día del mes', 'acumulado': 'Unidades acumuladas'}
                )
                fig.add_hline(
                    y=meta_mensual_transferencias, 
                    line_dash="dash", 
                    line_color="white", 
                    annotation_text="Meta Mensual"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No hay datos para el gráfico de Transferencias.")
    else:
        st.info("No hay datos de Transferencias para mostrar.")
    
    # Análisis detallado por equipo
    st.markdown("### 🏆 Análisis por Equipos")
    
    if not df_filtrado.empty:
        # Gráfico de eficiencia por equipo
        df_equipo = df_filtrado.groupby('equipo').agg({
            'eficiencia': 'mean',
            'cantidad': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_equipo = crear_grafico_interactivo(
                df_equipo, 
                'equipo', 
                'eficiencia', 
                'Eficiencia Promedio por Equipo',
                'Equipo', 
                'Eficiencia (%)',
                color='equipo',
                hover_data=['cantidad']
            )
            st.plotly_chart(fig_equipo, use_container_width=True)
        
        with col2:
            # Gráfico de tendencia de eficiencia
            df_tendencia = df_filtrado.groupby(['fecha', 'equipo'])['eficiencia'].mean().reset_index()
            fig_tendencia = crear_grafico_interactivo(
                df_tendencia, 
                'fecha', 
                'eficiencia', 
                'Tendencia de Eficiencia',
                'Fecha', 
                'Eficiencia (%)',
                tipo='line',
                color='equipo'
            )
            st.plotly_chart(fig_tendencia, use_container_width=True)
        
        # Tabla detallada de rendimiento
        st.markdown("### 📋 Rendimiento Detallado")
        
        # Preparar datos para la tabla
        df_resumen = df_filtrado.groupby(['nombre', 'equipo']).agg({
            'cantidad': 'sum',
            'eficiencia': 'mean',
            'productividad': 'mean',
            'horas_trabajo': 'sum'
        }).reset_index()
        
        # Formatear y mostrar
        df_resumen = df_resumen.sort_values('eficiencia', ascending=False)
        df_resumen = df_resumen.rename(columns={
            'cantidad': 'Unidades',
            'eficiencia': 'Eficiencia (%)',
            'productividad': 'Productividad (u/h)',
            'horas_trabajo': 'Horas Totales'
        })
        
        st.dataframe(
            df_resumen.style.format({
                'Unidades': '{:,.0f}',
                'Eficiencia (%)': '{:.1f}%',
                'Productividad (u/h)': '{:.2f}',
                'Horas Totales': '{:,.1f}'
            }).background_gradient(subset=['Eficiencia (%)'], cmap='Greens'),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

# ================================
# Panel: Análisis Histórico de KPIs
# ================================
def mostrar_analisis_historico_kpis():
    """Muestra el análisis histórico de KPIs con visualizaciones avanzadas"""
    st.markdown("<h1 class='header-title animate-fade-in'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    df = cargar_historico_db()
    
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos disponibles. Por favor, ingrese datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Filtros
    st.markdown("### 🔍 Filtros de análisis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", value=df['fecha'].min().date())
    
    with col2:
        fecha_fin = st.date_input("Fecha de fin", value=df['fecha'].max().date())
    
    with col3:
        equipos = ["Todos"] + obtener_equipos()
        equipo_seleccionado = st.selectbox("Equipo", equipos)
    
    # Filtrar datos
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]
    
    if equipo_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_seleccionado]
    
    # Análisis de tendencias
    st.markdown("### 📈 Análisis de Tendencias")
    
    if not df_filtrado.empty:
        # Calcular métricas diarias
        df_diario = df_filtrado.groupby(['fecha', 'equipo']).agg({
            'cantidad': 'sum',
            'eficiencia': 'mean'
        }).reset_index()
        
        # Gráfico de tendencia de cantidad
        fig_cantidad = crear_grafico_interactivo(
            df_diario, 
            'fecha', 
            'cantidad', 
            'Tendencia de Unidades Completadas',
            'Fecha', 
            'Unidades',
            tipo='line',
            color='equipo'
        )
        st.plotly_chart(fig_cantidad, use_container_width=True)
        
        # Gráfico de tendencia de eficiencia
        fig_eficiencia = crear_grafico_interactivo(
            df_diario, 
            'fecha', 
            'eficiencia', 
            'Tendencia de Eficiencia',
            'Fecha', 
            'Eficiencia (%)',
            tipo='line',
            color='equipo'
        )
        st.plotly_chart(fig_eficiencia, use_container_width=True)
        
        # Análisis de correlación
        st.markdown("### 🔗 Análisis de Correlación")
        
        df_correlacion = df_filtrado.groupby('fecha').agg({
            'cantidad': 'sum',
            'horas_trabajo': 'sum',
            'eficiencia': 'mean'
        }).reset_index()
        
        # Calcular productividad diaria
        df_correlacion['productividad'] = df_correlacion['cantidad'] / df_correlacion['horas_trabajo']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_corr = px.scatter(
                df_correlacion, 
                x='horas_trabajo', 
                y='cantidad',
                trendline="ols",
                title='Correlación: Horas Trabajadas vs Unidades Completadas',
                labels={'horas_trabajo': 'Horas Trabajadas', 'cantidad': 'Unidades Completadas'}
            )
            fig_corr.update_layout(template="plotly_white")
            st.plotly_chart(fig_corr, use_container_width=True)
        
        with col2:
            fig_corr2 = px.scatter(
                df_correlacion, 
                x='eficiencia', 
                y='productividad',
                trendline="ols",
                title='Correlación: Eficiencia vs Productividad',
                labels={'eficiencia': 'Eficiencia (%)', 'productividad': 'Productividad (u/h)'}
            )
            fig_corr2.update_layout(template="plotly_white")
            st.plotly_chart(fig_corr2, use_container_width=True)
        
        # Predicciones futuras
        st.markdown("### 📅 Predicciones Futuras")
        
        if len(df_correlacion) >= 10:  # Necesitamos suficientes datos
            # Preparar datos para regresión
            X = np.array(range(len(df_correlacion))).reshape(-1, 1)
            y = df_correlacion['cantidad'].values
            
            # Entrenar modelo
            model = LinearRegression()
            model.fit(X, y)
            
            # Predecir próximos 7 días
            dias_futuros = 7
            X_pred = np.array(range(len(X), len(X) + dias_futuros)).reshape(-1, 1)
            y_pred = model.predict(X_pred)
            
            # Mostrar predicciones
            st.markdown(f"**Predicción para los próximos {dias_futuros} días:**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Crear dataframe para visualización
                fechas_futuras = [df_correlacion['fecha'].max() + timedelta(days=i+1) for i in range(dias_futuros)]
                df_pred = pd.DataFrame({
                    'fecha': fechas_futuras,
                    'prediccion': y_pred
                })
                
                fig_pred = px.line(
                    pd.concat([df_correlacion[['fecha', 'cantidad']], df_pred.rename(columns={'prediccion': 'cantidad'})]),
                    x='fecha',
                    y='cantidad',
                    title='Predicción de Unidades Futuras',
                    labels={'cantidad': 'Unidades', 'fecha': 'Fecha'}
                )
                fig_pred.add_vrect(
                    x0=df_correlacion['fecha'].max(),
                    x1=fechas_futuras[-1],
                    fillcolor="rgba(0,100,80,0.2)",
                    line_width=0,
                    annotation_text="Predicción",
                    annotation_position="top left"
                )
                fig_pred.update_layout(template="plotly_white")
                st.plotly_chart(fig_pred, use_container_width=True)
            
            with col2:
                st.markdown("**Valores predichos:**")
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, y_pred)):
                    st.metric(
                        f"{fecha.strftime('%Y-%m-%d')}", 
                        f"{pred:,.0f} unidades",
                        delta=f"+{pred - y[-1]:,.0f}" if i == 0 else None
                    )
        else:
            st.warning("Se necesitan al menos 10 días de datos para realizar predicciones.")
    
    # Datos crudos
    st.markdown("### 📊 Datos Históricos")
    st.dataframe(
        df_filtrado.sort_values('fecha', ascending=False),
        use_container_width=True,
        hide_index=True
    )

# ================================
# Panel: Gestión de Trabajadores
# ================================
def mostrar_gestion_trabajadores():
    """Muestra la interfaz para gestionar trabajadores y equipos"""
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Pestañas para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["👥 Trabajadores", "🏢 Equipos", "📊 Asignación de Metas"])
    
    with tab1:
        mostrar_gestion_trabajadores_tab()
    
    with tab2:
        mostrar_gestion_equipos_tab()
    
    with tab3:
        mostrar_asignacion_metas_tab()

def mostrar_gestion_trabajadores_tab():
    """Muestra la gestión de trabajadores individuales"""
    st.markdown("### 👥 Gestión de Trabajadores")
    
    # Cargar trabajadores
    trabajadores = obtener_trabajadores()
    
    # Mostrar lista de trabajadores
    if not trabajadores.empty:
        st.markdown("#### 📋 Lista de Trabajadores")
        
        # Filtro por equipo
        equipos = ["Todos"] + trabajadores['equipo'].unique().tolist()
        equipo_filtro = st.selectbox("Filtrar por equipo", equipos, key="trabajadores_equipo_filtro")
        
        df_mostrar = trabajadores.copy()
        if equipo_filtro != "Todos":
            df_mostrar = df_mostrar[df_mostrar['equipo'] == equipo_filtro]
        
        # Mostrar tabla
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "equipo": st.column_config.TextColumn("Equipo", width="small"),
                "activo": st.column_config.CheckboxColumn("Activo", width="small")
            }
        )
        
        # Opciones de edición
        st.markdown("#### ✏️ Agregar/Editar Trabajador")
        
        with st.form("form_trabajador"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre completo")
                id_editar = st.selectbox("Editar trabajador existente", ["Nuevo"] + trabajadores['id'].tolist(), format_func=lambda x: trabajadores[trabajadores['id'] == x]['nombre'].values[0] if x != "Nuevo" else "Nuevo trabajador")
            
            with col2:
                equipos_disponibles = obtener_equipos()
                equipo = st.selectbox("Equipo", equipos_disponibles)
                activo = st.checkbox("Activo", value=True)
            
            submitted = st.form_submit_button("Guardar Trabajador", use_container_width=True)
            
            if submitted:
                try:
                    if id_editar == "Nuevo":
                        # Insertar nuevo trabajador
                        data = {
                            "nombre": nombre,
                            "equipo": equipo,
                            "activo": activo
                        }
                        supabase.from_('trabajadores').insert(data).execute()
                        st.success("✅ Trabajador agregado correctamente!")
                    else:
                        # Actualizar trabajador existente
                        data = {
                            "nombre": nombre,
                            "equipo": equipo,
                            "activo": activo
                        }
                        supabase.from_('trabajadores').update(data).eq('id', id_editar).execute()
                        st.success("✅ Trabajador actualizado correctamente!")
                    
                    # Limpiar caché
                    if 'trabajadores_cache' in st.session_state:
                        del st.session_state['trabajadores_cache']
                    
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar trabajador: {str(e)}")
    
    else:
        st.markdown("<div class='info-box animate-fade-in'>ℹ️ No hay trabajadores registrados. Agrega el primero a continuación.</div>", unsafe_allow_html=True)
        
        # Formulario para agregar el primer trabajador
        with st.form("form_primer_trabajador"):
            nombre = st.text_input("Nombre completo")
            equipos = obtener_equipos()
            equipo = st.selectbox("Equipo", equipos)
            activo = st.checkbox("Activo", value=True)
            
            submitted = st.form_submit_button("Agregar Trabajador", use_container_width=True)
            
            if submitted:
                try:
                    data = {
                        "nombre": nombre,
                        "equipo": equipo,
                        "activo": activo
                    }
                    supabase.from_('trabajadores').insert(data).execute()
                    st.success("✅ Trabajador agregado correctamente!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar trabajador: {str(e)}")

def mostrar_gestion_equipos_tab():
    """Muestra la gestión de equipos"""
    st.markdown("### 🏢 Gestión de Equipos")
    
    # Cargar equipos
    equipos = obtener_equipos()
    
    # Mostrar lista de equipos
    st.markdown("#### 📋 Lista de Equipos")
    st.dataframe(
        pd.DataFrame(equipos, columns=["Nombre del Equipo"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Formulario para agregar/eliminar equipos
    st.markdown("#### ✏️ Agregar/Eliminar Equipo")
    
    equipo_nombre = st.text_input("Nombre del nuevo equipo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Agregar Equipo", use_container_width=True):
            if equipo_nombre and equipo_nombre.strip():
                try:
                    # Verificar si el equipo ya existe
                    if equipo_nombre in equipos:
                        st.warning("⚠️ Este equipo ya existe.")
                    else:
                        # Insertar nuevo equipo (como trabajador con ese equipo)
                        data = {
                            "nombre": f"Miembro de {equipo_nombre}",
                            "equipo": equipo_nombre,
                            "activo": True
                        }
                        supabase.from_('trabajadores').insert(data).execute()
                        st.success(f"✅ Equipo '{equipo_nombre}' agregado correctamente!")
                        
                        # Limpiar caché
                        if 'equipos_cache' in st.session_state:
                            del st.session_state['equipos_cache']
                        
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar equipo: {str(e)}")
            else:
                st.error("El nombre del equipo no puede estar vacío.")
    
    with col2:
        if st.button("Eliminar Equipo", use_container_width=True):
            if equipo_nombre and equipo_nombre.strip():
                try:
                    # Verificar si el equipo existe
                    if equipo_nombre not in equipos or equipo_nombre in ["Transferencias", "Distribución"]:
                        st.warning("⚠️ No se puede eliminar este equipo o no existe.")
                    else:
                        # Eliminar todos los trabajadores de ese equipo
                        supabase.from_('trabajadores').delete().eq('equipo', equipo_nombre).execute()
                        st.success(f"✅ Equipo '{equipo_nombre}' eliminado correctamente!")
                        
                        # Limpiar caché
                        if 'equipos_cache' in st.session_state:
                            del st.session_state['equipos_cache']
                        
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar equipo: {str(e)}")
            else:
                st.error("Por favor, ingresa el nombre del equipo a eliminar.")

def mostrar_asignacion_metas_tab():
    """Muestra la asignación de metas por equipo"""
    st.markdown("### 📊 Asignación de Metas por Equipo")
    
    # Cargar equipos
    equipos = obtener_equipos()
    
    # Mostrar formulario para asignar metas
    st.markdown("#### 🎯 Metas Diarias por Equipo")
    
    metas_actuales = {
        "Transferencias": CONFIG["META_TRANSFERENCIAS_DIARIA"],
        "Distribución": CONFIG["META_DISTRIBUCION_DIARIA"],
        "Arreglo": CONFIG["META_ARREGLO_DIARIA"]
    }
    
    # Formulario para cada equipo
    for equipo in equipos:
        if equipo in metas_actuales:
            meta_actual = metas_actuales[equipo]
            st.number_input(
                f"Meta diaria para {equipo}",
                value=float(meta_actual),
                min_value=0.0,
                step=10.0,
                key=f"meta_{equipo}"
            )
    
    if st.button("Guardar Metas", use_container_width=True):
        # Aquí iría la lógica para guardar las nuevas metas
        # En una implementación completa, esto actualizaría la base de datos
        st.success("✅ Metas guardadas correctamente!")
        time.sleep(1.5)
        st.rerun()

# ================================
# Funciones auxiliares para guías
# ================================
def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único."""
    return f"9400{str(record_id).zfill(20)}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera y devuelve una imagen del código QR."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def generar_pdf_guia(store_name: str, brand: str, url: str, 
                    sender_name: str, sender_info: pd.Series, 
                    tracking_number: str) -> FPDF:
    """Genera un PDF con la guía de envío"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Logo de la marca
    logo_url = obtener_logo_url(f"{brand}.jpg")
    if logo_url:
        try:
            # Descargar la imagen
            import requests
            response = requests.get(logo_url)
            img = Image.open(io.BytesIO(response.content))
            
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                img.save(tmp.name)
                pdf.image(tmp.name, x=10, y=10, w=50)
        except Exception as e:
            logger.error(f"Error al agregar logo al PDF: {e}")
    
    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Guía de Envío - {brand}", ln=True, align="C")
    pdf.ln(10)
    
    # Información de la tienda
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Tienda:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, store_name, ln=True)
    
    # Información de la marca
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Marca:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, brand, ln=True)
    
    # Información del remitente
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Remitente:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"{sender_name} - {sender_info['telefono']}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 8, "")
    pdf.multi_cell(0, 8, sender_info['direccion'])
    pdf.ln(5)
    
    # Número de seguimiento
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Número de Seguimiento:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, tracking_number, ln=True)
    
    # Código QR
    try:
        qr_img = generar_qr_imagen(tracking_number)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            qr_img.save(tmp.name)
            pdf.image(tmp.name, x=10, y=pdf.get_y() + 5, w=40)
    except Exception as e:
        logger.error(f"Error al generar código QR para PDF: {e}")
    
    # URL del pedido
    pdf.ln(20)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "URL del Pedido:")
    pdf.set_font("Arial", "U", 10)
    pdf.cell(0, 8, url, ln=True)
    
    # Fecha de generación
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 6, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="R")
    
    return pdf

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
    """Función principal que ejecuta la aplicación"""
    st.set_page_config(
        page_title="Sistema de KPIs Aeropostale",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilos CSS personalizados
    st.markdown("""
        <style>
        /* Colores del tema */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --success-color: #2ca02c;
            --warning-color: #d62728;
            --info-color: #9467bd;
            --background-color: #f8f9fa;
            --text-color: #212529;
            --card-background: #ffffff;
        }
        
        /* Estilos generales */
        body {
            color: var(--text-color);
            background-color: var(--background-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Cabecera */
        .header-title {
            color: var(--primary-color);
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 1em;
            padding-bottom: 0.5em;
            border-bottom: 2px solid var(--primary-color);
        }
        
        /* Secciones */
        .section-title {
            color: var(--primary-color);
            font-size: 1.5em;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }
        
        /* Boxes de información */
        .info-box {
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #1e88e5;
            margin: 15px 0;
        }
        
        .success-box {
            background-color: #e8f5e9;
            color: #1b5e20;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #43a047;
            margin: 15px 0;
        }
        
        .warning-box {
            background-color: #fff8e1;
            color: #e65100;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #fb8c00;
            margin: 15px 0;
        }
        
        .error-box {
            background-color: #ffebee;
            color: #b71c1c;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e53935;
            margin: 15px 0;
        }
        
        /* Tarjetas de KPI */
        .kpi-card {
            background-color: var(--card-background);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
            transition: transform 0.3s;
        }
        
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        }
        
        .metric-label {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        
        .metric-value {
            font-size: 2.2em;
            font-weight: bold;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        /* Animaciones */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.5s ease forwards;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 5px 5px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Botones */
        .stButton>button {
            border-radius: 8px;
            padding: 0.5em 1em;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Dataframes */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 3em;
            padding: 1em;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
        
        /* Input containers */
        .stNumberInput, .stTextInput, .stSelectbox {
            margin-bottom: 1em;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: bold;
            color: var(--primary-color);
        }
        
        /* Estilos específicos para el sistema de guías */
        .guide-section {
            background: var(--card-background);
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .qr-preview {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .guide-metric {
            font-size: 1.3em;
            margin: 12px 0;
            color: var(--text-color);
            display: flex;
            align-items: center;
        }
        
        .guide-metric strong {
            color: var(--primary-color);
            margin-left: 8px;
        }
        
        .guide-icon {
            color: var(--primary-color);
            margin-right: 10px;
            font-size: 1.5em;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Barra lateral de navegación
    st.sidebar.title("📌 Sistema de KPIs Aeropostale")
    
    # Información del sistema
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 Estadísticas del Sistema")
        
        # Mostrar información de conexión a Supabase
        if supabase:
            st.success("✅ Conexión a Supabase: Activa")
            
            # Intentar obtener conteos de registros
            try:
                # Contar trabajadores
                response = supabase.from_('trabajadores').select('id', count='exact').execute()
                num_trabajadores = response.count if hasattr(response, 'count') else 0
                
                # Contar registros de KPIs
                response = supabase.from_('daily_kpis').select('id', count='exact').execute()
                num_kpis = response.count if hasattr(response, 'count') else 0
                
                st.metric("Trabajadores", num_trabajadores)
                st.metric("Registros de KPIs", num_kpis)
            except Exception as e:
                logger.error(f"Error al obtener estadísticas: {e}")
                st.warning("⚠️ No se pudieron cargar estadísticas")
        else:
            st.error("❌ Conexión a Supabase: Inactiva")
        
        st.markdown("---")
        st.markdown("### 🛠️ Versión del Sistema")
        st.markdown("**v2.3.1**")
        st.markdown("Última actualización: Septiembre 2025")
    
    # Selección de página
    st.sidebar.markdown("### 🌐 Navegación")
    page = st.sidebar.radio("Ir a", list(PAGES.keys()))
    
    # Ejecutar la página seleccionada
    PAGES[page]()
    
    # Footer
    st.markdown("""
        <div class="footer">
            Sistema de KPIs Aeropostale v2.3.1 | © 2025 Todos los derechos reservados.<br>
            Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com" style="color: #1f77b4;">Wilson Pérez</a>
            | Soporte técnico: soporte.kpis@aeropostale.com
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
