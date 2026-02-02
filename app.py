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
import requests
import smtplib
import imaplib
import email
import unicodedata
import warnings
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

# --- LIBRERÍAS DE TERCEROS ---
import qrcode
from PIL import Image as PILImage
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import xlsxwriter

# --- CONFIGURACIÓN INICIAL DE PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="ERP Aeropostale | Sistema Integral",
    page_icon="✈️",
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
# 0. FUNCIONES AUXILIARES GLOBALES (MOVIDAS AL INICIO PARA EVITAR REFERENCIAS ANTICIPADAS)
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
# 1. SIMULACIÓN DE BASE DE DATOS LOCAL (REEMPLAZO DE SUPABASE)
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
# 2. ESTILOS CSS MODERNO - INTERFAZ ERP AEROPOSTALE
# ==============================================================================
st.markdown("""
<style>
/* ============================================
   VARIABLES Y CONFIGURACIÓN GLOBAL
   ============================================ */
:root {
    /* Colores corporativos Aeropostale */
    --aeropostale-blue: #0033A0;
    --aeropostale-red: #E4002B;
    --aeropostale-white: #FFFFFF;
    --aeropostale-gray: #F5F7FA;
    --aeropostale-dark: #1A1F36;
    
    /* Colores de acento */
    --success: #00C853;
    --warning: #FFB300;
    --danger: #FF3D00;
    --info: #2979FF;
    --purple: #7B1FA2;
    
    /* Espaciado */
    --border-radius: 12px;
    --shadow: 0 8px 30px rgba(0, 51, 160, 0.08);
    --shadow-hover: 0 15px 40px rgba(0, 51, 160, 0.15);
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ============================================
   ESTRUCTURA PRINCIPAL
   ============================================ */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
    font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
}

/* Ocultar elementos por defecto de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* ============================================
   SIDEBAR MODERNO
   ============================================ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--aeropostale-dark) 0%, #2D3748 100%);
    border-right: none;
    padding-top: 20px;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 2rem;
}

/* Logo y marca */
.sidebar-header {
    text-align: center;
    padding: 0 1.5rem 2rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 1.5rem;
}

.sidebar-logo {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(45deg, var(--aeropostale-white), #A0AEC0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.sidebar-subtitle {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.85rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Botones del sidebar */
[data-testid="stSidebar"] button {
    background: transparent !important;
    border: none !important;
    color: rgba(255, 255, 255, 0.7) !important;
    text-align: left;
    padding: 0.85rem 1.5rem !important;
    margin: 0.25rem 0.5rem !important;
    border-radius: var(--border-radius) !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    width: calc(100% - 1rem) !important;
    transition: var(--transition) !important;
    position: relative;
    overflow: hidden;
}

[data-testid="stSidebar"] button:hover {
    background: rgba(255, 255, 255, 0.1) !important;
    color: var(--aeropostale-white) !important;
    transform: translateX(5px);
}

[data-testid="stSidebar"] button:active {
    transform: translateX(5px) scale(0.98);
}

/* Botón activo */
[data-testid="stSidebar"] button.active {
    background: linear-gradient(45deg, var(--aeropostale-blue), var(--aeropostale-red)) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(0, 51, 160, 0.3);
}

/* Indicador de botón activo */
[data-testid="stSidebar"] button.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 60%;
    background: var(--aeropostale-white);
    border-radius: 0 4px 4px 0;
}

/* Iconos en botones */
[data-testid="stSidebar"] button::after {
    content: '→';
    position: absolute;
    right: 1.5rem;
    opacity: 0;
    transition: var(--transition);
}

[data-testid="stSidebar"] button:hover::after {
    opacity: 1;
    transform: translateX(3px);
}

/* ============================================
   HEADER DE MÓDULO (FONDO DINÁMICO)
   ============================================ */
.dashboard-header {
    background: linear-gradient(135deg, 
        rgba(0, 51, 160, 0.9) 0%, 
        rgba(228, 0, 43, 0.8) 100%);
    padding: 2.5rem 3rem !important;
    border-radius: var(--border-radius);
    margin-bottom: 2rem;
    color: white;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
    border-left: 6px solid var(--aeropostale-white);
}

.dashboard-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" preserveAspectRatio="none" opacity="0.1"><path d="M0,0 L100,0 L100,100 Z" fill="white"/></svg>');
    background-size: cover;
}

.header-title {
    font-size: 2.5rem;
    font-weight: 800;
    margin: 0;
    position: relative;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.header-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    margin-top: 0.5rem;
    font-weight: 300;
    position: relative;
}

/* Fondos específicos por módulo */
.header-dashboard { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.header-reconciliation { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
.header-email { background: linear-gradient(135deg, #f46b45 0%, #eea849 100%); }
.header-guias { background: linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%); }
.header-etiquetas { background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%); }
.header-trabajadores { background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%); }
.header-distribuciones { background: linear-gradient(135deg, #654ea3 0%, #eaafc8 100%); }
.header-ayuda { background: linear-gradient(135deg, #232526 0%, #414345 100%); }

/* ============================================
   TARJETAS KPI MODERNAS
   ============================================ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.kpi-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 1.75rem;
    box-shadow: var(--shadow);
    transition: var(--transition);
    border-top: 4px solid var(--aeropostale-blue);
    position: relative;
    overflow: hidden;
}

.kpi-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-hover);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--aeropostale-blue), var(--aeropostale-red));
}

.kpi-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    opacity: 0.8;
}

.kpi-title {
    font-size: 0.9rem;
    color: #6B7280;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

.kpi-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--aeropostale-dark);
    margin: 0.5rem 0;
}

.kpi-change {
    font-size: 0.9rem;
    font-weight: 500;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
    margin-top: 0.5rem;
}

.kpi-change.positive { background: rgba(0, 200, 83, 0.1); color: var(--success); }
.kpi-change.negative { background: rgba(255, 61, 0, 0.1); color: var(--danger); }

/* ============================================
   BOTONES INTERACTIVOS MODERNOS
   ============================================ */
.stButton > button {
    background: linear-gradient(45deg, var(--aeropostale-blue), #0066CC) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    border-radius: var(--border-radius) !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
    box-shadow: 0 4px 15px rgba(0, 51, 160, 0.2) !important;
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 51, 160, 0.3) !important;
}

.stButton > button:active {
    transform: translateY(0);
}

.stButton > button::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
}

.stButton > button:focus:not(:active)::after {
    animation: ripple 1s ease-out;
}

@keyframes ripple {
    0% { transform: scale(0, 0); opacity: 0.5; }
    100% { transform: scale(40, 40); opacity: 0; }
}

/* Botones secundarios */
.stButton > button.secondary {
    background: linear-gradient(45deg, #6B7280, #9CA3AF) !important;
}

.stButton > button.success {
    background: linear-gradient(45deg, var(--success), #00E676) !important;
}

.stButton > button.warning {
    background: linear-gradient(45deg, var(--warning), #FFCA28) !important;
}

.stButton > button.danger {
    background: linear-gradient(45deg, var(--danger), #FF5252) !important;
}

/* ============================================
   PANELES DE FILTRO Y CONTENEDORES
   ============================================ */
.filter-panel {
    background: white;
    padding: 2rem;
    border-radius: var(--border-radius);
    margin-bottom: 2rem;
    box-shadow: var(--shadow);
    border: 1px solid #E5E7EB;
}

.filter-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--aeropostale-dark);
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #F3F4F6;
}

/* ============================================
   TABLAS ESTILIZADAS
   ============================================ */
.stDataFrame {
    border-radius: var(--border-radius) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
}

/* ============================================
   FORMULARIOS MODERNOS
   ============================================ */
.stTextInput > div > div > input,
.stSelectbox > div > div > select,
.stDateInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: var(--border-radius) !important;
    border: 2px solid #E5E7EB !important;
    padding: 0.75rem 1rem !important;
    transition: var(--transition) !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > select:focus,
.stDateInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--aeropostale-blue) !important;
    box-shadow: 0 0 0 3px rgba(0, 51, 160, 0.1) !important;
}

/* ============================================
   PÁGINA DE LOGIN MODERNA
   ============================================ */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 80vh;
    padding: 2rem;
}

.login-card {
    background: white;
    border-radius: var(--border-radius);
    padding: 3rem;
    box-shadow: 0 20px 60px rgba(0, 51, 160, 0.15);
    width: 100%;
    max-width: 450px;
    border-top: 6px solid var(--aeropostale-blue);
}

.login-logo {
    text-align: center;
    margin-bottom: 2rem;
}

.login-logo h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(45deg, var(--aeropostale-blue), var(--aeropostale-red));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.login-logo p {
    color: #6B7280;
    font-size: 0.9rem;
}

.login-input {
    margin-bottom: 1.5rem;
}

.login-button {
    width: 100%;
    margin-top: 1rem;
}

/* ============================================
   ALERTAS Y NOTIFICACIONES
   ============================================ */
.stAlert {
    border-radius: var(--border-radius) !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

/* ============================================
   FOOTER MODERNO
   ============================================ */
.footer {
    text-align: center;
    padding: 2rem;
    margin-top: 4rem;
    color: #6B7280;
    border-top: 1px solid #E5E7EB;
    font-size: 0.85rem;
    background: white;
    border-radius: var(--border-radius) var(--border-radius) 0 0;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
}

.footer-logo {
    color: var(--aeropostale-blue);
    font-weight: 700;
    font-size: 1.1rem;
}

/* ============================================
   EFECTOS DE CARGA Y ANIMACIONES
   ============================================ */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.dashboard-content {
    animation: fadeIn 0.5s ease-out;
}

/* ============================================
   RESPONSIVE DESIGN
   ============================================ */
@media (max-width: 768px) {
    .header-title { font-size: 2rem; }
    .kpi-grid { grid-template-columns: 1fr; }
    .dashboard-header { padding: 1.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. MÓDULO CORREO WILO (CORREGIDO Y ROBUSTO)
# ==============================================================================

class WiloEmailEngine:
    def __init__(self):
        self.imap_url = "mail.fashionclub.com.ec"
        self.email_user = ""
        self.email_pass = ""
        
        # Datos simulados para demo
        self.sample_emails = self._generate_sample_emails()

    def _generate_sample_emails(self):
        """Genera correos de ejemplo para demostración"""
        sample_data = []
        subjects = [
            "URGENTE: Faltante en envío #4567",
            "Confirmación de recepción pedido #1234",
            "Problema con etiquetas en lote #789",
            "Sobrante detectado en inventario",
            "Daño reportado en mercancía",
            "Consulta sobre guía de transporte"
        ]
        
        senders = [
            "almacen@tienda.com",
            "cliente@empresa.com",
            "transporte@logistica.com",
            "auditoria@aeropostale.com",
            "soporte@aeropostale.com"
        ]
        
        for i in range(6):
            subject = subjects[i % len(subjects)]
            sender = senders[i % len(senders)]
            date = (datetime.now() - timedelta(days=i, hours=np.random.randint(1, 12))).strftime("%a, %d %b %Y %H:%M:%S")
            
            # Determinar tipo basado en contenido
            if "Faltante" in subject:
                tipo = "📦 FALTANTE"
                urgencia = "ALTA"
            elif "Sobrante" in subject:
                tipo = "👔 SOBRANTE"
                urgencia = "MEDIA"
            elif "Daño" in subject:
                tipo = "⚠️ DAÑO"
                urgencia = "ALTA"
            elif "etiquetas" in subject.lower():
                tipo = "🏷️ ETIQUETA"
                urgencia = "MEDIA"
            elif "transporte" in subject.lower():
                tipo = "🚚 ENVÍO"
                urgencia = "BAJA"
            else:
                tipo = "ℹ️ GENERAL"
                urgencia = "BAJA"
            
            sample_data.append({
                "id": str(i + 1000),
                "fecha": date,
                "remitente": f"{sender}",
                "asunto": subject,
                "cuerpo": f"""Estimado equipo,

Se reporta un incidente con referencia al pedido #4567.

Detalles:
- Tipo de incidencia: {'Faltante' if 'Faltante' in subject else 'General'}
- Cantidad afectada: {np.random.randint(1, 10)} unidades
- Tienda destino: {'Mall del Sol' if i % 2 == 0 else 'San Marino'}
- Fecha de detección: {(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')}

Por favor, tomar las acciones correctivas necesarias.

Atentamente,
{sender.split('@')[0].title()}
                """,
                "tipo": tipo,
                "urgencia": urgencia
            })
        
        return sample_data

    def fetch_emails(self, limit=15):
        """Versión simulada para trabajar localmente"""
        return self.sample_emails[:limit]

def mostrar_modulo_email_wilo():
    st.markdown("""
    <div class='dashboard-header header-email'>
        <h1 class='header-title'>📧 Auditoría de Correos Wilo AI</h1>
        <div class='header-subtitle'>Análisis Inteligente de Novedades en Tiempo Real</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info("🔍 Este módulo analiza automáticamente correos para detectar novedades logísticas.")
    with col2:
        scan_btn = st.button("🔄 Escanear Ahora", use_container_width=True, type="primary")
    with col3:
        auto_scan = st.checkbox("Escaneo automático", value=False)

    if scan_btn or auto_scan:
        engine = WiloEmailEngine()
        with st.spinner("🔍 Conectando con servidor de correo y analizando..."):
            time.sleep(1.5)  # Simulación de procesamiento
            emails = engine.fetch_emails(10)
        
        if not emails:
            st.warning("⚠️ No se encontraron correos o hubo un error de conexión.")
        else:
            df = pd.DataFrame(emails)
            
            # KPIs Rápidos con diseño moderno
            st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = len(df)
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>📨</div>
                    <div class='kpi-title'>Correos Analizados</div>
                    <div class='kpi-value'>{total}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                alta = len(df[df['urgencia'] == 'ALTA'])
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>🚨</div>
                    <div class='kpi-title'>Alta Urgencia</div>
                    <div class='kpi-value'>{alta}</div>
                    <div class='kpi-change {'negative' if alta > 3 else 'positive'}">{'Requiere atención' if alta > 3 else 'Bajo control'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                faltantes = len(df[df['tipo'].str.contains('FALTANTE')])
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>📦</div>
                    <div class='kpi-title'>Faltantes</div>
                    <div class='kpi-value'>{faltantes}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                sobrantes = len(df[df['tipo'].str.contains('SOBRANTE')])
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>👔</div>
                    <div class='kpi-title'>Sobrantes</div>
                    <div class='kpi-value'>{sobrantes}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("### 📋 Bandeja de Entrada Analizada")
            st.dataframe(
                df[['fecha', 'remitente', 'asunto', 'tipo', 'urgencia']], 
                use_container_width=True,
                column_config={
                    "urgencia": st.column_config.TextColumn(
                        "Prioridad",
                        help="Nivel de urgencia detectado",
                        width="small"
                    ),
                    "tipo": st.column_config.TextColumn(
                        "Categoría",
                        width="medium"
                    )
                }
            )
            
            st.markdown("---")
            st.markdown("### 🔍 Inspector de Contenido Detallado")
            sel_id = st.selectbox("Seleccione un correo para ver detalles:", df['id'], format_func=lambda x: f"Correo #{x}")
            
            if sel_id:
                row = df[df['id'] == sel_id].iloc[0]
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f"""
                    <div class='filter-panel'>
                        <h4>📋 Información del Correo</h4>
                        <p><strong>De:</strong> {row['remitente']}</p>
                        <p><strong>Asunto:</strong> {row['asunto']}</p>
                        <p><strong>Fecha:</strong> {row['fecha']}</p>
                        <p><strong>Clasificación:</strong> <span style='color: {'#FF3D00' if row['urgencia'] == 'ALTA' else '#2979FF'}'>{row['tipo']}</span></p>
                        <p><strong>Urgencia:</strong> <span style='color: {'#FF3D00' if row['urgencia'] == 'ALTA' else '#FFB300' if row['urgencia'] == 'MEDIA' else '#00C853'}'>{row['urgencia']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.text_area("**Cuerpo del Correo:**", row['cuerpo'], height=200)
                
                # Análisis adicional
                st.markdown("#### 📊 Análisis Semántico")
                words = len(row['cuerpo'].split())
                sentences = len(re.split(r'[.!?]+', row['cuerpo']))
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Palabras", words)
                col_b.metric("Oraciones", sentences)
                col_c.metric("Detecciones", len(row['tipo'].split(', ')))

# ==============================================================================
# 4. MÓDULO RECONCILIACIÓN V8 (CORREGIDO Y ACTUALIZADO)
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
    <div class='dashboard-header header-reconciliation'>
        <h1 class='header-title'>📦 Reconciliación Logística V8.0</h1>
        <div class='header-subtitle'>Soporte avanzado para Piezas y Ventas Mayoristas (Jofre Santana)</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader("📂 Subir Manifiesto (Debe tener columna PIEZAS)", type=['xlsx', 'xls', 'csv'])
    with col2:
        f_facturas = st.file_uploader("📂 Subir Facturas (Debe tener VALORES)", type=['xlsx', 'xls', 'csv'])

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
                        nom = normalizar_texto_wilo(row['DESTINATARIO_NORM'])
                        if tipo == "VENTAS AL POR MAYOR": return "VENTAS AL POR MAYOR - JOFRE SANTANA"
                        if tipo == "VENTA WEB": return f"WEB - {nom}"
                        return f"TIENDA - {nom}"
                    
                    df_final['GRUPO'] = df_final.apply(crear_grupo, axis=1)

                    # --- RESULTADOS ---
                    st.markdown("""
                    <div class='dashboard-header'>
                        <h2>📊 Resultados del Análisis V8.0</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    total_facturado = df_final['VALOR_REAL'].sum()
                    total_piezas = df_final['PIEZAS_CALC'].sum()
                    con_factura = df_final[df_final['VALOR_REAL'] > 0].shape[0]
                    sin_factura = df_final[df_final['VALOR_REAL'] == 0].shape[0]
                    
                    # KPIs modernos
                    st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
                    k1, k2, k3, k4 = st.columns(4)
                    
                    with k1:
                        st.markdown(f"""
                        <div class='kpi-card'>
                            <div class='kpi-icon'>💰</div>
                            <div class='kpi-title'>Total Facturado</div>
                            <div class='kpi-value'>${total_facturado:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k2:
                        st.markdown(f"""
                        <div class='kpi-card'>
                            <div class='kpi-icon'>📦</div>
                            <div class='kpi-title'>Total Piezas</div>
                            <div class='kpi-value'>{total_piezas:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k3:
                        st.markdown(f"""
                        <div class='kpi-card'>
                            <div class='kpi-icon'>✅</div>
                            <div class='kpi-title'>Guías Conciliadas</div>
                            <div class='kpi-value'>{con_factura}</div>
                            <div class='kpi-change positive'>+{con_factura/len(df_final)*100:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k4:
                        st.markdown(f"""
                        <div class='kpi-card'>
                            <div class='kpi-icon'>⚠️</div>
                            <div class='kpi-title'>Guías Sin Factura</div>
                            <div class='kpi-value'>{sin_factura}</div>
                            <div class='kpi-change {'negative' if sin_factura > 5 else 'positive'}">{'Revisar' if sin_factura > 5 else 'OK'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Tablas
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
                            fig = px.pie(resumen, values='Valor Facturado', names='Canal', 
                                       title="Distribución por Canal", 
                                       color_discrete_sequence=px.colors.qualitative.Set3)
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with col_chart2:
                            fig2 = px.bar(resumen, x='Canal', y='Guías', color='Canal',
                                        title="Guías por Canal", text='Guías')
                            st.plotly_chart(fig2, use_container_width=True)

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
            st.exception(e)
    else:
        st.info("👆 Suba los archivos necesarios o active la opción de datos de demostración para comenzar.")

# ==============================================================================
# 5. MÓDULOS RESTANTES MEJORADOS
# ==============================================================================

# --- DASHBOARD KPIS ---
def mostrar_dashboard_kpis():
    st.markdown("""
    <div class='dashboard-header header-dashboard'>
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
            st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            
            with col_k1:
                prod_prom = df_filtered['produccion'].mean()
                prod_tend = ((df_filtered['produccion'].iloc[-1] - df_filtered['produccion'].iloc[0]) / df_filtered['produccion'].iloc[0] * 100) if len(df_filtered) > 1 else 0
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>🏭</div>
                    <div class='kpi-title'>Producción Promedio</div>
                    <div class='kpi-value'>{prod_prom:,.0f}</div>
                    <div class='kpi-change {'positive' if prod_tend > 0 else 'negative'}">{'📈' if prod_tend > 0 else '📉'} {prod_tend:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k2:
                efic_prom = df_filtered['eficiencia'].mean()
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>⚡</div>
                    <div class='kpi-title'>Eficiencia</div>
                    <div class='kpi-value'>{efic_prom:.1f}%</div>
                    <div class='kpi-change {'positive' if efic_prom > 90 else 'warning'}">{'Excelente' if efic_prom > 90 else 'Mejorable'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k3:
                alert_total = df_filtered['alertas'].sum()
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>🚨</div>
                    <div class='kpi-title'>Alertas Totales</div>
                    <div class='kpi-value'>{alert_total}</div>
                    <div class='kpi-change {'negative' if alert_total > 10 else 'positive'}">{'Revisar' if alert_total > 10 else 'Controlado'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_k4:
                costo_prom = df_filtered['costos'].mean()
                st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>💰</div>
                    <div class='kpi-title'>Costo Promedio</div>
                    <div class='kpi-value'>${costo_prom:,.0f}</div>
                    <div class='kpi-change'>Diario</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Gráficos
            tab1, tab2 = st.tabs(["📈 Tendencia Temporal", "📊 Distribución"])
            
            with tab1:
                fig = px.line(df_filtered, x='fecha', y='produccion', 
                            title='Producción Diaria',
                            labels={'produccion': 'Unidades', 'fecha': 'Fecha'})
                fig.update_traces(line=dict(color='#0033A0', width=3))
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                col_ch1, col_ch2 = st.columns(2)
                with col_ch1:
                    fig2 = px.pie(df_filtered.tail(10), values='produccion', names=df_filtered.tail(10)['fecha'].dt.strftime('%Y-%m-%d'),
                                title='Distribución Últimos 10 Días')
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col_ch2:
                    fig3 = px.bar(df_filtered.tail(7), x=df_filtered.tail(7)['fecha'].dt.strftime('%a'), y='eficiencia',
                                title='Eficiencia Semanal', color='eficiencia',
                                color_continuous_scale='Viridis')
                    st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("No hay datos para el rango de fechas seleccionado.")
    else:
        st.info("Cargando datos de KPIs...")

# --- GENERACIÓN DE GUÍAS ---
def mostrar_generacion_guias():
    st.markdown("""
    <div class='dashboard-header header-guias'>
        <h1 class='header-title'>📋 Generador de Guías de Envío</h1>
        <div class='header-subtitle'>Creación automatizada de documentación de transporte</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("guias_form", border=False):
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 class='filter-title'>📝 Información del Envío</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            marca = st.radio("🏷️ Marca", ["Fashion Club", "Tempo", "Aeropostale"], horizontal=True)
            tienda = st.selectbox("🏪 Tienda Destino", 
                                ["Mall del Sol", "San Marino", "Quicentro", "Mall del Río", 
                                 "Plaza de las Américas", "Riocentro Ceibos"])
            remitente = st.selectbox("👤 Remitente", ["Andrés Yépez", "Josué Imbacuán", "María González", "Carlos Pérez"])
        
        with col2:
            num_piezas = st.number_input("📦 Número de Piezas", min_value=1, max_value=100, value=1)
            peso = st.number_input("⚖️ Peso Aprox. (kg)", min_value=0.1, max_value=100.0, value=5.0)
            valor_declarado = st.number_input("💰 Valor Declarado", min_value=0.0, value=100.0)
        
        url_pedido = st.text_input("🔗 URL del Pedido", value="https://pedidos.aeropostale.com/", placeholder="Ingrese la URL completa del pedido")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("🚀 Generar Guía PDF", use_container_width=True, type="primary")
        with col_btn2:
            preview = st.form_submit_button("👁️ Vista Previa", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if submit or preview:
        if not url_pedido or len(url_pedido) < 10:
            st.error("❌ Por favor, ingrese una URL válida para el pedido.")
        else:
            # Simulación de generación
            guia_num = f"GUA-{datetime.now().strftime('%Y%m%d')}-{np.random.randint(1000, 9999)}"
            
            if submit:
                with st.spinner(f"Generando guía {guia_num}..."):
                    time.sleep(2)
                    
                    # Simular creación de PDF
                    st.success(f"✅ Guía generada exitosamente para {tienda}")
                    st.balloons()
                    
                    # Mostrar detalles
                    st.markdown("""
                    <div class='filter-panel'>
                        <h4>📄 Resumen de la Guía Generada</h4>
                    """, unsafe_allow_html=True)
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.markdown(f"""
                        - **Número de Guía:** `{guia_num}`
                        - **Marca:** {marca}
                        - **Tienda Destino:** {tienda}
                        - **Remitente:** {remitente}
                        """)
                    
                    with col_d2:
                        st.markdown(f"""
                        - **Piezas:** {num_piezas}
                        - **Peso:** {peso} kg
                        - **Valor Declarado:** ${valor_declarado:,.2f}
                        - **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
                        """)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Botón de descarga simulado - CORREGIDO
                    st.download_button(
                        label="📥 Descargar Guía PDF",
                        data=b"PDF simulated content",
                        file_name=f"guia_{guia_num}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            if preview:
                st.info(f"**Vista previa para:** {tienda} - Guía: {guia_num}")

# --- GENERACIÓN DE ETIQUETAS ---
def mostrar_generacion_etiquetas():
    st.markdown("""
    <div class='dashboard-header header-etiquetas'>
        <h1 class='header-title'>🏷️ Generador de Etiquetas Inteligente</h1>
        <div class='header-subtitle'>Creación de etiquetas para inventario y logística</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("etiqueta_form", border=False):
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h3 class='filter-title'>🛠️ Configuración de Etiquetas</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            referencia = st.text_input("🔤 Referencia/Modelo", placeholder="Ej: AP-JEANS-001")
            tipo_prenda = st.selectbox("👕 Tipo de Prenda", ["Jeans", "Camiseta", "Polo", "Chaqueta", "Vestido", "Accesorio"])
            temporada = st.selectbox("📅 Temporada", ["Verano 2024", "Invierno 2024", "Primavera 2024", "Otoño 2024"])
        
        with col2:
            cantidad = st.number_input("🔢 Cantidad de Etiquetas", min_value=1, max_value=1000, value=10)
            tamaño = st.selectbox("📏 Tamaño", ["Pequeño (5x3cm)", "Mediano (7x5cm)", "Grande (10x7cm)"])
            color_etiqueta = st.color_picker("🎨 Color de Fondo", "#0033A0")
        
        incluir_qr = st.checkbox("📱 Incluir Código QR", value=True)
        if incluir_qr:
            qr_data = st.text_area("📝 Datos para QR", value=f"https://aeropostale.com/ref/{referencia if referencia else 'MODELO'}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit = st.form_submit_button("🖨️ Generar Etiquetas", use_container_width=True, type="primary")
        with col_btn2:
            reset = st.form_submit_button("🔄 Limpiar", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if submit and referencia:
        with st.spinner(f"Generando {cantidad} etiquetas..."):
            time.sleep(1.5)
            
            st.success(f"✅ {cantidad} etiquetas generadas para '{referencia}'")
            
            # Mostrar preview
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown("""
                <div class='filter-panel' style='text-align: center;'>
                    <h4>📋 Vista Previa de Etiqueta</h4>
                    <div style='border: 2px dashed #0033A0; padding: 20px; margin: 15px 0; border-radius: 8px;'>
                        <h3 style='color: #0033A0;'>{}</h3>
                        <p><strong>Tipo:</strong> {}</p>
                        <p><strong>Temporada:</strong> {}</p>
                        <p><strong>Tamaño:</strong> {}</p>
                        {}
                    </div>
                </div>
                """.format(
                    referencia, 
                    tipo_prenda, 
                    temporada, 
                    tamaño,
                    "✅ Incluye QR" if incluir_qr else "❌ Sin QR"
                ), unsafe_allow_html=True)
            
            with col_p2:
                # Generar código QR simple
                if incluir_qr:
                    try:
                        qr = qrcode.QRCode(version=1, box_size=6, border=2)
                        qr.add_data(qr_data)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white")
                        
                        # Convertir a bytes
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='PNG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        st.image(img_byte_arr, caption="Código QR Generado", width=200)
                    except:
                        st.warning("No se pudo generar el código QR")
            
            # Opciones de exportación - TODOS CORREGIDOS
            st.markdown("### 💾 Opciones de Exportación")
            col_e1, col_e2, col_e3 = st.columns(3)
            
            with col_e1:
                st.download_button(
                    label="📄 Descargar PDF",
                    data=b"PDF content",
                    file_name=f"etiquetas_{referencia}_{datetime.now().date()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            with col_e2:
                st.download_button(
                    label="🖼️ Descargar PNG",
                    data=b"PNG content",
                    file_name=f"etiquetas_{referencia}_{datetime.now().date()}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            with col_e3:
                st.download_button(
                    label="📊 Descargar Excel",
                    data=b"Excel content",
                    file_name=f"etiquetas_{referencia}_{datetime.now().date()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

# --- GESTIÓN DE TRABAJADORES ---
def mostrar_gestion_trabajadores():
    st.markdown("""
    <div class='dashboard-header header-trabajadores'>
        <h1 class='header-title'>👥 Gestión de Personal</h1>
        <div class='header-subtitle'>Administración del equipo de trabajo Aeropostale</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Lista de Personal", "➕ Agregar Nuevo", "📊 Estadísticas"])
    
    with tab1:
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h4>👤 Personal Activo</h4>", unsafe_allow_html=True)
        
        # Obtener trabajadores de la base de datos local
        trabajadores = local_db.query('trabajadores')
        df_trabajadores = pd.DataFrame(trabajadores)
        
        if not df_trabajadores.empty:
            st.dataframe(
                df_trabajadores,
                use_container_width=True,
                column_config={
                    "nombre": st.column_config.TextColumn("Nombre", width="medium"),
                    "cargo": st.column_config.TextColumn("Cargo", width="medium"),
                    "estado": st.column_config.TextColumn(
                        "Estado",
                        width="small",
                        help="Estado del trabajador"
                    )
                }
            )
            
            # Estadísticas rápidas
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Total Personal", len(df_trabajadores))
            with col_s2:
                activos = len(df_trabajadores[df_trabajadores['estado'] == 'Activo'])
                st.metric("Activos", activos)
            with col_s3:
                st.metric("Diferentes Cargos", df_trabajadores['cargo'].nunique())
        else:
            st.info("No hay trabajadores registrados.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h4>📝 Registrar Nuevo Personal</h4>", unsafe_allow_html=True)
        
        with st.form("nuevo_trabajador"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nombre = st.text_input("Nombre Completo")
                cedula = st.text_input("Cédula/RUT")
                telefono = st.text_input("Teléfono")
            
            with col_f2:
                cargo = st.selectbox("Cargo", ["Operador", "Supervisor", "Auditor", "Administrativo", "Gerente"])
                departamento = st.selectbox("Departamento", ["Logística", "Almacén", "Transporte", "Administración"])
                fecha_ingreso = st.date_input("Fecha de Ingreso", datetime.now())
            
            submit = st.form_submit_button("💾 Guardar Trabajador", type="primary")
            
            if submit:
                if nombre and cargo:
                    # Simular guardado
                    nuevo_id = len(trabajadores) + 1
                    nuevo_trabajador = {
                        'id': nuevo_id,
                        'nombre': nombre,
                        'cargo': cargo,
                        'departamento': departamento,
                        'fecha_ingreso': fecha_ingreso.strftime('%Y-%m-%d'),
                        'estado': 'Activo'
                    }
                    
                    local_db.insert('trabajadores', nuevo_trabajador)
                    st.success(f"✅ Trabajador {nombre} registrado exitosamente!")
                    st.rerun()
                else:
                    st.error("❌ Por favor complete todos los campos obligatorios.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='filter-panel'>", unsafe_allow_html=True)
        st.markdown("<h4>📊 Estadísticas del Personal</h4>", unsafe_allow_html=True)
        
        if not df_trabajadores.empty:
            # Gráficos
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                dist_cargo = df_trabajadores['cargo'].value_counts()
                fig1 = px.pie(values=dist_cargo.values, names=dist_cargo.index, 
                            title="Distribución por Cargo")
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_g2:
                fig2 = px.bar(x=dist_cargo.index, y=dist_cargo.values,
                            title="Personal por Cargo",
                            labels={'x': 'Cargo', 'y': 'Cantidad'})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos para mostrar estadísticas.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- GESTIÓN DE DISTRIBUCIONES ---
def mostrar_gestion_distribuciones():
    st.markdown("""
    <div class='dashboard-header header-distribuciones'>
        <h1 class='header-title'>🚚 Gestión de Distribuciones</h1>
        <div class='header-subtitle'>Control y seguimiento de transportes: Tempo vs Luis Perugachi</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener datos de distribuciones
    distribuciones = local_db.query('distribuciones')
    df_dist = pd.DataFrame(distribuciones)
    
    if not df_dist.empty:
        # KPIs de transporte
        st.markdown("<div class='kpi-grid'>", unsafe_allow_html=True)
        col_t1, col_t2, col_t3 = st.columns(3)
        
        total_guias = df_dist['guías'].sum()
        
        with col_t1:
            tempo = df_dist[df_dist['transporte'] == 'Tempo']['guías'].sum()
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>🚛</div>
                <div class='kpi-title'>Tempo</div>
                <div class='kpi-value'>{tempo}</div>
                <div class='kpi-title'>{tempo/total_guias*100:.1f}% del total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_t2:
            luis = df_dist[df_dist['transporte'] == 'Luis Perugachi']['guías'].sum()
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>🚚</div>
                <div class='kpi-title'>Luis Perugachi</div>
                <div class='kpi-value'>{luis}</div>
                <div class='kpi-title'>{luis/total_guias*100:.1f}% del total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_t3:
            entregados = len(df_dist[df_dist['estado'] == 'Entregado'])
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>✅</div>
                <div class='kpi-title'>Entregados</div>
                <div class='kpi-value'>{entregados}</div>
                <div class='kpi-title'>{entregados/len(df_dist)*100:.1f}% completado</div>
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
        fig = px.bar(df_dist, x='transporte', y='guías', color='estado',
                    title="Distribución por Transporte y Estado",
                    barmode='group')
        st.plotly_chart(fig, use_container_width=True)
        
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

# --- AYUDA Y SOPORTE ---
def mostrar_ayuda():
    st.markdown("""
    <div class='dashboard-header header-ayuda'>
        <h1 class='header-title'>❓ Ayuda y Soporte Técnico</h1>
        <div class='header-subtitle'>Asistencia para el uso del Sistema ERP Aeropostale</div>
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
            
            #### 4. Generación de Guías
            - Creación de guías de envío
            - Asignación a transportistas
            - Generación de PDF
            
            #### 5. Etiquetas
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
# 6. SISTEMA DE AUTENTICACIÓN Y NAVEGACIÓN MODERNO
# ==============================================================================

def mostrar_pagina_login(rol_target):
    """Página de login moderna"""
    st.markdown("""
    <div class='login-container'>
        <div class='login-card'>
            <div class='login-logo'>
                <h1>AEROPOSTALE</h1>
                <p>Sistema ERP Integral</p>
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
                <div class='sidebar-logo'>AEROPOSTALE</div>
                <div class='sidebar-subtitle'>ERP Integral v3.0</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Estado de usuario
            if st.session_state.user_type:
                user_badge = "🛡️ ADMIN" if st.session_state.user_type == "admin" else "👤 USER"
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 10px; text-align: center;'>
                    <strong style='color: white;'>{user_badge}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            # Menú de navegación
            menu_items = {
                "Dashboard KPIs": {"icon": "📊", "role": "public"},
                "Reconciliación V8": {"icon": "💰", "role": "admin"},
                "Email Wilo AI": {"icon": "📧", "role": "admin"},
                "Generar Guías": {"icon": "📋", "role": "user"},
                "Etiquetas": {"icon": "🏷️", "role": "user"},
                "Trabajadores": {"icon": "👥", "role": "admin"},
                "Distribuciones": {"icon": "🚚", "role": "admin"},
                "Ayuda": {"icon": "❓", "role": "public"}
            }
            
            for page_name, page_info in menu_items.items():
                is_active = st.session_state.current_page == page_name
                button_class = "active" if is_active else ""
                
                # Crear botón personalizado
                if st.button(
                    f"{page_info['icon']} {page_name}",
                    key=f"btn_{page_name}",
                    use_container_width=True
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
                "Email Wilo AI": mostrar_modulo_email_wilo,
                "Generar Guías": mostrar_generacion_guias,
                "Etiquetas": mostrar_generacion_etiquetas,
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
                    "Generar Guías": "user",
                    "Etiquetas": "user",
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
        <div class="footer">
            <span class="footer-logo">AEROPOSTALE ERP</span> v3.0 | © 2025 Todos los derechos reservados.<br>
            Desarrollado con ❤️ para la optimización logística | <em>#EficienciaAeropostale</em>
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
        st.markdown("""
        <div class='filter-panel'>
            <h4>🆘 Sistema de Recuperación</h4>
            <p>La aplicación encontró un error. Por favor:</p>
            <ol>
                <li>Recargue la página (F5)</li>
                <li>Verifique sus archivos de entrada</li>
                <li>Contacte a soporte si el problema persiste</li>
            </ol>
            <p>Detalles técnicos: {}</p>
        </div>
        """.format(str(e)), unsafe_allow_html=True)
[file content end]
