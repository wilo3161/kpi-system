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
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
import pandas as pd
import pdfplumber
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
import streamlit as st

class StreamlitLogisticsReconciliation:
    def __init__(self):
        # Core data structures
        self.df_facturas = None
        self.df_manifiesto = None
        self.guides_facturadas = []
        self.guides_anuladas = []
        self.guides_sobrantes = []

        # KPI results
        self.kpis = {
            'total_facturadas': 0,
            'total_anuladas': 0,
            'total_sobrantes': 0,
            'total_value': 0.0,
            'value_facturadas': 0.0,
            'value_anuladas': 0.0,
            'value_sobrantes': 0.0,
            'top_cities': pd.Series(dtype="object"),
            'top_stores': pd.Series(dtype="object"),
            'spending_by_city': pd.Series(dtype="float"),
            'spending_by_store': pd.Series(dtype="float"),
            'avg_shipment_value': 0.0,
            'shipment_volume': pd.Series(dtype="int"),
            'anuladas_by_destinatario': pd.Series(dtype="object")
        }

    # ===========================================================
    # Identificación de columnas clave
    # ===========================================================
    def identify_guide_column(self, df):
        for col in df.columns:
            extracted = df[col].astype(str).str.extract(r'(LC\d+)', expand=False)
            if extracted.notna().mean() > 0.3:  # Adjusted threshold to 30% to be more flexible
                return col
        return None

    def identify_destination_city_column(self, df):
        ecuador_cities = [
            'GUAYAQUIL', 'QUITO', 'IBARRA', 'CUENCA', 'MACHALA',
            'SANGOLQUI', 'LATACUNGA', 'AMBATO', 'PORTOVIEJO',
            'MILAGRO', 'LOJA', 'RIOBAMBA', 'ESMERALDAS', 'LAGO AGRIO'
        ]
        for col in df.columns:
            upper_col = df[col].astype(str).str.upper()
            if upper_col.isin(ecuador_cities).mean() > 0.3:
                return col
        return None

    def identify_store_column(self, df):
        store_keywords = ['AEROPOSTALE', 'LOCAL', 'SHOPPING', 'MALL', 'CENTRO COMERCIAL']
        regex = '|'.join(store_keywords)
        for col in df.columns:
            if df[col].astype(str).str.upper().str.contains(regex).mean() > 0.4:
                return col
        return None

    def identify_monetary_column(self, df):
        for col in df.columns:
            try:
                numeric_vals = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')  # Handle commas
                if numeric_vals.notna().mean() > 0.7 and (numeric_vals > 0).mean() > 0.5:
                    return col
            except Exception:
                continue
        return None

    def identify_date_column(self, df):
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}'   # DD-MM-YYYY
        ]
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

    # ===========================================================
    # Procesamiento de archivos
    # =========================...(truncated 63942 characters)...='error-box animate-fade-in'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)

    # Función corregida para exportar a Excel
    def to_excel_bytes(self):
        """Genera un archivo Excel en bytes con los datos de reconciliación."""
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Hoja de KPIs
                kpi_data = {
                    'KPI': list(self.kpis.keys()),
                    'Valor': list(self.kpis.values())
                }
                kpi_df = pd.DataFrame(kpi_data)
                kpi_df.to_excel(writer, sheet_name='KPIs', index=False)

                # Hoja de Guías Facturadas
                pd.DataFrame({'Guías Facturadas': self.guides_facturadas}).to_excel(writer, sheet_name='Facturadas', index=False)

                # Hoja de Guías Anuladas
                pd.DataFrame({'Guías Anuladas': self.guides_anuladas}).to_excel(writer, sheet_name='Anuladas', index=False)

                # Hoja de Guías Sobrantes
                pd.DataFrame({'Guías Sobrantes': self.guides_sobrantes}).to_excel(writer, sheet_name='Sobrantes', index=False)

                # Otras hojas para series en KPIs (ejemplo para top_cities, etc.)
                for key, value in self.kpis.items():
                    if isinstance(value, pd.Series) and not value.empty:
                        value.to_frame(name=key).to_excel(writer, sheet_name=key.replace('_', ' ').title())

            output.seek(0)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Error al generar Excel: {e}", exc_info=True)
            return b""

    # Función corregida para generar reporte PDF
    def generate_report(self):
        """Genera un reporte PDF con los datos de reconciliación usando reportlab."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Título
            story.append(Paragraph("Reporte de Reconciliación Logística", styles['Title']))
            story.append(Spacer(1, 12))

            # KPIs principales
            story.append(Paragraph("Métricas Principales:", styles['Heading2']))
            for key, value in self.kpis.items():
                if not isinstance(value, pd.Series):
                    story.append(Paragraph(f"{key.replace('_', ' ').title()}: {value}", styles['Normal']))
            story.append(Spacer(1, 12))

            # Listas de guías
            story.append(Paragraph("Guías Facturadas:", styles['Heading2']))
            story.append(Paragraph(", ".join(self.guides_facturadas), styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Guías Anuladas:", styles['Heading2']))
            story.append(Paragraph(", ".join(self.guides_anuladas), styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Guías Sobrantes:", styles['Heading2']))
            story.append(Paragraph(", ".join(self.guides_sobrantes), styles['Normal']))
            story.append(Spacer(1, 12))

            # Otras series (ejemplo)
            for key, value in self.kpis.items():
                if isinstance(value, pd.Series) and not value.empty:
                    story.append(Paragraph(f"{key.replace('_', ' ').title()}:", styles['Heading2']))
                    for idx, val in value.items():
                        story.append(Paragraph(f"{idx}: {val}", styles['Normal']))

            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"Error al generar PDF: {e}", exc_info=True)
            return BytesIO(b"")

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
def mostrar_reconciliacion():
    """Muestra la interfaz completa de reconciliación con todas las funcionalidades de guiast.py"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Reconciliación Logística Completa</h1>", unsafe_allow_html=True)
    
    if 'reconciler' not in st.session_state:
        st.session_state.reconciler = StreamlitLogisticsReconciliation()
        st.session_state.processed = False
        st.session_state.show_details = False

    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Cargar Archivos</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        factura_file = st.file_uploader("Factura (Excel)", type=['xlsx','xls'], key="rec_factura")
    with col2:
        manifiesto_file = st.file_uploader("Manifiesto (Excel)", type=['xlsx','xls'], key="rec_manifiesto")

    process_btn = st.button("🚀 Procesar Archivos", use_container_width=True)

    if process_btn and factura_file and manifiesto_file:
        with st.spinner("Procesando archivos..."):
            st.session_state.processed = st.session_state.reconciler.process_files(factura_file, manifiesto_file)

    if st.session_state.processed:
        reconciler = st.session_state.reconciler
        kpis = reconciler.kpis

        st.markdown("<div class='success-box animate-fade-in'>✅ Procesamiento completado</div>", unsafe_allow_html=True)
        
        st.markdown("<h2 class='section-title animate-fade-in'>📊 Métricas Principales</h2>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Total Facturadas</div>
                <p class="metric-value">{kpis['total_facturadas']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Total Anuladas</div>
                <p class="metric-value">{kpis['total_anuladas']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Total Sobrantes</div>
                <p class="metric-value">{kpis['total_sobrantes']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            valor_promedio = f"${kpis['avg_shipment_value']:.2f}" if kpis['avg_shipment_value'] else "N/A"
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Valor Promedio</div>
                <p class="metric-value">{valor_promedio}</p>
            </div>
            """, unsafe_allow_html=True)

        # Métricas de valor
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Valor Total</div>
                <p class="metric-value">${kpis['total_value']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col6:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Valor Facturadas</div>
                <p class="metric-value">${kpis['value_facturadas']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col7:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Valor Anuladas</div>
                <p class="metric-value">${kpis['value_anuladas']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col8:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Valor Sobrantes</div>
                <p class="metric-value">${kpis['value_sobrantes']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

        # Gráficos y análisis detallados
        st.markdown("<h2 class='section-title animate-fade-in'>📈 Análisis Detallado</h2>", unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Top Ciudades", "Top Tiendas", "Gasto por Ciudad", "Gasto por Tienda", "Anuladas por Destinatario"])
        
        with tab1:
            if not kpis['top_cities'].empty:
                fig = px.bar(
                    x=kpis['top_cities'].index, 
                    y=kpis['top_cities'].values,
                    title="Top Ciudades por Volumen de Envíos",
                    labels={'x': 'Ciudad', 'y': 'Cantidad'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para top cities")
        
        with tab2:
            if not kpis['top_stores'].empty:
                fig = px.bar(
                    x=kpis['top_stores'].index, 
                    y=kpis['top_stores'].values,
                    title="Top Tiendas por Volumen de Envíos",
                    labels={'x': 'Tienda', 'y': 'Cantidad'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para top stores")
        
        with tab3:
            if not kpis['spending_by_city'].empty:
                fig = px.bar(
                    x=kpis['spending_by_city'].index, 
                    y=kpis['spending_by_city'].values,
                    title="Gasto por Ciudad",
                    labels={'x': 'Ciudad', 'y': 'Valor ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para gasto por ciudad")
        
        with tab4:
            if not kpis['spending_by_store'].empty:
                fig = px.bar(
                    x=kpis['spending_by_store'].index, 
                    y=kpis['spending_by_store'].values,
                    title="Gasto por Tienda",
                    labels={'x': 'Tienda', 'y': 'Valor ($)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para gasto por tienda")
        
        with tab5:
            if not kpis['anuladas_by_destinatario'].empty:
                fig = px.bar(
                    x=kpis['anuladas_by_destinatario'].index, 
                    y=kpis['anuladas_by_destinatario'].values,
                    title="Anuladas por Destinatario",
                    labels={'x': 'Destinatario', 'y': 'Cantidad'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles para anuladas por destinatario")

        # Volumen de envíos por mes
        if not kpis['shipment_volume'].empty:
            st.markdown("<h3 class='section-title animate-fade-in'>Volumen de Envíos por Mes</h3>", unsafe_allow_html=True)
            fig = px.bar(
                x=kpis['shipment_volume'].index.astype(str), 
                y=kpis['shipment_volume'].values,
                title="Volumen de Envíos por Mes",
                labels={'x': 'Mes', 'y': 'Cantidad'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Detalles de guías
        st.markdown("<h3 class='section-title animate-fade-in'>Detalles de Guías</h3>", unsafe_allow_html=True)
        
        if st.button("👁️ Mostrar/Ocultar Detalles de Guías"):
            st.session_state.show_details = not st.session_state.show_details

        if st.session_state.show_details:
            with st.expander("Guías Facturadas"):
                st.write(", ".join(reconciler.guides_facturadas))
            
            with st.expander("Guías Anuladas (Facturadas pero no en Manifiesto)"):
                st.write(", ".join(reconciler.guides_anuladas))
            
            with st.expander("Guías Sobrantes (No Facturadas, en Manifiesto pero no en Facturas)"):
                st.write(", ".join(reconciler.guides_sobrantes))

        # Descargar reporte
        st.markdown("<h3 class='section-title animate-fade-in'>Exportar Reporte</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            # Exportar a Excel
            excel_data = reconciler.to_excel_bytes()
            st.download_button(
                label="💾 Descargar Excel",
                data=excel_data,
                file_name="reconciliacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # Exportar a PDF
            pdf_buffer = reconciler.generate_report()
            st.download_button(
                label="📄 Descargar PDF",
                data=pdf_buffer,
                file_name="logistics_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    st.markdown("</div>", unsafe_allow_html=True)
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

# ================================
# FUNCIÓN PRINCIPAL
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
        ("Reconciliación", "🔁", mostrar_reconciliacion, "admin"),
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
