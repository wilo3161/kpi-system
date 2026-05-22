# app.py
import streamlit as st
from pathlib import Path
import base64
from utils.auth import check_password
from utils.ui import show_header, load_css
from modules.main_page import show_main_page
from database.manager import local_db
from modules.reconciliacion import show_reconciliacion_v8
from modules.auditoria import show_gestor_correos
from modules.logistica import show_logistica
from modules.kpi_analytics import show_kpi_analytics
from modules.equipo import show_gestion_equipo
from modules.guias import show_generar_guias
from modules.configuracion import show_configuracion
from modules.recepcion import show_recepcion_tienda
from modules.dashboard_kpis import show_dashboard_kpis
from modules.almacen import show_almacen

# Módulo de inventario (carga y búsqueda de stock consolidado)
try:
    from modules.inventario import show_control_inventario
    INVENTARIO_DISPONIBLE = True
except ImportError as e:
    INVENTARIO_DISPONIBLE = False
    def show_control_inventario():
        st.error(f"❌ Módulo de inventario no disponible. Error: {e}")

st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed",
)

def main():
    # Acceso directo a recepción desde QR (sin login)
    if st.query_params.get("modulo") == "recepcion":
        show_recepcion_tienda()
        return

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Inicio"

    if not check_password():
        return

    # Estado de BD
    if not local_db.connected:
        error_msg = getattr(local_db, '_connection_error', 'No se pudo conectar a MongoDB Atlas.')
        st.sidebar.error(f"🔴 Sin conexión a BD: {error_msg}")
    else:
        st.sidebar.success("🟢 Conectado a MongoDB Atlas")

    # === FONDO COMÚN (para toda la app después del login) ===
    image_path = Path("images/presentacion.png")
    if image_path.exists():
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{img_b64}) !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    show_header()

    # ----- MAPA DE NAVEGACIÓN ACTUALIZADO -----
    page_mapping = {
        "Inicio": show_main_page,
        "dashboard_kpis": show_dashboard_kpis,
        "kpi_analytics": show_kpi_analytics,
        "reconciliacion_v8": show_reconciliacion_v8,
        "reconciliacion": show_reconciliacion_v8,
        "auditoria_correos": show_gestor_correos,
        "dashboard_logistico": show_logistica,
        "logistica": show_logistica,
        "generar_guias": show_generar_guias,
        "guias": show_generar_guias,
        "configuracion": show_configuracion,
        "gestion_equipo": show_gestion_equipo,
        "equipo": show_gestion_equipo,
        "recepcion": show_recepcion_tienda,
    }

    # Solo agregamos el módulo inventario si está disponible
    page_mapping["almacen"] = show_almacen

    if INVENTARIO_DISPONIBLE:
        page_mapping["control_inventario"] = show_control_inventario
        page_mapping["inventario"] = show_control_inventario

    current_page = st.session_state.get("current_page", "Inicio")
    if current_page in page_mapping:
        try:
            page_mapping[current_page]()
        except Exception as e:
            st.error(f"❌ Error inesperado en el módulo '{current_page}': {e}")
            st.info("Redirigiendo a la página de inicio...")
            st.session_state.current_page = "Inicio"
            st.rerun()
    else:
        st.session_state.current_page = "Inicio"
        st.rerun()

if __name__ == '__main__':
    main()
