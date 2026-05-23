"""
app.py — AEROPOSTALE ERP SYSTEM (v3 CONECTADO COMPLETO)
=========================================================
- Todos los módulos enlazados sin errores
- Navegación protegida por roles
- Seed automático en cada inicio
"""

import streamlit as st
from datetime import datetime

from utils.auth import verificar_login, mostrar_login
from utils.ui import load_css
from utils.roles import can_access, navigate_to_module, ensure_all_store_users

st.set_page_config(
    page_title="AEROPOSTALE ERP",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()

# Seed automático de usuarios de tienda + datos demo (solo primera vez)
if "seed_done" not in st.session_state:
    try:
        ensure_all_store_users()
        from scripts.seed_demo_data import seed_demo_all
        seed_demo_all()
    except Exception:
        pass
    st.session_state.seed_done = True

# Login
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.assigned_store = ""

if not st.session_state.authenticated:
    mostrar_login()
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5e/Aeropostale_Logo.svg",
                 width=150)

st.sidebar.markdown(f"""
👤 **{st.session_state.get('username', '')}**
🔑 {st.session_state.get('role', '')}
""")
if st.session_state.get("assigned_store"):
    st.sidebar.markdown(f"🏪 {st.session_state.assigned_store}")

st.sidebar.markdown("---")

MODULES = [
    ("📊", "Dashboard Principal", "dashboard_kpis"),
    ("📈", "KPI Analytics", "kpi_analytics"),
    ("🔗", "Reconciliación", "reconciliacion"),
    ("📬", "Auditoría Correos", "auditoria_correos"),
    ("🚚", "Logística", "logistica"),
    ("👥", "Equipo", "equipo"),
    ("📦", "Guías", "guias"),
    ("📦", "Inventario", "inventario"),
    ("📬", "Recepción", "recepcion"),
    ("⚙️", "Configuración", "configuracion"),
]

for icon, title, module_key in MODULES:
    if can_access(module_key):
        if st.sidebar.button(f"{icon} {title}", key=f"nav_{module_key}", use_container_width=True):
            navigate_to_module(module_key)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    for k in ["authenticated", "username", "role", "assigned_store", "current_page"]:
        st.session_state.pop(k, None)
    st.rerun()

st.sidebar.caption(f"v3.0 — {datetime.now().strftime('%H:%M')}")

# =============================================================================
# MAIN ROUTER
# =============================================================================
current_page = st.session_state.get("current_page", "dashboard_kpis")

PAGES = {
    "dashboard_kpis": ("modules.main_page", "show_main_page"),
    "kpi_analytics": ("modules.kpi_analytics", "show_kpi_analytics"),
    "reconciliacion": ("modules.reconciliacion", "show_reconciliacion"),
    "auditoria_correos": ("modules.reconciliacion", "show_auditoria_correos"),  # reutiliza reconciliacion
    "logistica": ("modules.logistica", "show_logistica"),
    "equipo": ("modules.equipo", "show_equipo"),
    "guias": ("modules.guias", "show_guias"),
    "inventario": ("modules.inventario", "show_control_inventario"),
    "recepcion": ("modules.recepcion", "show_recepcion"),
    "configuracion": ("modules.configuracion", "show_configuracion"),
}

if current_page in PAGES:
    mod_path, func_name = PAGES[current_page]
    try:
        import importlib
        mod = importlib.import_module(mod_path)
        getattr(mod, func_name)()
    except ImportError as e:
        st.error(f"⚠️ Módulo no encontrado: {mod_path} ({e})")
        from modules.main_page import show_main_page
        show_main_page()
    except Exception as e:
        st.error(f"⚠️ Error al cargar {current_page}: {str(e)}")
        from modules.main_page import show_main_page
        show_main_page()
else:
    from modules.main_page import show_main_page
    show_main_page()
