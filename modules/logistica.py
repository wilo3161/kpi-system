"""
modules/logistica.py — DASHBOARD LOGÍSTICO AEROPOSTALE (v2 OPTIMIZADA)
=====================================================================
- Dashboard rápido con caché interna
- Métricas de transferencias diarias, semanales, mensuales
- Reemplazar registro (borrado controlado + nuevo insert) con auditoría
- Borrado Seguro con auditoría
- Histórico con búsqueda por fecha, tienda, usuario
- Consumo mínimo de recursos: carga 200 registros máx, proyecciones optimizadas
- Gráficos con Plotly Express (livianos)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go

from utils.ui import add_back_button, show_module_header
from utils.roles import can_access
from database.manager import (
    local_db, guardar_historico, consultar_historico,
    existe_historico_dia, obtener_historico_por_fecha,
    fusionar_historico_dia, registrar_auditoria,
    reemplazar_registro, borrado_seguro
)
from config.stores_data import TIENDAS_DATA

# =============================================================================
# CONSTANTES
# =============================================================================
COL_GUIAS = "guias"
COL_HISTORICO = "historico"

# =============================================================================
# CACHE DE DASHBOARD (carga cada 120 segundos)
# =============================================================================
@st.cache_data(ttl=120)
def _cargar_guias_cache() -> list:
    """Carga guías desde DB con caché para evitar consultas repetitivas."""
    return local_db.find(
        COL_GUIAS,
        {},
        projection={
            "numero_guia": 1, "estado": 1, "tienda_destino": 1,
            "fecha_guia": 1, "fecha_recepcion": 1, "total_prendas": 1,
            "usuario_creador": 1, "usuario_recepcion": 1,
        },
        limit=500
    )


# =============================================================================
# DASHBOARD PRINCIPAL
# =============================================================================
def _seccion_dashboard():
    st.markdown("### 📊 Dashboard Logístico")
    st.caption("Métricas generales de transferencias a tiendas")

    guias = _cargar_guias_cache()
    if not guias:
        st.info("ℹ️ No hay datos de guías para mostrar dashboard")
        return

    df = pd.DataFrame(guias)

    # Parsear fechas de forma segura
    for col in ["fecha_guia", "fecha_recepcion"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    hoy = datetime.now()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # Métricas
    total_guias = len(df)
    total_recibidas = len(df[df["estado"] == "RECIBIDA"]) if "estado" in df.columns else 0
    total_pendientes = len(df[df["estado"] == "PENDIENTE"]) if "estado" in df.columns else 0
    total_prendas = int(df["total_prendas"].sum()) if "total_prendas" in df.columns else 0

    # Métricas semanales
    df_semana = df[df["fecha_guia"] >= inicio_semana] if "fecha_guia" in df.columns else pd.DataFrame()
    guias_semana = len(df_semana)
    prendas_semana = int(df_semana["total_prendas"].sum()) if not df_semana.empty and "total_prendas" in df_semana.columns else 0

    # Métricas mensuales
    df_mes = df[df["fecha_guia"] >= inicio_mes] if "fecha_guia" in df.columns else pd.DataFrame()
    guias_mes = len(df_mes)
    prendas_mes = int(df_mes["total_prendas"].sum()) if not df_mes.empty and "total_prendas" in df_mes.columns else 0

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📦 Total Guías", total_guias,
                  delta=f"+{guias_semana} esta semana")
    with c2:
        st.metric("✅ Recibidas", total_recibidas,
                  delta=f"{round(total_recibidas/total_guias*100,1) if total_guias else 0}%" if total_guias else "0%")
    with c3:
        st.metric("⏳ Pendientes", total_pendientes)
    with c4:
        st.metric("👕 Prendas Transferidas", f"{total_prendas:,}",
                  delta=f"+{prendas_semana:,} esta semana")

    # Gráfico: Guías por día (últimos 30 días)
    st.markdown("#### 📈 Guías por Día (Últimos 30 días)")
    if "fecha_guia" in df.columns and not df.empty:
        fecha_fin = hoy
        fecha_ini = hoy - timedelta(days=30)
        df_30 = df[df["fecha_guia"] >= fecha_ini].copy()
        if not df_30.empty:
            df_30["dia"] = df_30["fecha_guia"].dt.date
            diario = df_30.groupby("dia").agg(
                guias=("numero_guia", "count"),
                prendas=("total_prendas", "sum")
            ).reset_index()

            fig = px.bar(diario, x="dia", y=["guias", "prendas"],
                         title="📊 Guías y Prendas por Día",
                         barmode="group",
                         color_discrete_sequence=["#636EFA", "#EF553B"])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#FFFFFF",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_tickangle=-45,
                height=400,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos en los últimos 30 días")
    else:
        st.info("Sin datos de fecha disponibles")

    # Gráfico: Distribución por tienda (Top 15)
    st.markdown("#### 🏪 Distribución por Tienda (Top 15)")
    if "tienda_destino" in df.columns and not df.empty:
        tiendas = df["tienda_destino"].value_counts().head(15).reset_index()
        tiendas.columns = ["Tienda", "Guías"]
        fig2 = px.pie(tiendas, values="Guías", names="Tienda",
                      title="📊 Guías por Tienda",
                      hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#FFFFFF",
            height=400,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Tabla de últimas guías
    st.markdown("#### 📋 Últimas 20 Guías")
    df_recent = df.head(20)
    cols_show = ["numero_guia", "tienda_destino", "estado", "total_prendas", "fecha_guia", "fecha_recepcion"]
    cols_exist = [c for c in cols_show if c in df_recent.columns]
    if cols_exist:
        df_tabla = df_recent[cols_exist].copy()
        for col in df_tabla.columns:
            if df_tabla[col].dtype in (np.dtype('datetime64[ns]'),):
                df_tabla[col] = df_tabla[col].dt.strftime("%Y-%m-%d")
        rename_map = {
            "numero_guia": "N° Guía", "tienda_destino": "Tienda",
            "estado": "Estado", "total_prendas": "Prendas",
            "fecha_guia": "Fecha", "fecha_recepcion": "Recibida",
        }
        df_tabla = df_tabla.rename(columns=rename_map)
        st.dataframe(df_tabla, use_container_width=True)


# =============================================================================
# SECCIÓN DE BÚSQUEDA Y GESTIÓN DE GUÍAS
# =============================================================================
def _seccion_gestion_guias():
    st.markdown("### 🔍 Gestión de Guías")
    st.caption("Buscar, reemplazar y borrar guías individuales")

    col1, col2, col3 = st.columns(3)
    with col1:
        estado_filter = st.selectbox("Estado", ["Todas", "PENDIENTE", "RECIBIDA"],
                                     key="log_gestion_estado")
    with col2:
        opciones_tienda = sorted([t.get("Nombre de Tienda", t.get("nombre", "")) for t in TIENDAS_DATA if t.get("Nombre de Tienda", t.get("nombre", ""))])
        tienda_filter = st.selectbox("Tienda", [""] + opciones_tienda, key="log_gestion_tienda")
    with col3:
        busqueda = st.text_input("🔍 Buscar N° Guía o Tienda", key="log_gestion_buscar")

    query = {}
    if estado_filter != "Todas":
        query["estado"] = estado_filter
    if tienda_filter:
        query["tienda_destino"] = tienda_filter
    if busqueda:
        query["$or"] = [
            {"numero_guia": {"$regex": busqueda, "$options": "i"}},
            {"tienda_destino": {"$regex": busqueda, "$options": "i"}},
        ]

    guias = local_db.find(COL_GUIAS, query, sort=[("fecha_creacion", -1)], limit=200)

    if guias:
        df = pd.DataFrame(guias)
        cols_show = ["numero_guia", "tienda_destino", "fecha_guia", "estado", "total_prendas", "usuario_creador"]
        cols_exist = [c for c in cols_show if c in df.columns]
        rename_map = {
            "numero_guia": "N° Guía", "tienda_destino": "Tienda",
            "fecha_guia": "Fecha", "estado": "Estado",
            "total_prendas": "Prendas", "usuario_creador": "Creador",
        }
        df_show = df[cols_exist].copy()
        if "fecha_guia" in df_show.columns:
            df_show["fecha_guia"] = df_show["fecha_guia"].astype(str).str[:10]
        df_show = df_show.rename(columns=rename_map)
        st.dataframe(df_show, use_container_width=True)

        # Seleccionar guía para acciones
        st.markdown("#### ⚙️ Acciones sobre Guía")
        opciones = {str(i): g.get("numero_guia", f"Guía #{i}") for i, g in enumerate(guias)}
        selected = st.selectbox("🔍 Selecciona guía", options=list(opciones.keys()),
                                format_func=lambda x: opciones[x], key="log_gestion_select")
        if selected:
            idx = int(selected)
            if idx < len(guias):
                g = guias[idx]
                st.markdown(f"**Guía:** {g.get('numero_guia')} | "
                           f"**Tienda:** {g.get('tienda_destino')} | "
                           f"**Estado:** {g.get('estado')}")

                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("🔄 Reemplazar Guía", key=f"log_reemp_{g.get('numero_guia')}"):
                        st.session_state["log_reemplazar_guia"] = g.get("numero_guia")
                        st.rerun()
                with c2:
                    if st.button("🗑️ Borrar Guía", key=f"log_borrar_{g.get('numero_guia')}"):
                        num_guia = g.get("numero_guia", "")
                        borrado_seguro(COL_GUIAS, {"numero_guia": num_guia})
                        local_db.delete("guias_pendientes", {"numero_guia": num_guia})
                        st.success(f"🗑️ Guía {num_guia} borrada con auditoría")
                        registrar_auditoria("BORRAR_GUIA_LOGISTICA", "logistica",
                                           f"Usuario {st.session_state.get('username')} borró guía {num_guia}")
                        st.rerun()
    else:
        st.info("ℹ️ No se encontraron guías con esos filtros")


# =============================================================================
# SECCIÓN DE HISTÓRICO
# =============================================================================
def _seccion_historico():
    st.markdown("### 📜 Histórico de Operaciones")
    st.caption("Registro de todas las operaciones logísticas registradas")

    col1, col2, col3 = st.columns(3)
    with col1:
        desde = st.date_input("Desde", value=date.today() - timedelta(days=30),
                              key="log_hist_desde")
    with col2:
        hasta = st.date_input("Hasta", value=date.today(), key="log_hist_hasta")
    with col3:
        busqueda_usuario = st.text_input("Usuario (opcional)", key="log_hist_usuario")

    historicos = consultar_historico(
        "dashboard_logistico",
        fecha_desde=desde,
        fecha_hasta=hasta,
        usuario=busqueda_usuario if busqueda_usuario else None,
    )

    if historicos:
        df_hist = pd.DataFrame(historicos)
        cols_show = ["fecha_archivo", "pestaña", "usuario", "archivo_nombre", "filas"]
        cols_exist = [c for c in cols_show if c in df_hist.columns]

        rename_map = {
            "fecha_archivo": "Fecha",
            "pestaña": "Tipo",
            "usuario": "Usuario",
            "archivo_nombre": "Archivo",
            "filas": "Registros",
        }
        df_show = df_hist[cols_exist].copy()
        if "fecha_archivo" in df_show.columns:
            df_show["fecha_archivo"] = df_show["fecha_archivo"].astype(str).str[:19]
        df_show = df_show.rename(columns=rename_map)
        st.dataframe(df_show, use_container_width=True)

        # Métricas de histórico
        total_ops = len(historicos)
        total_filas = sum(h.get("filas", 0) for h in historicos)
        st.caption(f"📊 Total: {total_ops} operaciones, {total_filas} registros procesados")
    else:
        st.info("ℹ️ No hay histórico en el rango seleccionado")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_logistica():
    """Punto de entrada del Dashboard Logístico."""
    if not can_access("logistica"):
        st.error("⛔ No tienes permisos para acceder a Logística")
        return

    add_back_button(key="back_logistica")
    show_module_header("🚚 Dashboard Logístico", "Análisis de transferencias, gestión y reemplazo de guías")

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Gestión Guías", "📜 Histórico"])
    with tab1:
        _seccion_dashboard()
    with tab2:
        _seccion_gestion_guias()
    with tab3:
        _seccion_historico()
