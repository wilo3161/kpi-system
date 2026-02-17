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
import io
import json
import qrcode
import requests
import imaplib
import email
from email.header import decode_header
from typing import Dict, List, Optional, Any, Union
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor

# --- CONFIGURACION DE PAGINA ---
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

/* Efecto de particulas */
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

/* Titulos */
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

/* Grid de modulos - Mejorado */
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

/* Tarjetas - COMPLETAMENTE CLICKEABLES CON ANCHOR */
.module-card-container {
    position: relative;
    width: 100%;
    height: 200px;
    text-decoration: none !important;
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

/* Boton de volver al inicio - FIJADO Y MEJORADO */
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

/* Cabecera de modulos */
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
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 15px;
}

.header-icon {
    display: inline-block;
    font-size: 2.8rem;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 5px 15px rgba(96, 165, 250, 0.3));
    text-shadow: 0 0 20px rgba(96, 165, 250, 0.4);
}

.header-text {
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

/* Asegurar que los iconos sean visibles en todos los contextos */
.module-header h1 .header-icon {
    opacity: 1 !important;
    visibility: visible !important;
}

/* Para los emojis en titulos */
.module-header h1 span:first-child {
    text-shadow: 0 0 20px rgba(96, 165, 250, 0.4);
}

/* Responsive para iconos */
@media (max-width: 768px) {
    .header-title {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }
    
    .header-icon {
        font-size: 2.5rem;
    }
    
    .header-text {
        font-size: 2.2rem;
    }
}

/* Contenido de modulos - ESPACIADO CORRECTO */
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

/* Metricas */
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

/* Responsive para modulos */
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

/* Estilos adicionales para tarjetas de metricas */
.stat-card {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-5px);
    border-color: #60A5FA;
    box-shadow: 0 10px 25px rgba(96, 165, 250, 0.2);
}

.card-blue {
    border-left: 4px solid #60A5FA;
}

.card-green {
    border-left: 4px solid #10B981;
}

.card-red {
    border-left: 4px solid #EF4444;
}

.card-purple {
    border-left: 4px solid #8B5CF6;
}

.card-orange {
    border-left: 4px solid #F59E0B;
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: 10px;
}

.stat-title {
    color: #CBD5E1;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.stat-value {
    color: white;
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 5px;
}

.stat-change {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 12px;
    display: inline-block;
}

.positive {
    background: rgba(16, 185, 129, 0.2);
    color: #10B981;
}

.negative {
    background: rgba(239, 68, 68, 0.2);
    color: #EF4444;
}

.warning {
    background: rgba(245, 158, 11, 0.2);
    color: #F59E0B;
}

/* Contenedor de graficos */
.chart-container {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
}

/* Panel de filtros */
.filter-panel {
    background: rgba(30, 41, 59, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
}

.filter-title {
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 15px;
}

/* Grid de estadisticas */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 30px;
}

@media (max-width: 1200px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .stats-grid { grid-template-columns: 1fr; }
}

/* Tarjetas de metricas alternativas */
.metric-card {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 12px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 10px;
}

.metric-title {
    color: #94A3B8;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
    margin: 5px 0;
}

.metric-subtitle {
    color: #64748B;
    font-size: 0.75rem;
}

/* Encabezados principales */
.main-header {
    text-align: center;
    padding: 30px 0;
    margin-bottom: 30px;
}

.header-title {
    color: white;
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 10px;
}

.header-subtitle {
    color: #94A3B8;
    font-size: 1.1rem;
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
}

.section-description {
    color: #94A3B8;
    font-size: 0.9rem;
    margin-top: 5px;
}

/* CORRECCION: Estilos para tarjetas clickeables nativas de Streamlit */
div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:has(button[kind="secondary"]) {
    cursor: pointer;
}

/* Ocultar el boton real pero mantener el area clickeable */
.module-clickable-area {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10;
    opacity: 0;
    cursor: pointer;
}

/* Estilo para el contenedor de la tarjeta clickeable */
.card-clickable-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    text-decoration: none;
}

/* Asegurar que todo el contenido de la tarjeta sea clickeable */
.card-clickable-wrapper * {
    pointer-events: none;
}

.card-clickable-wrapper .stButton {
    pointer-events: auto;
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    z-index: 100;
}

.card-clickable-wrapper button {
    width: 100% !important;
    height: 100% !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    opacity: 0 !important;
    cursor: pointer !important;
    z-index: 100 !important;
}
</style>

<div class="main-bg"></div>
<div class="particles"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEMA DE NAVEGACION MEJORADO
# ==============================================================================

def initialize_session_state():
    """Inicializa el estado de sesion"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Inicio"
    
    # Estado para cada modulo
    if 'module_data' not in st.session_state:
        st.session_state.module_data = {}
    
    # Para el generador de guias
    if 'guias_registradas' not in st.session_state:
        st.session_state.guias_registradas = []
    if 'contador_guias' not in st.session_state:
        st.session_state.contador_guias = 1000
    if 'qr_images' not in st.session_state:
        st.session_state.qr_images = {}
    if 'logos' not in st.session_state:
        st.session_state.logos = {}

# CORRECCION: Nueva funcion para manejar el clic en tarjetas
def navigate_to_module(module_key):
    """Navega al modulo seleccionado"""
    st.session_state.current_page = module_key
    st.rerun()

# CORRECCION: Funcion mejorada para crear tarjetas completamente clickeables
def create_module_card(icon, title, description, module_key):
    """Crea una tarjeta de modulo completamente clickeable usando st.button nativo"""
    # Crear un contenedor para la tarjeta
    card_container = st.container()
    
    with card_container:
        # Usar columns para centrar la tarjeta
        col1, col2, col3 = st.columns([1, 10, 1])
        
        with col2:
            # Crear el HTML de la tarjeta
            card_html = f"""
            <div class="module-card-container">
                <div class="module-card">
                    <div class="card-icon">{icon}</div>
                    <div class="card-title">{title}</div>
                    <div class="card-description">{description}</div>
                    <div class="card-hover-indicator">→</div>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # CORRECCION: Usar st.button con use_container_width=True para cubrir toda el area
            # El truco es usar un boton invisible que ocupe todo el espacio de la tarjeta
            # mediante CSS personalizado
            st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(2) button) {
                position: relative;
            }
            div[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(2) button) button {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 200px;
                opacity: 0;
                cursor: pointer;
                z-index: 1000;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Boton invisible que cubre toda la tarjeta
            if st.button(
                " ", 
                key=f"card_btn_{module_key}", 
                help=f"Acceder a {title}",
                use_container_width=True,
                type="secondary"
            ):
                navigate_to_module(module_key)

def add_back_button():
    """Agrega el boton de volver al inicio (estatico)"""
    # Boton fijo de Streamlit
    if st.button("← Menu Principal", 
                 key="back_button_main",
                 help="Volver al menu principal",
                 type="primary"):
        st.session_state.current_page = "Inicio"
        st.rerun()
    
    # Boton CSS adicional (solo visual)
    st.markdown("""
    <div class="back-to-home-btn" id="backBtn">
        ← Menu Principal
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

def show_module_header(title_with_icon, subtitle):
    """Muestra la cabecera de un modulo con icono visible"""
    # Separar el icono (primer caracter) del texto del titulo
    if title_with_icon and len(title_with_icon) > 0:
        # El icono es el primer caracter (los emojis son 1-2 caracteres)
        icon = title_with_icon[0]
        title_text = title_with_icon[1:].strip()
    else:
        icon = ""
        title_text = title_with_icon
    
    st.markdown(f"""
    <div class="module-header fade-in">
        <h1 class="header-title">
            <span class="header-icon">{icon}</span>
            <span class="header-text">{title_text}</span>
        </h1>
        <p class="header-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. FUNCIONES AUXILIARES
# ==============================================================================

def hash_password(password):
    """Hashea una contrasena"""
    return hashlib.sha256(password.encode()).hexdigest()

def normalizar_texto_wilo(texto):
    """Normaliza texto para comparaciones"""
    if pd.isna(texto):
        return ""
    # Convertir a mayusculas y eliminar acentos
    texto = str(texto).upper()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii')
    return texto

def procesar_subtotal_wilo(valor):
    """Procesa valores numericos"""
    try:
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, str):
            # Eliminar simbolos de moneda y separadores de miles
            valor = valor.replace('$', '').replace(',', '')
        return float(valor)
    except:
        return 0.0

def to_excel(df):
    """Convierte DataFrame a Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

def normalizar_codigo(df, columnas_posibles):
    """Normaliza la columna de codigo a string y elimina espacios"""
    for col in columnas_posibles:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            return df, col
    return df, None

def extraer_entero(valor):
    """Extrae valor entero de diferentes formatos"""
    try:
        if pd.isna(valor): return 0
        if isinstance(valor, str):
            valor = valor.replace('.', '')
            if ',' in valor: valor = valor.split(',')[0]
        val = float(valor)
        if val >= 1000000: return int(val // 1000000)
        return int(val)
    except:
        return 0

# ==============================================================================
# 4. SIMULACION DE BASE DE DATOS LOCAL
# ==============================================================================

class LocalDatabase:
    """Simulacion de base de datos local para reemplazar Supabase"""
    
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
                {'id': 1, 'nombre': 'Andres Yepez', 'cargo': 'Supervisor', 'estado': 'Activo'},
                {'id': 2, 'nombre': 'Josue Imbacuan', 'cargo': 'Operador', 'estado': 'Activo'},
                {'id': 3, 'nombre': 'Maria Gonzalez', 'cargo': 'Auditora', 'estado': 'Activo'}
            ],
            'distribuciones': [
                {'id': 1, 'transporte': 'Tempo', 'guias': 45, 'estado': 'En ruta'},
                {'id': 2, 'transporte': 'Luis Perugachi', 'guias': 32, 'estado': 'Entregado'}
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
        """Simula insercion de datos"""
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
    
    def delete(self, table, id):
        """Elimina un registro por ID"""
        if table in self.data:
            self.data[table] = [item for item in self.data[table] if item.get('id') != id]
        return True
    
    def authenticate(self, username, password):
        """Autenticacion local"""
        users = self.query('users', {'username': username})
        if not users:
            return None
        
        user = users[0]
        if user['password_hash'] == hash_password(password):
            return user
        return None

# Instancia global de base de datos local
local_db = LocalDatabase()

# ==============================================================================
# 5. PAGINA PRINCIPAL - COMPLETAMENTE REDISENADA
# ==============================================================================

def show_main_page():
    """Muestra la pagina principal con las tarjetas de modulos"""
    st.markdown("""
    <div class="gallery-container fade-in">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribucion Ecuador | ERP v4.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de modulos
    st.markdown('<div class="modules-grid fade-in">', unsafe_allow_html=True)
    
    # Definir modulos con sus propiedades
    modules = [
        {
            "icon": "📊",
            "title": "Dashboard KPIs",
            "description": "Dashboard en tiempo real con metricas operativas",
            "key": "dashboard_kpis"
        },
        {
            "icon": "💰", 
            "title": "Reconciliacion V8",
            "description": "Conciliacion financiera y analisis de facturas",
            "key": "reconciliacion_v8"
        },
        {
            "icon": "📧",
            "title": "Auditoria de Correos",
            "description": "Analisis inteligente de novedades por email",
            "key": "auditoria_correos"
        },
        {
            "icon": "📦",
            "title": "Dashboard Logistico",
            "description": "Control de transferencias y distribucion",
            "key": "dashboard_logistico"
        },
        {
            "icon": "👥",
            "title": "Gestion de Equipo",
            "description": "Administracion del personal del centro",
            "key": "gestion_equipo"
        },
        {
            "icon": "🚚",
            "title": "Generar Guias",
            "description": "Sistema de envios con seguimiento QR",
            "key": "generar_guias"
        },
        {
            "icon": "📋",
            "title": "Control de Inventario",
            "description": "Gestion de stock en tiempo real",
            "key": "control_inventario"
        },
        {
            "icon": "📈",
            "title": "Reportes Avanzados",
            "description": "Analisis y estadisticas ejecutivas",
            "key": "reportes_avanzados"
        },
        {
            "icon": "⚙️",
            "title": "Configuracion",
            "description": "Personalizacion del sistema ERP",
            "key": "configuracion"
        }
    ]
    
    # CORRECCION: Crear tarjetas en 3 columnas usando el nuevo sistema clickeable
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
        <p><strong>Sistema ERP v4.0</strong> • Desarrollado por Wilson Perez • Logistica & Sistemas</p>
        <p style="font-size: 0.85rem; color: #94A3B8; margin-top: 15px;">
            © 2024 AEROPOSTALE Ecuador • Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 6. MODULO DASHBOARD KPIs
# ==============================================================================

def show_dashboard_kpis():
    """Dashboard de KPIs - MEJORADO"""
    add_back_button()
    show_module_header(
        "📊 Dashboard de KPIs",
        "Metricas en tiempo real del Centro de Distribucion"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", datetime.now() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col3:
        tipo_kpi = st.selectbox("📈 Tipo de Metrica", ["Produccion", "Eficiencia", "Costos", "Alertas"])
    
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
                    <div class='stat-title'>Produccion Promedio</div>
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
            
            # Graficos
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = px.line(df_filtered, x='fecha', y='produccion', 
                        title='Produccion Diaria',
                        labels={'produccion': 'Unidades', 'fecha': 'Fecha'},
                        line_shape='spline')
            fig.update_traces(line=dict(color='#0033A0', width=3))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Graficos secundarios
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
                                title='Relacion Produccion vs Costos',
                                color='alertas',
                                size='eficiencia',
                                hover_data=['fecha'])
                st.plotly_chart(fig3, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No hay datos para el rango de fechas seleccionado.")
    else:
        st.info("Cargando datos de KPIs...")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 7. MODULO DASHBOARD LOGISTICO
# ==============================================================================


# ==============================================================================
# 7. MODULO DASHBOARD LOGISTICO - VERSION 2.0 (CORREGIDA)
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import re
from typing import Dict, List, Optional, Tuple

# ==============================================================================
# CONFIGURACION Y CONSTANTES
# ==============================================================================

# Constantes de infraestructura
TIENDAS_REGULARES = 42
PRICE_CLUBS = 5
TIENDA_WEB = 1
VENTAS_POR_MAYOR = 1
FALLAS = 1

# Keywords para clasificación de destinos
PRICE_KEYWORDS = ['PRICE', 'OIL']
WEB_KEYWORDS = ['WEB', 'TIENDA MOVIL', 'MOVIL']
FALLAS_KEYWORDS = ['FALLAS']
VENTAS_MAYOR_KEYWORDS = ['MAYOR', 'MAYORISTA']

# Lista actualizada de tiendas regulares (Aeropostale)
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

# ==============================================================================
# DICCIONARIOS DE CLASIFICACION TEXTIL
# ==============================================================================

GENDER_MAP = {
    'GIRLS': 'Mujer', 'TOPMUJER': 'Mujer', 'WOMEN': 'Mujer',
    'LADIES': 'Mujer', 'FEMALE': 'Mujer', 'MUJER': 'Mujer',
    'GUYS': 'Hombre', 'MEN': 'Hombre', 'MAN': 'Hombre',
    'HOMBRE': 'Hombre', 'MALE': 'Hombre',
    'UNISEX': 'Unisex', 'KIDS': 'Niño/a', 'CHILD': 'Niño/a',
    'BOYS': 'Niño', 'GIRLSKIDS': 'Niña',
    'BABY': 'Bebé', 'INFANT': 'Bebé'
}

CATEGORY_MAP = {
    'TEES': 'Camiseta', 'TEE': 'Camiseta', 'T-SHIRT': 'Camiseta',
    'TANK': 'Camiseta sin mangas', 'TANK TOP': 'Camiseta sin mangas',
    'TOP': 'Top', 'TOPS': 'Top', 'BARE': 'Blusa', 'CORE': 'Blusa',
    'GRAPHIC': 'Camiseta estampada', 'GRAPHICS': 'Camiseta estampada',
    'POLO': 'Polo', 'POLOS': 'Polo', 'SHIRT': 'Camisa',
    'BUTTON-DOWN': 'Camisa', 'BUTTONDOWN': 'Camisa',
    'DRESS': 'Vestido', 'DRESSES': 'Vestido', 'SUNDRESS': 'Vestido',
    'PANTS': 'Pantalón', 'PANT': 'Pantalón', 'TROUSERS': 'Pantalón',
    'JEANS': 'Jeans', 'JEAN': 'Jeans', 'DENIM': 'Jeans',
    'BOOTCUT': 'Pantalón bootcut', 'SKINNY': 'Pantalón ajustado',
    'STRAIGHT': 'Pantalón recto', 'FLARE': 'Pantalón campana',
    'SHORTS': 'Short', 'SHORT': 'Short', 'BERMUDA': 'Bermuda',
    'JACKET': 'Chaqueta', 'JACKETS': 'Chaqueta', 'HOODIE': 'Sudadera',
    'SWEATSHIRT': 'Sudadera', 'SWEATER': 'Suéter', 'BLAZER': 'Blazer',
    'BVD': 'Ropa interior', 'BOXER': 'Boxer', 'BOXERS': 'Boxer',
    'UNDERWEAR': 'Ropa interior', 'BRIEF': 'Calzoncillo',
    'BELT': 'Cinturón', 'BELTS': 'Cinturón', 'HAT': 'Gorro',
    'CAP': 'Gorra', 'SOCKS': 'Medias', 'SOCK': 'Medias',
    'WOVEN': 'Tejido', 'KNIT': 'Tejido', 'KNITTED': 'Tejido',
    'SOLID': 'Sólido', 'BASIC': 'Básico', 'BASICO': 'Básico',
    'LEATHER': 'Cuero', 'SUMMER': 'Verano', 'WINTER': 'Invierno',
    'SPRING': 'Primavera', 'FALL': 'Otoño', 'AUTUMN': 'Otoño'
}

COLOR_MAP = {
    'BLACK': 'Negro', 'BLACK/DARK': 'Negro', 'DARK BLACK': 'Negro Oscuro',
    'WHITE': 'Blanco', 'WHITE/LIGHT': 'Blanco',
    'RED': 'Rojo', 'RASPBERRY': 'Frambuesa', 'EARTH RED': 'Rojo Tierra',
    'BLUE': 'Azul', 'NAVY': 'Azul Marino', 'LIGHT BLUE': 'Azul Claro',
    'GREEN': 'Verde', 'GREEN GABLES': 'Verde Gabardina',
    'YELLOW': 'Amarillo', 'GOLD': 'Dorado',
    'PINK': 'Rosa', 'HOT PINK': 'Rosa Fuerte',
    'PURPLE': 'Morado', 'VIOLET': 'Violeta',
    'ORANGE': 'Naranja', 'BROWN': 'Marrón',
    'GRAY': 'Gris', 'GREY': 'Gris', 'SILVER': 'Plateado',
    'BEIGE': 'Beige', 'KHAKI': 'Caqui',
    'BLEACH': 'Blanqueado', 'LIGHT WASH': 'Lavado Claro',
    'DARK': 'Oscuro', 'LIGHT': 'Claro',
    'MULTI': 'Multicolor', 'MULTICOLOR': 'Multicolor'
}

SIZE_HIERARCHY = [
    '3XS', '2XS', 'XS', 'XSMALL', 'S', 'SMALL',
    'M', 'MEDIUM', 'L', 'LARGE', 'XL', 'XLARGE',
    '2XL', '3XL', '4XL', 'XXLARGE', 'XXXLARGE'
]

IGNORE_WORDS = {'AERO', 'OF', 'THE', 'AND', 'IN', 'WITH', 'FOR', 'BY', 'ON', 'AT', 'TO', 'EST', 'TEES'}

WAREHOUSE_GROUPS = {
    'PRICE': 'Price Club',
    'AERO': 'Aeropostale',
    'MALL': 'Centro Comercial',
    'RIOCENTRO': 'Riocentro',
    'CONDADO': 'Condado',
    'SAN': 'San',
    'LOS': 'Los'
}

# ==============================================================================
# CLASES DE PROCESAMIENTO AVANZADO
# ==============================================================================

class TextileClassifier:
    """Clasificador inteligente para productos textiles"""
    
    def __init__(self):
        self.gender_map = GENDER_MAP
        self.category_map = CATEGORY_MAP
        self.color_map = COLOR_MAP
        self.size_hierarchy = SIZE_HIERARCHY
        self.ignore_words = IGNORE_WORDS
        
    def classify_product(self, product_name: str) -> dict:
        """Clasificación completa del producto"""
        if not product_name or not isinstance(product_name, str):
            return self._get_empty_classification()
        
        product_name = str(product_name).upper().strip()
        words = product_name.split()
        
        classification = {
            'Genero': 'Unisex',
            'Categoria': 'General',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'Única',
            'Material': '',
            'Estilo': ''
        }
        
        classification['Genero'] = self._detect_gender(words)
        category_info = self._detect_category(words)
        classification['Categoria'] = category_info['categoria']
        classification['Subcategoria'] = category_info['subcategoria']
        classification['Color'] = self._detect_color(words)
        classification['Talla'] = self._detect_size(words)
        style_info = self._detect_style(words)
        classification['Material'] = style_info['material']
        classification['Estilo'] = style_info['estilo']
        classification = self._clean_classification(classification)
        
        return classification
    
    def _detect_gender(self, words: list) -> str:
        """Detecta el género del producto"""
        for word in words:
            if word in self.gender_map:
                return self.gender_map[word]
        text = ' '.join(words)
        if any(word in text for word in ['WOMEN', 'LADIES', 'FEMALE']):
            return 'Mujer'
        elif any(word in text for word in ['MEN', 'MAN', 'MALE']):
            return 'Hombre'
        return 'Unisex'
    
    def _detect_category(self, words: list) -> dict:
        """Detecta categoría y subcategoría del producto"""
        categoria = 'General'
        subcategoria = ''
        found_categories = []
        
        for word in words:
            if word in self.category_map:
                found_categories.append(self.category_map[word])
            elif word not in self.ignore_words and len(word) > 2:
                subcategoria += word.capitalize() + ' '
        
        if found_categories:
            main_categories = ['Polo', 'Camiseta', 'Jeans', 'Pantalón', 'Vestido', 'Chaqueta']
            for cat in main_categories:
                if cat in found_categories:
                    categoria = cat
                    break
            else:
                categoria = found_categories[0]
            
            other_cats = [cat for cat in found_categories if cat != categoria]
            if other_cats:
                subcategoria = ' '.join(other_cats) + ' ' + subcategoria.strip()
        
        return {'categoria': categoria.strip(), 'subcategoria': subcategoria.strip()}
    
    def _detect_color(self, words: list) -> str:
        """Detecta el color del producto"""
        for word in words:
            if word in self.color_map:
                return self.color_map[word]
        text = ' '.join(words)
        for eng_color, esp_color in self.color_map.items():
            if eng_color in text:
                return esp_color
        return 'No Especificado'
    
    def _detect_size(self, words: list) -> str:
        """Detecta la talla del producto"""
        for size in self.size_hierarchy:
            if f' {size} ' in f' {" ".join(words)} ':
                return size
        return 'Única'
    
    def _detect_style(self, words: list) -> dict:
        """Detecta material y estilo adicional"""
        material = ''
        estilo = ''
        materials = ['COTTON', 'POLYESTER', 'DENIM', 'LEATHER', 'WOOL', 'SILK']
        for word in words:
            if word in materials:
                material = word.lower().capitalize()
                break
        
        style_keywords = {
            'GRAPHIC': 'Estampado', 'PRINTED': 'Estampado',
            'SOLID': 'Liso', 'STRIPED': 'Rayado',
            'BASIC': 'Básico', 'PREMIUM': 'Premium'
        }
        
        for word in words:
            if word in style_keywords:
                estilo = style_keywords[word]
                break
        
        return {'material': material, 'estilo': estilo}
    
    def _clean_classification(self, classification: dict) -> dict:
        """Limpia y estandariza la clasificación"""
        size_map = {
            'XSMALL': 'XS', 'SMALL': 'S', 'MEDIUM': 'M',
            'LARGE': 'L', 'XLARGE': 'XL', 'XXLARGE': '2XL'
        }
        
        if classification['Talla'] in size_map:
            classification['Talla'] = size_map[classification['Talla']]
        
        for key, value in classification.items():
            if isinstance(value, str):
                classification[key] = value.strip()
        
        return classification
    
    def _get_empty_classification(self) -> dict:
        """Retorna clasificación vacía"""
        return {
            'Genero': 'No Identificado',
            'Categoria': 'No Identificado',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'No Especificado',
            'Material': '',
            'Estilo': ''
        }


class TransitDataProcessor:
    """Procesador para datos de tránsito con clasificación textil (ahora con un solo archivo)"""
    
    def __init__(self):
        self.classifier = TextileClassifier()
    
    def process_transit_file(self, file) -> pd.DataFrame:
        """Procesa archivo de tránsito con clasificación inteligente (sin base)"""
        try:
            # Leer archivo
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            
            if df.empty:
                st.error("❌ El archivo está vacío")
                return pd.DataFrame()
            
            # Normalizar nombres de columnas a mayúsculas para facilitar detección
            df.columns = [str(col).strip().upper() for col in df.columns]
            
            # Detectar columnas automáticamente
            col_mapping = self._detect_columns(df)
            
            if not col_mapping['codigo']:
                st.error("❌ No se encontró columna de código de producto")
                return pd.DataFrame()
            
            if not col_mapping['cantidad']:
                st.error("❌ No se encontró columna de cantidad")
                return pd.DataFrame()
            
            # Renombrar columnas estándar
            rename_dict = {}
            if col_mapping['codigo']:
                rename_dict[col_mapping['codigo']] = 'CODIGO'
            if col_mapping['cantidad']:
                rename_dict[col_mapping['cantidad']] = 'CANTIDAD'
            if col_mapping.get('producto'):
                rename_dict[col_mapping['producto']] = 'PRODUCTO'
            if col_mapping.get('bodega'):
                rename_dict[col_mapping['bodega']] = 'BODEGA'
            
            df = df.rename(columns=rename_dict)
            
            # Limpiar código
            df['CODIGO'] = df['CODIGO'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
            # Procesar cantidad
            df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(0)
            
            # Si no hay columna de producto, usar el código como producto
            if 'PRODUCTO' not in df.columns:
                df['PRODUCTO'] = df['CODIGO']
            
            # Aplicar clasificación textil
            df = self._apply_textile_classification(df)
            
            # Agrupar bodega si existe
            if 'BODEGA' in df.columns:
                df['GRUPO_BODEGA'] = df['BODEGA'].apply(self._group_warehouse)
            else:
                df['GRUPO_BODEGA'] = 'Sin Especificar'
            
            st.success(f"✅ Archivo procesado: {len(df)} registros clasificados")
            return df
            
        except Exception as e:
            st.error(f"❌ Error al procesar archivo: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return pd.DataFrame()
    
    def _detect_columns(self, df: pd.DataFrame) -> dict:
        """Detecta columnas relevantes automáticamente"""
        cols = df.columns.tolist()
        mapping = {'codigo': None, 'cantidad': None, 'producto': None, 'bodega': None}
        
        # Posibles nombres de columnas
        code_patterns = ['CODIGO', 'SKU', 'PRODUCTO', 'ITEM', 'CODE', 'ID']
        qty_patterns = ['CANTIDAD', 'QTY', 'QUANTITY', 'UNIDADES', 'UND', 'TOTAL']
        prod_patterns = ['PRODUCTO', 'DESCRIPCION', 'NOMBRE', 'DESC', 'ITEM_NAME']
        bodega_patterns = ['BODEGA', 'DESTINO', 'SUCURSAL', 'TIENDA', 'ALMACEN']
        
        for col in cols:
            col_upper = col.upper()
            if not mapping['codigo'] and any(pat in col_upper for pat in code_patterns):
                mapping['codigo'] = col
            if not mapping['cantidad'] and any(pat in col_upper for pat in qty_patterns):
                # Excluir columnas de totales agregados
                if not any(agg in col_upper for agg in ['TOTAL GENERAL', 'GRAN TOTAL', 'SUM']):
                    mapping['cantidad'] = col
            if not mapping['producto'] and any(pat in col_upper for pat in prod_patterns):
                mapping['producto'] = col
            if not mapping['bodega'] and any(pat in col_upper for pat in bodega_patterns):
                mapping['bodega'] = col
        
        return mapping
    
    def _apply_textile_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica clasificación textil a todos los productos"""
        if 'PRODUCTO' not in df.columns:
            df['PRODUCTO'] = df['CODIGO']
        
        classifications = []
        for product in df['PRODUCTO']:
            classification = self.classifier.classify_product(product)
            classifications.append(classification)
        
        class_df = pd.DataFrame(classifications)
        df = pd.concat([df.reset_index(drop=True), class_df], axis=1)
        
        return df
    
    def _group_warehouse(self, warehouse_name: str) -> str:
        """Agrupa bodegas por categoría"""
        if not isinstance(warehouse_name, str):
            return 'Otros'
        
        warehouse_upper = str(warehouse_name).upper()
        
        for key, group in WAREHOUSE_GROUPS.items():
            if key in warehouse_upper:
                return group
        
        if 'PRICE' in warehouse_upper:
            return 'Price Club'
        elif 'AERO' in warehouse_upper:
            return 'Aeropostale'
        elif any(word in warehouse_upper for word in ['MALL', 'CENTRO', 'SHOPPING']):
            return 'Centro Comercial'
        elif any(word in warehouse_upper for word in ['WEB', 'ONLINE', 'MOVIL']):
            return 'Tienda Online'
        
        return 'Otros'


# ==============================================================================
# FUNCIONES DE PROCESAMIENTO DE TRANSFERENCIAS DIARIAS (ORIGINAL MEJORADO)
# ==============================================================================

def clasificar_transferencia(row):
    """Clasifica las transferencias por categoria"""
    sucursal = str(row.get('Sucursal Destino', row.get('Bodega Destino', ''))).upper()
    cantidad = row.get('Cantidad_Entera', 0)
    
    try:
        cantidad = float(cantidad) if pd.notna(cantidad) else 0
    except:
        cantidad = 0
    
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
    """Procesa las transferencias diarias con manejo de errores mejorado"""
    try:
        df = df.copy()
        df = df.dropna(subset=['Secuencial'])
        df['Secuencial'] = df['Secuencial'].astype(str).str.strip()
        df = df[df['Secuencial'] != '']
        
        # Procesar cantidad con manejo de errores
        df['Cantidad_Entera'] = df['Cantidad Prendas'].apply(
            lambda x: extraer_entero(x) if pd.notna(x) else 0
        )
        
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
            res['por_categoria'][cat] = int(df_cat['Cantidad_Entera'].sum())
            if not df_cat.empty:
                # Determinar columna de sucursal
                sucursal_col = 'Sucursal Destino' if 'Sucursal Destino' in df_cat.columns else 'Bodega Destino'
                res['detalle_categoria'][cat] = {
                    'cantidad': int(df_cat['Cantidad_Entera'].sum()),
                    'transf': int(df_cat['Secuencial'].nunique()),
                    'unicas': int(df_cat[sucursal_col].nunique())
                }
                res['conteo_sucursales'][cat] = res['detalle_categoria'][cat]['unicas']
            else:
                res['detalle_categoria'][cat] = {'cantidad': 0, 'transf': 0, 'unicas': 0}
                res['conteo_sucursales'][cat] = 0
        return res
    except Exception as e:
        st.error(f"Error en procesar_transferencias_diarias: {str(e)}")
        return None


def extraer_entero(valor):
    """Extrae valor entero de diferentes formatos"""
    try:
        if pd.isna(valor):
            return 0
        if isinstance(valor, (int, float)):
            return int(valor)
        if isinstance(valor, str):
            # Limpiar string y convertir
            valor_limpio = valor.replace(',', '').replace("'", "").strip()
            return int(float(valor_limpio))
        return 0
    except:
        return 0


def to_excel(df):
    """Convierte DataFrame a Excel en memoria"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output.getvalue()


# ==============================================================================
# FUNCION PRINCIPAL DEL DASHBOARD
# ==============================================================================

def mostrar_dashboard_transferencias():
    """Muestra el dashboard de transferencias mejorado"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-title {
        font-size: 2.5em;
        margin: 0;
        font-weight: 700;
    }
    .header-subtitle {
        font-size: 1.1em;
        opacity: 0.9;
        margin-top: 10px;
    }
    .filter-panel {
        background: #f8fafc;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .section-description {
        color: #64748b;
        font-size: 0.9em;
    }
    .stat-card {
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
        text-align: center;
    }
    .stat-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 5px;
    }
    .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #1f2937;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #94a3b8;
        margin-top: 5px;
    }
    .card-blue { border-left: 5px solid #0033A0; }
    .card-green { border-left: 5px solid #10B981; }
    .card-orange { border-left: 5px solid #F59E0B; }
    .card-purple { border-left: 5px solid #8B5CF6; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Logísticas</h1>
        <div class='header-subtitle'>Análisis de distribución por canales, clasificación textil y métricas de desempeño</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📊 Transferencias Diarias", 
        "📦 Mercadería en Tránsito", 
        "📈 Análisis de Stock (En desarrollo)"
    ])
    
    # ==========================================
    # TAB 1: TRANSFERENCIAS DIARIAS (ORIGINAL MEJORADO)
    # ==========================================
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📂 Carga de Archivo de Transferencias</h4>
            <p class='section-description'>Sube el archivo Excel de transferencias diarias (ej: 322026.xlsx)</p>
        </div>
        """, unsafe_allow_html=True)
        
        upload_container = st.container()
        
        with upload_container:
            col_upload1, col_upload2 = st.columns([3, 1])
            with col_upload1:
                file_diario = st.file_uploader(
                    "Selecciona el archivo Excel",
                    type=['xlsx'],
                    key="diario_transferencias",
                    label_visibility="collapsed"
                )
            with col_upload2:
                if st.button("🔄 Limpiar", use_container_width=True):
                    st.rerun()
        
        if not file_diario:
            st.info("👆 **Por favor, sube un archivo Excel desde el panel superior para comenzar el análisis.**")
            
            st.markdown("### 📋 Estructura del archivo esperado:")
            ejemplo_data = pd.DataFrame({
                'Secuencial': ['TR001', 'TR002', 'TR003', 'TR004'],
                'Sucursal Destino': ['PRICE CLUB QUITO', 'AERO MALL DEL SOL', 'VENTAS POR MAYOR', 'TIENDA WEB'],
                'Cantidad Prendas': [1500, 245, 5000, 120],
                'Bodega Destino': ['BODEGA CENTRAL', 'BODEGA NORTE', 'BODEGA CENTRAL', 'BODEGA WEB']
            })
            
            st.dataframe(ejemplo_data, use_container_width=True)
            
            st.markdown("""
            ### 📝 Columnas requeridas:
            1. **Secuencial**: Número único de transferencia
            2. **Sucursal Destino** o **Bodega Destino**: Nombre de la tienda destino
            3. **Cantidad Prendas**: Cantidad de unidades a transferir
            
            ### 🎯 Categorías automáticas:
            - **Price Club**: Contiene "PRICE" o "OIL" en el nombre
            - **Tienda Web**: Contiene "WEB", "TIENDA MOVIL" o "MOVIL"
            - **Fallas**: Contiene "FALLAS"
            - **Ventas por Mayor**: Contiene "MAYOR" o "MAYORISTA"
            - **Fundas**: Cantidad ≥ 500 y múltiplo de 100
            - **Tiendas**: Todas las demás transferencias
            """)
            
        else:
            try:
                df_diario = pd.read_excel(file_diario)
                st.success(f"✅ Archivo cargado exitosamente: {file_diario.name}")
                
                with st.expander("🔍 Vista previa del archivo cargado", expanded=True):
                    st.dataframe(df_diario.head(10), use_container_width=True)
                    st.info(f"📊 **Total de filas:** {len(df_diario)} | **Total de columnas:** {len(df_diario.columns)}")
                    
                    st.write("**Columnas detectadas:**")
                    for col in df_diario.columns:
                        st.write(f"- `{col}`")
                
                columnas_requeridas = ['Secuencial', 'Cantidad Prendas']
                columnas_destino = ['Sucursal Destino', 'Bodega Destino']
                
                faltan_requeridas = [col for col in columnas_requeridas if col not in df_diario.columns]
                if faltan_requeridas:
                    st.error(f"❌ **Columnas faltantes:** {faltan_requeridas}")
                    st.info("Por favor, verifica que tu archivo tenga las columnas requeridas.")
                    
                else:
                    tiene_destino = any(col in df_diario.columns for col in columnas_destino)
                    if not tiene_destino:
                        st.error("❌ **No se encontró columna de destino.**")
                        st.info("El archivo debe tener al menos una de estas columnas: 'Sucursal Destino' o 'Bodega Destino'")
                        
                    else:
                        res = procesar_transferencias_diarias(df_diario)
                        
                        if res is None:
                            st.error("❌ Error al procesar los datos")
                            return
                        
                        # --- SECCION 1: KPIs POR CATEGORIA ---
                        st.header("📈 KPIs por Categoría")
                        
                        categorias_display = {
                            'Price Club': 'PRICE CLUB',
                            'Tiendas': 'TIENDAS AEROPOSTALE',
                            'Ventas por Mayor': 'VENTAS POR MAYOR',
                            'Tienda Web': 'TIENDA WEB',
                            'Fallas': 'FALLAS',
                            'Fundas': 'FUNDAS'
                        }
                        
                        sucursales_esperadas = {
                            'Price Club': PRICE_CLUBS,
                            'Tiendas': TIENDAS_REGULARES,
                            'Ventas por Mayor': VENTAS_POR_MAYOR,
                            'Tienda Web': TIENDA_WEB,
                            'Fallas': FALLAS,
                            'Fundas': None
                        }
                        
                        cols = st.columns(3)
                        for i, (cat, cat_display) in enumerate(categorias_display.items()):
                            cantidad = res['por_categoria'].get(cat, 0)
                            sucursales_activas = res['conteo_sucursales'].get(cat, 0)
                            esperadas = sucursales_esperadas.get(cat)
                            
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
                                    card_class = 'card-blue' if i % 3 == 0 else 'card-green' if i % 3 == 1 else 'card-orange'
                                    st.markdown(f"""
                                    <div class='stat-card {card_class}'>
                                        <div class='stat-title'>{cat_display}</div>
                                        <div class='stat-value'>{cantidad:,}</div>
                                        <div class='metric-subtitle'>{sucursales_activas} sucursales | {esperadas} esperadas</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            if i == 2:
                                cols = st.columns(3)
                        
                        st.divider()
                        
                        # --- SECCION 2: GRAFICO DE PASTEL Y ANALISIS VISUAL ---
                        st.header("📊 Análisis Visual")
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            categorias_pie = list(res['por_categoria'].keys())
                            valores_pie = list(res['por_categoria'].values())
                            
                            df_pie = pd.DataFrame({
                                'Categoria': categorias_pie,
                                'Unidades': valores_pie
                            })
                            
                            df_pie = df_pie[df_pie['Unidades'] > 0]
                            
                            if not df_pie.empty:
                                fig_pie = px.pie(
                                    df_pie,
                                    values='Unidades',
                                    names='Categoria',
                                    title="Distribución por Categoría (Gráfico de Pastel)",
                                    color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6', '#F59E0B', '#3B82F6'],
                                    hole=0.3
                                )
                                
                                fig_pie.update_traces(
                                    textposition='inside',
                                    textinfo='percent+label',
                                    hovertemplate='<b>%{label}</b><br>Unidades: %{value:,}<br>Porcentaje: %{percent}'
                                )
                                
                                fig_pie.update_layout(
                                    height=500,
                                    showlegend=True,
                                    legend=dict(
                                        orientation="h",
                                        yanchor="bottom",
                                        y=-0.2,
                                        xanchor="center",
                                        x=0.5
                                    )
                                )
                                
                                st.plotly_chart(fig_pie, use_container_width=True)
                            else:
                                st.info("No hay datos para mostrar el gráfico de pastel")
                        
                        with col2:
                            st.subheader("TOTAL GENERAL")
                            st.markdown(f"""
                            <div class='stat-card'>
                                <div class='stat-title'>Total Unidades</div>
                                <div class='stat-value'>{res['total_unidades']:,}</div>
                                <div class='metric-subtitle'>Suma de todas las unidades</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            promedio = res['total_unidades'] / res['transferencias'] if res['transferencias'] > 0 else 0
                            st.markdown(f"""
                            <div class='stat-card'>
                                <div class='stat-title'>PROMEDIO X TRANSFERENCIA</div>
                                <div class='stat-value'>{promedio:,.0f}</div>
                                <div class='metric-subtitle'>Unidades por transferencia</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            categorias_activas = sum(1 for cat in res['por_categoria'].values() if cat > 0)
                            st.markdown(f"""
                            <div class='stat-card'>
                                <div class='stat-title'>CATEGORÍAS ACTIVAS</div>
                                <div class='stat-value'>{categorias_activas}/6</div>
                                <div class='metric-subtitle'>Categorías con datos</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            porcentaje_fundas = (res['por_categoria'].get('Fundas', 0) / res['total_unidades']) * 100 if res['total_unidades'] > 0 else 0
                            st.markdown(f"""
                            <div class='stat-card'>
                                <div class='stat-title'>% FUNDAS</div>
                                <div class='stat-value'>{porcentaje_fundas:.1f}%</div>
                                <div class='metric-subtitle'>Porcentaje del total</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.divider()
                        
                        # --- SECCION 3: DISTRIBUCION EXCLUYENDO FUNDAS ---
                        st.header("📊 Distribución Excluyendo Fundas")
                        
                        categorias_excl_fundas = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas']
                        valores_excl_fundas = [res['por_categoria'].get(cat, 0) for cat in categorias_excl_fundas]
                        total_excl_fundas = sum(valores_excl_fundas)
                        
                        if total_excl_fundas > 0:
                            df_barras = pd.DataFrame({
                                'Categoria': ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas'],
                                'Unidades': [
                                    res['por_categoria'].get('Price Club', 0),
                                    res['por_categoria'].get('Tiendas', 0),
                                    res['por_categoria'].get('Ventas por Mayor', 0),
                                    res['por_categoria'].get('Tienda Web', 0),
                                    res['por_categoria'].get('Fallas', 0)
                                ]
                            })
                            
                            df_barras['Porcentaje'] = (df_barras['Unidades'] / total_excl_fundas) * 100
                            
                            fig_barras = go.Figure(data=[
                                go.Bar(
                                    x=df_barras['Categoria'],
                                    y=df_barras['Porcentaje'],
                                    text=[f"{p:.1f}%" for p in df_barras['Porcentaje']],
                                    textposition='auto',
                                    marker_color=['#0033A0', '#E4002B', '#10B981', '#8B5CF6', '#F59E0B']
                                )
                            ])
                            
                            fig_barras.update_layout(
                                title="Distribución por Categoría (excluyendo Fundas)",
                                yaxis_title="Porcentaje (%)",
                                xaxis_title="Categoría",
                                template="plotly_white",
                                height=400
                            )
                            
                            st.plotly_chart(fig_barras, use_container_width=True)
                            
                            st.dataframe(
                                df_barras[['Categoria', 'Unidades', 'Porcentaje']].sort_values('Porcentaje', ascending=False),
                                use_container_width=True
                            )
                        else:
                            st.info("No hay datos para mostrar la distribución (excluyendo Fundas)")
                        
                        st.divider()
                        
                        # --- SECCION 4: DETALLE Y EXPORTACION ---
                        st.header("📄 Detalle por Secuencial")
                        
                        # Determinar columna de destino
                        dest_col = 'Sucursal Destino' if 'Sucursal Destino' in res['df_procesado'].columns else 'Bodega Destino'
                        df_detalle = res['df_procesado'][[dest_col, 'Secuencial', 'Cantidad_Entera', 'Categoria']].copy()
                        
                        with st.expander("📋 Resumen Estadístico", expanded=True):
                            resumen_df = pd.DataFrame.from_dict(res['detalle_categoria'], orient='index')
                            resumen_df = resumen_df.reset_index().rename(columns={'index': 'Categoria', 'cantidad': 'Unidades', 'transf': 'Transferencias', 'unicas': 'Sucursales Únicas'})
                            st.dataframe(resumen_df, use_container_width=True)
                        
                        col_d1, col_d2 = st.columns([1, 4])
                        with col_d1:
                            excel_data = to_excel(df_detalle)
                            st.download_button(
                                label="📥 Descargar Excel",
                                data=excel_data,
                                file_name=f"detalle_transferencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        st.dataframe(
                            df_detalle.rename(columns={
                                dest_col: 'Sucursal',
                                'Cantidad_Entera': 'Cantidad',
                                'Categoria': 'Categoría'
                            }),
                            use_container_width=True,
                            height=400
                        )
            
            except Exception as e:
                st.error(f"❌ **Error al procesar el archivo:** {str(e)}")
                st.info("""
                **Posibles causas del error:**
                1. El archivo no es un Excel válido
                2. El archivo está vacío o corrupto
                3. Formato de archivo no compatible
                
                **Solución sugerida:**
                1. Verifica que el archivo sea un Excel (.xlsx)
                2. Asegúrate de que tenga datos en la primera hoja
                3. Verifica que tenga las columnas requeridas
                """)
    
    # ==========================================
    # TAB 2: MERCADERIA EN TRANSITO (AHORA CON UN SOLO ARCHIVO)
    # ==========================================
    with tab2:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📦 Análisis de Mercadería en Tránsito - Clasificación Inteligente</h4>
            <p class='section-description'>Sube un archivo Excel o CSV con los productos en tránsito. El sistema detectará automáticamente las columnas y clasificará género, categoría, color y talla.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Inicializar procesador
        transit_processor = TransitDataProcessor()
        
        file_transito = st.file_uploader(
            "Selecciona archivo de tránsito",
            type=['xlsx', 'csv'],
            key="transito_unico"
        )
        
        if file_transito:
            try:
                with st.spinner("🔍 Clasificando productos..."):
                    df_transito = transit_processor.process_transit_file(file_transito)
                
                if df_transito.empty:
                    st.error("❌ No se pudo procesar el archivo")
                    return
                
                # Métricas principales
                st.subheader("📊 Métricas del Tránsito")
                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                
                with col_m1:
                    st.metric("Total Unidades", f"{int(df_transito['CANTIDAD'].sum()):,}")
                with col_m2:
                    st.metric("SKUs Únicos", df_transito['CODIGO'].nunique())
                with col_m3:
                    st.metric("Categorías", df_transito['Categoria'].nunique())
                with col_m4:
                    st.metric("Géneros", df_transito['Genero'].nunique())
                with col_m5:
                    colores_detectados = df_transito[df_transito['Color'] != 'No Especificado']['Color'].nunique()
                    st.metric("Colores", colores_detectados)
                
                st.divider()
                
                # Gráficos de análisis
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    st.subheader("👕 Distribución por Categoría")
                    cat_dist = df_transito.groupby('Categoria')['CANTIDAD'].sum().sort_values(ascending=True)
                    if not cat_dist.empty:
                        fig_cat = px.bar(
                            x=cat_dist.values,
                            y=cat_dist.index,
                            orientation='h',
                            color=cat_dist.values,
                            color_continuous_scale='Blues',
                            text=cat_dist.values,
                            labels={'x': 'Unidades', 'y': ''}
                        )
                        fig_cat.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                        st.plotly_chart(fig_cat, use_container_width=True)
                
                with col_viz2:
                    st.subheader("⚧ Distribución por Género")
                    gen_dist = df_transito.groupby('Genero')['CANTIDAD'].sum()
                    if not gen_dist.empty:
                        fig_gen = px.pie(
                            values=gen_dist.values,
                            names=gen_dist.index,
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        st.plotly_chart(fig_gen, use_container_width=True)
                
                # Análisis por Color
                st.subheader("🎨 Análisis Cromático")
                if 'Color' in df_transito.columns:
                    col_c1, col_c2 = st.columns([2, 1])
                    color_data = df_transito[df_transito['Color'] != 'No Especificado']
                    
                    if not color_data.empty:
                        color_dist = color_data.groupby('Color')['CANTIDAD'].sum().nlargest(12)
                        
                        with col_c1:
                            fig_color = px.bar(
                                x=color_dist.index,
                                y=color_dist.values,
                                color=color_dist.values,
                                color_continuous_scale='Viridis',
                                text=color_dist.values,
                                labels={'x': 'Color', 'y': 'Unidades'}
                            )
                            fig_color.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                            st.plotly_chart(fig_color, use_container_width=True)
                        
                        with col_c2:
                            st.markdown("**Top 5 Colores:**")
                            total_color = color_data['CANTIDAD'].sum()
                            for i, (color, cant) in enumerate(color_dist.head(5).items(), 1):
                                pct = (cant / total_color) * 100
                                st.write(f"{i}. **{color}**: {int(cant):,} ({pct:.1f}%)")
                    else:
                        st.info("No se detectaron colores específicos.")
                
                # Análisis por Talla
                st.subheader("📏 Distribución por Talla")
                if 'Talla' in df_transito.columns:
                    talla_data = df_transito[~df_transito['Talla'].isin(['Única', 'No Especificado'])]
                    if not talla_data.empty:
                        talla_dist = talla_data.groupby('Talla')['CANTIDAD'].sum()
                        
                        # Ordenar según jerarquía
                        tallas_orden = [t for t in SIZE_HIERARCHY if t in talla_dist.index]
                        tallas_orden += [t for t in talla_dist.index if t not in SIZE_HIERARCHY]
                        talla_dist = talla_dist.reindex([t for t in tallas_orden if t in talla_dist.index])
                        
                        fig_talla = px.line(
                            x=talla_dist.index,
                            y=talla_dist.values,
                            markers=True,
                            labels={'x': 'Talla', 'y': 'Unidades'},
                            line_shape='spline'
                        )
                        fig_talla.update_traces(line_color='#FF6B6B', marker_size=10, line_width=3)
                        st.plotly_chart(fig_talla, use_container_width=True)
                    else:
                        st.info("No se detectaron tallas específicas.")
                
                # Tabla detallada con filtros
                st.subheader("🔍 Explorador de Datos Clasificados")
                
                filtros_cols = st.columns(4)
                df_filtrado = df_transito.copy()
                
                with filtros_cols[0]:
                    if 'Genero' in df_filtrado.columns:
                        gen_sel = st.multiselect("Género", options=df_filtrado['Genero'].unique())
                        if gen_sel:
                            df_filtrado = df_filtrado[df_filtrado['Genero'].isin(gen_sel)]
                
                with filtros_cols[1]:
                    if 'Categoria' in df_filtrado.columns:
                        cat_sel = st.multiselect("Categoría", options=df_filtrado['Categoria'].unique())
                        if cat_sel:
                            df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(cat_sel)]
                
                with filtros_cols[2]:
                    if 'Color' in df_filtrado.columns:
                        col_sel = st.multiselect("Color", options=df_filtrado['Color'].unique())
                        if col_sel:
                            df_filtrado = df_filtrado[df_filtrado['Color'].isin(col_sel)]
                
                with filtros_cols[3]:
                    if 'GRUPO_BODEGA' in df_filtrado.columns:
                        bod_sel = st.multiselect("Grupo Bodega", options=df_filtrado['GRUPO_BODEGA'].unique())
                        if bod_sel:
                            df_filtrado = df_filtrado[df_filtrado['GRUPO_BODEGA'].isin(bod_sel)]
                
                # Mostrar tabla
                display_cols = ['CODIGO', 'CANTIDAD', 'Genero', 'Categoria', 'Color', 'Talla', 'GRUPO_BODEGA']
                if 'PRODUCTO' in df_filtrado.columns:
                    display_cols.insert(1, 'PRODUCTO')
                
                st.dataframe(
                    df_filtrado[[c for c in display_cols if c in df_filtrado.columns]].sort_values('CANTIDAD', ascending=False),
                    use_container_width=True,
                    height=400
                )
                
                # Exportar a Excel
                col_exp1, col_exp2 = st.columns([1, 3])
                with col_exp1:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_transito.to_excel(writer, sheet_name='Datos_Completos', index=False)
                        
                        # Resúmenes adicionales
                        if 'Categoria' in df_transito.columns:
                            res_cat = df_transito.groupby('Categoria').agg({'CANTIDAD': 'sum', 'CODIGO': 'nunique'}).rename(columns={'CODIGO': 'SKUs'})
                            res_cat.to_excel(writer, sheet_name='Resumen_Categorias')
                        
                        if 'Genero' in df_transito.columns:
                            res_gen = df_transito.groupby('Genero').agg({'CANTIDAD': 'sum', 'CODIGO': 'nunique'}).rename(columns={'CODIGO': 'SKUs'})
                            res_gen.to_excel(writer, sheet_name='Resumen_Genero')
                        
                        if 'Color' in df_transito.columns:
                            res_col = df_transito[df_transito['Color'] != 'No Especificado'].groupby('Color').agg({'CANTIDAD': 'sum', 'CODIGO': 'nunique'}).rename(columns={'CODIGO': 'SKUs'})
                            res_col.to_excel(writer, sheet_name='Resumen_Colores')
                        
                        if 'Talla' in df_transito.columns:
                            res_talla = df_transito.groupby('Talla').agg({'CANTIDAD': 'sum', 'CODIGO': 'nunique'}).rename(columns={'CODIGO': 'SKUs'})
                            res_talla.to_excel(writer, sheet_name='Resumen_Tallas')
                    
                    st.download_button(
                        label="📥 Descargar Análisis Completo (Excel)",
                        data=output.getvalue(),
                        file_name=f"analisis_transito_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        use_container_width=True
                    )
                
                with col_exp2:
                    st.info(f"💡 **Tip:** El archivo exportado incluye múltiples pestañas con análisis por dimensión.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
        
        else:
            st.info("👆 Sube un archivo de tránsito para comenzar el análisis.")
    
    # ==========================================
    # TAB 3: ANALISIS DE STOCK (EN DESARROLLO)
    # ==========================================
    with tab3:
        st.header("📈 Análisis de Stock y Ventas (Módulo en Desarrollo)")
        
        st.markdown("""
        <div style="background: #fef3c7; padding: 30px; border-radius: 10px; text-align: center; border: 1px solid #fbbf24;">
            <h3 style="color: #92400e;">🚧 Módulo en Construcción</h3>
            <p style="color: #78350f; font-size: 1.1em;">Este módulo se encuentra actualmente en desarrollo. Pronto podrás acceder a análisis históricos avanzados y gestión de stock.</p>
            <p style="color: #78350f;">Mientras tanto, puedes utilizar las pestañas de Transferencias Diarias y Mercadería en Tránsito para obtener información valiosa.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Opcional: mantener la carga de archivos si ya estaba, pero lo dejamos como placeholder
        with st.expander("🔧 Estructura futura"):
            st.markdown("""
            **Archivo de Stock Actual debe contener:**
            - CODIGO: Código del producto
            - PRODUCTO: Descripción del producto
            - Stock: Cantidad disponible
            - DEPARTAMENTO: Categoría del producto
            
            **Archivo Histórico de Ventas debe contener:**
            - CODIGO: Código del producto
            - FECHA: Fecha de la venta
            - VENTAS: Cantidad vendida
            - SUCURSAL: Sucursal donde se realizó la venta
            """)


def show_dashboard_logistico():
    """Punto de entrada del dashboard logístico"""
    mostrar_dashboard_transferencias()


# Ejecutar si es llamado directamente
if __name__ == "__main__":
    show_dashboard_logistico()
# ==============================================================================
# 8. MODULO GESTION DE EQUIPO
# ==============================================================================

def show_gestion_equipo():
    """Gestion de personal"""
    add_back_button()
    show_module_header(
        "👥 Gestion de Equipo",
        "Administracion del personal del Centro de Distribucion"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>👥 Gestion de Personal</h1>
        <div class='header-subtitle'>Administracion del equipo de trabajo por areas</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Estructura Organizacional", "➕ Gestionar Personal", "📊 Estadisticas", "⚙️ Configuracion"])
    
    # Estructura organizacional base
    estructura_base = {
        "Liderazgo y Control": [
            {"id": 1, "nombre": "Wilson Perez", "cargo": "Jefe de Logistica", "subarea": "Cabeza del C.D.", "estado": "Activo", "es_base": True},
            {"id": 2, "nombre": "Andres Cadena", "cargo": "Jefe de Inventarios", "subarea": "Control de Inventarios", "estado": "Activo", "es_base": True}
        ],
        "Gestion de Transferencias": [
            {"id": 3, "nombre": "Cesar Yepez", "cargo": "Responsable", "subarea": "Transferencias Fashion", "estado": "Activo", "es_base": True},
            {"id": 4, "nombre": "Luis Perugachi", "cargo": "Encargado", "subarea": "Pivote de transferencias Price y Distribucion", "estado": "Activo", "es_base": True},
            {"id": 5, "nombre": "Josue Imbacuan", "cargo": "Responsable", "subarea": "Transferencias Tempo", "estado": "Activo", "es_base": True}
        ],
        "Distribucion, Empaque y Envios": [
            {"id": 6, "nombre": "Jessica Suarez", "cargo": "Distribucion Aero", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 7, "nombre": "Norma Paredes", "cargo": "Distribucion Price", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 8, "nombre": "Jhonny Villa", "cargo": "Empaque y Guias", "subarea": "", "estado": "Activo", "es_base": True},
            {"id": 9, "nombre": "Simon Vera", "cargo": "Guias y Envios", "subarea": "", "estado": "Activo", "es_base": True}
        ],
        "Ventas al Por Mayor": [
            {"id": 10, "nombre": "Jhonny Guadalupe", "cargo": "Encargado", "subarea": "Bodega y Packing", "estado": "Activo", "es_base": True},
            {"id": 11, "nombre": "Rocio Cadena", "cargo": "Responsable", "subarea": "Picking y Distribucion", "estado": "Activo", "es_base": True}
        ],
        "Reproceso y Calidad": [
            {"id": 12, "nombre": "Diana Garcia", "cargo": "Encargada", "subarea": "Reprocesado de prendas en cuarentena", "estado": "Activo", "es_base": True}
        ]
    }
    
    # Obtener trabajadores de la base de datos
    try:
        trabajadores = local_db.query('trabajadores')
        if not trabajadores:
            # Inicializar estructura base si esta vacia
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
                local_db.insert('trabajadores', trab)
            st.success("✅ Estructura base inicializada correctamente")
            trabajadores = local_db.query('trabajadores')
    except Exception as e:
        st.error(f"Error al cargar trabajadores: {str(e)}")
        trabajadores = []
    
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>🏢 Estructura Organizacional del Centro de Distribucion</h4>
            <p class='section-description'>Responsables por area (estructura base)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar estructura por areas
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
            st.metric("🏭 Areas Definidas", len(estructura_base))
        with col_res3:
            cargos_unicos = len(set([t['cargo'] for area in estructura_base.values() for t in area]))
            st.metric("🎯 Cargos Unicos", cargos_unicos)
    
    with tab2:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📝 Gestion de Personal por Area</h4>
            <p class='section-description'>Agregar o eliminar trabajadores en cada area</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Obtener todos los trabajadores actuales
        try:
            trabajadores_db = local_db.query('trabajadores')
            if trabajadores_db is None:
                trabajadores_db = []
        except:
            trabajadores_db = trabajadores
        
        # Pestanas para cada area
        area_tabs = st.tabs(list(estructura_base.keys()))
        
        for idx, (area, trabajadores_area_base) in enumerate(estructura_base.items()):
            with area_tabs[idx]:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Personal en {area}")
                    
                    # Filtrar trabajadores de esta area
                    trabajadores_area_actual = [t for t in trabajadores_db if t.get('area') == area]
                    
                    if trabajadores_area_actual:
                        # Crear dataframe para visualizacion
                        data = []
                        for trab in trabajadores_area_actual:
                            data.append({
                                'ID': trab.get('id', ''),
                                'Nombre': trab.get('nombre', ''),
                                'Cargo': trab.get('cargo', ''),
                                'Subarea': trab.get('subarea', ''),
                                'Estado': trab.get('estado', ''),
                                'Tipo': 'Base' if trab.get('es_base', False) else 'Adicional'
                            })
                        
                        df_area = pd.DataFrame(data)
                        
                        # Mostrar dataframe con opcion de eliminar
                        for i, row in df_area.iterrows():
                            col_d1, col_d2, col_d3, col_d4, col_d5, col_d6 = st.columns([1, 3, 2, 2, 1, 1])
                            with col_d1:
                                st.write(f"**{row['ID']}**")
                            with col_d2:
                                st.write(row['Nombre'])
                            with col_d3:
                                st.write(row['Cargo'])
                            with col_d4:
                                st.write(row['Subarea'] if row['Subarea'] else "-")
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
                                            local_db.delete('trabajadores', int(trabajador_id))
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
                        subarea_nuevo = st.text_input("Area especifica/Subarea", key=f"subarea_{area}")
                        estado_nuevo = st.selectbox("Estado", ["Activo", "Inactivo"], key=f"estado_{area}")
                        
                        submit = st.form_submit_button(f"➕ Agregar a {area}")
                        
                        if submit:
                            if nombre_nuevo and cargo_nuevo:
                                try:
                                    # Generar nuevo ID
                                    if trabajadores_db:
                                        max_id = max([t.get('id', 0) for t in trabajadores_db])
                                    else:
                                        max_id = 12  # Empezar despues de los IDs base
                                    
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
                            else:
                                st.error("❌ Nombre y Cargo son obligatorios")
    
    with tab3:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📊 Estadisticas del Personal</h4>
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
            
            # Metricas principales
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
                    base = len(estructura_base) * 2  # Estimacion
                st.metric("🏛️ Personal Base", base)
            with col_m4:
                if 'es_base' in df_todos.columns:
                    adicional = len(df_todos[df_todos['es_base'] == False])
                else:
                    adicional = max(0, total - base)
                st.metric("➕ Adicionales", adicional)
            
            # Graficos (solo si hay datos suficientes)
            if total > 0:
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    if 'area' in df_todos.columns:
                        dist_area = df_todos['area'].value_counts()
                        fig1 = px.bar(
                            x=dist_area.index, 
                            y=dist_area.values,
                            title="Distribucion por Area",
                            labels={'x': 'Area', 'y': 'Cantidad'},
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
            
            # Tabla resumen por area
            st.subheader("📋 Resumen por Area")
            resumen_data = []
            for area in estructura_base.keys():
                if 'area' in df_todos.columns:
                    area_data = df_todos[df_todos['area'] == area]
                    activos_area = len(area_data[area_data['estado'] == 'Activo']) if 'estado' in df_todos.columns else len(area_data)
                    base_area = len(area_data[area_data.get('es_base', False) == True]) if 'es_base' in df_todos.columns else 0
                    
                    resumen_data.append({
                        'Area': area,
                        'Total': len(area_data),
                        'Activos': activos_area,
                        'Base': base_area,
                        'Adicional': len(area_data) - base_area
                    })
            
            if resumen_data:
                df_resumen = pd.DataFrame(resumen_data)
                st.dataframe(df_resumen, use_container_width=True)
            else:
                st.info("No hay datos de areas para mostrar")
        else:
            st.info("No hay datos para mostrar estadisticas.")
    
    with tab4:
        st.markdown("""
        <div class='filter-panel'>
            <h4>⚙️ Configuracion del Sistema</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Restaurar Estructura Base")
            st.warning("⚠️ Esta accion eliminara todo el personal adicional y restaurara la estructura original")
            
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
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 9. MODULO RECONCILIACION V8
# ==============================================================================

def identificar_tipo_tienda_v8(nombre):
    """
    Logica V8.0 para clasificacion de tiendas.
    Incluye regla especifica para JOFRE SANTANA y manejo de Piezas.
    """
    if pd.isna(nombre) or nombre == '': return "DESCONOCIDO"
    nombre_norm = normalizar_texto_wilo(nombre)
    
    # 1. Regla Especifica Solicitada
    if 'JOFRE' in nombre_norm and 'SANTANA' in nombre_norm:
        return "VENTAS AL POR MAYOR"
    
    # 2. Tiendas Fisicas (Patrones)
    patrones_fisicas = ['LOCAL', 'MALL', 'PLAZA', 'SHOPPING', 'CENTRO', 'COMERCIAL', 'CC', 
                       'TIENDA', 'PASEO', 'PORTAL', 'DORADO', 'CITY', 'CEIBOS', 'QUITO', 
                       'GUAYAQUIL', 'AMBATO', 'MANTA', 'MACHALA', 'RIOCENTRO', 'AEROPOSTALE']
    
    if any(p in nombre_norm for p in patrones_fisicas):
        return "TIENDA FISICA"
        
    # 3. Nombres Propios (Venta Web)
    palabras = nombre_norm.split()
    if len(palabras) > 0 and len(palabras) <= 3:
        return "VENTA WEB"
        
    return "TIENDA FISICA" # Default

def show_reconciliacion_v8():
    """Modulo de reconciliacion financiera"""
    add_back_button()
    show_module_header(
        "💰 Reconciliacion V8",
        "Conciliacion de facturas y manifiestos con IA"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📦 Reconciliacion Logistica V8.0</h1>
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
    
    # Datos de ejemplo para demostracion
    use_sample = st.checkbox("Usar datos de demostracion", value=True)
    
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
                
                st.success("✅ Usando datos de demostracion. Puede subir sus propios archivos para procesamiento real.")
            else:
                # Lectura flexible de archivos subidos
                df_m = pd.read_excel(f_manifiesto) if f_manifiesto.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_manifiesto)
                df_f = pd.read_excel(f_facturas) if f_facturas.name.endswith(('xlsx', 'xls')) else pd.read_csv(f_facturas)

            # Configuracion de columnas
            st.markdown("""
            <div class='filter-panel'>
                <h3 class='filter-title'>⚙️ Configuracion de Columnas</h3>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.info("**Configuracion Manifiesto**")
                cols_m = df_m.columns.tolist()
                # Deteccion inteligente
                idx_guia = next((i for i, c in enumerate(cols_m) if 'GUIA' in str(c).upper()), 0)
                idx_dest = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['DEST', 'CLIEN', 'NOMB'])), 0)
                idx_piez = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['PIEZA', 'CANT', 'BULT'])), 0)
                idx_val = next((i for i, c in enumerate(cols_m) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL'])), 0)

                col_guia_m = st.selectbox("Columna Guia", cols_m, index=idx_guia, key='m_guia')
                col_dest_m = st.selectbox("Columna Destinatario", cols_m, index=idx_dest, key='m_dest')
                col_piezas_m = st.selectbox("Columna Piezas/Bultos", cols_m, index=idx_piez, key='m_piezas')
                col_valor_m = st.selectbox("Columna Valor Declarado", cols_m, index=idx_val, key='m_val')
            
            with c2:
                st.info("**Configuracion Facturas**")
                cols_f = df_f.columns.tolist()
                idx_guia_f = next((i for i, c in enumerate(cols_f) if 'GUIA' in str(c).upper()), 0)
                idx_val_f = next((i for i, c in enumerate(cols_f) if any(x in str(c).upper() for x in ['VALOR', 'TOTAL', 'SUBT'])), 0)

                col_guia_f = st.selectbox("Columna Guia", cols_f, index=idx_guia_f, key='f_guia')
                col_valor_f = st.selectbox("Columna Valor Cobrado", cols_f, index=idx_val_f, key='f_val')
            st.markdown("</div>", unsafe_allow_html=True)

            # Boton de ejecucion
            if st.button("🚀 EJECUTAR RECONCILIACION V8.0", type="primary", use_container_width=True):
                with st.spinner("🔄 Ejecutando algoritmo V8.0..."):
                    # Procesamiento
                    df_m['GUIA_CLEAN'] = df_m[col_guia_m].astype(str).str.strip().str.upper()
                    df_f['GUIA_CLEAN'] = df_f[col_guia_f].astype(str).str.strip().str.upper()
                    
                    # Merge
                    df_final = pd.merge(df_m, df_f, on='GUIA_CLEAN', how='left', suffixes=('_MAN', '_FAC'))
                    
                    # Logica V8
                    df_final['DESTINATARIO_NORM'] = df_final[col_dest_m].fillna('DESCONOCIDO')
                    df_final['TIPO_TIENDA'] = df_final['DESTINATARIO_NORM'].apply(identificar_tipo_tienda_v8)
                    
                    # Manejo de Piezas y Valores
                    df_final['PIEZAS_CALC'] = pd.to_numeric(df_final[col_piezas_m], errors='coerce').fillna(1)
                    df_final['VALOR_REAL'] = df_final[col_valor_f].apply(procesar_subtotal_wilo).fillna(0)
                    df_final['VALOR_MANIFIESTO'] = df_final[col_valor_m].apply(procesar_subtotal_wilo).fillna(0)
                    
                    # Creacion de Grupos
                    def crear_grupo(row):
                        tipo = row['TIPO_TIENDA']
                        nom = normalizar_texto_wilo(row['DESTINATARIO_NORM'])
                        if tipo == "VENTAS AL POR MAYOR": return "VENTAS AL POR MAYOR - JOFRE SANTANA"
                        if tipo == "VENTA WEB": return f"WEB - {nom}"
                        return f"TIENDA - {nom}"
                    
                    df_final['GRUPO'] = df_final.apply(crear_grupo, axis=1)

                    # --- RESULTADOS ---
                    st.markdown("""
                    <div class='main-header'>
                        <h2>📊 Resultados del Analisis V8.0</h2>
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
                            <div class='stat-title'>Guias Conciliadas</div>
                            <div class='stat-value'>{con_factura}</div>
                            <div class='stat-change positive'>+{con_factura/len(df_final)*100:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k4:
                        st.markdown(f"""
                        <div class='stat-card card-red'>
                            <div class='stat-icon'>⚠️</div>
                            <div class='stat-title'>Guias Sin Factura</div>
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
                        resumen.columns = ['Canal', 'Guias', 'Piezas', 'Valor Facturado']
                        resumen['% Gasto'] = (resumen['Valor Facturado'] / total_facturado * 100).round(2)
                        resumen['Valor Promedio'] = (resumen['Valor Facturado'] / resumen['Guias']).round(2)
                        
                        st.dataframe(
                            resumen.style.format({
                                'Valor Facturado': '${:,.2f}',
                                '% Gasto': '{:.2f}%',
                                'Valor Promedio': '${:,.2f}'
                            }).background_gradient(subset=['% Gasto'], cmap='Blues'),
                            use_container_width=True
                        )
                        
                        # Graficos
                        col_chart1, col_chart2 = st.columns(2)
                        with col_chart1:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            fig = px.pie(resumen, values='Valor Facturado', names='Canal', 
                                       title="Distribucion por Canal", 
                                       color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_chart2:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            fig2 = px.bar(resumen, x='Canal', y='Guias', color='Canal',
                                        title="Guias por Canal", text='Guias',
                                        color_discrete_sequence=['#0033A0', '#E4002B', '#10B981', '#8B5CF6'])
                            st.plotly_chart(fig2, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)

                    with tab2:
                        detalle = df_final.groupby('GRUPO').agg({
                            'GUIA_CLEAN': 'count',
                            'PIEZAS_CALC': 'sum',
                            'VALOR_REAL': 'sum'
                        }).sort_values('VALOR_REAL', ascending=False)
                        detalle.columns = ['Guias', 'Piezas', 'Valor Total']
                        
                        # Agregar metricas
                        detalle['Valor Promedio'] = (detalle['Valor Total'] / detalle['Guias']).round(2)
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
                    
                    # Exportacion
                    st.markdown("### 💾 Exportar Datos")
                    buffer = io.BytesIO()
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
                        # Exportar CSV rapido
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
        st.info("👆 Suba los archivos necesarios o active la opcion de datos de demostracion para comenzar.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 10. MODULO AUDITORIA DE CORREOS
# ==============================================================================

class WiloEmailEngine:
    """Motor real para extraccion y analisis de correos logisticos."""
    
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.mail = None

    def _connect(self):
        """Establece conexion segura SSL con el servidor de Fashion Club."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.host)
            self.mail.login(self.user, self.password)
            self.mail.select("inbox")
        except Exception as e:
            raise ConnectionError(f"Error de conexion: Verifica tu usuario/pass. Detalle: {e}")

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
        
        # Diccionario de busqueda semantica simple
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
        """Busca y procesa los correos mas recientes en la bandeja real."""
        self._connect()
        
        # Filtro: Solo correos de los ultimos 30 dias para no saturar el servidor
        date_filter = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        _, messages = self.mail.search(None, f'(SINCE "{date_filter}")')
        
        ids = messages[0].split()
        latest_ids = ids[-limit:]  # Tomar los ultimos N correos
        
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

                    # Inteligencia de Clasificacion
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

def show_auditoria_correos():
    """Modulo de auditoria de correos"""
    add_back_button()
    show_module_header(
        "📧 Auditoria de Correos",
        "Analisis inteligente de novedades por email"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # Sidebar para Credenciales (Seguridad primero)
    st.sidebar.title("🔐 Acceso Seguro")
    mail_user = st.sidebar.text_input("Correo", value="wperez@fashionclub.com.ec")
    mail_pass = st.sidebar.text_input("Contrasena", value="2wperez*", type="password")
    imap_host = "mail.fashionclub.com.ec"
    
    st.title("📧 Auditoria de Correos Wilo AI")
    st.markdown("---")

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"**Usuario:** {mail_user} | **Servidor:** {imap_host}")
    
    with col_btn:
        run_audit = st.button("🚀 Iniciar Auditoria Real", use_container_width=True, type="primary")

    if run_audit:
        if not mail_pass:
            st.error("Por favor ingresa tu contrasena en la barra lateral.")
            return

        engine = WiloEmailEngine(imap_host, mail_user, mail_pass)
        
        with st.spinner("Conectando con Fashion Club y analizando novedades..."):
            try:
                data = engine.get_latest_news(limit=30)
                if not data:
                    st.warning("No se encontraron novedades en los ultimos 30 dias.")
                    return

                df = pd.DataFrame(data)

                # --- DASHBOARD DE METRICAS ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Criticos 🚨", len(df[df['urgencia'] == 'ALTA']))
                m3.metric("Faltantes 📦", len(df[df['tipo'].str.contains('FALTANTE')]))
                m4.metric("Detecciones", df['pedido'].nunique() - (1 if 'N/A' in df['pedido'].values else 0))

                # --- TABLA DE RESULTADOS ---
                st.subheader("📋 Bandeja de Entrada Analizada")
                st.dataframe(
                    df[['fecha', 'remitente', 'asunto', 'tipo', 'urgencia', 'pedido']],
                    use_container_width=True,
                    column_config={
                        "urgencia": st.column_config.TextColumn("Prioridad"),
                        "tipo": st.column_config.TextColumn("Categoria"),
                        "pedido": st.column_config.TextColumn("ID Pedido")
                    }
                )

                # --- INSPECTOR DETALLADO ---
                st.markdown("---")
                st.subheader("🔍 Inspector de Contenido")
                selected_idx = st.selectbox(
                    "Selecciona un correo para leer el analisis completo:",
                    df.index,
                    format_func=lambda x: f"[{df.iloc[x]['tipo']}] - {df.iloc[x]['asunto'][:50]}..."
                )
                
                detail = df.iloc[selected_idx]
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"""
                    **Detalles Tecnicos:**
                    - **Remitente:** {detail['remitente']}
                    - **Fecha:** {detail['fecha']}
                    - **Pedido Detectado:** `{detail['pedido']}`
                    """)
                with c2:
                    st.text_area("Cuerpo del Correo:", detail['cuerpo'], height=200)

            except Exception as e:
                st.error(f"❌ Error durante la auditoria: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 11. MODULO GENERAR GUIAS
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
    """Genera un PDF profesional con formato similar a la guia medica de ejemplo"""
    buffer = io.BytesIO()
    
    # Configurar el documento
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.2*inch, leftMargin=0.2*inch,
                           topMargin=0.2*inch, bottomMargin=0.2*inch)
    
    styles = getSampleStyleSheet()
    
    # Crear estilos personalizados basados en la imagen
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Title'],
        fontSize=16,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=2
    ))
    
    styles.add(ParagraphStyle(
        name='EncabezadoSeccion',
        parent=styles['Heading3'],
        fontSize=10,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=4,
        spaceBefore=4,
        underline=True
    ))
    
    styles.add(ParagraphStyle(
        name='CampoTitulo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        name='CampoContenido',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        fontName='Helvetica',
        alignment=TA_LEFT,
        spaceAfter=4,
        leftIndent=10
    ))
    
    # Contenido del documento
    contenido = []
    
    # CABECERA CON LOGO, TITULO Y QR
    # ==========================
    
    # Determinar logo segun marca
    logo_bytes = None
    if guia_data['marca'] == 'Fashion Club':
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    else:
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
    # Descargar logo si no esta en session_state
    if guia_data['marca'] not in st.session_state.get('logos', {}):
        logo_bytes = descargar_logo(logo_url)
        if logo_bytes:
            if 'logos' not in st.session_state:
                st.session_state.logos = {}
            st.session_state.logos[guia_data['marca']] = logo_bytes
    else:
        logo_bytes = st.session_state.logos[guia_data['marca']]
    
    # Preparar elementos para la cabecera
    cabecera_elements = []
    
    # Columna izquierda: Logo
    if logo_bytes:
        try:
            logo_img = Image(io.BytesIO(logo_bytes), width=1*inch, height=1*inch)
            logo_cell = logo_img
        except:
            logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['TituloPrincipal'])
    else:
        logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['TituloPrincipal'])
    
    # Columna central: Titulo principal con fondo
    titulo_text = f"""
    <b>CENTRO DE DISTRIBUCION<br/>{guia_data['marca'].upper()}</b>
    """
    titulo_cell = Paragraph(titulo_text, styles['TituloPrincipal'])
    
    # Columna derecha: QR
    qr_cell = None
    if guia_data['url_pedido'] in st.session_state.get('qr_images', {}):
        try:
            qr_bytes = st.session_state.qr_images[guia_data['url_pedido']]
            qr_img = Image(io.BytesIO(qr_bytes), width=1*inch, height=1*inch)
            qr_cell = qr_img
        except:
            qr_cell = Paragraph(f"<b>QR<br/>Seguimiento</b>", 
                               ParagraphStyle(name='QRPlaceholder', fontSize=8, alignment=TA_CENTER))
    else:
        qr_cell = Paragraph("", styles['Normal'])
    
    # Crear tabla de cabecera con 3 columnas
    cabecera_table = Table([[logo_cell, titulo_cell, qr_cell]], 
                          colWidths=[1.5*inch, 3.5*inch, 1*inch])
    
    cabecera_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, 0), HexColor('#F0F0F0')),  # Fondo para el titulo
        ('BOX', (1, 0), (1, 0), 1, HexColor('#CCCCCC')),     # Borde alrededor del titulo
    ]))
    
    contenido.append(cabecera_table)
    
    # SUBTITULO: GUIA DE REMISION
    contenido.append(Paragraph("GUIA DE REMISION", styles['Subtitulo']))
    
    # NOTA SOBRE EL QR (justo debajo del subtitulo)
    contenido.append(Paragraph("<b>Nota:</b> Escanee el codigo QR en la cabecera para seguimiento del pedido", 
                             ParagraphStyle(name='NotaQR', fontSize=8, alignment=TA_CENTER, spaceAfter=8)))
    
    # INFORMACION DE LA GUIA EN UNA TABLA
    # ===================================
    
    # Informacion de la guia (numero, fecha, estado)
    info_guia = Table([
        [Paragraph(f"<b>Numero de Guia:</b> {guia_data['numero']}", styles['CampoContenido']),
         Paragraph(f"<b>Fecha de Emision:</b> {guia_data['fecha_emision']}", styles['CampoContenido']),
         Paragraph(f"<b>Estado:</b> {guia_data['estado']}", styles['CampoContenido'])]
    ], colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    
    info_guia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F0F0F0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
    ]))
    
    contenido.append(info_guia)
    contenido.append(Spacer(1, 0.1*inch))
    
    # REMITENTE Y DESTINATARIO EN UNA TABLA DE 2 COLUMNAS (GRID)
    # ===========================================================
    
    # Crear tabla con dos columnas para remitente y destinatario
    remitente_destinatario_data = [
        [Paragraph("<b>REMITENTE</b>", styles['EncabezadoSeccion']),
         Paragraph("<b>DESTINATARIO</b>", styles['EncabezadoSeccion'])],
        
        [Paragraph(f"<b>Nombre:</b> {guia_data['remitente']}", styles['CampoContenido']),
         Paragraph(f"<b>Nombre:</b> {guia_data['destinatario']}", styles['CampoContenido'])],
        
        [Paragraph(f"<b>Direccion:</b> {guia_data['direccion_remitente']}", styles['CampoContenido']),
         Paragraph(f"<b>Ciudad:</b> {guia_data['tienda_destino']}", styles['CampoContenido'])],
        
        ['',  # Celda vacia para remitente
         Paragraph(f"<b>Direccion:</b> {guia_data['direccion_destinatario']}", styles['CampoContenido'])]
    ]
    
    tabla_remitente_destinatario = Table(remitente_destinatario_data, colWidths=[3.5*inch, 3.5*inch])
    tabla_remitente_destinatario.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('BACKGROUND', (0, 0), (1, 0), HexColor('#E8E8E8')),  # Fondo para los encabezados
        ('SPAN', (0, 0), (0, 0)),  # Expandir REMITENTE en su columna
        ('SPAN', (1, 0), (1, 0)),  # Expandir DESTINATARIO en su columna
    ]))
    
    contenido.append(tabla_remitente_destinatario)
      
    # Construir el PDF
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()
    
def mostrar_vista_previa_guia(guia_data):
    """CORRECCION: Funcion que recibe guia_data como parametro explicito"""
    st.markdown("---")
    st.markdown(f"### 👁️ Vista Previa - Guia {guia_data['numero']}")
    
    col_prev1, col_prev2 = st.columns(2)
    
    with col_prev1:
        st.markdown(f"""
        <div style='background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #0033A0;'>
            <h4 style='color: #0033A0; margin-bottom: 10px;'>🏢 Informacion de la Empresa</h4>
            <p><strong>Marca:</strong> {guia_data['marca']}</p>
            <p><strong>Numero de Guia:</strong> {guia_data['numero']}</p>
            <p><strong>Fecha:</strong> {guia_data['fecha_emision']}</p>
            <p><strong>Estado:</strong> {guia_data['estado']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #E4002B;'>
            <h4 style='color: #E4002B; margin-bottom: 10px;'>👤 Informacion del Remitente</h4>
            <p><strong>Nombre:</strong> {guia_data['remitente']}</p>
            <p><strong>Direccion:</strong> {guia_data['direccion_remitente'][:50]}...</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_prev2:
        st.markdown(f"""
        <div style='background: #f8f9fa; border-radius: 10px; padding: 20px; margin-bottom: 20px; border-left: 4px solid #10B981;'>
            <h4 style='color: #10B981; margin-bottom: 10px;'>🏪 Informacion del Destinatario</h4>
            <p><strong>Nombre:</strong> {guia_data['destinatario']}</p>
            <p><strong>Telefono:</strong> {guia_data['telefono_destinatario']}</p>
            <p><strong>Tienda:</strong> {guia_data['tienda_destino']}</p>
            <p><strong>Direccion:</strong> {guia_data['direccion_destinatario'][:50]}...</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: #f8f9fa; border-radius: 10px; padding: 20px; border-left: 4px solid #8B5CF6;'>
            <h4 style='color: #8B5CF6; margin-bottom: 10px;'>🔗 Informacion Digital</h4>
            <p><strong>URL de Seguimiento:</strong></p>
            <p style='word-break: break-all; font-size: 0.9rem;'>{guia_data['url_pedido']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Mostrar QR si existe
    if guia_data.get('qr_bytes'):
        st.markdown("---")
        st.markdown("### 🔗 Vista Previa del Codigo QR")
        col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
        with col_qr2:
            st.image(guia_data['qr_bytes'], caption="Codigo QR para seguimiento", width=150)
    
    st.info("Esta es una vista previa. Haz clic en '🚀 Generar Guia PDF' para crear el documento oficial.")


def show_generar_guias():
    """Generador de guias de envio"""
    add_back_button()
    show_module_header(
        "🚚 Generador de Guias",
        "Sistema de envios con seguimiento QR"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    # URLs de logos desde GitHub
    url_fashion_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    url_tempo_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
    # Listas de tiendas y remitentes
    tiendas = [
        "Matriz","Aero Oil Uno", "Aero La Plaza", "Aero Milagro", "Aero Condado Shopping",
        "Aero Multiplaza Riobamba", "Aero Santo Domingo", "Aero Quevedo", "Aero Manta", "Aero Portoviejo", 
        "Price Club Portoviejo", "Aero Rio Centro Norte", "Aero Duran", "Price Club City Mall", "Aero Mall Del Sur",
        "Aero Los Ceibos", "Aero Ambato", "Aero Carapungo", "Aero Peninsula", "Aero Paseo Ambato", "Aero Mall Del Sol", 
        "Aero Babahoyo", "Aero Riobamba", "Aero Mall Del Pacifico", "Aero San Luis", "Aero Machala",
        "Aero Cuenca Centro Historico", "Aero Cuenca", "Aero Tienda Movil - Web",
        "Aero Playas", "Aero Bomboli", "Aero Mall Del Rio Gye","Aero Riocentro El Dorado", "Aero Pasaje", "Aero El Coca",
        "Aero 6 De Diciembre", "Aero Lago Agrio","Aero Pedernales", "Price Club Machala", "Price Club Guayaquil",
        "Aero CCi", "Aero Cayambe", "Aero Bahia De Caraquez", "Aero Daule", "Aero Jagi El Dorado"
    ]
    
    remitentes = [
        {"nombre": "Josue Imbacuan", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Luis Perugachi", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andres Yepez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Wilson Perez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andres Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Diana Garcia", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jessica Suarez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Rocio Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jhony Villa", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"}
    ]
    
    with st.form("guias_form", border=False):
        st.markdown("""
        <div class='filter-panel'>
            <h3 class='filter-title'>📋 Informacion de la Guia</h3>
        """, unsafe_allow_html=True)
        
        # Primera fila: Informacion de empresa y remitente
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Informacion de la Empresa")
            marca = st.radio("**Seleccione la Marca:**", ["Fashion Club", "Tempo"], horizontal=True)
            
            # Mostrar imagen segun seleccion
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
            st.subheader("👤 Informacion del Remitente")
            remitente_nombre = st.selectbox("**Seleccione Remitente:**", [r["nombre"] for r in remitentes])
            
            # Direccion del remitente
            remitente_direccion = next((r["direccion"] for r in remitentes if r["nombre"] == remitente_nombre), "")
            st.info(f"""
            **Direccion del Remitente:**
            📍 {remitente_direccion}
            """)
        
        
        st.divider()
        
        # Tercera fila: Informacion del destinatario
        st.subheader("🏪 Informacion del Destinatario")
        col5, col6 = st.columns(2)
        
        with col5:
            nombre_destinatario = st.text_input("**Nombre del Destinatario:**", placeholder="Ej: Pepito Paez")
            telefono_destinatario = st.text_input("**Telefono del Destinatario:**", placeholder="Ej: +593 99 999 9999")
        
        with col6:
            direccion_destinatario = st.text_area("**Direccion del Destinatario:**", 
                                                placeholder="Ej: Av. Principal #123, Ciudad, Provincia",
                                                height=100)
            tienda_destino = st.selectbox("**Tienda Destino (Opcional):**", [""] + tiendas)
        
        st.divider()
        
        # Cuarta fila: URL y QR
        st.subheader("🔗 Informacion Digital")
        url_pedido = st.text_input("**URL del Pedido/Tracking:**", 
                                 placeholder="https://pedidos.fashionclub.com/orden-12345",
                                 value="https://pedidos.fashionclub.com/")
        
        # Generar codigo QR basado en URL
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
                if 'qr_images' not in st.session_state:
                    st.session_state.qr_images = {}
                st.session_state.qr_images[url_pedido] = img_byte_arr.getvalue()
                
                # Mostrar QR
                col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                with col_qr2:
                    st.image(img_byte_arr, caption="Codigo QR Generado", width=150)
                    st.caption(f"URL: {url_pedido[:50]}...")
            except:
                st.warning("⚠️ No se pudo generar el codigo QR. Verifique la URL.")
        elif url_pedido:
            st.warning("⚠️ La URL debe comenzar con http:// o https://")
        
        st.divider()
        
        # Botones de accion
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit = st.form_submit_button("🚀 Generar Guia PDF", use_container_width=True, type="primary")
        with col_btn2:
            preview = st.form_submit_button("👁️ Vista Previa", use_container_width=True)
        with col_btn3:
            reset = st.form_submit_button("🔄 Nuevo Formulario", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Procesar la guia
    if preview:
        # Validaciones basicas para vista previa
        if not nombre_destinatario or not direccion_destinatario:
            st.warning("Complete al menos nombre y direccion del destinatario para ver la vista previa")
        else:
            # CORRECCION: Asegurar que contador_guias existe
            if 'contador_guias' not in st.session_state:
                st.session_state.contador_guias = 1000
            
            # Generar numero de guia para vista previa
            guia_num_preview = f"GFC-{st.session_state.contador_guias:04d}"
            
            # Obtener bytes del QR si existe
            qr_bytes = st.session_state.qr_images.get(url_pedido) if url_pedido in st.session_state.get('qr_images', {}) else None
            
            # Crear diccionario con datos de la guia para vista previa
            guia_data_preview = {
                "numero": guia_num_preview,
                "marca": marca,
                "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion,
                "destinatario": nombre_destinatario,
                "telefono_destinatario": telefono_destinatario or "No especificado",
                "direccion_destinatario": direccion_destinatario,
                "tienda_destino": tienda_destino if tienda_destino else "No especificada",
                "url_pedido": url_pedido if url_pedido else "No especificada",
                "estado": "Vista Previa",
                "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "qr_bytes": qr_bytes
            }
            
            # CORRECCION: Llamar funcion con parametro explicito
            mostrar_vista_previa_guia(guia_data_preview)
    
    if submit:
        # Validaciones
        errors = []
        if not nombre_destinatario:
            errors.append("❌ El nombre del destinatario es obligatorio")
        if not direccion_destinatario:
            errors.append("❌ La direccion del destinatario es obligatoria")
        if not url_pedido or len(url_pedido) < 10:
            errors.append("❌ Ingrese una URL valida para el pedido")
        elif not url_pedido.startswith(('http://', 'https://')):
            errors.append("❌ La URL debe comenzar con http:// o https://")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # CORRECCION: Asegurar que contador_guias existe
            if 'contador_guias' not in st.session_state:
                st.session_state.contador_guias = 1000
            
            # Generar numero de guia unico
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1
            
            # Descargar logo si no esta en cache
            if 'logos' not in st.session_state:
                st.session_state.logos = {}
                
            if marca not in st.session_state.logos:
                logo_url = url_fashion_logo if marca == "Fashion Club" else url_tempo_logo
                logo_bytes = descargar_logo(logo_url)
                if logo_bytes:
                    st.session_state.logos[marca] = logo_bytes
            
            # Obtener bytes del QR
            qr_bytes = st.session_state.qr_images.get(url_pedido) if 'qr_images' in st.session_state and url_pedido in st.session_state.qr_images else None
            
            # Crear diccionario con datos de la guia
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
            
            with st.spinner(f"Generando guia {guia_num}..."):
                time.sleep(1.5)
                
                # Agregar a lista de guias
                if 'guias_registradas' not in st.session_state:
                    st.session_state.guias_registradas = []
                st.session_state.guias_registradas.append(guia_data)
                
                # Tambien guardar en la base de datos local
                try:
                    local_db.insert('guias', guia_data)
                except Exception as e:
                    st.warning(f"⚠️ No se pudo guardar en la base de datos: {str(e)}")
                
                # Generar PDF mejorado con logo y QR
                pdf_bytes = generar_pdf_profesional(guia_data)
                
                st.success(f"✅ Guia {guia_num} generada exitosamente!")
                
                # MOSTRAR RESUMEN Y OPCIONES DE DESCARGA (CORRECCION)
                st.markdown("---")
                st.markdown(f"### 📋 Resumen de la Guia {guia_num}")
                
                col_sum1, col_sum2 = st.columns(2)
                with col_sum1:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Numero de Guia</div>
                        <div class='metric-value'>{guia_num}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Remitente</div>
                        <div class='metric-value'>{remitente_nombre}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Destinatario</div>
                        <div class='metric-value'>{nombre_destinatario}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_sum2:
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Marca</div>
                        <div class='metric-value'>{marca}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Fecha</div>
                        <div class='metric-value'>{datetime.now().strftime('%Y-%m-%d')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class='metric-card'>
                        <div class='metric-title'>Estado</div>
                        <div class='metric-value'>Generada</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Boton para descargar PDF
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"guia_{guia_num}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                
                with col_btn2:
                    if st.button("🔄 Generar Otra Guia", use_container_width=True):
                        st.rerun()
                
                # Mostrar QR generado
                if qr_bytes:
                    st.markdown("---")
                    st.markdown("### 🔗 Codigo QR Generado")
                    col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                    with col_qr2:
                        st.image(qr_bytes, caption="Escanea para seguir el pedido", width=200)
                        st.caption(f"URL: {url_pedido}")
    
    st.markdown('</div>', unsafe_allow_html=True)
# ==============================================================================
# 12. MODULOS RESTANTES (PLACEHOLDERS)
# ==============================================================================

def show_control_inventario():
    """Control de inventario"""
    add_back_button()
    show_module_header(
        "📋 Control de Inventario",
        "Gestion de stock en tiempo real"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.info("""
    ## 🚧 Modulo en Desarrollo
    
    **Funcionalidades planeadas:**
    - 📊 Control de stock en tiempo real
    - 📈 Alertas de inventario bajo
    - 🔄 Sistema de reposicion automatica
    - 📋 Auditorias de inventario
    
    *Disponible en la proxima version*
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_reportes_avanzados():
    """Generador de reportes"""
    add_back_button()
    show_module_header(
        "📈 Reportes Avanzados",
        "Analisis y estadisticas ejecutivas"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.info("""
    ## 🚧 Modulo en Desarrollo
    
    **Funcionalidades planeadas:**
    - 📊 Reportes personalizados
    - 📈 Analisis predictivo
    - 📋 Dashboards ejecutivos
    - 📤 Exportacion multiple formatos
    
    *Disponible en la proxima version*
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_configuracion():
    """Configuracion del sistema"""
    add_back_button()
    show_module_header(
        "⚙️ Configuracion",
        "Personalizacion del sistema ERP"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["General", "Usuarios", "Seguridad"])
    
    with tab1:
        st.header("Configuracion General")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌐 Configuracion Regional")
            zona_horaria = st.selectbox("Zona Horaria", ["America/Guayaquil", "UTC"])
            moneda = st.selectbox("Moneda", ["USD", "EUR", "COP"])
            idioma = st.selectbox("Idioma", ["Espanol", "Ingles"])
        
        with col2:
            st.subheader("📊 Configuracion de Reportes")
            formato_fecha = st.selectbox("Formato de Fecha", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
            decimales = st.slider("Decimales", 0, 4, 2)
            separador_miles = st.selectbox("Separador de Miles", [",", ".", " "])
        
        if st.button("💾 Guardar Configuracion"):
            st.success("✅ Configuracion guardada exitosamente")
    
    with tab2:
        st.header("Gestion de Usuarios")
        
        # Mostrar usuarios existentes
        usuarios = local_db.query('users')
        df_usuarios = pd.DataFrame(usuarios)
        
        if not df_usuarios.empty:
            st.dataframe(df_usuarios[['username', 'role']], use_container_width=True)
        
        # Formulario para agregar usuario
        with st.form("form_usuario"):
            st.subheader("Agregar Nuevo Usuario")
            nuevo_usuario = st.text_input("Nombre de usuario")
            nueva_contrasena = st.text_input("Contrasena", type="password")
            rol = st.selectbox("Rol", ["admin", "user"])
            
            if st.form_submit_button("➕ Agregar Usuario"):
                if nuevo_usuario and nueva_contrasena:
                    try:
                        local_db.insert('users', {
                            'username': nuevo_usuario,
                            'role': rol,
                            'password_hash': hash_password(nueva_contrasena)
                        })
                        st.success(f"✅ Usuario {nuevo_usuario} agregado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab3:
        st.header("Configuracion de Seguridad")
        
        st.subheader("🔐 Politicas de Contrasena")
        longitud_minima = st.slider("Longitud minima de contrasena", 6, 20, 8)
        requerir_mayusculas = st.checkbox("Requerir mayusculas", True)
        requerir_numeros = st.checkbox("Requerir numeros", True)
        expiracion = st.selectbox("Expiracion de contrasena (dias)", ["30", "60", "90", "Nunca"])
        
        st.subheader("🔒 Configuracion de Sesion")
        tiempo_inactividad = st.slider("Tiempo de inactividad (minutos)", 5, 120, 30)
        max_intentos = st.slider("Maximo de intentos fallidos", 3, 10, 5)
        
        if st.button("🔒 Aplicar Configuracion de Seguridad"):
            st.success("✅ Configuracion de seguridad aplicada")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 13. NAVEGACION PRINCIPAL
# ==============================================================================

def main():
    """Funcion principal de la aplicacion"""
    # Inicializar estado
    initialize_session_state()
    
    # Mapeo de paginas
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
    
    # Mostrar pagina actual
    current_page = st.session_state.current_page
    
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

if __name__ == "__main__":
    main()
