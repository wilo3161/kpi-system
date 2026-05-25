import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.manager import local_db
from modules.main_page import show_module_header
from utils.helpers import add_back_button


# =============================================================================
# PREDICCIÓN (sklearn se importa solo cuando se usa)
# =============================================================================
def entrenar_modelo_prediccion():
    import sklearn
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error

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


def predecir_proximos_7_dias(model, last_row, start_date):
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
        last_lag14 = last_lag7
        last_lag7 = y_pred_int
        if i >= 6:
            last_roll7 = np.mean([p["prediccion"] for p in preds[-7:]])
        else:
            last_roll7 = (last_roll7 * 7 + y_pred_int - last_row['unidades']) / 7
        current_date += timedelta(days=1)

    return pd.DataFrame(preds)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_kpi_analytics():
    add_back_button(key="back_kpi")
    from utils.ui import inject_acumatica_css, acu_metric
    inject_acumatica_css()
    show_module_header("📊 KPI Analytics", "Indicadores clave de rendimiento operacional")

    def kpi_color(val, meta, invert=False):
        ok = val >= meta if not invert else val <= meta
        return "#10b981" if ok else ("#f59e0b" if abs(val - meta) < 10 else "#ef4444")

    def kpi_card(col, titulo, valor, meta, unidad="%", formula="", frecuencia=""):
        color = kpi_color(valor, meta)
        delta = valor - meta
        bg_class = "acu-bg-green" if color == "#10b981" else ("acu-bg-yellow" if color == "#f59e0b" else "acu-bg-red")
        icon = "✅" if color == "#10b981" else ("⚠️" if color == "#f59e0b" else "🚨")
        
        col.markdown(f"""
        <div class="acu-kpi-card {bg_class}">
            <div class="acu-kpi-icon">{icon}</div>
            <div class="acu-kpi-data" style="align-items: flex-end;">
                <span class="acu-kpi-number">{valor:.1f}{unidad}</span>
                <span class="acu-kpi-label">{titulo}</span>
                <span style="font-size: 0.7em; margin-top: 4px; opacity: 0.85;">Meta: {meta}{unidad} | Dif: {delta:+.1f}{unidad}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🚚 Salidas y Despachos",
        "📦 Recepciones e Inventario",
        "✂️ Calidad y Reproceso",
        "📈 Resumen Ejecutivo",
        "📊 Desde Histórico",
        "🔮 Predicción de Demanda",
        "📦 Análisis ABC"
    ])

    # ==================== TAB 1 (Original) ====================
    with tab1:
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
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Exactitud de Despacho", exactitud_desp, meta_exactitud, formula="Pedidos correctos / Total pedidos × 100", frecuencia="📅 Semanal")
            kpi_card(c2, "OTIF (On Time In Full)", otif, meta_otif, formula="Pedidos a tiempo y completos / Total × 100", frecuencia="📅 Semanal")
            kpi_card(c3, "Cumplimiento Meta Diaria", cumpl_meta, 100, formula="Cantidad transferida / Meta diaria × 100", frecuencia="📅 Diario")
            if calcular:
                local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Salidas y Despachos", "kpis": {"exactitud_despacho": round(exactitud_desp,2), "otif": round(otif,2), "cumplimiento_meta_diaria": round(cumpl_meta,2)}, "usuario": st.session_state.get("username","admin")})
                st.success("✅ KPIs guardados en el histórico")

    # ==================== TAB 2 (Original) ====================
    with tab2:
        st.markdown("### 📦 KPIs de Recepciones y Control de Inventario")
        with st.form("form_inventario"):
            st.markdown("**Exactitud de Recepción**")
            col_a, col_b = st.columns(2)
            ped_recibidos_ok = col_a.number_input("Pedidos recibidos correctamente", min_value=0, value=0)
            total_esperados  = col_b.number_input("Total artículos esperados", min_value=1, value=1)
            st.markdown("**ERI — Exactitud de Registro de Inventario**")
            col_c, col_d = st.columns(2)
            stock_contado   = col_c.number_input("Stock contado (físico)", min_value=0, value=0)
            stock_registrado= col_d.number_input("Stock registrado en sistema", min_value=1, value=1)
            st.markdown("**Nivel de Pérdida sobre Ventas**")
            col_e, col_f = st.columns(2)
            num_faltantes   = col_e.number_input("Número de artículos faltantes", min_value=0, value=0)
            ventas_periodo  = col_f.number_input("Ventas del período (unidades)", min_value=1, value=1)
            st.markdown("**Índice de Recuperación de Faltantes**")
            col_g, col_h = st.columns(2)
            cant_recuperada = col_g.number_input("Cantidad recuperada", min_value=0, value=0)
            total_faltantes = col_h.number_input("Total de faltantes detectados", min_value=1, value=1)
            st.markdown("**Ajustes Manuales**")
            col_i, col_j = st.columns(2)
            ajustes_manuales     = col_i.number_input("Frecuencia de ajustes manuales", min_value=0, value=0)
            total_transferencias = col_j.number_input("Total transferencias de inventario", min_value=1, value=1)
            calcular2 = st.form_submit_button("📊 Calcular KPIs de Inventario", use_container_width=True, type="primary")
        if calcular2:
            exactitud_recepcion = (ped_recibidos_ok / max(total_esperados,1)) * 100
            eri = (stock_contado / max(stock_registrado,1)) * 100
            perdida_ventas = (num_faltantes / max(ventas_periodo,1)) * 100
            idx_recuperacion = (cant_recuperada / max(total_faltantes,1)) * 100
            frec_ajustes = (ajustes_manuales / max(total_transferencias,1)) * 100
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Exactitud de Recepción", exactitud_recepcion, 98, formula="Pedidos correctos / Total esperados × 100", frecuencia="📅 Mensual")
            kpi_card(c2, "ERI (Exactitud de Inventario)", eri, 98, formula="Stock contado / Stock sistema × 100", frecuencia="📅 Semanal")
            kpi_card(c3, "Nivel de Pérdida sobre Ventas", perdida_ventas, 2, formula="N° faltantes / Ventas período × 100", frecuencia="📅 Mensual", invert=True)
            c4, c5 = st.columns(2)
            kpi_card(c4, "Índice de Recuperación de Faltantes", idx_recuperacion, 80, formula="Cant. recuperada / Total faltantes × 100", frecuencia="📅 Trimestral")
            kpi_card(c5, "Frecuencia de Ajustes Manuales", frec_ajustes, 5, formula="Ajustes manuales / Total transferencias × 100", frecuencia="📅 Mensual")
            local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Inventario", "kpis": {"exactitud_recepcion": round(exactitud_recepcion,2), "eri": round(eri,2), "perdida_ventas": round(perdida_ventas,2), "recuperacion_faltantes": round(idx_recuperacion,2), "ajustes_manuales": round(frec_ajustes,2)}, "usuario": st.session_state.get("username","admin")})
            st.success("✅ KPIs de inventario guardados")

    # ==================== TAB 3 (Original) ====================
    with tab3:
        st.markdown("### ✂️ KPIs de Control de Calidad y Reproceso")
        with st.form("form_calidad"):
            col_a, col_b = st.columns(2)
            fallas_recuperadas = col_a.number_input("Fallas recuperadas por categoría", min_value=0, value=0)
            total_fallas       = col_b.number_input("Total fallas recibidas", min_value=1, value=1)
            col_c, col_d = st.columns(2)
            stock_bod_contado = col_c.number_input("Stock contado (inventario anual)", min_value=0, value=0)
            stock_bod_sistema = col_d.number_input("Stock en sistema (inventario anual)", min_value=1, value=1)
            calcular3 = st.form_submit_button("📊 Calcular KPIs de Calidad", use_container_width=True, type="primary")
        if calcular3:
            control_reproceso = (fallas_recuperadas / max(total_fallas,1)) * 100
            eri_bodega = (stock_bod_contado / max(stock_bod_sistema,1)) * 100
            st.markdown("---")
            c1, c2 = st.columns(2)
            kpi_card(c1, "Control de Reproceso", control_reproceso, 85, formula="Fallas recuperadas / Total fallas × 100", frecuencia="📅 Mensual")
            kpi_card(c2, "Gestión de Bodega (ERI)", eri_bodega, 98, formula="Stock contado / Stock sistema × 100", frecuencia="📅 Anual")
            local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Calidad", "kpis": {"control_reproceso": round(control_reproceso,2), "eri_bodega": round(eri_bodega,2)}, "usuario": st.session_state.get("username","admin")})
            st.success("✅ KPIs de calidad guardados")

    # ==================== TAB 4 (Original) ====================
    with tab4:
        st.markdown("### 📈 Historial de KPIs Registrados")
        hist_kpi = local_db.find("kpi_analytics", sort=[("fecha", -1)], limit=50)
        if not hist_kpi:
            st.info("Aún no hay KPIs calculados. Usa las pestañas anteriores para ingresar datos.")
        else:
            rows = []
            for rec in hist_kpi:
                fecha = rec.get("fecha", "")
                proceso = rec.get("proceso", "")
                for k, v in rec.get("kpis", {}).items():
                    rows.append({"Fecha": str(fecha)[:10], "Proceso": proceso, "KPI": k.replace("_"," ").title(), "Valor": v})
            if rows:
                df_kpi = pd.DataFrame(rows)
                st.dataframe(df_kpi, use_container_width=True, height=300)
                if len(df_kpi) > 0:
                    fig = go.Figure()
                    for proceso in df_kpi["Proceso"].unique():
                        df_p = df_kpi[df_kpi["Proceso"] == proceso]
                        fig.add_trace(go.Bar(name=proceso, x=df_p["KPI"], y=df_p["Valor"], text=df_p["Valor"].round(1), textposition="auto"))
                    fig.update_layout(title="KPIs por Proceso", paper_bgcolor="#0f172a", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0"), barmode="group", height=400, xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155", range=[0,110]))
                    st.plotly_chart(fig, use_container_width=True)

    # ==================== TAB 5 (Original) ====================
    with tab5:
        st.markdown("### Cálculo automático desde histórico logístico")
        hist = local_db.find("historico", {}, sort=[("fecha_archivo", -1)], limit=60)
        if not hist:
            st.info("Sin datos en histórico. Carga archivos en Dashboard Logístico primero.")
        else:
            df_hist = pd.DataFrame(hist)
            df_hist["fecha"] = pd.to_datetime(df_hist.get("fecha_archivo", pd.NaT), errors="coerce")
            df_hist = df_hist.dropna(subset=["fecha"])
            if "metricas" in df_hist.columns:
                met_exp = pd.json_normalize(df_hist["metricas"].fillna({}).tolist())
                df_hist = pd.concat([df_hist.drop("metricas", axis=1).reset_index(drop=True), met_exp.reset_index(drop=True)], axis=1)
            col_a, col_b = st.columns(2)
            meta_dia = col_a.number_input("Meta diaria (unidades)", value=1000, min_value=1)
            total_u = int(df_hist["total_unidades"].sum()) if "total_unidades" in df_hist.columns else 0
            dias    = len(df_hist)
            prom    = total_u / max(dias, 1)
            cumpl   = (prom / meta_dia) * 100
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Total unidades periodo", total_u, 0, unidad=" uds", frecuencia="Periodo seleccionado")
            kpi_card(c2, "Promedio diario", round(prom, 1), meta_dia, unidad=" uds", frecuencia="Diario")
            kpi_card(c3, "Cumplimiento meta", round(cumpl, 1), 100, frecuencia="Diario")
            if "total_unidades" in df_hist.columns:
                fig = px.bar(df_hist, x="fecha", y="total_unidades", title="Unidades despachadas por día")
                fig.add_hline(y=meta_dia, line_dash="dash", line_color="#ef4444", annotation_text="Meta")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            if st.button("Guardar KPIs en histórico", type="primary"):
                local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Automatico-Historico", "kpis": {"total_unidades": total_u, "promedio_diario": round(prom, 2), "cumplimiento_meta": round(cumpl, 2)}, "usuario": st.session_state.get("username","admin")})
                st.success("KPIs guardados desde histórico.")

    # ==================== NUEVA TAB 6: PREDICCIÓN ====================
    with tab6:
        st.subheader("🔮 Predicción de unidades para los próximos 7 días")
        if st.button("Entrenar modelo y predecir", type="primary"):
            try:
                model, last_row, mae = entrenar_modelo_prediccion()
                if model is None:
                    st.warning(last_row)   # mensaje de error
                else:
                    start_date = datetime.now().date()
                    df_pred = predecir_proximos_7_dias(model, last_row, start_date)
                    st.session_state['df_pred'] = df_pred
                    st.session_state['mae_pred'] = mae
                    st.success(f"Modelo entrenado. Error absoluto medio (MAE): {mae:.2f} unidades.")
            except ImportError:
                st.error("La librería scikit‑learn no está instalada. Agrégala al archivo requirements.txt.")

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

    # ==================== NUEVA TAB 7: ABC ====================
    with tab7:
        st.subheader("📦 Clasificación ABC de productos")
        st.info("Para el análisis ABC completo, necesitamos el detalle de productos del último archivo de transferencias. Por ahora, cargue un archivo en 'Dashboard KPIs' y luego contacte al administrador para activar esta función.")
