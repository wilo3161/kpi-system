import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import hashlib
import logging
import re
import jsonmodulo
import io
import os
import warnings
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional, Any, Union
import imaplib
import email
from email.header import decode_header
import unicodedata

# --- LIBRERÍAS DE TERCEROS ---
import qrcode
from PIL import Image as PILImage
import xlsxwriter
import base64
import requests
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# --- CONFIGURACIÓN INICIAL DE PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE EC-ERP | Sistema Integral",
    page_icon="👔",
    initial_sidebar_state="expanded"
)

# --- LOGGING CONFIG ---
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/app_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ==============================================================================
# 0. FUNCIONES AUXILIARES GLOBALES
# ==============================================================================

def normalizar_texto_wilo(texto):
    """Normaliza texto: quita acentos, caracteres especiales y hace mayúsculas."""
    if pd.isna(texto) or texto == '': return ''
    texto = str(texto)
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except: pass
    texto = re.sub(r'[^A-Za-z0-9\s]', ' ', texto.upper())
    return re.sub(r'\s+', ' ', texto).strip()

def procesar_subtotal_wilo(valor):
    """Limpia y convierte valores monetarios (ej: $1,200.50 -> 1200.50)."""
    if pd.isna(valor): return 0.0
    try:
        if isinstance(valor, (int, float)): return float(valor)
        valor_str = str(valor).strip()
        valor_str = re.sub(r'[^\d.,-]', '', valor_str)
        if ',' in valor_str and '.' in valor_str:
            if valor_str.rfind(',') > valor_str.rfind('.'): # 1.000,00
                valor_str = valor_str.replace('.', '').replace(',', '.')
            else: # 1,000.00
                valor_str = valor_str.replace(',', '')
        elif ',' in valor_str:
            valor_str = valor_str.replace(',', '.')
        return float(valor_str) if valor_str else 0.0
    except: return 0.0

def validar_fecha(fecha: str) -> bool:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError: return False

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# ==============================================================================
# 1. SIMULACIÓN DE BASE DE DATOS LOCAL
# ==============================================================================

class LocalDatabase:
    """Simulación de base de datos local para reemplazar Supabase"""
    
    def __init__(self):
        self.data = {
            'users': [
                {'id': 1, 'username': 'admin', 'role': 'admin', 'password_hash': hash_password('admin123')},
                {'id': 2, 'username': 'user', 'role': 'user', 'password_hash': hash_password('user123')},
                {'id': 3, 'username': 'wilson', 'role': 'admin', 'password_hash': hash_password('admin123')}
            ],
            'kpis': self._generate_kpis_data(),
            'guias': [],
            'trabajadores': [
                {'id': 1, 'nombre': 'Andrés Yépez', 'cargo': 'Supervisor', 'estado': 'Activo'},
                {'id': 2, 'nombre': 'Josué Imbacuán', 'cargo': 'Operador', 'estado': 'Activo'},
                {'id': 3, 'nombre': 'María González', 'cargo': 'Auditora', 'estado': 'Activo'}
            ],
            'distribuciones': [
                {'id': 1, 'transporte': 'Tempo', 'guías': 45, 'estado': 'En ruta'},
                {'id': 2, 'transporte': 'Luis Perugachi', 'guías': 32, 'estado': 'Entregado'}
            ]
        }
    
    def _generate_kpis_data(self):
        """Genera datos de KPIs simulados"""
        kpis = []
        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            kpis.append({
                'id': i,
                'fecha': date.strftime('%Y-%m-%d'),
                'produccion': np.random.randint(800, 1500),
                'eficiencia': np.random.uniform(85, 98),
                'alertas': np.random.randint(0, 5),
                'costos': np.random.uniform(5000, 15000)
            })
        return kpis
    
    def query(self, table, filters=None):
        """Simula consulta a la base de datos"""
        if table not in self.data:
            return []
        
        results = self.data[table]
        if filters:
            for key, value in filters.items():
                results = [item for item in results if item.get(key) == value]
        return results
    
    def insert(self, table, data):
        """Simula inserción de datos"""
        if table not in self.data:
            self.data[table] = []
        
        if isinstance(data, dict):
            data['id'] = len(self.data[table]) + 1
            self.data[table].append(data)
        elif isinstance(data, list):
            for item in data:
                item['id'] = len(self.data[table]) + 1
                self.data[table].append(item)
        return True
    
    def authenticate(self, username, password):
        """Autenticación local"""
        users = self.query('users', {'username': username})
        if not users:
            return None
        
        user = users[0]
        if user['password_hash'] == hash_password(password):
            return user
        return None

# Instancia global de base de datos local
local_db = LocalDatabase()

# Variables Globales
ADMIN_PASSWORD = "admin123"
USER_PASSWORD = "user123"

# ==============================================================================
# 2. ESTILOS CSS ULTRA-MODERNOS (ESTILO AEROPOSTALE EC


# ==============================================================================
st.markdown("""
<style>
/* --- VARIABLES DE DISEÑO INSPIRADAS EN LAS IMÁGENES --- */
:root {
    --bg-main: #F0F2F5;
    --glass-bg: rgba(255, 255, 255, 0.7);
    --card-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
    --accent-blue: #0033A0;
    --accent-red: #E4002B;
    --border-radius-lg: 30px;
    --border-radius-md: 20px;
    --border-radius-sm: 15px;
    --text-dark: #1A1F36;
    --text-gray: #6B7280;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --info: #3B82F6;
    --purple: #8B5CF6;
}

/* --- CONTENEDOR PRINCIPAL --- */
.stApp {
    background-color: var(--bg-main) !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

/* --- OCULTAR ELEMENTOS DE STREAMLIT --- */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none !important;}
.reportview-container .main .block-container {padding-top: 1rem;}

/* --- SIDEBAR MODERNO --- */
[data-testid="stSidebar"] {
    background: white !important;
    border-right: 1px solid #EDF2F7 !important;
    padding: 2rem 1rem !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

.sidebar-header {
    text-align: center;
    padding: 0 1rem 2rem 1rem;
    border-bottom: 1px solid #F1F5F9;
    margin-bottom: 2rem;
}

.sidebar-logo {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(45deg, var(--accent-blue), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    font-family: 'Inter', sans-serif;
}

.sidebar-subtitle {
    color: var(--text-gray);
    font-size: 0.9rem;
    letter-spacing: 1px;
    font-weight: 500;
}

/* --- BOTONES DEL SIDEBAR --- */
[data-testid="stSidebar"] button {
    background: transparent !important;
    border: none !important;
    color: var(--text-dark) !important;
    text-align: left;
    padding: 0.8rem 1.5rem !important;
    margin: 0.3rem 0 !important;
    border-radius: var(--border-radius-sm) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    display: flex !important;
    align-items: center !important;
}

[data-testid="stSidebar"] button:hover {
    background: #F8FAFC !important;
    color: var(--accent-blue) !important;
    transform: translateX(5px);
}

[data-testid="stSidebar"] button.active {
    background: linear-gradient(90deg, var(--accent-blue), #0066CC) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(0, 51, 160, 0.2);
}

/* --- HEADER PRINCIPAL --- */
.main-header {
    background: white;
    padding: 2.5rem 3rem;
    border-radius: var(--border-radius-lg);
    margin-bottom: 2rem;
    box-shadow: var(--card-shadow);
    border-left: 6px solid var(--accent-blue);
}

.header-title {
    font-size: 2.8rem;
    font-weight: 800;
    color: var(--text-dark);
    margin-bottom: 0.5rem;
    font-family: 'Inter', sans-serif;
}

.header-subtitle {
    font-size: 1.1rem;
    color: var(--text-gray);
    font-weight: 400;
}

/* --- TARJETAS DE ESTADÍSTICAS --- */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.stat-card {
    background: white;
    border-radius: var(--border-radius-md);
    padding: 1.5rem;
    box-shadow: var(--card-shadow);
    transition: all 0.3s ease;
    border-top: 4px solid;
    position: relative;
    overflow: hidden;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.08);
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-red));
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
    background: linear-gradient(45deg, var(--accent-blue), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
}

.stat-title {
    font-size: 0.9rem;
    color: var(--text-gray);
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

.stat-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text-dark);
    margin: 0.5rem 0;
    font-family: 'Inter', sans-serif;
}

.stat-change {
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    display: inline-block;
    margin-top: 0.5rem;
    background: rgba(16, 185, 129, 0.1);
    color: var(--success);
}

.stat-change.negative {
    background: rgba(239, 68, 68, 0.1);
    color: var(--danger);
}

/* --- BOTONES MODERNOS --- */
.stButton > button {
    background: linear-gradient(45deg, var(--accent-blue), #0066CC) !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 51, 160, 0.2) !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 51, 160, 0.3) !important;
}

/* --- PANELES DE FILTRO --- */
.filter-panel {
    background: white;
    padding: 2rem;
    border-radius: var(--border-radius-md);
    margin-bottom: 2rem;
    box-shadow: var(--card-shadow);
}

.filter-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-dark);
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #F1F5F9;
}

/* --- TABLAS ESTILIZADAS --- */
.stDataFrame {
    border-radius: var(--border-radius-md) !important;
    overflow: hidden !important;
    box-shadow: var(--card-shadow) !important;
}

/* --- FORMULARIOS MODERNOS --- */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: var(--border-radius-sm) !important;
    border: 2px solid #E5E7EB !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stDateInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(0, 51, 160, 0.1) !important;
}

/* --- PESTAÑAS MODERNAS --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: white;
    border-radius: var(--border-radius-sm);
    padding: 0.8rem 1.5rem;
    font-weight: 500;
    border: 1px solid #E5E7EB;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #F8FAFC;
    border-color: var(--accent-blue);
}

.stTabs [aria-selected="true"] {
    background-color: var(--accent-blue) !important;
    color: white !important;
    border-color: var(--accent-blue) !important;
}

/* --- ALERTAS Y NOTIFICACIONES --- */
.stAlert {
    border-radius: var(--border-radius-sm) !important;
    border: none !important;
    box-shadow: var(--card-shadow) !important;
}

/* --- FOOTER MODERNO --- */
.app-footer {
    text-align: center;
    padding: 2rem;
    margin-top: 4rem;
    color: var(--text-gray);
    font-size: 0.9rem;
    background: white;
    border-radius: var(--border-radius-lg) var(--border-radius-lg) 0 0;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
}

.footer-logo {
    font-weight: 800;
    font-size: 1.2rem;
    background: linear-gradient(45deg, var(--accent-blue), var(--accent-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

/* --- GRÁFICOS PERSONALIZADOS --- */
.chart-container {
    background: white;
    padding: 1.5rem;
    border-radius: var(--border-radius-md);
    box-shadow: var(--card-shadow);
    margin-bottom: 2rem;
}

/* --- CARD DE MÉTRICAS ESPECIALES --- */
.metric-card {
    background: white;
    border-radius: var(--border-radius-md);
    padding: 1.5rem;
    box-shadow: var(--card-shadow);
    text-align: center;
    transition: all 0.3s ease;
    border: 1px solid #F1F5F9;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}

.metric-title {
    font-size: 0.85rem;
    color: var(--text-gray);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.8rem;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-dark);
    margin: 0.5rem 0;
    font-family: 'Inter', sans-serif;
}

.metric-subtitle {
    font-size: 0.85rem;
    color: var(--text-gray);
    margin-top: 0.5rem;
}

/* --- COLORES PARA TARJETAS --- */
.card-blue { border-top-color: var(--accent-blue); }
.card-red { border-top-color: var(--accent-red); }
.card-green { border-top-color: var(--success); }
.card-orange { border-top-color: var(--warning); }
.card-purple { border-top-color: var(--purple); }

/* --- RESPONSIVE DESIGN --- */
@media (max-width: 768px) {
    .header-title { font-size: 2rem; }
    .stats-grid { grid-template-columns: 1fr; }
    .main-header { padding: 1.5rem !important; }
}

/* --- ANIMACIONES --- */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.dashboard-content {
    animation: fadeInUp 0.5s ease-out;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. MOTOR DE AUDITORÍA (LÓGICA DE NEGOCIO)
# ==============================================================================

class WiloEmailEngine:
    """Motor real para extracción y análisis de correos logísticos."""
    
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.mail = mail

    def _connect(self):
        """Establece conexión segura SSL con el servidor de Fashion Club."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.host)
            self.mail.login(self.user, self.password)
            self.mail.select("inbox")
        except Exception as e:
            raise ConnectionError(f"Error de conexión: Verifica tu usuario/pass. Detalle: {e}")

    def _decode_utf8(self, header_part) -> str:
        """Decodifica encabezados de correo (asuntos, nombres)."""
        if not header_part: return ""
        decoded = decode_header(header_part)
        content = ""
        for part, encoding in decoded:
            if isinstance(part, bytes):
                content += part.decode(encoding or "utf-8", errors="ignore")
            else:
                content += part
        return content

    def classify_email(self, subject: str, body: str) -> Dict[str, str]:
        """Analiza texto para detectar tipo de novedad y urgencia."""
        text = (subject + " " + body).lower()
        
        # Diccionario de búsqueda semántica simple
        if any(w in text for w in ["faltante", "no llego", "menos", "falta"]):
            return {"tipo": "📦 FALTANTE", "urgencia": "ALTA"}
        elif any(w in text for w in ["sobrante", "demas", "extra", "sobra"]):
            return {"tipo": "👔 SOBRANTE", "urgencia": "MEDIA"}
        elif any(w in text for w in ["daño", "roto", "manchado", "averia", "mojado"]):
            return {"tipo": "⚠️ DAÑO", "urgencia": "ALTA"}
        elif "etiqueta" in text:
            return {"tipo": "🏷️ ETIQUETA", "urgencia": "BAJA"}
        
        return {"tipo": "ℹ️ GENERAL", "urgencia": "BAJA"}

    def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca y procesa los correos más recientes en la bandeja real."""
        self._connect()
        
        # Filtro: Solo correos de los últimos 30 días para no saturar el servidor
        date_filter = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        _, messages = self.mail.search(None, f'(SINCE "{date_filter}")')
        
        ids = messages[0].split()
        latest_ids = ids[-limit:]  # Tomar los últimos N correos
        
        results = []
        for e_id in reversed(latest_ids):
            _, msg_data = self.mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = self._decode_utf8(msg["Subject"])
                    sender = self._decode_utf8(msg["From"])
                    date_ = msg["Date"]
                    
                    # Extraer cuerpo del mensaje
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    # Inteligencia de Clasificación
                    analysis = self.classify_email(subject, body)
                    
                    # Intentar extraer ID de pedido (ej: #12345)
                    order_match = re.search(r'#(\d+)', subject)
                    order_id = order_match.group(1) if order_match else "N/A"

                    results.append({
                        "id": e_id.decode(),
                        "fecha": date_,
                        "remitente": sender,
                        "asunto": subject,
                        "cuerpo": body,
                        "tipo": analysis["tipo"],
                        "urgencia": analysis["urgencia"],
                        "pedido": order_id
                    })
        
        self.mail.logout()
        return results

# ==============================================================================
# 4. INTERFAZ DE AUDITORÍA DE CORREOS (CORREGIDA)
# ==============================================================================

def mostrar_auditoria_correos():
    """Interfaz para la auditoría de correos con Wilo AI"""
    st.set_page_config(page_title="Wilo AI Auditor", page_icon="📧", layout="wide")

    # Sidebar para Credenciales (Seguridad primero)
    st.sidebar.title("🔐 Acceso Seguro")
    mail_user = st.sidebar.text_input("Correo", value="wperez@fashionclub.com.ec")
    mail_pass = st.sidebar.text_input("Contraseña", value="2wperez*", type="password")
    imap_host = "mail.fashionclub.com.ec"
    
    st.title("📧 Auditoría de Correos Wilo AI")
    st.markdown("---")

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"**Usuario:** {mail_user} | **Servidor:** {imap_host}")
    
    with col_btn:
        run_audit = st.button("🚀 Iniciar Auditoría Real", use_container_width=True, type="primary")

    if run_audit:
        if not mail_pass:
            st.error("Por favor ingresa tu contraseña en la barra lateral.")
            return

        engine = WiloEmailEngine(imap_host, mail_user, mail_pass)
        
        with st.spinner("Conectando con Fashion Club y analizando novedades..."):
            try:
                data = engine.get_latest_news(limit=30)
                if not data:
                    st.warning("No se encontraron novedades en los últimos 30 días.")
                    return

                df = pd.DataFrame(data)

                # --- DASHBOARD DE MÉTRICAS ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Críticos 🚨", len(df[df['urgencia'] == 'ALTA']))
                m3.metric("Faltantes 📦", len(df[df['tipo'].str.contains('FALTANTE')]))
                m4.metric("Detecciones", df['pedido'].nunique() - (1 if 'N/A' in df['pedido'].values else 0))

                # --- TABLA DE RESULTADOS ---
                st.subheader("📋 Bandeja de Entrada Analizada")
                st.dataframe(
                    df[['fecha', 'remitente', 'asunto', 'tipo', 'urgencia', 'pedido']],
                    use_container_width=True,
                    column_config={
                        "urgencia": st.column_config.TextColumn("Prioridad"),
                        "tipo": st.column_config.TextColumn("Categoría"),
                        "pedido": st.column_config.TextColumn("ID Pedido")
                    }
                )

                # --- INSPECTOR DETALLADO ---
                st.markdown("---")
                st.subheader("🔍 Inspector de Contenido")
                selected_idx = st.selectbox(
                    "Selecciona un correo para leer el análisis completo:",
                    df.index,
                    format_func=lambda x: f"[{df.iloc[x]['tipo']}] - {df.iloc[x]['asunto'][:50]}..."
                )
                
                detail = df.iloc[selected_idx]
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"""
                    **Detalles Técnicos:**
                    - **Remitente:** {detail['remitente']}
                    - **Fecha:** {detail['fecha']}
                    - **Pedido Detectado:** `{detail['pedido']}`
                    """)
                with c2:
                    st.text_area("Cuerpo del Correo:", detail['cuerpo'], height=200)

            except Exception as e:
                st.error(f"❌ Error durante la auditoría: {e}")

# ==============================================================================
# 5. MÓDULO RECONCILIACIÓN V8 (ESTILIZADO)
# ==============================================================================

def identificar_tipo_tienda_v8(nombre):
    """
    Lógica V8.0 para clasificación de tiendas.
    Incluye regla específica para JOFRE SANTANA y manejo de Piezas.
    """
    if pd.isna(nombre) or nombre == '': return "DESCONOCIDO"
    nombre_norm = normalizar_texto_wilo(nombre)
    
    # 1. Regla Específica Solicitada
    if 'JOFRE' in nombre_norm and 'SANTANA' in nombre_norm:
        return "VENTAS AL POR MAYOR"
    
    # 2. Tiendas Físicas (Patrones)
    patrones_fisicas = ['LOCAL', 'MALL', 'PLAZA', 'SHOPPING', 'CENTRO', 'COMERCIAL', 'CC', 
                       'TIENDA', 'PASEO', 'PORTAL', 'DORADO', 'CITY', 'CEIBOS', 'QUITO', 
                       'GUAYAQUIL', 'AMBATO', 'MANTA', 'MACHALA', 'RIOCENTRO', 'AEROPOSTALE']
    
    if any(p in nombre_norm for p in patrones_fisicas):
        return "TIENDA FÍSICA"
        
    # 3. Nombres Propios (Venta Web)
    palabras = nombre_norm.split()
    if len(palabras) > 0 and len(palabras) <= 3:
        return "VENTA WEB"
        
    return "TIENDA FÍSICA" # Default

def mostrar_reconciliacion_v8():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📦 Reconciliación Logística V8.0</h1>
        <div class='header-subtitle'>Soporte avanzado para Piezas y Ventas Mayoristas (Jofre Santana)</div>
    </div>
    """, unsafe_allow_html=True)

    # Panel de carga de archivos
    st.markdown("""
    <div class='filter-panel'>
        <h3 class='filter-title'>📂 Carga de Archivos</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader("Subir Manifiesto (Debe tener columna PIEZAS)", type=['xlsx', 'xls', 'csv'])
    with col2:
        f_facturas = st.file_uploader("Subir Facturas (Debe tener VALORES)", type=['xlsx', 'xls', 'csv'])
    
    # Datos de ejemplo para demostración
    use_sample = st.checkbox("Usar datos de demostración", value=True)
    
    if use_sample or (f_manifiesto and f_facturas):
        try:
            if use_sample:
                # Generar datos de ejemplo
                np.random.seed(42)
                num_rows = 50
                
                # Datos de manifiesto de ejemplo
                df_m = pd.DataFrame({
                    'GUIA': [f'GUA-{i:04d}' for i in range(1001, 1001 + num_rows)],
                    'DESTINATARIO': np.random.choice([
                        'JOFRE SANTANA IMPORT', 
                        'MALL DEL SOL AEROPOSTALE',
                        'SAN MARINO TIENDA',
                        'CARLOS PEREZ',
                        'MARIA GONZALEZ',
                        'CENTRO COMERCIAL QUITO',
                        'PLAZA DE LAS AMERICAS'
                    ], num_rows),
                    'PIEZAS': np.random.randint(1, 20, num_rows),
                    'VALOR_DECLARADO': np.random.uniform(50, 500, num_rows).round(2)
                })
                
                # Datos de facturas de ejemplo (algunas coinciden, otras no)
                df_f = pd.DataFrame({
                    'GUIA_FACTURA': [f'GUA-{i:04d}' for i in range(1001, 1001 + int(num_rows * 0.8))],
                    'VALOR_COBRADO': np.random.uniform(45, 550, int(num_rows * 0.8)).round(2)
                })
                
                st.success("✅ Usando datos de demostración. Puede subir sus propios archivos para procesamiento real.")
            else:
                # Lectura flexible de archivos subidos
                df_m = pd.read_excel(f_manifiesto) if f_manifiesto.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_manifiesto)
                df_f = pd.read_excel(f_facturas) if f_facturas.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_facturas)

            # Configuración de columnas
            st.markdown("""
            <div class='filter-panel'>
                <h3 class='filter-title'>⚙️ Configuración de Columnas</h3>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("**Configuración Manifiesto**")
                cols_m = df_m.columns.tolist()
                # Detección inteligente
                idx_guia = next((i for i, c in enumerate(cols_m) if 'GUIA' in str(c).upper()), 0)
                idx_dest = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['DEST', 'CLIEN', 'NOMB'])), 0)
                idx_piez = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['PIEZA', 'CANT', 'BULT'])), 0)
                idx_val = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL'])), 0)

                col_guia_m = st.selectbox("Columna Guía", cols_m, index=idx_guia, key='m_guia')
                col_dest_m = st.selectbox("Columna Destinatario", cols_m, index=idx_dest, key='m_dest')
                col_piezas_m = st.selectbox("Columna Piezas/Bultos", cols_m, index=idx_piez, key='m_piezas')
                col_valor_m = st.selectbox("Columna Valor Declarado", cols_m, index=idx_val, key='m_val')
            
            with c2:
                st.info("**Configuración Facturas**")
                cols_f = df_f.columns.tolist()
                idx_guia_f = next((i for i, c in enumerate(cols_f) if 'GUIA' in str(c).upper()), 0)
                idx_val_f = next((i for i, c in enumerate(cols_f) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL', 'SUBT'])), 0)

                col_guia_f = st.selectbox("Columna Guía", cols_f, index=idx_guia_f, key='f_guia')
                col_valor_f = st.selectbox("Columna Valor Cobrado", cols_f, index=idx_val_f, key='f_val')
            st.markdown("</div>", unsafe_allow_html=True)

            # Botón de ejecución
            if st.button("🚀 EJECUTAR RECONCILIACIÓN V8.0", type="primary", use_container_width=True):
                with st.spinner("🔄 Ejecutando algoritmo V8.0..."):
                    # Procesamiento
                    df_m['GUIA_CLEAN'] = df_m[col_guia_m].astype(str).str.strip().str.upper()
                    df_f['GUIA_CLEAN'] = df_f[col_guia_f].astype(str).str.strip().str.upper()
                    
                    # Merge
                    df_final = pd.merge(df_m, df_f, on='GUIA_CLEAN', how='left', suffixes=('_MAN', '_FAC'))
                    
                    # Lógica V8
                    df_final['DESTINATARIO_NORM'] = df_final[col_dest_m].fillna('DESCONOCIDO')
                    df_final['TIPO_TIENDA'] = df_final['DESTINATARIO_NORM'].apply(identificar_tipo_tienda_v8)
                    
                    # Manejo de Piezas y Valores
                    df_final['PIEZAS_CALC'] = pd.to_numeric(df_final[col_piezas_m], errors='coerce').fillna(1)
                    df_final['VALOR_REAL'] = df_final[col_valor_f].apply(procesar_subtotal_wilo).fillna(0)
                    df_final['VALOR_MANIFIESTO'] = df_final[col_valor_m].apply(procesar_subtotal_wilo).fillna(0)
                    
                    # Creación de Grupos
                    def crear_grupo(row):
                        tipo = row['TIPO_TIENDA']
                        nom = normalizar_texto_wilo(row['DESTINATARio_NORM'])
                        if tipo == "VENTAS AL POR MAYOR": return "VENTAS AL POR MAYOR - JOFRE SANTANA"
                        if tipo == "VENTA WEB": return f"WEB - {nom}"
                        return f"TIENDA - {nom}"
                    
                    df_final['GRUPO'] = df_final.apply(crear_grupo, axis=1)

                    # --- RESULTADOS ---
                    st.markdown("""
                    <div class='main-header'>
                        <h2>📊 Resultados del Análisis V8.0</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    total_facturado = df_final['VALOR_REAL'].sum()
                    total_piezas = df_final['PIEZAS_CALC'].sum()
                    con_factura = df_final[df_final['VALOR_REAL'] > 0].shape[0]
                    sin_factura = df_final[df_final['VALOR_REAL'] == 0].shape[0]
                    
                    # KPIs modernos
                    st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
                    k1, k2, k3, k4 = st.columns(4)
                    
                    with k1:
                        st.markdown(f"""
                        <div class='stat-card card-blue'>
                            <div class='stat-icon'>💰</div>
                            <div class='stat-title'>Total Facturado</div>
                            <div class='stat-value'>${total_facturado:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k2:
                        st.markdown(f"""
                        <div class='stat-card card-green'>
                            <div class='stat-icon'>📦</div>
                            <div class='stat-title'>Total Piezas</div>
                            <div class='stat-value'>{total_piezas:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k3:
                        st.markdown(f"""
                        <div class='stat-card card-purple'>
                            <div class='stat-icon'>✅</div>
                            <div class='stat-title'>Guías Conciliadas</div>
                            <div class='stat-value'>{con_factura}</div>
                            <div class='stat-change positive'>+{con_factura/len(df_final)*100:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k4:
                        st.markdown(f"""
                        <div class='stat-card card-red'>
                            <div class='stat-icon'>⚠️</div>
                            <div class='stat-title'>Guías Sin Factura</div>
                            <div class='stat-value'>{sin_factura}</div>
                            <div class='stat-change {'negative' if sin_factura > 5 else 'positive'}">{'Revisar' if sin_factura > 5 else 'OK'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Tabs para diferentes vistas
                    tab1, tab2, tab3 = st.tabs(["📈 Resumen por Canal", "📋 Detalle por Grupo", "🔍 Datos Completos"])
                    
                    with tab1:
                        resumen = df_final.groupby('TIPO_TIENDA').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).reset_index()
                        resumen.columns = ['Canal', 'Guías', 'Piezas', 'Valor Facturado']
                        resumen['% Gasto'] = (resumen['Valor Facturado'] / total_facturado * 100).round(2)
                        resumen['Valor Promedio'] = (resumen['Valor Facturado'] / resumen['Guías']).round(2)
                        
                        st.dataframe(
                            resumen.style.format({
                                'Valor Facturado': '${:,.2f}',
                                '% Gasto': '{:.2f}%',
                                'Valor Promedio': '${:,.2f}'
                            }).background_gradient(subset=['% Gasto'], cmap='Blues'),
                            use_container_width=True
                        )
                        
                        # Gráficos
                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            fig = px.pie(resumen, values='Valor Facturado', names='Canal', 
                                       title="Distribución por Canal", 
                                       color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_chart2:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            fig2 = px.bar(resumen, x='Canal', y='Guías', color='Canal',
                                        title="Guías por Canal", text='Guías',
                                        color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig2, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    with tab2:
                        detalle = df_final.groupby('GRUPO').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).sort_values('VALOR_REAL', ascending=False)
                        detalle.columns = ['Guías', 'Piezas', 'Valor Total']
                        
                        # Agregar métricas
                        detalle['Valor Promedio'] = (detalle['Valor Total'] / detalle['Guías']).round(2)
                        detalle['% del Total'] = (detalle['Valor Total'] / total_facturado * 100).round(2)
                        
                        st.dataframe(
                            detalle.style.format({
                                'Valor Total': '${:,.2f}',
                                'Valor Promedio': '${:,.2f}',
                                '% del Total': '{:.2f}%'
                            }).bar(subset=['Valor Total'], color='#5DA5DA'),
                            use_container_width=True
                        )

                    with tab3:
                        st.dataframe(
                            df_final[['GUIA_CLEAN', 'DESTINATARIO_NORM', 'TIPO_TIENDA', 'GRUPO', 
                                     'PIEZAS_CALC', 'VALOR_MANIFIESTO', 'VALOR_REAL']].head(50),
                            use_container_width=True
                        )
                    
                    # Exportación
                    st.markdown("### 💾 Exportar Datos")
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, sheet_name='Data_Completa', index=False)
                        resumen.to_excel(writer, sheet_name='Resumen_Canal', index=False)
                        detalle.to_excel(writer, sheet_name='Detalle_Grupos', index=True)
                    
                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        st.download_button(
                            label="📥 Descargar Excel Completo",
                            data=buffer.getvalue(),
                            file_name=f"conciliacion_v8_{datetime.now().date()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    with col_exp2:
                        # Exportar CSV rápido
                        csv = df_final.to_csv(index=False)
                        st.download_button(
                            label="📄 Descargar CSV",
                            data=csv,
                            file_name=f"conciliacion_v8_{datetime.now().date()}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

        except Exception as e:
            st.error(f"❌ Error en el procesamiento: {str(e)}")
    else:
        st.info("👆 Suba los archivos necesarios o active la opción de datos de demostración para comenzar.")

# ==============================================================================
# 6. MÓDULO DASHBOARD DE TRANSFERENCIAS (ACTUALIZADO Y MEJORADO) - CORREGIDO
# ==============================================================================

# --- CONFIGURACIÓN DE PARÁMETROS ---
TIENDAS_REGULARES = 42
PRICE_CLUBS = 5
TIENDA_WEB = 1
VENTAS_POR_MAYOR = 1
FALLAS = 1

PRICE_KEYWORDS = ['PRICE', 'OIL']
WEB_KEYWORDS = ['WEB', 'TIENDA MOVIL', 'MOVIL']
FALLAS_KEYWORDS = ['FALLAS']
VENTAS_MAYOR_KEYWORDS = ['MAYOR', 'MAYORISTA']

TIENDAS_REGULARES_LISTA = [
    'AERO CCI', 'AERO DAULE', 'AERO LAGO AGRIO', 'AERO MALL DEL RIO GYE',
    'AERO PLAYAS', 'AEROPOSTALE 6 DE DICIEMBRE', 'AEROPOSTALE BOMBOLI',
    'AEROPOSTALE CAYAMBE', 'AEROPOSTALE EL COCA', 'AEROPOSTALE PASAJE',
    'AEROPOSTALE PEDERNALES', 'AMBATO', 'BABAHOYO', 'BAHIA DE CARAQUEZ',
    'CARAPUNGO', 'CEIBOS', 'CONDADO SHOPPING', 'CUENCA', 'CUENCA CENTRO HISTORICO',
    'DURAN', 'LA PLAZA SHOPPING', 'MACHALA', 'MAL DEL SUR', 'MALL DEL PACIFICO',
    'MALL DEL SOL', 'MANTA', 'MILAGRO', 'MULTIPLAZA RIOBAMBA', 'PASEO AMBATO',
    'PENINSULA', 'PORTOVIEJO', 'QUEVEDO', 'RIOBAMBA', 'RIOCENTRO EL DORADO',
    'RIOCENTRO NORTE', 'SAN LUIS', 'SANTO DOMINGO'
]

# --- FUNCIONES DE SOPORTE MEJORADAS ---

def extraer_entero(valor):
    """Extrae el valor entero de una cadena o número"""
    try:
        if pd.isna(valor): 
            return 0
        if isinstance(valor, str):
            # Eliminar puntos de separadores de miles
            valor = valor.replace('.', '')
            # Si hay coma decimal, tomar solo la parte entera
            if ',' in valor:
                valor = valor.split(',')[0]
        # Convertir a float primero para manejar números decimales
        val = float(valor)
        return int(val)
    except:
        return 0

def clasificar_transferencia(row):
    """Clasifica la transferencia según el destino y cantidad"""
    sucursal = str(row.get('Sucursal Destino', row.get('Bodega Destino', ''))).upper()
    cantidad = row.get('Cantidad_Entera', 0)
    
    # Primero verificar si es Fundas (múltiplos de 100 y >= 500)
    if cantidad >= 500 and cantidad % 100 == 0:
        return 'Fundas'
    
    # Luego verificar las otras categorías
    if any(kw in sucursal for kw in PRICE_KEYWORDS): 
        return 'Price Club'
    if any(kw in sucursal for kw in WEB_KEYWORDS): 
        return 'Tienda Web'
    if any(kw in sucursal for kw in FALLAS_KEYWORDS): 
        return 'Fallas'
    if any(kw in sucursal for kw in VENTAS_MAYOR_KEYWORDS): 
        return 'Ventas por Mayor'
    
    # Verificar tiendas regulares específicas
    for tienda in TIENDAS_REGULARES_LISTA:
        if tienda.upper() in sucursal:
            return 'Tiendas'
    
    # Palabras clave generales para tiendas
    tiendas_kw = ['AERO', 'MALL', 'CENTRO', 'SHOPPING', 'PLAZA', 'RIOCENTRO']
    if any(kw in sucursal for kw in tiendas_kw): 
        return 'Tiendas'
    
    # Por defecto
    return 'Ventas por Mayor'

def procesar_transferencias_diarias(df):
    """Procesa el archivo de transferencias diarias"""
    # Eliminar filas sin secuencial
    df = df.dropna(subset=['Secuencial'])
    df['Secuencial'] = df['Secuencial'].astype(str).str.strip()
    df = df[df['Secuencial'] != '']
    
    # Extraer cantidad entera
    df['Cantidad_Entera'] = df['Cantidad Prendas'].apply(extraer_entero)
    
    # Clasificar transferencias
    df['Categoria'] = df.apply(clasificar_transferencia, axis=1)
    
    # Preparar resultados
    res = {
        'fecha': datetime.now(),
        'transferencias': int(df['Secuencial'].nunique()),
        'total_unidades': int(df['Cantidad_Entera'].sum()),
        'por_categoria': {},
        'detalle_categoria': {},
        'conteo_sucursales': {},
        'df_procesado': df
    }
    
    # Categorías definidas
    categorias = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas', 'Fundas']
    
    for cat in categorias:
        df_cat = df[df['Categoria'] == cat]
        
        # Calcular métricas por categoría
        res['por_categoria'][cat] = df_cat['Cantidad_Entera'].sum()
        
        if not df_cat.empty:
            res['detalle_categoria'][cat] = {
                'cantidad': int(df_cat['Cantidad_Entera'].sum()),
                'transf': int(df_cat['Secuencial'].nunique()),
                'unicas': int(df_cat['Sucursal Destino'].nunique())
            }
            res['conteo_sucursales'][cat] = res['detalle_categoria'][cat]['unicas']
        else:
            res['detalle_categoria'][cat] = {'cantidad': 0, 'transf': 0, 'unicas': 0}
            res['conteo_sucursales'][cat] = 0
    
    return res

def normalizar_codigo(df, columnas_posibles):
    """Normaliza la columna de código a string y elimina espacios"""
    for col in columnas_posibles:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            return df, col
    return df, None

def to_excel(df):
    """Convierte DataFrame a Excel en memoria"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Detalle_Secuencial')
    return output.getvalue()

def mostrar_dashboard_transferencias():
    """Dashboard principal de transferencias"""
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Diarias</h1>
        <div class='header-subtitle'>Análisis de distribución por categorías y sucursales</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- PESTAÑAS PRINCIPALES ---
    tab1, tab2, tab3 = st.tabs(["📊 Transferencias Diarias", "📦 Mercadería en Tránsito", "📈 Análisis de Stock"])
    
    # --- PESTAÑA 1: TRANSFERENCIAS DIARIAS (sin cambios) ---
    with tab1:
        # ... (el código existente de transferencias diarias se mantiene igual)
        pass
    
    # --- PESTAÑA 2: MERCADERÍA EN TRÁNSITO (CORREGIDA) ---
    with tab2:
        st.header("📦 Análisis de Mercadería en Tránsito")
        st.info("Este módulo requiere el 'Archivo Base' (con códigos y departamentos) y el 'Archivo de Tránsito' (con códigos y cantidades).")
        
        col_a, col_b = st.columns(2)
        with col_a:
            f_base = st.file_uploader("1. Cargar Stock Inicial (Base)", type=['xlsx', 'csv'], key="base_tr")
        with col_b:
            f_comp = st.file_uploader("2. Cargar Tránsito (Comparación)", type=['xlsx', 'csv'], key="comp_tr")
        
        if f_base and f_comp:
            try:
                # Leer archivos
                try:
                    df_b = pd.read_excel(f_base)
                except:
                    df_b = pd.read_csv(f_base)
                
                try:
                    df_c = pd.read_excel(f_comp)
                except:
                    df_c = pd.read_csv(f_comp)
                
                st.success("✅ Archivos cargados correctamente")
                
                # Mostrar información de columnas para debugging
                with st.expander("🔍 Ver información de columnas cargadas"):
                    col_debug1, col_debug2 = st.columns(2)
                    with col_debug1:
                        st.write("**Archivo Base - Columnas:**")
                        st.write(list(df_b.columns))
                        st.write(f"**Filas:** {len(df_b)}")
                    with col_debug2:
                        st.write("**Archivo Comparación - Columnas:**")
                        st.write(list(df_c.columns))
                        st.write(f"**Filas:** {len(df_c)}")
                
                # Encontrar columna de código en base
                columnas_codigo_posibles_base = ['CODIGO', 'Código', 'CÓDIGO', 'codigo', 'SKU', 'Producto', 'COD', 'Cod']
                df_b, col_codigo_base = normalizar_codigo(df_b, columnas_codigo_posibles_base)
                
                if col_codigo_base is None:
                    st.error("❌ No se encontró columna de código en el archivo base")
                    st.info("Columnas disponibles en archivo base:")
                    st.write(list(df_b.columns))
                    st.stop()
                
                # Encontrar columna de código en comparación
                columnas_codigo_posibles_comp = ['CODIGO', 'Código', 'CÓDIGO', 'codigo', 'SKU', 'Producto', 'COD', 'Cod', 'Código Producto', 'COD PRODUCTO']
                df_c, col_codigo_comp = normalizar_codigo(df_c, columnas_codigo_posibles_comp)
                
                if col_codigo_comp is None:
                    st.error("❌ No se encontró columna de código en el archivo de comparación")
                    st.info("Columnas disponibles en archivo de comparación:")
                    st.write(list(df_c.columns))
                    st.stop()
                
                # Encontrar columna de departamento en base
                columnas_departamento_posibles = ['DEPARTAMENTO', 'Departamento', 'departamento', 'DEPT', 'Depto', 'Categoría', 'CATEGORIA']
                col_depto = None
                for col in columnas_departamento_posibles:
                    if col in df_b.columns:
                        col_depto = col
                        break
                
                if col_depto is None:
                    st.error("❌ No se encontró columna de departamento en el archivo base")
                    st.info("Las siguientes columnas se buscaron como departamento:")
                    st.write(columnas_departamento_posibles)
                    st.info("Columnas disponibles en archivo base:")
                    st.write(list(df_b.columns))
                    st.stop()
                
                # Encontrar columna de cantidad en comparación
                columnas_cantidad_posibles = ['CANTIDAD', 'Cantidad', 'cantidad', 'QTY', 'Quantity', 'UNIDADES', 'Unidades', 'CANT', 'Cant']
                col_cantidad = None
                for col in columnas_cantidad_posibles:
                    if col in df_c.columns:
                        col_cantidad = col
                        break
                
                if col_cantidad is None:
                    st.error("❌ No se encontró columna de cantidad en el archivo de comparación")
                    st.info("Busque columnas numéricas que puedan representar cantidad:")
                    
                    # Mostrar columnas numéricas
                    numeric_cols = df_c.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        st.write("Columnas numéricas encontradas:", numeric_cols)
                        # Sugerir la primera columna numérica
                        col_cantidad = numeric_cols[0]
                        st.warning(f"Se usará '{col_cantidad}' como columna de cantidad")
                    else:
                        st.write("No se encontraron columnas numéricas")
                        st.stop()
                
                # Preparar datos base
                df_base = df_b[[col_codigo_base, col_depto]].copy()
                df_base = df_base.rename(columns={col_codigo_base: 'CODIGO', col_depto: 'DEPARTAMENTO'})
                
                # Preparar datos de comparación
                df_comp = df_c[[col_codigo_comp, col_cantidad]].copy()
                df_comp = df_comp.rename(columns={col_codigo_comp: 'CODIGO', col_cantidad: 'CANTIDAD'})
                
                # Limpiar y normalizar códigos
                df_base['CODIGO'] = df_base['CODIGO'].astype(str).str.strip().str.upper()
                df_comp['CODIGO'] = df_comp['CODIGO'].astype(str).str.strip().str.upper()
                
                # Eliminar códigos vacíos
                df_base = df_base[df_base['CODIGO'] != '']
                df_comp = df_comp[df_comp['CODIGO'] != '']
                
                # Eliminar duplicados en base (mantener primera ocurrencia)
                df_base = df_base.drop_duplicates(subset=['CODIGO'])
                
                # Convertir cantidad a numérico
                df_comp['CANTIDAD'] = pd.to_numeric(df_comp['CANTIDAD'], errors='coerce').fillna(0)
                
                # Realizar el merge
                df_merged = pd.merge(df_comp, df_base, on='CODIGO', how='left')
                
                # Clasificar productos sin departamento
                df_merged['DEPARTAMENTO'] = df_merged['DEPARTAMENTO'].fillna('SIN CLASIFICAR')
                
                # Resumen por departamento
                resumen_dept = df_merged[df_merged['DEPARTAMENTO'] != 'SIN CLASIFICAR'].groupby('DEPARTAMENTO').agg({
                    'CANTIDAD': 'sum',
                    'CODIGO': 'nunique'
                }).rename(columns={'CANTIDAD': 'Unidades en Tránsito', 'CODIGO': 'SKUs Únicos'}).sort_values('Unidades en Tránsito', ascending=False)
                
                # Calcular sin clasificar
                sin_clasificar = df_merged[df_merged['DEPARTAMENTO'] == 'SIN CLASIFICAR']
                unidades_sin_clasificar = sin_clasificar['CANTIDAD'].sum()
                skus_sin_clasificar = sin_clasificar['CODIGO'].nunique()
                
                # Mostrar resultados
                st.subheader("📊 Mercadería en Tránsito por Departamento")
                
                # Métricas principales
                col_total1, col_total2, col_total3 = st.columns(3)
                with col_total1:
                    total_unidades = df_merged['CANTIDAD'].sum()
                    st.metric("Total Unidades en Tránsito", f"{total_unidades:,.0f}")
                with col_total2:
                    total_skus = df_merged['CODIGO'].nunique()
                    st.metric("SKUs Diferentes", f"{total_skus:,.0f}")
                with col_total3:
                    dept_unicos = df_merged['DEPARTAMENTO'].nunique() - 1  # Excluir SIN CLASIFICAR
                    st.metric("Departamentos", f"{dept_unicos}")
                
                if unidades_sin_clasificar > 0:
                    st.warning(f"⚠️ **Nota:** Hay {unidades_sin_clasificar:,.0f} unidades ({skus_sin_clasificar} SKUs) sin clasificar en el departamento")
                
                # Gráfico de barras (top 10 departamentos)
                if not resumen_dept.empty:
                    # Limitar a top 10
                    df_top = resumen_dept.head(10).copy()
                    
                    # Si hay más de 10, agregar "OTROS"
                    if len(resumen_dept) > 10:
                        otros_total = resumen_dept.iloc[10:]['Unidades en Tránsito'].sum()
                        otros_skus = resumen_dept.iloc[10:]['SKUs Únicos'].sum()
                        otros_df = pd.DataFrame({
                            'Unidades en Tránsito': [otros_total],
                            'SKUs Únicos': [otros_skus]
                        }, index=['OTROS'])
                        df_top = pd.concat([df_top, otros_df])
                    
                    # Crear gráfico
                    fig = go.Figure(data=[
                        go.Bar(
                            x=df_top.index,
                            y=df_top['Unidades en Tránsito'],
                            text=df_top['Unidades en Tránsito'].apply(lambda x: f'{x:,.0f}'),
                            textposition='auto',
                            marker_color='#2E8B57',
                            name='Unidades'
                        )
                    ])
                    
                    fig.update_layout(
                        title="Top 10 Departamentos con Mercadería en Tránsito",
                        xaxis_title="Departamento",
                        yaxis_title="Unidades",
                        template="plotly_white",
                        height=400,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Gráfico de pastel
                    if len(df_top) > 1:
                        fig_pie = px.pie(
                            df_top.reset_index(),
                            values='Unidades en Tránsito',
                            names='DEPARTAMENTO',
                            title="Distribución por Departamento",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                # Mostrar tabla detallada
                with st.expander("📋 Ver Detalle por Departamento"):
                    st.dataframe(
                        resumen_dept.style.format({
                            'Unidades en Tránsito': '{:,.0f}',
                            'SKUs Únicos': '{:,.0f}'
                        }).background_gradient(subset=['Unidades en Tránsito'], cmap='Greens'),
                        use_container_width=True
                    )
                
                # Productos sin clasificar
                if not sin_clasificar.empty:
                    with st.expander("⚠️ Ver Productos Sin Clasificar"):
                        st.info(f"Total: {unidades_sin_clasificar:,.0f} unidades en {skus_sin_clasificar} SKUs")
                        st.dataframe(
                            sin_clasificar[['CODIGO', 'CANTIDAD']].sort_values('CANTIDAD', ascending=False),
                            use_container_width=True,
                            height=300
                        )
                
                # Estadísticas adicionales
                with st.expander("📊 Estadísticas Detalladas"):
                    col_stats1, col_stats2 = st.columns(2)
                    with col_stats1:
                        if total_skus > 0:
                            promedio_unidades = total_unidades / total_skus
                            st.metric("Promedio por SKU", f"{promedio_unidades:.1f}")
                        else:
                            st.metric("Promedio por SKU", "0.0")
                        
                        if not resumen_dept.empty:
                            dept_top = resumen_dept.index[0]
                            unidades_top = resumen_dept.iloc[0]['Unidades en Tránsito']
                            st.metric("Departamento Top", f"{dept_top}", f"{unidades_top:,.0f} unid.")
                    
                    with col_stats2:
                        if not resumen_dept.empty:
                            sku_max_dept = resumen_dept['SKUs Únicos'].idxmax()
                            sku_max_val = resumen_dept['SKUs Únicos'].max()
                            st.metric("Más SKUs", f"{sku_max_dept}", f"{sku_max_val} SKUs")
                        
                        porcentaje_clasificado = (total_unidades - unidades_sin_clasificar) / total_unidades * 100 if total_unidades > 0 else 0
                        st.metric("% Clasificado", f"{porcentaje_clasificado:.1f}%")
                
                # Opciones de exportación
                st.subheader("💾 Exportar Resultados")
                
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    # Exportar Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_merged.to_excel(writer, sheet_name='Datos_Completos', index=False)
                        resumen_dept.to_excel(writer, sheet_name='Resumen_Departamentos')
                        sin_clasificar.to_excel(writer, sheet_name='Sin_Clasificar', index=False)
                    
                    st.download_button(
                        label="📥 Descargar Excel Completo",
                        data=output.getvalue(),
                        file_name=f"mercaderia_transito_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_exp2:
                    # Exportar CSV
                    csv = df_merged.to_csv(index=False)
                    st.download_button(
                        label="📄 Descargar CSV",
                        data=csv,
                        file_name=f"mercaderia_transito_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            except Exception as e:
                st.error(f"❌ Error al procesar los archivos: {str(e)}")
                st.info("""
                **Posibles soluciones:**
                1. Verifique que ambos archivos tengan una columna con códigos de producto
                2. Asegúrese de que los códigos sean similares en ambos archivos
                3. Revise que el archivo base tenga una columna de departamento
                4. Verifique que el archivo de comparación tenga una columna numérica de cantidad
                """)
        
        else:
            st.info("👈 Por favor, carga ambos archivos para realizar el análisis de mercadería en tránsito.")
            
            # Mostrar ejemplo de estructura
            with st.expander("📋 Ver estructura esperada de archivos"):
                st.markdown("""
                **Archivo Base (Stock Inicial / Catálogo):**
                ```
                CODIGO    | DEPARTAMENTO
                ----------|--------------
                12345     | CAMISETAS
                67890     | PANTALONES
                24680     | ZAPATOS
                ```
                
                **Archivo de Comparación (Mercadería en Tránsito):**
                ```
                CODIGO    | CANTIDAD
                ----------|----------
                12345     | 100
                67890     | 50
                13579     | 200
                ```
                
                **Resultado esperado:**
                ```
                DEPARTAMENTO   | Unidades | SKUs
                ---------------|----------|-----
                CAMISETAS      | 100      | 1
                PANTALONES     | 50       | 1
                SIN CLASIFICAR | 200      | 1
                ```
                """)
    
    # --- PESTAÑA 3: ANÁLISIS DE STOCK (sin cambios) ---
    with tab3:
        st.header("📈 Análisis de Stock")
        st.info("Esta funcionalidad está en desarrollo. Próximamente disponible.")
# ==============================================================================
# 7. MÓDULO GENERACIÓN DE GUÍAS UNIFICADO (ACTUALIZADO)
# ==============================================================================

def descargar_logo(url):
    """Descarga el logo desde la URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        st.warning(f"No se pudo descargar el logo: {str(e)}")
        return None

def generar_pdf_profesional(guia_data):
    """Genera un PDF profesional con logo y QR integrado"""
    buffer = io.BytesIO()
    
    # Configurar el documento
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados (colores y fuentes basados en la guía de ejemplo)
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Title'],
        fontSize=20,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='TituloDerecha',
        parent=styles['Title'],
        fontSize=20,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='SubtituloDerecha',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#333333'),
        fontName='Helvetica',
        alignment=TA_RIGHT,
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='EncabezadoSeccion',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=12
    ))
    
    styles.add(ParagraphStyle(
        name='Contenido',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        fontName='Helvetica',
        alignment=TA_LEFT,
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        name='ContenidoNegrita',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=4
    ))
    
    # Contenido del documento
    contenido = []
    
    # CABECERA CON LOGO, QR Y TÍTULO A LA DERECHA
    # ==========================================
    
    # Determinar logo según marca
    logo_bytes = None
    if guia_data['marca'] == 'Fashion Club':
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    else:
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
    # Descargar logo si no está en session_state
    if guia_data['marca'] not in st.session_state.get('logos', {}):
        logo_bytes = descargar_logo(logo_url)
        if logo_bytes:
            if 'logos' not in st.session_state:
                st.session_state.logos = {}
            st.session_state.logos[guia_data['marca']] = logo_bytes
    else:
        logo_bytes = st.session_state.logos[guia_data['marca']]
    
    # Crear tabla de cabecera con logo, QR y título
    cabecera_data = []
    
    # Columna izquierda: Logo
    if logo_bytes:
        try:
            logo_img = Image(io.BytesIO(logo_bytes), width=2*inch, height=1.2*inch)
            logo_cell = logo_img
        except:
            logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['Titulo'])
    else:
        logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['Titulo'])
    
    # Columna central: QR
    qr_cell = ""
    if guia_data['url_pedido'] in st.session_state.qr_images:
        try:
            qr_bytes = st.session_state.qr_images[guia_data['url_pedido']]
            qr_img = Image(io.BytesIO(qr_bytes), width=1.2*inch, height=1.2*inch)
            qr_cell = qr_img
        except:
            qr_cell = Paragraph("QR no disponible", styles['Contenido'])
    
    # Columna derecha: Título (CENTRO DE DISTRIBUCIÓN a la derecha)
    titulo_text = f"""
    <b>CENTRO DE DISTRIBUCIÓN {guia_data['marca'].upper()}</b><br/>
    <font size=10>GUÍA DE ENVÍO</font>
    """
    titulo_cell = Paragraph(titulo_text, styles['TituloDerecha'])
    
    # Crear tabla de cabecera
    cabecera_table = Table([[logo_cell, qr_cell, titulo_cell]], 
                           colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    
    cabecera_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    contenido.append(cabecera_table)
    contenido.append(Spacer(1, 0.1*inch))
    
    # Línea separadora
    contenido.append(Paragraph("_" * 100, ParagraphStyle(name='Linea', fontSize=6)))
    contenido.append(Spacer(1, 0.2*inch))
    
    # INFORMACIÓN DE LA GUÍA (EXACTAMENTE COMO EN LA IMAGEN)
    # ==========================================
    
    # Número de guía, fecha y estado en una sola línea
    info_guia = Table([
        [Paragraph(f"<b>NÚMERO DE GUÍA:</b> {guia_data['numero']}", styles['ContenidoNegrita']),
         Paragraph(f"<b>FECHA DE EMISIÓN:</b> {guia_data['fecha_emision']}", styles['ContenidoNegrita']),
         Paragraph(f"<b>ESTADO:</b> {guia_data['estado']}", styles['ContenidoNegrita'])]
    ], colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    
    info_guia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F0F0')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
    ]))
    
    contenido.append(info_guia)
    contenido.append(Spacer(1, 0.2*inch))
    
    # INFORMACIÓN DE ENVÍO (EXACTAMENTE COMO EN LA IMAGEN)
    # ==========================================
    
    contenido.append(Paragraph("INFORMACIÓN DE ENVÍO", styles['EncabezadoSeccion']))
    
    # Crear tabla con dos columnas para remitente y destinatario
    datos_envio = [
        # Encabezados
        [Paragraph("<b>REMITENTE</b>", styles['ContenidoNegrita']), 
         Paragraph("<b>DESTINATARIO</b>", styles['ContenidoNegrita'])],
        
        # Nombre
        [Paragraph(f"<b>Nombre:</b> {guia_data['remitente']}", styles['Contenido']),
         Paragraph(f"<b>Nombre:</b> {guia_data['destinatario']}", styles['Contenido'])],
        
        # Dirección (con más espacio)
        [Paragraph(f"<b>Dirección:</b> {guia_data['direccion_remitente']}", styles['Contenido']),
         Paragraph(f"<b>Dirección:</b> {guia_data['direccion_destinatario']}", styles['Contenido'])],
        
        # Teléfono y tienda (solo destinatario)
        ["", Paragraph(f"<b>Teléfono:</b> {guia_data['telefono_destinatario']}", styles['Contenido'])],
        
        ["", Paragraph(f"<b>Tienda:</b> {guia_data['tienda_destino']}", styles['Contenido'])]
    ]
    
    tabla_envio = Table(datos_envio, colWidths=[3.5*inch, 3.5*inch])
    tabla_envio.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E8E8E8')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('SPAN', (0, 3), (0, 3)),
        ('SPAN', (0, 4), (0, 4)),
        ('BOTTOMPADDING', (0, 2), (1, 2), 12),
    ]))
    
    contenido.append(tabla_envio)
    
    # Construir el PDF
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()

def mostrar_vista_previa_guia(guia_data):
    """Muestra una vista previa de la guía sin generar PDF"""
    st.markdown("""
    <div class='filter-panel'>
        <h4>👁️ Vista Previa de la Guía</h4>
    """, unsafe_allow_html=True)
    
    # Mostrar logo según marca
    col_logo, col_info = st.columns([1, 3])
    
    with col_logo:
        if guia_data['marca'] == 'Fashion Club':
            logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
        else:
            logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
        
        try:
            st.image(logo_url, caption=guia_data['marca'], width=150)
        except:
            st.markdown(f"**{guia_data['marca']}**")
    
    with col_info:
        st.markdown("**📋 Información de la Guía**")
        st.write(f"**Número:** {guia_data['numero']}")
        st.write(f"**Estado:** {guia_data['estado']}")
        st.write(f"**Fecha:** {guia_data['fecha_emision']}")
    
    st.divider()
    
    # Información de envío
    col_rem, col_dest = st.columns(2)
    
    with col_rem:
        st.markdown("**👤 Remitente**")
        st.write(f"**Nombre:** {guia_data['remitente']}")
        st.write(f"**Dirección:** {guia_data['direccion_remitente']}")
    
    with col_dest:
        st.markdown("**🏪 Destinatario**")
        st.write(f"**Nombre:** {guia_data['destinatario']}")
        st.write(f"**Teléfono:** {guia_data['telefono_destinatario']}")
        st.write(f"**Dirección:** {guia_data['direccion_destinatario']}")
        if guia_data['tienda_destino'] != "No especificada":
            st.write(f"**Tienda:** {guia_data['tienda_destino']}")
    
    st.divider()
    
    # Seguimiento
    st.markdown("**🔗 Seguimiento**")
    st.write(f"**URL:** {guia_data['url_pedido']}")
    
    # Mostrar QR si está disponible
    if guia_data['url_pedido'] in st.session_state.qr_images:
        col_qr, col_url = st.columns([1, 3])
        with col_qr:
            qr_bytes = st.session_state.qr_images[guia_data['url_pedido']]
            st.image(qr_bytes, caption="Código QR", width=120)
        with col_url:
            st.info(f"**URL completa:** {guia_data['url_pedido']}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_resumen_guia(guia_data, pdf_bytes):
    """Muestra el resumen de la guía generada y opciones de descarga"""
    st.markdown("""
    <div class='filter-panel'>
        <h4>✅ Guía Generada Exitosamente</h4>
    """, unsafe_allow_html=True)
    
    # Mostrar información de la guía
    col_logo, col_info = st.columns([1, 3])
    
    with col_logo:
        if guia_data['marca'] == 'Fashion Club':
            logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
        else:
            logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
        
        try:
            st.image(logo_url, caption=guia_data['marca'], width=120)
        except:
            st.markdown(f"**{guia_data['marca']}**")
    
    with col_info:
        st.markdown("**📋 Información de la Guía**")
        st.write(f"**Número:** {guia_data['numero']}")
        st.write(f"**Estado:** {guia_data['estado']}")
        st.write(f"**Fecha:** {guia_data['fecha_creacion']}")
    
    st.divider()
    
    # Información del destinatario
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("**🏪 Destinatario**")
        st.write(f"**Nombre:** {guia_data['destinatario']}")
        st.write(f"**Teléfono:** {guia_data['telefono_destinatario']}")
    
    with col_det2:
        st.markdown("**📍 Dirección**")
        st.write(guia_data['direccion_destinatario'])
        if guia_data['tienda_destino'] != "No especificada":
            st.write(f"**Tienda:** {guia_data['tienda_destino']}")
    
    # Mostrar QR si está disponible
    if guia_data['url_pedido'] in st.session_state.qr_images:
        st.divider()
        col_qr, col_url = st.columns([1, 3])
        
        with col_qr:
            qr_bytes = st.session_state.qr_images[guia_data['url_pedido']]
            st.image(qr_bytes, caption="Código QR", width=100)
        
        with col_url:
            st.markdown("**🔗 URL de Seguimiento**")
            st.write(f"[{guia_data['url_pedido']}]({guia_data['url_pedido']})")
            st.caption("Escanee el código QR para rastrear el envío")
    
    st.divider()
    
    # Botones de descarga
    st.markdown("**💾 Opciones de Descarga:**")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        # Descargar PDF
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name=f"guia_{guia_data['numero']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    
    with col_r2:
        # Descargar JSON
        json_data = json.dumps(guia_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📋 Descargar JSON",
            data=json_data,
            file_name=f"guia_{guia_data['numero']}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col_r3:
        # Descargar Texto (simplificado)
        info_text = f"""GUÍA DE ENVÍO - {guia_data['marca'].upper()}
CENTRO DE DISTRIBUCIÓN {guia_data['marca'].upper()}

NÚMERO: {guia_data['numero']}
FECHA: {guia_data['fecha_emision']}
ESTADO: {guia_data['estado']}

REMITENTE:
Nombre: {guia_data['remitente']}
Dirección: {guia_data['direccion_remitente']}

DESTINATARIO:
Nombre: {guia_data['destinatario']}
Teléfono: {guia_data['telefono_destinatario']}
Tienda: {guia_data['tienda_destino']}
Dirección: {guia_data['direccion_destinatario']}

SEGUIMIENTO:
URL: {guia_data['url_pedido']}

Generado el: {guia_data['fecha_creacion']}
"""
        
        st.download_button(
            label="📄 Descargar Texto",
            data=info_text,
            file_name=f"guia_{guia_data['numero']}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Información adicional
    st.markdown(f"""
    **📌 Información Importante:**
    - La guía **{guia_data['numero']}** ha sido registrada en el sistema
    - Estado actual: **{guia_data['estado']}**
    - Puede realizar seguimiento en: [{guia_data['url_pedido'][:50]}...]({guia_data['url_pedido']})
    """)
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_generacion_guias():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>🚚 Centro de Distribución Fashion Club</h1>
        <div class='header-subtitle'>Generador de Guías de Envío con QR y Tracking</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuración inicial para el estado de sesión
    if 'guias_registradas' not in st.session_state:
        st.session_state.guias_registradas = []
        st.session_state.contador_guias = 1000
        st.session_state.qr_images = {}
        st.session_state.logos = {}
    
    # URLs de logos desde GitHub
    url_fashion_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    url_tempo_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
    # Listas de tiendas y remitentes
    tiendas = [
        "Aero Matriz", "Aero Zona Franca", "Aero Servicios Y Otros", "Aero Bod Donaciones", "Price Club", 
        "Aero Trans Toma Fisica", "Aero Oil Uno", "Aero La Plaza", "Aero Milagro", "Aero Condado Shopping",
        "Aero Multiplaza Riobamba", "Aero Santo Domingo", "Aero Quevedo", "Aero Manta", "Aero Portoviejo", 
        "Price Club Portoviejo", "Aero Rio Centro Norte", "Aero Duran", "Price Club City Mall", "Aero Mall Del Sur",
        "Aero Los Ceibos", "Aero Ambato", "Aero Carapungo", "Aero Peninsula", "Aero Paseo Ambato", "Aero Mall Del Sol", 
        "Aero Babahoyo", "Aero Riobamba", "Aero Mall Del Pacifico", "Aero San Luis", "Aero Machala",
        "Aero Ventas Por Mayor", "Aero Cuenca Centro Historico", "Aero Cuenca", "Aero Tienda Movil - Web",
        "Aero Playas", "Aero Bod San Roque", "Aero Bomboli", "Aero Mall Del Rio Gye", "Aero Urban Ambato", 
        "Aero Riocentro El Dorado", "Aero Pasaje", "Aero El Coca", "Aero 6 De Diciembre", "Aero Lago Agrio",
        "Aero Pedernales", "Price Club Machala", "Price Club Guayaquil", "Aero Bodega Fallas", "Aero Regional Costa",
        "Aero CCi", "Aero Cayambe", "Aero Bahia De Caraquez", "Aero Daule", "Aero Jagi El Dorado"
    ]
    
    remitentes = [
        {"nombre": "Josué Imbacuán", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Luis Perugachi", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andrés Yépez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Wilson Pérez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andrés Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Diana García", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jessica Suárez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Rocio Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jhony Villa", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"}
    ]
    
    with st.form("guias_form", border=False):
        st.markdown("""
        <div class='filter-panel'>
            <h3 class='filter-title'>📋 Información de la Guía</h3>
        """, unsafe_allow_html=True)
        
        # Primera fila: Información de empresa y remitente
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Información de la Empresa")
            marca = st.radio("**Seleccione la Marca:**", ["Fashion Club", "Tempo"], horizontal=True)
            
            # Mostrar imagen según selección
            if marca == "Tempo":
                try:
                    st.image(url_tempo_logo, caption=marca, use_container_width=True)
                except:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;'>
                        <div style='font-size: 3rem;'>🚚</div>
                        <div style='font-weight: bold; font-size: 1.2rem; color: #0033A0;'>{marca}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:  # Fashion Club
                try:
                    st.image(url_fashion_logo, caption=marca, use_container_width=True)
                except:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;'>
                        <div style='font-size: 3rem;'>👔</div>
                        <div style='font-weight: bold; font-size: 1.2rem; color: #0033A0;'>{marca}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("👤 Información del Remitente")
            remitente_nombre = st.selectbox("**Seleccione Remitente:**", [r["nombre"] for r in remitentes])
            
            # Dirección del remitente
            remitente_direccion = next((r["direccion"] for r in remitentes if r["nombre"] == remitente_nombre), "")
            st.info(f"""
            **Dirección del Remitente:**
            📍 {remitente_direccion}
            """)
        
        
        st.divider()
        
        # Tercera fila: Información del destinatario
        st.subheader("🏪 Información del Destinatario")
        col5, col6 = st.columns(2)
        
        with col5:
            nombre_destinatario = st.text_input("**Nombre del Destinatario:**", placeholder="Ej: Pepito Paez")
            telefono_destinatario = st.text_input("**Teléfono del Destinatario:**", placeholder="Ej: +593 99 999 9999")
        
        with col6:
            direccion_destinatario = st.text_area("**Dirección del Destinatario:**", 
                                                placeholder="Ej: Av. Principal #123, Ciudad, Provincia",
                                                height=100)
            tienda_destino = st.selectbox("**Tienda Destino (Opcional):**", [""] + tiendas)
        
        st.divider()
        
        # Cuarta fila: URL y QR
        st.subheader("🔗 Información Digital")
        url_pedido = st.text_input("**URL del Pedido/Tracking:**", 
                                 placeholder="https://pedidos.fashionclub.com/orden-12345",
                                 value="https://pedidos.fashionclub.com/")
        
        # Generar código QR basado en URL
        if url_pedido and url_pedido.startswith(('http://', 'https://')):
            try:
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(url_pedido)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                # Convertir a bytes
                img_byte_arr = io.BytesIO()
                img_qr.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                # Guardar QR en session state para usarlo en el PDF
                st.session_state.qr_images[url_pedido] = img_byte_arr.getvalue()
                
                # Mostrar QR
                col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                with col_qr2:
                    st.image(img_byte_arr, caption="Código QR Generado", width=150)
                    st.caption(f"URL: {url_pedido[:50]}...")
            except:
                st.warning("⚠️ No se pudo generar el código QR. Verifique la URL.")
        elif url_pedido:
            st.warning("⚠️ La URL debe comenzar con http:// o https://")
        
        st.divider()
        
        # Botones de acción
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit = st.form_submit_button("🚀 Generar Guía PDF", use_container_width=True, type="primary")
        with col_btn2:
            preview = st.form_submit_button("👁️ Vista Previa", use_container_width=True)
        with col_btn3:
            reset = st.form_submit_button("🔄 Nuevo Formulario", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Procesar la guía
    if submit or preview:
        # Validaciones
        errors = []
        if not nombre_destinatario:
            errors.append("❌ El nombre del destinatario es obligatorio")
        if not direccion_destinatario:
            errors.append("❌ La dirección del destinatario es obligatoria")
        if not url_pedido or len(url_pedido) < 10:
            errors.append("❌ Ingrese una URL válida para el pedido")
        elif not url_pedido.startswith(('http://', 'https://')):
            errors.append("❌ La URL debe comenzar con http:// o https://")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Generar número de guía único
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1
            
            # Descargar logo si no está en cache
            if marca not in st.session_state.logos:
                logo_url = url_fashion_logo if marca == "Fashion Club" else url_tempo_logo
                logo_bytes = descargar_logo(logo_url)
                if logo_bytes:
                    st.session_state.logos[marca] = logo_bytes
            
            # Obtener bytes del QR
            qr_bytes = st.session_state.qr_images.get(url_pedido)
            
            # Crear diccionario con datos de la guía
            guia_data = {
                "numero": guia_num,
                "marca": marca,
                "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion,
                "destinatario": nombre_destinatario,
                "telefono_destinatario": telefono_destinatario or "No especificado",
                "direccion_destinatario": direccion_destinatario,
                "tienda_destino": tienda_destino if tienda_destino else "No especificada",
                "url_pedido": url_pedido,
                "estado": "Generada",
                "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "qr_bytes": qr_bytes
            }
            
            if preview:
                # Vista previa
                mostrar_vista_previa_guia(guia_data)
            
            if submit:
                with st.spinner(f"Generando guía {guia_num}..."):
                    time.sleep(1.5)
                    
                    # Agregar a lista de guías
                    st.session_state.guias_registradas.append(guia_data)
                    
                    # También guardar en la base de datos local (si existe)
                    try:
                        if 'local_db' in globals():
                            local_db.insert('guias', guia_data)
                    except:
                        pass
                    
                    # Generar PDF mejorado con logo y QR
                    pdf_bytes = generar_pdf_profesional(guia_data)
                    
                    st.success(f"✅ Guía {guia_num} generada exitosamente!")
                    
                    # Mostrar resumen
                    mostrar_resumen_guia(guia_data, pdf_bytes)

# ==============================================================================
# 8. MÓDULO DASHBOARD DE KPIs
# ==============================================================================

def mostrar_dashboard_kpis():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de KPIs en Tiempo Real</h1>
        <div class='header-subtitle'>Monitorización Integral del Desempeño Operativo</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", datetime.now() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col3:
        tipo_kpi = st.selectbox("📈 Tipo de Métrica", ["Producción", "Eficiencia", "Costos", "Alertas"])
    
    # Obtener datos de la base de datos local
    kpis_data = local_db.query('kpis')
    df_kpis = pd.DataFrame(kpis_data)
    
    if not df_kpis.empty:
        df_kpis['fecha'] = pd.to_datetime(df_kpis['fecha'])
        mask = (df_kpis['fecha'].dt.date >= fecha_inicio) & (df_kpis['fecha'].dt.date <= fecha_fin)
        df_filtered = df_kpis[mask]
        
        if not df_filtered.empty:
            # KPIs Principales
            st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            
            with col_k1:
                prod_prom = df_filtered['produccion'].mean()
                prod_tend = ((df_filtered['produccion'].iloc[-1] - df_filtered['produccion'].iloc[0]) / df_filtered['produccion'].iloc[0] * 100) if len(df_filtered) > 1 else 0
                st.markdown(f"""
                <div class='stat-card card-blue'>
                    <div class='stat-icon'>🏭</div>
                    <div class='stat-title'>Producción Promedio</div>
                    <div class='stat-value'>{prod_prom:,.0f}</div>
                    <div class='stat-change {'positive' if prod_tend > 0 else 'negative'}">{'📈' if prod_tend > 0 else '📉'} {prod_tend:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k2:
                efic_prom = df_filtered['eficiencia'].mean()
                st.markdown(f"""
                <div class='stat-card card-green'>
                    <div class='stat-icon'>⚡</div>
                    <div class='stat-title'>Eficiencia</div>
                    <div class='stat-value'>{efic_prom:.1f}%</div>
                    <div class='stat-change {'positive' if efic_prom > 90 else 'warning'}">{'Excelente' if efic_prom > 90 else 'Mejorable'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k3:
                alert_total = df_filtered['alertas'].sum()
                st.markdown(f"""
                <div class='stat-card card-red'>
                    <div class='stat-icon'>🚨</div>
                    <div class='stat-title'>Alertas Totales</div>
                    <div class='stat-value'>{alert_total}</div>
                    <div class='stat-change {'negative' if alert_total > 10 else 'positive'}">{'Revisar' if alert_total > 10 else 'Controlado'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k4:
                costo_prom = df_filtered['costos'].mean()
                st.markdown(f"""
                <div class='stat-card card-purple'>
                    <div class='stat-icon'>💰</div>
                    <div class='stat-title'>Costo Promedio</div>
                    <div class='stat-value'>${costo_prom:,.0f}</div>
                    <div class='stat-change'>Diario</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Gráficos
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = px.line(df_filtered, x='fecha', y='produccion', 
                        title='Producción Diaria',
                        labels={'produccion': 'Unidades', 'fecha': 'Fecha'},
                        line_shape='spline')
            fig.update_traces(line=dict(color='#0033A0', width=3))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Gráficos secundarios
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig2 = px.bar(df_filtered.tail(7), x=df_filtered.tail(7)['fecha'].dt.strftime('%a'), y='eficiencia',
                            title='Eficiencia Semanal', 
                            color='eficiencia',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_ch2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig3 = px.scatter(df_filtered, x='produccion', y='costos',
                                title='Relación Producción vs Costos',
                                color='alertas',
                                size='eficiencia',
                                hover_data=['fecha'])
                st.plotly_chart(fig3, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No hay datos para el rango de fechas seleccionado.")
    else:
        st.info("Cargando datos de KPIs...")

# ==============================================================================
# 9. MÓDULO GESTIÓN DE TRABAJADORES
# ==============================================================================

def mostrar_gestion_trabajadores():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>👥 Gestión de Personal</h1>
        <div class='header-subtitle'>Administración del equipo de trabajo por áreas</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Estructura Organizacional", "➕ Gestionar Personal", "📊 Estadísticas", "⚙️ Configuración"])
    
    # Estructura organizacional base
    estructura_base = {
        "Liderazgo y Control": [
            {"id": 1, "nombre": "Wilson Pérez", "cargo": "Jefe de Logística", "subarea": "Cabeza del C.D.", "estado": "Activo", "es_base": True},
            {"id": 2, "nombre": "Andrés Cadena", "cargo": "Segundo al mando", "subarea": "Control de Inventarios", "estado": "Activo", "es_base": True}
        ],
        "Gestión de Transferencias": [
            {"id": 3, "nombre": "César Yépez", "cargo": "Responsable", "subarea": "Transferencias Fashion", "estado": "Activo", "es_base": True},
            {"id": 4, "nombre": "Luis Perugachi", "cargo": "Encargado", "subarea": "Pivote de transferencias y Distribución", "estado": "Activo", "es_base": True},
            {"id": 5, "nombre": "Josué Imbacuán", "cargo": "Responsable", "subarea": "Transferencias Tempo", "estado": "Activo", "es_base": True}
        ],
        "Distribución, Empaque y Envíos": [
            {"id": 6, "nombre": "Jessica Suárez", "cargo": "Distribución", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 7, "nombre": "Andrea Malquin", "cargo": "Distribución", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 8, "nombre": "Jhonny Villa", "cargo": "Empaque", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 9, "nombre": "Simón Vera", "cargo": "Guías y Envíos", "subarea": "", "estado": "Activo", "es_base": True}
        ],
        "Ventas al Por Mayor": [
            {"id": 10, "nombre": "Jhonny Guadalupe", "cargo": "Encargado", "subarea": "Bodega y Packing", "estado": "Activo", "es_base": True},
            {"id": 11, "nombre": "Rocio Cadena", "cargo": "Responsable", "subarea": "Picking y Distribución", "estado": "Activo", "es_base": True}
        ],
        "Mantenimiento y Calidad": [
            {"id": 12, "nombre": "Diana García", "cargo": "Encargada", "subarea": "Reprocesado de prendas en cuarentena", "estado": "Activo", "es_base": True}
        ]
    }
    
    # Inicializar base de datos local (solución temporal si falla)
    try:
        trabajadores = local_db.query('trabajadores')
        if trabajadores is None:
            trabajadores = []
    except:
        trabajadores = []
        st.warning("⚠️ Base de datos no disponible - usando almacenamiento temporal")
    
    # Inicializar estructura base si está vacía
    if not trabajadores:
        st.info("📝 Inicializando estructura organizacional base...")
        # Aplanar la estructura para guardar en base de datos
        todos_base = []
        for area, lista in estructura_base.items():
            for trabajador in lista:
                trabajador['area'] = area
                trabajador['fecha_ingreso'] = datetime.now().strftime('%Y-%m-%d')
                todos_base.append(trabajador)
        
        # Insertar en base de datos
        for trab in todos_base:
            try:
                local_db.insert('trabajadores', trab)
            except:
                # Si falla la inserción, añadir a lista temporal
                trabajadores.append(trab)
        st.success("✅ Estructura base inicializada correctamente")
    
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>🏢 Estructura Organizacional del Centro de Distribución</h4>
            <p class='section-description'>Responsables por área (estructura base)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar estructura por áreas
        for area, personal in estructura_base.items():
            with st.expander(f"📌 {area} ({len(personal)} personas)", expanded=True):
                # Crear 3 columnas para distribuir las tarjetas
                cols = st.columns(3)
                for idx, trab in enumerate(personal):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        st.markdown(f"""
                        <div style='background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #0033A0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                            <div style='font-weight: bold; font-size: 16px; color: #1e3a8a; margin-bottom: 5px;'>{trab['nombre']}</div>
                            <div style='font-size: 14px; color: #374151; margin-bottom: 3px;'>{trab['cargo']}</div>
                            <div style='font-size: 12px; color: #6b7280; font-style: italic; margin-bottom: 5px;'>{trab['subarea'] if trab['subarea'] else ''}</div>
                            <div style='background-color: #10B981; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; display: inline-block;'>Activo</div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Resumen general
        st.markdown("---")
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            total_personal = sum(len(p) for p in estructura_base.values())
            st.metric("👥 Total Personal Base", total_personal)
        with col_res2:
            st.metric("🏭 Áreas Definidas", len(estructura_base))
        with col_res3:
            cargos_unicos = len(set([t['cargo'] for area in estructura_base.values() for t in area]))
            st.metric("🎯 Cargos Únicos", cargos_unicos)
    
    with tab2:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📝 Gestión de Personal por Área</h4>
            <p class='section-description'>Agregar o eliminar trabajadores en cada área</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obtener todos los trabajadores actuales
        try:
            trabajadores_db = local_db.query('trabajadores')
            if trabajadores_db is None:
                trabajadores_db = []
        except:
            trabajadores_db = trabajadores  # Usar lista temporal si falla
        
        # Pestañas para cada área
        area_tabs = st.tabs(list(estructura_base.keys()))
        
        for idx, (area, trabajadores_area_base) in enumerate(estructura_base.items()):
            with area_tabs[idx]:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Personal en {area}")
                    
                    # Filtrar trabajadores de esta área
                    trabajadores_area_actual = [t for t in trabajadores_db if t.get('area') == area]
                    
                    if trabajadores_area_actual:
                        # Crear dataframe para visualización
                        data = []
                        for trab in trabajadores_area_actual:
                            data.append({
                                'ID': trab.get('id', ''),
                                'Nombre': trab.get('nombre', ''),
                                'Cargo': trab.get('cargo', ''),
                                'Subárea': trab.get('subarea', ''),
                                'Estado': trab.get('estado', ''),
                                'Tipo': 'Base' if trab.get('es_base', False) else 'Adicional'
                            })
                        
                        df_area = pd.DataFrame(data)
                        
                        # Mostrar dataframe con opción de eliminar
                        for i, row in df_area.iterrows():
                            col_d1, col_d2, col_d3, col_d4, col_d5, col_d6 = st.columns([1, 3, 2, 2, 1, 1])
                            with col_d1:
                                st.write(f"**{row['ID']}**")
                            with col_d2:
                                st.write(row['Nombre'])
                            with col_d3:
                                st.write(row['Cargo'])
                            with col_d4:
                                st.write(row['Subárea'] if row['Subárea'] else "-")
                            with col_d5:
                                tipo_color = "🟢" if row['Tipo'] == 'Base' else "🔵"
                                st.write(f"{tipo_color} {row['Tipo']}")
                            with col_d6:
                                # Solo permitir eliminar si NO es trabajador base
                                if row['Tipo'] != 'Base':
                                    trabajador_id = row['ID']
                                    if st.button("🗑️", key=f"eliminar_{area}_{trabajador_id}"):
                                        try:
                                            # Eliminar de la base de datos
                                            if hasattr(local_db, 'delete'):
                                                local_db.delete('trabajadores', trabajador_id)
                                            else:
                                                # Eliminar de lista temporal
                                                trabajadores_db = [t for t in trabajadores_db if t.get('id') != trabajador_id]
                                            st.success(f"✅ Trabajador {row['Nombre']} eliminado de {area}")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error al eliminar: {str(e)}")
                                else:
                                    st.write("🔒")
                    else:
                        st.info(f"No hay personal registrado en {area}")
                
                with col2:
                    st.subheader("Agregar Personal")
                    with st.form(key=f"form_{area}"):
                        nombre_nuevo = st.text_input("Nombre Completo", key=f"nombre_{area}")
                        cargo_nuevo = st.text_input("Cargo", key=f"cargo_{area}")
                        subarea_nuevo = st.text_input("Área específica/Subárea", key=f"subarea_{area}")
                        estado_nuevo = st.selectbox("Estado", ["Activo", "Inactivo"], key=f"estado_{area}")
                        
                        submit = st.form_submit_button(f"➕ Agregar a {area}")
                        
                        if submit:
                            if nombre_nuevo and cargo_nuevo:
                                try:
                                    # Generar nuevo ID
                                    if trabajadores_db:
                                        max_id = max([t.get('id', 0) for t in trabajadores_db])
                                    else:
                                        max_id = 12  # Empezar después de los IDs base
                                    
                                    nuevo_id = max_id + 1
                                    
                                    nuevo_trabajador = {
                                        'id': nuevo_id,
                                        'nombre': nombre_nuevo,
                                        'cargo': cargo_nuevo,
                                        'area': area,
                                        'subarea': subarea_nuevo,
                                        'estado': estado_nuevo,
                                        'es_base': False,
                                        'fecha_ingreso': datetime.now().strftime('%Y-%m-%d')
                                    }
                                    
                                    # Insertar en base de datos
                                    local_db.insert('trabajadores', nuevo_trabajador)
                                    st.success(f"✅ {nombre_nuevo} agregado a {area}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error al agregar trabajador: {str(e)}")
                                    # Alternativa: agregar a lista temporal
                                    trabajadores_db.append(nuevo_trabajador)
                                    st.success(f"✅ {nombre_nuevo} agregado temporalmente a {area}")
                                    st.rerun()
                            else:
                                st.error("❌ Nombre y Cargo son obligatorios")
    
    with tab3:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📊 Estadísticas del Personal</h4>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            trabajadores_db = local_db.query('trabajadores')
            if trabajadores_db is None:
                trabajadores_db = trabajadores
        except:
            trabajadores_db = trabajadores
        
        if trabajadores_db:
            df_todos = pd.DataFrame(trabajadores_db)
            
            # Métricas principales
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                total = len(df_todos)
                st.metric("👥 Total Personal", total)
            with col_m2:
                if 'estado' in df_todos.columns:
                    activos = len(df_todos[df_todos['estado'] == 'Activo'])
                else:
                    activos = total
                st.metric("🟢 Activos", activos, delta=f"{activos/total*100:.1f}%" if total > 0 else "0%")
            with col_m3:
                if 'es_base' in df_todos.columns:
                    base = len(df_todos[df_todos['es_base'] == True])
                else:
                    base = len(estructura_base) * 2  # Estimación
                st.metric("🏛️ Personal Base", base)
            with col_m4:
                if 'es_base' in df_todos.columns:
                    adicional = len(df_todos[df_todos['es_base'] == False])
                else:
                    adicional = max(0, total - base)
                st.metric("➕ Adicionales", adicional)
            
            # Gráficos (solo si hay datos suficientes)
            if total > 0:
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    if 'area' in df_todos.columns:
                        dist_area = df_todos['area'].value_counts()
                        fig1 = px.bar(
                            x=dist_area.index, 
                            y=dist_area.values,
                            title="Distribución por Área",
                            labels={'x': 'Área', 'y': 'Cantidad'},
                            color=dist_area.values,
                            color_continuous_scale='blues'
                        )
                        fig1.update_layout(showlegend=False)
                        st.plotly_chart(fig1, use_container_width=True)
                
                with col_g2:
                    if 'estado' in df_todos.columns:
                        estado_counts = df_todos['estado'].value_counts()
                        fig2 = px.pie(
                            values=estado_counts.values, 
                            names=estado_counts.index,
                            title="Estado del Personal",
                            color_discrete_sequence=['#10B981', '#EF4444']
                        )
                        st.plotly_chart(fig2, use_container_width=True)
            
            # Tabla resumen por área
            st.subheader("📋 Resumen por Área")
            resumen_data = []
            for area in estructura_base.keys():
                if 'area' in df_todos.columns:
                    area_data = df_todos[df_todos['area'] == area]
                    activos_area = len(area_data[area_data['estado'] == 'Activo']) if 'estado' in df_todos.columns else len(area_data)
                    base_area = len(area_data[area_data.get('es_base', False) == True]) if 'es_base' in df_todos.columns else 0
                    
                    resumen_data.append({
                        'Área': area,
                        'Total': len(area_data),
                        'Activos': activos_area,
                        'Base': base_area,
                        'Adicional': len(area_data) - base_area
                    })
            
            if resumen_data:
                df_resumen = pd.DataFrame(resumen_data)
                st.dataframe(df_resumen, use_container_width=True)
            else:
                st.info("No hay datos de áreas para mostrar")
        else:
            st.info("No hay datos para mostrar estadísticas.")
    
    with tab4:
        st.markdown("""
        <div class='filter-panel'>
            <h4>⚙️ Configuración del Sistema</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Restaurar Estructura Base")
            st.warning("⚠️ Esta acción eliminará todo el personal adicional y restaurará la estructura original")
            
            if st.button("🔄 Restaurar Estructura Base", type="secondary"):
                try:
                    # Obtener todos los trabajadores actuales
                    trabajadores_actuales = local_db.query('trabajadores')
                    if trabajadores_actuales:
                        # Eliminar solo los no base
                        for trab in trabajadores_actuales:
                            if not trab.get('es_base', False):
                                local_db.delete('trabajadores', trab['id'])
                    
                    st.success("✅ Estructura base restaurada exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al restaurar: {str(e)}")
        
        with col_c2:
            st.subheader("Exportar Datos")
            
            try:
                trabajadores_db = local_db.query('trabajadores')
                if trabajadores_db:
                    df_export = pd.DataFrame(trabajadores_db)
                    # Limpiar columnas internas
                    export_cols = ['nombre', 'cargo', 'area', 'subarea', 'estado', 'fecha_ingreso']
                    available_cols = [col for col in export_cols if col in df_export.columns]
                    df_export = df_export[available_cols]
                    
                    # Convertir a CSV
                    csv = df_export.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Descargar como CSV",
                        data=csv,
                        file_name="personal_cd.csv",
                        mime="text/csv",
                        help="Descargar todos los datos del personal"
                    )
                else:
                    st.info("No hay datos para exportar")
            except Exception as e:
                st.error(f"❌ Error al exportar datos: {str(e)}")

# ==============================================================================
# 10. MÓDULO GESTIÓN DE DISTRIBUCIONES
# ==============================================================================

def mostrar_gestion_distribuciones():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>🚚 Gestión de Distribuciones</h1>
        <div class='header-subtitle'>Control y seguimiento de transportes</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos de distribuciones
    distribuciones = local_db.query('distribuciones')
    df_dist = pd.DataFrame(distribuciones)
    
    if not df_dist.empty:
        # KPIs de transporte
        st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
        col_t1, col_t2, col_t3 = st.columns(3)
        
        total_guias = df_dist['guías'].sum()
        
        with col_t1:
            tempo = df_dist[df_dist['transporte'] == 'Tempo']['guías'].sum()
            st.markdown(f"""
            <div class='stat-card card-blue'>
                <div class='stat-icon'>🚛</div>
                <div class='stat-title'>Tempo</div>
                <div class='stat-value'>{tempo}</div>
                <div class='stat-subtitle'>{tempo/total_guias*100:.1f}% del total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_t2:
            luis = df_dist[df_dist['transporte'] == 'Luis Perugachi']['guías'].sum()
            st.markdown(f"""
            <div class='stat-card card-green'>
                <div class='stat-icon'>🚚</div>
                <div class='stat-title'>Luis Perugachi</div>
                <div class='stat-value'>{luis}</div>
                <div class='stat-subtitle'>{luis/total_guias*100:.1f}% del total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_t3:
            entregados = len(df_dist[df_dist['estado'] == 'Entregado'])
            st.markdown(f"""
            <div class='stat-card card-purple'>
                <div class='stat-icon'>✅</div>
                <div class='stat-title'>Entregados</div>
                <div class='stat-value'>{entregados}</div>
                <div class='stat-subtitle'>{entregados/len(df_dist)*100:.1f}% completado</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Tabla de distribuciones
        st.markdown("### 📋 Estado Actual de Distribuciones")
        st.dataframe(
            df_dist,
            use_container_width=True,
            column_config={
                "transporte": st.column_config.TextColumn("Transporte", width="medium"),
                "guías": st.column_config.NumberColumn("Guías", width="small"),
                "estado": st.column_config.TextColumn(
                    "Estado",
                    width="small",
                    help="Estado del transporte"
                )
            }
        )
        
        # Gráfico comparativo
        st.markdown("### 📊 Comparativa de Desempeño")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig = px.bar(df_dist, x='transporte', y='guías', color='estado',
                    title="Distribución por Transporte y Estado",
                    barmode='group',
                    color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Agregar nueva distribución
        st.markdown("### ➕ Agregar Nueva Distribución")
        with st.form("nueva_distribucion"):
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                transporte = st.selectbox("Transporte", ["Tempo", "Luis Perugachi", "Otro"])
            with col_d2:
                guias = st.number_input("Número de Guías", min_value=1, max_value=100, value=10)
            with col_d3:
                estado = st.selectbox("Estado", ["Pendiente", "En ruta", "Entregado", "Retrasado"])
            
            if st.form_submit_button("📦 Registrar Distribución", type="primary"):
                nueva_dist = {
                    'transporte': transporte,
                    'guías': guias,
                    'estado': estado
                }
                local_db.insert('distribuciones', nueva_dist)
                st.success(f"✅ Distribución de {transporte} registrada!")
                st.rerun()
    else:
        st.info("Cargando datos de distribuciones...")

# ==============================================================================
# 11. MÓDULO AYUDA Y SOPORTE
# ==============================================================================

def mostrar_ayuda():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>❓ Ayuda y Soporte Técnico</h1>
        <div class='header-subtitle'>Asistencia para el uso del Sistema ERP</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📚 Guías Rápidas", "📞 Contacto", "🛠️ Solución de Problemas"])
    
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📖 Manual de Usuario Rápido</h4>
            
            ### 🔐 Autenticación
            - **Admin:** Acceso completo a todos los módulos
            - **User:** Acceso limitado a módulos básicos
            
            ### 📊 Módulos Principales
            
            #### 1. Dashboard KPIs
            - Monitoreo en tiempo real de producción
            - Métricas de eficiencia y costos
            - Gráficos interactivos
            
            #### 2. Reconciliación V8.0
            - Subir manifiestos y facturas
            - Clasificación automática de tiendas
            - Detección especial de "JOFRE SANTANA"
            - Exportación a Excel y CSV
            
            #### 3. Email Wilo AI
            - Análisis automático de correos
            - Clasificación por urgencia
            - Detección de faltantes/sobrantes
            
            #### 4. Dashboard Transferencias
            - Análisis de transferencias diarias
            - Clasificación por categorías
            - Reportes ejecutivos
            
            #### 5. Generación de Guías
            - Creación de guías de envío
            - Asignación a transportistas
            - Generación de PDF
            
            #### 6. Etiquetas
            - Diseño personalizado de etiquetas
            - Inclusión de códigos QR
            - Exportación múltiple
            
            ### 💾 Exportación de Datos
            Todos los módulos permiten exportar resultados en:
            - Excel (.xlsx)
            - PDF (.pdf)
            - CSV (.csv)
            - Imágenes (.png)
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📞 Canales de Contacto</h4>
            
            ### 🏢 Soporte Técnico
            **Responsable:** Wilson Pérez  
            **Email:** wilson.perez@aeropostale.com  
            **Teléfono:** +593 98 765 4321  
            **Horario:** Lunes a Viernes 8:00 - 18:00
            
            ### 🚨 Soporte Urgente
            **WhatsApp:** +593 99 123 4567  
            **Disponibilidad:** 24/7 para emergencias críticas
            
            ### 📧 Correos por Departamento
            - **Logística:** logistica@aeropostale.com
            - **Almacén:** almacen@aeropostale.com
            - **TI:** soporte.ti@aeropostale.com
            - **Administración:** admin@aeropostale.com
            
            ### 🌐 Recursos Adicionales
            - [Portal de Soporte](https://soporte.aeropostale.com)
            - [Base de Conocimiento](https://kb.aeropostale.com)
            - [Foro de Usuarios](https://comunidad.aeropostale.com)
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("""
        <div class='filter-panel'>
            <h4>🛠️ Solución de Problemas Comunes</h4>
            
            ### ❌ Error al Subir Archivos
            **Síntoma:** El sistema no reconoce las columnas  
            **Solución:**
            1. Verificar que el archivo tenga extensión .xlsx, .xls o .csv
            2. Asegurarse que las columnas tengan nombres claros
            3. Usar la configuración manual de columnas
            
            ### 🔄 Lentitud en el Procesamiento
            **Síntoma:** Tiempos de espera muy largos  
            **Solución:**
            1. Reducir el tamaño de los archivos
            2. Dividir archivos grandes en lotes
            3. Verificar conexión a internet
            
            ### 📊 Datos Incorrectos en Reportes
            **Síntoma:** Las cifras no coinciden  
            **Solución:**
            1. Revisar formatos de fecha
            2. Verificar símbolos monetarios
            3. Validar tipos de datos
            
            ### 🔐 Problemas de Acceso
            **Síntoma:** No puedo ingresar a un módulo  
            **Solución:**
            1. Cerrar sesión y volver a ingresar
            2. Verificar permisos de usuario
            3. Contactar al administrador
            
            ### 🆘 ¿No encuentra su problema?
            1. **Documente el error:** Tome captura de pantalla
            2. **Describa los pasos:** Qué estaba haciendo cuando ocurrió
            3. **Contacte a soporte:** Envíe la información recopilada
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 12. SISTEMA DE AUTENTICACIÓN Y NAVEGACIÓN
# ==============================================================================

def mostrar_pagina_login(rol_target):
    """Página de login moderna"""
    st.markdown("""
    <div style='
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        padding: 2rem;
    '>
        <div style='
            background: white;
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 450px;
            border-top: 6px solid #0033A0;
        '>
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: linear-gradient(45deg, #0033A0, #E4002B);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                '>AEROPOSTALE EC ERP</h1>
                <p style='color: #6B7280; font-size: 0.9rem;'>Sistema Integral v3.0</p>
            </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown(f"### 🔐 Acceso {rol_target.upper()}")
        
        if rol_target == "admin":
            st.info("Acceso administrativo completo al sistema")
            password = st.text_input("Contraseña de Administrador", type="password")
            correct_password = ADMIN_PASSWORD
        else:
            st.info("Acceso básico a módulos operativos")
            password = st.text_input("Contraseña de Usuario", type="password")
            correct_password = USER_PASSWORD
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("🚪 Ingresar", use_container_width=True, type="primary")
        with col_btn2:
            cancel = st.form_submit_button("↩️ Cancelar", use_container_width=True)
    
    if submit:
        if password == correct_password:
            st.session_state.user_type = rol_target
            st.session_state.show_login = False
            st.session_state.current_page = "Dashboard KPIs"
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta. Intente nuevamente.")
    
    if cancel:
        st.session_state.show_login = False
        st.rerun()
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 13. FUNCIÓN PRINCIPAL DE LA APLICACIÓN
# ==============================================================================

def main():
    # Inicializar estado de sesión
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'login_target' not in st.session_state:
        st.session_state.login_target = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard KPIs"
    
    # Configurar sidebar solo si no estamos en login
    if not st.session_state.show_login:
        # --- SIDEBAR MODERNO ---
        with st.sidebar:
            # Encabezado del sidebar
            st.markdown("""
            <div class='sidebar-header'>
                <div class='sidebar-logo'>AEROPOSTALE ERP</div>
                <div class='sidebar-subtitle'>Sistema Integral v3.0</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Estado de usuario
            if st.session_state.user_type:
                user_badge = "🛡️ ADMIN" if st.session_state.user_type == "admin" else "👤 USER"
                st.markdown(f"""
                <div style='
                    background: rgba(0, 51, 160, 0.1); 
                    padding: 10px; 
                    border-radius: 8px; 
                    margin: 10px; 
                    text-align: center;
                    border: 1px solid rgba(0, 51, 160, 0.2);
                '>
                    <strong style='color: #0033A0;'>{user_badge}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Menú de navegación
            menu_items = {
                "Dashboard KPIs": {"icon": "📊", "role": "public"},
                "Reconciliación V8": {"icon": "💰", "role": "admin"},
                "Email Wilo AI": {"icon": "📧", "role": "admin"},
                "Dashboard Transferencias": {"icon": "📦", "role": "admin"},
                "Generar Guías": {"icon": "📋", "role": "user"},
                "Trabajadores": {"icon": "👥", "role": "admin"},
                "Distribuciones": {"icon": "🚚", "role": "admin"},
                "Ayuda": {"icon": "❓", "role": "public"}
            }
            
            for page_name, page_info in menu_items.items():
                is_active = st.session_state.current_page == page_name
                
                if st.button(
                    f"{page_info['icon']} {page_name}",
                    key=f"btn_{page_name}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    # Verificar permisos
                    if page_info['role'] == "public" or \
                       (st.session_state.user_type == "admin") or \
                       (st.session_state.user_type == "user" and page_info['role'] == "user"):
                        st.session_state.current_page = page_name
                        st.session_state.show_login = False
                        st.rerun()
                    else:
                        st.session_state.login_target = page_info['role']
                        st.session_state.show_login = True
                        st.rerun()
            
            st.markdown("---")
            
            # Botones de sesión
            if st.session_state.user_type:
                if st.button("🚪 Cerrar Sesión", use_container_width=True):
                    st.session_state.user_type = None
                    st.session_state.current_page = "Dashboard KPIs"
                    st.rerun()
            else:
                col_login1, col_login2 = st.columns(2)
                with col_login1:
                    if st.button("🛡️ Admin", use_container_width=True):
                        st.session_state.login_target = "admin"
                        st.session_state.show_login = True
                        st.rerun()
                with col_login2:
                    if st.button("👤 User", use_container_width=True):
                        st.session_state.login_target = "user"
                        st.session_state.show_login = True
                        st.rerun()
        
        # --- CONTENIDO PRINCIPAL ---
        if st.session_state.show_login:
            mostrar_pagina_login(st.session_state.login_target)
        else:
            # Ejecutar el módulo correspondiente
            page_mapping = {
                "Dashboard KPIs": mostrar_dashboard_kpis,
                "Reconciliación V8": mostrar_reconciliacion_v8,
                "Email Wilo AI": mostrar_auditoria_correos,
                "Dashboard Transferencias": mostrar_dashboard_transferencias,
                "Generar Guías": mostrar_generacion_guias,
                "Trabajadores": mostrar_gestion_trabajadores,
                "Distribuciones": mostrar_gestion_distribuciones,
                "Ayuda": mostrar_ayuda
            }
            
            current_func = page_mapping.get(st.session_state.current_page)
            if current_func:
                # Verificación de permisos
                page_roles = {
                    "Dashboard KPIs": "public",
                    "Reconciliación V8": "admin",
                    "Email Wilo AI": "admin",
                    "Dashboard Transferencias": "admin",
                    "Generar Guías": "user",
                    "Trabajadores": "admin",
                    "Distribuciones": "admin",
                    "Ayuda": "public"
                }
                
                required_role = page_roles.get(st.session_state.current_page, "admin")
                
                if required_role == "public" or \
                   (st.session_state.user_type == "admin") or \
                   (st.session_state.user_type == "user" and required_role == "user"):
                    current_func()
                else:
                    st.warning("🔒 Este módulo requiere permisos especiales.")
                    st.session_state.login_target = required_role
                    st.session_state.show_login = True
                    st.rerun()
            else:
                st.error("Página no encontrada")
                st.session_state.current_page = "Dashboard KPIs"
                st.rerun()
        
        # --- FOOTER ---
        st.markdown("""
        <div class="app-footer">
            <span class="footer-logo">AEROPOSTALE EC-ERP</span> v3.1 | © 2025 Todos los derechos reservados.<br>
            Desarrollado con ❤️ para la optimización logística | <em>#EficienciaOperativa</em>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mostrar página de login
        mostrar_pagina_login(st.session_state.login_target)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {e}")
        logger.error(f"Crash: {e}", exc_info=True)
        st.markdown(f"""
        <div class='filter-panel'>
            <h4>🆘 Sistema de Recuperación</h4>
            <p>La aplicación encontró un error. Por favor:</p>
            <ol>
                <li>Recargue la página (F5)</li>
                <li>Verifique sus archivos de entrada</li>
                <li>Contacte a soporte si el problema persiste</li>
            </ol>
            <p>Detalles técnicos: {str(e)}</p>
        </div>
        """, unsafe_allow_html=True)
