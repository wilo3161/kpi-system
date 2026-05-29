# app.py
import streamlit as st
from pathlib import Path
import base64
import traceback
from utils.auth import check_password
from utils.ui import show_header, load_css
from modules.main_page import show_main_page

# Las importaciones globales de módulos se han eliminado.
# Ahora se utiliza Lazy Loading (Carga Perezosa) en el bloque de despacho principal
# para evitar saturar la memoria RAM en cada reinicio de la interfaz.

st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👕",
    initial_sidebar_state="collapsed",
)

def main():
    if not check_password():
        return

    # Acceso directo a recepción desde QR (ahora requiere autenticación previa)
    if st.query_params.get("modulo") == "recepcion":
        from modules.recepcion import show_recepcion_tienda
        show_recepcion_tienda()
        return

    if "current_page" not in st.session_state:
        if st.session_state.get("role") == "Tienda":
            st.session_state.current_page = "recepcion"
        else:
            st.session_state.current_page = "Inicio"

    # Forzar siempre a recepción si el rol es Tienda
    if st.session_state.get("role") == "Tienda" and st.session_state.current_page != "recepcion":
        st.session_state.current_page = "recepcion"
        st.rerun()

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

    # Mapeo de páginas dinámico (Lazy Loading)
    current_page = st.session_state.current_page
    
    try:
        if current_page == "Inicio":
            from modules.main_page import show_main_page
            show_main_page()
        elif current_page == "dashboard_kpis":
            from modules.dashboard_kpis import show_dashboard_kpis
            show_dashboard_kpis()
        elif current_page == "kpi_analytics":
            from modules.kpi_analytics import show_kpi_analytics
            show_kpi_analytics()
        elif current_page in ["reconciliacion", "reconciliacion_v8"]:
            from modules.reconciliacion import show_reconciliacion_v8
            show_reconciliacion_v8()
        elif current_page == "auditoria_correos":
            from modules.auditoria import show_gestor_correos
            show_gestor_correos()
        elif current_page in ["logistica", "dashboard_logistico"]:
            from modules.logistica import show_logistica
            show_logistica()
        elif current_page in ["equipo", "gestion_equipo"]:
            from modules.equipo import show_gestion_equipo
            show_gestion_equipo()
        elif current_page in ["guias", "generar_guias"]:
            from modules.guias import show_generar_guias
            show_generar_guias()
        elif current_page == "configuracion":
            from modules.configuracion import show_configuracion
            show_configuracion()
        elif current_page == "recepcion":
            from modules.recepcion import show_recepcion_tienda
            show_recepcion_tienda()
        elif current_page in ["inventario", "control_inventario"]:
            from modules.inventario import show_control_inventario
            show_control_inventario()
        else:
            st.error(f"❌ La página '{current_page}' no está disponible.")
            if st.button("Ir a Inicio"):
                st.session_state.current_page = "Inicio"
                st.rerun()
    except Exception as e:
        import logging
        import traceback
        logging.error(f"Error en {current_page}: {str(e)}")
        logging.error(traceback.format_exc())
        
        st.error(f"❌ **Ha ocurrido un error inesperado en el módulo '{current_page}'**")
        st.warning("Por favor, contacta al administrador del sistema si el problema persiste.")
        if st.button("🏠 Volver al inicio"):
            st.session_state.current_page = "Inicio"
            st.rerun()

if __name__ == '__main__':
    main()
