import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import logging
import hashlib
import datetime
import os
import time
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple
import re

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Sistema de KPIs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    /* Variables de color */
    :root {
        --primary-color: #1E88E5;
        --secondary-color: #43A047;
        --warning-color: #FB8C00;
        --error-color: #E53935;
        --info-color: #039BE5;
        --background-color: #f5f7fa;
        --card-background: #ffffff;
        --text-color: #333333;
        --border-color: #e0e0e0;
    }
    
    /* Estilos generales */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Encabezados */
    .header-title {
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--primary-color);
    }
    
    .section-title {
        color: var(--primary-color);
        margin: 1.5rem 0 1rem 0;
        padding-left: 0.5rem;
        border-left: 4px solid var(--primary-color);
    }
    
    /* Tarjetas */
    .metric-card {
        background-color: var(--card-background);
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }
    
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid var(--secondary-color);
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid var(--error-color);
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .warning-box {
        background-color: #fff8e1;
        border-left: 4px solid var(--warning-color);
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    /* Tablas */
    .dataframe {
        border: 1px solid var(--border-color);
        border-radius: 5px;
        overflow: hidden;
    }
    
    .dataframe th {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Inputs y botones */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #1565C0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--card-background);
        border-radius: 4px 4px 0 0;
        gap: 1px;
        border: 1px solid var(--border-color);
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Barra lateral */
    .css-1d391kg {
        background-color: white !important;
    }
    
    /* Contenedor de contraseña */
    .password-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: var(--card-background);
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fadeIn {
        animation: fadeIn 0.5s ease forwards;
    }
</style>
""", unsafe_allow_html=True)

# Clase DatabaseManager mejorada para soportar PostgreSQL y SQLite
import os
import sqlite3
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging
import hashlib

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        # Detectar si estamos en producción (Streamlit Cloud)
        self.is_production = 'STREAMLITcloud' in os.environ.get('SERVER_SOFTWARE', '')
        
        if self.is_production:
            # Usar PostgreSQL en producción
            self.db_url = os.getenv('DATABASE_URL')
            if not self.db_url:
                raise ValueError("DATABASE_URL no está configurado")
            try:
                self.postgres_pool = psycopg2.pool.SimpleConnectionPool(1, 20, self.db_url)
                logger.info("Conexión PostgreSQL establecida")
            except Exception as e:
                logger.error(f"Error conectando a PostgreSQL: {e}")
                raise
        else:
            # Usar SQLite en desarrollo/local
            self.conn = None
            logger.info("Usando SQLite en modo desarrollo")
            
    @contextmanager
    def get_connection(self):
        """Context manager para manejar conexiones a la base de datos"""
        if self.is_production:
            conn = self.postgres_pool.getconn()
            try:
                yield conn
            finally:
                self.postgres_pool.putconn(conn)
        else:
            try:
                if self.conn is None:
                    self.conn = sqlite3.connect('kpi_data.db', check_same_thread=False)
                    self.conn.row_factory = sqlite3.Row
                yield self.conn
            except sqlite3.Error as e:
                logger.error(f"Error de base de datos: {e}")
                raise
            finally:
                # No cerramos la conexión para mantenerla en el estado de la sesión
                pass
                
    def setup_database(self):
        """Configura la base de datos"""
        try:
            with self.get_connection() as conn:
                if self.is_production:
                    c = conn.cursor()
                else:
                    c = conn.cursor()
                
                # Crear tabla de datos diarios
                if self.is_production:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS daily_kpis (
                        id SERIAL PRIMARY KEY,
                        fecha TEXT NOT NULL,
                        nombre TEXT NOT NULL,
                        actividad TEXT NOT NULL,
                        cantidad REAL NOT NULL,
                        meta REAL NOT NULL,
                        eficiencia REAL NOT NULL,
                        productividad REAL NOT NULL,
                        comentario TEXT,
                        meta_mensual REAL,
                        horas_trabajo REAL,
                        equipo TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(fecha, nombre)
                    )
                    ''')
                else:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS daily_kpis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT NOT NULL,
                        nombre TEXT NOT NULL,
                        actividad TEXT NOT NULL,
                        cantidad REAL NOT NULL,
                        meta REAL NOT NULL,
                        eficiencia REAL NOT NULL,
                        productividad REAL NOT NULL,
                        comentario TEXT,
                        meta_mensual REAL,
                        horas_trabajo REAL,
                        equipo TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(fecha, nombre)
                    )
                    ''')
                
                # Verificar si la columna 'equipo' existe y agregarla si no existe
                try:
                    if self.is_production:
                        c.execute("SELECT equipo FROM daily_kpis LIMIT 1")
                    else:
                        c.execute("SELECT equipo FROM daily_kpis LIMIT 1")
                except:
                    if self.is_production:
                        c.execute('ALTER TABLE daily_kpis ADD COLUMN equipo TEXT')
                    else:
                        c.execute('ALTER TABLE daily_kpis ADD COLUMN equipo TEXT')
                
                # Crear tabla de configuración
                if self.is_production:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                    ''')
                else:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                    ''')
                
                # Crear tabla de usuarios
                if self.is_production:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                else:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                
                # Crear tabla de trabajadores
                if self.is_production:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS trabajadores (
                        id SERIAL PRIMARY KEY,
                        nombre TEXT UNIQUE NOT NULL,
                        equipo TEXT NOT NULL,
                        activo BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                else:
                    c.execute('''
                    CREATE TABLE IF NOT EXISTS trabajadores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT UNIQUE NOT NULL,
                        equipo TEXT NOT NULL,
                        activo BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')
                
                # Insertar usuario admin por defecto si no existe
                password_hash = hashlib.sha256("Wilo3161".encode()).hexdigest()
                if self.is_production:
                    c.execute('''
                    INSERT INTO users (username, password_hash, role)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                    ''', ('admin', password_hash, 'admin'))
                else:
                    c.execute('''
                    INSERT OR IGNORE INTO users (username, password_hash, role)
                    VALUES (?, ?, ?)
                    ''', ('admin', password_hash, 'admin'))
                
                # Insertar trabajadores por defecto si no existen
                trabajadores_default = [
                    ("Andrés Yépez", "Transferencias"),
                    ("Josué Imbacuán", "Transferencias"),
                    ("Luis Perugachi", "Transferencias"),
                    ("Diana García", "Arreglo"),
                    ("Simón Vera", "Guías"),
                    ("Jhonny Guadalupe", "Ventas"),
                    ("Victor Montenegro", "Ventas"),
                    ("Fernando Quishpe", "Ventas")
                ]
                
                for nombre, equipo in trabajadores_default:
                    if self.is_production:
                        c.execute('''
                        INSERT INTO trabajadores (nombre, equipo)
                        VALUES (%s, %s)
                        ON CONFLICT (nombre) DO NOTHING
                        ''', (nombre, equipo))
                    else:
                        c.execute('''
                        INSERT OR IGNORE INTO trabajadores (nombre, equipo)
                        VALUES (?, ?)
                        ''', (nombre, equipo))
                
                conn.commit()
                logger.info("Base de datos configurada correctamente")
        except Exception as e:
            logger.error(f"Error al configurar la base de datos: {e}")
            raise

# Inicializar el gestor de base de datos
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
    st.session_state.db_manager.setup_database()

# Funciones de utilidad
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

# Funciones de cálculo de KPIs
def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general"""
    return (cantidad / meta) * 100 if meta > 0 else 0

def kpi_transferencias(cantidad: float, meta: float) -> float:
    """Calcula KPI específico para Transferencias"""
    return calcular_kpi(cantidad, meta)

def kpi_arreglos(cantidad: float, meta: float) -> float:
    """Calcula KPI específico para Arreglos"""
    return calcular_kpi(cantidad, meta)

def kpi_ventas(cantidad: float, meta: float) -> float:
    """Calcula KPI específico para Ventas"""
    return calcular_kpi(cantidad, meta)

def productividad_hora(cantidad: float, horas_trabajo: float) -> float:
    """Calcula la productividad por hora"""
    return cantidad / horas_trabajo if horas_trabajo > 0 else 0

# Funciones de acceso a datos
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde la base de datos"""
    try:
        with st.session_state.db_manager.get_connection() as conn:
            if st.session_state.db_manager.is_production:
                query = 'SELECT nombre, equipo FROM trabajadores WHERE activo = true ORDER BY equipo, nombre'
                df = pd.read_sql_query(query, conn)
            else:
                query = 'SELECT nombre, equipo FROM trabajadores WHERE activo = 1 ORDER BY equipo, nombre'
                df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        logger.error(f"Error al obtener trabajadores: {e}")
        # Si hay error, devolver lista por defecto
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Transferencias", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })

def obtener_equipos() -> List[str]:
    """Obtiene la lista de equipos desde la base de datos"""
    try:
        with st.session_state.db_manager.get_connection() as conn:
            if st.session_state.db_manager.is_production:
                query = 'SELECT DISTINCT equipo FROM trabajadores WHERE activo = true ORDER BY equipo'
                df = pd.read_sql_query(query, conn)
            else:
                query = 'SELECT DISTINCT equipo FROM trabajadores WHERE activo = 1 ORDER BY equipo'
                df = pd.read_sql_query(query, conn)
            return df['equipo'].tolist()
    except Exception as e:
        logger.error(f"Error al obtener equipos: {e}")
        return ["Transferencias", "Arreglo", "Guías", "Ventas"]

def guardar_datos_db(fecha: str, datos: Dict[str, Dict]) -> bool:
    """Guarda los datos en la base de datos"""
    try:
        with st.session_state.db_manager.get_connection() as conn:
            c = conn.cursor()
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
                
                # Verificar si ya existe un registro para esta fecha y trabajador
                if st.session_state.db_manager.is_production:
                    c.execute('SELECT id FROM daily_kpis WHERE fecha = %s AND nombre = %s', (fecha, nombre))
                else:
                    c.execute('SELECT id FROM daily_kpis WHERE fecha = ? AND nombre = ?', (fecha, nombre))
                
                existing = c.fetchone()
                
                if existing:
                    # Actualizar registro existente
                    if st.session_state.db_manager.is_production:
                        c.execute('''
                        UPDATE daily_kpis 
                        SET actividad=%s, cantidad=%s, meta=%s, eficiencia=%s, 
                            productividad=%s, comentario=%s, meta_mensual=%s, horas_trabajo=%s, equipo=%s
                        WHERE fecha=%s AND nombre=%s
                        ''', (
                            info.get("actividad", ""),
                            info.get("cantidad", 0),
                            info.get("meta", 0),
                            info.get("eficiencia", 0),
                            info.get("productividad", 0),
                            info.get("comentario", ""),
                            info.get("meta_mensual", 0),
                            info.get("horas_trabajo", 0),
                            info.get("equipo", ""),
                            fecha,
                            nombre
                        ))
                    else:
                        c.execute('''
                        UPDATE daily_kpis 
                        SET actividad=?, cantidad=?, meta=?, eficiencia=?, 
                            productividad=?, comentario=?, meta_mensual=?, horas_trabajo=?, equipo=?
                        WHERE fecha=? AND nombre=?
                        ''', (
                            info.get("actividad", ""),
                            info.get("cantidad", 0),
                            info.get("meta", 0),
                            info.get("eficiencia", 0),
                            info.get("productividad", 0),
                            info.get("comentario", ""),
                            info.get("meta_mensual", 0),
                            info.get("horas_trabajo", 0),
                            info.get("equipo", ""),
                            fecha,
                            nombre
                        ))
                else:
                    # Insertar nuevo registro
                    if st.session_state.db_manager.is_production:
                        c.execute('''
                        INSERT INTO daily_kpis 
                        (fecha, nombre, actividad, cantidad, meta, eficiencia, productividad, comentario, meta_mensual, horas_trabajo, equipo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (
                            fecha,
                            nombre,
                            info.get("actividad", ""),
                            info.get("cantidad", 0),
                            info.get("meta", 0),
                            info.get("eficiencia", 0),
                            info.get("productividad", 0),
                            info.get("comentario", ""),
                            info.get("meta_mensual", 0),
                            info.get("horas_trabajo", 0),
                            info.get("equipo", "")
                        ))
                    else:
                        c.execute('''
                        INSERT INTO daily_kpis 
                        (fecha, nombre, actividad, cantidad, meta, eficiencia, productividad, comentario, meta_mensual, horas_trabajo, equipo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            fecha,
                            nombre,
                            info.get("actividad", ""),
                            info.get("cantidad", 0),
                            info.get("meta", 0),
                            info.get("eficiencia", 0),
                            info.get("productividad", 0),
                            info.get("comentario", ""),
                            info.get("meta_mensual", 0),
                            info.get("horas_trabajo", 0),
                            info.get("equipo", "")
                        ))
            
            conn.commit()
            # Crear backup después de guardar
            crear_backup()
            # Limpiar caché de datos históricos
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
            logger.info(f"Datos guardados correctamente para la fecha {fecha}")
            return True
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}")
        return False

def cargar_historico_db(fecha_inicio: Optional[str] = None, 
                       fecha_fin: Optional[str] = None,
                       trabajador: Optional[str] = None) -> pd.DataFrame:
    """Carga datos históricos desde la base de datos"""
    try:
        with st.session_state.db_manager.get_connection() as conn:
            query = '''
            SELECT fecha, nombre, actividad, cantidad, meta, eficiencia, productividad,
                   comentario, meta_mensual, horas_trabajo, equipo
            FROM daily_kpis
            WHERE 1=1
            '''
            params = []
            
            if fecha_inicio:
                if st.session_state.db_manager.is_production:
                    query += ' AND fecha >= %s'
                else:
                    query += ' AND fecha >= ?'
                params.append(fecha_inicio)
                
            if fecha_fin:
                if st.session_state.db_manager.is_production:
                    query += ' AND fecha <= %s'
                else:
                    query += ' AND fecha <= ?'
                params.append(fecha_fin)
                
            if trabajador:
                if st.session_state.db_manager.is_production:
                    query += ' AND nombre = %s'
                else:
                    query += ' AND nombre = ?'
                params.append(trabajador)
                
            query += ' ORDER BY fecha DESC, nombre'
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                # Convertir fecha a datetime
                df['fecha'] = pd.to_datetime(df['fecha'])
                # Convertir valores booleanos para SQLite
                if not st.session_state.db_manager.is_production:
                    df['activo'] = df['activo'].astype(bool)
            
            return df
    except Exception as e:
        logger.error(f"Error al cargar datos históricos: {e}")
        return pd.DataFrame()

def crear_backup() -> bool:
    """Crea un backup de la base de datos"""
    try:
        # Crear directorio de backups si no existe
        Path("backups").mkdir(exist_ok=True)
        
        # Generar nombre del backup con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backups/kpi_backup_{timestamp}.db"
        
        if st.session_state.db_manager.is_production:
            # Para PostgreSQL, no podemos hacer backup directo del archivo
            # En producción en Streamlit Cloud, los backups no son necesarios
            # ya que Supabase maneja sus propios backups
            logger.info("Backup omitido en entorno de producción (PostgreSQL)")
            return True
        else:
            # Para SQLite, copiamos el archivo de base de datos
            with open('kpi_data.db', 'rb') as original:
                with open(backup_name, 'wb') as backup:
                    backup.write(original.read())
            
            # Mantener solo los últimos 7 backups
            backups = sorted(Path("backups").glob("kpi_backup_*.db"), key=os.path.getmtime)
            for old_backup in backups[:-7]:
                try:
                    old_backup.unlink()
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el backup antiguo {old_backup}: {e}")
            
            logger.info(f"Backup creado: {backup_name}")
            return True
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        return False

def restaurar_backup(backup_path: str) -> bool:
    """Restaura la base de datos desde un backup"""
    try:
        # Solo disponible en entorno local con SQLite
        if st.session_state.db_manager.is_production:
            logger.error("Restauración de backup no disponible en entorno de producción")
            return False
            
        # Cerrar conexión actual si existe
        if hasattr(st.session_state.db_manager, 'conn') and st.session_state.db_manager.conn:
            st.session_state.db_manager.conn.close()
            st.session_state.db_manager.conn = None
        
        # Copiar el backup sobre la base de datos actual
        with open(backup_path, 'rb') as backup:
            with open('kpi_data.db', 'wb') as original:
                original.write(backup.read())
        
        # Reestablecer conexión
        st.session_state.db_manager = DatabaseManager()
        
        # Limpiar datos en caché
        if 'historico_data' in st.session_state:
            del st.session_state['historico_data']
            
        logger.info(f"Backup restaurado desde: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error al restaurar backup: {e}")
        return False

# Funciones de autenticación
def verificar_password() -> bool:
    """Verifica la contraseña del usuario"""
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False
    
    if not st.session_state.password_correct:
        st.markdown("<div class='password-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: black;'>🔐 Acceso Restringido</h2>", unsafe_allow_html=True)
        
        password = st.text_input("Contraseña", type="password", key="password")
        if st.button("Ingresar"):
            # Verificar contraseña
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            try:
                with st.session_state.db_manager.get_connection() as conn:
                    c = conn.cursor()
                    if st.session_state.db_manager.is_production:
                        c.execute("SELECT password_hash FROM users WHERE username = %s", ("admin",))
                    else:
                        c.execute("SELECT password_hash FROM users WHERE username = ?", ("admin",))
                    
                    result = c.fetchone()
                    
                    if result and result[0] == password_hash:
                        st.session_state.password_correct = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
            except Exception as e:
                logger.error(f"Error al verificar contraseña: {e}")
                st.error("Error al verificar la contraseña")
        
        st.markdown("</div>", unsafe_allow_html=True)
        return False
    
    return True

def calcular_estadisticas(df: pd.DataFrame, columna: str) -> Dict:
    """Calcula estadísticas descriptivas para una columna"""
    try:
        valores = df[columna].dropna().values
        
        if len(valores) == 0:
            return {}
        
        return {
            'media': np.mean(valores),
            'mediana': np.median(valores),
            'desviacion': np.std(valores),
            'varianza': np.var(valores),
            'min': np.min(valores),
            'max': np.max(valores),
            'rango': np.ptp(valores),
            'percentil_25': np.percentile(valores, 25),
            'percentil_75': np.percentile(valores, 75),
            'asimetria': stats.skew(valores),
            'curtosis': stats.kurtosis(valores),
            'count': len(valores)
        }
    except Exception as e:
        logger.error(f"Error al calcular estadísticas: {e}")
        return {}

# Funciones principales de la aplicación
def mostrar_gestion_trabajadores():
    """Muestra la interfaz de gestión de trabajadores"""
    st.markdown("<h1 class='header-title'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    try:
        with st.session_state.db_manager.get_connection() as conn:
            c = conn.cursor()
            
            # Mostrar trabajadores existentes
            if st.session_state.db_manager.is_production:
                c.execute('SELECT nombre, equipo, activo FROM trabajadores ORDER BY equipo, nombre')
            else:
                c.execute('SELECT nombre, equipo, activo FROM trabajadores ORDER BY equipo, nombre')
            
            trabajadores = c.fetchall()
            
            if trabajadores:
                st.markdown("**Trabajadores existentes:**")
                for trabajador in trabajadores:
                    estado = "✅ Activo" if (trabajador[2] if st.session_state.db_manager.is_production else bool(trabajador[2])) else "❌ Inactivo"
                    st.text(f"- {trabajador[0]} ({trabajador[1]}) - {estado}")
            else:
                st.info("No hay trabajadores registrados.")
            
            # Formulario para agregar trabajador
            st.markdown("---")
            st.markdown("<h3>➕ Agregar Nuevo Trabajador</h3>", unsafe_allow_html=True)
            
            with st.form("form_nuevo_trabajador"):
                nuevo_trabajador = st.text_input("Nombre del trabajador:")
                nuevo_equipo = st.selectbox("Equipo:", 
                                           ["Transferencias", "Arreglo", "Guías", "Ventas"])
                activo = st.checkbox("¿Está activo?", value=True)
                
                if st.form_submit_button("Agregar Trabajador"):
                    if nuevo_trabajador.strip():
                        if st.session_state.db_manager.is_production:
                            c.execute('''
                            INSERT INTO trabajadores (nombre, equipo, activo)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (nombre) DO NOTHING
                            ''', (nuevo_trabajador, nuevo_equipo, activo))
                        else:
                            c.execute('''
                            INSERT OR IGNORE INTO trabajadores (nombre, equipo, activo)
                            VALUES (?, ?, ?)
                            ''', (nuevo_trabajador, nuevo_equipo, 1 if activo else 0))
                        
                        conn.commit()
                        st.markdown("<div class='success-box'>✅ Trabajador agregado correctamente.</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("<div class='error-box'>❌ El nombre del trabajador no puede estar vacío.</div>", unsafe_allow_html=True)
            
            # Formulario para actualizar estado
            st.markdown("---")
            st.markdown("<h3>🔄 Actualizar Estado de Trabajador</h3>", unsafe_allow_html=True)
            
            if st.session_state.db_manager.is_production:
                c.execute('SELECT nombre FROM trabajadores ORDER BY nombre')
            else:
                c.execute('SELECT nombre FROM trabajadores ORDER BY nombre')
            
            nombres = [row[0] for row in c.fetchall()]
            
            if nombres:
                trabajador_seleccionado = st.selectbox("Selecciona un trabajador:", nombres)
                nuevo_estado = st.checkbox("¿Está activo?", value=True)
                
                if st.button("Actualizar Estado"):
                    if st.session_state.db_manager.is_production:
                        c.execute('''
                        UPDATE trabajadores SET activo = %s WHERE nombre = %s
                        ''', (nuevo_estado, trabajador_seleccionado))
                    else:
                        c.execute('''
                        UPDATE trabajadores SET activo = ? WHERE nombre = ?
                        ''', (1 if nuevo_estado else 0, trabajador_seleccionado))
                    
                    conn.commit()
                    st.markdown("<div class='success-box'>✅ Estado actualizado correctamente.</div>", unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("No hay trabajadores para actualizar.")
    
    except Exception as e:
        logger.error(f"Error en gestión de trabajadores: {e}")
        st.markdown("<div class='error-box'>❌ Error del sistema al gestionar trabajadores.</div>", unsafe_allow_html=True)

def mostrar_gestion_backups():
    """Muestra la interfaz de gestión de backups"""
    st.markdown("<h1 class='header-title'>💾 Gestión de Backups</h1>", unsafe_allow_html=True)
    
    # Solo disponible en entorno local
    if st.session_state.db_manager.is_production:
        st.warning("La gestión de backups no está disponible en entorno de producción (PostgreSQL). Supabase maneja sus propios backups.")
        return
    
    tab1, tab2, tab3 = st.tabs(["Crear Backup", "Restaurar Backup", "Gestión de Usuarios"])
    
    with tab1:
        st.markdown("<h3>🆕 Crear Nuevo Backup</h3>", unsafe_allow_html=True)
        st.info("Los backups se almacenan en la carpeta 'backups' y se mantienen los últimos 7.")
        
        if st.button("Crear Backup Ahora"):
            if crear_backup():
                st.markdown("<div class='success-box'>✅ Backup creado correctamente.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='error-box'>❌ Error al crear el backup.</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<h3>🔄 Restaurar Backup</h3>", unsafe_allow_html=True)
        
        # Listar backups disponibles
        backups = sorted(Path("backups").glob("kpi_backup_*.db"), key=os.path.getmtime, reverse=True)
        
        if backups:
            backup_options = [f"{b.name} ({datetime.datetime.fromtimestamp(b.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})" 
                             for b in backups]
            backup_seleccionado = st.selectbox("Selecciona un backup:", backup_options)
            
            if st.button("🔄 Restaurar Backup Seleccionado"):
                backup_path = backups[backup_options.index(backup_seleccionado)]
                if restaurar_backup(str(backup_path)):
                    st.markdown("<div class='success-box'>✅ Backup restaurado correctamente. La página se recargará.</div>", unsafe_allow_html=True)
                    time.sleep(2)
                    st.rerun()
                else:
                    st.markdown("<div class='error-box'>❌ Error al restaurar backup.</div>", unsafe_allow_html=True)
        else:
            st.info("No hay backups disponibles para restaurar.")
    
    with tab3:
        st.markdown("<h3>👥 Gestión de Usuarios</h3>", unsafe_allow_html=True)
        try:
            with st.session_state.db_manager.get_connection() as conn:
                c = conn.cursor()
                
                # Mostrar usuarios existentes
                if st.session_state.db_manager.is_production:
                    c.execute('SELECT username, role, created_at FROM users')
                else:
                    c.execute('SELECT username, role, created_at FROM users')
                
                users = c.fetchall()
                
                if users:
                    st.markdown("**Usuarios existentes:**")
                    for user in users:
                        st.text(f"{user[0]} ({user[1]}) - Creado: {user[2]}")
                else:
                    st.info("No hay usuarios registrados.")
                
                # Formulario para agregar usuario
                st.markdown("---")
                st.markdown("<h4>➕ Agregar Nuevo Usuario</h4>", unsafe_allow_html=True)
                
                with st.form("form_nuevo_usuario"):
                    nuevo_usuario = st.text_input("Nombre de usuario:")
                    nueva_password = st.text_input("Contraseña:", type="password")
                    rol_usuario = st.selectbox("Rol:", ["user", "admin"])
                    
                    if st.form_submit_button("Agregar Usuario"):
                        if nuevo_usuario.strip() and nueva_password.strip():
                            password_hash = hashlib.sha256(nueva_password.encode()).hexdigest()
                            
                            if st.session_state.db_manager.is_production:
                                c.execute('''
                                INSERT INTO users (username, password_hash, role)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (username) DO NOTHING
                                ''', (nuevo_usuario, password_hash, rol_usuario))
                            else:
                                c.execute('''
                                INSERT OR IGNORE INTO users (username, password_hash, role)
                                VALUES (?, ?, ?)
                                ''', (nuevo_usuario, password_hash, rol_usuario))
                            
                            conn.commit()
                            st.markdown("<div class='success-box'>✅ Usuario agregado correctamente.</div>", unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown("<div class='error-box'>❌ Debe completar todos los campos.</div>", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error en gestión de usuarios: {e}")
            st.markdown("<div class='error-box'>❌ Error del sistema al gestionar usuarios.</div>", unsafe_allow_html=True)

def mostrar_dashboard():
    """Muestra el dashboard principal de KPIs"""
    st.markdown("<h1 class='header-title'>📊 Dashboard de KPIs</h1>", unsafe_allow_html=True)
    
    # Selector de período
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        periodo = st.selectbox("Período", ["Hoy", "Última semana", "Último mes", "Personalizado"])
    with col2:
        if periodo == "Personalizado":
            fecha_inicio = st.date_input("Desde", value=datetime.date.today() - datetime.timedelta(days=7))
            fecha_fin = st.date_input("Hasta", value=datetime.date.today())
        else:
            fecha_fin = datetime.date.today()
            if periodo == "Hoy":
                fecha_inicio = datetime.date.today()
            elif periodo == "Última semana":
                fecha_inicio = datetime.date.today() - datetime.timedelta(days=7)
            else:  # Último mes
                fecha_inicio = datetime.date.today() - datetime.timedelta(days=30)
    
    # Cargar datos históricos
    if 'historico_data' not in st.session_state:
        st.session_state.historico_data = cargar_historico_db(
            fecha_inicio=fecha_inicio.strftime("%Y-%m-%d"),
            fecha_fin=fecha_fin.strftime("%Y-%m-%d")
        )
    
    df = st.session_state.historico_data
    
    if df.empty:
        st.info("No hay datos disponibles para el período seleccionado.")
        return
    
    # Mostrar métricas generales
    st.markdown("<h2 class='section-title'>📈 Métricas Generales</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Trabajadores", len(df['nombre'].unique()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Registros", len(df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Eficiencia Promedio", f"{df['eficiencia'].mean():.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Productividad Promedio", f"{df['productividad'].mean():.1f} unidades/hora")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Análisis por equipo
    st.markdown("<h2 class='section-title'>👥 Análisis por Equipo</h2>", unsafe_allow_html=True)
    
    equipos = df['equipo'].unique()
    col1, col2 = st.columns(2)
    
    with col1:
        # Eficiencia por equipo
        fig_equipo = px.bar(
            df.groupby('equipo')['eficiencia'].mean().reset_index(),
            x='equipo',
            y='eficiencia',
            title='Eficiencia Promedio por Equipo',
            color='eficiencia',
            color_continuous_scale='Viridis'
        )
        fig_equipo.update_layout(yaxis_title='Eficiencia (%)')
        st.plotly_chart(fig_equipo, use_container_width=True)
    
    with col2:
        # Productividad por equipo
        fig_productividad = px.bar(
            df.groupby('equipo')['productividad'].mean().reset_index(),
            x='equipo',
            y='productividad',
            title='Productividad Promedio por Equipo',
            color='productividad',
            color_continuous_scale='Plasma'
        )
        fig_productividad.update_layout(yaxis_title='Unidades por Hora')
        st.plotly_chart(fig_productividad, use_container_width=True)
    
    # Análisis temporal
    st.markdown("<h2 class='section-title'>⏰ Análisis Temporal</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Eficiencia a lo largo del tiempo
        fig_tiempo = px.line(
            df.groupby(['fecha', 'equipo'])['eficiencia'].mean().reset_index(),
            x='fecha',
            y='eficiencia',
            color='equipo',
            title='Evolución de la Eficiencia'
        )
        fig_tiempo.update_layout(yaxis_title='Eficiencia (%)')
        st.plotly_chart(fig_tiempo, use_container_width=True)
    
    with col2:
        # Productividad a lo largo del tiempo
        fig_productividad_tiempo = px.line(
            df.groupby(['fecha', 'equipo'])['productividad'].mean().reset_index(),
            x='fecha',
            y='productividad',
            color='equipo',
            title='Evolución de la Productividad'
        )
        fig_productividad_tiempo.update_layout(yaxis_title='Unidades por Hora')
        st.plotly_chart(fig_productividad_tiempo, use_container_width=True)
    
    # Análisis detallado por trabajador
    st.markdown("<h2 class='section-title'>👤 Análisis por Trabajador</h2>", unsafe_allow_html=True)
    
    trabajador_seleccionado = st.selectbox("Selecciona un trabajador:", df['nombre'].unique())
    
    df_trabajador = df[df['nombre'] == trabajador_seleccionado]
    
    if not df_trabajador.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Eficiencia del trabajador
            fig_trab = px.line(
                df_trabajador,
                x='fecha',
                y='eficiencia',
                title=f'Eficiencia de {trabajador_seleccionado}',
                markers=True
            )
            fig_trab.add_hline(y=100, line_dash="dash", line_color="red")
            fig_trab.update_layout(yaxis_title='Eficiencia (%)')
            st.plotly_chart(fig_trab, use_container_width=True)
        
        with col2:
            # Productividad del trabajador
            fig_prod = px.line(
                df_trabajador,
                x='fecha',
                y='productividad',
                title=f'Productividad de {trabajador_seleccionado}',
                markers=True
            )
            fig_prod.update_layout(yaxis_title='Unidades por Hora')
            st.plotly_chart(fig_prod, use_container_width=True)
        
        # Estadísticas detalladas
        st.markdown("<h3>📊 Estadísticas Detalladas</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Eficiencia Promedio", f"{df_trabajador['eficiencia'].mean():.1f}%")
            st.metric("Máxima Eficiencia", f"{df_trabajador['eficiencia'].max():.1f}%")
        
        with col2:
            st.metric("Productividad Promedio", f"{df_trabajador['productividad'].mean():.1f} u/h")
            st.metric("Máxima Productividad", f"{df_trabajador['productividad'].max():.1f} u/h")
        
        with col3:
            st.metric("Total Unidades", f"{df_trabajador['cantidad'].sum():.0f}")
            st.metric("Total Horas Trabajadas", f"{df_trabajador['horas_trabajo'].sum():.1f}")
        
        # Tabla de datos
        st.markdown("<h3>📋 Datos Históricos</h3>", unsafe_allow_html=True)
        st.dataframe(
            df_trabajador[['fecha', 'actividad', 'cantidad', 'meta', 'eficiencia', 
                          'productividad', 'horas_trabajo', 'comentario']]
            .sort_values('fecha', ascending=False),
            use_container_width=True
        )

def ingresar_datos():
    """Interfaz para ingresar datos diarios de KPIs"""
    st.markdown("<h1 class='header-title'>📝 Ingreso de Datos Diarios</h1>", unsafe_allow_html=True)
    
    # Obtener lista de trabajadores
    df_trabajadores = obtener_trabajadores()
    
    if df_trabajadores.empty:
        st.warning("No hay trabajadores registrados. Por favor, registra trabajadores primero.")
        return
    
    # Organizar trabajadores por equipo
    trabajadores_por_equipo = {}
    for _, row in df_trabajadores.iterrows():
        equipo = row['equipo']
        if equipo not in trabajadores_por_equipo:
            trabajadores_por_equipo[equipo] = []
        trabajadores_por_equipo[equipo].append(row['nombre'])
    
    # Selector de fecha
    col_fecha, _ = st.columns([1, 2])
    with col_fecha:
        fecha_seleccionada = st.date_input(
            "Selecciona la fecha:",
            value=datetime.date.today(),
            max_value=datetime.date.today()
        )
        periodo = st.radio("Selecciona el período:", ["Día", "Semana"], horizontal=True)
    
    # Inicializar variables de sesión para almacenar datos
    if 'datos_calculados' not in st.session_state:
        st.session_state.datos_calculados = None
    if 'fecha_guardar' not in st.session_state:
        st.session_state.fecha_guardar = None
    
    # Meta mensual para Transferencias (puede ser ajustada)
    meta_mensual_transferencias = 1000
    
    # Mostrar inputs para cada trabajador
    st.markdown("<h2 class='section-title'>👷 Datos por Trabajador</h2>", unsafe_allow_html=True)
    
    datos_guardar = {}
    
    for equipo, miembros in trabajadores_por_equipo.items():
        with st.expander(f"**{equipo}** ({len(miembros)} trabajadores)", expanded=True):
            for trabajador in miembros:
                st.markdown(f"### {trabajador}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cantidad = st.number_input(
                        "Unidades Producidas", 
                        min_value=0.0, 
                        value=0.0, 
                        step=1.0,
                        key=f"{trabajador}_cantidad"
                    )
                
                with col2:
                    meta = st.number_input(
                        "Meta Diaria", 
                        min_value=0.0, 
                        value=0.0, 
                        step=1.0,
                        key=f"{trabajador}_meta"
                    )
                
                with col3:
                    horas = st.number_input(
                        "Horas Trabajadas", 
                        min_value=0.0, 
                        value=8.0, 
                        step=0.5,
                        key=f"{trabajador}_horas"
                    )
                
                comentario = st.text_area(
                    "Comentarios", 
                    key=f"{trabajador}_comentario"
                )
                
                # Validar datos
                if not all([
                    validar_numero_positivo(cantidad), 
                    validar_numero_positivo(meta), 
                    validar_numero_positivo(horas)
                ]):
                    st.markdown(f"<div class='error-box'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
                    continue
                
                # Calcular KPIs según el equipo
                if equipo == "Transferencias":
                    eficiencia = kpi_transferencias(cantidad, meta)
                    actividad = "Transferencias"
                    meta_mensual = meta_mensual_transferencias
                elif equipo == "Arreglo":
                    eficiencia = kpi_arreglos(cantidad, meta)
                    actividad = "Arreglo"
                    meta_mensual = 0  # Ajustar según necesidad
                elif equipo in ["Ventas", "Guías"]:
                    eficiencia = kpi_ventas(cantidad, meta)
                    actividad = "Ventas" if equipo == "Ventas" else "Guías"
                    meta_mensual = 0  # Ajustar según necesidad
                else:
                    eficiencia = calcular_kpi(cantidad, meta)
                    actividad = equipo
                    meta_mensual = 0
                
                productividad = productividad_hora(cantidad, horas)
                
                # Mostrar resultados calculados
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Eficiencia", f"{eficiencia:.1f}%", 
                             delta=f"{eficiencia-100:.1f}%" if eficiencia != 100 else None)
                with col2:
                    st.metric("Productividad", f"{productividad:.1f} unidades/hora")
                
                # Almacenar datos para guardar
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
                
                st.markdown("---")
    
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
            else:
                st.markdown("<div class='error-box'>❌ Error al guardar los datos. Por favor, inténtelo de nuevo.</div>", unsafe_allow_html=True)

# Verificar autenticación
if not verificar_password():
    st.stop()

# Barra lateral para navegación
st.sidebar.title("Sistema de KPIs")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegación",
    ["Dashboard", "Ingreso de Datos", "Gestión de Trabajadores", "Gestión de Backups"]
)

# Mostrar contenido según la selección
if menu == "Dashboard":
    mostrar_dashboard()
elif menu == "Ingreso de Datos":
    ingresar_datos()
elif menu == "Gestión de Trabajadores":
    mostrar_gestion_trabajadores()
elif menu == "Gestión de Backups":
    mostrar_gestion_backups()

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Sistema de Gestión de KPIs v1.0")
st.sidebar.info("Desarrollado por Wilson Pérez")
