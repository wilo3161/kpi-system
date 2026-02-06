"""
AEROPOSTALE ERP - Página Principal
Sistema de Gestión Empresarial para Centro de Distribución Ecuador

Autor: Wilson Pérez
Versión: 4.0
"""

import streamlit as st
from utils.styles import load_custom_css

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_title="AEROPOSTALE ERP | Control Total",
    page_icon="👔",
    initial_sidebar_state="expanded"
)

# Cargar estilos personalizados
load_custom_css()


def create_module_card(icon, title, description):
    """
    Crea una tarjeta visual de módulo
    
    Args:
        icon: Emoji o ícono del módulo
        title: Título del módulo
        description: Descripción breve del módulo
    """
    st.markdown(f"""
    <div class="module-card">
        <div class="card-icon">{icon}</div>
        <div class="card-title">{title}</div>
        <div class="card-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Función principal de la página de inicio"""
    
    # Encabezado principal
    st.markdown("""
    <div class="gallery-container">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribución Ecuador | ERP v4.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de módulos
    st.markdown('<div class="modules-grid">', unsafe_allow_html=True)
    
    # Definir módulos disponibles
    modulos = [
        {
            "icon": "📊",
            "title": "Dashboard KPIs",
            "description": "Métricas en tiempo real del centro de distribución",
            "page": "pages/1_📊_Dashboard_KPIs.py"
        },
        {
            "icon": "💰",
            "title": "Reconciliación V8",
            "description": "Conciliación financiera de facturas y manifiestos",
            "page": "pages/2_💰_Reconciliación_V8.py"
        },
        {
            "icon": "📧",
            "title": "Email Wilo AI",
            "description": "Auditoría inteligente de correos y novedades",
            "page": "pages/3_📧_Email_Wilo_AI.py"
        },
        {
            "icon": "📦",
            "title": "Dashboard Transferencias",
            "description": "Control logístico y distribución",
            "page": "pages/4_📦_Dashboard_Transferencias.py"
        },
        {
            "icon": "👥",
            "title": "Trabajadores",
            "description": "Gestión del equipo y personal",
            "page": "pages/5_👥_Trabajadores.py"
        },
        {
            "icon": "🚚",
            "title": "Generar Guías",
            "description": "Sistema de envíos con código QR",
            "page": "pages/6_🚚_Generar_Guías.py"
        },
        {
            "icon": "📋",
            "title": "Inventario",
            "description": "Control de stock y existencias",
            "page": "pages/7_📋_Inventario.py"
        },
        {
            "icon": "📈",
            "title": "Reportes",
            "description": "Análisis y estadísticas ejecutivas",
            "page": "pages/8_📈_Reportes.py"
        },
        {
            "icon": "⚙️",
            "title": "Configuración",
            "description": "Ajustes y preferencias del sistema",
            "page": "pages/9_⚙️_Configuración.py"
        }
    ]
    
    # Crear 3 columnas para el grid
    cols = st.columns(3)
    
    for idx, modulo in enumerate(modulos):
        with cols[idx % 3]:
            create_module_card(
                modulo["icon"],
                modulo["title"],
                modulo["description"]
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Sección de información rápida
    st.markdown("### 📌 Acceso Rápido")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>📦</div>
            <div class='stat-title'>Productividad Hoy</div>
            <div class='stat-value'>1,247</div>
            <div class='stat-change'>+12.5%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>⚡</div>
            <div class='stat-title'>Eficiencia</div>
            <div class='stat-value'>94.2%</div>
            <div class='stat-change'>+0.8%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>👥</div>
            <div class='stat-title'>Personal Activo</div>
            <div class='stat-value'>42</div>
            <div class='stat-change'>+2</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>🚚</div>
            <div class='stat-title'>Guías Hoy</div>
            <div class='stat-value'>156</div>
            <div class='stat-change'>+8</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Footer
    st.markdown("""
    <div class="app-footer">
        <p>Sistema ERP v4.0 • Desarrollado por Wilson Pérez • Logística & Sistemas</p>
        <p style="font-size: 0.8rem; color: #64748B; margin-top: 10px;">
            © 2024 AEROPOSTALE Ecuador • Todos los derechos reservados
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con información adicional
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-title">AERO ERP</div>
            <div class="sidebar-subtitle">v4.0 • Wilson Pérez</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 📋 Navegación")
        st.info("👈 Selecciona un módulo de la página principal o usa el menú lateral")
        
        st.divider()
        
        st.markdown("### ℹ️ Información")
        st.write("**Versión:** 4.0")
        st.write("**Última actualización:** 2024-02-06")
        st.write("**Estado:** ✅ Operativo")
        
        st.divider()
        
        st.markdown("### 🔗 Enlaces Rápidos")
        st.markdown("- 📊 [Dashboard KPIs](1_📊_Dashboard_KPIs)")
        st.markdown("- 💰 [Reconciliación](2_💰_Reconciliación_V8)")
        st.markdown("- 📧 [Email AI](3_📧_Email_Wilo_AI)")
        
        st.divider()
        
        st.markdown("### 👨‍💼 Usuario")
        st.write("**Wilson Pérez**")
        st.write("Jefe de Logística")


if __name__ == "__main__":
    main()
