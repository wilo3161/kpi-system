# utils/login_theme.py
"""Estilos exclusivos para la página de inicio de sesión con fondo responsivo."""

import streamlit as st

def inject_login_css(background_image_url: str = None):
    """
    Inyecta CSS para un login con fondo de pantalla completa.
    
    Args:
        background_image_url: URL o ruta local de la imagen de fondo.
                              Si es None, se usará un color sólido oscuro.
    """
    # Si no se proporciona imagen, usamos un color de respaldo
    if background_image_url is None:
        background_image_url = "https://placehold.co/1920x1080/111/white?text=Aeropostale"
    
    st.markdown(f"""
    <style>
    /* Eliminar elementos por defecto de Streamlit */
    [data-testid="stHeader"], [data-testid="stToolbar"], footer {{
        display: none !important;
    }}

    /* Fondo de pantalla completa responsivo */
    .stApp {{
        background-image: url('{background_image_url}');
        background-size: cover;        /* La imagen cubre todo sin deformarse (puede recortar bordes) */
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;  /* Fijo al hacer scroll */
    }}

    /* Ajuste para pantallas muy anchas (evita que la imagen se "estire" horizontalmente) */
    @media (min-aspect-ratio: 16/9) {{
        .stApp {{
            background-size: cover;
        }}
    }}

    /* Si prefieres ver la imagen completa sin recortes (pero puede dejar franjas negras),
       descomenta la línea de abajo y comenta la de background-size: cover */
    /* .stApp {{ background-size: contain; }} */

    /* Panel izquierdo del login (sobre el fondo) */
    div[data-testid="column"]:first-of-type {{
        background: rgba(15, 15, 20, 0.92) !important;
        padding: 4rem !important;
        border-radius: 0 30px 30px 0 !important;
        box-shadow: 25px 0 70px rgba(0,0,0,0.9) !important;
        backdrop-filter: blur(2px);    /* pequeño desenfoque para mejorar legibilidad */
        z-index: 10;
    }}

    /* Títulos y textos */
    .login-title {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 4.5rem;
        letter-spacing: 0.05em;
        color: #FFFFFF;
    }}
    .login-subtitle {{
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        color: #DDDDDD;
    }}

    /* Inputs del formulario */
    div[data-testid="column"]:first-of-type .stTextInput > div > div > input {{
        background: #1A1A1A !important;
        border: 1.5px solid #333333 !important;
        border-radius: 6px !important;
        color: #CCCCCC !important;
        padding: 13px 18px !important;
        font-size: 0.95rem !important;
        height: 52px !important;
    }}
    div[data-testid="column"]:first-of-type .stTextInput > div > div > input:focus {{
        border-color: #CF0A2C !important;
        box-shadow: 0 0 0 2px rgba(207,10,44,0.12) !important;
    }}

    /* Botón de submit */
    div[data-testid="stFormSubmitButton"] > button {{
        background: #A52030 !important;
        border-radius: 6px !important;
        height: 52px !important;
        font-size: 0.85rem !important;
        letter-spacing: .18em !important;
        color: white !important;
        border: none !important;
        width: 100%;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background: #CF0A2C !important;
        box-shadow: 0 6px 24px rgba(207,10,44,0.35) !important;
    }}
    </style>
    """, unsafe_allow_html=True)
