import streamlit as st
import base64
import os
from utils.login_theme import inject_login_css
from utils.common import hash_password

def get_background_base64():
    """Busca la imagen de fondo local; retorna bytes en base64 o None."""
    image_path = "images/background_aeropostale.png"
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            pass
    return None

def get_db():
    """Importación diferida para evitar errores de inicio."""
    from database.manager import get_db_v2
    return get_db_v2()

def check_password():
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return True
    
    inject_login_css()
    bg_base64 = get_background_base64()
    bg_css = f"url('data:image/png;base64,{bg_base64}')" if bg_base64 else "#0A0A0A"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600&display=swap');
    [data-testid="stAppViewContainer"] {{
        background-image: {bg_css} !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        min-height: 100vh !important;
    }}
    [data-testid="stAppViewContainer"] > .main {{ background: transparent !important; backdrop-filter: none !important; }}
    .login-footer {{ text-align: center; margin-top: 2rem; font-family: 'Outfit', sans-serif; font-size: 0.85rem; color: #AAAAAA; letter-spacing: 0.5px; }}
    .login-footer p {{ margin: 0.2rem 0; }}
    .login-footer .est {{ font-family: 'Bebas Neue', sans-serif; font-size: 0.9rem; letter-spacing: 1px; color: #CF0A2C; }}
    .aeropostale-title {{ text-align: center; margin-bottom: 0.5rem; font-family: 'Bebas Neue', sans-serif; font-size: 3.2rem; letter-spacing: 0.05em; color: #FFFFFF; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); -webkit-text-stroke: 0.5px rgba(255,255,255,0.2); }}
    .live-subtitle {{ text-align: center; font-family: 'Outfit', sans-serif; font-size: 1rem; color: #DDDDDD; letter-spacing: 0.1em; margin-top: -0.5rem; margin-bottom: 2rem; text-transform: uppercase; font-weight: 300; }}
    div[data-testid="column"]:first-of-type {{ display: flex; flex-direction: column; align-items: center; }}
    div[data-testid="stForm"] {{ width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])
    with col_left:
        st.markdown('<div style="margin-top: 20vh;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center;">
            <div class="aeropostale-title">AEROPOSTALE</div>
            <div class="live-subtitle">Live Original. Live Aeropostale.</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Usuario", key="login_user")
            password = st.text_input("🔒 Contraseña", type="password", key="login_pass")
            submitted = st.form_submit_button("INGRESAR", use_container_width=True)

            if submitted:
                db = get_db()
                user_data = db.authenticate(username, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = user_data.get("role", "Usuario")
                    st.session_state.user_name = user_data.get("name", username)
                    # ✅ NUEVO: Guardar tienda asignada para filtrado en recepción
                    st.session_state.assigned_store = user_data.get("assigned_store")
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

        st.markdown("""
        <div class="login-footer">
            <p>Designed by Wilson Pérez</p>
            <p class="est">EST.1983</p>
        </div>
        """, unsafe_allow_html=True)

    return False
