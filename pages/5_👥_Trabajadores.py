"""
Gestión de Trabajadores y Personal
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.styles import load_custom_css

st.set_page_config(layout="wide", page_title="Gestión Trabajadores | AEROPOSTALE ERP", page_icon="👥")
load_custom_css()

def main():
    st.markdown("""
    <div class='internal-header'>
        <h1 class='header-title'>👥 GESTIÓN DE EQUIPO</h1>
        <div class='header-subtitle'>Administración del personal del Centro de Distribución</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab_equipo1, tab_equipo2, tab_equipo3 = st.tabs(["🏢 Estructura", "➕ Agregar", "📊 Estadísticas"])
    
    with tab_equipo1:
        # Estructura organizacional
        estructura = {
            'Liderazgo': ['Wilson Pérez - Jefe Logística', 'Andrés Cadena - Jefe Inventarios'],
            'Transferencias': ['César Yépez - Transferencias Fashion', 'Luis Perugachi - Pivote Price', 'Josué Imbacuán - Transferencias Tempo'],
            'Distribución': ['Jessica Suárez - Distribución Aero', 'Norma Paredes - Distribución Price', 'Jhonny Villa - Empaque'],
            'Ventas Mayor': ['Jhonny Guadalupe - Bodega Packing', 'Rocio Cadena - Picking'],
            'Calidad': ['Diana García - Reproceso']
        }
        
        for departamento, personal in estructura.items():
            with st.expander(f"📌 {departamento} ({len(personal)} personas)", expanded=True):
                for persona in personal:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {persona}")
                    with col2:
                        st.button("👁️", key=f"ver_{persona}", help="Ver detalles")
    
    with tab_equipo2:
        # Formulario para agregar personal
        with st.form("form_personal"):
            col_per1, col_per2 = st.columns(2)
            
            with col_per1:
                nombre = st.text_input("Nombre completo")
                cargo = st.selectbox("Cargo", ["Operador", "Supervisor", "Coordinador", "Gerente"])
            
            with col_per2:
                departamento = st.selectbox("Departamento", ["Logística", "Almacén", "Ventas", "Administración"])
                fecha_ingreso = st.date_input("Fecha de ingreso")
            
            if st.form_submit_button("➕ Agregar Personal", type="primary"):
                st.success(f"✅ {nombre} agregado al equipo")
    
    with tab_equipo3:
        # Estadísticas del equipo
        col_est1, col_est2, col_est3, col_est4 = st.columns(4)
        
        with col_est1:
            st.metric("Total Personal", "42")
        
        with col_est2:
            st.metric("Activos", "40", "+2")
        
        with col_est3:
            st.metric("Rotación", "4.8%", "-0.5%")
        
        with col_est4:
            st.metric("Satisfacción", "8.7/10", "+0.3")

if __name__ == "__main__":
    main()
