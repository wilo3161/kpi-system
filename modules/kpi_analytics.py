# MODIFIED: 2026-05-21 - Auto-defaults from historical, improved RF features, real ABC analysis
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.manager import local_db
from utils.ui import show_module_header, add_back_button


# =============================================================================
# Auto-defaults desde historico
# =============================================================================
def _auto_defaults(proceso, dias=30):
    desde = (datetime.now() - timedelta(days=dias)).isoformat()
    registros = local_db.find("kpi_analytics", {"proceso": proceso, "fecha": {"$gte": desde}})
    if not registros:
        return {}
    totales = {}
    count = 0
    for r in registros:
        kpis = r.get("kpis", {})
        if isinstance(kpis, dict):
            for k, v in kpis.items():
                totales[k] = totales.get(k, 0) + v
            count += 1
    if count == 0:
        return {}
    return {k: round(v / count) for k, v in totales.items()}


# =============================================================================
# PREDICCION (sklearn se importa solo cuando se usa, features mejoradas)
# =============================================================================
def _es_quincena(fecha):
    import calendar
    if fecha.day == 15:
        return True
    ultimo_dia = calendar.monthrange(fecha.year, fecha.month)[1]
    ultimo = fecha.replace(day=ultimo_dia)
    while ultimo.weekday() >= 5:
        ultimo -= timedelta(days=1)
    return fecha == ultimo


def entrenar_modelo_prediccion():
    import sklearn
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error

    historicos = local_db.find("historico", {"modulo": "dashboard_logistico"}, sort=[("fecha_archivo", -1)], limit=90)
    if not historicos:
        return None, None, "No hay datos historicos. Carga archivos en el Dashboard Logistico primero."

    registros = []
    for h in historicos:
        met = h.get("metricas", {})
        if "total_unidades" in met:
            registros.append({"fecha": pd.to_datetime(h.get("fecha_archivo")), "unidades": met["total_unidades"]})

    if len(registros) < 14:
        return None, None, "Se necesitan al menos 14 dias de datos historicos."

    df = pd.DataFrame(registros).sort_values("fecha").drop_duplicates("fecha")
    df['dia_semana'] = df['fecha'].dt.dayofweek
    df['semana'] = df['fecha'].dt.isocalendar().week.astype(int)
    df['mes'] = df['fecha'].dt.month
    df['dia_mes'] = df['fecha'].dt.day                   # día del mes 1-31
    df['finde_semana'] = df['fecha'].dt.dayofweek.isin([5,6]).astype(int)  # bool
    df['quincena'] = ((df['dia_mes'] == 15) | (df['dia_mes'] == df['fecha'].dt.days_in_month)).astype(int)
    df['rolling_mean_3'] = df['unidades'].rolling(3).mean()
    df['lag_7'] = df['unidades'].shift(7)
    df['lag_14'] = df['unidades'].shift(14)
    df['rolling_mean_7'] = df['unidades'].rolling(7).mean()
    df = df.dropna()

    if len(df) < 14:
        return None, None, "Datos insuficientes despues de limpieza."

    X = df[['dia_semana', 'semana', 'mes', 'dia_mes', 'finde_semana', 'quincena', 'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_3']]
    y = df["unidades"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    return model, df.iloc[-1], mae


def predecir_proximos_7_dias(model, last_row, start_date):
    preds = []
    current_date = start_date
    last_units = last_row["unidades"]
    last_lag7 = last_row.get("lag_7", last_units)
    last_lag14 = last_row.get("lag_14", last_units)
    last_roll7 = last_row.get("rolling_mean_7", last_units)
    last_roll_mean_3 = last_row.get("rolling_mean_3", last_units)

    for i in range(7):
        features = {
            'dia_semana': current_date.dayofweek,
            'semana': current_date.isocalendar().week,
            'mes': current_date.month,
            'dia_mes': current_date.day,
            'finde_semana': int(current_date.dayofweek in [5,6]),
            'quincena': int(current_date.day == 15 or current_date.day == pd.Timestamp(current_date.year, current_date.month, 1).days_in_month),
            'lag_7': last_lag7,
            'lag_14': last_lag14,
            'rolling_mean_7': last_roll7,
            'rolling_mean_3': last_roll_mean_3,
        }
        X = pd.DataFrame([features])
        y_pred = model.predict(X)[0]
        y_pred_int = max(0, int(round(y_pred)))
        preds.append({"fecha": current_date, "prediccion": y_pred_int})
        last_lag14 = last_lag7
        last_lag7 = y_pred_int
        last_roll_mean_3 = np.mean([p["prediccion"] for p in preds[-3:]])
        last_roll7 = np.mean([p["prediccion"] for p in preds[-7:]]) if i >= 6 else (last_roll7 * 7 + y_pred_int - last_units) / 7
        current_date += timedelta(days=1)

    return pd.DataFrame(preds)


# =============================================================================
# ABC Analysis real desde inventario
# =============================================================================
def clasificacion_abc():
    inventario = local_db.find("inventario", {"carga_activa": True})
    if not inventario:
        st.warning("No hay datos de inventario activo. Carga un archivo en Control de Inventario primero.")
        return
    df_inv = pd.DataFrame(inventario)
    if 'cantidad' not in df_inv.columns or 'costo' not in df_inv.columns:
        # Intentar con otras columnas
        if 'stock' in df_inv.columns: df_inv.rename(columns={'stock':'cantidad'}, inplace=True)
        elif 'precio' in df_inv.columns: df_inv.rename(columns={'precio':'costo'}, inplace=True)
        else:
            st.error("El inventario no tiene columnas de cantidad y costo necesarias para ABC.")
            return
    
    df_inv['valor_total'] = df_inv['cantidad'].fillna(0) * df_inv['costo'].fillna(0)
    df_inv = df_inv.sort_values('valor_total', ascending=False).reset_index(drop=True)
    
    valor_total = df_inv['valor_total'].sum()
    df_inv['porcentaje_acumulado'] = df_inv['valor_total'].cumsum() / valor_total * 100
    
    condiciones = [
        df_inv['porcentaje_acumulado'] <= 80,
        (df_inv['porcentaje_acumulado'] > 80) & (df_inv['porcentaje_acumulado'] <= 95),
        df_inv['porcentaje_acumulado'] > 95
    ]
    categorias = ['A', 'B', 'C']
    df_inv['ABC'] = np.select(condiciones, categorias, default='C')
    
    col1, col2, col3 = st.columns(3)
    for clase, color in [('A', '#CF0A2C'), ('B', '#f59e0b'), ('C', '#10b981')]:
        subset = df_inv[df_inv['ABC'] == clase]
        with [col1, col2, col3][['A','B','C'].index(clase)]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-left:4px solid {color};border-radius:10px;padding:16px;text-align:center;">
                <div style="font-size:2rem;font-weight:800;color:{color};">{clase}</div>
                <div style="font-size:1.2rem;margin:8px 0;">{len(subset):,} productos</div>
                <div style="font-size:.9rem;color:#94a3b8;">${subset['valor_total'].sum():,.0f}</div>
                <div style="font-size:.8rem;color:#94a3b8;">{subset['valor_total'].sum()/valor_total*100:.1f}% del valor</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.dataframe(df_inv[['codigo_estilo', 'producto', 'color', 'talla', 'cantidad', 'costo', 'valor_total', 'ABC'] if all(c in df_inv.columns for c in ['codigo_estilo','producto','color','talla']) else ['codigo_estilo','producto','ABC']], use_container_width=True)
    
    fig = go.Figure()
    for clase, color in [('A', '#CF0A2C'), ('B', '#f59e0b'), ('C', '#10b981')]:
        subset = df_inv[df_inv['ABC'] == clase]
        fig.add_trace(go.Bar(name=f'Clase {clase}', x=['Valor Total'], y=[subset['valor_total'].sum()], marker_color=color, text=[f'${subset["valor_total"].sum():,.0f}'], textposition='inside'))
    fig.update_layout(title="Distribución de Valor por Clase ABC", barmode='group', template="plotly_dark", paper_bgcolor="rgba(15,23,42,0)", plot_bgcolor="rgba(30,41,59,0.5)")
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# FUNDCION PRINCIPAL
# =============================================================================
def show_kpi_analytics():
    add_back_button(key="back_kpi")
    show_module_header("KPI Analytics", "Indicadores clave de rendimiento operacional")

    def kpi_color(val, meta, invert=False):
        ok = val >= meta if not invert else val <= meta
        return "#10b981" if ok else ("#f59e0b" if abs(val - meta) < 10 else "#ef4444")

    def kpi_card(col, titulo, valor, meta, unidad="%", formula="", frecuencia=""):
        color = kpi_color(valor, meta)
        delta = valor - meta
        signo = "▲" if delta >= 0 else "▼"
        col.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-left:4px solid {color};border-radius:10px;padding:16px;margin-bottom:10px;">
            <div style="font-size:.75em;color:#94a3b8;margin-bottom:4px;">{frecuencia}</div>
            <div style="font-weight:700;color:#e2e8f0;font-size:1em;margin-bottom:8px;">{titulo}</div>
            <div style="font-size:2em;font-weight:800;color:{color};">{valor:.1f}{unidad}</div>
            <div style="font-size:.75em;color:#94a3b8;margin-top:4px;">
                Meta: {meta}{unidad} | <span style="color:{'#10b981' if delta>=0 else '#ef4444'}">{signo} {abs(delta):.1f}{unidad}</span>
            </div>
            {f"<div style='font-size:.7em;color:#64748b;margin-top:6px;font-style:italic;'>{formula}</div>" if formula else ""}
        </div>
        """, unsafe_allow_html=True)

    tabs = st.tabs([
        "Salidas y Despachos",
        "Recepciones e Inventario",
        "Calidad y Reproceso",
        "Resumen Ejecutivo",
        "Desde Historico",
        "Prediccion de Demanda",
        "Analisis ABC"
    ])
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = tabs

    # ==================== TAB 1 ====================
    with tab1:
        st.markdown("### KPIs de Salidas y Despachos")
        with st.form("form_despachos"):
            # Cargar valores por defecto del histórico reciente
            try:
                ultimo_kpi = local_db.find("kpi_analytics", {"proceso": {"$regex": "Salidas"}}, sort=[("fecha", -1)], limit=1)
                if ultimo_kpi:
                    u = ultimo_kpi[0].get("kpis", {})
                    default_vals = {k: u.get(k, 0) for k in u}
                else:
                    default_vals = {}
            except:
                default_vals = {}
            cols = st.columns(3)
            pedidos_desp_correctos = cols[0].number_input("Pedidos despachados correctamente", min_value=0, value=st.session_state.get("kpi_ped_desp_ok", default_vals.get("exactitud_despacho", 0)))
            total_pedidos = cols[1].number_input("Total pedidos del periodo", min_value=1, value=st.session_state.get("kpi_total_ped", default_vals.get("total_pedidos", 100)))
            meta_exactitud = cols[2].number_input("Meta Exactitud de Despacho (%)", min_value=0, max_value=100, value=95)
            cols = st.columns(3)
            pedidos_otif = cols[0].number_input("OTIF - entregados a tiempo/completos", min_value=0, value=st.session_state.get("kpi_otif_ok", default_vals.get("otif", 0)))
            meta_otif = cols[1].number_input("Meta OTIF (%)", min_value=0, max_value=100, value=95)
            cols = st.columns(3)
            cant_transferida = cols[0].number_input("Cantidad transferida hoy (unidades)", min_value=0, value=st.session_state.get("kpi_cant_transf", default_vals.get("cumplimiento_meta_diaria", 0)))
            meta_diaria = cols[1].number_input("Meta diaria (unidades)", min_value=1, value=st.session_state.get("kpi_meta_diaria", 1000))
            calcular = st.form_submit_button("Calcular KPIs", use_container_width=True, type="primary")
        if calcular or st.session_state.get("kpi_despachos_calculados"):
            if calcular:
                st.session_state.kpi_ped_desp_ok = pedidos_desp_correctos
                st.session_state.kpi_total_ped = total_pedidos
                st.session_state.kpi_otif_ok = pedidos_otif
                st.session_state.kpi_cant_transf = cant_transferida
                st.session_state.kpi_meta_diaria = meta_diaria
                st.session_state.kpi_despachos_calculados = True
            exactitud_desp = (st.session_state.kpi_ped_desp_ok / max(st.session_state.kpi_total_ped, 1)) * 100
            otif_val = (st.session_state.kpi_otif_ok / max(st.session_state.kpi_total_ped, 1)) * 100
            cumpl_meta = (st.session_state.kpi_cant_transf / max(st.session_state.kpi_meta_diaria, 1)) * 100
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Exactitud de Despacho", exactitud_desp, meta_exactitud, formula="Pedidos correctos / Total x 100", frecuencia="Semanal")
            kpi_card(c2, "OTIF", otif_val, meta_otif, formula="Pedidos a tiempo/completos / Total x 100", frecuencia="Semanal")
            kpi_card(c3, "Cumplimiento Meta Diaria", cumpl_meta, 100, formula="Cant. transferida / Meta x 100", frecuencia="Diario")
            if calcular:
                local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Salidas y Despachos", "kpis": {"exactitud_despacho": round(exactitud_desp,2), "otif": round(otif_val,2), "cumplimiento_meta_diaria": round(cumpl_meta,2), "total_pedidos": int(total_pedidos)}, "usuario": st.session_state.get("username","admin")})
                st.success("KPIs guardados en el historico")

    # ==================== TAB 2 ====================
    with tab2:
        st.markdown("### KPIs de Recepciones y Control de Inventario")
        with st.form("form_inventario"):
            # Cargar valores por defecto del histórico reciente
            try:
                ultimo_kpi = local_db.find("kpi_analytics", {"proceso": {"$regex": "Inventario"}}, sort=[("fecha", -1)], limit=1)
                if ultimo_kpi:
                    u = ultimo_kpi[0].get("kpis", {})
                    default_vals = {k: u.get(k, 0) for k in u}
                else:
                    default_vals = {}
            except:
                default_vals = {}
            st.markdown("**Exactitud de Recepcion**")
            col_a, col_b = st.columns(2)
            ped_recibidos_ok = col_a.number_input("Pedidos recibidos correctamente", min_value=0, value=default_vals.get("exactitud_recepcion", 0))
            total_esperados = col_b.number_input("Total articulos esperados", min_value=1, value=default_vals.get("total_esperados", 100))
            st.markdown("**ERI - Exactitud de Registro de Inventario**")
            col_c, col_d = st.columns(2)
            stock_contado = col_c.number_input("Stock contado (fisico)", min_value=0, value=default_vals.get("eri_stock_contado", 0))
            stock_registrado = col_d.number_input("Stock registrado en sistema", min_value=1, value=default_vals.get("eri_stock_registrado", 100))
            st.markdown("**Nivel de Perdida sobre Ventas**")
            col_e, col_f = st.columns(2)
            num_faltantes = col_e.number_input("Articulos faltantes", min_value=0, value=default_vals.get("perdida_faltantes", 0))
            ventas_periodo = col_f.number_input("Ventas del periodo (unidades)", min_value=1, value=default_vals.get("ventas_periodo", 1000))
            st.markdown("**Indice de Recuperacion de Faltantes**")
            col_g, col_h = st.columns(2)
            cant_recuperada = col_g.number_input("Cantidad recuperada", min_value=0, value=default_vals.get("recuperacion_cantidad", 0))
            total_faltantes = col_h.number_input("Total faltantes detectados", min_value=1, value=defaults_inv.get("recuperacion_total", 100))
            st.markdown("**Ajustes Manuales**")
            col_i, col_j = st.columns(2)
            ajustes_manuales = col_i.number_input("Ajustes manuales (frecuencia)", min_value=0, value=defaults_inv.get("ajustes_manuales", 0))
            total_transferencias = col_j.number_input("Total transferencias inventario", min_value=1, value=defaults_inv.get("total_transferencias", 10))
            calcular2 = st.form_submit_button("Calcular KPIs de Inventario", use_container_width=True, type="primary")
        if calcular2:
            exactitud_recepcion = (ped_recibidos_ok / max(total_esperados, 1)) * 100
            eri = (stock_contado / max(stock_registrado, 1)) * 100
            perdida_ventas = (num_faltantes / max(ventas_periodo, 1)) * 100
            idx_recuperacion = (cant_recuperada / max(total_faltantes, 1)) * 100
            frec_ajustes = (ajustes_manuales / max(total_transferencias, 1)) * 100
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Exactitud de Recepcion", exactitud_recepcion, 98, formula="Pedidos correctos / Total x 100", frecuencia="Mensual")
            kpi_card(c2, "ERI", eri, 98, formula="Stock contado / Stock sistema x 100", frecuencia="Semanal")
            kpi_card(c3, "Perdida sobre Ventas", perdida_ventas, 2, formula="Faltantes / Ventas x 100", frecuencia="Mensual", invert=True)
            c4, c5 = st.columns(2)
            kpi_card(c4, "Recuperacion de Faltantes", idx_recuperacion, 80, formula="Recuperada / Total x 100", frecuencia="Trimestral")
            kpi_card(c5, "Frecuencia Ajustes Manuales", frec_ajustes, 5, formula="Ajustes / Transferencias x 100", frecuencia="Mensual")
            local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Inventario", "kpis": {
                "exactitud_recepcion": round(exactitud_recepcion, 2), "eri": round(eri, 2),
                "perdida_ventas": round(perdida_ventas, 2), "recuperacion_faltantes": round(idx_recuperacion, 2),
                "ajustes_manuales": round(frec_ajustes, 2),
                "eri_stock_contado": int(stock_contado), "eri_stock_registrado": int(stock_registrado),
                "perdida_faltantes": int(num_faltantes), "ventas_periodo": int(ventas_periodo),
                "recuperacion_cantidad": int(cant_recuperada), "recuperacion_total": int(total_faltantes),
                "total_transferencias": int(total_transferencias),
            }, "usuario": st.session_state.get("username", "admin")})
            st.success("KPIs de inventario guardados")

    # ==================== TAB 3 ====================
    with tab3:
        st.markdown("### KPIs de Control de Calidad y Reproceso")
        with st.form("form_calidad"):
            # Cargar valores por defecto del histórico reciente
            try:
                ultimo_kpi = local_db.find("kpi_analytics", {"proceso": {"$regex": "Calidad"}}, sort=[("fecha", -1)], limit=1)
                if ultimo_kpi:
                    u = ultimo_kpi[0].get("kpis", {})
                    default_vals = {k: u.get(k, 0) for k in u}
                else:
                    default_vals = {}
            except:
                default_vals = {}
            col_a, col_b = st.columns(2)
            fallas_recuperadas = col_a.number_input("Fallas recuperadas por categoria", min_value=0, value=default_vals.get("control_reproceso", 0))
            total_fallas = col_b.number_input("Total fallas recibidas", min_value=1, value=default_vals.get("total_fallas", 100))
            col_c, col_d = st.columns(2)
            stock_bod_contado = col_c.number_input("Stock contado (inventario anual)", min_value=0, value=default_vals.get("eri_bodega_stock_contado", 0))
            stock_bod_sistema = col_d.number_input("Stock en sistema (inventario anual)", min_value=1, value=default_vals.get("eri_bodega_stock_sistema", 100))
            calcular3 = st.form_submit_button("Calcular KPIs de Calidad", use_container_width=True, type="primary")
        if calcular3:
            control_reproceso = (fallas_recuperadas / max(total_fallas, 1)) * 100
            eri_bodega = (stock_bod_contado / max(stock_bod_sistema, 1)) * 100
            st.markdown("---")
            c1, c2 = st.columns(2)
            kpi_card(c1, "Control de Reproceso", control_reproceso, 85, formula="Fallas recuperadas / Total x 100", frecuencia="Mensual")
            kpi_card(c2, "Gestion de Bodega (ERI)", eri_bodega, 98, formula="Stock contado / Stock sistema x 100", frecuencia="Anual")
            local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Calidad", "kpis": {
                "control_reproceso": round(control_reproceso, 2), "eri_bodega": round(eri_bodega, 2),
                "total_fallas": int(total_fallas),
                "eri_bodega_stock_contado": int(stock_bod_contado), "eri_bodega_stock_sistema": int(stock_bod_sistema),
            }, "usuario": st.session_state.get("username", "admin")})
            st.success("KPIs de calidad guardados")

    # ==================== TAB 4 ====================
    with tab4:
        st.markdown("### Historial de KPIs Registrados")
        hist_kpi = local_db.find("kpi_analytics", sort=[("fecha", -1)], limit=50)
        if not hist_kpi:
            st.info("Aun no hay KPIs calculados. Usa las pestanas anteriores para ingresar datos.")
        else:
            rows = []
            for rec in hist_kpi:
                fecha = rec.get("fecha", "")
                proceso = rec.get("proceso", "")
                for k, v in rec.get("kpis", {}).items():
                    rows.append({"Fecha": str(fecha)[:10], "Proceso": proceso, "KPI": k.replace("_", " ").title(), "Valor": v})
            if rows:
                df_kpi = pd.DataFrame(rows)
                st.dataframe(df_kpi, use_container_width=True, height=300)
                fig = go.Figure()
                for proceso in df_kpi["Proceso"].unique():
                    df_p = df_kpi[df_kpi["Proceso"] == proceso]
                    fig.add_trace(go.Bar(name=proceso, x=df_p["KPI"], y=df_p["Valor"], text=df_p["Valor"].round(1), textposition="auto"))
                fig.update_layout(title="KPIs por Proceso", paper_bgcolor="#0f172a", plot_bgcolor="#1e293b", font=dict(color="#e2e8f0"), barmode="group", height=400, xaxis=dict(gridcolor="#334155"), yaxis=dict(gridcolor="#334155", range=[0, 110]))
                st.plotly_chart(fig, use_container_width=True)

    # ==================== TAB 5 ====================
    with tab5:
        st.markdown("### Calculo automatico desde historico logistico")
        hist = local_db.find("historico", {}, sort=[("fecha_archivo", -1)], limit=60)
        if not hist:
            st.info("Sin datos en historico. Carga archivos en Dashboard Logistico primero.")
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
            dias = len(df_hist)
            prom = total_u / max(dias, 1)
            cumpl = (prom / meta_dia) * 100
            c1, c2, c3 = st.columns(3)
            kpi_card(c1, "Total unidades periodo", total_u, 0, unidad=" uds", frecuencia="Periodo seleccionado")
            kpi_card(c2, "Promedio diario", round(prom, 1), meta_dia, unidad=" uds", frecuencia="Diario")
            kpi_card(c3, "Cumplimiento meta", round(cumpl, 1), 100, frecuencia="Diario")
            if "total_unidades" in df_hist.columns:
                fig = px.bar(df_hist, x="fecha", y="total_unidades", title="Unidades despachadas por dia")
                fig.add_hline(y=meta_dia, line_dash="dash", line_color="#ef4444", annotation_text="Meta")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            if st.button("Guardar KPIs en historico", type="primary"):
                local_db.insert("kpi_analytics", {"fecha": datetime.utcnow(), "proceso": "Automatico-Historico", "kpis": {"total_unidades": total_u, "promedio_diario": round(prom, 2), "cumplimiento_meta": round(cumpl, 2)}, "usuario": st.session_state.get("username", "admin")})
                st.success("KPIs guardados desde historico.")

    # ==================== TAB 6: PREDICCION ====================
    with tab6:
        st.subheader("Prediccion de unidades para los proximos 7 dias")
        if st.button("Entrenar modelo y predecir", type="primary"):
            try:
                model, last_row, mae = entrenar_modelo_prediccion()
                if model is None:
                    st.warning(last_row)
                else:
                    start_date = datetime.now().date()
                    df_pred = predecir_proximos_7_dias(model, last_row, start_date)
                    st.session_state["df_pred"] = df_pred
                    st.session_state["mae_pred"] = mae
                    st.success(f"Modelo entrenado. Error absoluto medio (MAE): {mae:.2f} unidades.")
            except ImportError:
                st.error("scikit-learn no esta instalada. Agregala al archivo requirements.txt.")

        if "df_pred" in st.session_state:
            df_pred = st.session_state["df_pred"]
            fig = px.bar(df_pred, x="fecha", y="prediccion", title="Prediccion de unidades por dia", labels={"prediccion": "Unidades", "fecha": "Fecha"}, color="prediccion", color_continuous_scale="Blues")
            fig.update_layout(template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

            df_pred_display = df_pred.copy()
            df_pred_display["fecha_str"] = df_pred_display["fecha"].dt.strftime("%A %d/%m/%Y")
            st.dataframe(df_pred_display[["fecha_str", "prediccion"]].rename(columns={"fecha_str": "Fecha", "prediccion": "Unidades"}), use_container_width=True)
            total_semana = df_pred["prediccion"].sum()
            dia_pico = df_pred.loc[df_pred["prediccion"].idxmax()]
            st.metric("Total proyectado semana", f"{total_semana:,}")
            st.info(f"Dia pico: **{dia_pico['fecha'].strftime('%A %d/%m')}** con **{dia_pico['prediccion']:,}** unidades.")

    # ==================== TAB 7: ABC ANALYSIS ====================
    with tab7:
        st.subheader("📦 Clasificación ABC de productos")
        clasificacion_abc()
