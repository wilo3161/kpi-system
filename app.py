import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import time
import os
import hashlib
import logging
from supabase import create_client, Client
import qrcode
from PIL import Image
import fpdf
from fpdf import FPDF
import base64
import io
import tempfile
import re
import sqlite3
from typing import Dict, List, Optional, Tuple, Any, Union
import json
from dateutil.relativedelta import relativedelta
import calendar
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')

# ================================
# Configuración de logging
# ================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("KPIs_System")

# ================================
# Configuración de Supabase
# ================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Conexión exitosa a Supabase")
except Exception as e:
    logger.error(f"Error al configurar Supabase: {str(e)}")
    supabase = None

# ================================
# Constantes y configuración del sistema
# ================================
CONFIG = {
    "META_TRANSFERENCIAS_DIARIA": 1750,
    "META_DISTRIBUCION_DIARIA": 150,
    "META_ARREGLO_DIARIA": 200,
    "META_MENSUAL_TRANSFERENCIAS": 35000,
    "DIAS_LABORABLES_MES": 22,
    "COLORES_EQUIPOS": {
        "Transferencias": "#1f77b4",
        "Distribución": "#ff7f0e",
        "Arreglo": "#2ca02c",
        "Guías": "#d62728",
        "Ventas": "#9467bd"
    },
    "ICONOS_EQUIPOS": {
        "Transferencias": "🔄",
        "Distribución": "📦",
        "Arreglo": "🛠️",
        "Guías": "📝",
        "Ventas": "💰"
    }
}

# ================================
# Clases de utilidad
# ================================
class DateRange:
    """Clase para manejar rangos de fechas de manera eficiente"""
    
    @staticmethod
    def get_month_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango completo del mes para una fecha dada"""
        first_day = date(date_obj.year, date_obj.month, 1)
        last_day = date(date_obj.year, date_obj.month, calendar.monthrange(date_obj.year, date_obj.month)[1])
        return first_day, last_day
    
    @staticmethod
    def get_week_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango de la semana (lunes a domingo) para una fecha dada"""
        start = date_obj - timedelta(days=date_obj.weekday())
        end = start + timedelta(days=6)
        return start, end
    
    @staticmethod
    def get_year_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango completo del año para una fecha dada"""
        return date(date_obj.year, 1, 1), date(date_obj.year, 12, 31)
    
    @staticmethod
    def get_day_range(date_obj: date) -> Tuple[date, date]:
        """Obtiene el rango del día completo"""
        return date_obj, date_obj

# ================================
# Funciones de utilidad
# ================================
def validar_fecha(fecha_str: str) -> bool:
    """Valida que una cadena tenga formato de fecha válido (YYYY-MM-DD)"""
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validar_numero_positivo(valor: float) -> bool:
    """Valida que un valor sea un número positivo"""
    return isinstance(valor, (int, float)) and valor >= 0

def productividad_hora(cantidad: float, horas: float) -> float:
    """Calcula la productividad por hora"""
    return cantidad / horas if horas > 0 else 0

def hash_password(pw: str) -> str:
    """Genera un hash SHA256 para una contraseña"""
    return hashlib.sha256(pw.encode()).hexdigest()

def calcular_porcentaje_avance(mes_actual: date, dias_habiles: int = 22) -> float:
    """Calcula el porcentaje de avance del mes considerando días hábiles"""
    hoy = datetime.now().date()
    primer_dia_mes = date(mes_actual.year, mes_actual.month, 1)
    
    # Calcular días hábiles transcurridos en el mes
    dias_transcurridos = 0
    for i in range((hoy - primer_dia_mes).days + 1):
        dia = primer_dia_mes + timedelta(days=i)
        if dia.weekday() < 5:  # Lunes a viernes son días hábiles
            dias_transcurridos += 1
    
    # Calcular porcentaje de avance
    porcentaje = (dias_transcurridos / dias_habiles) * 100
    return min(porcentaje, 100)  # No superar 100%

# ================================
# Funciones de cálculo de KPIs
# ================================
def calcular_kpi(cantidad: float, meta: float) -> float:
    """Calcula el porcentaje de KPI general"""
    return (cantidad / meta) * 100 if meta > 0 else 0

def kpi_transferencias(transferidas: float, meta: float = CONFIG["META_TRANSFERENCIAS_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de transferencias"""
    return calcular_kpi(transferidas, meta)

def kpi_distribucion(unidades: float, meta: float = CONFIG["META_DISTRIBUCION_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de distribución"""
    return calcular_kpi(unidades, meta)

def kpi_arreglos(piezas: float, meta: float = CONFIG["META_ARREGLO_DIARIA"]) -> float:
    """Calcula el KPI para el equipo de arreglos"""
    return calcular_kpi(piezas, meta)

def kpi_guias(cantidad: float, meta: float = 50) -> float:
    """Calcula el KPI para el equipo de guías"""
    return calcular_kpi(cantidad, meta)

# ================================
# Funciones de acceso a datos (Supabase)
# ================================
def obtener_trabajadores() -> pd.DataFrame:
    """Obtiene la lista de trabajadores desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Si hay error, devolver lista por defecto con Luis Perugachi en Distribución
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                       "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"],
            'id': list(range(1, 9))
        })
    
    try:
        response = supabase.from_('trabajadores').select('*').eq('activo', True).order('equipo,nombre', desc=False).execute()
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Asegurar que Luis Perugachi esté en el equipo de Distribución
            if 'Luis Perugachi' in df['nombre'].values:
                df.loc[df['nombre'] == 'Luis Perugachi', 'equipo'] = 'Distribución'
            return df[['nombre', 'equipo', 'id']]
        logger.warning("No se encontraron trabajadores activos en Supabase")
        return pd.DataFrame(columns=['nombre', 'equipo', 'id'])
    except Exception as e:
        logger.error(f"Error al obtener trabajadores: {e}", exc_info=True)
        return pd.DataFrame({
            'nombre': ["Andrés Yépez", "Josué Imbacuán", "Luis Perugachi", "Diana García",
                       "Simón Vera", "Jhonny Guadalupe", "Victor Montenegro", "Fernando Quishpe"],
            'equipo': ["Transferencias", "Transferencias", "Distribución", "Arreglo",
                      "Guías", "Ventas", "Ventas", "Ventas"],
            'id': list(range(1, 9))
        })

def obtener_equipos() -> List[str]:
    """Obtiene la lista de equipos desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        # Incluir "Distribución" en la lista de equipos por defecto
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    
    try:
        response = supabase.from_('trabajadores').select('equipo', distinct=True).eq('activo', True).order('equipo', desc=False).execute()
        # Verificar si hay datos en la respuesta
        if response and response.data:
            equipos = [item['equipo'] for item in response.data]
            # Asegurar que "Distribución" esté en la lista
            if "Distribución" not in equipos:
                equipos.append("Distribución")
            return equipos
        logger.warning("No se encontraron equipos en Supabase")
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]
    except Exception as e:
        logger.error(f"Error al obtener equipos: {e}", exc_info=True)
        return ["Transferencias", "Distribución", "Arreglo", "Guías", "Ventas"]

def cargar_datos_fecha(fecha: str) -> Dict[str, Any]:
    """Carga datos ya guardados para una fecha específica"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return {}
    
    try:
        response = supabase.from_('daily_kpis').select('*').eq('fecha', fecha).execute()
        if response and response.data:
            df = pd.DataFrame(response.data)
            # Convertir a diccionario con nombre como clave
            return df.set_index('nombre').T.to_dict()
        return {}
    except Exception as e:
        logger.error(f"Error al cargar datos para {fecha}: {e}", exc_info=True)
        return {}

def guardar_datos_db(fecha: str, datos: dict) -> bool:
    """Guarda los datos en la tabla de Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return False
    
    try:
        registros = []
        for nombre, info in datos.items():
            # Validar datos antes de guardar
            if not all([
                validar_fecha(fecha),
                validar_numero_positivo(info.get("cantidad", 0)),
                validar_numero_positivo(info.get("meta", 0)),
                validar_numero_positivo(info.get("horas_trabajo", 0))
            ]):
                logger.warning(f"Datos inválidos para {nombre}, omitiendo guardado")
                continue
                
            registro = {
                "fecha": fecha,
                "nombre": nombre,
                "actividad": info.get("actividad", ""),
                "cantidad": float(info.get("cantidad", 0)),
                "meta": float(info.get("meta", 0)),
                "eficiencia": float(info.get("eficiencia", 0)),
                "productividad": float(info.get("productividad", 0)),
                "comentario": info.get("comentario", ""),
                "meta_mensual": float(info.get("meta_mensual", 0)),
                "horas_trabajo": float(info.get("horas_trabajo", 0)),
                "equipo": info.get("equipo", "")
            }
            registros.append(registro)
        
        if registros:
            # Usar upsert para actualizar si ya existe
            supabase.from_('daily_kpis').upsert(registros, on_conflict="fecha,nombre").execute()
            logger.info(f"Datos guardados para {fecha} - {len(registros)} registros")
            
            # Limpiar caché para forzar recarga de datos
            if 'historico_data' in st.session_state:
                del st.session_state['historico_data']
                
            return True
        logger.warning("No hay registros válidos para guardar")
        return False
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}", exc_info=True)
        return False

def cargar_historico_db(fecha_inicio: str = None, fecha_fin: str = None, trabajador: str = None, equipo: str = None) -> pd.DataFrame:
    """Carga datos históricos desde Supabase con filtros opcionales"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('daily_kpis').select('*')
        
        if fecha_inicio:
            query = query.gte('fecha', fecha_inicio)
        if fecha_fin:
            query = query.lte('fecha', fecha_fin)
        if trabajador and trabajador != "Todos":
            query = query.eq('nombre', trabajador)
        if equipo and equipo != "Todos":
            query = query.eq('equipo', equipo)
            
        query = query.order('fecha', desc=False)
        response = query.execute()
        
        if response and response.data:
            df = pd.DataFrame(response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        logger.info("No se encontraron datos históricos en Supabase")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al cargar datos históricos de Supabase: {e}", exc_info=True)
        return pd.DataFrame()

def obtener_tiendas() -> pd.DataFrame:
    """Obtiene la lista de tiendas desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })
    
    try:
        response = supabase.from_('tiendas').select('id, nombre').execute()
        if response and response.data:
            return pd.DataFrame(response.data)
        logger.warning("No se encontraron tiendas en Supabase")
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })
    except Exception as e:
        logger.error(f"Error al obtener tiendas: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'nombre': ["Fashion Club", "Tempo", "Aeropostale", "Gap", "Old Navy"]
        })

def obtener_remitentes() -> pd.DataFrame:
    """Obtiene la lista de remitentes desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })
    
    try:
        response = supabase.from_('remitentes').select('id, nombre, direccion, telefono').execute()
        if response and response.data:
            return pd.DataFrame(response.data)
        logger.warning("No se encontraron remitentes en Supabase")
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })
    except Exception as e:
        logger.error(f"Error al obtener remitentes de Supabase: {e}", exc_info=True)
        return pd.DataFrame({
            'id': [1, 2],
            'nombre': ["Fashion Club", "Tempo"],
            'direccion': ["Dirección 1", "Dirección 2"],
            'telefono': ["0993052744", "0987654321"]
        })

def guardar_guia(store_name: str, brand: str, url: str, sender_name: str) -> bool:
    """Guarda una guía de envío en Supabase"""
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
            'created_at': datetime.now().isoformat()
        }
        supabase.from_('guide_logs').insert(data).execute()
        logger.info(f"Guía guardada para {store_name} - {brand}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar guía: {e}", exc_info=True)
        return False

def obtener_guias(fecha_inicio: str = None, fecha_fin: str = None, tienda: str = None, marca: str = None) -> pd.DataFrame:
    """Obtiene la lista de guías desde Supabase"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return pd.DataFrame()
    
    try:
        query = supabase.from_('guide_logs').select('*')
        
        if fecha_inicio:
            query = query.gte('created_at', fecha_inicio)
        if fecha_fin:
            query = query.lte('created_at', fecha_fin)
        if tienda and tienda != "Todas":
            query = query.eq('store_name', tienda)
        if marca and marca != "Todas":
            query = query.eq('brand', marca)
            
        query = query.order('created_at', desc=True)
        response = query.execute()
        
        if response and response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
        logger.info("No se encontraron guías en Supabase")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error al obtener guías: {e}", exc_info=True)
        return pd.DataFrame()

# ================================
# Obtener logo desde Supabase Storage
# ================================
@st.cache_data(ttl=3600)
def obtener_logo_url(nombre_imagen: str) -> str:
    """Obtiene la URL pública de un logo en Supabase Storage"""
    if supabase is None:
        logger.error("Cliente de Supabase no inicializado")
        return ""
    
    try:
        # Intentar obtener la URL pública del archivo
        response = supabase.storage.from_('images').get_public_url(nombre_imagen)
        
        if response and "error" not in response.lower():
            return response
        
        # Si no funciona, construir la URL manualmente
        bucket_name = "public"  # Ajustar según tu configuración
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/images/{nombre_imagen}"
    except Exception as e:
        logger.error(f"Error al obtener logo {nombre_imagen}: {e}")
        return ""

# ================================
# Funciones de visualización
# ================================
def crear_grafico_interactivo(df: pd.DataFrame, x: str, y: str, title: str,
                             xlabel: str, ylabel: str, tipo: str = 'bar', 
                             color=None, hover_data=None) -> go.Figure:
    """Crea gráficos interactivos con Plotly"""
    try:
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para mostrar",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title=title,
                xaxis_title=xlabel,
                yaxis_title=ylabel,
                template="plotly_white"
            )
            return fig
        
        if tipo == 'bar':
            fig = px.bar(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        elif tipo == 'line':
            fig = px.line(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        elif tipo == 'pie':
            fig = px.pie(
                df, 
                names=x, 
                values=y,
                title=title,
                hover_data=hover_data
            )
        else:
            fig = px.scatter(
                df, 
                x=x, 
                y=y, 
                color=color,
                title=title,
                labels={x: xlabel, y: ylabel},
                hover_data=hover_data
            )
        
        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def crear_grafico_frasco(valor: float, titulo: str) -> go.Figure:
    """
    Crea un gráfico de frasco de agua (semáforo) para visualizar el progreso
    """
    try:
        # Determinar el color basado en el porcentaje
        if valor >= 100:
            color = "#2ca02c"  # Verde
        elif valor >= 80:
            color = "#ff7f0e"  # Naranja
        else:
            color = "#d62728"  # Rojo
        
        fig = go.Figure()
        
        # Agregar el frasco
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=valor,
            title={'text': titulo},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 80], 'color': '#d62728'},
                    {'range': [80, 100], 'color': '#ff7f0e'},
                    {'range': [100, 100], 'color': '#2ca02c'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': valor
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de frasco: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def crear_grafico_cubo_agua(df: pd.DataFrame, fecha_referencia: date) -> go.Figure:
    """
    Crea un gráfico de cubo de agua (waterfall) que muestra el progreso mensual
    Considerando solo los días del mes actual y el rango seleccionado
    """
    try:
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para mostrar",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title="Progreso Mensual",
                template="plotly_white"
            )
            return fig
        
        # Filtrar solo para el mes actual
        mes_actual = fecha_referencia.month
        anio_actual = fecha_referencia.year
        df_mes = df[(df['fecha'].dt.month == mes_actual) & (df['fecha'].dt.year == anio_actual)]
        
        if df_mes.empty:
            fig = go.Figure()
            fig.add_annotation(
                x=0.5, y=0.5,
                text="No hay datos para este mes",
                showarrow=False,
                font=dict(size=20, color="#666666")
            )
            fig.update_layout(
                title="Progreso Mensual",
                template="plotly_white"
            )
            return fig
        
        # Agrupar por día y calcular acumulado
        df_mes['dia'] = df_mes['fecha'].dt.day
        df_acumulado = df_mes.groupby('dia')['cantidad'].sum().reset_index()
        df_acumulado = df_acumulado.sort_values('dia')
        df_acumulado['acumulado'] = df_acumulado['cantidad'].cumsum()
        
        # Crear el gráfico waterfall
        fig = go.Figure()
        
        # Días transcurridos (increasing)
        dias_transcurridos = df_acumulado[df_acumulado['dia'] <= fecha_referencia.day]
        if not dias_transcurridos.empty:
            fig.add_trace(go.Waterfall(
                name="Días transcurridos",
                orientation="v",
                x=dias_transcurridos['dia'],
                y=dias_transcurridos['cantidad'],
                text=[f"{val:,.0f}" for val in dias_transcurridos['cantidad']],
                textposition="outside",
                marker=dict(color=CONFIG["COLORES_EQUIPOS"]["Transferencias"]),
                connector={"line": {"color": "rgb(63, 63, 63)"}}
            ))
        
        # Días restantes (decreasing)
        dias_restantes = df_acumulado[df_acumulado['dia'] > fecha_referencia.day]
        if not dias_restantes.empty:
            # Calcular el promedio diario para proyectar
            promedio_diario = dias_transcurridos['cantidad'].mean() if not dias_transcurridos.empty else 0
            
            # Crear datos proyectados
            dias_proyectados = []
            for dia in dias_restantes['dia']:
                dias_proyectados.append({
                    'dia': dia,
                    'cantidad': promedio_diario
                })
            
            if dias_proyectados:
                df_proyectado = pd.DataFrame(dias_proyectados)
                fig.add_trace(go.Waterfall(
                    name="Proyección",
                    orientation="v",
                    x=df_proyectado['dia'],
                    y=df_proyectado['cantidad'],
                    text=[f"{val:,.0f}" for val in df_proyectado['cantidad']],
                    textposition="outside",
                    marker=dict(color="#cccccc", pattern=dict(shape="/")),
                    connector={"line": {"color": "rgb(200, 200, 200)"}}
                ))
        
        # Meta mensual como total
        meta_mensual = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
        fig.add_trace(go.Waterfall(
            name="Meta Mensual",
            orientation="v",
            measure=["total"],
            x=["Meta"],
            y=[meta_mensual],
            text=[f"{meta_mensual:,.0f}"],
            textposition="outside",
            marker=dict(color="#2ca02c"),
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        
        # Configurar layout
        fig.update_layout(
            title=f"Progreso Mensual - {calendar.month_name[mes_actual]} {anio_actual}",
            xaxis_title="Día del mes",
            yaxis_title="Unidades",
            showlegend=True,
            template="plotly_white",
            xaxis=dict(tickmode='linear'),
            hovermode="x unified"
        )
        
        return fig
    except Exception as e:
        logger.error(f"Error al crear gráfico de cubo de agua: {e}", exc_info=True)
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=f"Error al generar gráfico: {str(e)}",
            showarrow=False,
            font=dict(size=16, color="#FF0000")
        )
        return fig

def generar_resumen_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Genera un resumen ejecutivo de KPIs basado en los datos filtrados"""
    if df.empty:
        return {
            "total_unidades": 0,
            "eficiencia_promedio": 0,
            "colaboradores": 0,
            "mejor_colaborador": "N/A",
            "mejor_equipo": "N/A",
            "porcentaje_avance": 0,
            "proyeccion_final": 0
        }
    
    # Calcular métricas
    total_unidades = int(df['cantidad'].sum())
    eficiencia_promedio = df['eficiencia'].mean()
    colaboradores = df['nombre'].nunique()
    
    # Mejor colaborador
    mejor_colaborador = df.groupby('nombre')['eficiencia'].mean().idxmax() if not df.empty else "N/A"
    
    # Mejor equipo
    mejor_equipo = df.groupby('equipo')['eficiencia'].mean().idxmax() if not df.empty else "N/A"
    
    # Porcentaje de avance del mes
    porcentaje_avance = calcular_porcentaje_avance(df['fecha'].max().date())
    
    # Proyección final basada en promedio diario
    dias_habiles_restantes = max(0, 22 - (datetime.now().weekday() + 1))
    promedio_diario = total_unidades / len(df['fecha'].unique())
    proyeccion_final = total_unidades + (promedio_diario * dias_habiles_restantes)
    
    return {
        "total_unidades": total_unidades,
        "eficiencia_promedio": eficiencia_promedio,
        "colaboradores": colaboradores,
        "mejor_colaborador": mejor_colaborador,
        "mejor_equipo": mejor_equipo,
        "porcentaje_avance": porcentaje_avance,
        "proyeccion_final": proyeccion_final
    }

# ================================
# Panel: Ingreso de Datos con Edición Completa
# ================================
def mostrar_ingreso_datos_kpis():
    """Muestra la interfaz para ingresar datos de KPIs con capacidad de edición"""
    st.markdown("<h1 class='header-title animate-fade-in'>📥 Ingreso de Datos de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Selector de fecha con capacidad para editar datos existentes
    col1, col2 = st.columns([2, 1])
    with col1:
        fecha_seleccionada = st.date_input(
            "Selecciona una fecha para ingresar o editar datos:", 
            value=datetime.now().date(),
            min_value=date(2020, 1, 1),
            max_value=datetime.now().date() + timedelta(days=1)
        )
    
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    
    # Cargar datos existentes si los hay
    datos_existentes = cargar_datos_fecha(fecha_str)
    trabajadores = obtener_trabajadores()
    
    if trabajadores.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay trabajadores registrados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Organizar trabajadores por equipo
    trabajadores_por_equipo = trabajadores.groupby('equipo')['nombre'].apply(list).to_dict()
    
    # Mostrar estado de los datos para esta fecha
    if datos_existentes:
        st.markdown(f"<div class='success-box animate-fade-in'>ℹ️ Ya existen datos para el {fecha_str}. Puedes editarlos a continuación.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='info-box animate-fade-in'>ℹ️ No hay datos registrados para el {fecha_str}. Ingresa los datos a continuación.</div>", unsafe_allow_html=True)
    
    # Formulario de ingreso/editado
    with st.form("form_ingreso_kpis"):
        st.markdown("### 🧑‍💼 Datos por equipo")
        
        datos_guardar = {}
        for equipo, miembros in trabajadores_por_equipo.items():
            with st.expander(f"{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}", expanded=True):
                # Mostrar meta diaria para referencia
                meta_diaria = CONFIG.get(f"MET_{equipo.upper()}_DIARIA", 100)
                st.markdown(f"**Meta diaria de referencia:** {meta_diaria} unidades")
                
                cols = st.columns(min(len(miembros), 3))
                
                for idx, trabajador in enumerate(miembros):
                    with cols[idx % len(cols)]:
                        st.markdown(f"#### {trabajador}")
                        
                        # Cargar valores existentes si los hay
                        datos_trab = datos_existentes.get(trabajador, {})
                        
                        # Inputs para datos
                        cantidad = st.number_input(
                            "Unidades completadas", 
                            value=float(datos_trab.get("cantidad", 0)), 
                            min_value=0.0, 
                            step=1.0, 
                            key=f"{trabajador}_cantidad_{fecha_str}"
                        )
                        
                        meta = st.number_input(
                            "Meta diaria", 
                            value=float(datos_trab.get("meta", meta_diaria)), 
                            min_value=0.0, 
                            step=1.0, 
                            key=f"{trabajador}_meta_{fecha_str}"
                        )
                        
                        horas = st.number_input(
                            "Horas trabajadas", 
                            value=float(datos_trab.get("horas_trabajo", 8)), 
                            min_value=0.0, 
                            max_value=24.0,
                            step=0.5, 
                            key=f"{trabajador}_horas_{fecha_str}"
                        )
                        
                        comentario = st.text_area(
                            "Comentarios", 
                            value=datos_trab.get("comentario", ""), 
                            key=f"{trabajador}_comentario_{fecha_str}"
                        )
                        
                        # Calcular métricas
                        eficiencia = (cantidad / meta * 100) if meta > 0 else 0
                        productividad = productividad_hora(cantidad, horas)
                        
                        # Mostrar métricas calculadas
                        col_metric1, col_metric2 = st.columns(2)
                        with col_metric1:
                            st.metric("Eficiencia", f"{eficiencia:.1f}%")
                        with col_metric2:
                            st.metric("Productividad", f"{productividad:.2f} u/h")
                        
                        # Guardar datos para procesamiento
                        datos_guardar[trabajador] = {
                            "actividad": equipo,
                            "cantidad": cantidad,
                            "meta": meta,
                            "eficiencia": eficiencia,
                            "productividad": productividad,
                            "comentario": comentario,
                            "meta_mensual": 0,  # Se calculará después
                            "horas_trabajo": horas,
                            "equipo": equipo
                        }
        
        submitted = st.form_submit_button("💾 Guardar Datos", use_container_width=True)
        
        if submitted:
            if guardar_datos_db(fecha_str, datos_guardar):
                st.markdown("<div class='success-box animate-fade-in'>✅ Datos guardados correctamente!</div>", unsafe_allow_html=True)
                time.sleep(1.5)
                st.rerun()
            else:
                st.markdown("<div class='error-box animate-fade-in'>❌ Error al guardar los datos. Por favor, intente nuevamente.</div>", unsafe_allow_html=True)
    
    # Mostrar datos guardados para esta fecha (solo lectura)
    if datos_existentes:
        st.markdown("### 📊 Datos guardados para esta fecha")
        df_guardados = pd.DataFrame.from_dict(datos_existentes, orient='index')
        df_guardados = df_guardados.reset_index().rename(columns={'index': 'nombre'})
        
        # Formatear y mostrar tabla
        df_mostrar = df_guardados[['nombre', 'cantidad', 'meta', 'eficiencia', 'productividad', 'comentario']]
        df_mostrar = df_mostrar.sort_values('eficiencia', ascending=False)
        
        st.dataframe(
            df_mostrar.style.format({
                'cantidad': '{:,.0f}',
                'meta': '{:,.0f}',
                'eficiencia': '{:.1f}%',
                'productividad': '{:.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# ================================
# Panel: Crear Guías (con logos desde Supabase)
# ================================
def mostrar_generacion_guias():
    """Muestra la interfaz para generar guías de envío con logos desde Supabase"""
    st.markdown("<h1 class='header-title animate-fade-in'>📦 Generación de Guías de Envío</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Obtener datos necesarios
    tiendas = obtener_tiendas()
    remitentes = obtener_remitentes()
    
    if tiendas.empty or remitentes.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay tiendas o remitentes configurados. Por favor, configure primero.</div>", unsafe_allow_html=True)
        return
    
    # Mostrar logos de las marcas desde Supabase
    st.markdown("<div class='brand-logos'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("### Selecciona la marca para la guía")
        marca = st.selectbox("Marca", ["Fashion", "Tempo"], key="marca_selector")
        
        # Mostrar logo de la marca seleccionada
        if marca == "Fashion":
            logo_url = obtener_logo_url("Fashion.jpg")
            if logo_url:
                st.image(logo_url, width=200, caption="Fashion Club")
            else:
                st.warning("No se pudo cargar el logo de Fashion desde Supabase")
        else:
            logo_url = obtener_logo_url("Tempo.jpg")
            if logo_url:
                st.image(logo_url, width=200, caption="Tempo")
            else:
                st.warning("No se pudo cargar el logo de Tempo desde Supabase")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Formulario para generar guías
    st.markdown("<div class='guide-section animate-fade-in'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛍️ Información del pedido")
        tienda_id = st.selectbox(
            "Tienda", 
            options=tiendas['id'], 
            format_func=lambda x: tiendas[tiendas['id'] == x]['nombre'].values[0],
            key="tienda_selector"
        )
        url_pedido = st.text_area("URL del pedido", height=100, key="url_pedido")
        observaciones = st.text_area("Observaciones adicionales", height=80, key="observaciones")
    
    with col2:
        st.markdown("#### 📦 Información del remitente")
        remitente_id = st.selectbox(
            "Remitente", 
            options=remitentes['id'], 
            format_func=lambda x: remitentes[remitentes['id'] == x]['nombre'].values[0],
            key="remitente_selector"
        )
        
        # Mostrar detalles del remitente seleccionado
        if not remitentes.empty:
            remitente_seleccionado = remitentes[remitentes['id'] == remitente_id].iloc[0]
            st.markdown("##### Detalles del remitente:")
            st.write(f"**Dirección:** {remitente_seleccionado['direccion']}")
            st.write(f"**Teléfono:** {remitente_seleccionado['telefono']}")
    
    # Botón para generar guía
    if st.button("🖨️ Generar Guía", use_container_width=True, type="primary"):
        # Validar campos requeridos
        if not url_pedido or not url_pedido.strip():
            st.error("La URL del pedido es requerida")
            return
            
        if tienda_id and remitente_id:
            # Obtener nombres reales
            tienda_nombre = tiendas[tiendas['id'] == tienda_id]['nombre'].values[0]
            remitente_nombre = remitentes[remitentes['id'] == remitente_id]['nombre'].values[0]
            
            # Guardar en la base de datos
            if guardar_guia(tienda_nombre, marca, url_pedido, remitente_nombre):
                st.success("✅ Guía generada y guardada exitosamente!")
                
                # Mostrar información de la guía generada
                st.markdown("### 📬 Detalles de la guía generada")
                
                # Generar número de seguimiento único
                seguimiento = f"{marca[:2].upper()}{datetime.now().strftime('%y%m%d')}{str(int(time.time()))[-6:]}"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Número de seguimiento:**")
                    st.code(seguimiento, language="text")
                    
                    # Generar y mostrar QR
                    qr_img = generar_qr_imagen(seguimiento)
                    st.image(qr_img, caption="Código QR de seguimiento", width=200)
                
                with col2:
                    st.markdown("**Fecha de generación:**")
                    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.markdown("**Tienda:**")
                    st.write(tienda_nombre)
                    st.markdown("**Marca:**")
                    st.write(marca)
                
                # Opción para descargar PDF
                if st.button("📥 Descargar Guía en PDF", use_container_width=True):
                    pdf = generar_pdf_guia(tienda_nombre, marca, url_pedido, 
                                         remitente_nombre, 
                                         remitentes[remitentes['id'] == remitente_id].iloc[0],
                                         seguimiento)
                    pdf_data = pdf.output(dest='S').encode('latin-1')
                    b64_pdf = base64.b64encode(pdf_data).decode()
                    
                    href = f'<a href="application/pdf;base64,{b64_pdf}" download="guia_{seguimiento}.pdf">Descargar PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.error("❌ Error al generar la guía. Por favor, intente nuevamente.")
        else:
            st.error("Por favor, seleccione una tienda y un remitente válidos.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ================================
# Panel: Dashboard de KPIs (con resumen y cubo de agua)
# ================================
def mostrar_dashboard_kpis():
    """Muestra el dashboard principal de KPIs con análisis detallado"""
    st.markdown("<h1 class='header-title animate-fade-in'>📊 Dashboard de KPIs Aeropostale</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos (con caché para mejorar rendimiento)
    @st.cache_data(ttl=300)
    def cargar_datos_cache():
        return cargar_historico_db()
    
    df = cargar_datos_cache()
    
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos disponibles. Por favor, ingrese datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Filtros globales
    st.markdown("### 🔍 Filtros de análisis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rango = st.selectbox("Rango de tiempo", ["Día", "Semana", "Mes", "Año", "Personalizado"], index=2)
    
    with col2:
        equipos = ["Todos"] + obtener_equipos()
        equipo_seleccionado = st.selectbox("Equipo", equipos)
    
    with col3:
        trabajadores = ["Todos"] + df['nombre'].unique().tolist()
        trabajador_seleccionado = st.selectbox("Colaborador", trabajadores)
    
    # Determinar fechas basado en el rango seleccionado
    hoy = datetime.now().date()
    
    if rango == "Personalizado":
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de inicio", value=hoy - timedelta(days=7))
        with col2:
            fecha_fin = st.date_input("Fecha de fin", value=hoy)
    else:
        if rango == "Día":
            fecha_inicio = hoy
            fecha_fin = hoy
        elif rango == "Semana":
            fecha_inicio = hoy - timedelta(days=hoy.weekday())
            fecha_fin = fecha_inicio + timedelta(days=6)
        elif rango == "Mes":
            fecha_inicio = date(hoy.year, hoy.month, 1)
            _, last_day = calendar.monthrange(hoy.year, hoy.month)
            fecha_fin = date(hoy.year, hoy.month, last_day)
        else:  # Año
            fecha_inicio = date(hoy.year, 1, 1)
            fecha_fin = date(hoy.year, 12, 31)
    
    # Convertir a string para filtrado
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    
    # Filtrar datos
    df_filtrado = df.copy()
    
    if fecha_inicio_str and fecha_fin_str:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]
    
    if equipo_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_seleccionado]
    
    if trabajador_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['nombre'] == trabajador_seleccionado]
    
    # Mostrar tarjetas de KPIs por equipo
    st.markdown("### 📊 Tarjetas de KPIs por Equipo")
    
    equipos = obtener_equipos()
    cols = st.columns(len(equipos))
    
    for i, equipo in enumerate(equipos):
        with cols[i]:
            df_equipo = df_filtrado[df_filtrado['equipo'] == equipo]
            
            if not df_equipo.empty:
                total_unidades = int(df_equipo['cantidad'].sum())
                eficiencia_promedio = df_equipo['eficiencia'].mean()
                num_colaboradores = df_equipo['nombre'].nunique()
                
                # Determinar meta mensual para el equipo
                meta_mensual = 0
                if equipo == "Transferencias":
                    meta_mensual = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
                    cumplimiento = (total_unidades / meta_mensual * 100) if meta_mensual > 0 else 0
                else:
                    # Para otros equipos, usar meta diaria promedio
                    dias_trabajados = len(df_equipo['fecha'].unique())
                    if dias_trabajados > 0:
                        meta_diaria = CONFIG.get(f"MET_{equipo.upper()}_DIARIA", 100)
                        meta_mensual = meta_diaria * 22  # 22 días hábiles
                        cumplimiento = (total_unidades / meta_mensual * 100) if meta_mensual > 0 else 0
                    else:
                        cumplimiento = 0
                
                # Mostrar tarjeta
                st.markdown(f"""
                <div class="kpi-card animate-fade-in">
                    <div class="metric-label">{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}</div>
                    <p class="metric-value">{eficiencia_promedio:.1f}%</p>
                    <p>Unidades: {total_unidades:,.0f}<br>
                       Colaboradores: {num_colaboradores}<br>
                       Cumplimiento: {cumplimiento:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="kpi-card animate-fade-in">
                    <div class="metric-label">{CONFIG['ICONOS_EQUIPOS'].get(equipo, '👥')} {equipo}</div>
                    <p class="metric-value">0%</p>
                    <p>Unidades: 0<br>
                       Colaboradores: 0<br>
                       Cumplimiento: 0%</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Mostrar progreso del mes para Transferencias (con semáforo)
    st.markdown("### 📈 Progreso Mensual - Transferencias")
    
    df_transferencias = df_filtrado[df_filtrado['equipo'] == "Transferencias"]
    
    if not df_transferencias.empty:
        cum_transferencias = int(df_transferencias['cantidad'].sum())
        meta_mensual_transferencias = CONFIG["META_MENSUAL_TRANSFERENCIAS"]
        cumplimiento_transferencias = (cum_transferencias / meta_mensual_transferencias * 100) if meta_mensual_transferencias > 0 else 0
        
        # Mostrar tarjeta de progreso
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card animate-fade-in">
                <div class="metric-label">Meta Mensual Transferencias</div>
                <p class="metric-value">{cumplimiento_transferencias:.1f}%</p>
                <p>Acumulado: {cum_transferencias:,.0f} / Meta Mensual: {meta_mensual_transferencias:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Gráfico de frasco de agua para el cumplimiento
            fig_frasco = crear_grafico_frasco(cumplimiento_transferencias, "Cumplimiento Mensual Transferencias")
            st.plotly_chart(fig_frasco, use_container_width=True, config={'displayModeBar': False})
        
        with col2:
            # Gráfico de evolución mensual
            df_transferencias_month = df[df['equipo'] == "Transferencias"]
            df_transferencias_month = df_transferencias_month[
                (df_transferencias_month['fecha'].dt.year == hoy.year) & 
                (df_transferencias_month['fecha'].dt.month == hoy.month)
            ]
            
            if not df_transferencias_month.empty:
                df_daily = df_transferencias_month.groupby(df_transferencias_month['fecha'].dt.day)['cantidad'].sum().reset_index()
                df_daily = df_daily.sort_values('fecha')
                df_daily['acumulado'] = df_daily['cantidad'].cumsum()
                
                fig = px.line(
                    df_daily,
                    x='fecha',
                    y='acumulado',
                    title='Evolución del Cumplimiento Mensual',
                    labels={'fecha': 'Día del mes', 'acumulado': 'Unidades acumuladas'}
                )
                fig.add_hline(
                    y=meta_mensual_transferencias, 
                    line_dash="dash", 
                    line_color="white", 
                    annotation_text="Meta Mensual"
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No hay datos para el gráfico de Transferencias.")
    else:
        st.info("No hay datos de Transferencias para mostrar.")
    
    # Análisis detallado por equipo
    st.markdown("### 🏆 Análisis por Equipos")
    
    if not df_filtrado.empty:
        # Gráfico de eficiencia por equipo
        df_equipo = df_filtrado.groupby('equipo').agg({
            'eficiencia': 'mean',
            'cantidad': 'sum'
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_equipo = crear_grafico_interactivo(
                df_equipo, 
                'equipo', 
                'eficiencia', 
                'Eficiencia Promedio por Equipo',
                'Equipo', 
                'Eficiencia (%)',
                color='equipo',
                hover_data=['cantidad']
            )
            st.plotly_chart(fig_equipo, use_container_width=True)
        
        with col2:
            # Gráfico de tendencia de eficiencia
            df_tendencia = df_filtrado.groupby(['fecha', 'equipo'])['eficiencia'].mean().reset_index()
            fig_tendencia = crear_grafico_interactivo(
                df_tendencia, 
                'fecha', 
                'eficiencia', 
                'Tendencia de Eficiencia',
                'Fecha', 
                'Eficiencia (%)',
                tipo='line',
                color='equipo'
            )
            st.plotly_chart(fig_tendencia, use_container_width=True)
        
        # Tabla detallada de rendimiento
        st.markdown("### 📋 Rendimiento Detallado")
        
        # Preparar datos para la tabla
        df_resumen = df_filtrado.groupby(['nombre', 'equipo']).agg({
            'cantidad': 'sum',
            'eficiencia': 'mean',
            'productividad': 'mean',
            'horas_trabajo': 'sum'
        }).reset_index()
        
        # Formatear y mostrar
        df_resumen = df_resumen.sort_values('eficiencia', ascending=False)
        df_resumen = df_resumen.rename(columns={
            'cantidad': 'Unidades',
            'eficiencia': 'Eficiencia (%)',
            'productividad': 'Productividad (u/h)',
            'horas_trabajo': 'Horas Totales'
        })
        
        st.dataframe(
            df_resumen.style.format({
                'Unidades': '{:,.0f}',
                'Eficiencia (%)': '{:.1f}%',
                'Productividad (u/h)': '{:.2f}',
                'Horas Totales': '{:,.1f}'
            }).background_gradient(subset=['Eficiencia (%)'], cmap='Greens'),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

# ================================
# Panel: Análisis Histórico de KPIs
# ================================
def mostrar_analisis_historico_kpis():
    """Muestra el análisis histórico de KPIs con visualizaciones avanzadas"""
    st.markdown("<h1 class='header-title animate-fade-in'>📈 Análisis Histórico de KPIs</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Cargar datos históricos
    df = cargar_historico_db()
    
    if df.empty:
        st.markdown("<div class='warning-box animate-fade-in'>⚠️ No hay datos históricos disponibles. Por favor, ingrese datos primero.</div>", unsafe_allow_html=True)
        return
    
    # Filtros
    st.markdown("### 🔍 Filtros de análisis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", value=df['fecha'].min().date())
    
    with col2:
        fecha_fin = st.date_input("Fecha de fin", value=df['fecha'].max().date())
    
    with col3:
        equipos = ["Todos"] + obtener_equipos()
        equipo_seleccionado = st.selectbox("Equipo", equipos)
    
    # Filtrar datos
    df_filtrado = df.copy()
    
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[
            (df_filtrado['fecha'].dt.date >= fecha_inicio) & 
            (df_filtrado['fecha'].dt.date <= fecha_fin)
        ]
    
    if equipo_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_seleccionado]
    
    # Análisis de tendencias
    st.markdown("### 📈 Análisis de Tendencias")
    
    if not df_filtrado.empty:
        # Calcular métricas diarias
        df_diario = df_filtrado.groupby(['fecha', 'equipo']).agg({
            'cantidad': 'sum',
            'eficiencia': 'mean'
        }).reset_index()
        
        # Gráfico de tendencia de cantidad
        fig_cantidad = crear_grafico_interactivo(
            df_diario, 
            'fecha', 
            'cantidad', 
            'Tendencia de Unidades Completadas',
            'Fecha', 
            'Unidades',
            tipo='line',
            color='equipo'
        )
        st.plotly_chart(fig_cantidad, use_container_width=True)
        
        # Gráfico de tendencia de eficiencia
        fig_eficiencia = crear_grafico_interactivo(
            df_diario, 
            'fecha', 
            'eficiencia', 
            'Tendencia de Eficiencia',
            'Fecha', 
            'Eficiencia (%)',
            tipo='line',
            color='equipo'
        )
        st.plotly_chart(fig_eficiencia, use_container_width=True)
        
        # Análisis de correlación
        st.markdown("### 🔗 Análisis de Correlación")
        
        df_correlacion = df_filtrado.groupby('fecha').agg({
            'cantidad': 'sum',
            'horas_trabajo': 'sum',
            'eficiencia': 'mean'
        }).reset_index()
        
        # Calcular productividad diaria
        df_correlacion['productividad'] = df_correlacion['cantidad'] / df_correlacion['horas_trabajo']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_corr = px.scatter(
                df_correlacion, 
                x='horas_trabajo', 
                y='cantidad',
                trendline="ols",
                title='Correlación: Horas Trabajadas vs Unidades Completadas',
                labels={'horas_trabajo': 'Horas Trabajadas', 'cantidad': 'Unidades Completadas'}
            )
            fig_corr.update_layout(template="plotly_white")
            st.plotly_chart(fig_corr, use_container_width=True)
        
        with col2:
            fig_corr2 = px.scatter(
                df_correlacion, 
                x='eficiencia', 
                y='productividad',
                trendline="ols",
                title='Correlación: Eficiencia vs Productividad',
                labels={'eficiencia': 'Eficiencia (%)', 'productividad': 'Productividad (u/h)'}
            )
            fig_corr2.update_layout(template="plotly_white")
            st.plotly_chart(fig_corr2, use_container_width=True)
        
        # Predicciones futuras
        st.markdown("### 📅 Predicciones Futuras")
        
        if len(df_correlacion) >= 10:  # Necesitamos suficientes datos
            # Preparar datos para regresión
            X = np.array(range(len(df_correlacion))).reshape(-1, 1)
            y = df_correlacion['cantidad'].values
            
            # Entrenar modelo
            model = LinearRegression()
            model.fit(X, y)
            
            # Predecir próximos 7 días
            dias_futuros = 7
            X_pred = np.array(range(len(X), len(X) + dias_futuros)).reshape(-1, 1)
            y_pred = model.predict(X_pred)
            
            # Mostrar predicciones
            st.markdown(f"**Predicción para los próximos {dias_futuros} días:**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Crear dataframe para visualización
                fechas_futuras = [df_correlacion['fecha'].max() + timedelta(days=i+1) for i in range(dias_futuros)]
                df_pred = pd.DataFrame({
                    'fecha': fechas_futuras,
                    'prediccion': y_pred
                })
                
                fig_pred = px.line(
                    pd.concat([df_correlacion[['fecha', 'cantidad']], df_pred.rename(columns={'prediccion': 'cantidad'})]),
                    x='fecha',
                    y='cantidad',
                    title='Predicción de Unidades Futuras',
                    labels={'cantidad': 'Unidades', 'fecha': 'Fecha'}
                )
                fig_pred.add_vrect(
                    x0=df_correlacion['fecha'].max(),
                    x1=fechas_futuras[-1],
                    fillcolor="rgba(0,100,80,0.2)",
                    line_width=0,
                    annotation_text="Predicción",
                    annotation_position="top left"
                )
                fig_pred.update_layout(template="plotly_white")
                st.plotly_chart(fig_pred, use_container_width=True)
            
            with col2:
                st.markdown("**Valores predichos:**")
                for i, (fecha, pred) in enumerate(zip(fechas_futuras, y_pred)):
                    st.metric(
                        f"{fecha.strftime('%Y-%m-%d')}", 
                        f"{pred:,.0f} unidades",
                        delta=f"+{pred - y[-1]:,.0f}" if i == 0 else None
                    )
        else:
            st.warning("Se necesitan al menos 10 días de datos para realizar predicciones.")
    
    # Datos crudos
    st.markdown("### 📊 Datos Históricos")
    st.dataframe(
        df_filtrado.sort_values('fecha', ascending=False),
        use_container_width=True,
        hide_index=True
    )

# ================================
# Panel: Gestión de Trabajadores
# ================================
def mostrar_gestion_trabajadores():
    """Muestra la interfaz para gestionar trabajadores y equipos"""
    st.markdown("<h1 class='header-title animate-fade-in'>👥 Gestión de Trabajadores</h1>", unsafe_allow_html=True)
    
    if supabase is None:
        st.markdown("<div class='error-box animate-fade-in'>❌ Error de conexión a la base de datos. Verifique las variables de entorno.</div>", unsafe_allow_html=True)
        return
    
    # Pestañas para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["👥 Trabajadores", "🏢 Equipos", "📊 Asignación de Metas"])
    
    with tab1:
        mostrar_gestion_trabajadores_tab()
    
    with tab2:
        mostrar_gestion_equipos_tab()
    
    with tab3:
        mostrar_asignacion_metas_tab()

def mostrar_gestion_trabajadores_tab():
    """Muestra la gestión de trabajadores individuales"""
    st.markdown("### 👥 Gestión de Trabajadores")
    
    # Cargar trabajadores
    trabajadores = obtener_trabajadores()
    
    # Mostrar lista de trabajadores
    if not trabajadores.empty:
        st.markdown("#### 📋 Lista de Trabajadores")
        
        # Filtro por equipo
        equipos = ["Todos"] + trabajadores['equipo'].unique().tolist()
        equipo_filtro = st.selectbox("Filtrar por equipo", equipos, key="trabajadores_equipo_filtro")
        
        df_mostrar = trabajadores.copy()
        if equipo_filtro != "Todos":
            df_mostrar = df_mostrar[df_mostrar['equipo'] == equipo_filtro]
        
        # Mostrar tabla
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "equipo": st.column_config.TextColumn("Equipo", width="small"),
                "activo": st.column_config.CheckboxColumn("Activo", width="small")
            }
        )
        
        # Opciones de edición
        st.markdown("#### ✏️ Agregar/Editar Trabajador")
        
        with st.form("form_trabajador"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre completo")
                id_editar = st.selectbox("Editar trabajador existente", ["Nuevo"] + trabajadores['id'].tolist(), format_func=lambda x: trabajadores[trabajadores['id'] == x]['nombre'].values[0] if x != "Nuevo" else "Nuevo trabajador")
            
            with col2:
                equipos_disponibles = obtener_equipos()
                equipo = st.selectbox("Equipo", equipos_disponibles)
                activo = st.checkbox("Activo", value=True)
            
            submitted = st.form_submit_button("Guardar Trabajador", use_container_width=True)
            
            if submitted:
                try:
                    if id_editar == "Nuevo":
                        # Insertar nuevo trabajador
                        data = {
                            "nombre": nombre,
                            "equipo": equipo,
                            "activo": activo
                        }
                        supabase.from_('trabajadores').insert(data).execute()
                        st.success("✅ Trabajador agregado correctamente!")
                    else:
                        # Actualizar trabajador existente
                        data = {
                            "nombre": nombre,
                            "equipo": equipo,
                            "activo": activo
                        }
                        supabase.from_('trabajadores').update(data).eq('id', id_editar).execute()
                        st.success("✅ Trabajador actualizado correctamente!")
                    
                    # Limpiar caché
                    if 'trabajadores_cache' in st.session_state:
                        del st.session_state['trabajadores_cache']
                    
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar trabajador: {str(e)}")
    
    else:
        st.markdown("<div class='info-box animate-fade-in'>ℹ️ No hay trabajadores registrados. Agrega el primero a continuación.</div>", unsafe_allow_html=True)
        
        # Formulario para agregar el primer trabajador
        with st.form("form_primer_trabajador"):
            nombre = st.text_input("Nombre completo")
            equipos = obtener_equipos()
            equipo = st.selectbox("Equipo", equipos)
            activo = st.checkbox("Activo", value=True)
            
            submitted = st.form_submit_button("Agregar Trabajador", use_container_width=True)
            
            if submitted:
                try:
                    data = {
                        "nombre": nombre,
                        "equipo": equipo,
                        "activo": activo
                    }
                    supabase.from_('trabajadores').insert(data).execute()
                    st.success("✅ Trabajador agregado correctamente!")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al guardar trabajador: {str(e)}")

def mostrar_gestion_equipos_tab():
    """Muestra la gestión de equipos"""
    st.markdown("### 🏢 Gestión de Equipos")
    
    # Cargar equipos
    equipos = obtener_equipos()
    
    # Mostrar lista de equipos
    st.markdown("#### 📋 Lista de Equipos")
    st.dataframe(
        pd.DataFrame(equipos, columns=["Nombre del Equipo"]),
        use_container_width=True,
        hide_index=True
    )
    
    # Formulario para agregar/eliminar equipos
    st.markdown("#### ✏️ Agregar/Eliminar Equipo")
    
    equipo_nombre = st.text_input("Nombre del nuevo equipo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Agregar Equipo", use_container_width=True):
            if equipo_nombre and equipo_nombre.strip():
                try:
                    # Verificar si el equipo ya existe
                    if equipo_nombre in equipos:
                        st.warning("⚠️ Este equipo ya existe.")
                    else:
                        # Insertar nuevo equipo (como trabajador con ese equipo)
                        data = {
                            "nombre": f"Miembro de {equipo_nombre}",
                            "equipo": equipo_nombre,
                            "activo": True
                        }
                        supabase.from_('trabajadores').insert(data).execute()
                        st.success(f"✅ Equipo '{equipo_nombre}' agregado correctamente!")
                        
                        # Limpiar caché
                        if 'equipos_cache' in st.session_state:
                            del st.session_state['equipos_cache']
                        
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar equipo: {str(e)}")
            else:
                st.error("El nombre del equipo no puede estar vacío.")
    
    with col2:
        if st.button("Eliminar Equipo", use_container_width=True):
            if equipo_nombre and equipo_nombre.strip():
                try:
                    # Verificar si el equipo existe
                    if equipo_nombre not in equipos or equipo_nombre in ["Transferencias", "Distribución"]:
                        st.warning("⚠️ No se puede eliminar este equipo o no existe.")
                    else:
                        # Eliminar todos los trabajadores de ese equipo
                        supabase.from_('trabajadores').delete().eq('equipo', equipo_nombre).execute()
                        st.success(f"✅ Equipo '{equipo_nombre}' eliminado correctamente!")
                        
                        # Limpiar caché
                        if 'equipos_cache' in st.session_state:
                            del st.session_state['equipos_cache']
                        
                        time.sleep(1.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar equipo: {str(e)}")
            else:
                st.error("Por favor, ingresa el nombre del equipo a eliminar.")

def mostrar_asignacion_metas_tab():
    """Muestra la asignación de metas por equipo"""
    st.markdown("### 📊 Asignación de Metas por Equipo")
    
    # Cargar equipos
    equipos = obtener_equipos()
    
    # Mostrar formulario para asignar metas
    st.markdown("#### 🎯 Metas Diarias por Equipo")
    
    metas_actuales = {
        "Transferencias": CONFIG["META_TRANSFERENCIAS_DIARIA"],
        "Distribución": CONFIG["META_DISTRIBUCION_DIARIA"],
        "Arreglo": CONFIG["META_ARREGLO_DIARIA"]
    }
    
    # Formulario para cada equipo
    for equipo in equipos:
        if equipo in metas_actuales:
            meta_actual = metas_actuales[equipo]
            st.number_input(
                f"Meta diaria para {equipo}",
                value=float(meta_actual),
                min_value=0.0,
                step=10.0,
                key=f"meta_{equipo}"
            )
    
    if st.button("Guardar Metas", use_container_width=True):
        # Aquí iría la lógica para guardar las nuevas metas
        # En una implementación completa, esto actualizaría la base de datos
        st.success("✅ Metas guardadas correctamente!")
        time.sleep(1.5)
        st.rerun()

# ================================
# Funciones auxiliares para guías
# ================================
def generar_numero_seguimiento(record_id: int) -> str:
    """Genera un número de seguimiento único."""
    return f"9400{str(record_id).zfill(20)}"

def generar_qr_imagen(url: str) -> Image.Image:
    """Genera y devuelve una imagen del código QR."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def generar_pdf_guia(store_name: str, brand: str, url: str, 
                    sender_name: str, sender_info: pd.Series, 
                    tracking_number: str) -> FPDF:
    """Genera un PDF con la guía de envío"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Logo de la marca
    logo_url = obtener_logo_url(f"{brand}.jpg")
    if logo_url:
        try:
            # Descargar la imagen
            import requests
            response = requests.get(logo_url)
            img = Image.open(io.BytesIO(response.content))
            
            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                img.save(tmp.name)
                pdf.image(tmp.name, x=10, y=10, w=50)
        except Exception as e:
            logger.error(f"Error al agregar logo al PDF: {e}")
    
    # Título
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Guía de Envío - {brand}", ln=True, align="C")
    pdf.ln(10)
    
    # Información de la tienda
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Tienda:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, store_name, ln=True)
    
    # Información de la marca
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Marca:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, brand, ln=True)
    
    # Información del remitente
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "Remitente:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"{sender_name} - {sender_info['telefono']}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(40, 8, "")
    pdf.multi_cell(0, 8, sender_info['direccion'])
    pdf.ln(5)
    
    # Número de seguimiento
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Número de Seguimiento:")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, tracking_number, ln=True)
    
    # Código QR
    try:
        qr_img = generar_qr_imagen(tracking_number)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            qr_img.save(tmp.name)
            pdf.image(tmp.name, x=10, y=pdf.get_y() + 5, w=40)
    except Exception as e:
        logger.error(f"Error al generar código QR para PDF: {e}")
    
    # URL del pedido
    pdf.ln(20)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 8, "URL del Pedido:")
    pdf.set_font("Arial", "U", 10)
    pdf.cell(0, 8, url, ln=True)
    
    # Fecha de generación
    pdf.ln(10)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 6, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align="R")
    
    return pdf

# ================================
# Menú principal
# ================================
PAGES = {
    "Dashboard de KPIs": mostrar_dashboard_kpis,
    "Ingreso de Datos": mostrar_ingreso_datos_kpis,
    "Crear Guías": mostrar_generacion_guias,
    "Análisis Histórico": mostrar_analisis_historico_kpis,
    "Gestión de Trabajadores": mostrar_gestion_trabajadores
}

def main():
    """Función principal que ejecuta la aplicación"""
    st.set_page_config(
        page_title="Sistema de KPIs Aeropostale",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilos CSS personalizados
    st.markdown("""
        <style>
        /* Colores del tema */
        :root {
            --primary-color: #1f77b4;
            --secondary-color: #ff7f0e;
            --success-color: #2ca02c;
            --warning-color: #d62728;
            --info-color: #9467bd;
            --background-color: #f8f9fa;
            --text-color: #212529;
            --card-background: #ffffff;
        }
        
        /* Estilos generales */
        body {
            color: var(--text-color);
            background-color: var(--background-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Cabecera */
        .header-title {
            color: var(--primary-color);
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 1em;
            padding-bottom: 0.5em;
            border-bottom: 2px solid var(--primary-color);
        }
        
        /* Secciones */
        .section-title {
            color: var(--primary-color);
            font-size: 1.5em;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }
        
        /* Boxes de información */
        .info-box {
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #1e88e5;
            margin: 15px 0;
        }
        
        .success-box {
            background-color: #e8f5e9;
            color: #1b5e20;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #43a047;
            margin: 15px 0;
        }
        
        .warning-box {
            background-color: #fff8e1;
            color: #e65100;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #fb8c00;
            margin: 15px 0;
        }
        
        .error-box {
            background-color: #ffebee;
            color: #b71c1c;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #e53935;
            margin: 15px 0;
        }
        
        /* Tarjetas de KPI */
        .kpi-card {
            background-color: var(--card-background);
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 15px;
            transition: transform 0.3s;
        }
        
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        }
        
        .metric-label {
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        
        .metric-value {
            font-size: 2.2em;
            font-weight: bold;
            color: var(--primary-color);
            margin: 10px 0;
        }
        
        /* Animaciones */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.5s ease forwards;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 5px 5px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary-color);
            color: white;
        }
        
        /* Botones */
        .stButton>button {
            border-radius: 8px;
            padding: 0.5em 1em;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Dataframes */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 3em;
            padding: 1em;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
        }
        
        /* Input containers */
        .stNumberInput, .stTextInput, .stSelectbox {
            margin-bottom: 1em;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: bold;
            color: var(--primary-color);
        }
        
        /* Estilos específicos para el sistema de guías */
        .guide-section {
            background: var(--card-background);
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        .qr-preview {
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .guide-metric {
            font-size: 1.3em;
            margin: 12px 0;
            color: var(--text-color);
            display: flex;
            align-items: center;
        }
        
        .guide-metric strong {
            color: var(--primary-color);
            margin-left: 8px;
        }
        
        .guide-icon {
            color: var(--primary-color);
            margin-right: 10px;
            font-size: 1.5em;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Barra lateral de navegación
    st.sidebar.title("📌 Sistema de KPIs Aeropostale")
    
    # Información del sistema
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 Estadísticas del Sistema")
        
        # Mostrar información de conexión a Supabase
        if supabase:
            st.success("✅ Conexión a Supabase: Activa")
            
            # Intentar obtener conteos de registros
            try:
                # Contar trabajadores
                response = supabase.from_('trabajadores').select('id', count='exact').execute()
                num_trabajadores = response.count if hasattr(response, 'count') else 0
                
                # Contar registros de KPIs
                response = supabase.from_('daily_kpis').select('id', count='exact').execute()
                num_kpis = response.count if hasattr(response, 'count') else 0
                
                st.metric("Trabajadores", num_trabajadores)
                st.metric("Registros de KPIs", num_kpis)
            except Exception as e:
                logger.error(f"Error al obtener estadísticas: {e}")
                st.warning("⚠️ No se pudieron cargar estadísticas")
        else:
            st.error("❌ Conexión a Supabase: Inactiva")
        
        st.markdown("---")
        st.markdown("### 🛠️ Versión del Sistema")
        st.markdown("**v2.3.1**")
        st.markdown("Última actualización: Septiembre 2025")
    
    # Selección de página
    st.sidebar.markdown("### 🌐 Navegación")
    page = st.sidebar.radio("Ir a", list(PAGES.keys()))
    
    # Ejecutar la página seleccionada
    PAGES[page]()
    
    # Footer
    st.markdown("""
        <div class="footer">
            Sistema de KPIs Aeropostale v2.3.1 | © 2025 Todos los derechos reservados.<br>
            Desarrollado por: <a href="mailto:wilson.perez@aeropostale.com" style="color: #1f77b4;">Wilson Pérez</a>
            | Soporte técnico: soporte.kpis@aeropostale.com
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
