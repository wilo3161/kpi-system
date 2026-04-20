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
import qrcode
import requests
import imaplib
import email
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from email.header import decode_header
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import letter, landscape, A5, A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white, grey, whitesmoke, beige
from openpyxl import Workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
import tempfile

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# CONSTANTES GLOBALES
# ==============================================================================
TIENDAS_DATA = [
    {
        "Nombre de Tienda": "Aeropostale - (Cuenca) Mall del Rio",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "CUENCA",
        "Contacto": "Marco Eras",
        "Dirección": "Av. Felipe II y Autopista Sur - CC Mall del Rio",
        "Teléfono": "994570933",
    },
    {
        "Nombre de Tienda": "Aeropostale - 6 de Diciembre",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUITO",
        "Contacto": "Micaela Yépez",
        "Dirección": "Av. 6 de Diciembre y Thomas de Berlanga CC Riocentro UIO",
        "Teléfono": "987883889",
    },
    {
        "Nombre de Tienda": "Aeropostale - Paseo Ambato",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "AMBATO",
        "Contacto": "Franco Torres",
        "Dirección": "Manuelita Saenz y Pio Baroja, cerca al parque de las Flores CC Paseo Shopping",
        "Teléfono": "984951515",
    },
    {
        "Nombre de Tienda": "Aeropostale - Ambato",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "AMBATO",
        "Contacto": "Gabriela Urrutia",
        "Dirección": "Av. Atahualpa y Victor Hugo CC Mall de Los Andes",
        "Teléfono": "967239488",
    },
    {
        "Nombre de Tienda": "Aeropostale - Babahoyo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "BABAHOYO",
        "Contacto": "Yomaira Sellan",
        "Dirección": "Av.Enrique Ponce Luque CC Paseo Shopping Babahoyo",
        "Teléfono": "981641355",
    },
    {
        "Nombre de Tienda": "Aeropostale - bomboli",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "SANTO DOMINGO",
        "Contacto": "Josselyn Navarrete",
        "Dirección": "Via Chone Diagonal a la Universidad Catolica CC Bpmbolí Shopping",
        "Teléfono": "933906346",
    },
    {
        "Nombre de Tienda": "Aeropostale - Bahía de Caráquez",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "BAHIA DE CARAQUEZ",
        "Contacto": "Nayely Orejuela",
        "Dirección": "Av. 3 de Noviembre - CC Paseo Shoping Bahía de caraquez",
        "Teléfono": "981131760",
    },
    {
        "Nombre de Tienda": "Aeropostale - Carapungo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUITO",
        "Contacto": "María José Benalcazar",
        "Dirección": "Av. Simón Bolívar, Panamericana Norte y calle, Capitán Giovanni Calles - CC",
        "Teléfono": "997242323",
    },
    {
        "Nombre de Tienda": "Aeropostale - CCI",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUITO",
        "Contacto": "Carolina Procel",
        "Dirección": "Av. Amazonas y Naciones Unidas - CC Iñaquito",
        "Teléfono": "984048928",
    },
    {
        "Nombre de Tienda": "Aeropostale - Ceibos",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Angie Delgado",
        "Dirección": "Av. Del Bombero y San Eduardo - Riocentro Ceibos",
        "Teléfono": "999085369",
    },
    {
        "Nombre de Tienda": "Aeropostale - Centro Histórico",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "CUENCA",
        "Contacto": "Renata Sacari",
        "Dirección": "Av. Simón Bolívar y PadreA guirre Centro Histórico diagonal a a la chocolateri",
        "Teléfono": "980874018",
    },
    {
        "Nombre de Tienda": "Aeropostale - City Mall",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Jordan Guale",
        "Dirección": "Av. felipe Pezo y Av. Benjamín Carrión CC City Mall",
        "Teléfono": "962880194",
    },
    {
        "Nombre de Tienda": "Aeropostale - Condado Shopping",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUITO",
        "Contacto": "Mateo Recalde",
        "Dirección": "Av. Mariscal Sucre entre Av. La Prensa Y Jhon F. Kennedy - CC Condado Sh",
        "Teléfono": "993736447",
    },
    {
        "Nombre de Tienda": "Aeropostale - Daule",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "DAULE",
        "Contacto": "Alisson Ramirez",
        "Dirección": "Av. Vicente Piedrahita y Coronel Calletano Cestaris- Paseo Shoping Daule",
        "Teléfono": "978881886",
    },
    {
        "Nombre de Tienda": "Aeropostale - Dorado",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Oscar Alvarado",
        "Dirección": "Av. León Febres Cordero Ribadeneyra - Rio Centro Dorado",
        "Teléfono": "959098012",
    },
    {
        "Nombre de Tienda": "Aeropostale - Durán",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "DURÁN",
        "Contacto": "Yaritza Córdova",
        "Dirección": "Av. Boliche Panamericana - Paseo Shoping Durán Junto al Terminal",
        "Teléfono": "996359344",
    },
    {
        "Nombre de Tienda": "Aeropostale - el Coca",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "EL COCA",
        "Contacto": "Adriana Zurita",
        "Dirección": "Av. 9 de Octubre y Rio Curaray - Junto a Super Akí el Coca",
        "Teléfono": "989137928",
    },
    {
        "Nombre de Tienda": "Aeropostale - La Plaza",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "IBARRA",
        "Contacto": "Andrea Andrango",
        "Dirección": "Av. Mariano Acosta entre Inacio Canelos y Victor Gómez Jurado - CC La Plaz",
        "Teléfono": "978765143",
    },
    {
        "Nombre de Tienda": "Aeropostale - Lago Agrio",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "LAGO AGRIO",
        "Contacto": "Angie Maldonado",
        "Dirección": "Av. Quito y Pasaje Brazil - Junto a Super Akí Lago Agrio",
        "Teléfono": "989893309",
    },
    {
        "Nombre de Tienda": "Aeropostale - Machala",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "MACHALA",
        "Contacto": "Iris carpio",
        "Dirección": "Av. Paquisha y Vía Machala km. 2 1/2 - CC Paseo Shoping Machala",
        "Teléfono": "997260162",
    },
    {
        "Nombre de Tienda": "Aeropostale - Mall del Pacífico",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "MANTA",
        "Contacto": "Karina Figueroa",
        "Dirección": "Av. Malecón y Calle 23 - CC Mall del Pacifico",
        "Teléfono": "990614279",
    },
    {
        "Nombre de Tienda": "Aeropostale - Mall del Rio (Gye)",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Danna Peralta",
        "Dirección": "Av. Francisco de Orellana y Av. Guillermo Pareja - CC Mall del Rio",
        "Teléfono": "995609664",
    },
    {
        "Nombre de Tienda": "Aeropostale - Mall del Sol",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Kiara Dávalos",
        "Dirección": "Av. Juan tanca marengo, Carlos Aurelio Rubira Infante 14 NE y Pasaje 1A - C",
        "Teléfono": "992753549",
    },
    {
        "Nombre de Tienda": "Aeropostale - Mall del Sur",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Judith Asunción",
        "Dirección": "AV 25 de Julio junto al Hospital de IESS - CC Mall del Sur",
        "Teléfono": "999669429",
    },
    {
        "Nombre de Tienda": "Aeropostale - Manta",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "MANTA",
        "Contacto": "Yenny Alvia",
        "Dirección": "Av. 4 de noviembre Paseo Shoping Manta",
        "Teléfono": "995168732",
    },
    {
        "Nombre de Tienda": "Aeropostale - Milagro",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "MILAGRO",
        "Contacto": "Lady Silva",
        "Dirección": "Av. 12 de Octubre, entre presidente Jerónimo Carrión y presidente Javier Espi",
        "Teléfono": "985415948",
    },
    {
        "Nombre de Tienda": "Aeropostale - Peso Shopping Riobama",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "RIOBAMBA",
        "Contacto": "María Fernanda Ibarra",
        "Dirección": "Av. Antonio José de Sucre frente a la Universidad UNACH CC Paseo Shoppin",
        "Teléfono": "993438844",
    },
    {
        "Nombre de Tienda": "Aeropostale - Multiplaza Riobamba",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "RIOBAMBA",
        "Contacto": "Jennifer Jimenez",
        "Dirección": "Avenida Lizarzaburu y Agustin Torres - CC Multiplaza Riobamba",
        "Teléfono": "962636619",
    },
    {
        "Nombre de Tienda": "Aeropostale - Pasaje",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PASAJE",
        "Contacto": "Jhonny Cun",
        "Dirección": "Av. Quito entrada a Pasaje y Redondel del León - Junto a Super Aki Pasaje",
        "Teléfono": "969586186",
    },
    {
        "Nombre de Tienda": "Aeropostale - Paseo Ambato",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "AMBATO",
        "Contacto": "Franco Torres",
        "Dirección": "Av.Pio Baroja Nesi y Av. Manuelita Saéns Paseo Shoping Ambato",
        "Teléfono": "984951515",
    },
    {
        "Nombre de Tienda": "Aeropostale - Pedernales",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PEDERNALES",
        "Contacto": "Mónica Muñoz",
        "Dirección": "Av. García Moreno y Calle Pedernales - Junto a Aki Pedernales",
        "Teléfono": "989113061",
    },
    {
        "Nombre de Tienda": "Aeropostale - Península",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PENINSULA",
        "Contacto": "Kenny Bohorquez",
        "Dirección": "Av. Carlos Espinosa y Av. Central CC Paseo Shopping La Peninsula",
        "Teléfono": "997432684",
    },
    {
        "Nombre de Tienda": "Aeropostale - Playas",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PLAYAS",
        "Contacto": "Steven Ortiz",
        "Dirección": "Av. General Villamil - Paseo Shoping Playas",
        "Teléfono": "991871477",
    },
    {
        "Nombre de Tienda": "Aeropostale - Portoviejo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PORTOVIEJO",
        "Contacto": "Gissel Loor",
        "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo",
        "Teléfono": "963683962",
    },
    {
        "Nombre de Tienda": "Aeropostale - Rio Centro Norte",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Doris Zambrano",
        "Dirección": "Av. Francisco de Orellana y Urb. Alcance CC Riocentro Norte",
        "Teléfono": "969705137",
    },
    {
        "Nombre de Tienda": "Aeropostale - San Luis",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUITO",
        "Contacto": "Karina Proaño",
        "Dirección": "Av. General Rumiñahui y Av. San Luis - CC San Luis Shoping",
        "Teléfono": "991879974",
    },
    {
        "Nombre de Tienda": "Aeropostale - Santo Domingo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "SANTO DOMINGO",
        "Contacto": "Mateo Fruto",
        "Dirección": "Av. Abraham Calazacón y Av. Quito - Paseo Shoping Santo Domingo",
        "Teléfono": "967593039",
    },
    {
        "Nombre de Tienda": "Aeropostale - Cayambe",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "CAYAMBE",
        "Contacto": "Celeste Contreras",
        "Dirección": "Panamericana norte y camino del sol CC Altos de Cayambe",
        "Teléfono": "995414136",
    },
    {
        "Nombre de Tienda": "Aeropostale Quevedo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "QUEVEDO",
        "Contacto": "Dayana León",
        "Dirección": "Av. Quito, frente a la policia Nacional CC Paseo Shopping Quevedo",
        "Teléfono": "981398074",
    },
    {
        "Nombre de Tienda": "Price Club - Portoviejo",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "PORTOVIEJO",
        "Contacto": "Dayana Merchan",
        "Dirección": "Jorge Washington entre Av. América y E30 CC Paseo Shopping Portoviejo",
        "Teléfono": "959877997",
    },
    {
        "Nombre de Tienda": "Price Club - Machala",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "MACHALA",
        "Contacto": "Yuleysi Delgado",
        "Dirección": "AV. 25 de Junio CC Oro Plaza",
        "Teléfono": "988087085",
    },
    {
        "Nombre de Tienda": "Price Club - Guayaquil",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "GUAYAQUIL",
        "Contacto": "Angie Delgado",
        "Dirección": "Pedro Carbo S/N y Luque junto a almacenes Estuardo Sánchez",
        "Teléfono": "999085369",
    },
    {
        "Nombre de Tienda": "Price Club - Ibarra",
        "Empresa": "Aeropostale",
        "Origen": "MATRIZ",
        "Destino": "IBARRA",
        "Contacto": "Silvia Urcuango",
        "Dirección": "Av. Victor Gómez Jurado y Rodrigo Miño junto a la cancha La Bombonera",
        "Teléfono": "982649058",
    },
]

USERS_DB = {
    "admin": {
        "password": hashlib.sha256("wilo3161".encode()).hexdigest(),
        "role": "Administrador",
        "name": "Administrador General",
        "email": "admin@aeropostale.com",
        "avatar": "👑",
    },
    "logistica": {
        "password": hashlib.sha256("log123".encode()).hexdigest(),
        "role": "Logística",
        "name": "Coordinador Logístico",
        "email": "logistica@aeropostale.com",
        "avatar": "🚚",
    },
    "ventas": {
        "password": hashlib.sha256("ven123".encode()).hexdigest(),
        "role": "Ventas",
        "name": "Ejecutivo de Ventas",
        "email": "ventas@aeropostale.com",
        "avatar": "💼",
    },
    "bodega": {
        "password": hashlib.sha256("bod123".encode()).hexdigest(),
        "role": "Bodega",
        "name": "Supervisor de Bodega",
        "email": "bodega@aeropostale.com",
        "avatar": "📦",
    },
}

# Palabras clave para clasificación en dashboard logístico
PRICE_KEYWORDS = ['PRICE', 'OIL', 'CITY MALL']
WEB_KEYWORDS = ['WEB', 'TIENDA MOVIL', 'MOVIL']
FALLAS_KEYWORDS = ['FALLAS']
VENTAS_MAYOR_KEYWORDS = ['MAYOR', 'MAYORISTA']

TIENDAS_REGULARES_LISTA = [
    'AERO CCI', 'AERO DAULE', 'AERO LAGO AGRIO', 'AERO MALL DEL RIO GYE',
    'AERO PLAYAS', 'AEROPOSTALE 6 DE DICIEMBRE', 'AEROPOSTALE BOMBOLI',
    'AEROPOSTALE CAYAMBE', 'AEROPOSTALE EL COCA', 'AEROPOSTALE PASAJE',
    'AEROPOSTALE PEDERNALES', 'AMBATO', 'BABAHOYO', 'BAHIA DE CARAQUEZ',
    'CARAPUNGO', 'CEIBOS', 'CONDADO SHOPPING', 'CUENCA', 'DURAN',
    'LA PLAZA SHOPPING', 'MACHALA', 'MAL DEL SUR', 'MALL DEL PACIFICO',
    'MALL DEL SOL', 'MANTA', 'MILAGRO', 'MULTIPLAZA RIOBAMBA', 'PASEO AMBATO',
    'PENINSULA', 'PORTOVIEJO', 'QUEVEDO', 'RIOBAMBA', 'RIOCENTRO EL DORADO',
    'RIOCENTRO NORTE', 'SAN LUIS', 'SANTO DOMINGO'
]

CATEGORIAS_TRANSFERENCIA = {
    'Price Club': {'icon': '🏬', 'color': '#0033A0'},
    'Tiendas': {'icon': '🏪', 'color': '#E4002B'},
    'Ventas por Mayor': {'icon': '🏭', 'color': '#10B981'},
    'Tienda Web': {'icon': '💻', 'color': '#8B5CF6'},
    'Fallas': {'icon': '⚠️', 'color': '#F59E0B'},
    'Fundas': {'icon': '📦', 'color': '#EC4899'}
}

# ==============================================================================
# FUNCIONES AUXILIARES GENERALES
# ==============================================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(str(password).encode()).hexdigest()

def extraer_entero(val) -> int:
    if pd.isna(val):
        return 0
    s = str(val).replace(',', '')
    match = re.search(r'\d+', s)
    return int(match.group()) if match else 0

def normalizar_texto(texto) -> str:
    if pd.isna(texto) or texto == "":
        return ""
    texto = str(texto)
    try:
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    except Exception:
        texto = texto.upper()
    texto = re.sub(r"[^A-Za-z0-9\s]", " ", texto.upper())
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def procesar_subtotal(valor) -> float:
    if pd.isna(valor):
        return 0.0
    try:
        if isinstance(valor, (int, float, np.number)):
            return float(valor)
        valor_str = str(valor).strip()
        valor_str = re.sub(r"[^\d.,-]", "", valor_str)
        if "," in valor_str and "." in valor_str:
            if valor_str.rfind(",") > valor_str.rfind("."):
                valor_str = valor_str.replace(".", "").replace(",", ".")
            else:
                valor_str = valor_str.replace(",", "")
        elif "," in valor_str:
            valor_str = valor_str.replace(",", ".")
        return float(valor_str) if valor_str else 0.0
    except Exception:
        return 0.0

def obtener_columna_piezas(df: pd.DataFrame) -> Optional[str]:
    posibles = ["PIEZAS", "CANTIDAD", "UNIDADES", "QTY", "CANT", "PZS", "BULTOS"]
    for col in df.columns:
        col_upper = str(col).upper()
        if any(p in col_upper for p in posibles):
            return col
    return None

def obtener_columna_fecha(df: pd.DataFrame) -> Optional[str]:
    posibles = ["FECHA", "FECHA ING", "FECHA INGRESO", "FECHA CREACION", "FECHA_ING", "FECHA_CREACION"]
    for col in df.columns:
        col_upper = str(col).upper()
        if any(p in col_upper for p in posibles):
            return col
    return None

def identificar_tipo_tienda(nombre) -> str:
    if pd.isna(nombre) or nombre == "":
        return "DESCONOCIDO"
    nombre_upper = normalizar_texto(nombre)
    if "JOFRE" in nombre_upper and "SANTANA" in nombre_upper:
        return "VENTAS AL POR MAYOR"
    nombres_personales = ["ROCIO", "ALEJANDRA", "ANGELICA", "DELGADO", "CRUZ", "LILIANA", "SALAZAR", "RICARDO", "SANCHEZ", "JAZMIN", "ALVARADO", "MELISSA", "CHAVEZ", "KARLA", "SORIANO", "ESTEFANIA", "GUALPA", "MARIA", "JESSICA", "PEREZ", "LOYO"]
    palabras = nombre_upper.split()
    for p in palabras:
        if len(p) > 2 and p in nombres_personales:
            return "VENTA WEB"
    patrones_fisicas = ["LOCAL", "AEROPOSTALE", "MALL", "PLAZA", "SHOPPING", "CENTRO COMERCIAL", "CC", "C.C", "TIENDA", "SUCURSAL", "PRICE", "CLUB", "DORADO", "CIUDAD", "RIOCENTRO", "PASEO", "PORTAL", "SOL", "CONDADO", "CITY", "CEIBOS", "IBARRA", "MATRIZ", "BODEGA", "FASHION", "GYE", "QUITO", "MACHALA", "PORTOVIEJO", "BABAHOYO", "MANTA", "AMBATO", "CUENCA", "ALMACEN", "PRATI"]
    for patron in patrones_fisicas:
        if patron in nombre_upper:
            return "TIENDA FÍSICA"
    if len(palabras) >= 3 or any(len(p) > 3 for p in palabras):
        return "TIENDA FÍSICA"
    return "VENTA WEB"

def to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def add_back_button(key: str = "back"):
    if st.button("⬅️ Volver", key=key):
        if 'current_page' in st.session_state:
            st.session_state.current_page = "Inicio"
        st.rerun()

# ==============================================================================
# BASE DE DATOS (MongoDB con fallback local)
# ==============================================================================
class MockLocalDB:
    def _get_db(self):
        if 'local_database' not in st.session_state:
            st.session_state.local_database = {
                'users': [
                    {'id':1, 'username':'admin', 'password': hash_password('wilo3161'), 'role':'Administrador', 'name':'Administrador General'},
                    {'id':2, 'username':'logistica', 'password': hash_password('log123'), 'role':'Logística', 'name':'Coordinador Logístico'},
                    {'id':3, 'username':'ventas', 'password': hash_password('ven123'), 'role':'Ventas', 'name':'Ejecutivo de Ventas'},
                    {'id':4, 'username':'bodega', 'password': hash_password('bod123'), 'role':'Bodega', 'name':'Supervisor de Bodega'}
                ],
                'trabajadores': [],
                'kpis': self._generate_kpis_data()
            }
        return st.session_state.local_database

    def _generate_kpis_data(self):
        kpis = []
        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            kpis.append({
                "id": i,
                "fecha": date.strftime("%Y-%m-%d"),
                "produccion": np.random.randint(800, 1500),
                "eficiencia": np.random.uniform(85, 98),
                "alertas": np.random.randint(0, 5),
                "costos": np.random.uniform(5000, 15000),
            })
        return kpis

    def query(self, table_name):
        return self._get_db().get(table_name, [])

    def insert(self, table_name, data):
        db = self._get_db()
        if table_name not in db:
            db[table_name] = []
        if 'id' not in data:
            data['id'] = len(db[table_name]) + 1
        db[table_name].append(data)

    def delete(self, table_name, id):
        db = self._get_db()
        if table_name in db:
            db[table_name] = [item for item in db[table_name] if item.get('id') != id]

    def update(self, table_name, id, update_data):
        db = self._get_db()
        if table_name in db:
            for item in db[table_name]:
                if item.get('id') == id:
                    item.update(update_data)
                    return True
        return False

    def authenticate(self, username, password):
        users = self.query('users')
        input_hash = hash_password(password)
        for user in users:
            if user.get('username') == username and user.get('password') == input_hash:
                return user
        return None

# Intentar importar MongoDB
try:
    from database import mongo_db as local_db, inicializar_datos_base, MockLocalDBFallback
    inicializar_datos_base()
    print("✅ Usando MongoDB Atlas")
except ImportError as e:
    print(f"⚠️ MongoDB no disponible, usando MockLocalDB local: {e}")
    local_db = MockLocalDB()

# ==============================================================================
# INICIALIZACIÓN DE SESSION STATE
# ==============================================================================
def initialize_session_state():
    defaults = {
        "current_page": "Inicio",
        "module_data": {},
        "guias_registradas": [],
        "contador_guias": 1000,
        "qr_images": {},
        "logos": {},
        "gastos_datos": {
            "manifesto": None,
            "facturas": None,
            "resultado": None,
            "metricas": None,
            "resumen": None,
            "validacion": None,
            "guias_anuladas": None,
            "procesado": False,
        },
        "clasificacion_data": pd.DataFrame(),
        "clasificacion_loaded": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==============================================================================
# ESTILOS CSS
# ==============================================================================
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    .stApp { font-family: 'Montserrat', sans-serif; background-color: #0f172a; overflow-x: hidden; }
    .main-bg { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: radial-gradient(circle at 20% 50%, rgba(96, 165, 250, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%), radial-gradient(circle at 40% 80%, rgba(244, 114, 182, 0.1) 0%, transparent 50%), linear-gradient(135deg, #0f172a 0%, #1e293b 100%); z-index: -2; }
    .particles { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 0.3; }
    .gallery-container { padding: 40px 5% 20px 5%; text-align: center; max-width: 1400px; margin: 0 auto; }
    .brand-title { color: white; font-size: 3.8rem; font-weight: 900; letter-spacing: 18px; margin-bottom: 15px; text-transform: uppercase; background: linear-gradient(45deg, #60A5FA, #8B5CF6, #F472B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: titleGlow 3s ease-in-out infinite alternate; text-shadow: 0 0 30px rgba(96, 165, 250, 0.3); }
    @keyframes titleGlow { 0% { text-shadow: 0 0 20px rgba(96, 165, 250, 0.3); } 100% { text-shadow: 0 0 40px rgba(139, 92, 246, 0.4); } }
    .brand-subtitle { color: #94A3B8; font-size: 1.1rem; letter-spacing: 8px; margin-bottom: 60px; text-transform: uppercase; font-weight: 400; display: inline-block; }
    .brand-subtitle::after { content: ''; position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%); width: 100px; height: 2px; background: linear-gradient(90deg, transparent, #60A5FA, transparent); }
    .modules-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; padding: 0 15px; margin-bottom: 50px; }
    @media (max-width: 1200px) { .modules-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 768px) { .modules-grid { grid-template-columns: 1fr; } .brand-title { font-size: 2.8rem; letter-spacing: 12px; } }
    .module-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(20px) saturate(180%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; height: 200px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 25px 20px; position: relative; cursor: pointer; overflow: hidden; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); }
    .module-card:hover { transform: translateY(-10px) scale(1.03); border-color: rgba(96, 165, 250, 0.3); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(96, 165, 250, 0.1); }
    .card-icon { font-size: 3.5rem; margin-bottom: 20px; transition: all 0.4s ease; }
    .module-card:hover .card-icon { transform: scale(1.3) rotate(10deg); filter: drop-shadow(0 5px 15px rgba(96, 165, 250, 0.4)); }
    .card-title { color: white; font-size: 1.3rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; text-align: center; margin-bottom: 8px; }
    .card-description { color: #CBD5E1; font-size: 0.9rem; text-align: center; opacity: 0.8; line-height: 1.5; }
    .module-header { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 3rem 2rem; border-radius: 24px; margin: 20px 0 40px 0; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05); }
    .header-title { font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 15px; }
    .header-icon { font-size: 2.8rem; background: linear-gradient(45deg, #60A5FA, #F472B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .header-text { background: linear-gradient(45deg, #60A5FA, #F472B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .module-content { margin-top: 30px; padding: 0 10px; }
    .stat-card { background: rgba(30, 41, 59, 0.8); border-radius: 16px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); transition: all 0.3s ease; }
    .stat-card:hover { transform: translateY(-5px); border-color: #60A5FA; box-shadow: 0 10px 25px rgba(96, 165, 250, 0.2); }
    .card-blue { border-left: 4px solid #60A5FA; }
    .card-green { border-left: 4px solid #10B981; }
    .card-red { border-left: 4px solid #EF4444; }
    .card-purple { border-left: 4px solid #8B5CF6; }
    .stat-icon { font-size: 2rem; margin-bottom: 10px; }
    .stat-title { color: #CBD5E1; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .stat-value { color: white; font-size: 2rem; font-weight: 800; margin-bottom: 5px; }
    .stat-change { font-size: 0.85rem; font-weight: 600; padding: 4px 8px; border-radius: 12px; display: inline-block; }
    .positive { background: rgba(16, 185, 129, 0.2); color: #10B981; }
    .negative { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
    .stButton > button { background: linear-gradient(135deg, #60A5FA, #8B5CF6) !important; color: white !important; border: none !important; border-radius: 12px !important; font-weight: 600 !important; transition: all 0.3s !important; box-shadow: 0 8px 25px rgba(96, 165, 250, 0.3); }
    .stButton > button:hover { transform: translateY(-3px) !important; box-shadow: 0 12px 30px rgba(96, 165, 250, 0.4) !important; background: linear-gradient(135deg, #8B5CF6, #F472B6) !important; }
    .app-footer { text-align: center; padding: 40px 20px; margin-top: 60px; color: #64748B; font-size: 0.9rem; border-top: 1px solid rgba(255, 255, 255, 0.1); background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); }
    </style>
    <div class="main-bg"></div>
    <div class="particles"></div>
    """, unsafe_allow_html=True)

# ==============================================================================
# AUTENTICACIÓN
# ==============================================================================
def check_password():
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return True

    st.markdown("""
    <style>
    @keyframes gradientBg { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .stApp { background: linear-gradient(-45deg, #020617, #0f172a, #1e1b4b, #0f172a); background-size: 400% 400%; animation: gradientBg 15s ease infinite; }
    .login-container { max-width: 380px; margin: 5vh auto; padding: 40px 30px; background: rgba(15, 23, 42, 0.45); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; box-shadow: 0 30px 40px rgba(0, 0, 0, 0.4); text-align: center; }
    .login-brand .main { font-size: 2.2rem; font-weight: 900; background: linear-gradient(to right, #60A5FA, #c084fc, #60A5FA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .login-brand .sub { font-size: 0.85rem; color: #94a3b8; letter-spacing: 3px; text-transform: uppercase; }
    .login-title { font-size: 1.15rem; font-weight: 600; color: #f8fafc; margin-bottom: 25px; }
    div[data-testid="stTextInput"] > div > div { background: rgba(30, 41, 59, 0.5) !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 12px !important; }
    .stButton > button { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important; border: none !important; border-radius: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-brand"><div class="main">AEROPOSTALE</div><div class="sub">ERP CONTROL TOTAL</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">INICIAR SESIÓN</div>', unsafe_allow_html=True)

        username = st.text_input("Usuario", placeholder="Nombre de usuario...", key="login_user", label_visibility="collapsed")
        password = st.text_input("Contraseña", placeholder="Contraseña segura...", type="password", key="login_pass", label_visibility="collapsed")
        remember = st.checkbox("Recordarme", key="remember_me")
        login_btn = st.button("Ingresar Seguro →", use_container_width=True, type="primary")
        st.markdown('<div class="login-version">v2.1.0</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if login_btn:
            # Autenticación con MongoDB primero
            try:
                user_data = local_db.authenticate(username, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = user_data.get("role", "Usuario")
                    st.session_state.user_name = user_data.get("name", username)
                    if remember:
                        st.session_state.remember_username = username
                    st.rerun()
            except Exception:
                pass

            # Fallback a USERS_DB
            if username in USERS_DB:
                if USERS_DB[username]["password"] == hash_password(password):
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

def show_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 Inicio", use_container_width=True):
            st.session_state.current_page = "Inicio"
            st.rerun()
    with col2:
        st.markdown(f"<div style='text-align: center; color: #CBD5E1;'><strong>{st.session_state.user_name}</strong> | {st.session_state.role} | {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Salir", use_container_width=True):
            for key in ["authenticated", "username", "role", "user_name"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    st.markdown("---")

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
        <h1 class="header-title"><span class="header-icon">{icon}</span> <span class="header-text">{title_text}</span></h1>
        <p style="color: #CBD5E1;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def show_main_page():
    load_css()
    st.markdown('<div class="gallery-container fade-in"><div class="brand-title">AEROPOSTALE</div><div class="brand-subtitle">Centro de Distribucion Ecuador | ERP</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="modules-grid fade-in">', unsafe_allow_html=True)

    all_modules = [
        {"icon": "📊", "title": "Dashboard KPIs", "description": "Dashboard en tiempo real con metricas operativas", "key": "dashboard_kpis"},
        {"icon": "💰", "title": "Reconciliacion", "description": "Conciliacion financiera y analisis de facturas", "key": "reconciliacion_v8"},
        {"icon": "📧", "title": "Auditoria de Correos", "description": "Analisis inteligente de novedades por email", "key": "auditoria_correos"},
        {"icon": "📦", "title": "Dashboard Logistico", "description": "Control de transferencias y distribucion", "key": "dashboard_logistico"},
        {"icon": "👥", "title": "Gestion de Equipo", "description": "Administracion del personal del centro", "key": "gestion_equipo"},
        {"icon": "🚚", "title": "Generar Guias", "description": "Sistema de envios con seguimiento QR", "key": "generar_guias"},
        {"icon": "📋", "title": "Control de Inventario", "description": "Gestion de stock en tiempo real", "key": "control_inventario"},
        {"icon": "📈", "title": "Reportes Avanzados", "description": "Analisis y estadisticas ejecutivas", "key": "reportes_avanzados"},
        {"icon": "⚙️", "title": "Configuracion", "description": "Personalizacion del sistema ERP", "key": "configuracion"},
    ]

    role = st.session_state.role
    if role == "Bodega":
        modules = [m for m in all_modules if m["key"] in ["generar_guias", "control_inventario"]]
    else:
        modules = all_modules

    cols = st.columns(3)
    for idx, module in enumerate(modules):
        with cols[idx % 3]:
            create_module_card(module["icon"], module["title"], module["description"], module["key"])

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="app-footer"><p><strong>Sistema ERP v4.0</strong> • Desarrollado por Wilson Perez • Logistica & Sistemas</p><p style="font-size: 0.85rem; color: #94A3B8;">© 2024 AEROPOSTALE Ecuador • Todos los derechos reservados</p></div>', unsafe_allow_html=True)
    # ==============================================================================
# MÓDULO: DASHBOARD KPIs
# ==============================================================================
def show_dashboard_kpis():
    """Dashboard de KPIs - MEJORADO"""
    add_back_button(key="back_kpis")
    show_module_header(
        "📊 Dashboard de KPIs", "Metricas en tiempo real del Centro de Distribucion"
    )

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input(
            "📅 Fecha Inicio", datetime.now() - timedelta(days=30)
        )
    with col2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col3:
        st.selectbox(
            "📈 Tipo de Metrica", ["Produccion", "Eficiencia", "Costos", "Alertas"]
        )

    kpis_data = local_db.query("kpis")
    df_kpis = pd.DataFrame(kpis_data)

    if not df_kpis.empty:
        df_kpis["fecha"] = pd.to_datetime(df_kpis["fecha"])
        mask = (df_kpis["fecha"].dt.date >= fecha_inicio) & (
            df_kpis["fecha"].dt.date <= fecha_fin
        )
        df_filtered = df_kpis[mask]

        if not df_filtered.empty:
            st.markdown("<div class='stats-grid'>", unsafe_allow_html=True)
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)

            with col_k1:
                prod_prom = df_filtered["produccion"].mean()
                prod_tend = (
                    (
                        (
                            df_filtered["produccion"].iloc[-1]
                            - df_filtered["produccion"].iloc[0]
                        )
                        / df_filtered["produccion"].iloc[0]
                        * 100
                    )
                    if len(df_filtered) > 1
                    else 0
                )
                st.markdown(
                    f"""
                <div class='stat-card card-blue'>
                    <div class='stat-icon'>🏭</div>
                    <div class='stat-title'>Produccion Promedio</div>
                    <div class='stat-value'>{prod_prom:,.0f}</div>
                    <div class='stat-change {"positive" if prod_tend > 0 else "negative"}'>{"📈" if prod_tend > 0 else "📉"} {prod_tend:.1f}%</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col_k2:
                efic_prom = df_filtered["eficiencia"].mean()
                st.markdown(
                    f"""
                <div class='stat-card card-green'>
                    <div class='stat-icon'>⚡</div>
                    <div class='stat-title'>Eficiencia</div>
                    <div class='stat-value'>{efic_prom:.1f}%</div>
                    <div class='stat-change {"positive" if efic_prom > 90 else "warning"}'>{"Excelente" if efic_prom > 90 else "Mejorable"}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col_k3:
                alert_total = df_filtered["alertas"].sum()
                st.markdown(
                    f"""
                <div class='stat-card card-red'>
                    <div class='stat-icon'>🚨</div>
                    <div class='stat-title'>Alertas Totales</div>
                    <div class='stat-value'>{alert_total}</div>
                    <div class='stat-change {"negative" if alert_total > 10 else "positive"}'>{"Revisar" if alert_total > 10 else "Controlado"}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col_k4:
                costo_prom = df_filtered["costos"].mean()
                st.markdown(
                    f"""
                <div class='stat-card card-purple'>
                    <div class='stat-icon'>💰</div>
                    <div class='stat-title'>Costo Promedio</div>
                    <div class='stat-value'>${costo_prom:,.0f}</div>
                    <div class='stat-change'>Diario</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = px.line(
                df_filtered,
                x="fecha",
                y="produccion",
                title="Produccion Diaria",
                labels={"produccion": "Unidades", "fecha": "Fecha"},
                line_shape="spline",
            )
            fig.update_traces(line=dict(color="#0033A0", width=3))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig2 = px.bar(
                    df_filtered.tail(7),
                    x=df_filtered.tail(7)["fecha"].dt.strftime("%a"),
                    y="eficiencia",
                    title="Eficiencia Semanal",
                    color="eficiencia",
                    color_continuous_scale="Viridis",
                )
                st.plotly_chart(fig2, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_ch2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig3 = px.scatter(
                    df_filtered,
                    x="produccion",
                    y="costos",
                    title="Relacion Produccion vs Costos",
                    color="alertas",
                    size="eficiencia",
                    hover_data=["fecha"],
                )
                st.plotly_chart(fig3, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No hay datos para el rango de fechas seleccionado.")
    else:
        st.info("Cargando datos de KPIs...")

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# FUNCIONES AUXILIARES PARA RECONCILIACIÓN (GESTIÓN DE GASTOS)
# ==============================================================================
def cargar_archivo_local(uploaded_file, nombre):
    """Carga archivos Excel o CSV para el módulo de reconciliación"""
    try:
        if uploaded_file.name.endswith((".xlsx", ".xls")):
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
            st.sidebar.info(
                f"Hoja seleccionada automáticamente: {hoja_seleccionada}"
            )
            df = pd.read_excel(uploaded_file, sheet_name=hoja_seleccionada)
            st.sidebar.success(f"✓ {nombre}: {len(df):,} filas de Excel")
        elif uploaded_file.name.endswith(".csv"):
            encodings = ["utf-8", "latin-1", "cp1252", "ISO-8859-1"]
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    st.sidebar.success(
                        f"✓ {nombre}: {len(df):,} filas de CSV ({encoding})"
                    )
                    break
                except UnicodeDecodeError:
                    if encoding == encodings[-1]:
                        raise
                    continue
        else:
            st.sidebar.error(f"✗ Formato no soportado: {uploaded_file.name}")
            return None
        df = df.dropna(axis=1, how="all")
        df = df.dropna(how="all")
        if df.empty:
            st.sidebar.error(f"✗ {nombre}: Archivo vacío o sin datos válidos")
            return None
        return df
    except Exception as e:
        st.sidebar.error(f"✗ Error al cargar {nombre}: {str(e)}")
        return None


def procesar_gastos_reconciliacion(manifesto, facturas, config):
    """Procesa y valida gastos por tienda usando solo DESTINATARIO del MANIFIESTO"""
    try:
        # 1. PREPARAR MANIFIESTO
        st.info("📦 Procesando manifiesto...")
        columnas_manifesto = manifesto.columns.tolist()

        # Buscar columna de guía en manifiesto
        col_guia_m = config["guia_m"]
        if col_guia_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if "GUIA" in str(col).upper() or "GUÍA" in str(col).upper():
                    col_guia_m = col
                    break
            if col_guia_m not in columnas_manifesto:
                raise ValueError(
                    f"No se encontró columna de guía en el manifiesto. Columnas disponibles: {columnas_manifesto}"
                )

        # Buscar columna de subtotal en manifiesto
        col_subtotal_m = config.get("subtotal_m", "")
        if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if (
                    "SUBT" in str(col).upper()
                    or "TOTAL" in str(col).upper()
                    or "VALOR" in str(col).upper()
                ):
                    col_subtotal_m = col
                    break
            if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
                col_subtotal_m = columnas_manifesto[-1]  # Última columna como fallback

        # Buscar columna de ciudad en manifiesto
        col_ciudad_m = config.get("ciudad_destino", "")
        if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if (
                    "CIUDAD" in str(col).upper()
                    or "DES" in str(col).upper()
                    or "DESTINO" in str(col).upper()
                ):
                    col_ciudad_m = col
                    break
            if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
                col_ciudad_m = "CIUDAD"
                manifesto[col_ciudad_m] = "DESCONOCIDA"

        # Buscar columna de PIEZAS en el manifiesto
        col_piezas_m = obtener_columna_piezas(manifesto)
        if col_piezas_m:
            st.info(f"✓ Columna de piezas detectada: {col_piezas_m}")
        else:
            st.warning(
                "⚠ No se encontró columna de número de piezas. Se usará valor por defecto de 1 por guía."
            )
            manifesto["PIEZAS"] = 1
            col_piezas_m = "PIEZAS"

        # Buscar columna de FECHA en el manifiesto
        col_fecha_m = obtener_columna_fecha(manifesto)
        if col_fecha_m:
            st.info(f"✓ Columna de fecha detectada: {col_fecha_m}")
        else:
            st.warning(
                "⚠ No se encontró columna de fecha. Se omitirá la fecha en los reportes."
            )

        # Buscar columna de DESTINATARIO en el MANIFIESTO
        col_destinatario_m = None
        posibles_destinatario = [
            "DESTINATARIO",
            "CONSIGNATARIO",
            "CLIENTE",
            "NOMBRE",
            "RAZON SOCIAL",
        ]
        for col in posibles_destinatario:
            if col in columnas_manifesto:
                col_destinatario_m = col
                break

        if not col_destinatario_m:
            for col in columnas_manifesto:
                col_upper = str(col).upper()
                if any(
                    palabra in col_upper
                    for palabra in ["DEST", "CONSIG", "CLIEN", "NOMB", "RAZON"]
                ):
                    col_destinatario_m = col
                    break

        if not col_destinatario_m:
            manifesto["DESTINATARIO_MANIFIESTO"] = "TIENDA " + manifesto[
                col_ciudad_m
            ].astype(str)
            col_destinatario_m = "DESTINATARIO_MANIFIESTO"

        # Incluir otras columnas importantes del manifiesto
        otras_columnas_importantes = []
        for col in manifesto.columns:
            col_upper = str(col).upper()
            if any(
                palabra in col_upper
                for palabra in [
                    "FECHA",
                    "ORIGEN",
                    "SERVICIO",
                    "TRANSPORTE",
                    "PESO",
                    "FLETE",
                ]
            ):
                otras_columnas_importantes.append(col)

        # Crear DataFrame del manifiesto con las columnas seleccionadas
        columnas_manifiesto = [
            col_guia_m,
            col_subtotal_m,
            col_ciudad_m,
            col_destinatario_m,
            col_piezas_m,
        ]
        if col_fecha_m:
            columnas_manifiesto.append(col_fecha_m)
        columnas_manifiesto += otras_columnas_importantes
        columnas_manifiesto = list(dict.fromkeys(columnas_manifiesto))
        df_m = manifesto[columnas_manifiesto].copy()

        # Estandarizar nombres de columnas
        df_m["GUIA"] = df_m[col_guia_m].astype(str).str.strip()
        df_m["SUBTOTAL_MANIFIESTO"] = df_m[col_subtotal_m].apply(procesar_subtotal)
        df_m["CIUDAD_MANIFIESTO"] = df_m[col_ciudad_m].fillna("DESCONOCIDA").astype(str)
        df_m["DESTINATARIO_MANIFIESTO"] = (
            df_m[col_destinatario_m].fillna("DESTINATARIO DESCONOCIDO").astype(str)
        )
        df_m["PIEZAS_MANIFIESTO"] = pd.to_numeric(
            df_m[col_piezas_m], errors="coerce"
        ).fillna(1)

        if col_fecha_m:
            try:
                df_m["FECHA_MANIFIESTO"] = pd.to_datetime(
                    df_m[col_fecha_m], errors="coerce"
                )
            except Exception:
                df_m["FECHA_MANIFIESTO"] = df_m[col_fecha_m].astype(str)

        df_m["GUIA_LIMPIA"] = df_m["GUIA"].str.upper()

        st.success(
            f"✓ Manifiesto procesado: {len(df_m):,} guías, {df_m['PIEZAS_MANIFIESTO'].sum():,.0f} piezas totales"
        )

    except Exception as e:
        st.error(f"Error al procesar manifiesto: {str(e)}")
        st.error(f"Columnas disponibles en manifiesto: {manifesto.columns.tolist()}")
        raise

    try:
        # 2. PREPARAR FACTURAS (solo GUÍA y SUBTOTAL)
        st.info("🧾 Procesando facturas...")
        columnas_facturas = facturas.columns.tolist()

        # Limpiar nombres de columna (quitar espacios, saltos de línea)
        facturas.columns = facturas.columns.str.strip().str.replace('\n', ' ').str.replace('\r', '')

        # Buscar columna de guía en facturas
        col_guia_f = config["guia_f"]
        # Asegurar que sea un string único
        if isinstance(col_guia_f, list):
            col_guia_f = col_guia_f[0]
        
        if col_guia_f not in columnas_facturas:
            for col in columnas_facturas:
                if "GUIA" in str(col).upper() or "GUÍA" in str(col).upper():
                    col_guia_f = col
                    break
            if col_guia_f not in columnas_facturas:
                raise ValueError(
                    f"No se encontró columna de guía en las facturas. Columnas disponibles: {columnas_facturas}"
                )

        # Buscar columna de subtotal en facturas
        col_subtotal_f = config.get("subtotal", "")
        if isinstance(col_subtotal_f, list):
            col_subtotal_f = col_subtotal_f[0]
        if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
            for col in columnas_facturas:
                if (
                    "SUBTOTAL" in str(col).upper()
                    or "TOTAL" in str(col).upper()
                    or "IMPORTE" in str(col).upper()
                    or "VALOR" in str(col).upper()
                ):
                    col_subtotal_f = col
                    break
            if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
                col_subtotal_f = columnas_facturas[-1]  # Última columna como fallback

        # Crear DataFrame de facturas
        # Asegurar que seleccionamos una Serie, no DataFrame
        df_f = facturas[[col_guia_f, col_subtotal_f]].copy()
        # Si por alguna razón tenemos multi-índice, resetear
        if isinstance(df_f.columns, pd.MultiIndex):
            df_f.columns = ['_'.join(col).strip() for col in df_f.columns.values]
            col_guia_f = df_f.columns[0]
            col_subtotal_f = df_f.columns[1]
        
        # Convertir a string y limpiar
        df_f["GUIA_FACTURA"] = df_f[col_guia_f].astype(str).str.strip()
        df_f["SUBTOTAL_FACTURA"] = df_f[col_subtotal_f].apply(procesar_subtotal)
        df_f["GUIA_LIMPIA"] = df_f["GUIA_FACTURA"].str.upper()

        st.success(f"✓ Facturas procesadas: {len(df_f):,} registros")

    except Exception as e:
        st.error(f"Error al procesar facturas: {str(e)}")
        st.error(f"Columnas disponibles en facturas: {facturas.columns.tolist()}")
        raise

    # ... (el resto de la función continúa igual: unir, métricas, etc.)
    # Nota: El resto del código de la función se mantiene idéntico desde "try: 3. UNIR DATOS POR GUÍA..."
    # Por brevedad, no lo copio aquí, pero asegúrate de que el resto de la función siga igual.

    try:
        # 3. UNIR DATOS POR GUÍA - LEFT JOIN (mantener TODAS las guías del manifiesto)
        st.info("🔗 Uniendo datos por guía...")
        df_completo = pd.merge(
            df_m,
            df_f[["GUIA_LIMPIA", "SUBTOTAL_FACTURA"]],
            on="GUIA_LIMPIA",
            how="left",
        )

        df_completo["DESTINATARIO"] = df_completo["DESTINATARIO_MANIFIESTO"]
        df_completo["CIUDAD"] = df_completo["CIUDAD_MANIFIESTO"]
        df_completo["PIEZAS"] = df_completo["PIEZAS_MANIFIESTO"]

        df_completo["ESTADO"] = df_completo["SUBTOTAL_FACTURA"].apply(
            lambda x: "FACTURADA" if pd.notna(x) and float(x) > 0 else "ANULADA"
        )
        df_completo["SUBTOTAL"] = df_completo["SUBTOTAL_FACTURA"].fillna(0)
        df_completo["DIFERENCIA"] = (
            df_completo["SUBTOTAL_MANIFIESTO"] - df_completo["SUBTOTAL"]
        )

        df_completo["TIPO"] = df_completo["DESTINATARIO"].apply(identificar_tipo_tienda)
        df_completo["NOMBRE_NORMALIZADO"] = df_completo["DESTINATARIO"].apply(
            normalizar_texto
        )

        def crear_grupo(fila):
            tipo = fila["TIPO"]
            nombre = fila["NOMBRE_NORMALIZADO"]
            ciudad = normalizar_texto(fila["CIUDAD"])
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
                    nombre_grupo = " ".join(palabras[: min(3, len(palabras))])
                    return f"{grupo_ciudad}{nombre_grupo}"
                else:
                    return f"{grupo_ciudad}TIENDA"
            else:
                return f"DESCONOCIDO - {nombre[:20]}"

        df_completo["GRUPO"] = df_completo.apply(crear_grupo, axis=1)

        guias_facturadas = df_completo[df_completo["ESTADO"] == "FACTURADA"].shape[0]
        guias_anuladas = df_completo[df_completo["ESTADO"] == "ANULADA"].shape[0]
        total_piezas = df_completo["PIEZAS"].sum()
        guias_anuladas_df = df_completo[df_completo["ESTADO"] == "ANULADA"].copy()

        st.success(f"✓ Datos unidos: {len(df_completo):,} registros")
        st.info(f"  • Guías facturadas: {guias_facturadas:,}")
        st.info(f"  • Guías anuladas: {guias_anuladas:,}")
        st.info(f"  • Piezas totales: {total_piezas:,}")

    except Exception as e:
        st.error(f"Error al unir datos: {str(e)}")
        raise

    try:
        # 4. CALCULAR MÉTRICAS POR GRUPO (solo guías FACTURADAS)
        st.info("📊 Calculando métricas por grupo...")
        df_facturadas = df_completo[df_completo["ESTADO"] == "FACTURADA"]

        metricas = (
            df_facturadas.groupby("GRUPO")
            .agg(
                GUIAS=("GUIA_LIMPIA", "count"),
                PIEZAS=("PIEZAS", "sum"),
                SUBTOTAL=("SUBTOTAL", "sum"),
                SUBTOTAL_MANIFIESTO=("SUBTOTAL_MANIFIESTO", "sum"),
                DIFERENCIA=("DIFERENCIA", "sum"),
                DESTINATARIOS=(
                    "DESTINATARIO",
                    lambda x: ", ".join(
                        sorted(set(str(d) for d in x if pd.notna(d) and str(d) != ""))[
                            :5
                        ]
                    ),
                ),
                CIUDADES=(
                    "CIUDAD",
                    lambda x: ", ".join(
                        sorted(set(str(c) for c in x if pd.notna(c) and str(c) != ""))[
                            :3
                        ]
                    ),
                ),
                TIPO=(
                    "TIPO",
                    lambda x: x.mode()[0] if not x.mode().empty else "DESCONOCIDO",
                ),
            )
            .reset_index()
        )

        total_general = metricas["SUBTOTAL"].sum()
        if total_general > 0:
            metricas["PORCENTAJE"] = (metricas["SUBTOTAL"] / total_general * 100).round(
                2
            )
            metricas["PROMEDIO_POR_PIEZA"] = (
                metricas["SUBTOTAL"] / metricas["PIEZAS"]
            ).round(2)
        else:
            metricas["PORCENTAJE"] = 0.0
            metricas["PROMEDIO_POR_PIEZA"] = 0.0

        metricas["PIEZAS_POR_GUIA"] = (metricas["PIEZAS"] / metricas["GUIAS"]).round(2)
        metricas = metricas.sort_values("SUBTOTAL", ascending=False)

        st.success(f"✓ Métricas calculadas: {len(metricas):,} grupos identificados")

    except Exception as e:
        st.error(f"Error al calcular métricas: {str(e)}")
        raise

    try:
        # 5. RESUMEN POR TIPO (solo guías FACTURADAS)
        st.info("📋 Generando resumen por tipo...")
        resumen = (
            df_facturadas.groupby("TIPO")
            .agg(
                TIENDAS=("GRUPO", "nunique"),
                GUIAS=("GUIA_LIMPIA", "count"),
                PIEZAS=("PIEZAS", "sum"),
                SUBTOTAL=("SUBTOTAL", "sum"),
            )
            .reset_index()
        )

        if total_general > 0:
            resumen["PORCENTAJE"] = (resumen["SUBTOTAL"] / total_general * 100).round(2)
        else:
            resumen["PORCENTAJE"] = 0.0

        resumen = resumen.sort_values("SUBTOTAL", ascending=False)
        st.success("✓ Resumen por tipo generado")

    except Exception as e:
        st.error(f"Error al calcular resumen: {str(e)}")
        raise

    try:
        # 6. VALIDACIÓN
        st.info("✅ Realizando validación...")
        total_manifiesto = df_completo["SUBTOTAL_MANIFIESTO"].sum()
        total_facturas = df_completo["SUBTOTAL"].sum()
        total_piezas_manifesto = df_completo["PIEZAS"].sum()

        validacion = {
            "total_manifiesto": total_manifiesto,
            "total_facturas": total_facturas,
            "diferencia": abs(total_manifiesto - total_facturas),
            "porcentaje": (
                abs(total_manifiesto - total_facturas) / total_manifiesto * 100
            )
            if total_manifiesto > 0
            else 0,
            "coincide": abs(total_manifiesto - total_facturas) < 0.01,
            "guias_procesadas": len(df_completo),
            "guias_facturadas": guias_facturadas,
            "guias_anuladas": guias_anuladas,
            "piezas_totales": total_piezas_manifesto,
            "grupos_identificados": len(metricas),
            "porcentaje_facturadas": (guias_facturadas / len(df_completo) * 100)
            if len(df_completo) > 0
            else 0,
            "porcentaje_anuladas": (guias_anuladas / len(df_completo) * 100)
            if len(df_completo) > 0
            else 0,
        }

        st.success("✓ Validación completada")

    except Exception as e:
        st.error(f"Error al realizar validación: {str(e)}")
        raise

    return df_completo, metricas, resumen, validacion, guias_anuladas_df


def generar_excel_con_formato_exacto(
    metricas_filt, resultado, guias_anuladas, manifesto_original, filtros_aplicados=None
):
    """
    Genera un archivo Excel con el formato exacto requerido:
    - Hoja "Reporte": Tabla dinámica con Etiquetas de fila y Suma de SUBTOTAL
    - Hoja "Tiendas": Métricas agrupadas por DESTINATARIO
    - Hoja "Guias Anuladas": Detalle de guías sin factura (incluye fecha)
    - Hoja "Detalle": Todas las guías con fecha y número de guía
    """
    try:
        output = BytesIO()
        wb = Workbook()

        # ============================================
        # HOJA 1: Reporte (Tabla dinámica)
        # ============================================
        ws1 = wb.active
        ws1.title = "Reporte"

        hoja1_data = metricas_filt[["GRUPO", "SUBTOTAL"]].copy()
        hoja1_data = hoja1_data.sort_values("GRUPO")

        ws1.append(["", ""])
        ws1.append(["", ""])
        ws1.append(["Etiquetas de fila", "Suma de SUBTOTAL"])

        for _, row in hoja1_data.iterrows():
            ws1.append([row["GRUPO"], row["SUBTOTAL"]])

        total_general = hoja1_data["SUBTOTAL"].sum()
        ws1.append(["Total general", total_general])

        for row in ws1.iter_rows(min_row=3, max_row=ws1.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )

        for cell in ws1[3]:
            cell.fill = PatternFill(
                start_color="366092", end_color="366092", fill_type="solid"
            )
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        for row in range(4, ws1.max_row + 1):
            ws1.cell(row=row, column=2).number_format = "#,##0.00"

        ws1.column_dimensions["A"].width = 50
        ws1.column_dimensions["B"].width = 20

        # ============================================
        # HOJA 2: Tiendas (Métricas por grupo)
        # ============================================
        ws2 = wb.create_sheet(title="Tiendas")

        columnas = [
            "GRUPO",
            "GUIAS",
            "PIEZAS",
            "SUBTOTAL",
            "DESTINATARIOS",
            "CIUDADES",
            "TIPO",
            "PORCENTAJE",
            "PROMEDIO_POR_PIEZA",
            "PIEZAS_POR_GUIA",
        ]

        ws2.append(columnas)

        for _, row in metricas_filt.iterrows():
            ws2.append(
                [
                    row["GRUPO"],
                    int(row["GUIAS"]),
                    int(row["PIEZAS"]),
                    row["SUBTOTAL"],
                    row["DESTINATARIOS"],
                    row["CIUDADES"],
                    row["TIPO"],
                    row["PORCENTAJE"],
                    row["PROMEDIO_POR_PIEZA"],
                    row["PIEZAS_POR_GUIA"],
                ]
            )

        ws2.append(["" for _ in range(len(columnas))])
        ultima_fila_datos = ws2.max_row - 1
        total_row = ["" for _ in range(len(columnas))]
        total_row[0] = "Total general"
        total_row[3] = f"=SUBTOTAL(109,D2:D{ultima_fila_datos})"
        ws2.append(total_row)

        for row in ws2.iter_rows(
            min_row=1, max_row=ws2.max_row, min_col=1, max_col=len(columnas)
        ):
            for cell in row:
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )
                if cell.column in [2, 3, 8, 9, 10]:
                    cell.alignment = Alignment(horizontal="right")
                else:
                    cell.alignment = Alignment(horizontal="left")

        for cell in ws2[1]:
            cell.fill = PatternFill(
                start_color="366092", end_color="366092", fill_type="solid"
            )
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        for row in range(2, ws2.max_row + 1):
            ws2.cell(row=row, column=4).number_format = "#,##0.00"
            ws2.cell(row=row, column=8).number_format = "0.00"
            ws2.cell(row=row, column=9).number_format = "0.00"
            ws2.cell(row=row, column=10).number_format = "0.00"

        for cell in ws2[ws2.max_row]:
            cell.font = Font(bold=True)
            if cell.column == 4:
                cell.number_format = "#,##0.00"

        anchos = [40, 10, 10, 15, 50, 20, 20, 15, 20, 20]
        for i, ancho in enumerate(anchos, 1):
            ws2.column_dimensions[get_column_letter(i)].width = ancho

        # ============================================
        # HOJA 3: Guias Anuladas (con fecha)
        # ============================================
        if not guias_anuladas.empty:
            ws3 = wb.create_sheet(title="Guias Anuladas")

            columnas_anuladas = []
            posibles_columnas = [
                "FECHA_MANIFIESTO",
                "GUIA",
                "ORIGEN",
                "GUIA2",
                "DESTINATARIO_MANIFIESTO",
                "SERVICIO",
                "TRANSPORTE",
                "PIEZAS_MANIFIESTO",
                "PESO",
                "FLETE",
                "SUBTOTAL_MANIFIESTO",
                "CIUDAD_MANIFIESTO",
                "ESTADO",
            ]

            for col in posibles_columnas:
                if col in guias_anuladas.columns:
                    columnas_anuladas.append(col)

            mapeo_nombres = {
                "FECHA_MANIFIESTO": "FECHA",
                "DESTINATARIO_MANIFIESTO": "DESTINATARIO",
                "PIEZAS_MANIFIESTO": "NUMERO DE PIEZAS",
                "SUBTOTAL_MANIFIESTO": "SUBTOTAL",
                "CIUDAD_MANIFIESTO": "CIUDAD",
            }

            columnas_anuladas = [
                mapeo_nombres.get(col, col) for col in columnas_anuladas
            ]

            ws3.append(columnas_anuladas)

            for _, row in guias_anuladas.iterrows():
                fila_data = []
                for col_original in posibles_columnas:
                    if col_original in guias_anuladas.columns:
                        valor = row[col_original]
                        if col_original == "FECHA_MANIFIESTO":
                            if pd.notna(valor) and hasattr(valor, "strftime"):
                                fila_data.append(valor.strftime("%d/%m/%Y %H:%M"))
                            else:
                                fila_data.append(valor if pd.notna(valor) else "")
                        elif col_original == "DESTINATARIO_MANIFIESTO":
                            fila_data.append(valor if pd.notna(valor) else "")
                        elif col_original == "PIEZAS_MANIFIESTO":
                            fila_data.append(int(valor) if pd.notna(valor) else 0)
                        elif col_original == "SUBTOTAL_MANIFIESTO":
                            fila_data.append(float(valor) if pd.notna(valor) else 0.0)
                        else:
                            fila_data.append(valor if pd.notna(valor) else "")
                ws3.append(fila_data)

            ws3.append(["" for _ in range(len(columnas_anuladas))])
            total_row = ["" for _ in range(len(columnas_anuladas))]
            total_row[0] = "Total guías anuladas"
            if "NUMERO DE PIEZAS" in columnas_anuladas:
                idx_piezas = columnas_anuladas.index("NUMERO DE PIEZAS") + 1
                total_row[idx_piezas - 1] = (
                    f"=SUBTOTAL(109,{get_column_letter(idx_piezas)}2:{get_column_letter(idx_piezas)}{ws3.max_row - 1})"
                )
            if "SUBTOTAL" in columnas_anuladas:
                idx_subtotal = columnas_anuladas.index("SUBTOTAL") + 1
                total_row[idx_subtotal - 1] = (
                    f"=SUBTOTAL(109,{get_column_letter(idx_subtotal)}2:{get_column_letter(idx_subtotal)}{ws3.max_row - 1})"
                )
            ws3.append(total_row)

            for row in ws3.iter_rows(
                min_row=1,
                max_row=ws3.max_row,
                min_col=1,
                max_col=len(columnas_anuladas),
            ):
                for cell in row:
                    cell.border = Border(
                        left=Side(style="thin"),
                        right=Side(style="thin"),
                        top=Side(style="thin"),
                        bottom=Side(style="thin"),
                    )

            for cell in ws3[1]:
                cell.fill = PatternFill(
                    start_color="FF0000", end_color="FF0000", fill_type="solid"
                )
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")

            for row in range(2, ws3.max_row + 1):
                if "NUMERO DE PIEZAS" in columnas_anuladas:
                    col_idx = columnas_anuladas.index("NUMERO DE PIEZAS") + 1
                    ws3.cell(row=row, column=col_idx).number_format = "0"
                if "SUBTOTAL" in columnas_anuladas:
                    col_idx = columnas_anuladas.index("SUBTOTAL") + 1
                    ws3.cell(row=row, column=col_idx).number_format = "#,##0.00"

            anchos_anuladas = [18, 15, 15, 20, 15, 40, 15, 15, 15, 10, 10, 15, 20, 15]
            for i, ancho in enumerate(anchos_anuladas[: len(columnas_anuladas)]):
                ws3.column_dimensions[get_column_letter(i + 1)].width = ancho

        # ============================================
        # HOJA 4: Detalle (Todas las guías con fecha)
        # ============================================
        ws4 = wb.create_sheet(title="Detalle")

        columnas_detalle = []
        if "FECHA_MANIFIESTO" in resultado.columns:
            columnas_detalle.append("FECHA_MANIFIESTO")
        columnas_detalle += [
            "GUIA",
            "ESTADO",
            "GRUPO",
            "DESTINATARIO",
            "CIUDAD",
            "PIEZAS",
            "SUBTOTAL_MANIFIESTO",
            "SUBTOTAL",
            "DIFERENCIA",
            "TIPO",
        ]

        columnas_detalle = [col for col in columnas_detalle if col in resultado.columns]
        detalle_df = resultado[columnas_detalle].copy()

        mapeo_detalle = {
            "FECHA_MANIFIESTO": "FECHA",
            "GUIA": "GUIA",
            "ESTADO": "ESTADO",
            "GRUPO": "GRUPO",
            "DESTINATARIO": "DESTINATARIO",
            "CIUDAD": "CIUDAD",
            "PIEZAS": "PIEZAS",
            "SUBTOTAL_MANIFIESTO": "SUBTOTAL MANIFIESTO",
            "SUBTOTAL": "SUBTOTAL FACTURA",
            "DIFERENCIA": "DIFERENCIA",
            "TIPO": "TIPO",
        }
        detalle_df = detalle_df.rename(
            columns={k: v for k, v in mapeo_detalle.items() if k in detalle_df.columns}
        )

        ws4.append(list(detalle_df.columns))

        for _, row in detalle_df.iterrows():
            fila_data = []
            for col in detalle_df.columns:
                valor = row[col]
                if col == "FECHA" and pd.notna(valor) and hasattr(valor, "strftime"):
                    fila_data.append(valor.strftime("%d/%m/%Y %H:%M"))
                elif col in ["PIEZAS"]:
                    fila_data.append(int(valor) if pd.notna(valor) else 0)
                elif col in ["SUBTOTAL MANIFIESTO", "SUBTOTAL FACTURA", "DIFERENCIA"]:
                    fila_data.append(float(valor) if pd.notna(valor) else 0.0)
                else:
                    fila_data.append(valor if pd.notna(valor) else "")
            ws4.append(fila_data)

        for row in ws4.iter_rows(
            min_row=1, max_row=ws4.max_row, min_col=1, max_col=len(detalle_df.columns)
        ):
            for cell in row:
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin"),
                )

        for cell in ws4[1]:
            cell.fill = PatternFill(
                start_color="366092", end_color="366092", fill_type="solid"
            )
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")

        for row in range(2, ws4.max_row + 1):
            for col_idx, col_name in enumerate(detalle_df.columns, 1):
                if col_name in ["PIEZAS"]:
                    ws4.cell(row=row, column=col_idx).number_format = "0"
                elif col_name in [
                    "SUBTOTAL MANIFIESTO",
                    "SUBTOTAL FACTURA",
                    "DIFERENCIA",
                ]:
                    ws4.cell(row=row, column=col_idx).number_format = "#,##0.00"

        anchos_detalle = [20, 15, 12, 40, 30, 20, 10, 15, 15, 15, 20]
        for i, ancho in enumerate(anchos_detalle[: len(detalle_df.columns)]):
            ws4.column_dimensions[get_column_letter(i + 1)].width = ancho

        # ============================================
        # HOJA 5: Filtros Aplicados (opcional)
        # ============================================
        if filtros_aplicados:
            ws5 = wb.create_sheet(title="Filtros Aplicados")
            ws5.append(["Filtro", "Valor"])
            for filtro, valor in filtros_aplicados.items():
                ws5.append([filtro, str(valor)])

            for row in ws5.iter_rows(
                min_row=1, max_row=ws5.max_row, min_col=1, max_col=2
            ):
                for cell in row:
                    cell.border = Border(
                        left=Side(style="thin"),
                        right=Side(style="thin"),
                        top=Side(style="thin"),
                        bottom=Side(style="thin"),
                    )

            for cell in ws5[1]:
                cell.fill = PatternFill(
                    start_color="366092", end_color="366092", fill_type="solid"
                )
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")

            ws5.column_dimensions["A"].width = 30
            ws5.column_dimensions["B"].width = 50

        wb.save(output)
        output.seek(0)
        return output

    except Exception as e:
        st.error(f"Error al generar Excel con formato: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def generar_pdf_reporte(metricas, resumen, validacion, filtros_aplicados=None):
    """Genera un PDF con el reporte ejecutivo"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdf_path = tmp_file.name

        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            "CustomSubtitle", parent=styles["Heading2"], fontSize=12, spaceAfter=6
        )
        normal_style = styles["Normal"]

        elements.append(
            Paragraph("REPORTE EJECUTIVO - GESTIÓN DE GASTOS POR TIENDA", title_style)
        )
        elements.append(
            Paragraph(
                f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                normal_style,
            )
        )
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("MÉTRICAS PRINCIPALES", subtitle_style))
        metricas_data = [
            ["Total Facturado", f"${validacion['total_facturas']:,.2f}"],
            ["Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}"],
            [
                "Diferencia",
                f"${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%)",
            ],
            ["Guías Procesadas", f"{validacion['guias_procesadas']:,}"],
            [
                "Guías Facturadas",
                f"{validacion['guias_facturadas']:,} ({validacion['porcentaje_facturadas']:.1f}%)",
            ],
            [
                "Guías Anuladas",
                f"{validacion['guias_anuladas']:,} ({validacion['porcentaje_anuladas']:.1f}%)",
            ],
            ["Piezas Totales", f"{validacion['piezas_totales']:,}"],
            ["Grupos Identificados", f"{validacion['grupos_identificados']:,}"],
        ]

        metricas_table = Table(metricas_data, colWidths=[200, 150])
        metricas_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.append(metricas_table)
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("RESUMEN POR TIPO DE TIENDA", subtitle_style))
        if not resumen.empty:
            resumen_data = [["TIPO", "TIENDAS", "GUÍAS", "PIEZAS", "SUBTOTAL", "%"]]
            for _, row in resumen.iterrows():
                resumen_data.append(
                    [
                        row["TIPO"],
                        str(int(row["TIENDAS"])),
                        str(int(row["GUIAS"])),
                        str(int(row["PIEZAS"])),
                        f"${row['SUBTOTAL']:,.2f}",
                        f"{row['PORCENTAJE']:.2f}%",
                    ]
                )

            resumen_table = Table(resumen_data, colWidths=[120, 80, 80, 80, 100, 80])
            resumen_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(resumen_table)

        elements.append(Spacer(1, 20))

        elements.append(Paragraph("TOP 15 GRUPOS POR GASTO", subtitle_style))
        if not metricas.empty:
            top_15 = metricas.head(15)
            grupos_data = [["GRUPO", "GUÍAS", "PIEZAS", "SUBTOTAL", "%", "PROM/PIEZA"]]
            for _, row in top_15.iterrows():
                grupos_data.append(
                    [
                        row["GRUPO"][:30] + "..."
                        if len(row["GRUPO"]) > 30
                        else row["GRUPO"],
                        str(int(row["GUIAS"])),
                        str(int(row["PIEZAS"])),
                        f"${row['SUBTOTAL']:,.2f}",
                        f"{row['PORCENTAJE']:.2f}%",
                        f"${row['PROMEDIO_POR_PIEZA']:,.2f}",
                    ]
                )

            grupos_table = Table(grupos_data, colWidths=[150, 60, 60, 90, 60, 80])
            grupos_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(grupos_table)

        elements.append(Spacer(1, 20))

        elements.append(Paragraph("ANÁLISIS EJECUTIVO", subtitle_style))
        analisis_text = f"""
        <b>Validación:</b> {"✅ COINCIDENCIA EXACTA" if validacion["coincide"] else "⚠ CON DIFERENCIAS"}<br/>
        <b>Facturación:</b> {validacion["porcentaje_facturadas"]:.1f}% de guías facturadas ({validacion["guias_facturadas"]:,} guías)<br/>
        <b>Anulaciones:</b> {validacion["porcentaje_anuladas"]:.1f}% de guías anuladas ({validacion["guias_anuladas"]:,} guías)<br/>
        <b>Distribución:</b> {resumen.iloc[0]["TIPO"] if not resumen.empty else "N/A"} representa el {resumen.iloc[0]["PORCENTAJE"] if not resumen.empty else 0:.1f}% del total facturado<br/>
        <b>Eficiencia:</b> Promedio de {validacion["piezas_totales"] / validacion["guias_procesadas"]:.1f} piezas por guía<br/>
        <b>Recomendación:</b> {"Revisar guías anuladas para optimizar facturación" if validacion["guias_anuladas"] > 0 else "Proceso de facturación eficiente"}
        """
        elements.append(Paragraph(analisis_text, normal_style))

        doc.build(elements)
        return pdf_path

    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None
    # ==============================================================================
# MÓDULO: RECONCILIACIÓN (GESTIÓN DE GASTOS POR TIENDA)
# ==============================================================================
def show_reconciliacion_v8():
    """Modulo de reconciliacion financiera y gestion de gastos por tienda"""
    add_back_button(key="back_recon")
    show_module_header(
        "💰 Gestión de Gastos por Tienda",
        "Conciliación financiera y análisis de facturas",
    )

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    # Inicializar datos del módulo en session_state si no existen
    if "gastos_datos" not in st.session_state:
        st.session_state.gastos_datos = {
            "manifesto": None,
            "facturas": None,
            "resultado": None,
            "metricas": None,
            "resumen": None,
            "validacion": None,
            "guias_anuladas": None,
            "procesado": False,
        }

    # --- Sidebar para carga de archivos ---
    with st.sidebar:
        st.header("📁 Carga de Archivos")
        st.markdown("**Formatos soportados:** Excel (.xlsx, .xls) y CSV")

        uploaded_manifesto = st.file_uploader(
            "Manifiesto (con DESTINATARIO y PIEZAS)",
            type=["csv", "xlsx", "xls"],
            key="manifesto_upload",
        )

        uploaded_facturas = st.file_uploader(
            "Facturas (solo GUÍA y VALOR)",
            type=["csv", "xlsx", "xls"],
            key="facturas_upload",
        )

        if uploaded_manifesto and uploaded_facturas:
            if st.button(
                "📥 Cargar Archivos", type="primary", use_container_width=True
            ):
                with st.spinner("Cargando archivos..."):
                    manifesto = cargar_archivo_local(uploaded_manifesto, "Manifiesto")
                    facturas = cargar_archivo_local(uploaded_facturas, "Facturas")

                    if manifesto is not None and facturas is not None:
                        st.session_state.gastos_datos["manifesto"] = manifesto
                        st.session_state.gastos_datos["facturas"] = facturas

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Registros (Manifiesto)", f"{len(manifesto):,}")
                            st.caption(f"{len(manifesto.columns)} columnas")
                        with col2:
                            st.metric("Registros (Facturas)", f"{len(facturas):,}")
                            st.caption(f"{len(facturas.columns)} columnas")

    # --- Contenido principal ---
    datos = st.session_state.gastos_datos
    if datos["manifesto"] is not None:
        manifesto = datos["manifesto"]
        facturas = datos["facturas"]

        st.header("⚙️ Configuración de Procesamiento")
        st.subheader("🔍 Detección Automática de Columnas")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Manifiesto**")
            guia_opciones_m = [
                col
                for col in manifesto.columns
                if "GUIA" in str(col).upper() or "GUÍA" in str(col).upper()
            ]
            if not guia_opciones_m:
                guia_opciones_m = manifesto.columns.tolist()
            guia_m = st.selectbox(
                "Columna Guía",
                guia_opciones_m,
                index=0 if guia_opciones_m else 0,
                help="Columna que contiene el número de guía",
            )

            subtotal_opciones_m = [
                col
                for col in manifesto.columns
                if "SUBT" in str(col).upper()
                or "TOTAL" in str(col).upper()
                or "VALOR" in str(col).upper()
            ]
            if not subtotal_opciones_m:
                subtotal_opciones_m = manifesto.columns.tolist()
            subtotal_m = st.selectbox(
                "Columna Subtotal/Valor",
                subtotal_opciones_m,
                index=0 if subtotal_opciones_m else 0,
                help="Columna que contiene el valor en el manifiesto",
            )

            ciudad_opciones_m = [
                col
                for col in manifesto.columns
                if "CIUDAD" in str(col).upper()
                or "DES" in str(col).upper()
                or "DESTINO" in str(col).upper()
            ]
            if not ciudad_opciones_m:
                ciudad_opciones_m = manifesto.columns.tolist()
            ciudad_destino = st.selectbox(
                "Columna Ciudad Destino",
                ciudad_opciones_m,
                index=0 if ciudad_opciones_m else 0,
                help="Columna que contiene la ciudad de destino",
            )

            st.caption(
                "⚠ **IMPORTANTE:** Para agrupar gastos se usará SOLO el DESTINATARIO del manifiesto"
            )
            destinatario_opciones_m = [
                col
                for col in manifesto.columns
                if any(
                    palabra in str(col).upper()
                    for palabra in ["DEST", "CONSIG", "CLIEN", "NOMB", "RAZON"]
                )
            ]
            if destinatario_opciones_m:
                st.info(
                    f"Columnas de destinatario detectadas: {', '.join(destinatario_opciones_m)}"
                )

        with col2:
            st.write("**Facturas**")
            guia_opciones_f = [
                col
                for col in facturas.columns
                if "GUIA" in str(col).upper() or "GUÍA" in str(col).upper()
            ]
            if not guia_opciones_f:
                guia_opciones_f = facturas.columns.tolist()
            guia_f = st.selectbox(
                "Columna Guía (Facturas)",
                guia_opciones_f,
                index=0 if guia_opciones_f else 0,
                help="Columna que contiene el número de guía en las facturas",
            )

            subtotal_opciones_f = [
                col
                for col in facturas.columns
                if "SUBTOTAL" in str(col).upper()
                or "TOTAL" in str(col).upper()
                or "IMPORTE" in str(col).upper()
                or "VALOR" in str(col).upper()
            ]
            if not subtotal_opciones_f:
                subtotal_opciones_f = facturas.columns.tolist()
            subtotal_f = st.selectbox(
                "Columna Subtotal (Facturas)",
                subtotal_opciones_f,
                index=0 if subtotal_opciones_f else 0,
                help="Columna que contiene el monto REAL cobrado en las facturas",
            )

            if subtotal_f in facturas.columns:
                st.caption("Previsualización de valores de facturas:")
                valores = facturas[subtotal_f].dropna().head(3).tolist()
                for i, val in enumerate(valores, 1):
                    st.code(f"{i}. {val}")

        config = {
            "guia_m": guia_m,
            "subtotal_m": subtotal_m,
            "ciudad_destino": ciudad_destino,
            "guia_f": guia_f,
            "subtotal": subtotal_f,
        }

        if st.button(
            "🚀 Procesar Gastos por Tienda", type="primary", use_container_width=True
        ):
            with st.spinner("Procesando y validando datos..."):
                try:
                    resultado, metricas, resumen, validacion, guias_anuladas = (
                        procesar_gastos_reconciliacion(manifesto, facturas, config)
                    )

                    datos["resultado"] = resultado
                    datos["metricas"] = metricas
                    datos["resumen"] = resumen
                    datos["validacion"] = validacion
                    datos["guias_anuladas"] = guias_anuladas
                    datos["procesado"] = True

                    st.success("✅ Procesamiento completado exitosamente")

                    if validacion["coincide"]:
                        st.balloons()
                        st.success(
                            "✅ Validación exitosa: Los totales coinciden dentro del margen aceptable"
                        )
                    else:
                        st.warning(
                            f"⚠ Hay una diferencia de ${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%)"
                        )

                    st.info(f"""
                    🎯 **Resumen del procesamiento:**
                    - Guías totales procesadas: {validacion["guias_procesadas"]:,}
                    - Guías facturadas: {validacion["guias_facturadas"]:,} ({validacion["porcentaje_facturadas"]:.1f}%)
                    - **Guías anuladas:** {validacion["guias_anuladas"]:,} ({validacion["porcentaje_anuladas"]:.1f}%)
                    - Piezas totales: {validacion["piezas_totales"]:,}
                    - Grupos de tiendas identificados: {validacion["grupos_identificados"]:,}
                    - **Total facturado:** ${validacion["total_facturas"]:,.2f}
                    - **Total manifiesto:** ${validacion["total_manifiesto"]:,.2f}
                    """)

                except Exception as e:
                    st.error(f"Error en el procesamiento: {str(e)}")
                    st.exception(e)

    # --- Mostrar resultados si ya se procesó ---
    if datos["procesado"]:
        resultado = datos["resultado"]
        metricas = datos["metricas"]
        resumen = datos["resumen"]
        validacion = datos["validacion"]
        guias_anuladas = datos["guias_anuladas"]

        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
            [
                "📊 Resumen",
                "✅ Validación",
                "🏪 Todas las Tiendas",
                "🚫 Guías Anuladas",
                "🌎 Geografía",
                "📋 Datos",
                "💾 Exportar",
                "📄 Reporte PDF",
            ]
        )

        # --- Tab 1: Resumen ---
        with tab1:
            st.header("📊 Resumen Ejecutivo")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Grupos de Tiendas", f"{len(metricas):,}")
            with col2:
                st.metric("Total Guías", f"{len(resultado):,}")
            with col3:
                st.metric("Guías Anuladas", f"{validacion['guias_anuladas']:,}")
            with col4:
                st.metric("Piezas Totales", f"{validacion['piezas_totales']:,}")
            with col5:
                st.metric("Total Facturado", f"${metricas['SUBTOTAL'].sum():,.2f}")

            st.subheader("Distribución por Tipo de Tienda")
            if not resumen.empty:
                fig = px.pie(
                    resumen,
                    values="SUBTOTAL",
                    names="TIPO",
                    title="Distribución de Gastos por Tipo de Tienda",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Resumen por Tipo de Tienda")
            if not resumen.empty:
                resumen_display = resumen.copy()
                resumen_display["PIEZAS_POR_GUIA"] = (
                    resumen_display["PIEZAS"] / resumen_display["GUIAS"]
                ).round(2)
                st.dataframe(
                    resumen_display.style.format(
                        {
                            "SUBTOTAL": "${:,.2f}",
                            "PORCENTAJE": "{:.2f}%",
                            "PIEZAS_POR_GUIA": "{:.2f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

        # --- Tab 2: Validación ---
        with tab2:
            st.header("✅ Validación de Totales")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}")
            with col2:
                st.metric("Total Facturas", f"${validacion['total_facturas']:,.2f}")
            with col3:
                st.metric("Diferencia", f"${validacion['diferencia']:,.2f}")
            with col4:
                st.metric("% Diferencia", f"{validacion['porcentaje']:.2f}%")
            with col5:
                st.metric("Guías Anuladas", f"{validacion['guias_anuladas']:,}")

            if validacion["coincide"]:
                st.success(
                    "✅ **Validación Exitosa**\n\nLos totales coinciden dentro del margen aceptable."
                )
            else:
                st.warning(
                    f"⚠ **Validación con Diferencia**\n\nHay una diferencia de **${validacion['diferencia']:,.2f}** ({validacion['porcentaje']:.2f}%). Revisar guías anuladas."
                )

            st.info(f"""
            **📈 Métricas de Coincidencia:**
            - Guías totales procesadas: {validacion["guias_procesadas"]:,}
            - Guías facturadas: {validacion["guias_facturadas"]:,} ({validacion["porcentaje_facturadas"]:.1f}%)
            - **Guías anuladas:** {validacion["guias_anuladas"]:,} ({validacion["porcentaje_anuladas"]:.1f}%)
            - Piezas totales: {validacion["piezas_totales"]:,}
            - Promedio piezas/guía: {(validacion["piezas_totales"] / validacion["guias_procesadas"]):.1f}
            """)

        # --- Tab 3: Todas las Tiendas ---
        with tab3:
            st.header("🏪 Gastos por Tienda/Grupo - TODAS LAS TIENDAS")
            st.info("""
            **🏷️ Clasificación Automática:**
            - **TIENDA FÍSICA:** Nombres comerciales (MALL, PLAZA, CENTRO COMERCIAL, etc.)
            - **VENTA WEB:** Nombres personales (ROCIO, ALEJANDRA, MARIA, etc.)
            - **VENTAS AL POR MAYOR:** JOFRE SANTANA (clasificado automáticamente)
            """)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                min_gasto = st.number_input(
                    "Gasto mínimo",
                    value=0.0,
                    step=10.0,
                    format="%.2f",
                    key="min_gasto_todas",
                )
            with col2:
                tipo_filtro = st.multiselect(
                    "Tipo",
                    metricas["TIPO"].unique() if "TIPO" in metricas.columns else [],
                    default=[],
                    key="tipo_filtro_todas",
                )
            with col3:
                ciudad_filtro = st.text_input(
                    "Ciudad (parcial)", "", key="ciudad_filtro_todas"
                )
            with col4:
                min_piezas = st.number_input(
                    "Mín. piezas", value=0, step=1, key="min_piezas_todas"
                )

            buscar_grupo = st.text_input(
                "🔍 Buscar grupo, destinatario o ciudad:", key="buscar_grupo_todas"
            )

            col1, col2 = st.columns(2)
            with col1:
                orden_campo = st.selectbox(
                    "Ordenar por campo:",
                    ["SUBTOTAL", "GUIAS", "PIEZAS", "PORCENTAJE", "PROMEDIO_POR_PIEZA"],
                    key="orden_campo_todas",
                )
            with col2:
                orden_direccion = st.selectbox(
                    "Dirección:",
                    ["Descendente", "Ascendente"],
                    key="orden_direccion_todas",
                )

            metricas_filt = metricas.copy()
            if min_gasto > 0:
                metricas_filt = metricas_filt[metricas_filt["SUBTOTAL"] >= min_gasto]
            if tipo_filtro:
                metricas_filt = metricas_filt[metricas_filt["TIPO"].isin(tipo_filtro)]
            if ciudad_filtro:
                metricas_filt = metricas_filt[
                    metricas_filt["CIUDADES"].str.contains(
                        ciudad_filtro, case=False, na=False
                    )
                ]
            if min_piezas > 0:
                metricas_filt = metricas_filt[metricas_filt["PIEZAS"] >= min_piezas]
            if buscar_grupo:
                metricas_filt = metricas_filt[
                    metricas_filt["GRUPO"].str.contains(
                        buscar_grupo, case=False, na=False
                    )
                    | metricas_filt["DESTINATARIOS"].str.contains(
                        buscar_grupo, case=False, na=False
                    )
                    | metricas_filt["CIUDADES"].str.contains(
                        buscar_grupo, case=False, na=False
                    )
                ]

            if orden_direccion == "Descendente":
                metricas_filt = metricas_filt.sort_values(orden_campo, ascending=False)
            else:
                metricas_filt = metricas_filt.sort_values(orden_campo, ascending=True)

            st.subheader(f"📋 Todas las Tiendas ({len(metricas_filt):,} grupos)")
            if len(metricas_filt) > 0:
                st.subheader("📊 Distribución de Todas las Tiendas Filtradas")
                fig = px.bar(
                    metricas_filt.head(30),
                    x="SUBTOTAL",
                    y="GRUPO",
                    orientation="h",
                    title="Distribución de Gastos por Tienda",
                    color="TIPO",
                    text="SUBTOTAL",
                    hover_data=[
                        "GUIAS",
                        "PIEZAS",
                        "PORCENTAJE",
                        "DESTINATARIOS",
                        "CIUDADES",
                        "PROMEDIO_POR_PIEZA",
                    ],
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    height=max(400, len(metricas_filt.head(30)) * 25),
                    showlegend=True,
                )
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Tabla Completa de Todas las Tiendas")
            if not metricas_filt.empty:
                metricas_display = metricas_filt[
                    [
                        "GRUPO",
                        "TIPO",
                        "GUIAS",
                        "PIEZAS",
                        "SUBTOTAL",
                        "PORCENTAJE",
                        "PROMEDIO_POR_PIEZA",
                        "DESTINATARIOS",
                        "CIUDADES",
                    ]
                ].copy()
                styled_df = metricas_display.style.format(
                    {
                        "SUBTOTAL": "${:,.2f}",
                        "PORCENTAJE": "{:.2f}%",
                        "PROMEDIO_POR_PIEZA": "${:,.2f}",
                    }
                ).background_gradient(subset=["SUBTOTAL", "PORCENTAJE"], cmap="Blues")
                st.dataframe(styled_df, use_container_width=True, height=600)

                st.subheader("📈 Estadísticas de la Tabla Filtrada")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Grupos Mostrados", len(metricas_filt))
                with col2:
                    st.metric(
                        "Subtotal Total", f"${metricas_filt['SUBTOTAL'].sum():,.2f}"
                    )
                with col3:
                    st.metric("Piezas Totales", f"{metricas_filt['PIEZAS'].sum():,.0f}")
                with col4:
                    st.metric(
                        "Promedio por Pieza",
                        f"${(metricas_filt['SUBTOTAL'].sum() / metricas_filt['PIEZAS'].sum()):.2f}",
                    )

        # --- Tab 4: Guías Anuladas ---
        with tab4:
            st.header("🚫 Guías Anuladas")
            if not guias_anuladas.empty:
                st.info(
                    f"📊 **Total de guías anuladas:** {len(guias_anuladas):,} ({validacion['porcentaje_anuladas']:.1f}% del total)"
                )
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Guías", len(guias_anuladas))
                with col2:
                    total_manifiesto_anuladas = guias_anuladas[
                        "SUBTOTAL_MANIFIESTO"
                    ].sum()
                    st.metric("Valor Manifiesto", f"${total_manifiesto_anuladas:,.2f}")
                with col3:
                    total_piezas_anuladas = guias_anuladas["PIEZAS"].sum()
                    st.metric("Piezas", f"{total_piezas_anuladas:,}")
                with col4:
                    st.metric(
                        "Destinatarios Únicos", guias_anuladas["DESTINATARIO"].nunique()
                    )

                st.subheader("🔍 Filtros para Guías Anuladas")
                col1, col2, col3 = st.columns(3)
                with col1:
                    min_valor = st.number_input(
                        "Valor mínimo", value=0.0, step=1.0, key="min_valor_anuladas"
                    )
                with col2:
                    buscar_destinatario = st.text_input(
                        "Buscar destinatario", "", key="buscar_dest_anuladas"
                    )
                with col3:
                    buscar_ciudad = st.text_input(
                        "Buscar ciudad", "", key="buscar_ciudad_anuladas"
                    )

                guias_anuladas_filt = guias_anuladas.copy()
                if min_valor > 0:
                    guias_anuladas_filt = guias_anuladas_filt[
                        guias_anuladas_filt["SUBTOTAL_MANIFIESTO"] >= min_valor
                    ]
                if buscar_destinatario:
                    guias_anuladas_filt = guias_anuladas_filt[
                        guias_anuladas_filt["DESTINATARIO"].str.contains(
                            buscar_destinatario, case=False, na=False
                        )
                    ]
                if buscar_ciudad:
                    guias_anuladas_filt = guias_anuladas_filt[
                        guias_anuladas_filt["CIUDAD"].str.contains(
                            buscar_ciudad, case=False, na=False
                        )
                    ]

                st.subheader(
                    f"📋 Guías Anuladas Filtradas ({len(guias_anuladas_filt):,})"
                )
                columnas_mostrar = [
                    "FECHA_MANIFIESTO",
                    "GUIA",
                    "DESTINATARIO",
                    "CIUDAD",
                    "PIEZAS",
                    "SUBTOTAL_MANIFIESTO",
                    "TIPO",
                ]
                columnas_disponibles = [
                    col
                    for col in columnas_mostrar
                    if col in guias_anuladas_filt.columns
                ]
                guias_display = guias_anuladas_filt[columnas_disponibles].copy()
                if "FECHA_MANIFIESTO" in guias_display.columns:
                    guias_display["FECHA_MANIFIESTO"] = pd.to_datetime(
                        guias_display["FECHA_MANIFIESTO"], errors="coerce"
                    ).dt.strftime("%d/%m/%Y")
                if not guias_display.empty:
                    st.dataframe(
                        guias_display.style.format({"SUBTOTAL_MANIFIESTO": "${:,.2f}"}),
                        use_container_width=True,
                        height=400,
                    )

                    st.subheader("📊 Distribución de Guías Anuladas por Tipo")
                    anuladas_por_tipo = (
                        guias_anuladas_filt.groupby("TIPO")
                        .agg(
                            CANTIDAD=("GUIA", "count"),
                            VALOR=("SUBTOTAL_MANIFIESTO", "sum"),
                        )
                        .reset_index()
                    )
                    if not anuladas_por_tipo.empty:
                        fig = px.bar(
                            anuladas_por_tipo,
                            x="VALOR",
                            y="TIPO",
                            orientation="h",
                            title="Valor de Guías Anuladas por Tipo",
                            color="CANTIDAD",
                            text="VALOR",
                            color_continuous_scale="Reds",
                        )
                        fig.update_traces(
                            texttemplate="$%{text:,.2f}", textposition="outside"
                        )
                        fig.update_layout(
                            yaxis={"categoryorder": "total ascending"}, height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    st.download_button(
                        label="📥 Descargar Guías Anuladas (CSV)",
                        data=guias_display.to_csv(index=False),
                        file_name=f"guias_anuladas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            else:
                st.success(
                    "✅ No hay guías anuladas. Todas las guías del manifiesto tienen factura asociada."
                )

        # --- Tab 5: Geografía ---
        with tab5:
            st.header("🌎 Distribución Geográfica")
            if "CIUDAD" in resultado.columns:
                df_facturadas = resultado[resultado["ESTADO"] == "FACTURADA"]
                ciudad_agrupada = (
                    df_facturadas.groupby("CIUDAD")
                    .agg({"GUIA_LIMPIA": "count", "PIEZAS": "sum", "SUBTOTAL": "sum"})
                    .reset_index()
                )
                ciudad_agrupada = ciudad_agrupada.rename(
                    columns={
                        "GUIA_LIMPIA": "TOTAL_GUIAS",
                        "PIEZAS": "TOTAL_PIEZAS",
                        "SUBTOTAL": "TOTAL_SUBTOTAL",
                    }
                ).sort_values("TOTAL_SUBTOTAL", ascending=False)

                st.subheader("Top 15 Ciudades por Gasto (Facturadas)")
                if not ciudad_agrupada.empty:
                    fig = px.bar(
                        ciudad_agrupada.head(15),
                        x="TOTAL_SUBTOTAL",
                        y="CIUDAD",
                        orientation="h",
                        title="Distribución por Ciudad",
                        color="TOTAL_PIEZAS",
                        color_continuous_scale="Viridis",
                        text="TOTAL_SUBTOTAL",
                        hover_data=["TOTAL_GUIAS", "TOTAL_PIEZAS"],
                    )
                    fig.update_traces(
                        texttemplate="$%{text:,.2f}", textposition="outside"
                    )
                    fig.update_layout(
                        yaxis={"categoryorder": "total ascending"}, height=600
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.subheader("Tabla Detallada por Ciudad")
                    ciudad_agrupada["PORCENTAJE"] = (
                        ciudad_agrupada["TOTAL_SUBTOTAL"]
                        / ciudad_agrupada["TOTAL_SUBTOTAL"].sum()
                        * 100
                    ).round(2)
                    ciudad_agrupada["PROMEDIO_POR_PIEZA"] = (
                        ciudad_agrupada["TOTAL_SUBTOTAL"]
                        / ciudad_agrupada["TOTAL_PIEZAS"]
                    ).round(2)
                    st.dataframe(
                        ciudad_agrupada.style.format(
                            {
                                "TOTAL_SUBTOTAL": "${:,.2f}",
                                "PORCENTAJE": "{:.2f}%",
                                "PROMEDIO_POR_PIEZA": "${:,.2f}",
                            }
                        ),
                        use_container_width=True,
                        height=400,
                    )

        # --- Tab 6: Datos Detallados ---
        with tab6:
            st.header("📋 Datos Detallados")
            col1, col2, col3 = st.columns(3)
            with col1:
                grupo_filtro = st.multiselect(
                    "Filtrar por Grupo:",
                    sorted(resultado["GRUPO"].unique()),
                    default=[],
                    key="filtro_grupo_detalle",
                )
            with col2:
                estado_filtro = st.selectbox(
                    "Estado:",
                    ["TODOS", "FACTURADA", "ANULADA"],
                    key="estado_filtro_detalle",
                )
            with col3:
                min_subtotal = st.number_input(
                    "Mínimo subtotal:",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key="min_subtotal_detalle",
                )
            buscar = st.text_input(
                "🔍 Buscar por guía, destinatario o ciudad:", key="buscar_detalle"
            )

            datos_filt = resultado.copy()
            if grupo_filtro:
                datos_filt = datos_filt[datos_filt["GRUPO"].isin(grupo_filtro)]
            if estado_filtro == "FACTURADA":
                datos_filt = datos_filt[datos_filt["ESTADO"] == "FACTURADA"]
            elif estado_filtro == "ANULADA":
                datos_filt = datos_filt[datos_filt["ESTADO"] == "ANULADA"]
            datos_filt = datos_filt[datos_filt["SUBTOTAL_MANIFIESTO"] >= min_subtotal]
            if buscar:
                datos_filt = datos_filt[
                    datos_filt["GUIA_LIMPIA"]
                    .astype(str)
                    .str.contains(buscar, case=False, na=False)
                    | datos_filt["DESTINATARIO"]
                    .astype(str)
                    .str.contains(buscar, case=False, na=False)
                    | datos_filt["CIUDAD"]
                    .astype(str)
                    .str.contains(buscar, case=False, na=False)
                    | datos_filt["GRUPO"].str.contains(buscar, case=False, na=False)
                ]

            columnas_mostrar = [
                "FECHA_MANIFIESTO",
                "GUIA_LIMPIA",
                "ESTADO",
                "GRUPO",
                "DESTINATARIO",
                "CIUDAD",
                "PIEZAS",
                "SUBTOTAL_MANIFIESTO",
                "SUBTOTAL",
                "DIFERENCIA",
                "TIPO",
            ]
            columnas_disponibles = [
                col for col in columnas_mostrar if col in datos_filt.columns
            ]

            st.subheader(f"Registros filtrados: {len(datos_filt):,}")
            if not datos_filt.empty:
                datos_display = datos_filt[columnas_disponibles].copy()
                if "FECHA_MANIFIESTO" in datos_display.columns:
                    datos_display["FECHA_MANIFIESTO"] = pd.to_datetime(
                        datos_display["FECHA_MANIFIESTO"], errors="coerce"
                    ).dt.strftime("%d/%m/%Y")
                styled_datos = datos_display.style.format(
                    {
                        "SUBTOTAL_MANIFIESTO": "${:,.2f}",
                        "SUBTOTAL": "${:,.2f}",
                        "DIFERENCIA": "${:,.2f}",
                    }
                )

                def color_estado(val):
                    if val == "ANULADA":
                        return "background-color: #ffcccc"
                    elif val == "FACTURADA":
                        return "background-color: #ccffcc"
                    return ""

                styled_datos = styled_datos.applymap(color_estado, subset=["ESTADO"])
                st.dataframe(styled_datos, use_container_width=True, height=500)

                st.download_button(
                    label="📥 Descargar datos filtrados (CSV)",
                    data=datos_display.to_csv(index=False),
                    file_name=f"datos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            st.subheader("📈 Estadísticas de los Datos Filtrados")
            if not datos_filt.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Registros", len(datos_filt))
                    st.caption(
                        f"Facturadas: {len(datos_filt[datos_filt['ESTADO'] == 'FACTURADA']):,}"
                    )
                    st.caption(
                        f"Anuladas: {len(datos_filt[datos_filt['ESTADO'] == 'ANULADA']):,}"
                    )
                with col2:
                    st.metric("Subtotal Total", f"${datos_filt['SUBTOTAL'].sum():,.2f}")
                with col3:
                    st.metric("Piezas Totales", f"{datos_filt['PIEZAS'].sum():,.0f}")
                with col4:
                    st.metric(
                        "Promedio por Pieza",
                        f"${(datos_filt['SUBTOTAL'].sum() / datos_filt['PIEZAS'].sum()):.2f}",
                    )

        # --- Tab 7: Exportar ---
        with tab7:
            st.header("💾 Exportar Resultados")

            formato = st.radio(
                "Seleccione el formato de exportación:",
                [
                    "Excel Formato Exacto (.xlsx)",
                    "Excel Normal (.xlsx)",
                    "CSV (.csv)",
                    "JSON (.json)",
                ],
                horizontal=True,
                key="formato_export",
            )

            nombre_base = st.text_input(
                "Nombre base para los archivos:",
                value=f"gastos_tiendas_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                key="nombre_base_export",
            )

            st.markdown("---")
            st.subheader("📤 Exportaciones Principales")
            col1, col2, col3 = st.columns(3)

            if formato == "Excel Formato Exacto (.xlsx)":
                if st.button(
                    "📊 Generar Excel Formato Exacto",
                    use_container_width=True,
                    type="primary",
                ):
                    with st.spinner("Generando Excel con formato exacto..."):
                        excel_output = generar_excel_con_formato_exacto(
                            metricas, resultado, guias_anuladas, manifesto
                        )
                        if excel_output and hasattr(excel_output, "getvalue"):
                            col1.download_button(
                                label="📥 Descargar Excel Formato Exacto",
                                data=excel_output.getvalue(),
                                file_name=f"{nombre_base}_formato_exacto.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                help="Formato exacto con varias hojas y estilos",
                            )
                        else:
                            st.error(
                                "No se pudo generar el archivo Excel con formato exacto"
                            )

            elif formato == "Excel Normal (.xlsx)":
                if st.button(
                    "📊 Generar Excel Normal", use_container_width=True, type="primary"
                ):
                    with st.spinner("Generando Excel estándar..."):
                        output = io.BytesIO()
                        try:
                            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                                metricas.to_excel(
                                    writer, sheet_name="Gastos por Grupo", index=False
                                )

                                columnas_export = [
                                    "FECHA_MANIFIESTO",
                                    "GUIA_LIMPIA",
                                    "ESTADO",
                                    "GRUPO",
                                    "DESTINATARIO",
                                    "CIUDAD",
                                    "PIEZAS",
                                    "SUBTOTAL_MANIFIESTO",
                                    "SUBTOTAL",
                                    "DIFERENCIA",
                                    "TIPO",
                                ]
                                columnas_export = [
                                    col
                                    for col in columnas_export
                                    if col in resultado.columns
                                ]
                                resultado[columnas_export].to_excel(
                                    writer, sheet_name="Datos Completos", index=False
                                )

                                resumen.to_excel(
                                    writer, sheet_name="Resumen por Tipo", index=False
                                )

                                pd.DataFrame([validacion]).to_excel(
                                    writer, sheet_name="Validación", index=False
                                )

                                if not guias_anuladas.empty:
                                    guias_anuladas.to_excel(
                                        writer, sheet_name="Guias Anuladas", index=False
                                    )

                            output.seek(0)
                            col2.download_button(
                                label="📥 Descargar Excel Normal",
                                data=output.getvalue(),
                                file_name=f"{nombre_base}_normal.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                        except Exception as e:
                            st.error(f"Error al generar Excel normal: {str(e)}")

            elif formato == "CSV (.csv)":
                col1.download_button(
                    label="📥 Métricas (CSV)",
                    data=metricas.to_csv(index=False).encode("utf-8"),
                    file_name=f"{nombre_base}_metricas.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                col2.download_button(
                    label="📥 Datos completos (CSV)",
                    data=resultado.to_csv(index=False).encode("utf-8"),
                    file_name=f"{nombre_base}_datos.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                if not guias_anuladas.empty:
                    col3.download_button(
                        label="📥 Guías Anuladas (CSV)",
                        data=guias_anuladas.to_csv(index=False).encode("utf-8"),
                        file_name=f"{nombre_base}_anuladas.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            elif formato == "JSON (.json)":
                col1.download_button(
                    label="📥 Métricas (JSON)",
                    data=metricas.to_json(
                        orient="records", indent=2, force_ascii=False
                    ).encode("utf-8"),
                    file_name=f"{nombre_base}_metricas.json",
                    mime="application/json",
                    use_container_width=True,
                )

            st.markdown("---")
            st.subheader("📤 Exportaciones Específicas")
            col1, col2, col3 = st.columns(3)
            with col1:
                if not metricas.empty:
                    grupos_principales = metricas[metricas["SUBTOTAL"] > 0]
                    st.download_button(
                        label="🎯 Grupos Principales",
                        data=grupos_principales.to_csv(index=False).encode("utf-8"),
                        file_name=f"{nombre_base}_grupos_principales.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            with col2:
                if not resultado.empty:
                    venta_web = resultado[resultado["TIPO"] == "VENTA WEB"]
                    if not venta_web.empty:
                        st.download_button(
                            label="🛒 Ventas Web Detalladas",
                            data=venta_web[
                                [
                                    "FECHA_MANIFIESTO",
                                    "GUIA_LIMPIA",
                                    "ESTADO",
                                    "DESTINATARIO",
                                    "CIUDAD",
                                    "PIEZAS",
                                    "SUBTOTAL",
                                ]
                            ]
                            .to_csv(index=False)
                            .encode("utf-8"),
                            file_name=f"{nombre_base}_ventas_web.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
            with col3:
                if not guias_anuladas.empty:
                    st.download_button(
                        label="🚫 Guías Anuladas Detalladas",
                        data=guias_anuladas[
                            [
                                "FECHA_MANIFIESTO",
                                "GUIA_LIMPIA",
                                "DESTINATARIO",
                                "CIUDAD",
                                "PIEZAS",
                                "SUBTOTAL_MANIFIESTO",
                                "TIPO",
                            ]
                        ]
                        .to_csv(index=False)
                        .encode("utf-8"),
                        file_name=f"{nombre_base}_guias_anuladas_detalladas.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

        # --- Tab 8: Reporte PDF ---
        with tab8:
            st.header("📄 Generar Reporte PDF Ejecutivo")
            st.info("""
            **📋 Contenido del Reporte PDF:**
            1. Métricas principales del análisis
            2. Resumen por tipo de tienda
            3. Top 15 grupos por gasto
            4. Análisis ejecutivo con guías anuladas
            5. Recomendaciones
            """)
            if st.button(
                "🖨️ Generar Reporte PDF Ejecutivo",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Generando reporte PDF..."):
                    try:
                        pdf_path = generar_pdf_reporte(metricas, resumen, validacion)
                        if pdf_path:
                            with open(pdf_path, "rb") as pdf_file:
                                pdf_bytes = pdf_file.read()
                            st.success("✅ Reporte PDF generado exitosamente")
                            st.download_button(
                                label="📥 Descargar Reporte PDF",
                                data=pdf_bytes,
                                file_name=f"reporte_ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(f"Error al generar el reporte PDF: {str(e)}")
    else:
        # Pantalla inicial del módulo
        st.info(
            "👆 **Por favor, carga los archivos de manifiesto y facturas desde el panel lateral para comenzar el análisis.**"
        )
        st.markdown("### 📋 Estructura esperada del Manifiesto:")
        st.code("""
        FECHA,GUIA,ORIGEN,GUIA2,DESTINATARIO,SERVICIO,TRANSPORTE,PIEZAS,PESO,FLETE,SUBTOTAL
        46004,20176386,DURAN,LC52450203,Lider celeley zamb CAR,SEC,,1,16,3.41,3.41
        46006,LC52390589,GUAYAQUIL,LC52516378,COMERCIALIZADO CAR,PRI,,1,4,2.15,2.15
        """)
        st.markdown("### 📋 Estructura esperada de Facturas:")
        st.code("""
        GUIA,SUBTOTAL
        LC52450203,3.41
        LC52516378,2.15
        """)

    st.markdown("</div>", unsafe_allow_html=True)
    # ==============================================================================
# MÓDULO: AUDITORÍA DE CORREOS
# ==============================================================================
class WiloEmailEngine:
    """Motor real para extraccion y analisis de correos logisticos desde TODAS las carpetas."""

    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self.password = password
        self.mail = None

    def _connect(self):
        """Establece conexión IMAP segura."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.host)
            self.mail.login(self.user, self.password)
        except Exception as e:
            raise ConnectionError(
                f"Error de conexion: Verifica tu usuario/pass. Detalle: {e}"
            )

    def _decode_utf8(self, header_part) -> str:
        """Decodifica cabeceras de correo correctamente."""
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
        """Obtiene lista de todas las carpetas (buzones) disponibles."""
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
        except Exception as e:
            st.warning(f"No se pudieron listar carpetas: {e}")
            return ["INBOX"]

    def classify_email(self, subject: str, body: str) -> Dict[str, str]:
        """Clasifica el correo según palabras clave."""
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

    def get_latest_news(
        self, days: int = 90, limit_per_folder: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Busca correos en TODAS las carpetas desde hace 'days' días.
        Retorna una lista con los analizados, limitando por carpeta para no saturar.
        """
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
                    _, msg_data = self.mail.fetch(e_id, "(RFC822)")
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
                                        body = part.get_payload(decode=True).decode(
                                            errors="ignore"
                                        )
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode(
                                    errors="ignore"
                                )

                            analysis = self.classify_email(subject, body)
                            order_match = re.search(r"#(\d+)", subject)
                            order_id = order_match.group(1) if order_match else "N/A"

                            results.append(
                                {
                                    "id": e_id.decode(),
                                    "fecha": date_,
                                    "remitente": sender,
                                    "asunto": subject,
                                    "cuerpo": body,
                                    "tipo": analysis["tipo"],
                                    "urgencia": analysis["urgencia"],
                                    "pedido": order_id,
                                    "carpeta": folder,
                                }
                            )
            except Exception as e:
                st.warning(f"Error procesando carpeta '{folder}': {e}")
                continue

        self.mail.logout()
        return results


def show_auditoria_correos():
    """Modulo de auditoria de correos (interfaz Streamlit)"""
    add_back_button(key="back_auditoria")
    show_module_header(
        "📧 Auditoria de Correos",
        "Analisis inteligente de novedades por email en TODAS las carpetas",
    )

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    st.sidebar.title("🔐 Acceso Seguro")
    mail_user = st.sidebar.text_input("Correo", value="wperez@fashionclub.com.ec")
    mail_pass = st.sidebar.text_input("Contraseña", value="2wperez*.", type="password")
    imap_host = "mail.fashionclub.com.ec"

    st.title("📧 Auditoria de Correos Wilo AI (Multicarpeta)")
    st.markdown("---")

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"**Usuario:** {mail_user} | **Servidor:** {imap_host}")

    with col_btn:
        run_audit = st.button(
            "🚀 Iniciar Auditoria Completa", use_container_width=True, type="primary"
        )

    if run_audit:
        if not mail_pass:
            st.error("Por favor ingresa tu contraseña en la barra lateral.")
            return

        engine = WiloEmailEngine(imap_host, mail_user, mail_pass)

        with st.spinner(
            "Conectando con Fashion Club y analizando TODAS las carpetas (esto puede tomar unos segundos)..."
        ):
            try:
                data = engine.get_latest_news(days=90, limit_per_folder=50)
                if not data:
                    st.warning(
                        "No se encontraron novedades en los últimos 90 días en ninguna carpeta."
                    )
                    return

                df = pd.DataFrame(data)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Analizados", len(df))
                m2.metric("Críticos 🚨", len(df[df["urgencia"] == "ALTA"]))
                m3.metric("Faltantes 📦", len(df[df["tipo"].str.contains("FALTANTE")]))
                m4.metric(
                    "Pedidos únicos",
                    df["pedido"].nunique() - (1 if "N/A" in df["pedido"].values else 0),
                )

                st.subheader("📋 Bandeja de Entrada Analizada (Todas las carpetas)")
                st.dataframe(
                    df[
                        [
                            "fecha",
                            "remitente",
                            "asunto",
                            "tipo",
                            "urgencia",
                            "pedido",
                            "carpeta",
                        ]
                    ],
                    use_container_width=True,
                    column_config={
                        "urgencia": st.column_config.TextColumn("Prioridad"),
                        "tipo": st.column_config.TextColumn("Categoría"),
                        "pedido": st.column_config.TextColumn("ID Pedido"),
                        "carpeta": st.column_config.TextColumn("Carpeta"),
                    },
                )

                st.markdown("---")
                st.subheader("🔍 Inspector de Contenido")
                selected_idx = st.selectbox(
                    "Selecciona un correo para leer el análisis completo:",
                    df.index,
                    format_func=lambda x: (
                        f"[{df.iloc[x]['tipo']}] - {df.iloc[x]['asunto'][:50]}..."
                    ),
                )

                detail = df.iloc[selected_idx]
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.markdown(f"""
                    **Detalles Técnicos:**
                    - **Remitente:** {detail["remitente"]}
                    - **Fecha:** {detail["fecha"]}
                    - **Pedido Detectado:** `{detail["pedido"]}`
                    - **Carpeta:** `{detail["carpeta"]}`
                    """)
                with c2:
                    st.text_area("Cuerpo del Correo:", detail["cuerpo"], height=200)

            except Exception as e:
                st.error(f"❌ Error durante la auditoría: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# FUNCIONES AUXILIARES PARA DASHBOARD LOGÍSTICO (TRANSFERENCIAS)
# ==============================================================================
def clasificar_transferencia(row: pd.Series) -> str:
    """Clasifica una transferencia según destino y cantidad."""
    sucursal = str(row.get('Sucursal Destino', row.get('Bodega Destino', ''))).upper()
    cantidad = row.get('Cantidad_Entera', 0)
    
    if any(kw in sucursal for kw in PRICE_KEYWORDS) or \
       'CITY MALL' in sucursal or \
       'CUENCA CENTRO HISTORICO' in sucursal:
        return 'Price Club'
    
    if cantidad >= 500 and cantidad % 100 == 0:
        return 'Fundas'
    
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


def procesar_transferencias(df: pd.DataFrame) -> Dict:
    """Procesa DataFrame de transferencias y retorna resumen."""
    df = df.dropna(subset=['Secuencial'])
    df['Secuencial'] = df['Secuencial'].astype(str).str.strip()
    df = df[df['Secuencial'] != '']
    
    cant_col = 'Cantidad Prendas' if 'Cantidad Prendas' in df.columns else 'Cantidad'
    df['Cantidad_Entera'] = df[cant_col].apply(extraer_entero)
    
    df['Categoria'] = df.apply(clasificar_transferencia, axis=1)
    
    # Determinar total de sucursales únicas por categoría (para comparación con esperadas)
    suc_por_cat = df.groupby('Categoria')['Sucursal Destino'].nunique().to_dict() if 'Sucursal Destino' in df.columns else {}
    
    resumen = {
        'total_unidades': int(df['Cantidad_Entera'].sum()),
        'total_transferencias': int(df['Secuencial'].nunique()),
        'por_categoria': {},
        'detalle_categoria': {},
        'sucursales_por_categoria': suc_por_cat,
        'df_procesado': df
    }
    
    for cat in CATEGORIAS_TRANSFERENCIA.keys():
        df_cat = df[df['Categoria'] == cat]
        resumen['por_categoria'][cat] = int(df_cat['Cantidad_Entera'].sum())
        resumen['detalle_categoria'][cat] = {
            'cantidad': int(df_cat['Cantidad_Entera'].sum()),
            'transferencias': int(df_cat['Secuencial'].nunique()),
            'sucursales_unicas': int(df_cat['Sucursal Destino'].nunique()) if 'Sucursal Destino' in df_cat.columns else 0
        }
    
    return resumen


# ==============================================================================
# MÓDULO PRINCIPAL: DASHBOARD LOGÍSTICO (show_logistica) MEJORADO
# ==============================================================================
def show_logistica():
    """Dashboard logístico completo con visualización en millones."""
    add_back_button(key="back_logistica")
    show_module_header(
        "📦 Dashboard Logístico",
        "Control de transferencias y distribución de mercadería"
    )

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Transferencias Diarias", "🧠 Clasificación Inteligente"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)

        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            uploaded = st.file_uploader(
                "Subir archivo de transferencias (Excel)",
                type=['xlsx', 'xls'],
                key="log_upload"
            )
        with col_u2:
            if st.button("🔄 Limpiar", use_container_width=True):
                st.rerun()

        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                st.success(f"✅ Archivo cargado: {len(df)} registros")

                with st.expander("🔍 Vista previa", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)

                required = ['Secuencial']
                has_destino = any(c in df.columns for c in ['Sucursal Destino', 'Bodega Destino'])
                has_cantidad = any(c in df.columns for c in ['Cantidad Prendas', 'Cantidad'])

                if not all(c in df.columns for c in required):
                    st.error("❌ Falta columna 'Secuencial'")
                elif not has_destino:
                    st.error("❌ No se encontró columna de destino")
                elif not has_cantidad:
                    st.error("❌ No se encontró columna de cantidad")
                else:
                    resultado = procesar_transferencias(df)

                    # ---- KPIs en formato estilo imagen ----
                    total_unidades = resultado['total_unidades']
                    total_millones = total_unidades / 1_000_000
                    promedio_transf = total_unidades / resultado['total_transferencias'] if resultado['total_transferencias'] > 0 else 0
                    categorias_activas = sum(1 for v in resultado['por_categoria'].values() if v > 0)
                    total_categorias = len(CATEGORIAS_TRANSFERENCIA)
                    pct_fundas = (resultado['por_categoria'].get('Fundas', 0) / total_unidades * 100) if total_unidades > 0 else 0

                    st.markdown("---")
                    st.markdown("### 📊 KPIs por Categoría")

                    # Primera fila de KPIs grandes (Total, Promedio, Categ, %Fundas)
                    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                    with col_k1:
                        st.metric("📦 Total General", f"{total_millones:,.3f} M", help=f"{total_unidades:,} unidades")
                    with col_k2:
                        st.metric("📊 Promedio x Transferencia", f"{promedio_transf:,.0f}")
                    with col_k3:
                        st.metric("🏷️ Categorías Activas", f"{categorias_activas}/{total_categorias}")
                    with col_k4:
                        st.metric("📎 % Fundas", f"{pct_fundas:.1f}%")

                    st.markdown("---")
                    st.subheader("📈 Distribución por Categoría")

                    # Gráfico de pastel con valores en millones
                    df_pie = pd.DataFrame({
                        'Categoria': list(resultado['por_categoria'].keys()),
                        'Unidades': list(resultado['por_categoria'].values())
                    })
                    df_pie = df_pie[df_pie['Unidades'] > 0]
                    df_pie['Unidades_M'] = df_pie['Unidades'] / 1_000_000

                    col_g1, col_g2 = st.columns([2, 1])
                    with col_g1:
                        fig = px.pie(df_pie, values='Unidades', names='Categoria',
                                     title="Distribución por Categoría (unidades)",
                                     hole=0.4,
                                     color_discrete_sequence=px.colors.qualitative.Set3)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)

                    with col_g2:
                        st.subheader("Detalle por Categoría")
                        for cat, info in resultado['detalle_categoria'].items():
                            if info['cantidad'] > 0:
                                icon = CATEGORIAS_TRANSFERENCIA.get(cat, {}).get('icon', '📌')
                                color = CATEGORIAS_TRANSFERENCIA.get(cat, {}).get('color', '#60A5FA')
                                cantidad_m = info['cantidad'] / 1_000_000
                                st.markdown(f"""
                                <div style="background: {color}15; border-left: 4px solid {color}; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;">
                                    <div style="font-weight: 700; color: white;">{icon} {cat}</div>
                                    <div style="font-size: 0.85rem; color: #94A3B8;">
                                        {cantidad_m:,.3f}M unidades • {info['transferencias']} transf. • {info['sucursales_unicas']} suc.
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Tabla detalle (sin cambios)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("📋 Detalle de Transferencias")
                    destino_col = 'Sucursal Destino' if 'Sucursal Destino' in resultado['df_procesado'].columns else 'Bodega Destino'
                    df_detalle = resultado['df_procesado'][['Secuencial', destino_col, 'Cantidad_Entera', 'Categoria']].copy()
                    df_detalle.columns = ['Secuencial', 'Destino', 'Cantidad', 'Categoría']
                    st.dataframe(df_detalle, use_container_width=True, height=300)

                    # Exportar
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_detalle.to_excel(writer, sheet_name='Detalle', index=False)
                        pd.DataFrame(resultado['detalle_categoria']).T.to_excel(writer, sheet_name='Resumen')
                    st.download_button(
                        "📥 Descargar Excel",
                        buffer.getvalue(),
                        f"transferencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")

        else:
            st.info("👆 **Sube un archivo Excel** con columnas: `Secuencial`, `Sucursal Destino`/`Bodega Destino`, `Cantidad Prendas`/`Cantidad`.")

    with tab2:
        mostrar_clasificacion_inteligente()

    st.markdown('</div>', unsafe_allow_html=True)



# ==============================================================================
# CLASIFICACIÓN INTELIGENTE DE PRODUCTOS (TAB2 DEL DASHBOARD LOGÍSTICO)
# ==============================================================================
GENDER_MAP = {
    'GIRLS': 'Mujer', 'WOMEN': 'Mujer', 'WOMENS': 'Mujer', 'WOMAN': 'Mujer',
    'LADIES': 'Mujer', 'FEMALE': 'Mujer', 'MUJER': 'Mujer', 'LADY': 'Mujer',
    'GUYS': 'Hombre', 'MEN': 'Hombre', 'MENS': 'Hombre', 'MAN': 'Hombre',
    'HOMBRE': 'Hombre', 'MALE': 'Hombre', 'BOY': 'Hombre', 'BOYS': 'Hombre',
    'UNISEX': 'Unisex', 'KIDS': 'Niño/a', 'CHILD': 'Niño/a', 'CHILDREN': 'Niños',
    'BABY': 'Bebé', 'INFANT': 'Bebé', 'TODDLER': 'Bebé'
}

CATEGORY_MAP = {
    'TEES': 'Camiseta', 'TEE': 'Camiseta', 'T-SHIRT': 'Camiseta', 'TSHIRT': 'Camiseta',
    'TANK': 'Camiseta sin mangas', 'TANK TOP': 'Camiseta sin mangas',
    'TOP': 'Top', 'TOPS': 'Top', 'BABY TEE': 'Top', 'BABYTEE': 'Top',
    'BARE': 'Blusa', 'CORE': 'Blusa', 'BLOUSE': 'Blusa',
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
    'SPRING': 'Primavera', 'FALL': 'Otoño', 'AUTUMN': 'Otoño',
    'FASHION': 'Moda', 'SS': 'Primavera-Verano', 'FW': 'Otoño-Invierno'
}

COLOR_MAP = {
    'BLACK': 'Negro', 'BLACK/DARK': 'Negro', 'DARK BLACK': 'Negro Oscuro',
    'WHITE': 'Blanco', 'WHITE/LIGHT': 'Blanco', 'CREAM': 'Crema',
    'RED': 'Rojo', 'RASPBERRY': 'Frambuesa', 'EARTH RED': 'Rojo Tierra',
    'BLUE': 'Azul', 'NAVY': 'Azul Marino', 'LIGHT BLUE': 'Azul Claro', 'ROYAL': 'Azul Rey',
    'GREEN': 'Verde', 'GREEN GABLES': 'Verde Gabardina', 'OLIVE': 'Verde Oliva',
    'YELLOW': 'Amarillo', 'GOLD': 'Dorado', 'MUSTARD': 'Mostaza',
    'PINK': 'Rosa', 'HOT PINK': 'Rosa Fuerte', 'BLUSH': 'Rosa Palo',
    'PURPLE': 'Morado', 'VIOLET': 'Violeta', 'LILAC': 'Lila', 'LAVENDER': 'Lavanda',
    'ORANGE': 'Naranja', 'PEACH': 'Durazno', 'CORAL': 'Coral',
    'BROWN': 'Marrón', 'TAN': 'Café Claro', 'COFFEE': 'Café',
    'GRAY': 'Gris', 'GREY': 'Gris', 'SILVER': 'Plateado', 'CHARCOAL': 'Gris Carbón',
    'BEIGE': 'Beige', 'KHAKI': 'Caqui', 'CAMEL': 'Camello',
    'BLEACH': 'Blanqueado', 'LIGHT WASH': 'Lavado Claro', 'DARK WASH': 'Lavado Oscuro',
    'DARK': 'Oscuro', 'LIGHT': 'Claro', 'TENDER': 'Tender (Amarillo Suave)',
    'MULTI': 'Multicolor', 'MULTICOLOR': 'Multicolor', 'MIXED': 'Multicolor'
}

SIZE_HIERARCHY = [
    '3XS', 'XXS', '2XS', 'XS', 'XSMALL', 'EXTRA SMALL',
    'S', 'SMALL', 'M', 'MEDIUM', 'L', 'LARGE', 
    'XL', 'XLARGE', 'EXTRA LARGE', '1XL',
    '2XL', 'XXL', 'XXLARGE', '3XL', 'XXXL', 'XXXLARGE',
    '4XL', 'XXXXL', '5XL', 'OS', 'ONE SIZE', 'UNICA', 'U'
]

SIZE_NORMALIZATION = {
    'XSMALL': 'XS', 'EXTRA SMALL': 'XS', 'XXS': '2XS', '2XS': '2XS',
    'SMALL': 'S', 'MEDIUM': 'M', 'LARGE': 'L',
    'XLARGE': 'XL', 'EXTRA LARGE': 'XL', '1XL': 'XL',
    'XXLARGE': '2XL', 'XXL': '2XL', '2XL': '2XL',
    'XXXLARGE': '3XL', 'XXXL': '3XL', '3XL': '3XL',
    'XXXXL': '4XL', '4XL': '4XL', '5XL': '5XL',
    'OS': 'Única', 'ONE SIZE': 'Única', 'UNICA': 'Única', 'U': 'Única'
}

IGNORE_WORDS = {'AERO', 'OF', 'THE', 'AND', 'IN', 'WITH', 'FOR', 'BY', 'ON', 'AT', 'TO', 'FROM'}


class TextileClassifier:
    """Clasificador inteligente para productos textiles."""
    
    def __init__(self):
        self.gender_map = GENDER_MAP
        self.category_map = CATEGORY_MAP
        self.color_map = COLOR_MAP
        self.size_hierarchy = SIZE_HIERARCHY
        self.size_norm = SIZE_NORMALIZATION
        self.ignore_words = IGNORE_WORDS
        
    def classify_product(self, product_name: str) -> dict:
        if not product_name or not isinstance(product_name, str):
            return self._get_empty_classification()
        
        product_name = str(product_name).upper().strip()
        words = product_name.split()
        
        if not words:
            return self._get_empty_classification()
        
        color_idx, color_norm = self._detect_color_index(words)
        size_idx, size_norm = self._detect_size_index(words)
        gender_phrase, gender_norm = self._extract_gender_phrase(words)
        desc_words = self._extract_description(words, gender_phrase, color_idx, size_idx)
        descripcion = ' '.join(desc_words) if desc_words else ''
        category_info = self._detect_category(words)
        style_info = self._detect_style(words)
        
        classification = {
            'Genero_Raw': gender_phrase,
            'Genero': gender_norm,
            'Descripcion': descripcion,
            'Categoria': category_info['categoria'],
            'Subcategoria': category_info['subcategoria'],
            'Color': color_norm,
            'Talla': size_norm,
            'Material': style_info['material'],
            'Estilo': style_info['estilo']
        }
        
        return self._clean_classification(classification)
    
    def _extract_gender_phrase(self, words):
        if not words:
            return '', 'Unisex'
        
        if len(words) >= 2 and words[0] == 'AERO' and words[1] in self.gender_map:
            phrase = f"{words[0]} {words[1]}"
            norm = self.gender_map[words[1]]
            return phrase, norm
        
        if words[0] in self.gender_map:
            return words[0], self.gender_map[words[0]]
        
        for i, w in enumerate(words):
            if w in self.gender_map:
                phrase = ' '.join(words[:i+1])
                return phrase, self.gender_map[w]
        
        return words[0], 'Unisex'
    
    def _detect_color_index(self, words):
        for i, w in enumerate(words):
            if w in self.color_map:
                return i, self.color_map[w]
            for color_key, color_val in self.color_map.items():
                if color_key in w and len(w) < len(color_key) + 3:
                    return i, color_val
        return None, 'No Especificado'
    
    def _detect_size_index(self, words):
        for i, w in enumerate(words):
            if w in self.size_hierarchy:
                return i, self._normalize_size(w)
            if w in self.size_norm:
                return i, self.size_norm[w]
        return None, 'Única'
    
    def _extract_description(self, words, gender_phrase, color_idx, size_idx):
        if not gender_phrase:
            return []
        
        gender_words = gender_phrase.split()
        start_idx = len(gender_words)
        
        end_candidates = []
        if color_idx is not None:
            end_candidates.append(color_idx)
        if size_idx is not None:
            end_candidates.append(size_idx)
        
        if end_candidates:
            end_idx = min(end_candidates)
        else:
            end_idx = len(words)
        
        if end_idx <= start_idx:
            return []
        
        desc_words = words[start_idx:end_idx]
        desc_words = [w for w in desc_words if w not in self.ignore_words and len(w) > 1]
        
        return desc_words
    
    def _normalize_size(self, size):
        return self.size_norm.get(size, size)
    
    def _detect_category(self, words):
        categoria = 'General'
        subcategoria = ''
        found_categories = []
        
        for word in words:
            if word in self.category_map:
                found_categories.append(self.category_map[word])
        
        if found_categories:
            priority = ['Camiseta', 'Pantalón', 'Jeans', 'Vestido', 'Chaqueta', 
                       'Sudadera', 'Top', 'Short', 'Polo']
            for p in priority:
                if p in found_categories:
                    categoria = p
                    others = [c for c in found_categories if c != p]
                    subcategoria = ' / '.join(others[:2])
                    break
            else:
                categoria = found_categories[0]
                if len(found_categories) > 1:
                    subcategoria = ' / '.join(found_categories[1:3])
        
        return {'categoria': categoria, 'subcategoria': subcategoria}
    
    def _detect_style(self, words):
        material = ''
        estilo = ''
        
        materials = {
            'COTTON': 'Algodón', 'POLYESTER': 'Poliéster', 'DENIM': 'Denim',
            'LEATHER': 'Cuero', 'WOOL': 'Lana', 'SILK': 'Seda', 'LINEN': 'Lino',
            'RAYON': 'Rayón', 'SPANDEX': 'Spandex', 'NYLON': 'Nylon'
        }
        
        styles = {
            'GRAPHIC': 'Estampado', 'PRINTED': 'Estampado', 'LOGO': 'Con Logo',
            'SOLID': 'Liso', 'STRIPED': 'Rayado', 'PLAID': 'Cuadros',
            'BASIC': 'Básico', 'PREMIUM': 'Premium', 'FASHION': 'Moda',
            'VINTAGE': 'Vintage', 'CLASSIC': 'Clásico', 'SLIM': 'Slim Fit',
            'RELAXED': 'Relaxed Fit', 'OVERSIZED': 'Oversized'
        }
        
        for word in words:
            if word in materials:
                material = materials[word]
            if word in styles:
                estilo = styles[word]
        
        return {'material': material, 'estilo': estilo}
    
    def _clean_classification(self, classification):
        if not classification['Genero']:
            classification['Genero'] = 'Unisex'
        if not classification['Categoria']:
            classification['Categoria'] = 'General'
        if not classification['Descripcion']:
            classification['Descripcion'] = '-'
        
        for key in classification:
            if isinstance(classification[key], str):
                classification[key] = classification[key].strip()
        
        return classification
    
    def _get_empty_classification(self):
        return {
            'Genero_Raw': '',
            'Genero': 'Unisex',
            'Descripcion': '-',
            'Categoria': 'General',
            'Subcategoria': '',
            'Color': 'No Especificado',
            'Talla': 'Única',
            'Material': '',
            'Estilo': ''
        }


class DataProcessor:
    """Procesador de archivos de transferencias para clasificación inteligente."""
    
    def __init__(self):
        self.classifier = TextileClassifier()
    
    def process_excel_file(self, file) -> pd.DataFrame:
        try:
            if hasattr(file, 'name'):
                filename = file.name.lower()
                if filename.endswith('.csv'):
                    df = pd.read_csv(file, encoding='utf-8')
                else:
                    df = pd.read_excel(file, engine='openpyxl')
            else:
                df = pd.read_excel(file)
            
            df.columns = df.columns.str.strip().str.upper()
            
            product_col = None
            product_aliases = ['PRODUCTO', 'ITEM', 'DESCRIPCION', 'DESCRIPTION', 
                             'ARTICULO', 'PRODUCT', 'NOMBRE', 'NAME', 'ITEM DESCRIPTION']
            
            for alias in product_aliases:
                matching_cols = [c for c in df.columns if alias in c]
                if matching_cols:
                    product_col = matching_cols[0]
                    break
            
            if product_col is None:
                for col in df.columns:
                    if len(df) > 0:
                        sample = str(df[col].iloc[0])
                        if len(sample) > 10 and any(x in sample.upper() for x in ['AERO', 'GIRLS', 'WOMEN', 'MEN']):
                            product_col = col
                            break
            
            if product_col is None:
                product_col = df.columns[0]
            
            df = df.rename(columns={product_col: 'PRODUCTO'})
            df = df.dropna(subset=['PRODUCTO'])
            df['PRODUCTO'] = df['PRODUCTO'].astype(str).str.strip()
            
            bodega_col = None
            bodega_aliases = ['BODEGA RECIBE', 'BODEGA DESTINO', 'SUCURSAL DESTINO', 
                            'DESTINO', 'BODEGA', 'SUCURSAL', 'TIENDA', 'STORE']
            for alias in bodega_aliases:
                matching_cols = [c for c in df.columns if alias in c]
                if matching_cols:
                    bodega_col = matching_cols[0]
                    break
            
            if bodega_col:
                df = df.rename(columns={bodega_col: 'BODEGA_RECIBE'})
            
            cant_col = None
            cant_aliases = ['CANTIDAD', 'QUANTITY', 'UNIDADES', 'QTY', 'CANT']
            for alias in cant_aliases:
                matching_cols = [c for c in df.columns if alias in c]
                if matching_cols:
                    cant_col = matching_cols[0]
                    break
            
            if cant_col:
                df = df.rename(columns={cant_col: 'CANTIDAD'})
                df['CANTIDAD'] = pd.to_numeric(
                    df['CANTIDAD'].astype(str).str.replace(',', '').str.replace(' ', ''), 
                    errors='coerce'
                ).fillna(0)
            
            fecha_col = None
            fecha_aliases = ['FECHA', 'DATE', 'DIA', 'DAY']
            for alias in fecha_aliases:
                matching_cols = [c for c in df.columns if alias in c]
                if matching_cols:
                    fecha_col = matching_cols[0]
                    break
            
            if fecha_col:
                df = df.rename(columns={fecha_col: 'FECHA'})
                df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce', dayfirst=True)
            
            if df.empty or 'PRODUCTO' not in df.columns:
                st.error("No se encontraron datos válidos para clasificar.")
                return pd.DataFrame()
            
            df = self._classify_products(df)
            return df
            
        except Exception as e:
            st.error(f"Error procesando archivo: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return pd.DataFrame()
    
    def _classify_products(self, df):
        classifications = []
        for prod in df['PRODUCTO']:
            classifications.append(self.classifier.classify_product(prod))
        
        class_df = pd.DataFrame(classifications)
        
        cols_to_drop = [col for col in class_df.columns if col in df.columns and col != 'PRODUCTO']
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        
        result = pd.concat([df.reset_index(drop=True), class_df.reset_index(drop=True)], axis=1)
        return result
    # ==============================================================================
# FUNCIÓN AUXILIAR PARA MOSTRAR CLASIFICACIÓN INTELIGENTE (TAB2)
# ==============================================================================
def mostrar_clasificacion_inteligente():
    """Dashboard de Clasificación Inteligente con tablas dinámicas por talla, color y tienda."""
    
    st.markdown("### 📂 Cargar archivo de productos para clasificación inteligente")
    st.markdown("Soporta archivos: **Excel (.xlsx, .xls)** y **CSV (.csv)**")
    
    if 'clasificacion_data' not in st.session_state:
        st.session_state.clasificacion_data = pd.DataFrame()
    if 'clasificacion_loaded' not in st.session_state:
        st.session_state.clasificacion_loaded = False
    
    processor = DataProcessor()
    
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Selecciona tu archivo",
            type=['xlsx', 'xls', 'csv'],
            key="clasificador_file_uploader"
        )
    with col_up2:
        if st.button("🔄 Limpiar datos", key="btn_limpiar_clasificacion", use_container_width=True):
            st.session_state.clasificacion_data = pd.DataFrame()
            st.session_state.clasificacion_loaded = False
            st.rerun()
    
    if uploaded_file is not None:
        with st.spinner("🔍 Procesando y clasificando productos..."):
            try:
                df_procesado = processor.process_excel_file(uploaded_file)
                if not df_procesado.empty:
                    st.session_state.clasificacion_data = df_procesado
                    st.session_state.clasificacion_loaded = True
                    st.success(f"✅ **{len(df_procesado)}** productos clasificados exitosamente")
                else:
                    st.error("❌ El archivo no contiene datos válidos para clasificar.")
                    st.session_state.clasificacion_loaded = False
            except Exception as e:
                st.error(f"❌ Error al procesar: {str(e)}")
                st.session_state.clasificacion_loaded = False
    
    if not st.session_state.clasificacion_loaded:
        st.info("👆 **Sube un archivo** para comenzar el análisis.")
        with st.expander("📋 Ver formato esperado"):
            ejemplo_df = pd.DataFrame({
                'PRODUCTO': [
                    'AERO GIRLS SS FASHION GRAPHICS TENDER YELLOW XLARGE BABY TEE',
                    'AERO WOMEN DENIM JACKET BLUE M',
                    'MENS COTTON T-SHIRT BLACK L',
                    'KIDS SUMMER SHORTS RED S'
                ]
            })
            st.dataframe(ejemplo_df, use_container_width=True)
            st.markdown("""
            **Extracción automática:**
            - **Género**: "AERO GIRLS" → Mujer
            - **Descripción**: "SS FASHION GRAPHICS TENDER"
            - **Color**: "YELLOW"
            - **Talla**: "XLARGE" → XL
            """)
        
        st.markdown("---")
        st.subheader("🧠 Demo: Probar Clasificador")
        producto_demo = st.text_input(
            "Ingresa nombre de producto",
            "AERO GIRLS SS FASHION GRAPHICS TENDER YELLOW XLARGE BABY TEE",
            key="input_demo_clasificador"
        )
        if st.button("🔍 Clasificar", key="btn_demo_clasificar"):
            classifier = TextileClassifier()
            resultado = classifier.classify_product(producto_demo)
            st.markdown("#### 🏷️ Resultado:")
            cols = st.columns(4)
            campos = [
                ("Género (Raw)", resultado['Genero_Raw'], "🏷️"),
                ("Género", resultado['Genero'], "👤"),
                ("Descripción", resultado['Descripcion'], "📝"),
                ("Categoría", resultado['Categoria'], "👕"),
                ("Color", resultado['Color'], "🎨"),
                ("Talla", resultado['Talla'], "📏"),
                ("Material", resultado['Material'], "🧵"),
                ("Estilo", resultado['Estilo'], "✨")
            ]
            for i, (label, value, icon) in enumerate(campos):
                with cols[i % 4]:
                    st.metric(f"{icon} {label}", value if value else "N/A")
        return
    
    data = st.session_state.clasificacion_data
    if data.empty:
        st.error("No hay datos para mostrar.")
        return
    
    total_unidades = int(data['CANTIDAD'].sum()) if 'CANTIDAD' in data.columns else len(data)
    
    col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
    with col_k1:
        st.metric("📦 Total Productos", f"{len(data):,}")
    with col_k2:
        st.metric("📊 Unidades Totales", f"{total_unidades:,}")
    with col_k3:
        if 'Genero' in data.columns:
            gen_dist = data['Genero'].value_counts()
            st.metric("👤 Género Top", gen_dist.index[0] if len(gen_dist) > 0 else "N/A")
    with col_k4:
        if 'Color' in data.columns:
            col_dist = data['Color'].value_counts()
            st.metric("🎨 Color Top", col_dist.index[0] if len(col_dist) > 0 else "N/A")
    with col_k5:
        if 'Talla' in data.columns:
            talla_dist = data['Talla'].value_counts()
            st.metric("📏 Talla Top", talla_dist.index[0] if len(talla_dist) > 0 else "N/A")
    
    st.markdown("---")
    st.subheader("📈 Análisis por Dimensiones")
    
    tab_dims = st.tabs(["🏪 Por Tienda/Bodega", "🎨 Por Color", "📏 Por Talla", "👤 Por Género", "📋 Tabla Dinámica"])
    
    cantidad_col = 'CANTIDAD' if 'CANTIDAD' in data.columns else None
    bodega_col = None
    for col in ['BODEGA_RECIBE', 'Bodega Recibe', 'Bodega Destino', 'Sucursal Destino']:
        if col in data.columns:
            bodega_col = col
            break
    
    # Tab 1: Por Tienda/Bodega
    with tab_dims[0]:
        st.markdown("### 🏪 Análisis por Tienda/Bodega")
        if bodega_col:
            if cantidad_col:
                tienda_stats = data.groupby(bodega_col).agg({cantidad_col: 'sum', 'PRODUCTO': 'count'}).reset_index()
                tienda_stats.columns = ['Tienda', 'Unidades', 'Productos']
                tienda_stats = tienda_stats.sort_values('Unidades', ascending=False)
            else:
                tienda_stats = data.groupby(bodega_col).size().reset_index(name='Productos')
                tienda_stats.columns = ['Tienda', 'Productos']
                tienda_stats = tienda_stats.sort_values('Productos', ascending=False)
            
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                fig = px.bar(
                    tienda_stats.head(15),
                    x='Tienda',
                    y='Unidades' if cantidad_col else 'Productos',
                    title="Distribución por Tienda",
                    color='Unidades' if cantidad_col else 'Productos',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            with col_t2:
                st.dataframe(tienda_stats.head(20), use_container_width=True, height=500)
            
            if 'Genero' in data.columns and cantidad_col:
                pivot_tienda_genero = pd.pivot_table(
                    data, values=cantidad_col, index=bodega_col, columns='Genero',
                    aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL'
                )
                st.dataframe(pivot_tienda_genero.style.format('{:,.0f}'), use_container_width=True)
        else:
            st.warning("No se encontró columna de tienda/bodega en los datos.")
    
    # Tab 2: Por Color
    with tab_dims[1]:
        st.markdown("### 🎨 Análisis por Color")
        if 'Color' in data.columns:
            if cantidad_col:
                color_stats = data.groupby('Color').agg({cantidad_col: ['sum', 'count'], 'PRODUCTO': 'nunique'}).reset_index()
                color_stats.columns = ['Color', 'Unidades', 'Productos', 'SKUs Únicos']
                color_stats = color_stats.sort_values('Unidades', ascending=False)
            else:
                color_stats = data.groupby('Color').agg({'PRODUCTO': ['count', 'nunique']}).reset_index()
                color_stats.columns = ['Color', 'Productos', 'SKUs Únicos']
                color_stats = color_stats.sort_values('Productos', ascending=False)
            
            col_c1, col_c2 = st.columns([2, 1])
            with col_c1:
                fig = px.pie(color_stats.head(15), values='Unidades' if cantidad_col else 'Productos', names='Color', title="Top 15 Colores", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            with col_c2:
                st.dataframe(color_stats.style.format({'Unidades': '{:,}', 'Productos': '{:,}', 'SKUs Únicos': '{:,}'}), use_container_width=True, height=400)
            
            if 'Talla' in data.columns and cantidad_col:
                pivot_color_talla = pd.pivot_table(
                    data, values=cantidad_col, index='Color', columns='Talla',
                    aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL'
                )
                st.dataframe(pivot_color_talla.style.format('{:,.0f}'), use_container_width=True)
        else:
            st.warning("No hay datos de color disponibles.")
    
    # Tab 3: Por Talla
    with tab_dims[2]:
        st.markdown("### 📏 Análisis por Talla")
        if 'Talla' in data.columns:
            talla_order = ['2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', 'Única']
            if cantidad_col:
                talla_stats = data.groupby('Talla').agg({cantidad_col: ['sum', 'count'], 'PRODUCTO': 'nunique'}).reset_index()
                talla_stats.columns = ['Talla', 'Unidades', 'Productos', 'SKUs Únicos']
            else:
                talla_stats = data.groupby('Talla').agg({'PRODUCTO': ['count', 'nunique']}).reset_index()
                talla_stats.columns = ['Talla', 'Productos', 'SKUs Únicos']
            
            talla_stats['Talla_Order'] = talla_stats['Talla'].apply(lambda x: talla_order.index(x) if x in talla_order else 999)
            talla_stats = talla_stats.sort_values('Talla_Order')
            
            col_ta1, col_ta2 = st.columns([2, 1])
            with col_ta1:
                fig = px.bar(talla_stats, x='Talla', y='Unidades' if cantidad_col else 'Productos', title="Distribución por Talla", color='Unidades' if cantidad_col else 'Productos', color_continuous_scale='Plasma')
                st.plotly_chart(fig, use_container_width=True)
            with col_ta2:
                st.dataframe(talla_stats[['Talla', 'Unidades' if cantidad_col else 'Productos', 'SKUs Únicos']].style.format({'Unidades': '{:,}', 'Productos': '{:,}', 'SKUs Únicos': '{:,}'}), use_container_width=True, height=400)
            
            if 'Genero' in data.columns and cantidad_col:
                pivot_talla_genero = pd.pivot_table(
                    data, values=cantidad_col, index='Talla', columns='Genero',
                    aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL'
                )
                pivot_talla_genero = pivot_talla_genero.reindex([t for t in talla_order if t in pivot_talla_genero.index] + [t for t in pivot_talla_genero.index if t not in talla_order])
                st.dataframe(pivot_talla_genero.style.format('{:,.0f}'), use_container_width=True)
        else:
            st.warning("No hay datos de talla disponibles.")
    
    # Tab 4: Por Género
    with tab_dims[3]:
        st.markdown("### 👤 Análisis por Género")
        if 'Genero' in data.columns:
            if cantidad_col:
                genero_stats = data.groupby('Genero').agg({cantidad_col: ['sum', 'count'], 'PRODUCTO': 'nunique'}).reset_index()
                genero_stats.columns = ['Género', 'Unidades', 'Productos', 'SKUs Únicos']
                genero_stats = genero_stats.sort_values('Unidades', ascending=False)
            else:
                genero_stats = data.groupby('Genero').agg({'PRODUCTO': ['count', 'nunique']}).reset_index()
                genero_stats.columns = ['Género', 'Productos', 'SKUs Únicos']
                genero_stats = genero_stats.sort_values('Productos', ascending=False)
            
            col_g1, col_g2 = st.columns([2, 1])
            with col_g1:
                fig = px.pie(genero_stats, values='Unidades' if cantidad_col else 'Productos', names='Género', title="Distribución por Género", color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            with col_g2:
                st.dataframe(genero_stats.style.format({'Unidades': '{:,}', 'Productos': '{:,}', 'SKUs Únicos': '{:,}'}), use_container_width=True, height=300)
            
            if 'Categoria' in data.columns and cantidad_col:
                pivot_gen_cat = pd.pivot_table(
                    data, values=cantidad_col, index='Genero', columns='Categoria',
                    aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL'
                )
                st.dataframe(pivot_gen_cat.style.format('{:,.0f}'), use_container_width=True)
                
                gen_cat_data = data.groupby(['Genero', 'Categoria']).agg({cantidad_col: 'sum'}).reset_index()
                gen_cat_data.columns = ['Género', 'Categoría', 'Cantidad']
                fig_stack = px.bar(gen_cat_data, x='Género', y='Cantidad', color='Categoría', title="Distribución por Género y Categoría", barmode='stack')
                st.plotly_chart(fig_stack, use_container_width=True)
        else:
            st.warning("No hay datos de género disponibles.")
    
    # Tab 5: Tabla Dinámica Personalizada
    with tab_dims[4]:
        st.markdown("### 📋 Tabla Dinámica Personalizada")
        available_dims = []
        if 'Genero' in data.columns:
            available_dims.append('Genero')
        if 'Color' in data.columns:
            available_dims.append('Color')
        if 'Talla' in data.columns:
            available_dims.append('Talla')
        if 'Categoria' in data.columns:
            available_dims.append('Categoria')
        if bodega_col:
            available_dims.append('Tienda/Bodega')
        
        if available_dims:
            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
            filas = col_cfg1.selectbox("Filas (índice)", available_dims, index=0)
            columnas = col_cfg2.selectbox("Columnas", available_dims, index=min(1, len(available_dims)-1) if len(available_dims) > 1 else 0)
            valores = col_cfg3.selectbox("Valores a agregar", ['Cantidad (suma)' if cantidad_col else 'Conteo de productos', 'Conteo de productos', 'SKUs únicos'], index=0)
            
            if filas and columnas and filas != columnas:
                fila_col = 'BODEGA_RECIBE' if filas == 'Tienda/Bodega' and 'BODEGA_RECIBE' in data.columns else filas
                col_col = 'BODEGA_RECIBE' if columnas == 'Tienda/Bodega' and 'BODEGA_RECIBE' in data.columns else columnas
                
                if 'Cantidad' in valores and cantidad_col:
                    agg_val = cantidad_col
                    agg_func = 'sum'
                elif 'SKUs' in valores:
                    agg_val = 'PRODUCTO'
                    agg_func = 'nunique'
                else:
                    agg_val = cantidad_col if cantidad_col else 'PRODUCTO'
                    agg_func = 'sum' if cantidad_col else 'count'
                
                try:
                    pivot_custom = pd.pivot_table(
                        data, values=agg_val, index=fila_col, columns=col_col,
                        aggfunc=agg_func, fill_value=0, margins=True, margins_name='TOTAL'
                    )
                    st.dataframe(pivot_custom.style.format('{:,.0f}'), use_container_width=True)
                    csv = pivot_custom.to_csv()
                    st.download_button("📥 Descargar CSV", data=csv, file_name=f"tabla_dinamica_{filas}_vs_{columnas}.csv", mime="text/csv")
                except Exception as e:
                    st.error(f"Error generando tabla: {str(e)}")
            else:
                st.info("Selecciona dimensiones diferentes para filas y columnas.")
        else:
            st.warning("No hay dimensiones disponibles para crear tablas dinámicas.")
    
    # Filtros y tabla detalle
    st.markdown("---")
    st.subheader("🔍 Filtros y Detalle")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    filtro_gen = 'Todos'
    filtro_col = 'Todos'
    filtro_talla = 'Todos'
    filtro_bod = 'Todas'
    
    with col_f1:
        if 'Genero' in data.columns:
            gen_opts = ['Todos'] + sorted(data['Genero'].unique())
            filtro_gen = st.selectbox("👤 Género", gen_opts, key="filtro_gen")
    with col_f2:
        if 'Color' in data.columns:
            col_opts = ['Todos'] + sorted(data['Color'].unique())
            filtro_col = st.selectbox("🎨 Color", col_opts, key="filtro_col")
    with col_f3:
        if 'Talla' in data.columns:
            talla_opts = ['Todos'] + sorted(data['Talla'].unique())
            filtro_talla = st.selectbox("📏 Talla", talla_opts, key="filtro_talla")
    with col_f4:
        if bodega_col:
            bod_opts = ['Todas'] + sorted(data[bodega_col].unique())
            filtro_bod = st.selectbox("🏪 Tienda", bod_opts, key="filtro_bod")
    
    filtered = data.copy()
    if filtro_gen != 'Todos' and 'Genero' in filtered.columns:
        filtered = filtered[filtered['Genero'] == filtro_gen]
    if filtro_col != 'Todos' and 'Color' in filtered.columns:
        filtered = filtered[filtered['Color'] == filtro_col]
    if filtro_talla != 'Todos' and 'Talla' in filtered.columns:
        filtered = filtered[filtered['Talla'] == filtro_talla]
    if filtro_bod != 'Todas' and bodega_col:
        filtered = filtered[filtered[bodega_col] == filtro_bod]
    
    st.markdown(f"**📋 Mostrando {len(filtered)} registros filtrados de {len(data)} totales**")
    display_cols = [c for c in ['PRODUCTO', 'Genero_Raw', 'Genero', 'Descripcion', 'Categoria', 'Color', 'Talla', 'CANTIDAD', 'BODEGA_RECIBE', 'FECHA'] if c in filtered.columns]
    if not display_cols:
        display_cols = filtered.columns.tolist()[:10]
    
    st.dataframe(
        filtered[display_cols].sort_values(by='CANTIDAD' if 'CANTIDAD' in filtered.columns else display_cols[0], ascending=False),
        use_container_width=True, height=400
    )
    
    if len(filtered) > 0:
        st.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered.to_excel(writer, sheet_name='Datos Filtrados', index=False)
            resumen_export = []
            if 'Genero' in filtered.columns:
                resumen_export.append(['Géneros', filtered['Genero'].nunique()])
            if 'Color' in filtered.columns:
                resumen_export.append(['Colores', filtered['Color'].nunique()])
            if 'Talla' in filtered.columns:
                resumen_export.append(['Tallas', filtered['Talla'].nunique()])
            if 'CANTIDAD' in filtered.columns:
                resumen_export.append(['Total Unidades', int(filtered['CANTIDAD'].sum())])
            resumen_export.append(['Total Productos', len(filtered)])
            pd.DataFrame(resumen_export, columns=['Métrica', 'Valor']).to_excel(writer, sheet_name='Resumen', index=False)
        st.download_button(
            label="📥 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f"clasificacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# ==============================================================================
# MÓDULO PRINCIPAL: DASHBOARD LOGÍSTICO (show_logistica)
# ==============================================================================
# ==============================================================================
# MÓDULO PRINCIPAL: DASHBOARD LOGÍSTICO (show_logistica) - CORREGIDO
# ==============================================================================
def show_logistica():
    """Dashboard logístico completo con diseño mejorado."""
    add_back_button(key="back_logistica")
    show_module_header(
        "📦 Dashboard Logístico",
        "Control de transferencias y distribución de mercadería"
    )

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    # Tabs para organizar contenido
    tab1, tab2 = st.tabs(["📊 Transferencias Diarias", "🧠 Clasificación Inteligente"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)

        # Carga de archivo
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            uploaded = st.file_uploader(
                "Subir archivo de transferencias (Excel)",
                type=['xlsx', 'xls'],
                key="log_upload"
            )
        with col_u2:
            if st.button("🔄 Limpiar", use_container_width=True):
                st.rerun()

        if uploaded:
            try:
                df = pd.read_excel(uploaded)
                st.success(f"✅ Archivo cargado: {len(df)} registros")

                with st.expander("🔍 Vista previa", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)

                # Verificar columnas requeridas
                required = ['Secuencial']
                has_destino = any(c in df.columns for c in ['Sucursal Destino', 'Bodega Destino'])
                has_cantidad = any(c in df.columns for c in ['Cantidad Prendas', 'Cantidad'])

                missing_required = [c for c in required if c not in df.columns]

                if missing_required:
                    st.error(f"❌ Faltan columnas requeridas: {missing_required}")
                elif not has_destino:
                    st.error("❌ No se encontró columna de destino")
                elif not has_cantidad:
                    st.error("❌ No se encontró columna de cantidad")
                else:
                    # Procesar
                    resultado = procesar_transferencias(df)

                    # --- MÉTRICAS PRINCIPALES (estilo imagen) ---
                    total_unidades = resultado['total_unidades']
                    total_transferencias = resultado['total_transferencias']
                    promedio_x_transf = total_unidades / total_transferencias if total_transferencias > 0 else 0

                    # Categorías activas (con unidades > 0)
                    categorias_activas = sum(1 for v in resultado['por_categoria'].values() if v > 0)
                    total_categorias = len(CATEGORIAS_TRANSFERENCIA)

                    # Porcentaje de Fundas
                    fundas_unidades = resultado['por_categoria'].get('Fundas', 0)
                    pct_fundas = (fundas_unidades / total_unidades * 100) if total_unidades > 0 else 0

                    # Mostrar KPIs en cards
                    st.markdown("---")
                    st.markdown("### 📊 Resumen General")
                    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                    with col_k1:
                        st.metric("📦 Total General", f"{total_unidades:,}")
                    with col_k2:
                        st.metric("📊 Promedio x Transferencia", f"{promedio_x_transf:.0f}")
                    with col_k3:
                        st.metric("🏷️ Categorías Activas", f"{categorias_activas}/{total_categorias}")
                    with col_k4:
                        st.metric("📎 % Fundas", f"{pct_fundas:.1f}%")

                    # Gráfico de pastel (distribución por categoría)
                    st.markdown("---")
                    st.subheader("📈 Distribución por Categoría")
                    col_g1, col_g2 = st.columns([2, 1])
                    with col_g1:
                        df_pie = pd.DataFrame({
                            'Categoria': list(resultado['por_categoria'].keys()),
                            'Unidades': list(resultado['por_categoria'].values())
                        })
                        df_pie = df_pie[df_pie['Unidades'] > 0]
                        fig = px.pie(
                            df_pie,
                            values='Unidades',
                            names='Categoria',
                            hole=0.4,
                            title="Distribución por Categoría",
                            color='Categoria',
                            color_discrete_map={
                                'Price Club': CATEGORIAS_TRANSFERENCIA['Price Club']['color'],
                                'Tiendas': CATEGORIAS_TRANSFERENCIA['Tiendas']['color'],
                                'Ventas por Mayor': CATEGORIAS_TRANSFERENCIA['Ventas por Mayor']['color'],
                                'Tienda Web': CATEGORIAS_TRANSFERENCIA['Tienda Web']['color'],
                                'Fallas': CATEGORIAS_TRANSFERENCIA['Fallas']['color'],
                                'Fundas': CATEGORIAS_TRANSFERENCIA['Fundas']['color']
                            }
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)

                    with col_g2:
                        st.markdown("#### Detalle por Categoría")
                        for cat, info in resultado['detalle_categoria'].items():
                            if info['cantidad'] > 0:
                                color = CATEGORIAS_TRANSFERENCIA.get(cat, {}).get('color', '#60A5FA')
                                icon = CATEGORIAS_TRANSFERENCIA.get(cat, {}).get('icon', '📌')
                                st.markdown(f"""
                                <div style="background: {color}15; border-left: 4px solid {color}; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;">
                                    <div style="font-weight: 700; color: white;">{icon} {cat}</div>
                                    <div style="font-size: 0.85rem; color: #94A3B8;">
                                        {info['cantidad']:,} unidades • {info['transferencias']} transf. • {info['sucursales_unicas']} suc.
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                    # --- KPIs por Categoría con comparativa (estilo imagen) ---
                    st.markdown("---")
                    st.subheader("🏆 KPIs por Categoría")

                    # Definir sucursales esperadas (según imagen, se pueden parametrizar)
                    expected_stores = {
                        'Price Club': 5,
                        'Tiendas': 42,
                        'Ventas por Mayor': 1,
                        'Tienda Web': 1,
                        'Fallas': 1,
                        'Fundas': 0  # No aplica
                    }

                    # Crear columnas para las tarjetas (3 por fila)
                    cats = list(CATEGORIAS_TRANSFERENCIA.keys())
                    for i in range(0, len(cats), 3):
                        cols = st.columns(3)
                        for j in range(3):
                            if i + j < len(cats):
                                cat = cats[i + j]
                                info = resultado['detalle_categoria'].get(cat, {'cantidad': 0, 'sucursales_unicas': 0})
                                cantidad = info['cantidad']
                                suc_actual = info['sucursales_unicas']
                                suc_esperada = expected_stores.get(cat, 0)
                                icon = CATEGORIAS_TRANSFERENCIA[cat]['icon']
                                color = CATEGORIAS_TRANSFERENCIA[cat]['color']

                                with cols[j]:
                                    # Construir texto comparativo
                                    if cat == 'Fundas':
                                        comp_text = "Múltiplos de 100 ≥ 500 unidades"
                                    else:
                                        comp_text = f"{suc_actual} sucursales | {suc_esperada} esperadas"

                                    st.markdown(f"""
                                    <div style="background: {color}10; border: 1px solid {color}30; border-radius: 16px; padding: 20px; margin-bottom: 15px;">
                                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                            <span style="font-size: 2rem;">{icon}</span>
                                            <span style="font-weight: 700; font-size: 1.2rem; color: {color};">{cat.upper()}</span>
                                        </div>
                                        <div style="font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 5px;">
                                            {cantidad:,}
                                        </div>
                                        <div style="font-size: 0.9rem; color: #94A3B8;">
                                            {comp_text}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # Tabla detalle
                    st.markdown("---")
                    st.subheader("📋 Detalle de Transferencias")
                    destino_col = 'Sucursal Destino' if 'Sucursal Destino' in resultado['df_procesado'].columns else 'Bodega Destino'
                    df_detalle = resultado['df_procesado'][['Secuencial', destino_col, 'Cantidad_Entera', 'Categoria']].copy()
                    df_detalle.columns = ['Secuencial', 'Destino', 'Cantidad', 'Categoría']
                    st.dataframe(df_detalle, use_container_width=True, height=300)

                    # Exportar
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df_detalle.to_excel(writer, sheet_name='Detalle', index=False)
                        pd.DataFrame(resultado['detalle_categoria']).T.to_excel(writer, sheet_name='Resumen')

                    st.download_button(
                        "📥 Descargar Excel",
                        buffer.getvalue(),
                        f"transferencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"❌ Error procesando archivo: {str(e)}")

        else:
            st.info("👆 **Sube un archivo Excel** con las columnas: `Secuencial`, `Sucursal Destino`/`Bodega Destino`, `Cantidad Prendas`/`Cantidad`. El sistema clasificará automáticamente en categorías (Price Club, Tiendas, Web, etc.).")

    with tab2:
        mostrar_clasificacion_inteligente()

    st.markdown('</div>', unsafe_allow_html=True)
# ==============================================================================
# MÓDULO: GESTIÓN DE EQUIPO
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
    
    # Estructura base del personal
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
    
    # Cargar trabajadores desde la base de datos
    try:
        trabajadores = local_db.query('trabajadores')
        if trabajadores is None:
            trabajadores = []
        # Inicializar estructura base si no hay datos
        if not trabajadores:
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Estructura Organizacional", "➕ Gestionar Personal", "📊 Estadisticas", "⚙️ Configuracion"])
    
    # --- Tab 1: Estructura Organizacional ---
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
    
    # --- Tab 2: Gestionar Personal ---
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
                        # Mostrar tabla de trabajadores con opción de eliminar adicionales
                        for trab in trabajadores_area_actual:
                            col_d1, col_d2, col_d3, col_d4, col_d5, col_d6 = st.columns([1, 3, 2, 2, 1, 1])
                            with col_d1:
                                st.write(f"**{trab.get('id', '')}**")
                            with col_d2:
                                st.write(trab.get('nombre', ''))
                            with col_d3:
                                st.write(trab.get('cargo', ''))
                            with col_d4:
                                st.write(trab.get('subarea', '-'))
                            with col_d5:
                                tipo = "Base" if trab.get('es_base', False) else "Adicional"
                                tipo_color = "🟢" if tipo == "Base" else "🔵"
                                st.write(f"{tipo_color} {tipo}")
                            with col_d6:
                                if not trab.get('es_base', False):
                                    trabajador_id = trab.get('id')
                                    if st.button("🗑️", key=f"eliminar_{area}_{trabajador_id}"):
                                        try:
                                            local_db.delete('trabajadores', int(trabajador_id))
                                            st.success(f"✅ Trabajador {trab.get('nombre')} eliminado de {area}")
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
    
    # --- Tab 3: Estadisticas ---
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
                    base = sum(len(p) for p in estructura_base.values())
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
    
    # --- Tab 4: Configuracion ---
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
# FUNCIONES AUXILIARES PARA GENERAR GUÍAS
# ==============================================================================

def descargar_logo(url):
    """Descarga un logo desde una URL y retorna los bytes."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        st.warning(f"No se pudo descargar el logo: {str(e)}")
        return None


def generar_qr_bytes(url_pedido):
    """Genera un código QR en bytes a partir de una URL."""
    try:
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url_pedido)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        img_byte_arr = io.BytesIO()
        img_qr.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()
    except Exception:
        return None


def mostrar_vista_previa_guia(guia_data):
    """Muestra una vista previa de la guía en formato visual."""
    st.markdown("---")
    st.subheader(f"👁️ Vista Previa de la Guía {guia_data['numero']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        **🏢 Marca:** {guia_data['marca']}  
        **👤 Remitente:** {guia_data['remitente']}  
        **📍 Dir. Remitente:** {guia_data['direccion_remitente']}
        """)
    with col2:
        st.markdown(f"""
        **👤 Destinatario:** {guia_data['destinatario']}  
        **📞 Teléfono:** {guia_data.get('telefono_destinatario', 'No especificado')}  
        **📍 Dirección:** {guia_data['direccion_destinatario']}  
        **🏪 Tienda:** {guia_data.get('tienda_destino', 'No especificada')}
        """)
    
    st.markdown(f"**🔗 URL Pedido:** {guia_data.get('url_pedido', 'No especificada')}")
    st.markdown(f"**📅 Fecha:** {guia_data['fecha_emision']} | **Estado:** {guia_data.get('estado', 'Vista Previa')}")
    
    if guia_data.get('qr_bytes'):
        col_q1, col_q2, col_q3 = st.columns([1, 2, 1])
        with col_q2:
            st.image(guia_data['qr_bytes'], caption="Código QR", width=150)


def generar_pdf_profesional(guia_data):
    """
    Genera una guía A4 vertical con diseño limpio, colores Aeropostale,
    iconos y espacio para firmas.
    """
    buffer = io.BytesIO()
    
    from reportlab.lib.pagesizes import A4
    page_width, page_height = A4
    margen = 1.5 * cm
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=margen,
        rightMargin=margen,
        topMargin=margen,
        bottomMargin=margen
    )
    
    styles = getSampleStyleSheet()
    
    color_primario = HexColor("#0033A0")
    color_acento = HexColor("#E4002B")
    color_texto = HexColor("#1E293B")
    color_texto_suave = HexColor("#64748B")
    color_fondo = HexColor("#F8FAFC")
    
    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=color_primario,
        alignment=TA_CENTER,
        spaceAfter=2,
        leading=24
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=color_texto_suave,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=18
    )
    
    tienda_style = ParagraphStyle(
        'Tienda',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=color_primario,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=18
    )
    
    seccion_title_style = ParagraphStyle(
        'SeccionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=color_acento,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=2,
        leading=13
    )
    
    contenido_style = ParagraphStyle(
        'Contenido',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=color_texto,
        alignment=TA_LEFT,
        spaceAfter=2,
        leading=12
    )
    
    valor_destacado_style = ParagraphStyle(
        'ValorDestacado',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=color_primario,
        alignment=TA_RIGHT,
        spaceAfter=2
    )
    
    fecha_hora_style = ParagraphStyle(
        'FechaHora',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=color_texto_suave,
        alignment=TA_RIGHT,
        spaceAfter=0,
        leading=10
    )
    
    leyenda_qr_style = ParagraphStyle(
        'LeyendaQR',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=color_primario,
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=0
    )
    
    firma_label_style = ParagraphStyle(
        'FirmaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=color_primario,
        alignment=TA_CENTER,
        spaceBefore=10
    )
    
    firma_linea_style = ParagraphStyle(
        'FirmaLinea',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=color_texto_suave,
        alignment=TA_CENTER
    )

    contenido = []
    
    # Título
    contenido.append(Paragraph("🚚 GUÍA DE REMISIÓN", titulo_principal))
    contenido.append(Paragraph(f"Centro de Distribución {guia_data['marca']}", subtitulo_style))
    contenido.append(Spacer(1, 0.2*cm))
    
    # Nombre tienda
    tienda_nombre = guia_data.get('tienda_destino', 'Tienda no especificada')
    contenido.append(Paragraph(tienda_nombre, tienda_style))
    contenido.append(Spacer(1, 0.3*cm))
    
    # ========== DATOS DE LA GUÍA (ARRIBA, ALINEADOS A LA DERECHA) ==========
    datos_tabla = Table(
        [[Paragraph(f"N° Guía: {guia_data['numero']}", valor_destacado_style)],
         [Paragraph(f"Fecha: {guia_data['fecha_emision']}", fecha_hora_style)],
         [Paragraph(f"Hora: {datetime.now().strftime('%H:%M')}", fecha_hora_style)]],
        colWidths=[6*cm]
    )
    datos_tabla.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    # Envolvemos en una tabla de una sola celda para poder alinear a la derecha dentro del ancho total
    datos_fila = Table([[datos_tabla]], colWidths=[page_width - 2*margen])
    datos_fila.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
    ]))
    contenido.append(datos_fila)
    contenido.append(Spacer(1, 0.3*cm))
    
    # ========== BLOQUE LOGO + QR (ahora alineados horizontalmente) ==========
    logo_bytes = st.session_state.logos.get(guia_data['marca'])
    if not logo_bytes:
        logo_url = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg" if guia_data['marca'] == "Fashion Club" else "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"
        logo_bytes = descargar_logo(logo_url)
        if logo_bytes:
            st.session_state.logos[guia_data['marca']] = logo_bytes
    
    # Bloque izquierdo: Logo y Marca
    if logo_bytes:
        try:
            logo_img = Image(io.BytesIO(logo_bytes), width=5.0*cm, height=5.0*cm)
            logo_cell = logo_img
        except:
            logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", contenido_style)
    else:
        logo_cell = Paragraph(f"<b>{guia_data['marca']}</b>", contenido_style)
    
    marca_texto = Paragraph(f"<b>{guia_data['marca']}</b>", contenido_style)
    
    bloque_izq = Table(
        [[logo_cell], [marca_texto]],
        colWidths=[5*cm]
    )
    bloque_izq.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    # Bloque derecho: solo QR y leyenda (sin los datos)
    qr_bytes = guia_data.get("qr_bytes")
    if qr_bytes:
        try:
            qr_img = Image(io.BytesIO(qr_bytes), width=5.0*cm, height=5.0*cm)
        except:
            qr_img = Paragraph("[QR]", contenido_style)
        qr_leyenda = Paragraph("📱 Escanea aquí tu transferencia", leyenda_qr_style)
        bloque_qr = Table(
            [[qr_img], [qr_leyenda]],
            colWidths=[4*cm]
        )
        bloque_qr.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
    else:
        bloque_qr = Paragraph("", contenido_style)
    
    # Columna derecha: solo el QR
    col_derecha = Table(
        [[bloque_qr]],
        colWidths=[4.5*cm]
    )
    col_derecha.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    # Fila con logo a la izquierda y QR a la derecha (misma altura)
    fila_logo_qr = Table(
        [[bloque_izq, "", col_derecha]],
        colWidths=[5*cm, 9*cm, 4.5*cm]
    )
    fila_logo_qr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    contenido.append(fila_logo_qr)
    contenido.append(Spacer(1, 0.5*cm))
    
    # ========== SECCIÓN DESTINATARIO / REMITENTE (sin cambios) ==========
    dest_data = [
        [Paragraph("👤 DESTINATARIO", seccion_title_style)],
        [Paragraph(f"{guia_data['destinatario']}", contenido_style)],
        [Paragraph(f"📞 {guia_data.get('telefono_destinatario', 'No especificado')}", contenido_style)],
        [Paragraph(f"📍 {guia_data['direccion_destinatario']}", contenido_style)]
    ]
    tabla_dest = Table(dest_data, colWidths=[8.5*cm])
    tabla_dest.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), color_fondo),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (0,0), 4),
        ('BOTTOMPADDING', (-1,0), (-1,0), 4),
    ]))
    
    rem_data = [
        [Paragraph("🏢 REMITENTE", seccion_title_style)],
        [Paragraph(f"{guia_data['remitente']}", contenido_style)],
        [Paragraph(f"📍 {guia_data['direccion_remitente']}", contenido_style)]
    ]
    tabla_rem = Table(rem_data, colWidths=[8.5*cm])
    tabla_rem.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), color_fondo),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (0,0), 4),
        ('BOTTOMPADDING', (-1,0), (-1,0), 4),
    ]))
    
    contacto_fila = Table(
        [[tabla_dest, tabla_rem]],
        colWidths=[9*cm, 9*cm]
    )
    contacto_fila.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (0,0), 0),
        ('RIGHTPADDING', (0,0), (0,0), 4),
        ('LEFTPADDING', (1,0), (1,0), 4),
        ('RIGHTPADDING', (1,0), (1,0), 0),
    ]))
    contenido.append(contacto_fila)
    contenido.append(Spacer(1, 0.8*cm))
    
    # Sección de firmas
    contenido.append(Spacer(1, 0.3*cm))
    firma_tabla = Table(
        [[Paragraph("_________________________", firma_linea_style),
          Paragraph("_________________________", firma_linea_style)],
         [Paragraph("Revisado por:", firma_label_style),
          Paragraph("Recontado por:", firma_label_style)]],
        colWidths=[9*cm, 9*cm]
    )
    firma_tabla.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    contenido.append(firma_tabla)
    
    # Pie de página
    contenido.append(Spacer(1, 0.3*cm))
    pie = Paragraph(
        "<font size=7 color='#94A3B8'>Documento generado electrónicamente — Válido sin firma</font>",
        ParagraphStyle('Pie', alignment=TA_CENTER)
    )
    contenido.append(pie)
    
    doc.build(contenido)
    buffer.seek(0)
    return buffer.getvalue()
# ==============================================================================
# MÓDULO: CONTROL DE INVENTARIO (PLACEHOLDER)
# ==============================================================================
#def show_control_inventario():
    """Control de inventario"""
    add_back_button(key="back_inventario")
    show_module_header("📋 Control de Inventario", "Gestion de stock en tiempo real")
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
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================
# MÓDULO: CONTROL DE INVENTARIO (IMPLEMENTADO)
# ==============================================================================
def show_control_inventario():
    """Control de inventario con búsqueda de SKU y reportes."""
    add_back_button(key="back_inventario")
    show_module_header("📋 Control de Inventario", "Gestión de stock en tiempo real")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    # Verificar permisos (aunque ya lo hace el enrutador, doble chequeo)
    if st.session_state.role not in ["Administrador", "Bodega"]:
        st.error("⛔ Acceso denegado. Solo Administrador y Bodega pueden acceder a este módulo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Inicializar estado para almacenar el DataFrame
    if 'inventario_df' not in st.session_state:
        st.session_state.inventario_df = None
    if 'inventario_tiendas' not in st.session_state:
        st.session_state.inventario_tiendas = []

    st.sidebar.header("📁 Carga de Inventario")
    uploaded_file = st.sidebar.file_uploader(
        "Selecciona archivo Excel de inventario",
        type=['xlsx', 'xls'],
        key="inv_upload"
    )

    if uploaded_file is not None:
        try:
            # Cargar datos (cachear para no recargar)
            if st.session_state.inventario_df is None or st.sidebar.button("🔄 Recargar archivo"):
                with st.spinner("Cargando archivo de inventario..."):
                    df = pd.read_excel(uploaded_file)
                    # Limpiar nombres de columna
                    df.columns = df.columns.str.strip().str.upper()
                    st.session_state.inventario_df = df
                    
                    # Detectar columnas de tiendas (entre "MATRIZ" y "TOTAL" o similar)
                    cols = df.columns.tolist()
                    start_idx = 0
                    end_idx = len(cols)
                    if "MATRIZ" in cols:
                        start_idx = cols.index("MATRIZ") + 1
                    if "TOTAL" in cols:
                        end_idx = cols.index("TOTAL")
                    tiendas_cols = cols[start_idx:end_idx]
                    # Filtrar columnas que probablemente son tiendas (no contengan palabras clave no deseadas)
                    excluir = ['FECHA', 'CODIGO', 'PRODUCTO', 'COLECCION', 'DIVISION', 'DEPARTAMENTO', 'STOCK', 'TOTAL']
                    tiendas_cols = [c for c in tiendas_cols if not any(ex in c for ex in excluir)]
                    st.session_state.inventario_tiendas = tiendas_cols
                    
                    # Procesar fechas si existe columna FECHA COMPRA
                    if 'FECHA COMPRA' in df.columns:
                        df['FECHA_COMPRA_DT'] = pd.to_datetime(df['FECHA COMPRA'], errors='coerce')
                        today = datetime.now()
                        df['DIAS_INVENTARIO'] = (today - df['FECHA_COMPRA_DT']).dt.days
                    
                    st.sidebar.success(f"✅ Archivo cargado: {len(df)} SKUs, {len(tiendas_cols)} tiendas")
        except Exception as e:
            st.error(f"❌ Error al cargar archivo: {str(e)}")
            st.session_state.inventario_df = None

    # Contenido principal
    if st.session_state.inventario_df is not None:
        df = st.session_state.inventario_df
        tiendas = st.session_state.inventario_tiendas

        # Métricas rápidas
        total_skus = len(df)
        total_stock = df[tiendas].sum().sum() if tiendas else 0
        avg_dias = df['DIAS_INVENTARIO'].mean() if 'DIAS_INVENTARIO' in df.columns else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Total SKUs", f"{total_skus:,}")
        col2.metric("📊 Stock Total", f"{total_stock:,.0f}")
        col3.metric("⏳ Días Promedio en Inventario", f"{avg_dias:.1f} días")

        st.markdown("---")

        # Búsqueda de SKU
        st.subheader("🔍 Buscar SKU")
        sku_input = st.text_input("Ingrese el código SKU:", key="sku_search")
        col_b1, col_b2 = st.columns([1, 4])
        with col_b1:
            buscar_btn = st.button("Buscar", type="primary")
        with col_b2:
            if st.button("🔄 Limpiar búsqueda"):
                sku_input = ""
                st.rerun()

        if buscar_btn and sku_input:
            sku = sku_input.strip()
            # Buscar en columna 'CODIGO' (puede variar, intentar varias)
            codigo_col = None
            for col in ['CODIGO', 'COD', 'SKU', 'CODIGO PRODUCTO']:
                if col in df.columns:
                    codigo_col = col
                    break
            if codigo_col is None:
                st.error("No se encontró columna de código (CODIGO, SKU, etc.)")
            else:
                mask = df[codigo_col].astype(str).str.strip() == sku
                if mask.any():
                    producto = df[mask].iloc[0]
                    st.success(f"✅ SKU encontrado: {sku}")
                    
                    # Mostrar información del producto
                    st.markdown("### 📄 Información del Producto")
                    info_cols = ['PRODUCTO', 'COLECCION', 'DIVISION', 'DEPARTAMENTO', 'FECHA COMPRA']
                    available_info = [c for c in info_cols if c in producto.index]
                    if available_info:
                        for col in available_info:
                            st.write(f"**{col.title()}:** {producto[col]}")
                    
                    if 'DIAS_INVENTARIO' in producto.index and pd.notna(producto['DIAS_INVENTARIO']):
                        dias = int(producto['DIAS_INVENTARIO'])
                        color = "red" if dias > 90 else "orange" if dias > 60 else "green"
                        st.markdown(f"**Días en inventario:** <span style='color:{color}; font-weight:bold;'>{dias}</span>", unsafe_allow_html=True)
                    
                    # Mostrar stock por tienda
                    st.markdown("### 🏪 Stock por Tienda")
                    stock_data = []
                    for tienda in tiendas:
                        stock = producto[tienda] if tienda in producto.index else 0
                        if pd.notna(stock) and stock > 0:
                            stock_data.append({"Tienda": tienda, "Stock": int(stock)})
                    
                    if stock_data:
                        stock_df = pd.DataFrame(stock_data)
                        st.dataframe(stock_df, use_container_width=True, hide_index=True)
                        total_unidades = stock_df['Stock'].sum()
                        st.metric("Total Unidades", total_unidades)
                    else:
                        st.info("No hay stock en ninguna tienda.")
                else:
                    st.warning(f"No se encontró el SKU '{sku}'.")

        st.markdown("---")
        st.subheader("📊 Reportes")
        if st.button("Generar Reporte de Productos Lentos (>90 días)"):
            if 'DIAS_INVENTARIO' not in df.columns:
                st.warning("No hay datos de fecha de compra para calcular días en inventario.")
            else:
                slow = df[df['DIAS_INVENTARIO'] > 90].copy()
                if slow.empty:
                    st.success("No hay productos con más de 90 días en inventario.")
                else:
                    # Seleccionar columnas relevantes
                    display_cols = ['CODIGO', 'PRODUCTO', 'DIAS_INVENTARIO'] + tiendas
                    available = [c for c in display_cols if c in slow.columns]
                    slow_display = slow[available].sort_values('DIAS_INVENTARIO', ascending=False)
                    st.dataframe(slow_display, use_container_width=True)
                    
                    # Exportar
                    csv = slow_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Descargar CSV",
                        csv,
                        "productos_lentos.csv",
                        "text/csv"
                    )

    else:
        st.info("👆 **Carga un archivo Excel de inventario** desde la barra lateral para comenzar.")
        with st.expander("📋 Estructura esperada del archivo"):
            st.markdown("""
            El archivo debe contener al menos las siguientes columnas:
            - **CODIGO** (o SKU): identificador único del producto.
            - **PRODUCTO**: descripción.
            - **FECHA COMPRA** (opcional): para calcular días en inventario.
            - Columnas con nombres de tiendas (ej: "MATRIZ", "MALL DEL SOL", etc.) que contengan el stock.
            
            Ejemplo:
            | CODIGO | PRODUCTO | FECHA COMPRA | MATRIZ | MALL DEL SOL | ... | TOTAL |
            |--------|----------|--------------|--------|--------------|-----|-------|
            | 12345  | Camisa   | 2025-01-01   | 10     | 5            | ... | 15    |
            """)

    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# MÓDULO: REPORTES AVANZADOS (PLACEHOLDER)
# ==============================================================================
def show_reportes_avanzados():
    """Generador de reportes"""
    add_back_button(key="back_reportes")
    show_module_header("📈 Reportes Avanzados", "Analisis y estadisticas ejecutivas")
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
    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MÓDULO: CONFIGURACIÓN
# ==============================================================================
def show_configuracion():
    """Configuracion del sistema"""
    add_back_button(key="back_config")
    show_module_header("⚙️ Configuracion", "Personalizacion del sistema ERP")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["General", "Usuarios", "Seguridad"])

    with tab1:
        st.header("Configuracion General")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🌐 Configuracion Regional")
            st.selectbox("Zona Horaria", ["America/Guayaquil", "UTC"])
            st.selectbox("Moneda", ["USD", "EUR", "COP"])
            st.selectbox("Idioma", ["Espanol", "Ingles"])
        with col2:
            st.subheader("📊 Configuracion de Reportes")
            st.selectbox("Formato de Fecha", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
            st.slider("Decimales", 0, 4, 2)
            st.selectbox("Separador de Miles", [",", ".", " "])
        if st.button("💾 Guardar Configuracion"):
            st.success("✅ Configuracion guardada exitosamente")

    with tab2:
        st.header("Gestion de Usuarios")
        usuarios = local_db.query("users")
        df_usuarios = pd.DataFrame(usuarios)
        if not df_usuarios.empty:
            st.dataframe(df_usuarios[["username", "role"]], use_container_width=True)

        with st.form("form_usuario"):
            st.subheader("Agregar Nuevo Usuario")
            nuevo_usuario = st.text_input("Nombre de usuario")
            nueva_contrasena = st.text_input("Contrasena", type="password")
            rol = st.selectbox("Rol", ["admin", "user"])

            if st.form_submit_button("➕ Agregar Usuario"):
                if nuevo_usuario and nueva_contrasena:
                    try:
                        local_db.insert(
                            "users",
                            {
                                "username": nuevo_usuario,
                                "role": rol,
                                "password_hash": hash_password(nueva_contrasena),
                            },
                        )
                        st.success(f"✅ Usuario {nuevo_usuario} agregado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    with tab3:
        st.header("Configuracion de Seguridad")
        st.subheader("🔐 Politicas de Contrasena")
        st.slider("Longitud minima de contrasena", 6, 20, 8)
        st.checkbox("Requerir mayusculas", True)
        st.checkbox("Requerir numeros", True)
        st.selectbox("Expiracion de contrasena (dias)", ["30", "60", "90", "Nunca"])

        st.subheader("🔒 Configuracion de Sesion")
        st.slider("Tiempo de inactividad (minutos)", 5, 120, 30)
        st.slider("Maximo de intentos fallidos", 3, 10, 5)

        if st.button("🔒 Aplicar Configuracion de Seguridad"):
            st.success("✅ Configuracion de seguridad aplicada")

    st.markdown("</div>", unsafe_allow_html=True)
  # Mapeo de páginas a funciones
    page_mapping = {
        "Inicio": show_main_page,
        "dashboard_kpis": show_dashboard_kpis,
        "reconciliacion_v8": show_reconciliacion_v8,
        "auditoria_correos": show_auditoria_correos,
        "dashboard_logistico": show_logistica,
        "gestion_equipo": show_gestion_equipo,
        "generar_guias": show_generar_guias,
        "control_inventario": show_control_inventario,
        "reportes_avanzados": show_reportes_avanzados,
        "configuracion": show_configuracion,
    }

    # Ejecutar la página actual
    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

# ==============================================================================
# FUNCIÓN PRINCIPAL main() - ENRUTAMIENTO
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
        "generar_guias": ["Administrador", "Bodega"],
        "control_inventario": ["Administrador", "Bodega"],
        "reportes_avanzados": ["Administrador"],
        "configuracion": ["Administrador"],
    }

    current_page = st.session_state.current_page
    if current_page != "Inicio":
        if current_page in allowed_modules:
            if role not in allowed_modules[current_page]:
                st.error("⛔ Acceso denegado. No tienes permiso para ver este módulo.")
                st.session_state.current_page = "Inicio"
                st.rerun()
        else:
            if role != "Administrador":
                st.error("⛔ Acceso denegado.")
                st.session_state.current_page = "Inicio"
                st.rerun()

    # ✅ ESTE BLOQUE DEBE ESTAR AQUÍ — no en show_generar_guias
    page_mapping = {
        "Inicio": show_main_page,
        "dashboard_kpis": show_dashboard_kpis,
        "reconciliacion_v8": show_reconciliacion_v8,
        "auditoria_correos": show_auditoria_correos,
        "dashboard_logistico": show_logistica,
        "gestion_equipo": show_gestion_equipo,
        "generar_guias": show_generar_guias,
        "control_inventario": show_control_inventario,
        "reportes_avanzados": show_reportes_avanzados,
        "configuracion": show_configuracion,
    }

    if current_page in page_mapping:
        page_mapping[current_page]()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()
    # ==============================================================================
# MÓDULO: GENERAR GUÍAS
# ==============================================================================
def show_generar_guias():
    """Generador de guias de envio con autocompletado desde TIENDAS_DATA"""
    add_back_button(key="back_guias")
    show_module_header("🚚 Generador de Guias", "Sistema de envios con seguimiento QR")

    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    # URLs de logos
    url_fashion_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Fashion.jpg"
    url_tempo_logo = "https://raw.githubusercontent.com/wilo3161/kpi-system/main/images/Tempo.jpg"

    # Lista de tiendas desde TIENDAS_DATA (global)
    tiendas_options = [""] + [t["Nombre de Tienda"] for t in TIENDAS_DATA]

    # Remitentes
    remitentes = [
        {"nombre": "Josue Imbacuan", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Luis Perugachi", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andres Yepez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Wilson Perez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Andres Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Diana Garcia", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jessica Suarez", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Rocio Cadena", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
        {"nombre": "Jhony Villa", "direccion": "San Roque, Calle Santo Thomas y antigua via a Cotacachi"},
    ]

    # Función para obtener datos de una tienda
    def get_tienda_data(nombre_tienda):
        for t in TIENDAS_DATA:
            if t["Nombre de Tienda"] == nombre_tienda:
                return t
        return None

    # --- Formulario principal ---
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

        # Selección de tienda (autocompletado)
        tienda_seleccionada = st.selectbox("**Tienda Destino (seleccione para autocompletar):**", tiendas_options, index=0)
        datos_tienda = get_tienda_data(tienda_seleccionada) if tienda_seleccionada else None

        col5, col6 = st.columns(2)
        with col5:
            nombre_destinatario = st.text_input(
                "**Nombre del Destinatario:**",
                value=datos_tienda["Contacto"] if datos_tienda else "",
                placeholder="Ej: Pepito Paez"
            )
            telefono_destinatario = st.text_input(
                "**Telefono del Destinatario:**",
                value=datos_tienda["Teléfono"] if datos_tienda else "",
                placeholder="Ej: +593 99 999 9999"
            )
        with col6:
            direccion_destinatario = st.text_area(
                "**Direccion del Destinatario:**",
                value=datos_tienda["Dirección"] if datos_tienda else "",
                placeholder="Ej: Av. Principal #123, Ciudad, Provincia",
                height=100
            )
            st.caption("💡 Seleccione una tienda arriba para autocompletar los datos del destinatario.")

        st.divider()

        st.subheader("🔗 Informacion Digital")
        url_pedido = st.text_input(
            "**URL del Pedido/Tracking:**",
            placeholder="https://pedidos.fashionclub.com/orden-12345",
            value="https://pedidos.fashionclub.com/"
        )

        if url_pedido and url_pedido.startswith(("http://", "https://")):
            try:
                qr = qrcode.QRCode(version=1, box_size=8, border=2)
                qr.add_data(url_pedido)
                qr.make(fit=True)
                img_qr = qr.make_image(fill_color="black", back_color="white")
                img_byte_arr = io.BytesIO()
                img_qr.save(img_byte_arr, format="PNG")
                img_byte_arr.seek(0)

                if "qr_images" not in st.session_state:
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
            st.form_submit_button("🔄 Nuevo Formulario", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # --- Lógica de preview y generación ---
    if preview:
        if not nombre_destinatario or not direccion_destinatario:
            st.warning("Complete al menos nombre y direccion del destinatario para ver la vista previa")
        else:
            if "contador_guias" not in st.session_state:
                st.session_state.contador_guias = 1000
            guia_num_preview = f"GFC-{st.session_state.contador_guias:04d}"
            qr_bytes = st.session_state.qr_images.get(url_pedido) if url_pedido in st.session_state.get("qr_images", {}) else None
            guia_data_preview = {
                "numero": guia_num_preview,
                "marca": marca,
                "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion,
                "destinatario": nombre_destinatario,
                "telefono_destinatario": telefono_destinatario or "No especificado",
                "direccion_destinatario": direccion_destinatario,
                "tienda_destino": tienda_seleccionada if tienda_seleccionada else "No especificada",
                "url_pedido": url_pedido if url_pedido else "No especificada",
                "estado": "Vista Previa",
                "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "qr_bytes": qr_bytes,
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
        elif not url_pedido.startswith(("http://", "https://")):
            errors.append("❌ La URL debe comenzar con http:// o https://")

        if errors:
            for error in errors:
                st.error(error)
        else:
            if "contador_guias" not in st.session_state:
                st.session_state.contador_guias = 1000
            guia_num = f"GFC-{st.session_state.contador_guias:04d}"
            st.session_state.contador_guias += 1

            if "logos" not in st.session_state:
                st.session_state.logos = {}
            if marca not in st.session_state.logos:
                logo_url = url_fashion_logo if marca == "Fashion Club" else url_tempo_logo
                logo_bytes = descargar_logo(logo_url)
                if logo_bytes:
                    st.session_state.logos[marca] = logo_bytes

            qr_bytes = st.session_state.qr_images.get(url_pedido) if "qr_images" in st.session_state and url_pedido in st.session_state.qr_images else None
            guia_data = {
                "numero": guia_num,
                "marca": marca,
                "remitente": remitente_nombre,
                "direccion_remitente": remitente_direccion,
                "destinatario": nombre_destinatario,
                "telefono_destinatario": telefono_destinatario or "No especificado",
                "direccion_destinatario": direccion_destinatario,
                "tienda_destino": tienda_seleccionada if tienda_seleccionada else "No especificada",
                "url_pedido": url_pedido,
                "estado": "Generada",
                "fecha_emision": datetime.now().strftime("%Y-%m-%d"),
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "qr_bytes": qr_bytes,
            }

            with st.spinner(f"Generando guia {guia_num}..."):
                time.sleep(1.5)

                if "guias_registradas" not in st.session_state:
                    st.session_state.guias_registradas = []
                st.session_state.guias_registradas.append(guia_data)

                try:
                    local_db.insert("guias", guia_data)
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
                        <div class='metric-value'>{datetime.now().strftime("%Y-%m-%d")}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("""
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
                        type="primary",
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

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()
