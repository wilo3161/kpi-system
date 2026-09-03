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
    # Importación local para evitar dependencias circulares
    from database.manager import local_db
    
    # Intentar cargar desde la base de datos
    db_tiendas = []
    try:
        db_tiendas = local_db.find("tiendas", {})
    except Exception:
        db_tiendas = []
        
    # Auto-migración: Si detecta la data vieja (ej. "Aeropostale Mall del Rio" sin estructura nueva)
    if db_tiendas and any("Aeropostale Mall del Rio" == t.get("Nombre de Tienda") for t in db_tiendas):
        try:
            if hasattr(local_db, "db") and hasattr(local_db.db, "__getitem__"):
                local_db.db["tiendas"].drop()
            else:
                local_db.delete("tiendas", {})
        except Exception:
            pass
        db_tiendas = []
        
    if db_tiendas:
        TIENDAS_DATA.clear()
        TIENDAS_DATA.extend(db_tiendas)
    else:
        # Fallback 1: load_tiendas.py
        tiendas_source = []
        try:
            from load_tiendas import tiendas_data
            tiendas_source = list(tiendas_data)
        except Exception:
            pass
            
        # Fallback 2: private_data.json
        if not tiendas_source and _private_data_path.exists():
            try:
                with open(_private_data_path, "r", encoding="utf-8-sig") as f:
                    tiendas_source = json.load(f).get("tiendas", [])
            except Exception:
                pass
                
        # Fallback 3: automation.tiendas_data
        if not tiendas_source:
            try:
                from automation.tiendas_data import TIENDAS_DATA as auto_tiendas
                tiendas_source = list(auto_tiendas)
            except Exception:
                pass

        if tiendas_source:
            try:
                for t in tiendas_source:
                    local_db.insert("tiendas", t)
            except Exception:
                pass
            TIENDAS_DATA.clear()
            TIENDAS_DATA.extend(tiendas_source)
                
    PRICE_CLUBS.clear()
    PRICE_CLUBS.extend([t["Nombre de Tienda"] for t in TIENDAS_DATA if "Price Club" in t.get("Empresa", "")])
    
    TIENDAS_REGULARES.clear()
    TIENDAS_REGULARES.extend([t["Nombre de Tienda"] for t in TIENDAS_DATA if "Aeropostale" in t.get("Empresa", "")])
    
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
