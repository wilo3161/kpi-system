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
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import warnings
warnings.filterwarnings('ignore')
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False
if 'selected_menu' not in st.session_state:
    st.session_state.selected_menu = 0
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'reconciler' not in st.session_state:
    st.session_state.reconciler = Reconciler()
if 'processed' not in st.session_state:
    st.session_state.processed = False   

# ================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ================================

# Configuración de logging para registrar eventos y errores
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de Supabase con las credenciales proporcionadas
SUPABASE_URL = "https://nsgdyqoqzlcyyameccqn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zZ2R5cW9xemxjeXlhbWVjY3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMTA3MzksImV4cCI6MjA3MTU4NjczOX0.jA6sem9IMts6aPeYlMsldbtQaEaKAuQaQ1xf03TdWso"
ADMIN_PASSWORD = "Wilo3161"  # Contraseña única sensible a mayúsculas
USER_PASSWORD = "User1234"   # Nueva contraseña para usuarios normales

# Configuración de directorios para imágenes
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

# Configuración de página de Streamlit
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ================================
# ESTILOS CSS PERSONALIZADOS
# ================================

# CSS profesional mejorado con colores corporativos de Aeropostale
st.markdown("""
<style>
/* Colores corporativos de Aeropostale */
:root {
    --primary-color: #e60012; /* Rojo Aeropostale */
    --secondary-color: #000000;
    --accent-color: #333333;
    --background-dark: #121212;
    --card-background: #1a1a1a;
    --text-color: #ffffff;
    --text-secondary: #b0b0b0;
    --success-color: #4caf50;
    --warning-color: #ff9800;
    --error-color: #f44336;
    --border-radius: 16px;
    --transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* Fondo con textura sutil de puntos */
body {
    background-color: var(--background-dark);
    color: var(--text-color);
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    background-image: radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: 20px 20px;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

.stApp {
    background-color: transparent;
}

/* Estilos del sidebar */
.css-1d391kg {
    background-color: #1a1a1a !important;
}

/* Estilos específicos para el sistema de guías */
.guide-section {
    background: var(--card-background);
    border-radius: var(--border-radius);
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(230, 0, 18, 0.1);
    backdrop-filter: blur(8px);
    transition: var(--transition);
}

.guide-section:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(230, 0, 18, 0.2);
}

.qr-preview {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #2a2a2a;
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
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

/* ================================ */
/* DASHBOARD: KPI CARDS MEJORADAS */
/* ================================ */

.kpi-card {
    background: linear-gradient(145deg, #057dcd, #161616);
    border-radius: var(--border-radius);
    box-shadow: 
        0 8px 20px rgba(0, 0, 0, 0.3),
        0 0 15px rgba(230, 0, 18, 0.1) inset;
    padding: 22px;
    margin: 15px 0;
    border-left: 6px solid var(--primary-color);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(230, 0, 18, 0.15);
}

/* Efecto de brillo al pasar el mouse */
.kpi-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.6s;
    transform: scale(0.8);
}

.kpi-card:hover::before {
    opacity: 1;
    transform: scale(1);
}

.kpi-card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 
        0 16px 40px rgba(0, 0, 0, 0.4),
        0 0 30px rgba(230, 0, 18, 0.25);
    border-color: var(--primary-color);
}

.metric-value {
    font-size: 2.8em;
    font-weight: bold;
    color: var(--primary-color);
    line-height: 1.2;
    margin: 10px 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.metric-label {
    color: var(--text-secondary);
    font-size: 1.1em;
    margin-bottom: 5px;
    font-weight: 500;
}

/* Icono decorativo opcional en la tarjeta */
.kpi-card::after {
    content: "📊";
    position: absolute;
    bottom: 15px;
    right: 15px;
    font-size: 1.2em;
    opacity: 0.3;
    filter: blur(0.5px);
}

/* Worker card mejorada */
.worker-card {
   background: linear-gradient(145deg, #0052cc, #161616);
    border-radius: var(--border-radius);
    box-shadow: 
        0 8px 20px rgba(0, 0, 0, 0.3),
        0 0 15px rgba(230, 0, 18, 0.1) inset;
    padding: 22px;
    margin: 15px 0;
    border-left: 6px solid var(--primary-color);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(230, 0, 18, 0.15);
}

.worker-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.worker-header {
    font-weight: bold;
    color: var(--text-color);
    margin-bottom: 6px;
    font-size: 2.65em;
}

.worker-metric {
    color: var(--text-secondary);
    font-size: 1.3em;
}

.trend-up {
    color: var(--success-color);
}

.trend-down {
    color: var(--error-color);
}

/* Info, warning, success boxes con iluminación */
.info-box, .warning-box, .success-box, .error-box {
    padding: 16px;
    margin: 15px 0;
    border-radius: 12px;
    font-weight: 500;
    animation: animate-fade-in 0.6s ease-out;
    border-left: 5px solid var(--primary-color);
    background: rgba(230, 0, 18, 0.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.success-box {
    border-left-color: var(--success-color);
    background: rgba(76, 175, 80, 0.1);
    color: #c8e6c9;
}

.warning-box {
    border-left-color: var(--warning-color);
    background: rgba(255, 152, 0, 0.1);
    color: #ffe0b2;
}

.error-box {
    border-left-color: var(--error-color);
    background: rgba(244, 67, 54, 0.1);
    color: #ffcdd2;
}

/* Animaciones */
@keyframes animate-fade-in {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
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
    backdrop-filter: blur(10px);
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
    text-shadow: 0 0 10px rgba(230, 0, 18, 0.5);
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 40px;
    color: var(--text-secondary);
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

    .kpi-card {
        padding: 18px;
    }
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
        return num >= 0 and num <= 10000  # Límite razonable
    except (ValueError, TypeError):
        return False

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(pw.encode()).hexdigest()

# ================================
# FUNCIONES DE KPIs
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

# ================================
# FUNCIONES DE ACCESO A DATOS (SUPABASE)
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
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })
    
    try:
        response = supabase.from_('trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
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
        if response and hasattr(response, 'data') and response.data:
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
    """Guarda los datos en la tabla de Supabase con mejor manejo de errores"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        st.error("Error de conexión con la base de datos")
        return False
    
    try:
        # Validaciones adicionales
        if not validar_fecha(fecha):
            logger.error(f"Fecha inválida: {fecha}")
            st.error("Formato de fecha inválido")
            return False
            
        registros = []
        for nombre, info in datos.items():
            # Validar datos antes de guardar
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
            # Usar upsert para insertar o actualizar
            response = supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            
            # Limpiar caché de datos históricos
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
        
        # Verificar si hay datos en la respuesta
        if response and hasattr(response, 'data') and response.data:
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

def obtener_datos_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene los datos de una fecha específica desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        
        # Verificar si hay datos en la respuesta
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
# NUEVAS FUNCIONES PARA DISTRIBUCIONES Y DEPENDENCIAS
# ================================

def obtener_distribuciones_semana(fecha_inicio_semana: str) -> dict:
    """Obtiene las distribuciones de la semana actual desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return {'tempo': 0, 'luis': 0}
    
    try:
        # Calcular fecha fin de semana
        fecha_inicio = datetime.strptime(fecha_inicio_semana, "%Y-%m-%d")
        fecha_fin = fecha_inicio + timedelta(days=6)
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
        
        # Consultar distribuciones semanales
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
        # Validar datos
        if not all([validar_fecha(semana),
                    validar_distribuciones(tempo_distribuciones),
                    validar_distribuciones(luis_distribuciones),
                    validar_distribuciones(meta_semanal)]):
            logger.error("Datos de distribuciones inválidos")
            return False
            
        # Verificar si ya existe registro para esta semana
        response = supabase.from_('distribuciones_semanales').select('*').eq('semana', semana).execute()
        
        if response and hasattr(response, 'data') and response.data:
            # Actualizar registro existente
            update_data = {
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal,
                'updated_at': datetime.now().isoformat()
            }
            response = supabase.from_('distribuciones_semanales').update(update_data).eq('semana', semana).execute()
        else:
            # Crear nuevo registro
            insert_data = {
                'semana': semana,
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal
            }
            response = supabase.from_('distribuciones_semanales').insert(insert_data).execute()
        
        # Verificar si la operación fue exitosa
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
        # Devolver dependencias por defecto
        return pd.DataFrame({
            'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
            'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
        })
    
    try:
        response = supabase.from_('dependencias_transferencias').select('*').execute()
        
        # Verificar si hay datos en la respuesta
        if response and hasattr(response, 'data') and response.data:
            return pd.DataFrame(response.data)
        else:
            logger.info("No se encontraron dependencias de transferencias")
            # Crear dependencias por defecto si no existen
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
    # Obtener distribuciones de la semana actual
    fecha_inicio_semana = datetime.now().date() - timedelta(days=datetime.now().weekday())
    distribuciones_semana = obtener_distribuciones_semana(fecha_inicio_semana.strftime("%Y-%m-%d"))
    
    # Calcular cumplimiento
    meta_semanal = 7500
    distribuciones_totales = distribuciones_semana['tempo'] + distribuciones_semana['luis']
    
    # Determinar responsabilidades
    resultado = {
        'meta_semanal': meta_semanal,
        'distribuciones_totales': distribuciones_totales,
        'cumplimiento_porcentaje': (distribuciones_totales / meta_semanal) * 100 if meta_semanal > 0 else 0,
        'detalles': []
    }
    
    # Verificar abastecimiento de Tempo para Josué
    if distribuciones_semana['tempo'] < 3750:  # Mitad de la meta semanal
        resultado['detalles'].append({
            'transferidor': 'Josué Imbacuán',
            'proveedor': 'Tempo',
            'distribuciones_recibidas': distribuciones_semana['tempo'],
            'distribuciones_requeridas': 3750,
            'estado': 'INSUFICIENTE'
        })
    
    # Verificar abastecimiento de Luis para Andrés
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
# FUNCIONES DE GUIAS (NUEVAS) - CORREGIDAS
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
    return f"AERO{str(record_id).zfill(8)}"  # Formato AERO + 8 dígitos

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
        
        # Verificar si la inserción fue exitosa
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
        # Si es una URL local (file://), verificar con os.path.exists
        if url.startswith("file://"):
            local_path = url[7:]  # Remover "file://"
            return os.path.exists(local_path)
        
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al verificar imagen {url}: {e}")
        return False

def obtener_url_logo(brand: str) -> str:
    """Obtiene la URL pública del logo de la marca desde Supabase Storage"""
    brand_lower = brand.lower()
    
    # URLs predefinidas para marcas específicas (más eficiente)
    branded_logos = {
        "fashion": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Fashion.jpg",
        "tempo": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Tempo.jpg",
        # Agrega más marcas conocidas aquí
    }
    
    # Primero, intentar con URLs predefinidas para marcas conocidas
    if brand_lower in branded_logos:
        logo_url = branded_logos[brand_lower]
        if verificar_imagen_existe(logo_url):
            logger.info(f"Imagen encontrada para marca {brand}: {logo_url}")
            return logo_url
    
    # Si no es una marca predefinida, intentar con el método genérico
    try:
        project_id = "nsgdyqoqzlcyyameccqn"
        bucket_name = 'images'
        
        # Intentar con diferentes extensiones y formatos
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
            # CONSTRUCCIÓN CORRECTA DE LA URL PÚBLICA DE SUPABASE
            logo_url = f"https://{project_id}.supabase.co/storage/v1/object/public/{bucket_name}/{file_name}"
            
            # Verificar si la imagen existe
            if verificar_imagen_existe(logo_url):
                logger.info(f"Imagen encontrada: {logo_url}")
                return logo_url
        
        # Si no se encontró en Supabase, intentar con imágenes locales de respaldo
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
        
        # Manejar URLs locales
        if logo_url.startswith("file://"):
            local_path = logo_url[7:]
            return Image.open(local_path)
        
        # Manejar URLs web
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
    
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Configuración inicial
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(True, 15)
        
        # Fondo azul para el encabezado
        pdf.set_fill_color(0, 45, 98)  # Azul (#002D62)
        pdf.rect(0, 0, 210, 35, style='F')  # Rectángulo azul de 35mm de alto
        
        # Insertar logo de brand en la izquierda del encabezado
        logo_img = obtener_logo_imagen(brand)
        if logo_img:
            try:
                # Convertir a RGB si es necesario
                if logo_img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', logo_img.size, (255, 255, 255))
                    background.paste(logo_img, mask=logo_img.split()[-1])
                    logo_img = background
                
                # Guardar temporalmente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    logo_img.save(temp_file.name, format='JPEG', quality=95)
                    temp_logo_path = temp_file.name
                
                # Insertar logo a la izquierda
                pdf.image(temp_logo_path, x=10, y=5, w=30)
                os.unlink(temp_logo_path)
            except Exception as e:
                logger.error(f"Error al insertar el logo en el PDF: {e}")
        
        # Texto blanco para el encabezado centrado
        pdf.set_text_color(255, 0, 0)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_xy(0, 5)
        pdf.cell(210, 10, "AEROPOSTALE", 0, 1, "C")

        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(0, 18)
        pdf.cell(210, 10, "CENTRO DE DISTRIBUCIÓN FASHION CLUB", 0, 1, "C")
        
        # Restablecer color de texto a negro
        pdf.set_text_color(0, 0, 0)
        
        # Mover hacia abajo
        pdf.set_y(40)
        
        # Guardar posición Y para alineación
        y_start = pdf.get_y()
        
        # === SECCIÓN REMITENTE (izquierda) ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(90, 10, "REMITENTE:", 0, 1)
        
        remitentes = obtener_remitentes()
        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
        
        pdf.set_font("Arial", "", 14)
        pdf.multi_cell(90, 8, f"{remitente_info['name']}\n{remitente_info['address']}")
        
        pdf.ln(5)
        
        # === SECCIÓN DESTINATARIO (izquierda) ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(90, 10, "DESTINATARIO:", 0, 1)
        
        pdf.set_font("Arial", "", 14)
        pdf.cell(90, 8, tracking_number, 0, 1)
        
        tiendas = obtener_tiendas()
        tienda_info = tiendas[tiendas['name'] == store_name].iloc[0]
        
        if 'address' in tienda_info:
            pdf.multi_cell(90, 8, tienda_info['address'])
        
        pdf.ln(5)
        
        # Nombre de la tienda
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(90, 8, store_name, 0, 1)
        
        pdf.ln(5)
        
       
        if 'phone' in tienda_info:
            pdf.cell(90, 8, f"TEL.: {tienda_info['phone']}", 0, 1)
        
        # === CÓDIGO QR (derecha, alineado con los datos) ===
        qr_img = generar_qr_imagen(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            qr_img.save(temp_file.name)
            temp_qr_path = temp_file.name
        
        # Insertar QR a la derecha
        pdf.image(temp_qr_path, x=120, y=y_start, w=80)
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

# ================================
# FUNCIÓN PARA ELIMINAR GUÍAS
# ================================

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

# ================================
# SISTEMA DE AUTENTICACIÓN
# ================================

def verificar_password(tipo_requerido: str = "admin") -> bool:
    """Verifica si el usuario tiene permisos para la sección requerida"""
    # Las secciones públicas siempre son accesibles
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
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Gestión de KPIs</div>
        </div>
        <h2 class="password-title">🔐 Acceso Restringido</h2>
        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 25px;">
            Ingrese la contraseña para acceso de {tipo_requerido}
        </p>
    """.format(tipo_requerido="Administrador" if tipo_requerido == "admin" else "Usuario"), unsafe_allow_html=True)
    
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
# NUEVAS FUNCIONES PARA MOSTRAR ESTADO DE ABASTECIMIENTO
# ================================

def mostrar_estado_abastecimiento():
    """Muestra el estado de abastecimiento para transferencias"""
    resultado = calcular_metas_semanales()
    
    st.markdown("<h2 class='section-title'>📦 Estado de Abastecimiento Semanal</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Meta Semanal</div>
            <p class="metric-value">{resultado['meta_semanal']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Distribuciones Totales</div>
            <p class="metric-value">{resultado['distribuciones_totales']:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tendencia = "trend-up" if resultado['cumplimiento_porcentaje'] >= 100 else "trend-down"
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Cumplimiento</div>
            <p class="metric-value">{resultado['cumplimiento_porcentaje']:.1f}%</p>
            <p class="{tendencia}">Meta: 100%</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Mostrar detalles de abastecimiento
    if resultado['detalles']:
        st.markdown("<div class='warning-box'>⚠️ Problemas de Abastecimiento Detectados</div>", unsafe_allow_html=True)
        
        for detalle in resultado['detalles']:
            st.markdown(f"""
            <div class="info-box">
                <strong>{detalle['transferidor']}</strong> no recibió suficientes distribuciones de <strong>{detalle['proveedor']}</strong><br>
                - Recibido: {detalle['distribuciones_recibidas']:,.0f}<br>
                - Requerido: {detalle['distribuciones_requeridas']:,.0f}<br>
                - Déficit: {detalle['distribuciones_requeridas'] - detalle['distribuciones_recibidas']:,.0f}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='success-box'>✅ Abastecimiento adecuado para cumplir la meta semanal</div>", unsafe_allow_html=True)

def mostrar_gestion_distribuciones():
    """Muestra la interfaz para gestionar distribuciones semanales"""
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Gestión de Distribuciones Semanales</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener fecha de inicio de la semana actual
    fecha_actual = datetime.now().date()
    fecha_inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fecha_inicio_semana_str = fecha_inicio_semana.strftime("%Y-%m-%d")
    
    # Obtener distribuciones existentes si las hay
    distribuciones_existentes = obtener_distribuciones_semana(fecha_inicio_semana_str)
    
    with st.form("form_distribuciones_semanales"):
        st.markdown("<h3 class='section-title'>Distribuciones de la Semana</h3>", unsafe_allow_html=True)
        
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
                st.markdown("<div class='success-box animate-fade-in'>✅ Distribuciones guardadas correctamente!</div>", unsafe_allow_html=True)
                time.sleep(1)
                st.rerun()
            else:
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar las distribuciones.</div>", unsafe_allow_html=True)
    
    # Mostrar estado actual de abastecimiento
    mostrar_estado_abastecimiento()
    
    # Mostrar alertas de abastecimiento
    alertas = verificar_alertas_abastecimiento()
    if alertas:
        st.markdown("<h3 class='section-title'>🚨 Alertas de Abastecimiento</h3>", unsafe_allow_html=True)
        for alerta in alertas:
            if alerta['gravedad'] == 'ALTA':
                st.markdown(f"<div class='error-box'>{alerta['mensaje']}<br>Acción: {alerta['accion']}</div>", unsafe_allow_html=True)

# ================================
# COMPONENTES DE LA APLICACIÓN
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs"""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Mostrar alertas de abastecimiento
    alertas = verificar_alertas_abastecimiento()
    if alertas:
        for alerta in alertas:
            if alerta['gravedad'] == 'ALTA':
                st.markdown(f"<div class='error-box'>🚨 {alerta['mensaje']}</div>", unsafe_allow_html=True)
    
    # Cargar datos históricos
    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos. Por favor, ingresa datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Crear selector de rango de fechas
    st.markdown("<div class='date-selector animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h3>Selecciona el rango de fechas a visualizar:</h3>", unsafe_allow_html=True)
    
    # Obtener fechas únicas y ordenarlas
    if not df.empty and 'fecha' in df.columns:
        # Convertir a fecha y eliminar duplicados
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles.</div>", unsafe_allow_html=True)
        return
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Validar que la fecha de inicio no sea mayor que la fecha de fin
    if fecha_inicio > fecha_fin:
        st.markdown("<div class='error-box animate-fade-in'>❌ La fecha de inicio no puede ser mayor que la fecha de fin.</div>", unsafe_allow_html=True)
        return
    
    # Filtrar datos por rango de fechas seleccionado
    df_rango = df[(df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)]
    if df_rango.empty:
        st.markdown(f"<div class='warning-box animate-fade-in'>⚠️ No hay datos disponibles para el rango de fechas {fecha_inicio} a {fecha_fin}.</div>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<p style='color: var(--text-secondary); font-size: 1.1em;'>Datos para el rango de fechas: {fecha_inicio} a {fecha_fin}</p>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    
    # Cálculos globales
    total_cantidad = df_rango['cantidad'].sum()
    total_meta = df_rango['meta'].sum()
    total_horas = df_rango['horas_trabajo'].sum()
    avg_eficiencia = (df_rango['eficiencia'] * df_rango['horas_trabajo']).sum() / total_horas if total_horas > 0 else 0
    avg_productividad = df_rango['productividad'].mean()
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
    
    # Mostrar estado de abastecimiento
    mostrar_estado_abastecimiento()
    
    st.markdown("<h2 class='section-title animate-fade-in'>📅 Cumplimiento de Metas Mensuales (Transferencias)</h2>", unsafe_allow_html=True)
    
    # Obtener el mes y año del rango de fechas
    current_month = fecha_inicio.month
    current_year = fecha_inicio.year
    
    # Filtrar datos del mes actual para transferencias
    df_month = df[(df['fecha'].dt.month == current_month) & 
                  (df['fecha'].dt.year == current_year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    # Obtener meta mensual de transferencias (usamos el último valor registrado)
    if not df_transferencias_month.empty:
        meta_mensual_transferencias = df_transferencias_month['meta_mensual'].iloc[0]
    else:
        # Si no hay datos, usar un valor por defecto
        meta_mensual_transferencias = 70000
    
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
    equipos = df_rango['equipo'].unique()
    # Ordenar equipos en un orden específico
    orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
    equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
    equipos_finales = equipos_ordenados + equipos_restantes
    
    for equipo in equipos_finales:
        df_equipo = df_rango[df_rango['equipo'] == equipo]
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
        if st.button("📄 Exportar to PDF", use_container_width=True):
            try:
                # Crear un PDF simple con los datos
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Reporte de KPIs - Aeropostale", ln=True, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Período: {fecha_inicio} a {fecha_fin}", ln=True)
                pdf.ln(10)
                
                # Agregar tabla con los datos
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
                
                # Convertir PDF to bytes
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
    if not verificar_password("admin"):  # ← Misma indentación que las demás líneas
        solicitar_autenticacion("admin")
        return
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
    
    # Verificar si ya existen datos para esta fecha
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    datos_existentes = obtener_datos_fecha(fecha_str)
    
    # Inicializar variables de sesión para almacenar datos
    if 'datos_calculados' not in st.session_state:
        st.session_state.datos_calculados = None
    if 'fecha_guardar' not in st.session_state:
        st.session_state.fecha_guardar = None
    
    # Si hay datos existentes, mostrar mensaje
    if not datos_existentes.empty:
        st.markdown(f"<div class='info-box animate-fade-in'>ℹ️ Ya existen datos para la fecha {fecha_seleccionada}. Puede editarlos a continuación.</div>", unsafe_allow_html=True)
    
    periodo = st.radio("Selecciona el período:", ["Día", "Semana"], horizontal=True)
    
    with st.form("form_datos"):
        # Meta mensual única para transferencias
        st.markdown("<h3 class='section-title animate-fade-in'>Meta Mensual de Transferencias</h3>", unsafe_allow_html=True)
        
        # Obtener meta mensual existente si hay datos
        meta_mensual_existente = 70000  # Valor por defecto
        if not datos_existentes.empty:
            meta_mensual_existente = datos_existentes['meta_mensual'].iloc[0] if 'meta_mensual' in datos_existentes.columns else 70000
        
        meta_mensual_transferencias = st.number_input("Meta mensual para el equipo de transferencias:", min_value=0, value=int(meta_mensual_existente), key="meta_mensual_transferencias")
        
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
                
                # Obtener datos existentes para este trabajador si existen
                datos_trabajador = None
                if not datos_existentes.empty:
                    datos_trabajador = datos_existentes[datos_existentes['nombre'] == trabajador].iloc[0] if trabajador in datos_existentes['nombre'].values else None
                
                col1, col2 = st.columns(2)
                with col1:
                    # Establecer valores por defecto basados en datos existentes o valores predeterminados
                    if datos_trabajador is not None:
                        cantidad_default = int(datos_trabajador['cantidad']) if pd.notna(datos_trabajador['cantidad']) else 0
                        meta_default = int(datos_trabajador['meta']) if pd.notna(datos_trabajador['meta']) else 0
                        comentario_default = datos_trabajador['comentario'] if pd.notna(datos_trabajador['comentario']) else ""
                    else:
                        # Valores por defecto según el equipo
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
                        # Para el equipo de Distribución
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
                    # Obtener horas trabajadas existentes o usar valor por defecto
                    if datos_trabajador is not None:
                        horas_default = float(datos_trabajador['horas_trabajo']) if pd.notna(datos_trabajador['horas_trabajo']) else 8.0
                    else:
                        horas_default = 8.0
                    
                    horas = st.number_input(f"Horas trabajadas por {trabajador}:", min_value=0.0, value=horas_default, key=f"{trabajador}_horas", step=0.5)
                    comentario = st.text_area(f"Comentario para {trabajador}:", value=comentario_default, key=f"{trabajador}_comentario")
        
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
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    try:
        # Obtener lista actual de trabajadores
        response = supabase.from_('trabajadores').select('*').order('equipo,nombre', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and hasattr(response, 'data') and response.data:
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
                        if response and hasattr(response, 'data') and response.data:
                            st.markdown("<div class='error-box animate-fade-in'>❌ El trabajador ya existe.</div>", unsafe_allow_html=True)
                            st.session_state.show_preview = False
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
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al agregar trabajador.</div>", unsafe_allow_html=True)
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

def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    """Convierte un objeto de imagen de PIL a bytes."""
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()
    # ================================
# NUEVAS FUNCIONES PARA GESTIÓN DE TIENDAS
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
    
def mostrar_reconciliacion_logistica():
    """Muestra la interfaz de reconciliación logística"""
    if not verificar_password("admin"):
        solicitar_autenticacion("admin")
        return
    
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Reconciliación Logística</h1>", unsafe_allow_html=True)
    
    # Inicializar el reconciliador en session state si no existe
    if 'reconciler' not in st.session_state:
        st.session_state.reconciler = StreamlitLogisticsReconciliation()
        st.session_state.processed = False
        st.session_state.show_details = False
    
    # Cargar archivos
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Cargar Archivos</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
    factura_file = st.file_uploader(
            "Subir archivo de facturas (Excel)",
            type=['xlsx', 'xls'],
            key="factura_file"
        )
    with col2:
        manifiesto_file = st.file_uploader(
            "Subir archivo de manifiesto (Excel)",
            type=['xlsx', 'xls'],
            key="manifiesto_file"
        )
    
    if st.button("🚀 Procesar Archivos", use_container_width=True) and factura_file and manifiesto_file:
        with st.spinner("Procesando archivos..."):
            st.session_state.processed = st.session_state.reconciler.process_files(
                factura_file, manifiesto_file
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Mostrar resultados si se procesaron los archivos
    if st.session_state.processed:
        reconciler = st.session_state.reconciler
        kpis = reconciler.kpis
        
        st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title animate-fade-in'>📊 Métricas Principales</h2>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Facturadas", kpis['total_facturadas'])
        col2.metric("Total Anuladas", kpis['total_anuladas'])
        col3.metric("Total Sobrantes", kpis['total_sobrantes'])
        col4.metric("Valor Promedio Envío", f"${kpis['avg_shipment_value']:.2f}" if kpis['avg_shipment_value'] else "N/A")
        
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Valor Total Pagado", f"${kpis['total_value']:.2f}")
        col6.metric("Valor Facturadas", f"${kpis['value_facturadas']:.2f}")
        col7.metric("Valor Anuladas", f"${kpis['value_anuladas']:.2f}")
        col8.metric("Valor Sobrantes", f"${kpis['value_sobrantes']:.2f}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Gráficos y tablas adicionales
        st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title animate-fade-in'>📈 Análisis Detallado</h2>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Ciudades", "Tiendas", "Gastos", "Volumen", "Anuladas"])
        
        with tab1:
            st.markdown("<h3>Top Ciudades</h3>", unsafe_allow_html=True)
            if not kpis['top_cities'].empty:
                fig = px.bar(
                    x=kpis['top_cities'].index, 
                    y=kpis['top_cities'].values,
                    labels={'x': 'Ciudad', 'y': 'Cantidad'},
                    title='Top Ciudades por Envíos'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para ciudades")
        
        with tab2:
            st.markdown("<h3>Top Tiendas</h3>", unsafe_allow_html=True)
            if not kpis['top_stores'].empty:
                fig = px.bar(
                    x=kpis['top_stores'].index, 
                    y=kpis['top_stores'].values,
                    labels={'x': 'Tienda', 'y': 'Cantidad'},
                    title='Top Tiendas por Envíos'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para tiendas")
        
        # ... (agregar más pestañas según sea necesario)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Botón para ver detalles
        if st.button("Ver Detalles de Guías", use_container_width=True):
            st.session_state.show_details = not st.session_state.show_details
        
        if st.session_state.show_details:
            st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
            st.markdown("<h2 class='section-title animate-fade-in'>🔍 Detalles de Guías</h2>", unsafe_allow_html=True)
            
            with st.expander("Guías Facturadas"):
                st.write(", ".join(reconciler.guides_facturadas))
            
            with st.expander("Guías Anuladas"):
                st.write(", ".join(reconciler.guides_anuladas))
            
            with st.expander("Guías Sobrantes"):
                st.write(", ".join(reconciler.guides_sobrantes))
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Botón para descargar reporte
        pdf_buffer = reconciler.generate_report()
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_buffer,
            file_name=f"reporte_reconciliacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío y gestionar tiendas"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Crear pestañas para las diferentes funcionalidades
    tab1, tab2 = st.tabs(["📋 Generar Guía", "🏬 Gestionar Tiendas"])
    
    with tab1:
        # Código existente para generar guías
        # Obtener datos necesarios
        tiendas = obtener_tiendas()
        remitentes = obtener_remitentes()
        
        if tiendas.empty or remitentes.empty:
            st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
            return
        
        # Inicializar estado de sesión si no existe
        if 'show_preview' not in st.session_state:
            st.session_state.show_preview = False
        if 'pdf_data' not in st.session_state:
            st.session_state.pdf_data = None
        
        # Formulario para generar guía
        st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h2 class='section-title animate-fade-in'>Generar Nueva Guía</h2>", unsafe_allow_html=True)
        
        with st.form("form_generar_guia", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                store_name = st.selectbox("Seleccione Tienda", tiendas['name'].tolist(), key="store_select")
                brand = st.radio("Seleccione Empresa:", ["Fashion", "Tempo"], horizontal=True, key="brand_select")
            
            with col2:
                sender_name = st.selectbox("Seleccione Remitente:", options=remitentes['name'].tolist(), key="sender_select")
                url = st.text_input("Ingrese URL del Pedido:", key="url_input", placeholder="https://...")
            
            # Botón de submit dentro del formulario
            submitted = st.form_submit_button("Generar Guía", use_container_width=True)
            
            if submitted:
                if not all([store_name, brand, url, sender_name]):
                    st.markdown("<div class='error-box animate-fade-in'>❌ Por favor, complete todos los campos.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                elif not url.startswith(('http://', 'https://')):
                    st.markdown("<div class='error-box animate-fade-in'>❌ La URL debe comenzar con http:// or https://</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                else:
                    # Guardar la guía
                    if guardar_guia(store_name, brand, url, sender_name):
                        st.session_state.show_preview = True
                        # Obtener información del remitente
                        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                        st.session_state.remitente_address = remitente_info['address']
                        st.session_state.remitente_phone = remitente_info['phone']
                        st.session_state.tracking_number = generar_numero_seguimiento(1)
                        
                        # Generar PDF y guardarlo en session state
                        st.session_state.pdf_data = generar_pdf_guia(
                            store_name, brand, url, sender_name, st.session_state.tracking_number
                        )
                        
                        st.markdown("<div class='success-box animate-fade-in'>✅ Guía generada correctamente. Puede ver la previsualización y exportarla.</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar la guía.</div>", unsafe_allow_html=True)
                        st.session_state.show_preview = False
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Previsualización de la guía
        if st.session_state.show_preview:
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
            
            # Convertir la imagen PIL a bytes antes de mostrarla
            qr_bytes = pil_image_to_bytes(qr_img)
            st.image(qr_bytes, width=200)
            
            # Botones de exportación
            st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                # Descargar PDF
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
                    # Aquí iría la lógica para actualizar el estado de la guía
                    st.markdown("<div class='success-box animate-fade-in'>✅ Guía marcada como impresa.</div>", unsafe_allow_html=True)
                    st.session_state.show_preview = False
                    # Limpiar datos de la sesión
                    if 'pdf_data' in st.session_state:
                        del st.session_state.pdf_data
                    time.sleep(1)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        # Nueva sección para gestionar tiendas (requiere permisos de admin)
        if not verificar_password("admin"):
            solicitar_autenticacion("admin")
        else:
            st.markdown("<h2 class='section-title animate-fade-in'>Gestión de Tiendas</h2>", unsafe_allow_html=True)
            
            # Obtener tiendas actuales
            tiendas = obtener_tiendas()
            
            if tiendas.empty:
                st.info("No hay tiendas registradas.")
            else:
                st.markdown("<h3>Tiendas Existentes</h3>", unsafe_allow_html=True)
                
                # Mostrar tiendas en un dataframe editable
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
                
                # Botones para guardar cambios y eliminar tiendas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Guardar Cambios", use_container_width=True):
                        cambios_realizados = 0
                        for _, row in edited_tiendas.iterrows():
                            tienda_original = tiendas[tiendas['id'] == row['id']].iloc[0]
                            
                            # Verificar si hay cambios
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
                    # Selector para eliminar tienda
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
            
            # Formulario para agregar nueva tienda
            st.markdown("<h3>Agregar Nueva Tienda</h3>", unsafe_allow_html=True)
            
            with st.form("form_nueva_tienda"):
                col1, col2 = st.columns(2)
                with col1:
                    nuevo_nombre = st.text_input("Nombre de la tienda:", key="nueva_tienda_nombre")
                    nueva_direccion = st.text_area("Dirección:", key="nueva_tienda_direccion")
                with col2:
                    nuevo_telefono = st.text_input("Teléfono:", key="nueva_tienda_telefono")
                    # Espaciador para alinear el botón
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
        
def mostrar_historial_guias():
    """Muestra el historial de guías generadas"""
    if not verificar_password("user"):
        # Mostrar formulario de autenticación para usuario o admin
        if st.session_state.user_type is None:
            solicitar_autenticacion("user")
        return
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
    columns_to_display = ['id', 'store_name', 'brand', 'sender_name', 'status', 'created_at']
    df_display = df_display[columns_to_display]
    
    # Renombrar columnas para mejor presentación
    df_display = df_display.rename(columns={
        'id': 'ID',
        'store_name': 'Tienda',
        'brand': 'Marca',
        'sender_name': 'Remitente',
        'status': 'Estado',
        'created_at': 'Fecha'
    })
    
    st.dataframe(df_display, use_container_width=True)
    
    # Botones de exportación y eliminación
    st.markdown("<div class='export-buttons animate-fade-in'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
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
                    file_name=f"historial_guias_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                logger.error(f"Error al exportar historial de guías a Excel: {e}", exc_info=True)
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al exportar a Excel.</div>", unsafe_allow_html=True)
    
    with col2:
        # Exportar to CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"historial_guias_{fecha_inicio.strftime('%Y%m%d')}_a_{fecha_fin.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Eliminar guías seleccionadas
        if verificar_password():
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
                        st.markdown(f"<div class='success-box animate-fade-in'>✅ {eliminaciones_exitosas} guía(s) eliminada(s) correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al eliminar las guías.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='warning-box animate-fade-in'>⚠️ No se seleccionaron guías para eliminar.</div>", unsafe_allow_html=True)
        else:
            st.info("🔒 Autenticación requerida para eliminar guías")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
def mostrar_generacion_etiquetas():
    """Muestra la interfaz para generar etiquetas de productos"""
    if not verificar_password("user"):
        solicitar_autenticacion("user")
        return

    st.markdown("<h1 class='header-title animate-fade-in'>🏷️ Generación de Etiquetas de Producto</h1>", unsafe_allow_html=True)

    with st.form("form_etiqueta"):
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
        # Retrieve values from session_state after submission
        referencia = st.session_state.etiqueta_referencia
        tipo = st.session_state.etiqueta_tipo
        cantidad = st.session_state.etiqueta_cantidad
        caja = st.session_state.etiqueta_caja
        uploaded_file = st.session_state.etiqueta_imagen  # This is the file object if uploaded

        if not all([referencia, tipo, cantidad is not None, caja is not None]):
            st.error("❌ Por favor, complete todos los campos obligatorios.")
        else:
            # Determinar piso según el tipo
            if tipo == 'hombre':
                piso = 1
            elif tipo == 'mujer':
                piso = 3
            else:
                piso = 2

            # Guardar imagen temporalmente si se subió
            imagen_path = None
            if uploaded_file is not None:
                try:
                    # Crear directorio temporal si no existe
                    os.makedirs("temp", exist_ok=True)
                    # Guardar la imagen en un archivo temporal
                    temp_path = f"temp/{int(datetime.now().timestamp())}_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    imagen_path = temp_path
                except Exception as e:
                    logger.error(f"Error al guardar imagen temporal: {e}")
                    st.error("⚠️ No se pudo procesar la imagen.")

            # Datos para generar la etiqueta
            datos_etiqueta = {
                'referencia': referencia,
                'tipo': tipo,
                'cantidad': int(cantidad),
                'caja': int(caja),
                'piso': piso,
                'imagen_path': imagen_path
            }

            # Generar PDF
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
                # Optional: Clean up temp file
                if imagen_path and os.path.exists(imagen_path):
                    os.remove(imagen_path)
            else:
                st.error("❌ Error al generar la etiqueta.")
                # Clean up if failed
                if imagen_path and os.path.exists(imagen_path):
                    os.remove(imagen_path)

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
        
        # Configuración inicial
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(True, 15)
        
        # Fondo azul para el encabezado
        pdf.set_fill_color(10, 16, 153)  # Azul de Aeropostale (c81d11)
        pdf.rect(0, 0, 210, 35, style='F')  # Rectángulo azul de 35mm de alto
        
        # Texto blanco para el encabezado
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_xy(0, 5)
        pdf.cell(210, 10, "AEROPOSTALE", 0, 1, "C")
        
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(0, 18)
        pdf.cell(210, 10, "PRICE CLUB GUAYAQUIL", 0, 1, "C")
        
        # Restablecer color de texto a negro
        pdf.set_text_color(0, 0, 0)
        
        # Mover hacia abajo
        pdf.set_y(40)
        
      
        # Línea separadora
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
                # Insertar imagen alineada a la derecha
                pdf.image(datos['imagen_path'], x=120, y=40, w=85)
            except Exception as e:
                logger.error(f"Error al insertar imagen en PDF: {e}")
        
        # Mover hacia abajo después de la imagen/texto
        image_height = 40 if datos['imagen_path'] else 0
        pdf.set_y(max(pdf.get_y(), y_start + image_height + 5))
        
        # PISO
        pdf.set_font("Helvetica", "B", 78)
        pdf.cell(190, 15, f"PISO {datos['piso']}", 0, 1, "L")
        
        return pdf.output(dest="S").encode("latin1")
        
    except Exception as e:
        logger.error(f"Error al generar PDF de etiqueta: {e}", exc_info=True)
        return None
import streamlit as st
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
import datetime
from io import BytesIO
import warnings

warnings.filterwarnings('ignore')

class StreamlitLogisticsReconciliation:
    def __init__(self):
        # Estructuras principales
        self.df_facturas = None
        self.df_manifiesto = None
        self.guides_facturadas = []
        self.guides_anuladas = []
        self.guides_sobrantes = []
        # Resultados de KPIs
        self.kpis = {}

    def identify_guide_column(self, df: pd.DataFrame) -> str:
        """Identifica automáticamente la columna de guías en un DataFrame."""
        guide_keywords = ['guia', 'guía', 'nro', 'numero', 'número', 'tracking', 'codigo', 'código', 'id']
        for col in df.columns:
            col_lower = str(col).strip().lower()
            if any(keyword in col_lower for keyword in guide_keywords):
                return col
        return None

    def process_files(self, factura_file, manifiesto_file):
        try:
            # Cargar archivos Excel
            self.df_facturas = pd.read_excel(factura_file, sheet_name=0, header=0)
            self.df_manifiesto = pd.read_excel(manifiesto_file, sheet_name=0, header=0)

            # Limpiar datos
            self.df_facturas = self.df_facturas.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            self.df_manifiesto = self.df_manifiesto.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            # Identificar columnas clave
            factura_guide_col = self.identify_guide_column(self.df_facturas)
            if not factura_guide_col:
                st.error(f"No se pudo identificar la columna de guías en el archivo de facturas.\nColumnas disponibles: {list(self.df_facturas.columns)}")
                return False

            manifiesto_guide_col = self.identify_guide_column(self.df_manifiesto)
            if not manifiesto_guide_col:
                st.error(f"No se pudo identificar la columna de guías en el archivo de manifiesto.\nColumnas disponibles: {list(self.df_manifiesto.columns)}")
                return False

            # Crear columna limpia de guías
            self.df_facturas['GUIDE_CLEAN'] = self.df_facturas[factura_guide_col].astype(str).str.strip().str.upper()
            self.df_manifiesto['GUIDE_CLEAN'] = self.df_manifiesto[manifiesto_guide_col].astype(str).str.strip().str.upper()

            # Eliminar guías vacías
            self.df_facturas = self.df_facturas[self.df_facturas['GUIDE_CLEAN'] != '']
            self.df_manifiesto = self.df_manifiesto[self.df_manifiesto['GUIDE_CLEAN'] != '']

            # Reconciliación
            facturas_set = set(self.df_facturas['GUIDE_CLEAN'])
            manifiesto_set = set(self.df_manifiesto['GUIDE_CLEAN'])

            self.guides_facturadas = sorted(list(facturas_set & manifiesto_set))
            self.guides_anuladas = sorted(list(facturas_set - manifiesto_set))
            self.guides_sobrantes = sorted(list(manifiesto_set - facturas_set))

            # Calcular KPIs
            self.calculate_kpis()
            return True

        except Exception as e:
            st.error(f"Error procesando archivos: {str(e)}")
            return False

    def calculate_kpis(self):
        """Calcula todos los KPIs necesarios a partir de los datos procesados."""
        try:
            # KPIs básicos
            self.kpis['total_facturadas'] = len(self.guides_facturadas)
            self.kpis['total_anuladas'] = len(self.guides_anuladas)
            self.kpis['total_sobrantes'] = len(self.guides_sobrantes)

            # Valor promedio y total (simulado, ajusta según tus columnas reales)
            valor_cols_factura = [col for col in self.df_facturas.columns if 'valor' in col.lower() or 'monto' in col.lower()]
            valor_col = valor_cols_factura[0] if valor_cols_factura else None

            if valor_col and valor_col in self.df_facturas.columns:
                facturadas_mask = self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)
                anuladas_mask = self.df_facturas['GUIDE_CLEAN'].isin(self.guides_anuladas)
                self.kpis['value_facturadas'] = self.df_facturas.loc[facturadas_mask, valor_col].sum()
                self.kpis['value_anuladas'] = self.df_facturas.loc[anuladas_mask, valor_col].sum()
                self.kpis['total_value'] = self.kpis['value_facturadas'] + self.kpis['value_anuladas']
                self.kpis['avg_shipment_value'] = self.kpis['total_value'] / (
                    len(self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)])
                ) if self.kpis['total_value'] > 0 else 0.0
                self.kpis['value_sobrantes'] = 0.0  # No facturadas
            else:
                self.kpis['value_facturadas'] = 0.0
                self.kpis['value_anuladas'] = 0.0
                self.kpis['total_value'] = 0.0
                self.kpis['avg_shipment_value'] = 0.0
                self.kpis['value_sobrantes'] = 0.0

            # Top Ciudades
            ciudad_col = 'CIUDAD_DESTINO'
            if ciudad_col in self.df_facturas.columns:
                top_cities = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)][ciudad_col].value_counts().head(10)
                self.kpis['top_cities'] = top_cities
            else:
                self.kpis['top_cities'] = pd.Series(dtype=int)

            # Top Tiendas
            tienda_col = 'TIENDA'
            if tienda_col in self.df_facturas.columns:
                top_stores = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)][tienda_col].value_counts().head(10)
                self.kpis['top_stores'] = top_stores
            else:
                self.kpis['top_stores'] = pd.Series(dtype=int)

            # Gasto por ciudad
            if ciudad_col in self.df_facturas.columns and valor_col:
                spending_by_city = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)].groupby(ciudad_col)[valor_col].sum().sort_values(ascending=False).head(10)
                self.kpis['spending_by_city'] = spending_by_city
            else:
                self.kpis['spending_by_city'] = pd.Series(dtype=float)

            # Gasto por tienda
            if tienda_col in self.df_facturas.columns and valor_col:
                spending_by_store = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)].groupby(tienda_col)[valor_col].sum().sort_values(ascending=False).head(10)
                self.kpis['spending_by_store'] = spending_by_store
            else:
                self.kpis['spending_by_store'] = pd.Series(dtype=float)

            # Volumen por mes
            fecha_col = 'FECHA'
            if fecha_col in self.df_facturas.columns:
                self.df_facturas[fecha_col] = pd.to_datetime(self.df_facturas[fecha_col], errors='coerce')
                shipment_volume = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_facturadas)].groupby(
                    self.df_facturas[fecha_col].dt.to_period('M')).size()
                self.kpis['shipment_volume'] = shipment_volume
            else:
                self.kpis['shipment_volume'] = pd.Series(dtype=int)

            # Anuladas por destinatario
            destinatario_col = 'DESTINATARIO'
            if destinatario_col in self.df_facturas.columns:
                anuladas_df = self.df_facturas[self.df_facturas['GUIDE_CLEAN'].isin(self.guides_anuladas)]
                anuladas_group = anuladas_df.groupby(destinatario_col).size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False)
                self.kpis['anuladas_by_destinatario'] = anuladas_group
            else:
                self.kpis['anuladas_by_destinatario'] = pd.DataFrame(columns=['Destinatario', 'Cantidad'])

        except Exception as e:
            st.error(f"Error calculando KPIs: {str(e)}")
            self.kpis.update({
                'total_facturadas': 0,
                'total_anuladas': 0,
                'total_sobrantes': 0,
                'value_facturadas': 0.0,
                'value_anuladas': 0.0,
                'total_value': 0.0,
                'avg_shipment_value': 0.0,
                'value_sobrantes': 0.0,
                'top_cities': pd.Series(dtype=int),
                'top_stores': pd.Series(dtype=int),
                'spending_by_city': pd.Series(dtype=float),
                'spending_by_store': pd.Series(dtype=float),
                'shipment_volume': pd.Series(dtype=int),
                'anuladas_by_destinatario': pd.DataFrame()
            })

    def generate_report(self):
        """Genera un informe PDF con los resultados de la reconciliación."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Logistics Reconciliation Report", styles['Title']))
        elements.append(Spacer(1, 12))

        kpi_data = [
            ['Métrica', 'Valor'],
            ['Total Facturadas', str(self.kpis.get('total_facturadas', 0))],
            ['Total Anuladas', str(self.kpis.get('total_anuladas', 0))],
            ['Total Sobrantes', str(self.kpis.get('total_sobrantes', 0))],
            ['Valor Total Pagado', f"${self.kpis.get('total_value', 0):.2f}"],
            ['Valor Promedio Envío', f"${self.kpis.get('avg_shipment_value', 0):.2f}"]
        ]
        table = Table(kpi_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        doc.build(elements)
        buffer.seek(0)
        return buffer
# ================================
# FUNCIÓN PRINCIPAL
# ================================
st.title("📦 Logistics Reconciliation & Business Intelligence Tool")

        factura_file = st.sidebar.file_uploader(
        "Upload Invoice File (Excel)",
        type=['xlsx', 'xls']
    )

    manifiesto_file = st.sidebar.file_uploader(
        "Upload Manifest File (Excel)",
        type=['xlsx', 'xls']
    )

    process_btn = st.sidebar.button("🚀 Process Files")

    if process_btn and factura_file and manifiesto_file:
        with st.spinner("Processing files..."):
            st.session_state.processed = st.session_state.reconciler.process_files(
                factura_file, manifiesto_file
            )

    if st.session_state.processed:
        reconciler = st.session_state.reconciler
        kpis = reconciler.kpis

        st.header("📊 Key Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Facturadas", kpis['total_facturadas'])
        col2.metric("Total Anuladas", kpis['total_anuladas'])
        col3.metric("Total Sobrantes", kpis['total_sobrantes'])
        col4.metric("Valor Promedio de Envío", f"${kpis['avg_shipment_value']:.2f}" if kpis['avg_shipment_value'] else "N/A")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Valor Total Pagado", f"${kpis['total_value']:.2f}")
        col6.metric("Valor Facturadas", f"${kpis['value_facturadas']:.2f}")
        col7.metric("Valor Anuladas", f"${kpis['value_anuladas']:.2f}")
        col8.metric("Valor Sobrantes (No Facturadas)", f"${kpis['value_sobrantes']:.2f}")

        st.subheader("Top Ciudades")
        if not kpis['top_cities'].empty:
            st.bar_chart(kpis['top_cities'])
        else:
            st.info("No data available for top cities")

        st.subheader("Top Tiendas")
        if not kpis['top_stores'].empty:
            st.bar_chart(kpis['top_stores'])
        else:
            st.info("No data available for top stores")

        st.subheader("Gasto por Ciudad")
        if not kpis['spending_by_city'].empty:
            st.bar_chart(kpis['spending_by_city'])
        else:
            st.info("No data available for spending by city")

        st.subheader("Gasto por Tienda")
        if not kpis['spending_by_store'].empty:
            st.bar_chart(kpis['spending_by_store'])
        else:
            st.info("No data available for spending by store")

        st.subheader("Volumen de Envíos por Mes")
        if not kpis['shipment_volume'].empty:
            st.bar_chart(kpis['shipment_volume'])
        else:
            st.info("No data available for shipment volume")

        st.subheader("Anuladas por Destinatario")
        if not kpis['anuladas_by_destinatario'].empty:
            st.dataframe(kpis['anuladas_by_destinatario'])
        else:
            st.info("No data available for anuladas by destinatario")

        # Botón para ver detalles
        if st.button("Ver Detalles de Guías"):
            st.session_state.show_details = not st.session_state.show_details

        if st.session_state.show_details:
            with st.expander("Guías Facturadas"):
                st.write(", ".join(reconciler.guides_facturadas))

            with st.expander("Guías Anuladas (Facturadas pero no en Manifiesto)"):
                st.write(", ".join(reconciler.guides_anuladas))

            with st.expander("Guías Sobrantes (No Facturadas, en Manifiesto pero no en Facturas)"):
                st.write(", ".join(reconciler.guides_sobrantes))

        # Botón para descargar reporte PDF
        pdf_buffer = reconciler.generate_report()
        st.download_button(
            label="📥 Download Report PDF",
            data=pdf_buffer,
            file_name="logistics_report.pdf",
            mime="application/pdf"
        )
    """Función principal de la aplicación"""
    
    # Mostrar logo y título en el sidebar
    st.sidebar.markdown("""
    <div class='sidebar-title'>
        <div class='aeropostale-logo'>AEROPOSTALE</div>
        <div class='aeropostale-subtitle'>Sistema de Gestión de KPIs</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar session state variables si no existen
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'selected_menu' not in st.session_state:
        st.session_state.selected_menu = 0
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    
    # Definir opciones de menú
    menu_options = [
        ("Dashboard KPIs", "📊", mostrar_dashboard_kpis, "public"),
        ("Análisis Histórico", "📈", mostrar_analisis_historico_kpis, "public"),
        ("Ingreso de Datos", "📥", mostrar_ingreso_datos_kpis, "admin"),
        ("Gestión de Trabajadores", "👥", mostrar_gestion_trabajadores_kpis, "admin"),
        ("Gestión de Distribuciones", "📦", mostrar_gestion_distribuciones, "admin"),
        ("Reconciliación Logística", "📦", mostrar_reconciliacion_logistica, "admin"),
        ("Generar Guías", "📋", mostrar_generacion_guias, "user"),
        ("Historial de Guías", "🔍", mostrar_historial_guias, "user"),
        ("Generar Etiquetas", "🏷️", mostrar_generacion_etiquetas, "user"),
        ("Ayuda y Contacto", "❓", mostrar_ayuda, "public")
    ]
    
    # Mostrar opciones del menú según permisos
    for i, (label, icon, _, permiso) in enumerate(menu_options):
        # Verificar si la opción debe mostrarse
        mostrar_opcion = False
        
        if permiso == "public":
            mostrar_opcion = True
        elif permiso == "user" and st.session_state.user_type in ["user", "admin"]:
            mostrar_opcion = True
        elif permiso == "admin" and st.session_state.user_type == "admin":
            mostrar_opcion = True
        
        if mostrar_opcion:
            selected = st.sidebar.button(
                f"{icon} {label}",
                key=f"menu_{i}",
                use_container_width=True
            )
            if selected:
                st.session_state.selected_menu = i
    
    # Mostrar botón de login si no está autenticado
    if st.session_state.user_type is None:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("👤 Acceso Usuario", use_container_width=True):
                st.session_state.show_login = True
                st.session_state.login_type = "user"
        with col2:
            if st.button("🔧 Acceso Admin", use_container_width=True):
                st.session_state.show_login = True
                st.session_state.login_type = "admin"
        
        if st.session_state.get('show_login', False):
            solicitar_autenticacion(st.session_state.get('login_type', 'user'))
    
    # Mostrar botón de logout si está autenticado
    else:
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.user_type = None
            st.session_state.password_correct = False
            st.session_state.selected_menu = 0
            st.session_state.show_login = False
            st.rerun()
        
        # Mostrar información del usuario actual
        st.sidebar.info(f"Usuario: {'Administrador' if st.session_state.user_type == 'admin' else 'Usuario'}")
    
    # Verificar que selected_menu esté dentro del rango válido
    if st.session_state.selected_menu >= len(menu_options):
        st.session_state.selected_menu = 0
    
    # Obtener la opción seleccionada
    label, icon, func, permiso = menu_options[st.session_state.selected_menu]
    
    # Verificar permisos para la opción seleccionada
    if permiso == "public":
        func()
    elif permiso == "user" and st.session_state.user_type in ["user", "admin"]:
        func()
    elif permiso == "admin" and st.session_state.user_type == "admin":
        func()
    else:
        # Mostrar mensaje de acceso denegado
        st.error("🔒 Acceso restringido. Necesita autenticarse para acceder a esta sección.")
        
        # Mostrar opciones de autenticación según el tipo requerido
        if permiso == "admin":
            solicitar_autenticacion("admin")
        else:
            solicitar_autenticacion("user")
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.<br>
        Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com">Wilson Pérez</a>
    </div>
    """, unsafe_allow_html=True)
if __name__ == "__main__":
    main()
