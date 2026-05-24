# app.py
import streamlit as st
from pathlib import Path
import base64
import traceback
from utils.auth import check_password
from utils.ui import show_header, load_css
from modules.main_page import show_main_page

# Importaciones de todos los módulos (con try/except para identificar fallos)
try:
    from modules.reconciliacion import show_reconciliacion_v8
except Exception as e:
    st.error(f"Error importando reconciliacion: {e}")
    show_reconciliacion_v8 = None

try:
    from modules.auditoria import show_gestor_correos
except Exception as e:
    st.error(f"Error importando auditoria: {e}")
    show_gestor_correos = None

try:
    from modules.logistica import show_logistica
except Exception as e:
    st.error(f"Error importando logistica: {e}")
    show_logistica = None

try:
    from modules.kpi_analytics import show_kpi_analytics
except Exception as e:
    st.error(f"Error importando kpi_analytics: {e}")
    show_kpi_analytics = None

try:
    from modules.equipo import show_gestion_equipo
except Exception as e:
    st.error(f"Error importando equipo: {e}")
    show_gestion_equipo = None

try:
    from modules.guias import show_generar_guias
except Exception as e:
    st.error(f"Error importando guias: {e}")
    show_generar_guias = None

try:
    from modules.configuracion import show_configuracion
except Exception as e:
    st.error(f"Error importando configuracion: {e}")
    show_configuracion = None

try:
    from modules.recepcion import show_recepcion_tienda
except Exception as e:
    st.error(f"Error importando recepcion: {e}")
    show_recepcion_tienda = None

try:
    from modules.dashboard_kpis import show_dashboard_kpis
except Exception as e:
    st.error(f"Error importando dashboard_kpis: {e}")
    show_dashboard_kpis = None

# Inventario con fallback
try:
    from modules.inventario import show_control_inventario
    INVENTARIO_DISPONIBLE = True
except Exception as e:
    st.error(f"Error importando inventario: {e}")
    INVENTARIO_DISPONIBLE = False
    def show_control_inventario():
        st.error("❌ Módulo de inventario no disponible.")

st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="collapsed",
)

def main():
    if not check_password():
        return

    # Acceso directo a recepción desde QR (ahora requiere autenticación previa)
    if st.query_params.get("modulo") == "recepcion":
        if show_recepcion_tienda:
            show_recepcion_tienda()
        else:
            st.error("Módulo de recepción no disponible")
        return

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Inicio"

    # Mostrar rol y página actual para depuración
    st.sidebar.info(f"👤 Rol: {st.session_state.get('role', '?')}")
    st.sidebar.info(f"📄 Página: {st.session_state.current_page}")

    # Conexión a BD
    from database.manager import local_db
    if not local_db.connected:
        st.sidebar.error("🔴 Sin conexión a BD")
    else:
        st.sidebar.success("🟢 Conectado a MongoDB")

    # Fondo común
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

    # Mapeo de páginas (solo funciones que se importaron correctamente)
    page_mapping = {
        "Inicio": show_main_page,
    }
    if show_dashboard_kpis:
        page_mapping["dashboard_kpis"] = show_dashboard_kpis
    if show_kpi_analytics:
        page_mapping["kpi_analytics"] = show_kpi_analytics
    if show_reconciliacion_v8:
        page_mapping["reconciliacion"] = show_reconciliacion_v8
        page_mapping["reconciliacion_v8"] = show_reconciliacion_v8
    if show_gestor_correos:
        page_mapping["auditoria_correos"] = show_gestor_correos
    if show_logistica:
        page_mapping["logistica"] = show_logistica
        page_mapping["dashboard_logistico"] = show_logistica
    if show_gestion_equipo:
        page_mapping["equipo"] = show_gestion_equipo
        page_mapping["gestion_equipo"] = show_gestion_equipo
    if show_generar_guias:
        page_mapping["guias"] = show_generar_guias
        page_mapping["generar_guias"] = show_generar_guias
    if show_configuracion:
        page_mapping["configuracion"] = show_configuracion
    if show_recepcion_tienda:
        page_mapping["recepcion"] = show_recepcion_tienda
    if INVENTARIO_DISPONIBLE and show_control_inventario:
        page_mapping["inventario"] = show_control_inventario
        page_mapping["control_inventario"] = show_control_inventario

    current_page = st.session_state.current_page
    if current_page in page_mapping:
        try:
            # Ejecutar el módulo
            page_mapping[current_page]()
        except Exception as e:
            # Registrar el error internamente (ocultar el stack trace al usuario por seguridad)
            import logging
            logging.error(f"Error en {current_page}: {str(e)}")
            logging.error(traceback.format_exc())
            
            st.error(f"❌ **Ha ocurrido un error inesperado en el módulo '{current_page}'**")
            st.warning("Por favor, contacta al administrador del sistema si el problema persiste.")
            # Opcional: botón para volver al inicio
            if st.button("🏠 Volver al inicio"):
                st.session_state.current_page = "Inicio"
                st.rerun()
    else:
        st.error(f"❌ La página '{current_page}' no está disponible.")
        st.info("Páginas disponibles: " + ", ".join(page_mapping.keys()))
        if st.button("Ir a Inicio"):
            st.session_state.current_page = "Inicio"
            st.rerun()

if __name__ == '__main__':
    main()
