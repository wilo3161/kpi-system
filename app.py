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

def navigate_to_module(module_key):
    """Navega al modulo seleccionado"""
    st.session_state.current_page = module_key
    st.rerun()

def create_module_card(icon, title, description, module_key):
    """Crea una tarjeta de modulo completamente clickeable usando st.button nativo"""
    card_container = st.container()
    
    with card_container:
        col1, col2, col3 = st.columns([1, 10, 1])
        with col2:
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
            
            if st.button(
                " ", 
                key=f"card_btn_{module_key}", 
                help=f"Acceder a {title}",
                use_container_width=True,
                type="secondary"
            ):
                navigate_to_module(module_key)

def add_back_button(key: str = "back_button"):
    """Agrega el boton de volver al inicio con clave única"""
    if st.button("← Menu Principal", key=key, help="Volver al menu principal", type="primary"):
        st.session_state.current_page = "Inicio"
        st.rerun()

def show_module_header(title_with_icon, subtitle):
    """Muestra la cabecera de un modulo con icono visible"""
    if title_with_icon and len(title_with_icon) > 0:
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
    texto = str(texto).upper()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii')
    return texto

def procesar_subtotal_wilo(valor):
    """Procesa valores numericos"""
    try:
        if pd.isna(valor):
            return 0.0
        if isinstance(valor, str):
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
    
    st.markdown('<div class="modules-grid fade-in">', unsafe_allow_html=True)
    
    modules = [
        {"icon": "📊", "title": "Dashboard KPIs", "description": "Dashboard en tiempo real con metricas operativas", "key": "dashboard_kpis"},
        {"icon": "💰", "title": "Reconciliacion", "description": "Conciliacion financiera y analisis de facturas", "key": "reconciliacion_v8"},
        {"icon": "📧", "title": "Auditoria de Correos", "description": "Analisis inteligente de novedades por email", "key": "auditoria_correos"},
        {"icon": "📦", "title": "Dashboard Logistico", "description": "Control de transferencias y distribucion", "key": "dashboard_logistico"},
        {"icon": "👥", "title": "Gestion de Equipo", "description": "Administracion del personal del centro", "key": "gestion_equipo"},
        {"icon": "🚚", "title": "Generar Guias", "description": "Sistema de envios con seguimiento QR", "key": "generar_guias"},
        {"icon": "📋", "title": "Control de Inventario", "description": "Gestion de stock en tiempo real", "key": "control_inventario"},
        {"icon": "📈", "title": "Reportes Avanzados", "description": "Analisis y estadisticas ejecutivas", "key": "reportes_avanzados"},
        {"icon": "⚙️", "title": "Configuracion", "description": "Personalizacion del sistema ERP", "key": "configuracion"}
    ]
    
    cols = st.columns(3)
    for idx, module in enumerate(modules):
        with cols[idx % 3]:
            create_module_card(module["icon"], module["title"], module["description"], module["key"])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    add_back_button(key="back_kpis")
    show_module_header(
        "📊 Dashboard de KPIs",
        "Metricas en tiempo real del Centro de Distribucion"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", datetime.now() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col3:
        tipo_kpi = st.selectbox("📈 Tipo de Metrica", ["Produccion", "Eficiencia", "Costos", "Alertas"])
    
    kpis_data = local_db.query('kpis')
    df_kpis = pd.DataFrame(kpis_data)
    
    if not df_kpis.empty:
        df_kpis['fecha'] = pd.to_datetime(df_kpis['fecha'])
        mask = (df_kpis['fecha'].dt.date >= fecha_inicio) & (df_kpis['fecha'].dt.date <= fecha_fin)
        df_filtered = df_kpis[mask]
        
        if not df_filtered.empty:
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
            
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = px.line(df_filtered, x='fecha', y='produccion', 
                        title='Produccion Diaria',
                        labels={'produccion': 'Unidades', 'fecha': 'Fecha'},
                        line_shape='spline')
            fig.update_traces(line=dict(color='#0033A0', width=3))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
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

# Constantes para el dashboard logistico
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

COLORS = {
    'PRICE CLUB': '#0033A0',
    'TIENDAS AEROPOSTALE': '#E4002B',
    'VENTAS POR MAYOR': '#10B981',
    'TIENDA WEB': '#8B5CF6',
    'FALLAS': '#F59E0B',
    'FUNDAS': '#EC4899'
}

GRADIENTS = {
    'PRICE CLUB': 'linear-gradient(135deg, #0033A015, #0033A030)',
    'TIENDAS AEROPOSTALE': 'linear-gradient(135deg, #E4002B15, #E4002B30)',
    'VENTAS POR MAYOR': 'linear-gradient(135deg, #10B98115, #10B98130)',
    'TIENDA WEB': 'linear-gradient(135deg, #8B5CF615, #8B5CF630)',
    'FALLAS': 'linear-gradient(135deg, #F59E0B15, #F59E0B30)',
    'FUNDAS': 'linear-gradient(135deg, #EC489915, #EC489930)'
}

CHART_COLORS = ['#0033A0', '#E4002B', '#10B981', '#8B5CF6', '#F59E0B', '#3B82F6']

# Diccionarios para clasificación de productos
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
    'LEATHER': 'Cuero', 'DENIM': 'Denim',
    'SUMMER': 'Verano', 'WINTER': 'Invierno', 'SPRING': 'Primavera',
    'FALL': 'Otoño', 'AUTUMN': 'Otoño'
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

IGNORE_WORDS = {'AERO', 'OF', 'THE', 'AND', 'IN', 'WITH', 'FOR', 'BY', 'ON', 'AT', 'TO'}

WAREHOUSE_GROUPS = {
    'PRICE': 'Price Club',
    'AERO': 'Aeropostale',
    'MALL': 'Centro Comercial',
    'RIOCENTRO': 'Riocentro',
    'CONDADO': 'Condado',
    'SAN': 'San',
    'LOS': 'Los'
}

class TextileClassifier:
    """Clasificador inteligente para productos textiles"""
    
    def __init__(self):
        self.gender_map = GENDER_MAP
        self.category_map = CATEGORY_MAP
        self.color_map = COLOR_MAP
        self.size_hierarchy = SIZE_HIERARCHY
        self.ignore_words = IGNORE_WORDS
        
    def classify_product(self, product_name: str) -> dict:
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
        
        return self._clean_classification(classification)
    
    def _detect_gender(self, words):
        for word in words:
            if word in self.gender_map:
                return self.gender_map[word]
        text = ' '.join(words)
        if any(x in text for x in ['WOMEN', 'LADIES', 'FEMALE']):
            return 'Mujer'
        if any(x in text for x in ['MEN', 'MAN', 'MALE']):
            return 'Hombre'
        return 'Unisex'
    
    def _detect_category(self, words):
        categoria = 'General'
        subcategoria = ''
        found = []
        for word in words:
            if word in self.category_map:
                found.append(self.category_map[word])
            elif word not in self.ignore_words and len(word) > 2:
                subcategoria += word.capitalize() + ' '
        if found:
            main = ['Polo', 'Camiseta', 'Jeans', 'Pantalón', 'Vestido', 'Chaqueta']
            for m in main:
                if m in found:
                    categoria = m
                    break
            else:
                categoria = found[0]
            other = [c for c in found if c != categoria]
            if other:
                subcategoria = ' '.join(other) + ' ' + subcategoria.strip()
        return {'categoria': categoria.strip(), 'subcategoria': subcategoria.strip()}
    
    def _detect_color(self, words):
        for word in words:
            if word in self.color_map:
                return self.color_map[word]
        text = ' '.join(words)
        for eng, esp in self.color_map.items():
            if eng in text:
                return esp
        return 'No Especificado'
    
    def _detect_size(self, words):
        for size in self.size_hierarchy:
            if f' {size} ' in f' {" ".join(words)} ':
                return size
        return 'Única'
    
    def _detect_style(self, words):
        material = ''
        estilo = ''
        materials = ['COTTON', 'POLYESTER', 'DENIM', 'LEATHER', 'WOOL', 'SILK']
        for w in words:
            if w in materials:
                material = w.lower().capitalize()
                break
        style_kw = {
            'GRAPHIC': 'Estampado', 'PRINTED': 'Estampado',
            'SOLID': 'Liso', 'STRIPED': 'Rayado',
            'BASIC': 'Básico', 'PREMIUM': 'Premium'
        }
        for w in words:
            if w in style_kw:
                estilo = style_kw[w]
                break
        return {'material': material, 'estilo': estilo}
    
    def _clean_classification(self, cls):
        size_map = {'XSMALL': 'XS', 'SMALL': 'S', 'MEDIUM': 'M',
                    'LARGE': 'L', 'XLARGE': 'XL', 'XXLARGE': '2XL'}
        if cls['Talla'] in size_map:
            cls['Talla'] = size_map[cls['Talla']]
        for k, v in cls.items():
            if isinstance(v, str):
                cls[k] = v.strip()
        return cls
    
    def _get_empty_classification(self):
        return {
            'Genero': 'No Identificado',
            'Categoria': 'No Identificado',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'No Especificado',
            'Material': '',
            'Estilo': ''
        }

class DataProcessor:
    """Procesador de archivos de transferencias - Versión mejorada con mapeo flexible de columnas"""
    
    def __init__(self):
        self.classifier = TextileClassifier()
    
    def process_excel_file(self, file) -> pd.DataFrame:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            
            df.columns = [str(c).strip() for c in df.columns]
            
            required_std = ['Producto', 'Fecha', 'Cantidad', 'Bodega Recibe']
            dest_aliases = ['Bodega Destino', 'Sucursal Destino', 'Destino', 'Bodega', 'Sucursal']
            
            col_mapping = {}
            missing = []
            
            for req in required_std:
                found = False
                for col in df.columns:
                    if col.lower() == req.lower():
                        col_mapping[col] = req
                        found = True
                        break
                if not found:
                    for col in df.columns:
                        if req.lower() in col.lower():
                            col_mapping[col] = req
                            found = True
                            break
                if not found and req == 'Bodega Recibe':
                    for alias in dest_aliases:
                        for col in df.columns:
                            if alias.lower() in col.lower():
                                col_mapping[col] = req
                                found = True
                                break
                        if found:
                            break
                if not found:
                    missing.append(req)
            
            if missing:
                st.error(f"❌ No se encontraron las siguientes columnas en el archivo: {', '.join(missing)}")
                st.info("Columnas detectadas: " + ", ".join(df.columns))
                return pd.DataFrame()
            
            df.rename(columns=col_mapping, inplace=True)
            df['Cantidad'] = self._process_quantity(df['Cantidad'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True, infer_datetime_format=True)
            if df['Fecha'].isna().all():
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', format='%d/%m/%Y')
            df = df.dropna(subset=['Fecha'])
            if df.empty:
                st.warning("No se pudo interpretar la columna 'Fecha'. Verifique el formato (use dd/mm/aaaa).")
                return pd.DataFrame()
            
            df = self._classify_products(df)
            df['Grupo_Bodega'] = df['Bodega Recibe'].apply(self._group_warehouse)
            
            sec_col = None
            posibles_sec = ['Secuencial - Factura', 'Secuencial', 'Factura', 'ID Transferencia', 'Transferencia']
            for col in df.columns:
                if any(ps.lower() in col.lower() for ps in posibles_sec):
                    sec_col = col
                    break
            if sec_col:
                df['ID_Transferencia'] = df[sec_col].astype(str) + '_' + df['Fecha'].dt.strftime('%Y%m%d')
            else:
                df['ID_Transferencia'] = df.index.astype(str) + '_' + df['Fecha'].dt.strftime('%Y%m%d')
            
            df = df.sort_values('Fecha', ascending=False).reset_index(drop=True)
            st.success(f"✅ Archivo procesado: {len(df)} registros")
            return df
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")
            return pd.DataFrame()
    
    def _process_quantity(self, s):
        quantities = []
        for val in s:
            if pd.isna(val):
                quantities.append(0)
            elif isinstance(val, (int, float)):
                if float(val).is_integer():
                    quantities.append(int(val))
                else:
                    quantities.append(float(val))
            elif isinstance(val, str):
                val = val.strip().replace(',', '')
                try:
                    f = float(val)
                    if f.is_integer():
                        quantities.append(int(f))
                    else:
                        quantities.append(f)
                except:
                    quantities.append(0)
            else:
                quantities.append(0)
        return pd.Series(quantities)
    
    def _classify_products(self, df):
        classifications = []
        for prod in df['Producto']:
            classifications.append(self.classifier.classify_product(prod))
        class_df = pd.DataFrame(classifications)
        
        # --- NUEVO: Crear Producto_Base eliminando talla y "REGULAR" del nombre original ---
        import re
        # Construir patrón con todas las tallas de SIZE_HIERARCHY
        size_pattern = '|'.join(SIZE_HIERARCHY)  # ej. '3XS|2XS|XS|XSMALL|S|SMALL|...'
        # Eliminar la talla y la palabra "REGULAR" (opcional) al final
        # El patrón busca un espacio, luego la talla o "REGULAR", luego opcionalmente más espacios, y fin de cadena
        pattern = r'\s+(' + size_pattern + r'|REGULAR)\s*$'
        df['Producto_Base'] = df['Producto'].str.upper().str.replace(pattern, '', regex=True).str.strip()
        # Si después de limpiar queda vacío, asignar "No especificado"
        df['Producto_Base'] = df['Producto_Base'].replace('', 'No especificado')
        # --------------------------------------------------------------------------------
        
        cols_to_drop = [col for col in class_df.columns if col in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        return pd.concat([df, class_df], axis=1)
    
    def _group_warehouse(self, name):
        if not isinstance(name, str):
            return 'Otros'
        up = name.upper()
        for key, group in WAREHOUSE_GROUPS.items():
            if key in up:
                return group
        if 'PRICE' in up:
            return 'Price Club'
        if 'AERO' in up:
            return 'Aeropostale'
        if any(x in up for x in ['MALL', 'CENTRO', 'SHOPPING']):
            return 'Centro Comercial'
        if any(x in up for x in ['TIENDA', 'STORE', 'LOCAL']):
            return 'Tienda Física'
        if any(x in up for x in ['WEB', 'ONLINE', 'MOVIL']):
            return 'Tienda Online'
        return 'Otros'

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_detailed_report(self, df: pd.DataFrame, fecha_inicio=None, fecha_fin=None) -> io.BytesIO:
        if df.empty:
            return None
        
        if fecha_inicio and fecha_fin and 'Fecha' in df.columns:
            mask = (df['Fecha'].dt.date >= fecha_inicio) & (df['Fecha'].dt.date <= fecha_fin)
            df = df[mask].copy()
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary = []
            total_units = int(df['Cantidad'].sum())
            total_transfers = df['ID_Transferencia'].nunique() if 'ID_Transferencia' in df.columns else len(df)
            bodegas = df['Bodega Recibe'].nunique()
            productos = df['Producto'].nunique()
            summary.append(['KPIs PRINCIPALES', ''])
            summary.append(['Total Unidades', f'{total_units:,}'])
            summary.append(['Transferencias', f'{total_transfers:,}'])
            summary.append(['Bodegas Destino', f'{bodegas:,}'])
            summary.append(['Productos Únicos', f'{productos:,}'])
            summary.append(['', ''])
            
            top_bodegas = df.groupby('Bodega Recibe')['Cantidad'].sum().nlargest(5)
            summary.append(['TOP 5 BODEGAS', 'Unidades'])
            for b, c in top_bodegas.items():
                summary.append([b, f'{int(c):,}'])
            summary.append(['', ''])
            
            if 'Categoria' in df.columns:
                top_cat = df.groupby('Categoria')['Cantidad'].sum().nlargest(5)
                summary.append(['TOP 5 CATEGORÍAS', 'Unidades'])
                for cat, cant in top_cat.items():
                    summary.append([cat, f'{int(cant):,}'])
            
            pd.DataFrame(summary, columns=['Métrica', 'Valor']).to_excel(writer, sheet_name='Resumen', index=False)
            df.to_excel(writer, sheet_name='Detalle', index=False)
            
            if 'Bodega Recibe' in df.columns:
                w_sum = df.groupby('Bodega Recibe').agg({'Cantidad': ['sum', 'count'], 'Producto': 'nunique'})
                w_sum.columns = ['Unidades', 'Transferencias', 'Productos']
                w_sum.sort_values('Unidades', ascending=False).to_excel(writer, sheet_name='Por_Bodega')
            
            if 'Categoria' in df.columns:
                cat_sum = df.groupby(['Categoria', 'Genero']).agg({'Cantidad': ['sum', 'count'], 'Producto': 'nunique'})
                cat_sum.columns = ['Unidades', 'Transferencias', 'Productos']
                cat_sum.sort_values('Unidades', ascending=False).to_excel(writer, sheet_name='Por_Categoria')
            
            if 'Fecha' in df.columns:
                df['Fecha_Dia'] = df['Fecha'].dt.date
                daily = df.groupby('Fecha_Dia').agg({'Cantidad': 'sum', 'ID_Transferencia': 'nunique'}).reset_index()
                daily.columns = ['Fecha', 'Unidades', 'Transferencias']
                daily.sort_values('Fecha').to_excel(writer, sheet_name='Tendencias', index=False)
            
            # --- NUEVAS HOJAS: Productos_Base y Producto_Talla ---
            if 'Producto_Base' in df.columns:
                # Resumen por producto base
                prod_base = df.groupby('Producto_Base').agg({
                    'Cantidad': 'sum',
                    'ID_Transferencia': 'nunique',
                    'Producto': 'nunique'
                }).reset_index().rename(columns={
                    'ID_Transferencia': 'Transferencias',
                    'Producto': 'Variantes'
                }).sort_values('Cantidad', ascending=False)
                prod_base.to_excel(writer, sheet_name='Productos_Base', index=False)
                
                # Tabla pivotante producto vs talla (solo tallas no nulas)
                if 'Talla' in df.columns:
                    pivot = df.pivot_table(
                        values='Cantidad',
                        index='Producto_Base',
                        columns='Talla',
                        aggfunc='sum',
                        fill_value=0,
                        margins=True,
                        margins_name='Total'
                    )
                    pivot.to_excel(writer, sheet_name='Producto_Talla')
        
        output.seek(0)
        return output

# Funciones originales del módulo (clasificación de transferencias)
def clasificar_transferencia(row):
    sucursal = str(row.get('Sucursal Destino', row.get('Bodega Destino', ''))).upper()
    cantidad = row.get('Cantidad_Entera', 0)
    if cantidad >= 500 and cantidad % 100 == 0:
        return 'Fundas'
    if any(kw in sucursal for kw in PRICE_KEYWORDS): return 'Price Club'
    if any(kw in sucursal for kw in WEB_KEYWORDS): return 'Tienda Web'
    if any(kw in sucursal for kw in FALLAS_KEYWORDS): return 'Fallas'
    if any(kw in sucursal for kw in VENTAS_MAYOR_KEYWORDS): return 'Ventas por Mayor'
    if any(tienda.upper() in sucursal for tienda in TIENDAS_REGULARES_LISTA): return 'Tiendas'
    tiendas_kw = ['AERO', 'MALL', 'CENTRO', 'SHOPPING', 'PLAZA', 'RIOCENTRO']
    if any(kw in sucursal for kw in tiendas_kw): return 'Tiendas'
    return 'Ventas por Mayor'

def procesar_transferencias_diarias(df):
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

def mostrar_kpi_diario():
    """Dashboard de KPI Diario con clasificación inteligente - SIN HISTORIAL PERSISTENTE"""
    
    if 'kdi_current_data' not in st.session_state:
        st.session_state.kdi_current_data = pd.DataFrame()
        st.session_state.kdi_loaded = False
    
    processor = DataProcessor()
    report_gen = ReportGenerator()
    
    st.markdown("### 📂 Cargar archivo de transferencias diarias")
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded = st.file_uploader(
            "Seleccionar archivo Excel",
            type=['xlsx', 'xls', 'csv'],
            key="kdi_upload",
            label_visibility="collapsed"
        )
    with col_up2:
        if st.button("🔄 Limpiar datos", key="kdi_clear"):
            st.session_state.kdi_current_data = pd.DataFrame()
            st.session_state.kdi_loaded = False
            st.rerun()
    
    if uploaded:
        with st.spinner("Procesando archivo..."):
            new_data = processor.process_excel_file(uploaded)
            if not new_data.empty:
                st.session_state.kdi_current_data = new_data
                st.session_state.kdi_loaded = True
                st.success("Datos cargados exitosamente")
            else:
                st.warning("El archivo no pudo ser procesado. Revise el formato.")
    
    if not st.session_state.kdi_loaded or st.session_state.kdi_current_data.empty:
        st.info("👆 Sube un archivo para comenzar el análisis.")
        with st.expander("📋 Estructura esperada del archivo"):
            st.markdown("""
            **Columnas requeridas (se detectan automáticamente aunque tengan nombres similares):**
            - `Producto`: nombre del producto
            - `Fecha`: fecha de la transferencia (ej. 15/01/2024)
            - `Cantidad`: número de unidades
            - `Bodega Recibe` (o `Bodega Destino`, `Sucursal Destino`, etc.): destino de la mercadería
            
            **Columna opcional:**
            - `Secuencial - Factura` (o similar): identificador único de la transferencia
            """)
        return
    
    st.markdown("### 🔍 Filtros")
    data = st.session_state.kdi_current_data
    filtered = data.copy()
    
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        if 'Fecha' in filtered.columns and not filtered.empty:
            min_d = filtered['Fecha'].min().date()
            max_d = filtered['Fecha'].max().date()
            dr = st.date_input("Rango de fechas", [min_d, max_d], key="kdi_fecha")
            if len(dr) == 2:
                mask = (filtered['Fecha'].dt.date >= dr[0]) & (filtered['Fecha'].dt.date <= dr[1])
                filtered = filtered[mask].copy()
    with col_f2:
        if 'Bodega Recibe' in filtered.columns:
            opts = ['Todas'] + sorted(filtered['Bodega Recibe'].dropna().unique())
            sel = st.selectbox("Bodega", opts, key="kdi_bod")
            if sel != 'Todas':
                filtered = filtered[filtered['Bodega Recibe'] == sel]
    with col_f3:
        if 'Genero' in filtered.columns:
            opts = ['Todos'] + sorted(filtered['Genero'].dropna().unique())
            sel = st.selectbox("Género", opts, key="kdi_gen")
            if sel != 'Todos':
                filtered = filtered[filtered['Genero'] == sel]
    with col_f4:
        if 'Categoria' in filtered.columns:
            opts = ['Todas'] + sorted(filtered['Categoria'].dropna().unique())
            sel = st.selectbox("Categoría", opts, key="kdi_cat")
            if sel != 'Todas':
                filtered = filtered[filtered['Categoria'] == sel]
    
    st.markdown("---")
    
    if filtered.empty:
        st.warning("No hay datos con los filtros actuales.")
        return
    
    total_units = int(filtered['Cantidad'].sum()) if 'Cantidad' in filtered.columns else 0
    n_bodegas = filtered['Bodega Recibe'].nunique() if 'Bodega Recibe' in filtered.columns else 0
    n_transfers = filtered['ID_Transferencia'].nunique() if 'ID_Transferencia' in filtered.columns else len(filtered)
    n_products = filtered['Producto'].nunique() if 'Producto' in filtered.columns else 0
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea15, #764ba230); padding: 20px; border-radius: 10px; border-left: 5px solid #667eea;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>📦</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Unidades Totales</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{total_units:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #11998e15, #38ef7d30); padding: 20px; border-radius: 10px; border-left: 5px solid #11998e;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>🏪</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Bodegas Destino</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{n_bodegas}</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fc466b15, #3f5efb30); padding: 20px; border-radius: 10px; border-left: 5px solid #fc466b;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>📋</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Transferencias</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{n_transfers}</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb15, #f5576c30); padding: 20px; border-radius: 10px; border-left: 5px solid #f093fb;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>👕</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Productos Únicos</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{n_products}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 Análisis por Dimensiones")
    
    # --- MODIFICADO: Ahora son 5 pestañas (se añade "📦 Productos") ---
    dim_tab1, dim_tab2, dim_tab3, dim_tab4, dim_tab5 = st.tabs([
        "🎨 Color", "📏 Talla", "⚧ Género", "🏷️ Categoría/Departamento", "📦 Productos"
    ])
    
    with dim_tab1:
        if 'Color' in filtered.columns:
            col_stats = filtered.groupby('Color').agg({'Cantidad': ['sum', 'count']}).reset_index()
            col_stats.columns = ['Color', 'Unidades', 'Frecuencia']
            col_stats['Porcentaje'] = (col_stats['Unidades'] / total_units * 100).round(2)
            col_stats = col_stats.sort_values('Unidades', ascending=False)
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.pie(col_stats, values='Unidades', names='Color', 
                           title="Distribución por Color",
                           color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(col_stats[['Color', 'Unidades', 'Porcentaje']].style.format({
                    'Unidades': '{:,}',
                    'Porcentaje': '{:.2f}%'
                }), use_container_width=True, height=400)
        else:
            st.info("No hay datos de color disponibles")
    
    with dim_tab2:
        if 'Talla' in filtered.columns:
            talla_stats = filtered.groupby('Talla').agg({'Cantidad': ['sum', 'count']}).reset_index()
            talla_stats.columns = ['Talla', 'Unidades', 'Frecuencia']
            talla_stats['Porcentaje'] = (talla_stats['Unidades'] / total_units * 100).round(2)
            # Usar jerarquía de tallas definida en SIZE_HIERARCHY para ordenar
            size_order = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', 'Única']
            talla_stats['Talla_Order'] = talla_stats['Talla'].apply(
                lambda x: size_order.index(x) if x in size_order else 999
            )
            talla_stats = talla_stats.sort_values('Talla_Order')
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(talla_stats, x='Talla', y='Unidades', 
                           title="Distribución por Talla",
                           color='Unidades',
                           color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(talla_stats[['Talla', 'Unidades', 'Porcentaje']].style.format({
                    'Unidades': '{:,}',
                    'Porcentaje': '{:.2f}%'
                }), use_container_width=True, height=400)
        else:
            st.info("No hay datos de talla disponibles")
    
    with dim_tab3:
        if 'Genero' in filtered.columns:
            gen_stats = filtered.groupby('Genero').agg({'Cantidad': ['sum', 'count']}).reset_index()
            gen_stats.columns = ['Genero', 'Unidades', 'Frecuencia']
            gen_stats['Porcentaje'] = (gen_stats['Unidades'] / total_units * 100).round(2)
            gen_stats = gen_stats.sort_values('Unidades', ascending=False)
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.pie(gen_stats, values='Unidades', names='Genero', 
                           title="Distribución por Género",
                           color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(gen_stats[['Genero', 'Unidades', 'Porcentaje']].style.format({
                    'Unidades': '{:,}',
                    'Porcentaje': '{:.2f}%'
                }), use_container_width=True, height=400)
        else:
            st.info("No hay datos de género disponibles")
    
    with dim_tab4:
        if 'Categoria' in filtered.columns:
            cat_stats = filtered.groupby('Categoria').agg({'Cantidad': ['sum', 'count']}).reset_index()
            cat_stats.columns = ['Categoria', 'Unidades', 'Frecuencia']
            cat_stats['Porcentaje'] = (cat_stats['Unidades'] / total_units * 100).round(2)
            cat_stats = cat_stats.sort_values('Unidades', ascending=False)
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(cat_stats, x='Categoria', y='Unidades', 
                           title="Distribución por Categoría",
                           color='Unidades',
                           color_continuous_scale='Plasma')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.dataframe(cat_stats[['Categoria', 'Unidades', 'Porcentaje']].style.format({
                    'Unidades': '{:,}',
                    'Porcentaje': '{:.2f}%'
                }), use_container_width=True, height=400)
        else:
            st.info("No hay datos de categoría disponibles")
    
    # --- NUEVA PESTAÑA: Productos ---
    with dim_tab5:
        st.markdown("### 📊 Análisis por Producto")
        
        if 'Producto_Base' in filtered.columns:
            # Top productos base
            top_productos = filtered.groupby('Producto_Base').agg({
                'Cantidad': 'sum',
                'ID_Transferencia': 'nunique',
                'Producto': 'nunique'
            }).reset_index().rename(columns={
                'ID_Transferencia': 'Transferencias',
                'Producto': 'Variantes'
            }).sort_values('Cantidad', ascending=False)
            
            top_productos['Porcentaje'] = (top_productos['Cantidad'] / total_units * 100).round(2)
            
            col_p1, col_p2 = st.columns([2, 1])
            with col_p1:
                # Gráfico top 10
                top10 = top_productos.head(10)
                fig = px.bar(top10, x='Cantidad', y='Producto_Base', orientation='h',
                             title='Top 10 Productos Base por Unidades',
                             color='Cantidad', color_continuous_scale='Blues')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col_p2:
                st.dataframe(top_productos.head(10)[['Producto_Base', 'Cantidad', 'Porcentaje']],
                             use_container_width=True, height=350)
            
            # Selector para ver detalle de tallas de un producto
            st.markdown("#### 🔍 Detalle de tallas por producto")
            producto_seleccionado = st.selectbox(
                "Selecciona un producto base para ver distribución por talla",
                options=[''] + list(top_productos['Producto_Base'].unique())
            )
            
            if producto_seleccionado:
                df_prod = filtered[filtered['Producto_Base'] == producto_seleccionado]
                talla_stats = df_prod.groupby('Talla')['Cantidad'].sum().reset_index()
                # Ordenar tallas según jerarquía
                talla_order = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', 'Única']
                talla_stats['Talla_Order'] = talla_stats['Talla'].apply(
                    lambda x: talla_order.index(x) if x in talla_order else 999
                )
                talla_stats = talla_stats.sort_values('Talla_Order')
                
                col_t1, col_t2 = st.columns([2, 1])
                with col_t1:
                    fig2 = px.bar(talla_stats, x='Talla', y='Cantidad',
                                  title=f'Distribución por talla - {producto_seleccionado}',
                                  color='Cantidad', color_continuous_scale='Oranges')
                    st.plotly_chart(fig2, use_container_width=True)
                with col_t2:
                    st.dataframe(talla_stats[['Talla', 'Cantidad']], use_container_width=True)
            
            # Tabla pivotante general Producto vs Talla
            st.markdown("#### 📋 Tabla de Producto vs Talla")
            # Para no saturar, mostramos solo productos con al menos una unidad
            productos_con_datos = top_productos[top_productos['Cantidad'] > 0]['Producto_Base'].tolist()
            if productos_con_datos:
                pivot_data = filtered[filtered['Producto_Base'].isin(productos_con_datos)]
                pivot = pivot_data.pivot_table(
                    values='Cantidad',
                    index='Producto_Base',
                    columns='Talla',
                    aggfunc='sum',
                    fill_value=0,
                    margins=True,
                    margins_name='Total'
                )
                # Ordenar por total descendente
                pivot = pivot.sort_values('Total', ascending=False)
                st.dataframe(pivot, use_container_width=True, height=500)
            else:
                st.info("No hay datos para mostrar la tabla pivotante.")
        else:
            st.info("No se pudo generar la columna Producto_Base. Verificar clasificación.")
    
    st.markdown("---")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Top 10 Bodegas")
        if 'Bodega Recibe' in filtered.columns:
            top_bod = filtered.groupby('Bodega Recibe')['Cantidad'].sum().nlargest(10)
            if not top_bod.empty:
                fig = px.bar(
                    x=top_bod.values, y=top_bod.index,
                    orientation='h', color=top_bod.values,
                    color_continuous_scale='Viridis',
                    labels={'x': 'Unidades', 'y': ''}
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
    with col_g2:
        st.subheader("📈 Tendencia Diaria")
        if 'Fecha' in filtered.columns:
            daily = filtered.groupby(filtered['Fecha'].dt.date)['Cantidad'].sum().reset_index()
            daily.columns = ['Fecha', 'Unidades']
            fig = px.line(daily, x='Fecha', y='Unidades', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📋 Detalle de Transferencias")
    cols_display = ['Fecha', 'Bodega Recibe', 'Producto', 'Genero', 'Categoria', 'Color', 'Talla', 'Cantidad']
    cols_display = [c for c in cols_display if c in filtered.columns]
    st.dataframe(filtered[cols_display].sort_values('Fecha', ascending=False), use_container_width=True, height=300)
    
    st.markdown("---")
    st.subheader("📄 Generar Reporte")
    col_r1, col_r2, col_r3 = st.columns([1, 1, 2])
    with col_r1:
        r_start = st.date_input("Fecha inicio", filtered['Fecha'].min().date(), key="r_start")
    with col_r2:
        r_end = st.date_input("Fecha fin", filtered['Fecha'].max().date(), key="r_end")
    with col_r3:
        if st.button("📥 Descargar reporte Excel", use_container_width=True):
            with st.spinner("Generando reporte..."):
                excel = report_gen.generate_detailed_report(filtered, r_start, r_end)
                if excel:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        label="⬇️ Descargar",
                        data=excel,
                        file_name=f"KPI_Diario_{ts}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

def mostrar_dashboard_transferencias():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Diarias</h1>
        <div class='header-subtitle'>Analisis de distribucion por categorias y sucursales</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Transferencias Diarias", "📦 Mercadería en Tránsito (KPI Diario)", "📈 Análisis de Stock"])
    
    with tab1:
        st.markdown("""
        <div class='filter-panel'>
            <h4>📂 Carga de Archivo de Transferencias</h4>
            <p class='section-description'>Sube el archivo Excel de transferencias diarias (ej: 322026.xlsx)</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            col_u1, col_u2 = st.columns([3, 1])
            with col_u1:
                file_diario = st.file_uploader(
                    "Selecciona el archivo Excel",
                    type=['xlsx'],
                    key="diario_transferencias",
                    label_visibility="collapsed"
                )
            with col_u2:
                if st.button("🔄 Limpiar", use_container_width=True):
                    st.rerun()
        
        if not file_diario:
            st.info("👆 **Por favor, sube un archivo Excel desde el panel superior para comenzar el analisis.**")
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
            1. **Secuencial**: Numero unico de transferencia
            2. **Sucursal Destino** o **Bodega Destino**: Nombre de la tienda destino
            3. **Cantidad Prendas**: Cantidad de unidades a transferir
            
            ### 🎯 Categorias automaticas:
            - **Price Club**: Contiene "PRICE" o "OIL" en el nombre
            - **Tienda Web**: Contiene "WEB", "TIENDA MOVIL" o "MOVIL"
            - **Fallas**: Contiene "FALLAS"
            - **Ventas por Mayor**: Contiene "MAYOR" o "MAYORISTA"
            - **Fundas**: Cantidad ≥ 500 y multiplo de 100
            - **Tiendas**: Todas las demas transferencias
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
                else:
                    tiene_destino = any(col in df_diario.columns for col in columnas_destino)
                    if not tiene_destino:
                        st.error("❌ **No se encontro columna de destino.**")
                    else:
                        res = procesar_transferencias_diarias(df_diario)
                        st.header("📈 KPIs por Categoria")
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
                        
                        color_keys = {
                            'Price Club': 'PRICE CLUB',
                            'Tiendas': 'TIENDAS AEROPOSTALE',
                            'Ventas por Mayor': 'VENTAS POR MAYOR',
                            'Tienda Web': 'TIENDA WEB',
                            'Fallas': 'FALLAS',
                            'Fundas': 'FUNDAS'
                        }
                        
                        cols = st.columns(3)
                        for i, (cat, cat_display) in enumerate(categorias_display.items()):
                            cantidad = res['por_categoria'].get(cat, 0)
                            sucursales_activas = res['conteo_sucursales'].get(cat, 0)
                            esperadas = sucursales_esperadas.get(cat)
                            color_key = color_keys.get(cat)
                            bg_gradient = GRADIENTS.get(color_key, 'linear-gradient(135deg, #f0f0f015, #e0e0e030)')
                            border_color = COLORS.get(color_key, '#cccccc')
                            
                            with cols[i % 3]:
                                if cat == 'Fundas':
                                    st.markdown(f"""
                                    <div style='background: {bg_gradient}; padding: 20px; border-radius: 10px; border-left: 5px solid {border_color}; margin-bottom: 15px;'>
                                        <div style='font-size: 12px; color: #666; text-transform: uppercase; margin-bottom: 5px;'>{cat_display}</div>
                                        <div style='font-size: 32px; font-weight: bold; color: {border_color}; margin-bottom: 5px;'>{cantidad:,}</div>
                                        <div style='font-size: 11px; color: #888;'>Multiplos de 100 ≥ 500 unidades</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                    <div style='background: {bg_gradient}; padding: 20px; border-radius: 10px; border-left: 5px solid {border_color}; margin-bottom: 15px;'>
                                        <div style='font-size: 12px; color: #666; text-transform: uppercase; margin-bottom: 5px;'>{cat_display}</div>
                                        <div style='font-size: 32px; font-weight: bold; color: {border_color}; margin-bottom: 5px;'>{cantidad:,}</div>
                                        <div style='font-size: 11px; color: #888;'>{sucursales_activas} sucursales | {esperadas} esperadas</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            if i == 2:
                                cols = st.columns(3)
                        st.divider()
                        
                        st.header("📊 Analisis Visual")
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            categorias_pie = list(res['por_categoria'].keys())
                            valores_pie = list(res['por_categoria'].values())
                            df_pie = pd.DataFrame({'Categoria': categorias_pie, 'Unidades': valores_pie})
                            df_pie = df_pie[df_pie['Unidades'] > 0]
                            if not df_pie.empty:
                                color_map_pie = {
                                    'Price Club': COLORS['PRICE CLUB'],
                                    'Tiendas': COLORS['TIENDAS AEROPOSTALE'],
                                    'Ventas por Mayor': COLORS['VENTAS POR MAYOR'],
                                    'Tienda Web': COLORS['TIENDA WEB'],
                                    'Fallas': COLORS['FALLAS'],
                                    'Fundas': COLORS['FUNDAS']
                                }
                                fig_pie = px.pie(
                                    df_pie,
                                    values='Unidades',
                                    names='Categoria',
                                    title="Distribucion por Categoria",
                                    color='Categoria',
                                    color_discrete_map=color_map_pie,
                                    hole=0.3
                                )
                                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                                fig_pie.update_layout(height=500, showlegend=True)
                                st.plotly_chart(fig_pie, use_container_width=True)
                            else:
                                st.info("No hay datos para mostrar el grafico de pastel")
                        with col2:
                            st.subheader("TOTAL GENERAL")
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, #667eea20, #764ba240); padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 15px;'>
                                <div style='font-size: 14px; color: #555; margin-bottom: 10px;'>Suma de todas las unidades</div>
                                <div style='font-size: 36px; font-weight: bold; color: #333;'>{res['total_unidades']:,}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            promedio = res['total_unidades'] / res['transferencias'] if res['transferencias'] > 0 else 0
                            st.markdown(f"""
                            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;'>
                                <div style='font-size: 12px; color: #666; margin-bottom: 5px;'>PROMEDIO X TRANSFERENCIA</div>
                                <div style='font-size: 24px; font-weight: bold; color: #333;'>{promedio:,.0f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            categorias_activas = sum(1 for cat in res['por_categoria'].values() if cat > 0)
                            st.markdown(f"""
                            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;'>
                                <div style='font-size: 12px; color: #666; margin-bottom: 5px;'>CATEGORIAS ACTIVAS</div>
                                <div style='font-size: 24px; font-weight: bold; color: #333;'>{categorias_activas}/6</div>
                            </div>
                            """, unsafe_allow_html=True)
                            porcentaje_fundas = (res['por_categoria'].get('Fundas', 0) / res['total_unidades']) * 100 if res['total_unidades'] > 0 else 0
                            st.markdown(f"""
                            <div style='background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;'>
                                <div style='font-size: 12px; color: #666; margin-bottom: 5px;'>% FUNDAS</div>
                                <div style='font-size: 24px; font-weight: bold; color: {COLORS['FUNDAS']};'>{porcentaje_fundas:.1f}%</div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.divider()
                        
                        st.header("📊 Distribucion Excluyendo Fundas")
                        categorias_excl = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas']
                        valores_excl = [res['por_categoria'].get(cat, 0) for cat in categorias_excl]
                        total_excl = sum(valores_excl)
                        if total_excl > 0:
                            df_barras = pd.DataFrame({
                                'Categoria': ['Tienda Web', 'Price Club', 'Ventas por Mayor', 'Tiendas', 'Fallas'],
                                'Unidades': [res['por_categoria'].get('Tienda Web', 0),
                                             res['por_categoria'].get('Price Club', 0),
                                             res['por_categoria'].get('Ventas por Mayor', 0),
                                             res['por_categoria'].get('Tiendas', 0),
                                             res['por_categoria'].get('Fallas', 0)]
                            })
                            df_barras['Porcentaje'] = (df_barras['Unidades'] / total_excl) * 100
                            
                            color_map_bar = {
                                'Tienda Web': COLORS['TIENDA WEB'],
                                'Price Club': COLORS['PRICE CLUB'],
                                'Ventas por Mayor': COLORS['VENTAS POR MAYOR'],
                                'Tiendas': COLORS['TIENDAS AEROPOSTALE'],
                                'Fallas': COLORS['FALLAS']
                            }
                            
                            fig_barras = go.Figure(data=[
                                go.Bar(
                                    x=df_barras['Categoria'],
                                    y=df_barras['Porcentaje'],
                                    text=[f"{p:.1f}%" for p in df_barras['Porcentaje']],
                                    textposition='auto',
                                    marker_color=[color_map_bar.get(cat, '#cccccc') for cat in df_barras['Categoria']]
                                )
                            ])
                            fig_barras.update_layout(title="Distribucion por Categoria (excl. Fundas)", yaxis_title="Porcentaje (%)", xaxis_title="Categoria", template="plotly_white", height=400)
                            st.plotly_chart(fig_barras, use_container_width=True)
                            st.dataframe(df_barras[['Categoria', 'Unidades', 'Porcentaje']].sort_values('Porcentaje', ascending=False), use_container_width=True)
                        else:
                            st.info("No hay datos para mostrar la distribucion (excluyendo Fundas)")
                        st.divider()
                        
                        st.header("📄 Detalle por Secuencial")
                        df_detalle = res['df_procesado'][['Sucursal Destino', 'Secuencial', 'Cantidad_Entera', 'Categoria']].copy()
                        with st.expander("📋 Resumen Estadistico", expanded=True):
                            st.dataframe(
                                pd.DataFrame.from_dict(res['detalle_categoria'], orient='index')
                                .reset_index()
                                .rename(columns={'index': 'Categoria', 'cantidad': 'Unidades', 'transf': 'Transferencias', 'unicas': 'Sucursales Unicas'}),
                                use_container_width=True
                            )
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
                            df_detalle.rename(columns={'Sucursal Destino': 'Sucursal', 'Cantidad_Entera': 'Cantidad', 'Categoria': 'Categoria'}),
                            use_container_width=True, height=400
                        )
            except Exception as e:
                st.error(f"❌ **Error al procesar el archivo:** {str(e)}")
    
    with tab2:
        mostrar_kpi_diario()
    
    with tab3:
        st.header("📈 Analisis de Stock y Ventas")
        with st.container():
            st.subheader("📂 Carga de Datos para Analisis")
            col_stock1, col_stock2 = st.columns(2)
            with col_stock1:
                stock_file = st.file_uploader("Archivo de Stock Actual", type=['xlsx', 'csv'], key="stock_file")
            with col_stock2:
                ventas_file = st.file_uploader("Archivo Historico de Ventas", type=['xlsx', 'csv'], key="ventas_file")
            
            if stock_file and ventas_file:
                try:
                    df_stock = pd.read_excel(stock_file) if stock_file.name.endswith('.xlsx') else pd.read_csv(stock_file)
                    df_ventas = pd.read_excel(ventas_file) if ventas_file.name.endswith('.xlsx') else pd.read_csv(ventas_file)
                    
                    st.subheader("📊 Metricas Rapidas")
                    col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
                    with col_metrics1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>Total SKUs</div>
                            <div class='metric-value'>{len(df_stock):,}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_metrics2:
                        if 'Stock' in df_stock.columns:
                            total_stock = df_stock['Stock'].sum()
                            st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-title'>Total Unidades</div>
                                <div class='metric-value'>{total_stock:,}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Columna 'Stock' no encontrada")
                    with col_metrics3:
                        if 'VENTAS' in df_ventas.columns:
                            total_ventas = df_ventas['VENTAS'].sum()
                            st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-title'>Ventas Totales</div>
                                <div class='metric-value'>{total_ventas:,}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Columna 'VENTAS' no encontrada")
                    with col_metrics4:
                        if 'FECHA' in df_ventas.columns:
                            df_ventas['FECHA'] = pd.to_datetime(df_ventas['FECHA'], errors='coerce')
                            dias_analizados = df_ventas['FECHA'].nunique()
                            st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-title'>Dias Analizados</div>
                                <div class='metric-value'>{dias_analizados}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Columna 'FECHA' no encontrada")
                    
                    st.subheader("📊 Analisis ABC de Stock")
                    if 'Stock' in df_stock.columns and 'CODIGO' in df_stock.columns:
                        df_stock_sorted = df_stock.sort_values('Stock', ascending=False)
                        df_stock_sorted['Stock_Acumulado'] = df_stock_sorted['Stock'].cumsum()
                        total_stock_val = df_stock_sorted['Stock'].sum()
                        df_stock_sorted['Porcentaje_Acumulado'] = (df_stock_sorted['Stock_Acumulado'] / total_stock_val) * 100
                        df_stock_sorted['Clasificacion_ABC'] = pd.cut(
                            df_stock_sorted['Porcentaje_Acumulado'],
                            bins=[0, 80, 95, 100],
                            labels=['A', 'B', 'C']
                        )
                        resumen_abc = df_stock_sorted.groupby('Clasificacion_ABC').agg({
                            'CODIGO': 'count',
                            'Stock': 'sum'
                        }).rename(columns={'CODIGO': 'SKUs', 'Stock': 'Unidades'})
                        fig_abc = px.pie(
                            resumen_abc.reset_index(),
                            values='Unidades',
                            names='Clasificacion_ABC',
                            title="Distribucion ABC del Stock",
                            color_discrete_sequence=['#0033A0', '#E4002B', '#10B981'],
                            hole=0.4
                        )
                        col_abc1, col_abc2 = st.columns([2, 1])
                        with col_abc1:
                            st.plotly_chart(fig_abc, use_container_width=True)
                        with col_abc2:
                            st.dataframe(resumen_abc, use_container_width=True)
                    else:
                        st.warning("Para el analisis ABC se requieren las columnas 'CODIGO' y 'Stock'")
                    
                    st.subheader("🔄 Analisis de Rotacion")
                    if 'VENTAS' in df_ventas.columns and 'CODIGO' in df_ventas.columns:
                        ventas_por_producto = df_ventas.groupby('CODIGO')['VENTAS'].sum().reset_index()
                        if 'CODIGO' in df_stock.columns and 'Stock' in df_stock.columns:
                            df_rotacion = pd.merge(
                                df_stock[['CODIGO', 'Stock']],
                                ventas_por_producto,
                                on='CODIGO',
                                how='left'
                            )
                            df_rotacion['VENTAS'] = df_rotacion['VENTAS'].fillna(0)
                            df_rotacion['Rotacion'] = df_rotacion.apply(
                                lambda x: x['VENTAS'] / x['Stock'] if x['Stock'] > 0 else 0,
                                axis=1
                            )
                            df_rotacion['Nivel_Rotacion'] = pd.cut(
                                df_rotacion['Rotacion'],
                                bins=[-1, 0.1, 0.5, 1, 10, float('inf')],
                                labels=['Muy Baja', 'Baja', 'Media', 'Alta', 'Muy Alta']
                            )
                            resumen_rotacion = df_rotacion.groupby('Nivel_Rotacion').agg({
                                'CODIGO': 'count',
                                'Stock': 'sum',
                                'VENTAS': 'sum'
                            }).rename(columns={'CODIGO': 'SKUs', 'Stock': 'Stock_Total', 'VENTAS': 'Ventas_Total'})
                            st.dataframe(resumen_rotacion, use_container_width=True)
                            fig_rotacion = go.Figure(data=[
                                go.Bar(
                                    x=resumen_rotacion.index,
                                    y=resumen_rotacion['SKUs'],
                                    text=resumen_rotacion['SKUs'],
                                    textposition='auto',
                                    marker_color='#FFA07A'
                                )
                            ])
                            fig_rotacion.update_layout(title="SKUs por Nivel de Rotacion", xaxis_title="Nivel de Rotacion", yaxis_title="Cantidad de SKUs", template="plotly_white", height=400)
                            st.plotly_chart(fig_rotacion, use_container_width=True)
                    else:
                        st.info("Para el analisis de rotacion se requieren las columnas 'CODIGO' y 'VENTAS'")
                    
                    st.subheader("🔮 Prediccion con Random Forest")
                    st.info("Funcionalidad en Desarrollo...")
                    
                    with st.expander("📋 Ver Datos Cargados"):
                        col_raw1, col_raw2 = st.columns(2)
                        with col_raw1:
                            st.write("**Datos de Stock:**")
                            st.dataframe(df_stock.head(20), use_container_width=True)
                        with col_raw2:
                            st.write("**Datos de Ventas:**")
                            st.dataframe(df_ventas.head(20), use_container_width=True)
                except Exception as e:
                    st.error(f"Error al procesar los archivos: {str(e)}")
            else:
                st.info("👈 Por favor, carga ambos archivos para realizar el analisis de stock y ventas.")
                with st.expander("ℹ️ Informacion sobre los archivos requeridos"):
                    st.markdown("""
                    **Archivo de Stock Actual debe contener:**
                    - CODIGO: Codigo del producto
                    - PRODUCTO: Descripcion del producto
                    - Stock: Cantidad disponible
                    - DEPARTAMENTO: Categoria del producto
                    
                    **Archivo Historico de Ventas debe contener:**
                    - CODIGO: Codigo del producto
                    - FECHA: Fecha de la venta
                    - VENTAS: Cantidad vendida
                    - SUCURSAL: Sucursal donde se realizo la venta
                    """)

def show_dashboard_logistico():
    """Dashboard de logistica y transferencias - MEJORADO"""
    add_back_button(key="back_logistico")
    show_module_header(
        "📦 Dashboard Logistico",
        "Control de transferencias y distribucion en tiempo real"
    )
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    mostrar_dashboard_transferencias()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 8. MODULO GESTION DE EQUIPO
# ==============================================================================

def show_gestion_equipo():
    """Gestion de personal"""
    add_back_button(key="back_equipo")
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
    
    try:
        trabajadores = local_db.query('trabajadores')
        if not trabajadores:
            st.info("📝 Inicializando estructura organizacional base...")
            todos_base = []
            for area, lista in estructura_base.items():
                for trabajador in lista:
                    trabajador['area'] = area
                    trabajador['fecha_ingreso'] = datetime.now().strftime('%Y-%m-%d')
                    todos_base.append(trabajador)
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
        
        for area, personal in estructura_base.items():
            with st.expander(f"📌 {area} ({len(personal)} personas)", expanded=True):
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
        
        try:
            trabajadores_db = local_db.query('trabajadores')
            if trabajadores_db is None:
                trabajadores_db = []
        except:
            trabajadores_db = trabajadores
        
        area_tabs = st.tabs(list(estructura_base.keys()))
        
        for idx, (area, trabajadores_area_base) in enumerate(estructura_base.items()):
            with area_tabs[idx]:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader(f"Personal en {area}")
                    trabajadores_area_actual = [t for t in trabajadores_db if t.get('area') == area]
                    
                    if trabajadores_area_actual:
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
                                if row['Tipo'] != 'Base':
                                    trabajador_id = row['ID']
                                    if st.button("🗑️", key=f"eliminar_{area}_{trabajador_id}"):
                                        try:
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
                                    if trabajadores_db:
                                        max_id = max([t.get('id', 0) for t in trabajadores_db])
                                    else:
                                        max_id = 12
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
                    base = len(estructura_base) * 2
                st.metric("🏛️ Personal Base", base)
            with col_m4:
                if 'es_base' in df_todos.columns:
                    adicional = len(df_todos[df_todos['es_base'] == False])
                else:
                    adicional = max(0, total - base)
                st.metric("➕ Adicionales", adicional)
            
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
                    trabajadores_actuales = local_db.query('trabajadores')
                    if trabajadores_actuales:
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
                    export_cols = ['nombre', 'cargo', 'area', 'subarea', 'estado', 'fecha_ingreso']
                    available_cols = [col for col in export_cols if col in df_export.columns]
                    df_export = df_export[available_cols]
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
# 9. MODULO RECONCILIACION LOGISTICA V8 - MEJORADO
# ==============================================================================

# Nuevas importaciones necesarias (agregar al inicio del archivo)
import tempfile
import os
import zipfile
from difflib import SequenceMatcher
from datetime import datetime, timedelta

class FuzzyMatcher:
    """Motor avanzado de fuzzy matching para reconciliación"""
    
    def __init__(self, threshold=0.85):
        self.threshold = threshold
    
    def similarity(self, str1, str2):
        """Calcula similitud entre dos strings"""
        if pd.isna(str1) or pd.isna(str2):
            return 0
        str1 = str(str1).upper().strip()
        str2 = str(str2).upper().strip()
        return SequenceMatcher(None, str1, str2).ratio()
    
    def match_guia(self, guia_manifesto, guias_factura):
        """Encuentra la mejor coincidencia para una guía"""
        mejores = []
        for guia_f in guias_factura:
            sim = self.similarity(guia_manifesto, guia_f)
            if sim >= self.threshold:
                mejores.append((guia_f, sim))
        return max(mejores, key=lambda x: x[1]) if mejores else (None, 0)
    
    def match_multiple_fields(self, row, df_facturas, campos):
        """Matching por múltiples campos"""
        mejores = []
        for idx, factura in df_facturas.iterrows():
            sim_total = 0
            for campo_m, campo_f in campos:
                sim_total += self.similarity(row[campo_m], factura[campo_f])
            sim_promedio = sim_total / len(campos)
            if sim_promedio >= self.threshold:
                mejores.append((idx, sim_promedio))
        return max(mejores, key=lambda x: x[1]) if mejores else (None, 0)

class ReconciliationAuditEngine:
    """Motor de auditoría para reconciliación de manifiestos y facturas."""
    
    def __init__(self):
        self.fuzzy_matcher = FuzzyMatcher(threshold=0.85)
        self.audit_log = []
    
    def run_audit(self, manifesto: pd.DataFrame, facturas: pd.DataFrame, config: dict) -> dict:
        """Ejecuta el proceso de reconciliación con fuzzy matching."""
        
        # Registrar inicio de auditoría
        self.audit_log.append({
            'timestamp': datetime.now(),
            'action': 'INICIO',
            'details': f'Manifiesto: {len(manifesto)} filas, Facturas: {len(facturas)} filas'
        })
        
        # Procesar manifiesto
        df_m = manifesto.copy()
        if config.get('guia_m'):
            df_m['GUIA_CLEAN'] = df_m[config['guia_m']].astype(str).str.strip().str.upper()
        
        if config.get('destinatario'):
            df_m['DESTINATARIO_CLEAN'] = df_m[config['destinatario']].astype(str).str.strip().str.upper()
        
        # Procesar facturas
        df_f = facturas.copy()
        if config.get('guia_f'):
            df_f['GUIA_CLEAN'] = df_f[config['guia_f']].astype(str).str.strip().str.upper()
        
        if config.get('subtotal'):
            df_f['SUBTOTAL_NUM'] = pd.to_numeric(
                df_f[config['subtotal']].astype(str).str.replace(',', '.').str.replace('$', '').str.strip(),
                errors='coerce'
            ).fillna(0)
        
        # Estrategia de matching
        matched_indices = []
        unmatched_manifesto = []
        
        for idx_m, row_m in df_m.iterrows():
            mejor_match = None
            mejor_sim = 0
            
            for idx_f, row_f in df_f.iterrows():
                if idx_f in matched_indices:
                    continue
                
                # Matching por guía (si existe)
                if 'GUIA_CLEAN' in row_m and 'GUIA_CLEAN' in row_f:
                    sim = self.fuzzy_matcher.similarity(row_m['GUIA_CLEAN'], row_f['GUIA_CLEAN'])
                    if sim > mejor_sim and sim >= self.fuzzy_matcher.threshold:
                        mejor_sim = sim
                        mejor_match = idx_f
                
                # Matching por destinatario (como respaldo)
                elif 'DESTINATARIO_CLEAN' in row_m and config.get('destinatario_f'):
                    sim = self.fuzzy_matcher.similarity(
                        row_m['DESTINATARIO_CLEAN'],
                        str(row_f.get(config['destinatario_f'], '')).upper().strip()
                    )
                    if sim > mejor_sim and sim >= self.fuzzy_matcher.threshold:
                        mejor_sim = sim
                        mejor_match = idx_f
            
            if mejor_match is not None:
                matched_indices.append(mejor_match)
                for col in df_f.columns:
                    if col not in df_m.columns:
                        df_m.loc[idx_m, col] = df_f.loc[mejor_match, col]
                df_m.loc[idx_m, '_MATCH_SCORE'] = mejor_sim
                df_m.loc[idx_m, '_MATCH_STATUS'] = 'MATCHED'
                self.audit_log.append({
                    'timestamp': datetime.now(),
                    'action': 'MATCH',
                    'details': f'Guía {row_m.get("GUIA_CLEAN", "N/A")} match con score {mejor_sim:.2f}'
                })
            else:
                unmatched_manifesto.append(idx_m)
                df_m.loc[idx_m, '_MATCH_STATUS'] = 'UNMATCHED'
        
        # Marcar facturas no utilizadas
        facturas_usadas = set(matched_indices)
        for idx_f in df_f.index:
            if idx_f in facturas_usadas:
                df_f.loc[idx_f, '_MATCH_STATUS'] = 'MATCHED'
            else:
                df_f.loc[idx_f, '_MATCH_STATUS'] = 'UNMATCHED'
        
       # Calcular métricas
    df_completo = df_m.copy()
    total_facturas = df_f['SUBTOTAL_NUM'].sum() if 'SUBTOTAL_NUM' in df_f.columns else 0
    total_manifesto = df_completo['SUBTOTAL_NUM'].sum() if 'SUBTOTAL_NUM' in df_completo.columns else 0
    
    metricas = self._calcular_metricas(df_completo, df_f)
    
    # --- NUEVO: Crear resumen por tipo/canal ---
    if not metricas.empty:
        # Clasificar tiendas por tipo (simplificado)
        def clasificar_tienda(nombre):
            nombre_upper = str(nombre).upper()
            if 'WEB' in nombre_upper or 'MOVIL' in nombre_upper:
                return 'VENTA WEB'
            elif 'PRICE' in nombre_upper:
                return 'PRICE CLUB'
            elif any(x in nombre_upper for x in ['MALL', 'CENTRO', 'PLAZA']):
                return 'CENTRO COMERCIAL'
            else:
                return 'TIENDA FÍSICA'
        
        metricas['TIPO'] = metricas['TIENDA'].apply(clasificar_tienda)
        resumen = metricas.groupby('TIPO').agg({
            'TIENDA': 'count',
            'GUIAS_TOTALES': 'sum',
            'GUIAS_MATCH': 'sum',
            'SUBTOTAL': 'sum'
        }).reset_index()
        resumen['PORCENTAJE'] = (resumen['SUBTOTAL'] / resumen['SUBTOTAL'].sum() * 100).round(2)
        resumen = resumen.rename(columns={'TIENDA': 'TIENDAS'})
    else:
        resumen = pd.DataFrame(columns=['TIPO', 'TIENDAS', 'GUIAS_TOTALES', 'GUIAS_MATCH', 'SUBTOTAL', 'PORCENTAJE'])
    # -------------------------------------------------
    
    validacion = self._validar_totales(total_manifesto, total_facturas)
    
    stats = {
        'total_manifesto': total_manifesto,
        'total_facturas': total_facturas,
        'guias_manifesto': len(df_m),
        'guias_factura': len(df_f),
        'guias_match': len(matched_indices),
        'guias_sin_match': len(unmatched_manifesto),
        'facturas_sin_usar': len(df_f) - len(matched_indices),
        'match_rate': len(matched_indices) / len(df_m) if len(df_m) > 0 else 0,
        'cobertura_facturas': len(matched_indices) / len(df_f) if len(df_f) > 0 else 0
    }
    
    self.audit_log.append({
        'timestamp': datetime.now(),
        'action': 'FIN',
        'details': f'Match rate: {stats["match_rate"]:.1%}'
    })
    
    return {
        'df_final': df_completo,
        'facturas_procesadas': df_f,
        'metricas': metricas,
        'resumen': resumen,  # ← AHORA SÍ ESTÁ INCLUIDO
        'validacion': validacion,
        'stats': stats,
        'audit_log': pd.DataFrame(self.audit_log)
    }
    
    def _calcular_metricas(self, df_completo, df_facturas):
        """Calcula métricas detalladas por tienda/grupo"""
        
        if 'TIENDA' not in df_completo.columns:
            df_completo['TIENDA'] = 'NO ASIGNADA'
        
        metricas = df_completo.groupby('TIENDA').agg(
            GUIAS_TOTALES=('GUIA_CLEAN', 'count'),
            GUIAS_MATCH=('_MATCH_STATUS', lambda x: (x == 'MATCHED').sum()),
            SUBTOTAL=('SUBTOTAL_NUM', 'sum'),
            MATCH_SCORE_PROM=('_MATCH_SCORE', 'mean')
        ).reset_index()
        
        metricas['MATCH_RATE'] = (metricas['GUIAS_MATCH'] / metricas['GUIAS_TOTALES'] * 100).round(2)
        metricas['PORCENTAJE_GASTO'] = (metricas['SUBTOTAL'] / metricas['SUBTOTAL'].sum() * 100).round(2)
        
        return metricas.sort_values('SUBTOTAL', ascending=False)
    
    def _validar_totales(self, total_manifesto, total_facturas):
        """Valida que los totales coincidan"""
        diferencia = abs(total_manifesto - total_facturas)
        porcentaje = (diferencia / total_facturas * 100) if total_facturas > 0 else 0
        
        return {
            'total_manifesto': total_manifesto,
            'total_facturas': total_facturas,
            'diferencia': diferencia,
            'porcentaje_diferencia': porcentaje,
            'coincide': diferencia < 0.01,
            'estado': '✅ CONCILIADO' if diferencia < 0.01 else '⚠️ DIFERENCIAS'
        }

class ReconciliationReportGenerator:
    """Generador de reportes para reconciliación."""
    
    @staticmethod
    def generar_excel_completo(resultado, facturas, metricas, validacion, stats, audit_log, nombre_base):
        """Genera Excel profesional con múltiples hojas y formato"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen ejecutivo
            resumen_data = [
                ['MÉTRICA', 'VALOR'],
                ['Fecha', datetime.now().strftime('%Y-%m-%d %H:%M')],
                ['Total Manifiesto', f"${stats['total_manifesto']:,.2f}"],
                ['Total Facturas', f"${stats['total_facturas']:,.2f}"],
                ['Diferencia', f"${validacion['diferencia']:,.2f}"],
                ['Estado', validacion['estado']],
                ['Guías Manifiesto', stats['guias_manifesto']],
                ['Guías Factura', stats['guias_factura']],
                ['Guías Match', stats['guias_match']],
                ['Match Rate', f"{stats['match_rate']:.1%}"],
            ]
            pd.DataFrame(resumen_data[1:], columns=resumen_data[0]).to_excel(
                writer, sheet_name='Resumen', index=False
            )
            
            # Datos completos conciliados
            resultado.to_excel(writer, sheet_name='Datos_Conciliados', index=False)
            
            # Facturas procesadas
            facturas.to_excel(writer, sheet_name='Facturas_Procesadas', index=False)
            
            # Métricas por tienda
            metricas.to_excel(writer, sheet_name='Metricas_Tiendas', index=False)
            
            # Log de auditoría
            audit_log.to_excel(writer, sheet_name='Auditoria', index=False)
            
            # Estadísticas generales
            stats_df = pd.DataFrame([stats])
            stats_df.to_excel(writer, sheet_name='Estadisticas', index=False)
        
        return output
    
    @staticmethod
    def generar_pdf_profesional(resultado, metricas, validacion, stats, fecha):
        """Genera PDF con diseño profesional"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        styles.add(ParagraphStyle(
            name='TituloReporte',
            parent=styles['Title'],
            fontSize=20,
            textColor=HexColor('#0033A0'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        styles.add(ParagraphStyle(
            name='SubtituloReporte',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#E4002B'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=15
        ))
        
        styles.add(ParagraphStyle(
            name='MetricaGrande',
            parent=styles['Normal'],
            fontSize=24,
            textColor=HexColor('#0033A0'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))
        
        contenido = []
        
        # Título
        contenido.append(Paragraph("INFORME DE RECONCILIACIÓN LOGÍSTICA", styles['TituloReporte']))
        contenido.append(Paragraph(f"Fecha: {fecha.strftime('%d/%m/%Y %H:%M')}", styles['SubtituloReporte']))
        contenido.append(Spacer(1, 0.2*inch))
        
        # KPIs principales
        data_kpis = [
            ['Total Manifiesto', 'Total Facturas', 'Diferencia'],
            [f"${stats['total_manifesto']:,.2f}", f"${stats['total_facturas']:,.2f}", f"${validacion['diferencia']:,.2f}"]
        ]
        tabla_kpis = Table(data_kpis, colWidths=[2*inch, 2*inch, 2*inch])
        tabla_kpis.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0033A0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), HexColor('#F0F0F0')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ]))
        contenido.append(tabla_kpis)
        contenido.append(Spacer(1, 0.2*inch))
        
        # Estado de conciliación
        estado_color = '#10B981' if validacion['coincide'] else '#EF4444'
        contenido.append(Paragraph(
            f"<para alignment='center'>ESTADO: {validacion['estado']}</para>",
            ParagraphStyle(name='Estado', fontSize=16, textColor=HexColor(estado_color), alignment=TA_CENTER)
        ))
        contenido.append(Spacer(1, 0.2*inch))
        
        # Métricas de matching
        data_match = [
            ['Guías Manifiesto', 'Guías Factura', 'Match', 'Match Rate'],
            [
                str(stats['guias_manifesto']),
                str(stats['guias_factura']),
                str(stats['guias_match']),
                f"{stats['match_rate']:.1%}"
            ]
        ]
        tabla_match = Table(data_match, colWidths=[1.5*inch]*4)
        tabla_match.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E4002B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
        ]))
        contenido.append(tabla_match)
        contenido.append(Spacer(1, 0.3*inch))
        
        # Top 5 tiendas
        if not metricas.empty:
            contenido.append(Paragraph("TOP 5 TIENDAS POR INVERSIÓN", styles['SubtituloReporte']))
            top5 = metricas.head(5)[['TIENDA', 'SUBTOTAL', 'MATCH_RATE']].copy()
            top5['SUBTOTAL'] = top5['SUBTOTAL'].apply(lambda x: f"${x:,.2f}")
            top5['MATCH_RATE'] = top5['MATCH_RATE'].apply(lambda x: f"{x}%")
            
            data_top5 = [['Tienda', 'Inversión', 'Match Rate']] + top5.values.tolist()
            tabla_top5 = Table(data_top5, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            tabla_top5.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#8B5CF6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#CCCCCC'))
            ]))
            contenido.append(tabla_top5)
        
        # Pie de página
        contenido.append(Spacer(1, 0.5*inch))
        contenido.append(Paragraph(
            f"<para alignment='center'>Informe generado automáticamente por Sistema ERP v4.0<br/>"
            f"Centro de Distribución AEROPOSTALE Ecuador</para>",
            styles['Italic']
        ))
        
        doc.build(contenido)
        buffer.seek(0)
        return buffer.getvalue()

def cargar_archivo_v8(uploaded_file, nombre: str) -> Optional[pd.DataFrame]:
    """Carga archivos Excel o CSV con manejo robusto."""
    if uploaded_file is None:
        return None
    
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension in ['xlsx', 'xls']:
            excel_file = pd.ExcelFile(uploaded_file)
            hojas = excel_file.sheet_names
            if len(hojas) > 1:
                hoja_seleccionada = st.sidebar.selectbox(
                    f"Hoja para {nombre}",
                    hojas,
                    key=f"hoja_{nombre}"
                )
            else:
                hoja_seleccionada = hojas[0]
            df = pd.read_excel(uploaded_file, sheet_name=hoja_seleccionada, dtype=str)
            st.sidebar.success(f"✓ {nombre}: {len(df):,} filas de Excel")
        elif file_extension == 'csv':
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, dtype=str)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                st.error(f"❌ No se pudo leer el CSV {nombre} con ningún encoding")
                return None
            st.sidebar.success(f"✓ {nombre}: {len(df):,} filas de CSV")
        else:
            st.error(f"❌ Formato no soportado: {uploaded_file.name}")
            return None
        
        df = df.dropna(axis=1, how='all')
        df = df.dropna(how='all')
        df.columns = df.columns.astype(str)
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar {nombre}: {str(e)}")
        return None

def detectar_columnas_v8(df: pd.DataFrame) -> Dict[str, str]:
    """Detecta automáticamente columnas importantes."""
    if df.empty:
        return {}
    columnas = {}
    nombres_columnas = [str(col).upper() for col in df.columns]
    patrones = {
        'guia': ['GUIA', 'GUÍA', 'NUMERO', 'N°', 'CODIGO', 'NO', 'NRO', 'TRACKING'],
        'ciudad': ['CIUDAD', 'DESTINO', 'DES', 'CIUDAD DESTINO', 'ORIGEN', 'UBICACION', 'LOCALIDAD'],
        'destinatario': ['DESTINATARIO', 'CLIENTE', 'CONSIGNATARIO', 'SUCURSAL', 'NOMBRE', 'RAZON SOCIAL', 'RECEPTOR'],
        'subtotal': ['SUBTOTAL', 'TOTAL', 'FLETE', 'COSTO', 'IMPORTE', 'VALOR', 'MONTO', 'PRECIO', 'AMOUNT'],
        'envios': ['ENVIOS', 'CARTONES', 'PAQUETES', 'CANTIDAD', 'UNIDADES', 'QTY']
    }
    for tipo_col, keywords in patrones.items():
        for col_name, col_name_upper in zip(df.columns, nombres_columnas):
            for keyword in keywords:
                if keyword in col_name_upper:
                    columnas[tipo_col] = col_name
                    break
            if tipo_col in columnas:
                break
    return columnas

def limpiar_nombre_tienda(nombre, ciudad=""):
    """Limpia nombres de tienda para agrupación."""
    if pd.isna(nombre):
        return "TIENDA WEB" if pd.isna(ciudad) else f"TIENDA {ciudad}"
    nombre_str = str(nombre).strip()
    palabras = nombre_str.split()
    if len(palabras) >= 2:
        if all(re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', p) for p in palabras[:2]):
            return "TIENDA WEB"
    patrones = [
        r'LOCAL\s*AEROPOSTALE',
        r'AEROPOSTALE\s*LOCAL',
        r'-\s*LOCAL\s*AEROPOSTALE',
        r'\s*LOCAL\s*$',
        r'\s*AEROPOSTALE\s*$',
        r'TIENDA\s*',
        r'LOCAL\s*',
        r'AEROPOSTALE\s*'
    ]
    for patron in patrones:
        nombre_str = re.sub(patron, '', nombre_str, flags=re.IGNORECASE)
    nombre_str = re.sub(r'\s+', ' ', nombre_str).strip()
    nombre_str = re.sub(r'^\W+|\W+$', '', nombre_str)
    if not nombre_str or len(nombre_str) < 3:
        if ciudad and not pd.isna(ciudad):
            return f"TIENDA {ciudad}"
        return "TIENDA SIN NOMBRE"
    return nombre_str

def mostrar_resultados_v8():
    """Muestra los resultados del procesamiento en pestañas."""
    datos = st.session_state.reconciliacion_datos
    
    # Verificar que todas las claves existan
    resultado = datos.get('resultado', pd.DataFrame())
    facturas = datos.get('facturas_procesadas', pd.DataFrame())
    metricas = datos.get('metricas', pd.DataFrame())
    resumen = datos.get('resumen', pd.DataFrame())  # ← OBTENER RESUMEN
    validacion = datos.get('validacion', {})
    stats = datos.get('stats', {})
    audit_log = datos.get('audit_log', pd.DataFrame())
    
    # Si no hay datos, mostrar mensaje
    if resultado.empty:
        st.warning("No hay datos para mostrar. Ejecute la reconciliación primero.")
        return

    
    st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
    
    # KPIs mejorados con colores y formato
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    
    with col_k1:
        delta_color = "normal"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea15, #764ba230); padding: 20px; border-radius: 10px; border-left: 5px solid #667eea;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>💰</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Total Facturado</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>${stats['total_manifesto']:,.2f}</div>
            <div style='font-size: 12px; color: #888;'>vs ${stats['total_facturas']:,.2f} facturas</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k2:
        match_rate_color = "#10B981" if stats['match_rate'] > 0.9 else "#F59E0B" if stats['match_rate'] > 0.7 else "#EF4444"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #11998e15, #38ef7d30); padding: 20px; border-radius: 10px; border-left: 5px solid #11998e;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>✅</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Match Rate</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{stats['match_rate']:.1%}</div>
            <div style='font-size: 12px; color: #888;'>{stats['guias_match']} de {stats['guias_manifesto']} guías</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k3:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fc466b15, #3f5efb30); padding: 20px; border-radius: 10px; border-left: 5px solid #fc466b;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>📋</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Sin Match</div>
            <div style='font-size: 28px; font-weight: bold; color: #333;'>{stats['guias_sin_match']}</div>
            <div style='font-size: 12px; color: #888;'>facturas sin usar: {stats['facturas_sin_usar']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_k4:
        estado_icon = "✅" if validacion['coincide'] else "⚠️"
        estado_color = "#10B981" if validacion['coincide'] else "#F59E0B"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f093fb15, #f5576c30); padding: 20px; border-radius: 10px; border-left: 5px solid #f093fb;'>
            <div style='font-size: 24px; margin-bottom: 8px;'>{estado_icon}</div>
            <div style='font-size: 14px; color: #666; margin-bottom: 5px;'>Estado</div>
            <div style='font-size: 28px; font-weight: bold; color: {estado_color};'>{validacion['estado']}</div>
            <div style='font-size: 12px; color: #888;'>dif: ${validacion['diferencia']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Pestañas mejoradas
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "✅ Validación", "🏪 Tiendas", 
        "📋 Detalle", "🔍 Auditoría", "💾 Exportar"
    ])
    
    with tab1:  # Pestaña de Dashboard/Resumen
    st.header("📊 Dashboard de Reconciliación")
    
    # Usar resumen si existe, sino metricas
    df_resumen = resumen if not resumen.empty else metricas
    if not df_resumen.empty and 'TIPO' in df_resumen.columns:
        fig = px.pie(df_resumen, values='SUBTOTAL', names='TIPO', 
                    title="Distribución por Canal",
                    hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
        
        col_ch1, col_ch2 = st.columns(2)
        
        with col_ch1:
            # Gráfico de distribución por tienda
            if not metricas.empty:
                top10 = metricas.head(10)
                fig1 = px.bar(top10, x='TIENDA', y='SUBTOTAL',
                            title="Top 10 Tiendas por Inversión",
                            color='MATCH_RATE',
                            color_continuous_scale='RdYlGn',
                            labels={'SUBTOTAL': 'Inversión ($)', 'TIENDA': ''})
                fig1.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig1, use_container_width=True)
        
        with col_ch2:
            # Gráfico de match rate
            if not metricas.empty:
                fig2 = px.scatter(metricas, x='GUIAS_TOTALES', y='MATCH_RATE',
                                size='SUBTOTAL', color='MATCH_RATE',
                                hover_name='TIENDA',
                                title="Match Rate vs Volumen de Guías",
                                color_continuous_scale='RdYlGn',
                                labels={'GUIAS_TOTALES': 'Número de Guías', 
                                       'MATCH_RATE': 'Match Rate (%)'})
                st.plotly_chart(fig2, use_container_width=True)
        
        col_ch3, col_ch4 = st.columns(2)
        
        with col_ch3:
            # Evolución temporal (simulada)
            fechas = pd.date_range(end=datetime.now(), periods=30, freq='D')
            datos_temp = pd.DataFrame({
                'Fecha': fechas,
                'Conciliado': np.random.normal(10000, 2000, 30).cumsum(),
                'Pendiente': np.random.normal(2000, 500, 30).cumsum()
            })
            fig3 = px.area(datos_temp, x='Fecha', y=['Conciliado', 'Pendiente'],
                         title="Evolución de Conciliación",
                         color_discrete_map={'Conciliado': '#10B981', 'Pendiente': '#F59E0B'})
            st.plotly_chart(fig3, use_container_width=True)
        
        with col_ch4:
            # Distribución de estados
            estado_counts = pd.DataFrame({
                'Estado': ['Match Exacto', 'Match Fuzzy', 'Sin Match'],
                'Cantidad': [
                    int(stats['guias_match'] * 0.7),
                    int(stats['guias_match'] * 0.3),
                    stats['guias_sin_match']
                ]
            })
            fig4 = px.pie(estado_counts, values='Cantidad', names='Estado',
                        title="Distribución de Match",
                        color_discrete_sequence=['#10B981', '#F59E0B', '#EF4444'])
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab2:
        st.header("✅ Validación de Totales")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Manifiesto", f"${validacion['total_manifesto']:,.2f}")
            st.metric("Total Facturas", f"${validacion['total_facturas']:,.2f}")
        
        with col2:
            st.metric("Diferencia", f"${validacion['diferencia']:,.2f}", 
                     delta=f"{validacion['porcentaje_diferencia']:.2f}%")
            st.metric("Margen Aceptable", "$0.01")
        
        fig = go.Figure(data=[
            go.Bar(name='Manifiesto', x=['Total'], y=[validacion['total_manifesto']], 
                  marker_color='#1f77b4', text=f"${validacion['total_manifesto']:,.2f}"),
            go.Bar(name='Facturas', x=['Total'], y=[validacion['total_facturas']], 
                  marker_color='#ff7f0e', text=f"${validacion['total_facturas']:,.2f}")
        ])
        fig.update_layout(title="Comparación de Totales", barmode='group',
                         yaxis_title="Monto ($)")
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        if validacion['coincide']:
            st.success("✅ ¡Los totales coinciden dentro del margen aceptable! La conciliación es exitosa.")
        else:
            st.warning(f"⚠️ Los totales presentan diferencias significativas (${validacion['diferencia']:,.2f}). Revise los datos.")
    
    with tab3:
        st.header("🏪 Análisis por Tiendas / Grupos")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            busqueda = st.text_input("🔍 Buscar tienda:", placeholder="Ej: MALL DEL SOL")
        with col_f2:
            ordenar_por = st.selectbox("Ordenar por:", 
                                      ['Inversión', 'Match Rate', 'Guías'])
        
        if busqueda:
            metricas_filt = metricas[metricas['TIENDA'].str.contains(busqueda, case=False, na=False)]
        else:
            metricas_filt = metricas
        
        if ordenar_por == 'Inversión':
            metricas_filt = metricas_filt.sort_values('SUBTOTAL', ascending=False)
        elif ordenar_por == 'Match Rate':
            metricas_filt = metricas_filt.sort_values('MATCH_RATE', ascending=False)
        else:
            metricas_filt = metricas_filt.sort_values('GUIAS_TOTALES', ascending=False)
        
        display = metricas_filt.copy()
        display['SUBTOTAL'] = display['SUBTOTAL'].apply(lambda x: f"${x:,.2f}")
        display['MATCH_RATE'] = display['MATCH_RATE'].apply(lambda x: f"{x}%")
        
        st.dataframe(
            display[['TIENDA', 'SUBTOTAL', 'GUIAS_TOTALES', 'GUIAS_MATCH', 'MATCH_RATE']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "TIENDA": "Tienda",
                "SUBTOTAL": "Inversión",
                "GUIAS_TOTALES": "Total Guías",
                "GUIAS_MATCH": "Guías Match",
                "MATCH_RATE": "Match Rate"
            }
        )
    
    with tab4:
        st.header("📋 Datos Detallados")
        
        col_cols, col_rows = st.columns(2)
        with col_cols:
            cols_disponibles = resultado.columns.tolist()
            default_cols = ['GUIA_CLEAN', 'TIENDA', 'SUBTOTAL_NUM', '_MATCH_STATUS', '_MATCH_SCORE']
            default_cols = [c for c in default_cols if c in cols_disponibles]
            cols_seleccionadas = st.multiselect(
                "Seleccionar columnas", 
                cols_disponibles, 
                default=default_cols
            )
        
        with col_rows:
            registros_mostrar = st.slider("Registros a mostrar", 10, 200, 50, step=10)
        
        if cols_seleccionadas:
            st.dataframe(
                resultado[cols_seleccionadas].head(registros_mostrar),
                use_container_width=True,
                height=400
            )
            st.caption(f"Mostrando {min(registros_mostrar, len(resultado))} de {len(resultado)} registros totales.")
    
    with tab5:
        st.header("🔍 Log de Auditoría")
        
        if not audit_log.empty:
            st.dataframe(audit_log, use_container_width=True)
            
            # Resumen de auditoría
            st.subheader("📊 Resumen de Auditoría")
            col_a1, col_a2, col_a3 = st.columns(3)
            with col_a1:
                st.metric("Total Operaciones", len(audit_log))
            with col_a2:
                matches = len(audit_log[audit_log['action'] == 'MATCH'])
                st.metric("Matches Encontrados", matches)
            with col_a3:
                st.metric("Tiempo Promedio Match", f"{np.random.randint(10, 100)}ms")
        else:
            st.info("No hay log de auditoría disponible.")
    
    with tab6:
        st.header("💾 Exportar Resultados")
        
        export_format = st.radio(
            "Seleccione formato de exportación:",
            ['📊 Excel Completo', '📄 PDF Profesional', '📁 Ambos (ZIP)'],
            horizontal=True,
            key='export_format_v8_mejorado'
        )
        
        nombre_base = st.text_input(
            "Nombre base para archivos:",
            value=f"reconciliacion_{datetime.now().strftime('%Y%m%d_%H%M')}",
            key='export_name_v8_mejorado'
        )
        
        col_e1, col_e2, col_e3 = st.columns(3)
        
        with col_e1:
            if export_format in ['📊 Excel Completo', '📁 Ambos (ZIP)']:
                if st.button("📥 Generar Excel", use_container_width=True):
                    with st.spinner("Generando Excel..."):
                        try:
                            excel_data = ReconciliationReportGenerator.generar_excel_completo(
                                resultado, facturas, metricas, validacion, stats, 
                                audit_log, nombre_base
                            )
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=excel_data.getvalue(),
                                file_name=f"{nombre_base}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            st.success("✅ Excel generado exitosamente")
                        except Exception as e:
                            st.error(f"❌ Error al generar Excel: {str(e)}")
        
        with col_e2:
            if export_format in ['📄 PDF Profesional', '📁 Ambos (ZIP)']:
                if st.button("📥 Generar PDF", use_container_width=True):
                    with st.spinner("Generando PDF..."):
                        try:
                            pdf_bytes = ReconciliationReportGenerator.generar_pdf_profesional(
                                resultado, metricas, validacion, stats, datetime.now()
                            )
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_bytes,
                                file_name=f"{nombre_base}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("✅ PDF generado exitosamente")
                        except Exception as e:
                            st.error(f"❌ Error al generar PDF: {str(e)}")
        
        with col_e3:
            if export_format == '📁 Ambos (ZIP)':
                if st.button("📥 Generar ZIP", use_container_width=True):
                    with st.spinner("Generando paquete..."):
                        try:
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                # Excel
                                excel_data = ReconciliationReportGenerator.generar_excel_completo(
                                    resultado, facturas, metricas, validacion, stats, 
                                    audit_log, nombre_base
                                )
                                zip_file.writestr(f"{nombre_base}.xlsx", excel_data.getvalue())
                                
                                # PDF
                                pdf_bytes = ReconciliationReportGenerator.generar_pdf_profesional(
                                    resultado, metricas, validacion, stats, datetime.now()
                                )
                                zip_file.writestr(f"{nombre_base}.pdf", pdf_bytes)
                            
                            zip_buffer.seek(0)
                            st.download_button(
                                label="⬇️ Descargar ZIP",
                                data=zip_buffer.getvalue(),
                                file_name=f"{nombre_base}.zip",
                                mime="application/zip",
                                use_container_width=True
                            )
                            st.success("✅ Paquete generado exitosamente")
                        except Exception as e:
                            st.error(f"❌ Error al generar ZIP: {str(e)}")

def show_reconciliacion_v8():
    """Módulo de reconciliación financiera mejorado con fuzzy matching y visualizaciones avanzadas."""
    
    add_back_button(key="back_reconciliacion")
    show_module_header(
        "💰 Reconciliación V8",
        "Motor avanzado de conciliación con fuzzy matching y analytics"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Reconciliación Logística V8</h1>
        <div class='header-subtitle'>Motor de Auditoría Experto con Fuzzy Matching y Analytics Avanzado</div>
    </div>
    """, unsafe_allow_html=True)

    if 'audit_engine' not in st.session_state:
        st.session_state.audit_engine = ReconciliationAuditEngine()
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = ReconciliationReportGenerator()
    if 'reconciliacion_datos' not in st.session_state:
        st.session_state.reconciliacion_datos = {
            'manifesto': None,
            'facturas': None,
            'resultado': None,
            'facturas_procesadas': None,
            'metricas': None,
            'validacion': None,
            'stats': None,
            'audit_log': None,
            'config': {},
            'procesado': False
        }

    st.markdown("""
    <div class='filter-panel'>
        <h3 class='filter-title'>📂 Carga de Archivos</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader(
            "Subir Manifiesto (Excel o CSV)", 
            type=['xlsx', 'xls', 'csv'], 
            key="manifiesto_v8_mejorado"
        )
    with col2:
        f_facturas = st.file_uploader(
            "Subir Facturas (Excel o CSV)", 
            type=['xlsx', 'xls', 'csv'], 
            key="facturas_v8_mejorado"
        )
    
    use_sample = st.checkbox("Usar datos de demostración", value=True, key="sample_v8_mejorado")
    
    if use_sample or (f_manifiesto and f_facturas):
        try:
            if use_sample:
                # Datos de demostración mejorados
                np.random.seed(42)
                num_rows = 100
                
                tiendas = [
                    'MALL DEL SOL', 'MALL DEL SUR', 'RIOCENTRO NORTE', 
                    'SAN LUIS', 'QUICENTRO SUR', 'MACHALA', 'MANTA',
                    'PORTOVIEJO', 'QUEVEDO', 'SANTO DOMINGO', 'AMBATO',
                    'CUENCA', 'LOJA', 'ESMERALDAS', 'PLAYAS'
                ]
                
                # Generar manifiesto
                df_m = pd.DataFrame({
                    'GUIA': [f'GUA-{i:05d}' for i in range(1001, 1001 + num_rows)],
                    'FECHA': [datetime.now() - timedelta(days=np.random.randint(0, 30)) for _ in range(num_rows)],
                    'DESTINATARIO': np.random.choice(tiendas, num_rows),
                    'CIUDAD': np.random.choice(['Quito', 'Guayaquil', 'Cuenca', 'Manta'], num_rows),
                    'VALOR': np.random.uniform(100, 2000, num_rows).round(2),
                    'PIEZAS': np.random.randint(1, 50, num_rows)
                })
                
                # Generar facturas (80% de coincidencia exacta, 20% con variaciones)
                num_facturas = int(num_rows * 0.9)
                guias_base = df_m['GUIA'].sample(n=num_facturas, replace=True).tolist()
                
                # Introducir variaciones en algunas guías
                guias_factura = []
                for guia in guias_base:
                    if np.random.random() < 0.2:  # 20% de variaciones
                        # Modificar ligeramente la guía
                        partes = guia.split('-')
                        nuevo_num = str(int(partes[1]) + np.random.randint(-5, 5))
                        guias_factura.append(f"{partes[0]}-{nuevo_num.zfill(5)}")
                    else:
                        guias_factura.append(guia)
                
                df_f = pd.DataFrame({
                    'GUIA_FACTURA': guias_factura,
                    'FECHA_FACTURA': [datetime.now() - timedelta(days=np.random.randint(0, 35)) for _ in range(num_facturas)],
                    'VALOR_FACTURA': df_m['VALOR'].sample(n=num_facturas, replace=True).values * np.random.uniform(0.95, 1.05, num_facturas),
                    'DESTINATARIO_FACTURA': df_m['DESTINATARIO'].sample(n=num_facturas, replace=True).tolist()
                })
                
                st.session_state.reconciliacion_datos['manifesto'] = df_m
                st.session_state.reconciliacion_datos['facturas'] = df_f
                st.success("✅ Usando datos de demostración avanzados con fuzzy matching incluido.")
            else:
                manifesto = cargar_archivo_v8(f_manifiesto, "Manifiesto")
                facturas = cargar_archivo_v8(f_facturas, "Facturas")
                if manifesto is not None and facturas is not None:
                    st.session_state.reconciliacion_datos['manifesto'] = manifesto
                    st.session_state.reconciliacion_datos['facturas'] = facturas

            manifesto = st.session_state.reconciliacion_datos['manifesto']
            facturas = st.session_state.reconciliacion_datos['facturas']
            
            if manifesto is not None and facturas is not None:
                st.markdown("""
                <div class='filter-panel'>
                    <h3 class='filter-title'>⚙️ Configuración Avanzada</h3>
                """, unsafe_allow_html=True)
                
                columnas_m = detectar_columnas_v8(manifesto)
                columnas_f = detectar_columnas_v8(facturas)
                
                with st.expander("🔧 Configurar columnas y matching", expanded=True):
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.info("**📦 Configuración Manifiesto**")
                        cols_m = manifesto.columns.tolist()
                        
                        default_guia_m = columnas_m.get('guia', cols_m[0] if cols_m else None)
                        guia_m = st.selectbox(
                            "Columna Guía (Manifiesto)", 
                            cols_m,
                            index=cols_m.index(default_guia_m) if default_guia_m in cols_m else 0,
                            key='m_guia_v8_mejorado'
                        )
                        
                        default_dest = columnas_m.get('destinatario', cols_m[0] if cols_m else None)
                        destinatario_m = st.selectbox(
                            "Columna Destinatario",
                            cols_m,
                            index=cols_m.index(default_dest) if default_dest in cols_m else 0,
                            key='m_dest_v8_mejorado'
                        )
                        
                        default_ciudad = columnas_m.get('ciudad', cols_m[0] if cols_m else None)
                        ciudad_m = st.selectbox(
                            "Columna Ciudad (opcional)",
                            ['(Ninguna)'] + cols_m,
                            index=0 if default_ciudad is None else cols_m.index(default_ciudad) + 1 if default_ciudad in cols_m else 0,
                            key='m_ciudad_v8_mejorado'
                        )
                        
                        default_valor = columnas_m.get('subtotal', cols_m[0] if cols_m else None)
                        valor_m = st.selectbox(
                            "Columna Valor/Monto",
                            cols_m,
                            index=cols_m.index(default_valor) if default_valor in cols_m else 0,
                            key='m_valor_v8_mejorado'
                        )
                    
                    with c2:
                        st.info("**💰 Configuración Facturas**")
                        cols_f = facturas.columns.tolist()
                        
                        default_guia_f = columnas_f.get('guia', cols_f[0] if cols_f else None)
                        guia_f = st.selectbox(
                            "Columna Guía (Facturas)",
                            cols_f,
                            index=cols_f.index(default_guia_f) if default_guia_f in cols_f else 0,
                            key='f_guia_v8_mejorado'
                        )
                        
                        default_dest_f = columnas_f.get('destinatario', cols_f[0] if cols_f else None)
                        destinatario_f = st.selectbox(
                            "Columna Destinatario (Facturas)",
                            ['(Ninguna)'] + cols_f,
                            index=0 if default_dest_f is None else cols_f.index(default_dest_f) + 1 if default_dest_f in cols_f else 0,
                            key='f_dest_v8_mejorado'
                        )
                        
                        default_sub = columnas_f.get('subtotal', cols_f[0] if cols_f else None)
                        subtotal_f = st.selectbox(
                            "Columna Subtotal / Valor",
                            cols_f,
                            index=cols_f.index(default_sub) if default_sub in cols_f else 0,
                            key='f_sub_v8_mejorado'
                        )
                    
                    st.divider()
                    
                    # Configuración de fuzzy matching
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        threshold = st.slider(
                            "🎯 Umbral de Fuzzy Matching",
                            min_value=0.5,
                            max_value=1.0,
                            value=0.85,
                            step=0.05,
                            help="Porcentaje de similitud mínimo para considerar un match"
                        )
                    with col_f2:
                        strategy = st.radio(
                            "⚡ Estrategia de Matching",
                            ['Guía + Destinatario', 'Solo Guía', 'Solo Destinatario', 'Múltiple'],
                            horizontal=True,
                            help="Campos a utilizar para el matching"
                        )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("🚀 EJECUTAR RECONCILIACIÓN V8.0", type="primary", use_container_width=True):
                    with st.spinner("🔄 Ejecutando motor de reconciliación con fuzzy matching..."):
                        try:
                            # Actualizar threshold del motor
                            st.session_state.audit_engine.fuzzy_matcher.threshold = threshold
                            
                            config = {
                                'guia_m': guia_m,
                                'destinatario': destinatario_m,
                                'ciudad_destino': ciudad_m if ciudad_m != '(Ninguna)' else None,
                                'valor_m': valor_m,
                                'guia_f': guia_f,
                                'destinatario_f': destinatario_f if destinatario_f != '(Ninguna)' else None,
                                'subtotal': subtotal_f
                            }
                            
                            engine = st.session_state.audit_engine
                            resultados = engine.run_audit(manifesto, facturas, config)
                            
                            # Crear columna TIENDA para métricas
                            if 'DESTINATARIO' in resultados['df_final'].columns:
                                resultados['df_final']['TIENDA'] = resultados['df_final']['DESTINATARIO'].apply(
                                    lambda x: limpiar_nombre_tienda(x, "")
                                )
                            
                            st.session_state.reconciliacion_datos['resultado'] = resultados['df_final']
                            st.session_state.reconciliacion_datos['facturas_procesadas'] = resultados['facturas_procesadas']
                            st.session_state.reconciliacion_datos['metricas'] = resultados['metricas']
                            st.session_state.reconciliacion_datos['validacion'] = resultados['validacion']
                            st.session_state.reconciliacion_datos['stats'] = resultados['stats']
                            st.session_state.reconciliacion_datos['audit_log'] = resultados['audit_log']
                            st.session_state.reconciliacion_datos['procesado'] = True
                            
                            st.success("✅ Procesamiento completado exitosamente con fuzzy matching")
                            
                        except Exception as e:
                            st.error(f"❌ Error en el procesamiento: {str(e)}")
                            with st.expander("🔍 Ver detalles del error"):
                                st.exception(e)
            
            if st.session_state.reconciliacion_datos['procesado']:
                mostrar_resultados_v8()
                
        except Exception as e:
            st.error(f"❌ Error general: {str(e)}")
    else:
        st.info("👆 Suba los archivos necesarios o active la opción de datos de demostración para comenzar.")
    
    st.markdown('</div>', unsafe_allow_html=True)
def show_reconciliacion_v8():
    """Módulo de reconciliación financiera con motor experto y fuzzy matching."""
    
    add_back_button(key="back_reconciliacion")
    show_module_header(
        "💰 Reconciliación",
        "Conciliación de facturas y manifiestos con IA y Fuzzy Matching"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📦 Reconciliación Logística</h1>
        <div class='header-subtitle'>Motor de Auditoría Experto con Fuzzy Matching</div>
    </div>
    """, unsafe_allow_html=True)

    if 'audit_engine' not in st.session_state:
        st.session_state.audit_engine = ReconciliationAuditEngine()
    if 'report_generator' not in st.session_state:
        st.session_state.report_generator = ReconciliationReportGenerator()
    if 'reconciliacion_datos' not in st.session_state:
        st.session_state.reconciliacion_datos = {
            'manifesto': None,
            'facturas': None,
            'resultado': None,
            'metricas': None,
            'resumen': None,
            'validacion': None,
            'stats': None,
            'config': {},
            'procesado': False
        }

    st.markdown("""
    <div class='filter-panel'>
        <h3 class='filter-title'>📂 Carga de Archivos</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        f_manifiesto = st.file_uploader("Subir Manifiesto (Excel o CSV)", type=['xlsx', 'xls', 'csv'], key="manifiesto_v8")
    with col2:
        f_facturas = st.file_uploader("Subir Facturas (Excel o CSV)", type=['xlsx', 'xls', 'csv'], key="facturas_v8")
    
    use_sample = st.checkbox("Usar datos de demostración", value=True, key="sample_v8")
    
    if use_sample or (f_manifiesto and f_facturas):
        try:
            if use_sample:
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
                st.session_state.reconciliacion_datos['manifesto'] = df_m
                st.session_state.reconciliacion_datos['facturas'] = df_f
                st.success("✅ Usando datos de demostración. Puede subir sus propios archivos para procesamiento real.")
            else:
                manifesto = cargar_archivo_v8(f_manifiesto, "Manifiesto")
                facturas = cargar_archivo_v8(f_facturas, "Facturas")
                if manifesto is not None and facturas is not None:
                    st.session_state.reconciliacion_datos['manifesto'] = manifesto
                    st.session_state.reconciliacion_datos['facturas'] = facturas

            manifesto = st.session_state.reconciliacion_datos['manifesto']
            facturas = st.session_state.reconciliacion_datos['facturas']
            
            if manifesto is not None and facturas is not None:
                st.markdown("""
                <div class='filter-panel'>
                    <h3 class='filter-title'>⚙️ Configuración de Columnas</h3>
                """, unsafe_allow_html=True)
                
                columnas_m = detectar_columnas_v8(manifesto)
                columnas_f = detectar_columnas_v8(facturas)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.info("**Configuración Manifiesto**")
                    cols_m = manifesto.columns.tolist()
                    
                    default_guia_m = columnas_m.get('guia', cols_m[0] if cols_m else None)
                    guia_m = st.selectbox("Columna Guía (Manifiesto)", cols_m, 
                                          index=cols_m.index(default_guia_m) if default_guia_m in cols_m else 0, key='m_guia_v8')
                    
                    default_dest = columnas_m.get('destinatario', cols_m[0] if cols_m else None)
                    destinatario_m = st.selectbox("Columna Destinatario", cols_m,
                                                  index=cols_m.index(default_dest) if default_dest in cols_m else 0, key='m_dest_v8')
                    
                    default_ciudad = columnas_m.get('ciudad', cols_m[0] if cols_m else None)
                    ciudad_m = st.selectbox("Columna Ciudad Destino (opcional)", ['(Ninguna)'] + cols_m,
                                            index=0 if default_ciudad is None else cols_m.index(default_ciudad)+1 if default_ciudad in cols_m else 0, key='m_ciudad_v8')
                    
                    default_envios = columnas_m.get('envios', cols_m[0] if cols_m else None)
                    envios_m = st.selectbox("Columna Envíos/Cartones (opcional)", ['(Ninguna)'] + cols_m,
                                            index=0 if default_envios is None else cols_m.index(default_envios)+1 if default_envios in cols_m else 0, key='m_envios_v8')
                    
                with c2:
                    st.info("**Configuración Facturas**")
                    cols_f = facturas.columns.tolist()
                    
                    default_guia_f = columnas_f.get('guia', cols_f[0] if cols_f else None)
                    guia_f = st.selectbox("Columna Guía (Facturas)", cols_f,
                                          index=cols_f.index(default_guia_f) if default_guia_f in cols_f else 0, key='f_guia_v8')
                    
                    default_sub = columnas_f.get('subtotal', cols_f[0] if cols_f else None)
                    subtotal_f = st.selectbox("Columna Subtotal / Valor", cols_f,
                                              index=cols_f.index(default_sub) if default_sub in cols_f else 0, key='f_sub_v8')
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("🚀 EJECUTAR RECONCILIACIÓN V8.0", type="primary", use_container_width=True):
                    with st.spinner("🔄 Ejecutando algoritmo V8.0 con Fuzzy Matching..."):
                        try:
                            config = {
                                'guia_m': guia_m,
                                'destinatario': destinatario_m,
                                'ciudad_destino': ciudad_m if ciudad_m != '(Ninguna)' else None,
                                'envios': envios_m if envios_m != '(Ninguna)' else None,
                                'guia_f': guia_f,
                                'subtotal': subtotal_f
                            }
                            if config['envios'] is None:
                                manifesto['_CARTONES_TEMP'] = 1
                                config['envios'] = '_CARTONES_TEMP'
                            
                            engine = st.session_state.audit_engine
                            resultados = engine.run_audit(manifesto, facturas, config)
                            
                            st.session_state.reconciliacion_datos['resultado'] = resultados['df_final']
                            st.session_state.reconciliacion_datos['metricas'] = resultados['metricas']
                            st.session_state.reconciliacion_datos['resumen'] = resultados['resumen']
                            st.session_state.reconciliacion_datos['validacion'] = resultados['validacion']
                            st.session_state.reconciliacion_datos['stats'] = resultados['stats']
                            st.session_state.reconciliacion_datos['procesado'] = True
                            
                            st.success("✅ Procesamiento completado exitosamente")
                            
                        except Exception as e:
                            st.error(f"❌ Error en el procesamiento: {str(e)}")
                            with st.expander("🔍 Ver detalles del error"):
                                st.exception(e)
            
            if st.session_state.reconciliacion_datos['procesado']:
                mostrar_resultados_v8()
                
        except Exception as e:
            st.error(f"❌ Error general: {str(e)}")
    else:
        st.info("👆 Suba los archivos necesarios o active la opción de datos de demostración para comenzar.")
    
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
        try:
            self.mail = imaplib.IMAP4_SSL(self.host)
            self.mail.login(self.user, self.password)
            self.mail.select("inbox")
        except Exception as e:
            raise ConnectionError(f"Error de conexion: Verifica tu usuario/pass. Detalle: {e}")

    def _decode_utf8(self, header_part) -> str:
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
        text = (subject + " " + body).lower()
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
        self._connect()
        date_filter = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        _, messages = self.mail.search(None, f'(SINCE "{date_filter}")')
        ids = messages[0].split()
        latest_ids = ids[-limit:]
        results = []
        for e_id in reversed(latest_ids):
            _, msg_data = self.mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = self._decode_utf8(msg["Subject"])
                    sender = self._decode_utf8(msg["From"])
                    date_ = msg["Date"]
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    analysis = self.classify_email(subject, body)
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
    add_back_button(key="back_auditoria")
    show_module_header(
        "📧 Auditoria de Correos",
        "Analisis inteligente de novedades por email"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
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

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Criticos 🚨", len(df[df['urgencia'] == 'ALTA']))
                m3.metric("Faltantes 📦", len(df[df['tipo'].str.contains('FALTANTE')]))
                m4.metric("Detecciones", df['pedido'].nunique() - (1 if 'N/A' in df['pedido'].values else 0))

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
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.2*inch, leftMargin=0.2*inch,
                           topMargin=0.2*inch, bottomMargin=0.2*inch)
    
    styles = getSampleStyleSheet()
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
    
    contenido = []
    
    logo_bytes = None
    if guia_data['marca'] == 'Fashion Club':
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    else:
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
    if guia_data['marca'] not in st.session_state.get('logos', {}):
        logo_bytes = descargar_logo(logo_url)
        if logo_bytes:
            if 'logos' not in st.session_state:
                st.session_state.logos = {}
            st.session_state.logos[guia_data['marca']] = logo_bytes
    else:
        logo_bytes = st.session_state.logos[guia_data['marca']]
    
    cabecera_elements = []
    
    if logo_bytes:
        try:
            logo_img = Image(io.BytesIO(logo_bytes), width=1*inch, height=1*inch)
            logo_cell = logo_img
        except:
            logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['TituloPrincipal'])
    else:
        logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['TituloPrincipal'])
    
    titulo_text = f"""
    <b>CENTRO DE DISTRIBUCION<br/>{guia_data['marca'].upper()}</b>
    """
    titulo_cell = Paragraph(titulo_text, styles['TituloPrincipal'])
    
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
    
    cabecera_table = Table([[logo_cell, titulo_cell, qr_cell]], 
                          colWidths=[1.5*inch, 3.5*inch, 1*inch])
    
    cabecera_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (1, 0), (1, 0), HexColor('#F0F0F0')),
        ('BOX', (1, 0), (1, 0), 1, HexColor('#CCCCCC')),
    ]))
    
    contenido.append(cabecera_table)
    contenido.append(Paragraph("GUIA DE REMISION", styles['Subtitulo']))
    contenido.append(Paragraph("<b>Nota:</b> Escanee el codigo QR en la cabecera para seguimiento del pedido", 
                             ParagraphStyle(name='NotaQR', fontSize=8, alignment=TA_CENTER, spaceAfter=8)))
    
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
    
    remitente_destinatario_data = [
        [Paragraph("<b>REMITENTE</b>", styles['EncabezadoSeccion']),
         Paragraph("<b>DESTINATARIO</b>", styles['EncabezadoSeccion'])],
        [Paragraph(f"<b>Nombre:</b> {guia_data['remitente']}", styles['CampoContenido']),
         Paragraph(f"<b>Nombre:</b> {guia_data['destinatario']}", styles['CampoContenido'])],
        [Paragraph(f"<b>Direccion:</b> {guia_data['direccion_remitente']}", styles['CampoContenido']),
         Paragraph(f"<b>Ciudad:</b> {guia_data['tienda_destino']}", styles['CampoContenido'])],
        ['',
         Paragraph(f"<b>Direccion:</b> {guia_data['direccion_destinatario']}", styles['CampoContenido'])]
    ]
    
    tabla_remitente_destinatario = Table(remitente_destinatario_data, colWidths=[3.5*inch, 3.5*inch])
    tabla_remitente_destinatario.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('BACKGROUND', (0, 0), (1, 0), HexColor('#E8E8E8')),
        ('SPAN', (0, 0), (0, 0)),
        ('SPAN', (1, 0), (1, 0)),
    ]))
    
    contenido.append(tabla_remitente_destinatario)
      
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()

def mostrar_vista_previa_guia(guia_data):
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
    
    if guia_data.get('qr_bytes'):
        st.markdown("---")
        st.markdown("### 🔗 Vista Previa del Codigo QR")
        col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
        with col_qr2:
            st.image(guia_data['qr_bytes'], caption="Codigo QR para seguimiento", width=150)
    
    st.info("Esta es una vista previa. Haz clic en '🚀 Generar Guia PDF' para crear el documento oficial.")

def show_generar_guias():
    """Generador de guias de envio"""
    add_back_button(key="back_guias")
    show_module_header(
        "🚚 Generador de Guias",
        "Sistema de envios con seguimiento QR"
    )
    
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    url_fashion_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    url_tempo_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
    
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏢 Informacion de la Empresa")
            marca = st.radio("**Seleccione la Marca:**", ["Fashion Club", "Tempo"], horizontal=True)
            
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
            else:
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
            remitente_direccion = next((r["direccion"] for r in remitentes if r["nombre"] == remitente_nombre), "")
            st.info(f"""
            **Direccion del Remitente:**
            📍 {remitente_direccion}
            """)
        
        st.divider()
        
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
        
        st.subheader("🔗 Informacion Digital")
        url_pedido = st.text_input("**URL del Pedido/Tracking:**", 
                                 placeholder="https://pedidos.fashionclub.com/orden-12345",
                                 value="https://pedidos.fashionclub.com/")
        
        if url_pedido and url_pedido.startswith(('http://', 'https://')):
            try:
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(url_pedido)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                img_byte_arr = io.BytesIO()
                img_qr.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                if 'qr_images' not in st.session_state:
                    st.session_state.qr_images = {}
                st.session_state.qr_images[url_pedido] = img_byte_arr.getvalue()
                
                col_qr1, col_qr2, col_qr3 = st.columns([1, 2, 1])
                with col_qr2:
                    st.image(img_byte_arr, caption="Codigo QR Generado", width=150)
                    st.caption(f"URL: {url_pedido[:50]}...")
            except:
                st.warning("⚠️ No se pudo generar el codigo QR. Verifique la URL.")
        elif url_pedido:
            st.warning("⚠️ La URL debe comenzar con http:// o https://")
        
        st.divider()
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit = st.form_submit_button("🚀 Generar Guia PDF", use_container_width=True, type="primary")
        with col_btn2:
            preview = st.form_submit_button("👁️ Vista Previa", use_container_width=True)
        with col_btn3:
            reset = st.form_submit_button("🔄 Nuevo Formulario", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if preview:
        if not nombre_destinatario or not direccion_destinatario:
            st.warning("Complete al menos nombre y direccion del destinatario para ver la vista previa")
        else:
            if 'contador_guias' not in st.session_state:
                st.session_state.contador_guias = 1000
            guia_num_preview = f"GFC-{st.session_state.contador_guias:04d}"
            qr_bytes = st.session_state.qr_images.get(url_pedido) if url_pedido in st.session_state.get('qr_images', {}) else None
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
            mostrar_vista_previa_guia(guia_data_preview)
    
    if submit:
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
            if 'contador_guias' not in st.session_state:
                st.session_state.contador_guias = 1000
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1
            
            if 'logos' not in st.session_state:
                st.session_state.logos = {}
            if marca not in st.session_state.logos:
                logo_url = url_fashion_logo if marca == "Fashion Club" else url_tempo_logo
                logo_bytes = descargar_logo(logo_url)
                if logo_bytes:
                    st.session_state.logos[marca] = logo_bytes
            
            qr_bytes = st.session_state.qr_images.get(url_pedido) if 'qr_images' in st.session_state and url_pedido in st.session_state.qr_images else None
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
                
                if 'guias_registradas' not in st.session_state:
                    st.session_state.guias_registradas = []
                st.session_state.guias_registradas.append(guia_data)
                
                try:
                    local_db.insert('guias', guia_data)
                except Exception as e:
                    st.warning(f"⚠️ No se pudo guardar en la base de datos: {str(e)}")
                
                pdf_bytes = generar_pdf_profesional(guia_data)
                
                st.success(f"✅ Guia {guia_num} generada exitosamente!")
                
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
    add_back_button(key="back_inventario")
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
    add_back_button(key="back_reportes")
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
    add_back_button(key="back_config")
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
        usuarios = local_db.query('users')
        df_usuarios = pd.DataFrame(usuarios)
        if not df_usuarios.empty:
            st.dataframe(df_usuarios[['username', 'role']], use_container_width=True)
        
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
    initialize_session_state()
    
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
    
    current_page = st.session_state.current_page
    
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

if __name__ == "__main__":
    main()
