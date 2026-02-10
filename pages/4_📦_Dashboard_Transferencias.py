"""
Dashboard de Transferencias y Logística
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="Dashboard Transferencias | AEROPOSTALE ERP", page_icon="📦")
load_custom_css()

def main():
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>📦 DASHBOARD LOGÍSTICO</h1>
        <div class='header-subtitle'>Control de transferencias y distribución</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Subir archivo de transferencias
    archivo_transferencias = st.file_uploader("📂 Subir archivo de transferencias (Excel)", type=['xlsx'], key="transferencias_file")
    
    usar_demo = st.checkbox("Usar datos de demostración", value=True)
    
    if archivo_transferencias or usar_demo:
        # Datos de demostración
        categorias = ['Tiendas', 'Price Club', 'Ventas Mayor', 'Tienda Web', 'Fallas', 'Fundas']
        unidades = [1250, 850, 320, 180, 75, 450]
        
        col_log1, col_log2 = st.columns([2, 1])
        
        with col_log1:
            # Gráfico de distribución
            fig = px.pie(values=unidades, names=categorias, title="Distribución por Categoría",
                        color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_log2:
            st.subheader("📊 Resumen")
            for cat, uni in zip(categorias, unidades):
                st.metric(cat, f"{uni:,}", delta=f"{uni/sum(unidades)*100:.1f}%")
        
        st.divider()
        
        # Tabla detallada
        st.subheader("📋 Detalle de Transferencias")
        
        data_detalle = {
            'Secuencial': [f'TRF-{i:04d}' for i in range(1001, 1021)],
            'Destino': ['Mall del Sol', 'Price Club', 'Ventas Mayor', 'Tienda Web'] * 5,
            'Categoría': ['Tiendas', 'Price Club', 'Ventas Mayor', 'Tienda Web'] * 5,
            'Unidades': np.random.randint(10, 500, 20),
            'Estado': ['Completada', 'En tránsito', 'Pendiente'] * 7,
            'Fecha': [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(20)]
        }
        
        df_detalle = pd.DataFrame(data_detalle)
        st.dataframe(df_detalle, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
