# config/stores_data.py
# UNICA FUENTE DE VERDAD PARA TIENDAS Y CONSTANTES

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
_private_data_path = BASE_DIR / "config" / "private_data.json"

TIENDAS_DATA = []
PRICE_CLUBS = []
TIENDAS_REGULARES = []
TIENDAS_DICT = {}
DESTINO_A_TIENDAS = {}

def reload_stores_data():
    """Recarga los datos desde el JSON mutando las estructuras en memoria para actualizar referencias globales."""
    if _private_data_path.exists():
        with open(_private_data_path, "r", encoding="utf-8-sig") as f:
            try:
                _private_data = json.load(f)
                TIENDAS_DATA.clear()
                TIENDAS_DATA.extend(_private_data.get("tiendas", []))
            except Exception:
                pass
                
    PRICE_CLUBS.clear()
    PRICE_CLUBS.extend([t["Nombre de Tienda"] for t in TIENDAS_DATA if "Price Club" in t["Nombre de Tienda"]])
    
    TIENDAS_REGULARES.clear()
    TIENDAS_REGULARES.extend([t["Nombre de Tienda"] for t in TIENDAS_DATA if "Aeropostale" in t["Empresa"] and "Price Club" not in t["Nombre de Tienda"]])
    
    TIENDAS_DICT.clear()
    TIENDAS_DICT.update({t["Nombre de Tienda"]: t for t in TIENDAS_DATA})
    
    DESTINO_A_TIENDAS.clear()
    for t in TIENDAS_DATA:
        DESTINO_A_TIENDAS.setdefault(t["Destino"], []).append(t["Nombre de Tienda"])

# Carga inicial
reload_stores_data()

VENTAS_POR_MAYOR = ["VENTAS POR MAYOR", "MAYORISTA"]
TIENDA_WEB = ["TIENDA WEB", "WEB", "TIENDA MOVIL", "MOVIL"]
FALLAS = ["FALLAS"]

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

# Solución al Bug de Importación Logística
COLOR_KEYS = {
    'Price Club': 'PRICE CLUB',
    'Tiendas': 'TIENDAS AEROPOSTALE',
    'Ventas por Mayor': 'VENTAS POR MAYOR',
    'Tienda Web': 'TIENDA WEB',
    'Fallas': 'FALLAS',
    'Fundas': 'FUNDAS'
}
