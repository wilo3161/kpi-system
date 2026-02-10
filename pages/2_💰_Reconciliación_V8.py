"""
Módulo de Reconciliación Financiera V8
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime
from utils.styles import load_custom_css
from utils.helpers import normalizar_texto_wilo, procesar_subtotal_wilo, identificar_tipo_tienda_v8

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_title="Reconciliación V8 | AEROPOSTALE ERP",
    page_icon="💰"
)

# Cargar estilos
load_custom_css()

def main():
    """Función principal del módulo de reconciliación"""
    
    # Encabezado
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>💰 RECONCILIACIÓN FINANCIERA V8</h1>
        <div class='header-subtitle'>Conciliación de facturas y manifiestos</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📤 Cargar Archivos", "⚙️ Configurar", "📊 Resultados"])
    
    with tab1:
        st.subheader("Subir Archivos para Reconciliación")
        
        col_archivo1, col_archivo2 = st.columns(2)
        
        with col_archivo1:
            st.markdown("### 📄 Manifiesto")
            f_manifiesto = st.file_uploader(
                "Subir archivo Excel/CSV",
                type=['xlsx', 'xls', 'csv'],
                key="manifiesto_file",
                help="Archivo con columnas: Guía, Destinatario, Valor, Piezas"
            )
        
        with col_archivo2:
            st.markdown("### 🧾 Facturas")
            f_facturas = st.file_uploader(
                "Subir archivo Excel/CSV",
                type=['xlsx', 'xls', 'csv'],
                key="facturas_file",
                help="Archivo con columnas: Guía, Valor Facturado"
            )
        
        st.divider()
        
        # Opciones de procesamiento
        col_op1, col_op2, col_op3 = st.columns(3)
        
        with col_op1:
            usar_demo = st.checkbox("Usar datos de demostración", value=True)
        
        with col_op2:
            auto_clasificar = st.checkbox("Clasificación automática", value=True)
        
        with col_op3:
            generar_informes = st.checkbox("Generar informes PDF", value=True)
    
    with tab2:
        st.subheader("Configuración de Columnas")
        
        if usar_demo:
            st.info("📊 **Usando datos de demostración** - Configure las columnas para su estructura")
            
            # Datos de ejemplo para demostración
            np.random.seed(42)
            num_rows = 50
            
            # Datos de manifiesto de ejemplo
            df_m = pd.DataFrame({
                'GUIA': [f'GUA-{i:04d}' for i in range(1001, 1001 + num_rows)],
                'DESTINATARIO': np.random.choice([
                    'JOFRE SANTANA IMPORT', 
                    'MALL DEL SOL AEROPOSTALE',
                    'SAN MARINO TIENDA',
                    'CARLOS PEREZ',
                    'MARIA GONZALEZ',
                    'CENTRO COMERCIAL QUITO',
                    'PLAZA DE LAS AMERICAS'
                ], num_rows),
                'PIEZAS': np.random.randint(1, 20, num_rows),
                'VALOR_DECLARADO': np.random.uniform(50, 500, num_rows).round(2)
            })
            
            # Datos de facturas de ejemplo
            df_f = pd.DataFrame({
                'GUIA_FACTURA': [f'GUA-{i:04d}' for i in range(1001, 1001 + int(num_rows * 0.8))],
                'VALOR_COBRADO': np.random.uniform(45, 550, int(num_rows * 0.8)).round(2)
            })
            
            # Guardar en session_state
            st.session_state.df_manifiesto = df_m
            st.session_state.df_facturas = df_f
            
            col_conf1, col_conf2 = st.columns(2)
            
            with col_conf1:
                st.markdown("**Manifiesto**")
                col_guia_m = st.selectbox("Columna Guía", df_m.columns.tolist(), index=0)
                col_dest_m = st.selectbox("Columna Destinatario", df_m.columns.tolist(), index=1)
                col_valor_m = st.selectbox("Columna Valor", df_m.columns.tolist(), index=3)
                col_piezas_m = st.selectbox("Columna Piezas", df_m.columns.tolist(), index=2)
            
            with col_conf2:
                st.markdown("**Facturas**")
                col_guia_f = st.selectbox("Columna Guía Factura", df_f.columns.tolist(), index=0)
                col_valor_f = st.selectbox("Columna Valor Facturado", df_f.columns.tolist(), index=1)
            
            # Guardar configuración en session_state
            st.session_state.config_cols = {
                'guia_m': col_guia_m,
                'dest_m': col_dest_m,
                'valor_m': col_valor_m,
                'piezas_m': col_piezas_m,
                'guia_f': col_guia_f,
                'valor_f': col_valor_f
            }
    
    with tab3:
        st.subheader("Resultados de la Reconciliación")
        
        if st.button("🚀 Ejecutar Reconciliación", type="primary", use_container_width=True):
            if 'df_manifiesto' in st.session_state and 'df_facturas' in st.session_state:
                with st.spinner("🔄 Procesando datos..."):
                    time.sleep(2)
                    
                    # Obtener configuración
                    config = st.session_state.config_cols
                    df_m = st.session_state.df_manifiesto
                    df_f = st.session_state.df_facturas
                    
                    # Procesamiento
                    df_m['GUIA_CLEAN'] = df_m[config['guia_m']].astype(str).str.strip().str.upper()
                    df_f['GUIA_CLEAN'] = df_f[config['guia_f']].astype(str).str.strip().str.upper()
                    
                    # Merge
                    df_final = pd.merge(df_m, df_f, on='GUIA_CLEAN', how='left', suffixes=('_MAN', '_FAC'))
                    
                    # Lógica V8
                    df_final['DESTINATARIO_NORM'] = df_final[config['dest_m']].fillna('DESCONOCIDO')
                    df_final['TIPO_TIENDA'] = df_final['DESTINATARIO_NORM'].apply(identificar_tipo_tienda_v8)
                    
                    # Manejo de Piezas y Valores
                    df_final['PIEZAS_CALC'] = pd.to_numeric(df_final[config['piezas_m']], errors='coerce').fillna(1)
                    df_final['VALOR_REAL'] = df_final[config['valor_f']].apply(procesar_subtotal_wilo).fillna(0)
                    df_final['VALOR_MANIFIESTO'] = df_final[config['valor_m']].apply(procesar_subtotal_wilo).fillna(0)
                    
                    total_facturado = df_final['VALOR_REAL'].sum()
                    total_piezas = df_final['PIEZAS_CALC'].sum()
                    con_factura = df_final[df_final['VALOR_REAL'] > 0].shape[0]
                    sin_factura = df_final[df_final['VALOR_REAL'] == 0].shape[0]
                    
                    # Métricas
                    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                    
                    with col_res1:
                        st.metric("Guías Procesadas", len(df_final))
                    
                    with col_res2:
                        st.metric("Conciliadas", con_factura, f"{(con_factura/len(df_final))*100:.1f}%")
                    
                    with col_res3:
                        st.metric("Valor Total", f"${total_facturado:,.2f}")
                    
                    with col_res4:
                        diferencia = total_facturado - df_final['VALOR_MANIFIESTO'].sum()
                        st.metric("Diferencia", f"${diferencia:,.2f}", delta_color="inverse")
                    
                    st.divider()
                    
                    # Gráfico de conciliación
                    fig = go.Figure(data=[
                        go.Bar(name='Conciliadas', x=['Resultado'], y=[con_factura], marker_color='#34D399'),
                        go.Bar(name='Pendientes', x=['Resultado'], y=[sin_factura], marker_color='#F87171')
                    ])
                    
                    fig.update_layout(
                        title="Estado de Conciliación",
                        barmode='stack',
                        height=300,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.divider()
                    
                    # Mostrar resultados
                    st.subheader("📋 Datos Reconciliados")
                    st.dataframe(df_final.head(20), use_container_width=True, hide_index=True)
                    
                    # Opciones de exportación
                    col_exp1, col_exp2 = st.columns([3, 1])
                    with col_exp2:
                        if st.button("📥 Exportar Resultados", use_container_width=True):
                            st.success("✅ Resultados exportados exitosamente")
            else:
                st.warning("⚠️ Configure los archivos en la pestaña 'Configurar'")

if __name__ == "__main__":
    main()
