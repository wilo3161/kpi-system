# utils/common.py
"""
Funciones comunes de utilidad: normalización, parsing, hashing, serialización.
"""

import hashlib
import pandas as pd
import numpy as np
import re
import unicodedata
import io
from typing import Optional
from datetime import datetime, date


def normalizar_texto(texto) -> str:
    """Normaliza texto: elimina acentos, caracteres especiales, espacios extra."""
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


def extraer_entero(val) -> int:
    """Extrae el primer número entero de una cadena o valor."""
    if pd.isna(val):
        return 0
    s = str(val).replace(',', '')
    match = re.search(r'\d+', s)
    return int(match.group()) if match else 0


def procesar_subtotal(valor) -> float:
    """Convierte un valor monetario con posibles formatos a float."""
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
    """Busca la columna de piezas/cantidad en un DataFrame."""
    posibles = ["PIEZAS", "CANTIDAD", "UNIDADES", "QTY", "CANT", "PZS", "BULTOS"]
    for col in df.columns:
        col_upper = str(col).upper()
        if any(p in col_upper for p in posibles):
            return col
    return None


def obtener_columna_fecha(df: pd.DataFrame) -> Optional[str]:
    """Busca la columna de fecha en un DataFrame."""
    posibles = ["FECHA", "FECHA ING", "FECHA INGRESO", "FECHA CREACION", "FECHA_ING", "FECHA_CREACION"]
    for col in df.columns:
        col_upper = str(col).upper()
        if any(p in col_upper for p in posibles):
            return col
    return None


def identificar_tipo_tienda(nombre) -> str:
    """
    Identifica el tipo de tienda a partir de su nombre.
    1. Coincidencia exacta en TIENDAS_DICT (config/stores_data.py).
    2. Heurísticas de nombres personales, patrones de tiendas físicas, etc.
    """
    if pd.isna(nombre) or nombre == "":
        return "DESCONOCIDO"

    # 1. Coincidencia exacta con el catálogo oficial de tiendas
    from config.stores_data import TIENDAS_DICT
    if nombre in TIENDAS_DICT:
        info = TIENDAS_DICT[nombre]
        if "Price Club" in info.get("Nombre de Tienda", ""):
            return "PRICE CLUB"
        return "TIENDA FÍSICA"

    nombre_upper = normalizar_texto(nombre)

    # 2. Heurísticas
    if "JOFRE" in nombre_upper and "SANTANA" in nombre_upper:
        return "VENTAS POR MAYOR"

    nombres_personales = [
        "ROCIO", "ALEJANDRA", "ANGELICA", "DELGADO", "CRUZ", "LILIANA",
        "SALAZAR", "RICARDO", "SANCHEZ", "JAZMIN", "ALVARADO", "MELISSA",
        "CHAVEZ", "KARLA", "SORIANO", "ESTEFANIA", "GUALPA", "MARIA",
        "JESSICA", "PEREZ", "LOYO"
    ]
    palabras = nombre_upper.split()
    for p in palabras:
        if len(p) > 2 and p in nombres_personales:
            return "VENTA WEB"

    patrones_fisicas = [
        "LOCAL", "AEROPOSTALE", "MALL", "PLAZA", "SHOPPING", "CENTRO COMERCIAL",
        "CC", "C.C", "TIENDA", "SUCURSAL", "PRICE", "CLUB", "DORADO", "CIUDAD",
        "RIOCENTRO", "PASEO", "PORTAL", "SOL", "CONDADO", "CITY", "CEIBOS",
        "IBARRA", "MATRIZ", "BODEGA", "FASHION", "GYE", "QUITO", "MACHALA",
        "PORTOVIEJO", "BABAHOYO", "MANTA", "AMBATO", "CUENCA", "ALMACEN", "PRATI"
    ]
    for patron in patrones_fisicas:
        if patron in nombre_upper:
            return "TIENDA FÍSICA"

    if len(palabras) >= 3 or any(len(p) > 3 for p in palabras):
        return "TIENDA FÍSICA"

    return "VENTA WEB"


def to_excel(df: pd.DataFrame) -> bytes:
    """Convierte un DataFrame a un archivo Excel en bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


def hash_password(password: str) -> str:
    """Genera un hash bcrypt de una contraseña."""
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(str(password).encode('utf-8'), salt).decode('utf-8')
    except ImportError:
        # Fallback de desarrollo si bcrypt no está instalado
        import hashlib
        return hashlib.sha256(str(password).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash (soporta bcrypt y legacy sha256)."""
    password_bytes = str(password).encode('utf-8')
    # Detección de Legacy SHA-256 (64 caracteres hex)
    if len(hashed) == 64 and re.match(r'^[0-9a-f]{64}$', hashed):
        import hashlib
        return hashlib.sha256(password_bytes).hexdigest() == hashed
    
    # Verificación Bcrypt
    try:
        import bcrypt
        return bcrypt.checkpw(password_bytes, hashed.encode('utf-8'))
    except Exception:
        return False


def sanitize_for_mongo(value):
    """
    Convierte recursivamente cualquier valor a un tipo nativo de Python
    apto para inserción en MongoDB.
    """
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat() if isinstance(value, pd.Timestamp) else str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    if isinstance(value, list):
        return [sanitize_for_mongo(v) for v in value]
    if isinstance(value, tuple):
        return tuple(sanitize_for_mongo(v) for v in value)
    if isinstance(value, dict):
        return {k: sanitize_for_mongo(v) for k, v in value.items()}
    return value
