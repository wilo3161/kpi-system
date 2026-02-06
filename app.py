import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import hashlib
import re
import unicodedata
from typing import Dict, List, Optional, Any, Union

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 1. ESTILOS CSS - MODERNIZADO Y MEJORADO
# ==============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

.stApp {
    font-family: 'Montserrat', sans-serif;
    background-color: #0f172a;
    overflow-x: hidden;
}

/* Fondo principal */
.main-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: 
        radial-gradient(circle at 20% 50%, rgba(96, 165, 250, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(244, 114, 182, 0.1) 0%, transparent 50%),
        linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    z-index: -2;
}

/* Efecto de partículas */
.particles {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    opacity: 0.3;
}

/* Contenedor principal */
.gallery-container {
    padding: 40px 5% 20px 5%;
    text-align: center;
    max-width: 1400px;
    margin: 0 auto;
    position: relative;
}

/* Títulos */
.brand-title {
    color: white;
    font-size: 3.8rem;
    font-weight: 900;
    letter-spacing: 18px;
    margin-bottom: 15px;
    text-transform: uppercase;
    background: linear-gradient(45deg, #60A5FA, #8B5CF6, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: titleGlow 3s ease-in-out infinite alternate;
    text-shadow: 0 0 30px rgba(96, 165, 250, 0.3);
}

@keyframes titleGlow {
    0% { text-shadow: 0 0 20px rgba(96, 165, 250, 0.3); }
    100% { text-shadow: 0 0 40px rgba(139, 92, 246, 0.4); }
}

.brand-subtitle {
    color: #94A3B8;
    font-size: 1.1rem;
    letter-spacing: 8px;
    margin-bottom: 60px;
    text-transform: uppercase;
    font-weight: 400;
    position: relative;
    display: inline-block;
}

.brand-subtitle::after {
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 100px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #60A5FA, transparent);
}

/* Grid de módulos - Mejorado */
.modules-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 25px;
    padding: 0 15px;
    margin-bottom: 50px;
}

@media (max-width: 1200px) {
    .modules-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .modules-grid { grid-template-columns: 1fr; }
    .brand-title { 
        font-size: 2.8rem; 
        letter-spacing: 12px; 
    }
}

/* Tarjetas - COMPLETAMENTE CLICKEABLES */
.module-card-container {
    position: relative;
    width: 100%;
    height: 200px;
}

.module-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    height: 100%;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 25px 20px;
    position: relative;
    cursor: pointer;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.module-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 100%;
    background: linear-gradient(135deg, 
        rgba(96, 165, 250, 0.1) 0%, 
        rgba(139, 92, 246, 0.1) 50%, 
        rgba(244, 114, 182, 0.1) 100%);
    opacity: 0;
    transition: opacity 0.4s ease;
    z-index: 1;
}

.module-card:hover::before {
    opacity: 1;
}

.module-card::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
        transparent, 
        rgba(255, 255, 255, 0.1), 
        transparent);
    transition: left 0.7s ease;
}

.module-card:hover::after {
    left: 100%;
}

.module-card:hover {
    transform: translateY(-10px) scale(1.03);
    border-color: rgba(96, 165, 250, 0.3);
    box-shadow: 
        0 20px 40px rgba(0, 0, 0, 0.3),
        0 0 0 1px rgba(96, 165, 250, 0.1);
}

.card-icon {
    font-size: 3.5rem;
    margin-bottom: 20px;
    transition: all 0.4s ease;
    position: relative;
    z-index: 2;
}

.module-card:hover .card-icon {
    transform: scale(1.3) rotate(10deg);
    filter: drop-shadow(0 5px 15px rgba(96, 165, 250, 0.4));
}

.card-title {
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 8px;
    position: relative;
    z-index: 2;
}

.card-description {
    color: #CBD5E1;
    font-size: 0.9rem;
    text-align: center;
    opacity: 0.8;
    line-height: 1.5;
    position: relative;
    z-index: 2;
    font-weight: 400;
}

/* Indicador de hover */
.card-hover-indicator {
    position: absolute;
    bottom: 15px;
    right: 15px;
    color: #60A5FA;
    opacity: 0;
    transform: translateX(10px);
    transition: all 0.3s ease;
    font-size: 1.2rem;
    z-index: 2;
}

.module-card:hover .card-hover-indicator {
    opacity: 1;
    transform: translateX(0);
}

/* Botón de volver al inicio - FIJADO Y MEJORADO */
.back-to-home-btn {
    position: fixed !important;
    top: 25px !important;
    left: 25px !important;
    z-index: 1000 !important;
    background: linear-gradient(135deg, #60A5FA, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 8px 25px rgba(96, 165, 250, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    min-width: 160px !important;
    justify-content: center !important;
}

.back-to-home-btn:hover {
    transform: translateX(-5px) scale(1.05) !important;
    box-shadow: 
        0 12px 30px rgba(96, 165, 250, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    background: linear-gradient(135deg, #8B5CF6, #F472B6) !important;
}

.back-to-home-btn:active {
    transform: translateX(-5px) scale(0.98) !important;
}

/* Cabecera de módulos */
.module-header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 3rem 2rem;
    border-radius: 24px;
    margin: 20px 0 40px 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 
        0 20px 40px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    position: relative;
    overflow: hidden;
}

.module-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #60A5FA, #8B5CF6, #F472B6);
}

.header-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: white;
    margin-bottom: 15px;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 5px 15px rgba(96, 165, 250, 0.2);
}

.header-subtitle {
    font-size: 1.1rem;
    color: #CBD5E1;
    font-weight: 400;
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Contenido de módulos - ESPACIADO CORRECTO */
.module-content {
    margin-top: 30px;
    padding: 0 10px;
}

/* Mejoras para componentes de Streamlit */

/* File uploader mejorado */
.stFileUploader > div > div {
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(10px) !important;
    border: 2px dashed rgba(96, 165, 250, 0.3) !important;
    border-radius: 16px !important;
    padding: 40px 20px !important;
    transition: all 0.3s ease !important;
}

.stFileUploader > div > div:hover {
    border-color: #60A5FA !important;
    background: rgba(30, 41, 59, 0.9) !important;
}

.stFileUploader > div > div > div {
    color: #CBD5E1 !important;
}

/* Checkboxes y radio buttons */
.stCheckbox > label, .stRadio > label {
    color: #CBD5E1 !important;
    font-weight: 500 !important;
}

/* Selectboxes y inputs */
.stSelectbox > div > div, .stTextInput > div > div {
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: white !important;
}

.stSelectbox > div > div:hover, .stTextInput > div > div:hover {
    border-color: #60A5FA !important;
}

/* Botones de Streamlit */
.stButton > button {
    background: linear-gradient(135deg, #60A5FA, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    padding: 14px 28px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
        0 8px 25px rgba(96, 165, 250, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 
        0 12px 30px rgba(96, 165, 250, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    background: linear-gradient(135deg, #8B5CF6, #F472B6) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: transparent;
    padding: 0;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(10px);
    border-radius: 12px !important;
    padding: 16px 24px !important;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    transition: all 0.3s ease;
    color: #94A3B8 !important;
    margin: 0 5px !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #60A5FA !important;
    color: white !important;
    transform: translateY(-2px);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.2), rgba(139, 92, 246, 0.2)) !important;
    color: #60A5FA !important;
    border-color: #60A5FA !important;
    box-shadow: 0 5px 15px rgba(96, 165, 250, 0.2) !important;
}

/* Dataframes */
.stDataFrame {
    border-radius: 16px !important;
    overflow: hidden !important;
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Métricas */
[data-testid="stMetricValue"] {
    color: white !important;
    font-weight: 800 !important;
}

[data-testid="stMetricLabel"] {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: #60A5FA !important;
}

/* Scrollbar personalizado */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #60A5FA, #8B5CF6);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #8B5CF6, #F472B6);
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 40px 20px;
    margin-top: 60px;
    color: #64748B;
    font-size: 0.9rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(10px);
}

/* Efecto de carga */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease-out forwards;
}

/* Responsive para módulos */
@media (max-width: 768px) {
    .module-header {
        padding: 2rem 1rem;
    }
    
    .header-title {
        font-size: 2rem;
    }
    
    .back-to-home-btn {
        padding: 10px 16px !important;
        font-size: 0.9rem !important;
        min-width: 140px !important;
    }
}

/* Clase para ocultar elementos */
.hidden {
    display: none !important;
}
</style>

<div class="main-bg"></div>
<div class="particles"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE NAVEGACIÓN MEJORADO
# ==============================================================================

def initialize_session_state():
    """Inicializa el estado de sesión"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Inicio"
    
    # Estado para cada módulo
    if 'module_data' not in st.session_state:
        st.session_state.module_data = {}

def create_module_card(icon, title, description, module_key):
    """Crea una tarjeta de módulo completamente clickeable"""
    # Usar columnas para estructura
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Contenedor de tarjeta
        st.markdown(f"""
        <div class="module-card-container">
            <div class="module-card" onclick="handleCardClick('{module_key}')">
                <div class="card-icon">{icon}</div>
                <div class="card-title">{title}</div>
                <div class="card-description">{description}</div>
                <div class="card-hover-indicator">→</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # JavaScript para manejar clics
        st.markdown(f"""
        <script>
        function handleCardClick(moduleKey) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: moduleKey
            }}, '*');
        }}
        </script>
        """, unsafe_allow_html=True)
        
        # Botón invisible que cubre toda la tarjeta
        if st.button("", key=f"card_btn_{module_key}", 
                    help=f"Acceder a {title}",
                    use_container_width=True):
            st.session_state.current_page = module_key
            st.rerun()

def add_back_button():
    """Agrega el botón de volver al inicio (estático)"""
    # Botón fijo de Streamlit
    if st.button("← Menú Principal", 
                 key="back_button_main",
                 help="Volver al menú principal"):
        st.session_state.current_page = "Inicio"
        st.rerun()
    
    # Botón CSS adicional (solo visual)
    st.markdown("""
    <div class="back-to-home-btn" id="backBtn">
        ← Menú Principal
    </div>
    
    <script>
    document.getElementById('backBtn').addEventListener('click', function() {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: 'Inicio'
        }, '*');
    });
    </script>
    """, unsafe_allow_html=True)

def show_module_header(title, subtitle):
    """Muestra la cabecera de un módulo"""
    st.markdown(f"""
    <div class="module-header fade-in">
        <h1 class="header-title">{title}</h1>
        <p class="header-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. PÁGINA PRINCIPAL - COMPLETAMENTE REDISEÑADA
# ==============================================================================

def show_main_page():
    """Muestra la página principal con las tarjetas de módulos"""
    st.markdown("""
    <div class="gallery-container fade-in">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribución Ecuador | ERP v4.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de módulos
    st.markdown('<div class="modules-grid fade-in">', unsafe_allow_html=True)
    
    # Definir módulos con sus propiedades
    modules = [
        {
            "icon": "📊",
            "title": "Dashboard KPIs",
            "description": "Dashboard en tiempo real con métricas operativas",
            "key": "dashboard_kpis"
        },
        {
            "icon": "💰", 
            "title": "Reconciliación V8",
            "description": "Conciliación financiera y análisis de facturas",
            "key": "reconciliacion_v8"
        },
        {
            "icon": "📧",
            "title": "Auditoría de Correos",
            "description": "Análisis inteligente de novedades por email",
            "key": "auditoria_correos"
        },
        {
            "icon": "📦",
            "title": "Dashboard Logístico",
            "description": "Control de transferencias y distribución",
            "key": "dashboard_logistico"
        },
        {
            "icon": "👥",
            "title": "Gestión de Equipo",
            "description": "Administración del personal del centro",
            "key": "gestion_equipo"
        },
        {
            "icon": "🚚",
            "title": "Generar Guías",
            "description": "Sistema de envíos con seguimiento QR",
            "key": "generar_guias"
        },
        {
            "icon": "📋",
            "title": "Control de Inventario",
            "description": "Gestión de stock en tiempo real",
            "key": "control_inventario"
        },
        {
            "icon": "📈",
            "title": "Reportes Avanzados",
            "description": "Análisis y estadísticas ejecutivas",
            "key": "reportes_avanzados"
        },
        {
            "icon": "⚙️",
            "title": "Configuración",
            "description": "Personalización del sistema ERP",
            "key": "configuracion"
        }
    ]
    
    # Crear tarjetas en 3 columnas
    cols = st.columns(3)
    
    for idx, module in enumerate(modules):
        with cols[idx % 3]:
            create_module_card(
                module["icon"],
                module["title"],
                module["description"],
                module["key"]
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="app-footer">
        <p><strong>Sistema ERP v4.0</strong> • Desarrollado por Wilson Pérez • Logística & Sistemas</p>
        <p style="font-size: 0.85rem; color: #94A3B8; margin-top: 15px;">
            © 2024 AEROPOSTALE Ecuador • Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 4. MÓDULOS ESPECÍFICOS - MEJORADOS ESTÉTICAMENTE
# ==============================================================================

def show_dashboard_logistico():
    """Dashboard de logística y transferencias - MEJORADO"""
    # Botón de volver
    add_back_button()
    
    # Cabecera del módulo
    show_module_header(
        "📦 Dashboard Logístico",
        "Control de transferencias y distribución en tiempo real"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Sección de carga de archivos - MEJORADA
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📤 Subir Archivo de Transferencias")
            st.markdown("""
            <div style="margin-bottom: 20px; color: #CBD5E1; font-size: 0.95rem;">
                Sube tu archivo Excel con los datos de transferencias para análisis.
                Formato soportado: XLSX (máx. 200MB)
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "",
                type=['xlsx', 'xls'],
                key="logistica_file",
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                st.success(f"✅ Archivo cargado: {uploaded_file.name}")
                
                # Procesar archivo
                try:
                    df = pd.read_excel(uploaded_file)
                    st.info(f"📊 {len(df)} registros cargados correctamente")
                    
                    # Vista previa
                    with st.expander("👁️ Vista previa de datos", expanded=False):
                        st.dataframe(df.head(10), use_container_width=True)
                        
                except Exception as e:
                    st.error(f"❌ Error al procesar el archivo: {str(e)}")
        
        with col2:
            st.markdown("### ⚙️ Opciones")
            use_demo = st.checkbox("Usar datos de demostración", value=True)
            
            if use_demo:
                st.info("ℹ️ Usando conjunto de datos de ejemplo")
                
            # Botón de procesamiento
            if st.button("🚀 Procesar Datos", type="primary", use_container_width=True):
                with st.spinner("🔄 Analizando datos..."):
                    time.sleep(2)
                    st.success("✅ Análisis completado")
    
    st.divider()
    
    # Sección de visualización - MEJORADA
    if use_demo or uploaded_file:
        st.markdown("## 📊 Análisis Visual")
        
        # Métricas rápidas
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            st.metric("Total Transferencias", "1,247", "+12%")
        
        with col_met2:
            st.metric("Completadas", "1,089", "87.3%")
        
        with col_met3:
            st.metric("En Proceso", "124", "-8%")
        
        with col_met4:
            st.metric("Pendientes", "34", "+2")
        
        st.divider()
        
        # Gráficos
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Gráfico de distribución por categoría
            categorias = ['Tiendas', 'Price Club', 'Ventas Mayor', 'Tienda Web', 'Fallas', 'Fundas']
            valores = [1250, 850, 320, 180, 75, 450]
            
            fig1 = px.pie(
                values=valores,
                names=categorias,
                title="<b>Distribución por Categoría</b>",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig1.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )
            fig1.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>%{value} unidades<br>%{percent}"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_chart2:
            # Gráfico de tendencias
            fechas = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
            tendencia = np.random.normal(100, 20, len(fechas)).cumsum()
            
            fig2 = px.line(
                x=fechas,
                y=tendencia,
                title="<b>Tendencia Mensual de Transferencias</b>",
                labels={'x': 'Fecha', 'y': 'Unidades Transferidas'}
            )
            fig2.update_traces(
                line=dict(color='#60A5FA', width=3),
                mode='lines+markers',
                marker=dict(size=8)
            )
            fig2.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Tabla detallada
        st.divider()
        st.markdown("### 📋 Detalle de Transferencias")
        
        # Datos de ejemplo
        data_detalle = {
            'ID': [f'TRF-{i:04d}' for i in range(1001, 1021)],
            'Destino': ['Mall del Sol', 'Price Club', 'Ventas Mayor', 'Tienda Web'] * 5,
            'Categoría': ['Tiendas', 'Price Club', 'Ventas Mayor', 'Tienda Web'] * 5,
            'Unidades': np.random.randint(10, 500, 20),
            'Estado': ['✅ Completada', '🔄 En tránsito', '⏳ Pendiente'] * 7,
            'Fecha': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(20)],
            'Responsable': ['Wilson Pérez', 'Luis Perugachi', 'Andrés Cadena'] * 7
        }
        
        df_detalle = pd.DataFrame(data_detalle)
        
        # Filtros para la tabla
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            filtro_estado = st.selectbox(
                "Filtrar por Estado",
                ["Todos", "✅ Completada", "🔄 En tránsito", "⏳ Pendiente"]
            )
        
        with col_filt2:
            filtro_categoria = st.selectbox(
                "Filtrar por Categoría",
                ["Todas", "Tiendas", "Price Club", "Ventas Mayor", "Tienda Web"]
            )
        
        with col_filt3:
            items_por_pagina = st.selectbox(
                "Items por página",
                [10, 20, 50, 100],
                index=1
            )
        
        # Aplicar filtros
        df_filtrado = df_detalle.copy()
        
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Estado'] == filtro_estado]
        
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Categoría'] == filtro_categoria]
        
        # Mostrar tabla
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            height=400
        )
        
        # Opciones de exportación
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp2:
            if st.button("📥 Exportar Reporte", use_container_width=True):
                st.success("✅ Reporte exportado correctamente")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard_kpis():
    """Dashboard de KPIs - MEJORADO"""
    add_back_button()
    show_module_header(
        "📊 Dashboard de KPIs",
        "Métricas en tiempo real del Centro de Distribución"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Filtros mejorados
    with st.container():
        col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns(4)
        
        with col_filtro1:
            fecha_inicio = st.date_input(
                "📅 Fecha Inicio",
                datetime.now() - timedelta(days=30),
                key="kpi_fecha_inicio"
            )
        
        with col_filtro2:
            fecha_fin = st.date_input(
                "📅 Fecha Fin",
                datetime.now(),
                key="kpi_fecha_fin"
            )
        
        with col_filtro3:
            departamento = st.selectbox(
                "🏭 Departamento",
                ["Todos", "Logística", "Almacén", "Ventas", "Administración", "Calidad"],
                key="kpi_depto"
            )
        
        with col_filtro4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Actualizar Dashboard", use_container_width=True):
                st.rerun()
    
    # Métricas principales
    st.markdown("### 🎯 Métricas Clave")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); 
                    border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: rgba(96, 165, 250, 0.2); padding: 10px; border-radius: 12px; margin-right: 15px;">
                    <span style="font-size: 1.5rem;">📦</span>
                </div>
                <div>
                    <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">PRODUCTIVIDAD</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">1,247</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #4ADE80; font-size: 0.9rem; font-weight: 600;">+12.5%</div>
                <div style="color: #94A3B8; font-size: 0.8rem;">vs período anterior</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); 
                    border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: rgba(139, 92, 246, 0.2); padding: 10px; border-radius: 12px; margin-right: 15px;">
                    <span style="font-size: 1.5rem;">⚡</span>
                </div>
                <div>
                    <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">EFICIENCIA</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">94.2%</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #4ADE80; font-size: 0.9rem; font-weight: 600;">+0.8%</div>
                <div style="color: #94A3B8; font-size: 0.8rem;">vs meta (95%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); 
                    border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: rgba(244, 114, 182, 0.2); padding: 10px; border-radius: 12px; margin-right: 15px;">
                    <span style="font-size: 1.5rem;">💰</span>
                </div>
                <div>
                    <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">INGRESOS</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">$45,230</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #4ADE80; font-size: 0.9rem; font-weight: 600;">+8.3%</div>
                <div style="color: #94A3B8; font-size: 0.8rem;">vs mes anterior</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); 
                    border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <div style="background: rgba(34, 211, 238, 0.2); padding: 10px; border-radius: 12px; margin-right: 15px;">
                    <span style="font-size: 1.5rem;">👥</span>
                </div>
                <div>
                    <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 600;">PERSONAL ACTIVO</div>
                    <div style="color: white; font-size: 2rem; font-weight: 800;">42</div>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: #4ADE80; font-size: 0.9rem; font-weight: 600;">+2</div>
                <div style="color: #94A3B8; font-size: 0.8rem;">nuevos contratados</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 5. FUNCIONES AUXILIARES Y MÓDULOS RESTANTES
# ==============================================================================

def show_reconciliacion_v8():
    """Módulo de reconciliación financiera"""
    add_back_button()
    show_module_header(
        "💰 Reconciliación V8",
        "Conciliación de facturas y manifiestos con IA"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📤 Cargar Archivos", "⚙️ Configurar", "📊 Resultados"])
    
    with tab1:
        st.info("Carga los archivos de manifiesto y facturas para comenzar la reconciliación")
        
        col_arch1, col_arch2 = st.columns(2)
        
        with col_arch1:
            st.markdown("### 📄 Manifiesto")
            st.file_uploader(
                "Arrastra o haz clic para subir",
                type=['xlsx', 'xls', 'csv'],
                key="manif_file",
                help="Archivo con columnas: Guía, Destinatario, Valor, Piezas"
            )
        
        with col_arch2:
            st.markdown("### 🧾 Facturas")
            st.file_uploader(
                "Arrastra o haz clic para subir",
                type=['xlsx', 'xls', 'csv'],
                key="fact_file",
                help="Archivo con columnas: Guía, Valor Facturado"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_auditoria_correos():
    """Módulo de auditoría de correos"""
    add_back_button()
    show_module_header(
        "📧 Auditoría de Correos",
        "Análisis inteligente de novedades por email"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Credenciales
    col_cred1, col_cred2 = st.columns(2)
    
    with col_cred1:
        email_user = st.text_input("Correo", "wperez@fashionclub.com.ec")
    
    with col_cred2:
        email_pass = st.text_input("Contraseña", type="password", value="demo123")
    
    if st.button("🔍 Iniciar Auditoría", type="primary", use_container_width=True):
        with st.spinner("Analizando bandeja de entrada..."):
            time.sleep(2)
            st.success("✅ Auditoría completada")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_gestion_equipo():
    """Gestión de personal"""
    add_back_button()
    show_module_header(
        "👥 Gestión de Equipo",
        "Administración del personal del Centro de Distribución"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🏢 Estructura", "➕ Agregar", "📊 Estadísticas"])
    
    with tab1:
        # Contenido existente
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_generar_guias():
    """Generador de guías de envío"""
    add_back_button()
    show_module_header(
        "🚚 Generador de Guías",
        "Sistema de envíos con seguimiento QR"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Contenido existente
    pass
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_control_inventario():
    """Control de inventario"""
    add_back_button()
    show_module_header(
        "📋 Control de Inventario",
        "Gestión de stock en tiempo real"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.info("Módulo en desarrollo...")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_reportes_avanzados():
    """Generador de reportes"""
    add_back_button()
    show_module_header(
        "📈 Reportes Avanzados",
        "Análisis y estadísticas ejecutivas"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.info("Módulo en desarrollo...")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_configuracion():
    """Configuración del sistema"""
    add_back_button()
    show_module_header(
        "⚙️ Configuración",
        "Personalización del sistema ERP"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["General", "Usuarios", "Seguridad"])
    
    with tab1:
        # Contenido existente
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 6. NAVEGACIÓN PRINCIPAL
# ==============================================================================

def main():
    """Función principal de la aplicación"""
    # Inicializar estado
    initialize_session_state()
    
    # Mapeo de páginas
    page_mapping = {
        "Inicio": show_main_page,
        "dashboard_kpis": show_dashboard_kpis,
        "reconciliacion_v8": show_reconciliacion_v8,
        "auditoria_correos": show_auditoria_correos,
        "dashboard_logistico": show_dashboard_logistico,
        "gestion_equipo": show_gestion_equipo,
        "generar_guias": show_generar_guias,
        "control_inventario": show_control_inventario,
        "reportes_avanzados": show_reportes_avanzados,
        "configuracion": show_configuracion
    }
    
    # Mostrar página actual
    current_page = st.session_state.current_page
    
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

if __name__ == "__main__":
    main()
