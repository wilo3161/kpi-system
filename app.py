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
from dataclasses import dataclass, asdict
import json

# ==============================================================================
# CONFIGURACION Y CONSTANTES MEJORADAS
# ==============================================================================

# Constantes de infraestructura
TIENDAS_REGULARES = 42
PRICE_CLUBS = 5
TIENDA_WEB = 1
VENTAS_POR_MAYOR = 1
FALLAS = 1

# Keywords para clasificación de destinos
PRICE_KEYWORDS = ['PRICE', 'OIL', 'PRICE CLUB', 'PRICECLUB']
WEB_KEYWORDS = ['WEB', 'TIENDA MOVIL', 'MOVIL', 'ONLINE', 'ECOMMERCE', 'E-COMMERCE']
FALLAS_KEYWORDS = ['FALLAS', 'DEFECTUOSO', 'DAÑADO', 'MALO']
VENTAS_MAYOR_KEYWORDS = ['MAYOR', 'MAYORISTA', 'WHOLESALE', 'DISTRIBUIDOR']

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
    'RIOCENTRO NORTE', 'SAN LUIS', 'SANTO DOMINGO', 'AEROPOSTALE', 'AERO'
]

# ==============================================================================
# DICCIONARIOS DE CLASIFICACION TEXTIL OPTIMIZADOS
# ==============================================================================

GENDER_MAP = {
    # Mujer
    'GIRLS': 'Mujer', 'TOPMUJER': 'Mujer', 'WOMEN': 'Mujer', 
    'LADIES': 'Mujer', 'FEMALE': 'Mujer', 'MUJER': 'Mujer',
    'WOMAN': 'Mujer', 'CHICA': 'Mujer', 'DAMA': 'Mujer', 'DAMAS': 'Mujer',
    'FEMENINO': 'Mujer', 'FEMENINA': 'Mujer', 'NIÑA': 'Niña', 'NIÑAS': 'Niña',
    # Hombre  
    'GUYS': 'Hombre', 'MEN': 'Hombre', 'MAN': 'Hombre', 
    'HOMBRE': 'Hombre', 'MALE': 'Hombre', 'CHICO': 'Hombre', 'CABALLERO': 'Hombre',
    'MASCULINO': 'Hombre', 'NIÑO': 'Niño', 'NIÑOS': 'Niño', 'BOYS': 'Niño',
    # Unisex/Otros
    'UNISEX': 'Unisex', 'UNISEXO': 'Unisex', 'KIDS': 'Niño/a', 'CHILD': 'Niño/a',
    'CHILDREN': 'Niño/a', 'INFANT': 'Bebé', 'BABY': 'Bebé', 'BEBE': 'Bebé',
    'JUNIOR': 'Junior', 'JR': 'Junior'
}

CATEGORY_MAP = {
    # Superiores
    'TEES': 'Camiseta', 'TEE': 'Camiseta', 'T-SHIRT': 'Camiseta', 'TSHIRT': 'Camiseta',
    'TANK': 'Tank Top', 'TANK TOP': 'Tank Top', 'TANKTOP': 'Tank Top',
    'TOP': 'Top', 'TOPS': 'Top', 'BARE': 'Top', 'CORE': 'Básico',
    'GRAPHIC': 'Gráfico', 'GRAPHICS': 'Gráfico', 'ESTAMPADO': 'Gráfico',
    'POLO': 'Polo', 'POLOS': 'Polo', 'SHIRT': 'Camisa', 'CAMISA': 'Camisa',
    'BUTTON-DOWN': 'Camisa', 'BUTTONDOWN': 'Camisa', 'BUTTON DOWN': 'Camisa',
    'BLOUSE': 'Blusa', 'BLUSA': 'Blusa', 'BODYSUIT': 'Body', 'BODY': 'Body',
    'HOODIE': 'Hoodie', 'SWEATSHIRT': 'Sudadera', 'SWEATER': 'Suéter', 'PULLOVER': 'Suéter',
    'JACKET': 'Chaqueta', 'JACKETS': 'Chaqueta', 'CHAQUETA': 'Chaqueta', 'ROMPEVIENTOS': 'Chaqueta',
    'BLAZER': 'Blazer', 'SACO': 'Saco', 'CARDIGAN': 'Cárdigan', 'VEST': 'Chaleco',
    'CHALECO': 'Chaleco', 'FLEECE': 'Polar', 'POLAR': 'Polar',
    # Inferiores
    'PANTS': 'Pantalón', 'PANT': 'Pantalón', 'PANTALON': 'Pantalón', 'TROUSERS': 'Pantalón',
    'JEANS': 'Jeans', 'JEAN': 'Jeans', 'DENIM': 'Jeans', 'JEGGING': 'Jegging',
    'BOOTCUT': 'Bootcut', 'SKINNY': 'Skinny', 'STRAIGHT': 'Straight', 
    'FLARE': 'Flare', 'WIDE': 'Wide Leg', 'JOGGER': 'Jogger', 'JOGGERS': 'Jogger',
    'SHORTS': 'Short', 'SHORT': 'Short', 'BERMUDA': 'Bermuda', 'BERMUDAS': 'Bermuda',
    'CAPRI': 'Capri', 'CROP': 'Crop', 'CROPPED': 'Crop', 'LEGGING': 'Legging', 'LEGGINGS': 'Legging',
    # Vestidos y faldas
    'DRESS': 'Vestido', 'DRESSES': 'Vestido', 'SUNDRESS': 'Vestido', 'VESTIDO': 'Vestido',
    'SKIRT': 'Falda', 'FALDA': 'Falda', 'SKORT': 'Skort', 'JUMPSUIT': 'Jumpsuit',
    'OVERALL': 'Overol', 'OVERALLS': 'Overol', 'ENTERIZO': 'Enterizo',
    # Ropa interior y accesorios
    'BVD': 'Ropa Interior', 'BOXER': 'Boxer', 'BOXERS': 'Boxer', 'BRIEF': 'Brief',
    'UNDERWEAR': 'Ropa Interior', 'PANTY': 'Panty', 'PANTIES': 'Panty', 'BRALETTE': 'Bralette',
    'BRALET': 'Bralette', 'BRA': 'Brassiere', 'SOCKS': 'Medias', 'SOCK': 'Medias',
    'MEDIAS': 'Medias', 'TIGHTS': 'Pantyhose', 'LEGGINGS': 'Legging',
    # Accesorios
    'BELT': 'Cinturón', 'BELTS': 'Cinturón', 'CINTURON': 'Cinturón',
    'HAT': 'Gorro', 'CAP': 'Gorra', 'GORRO': 'Gorro', 'GORRA': 'Gorra',
    'BEANIE': 'Beanie', 'SCARF': 'Bufanda', 'GLOVES': 'Guantes', 'MITTENS': 'Mitones',
    'BAG': 'Bolso', 'BAGS': 'Bolso', 'MOCHILA': 'Mochila', 'BACKPACK': 'Mochila',
    'WALLET': 'Billetera', 'CARTERA': 'Cartera', 'WATCH': 'Reloj', 'RELOJ': 'Reloj',
    'SUNGLASSES': 'Gafas', 'LENTES': 'Gafas', 'GLASSES': 'Gafas', 'JEWELRY': 'Joyería',
    # Calzado
    'SHOES': 'Zapatos', 'SHOE': 'Zapatos', 'ZAPATOS': 'Zapatos', 'ZAPATO': 'Zapatos',
    'SNEAKERS': 'Tenis', 'TENIS': 'Tenis', 'BOOTS': 'Botas', 'BOTAS': 'Botas',
    'SANDALS': 'Sandalias', 'SANDALIAS': 'Sandalias', 'SLIPPERS': 'Pantuflas',
    # Otros
    'SWIMWEAR': 'Traje de Baño', 'BIKINI': 'Bikini', 'TRUNKS': 'Short de Baño',
    'PAJAMAS': 'Pijama', 'ROBE': 'Bata', 'ACTIVE': 'Activewear', 'SPORT': 'Deportivo'
}

COLOR_MAP = {
    # Neutros
    'BLACK': 'Negro', 'BLACK/DARK': 'Negro', 'DARK BLACK': 'Negro', 'NEGRO': 'Negro',
    'WHITE': 'Blanco', 'WHITE/LIGHT': 'Blanco', 'BLANCO': 'Blanco', 'CREAM': 'Crema',
    'GRAY': 'Gris', 'GREY': 'Gris', 'GRIS': 'Gris', 'CHARCOAL': 'Gris Carbón',
    'SILVER': 'Plateado', 'GOLD': 'Dorado', 'BEIGE': 'Beige', 'KHAKI': 'Caqui',
    'TAN': 'Café Claro', 'BROWN': 'Café', 'MARRON': 'Café', 'COFFEE': 'Café',
    'NAVY': 'Azul Marino', 'AZUL MARINO': 'Azul Marino',
    # Colores primarios
    'RED': 'Rojo', 'ROJO': 'Rojo', 'CRIMSON': 'Carmesí', 'BURGUNDY': 'Borgoña',
    'RASPBERRY': 'Frambuesa', 'EARTH RED': 'Rojo Tierra', 'TERRACOTTA': 'Terracota',
    'BLUE': 'Azul', 'AZUL': 'Azul', 'ROYAL': 'Azul Rey', 'COBALT': 'Cobalto',
    'LIGHT BLUE': 'Azul Claro', 'SKY': 'Celeste', 'AZUL CLARO': 'Azul Claro',
    'TURQUOISE': 'Turquesa', 'TEAL': 'Verde Azulado', 'MINT': 'Menta',
    'GREEN': 'Verde', 'VERDE': 'Verde', 'GREEN GABLES': 'Verde Bosque',
    'OLIVE': 'Oliva', 'LIME': 'Lima', 'FOREST': 'Verde Bosque',
    'YELLOW': 'Amarillo', 'AMARILLO': 'Amarillo', 'MUSTARD': 'Mostaza', 'GOLDEN': 'Dorado',
    # Secundarios
    'PINK': 'Rosa', 'ROSA': 'Rosa', 'HOT PINK': 'Rosa Fuerte', 'FUCHSIA': 'Fucsia',
    'BLUSH': 'Rosa Palo', 'SALMON': 'Salmón', 'CORAL': 'Coral',
    'PURPLE': 'Morado', 'MORADO': 'Morado', 'VIOLET': 'Violeta', 'LILAC': 'Lila',
    'LAVENDER': 'Lavanda', 'PLUM': 'Ciruela',
    'ORANGE': 'Naranja', 'NARANJA': 'Naranja', 'PEACH': 'Durazno', 'TANGERINE': 'Mandarina',
    # Especiales
    'BLEACH': 'Blanqueado', 'LIGHT WASH': 'Lavado Claro', 'DARK WASH': 'Lavado Oscuro',
    'ACID': 'Ácido', 'VINTAGE': 'Vintage', 'DISTRESSED': 'Desgastado',
    'CAMO': 'Camuflado', 'CAMOUFLAGE': 'Camuflado', 'CAMOFLAJE': 'Camuflado',
    'TIE DYE': 'Tie Dye', 'TIEDYE': 'Tie Dye', 'MULTI': 'Multicolor', 
    'MULTICOLOR': 'Multicolor', 'MIXED': 'Mixto', 'STRIPED': 'Rayado', 
    'RAYAS': 'Rayado', 'CHECK': 'Cuadros', 'PLAID': 'Cuadros', 'CUADROS': 'Cuadros',
    'FLORAL': 'Floral', 'PRINT': 'Estampado', 'SOLID': 'Sólido', 'LISO': 'Liso'
}

SIZE_HIERARCHY = [
    'XXS', '2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', 'XXL', '3XL', 'XXXL', 
    '4XL', '5XL', '6XL', 'OS', 'ONE SIZE', 'UNICA', 'U', 'N/A', 'NA',
    '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', 
    '39', '40', '41', '42', '43', '44', '0', '2', '4', '6', '8', '10', 
    '12', '14', '16', '18', '20', '22', '24', '26'
]

IGNORE_WORDS = {
    'AERO', 'OF', 'THE', 'AND', 'IN', 'WITH', 'FOR', 'BY', 'ON', 'AT', 'TO', 
    'EST', 'TEES', 'AEROPOSTALE', 'PRICE', 'CLUB', 'NEW', 'NUOVO', 'CLASSIC',
    'ORIGINAL', 'BASIC', 'STANDARD', 'PREMIUM', 'ESSENTIAL', 'SIGNATURE'
}

WAREHOUSE_GROUPS = {
    'PRICE': 'Price Club',
    'AERO': 'Aeropostale',
    'MALL': 'Centro Comercial',
    'RIOCENTRO': 'Riocentro',
    'CONDADO': 'Condado',
    'SAN': 'San',
    'LOS': 'Los',
    'CCI': 'CCI',
    'DAULE': 'Daule',
    'MANTA': 'Manta',
    'AMBATO': 'Ambato'
}

# ==============================================================================
# CLASES DE PROCESAMIENTO AVANZADO
# ==============================================================================

class TextileClassifier:
    """Clasificador inteligente para productos textiles - V2.0"""
    
    def __init__(self):
        self.gender_map = GENDER_MAP
        self.category_map = CATEGORY_MAP
        self.color_map = COLOR_MAP
        self.size_hierarchy = SIZE_HIERARCHY
        self.ignore_words = IGNORE_WORDS
        
    def classify_product(self, product_name: str) -> Dict:
        """Clasificación completa del producto con lógica mejorada"""
        if not product_name or not isinstance(product_name, str):
            return self._get_empty_classification()
        
        product_name = str(product_name).upper().strip()
        
        # Preprocesamiento: eliminar caracteres especiales pero mantener espacios
        product_clean = re.sub(r'[^\w\s]', ' ', product_name)
        words = [w for w in product_clean.split() if w and len(w) > 1]
        
        classification = {
            'Genero': 'Unisex',
            'Categoria': 'General',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'Única',
            'Material': '',
            'Estilo': '',
            'Temporada': ''
        }
        
        # Detección en orden de prioridad
        classification['Genero'] = self._detect_gender(words, product_name)
        category_info = self._detect_category(words, product_name)
        classification['Categoria'] = category_info['categoria']
        classification['Subcategoria'] = category_info['subcategoria']
        classification['Color'] = self._detect_color(words, product_name)
        classification['Talla'] = self._detect_size(words, product_name)
        style_info = self._detect_style_material(words)
        classification['Material'] = style_info['material']
        classification['Estilo'] = style_info['estilo']
        classification['Temporada'] = style_info['temporada']
        
        return self._clean_classification(classification)
    
    def _detect_gender(self, words: List[str], full_text: str) -> str:
        """Detección de género con contexto mejorado"""
        # Buscar palabras exactas primero
        for word in words:
            if word in self.gender_map:
                return self.gender_map[word]
        
        # Búsqueda por contención para casos compuestos
        text = full_text
        female_indicators = ['WOMEN', 'LADIES', 'FEMALE', 'MUJER', 'DAMA', 'GIRL', 'NIÑA', 'FEMENINO']
        male_indicators = ['MEN', 'MAN', 'MALE', 'HOMBRE', 'CABALLERO', 'BOY', 'NIÑO', 'MASCULINO']
        
        female_score = sum(1 for ind in female_indicators if ind in text)
        male_score = sum(1 for ind in male_indicators if ind in text)
        
        if female_score > male_score:
            return 'Mujer'
        elif male_score > female_score:
            return 'Hombre'
        
        # Inferir por categoría si no hay indicadores explícitos
        if any(cat in text for cat in ['DRESS', 'SKIRT', 'FALDA', 'VESTIDO', 'BLUSA']):
            return 'Mujer'
        if any(cat in text for cat in ['BOXER', 'BRIEF', 'MEN']):
            return 'Hombre'
            
        return 'Unisex'
    
    def _detect_category(self, words: List[str], full_text: str) -> Dict:
        """Detección de categoría con análisis de contexto"""
        categoria = 'General'
        subcategorias = []
        
        # Buscar categorías principales
        found_categories = []
        for word in words:
            if word in self.category_map:
                found_categories.append(self.category_map[word])
        
        # Si no encontró por palabra exacta, buscar en texto completo
        if not found_categories:
            for key, value in self.category_map.items():
                if key in full_text:
                    found_categories.append(value)
        
        # Priorizar categorías principales
        if found_categories:
            # Prioridad de categorías
            priority = ['Jeans', 'Pantalón', 'Camiseta', 'Polo', 'Camisa', 'Vestido', 
                       'Chaqueta', 'Short', 'Hoodie', 'Suéter']
            
            for priority_cat in priority:
                if priority_cat in found_categories:
                    categoria = priority_cat
                    break
            else:
                categoria = found_categories[0]
            
            # Subcategorías son las demás categorías encontradas
            other_cats = [cat for cat in found_categories if cat != categoria]
            if other_cats:
                subcategorias = other_cats
        
        # Detectar subcategorías adicionales de palabras no mapeadas
        for word in words:
            if word not in self.category_map and word not in self.ignore_words and len(word) > 2:
                if word not in [c.upper().replace(' ', '') for c in found_categories]:
                    subcategorias.append(word.capitalize())
        
        return {
            'categoria': categoria, 
            'subcategoria': ', '.join(list(dict.fromkeys(subcategorias)))  # Eliminar duplicados manteniendo orden
        }
    
    def _detect_color(self, words: List[str], full_text: str) -> str:
        """Detección de color con manejo de compuestos"""
        # Buscar colores exactos
        for word in words:
            if word in self.color_map:
                return self.color_map[word]
        
        # Buscar en texto completo (para colores de dos palabras)
        for eng_color, esp_color in self.color_map.items():
            if ' ' in eng_color and eng_color in full_text:
                return esp_color
        
        # Búsqueda parcial para colores simples
        for eng_color, esp_color in self.color_map.items():
            if ' ' not in eng_color and eng_color in full_text:
                return esp_color
        
        # Detección de patrones de lavado/denim
        if any(x in full_text for x in ['WASH', 'LAVADO', 'BLEACH']):
            if 'DARK' in full_text or 'OSCuro' in full_text:
                return 'Lavado Oscuro'
            elif 'LIGHT' in full_text or 'CLARO' in full_text:
                return 'Lavado Claro'
            else:
                return 'Lavado Medio'
        
        return 'No Especificado'
    
    def _detect_size(self, words: List[str], full_text: str) -> str:
        """Detección de talla mejorada"""
        # Crear patrón de búsqueda con delimitadores
        text_with_delim = f' {full_text} '
        
        for size in self.size_hierarchy:
            # Buscar con delimitadores de espacio o no alfanuméricos
            pattern = rf'[\s\W]{re.escape(size)}[\s\W]'
            if re.search(pattern, text_with_delim):
                return size
        
        # Buscar tallas numéricas de pantalón (28-44)
        numeric_sizes = re.findall(r'\b(2[8-9]|[3-4][0-9])\b', full_text)
        if numeric_sizes:
            return numeric_sizes[0]
        
        # Buscar tallas US (0, 2, 4, 6...)
        us_sizes = re.findall(r'\b([02468]|1[02468]|2[024])\b', full_text)
        if us_sizes:
            return us_sizes[0]
        
        return 'Única'
    
    def _detect_style_material(self, words: List[str]) -> Dict:
        """Detección de material, estilo y temporada"""
        material = ''
        estilo = ''
        temporada = ''
        
        # Materiales
        materials = {
            'COTTON': 'Algodón', 'POLYESTER': 'Poliéster', 'DENIM': 'Denim',
            'JEAN': 'Denim', 'LEATHER': 'Cuero', 'WOOL': 'Lana', 
            'SILK': 'Seda', 'LINEN': 'Lino', 'NYLON': 'Nylon', 'SPANDEX': 'Spandex',
            'RAYON': 'Rayón', 'VISCOSE': 'Viscosa', 'ACRYLIC': 'Acrílico',
            'FLEECE': 'Polar', 'KNIT': 'Tejido', 'WOVEN': 'Tejido', 'JERSEY': 'Jersey'
        }
        
        for word in words:
            if word in materials:
                material = materials[word]
                break
        
        # Estilos/Temporadas
        style_keywords = {
            'GRAPHIC': 'Gráfico', 'PRINT': 'Estampado', 'PRINTED': 'Estampado',
            'SOLID': 'Liso', 'PLAIN': 'Liso', 'STRIPED': 'Rayado', 'STRIPE': 'Rayado',
            'CHECK': 'Cuadros', 'PLAID': 'Cuadros', 'FLORAL': 'Floral',
            'BASIC': 'Básico', 'ESSENTIAL': 'Esencial', 'PREMIUM': 'Premium',
            'VINTAGE': 'Vintage', 'DISTRESSED': 'Desgastado', 'DESTROYED': 'Roto',
            'EMBROIDERED': 'Bordado', 'CROCHET': 'Crochet', 'LACE': 'Encaje'
        }
        
        season_keywords = {
            'SUMMER': 'Verano', 'WINTER': 'Invierno', 'SPRING': 'Primavera',
            'FALL': 'Otoño', 'AUTUMN': 'Otoño', 'VERANO': 'Verano', 
            'INVIERNO': 'Invierno', 'PRIMAVERA': 'Primavera', 'OTOÑO': 'Otoño'
        }
        
        for word in words:
            if word in style_keywords and not estilo:
                estilo = style_keywords[word]
            if word in season_keywords and not temporada:
                temporada = season_keywords[word]
        
        return {'material': material, 'estilo': estilo, 'temporada': temporada}
    
    def _clean_classification(self, classification: Dict) -> Dict:
        """Limpieza y estandarización final"""
        # Mapeo de tallas alternativas
        size_map = {
            'XSMALL': 'XS', 'SMALL': 'S', 'MEDIUM': 'M', 'MED': 'M',
            'LARGE': 'L', 'XLARGE': 'XL', 'XXLARGE': '2XL', 'XXXLARGE': '3XL',
            '2XS': 'XXS', 'XXL': '2XL', 'XXXL': '3XL', 'XXXXL': '4XL',
            'ONE SIZE': 'Única', 'OS': 'Única', 'UNICA': 'Única', 'U': 'Única',
            'N/A': 'Única', 'NA': 'Única'
        }
        
        if classification['Talla'] in size_map:
            classification['Talla'] = size_map[classification['Talla']]
        
        # Limpiar espacios
        for key, value in classification.items():
            if isinstance(value, str):
                classification[key] = value.strip().strip(',')
        
        return classification
    
    def _get_empty_classification(self) -> Dict:
        """Clasificación por defecto"""
        return {
            'Genero': 'No Identificado',
            'Categoria': 'No Identificado',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'No Especificado',
            'Material': '',
            'Estilo': '',
            'Temporada': ''
        }


class TransferHistoryManager:
    """Gestor de histórico de transferencias para almacenamiento interno"""
    
    def __init__(self):
        self.storage_key = 'transferencias_historico'
        self._init_storage()
    
    def _init_storage(self):
        """Inicializa el almacenamiento en session_state"""
        if self.storage_key not in st.session_state:
            st.session_state[self.storage_key] = {
                'registros': [],
                'ultima_actualizacion': None,
                'metricas_acumuladas': {
                    'total_transferencias': 0,
                    'total_unidades': 0,
                    'por_categoria': {},
                    'por_genero': {},
                    'por_color': {},
                    'evolucion_diaria': []
                }
            }
    
    def add_transfer_record(self, df: pd.DataFrame, fecha: Optional[datetime] = None, 
                           categoria_dia: Optional[str] = None):
        """Agrega un registro de transferencia al histórico"""
        if fecha is None:
            fecha = datetime.now()
        
        record = {
            'fecha': fecha.isoformat(),
            'fecha_str': fecha.strftime('%Y-%m-%d'),
            'registros_count': len(df),
            'total_unidades': int(df['Cantidad_Entera'].sum()) if 'Cantidad_Entera' in df.columns else 0,
            'categoria_dia': categoria_dia,
            'resumen': {}
        }
        
        # Agregar resumen por categoría si existe
        if 'Categoria' in df.columns and 'Cantidad_Entera' in df.columns:
            resumen_cat = df.groupby('Categoria')['Cantidad_Entera'].sum().to_dict()
            record['resumen'] = {k: int(v) for k, v in resumen_cat.items()}
        
        st.session_state[self.storage_key]['registros'].append(record)
        st.session_state[self.storage_key]['ultima_actualizacion'] = fecha.isoformat()
        
        # Actualizar métricas acumuladas
        self._update_accumulated_metrics(df)
    
    def _update_accumulated_metrics(self, df: pd.DataFrame):
        """Actualiza métricas acumuladas con nuevos datos"""
        metrics = st.session_state[self.storage_key]['metricas_acumuladas']
        
        if 'Cantidad_Entera' in df.columns:
            metrics['total_unidades'] += int(df['Cantidad_Entera'].sum())
        
        # Acumular por categoría
        if 'Categoria' in df.columns:
            for cat, cant in df.groupby('Categoria')['Cantidad_Entera'].sum().items():
                metrics['por_categoria'][cat] = metrics['por_categoria'].get(cat, 0) + int(cant)
        
        # Acumular por género si existe clasificación
        if 'Genero' in df.columns:
            for gen, cant in df.groupby('Genero')['Cantidad_Entera'].sum().items():
                metrics['por_genero'][gen] = metrics['por_genero'].get(gen, 0) + int(cant)
        
        # Acumular por color si existe
        if 'Color' in df.columns:
            for color, cant in df.groupby('Color')['Cantidad_Entera'].sum().items():
                metrics['por_color'][color] = metrics['por_color'].get(color, 0) + int(cant)
    
    def get_historical_data(self, dias: int = 30) -> pd.DataFrame:
        """Obtiene datos históricos de los últimos N días"""
        registros = st.session_state[self.storage_key]['registros']
        if not registros:
            return pd.DataFrame()
        
        df_hist = pd.DataFrame(registros)
        df_hist['fecha'] = pd.to_datetime(df_hist['fecha'])
        
        # Filtrar por días
        fecha_limite = datetime.now() - timedelta(days=dias)
        return df_hist[df_hist['fecha'] >= fecha_limite]
    
    def get_accumulated_metrics(self) -> Dict:
        """Obtiene métricas acumuladas"""
        return st.session_state[self.storage_key]['metricas_acumuladas']
    
    def clear_history(self):
        """Limpia el histórico"""
        st.session_state[self.storage_key] = {
            'registros': [],
            'ultima_actualizacion': None,
            'metricas_acumuladas': {
                'total_transferencias': 0,
                'total_unidades': 0,
                'por_categoria': {},
                'por_genero': {},
                'por_color': {},
                'evolucion_diaria': []
            }
        }


class TransitDataProcessor:
    """Procesador especializado para datos de tránsito con clasificación textil"""
    
    def __init__(self):
        self.classifier = TextileClassifier()
    
    def process_transit_file(self, file, df_base=None) -> pd.DataFrame:
        """Procesa archivo de tránsito con clasificación inteligente completa"""
        try:
            # Leer archivo
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            
            if df.empty:
                st.error("❌ El archivo está vacío")
                return pd.DataFrame()
            
            # Normalizar nombres de columnas
            df.columns = [str(col).strip() for col in df.columns]
            
            # Detectar columnas automáticamente
            col_mapping = self._detect_columns(df)
            
            if not col_mapping.get('codigo'):
                st.error(f"❌ No se encontró columna de código. Columnas: {list(df.columns)}")
                return pd.DataFrame()
            
            if not col_mapping.get('cantidad'):
                st.error(f"❌ No se encontró columna de cantidad. Columnas: {list(df.columns)}")
                return pd.DataFrame()
            
            # Renombrar columnas a estándar
            rename_map = {}
            if col_mapping.get('codigo'):
                rename_map[col_mapping['codigo']] = 'CODIGO'
            if col_mapping.get('cantidad'):
                rename_map[col_mapping['cantidad']] = 'CANTIDAD'
            if col_mapping.get('producto'):
                rename_map[col_mapping['producto']] = 'PRODUCTO_ORIGINAL'
            if col_mapping.get('bodega'):
                rename_map[col_mapping['bodega']] = 'BODEGA'
            
            df = df.rename(columns=rename_map)
            
            # Limpiar y normalizar datos
            df['CODIGO'] = df['CODIGO'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce').fillna(0)
            
            # Merge con base si existe
            if df_base is not None and not df_base.empty:
                df = self._merge_with_base(df, df_base)
            
            # Asegurar columna PRODUCTO para clasificación
            if 'PRODUCTO' not in df.columns:
                if 'PRODUCTO_ORIGINAL' in df.columns:
                    df['PRODUCTO'] = df['PRODUCTO_ORIGINAL']
                else:
                    df['PRODUCTO'] = df['CODIGO']
            
            # Aplicar clasificación textil completa
            df = self._apply_textile_classification(df)
            
            # Clasificar grupo de bodega
            if 'BODEGA' in df.columns:
                df['GRUPO_BODEGA'] = df['BODEGA'].apply(self._group_warehouse)
            else:
                df['GRUPO_BODEGA'] = 'Sin Especificar'
            
            # Agregar metadata
            df['FECHA_PROCESAMIENTO'] = datetime.now()
            df['ARCHIVO_ORIGEN'] = file.name
            
            st.success(f"✅ Procesados {len(df)} registros con clasificación completa")
            return df
            
        except Exception as e:
            st.error(f"❌ Error al procesar archivo: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return pd.DataFrame()
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict:
        """Detección robusta de columnas"""
        cols = df.columns.tolist()
        cols_upper = [str(col).upper().strip() for col in cols]
        
        mapping = {'codigo': None, 'cantidad': None, 'producto': None, 'bodega': None}
        
        # Patrones de búsqueda expandidos
        patterns = {
            'codigo': ['CODIGO', 'CÓDIGO', 'CODIGO PRODUCTO', 'SKU', 'ITEM', 'CODE', 'ID', 
                      'REFERENCIA', 'COD_PRODUCTO', 'PRODUCT_ID', 'ARTICULO', 'COD'],
            'cantidad': ['CANTIDAD', 'QTY', 'QUANTITY', 'UNIDADES', 'UND', 'UNDS', 'UNID', 
                        'TOTAL', 'CANT', 'Q', 'QTY_TOTAL', 'PIEZAS', 'PRENDAS'],
            'producto': ['PRODUCTO', 'DESCRIPCION', 'DESCRIPCIÓN', 'NOMBRE', 'DESC', 
                        'ITEM_NAME', 'ARTICULO', 'DETALLE', 'ITEM DESCRIPTION', 'NOMBRE PRODUCTO'],
            'bodega': ['BODEGA', 'DESTINO', 'BODEGA RECIBE', 'BODEGA DESTINO', 
                      'SUCURSAL', 'TIENDA', 'UBICACION', 'UBICACIÓN', 'DESTINO', 'ALMACEN']
        }
        
        for field, pattern_list in patterns.items():
            # Búsqueda exacta primero
            for i, col_upper in enumerate(cols_upper):
                if any(p == col_upper for p in pattern_list):
                    mapping[field] = cols[i]
                    break
            
            # Si no encontró, búsqueda parcial
            if not mapping[field]:
                for i, col_upper in enumerate(cols_upper):
                    if any(p in col_upper for p in pattern_list):
                        # Excluir totales agregados
                        if field == 'cantidad' and any(x in col_upper for x in ['TOTAL GENERAL', 'GRAN TOTAL', 'SUM']):
                            continue
                        mapping[field] = cols[i]
                        break
        
        return mapping
    
    def _merge_with_base(self, df_transit: pd.DataFrame, df_base: pd.DataFrame) -> pd.DataFrame:
        """Merge inteligente con archivo base"""
        try:
            df_base = df_base.copy()
            df_base.columns = [str(col).strip() for col in df_base.columns]
            base_cols_upper = [str(col).upper().strip() for col in df_base.columns]
            
            # Detectar columna de código en base
            code_patterns = ['CODIGO', 'CÓDIGO', 'SKU', 'ID', 'REFERENCIA', 'PRODUCTO', 'ARTICULO']
            code_col = None
            
            for i, col_upper in enumerate(base_cols_upper):
                if any(p in col_upper for p in code_patterns):
                    code_col = df_base.columns[i]
                    break
            
            if not code_col:
                st.warning("⚠️ No se encontró columna de código en base")
                return df_transit
            
            # Limpiar código en base
            df_base[code_col] = df_base[code_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            
            # Detectar otras columnas útiles
            dept_col = self._find_column(base_cols_upper, df_base.columns, 
                                       ['DEPARTAMENTO', 'DEPTO', 'CATEGORIA', 'LINEA', 'GRUPO', 'FAMILIA'])
            desc_col = self._find_column(base_cols_upper, df_base.columns,
                                       ['PRODUCTO', 'DESCRIPCION', 'NOMBRE', 'DESC', 'ARTICULO'])
            
            # Preparar merge
            merge_cols = [code_col]
            if dept_col:
                merge_cols.append(dept_col)
            if desc_col and desc_col != code_col:
                merge_cols.append(desc_col)
            
            # Realizar merge
            df_base_subset = df_base[merge_cols].drop_duplicates(subset=[code_col])
            df_merged = df_transit.merge(df_base_subset, left_on='CODIGO', right_on=code_col, how='left')
            
            # Renombrar columnas resultantes
            if desc_col:
                df_merged = df_merged.rename(columns={desc_col: 'PRODUCTO'})
            if dept_col:
                df_merged = df_merged.rename(columns={dept_col: 'DEPARTAMENTO_BASE'})
            
            # Limpiar columna de código duplicada
            if code_col in df_merged.columns and code_col != 'CODIGO':
                df_merged = df_merged.drop(columns=[code_col])
            
            return df_merged
            
        except Exception as e:
            st.warning(f"⚠️ Error en merge: {str(e)}")
            return df_transit
    
    def _find_column(self, cols_upper: List[str], original_cols: List[str], patterns: List[str]) -> Optional[str]:
        """Encuentra columna por patrones"""
        for i, col_upper in enumerate(cols_upper):
            if any(p in col_upper for p in patterns):
                return original_cols[i]
        return None
    
    def _apply_textile_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica clasificación textil a todo el DataFrame"""
        if 'PRODUCTO' not in df.columns:
            df['PRODUCTO'] = df['CODIGO']
        
        # Vectorizar clasificación para performance
        classifications = df['PRODUCTO'].apply(lambda x: self.classifier.classify_product(x))
        class_df = pd.DataFrame(classifications.tolist())
        
        # Concatenar resultados
        df = pd.concat([df.reset_index(drop=True), class_df], axis=1)
        
        return df
    
    def _group_warehouse(self, warehouse_name) -> str:
        """Clasificación de grupo de bodega/tienda"""
        if pd.isna(warehouse_name):
            return 'Otros'
        
        warehouse_upper = str(warehouse_name).upper()
        
        # Clasificación específica
        if any(kw in warehouse_upper for kw in PRICE_KEYWORDS):
            return 'Price Club'
        elif any(kw in warehouse_upper for kw in WEB_KEYWORDS):
            return 'Tienda Web/Online'
        elif any(kw in warehouse_upper for kw in FALLAS_KEYWORDS):
            return 'Fallas/Devoluciones'
        elif any(kw in warehouse_upper for kw in VENTAS_MAYOR_KEYWORDS):
            return 'Ventas por Mayor'
        
        # Tiendas Aeropostale
        aero_indicators = ['AERO', 'AEROPOSTALE', 'MALL', 'CENTRO', 'SHOPPING', 
                          'PLAZA', 'RIOCENTRO', 'CONDADO', 'CCI']
        if any(kw in warehouse_upper for kw in aero_indicators):
            return 'Tiendas Aeropostale'
        
        return 'Otros/No Clasificado'


# ==============================================================================
# FUNCIONES DE PROCESAMIENTO DE TRANSFERENCIAS DIARIAS (MEJORADAS)
# ==============================================================================

def clasificar_transferencia_mejorada(row: pd.Series) -> str:
    """Clasificación mejorada de transferencias por destino"""
    # Buscar en múltiples posibles columnas de destino
    sucursal = ''
    for col in ['Sucursal Destino', 'Bodega Destino', 'BODEGA', 'DESTINO', 'SUCURSAL']:
        if col in row and pd.notna(row[col]):
            sucursal = str(row[col]).upper()
            break
    
    cantidad = 0
    for col in ['Cantidad_Entera', 'Cantidad Prendas', 'CANTIDAD', 'TOTAL']:
        if col in row:
            try:
                cantidad = float(row[col]) if pd.notna(row[col]) else 0
                break
            except:
                continue
    
    # Regla de fundas: cantidades grandes y redondas
    if cantidad >= 500 and cantidad % 100 == 0:
        return 'Fundas'
    
    # Clasificación por keywords
    if any(kw in sucursal for kw in PRICE_KEYWORDS):
        return 'Price Club'
    if any(kw in sucursal for kw in WEB_KEYWORDS):
        return 'Tienda Web'
    if any(kw in sucursal for kw in FALLAS_KEYWORDS):
        return 'Fallas'
    if any(kw in sucursal for kw in VENTAS_MAYOR_KEYWORDS):
        return 'Ventas por Mayor'
    
    # Tiendas regulares
    if any(tienda.upper() in sucursal for tienda in TIENDAS_REGULARES_LISTA):
        return 'Tiendas'
    
    # Fallback por keywords genéricos de tienda
    tiendas_kw = ['AERO', 'MALL', 'CENTRO', 'SHOPPING', 'PLAZA', 'RIOCENTRO', 'CONDADO', 'CCI']
    if any(kw in sucursal for kw in tiendas_kw):
        return 'Tiendas'
    
    return 'Otros/No Clasificado'


def extraer_entero_mejorado(valor) -> int:
    """Extracción robusta de valores enteros"""
    try:
        if pd.isna(valor):
            return 0
        if isinstance(valor, (int, float)):
            return int(valor)
        if isinstance(valor, str):
            # Limpiar formato latino (1.234,56 -> 1234.56)
            valor_limpio = valor.replace(',', '').replace("'", "").replace('"', '').strip()
            # Manejar notación científica
            if 'e' in valor_limpio.lower():
                return int(float(valor_limpio))
            return int(float(valor_limpio))
        return 0
    except Exception:
        return 0


def procesar_transferencias_diarias_mejorado(df: pd.DataFrame, 
                                           history_manager: Optional[TransferHistoryManager] = None) -> Optional[Dict]:
    """Procesamiento completo de transferencias diarias con métricas extendidas"""
    try:
        df = df.copy()
        
        # Limpiar secuenciales
        if 'Secuencial' in df.columns:
            df = df.dropna(subset=['Secuencial'])
            df['Secuencial'] = df['Secuencial'].astype(str).str.strip()
            df = df[df['Secuencial'] != '']
        
        # Procesar cantidades
        cantidad_col = None
        for col in ['Cantidad Prendas', 'CANTIDAD', 'TOTAL', 'UNIDADES']:
            if col in df.columns:
                cantidad_col = col
                break
        
        if cantidad_col:
            df['Cantidad_Entera'] = df[cantidad_col].apply(extraer_entero_mejorado)
        else:
            df['Cantidad_Entera'] = 0
        
        # Clasificar categorías
        df['Categoria'] = df.apply(clasificar_transferencia_mejorada, axis=1)
        
        # Aplicar clasificación textil si hay descripción de producto
        classifier = TextileClassifier()
        producto_col = None
        for col in ['Producto', 'PRODUCTO', 'Descripcion', 'DESCRIPCION', 'Articulo']:
            if col in df.columns:
                producto_col = col
                break
        
        if producto_col:
            classifications = df[producto_col].apply(lambda x: classifier.classify_product(x))
            class_df = pd.DataFrame(classifications.tolist())
            df = pd.concat([df.reset_index(drop=True), class_df], axis=1)
        
        # Calcular métricas
        total_unidades = int(df['Cantidad_Entera'].sum())
        total_transferencias = int(df['Secuencial'].nunique()) if 'Secuencial' in df.columns else len(df)
        
        # Métricas por categoría
        categorias = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas', 'Fundas', 'Otros/No Clasificado']
        por_categoria = {}
        detalle_categoria = {}
        conteo_sucursales = {}
        
        for cat in categorias:
            df_cat = df[df['Categoria'] == cat]
            por_categoria[cat] = int(df_cat['Cantidad_Entera'].sum())
            
            # Detectar columna de sucursal para conteo único
            sucursal_col = None
            for col in ['Sucursal Destino', 'Bodega Destino', 'BODEGA', 'DESTINO']:
                if col in df.columns:
                    sucursal_col = col
                    break
            
            unicas = df_cat[sucursal_col].nunique() if sucursal_col and not df_cat.empty else 0
            transf_count = df_cat['Secuencial'].nunique() if 'Secuencial' in df_cat.columns else len(df_cat)
            
            detalle_categoria[cat] = {
                'cantidad': por_categoria[cat],
                'transf': int(transf_count),
                'unicas': int(unicas)
            }
            conteo_sucursales[cat] = int(unicas)
        
        # Métricas por género si existe
        por_genero = {}
        if 'Genero' in df.columns:
            for gen in df['Genero'].unique():
                por_genero[gen] = int(df[df['Genero'] == gen]['Cantidad_Entera'].sum())
        
        # Métricas por color si existe
        por_color = {}
        if 'Color' in df.columns:
            color_dist = df[df['Color'] != 'No Especificado'].groupby('Color')['Cantidad_Entera'].sum()
            por_color = {k: int(v) for k, v in color_dist.nlargest(10).items()}
        
        resultado = {
            'fecha': datetime.now(),
            'transferencias': total_transferencias,
            'total_unidades': total_unidades,
            'por_categoria': por_categoria,
            'por_genero': por_genero,
            'por_color': por_color,
            'detalle_categoria': detalle_categoria,
            'conteo_sucursales': conteo_sucursales,
            'df_procesado': df
        }
        
        # Agregar al histórico si se proporciona manager
        if history_manager:
            history_manager.add_transfer_record(df, categoria_dia='Diaria')
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error en procesamiento: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def crear_grafico_columnas_porcentajes(res: Dict) -> go.Figure:
    """Crea gráfico de columnas con porcentajes y cantidades - REQUERIMIENTO PRINCIPAL"""
    
    # Preparar datos excluyendo Fundas para análisis de distribución real
    categorias_excluir = ['Fundas', 'Otros/No Clasificado']
    categorias_validas = [k for k in res['por_categoria'].keys() if k not in categorias_excluir and res['por_categoria'][k] > 0]
    
    if not categorias_validas:
        return go.Figure()
    
    # Ordenar por cantidad descendente
    categorias_ordenadas = sorted(categorias_validas, key=lambda x: res['por_categoria'][x], reverse=True)
    cantidades = [res['por_categoria'][cat] for cat in categorias_ordenadas]
    total = sum(cantidades)
    porcentajes = [(c/total)*100 if total > 0 else 0 for c in cantidades]
    
    # Colores corporativos
    colores = {
        'Price Club': '#0033A0',      # Azul corporativo
        'Tiendas': '#E4002B',          # Rojo
        'Ventas por Mayor': '#10B981', # Verde
        'Tienda Web': '#8B5CF6',       # Púrpura
        'Fallas': '#F59E0B'            # Amarillo/Naranja
    }
    
    colores_barras = [colores.get(cat, '#6B7280') for cat in categorias_ordenadas]
    
    fig = go.Figure()
    
    # Barras principales
    fig.add_trace(go.Bar(
        x=categorias_ordenadas,
        y=cantidades,
        text=[f"{int(c):,}<br>({p:.1f}%)" for c, p in zip(cantidades, porcentajes)],
        textposition='outside',
        textfont=dict(size=14, color='black', family='Arial Black'),
        marker_color=colores_barras,
        name='Unidades',
        hovertemplate='<b>%{x}</b><br>' +
                      'Cantidad: %{y:,.0f}<br>' +
                      'Porcentaje: %{customdata:.1f}%<br>' +
                      '<extra></extra>',
        customdata=porcentajes
    ))
    
    # Línea de porcentaje acumulado (Pareto opcional)
    porcentajes_acum = [sum(porcentajes[:i+1]) for i in range(len(porcentajes))]
    
    fig.add_trace(go.Scatter(
        x=categorias_ordenadas,
        y=[max(cantidades) * (p/100) * 1.1 for p in porcentajes_acum],  # Escalar para visualización
        mode='lines+markers',
        name='% Acumulado',
        line=dict(color='red', width=2, dash='dot'),
        marker=dict(size=8, color='red'),
        yaxis='y2',
        hovertemplate='Acumulado: %{customdata:.1f}%',
        customdata=porcentajes_acum,
        visible='legendonly'  # Oculto por defecto, activable en leyenda
    ))
    
    # Layout optimizado
    fig.update_layout(
        title={
            'text': "Distribución de Transferencias por Canal<br><sub>Cantidades y Porcentajes del Total</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=20, color='#1f2937')
        },
        xaxis_title="Canal de Distribución",
        yaxis_title="Unidades Transferidas",
        yaxis2=dict(
            title="Porcentaje Acumulado",
            overlaying='y',
            side='right',
            showgrid=False,
            visible=False
        ),
        template="plotly_white",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=100, b=50),
        bargap=0.3
    )
    
    # Anotaciones de totales
    fig.add_annotation(
        x=0.95,
        y=0.95,
        xref='paper',
        yref='paper',
        text=f"<b>Total:<br>{total:,} und</b>",
        showarrow=False,
        font=dict(size=16, color='#1f2937'),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='#1f2937',
        borderwidth=2,
        borderpad=4
    )
    
    return fig


# ==============================================================================
# FUNCIONES UTILITARIAS
# ==============================================================================

def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convierte DataFrame a bytes de Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    output.seek(0)
    return output.getvalue()


def mostrar_metricas_kpis(res: Dict, container):
    """Muestra KPIs en formato de tarjetas"""
    categorias_display = {
        'Price Club': ('PRICE CLUB', '#0033A0', PRICE_CLUBS),
        'Tiendas': ('TIENDAS AERO', '#E4002B', TIENDAS_REGULARES),
        'Ventas por Mayor': ('MAYORISTAS', '#10B981', VENTAS_POR_MAYOR),
        'Tienda Web': ('E-COMMERCE', '#8B5CF6', TIENDA_WEB),
        'Fallas': ('FALLAS/DAÑADOS', '#F59E0B', FALLAS),
        'Fundas': ('FUNDAS/BULTOS', '#EC4899', None)
    }
    
    cols = container.columns(3)
    idx = 0
    
    for cat, (display, color, esperadas) in categorias_display.items():
        cantidad = res['por_categoria'].get(cat, 0)
        sucursales = res['conteo_sucursales'].get(cat, 0)
        
        with cols[idx % 3]:
            if cat == 'Fundas':
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {color}20, {color}40); 
                            padding: 20px; border-radius: 10px; border-left: 5px solid {color};'>
                    <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>{display}</div>
                    <div style='font-size: 32px; font-weight: bold; color: {color};'>{cantidad:,}</div>
                    <div style='font-size: 12px; color: #888;'>Bultos ≥500 und múltiplos 100</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                cobertura = f"{sucursales}/{esperadas} suc." if esperadas else f"{sucursales} suc."
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, {color}15, {color}30); 
                            padding: 20px; border-radius: 10px; border-left: 5px solid {color};'>
                    <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>{display}</div>
                    <div style='font-size: 32px; font-weight: bold; color: {color};'>{cantidad:,}</div>
                    <div style='font-size: 12px; color: #666;'>{cobertura}</div>
                </div>
                """, unsafe_allow_html=True)
        
        idx += 1
        if idx % 3 == 0 and idx < len(categorias_display):
            cols = container.columns(3)


# ==============================================================================
# FUNCION PRINCIPAL DEL DASHBOARD
# ==============================================================================

def mostrar_dashboard_transferencias():
    """Dashboard principal de transferencias - V2.0 Mejorado"""
    
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
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Logísticas</h1>
        <div class='header-subtitle'>Análisis de distribución por canales, clasificación textil y métricas de desempeño</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar gestor de histórico
    history_manager = TransferHistoryManager()
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📊 Transferencias Diarias", 
        "📦 Mercadería en Tránsito", 
        "📈 Análisis Histórico & Stock (En desarrollo)"
    ])
    
    # ==========================================
    # TAB 1: TRANSFERENCIAS DIARIAS (MEJORADO)
    # ==========================================
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📂 Carga de Archivo de Transferencias Diarias</h4>
            <p class='section-description'>Sube el archivo Excel de transferencias (ej: 322026.xlsx) para análisis completo con desagregación por género, color y talla.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_upload1, col_upload2 = st.columns([3, 1])
        with col_upload1:
            file_diario = st.file_uploader(
                "Selecciona archivo Excel de transferencias",
                type=['xlsx', 'xls'],
                key="diario_transferencias_v2"
            )
        with col_upload2:
            if st.button("🔄 Limpiar Todo", use_container_width=True):
                history_manager.clear_history()
                st.rerun()
        
        if not file_diario:
            st.info("👆 **Sube un archivo Excel para comenzar el análisis.**")
            
            with st.expander("📋 Estructura esperada del archivo"):
                ejemplo = pd.DataFrame({
                    'Secuencial': ['TR-001', 'TR-002', 'TR-003', 'TR-004', 'TR-005'],
                    'Sucursal Destino': [
                        'PRICE CLUB QUITO', 
                        'AERO MALL DEL SOL', 
                        'VENTAS POR MAYOR', 
                        'TIENDA WEB',
                        'FALLAS BODEGA'
                    ],
                    'Cantidad Prendas': [1500, 245, 5000, 120, 50],
                    'Producto': [
                        'CAMISETA POLO HOMBRE AZUL M',
                        'JEANS SKINNY MUJER NEGRO 28',
                        'FUNDAS CAMISETAS VARIAS',
                        'HOODIE UNISEX GRIS L',
                        'BOXER ALGODON DAÑADO'
                    ]
                })
                st.dataframe(ejemplo, use_container_width=True)
                st.caption("El sistema detectará automáticamente las columnas sin importar el nombre exacto.")
        
        else:
            try:
                # Cargar y mostrar preview
                df_diario = pd.read_excel(file_diario)
                st.success(f"✅ Archivo cargado: **{file_diario.name}** ({len(df_diario)} filas)")
                
                with st.expander("🔍 Vista previa de datos crudos", expanded=False):
                    st.dataframe(df_diario.head(10), use_container_width=True)
                    st.json({
                        "columnas_detectadas": list(df_diario.columns),
                        "tipos_datos": {k: str(v) for k, v in df_diario.dtypes.to_dict().items()}
                    })
                
                # Procesar datos
                with st.spinner("🔄 Procesando transferencias con clasificación inteligente..."):
                    res = procesar_transferencias_diarias_mejorado(df_diario, history_manager)
                
                if res is None:
                    st.error("❌ Error al procesar los datos. Revisa la estructura del archivo.")
                    return
                
                # ==========================================
                # SECCION DE KPIs Y METRICAS
                # ==========================================
                st.header("📈 KPIs por Canal de Distribución")
                mostrar_metricas_kpis(res, st)
                
                st.divider()
                
                # ==========================================
                # GRAFICO DE COLUMNAS CON PORCENTAJES - REQUERIMIENTO PRINCIPAL
                # ==========================================
                st.header("📊 Distribución por Canal (Cantidades y Porcentajes)")
                
                col_graf1, col_graf2 = st.columns([3, 1])
                
                with col_graf1:
                    fig_columnas = crear_grafico_columnas_porcentajes(res)
                    st.plotly_chart(fig_columnas, use_container_width=True, use_container_height=True)
                    
                    # Leyenda explicativa
                    st.caption("""
                    **Interpretación:** 
                    - Barras = Unidades absolutas transferidas
                    - Porcentaje = Participación sobre el total (excluyendo fundas)
                    - Orden descendente por volumen
                    """)
                
                with col_graf2:
                    st.subheader("Resumen %")
                    total_efectivo = sum(v for k, v in res['por_categoria'].items() 
                                        if k not in ['Fundas', 'Otros/No Clasificado'])
                    
                    for cat in ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas']:
                        cant = res['por_categoria'].get(cat, 0)
                        pct = (cant/total_efectivo*100) if total_efectivo > 0 else 0
                        color = {'Price Club': '🔵', 'Tiendas': '🔴', 'Ventas por Mayor': '🟢', 
                                'Tienda Web': '🟣', 'Fallas': '🟠'}.get(cat, '⚪')
                        st.metric(f"{color} {cat}", f"{cant:,}", f"{pct:.1f}%")
                
                st.divider()
                
                # ==========================================
                # ANALISIS TEXTIL (SI APLICA)
                # ==========================================
                if res.get('por_genero') or res.get('por_color'):
                    st.header("👕 Desagregación Textil de las Transferencias")
                    
                    col_text1, col_text2, col_text3 = st.columns(3)
                    
                    with col_text1:
                        if res.get('por_genero'):
                            st.subheader("⚧ Por Género")
                            fig_gen = px.pie(
                                names=list(res['por_genero'].keys()),
                                values=list(res['por_genero'].values()),
                                hole=0.4,
                                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
                            )
                            st.plotly_chart(fig_gen, use_container_width=True)
                    
                    with col_text2:
                        if res.get('por_color'):
                            st.subheader("🎨 Top Colores")
                            colors = dict(list(res['por_color'].items())[:5])
                            fig_col = px.bar(
                                x=list(colors.values()),
                                y=list(colors.keys()),
                                orientation='h',
                                color=list(colors.values()),
                                color_continuous_scale='Viridis'
                            )
                            fig_col.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_col, use_container_width=True)
                    
                    with col_text3:
                        st.subheader("📊 Métricas Textiles")
                        if res.get('por_genero'):
                            for gen, cant in sorted(res['por_genero'].items(), key=lambda x: x[1], reverse=True):
                                pct = (cant/res['total_unidades']*100) if res['total_unidades'] > 0 else 0
                                st.write(f"**{gen}:** {cant:,} und ({pct:.1f}%)")
                
                st.divider()
                
                # ==========================================
                # TABLAS DETALLADAS Y EXPORTACION
                # ==========================================
                st.header("📋 Detalle Completo por Transferencia")
                
                # Tabs para diferentes vistas
                tab_detalle1, tab_detalle2, tab_detalle3 = st.tabs([
                    "Por Secuencial", "Por Categoría", "Datos Completos"
                ])
                
                with tab_detalle1:
                    cols_detalle = ['Secuencial', 'Sucursal Destino', 'Cantidad_Entera', 'Categoria']
                    cols_disponibles = [c for c in cols_detalle if c in res['df_procesado'].columns]
                    
                    if cols_disponibles:
                        df_det = res['df_procesado'][cols_disponibles].copy()
                        df_det = df_det.rename(columns={
                            'Sucursal Destino': 'Destino',
                            'Cantidad_Entera': 'Unidades',
                            'Categoria': 'Canal'
                        })
                        st.dataframe(df_det, use_container_width=True, height=400)
                
                with tab_detalle2:
                    resumen_df = pd.DataFrame.from_dict(
                        res['detalle_categoria'], 
                        orient='index'
                    ).reset_index().rename(columns={
                        'index': 'Canal',
                        'cantidad': 'Unidades',
                        'transf': 'N° Transferencias',
                        'unicas': 'Sucursales'
                    })
                    st.dataframe(resumen_df, use_container_width=True)
                    
                    # Gráfico de burbujas
                    if not resumen_df.empty:
                        fig_bubble = px.scatter(
                            resumen_df[resumen_df['Unidades'] > 0],
                            x='N° Transferencias',
                            y='Unidades',
                            size='Sucursales',
                            color='Canal',
                            hover_name='Canal',
                            size_max=60,
                            title="Relación Transferencias vs Unidades vs Cobertura"
                        )
                        st.plotly_chart(fig_bubble, use_container_width=True)
                
                with tab_detalle3:
                    st.dataframe(res['df_procesado'], use_container_width=True, height=400)
                
                # Exportación
                st.divider()
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                with col_exp1:
                    excel_data = to_excel_bytes(res['df_procesado'])
                    st.download_button(
                        label="📥 Descargar Todo (Excel)",
                        data=excel_data,
                        file_name=f"transferencias_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_exp2:
                    # Exportar resumen
                    resumen_export = pd.DataFrame({
                        'Canal': list(res['por_categoria'].keys()),
                        'Unidades': list(res['por_categoria'].values()),
                        'Porcentaje': [
                            (v/sum(res['por_categoria'].values())*100) 
                            for v in res['por_categoria'].values()
                        ]
                    })
                    excel_resumen = to_excel_bytes(resumen_export)
                    st.download_button(
                        label="📊 Solo Resumen",
                        data=excel_resumen,
                        file_name=f"resumen_transferencias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        use_container_width=True
                    )
                
                with col_exp3:
                    if st.button("💾 Guardar en Histórico", use_container_width=True):
                        st.success("✅ Datos guardados en histórico de sesión")
                        st.info(f"Total acumulado histórico: {history_manager.get_accumulated_metrics()['total_unidades']:,} unidades")
            
            except Exception as e:
                st.error(f"❌ Error crítico: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

    # ==========================================
    # TAB 2: MERCADERIA EN TRANSITO (AHORA CON UN SOLO ARCHIVO)
    # ==========================================
    with tab2:
        st.header("📦 Análisis de Mercadería en Tránsito con Clasificación Inteligente")
        
        transit_processor = TransitDataProcessor()
        
        st.markdown("""
        <div class='filter-panel'>
            <h4>📂 Carga de Archivo de Tránsito</h4>
            <p class='section-description'>Sube el archivo de mercadería en tránsito (Excel o CSV). El sistema detectará automáticamente las columnas y clasificará los productos por género, categoría textil, color y talla.</p>
        </div>
        """, unsafe_allow_html=True)
        
        f_transito = st.file_uploader(
            "Archivo de Tránsito/Transferencias", 
            type=['xlsx', 'csv'], 
            key="transito_unico"
        )
        
        if f_transito:
            try:
                # Procesar tránsito sin base
                with st.spinner("🔍 Clasificando productos textilmente..."):
                    df_transito = transit_processor.process_transit_file(f_transito, df_base=None)
                
                if df_transito is None or df_transito.empty:
                    st.error("❌ No se pudo procesar el archivo de tránsito")
                    return
                
                # Métricas principales
                st.subheader("📊 Métricas del Tránsito")
                m1, m2, m3, m4, m5 = st.columns(5)
                
                with m1:
                    st.metric("Total Unidades", f"{int(df_transito['CANTIDAD'].sum()):,}")
                with m2:
                    st.metric("SKUs Únicos", df_transito['CODIGO'].nunique())
                with m3:
                    st.metric("Categorías", df_transito['Categoria'].nunique() if 'Categoria' in df_transito.columns else "N/A")
                with m4:
                    st.metric("Géneros", df_transito['Genero'].nunique() if 'Genero' in df_transito.columns else "N/A")
                with m5:
                    st.metric("Colores ID", df_transito[df_transito['Color'] != 'No Especificado']['Color'].nunique() if 'Color' in df_transito.columns else 0)
                
                st.divider()
                
                # Dashboard visual
                col_viz1, col_viz2 = st.columns(2)
                
                with col_viz1:
                    st.subheader("👕 Distribución por Categoría Textil")
                    if 'Categoria' in df_transito.columns:
                        cat_dist = df_transito.groupby('Categoria')['CANTIDAD'].sum().sort_values(ascending=True)
                        fig_cat = px.bar(
                            x=cat_dist.values,
                            y=cat_dist.index,
                            orientation='h',
                            color=cat_dist.values,
                            color_continuous_scale='Blues',
                            text=cat_dist.values
                        )
                        fig_cat.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                        st.plotly_chart(fig_cat, use_container_width=True)
                
                with col_viz2:
                    st.subheader("⚧ Distribución por Género")
                    if 'Genero' in df_transito.columns:
                        gen_dist = df_transito.groupby('Genero')['CANTIDAD'].sum()
                        fig_gen = px.pie(
                            values=gen_dist.values,
                            names=gen_dist.index,
                            hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        st.plotly_chart(fig_gen, use_container_width=True)
                
                # Análisis por color
                st.subheader("🎨 Análisis Cromático")
                if 'Color' in df_transito.columns:
                    col_c1, col_c2 = st.columns([2, 1])
                    
                    with col_c1:
                        color_data = df_transito[df_transito['Color'] != 'No Especificado']
                        if not color_data.empty:
                            color_dist = color_data.groupby('Color')['CANTIDAD'].sum().nlargest(12)
                            
                            fig_color = px.bar(
                                x=color_dist.index,
                                y=color_dist.values,
                                color=color_dist.values,
                                color_continuous_scale='Viridis',
                                labels={'x': 'Color', 'y': 'Unidades'},
                                text=color_dist.values
                            )
                            fig_color.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                            st.plotly_chart(fig_color, use_container_width=True)
                    
                    with col_c2:
                        st.markdown("**Top 5 Colores:**")
                        for i, (color, cant) in enumerate(color_dist.head(5).items(), 1):
                            pct = (cant/color_data['CANTIDAD'].sum())*100
                            st.write(f"{i}. **{color}**: {int(cant):,} ({pct:.1f}%)")
                
                # Análisis por talla
                if 'Talla' in df_transito.columns:
                    st.subheader("📏 Distribución por Talla")
                    talla_data = df_transito[~df_transito['Talla'].isin(['Única', 'No Especificado'])]
                    
                    if not talla_data.empty:
                        talla_dist = talla_data.groupby('Talla')['CANTIDAD'].sum()
                        
                        # Ordenar según jerarquía estándar
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
                
                # Tabla detallada con filtros
                st.subheader("🔍 Explorador de Datos Clasificados")
                
                # Filtros dinámicos
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
                display_cols = [c for c in display_cols if c in df_filtrado.columns]
                if 'PRODUCTO' in df_filtrado.columns:
                    display_cols.insert(1, 'PRODUCTO')
                
                st.dataframe(
                    df_filtrado[display_cols].sort_values('CANTIDAD', ascending=False),
                    use_container_width=True,
                    height=400
                )
                
                # Exportar análisis completo
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_transito.to_excel(writer, sheet_name='Datos_Completos', index=False)
                        
                        # Resúmenes
                        if 'Categoria' in df_transito.columns:
                            res_cat = df_transito.groupby('Categoria').agg({
                                'CANTIDAD': 'sum',
                                'CODIGO': 'nunique'
                            }).rename(columns={'CODIGO': 'SKUs'}).sort_values('CANTIDAD', ascending=False)
                            res_cat.to_excel(writer, sheet_name='Resumen_Categorias')
                        
                        if 'Genero' in df_transito.columns:
                            res_gen = df_transito.groupby('Genero').agg({
                                'CANTIDAD': 'sum',
                                'CODIGO': 'nunique'
                            }).rename(columns={'CODIGO': 'SKUs'}).sort_values('CANTIDAD', ascending=False)
                            res_gen.to_excel(writer, sheet_name='Resumen_Genero')
                        
                        if 'Color' in df_transito.columns:
                            res_col = df_transito[df_transito['Color'] != 'No Especificado'].groupby('Color').agg({
                                'CANTIDAD': 'sum',
                                'CODIGO': 'nunique'
                            }).rename(columns={'CODIGO': 'SKUs'}).sort_values('CANTIDAD', ascending=False)
                            res_col.to_excel(writer, sheet_name='Resumen_Colores')
                        
                        if 'Talla' in df_transito.columns:
                            res_talla = df_transito.groupby('Talla').agg({
                                'CANTIDAD': 'sum',
                                'CODIGO': 'nunique'
                            }).rename(columns={'CODIGO': 'SKUs'}).sort_values('CANTIDAD', ascending=False)
                            res_talla.to_excel(writer, sheet_name='Resumen_Tallas')
                    
                    st.download_button(
                        label="📥 Descargar Análisis Completo (Excel)",
                        data=output.getvalue(),
                        file_name=f"analisis_transito_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        use_container_width=True
                    )
                
                with col_exp2:
                    st.info(f"💡 **Tip:** El archivo exportado incluye múltiples pestañas con análisis por dimensión (categoría, género, color, talla).")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
        
        else:
            st.info("👆 Sube el archivo de tránsito para comenzar el análisis.")
            
            with st.expander("ℹ️ Guía de uso"):
                st.markdown("""
                **Archivo de Tránsito:**
                - Debe contener columnas con código de producto, cantidad y opcionalmente descripción del producto.
                - El sistema detectará automáticamente las columnas y clasificará cada prenda por género, categoría textil, color y talla.
                - Se generarán gráficos y tablas resumen.
                """)

    # ==========================================
    # TAB 3: ANALISIS HISTORICO Y STOCK (EN DESARROLLO)
    # ==========================================
    with tab3:
        st.header("📈 Análisis Histórico y de Stock (Módulo en Desarrollo)")
        
        st.markdown("""
        <div style="background: #fef3c7; padding: 30px; border-radius: 10px; text-align: center; border: 1px solid #fbbf24;">
            <h3 style="color: #92400e;">🚧 Módulo en Construcción</h3>
            <p style="color: #78350f; font-size: 1.1em;">Este módulo se encuentra actualmente en desarrollo. Pronto podrás acceder a análisis históricos avanzados y gestión de stock.</p>
            <p style="color: #78350f;">Mientras tanto, puedes utilizar las pestañas de Transferencias Diarias y Mercadería en Tránsito para obtener información valiosa.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Opcional: mostrar algún dato histórico si ya se ha cargado algo
        metrics = history_manager.get_accumulated_metrics()
        if metrics['total_unidades'] > 0:
            st.subheader("📊 Datos Históricos Acumulados (Sesión Actual)")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Unidades Históricas", f"{metrics['total_unidades']:,}")
            with col2:
                st.metric("Categorías", len(metrics['por_categoria']))
            with col3:
                st.metric("Géneros", len(metrics['por_genero']))


# ==============================================================================
# FUNCION DE ENTRADA PRINCIPAL
# ==============================================================================

def show_dashboard_logistico():
    """Punto de entrada del dashboard logístico"""
    
    # CSS adicional para mejorar apariencia
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
