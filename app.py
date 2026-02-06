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
import json
import io
import os
import warnings
import smtplib
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
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed"
)

# --- LOGGING CONFIG ---
if not os.path.exists('logs'): 
    os.makedirs('logs')
logging.basicConfig(filename='logs/app_system.log', level=logging.INFO)
warnings.filterwarnings('ignore')

# --- VARIABLES GLOBALES ---
ADMIN_PASSWORD = "admin123"
USER_PASSWORD = "user123"

# Base de datos simulada en memoria
class LocalDB:
    def __init__(self):
        self.data = {
            'kpis': [],
            'trabajadores': [],
            'distribuciones': [],
            'guias': []
        }
    
    def query(self, table):
        return self.data.get(table, [])
    
    def insert(self, table, record):
        if table not in self.data:
            self.data[table] = []
        self.data[table].append(record)
    
    def delete(self, table, record_id):
        if table in self.data:
            self.data[table] = [r for r in self.data[table] if r.get('id') != record_id]

local_db = LocalDB()

# ==============================================================================
# 1. ESTILOS CSS - MEJORADO Y COMPLETO
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700;800&display=swap');

.stApp {
    font-family: 'Montserrat', sans-serif;
    background-color: #0e1117;
    overflow: hidden;
}

.main-bg {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    z-index: -1;
}

/* Contenedor Ultra-Compacto */
.gallery-container {
    padding: 30px 5% 10px 5%;
    text-align: center;
    max-width: 1400px;
    margin: 0 auto;
}

.brand-title {
    color: white;
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: 15px;
    margin-bottom: 10px;
    text-transform: uppercase;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px rgba(96, 165, 250, 0.5); }
    to { text-shadow: 0 0 20px rgba(244, 114, 182, 0.8); }
}

.brand-subtitle {
    color: #94A3B8;
    font-size: 1rem;
    letter-spacing: 6px;
    margin-bottom: 40px;
    text-transform: uppercase;
    font-weight: 300;
}

/* Grid de módulos */
.modules-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 0 10px;
}

@media (max-width: 1024px) {
    .modules-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .modules-grid { grid-template-columns: 1fr; }
    .brand-title { font-size: 2.5rem; letter-spacing: 10px; }
}

/* Tarjetas Rectangulares Compactas */
.module-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    height: 180px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    position: relative;
    cursor: pointer;
    overflow: hidden;
}

.module-card:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.module-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.7s;
}

.module-card:hover::before {
    left: 100%;
}

.card-icon {
    font-size: 2.8rem;
    margin-bottom: 15px;
    transition: transform 0.3s ease;
}

.module-card:hover .card-icon {
    transform: scale(1.2) rotate(5deg);
}

.card-title {
    color: white;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    text-align: center;
}

.card-description {
    color: #94A3B8;
    font-size: 0.85rem;
    text-align: center;
    margin-top: 8px;
    opacity: 0.8;
    line-height: 1.3;
}

/* Botones invisibles */
.stButton > button.module-btn {
    width: 100% !important;
    height: 180px !important;
    background-color: transparent !important;
    border: none !important;
    color: transparent !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    z-index: 10 !important;
    cursor: pointer !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
}

.sidebar-header {
    text-align: center;
    padding: 20px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 5px;
}

.sidebar-subtitle {
    color: #94A3B8;
    font-size: 0.8rem;
}

/* Contenido interno */
.internal-header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 2rem;
    border-left: 6px solid #60A5FA;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.5rem;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-subtitle {
    font-size: 1rem;
    color: #94A3B8;
    font-weight: 400;
}

/* Tarjetas de estadísticas */
.stat-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    height: 100%;
}

.stat-card:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-3px);
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #60A5FA;
}

.stat-title {
    font-size: 0.9rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: white;
    margin: 0.5rem 0;
}

.stat-change {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
    background: rgba(34, 197, 94, 0.2);
    color: #4ADE80;
}

.stat-change.negative {
    background: rgba(239, 68, 68, 0.2);
    color: #F87171;
}

/* Grid para métricas */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

/* Tabs personalizados */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.8rem 1.5rem;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    color: #94A3B8;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-color: #60A5FA;
    color: white;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(96, 165, 250, 0.2);
    color: #60A5FA;
    border-color: #60A5FA;
}

/* Botones */
.stButton > button {
    background: linear-gradient(45deg, #60A5FA, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(96, 165, 250, 0.3) !important;
}

/* DataFrames */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

/* Scrollbar personalizado */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #60A5FA, #8B5CF6);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, #8B5CF6, #F472B6);
}

/* Notificaciones */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background: rgba(34, 197, 94, 0.9);
    color: white;
    border-radius: 8px;
    z-index: 1000;
    animation: slideIn 0.3s ease;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
    color: #64748B;
    font-size: 0.9rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Botón flotante */
.floating-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(45deg, #60A5FA, #8B5CF6);
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    box-shadow: 0 8px 25px rgba(96, 165, 250, 0.3);
    transition: all 0.3s ease;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
}

.floating-btn:hover {
    transform: scale(1.1) rotate(90deg);
    box-shadow: 0 12px 30px rgba(96, 165, 250, 0.4);
}

/* Estilos adicionales para las nuevas clases */
.filter-panel {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-title {
    color: white;
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.metric-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-title {
    color: #94A3B8;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

.metric-value {
    color: white;
    font-size: 2rem;
    font-weight: 800;
    margin: 0.5rem 0;
}

.metric-subtitle {
    color: #94A3B8;
    font-size: 0.85rem;
    margin-top: 0.5rem;
}

.card-blue {
    border-left: 4px solid #60A5FA;
}

.card-green {
    border-left: 4px solid #10B981;
}

.card-red {
    border-left: 4px solid #F87171;
}

.card-purple {
    border-left: 4px solid #8B5CF6;
}

.card-orange {
    border-left: 4px solid #F59E0B;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.chart-container {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.gallery-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
    cursor: pointer;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.gallery-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.card-image {
    width: 100%;
    height: 150px;
    background-size: cover;
    background-position: center;
}

.card-text {
    padding: 1rem;
    color: white;
    text-align: center;
    font-weight: 600;
}

.landing-container {
    padding: 2rem;
}

.nav-header {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 3rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
}

.nav-item {
    color: white;
    font-weight: 600;
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.nav-item:hover {
    background: rgba(255, 255, 255, 0.1);
}

.section-description {
    color: #94A3B8;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

.positive {
    color: #10B981;
}

.negative {
    color: #F87171;
}

.warning {
    color: #F59E0B;
}
</style>

<div class="main-bg"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNCIONES DE APOYO
# ==============================================================================

def create_card(icon, title, description, key_target):
    """Crea una tarjeta de módulo interactiva"""
    st.markdown(f"""
    <div class="module-card">
        <div class="card-icon">{icon}</div>
        <div class="card-title">{title}</div>
        <div class="card-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón invisible que cubre toda la tarjeta
    if st.button(f"Entrar {title}", key=f"btn_{key_target}", help=f"Acceder a {title}"):
        st.session_state.current_page = key_target
        st.rerun()

def show_sidebar():
    """Muestra la barra lateral de navegación"""
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-title">AERO ERP</div>
            <div class="sidebar-subtitle">v4.0 • Wilson Pérez</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏠 INICIO PRINCIPAL", use_container_width=True, type="primary"):
            st.session_state.current_page = "Inicio"
            st.rerun()
        
        st.divider()
        
        st.markdown("**📋 Módulos:**")
        
        # Menú de navegación rápida
        modules = [
            ("Dashboard KPIs", "Dashboard KPIs"),
            ("Reconciliación V8", "Reconciliación V8"),
            ("Email Wilo AI", "Email Wilo AI"),
            ("Dashboard Transferencias", "Dashboard Transferencias"),
            ("Trabajadores", "Trabajadores"),
            ("Generar Guías", "Generar Guías"),
            ("Inventario", "inventario"),
            ("Reportes", "reportes")
        ]
        
        for name, key in modules:
            if st.button(f"📌 {name}", key=f"sidebar_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()
        
        st.divider()
        
        if st.button("⚙️ Configuración", use_container_width=True):
            st.session_state.current_page = "configuracion"
            st.rerun()
        
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.current_page = "Inicio"
            st.rerun()

def normalizar_texto_wilo(texto):
    """Normaliza texto para comparación"""
    if pd.isna(texto) or texto == '':
        return ''
    
    texto = str(texto)
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except:
        pass
    
    texto = re.sub(r'[^A-Za-z0-9\s]', ' ', texto.upper())
    return re.sub(r'\s+', ' ', texto).strip()

def procesar_subtotal_wilo(valor):
    """Procesa valores monetarios"""
    if pd.isna(valor): 
        return 0.0
    
    try:
        if isinstance(valor, (int, float)): 
            return float(valor)
        
        valor_str = str(valor).strip()
        valor_str = re.sub(r'[^\d.,-]', '', valor_str)
        
        if ',' in valor_str and '.' in valor_str:
            if valor_str.rfind(',') > valor_str.rfind('.'): 
                valor_str = valor_str.replace('.', '').replace(',', '.')
            else: 
                valor_str = valor_str.replace(',', '')
        elif ',' in valor_str: 
            valor_str = valor_str.replace(',', '.')
        
        return float(valor_str) if valor_str else 0.0
    except: 
        return 0.0

def hash_password(pw: str) -> str:
    """Genera hash SHA256 de contraseña"""
    return hashlib.sha256(pw.encode()).hexdigest()

def validar_fecha(fecha: str) -> bool:
    """Valida formato de fecha"""
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError: 
        return False

def render_gallery_card(title, image_url, page_key):
    """Renderiza una tarjeta estilo galería"""
    card_id = title.replace(" ", "_").lower()
    
    html = f"""
    <div class="gallery-card">
        <div class="card-image" style="background-image: url('{image_url}')"></div>
        <div class="card-text">{title}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    
    # Botón invisible para capturar el clic
    if st.button(f"Go to {title}", key=f"btn_nav_{card_id}"):
        st.session_state.current_page = page_key
        st.rerun()

# ==============================================================================
# 3. MOTOR DE AUDITORÍA (LÓGICA DE NEGOCIO)
# ==============================================================================

class WiloEmailEngine:
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.mail = None

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
        if not header_part: 
            return ""
        
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
        
        # Filtro: Solo correos de los últimos 30 días
        date_filter = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        _, messages = self.mail.search(None, f'(SINCE "{date_filter}")')
        
        ids = messages[0].split()
        latest_ids = ids[-limit:] if len(ids) > limit else ids
        
        results = []
        for e_id in reversed(latest_ids):
            try:
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
                                    body_bytes = part.get_payload(decode=True)
                                    if body_bytes:
                                        body = body_bytes.decode(errors="ignore")
                                    break
                        else:
                            body_bytes = msg.get_payload(decode=True)
                            if body_bytes:
                                body = body_bytes.decode(errors="ignore")

                        # Inteligencia de Clasificación
                        analysis = self.classify_email(subject, body)
                        
                        # Intentar extraer ID de pedido
                        order_match = re.search(r'#(\d+)', subject)
                        order_id = order_match.group(1) if order_match else "N/A"

                        results.append({
                            "id": e_id.decode() if isinstance(e_id, bytes) else str(e_id),
                            "fecha": date_,
                            "remitente": sender,
                            "asunto": subject,
                            "cuerpo": body[:500] + "..." if len(body) > 500 else body,
                            "tipo": analysis["tipo"],
                            "urgencia": analysis["urgencia"],
                            "pedido": order_id
                        })
            except Exception as e:
                continue
        
        self.mail.logout()
        return results

# ==============================================================================
# 4. INTERFAZ DE AUDITORÍA DE CORREOS
# ==============================================================================

def mostrar_auditoria_correos():
    """Interfaz para la auditoría de correos con Wilo AI"""
    st.title("📧 Auditoría de Correos Wilo AI")
    st.markdown("---")

    # Sidebar para Credenciales
    st.sidebar.title("🔐 Acceso Seguro")
    mail_user = st.sidebar.text_input("Correo", value="wperez@fashionclub.com.ec")
    mail_pass = st.sidebar.text_input("Contraseña", value="2wperez*", type="password")
    imap_host = "mail.fashionclub.com.ec"
    
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
                
                if not df.empty:
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
                st.error(f"❌ Error durante la auditoría: {str(e)}")

# ==============================================================================
# 5. PANTALLA DE INICIO
# ==============================================================================

def mostrar_pantalla_inicio():
    """Muestra la pantalla de inicio con todos los módulos"""
    st.markdown('<div class="landing-container">', unsafe_allow_html=True)
    
    # Header de Navegación
    st.markdown("""
    <div class="nav-header">
        <span class="nav-item">Gallery</span>
        <span class="nav-item">Logistics</span>
        <span class="nav-item">Distribution</span>
        <span class="nav-item">Contacts</span>
    </div>
    <div style='text-align:center; color:white; margin-bottom:50px;'>
        <h1 style='font-weight:800; letter-spacing:10px; font-size:3.5rem;'>AEROPOSTALE</h1>
        <p style='letter-spacing:5px; opacity:0.7;'>CENTRO DE DISTRIBUCIÓN ECUADOR | ERP SYSTEM</p>
    </div>
    """, unsafe_allow_html=True)

    # Grid de Módulos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_gallery_card("Dashboard KPIs", "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=500", "Dashboard KPIs")
    with col2:
        render_gallery_card("Reconciliación", "https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=500", "Reconciliación V8")
    with col3:
        render_gallery_card("Auditoría Email", "https://images.unsplash.com/photo-1557200134-90327ee9fafa?q=80&w=500", "Email Wilo AI")

    st.markdown("<br>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    with col4:
        render_gallery_card("Transferencias", "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=500", "Dashboard Transferencias")
    with col5:
        render_gallery_card("Personal CD", "https://images.unsplash.com/photo-1521737711867-e3b97375f902?q=80&w=500", "Trabajadores")
    with col6:
        render_gallery_card("Guías QR", "https://images.unsplash.com/photo-1566576721346-d4a3b4eaad5b?q=80&w=500", "Generar Guías")

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. MÓDULO RECONCILIACIÓN V8
# ==============================================================================

def identificar_tipo_tienda_v8(nombre):
    """Lógica V8.0 para clasificación de tiendas."""
    if pd.isna(nombre) or nombre == '': 
        return "DESCONOCIDO"
    
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
        
    return "TIENDA FÍSICA"  # Default

def mostrar_reconciliacion_v8():
    """Muestra el módulo de reconciliación V8.0"""
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
                
                df_f = pd.DataFrame({
                    'GUIA_FACTURA': [f'GUA-{i:04d}' for i in range(1001, 1001 + int(num_rows * 0.8))],
                    'VALOR_COBRADO': np.random.uniform(45, 550, int(num_rows * 0.8)).round(2)
                })
                
                st.success("✅ Usando datos de demostración.")
            else:
                # Lectura de archivos subidos
                if f_manifiesto.name.endswith(('xlsx', 'xls')):
                    df_m = pd.read_excel(f_manifiesto)
                else:
                    df_m = pd.read_csv(f_manifiesto)
                    
                if f_facturas.name.endswith(('xlsx', 'xls')):
                    df_f = pd.read_excel(f_facturas)
                else:
                    df_f = pd.read_csv(f_facturas)

            # Configuración de columnas
            st.markdown("""
            <div class='filter-panel'>
                <h3 class='filter-title'>⚙️ Configuración de Columnas</h3>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("**Configuración Manifiesto**")
                cols_m = df_m.columns.tolist()
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
                        nom = normalizar_texto_wilo(str(row['DESTINATARIO_NORM']))
                        if tipo == "VENTAS AL POR MAYOR": 
                            return "VENTAS AL POR MAYOR - JOFRE SANTANA"
                        if tipo == "VENTA WEB": 
                            return f"WEB - {nom}"
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
                    
                    # KPIs
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
                        porcentaje = (con_factura/len(df_final)*100) if len(df_final) > 0 else 0
                        st.markdown(f"""
                        <div class='stat-card card-purple'>
                            <div class='stat-icon'>✅</div>
                            <div class='stat-title'>Guías Conciliadas</div>
                            <div class='stat-value'>{con_factura}</div>
                            <div class='stat-change positive'>+{porcentaje:.1f}%</div>
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
                    
                    # Tabs para diferentes vistas
                    tab1, tab2, tab3 = st.tabs(["📈 Resumen por Canal", "📋 Detalle por Grupo", "🔍 Datos Completos"])
                    
                    with tab1:
                        resumen = df_final.groupby('TIPO_TIENDA').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).reset_index()
                        resumen.columns = ['Canal', 'Guías', 'Piezas', 'Valor Facturado']
                        resumen['% Gasto'] = (resumen['Valor Facturado'] / total_facturado * 100).round(2) if total_facturado > 0 else 0
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
                            fig = px.pie(resumen, values='Valor Facturado', names='Canal', 
                                       title="Distribución por Canal", 
                                       color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_chart2:
                            fig2 = px.bar(resumen, x='Canal', y='Guías', color='Canal',
                                        title="Guías por Canal", text='Guías',
                                        color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig2, use_container_width=True)

                    with tab2:
                        detalle = df_final.groupby('GRUPO').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).sort_values('VALOR_REAL', ascending=False)
                        detalle.columns = ['Guías', 'Piezas', 'Valor Total']
                        
                        detalle['Valor Promedio'] = (detalle['Valor Total'] / detalle['Guías']).round(2)
                        detalle['% del Total'] = (detalle['Valor Total'] / total_facturado * 100).round(2) if total_facturado > 0 else 0
                        
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
# 7. MÓDULO DASHBOARD DE TRANSFERENCIAS
# ==============================================================================

def extraer_entero(valor):
    """Extrae valor entero de diferentes formatos"""
    try:
        if pd.isna(valor): 
            return 0
        if isinstance(valor, str):
            valor = valor.replace('.', '')
            if ',' in valor: 
                valor = valor.split(',')[0]
        val = float(valor)
        if val >= 1000000: 
            return int(val // 1000000)
        return int(val)
    except:
        return 0

def clasificar_transferencia(row):
    """Clasifica transferencias por categoría"""
    sucursal = str(row.get('Sucursal Destino', row.get('Bodega Destino', ''))).upper()
    cantidad = row.get('Cantidad_Entera', 0)
    
    # Definir palabras clave
    PRICE_KEYWORDS = ['PRICE', 'OIL']
    WEB_KEYWORDS = ['WEB', 'TIENDA MOVIL', 'MOVIL']
    FALLAS_KEYWORDS = ['FALLAS']
    VENTAS_MAYOR_KEYWORDS = ['MAYOR', 'MAYORISTA']
    TIENDAS_REGULARES_LISTA = ['AERO CCI', 'AERO DAULE', 'AERO LAGO AGRIO', 'AERO MALL DEL RIO GYE']
    
    if cantidad >= 500 and cantidad % 100 == 0:
        return 'Fundas'
    if any(kw in sucursal for kw in PRICE_KEYWORDS): 
        return 'Price Club'
    if any(kw in sucursal for kw in WEB_KEYWORDS): 
        return 'Tienda Web'
    if any(kw in sucursal for kw in FALLAS_KEYWORDS): 
        return 'Fallas'
    if any(kw in sucursal for kw in VENTAS_MAYOR_KEYWORDS): 
        return 'Ventas por Mayor'
    if any(tienda.upper() in sucursal for tienda in TIENDAS_REGULARES_LISTA): 
        return 'Tiendas'
    
    tiendas_kw = ['AERO', 'MALL', 'CENTRO', 'SHOPPING', 'PLAZA', 'RIOCENTRO']
    if any(kw in sucursal for kw in tiendas_kw): 
        return 'Tiendas'
    
    return 'Ventas por Mayor'

def procesar_transferencias_diarias(df):
    """Procesa datos de transferencias diarias"""
    if df.empty:
        return None
    
    df = df.dropna(subset=['Secuencial'])
    df['Secuencial'] = df['Secuencial'].astype(str).str.strip()
    df = df[df['Secuencial'] != '']
    df['Cantidad_Entera'] = df['Cantidad Prendas'].apply(extraer_entero)
    df['Categoria'] = df.apply(clasificar_transferencia, axis=1)
    
    res = {
        'fecha': datetime.now(),
        'transferencias': int(df['Secuencial'].nunique()),
        'total_unidades': int(df['Cantidad_Entera'].sum()),
        'por_categoria': {},
        'detalle_categoria': {},
        'conteo_sucursales': {},
        'df_procesado': df
    }
    
    categorias = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas', 'Fundas']
    for cat in categorias:
        df_cat = df[df['Categoria'] == cat]
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

def mostrar_dashboard_transferencias():
    """Muestra el dashboard de transferencias"""
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Diarias</h1>
        <div class='header-subtitle'>Análisis de distribución por categorías y sucursales</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Transferencias Diarias", "📦 Mercadería en Tránsito", "📈 Análisis de Stock"])
    
    with tab1:
        with st.sidebar:
            st.markdown("""
            <div class='filter-panel'>
                <h4>📂 Carga de Datos</h4>
            """, unsafe_allow_html=True)
            file_diario = st.file_uploader("Subir archivo diario (xlsx)", type=['xlsx'], key="diario_up")
            if st.button("🔄 Limpiar y Recargar", use_container_width=True):
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        if file_diario:
            try:
                df_diario = pd.read_excel(file_diario)
                res = procesar_transferencias_diarias(df_diario)
                
                if res:
                    # Mostrar KPIs
                    st.header("📈 KPIs por Categoría")
                    
                    categorias_display = {
                        'Price Club': 'PRICE CLUB',
                        'Tiendas': 'TIENDAS REGULARES',
                        'Ventas por Mayor': 'VENTAS POR MAYOR',
                        'Tienda Web': 'TIENDA WEB',
                        'Fallas': 'FALLAS',
                        'Fundas': 'FUNDAS'
                    }
                    
                    cols = st.columns(3)
                    for i, (cat, cat_display) in enumerate(categorias_display.items()):
                        cantidad = res['por_categoria'].get(cat, 0)
                        
                        with cols[i % 3]:
                            if cat == 'Fundas':
                                st.markdown(f"""
                                <div class='stat-card card-purple'>
                                    <div class='stat-title'>{cat_display}</div>
                                    <div class='stat-value'>{cantidad:,}</div>
                                    <div class='metric-subtitle'>Múltiplos de 100 ≥ 500 unidades</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class='stat-card {'card-blue' if i % 3 == 0 else 'card-green' if i % 3 == 1 else 'card-orange'}'>
                                    <div class='stat-title'>{cat_display}</div>
                                    <div class='stat-value'>{cantidad:,}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if i == 2:
                            cols = st.columns(3)
                    
                    # Gráficos
                    st.header("📊 Análisis Visual")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        categorias_pie = list(res['por_categoria'].keys())
                        valores_pie = list(res['por_categoria'].values())
                        
                        df_pie = pd.DataFrame({
                            'Categoría': categorias_pie,
                            'Unidades': valores_pie
                        })
                        df_pie = df_pie[df_pie['Unidades'] > 0]
                        
                        if not df_pie.empty:
                            fig_pie = px.pie(
                                df_pie,
                                values='Unidades',
                                names='Categoría',
                                title="Distribución por Categoría",
                                color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6', '#F59E0B', '#3B82F6'],
                                hole=0.3
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.info("No hay datos para mostrar el gráfico")
                    
                    with col2:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{res['total_unidades']:,}</div>
                            <div class='metric-subtitle'>Total de unidades</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        promedio = res['total_unidades'] / res['transferencias'] if res['transferencias'] > 0 else 0
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{promedio:,.0f}</div>
                            <div class='metric-subtitle'>Promedio por transferencia</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Detalle
                    st.header("📄 Detalle por Secuencial")
                    df_detalle = res['df_procesado'][['Sucursal Destino', 'Secuencial', 'Cantidad_Entera', 'Categoria']].copy()
                    
                    st.dataframe(
                        df_detalle.rename(columns={
                            'Sucursal Destino': 'Sucursal',
                            'Cantidad_Entera': 'Cantidad',
                            'Categoria': 'Categoría'
                        }),
                        use_container_width=True,
                        height=400
                    )
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")
        else:
            st.info("👈 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")
    
    with tab2:
        st.header("📦 Análisis de Mercadería en Tránsito")
        st.info("Este módulo requiere el 'Archivo Base' y el 'Archivo de Comparación'")
        
        col_a, col_b = st.columns(2)
        with col_a:
            f_base = st.file_uploader("1. Cargar Stock Inicial (Base)", type=['xlsx', 'csv'], key="base_tr")
        with col_b:
            f_comp = st.file_uploader("2. Cargar Tránsito (Comparación)", type=['xlsx', 'csv'], key="comp_tr")
        
        if f_base and f_comp:
            st.success("Archivos cargados correctamente")
        else:
            st.info("👈 Por favor, carga ambos archivos para realizar el análisis.")
    
    with tab3:
        st.header("📈 Análisis de Stock y Ventas")
        st.info("Funcionalidad en desarrollo")

# ==============================================================================
# 8. MÓDULO GENERACIÓN DE GUÍAS
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
    
    # Crear estilos personalizados
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
    
    # Contenido del documento
    contenido = []
    
    # Cabecera
    titulo_text = f"""
    <b>CENTRO DE DISTRIBUCIÓN {guia_data['marca'].upper()}</b><br/>
    <font size=10>GUÍA DE ENVÍO</font>
    """
    contenido.append(Paragraph(titulo_text, styles['Titulo']))
    contenido.append(Spacer(1, 0.2*inch))
    
    # Información de la guía
    info_text = f"""
    <b>NÚMERO DE GUÍA:</b> {guia_data['numero']}<br/>
    <b>FECHA DE EMISIÓN:</b> {guia_data['fecha_emision']}<br/>
    <b>ESTADO:</b> {guia_data['estado']}
    """
    contenido.append(Paragraph(info_text, styles['Contenido']))
    contenido.append(Spacer(1, 0.2*inch))
    
    # Información de envío
    contenido.append(Paragraph("INFORMACIÓN DE ENVÍO", styles['EncabezadoSeccion']))
    
    envio_text = f"""
    <b>REMITENTE:</b><br/>
    Nombre: {guia_data['remitente']}<br/>
    Dirección: {guia_data['direccion_remitente']}<br/><br/>
    
    <b>DESTINATARIO:</b><br/>
    Nombre: {guia_data['destinatario']}<br/>
    Teléfono: {guia_data['telefono_destinatario']}<br/>
    Dirección: {guia_data['direccion_destinatario']}<br/>
    Tienda: {guia_data['tienda_destino']}
    """
    contenido.append(Paragraph(envio_text, styles['Contenido']))
    
    # Construir el PDF
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()

def mostrar_vista_previa_guia(guia_data):
    """Muestra una vista previa de la guía"""
    st.markdown("""
    <div class='filter-panel'>
        <h4>👁️ Vista Previa de la Guía</h4>
    """, unsafe_allow_html=True)
    
    col_logo, col_info = st.columns([1, 3])
    
    with col_logo:
        st.markdown(f"**{guia_data['marca']}**")
    
    with col_info:
        st.markdown("**📋 Información de la Guía**")
        st.write(f"**Número:** {guia_data['numero']}")
        st.write(f"**Estado:** {guia_data['estado']}")
        st.write(f"**Fecha:** {guia_data['fecha_emision']}")
    
    st.divider()
    
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
    
    st.markdown("</div>", unsafe_allow_html=True)

def mostrar_generacion_guias():
    """Muestra el módulo de generación de guías"""
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>🚚 Centro de Distribución Fashion Club</h1>
        <div class='header-subtitle'>Generador de Guías de Envío con QR y Tracking</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar estado de sesión
    if 'guias_registradas' not in st.session_state:
        st.session_state.guias_registradas = []
        st.session_state.contador_guias = 1000
        st.session_state.qr_images = {}
        st.session_state.logos = {}
    
    tiendas = [
        "Aero Matriz", "Aero Zona Franca", "Aero Servicios Y Otros", "Price Club", 
        "Aero La Plaza", "Aero Milagro", "Aero Condado Shopping", "Aero Mall Del Sol"
    ]
    
    remitentes = [
        {"nombre": "Josué Imbacuán", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Luis Perugachi", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Wilson Pérez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"}
    ]
    
    with st.form("guias_form", border=False):
        st.markdown("""
        <div class='filter-panel'>
            <h3 class='filter-title'>📋 Información de la Guía</h3>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Información de la Empresa")
            marca = st.radio("**Seleccione la Marca:**", ["Fashion Club", "Tempo"], horizontal=True)
            
            if marca == "Tempo":
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;'>
                    <div style='font-size: 3rem;'>🚚</div>
                    <div style='font-weight: bold; font-size: 1.2rem; color: #0033A0;'>{marca}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;'>
                    <div style='font-size: 3rem;'>👔</div>
                    <div style='font-weight: bold; font-size: 1.2rem; color: #0033A0;'>{marca}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("👤 Información del Remitente")
            remitente_nombre = st.selectbox("**Seleccione Remitente:**", [r["nombre"] for r in remitentes])
            remitente_direccion = next((r["direccion"] for r in remitentes if r["nombre"] == remitente_nombre), "")
            st.info(f"**Dirección:** {remitente_direccion}")
        
        st.divider()
        
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
        
        st.subheader("🔗 Información Digital")
        url_pedido = st.text_input("**URL del Pedido/Tracking:**", 
                                 placeholder="https://pedidos.fashionclub.com/orden-12345",
                                 value="https://pedidos.fashionclub.com/")
        
        # Generar código QR
        if url_pedido and url_pedido.startswith(('http://', 'https://')):
            try:
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(url_pedido)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                
                img_byte_arr = io.BytesIO()
                img_qr.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                st.session_state.qr_images[url_pedido] = img_byte_arr.getvalue()
                
                col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                with col_qr2:
                    st.image(img_byte_arr, caption="Código QR Generado", width=150)
            except:
                st.warning("⚠️ No se pudo generar el código QR.")
        
        st.divider()
        
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
        errors = []
        if not nombre_destinatario:
            errors.append("❌ El nombre del destinatario es obligatorio")
        if not direccion_destinatario:
            errors.append("❌ La dirección del destinatario es obligatoria")
        if not url_pedido or len(url_pedido) < 10:
            errors.append("❌ Ingrese una URL válida para el pedido")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Generar número de guía único
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1
            
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
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if preview:
                mostrar_vista_previa_guia(guia_data)
            
            if submit:
                with st.spinner(f"Generando guía {guia_num}..."):
                    time.sleep(1)
                    
                    # Agregar a lista de guías
                    st.session_state.guias_registradas.append(guia_data)
                    
                    # Generar PDF
                    pdf_bytes = generar_pdf_profesional(guia_data)
                    
                    st.success(f"✅ Guía {guia_num} generada exitosamente!")
                    
                    # Mostrar resumen
                    col_r1, col_r2 = st.columns(2)
                    
                    with col_r1:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=pdf_bytes,
                            file_name=f"guia_{guia_data['numero']}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    with col_r2:
                        json_data = json.dumps(guia_data, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📋 Descargar JSON",
                            data=json_data,
                            file_name=f"guia_{guia_data['numero']}.json",
                            mime="application/json",
                            use_container_width=True
                        )

# ==============================================================================
# 9. MÓDULO DASHBOARD DE KPIs
# ==============================================================================

def mostrar_dashboard_kpis():
    """Muestra el dashboard de KPIs"""
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
    
    # Datos de ejemplo
    dates = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    df_kpis = pd.DataFrame({
        'fecha': dates,
        'produccion': np.random.randint(1000, 5000, len(dates)),
        'eficiencia': np.random.uniform(80, 99, len(dates)).round(1),
        'costos': np.random.randint(5000, 20000, len(dates)),
        'alertas': np.random.randint(0, 10, len(dates))
    })
    
    # KPIs Principales
    st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    
    with col_k1:
        prod_prom = df_kpis['produccion'].mean()
        prod_tend = 5.2  # Ejemplo
        st.markdown(f"""
        <div class='stat-card card-blue'>
            <div class='stat-icon'>🏭</div>
            <div class='stat-title'>Producción Promedio</div>
            <div class='stat-value'>{prod_prom:,.0f}</div>
            <div class='stat-change {'positive' if prod_tend > 0 else 'negative'}">{'📈' if prod_tend > 0 else '📉'} {prod_tend:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k2:
        efic_prom = df_kpis['eficiencia'].mean()
        st.markdown(f"""
        <div class='stat-card card-green'>
            <div class='stat-icon'>⚡</div>
            <div class='stat-title'>Eficiencia</div>
            <div class='stat-value'>{efic_prom:.1f}%</div>
            <div class='stat-change {'positive' if efic_prom > 90 else 'warning'}">{'Excelente' if efic_prom > 90 else 'Mejorable'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k3:
        alert_total = df_kpis['alertas'].sum()
        st.markdown(f"""
        <div class='stat-card card-red'>
            <div class='stat-icon'>🚨</div>
            <div class='stat-title'>Alertas Totales</div>
            <div class='stat-value'>{alert_total}</div>
            <div class='stat-change {'negative' if alert_total > 10 else 'positive'}">{'Revisar' if alert_total > 10 else 'Controlado'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k4:
        costo_prom = df_kpis['costos'].mean()
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
    fig = px.line(df_kpis, x='fecha', y='produccion', 
                title='Producción Diaria',
                labels={'produccion': 'Unidades', 'fecha': 'Fecha'},
                line_shape='spline')
    fig.update_traces(line=dict(color='#0033A0', width=3))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 10. MÓDULO GESTIÓN DE TRABAJADORES
# ==============================================================================

def mostrar_gestion_trabajadores():
    """Muestra el módulo de gestión de trabajadores"""
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
            {"id": 2, "nombre": "Andrés Cadena", "cargo": "Jefe de Inventarios", "subarea": "Control de Inventarios", "estado": "Activo", "es_base": True}
        ],
        "Gestión de Transferencias": [
            {"id": 3, "nombre": "César Yépez", "cargo": "Responsable", "subarea": "Transferencias Fashion", "estado": "Activo", "es_base": True},
            {"id": 4, "nombre": "Luis Perugachi", "cargo": "Encargado", "subarea": "Pivote de transferencias", "estado": "Activo", "es_base": True}
        ]
    }
    
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
                cols = st.columns(2)
                for idx, trab in enumerate(personal):
                    col_idx = idx % 2
                    with cols[col_idx]:
                        st.markdown(f"""
                        <div style='background: white; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #0033A0;'>
                            <div style='font-weight: bold; font-size: 16px; color: #1e3a8a; margin-bottom: 5px;'>{trab['nombre']}</div>
                            <div style='font-size: 14px; color: #374151; margin-bottom: 3px;'>{trab['cargo']}</div>
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
        </div>
        """, unsafe_allow_html=True)
        
        # Simular trabajadores en base de datos
        trabajadores_db = []
        for area, personal in estructura_base.items():
            for trab in personal:
                trab['area'] = area
                trabajadores_db.append(trab)
        
        # Formulario para agregar trabajador
        with st.form("nuevo_trabajador"):
            st.subheader("➕ Agregar Nuevo Trabajador")
            
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                nombre = st.text_input("Nombre Completo")
                cargo = st.text_input("Cargo")
            with col_n2:
                area = st.selectbox("Área", list(estructura_base.keys()))
                estado = st.selectbox("Estado", ["Activo", "Inactivo"])
            
            subarea = st.text_input("Subárea/Especialidad (Opcional)")
            
            if st.form_submit_button("Agregar Trabajador"):
                if nombre and cargo:
                    nuevo_id = max([t['id'] for t in trabajadores_db]) + 1 if trabajadores_db else 1
                    nuevo_trab = {
                        'id': nuevo_id,
                        'nombre': nombre,
                        'cargo': cargo,
                        'area': area,
                        'subarea': subarea,
                        'estado': estado,
                        'es_base': False
                    }
                    
                    local_db.insert('trabajadores', nuevo_trab)
                    st.success(f"✅ {nombre} agregado a {area}")
                else:
                    st.error("❌ Nombre y Cargo son obligatorios")
    
    with tab3:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📊 Estadísticas del Personal</h4>
        </div>
        """, unsafe_allow_html=True)
        
        trabajadores_db = local_db.query('trabajadores')
        
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
                st.metric("🟢 Activos", activos)
            with col_m3:
                if 'es_base' in df_todos.columns:
                    base = len(df_todos[df_todos['es_base'] == True])
                else:
                    base = 0
                st.metric("🏛️ Personal Base", base)
            with col_m4:
                st.metric("➕ Adicionales", total - base)
            
            # Gráfico de distribución por área
            if 'area' in df_todos.columns:
                dist_area = df_todos['area'].value_counts()
                fig = px.bar(
                    x=dist_area.index, 
                    y=dist_area.values,
                    title="Distribución por Área",
                    labels={'x': 'Área', 'y': 'Cantidad'},
                    color=dist_area.values,
                    color_continuous_scale='blues'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("""
        <div class='filter-panel'>
            <h4>⚙️ Configuración del Sistema</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Exportar Datos")
            
            trabajadores_db = local_db.query('trabajadores')
            if trabajadores_db:
                df_export = pd.DataFrame(trabajadores_db)
                csv = df_export.to_csv(index=False)
                
                st.download_button(
                    label="📥 Descargar como CSV",
                    data=csv,
                    file_name="personal_cd.csv",
                    mime="text/csv"
                )
            else:
                st.info("No hay datos para exportar")
        
        with col_c2:
            st.subheader("Restaurar Estructura Base")
            st.warning("⚠️ Esta acción restaurará la estructura original")
            
            if st.button("🔄 Restaurar Estructura Base"):
                st.info("Funcionalidad en desarrollo")

# ==============================================================================
# 11. SISTEMA DE AUTENTICACIÓN
# ==============================================================================

def mostrar_pagina_login(rol_target):
    """Página de login"""
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
# 12. FUNCIÓN PRINCIPAL
# ==============================================================================

def main():
    """Función principal de la aplicación"""
    # Inicialización de estado
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Inicio"
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'login_target' not in st.session_state:
        st.session_state.login_target = "user"
    
    # Sidebar (solo visible si no es la página de inicio)
    if st.session_state.current_page != "Inicio":
        with st.sidebar:
            st.markdown("<h2 style='text-align:center; color:#0033A0;'>AERO ERP</h2>", unsafe_allow_html=True)
            
            if st.button("🏠 Volver al Inicio Principal", use_container_width=True):
                st.session_state.current_page = "Inicio"
                st.rerun()
            
            st.divider()
            
            # Menú de navegación
            modules = [
                ("Dashboard KPIs", "Dashboard KPIs"),
                ("Reconciliación V8", "Reconciliación V8"),
                ("Email Wilo AI", "Email Wilo AI"),
                ("Dashboard Transferencias", "Dashboard Transferencias"),
                ("Trabajadores", "Trabajadores"),
                ("Generar Guías", "Generar Guías")
            ]
            
            for name, key in modules:
                if st.button(f"📌 {name}", key=f"sidebar_{key}", use_container_width=True):
                    st.session_state.current_page = key
                    st.rerun()
            
            st.divider()
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.user_type = None
                st.session_state.current_page = "Inicio"
                st.rerun()

    # Routing
    if st.session_state.show_login:
        mostrar_pagina_login(st.session_state.login_target)
    elif st.session_state.current_page == "Inicio":
        mostrar_pantalla_inicio()
    else:
        # Validación de Roles
        page_roles = {
            "Dashboard KPIs": "public",
            "Reconciliación V8": "admin", 
            "Email Wilo AI": "admin",
            "Dashboard Transferencias": "admin",
            "Generar Guías": "user",
            "Trabajadores": "admin"
        }
        
        req_role = page_roles.get(st.session_state.current_page, "admin")
        
        if (req_role == "public" or 
            st.session_state.user_type == "admin" or 
            (st.session_state.user_type == "user" and req_role == "user")):
            
            # Mapeo de páginas a funciones
            page_functions = {
                "Dashboard KPIs": mostrar_dashboard_kpis,
                "Reconciliación V8": mostrar_reconciliacion_v8,
                "Email Wilo AI": mostrar_auditoria_correos,
                "Dashboard Transferencias": mostrar_dashboard_transferencias,
                "Generar Guías": mostrar_generacion_guias,
                "Trabajadores": mostrar_gestion_trabajadores
            }
            
            if st.session_state.current_page in page_functions:
                page_functions[st.session_state.current_page]()
            else:
                st.error("Página no encontrada")
                if st.button("Volver al Inicio"):
                    st.session_state.current_page = "Inicio"
                    st.rerun()
        else:
            st.session_state.login_target = req_role
            st.session_state.show_login = True
            st.rerun()

    # Footer
    st.markdown("<div class='app-footer'>AEROPOSTALE EC-ERP v3.5 | Wilson Pérez Logistics Design</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
