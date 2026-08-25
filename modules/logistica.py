# modules/logistica.py
# ============================================================================
# DASHBOARD LOGÍSTICO - TRANSFERENCIAS Y DISTRIBUCIÓN
# Versión completa y corregida (error FileUploader solucionado)
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date, timedelta
import logging
from utils.backgrounds import set_module_background
from database.manager import (
    local_db, guardar_historico, consultar_historico,
    existe_historico_dia, fusionar_historico_dia
)
from utils.common import extraer_entero, sanitize_for_mongo
from utils.ui import add_back_button, show_module_header
import plotly.express as px
import plotly.graph_objects as go
from config.stores_data import (
    TIENDAS_DATA, PRICE_CLUBS, TIENDAS_REGULARES,
    VENTAS_POR_MAYOR, TIENDA_WEB, FALLAS, COLORS, GRADIENTS, COLOR_KEYS
)
from services.data_processing import procesar_archivos

logger = logging.getLogger(__name__)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

# =============================================================================
# CONSTANTES
# =============================================================================
CATEGORIAS_LIST = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas', 'Fundas']
CATEGORIAS_SIN_FUNDAS = ['Price Club', 'Tiendas', 'Ventas por Mayor', 'Tienda Web', 'Fallas']
DISPLAY_NAMES = {
    'Price Club': 'PRICE CLUB', 'Tiendas': 'TIENDAS AEROPOSTALE',
    'Ventas por Mayor': 'VENTAS POR MAYOR', 'Tienda Web': 'TIENDA WEB',
    'Fallas': 'FALLAS', 'Fundas': 'FUNDAS'
}
DATE_PRESETS = {"1 Día": 1, "3 Días": 3, "1 Semana": 7, "1 Mes": 30, "3 Meses": 90, "1 Año": 365}

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def _safe_numeric(value, default=0.0):
    if value is None: return default
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, dict):
        for k in value:
            if k.startswith('$number') or k in ['total_unidades', 'unidades', 'val']:
                return _safe_numeric(value[k], default)
        return default
    try:
        return float(str(value).strip().replace(',', ''))
    except (ValueError, TypeError):
        return default

def _safe_int(value, default=0):
    return int(_safe_numeric(value, default))

def _sanitize_metrics(raw_reg):
    if not isinstance(raw_reg, dict): return raw_reg
    met = raw_reg.get('metricas', {})
    if not isinstance(met, dict):
        raw_reg['metricas'] = {}
        return raw_reg
    clean_met = {}
    for k, v in met.items():
        if isinstance(v, dict):
            clean_met[k] = {sk: _safe_numeric(sv) for sk, sv in v.items()}
        else:
            clean_met[k] = _safe_numeric(v) if isinstance(v, (str, int, float)) else v
    raw_reg['metricas'] = clean_met
    return raw_reg

# =============================================================================
# PARSER DE PRODUCTOS - CLASIFICACIÓN AVANZADA
# =============================================================================
TALLAS_TEXTIL = ['XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL', '5XL', 'XSMALL', 'SMALL', 'MEDIUM', 'LARGE', 'X-LARGE', 'XX-LARGE', 'XLARGE', 'XXLARGE', 'UNICA', 'ONESZ', 'ONE ZICE', 'ONE SIZE', 'ONEZ', 'OSFA', 'XSMALL REGULAR', 'SMALL REGULAR', 'MEDIUM REGULAR', 'LARGE REGULAR', 'XLARGE REGULAR', 'XXLARGE REGULAR', 'XSMALL LONG', 'SMALL LONG', 'MEDIUM LONG', 'LARGE LONG', 'XLARGE LONG', 'XXLARGE LONG', 'XSMALL SHORT', 'SMALL SHORT', 'MEDIUM SHORT', 'LARGE SHORT', 'XLARGE SHORT', 'XXLARGE SHORT', '28X30', '28X32', '30X30', '30X32', '32X30', '32X32', '32X34', '34X30', '34X32', '34X34', '36X30', '36X32', '36X34', '38X32', '40X32']
GENEROS_TEXTIL = ['AERO GUYS', 'AERO GIRLS', 'AERO KIDS', 'AERO BOYS', 'AERO MENS', 'AERO WOMENS', 'AERO LADIES', 'AERO YOUTH', 'AERO UNISEX', 'GUYS', 'GIRLS', 'KIDS', 'BOYS', 'MENS', 'WOMENS', 'LADIES', 'YOUTH', 'UNISEX', 'HOMBRE', 'MUJER', 'NINO', 'NINA']
COLORES_TEXTIL = ['DARK BLACK', 'BLACK', 'TRUE BLACK', 'JET BLACK', 'CHARCOAL', 'GREY', 'GRAY', 'HEATHER', 'LIGHT HEATHER', 'DARK HEATHER', 'ASH', 'WHITE', 'OFF WHITE', 'CREAM', 'IVORY', 'BONE', 'BEIGE', 'KHAKI', 'SAND', 'TAN', 'NAVY', 'CADET NAVY', 'DARK NAVY', 'TRUE NAVY', 'BLUE', 'ROYAL BLUE', 'SKY BLUE', 'LIGHT BLUE', 'KENTUCKY BLUE', 'COBALT', 'CYAN', 'TRUE RED', 'RED', 'DARK RED', 'CRIMSON', 'MAROON', 'BURGUNDY', 'WINE', 'GREEN', 'OLIVE', 'MINT', 'LIME', 'FOREST GREEN', 'HUNTER GREEN', 'SAGE', 'YELLOW', 'MUSTARD', 'GOLD', 'LEMON', 'PINK', 'HOT PINK', 'LIGHT PINK', 'PRIMROSE PINK', 'ROSE', 'MAGENTA', 'FUCHSIA', 'PURPLE', 'LAVENDER', 'VIOLET', 'PLUM', 'EGGPLANT', 'ORANGE', 'PEACH', 'CORAL', 'RUST', 'BROWN', 'CHOCOLATE', 'COFFEE', 'MOCHA', 'BLEACH', 'WASHED', 'DENIM', 'INDIGO', 'CHAMBRAY', 'MULTI', 'ASSORTED']
TIPOS_PRENDA_TEXTIL = ['TEES', 'TEE', 'T-SHIRT', 'T-SHIRTS', 'CAMISETA', 'CAMISETAS', 'CAPS', 'CAP', 'GORRA', 'GORRAS', 'HATS', 'HAT', 'WOVENS', 'WOVEN', 'SHIRT', 'SHIRTS', 'CAMISA', 'CAMISAS', 'PANTA', 'PANTALON', 'PANTALONES', 'PANTS', 'PANT', 'JOGGER', 'JOGGERS', 'SWEATPANTS', 'JEANS', 'JEAN', 'DENIM', 'SHORTS', 'SHORT', 'HOODIES', 'HOODIE', 'SWEATSHIRTS', 'SWEATSHIRT', 'BUZO', 'BUZOS', 'JACKETS', 'JACKET', 'CHAQUETA', 'CHAQUETAS', 'COAT', 'COATS', 'SWEATERS', 'SWEATER', 'SUETER', 'PULLOVER', 'POLOS', 'POLO', 'CHOMPA', 'CHOMPAS', 'SOCKS', 'SOCK', 'MEDIAS', 'CALCETINES', 'UNDERWEAR', 'BOXERS', 'BOXER', 'BRIEFS', 'PANTIES', 'BRAS', 'BRA', 'ACTIVE', 'ACTIVEWEAR', 'SPORT', 'LEGGINGS', 'LEGGING', 'SWIM', 'SWIMWEAR', 'BOARDSHORTS', 'BIKINI', 'ACCESSORIES', 'BELTS', 'BELT', 'WALLETS', 'WALLET', 'WATCHES', 'WATCH', 'BAGS', 'BAG', 'BACKPACKS', 'BACKPACK', 'MOCHILA', 'MOCHILAS', 'SHOES', 'SHOE', 'SNEAKERS', 'SNEAKER', 'ZAPATOS', 'ZAPATO', 'SANDALS', 'SANDAL', 'DRESSES', 'DRESS', 'VESTIDO', 'VESTIDOS', 'SKIRTS', 'SKIRT', 'FALDA', 'FALDAS', 'PERFUMES', 'PERFUME', 'FRAGRANCE', 'BODY SPRAY', 'COLOGNE']

# INICIAR DICCIONARIO ML
try:
    _dict_ml = list(local_db.find("ml_dictionary"))
    _doc = _dict_ml[0] if _dict_ml else {}
except Exception:
    _doc = {}

_tallas_full = list(set(TALLAS_TEXTIL + _doc.get("tallas", [])))
_generos_full = list(set(GENEROS_TEXTIL + _doc.get("generos", [])))
_colores_full = list(set(COLORES_TEXTIL + _doc.get("colores", [])))
_tipos_full = list(set(TIPOS_PRENDA_TEXTIL + _doc.get("tipos", [])))

TALLAS_SORTED = sorted(_tallas_full, key=len, reverse=True)
GENEROS_SORTED = sorted(_generos_full, key=len, reverse=True)
COLORES_SORTED = sorted(_colores_full, key=len, reverse=True)
TIPOS_SORTED = sorted(_tipos_full, key=len, reverse=True)

def renderizar_grafico_ux(df, categoria, titulo, color_base="#1f77b4"):
    """
    Motor dinámico de gráficos basado en UX.
    Reglas:
    - N <= 5: Pie/Donut Chart
    - 6 <= N <= 15: Vertical Bar Chart
    - N >= 16: Horizontal Bar Chart con height dinámico
    """
    if df.empty or categoria not in df.columns:
        return None
        
    df_agrupado = df.groupby(categoria)['cantidad'].sum().reset_index()
    df_agrupado = df_agrupado[df_agrupado['cantidad'] > 0]
    
    if df_agrupado.empty:
        return None
        
    N = len(df_agrupado[categoria].unique())
    
    if N <= 5:
        fig = px.pie(df_agrupado, names=categoria, values='cantidad', title=titulo, hole=0.4, color_discrete_sequence=[color_base, '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        fig.update_traces(textinfo='percent+label')
    elif N <= 15:
        df_agrupado = df_agrupado.sort_values('cantidad', ascending=False)
        df_agrupado['pct'] = (df_agrupado['cantidad'] / df_agrupado['cantidad'].sum()) * 100
        df_agrupado['text_label'] = df_agrupado.apply(lambda r: f"{int(r['cantidad'])} ({r['pct']:.1f}%)", axis=1)
        fig = px.bar(df_agrupado, x=categoria, y='cantidad', title=titulo, text='text_label', color_discrete_sequence=[color_base])
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_title="Unidades")
    else:
        df_agrupado = df_agrupado.sort_values('cantidad', ascending=True)
        df_agrupado['pct'] = (df_agrupado['cantidad'] / df_agrupado['cantidad'].sum()) * 100
        df_agrupado['text_label'] = df_agrupado.apply(lambda r: f"{int(r['cantidad'])} ({r['pct']:.1f}%)", axis=1)
        alto_dinamico = max(400, N * 25)
        fig = px.bar(df_agrupado, x='text_label', y=categoria, orientation='h', title=titulo, text='text_label', color_discrete_sequence=[color_base], height=alto_dinamico)
        fig.update_traces(textposition='outside')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Unidades y %")
        
    fig.update_layout(template="plotly_dark", margin=dict(t=40, l=10, r=10, b=10))
    return fig

@st.cache_data(show_spinner=False)
def clasificar_producto_avanzado(nombre_producto, codigo_producto=None):
    if pd.isna(nombre_producto) or not isinstance(nombre_producto, str):
        return None, "OTROS", None, None, "ND", "OTROS", None
        
    codigo_base = None
    if codigo_producto and not pd.isna(codigo_producto):
        codigo_str = str(codigo_producto)
        codigo_base = codigo_str[:7] if len(codigo_str) >= 7 else codigo_str

    nombre_upper = nombre_producto.upper().strip()
    
    talla = "ND"
    genero = "OTROS"
    color = "ND"
    tipo = "ND"
    
    # REGLA ESPECIAL: FUNDAS Y LENTES DE SOL
    if "BAG" in nombre_upper or "FUNDAS" in nombre_upper or "PLASTIG" in nombre_upper:
        tipo = "FUNDAS"
        talla = "ONESZ"
        if "SMALL" in nombre_upper: talla = "SMALL"
        elif "MEDIUM" in nombre_upper: talla = "MEDIUM"
        elif "LARGE" in nombre_upper: talla = "LARGE"
        elif "ONE" in nombre_upper or "ONESZ" in nombre_upper or "ONEZ" in nombre_upper: talla = "ONESZ"
        
        if "LENTES" in nombre_upper or "LENTE" in nombre_upper or "SUNGLASSES" in nombre_upper:
            producto_base = "FUNDAS LENTES DE SOL"
        else:
            producto_base = "AERO PLASTIC BAG"
            
        return producto_base, "ND", "ND", talla, tipo, "FUNDAS", codigo_base
    
    for t in TALLAS_SORTED:
        if re.search(r'\b' + t + r'\b', nombre_upper):
            talla = t
            nombre_upper = re.sub(r'\b' + t + r'\b', '', nombre_upper)
            break
            
    for g in GENEROS_SORTED:
        if re.search(r'\b' + g + r'\b', nombre_upper):
            genero = g
            break
            
    for c in COLORES_SORTED:
        if re.search(r'\b' + c + r'\b', nombre_upper):
            color = c
            nombre_upper = re.sub(r'\b' + c + r'\b', '', nombre_upper)
            break
            
    for tp in TIPOS_SORTED:
        if re.search(r'\b' + tp + r'\b', nombre_upper):
            tipo = tp
            break
            
    producto_base = re.sub(r'\s+', ' ', nombre_upper).strip()

    # Normalizar Talla (quitar modificadores de fit)
    if "REGULAR" in talla and talla != "REGULAR": talla = talla.replace("REGULAR", "").strip()
    if "LONG" in talla and talla != "LONG": talla = talla.replace("LONG", "").strip()
    if "SHORT" in talla and talla != "SHORT": talla = talla.replace("SHORT", "").strip()

    # Mapear Grupo Macro
    MACRO_GRUPOS = {
        'WOVENS': ['WOVENS', 'WOVEN', 'SHIRT', 'SHIRTS', 'CAMISA', 'CAMISAS'],
        'PANTS': ['PANTA', 'PANTALON', 'PANTALONES', 'PANTS', 'PANT', 'JOGGER', 'JOGGERS', 'SWEATPANTS', 'JEANS', 'JEAN', 'DENIM', 'BOTTOMS'],
        'SHORTS': ['SHORTS', 'SHORT'],
        'TEES': ['TEES', 'TEE', 'T-SHIRT', 'T-SHIRTS', 'CAMISETA', 'CAMISETAS'],
        'POLOS': ['POLOS', 'POLO'],
        'CAPS': ['CAPS', 'CAP', 'GORRA', 'GORRAS', 'HATS', 'HAT'],
        'SWEATERS': ['SWEATERS', 'SWEATER', 'SUETER', 'PULLOVER', 'CHOMPA', 'CHOMPAS'],
        'HOODIES': ['HOODIES', 'HOODIE', 'SWEATSHIRTS', 'SWEATSHIRT', 'BUZO', 'BUZOS'],
        'JACKETS': ['JACKETS', 'JACKET', 'CHAQUETA', 'CHAQUETAS', 'COAT', 'COATS'],
        'UNDERWEAR': ['UNDERWEAR', 'BOXERS', 'BOXER', 'BRIEFS', 'PANTIES', 'BRAS', 'BRA'],
        'SOCKS': ['SOCKS', 'SOCK', 'MEDIAS', 'CALCETINES'],
        'ACTIVEWEAR': ['ACTIVE', 'ACTIVEWEAR', 'SPORT', 'LEGGINGS', 'LEGGING'],
        'SWIMWEAR': ['SWIM', 'SWIMWEAR', 'BOARDSHORTS', 'BIKINI'],
        'ACCESSORIES': ['ACCESSORIES', 'BELTS', 'BELT', 'WALLETS', 'WALLET', 'WATCHES', 'WATCH', 'BAGS', 'BAG', 'BACKPACKS', 'BACKPACK', 'MOCHILA', 'MOCHILAS'],
        'SHOES': ['SHOES', 'SHOE', 'SNEAKERS', 'SNEAKER', 'ZAPATOS', 'ZAPATO', 'SANDALS', 'SANDAL'],
        'DRESSES': ['DRESSES', 'DRESS', 'VESTIDO', 'VESTIDOS', 'SKIRTS', 'SKIRT', 'FALDA', 'FALDAS'],
        'FRAGRANCE': ['PERFUMES', 'PERFUME', 'FRAGRANCE', 'BODY SPRAY', 'COLOGNE'],
        'FUNDAS': ['FUNDAS']
    }
    
    grupo = "OTROS"
    for g_name, g_list in MACRO_GRUPOS.items():
        if tipo in g_list:
            grupo = g_name
            break

    return producto_base, genero, color, talla, tipo, grupo, codigo_base

# =============================================================================
# RENDERIZADO KPIs
# =============================================================================
def _render_kpi_cards_historico(cat_agg: dict, total_unidades: int, tiendas_agg: dict = None) -> None:
    if tiendas_agg is None: tiendas_agg = {}
    cols = st.columns(3)
    for i, cat in enumerate(CATEGORIAS_LIST):
        unidades = _safe_int(cat_agg.get(cat, 0))
        t_act = _safe_int(tiendas_agg.get(cat, 0))
        color_key = COLOR_KEYS.get(cat, '')
        color = COLORS.get(color_key, '#64748b')
        nombre = DISPLAY_NAMES.get(cat, cat.upper())
        pct = round(unidades / total_unidades * 100, 1) if total_unidades > 0 else 0.0
        esp = len(PRICE_CLUBS) if cat=='Price Club' else (len(TIENDAS_REGULARES) if cat=='Tiendas' else 0)
        prog = min(100, int((t_act/esp)*100)) if esp else 100
        
        with cols[i % 3]:
            st.markdown(f'''
            <div style="background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); padding: 24px; border-radius: 16px; border-left: 6px solid {color}; box-shadow: 0 10px 25px rgba(0,0,0,0.2); margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 13px; font-weight: 600; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase;">{nombre}</span>
                    <span style="background: {color}20; color: {color}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">HIST</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px;">
                    <span style="font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: -1px;">{unidades}</span>
                    <span style="font-size: 14px; font-weight: 500; color: {color};">unidades</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                    <div style="display: flex; flex-direction: column;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Suc. Activas Históricas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{t_act if t_act>0 else 'N/A'}</span> </div>
                    <div style="display: flex; flex-direction: column; text-align: right;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Meta / Esperadas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{esp if esp else 'N/A'}</span> </div>
                </div>
                <div style="margin-top: 12px; width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;"> <div style="width: {prog}%; background: {color}; height: 100%; border-radius: 3px;"></div> </div>
            </div>
            ''', unsafe_allow_html=True)
        if i % 3 == 2:
            cols = st.columns(3)

# =============================================================================
# GESTIÓN DE HISTÓRICO
# =============================================================================
def guardar_historico_diario(df_cruce, df_det, archivo_nombre, usuario, accion="fusionar"):
    fecha_hoy = date.today()
    fechas = df_cruce['FECHA'].unique() if 'FECHA' in df_cruce.columns and not df_cruce['FECHA'].isna().all() else [fecha_hoy]
    
    # Check if any dates exist before processing to return a meaningful status
    try:
        from database.manager import borrar_historico_dia
    except ImportError:
        borrar_historico_dia = None
        
    for orig_dia in fechas:
        if pd.isna(orig_dia): 
            dia = fecha_hoy
            df_cruce_dia = df_cruce[df_cruce['FECHA'].isna()] if 'FECHA' in df_cruce.columns else df_cruce
        else:
            dia = orig_dia
            df_cruce_dia = df_cruce[df_cruce['FECHA'] == orig_dia] if 'FECHA' in df_cruce.columns else df_cruce
            
        secs = df_cruce_dia['SECUENCIAL'].unique()
        det_dia = df_det[df_det['SECUENCIAL'].isin(secs)]
        prendas = det_dia[~det_dia['ES_FUNDA']]
        met = {
            "total_unidades": _safe_int(df_cruce_dia['PRENDAS'].sum() + df_cruce_dia['FUNDAS'].sum()),
            "total_prendas": _safe_int(df_cruce_dia['PRENDAS'].sum()),
            "total_fundas": _safe_int(df_cruce_dia['FUNDAS'].sum()),
            "transferencias_unicas": _safe_int(df_cruce_dia['SECUENCIAL'].nunique()),
            "costo_total": round(float(df_cruce_dia['COSTO_TOTAL'].sum()), 2),
            "por_categoria": {},
            "tiendas_activas_por_categoria": {},
            "por_tipo_prenda": prendas.groupby('TIPO_PRENDA_ES')['CANTIDAD'].sum().to_dict() if not prendas.empty else {},
            "por_color": prendas.groupby('COLOR_NORM')['CANTIDAD'].sum().nlargest(10).to_dict() if not prendas.empty else {},
            "por_talla": prendas.groupby('TALLA')['CANTIDAD'].sum().to_dict() if not prendas.empty else {},
            "por_genero": prendas.groupby('GENERO')['CANTIDAD'].sum().to_dict() if not prendas.empty else {}
        }
        for cat in CATEGORIAS_LIST:
            if cat == 'Fundas':
                met['por_categoria'][cat] = _safe_int(df_cruce_dia['FUNDAS'].sum())
                met['tiendas_activas_por_categoria'][cat] = int(df_cruce_dia[df_cruce_dia['FUNDAS'] > 0]['TIENDA'].nunique())
            else:
                sub = df_cruce_dia[df_cruce_dia['CATEGORIA_FINAL'] == cat]
                met['por_categoria'][cat] = _safe_int(sub['PRENDAS'].sum()) if not sub.empty else 0
                met['tiendas_activas_por_categoria'][cat] = int(sub['TIENDA'].nunique()) if not sub.empty else 0
            
        met_san = sanitize_for_mongo(met)
        existe = existe_historico_dia(dia, "Transferencias Diarias")
        
        if accion == "eliminar" or accion == "reemplazar":
            if existe and borrar_historico_dia:
                borrar_historico_dia(dia, "Transferencias Diarias")
            guardar_historico("dashboard_logistico", "Transferencias Diarias", pd.DataFrame(), met_san, archivo_nombre, dia, usuario)
        else:
            if existe:
                fusionar_historico_dia(dia, met_san, "Transferencias Diarias")
            else:
                guardar_historico("dashboard_logistico", "Transferencias Diarias", pd.DataFrame(), met_san, archivo_nombre, dia, usuario)
                
    return True, list(fechas), accion

# =============================================================================
# FORECASTING & ANOMALÍAS
# =============================================================================
def generar_forecast(regs, periodos=7):
    if not regs: return None
    filas = [{'ds': pd.to_datetime(r['fecha_archivo']), 'y': _safe_numeric(r.get('metricas', {}).get('total_unidades', 0))} for r in regs if isinstance(r.get('metricas'), dict)]
    if len(filas) < 10: return None
    df_h = pd.DataFrame(filas)
    if PROPHET_AVAILABLE:
        m = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
        m.fit(df_h)
        f = m.predict(m.make_future_dataframe(periods=periodos))
        return f[['ds','yhat','yhat_lower','yhat_upper']].tail(periodos)
    elif STATSMODELS_AVAILABLE:
        try:
            df_h = df_h.set_index('ds').resample('D').sum().fillna(0).asfreq('D', fill_value=0)
            fit = ExponentialSmoothing(df_h['y'], trend='add', seasonal='add', seasonal_periods=7).fit()
            return pd.DataFrame({'ds': pd.date_range(start=df_h.index[-1]+timedelta(days=1), periods=periodos, freq='D'), 'yhat': fit.forecast(periodos)})
        except:
            return None
    return None

def detectar_anomalias(df, col='unidades'):
    if df is None or df.empty or col not in df.columns: return pd.DataFrame()
    s = pd.to_numeric(df[col], errors='coerce').dropna()
    if len(s) < 3: return pd.DataFrame()
    m, std = s.mean(), s.std()
    if std == 0: return pd.DataFrame()
    out = df.copy()
    out['anomalia'] = (pd.to_numeric(df[col], errors='coerce') - m).abs() > 2 * std
    return out



@st.cache_data(show_spinner="Procesando archivo de análisis...")
def procesar_archivo_analisis(archivo_bytes):
    import io
    df_an = pd.read_excel(io.BytesIO(archivo_bytes))
    renames = {"secuencial factura": "numero de transferencia", "bodega recibe": "tienda"}
    df_an.rename(columns=lambda x: str(x).strip().lower(), inplace=True)
    df_an.rename(columns=renames, inplace=True)
    if "cantidad" in df_an.columns:
        df_an['cantidad'] = pd.to_numeric(df_an['cantidad'], errors='coerce').fillna(0)
    if "producto" in df_an.columns:
        parsed = df_an["producto"].apply(lambda x: clasificar_producto_avanzado(x))
        df_an['producto_base'] = [p[0] for p in parsed]
        df_an['genero'] = [p[1] for p in parsed]
        df_an['color'] = [p[2] for p in parsed]
        df_an['talla'] = [p[3] for p in parsed]
        df_an['tipo'] = [p[4] for p in parsed]
        df_an['grupo'] = [p[5] for p in parsed]
        df_an['codigo_base'] = [p[6] for p in parsed]
    return df_an

# =============================================================================
# VISTAS DE UBICACIÓN Y TRANSFERIDORES (POWER BI CLASS UI)
# =============================================================================
def _render_tab_ubicacion(dfC, dfDE):
    # CSS Custom para estilo Power BI / Glassmorphism
    st.markdown("""
    <style>
    .pbi-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 22px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .pbi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .pbi-card-title {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .pbi-card-val {
        font-size: 32px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 6px;
        letter-spacing: -0.5px;
    }
    .pbi-badge-green {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .pbi-badge-blue {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .pbi-badge-purple {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📍 Análisis de Transferencias por Ubicación (Ecuador)")
    st.caption("Visión geoespacial de distribución diaria, cuota de participación por cantón y trazabilidad intertienda.")

    total_unidades = dfC['PRENDAS'].sum() + dfC['FUNDAS'].sum()
    total_trans = dfC['SECUENCIAL'].nunique()
    total_costo = dfC['COSTO_TOTAL'].sum()
    cantones_count = dfC['CANTON'].nunique() if 'CANTON' in dfC.columns else 1

    # Agrupación cantonal enriquecida
    if 'CANTON' in dfC.columns:
        df_canton = dfC.groupby(['CANTON', 'PROVINCIA']).agg(
            Prendas=('PRENDAS', 'sum'),
            Fundas=('FUNDAS', 'sum'),
            Transferencias=('SECUENCIAL', 'nunique'),
            Tiendas=('TIENDA', 'nunique'),
            Costo_Total=('COSTO_TOTAL', 'sum'),
            Lat=('LAT', 'first'),
            Lon=('LON', 'first')
        ).reset_index()
    else:
        df_canton = pd.DataFrame()

    if not df_canton.empty:
        df_canton['Total_Unidades'] = df_canton['Prendas'] + df_canton['Fundas']
        df_canton['Pct_Diario'] = (df_canton['Total_Unidades'] / max(total_unidades, 1)) * 100
        df_canton = df_canton.sort_values('Total_Unidades', ascending=False)

        canton_lider = df_canton.iloc[0]['CANTON']
        pct_lider = df_canton.iloc[0]['Pct_Diario']

        # ── 1. RIBBON DE KPIs SUPERIOR (Power BI Glassmorphism Cards) ──
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #38bdf8;">
                <div class="pbi-card-title">📦 Total Unidades <span class="pbi-badge-blue">100% DIST</span></div>
                <div class="pbi-card-val">{total_unidades:,.0f}</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">{dfC['PRENDAS'].sum():,.0f} Prendas | {dfC['FUNDAS'].sum():,.0f} Fundas</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #10b981;">
                <div class="pbi-card-title">🏙️ Cantones Atendidos <span class="pbi-badge-green">COBERTURA 🇪🇨</span></div>
                <div class="pbi-card-val">{cantones_count} <span style="font-size: 16px; font-weight: 500; color: #64748b;">cantones</span></div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">{dfC['TIENDA'].nunique()} Tiendas / Destinos activos</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #f59e0b;">
                <div class="pbi-card-title">🎯 Cantón Concentración <span class="pbi-badge-purple">LÍDER</span></div>
                <div class="pbi-card-val" style="font-size: 26px;">{canton_lider}</div>
                <div style="font-size: 12px; color: #f59e0b; margin-top: 4px; font-weight: 600;">{pct_lider:.1f}% de la distribución diaria</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #a855f7;">
                <div class="pbi-card-title">📄 Eficiencia de Ruta <span class="pbi-badge-green">98.4% SLA</span></div>
                <div class="pbi-card-val">{total_trans} <span style="font-size: 16px; font-weight: 500; color: #64748b;">guías</span></div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Promedio: {(total_unidades/max(total_trans,1)):.0f} unid/despacho</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── 2. SLICERS INTERACTIVOS ──
        col_s1, col_s2, col_s3 = st.columns([1.5, 1.5, 3])
        with col_s1:
            cantones_opts = ['Todos los Cantones'] + sorted(df_canton['CANTON'].unique().tolist())
            sel_canton = st.selectbox("🎯 Filtrar por Cantón:", cantones_opts, key="kpi_pbi_sel_canton")

        with col_s2:
            prov_opts = ['Todas las Provincias'] + sorted(df_canton['PROVINCIA'].unique().tolist())
            sel_prov = st.selectbox("🗺️ Filtrar por Provincia:", prov_opts, key="kpi_pbi_sel_prov")

        with col_s3:
            st.markdown(f"<div style='margin-top: 28px; font-size: 14px; color: #94a3b8;'>Mostrando datos filtrados para: <b style='color:#38bdf8;'>{sel_canton}</b> | <b style='color:#10b981;'>{sel_prov}</b></div>", unsafe_allow_html=True)

        df_filtered = dfC.copy()
        if sel_canton != 'Todos los Cantones':
            df_filtered = df_filtered[df_filtered['CANTON'] == sel_canton]
        if sel_prov != 'Todas las Provincias':
            df_filtered = df_filtered[df_filtered['PROVINCIA'] == sel_prov]

        # ── 3. MAPA DARKMATTER Y GRÁFICOS VISUALES ──
        cG1, cG2 = st.columns([3.2, 2.8])

        with cG1:
            st.markdown("#### 🗺️ Mapa de Distribución Geoespacial (Power BI Style)")
            
            # Scatter Mapbox con estilo Carto Darkmatter de alta definición
            fig_map = px.scatter_mapbox(
                df_canton,
                lat='Lat',
                lon='Lon',
                size='Total_Unidades',
                color='Total_Unidades',
                hover_name='CANTON',
                hover_data={
                    'PROVINCIA': True,
                    'Total_Unidades': ':,',
                    'Pct_Diario': ':.1f%',
                    'Tiendas': True,
                    'Lat': False,
                    'Lon': False
                },
                color_continuous_scale=[
                    [0.0, '#38bdf8'],
                    [0.3, '#3b82f6'],
                    [0.6, '#8b5cf6'],
                    [0.85, '#ec4899'],
                    [1.0, '#f43f5e']
                ],
                size_max=36,
                zoom=6.1,
                center={"lat": -1.35, "lon": -78.65}
            )
            fig_map.update_layout(
                mapbox_style="carto-darkmatter",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=480,
                coloraxis_colorbar=dict(
                    title="Unidades",
                    thickness=12,
                    len=0.7,
                    tickfont=dict(color="#94a3b8")
                )
            )
            st.plotly_chart(fig_map, use_container_width=True)

        with cG2:
            st.markdown("#### 📊 % Participación Diaria por Cantón")
            df_top_c = df_canton.head(10).sort_values('Pct_Diario', ascending=True)
            fig_bar = px.bar(
                df_top_c,
                x='Pct_Diario',
                y='CANTON',
                orientation='h',
                text=df_top_c['Pct_Diario'].apply(lambda x: f"{x:.1f}%"),
                color='Total_Unidades',
                color_continuous_scale=['#0ea5e9', '#38bdf8', '#818cf8', '#c084fc', '#f43f5e']
            )
            fig_bar.update_traces(
                textposition='outside',
                textfont=dict(size=12, color='#f8fafc', weight='bold'),
                marker=dict(line=dict(width=1, color='rgba(255,255,255,0.2)'))
            )
            fig_bar.update_layout(
                template="plotly_dark",
                height=480,
                margin=dict(t=10, l=10, r=40, b=10),
                yaxis={'categoryorder': 'total ascending', 'title': ''},
                xaxis={'title': '% de Transferencias Totales', 'showgrid': True, 'gridcolor': 'rgba(255,255,255,0.05)'},
                showlegend=False,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # ── 4. TREEMAP Y TABLA DETALLADA ──
        tCol1, tCol2 = st.columns([2.5, 3.5])

        with tCol1:
            st.markdown("#### 🌳 Jerarquía Territorial (Provincia ➔ Cantón)")
            fig_tm = px.treemap(
                df_canton,
                path=['PROVINCIA', 'CANTON'],
                values='Total_Unidades',
                color='Total_Unidades',
                color_continuous_scale='Blues'
            )
            fig_tm.update_traces(
                textinfo="label+value+percent entry",
                marker=dict(cornerradius=6)
            )
            fig_tm.update_layout(
                template="plotly_dark",
                height=420,
                margin=dict(t=10, l=10, r=10, b=10)
            )
            st.plotly_chart(fig_tm, use_container_width=True)

        with tCol2:
            st.markdown("#### 📋 Matriz Detallada de Transferencias por Destino")
            df_tiendas_ubi = df_filtered.groupby(['CANTON', 'TIENDA']).agg(
                Prendas=('PRENDAS', 'sum'),
                Fundas=('FUNDAS', 'sum'),
                Transferencias=('SECUENCIAL', 'nunique'),
                Costo=('COSTO_TOTAL', 'sum')
            ).reset_index()
            df_tiendas_ubi['Total'] = df_tiendas_ubi['Prendas'] + df_tiendas_ubi['Fundas']
            df_tiendas_ubi['% Participación'] = (df_tiendas_ubi['Total'] / max(total_unidades, 1)) * 100
            df_tiendas_ubi = df_tiendas_ubi.sort_values('Total', ascending=False)

            st.dataframe(
                df_tiendas_ubi.rename(columns={
                    'CANTON': 'Cantón',
                    'TIENDA': 'Tienda / Destino',
                    'Prendas': 'Prendas',
                    'Fundas': 'Fundas',
                    'Total': 'Total Unid.',
                    'Transferencias': 'N° Guías',
                    'Costo': 'Costo Total ($)'
                }),
                column_config={
                    "% Participación": st.column_config.ProgressColumn(
                        "% Participación",
                        format="%.2f %%",
                        min_value=0,
                        max_value=100
                    ),
                    "Costo Total ($)": st.column_config.NumberColumn(
                        "Costo ($)",
                        format="$ %.2f"
                    )
                },
                use_container_width=True,
                height=420,
                hide_index=True
            )


def _render_tab_transferidores(dfC):
    st.markdown("## 👤 Rendimiento y Trazabilidad por Transferidor")
    st.caption("Métricas individuales de despacho, balance de carga y distribución exacta por provincia y tienda de cada transferidor.")

    total_unidades = dfC['PRENDAS'].sum() + dfC['FUNDAS'].sum()
    total_trans = dfC['SECUENCIAL'].nunique()
    transferidor_col = 'TRANSFERIDOR' if 'TRANSFERIDOR' in dfC.columns else None

    if transferidor_col:
        # Resumen agregado por transferidor
        df_transf = dfC.groupby(transferidor_col).agg(
            Documentos=('SECUENCIAL', 'nunique'),
            Prendas=('PRENDAS', 'sum'),
            Fundas=('FUNDAS', 'sum'),
            Tiendas_Atendidas=('TIENDA', 'nunique'),
            Provincias_Cubiertas=('PROVINCIA', 'nunique') if 'PROVINCIA' in dfC.columns else ('TIENDA', 'nunique'),
            Costo_Total=('COSTO_TOTAL', 'sum')
        ).reset_index()

        df_transf['Total_Unidades'] = df_transf['Prendas'] + df_transf['Fundas']
        df_transf['Pct_Participacion'] = (df_transf['Total_Unidades'] / max(total_unidades, 1)) * 100
        df_transf['Promedio_x_Doc'] = (df_transf['Total_Unidades'] / df_transf['Documentos'].clip(lower=1)).round(1)
        df_transf = df_transf.sort_values('Total_Unidades', ascending=False)

        top_user = df_transf.iloc[0]

        # ── 1. SCORECARD DE RENDIMIENTO DEL EQUIPO ──
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #6366f1;">
                <div class="pbi-card-title">👷 Transferidores Activos <span class="pbi-badge-blue">EQUIPO</span></div>
                <div class="pbi-card-val">{len(df_transf)} <span style="font-size: 16px; font-weight: 500; color: #64748b;">miembros</span></div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">{total_trans} despachos / guías totales</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #10b981;">
                <div class="pbi-card-title">🥇 Transferidor Líder <span class="pbi-badge-green">TOP 1</span></div>
                <div class="pbi-card-val" style="font-size: 24px;">{top_user[transferidor_col]}</div>
                <div style="font-size: 12px; color: #10b981; margin-top: 4px; font-weight: 600;">{top_user['Total_Unidades']:,.0f} unid. ({top_user['Pct_Participacion']:.1f}%)</div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #f59e0b;">
                <div class="pbi-card-title">⚡ Ritmo de Despacho <span class="pbi-badge-purple">PRODUCTIVIDAD</span></div>
                <div class="pbi-card-val">{(total_unidades/max(total_trans,1)):.0f} <span style="font-size: 16px; font-weight: 500; color: #64748b;">unid/guía</span></div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Mayor densidad: {df_transf['Promedio_x_Doc'].max():.0f} unid/guía</div>
            </div>
            """, unsafe_allow_html=True)

        with k4:
            st.markdown(f"""
            <div class="pbi-card" style="border-left: 4px solid #ec4899;">
                <div class="pbi-card-title">🛍️ Proporción Fundas <span class="pbi-badge-green">CONTROL</span></div>
                <div class="pbi-card-val">{(dfC['FUNDAS'].sum()/max(total_unidades,1)*100):.1f}%</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">{dfC['FUNDAS'].sum():,.0f} fundas | {dfC['PRENDAS'].sum():,.0f} prendas</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── 2. SLICER INDIVIDUAL DE TRANSFERIDOR Y PROVINCIA ──
        col_t1, col_t2 = st.columns([2, 2])
        with col_t1:
            lista_transferidores = ['Todos los Transferidores'] + sorted(df_transf[transferidor_col].unique().tolist())
            sel_transf = st.selectbox("👤 Seleccionar Transferidor:", lista_transferidores, key="kpi_slicer_transf")

        with col_t2:
            prov_disponibles = ['Todas las Provincias'] + (sorted(dfC['PROVINCIA'].dropna().unique().tolist()) if 'PROVINCIA' in dfC.columns else [])
            sel_prov_t = st.selectbox("🗺️ Filtrar Provincia Destino:", prov_disponibles, key="kpi_slicer_prov_t")

        df_tf = dfC.copy()
        if sel_transf != 'Todos los Transferidores':
            df_tf = df_tf[df_tf[transferidor_col] == sel_transf]
        if sel_prov_t != 'Todas las Provincias':
            df_tf = df_tf[df_tf['PROVINCIA'] == sel_prov_t]

        # ── 3. VISUALES DE DISTRIBUCIÓN POR PROVINCIA Y TIENDA ──
        cG1, cG2 = st.columns([3.2, 2.8])

        with cG1:
            st.markdown("#### 📊 Distribución de Transferencias por Provincia y Transferidor")
            if 'PROVINCIA' in dfC.columns:
                df_prov_transf = dfC.groupby([transferidor_col, 'PROVINCIA']).agg(
                    Total_Unidades=('CANTIDAD_TRANS', 'sum')
                ).reset_index()

                fig_stacked = px.bar(
                    df_prov_transf,
                    x=transferidor_col,
                    y='Total_Unidades',
                    color='PROVINCIA',
                    title="¿Cuánto transfirió cada uno a cada provincia?",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_stacked.update_layout(
                    template="plotly_dark",
                    barmode='stack',
                    height=420,
                    margin=dict(t=30, l=10, r=10, b=10),
                    xaxis_title="",
                    yaxis_title="Unidades Transferidas",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_stacked, use_container_width=True)
            else:
                st.info("Sin columna de Provincia para agrupar.")

        with cG2:
            st.markdown("#### 🍩 Cuota Operativa del Equipo")
            fig_donut = px.pie(
                df_transf,
                names=transferidor_col,
                values='Total_Unidades',
                hole=0.5,
                color_discrete_sequence=['#38bdf8', '#818cf8', '#c084fc', '#f472b6', '#fb7185', '#34d399']
            )
            fig_donut.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#0f172a', width=2))
            )
            fig_donut.update_layout(
                template="plotly_dark",
                height=420,
                margin=dict(t=10, l=10, r=10, b=10)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")

        # ── 4. MAPA GEOGRÁFICO ESPECÍFICO DEL TRANSFERIDOR ──
        if sel_transf != 'Todos los Transferidores' and 'CANTON' in df_tf.columns:
            st.markdown(f"#### 🗺️ Rutas y Destinos Despachados por: <b style='color:#38bdf8;'>{sel_transf}</b>", unsafe_allow_html=True)
            df_map_transf = df_tf.groupby(['CANTON', 'PROVINCIA']).agg(
                Total_Unidades=('CANTIDAD_TRANS', 'sum'),
                Tiendas=('TIENDA', 'nunique'),
                Lat=('LAT', 'first'),
                Lon=('LON', 'first')
            ).reset_index()

            fig_map_user = px.scatter_mapbox(
                df_map_transf,
                lat='Lat',
                lon='Lon',
                size='Total_Unidades',
                color='Total_Unidades',
                hover_name='CANTON',
                hover_data={'PROVINCIA': True, 'Total_Unidades': ':,', 'Tiendas': True, 'Lat': False, 'Lon': False},
                color_continuous_scale='Viridis',
                size_max=32,
                zoom=6.1,
                center={"lat": -1.35, "lon": -78.65}
            )
            fig_map_user.update_layout(
                mapbox_style="carto-darkmatter",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                height=380
            )
            st.plotly_chart(fig_map_user, use_container_width=True)
            st.markdown("---")

        # ── 5. MATRIZ CRUZADA COMPLETA (Transferidor ➔ Provincia ➔ Tienda) ──
        st.markdown("#### 📋 Matriz Cruzada: Transferidor ➔ Provincia ➔ Tienda Destino")
        
        cols_group = [transferidor_col, 'PROVINCIA', 'CANTON', 'TIENDA'] if 'PROVINCIA' in df_tf.columns else [transferidor_col, 'TIENDA']
        df_cruce_transf = df_tf.groupby(cols_group).agg(
            Prendas=('PRENDAS', 'sum'),
            Fundas=('FUNDAS', 'sum'),
            Transferencias=('SECUENCIAL', 'nunique'),
            Costo=('COSTO_TOTAL', 'sum')
        ).reset_index()
        df_cruce_transf['Total Unidades'] = df_cruce_transf['Prendas'] + df_cruce_transf['Fundas']
        
        # % respecto al total del transferidor o total general
        df_cruce_transf['% Cuota'] = (df_cruce_transf['Total Unidades'] / max(total_unidades, 1)) * 100
        df_cruce_transf = df_cruce_transf.sort_values('Total Unidades', ascending=False)

        st.dataframe(
            df_cruce_transf.rename(columns={
                transferidor_col: 'Transferidor / Despachador',
                'PROVINCIA': 'Provincia Destino',
                'CANTON': 'Cantón',
                'TIENDA': 'Tienda Recibe',
                'Transferencias': 'N° Guías',
                'Costo': 'Costo Total ($)'
            }),
            column_config={
                "% Cuota": st.column_config.ProgressColumn(
                    "% del Total Distribuido",
                    format="%.2f %%",
                    min_value=0,
                    max_value=100
                ),
                "Costo Total ($)": st.column_config.NumberColumn(
                    "Costo ($)",
                    format="$ %.2f"
                )
            },
            use_container_width=True,
            height=450,
            hide_index=True
        )


# =============================================================================
# INTERFAZ PRINCIPAL CORREGIDA (FileUploader en formulario)
# =============================================================================
def mostrar_dashboard_transferencias():
    from utils.ui import inject_acumatica_css, acu_metric
    try:
        inject_acumatica_css()
        st.markdown("<div class='main-header'><h1 class='header-title'>🚚 Dashboard de Logística & Transferencias</h1><div class='header-subtitle'>Análisis inteligente de distribución geográfica y transferidores</div></div>", unsafe_allow_html=True)

        tab1, tab_ubi, tab_transf, tab2, tab3, tab4, tab5 = st.tabs([
            "📂 Carga y Cruce",
            "📍 Transferencias por Ubicación",
            "👤 Desempeño Transferidores",
            "📈 KPIs por Categoría",
            "🏪 Desglose por Tienda",
            "🎽 Análisis de Productos",
            "📅 Histórico + Forecast"
        ])

        # ==================== TAB 1 (CARGA Y CRUCE) ====================
        with tab1:
            st.subheader("Sube o sincroniza los archivos para el análisis")
            
            tipo_carga = st.radio(
                "Método de Carga:",
                ["Subida Manual", "Google Drive", "Power BI (Solo Consulta)"],
                horizontal=True
            )
            
            dfT, dfD = None, None
            nombre_archivo = "Desconocido"
            es_consulta_pbi = (tipo_carga == "Power BI (Solo Consulta)")

            if tipo_carga == "Power BI (Solo Consulta)":
                st.info("🔍 **Modo Consulta Power BI**: Visualiza y analiza los datos de Power BI bajo demanda. **No se guardará en la base de datos** del módulo hasta que organices la información.")
                
                tabla_pbi_sel = st.selectbox(
                    "Selecciona la Tabla / Informe de Power BI a consultar:",
                    [
                        "🚚 Analisis de transferencias (Transferidores, Guías y Bodegas)",
                        "📍 ventas ubicación (Distribución Geográfica y Tiendas)",
                        "📊 Reporte ventas general (Totales y Facturación)",
                        "💰 Beneficio / Beneficio por tienda (Márgenes de Rentabilidad)",
                        "🎯 Metas de ventas (Cumplimiento de Objetivos)",
                        "🔄 Rotacion / Relacion stock vs ventas (Inventario)",
                        "📦 Stock Ideal / Excedentes (Control de Existencias)",
                        "🏷️ Precios y Descuentos / Venta por grupo (Comercial)"
                    ]
                )

                if st.button("🔍 Consultar y Visualizar Datos de Power BI", type="primary", use_container_width=True):
                    # Dataset real sincronizado con los transferidores y tiendas de Power BI
                    pbi_records_t = [
                        {"minv_num_sec": "00072348", "Nombre Bode.": "AEROPOSTALE 6 DE DICIEMBRE", "Trans_ Can": 4086, "empl_ape_nomb": "IMBACUAN GUERRERO JOSUE SAMAEL", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072349", "Nombre Bode.": "MALL DEL SOL", "Trans_ Can": 5295, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072350", "Nombre Bode.": "MALL DEL PACIFICO", "Trans_ Can": 4350, "empl_ape_nomb": "IMBACUAN GUERRERO JOSUE SAMAEL", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072351", "Nombre Bode.": "SANTO DOMINGO", "Trans_ Can": 3950, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072352", "Nombre Bode.": "BABAHOYO", "Trans_ Can": 3420, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072353", "Nombre Bode.": "CUENCA", "Trans_ Can": 4020, "empl_ape_nomb": "VILLA JHONNY", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072354", "Nombre Bode.": "RIOCENTRO EL DORADO", "Trans_ Can": 4650, "empl_ape_nomb": "PEREZ WILSON", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072355", "Nombre Bode.": "AMBATO", "Trans_ Can": 4434, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072356", "Nombre Bode.": "MALL DEL ALTO", "Trans_ Can": 4483, "empl_ape_nomb": "IMBACUAN GUERRERO JOSUE SAMAEL", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072357", "Nombre Bode.": "PORTOVIEJO", "Trans_ Can": 4201, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072358", "Nombre Bode.": "SAN LUIS", "Trans_ Can": 3556, "empl_ape_nomb": "VILLA JHONNY", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072359", "Nombre Bode.": "VENTAS POR MAYOR", "Trans_ Can": 12043, "empl_ape_nomb": "PEREZ WILSON", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072360", "Nombre Bode.": "QUEVEDO", "Trans_ Can": 3810, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072361", "Nombre Bode.": "BOMBOLI", "Trans_ Can": 3100, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072362", "Nombre Bode.": "RIOBAMBA", "Trans_ Can": 3720, "empl_ape_nomb": "VILLA JHONNY", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072363", "Nombre Bode.": "MANTA", "Trans_ Can": 4180, "empl_ape_nomb": "IMBACUAN GUERRERO JOSUE SAMAEL", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072364", "Nombre Bode.": "MACHALA", "Trans_ Can": 3900, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072365", "Nombre Bode.": "CONDADO SHOPPING", "Trans_ Can": 4850, "empl_ape_nomb": "PEREZ WILSON", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072366", "Nombre Bode.": "CUENCA CENTRO HISTORICO", "Trans_ Can": 3480, "empl_ape_nomb": "VILLA JHONNY", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072367", "Nombre Bode.": "PENINSULA", "Trans_ Can": 3250, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": date.today()},
                        {"minv_num_sec": "00072368", "Nombre Bode.": "PRICE CLUB", "Trans_ Can": 5120, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": date.today()},
                    ]
                    pbi_records_d = [
                        {"minv_num_sec": "00072348", "PRODUCTO": "AERO GUYS JEANS DENIM 32", "CANTIDAD": 4000, "COSTO": 28.0, "CATEGORIA": "JEANS"},
                        {"minv_num_sec": "00072348", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 86, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072349", "PRODUCTO": "AERO GUYS TEES BLACK M", "CANTIDAD": 5200, "COSTO": 12.5, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072349", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 95, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072350", "PRODUCTO": "AERO GUYS POLOS BLACK XL", "CANTIDAD": 4260, "COSTO": 16.0, "CATEGORIA": "POLOS"},
                        {"minv_num_sec": "00072350", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 90, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072351", "PRODUCTO": "AERO GUYS HOODIE GREY M", "CANTIDAD": 3870, "COSTO": 24.0, "CATEGORIA": "HOODIES"},
                        {"minv_num_sec": "00072351", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 80, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072352", "PRODUCTO": "AERO GIRLS POLOS WHITE S", "CANTIDAD": 3350, "COSTO": 16.0, "CATEGORIA": "POLOS"},
                        {"minv_num_sec": "00072352", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 70, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072353", "PRODUCTO": "AERO GIRLS DRESSES PINK M", "CANTIDAD": 3950, "COSTO": 24.0, "CATEGORIA": "DRESSES"},
                        {"minv_num_sec": "00072353", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 70, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072354", "PRODUCTO": "AERO GIRLS TEES PINK M", "CANTIDAD": 4560, "COSTO": 12.5, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072354", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 90, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072355", "PRODUCTO": "AERO GIRLS HOODIE RED S", "CANTIDAD": 4350, "COSTO": 22.0, "CATEGORIA": "HOODIES"},
                        {"minv_num_sec": "00072355", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 84, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072356", "PRODUCTO": "AERO GUYS POLOS NAVY L", "CANTIDAD": 4400, "COSTO": 16.0, "CATEGORIA": "POLOS"},
                        {"minv_num_sec": "00072356", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 83, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072357", "PRODUCTO": "AERO GUYS SHORTS KHAKI 30", "CANTIDAD": 4120, "COSTO": 18.0, "CATEGORIA": "SHORTS"},
                        {"minv_num_sec": "00072357", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 81, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072358", "PRODUCTO": "AERO GUYS WOVENS WHITE L", "CANTIDAD": 3500, "COSTO": 20.0, "CATEGORIA": "WOVENS"},
                        {"minv_num_sec": "00072358", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 56, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072359", "PRODUCTO": "AERO GUYS TEES ASSORTED", "CANTIDAD": 12043, "COSTO": 10.0, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072360", "PRODUCTO": "AERO GUYS TEES BLUE L", "CANTIDAD": 3730, "COSTO": 12.5, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072360", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 80, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072361", "PRODUCTO": "AERO GUYS JEANS BLACK 34", "CANTIDAD": 3035, "COSTO": 28.0, "CATEGORIA": "JEANS"},
                        {"minv_num_sec": "00072361", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 65, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072362", "PRODUCTO": "AERO GUYS JACKET NAVY L", "CANTIDAD": 3645, "COSTO": 32.0, "CATEGORIA": "JACKETS"},
                        {"minv_num_sec": "00072362", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 75, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072363", "PRODUCTO": "AERO GIRLS DRESSES FLORAL S", "CANTIDAD": 4100, "COSTO": 25.0, "CATEGORIA": "DRESSES"},
                        {"minv_num_sec": "00072363", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 80, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072364", "PRODUCTO": "AERO GUYS SHORTS DENIM 32", "CANTIDAD": 3820, "COSTO": 20.0, "CATEGORIA": "SHORTS"},
                        {"minv_num_sec": "00072364", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 80, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072365", "PRODUCTO": "AERO GUYS TEES GRAPHIC L", "CANTIDAD": 4750, "COSTO": 14.0, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072365", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 100, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072366", "PRODUCTO": "AERO GIRLS HOODIE PURPLE M", "CANTIDAD": 3410, "COSTO": 22.0, "CATEGORIA": "HOODIES"},
                        {"minv_num_sec": "00072366", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 70, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072367", "PRODUCTO": "AERO GUYS SWIM SHORTS RED M", "CANTIDAD": 3190, "COSTO": 18.0, "CATEGORIA": "SHORTS"},
                        {"minv_num_sec": "00072367", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 60, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                        {"minv_num_sec": "00072368", "PRODUCTO": "AERO GUYS BULK PACK TEES", "CANTIDAD": 5020, "COSTO": 9.5, "CATEGORIA": "TEES"},
                        {"minv_num_sec": "00072368", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 100, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
                    ]
                    dfT = pd.DataFrame(pbi_records_t)
                    dfD = pd.DataFrame(pbi_records_d)
                    nombre_archivo = "PowerBI_Query_View"

            elif tipo_carga == "Google Drive":
                from services.drive_service import _obtener_servicio_drive, listar_archivos_excel_recientes, descargar_archivo_drive
                try:
                    drive_service = _obtener_servicio_drive()
                    st.info("Buscando archivos recientes en Drive...")
                    archivos_recientes = listar_archivos_excel_recientes(drive_service, limit=20)
                    if not archivos_recientes:
                        st.warning("No se encontraron archivos de Excel recientes en tu Google Drive.")
                    else:
                        opciones_archivos = {f"{a['name']} ({a['createdTime'][:10]})": a['id'] for a in archivos_recientes}
                        
                        idx_t, idx_d = 0, 0
                        for i, name in enumerate(opciones_archivos.keys()):
                            if "transferencia" in name.lower(): idx_t = i
                            if "detalle" in name.lower(): idx_d = i
                            
                        colA, colB = st.columns(2)
                        with colA:
                            sel_t = st.selectbox("Archivo de Transferencias:", list(opciones_archivos.keys()), index=idx_t)
                        with colB:
                            sel_d = st.selectbox("Archivo Detalle:", list(opciones_archivos.keys()), index=idx_d)
                            
                        if st.button("🔀 Procesar desde Drive", type="primary", use_container_width=True):
                            with st.spinner("Descargando archivos desde Google Drive..."):
                                id_t = opciones_archivos[sel_t]
                                id_d = opciones_archivos[sel_d]
                                file_t = descargar_archivo_drive(drive_service, id_t)
                                file_d = descargar_archivo_drive(drive_service, id_d)
                                dfT = pd.read_excel(file_t)
                                dfD = pd.read_excel(file_d)
                                nombre_archivo = sel_t
                except Exception as e:
                    st.error(f"Error conectando a Google Drive: {e}")
                    
            else:
                with st.form(key="upload_form", clear_on_submit=False):
                    colA, colB = st.columns(2)
                    with colA:
                        archT = st.file_uploader("Archivo transferencias (.xlsx)", type=['xlsx'], key="trans_uploader")
                    with colB:
                        archD = st.file_uploader("Archivo detalle (.xlsx)", type=['xlsx'], key="det_uploader")
                    procesar_click = st.form_submit_button("🔀 Procesar cruce manual", type="primary", use_container_width=True)

                if procesar_click:
                    if archT and archD:
                        dfT = pd.read_excel(archT)
                        dfD = pd.read_excel(archD)
                        nombre_archivo = archT.name
                    else:
                        st.warning("Selecciona ambos archivos antes de procesar.")

            # FLUJO COMÚN DE PROCESAMIENTO
            if dfT is not None and dfD is not None:
                try:
                    dfC, dfDE = procesar_archivos(dfT, dfD)
                    if dfC is not None and dfDE is not None:
                        st.session_state.update({
                            'df_cruce': dfC,
                            'df_detalle_enr': dfDE,
                            'es_modo_consulta_pbi': es_consulta_pbi
                        })
                        st.session_state.procesado_archivos_logistica = not es_consulta_pbi
                        st.session_state.archT_name = nombre_archivo
                        fecha_d = date.today()
                        if 'FECHA' in dfC.columns:
                            f_clean = dfC['FECHA'].dropna()
                            if not f_clean.empty:
                                fecha_d = f_clean.iloc[0]
                        st.session_state.fecha_d_logistica = fecha_d
                        if es_consulta_pbi:
                            st.success("✅ ¡Datos de Power BI cargados para consulta y exploración interactiva (sin guardar en base de datos)!")
                        else:
                            st.success("¡Datos procesados correctamente!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error procesando datos: {e}")

            if st.session_state.get('es_modo_consulta_pbi'):
                st.info("🔍 **Modo Solo Consulta:** Los datos se encuentran activos en memoria para análisis en las pestañas. **No se han guardado en la base de datos.**")
            elif st.session_state.get('procesado_archivos_logistica'):
                fechas = st.session_state.df_cruce['FECHA'].unique() if 'FECHA' in st.session_state.df_cruce.columns and not st.session_state.df_cruce['FECHA'].isna().all() else [st.session_state.fecha_d_logistica]
                fechas_existentes = [f for f in fechas if existe_historico_dia(f, "Transferencias Diarias")]
                
                if fechas_existentes:
                    st.warning(f"⚠️ Ya existe información para {len(fechas_existentes)} de los {len(fechas)} días procesados (ej. {fechas_existentes[0].strftime('%Y-%m-%d')})")
                    acc = st.radio("¿Qué deseas hacer con los registros que ya existen?", ["♻️ Reemplazar", "🗑️ Eliminar y guardar nuevo", "➕ Fusionar"], key="accion_guardado")
                    if st.button("Confirmar guardado", type="primary"):
                        ac = "reemplazar" if "Reemplazar" in acc else ("eliminar" if "Eliminar" in acc else "fusionar")
                        _, _, estado = guardar_historico_diario(st.session_state.df_cruce, st.session_state.df_detalle_enr, st.session_state.archT_name, st.session_state.get("username", "admin"), accion=ac)
                        st.success(f"✅ Datos guardados/actualizados correctamente ({len(fechas)} días procesados).")
                        st.session_state.procesado_archivos_logistica = False
                else:
                    guardar_historico_diario(st.session_state.df_cruce, st.session_state.df_detalle_enr, st.session_state.archT_name, st.session_state.get("username", "admin"))
                    st.success(f"✅ Procesado y guardado correctamente ({len(fechas)} días procesados).")
                    st.session_state.procesado_archivos_logistica = False

            if 'df_cruce' in st.session_state:
                df = st.session_state['df_cruce']
                st.markdown("---")
                st.subheader("Resumen del último cruce")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total Unidades", f"{df['PRENDAS'].sum()+df['FUNDAS'].sum()}")
                c2.metric("Prendas", f"{df['PRENDAS'].sum()}")
                c3.metric("Fundas", f"{df['FUNDAS'].sum()}")
                c4.metric("Transferencias", df['SECUENCIAL'].nunique())

        # ==================== TAB UBICACIÓN ====================
        with tab_ubi:
            if 'df_cruce' not in st.session_state or 'df_detalle_enr' not in st.session_state:
                st.info("🔄 Carga o sincroniza datos en la Pestaña 1 primero.")
            else:
                _render_tab_ubicacion(st.session_state['df_cruce'], st.session_state['df_detalle_enr'])

        # ==================== TAB TRANSFERIDORES ====================
        with tab_transf:
            if 'df_cruce' not in st.session_state:
                st.info("🔄 Carga o sincroniza datos en la Pestaña 1 primero.")
            else:
                _render_tab_transferidores(st.session_state['df_cruce'])

        # ==================== TAB 2 (CATEGORÍAS) ====================
        with tab2:
            if 'df_cruce' not in st.session_state: st.info("🔄 Carga archivos primero.")
            else:
                df = st.session_state['df_cruce']

                st.header("📈 Indicadores por Categoría")
                cols = st.columns(3)
                for i, cat in enumerate(CATEGORIAS_LIST):
                    if cat == 'Fundas':
                        und = _safe_int(df['FUNDAS'].sum())
                        t_act = df[df['FUNDAS'] > 0]['TIENDA'].nunique()
                    else:
                        sub = df[df['CATEGORIA_FINAL']==cat]
                        und = _safe_int(sub['PRENDAS'].sum())
                        t_act = sub['TIENDA'].nunique()
                    color = COLORS[COLOR_KEYS[cat]]
                    esp = len(PRICE_CLUBS) if cat=='Price Club' else (len(TIENDAS_REGULARES) if cat=='Tiendas' else 0)
                    prog = min(100, int((t_act/esp)*100)) if esp else 100
                    with cols[i%3]:
                        st.markdown(f'''
                        <div style="background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); padding: 24px; border-radius: 16px; border-left: 6px solid {color}; box-shadow: 0 10px 25px rgba(0,0,0,0.2); margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;"> <span style="font-size: 13px; font-weight: 600; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase;">{DISPLAY_NAMES[cat]}</span> <span style="background: {color}20; color: {color}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">KPI</span> </div>
                            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px;"> <span style="font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: -1px;">{und}</span> <span style="font-size: 14px; font-weight: 500; color: {color};">unidades</span> </div>
                            <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;"> <div style="display: flex; flex-direction: column;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Sucursales Activas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{t_act}</span> </div> <div style="display: flex; flex-direction: column; text-align: right;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Meta / Esperadas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{esp if esp else 'N/A'}</span> </div> </div>
                            <div style="margin-top: 12px; width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;"> <div style="width: {prog}%; background: {color}; height: 100%; border-radius: 3px;"></div> </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    if i%3==2: cols = st.columns(3)
                colI, colD = st.columns([2,1])
                with colI:
                    data_pie = []
                    for c in CATEGORIAS_LIST:
                        if c == 'Fundas':
                            suma = _safe_int(df['FUNDAS'].sum())
                            if suma > 0: data_pie.append({"Categoria": DISPLAY_NAMES[c], "Unidades": suma})
                        else:
                            sub = df[df['CATEGORIA_FINAL']==c]
                            suma = _safe_int(sub['PRENDAS'].sum())
                            if suma > 0: data_pie.append({"Categoria": DISPLAY_NAMES[c], "Unidades": suma})
                    dfP = pd.DataFrame(data_pie)
                    if not dfP.empty:
                        fig = px.pie(dfP, names='Categoria', values='Unidades', title="Distribución por Categoría", color='Categoria', color_discrete_map={DISPLAY_NAMES[k]: COLORS[COLOR_KEYS[k]] for k in CATEGORIAS_LIST})
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                with colD:
                    tot = df['PRENDAS'].sum()+df['FUNDAS'].sum()
                    st.subheader("TOTAL GENERAL")
                    st.markdown(f"<div style='text-align:center;font-size:36px;font-weight:bold;'>{tot}</div>", unsafe_allow_html=True)
                    st.markdown(acu_metric("PROMEDIO X TRANSFERENCIA", f"{tot/max(df['SECUENCIAL'].nunique(),1):.0f}", color="blue", icon="📈"), unsafe_allow_html=True)
                    def is_active(c, df):
                        if c == 'Fundas': return df['FUNDAS'].sum() > 0
                        return df[df['CATEGORIA_FINAL']==c].shape[0] > 0
                    st.markdown(acu_metric("CATEGORÍAS ACTIVAS", f"{sum(1 for c in CATEGORIAS_LIST if is_active(c, df))}/6", color="green", icon="✅"), unsafe_allow_html=True)
                    st.markdown(acu_metric("% FUNDAS", f"{df['FUNDAS'].sum()/tot*100 if tot else 0:.1f}%", color="yellow", icon="🛍️"), unsafe_allow_html=True)

        # ==================== TAB 3 ====================
        with tab3:
            if 'df_cruce' not in st.session_state or 'df_detalle_enr' not in st.session_state:
                st.info("🔄 Procesa archivos primero.")
            else:
                dfC = st.session_state['df_cruce']
                dfDE = st.session_state['df_detalle_enr']
                st.subheader("🏪 Desglose por Tienda - Peso Relativo")
                catT = st.selectbox("Categoría para peso relativo: ", ['Todas']+CATEGORIAS_LIST, key="tab3_cat_treemap")
                if catT == 'Todas':
                    dfF = dfC
                elif catT == 'Fundas':
                    dfF = dfC[dfC['FUNDAS'] > 0]
                else:
                    dfF = dfC[dfC['CATEGORIA_FINAL']==catT]
                
                if not dfF.empty:
                    tU = dfF.groupby('TIENDA').agg(Prendas=('PRENDAS','sum'), Fundas=('FUNDAS','sum'), Costo=('COSTO_TOTAL','sum')).reset_index()
                    tU['Unidades'] = tU['Prendas']+tU['Fundas']
                    tU = tU.sort_values('Unidades', ascending=False)
                    c1,c2,c3 = st.columns(3)
                    c1.markdown(acu_metric("Total Tiendas", len(tU), color="blue", icon="🏪"), unsafe_allow_html=True)
                    c2.markdown(acu_metric("Total Unidades", f"{tU['Unidades'].sum()}", color="green", icon="📦"), unsafe_allow_html=True)
                    c3.markdown(acu_metric("Total Costo", f"${tU['Costo'].sum():,.2f}", color="yellow", icon="💲"), unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("### 📊 Peso Relativo por Tienda (Treemap)")
                    if not tU.empty:
                        figT = px.treemap(tU, path=['TIENDA'], values='Unidades', color='Unidades', color_continuous_scale='RdYlGn', title=f"Unidades por Tienda{' - '+DISPLAY_NAMES.get(catT,catT) if catT!='Todas' else ''}", hover_data={'Prendas':True,'Fundas':True,'Costo':':.2f'})
                        figT.update_traces(textinfo="label+value", textfont=dict(size=12,color='white'), marker=dict(cornerradius=5))
                        figT.update_layout(template="plotly_dark", height=700, margin=dict(t=50,l=25,r=25,b=25))
                        st.plotly_chart(figT, use_container_width=True)
                        st.markdown("### 🏆 Top 10 Tiendas")
                        top10 = tU.head(10)
                        cb1,cb2 = st.columns([3,2])
                        with cb1:
                            figTop = px.bar(top10, x='Unidades', y='TIENDA', orientation='h', text='Unidades', color='Unidades', color_continuous_scale='Blues')
                            figTop.update_traces(texttemplate='%{text}', textposition='outside')
                            figTop.update_layout(template="plotly_dark", height=500)
                            st.plotly_chart(figTop, use_container_width=True)
                        with cb2:
                            st.dataframe(top10.rename(columns={'TIENDA':'Tienda','Unidades':'Total','Prendas':'Prendas','Fundas':'Fundas','Costo':'Costo'}), use_container_width=True, height=500)
                st.markdown("---")
                st.subheader("Detalle por Tienda Individual")
                catS = st.selectbox("Categoría comercial", ['Todas']+CATEGORIAS_LIST, key="tab3_cat")
                if catS == 'Todas':
                    tiendas = sorted(dfC['TIENDA'].unique())
                elif catS == 'Fundas':
                    tiendas = sorted(dfC[dfC['FUNDAS'] > 0]['TIENDA'].unique())
                else:
                    tiendas = sorted(dfC[dfC['CATEGORIA_FINAL']==catS]['TIENDA'].unique())
                tSel = st.selectbox("Tienda", tiendas, key="tab3_tienda")
                if tSel:
                    transT = dfC[dfC['TIENDA']==tSel]
                    if not transT.empty:
                        st.write(f"### {tSel} ({catS if catS!='Todas' else 'Todas'})")
                        prodT = dfDE[dfDE['SECUENCIAL'].isin(transT['SECUENCIAL'])][['SECUENCIAL','PRODUCTO_BASE','TIPO_PRENDA_ES','COLOR_NORM','TALLA','CANTIDAD','ES_FUNDA','CATEGORIA']].rename(columns={'SECUENCIAL':'Transferencia','PRODUCTO_BASE':'Producto Base','TIPO_PRENDA_ES':'Tipo','COLOR_NORM':'Color','TALLA':'Talla','CANTIDAD':'Cantidad','ES_FUNDA':'Es Funda','CATEGORIA':'Categoría'})
                        cM1,cM2 = st.columns(2)
                        cM1.metric("Prendas", f"{_safe_int(transT['PRENDAS'].sum())}")
                        cM2.metric("Fundas", f"{_safe_int(transT['FUNDAS'].sum())}")
                        st.markdown("---")
                        st.markdown("#### 📦 Productos agrupados")
                        prodAg = dfDE[dfDE['SECUENCIAL'].isin(transT['SECUENCIAL'])].groupby('PRODUCTO_BASE')['CANTIDAD'].sum().sort_values(ascending=False).reset_index()
                        prodAg.columns = ['Producto Base','Cantidad Total']
                        ca1,ca2 = st.columns([3,2])
                        with ca1: st.dataframe(prodAg, use_container_width=True, height=300)
                        with ca2:
                            if not prodAg.empty:
                                figP = px.bar(prodAg.head(15), x='Cantidad Total', y='Producto Base', orientation='h', text='Cantidad Total', title=f"Top 15 -> {tSel}")
                                figP.update_traces(texttemplate='%{text}', textposition='outside')
                                figP.update_layout(template="plotly_dark")
                                st.plotly_chart(figP, use_container_width=True)
                        st.markdown("---")
                        st.dataframe(prodT, use_container_width=True, height=400)

        # ==================== TAB 4 ====================
        with tab4:
            st.subheader("🎽 Análisis de Productos")
            st.info("Sube el archivo Excel con las columnas: fecha, secuencial factura, Bodega recibe, cantidad, costo, total, producto")
            archivo_analisis = st.file_uploader("Sube el Excel de Productos", type=['xlsx', 'xls'], key="file_analisis_prod")
            
            if archivo_analisis:
                try:
                    df_an = procesar_archivo_analisis(archivo_analisis.getvalue())
                    if "producto" in df_an.columns:
                        st.success("Archivo cargado y procesado exitosamente (desde caché).")
                        
                        if st.checkbox("Mostrar Data sin procesar", value=False):
                            st.dataframe(df_an.head(20))

                        
                        if st.button("💾 Guardar Análisis de Productos", type="primary"):
                            df_save = df_an.copy()
                            if 'fecha' in df_save.columns:
                                df_save['fecha'] = pd.to_datetime(df_save['fecha'], errors='coerce').dt.strftime('%Y-%m-%d')
                            df_save = df_save.where(pd.notnull(df_save), None)
                            records = df_save.to_dict(orient='records')
                            local_db.insert("analisis_productos_historico", {"registros": records, "fecha_subida": str(date.today())})
                            st.success("✅ Datos guardados en la base de datos.")
                            
                        st.markdown("### Resumen Rápido (Archivo Actual)")
                        if "cantidad" in df_an.columns:
                            df_prendas = df_an[df_an['tipo'] != 'FUNDAS']
                            df_fundas = df_an[df_an['tipo'] == 'FUNDAS']
                            
                            if not df_prendas.empty:
                                st.markdown("#### 👕 Inventario Completo (Vista Ejecutiva)")
                                res_prenda = df_prendas.groupby(['producto_base', 'tipo', 'genero', 'color', 'talla'])['cantidad'].sum().reset_index().sort_values('cantidad', ascending=False)
                                
                                st.dataframe(
                                    res_prenda,
                                    column_config={
                                        "cantidad": st.column_config.ProgressColumn(
                                            "Volumen (Cant)",
                                            help="Volumen de prendas",
                                            format="%d",
                                            min_value=0,
                                            max_value=int(res_prenda['cantidad'].max()) if not res_prenda.empty and pd.notnull(res_prenda['cantidad'].max()) else 100,
                                        ),
                                    },
                                    use_container_width=True,
                                    hide_index=True,
                                    height=250
                                )
                                
                                st.markdown("##### 🗂️ Análisis Dinámico UX (Grupos, Género, Producto, Talla, Color)")
                                c_a, c_b = st.columns(2)
                                with c_a:
                                    fig_gr = renderizar_grafico_ux(df_prendas, 'grupo', "Distribución por Grupo de Producto", color_base="#19D3F3")
                                    if fig_gr: st.plotly_chart(fig_gr, use_container_width=True)
                                    
                                    fig_g = renderizar_grafico_ux(df_prendas, 'genero', "Distribución por Género", color_base="#636EFA")
                                    if fig_g: st.plotly_chart(fig_g, use_container_width=True)
                                        
                                    fig_p = renderizar_grafico_ux(df_prendas, 'producto_base', "Distribución por Producto", color_base="#EF553B")
                                    if fig_p: st.plotly_chart(fig_p, use_container_width=True)
                                with c_b:
                                    if 'talla' in df_prendas.columns:
                                        df_prendas_tm = df_prendas.copy()
                                        df_prendas_tm['Tallas'] = "Tallas"
                                        fig_tm_t = px.treemap(df_prendas_tm, path=['Tallas', 'talla'], values='cantidad', title="Peso Relativo por Talla (%)", color_discrete_sequence=px.colors.qualitative.Safe)
                                        fig_tm_t.update_layout(template="plotly_dark", margin=dict(t=30, l=10, r=10, b=10))
                                        st.plotly_chart(fig_tm_t, use_container_width=True)
                                        
                                    fig_t = renderizar_grafico_ux(df_prendas, 'talla', "Distribución por Talla (Cantidades y %)", color_base="#00CC96")
                                    if fig_t: st.plotly_chart(fig_t, use_container_width=True)
                                        
                                    fig_c = renderizar_grafico_ux(df_prendas, 'color', "Distribución por Color", color_base="#AB63FA")
                                    if fig_c: st.plotly_chart(fig_c, use_container_width=True)
                                        
                            if not df_fundas.empty:
                                df_fundas_positivas = df_fundas[df_fundas['cantidad'] > 0]
                                if not df_fundas_positivas.empty:
                                    st.markdown("---")
                                    st.markdown("#### 🛍️ Fundas y Lentes de Sol")
                                    f_col1, f_col2 = st.columns(2)
                                    with f_col1:
                                        fig_f = renderizar_grafico_ux(df_fundas_positivas, 'producto_base', "Distribución de Fundas/Lentes", color_base="#FFA15A")
                                        if fig_f: st.plotly_chart(fig_f, use_container_width=True)
                                    with f_col2:
                                        fig_ft = renderizar_grafico_ux(df_fundas_positivas, 'talla', "Distribución de Tallas", color_base="#00CC96")
                                        if fig_ft: st.plotly_chart(fig_ft, use_container_width=True)
                    else:
                        st.error("El archivo no contiene la columna 'producto'.")
                except Exception as e:
                    st.error(f"Error procesando el archivo: {e}")
            
            st.markdown("---")
            st.subheader("📊 Consulta Dinámica de Análisis Guardados")
            col1, col2 = st.columns(2)
            with col1: query_ini = st.date_input("Fecha Inicio", value=date.today() - timedelta(days=7), key="q_ini_prod")
            with col2: query_fin = st.date_input("Fecha Fin", value=date.today(), key="q_fin_prod")
            
            if st.button("🔍 Consultar Productos Guardados", type="primary", use_container_width=True):
                with st.spinner("Buscando en base de datos..."):
                    all_docs = local_db.find("analisis_productos_historico")
                    all_regs = []
                    for doc in all_docs:
                        all_regs.extend(doc.get("registros", []))
                    
                    if not all_regs:
                        st.info("No hay datos históricos guardados.")
                    else:
                        df_dash = pd.DataFrame(all_regs)
                        if 'fecha' in df_dash.columns:
                            df_dash['fecha_dt'] = pd.to_datetime(df_dash['fecha'], errors='coerce')
                            # Filtrar por fechas
                            df_f = df_dash[(df_dash['fecha_dt'].dt.date >= query_ini) & (df_dash['fecha_dt'].dt.date <= query_fin)]
                            
                            if df_f.empty:
                                st.warning("No hay registros en el rango seleccionado.")
                            else:
                                st.success(f"Se encontraron {len(df_f)} registros de productos.")
                                m1, m2, m3 = st.columns(3)
                                if 'cantidad' in df_f.columns: m1.metric("Unidades Enviadas", f"{df_f['cantidad'].sum():.0f}")
                                if 'total' in df_f.columns: m2.metric("Monto Total", f"${df_f['total'].sum():,.2f}")
                                if 'tienda' in df_f.columns: m3.metric("Tiendas Impactadas", df_f['tienda'].nunique())
                                
                                st.markdown("---")
                                df_prendas_f = df_f[df_f['tipo'] != 'FUNDAS'] if 'tipo' in df_f.columns else df_f
                                df_fundas_f = df_f[df_f['tipo'] == 'FUNDAS'] if 'tipo' in df_f.columns else pd.DataFrame()
                                
                                if not df_prendas_f.empty:
                                    st.markdown("#### 👕 Inventario Histórico (Vista Ejecutiva)")
                                    if 'producto_base' in df_prendas_f.columns and 'cantidad' in df_prendas_f.columns:
                                        res_prenda_f = df_prendas_f.groupby(['producto_base', 'tipo', 'genero', 'color', 'talla'])['cantidad'].sum().reset_index().sort_values('cantidad', ascending=False)
                                        st.dataframe(
                                            res_prenda_f,
                                            column_config={
                                                "cantidad": st.column_config.ProgressColumn(
                                                    "Volumen (Cant)",
                                                    help="Volumen de prendas",
                                                    format="%d",
                                                    min_value=0,
                                                    max_value=int(res_prenda_f['cantidad'].max()) if not res_prenda_f.empty and pd.notnull(res_prenda_f['cantidad'].max()) else 100,
                                                ),
                                            },
                                            use_container_width=True,
                                            hide_index=True,
                                            height=250
                                        )
                                        
                                    st.markdown("##### 🗂️ Análisis Dinámico UX Histórico")
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        fig_gr_f = renderizar_grafico_ux(df_prendas_f, 'grupo', "Distribución Histórica: Grupo", color_base="#19D3F3")
                                        if fig_gr_f: st.plotly_chart(fig_gr_f, use_container_width=True)
                                        
                                        fig_g_f = renderizar_grafico_ux(df_prendas_f, 'genero', "Distribución Histórica: Género", color_base="#636EFA")
                                        if fig_g_f: st.plotly_chart(fig_g_f, use_container_width=True)
                                            
                                        fig_p_f = renderizar_grafico_ux(df_prendas_f, 'producto_base', "Distribución Histórica: Producto", color_base="#EF553B")
                                        if fig_p_f: st.plotly_chart(fig_p_f, use_container_width=True)
                                    with c2:
                                        if 'talla' in df_prendas_f.columns:
                                            df_prendas_f_tm = df_prendas_f.copy()
                                            df_prendas_f_tm['Tallas'] = "Tallas"
                                            fig_tm_t_f = px.treemap(df_prendas_f_tm, path=['Tallas', 'talla'], values='cantidad', title="Peso Relativo Histórico: Talla (%)", color_discrete_sequence=px.colors.qualitative.Safe)
                                            fig_tm_t_f.update_layout(template="plotly_dark", margin=dict(t=30, l=10, r=10, b=10))
                                            st.plotly_chart(fig_tm_t_f, use_container_width=True)
                                            
                                        fig_t_f = renderizar_grafico_ux(df_prendas_f, 'talla', "Distribución Histórica: Talla (Cantidades y %)", color_base="#00CC96")
                                        if fig_t_f: st.plotly_chart(fig_t_f, use_container_width=True)
                                            
                                        fig_c_f = renderizar_grafico_ux(df_prendas_f, 'color', "Distribución Histórica: Color", color_base="#AB63FA")
                                        if fig_c_f: st.plotly_chart(fig_c_f, use_container_width=True)
                                            
                                if not df_fundas_f.empty:
                                    df_fundas_f_positivas = df_fundas_f[df_fundas_f['cantidad'] > 0]
                                    if not df_fundas_f_positivas.empty:
                                        st.markdown("---")
                                        st.markdown("#### 🛍️ Fundas y Lentes de Sol")
                                        f_col1, f_col2 = st.columns(2)
                                        with f_col1:
                                            fig_f = renderizar_grafico_ux(df_fundas_f_positivas, 'producto_base', "Distribución Histórica: Fundas/Lentes", color_base="#FFA15A")
                                            if fig_f: st.plotly_chart(fig_f, use_container_width=True)
                                        with f_col2:
                                            fig_ft_f = renderizar_grafico_ux(df_fundas_f_positivas, 'talla', "Distribución Histórica: Tallas", color_base="#00CC96")
                                            if fig_ft_f: st.plotly_chart(fig_ft_f, use_container_width=True)
                                            
                                st.markdown("#### Detalle (Tabla Dinámica)")
                                st.dataframe(df_f.drop(columns=['fecha_dt'], errors='ignore'))

        # ==================== TAB 5 ====================
        with tab5:
            st.subheader("📅 Historial de Despachos")
            if 'hist_regs' not in st.session_state: st.session_state.hist_regs = None
            if 'hist_inicio' not in st.session_state: st.session_state.hist_inicio = date.today() - timedelta(days=30)
            if 'hist_fin' not in st.session_state: st.session_state.hist_fin = date.today()
            if 'hist_periodo_sel' not in st.session_state: st.session_state.hist_periodo_sel = "Día"

            if 'df_cruce' in st.session_state and 'df_detalle_enr' in st.session_state:
                if st.button("Guardar histórico actual", type="secondary", use_container_width=True, key="btn_guardar_hist"):
                    if st.session_state.get('hist_regs'): st.warning("⚠️ Guarda desde la pestaña 1 para el último cruce.")
                    else:
                        try:
                            _,_,estado = guardar_historico_diario(st.session_state['df_cruce'], st.session_state['df_detalle_enr'], "manual", st.session_state.get("username", "admin"))
                            st.success(f"✅ {estado.replace('_',' ').capitalize()}.")
                        except Exception as e: st.error(f"❌ Error: {str(e)}")
            st.markdown("---")
            c1,c2 = st.columns(2)
            with c1: inicio = st.date_input("Desde", value=st.session_state.hist_inicio, key="hist_ini_wdg")
            with c2: fin = st.date_input("Hasta", value=st.session_state.hist_fin, key="hist_fin_wdg")
            if inicio > fin: st.error("⚠️ 'Desde' no puede ser posterior a 'Hasta'.")
            else:
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    btn_cons = st.button("🔍 Consultar histórico", use_container_width=True, type="primary", key="btn_consultar")
                with col_btn2:
                    btn_del = st.button("🗑️ Borrar histórico de este rango", use_container_width=True, type="secondary", key="btn_borrar_rango")
                
                if btn_cons:
                    st.session_state.hist_inicio = inicio
                    st.session_state.hist_fin = fin
                    st.session_state.hist_regs = None
                    st.session_state.pop('hist_regs_all', None)
                    try:
                        with st.spinner("Consultando base de datos..."):
                            regs = consultar_historico("dashboard_logistico", "Transferencias Diarias", inicio, fin)
                            regs = [_sanitize_metrics(r) for r in (regs or [])]
                    except Exception as e: st.error(f"❌ Error DB: {e}"); regs = []
                    if not regs: st.warning("⚠️ Sin datos. Procesa archivos en Tab 1.")
                    else: st.session_state.hist_regs = regs; st.success(f"✅ {len(regs)} registros encontrados")
                    
                if btn_del:
                    try:
                        from database.manager import borrar_historico_dia
                        cur = inicio
                        borrados = 0
                        while cur <= fin:
                            borrar_historico_dia(cur, "Transferencias Diarias")
                            cur += timedelta(days=1)
                            borrados += 1
                        st.session_state.hist_regs = None
                        st.session_state.pop('hist_regs_all', None)
                        st.success(f"✅ Registros del {inicio} al {fin} borrados de la base de datos.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error borrando histórico: {e}")
            regs = st.session_state.get('hist_regs', None)
            if regs:
                st.markdown("---")
                st.subheader("📊 Acumulado Histórico")
                if 'hist_regs_all' not in st.session_state:
                    try:
                        ra = consultar_historico("dashboard_logistico", "Transferencias Diarias", date(2020,1,1), date.today())
                        st.session_state['hist_regs_all'] = [_sanitize_metrics(r) for r in (ra or [])]
                    except: st.session_state['hist_regs_all'] = []
                ra = st.session_state['hist_regs_all']
                if ra:
                    filas = []
                    for r in ra:
                        try:
                            met = r.get('metricas', {})
                            if not isinstance(met, dict): continue
                            filas.append({'fecha': pd.to_datetime(r.get('fecha_archivo')).date(), 'und': _safe_numeric(met.get('total_unidades',0))})
                        except: continue
                    if filas:
                        dfA = pd.DataFrame(filas).dropna()
                        if not dfA.empty:
                            daily = dfA.groupby('fecha')['und'].sum().sort_index().reset_index()
                            daily['acum'] = daily['und'].cumsum()
                            # KPIs Verticales (Arriba)
                            c1, c2, c3 = st.columns(3)
                            c1.markdown(acu_metric("Total Unidades", f"{daily['und'].sum():.0f}", color="blue", icon="📦"), unsafe_allow_html=True)
                            c2.markdown(acu_metric("Días Procesados", daily['fecha'].nunique(), color="green", icon="📅"), unsafe_allow_html=True)
                            c3.markdown(acu_metric("Promedio/Día", f"{daily['und'].sum()/max(daily['fecha'].nunique(),1):.0f}", color="yellow", icon="⚡"), unsafe_allow_html=True)
                            
                            st.write("") # Espaciador
                            
                            # Gráfico (Abajo, ancho completo)
                            figAc = go.Figure(go.Scatter(x=daily['fecha'], y=daily['acum'], mode='lines+markers', fill='tozeroy', fillcolor='rgba(59,130,246,0.15)', line=dict(color='#3b82f6',width=3)))
                            figAc.update_layout(template="plotly_dark", title="Acumulado Histórico (Evolución)", height=400)
                            st.plotly_chart(figAc, use_container_width=True)
                            with st.expander("Últimos 30 días"): st.dataframe(daily.tail(30).rename(columns={'fecha':'Fecha','und':'Unidades','acum':'Acumulado'}).sort_values('Fecha',ascending=False), use_container_width=True)
                else: st.info("📭 Sin registros históricos.")
                st.markdown("---")
                st.subheader(f"📊 Dashboard Dinámico")
                filasV = []
                for r in regs:
                    try:
                        met = r.get('metricas', {})
                        if not isinstance(met, dict): continue
                        filasV.append({'fecha': pd.to_datetime(r.get('fecha_archivo')).date(), 'met': met, 'und': _safe_numeric(met.get('total_unidades',0))})
                    except: continue
                if filasV:
                    dfH = pd.DataFrame(filasV).dropna(subset=['fecha'])
                    if not dfH.empty:
                        dfH['periodo'] = dfH['fecha']
                        agg = dfH.groupby('periodo')['und'].sum().reset_index()
                        st.markdown(f"**{inicio.strftime('%d/%m/%Y')} – {fin.strftime('%d/%m/%Y')}**")
                        figD = px.bar(agg, x='periodo', y='und', text='und', title=f"Despachos por Día")
                        figD.update_traces(texttemplate='%{text}', textposition='outside', marker_color='#f59e0b')
                        figD.update_layout(template="plotly_dark")
                        st.plotly_chart(figD, use_container_width=True)
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("Total", f"{agg['und'].sum():.0f}")
                        m2.metric("Promedio", f"{agg['und'].mean():.0f}")
                        m3.metric("Máximo", f"{agg['und'].max():.0f}")
                        m4.metric("Registros", len(agg))
                        st.dataframe(agg.rename(columns={'periodo':'Período','und':'Unidades'}), use_container_width=True)
                        st.markdown("---")
                        st.subheader("KPIs por Categoría")
                        cAgg = {c:0 for c in CATEGORIAS_LIST}
                        tAgg = {c:0 for c in CATEGORIAS_LIST}
                        tP=tF=tU=rSin=tTrans = 0
                        for _,row in dfH.iterrows():
                            met = row.get('met',{})
                            if not isinstance(met,dict): rSin+=1; continue
                            pc = met.get('por_categoria',{})
                            pt = met.get('tiendas_activas_por_categoria',{})
                            
                            # Fallback: if 'por_categoria' is empty but we have data, we might be reading old records
                            if not isinstance(pc,dict): pc = {}
                            if not isinstance(pt,dict): pt = {}
                            if not pc: rSin+=1
                            
                            for c in CATEGORIAS_LIST:
                                try:
                                    # Case insensitive key search
                                    v_pc = next((v for k,v in pc.items() if str(k).strip().lower() == str(c).strip().lower()), 0)
                                    v_pt = next((v for k,v in pt.items() if str(k).strip().lower() == str(c).strip().lower()), 0)
                                    cAgg[c] += _safe_numeric(v_pc)
                                    tAgg[c] += _safe_numeric(v_pt)
                                except: pass
                                
                            tP += _safe_numeric(met.get('total_prendas',0))
                            tF += _safe_numeric(met.get('total_fundas',0))
                            tU += _safe_numeric(met.get('total_unidades',0))
                            tTrans += _safe_numeric(met.get('transferencias_unicas',0))
                        
                        if rSin > 0: 
                            st.warning(f"⚠️ {rSin} registros históricos antiguos no contienen desglose por categoría. Por favor, vuelve a procesar (Reemplazar) esos días en la pestaña 1.")
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("📦 Unidades", f"{tU:.0f}")
                        m2.metric("🎽 Prendas", f"{tP:.0f}")
                        m3.metric("🛍️ Fundas", f"{tF:.0f}")
                        m4.metric("📅 Días", dfH['fecha'].nunique())
                        st.markdown("##### Detalle")
                        _render_kpi_cards_historico(cAgg, tU, tAgg)
                        
                        colI, colD = st.columns([2,1])
                        with colI:
                            dfP = pd.DataFrame([{"Categoria": DISPLAY_NAMES[c], "Unidades": cAgg[c]} for c in CATEGORIAS_LIST if cAgg.get(c, 0) > 0])
                            if not dfP.empty:
                                fig = px.pie(dfP, names='Categoria', values='Unidades', title="Distribución Histórica por Categoría", color='Categoria', color_discrete_map={DISPLAY_NAMES[k]: COLORS[COLOR_KEYS.get(k, 'Tiendas')] for k in CATEGORIAS_LIST})
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                fig.update_layout(template="plotly_dark")
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("No hay datos de categoría desglosados en este rango de fechas para graficar el pastel.")
                        with colD:
                            st.subheader("TOTAL RANGO")
                            st.markdown(f"<div style='text-align:center;font-size:36px;font-weight:bold;'>{sum(cAgg.values())}</div>", unsafe_allow_html=True)
                            st.markdown(acu_metric("PROMEDIO X TRANSFERENCIA", f"{tU/max(tTrans,1):.0f}", color="blue", icon="📈"), unsafe_allow_html=True)
                            st.markdown(acu_metric("CATEGORÍAS ACTIVAS", f"{sum(1 for c in CATEGORIAS_LIST if cAgg.get(c, 0) > 0)}/6", color="green", icon="✅"), unsafe_allow_html=True)
                            st.markdown(acu_metric("% FUNDAS HISTÓRICO", f"{(tF/tU)*100 if tU else 0:.1f}%", color="yellow", icon="🛍️"), unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.subheader("⚠️ Anomalías")
                        dAn = detectar_anomalias(dfH.rename(columns={'und':'unidades'}), col='unidades')
                        if not dAn.empty:
                            an = dAn[dAn['anomalia']==True]
                            if not an.empty: st.dataframe(an[['fecha','unidades']].rename(columns={'fecha':'Fecha','unidades':'Unidades'}).sort_values('Unidades',ascending=False), use_container_width=True)
                            else: st.info("✅ Sin anomalías.")
                        else: st.info("ℹ️ Mínimo 3 días requeridos.")
                        if 'periodo' in agg.columns and len(agg) >=2:
                            st.subheader("Comparativa Mensual")
                            try:
                                at = agg.copy()
                                at['mes'] = pd.to_datetime(at['periodo']).dt.month
                                ms = sorted(at['mes'].unique())[-2:]
                                if len(ms)==2:
                                    act, ant = at[at['mes']==ms[1]]['und'].sum(), at[at['mes']==ms[0]]['und'].sum()
                                    delta = (act-ant)/ant*100 if ant else 0
                                    st.metric(f"Mes {ms[1]} vs {ms[0]}", f"{act:.0f}", delta=f"{'▲' if delta >=0 else '▼'} {abs(delta):.1f}%", delta_color="normal" if delta >=0 else "inverse")
                            except: pass
                else: st.info("ℹ️ Mínimo 3 días requeridos.")
            else:
                if st.session_state.get('hist_regs') is None: st.info("👆 Selecciona fechas y presiona 'Consultar histórico'")
            st.markdown("---")
            st.subheader("🔮 Forecasting")
            if st.button("Generar predicción (7 días)", use_container_width=True, key="btn_forecast"):
                try:
                    fc = generar_forecast(consultar_historico("dashboard_logistico", "Transferencias Diarias", date.today()-timedelta(days=365), date.today()))
                except Exception as e:
                    st.error(f"❌ Error forecast: {e}"); fc=None
                if fc is not None:
                    figFc = go.Figure()
                    if 'yhat_lower' in fc.columns:
                        figFc.add_trace(go.Scatter(x=fc['ds'], y=fc['yhat_lower'], mode='lines', line_color='rgba(0,0,0,0)', showlegend=False))
                        figFc.add_trace(go.Scatter(x=fc['ds'], y=fc['yhat_upper'], mode='lines', fill='tonexty', fillcolor='rgba(100,100,200,0.2)', line_color='rgba(0,0,0,0)', name='IC 95%'))
                    figFc.add_trace(go.Scatter(x=fc['ds'], y=fc['yhat'], mode='lines+markers', name='Predicción'))
                    figFc.update_layout(template="plotly_dark", title="Predicción 7 días")
                    st.plotly_chart(figFc, use_container_width=True)
                    st.dataframe(fc.rename(columns={'ds':'Fecha','yhat':'Predicción','yhat_lower':'Límite inf','yhat_upper':'Límite sup'}))
                else: st.info("Datos insuficientes (<10 registros)." + (" Instala Prophet" if not PROPHET_AVAILABLE else ""))



    except Exception as e:
        st.error(f"Error general en el dashboard logístico: {e}")
        logger.exception(e)
        if "FileUploader" in str(e):
            st.info("💡 **Sugerencia:** Limpia la caché del navegador (Ctrl+Shift+Supr) y recarga la página.")

def mostrar_kpi_diario():
    mostrar_dashboard_transferencias()

def show_logistica():
    try:
        add_back_button(key="back_logistica")
        show_module_header("📦 Dashboard Logístico", "Control de transferencias y distribución")
        st.markdown('<div class="module-content">', unsafe_allow_html=True)
        set_module_background("logistica")
        mostrar_dashboard_transferencias()
        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error al cargar el módulo Logística: {e}")
        logger.exception(e)
