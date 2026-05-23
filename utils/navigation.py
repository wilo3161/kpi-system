"""
Navegación centralizada para el ERP Aeropostale.
Única fuente de verdad para cambios de página.
# FIX [NAV] - Centralización de navegación para evitar doble-render - Mayo 2026
"""
import streamlit as st


def navigate_to(page: str) -> None:
    """
    Cambia la página actual del ERP.
    Esta es la ÚNICA función que debe modificar st.session_state.current_page.
    
    Args:
        page: Clave de la página destino (ej: "Inicio", "dashboard_kpis", etc.)
    """
    st.session_state.current_page = page
    st.rerun()


def go_home() -> None:
    """Navega al home/inicio del sistema."""
    navigate_to("Inicio")


def get_current_page() -> str:
    """Retorna la página actual desde session_state."""
    return st.session_state.get("current_page", "Inicio")
