import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
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
import requests
from io import BytesIO
from PIL import Image as PILImage
import os
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# ================================
# INICIALIZACIÓN DE SESSION STATE
# ================================
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = 0
if 'show_login' not in st.session_state:
    st.session_state.show_login = False

# ================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = "https://nsgdyqoqzlcyyameccqn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zZ2R5cW9xemxjeXlhbWVjY3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMTA3MzksImV4cCI6MjA3MTU4NjczOX0.jA6sem9IMts6aPeYlMsldbtQaEaKAuQaQ1xf03TdWso"
ADMIN_PASSWORD = "Wilo3161"
USER_PASSWORD = "User1234"

# Configuración de directorios
APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ================================
# INICIALIZACIÓN DE SUPABASE
# ================================
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
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ================================
# CSS PROFESIONAL - ESTILOS LOGÍSTICOS
# ================================
st.markdown("""
<style>
/* Torrecarga.css - Estilos Profesionales para Dashboard Logístico Aeropostale */

:root {
    --primary-blue: #004085;
    --secondary-blue: #007BFF;
    --success-green: #28A745;
    --warning-yellow: #FFC107;
    --danger-red: #DC3545;
    --dark-bg: #343a40;
    --light-bg: #f8f9fa;
    --text-dark: #333333;
    --text-light: #ffffff;
    --border-radius: 8px;
}

/* Estructura principal */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    margin: 0;
    padding: 0;
}

/* Contenedor principal de Streamlit */
.stApp {
    background-color: transparent;
}

/* Dashboard Header */
.dashboard-header {
    background: linear-gradient(90deg, #004085 0%, #007BFF 100%);
    padding: 25px 30px;
    border-radius: var(--border-radius);
    margin: 15px 0 25px 0;
    box-shadow: 0 4px 12px rgba(0, 64, 133, 0.15);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.header-title {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.header-subtitle {
    font-size: 1rem;
    opacity: 0.9;
    margin-top: 5px;
}

/* KPI Cards - Estilo Torre de Control */
.kpi-tower {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin: 25px 0;
}

.kpi-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
    border-left: 5px solid var(--secondary-blue);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;
    overflow: hidden;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, var(--secondary-blue), transparent);
}

.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0, 123, 255, 0.15);
}

.kpi-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
}

.kpi-icon {
    font-size: 2.2rem;
    margin-right: 15px;
    width: 50px;
    height: 50px;
    background: rgba(0, 123, 255, 0.1);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.kpi-title {
    font-size: 0.9rem;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    margin-bottom: 5px;
}

.kpi-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--primary-blue);
    line-height: 1.2;
    margin: 5px 0;
}

.kpi-change {
    font-size: 0.85rem;
    padding: 3px 8px;
    border-radius: 12px;
    display: inline-block;
    margin-top: 5px;
}

.kpi-change.positive {
    background: rgba(40, 167, 69, 0.1);
    color: var(--success-green);
}

.kpi-change.negative {
    background: rgba(220, 53, 69, 0.1);
    color: var(--danger-red);
}

/* Grid Layout para dashboard logístico */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin: 25px 0;
}

.grid-item {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* Tarjetas de equipo - Estilo logístico */
.team-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    margin-bottom: 15px;
    border: 1px solid #e9ecef;
    transition: all 0.2s ease;
}

.team-card:hover {
    border-color: var(--secondary-blue);
    background: #f8f9fa;
}

.team-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e9ecef;
}

.team-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--primary-blue);
}

.team-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-top: 15px;
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--primary-blue);
}

.stat-label {
    font-size: 0.8rem;
    color: #6c757d;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Alertas de logística */
.alert-banner {
    padding: 15px 20px;
    border-radius: var(--border-radius);
    margin: 15px 0;
    display: flex;
    align-items: center;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.alert-warning {
    background: linear-gradient(90deg, #fff3cd, #ffecb5);
    border-left: 5px solid var(--warning-yellow);
    color: #856404;
}

.alert-danger {
    background: linear-gradient(90deg, #f8d7da, #f5c6cb);
    border-left: 5px solid var(--danger-red);
    color: #721c24;
}

.alert-success {
    background: linear-gradient(90deg, #d4edda, #c3e6cb);
    border-left: 5px solid var(--success-green);
    color: #155724;
}

.alert-info {
    background: linear-gradient(90deg, #d1ecf1, #bee5eb);
    border-left: 5px solid #17a2b8;
    color: #0c5460;
}

/* Sidebar profesional */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #343a40 0%, #212529 100%);
    padding: 20px !important;
}

.sidebar-logo {
    padding: 20px 0;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 30px;
}

.logo-text {
    font-size: 1.8rem;
    font-weight: 700;
    color: white;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.logo-subtext {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 5px;
}

.sidebar-menu {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.menu-item {
    padding: 12px 15px;
    color: rgba(255, 255, 255, 0.8);
    border-radius: var(--border-radius);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.2s ease;
    font-weight: 500;
    border: none;
    background: none;
    width: 100%;
    text-align: left;
    cursor: pointer;
}

.menu-item:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    transform: translateX(5px);
}

.menu-item.active {
    background: var(--secondary-blue);
    color: white;
    box-shadow: 0 3px 10px rgba(0, 123, 255, 0.3);
}

.menu-icon {
    font-size: 1.2rem;
    width: 24px;
    text-align: center;
}

/* Controles de filtro estilo logístico */
.filter-panel {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    border: 1px solid #e9ecef;
}

.filter-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--primary-blue);
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Tablas de datos profesionales */
.data-table {
    background: white;
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    margin: 20px 0;
}

.table-header {
    background: var(--primary-blue);
    color: white;
    padding: 15px 20px;
    font-weight: 600;
}

.table-content {
    padding: 20px;
}

/* Botones de acción */
.stButton > button {
    background: linear-gradient(90deg, var(--secondary-blue), #0056b3);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: var(--border-radius);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    justify-content: center;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #0056b3, #004085);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.stDownloadButton > button {
    background: linear-gradient(90deg, #28A745, #1e7e34);
}

.stDownloadButton > button:hover {
    background: linear-gradient(90deg, #1e7e34, #155724);
}

/* Indicadores de estado */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 500;
}

.status-active {
    background: rgba(40, 167, 69, 0.1);
    color: var(--success-green);
}

.status-pending {
    background: rgba(255, 193, 7, 0.1);
    color: var(--warning-yellow);
}

.status-inactive {
    background: rgba(108, 117, 125, 0.1);
    color: #6c757d;
}

/* Gráficos y visualizaciones */
.chart-container {
    background: white;
    border-radius: var(--border-radius);
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.chart-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--primary-blue);
    margin-bottom: 15px;
}

/* Footer profesional */
.footer {
    text-align: center;
    padding: 20px;
    margin-top: 40px;
    color: #6c757d;
    font-size: 0.85rem;
    border-top: 1px solid #e9ecef;
}

.footer-links {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 10px;
}

.footer-link {
    color: var(--secondary-blue);
    text-decoration: none;
    transition: color 0.2s ease;
}

.footer-link:hover {
    color: var(--primary-blue);
    text-decoration: underline;
}

/* Sistema de autenticación */
.auth-container {
    max-width: 400px;
    margin: 50px auto;
    padding: 30px;
    background: white;
    border-radius: var(--border-radius);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.auth-title {
    color: var(--primary-blue);
    text-align: center;
    margin-bottom: 30px;
    font-size: 1.8rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .kpi-tower {
        grid-template-columns: 1fr;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    
    .team-stats {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .header-title {
        font-size: 1.8rem;
    }
    
    .auth-container {
        margin: 20px;
        padding: 20px;
    }
}

/* Estilos específicos para inputs y selects */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    border-radius: var(--border-radius);
    border: 1px solid #ced4da;
    padding: 8px 12px;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stNumberInput > div > div > input:focus,
.stDateInput > div > div > input:focus {
    border-color: var(--secondary-blue);
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Estilos para pestañas */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--border-radius) var(--border-radius) 0 0;
    padding: 10px 20px;
    background-color: #f8f9fa;
}

.stTabs [aria-selected="true"] {
    background-color: var(--secondary-blue);
    color: white;
}

/* Estilos para métricas */
.stMetric {
    background: white;
    padding: 15px;
    border-radius: var(--border-radius);
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

/* Estilos para expansores */
.streamlit-expanderHeader {
    background-color: #f8f9fa;
    border-radius: var(--border-radius);
    font-weight: 600;
}

.streamlit-expanderContent {
    background-color: white;
    border-radius: 0 0 var(--border-radius) var(--border-radius);
}
</style>
""", unsafe_allow_html=True)

# ================================
# FUNCIONES DE UTILIDAD COMPARTIDAS
# ================================
def validar_fecha(fecha: str) -> bool:
    """Valida que la fecha tenga el formato YYYY-MM-DD"""
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

def validar_distribuciones(valor: Any) -> bool:
    """Valida que el valor de distribuciones sea positivo y numérico"""
    try:
        num = float(valor)
        return num >= 0 and num <= 10000
    except (ValueError, TypeError):
        return False

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(pw.encode()).hexdigest()

# ================================
# FUNCIONES DE KPIs
# ================================
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

# ================================
# FUNCIONES DE ACCESO A DATOS (SUPABASE)
# ================================
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })
    
    try:
        response = supabase.from_('trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre', desc=False).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudieron obtener trabajadores: {response.error}")
            return pd.DataFrame({
                'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                          "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
                'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                          "Guías", "Ventas", "Ventas", "Ventas"]
            })
        
        if response and hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df
        else:
            logger.warning("No se encontraron trabajadores en Supabase")
            return pd.DataFrame(columns=['nombre', 'equipo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores de Supabase: {e}", exc_info=True)
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
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        
        if response and hasattr(response, 'data') and response.data:
            equipos = [item['equipo'] for item in response.data]
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
            equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
            equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
            return equipos_ordenados + equipos_restantes
        else:
            logger.warning("No se encontraron equipos en Supabase")
            return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos de Supabase: {e}", exc_info=True)
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos en la tabla de Supabase con mejor manejo de errores"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        st.error("Error de conexión con la base de datos")
        return False
    
    try:
        if not validar_fecha(fecha):
            logger.error(f"Fecha inválida: {fecha}")
            st.error("Formato de fecha inválido")
            return False
            
        registros = []
        for nombre, info in datos.items():
            if not all([
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                logger.warning(f"Datos inválidos para {nombre}, omitiendo guardado")
                st.error(f"Datos inválidos para {nombre}")
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
            response = supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
                
            logger.info(f"Datos guardados correctamente en Supabase para la fecha {fecha}")
            return True
        else:
            logger.warning("No hay registros válidos para guardar")
            st.error("No hay registros válidos para guardar")
            return False
    except Exception as e:
        logger.error(f"Error crítico al guardar datos: {e}", exc_info=True)
        st.error("Error crítico al guardar datos. Contacte al administrador.")
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
        
        if response and hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                df['fecha'] = pd.to_datetime(df['fecha'])
                df['cumplimiento_meta'] = np.where(df['cantidad'] >= df['meta'], 'Sí', 'No')
                df['diferencia_meta'] = df['cantidad'] - df['meta']
            return df
        else:
            logger.info("No se encontraron datos históricos en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def obtener_datos_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene los datos de una fecha específica desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        
        if response and hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            logger.info(f"No se encontraron datos para la fecha {fecha}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos de fecha {fecha} de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# FUNCIONES PARA DISTRIBUCIONES Y DEPENDENCIAS
# ================================
def obtener_distribuciones_semana(fecha_inicio_semana: str) -> dict:
    """Obtiene las distribuciones de la semana actual desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return {'tempo': 0, 'luis': 0}
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_semana, "%Y-%m-%d")
        fecha_fin = fecha_inicio + timedelta(days=6)
        
        response = supabase.from_('distribuciones_semanales').select('*').eq('semana', fecha_inicio_semana).execute()
        
        if response and hasattr(response, 'data') and response.data:
            distribucion = response.data[0]
            return {
                'tempo': distribucion.get('tempo_distribuciones', 0),
                'luis': distribucion.get('luis_distribuciones', 0)
            }
        else:
            logger.info(f"No se encontraron distribuciones para la semana {fecha_inicio_semana}")
            return {'tempo': 0, 'luis': 0}
    except Exception as e:
        logger.error(f"Error al obtener distribuciones semanales: {e}", exc_info=True)
        return {'tempo': 0, 'luis': 0}

def guardar_distribuciones_semanales(semana: str, tempo_distribuciones: int, luis_distribuciones: int, meta_semanal: int = 7500) -> bool:
    """Guarda las distribuciones semanales en Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        if not all([validar_fecha(semana),
                    validar_distribuciones(tempo_distribuciones),
                    validar_distribuciones(luis_distribuciones),
                    validar_distribuciones(meta_semanal)]):
            logger.error("Datos de distribuciones inválidos")
            return False
            
        response = supabase.from_('distribuciones_semanales').select('*').eq('semana', semana).execute()
        
        if response and hasattr(response, 'data') and response.data:
            update_data = {
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal,
                'updated_at': datetime.now().isoformat()
            }
            response = supabase.from_('distribuciones_semanales').update(update_data).eq('semana', semana).execute()
        else:
            insert_data = {
                'semana': semana,
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal
            }
            response = supabase.from_('distribuciones_semanales').insert(insert_data).execute()
        
        if response and not hasattr(response, 'error') or response.error is None:
            logger.info(f"Distribuciones semanales guardadas correctamente para la semana {semana}")
            return True
        else:
            logger.error(f"No se pudieron guardar las distribuciones semanales: {getattr(response, 'error', 'Error desconocido')}")
            return False
    except Exception as e:
        logger.error(f"Error al guardar distribuciones semanales: {e}", exc_info=True)
        return False

def obtener_dependencias_transferencias() -> pd.DataFrame:
    """Obtiene las dependencias entre transferidores y proveedores"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
            'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
        })
    
    try:
        response = supabase.from_('dependencias_transferencias').select('*').execute()
        
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.info("No se encontraron dependencias de transferencias")
            dependencias_por_defecto = [
                {'transferidor': 'Josué Imbacuán', 'proveedor_distribuciones': 'Tempo'},
                {'transferidor': 'Andrés Yépez', 'proveedor_distribuciones': 'Luis Perugachi'}
            ]
            for dependencia in dependencias_por_defecto:
                supabase.from_('dependencias_transferencias').upsert(dependencia).execute()
            
            return pd.DataFrame(dependencias_por_defecto)
    except Exception as e:
        logger.error(f"Error al obtener dependencias de transferencias: {e}", exc_info=True)
        return pd.DataFrame({
            'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
            'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
        })

def calcular_metas_semanales():
    """Calcula el progreso semanal y asigna responsabilidades"""
    fecha_inicio_semana = datetime.now().date() - timedelta(days=datetime.now().weekday())
    distribuciones_semana = obtener_distribuciones_semana(fecha_inicio_semana.strftime("%Y-%m-%d"))
    
    meta_semanal = 7500
    distribuciones_totales = distribuciones_semana['tempo'] + distribuciones_semana['luis']
    
    resultado = {
        'meta_semanal': meta_semanal,
        'distribuciones_totales': distribuciones_totales,
        'cumplimiento_porcentaje': (distribuciones_totales / meta_semanal) * 100 if meta_semanal > 0 else 0,
        'detalles': []
    }
    
    if distribuciones_semana['tempo'] < 3750:
        resultado['detalles'].append({
            'transferidor': 'Josué Imbacuán',
            'proveedor': 'Tempo',
            'distribuciones_recibidas': distribuciones_semana['tempo'],
            'distribuciones_requeridas': 3750,
            'estado': 'INSUFICIENTE'
        })
    
    if distribuciones_semana['luis'] < 3750:
        resultado['detalles'].append({
            'transferidor': 'Andrés Yépez',
            'proveedor': 'Luis Perugachi',
            'distribuciones_recibidas': distribuciones_semana['luis'],
            'distribuciones_requeridas': 3750,
            'estado': 'INSUFICIENTE'
        })
    
    return resultado

def verificar_alertas_abastecimiento():
    """Verifica y muestra alertas de abastecimiento"""
    resultado = calcular_metas_semanales()
    alertas = []
    
    for detalle in resultado['detalles']:
        if detalle['estado'] == 'INSUFICIENTE':
            alertas.append({
                'tipo': 'ABASTECIMIENTO',
                'mensaje': f"{detalle['proveedor']} no abasteció suficiente para {detalle['transferidor']}",
                'gravedad': 'ALTA',
                'accion': 'Revisar distribuciones de ' + detalle['proveedor']
            })
    
    return alertas

# ================================
# FUNCIONES DE VISUALIZACIÓN
# ================================
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
# FUNCIONES DE GUIAS
# ================================
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

def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único."""
    return f"AERO{str(record_id).zfill(8)}"

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
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"],
            'address': ["Dirección Centro", "Dirección Norte", "Dirección Sur"],
            'phone': ["0999999991", "0999999992", "0999999993"]
        })
    
    try:
        response = supabase.from_('guide_stores').select('*').execute()
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron tiendas en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"],
            'address': ["Dirección Centro", "Dirección Norte", "Dirección Sur"],
            'phone': ["0999999991", "0999999992", "0999999993"]
        })

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["ANDRÉS YÉPEZ", "JOSUÉ IMBACUAN"],
            'address': ["SAN ROQUE", "SAN ROQUE"],
            'phone': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.from_('guide_senders').select('*').execute()
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron remitentes en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["ANDRÉS YÉPEZ", "JOSUÉ IMBACUAN"],
            'address': ["SAN ROQUE", "SAN ROQUE"],
            'phone': ["0993052744", "0987654321"]
        })

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """Guarda una guía en Supabase"""
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
        response = supabase.from_('guide_logs').insert(data).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudo guardar la guía en Supabase: {response.error}")
            return False
        else:
            logger.info(f"Guía guardada correctamente para {store_name}")
            return True
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
        
        if response and hasattr(response, 'data') and response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        else:
            logger.info("No se encontraron guías en Supabase")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar historial de guías de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# FUNCIONES MEJORADAS PARA MANEJO DE IMÁGENES
# ================================
def verificar_imagen_existe(url: str) -> bool:
    """Verifica si una imagen existe en la URL proporcionada"""
    try:
        if url.startswith("file://"):
            local_path = url[7:]
            return os.path.exists(local_path)
        
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al verificar imagen {url}: {e}")
        return False

def obtener_url_logo(brand: str) -> str:
    """Obtiene la URL pública del logo de la marca desde Supabase Storage"""
    brand_lower = brand.lower()
    brand_upper = brand.upper()
    brand_capitalize = brand.capitalize()

    branded_logos = {
        "fashion": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Fashion.jpg",
        "tempo": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Tempo.jpg",
    }
    
    if brand_lower in branded_logos:
        logo_url = branded_logos[brand_lower]
        if verificar_imagen_existe(logo_url):
            logger.info(f"Imagen encontrada para marca {brand}: {logo_url}")
            return logo_url
    
    try:
        project_id = "nsgdyqoqzlcyyameccqn"
        bucket_name = 'images'
        
        posibles_nombres = [
            f"{brand_lower}.jpg",
            f"{brand_lower}.jpeg",
            f"{brand_lower}.png",
            f"{brand_lower}.webp",
            f"{brand_upper}.JPG",
            f"{brand_upper}.JPEG",
            f"{brand_upper}.PNG",
            f"{brand_capitalize}.jpg",
            f"{brand_capitalize}.jpeg",
            f"{brand_capitalize}.png"
        ]
        
        for file_name in posibles_nombres:
            logo_url = f"https://{project_id}.supabase.co/storage/v1/object/public/{bucket_name}/{file_name}"
            
            if verificar_imagen_existe(logo_url):
                logger.info(f"Imagen encontrada: {logo_url}")
                return logo_url
        
        local_backup = {
            "fashion": "local_images/fashion.jpg",
            "tempo": "local_images/tempo.jpg"
        }
        
        if brand_lower in local_backup:
            local_path = local_backup[brand_lower]
            if os.path.exists(local_path):
                logger.info(f"Usando imagen de respaldo local para {brand}: {local_path}")
                return f"file://{os.path.abspath(local_path)}"
        
        logger.error(f"No se encontró ninguna imagen para la marca {brand}")
        return None
            
    except Exception as e:
        logger.error(f"Error al obtener URL del logo para {brand}: {e}", exc_info=True)
        return None

def obtener_logo_imagen(brand: str) -> Image.Image:
    """Obtiene y devuelve la imagen del logo desde Supabase Storage o local"""
    logo_url = obtener_url_logo(brand)
    
    if not logo_url:
        logger.error(f"No se pudo obtener URL del logo para {brand}")
        return None
        
    try:
        logger.info(f"Intentando descargar imagen desde: {logo_url}")
        
        if logo_url.startswith("file://"):
            local_path = logo_url[7:]
            return Image.open(local_path)
        
        response = requests.get(logo_url, timeout=10)
        
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            logger.warning(f"No se pudo descargar el logo desde {logo_url}. Status: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error al cargar el logo: {e}")
        return None

def generar_pdf_guia(store_name: str, brand: str, url: str, sender_name: str, tracking_number: str) -> bytes:
    """Genera el PDF de la guía con el logo correspondiente"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(True, 15)
        
        # Fondo azul para el encabezado
        pdf.set_fill_color(0, 45, 98)
        pdf.rect(0, 0, 210, 35, style='F')
        
        # Insertar logo desde GitHub
        logos_urls = {
            "Fashion": "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg",
            "Tempo": "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
        }
        
        logo_url = logos_urls.get(brand)
        if logo_url:
            try:
                response = requests.get(logo_url)
                if response.status_code == 200:
                    logo_img = Image.open(BytesIO(response.content))
                    
                    if logo_img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', logo_img.size, (255, 255, 255))
                        background.paste(logo_img, mask=logo_img.split()[-1] if logo_img.mode in ('RGBA', 'P') else None)
                        logo_img = background
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        logo_img.save(temp_file.name, format='JPEG')
                        temp_logo_path = temp_file.name
                    
                    pdf.image(temp_logo_path, x=10, y=1, w=30)
                    os.unlink(temp_logo_path)
                else:
                    logger.error(f"No se pudo descargar el logo desde {logo_url}")
            except Exception as e:
                logger.error(f"Error al procesar e insertar el logo en el PDF: {e}")
        
        # Texto del encabezado
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_xy(0, 5)
        pdf.cell(210, 10, "AEROPOSTALE", 0, 1, "C")

        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_xy(0, 18)
        pdf.cell(210, 10, "CENTRO DE DISTRIBUCIÓN FASHION CLUB", 0, 1, "C")
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(40)
        
        y_start = pdf.get_y()
        
        # Sección Remitente
        pdf.set_font("Arial", "B", 20)
        pdf.cell(90, 10, "REMITENTE:", 0, 1)
        
        remitentes = obtener_remitentes()
        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
        
        pdf.set_font("Arial", "", 14)
        pdf.multi_cell(90, 8, f"{remitente_info['name']}\n{remitente_info['address']}")
        
        pdf.ln(5)
        
        # Sección Destinatario
        pdf.set_font("Arial", "B", 20)
        pdf.cell(90, 10, "DESTINATARIO:", 0, 1)
        
        pdf.set_font("Arial", "", 14)
        pdf.cell(90, 8, tracking_number, 0, 1)
        
        tiendas = obtener_tiendas()
        tienda_info = tiendas[tiendas['name'] == store_name].iloc[0]
        
        if 'address' in tienda_info:
            pdf.multi_cell(90, 8, tienda_info['address'])
        
        pdf.ln(5)
        
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(90, 8, store_name, 0, 1)
        
        pdf.ln(5)
        
        if 'phone' in tienda_info:
            pdf.cell(90, 8, f"TEL.: {tienda_info['phone']}", 0, 1)
        
        # Código QR
        qr_img = generar_qr_imagen(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            qr_img.save(temp_file.name)
            temp_qr_path = temp_file.name
        
        pdf.image(temp_qr_path, x=140, y=y_start, w=65)
        os.unlink(temp_qr_path)
        
        return pdf.output(dest="S").encode("latin1")
        
    except Exception as e:
        logger.error(f"Error al generar PDF de guía: {e}", exc_info=True)
        return b""

def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    """Convierte un objeto de imagen de PIL a bytes."""
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()

def eliminar_guia(guia_id: int) -> bool:
    """Elimina una guía de la base de datos Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        response = supabase.from_('guide_logs').delete().eq('id', guia_id).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudo eliminar la guía: {response.error}")
            return False
        else:
            logger.info(f"Guía {guia_id} eliminada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al eliminar guía: {e}", exc_info=True)
        return False

# ===========================================================
# CLASE DE RECONCILIACIÓN LOGÍSTICA
# ===========================================================
class StreamlitLogisticsReconciliation:
    def __init__(self):
        self.df_facturas = None
        self.df_manifiesto = None
        self.guides_facturadas = []
        self.guides_anuladas = []
        self.guides_sobrantes_factura = []
        self.kpis = {
            'total_facturadas': 0,
            'total_anuladas': 0,
            'total_sobrantes_factura': 0,
            'total_value': 0.0,
            'value_facturadas': 0.0,
            'value_anuladas': 0.0,
            'top_cities': pd.Series(dtype="object"),
            'top_stores': pd.Series(dtype="object"),
            'spending_by_city': pd.Series(dtype="float"),
            'spending_by_store': pd.Series(dtype="float"),
            'avg_shipment_value': 0.0,
            'shipment_volume': pd.Series(dtype="int"),
            'anuladas_by_destinatario': pd.Series(dtype="object")
        }

    def identify_guide_column(self, df):
        guide_pattern = r'(LC\d+|\d{6,})'
        for col in df.columns:
            extracted = df[col].astype(str).str.extract(guide_pattern, expand=False)
            if extracted.notna().mean() > 0.3:
                return col
        return None

    def identify_destination_city_column(self, df):
        ecuador_cities = [
            'GUAYAQUIL', 'QUITO', 'IBARRA', 'CUENCA', 'MACHALA',
            'SANGOLQUI', 'LATACUNGA', 'AMBATO', 'PORTOVIEJO',
            'MILAGRO', 'LOJA', 'RIOBAMBA', 'ESMERALDAS', 'LAGO AGRIO'
        ]
        for col in df.columns:
            if df[col].dtype == 'object':
                upper_col = df[col].astype(str).str.upper()
                if upper_col.isin(ecuador_cities).mean() > 0.3:
                    return col
        return None

    def identify_store_column(self, df):
        store_keywords = ['AEROPOSTALE', 'LOCAL', 'SHOPPING', 'MALL', 'CENTRO COMERCIAL']
        regex = '|'.join(store_keywords)
        for col in df.columns:
            if df[col].dtype == 'object':
                if df[col].astype(str).str.upper().str.contains(regex).mean() > 0.4:
                    return col
        return None

    def identify_monetary_column_fallback(self, df):
        for col in df.columns:
            if df[col].astype(str).str.match(r'^\d{6,}$').mean() < 0.5:
                try:
                    numeric_vals = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
                    if numeric_vals.notna().mean() > 0.7 and (numeric_vals > 0).mean() > 0.5:
                        return col
                except Exception:
                    continue
        return None

    def identify_date_column(self, df):
        date_patterns = [r'\d{4}-\d{2}-\d{2}', r'\d{2}/\d{2}/\d{4}', r'\d{2}-\d{2}-\d{4}']
        for col in df.columns:
            col_str = df[col].astype(str)
            for pattern in date_patterns:
                if col_str.str.match(pattern).mean() > 0.7:
                    return col
        return None

    def identify_destinatario_column(self, df):
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['destin', 'cliente', 'nombre', 'recipient']):
                return col
        return None

    def process_files(self, factura_file, manifiesto_file):
        try:
            self.df_facturas = pd.read_excel(factura_file, sheet_name=0, header=0)
            self.df_manifiesto = pd.read_excel(manifiesto_file, sheet_name=0, header=0)

            self.df_facturas = self.df_facturas.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            self.df_manifiesto = self.df_manifiesto.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            factura_guide_col = self.identify_guide_column(self.df_facturas)
            if not factura_guide_col:
                st.error("No se pudo identificar una columna de guías válida en el archivo de facturas.")
                return False

            manifiesto_guide_col = self.identify_guide_column(self.df_manifiesto)
            if not manifiesto_guide_col:
                st.error("No se pudo identificar una columna de guías válida en el archivo de manifiesto.")
                return False

            guide_pattern = r'(LC\d+|\d{6,})'

            self.df_facturas['GUIDE_CLEAN'] = self.df_facturas[factura_guide_col].astype(str).str.strip().str.upper().str.extract(guide_pattern, expand=False)
            invalid_guides_factura = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isna()]
            if not invalid_guides_factura.empty:
                st.warning(f"⚠️ Se encontraron {len(invalid_guides_factura)} filas en Facturas sin formato de guía válido. Serán ignoradas:")
                st.dataframe(invalid_guides_factura[[factura_guide_col]].rename(columns={factura_guide_col: "Guías con formato incorrecto"}), use_container_width=True)
            self.df_facturas.dropna(subset=['GUIDE_CLEAN'], inplace=True)
            
            self.df_manifiesto['GUIDE_CLEAN'] = self.df_manifiesto[manifiesto_guide_col].astype(str).str.strip().str.upper().str.extract(guide_pattern, expand=False)
            invalid_guides_manifiesto = self.df_manifiesto[self.df_manifiesto['GUIDE_CLEAN'].isna()]
            if not invalid_guides_manifiesto.empty:
                st.warning(f"⚠️ Se encontraron {len(invalid_guides_manifiesto)} filas en Manifiesto sin formato de guía válido. Serán ignoradas:")
                st.dataframe(invalid_guides_manifiesto[[manifiesto_guide_col]].rename(columns={manifiesto_guide_col: "Guías con formato incorrecto"}), use_container_width=True)
            self.df_manifiesto.dropna(subset=['GUIDE_CLEAN'], inplace=True)

            facturas_set = set(self.df_facturas['GUIDE_CLEAN'])
            manifiesto_set = set(self.df_manifiesto['GUIDE_CLEAN'])

            self.guides_facturadas = list(facturas_set & manifiesto_set)
            self.guides_anuladas = list(manifiesto_set - facturas_set)
            self.guides_sobrantes_factura = list(facturas_set - manifiesto_set)

            self.calculate_kpis()
            return True

        except Exception as e:
            st.error(f"Error procesando archivos: {str(e)}")
            return False

    def calculate_kpis(self):
        self.kpis['total_facturadas'] = len(self.guides_facturadas)
        self.kpis['total_anuladas'] = len(self.guides_anuladas)
        self.kpis['total_sobrantes_factura'] = len(self.guides_sobrantes_factura)

        facturadas_df = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)].copy()
        manifest_fact = self.df_manifiesto[self.df_manifiesto['GUIDE_CLEAN'].isin(self.guides_facturadas)].copy()
        
        if not facturadas_df.empty and not manifest_fact.empty:
             facturadas_merged = pd.merge(facturadas_df, manifest_fact, on='GUIDE_CLEAN', suffixes=('_fact', '_man'), how='left')
        else:
            facturadas_merged = facturadas_df.copy()

        monetary_col = None
        for col in self.df_facturas.columns:
            if 'SUBTOTAL' in str(col).upper():
                monetary_col = col
                st.success(f"Columna de subtotal encontrada: **'{monetary_col}'**")
                break
        
        if not monetary_col:
            monetary_col = self.identify_monetary_column_fallback(self.df_facturas)
            if monetary_col:
                st.info(f"No se encontró 'Subtotal'. Usando columna numérica detectada: **'{monetary_col}'**")

        if not monetary_col:
            st.error("Error crítico: No se pudo encontrar ninguna columna de valores monetarios en el archivo de facturas.")
            return

        city_col = self.identify_destination_city_column(facturadas_merged)
        store_col = self.identify_store_column(facturadas_merged)
        date_col = self.identify_date_column(facturadas_merged)
        destinatario_col = self.identify_destinatario_column(self.df_manifiesto)

        if not facturadas_merged.empty:
            if monetary_col in facturadas_merged.columns:
                facturadas_merged[monetary_col] = pd.to_numeric(facturadas_merged[monetary_col].astype(str).str.replace(',', '.'), errors='coerce')
            if date_col in facturadas_merged.columns:
                if facturadas_merged[date_col].dtype in [float, int]:
                    facturadas_merged[date_col] = pd.to_datetime('1899-12-30') + pd.to_timedelta(facturadas_merged[date_col], unit='D')
                else:
                    facturadas_merged[date_col] = pd.to_datetime(facturadas_merged[date_col], errors='coerce', dayfirst=True)

            if city_col: self.kpis['top_cities'] = facturadas_merged[city_col].value_counts().head(10)
            if store_col: self.kpis['top_stores'] = facturadas_merged[store_col].value_counts().head(10)
            if city_col and monetary_col: self.kpis['spending_by_city'] = facturadas_merged.groupby(city_col)[monetary_col].sum().sort_values(ascending=False).head(10)
            if store_col and monetary_col: self.kpis['spending_by_store'] = facturadas_merged.groupby(store_col)[monetary_col].sum().sort_values(ascending=False).head(10)

            if monetary_col in facturadas_merged.columns:
                valid_amounts = facturadas_merged[monetary_col].dropna()
                if not valid_amounts.empty: self.kpis['avg_shipment_value'] = valid_amounts.mean()

            if date_col in facturadas_merged.columns:
                valid_dates = facturadas_merged[facturadas_merged[date_col].notna()].copy()
                valid_dates['MONTH'] = valid_dates[date_col].dt.to_period('M')
                self.kpis['shipment_volume'] = valid_dates['MONTH'].value_counts().sort_index()

        anuladas_df = self.df_manifiesto[self.df_manifiesto['GUIDE_CLEAN'].isin(self.guides_anuladas)].copy()
        if destinatario_col and destinatario_col in anuladas_df.columns:
            self.kpis['anuladas_by_destinatario'] = anuladas_df[destinatario_col].value_counts().head(10)
        
        self.df_facturas[monetary_col] = pd.to_numeric(self.df_facturas[monetary_col].astype(str).str.replace(',', '.'), errors='coerce')
        self.kpis['total_value'] = self.df_facturas[monetary_col].sum()
        
        facturadas_df_monetary = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)]
        self.kpis['value_facturadas'] = facturadas_df_monetary[monetary_col].sum()
        self.kpis['value_anuladas'] = 0.0

    def generate_report(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Reporte de Reconciliación Logística", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Indicadores Clave de Desempeño", styles['Heading2']))
        
        kpi_data = [
            ['Métrica', 'Valor'],
            ['Total Concordantes', self.kpis['total_facturadas']],
            ['Total Anuladas', self.kpis['total_anuladas']],
            ['Total Sobrantes en Factura', self.kpis['total_sobrantes_factura']],
            ['Valor Total (Bruto Facturas)', f"${self.kpis['total_value']:,.2f}"],
            ['Valor Concordante', f"${self.kpis['value_facturadas']:,.2f}"],
            ['Valor Anuladas', f"${self.kpis['value_anuladas']:,.2f}"],
            ['Valor Promedio de Envío (Concordantes)', f"${self.kpis['avg_shipment_value']:,.2f}" if self.kpis['avg_shipment_value'] else 'N/A']
        ]
        table = Table(kpi_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        def add_series_table(title, series, is_float=False):
            if not series.empty:
                elements.append(Paragraph(title, styles['Heading2']))
                data = [['Categoría', 'Valor']] + [[str(idx), f"${val:,.2f}" if is_float else val] for idx, val in series.items()]
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))

        add_series_table("Top Ciudades (Envíos Concordantes)", self.kpis['top_cities'])
        add_series_table("Top Tiendas (Envíos Concordantes)", self.kpis['top_stores'])
        add_series_table("Gasto por Ciudad (Envíos Concordantes)", self.kpis['spending_by_city'], is_float=True)
        add_series_table("Gasto por Tienda (Envíos Concordantes)", self.kpis['spending_by_store'], is_float=True)
        add_series_table("Anuladas por Destinatario", self.kpis['anuladas_by_destinatario'])
        
        if not self.kpis['shipment_volume'].empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            shipment_volume_str_index = self.kpis['shipment_volume'].copy()
            shipment_volume_str_index.index = shipment_volume_str_index.index.astype(str)
            shipment_volume_str_index.plot(kind='bar', ax=ax, color='skyblue')

            ax.set_title('Volumen de Envíos por Mes (Concordantes)')
            ax.set_ylabel('Número de Guías')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='PNG', dpi=300)
            img_buffer.seek(0)
            
            elements.append(Paragraph("Volumen de Envíos Mensual", styles['Heading2']))
            elements.append(ReportLabImage(img_buffer, width=450, height=225))
            elements.append(Spacer(1, 12))
            plt.close(fig)

        doc.build(elements)
        buffer.seek(0)
        return buffer

# ================================
# SISTEMA DE AUTENTICACIÓN
# ================================
def verificar_password(tipo_requerido: str = "admin") -> bool:
    """Verifica si el usuario tiene permisos para la sección requerida"""
    if tipo_requerido == "public":
        return True
    
    if 'user_type' not in st.session_state:
        return False
    
    if tipo_requerido == "admin":
        return st.session_state.user_type == "admin"
    elif tipo_requerido == "user":
        return st.session_state.user_type in ["admin", "user"]
    return False

def solicitar_autenticacion(tipo_requerido: str = "admin"):
    """Muestra un formulario de autenticación para diferentes tipos de usuario"""
    st.markdown(f"""
    <div class='auth-container'>
        <div class='auth-title'>🔐 Acceso Restringido</div>
        <p style='text-align: center; color: #6c757d; margin-bottom: 25px;'>
            Ingrese la contraseña para acceso de {'Administrador' if tipo_requerido == 'admin' else 'Usuario'}
        </p>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña:", type="password", key="auth_password", 
                            placeholder="Ingrese su contraseña", 
                            label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.button("Ingresar", use_container_width=True)
        cancel = st.button("Cancelar", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if cancel:
        st.session_state.show_login = False
        st.rerun()
    
    if submitted:
        if tipo_requerido == "admin" and password == ADMIN_PASSWORD:
            st.session_state.user_type = "admin"
            st.session_state.password_correct = True
            st.session_state.show_login = False
            st.success("✅ Acceso de administrador concedido")
            time.sleep(1)
            st.rerun()
        elif tipo_requerido == "user" and password == USER_PASSWORD:
            st.session_state.user_type = "user"
            st.session_state.password_correct = True
            st.session_state.show_login = False
            st.success("✅ Acceso de usuario concedido")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

# ================================
# FUNCIONES PARA MOSTRAR ESTADO DE ABASTECIMIENTO
# ================================
def mostrar_estado_abastecimiento():
    """Muestra el estado de abastecimiento para transferencias"""
    resultado = calcular_metas_semanales()
    
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>📦 Estado de Abastecimiento Semanal</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">🎯</div>
                <div>
                    <div class="kpi-title">Meta Semanal</div>
                    <div class="kpi-value">{resultado['meta_semanal']:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">📦</div>
                <div>
                    <div class="kpi-title">Distribuciones Totales</div>
                    <div class="kpi-value">{resultado['distribuciones_totales']:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tendencia_clase = "positive" if resultado['cumplimiento_porcentaje'] >= 100 else "negative"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">📊</div>
                <div>
                    <div class="kpi-title">Cumplimiento</div>
                    <div class="kpi-value">{resultado['cumplimiento_porcentaje']:.1f}%</div>
                    <div class="kpi-change {tendencia_clase}">Meta: 100%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if resultado['detalles']:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ Problemas de Abastecimiento Detectados</div>", unsafe_allow_html=True)
        
        for detalle in resultado['detalles']:
            st.markdown(f"""
            <div class="alert-banner alert-danger">
                <strong>{detalle['transferidor']}</strong> no recibió suficientes distribuciones de <strong>{detalle['proveedor']}</strong><br>
                • Recibido: {detalle['distribuciones_recibidas']:,.0f}<br>
                • Requerido: {detalle['distribuciones_requeridas']:,.0f}<br>
                • Déficit: {detalle['distribuciones_requeridas'] - detalle['distribuciones_recibidas']:,.0f}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='alert-banner alert-success'>✅ Abastecimiento adecuado para cumplir la meta semanal</div>", unsafe_allow_html=True)

def mostrar_gestion_distribuciones():
    """Muestra la interfaz para gestionar distribuciones semanales"""
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📊 Gestión de Distribuciones Semanales</h1></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    fecha_actual = datetime.now().date()
    fecha_inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fecha_inicio_semana_str = fecha_inicio_semana.strftime("%Y-%m-%d")
    
    distribuciones_existentes = obtener_distribuciones_semana(fecha_inicio_semana_str)
    
    with st.form("form_distribuciones_semanales"):
        st.markdown("<div class='filter-panel'><h3 class='filter-title'>📅 Distribuciones de la Semana</h3></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            tempo_distribuciones = st.number_input(
                "Distribuciones de Tempo:", 
                min_value=0, 
                value=distribuciones_existentes.get('tempo', 0),
                key="tempo_distribuciones"
            )
        
        with col2:
            luis_distribuciones = st.number_input(
                "Distribuciones de Luis Perugachi:", 
                min_value=0, 
                value=distribuciones_existentes.get('luis', 0),
                key="luis_distribuciones"
            )
        
        meta_semanal = st.number_input(
            "Meta Semanal:", 
            min_value=0, 
            value=7500,
            key="meta_semanal"
        )
        
        submitted = st.form_submit_button("Guardar Distribuciones", use_container_width=True)
        
        if submitted:
            if guardar_distribuciones_semanales(fecha_inicio_semana_str, tempo_distribuciones, luis_distribuciones, meta_semanal):
                st.markdown("<div class='alert-banner alert-success'>✅ Distribuciones guardadas correctamente!</div>", unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
            else:
                st.markdown("<div class='alert-banner alert-danger'>❌ Error al guardar las distribuciones.</div>", unsafe_allow_html=True)
    
    mostrar_estado_abastecimiento()
    
    alertas = verificar_alertas_abastecimiento()
    if alertas:
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>🚨 Alertas de Abastecimiento</h2></div>", unsafe_allow_html=True)
        for alerta in alertas:
            if alerta['gravedad'] == 'ALTA':
                st.markdown(f"<div class='alert-banner alert-danger'>{alerta['mensaje']}<br>Acción: {alerta['accion']}</div>", unsafe_allow_html=True)

# ================================
# COMPONENTES DE LA APLICACIÓN
# ================================
def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📊 Dashboard de KPIs Aeropostale</h1><div class='header-subtitle'>Control Logístico en Tiempo Real</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    alertas = verificar_alertas_abastecimiento()
    if alertas:
        for alerta in alertas:
            if alerta['gravedad'] == 'ALTA':
                st.markdown(f"<div class='alert-banner alert-danger'>🚨 {alerta['mensaje']}</div>", unsafe_allow_html=True)
    
    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>📅 Selecciona el rango de fechas a visualizar:</h3>", unsafe_allow_html=True)
    
    if not df.empty and 'fecha' in df.columns:
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
            return
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input(
                "Fecha de inicio:",
                value=fechas_disponibles[-1] if fechas_disponibles else datetime.now().date(),
                min_value=fechas_disponibles[-1] if fechas_disponibles else datetime.now().date(),
                max_value=fechas_disponibles[0] if fechas_disponibles else datetime.now().date()
            )
        with col2:
            fecha_fin = st.date_input(
                "Fecha de fin:",
                value=fechas_disponibles[0] if fechas_disponibles else datetime.now().date(),
                min_value=fechas_disponibles[-1] if fechas_disponibles else datetime.now().date(),
                max_value=fechas_disponibles[0] if fechas_disponibles else datetime.now().date()
            )
    else:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay datos disponibles.</div>", unsafe_allow_html=True)
        return
    st.markdown("</div>", unsafe_allow_html=True)
    
    if fecha_inicio > fecha_fin:
        st.markdown("<div class='alert-banner alert-danger'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    df_rango = df[(df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)]
    if df_rango.empty:
        st.markdown(f"<div class='alert-banner alert-warning'>⚠️ No hay datos disponibles para el rango de fechas {fecha_inicio} a {fecha_fin}.</div>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<p style='color: #6c757d; font-size: 1.1em; text-align: center;'>Datos para el rango de fechas: {fecha_inicio} a {fecha_fin}</p>", unsafe_allow_html=True)
    
    # Cálculos globales
    total_cantidad = df_rango['cantidad'].sum()
    total_meta = df_rango['meta'].sum()
    total_horas = df_rango['horas_trabajo'].sum()
    avg_eficiencia = (df_rango['eficiencia'] * df_rango['horas_trabajo']).sum() / total_horas if total_horas > 0 else 0
    avg_productividad = df_rango['productividad'].mean()
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0
    
    st.markdown("<div class='kpi-tower'>", unsafe_allow_html=True)
    
    # KPI 1: Total Producción
    cumplimiento_meta = (total_cantidad / total_meta * 100) if total_meta > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon">📦</div>
            <div>
                <div class="kpi-title">Total Producción</div>
                <div class="kpi-value">{total_cantidad:,.0f}</div>
                <div class="kpi-change {'positive' if cumplimiento_meta >= 100 else 'negative'}">
                    Meta: {total_meta:,.0f} | {cumplimiento_meta:.1f}%
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI 2: Eficiencia Promedio
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon">🎯</div>
            <div>
                <div class="kpi-title">Eficiencia Promedio</div>
                <div class="kpi-value">{avg_eficiencia:.1f}%</div>
                <div class="kpi-change {'positive' if avg_eficiencia >= 100 else 'negative'}">
                    Meta: 100% | {avg_eficiencia - 100:.1f}%
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI 3: Productividad Promedio
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon">⚡</div>
            <div>
                <div class="kpi-title">Productividad Promedio</div>
                <div class="kpi-value">{avg_productividad:.1f}</div>
                <div class="kpi-title">unidades/hora</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPI 4: Productividad Total
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-header">
            <div class="kpi-icon">⏱️</div>
            <div>
                <div class="kpi-title">Productividad Total</div>
                <div class="kpi-value">{productividad_total:.1f}</div>
                <div class="kpi-title">unidades/hora ({total_horas:.1f} h)</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    mostrar_estado_abastecimiento()
    
    # Cumplimiento de Metas Mensuales
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>📅 Cumplimiento de Metas Mensuales</h2></div>", unsafe_allow_html=True)
    
    current_month = fecha_inicio.month
    current_year = fecha_inicio.year
    
    df_month = df[(df['fecha'].dt.month == current_month) & 
                  (df['fecha'].dt.year == current_year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    if not df_transferencias_month.empty:
        meta_mensual_transferencias = df_transferencias_month['meta_mensual'].iloc[0]
    else:
        meta_mensual_transferencias = 70000
    
    cum_transferencias = df_transferencias_month['cantidad'].sum()
    cumplimiento_transferencias = (cum_transferencias / meta_mensual_transferencias * 100) if meta_mensual_transferencias > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">📈</div>
                <div>
                    <div class="kpi-title">Meta Mensual Transferencias</div>
                    <div class="kpi-value">{cumplimiento_transferencias:.1f}%</div>
                    <div class="kpi-title">Acumulado: {cum_transferencias:,.0f} / Meta: {meta_mensual_transferencias:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
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
        fig.add_hline(y=meta_mensual_transferencias, line_dash="dash", line_color="white", annotation_text="Meta Mensual")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No hay datos para el gráfico de Transferencias.")
    
    # Rendimiento por Equipos
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>👥 Rendimiento por Equipos</h2></div>", unsafe_allow_html=True)
    
    equipos = df_rango['equipo'].unique()
    orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
    equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
    equipos_finales = equipos_ordenados + equipos_restantes
    
    for equipo in equipos_finales:
        df_equipo = df_rango[df_rango['equipo'] == equipo]
        
        st.markdown(f"<div class='team-card'><div class='team-header'><span class='team-name'>{equipo}</span></div>", unsafe_allow_html=True)
        
        total_equipo = df_equipo['cantidad'].sum()
        meta_equipo = df_equipo['meta'].sum()
        horas_equipo = df_equipo['horas_trabajo'].sum()
        eficiencia_equipo = (df_equipo['eficiencia'] * df_equipo['horas_trabajo']).sum() / horas_equipo if horas_equipo > 0 else 0
        productividad_equipo = total_equipo / horas_equipo if horas_equipo > 0 else 0
        
        st.markdown("<div class='team-stats'>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-item">
            <div class="stat-value">{total_equipo:,.0f}</div>
            <div class="stat-label">Producción</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-item">
            <div class="stat-value">{eficiencia_equipo:.1f}%</div>
            <div class="stat-label">Eficiencia</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-item">
            <div class="stat-value">{productividad_equipo:.1f}</div>
            <div class="stat-label">Productividad/h</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Mostrar trabajadores del equipo
        for _, row in df_equipo.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                color = "#28A745" if row['eficiencia'] >= 100 else "#DC3545"
                st.markdown(f"""
                <div class="team-card">
                    <div class="team-header">
                        <span class="team-name">{row['nombre']}</span>
                        <span class="status-indicator {'status-active' if row['eficiencia'] >= 100 else 'status-pending'}">
                            {row['eficiencia']:.1f}%
                        </span>
                    </div>
                    <div class="team-stats">
                        <div class="stat-item">
                            <div class="stat-value">{row['cantidad']}</div>
                            <div class="stat-label">Unidades</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{row['productividad']:.1f}</div>
                            <div class="stat-label">Prod/h</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{row['horas_trabajo']:.1f}</div>
                            <div class="stat-label">Horas</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                comentario = row.get('comentario', None)
                if pd.notna(comentario) and str(comentario).strip() != "":
                    st.markdown(f"""
                    <div class="alert-banner alert-info">
                        <strong>💬 Comentario:</strong><br>
                        {comentario}
                    </div>
                    """, unsafe_allow_html=True)

def mostrar_analisis_historico_kpis():
    """Muestra el análisis histórico de KPIs"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📈 Análisis Histórico de KPIs</h1><div class='header-subtitle'>Análisis de tendencias y reportes</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    df = cargar_historico_db()
    if df.empty:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    df['dia'] = df['fecha'].dt.date
    fecha_min = df['dia'].min()
    fecha_max = df['dia'].max()
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=fecha_max, min_value=fecha_min, max_value=fecha_max)
    with col3:
        trabajador = st.selectbox("Filtrar por trabajador:", options=["Todos"] + list(df['nombre'].unique()))
    st.markdown("</div>", unsafe_allow_html=True)
    
    if fecha_inicio > fecha_fin:
        st.markdown("<div class='alert-banner alert-danger'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    df_filtrado = df[(df['dia'] >= fecha_inicio) & (df['dia'] <= fecha_fin)]
    if trabajador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador]
    
    if df_filtrado.empty:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay datos en el rango de fechas seleccionado.</div>", unsafe_allow_html=True)
        return
    
    # Botones de exportación
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>📤 Exportar Datos</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                export_df = df_filtrado.copy()
                
                if 'fecha' in export_df.columns:
                    export_df['fecha'] = pd.to_datetime(export_df['fecha']).dt.strftime('%Y-%m-%d')
                
                export_df = export_df.fillna('N/A')
                
                columnas_ordenadas = [
                    'fecha', 'nombre', 'equipo', 'actividad', 'cantidad', 'meta', 
                    'eficiencia', 'productividad', 'horas_trabajo', 'meta_mensual', 'comentario'
                ]
                columnas_finales = [col for col in columnas_ordenadas if col in export_df.columns]
                export_df = export_df[columnas_finales]
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Datos_KPIs', index=False)
                
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
                st.markdown("<div class='alert-banner alert-danger'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        if st.button("📄 Exportar a PDF", use_container_width=True):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Reporte de KPIs - Aeropostale", ln=True, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Período: {fecha_inicio} a {fecha_fin}", ln=True)
                pdf.ln(10)
                
                pdf.set_font("Arial", "B", 10)
                columnas = ['Fecha', 'Nombre', 'Equipo', 'Actividad', 'Cantidad', 'Meta', 'Eficiencia']
                for i, col in enumerate(columnas):
                    pdf.cell(27, 10, col, border=1)
                pdf.ln()
                
                pdf.set_font("Arial", "", 8)
                for _, row in df_filtrado.iterrows():
                    pdf.cell(27, 10, str(row['fecha'].strftime('%Y-%m-%d') if pd.notna(row['fecha']) else ''), border=1)
                    pdf.cell(27, 10, str(row['nombre'])[:15] if pd.notna(row['nombre']) else '', border=1)
                    pdf.cell(27, 10, str(row['equipo'])[:10] if pd.notna(row['equipo']) else '', border=1)
                    pdf.cell(27, 10, str(row['actividad'])[:10] if pd.notna(row['actividad']) else '', border=1)
                    pdf.cell(27, 10, str(row['cantidad']) if pd.notna(row['cantidad']) else '', border=1)
                    pdf.cell(27, 10, str(row['meta']) if pd.notna(row['meta']) else '', border=1)
                    pdf.cell(27, 10, f"{row['eficiencia']:.1f}%" if pd.notna(row['eficiencia']) else '', border=1)
                    pdf.ln()
                
                pdf_data = pdf.output(dest="S").encode("latin1")
                
                st.download_button(
                    label="⬇️ Descargar reporte PDF",
                    data=pdf_data,
                    file_name=f"reporte_kpis_{fecha_inicio}_a_{fecha_fin}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar a PDF: {e}", exc_info=True)
                st.markdown("<div class='alert-banner alert-danger'>❌ Error al exportar a PDF.</div>", unsafe_allow_html=True)
    
    with col3:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"kpis_historico_{fecha_inicio}_a_{fecha_fin}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Resumen Estadístico
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>📋 Resumen Estadístico</h2></div>", unsafe_allow_html=True)
    st.dataframe(df_filtrado.groupby('nombre').agg({
        'cantidad': ['count', 'mean', 'sum', 'max', 'min'],
        'eficiencia': ['mean', 'max', 'min'],
        'productividad': ['mean', 'max', 'min'],
        'horas_trabajo': ['sum', 'mean']
    }).round(2), use_container_width=True)
    
    # Tendencias Históricas
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>📊 Tendencias Históricas</h2></div>", unsafe_allow_html=True)
    
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
        df_eficiencia_dia = df_filtrado.groupby('dia')['eficiencia'].mean().reset_index()
        if not df_eficiencia_dia.empty and len(df_eficiencia_dia) > 5:
            try:
                dias_prediccion = 7
                x = np.arange(len(df_eficiencia_dia))
                y = df_eficiencia_dia['eficiencia'].values
                
                model = np.polyfit(x, y, 1)
                poly = np.poly1d(model)
                
                x_pred = np.arange(len(df_eficiencia_dia), len(df_eficiencia_dia) + dias_prediccion)
                y_pred = poly(x_pred)
                
                ultima_fecha = df_eficiencia_dia['dia'].max()
                fechas_futuras = [ultima_fecha + timedelta(days=i+1) for i in range(dias_prediccion)]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_eficiencia_dia['dia'], 
                    y=df_eficiencia_dia['eficiencia'],
                    mode='lines+markers',
                    name='Datos Históricos'
                ))
                fig.add_trace(go.Scatter(
                    x=fechas_futuras, 
                    y=y_pred,
                    mode='lines+markers',
                    name='Predicción',
                    line=dict(dash='dash', color='orange')
                ))
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
                
                st.markdown("<h4>Valores de Predicción:</h4>", unsafe_allow_html=True)
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, y_pred)):
                    st.write(f"{fecha.strftime('%Y-%m-%d')}: {pred:.1f}%")
            except Exception as e:
                st.error(f"Error al generar predicciones: {str(e)}")
        else:
            st.info("Se necesitan al menos 5 días de datos para realizar predicciones.")

def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs"""
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📥 Ingreso de Datos de KPIs</h1><div class='header-subtitle'>Registro diario de producción</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay trabajadores registrados. Por favor, registre trabajadores primero.</div>", unsafe_allow_html=True)
        return
    
    if 'Luis Perugachi' in df_trabajadores['nombre'].values:
        df_trabajadores.loc[df_trabajadores['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
    
    trabajadores_por_equipo = {}
    for _, row in df_trabajadores.iterrows():
        equipo = row['equipo']
        if equipo not in trabajadores_por_equipo:
            trabajadores_por_equipo[equipo] = []
        trabajadores_por_equipo[equipo].append(row['nombre'])
    
    if 'Distribución' not in trabajadores_por_equipo:
        trabajadores_por_equipo['Distribución'] = []
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_seleccionada = st.date_input(
            "Selecciona la fecha:",
            value=datetime.now(),
            max_value=datetime.now()
        )
    st.markdown("</div>", unsafe_allow_html=True)
    
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    datos_existentes = obtener_datos_fecha(fecha_str)
    
    if 'datos_calculados' not in st.session_state:
        st.session_state.datos_calculados = None
    if 'fecha_guardar' not in st.session_state:
        st.session_state.fecha_guardar = None
    
    if not datos_existentes.empty:
        st.markdown(f"<div class='alert-banner alert-info'>ℹ️ Ya existen datos para la fecha {fecha_seleccionada}. Puede editarlos a continuación.</div>", unsafe_allow_html=True)
    
    periodo = st.radio("Selecciona el período:", ["Día", "Semana"], horizontal=True)
    
    with st.form("form_datos"):
        st.markdown("<div class='filter-panel'><h3 class='filter-title'>🎯 Meta Mensual de Transferencias</h3></div>", unsafe_allow_html=True)
        
        meta_mensual_existente = 70000
        if not datos_existentes.empty:
            meta_mensual_existente = datos_existentes['meta_mensual'].iloc[0] if 'meta_mensual' in datos_existentes.columns else 70000
        
        meta_mensual_transferencias = st.number_input("Meta mensual para el equipo de transferencias:", min_value=0, value=int(meta_mensual_existente), key="meta_mensual_transferencias")
        
        if 'Distribución' not in trabajadores_por_equipo:
            trabajadores_por_equipo['Distribución'] = []
        
        orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
        equipos_ordenados = [eq for eq in orden_equipos if eq in trabajadores_por_equipo]
        equipos_restantes = [eq for eq in trabajadores_por_equipo.keys() if eq not in orden_equipos]
        equipos_finales = equipos_ordenados + equipos_restantes
        
        for equipo in equipos_finales:
            miembros = trabajadores_por_equipo[equipo]
            
            st.markdown(f"<div class='team-card'><div class='team-header'><span class='team-name'>{equipo}</span></div>", unsafe_allow_html=True)
            
            for trabajador in miembros:
                datos_trabajador = None
                if not datos_existentes.empty:
                    datos_trabajador = datos_existentes[datos_existentes['nombre'] == trabajador].iloc[0] if trabajador in datos_existentes['nombre'].values else None
                
                col1, col2 = st.columns(2)
                with col1:
                    if datos_trabajador is not None:
                        cantidad_default = int(datos_trabajador['cantidad']) if pd.notna(datos_trabajador['cantidad']) else 0
                        meta_default = int(datos_trabajador['meta']) if pd.notna(datos_trabajador['meta']) else 0
                        comentario_default = datos_trabajador['comentario'] if pd.notna(datos_trabajador['comentario']) else ""
                    else:
                        if equipo == "Transferencias":
                            cantidad_default = 1800
                            meta_default = 1750
                        elif equipo == "Distribución":
                            cantidad_default = 1000
                            meta_default = 1750
                        elif equipo == "Arreglo":
                            cantidad_default = 130
                            meta_default = 1000
                        elif equipo == "Guías":
                            cantidad_default = 110
                            meta_default = 120
                        elif equipo == "Ventas":
                            cantidad_default = 600
                            meta_default = 700
                        else:
                            cantidad_default = 100
                            meta_default = 100
                        comentario_default = ""
                    
                    if equipo == "Transferencias":
                        cantidad = st.number_input(f"Prendas transferidas por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                    elif equipo == "Distribución":
                        cantidad = st.number_input(f"Prendas distribuidas por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                    elif equipo == "Arreglo":
                        cantidad = st.number_input(f"Prendas arregladas por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                    elif equipo == "Guías":
                        cantidad = st.number_input(f"Guías realizadas por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                    elif equipo == "Ventas":
                        cantidad = st.number_input(f"Pedidos preparados por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                    else:
                        cantidad = st.number_input(f"Cantidad realizada por {trabajador}:", min_value=0, value=cantidad_default, key=f"{trabajador}_cantidad")
                        meta = st.number_input(f"Meta diaria para {trabajador}:", min_value=0, value=meta_default, key=f"{trabajador}_meta")
                with col2:
                    if datos_trabajador is not None:
                        horas_default = float(datos_trabajador['horas_trabajo']) if pd.notna(datos_trabajador['horas_trabajo']) else 8.0
                    else:
                        horas_default = 8.0
                    
                    horas = st.number_input(f"Horas trabajadas por {trabajador}:", min_value=0.0, value=horas_default, key=f"{trabajador}_horas", step=0.5)
                    comentario = st.text_area(f"Comentario para {trabajador}:", value=comentario_default, key=f"{trabajador}_comentario")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Calcular KPIs", use_container_width=True)
        if submitted:
            datos_guardar = {}
            for equipo, miembros in trabajadores_por_equipo.items():
                for trabajador in miembros:
                    cantidad = st.session_state.get(f"{trabajador}_cantidad", 0)
                    meta = st.session_state.get(f"{trabajador}_meta", 0)
                    horas = st.session_state.get(f"{trabajador}_horas", 0)
                    comentario = st.session_state.get(f"{trabajador}_comentario", "")
                    
                    if not all([validar_numero_positivo(cantidad), validar_numero_positivo(meta), validar_numero_positivo(horas)]):
                        st.markdown(f"<div class='alert-banner alert-danger'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
                        continue
                    
                    if equipo == "Transferencias":
                        eficiencia = kpi_transferencias(cantidad, meta)
                        actividad = "Transferencias"
                        meta_mensual = meta_mensual_transferencias
                    elif equipo == "Distribución":
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
            
            st.session_state.datos_calculados = datos_guardar
            st.session_state.fecha_guardar = fecha_str
            
            st.markdown("<div class='dashboard-header'><h2 class='header-title'>📋 Resumen de KPIs Calculados</h2></div>", unsafe_allow_html=True)
            for equipo, miembros in trabajadores_por_equipo.items():
                st.markdown(f"**{equipo}:**")
                for trabajador in miembros:
                    if trabajador in datos_guardar:
                        datos = datos_guardar[trabajador]
                        st.markdown(f"- {trabajador}: {datos['cantidad']} unidades ({datos['eficiencia']:.1f}%)")
    
    if st.session_state.datos_calculados is not None and st.session_state.fecha_guardar is not None:
        if st.button("✅ Confirmar y Guardar Datos", key="confirmar_guardar", use_container_width=True):
            if guardar_datos_db(st.session_state.fecha_guardar, st.session_state.datos_calculados):
                st.markdown("<div class='alert-banner alert-success'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                st.session_state.datos_calculados = None
                st.session_state.fecha_guardar = None
                time.sleep(2)
                st.rerun()
            else:
                st.markdown("<div class='alert-banner alert-danger'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)

def mostrar_gestion_trabajadores_kpis():
    """Muestra la interfaz de gestión de trabajadores"""
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>👥 Gestión de Trabajadores</h1><div class='header-subtitle'>Administración del personal</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    try:
        response = supabase.from_('trabajadores').select('*').order('equipo,nombre', desc=False).execute()
        
        if response and hasattr(response, 'data') and response.data:
            trabajadores = response.data
        else:
            trabajadores = []
        
        if any(trab['nombre'] == 'Luis Perugachi' for trab in trabajadores):
            for trab in trabajadores:
                if trab['nombre'] == 'Luis Perugachi':
                    trab['equipo'] = 'Distribución'
        
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>Trabajadores Actuales</h2></div>", unsafe_allow_html=True)
        if trabajadores:
            df_trabajadores = pd.DataFrame(trabajadores)
            st.dataframe(df_trabajadores[['nombre', 'equipo', 'activo']], use_container_width=True)
        else:
            st.info("No hay trabajadores registrados.")
        
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>Agregar Nuevo Trabajador</h2></div>", unsafe_allow_html=True)
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
                        response = supabase.from_('trabajadores').select('*').eq('nombre', nuevo_nombre).execute()
                        
                        if response and hasattr(response, 'data') and response.data:
                            st.markdown("<div class='alert-banner alert-danger'>❌ El trabajador ya existe.</div>", unsafe_allow_html=True)
                            st.session_state.show_preview = False
                        else:
                            supabase.from_('trabajadores').insert({
                                'nombre': nuevo_nombre, 
                                'equipo': nuevo_equipo,
                                'activo': True
                            }).execute()
                            st.markdown("<div class='alert-banner alert-success'>✅ Trabajador agregado correctamente.</div>", unsafe_allow_html=True)
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        logger.error(f"Error al agregar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='alert-banner alert-danger'>❌ Error al agregar trabajador.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='alert-banner alert-danger'>❌ Debe ingresar un nombre.</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>Eliminar Trabajador</h2></div>", unsafe_allow_html=True)
        if trabajadores:
            trabajadores_activos = [t['nombre'] for t in trabajadores if t.get('activo', True)]
            if trabajadores_activos:
                trabajador_eliminar = st.selectbox("Selecciona un trabajador para eliminar:", options=trabajadores_activos)
                if st.button("Eliminar Trabajador", use_container_width=True):
                    try:
                        supabase.from_('trabajadores').update({'activo': False}).eq('nombre', trabajador_eliminar).execute()
                        st.markdown("<div class='alert-banner alert-success'>✅ Trabajador eliminado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Error al eliminar trabajador: {e}", exc_info=True)
                        st.markdown("<div class='alert-banner alert-danger'>❌ Error al eliminar trabajador.</div>", unsafe_allow_html=True)
            else:
                st.info("No hay trabajadores activos para eliminar.")
        else:
            st.info("No hay trabajadores registrados.")
    except Exception as e:
        logger.error(f"Error en gestión de trabajadores: {e}", exc_info=True)
        st.markdown("<div class='alert-banner alert-danger'>❌ Error del sistema al gestionar trabajadores.</div>", unsafe_allow_html=True)

# ================================
# FUNCIONES PARA GESTIÓN DE TIENDAS
# ================================
def obtener_tienda_por_id(tienda_id: int) -> Optional[Dict]:
    """Obtiene una tienda específica por su ID desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return None
    
    try:
        response = supabase.from_('guide_stores').select('*').eq('id', tienda_id).execute()
        if response and hasattr(response, 'data') and response.data:
            return response.data[0]
        else:
            logger.warning(f"No se encontró la tienda con ID {tienda_id}")
            return None
    except Exception as e:
        logger.error(f"Error al obtener tienda por ID: {e}", exc_info=True)
        return None

def agregar_tienda(nombre: str, direccion: str, telefono: str) -> bool:
    """Agrega una nueva tienda a la base de datos"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        data = {
            'name': nombre,
            'address': direccion,
            'phone': telefono
        }
        response = supabase.from_('guide_stores').insert(data).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudo agregar la tienda: {response.error}")
            return False
        else:
            logger.info(f"Tienda '{nombre}' agregada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al agregar tienda: {e}", exc_info=True)
        return False

def actualizar_tienda(tienda_id: int, nombre: str, direccion: str, telefono: str) -> bool:
    """Actualiza una tienda existente en la base de datos"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        data = {
            'name': nombre,
            'address': direccion,
            'phone': telefono
        }
        response = supabase.from_('guide_stores').update(data).eq('id', tienda_id).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudo actualizar la tienda: {response.error}")
            return False
        else:
            logger.info(f"Tienda ID {tienda_id} actualizada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al actualizar tienda: {e}", exc_info=True)
        return False

def eliminar_tienda(tienda_id: int) -> bool:
    """Elimina una tienda de la base de datos"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        response = supabase.from_('guide_stores').delete().eq('id', tienda_id).execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"No se pudo eliminar la tienda: {response.error}")
            return False
        else:
            logger.info(f"Tienda ID {tienda_id} eliminada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al eliminar tienda: {e}", exc_info=True)
        return False

def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío y gestionar tiendas"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📦 Generación de Guías de Envío</h1><div class='header-subtitle'>Sistema de etiquetado logístico</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    tab1, tab2 = st.tabs(["📋 Generar Guía", "🏬 Gestionar Tiendas"])
    
    with tab1:
        # URLs de logos desde GitHub
        url_fashion_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
        url_tempo_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"

        col_controles, col_imagen = st.columns([2, 1])

        with col_controles:
            st.markdown("### 1. Seleccione la Empresa")
            brand = st.radio(
                "Seleccione Empresa:", 
                ["Fashion", "Tempo"], 
                horizontal=True, 
                key="brand_select",
                label_visibility="collapsed"
            )

        with col_imagen:
            if brand == "Tempo":
                st.image(url_tempo_logo, caption="Logo Tempo", use_container_width=True)
            else:
                st.image(url_fashion_logo, caption="Logo Fashion Club", use_container_width=True)
        
        tiendas = obtener_tiendas()
        remitentes = obtener_remitentes()
        
        if tiendas.empty or remitentes.empty:
            st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
            return
        
        if 'show_preview' not in st.session_state:
            st.session_state.show_preview = False
        if 'pdf_data' not in st.session_state:
            st.session_state.pdf_data = None
        
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 class='filter-title'>2. Complete los Datos de la Guía</h3>", unsafe_allow_html=True)
        
        with st.form("form_generar_guia", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                store_name = st.selectbox("Seleccione Tienda", tiendas['name'].tolist(), key="store_select")
            
            with col2:
                sender_name = st.selectbox("Seleccione Remitente:", options=remitentes['name'].tolist(), key="sender_select")
            
            url = st.text_input("Ingrese URL del Pedido:", key="url_input", placeholder="https://...")
            
            submitted = st.form_submit_button("Generar Guía", use_container_width=True)
            
            if submitted:
                if not all([store_name, brand, url, sender_name]):
                    st.markdown("<div class='alert-banner alert-danger'>❌ Por favor, complete todos los campos.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                elif not url.startswith(('http://', 'https://')):
                    st.markdown("<div class='alert-banner alert-danger'>❌ La URL debe comenzar con http:// o https://</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                else:
                    if guardar_guia(store_name, brand, url, sender_name):
                        st.session_state.show_preview = True
                        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                        st.session_state.remitente_address = remitente_info['address']
                        st.session_state.remitente_phone = remitente_info['phone']
                        st.session_state.tracking_number = generar_numero_seguimiento(1)
                        
                        st.session_state.pdf_data = generar_pdf_guia(
                            store_name, brand, url, sender_name, st.session_state.tracking_number
                        )
                        
                        st.markdown("<div class='alert-banner alert-success'>✅ Guía generada correctamente. Puede ver la previsualización y exportarla.</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='alert-banner alert-danger'>❌ Error al guardar la guía.</div>", unsafe_allow_html=True)
                        st.session_state.show_preview = False
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.show_preview:
            st.markdown("<div class='dashboard-header'><h2 class='header-title'>Previsualización de la Guía</h2></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-icon">🏬</div>
                        <div>
                            <div class="kpi-title">Tienda</div>
                            <div class="kpi-value">{st.session_state.get('store_select', '')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-icon">🏷️</div>
                        <div>
                            <div class="kpi-title">Marca</div>
                            <div class="kpi-value">{st.session_state.get('brand_select', '')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-header">
                        <div class="kpi-icon">📦</div>
                        <div>
                            <div class="kpi-title">Remitente</div>
                            <div class="kpi-value">{st.session_state.get('sender_select', '')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="alert-banner alert-info">
                <strong>🔗 URL del Pedido:</strong> <a href='{st.session_state.get('url_input', '')}' target='_blank'>{st.session_state.get('url_input', '')}</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h3>Código QR:</h3>", unsafe_allow_html=True)
            qr_img = generar_qr_imagen(st.session_state.get('url_input', ''))
            qr_bytes = pil_image_to_bytes(qr_img)
            st.image(qr_bytes, width=200)
            
            st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.session_state.pdf_data is not None:
                    st.download_button(
                        label="📄 Descargar PDF",
                        data=st.session_state.pdf_data,
                        file_name=f"guia_{st.session_state.get('store_select', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="download_pdf_button"
                    )
            with col2:
                if st.button("🖨️ Marcar como Impresa", use_container_width=True, key="mark_printed_button"):
                    st.markdown("<div class='alert-banner alert-success'>✅ Guía marcada como impresa.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                    if 'pdf_data' in st.session_state:
                        del st.session_state.pdf_data
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        if not verificar_password("admin"):
            solicitar_autenticacion("admin")
        else:
            st.markdown("<div class='dashboard-header'><h2 class='header-title'>Gestión de Tiendas</h2></div>", unsafe_allow_html=True)
            
            tiendas = obtener_tiendas()
            
            if tiendas.empty:
                st.info("No hay tiendas registradas.")
            else:
                st.markdown("<h3>Tiendas Existentes</h3>", unsafe_allow_html=True)
                
                edited_tiendas = st.data_editor(
                    tiendas[['id', 'name', 'address', 'phone']],
                    column_config={
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                        "name": "Nombre",
                        "address": "Dirección",
                        "phone": "Teléfono"
                    },
                    use_container_width=True,
                    num_rows="dynamic",
                    key="tiendas_editor"
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Guardar Cambios", use_container_width=True):
                        cambios_realizados = 0
                        for _, row in edited_tiendas.iterrows():
                            tienda_original = tiendas[tiendas['id'] == row['id']].iloc[0]
                            
                            if (tienda_original['name'] != row['name'] or 
                                tienda_original['address'] != row['address'] or 
                                tienda_original['phone'] != row['phone']):
                                
                                if actualizar_tienda(row['id'], row['name'], row['address'], row['phone']):
                                    cambios_realizados += 1
                        
                        if cambios_realizados > 0:
                            st.success(f"✅ {cambios_realizados} tienda(s) actualizada(s) correctamente.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.info("ℹ️ No se detectaron cambios para guardar.")
                
                with col2:
                    tiendas_para_eliminar = st.selectbox(
                        "Seleccionar tienda para eliminar:",
                        options=tiendas['id'].tolist(),
                        format_func=lambda x: f"{tiendas[tiendas['id'] == x]['name'].iloc[0]} (ID: {x})",
                        key="eliminar_tienda_select"
                    )
                
                with col3:
                    if st.button("🗑️ Eliminar Tienda Seleccionada", use_container_width=True):
                        if eliminar_tienda(tiendas_para_eliminar):
                            st.success("✅ Tienda eliminada correctamente.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Error al eliminar la tienda.")
            
            st.markdown("<h3>Agregar Nueva Tienda</h3>", unsafe_allow_html=True)
            
            with st.form("form_nueva_tienda"):
                col1, col2 = st.columns(2)
                with col1:
                    nuevo_nombre = st.text_input("Nombre de la tienda:", key="nueva_tienda_nombre")
                    nueva_direccion = st.text_area("Dirección:", key="nueva_tienda_direccion")
                with col2:
                    nuevo_telefono = st.text_input("Teléfono:", key="nueva_tienda_telefono")
                    st.write("")  
                    st.write("")  
                
                submitted = st.form_submit_button("➕ Agregar Tienda", use_container_width=True)
                
                if submitted:
                    if not all([nuevo_nombre, nueva_direccion, nuevo_telefono]):
                        st.error("❌ Por favor, complete todos los campos.")
                    else:
                        if agregar_tienda(nuevo_nombre, nueva_direccion, nuevo_telefono):
                            st.success("✅ Tienda agregada correctamente.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar la tienda.")

def mostrar_reconciliacion():
    """Muestra la interfaz de reconciliación logística"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📦 Herramienta de Reconciliación Logística y BI</h1><div class='header-subtitle'>Análisis de facturas vs manifiestos</div></div>", unsafe_allow_html=True)

    if 'reconciler' not in st.session_state:
        st.session_state.reconciler = StreamlitLogisticsReconciliation()
        st.session_state.processed = False
        st.session_state.show_details = False

    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>Carga de Archivos</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        factura_file = st.file_uploader("Cargar Archivo de Facturas (Excel)", type=['xlsx', 'xls'])
    with col2:
        manifiesto_file = st.file_uploader("Cargar Archivo de Manifiesto (Excel)", type=['xlsx', 'xls'])
    
    if st.button("🚀 Procesar Archivos", use_container_width=True):
        if factura_file and manifiesto_file:
            with st.spinner("Procesando y reconciliando archivos..."):
                st.session_state.processed = st.session_state.reconciler.process_files(factura_file, manifiesto_file)
        else:
            st.warning("Por favor, carga ambos archivos.")
    
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.processed:
        reconciler = st.session_state.reconciler
        kpis = reconciler.kpis

        st.markdown("<div class='dashboard-header'><h2 class='header-title'>📊 Resumen de Reconciliación</h2></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Guías Concordantes", f"{kpis['total_facturadas']:,}", help="Guías encontradas en Facturas y Manifiesto.")
        col2.metric("Guías Anuladas", f"{kpis['total_anuladas']:,}", help="Guías en Manifiesto pero NO en Facturas.")
        col3.metric("Guías Sobrantes", f"{kpis['total_sobrantes_factura']:,}", help="Guías en Facturas pero NO en Manifiesto.")

        col4, col5, col6 = st.columns(3)
        col4.metric("Valor Total (Bruto Facturas)", f"${kpis['total_value']:,.2f}")
        col5.metric("Valor Concordante", f"${kpis['value_facturadas']:,.2f}")
        col6.metric("Valor Anuladas", f"${kpis['value_anuladas']:,.2f}")
        
        st.markdown("---")
        
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>📈 Análisis de Guías Concordantes</h2></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top 5 Ciudades")
            if not kpis['top_cities'].empty: st.bar_chart(kpis['top_cities'].head(5))
            else: st.info("No hay datos disponibles.")

            st.subheader("Gasto por Ciudad")
            if not kpis['spending_by_city'].empty: st.bar_chart(kpis['spending_by_city'].head(5))
            else: st.info("No hay datos disponibles.")

        with c2:
            st.subheader("Top 5 Tiendas")
            if not kpis['top_stores'].empty: st.bar_chart(kpis['top_stores'].head(5))
            else: st.info("No hay datos disponibles.")
            
            st.subheader("Gasto por Tienda")
            if not kpis['spending_by_store'].empty: st.bar_chart(kpis['spending_by_store'].head(5))
            else: st.info("No hay datos disponibles.")
        
        st.markdown("---")

        st.subheader("Volumen de Envíos por Mes")
        if not kpis['shipment_volume'].empty:
            shipment_volume_str_index = kpis['shipment_volume'].copy()
            shipment_volume_str_index.index = shipment_volume_str_index.index.astype(str)
            st.line_chart(shipment_volume_str_index)
        else:
            st.info("No hay datos para el volumen de envíos.")

        st.subheader("Análisis de Guías Anuladas por Destinatario")
        if not kpis['anuladas_by_destinatario'].empty:
            st.dataframe(kpis['anuladas_by_destinatario'])
        else:
            st.info("No se encontraron guías anuladas.")

        if st.button("👁️ Mostrar/Ocultar Detalles de Guías"):
            st.session_state.show_details = not st.session_state.show_details

        if st.session_state.show_details:
            st.header("Detalle de Guías por Categoría")
            with st.expander("Guías Concordantes (Facturadas)"):
                st.text_area("guides_facturadas_list", ", ".join(reconciler.guides_facturadas), height=150)

            with st.expander("Guías Anuladas (En Manifiesto pero no en Facturas)"):
                st.text_area("guides_anuladas_list", ", ".join(reconciler.guides_anuladas), height=150)
            
            with st.expander("Guías Sobrantes (En Facturas pero no en Manifiesto)"):
                st.text_area("guides_sobrantes_list", ", ".join(reconciler.guides_sobrantes_factura), height=150)

        st.markdown("---")
        st.markdown("<div class='dashboard-header'><h2 class='header-title'>Descargas</h2></div>", unsafe_allow_html=True)
        pdf_buffer = reconciler.generate_report()
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_buffer,
            file_name=f"reporte_logistica_{datetime.now().date()}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

def mostrar_historial_guias():
    """Muestra el historial de guías generadas"""
    if not verificar_password("user"):
        if st.session_state.user_type is None:
            solicitar_autenticacion("user")
        return
    
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>🔍 Historial de Guías de Envío</h1><div class='header-subtitle'>Registro y seguimiento de envíos</div></div>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='alert-banner alert-danger'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.markdown("<div class='alert-banner alert-warning'>⚠️ No hay guías generadas.</div>", unsafe_allow_html=True)
        return
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>Filtros</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=df_guias['created_at'].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=df_guias['created_at'].max().date())
    with col3:
        estado = st.selectbox("Estado:", ["Todos", "Pending", "Printed"])
    
    df_filtrado = df_guias[
        (df_guias['created_at'].dt.date >= fecha_inicio) & 
        (df_guias['created_at'].dt.date <= fecha_fin)
    ]
    
    if estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['status'] == estado]
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_creados = len(df_guias)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">📦</div>
                <div>
                    <div class="kpi-title">Total de Guías</div>
                    <div class="kpi-value">{total_creados}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pendientes = len(df_guias[df_guias['status'] == 'Pending'])
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">⏳</div>
                <div>
                    <div class="kpi-title">Pendientes</div>
                    <div class="kpi-value">{pendientes}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        impresos = len(df_guias[df_guias['status'] == 'Printed'])
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header">
                <div class="kpi-icon">✅</div>
                <div>
                    <div class="kpi-title">Impresas</div>
                    <div class="kpi-value">{impresos}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='dashboard-header'><h2 class='header-title'>Guías Generadas</h2></div>", unsafe_allow_html=True)
    
    df_display = df_filtrado.copy()
    df_display['created_at'] = df_display['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    
    columns_to_display = ['id', 'store_name', 'brand', 'sender_name', 'status', 'created_at']
    df_display = df_display[columns_to_display]
    
    df_display = df_display.rename(columns={
        'id': 'ID',
        'store_name': 'Tienda',
        'brand': 'Marca',
        'sender_name': 'Remitente',
        'status': 'Estado',
        'created_at': 'Fecha'
    })
    
    st.dataframe(df_display, use_container_width=True)
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>Exportación y Gestión</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Exportar a Excel", use_container_width=True):
            try:
                export_df = df_filtrado.copy()
                export_df['created_at'] = export_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
                
                export_df = export_df.rename(columns={
                    'store_name': 'Tienda',
                    'brand': 'Marca',
                    'sender_name': 'Remitente',
                    'status': 'Estado',
                    'created_at': 'Fecha'
                })
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, sheet_name='Historial_Guías', index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=excel_data,
                    file_name=f"historial_guias_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar historial de guías a Excel: {e}", exc_info=True)
                st.markdown("<div class='alert-banner alert-danger'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"historial_guias_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if verificar_password("admin"):
            guias_a_eliminar = st.multiselect("Seleccionar guías para eliminar:", 
                                             options=df_filtrado['id'].tolist(),
                                             format_func=lambda x: f"Guía {x}")
            
            if st.button("🗑️ Eliminar Guías Seleccionadas", use_container_width=True):
                if guias_a_eliminar:
                    eliminaciones_exitosas = 0
                    for guia_id in guias_a_eliminar:
                        if eliminar_guia(guia_id):
                            eliminaciones_exitosas += 1
                    
                    if eliminaciones_exitosas > 0:
                        st.markdown(f"<div class='alert-banner alert-success'>✅ {eliminaciones_exitosas} guía(s) eliminada(s) correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("<div class='alert-banner alert-danger'>❌ Error al eliminar las guías.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='alert-banner alert-warning'>⚠️ No se seleccionaron guías para eliminar.</div>", unsafe_allow_html=True)
        else:
            st.info("🔒 Autenticación requerida para eliminar guías")
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_generacion_etiquetas():
    """Muestra la interfaz para generar etiquetas de productos"""
    if not verificar_password("user"):
        solicitar_autenticacion("user")
        return

    st.markdown("<div class='dashboard-header'><h1 class='header-title'>🏷️ Generación de Etiquetas de Producto</h1><div class='header-subtitle'>Etiquetado para almacén</div></div>", unsafe_allow_html=True)

    with st.form("form_etiqueta"):
        st.markdown("<div class='filter-panel'><h3 class='filter-title'>Datos de la Etiqueta</h3></div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            referencia = st.text_input("Referencia:", key="etiqueta_referencia")
            tipo = st.selectbox("Tipo:", options=["hombre", "mujer", "accesorios"], key="etiqueta_tipo")
        with col2:
            cantidad = st.number_input("Cantidad:", min_value=0, key="etiqueta_cantidad")
            caja = st.number_input("Número de Caja:", min_value=0, key="etiqueta_caja")
        
        imagen_file = st.file_uploader("Imagen del producto (opcional):", type=['png', 'jpg', 'jpeg', 'bmp', 'gif'], key="etiqueta_imagen")
        submitted = st.form_submit_button("Generar Etiqueta PDF", use_container_width=True)

    if submitted:
        referencia = st.session_state.etiqueta_referencia
        tipo = st.session_state.etiqueta_tipo
        cantidad = st.session_state.etiqueta_cantidad
        caja = st.session_state.etiqueta_caja
        uploaded_file = st.session_state.etiqueta_imagen

        if not all([referencia, tipo, cantidad is not None, caja is not None]):
            st.error("❌ Por favor, complete todos los campos obligatorios.")
        else:
            if tipo == 'hombre':
                piso = 1
            elif tipo == 'mujer':
                piso = 3
            else:
                piso = 2

            imagen_path = None
            if uploaded_file is not None:
                try:
                    os.makedirs("temp", exist_ok=True)
                    temp_path = f"temp/{int(datetime.now().timestamp())}_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    imagen_path = temp_path
                except Exception as e:
                    logger.error(f"Error al guardar imagen temporal: {e}")
                    st.error("⚠️ No se pudo procesar la imagen.")

            datos_etiqueta = {
                'referencia': referencia,
                'tipo': tipo,
                'cantidad': int(cantidad),
                'caja': int(caja),
                'piso': piso,
                'imagen_path': imagen_path
            }

            pdf_data = generar_pdf_etiqueta(datos_etiqueta)
            if pdf_data:
                st.success("✅ Etiqueta generada correctamente.")
                st.download_button(
                    label="⬇️ Descargar Etiqueta PDF",
                    data=pdf_data,
                    file_name=f"etiqueta_{referencia}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                if imagen_path and os.path.exists(imagen_path):
                    os.remove(imagen_path)
            else:
                st.error("❌ Error al generar la etiqueta.")
                if imagen_path and os.path.exists(imagen_path):
                    os.remove(imagen_path)

def mostrar_ayuda():
    """Muestra la página de ayuda y contacto"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>❓ Ayuda y Contacto</h1><div class='header-subtitle'>Soporte y documentación</div></div>", unsafe_allow_html=True)
    
    st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
    st.markdown("<h3 class='filter-title'>📝 Guía de uso</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-banner alert-info">
        <h4>**Sistema de KPIs:**</h4>
        <ul>
            <li><strong>Dashboard de KPIs:</strong> Visualiza el rendimiento diario de los equipos.</li>
            <li><strong>Análisis Histórico:</strong> Analiza tendencias y exporta reportes.</li>
            <li><strong>Ingreso de Datos:</strong> Ingresa los datos diarios de producción.</li>
            <li><strong>Gestión de Trabajadores:</strong> Administra el personal de la empresa.</li>
            <li><strong>Gestión de Distribuciones:</strong> Controla las distribuciones semanales y el estado de abastecimiento.</li>
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

def generar_pdf_etiqueta(datos: dict) -> bytes:
    """Genera un PDF con la etiqueta de producto en el formato de AEROPOSTALE"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(True, 15)
        
        # Fondo azul para el encabezado
        pdf.set_fill_color(10, 16, 153)
        pdf.rect(0, 0, 210, 35, style='F')
        
        # Texto blanco para el encabezado
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_xy(0, 5)
        pdf.cell(210, 10, "AEROPOSTALE", 0, 1, "C")
        
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(0, 18)
        pdf.cell(210, 10, "PRICE CLUB GUAYAQUIL", 0, 1, "C")
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(40)
        
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # REFERENCIA
        pdf.set_font("Helvetica", "", 20)
        pdf.cell(50, 8, "REFERENCIA", 0, 0)
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 8, datos['referencia'], 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(2)
        
        # TIPO solo
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(10, 16, 153)
        pdf.cell(80, 18, datos['tipo'].upper(), 0, 1)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln(2)
        
        # Guardar posición Y para alineación de imagen
        y_start = pdf.get_y()
        
        # CANTIDAD
        pdf.set_font("Helvetica", "", 20)
        pdf.cell(50, 8, "CANTIDAD", 0, 0)
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 8, str(datos['cantidad']), 0, 1)
        
        pdf.ln(2)
        
        # CAJA
        pdf.set_font("Helvetica", "", 20)
        pdf.cell(50, 8, "CAJA", 0, 0)
        pdf.set_font("Helvetica", "B", 24)
        pdf.cell(0, 8, str(datos['caja']), 0, 1)
        
        # IMAGEN (si existe)
        if datos['imagen_path'] and os.path.exists(datos['imagen_path']):
            try:
                pdf.image(datos['imagen_path'], x=120, y=40, w=85)
            except Exception as e:
                logger.error(f"Error al insertar imagen en PDF: {e}")
        
        image_height = 40 if datos['imagen_path'] else 0
        pdf.set_y(max(pdf.get_y(), y_start + image_height + 5))
        
        # PISO
        pdf.set_font("Helvetica", "B", 78)
        pdf.cell(190, 15, f"PISO {datos['piso']}", 0, 1, "L")
        
        return pdf.output(dest="S").encode("latin1")
        
    except Exception as e:
        logger.error(f"Error al generar PDF de etiqueta: {e}", exc_info=True)
        return None

# ================================
# FUNCIÓN PRINCIPAL
# ================================
def main():
    """Función principal de la aplicación"""
    
    # Sidebar con logo y menú
    with st.sidebar:
        st.markdown("""
        <div class='sidebar-logo'>
            <div class='logo-text'>AEROPOSTALE</div>
            <div class='logo-subtext'>Sistema de Gestión Logística</div>
        </div>
        """, unsafe_allow_html=True)
        
        menu_options = [
            ("Dashboard KPIs", "📊", mostrar_dashboard_kpis, "public"),
            ("Análisis Histórico", "📈", mostrar_analisis_historico_kpis, "public"),
            ("Ingreso de Datos", "📥", mostrar_ingreso_datos_kpis, "admin"),
            ("Gestión de Trabajadores", "👥", mostrar_gestion_trabajadores_kpis, "admin"),
            ("Gestión de Distribuciones", "📦", mostrar_gestion_distribuciones, "admin"),
            ("Reconciliación", "🔁", mostrar_reconciliacion, "admin"),
            ("Generar Guías", "📋", mostrar_generacion_guias, "user"),
            ("Historial de Guías", "🔍", mostrar_historial_guias, "user"),
            ("Generar Etiquetas", "🏷️", mostrar_generacion_etiquetas, "user"),
            ("Ayuda y Contacto", "❓", mostrar_ayuda, "public")
        ]
        
        # Mostrar opciones del menú según permisos
        for i, (label, icon, _, permiso) in enumerate(menu_options):
            mostrar_opcion = False
            
            if permiso == "public":
                mostrar_opcion = True
            elif permiso == "user" and st.session_state.user_type in ["user", "admin"]:
                mostrar_opcion = True
            elif permiso == "admin" and st.session_state.user_type == "admin":
                mostrar_opcion = True
            
            if mostrar_opcion:
                selected = st.button(
                    f"{icon} {label}",
                    key=f"menu_{i}",
                    use_container_width=True
                )
                if selected:
                    st.session_state.selected_menu = i
        
        # Botones de autenticación
        st.markdown("---")
        if st.session_state.user_type is None:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👤 Acceso Usuario", use_container_width=True):
                    st.session_state.show_login = True
                    st.session_state.login_type = "user"
            with col2:
                if st.button("🔧 Acceso Admin", use_container_width=True):
                    st.session_state.show_login = True
                    st.session_state.login_type = "admin"
        else:
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.user_type = None
                st.session_state.password_correct = False
                st.session_state.selected_menu = 0
                st.session_state.show_login = False
                st.rerun()
            
            tipo_usuario = "Administrador" if st.session_state.user_type == "admin" else "Usuario"
            st.markdown(f"""
            <div class="alert-banner alert-info" style="margin-top: 20px;">
                <strong>👤 Usuario:</strong> {tipo_usuario}
            </div>
            """, unsafe_allow_html=True)
    
    # Mostrar formulario de autenticación si es necesario
    if st.session_state.get('show_login', False):
        solicitar_autenticacion(st.session_state.get('login_type', 'user'))
        return
    
    # Verificar que selected_menu esté dentro del rango válido
    if st.session_state.selected_menu >= len(menu_options):
        st.session_state.selected_menu = 0
    
    # Obtener y ejecutar la función seleccionada
    label, icon, func, permiso = menu_options[st.session_state.selected_menu]
    
    if permiso == "public":
        func()
    elif permiso == "user" and st.session_state.user_type in ["user", "admin"]:
        func()
    elif permiso == "admin" and st.session_state.user_type == "admin":
        func()
    else:
        if not st.session_state.get('show_login', False):
            st.error("🔒 Acceso restringido. Necesita autenticarse para acceder a esta sección.")
        
        if permiso == "admin" and not st.session_state.get('show_login', False):
            st.session_state.show_login = True
            st.session_state.login_type = "admin"
            st.rerun()
        elif not st.session_state.get('show_login', False):
            st.session_state.show_login = True
            st.session_state.login_type = "user"
            st.rerun()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.<br>
        Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com" class="footer-link">Wilson Pérez</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
