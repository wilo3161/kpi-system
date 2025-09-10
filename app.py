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
import calendar
from dateutil.relativedelta import relativedelta


# ================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ================================

# Configuración de logging para registrar eventos y errores
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de Supabase con las credenciales proporcionadas
SUPABASE_URL = "https://nsgdyqoqzlcyyameccqn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zZ2R5cW9xemxjeXlhbWVjY3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMTA3MzksImV4cCI6MjA3MTU4NjczOX0.jA6sem9IMts6aPeYlMsldbtQaEaKAuQaQ1xf03TdWso"
ADMIN_PASSWORD = "Wilo3161"  # Contraseña única sensible a mayúsculas
GUIDE_USER_PASSWORD = "AeroGuide2024"  # Contraseña por defecto para usuarios de guías

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

.trend-neutral {
    color: var(--warning-color);
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

.alert-box {
    border-left-color: var(--warning-color);
    background: rgba(255, 152, 0, 0.15);
    color: #ffe0b2;
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(255, 152, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
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

/* Estilos para indicadores de tendencia */
.trend-indicator {
    display: inline-flex;
    align-items: center;
    font-size: 0.9em;
    padding: 4px 8px;
    border-radius: 12px;
    margin-left: 8px;
}

.trend-indicator.up {
    background-color: rgba(76, 175, 80, 0.2);
    color: var(--success-color);
}

.trend-indicator.down {
    background-color: rgba(244, 67, 54, 0.2);
    color: var(--error-color);
}

.trend-indicator.neutral {
    background-color: rgba(255, 152, 0, 0.2);
    color: var(--warning-color);
}

.variation-indicator {
    font-size: 0.85em;
    margin-top: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.variation-positive {
    color: var(--success-color);
}

.variation-negative {
    color: var(--error-color);
}

.variation-neutral {
    color: var(--warning-color);
}

/* Estilos para alertas tempranas */
.early-warning {
    border: 1px solid var(--warning-color);
    background: rgba(255, 152, 0, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    animation: pulse 2s infinite;
}

.early-warning-critical {
    border: 1px solid var(--error-color);
    background: rgba(244, 67, 54, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    animation: pulse 1s infinite;
}

.warning-icon {
    font-size: 1.5em;
    margin-right: 10px;
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

def obtener_dias_laborales_mes(ano: int, mes: int) -> int:
    """Calcula la cantidad de días laborales en un mes (excluye fines de semana)"""
    num_dias = calendar.monthrange(ano, mes)[1]
    dias_laborales = 0
    
    for dia in range(1, num_dias + 1):
        fecha = datetime(ano, mes, dia)
        # Lunes a Viernes (0=Lunes, 6=Domingo)
        if fecha.weekday() < 5:
            dias_laborales += 1
    
    return dias_laborales

def obtener_dias_laborales_hasta_hoy(ano: int, mes: int) -> int:
    """Calcula la cantidad de días laborales hasta la fecha actual en el mes"""
    hoy = datetime.now()
    dias_laborales = 0
    
    for dia in range(1, hoy.day + 1):
        try:
            fecha = datetime(ano, mes, dia)
            # Lunes a Viernes (0=Lunes, 6=Domingo)
            if fecha.weekday() < 5 and fecha <= hoy:
                dias_laborales += 1
        except ValueError:
            # Día inválido para el mes (por ejemplo, 31 en febrero)
            continue
    
    return dias_laborales

def calcular_variacion(valor_actual: float, valor_anterior: float) -> Tuple[float, str]:
    """Calcula la variación porcentual entre dos valores y determina la tendencia"""
    if valor_anterior == 0:
        return 0, "neutral"
    
    variacion = ((valor_actual - valor_anterior) / valor_anterior) * 100
    
    if variacion > 5:
        tendencia = "up"
    elif variacion < -5:
        tendencia = "down"
    else:
        tendencia = "neutral"
    
    return variacion, tendencia

def obtener_icono_tendencia(tendencia: str) -> str:
    """Devuelve el icono correspondiente a la tendencia"""
    if tendencia == "up":
        return "📈"
    elif tendencia == "down":
        return "📉"
    else:
        return "➡️"

# ================================
# SISTEMA DE AUTENTICACIÓN MEJORADO
# ================================

def verificar_password() -> bool:
    """Verifica si el usuario tiene permisos para realizar acciones críticas"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    return st.session_state.password_correct

def verificar_usuario_guia() -> bool:
    """Verifica si el usuario tiene permisos para el sistema de guías"""
    if 'guia_authenticated' not in st.session_state:
        st.session_state.guia_authenticated = False
    return st.session_state.guia_authenticated

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

def autenticar_usuario_guia():
    """Muestra un formulario de autenticación para usuarios de guías"""
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Guías</div>
        </div>
        <h2 class="password-title">🔐 Acceso Usuarios de Guías</h2>
        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 25px;">
            Ingrese la contraseña para acceder al sistema de guías
        </p>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña:", type="password", key="guia_password", 
                            placeholder="Ingrese la contraseña de guías", 
                            label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.button("Ingresar", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submitted:
        if password == GUIDE_USER_PASSWORD:
            st.session_state.guia_authenticated = True
            st.success("✅ Acceso concedido al sistema de guías")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

def mostrar_gestion_usuarios_guias():
    """Muestra la interfaz de gestión de usuarios de guías (solo admin)"""
    if not verificar_password():
        solicitar_autenticacion()
        return
        
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Usuarios de Guías</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    st.markdown("<h2 class='section-title animate-fade-in'>Configuración de Contraseña</h2>", unsafe_allow_html=True)
    
    nueva_password = st.text_input("Nueva contraseña para usuarios de guías:", 
                                  type="password", 
                                  value=GUIDE_USER_PASSWORD,
                                  key="nueva_password_guias")
    
    if st.button("Actualizar Contraseña", key="actualizar_password_guias"):
        # Aquí iría la lógica para guardar la nueva contraseña en una base de datos segura
        st.success("✅ Contraseña actualizada correctamente")
        time.sleep(1)
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

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

def calcular_meta_diaria_dinamica(meta_mensual: float, ano: int, mes: int) -> float:
    """Calcula la meta diaria dinámica basada en días laborales"""
    dias_laborales_totales = obtener_dias_laborales_mes(ano, mes)
    if dias_laborales_totales == 0:
        return 0
    return meta_mensual / dias_laborales_totales

def calcular_meta_acumulada_hasta_hoy(meta_mensual: float, ano: int, mes: int) -> float:
    """Calcula la meta acumulada hasta el día actual basada en días laborales"""
    dias_laborales_hasta_hoy = obtener_dias_laborales_hasta_hoy(ano, mes)
    dias_laborales_totales = obtener_dias_laborales_mes(ano, mes)
    
    if dias_laborales_totales == 0:
        return 0
    
    return (meta_mensual / dias_laborales_totales) * dias_laborales_hasta_hoy

def verificar_alertas_rendimiento(eficiencia: float, productividad: float, meta_diaria: float, cantidad_real: float) -> List[Dict]:
    """Verifica y genera alertas tempranas de rendimiento"""
    alertas = []
    
    # Alertas de eficiencia
    if eficiencia < 80:
        alertas.append({
            'tipo': 'EFICIENCIA_BAJA',
            'mensaje': f'Eficiencia por debajo del 80% ({eficiencia:.1f}%)',
            'gravedad': 'ALTA' if eficiencia < 70 else 'MEDIA'
        })
    elif eficiencia < 90:
        alertas.append({
            'tipo': 'EFICIENCIA_MODERADA',
            'mensaje': f'Eficiencia por debajo del 90% ({eficiencia:.1f}%)',
            'gravedad': 'MEDIA'
        })
    
    # Alertas de productividad
    productividad_esperada = meta_diaria / 8  # Asumiendo 8 horas de trabajo
    if productividad < productividad_esperada * 0.8:
        alertas.append({
            'tipo': 'PRODUCTIVIDAD_BAJA',
            'mensaje': f'Productividad por debajo del 80% de lo esperado ({productividad:.1f} vs {productividad_esperada:.1f}/hora)',
            'gravedad': 'ALTA' if productividad < productividad_esperada * 0.7 else 'MEDIA'
        })
    
    # Alertas de cumplimiento de meta diaria
    if cantidad_real < meta_diaria * 0.8:
        alertas.append({
            'tipo': 'META_DIARIA_BAJA',
            'mensaje': f'Producción por debajo del 80% de la meta diaria ({cantidad_real:.0f} vs {meta_diaria:.0f})',
            'gravedad': 'ALTA' if cantidad_real < meta_diaria * 0.7 else 'MEDIA'
        })
    
    return alertas

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

# ... (continuación del código anterior)

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
    
    # URLs públicas de Supabase Storage (sin token)
    branded_logos = {
        "fashion": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Fashion.jpg",
        "tempo": "https://nsgdyqoqzlcyyameccqn.supabase.co/storage/v1/object/public/images/Tempo.jpg",
    }
    
    if brand_lower in branded_logos:
        logo_url = branded_logos[brand_lower]
        if verificar_imagen_existe(logo_url):
            logger.info(f"Imagen encontrada para marca {brand}: {logo_url}")
            return logo_url
        else:
            logger.error(f"Imagen no encontrada en {logo_url}")
            return None
    else:
        logger.error(f"No se encontró ninguna imagen para la marca {brand}")
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
    """Genera un PDF con la guía de envío en el formato exacto de la imagen"""
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Configuración inicial
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(True, 15)
        
        # === ENCABEZADO: AEROPOSTALE ===
        pdf.set_font("Arial", "B", 40)
        pdf.cell(0, 15, "AEROPOSTALE", 0, 1, "C")
        pdf.line(10, 25, 200, 25)
        
        # === SECCIÓN REMITENTE ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "REMITENTE:", 0, 1)
        
        remitentes = obtener_remitentes()
        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
        
        pdf.set_font("Arial", "", 14)
        pdf.multi_cell(0, 8, f"{remitente_info['name']}\n{remitente_info['address']}")
        
        # Línea separadora
        y_after_remitente = pdf.get_y()
        pdf.line(10, y_after_remitente + 5, 200, y_after_remitente + 5)
        pdf.ln(10)
        
        # === SECCIÓN DESTINO ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "DESTINO:", 0, 1)
        
        pdf.set_font("Arial", "", 14)
        pdf.cell(0, 8, tracking_number, 0, 1)
        
        tiendas = obtener_tiendas()
        tienda_info = tiendas[tiendas['name'] == store_name].iloc[0]
        
        if 'address' in tienda_info:
            pdf.multi_cell(0, 8, tienda_info['address'])
        
        # Línea separadora
        y_after_destino = pdf.get_y()
        pdf.line(10, y_after_destino + 5, 200, y_after_destino + 5)
        pdf.ln(10)
        
        # === SECCIÓN RECEPTOR ===
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 12, store_name, 0, 1, "C")
        pdf.ln(5)
        
        # === LOGO E INFORMACIÓN ADICIONAL ===
        # Logo - intentar cargar desde Supabase
        logo_img = obtener_logo_imagen(brand)
        current_y = pdf.get_y()
        
        if logo_img:
            try:
                # Convertir a RGB si es necesario (para PNG con canal alpha)
                if logo_img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', logo_img.size, (255, 255, 255))
                    background.paste(logo_img, mask=logo_img.split()[-1])
                    logo_img = background
                
                # Guardar imagen temporalmente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    logo_img.save(temp_file.name, format='JPEG', quality=95)
                    temp_logo_path = temp_file.name
                
                # Insertar logo centrado
                pdf.image(temp_logo_path, x=80, y=current_y, w=50)
                os.unlink(temp_logo_path)
                
                # Ajustar la posición Y después del logo
                current_y += 55
                pdf.set_y(current_y)
                logger.info("Logo insertado correctamente en el PDF")
            except Exception as e:
                logger.error(f"Error al insertar el logo en el PDF: {e}")
                # Insertar texto alternativo
                pdf.set_font("Arial", "I", 12)
                pdf.cell(0, 10, f"[Logo de {brand}]", 0, 1, "C")
                current_y += 10
                pdf.set_y(current_y)
        else:
            # Insertar texto alternativo si no hay logo
            pdf.set_font("Arial", "I", 12)
            pdf.cell(0, 10, f"[Logo de {brand}]", 0, 1, "C")
            current_y += 10
            pdf.set_y(current_y)
        
        # Información de piezas y teléfono
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, "PIEZAS 1/1", 0, 1, "C")
        
        if 'phone' in tienda_info:
            pdf.cell(0, 8, f"TEL.: {tienda_info['phone']}", 0, 1, "C")
        
        # Código QR
        qr_img = generar_qr_imagen(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            qr_img.save(temp_file.name)
            temp_qr_path = temp_file.name
        
        # Posicionar el QR centrado
        qr_y = pdf.get_y() + 5
        pdf.image(temp_qr_path, x=80, y=qr_y, w=50)
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
# NUEVAS FUNCIONES PARA MOSTRAR ESTADO DE ABASTECIMIENTO
# ================================

# ... (continuación del código anterior)

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
# COMPONENTES DE LA APLICACIÓN CON MEJORAS IMPLEMENTADAS
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs mejorados"""
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
    
    # Calcular lunes y viernes de la semana actual por defecto
    hoy = datetime.now().date()
    lunes_semana = hoy - timedelta(days=hoy.weekday())
    viernes_semana = lunes_semana + timedelta(days=4)
    
    # Obtener fechas únicas y ordenarlas
    if not df.empty and 'fecha' in df.columns:
        # Convertir a fecha y eliminar duplicados
        fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
        if not fechas_disponibles:
            st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay fechas disponibles para mostrar.</div>", unsafe_allow_html=True)
            return
        
        st.markdown("<div class='date-selector animate-fade-in'>", unsafe_allow_html=True)
        st.markdown("<h3>Selecciona el rango de fechas a visualizar:</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input(
                "Fecha de inicio:",
                value=lunes_semana,
                min_value=fechas_disponibles[-1] if fechas_disponibles else lunes_semana,
                max_value=fechas_disponibles[0] if fechas_disponibles else viernes_semana
            )
        with col2:
            fecha_fin = st.date_input(
                "Fecha de fin:",
                value=viernes_semana,
                min_value=fechas_disponibles[-1] if fechas_disponibles else lunes_semana,
                max_value=fechas_disponibles[0] if fechas_disponibles else viernes_semana
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
    
    # ===========================================
    # NUEVO: CÁLCULO DE TENDENCIAS Y VARIACIONES
    # ===========================================
    
    # Obtener datos del período anterior para comparación
    dias_rango = (fecha_fin - fecha_inicio).days
    fecha_inicio_anterior = fecha_inicio - timedelta(days=dias_rango + 1)
    fecha_fin_anterior = fecha_inicio - timedelta(days=1)
    
    df_anterior = df[(df['fecha'].dt.date >= fecha_inicio_anterior) & (df['fecha'].dt.date <= fecha_fin_anterior)]
    
    # Cálculos globales período actual
    total_cantidad = df_rango['cantidad'].sum()
    total_meta = df_rango['meta'].sum()
    total_horas = df_rango['horas_trabajo'].sum()
    avg_eficiencia = (df_rango['eficiencia'] * df_rango['horas_trabajo']).sum() / total_horas if total_horas > 0 else 0
    avg_productividad = df_rango['productividad'].mean()
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0
    
    # Cálculos globales período anterior
    total_cantidad_anterior = df_anterior['cantidad'].sum() if not df_anterior.empty else 0
    total_meta_anterior = df_anterior['meta'].sum() if not df_anterior.empty else 0
    total_horas_anterior = df_anterior['horas_trabajo'].sum() if not df_anterior.empty else 0
    avg_eficiencia_anterior = (df_anterior['eficiencia'] * df_anterior['horas_trabajo']).sum() / total_horas_anterior if total_horas_anterior > 0 else 0
    avg_productividad_anterior = df_anterior['productividad'].mean() if not df_anterior.empty else 0
    
    # Calcular variaciones
    variacion_cantidad, tendencia_cantidad = calcular_variacion(total_cantidad, total_cantidad_anterior)
    variacion_eficiencia, tendencia_eficiencia = calcular_variacion(avg_eficiencia, avg_eficiencia_anterior)
    variacion_productividad, tendencia_productividad = calcular_variacion(avg_productividad, avg_productividad_anterior)
    
    # Mostrar KPIs con tendencias
    st.markdown("<h2 class='section-title animate-fade-in'>📈 KPIs Globales con Tendencias</h2>", unsafe_allow_html=True)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        cumplimiento_meta = (total_cantidad / total_meta * 100) if total_meta > 0 else 0
        icono_tendencia = obtener_icono_tendencia(tendencia_cantidad)
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">✅ Total Producción {icono_tendencia}</div>
            <p class="metric-value">{total_cantidad:,.0f}</p>
            <p>Meta: {total_meta:,.0f} | <span class="{'trend-up' if cumplimiento_meta >= 100 else 'trend-down'}">{cumplimiento_meta:.1f}%</span></p>
            <div class="variation-indicator {'variation-positive' if variacion_cantidad > 0 else 'variation-negative' if variacion_cantidad < 0 else 'variation-neutral'}">
                {f'+{variacion_cantidad:.1f}%' if variacion_cantidad > 0 else f'{variacion_cantidad:.1f}%'} vs período anterior
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        icono_tendencia = obtener_icono_tendencia(tendencia_eficiencia)
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">🎯 Eficiencia Promedio {icono_tendencia}</div>
            <p class="metric-value">{avg_eficiencia:.1f}%</p>
            <p>Meta: 100% | <span class="{'trend-up' if avg_eficiencia >= 100 else 'trend-down'}">{avg_eficiencia - 100:.1f}%</span></p>
            <div class="variation-indicator {'variation-positive' if variacion_eficiencia > 0 else 'variation-negative' if variacion_eficiencia < 0 else 'variation-neutral'}">
                {f'+{variacion_eficiencia:.1f}%' if variacion_eficiencia > 0 else f'{variacion_eficiencia:.1f}%'} vs período anterior
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        icono_tendencia = obtener_icono_tendencia(tendencia_productividad)
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">⚡ Productividad Promedio {icono_tendencia}</div>
            <p class="metric-value">{avg_productividad:.1f}</p>
            <p>unidades/hora</p>
            <div class="variation-indicator {'variation-positive' if variacion_productividad > 0 else 'variation-negative' if variacion_productividad < 0 else 'variation-neutral'}">
                {f'+{variacion_productividad:.1f}%' if variacion_productividad > 0 else f'{variacion_productividad:.1f}%'} vs período anterior
            </div>
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
    
    # ===========================================
    # NUEVO: METAS MENSUALES DINÁMICAS
    # ===========================================
    
    # Obtener el mes y año del rango de fechas seleccionado
    selected_month = fecha_inicio.month
    selected_year = fecha_inicio.year
    
    # Filtrar datos del mes seleccionado para transferencias
    df_month = df[(df['fecha'].dt.month == selected_month) & 
                  (df['fecha'].dt.year == selected_year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    # Obtener meta mensual de transferencias
    if not df_transferencias_month.empty:
        meta_mensual_transferencias = df_transferencias_month['meta_mensual'].iloc[0]
    else:
        # Si no hay datos, usar un valor por defecto basado en días laborales
        dias_laborales_mes = obtener_dias_laborales_mes(selected_year, selected_month)
        meta_mensual_transferencias = 1750 * dias_laborales_mes  # Meta diaria promedio * días laborales
    
    # Calcular meta acumulada hasta hoy basada en días laborales
    meta_acumulada_hasta_hoy = calcular_meta_acumulada_hasta_hoy(meta_mensual_transferencias, selected_year, selected_month)
    cum_transferencias = df_transferencias_month['cantidad'].sum() if not df_transferencias_month.empty else 0
    cumplimiento_transferencias = (cum_transferencias / meta_acumulada_hasta_hoy * 100) if meta_acumulada_hasta_hoy > 0 else 0
    
    # Mostrar el mes que se está visualizando
    nombre_mes = fecha_inicio.strftime('%B')
    st.markdown(f"<h2 class='section-title animate-fade-in'>📅 Cumplimiento de Metas Mensuales - {nombre_mes} {selected_year}</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        dias_laborales_hasta_hoy = obtener_dias_laborales_hasta_hoy(selected_year, selected_month)
        dias_laborales_totales = obtener_dias_laborales_mes(selected_year, selected_month)
        
        st.markdown(f"""
        <div class="kpi-card animate-fade-in">
            <div class="metric-label">Meta Mensual Transferencias</div>
            <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
            <p>Acumulado: {cum_transferencias:,.0f} / Meta Acumulada: {meta_acumulada_hasta_hoy:,.0f}</p>
            <p>Días laborales: {dias_laborales_hasta_hoy}/{dias_laborales_totales}</p>
            <p>Meta mensual total: {meta_mensual_transferencias:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Gráfico de frasco de agua para el cumplimiento
        fig = crear_grafico_frasco(cumplimiento_transferencias, f"Cumplimiento Mensual {nombre_mes}")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # ===========================================
    # NUEVO: ALERTAS TEMPRANAS DE RENDIMIENTO
    # ===========================================
    
    # Verificar alertas de rendimiento para cada trabajador
    st.markdown("<h2 class='section-title animate-fade-in'>🚨 Alertas Tempranas de Rendimiento</h2>", unsafe_allow_html=True)
    
    alertas_totales = []
    for _, row in df_rango.iterrows():
        # Calcular meta diaria dinámica para este trabajador
        if row['equipo'] == 'Transferencias' and row['meta_mensual'] > 0:
            meta_diaria_dinamica = calcular_meta_diaria_dinamica(row['meta_mensual'], selected_year, selected_month)
        else:
            meta_diaria_dinamica = row['meta']
        
        # Verificar alertas
        alertas = verificar_alertas_rendimiento(
            row['eficiencia'], 
            row['productividad'], 
            meta_diaria_dinamica,
            row['cantidad']
        )
        
        for alerta in alertas:
            alerta['trabajador'] = row['nombre']
            alerta['fecha'] = row['fecha'].strftime('%Y-%m-%d')
            alertas_totales.append(alerta)
    
    # Mostrar alertas
    if alertas_totales:
        # Separar alertas por gravedad
        alertas_altas = [a for a in alertas_totales if a['gravedad'] == 'ALTA']
        alertas_medias = [a for a in alertas_totales if a['gravedad'] == 'MEDIA']
        
        if alertas_altas:
            st.markdown("<h3 class='section-title'>🔴 Alertas Críticas</h3>", unsafe_allow_html=True)
            for alerta in alertas_altas:
                st.markdown(f"""
                <div class="early-warning-critical">
                    <span class="warning-icon">⚠️</span>
                    <strong>{alerta['trabajador']} - {alerta['fecha']}:</strong> {alerta['mensaje']}
                </div>
                """, unsafe_allow_html=True)
        
        if alertas_medias:
            st.markdown("<h3 class='section-title'>🟡 Alertas de Advertencia</h3>", unsafe_allow_html=True)
            for alerta in alertas_medias:
                st.markdown(f"""
                <div class="early-warning">
                    <span class="warning-icon">⚠️</span>
                    <strong>{alerta['trabajador']} - {alerta['fecha']}:</strong> {alerta['mensaje']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("<div class='success-box'>✅ No se detectaron problemas de rendimiento críticos</div>", unsafe_allow_html=True)
    
    # Resto del dashboard (equipos, trabajadores, etc.)
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

# ================================
# FUNCIÓN PRINCIPAL MEJORADA
# ================================

def main():
    """Función principal de la aplicación con sistema de autenticación mejorado"""
    
    # Mostrar logo y título en el sidebar
    st.sidebar.markdown("""
    <div class='sidebar-title'>
        <div class='aeropostale-logo'>AEROPOSTALE</div>
        <div class='aeropostale-subtitle'>Sistema de Gestión de KPIs</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Menú de navegación para administrador
    admin_menu_options = [
        ("Dashboard KPIs", "📊", mostrar_dashboard_kpis),
        ("Análisis Histórico", "📈", mostrar_analisis_historico_kpis),
        ("Ingreso de Datos", "📥", mostrar_ingreso_datos_kpis),
        ("Gestión de Trabajadores", "👥", mostrar_gestion_trabajadores_kpis),
        ("Gestión de Distribuciones", "📦", mostrar_gestion_distribuciones),
        ("Gestión de Usuarios Guías", "👤", mostrar_gestion_usuarios_guias),
        ("Generar Guías", "📋", mostrar_generacion_guias),
        ("Historial de Guías", "🔍", mostrar_historial_guias),
        ("Ayuda y Contacto", "❓", mostrar_ayuda)
    ]
    
    # Menú de navegación para usuarios de guías
    guia_menu_options = [
        ("Generar Guías", "📋", mostrar_generacion_guias),
        ("Historial de Guías", "🔍", mostrar_historial_guias),
        ("Ayuda y Contacto", "❓", mostrar_ayuda)
    ]
    
    # Menú básico para usuarios no autenticados
    basic_menu_options = [
        ("Dashboard KPIs", "📊", mostrar_dashboard_kpis),
        ("Generar Guías", "📋", mostrar_generacion_guias),
        ("Historial de Guías", "🔍", mostrar_historial_guias),
        ("Ayuda y Contacto", "❓", mostrar_ayuda)
    ]
    
    # Determinar qué menú mostrar
    if verificar_password():
        menu_options = admin_menu_options
    elif verificar_usuario_guia():
        menu_options = guia_menu_options
    else:
        menu_options = basic_menu_options
    
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
    
    # Para las opciones que requieren autenticación específica
    if st.session_state.selected_menu == 5:  # Gestión de Usuarios Guías
        if not verificar_password():
            solicitar_autenticacion()
        else:
            func()
    elif st.session_state.selected_menu in [6, 7]:  # Generar Guías, Historial de Guías
        if not verificar_usuario_guia() and not verificar_password():
            autenticar_usuario_guia()
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
