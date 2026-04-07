import streamlit as st
import pandas as pd 
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import hashlib
import re
import threading
import asyncio
import unicodedata
import io
import json
import qrcode
import requests
import imaplib
import email
from io import BytesIO
from email.header import decode_header
from typing import Dict, List, Optional, Any, Union
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import HexColor
from openpyxl import Workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
import tempfile
from reportlab.lib import colors

# ==============================================================================
# FUNCIONES AUXILIARES FALTANTES
# ==============================================================================

def hash_password(password: str) -> str:
    """Genera hash SHA256 de una contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def extraer_entero(valor):
    """Convierte a entero extrayendo la parte numérica si es necesario"""
    if pd.isna(valor):
        return 0
    try:
        if isinstance(valor, (int, float)):
            return int(valor)
        # Si es string, extraer números
        valor_str = str(valor).strip()
        numeros = re.findall(r'\d+', valor_str)
        if numeros:
            return int(numeros[0])
        return 0
    except:
        return 0

def to_excel(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a bytes de Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output.getvalue()

# ==============================================================================
# CONFIGURACION DE PAGINA
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# DATOS DE TIENDAS
# ==============================================================================
TIENDAS_DATA = [
    {"Nombre de Tienda": "Aeropostale - (Cuenca) Mall del Rio", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "CUENCA", "Contacto": "Marco Eras", "Dirección": "Av. Felipe II y Autopista Sur - CC Mall del Rio", "Teléfono": "994570933"},
    {"Nombre de Tienda": "Aeropostale - 6 de Diciembre", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "Micaela Yépez", "Dirección": "Av. 6 de Diciembre y Thomas de Berlanga CC Riocentro UIO", "Teléfono": "987883889"},
    {"Nombre de Tienda": "Aeropostale - Paseo Ambato", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "AMBATO", "Contacto": "Franco Torres", "Dirección": "Manuelita Saenz y Pio Baroja, cerca al parque de las Flores CC Paseo Shopping", "Teléfono": "984951515"},
    {"Nombre de Tienda": "Aeropostale - Ambato", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "AMBATO", "Contacto": "Gabriela Urrutia", "Dirección": "Av. Atahualpa y Victor Hugo CC Mall de Los Andes", "Teléfono": "967239488"},
    {"Nombre de Tienda": "Aeropostale - Babahoyo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "BABAHOYO", "Contacto": "Yomaira Sellan", "Dirección": "Av.Enrique Ponce Luque CC Paseo Shopping Babahoyo", "Teléfono": "981641355"},
    {"Nombre de Tienda": "Aeropostale - bomboli", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "SANTO DOMINGO", "Contacto": "Josselyn Navarrete", "Dirección": "Via Chone Diagonal a la Universidad Catolica CC Bpmbolí Shopping", "Teléfono": "933906346"},
    {"Nombre de Tienda": "Aeropostale - Bahía de Caráquez", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "BAHIA DE CARAQUEZ", "Contacto": "Nayely Orejuela", "Dirección": "Av. 3 de Noviembre - CC Paseo Shoping Bahía de caraquez", "Teléfono": "981131760"},
    {"Nombre de Tienda": "Aeropostale - Carapungo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "María José Benalcazar", "Dirección": "Av. Simón Bolívar, Panamericana Norte y calle, Capitán Giovanni Calles - CC", "Teléfono": "997242323"},
    {"Nombre de Tienda": "Aeropostale - CCI", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "Carolina Procel", "Dirección": "Av. Amazonas y Naciones Unidas - CC Iñaquito", "Teléfono": "984048928"},
    {"Nombre de Tienda": "Aeropostale - Ceibos", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Angie Delgado", "Dirección": "Av. Del Bombero y San Eduardo - Riocentro Ceibos", "Teléfono": "999085369"},
    {"Nombre de Tienda": "Aeropostale - Centro Histórico", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "CUENCA", "Contacto": "Renata Sacari", "Dirección": "Av. Simón Bolívar y PadreA guirre Centro Histórico diagonal a a la chocolateri", "Teléfono": "980874018"},
    {"Nombre de Tienda": "Aeropostale - City Mall", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Jordan Guale", "Dirección": "Av. felipe Pezo y Av. Benjamín Carrión CC City Mall", "Teléfono": "962880194"},
    {"Nombre de Tienda": "Aeropostale - Condado Shopping", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "Mateo Recalde", "Dirección": "Av. Mariscal Sucre entre Av. La Prensa Y Jhon F. Kennedy - CC Condado Sh", "Teléfono": "993736447"},
    {"Nombre de Tienda": "Aeropostale - Daule", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "DAULE", "Contacto": "Alisson Ramirez", "Dirección": "Av. Vicente Piedrahita y Coronel Calletano Cestaris- Paseo Shoping Daule", "Teléfono": "978881886"},
    {"Nombre de Tienda": "Aeropostale - Dorado", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Oscar Alvarado", "Dirección": "Av. León Febres Cordero Ribadeneyra - Rio Centro Dorado", "Teléfono": "959098012"},
    {"Nombre de Tienda": "Aeropostale - Durán", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "DURÁN", "Contacto": "Yaritza Córdova", "Dirección": "Av. Boliche Panamericana - Paseo Shoping Durán Junto al Terminal", "Teléfono": "996359344"},
    {"Nombre de Tienda": "Aeropostale - el Coca", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "EL COCA", "Contacto": "Adriana Zurita", "Dirección": "Av. 9 de Octubre y Rio Curaray - Junto a Super Akí el Coca", "Teléfono": "989137928"},
    {"Nombre de Tienda": "Aeropostale - La Plaza", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "IBARRA", "Contacto": "Andrea Andrango", "Dirección": "Av. Mariano Acosta entre Inacio Canelos y Victor Gómez Jurado - CC La Plaz", "Teléfono": "978765143"},
    {"Nombre de Tienda": "Aeropostale - Lago Agrio", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "LAGO AGRIO", "Contacto": "Angie Maldonado", "Dirección": "Av. Quito y Pasaje Brazil - Junto a Super Akí Lago Agrio", "Teléfono": "989893309"},
    {"Nombre de Tienda": "Aeropostale - Machala", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "MACHALA", "Contacto": "Iris carpio", "Dirección": "Av. Paquisha y Vía Machala km. 2 1/2 - CC Paseo Shoping Machala", "Teléfono": "997260162"},
    {"Nombre de Tienda": "Aeropostale - Mall del Pacífico", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "MANTA", "Contacto": "Karina Figueroa", "Dirección": "Av. Malecón y Calle 23 - CC Mall del Pacifico", "Teléfono": "990614279"},
    {"Nombre de Tienda": "Aeropostale - Mall del Rio (Gye)", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Danna Peralta", "Dirección": "Av. Francisco de Orellana y Av. Guillermo Pareja - CC Mall del Rio", "Teléfono": "995609664"},
    {"Nombre de Tienda": "Aeropostale - Mall del Sol", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Kiara Dávalos", "Dirección": "Av. Juan tanca marengo, Carlos Aurelio Rubira Infante 14 NE y Pasaje 1A - C", "Teléfono": "992753549"},
    {"Nombre de Tienda": "Aeropostale - Mall del Sur", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Judith Asunción", "Dirección": "AV 25 de Julio junto al Hospital de IESS - CC Mall del Sur", "Teléfono": "999669429"},
    {"Nombre de Tienda": "Aeropostale - Manta", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "MANTA", "Contacto": "Yenny Alvia", "Dirección": "Av. 4 de noviembre Paseo Shoping Manta", "Teléfono": "995168732"},
    {"Nombre de Tienda": "Aeropostale - Milagro", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "MILAGRO", "Contacto": "Lady Silva", "Dirección": "Av. 12 de Octubre, entre presidente Jerónimo Carrión y presidente Javier Espi", "Teléfono": "985415948"},
    {"Nombre de Tienda": "Aeropostale - Peso Shopping Riobama", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "RIOBAMBA", "Contacto": "María Fernanda Ibarra", "Dirección": "Av. Antonio José de Sucre frente a la Universidad UNACH CC Paseo Shoppin", "Teléfono": "993438844"},
    {"Nombre de Tienda": "Aeropostale - Multiplaza Riobamba", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "RIOBAMBA", "Contacto": "Jennifer Jimenez", "Dirección": "Avenida Lizarzaburu y Agustin Torres - CC Multiplaza Riobamba", "Teléfono": "962636619"},
    {"Nombre de Tienda": "Aeropostale - Pasaje", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PASAJE", "Contacto": "Jhonny Cun", "Dirección": "Av. Quito entrada a Pasaje y Redondel del León - Junto a Super Aki Pasaje", "Teléfono": "969586186"},
    {"Nombre de Tienda": "Aeropostale - Paseo Ambato", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "AMBATO", "Contacto": "Franco Torres", "Dirección": "Av.Pio Baroja Nesi y Av. Manuelita Saéns Paseo Shoping Ambato", "Teléfono": "984951515"},
    {"Nombre de Tienda": "Aeropostale - Pedernales", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PEDERNALES", "Contacto": "Mónica Muñoz", "Dirección": "Av. García Moreno y Calle Pedernales - Junto a Aki Pedernales", "Teléfono": "989113061"},
    {"Nombre de Tienda": "Aeropostale - Península", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PENINSULA", "Contacto": "Kenny Bohorquez", "Dirección": "Av. Carlos Espinosa y Av. Central CC Paseo Shopping La Peninsula", "Teléfono": "997432684"},
    {"Nombre de Tienda": "Aeropostale - Playas", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PLAYAS", "Contacto": "Steven Ortiz", "Dirección": "Av. General Villamil - Paseo Shoping Playas", "Teléfono": "991871477"},
    {"Nombre de Tienda": "Aeropostale - Portoviejo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PORTOVIEJO", "Contacto": "Gissel Loor", "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo", "Teléfono": "963683962"},
    {"Nombre de Tienda": "Aeropostale - Rio Centro Norte", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Doris Zambrano", "Dirección": "Av. Francisco de Orellana y Urb. Alcance CC Riocentro Norte", "Teléfono": "969705137"},
    {"Nombre de Tienda": "Aeropostale - San Luis", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "Karina Proaño", "Dirección": "Av. General Rumiñahui y Av. San Luis - CC San Luis Shoping", "Teléfono": "991879974"},
    {"Nombre de Tienda": "Aeropostale - Santo Domingo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "SANTO DOMINGO", "Contacto": "Mateo Fruto", "Dirección": "Av. Abraham Calazacón y Av. Quito - Paseo Shoping Santo Domingo", "Teléfono": "967593039"},
    {"Nombre de Tienda": "Aeropostale - Cayambe", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "CAYAMBE", "Contacto": "Celeste Contreras", "Dirección": "Panamericana norte y camino del sol CC Altos de Cayambe", "Teléfono": "995414136"},
    {"Nombre de Tienda": "Aeropostale Quevedo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUEVEDO", "Contacto": "Dayana León", "Dirección": "Av. Quito, frente a la policia Nacional CC Paseo Shopping Quevedo", "Teléfono": "981398074"},
    {"Nombre de Tienda": "Price Club - Portoviejo", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "PORTOVIEJO", "Contacto": "Dayana Merchan", "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo", "Teléfono": "959877997"},
    {"Nombre de Tienda": "Price Club - Machala", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "MACHALA", "Contacto": "Yuleysi Delgado", "Dirección": "AV. 25 de Junio CC Oro Plaza", "Teléfono": "988087085"},
    {"Nombre de Tienda": "Price Club - Guayaquil", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "GUAYAQUIL", "Contacto": "Angie Delgado", "Dirección": "Pedro Carbo S/N y Luque junto a almacenes Estuardo Sánchez", "Teléfono": "999085369"},
    {"Nombre de Tienda": "Price Club - Ibarra", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "IBARRA", "Contacto": "Silvia Urcuango", "Dirección": "Av. Victor Gómez Jurado y Rodrigo Miño junto a la cancha La Bombonera", "Teléfono": "982649058"},
]

# ==============================================================================
# SISTEMA DE AUTENTICACION
# ==============================================================================
USERS_DB = {
    "admin": {
        "password": hash_password("wilo3161"),
        "role": "Administrador",
        "name": "Administrador General",
        "email": "admin@aeropostale.com",
        "avatar": "👑"
    },
    "logistica": {
        "password": hash_password("log123"),
        "role": "Logística",
        "name": "Coordinador Logístico",
        "email": "logistica@aeropostale.com",
        "avatar": "🚚"
    },
    "ventas": {
        "password": hash_password("ven123"),
        "role": "Ventas",
        "name": "Ejecutivo de Ventas",
        "email": "ventas@aeropostale.com",
        "avatar": "💼"
    },
    "bodega": {
        "password": hash_password("bod123"),
        "role": "Bodega",
        "name": "Supervisor de Bodega",
        "email": "bodega@aeropostale.com",
        "avatar": "📦"
    }
}

def check_password():
    """Devuelve True si el usuario está autenticado"""
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        return True
    
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 80px auto;
        padding: 40px 30px;
        background: rgba(30, 41, 59, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        text-align: center;
    }
    .login-brand {
        margin-bottom: 30px;
    }
    .login-brand .main {
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: 4px;
        background: linear-gradient(45deg, #60A5FA, #8B5CF6, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .login-brand .sub {
        font-size: 1rem;
        color: #CBD5E1;
        letter-spacing: 2px;
        margin-bottom: 15px;
    }
    .login-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
        margin-bottom: 25px;
        border-bottom: 2px solid #60A5FA;
        display: inline-block;
        padding-bottom: 5px;
    }
    .login-version {
        margin-top: 20px;
        font-size: 0.8rem;
        color: #64748B;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-brand">
            <div class="main">AEROPOSTAL</div>
            <div class="sub">ERP CONTROL TOTAL</div>
        </div>
        <div class="login-title">INICIAR SESIÓN</div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario", key="login_user", label_visibility="collapsed")
        password = st.text_input("Contraseña", placeholder="Ingresa tu contraseña", type="password", key="login_pass", label_visibility="collapsed")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            remember = st.checkbox("Recordarme", key="remember_me")
        with col2:
            pass
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            login_btn = st.button("Ingresar", use_container_width=True, type="primary")
        
        st.markdown('<div class="login-version">v2.0.0</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if login_btn:
            if username in USERS_DB:
                stored_hash = USERS_DB[username]["password"]
                input_hash = hash_password(password)
                if stored_hash == input_hash:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = USERS_DB[username]["role"]
                    st.session_state.user_name = USERS_DB[username]["name"]
                    if remember:
                        st.session_state.remember_username = username
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.error("❌ Usuario no existe")
    return False

def logout():
    for key in ['authenticated', 'username', 'role', 'user_name', 'remember_username']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def show_header():
    """Barra superior con Inicio, info usuario y Salir"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 Inicio", use_container_width=True):
            st.session_state.current_page = "Inicio"
            st.rerun()
    with col2:
        st.markdown(
            f"<div style='text-align: center; color: #CBD5E1; font-size: 0.9rem;'>"
            f"<strong>{st.session_state.user_name}</strong> | {st.session_state.role} | "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("🚪 Salir", use_container_width=True):
            logout()
    st.markdown("---")

# ==============================================================================
# ESTILOS CSS
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

.gallery-container {
    padding: 40px 5% 20px 5%;
    text-align: center;
    max-width: 1400px;
    margin: 0 auto;
    position: relative;
}

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
}

.module-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 25px 20px;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    cursor: pointer;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}
.module-card:hover {
    transform: translateY(-10px) scale(1.03);
    border-color: rgba(96, 165, 250, 0.3);
}
.card-icon {
    font-size: 3.5rem;
    margin-bottom: 20px;
}
.card-title {
    color: white;
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.card-description {
    color: #CBD5E1;
    font-size: 0.9rem;
    opacity: 0.8;
}

.module-header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 2rem;
    border-radius: 24px;
    margin: 20px 0;
    border: 1px solid rgba(255, 255, 255, 0.1);
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
    font-size: 2rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.5rem;
}
.header-subtitle {
    font-size: 1rem;
    color: #CBD5E1;
}

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
}
.card-blue { border-left: 4px solid #60A5FA; }
.card-green { border-left: 4px solid #10B981; }
.card-red { border-left: 4px solid #EF4444; }
.card-purple { border-left: 4px solid #8B5CF6; }
.stat-icon { font-size: 2rem; margin-bottom: 10px; }
.stat-title { color: #CBD5E1; font-size: 0.9rem; font-weight: 600; }
.stat-value { color: white; font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
.stat-change { font-size: 0.85rem; font-weight: 600; display: inline-block; padding: 4px 8px; border-radius: 12px; }
.positive { background: rgba(16, 185, 129, 0.2); color: #10B981; }
.negative { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
.warning { background: rgba(245, 158, 11, 0.2); color: #F59E0B; }

.chart-container {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
}

.filter-panel {
    background: rgba(30, 41, 59, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 30px;
}
@media (max-width: 1200px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .stats-grid { grid-template-columns: 1fr; } }

.metric-card {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 12px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.metric-title { color: #94A3B8; font-size: 0.8rem; font-weight: 600; }
.metric-value { color: white; font-size: 1.5rem; font-weight: 700; margin: 5px 0; }

.app-footer {
    text-align: center;
    padding: 40px 20px;
    margin-top: 60px;
    color: #64748B;
    font-size: 0.9rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
<div class="main-bg"></div>
""", unsafe_allow_html=True)

# ==============================================================================
# NAVEGACION
# ==============================================================================
def initialize_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Inicio"
    if 'module_data' not in st.session_state:
        st.session_state.module_data = {}
    if 'guias_registradas' not in st.session_state:
        st.session_state.guias_registradas = []
    if 'contador_guias' not in st.session_state:
        st.session_state.contador_guias = 1000
    if 'qr_images' not in st.session_state:
        st.session_state.qr_images = {}
    if 'logos' not in st.session_state:
        st.session_state.logos = {}
    if 'gastos_datos' not in st.session_state:
        st.session_state.gastos_datos = {
            'manifesto': None, 'facturas': None, 'resultado': None,
            'metricas': None, 'resumen': None, 'validacion': None,
            'guias_anuladas': None, 'procesado': False
        }

def navigate_to_module(module_key):
    st.session_state.current_page = module_key
    st.rerun()

def create_module_card(icon, title, description, module_key):
    card_html = f"""
    <div class="module-card" onclick="window.location.href='?page={module_key}'">
        <div class="card-icon">{icon}</div>
        <div class="card-title">{title}</div>
        <div class="card-description">{description}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    if st.button(f"Acceder a {title}", key=f"btn_{module_key}", use_container_width=True):
        navigate_to_module(module_key)

def show_module_header(title_with_icon, subtitle):
    icon = title_with_icon[0] if title_with_icon else ""
    title_text = title_with_icon[1:].strip() if title_with_icon else ""
    st.markdown(f"""
    <div class="module-header">
        <h1 class="header-title">{icon} {title_text}</h1>
        <div class="header-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def show_main_page():
    st.markdown("""
    <div class="gallery-container">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribucion Ecuador | ERP</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="modules-grid">', unsafe_allow_html=True)
    all_modules = [
        {"icon": "📊", "title": "Dashboard KPIs", "description": "Metricas operativas en tiempo real", "key": "dashboard_kpis"},
        {"icon": "💰", "title": "Reconciliacion", "description": "Conciliacion financiera y analisis de facturas", "key": "reconciliacion_v8"},
        {"icon": "📧", "title": "Auditoria de Correos", "description": "Analisis inteligente de novedades por email", "key": "auditoria_correos"},
        {"icon": "📦", "title": "Dashboard Logistico", "description": "Control de transferencias y distribucion", "key": "dashboard_logistico"},
        {"icon": "👥", "title": "Gestion de Equipo", "description": "Administracion del personal", "key": "gestion_equipo"},
        {"icon": "🚚", "title": "Generar Guias", "description": "Sistema de envios con seguimiento QR", "key": "generar_guias"},
        {"icon": "📋", "title": "Control de Inventario", "description": "Gestion de stock en tiempo real", "key": "control_inventario"},
        {"icon": "📈", "title": "Reportes Avanzados", "description": "Analisis y estadisticas ejecutivas", "key": "reportes_avanzados"},
        {"icon": "⚙️", "title": "Configuracion", "description": "Personalizacion del sistema ERP", "key": "configuracion"}
    ]
    role = st.session_state.role
    if role == "Bodega":
        modules = [m for m in all_modules if m["key"] == "generar_guias"]
    else:
        modules = all_modules
    
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
# BASE DE DATOS LOCAL
# ==============================================================================
class LocalDatabase:
    def __init__(self):
        self.data = {
            'users': [
                {'id': 1, 'username': 'admin', 'role': 'admin', 'password_hash': hash_password('admin123')},
                {'id': 2, 'username': 'user', 'role': 'user', 'password_hash': hash_password('user123')},
            ],
            'kpis': self._generate_kpis_data(),
            'guias': [],
            'trabajadores': [
                {'id': 1, 'nombre': 'Andres Yepez', 'cargo': 'Supervisor', 'estado': 'Activo'},
                {'id': 2, 'nombre': 'Josue Imbacuan', 'cargo': 'Operador', 'estado': 'Activo'},
                {'id': 3, 'nombre': 'Maria Gonzalez', 'cargo': 'Auditora', 'estado': 'Activo'}
            ],
            'distribuciones': []
        }
    
    def _generate_kpis_data(self):
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
        if table not in self.data:
            return []
        results = self.data[table]
        if filters:
            for key, value in filters.items():
                results = [item for item in results if item.get(key) == value]
        return results
    
    def insert(self, table, data):
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
        if table in self.data:
            self.data[table] = [item for item in self.data[table] if item.get('id') != id]
        return True

local_db = LocalDatabase()

# ==============================================================================
# FUNCIONES GLOBALES PARA RECONCILIACION
# ==============================================================================
def normalizar_texto(texto):
    if pd.isna(texto) or texto == '':
        return ''
    texto = str(texto)
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except:
        texto = texto.upper()
    texto = re.sub(r'[^A-Za-z0-9\s]', ' ', texto.upper())
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def identificar_tipo_tienda(nombre):
    try:
        if pd.isna(nombre) or nombre == '':
            return "DESCONOCIDO"
        nombre_upper = normalizar_texto(nombre)
        if 'JOFRE' in nombre_upper and 'SANTANA' in nombre_upper:
            return "VENTAS AL POR MAYOR"
        nombres_personales = [
            'ROCIO','ALEJANDRA','ANGELICA','DELGADO','CRUZ','LILIANA','SALAZAR','RICARDO',
            'SANCHEZ','JAZMIN','ALVARADO','MELISSA','CHAVEZ','KARLA','SORIANO','ESTEFANIA',
            'GUALPA','MARIA','JESSICA','PEREZ','LOYO'
        ]
        palabras = nombre_upper.split()
        for palabra in palabras:
            if len(palabra) > 2 and palabra in nombres_personales:
                return "VENTA WEB"
        patrones_fisicas = [
            'LOCAL','AEROPOSTALE','MALL','PLAZA','SHOPPING','CENTRO','COMERCIAL',
            'CC','C.C','TIENDA','SUCURSAL','PRICE','CLUB','DORADO','CIUDAD',
            'RIOCENTRO','PASEO','PORTAL','SOL','CONDADO','CITY','CEIBOS',
            'IBARRA','MATRIZ','BODEGA','FASHION','GYE','QUITO','MACHALA',
            'PORTOVIEJO','BABAHOYO','MANTA','AMBATO','CUENCA','ALMACEN','PRATI'
        ]
        for patron in patrones_fisicas:
            if patron in nombre_upper:
                return "TIENDA FÍSICA"
        if len(palabras) >= 3:
            return "TIENDA FÍSICA"
        elif any(len(p) > 3 for p in palabras):
            return "TIENDA FÍSICA"
        else:
            return "VENTA WEB"
    except:
        return "DESCONOCIDO"

def procesar_subtotal(valor):
    if pd.isna(valor):
        return 0.0
    try:
        if isinstance(valor, (int, float, np.number)):
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

def obtener_columna_piezas(manifesto):
    posibles_nombres = ['PIEZAS', 'CANTIDAD', 'UNIDADES', 'QTY', 'CANT', 'PZS', 'BULTOS']
    for col in manifesto.columns:
        col_upper = str(col).upper()
        for nombre in posibles_nombres:
            if nombre in col_upper:
                return col
    return None

def obtener_columna_fecha(manifesto):
    posibles_nombres = ['FECHA', 'FECHA ING', 'FECHA INGRESO', 'FECHA CREACION', 'FECHA_ING', 'FECHA_CREACION']
    for col in manifesto.columns:
        col_upper = str(col).upper()
        for nombre in posibles_nombres:
            if nombre in col_upper:
                return col
    return None

# ==============================================================================
# FUNCION GLOBAL PROCESAR GASTOS
# ==============================================================================
def procesar_gastos(manifesto, facturas, config):
    """Procesa y valida gastos por tienda usando DESTINATARIO del manifiesto"""
    try:
        columnas_manifesto = manifesto.columns.tolist()
        col_guia_m = config['guia_m']
        if col_guia_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if 'GUIA' in str(col).upper() or 'GUÍA' in str(col).upper():
                    col_guia_m = col
                    break
            if col_guia_m not in columnas_manifesto:
                raise ValueError(f"No se encontró columna de guía en el manifiesto. Columnas: {columnas_manifesto}")
        
        col_subtotal_m = config.get('subtotal_m', '')
        if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if 'SUBT' in str(col).upper() or 'TOTAL' in str(col).upper() or 'VALOR' in str(col).upper():
                    col_subtotal_m = col
                    break
            if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
                col_subtotal_m = columnas_manifesto[-1]
        
        col_ciudad_m = config.get('ciudad_destino', '')
        if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if 'CIUDAD' in str(col).upper() or 'DES' in str(col).upper() or 'DESTINO' in str(col).upper():
                    col_ciudad_m = col
                    break
            if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
                col_ciudad_m = 'CIUDAD'
                manifesto[col_ciudad_m] = 'DESCONOCIDA'
        
        col_piezas_m = obtener_columna_piezas(manifesto)
        if not col_piezas_m:
            manifesto['PIEZAS'] = 1
            col_piezas_m = 'PIEZAS'
        
        col_fecha_m = obtener_columna_fecha(manifesto)
        
        col_destinatario_m = None
        posibles_destinatario = ['DESTINATARIO', 'CONSIGNATARIO', 'CLIENTE', 'NOMBRE', 'RAZON SOCIAL']
        for col in posibles_destinatario:
            if col in columnas_manifesto:
                col_destinatario_m = col
                break
        if not col_destinatario_m:
            for col in columnas_manifesto:
                col_upper = str(col).upper()
                if any(p in col_upper for p in ['DEST', 'CONSIG', 'CLIEN', 'NOMB', 'RAZON']):
                    col_destinatario_m = col
                    break
        if not col_destinatario_m:
            manifesto['DESTINATARIO_MANIFIESTO'] = 'TIENDA ' + manifesto[col_ciudad_m].astype(str)
            col_destinatario_m = 'DESTINATARIO_MANIFIESTO'
        
        otras_columnas_importantes = []
        for col in manifesto.columns:
            col_upper = str(col).upper()
            if any(p in col_upper for p in ['FECHA', 'ORIGEN', 'SERVICIO', 'TRANSPORTE', 'PESO', 'FLETE']):
                otras_columnas_importantes.append(col)
        
        columnas_manifiesto = [col_guia_m, col_subtotal_m, col_ciudad_m, col_destinatario_m, col_piezas_m]
        if col_fecha_m:
            columnas_manifiesto.append(col_fecha_m)
        columnas_manifiesto += otras_columnas_importantes
        columnas_manifiesto = list(dict.fromkeys(columnas_manifiesto))
        df_m = manifesto[columnas_manifiesto].copy()
        
        df_m['GUIA'] = df_m[col_guia_m].astype(str).str.strip()
        df_m['SUBTOTAL_MANIFIESTO'] = df_m[col_subtotal_m].apply(procesar_subtotal)
        df_m['CIUDAD_MANIFIESTO'] = df_m[col_ciudad_m].fillna('DESCONOCIDA').astype(str)
        df_m['DESTINATARIO_MANIFIESTO'] = df_m[col_destinatario_m].fillna('DESTINATARIO DESCONOCIDO').astype(str)
        df_m['PIEZAS_MANIFIESTO'] = pd.to_numeric(df_m[col_piezas_m], errors='coerce').fillna(1)
        if col_fecha_m:
            try:
                df_m['FECHA_MANIFIESTO'] = pd.to_datetime(df_m[col_fecha_m], errors='coerce')
            except:
                df_m['FECHA_MANIFIESTO'] = df_m[col_fecha_m].astype(str)
        df_m['GUIA_LIMPIA'] = df_m['GUIA'].str.upper()
        
        columnas_facturas = facturas.columns.tolist()
        col_guia_f = config['guia_f']
        if col_guia_f not in columnas_facturas:
            for col in columnas_facturas:
                if 'GUIA' in str(col).upper() or 'GUÍA' in str(col).upper():
                    col_guia_f = col
                    break
            if col_guia_f not in columnas_facturas:
                raise ValueError(f"No se encontró columna de guía en facturas. Columnas: {columnas_facturas}")
        
        col_subtotal_f = config.get('subtotal', '')
        if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
            for col in columnas_facturas:
                if 'SUBTOTAL' in str(col).upper() or 'TOTAL' in str(col).upper() or 'IMPORTE' in str(col).upper() or 'VALOR' in str(col).upper():
                    col_subtotal_f = col
                    break
            if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
                col_subtotal_f = columnas_facturas[-1]
        
        df_f = facturas[[col_guia_f, col_subtotal_f]].copy()
        df_f['GUIA_FACTURA'] = df_f[col_guia_f].astype(str).str.strip()
        df_f['SUBTOTAL_FACTURA'] = df_f[col_subtotal_f].apply(procesar_subtotal)
        df_f['GUIA_LIMPIA'] = df_f['GUIA_FACTURA'].str.upper()
        
        df_completo = pd.merge(df_m, df_f[['GUIA_LIMPIA', 'SUBTOTAL_FACTURA']], on='GUIA_LIMPIA', how='left')
        df_completo['DESTINATARIO'] = df_completo['DESTINATARIO_MANIFIESTO']
        df_completo['CIUDAD'] = df_completo['CIUDAD_MANIFIESTO']
        df_completo['PIEZAS'] = df_completo['PIEZAS_MANIFIESTO']
        df_completo['ESTADO'] = df_completo['SUBTOTAL_FACTURA'].apply(lambda x: 'FACTURADA' if pd.notna(x) and float(x) > 0 else 'ANULADA')
        df_completo['SUBTOTAL'] = df_completo['SUBTOTAL_FACTURA'].fillna(0)
        df_completo['DIFERENCIA'] = df_completo['SUBTOTAL_MANIFIESTO'] - df_completo['SUBTOTAL']
        df_completo['TIPO'] = df_completo['DESTINATARIO'].apply(identificar_tipo_tienda)
        df_completo['NOMBRE_NORMALIZADO'] = df_completo['DESTINATARIO'].apply(normalizar_texto)
        
        def crear_grupo(fila):
            tipo = fila['TIPO']
            nombre = fila['NOMBRE_NORMALIZADO']
            ciudad = normalizar_texto(fila['CIUDAD'])
            if tipo == "VENTA WEB":
                palabras = nombre.split()
                if len(palabras) >= 2:
                    return f"VENTA WEB - {palabras[0]} {palabras[1]}"
                else:
                    return f"VENTA WEB - {nombre}"
            elif tipo == "VENTAS AL POR MAYOR":
                return "VENTAS AL POR MAYOR - JOFRE SANTANA"
            elif tipo == "TIENDA FÍSICA":
                grupo_ciudad = f"{ciudad} - " if ciudad != "DESCONOCIDA" else ""
                palabras = nombre.split()
                if len(palabras) > 0:
                    nombre_grupo = ' '.join(palabras[:min(3, len(palabras))])
                    return f"{grupo_ciudad}{nombre_grupo}"
                else:
                    return f"{grupo_ciudad}TIENDA"
            else:
                return f"DESCONOCIDO - {nombre[:20]}"
        df_completo['GRUPO'] = df_completo.apply(crear_grupo, axis=1)
        
        guias_facturadas = df_completo[df_completo['ESTADO'] == 'FACTURADA'].shape[0]
        guias_anuladas = df_completo[df_completo['ESTADO'] == 'ANULADA'].shape[0]
        total_piezas = df_completo['PIEZAS'].sum()
        guias_anuladas_df = df_completo[df_completo['ESTADO'] == 'ANULADA'].copy()
        
        df_facturadas = df_completo[df_completo['ESTADO'] == 'FACTURADA']
        metricas = df_facturadas.groupby('GRUPO').agg(
            GUIAS=('GUIA_LIMPIA', 'count'),
            PIEZAS=('PIEZAS', 'sum'),
            SUBTOTAL=('SUBTOTAL', 'sum'),
            SUBTOTAL_MANIFIESTO=('SUBTOTAL_MANIFIESTO', 'sum'),
            DIFERENCIA=('DIFERENCIA', 'sum'),
            DESTINATARIOS=('DESTINATARIO', lambda x: ', '.join(sorted(set(str(d) for d in x if pd.notna(d) and str(d) != ''))[:5])),
            CIUDADES=('CIUDAD', lambda x: ', '.join(sorted(set(str(c) for c in x if pd.notna(c) and str(c) != ''))[:3])),
            TIPO=('TIPO', lambda x: x.mode()[0] if not x.mode().empty else 'DESCONOCIDO')
        ).reset_index()
        total_general = metricas['SUBTOTAL'].sum()
        if total_general > 0:
            metricas['PORCENTAJE'] = (metricas['SUBTOTAL'] / total_general * 100).round(2)
            metricas['PROMEDIO_POR_PIEZA'] = (metricas['SUBTOTAL'] / metricas['PIEZAS']).round(2)
        else:
            metricas['PORCENTAJE'] = 0.0
            metricas['PROMEDIO_POR_PIEZA'] = 0.0
        metricas['PIEZAS_POR_GUIA'] = (metricas['PIEZAS'] / metricas['GUIAS']).round(2)
        metricas = metricas.sort_values('SUBTOTAL', ascending=False)
        
        resumen = df_facturadas.groupby('TIPO').agg(
            TIENDAS=('GRUPO', 'nunique'),
            GUIAS=('GUIA_LIMPIA', 'count'),
            PIEZAS=('PIEZAS', 'sum'),
            SUBTOTAL=('SUBTOTAL', 'sum')
        ).reset_index()
        if total_general > 0:
            resumen['PORCENTAJE'] = (resumen['SUBTOTAL'] / total_general * 100).round(2)
        resumen = resumen.sort_values('SUBTOTAL', ascending=False)
        
        total_manifiesto = df_completo['SUBTOTAL_MANIFIESTO'].sum()
        total_facturas = df_completo['SUBTOTAL'].sum()
        validacion = {
            'total_manifiesto': total_manifiesto,
            'total_facturas': total_facturas,
            'diferencia': abs(total_manifiesto - total_facturas),
            'porcentaje': (abs(total_manifiesto - total_facturas) / total_manifiesto * 100) if total_manifiesto > 0 else 0,
            'coincide': abs(total_manifiesto - total_facturas) < 0.01,
            'guias_procesadas': len(df_completo),
            'guias_facturadas': guias_facturadas,
            'guias_anuladas': guias_anuladas,
            'piezas_totales': total_piezas,
            'grupos_identificados': len(metricas),
            'porcentaje_facturadas': (guias_facturadas / len(df_completo) * 100) if len(df_completo) > 0 else 0,
            'porcentaje_anuladas': (guias_anuladas / len(df_completo) * 100) if len(df_completo) > 0 else 0
        }
        return df_completo, metricas, resumen, validacion, guias_anuladas_df
    except Exception as e:
        st.error(f"Error en procesar_gastos: {str(e)}")
        raise

# ==============================================================================
# GENERAR EXCEL CON FORMATO EXACTO
# ==============================================================================
def generar_excel_con_formato_exacto(metricas_filt, resultado, guias_anuladas, manifesto_original=None):
    try:
        output = BytesIO()
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Reporte"
        hoja1_data = metricas_filt[['GRUPO', 'SUBTOTAL']].copy().sort_values('GRUPO')
        ws1.append(["", ""])
        ws1.append(["", ""])
        ws1.append(["Etiquetas de fila", "Suma de SUBTOTAL"])
        for _, row in hoja1_data.iterrows():
            ws1.append([row['GRUPO'], row['SUBTOTAL']])
        ws1.append(["Total general", hoja1_data['SUBTOTAL'].sum()])
        for row in ws1.iter_rows(min_row=3, max_row=ws1.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for cell in ws1[3]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(4, ws1.max_row + 1):
            ws1.cell(row=row, column=2).number_format = '#,##0.00'
        ws1.column_dimensions['A'].width = 50
        ws1.column_dimensions['B'].width = 20
        
        ws2 = wb.create_sheet(title="Tiendas")
        columnas = ["GRUPO", "GUIAS", "PIEZAS", "SUBTOTAL", "DESTINATARIOS", "CIUDADES", "TIPO", "PORCENTAJE", "PROMEDIO_POR_PIEZA", "PIEZAS_POR_GUIA"]
        ws2.append(columnas)
        for _, row in metricas_filt.iterrows():
            ws2.append([row['GRUPO'], int(row['GUIAS']), int(row['PIEZAS']), row['SUBTOTAL'], row['DESTINATARIOS'], row['CIUDADES'], row['TIPO'], row['PORCENTAJE'], row['PROMEDIO_POR_PIEZA'], row['PIEZAS_POR_GUIA']])
        ws2.append(["" for _ in columnas])
        ult_fila = ws2.max_row - 1
        ws2.append(["Total general", "", "", f"=SUBTOTAL(109,D2:D{ult_fila})", "", "", "", "", "", ""])
        for row in ws2.iter_rows(min_row=1, max_row=ws2.max_row, min_col=1, max_col=len(columnas)):
            for cell in row:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for cell in ws2[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(2, ws2.max_row + 1):
            ws2.cell(row=row, column=4).number_format = '#,##0.00'
            ws2.cell(row=row, column=8).number_format = '0.00'
            ws2.cell(row=row, column=9).number_format = '0.00'
            ws2.cell(row=row, column=10).number_format = '0.00'
        ws2.column_dimensions['A'].width = 40
        ws2.column_dimensions['B'].width = 10
        ws2.column_dimensions['C'].width = 10
        ws2.column_dimensions['D'].width = 15
        ws2.column_dimensions['E'].width = 50
        ws2.column_dimensions['F'].width = 20
        ws2.column_dimensions['G'].width = 20
        ws2.column_dimensions['H'].width = 15
        ws2.column_dimensions['I'].width = 20
        ws2.column_dimensions['J'].width = 20
        
        if not guias_anuladas.empty:
            ws3 = wb.create_sheet(title="Guias Anuladas")
            posibles_columnas = ['FECHA_MANIFIESTO', 'GUIA', 'ORIGEN', 'GUIA2', 'DESTINATARIO_MANIFIESTO', 'SERVICIO', 'TRANSPORTE', 'PIEZAS_MANIFIESTO', 'PESO', 'FLETE', 'SUBTOTAL_MANIFIESTO', 'CIUDAD_MANIFIESTO', 'ESTADO']
            columnas_anuladas = [c for c in posibles_columnas if c in guias_anuladas.columns]
            mapeo_nombres = {'FECHA_MANIFIESTO':'FECHA','DESTINATARIO_MANIFIESTO':'DESTINATARIO','PIEZAS_MANIFIESTO':'NUMERO DE PIEZAS','SUBTOTAL_MANIFIESTO':'SUBTOTAL','CIUDAD_MANIFIESTO':'CIUDAD'}
            columnas_anuladas_display = [mapeo_nombres.get(c,c) for c in columnas_anuladas]
            ws3.append(columnas_anuladas_display)
            for _, row in guias_anuladas.iterrows():
                fila_data = []
                for col in columnas_anuladas:
                    val = row[col]
                    if col == 'FECHA_MANIFIESTO' and pd.notna(val) and hasattr(val, 'strftime'):
                        fila_data.append(val.strftime('%d/%m/%Y %H:%M'))
                    elif col in ['PIEZAS_MANIFIESTO']:
                        fila_data.append(int(val) if pd.notna(val) else 0)
                    elif col in ['SUBTOTAL_MANIFIESTO']:
                        fila_data.append(float(val) if pd.notna(val) else 0.0)
                    else:
                        fila_data.append(val if pd.notna(val) else '')
                ws3.append(fila_data)
            ws3.append(["" for _ in columnas_anuladas_display])
            total_row = ["" for _ in columnas_anuladas_display]
            if 'NUMERO DE PIEZAS' in columnas_anuladas_display:
                idx = columnas_anuladas_display.index('NUMERO DE PIEZAS') + 1
                total_row[idx-1] = f"=SUBTOTAL(109,{get_column_letter(idx)}2:{get_column_letter(idx)}{ws3.max_row-1})"
            if 'SUBTOTAL' in columnas_anuladas_display:
                idx = columnas_anuladas_display.index('SUBTOTAL') + 1
                total_row[idx-1] = f"=SUBTOTAL(109,{get_column_letter(idx)}2:{get_column_letter(idx)}{ws3.max_row-1})"
            ws3.append(total_row)
            for row in ws3.iter_rows(min_row=1, max_row=ws3.max_row, min_col=1, max_col=len(columnas_anuladas_display)):
                for cell in row:
                    cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            for cell in ws3[1]:
                cell.fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")
            for i, ancho in enumerate([18,15,15,20,15,40,15,15,15,10,10,15,20,15][:len(columnas_anuladas_display)]):
                ws3.column_dimensions[get_column_letter(i+1)].width = ancho
        
        ws4 = wb.create_sheet(title="Detalle")
        col_detalle = ['FECHA_MANIFIESTO', 'GUIA', 'ESTADO', 'GRUPO', 'DESTINATARIO', 'CIUDAD', 'PIEZAS', 'SUBTOTAL_MANIFIESTO', 'SUBTOTAL', 'DIFERENCIA', 'TIPO']
        col_detalle = [c for c in col_detalle if c in resultado.columns]
        detalle_df = resultado[col_detalle].copy()
        mapeo = {'FECHA_MANIFIESTO':'FECHA','GUIA':'GUIA','ESTADO':'ESTADO','GRUPO':'GRUPO','DESTINATARIO':'DESTINATARIO','CIUDAD':'CIUDAD','PIEZAS':'PIEZAS','SUBTOTAL_MANIFIESTO':'SUBTOTAL MANIFIESTO','SUBTOTAL':'SUBTOTAL FACTURA','DIFERENCIA':'DIFERENCIA','TIPO':'TIPO'}
        detalle_df = detalle_df.rename(columns=mapeo)
        ws4.append(list(detalle_df.columns))
        for _, row in detalle_df.iterrows():
            fila = []
            for col in detalle_df.columns:
                val = row[col]
                if col == 'FECHA' and pd.notna(val) and hasattr(val, 'strftime'):
                    fila.append(val.strftime('%d/%m/%Y %H:%M'))
                elif col in ['PIEZAS']:
                    fila.append(int(val) if pd.notna(val) else 0)
                elif col in ['SUBTOTAL MANIFIESTO','SUBTOTAL FACTURA','DIFERENCIA']:
                    fila.append(float(val) if pd.notna(val) else 0.0)
                else:
                    fila.append(val if pd.notna(val) else '')
            ws4.append(fila)
        for row in ws4.iter_rows(min_row=1, max_row=ws4.max_row, min_col=1, max_col=len(detalle_df.columns)):
            for cell in row:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for cell in ws4[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        anchos = [20,15,12,40,30,20,10,15,15,15,20]
        for i, ancho in enumerate(anchos[:len(detalle_df.columns)]):
            ws4.column_dimensions[get_column_letter(i+1)].width = ancho
        
        wb.save(output)
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Error generar Excel: {str(e)}")
        return None

# ==============================================================================
# GENERAR PDF REPORTE EJECUTIVO
# ==============================================================================
def generar_pdf_reporte(metricas, resumen, validacion, filtros_aplicados=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=12, alignment=1)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
        normal_style = styles['Normal']
        elements.append(Paragraph("REPORTE EJECUTIVO - GESTIÓN DE GASTOS POR TIENDA", title_style))
        elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
        elements.append(Spacer(1,12))
        elements.append(Paragraph("MÉTRICAS PRINCIPALES", subtitle_style))
        metricas_data = [
            ["Total Facturado", f"${validacion['total_facturas']:,.2f}"],
            ["Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}"],
            ["Diferencia", f"${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%)"],
            ["Guías Procesadas", f"{validacion['guias_procesadas']:,}"],
            ["Guías Facturadas", f"{validacion['guias_facturadas']:,} ({validacion['porcentaje_facturadas']:.1f}%)"],
            ["Guías Anuladas", f"{validacion['guias_anuladas']:,} ({validacion['porcentaje_anuladas']:.1f}%)"],
            ["Piezas Totales", f"{validacion['piezas_totales']:,}"],
            ["Grupos Identificados", f"{validacion['grupos_identificados']:,}"]
        ]
        metricas_table = Table(metricas_data, colWidths=[200,150])
        metricas_table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,0),12),
            ('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)
        ]))
        elements.append(metricas_table)
        elements.append(Spacer(1,20))
        elements.append(Paragraph("RESUMEN POR TIPO DE TIENDA", subtitle_style))
        if not resumen.empty:
            resumen_data = [["TIPO","TIENDAS","GUÍAS","PIEZAS","SUBTOTAL","%"]]
            for _, row in resumen.iterrows():
                resumen_data.append([row['TIPO'], str(int(row['TIENDAS'])), str(int(row['GUIAS'])), str(int(row['PIEZAS'])), f"${row['SUBTOTAL']:,.2f}", f"{row['PORCENTAJE']:.2f}%"])
            resumen_table = Table(resumen_data, colWidths=[120,80,80,80,100,80])
            resumen_table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('FONTSIZE',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,0),12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)
            ]))
            elements.append(resumen_table)
        elements.append(Spacer(1,20))
        elements.append(Paragraph("TOP 15 GRUPOS POR GASTO", subtitle_style))
        if not metricas.empty:
            top_15 = metricas.head(15)
            grupos_data = [["GRUPO","GUÍAS","PIEZAS","SUBTOTAL","%","PROM/PIEZA"]]
            for _, row in top_15.iterrows():
                grupo = row['GRUPO'][:30] + "..." if len(row['GRUPO'])>30 else row['GRUPO']
                grupos_data.append([grupo, str(int(row['GUIAS'])), str(int(row['PIEZAS'])), f"${row['SUBTOTAL']:,.2f}", f"{row['PORCENTAJE']:.2f}%", f"${row['PROMEDIO_POR_PIEZA']:,.2f}"])
            grupos_table = Table(grupos_data, colWidths=[150,60,60,90,60,80])
            grupos_table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('FONTSIZE',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,0),12),
                ('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),1,colors.black)
            ]))
            elements.append(grupos_table)
        elements.append(Spacer(1,20))
        elements.append(Paragraph("ANÁLISIS EJECUTIVO", subtitle_style))
        analisis_text = f"""
        <b>Validación:</b> {"✅ COINCIDENCIA EXACTA" if validacion['coincide'] else "⚠ CON DIFERENCIAS"}<br/>
        <b>Facturación:</b> {validacion['porcentaje_facturadas']:.1f}% de guías facturadas ({validacion['guias_facturadas']:,} guías)<br/>
        <b>Anulaciones:</b> {validacion['porcentaje_anuladas']:.1f}% de guías anuladas ({validacion['guias_anuladas']:,} guías)<br/>
        <b>Distribución:</b> {resumen.iloc[0]['TIPO'] if not resumen.empty else 'N/A'} representa el {resumen.iloc[0]['PORCENTAJE'] if not resumen.empty else 0:.1f}% del total facturado<br/>
        <b>Eficiencia:</b> Promedio de {validacion['piezas_totales']/validacion['guias_procesadas']:.1f} piezas por guía<br/>
        <b>Recomendación:</b> {"Revisar guías anuladas para optimizar facturación" if validacion['guias_anuladas'] > 0 else "Proceso de facturación eficiente"}
        """
        elements.append(Paragraph(analisis_text, normal_style))
        doc.build(elements)
        return pdf_path
    except Exception as e:
        st.error(f"Error generar PDF: {str(e)}")
        return None

# ==============================================================================
# MODULO RECONCILIACION V8
# ==============================================================================
def show_reconciliacion_v8():
    show_module_header("💰 Gestión de Gastos por Tienda", "Conciliación financiera y análisis de facturas")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    
    if 'gastos_datos' not in st.session_state:
        st.session_state.gastos_datos = {
            'manifesto': None, 'facturas': None, 'resultado': None,
            'metricas': None, 'resumen': None, 'validacion': None,
            'guias_anuladas': None, 'procesado': False
        }
    
    def cargar_archivo_local(uploaded_file, nombre):
        try:
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                excel_file = pd.ExcelFile(uploaded_file)
                hojas = excel_file.sheet_names
                hoja_seleccionada = None
                for hoja in hojas:
                    temp_df = pd.read_excel(uploaded_file, sheet_name=hoja, nrows=5)
                    if not temp_df.empty and len(temp_df.columns) > 1:
                        hoja_seleccionada = hoja
                        break
                if hoja_seleccionada is None:
                    hoja_seleccionada = hojas[0]
                st.sidebar.info(f"Hoja seleccionada: {hoja_seleccionada}")
                df = pd.read_excel(uploaded_file, sheet_name=hoja_seleccionada)
                st.sidebar.success(f"✓ {nombre}: {len(df):,} filas")
            elif uploaded_file.name.endswith('.csv'):
                encodings = ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(uploaded_file, encoding=encoding)
                        st.sidebar.success(f"✓ {nombre}: {len(df):,} filas ({encoding})")
                        break
                    except UnicodeDecodeError:
                        if encoding == encodings[-1]:
                            raise
                        continue
            else:
                st.sidebar.error(f"Formato no soportado: {uploaded_file.name}")
                return None
            df = df.dropna(axis=1, how='all').dropna(how='all')
            if df.empty:
                st.sidebar.error(f"{nombre}: Archivo vacío")
                return None
            return df
        except Exception as e:
            st.sidebar.error(f"Error cargar {nombre}: {str(e)}")
            return None

    with st.sidebar:
        st.header("📁 Carga de Archivos")
        uploaded_manifesto = st.file_uploader("Manifiesto (con DESTINATARIO y PIEZAS)", type=['csv','xlsx','xls'], key="manifesto_upload")
        uploaded_facturas = st.file_uploader("Facturas (solo GUÍA y VALOR)", type=['csv','xlsx','xls'], key="facturas_upload")
        if uploaded_manifesto and uploaded_facturas:
            if st.button("📥 Cargar Archivos", type="primary", use_container_width=True):
                with st.spinner("Cargando..."):
                    manifesto = cargar_archivo_local(uploaded_manifesto, "Manifiesto")
                    facturas = cargar_archivo_local(uploaded_facturas, "Facturas")
                    if manifesto is not None and facturas is not None:
                        st.session_state.gastos_datos['manifesto'] = manifesto
                        st.session_state.gastos_datos['facturas'] = facturas
                        col1,col2 = st.columns(2)
                        with col1: st.metric("Registros Manifiesto", f"{len(manifesto):,}")
                        with col2: st.metric("Registros Facturas", f"{len(facturas):,}")
    
    if st.session_state.gastos_datos['manifesto'] is not None:
        manifesto = st.session_state.gastos_datos['manifesto']
        facturas = st.session_state.gastos_datos['facturas']
        st.header("⚙️ Configuración")
        col1,col2 = st.columns(2)
        with col1:
            st.write("**Manifiesto**")
            guia_opciones_m = [c for c in manifesto.columns if 'GUIA' in str(c).upper() or 'GUÍA' in str(c).upper()] or manifesto.columns.tolist()
            guia_m = st.selectbox("Columna Guía", guia_opciones_m, index=0)
            subtotal_opciones_m = [c for c in manifesto.columns if any(p in str(c).upper() for p in ['SUBT','TOTAL','VALOR'])] or manifesto.columns.tolist()
            subtotal_m = st.selectbox("Columna Subtotal", subtotal_opciones_m, index=0)
            ciudad_opciones_m = [c for c in manifesto.columns if any(p in str(c).upper() for p in ['CIUDAD','DES','DESTINO'])] or manifesto.columns.tolist()
            ciudad_destino = st.selectbox("Columna Ciudad", ciudad_opciones_m, index=0)
        with col2:
            st.write("**Facturas**")
            guia_opciones_f = [c for c in facturas.columns if 'GUIA' in str(c).upper() or 'GUÍA' in str(c).upper()] or facturas.columns.tolist()
            guia_f = st.selectbox("Columna Guía", guia_opciones_f, index=0)
            subtotal_opciones_f = [c for c in facturas.columns if any(p in str(c).upper() for p in ['SUBTOTAL','TOTAL','IMPORTE','VALOR'])] or facturas.columns.tolist()
            subtotal_f = st.selectbox("Columna Subtotal", subtotal_opciones_f, index=0)
        
        config = {'guia_m':guia_m, 'subtotal_m':subtotal_m, 'ciudad_destino':ciudad_destino, 'guia_f':guia_f, 'subtotal':subtotal_f}
        
        if st.button("🚀 Procesar Gastos por Tienda", type="primary", use_container_width=True):
            with st.spinner("Procesando..."):
                try:
                    resultado, metricas, resumen, validacion, guias_anuladas = procesar_gastos(manifesto, facturas, config)
                    st.session_state.gastos_datos.update({'resultado':resultado, 'metricas':metricas, 'resumen':resumen, 'validacion':validacion, 'guias_anuladas':guias_anuladas, 'procesado':True})
                    st.success("✅ Procesamiento exitoso")
                    if validacion['coincide']:
                        st.balloons()
                    else:
                        st.warning(f"⚠ Diferencia de ${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%)")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    if st.session_state.gastos_datos['procesado']:
        resultado = st.session_state.gastos_datos['resultado']
        metricas = st.session_state.gastos_datos['metricas']
        resumen = st.session_state.gastos_datos['resumen']
        validacion = st.session_state.gastos_datos['validacion']
        guias_anuladas = st.session_state.gastos_datos['guias_anuladas']
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 Resumen","✅ Validación","🏪 Todas las Tiendas","🚫 Guías Anuladas","🌎 Geografía","📋 Datos","💾 Exportar","📄 Reporte PDF"])
        
        with tab1:
            st.header("Resumen Ejecutivo")
            col1,col2,col3,col4,col5 = st.columns(5)
            with col1: st.metric("Grupos", len(metricas))
            with col2: st.metric("Total Guías", len(resultado))
            with col3: st.metric("Guías Anuladas", validacion['guias_anuladas'])
            with col4: st.metric("Piezas Totales", validacion['piezas_totales'])
            with col5: st.metric("Total Facturado", f"${metricas['SUBTOTAL'].sum():,.2f}")
            if not resumen.empty:
                fig = px.pie(resumen, values='SUBTOTAL', names='TIPO', title="Distribución por Tipo", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(resumen.style.format({'SUBTOTAL':'${:,.2f}','PORCENTAJE':'{:.2f}%'}))
        
        with tab2:
            st.header("Validación")
            col1,col2,col3,col4,col5 = st.columns(5)
            with col1: st.metric("Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}")
            with col2: st.metric("Total Facturas", f"${validacion['total_facturas']:,.2f}")
            with col3: st.metric("Diferencia", f"${validacion['diferencia']:,.2f}")
            with col4: st.metric("% Diferencia", f"{validacion['porcentaje']:.2f}%")
            with col5: st.metric("Guías Anuladas", validacion['guias_anuladas'])
            if validacion['coincide']:
                st.success("✅ Validación exitosa")
            else:
                st.warning(f"⚠ Diferencia de ${validacion['diferencia']:,.2f}")
        
        with tab3:
            st.header("Todas las Tiendas")
            # Filtros
            min_gasto = st.number_input("Gasto mínimo", value=0.0, step=10.0)
            tipo_filtro = st.multiselect("Tipo", metricas['TIPO'].unique() if 'TIPO' in metricas.columns else [])
            ciudad_filtro = st.text_input("Ciudad (parcial)")
            min_piezas = st.number_input("Mín. piezas", value=0, step=1)
            buscar = st.text_input("Buscar grupo/destinatario")
            metricas_filt = metricas.copy()
            if min_gasto>0: metricas_filt = metricas_filt[metricas_filt['SUBTOTAL']>=min_gasto]
            if tipo_filtro: metricas_filt = metricas_filt[metricas_filt['TIPO'].isin(tipo_filtro)]
            if ciudad_filtro: metricas_filt = metricas_filt[metricas_filt['CIUDADES'].str.contains(ciudad_filtro, case=False, na=False)]
            if min_piezas>0: metricas_filt = metricas_filt[metricas_filt['PIEZAS']>=min_piezas]
            if buscar: metricas_filt = metricas_filt[metricas_filt['GRUPO'].str.contains(buscar, case=False, na=False) | metricas_filt['DESTINATARIOS'].str.contains(buscar, case=False, na=False)]
            st.dataframe(metricas_filt.style.format({'SUBTOTAL':'${:,.2f}','PORCENTAJE':'{:.2f}%','PROMEDIO_POR_PIEZA':'${:,.2f}'}), use_container_width=True)
        
        with tab4:
            st.header("Guías Anuladas")
            if not guias_anuladas.empty:
                st.metric("Total", len(guias_anuladas))
                st.dataframe(guias_anuladas[['FECHA_MANIFIESTO','GUIA','DESTINATARIO','CIUDAD','PIEZAS','SUBTOTAL_MANIFIESTO','TIPO']].style.format({'SUBTOTAL_MANIFIESTO':'${:,.2f}'}), use_container_width=True)
            else:
                st.success("No hay guías anuladas")
        
        with tab5:
            st.header("Geografía")
            if 'CIUDAD' in resultado.columns:
                df_fact = resultado[resultado['ESTADO']=='FACTURADA']
                ciudad_agg = df_fact.groupby('CIUDAD').agg({'GUIA_LIMPIA':'count','PIEZAS':'sum','SUBTOTAL':'sum'}).reset_index().rename(columns={'GUIA_LIMPIA':'GUIAS','PIEZAS':'PIEZAS','SUBTOTAL':'SUBTOTAL'})
                fig = px.bar(ciudad_agg.head(15), x='SUBTOTAL', y='CIUDAD', orientation='h', title="Top Ciudades")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab6:
            st.header("Datos Detallados")
            estado_filtro = st.selectbox("Estado", ['TODOS','FACTURADA','ANULADA'])
            datos_filt = resultado.copy()
            if estado_filtro == 'FACTURADA': datos_filt = datos_filt[datos_filt['ESTADO']=='FACTURADA']
            elif estado_filtro == 'ANULADA': datos_filt = datos_filt[datos_filt['ESTADO']=='ANULADA']
            st.dataframe(datos_filt[['FECHA_MANIFIESTO','GUIA','ESTADO','GRUPO','DESTINATARIO','CIUDAD','PIEZAS','SUBTOTAL_MANIFIESTO','SUBTOTAL','DIFERENCIA','TIPO']].style.format({'SUBTOTAL_MANIFIESTO':'${:,.2f}','SUBTOTAL':'${:,.2f}','DIFERENCIA':'${:,.2f}'}), use_container_width=True)
        
        with tab7:
            st.header("Exportar")
            if st.button("📊 Generar Excel Formato Exacto", use_container_width=True):
                with st.spinner("Generando..."):
                    excel_output = generar_excel_con_formato_exacto(metricas, resultado, guias_anuladas)
                    if excel_output:
                        st.download_button("📥 Descargar", data=excel_output.getvalue(), file_name=f"reporte_gastos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        with tab8:
            st.header("Reporte PDF")
            if st.button("🖨️ Generar PDF", use_container_width=True):
                with st.spinner("Generando..."):
                    pdf_path = generar_pdf_reporte(metricas, resumen, validacion)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            st.download_button("📥 Descargar PDF", data=f.read(), file_name=f"reporte_ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
    
    else:
        st.info("👆 Carga los archivos desde el panel lateral para comenzar.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MODULO AUDITORIA DE CORREOS
# ==============================================================================
class WiloEmailEngine:
    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.mail = None

    def _connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.host)
            self.mail.login(self.user, self.password)
        except Exception as e:
            raise ConnectionError(f"Error conexión: {e}")

    def _decode_utf8(self, header_part) -> str:
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

    def _get_folders(self) -> List[str]:
        try:
            result, folder_list = self.mail.list()
            folders = []
            for folder in folder_list:
                folder_name = folder.decode()
                if ' "/" ' in folder_name:
                    parts = folder_name.split(' "/" ')
                    name = parts[-1].strip('"')
                elif ' "." ' in folder_name:
                    parts = folder_name.split(' "." ')
                    name = parts[-1].strip('"')
                else:
                    name = folder_name.strip()
                folders.append(name)
            return folders
        except:
            return ["INBOX"]

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

    def get_latest_news(self, days: int = 90, limit_per_folder: int = 50) -> List[Dict[str, Any]]:
        self._connect()
        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        folders = self._get_folders()
        results = []
        for folder in folders:
            try:
                self.mail.select(folder)
                _, messages = self.mail.search(None, f'(SINCE "{since_date}")')
                ids = messages[0].split()
                if not ids:
                    continue
                recent_ids = ids[-limit_per_folder:]
                for e_id in reversed(recent_ids):
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
                                "pedido": order_id,
                                "carpeta": folder
                            })
            except Exception as e:
                st.warning(f"Error en carpeta {folder}: {e}")
        self.mail.logout()
        return results

def show_auditoria_correos():
    show_module_header("📧 Auditoria de Correos", "Análisis inteligente de novedades por email")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    st.sidebar.title("🔐 Acceso")
    mail_user = st.sidebar.text_input("Correo", value="wperez@fashionclub.com.ec")
    mail_pass = st.sidebar.text_input("Contraseña", value="2wperez*.", type="password")
    imap_host = "mail.fashionclub.com.ec"
    st.title("📧 Auditoria de Correos Wilo AI")
    col_info, col_btn = st.columns([3,1])
    with col_info:
        st.info(f"Usuario: {mail_user} | Servidor: {imap_host}")
    with col_btn:
        run_audit = st.button("🚀 Iniciar Auditoria", use_container_width=True, type="primary")
    if run_audit:
        if not mail_pass:
            st.error("Ingresa la contraseña")
            return
        engine = WiloEmailEngine(imap_host, mail_user, mail_pass)
        with st.spinner("Conectando y analizando..."):
            try:
                data = engine.get_latest_news(days=90, limit_per_folder=50)
                if not data:
                    st.warning("No se encontraron correos en los últimos 90 días")
                    return
                df = pd.DataFrame(data)
                m1,m2,m3,m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Críticos", len(df[df['urgencia']=='ALTA']))
                m3.metric("Faltantes", len(df[df['tipo'].str.contains('FALTANTE')]))
                m4.metric("Pedidos únicos", df['pedido'].nunique())
                st.dataframe(df[['fecha','remitente','asunto','tipo','urgencia','pedido','carpeta']], use_container_width=True)
                st.subheader("🔍 Inspector")
                idx = st.selectbox("Selecciona correo", df.index, format_func=lambda x: f"{df.iloc[x]['tipo']} - {df.iloc[x]['asunto'][:50]}")
                det = df.iloc[idx]
                st.markdown(f"**Remitente:** {det['remitente']}  \n**Fecha:** {det['fecha']}  \n**Pedido:** {det['pedido']}  \n**Carpeta:** {det['carpeta']}")
                st.text_area("Cuerpo", det['cuerpo'], height=200)
            except Exception as e:
                st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MODULO DASHBOARD LOGISTICO (KPI DIARIO, TRANSFERENCIAS, ETC)
# ==============================================================================
# Definir constantes y clases necesarias
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
COLORS = {'PRICE CLUB':'#0033A0','TIENDAS AEROPOSTALE':'#E4002B','VENTAS POR MAYOR':'#10B981','TIENDA WEB':'#8B5CF6','FALLAS':'#F59E0B','FUNDAS':'#EC4899'}
GRADIENTS = {k: f'linear-gradient(135deg, {v}15, {v}30)' for k,v in COLORS.items()}
SIZE_HIERARCHY = ['3XS','2XS','XS','XSMALL','S','SMALL','M','MEDIUM','L','LARGE','XL','XLARGE','2XL','3XL','4XL','XXLARGE','XXXLARGE']
WAREHOUSE_GROUPS = {'PRICE':'Price Club','AERO':'Aeropostale','MALL':'Centro Comercial','RIOCENTRO':'Riocentro','CONDADO':'Condado','SAN':'San','LOS':'Los'}
GENDER_MAP = {'GIRLS':'Mujer','TOPMUJER':'Mujer','WOMEN':'Mujer','LADIES':'Mujer','FEMALE':'Mujer','MUJER':'Mujer','GUYS':'Hombre','MEN':'Hombre','MAN':'Hombre','HOMBRE':'Hombre','MALE':'Hombre','UNISEX':'Unisex','KIDS':'Niño/a','CHILD':'Niño/a','BOYS':'Niño','GIRLSKIDS':'Niña','BABY':'Bebé','INFANT':'Bebé'}
CATEGORY_MAP = {
    'TEES':'Camiseta','TEE':'Camiseta','T-SHIRT':'Camiseta','TANK':'Camiseta sin mangas','TANK TOP':'Camiseta sin mangas',
    'TOP':'Top','TOPS':'Top','BARE':'Blusa','CORE':'Blusa','GRAPHIC':'Camiseta estampada','GRAPHICS':'Camiseta estampada',
    'POLO':'Polo','POLOS':'Polo','SHIRT':'Camisa','BUTTON-DOWN':'Camisa','BUTTONDOWN':'Camisa','DRESS':'Vestido','DRESSES':'Vestido','SUNDRESS':'Vestido',
    'PANTS':'Pantalón','PANT':'Pantalón','TROUSERS':'Pantalón','JEANS':'Jeans','JEAN':'Jeans','DENIM':'Jeans',
    'BOOTCUT':'Pantalón bootcut','SKINNY':'Pantalón ajustado','STRAIGHT':'Pantalón recto','FLARE':'Pantalón campana',
    'SHORTS':'Short','SHORT':'Short','BERMUDA':'Bermuda','JACKET':'Chaqueta','JACKETS':'Chaqueta','HOODIE':'Sudadera',
    'SWEATSHIRT':'Sudadera','SWEATER':'Suéter','BLAZER':'Blazer','BVD':'Ropa interior','BOXER':'Boxer','BOXERS':'Boxer',
    'UNDERWEAR':'Ropa interior','BRIEF':'Calzoncillo','BELT':'Cinturón','BELTS':'Cinturón','HAT':'Gorro','CAP':'Gorra',
    'SOCKS':'Medias','SOCK':'Medias','WOVEN':'Tejido','KNIT':'Tejido','KNITTED':'Tejido','SOLID':'Sólido','BASIC':'Básico','BASICO':'Básico',
    'LEATHER':'Cuero','SUMMER':'Verano','WINTER':'Invierno','SPRING':'Primavera','FALL':'Otoño','AUTUMN':'Otoño'
}
COLOR_MAP = {
    'BLACK':'Negro','BLACK/DARK':'Negro','DARK BLACK':'Negro Oscuro','WHITE':'Blanco','WHITE/LIGHT':'Blanco',
    'RED':'Rojo','RASPBERRY':'Frambuesa','EARTH RED':'Rojo Tierra','BLUE':'Azul','NAVY':'Azul Marino','LIGHT BLUE':'Azul Claro',
    'GREEN':'Verde','GREEN GABLES':'Verde Gabardina','YELLOW':'Amarillo','GOLD':'Dorado','PINK':'Rosa','HOT PINK':'Rosa Fuerte',
    'PURPLE':'Morado','VIOLET':'Violeta','ORANGE':'Naranja','BROWN':'Marrón','GRAY':'Gris','GREY':'Gris','SILVER':'Plateado',
    'BEIGE':'Beige','KHAKI':'Caqui','BLEACH':'Blanqueado','LIGHT WASH':'Lavado Claro','DARK':'Oscuro','LIGHT':'Claro','MULTI':'Multicolor','MULTICOLOR':'Multicolor'
}
IGNORE_WORDS = {'AERO','OF','THE','AND','IN','WITH','FOR','BY','ON','AT','TO'}

class TextileClassifier:
    def __init__(self):
        self.gender_map = GENDER_MAP
        self.category_map = CATEGORY_MAP
        self.color_map = COLOR_MAP
        self.size_hierarchy = SIZE_HIERARCHY
        self.ignore_words = IGNORE_WORDS
    def classify_product(self, product_name: str) -> dict:
        if not product_name or not isinstance(product_name, str):
            return {'Genero':'No Identificado','Categoria':'No Identificado','Subcategoria':'','Color':'No Especificado','Talla':'No Especificado','Material':'','Estilo':''}
        product_name = str(product_name).upper().strip()
        words = product_name.split()
        classification = {'Genero':'Unisex','Categoria':'General','Subcategoria':'','Color':'No Especificado','Talla':'Única','Material':'','Estilo':''}
        classification['Genero'] = self._detect_gender(words)
        cat_info = self._detect_category(words)
        classification['Categoria'] = cat_info['categoria']
        classification['Subcategoria'] = cat_info['subcategoria']
        classification['Color'] = self._detect_color(words)
        classification['Talla'] = self._detect_size(words)
        style_info = self._detect_style(words)
        classification['Material'] = style_info['material']
        classification['Estilo'] = style_info['estilo']
        return self._clean_classification(classification)
    def _detect_gender(self, words):
        for w in words:
            if w in self.gender_map:
                return self.gender_map[w]
        text = ' '.join(words)
        if any(x in text for x in ['WOMEN','LADIES','FEMALE']): return 'Mujer'
        if any(x in text for x in ['MEN','MAN','MALE']): return 'Hombre'
        return 'Unisex'
    def _detect_category(self, words):
        categoria = 'General'
        subcategoria = ''
        found = []
        for w in words:
            if w in self.category_map:
                found.append(self.category_map[w])
            elif w not in self.ignore_words and len(w)>2:
                subcategoria += w.capitalize() + ' '
        if found:
            main = ['Polo','Camiseta','Jeans','Pantalón','Vestido','Chaqueta']
            for m in main:
                if m in found:
                    categoria = m
                    break
            else:
                categoria = found[0]
            other = [c for c in found if c != categoria]
            if other:
                subcategoria = ' '.join(other) + ' ' + subcategoria.strip()
        return {'categoria':categoria.strip(),'subcategoria':subcategoria.strip()}
    def _detect_color(self, words):
        for w in words:
            if w in self.color_map:
                return self.color_map[w]
        return 'No Especificado'
    def _detect_size(self, words):
        for size in self.size_hierarchy:
            if f' {size} ' in f' {" ".join(words)} ':
                return size
        return 'Única'
    def _detect_style(self, words):
        material = ''
        estilo = ''
        materials = ['COTTON','POLYESTER','DENIM','LEATHER','WOOL','SILK']
        for w in words:
            if w in materials:
                material = w.lower().capitalize()
                break
        style_kw = {'GRAPHIC':'Estampado','PRINTED':'Estampado','SOLID':'Liso','STRIPED':'Rayado','BASIC':'Básico','PREMIUM':'Premium'}
        for w in words:
            if w in style_kw:
                estilo = style_kw[w]
                break
        return {'material':material,'estilo':estilo}
    def _clean_classification(self, cls):
        size_map = {'XSMALL':'XS','SMALL':'S','MEDIUM':'M','LARGE':'L','XLARGE':'XL','XXLARGE':'2XL'}
        if cls['Talla'] in size_map:
            cls['Talla'] = size_map[cls['Talla']]
        return cls

class DataProcessor:
    def __init__(self):
        self.classifier = TextileClassifier()
    def process_excel_file(self, file) -> pd.DataFrame:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]
            required_std = ['Producto','Fecha','Cantidad','Bodega Recibe']
            dest_aliases = ['Bodega Destino','Sucursal Destino','Destino','Bodega','Sucursal']
            col_mapping = {}
            for req in required_std:
                found = False
                for col in df.columns:
                    if col.lower() == req.lower():
                        col_mapping[col]=req; found=True; break
                if not found:
                    for col in df.columns:
                        if req.lower() in col.lower():
                            col_mapping[col]=req; found=True; break
                if not found and req == 'Bodega Recibe':
                    for alias in dest_aliases:
                        for col in df.columns:
                            if alias.lower() in col.lower():
                                col_mapping[col]=req; found=True; break
                        if found: break
                if not found:
                    st.error(f"No se encontró columna: {req}")
                    return pd.DataFrame()
            df.rename(columns=col_mapping, inplace=True)
            df['Cantidad'] = self._process_quantity(df['Cantidad'])
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True, infer_datetime_format=True)
            if df['Fecha'].isna().all():
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', format='%d/%m/%Y')
            df = df.dropna(subset=['Fecha'])
            if df.empty:
                st.warning("No se pudo interpretar la fecha")
                return pd.DataFrame()
            df = self._classify_products(df)
            df['Grupo_Bodega'] = df['Bodega Recibe'].apply(self._group_warehouse)
            sec_col = None
            posibles_sec = ['Secuencial - Factura','Secuencial','Factura','ID Transferencia','Transferencia']
            for col in df.columns:
                if any(ps.lower() in col.lower() for ps in posibles_sec):
                    sec_col = col; break
            if sec_col:
                df['ID_Transferencia'] = df[sec_col].astype(str) + '_' + df['Fecha'].dt.strftime('%Y%m%d')
            else:
                df['ID_Transferencia'] = df.index.astype(str) + '_' + df['Fecha'].dt.strftime('%Y%m%d')
            df = df.sort_values('Fecha', ascending=False).reset_index(drop=True)
            st.success(f"✅ Procesado: {len(df)} registros")
            return df
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()
    def _process_quantity(self, s):
        return pd.to_numeric(s, errors='coerce').fillna(0).astype(int)
    def _classify_products(self, df):
        classifications = [self.classifier.classify_product(p) for p in df['Producto']]
        class_df = pd.DataFrame(classifications)
        import re
        size_pattern = '|'.join(SIZE_HIERARCHY)
        pattern = r'\s+(' + size_pattern + r'|REGULAR)\s*$'
        df['Producto_Base'] = df['Producto'].str.upper().str.replace(pattern, '', regex=True).str.strip()
        df['Producto_Base'] = df['Producto_Base'].replace('', 'No especificado')
        cols_to_drop = [c for c in class_df.columns if c in df.columns]
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
        if 'PRICE' in up: return 'Price Club'
        if 'AERO' in up: return 'Aeropostale'
        if any(x in up for x in ['MALL','CENTRO','SHOPPING']): return 'Centro Comercial'
        return 'Otros'

class ReportGenerator:
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
            summary.append(['KPIs PRINCIPALES',''])
            summary.append(['Total Unidades',f'{total_units:,}'])
            summary.append(['Transferencias',f'{total_transfers:,}'])
            summary.append(['Bodegas Destino',f'{bodegas:,}'])
            summary.append(['Productos Únicos',f'{productos:,}'])
            pd.DataFrame(summary, columns=['Métrica','Valor']).to_excel(writer, sheet_name='Resumen', index=False)
            df.to_excel(writer, sheet_name='Detalle', index=False)
            if 'Bodega Recibe' in df.columns:
                w_sum = df.groupby('Bodega Recibe').agg({'Cantidad':['sum','count'],'Producto':'nunique'})
                w_sum.columns = ['Unidades','Transferencias','Productos']
                w_sum.sort_values('Unidades', ascending=False).to_excel(writer, sheet_name='Por_Bodega')
            if 'Categoria' in df.columns:
                cat_sum = df.groupby(['Categoria','Genero']).agg({'Cantidad':['sum','count'],'Producto':'nunique'})
                cat_sum.columns = ['Unidades','Transferencias','Productos']
                cat_sum.sort_values('Unidades', ascending=False).to_excel(writer, sheet_name='Por_Categoria')
            if 'Fecha' in df.columns:
                df['Fecha_Dia'] = df['Fecha'].dt.date
                daily = df.groupby('Fecha_Dia').agg({'Cantidad':'sum','ID_Transferencia':'nunique'}).reset_index()
                daily.columns = ['Fecha','Unidades','Transferencias']
                daily.sort_values('Fecha').to_excel(writer, sheet_name='Tendencias', index=False)
            if 'Producto_Base' in df.columns:
                prod_base = df.groupby('Producto_Base').agg({'Cantidad':'sum','ID_Transferencia':'nunique','Producto':'nunique'}).reset_index().rename(columns={'ID_Transferencia':'Transferencias','Producto':'Variantes'}).sort_values('Cantidad', ascending=False)
                prod_base.to_excel(writer, sheet_name='Productos_Base', index=False)
                if 'Talla' in df.columns:
                    pivot = df.pivot_table(values='Cantidad', index='Producto_Base', columns='Talla', aggfunc='sum', fill_value=0, margins=True, margins_name='Total')
                    pivot.to_excel(writer, sheet_name='Producto_Talla')
        output.seek(0)
        return output

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
    categorias = ['Price Club','Tiendas','Ventas por Mayor','Tienda Web','Fallas','Fundas']
    for cat in categorias:
        df_cat = df[df['Categoria'] == cat]
        res['por_categoria'][cat] = df_cat['Cantidad_Entera'].sum()
        if not df_cat.empty:
            res['detalle_categoria'][cat] = {'cantidad':int(df_cat['Cantidad_Entera'].sum()),'transf':int(df_cat['Secuencial'].nunique()),'unicas':int(df_cat['Sucursal Destino'].nunique())}
            res['conteo_sucursales'][cat] = res['detalle_categoria'][cat]['unicas']
        else:
            res['detalle_categoria'][cat] = {'cantidad':0,'transf':0,'unicas':0}
            res['conteo_sucursales'][cat] = 0
    return res

def mostrar_kpi_diario():
    if 'kdi_current_data' not in st.session_state:
        st.session_state.kdi_current_data = pd.DataFrame()
        st.session_state.kdi_loaded = False
    processor = DataProcessor()
    report_gen = ReportGenerator()
    st.markdown("### 📂 Cargar archivo de transferencias diarias")
    col_up1, col_up2 = st.columns([3,1])
    with col_up1:
        uploaded = st.file_uploader("Seleccionar archivo", type=['xlsx','xls','csv'], key="kdi_upload", label_visibility="collapsed")
    with col_up2:
        if st.button("🔄 Limpiar", key="kdi_clear"):
            st.session_state.kdi_current_data = pd.DataFrame()
            st.session_state.kdi_loaded = False
            st.rerun()
    if uploaded:
        with st.spinner("Procesando..."):
            new_data = processor.process_excel_file(uploaded)
            if not new_data.empty:
                st.session_state.kdi_current_data = new_data
                st.session_state.kdi_loaded = True
                st.success("Datos cargados")
    if not st.session_state.kdi_loaded or st.session_state.kdi_current_data.empty:
        st.info("👆 Sube un archivo para comenzar")
        return
    st.markdown("### 🔍 Filtros")
    data = st.session_state.kdi_current_data
    filtered = data.copy()
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        if 'Fecha' in filtered.columns:
            min_d = filtered['Fecha'].min().date()
            max_d = filtered['Fecha'].max().date()
            dr = st.date_input("Rango fechas", [min_d, max_d], key="kdi_fecha")
            if len(dr)==2:
                filtered = filtered[(filtered['Fecha'].dt.date>=dr[0]) & (filtered['Fecha'].dt.date<=dr[1])]
    with col_f2:
        if 'Bodega Recibe' in filtered.columns:
            opts = ['Todas'] + sorted(filtered['Bodega Recibe'].dropna().unique())
            sel = st.selectbox("Bodega", opts, key="kdi_bod")
            if sel != 'Todas':
                filtered = filtered[filtered['Bodega Recibe']==sel]
    with col_f3:
        if 'Genero' in filtered.columns:
            opts = ['Todos'] + sorted(filtered['Genero'].dropna().unique())
            sel = st.selectbox("Género", opts, key="kdi_gen")
            if sel != 'Todos':
                filtered = filtered[filtered['Genero']==sel]
    with col_f4:
        if 'Categoria' in filtered.columns:
            opts = ['Todas'] + sorted(filtered['Categoria'].dropna().unique())
            sel = st.selectbox("Categoría", opts, key="kdi_cat")
            if sel != 'Todas':
                filtered = filtered[filtered['Categoria']==sel]
    if filtered.empty:
        st.warning("No hay datos con filtros")
        return
    total_units = int(filtered['Cantidad'].sum())
    n_bodegas = filtered['Bodega Recibe'].nunique()
    n_transfers = filtered['ID_Transferencia'].nunique() if 'ID_Transferencia' in filtered.columns else len(filtered)
    n_products = filtered['Producto'].nunique()
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Unidades", f"{total_units:,}")
    k2.metric("Bodegas", n_bodegas)
    k3.metric("Transferencias", n_transfers)
    k4.metric("Productos", n_products)
    st.markdown("---")
    st.markdown("### 📊 Análisis por Dimensiones")
    tab_c, tab_t, tab_g, tab_cat, tab_prod = st.tabs(["🎨 Color","📏 Talla","⚧ Género","🏷️ Categoría","📦 Productos"])
    with tab_c:
        if 'Color' in filtered.columns:
            col_stats = filtered.groupby('Color')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=False)
            fig = px.pie(col_stats, values='Cantidad', names='Color', title="Color")
            st.plotly_chart(fig, use_container_width=True)
    with tab_t:
        if 'Talla' in filtered.columns:
            talla_stats = filtered.groupby('Talla')['Cantidad'].sum().reset_index()
            fig = px.bar(talla_stats, x='Talla', y='Cantidad', title="Talla")
            st.plotly_chart(fig, use_container_width=True)
    with tab_g:
        if 'Genero' in filtered.columns:
            gen_stats = filtered.groupby('Genero')['Cantidad'].sum().reset_index()
            fig = px.pie(gen_stats, values='Cantidad', names='Genero', title="Género")
            st.plotly_chart(fig, use_container_width=True)
    with tab_cat:
        if 'Categoria' in filtered.columns:
            cat_stats = filtered.groupby('Categoria')['Cantidad'].sum().reset_index().sort_values('Cantidad', ascending=False)
            fig = px.bar(cat_stats, x='Categoria', y='Cantidad', title="Categoría")
            st.plotly_chart(fig, use_container_width=True)
    with tab_prod:
        if 'Producto_Base' in filtered.columns:
            top_prod = filtered.groupby('Producto_Base')['Cantidad'].sum().nlargest(10).reset_index()
            fig = px.bar(top_prod, x='Cantidad', y='Producto_Base', orientation='h', title="Top 10 Productos")
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("Detalle de tallas por producto")
            prod_sel = st.selectbox("Producto", top_prod['Producto_Base'].unique())
            if prod_sel:
                df_prod = filtered[filtered['Producto_Base']==prod_sel]
                tallas = df_prod.groupby('Talla')['Cantidad'].sum().reset_index()
                st.bar_chart(tallas.set_index('Talla'))
    st.markdown("---")
    st.subheader("📄 Generar Reporte")
    col_r1, col_r2, col_r3 = st.columns([1,1,2])
    with col_r1:
        r_start = st.date_input("Inicio", filtered['Fecha'].min().date(), key="r_start")
    with col_r2:
        r_end = st.date_input("Fin", filtered['Fecha'].max().date(), key="r_end")
    with col_r3:
        if st.button("📥 Descargar Excel", use_container_width=True):
            with st.spinner("Generando..."):
                excel = report_gen.generate_detailed_report(filtered, r_start, r_end)
                if excel:
                    st.download_button("⬇️ Descargar", data=excel, file_name=f"KPI_Diario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def mostrar_dashboard_transferencias():
    st.markdown("""
    <div class='main-header'>
        <h1 class='header-title'>📊 Dashboard de Transferencias Diarias</h1>
        <div class='header-subtitle'>Análisis de distribución por categorías y sucursales</div>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 Transferencias Diarias","📦 Mercadería en Tránsito (KPI Diario)","📈 Análisis de Stock"])
    with tab1:
        st.markdown("### 📂 Carga de Archivo")
        file_diario = st.file_uploader("Selecciona archivo Excel", type=['xlsx'], key="diario_transferencias")
        if not file_diario:
            st.info("👆 Sube un archivo Excel para comenzar")
            return
        try:
            df_diario = pd.read_excel(file_diario)
            st.success(f"✅ Archivo cargado: {file_diario.name}")
            columnas_requeridas = ['Secuencial','Cantidad Prendas']
            columnas_destino = ['Sucursal Destino','Bodega Destino']
            faltan = [c for c in columnas_requeridas if c not in df_diario.columns]
            if faltan:
                st.error(f"Faltan columnas: {faltan}")
                return
            if not any(c in df_diario.columns for c in columnas_destino):
                st.error("No se encontró columna de destino")
                return
            res = procesar_transferencias_diarias(df_diario)
            categorias_display = {'Price Club':'PRICE CLUB','Tiendas':'TIENDAS AEROPOSTALE','Ventas por Mayor':'VENTAS POR MAYOR','Tienda Web':'TIENDA WEB','Fallas':'FALLAS','Fundas':'FUNDAS'}
            sucursales_esperadas = {'Price Club':PRICE_CLUBS,'Tiendas':TIENDAS_REGULARES,'Ventas por Mayor':VENTAS_POR_MAYOR,'Tienda Web':TIENDA_WEB,'Fallas':FALLAS,'Fundas':None}
            cols = st.columns(3)
            for i, (cat, cat_disp) in enumerate(categorias_display.items()):
                cantidad = res['por_categoria'].get(cat,0)
                suc_act = res['conteo_sucursales'].get(cat,0)
                esperadas = sucursales_esperadas.get(cat)
                color = COLORS.get(cat_disp, '#cccccc')
                with cols[i%3]:
                    st.markdown(f"""
                    <div style='background:{GRADIENTS.get(cat_disp, "linear-gradient(135deg,#f0f0f015,#e0e0e030)")}; padding:20px; border-radius:10px; border-left:5px solid {color}; margin-bottom:15px;'>
                        <div style='font-size:12px; color:#666;'>{cat_disp}</div>
                        <div style='font-size:32px; font-weight:bold; color:{color};'>{cantidad:,}</div>
                        <div style='font-size:11px; color:#888;'>{suc_act} sucursales | {esperadas} esperadas</div>
                    </div>
                    """, unsafe_allow_html=True)
                if i==2:
                    cols = st.columns(3)
            st.divider()
            st.header("Análisis Visual")
            col1, col2 = st.columns([2,1])
            with col1:
                df_pie = pd.DataFrame({'Categoria':list(res['por_categoria'].keys()),'Unidades':list(res['por_categoria'].values())})
                df_pie = df_pie[df_pie['Unidades']>0]
                fig = px.pie(df_pie, values='Unidades', names='Categoria', title="Distribución", hole=0.3, color='Categoria', color_discrete_map=COLORS)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.metric("Total General", f"{res['total_unidades']:,}")
                promedio = res['total_unidades']/res['transferencias'] if res['transferencias']>0 else 0
                st.metric("Promedio x Transferencia", f"{promedio:,.0f}")
                st.metric("Categorías Activas", f"{len(df_pie)}/6")
            st.divider()
            st.subheader("Detalle por Secuencial")
            df_detalle = res['df_procesado'][['Sucursal Destino','Secuencial','Cantidad_Entera','Categoria']].copy()
            st.dataframe(df_detalle, use_container_width=True)
            excel_data = to_excel(df_detalle)
            st.download_button("📥 Descargar Excel", data=excel_data, file_name=f"detalle_transferencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    with tab2:
        mostrar_kpi_diario()
    with tab3:
        st.header("📈 Análisis de Stock y Ventas")
        stock_file = st.file_uploader("Archivo de Stock Actual", type=['xlsx','csv'], key="stock_file")
        ventas_file = st.file_uploader("Archivo Histórico de Ventas", type=['xlsx','csv'], key="ventas_file")
        if stock_file and ventas_file:
            try:
                df_stock = pd.read_excel(stock_file) if stock_file.name.endswith('.xlsx') else pd.read_csv(stock_file)
                df_ventas = pd.read_excel(ventas_file) if ventas_file.name.endswith('.xlsx') else pd.read_csv(ventas_file)
                st.success("Datos cargados")
                # Aquí podrías agregar más análisis de stock
            except Exception as e:
                st.error(f"Error: {e}")

def show_dashboard_logistico():
    show_module_header("📦 Dashboard Logístico", "Control de transferencias y distribución en tiempo real")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    mostrar_dashboard_transferencias()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MODULO GESTION DE EQUIPO
# ==============================================================================
def show_gestion_equipo():
    show_module_header("👥 Gestión de Equipo", "Administración del personal del Centro de Distribución")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    estructura_base = {
        "Liderazgo y Control": [{"id":1,"nombre":"Wilson Perez","cargo":"Jefe de Logistica","subarea":"Cabeza del C.D.","estado":"Activo","es_base":True},
                                 {"id":2,"nombre":"Andres Cadena","cargo":"Jefe de Inventarios","subarea":"Control de Inventarios","estado":"Activo","es_base":True}],
        "Gestion de Transferencias": [{"id":3,"nombre":"Cesar Yepez","cargo":"Responsable","subarea":"Transferencias Fashion","estado":"Activo","es_base":True},
                                      {"id":4,"nombre":"Luis Perugachi","cargo":"Encargado","subarea":"Pivote de transferencias Price y Distribucion","estado":"Activo","es_base":True},
                                      {"id":5,"nombre":"Josue Imbacuan","cargo":"Responsable","subarea":"Transferencias Tempo","estado":"Activo","es_base":True}],
        "Distribucion, Empaque y Envios": [{"id":6,"nombre":"Jessica Suarez","cargo":"Distribucion Aero","subarea":"","estado":"Activo","es_base":True},
                                           {"id":7,"nombre":"Norma Paredes","cargo":"Distribucion Price","subarea":"","estado":"Activo","es_base":True},
                                           {"id":8,"nombre":"Jhonny Villa","cargo":"Empaque y Guias","subarea":"","estado":"Activo","es_base":True},
                                           {"id":9,"nombre":"Simon Vera","cargo":"Guias y Envios","subarea":"","estado":"Activo","es_base":True}],
        "Ventas al Por Mayor": [{"id":10,"nombre":"Jhonny Guadalupe","cargo":"Encargado","subarea":"Bodega y Packing","estado":"Activo","es_base":True},
                                {"id":11,"nombre":"Rocio Cadena","cargo":"Responsable","subarea":"Picking y Distribucion","estado":"Activo","es_base":True}],
        "Reproceso y Calidad": [{"id":12,"nombre":"Diana Garcia","cargo":"Encargada","subarea":"Reprocesado de prendas en cuarentena","estado":"Activo","es_base":True}]
    }
    trabajadores = local_db.query('trabajadores')
    if not trabajadores:
        for area, lista in estructura_base.items():
            for t in lista:
                t['area'] = area
                t['fecha_ingreso'] = datetime.now().strftime('%Y-%m-%d')
                local_db.insert('trabajadores', t)
        trabajadores = local_db.query('trabajadores')
    tabs = st.tabs(["📋 Estructura","➕ Gestionar","📊 Estadísticas","⚙️ Configuración"])
    with tabs[0]:
        for area, personal in estructura_base.items():
            with st.expander(f"📌 {area} ({len(personal)} personas)", expanded=True):
                cols = st.columns(3)
                for idx, p in enumerate(personal):
                    with cols[idx%3]:
                        st.markdown(f"""
                        <div style='background:white; border-radius:10px; padding:15px; margin-bottom:10px; border-left:4px solid #0033A0;'>
                            <div style='font-weight:bold;'>{p['nombre']}</div>
                            <div>{p['cargo']}</div>
                            <div style='font-size:12px; color:gray;'>{p['subarea']}</div>
                            <div style='background:#10B981; color:white; padding:2px 8px; border-radius:12px; display:inline-block;'>Activo</div>
                        </div>
                        """, unsafe_allow_html=True)
    with tabs[1]:
        area_tabs = st.tabs(list(estructura_base.keys()))
        for idx, (area, base_list) in enumerate(estructura_base.items()):
            with area_tabs[idx]:
                col1, col2 = st.columns([2,1])
                with col1:
                    st.subheader(f"Personal en {area}")
                    area_trabajadores = [t for t in trabajadores if t.get('area')==area]
                    for t in area_trabajadores:
                        cols = st.columns([1,3,2,2,1,1])
                        cols[0].write(f"**{t['id']}**")
                        cols[1].write(t['nombre'])
                        cols[2].write(t['cargo'])
                        cols[3].write(t.get('subarea','-'))
                        tipo = "Base" if t.get('es_base') else "Adicional"
                        cols[4].write(f"🟢 {tipo}")
                        if not t.get('es_base'):
                            if cols[5].button("🗑️", key=f"del_{area}_{t['id']}"):
                                local_db.delete('trabajadores', t['id'])
                                st.rerun()
                with col2:
                    with st.form(key=f"form_{area}"):
                        nombre = st.text_input("Nombre", key=f"nombre_{area}")
                        cargo = st.text_input("Cargo", key=f"cargo_{area}")
                        subarea = st.text_input("Subarea", key=f"subarea_{area}")
                        estado = st.selectbox("Estado", ["Activo","Inactivo"], key=f"estado_{area}")
                        if st.form_submit_button("➕ Agregar"):
                            if nombre and cargo:
                                new_id = max([t['id'] for t in trabajadores])+1 if trabajadores else 13
                                local_db.insert('trabajadores', {'id':new_id,'nombre':nombre,'cargo':cargo,'area':area,'subarea':subarea,'estado':estado,'es_base':False,'fecha_ingreso':datetime.now().strftime('%Y-%m-%d')})
                                st.rerun()
    with tabs[2]:
        if trabajadores:
            df_todos = pd.DataFrame(trabajadores)
            total = len(df_todos)
            activos = len(df_todos[df_todos['estado']=='Activo']) if 'estado' in df_todos else total
            base = len(df_todos[df_todos.get('es_base',False)==True]) if 'es_base' in df_todos else 0
            adicional = total - base
            col1,col2,col3,col4 = st.columns(4)
            col1.metric("Total Personal", total)
            col2.metric("Activos", activos)
            col3.metric("Personal Base", base)
            col4.metric("Adicionales", adicional)
            if 'area' in df_todos:
                area_counts = df_todos['area'].value_counts().reset_index()
                area_counts.columns = ['Area','Cantidad']
                fig = px.bar(area_counts, x='Area', y='Cantidad', title="Distribución por Área")
                st.plotly_chart(fig, use_container_width=True)
    with tabs[3]:
        if st.button("🔄 Restaurar Estructura Base"):
            for t in trabajadores:
                if not t.get('es_base'):
                    local_db.delete('trabajadores', t['id'])
            st.success("Estructura base restaurada")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MODULO GENERAR GUIAS
# ==============================================================================
def descargar_logo(url):
    try:
        resp = requests.get(url, timeout=10)
        return resp.content if resp.status_code==200 else None
    except:
        return None

def generar_pdf_profesional(guia_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.2*inch, leftMargin=0.2*inch, topMargin=0.2*inch, bottomMargin=0.2*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('TituloPrincipal', parent=styles['Title'], fontSize=16, textColor=HexColor('#000000'), fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle('Subtitulo', parent=styles['Heading2'], fontSize=12, textColor=HexColor('#000000'), fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle('EncabezadoSeccion', parent=styles['Heading3'], fontSize=10, textColor=HexColor('#000000'), fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=4, underline=True))
    styles.add(ParagraphStyle('CampoContenido', parent=styles['Normal'], fontSize=10, textColor=HexColor('#000000'), fontName='Helvetica', alignment=TA_LEFT, spaceAfter=4, leftIndent=10))
    contenido = []
    logo_bytes = st.session_state.logos.get(guia_data['marca'])
    if not logo_bytes:
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg" if guia_data['marca']=='Fashion Club' else "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
        logo_bytes = descargar_logo(logo_url)
        if logo_bytes:
            st.session_state.logos[guia_data['marca']] = logo_bytes
    if logo_bytes:
        logo_img = Image(io.BytesIO(logo_bytes), width=1*inch, height=1*inch)
        logo_cell = logo_img
    else:
        logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", styles['TituloPrincipal'])
    titulo_cell = Paragraph(f"<b>CENTRO DE DISTRIBUCION<br/>{guia_data['marca'].upper()}</b>", styles['TituloPrincipal'])
    qr_bytes = guia_data.get('qr_bytes')
    if qr_bytes:
        qr_img = Image(io.BytesIO(qr_bytes), width=1*inch, height=1*inch)
        qr_cell = qr_img
    else:
        qr_cell = Paragraph("", styles['Normal'])
    cabecera = Table([[logo_cell, titulo_cell, qr_cell]], colWidths=[1.5*inch,3.5*inch,1*inch])
    cabecera.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(0,0),'LEFT'),('ALIGN',(1,0),(1,0),'CENTER'),('ALIGN',(2,0),(2,0),'CENTER'),('PADDING',(0,0),(-1,-1),2)]))
    contenido.append(cabecera)
    contenido.append(Paragraph("GUIA DE REMISION", styles['Subtitulo']))
    info_guia = Table([[Paragraph(f"<b>Numero de Guia:</b> {guia_data['numero']}", styles['CampoContenido']),
                        Paragraph(f"<b>Fecha de Emision:</b> {guia_data['fecha_emision']}", styles['CampoContenido']),
                        Paragraph(f"<b>Estado:</b> {guia_data['estado']}", styles['CampoContenido'])]], colWidths=[2.5*inch,2.5*inch,2.5*inch])
    info_guia.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#F0F0F0')),('PADDING',(0,0),(-1,-1),6),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BOX',(0,0),(-1,-1),0.5,HexColor('#CCCCCC'))]))
    contenido.append(info_guia)
    contenido.append(Spacer(1,0.1*inch))
    remitente_destinatario = Table([
        [Paragraph("<b>REMITENTE</b>", styles['EncabezadoSeccion']), Paragraph("<b>DESTINATARIO</b>", styles['EncabezadoSeccion'])],
        [Paragraph(f"<b>Nombre:</b> {guia_data['remitente']}", styles['CampoContenido']), Paragraph(f"<b>Nombre:</b> {guia_data['destinatario']}", styles['CampoContenido'])],
        [Paragraph(f"<b>Direccion:</b> {guia_data['direccion_remitente']}", styles['CampoContenido']), Paragraph(f"<b>Ciudad:</b> {guia_data['tienda_destino']}", styles['CampoContenido'])],
        ['', Paragraph(f"<b>Direccion:</b> {guia_data['direccion_destinatario']}", styles['CampoContenido'])]
    ], colWidths=[3.5*inch,3.5*inch])
    remitente_destinatario.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),4),('GRID',(0,0),(-1,-1),0.5,HexColor('#CCCCCC')),('BACKGROUND',(0,0),(1,0),HexColor('#E8E8E8'))]))
    contenido.append(remitente_destinatario)
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()

def mostrar_vista_previa_guia(guia_data):
    st.markdown("---")
    st.markdown(f"### 👁️ Vista Previa - Guía {guia_data['numero']}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='background:#f8f9fa; border-radius:10px; padding:20px; margin-bottom:20px; border-left:4px solid #0033A0;'>
            <h4 style='color:#0033A0;'>🏢 Información de la Empresa</h4>
            <p><strong>Marca:</strong> {guia_data['marca']}</p>
            <p><strong>Número de Guía:</strong> {guia_data['numero']}</p>
            <p><strong>Fecha:</strong> {guia_data['fecha_emision']}</p>
            <p><strong>Estado:</strong> {guia_data['estado']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#f8f9fa; border-radius:10px; padding:20px; border-left:4px solid #E4002B;'>
            <h4 style='color:#E4002B;'>👤 Remitente</h4>
            <p><strong>Nombre:</strong> {guia_data['remitente']}</p>
            <p><strong>Dirección:</strong> {guia_data['direccion_remitente'][:50]}...</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='background:#f8f9fa; border-radius:10px; padding:20px; border-left:4px solid #10B981;'>
            <h4 style='color:#10B981;'>🏪 Destinatario</h4>
            <p><strong>Nombre:</strong> {guia_data['destinatario']}</p>
            <p><strong>Teléfono:</strong> {guia_data['telefono_destinatario']}</p>
            <p><strong>Tienda:</strong> {guia_data['tienda_destino']}</p>
            <p><strong>Dirección:</strong> {guia_data['direccion_destinatario'][:50]}...</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#f8f9fa; border-radius:10px; padding:20px; border-left:4px solid #8B5CF6;'>
            <h4 style='color:#8B5CF6;'>🔗 Seguimiento</h4>
            <p><strong>URL:</strong> {guia_data['url_pedido']}</p>
        </div>
        """, unsafe_allow_html=True)
    if guia_data.get('qr_bytes'):
        st.image(guia_data['qr_bytes'], caption="Código QR", width=150)

def show_generar_guias():
    show_module_header("🚚 Generador de Guías", "Sistema de envíos con seguimiento QR")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    tiendas_options = [""] + [t["Nombre de Tienda"] for t in TIENDAS_DATA]
    remitentes = [{"nombre":"Josue Imbacuan","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Luis Perugachi","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Andres Yepez","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Wilson Perez","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Andres Cadena","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Diana Garcia","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Jessica Suarez","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Rocio Cadena","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
                  {"nombre":"Jhony Villa","direccion":"San Roque, Calle Santo Thomas y antigua via a Cotacachi"}]
    def get_tienda_data(nombre):
        for t in TIENDAS_DATA:
            if t["Nombre de Tienda"] == nombre:
                return t
        return None
    with st.form("guias_form", border=False):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.radio("Marca", ["Fashion Club","Tempo"], horizontal=True)
            if marca == "Tempo":
                st.image("https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg", caption="Tempo", use_container_width=True)
            else:
                st.image("https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg", caption="Fashion Club", use_container_width=True)
        with col2:
            remitente_nombre = st.selectbox("Remitente", [r["nombre"] for r in remitentes])
            remitente_direccion = next(r["direccion"] for r in remitentes if r["nombre"]==remitente_nombre)
            st.info(f"📍 {remitente_direccion}")
        st.divider()
        tienda_seleccionada = st.selectbox("Tienda Destino (autocompletar)", tiendas_options, index=0)
        datos_tienda = get_tienda_data(tienda_seleccionada) if tienda_seleccionada else None
        col5, col6 = st.columns(2)
        with col5:
            nombre_dest = st.text_input("Nombre del Destinatario", value=datos_tienda["Contacto"] if datos_tienda else "")
            telefono_dest = st.text_input("Teléfono", value=datos_tienda["Teléfono"] if datos_tienda else "")
        with col6:
            direccion_dest = st.text_area("Dirección", value=datos_tienda["Dirección"] if datos_tienda else "", height=100)
        st.divider()
        url_pedido = st.text_input("URL del Pedido", placeholder="https://...", value="https://pedidos.fashionclub.com/")
        if url_pedido and url_pedido.startswith(('http://','https://')):
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(url_pedido)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            st.session_state.qr_images[url_pedido] = img_bytes.getvalue()
            st.image(img_bytes, caption="Código QR", width=150)
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit = st.form_submit_button("🚀 Generar Guia PDF", type="primary", use_container_width=True)
        with col_btn2:
            preview = st.form_submit_button("👁️ Vista Previa", use_container_width=True)
        with col_btn3:
            reset = st.form_submit_button("🔄 Nuevo Formulario", use_container_width=True)
    if preview:
        if not nombre_dest or not direccion_dest:
            st.warning("Complete nombre y dirección del destinatario")
        else:
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            qr_bytes = st.session_state.qr_images.get(url_pedido) if url_pedido in st.session_state.qr_images else None
            preview_data = {
                "numero": guia_num, "marca": marca, "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion, "destinatario": nombre_dest,
                "telefono_destinatario": telefono_dest or "No especificado",
                "direccion_destinatario": direccion_dest, "tienda_destino": tienda_seleccionada or "No especificada",
                "url_pedido": url_pedido, "estado": "Vista Previa", "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "qr_bytes": qr_bytes
            }
            mostrar_vista_previa_guia(preview_data)
    if submit:
        errors = []
        if not nombre_dest: errors.append("Nombre del destinatario obligatorio")
        if not direccion_dest: errors.append("Dirección del destinatario obligatoria")
        if not url_pedido.startswith(('http://','https://')): errors.append("URL debe comenzar con http:// o https://")
        if errors:
            for e in errors: st.error(e)
        else:
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1
            qr_bytes = st.session_state.qr_images.get(url_pedido) if url_pedido in st.session_state.qr_images else None
            guia_data = {
                "numero": guia_num, "marca": marca, "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion, "destinatario": nombre_dest,
                "telefono_destinatario": telefono_dest or "No especificado",
                "direccion_destinatario": direccion_dest, "tienda_destino": tienda_seleccionada or "No especificada",
                "url_pedido": url_pedido, "estado": "Generada", "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "qr_bytes": qr_bytes
            }
            st.session_state.guias_registradas.append(guia_data)
            try:
                local_db.insert('guias', guia_data)
            except: pass
            pdf_bytes = generar_pdf_profesional(guia_data)
            st.success(f"✅ Guía {guia_num} generada")
            st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=f"guia_{guia_num}.pdf", mime="application/pdf")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MODULOS RESTANTES (PLACEHOLDERS)
# ==============================================================================
def show_control_inventario():
    show_module_header("📋 Control de Inventario", "Gestión de stock en tiempo real")
    st.info("🚧 Módulo en Desarrollo")

def show_reportes_avanzados():
    show_module_header("📈 Reportes Avanzados", "Análisis y estadísticas ejecutivas")
    st.info("🚧 Módulo en Desarrollo")

def show_configuracion():
    show_module_header("⚙️ Configuración", "Personalización del sistema ERP")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["General","Usuarios","Seguridad"])
    with tab1:
        st.header("Configuración General")
        col1, col2 = st.columns(2)
        with col1:
            zona = st.selectbox("Zona Horaria", ["America/Guayaquil","UTC"])
            moneda = st.selectbox("Moneda", ["USD","EUR","COP"])
        with col2:
            formato_fecha = st.selectbox("Formato Fecha", ["DD/MM/YYYY","MM/DD/YYYY"])
            decimales = st.slider("Decimales",0,4,2)
        if st.button("💾 Guardar"):
            st.success("Guardado")
    with tab2:
        st.header("Usuarios")
        usuarios = local_db.query('users')
        if usuarios:
            st.dataframe(pd.DataFrame(usuarios)[['username','role']])
        with st.form("new_user"):
            user = st.text_input("Usuario")
            pwd = st.text_input("Contraseña", type="password")
            role = st.selectbox("Rol", ["admin","user"])
            if st.form_submit_button("Agregar"):
                if user and pwd:
                    local_db.insert('users', {'username':user, 'role':role, 'password_hash':hash_password(pwd)})
                    st.rerun()
    with tab3:
        st.header("Seguridad")
        st.slider("Longitud mínima",6,20,8)
        st.checkbox("Requerir mayúsculas", True)
        st.checkbox("Requerir números", True)
        if st.button("Aplicar"):
            st.success("Aplicado")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# NAVEGACION PRINCIPAL
# ==============================================================================
def main():
    initialize_session_state()
    if not check_password():
        return
    show_header()
    role = st.session_state.role
    allowed_modules = {
        "dashboard_kpis": ["Administrador"],
        "reconciliacion_v8": ["Administrador"],
        "auditoria_correos": ["Administrador"],
        "dashboard_logistico": ["Administrador"],
        "gestion_equipo": ["Administrador"],
        "generar_guias": ["Administrador","Bodega"],
        "control_inventario": ["Administrador"],
        "reportes_avanzados": ["Administrador"],
        "configuracion": ["Administrador"]
    }
    current_page = st.session_state.current_page
    if current_page != "Inicio":
        if current_page in allowed_modules and role not in allowed_modules[current_page]:
            st.error("⛔ Acceso denegado")
            st.session_state.current_page = "Inicio"
            st.rerun()
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
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

# ==============================================================================
# FUNCION DASHBOARD KPIS (definida al final para no romper referencias)
# ==============================================================================
def show_dashboard_kpis():
    show_module_header("📊 Dashboard de KPIs", "Métricas en tiempo real del Centro de Distribución")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", datetime.now() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col3:
        tipo_kpi = st.selectbox("📈 Tipo de Métrica", ["Produccion","Eficiencia","Costos","Alertas"])
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
                st.markdown(f"""
                <div class='stat-card card-blue'>
                    <div class='stat-icon'>🏭</div>
                    <div class='stat-title'>Producción Promedio</div>
                    <div class='stat-value'>{prod_prom:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k2:
                efic_prom = df_filtered['eficiencia'].mean()
                st.markdown(f"""
                <div class='stat-card card-green'>
                    <div class='stat-icon'>⚡</div>
                    <div class='stat-title'>Eficiencia</div>
                    <div class='stat-value'>{efic_prom:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k3:
                alert_total = df_filtered['alertas'].sum()
                st.markdown(f"""
                <div class='stat-card card-red'>
                    <div class='stat-icon'>🚨</div>
                    <div class='stat-title'>Alertas Totales</div>
                    <div class='stat-value'>{alert_total}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k4:
                costo_prom = df_filtered['costos'].mean()
                st.markdown(f"""
                <div class='stat-card card-purple'>
                    <div class='stat-icon'>💰</div>
                    <div class='stat-title'>Costo Promedio</div>
                    <div class='stat-value'>${costo_prom:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            fig = px.line(df_filtered, x='fecha', y='produccion', title='Producción Diaria', line_shape='spline')
            fig.update_traces(line=dict(color='#0033A0', width=3))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Cargando datos de KPIs...")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
