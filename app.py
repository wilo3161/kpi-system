import streamlit as st
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
from typing import Dict, List, Optional, Tuple, Any, Union
import requests
from io import BytesIO
from PIL import Image as PILImage
import os

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
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS profesional mejorado (sin cambios)
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
    background: linear-gradient(145deg, #1e1e1e, #161616);
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
    background: #1e1e1e;
    border-radius: 12px;
    padding: 16px;
    margin: 10px 0;
    border: 1px solid rgba(230, 0, 18, 0.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: var(--transition);
}

.worker-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.worker-header {
    font-weight: bold;
    color: var(--text-color);
    margin-bottom: 6px;
    font-size: 1.1em;
}

.worker-metric {
    color: var(--text-secondary);
    font-size: 0.95em;
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

def obtener_datos_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene los datos de una fecha específica desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        
        # Verificar si hay datos en la respuesta
        if response and response.data:
            df = pd.DataFrame(response.data)
            return df
        else:
            logger.info(f"No se encontraron datos para la fecha {fecha}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos de fecha {fecha} de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# Nuevas funciones para distribuciones y dependencias
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
        
        if response and response.data:
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
        if not all([
            validar_fecha(semana),
            validar_distribuciones(tempo_distribuciones),
            validar_distribuciones(luis_distribuciones),
            validar_distribuciones(meta_semanal)
        ]):
            logger.error("Datos de distribuciones inválidos")
            return False
            
        # Verificar si ya existe registro para esta semana
        response = supabase.from_('distribuciones_semanales').select('*').eq('semana', semana).execute()
        
        if response and response.data:
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
        if response and response.data:
            logger.info(f"Distribuciones semanales guardadas correctamente para la semana {semana}")
            return True
        else:
            logger.error("No se pudieron guardar las distribuciones semanales")
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
        if response and response.data:
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

def get_logo_url(brand: str) -> Optional[str]:
    """Obtiene la URL del logo de una marca desde Supabase."""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado en get_logo_url")
        return None
    try:
        # Asumiendo una tabla 'guide_logos' con 'brand' y 'logo_url'
        response = supabase.from_('guide_logos').select('logo_url').eq('brand', brand).execute()
        if response and response.data:
            return response.data[0].get('logo_url')
        else:
            logger.warning(f"No se encontró URL de logo para la marca: {brand}")
            return None
    except Exception as e:
        logger.error(f"Error al obtener logo de Supabase para {brand}: {e}", exc_info=True)
        return None

def generar_pdf_guia(
    store_name: str,
    brand: str,
    url: str,
    sender_name: str,
    sender_address: str,
    sender_phone: str,
    tracking_number: str
) -> bytes:
    """Genera un PDF de la guía de envío con diseño mejorado y logos desde Supabase."""
    try:
        # Crear un PDF en memoria
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=False, margin=20)
        pdf.set_font("Arial", "", 10)

        # === 1. REMITENTE (arriba a la izquierda) ===
        pdf.set_xy(10, 10)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Remitente:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(10, 16)
        pdf.cell(0, 6, f"{sender_name}", ln=True)
        pdf.set_xy(10, 22)
        pdf.multi_cell(80, 6, sender_address)
        pdf.set_xy(10, pdf.get_y() + 2)
        pdf.cell(0, 6, f"Tel: {sender_phone}")

        # === 2. DESTINATARIO (arriba a la derecha) ===
        pdf.set_xy(100, 10)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "Destinatario:", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(100, 16)
        pdf.cell(0, 6, f"{store_name}", ln=True)
        pdf.set_xy(100, 22)
        pdf.multi_cell(90, 6, "Dirección del destinatario no disponible")

        # Guardar la posición actual del Y después del destinatario
        y_after_destinatario = pdf.get_y()
        
        # === 3. LOGO DE LA MARCA (debajo del remitente) ===
        logo_url = get_logo_url(brand)
        if logo_url:
            try:
                response = requests.get(logo_url)
                response.raise_for_status()
                # Usar BytesIO para pasar la imagen en memoria a FPDF
                pdf.image(BytesIO(response.content), x=10, y=pdf.get_y() + 5, w=50)
                logo_height = 20
            except Exception as e:
                logger.warning(f"No se pudo cargar el logo desde {logo_url}: {e}")
                pdf.set_xy(10, pdf.get_y() + 5)
                pdf.cell(0, 10, f"[Logo {brand}]")
                logo_height = 10
        else:
            pdf.set_xy(10, pdf.get_y() + 5)
            pdf.cell(0, 10, "[Sin logo]")
            logo_height = 10

        # === 4. CÓDIGO QR y NÚMERO DE SEGUIMIENTO (debajo del destinatario) ===
        # Generar QR
        qr_img = generar_qr_imagen(url)
        qr_stream = BytesIO()
        qr_img.save(qr_stream, format='PNG')
        qr_stream.seek(0)
        
        # Posicionar QR a la derecha, debajo del destinatario
        qr_x = 100
        qr_y = y_after_destinatario + 10
        pdf.image(qr_stream, x=qr_x, y=qr_y, w=40, h=40, type='PNG')

        # === 5. NÚMERO DE SEGUIMIENTO debajo del QR ===
        pdf.set_xy(qr_x, qr_y + 45)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Guía: {tracking_number}")

        # === 6. URL del pedido (opcional, abajo) ===
        pdf.set_xy(10, pdf.get_y() + 10)
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(0, 0, 255) # Azul
        pdf.set_link(pdf.add_link(), url)
        pdf.multi_cell(0, 5, "URL del pedido: " + url, align='L', border=0)

        # Retornar el PDF en bytes
        return pdf.output(dest='S').encode('latin1')

    except Exception as e:
        logger.error(f"Error al generar el PDF: {e}", exc_info=True)
        return b""

# ================================
# Vistas y lógica de la aplicación Streamlit
# ================================

def verificar_password() -> bool:
    """Verifica si la contraseña es correcta."""
    if 'password_correcta' not in st.session_state:
        st.session_state.password_correcta = False
    return st.session_state.password_correcta

def solicitar_autenticacion():
    """Muestra el formulario de autenticación."""
    with st.container():
        st.markdown(
            f'<div class="password-container">',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="logo-container"><span class="aeropostale-logo">AEROPOSTALE</span></div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<h1 class="password-title">Acceso Restringido</h1>',
            unsafe_allow_html=True
        )
        
        with st.form("password_form"):
            password = st.text_input("Ingrese la contraseña:", type="password", help="Contraseña única de administrador")
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("Ingresar", use_container_width=True)
            with col2:
                if st.button("Cancelar", use_container_width=True):
                    st.stop()
            
            if submitted:
                if hash_password(password) == hash_password(ADMIN_PASSWORD):
                    st.session_state.password_correcta = True
                    st.experimental_rerun()
                else:
                    st.error("Contraseña incorrecta. Por favor, intente de nuevo.")
        
        st.markdown(
            f'</div>',
            unsafe_allow_html=True
        )

def mostrar_dashboard():
    """Muestra el Dashboard de KPIs."""
    st.title("📊 Dashboard de KPIs")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        df = cargar_historico_db()
        if df.empty:
            st.warning("No hay datos para mostrar en el dashboard.")
            return

        df_hoy = obtener_datos_fecha(datetime.now().strftime("%Y-%m-%d"))

        # Cálculos de hoy
        transferencias_hoy = df_hoy[df_hoy['actividad'] == 'Transferencias']['cantidad'].sum()
        arreglos_hoy = df_hoy[df_hoy['actividad'] == 'Arreglos']['cantidad'].sum()
        distribuciones_hoy = df_hoy[df_hoy['actividad'] == 'Distribución']['cantidad'].sum()
        guias_hoy = df_hoy[df_hoy['actividad'] == 'Guías']['cantidad'].sum()
        
        # Cálculos de KPI
        kpi_trans_hoy = kpi_transferencias(transferencias_hoy)
        kpi_arr_hoy = kpi_arreglos(arreglos_hoy)
        kpi_dist_hoy = kpi_distribucion(distribuciones_hoy)
        kpi_guias_hoy = kpi_guias(guias_hoy)

        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Transferencias Hoy</div>
                <div class="metric-value">{transferencias_hoy:,.0f}</div>
                <div class="trend-up">{kpi_trans_hoy:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Arreglos Hoy</div>
                <div class="metric-value">{arreglos_hoy:,.0f}</div>
                <div class="trend-up">{kpi_arr_hoy:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Distribuciones Hoy</div>
                <div class="metric-value">{distribuciones_hoy:,.0f}</div>
                <div class="trend-up">{kpi_dist_hoy:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="metric-label">Guías Hoy</div>
                <div class="metric-value">{guias_hoy:,.0f}</div>
                <div class="trend-up">{kpi_guias_hoy:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Tendencia Semanal")
        
        df['semana'] = df['fecha'].dt.strftime('%Y-%W')
        semana_actual = datetime.now().strftime('%Y-%W')
        df_semanal = df.groupby('semana').agg(
            transferencias=('cantidad', lambda x: x[df.loc[x.index, 'actividad'] == 'Transferencias'].sum()),
            arreglos=('cantidad', lambda x: x[df.loc[x.index, 'actividad'] == 'Arreglos'].sum()),
            distribuciones=('cantidad', lambda x: x[df.loc[x.index, 'actividad'] == 'Distribución'].sum()),
            guias=('cantidad', lambda x: x[df.loc[x.index, 'actividad'] == 'Guías'].sum())
        ).reset_index()
        
        # Obtener los últimos 4 registros de la semana
        df_semanal = df_semanal.tail(4)
        
        # Gráficos de tendencias
        st.plotly_chart(crear_grafico_interactivo(df_semanal, 'semana', 'transferencias', 'Transferencias Semanales', 'Semana', 'Cantidad', tipo='line'), use_container_width=True)
        st.plotly_chart(crear_grafico_interactivo(df_semanal, 'semana', 'arreglos', 'Arreglos Semanales', 'Semana', 'Cantidad', tipo='line'), use_container_width=True)
        st.plotly_chart(crear_grafico_interactivo(df_semanal, 'semana', 'distribuciones', 'Distribuciones Semanales', 'Semana', 'Cantidad', tipo='line'), use_container_width=True)
        st.plotly_chart(crear_grafico_interactivo(df_semanal, 'semana', 'guias', 'Guías Semanales', 'Semana', 'Cantidad', tipo='line'), use_container_width=True)

    except Exception as e:
        logger.error(f"Error al mostrar dashboard: {e}", exc_info=True)
        st.error("Error al cargar los datos del dashboard. Verifique la conexión a la base de datos.")

def mostrar_ingreso_datos():
    """Muestra la sección para el ingreso de datos diarios de KPIs."""
    st.title("➕ Ingreso de Datos Diarios")
    st.markdown("---")
    
    trabajadores = obtener_trabajadores()
    equipos = obtener_equipos()
    
    if trabajadores.empty or not equipos:
        st.error("No se pudieron cargar los datos de trabajadores o equipos.")
        return

    with st.form(key="daily_kpis_form"):
        st.markdown("### Seleccione la fecha y el equipo")
        
        fecha = st.date_input(
            "Fecha",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        ).strftime("%Y-%m-%d")

        equipo_seleccionado = st.selectbox(
            "Seleccione el equipo",
            options=equipos
        )
        
        st.markdown("---")
        
        st.markdown("### Ingrese los datos de cada trabajador")
        
        datos_equipo = {}
        trabajadores_equipo = trabajadores[trabajadores['equipo'] == equipo_seleccionado]

        if trabajadores_equipo.empty:
            st.warning("No hay trabajadores en este equipo.")
        else:
            for _, row in trabajadores_equipo.iterrows():
                nombre = row['nombre']
                st.subheader(f"{nombre}")
                
                col1, col2 = st.columns(2)
                with col1:
                    cantidad = st.number_input(f"Cantidad", key=f"{nombre}_cantidad", min_value=0, step=1)
                with col2:
                    horas = st.number_input(f"Horas de trabajo", key=f"{nombre}_horas", min_value=0.0, step=0.5)

                comentario = st.text_area(f"Comentario (opcional)", key=f"{nombre}_comentario")

                # Valores de meta por defecto
                meta_kpi = 0
                meta_mensual = 0
                if equipo_seleccionado == "Transferencias":
                    meta_kpi = 1750
                    meta_mensual = 35000
                elif equipo_seleccionado == "Arreglo":
                    meta_kpi = 150
                    meta_mensual = 3000
                elif equipo_seleccionado == "Guías":
                    meta_kpi = 120
                    meta_mensual = 2400
                elif equipo_seleccionado == "Distribución":
                    meta_kpi = 1000
                    meta_mensual = 20000

                # Calcular métricas
                eficiencia = calcular_kpi(cantidad, meta_kpi)
                productividad = productividad_hora(cantidad, horas)
                
                datos_equipo[nombre] = {
                    "cantidad": cantidad,
                    "meta": meta_kpi,
                    "eficiencia": eficiencia,
                    "productividad": productividad,
                    "comentario": comentario,
                    "meta_mensual": meta_mensual,
                    "horas_trabajo": horas,
                    "actividad": equipo_seleccionado,
                    "equipo": equipo_seleccionado
                }
                
                st.info(f"**Eficiencia**: {eficiencia:.1f}% | **Productividad**: {productividad:.1f} unidades/hora")
                st.markdown("---")

        submitted = st.form_submit_button("Guardar Datos")

    if submitted:
        if not datos_equipo:
            st.error("Por favor, ingrese datos para al menos un trabajador.")
            return

        with st.spinner("Guardando datos en la base de datos..."):
            if guardar_datos_db(fecha, datos_equipo):
                st.success("🎉 ¡Datos guardados correctamente!")
            else:
                st.error("Hubo un error al guardar los datos.")

def mostrar_historial_kpis():
    """Muestra la sección del historial de KPIs."""
    st.title("🔍 Historial de KPIs")
    st.markdown("---")
    
    with st.container():
        st.subheader("Filtros de Búsqueda")
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=7)).strftime("%Y-%m-%d")
        with col2:
            fecha_fin = st.date_input("Fecha de fin", value=datetime.now().date()).strftime("%Y-%m-%d")
        with col3:
            trabajadores = obtener_trabajadores()
            nombres_trabajadores = ["Todos"] + list(trabajadores['nombre'])
            trabajador_seleccionado = st.selectbox("Trabajador", options=nombres_trabajadores)
    
    if st.button("Buscar"):
        with st.spinner("Cargando datos..."):
            trabajador_filtro = trabajador_seleccionado if trabajador_seleccionado != "Todos" else None
            df_historico = cargar_historico_db(fecha_inicio, fecha_fin, trabajador_filtro)
            
            if not df_historico.empty:
                st.markdown("---")
                st.subheader("Resultados de la Búsqueda")
                st.dataframe(df_historico)
                
                # Gráficos de tendencias
                st.markdown("### Gráficos de Tendencia Individual")
                
                # Gráfico de cantidad vs fecha
                fig = px.line(
                    df_historico, 
                    x='fecha', 
                    y='cantidad', 
                    title='Cantidad vs Fecha', 
                    labels={'fecha': 'Fecha', 'cantidad': 'Cantidad'},
                    color='actividad'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Gráfico de eficiencia vs fecha
                fig_eficiencia = px.line(
                    df_historico, 
                    x='fecha', 
                    y='eficiencia', 
                    title='Eficiencia vs Fecha', 
                    labels={'fecha': 'Fecha', 'eficiencia': 'Eficiencia (%)'},
                    color='actividad'
                )
                st.plotly_chart(fig_eficiencia, use_container_width=True)
                
            else:
                st.warning("No se encontraron datos para los filtros seleccionados.")

def mostrar_gestion_distribuciones():
    """Muestra la sección de Gestión de Distribuciones."""
    st.title("📦 Gestión de Distribuciones")
    st.markdown("---")

    # Obtener fecha de inicio de semana
    hoy = datetime.now().date()
    fecha_inicio_semana = hoy - timedelta(days=hoy.weekday())
    semana_str = fecha_inicio_semana.strftime("%Y-%m-%d")

    st.info(f"Semana actual: {semana_str} a {(fecha_inicio_semana + timedelta(days=6)).strftime('%Y-%m-%d')}")

    # Obtener datos actuales de la semana
    distribuciones_actuales = obtener_distribuciones_semana(semana_str)
    tempo_actual = distribuciones_actuales.get('tempo', 0)
    luis_actual = distribuciones_actuales.get('luis', 0)

    with st.form(key="gestion_distribuciones_form"):
        st.markdown("### Actualizar distribuciones semanales")
        
        col1, col2 = st.columns(2)
        with col1:
            tempo_distribuciones = st.number_input(
                "Distribuciones de Tempo", 
                value=tempo_actual, 
                min_value=0, 
                step=10,
                key="tempo_input"
            )
        with col2:
            luis_distribuciones = st.number_input(
                "Distribuciones de Luis Perugachi", 
                value=luis_actual, 
                min_value=0, 
                step=10,
                key="luis_input"
            )

        submit_button = st.form_submit_button(
            "Guardar Distribuciones", 
            use_container_width=True,
            help="Guarda las distribuciones para la semana actual."
        )

    if submit_button:
        with st.spinner("Guardando distribuciones..."):
            if guardar_distribuciones_semanales(semana_str, tempo_distribuciones, luis_distribuciones):
                st.success("🎉 ¡Distribuciones guardadas correctamente!")
                st.experimental_rerun()
            else:
                st.error("Hubo un error al guardar las distribuciones. Por favor, intente de nuevo.")

    st.markdown("---")
    st.subheader("Estado Semanal de Distribuciones")

    resultado_semana = calcular_metas_semanales()

    col_total, col_meta = st.columns(2)
    with col_total:
        st.metric(
            label="Total de Distribuciones (semanal)",
            value=f"{resultado_semana['distribuciones_totales']:,}"
        )
    with col_meta:
        st.metric(
            label="Meta Semanal",
            value=f"{resultado_semana['meta_semanal']:,}"
        )
    
    st.plotly_chart(
        crear_grafico_frasco(
            resultado_semana['cumplimiento_porcentaje'], 
            "Progreso Semanal"
        ), 
        use_container_width=True
    )
    
    # Mostrar alertas si hay
    alertas = verificar_alertas_abastecimiento()
    if alertas:
        st.markdown(
            f'<div class="warning-box"><h3>🚨 Alertas de Abastecimiento</h3></div>', 
            unsafe_allow_html=True
        )
        for alerta in alertas:
            st.warning(f"**{alerta['proveedor']}**: {alerta['mensaje']}. Acción: {alerta['accion']}")

def mostrar_generacion_guias():
    """Muestra la sección para generar guías de envío."""
    st.title("📋 Generar Guías")
    st.markdown("---")

    tiendas_df = obtener_tiendas()
    remitentes_df = obtener_remitentes()

    if tiendas_df.empty or remitentes_df.empty:
        st.error("No se pudo cargar la información de tiendas o remitentes. Verifique la base de datos.")
        return

    marcas = ["Aeropostale", "Aéropostale Kids", "P.S. Aéropostale"]

    with st.form(key="guia_form"):
        col1, col2 = st.columns(2)
        with col1:
            store_name = st.selectbox("Tienda Destino", options=tiendas_df['name'])
            brand = st.selectbox("Marca", options=marcas)
        with col2:
            sender_name = st.selectbox("Remitente", options=remitentes_df['name'])

        url = st.text_input("URL del Pedido", help="Pegue el enlace al pedido para el código QR.")
        
        submitted = st.form_submit_button("Generar Guía y PDF")

    if submitted:
        if not url:
            st.error("Por favor, ingrese la URL del pedido.")
        else:
            with st.spinner("Generando guía..."):
                try:
                    # Guardar la guía en la base de datos
                    if guardar_guia(store_name, brand, url, sender_name):
                        # Obtener los datos del remitente
                        remitente_info = remitentes_df[remitentes_df['name'] == sender_name].iloc[0]
                        sender_address = remitente_info['address']
                        sender_phone = remitente_info['phone']

                        # Simular un ID de registro para el número de seguimiento
                        latest_guide = obtener_historial_guias().iloc[0]
                        tracking_number = generar_numero_seguimiento(latest_guide['id'])

                        # Generar el PDF
                        pdf_bytes = generar_pdf_guia(
                            store_name,
                            brand,
                            url,
                            sender_name,
                            sender_address,
                            sender_phone,
                            tracking_number
                        )

                        if pdf_bytes:
                            st.success("🎉 ¡Guía generada exitosamente!")
                            st.download_button(
                                label="Descargar Guía PDF",
                                data=pdf_bytes,
                                file_name=f"guia_{store_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.error("Hubo un error al generar el PDF.")
                    else:
                        st.error("No se pudo guardar la guía en la base de datos. Vuelva a intentar.")
                except Exception as e:
                    logger.error(f"Error en el proceso de generación de guía: {e}", exc_info=True)
                    st.error("Ocurrió un error inesperado. Por favor, revise el log de errores.")


def mostrar_historial_guias():
    """Muestra el historial de guías generadas."""
    st.title("🔍 Historial de Guías")
    st.markdown("---")
    
    with st.spinner("Cargando historial de guías..."):
        df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.info("No se han generado guías aún.")
    else:
        st.dataframe(df_guias)


def mostrar_ayuda():
    """Muestra la sección de ayuda."""
    st.title("❓ Ayuda y Contacto")
    st.markdown("---")
    st.markdown("""
    Este es un sistema para el seguimiento de KPIs en Aeropostale.
    
    ### Secciones de la aplicación:
    - **Dashboard**: Muestra un resumen visual del desempeño de los equipos.
    - **Ingreso de Datos**: Permite ingresar los datos diarios de productividad de cada trabajador.
    - **Historial de KPIs**: Permite consultar y filtrar los datos históricos por fecha y trabajador.
    - **Gestión de Distribuciones**: Muestra las distribuciones semanales y su progreso.
    - **Generar Guías**: Crea y descarga guías de envío en formato PDF.
    - **Historial de Guías**: Muestra las guías de envío generadas previamente.
    
    Si necesitas ayuda adicional o reportar un problema, por favor contacta al equipo de desarrollo.
    
    **Contacto de Soporte:**
    - Correo: soporte@aeropostale.com
    - Teléfono: +593 999 123 456
    """)

# Función principal para la navegación
def main():
    """Función principal que controla la navegación de la aplicación."""
    # Menú de navegación
    menu_options = [
        ("Dashboard", "📊", mostrar_dashboard),
        ("Ingreso de Datos", "✍️", mostrar_ingreso_datos),
        ("Historial de KPIs", "📈", mostrar_historial_kpis),
        ("Gestión de Distribuciones", "📦", mostrar_gestion_distribuciones),
        ("Generar Guías", "📋", mostrar_generacion_guias),
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
    if st.session_state.selected_menu in [1, 2, 3, 4, 5]:  # Ingreso de Datos, Historial de KPIs, Gestión de Distribuciones, Generar Guías, Historial de Guías
        if not verificar_password():
            solicitar_autenticacion()
        else:
            func()
    else:
        func()
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
