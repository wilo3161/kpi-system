"""
Generador de Guías de Envío con QR
"""

import streamlit as st
import numpy as np
from datetime import datetime
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="Generar Guías | AEROPOSTALE ERP", page_icon="🚚")
load_custom_css()

def main():
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>🚚 GENERADOR DE GUÍAS</h1>
        <div class='header-subtitle'>Sistema de envíos con seguimiento QR</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_guia"):
        col_guia1, col_guia2 = st.columns(2)
        
        with col_guia1:
            st.subheader("🏢 Información Remitente")
            remitente = st.selectbox("Remitente", ["Wilson Pérez", "Luis Perugachi", "Andrés Cadena"])
            marca = st.radio("Marca", ["Fashion Club", "Tempo"], horizontal=True)
        
        with col_guia2:
            st.subheader("🏪 Información Destinatario")
            destinatario = st.text_input("Nombre destinatario")
            telefono = st.text_input("Teléfono")
        
        direccion = st.text_area("Dirección completa", height=100)
        
        col_guia3, col_guia4, col_guia5 = st.columns(3)
        
        with col_guia3:
            tienda_destino = st.selectbox("Tienda destino", ["Mall del Sol", "Price Club", "Tienda Web", "Ventas Mayor"])
        
        with col_guia4:
            piezas = st.number_input("Número de piezas", min_value=1, value=1)
        
        with col_guia5:
            urgente = st.checkbox("Envío urgente")
        
        url_seguimiento = st.text_input("URL seguimiento", "https://aeropostale.com.ec/seguimiento/")
        
        generar = st.form_submit_button("📄 Generar Guía PDF", type="primary", use_container_width=True)
    
    if generar and destinatario:
        with st.spinner("🔄 Generando guía..."):
            import time
            time.sleep(2)
            
            numero_guia = f"GFC-{np.random.randint(1000, 9999)}"
            
            st.success(f"✅ Guía {numero_guia} generada exitosamente")
            
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.markdown("### 📋 Resumen de Guía")
                st.write(f"**Número:** {numero_guia}")
                st.write(f"**Remitente:** {remitente}")
                st.write(f"**Destinatario:** {destinatario}")
                st.write(f"**Tienda:** {tienda_destino}")
                st.write(f"**Piezas:** {piezas}")
                st.write(f"**Urgente:** {'Sí' if urgente else 'No'}")
            
            with col_res2:
                st.markdown("### 📍 Información de Envío")
                st.write(f"**Dirección:** {direccion}")
                st.write(f"**Teléfono:** {telefono}")
                st.write(f"**Seguimiento:** {url_seguimiento}{numero_guia}")
                st.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            st.divider()
            
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            with col_btn1:
                st.button("📥 Descargar PDF", use_container_width=True)
            with col_btn2:
                st.button("📧 Enviar por Email", use_container_width=True)
            with col_btn3:
                st.button("🖨️ Imprimir", use_container_width=True)

if __name__ == "__main__":
    main()
