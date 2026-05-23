"""
modules/main_page.py — PÁGINA PRINCIPAL AEROPOSTALE ERP (v2 CORREGIDA)
=====================================================================
- Sin recursión infinita
- Muestra solo módulos accesibles según rol
- Tarjetas de acceso rápido
- KPIs resistentes (no rompen si no hay datos)
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.roles import can_access, navigate_to_module
from database.manager import local_db


def create_module_card(icon, title, description, module_key):
    """Crea una tarjeta clicable de módulo, con verificación de permisos."""
    if not can_access(module_key):
        return  # No mostrar si no tiene permiso

    # Usar columna y botón para navegar
    with st.container():
        st.markdown(f"### {icon} {title}")
        st.caption(description)
        if st.button(f"Ir a {title}", key=f"card_{module_key}", use_container_width=True):
            navigate_to_module(module_key)
        st.markdown("---")


def show_main_page():
    """Página principal con bienvenida y KPIs ligeros."""

    st.markdown("# 👕 AEROPOSTALE ERP")
    st.markdown(f"**Bienvenido, {st.session_state.get('username', 'Usuario')}** ({st.session_state.get('role', '')})")
    st.markdown("---")

    # =====================================================================
    # KPIs RÁPIDOS  (no intensivos en recursos)
    # =====================================================================
    st.markdown("### 📊 Resumen Rápido")

    try:
        total_guias = local_db.count_fast("guias", use_cache=True)
        guias_recibidas = local_db.count_fast("guias", {"estado": "RECIBIDA"})
        guias_pendientes = local_db.count_fast("guias", {"estado": "PENDIENTE"})
        total_notificaciones = local_db.count_fast("notificaciones", {"leida": False, "modulo": "guias"})
    except Exception:
        total_guias = guias_recibidas = guias_pendientes = total_notificaciones = 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📦 Guías Totales", total_guias)
    with c2:
        st.metric("✅ Recibidas", guias_recibidas)
    with c3:
        st.metric("⏳ Pendientes", guias_pendientes)
    with c4:
        if total_notificaciones > 0:
            st.metric("🔔 Notificaciones", total_notificaciones)
        else:
            st.metric("🔔 Notificaciones", "0")

    st.markdown("---")

    # =====================================================================
    # MÓDULOS DISPONIBLES  (tarjetas, sin recursión)
    # =====================================================================
    st.markdown("### 🧩 Módulos Disponibles")

    all_modules = [
        ("📊", "Dashboard KPIs", "Métricas principales del negocio", "dashboard_kpis"),
        ("📈", "KPI Analytics", "Análisis detallado de rendimiento", "kpi_analytics"),
        ("🔗", "Reconciliación", "Reconciliación de datos", "reconciliacion"),
        ("📬", "Auditoría Correos", "Revisión de comunicaciones", "auditoria_correos"),
        ("🚚", "Logística", "Dashboard y gestión logística", "logistica"),
        ("👥", "Equipo Logístico", "Personal y contactos", "equipo"),
        ("📦", "Guías de Transferencia", "Generación de guías", "guias"),
        ("📦", "Control Inventario", "Stock y búsqueda", "inventario"),
        ("📬", "Recepción de Guías", "Recibir en tienda", "recepcion"),
        ("⚙️", "Configuración", "Ajustes del sistema", "configuracion"),
    ]

    # Mostrar en grid de 2 columnas
    cols = st.columns(2)
    col_idx = 0
    for icon, title, desc, module_key in all_modules:
        if can_access(module_key):
            with cols[col_idx % 2]:
                create_module_card(icon, title, desc, module_key)
            col_idx += 1

    # Si no hay módulos accesibles
    if col_idx == 0:
        st.warning("⚠️ No tienes módulos asignados. Contacta al administrador.")
