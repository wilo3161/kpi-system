# modules/dashboard_kpis.py
# ============================================================================
# DASHBOARD KPIS - MÓDULO UNIFICADO DE INDICADORES, ANALYTICS Y PREDICCIONES
# Integra KPI Analytics, motor de KPIs en tiempo real y machine learning.
# Versión robustecida con manejo de errores, logging y caché.
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from database.manager import local_db
from core.kpi_engine import KPIEngine
from modules.main_page import show_module_header
from utils.ui import add_back_button, apply_plotly_theme
from utils.backgrounds import set_module_background
from ai.supply_chain_ai import _ejecutar_prompt

logger = logging.getLogger(__name__)

# Intentar importar sklearn para predicciones
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn no disponible para predicciones")

# =============================================================================
# FUNCIONES AUXILIARES PARA KPI ANALYTICS
# =============================================================================
def kpi_color(val, meta, invert=False):
    ok = val >= meta if not invert else val <= meta
    return "#10b981" if ok else ("#f59e0b" if abs(val - meta) < 10 else "#ef4444")

def kpi_card(col, titulo, valor, meta, unidad="%", formula="", frecuencia=""):
    color = kpi_color(valor, meta)
    delta = valor - meta
    col.markdown(f"""
    <div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-left:4px solid {color};border-radius:10px;padding:16px;margin-bottom:10px;'>
        <div style='font-size:.75em;color:#94a3b8;margin-bottom:4px;'>{frecuencia}</div>
        <div style='font-weight:700;color:#e2e8f0;font-size:1em;margin-bottom:8px;'>{titulo}</div>
        <div style='font-size:2em;font-weight:800;color:{color};'>{valor:.1f}{unidad}</div>
        <div style='font-size:.75em;color:#94a3b8;margin-top:4px;'>
            Meta: {meta}{unidad} &nbsp;|&nbsp;
            <span style="color:{'#10b981' if delta>=0 else '#ef4444'}">
                {"▲" if delta>=0 else "▼"} {abs(delta):.1f}{unidad}
            </span>
        </div>
        {f"<div style='font-size:.7em;color:#64748b;margin-top:6px;font-style:italic;'>{formula}</div>" if formula else ""}
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# PREDICCIÓN CON RANDOM FOREST
# =============================================================================
def entrenar_modelo_prediccion():
    if not SKLEARN_AVAILABLE:
        return None, None, "scikit-learn no instalado"

    try:
        historicos = local_db.find("historico", {"modulo": "dashboard_logistico"}, sort=[("fecha_archivo", -1)], limit=90)
        if not historicos:
            return None, None, "No hay datos históricos. Carga archivos en el Dashboard Logístico primero."

        registros = []
        for h in historicos:
            met = h.get("metricas", {})
            if "total_unidades" in met:
                registros.append({"fecha": pd.to_datetime(h.get("fecha_archivo")), "unidades": met["total_unidades"]})

        if len(registros) < 14:
            return None, None, "Se necesitan al menos 14 días de datos históricos."

        df = pd.DataFrame(registros).sort_values("fecha").drop_duplicates("fecha")
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['semana'] = df['fecha'].dt.isocalendar().week.astype(int)
        df['mes'] = df['fecha'].dt.month
        df['lag_7'] = df['unidades'].shift(7)
        df['lag_14'] = df['unidades'].shift(14)
        df['rolling_mean_7'] = df['unidades'].rolling(7).mean()
        df = df.dropna()

        if len(df) < 14:
            return None, None, "Datos insuficientes después de limpieza."

        X = df[['dia_semana', 'semana', 'mes', 'lag_7', 'lag_14', 'rolling_mean_7']]
        y = df['unidades']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        return model, df.iloc[-1], mae
    except Exception as e:
        logger.error(f"Error en modelo de predicción: {e}")
        return None, None, str(e)

def predecir_proximos_7_dias(model, last_row, start_date):
    try:
        preds = []
        current_date = start_date
        last_units = last_row['unidades']
        last_lag7 = last_row.get('lag_7', last_units)
        last_lag14 = last_row.get('lag_14', last_units)
        last_roll7 = last_row.get('rolling_mean_7', last_units)

        for i in range(7):
            features = {
                'dia_semana': current_date.dayofweek,
                'semana': current_date.isocalendar().week,
                'mes': current_date.month,
                'lag_7': last_lag7,
                'lag_14': last_lag14,
                'rolling_mean_7': last_roll7,
            }
            X = pd.DataFrame([features])
            y_pred = model.predict(X)[0]
            y_pred_int = max(0, int(y_pred))
            preds.append({"fecha": current_date, "prediccion": y_pred_int})
            # Actualizar lags para el siguiente día
            last_lag14 = last_lag7
            last_lag7 = y_pred_int
            if i >= 6:
                last_roll7 = np.mean([p["prediccion"] for p in preds[-7:]])
            else:
                last_roll7 = (last_roll7 * 7 + y_pred_int - last_row['unidades']) / 7
            current_date += timedelta(days=1)

        return pd.DataFrame(preds)
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return pd.DataFrame()

# =============================================================================
# INTERFAZ PRINCIPAL UNIFICADA
# =============================================================================
def show_dashboard_kpis():
    try:
        add_back_button(key="back_dashboard_kpis")
        show_module_header("📊 Dashboard KPIs", "Indicadores clave de rendimiento y predicciones")
        set_module_background("dashboard_kpis")

        from utils.ui import inject_acumatica_css, acu_metric
        inject_acumatica_css()
        st.markdown('<div class="module-content">', unsafe_allow_html=True)

        # Inicializar motor de KPIs
        kpi_engine = KPIEngine()

        # Pestañas: Resumen Ejecutivo, KPI Analytics, Predicciones ML
        tab1, tab2, tab3 = st.tabs(["📈 Resumen Ejecutivo", "⚙️ KPI Analytics", "🔮 Predicciones ML"])

        # ==================== TAB 1: RESUMEN EJECUTIVO (desde kpi_engine) ====================
        with tab1:
            st.subheader("KPIs en Tiempo Real")
            col1, col2, col3, col4 = st.columns(4)
            try:
                otif = kpi_engine.otif(30)
                tiempo_prom = kpi_engine.tiempo_promedio_recepcion(30)
                tasa_faltantes = kpi_engine.tasa_faltantes(30)
                recepciones_hoy = kpi_engine.recepciones_hoy()

                col1.markdown(acu_metric("OTIF 30 días", f"{otif:.1f}%", color="blue", icon="🎯"), unsafe_allow_html=True)
                col2.markdown(acu_metric("Tiempo prom. recepción", f"{tiempo_prom} hrs", color="yellow", icon="⏱️"), unsafe_allow_html=True)
                col3.markdown(acu_metric("Tasa faltantes 30d", f"{tasa_faltantes:.1f}%", color="red", icon="📉"), unsafe_allow_html=True)
                col4.markdown(acu_metric("Recepciones hoy", recepciones_hoy, color="green", icon="📦"), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error cargando KPIs: {e}")
                logger.exception(e)

            st.divider()
            st.subheader("🌐 Visión Global del ERP (Logística y Finanzas)")
            try:
                # LOGISTICA
                guias_activas = local_db.count("guias", {"anulada": False, "estado": {"$ne": "CERRADA"}})
                guias_recibidas = local_db.count("guias", {"anulada": False, "estado": {"$in": ["RECIBIDA_CONFORME", "RECIBIDA_CON_NOVEDAD", "CONCILIADA"]}})
                
                # FINANZAS / RECONCILIACION
                facturas_conciliadas = local_db.count("reconciliacion", {"estado": "CONCILIADA"})
                
                c_log1, c_log2, c_fin1 = st.columns(3)
                c_log1.markdown(acu_metric("Guías Activas/Tránsito", guias_activas, color="blue", icon="🚚"), unsafe_allow_html=True)
                c_log2.markdown(acu_metric("Guías Recibidas", guias_recibidas, color="green", icon="📦"), unsafe_allow_html=True)
                c_fin1.markdown(acu_metric("Facturas Conciliadas", facturas_conciliadas, color="yellow", icon="💰"), unsafe_allow_html=True)
            except Exception as e:
                logger.error(f"Error cargando visión global: {e}")

            st.divider()
            st.subheader("Distribución de incidencias (últimos 30 días)")
            try:
                incidencias = kpi_engine.distribucion_incidencias(30)
                if incidencias:
                    df_inc = pd.DataFrame(incidencias)
                    fig = px.pie(df_inc, values='count', names='_id', title="Incidencias por tipo")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay incidencias en el período.")
            except Exception as e:
                logger.error(f"Error en gráfico de incidencias: {e}")

            st.subheader("Top 10 tiendas con más incidencias")
            try:
                top_tiendas = kpi_engine.top_tiendas_incidencias(30, 10)
                if top_tiendas:
                    df_top = pd.DataFrame(top_tiendas)
                    fig = px.bar(df_top, x='count', y='_id', orientation='h', title="Tiendas con más incidencias")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sin datos de incidencias.")
            except Exception as e:
                logger.error(f"Error en top tiendas: {e}")

        # ==================== TAB 2: KPI ANALYTICS (entrada manual y desde histórico) ====================
        with tab2:
            st.subheader("📊 KPI Analytics - Indicadores detallados")

            # Sección: KPIs de Salidas y Despachos (entrada manual)
            st.markdown("### 🚚 KPIs de Salidas y Despachos")
            with st.form("form_despachos"):
                col_a, col_b, col_c = st.columns(3)
                pedidos_desp_correctos = col_a.number_input("Pedidos despachados correctamente", min_value=0, value=st.session_state.get("kpi_ped_desp_ok", 0))
                total_pedidos = col_b.number_input("Total pedidos del período", min_value=1, value=st.session_state.get("kpi_total_ped", 1))
                meta_exactitud = col_c.number_input("Meta Exactitud de Despacho (%)", min_value=0, max_value=100, value=95)
                col_d, col_e, col_f = st.columns(3)
                pedidos_otif = col_d.number_input("Pedidos entregados a tiempo y completos (OTIF)", min_value=0, value=st.session_state.get("kpi_otif_ok", 0))
                meta_otif = col_e.number_input("Meta OTIF (%)", min_value=0, max_value=100, value=95)
                col_g, col_h, col_i = st.columns(3)
                cant_transferida = col_g.number_input("Cantidad transferida hoy (unidades)", min_value=0, value=st.session_state.get("kpi_cant_transf", 0))
                meta_diaria = col_h.number_input("Meta diaria (unidades)", min_value=1, value=st.session_state.get("kpi_meta_diaria", 1000))
                calcular = st.form_submit_button("📊 Calcular KPIs", use_container_width=True, type="primary")

            if calcular or st.session_state.get("kpi_despachos_calculados"):
                if calcular:
                    st.session_state.kpi_ped_desp_ok = pedidos_desp_correctos
                    st.session_state.kpi_total_ped = total_pedidos
                    st.session_state.kpi_otif_ok = pedidos_otif
                    st.session_state.kpi_cant_transf = cant_transferida
                    st.session_state.kpi_meta_diaria = meta_diaria
                    st.session_state.kpi_despachos_calculados = True

                exactitud_desp = (st.session_state.kpi_ped_desp_ok / max(st.session_state.kpi_total_ped, 1)) * 100
                otif = (st.session_state.kpi_otif_ok / max(st.session_state.kpi_total_ped, 1)) * 100
                cumpl_meta = (st.session_state.kpi_cant_transf / max(st.session_state.kpi_meta_diaria, 1)) * 100

                c1, c2, c3 = st.columns(3)
                kpi_card(c1, "Exactitud de Despacho", exactitud_desp, meta_exactitud, formula="Pedidos correctos / Total × 100", frecuencia="📅 Semanal")
                kpi_card(c2, "OTIF", otif, meta_otif, formula="Pedidos a tiempo y completos / Total × 100", frecuencia="📅 Semanal")
                kpi_card(c3, "Cumplimiento Meta Diaria", cumpl_meta, 100, formula="Cantidad transferida / Meta diaria × 100", frecuencia="📅 Diario")

                # Guardar en BD (histórico de KPIs)
                try:
                    local_db.insert("kpi_analytics", {
                        "fecha": datetime.utcnow(),
                        "proceso": "Salidas y Despachos",
                        "kpis": {"exactitud_despacho": round(exactitud_desp,2), "otif": round(otif,2), "cumplimiento_meta_diaria": round(cumpl_meta,2)},
                        "usuario": st.session_state.get("username", "admin")
                    })
                    st.success("✅ KPIs guardados")
                except Exception as e:
                    logger.error(f"Error guardando KPIs: {e}")

            # Sección: KPIs desde histórico logístico
            st.markdown("---")
            st.subheader("📊 KPIs desde Histórico Logístico")
            hist = local_db.find("historico", {}, sort=[("fecha_archivo", -1)], limit=60)
            if hist:
                df_hist = pd.DataFrame(hist)
                df_hist["fecha"] = pd.to_datetime(df_hist.get("fecha_archivo", pd.NaT), errors="coerce")
                df_hist = df_hist.dropna(subset=["fecha"])
                if "metricas" in df_hist.columns:
                    met_exp = pd.json_normalize(df_hist["metricas"].fillna({}).tolist())
                    df_hist = pd.concat([df_hist.drop("metricas", axis=1).reset_index(drop=True), met_exp.reset_index(drop=True)], axis=1)

                meta_dia = st.number_input("Meta diaria (unidades)", value=1000, min_value=1, key="meta_historico")
                total_u = int(df_hist["total_unidades"].sum()) if "total_unidades" in df_hist.columns else 0
                dias = len(df_hist)
                prom = total_u / max(dias, 1)
                cumpl = (prom / meta_dia) * 100

                ck1, ck2, ck3 = st.columns(3)
                kpi_card(ck1, "Total unidades periodo", total_u, 0, unidad=" uds", frecuencia="Periodo")
                kpi_card(ck2, "Promedio diario", round(prom, 1), meta_dia, unidad=" uds", frecuencia="Diario")
                kpi_card(ck3, "Cumplimiento meta", round(cumpl, 1), 100, frecuencia="Diario")

                if "total_unidades" in df_hist.columns:
                    fig = px.bar(df_hist, x="fecha", y="total_unidades", title="Unidades despachadas por día")
                    fig.add_hline(y=meta_dia, line_dash="dash", line_color="#ef4444", annotation_text="Meta")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

                if st.button("Guardar KPIs en histórico", type="primary"):
                    try:
                        local_db.insert("kpi_analytics", {
                            "fecha": datetime.utcnow(),
                            "proceso": "Automatico-Historico",
                            "kpis": {"total_unidades": total_u, "promedio_diario": round(prom, 2), "cumplimiento_meta": round(cumpl, 2)},
                            "usuario": st.session_state.get("username", "admin")
                        })
                        st.success("KPIs guardados")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("Carga archivos en el Dashboard Logístico primero.")

        # ==================== TAB 3: PREDICCIONES ML ====================
        with tab3:
            st.subheader("🔮 Predicción de unidades para los próximos 7 días")
            if not SKLEARN_AVAILABLE:
                st.error("La librería scikit-learn no está instalada. Agrega 'scikit-learn' a requirements.txt.")
            else:
                if st.button("Entrenar modelo y predecir", type="primary"):
                    with st.spinner("Entrenando modelo..."):
                        model, last_row, mae = entrenar_modelo_prediccion()
                        if model is None:
                            st.warning(mae)
                        else:
                            start_date = datetime.now().date()
                            df_pred = predecir_proximos_7_dias(model, last_row, start_date)
                            if not df_pred.empty:
                                st.session_state['df_pred'] = df_pred
                                st.session_state['mae_pred'] = mae
                                st.success(f"Modelo entrenado. Error absoluto medio (MAE): {mae:.2f} unidades.")
                            else:
                                st.error("No se pudo generar la predicción.")

                if 'df_pred' in st.session_state:
                    df_pred = st.session_state['df_pred']
                    fig = px.bar(df_pred, x='fecha', y='prediccion',
                                 title="Predicción de unidades por día",
                                 labels={'prediccion':'Unidades predichas','fecha':'Fecha'},
                                 color='prediccion', color_continuous_scale='Blues')
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

                    df_pred_display = df_pred.copy()
                    df_pred_display['fecha_str'] = df_pred_display['fecha'].dt.strftime('%A %d/%m/%Y')
                    st.dataframe(df_pred_display[['fecha_str','prediccion']].rename(columns={'fecha_str':'Fecha','prediccion':'Unidades'}),
                                 use_container_width=True)
                    total_semana = df_pred['prediccion'].sum()
                    dia_pico = df_pred.loc[df_pred['prediccion'].idxmax()]
                    st.markdown(acu_metric("Total proyectado semana", f"{total_semana:,}", color="blue", icon="📊"), unsafe_allow_html=True)
                    st.info(f"📌 Día pico: **{dia_pico['fecha'].strftime('%A %d/%m')}** con **{dia_pico['prediccion']:,}** unidades.")

        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error general en Dashboard KPIs: {e}")
        logger.exception(e)
