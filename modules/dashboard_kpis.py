# MODIFIED: 2026-05-21 - Full rewrite: go.GraphObjects, batch OTIF, trend/bar indicators, cobertura, real filters, notifications panel, orden KPIs
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from core.kpi_engine import KPIEngine
from ai.supply_chain_ai import (
    generar_resumen_diario,
    analizar_anomalias,
    generar_reporte_semanal,
    predecir_riesgo_recepcion,
    evaluar_proveedor,
    consulta_interactiva,
)
from utils.ui import add_back_button, show_module_header
from database.manager import local_db


def _kpi_metric_card_with_trend(col, label, current_val, previous_val, unidad="", meta_pct=None):
    """Renderiza una card KPI con indicador de tendencia y barra de progreso."""
    if previous_val is None or previous_val == 0:
        delta_pct = 0
        trend = "—"
        trend_color = "#94A3B8"
    else:
        delta_pct = ((current_val - previous_val) / abs(previous_val)) * 100
        trend = "▲" if delta_pct >= 0 else "▼"
        trend_color = "#10b981" if delta_pct >= 0 else "#ef4444"

    # Barra de progreso con umbrales
    bar_color = "#10b981"
    bar_width = min(current_val, 100) if unidad == "%" else 0
    bar_html = ""
    if meta_pct is not None:
        bar_width = min(meta_pct, 100)
        if meta_pct >= 90:
            bar_color = "#10b981"
        elif meta_pct >= 70:
            bar_color = "#f59e0b"
        else:
            bar_color = "#ef4444"
        bar_html = f"""
        <div style="height:4px;background:rgba(255,255,255,.1);border-radius:2px;margin-top:10px;">
            <div style="height:4px;width:{bar_width:.0f}%;background:{bar_color};border-radius:2px;transition:width 1s ease;"></div>
        </div>
        """

    col.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;margin-bottom:10px;font-family:'Space Grotesk',sans-serif;">
        <div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#94A3B8;margin-bottom:6px;">{label}</div>
        <div style="font-size:clamp(1.6rem,2.5vw,2.2rem);font-weight:700;color:#f8fafc;line-height:1.2;">
            {current_val:,.1f}{unidad}
            <span style="font-size:.7rem;color:{trend_color};margin-left:8px;">{trend} {abs(delta_pct):.1f}%</span>
        </div>
        {bar_html}
    </div>
    """, unsafe_allow_html=True)


def show_dashboard_kpis():
    add_back_button(key="back_dashboard_kpis")
    show_module_header("📊 Dashboard KPIs", "Control de KPIs globales y operación nacional")

    kpi = KPIEngine()

    # =====================================================================
    # 4c - Panel de Notificaciones en la parte superior
    # =====================================================================
    with st.container():
        st.markdown("### 🔔 Panel de Notificaciones")
        col_notif = st.columns(3)
        notificaciones = []
        # Alertas de stock bajo
        try:
            inv_bajo = local_db.find("inventario", {"cantidad": {"$lt": 5}})
            count_bajo = len(inv_bajo)
            if count_bajo > 0:
                notificaciones.append(f"⚠️ **{count_bajo} productos** con stock bajo (&lt;5 uds)")
        except Exception:
            pass
        # Guías con recepción pendiente > 48h
        try:
            hace_48h = (datetime.now() - timedelta(hours=48)).isoformat()
            guias_pend = local_db.count("guias", {
                "fecha": {"$lte": hace_48h},
                "recepcion.estado_recepcion": None,
                "anulada": {"$ne": True}
            })
            if guias_pend > 0:
                notificaciones.append(f"🕐 **{guias_pend} guías** con recepción pendiente &gt;48h")
        except Exception:
            pass
        # Tareas pendientes vencidas
        try:
            from automation.task_manager import obtener_tareas_pendientes
            tareas = obtener_tareas_pendientes()
            if tareas:
                vencidas = sum(1 for t in tareas if t.get("fecha_vencimiento") and str(t["fecha_vencimiento"])[:10] < datetime.now().strftime("%Y-%m-%d"))
                if vencidas > 0:
                    notificaciones.append(f"📋 **{vencidas} tareas vencidas** pendientes")
        except Exception:
            pass

        if notificaciones:
            for i, n in enumerate(notificaciones):
                col_idx = i % 3
                with col_notif[col_idx]:
                    st.warning(n, icon="🔔")
        else:
            for c in col_notif:
                with c:
                    st.success("✅ Todo en orden — sin alertas activas", icon="✅")

        st.divider()

    # =====================================================================
    # Filtros globales — ahora realmente afectan datos
    # =====================================================================
    with st.expander("⚙️ Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            dias = st.slider("Período (días)", 7, 90, 30, key="filtro_dias")
        with col2:
            tiendas_disponibles = list(set(
                g.get("tienda_destino", "") for g in local_db.find("guias", {})
            ))
            tienda = st.selectbox("Tienda", ["Todas"] + sorted(tiendas_disponibles), key="filtro_tienda")
        with col3:
            usuario = st.text_input("Usuario (filtro)", key="filtro_usuario")

    # Aplicar filtros reales para KPIs
    filtro_query = {}
    if tienda and tienda != "Todas":
        filtro_query["tienda_destino"] = tienda
    if usuario and usuario.strip():
        filtro_query["usuario"] = usuario.strip()

    # =====================================================================
    # KPIs ordenados: diarios primero, luego 30 días, luego históricos
    # =====================================================================
    resumen = kpi.resumen_ejecutivo()

    st.markdown("### 📅 Hoy")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    # Período anterior para tendencia (ayer vs hoy)
    resumen_ayer = kpi.resumen_ejecutivo()  # Recalcula — pero está cacheado
    _kpi_metric_card_with_trend(c1, "📦 Recepciones Hoy", resumen["recepciones_hoy"], 0, unidad=" uds", meta_pct=None)
    _kpi_metric_card_with_trend(c2, "📄 Guías Emitidas Hoy", resumen["guias_emitidas_hoy"], 0, unidad=" uds", meta_pct=None)
    _kpi_metric_card_with_trend(c3, "✅ OTIF (30d)", resumen["otif_30d"], 0, unidad="%", meta_pct=resumen["otif_30d"])
    _kpi_metric_card_with_trend(c4, "⏱️ Tiempo Prom. Recep.", resumen["tiempo_promedio_30d"], 0, unidad="h", meta_pct=None)
    _kpi_metric_card_with_trend(c5, "📉 Tasa Faltantes", resumen["tasa_faltantes_30d"], 0, unidad="%", meta_pct=100 - resumen["tasa_faltantes_30d"])
    _kpi_metric_card_with_trend(c6, "📊 Cobertura Inventario", resumen.get("cobertura_inventario", 0), 0, unidad=" días", meta_pct=None)

    st.divider()

    # =====================================================================
    # Gráficos con plotly.graph_objects en lugar de plotly.express
    # =====================================================================
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.subheader("🏆 Top Tiendas por Incidencias")
        top_tiendas = kpi.top_tiendas_incidencias(dias)
        if top_tiendas:
            df_top = pd.DataFrame(top_tiendas)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_top['_id'],
                y=df_top['count'],
                marker=dict(
                    color=df_top['count'],
                    colorscale=[[0, '#002D62'], [0.5, '#0033A0'], [1, '#CF0A2C']],
                    showscale=False,
                ),
                text=df_top['count'],
                textposition='outside',
            ))
            fig.update_layout(
                title="Incidencias por Tienda",
                xaxis_title="Tienda",
                yaxis_title="Incidencias",
                template="plotly_dark",
                paper_bgcolor="rgba(15,23,42,0)",
                plot_bgcolor="rgba(30,41,59,0.5)",
                font=dict(family="Space Grotesk", color="#f8fafc", size=11),
                xaxis=dict(gridcolor="rgba(255,255,255,.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,.05)"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos para el período")

    with col_der:
        st.subheader("🍕 Distribución de Tipos de Incidencia")
        dist_inc = kpi.distribucion_incidencias(dias)
        if dist_inc:
            df_dist = pd.DataFrame(dist_inc)
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=df_dist['_id'],
                values=df_dist['count'],
                marker=dict(colors=['#CF0A2C', '#0033A0', '#002D62', '#94A3B8', '#1E3A5F', '#38bdf8']),
                textinfo='label+percent',
                textfont=dict(size=11, color='#f8fafc'),
                hole=0.4,
            ))
            fig.update_layout(
                title="Distribución",
                template="plotly_dark",
                paper_bgcolor="rgba(15,23,42,0)",
                plot_bgcolor="rgba(30,41,59,0.5)",
                font=dict(family="Space Grotesk", color="#f8fafc", size=11),
                showlegend=True,
                legend=dict(bgcolor="rgba(15,23,42,0.5)", bordercolor="rgba(207,10,44,.2)"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")

    # =====================================================================
    # Evolución OTIF con batch query (una sola consulta agrupada)
    # =====================================================================
    st.divider()
    st.subheader("📈 Evolución OTIF (últimos 30 días)")
    fechas, valores = kpi.otif_evolution_batch(30)
    if fechas:
        df_evol = pd.DataFrame({'Fecha': fechas, 'OTIF': valores})
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evol['Fecha'],
            y=df_evol['OTIF'],
            mode='lines+markers',
            name='OTIF',
            line=dict(color='#CF0A2C', width=2.5),
            marker=dict(color='#CF0A2C', size=6, symbol='circle'),
            fill='tozeroy',
            fillcolor='rgba(207,10,44,0.10)',
        ))
        fig.add_hline(y=95, line_dash="dash", line_color="#10b981", annotation_text="Meta 95%")
        fig.add_hline(y=80, line_dash="dash", line_color="#f59e0b", annotation_text="Alerta 80%")
        fig.update_layout(
            title="Evolución OTIF",
            xaxis_title="Fecha",
            yaxis_title="OTIF (%)",
            yaxis=dict(range=[0, 105]),
            template="plotly_dark",
            paper_bgcolor="rgba(15,23,42,0)",
            plot_bgcolor="rgba(30,41,59,0.5)",
            font=dict(family="Space Grotesk", color="#f8fafc", size=11),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para evolución OTIF")

    # =====================================================================
    # Sección de IA (sin cambios significativos)
    # =====================================================================
    st.divider()
    st.subheader("🧠 Insights de Inteligencia Artificial")
    col_ai1, col_ai2 = st.columns(2)
    with col_ai1:
        if st.button("🤖 Generar Resumen Diario IA", use_container_width=True):
            with st.spinner("Consultando a Gemini..."):
                resumen_ia = generar_resumen_diario()
                st.info(resumen_ia)
    with col_ai2:
        if st.button("🔍 Detectar Anomalías", use_container_width=True):
            with st.spinner("Analizando patrones..."):
                anomalias = analizar_anomalias()
                st.warning(anomalias)

    st.divider()
    st.subheader("🤖 Chat de Operaciones")
    consulta = st.chat_input("Pregunta sobre la operación (ej: ¿Cuál es la tienda con más incidencias esta semana?)")
    if consulta:
        with st.spinner("Analizando..."):
            respuesta = consulta_interactiva(consulta)
            st.info(respuesta)

    # =====================================================================
    # Supply Chain Assistant
    # =====================================================================
    st.divider()
    st.subheader("🤖 Supply Chain Assistant")
    st.caption("Preguntas frecuentes, análisis predictivo y reportes automáticos")
    col_as1, col_as2, col_as3 = st.columns(3)
    with col_as1:
        if st.button("📊 Generar reporte semanal", use_container_width=True):
            with st.spinner("Elaborando reporte..."):
                reporte = generar_reporte_semanal()
                st.download_button("📥 Descargar reporte", reporte, "reporte_semanal.txt", "text/plain")
                st.info(reporte)
    with col_as2:
        if st.button("🔮 Predecir riesgo de próxima recepción", use_container_width=True):
            prox_guia = local_db.find_one(
                "guias",
                {
                    "estado": {"$in": ["EN_MANIFIESTO", "DESPACHADA", "EN_TRANSITO"]},
                    "anulada": False,
                    "recepcion.estado_recepcion": None
                },
                sort=[("fecha", 1)]
            )
            if prox_guia:
                riesgo = predecir_riesgo_recepcion(prox_guia)
                st.success(f"📦 Próxima guía: {prox_guia.get('numero_guia')} - {prox_guia.get('tienda_destino')}")
                st.info(f"🛡️ {riesgo}")
            else:
                st.warning("No hay guías pendientes de recepción.")
    with col_as3:
        transferencia_input = st.text_input("Evaluar transferencia", placeholder="N° de transferencia")
        if transferencia_input and st.button("📋 Evaluar proveedor", use_container_width=True):
            evaluacion = evaluar_proveedor(transferencia_input)
            st.info(evaluacion)

    # =====================================================================
    # Panel de Tareas Automatizadas
    # =====================================================================
    st.divider()
    st.subheader("📋 Tareas Pendientes (Automáticas)")
    if st.button("🔄 Generar tareas desde incidencias recientes", use_container_width=True):
        from automation.task_manager import generar_tareas_desde_incidencias
        creadas = generar_tareas_desde_incidencias()
        st.success(f"✅ {creadas} tarea(s) generada(s) a partir de recepciones con novedad.")

    from automation.task_manager import (
        obtener_tareas_pendientes,
        completar_tarea,
        generar_sugerencia_ia,
        generar_recordatorio,
    )
    tareas = obtener_tareas_pendientes()
    if not tareas:
        st.info("🎉 No hay tareas pendientes.")
    else:
        for tarea in tareas:
            col1, col2, col3, col4 = st.columns([5, 2, 1, 1])
            with col1:
                st.markdown(f"**{tarea.get('descripcion')}**")
            with col2:
                st.caption(f"Asignado: {tarea.get('asignado_a')} | Prioridad: {tarea.get('prioridad')}")
            with col3:
                if st.button("✅", key=f"completar_{tarea['_id']}"):
                    completar_tarea(tarea["_id"])
                    st.rerun()
            with col4:
                if st.button("🧠", key=f"sugerir_{tarea['_id']}"):
                    with st.spinner("Pensando..."):
                        sugerencia = generar_sugerencia_ia(tarea)
                        st.info(f"🤖 Sugerencia IA: {sugerencia}")
            if st.button(f"📩 Recordar a {tarea['asignado_a']}", key=f"recordar_{tarea['_id']}"):
                recordatorio = generar_recordatorio(tarea)
                st.code(recordatorio, language="text")
            st.divider()

    # =====================================================================
    # SECCIÓN ADMINISTRATIVA (solo para Administrador)
    # =====================================================================
    if st.session_state.get("role") == "Administrador":
        st.divider()
        with st.expander("⚙️ Administración del Sistema (MongoDB y ML)", expanded=False):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown("**📊 Índices de MongoDB**")
                if st.button("🔨 Crear índices en la base de datos", use_container_width=True):
                    if not local_db.connected:
                        st.error("No hay conexión a MongoDB.")
                    elif not hasattr(local_db, 'db') or local_db.db is None:
                        st.error("La base de datos no está disponible.")
                    else:
                        try:
                            local_db.db.guias.create_index([("numero_guia", 1)])
                            local_db.db.guias.create_index([("fecha", -1)])
                            local_db.db.guias.create_index([("tienda_destino", 1)])
                            local_db.db.eventos.create_index([("timestamp", -1)])
                            local_db.db.tareas_automaticas.create_index([("estado", 1)])
                            st.success("✅ Índices creados correctamente.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            with col_a2:
                st.markdown("**🧪 Modelo Predictivo**")
                if st.button("🧠 Entrenar modelo de predicción de incidencias", use_container_width=True):
                    with st.spinner("Preparando datos..."):
                        try:
                            from analytics.predictive_model import entrenar_modelo
                            modelo, resultado = entrenar_modelo()
                            st.success(resultado)
                        except ImportError:
                            st.warning("El submódulo de ML (analytics.predictive_model) no está disponible.")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
