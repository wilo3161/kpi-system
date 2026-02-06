"""
Funciones auxiliares para procesamiento de datos
"""

import re
import hashlib
import unicodedata
import pandas as pd
from datetime import datetime


def normalizar_texto_wilo(texto):
    """
    Normaliza texto para comparaciones consistentes
    
    Args:
        texto: String o valor a normalizar
        
    Returns:
        String normalizado en mayúsculas sin caracteres especiales
    """
    if pd.isna(texto) or texto == '': 
        return ''
    texto = str(texto)
    try:
        texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    except: 
        pass
    texto = re.sub(r'[^A-Za-z0-9\s]', ' ', texto.upper())
    return re.sub(r'\s+', ' ', texto).strip()


def procesar_subtotal_wilo(valor):
    """
    Convierte valores monetarios a float
    
    Args:
        valor: Valor numérico o string con formato monetario
        
    Returns:
        Float con el valor numérico
    """
    if pd.isna(valor): 
        return 0.0
    try:
        if isinstance(valor, (int, float)): 
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


def hash_password(pw: str) -> str:
    """
    Genera hash SHA256 de una contraseña
    
    Args:
        pw: Contraseña en texto plano
        
    Returns:
        Hash SHA256 de la contraseña
    """
    return hashlib.sha256(pw.encode()).hexdigest()


def validar_fecha(fecha: str) -> bool:
    """
    Valida formato de fecha YYYY-MM-DD
    
    Args:
        fecha: String con fecha
        
    Returns:
        True si el formato es válido, False en caso contrario
    """
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except ValueError: 
        return False


def identificar_tipo_tienda_v8(nombre):
    """
    Lógica V8.0 para clasificación de tiendas.
    Incluye regla específica para JOFRE SANTANA y manejo de Piezas.
    
    Args:
        nombre: Nombre del destinatario
        
    Returns:
        Tipo de tienda clasificado
    """
    if pd.isna(nombre) or nombre == '': 
        return "DESCONOCIDO"
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
        
    return "TIENDA FÍSICA"  # Default
