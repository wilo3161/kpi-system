# utils/backgrounds.py
"""Gestión de fondos personalizados por módulo."""
import streamlit as st
from pathlib import Path
import base64

def set_module_background(module_name: str) -> None:
    """
    Establece una imagen de fondo para el módulo actual.
    La imagen debe estar en images/{module_name}.png (o .jpg).
    Si no existe, no hace nada.
    """
    image_path = Path(f"images/{module_name}.png")
    if not image_path.exists():
        image_path = Path(f"images/{module_name}.jpg")
    if not image_path.exists():
        return  # No hay imagen para este módulo

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{img_b64}) !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
