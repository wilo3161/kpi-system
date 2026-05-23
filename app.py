"""
app.py — AEROPOSTALE ERP SYSTEM (v2 CORREGIDA)
===============================================
- Control total por roles (Administrador, Bodega, Tienda, Ventas)
- Navegación protegida por permisos
- Seed automático de usuarios
- Login con fondo personalizado
- Optimización de memoria
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import base64

from utils.auth import verificar_login, mostrar_login
from utils.ui import load_css, agregar_logo
from utils.roles import can_access, navigate_to_module, ensure_all_store_users
from utils.login_theme import aplicar_theme_login

# from database.manager import local_db  # solo si necesitas algo al inicio

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(
    page_title="AEROPOSTALE ERP",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
aplicar_theme_login()

# =============================================================================
# SEED AUTOMÁTICO DE USUARIOS DE TIENDA (solo primera vez que se ejecuta)
# =============================================================================
if "seed_done" not in st.session_state:
    try:
        ensure_all_store_users()
    except Exception:
        pass
    st.session_state.seed_done = True

# =============================================================================
# LOGIN
# =============================================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.assigned_store = ""

if not st.session_state.authenticated:
    mostrar_login()
    st.stop()

# =============================================================================
# SIDEBAR — Navegación por Roles
# =============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5e/Aeropostale_Logo.svg",
                 width=150, use_container_width=False)

st.sidebar.markdown(f"""
👤 **Usuario:** {st.session_state.get('username', '')}
🔑 **Rol:** {st.session_state.get('role', '')}
""")

if st.session_state.get("assigned_store"):
    st.sidebar.markdown(f"🏪 **Tienda:** {st.session_state.assigned_store}")

st.sidebar.markdown("---")

# Menú de navegación por módulos — solo muestra los que el rol puede ver
MODULES = [
    ("📊", "Dashboard KPIs", "Dashboard principal con métricas clave", "dashboard_kpis"),
    ("📈", "KPI Analytics", "Análisis avanzado de KPI", "kpi_analytics"),
    ("🔗", "Reconciliación", "Reconciliación de datos", "reconciliacion"),
    ("📬", "Auditoría Correos", "Revisión de correos", "auditoria_correos"),
    ("🚚", "Logística", "Dashboard logístico y gestión de guías", "logistica"),
    ("👥", "Equipo Logístico", "Gestión del equipo logístico", "equipo"),
    ("📦", "Guías de Transferencia", "Crear y gestionar guías", "guias"),
    ("📦", "Control Inventario", "Búsqueda y carga de inventario", "inventario"),
    ("📬", "Recepción de Guías", "Recibir guías en tienda", "recepcion"),
    ("⚙️", "Configuración", "Configuración del sistema", "configuracion"),
]

for icon, title, desc, module_key in MODULES:
    if can_access(module_key):
        if st.sidebar.button(f"{icon} {title}", key=f"nav_{module_key}", use_container_width=True):
            navigate_to_module(module_key)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    for key in ["authenticated", "username", "role", "assigned_store", "current_page"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.sidebar.caption("v2.0 — AEROPOSTALE ERP")

# =============================================================================
# MAIN — Enrutador de páginas
# =============================================================================
current_page = st.session_state.get("current_page", "dashboard_kpis")

if current_page == "dashboard_kpis":
    from modules.main_page import show_main_page
    show_main_page()

elif current_page == "kpi_analytics":
    from modules.dashboard_kpis import show_kpi_analytics
    show_kpi_analytics()

elif current_page == "reconciliacion":
    st.info("🔗 Módulo de Reconciliación — Próximamente")

elif current_page == "auditoria_correos":
    st.info("📬 Módulo de Auditoría de Correos — Próximamente")

elif current_page == "logistica":
    from modules.logistica import show_logistica
    show_logistica()

elif current_page == "equipo":
    equipo_importado = False
    try:
        from modules.equipo_logistico import show_equipo_logistico
        show_equipo_logistico()
        equipo_importado = True
    except ImportError:
        pass
    if not equipo_importado:
        st.info("👥 Módulo de Equipo Logístico — Próximamente")

elif current_page == "guias":
    from modules.guias import show_guias
    show_guias()

elif current_page == "inventario":
    from modules.inventario import show_control_inventario
    show_control_inventario()

elif current_page == "recepcion":
    from modules.recepcion import show_recepcion
    show_recepcion()

elif current_page == "configuracion":
    st.info("⚙️ Módulo de Configuración — Próximamente")

else:
    from modules.main_page import show_main_page
    show_main_page()
