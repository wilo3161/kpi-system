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
# ! Nunca dejes contraseñas escritas directamente en el código.
# ! Para ejecutar la app, debes configurar esta variable en tu entorno.
# ! Ejemplo: export ADMIN_PASSWORD="TuContraseñaSegura"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Wilo3161") # Se mantiene el valor original como fallback para desarrollo local

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

# Inicializar cliente de Supabase
supabase = init_supabase()

# Configuración de página
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📦",
    initial_sidebar_state="expanded"
)

# CSS profesional (sin cambios, se asume correcto)
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
# Funciones de utilidad compartidas
# ================================

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

def validar_distribuciones(valor: Any) -> bool:
    """Valida que el valor de distribuciones sea numérico, no negativo y dentro de un límite razonable."""
    try:
        num = float(valor)
        return 0 <= num <= 20000  # Límite razonable aumentado
    except (ValueError, TypeError):
        return False

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña."""
    return hashlib.sha256(pw.encode()).hexdigest()

# ================================
# Funciones de KPIs
# ================================

def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general de forma segura."""
    return (cantidad / meta) * 100 if meta > 0 else 0.0

def kpi_transferencias(transferidas: float, meta: float = 1750) -> float:
    return calcular_kpi(transferidas, meta)

def kpi_arreglos(arregladas: float, meta: float = 150) -> float:
    return calcular_kpi(arregladas, meta)

def kpi_distribucion(distribuidas: float, meta: float = 1000) -> float:
    return calcular_kpi(distribuidas, meta)

def kpi_guias(guias: float, meta: float = 120) -> float:
    return calcular_kpi(guias, meta)

def productividad_hora(cantidad: float, horas_trabajo: float) -> float:
    """Calcula la productividad por hora de forma segura."""
    return cantidad / horas_trabajo if horas_trabajo > 0 else 0.0

# ================================
# Funciones de Acceso a Datos (Supabase)
# ================================

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

def cargar_historico_db(fecha_inicio: Optional[str] = None, 
                       fecha_fin: Optional[str] = None, 
                       trabajador: Optional[str] = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase con filtros opcionales."""
    if supabase is None:
        logger.error("No se pueden cargar datos: Cliente de Supabase no inicializado.")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('daily_kpis').select('*')
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador and trabajador != "Todos":
            query = query.eq('nombre', trabajador)
            
        response = query.order('fecha', desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['cumplimiento_meta'] = np.where(df['cantidad'] >= df['meta'], 'Sí', 'No')
            df['diferencia_meta'] = df['cantidad'] - df['meta']
            return df
        else:
            logger.info("No se encontraron datos históricos en Supabase para los filtros aplicados.")
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
# Funciones para Distribuciones y Dependencias
# ================================

def obtener_distribuciones_semana(fecha_inicio_semana: str) -> Dict[str, int]:
    """Obtiene las distribuciones de una semana específica desde Supabase."""
    default_dist = {'tempo': 0, 'luis': 0}
    if supabase is None or not validar_fecha(fecha_inicio_semana):
        return default_dist
    
    try:
        response = supabase.from_('distribuciones_semanales').select('tempo_distribuciones, luis_distribuciones').eq('semana', fecha_inicio_semana).maybe_single().execute()
        if response.data:
            return {
                'tempo': response.data.get('tempo_distribuciones', 0),
                'luis': response.data.get('luis_distribuciones', 0)
            }
        return default_dist
    except Exception as e:
        logger.error(f"Error al obtener distribuciones semanales: {e}", exc_info=True)
        return default_dist

def guardar_distribuciones_semanales(semana: str, tempo_distribuciones: int, luis_distribuciones: int, meta_semanal: int = 7500) -> bool:
    """Guarda (inserta o actualiza) las distribuciones semanales en Supabase usando upsert."""
    if supabase is None:
        logger.error("No se pueden guardar distribuciones: Cliente de Supabase no inicializado.")
        return False

    if not all([validar_fecha(semana), 
                validar_distribuciones(tempo_distribuciones), 
                validar_distribuciones(luis_distribuciones), 
                validar_distribuciones(meta_semanal)]):
        logger.error("Datos de distribuciones inválidos.")
        st.error("Los valores ingresados para las distribuciones no son válidos.")
        return False
    
    try:
        # ! REFACTOR: Se utiliza upsert para simplificar la lógica y reducir llamadas a la BD.
        data_to_upsert = {
            'semana': semana,
            'tempo_distribuciones': int(tempo_distribuciones),
            'luis_distribuciones': int(luis_distribuciones),
            'meta_semanal': int(meta_semanal),
            'updated_at': datetime.now().isoformat()
        }
        supabase.from_('distribuciones_semanales').upsert(data_to_upsert, on_conflict='semana').execute()
        logger.info(f"Distribuciones semanales guardadas correctamente para la semana {semana}.")
        return True
    except Exception as e:
        logger.error(f"Error al guardar distribuciones semanales: {e}", exc_info=True)
        st.error("Ocurrió un error al intentar guardar las distribuciones.")
        return False

def obtener_dependencias_transferencias() -> pd.DataFrame:
    """Obtiene las dependencias entre transferidores y proveedores desde Supabase."""
    default_deps = pd.DataFrame({
        'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
        'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
    })
    if supabase is None:
        return default_deps
    
    try:
        response = supabase.from_('dependencias_transferencias').select('*').execute()
        return pd.DataFrame(response.data) if response.data else default_deps
    except Exception as e:
        logger.error(f"Error al obtener dependencias de transferencias: {e}", exc_info=True)
        return default_deps

# ================================
# Funciones de Guías
# ================================

def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único basado en el ID del registro."""
    # ! FIX: El número de seguimiento ahora es único por registro.
    return f"9400{str(record_id).zfill(20)}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera una imagen de código QR a partir de una URL."""
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
    """Obtiene la lista de tiendas desde Supabase."""
    if supabase is None:
        return pd.DataFrame(columns=['id', 'name'])
    try:
        response = supabase.from_('guide_stores').select('id, name').execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'name'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas: {e}", exc_info=True)
        return pd.DataFrame(columns=['id', 'name'])

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase."""
    if supabase is None:
        return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    try:
        response = supabase.from_('guide_senders').select('*').execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes: {e}", exc_info=True)
        return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> Optional[int]:
    """Guarda una guía en Supabase y devuelve el ID del nuevo registro."""
    if supabase is None:
        logger.error("No se pudo guardar la guía: Cliente Supabase no inicializado.")
        return None
    
    try:
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        }
        # ! FIX: Se añade .select() para retornar el ID del registro insertado.
        response = supabase.from_('guide_logs').insert(data).select('id').execute()
        
        if response.data:
            new_id = response.data[0]['id']
            logger.info(f"Guía guardada correctamente para {store_name} con ID: {new_id}")
            return new_id
        else:
            logger.error("No se pudo guardar la guía en Supabase (respuesta vacía).")
            return None
    except Exception as e:
        logger.error(f"Error al guardar guía en Supabase: {e}", exc_info=True)
        return None

def actualizar_guia_con_tracking(guia_id: int, tracking_number: str) -> bool:
    """Actualiza una guía con su número de seguimiento."""
    if supabase is None:
        return False
    try:
        supabase.from_('guide_logs').update({'tracking_number': tracking_number}).eq('id', guia_id).execute()
        logger.info(f"Guía {guia_id} actualizada con tracking number.")
        return True
    except Exception as e:
        logger.error(f"Error al actualizar guía {guia_id} con tracking number: {e}", exc_info=True)
        return False

def obtener_historial_guias() -> pd.DataFrame:
    """Obtiene el historial completo de guías desde Supabase."""
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.from_('guide_logs').select('*').order('created_at', desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar historial de guías: {e}", exc_info=True)
        return pd.DataFrame()

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
# Lógica de negocio y Visualizaciones
# ================================

def calcular_metas_semanales() -> Dict:
    """Calcula el progreso semanal y asigna responsabilidades."""
    fecha_inicio_semana = (datetime.now().date() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
    distribuciones = obtener_distribuciones_semana(fecha_inicio_semana)
    
    meta_semanal = 7500
    dist_totales = distribuciones['tempo'] + distribuciones['luis']
    
    resultado = {
        'meta_semanal': meta_semanal,
        'distribuciones_totales': dist_totales,
        'cumplimiento_porcentaje': calcular_kpi(dist_totales, meta_semanal),
        'detalles': []
    }
    
    meta_individual = meta_semanal / 2
    if distribuciones['tempo'] < meta_individual:
        resultado['detalles'].append({
            'transferidor': 'Josué Imbacuán', 'proveedor': 'Tempo',
            'recibidas': distribuciones['tempo'], 'requeridas': meta_individual, 'estado': 'INSUFICIENTE'
        })
    if distribuciones['luis'] < meta_individual:
        resultado['detalles'].append({
            'transferidor': 'Andrés Yépez', 'proveedor': 'Luis Perugachi',
            'recibidas': distribuciones['luis'], 'requeridas': meta_individual, 'estado': 'INSUFICIENTE'
        })
    return resultado

def verificar_alertas_abastecimiento() -> List[Dict]:
    """Verifica y devuelve alertas de abastecimiento si las hay."""
    resultado = calcular_metas_semanales()
    alertas = []
    for detalle in resultado.get('detalles', []):
        if detalle['estado'] == 'INSUFICIENTE':
            alertas.append({
                'tipo': 'ABASTECIMIENTO',
                'mensaje': f"{detalle['proveedor']} no abasteció lo suficiente para {detalle['transferidor']}.",
                'gravedad': 'ALTA',
                'accion': f"Revisar distribuciones de {detalle['proveedor']}."
            })
    return alertas

def crear_grafico_interactivo(df: pd.DataFrame, x: str, y: str, title: str, 
                             xlabel: str, ylabel: str, tipo: str = 'bar') -> go.Figure:
    """Crea gráficos interactivos con Plotly de forma robusta."""
    fig = go.Figure()
    if df.empty or x not in df.columns or y not in df.columns:
        logger.warning(f"DataFrame vacío o columnas no encontradas para el gráfico '{title}'.")
        fig.add_annotation(text="No hay datos disponibles para mostrar.", showarrow=False)
    else:
        try:
            if tipo == 'line':
                fig = px.line(df, x=x, y=y)
            elif tipo == 'scatter':
                fig = px.scatter(df, x=x, y=y)
            elif tipo == 'box':
                fig = px.box(df, x=x, y=y)
            else: # bar por defecto
                fig = px.bar(df, x=x, y=y)
        except Exception as e:
            logger.error(f"Error al generar gráfico con Plotly Express: {e}", exc_info=True)
            fig.add_annotation(text=f"Error al crear gráfico: {e}", showarrow=False)
            
    fig.update_layout(
        title_text=title,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color="#ffffff",
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    return fig

def crear_grafico_frasco(porcentaje: float, titulo: str) -> go.Figure:
    """Crea un gráfico de medidor (gauge) para porcentajes de cumplimiento."""
    try:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=porcentaje,
            number={'suffix': '%', 'font': {'size': 36}},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': titulo, 'font': {'size': 20}},
            gauge={
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
                'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 90}
            }
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            font_color="#ffffff"
        )
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de frasco: {e}", exc_info=True)
        return go.Figure().add_annotation(text="Error al crear gráfico.", showarrow=False)

def custom_selectbox(label: str, options: list, key: str, search_placeholder: str = "Buscar...") -> Optional[str]:
    """Componente personalizado de selectbox con búsqueda."""
    search_term = st.text_input(f"{search_placeholder} en {label}", key=f"{key}_search")
    
    if search_term:
        filtered_options = [opt for opt in options if search_term.lower() in str(opt).lower()]
    else:
        filtered_options = options
    
    if not filtered_options:
        st.warning("No se encontraron resultados.")
        return None
    
    return st.selectbox(label, filtered_options, key=key)

# ================================
# Sistema de Autenticación
# ================================

def verificar_password() -> bool:
    """Verifica si el usuario ha ingresado la contraseña correcta."""
    return st.session_state.get('password_correct', False)

def solicitar_autenticacion():
    """Muestra un formulario de autenticación centrado y estilizado."""
    st.markdown("""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Gestión de KPIs</div>
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

# ================================
# Componentes de la Aplicación (Páginas)
# ================================

def mostrar_estado_abastecimiento():
    """Muestra el estado de abastecimiento para transferencias."""
    resultado = calcular_metas_semanales()
    
    st.markdown("<h2 class='section-title'>📦 Estado de Abastecimiento Semanal</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Meta Semanal", f"{resultado['meta_semanal']:,.0f}")
    with col2:
        st.metric("Distribuciones Totales", f"{resultado['distribuciones_totales']:,.0f}")
    with col3:
        st.metric("Cumplimiento", f"{resultado['cumplimiento_porcentaje']:.1f}%")

    if resultado['detalles']:
        st.error("⚠️ **Problemas de Abastecimiento Detectados**")
        for detalle in resultado['detalles']:
            st.warning(f"""
            **{detalle['transferidor']}** no ha recibido suficientes distribuciones de **{detalle['proveedor']}**.
            - **Recibido:** {detalle['recibidas']:,.0f}
            - **Requerido:** {detalle['requeridas']:,.0f}
            - **Déficit:** {detalle['requeridas'] - detalle['recibidas']:,.0f}
            """)
    else:
        st.success("✅ **Abastecimiento adecuado** para cumplir la meta semanal.")

def mostrar_gestion_distribuciones():
    """Página para gestionar las distribuciones semanales."""
    st.markdown("<h1 class='header-title'>📊 Gestión de Distribuciones Semanales</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos. Esta función no está disponible.")
        return
    
    fecha_actual = datetime.now().date()
    fecha_inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fecha_inicio_semana_str = fecha_inicio_semana.strftime("%Y-%m-%d")
    
    st.info(f"Mostrando gestión para la semana que inicia el **{fecha_inicio_semana_str}**.")
    
    dist_existentes = obtener_distribuciones_semana(fecha_inicio_semana_str)
    
    with st.form("form_distribuciones"):
        st.markdown("<h3 class='section-title'>Registrar Distribuciones</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            tempo_dist = st.number_input("Distribuciones de Tempo:", min_value=0, value=dist_existentes.get('tempo', 0))
        with col2:
            luis_dist = st.number_input("Distribuciones de Luis Perugachi:", min_value=0, value=dist_existentes.get('luis', 0))
        
        meta_semanal = st.number_input("Meta Semanal (opcional):", min_value=0, value=7500)
        
        if st.form_submit_button("Guardar Distribuciones", use_container_width=True):
            if guardar_distribuciones_semanales(fecha_inicio_semana_str, tempo_dist, luis_dist, meta_semanal):
                st.success("✅ Distribuciones guardadas correctamente.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error al guardar las distribuciones.")
    
    mostrar_estado_abastecimiento()

def mostrar_dashboard_kpis():
    """Muestra el dashboard principal con KPIs."""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos. No se pueden mostrar los KPIs.")
        return
        
    # Mostrar alertas de abastecimiento en el dashboard principal
    for alerta in verificar_alertas_abastecimiento():
        st.error(f"🚨 **Alerta de Abastecimiento:** {alerta['mensaje']} {alerta['accion']}")

    if 'historico_data' not in st.session_state:
        with st.spinner("Cargando datos históricos..."):
            st.session_state.historico_data = cargar_historico_db()
    
    df = st.session_state.historico_data
    if df.empty:
        st.warning("⚠️ No hay datos históricos. Por favor, ingrese datos en la sección 'Ingreso de Datos'.")
        return
    
    # Selector de rango de fechas
    fechas_disponibles = sorted(df['fecha'].dt.date.unique(), reverse=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio:", value=fechas_disponibles[-1], min_value=fechas_disponibles[-1], max_value=fechas_disponibles[0])
    with col2:
        fecha_fin = st.date_input("Fecha de fin:", value=fechas_disponibles[0], min_value=fechas_disponibles[-1], max_value=fechas_disponibles[0])
    
    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
        return
    
    df_rango = df[(df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)]
    if df_rango.empty:
        st.warning(f"⚠️ No hay datos disponibles para el rango de fechas seleccionado.")
        return
    
    st.markdown("<h2 class='section-title'>📈 KPIs Globales</h2>", unsafe_allow_html=True)
    
    # Cálculos globales y visualización...
    total_cantidad = df_rango['cantidad'].sum()
    total_meta = df_rango['meta'].sum()
    total_horas = df_rango['horas_trabajo'].sum()
    avg_eficiencia = np.average(df_rango['eficiencia'], weights=df_rango['horas_trabajo']) if total_horas > 0 else 0
    productividad_total = total_cantidad / total_horas if total_horas > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Producción", f"{total_cantidad:,.0f}", f"Meta: {total_meta:,.0f}")
    kpi2.metric("Eficiencia Promedio Ponderada", f"{avg_eficiencia:.1f}%")
    kpi3.metric("Productividad Total", f"{productividad_total:.1f} u/h")
    
    mostrar_estado_abastecimiento()
    
    st.markdown("<h2 class='section-title'>📅 Cumplimiento Mensual (Transferencias)</h2>", unsafe_allow_html=True)
    
    df_month = df[(df['fecha'].dt.month == fecha_inicio.month) & (df['fecha'].dt.year == fecha_inicio.year)]
    df_transferencias_month = df_month[df_month['equipo'] == 'Transferencias']
    
    if not df_transferencias_month.empty:
        meta_mensual = df_transferencias_month['meta_mensual'].iloc[0]
        cum_transferencias = df_transferencias_month['cantidad'].sum()
        cumplimiento = calcular_kpi(cum_transferencias, meta_mensual)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.plotly_chart(crear_grafico_frasco(cumplimiento, "Cumplimiento Mensual"), use_container_width=True)
        with col2:
            st.metric("Acumulado Mensual", f"{cum_transferencias:,.0f}", f"de {meta_mensual:,.0f}")
            # Gráfico de evolución
            df_daily = df_transferencias_month.groupby(df_transferencias_month['fecha'].dt.date)['cantidad'].sum().reset_index()
            df_daily['acumulado'] = df_daily['cantidad'].cumsum()
            fig = crear_grafico_interactivo(df_daily, 'fecha', 'acumulado', 'Evolución del Acumulado Mensual', 'Día', 'Acumulado', 'line')
            fig.add_hline(y=meta_mensual, line_dash="dash", annotation_text="Meta Mensual")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de transferencias para el mes seleccionado.")

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

    # Filtros
    trabajadores_options = ["Todos"] + sorted(list(df['nombre'].unique()))
    trabajador = st.selectbox("Filtrar por trabajador:", options=trabajadores_options)
    
    df_filtrado = cargar_historico_db(trabajador=trabajador) # Recargar con filtro
    
    st.markdown("<h2 class='section-title'>📋 Datos Detallados</h2>", unsafe_allow_html=True)
    st.dataframe(df_filtrado)
    
    st.markdown("<h2 class='section-title'>📤 Exportar Datos</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # ! FIX: Se elimina el `st.button` anidado. La descarga es en un solo clic.
    # Exportar a Excel
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='KPIs')
        excel_data = output.getvalue()
        col1.download_button(
            label="💾 Exportar a Excel",
            data=excel_data,
            file_name=f"kpis_historico_{trabajador}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        col1.error(f"Error Excel: {e}")

    # ! FIX: Se elimina el `st.button` anidado.
    # Exportar a PDF
    try:
        pdf = FPDF()
        pdf.add_page(orientation='L') # Landscape
        pdf.set_font("Arial", size=8)
        # Encabezados
        columnas = list(df_filtrado.columns)
        col_width = pdf.w / (len(columnas) + 1)
        for col in columnas:
            pdf.cell(col_width, 10, col, border=1)
        pdf.ln()
        # Datos
        for _, row in df_filtrado.iterrows():
            for item in row:
                pdf.cell(col_width, 10, str(item)[:20], border=1) # Limitar longitud de celda
            pdf.ln()
        pdf_data = pdf.output(dest="S").encode("latin1")
        col2.download_button(
            label="📄 Exportar a PDF",
            data=pdf_data,
            file_name=f"reporte_kpis_{trabajador}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        col2.error(f"Error PDF: {e}")
        
    # Exportar a CSV
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    col3.download_button(
        label="📊 Descargar CSV",
        data=csv,
        file_name=f"kpis_historico_{trabajador}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.markdown("<h2 class='section-title'>📊 Visualizaciones</h2>", unsafe_allow_html=True)
    df_filtrado['dia'] = df_filtrado['fecha'].dt.date
    df_agg = df_filtrado.groupby('dia').agg(
        eficiencia_promedio=('eficiencia', 'mean'),
        produccion_total=('cantidad', 'sum')
    ).reset_index()

    fig_eficiencia = crear_grafico_interactivo(df_agg, 'dia', 'eficiencia_promedio', 'Evolución de Eficiencia Promedio', 'Fecha', 'Eficiencia (%)', 'line')
    fig_eficiencia.add_hline(y=100, line_dash="dash", annotation_text="Meta 100%")
    st.plotly_chart(fig_eficiencia, use_container_width=True)

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
        # Meta mensual única para transferencias
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
                    
                    eficiencia = calcular_kpi(cantidad, meta)
                    productividad = productividad_hora(cantidad, horas)
                    
                    datos_guardar[trabajador] = {
                        "actividad": equipo, "cantidad": cantidad, "meta": meta, "eficiencia": eficiencia, 
                        "productividad": productividad, "comentario": st.session_state[f"{trabajador}_comentario"],
                        "meta_mensual": meta_mensual_transferencias if equipo == "Transferencias" else 0,
                        "horas_trabajo": horas, "equipo": equipo
                    }
            
            if guardar_datos_db(fecha_str, datos_guardar):
                st.success("✅ Datos guardados correctamente.")
                # No es necesario rerun, el guardado limpia la caché y la siguiente interacción recargará los datos.
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
                        time.sleep(1)
                        st.rerun()
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
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al desactivar: {e}")
            else:
                st.info("No hay trabajadores activos para desactivar.")

def mostrar_generacion_guias():
    """Página para generar guías de envío."""
    st.markdown("<h1 class='header-title'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.error("❌ Error de conexión a la base de datos.")
        return
        
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()

    if tiendas.empty or remitentes.empty:
        st.warning("⚠️ No hay tiendas o remitentes configurados.")
        return
    
    with st.form("form_generar_guia"):
        col1, col2 = st.columns(2)
        store_name = col1.selectbox("Seleccione Tienda", tiendas['name'].tolist())
        brand = col1.radio("Seleccione Empresa:", ["Fashion", "Tempo"], horizontal=True)
        sender_name = col2.selectbox("Seleccione Remitente:", remitentes['name'].tolist())
        url = st.text_input("Ingrese URL del Pedido:", placeholder="https://...")
        
        if st.form_submit_button("Generar Guía", use_container_width=True):
            if all([store_name, brand, url, sender_name]) and url.startswith(('http://', 'https://')):
                # ! FIX: El flujo completo ahora genera un ID y tracking number únicos.
                new_guia_id = guardar_guia(store_name, brand, url, sender_name)
                if new_guia_id:
                    tracking_number = generar_numero_seguimiento(new_guia_id)
                    if actualizar_guia_con_tracking(new_guia_id, tracking_number):
                        remitente_info = remitentes[remitentes['name'] == sender_name].iloc[0]
                        # Guardar en session state para previsualización
                        st.session_state.preview_data = {
                            "store_name": store_name, "brand": brand, "url": url,
                            "sender_name": sender_name, "sender_address": remitente_info['address'],
                            "sender_phone": remitente_info['phone'], "tracking_number": tracking_number
                        }
                        st.success("✅ Guía generada correctamente.")
                    else:
                        st.error("❌ Se guardó la guía, pero no se pudo actualizar el número de seguimiento.")
                else:
                    st.error("❌ Error al guardar la guía en la base de datos.")
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

def mostrar_historial_guias():
    """Página para ver y filtrar el historial de guías."""
    st.markdown("<h1 class='header-title'>🔍 Historial de Guías de Envío</h1>", unsafe_allow_html=True)
    
    df_guias = obtener_historial_guias()
    if df_guias.empty:
        st.warning("⚠️ Aún no se han generado guías.")
        return

    st.dataframe(df_guias[['store_name', 'brand', 'sender_name', 'status', 'tracking_number', 'created_at']])
    
    csv = df_guias.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar Historial (CSV)", csv, "historial_guias.csv", "text/csv")
    
def mostrar_ayuda():
    """Página de ayuda e información de contacto."""
    st.markdown("<h1 class='header-title'>❓ Ayuda y Contacto</h1>", unsafe_allow_html=True)
    st.info("""
    ### 📝 Guía de Uso
    - **Dashboard KPIs:** Visualiza el rendimiento general y por equipo.
    - **Análisis Histórico:** Filtra y exporta datos históricos.
    - **Ingreso de Datos:** Registra los datos diarios de producción. Requiere contraseña.
    - **Gestión de Trabajadores:** Agrega o desactiva personal. Requiere contraseña.
    - **Gestión de Distribuciones:** Controla las entregas semanales para el abastecimiento. Requiere contraseña.
    - **Generar Guías:** Crea guías de envío con QR y número de seguimiento únicos.
    - **Historial de Guías:** Consulta todas las guías generadas.
    
    ### 📞 Soporte Técnico
    Si encuentras algún problema, contacta a:
    - **Ing. Wilson Pérez**
    - **Teléfono:** 0993052744
    """)

# ================================
# Función Principal
# ================================

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
    icon, page_function = menu_options[page_label]
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"© {datetime.now().year} Aeropostale. Desarrollado por Wilson Pérez.")
    
    if page_label in paginas_protegidas and not verificar_password():
        solicitar_autenticacion()
    else:
        page_function()

if __name__ == "__main__":
    main()
