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
            f"{brand_lower.upper()}.JPG",
            f"{brand_lower.upper()}.JPEG",
            f"{brand_lower.upper()}.PNG",
            f"{brand.capitalize()}.jpg",
            f"{brand.capitalize()}.jpeg",
            f"{brand.capitalize()}.png"
        ]
        
        for file_name in posibles_nombres:
            # CONSTRUCCIÓN CORRECTA DE LA URL PÚBLICA DE SUPABASE
            logo_url = f"https://{project_id}.supabase.co/storage/v1/object/public/{bucket_name}/{file_name}"
            
            if verificar_imagen_existe(logo_url):
                logger.info(f"Imagen encontrada para marca {brand} en el servidor: {logo_url}")
                return logo_url
                
        logger.warning(f"No se pudo encontrar una imagen para la marca {brand}")
        return None
    except Exception as e:
        logger.error(f"Error al buscar logo de la marca {brand}: {e}", exc_info=True)
        return None

# ================================
# COMPONENTES DE LA INTERFAZ
# ================================

def mostrar_kpis_dashboard():
    """Muestra el dashboard principal con los KPIs"""
    st.title("📊 Dashboard de KPIs Operacionales")
    st.markdown("### Resumen de Productividad por Equipo")
    
    # Cargar datos históricos
    df_historico = cargar_historico_db(fecha_inicio=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    if not df_historico.empty:
        df_equipo = df_historico.groupby('equipo').agg(
            total_cantidad=('cantidad', 'sum'),
            total_meta=('meta', 'sum'),
            total_horas=('horas_trabajo', 'sum')
        ).reset_index()
        
        # Calcular eficiencia por equipo
        df_equipo['eficiencia_promedio'] = (df_equipo['total_cantidad'] / df_equipo['total_meta']) * 100
        
        # Tarjetas de KPIs por equipo
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"<div class='kpi-card'><div class='metric-label'>Transferencias</div><div class='metric-value'>{df_equipo[df_equipo['equipo'] == 'Transferencias']['eficiencia_promedio'].iloc[0]:.1f}%</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='kpi-card'><div class='metric-label'>Distribución</div><div class='metric-value'>{df_equipo[df_equipo['equipo'] == 'Distribución']['eficiencia_promedio'].iloc[0]:.1f}%</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='kpi-card'><div class='metric-label'>Arreglo</div><div class='metric-value'>{df_equipo[df_equipo['equipo'] == 'Arreglo']['eficiencia_promedio'].iloc[0]:.1f}%</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='kpi-card'><div class='metric-label'>Guías</div><div class='metric-value'>{df_equipo[df_equipo['equipo'] == 'Guías']['eficiencia_promedio'].iloc[0]:.1f}%</div></div>", unsafe_allow_html=True)
        with col5:
            st.markdown(f"<div class='kpi-card'><div class='metric-label'>Ventas</div><div class='metric-value'>{df_equipo[df_equipo['equipo'] == 'Ventas']['eficiencia_promedio'].iloc[0]:.1f}%</div></div>", unsafe_allow_html=True)
            
        # Gráficos
        st.markdown("---")
        st.markdown("### Productividad Promedio por Trabajador")
        
        col1, col2 = st.columns(2)
        
        # Gráfico 1: Eficiencia por trabajador
        df_trabajador = df_historico.groupby('nombre').agg(
            total_cantidad=('cantidad', 'sum'),
            total_meta=('meta', 'sum')
        ).reset_index()
        df_trabajador['eficiencia'] = (df_trabajador['total_cantidad'] / df_trabajador['total_meta']) * 100
        fig_eficiencia = crear_grafico_interactivo(df_trabajador, 'nombre', 'eficiencia', 'Eficiencia de Producción', 'Trabajador', 'Eficiencia (%)')
        with col1:
            st.plotly_chart(fig_eficiencia, use_container_width=True)
            
        # Gráfico 2: Cantidad por trabajador
        fig_cantidad = crear_grafico_interactivo(df_trabajador, 'nombre', 'total_cantidad', 'Cantidad Total Producida', 'Trabajador', 'Cantidad')
        with col2:
            st.plotly_chart(fig_cantidad, use_container_width=True)
            
        # Tablas detalladas
        st.markdown("---")
        st.markdown("### Detalles de la Productividad")
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos disponibles para mostrar el dashboard. ¡Ingrese algunos datos en el formulario!")

def mostrar_formulario_kpis():
    """Muestra el formulario para ingresar datos de KPIs diarios"""
    st.title("📝 Formulario de Ingreso de KPIs")
    st.info("Utilice este formulario para registrar las métricas de rendimiento diarias de su equipo.")
    
    # Obtener la fecha seleccionada o la actual por defecto
    hoy = datetime.now().date()
    fecha_default = st.session_state.get('fecha_seleccionada', hoy)
    fecha_seleccionada = st.date_input("🗓️ Seleccione la fecha del registro:", value=fecha_default, key='fecha_input')
    
    st.session_state.fecha_seleccionada = fecha_seleccionada
    
    # Cargar datos existentes para la fecha seleccionada
    df_existente = obtener_datos_fecha(fecha_seleccionada.strftime("%Y-%m-%d"))
    
    # Obtener listas de trabajadores y equipos
    df_trabajadores = obtener_trabajadores()
    equipos = obtener_equipos()
    
    if df_trabajadores.empty:
        st.error("No se pudo cargar la lista de trabajadores. Verifique la conexión a la base de datos.")
        return
    
    trabajadores = df_trabajadores['nombre'].unique().tolist()
    
    # Formulario para ingresar datos
    with st.form("kpi_form", clear_on_submit=False):
        
        st.subheader("Datos Generales")
        
        # Diccionario para almacenar los datos ingresados
        datos_ingresados = {}
        
        # Crear un expander para cada equipo
        for equipo in equipos:
            with st.expander(f"📦 Equipo de {equipo}", expanded=False):
                trabajadores_equipo = df_trabajadores[df_trabajadores['equipo'] == equipo]['nombre'].tolist()
                
                # Iterar sobre cada trabajador del equipo
                for trabajador in trabajadores_equipo:
                    
                    st.markdown(f"**Trabajador:** {trabajador}")
                    
                    # Cargar datos existentes si los hay
                    datos_trabajador = df_existente[df_existente['nombre'] == trabajador].to_dict('records')[0] if not df_existente[df_existente['nombre'] == trabajador].empty else {}
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        cantidad = st.number_input(f"Cantidad producida:", 
                                                   min_value=0, 
                                                   value=int(datos_trabajador.get('cantidad', 0)), 
                                                   key=f"{trabajador}_cantidad")
                        
                    with col2:
                        meta = st.number_input(f"Meta Diaria:", 
                                               min_value=0, 
                                               value=int(datos_trabajador.get('meta', 0)), 
                                               key=f"{trabajador}_meta")
                        
                    with col3:
                        horas = st.number_input(f"Horas trabajadas:", 
                                                min_value=0.0, 
                                                value=float(datos_trabajador.get('horas_trabajo', 8.0)), 
                                                step=0.5, 
                                                key=f"{trabajador}_horas")
                        
                    comentario = st.text_area(f"Comentario:", 
                                              value=datos_trabajador.get('comentario', ""), 
                                              key=f"{trabajador}_comentario")
                    
                    # Calcular eficiencia y productividad
                    eficiencia = calcular_kpi(cantidad, meta)
                    productividad = productividad_hora(cantidad, horas)
                    
                    # Almacenar los datos para el envío
                    datos_ingresados[trabajador] = {
                        "actividad": equipo,
                        "cantidad": cantidad,
                        "meta": meta,
                        "eficiencia": eficiencia,
                        "productividad": productividad,
                        "comentario": comentario,
                        "meta_mensual": meta * 22,  # Asumir 22 días laborales
                        "horas_trabajo": horas,
                        "equipo": equipo
                    }
                    st.markdown("---")
        
        st.subheader("Datos Adicionales")
        with st.expander("🚚 Datos de Distribución Semanal", expanded=True):
            st.info("Ingrese las distribuciones de esta semana.")
            fecha_inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
            st.write(f"Semana del: **{fecha_inicio_semana.strftime('%d-%m-%Y')}**")
            
            # Obtener datos de distribución semanales existentes
            distribuciones_existentes = obtener_distribuciones_semana(fecha_inicio_semana.strftime("%Y-%m-%d"))
            
            col_dist1, col_dist2 = st.columns(2)
            with col_dist1:
                tempo_distribuciones = st.number_input("Distribuciones de Tempo (Unidades)", 
                                                       min_value=0, 
                                                       value=distribuciones_existentes['tempo'], 
                                                       key="tempo_distribuciones")
            with col_dist2:
                luis_distribuciones = st.number_input("Distribuciones de Luis (Unidades)", 
                                                      min_value=0, 
                                                      value=distribuciones_existentes['luis'], 
                                                      key="luis_distribuciones")
        
        submitted = st.form_submit_button("💾 Guardar Datos")
        
        if submitted:
            # Guardar datos diarios
            if guardar_datos_db(fecha_seleccionada.strftime("%Y-%m-%d"), datos_ingresados):
                st.success("✅ Datos guardados exitosamente!")
            else:
                st.error("❌ Error al guardar los datos diarios.")
            
            # Guardar distribuciones semanales
            if guardar_distribuciones_semanales(fecha_inicio_semana.strftime("%Y-%m-%d"), tempo_distribuciones, luis_distribuciones):
                st.success("✅ Distribuciones semanales actualizadas!")
            else:
                st.error("❌ Error al guardar las distribuciones semanales.")

def mostrar_reportes_kpis():
    """Muestra la sección de reportes de KPIs y análisis"""
    st.title("📈 Reportes y Análisis de KPIs")
    st.info("Explore el rendimiento de los equipos y trabajadores en periodos de tiempo específicos.")
    
    # Obtener datos de trabajadores para el filtro
    df_trabajadores = obtener_trabajadores()
    trabajadores = ['Todos'] + df_trabajadores['nombre'].unique().tolist()
    
    # Filtros
    st.markdown("### Filtros de Búsqueda")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        fecha_inicio = st.date_input("Fecha de Inicio:", datetime.now().date() - timedelta(days=30))
    with col_filtro2:
        fecha_fin = st.date_input("Fecha de Fin:", datetime.now().date())
    with col_filtro3:
        trabajador_seleccionado = st.selectbox("Seleccionar Trabajador:", trabajadores)
    
    # Botón de carga
    if st.button("🔎 Cargar Reporte"):
        with st.spinner("Cargando datos..."):
            trabajador_filtro = trabajador_seleccionado if trabajador_seleccionado != 'Todos' else None
            df_reporte = cargar_historico_db(
                fecha_inicio=fecha_inicio.strftime("%Y-%m-%d"),
                fecha_fin=fecha_fin.strftime("%Y-%m-%d"),
                trabajador=trabajador_filtro
            )
            
            if not df_reporte.empty:
                st.session_state.reporte_data = df_reporte
                st.success("✅ Reporte cargado exitosamente!")
            else:
                st.warning("⚠️ No se encontraron datos para los filtros seleccionados.")
    
    # Mostrar reporte
    if 'reporte_data' in st.session_state and not st.session_state.reporte_data.empty:
        df_reporte = st.session_state.reporte_data
        
        # Mostrar KPIs resumen
        st.markdown("---")
        st.markdown("### Resumen del Período")
        col_resumen1, col_resumen2, col_resumen3 = st.columns(3)
        
        total_cantidad = df_reporte['cantidad'].sum()
        total_meta = df_reporte['meta'].sum()
        eficiencia_total = (total_cantidad / total_meta) * 100 if total_meta > 0 else 0
        
        with col_resumen1:
            st.metric("📦 Cantidad Total", f"{total_cantidad:,.0f} Unidades")
        with col_resumen2:
            st.metric("🎯 Meta Total", f"{total_meta:,.0f} Unidades")
        with col_resumen3:
            st.metric("📊 Eficiencia Total", f"{eficiencia_total:.2f}%")
        
        # Gráficos de rendimiento
        st.markdown("---")
        st.markdown("### Rendimiento Diario y por Trabajador")
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            df_diario = df_reporte.groupby(df_reporte['fecha'].dt.date).agg(
                cantidad_diaria=('cantidad', 'sum'),
                meta_diaria=('meta', 'sum')
            ).reset_index()
            fig_diario = crear_grafico_interactivo(df_diario, 'fecha', 'cantidad_diaria', 'Cantidad Producida Diariamente', 'Fecha', 'Cantidad', tipo='line')
            st.plotly_chart(fig_diario, use_container_width=True)
            
        with col_graf2:
            df_trabajador_prod = df_reporte.groupby('nombre')['cantidad'].sum().reset_index()
            fig_prod_trabajador = crear_grafico_interactivo(df_trabajador_prod, 'nombre', 'cantidad', 'Productividad por Trabajador', 'Trabajador', 'Cantidad', tipo='bar')
            st.plotly_chart(fig_prod_trabajador, use_container_width=True)
            
        # Tabla de datos
        st.markdown("---")
        st.markdown("### Datos Detallados del Reporte")
        st.dataframe(df_reporte, use_container_width=True, hide_index=True)
    else:
        st.info("Seleccione los filtros y haga clic en 'Cargar Reporte' para ver los datos.")

def mostrar_guia_ingreso():
    """Muestra el formulario para crear una guía de envío"""
    st.title("📝 Generador de Guías de Envío")
    st.info("Llene los datos para generar una guía de envío con su respectivo código QR.")
    
    # Obtener listas de tiendas y remitentes
    df_tiendas = obtener_tiendas()
    df_remitentes = obtener_remitentes()
    
    if df_tiendas.empty or df_remitentes.empty:
        st.error("No se pudieron cargar las tiendas o remitentes desde la base de datos.")
        return
        
    tiendas = df_tiendas['name'].unique().tolist()
    remitentes = df_remitentes['name'].unique().tolist()
    
    with st.form("guia_form", clear_on_submit=False):
        st.subheader("Detalles de la Guía")
        
        col1, col2 = st.columns(2)
        with col1:
            store_name = custom_selectbox("Seleccione la Tienda:", tiendas, key="guia_tienda")
        with col2:
            brand = st.text_input("Marca de la Ropa:", value="", placeholder="Ej: Aeropostale, Fashion, etc.")
            
        sender_name = custom_selectbox("Seleccione Remitente:", remitentes, key="guia_remitente")
        
        submitted = st.form_submit_button("📦 Generar Guía")
        
        if submitted:
            if not store_name or not brand or not sender_name:
                st.error("Por favor, complete todos los campos.")
            else:
                with st.spinner("Generando guía..."):
                    # Simular la inserción para obtener un ID
                    id_guia_simulado = supabase.from_('guide_logs').insert({'store_name': store_name, 'brand': brand, 'sender_name': sender_name}).execute()
                    
                    if id_guia_simulado and hasattr(id_guia_simulado, 'data') and id_guia_simulado.data:
                        record_id = id_guia_simulado.data[0]['id']
                        tracking_number = generar_numero_seguimiento(record_id)
                        
                        # Generar URL del QR
                        qr_data = {
                            "id_guia": record_id,
                            "seguimiento": tracking_number,
                            "tienda": store_name,
                            "marca": brand,
                            "remitente": sender_name
                        }
                        # Simular URL de la guía
                        guia_url = f"https://your-domain.com/guia?id={record_id}"
                        
                        # Guardar la guía con la URL real
                        if guardar_guia(store_name, brand, guia_url, sender_name):
                            st.success("✅ Guía generada y guardada exitosamente!")
                            st.markdown("---")
                            
                            st.subheader("Guía de Envío Lista!")
                            
                            col_info, col_qr = st.columns([2, 1])
                            
                            with col_info:
                                st.markdown(f"**Número de Seguimiento:** `{tracking_number}`")
                                st.markdown(f"**Tienda Destino:** `{store_name}`")
                                st.markdown(f"**Marca:** `{brand}`")
                                st.markdown(f"**Remitente:** `{sender_name}`")
                                
                                logo_url = obtener_url_logo(brand)
                                if logo_url:
                                    st.image(logo_url, caption=f"Logo de {brand}", width=150)
                                
                            with col_qr:
                                st.markdown("<div class='qr-preview'>", unsafe_allow_html=True)
                                qr_image = generar_qr_imagen(guia_url)
                                # Guardar temporalmente la imagen para mostrarla
                                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                                    qr_image.save(temp_img.name)
                                    st.image(temp_img.name, caption="Código QR", width=150)
                                    os.unlink(temp_img.name)  # Eliminar el archivo temporal
                                st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Botón para descargar PDF
                            if st.button("⬇️ Descargar PDF de la Guía"):
                                pdf_buffer = generar_pdf_guia(tracking_number, store_name, brand, sender_name, qr_image)
                                st.download_button(
                                    label="Descargar PDF",
                                    data=pdf_buffer,
                                    file_name=f"guia_{tracking_number}.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error("❌ Ocurrió un error al guardar la guía.")
                    else:
                        st.error("❌ No se pudo generar un ID para la guía.")

def mostrar_historial_guias():
    """Muestra el historial de guías de envío"""
    st.title("📦 Historial de Guías de Envío")
    st.info("Aquí puede ver y descargar las guías de envío generadas.")
    
    df_historial = obtener_historial_guias()
    
    if not df_historial.empty:
        df_historial_display = df_historial[['created_at', 'store_name', 'brand', 'sender_name', 'status']].copy()
        df_historial_display.rename(columns={
            'created_at': 'Fecha y Hora',
            'store_name': 'Tienda',
            'brand': 'Marca',
            'sender_name': 'Remitente',
            'status': 'Estado'
        }, inplace=True)
        
        st.dataframe(df_historial_display, use_container_width=True, hide_index=True)
    else:
        st.info("No se han generado guías de envío aún.")

def generar_pdf_guia(tracking_number: str, store_name: str, brand: str, sender_name: str, qr_image: Image.Image) -> BytesIO:
    """Genera un PDF de la guía de envío y lo devuelve como un buffer de bytes"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20, bottomMargin=20, leftMargin=20, rightMargin=20)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['h2']
    body_style = styles['Normal']
    
    # Título
    story.append(Paragraph("Guía de Envío Aeropostale", title_style))
    story.append(Spacer(1, 12))
    
    # Información de la guía
    story.append(Paragraph(f"<b>Número de Seguimiento:</b> {tracking_number}", body_style))
    story.append(Paragraph(f"<b>Tienda Destino:</b> {store_name}", body_style))
    story.append(Paragraph(f"<b>Marca:</b> {brand}", body_style))
    story.append(Paragraph(f"<b>Remitente:</b> {sender_name}", body_style))
    story.append(Spacer(1, 24))
    
    # Convertir la imagen QR a un formato que ReportLab pueda usar
    qr_img_buffer = BytesIO()
    qr_image.save(qr_img_buffer, format='PNG')
    qr_img_buffer.seek(0)
    img = Image(qr_img_buffer, width=150, height=150)
    story.append(img)
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer

# ================================
# SISTEMA DE AUTENTICACIÓN
# ================================

def solicitar_autenticacion(requiere_permiso: str):
    """Muestra el formulario de inicio de sesión"""
    st.markdown("""
        <div class="password-container">
            <h1 class="password-title">🔒 Ingreso Seguro</h1>
            <div class="logo-container">
                <span class="aeropostale-logo">AEROPOSTALE</span>
            </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Ingrese la contraseña:", type="password", help="Contraseña para acceder al sistema.")
    
    # Definir la contraseña y el tipo de usuario requerido
    if requiere_permiso == "admin":
        password_valida = ADMIN_PASSWORD
        mensaje_error = "Contraseña de administrador incorrecta."
    elif requiere_permiso == "user":
        password_valida = USER_PASSWORD
        mensaje_error = "Contraseña de usuario incorrecta."
    else:
        password_valida = None
        mensaje_error = "Permiso no reconocido."
        
    submitted = st.button("🔑 Entrar")
    
    if submitted:
        if password == password_valida:
            st.session_state.password_correct = True
            st.session_state.show_login = False
            st.session_state.user_type = requiere_permiso
            st.rerun()
        else:
            st.error(mensaje_error)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
# ================================
# FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ================================

def main():
    """Lógica principal de la aplicación"""
    
    if not st.session_state.password_correct:
        st.session_state.show_login = True

    # Lógica de autenticación
    if st.session_state.show_login:
        solicitar_autenticacion("user") # Opcional, puede cambiar a "admin" si se requiere
    else:
        # Menú de navegación en el sidebar
        st.sidebar.image(obtener_url_logo("aeropostale"), width=200)
        
        menu_options = [
            ("Dashboard", "📊", mostrar_kpis_dashboard, "public"),
            ("Ingreso de KPIs", "📝", mostrar_formulario_kpis, "user"),
            ("Reportes", "📈", mostrar_reportes_kpis, "user"),
            ("Generar Guía", "📦", mostrar_guia_ingreso, "user"),
            ("Historial de Guías", "📜", mostrar_historial_guias, "user"),
            ("Configuración", "⚙️", lambda: st.info("Sección de configuración."), "admin")
        ]
        
        st.sidebar.markdown("---")
        
        # Iterar sobre las opciones del menú
        for i, (label, icon, func, permiso) in enumerate(menu_options):
            # Controlar el acceso al menú según el tipo de usuario
            if permiso == "public" or \
               (permiso == "user" and st.session_state.user_type in ["user", "admin"]) or \
               (permiso == "admin" and st.session_state.user_type == "admin"):
                
                if st.sidebar.button(f"{icon} {label}", key=f"menu_button_{i}", use_container_width=True):
                    st.session_state.selected_menu = i
                    st.rerun()

        st.sidebar.markdown("---")
        
        # Botón de cierre de sesión
        if st.sidebar.button("Cerrar Sesión", key="logout_button"):
            st.session_state.password_correct = False
            st.session_state.user_type = None
            st.session_state.show_login = True
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
        Desarrollado por: <a href="mailto:info@aeropostale.com">info@aeropostale.com</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
