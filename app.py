"""
Sistema de Gestión Aeropostale
================================

Este módulo implementa una aplicación Streamlit para la gestión de tiendas,
KPIs, reconciliación logística y generación de guías de envío para Aeropostale.

Arquitectura del sistema:
- Capa de acceso a datos: Funciones para interactuar con Supabase
- Capa de lógica de negocio: Reglas y procesos específicos del dominio
- Capa de presentación: Interfaz de usuario Streamlit
- Infraestructura: Configuración, logging y servicios externos
"""

import os
import io
import json
import logging
import requests
import tempfile
import datetime
import pandas as pd
import numpy as np
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
import re
from io import BytesIO
import base64
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from supabase import create_client, Client
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import warnings

# ================================
# CONFIGURACIÓN INICIAL Y LOGGING
# ================================

# Configuración de logging para registrar eventos y errores
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AeropostaleKPIs")

# Suprimir advertencias no críticas
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', category=DeprecationWarning)

# ================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# ================================

class Config:
    """Maneja la configuración de la aplicación usando variables de entorno."""
    
    @staticmethod
    def get_supabase_url() -> str:
        """Obtiene la URL de Supabase desde variables de entorno."""
        url = os.getenv("SUPABASE_URL")
        if not url:
            logger.critical("SUPABASE_URL no está configurado en las variables de entorno")
            raise EnvironmentError("Falta la variable de entorno SUPABASE_URL")
        return url
    
    @staticmethod
    def get_supabase_key() -> str:
        """Obtiene la clave de API de Supabase desde variables de entorno."""
        key = os.getenv("SUPABASE_KEY")
        if not key:
            logger.critical("SUPABASE_KEY no está configurado en las variables de entorno")
            raise EnvironmentError("Falta la variable de entorno SUPABASE_KEY")
        return key
    
    @staticmethod
    def get_admin_password() -> str:
        """Obtiene la contraseña de administrador desde variables de entorno."""
        password = os.getenv("ADMIN_PASSWORD", "Wilo3161")
        if not password:
            logger.warning("ADMIN_PASSWORD no está configurado, usando valor por defecto")
        return password
    
    @staticmethod
    def get_user_password() -> str:
        """Obtiene la contraseña de usuario desde variables de entorno."""
        password = os.getenv("USER_PASSWORD", "User1234")
        if not password:
            logger.warning("USER_PASSWORD no está configurado, usando valor por defecto")
        return password
    
    @staticmethod
    def get_app_dir() -> str:
        """Obtiene el directorio base de la aplicación."""
        return os.path.dirname(os.path.abspath(__file__))
    
    @staticmethod
    def get_images_dir() -> str:
        """Obtiene el directorio de imágenes de la aplicación."""
        images_dir = os.path.join(Config.get_app_dir(), "images")
        os.makedirs(images_dir, exist_ok=True)
        return images_dir


# ================================
# INICIALIZACIÓN DE SERVICIOS
# ================================

# Inicializar cliente de Supabase
supabase: Optional[Client] = None
try:
    supabase = create_client(Config.get_supabase_url(), Config.get_supabase_key())
    logger.info("Cliente de Supabase inicializado correctamente")
except Exception as e:
    logger.critical(f"Error crítico al inicializar Supabase: {str(e)}")
    supabase = None

# ================================
# DEFINICIÓN DE CLASES Y ENUMS
# ================================

class UserRole(Enum):
    """Define los roles de usuario en el sistema."""
    ADMIN = "admin"
    USER = "user"
    PUBLIC = "public"

class Store:
    """Modelo de datos para una tienda."""
    
    def __init__(self, id: int, name: str, address: str, phone: str):
        self.id = id
        self.name = name
        self.address = address
        self.phone = phone
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Store':
        """Crea una instancia de Store a partir de un diccionario."""
        return cls(
            id=data['id'],
            name=data['name'],
            address=data['address'],
            phone=data['phone']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia a un diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone
        }

class Sender:
    """Modelo de datos para un remitente."""
    
    def __init__(self, id: int, name: str, address: str, phone: str):
        self.id = id
        self.name = name
        self.address = address
        self.phone = phone
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sender':
        """Crea una instancia de Sender a partir de un diccionario."""
        return cls(
            id=data['id'],
            name=data['name'],
            address=data['address'],
            phone=data['phone']
        )

class Worker:
    """Modelo de datos para un trabajador."""
    
    def __init__(self, nombre: str, equipo: str, activo: bool = True):
        self.nombre = nombre
        self.equipo = equipo
        self.activo = activo
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Worker':
        """Crea una instancia de Worker a partir de un diccionario."""
        return cls(
            nombre=data['nombre'],
            equipo=data['equipo'],
            activo=data.get('activo', True)
        )

class Distribution:
    """Modelo de datos para distribuciones semanales."""
    
    def __init__(self, semana: str, tempo_distribuciones: int, luis_distribuciones: int, meta_semanal: int = 7500):
        self.semana = semana
        self.tempo_distribuciones = tempo_distribuciones
        self.luis_distribuciones = luis_distribuciones
        self.meta_semanal = meta_semanal
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Distribution':
        """Crea una instancia de Distribution a partir de un diccionario."""
        return cls(
            semana=data['semana'],
            tempo_distribuciones=data['tempo_distribuciones'],
            luis_distribuciones=data['luis_distribuciones'],
            meta_semanal=data.get('meta_semanal', 7500)
        )

class KPIRecord:
    """Modelo de datos para un registro de KPI."""
    
    def __init__(self, fecha: str, nombre: str, equipo: str, cantidad: float, meta: float, 
                 eficiencia: float, productividad: float, comentario: str, meta_mensual: float, 
                 horas_trabajo: float, actividad: str):
        self.fecha = fecha
        self.nombre = nombre
        self.equipo = equipo
        self.cantidad = cantidad
        self.meta = meta
        self.eficiencia = eficiencia
        self.productividad = productividad
        self.comentario = comentario
        self.meta_mensual = meta_mensual
        self.horas_trabajo = horas_trabajo
        self.actividad = actividad
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KPIRecord':
        """Crea una instancia de KPIRecord a partir de un diccionario."""
        return cls(
            fecha=data['fecha'],
            nombre=data['nombre'],
            equipo=data['equipo'],
            cantidad=data['cantidad'],
            meta=data['meta'],
            eficiencia=data['eficiencia'],
            productividad=data['productividad'],
            comentario=data.get('comentario', ''),
            meta_mensual=data['meta_mensual'],
            horas_trabajo=data['horas_trabajo'],
            actividad=data['actividad']
        )

class Guide:
    """Modelo de datos para una guía de envío."""
    
    def __init__(self, id: int, store_name: str, brand: str, url: str, sender_name: str, 
                 status: str = "Pending", created_at: Optional[str] = None):
        self.id = id
        self.store_name = store_name
        self.brand = brand
        self.url = url
        self.sender_name = sender_name
        self.status = status
        self.created_at = created_at or datetime.datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Guide':
        """Crea una instancia de Guide a partir de un diccionario."""
        return cls(
            id=data['id'],
            store_name=data['store_name'],
            brand=data['brand'],
            url=data['url'],
            sender_name=data['sender_name'],
            status=data.get('status', 'Pending'),
            created_at=data.get('created_at')
        )

# ================================
# FUNCIONES DE ACCESO A DATOS
# ================================

def obtener_tienda_por_id(tienda_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene una tienda específica por su ID desde Supabase.
    
    Args:
        tienda_id: ID de la tienda a buscar
    
    Returns:
        Diccionario con los datos de la tienda o None si no se encuentra
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return None
    
    try:
        response = supabase.table('guide_stores').select('*').eq('id', tienda_id).execute()
        
        if response.data:
            return response.data[0]
        else:
            logger.warning(f"No se encontró la tienda con ID {tienda_id}")
            return None
    except Exception as e:
        logger.error(f"Error al obtener tienda por ID: {e}", exc_info=True)
        return None


def obtener_todas_tiendas() -> pd.DataFrame:
    """
    Obtiene todas las tiendas desde Supabase.
    
    Returns:
        DataFrame con todas las tiendas o un DataFrame vacío en caso de error
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Retornar datos de ejemplo solo para desarrollo
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"],
            'address': ["Dirección Centro", "Dirección Norte", "Dirección Sur"],
            'phone': ["0999999991", "0999999992", "0999999993"]
        })
    
    try:
        response = supabase.table('guide_stores').select('*').execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron tiendas en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener tiendas de Supabase: {e}", exc_info=True)
        # Retornar datos de ejemplo solo para desarrollo
        return pd.DataFrame({
            'id': [1, 2, 3],
            'name': ["Tienda Centro", "Tienda Norte", "Tienda Sur"],
            'address': ["Dirección Centro", "Dirección Norte", "Dirección Sur"],
            'phone': ["0999999991", "0999999992", "0999999993"]
        })


def agregar_tienda(nombre: str, direccion: str, telefono: str) -> bool:
    """
    Agrega una nueva tienda a la base de datos.
    
    Args:
        nombre: Nombre de la tienda
        direccion: Dirección de la tienda
        telefono: Número de teléfono de la tienda
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        data = {
            'name': nombre,
            'address': direccion,
            'phone': telefono
        }
        response = supabase.table('guide_stores').insert(data).execute()
        
        if response.status_code >= 400:
            logger.error(f"No se pudo agregar la tienda: {response.json()}")
            return False
        else:
            logger.info(f"Tienda '{nombre}' agregada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al agregar tienda: {e}", exc_info=True)
        return False


def actualizar_tienda(tienda_id: int, nombre: str, direccion: str, telefono: str) -> bool:
    """
    Actualiza una tienda existente en la base de datos.
    
    Args:
        tienda_id: ID de la tienda a actualizar
        nombre: Nuevo nombre de la tienda
        direccion: Nueva dirección de la tienda
        telefono: Nuevo número de teléfono de la tienda
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        data = {
            'name': nombre,
            'address': direccion,
            'phone': telefono
        }
        response = supabase.table('guide_stores').update(data).eq('id', tienda_id).execute()
        
        if response.status_code >= 400:
            logger.error(f"No se pudo actualizar la tienda: {response.json()}")
            return False
        else:
            logger.info(f"Tienda ID {tienda_id} actualizada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al actualizar tienda: {e}", exc_info=True)
        return False


def eliminar_tienda(tienda_id: int) -> bool:
    """
    Elimina una tienda de la base de datos.
    
    Args:
        tienda_id: ID de la tienda a eliminar
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        response = supabase.table('guide_stores').delete().eq('id', tienda_id).execute()
        
        if response.status_code >= 400:
            logger.error(f"No se pudo eliminar la tienda: {response.json()}")
            return False
        else:
            logger.info(f"Tienda ID {tienda_id} eliminada correctamente")
            return True
    except Exception as e:
        logger.error(f"Error al eliminar tienda: {e}", exc_info=True)
        return False


def obtener_remitentes() -> pd.DataFrame:
    """
    Obtiene la lista de remitentes desde Supabase.
    
    Returns:
        DataFrame con los remitentes o un DataFrame con datos de ejemplo en caso de error
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["ANDRÉS YÉPEZ", "JOSUÉ IMBACUAN"],
            'address': ["SAN ROQUE", "SAN ROQUE"],
            'phone': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.table('guide_senders').select('*').execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron remitentes en Supabase")
            return pd.DataFrame(columns=['id', 'name', 'address', 'phone'])
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'name': ["ANDRÉS YÉPEZ", "JOSUÉ IMBACUAN"],
            'address': ["SAN ROQUE", "SAN ROQUE"],
            'phone': ["0993052744", "0987654321"]
        })


def obtener_trabajadores() -> pd.DataFrame:
    """
    Obtiene la lista de trabajadores desde Supabase.
    
    Returns:
        DataFrame con los trabajadores o un DataFrame con datos de ejemplo en caso de error
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Retornar datos de ejemplo solo para desarrollo
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })
    
    try:
        response = supabase.table('trabajadores').select('nombre, equipo, activo')\
            .eq('activo', True).order('equipo,nombre', desc=False).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df
        else:
            logger.warning("No se encontraron trabajadores en Supabase")
            return pd.DataFrame(columns=['nombre', 'equipo', 'activo'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores de Supabase: {e}", exc_info=True)
        # Retornar datos de ejemplo solo para desarrollo
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                      "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"]
        })


def obtener_equipos() -> List[str]:
    """
    Obtiene la lista de equipos desde Supabase.
    
    Returns:
        Lista de nombres de equipos ordenados
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.table('equipos').select('equipo').order('equipo').execute()
        
        if response.data:
            equipos = [item['equipo'] for item in response.data]
            # Asegurar que "Distribución" esté en la lista
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            
            # Ordenar los equipos en un orden específico
            orden_equipos = ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
            equipos_ordenados = [eq for eq in orden_equipos if eq in equipos]
            equipos_restantes = [eq for eq in equipos if eq not in orden_equipos]
            return equipos_ordenados + equipos_restantes
        else:
            logger.warning("No se encontraron equipos en Supabase")
            return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos de Supabase: {e}", exc_info=True)
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]


def guardar_datos_db(fecha: str, datos: Dict[str, Dict[str, Any]]) -> bool:
    """
    Guarda los datos de KPIs en la tabla de Supabase.
    
    Args:
        fecha: Fecha del registro en formato YYYY-MM-DD
        datos: Diccionario con los datos de KPIs por trabajador
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        st.error("Error de conexión con la base de datos")
        return False
    
    try:
        # Validaciones adicionales
        if not fecha:
            logger.error("La fecha no puede estar vacía")
            return False
        
        if not datos:
            logger.error("Los datos no pueden estar vacíos")
            return False
        
        # Preparar registros para inserción
        registros = []
        for nombre, info in datos.items():
            # Validar que todos los campos requeridos estén presentes
            if not all(k in info for k in ['cantidad', 'meta', 'eficiencia', 'productividad', 
                                         'comentario', 'meta_mensual', 'horas_trabajo', 'equipo']):
                logger.error(f"Faltan campos requeridos para el trabajador {nombre}")
                continue
                
            registro = {
                "fecha": fecha,
                "nombre": nombre,
                "cantidad": float(info["cantidad"]),
                "meta": float(info["meta"]),
                "eficiencia": float(info["eficiencia"]),
                "productividad": float(info["productividad"]),
                "comentario": str(info["comentario"]),
                "meta_mensual": float(info["meta_mensual"]),
                "horas_trabajo": float(info["horas_trabajo"]),
                "equipo": str(info["equipo"])
            }
            registros.append(registro)
        
        if not registros:
            logger.warning("No hay registros válidos para guardar")
            return False
        
        # Usar upsert para insertar o actualizar
        response = supabase.table('daily_kpis').upsert(
            registros, 
            on_conflict="fecha,nombre"
        ).execute()
        
        if response.status_code >= 400:
            logger.error(f"No se pudieron guardar los datos: {response.json()}")
            return False
        
        logger.info(f"{len(registros)} registros de KPIs guardados correctamente para la fecha {fecha}")
        return True
    
    except ValueError as ve:
        logger.error(f"Error de conversión de tipos: {str(ve)}", exc_info=True)
        st.error("Error en los tipos de datos. Por favor verifique los valores ingresados.")
        return False
    except Exception as e:
        logger.error(f"Error al guardar datos en la base de datos: {str(e)}", exc_info=True)
        st.error("Ocurrió un error inesperado al guardar los datos.")
        return False


def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """
    Guarda una guía de envío en Supabase.
    
    Args:
        store_name: Nombre de la tienda
        brand: Marca (Fashion o Tempo)
        url: URL del pedido
        sender_name: Nombre del remitente
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        data = {
            'store_name': store_name,
            'brand': brand,
            'url': url,
            'sender_name': sender_name,
            'status': 'Pending',
            'created_at': datetime.datetime.now().isoformat()
        }
        response = supabase.table('guide_logs').insert(data).execute()
        
        if response.status_code >= 400:
            logger.error(f"No se pudo guardar la guía en Supabase: {response.json()}")
            return False
        else:
            logger.info(f"Guía guardada correctamente para {store_name}")
            return True
    except Exception as e:
        logger.error(f"Error al guardar guía en Supabase: {e}", exc_info=True)
        return False


def obtener_historial_guias() -> pd.DataFrame:
    """
    Obtiene el historial de guías de envío desde Supabase.
    
    Returns:
        DataFrame con el historial de guías o un DataFrame vacío en caso de error
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        response = supabase.table('guide_logs').select('*').order('created_at', desc=True).execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        else:
            logger.info("No hay guías registradas en la base de datos")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar historial de guías de Supabase: {e}", exc_info=True)
        return pd.DataFrame()


def eliminar_guias(guias_ids: List[int]) -> bool:
    """
    Elimina múltiples guías de la base de datos.
    
    Args:
        guias_ids: Lista de IDs de guías a eliminar
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if not guias_ids:
        logger.warning("No se proporcionaron IDs de guías para eliminar")
        return False
    
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Eliminar una por una para manejar errores individuales
        eliminadas = 0
        for guia_id in guias_ids:
            response = supabase.table('guide_logs').delete().eq('id', guia_id).execute()
            if response.status_code < 400:
                eliminadas += 1
        
        logger.info(f"Se eliminaron {eliminadas} de {len(guias_ids)} guías solicitadas")
        return eliminadas == len(guias_ids)
    
    except Exception as e:
        logger.error(f"Error al eliminar guías: {e}", exc_info=True)
        return False


def guardar_distribuciones_semanales(semana: str, tempo_distribuciones: int, 
                                    luis_distribuciones: int, meta_semanal: int = 7500) -> bool:
    """
    Guarda las distribuciones semanales en Supabase.
    
    Args:
        semana: Fecha de inicio de la semana en formato YYYY-MM-DD
        tempo_distribuciones: Número de distribuciones de Tempo
        luis_distribuciones: Número de distribuciones de Luis
        meta_semanal: Meta semanal (por defecto 7500)
    
    Returns:
        True si la operación fue exitosa, False en caso contrario
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        # Validar datos
        if not isinstance(semana, str) or len(semana) != 10 or '-' not in semana:
            logger.error("Formato de fecha inválido para semana")
            return False
            
        if not isinstance(tempo_distribuciones, int) or tempo_distribuciones < 0:
            logger.error("tempo_distribuciones debe ser un entero no negativo")
            return False
            
        if not isinstance(luis_distribuciones, int) or luis_distribuciones < 0:
            logger.error("luis_distribuciones debe ser un entero no negativo")
            return False
            
        if not isinstance(meta_semanal, int) or meta_semanal <= 0:
            logger.error("meta_semanal debe ser un entero positivo")
            return False
        
        # Verificar si ya existe registro para esta semana
        existing = supabase.table('distribuciones_semanales')\
            .select('id').eq('semana', semana).execute()
        
        if existing.data:
            # Actualizar registro existente
            data = {
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal
            }
            response = supabase.table('distribuciones_semanales')\
                .update(data).eq('semana', semana).execute()
        else:
            # Insertar nuevo registro
            data = {
                'semana': semana,
                'tempo_distribuciones': tempo_distribuciones,
                'luis_distribuciones': luis_distribuciones,
                'meta_semanal': meta_semanal
            }
            response = supabase.table('distribuciones_semanales').insert(data).execute()
        
        # Verificar si la operación fue exitosa
        if response.status_code >= 400:
            logger.error(f"No se pudieron guardar las distribuciones semanales: {response.json()}")
            return False
        
        logger.info(f"Distribuciones semanales guardadas correctamente para la semana {semana}")
        return True
    
    except Exception as e:
        logger.error(f"Error al guardar distribuciones semanales: {e}", exc_info=True)
        return False


def obtener_distribuciones_semana(fecha: str) -> Dict[str, int]:
    """
    Obtiene las distribuciones de la semana para una fecha dada.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD
    
    Returns:
        Diccionario con las distribuciones de Tempo y Luis
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return {'tempo': 0, 'luis': 0}
    
    try:
        # Calcular el lunes de la semana
        fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
        lunes = fecha_dt - datetime.timedelta(days=fecha_dt.weekday())
        semana = lunes.strftime("%Y-%m-%d")
        
        response = supabase.table('distribuciones_semanales')\
            .select('*').eq('semana', semana).execute()
        
        if response.data:
            data = response.data[0]
            return {
                'tempo': data['tempo_distribuciones'],
                'luis': data['luis_distribuciones']
            }
        else:
            logger.info(f"No hay datos de distribución para la semana {semana}")
            return {'tempo': 0, 'luis': 0}
    
    except Exception as e:
        logger.error(f"Error al obtener distribuciones semanales: {e}", exc_info=True)
        return {'tempo': 0, 'luis': 0}


def obtener_dependencias_transferencias() -> pd.DataFrame:
    """
    Obtiene las dependencias entre transferidores y proveedores.
    
    Returns:
        DataFrame con las dependencias o un DataFrame con datos de ejemplo en caso de error
    """
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Devolver dependencias por defecto
        return pd.DataFrame({
            'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
            'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
        })
    
    try:
        response = supabase.table('dependencias_transferencias').select('*').execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        else:
            logger.warning("No se encontraron dependencias de transferencias en Supabase")
            # Devolver dependencias por defecto
            return pd.DataFrame({
                'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
                'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
            })
    except Exception as e:
        logger.error(f"Error al obtener dependencias de transferencias: {e}", exc_info=True)
        # Devolver dependencias por defecto
        return pd.DataFrame({
            'transferidor': ['Josué Imbacuán', 'Andrés Yépez'],
            'proveedor_distribuciones': ['Tempo', 'Luis Perugachi']
        })

# ================================
# FUNCIONES DE LÓGICA DE NEGOCIO
# ================================

def calcular_metas_semanales() -> Dict[str, Any]:
    """
    Calcula el progreso semanal y asigna responsabilidades.
    
    Returns:
        Diccionario con el resultado del cálculo de metas semanales
    """
    # Obtener distribuciones de la semana actual
    fecha_actual = datetime.datetime.now().date()
    fecha_inicio_semana = fecha_actual - datetime.timedelta(days=fecha_actual.weekday())
    distribuciones_semana = obtener_distribuciones_semana(fecha_inicio_semana.strftime("%Y-%m-%d"))
    
    # Calcular cumplimiento
    meta_semanal = 7500
    distribuciones_totales = distribuciones_semana['tempo'] + distribuciones_semana['luis']
    
    # Determinar responsabilidades
    resultado = {
        'meta_semanal': meta_semanal,
        'distribuciones_totales': distribuciones_totales,
        'cumplimiento_porcentaje': (distribuciones_totales / meta_semanal) * 100 if meta_semanal > 0 else 0,
        'detalles': []
    }
    
    # Verificar abastecimiento de Tempo para Josué
    if distribuciones_semana['tempo'] < 3750:  # Mitad de la meta semanal
        resultado['detalles'].append({
            'transferidor': 'Josué Imbacuán',
            'proveedor': 'Tempo',
            'distribuciones_recibidas': distribuciones_semana['tempo'],
            'distribuciones_requeridas': 3750,
            'estado': 'INSUFICIENTE'
        })
    
    # Verificar abastecimiento de Luis para Andrés
    if distribuciones_semana['luis'] < 3750:
        resultado['detalles'].append({
            'transferidor': 'Andrés Yépez',
            'proveedor': 'Luis Perugachi',
            'distribuciones_recibidas': distribuciones_semana['luis'],
            'distribuciones_requeridas': 3750,
            'estado': 'INSUFICIENTE'
        })
    
    return resultado


def verificar_alertas_abastecimiento() -> List[Dict[str, Any]]:
    """
    Verifica y retorna alertas de abastecimiento.
    
    Returns:
        Lista de alertas de abastecimiento
    """
    resultado = calcular_metas_semanales()
    alertas = []
    
    for detalle in resultado['detalles']:
        if detalle['estado'] == 'INSUFICIENTE':
            alertas.append({
                'mensaje': f"⚠️ Alerta de abastecimiento para {detalle['transferidor']}",
                'descripcion': f"{detalle['proveedor']} solo proporcionó {detalle['distribuciones_recibidas']} de {detalle['distribuciones_requeridas']} distribuciones requeridas",
                'nivel': "ALTO"
            })
    
    return alertas


def kpi_transferencias(cantidad: float, meta: float) -> float:
    """
    Calcula el KPI para el equipo de Transferencias.
    
    Args:
        cantidad: Cantidad realizada
        meta: Meta establecida
    
    Returns:
        Valor del KPI (porcentaje de cumplimiento)
    """
    if meta <= 0:
        return 0.0
    return min((cantidad / meta) * 100, 100.0)


def kpi_distribucion(cantidad: float, meta: float) -> float:
    """
    Calcula el KPI para el equipo de Distribución.
    
    Args:
        cantidad: Cantidad realizada
        meta: Meta establecida
    
    Returns:
        Valor del KPI (porcentaje de cumplimiento)
    """
    if meta <= 0:
        return 0.0
    return min((cantidad / meta) * 100, 100.0)


def kpi_arreglos(cantidad: float, meta: float) -> float:
    """
    Calcula el KPI para el equipo de Arreglos.
    
    Args:
        cantidad: Cantidad realizada
        meta: Meta establecida
    
    Returns:
        Valor del KPI (porcentaje de cumplimiento)
    """
    if meta <= 0:
        return 0.0
    return min((cantidad / meta) * 100, 100.0)


def kpi_guias(cantidad: float, meta: float) -> float:
    """
    Calcula el KPI para el equipo de Guías.
    
    Args:
        cantidad: Cantidad realizada
        meta: Meta establecida
    
    Returns:
        Valor del KPI (porcentaje de cumplimiento)
    """
    if meta <= 0:
        return 0.0
    return min((cantidad / meta) * 100, 100.0)


def validar_numero_positivo(valor: Any) -> bool:
    """
    Valida si un valor es un número positivo.
    
    Args:
        valor: Valor a validar
    
    Returns:
        True si el valor es un número positivo, False en caso contrario
    """
    try:
        num = float(valor)
        return num >= 0
    except (TypeError, ValueError):
        return False


def validar_fecha(fecha: str) -> bool:
    """
    Valida si una cadena tiene formato de fecha válido (YYYY-MM-DD).
    
    Args:
        fecha: Cadena a validar
    
    Returns:
        True si el formato es válido, False en caso contrario
    """
    try:
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def validar_distribuciones(valor: int) -> bool:
    """
    Valida si un valor es adecuado para distribuciones (entero no negativo).
    
    Args:
        valor: Valor a validar
    
    Returns:
        True si el valor es adecuado, False en caso contrario
    """
    return isinstance(valor, int) and valor >= 0


def generar_numero_seguimiento(record_id: int) -> str:
    """
    Genera un número de seguimiento único.
    
    Args:
        record_id: ID del registro
    
    Returns:
        Número de seguimiento en formato AERO + 8 dígitos
    """
    return f"AERO{str(record_id).zfill(8)}"  # Formato AERO + 8 dígitos


def generar_qr_imagen(url: str) -> Image.Image:
    """
    Genera y devuelve una imagen del código QR.
    
    Args:
        url: URL a codificar en el QR
    
    Returns:
        Imagen PIL del código QR
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=5,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def pil_image_to_bytes(pil_image: Image.Image) -> bytes:
    """
    Convierte un objeto de imagen de PIL a bytes.
    
    Args:
        pil_image: Imagen PIL a convertir
    
    Returns:
        Bytes de la imagen en formato PNG
    """
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return buf.getvalue()


def verificar_imagen_existe(url: str) -> bool:
    """
    Verifica si una imagen existe en la URL proporcionada.
    
    Args:
        url: URL de la imagen a verificar
    
    Returns:
        True si la imagen existe, False en caso contrario
    """
    try:
        # Si es una URL local (file://), verificar con os.path.exists
        if url.startswith("file://"):
            local_path = url[7:]  # Remover "file://"
            return os.path.exists(local_path)
        
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al verificar imagen: {str(e)}")
        return False


def generar_pdf_guia(tienda_info: Dict[str, str], url: str) -> bytes:
    """
    Genera un PDF de guía de envío.
    
    Args:
        tienda_info: Información de la tienda
        url: URL del pedido
    
    Returns:
        Bytes del PDF generado
    """
    try:
        # Crear un buffer en memoria para el PDF
        buffer = io.BytesIO()
        
        # Crear el PDF
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Establecer colores y fuentes
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica", 12)
        
        # Título principal
        pdf.setFillColorRGB(230, 0, 18)
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawCentredString(width/2, height - 50, "AEROPOSTALE")
        
        # Subtítulo
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(width/2, height - 80, "CENTRO DE DISTRIBUCIÓN FASHION CLUB")
        
        # Información de la tienda
        pdf.setFont("Helvetica", 12)
        y_start = height - 120
        pdf.drawString(50, y_start, "DATOS DE LA TIENDA:")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y_start - 20, f"TIENDA: {tienda_info.get('name', '')}")
        pdf.drawString(50, y_start - 40, f"DIRECCIÓN: {tienda_info.get('address', '')}")
        pdf.drawString(50, y_start - 60, f"TEL.: {tienda_info.get('phone', '')}")
        
        # Código QR
        qr_img = generar_qr_imagen(url)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        
        # Insertar QR
        pdf.drawImage(qr_buffer, width - 150, y_start - 60, width=100, height=100)
        
        # Pie de página
        pdf.setFont("Helvetica-Oblique", 10)
        pdf.setFillColorRGB(0.5, 0.5, 0.5)
        pdf.drawCentredString(width/2, 30, "Guía de envío generada automáticamente - Aeropostale")
        
        # Guardar y obtener los bytes
        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    except Exception as e:
        logger.error(f"Error al generar PDF de guía: {e}", exc_info=True)
        return b""


# ================================
# COMPONENTES DE INTERFAZ DE USUARIO
# ================================

def aplicar_estilos_css():
    """Aplica estilos CSS personalizados a la aplicación Streamlit."""
    st.markdown("""
    <style>
        /* Variables de color */
        :root {
            --primary-color: #e60012;
            --secondary-color: #1a1a1a;
            --success-color: #4CAF50;
            --warning-color: #FF9800;
            --error-color: #F44336;
            --card-background: #2d2d2d;
            --background-dark: #1a1a1a;
            --text-color: #ffffff;
            --text-secondary: #b0b0b0;
            --border-radius: 10px;
            --transition: all 0.3s ease;
        }
        
        /* Estilos generales */
        .stApp {
            background-color: var(--background-dark);
            color: var(--text-color);
        }
        
        /* Encabezados */
        .header-title {
            color: var(--primary-color);
            font-weight: bold;
            margin-bottom: 2rem;
            text-align: center;
            text-shadow: 0 0 10px rgba(230, 0, 18, 0.3);
        }
        
        .section-title {
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 0.5rem;
            margin: 1.5rem 0;
        }
        
        /* Tarjetas */
        .card {
            background: var(--card-background);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border-left: 4px solid var(--primary-color);
        }
        
        /* Botones */
        .stButton>button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--border-radius);
            padding: 0.5rem 1rem;
            font-weight: bold;
            transition: var(--transition);
        }
        
        .stButton>button:hover {
            background-color: #b3000e;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* Cuadros de alerta */
        .success-box {
            background: rgba(76, 175, 80, 0.1);
            border-left: 4px solid var(--success-color);
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            color: #c8e6c9;
        }
        
        .warning-box {
            background: rgba(255, 152, 0, 0.1);
            border-left: 4px solid var(--warning-color);
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            color: #ffe0b2;
        }
        
        .error-box {
            background: rgba(244, 67, 54, 0.1);
            border-left: 4px solid var(--error-color);
            padding: 1rem;
            border-radius: var(--border-radius);
            margin: 1rem 0;
            color: #ffcdd2;
        }
        
        /* Animaciones */
        @keyframes animate-fade-in {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .animate-fade-in {
            animation: animate-fade-in 0.5s ease forwards;
        }
        
        /* Sistema de autenticación */
        .password-container {
            background: var(--card-background);
            padding: 2rem;
            border-radius: 15px;
            max-width: 450px;
            margin: 4rem auto;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(230, 0, 18, 0.2);
        }
        
        .logo-container {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        .aeropostale-logo {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .aeropostale-subtitle {
            color: var(--text-secondary);
            font-size: 1.2rem;
        }
        
        .password-title {
            color: var(--primary-color);
            text-align: center;
            margin-bottom: 1.5rem;
        }
        
        /* Comentarios */
        .comment-container {
            background: var(--card-background);
            border-left: 3px solid var(--primary-color);
            padding: 0.75rem;
            border-radius: 0 4px 4px 0;
            margin: 1rem 0;
        }
        
        .comment-title {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .comment-content {
            color: var(--text-secondary);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 1.5rem 0;
            margin-top: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Métricas de KPI */
        .kpi-card {
            background: var(--card-background);
            border-radius: var(--border-radius);
            padding: 1.2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: var(--transition);
        }
        
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary-color);
        }
        
        /* Tablas */
        .dataframe {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            overflow: hidden;
        }
        
        .dataframe thead {
            background-color: rgba(230, 0, 18, 0.1);
        }
        
        .dataframe th {
            color: var(--primary-color) !important;
        }
        
        .dataframe td {
            border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Selectores */
        .stSelectbox > div > div {
            background-color: var(--card-background) !important;
            color: var(--text-color) !important;
        }
        
        .stTextInput > div > div > input {
            background-color: var(--card-background) !important;
            color: var(--text-color) !important;
        }
        
        .stNumberInput > div > div > input {
            background-color: var(--card-background) !important;
            color: var(--text-color) !important;
        }
        
        .stTextArea > div > div > textarea {
            background-color: var(--card-background) !important;
            color: var(--text-color) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def verificar_password(tipo_requerido: UserRole = UserRole.ADMIN) -> bool:
    """
    Verifica si el usuario tiene permisos para la sección requerida.
    
    Args:
        tipo_requerido: Rol requerido para acceder (ADMIN, USER, PUBLIC)
    
    Returns:
        True si el usuario tiene los permisos necesarios, False en caso contrario
    """
    # Las secciones públicas siempre son accesibles
    if tipo_requerido == UserRole.PUBLIC:
        return True
    
    if 'user_type' not in st.session_state:
        return False
    
    current_role = st.session_state.user_type
    
    if tipo_requerido == UserRole.ADMIN:
        return current_role == "admin"
    elif tipo_requerido == UserRole.USER:
        return current_role in ["admin", "user"]
    
    return False


def solicitar_autenticacion(tipo_requerido: UserRole = UserRole.ADMIN):
    """
    Muestra un formulario de autenticación para diferentes tipos de usuario.
    
    Args:
        tipo_requerido: Tipo de usuario requerido para autenticación
    """
    st.markdown(f"""
    <div class="password-container animate-fade-in">
        <div class="logo-container">
            <div class="aeropostale-logo">AEROPOSTALE</div>
            <div class="aeropostale-subtitle">Sistema de Gestión de KPIs</div>
        </div>
        <h2 class="password-title">🔐 Acceso {"Administrativo" if tipo_requerido == UserRole.ADMIN else "Restringido"}</h2>
    """, unsafe_allow_html=True)
    
    password = st.text_input("Contraseña", type="password", key=f"password_{tipo_requerido.value}")
    
    if st.button("Verificar Acceso", use_container_width=True):
        if tipo_requerido == UserRole.ADMIN and password == Config.get_admin_password():
            st.session_state.user_type = "admin"
            st.success("✅ Autenticación exitosa. Bienvenido Administrador.")
            time.sleep(1)
            st.rerun()
        elif tipo_requerido == UserRole.USER and password in [Config.get_admin_password(), Config.get_user_password()]:
            st.session_state.user_type = "user" if password == Config.get_user_password() else "admin"
            st.success("✅ Autenticación exitosa.")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta. Por favor intente nuevamente.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_panel_control():
    """Muestra el panel de control principal de la aplicación."""
    aplicar_estilos_css()
    
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Panel de Control Aeropostale</h1>", unsafe_allow_html=True)
    
    # Verificar conexión a la base de datos
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
    
    # Mostrar alertas de abastecimiento si existen
    alertas = verificar_alertas_abastecimiento()
    for alerta in alertas:
        st.markdown(f"<div class='warning-box animate-fade-in'>{alerta['mensaje']}<br>{alerta['descripcion']}</div>", unsafe_allow_html=True)
    
    # Crear pestañas para diferentes funcionalidades
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 KPIs Diarios", 
        "🏪 Gestión de Tiendas", 
        "📦 Reconciliación Logística",
        "🏷️ Generación de Guías",
        "🔍 Historial de Guías"
    ])
    
    with tab1:
        mostrar_ingreso_datos_kpis()
    
    with tab2:
        if verificar_password(UserRole.ADMIN):
            mostrar_gestion_tiendas()
        else:
            solicitar_autenticacion(UserRole.ADMIN)
    
    with tab3:
        if verificar_password(UserRole.ADMIN):
            mostrar_reconciliacion_logistica()
        else:
            solicitar_autenticacion(UserRole.ADMIN)
    
    with tab4:
        if verificar_password(UserRole.USER):
            mostrar_generacion_etiquetas()
        else:
            solicitar_autenticacion(UserRole.USER)
    
    with tab5:
        if verificar_password(UserRole.USER):
            mostrar_historial_guias()
        else:
            solicitar_autenticacion(UserRole.USER)
    
    # Footer
    st.markdown("""
    <div class="footer">
        Sistema de KPIs Aeropostale v2.0 | © 2025 Aeropostale. Todos los derechos reservados.<br>
        Soporte técnico: <strong>Ing. Wilson Pérez</strong> - wperez@aeropostale.com
    </div>
    """, unsafe_allow_html=True)


def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs."""
    st.markdown("<h2 class='section-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h2>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener trabajadores desde Supabase
    df_trabajadores = obtener_trabajadores()
    if df_trabajadores.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay trabajadores registrados. Por favor, registre trabajadores primero.</div>", unsafe_allow_html=True)
        return
    
    # Seleccionar fecha
    fecha = st.date_input("Fecha", value=datetime.date.today())
    fecha_str = fecha.strftime("%Y-%m-%d")
    
    # Organizar trabajadores por equipo
    equipos = obtener_equipos()
    trabajadores_por_equipo = {}
    
    for equipo in equipos:
        trabajadores_equipo = df_trabajadores[df_trabajadores['equipo'] == equipo]
        if not trabajadores_equipo.empty:
            trabajadores_por_equipo[equipo] = trabajadores_equipo
    
    # Crear formulario para ingreso de datos
    with st.form("form_kpis"):
        st.markdown("<h3>Datos de KPIs por Trabajador</h3>", unsafe_allow_html=True)
        
        # Almacenar datos ingresados
        datos_kpis = {}
        
        for equipo, df in trabajadores_por_equipo.items():
            with st.expander(f"**{equipo}**", expanded=True):
                for _, row in df.iterrows():
                    trabajador = row['nombre']
                    
                    # Meta mensual predeterminada según el equipo
                    meta_mensual = 0
                    if equipo == "Transferencias":
                        meta_mensual = 2000
                    elif equipo == "Distribución":
                        meta_mensual = 7500
                    
                    st.markdown(f"#### {trabajador}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        cantidad = st.number_input(
                            "Cantidad realizada", 
                            min_value=0.0, 
                            value=0.0, 
                            step=1.0,
                            key=f"{trabajador}_cantidad"
                        )
                    with col2:
                        meta = st.number_input(
                            "Meta diaria", 
                            min_value=0.0, 
                            value=meta_mensual / 22,  # Promedio diario
                            step=1.0,
                            key=f"{trabajador}_meta"
                        )
                    with col3:
                        horas = st.number_input(
                            "Horas trabajadas", 
                            min_value=0.0, 
                            value=8.0, 
                            step=0.5,
                            key=f"{trabajador}_horas"
                        )
                    
                    comentario = st.text_area(
                        "Comentarios", 
                        key=f"{trabajador}_comentario"
                    )
                    
                    # Calcular KPIs en tiempo real
                    eficiencia = 0
                    productividad = 0
                    
                    if meta > 0:
                        eficiencia = min((cantidad / meta) * 100, 100)
                    
                    if horas > 0:
                        productividad = cantidad / horas
                    
                    st.markdown(f"**Eficiencia:** {eficiencia:.1f}% | **Productividad:** {productividad:.1f} unidades/hora")
                    
                    # Almacenar datos
                    datos_kpis[trabajador] = {
                        "cantidad": cantidad,
                        "meta": meta,
                        "eficiencia": eficiencia,
                        "productividad": productividad,
                        "comentario": comentario,
                        "meta_mensual": meta_mensual,
                        "horas_trabajo": horas,
                        "equipo": equipo
                    }
        
        # Botón de envío
        submitted = st.form_submit_button("Guardar Datos", use_container_width=True)
        
        if submitted:
            # Validar datos
            datos_validos = True
            for trabajador, info in datos_kpis.items():
                if not validar_numero_positivo(info["cantidad"]) or \
                   not validar_numero_positivo(info["meta"]) or \
                   not validar_numero_positivo(info["horas_trabajo"]):
                    st.markdown(f"<div class='error-box animate-fade-in'>❌ Datos inválidos para {trabajador}. Verifique los valores ingresados.</div>", unsafe_allow_html=True)
                    datos_validos = False
                    break
            
            if datos_validos:
                # Guardar en la base de datos
                if guardar_datos_db(fecha_str, datos_kpis):
                    st.markdown("<div class='success-box animate-fade-in'>✅ Datos guardados correctamente</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar los datos en la base de datos</div>", unsafe_allow_html=True)
    
    # Mostrar datos históricos
    st.markdown("<h2 class='section-title animate-fade-in'>📊 Visualización de Datos Históricos</h2>", unsafe_allow_html=True)
    
    if 'historical_data' not in st.session_state:
        try:
            # Obtener datos históricos desde Supabase
            response = supabase.table('daily_kpis').select('*').order('fecha', desc=True).limit(30).execute()
            if response.data:
                st.session_state.historical_data = pd.DataFrame(response.data)
            else:
                st.session_state.historical_data = pd.DataFrame()
        except Exception as e:
            logger.error(f"Error al cargar datos históricos: {e}", exc_info=True)
            st.session_state.historical_data = pd.DataFrame()
    
    if 'historical_data' in st.session_state and not st.session_state.historical_data.empty:
        df_historico = st.session_state.historical_data.copy()
        
        # Convertir fecha a datetime
        df_historico['fecha'] = pd.to_datetime(df_historico['fecha'])
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha inicial", value=df_historico['fecha'].min().date())
        with col2:
            fecha_fin = st.date_input("Fecha final", value=df_historico['fecha'].max().date())
        
        # Aplicar filtros
        mask = (df_historico['fecha'].dt.date >= fecha_inicio) & (df_historico['fecha'].dt.date <= fecha_fin)
        df_filtrado = df_historico[mask]
        
        if not df_filtrado.empty:
            # Gráfico de eficiencia por equipo
            st.markdown("### Eficiencia por Equipo")
            fig_equipo = px.line(
                df_filtrado, 
                x='fecha', 
                y='eficiencia', 
                color='equipo',
                title='Eficiencia Diaria por Equipo',
                labels={'fecha': 'Fecha', 'eficiencia': 'Eficiencia (%)', 'equipo': 'Equipo'}
            )
            fig_equipo.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_equipo, use_container_width=True)
            
            # Gráfico de productividad por trabajador
            st.markdown("### Productividad por Trabajador")
            fig_trabajador = px.bar(
                df_filtrado, 
                x='nombre', 
                y='productividad',
                color='equipo',
                title='Productividad Promedio por Trabajador',
                labels={'nombre': 'Trabajador', 'productividad': 'Productividad (unidades/hora)', 'equipo': 'Equipo'}
            )
            fig_trabajador.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_trabajador, use_container_width=True)
        else:
            st.info("No hay datos disponibles para el rango de fechas seleccionado.")
    else:
        st.info("No hay datos históricos disponibles para mostrar.")


def mostrar_gestion_tiendas():
    """Muestra la interfaz para la gestión de tiendas."""
    st.markdown("<h2 class='section-title animate-fade-in'>🏪 Gestión de Tiendas</h2>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener tiendas
    df_tiendas = obtener_todas_tiendas()
    
    # Mostrar tiendas existentes
    st.markdown("### Tiendas Registradas")
    if not df_tiendas.empty:
        st.dataframe(df_tiendas, use_container_width=True)
        
        # Selección de tienda para editar
        tienda_seleccionada = st.selectbox(
            "Seleccionar tienda para editar", 
            options=df_tiendas['id'].tolist(),
            format_func=lambda x: f"{df_tiendas[df_tiendas['id'] == x]['name'].values[0]} (ID: {x})",
            index=None,
            placeholder="Seleccione una tienda..."
        )
        
        if tienda_seleccionada:
            tienda_data = df_tiendas[df_tiendas['id'] == tienda_seleccionada].iloc[0]
            
            with st.form("editar_tienda"):
                st.markdown("#### Editar Tienda")
                
                nombre = st.text_input("Nombre", value=tienda_data['name'])
                direccion = st.text_input("Dirección", value=tienda_data['address'])
                telefono = st.text_input("Teléfono", value=tienda_data['phone'])
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Actualizar Tienda", use_container_width=True)
                with col2:
                    deleted = st.form_submit_button("Eliminar Tienda", use_container_width=True, type="secondary")
                
                if submitted:
                    if actualizar_tienda(tienda_seleccionada, nombre, direccion, telefono):
                        st.markdown("<div class='success-box animate-fade-in'>✅ Tienda actualizada correctamente</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al actualizar la tienda</div>", unsafe_allow_html=True)
                
                if deleted:
                    if eliminar_tienda(tienda_seleccionada):
                        st.markdown("<div class='success-box animate-fade-in'>✅ Tienda eliminada correctamente</div>", unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown("<div class='error-box animate-fade-in'>❌ Error al eliminar la tienda</div>", unsafe_allow_html=True)
    else:
        st.info("No hay tiendas registradas.")
    
    # Formulario para agregar nueva tienda
    st.markdown("### Agregar Nueva Tienda")
    with st.form("nueva_tienda"):
        nombre = st.text_input("Nombre de la tienda")
        direccion = st.text_input("Dirección")
        telefono = st.text_input("Teléfono")
        
        submitted = st.form_submit_button("Agregar Tienda", use_container_width=True)
        
        if submitted:
            if not nombre or not direccion or not telefono:
                st.markdown("<div class='error-box animate-fade-in'>❌ Por favor complete todos los campos</div>", unsafe_allow_html=True)
            else:
                if agregar_tienda(nombre, direccion, telefono):
                    st.markdown("<div class='success-box animate-fade-in'>✅ Tienda agregada correctamente</div>", unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Error al agregar la tienda</div>", unsafe_allow_html=True)


def mostrar_generacion_etiquetas():
    """Muestra la interfaz para generar etiquetas de productos."""
    st.markdown("<h2 class='section-title animate-fade-in'>🏷️ Generación de Guías de Envío</h2>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    df_tiendas = obtener_todas_tiendas()
    df_remitentes = obtener_remitentes()
    
    if df_tiendas.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas registradas. Por favor, registre tiendas primero.</div>", unsafe_allow_html=True)
        return
    
    if df_remitentes.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay remitentes registrados. Por favor, registre remitentes primero.</div>", unsafe_allow_html=True)
        return
    
    # Formulario de generación de guía
    with st.form("generar_guia"):
        st.markdown("#### Datos de la Guía")
        
        col1, col2 = st.columns(2)
        with col1:
            tienda = st.selectbox(
                "Tienda", 
                options=df_tiendas['id'].tolist(),
                format_func=lambda x: df_tiendas[df_tiendas['id'] == x]['name'].values[0],
                index=None,
                placeholder="Seleccione una tienda..."
            )
        
        with col2:
            marca = st.selectbox(
                "Marca", 
                options=["Fashion", "Tempo"],
                index=None,
                placeholder="Seleccione una marca..."
            )
        
        col3, col4 = st.columns(2)
        with col3:
            remitente = st.selectbox(
                "Remitente", 
                options=df_remitentes['id'].tolist(),
                format_func=lambda x: df_remitentes[df_remitentes['id'] == x]['name'].values[0],
                index=None,
                placeholder="Seleccione un remitente..."
            )
        
        with col4:
            url_pedido = st.text_input("URL del Pedido")
        
        submitted = st.form_submit_button("Generar Guía", use_container_width=True)
        
        if submitted:
            # Validar campos
            if not all([tienda, marca, remitente, url_pedido]):
                st.markdown("<div class='error-box animate-fade-in'>❌ Por favor complete todos los campos</div>", unsafe_allow_html=True)
            else:
                try:
                    # Obtener información de la tienda
                    tienda_info = df_tiendas[df_tiendas['id'] == tienda].iloc[0].to_dict()
                    remitente_info = df_remitentes[df_remitentes['id'] == remitente].iloc[0]
                    
                    # Guardar en la base de datos
                    if guardar_guia(
                        tienda_info['name'], 
                        marca, 
                        url_pedido, 
                        remitente_info['name']
                    ):
                        # Generar PDF
                        pdf_bytes = generar_pdf_guia(tienda_info, url_pedido)
                        
                        if pdf_bytes:
                            st.success("✅ Guía generada correctamente")
                            
                            # Mostrar vista previa
                            with st.expander("Vista previa de la guía", expanded=True):
                                st.download_button(
                                    label="📥 Descargar Guía PDF",
                                    data=pdf_bytes,
                                    file_name=f"guia_{tienda_info['name']}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                                
                                # Mostrar imagen del QR
                                qr_img = generar_qr_imagen(url_pedido)
                                st.image(qr_img, caption="Código QR de la guía", width=200)
                        else:
                            st.error("❌ Error al generar el PDF de la guía")
                    else:
                        st.error("❌ Error al guardar la guía en la base de datos")
                except Exception as e:
                    logger.error(f"Error al generar guía: {str(e)}", exc_info=True)
                    st.error(f"❌ Error inesperado: {str(e)}")


def mostrar_historial_guias():
    """Muestra el historial de guías de envío."""
    st.markdown("<h2 class='section-title animate-fade-in'>🔍 Historial de Guías de Envío</h2>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar historial de guías
    df_guias = obtener_historial_guias()
    
    if df_guias.empty:
        st.info("No hay guías registradas.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_inicio = st.date_input("Fecha inicial", value=df_guias['created_at'].min().date())
    with col2:
        fecha_fin = st.date_input("Fecha final", value=datetime.date.today())
    with col3:
        tienda_filtro = st.selectbox(
            "Tienda", 
            options=["Todas"] + df_guias['store_name'].unique().tolist(),
            index=0
        )
    
    # Aplicar filtros
    df_filtrado = df_guias.copy()
    df_filtrado['created_at'] = pd.to_datetime(df_filtrado['created_at'])
    
    # Filtro de fechas
    mask = (df_filtrado['created_at'].dt.date >= fecha_inicio) & (df_filtrado['created_at'].dt.date <= fecha_fin)
    df_filtrado = df_filtrado[mask]
    
    # Filtro de tienda
    if tienda_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['store_name'] == tienda_filtro]
    
    # Mostrar resultados
    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado[[
                'id', 'store_name', 'brand', 'sender_name', 
                'status', 'created_at'
            ]],
            use_container_width=True,
            hide_index=True
        )
        
        # Selección para eliminar
        guias_seleccionadas = st.multiselect(
            "Seleccionar guías para eliminar",
            options=df_filtrado['id'].tolist(),
            format_func=lambda x: f"ID: {x} - {df_filtrado[df_filtrado['id'] == x]['store_name'].values[0]} ({df_filtrado[df_filtrado['id'] == x]['created_at'].dt.strftime('%Y-%m-%d').values[0]})"
        )
        
        if st.button("Eliminar Guías Seleccionadas", type="primary", use_container_width=True):
            if guias_seleccionadas:
                if eliminar_guias(guias_seleccionadas):
                    st.markdown("<div class='success-box animate-fade-in'>✅ Guías eliminadas correctamente</div>", unsafe_allow_html=True)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.markdown("<div class='error-box animate-fade-in'>❌ Error al eliminar las guías</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='warning-box animate-fade-in'>⚠️ No se seleccionaron guías para eliminar</div>", unsafe_allow_html=True)
        
        # Exportar a CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar a CSV",
            data=csv,
            file_name=f"historial_guias_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No hay guías que coincidan con los filtros aplicados.")


class StreamlitLogisticsReconciliation:
    """Clase para manejar la reconciliación logística en Streamlit."""
    
    def __init__(self):
        # Estructuras principales
        self.df_facturas = None
        self.df_manifiesto = None
        self.guides_facturadas = []
        self.guides_anuladas = []
        self.guides_sobrantes = []
        
        # Resultados de KPIs
        self.kpis = {
            'total_facturadas': 0,
            'total_anuladas': 0,
            'total_sobrantes': 0,
            'avg_shipment_value': 0.0
        }
        
        # Datos procesados
        self.processed = False
        self.shipment_volume = pd.Series(dtype=int)
        self.anuladas_by_destinatario = pd.DataFrame()
    
    def identify_guide_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identifica la columna que contiene los números de guía en un DataFrame.
        
        Args:
            df: DataFrame a analizar
        
        Returns:
            Nombre de la columna con guías o None si no se encuentra
        """
        # Nombres comunes de columnas que podrían contener guías
        guide_keywords = ['guia', 'guía', 'guide', 'tracking', 'codigo', 'código', 'referencia', 'reference']
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in guide_keywords):
                return col
        
        # Si no se encuentra por nombre, intentar identificar por contenido
        for col in df.columns:
            # Verificar si la columna tiene formato de guía (números y posiblemente letras)
            sample = df[col].dropna().head(5)
            if not sample.empty:
                if all(isinstance(x, (str, int)) for x in sample):
                    # Verificar si los valores tienen longitud típica de guías
                    lengths = [len(str(x)) for x in sample if isinstance(x, (str, int))]
                    if lengths and min(lengths) >= 8 and max(lengths) <= 20:
                        return col
        
        return None
    
    def process_files(self, factura_file: UploadedFile, manifiesto_file: UploadedFile) -> bool:
        """
        Procesa los archivos de factura y manifiesto.
        
        Args:
            factura_file: Archivo de factura
            manifiesto_file: Archivo de manifiesto
        
        Returns:
            True si el procesamiento fue exitoso, False en caso contrario
        """
        try:
            # Leer archivos
            if factura_file.name.endswith('.csv'):
                self.df_facturas = pd.read_csv(factura_file)
            else:
                self.df_facturas = pd.read_excel(factura_file)
            
            if manifiesto_file.name.endswith('.csv'):
                self.df_manifiesto = pd.read_csv(manifiesto_file)
            else:
                self.df_manifiesto = pd.read_excel(manifiesto_file)
            
            # Limpiar datos
            self.df_facturas = self.df_facturas.applymap(
                lambda x: x.strip() if isinstance(x, str) else x
            )
            self.df_manifiesto = self.df_manifiesto.applymap(
                lambda x: x.strip() if isinstance(x, str) else x
            )
            
            # Identificar columnas clave
            factura_guide_col = self.identify_guide_column(self.df_facturas)
            manifiesto_guide_col = self.identify_guide_column(self.df_manifiesto)
            
            if not factura_guide_col:
                st.error(f"No se pudo identificar la columna de guías en el archivo de facturas.\nColumnas disponibles: {list(self.df_facturas.columns)}")
                return False
            
            if not manifiesto_guide_col:
                st.error(f"No se pudo identificar la columna de guías en el archivo de manifiesto.\nColumnas disponibles: {list(self.df_manifiesto.columns)}")
                return False
            
            # Crear columna limpia de guías
            self.df_facturas['GUIDE_CLEAN'] = self.df_facturas[factura_guide_col].astype(str).str.strip().str.upper()
            self.df_manifiesto['GUIDE_CLEAN'] = self.df_manifiesto[manifiesto_guide_col].astype(str).str.strip().str.upper()
            
            # Eliminar guías vacías
            self.df_facturas = self.df_facturas[self.df_facturas['GUIDE_CLEAN'] != '']
            self.df_manifiesto = self.df_manifiesto[self.df_manifiesto['GUIDE_CLEAN'] != '']
            
            # Identificar guías facturadas pero no en manifiesto (anuladas)
            self.guides_facturadas = self.df_facturas['GUIDE_CLEAN'].tolist()
            self.guides_anuladas = [
                guide for guide in self.guides_facturadas 
                if guide not in self.df_manifiesto['GUIDE_CLEAN'].values
            ]
            
            # Identificar guías en manifiesto pero no facturadas (sobrantes)
            self.guides_sobrantes = [
                guide for guide in self.df_manifiesto['GUIDE_CLEAN'].tolist()
                if guide not in self.guides_facturadas
            ]
            
            # Calcular KPIs
            self.kpis['total_facturadas'] = len(self.guides_facturadas)
            self.kpis['total_anuladas'] = len(self.guides_anuladas)
            self.kpis['total_sobrantes'] = len(self.guides_sobrantes)
            
            # Calcular valor promedio de envío (simulado)
            if self.kpis['total_facturadas'] > 0:
                # En un sistema real, esto vendría de los datos de facturación
                self.kpis['avg_shipment_value'] = 25.50
            
            # Calcular volumen de envíos por día (simulado)
            self.df_facturas['fecha'] = pd.to_datetime(self.df_facturas.iloc[:, 0], errors='coerce')
            if 'fecha' in self.df_facturas.columns:
                self.shipment_volume = self.df_facturas['fecha'].value_counts().sort_index()
            
            # Calcular anuladas por destinatario (simulado)
            if 'destinatario' in self.df_facturas.columns:
                self.anuladas_by_destinatario = self.df_facturas[
                    self.df_facturas['GUIDE_CLEAN'].isin(self.guides_anuladas)
                ]['destinatario'].value_counts().reset_index()
                self.anuladas_by_destinatario.columns = ['Destinatario', 'Cantidad']
            
            self.processed = True
            return True
        
        except Exception as e:
            logger.error(f"Error al procesar archivos: {str(e)}", exc_info=True)
            st.error(f"Error al procesar los archivos: {str(e)}")
            return False
    
    def generate_report(self) -> bytes:
        """
        Genera un informe PDF con los resultados de la reconciliación.
        
        Returns:
            Bytes del PDF generado
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("Logistics Reconciliation Report", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Datos de KPIs
        kpi_data = [
            ['Métrica', 'Valor'],
            ['Total Facturadas', str(self.kpis.get('total_facturadas', 0))],
            ['Total Anuladas', str(self.kpis.get('total_anuladas', 0))],
            ['Total Sobrantes', str(self.kpis.get('total_sobrantes', 0))],
            ['Valor Promedio de Envío', f"${self.kpis.get('avg_shipment_value', 0):.2f}"]
        ]
        
        table = Table(kpi_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 24))
        
        # Gráfico de volumen de envíos
        if not self.shipment_volume.empty:
            plt.figure(figsize=(8, 4))
            self.shipment_volume.plot(kind='bar', color='steelblue')
            plt.title('Volumen de Envíos por Día')
            plt.xlabel('Fecha')
            plt.ylabel('Cantidad')
            plt.tight_layout()
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG')
            img_buffer.seek(0)
            elements.append(Image(img_buffer, width=500, height=300))
        
        # Anuladas por destinatario
        if not self.anuladas_by_destinatario.empty:
            elements.append(Paragraph("Anuladas por Destinatario", styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            # Preparar datos para tabla
            table_data = [['Destinatario', 'Cantidad']]
            for _, row in self.anuladas_by_destinatario.head(10).iterrows():
                table_data.append([row['Destinatario'], str(row['Cantidad'])])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
            ]))
            elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


def mostrar_reconciliacion_logistica():
    """Muestra la interfaz de reconciliación logística."""
    st.markdown("<h2 class='section-title animate-fade-in'>📦 Reconciliación Logística</h2>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Inicializar el reconciliador en session state si no existe
    if 'reconciler' not in st.session_state:
        st.session_state.reconciler = StreamlitLogisticsReconciliation()
    
    reconciler = st.session_state.reconciler
    
    # Subir archivos
    st.markdown("#### Cargar Archivos")
    col1, col2 = st.columns(2)
    with col1:
        factura_file = st.file_uploader("Archivo de Factura", type=['csv', 'xlsx'])
    with col2:
        manifiesto_file = st.file_uploader("Archivo de Manifiesto", type=['csv', 'xlsx'])
    
    # Procesar archivos
    if factura_file and manifiesto_file:
        if st.button("Procesar Archivos", use_container_width=True):
            with st.spinner("Procesando archivos..."):
                st.session_state.processed = reconciler.process_files(factura_file, manifiesto_file)
    
    # Mostrar resultados
    if hasattr(st.session_state, 'processed') and st.session_state.processed:
        kpis = reconciler.kpis
        
        st.markdown("#### 📊 Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Facturadas", kpis['total_facturadas'])
        col2.metric("Total Anuladas", kpis['total_anuladas'])
        col3.metric("Total Sobrantes", kpis['total_sobrantes'])
        col4.metric("Valor Promedio de Envío", f"${kpis['avg_shipment_value']:.2f}" if kpis['avg_shipment_value'] else "N/A")
        
        # Generar y mostrar informe
        st.markdown("#### Informe Detallado")
        if st.button("Generar Informe PDF", use_container_width=True):
            pdf_bytes = reconciler.generate_report()
            st.download_button(
                label="📥 Descargar Informe PDF",
                data=pdf_bytes,
                file_name=f"reconciliacion_logistica_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        # Mostrar detalles
        with st.expander("Ver Detalles"):
            st.markdown("#### Guías Facturadas")
            st.write(f"Total: {len(reconciler.guides_facturadas)}")
            st.write(", ".join(reconciler.guides_facturadas[:10]) + ("..." if len(reconciler.guides_facturadas) > 10 else ""))
            
            st.markdown("#### Guías Anuladas (Facturadas pero no en Manifiesto)")
            st.write(f"Total: {len(reconciler.guides_anuladas)}")
            st.write(", ".join(reconciler.guides_anuladas[:10]) + ("..." if len(reconciler.guides_anuladas) > 10 else ""))
            
            st.markdown("#### Guías Sobrantes (No Facturadas, en Manifiesto pero no en Facturas)")
            st.write(f"Total: {len(reconciler.guides_sobrantes)}")
            st.write(", ".join(reconciler.guides_sobrantes[:10]) + ("..." if len(reconciler.guides_sobrantes) > 10 else ""))
        
        # Mostrar gráficos
        st.markdown("#### Visualización de Datos")
        
        if not reconciler.shipment_volume.empty:
            st.markdown("##### Volumen de Envíos por Día")
            fig = px.bar(
                reconciler.shipment_volume.reset_index(),
                x='index',
                y=0,
                labels={'index': 'Fecha', '0': 'Cantidad'},
                title='Volumen de Envíos por Día'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        if not reconciler.anuladas_by_destinatario.empty:
            st.markdown("##### Anuladas por Destinatario")
            fig = px.bar(
                reconciler.anuladas_by_destinatario.head(10),
                x='Destinatario',
                y='Cantidad',
                title='Top 10 Destinatarios con Guías Anuladas'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)


# ================================
# FUNCIÓN PRINCIPAL
# ================================

def main():
    """Función principal que inicia la aplicación."""
    # Configurar la página de Streamlit
    st.set_page_config(
        page_title="Aeropostale KPIs",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar estado de sesión si es necesario
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    
    # Mostrar panel de control
    mostrar_panel_control()


if __name__ == "__main__":
    main()
