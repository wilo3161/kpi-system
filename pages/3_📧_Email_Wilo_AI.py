"""
Email Wilo AI - Auditoría Inteligente de Correos
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from utils.styles import load_custom_css

# Configuración de la página
st.set_page_config(
    layout="wide",
    page_title="Email Wilo AI | AEROPOSTALE ERP",
    page_icon="📧"
)

# Cargar estilos
load_custom_css()

def main():
    """Función principal del módulo de auditoría de correos"""
    
    # Encabezado
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>📧 EMAIL WILO AI</h1>
        <div class='header-subtitle'>Auditoría inteligente de correos y novedades</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuración de conexión
    with st.expander("⚙️ Configuración de Correo", expanded=True):
        col_cfg1, col_cfg2 = st.columns(2)
        
        with col_cfg1:
            email_user = st.text_input("📧 Correo electrónico", "wperez@fashionclub.com.ec")
            imap_server = st.text_input("🌐 Servidor IMAP", "mail.fashionclub.com.ec")
        
        with col_cfg2:
            email_pass = st.text_input("🔒 Contraseña", type="password", value="demo123")
            carpeta = st.selectbox("📁 Carpeta", ["INBOX", "Novedades", "Clientes", "Proveedores"])
    
    st.divider()
    
    # Botón para iniciar auditoría
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        st.info(f"**Servidor:** {imap_server} | **Usuario:** {email_user}")
    
    with col_btn2:
        iniciar_auditoria = st.button("🔍 Iniciar Auditoría", type="primary", use_container_width=True)
    
    if iniciar_auditoria:
        with st.spinner("🔍 Analizando bandeja de entrada..."):
            time.sleep(3)
            
            # Datos de demostración
            datos_auditoria = [
                {
                    'Fecha': '2024-01-15 09:30',
                    'Remitente': 'cliente@empresa.com',
                    'Asunto': 'Faltante en pedido #12345',
                    'Tipo': '📦 FALTANTE',
                    'Urgencia': 'ALTA',
                    'Pedido': '#12345',
                    'Estado': 'Pendiente'
                },
                {
                    'Fecha': '2024-01-15 10:15',
                    'Remitente': 'tienda@mall.com',
                    'Asunto': 'Sobrante en entrega',
                    'Tipo': '👔 SOBRANTE',
                    'Urgencia': 'MEDIA',
                    'Pedido': '#12346',
                    'Estado': 'En revisión'
                },
                {
                    'Fecha': '2024-01-15 11:45',
                    'Remitente': 'soporte@aeropostale.com',
                    'Asunto': 'Re: Etiquetas dañadas',
                    'Tipo': '⚠️ DAÑO',
                    'Urgencia': 'ALTA',
                    'Pedido': '#12347',
                    'Estado': 'Urgente'
                },
                {
                    'Fecha': '2024-01-15 14:20',
                    'Remitente': 'ventas@web.com',
                    'Asunto': 'Consulta general',
                    'Tipo': 'ℹ️ GENERAL',
                    'Urgencia': 'BAJA',
                    'Pedido': 'N/A',
                    'Estado': 'Atendido'
                },
                {
                    'Fecha': '2024-01-15 15:30',
                    'Remitente': 'logistica@proveedor.com',
                    'Asunto': 'Retraso en envío #12348',
                    'Tipo': '🚚 LOGÍSTICA',
                    'Urgencia': 'MEDIA',
                    'Pedido': '#12348',
                    'Estado': 'En proceso'
                }
            ]
            
            df_auditoria = pd.DataFrame(datos_auditoria)
            
            st.success("✅ Análisis completado")
            
            # Métricas
            st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
            
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            
            with col_met1:
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-icon'>📧</div>
                    <div class='stat-title'>Correos Analizados</div>
                    <div class='stat-value'>{len(df_auditoria)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met2:
                altas = len(df_auditoria[df_auditoria['Urgencia'] == 'ALTA'])
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-icon'>🚨</div>
                    <div class='stat-title'>Urgencias Altas</div>
                    <div class='stat-value'>{altas}</div>
                    <div class='stat-change {'negative' if altas > 2 else ''}'>{'Revisar' if altas > 2 else 'OK'}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met3:
                faltantes = len(df_auditoria[df_auditoria['Tipo'].str.contains('FALTANTE')])
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-icon'>📦</div>
                    <div class='stat-title'>Faltantes</div>
                    <div class='stat-value'>{faltantes}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met4:
                pendientes = len(df_auditoria[df_auditoria['Estado'] == 'Pendiente'])
                st.markdown(f"""
                <div class='stat-card'>
                    <div class='stat-icon'>⏳</div>
                    <div class='stat-title'>Pendientes</div>
                    <div class='stat-value'>{pendientes}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.divider()
            
            # Filtros
            col_filtro1, col_filtro2 = st.columns(2)
            with col_filtro1:
                filtro_tipo = st.multiselect("Filtrar por tipo", df_auditoria['Tipo'].unique())
            with col_filtro2:
                filtro_urgencia = st.multiselect("Filtrar por urgencia", df_auditoria['Urgencia'].unique())
            
            # Aplicar filtros
            df_filtrado = df_auditoria.copy()
            if filtro_tipo:
                df_filtrado = df_filtrado[df_filtrado['Tipo'].isin(filtro_tipo)]
            if filtro_urgencia:
                df_filtrado = df_filtrado[df_filtrado['Urgencia'].isin(filtro_urgencia)]
            
            # Tabla de resultados
            st.subheader("📋 Resultados del Análisis")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            
            # Acciones
            st.divider()
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if st.button("📥 Exportar Resultados", use_container_width=True):
                    st.success("✅ Resultados exportados")
            
            with col_act2:
                if st.button("📧 Generar Respuestas", use_container_width=True):
                    st.info("📝 Respuestas generadas automáticamente")
            
            with col_act3:
                if st.button("🔄 Actualizar", use_container_width=True):
                    st.rerun()

if __name__ == "__main__":
    main()
