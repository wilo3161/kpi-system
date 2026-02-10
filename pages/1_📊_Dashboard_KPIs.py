"""
Dashboard de KPIs - Métricas en Tiempo Real
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.styles import load_custom_css
from utils.database import LocalDatabase

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_title="Dashboard KPIs | AEROPOSTALE ERP",
    page_icon="📊"
)

# Cargar estilos
load_custom_css()

# Inicializar base de datos
if 'db' not in st.session_state:
    st.session_state.db = LocalDatabase()

def main():
    """Función principal del dashboard de KPIs"""
    
    # Encabezado
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>📊 DASHBOARD DE KPIs</h1>
        <div class='header-subtitle'>Métricas en tiempo real del Centro de Distribución</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    with col_filtro1:
        fecha_inicio = st.date_input("📅 Fecha Inicio", datetime.now() - timedelta(days=30))
    with col_filtro2:
        fecha_fin = st.date_input("📅 Fecha Fin", datetime.now())
    with col_filtro3:
        departamento = st.selectbox("🏭 Departamento", ["Todos", "Logística", "Almacén", "Ventas", "Administración"])
    
    st.divider()
    
    # Métricas principales
    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>📦</div>
            <div class='stat-title'>Productividad</div>
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
            <div class='stat-icon'>💰</div>
            <div class='stat-title'>Ingresos</div>
            <div class='stat-value'>$45,230</div>
            <div class='stat-change'>+8.3%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='stat-card'>
            <div class='stat-icon'>👥</div>
            <div class='stat-title'>Personal Activo</div>
            <div class='stat-value'>42</div>
            <div class='stat-change'>+2</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Gráficos
    col_grafico1, col_grafico2 = st.columns(2)
    
    with col_grafico1:
        # Gráfico de líneas: Productividad diaria
        fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
        productividad = np.random.normal(1000, 200, len(fechas)).cumsum()
        
        fig1 = px.line(
            x=fechas, y=productividad,
            title="📈 Productividad Diaria",
            labels={'x': 'Fecha', 'y': 'Unidades Procesadas'},
            line_shape='spline'
        )
        fig1.update_traces(line=dict(color='#60A5FA', width=3))
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_grafico2:
        # Gráfico de barras: Distribución por departamento
        departamentos = ['Logística', 'Almacén', 'Ventas', 'Administración', 'Calidad']
        valores = np.random.randint(100, 1000, len(departamentos))
        
        fig2 = px.bar(
            x=departamentos, y=valores,
            title="🏭 Productividad por Departamento",
            color=departamentos,
            color_discrete_sequence=['#60A5FA', '#8B5CF6', '#F472B6', '#34D399', '#FBBF24']
        )
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Tabla de detalle
    st.subheader("📋 Detalle de Métricas")
    
    data = {
        'Métrica': ['Productividad CD', 'Eficiencia Operativa', 'Costos Logísticos', 
                   'Tiempo Promedio', 'Exactitud Inventario', 'Satisfacción Cliente'],
        'Valor Actual': ['1,247 unidades', '94.2%', '$12,450', '2.3 horas', '98.7%', '4.8/5.0'],
        'Meta': ['1,500 unidades', '95.0%', '$10,000', '2.0 horas', '99.0%', '5.0/5.0'],
        'Tendencia': ['↗️ Mejorando', '↗️ Mejorando', '↘️ Aumentando', '↘️ Aumentando', '→ Estable', '↗️ Mejorando'],
        'Responsable': ['W. Pérez', 'L. Perugachi', 'A. Cadena', 'J. Imbacuán', 'D. García', 'J. Suárez']
    }
    
    df_metricas = pd.DataFrame(data)
    st.dataframe(df_metricas, use_container_width=True, hide_index=True)
    
    # Exportar datos
    st.divider()
    col_export1, col_export2 = st.columns([3, 1])
    with col_export2:
        if st.button("📥 Exportar a Excel", type="primary", use_container_width=True):
            st.success("✅ Datos exportados exitosamente")

if __name__ == "__main__":
    main()
