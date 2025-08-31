import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import time
import json
import os
import hashlib
from pathlib import Path
import warnings
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.impute import SimpleImputer
from contextlib import contextmanager
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import base64
import tempfile
from supabase import create_client, Client
import qrcode
from PIL import Image
import fpdf
from fpdf import FPDF

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

# Inicializar cliente de Supabase
@st.cache_resource
def init_supabase() -> Optional[Client]:
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
    page_title="Sistema Integrado - KPIs y Guías de Envío",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado (combinado de ambos sistemas)
st.markdown("""
<style>
    .main { background-color: white; }
    .stApp { background-color: black; }
    .kpi-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        padding: 18px;
        margin: 10px 0;
        border-left: 4px solid #2c3e50;
        transition: all 0.3s ease;
    }
    .kpi-card:hover { 
        box-shadow: 0 6px 16px rgba(0,0,0,0.12); 
        transform: translateY(-3px); 
    }
    .metric-value { 
        font-size: 2.8em !important; 
        font-weight: bold; 
        color: #2c3e50;
        line-height: 1.2;
    }
    .worker-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        color: #2c3e50;
        margin: 8px;
        min-height: 250px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #3498db;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .worker-header { 
        font-size: 1.3em; 
        margin-bottom: 10px; 
        color: #2c3e50;
        font-weight: bold;
    }
    .worker-metric { 
        font-size: 1.1em; 
        margin: 5px 0; 
        color: #2c3e50;
    }
    .trend-up { color: #27ae60; }
    .trend-down { color: #e74c3c; }
    .header-title { 
        color: #2c3e50;
        font-weight: 800;
        font-size: 2.5em;
        margin-bottom: 20px;
    }
    .section-title {
        border-left: 5px solid #3498db;
        padding-left: 10px;
        margin: 20px 0;
        color: #2c3e50;
        font-size: 1.8em;
    }
    .comment-container {
        margin-top: 15px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 5px;
        border-left: 3px solid #3498db;
    }
    .comment-title {
        font-weight: bold;
        margin-bottom: 5px;
        color: #2c3e50;
    }
    .comment-content {
        font-size: 0.9em;
        color: #2c3e50;
    }
    .metric-label {
        color: #2c3e50;
        font-size: 0.9em;
    }
    .password-container {
        background-color: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        max-width: 400px;
        margin: 100px auto;
    }
    .stats-container {
        flex-grow: 1;
    }
    .date-selector {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #17a2b8;
        margin: 10px 0;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        color: white;
    }
    .stSelectbox, .stDateInput, .stNumberInput, .stTextArea {
        margin-bottom: 15px;
    }
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .jar-progress {
        background: #f0f0f0;
        border-radius: 20px;
        height: 30px;
        margin: 15px 0;
        overflow: hidden;
    }
    .jar-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        border-radius: 20px;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }
    .team-section {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .team-header {
        font-size: 1.5em;
        color: #2c3e50;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #3498db;
    }
    .export-buttons {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
    }
    .export-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .export-button:hover {
        background-color: #2980b9;
    }
    /* Estilos adicionales para el sistema de guías */
    .guide-header {
        color: #2c3e50;
        font-weight: 800;
        font-size: 2.5em;
        margin-bottom: 20px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    .guide-section {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .guide-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        color: #2c3e50;
        margin: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #e74c3c;
    }
    .qr-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }
    .guide-metric {
        font-size: 1.2em;
        margin: 8px 0;
        color: #2c3e50;
    }
    .guide-input {
        margin-bottom: 15px;
    }
    .guide-success {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .guide-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .guide-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .guide-info {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
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

def verificar_permisos(permiso: str) -> bool:
    """Verifica si el usuario actual tiene un permiso específico"""
    if 'user' not in st.session_state:
        return False
    
    # Para este ejemplo, asumimos que los roles se almacenan en la tabla de usuarios
    if supabase is None:
        return False
    
    try:
        response = supabase.from_('kpi_users').select('role').eq('email', st.session_state.user).execute()
        # CORRECCIÓN: Verificar si hay datos en la respuesta
        if response and response.data:
            role = response.data[0]['role']
            # Definir permisos según el rol
            permisos = {
                'admin': ['all'],
                'manager': ['view_kpis', 'manage_guides', 'view_reports'],
                'user': ['view_kpis', 'create_guides']
            }
            return permiso in permisos.get(role, []) or 'all' in permisos.get(role, [])
        return False
    except Exception as e:
        logger.error(f"Error al verificar permisos: {e}", exc_info=True)
        return False

# ================================
# Funciones de KPIs (adaptadas)
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
        response = supabase.from_('kpi_trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre', desc=False).execute()
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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

def obtener_equipos() -> List[str]:
    """Obtiene la lista de equipos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('kpi_trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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

def guardar_datos_db(fecha: str, datos: Dict[str, Dict]) -> bool:
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
            response = supabase.from_('kpi_daily').upsert(registros, on_conflict="fecha,nombre").execute()
            
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

def cargar_historico_db(fecha_inicio: Optional[str] = None, 
                       fecha_fin: Optional[str] = None, 
                       trabajador: Optional[str] = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('kpi_daily').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador:
            query = query.eq('nombre', trabajador)
            
        query = query.order('fecha', desc=True)
        
        response = query.execute()
        
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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
            font=dict(color="#2c3e50"),
            title_font_color="#2c3e50",
            xaxis_title_font_color="#2c3e50",
            yaxis_title_font_color="#2c3e50",
            xaxis_tickfont_color="#2c3e50",
            yaxis_tickfont_color="#2c3e50"
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
            number = {'suffix': '%', 'font': {'size': 36}},
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': titulo, 'font': {'size': 20}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "gold", 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': "darkred"},
                    {'range': [50, 75], 'color': "darkorange"},
                    {'range': [75, 100], 'color': "forestgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
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
# Funciones de Guías (adaptadas a Supabase)
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
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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
        # Obtener ID del usuario actual
        user_id = None
        if 'user' in st.session_state:
            user_response = supabase.from_('kpi_users').select('id').eq('email', st.session_state.user).execute()
            # CORRECCIÓN: Verificar si hay datos en la respuesta
            if user_response and user_response.data:
                user_id = user_response.data[0]['id']
        
        # Insertar nueva guía
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat(),
            'user_id': user_id
        }
        
        response = supabase.from_('guide_logs').insert(data).execute()
        
        # CORRECCIÓN: Verificar si la inserción fue exitosa
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
        # Si el usuario es admin, obtener todas las guías
        # Si no, obtener solo las del usuario actual
        query = supabase.from_('guide_logs').select('*')
        
        if 'user' in st.session_state and not verificar_permisos('all'):
            user_response = supabase.from_('kpi_users').select('id').eq('email', st.session_state.user).execute()
            # CORRECCIÓN: Verificar si hay datos en la respuesta
            if user_response and user_response.data:
                user_id = user_response.data[0]['id']
                query = query.eq('user_id', user_id)
        
        query = query.order('created_at', desc=True)
        
        response = query.execute()
        
        # CORRECCIÓN: Verificar si hay datos en la respuesta
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

# ================================
# Funciones de autenticación unificadas
# ================================

def verificar_password() -> bool:
    """Verifica la contraseña del usuario"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        st.markdown("<div class='password-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: black;'>🔐 Acceso Restringido</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            username = st.text_input("Email:", key="login_email")
            password = st.text_input("Contraseña:", type="password", key="login_password")
            if st.button("Iniciar Sesión", key="login_button"):
                if autenticar_usuario(username, password):
                    st.session_state.password_correct = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.markdown("<div class='error-box'>❌ Email o contraseña incorrectos</div>", unsafe_allow_html=True)
        
        with tab2:
            new_email = st.text_input("Nuevo Email:", key="register_email")
            new_password = st.text_input("Nueva Contraseña:", type="password", key="register_password")
            if st.button("Registrarse", key="register_button"):
                if registrar_usuario(new_email, new_password):
                    st.markdown("<div class='success-box'>✅ Registro exitoso. Inicia sesión con tus credenciales.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box'>❌ Error al registrar usuario. El email ya existe.</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    
    return True

def autenticar_usuario(email: str, password: str) -> bool:
    """Autentica un usuario contra Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Buscar usuario por email
        response = supabase.from_('kpi_users').select('*').eq('email', email).execute()
        
        # CORRECCIÓN: Verificar si hay datos en la respuesta
        if response and response.data:
            # Verificar contraseña
            hashed_password = hash_password(password)
            if response.data[0]['password'] == hashed_password:
                return True
        return False
    except Exception as e:
        logger.error(f"Error al autenticar usuario: {e}", exc_info=True)
        return False

def registrar_usuario(email: str, password: str) -> bool:
    """Registra un nuevo usuario en Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Verificar si el email ya existe
        response = supabase.from_('kpi_users').select('id').eq('email', email).execute()
        
        # CORRECCIÓN: Verificar si hay datos en la respuesta
        if response and response.data:
            return False  # El email ya existe
        
        # Insertar nuevo usuario
        hashed_password = hash_password(password)
        data = {
            'email': email,
            'password': hashed_password,
            'role': 'user',  # Rol por defecto
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.from_('kpi_users').insert(data).execute()
        
        # CORRECCIÓN: Verificar si la inserción fue exitosa
        if response and response.data:
            return True
        return False
    except Exception as e:
        logger.error(f"Error al registrar usuario: {e}", exc_info=True)
        return False

# ================================
# Funciones de análisis (compartidas)
# ================================

def analizar_tendencias(df: pd.DataFrame, metric: str) -> Union[Dict[str, Any], str]:
    """Analiza tendencias en los datos"""
    if df.empty or len(df) < 2:
        return "No hay suficientes datos para analizar tendencias"
    try:
        # Calcular media móvil
        df = df.sort_values('fecha')
        df['media_movil'] = df[metric].rolling(window=7, min_periods=1).mean()
        # Calcular tendencia (regresión lineal simple)
        x = np.arange(len(df))
        y = df[metric].values
        coeficientes = np.polyfit(x, y, 1)
        tendencia = coeficientes[0] * x + coeficientes[1]
        # Determinar dirección de la tendencia
        if coeficientes[0] > 0.5:  # Umbral más alto para evitar fluctuaciones pequeñas
            direccion = "↑ Ascendente significativa"
        elif coeficientes[0] > 0:
            direccion = "↑ Ligeramente ascendente"
        elif coeficientes[0] < -0.5:
            direccion = "↓ Descendente significativa"
        elif coeficientes[0] < 0:
            direccion = "↓ Ligeramente descendente"
        else:
            direccion = "→ Estable"
        return {
            'tendencia': tendencia,
            'direccion': direccion,
            'pendiente': coeficientes[0],
            'r_cuadrado': np.corrcoef(x, y)[0, 1]**2
        }
    except Exception as e:
        logger.error(f"Error en análisis de tendencias: {e}", exc_info=True)
        return "Error al analizar tendencias"

def predecir_valores_futuros(df: pd.DataFrame, columna: str, dias: int = 7) -> Optional[np.ndarray]:
    """Predice valores futuros usando regresión con validación"""
    if len(df) < 5:  # Mínimo de datos para predicción
        return None
    try:
        # Preparar datos
        df = df.sort_values('fecha')
        X = np.arange(len(df)).reshape(-1, 1)
        y = df[columna].values
        # Dividir en train y test para validación
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        # Probar múltiples modelos
        modelos = {
            'Lineal': LinearRegression(),
            'Ridge': Ridge(alpha=1.0),
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        mejor_modelo = None
        mejor_mae = float('inf')
        for nombre, modelo in modelos.items():
            modelo.fit(X_train, y_train)
            predicciones = modelo.predict(X_test)
            mae = mean_absolute_error(y_test, predicciones)
            if mae < mejor_mae:
                mejor_mae = mae
                mejor_modelo = modelo
        # Predecir valores futuros con el mejor modelo
        X_futuro = np.arange(len(df), len(df) + dias).reshape(-1, 1)
        predicciones = mejor_modelo.predict(X_futuro)
        return predicciones
    except Exception as e:
        logger.error(f"Error en predicción: {e}", exc_info=True)
        return None

def calcular_estadisticas_avanzadas(df: pd.DataFrame, columna: str) -> Dict[str, Any]:
    """Calcula estadísticas avanzadas para una columna"""
    if df.empty:
        return {}
    try:
        valores = df[columna].dropna()
        if len(valores) == 0:
            return {}
        return {
            'media': np.mean(valores),
            'mediana': np.median(valores),
            'desviacion_estandar': np.std(valores),
            'percentil_25': np.percentile(valores, 25),
            'percentil_75': np.percentile(valores, 75),
            'rango': np.ptp(valores),
            'asimetria': stats.skew(valores),
            'curtosis': stats.kurtosis(valores),
            'count': len(valores),
            'min': np.min(valores),
            'max': np.max(valores)
        }
    except Exception as e:
        logger.error(f"Error al calcular estadísticas: {e}", exc_info=True)
        return {}

# ================================
# Funciones de exportación (compartidas)
# ================================

def exportar_excel(df: pd.DataFrame) -> bytes:
    """Exporta el DataFrame a un archivo Excel en memoria"""
    try:
        # Crear una copia del DataFrame para no modificar el original
        export_df = df.copy()
        
        # Asegurar que las fechas estén en formato adecuado
        if 'fecha' in export_df.columns:
            export_df['fecha'] = pd.to_datetime(export_df['fecha']).dt.strftime('%Y-%m-%d')
        
        # Convertir cualquier columna de fecha a string para evitar problemas
        for col in export_df.select_dtypes(include=['datetime64']).columns:
            export_df[col] = export_df[col].dt.strftime('%Y-%m-%d')
        
        # Manejar valores NaN y None
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
                'fg_color': '#4472C4',
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
        
        processed_data = output.getvalue()
        return processed_data
    except Exception as e:
        logger.error(f"Error al exportar a Excel: {e}", exc_info=True)
        st.error(f"Error al exportar a Excel: {str(e)}")
        raise

def plot_to_base64(fig):
    """Convierte un gráfico Plotly a base64 para incrustar en PDF"""
    try:
        # Intentar convertir figura a imagen en memoria
        try:
            img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
        except Exception as e:
            logger.warning(f"Error al convertir gráfico con to_image: {e}. Intentando alternativa...")
            # Alternativa si kaleido no está disponible
            img_bytes = fig.to_image(format="png", width=800, height=600, engine='kaleido')
        
        if img_bytes is None:
            logger.error("No se pudo generar la imagen del gráfico")
            return None
            
        return base64.b64encode(img_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Error crítico al convertir gráfico a base64: {e}", exc_info=True)
        return None

def crear_reporte_pdf(df: pd.DataFrame, fecha_inicio: str, fecha_fin: str) -> bytes:
    """Crea un reporte PDF con los datos y gráficas"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Título del reporte
        title = Paragraph("Reporte de KPIs - Fashion Club", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Información del período
        periodo_text = f"Período: {fecha_inicio} a {fecha_fin}"
        periodo = Paragraph(periodo_text, styles['Normal'])
        elements.append(periodo)
        elements.append(Spacer(1, 12))
        
        # Resumen estadístico
        resumen_text = "Resumen Estadístico"
        resumen_title = Paragraph(resumen_text, styles['Heading2'])
        elements.append(resumen_title)
        
        # Crear tabla de resumen
        try:
            resumen_data = df.groupby('nombre').agg({
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
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))
        except Exception as e:
            logger.error(f"Error al crear tabla de resumen: {e}", exc_info=True)
            error_msg = Paragraph(f"Error al generar tabla de resumen: {str(e)}", styles['Normal'])
            elements.append(error_msg)
            elements.append(Spacer(1, 12))
        
        # Gráficas - Ahora con manejo robusto de errores
        try:
            # Crear gráfica de eficiencia por día
            df_eficiencia_dia = df.groupby('fecha')['eficiencia'].mean().reset_index()
            if not df_eficiencia_dia.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_eficiencia_dia['fecha'], 
                    y=df_eficiencia_dia['eficiencia'],
                    mode='lines+markers',
                    name='Eficiencia Promedio'
                ))
                fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta")
                fig.update_layout(
                    title='Evolución de la Eficiencia Promedio',
                    xaxis_title='Fecha',
                    yaxis_title='Eficiencia (%)',
                    width=800,
                    height=600
                )
                # Convertir gráfico a base64
                img_data = plot_to_base64(fig)
                if img_data:
                    # Guardar imagen temporalmente
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                        tmpfile.write(base64.b64decode(img_data))
                        img_path = tmpfile.name
                    # Agregar gráfica al PDF
                    img = Image(img_path, width=6*inch, height=4*inch)
                    elements.append(Spacer(1, 12))
                    elements.append(Paragraph("Evolución de la Eficiencia Promedio", styles['Heading3']))
                    elements.append(img)
                    # Limpiar archivo temporal
                    os.unlink(img_path)
                else:
                    logger.warning("No se pudo generar la imagen del gráfico de eficiencia")
                    elements.append(Paragraph("No se pudo generar el gráfico de eficiencia", styles['Normal']))
            else:
                elements.append(Paragraph("No hay datos suficientes para el gráfico de eficiencia", styles['Normal']))
        except Exception as e:
            logger.error(f"Error al crear gráfica de eficiencia para PDF: {e}", exc_info=True)
            elements.append(Paragraph(f"Error al generar gráfica de eficiencia: {str(e)}", styles['Normal']))
        
        try:
            # Crear gráfica de productividad por equipo
            df_productividad_equipo = df.groupby('equipo')['productividad'].mean().reset_index()
            if not df_productividad_equipo.empty:
                fig = px.bar(df_productividad_equipo, x='equipo', y='productividad', 
                            title='Productividad Promedio por Equipo',
                            labels={'equipo': 'Equipo', 'productividad': 'Productividad (unidades/hora)'})
                fig.update_layout(width=800, height=600)
                # Convertir gráfico a base64
                img_data = plot_to_base64(fig)
                if img_data:
                    # Guardar imagen temporalmente
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                        tmpfile.write(base64.b64decode(img_data))
                        img_path = tmpfile.name
                    # Agregar gráfica al PDF
                    img = Image(img_path, width=6*inch, height=4*inch)
                    elements.append(Spacer(1, 12))
                    elements.append(Paragraph("Productividad por Equipo", styles['Heading3']))
                    elements.append(img)
                    # Limpiar archivo temporal
                    os.unlink(img_path)
                else:
                    logger.warning("No se pudo generar la imagen del gráfico de productividad")
                    elements.append(Paragraph("No se pudo generar el gráfico de productividad", styles['Normal']))
            else:
                elements.append(Paragraph("No hay datos suficientes para el gráfico de productividad por equipo", styles['Normal']))
        except Exception as e:
            logger.error(f"Error al crear gráfica de productividad para PDF: {e}", exc_info=True)
            elements.append(Paragraph(f"Error al generar gráfica de productividad: {str(e)}", styles['Normal']))
        
        try:
            # Crear gráfica de cumplimiento de metas
            df_cumplimiento = df.copy()
            df_cumplimiento['cumplio_meta'] = df_cumplimiento['eficiencia'] >= 100
            cumplimiento_por_equipo = df_cumplimiento.groupby('equipo')['cumplio_meta'].mean() * 100
            
            if not cumplimiento_por_equipo.empty:
                fig = go.Figure(data=[go.Bar(
                    x=cumplimiento_por_equipo.index,
                    y=cumplimiento_por_equipo.values,
                    marker_color=['#27ae60' if val >= 80 else '#e74c3c' for val in cumplimiento_por_equipo.values]
                )])
                fig.update_layout(
                    title='Porcentaje de Días que Cumplieron la Meta por Equipo',
                    xaxis_title='Equipo',
                    yaxis_title='Porcentaje de Cumplimiento (%)',
                    yaxis_range=[0, 100],
                    width=800,
                    height=600
                )
                # Convertir gráfico a base64
                img_data = plot_to_base64(fig)
                if img_data:
                    # Guardar imagen temporalmente
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                        tmpfile.write(base64.b64decode(img_data))
                        img_path = tmpfile.name
                    # Agregar gráfica al PDF
                    img = Image(img_path, width=6*inch, height=4*inch)
                    elements.append(Spacer(1, 12))
                    elements.append(Paragraph("Cumplimiento de Metas por Equipo", styles['Heading3']))
                    elements.append(img)
                    # Limpiar archivo temporal
                    os.unlink(img_path)
                else:
                    logger.warning("No se pudo generar la imagen del gráfico de cumplimiento")
                    elements.append(Paragraph("No se pudo generar el gráfico de cumplimiento", styles['Normal']))
            else:
                elements.append(Paragraph("No hay datos suficientes para el gráfico de cumplimiento de metas", styles['Normal']))
        except Exception as e:
            logger.error(f"Error al crear gráfica de cumplimiento para PDF: {e}", exc_info=True)
            elements.append(Paragraph(f"Error al generar gráfico de cumplimiento: {str(e)}", styles['Normal']))
        
        # Construir PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error crítico al crear reporte PDF: {e}", exc_info=True)
        st.error(f"Error al crear reporte PDF: {str(e)}")
        raise

# ================================
# Componentes de la aplicación
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs"""
    st.markdown("<h1 class='header-title'>📊 Dashboard de KPIs Fashion Club</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Crear selector de fecha
    st.markdown("<div class='date-selector'>", unsafe_allow_html=True)
    st.markdown("<h3>Selecciona la fecha a visualizar:</h3>", unsafe_allow_html=True)
    
    # Obtener fechas únicas y ordenarlas
    if not df.empty and 'fecha' in df.columns:
        # Convertir a fecha y eliminar duplicados
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='warning-box'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
            return
        fecha_seleccionada = st.selectbox(
            "Fecha:",
            options=fechas_disponibles,
            index=0,
            label_visibility="collapsed"
        )
    else:
        st.markdown("<div class='warning-box'>⚠️ No hay datos disponibles.</div>", unsafe_allow_html=True)
        return
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Filtrar datos por fecha seleccionada
    df_reciente = df[df['fecha'].dt.date == fecha_seleccionada]
    if df_reciente.empty:
        st.markdown(f"<div class='warning-box'>⚠️ No hay datos disponibles para la fecha {fecha_seleccionada}.</div>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<p style='color: #2c3e50; font-size: 1.1em;'>Datos para la fecha: {fecha_seleccionada}</p>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    
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
        <div class="kpi-card">
            <h3>✅ Total Producción</h3>
            <p class="metric-value">{total_cantidad:,.0f}</p>
            <p>Meta: {total_meta:,.0f} | <span class="{'trend-up' if cumplimiento_meta >= 100 else 'trend-down'}">{cumplimiento_meta:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>🎯 Eficiencia Promedio</h3>
            <p class="metric-value">{avg_eficiencia:.1f}%</p>
            <p>Meta: 100% | <span class="{'trend-up' if avg_eficiencia >= 100 else 'trend-down'}">{avg_eficiencia - 100:.1f}%</span></p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>⚡ Productividad Promedio</h3>
            <p class="metric-value">{avg_productividad:.1f}</p>
            <p>unidades/hora</p>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>⏱️ Productividad Total</h3>
            <p class="metric-value">{productividad_total:.1f}</p>
            <p>unidades/hora ({total_horas:.1f} h)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<h2 class='section-title'>📅 Cumplimiento de Metas Mensuales (Transferencias)</h2>", unsafe_allow_html=True)
    
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
        <div class="kpi-card">
            <h3>Meta Mensual Transferencias</h3>
            <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
            <p>Acumulado: {cum_transferencias:,.0f} / Meta Mensual: {meta_mensual_transferencias:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Gráfico de frasco de agua para el cumplimiento
        fig = crear_grafico_frasco(cumplimiento_transferencias, "Cumplimiento Mensual Transferencias")
        st.plotly_chart(fig, use_container_width=True)
    
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
        fig.add_hline(y=meta_mensual_transferencias, line_dash="dash", line_color="red", annotation_text="Meta Mensual")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para el gráfico de Transferencias.")
    
    st.markdown("<h2 class='section-title'>👥 Rendimiento por Equipos</h2>", unsafe_allow_html=True)
    
    # Obtener lista de equipos
    equipos = df_reciente['equipo'].unique()
    # Ordenar equipos en un orden específico
    orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
    equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
    equipos_finales = equipos_ordenados + equipos_restantes
    
    for equipo in equipos_finales:
        df_equipo = df_reciente[df_reciente['equipo'] == equipo]
        st.markdown(f"<div class='team-section'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
        
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
                <h3>Producción</h3>
                <p class="metric-value">{total_equipo:,.0f}</p>
                <p>Meta: {meta_equipo:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>Eficiencia</h3>
                <p class="metric-value">{eficiencia_equipo:.1f}%</p>
                <p>Meta: 100%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>Productividad</h3>
                <p class="metric-value">{productividad_equipo:.1f}</p>
                <p>unidades/hora</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <h3>Horas</h3>
                <p class="metric-value">{horas_equipo:.1f}</p>
                <p>horas trabajadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Mostrar trabajadores del equipo
        for _, row in df_equipo.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                color = "#27ae60" if row['eficiencia'] >= 100 else "#e74c3c"
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
    st.markdown("<h1 class='header-title'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    df = cargar_historico_db()
    if df.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='error-box'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    # Aplicar filtros
    df_filtrado = df[(df['dia'] >= fecha_inicio) & (df['dia'] <= fecha_fin)]
    if trabajador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador]
    
    if df_filtrado.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay datos en el rango de fechas seleccionado.</div>", unsafe_allow_html=True)
        return
    
    # Botones de exportación
    st.markdown("<div class='export-buttons'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        # Botón para exportar a Excel
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                excel_data = exportar_excel(df_filtrado)
                st.download_button(
                    label="⬇️ Descargar archivo Excel",
                    data=excel_data,
                    file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Botón para exportar a PDF
        if st.button("📄 Exportar a PDF", use_container_width=True):
            try:
                with st.spinner("Generando reporte PDF..."):
                    pdf_data = crear_reporte_pdf(df_filtrado, str(fecha_inicio), str(fecha_fin))
                    st.download_button(
                        label="⬇️ Descargar reporte PDF",
                        data=pdf_data,
                        file_name=f"reporte_kpis_{fecha_inicio}_a_{fecha_fin}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                logger.error(f"Error al exportar a PDF: {e}", exc_info=True)
                st.markdown("<div class='error-box'>❌ Error al exportar a PDF.</div>", unsafe_allow_html=True)
    
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
    
    st.markdown("<h2 class='section-title'>📋 Resumen Estadístico</h2>", unsafe_allow_html=True)
    # Mostrar resumen estadístico
    st.dataframe(df_filtrado.groupby('nombre').agg({
        'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
        'eficiencia': ['mean', 'max', 'min'],
        'productividad': ['mean', 'max', 'min'],
        'horas_trabajo': ['sum', 'mean']
    }).round(2), use_container_width=True)
    
    st.markdown("<h2 class='section-title'>📊 Tendencias Históricas</h2>", unsafe_allow_html=True)
    
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
            fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta de eficiencia")
            # Analizar tendencia
            tendencia = analizar_tendencias(df_eficiencia_dia, 'eficiencia')
            if isinstance(tendencia, dict):
                fig.add_trace(go.Scatter(
                    x=df_eficiencia_dia['dia'], 
                    y=tendencia['tendencia'], 
                    mode='lines', 
                    name=f'Tendencia ({tendencia["direccion"]})',
                    line=dict(dash='dash', color='orange')
                ))
            st.plotly_chart(fig, use_container_width=True)
            # Mostrar información de tendencia
            if isinstance(tendencia, dict):
                st.markdown(f"**Tendencia:** {tendencia['direccion']} (R²: {tendencia['r_cuadrado']:.3f})")
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
            st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(fig, use_container_width=True)
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
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay suficientes datos numéricos para calcular correlaciones.")
        
        st.markdown("<h3>📋 Datos Detallados</h3>", unsafe_allow_html=True)
        st.dataframe(df_filtrado, use_container_width=True)
    
    with tab5:
        st.markdown("<h3>🔮 Predicción de Tendencia</h3>", unsafe_allow_html=True)
        if not df_eficiencia_dia.empty and len(df_eficiencia_dia) > 5:
            # Preparar datos para predicción
            dias_prediccion = 7
            predicciones = predecir_valores_futuros(df_eficiencia_dia, 'eficiencia', dias_prediccion)
            if predicciones is not None:
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
                    y=predicciones,
                    mode='lines+markers',
                    name='Predicción',
                    line=dict(dash='dash', color='orange')
                ))
                # Línea de meta
                fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta de eficiencia")
                fig.update_layout(
                    title='Predicción de Eficiencia para los Próximos 7 Días',
                    xaxis_title='Fecha',
                    yaxis_title='Eficiencia Promedio (%)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#2c3e50")
                )
                st.plotly_chart(fig, use_container_width=True)
                # Mostrar valores de predicción
                st.markdown("<h4>Valores de Predicción:</h4>", unsafe_allow_html=True)
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, predicciones)):
                    st.write(f"{fecha.strftime('%Y-%m-%d')}: {pred:.1f}%")
            else:
                st.info("Error al generar predicciones. Verifique los datos.")
        else:
            st.info("Se necesitan al menos 5 días de datos para realizar predicciones.")

def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs"""
    st.markdown("<h1 class='header-title'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener trabajadores desde Supabase
    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay trabajadores registrados. Por favor, registre trabajadores primero.</div>", unsafe_allow_html=True)
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
        st.markdown("<h3 class='section-title'>Meta Mensual de Transferencias</h3>", unsafe_allow_html=True)
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
            st.markdown(f"<div class='team-section'><div class='team-header'>{equipo}</div></div>", unsafe_allow_html=True)
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
                        st.markdown(f"<div class='error-box'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
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
            st.markdown("<h3 class='section-title'>📋 Resumen de KPIs Calculados</h3>", unsafe_allow_html=True)
            for equipo, miembros in trabajadores_por_equipo.items():
                st.markdown(f"**{equipo}:**")
                for trabajador in miembros:
                    if trabajador in datos_guardar:
                        datos = datos_guardar[trabajador]
                        st.markdown(f"- {trabajador}: {datos['cantidad']} unidades ({datos['eficiencia']:.1f}%)")
    
    # Botón de confirmación fuera del formulario
    if st.session_state.datos_calculados is not None and st.session_state.fecha_guardar is not None:
        if st.button("✅ Confirmar y Guardar Datos", key="confirmar_guardar"):
            if guardar_datos_db(st.session_state.fecha_guardar, st.session_state.datos_calculados):
                st.markdown("<div class='success-box'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                # Limpiar datos de confirmación
                st.session_state.datos_calculados = None
                st.session_state.fecha_guardar = None
                time.sleep(2)
                st.rerun()
            else:
                st.markdown("<div class='error-box'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)

def mostrar_gestion_trabajadores_kpis():
    """Muestra la interfaz de gestión de trabajadores"""
    st.markdown("<h1 class='header-title'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    try:
        # Obtener lista actual de trabajadores
        response = supabase.from_('kpi_trabajadores').select('*').order('equipo,nombre', desc=False).execute()
        # CORRECCIÓN: Verificar si hay datos en la respuesta
        if response and response.data:
            trabajadores = response.data
        else:
            trabajadores = []
        
        # Asegurar que Luis Perugachi esté en el equipo de Distribución
        if any(trab['nombre'] == 'Luis Perugachi' for trab in trabajadores):
            for trab in trabajadores:
                if trab['nombre'] == 'Luis Perugachi':
                    trab['equipo'] = 'Distribución'
        
        st.markdown("<h2 class='section-title'>Trabajadores Actuales</h2>", unsafe_allow_html=True)
        if trabajadores:
            df_trabajadores = pd.DataFrame(trabajadores)
            st.dataframe(df_trabajadores[['nombre', 'equipo', 'activo']], use_container_width=True)
        else:
            st.info("No hay trabajadores registrados.")
        
        st.markdown("<h2 class='section-title'>Agregar Nuevo Trabajador</h2>", unsafe_allow_html=True)
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
                        response = supabase.from_('kpi_trabajadores').select('*').eq('nombre', nuevo_nombre).execute()
                        # CORRECCIÓN: Verificar si hay datos en la respuesta
                        if response and response.data:
                            st.markdown("<div class='error-box'>❌ El trabajador ya existe.</div>", unsafe_allow_html=True)
                        else:
                            # Insertar nuevo trabajador
                            supabase.from_('kpi_trabajadores').insert({
                                'nombre': nuevo_nombre, 
                                'equipo': nuevo_equipo,
                                'activo': True
                            }).execute()
                            st.markdown("<div class='success-box'>✅ Trabajador agregado correctamente.</div>", unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error al agregar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box'>❌ Error al agregar trabajador.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box'>❌ Debe ingresar un nombre.</div>", unsafe_allow_html=True)
        
        st.markdown("<h2 class='section-title'>Eliminar Trabajador</h2>", unsafe_allow_html=True)
        if trabajadores:
            trabajadores_activos = [t['nombre'] for t in trabajadores if t.get('activo', True)]
            if trabajadores_activos:
                trabajador_eliminar = st.selectbox("Selecciona un trabajador para eliminar:", options=trabajadores_activos)
                if st.button("Eliminar Trabajador"):
                    try:
                        # Actualizar el estado del trabajador a inactivo
                        supabase.from_('kpi_trabajadores').update({'activo': False}).eq('nombre', trabajador_eliminar).execute()
                        st.markdown("<div class='success-box'>✅ Trabajador eliminado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error al eliminar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='error-box'>❌ Error al eliminar trabajador.</div>", unsafe_allow_html=True)
            else:
                st.info("No hay trabajadores activos para eliminar.")
        else:
            st.info("No hay trabajadores registrados.")
    except Exception as e:
        logger.error(f"Error en gestión de trabajadores: {e}", exc_info=True)
        st.markdown("<div class='error-box'>❌ Error del sistema al gestionar trabajadores.</div>", unsafe_allow_html=True)

def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío"""
    st.markdown("<h1 class='guide-header'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    if not verificar_permisos('create_guides'):
        st.markdown("<div class='error-box'>❌ No tiene permisos para generar guías.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()
    
    if tiendas.empty or remitentes.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Formulario para generar guía
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>Generar Nueva Guía</h2>", unsafe_allow_html=True)
    
    with st.form("form_generar_guia"):
        col1, col2 = st.columns(2)
        with col1:
            store_name = st.selectbox("Tienda:", options=tiendas['name'].tolist(), key="store_select")
            brand = st.radio("Marca:", ["Fashion", "Tempo"], horizontal=True, key="brand_select")
        
        with col2:
            sender_name = st.selectbox("Remitente:", options=remitentes['name'].tolist(), key="sender_select")
            url = st.text_input("URL del Pedido:", key="url_input")
        
        submitted = st.form_submit_button("Generar Guía")
        
        if submitted:
            if not all([store_name, brand, url, sender_name]):
                st.markdown("<div class='error-box'>❌ Por favor, complete todos los campos.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
            elif not url.startswith(('http://', 'https://')):
                st.markdown("<div class='error-box'>❌ La URL debe comenzar con http:// o https://</div>", unsafe_allow_html=True)
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
                    st.success("✅ Guía generada correctamente. Puede ver la previsualización y exportarla.")
                else:
                    st.markdown("<div class='error-box'>❌ Error al guardar la guía.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Previsualización de la guía
    if st.session_state.get('show_preview', False):
        st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title'>Previsualización de la Guía</h2>", unsafe_allow_html=True)
        
        # Información de la guía
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='guide-metric'>Tienda: <strong>{st.session_state.get('store_select', '')}</strong></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='guide-metric'>Marca: <strong>{st.session_state.get('brand_select', '')}</strong></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='guide-metric'>Remitente: <strong>{st.session_state.get('sender_select', '')}</strong></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='guide-metric'>URL del Pedido: <a href='{st.session_state.get('url_input', '')}' target='_blank'>{st.session_state.get('url_input', '')}</a></div>", unsafe_allow_html=True)
        
        # Código QR
        st.markdown("<h3>Código QR:</h3>", unsafe_allow_html=True)
        qr_img = generar_qr_imagen(st.session_state.get('url_input', ''))
        st.image(qr_img, width=200)
        
        # Botones de exportación
        st.markdown("<div class='export-buttons'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Exportar a PDF", use_container_width=True):
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
                    label="⬇️ Descargar PDF",
                    data=pdf_data,
                    file_name=f"guia_{st.session_state.get('store_select', '')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        with col2:
            if st.button("🖨️ Marcar como Impresa", use_container_width=True):
                # Aquí iría la lógica para actualizar el estado de la guía
                st.markdown("<div class='success-box'>✅ Guía marcada como impresa.</div>", unsafe_allow_html=True)
                st.session_state.show_preview = False
                time.sleep(1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_historial_guias():
    """Muestra el historial de guías generadas"""
    st.markdown("<h1 class='guide-header'>🔍 Historial de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar historial de guías
    df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.markdown("<div class='warning-box'>⚠️ No hay guías generadas.</div>", unsafe_allow_html=True)
        return
    
    # Filtros
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>Filtros</h2>", unsafe_allow_html=True)
    
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
        st.markdown(f'<div class="kpi-card"><h3>Total de Guías</h3><p class="metric-value">{total_creados}</p></div>', unsafe_allow_html=True)
    
    with col2:
        pendientes = len(df_guias[df_guias['status'] == 'Pending'])
        st.markdown(f'<div class="kpi-card"><h3>Pendientes</h3><p class="metric-value">{pendientes}</p></div>', unsafe_allow_html=True)
    
    with col3:
        impresos = len(df_guias[df_guias['status'] == 'Printed'])
        st.markdown(f'<div class="kpi-card"><h3>Impresas</h3><p class="metric-value">{impresos}</p></div>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar tabla de guías
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>Guías Generadas</h2>", unsafe_allow_html=True)
    
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
    st.markdown("<div class='export-buttons'>", unsafe_allow_html=True)
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
                st.markdown("<div class='error-box'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
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

def mostrar_gestion_tiendas():
    """Muestra la interfaz para gestionar tiendas"""
    st.markdown("<h1 class='guide-header'>🏬 Gestión de Tiendas</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    if not verificar_permisos('all'):
        st.markdown("<div class='error-box'>❌ No tiene permisos para gestionar tiendas.</div>", unsafe_allow_html=True)
        return
    
    # Obtener lista de tiendas
    tiendas = obtener_tiendas()
    
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>Tiendas Registradas</h2>", unsafe_allow_html=True)
    
    if not tiendas.empty:
        st.dataframe(tiendas[['name']], use_container_width=True)
    else:
        st.info("No hay tiendas registradas.")
    
    st.markdown("<h2 class='section-title'>Agregar Nueva Tienda</h2>", unsafe_allow_html=True)
    with st.form("form_agregar_tienda"):
        nombre_tienda = st.text_input("Nombre de la tienda:")
        submitted = st.form_submit_button("Agregar Tienda")
        
        if submitted:
            if nombre_tienda:
                try:
                    # Verificar si la tienda ya existe
                    response = supabase.from_('guide_stores').select('*').eq('name', nombre_tienda).execute()
                    # CORRECCIÓN: Verificar si hay datos en la respuesta
                    if response and response.data:
                        st.markdown("<div class='error-box'>❌ La tienda ya existe.</div>", unsafe_allow_html=True)
                    else:
                        # Insertar nueva tienda
                        supabase.from_('guide_stores').insert({'name': nombre_tienda}).execute()
                        st.markdown("<div class='success-box'>✅ Tienda agregada correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    logger.error(f"Error al agregar tienda: {e}", exc_info=True)
                    st.markdown("<div class='error-box'>❌ Error al agregar tienda.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='error-box'>❌ Debe ingresar un nombre de tienda.</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_gestion_remitentes():
    """Muestra la interfaz para gestionar remitentes"""
    st.markdown("<h1 class='guide-header'>📬 Gestión de Remitentes</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    if not verificar_permisos('all'):
        st.markdown("<div class='error-box'>❌ No tiene permisos para gestionar remitentes.</div>", unsafe_allow_html=True)
        return
    
    # Obtener lista de remitentes
    remitentes = obtener_remitentes()
    
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>Remitentes Registrados</h2>", unsafe_allow_html=True)
    
    if not remitentes.empty:
        st.dataframe(remitentes[['name', 'address', 'phone']], use_container_width=True)
    else:
        st.info("No hay remitentes registrados.")
    
    st.markdown("<h2 class='section-title'>Agregar Nuevo Remitente</h2>", unsafe_allow_html=True)
    with st.form("form_agregar_remitente"):
        nombre = st.text_input("Nombre del remitente:")
        direccion = st.text_area("Dirección:")
        telefono = st.text_input("Teléfono:")
        submitted = st.form_submit_button("Agregar Remitente")
        
        if submitted:
            if all([nombre, direccion, telefono]):
                try:
                    # Verificar si el remitente ya existe
                    response = supabase.from_('guide_senders').select('*').eq('name', nombre).execute()
                    # CORRECCIÓN: Verificar si hay datos en la respuesta
                    if response and response.data:
                        st.markdown("<div class='error-box'>❌ El remitente ya existe.</div>", unsafe_allow_html=True)
                    else:
                        # Insertar nuevo remitente
                        supabase.from_('guide_senders').insert({
                            'name': nombre,
                            'address': direccion,
                            'phone': telefono
                        }).execute()
                        st.markdown("<div class='success-box'>✅ Remitente agregado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    logger.error(f"Error al agregar remitente: {e}", exc_info=True)
                    st.markdown("<div class='error-box'>❌ Error al agregar remitente.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='error-box'>❌ Debe completar todos los campos.</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_ayuda():
    """Muestra la página de ayuda y contacto"""
    st.markdown("<h1 class='guide-header'>❓ Ayuda y Contacto</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='guide-section'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title'>¿Cómo usar la aplicación?</h2>", unsafe_allow_html=True)
    
    st.info("""
    ### 📝 Guía de uso
    
    **Sistema de KPIs:**
    - **Dashboard de KPIs:** Visualiza el rendimiento diario de los equipos.
    - **Análisis Histórico:** Analiza tendencias y exporta reportes.
    - **Ingreso de Datos:** Ingresa los datos diarios de producción.
    - **Gestión de Trabajadores:** Administra el personal de la empresa.
    
    **Sistema de Guías:**
    - **Generar Guía:** Selecciona la tienda, la empresa (Fashion o Tempo), el remitente y pega la URL del pedido. Haz clic en "Generar Guía".
    - **Historial de Guías:** Consulta y exporta el historial de guías generadas.
    - **Gestión de Tiendas:** Administra las tiendas registradas en el sistema.
    - **Gestión de Remitentes:** Administra los remitentes disponibles para las guías.
    
    ### 📞 Soporte Técnico
    Si tienes algún problema o necesitas asistencia, por favor contacta a:
    
    **Ing. Wilson Perez**
    **Teléfono:** 0993052744
    """)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================================
# Función principal
# ================================

def main():
    """Función principal de la aplicación"""
    st.sidebar.title("🔧 Menú de Navegación")
    
    # Mostrar información del usuario si está logueado
    if 'user' in st.session_state:
        st.sidebar.markdown(f"**Usuario:** {st.session_state.user}")
        # Determinar rol
        if supabase:
            try:
                response = supabase.from_('kpi_users').select('role').eq('email', st.session_state.user).execute()
                # CORRECCIÓN: Verificar si hay datos en la respuesta
                if response and response.data:
                    role = response.data[0]['role'] if response.data else "usuario"
                    st.sidebar.markdown(f"**Rol:** {role.capitalize()}")
            except:
                st.sidebar.markdown("**Rol:** usuario")
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state.password_correct = False
            st.session_state.pop('user', None)
            st.session_state.pop('role', None)
            st.rerun()
    
    # Opciones del menú según los permisos
    menu_options = ["Dashboard KPIs", "Análisis Histórico", "Ingreso de Datos", "Gestión de Trabajadores"]
    
    if supabase and verificar_permisos('create_guides') or verificar_permisos('all'):
        menu_options.extend(["Generar Guías", "Historial de Guías"])
    
    if supabase and verificar_permisos('all'):
        menu_options.extend(["Gestión de Tiendas", "Gestión de Remitentes"])
    
    menu_options.append("Ayuda y Contacto")
    
    opcion = st.sidebar.radio("Selecciona una opción:", menu_options)
    
    if supabase is None:
        st.markdown("<div class='error-box'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Verificar autenticación
    if not verificar_password():
        return
    
    # Navegación
    if opcion == "Dashboard KPIs":
        mostrar_dashboard_kpis()
    elif opcion == "Análisis Histórico":
        mostrar_analisis_historico_kpis()
    elif opcion == "Ingreso de Datos":
        mostrar_ingreso_datos_kpis()
    elif opcion == "Gestión de Trabajadores":
        mostrar_gestion_trabajadores_kpis()
    elif opcion == "Generar Guías":
        mostrar_generacion_guias()
    elif opcion == "Historial de Guías":
        mostrar_historial_guias()
    elif opcion == "Gestión de Tiendas":
        mostrar_gestion_tiendas()
    elif opcion == "Gestión de Remitentes":
        mostrar_gestion_remitentes()
    elif opcion == "Ayuda y Contacto":
        mostrar_ayuda()

if __name__ == "__main__":
    main()
