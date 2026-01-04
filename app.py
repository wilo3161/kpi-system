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
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import smtplib
import imaplib
import json
from pathlib import Path
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
import unicodedata
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, stop_after_attempt, wait_exponential
from bs4 import BeautifulSoup  # REQUERIDO PARA CORRECCIÓN DE EMAIL

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Sistema de KPIs Aeropostale",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# --- LOGGING ---
logging.basicConfig(
    filename='logs/app_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
os.makedirs('logs', exist_ok=True)

# --- GESTIÓN DE SECRETOS (FALLBACK SEGURO) ---
def get_secret(key_path, default=None):
    """Obtiene secretos de st.secrets de forma segura"""
    try:
        keys = key_path.split('.')
        value = st.secrets
        for k in keys:
            value = value[k]
        return value
    except Exception:
        return default

# Variables Globales de Configuración
SUPABASE_URL = get_secret("supabase.url")
SUPABASE_KEY = get_secret("supabase.key")
ADMIN_PASSWORD = get_secret("auth.admin_password", "admin123")
USER_PASSWORD = get_secret("auth.user_password", "user123")

# --- INICIALIZACIÓN SUPABASE ---
@st.cache_resource
def init_supabase() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.sidebar.error("⚠️ Faltan credenciales de Supabase en secrets.toml")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error Supabase: {e}")
        return None

supabase = init_supabase()

# ================================
# CSS PROFESIONAL
# ================================
st.markdown("""
<style>
:root {
    --primary-blue: #004085;
    --secondary-blue: #007BFF;
    --success-green: #28A745;
    --warning-yellow: #FFC107;
    --danger-red: #DC3545;
    --light-bg: #f8f9fa;
    --border-radius: 8px;
}
body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
.stApp { background-color: transparent; }
.dashboard-header {
    background: linear-gradient(90deg, #004085 0%, #007BFF 100%);
    padding: 25px 30px;
    border-radius: 8px;
    margin: 15px 0 25px 0;
    box-shadow: 0 4px 12px rgba(0, 64, 133, 0.15);
    color: white;
}
.header-title { font-size: 2.2rem; font-weight: 700; margin: 0; color: white !important; }
.header-subtitle { font-size: 1rem; opacity: 0.9; margin-top: 5px; color: #e0e0e0 !important; }
.kpi-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
    border-left: 5px solid #007BFF;
    transition: transform 0.3s;
}
.kpi-card:hover { transform: translateY(-5px); }
.kpi-title { font-size: 0.9rem; color: #6c757d; text-transform: uppercase; font-weight: 600; }
.kpi-value { font-size: 2.2rem; font-weight: 700; color: #004085; margin: 5px 0; }
.alert-banner { padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 5px solid; }
.alert-info { background: #e3f2fd; border-color: #2196f3; color: #0d47a1; }
.alert-success { background: #d4edda; border-color: #28a745; color: #155724; }
.alert-warning { background: #fff3cd; border-color: #ffc107; color: #856404; }
.alert-danger { background: #f8d7da; border-color: #dc3545; color: #721c24; }
.filter-panel { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e9ecef; }
.team-card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px; border: 1px solid #e9ecef; }
.footer { text-align: center; padding: 20px; margin-top: 40px; color: #6c757d; border-top: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# ================================
# FUNCIONES AUXILIARES (NORMALIZACIÓN V8)
# ================================
def normalizar_texto_wilo(texto):
    """Normaliza texto eliminando acentos y caracteres especiales"""
    if pd.isna(texto) or texto == '': return ''
    texto = str(texto)
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except: pass
    texto = re.sub(r'[^A-Za-z0-9\s]', ' ', texto.upper())
    return re.sub(r'\s+', ' ', texto).strip()

def procesar_subtotal_wilo(valor):
    """Convierte valores monetarios sucios a float robustamente"""
    if pd.isna(valor): return 0.0
    try:
        if isinstance(valor, (int, float)): return float(valor)
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
    except: return 0.0

def identificar_tipo_tienda_v8(nombre):
    """Clasificación inteligente para V8.0 (Incluye JOFRE SANTANA)"""
    if pd.isna(nombre) or nombre == '': return "DESCONOCIDO"
    nombre_upper = normalizar_texto_wilo(nombre)
    
    # REGLA JOFRE SANTANA (SOLICITUD EXPLICITA)
    if 'JOFRE' in nombre_upper and 'SANTANA' in nombre_upper:
        return "VENTAS AL POR MAYOR"
    
    fisicas = ['LOCAL', 'AEROPOSTALE', 'MALL', 'PLAZA', 'SHOPPING', 'CENTRO', 'COMERCIAL', 'CC', 
               'TIENDA', 'SUCURSAL', 'PASEO', 'PORTAL', 'DORADO', 'CITY', 'CEIBOS', 
               'QUITO', 'GUAYAQUIL', 'AMBATO', 'MANTA', 'MACHALA', 'RIOCENTRO']
    
    if any(p in nombre_upper for p in fisicas):
        return "TIENDA FÍSICA"
    
    # Nombres personales cortos suelen ser ventas web
    if len(nombre_upper.split()) < 4:
        return "VENTA WEB"
        
    return "TIENDA FÍSICA"

# ================================
# MÓDULO EMAIL WILO (CORREGIDO)
# ================================
NOVEDAD_PATTERNS = {
    "PRENDA_MAS": r"(?:extra|adicional|demás|sobrante).{0,15}prenda[s]?",
    "PRENDA_MENOS": r"(?:falta|faltante|no\s+recib|incompleto).{0,15}prenda[s]?",
    "MANCHADA": r"manchad[ao]|stain|suciedad",
    "ROTA": r"rota|roto|desgarrad[ao]|torn|agujero",
    "CRUCE_CODIGO": r"cruce|etiqueta|sku|mismatch"
}

class WiloAIEngine:
    def __init__(self):
        self.imap_url = get_secret("email.imap_server", "mail.fashionclub.com.ec")
        self.email_user = get_secret("email.username", "")
        self.email_pass = get_secret("email.password", "")

    def connect_imap(self):
        try:
            if not self.email_user or not self.email_pass:
                return None
            mail = imaplib.IMAP4_SSL(self.imap_url, 993)
            mail.login(self.email_user, self.email_pass)
            return mail
        except Exception as e:
            logger.error(f"Error IMAP: {e}")
            return None

    def decode_mime_header(self, s):
        try:
            decoded = decode_header(s)
            content, encoding = decoded[0]
            if isinstance(content, bytes):
                return content.decode(encoding or 'utf-8', errors='ignore')
            return str(content)
        except: return str(s)

    def get_email_body_robust(self, msg):
        """Versión CORREGIDA que extrae texto de HTML si es necesario"""
        cuerpo = ""
        try:
            if msg.is_multipart():
                parte_texto = None
                parte_html = None
                
                for part in msg.walk():
                    ctype = part.get_content_type()
                    dispo = str(part.get("Content-Disposition"))
                    if "attachment" in dispo: continue
                    
                    if ctype == "text/plain" and not parte_texto: parte_texto = part
                    elif ctype == "text/html" and not parte_html: parte_html = part
                
                if parte_texto:
                    payload = parte_texto.get_payload(decode=True)
                    cuerpo = payload.decode('utf-8', errors='ignore')
                elif parte_html:
                    # FALLBACK: Extraer texto de HTML usando BeautifulSoup
                    payload = parte_html.get_payload(decode=True)
                    html = payload.decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, "html.parser")
                    cuerpo = soup.get_text(separator="\n")
            else:
                payload = msg.get_payload(decode=True)
                text = payload.decode('utf-8', errors='ignore')
                if msg.get_content_type() == "text/html":
                    soup = BeautifulSoup(text, "html.parser")
                    cuerpo = soup.get_text(separator="\n")
                else:
                    cuerpo = text
            
            return cuerpo[:5000].strip() if cuerpo else "[Sin contenido legible]"
        except Exception as e:
            return f"Error leyendo cuerpo: {str(e)}"

    def fetch_emails(self, limit=10):
        mail = self.connect_imap()
        if not mail: return []
        
        results = []
        try:
            mail.select("INBOX")
            _, data = mail.search(None, 'ALL')
            ids = data[0].split()[-limit:]
            
            for i in reversed(ids):
                _, msg_data = mail.fetch(i, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                asunto = self.decode_mime_header(msg.get("Subject", ""))
                remitente = msg.get("From", "")
                fecha = msg.get("Date", "")
                cuerpo = self.get_email_body_robust(msg)
                
                # Clasificación simple
                tipo = "OTRO"
                urgencia = "BAJA"
                for k, v in NOVEDAD_PATTERNS.items():
                    if re.search(v, cuerpo + asunto, re.IGNORECASE):
                        tipo = k
                        if k in ["ROTA", "MANCHADA", "CRUCE_CODIGO"]: urgencia = "ALTA"
                        elif k in ["PRENDA_MENOS"]: urgencia = "MEDIA"
                        break
                
                results.append({
                    "id": i.decode(),
                    "fecha": fecha,
                    "asunto": asunto,
                    "remitente": remitente,
                    "cuerpo": cuerpo,
                    "tipo": tipo,
                    "urgencia": urgencia
                })
            mail.logout()
            return results
        except Exception as e:
            logger.error(f"Error fetching: {e}")
            return []

def modulo_novedades_correo_mejorado():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📧 Auditoría de Correos Wilo</h1></div>", unsafe_allow_html=True)
    
    if st.button("🔄 Escanear Bandeja"):
        engine = WiloAIEngine()
        with st.spinner("Analizando correos (decodificando HTML)..."):
            emails = engine.fetch_emails(limit=15)
        
        if not emails:
            st.warning("No se encontraron correos o error de conexión.")
        else:
            df = pd.DataFrame(emails)
            st.dataframe(df[['fecha', 'remitente', 'asunto', 'tipo', 'urgencia']], use_container_width=True)
            
            st.markdown("### 🔍 Inspector de Contenido")
            sel = st.selectbox("Ver detalle de:", df['id'])
            if sel:
                row = df[df['id'] == sel].iloc[0]
                st.info(f"**Asunto:** {row['asunto']}")
                st.text_area("Contenido Extraído:", row['cuerpo'], height=300)

# ================================
# MÓDULO RECONCILIACIÓN V8 (CORREGIDO)
# ================================
def mostrar_reconciliacion():
    """Versión V8.0 Integrada de Reconciliación con Soporte de PIEZAS y JOFRE SANTANA"""
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📦 Reconciliación Logística V8.0</h1><div class='header-subtitle'>Soporte para Piezas y Ventas Mayoristas</div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader("📂 Manifiesto (Con columna PIEZAS)", type=['xlsx', 'xls', 'csv'])
    with col2:
        f_facturas = st.file_uploader("📂 Facturas (Con VALORES)", type=['xlsx', 'xls', 'csv'])

    if f_manifiesto and f_facturas:
        try:
            # Carga flexible
            df_m = pd.read_excel(f_manifiesto) if f_manifiesto.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_manifiesto)
            df_f = pd.read_excel(f_facturas) if f_facturas.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_facturas)

            st.markdown("<div class='filter-panel'><h3 class='filter-title'>⚙️ Configuración de Columnas</h3>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("Configuración Manifiesto")
                cols_m = df_m.columns.tolist()
                # Detección automática
                idx_guia_m = next((i for i, c in enumerate(cols_m) if 'GUIA' in str(c).upper()), 0)
                idx_dest_m = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['DEST', 'CLIEN', 'NOMB'])), 0)
                idx_piezas = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['PIEZA', 'CANT', 'BULT'])), 0)
                idx_val_m = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL'])), 0)

                col_guia_m = st.selectbox("Columna Guía", cols_m, index=idx_guia_m, key='m_guia')
                col_dest_m = st.selectbox("Columna Destinatario", cols_m, index=idx_dest_m, key='m_dest')
                col_piezas_m = st.selectbox("Columna Piezas/Bultos", cols_m, index=idx_piezas, key='m_piezas')
                col_valor_m = st.selectbox("Columna Valor Declarado", cols_m, index=idx_val_m, key='m_val')
            
            with c2:
                st.info("Configuración Facturas")
                cols_f = df_f.columns.tolist()
                idx_guia_f = next((i for i, c in enumerate(cols_f) if 'GUIA' in str(c).upper()), 0)
                idx_val_f = next((i for i, c in enumerate(cols_f) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL', 'SUBT'])), 0)

                col_guia_f = st.selectbox("Columna Guía", cols_f, index=idx_guia_f, key='f_guia')
                col_valor_f = st.selectbox("Columna Valor Cobrado", cols_f, index=idx_val_f, key='f_val')
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("🚀 PROCESAR RECONCILIACIÓN", type="primary", use_container_width=True):
                with st.spinner("Procesando datos y aplicando lógica V8..."):
                    # Normalización
                    df_m['GUIA_CLEAN'] = df_m[col_guia_m].astype(str).str.strip().str.upper()
                    df_f['GUIA_CLEAN'] = df_f[col_guia_f].astype(str).str.strip().str.upper()
                    
                    # Merge
                    df_final = pd.merge(df_m, df_f, on='GUIA_CLEAN', how='left', suffixes=('_MAN', '_FAC'))
                    
                    # Lógica de Negocio V8
                    df_final['DESTINATARIO_NORM'] = df_final[col_dest_m].fillna('DESCONOCIDO')
                    df_final['TIPO_TIENDA'] = df_final['DESTINATARIO_NORM'].apply(identificar_tipo_tienda_v8)
                    
                    # Datos Numéricos
                    df_final['PIEZAS_CALC'] = pd.to_numeric(df_final[col_piezas_m], errors='coerce').fillna(1)
                    df_final['VALOR_REAL'] = df_final[col_valor_f].apply(procesar_subtotal_wilo).fillna(0)
                    df_final['VALOR_MAN'] = df_final[col_valor_m].apply(procesar_subtotal_wilo).fillna(0)
                    
                    # Creación de Grupos
                    def crear_grupo(row):
                        tipo = row['TIPO_TIENDA']
                        nom = normalizar_texto_wilo(row['DESTINATARIO_NORM'])
                        if tipo == "VENTAS AL POR MAYOR": return "VENTAS AL POR MAYOR - JOFRE SANTANA"
                        if tipo == "VENTA WEB": return f"WEB - {nom}"
                        return f"TIENDA - {nom}"
                    
                    df_final['GRUPO'] = df_final.apply(crear_grupo, axis=1)

                    # --- RESULTADOS ---
                    total_facturado = df_final['VALOR_REAL'].sum()
                    total_piezas = df_final['PIEZAS_CALC'].sum()
                    con_factura = df_final[df_final['VALOR_REAL'] > 0].shape[0]
                    sin_factura = df_final[df_final['VALOR_REAL'] == 0].shape[0]
                    
                    st.markdown("<div class='dashboard-header'><h2>📊 Resultados del Análisis</h2></div>", unsafe_allow_html=True)
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Total Facturado", f"${total_facturado:,.2f}")
                    k2.metric("Total Piezas", f"{total_piezas:,.0f}")
                    k3.metric("Guías Conciliadas", f"{con_factura}")
                    k4.metric("Guías Sin Factura", f"{sin_factura}")
                    
                    tab1, tab2, tab3 = st.tabs(["Resumen por Canal", "Detalle por Grupo", "Datos Crudos"])
                    
                    with tab1:
                        resumen = df_final.groupby('TIPO_TIENDA').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).reset_index()
                        resumen['% Gasto'] = (resumen['VALOR_REAL'] / total_facturado * 100).round(2)
                        st.dataframe(resumen.style.format({'VALOR_REAL': '${:,.2f}', '% Gasto': '{:.2f}%'}), use_container_width=True)
                        fig = px.pie(resumen, values='VALOR_REAL', names='TIPO_TIENDA', title="Distribución de Gasto", color_discrete_sequence=px.colors.qualitative.Set3)
                        st.plotly_chart(fig, use_container_width=True)

                    with tab2:
                        detalle = df_final.groupby('GRUPO').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).sort_values('VALOR_REAL', ascending=False)
                        st.dataframe(detalle.style.format({'VALOR_REAL': '${:,.2f}'}), use_container_width=True)
                    
                    with tab3:
                        st.dataframe(df_final)

                    # Exportación
                    st.markdown("### 💾 Descargar Reportes")
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, sheet_name='Data_Completa', index=False)
                        resumen.to_excel(writer, sheet_name='Resumen_Canal', index=False)
                        detalle.to_excel(writer, sheet_name='Detalle_Grupos')
                    
                    st.download_button(
                        label="📥 Descargar Excel Completo",
                        data=buffer.getvalue(),
                        file_name=f"conciliacion_v8_{datetime.now().date()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"Error procesando archivos: {str(e)}")

# ================================
# RESTO DE MÓDULOS DEL SISTEMA
# ================================

def validar_fecha(fecha: str) -> bool:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError: return False

def mostrar_dashboard_kpis():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📊 Dashboard KPIs</h1></div>", unsafe_allow_html=True)
    if not supabase:
        st.error("Error conexión BD")
        return
    # Lógica simplificada de visualización para mantener funcionalidad básica
    st.info("Conectado a Supabase. Seleccione un rango de fechas para ver métricas.")
    col1, col2 = st.columns(2)
    with col1: st.date_input("Inicio")
    with col2: st.date_input("Fin")
    
    # Mockup visual para mantener estética
    k1, k2, k3 = st.columns(3)
    k1.markdown("""<div class='kpi-card'><div class='kpi-title'>Producción</div><div class='kpi-value'>1,250</div></div>""", unsafe_allow_html=True)
    k2.markdown("""<div class='kpi-card'><div class='kpi-title'>Eficiencia</div><div class='kpi-value'>95%</div></div>""", unsafe_allow_html=True)
    k3.markdown("""<div class='kpi-card'><div class='kpi-title'>Alertas</div><div class='kpi-value' style='color:red'>2</div></div>""", unsafe_allow_html=True)

def mostrar_generacion_guias():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📋 Generar Guías</h1></div>", unsafe_allow_html=True)
    with st.form("guias_form"):
        c1, c2 = st.columns(2)
        c1.selectbox("Tienda", ["Mall del Sol", "San Marino", "Quicentro"])
        c2.text_input("Tracking #")
        if st.form_submit_button("Generar PDF"):
            st.success("Guía generada (Simulación)")

def mostrar_ayuda():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>❓ Ayuda</h1></div>", unsafe_allow_html=True)
    st.info("Contactar soporte: wilson.perez@aeropostale.com")

def verificar_password(rol):
    # Simulación de auth simple
    return True 

def solicitar_autenticacion(rol):
    st.warning("Debe iniciar sesión")

# ================================
# ORQUESTADOR PRINCIPAL
# ================================
def main():
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None

    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: white;'>AEROPOSTALE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #ccc;'>Sistema Integral v2.1</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Menú de Navegación
        menu_options = [
            ("Dashboard KPIs", "📊", mostrar_dashboard_kpis, "public"),
            ("Reconciliación V8", "💰", mostrar_reconciliacion, "admin"),
            ("Auditoría Email Wilo", "📧", modulo_novedades_correo_mejorado, "admin"),
            ("Generar Guías", "📋", mostrar_generacion_guias, "user"),
            ("Ayuda", "❓", mostrar_ayuda, "public")
        ]
        
        for label, icon, func, perm in menu_options:
            if st.button(f"{icon} {label}", use_container_width=True):
                st.session_state.current_page = func
        
        st.markdown("---")
        if st.session_state.user_type:
            if st.button("Cerrar Sesión"):
                st.session_state.user_type = None
                st.rerun()
        else:
            if st.button("Ingresar como Admin"):
                st.session_state.user_type = "admin"
                st.rerun()

    # Router de páginas
    if 'current_page' not in st.session_state:
        st.session_state.current_page = mostrar_dashboard_kpis
    
    # Ejecutar página actual
    st.session_state.current_page()

    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.1 | Desarrrollado por Wilson Pérez<br>
        © 2025 Todos los derechos reservados
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico: {e}")
        logger.error(f"Crash: {e}", exc_info=True)
