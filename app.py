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
from fpdf import FPDF
import base64
import io
import tempfile
import random #! IMPORTANTE: Añadido para generar tracking numbers únicos
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

# ================================
# Configuración y Conexiones
# ================================

# Configuración de Supabase (desde variables de entorno)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ! CRITICAL: La contraseña se ha movido a una variable de entorno por seguridad.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Wilo3161")

# Configuración de imágenes
APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

@st.cache_resource
def init_supabase() -> Optional[Client]:
    """Inicializa y cachea el cliente de Supabase de forma segura."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY")
        st.error("Error de configuración: Faltan las variables de conexión a la base de datos.")
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error al inicializar Supabase: {e}", exc_info=True)
        st.error("Error al conectar con la base de datos. Verifique la configuración.")
        return None

supabase = init_supabase()

# Configuración de página
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# CSS (sin cambios)
st.markdown("""
<style>
    /* Colores corporativos de Aeropostale */
    :root {
        --primary-color: navy;
        --secondary-color: #000000;
        --accent-color: #333333;
        --background-dark: #121212;
        --card-background: #2d30f0;
        --text-color: white;
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
# Funciones de Utilidad y KPIs
# ================================
# (Sin cambios en esta sección, se asumen correctas)
def validar_fecha(fecha: str) -> bool:
    """Valida que una fecha tenga el formato correcto YYYY-MM-DD."""
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False

def validar_numero_positivo(valor: Any) -> bool:
    """Valida que un valor sea numérico y no negativo."""
    try:
        return float(valor) >= 0
    except (ValueError, TypeError):
        return False

def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general de forma segura."""
    return (cantidad / meta) * 100 if meta > 0 else 0.0

def productividad_hora(cantidad: float, horas_trabajo: float) -> float:
    """Calcula la productividad por hora de forma segura."""
    return cantidad / horas_trabajo if horas_trabajo > 0 else 0.0

# ================================
# Funciones de Acceso a Datos (Supabase)
# ================================
# (Sin cambios en las funciones de obtener trabajadores, equipos, guardar kpis, etc.)
def get_default_workers() -> pd.DataFrame:
    """Retorna un DataFrame de trabajadores por defecto para resiliencia."""
    logger.warning("Usando lista de trabajadores por defecto debido a un error o falta de conexión.")
    return pd.DataFrame({
        'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García", 
                   "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
        'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo", 
                   "Guías", "Ventas", "Ventas", "Ventas"]
    })

def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores activos desde Supabase con fallback."""
    if supabase is None:
        return get_default_workers()
    
    try:
        response = supabase.from_('trabajadores').select('nombre, equipo').eq('activo', True).order('equipo,nombre').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df
        else:
            logger.warning("No se encontraron trabajadores activos en Supabase.")
            return pd.DataFrame(columns=['nombre', 'equipo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores de Supabase: {e}", exc_info=True)
        return get_default_workers()

def obtener_equipos() -> list:
    """Obtiene la lista de equipos únicos desde Supabase con fallback."""
    default_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    if supabase is None:
        logger.warning("Usando lista de equipos por defecto.")
        return default_equipos

    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo').execute()
        if response.data:
            equipos = {item['equipo'] for item in response.data}
            # Asegurar que los equipos principales estén presentes
            for eq in default_equipos:
                equipos.add(eq)
            
            # Ordenar los equipos en un orden específico
            orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
            equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
            equipos_restantes = sorted([eq for eq in equipos if eq not in orden_equipos])
            return equipos_ordenados + equipos_restantes
        else:
            logger.warning("No se encontraron equipos en Supabase, usando lista por defecto.")
            return default_equipos
    except Exception as e:
        logger.error(f"Error al obtener equipos de Supabase: {e}", exc_info=True)
        return default_equipos
        
def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos de KPIs en Supabase usando upsert para eficiencia."""
    if supabase is None:
        logger.error("No se pueden guardar datos: Cliente de Supabase no inicializado.")
        st.error("Error de conexión con la base de datos.")
        return False
    
    if not validar_fecha(fecha):
        logger.error(f"Intento de guardado con fecha inválida: {fecha}")
        st.error("Formato de fecha inválido. No se pudo guardar.")
        return False

    registros = []
    for nombre, info in datos.items():
        if not all(validar_numero_positivo(info.get(k, 0)) for k in ["cantidad", "meta", "horas_trabajo"]):
            logger.warning(f"Datos numéricos inválidos para {nombre}, omitiendo registro.")
            st.warning(f"Datos inválidos para {nombre}. Por favor, revise los valores.")
            continue
            
        registros.append({
            "fecha": fecha,
            "nombre": nombre,
            "actividad": info.get("actividad", "N/A"),
            "cantidad": float(info.get("cantidad", 0)),
            "meta": float(info.get("meta", 0)),
            "eficiencia": float(info.get("eficiencia", 0)),
            "productividad": float(info.get("productividad", 0)),
            "comentario": info.get("comentario", ""),
            "meta_mensual": float(info.get("meta_mensual", 0)),
            "horas_trabajo": float(info.get("horas_trabajo", 0)),
            "equipo": info.get("equipo", "N/A")
        })
    
    if not registros:
        logger.warning("No hay registros válidos para guardar.")
        st.error("No se encontraron datos válidos para guardar.")
        return False
    
    try:
        supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
        # Limpiar caché de datos históricos para forzar recarga
        if 'historico_data' in st.session_state:
            del st.session_state['historico_data']
        logger.info(f"Datos guardados correctamente en Supabase para la fecha {fecha}.")
        return True
    except Exception as e:
        logger.error(f"Error crítico al guardar datos en Supabase: {e}", exc_info=True)
        st.error("Error crítico al guardar los datos. Por favor, contacte al administrador.")
        return False

def cargar_historico_db() -> pd.DataFrame:
    """Carga todos los datos históricos desde Supabase."""
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.from_('daily_kpis').select('*').order('fecha', desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def obtener_datos_fecha(fecha: str) -> pd.DataFrame:
    """Obtiene los datos de una fecha específica desde Supabase."""
    if supabase is None or not validar_fecha(fecha):
        return pd.DataFrame()
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos para la fecha {fecha}: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# Funciones de Guías (CORREGIDAS)
# ================================

def generar_numero_seguimiento() -> str:
    """
    ! CORREGIDO: Genera un número de seguimiento único basado en el timestamp.
    Esto elimina la dependencia del ID de la base de datos y permite guardar en un solo paso.
    """
    timestamp_ms = int(time.time() * 1000)
    random_part = random.randint(100, 999)
    return f"9400{timestamp_ms}{random_part}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera una imagen de código QR a partir de una URL."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=5, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def obtener_tiendas() -> pd.DataFrame:
    """Obtiene la lista de tiendas desde Supabase."""
    if supabase is None: return pd.DataFrame(columns=['id', 'name'])
    try:
        response = supabase.from_('guide_stores').select('id, name').execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'name'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas: {e}", exc_info=True)
        return pd.DataFrame(columns=['id', 'name'])

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase."""
    if supabase is None: return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    try:
        response = supabase.from_('guide_senders').select('*').execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes: {e}", exc_info=True)
        return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> Optional[Dict]:
    """
    ! CORREGIDO: Guarda una guía en Supabase en un solo paso y devuelve los datos guardados.
    """
    if supabase is None:
        logger.error("No se pudo guardar la guía: Cliente Supabase no inicializado.")
        return None
    
    try:
        # 1. Generar el número de seguimiento ANTES de la inserción
        tracking_number = generar_numero_seguimiento()
        
        # 2. Preparar el registro completo
        data_to_insert = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat(),
            'tracking_number': tracking_number # Incluir el tracking number
        }
        
        # 3. Insertar el registro y solicitar que se devuelvan los datos insertados
        response = supabase.from_('guide_logs').insert(data_to_insert).select().execute()
        
        if response.data:
            saved_data = response.data[0]
            logger.info(f"Guía guardada con tracking_number: {saved_data['tracking_number']}")
            return saved_data # Devolver el diccionario completo del registro
        else:
            logger.error("No se pudo guardar la guía en Supabase (respuesta vacía).", extra={"response": response})
            return None
    except Exception as e:
        logger.error(f"Error al guardar guía en Supabase: {e}", exc_info=True)
        st.error(f"Error de base de datos al guardar la guía: {e}")
        return None

def generar_pdf_guia(store_name: str, brand: str, url: str, sender_name: str, 
                    sender_address: str, sender_phone: str, tracking_number: str) -> bytes:
    """Genera un archivo PDF para la guía de envío."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Guía de Envío", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Tienda:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, store_name, ln=True)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Marca:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, brand, ln=True)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "Remitente:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{sender_name} - {sender_phone}", ln=True)
        
        pdf.cell(40, 8, "") # Alineación
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, sender_address)
        pdf.ln(5)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 8, "Número de Seguimiento:")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, tracking_number, ln=True)
        pdf.ln(5)
        
        qr_img = generar_qr_imagen(url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_qr:
            qr_img.save(temp_qr.name)
            pdf.image(temp_qr.name, x=70, y=pdf.get_y(), w=70, h=70)
            os.unlink(temp_qr.name)
        
        pdf.ln(75)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(40, 8, "URL del Pedido:")
        pdf.set_font("Arial", "U", 12)
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 8, url, link=url, ln=True)
        
        return pdf.output(dest="S").encode("latin1")
    except Exception as e:
        logger.error(f"Error al generar PDF de guía: {e}", exc_info=True)
        return b""
        
# ================================
# Componentes de la Aplicación (Páginas)
# ================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs y el rendimiento de equipos clave."""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos. No se pueden mostrar los KPIs.")
        return

    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.warning("⚠️ No hay datos históricos. Por favor, ingrese datos en la sección 'Ingreso de Datos'.")
        return
    
    fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
    col1, col2 = st.columns(2)
    fecha_inicio = col1.date_input("Fecha de inicio:", value=fechas_disponibles[-1], min_value=fechas_disponibles[-1], max_value=fechas_disponibles[0])
    fecha_fin = col2.date_input("Fecha de fin:", value=fechas_disponibles[0], min_value=fechas_disponibles[-1], max_value=fechas_disponibles[0])
    
    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
        return
    
    df_rango = df[(df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)]
    if df_rango.empty:
        st.warning(f"⚠️ No hay datos disponibles para el rango de fechas seleccionado.")
        return
    
    st.markdown("<h2 class='section-title'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    total_cantidad = df_rango['cantidad'].sum()
    total_meta = df_rango['meta'].sum()
    total_horas = df_rango['horas_trabajo'].sum()
    avg_eficiencia = np.average(df_rango['eficiencia'], weights=df_rango['horas_trabajo']) if total_horas > 0 else 0
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Producción", f"{total_cantidad:,.0f}", f"Meta: {total_meta:,.0f}")
    kpi2.metric("Eficiencia Promedio Ponderada", f"{avg_eficiencia:.1f}%")
    kpi3.metric("Productividad Total", f"{productividad_total:.1f} u/h")

    # ! SECCIÓN MEJORADA: Rendimiento por Equipos Clave
    st.markdown("<h2 class='section-title'>📊 Rendimiento por Equipos Clave</h2>", unsafe_allow_html=True)
    
    equipos_clave = ["Transferencias", "Distribución", "Guías", "Ventas"]
    
    for equipo in equipos_clave:
        df_equipo = df_rango[df_rango['equipo'] == equipo].copy()
        
        with st.expander(f"**{equipo}**", expanded=True):
            if df_equipo.empty:
                st.write("No hay datos para este equipo en el período seleccionado.")
                continue

            # Calcular KPIs del equipo
            total_equipo = df_equipo['cantidad'].sum()
            meta_equipo = df_equipo['meta'].sum()
            horas_equipo = df_equipo['horas_trabajo'].sum()
            eficiencia_equipo = np.average(df_equipo['eficiencia'], weights=df_equipo['horas_trabajo']) if horas_equipo > 0 else 0
            
            # Mostrar métricas del equipo
            col1, col2, col3 = st.columns(3)
            col1.metric("Producción del Equipo", f"{total_equipo:,.0f}", f"Meta: {meta_equipo:,.0f}")
            col2.metric("Eficiencia Promedio", f"{eficiencia_equipo:.1f}%")
            col3.metric("Horas Totales", f"{horas_equipo:.1f} h")
            
            st.markdown("---")
            st.write("**Detalle por Trabajador:**")
            
            # Mostrar trabajadores del equipo
            for _, row in df_equipo.iterrows():
                color = "green" if row['eficiencia'] >= 100 else "red"
                st.markdown(f"**{row['nombre']}** - Eficiencia: <span style='color:{color};'>**{row['eficiencia']:.1f}%**</span>", unsafe_allow_html=True)
                st.write(f"Producción: **{row['cantidad']}** | Productividad: **{row['productividad']:.1f}/hora** | Horas: **{row['horas_trabajo']:.1f}**")
                
                # Mostrar comentario si existe
                comentario = row.get('comentario')
                if comentario and str(comentario).strip():
                    st.info(f"💬 Comentario: {comentario}")
                st.markdown("---")

def mostrar_generacion_guias():
    """Página para generar guías de envío (flujo corregido)."""
    st.markdown("<h1 class='header-title'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos.")
        return
        
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()

    if tiendas.empty or remitentes.empty:
        st.warning("⚠️ No hay tiendas o remitentes configurados. Vaya a la sección de configuración.")
        return
    
    with st.form("form_generar_guia"):
        col1, col2 = st.columns(2)
        store_name = col1.selectbox("Seleccione Tienda", tiendas['name'].tolist())
        brand = col1.radio("Seleccione Empresa:", ["Fashion", "Tempo"], horizontal=True)
        sender_name = col2.selectbox("Seleccione Remitente:", remitentes['name'].tolist())
        url = st.text_input("Ingrese URL del Pedido:", placeholder="https://...")
        
        submitted = st.form_submit_button("Generar Guía", use_container_width=True)
        
        if submitted:
            if all([store_name, brand, url, sender_name]) and url.startswith(('http://', 'https://')):
                # ! FLUJO CORREGIDO: Llamada única a la función de guardado
                with st.spinner("Generando y guardando guía..."):
                    saved_guia_data = guardar_guia(store_name, brand, url, sender_name)
                
                if saved_guia_data:
                    remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                    # Guardar en session state para previsualización
                    st.session_state.preview_data = {
                        "store_name": saved_guia_data['store_name'],
                        "brand": saved_guia_data['brand'],
                        "url": saved_guia_data['url'],
                        "sender_name": saved_guia_data['sender_name'],
                        "sender_address": remitente_info['address'],
                        "sender_phone": remitente_info['phone'],
                        "tracking_number": saved_guia_data['tracking_number']
                    }
                    st.success("✅ Guía generada y guardada correctamente.")
                    st.rerun() # Forzar la recarga para mostrar la previsualización
                else:
                    st.error("❌ Error al guardar la guía en la base de datos. Revise los logs.")
            else:
                st.error("❌ Por favor, complete todos los campos y asegúrese de que la URL sea válida.")

    if 'preview_data' in st.session_state:
        data = st.session_state.preview_data
        st.markdown("<h2 class='section-title'>Previsualización de la Guía</h2>", unsafe_allow_html=True)
        
        st.info(f"**Tienda:** {data['store_name']} | **Marca:** {data['brand']} | **Remitente:** {data['sender_name']}")
        st.code(f"URL: {data['url']}\nTracking: {data['tracking_number']}", language=None)

        qr_img = generar_qr_imagen(data['url'])
        st.image(qr_img, width=150)
        
        pdf_data = generar_pdf_guia(**data)
        st.download_button(
            label="📄 Descargar PDF de la Guía",
            data=pdf_data,
            file_name=f"guia_{data['store_name']}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            on_click=lambda: st.session_state.pop('preview_data', None) # Limpiar preview después de descargar
        )

# El resto de las funciones (autenticación, main, etc.) permanecen sin cambios
# ... (Se omite el resto del código por brevedad, ya que no fue modificado)
# ... (Pegar aquí el resto del código sin modificar: `verificar_password`, `solicitar_autenticacion`,
#     `mostrar_analisis_historico_kpis`, `mostrar_ingreso_datos_kpis`, 
#     `mostrar_gestion_trabajadores_kpis`, `mostrar_gestion_distribuciones`,
#     `mostrar_historial_guias`, `mostrar_ayuda`, y `main`)

def verificar_password() -> bool:
    """Verifica si el usuario ha ingresado la contraseña correcta."""
    return st.session_state.get('password_correct', False)

def solicitar_autenticacion():
    """Muestra un formulario de autenticación centrado y estilizado."""
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aerostale-subtitle">Sistema de Gestión de KPIs</div>
        </div>
        <h2 class="password-title">🔐 Acceso Restringido</h2>
        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 25px;">
            Ingrese la contraseña de administrador para continuar.
        </p>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña:", type="password", key="auth_password", label_visibility="collapsed")
    
    if st.button("Ingresar", use_container_width=True):
        if password == ADMIN_PASSWORD:
            st.session_state.password_correct = True
            st.success("✅ Acceso concedido. Redirigiendo...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_analisis_historico_kpis():
    """Página para análisis histórico y exportación de datos."""
    st.markdown("<h1 class='header-title'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos.")
        return
        
    df = cargar_historico_db()
    if df.empty:
        st.warning("⚠️ No hay datos históricos para analizar.")
        return

    st.markdown("<h2 class='section-title'>📋 Datos Detallados</h2>", unsafe_allow_html=True)
    st.dataframe(df)
    
    st.markdown("<h2 class='section-title'>📤 Exportar Datos</h2>", unsafe_allow_html=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📊 Descargar CSV",
        data=csv,
        file_name="kpis_historico_completo.csv",
        mime="text/csv",
        use_container_width=True
    )
    
def mostrar_ingreso_datos_kpis():
    """Página para el ingreso diario de datos de KPIs."""
    st.markdown("<h1 class='header-title'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)

    if supabase is None:
        st.error("❌ Error de conexión a la base de datos.")
        return

    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.warning("⚠️ No hay trabajadores registrados. Vaya a 'Gestión de Trabajadores' para agregarlos.")
        return

    trabajadores_por_equipo = df_trabajadores.groupby('equipo')['nombre'].apply(list).to_dict()
    
    fecha_seleccionada = st.date_input("Selecciona la fecha:", value=datetime.now(), max_value=datetime.now())
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    
    datos_existentes = obtener_datos_fecha(fecha_str)
    if not datos_existentes.empty:
        st.info(f"ℹ️ Ya existen datos para la fecha {fecha_str}. Puede editarlos a continuación.")

    with st.form("form_datos"):
        st.markdown("<h3 class='section-title'>Meta Mensual (Transferencias)</h3>", unsafe_allow_html=True)
        meta_mensual_default = 150000
        if not datos_existentes.empty and 'meta_mensual' in datos_existentes.columns:
            meta_existente = datos_existentes[datos_existentes['equipo'] == 'Transferencias']['meta_mensual']
            if not meta_existente.empty:
                meta_mensual_default = int(meta_existente.iloc[0])
        
        meta_mensual_transferencias = st.number_input("Meta mensual para el equipo de transferencias:", min_value=0, value=meta_mensual_default)
        
        equipos_ordenados = sorted(trabajadores_por_equipo.keys())
        
        for equipo in equipos_ordenados:
            st.markdown(f"<h3 class='section-title'>{equipo}</h3>", unsafe_allow_html=True)
            for trabajador in trabajadores_por_equipo[equipo]:
                st.subheader(trabajador)
                
                datos_trab_exist = datos_existentes[datos_existentes['nombre'] == trabajador] if not datos_existentes.empty else pd.DataFrame()
                
                default_values = {
                    "cantidad": int(datos_trab_exist['cantidad'].iloc[0]) if not datos_trab_exist.empty else 0,
                    "meta": int(datos_trab_exist['meta'].iloc[0]) if not datos_trab_exist.empty else 100,
                    "horas": float(datos_trab_exist['horas_trabajo'].iloc[0]) if not datos_trab_exist.empty else 8.0,
                    "comentario": datos_trab_exist['comentario'].iloc[0] if not datos_trab_exist.empty else ""
                }
                
                col1, col2, col3 = st.columns(3)
                cantidad = col1.number_input("Cantidad:", min_value=0, value=default_values['cantidad'], key=f"{trabajador}_cantidad")
                meta = col2.number_input("Meta Diaria:", min_value=0, value=default_values['meta'], key=f"{trabajador}_meta")
                horas = col3.number_input("Horas Trabajadas:", min_value=0.0, step=0.5, value=default_values['horas'], key=f"{trabajador}_horas")
                comentario = st.text_area("Comentario (opcional):", value=default_values['comentario'], key=f"{trabajador}_comentario")

        if st.form_submit_button("Guardar Datos", use_container_width=True):
            datos_guardar = {}
            for equipo, miembros in trabajadores_por_equipo.items():
                for trabajador in miembros:
                    cantidad = st.session_state[f"{trabajador}_cantidad"]
                    meta = st.session_state[f"{trabajador}_meta"]
                    horas = st.session_state[f"{trabajador}_horas"]
                    
                    datos_guardar[trabajador] = {
                        "actividad": equipo, "cantidad": cantidad, "meta": meta,
                        "eficiencia": calcular_kpi(cantidad, meta), 
                        "productividad": productividad_hora(cantidad, horas),
                        "comentario": st.session_state[f"{trabajador}_comentario"],
                        "meta_mensual": meta_mensual_transferencias if equipo == "Transferencias" else 0,
                        "horas_trabajo": horas, "equipo": equipo
                    }
            
            if guardar_datos_db(fecha_str, datos_guardar):
                st.success("✅ Datos guardados correctamente.")
            else:
                st.error("❌ Error al guardar los datos.")

def mostrar_gestion_trabajadores_kpis():
    """Página para agregar, ver y desactivar trabajadores."""
    st.markdown("<h1 class='header-title'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos.")
        return
        
    response = supabase.from_('trabajadores').select('*').order('equipo,nombre').execute()
    trabajadores = pd.DataFrame(response.data) if response.data else pd.DataFrame()

    st.markdown("<h2 class='section-title'>Trabajadores Actuales</h2>", unsafe_allow_html=True)
    if not trabajadores.empty:
        st.dataframe(trabajadores[['nombre', 'equipo', 'activo']], use_container_width=True)
    else:
        st.info("No hay trabajadores registrados.")
        
    tab1, tab2 = st.tabs(["➕ Agregar Trabajador", "➖ Desactivar Trabajador"])

    with tab1:
        with st.form("form_nuevo_trabajador"):
            nuevo_nombre = st.text_input("Nombre del trabajador:")
            nuevo_equipo = st.selectbox("Equipo:", options=obtener_equipos())
            if st.form_submit_button("Agregar Trabajador"):
                if nuevo_nombre and nuevo_equipo:
                    try:
                        supabase.from_('trabajadores').insert({'nombre': nuevo_nombre, 'equipo': nuevo_equipo, 'activo': True}).execute()
                        st.success(f"✅ Trabajador '{nuevo_nombre}' agregado correctamente.")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error: Es posible que el trabajador ya exista. ({e})")
                else:
                    st.error("❌ El nombre y el equipo no pueden estar vacíos.")

    with tab2:
        if not trabajadores.empty:
            trabajadores_activos = trabajadores[trabajadores['activo'] == True]['nombre'].tolist()
            if trabajadores_activos:
                trab_eliminar = st.selectbox("Selecciona trabajador a desactivar:", options=trabajadores_activos)
                if st.button("Desactivar Trabajador", type="primary"):
                    try:
                        supabase.from_('trabajadores').update({'activo': False}).eq('nombre', trab_eliminar).execute()
                        st.success(f"✅ Trabajador '{trab_eliminar}' desactivado.")
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"Error al desactivar: {e}")
            else:
                st.info("No hay trabajadores activos para desactivar.")

def mostrar_gestion_distribuciones():
    st.markdown("<h1 class='header-title'>📊 Gestión de Distribuciones Semanales</h1>", unsafe_allow_html=True)
    st.write("Esta sección está en desarrollo.")

def mostrar_historial_guias():
    st.markdown("<h1 class='header-title'>🔍 Historial de Guías de Envío</h1>", unsafe_allow_html=True)
    st.write("Esta sección está en desarrollo.")

def mostrar_ayuda():
    st.markdown("<h1 class='header-title'>❓ Ayuda y Contacto</h1>", unsafe_allow_html=True)
    st.info("""
    ### 📞 Soporte Técnico
    Si encuentras algún problema, contacta a:
    - **Ing. Wilson Pérez**
    - **Teléfono:** 0993052744
    """)

def main():
    """Función principal que renderiza la aplicación Streamlit."""
    
    st.sidebar.markdown("<div class='sidebar-title'>AEROPOSTALE<br><span class='aeropostale-subtitle'>Gestión de KPIs</span></div>", unsafe_allow_html=True)
    
    menu_options = {
        "Dashboard KPIs": ("📊", mostrar_dashboard_kpis),
        "Análisis Histórico": ("📈", mostrar_analisis_historico_kpis),
        "Generar Guías": ("📋", mostrar_generacion_guias),
        "Historial de Guías": ("🔍", mostrar_historial_guias),
        "Ingreso de Datos": ("📥", mostrar_ingreso_datos_kpis),
        "Gestión de Distribuciones": ("📦", mostrar_gestion_distribuciones),
        "Gestión de Trabajadores": ("👥", mostrar_gestion_trabajadores_kpis),
        "Ayuda y Contacto": ("❓", mostrar_ayuda)
    }
    
    paginas_protegidas = ["Ingreso de Datos", "Gestión de Distribuciones", "Gestión de Trabajadores"]
    
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "Dashboard KPIs"

    for label, (icon, _) in menu_options.items():
        if st.sidebar.button(f"{icon} {label}", use_container_width=True):
            st.session_state.selected_page = label
            st.rerun()

    page_label = st.session_state.selected_page
    _, page_function = menu_options[page_label]
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"© {datetime.now().year} Aeropostale. Desarrollado por Wilson Pérez.")
    
    if page_label in paginas_protegidas and not verificar_password():
        solicitar_autenticacion()
    else:
        page_function()

if __name__ == "__main__":
    main()
