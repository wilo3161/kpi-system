"""
Configuración del Sistema
"""

import streamlit as st
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="Configuración | AEROPOSTALE ERP", page_icon="⚙️")
load_custom_css()

def main():
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>⚙️ CONFIGURACIÓN</h1>
        <div class='header-subtitle'>Personalización del sistema ERP</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_conf1, tab_conf2, tab_conf3 = st.tabs(["🏢 General", "👤 Usuarios", "🔒 Seguridad"])
    
    with tab_conf1:
        st.subheader("Configuración General")
        
        col1, col2 = st.columns(2)
        
        with col1:
            empresa = st.text_input("Nombre Empresa", "AEROPOSTALE Ecuador")
            moneda = st.selectbox("Moneda", ["USD", "EUR", "PEN"])
            idioma = st.selectbox("Idioma", ["Español", "Inglés"])
        
        with col2:
            zona_horaria = st.selectbox("Zona Horaria", ["UTC-5 (Ecuador)", "UTC-4", "UTC-3"])
            formato_fecha = st.selectbox("Formato Fecha", ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"])
            tema = st.selectbox("Tema", ["Oscuro", "Claro", "Auto"])
        
        if st.button("💾 Guardar Configuración", type="primary"):
            st.success("✅ Configuración guardada exitosamente")
    
    with tab_conf2:
        st.subheader("Gestión de Usuarios")
        
        st.info("Funcionalidad disponible próximamente")
        
        # Tabla de usuarios de ejemplo
        import pandas as pd
        usuarios_demo = pd.DataFrame({
            'Usuario': ['Wilson Pérez', 'Andrés Cadena', 'Luis Perugachi'],
            'Email': ['wperez@aero.com', 'acadena@aero.com', 'lperugachi@aero.com'],
            'Rol': ['Admin', 'Admin', 'Usuario'],
            'Estado': ['Activo', 'Activo', 'Activo']
        })
        
        st.dataframe(usuarios_demo, use_container_width=True, hide_index=True)
    
    with tab_conf3:
        st.subheader("Configuración de Seguridad")
        
        st.checkbox("Autenticación de dos factores (2FA)", value=False)
        st.checkbox("Requerir cambio de contraseña cada 90 días", value=True)
        st.checkbox("Bloquear después de 5 intentos fallidos", value=True)
        
        st.divider()
        
        st.subheader("Registro de Actividad")
        st.info("Registro de actividades del sistema")
        
        if st.button("📥 Descargar Logs"):
            st.success("✅ Logs descargados")

if __name__ == "__main__":
    main()
