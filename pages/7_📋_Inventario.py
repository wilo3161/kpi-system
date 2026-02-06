"""
Control de Inventario
"""

import streamlit as st
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="Inventario | AEROPOSTALE ERP", page_icon="📋")
load_custom_css()

def main():
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>📋 CONTROL DE INVENTARIO</h1>
        <div class='header-subtitle'>Gestión de stock en tiempo real</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🚧 **Módulo en desarrollo** - Próximamente disponible")
    
    st.markdown("### Funcionalidades Planificadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - ✅ Control de existencias
        - ✅ Alertas de stock bajo
        - ✅ Reportes de rotación
        - ✅ Valorización de inventario
        """)
    
    with col2:
        st.markdown("""
        - ✅ Trazabilidad de productos
        - ✅ Auditorías de inventario
        - ✅ Integración con transferencias
        - ✅ Dashboard analítico
        """)

if __name__ == "__main__":
    main()
