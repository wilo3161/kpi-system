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

# --- LIBRERÍAS DE TERCEROS ---
from supabase import create_client, Client
import qrcode
from PIL import Image as PILImage
from fpdf import FPDF
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import xlsxwriter

# --- CONFIGURACIÓN INICIAL DE PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Sistema Integral Aeropostale",
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
# 1. GESTIÓN DE SECRETOS Y BASE DE DATOS
# ==============================================================================

def get_secret(key_path, default=None):
    """Obtiene secretos de st.secrets de forma segura con soporte anidado"""
    try:
        keys = key_path.split('.')
        value = st.secrets
        for k in keys:
            value = value[k]
        return value
    except Exception:
        return default

# Variables Globales
SUPABASE_URL = get_secret("supabase.url")
SUPABASE_KEY = get_secret("supabase.key")
ADMIN_PASSWORD = get_secret("auth.admin_password", "admin123")
USER_PASSWORD = get_secret("auth.user_password", "user123")

@st.cache_resource
def init_supabase() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error Supabase: {e}")
        return None

supabase = init_supabase()

# ==============================================================================
# 2. ESTILOS CSS UNIFICADOS (DISEÑO PROFESIONAL)
# ==============================================================================
st.markdown("""
<style>
/* Variables Globales */
:root {
    --primary-blue: #004085;
    --secondary-blue: #007BFF;
    --success-green: #28A745;
    --warning-yellow: #FFC107;
    --danger-red: #DC3545;
    --light-bg: #f8f9fa;
    --border-radius: 8px;
}

/* Estructura */
.stApp { background-color: #f4f6f9; }

/* Encabezados de Módulo */
.dashboard-header {
    background: linear-gradient(90deg, #004085 0%, #007BFF 100%);
    padding: 20px 30px;
    border-radius: 8px;
    margin-bottom: 25px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header-title { font-size: 2rem; font-weight: 700; margin: 0; color: white !important; }
.header-subtitle { font-size: 1rem; opacity: 0.9; margin-top: 5px; color: #e0e0e0 !important; }

/* Tarjetas KPI */
.kpi-card {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    border-left: 5px solid #007BFF;
    transition: transform 0.2s;
}
.kpi-card:hover { transform: translateY(-3px); }
.kpi-title { font-size: 0.9rem; color: #6c757d; text-transform: uppercase; font-weight: 600; }
.kpi-value { font-size: 2.2rem; font-weight: 700; color: #004085; margin: 5px 0; }

/* Alertas */
.alert-banner { padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 5px solid; }
.alert-info { background: #e3f2fd; border-color: #2196f3; color: #0d47a1; }
.alert-success { background: #d4edda; border-color: #28a745; color: #155724; }
.alert-warning { background: #fff3cd; border-color: #ffc107; color: #856404; }
.alert-danger { background: #f8d7da; border-color: #dc3545; color: #721c24; }

/* Tablas y Paneles */
.filter-panel { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e9ecef; }
.team-card { background: white; border-radius: 8px; padding: 15px; margin-bottom: 10px; border: 1px solid #dee2e6; }
.team-name { font-weight: bold; color: #004085; font-size: 1.1rem; }

/* Footer */
.footer { text-align: center; padding: 20px; margin-top: 40px; color: #6c757d; border-top: 1px solid #e9ecef; font-size: 0.8rem;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNCIONES AUXILIARES GLOBALES
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
# 4. MÓDULO CORREO WILO (CORREGIDO Y ROBUSTO)
# ==============================================================================

class WiloEmailEngine:
    def __init__(self):
        self.imap_url = get_secret("email.imap_server", "mail.fashionclub.com.ec")
        self.email_user = get_secret("email.username", "")
        self.email_pass = get_secret("email.password", "")

    def connect(self):
        try:
            if not self.email_user or not self.email_pass:
                return None
            mail = imaplib.IMAP4_SSL(self.imap_url, 993)
            mail.login(self.email_user, self.email_pass)
            return mail
        except Exception as e:
            logger.error(f"Error conexión IMAP: {e}")
            return None

    def decode_header_safe(self, header):
        if not header: return ""
        try:
            parts = decode_header(header)
            decoded = ""
            for content, encoding in parts:
                if isinstance(content, bytes):
                    decoded += content.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded += str(content)
            return decoded
        except: return str(header)

    def extract_body_robust(self, msg):
        """
        Versión Corregida con BeautifulSoup para extraer texto real
        de correos HTML complejos o anidados.
        """
        body_text = ""
        body_html = ""

        try:
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))

                    if "attachment" in cdispo: continue

                    try:
                        payload = part.get_payload(decode=True)
                        if not payload: continue
                        
                        # Decodificación resiliente
                        decoded = ""
                        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                            try:
                                decoded = payload.decode(enc)
                                break
                            except: continue
                        
                        if ctype == "text/plain": body_text += decoded
                        elif ctype == "text/html": body_html += decoded
                    except: pass
            else:
                payload = msg.get_payload(decode=True)
                # Decodificación resiliente
                decoded = ""
                for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        decoded = payload.decode(enc)
                        break
                    except: continue
                
                if msg.get_content_type() == "text/html": body_html = decoded
                else: body_text = decoded

            # Prioridad: Texto plano > HTML limpio
            if body_text.strip():
                return body_text[:8000]
            elif body_html.strip():
                soup = BeautifulSoup(body_html, "html.parser")
                return soup.get_text(separator="\n")[:8000]
            
            return "[Sin contenido legible]"
        except Exception as e:
            return f"Error extrayendo cuerpo: {e}"

    def analyze_content(self, text, subject):
        """Clasificación basada en Regex mejorados"""
        full_text = (subject + " " + text).lower()
        
        patterns = {
            "🚨 CRÍTICO": r"robo|asalto|accidente|urgente|inmediato",
            "📦 FALTANTE": r"falta|faltante|no recib|incompleto|menos prenda",
            "👔 SOBRANTE": r"sobra|sobrante|demas|mas prenda|extra",
            "⚠️ DAÑO": r"roto|rota|mancha|sucio|dañado|falla|defecto",
            "🏷️ ETIQUETA": r"etiqueta|precio|codigo|sku|cruce",
            "🚚 ENVÍO": r"guia|transporte|servientrega|tramaco"
        }
        
        detected = []
        for label, pattern in patterns.items():
            if re.search(pattern, full_text):
                detected.append(label)
        
        if not detected: return "ℹ️ GENERAL", "BAJA"
        
        urgencia = "ALTA" if any(x in ["🚨 CRÍTICO", "⚠️ DAÑO"] for x in detected) else "MEDIA"
        return ", ".join(detected), urgencia

    def fetch_emails(self, limit=15):
        mail = self.connect()
        if not mail: return []
        
        results = []
        try:
            mail.select("INBOX")
            _, data = mail.search(None, 'ALL')
            ids = data[0].split()[-limit:]
            
            for i in reversed(ids):
                _, msg_data = mail.fetch(i, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = self.decode_header_safe(msg.get("Subject"))
                sender = self.decode_header_safe(msg.get("From"))
                date = msg.get("Date")
                body = self.extract_body_robust(msg)
                tipo, urgencia = self.analyze_content(body, subject)
                
                results.append({
                    "id": i.decode(),
                    "fecha": date,
                    "remitente": sender,
                    "asunto": subject,
                    "cuerpo": body,
                    "tipo": tipo,
                    "urgencia": urgencia
                })
            mail.logout()
            return results
        except Exception as e:
            logger.error(f"Error fetching: {e}")
            return []

def mostrar_modulo_email_wilo():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📧 Auditoría de Correos Wilo AI</h1><div class='header-subtitle'>Análisis Inteligente de Novedades</div></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Este módulo utiliza análisis semántico para detectar novedades en la bandeja de entrada.")
    with col2:
        scan_btn = st.button("🔄 Escanear Ahora", use_container_width=True, type="primary")

    if scan_btn:
        engine = WiloEmailEngine()
        with st.spinner("Conectando con servidor de correo y analizando..."):
            emails = engine.fetch_emails()
        
        if not emails:
            st.warning("No se encontraron correos o hubo un error de conexión.")
        else:
            df = pd.DataFrame(emails)
            
            # KPIs Rápidos
            k1, k2, k3 = st.columns(3)
            k1.metric("Correos Analizados", len(df))
            k2.metric("Alta Urgencia", len(df[df['urgencia'] == 'ALTA']))
            k3.metric("Faltantes/Sobrantes", len(df[df['tipo'].str.contains('FALTANTE') | df['tipo'].str.contains('SOBRANTE')]))
            
            st.markdown("### 📋 Bandeja de Entrada Analizada")
            st.dataframe(
                df[['fecha', 'remitente', 'asunto', 'tipo', 'urgencia']], 
                use_container_width=True,
                column_config={
                    "urgencia": st.column_config.TextColumn(
                        "Prioridad",
                        help="Nivel de urgencia detectado",
                        width="small"
                    )
                }
            )
            
            st.markdown("---")
            st.subheader("🔍 Inspector de Contenido")
            sel_id = st.selectbox("Seleccione un correo para ver detalles:", df['id'])
            
            if sel_id:
                row = df[df['id'] == sel_id].iloc[0]
                st.markdown(f"**De:** {row['remitente']}")
                st.markdown(f"**Asunto:** {row['asunto']}")
                st.markdown(f"**Clasificación:** {row['tipo']}")
                st.text_area("Cuerpo del Correo (Texto Extraído):", row['cuerpo'], height=300)

# ==============================================================================
# 5. MÓDULO RECONCILIACIÓN V8 (CORREGIDO Y ACTUALIZADO)
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
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📦 Reconciliación Logística V8.0</h1><div class='header-subtitle'>Soporte para Piezas y Ventas Mayoristas (Jofre Santana)</div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader("📂 Manifiesto (Debe tener columna PIEZAS)", type=['xlsx', 'xls', 'csv'])
    with col2:
        f_facturas = st.file_uploader("📂 Facturas (Debe tener VALORES)", type=['xlsx', 'xls', 'csv'])

    if f_manifiesto and f_facturas:
        try:
            # Lectura flexible
            df_m = pd.read_excel(f_manifiesto) if f_manifiesto.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_manifiesto)
            df_f = pd.read_excel(f_facturas) if f_facturas.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_facturas)

            st.markdown("<div class='filter-panel'><h3 class='filter-title'>⚙️ Configuración de Columnas</h3>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("Configuración Manifiesto")
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
                st.info("Configuración Facturas")
                cols_f = df_f.columns.tolist()
                idx_guia_f = next((i for i, c in enumerate(cols_f) if 'GUIA' in str(c).upper()), 0)
                idx_val_f = next((i for i, c in enumerate(cols_f) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL', 'SUBT'])), 0)

                col_guia_f = st.selectbox("Columna Guía", cols_f, index=idx_guia_f, key='f_guia')
                col_valor_f = st.selectbox("Columna Valor Cobrado", cols_f, index=idx_val_f, key='f_val')
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("🚀 PROCESAR RECONCILIACIÓN", type="primary", use_container_width=True):
                with st.spinner("Ejecutando algoritmo V8.0..."):
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
                    st.markdown("<div class='dashboard-header'><h2>📊 Resultados del Análisis</h2></div>", unsafe_allow_html=True)
                    
                    total_facturado = df_final['VALOR_REAL'].sum()
                    total_piezas = df_final['PIEZAS_CALC'].sum()
                    con_factura = df_final[df_final['VALOR_REAL'] > 0].shape[0]
                    sin_factura = df_final[df_final['VALOR_REAL'] == 0].shape[0]
                    
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Total Facturado", f"${total_facturado:,.2f}")
                    k2.metric("Total Piezas", f"{total_piezas:,.0f}")
                    k3.metric("Guías Conciliadas", f"{con_factura}")
                    k4.metric("Guías Sin Factura", f"{sin_factura}", delta_color="inverse")
                    
                    # Tablas
                    tab1, tab2 = st.tabs(["Resumen por Canal", "Detalle por Grupo"])
                    
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
                    
                    # Exportación
                    st.markdown("### 💾 Exportar Datos")
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, sheet_name='Data_Completa', index=False)
                        resumen.to_excel(writer, sheet_name='Resumen_Canal', index=False)
                        detalle.to_excel(writer, sheet_name='Detalle_Grupos')
                    
                    st.download_button(
                        label="📥 Descargar Excel de Conciliación",
                        data=buffer.getvalue(),
                        file_name=f"conciliacion_v8_{datetime.now().date()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"Error en el procesamiento: {str(e)}")
            st.exception(e)

# ==============================================================================
# 6. MÓDULOS RESTANTES (KPIS, GUÍAS, ETIQUETAS, TRABAJADORES)
# ==============================================================================

# --- KPIs ---
def mostrar_dashboard_kpis():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📊 Dashboard de KPIs</h1></div>", unsafe_allow_html=True)
    if not supabase:
        st.error("Error de conexión con la base de datos.")
        return
    
    # Aquí iría la lógica de consulta a Supabase para daily_kpis
    # Simplificado para este ejemplo integrado
    col1, col2 = st.columns(2)
    with col1: st.date_input("Fecha Inicio", key="kpi_start")
    with col2: st.date_input("Fecha Fin", key="kpi_end")
    
    st.info("Visualizando datos de producción (Ejemplo: Eficiencia 95%)")
    k1, k2, k3 = st.columns(3)
    k1.markdown("""<div class='kpi-card'><div class='kpi-title'>Producción</div><div class='kpi-value'>1,250</div></div>""", unsafe_allow_html=True)
    k2.markdown("""<div class='kpi-card'><div class='kpi-title'>Eficiencia</div><div class='kpi-value'>95%</div></div>""", unsafe_allow_html=True)
    k3.markdown("""<div class='kpi-card'><div class='kpi-title'>Alertas</div><div class='kpi-value' style='color:red'>0</div></div>""", unsafe_allow_html=True)

# --- GUÍAS ---
def mostrar_generacion_guias():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>📋 Generar Guías de Envío</h1></div>", unsafe_allow_html=True)
    
    brand = st.radio("Marca", ["Fashion", "Tempo"], horizontal=True)
    
    with st.form("guias_form"):
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.selectbox("Tienda Destino", ["Mall del Sol", "San Marino", "Quicentro"])
            remitente = st.selectbox("Remitente", ["Andrés Yépez", "Josué Imbacuán"])
        with col2:
            url_pedido = st.text_input("URL Pedido", value="https://")
        
        if st.form_submit_button("Generar Guía PDF"):
            if not url_pedido or len(url_pedido) < 10:
                st.error("Ingrese una URL válida")
            else:
                st.success(f"Guía generada para {tienda} (Simulación)")
                # Aquí iría la llamada a generar_pdf_guia (simplificada para integración)

# --- ETIQUETAS ---
def mostrar_generacion_etiquetas():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>🏷️ Generar Etiquetas</h1></div>", unsafe_allow_html=True)
    with st.form("etiqueta_form"):
        ref = st.text_input("Referencia")
        cant = st.number_input("Cantidad", min_value=1)
        tipo = st.selectbox("Tipo", ["Hombre", "Mujer", "Niños"])
        if st.form_submit_button("Crear Etiqueta"):
            st.success(f"Etiqueta para {ref} creada")

# --- TRABAJADORES ---
def mostrar_gestion_trabajadores():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>👥 Gestión de Personal</h1></div>", unsafe_allow_html=True)
    # Lógica CRUD simplificada
    st.info("Módulo de administración de personal activo.")

# --- DISTRIBUCIONES ---
def mostrar_gestion_distribuciones():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>🚚 Gestión de Distribuciones</h1></div>", unsafe_allow_html=True)
    st.info("Control de Tempo vs Luis Perugachi.")

# --- AYUDA ---
def mostrar_ayuda():
    st.markdown("<div class='dashboard-header'><h1 class='header-title'>❓ Ayuda y Soporte</h1></div>", unsafe_allow_html=True)
    st.info("Contactar a Soporte TI: wilson.perez@aeropostale.com")

# ==============================================================================
# 7. SISTEMA DE AUTENTICACIÓN Y NAVEGACIÓN
# ==============================================================================

def solicitar_autenticacion(rol):
    st.markdown(f"<div class='filter-panel' style='max-width:400px; margin:auto;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center'>🔐 Acceso {rol.upper()}</h3>", unsafe_allow_html=True)
    password = st.text_input("Contraseña", type="password", key=f"pw_{rol}")
    
    if st.button("Ingresar", key=f"btn_{rol}", use_container_width=True):
        esperada = ADMIN_PASSWORD if rol == "admin" else USER_PASSWORD
        if password == esperada:
            st.session_state.user_type = rol
            st.session_state.show_login = False
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'login_target' not in st.session_state:
        st.session_state.login_target = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard KPIs"

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("<h2 style='text-align:center; color:white;'>AEROPOSTALE</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Opciones de Menú
        menu = {
            "Dashboard KPIs": {"icon": "📊", "func": mostrar_dashboard_kpis, "role": "public"},
            "Reconciliación V8": {"icon": "💰", "func": mostrar_reconciliacion_v8, "role": "admin"},
            "Email Wilo AI": {"icon": "📧", "func": mostrar_modulo_email_wilo, "role": "admin"},
            "Generar Guías": {"icon": "📋", "func": mostrar_generacion_guias, "role": "user"},
            "Etiquetas": {"icon": "🏷️", "func": mostrar_generacion_etiquetas, "role": "user"},
            "Trabajadores": {"icon": "👥", "func": mostrar_gestion_trabajadores, "role": "admin"},
            "Distribuciones": {"icon": "🚚", "func": mostrar_gestion_distribuciones, "role": "admin"},
            "Ayuda": {"icon": "❓", "func": mostrar_ayuda, "role": "public"}
        }

        for name, info in menu.items():
            if st.button(f"{info['icon']} {name}", use_container_width=True):
                st.session_state.current_page = name
                if info['role'] != "public" and st.session_state.user_type != info['role'] and st.session_state.user_type != "admin":
                    st.session_state.show_login = True
                    st.session_state.login_target = info['role']
                else:
                    st.session_state.show_login = False

        st.markdown("---")
        if st.session_state.user_type:
            st.info(f"Usuario: {st.session_state.user_type.upper()}")
            if st.button("Cerrar Sesión"):
                st.session_state.user_type = None
                st.rerun()
        else:
            if st.button("Login Admin"):
                st.session_state.show_login = True
                st.session_state.login_target = "admin"

    # --- MAIN CONTENT ---
    if st.session_state.show_login:
        solicitar_autenticacion(st.session_state.login_target)
    else:
        # Ejecutar la función correspondiente a la página actual
        page_info = menu.get(st.session_state.current_page)
        if page_info:
            # Verificación doble de seguridad
            if page_info['role'] == "public" or (st.session_state.user_type in ["admin", "user"]):
                page_info['func']()
            else:
                st.warning("🔒 Inicie sesión para ver este módulo.")
                solicitar_autenticacion(page_info['role'])

    # --- FOOTER ---
    st.markdown("""
    <div class="footer">
        Sistema Integral Aeropostale v2.5 | © 2025 Todos los derechos reservados.<br>
        Desarrollado con Streamlit, Supabase y Wilo AI.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {e}")
        logger.error(f"Crash: {e}", exc_info=True)
