# modules/logistica.py
# ============================================================================
# DASHBOARD LOGÍSTICO - TRANSFERENCIAS Y DISTRIBUCIÓN
# Versión completa y corregida (error FileUploader solucionado)
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
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
from ai.supply_chain_ai import _ejecutar_prompt, transcribir_audio as transcribir_audio_central

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
        clean_met[k] = _safe_numeric(v) if isinstance(v, (dict, str, int, float)) else v
    raw_reg['metricas'] = clean_met
    return raw_reg

# =============================================================================
# PARSER DE PRODUCTOS - CLASIFICACIÓN AVANZADA
# =============================================================================
def clasificar_producto_avanzado(nombre_producto, codigo_producto=None):
    """Extrae género, color, talla, tipo de prenda de forma segura."""
    if pd.isna(nombre_producto) or not isinstance(nombre_producto, str):
        return None, None, None, None, None
    nombre_upper = nombre_producto.upper().strip()
    palabras = nombre_upper.split()

    # Género
    genero = "OTROS"
    if any(g in nombre_upper for g in ['GUYS', 'HOMBRE', 'MEN', 'MASCULINO']):
        genero = "GUYS"
    elif any(g in nombre_upper for g in ['GIRLS', 'MUJER', 'WOMEN', 'FEMENINO', 'LADIES']):
        genero = "GIRLS"
    elif any(g in nombre_upper for g in ['KIDS', 'NIÑO', 'NIÑA', 'JUNIOR', 'YOUTH']):
        genero = "KIDS"
    elif any(g in nombre_upper for g in ['ACCESORIO', 'ACCESORIES', 'COMPLEMENTO']):
        genero = "ACCESORIOS"

    # Tallas
    tallas_ref = {'XS','S','M','L','XL','XXL','XXXL','2XL','3XL','UNICA','ÚNICA','ONE-SIZE','ONESIZE'}
    tallas_adicionales = {'XSMALL':'XS', 'SMALL':'S', 'MEDIUM':'M', 'LARGE':'L', 'X-LARGE':'XL', 'XX-LARGE':'XXL'}
    talla = None
    for p in palabras:
        p_clean = p.replace('-','').replace('.','')
        if p_clean in tallas_ref:
            talla = p_clean
            break
        if p_clean in tallas_adicionales:
            talla = tallas_adicionales[p_clean]
            break

    # Colores
    colores_ref = {'BLACK','WHITE','RED','BLUE','GREEN','YELLOW','PINK','PURPLE','ORANGE','BROWN','GRAY','GREY',
                   'NAVY','KHAKI','BEIGE','CREAM','EGRET','IVORY','TEAL','CORAL','MINT','LAVENDER','BURGUNDY','OLIVE',
                   'CHARCOAL','HEATHER','ASH','DENIM','INDIGO','VIOLET','MAGENTA','FUCHSIA','TURQUOISE','AQUA',
                   'MAROON','CRIMSON','SCARLET','RUBY','SILVER','GOLD','BRONZE','COPPER'}
    color = None
    color_words = []
    for i, p in enumerate(palabras):
        if p in colores_ref or (i > 0 and palabras[i-1] in colores_ref):
            color_words.append(p)
    if color_words:
        color = ' '.join(color_words)

    # Tipo de prenda
    palabras_excluir = {'GUYS','GIRLS','KIDS','BOYS','GIRLS','MEN','WOMEN','LADIES','YOUTH',
                        'XS','S','M','L','XL','XXL','XXXL','2XL','3XL','UNICA','ÚNICA',
                        'XSMALL','SMALL','MEDIUM','LARGE','X-LARGE','XX-LARGE',
                        'REGULAR','SLIM','FIT','STRETCH'}
    palabras_excluir.update(colores_ref)
    tipo_prenda_words = [p for p in palabras if p not in palabras_excluir and p not in color_words]
    tipo_prenda = ' '.join(tipo_prenda_words) if tipo_prenda_words else nombre_producto

    # Código base
    codigo_base = None
    if codigo_producto and not pd.isna(codigo_producto):
        codigo_str = str(codigo_producto)
        codigo_base = codigo_str[:7] if len(codigo_str) >= 7 else codigo_str

    return tipo_prenda.strip(), genero, color, talla, codigo_base

# =============================================================================
# RENDERIZADO KPIs
# =============================================================================
def _render_kpi_cards_historico(cat_agg: dict, total_unidades: int) -> None:
    cols = st.columns(3)
    for i, cat in enumerate(CATEGORIAS_LIST):
        unidades = _safe_int(cat_agg.get(cat, 0))
        color_key = COLOR_KEYS.get(cat, '')
        color = COLORS.get(color_key, '#64748b')
        nombre = DISPLAY_NAMES.get(cat, cat.upper())
        pct = round(unidades / total_unidades * 100, 1) if total_unidades > 0 else 0.0
        with cols[i % 3]:
            st.markdown(f'''
            <div style="background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); padding: 24px; border-radius: 16px; border-left: 6px solid {color}; box-shadow: 0 10px 25px rgba(0,0,0,0.2); margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 13px; font-weight: 600; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase;">{nombre}</span>
                    <span style="background: {color}20; color: {color}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">HIST</span>
                </div>
                <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px;">
                    <span style="font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: -1px;">{unidades:,}</span>
                    <span style="font-size: 14px; font-weight: 500; color: {color};">unidades</span>
                </div>
                <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;">
                    <div style="display: flex; flex-direction: column;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">% del Total</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{pct}%</span> </div>
                </div>
                <div style="margin-top: 12px; width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;"> <div style="width: {pct}%; background: {color}; height: 100%; border-radius: 3px;"></div> </div>
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
    for dia in fechas:
        if pd.isna(dia): dia = fecha_hoy
        secs = df_cruce[df_cruce['FECHA'] == dia]['SECUENCIAL'].unique() if 'FECHA' in df_cruce.columns else df_cruce['SECUENCIAL'].unique()
        det_dia = df_det[df_det['SECUENCIAL'].isin(secs)]
        prendas = det_dia[~det_dia['ES_FUNDA']]
        met = {
            "total_unidades": _safe_int(df_cruce['PRENDAS'].sum() + df_cruce['FUNDAS'].sum()),
            "total_prendas": _safe_int(df_cruce['PRENDAS'].sum()),
            "total_fundas": _safe_int(df_cruce['FUNDAS'].sum()),
            "transferencias_unicas": _safe_int(df_cruce['SECUENCIAL'].nunique()),
            "costo_total": round(float(df_cruce['COSTO_TOTAL'].sum()), 2),
            "por_categoria": {},
            "por_tipo_prenda": prendas.groupby('TIPO_PRENDA_ES')['CANTIDAD'].sum().to_dict() if not prendas.empty else {},
            "por_color": prendas.groupby('COLOR_NORM')['CANTIDAD'].sum().nlargest(10).to_dict() if not prendas.empty else {},
            "por_talla": prendas.groupby('TALLA')['CANTIDAD'].sum().to_dict() if not prendas.empty else {},
            "por_genero": prendas.groupby('GENERO')['CANTIDAD'].sum().to_dict() if not prendas.empty else {}
        }
        for cat in CATEGORIAS_LIST:
            sub = df_cruce[df_cruce['CATEGORIA_FINAL'] == cat]
            met['por_categoria'][cat] = _safe_int(sub['FUNDAS'].sum()) if cat == 'Fundas' and not sub.empty else (_safe_int(sub['PRENDAS'].sum()) if not sub.empty else 0)
        met_san = sanitize_for_mongo(met)
        existe = existe_historico_dia(dia, "Transferencias Diarias")
        try:
            from database.manager import eliminar_historico_dia
        except ImportError:
            eliminar_historico_dia = None
        if accion == "eliminar":
            if existe and eliminar_historico_dia:
                eliminar_historico_dia(dia, "Transferencias Diarias")
            guardar_historico("dashboard_logistico", "Transferencias Diarias", pd.DataFrame(), met_san, archivo_nombre, dia, usuario)
            return True, dia, "eliminado_y_guardado"
        elif accion == "reemplazar":
            if existe and eliminar_historico_dia:
                eliminar_historico_dia(dia, "Transferencias Diarias")
            guardar_historico("dashboard_logistico", "Transferencias Diarias", pd.DataFrame(), met_san, archivo_nombre, dia, usuario)
            return True, dia, "reemplazado"
        else:
            if existe:
                fusionar_historico_dia(dia, met_san, "Transferencias Diarias")
                return True, dia, "fusionado"
            else:
                guardar_historico("dashboard_logistico", "Transferencias Diarias", pd.DataFrame(), met_san, archivo_nombre, dia, usuario)
                return True, dia, "guardado"
    return True, fecha_hoy, "guardado"

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

# =============================================================================
# ASISTENTE IA
# =============================================================================
def _contexto_ia(df_c, df_d, regs):
    cats = {c: _safe_int((df_c[df_c['CATEGORIA_FINAL']==c]['FUNDAS'].sum() if c=='Fundas' else df_c[df_c['CATEGORIA_FINAL']==c]['PRENDAS'].sum())) for c in CATEGORIAS_LIST}
    return f"Eres asistente de logística Aeropostale. Prendas: {df_c['PRENDAS'].sum():,}, Fundas: {df_c['FUNDAS'].sum():,}. Cats: {cats}. Responde breve."

def _responder_ia(preg, df_c, df_d, regs):
    p = preg.lower().strip()
    if 'cuántas' in p or 'cuantas' in p:
        if 'funda' in p: return f"Total fundas: {df_c['FUNDAS'].sum():,}"
        if 'prenda' in p: return f"Total prendas: {df_c['PRENDAS'].sum():,}"
    return _ejecutar_prompt(f"{_contexto_ia(df_c, df_d, regs)}\nPregunta: {preg}", "No pude procesar la consulta.")

def transcribir_audio(audio_bytes): return transcribir_audio_central(audio_bytes)

# =============================================================================
# INTERFAZ PRINCIPAL CORREGIDA (FileUploader en formulario)
# =============================================================================
def mostrar_dashboard_transferencias():
    try:
        st.markdown("<div class='main-header'><h1 class='header-title'>📊 Dashboard de Logística</h1><div class='header-subtitle'>Análisis inteligente de distribución</div></div>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📂 Carga y Cruce", "📈 KPIs por Categoría", "🏪 Desglose por Tienda", "🎽 Análisis de Productos", "📅 Histórico + Forecast", "🤖 Asistente IA"])

        # ==================== TAB 1 (CORREGIDA) ====================
        with tab1:
            st.subheader("Sube los archivos para el análisis")
            with st.form(key="upload_form", clear_on_submit=False):
                colA, colB = st.columns(2)
                with colA:
                    archT = st.file_uploader("Archivo transferencias (.xlsx)", type=['xlsx'], key="trans_uploader")
                with colB:
                    archD = st.file_uploader("Archivo detalle (.xlsx)", type=['xlsx'], key="det_uploader")
                procesar_click = st.form_submit_button("🔀 Procesar cruce", type="primary", use_container_width=True)

            if procesar_click and archT and archD:
                try:
                    dfT, dfD = pd.read_excel(archT), pd.read_excel(archD)
                    dfC, dfDE = procesar_archivos(dfT, dfD)
                    if dfC is not None and dfDE is not None:
                        st.session_state.update({'df_cruce': dfC, 'df_detalle_enr': dfDE})
                        st.session_state.procesado_archivos_logistica = True
                        st.session_state.archT_name = archT.name
                        fecha_d = date.today()
                        if 'FECHA' in dfC.columns:
                            f_clean = dfC['FECHA'].dropna()
                            if not f_clean.empty:
                                fecha_d = f_clean.iloc[0]
                        st.session_state.fecha_d_logistica = fecha_d
                except Exception as e:
                    st.error(f"Error procesando archivos: {e}")

            if st.session_state.get('procesado_archivos_logistica'):
                existe = existe_historico_dia(st.session_state.fecha_d_logistica, "Transferencias Diarias")
                if existe:
                    st.warning(f"⚠️ Ya existe información para **{st.session_state.fecha_d_logistica.strftime('%Y-%m-%d')}**")
                    acc = st.radio("¿Qué deseas hacer?", ["🔄 Fusionar", "♻️ Reemplazar", "🗑️ Eliminar y guardar nuevo"], key="accion_guardado")
                    if st.button("Confirmar guardado", type="primary"):
                        ac = "fusionar" if "Fusionar" in acc else ("reemplazar" if "Reemplazar" in acc else "eliminar")
                        _, _, estado = guardar_historico_diario(st.session_state.df_cruce, st.session_state.df_detalle_enr, st.session_state.archT_name, st.session_state.get("username", "admin"), accion=ac)
                        st.success(f"✅ {estado.replace('_',' ').capitalize()} correctamente.")
                        st.session_state.procesado_archivos_logistica = False
                else:
                    guardar_historico_diario(st.session_state.df_cruce, st.session_state.df_detalle_enr, st.session_state.archT_name, st.session_state.get("username", "admin"))
                    st.success("✅ Procesado y guardado correctamente.")
                    st.session_state.procesado_archivos_logistica = False
                elif procesar_click:
                    st.warning("Selecciona ambos archivos antes de procesar.")

            if 'df_cruce' in st.session_state:
                df = st.session_state['df_cruce']
                st.markdown("---")
                st.subheader("Resumen del último cruce")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Total Unidades", f"{df['PRENDAS'].sum()+df['FUNDAS'].sum():,}")
                c2.metric("Prendas", f"{df['PRENDAS'].sum():,}")
                c3.metric("Fundas", f"{df['FUNDAS'].sum():,}")
                c4.metric("Transferencias", df['SECUENCIAL'].nunique())

        # ==================== TAB 2 ====================
        with tab2:
            if 'df_cruce' not in st.session_state: st.info("🔄 Carga archivos primero.")
            else:
                df = st.session_state['df_cruce']
                st.header("📈 Indicadores por Categoría")
                cols = st.columns(3)
                for i, cat in enumerate(CATEGORIAS_LIST):
                    sub = df[df['CATEGORIA_FINAL']==cat]
                    und = _safe_int(sub['FUNDAS'].sum() if cat=='Fundas' else sub['PRENDAS'].sum())
                    t_act = sub['TIENDA'].nunique()
                    color = COLORS[COLOR_KEYS[cat]]
                    esp = len(PRICE_CLUBS) if cat=='Price Club' else (len(TIENDAS_REGULARES) if cat=='Tiendas' else 0)
                    prog = min(100, int((t_act/esp)*100)) if esp else 100
                    with cols[i%3]:
                        st.markdown(f'''
                        <div style="background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); padding: 24px; border-radius: 16px; border-left: 6px solid {color}; box-shadow: 0 10px 25px rgba(0,0,0,0.2); margin-bottom: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;"> <span style="font-size: 13px; font-weight: 600; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase;">{DISPLAY_NAMES[cat]}</span> <span style="background: {color}20; color: {color}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold;">KPI</span> </div>
                            <div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px;"> <span style="font-size: 42px; font-weight: 800; color: #ffffff; letter-spacing: -1px;">{und:,}</span> <span style="font-size: 14px; font-weight: 500; color: {color};">unidades</span> </div>
                            <div style="display: flex; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px;"> <div style="display: flex; flex-direction: column;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Sucursales Activas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{t_act}</span> </div> <div style="display: flex; flex-direction: column; text-align: right;"> <span style="font-size: 11px; color: #64748b; margin-bottom: 2px;">Meta / Esperadas</span> <span style="font-size: 14px; font-weight: 600; color: #e2e8f0;">{esp if esp else 'N/A'}</span> </div> </div>
                            <div style="margin-top: 12px; width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;"> <div style="width: {prog}%; background: {color}; height: 100%; border-radius: 3px;"></div> </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    if i%3==2: cols = st.columns(3)
                colI, colD = st.columns([2,1])
                with colI:
                    dfP = pd.DataFrame([{"Categoria": DISPLAY_NAMES[c], "Unidades": _safe_int(df[df['CATEGORIA_FINAL']==c]['FUNDAS'].sum() if c=='Fundas' else df[df['CATEGORIA_FINAL']==c]['PRENDAS'].sum())} for c in CATEGORIAS_LIST if df[df['CATEGORIA_FINAL']==c].shape[0] >0])
                    if not dfP.empty:
                        fig = px.pie(dfP, names='Categoria', values='Unidades', title="Distribución por Categoría", color='Categoria', color_discrete_map={DISPLAY_NAMES[k]: COLORS[COLOR_KEYS[k]] for k in CATEGORIAS_LIST})
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                with colD:
                    tot = df['PRENDAS'].sum()+df['FUNDAS'].sum()
                    st.subheader("TOTAL GENERAL")
                    st.markdown(f"<div style='text-align:center;font-size:36px;font-weight:bold;'>{tot:,}</div>", unsafe_allow_html=True)
                    st.metric("PROMEDIO X TRANSFERENCIA", f"{tot/max(df['SECUENCIAL'].nunique(),1):,.0f}")
                    st.metric("CATEGORÍAS ACTIVAS", f"{sum(1 for c in CATEGORIAS_LIST if df[df['CATEGORIA_FINAL']==c].shape[0] >0)}/6")
                    st.metric("% FUNDAS", f"{df['FUNDAS'].sum()/tot*100 if tot else 0:.1f}%")

        # ==================== TAB 3 ====================
        with tab3:
            if 'df_cruce' not in st.session_state or 'df_detalle_enr' not in st.session_state:
                st.info("🔄 Procesa archivos primero.")
            else:
                dfC = st.session_state['df_cruce']
                dfDE = st.session_state['df_detalle_enr']
                st.subheader("🏪 Desglose por Tienda - Peso Relativo")
                catT = st.selectbox("Categoría para peso relativo: ", ['Todas']+CATEGORIAS_LIST, key="tab3_cat_treemap")
                dfF = dfC[dfC['CATEGORIA_FINAL']==catT] if catT!='Todas' else dfC
                if not dfF.empty:
                    tU = dfF.groupby('TIENDA').agg(Prendas=('PRENDAS','sum'), Fundas=('FUNDAS','sum'), Costo=('COSTO_TOTAL','sum')).reset_index()
                    tU['Unidades'] = tU['Prendas']+tU['Fundas']
                    tU = tU.sort_values('Unidades', ascending=False)
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Total Tiendas", len(tU))
                    c2.metric("Total Unidades", f"{tU['Unidades'].sum():,}")
                    c3.metric("Total Costo", f"${tU['Costo'].sum():,.2f}")
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
                            figTop.update_traces(texttemplate='%{text:,}', textposition='outside')
                            figTop.update_layout(template="plotly_dark", height=500)
                            st.plotly_chart(figTop, use_container_width=True)
                        with cb2:
                            st.dataframe(top10.rename(columns={'TIENDA':'Tienda','Unidades':'Total','Prendas':'Prendas','Fundas':'Fundas','Costo':'Costo'}), use_container_width=True, height=500)
                st.markdown("---")
                st.subheader("Detalle por Tienda Individual")
                catS = st.selectbox("Categoría comercial", ['Todas']+CATEGORIAS_LIST, key="tab3_cat")
                tiendas = sorted(dfC[dfC['CATEGORIA_FINAL']==catS]['TIENDA'].unique()) if catS!='Todas' else sorted(dfC['TIENDA'].unique())
                tSel = st.selectbox("Tienda", tiendas, key="tab3_tienda")
                if tSel:
                    transT = dfC[dfC['TIENDA']==tSel]
                    if not transT.empty:
                        st.write(f"### {tSel} ({catS if catS!='Todas' else 'Todas'})")
                        prodT = dfDE[dfDE['SECUENCIAL'].isin(transT['SECUENCIAL'])][['SECUENCIAL','PRODUCTO_BASE','TIPO_PRENDA_ES','COLOR_NORM','TALLA','CANTIDAD','ES_FUNDA','CATEGORIA']].rename(columns={'SECUENCIAL':'Transferencia','PRODUCTO_BASE':'Producto Base','TIPO_PRENDA_ES':'Tipo','COLOR_NORM':'Color','TALLA':'Talla','CANTIDAD':'Cantidad','ES_FUNDA':'Es Funda','CATEGORIA':'Categoría'})
                        cM1,cM2 = st.columns(2)
                        cM1.metric("Prendas", f"{_safe_int(transT['PRENDAS'].sum()):,}")
                        cM2.metric("Fundas", f"{_safe_int(transT['FUNDAS'].sum()):,}")
                        st.markdown("---")
                        st.markdown("#### 📦 Productos agrupados")
                        prodAg = dfDE[dfDE['SECUENCIAL'].isin(transT['SECUENCIAL'])].groupby('PRODUCTO_BASE')['CANTIDAD'].sum().sort_values(ascending=False).reset_index()
                        prodAg.columns = ['Producto Base','Cantidad Total']
                        ca1,ca2 = st.columns([3,2])
                        with ca1: st.dataframe(prodAg, use_container_width=True, height=300)
                        with ca2:
                            if not prodAg.empty:
                                figP = px.bar(prodAg.head(15), x='Cantidad Total', y='Producto Base', orientation='h', text='Cantidad Total', title=f"Top 15 -> {tSel}")
                                figP.update_traces(texttemplate='%{text:,}', textposition='outside')
                                figP.update_layout(template="plotly_dark")
                                st.plotly_chart(figP, use_container_width=True)
                        st.markdown("---")
                        st.dataframe(prodT, use_container_width=True, height=400)

        # ==================== TAB 4 ====================
        with tab4:
            if 'df_detalle_enr' not in st.session_state:
                st.info("🔄 Procesa archivos primero.")
            else:
                det = st.session_state['df_detalle_enr']
                st.subheader("🎽 Análisis Quirúrgico de Productos")
                st.markdown("Desglose por **tipo, talla y color**. *Fundas excluidas.*")
                catA = st.selectbox("Categoría", CATEGORIAS_SIN_FUNDAS, key="tab4_cat_principal")
                detC = det[(det['CATEGORIA_FINAL']==catA) & (~det['ES_FUNDA'])]
                if detC.empty:
                    st.warning(f"⚠️ Sin datos para **{DISPLAY_NAMES.get(catA,catA)}**.")
                else:
                    colorCat = COLORS.get(COLOR_KEYS.get(catA,''),'#64748b')
                    nombreCat = DISPLAY_NAMES.get(catA, catA.upper())
                    st.markdown(f"""<div style="background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); padding: 16px 24px; border-radius: 12px; border-left: 6px solid {colorCat}; margin-bottom: 20px;">
                        <span style="font-size: 18px; font-weight: 700; color: #ffffff;">{nombreCat}</span>
                        <span style="float: right; color: {colorCat}; font-weight: 600;">{detC['TIENDA'].nunique()} tiendas</span>
                    </div>""", unsafe_allow_html=True)
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Ítems únicos", detC['PRODUCTO_BASE'].nunique())
                    c2.metric("Total Unidades", f"{_safe_int(detC['CANTIDAD'].sum()):,}")
                    c3.metric("Tipos de Prenda", detC['TIPO_PRENDA_ES'].nunique())
                    c4.metric("Colores Distintos", detC['COLOR_NORM'].nunique())
                    st.markdown("---")
                    tipoS = detC.groupby('TIPO_PRENDA_ES').agg(Unidades=('CANTIDAD','sum'), Productos=('PRODUCTO_BASE','nunique'), Tiendas=('TIENDA','nunique')).sort_values('Unidades', ascending=False).reset_index()
                    ct1,ct2 = st.columns([2,2])
                    with ct1:
                        figTipo = px.bar(tipoS.head(15), x='Unidades', y='TIPO_PRENDA_ES', orientation='h', text='Unidades', color='Unidades', color_continuous_scale='Viridis')
                        figTipo.update_traces(texttemplate='%{text:,}', textposition='outside')
                        figTipo.update_layout(template="plotly_dark", height=500)
                        st.plotly_chart(figTipo, use_container_width=True)
                    with ct2: st.dataframe(tipoS.style.background_gradient(subset=['Unidades'], cmap='Blues'), use_container_width=True, height=500)
                    st.markdown("---")
                    st.markdown("#### 📏 Por **Tallas**")
                    tOrder = ['XS','S','M','L','XL','XXL','ÚNICA','XSMALL','SMALL','MEDIUM','LARGE']
                    detCT = detC.copy()
                    detCT['TALLA_FINAL'] = pd.Categorical(detCT['TALLA'], categories=tOrder, ordered=True)
                    tallaS = detCT.groupby('TALLA_FINAL').agg(Unidades=('CANTIDAD','sum'), Productos=('PRODUCTO_BASE','nunique')).reset_index()
                    tallaS['% Total'] = (tallaS['Unidades']/tallaS['Unidades'].sum()*100).round(1)
                    ct1,ct2 = st.columns(2)
                    with ct1:
                        figTalla = px.bar(tallaS, x='TALLA_FINAL', y='Unidades', text='Unidades', color='Unidades', color_continuous_scale='Plasma')
                        figTalla.update_traces(texttemplate='%{text:,}', textposition='outside')
                        figTalla.update_layout(template="plotly_dark")
                        st.plotly_chart(figTalla, use_container_width=True)
                    with ct2: st.dataframe(tallaS.style.background_gradient(subset=['Unidades'], cmap='Greens'), use_container_width=True, height=400)
                    figLine = px.line(tallaS, x='TALLA_FINAL', y='Unidades', markers=True, title="Curva de Tallas")
                    figLine.update_layout(template="plotly_dark")
                    st.plotly_chart(figLine, use_container_width=True)
                    st.markdown("---")
                    st.markdown("#### 🎨 Por **Colores**")
                    colorS = detC.groupby('COLOR_NORM').agg(Unidades=('CANTIDAD','sum'), Productos=('PRODUCTO_BASE','nunique')).sort_values('Unidades', ascending=False).reset_index()
                    cc1,cc2 = st.columns(2)
                    with cc1:
                        figColor = px.bar(colorS.head(15), x='Unidades', y='COLOR_NORM', orientation='h', text='Unidades', color='Unidades', color_continuous_scale='Rainbow')
                        figColor.update_traces(texttemplate='%{text:,}', textposition='outside')
                        figColor.update_layout(template="plotly_dark", height=500)
                        st.plotly_chart(figColor, use_container_width=True)
                    with cc2: st.dataframe(colorS.head(20).style.background_gradient(subset=['Unidades'], cmap='Reds'), use_container_width=True, height=500)
                    with st.expander("📋 Detalle completo"):
                        colsShow = ['TIENDA','PRODUCTO_BASE','COLOR_NORM','TALLA','TIPO_PRENDA_ES','CANTIDAD','COSTO']
                        st.dataframe(detC[colsShow], use_container_width=True)
                        csv = detC[colsShow].to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Exportar CSV", csv, f"productos_{catA.lower().replace(' ','_')}.csv", "text/csv")

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
            st.markdown("**⚡ Presets:**")
            pCols = st.columns(len(DATE_PRESETS))
            for idx,(lab,d) in enumerate(DATE_PRESETS.items()):
                if pCols[idx].button(lab, key=f"pre_{lab}", use_container_width=True):
                    st.session_state.hist_inicio = date.today()-timedelta(days=d)
                    st.session_state.hist_fin = date.today()
                    st.session_state.hist_regs = None
                    st.session_state.hist_periodo_sel = "Día"
            st.markdown("---")
            c1,c2,c3 = st.columns([2,1,1])
            with c1:
                periodo_options = ["Día", "Semana", "Mes"]
                periodo_default = st.session_state.hist_periodo_sel if st.session_state.hist_periodo_sel in periodo_options else "Día"
                periodo = st.selectbox("Agrupar", periodo_options, key="hist_periodo", index=periodo_options.index(periodo_default))
            with c2: inicio = st.date_input("Desde", value=st.session_state.hist_inicio, key="hist_ini")
            with c3: fin = st.date_input("Hasta", value=st.session_state.hist_fin, key="hist_fin")
            if inicio > fin: st.error("⚠️ 'Desde' no puede ser posterior a 'Hasta'.")
            else:
                if st.button("🔍 Consultar histórico", use_container_width=True, type="primary", key="btn_consultar"):
                    st.session_state.hist_inicio = inicio
                    st.session_state.hist_fin = fin
                    st.session_state.hist_periodo_sel = periodo
                    st.session_state.hist_regs = None
                    try:
                        with st.spinner("Consultando base de datos..."):
                            regs = consultar_historico("dashboard_logistico", "Transferencias Diarias", inicio, fin)
                            regs = [_sanitize_metrics(r) for r in (regs or [])]
                    except Exception as e: st.error(f"❌ Error DB: {e}"); regs = []
                    if not regs: st.warning("⚠️ Sin datos. Procesa archivos en Tab 1.")
                    else: st.session_state.hist_regs = regs; st.success(f"✅ {len(regs)} registros encontrados")
            regs = st.session_state.get('hist_regs', None)
            pUsado = st.session_state.get('hist_periodo_sel', "Día")
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
                            ca1,ca2 = st.columns([3,1])
                            with ca1:
                                figAc = go.Figure(go.Scatter(x=daily['fecha'], y=daily['acum'], mode='lines+markers', fill='tozeroy', fillcolor='rgba(59,130,246,0.15)', line=dict(color='#3b82f6',width=3)))
                                figAc.update_layout(template="plotly_dark", title="Acumulado Histórico", height=400)
                                st.plotly_chart(figAc, use_container_width=True)
                            with ca2:
                                st.metric("Total", f"{daily['und'].sum():,.0f}")
                                st.metric("Días", daily['fecha'].nunique())
                                st.metric("Promedio/Día", f"{daily['und'].sum()/max(daily['fecha'].nunique(),1):,.0f}")
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
                        if pUsado=="Semana": dfH['per'] = dfH['fecha'].apply(lambda d: d-timedelta(days=d.weekday()))
                        elif pUsado=="Mes": dfH['per'] = dfH['fecha'].apply(lambda d: d.replace(day=1))
                        else: dfH['per'] = dfH['fecha']
                        agg = dfH.groupby('per')['und'].sum().reset_index().rename(columns={'per':'periodo'})
                        st.markdown(f"**{inicio.strftime('%d/%m/%Y')} – {fin.strftime('%d/%m/%Y')}**")
                        figD = px.bar(agg, x='periodo', y='und', text='und', title=f"Despachos por {pUsado}")
                        figD.update_traces(texttemplate='%{text:,}', textposition='outside', marker_color='#f59e0b')
                        figD.update_layout(template="plotly_dark")
                        st.plotly_chart(figD, use_container_width=True)
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("Total", f"{agg['und'].sum():,.0f}")
                        m2.metric("Promedio", f"{agg['und'].mean():,.0f}")
                        m3.metric("Máximo", f"{agg['und'].max():,.0f}")
                        m4.metric("Registros", len(agg))
                        st.dataframe(agg.rename(columns={'periodo':'Período','und':'Unidades'}), use_container_width=True)
                        st.markdown("---")
                        st.subheader("KPIs por Categoría")
                        cAgg = {c:0 for c in CATEGORIAS_LIST}
                        tP=tF=tU=rSin = 0
                        for _,row in dfH.iterrows():
                            met = row.get('met',{})
                            if not isinstance(met,dict): rSin+=1; continue
                            pc = met.get('por_categoria',{})
                            if not isinstance(pc,dict) or not pc: rSin+=1
                            else:
                                for c in CATEGORIAS_LIST:
                                    try: cAgg[c] += _safe_numeric(pc.get(c,0))
                                    except: pass
                            tP += _safe_numeric(met.get('total_prendas',0))
                            tF += _safe_numeric(met.get('total_fundas',0))
                            tU += _safe_numeric(met.get('total_unidades',0))
                        if rSin >0: st.warning(f"⚠️ {rSin} registros sin desglose.")
                        m1,m2,m3,m4 = st.columns(4)
                        m1.metric("📦 Unidades", f"{tU:,.0f}")
                        m2.metric("🎽 Prendas", f"{tP:,.0f}")
                        m3.metric("🛍️ Fundas", f"{tF:,.0f}")
                        m4.metric("📅 Días", dfH['fecha'].nunique())
                        st.markdown("##### Detalle")
                        _render_kpi_cards_historico(cAgg, tU)
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
                                    st.metric(f"Mes {ms[1]} vs {ms[0]}", f"{act:,.0f}", delta=f"{'▲' if delta >=0 else '▼'} {abs(delta):.1f}%", delta_color="normal" if delta >=0 else "inverse")
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

        # ==================== TAB 6 ====================
        with tab6:
            st.subheader("🤖 Asistente IA")
            if 'chat_history' not in st.session_state: st.session_state.chat_history = []
            modo = st.radio("Entrada", ["⌨️ Texto", "🎙️ Voz"], key="radio_ia")
            if modo=="🎙️ Voz":
                ab = st.audio_input("Habla tu pregunta", key="audio_input")
                if ab:
                    with st.spinner("Transcribiendo..."):
                        preg = transcribir_audio(ab.read())
                        if preg:
                            st.session_state.chat_history.append({"role": "user", "content":preg})
                            with st.spinner("Analizando..."):
                                resp = _responder_ia(preg, st.session_state.get('df_cruce'), st.session_state.get('df_detalle_enr'), []) if 'df_cruce' in st.session_state else "Carga archivos primero."
                            st.session_state.chat_history.append({"role": "assistant", "content":resp})
            else:
                preg = st.text_input("Escribe tu pregunta: ", key="text_input_ia")
                if preg:
                    st.session_state.chat_history.append({"role": "user", "content":preg})
                    with st.spinner("Analizando..."):
                        resp = _responder_ia(preg, st.session_state.get('df_cruce'), st.session_state.get('df_detalle_enr'), []) if 'df_cruce' in st.session_state else "Carga archivos primero."
                    st.session_state.chat_history.append({"role": "assistant", "content":resp})
            if st.session_state.chat_history:
                with st.expander("📜 Historial"):
                    for m in st.session_state.chat_history:
                        st.markdown(f"**🧑 Usuario:** {m['content']}" if m['role']=='user' else f"**🤖 Asistente:** {m['content']}")

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
