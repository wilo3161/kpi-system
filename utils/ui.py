# utils/ui.py
import streamlit as st
import os
from datetime import datetime

def inject_css_libraries():
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=Rajdhani:wght@500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
    <link href="https://unpkg.com/aos@2.3.4/dist/aos.css" rel="stylesheet">
    <script src="https://unpkg.com/aos@2.3.4/dist/aos.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/TextPlugin.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/typed.js/2.1.0/typed.umd.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/splitting/dist/splitting.css">
    <script src="https://unpkg.com/splitting/dist/splitting.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/hover.css/2.3.1/css/hover-min.css">
    <script>
    (function() {
        const doc = window.parent.document;
        function initAero() {
            if(typeof AOS !== 'undefined') AOS.init({ duration:800, easing:'ease-out-cubic', once:true, offset:80 });
            if(typeof Splitting !== 'undefined') Splitting();
            if(typeof gsap !== 'undefined') gsap.registerPlugin(ScrollTrigger, TextPlugin);
        }
        if (document.readyState === 'complete') initAero();
        else window.addEventListener('load', initAero);
        if (window.aeroInitialized) return;
        window.aeroInitialized = true;
        doc.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-testid="stSidebarNav"] button, [data-testid="stSidebar"] button');
            if (btn) {
                const curtain = doc.getElementById('module-curtain');
                if (curtain) {
                    curtain.classList.remove('exiting');
                    curtain.classList.add('entering');
                    setTimeout(() => {
                        curtain.classList.remove('entering');
                        curtain.classList.add('exiting');
                        setTimeout(() => curtain.classList.remove('exiting'), 600);
                    }, 600);
                }
            }
        }, true);
        doc.addEventListener('keydown', function(e) {
            if ((e.key === 'c' || e.key === 'C') && !e.ctrlKey && !e.altKey && !e.metaKey) {
                const tag = e.target.tagName;
                if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
                    e.stopPropagation();
                }
            }
        }, true);
    })();
    </script>
    """, unsafe_allow_html=True)

def inject_acumatica_css():
    st.markdown("""
    <style>
    /* Acumatica Flat Dashboard Styles */
    .acu-kpi-card {
        display: flex;
        justify-content: space-between;
        padding: 15px 20px;
        color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
        height: 110px;
        box-sizing: border-box;
        margin-bottom: 15px;
        border-radius: 2px;
    }
    .acu-kpi-icon { font-size: 3.5em; display: flex; align-items: center; opacity: 0.9; }
    .acu-kpi-data { text-align: right; display: flex; flex-direction: column; justify-content: center; }
    .acu-kpi-number { font-size: 3em; line-height: 1; margin-bottom: 5px; font-weight: normal; }
    .acu-kpi-label { font-size: 0.75em; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; }
    
    .acu-bg-green { background-color: #27ae60; }
    .acu-bg-red { background-color: #e74c3c; }
    .acu-bg-yellow { background-color: #f39c12; }
    .acu-bg-blue { background-color: #2980b9; }

    .acu-panel {
        background-color: white;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        color: #333;
        border-radius: 2px;
    }
    .acu-panel-header {
        text-transform: uppercase;
        font-size: 0.9em;
        color: #555;
        border-bottom: 1px solid #eee;
        padding: 12px 15px;
        background-color: transparent;
        font-weight: 600;
    }
    .acu-panel table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
    .acu-panel table th { padding: 10px 15px; border-bottom: 1px solid #eee; text-align: left; text-transform: uppercase; color: #777;}
    .acu-panel table td { padding: 10px 15px; border-bottom: 1px solid #f9f9f9; color: #333; }
    .acu-panel table tr:hover { background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

def acu_metric(label, value, color="blue", icon="📊"):
    bg_class = f"acu-bg-{color}"
    return f'''
    <div class="acu-kpi-card {bg_class}">
        <div class="acu-kpi-icon">{icon}</div>
        <div class="acu-kpi-data">
            <span class="acu-kpi-number">{value}</span>
            <span class="acu-kpi-label">{label}</span>
        </div>
    </div>
    '''

def inject_global_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --aero-red:       #E11D48;  /* Rojo cereza premium */
        --aero-navy:      #0B1120;  /* Azul medianoche profundo */
        --aero-blue:      #2563EB;
        --aero-dark:      #080C14;
        --aero-panel:     rgba(30, 41, 59, 0.6);
        --aero-muted:     #94A3B8;
        --aero-red-glow:  rgba(225, 29, 72, 0.3);
        --aero-blue-glow: rgba(37, 99, 235, 0.3);
        --font-hero:    'Bebas Neue', sans-serif;
        --font-heading: 'Rajdhani', sans-serif;
        --font-body:    'Outfit', sans-serif;
        --font-data:    'Space Grotesk', sans-serif;
        --font-mono:    'JetBrains Mono', monospace;
        --font-ui:      'Inter', sans-serif;
    }

    /* Fondo general: Un color sólido super oscuro. No usamos "background" 
       para no sobreescribir las imágenes establecidas vía utils/backgrounds.py */
    body:not(.login-page) .stApp {
        background-color: var(--aero-navy);
    }
    
    /* Overlay para oscurecer la imagen de fondo y que las letras resalten */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at center, rgba(11, 17, 32, 0.5) 0%, rgba(8, 12, 20, 0.85) 100%);
        pointer-events: none;
        z-index: -1;
    }

    /* Sidebar Glassmorphism Avanzado */
    [data-testid="stSidebar"] {
        background: rgba(8, 12, 20, 0.65) !important;
        backdrop-filter: blur(25px) saturate(200%);
        -webkit-backdrop-filter: blur(25px) saturate(200%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 4px 0 30px rgba(0, 0, 0, 0.5);
    }
    [data-testid="stSidebar"] * { font-family: var(--font-ui) !important; color: #F8FAFC !important; }

    /* Títulos de módulo estilo Neon/Cyber */
    .module-title {
        font-family: var(--font-hero) !important;
        font-size: clamp(3rem, 7vw, 5.5rem);
        letter-spacing: .08em;
        text-align: center;
        background: linear-gradient(135deg, #FFFFFF 20%, #E11D48 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 25px var(--aero-red-glow));
        animation: titleReveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) both, titlePulse 5s ease-in-out infinite alternate;
        margin-bottom: .3rem;
        line-height: 1;
    }
    @keyframes titleReveal {
        from { opacity: 0; transform: translateY(50px) scale(0.9); filter: blur(10px); }
        to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }
    }
    @keyframes titlePulse {
        0%   { filter: drop-shadow(0 0 15px rgba(225, 29, 72, 0.2)); }
        100% { filter: drop-shadow(0 0 45px rgba(225, 29, 72, 0.6)); }
    }
    
    .module-kicker {
        font-family: var(--font-ui);
        font-size: .8rem;
        font-weight: 700;
        letter-spacing: .3em;
        text-transform: uppercase;
        color: var(--aero-red);
        text-align: center;
        margin-bottom: .8rem;
        animation: fadeUp .8s ease .3s both;
    }

    .section-heading {
        font-family: var(--font-heading) !important;
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: .05em;
        position: relative;
        display: inline-block;
        padding-bottom: 8px;
        margin-top: 1rem;
    }
    .section-heading::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        height: 3px; width: 0%;
        background: linear-gradient(90deg, #E11D48, #2563EB);
        border-radius: 3px;
        animation: underlineGrow 1.2s cubic-bezier(0.16, 1, 0.3, 1) .5s forwards;
    }
    @keyframes underlineGrow { to { width: 100% } }

    /* Tarjetas KPI Super Premium */
    .kpi-card {
        background: var(--aero-panel);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 1.8rem;
        position: relative;
        overflow: hidden;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: cardEntrance .7s cubic-bezier(0.16, 1, 0.3, 1) both;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .kpi-card:hover {
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0 25px 50px rgba(0,0,0,0.6), 0 0 0 1px rgba(225, 29, 72, 0.4);
        border-color: rgba(225, 29, 72, 0.6);
    }
    .kpi-card:hover::before { opacity: 1; }

    @keyframes cardEntrance {
        from { opacity: 0; transform: translateY(40px) scale(0.95); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* =========================================== */
    /* ESTILO ÚNICO PARA BOTONES                   */
    /* =========================================== */
    .stButton > button {
        font-family: var(--font-ui) !important;
        font-weight: 700 !important;
        letter-spacing: .08em !important;
        text-transform: uppercase !important;
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    .stButton > button::after {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%);
        transform: rotate(45deg) translateX(-100%);
        transition: transform 0.6s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.5), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    }
    .stButton > button:hover::after {
        transform: rotate(45deg) translateX(100%);
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.4) !important;
    }

    /* Botón Primario Específico (Rojo) */
    [data-testid="baseButton-primary"] > button {
        background: linear-gradient(135deg, #BE123C 0%, #E11D48 100%) !important;
        box-shadow: 0 4px 15px rgba(225, 29, 72, 0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    }
    [data-testid="baseButton-primary"] > button:hover {
        background: linear-gradient(135deg, #E11D48 0%, #F43F5E 100%) !important;
        box-shadow: 0 10px 25px rgba(225, 29, 72, 0.5), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    }

    /* Tablas (DataFrames) Premium */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
    }
    .stDataFrame table {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px);
    }
    .stDataFrame thead th {
        background: rgba(30, 41, 59, 0.9) !important;
        color: #F8FAFC !important;
        font-family: var(--font-heading) !important;
        font-size: 1.1rem !important;
        letter-spacing: .05em;
        text-transform: uppercase;
        border-bottom: 2px solid var(--aero-red) !important;
        padding: 1rem !important;
    }
    .stDataFrame tbody td {
        font-family: var(--font-data) !important;
        font-size: 0.95rem;
        color: #CBD5E1 !important;
        border-bottom: 1px solid rgba(255,255,255,0.03) !important;
        padding: 0.8rem 1rem !important;
        transition: all 0.2s ease;
    }
    .stDataFrame tbody tr {
        transition: background-color 0.2s ease, transform 0.2s ease;
    }
    .stDataFrame tbody tr:hover {
        background: rgba(225, 29, 72, 0.15) !important;
        transform: scale(1.005);
    }
    .stDataFrame tbody tr:hover td {
        color: #FFFFFF !important;
        font-weight: 500;
    }

    /* Charts (Plotly) */
    [data-testid="stPlotlyChart"] {
        background: var(--aero-panel);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 10px;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-4px);
        border-color: rgba(255,255,255,0.15);
    }

    /* Inputs (Text, Number, Select) */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
        font-family: var(--font-body) !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus, 
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within {
        border-color: var(--aero-blue) !important;
        box-shadow: 0 0 0 3px var(--aero-blue-glow) !important;
        background: rgba(30, 41, 59, 0.9) !important;
    }

    /* Curtains and Animations */
    #module-curtain {
        position: fixed; top:0; left:0; width:100%; height:100%;
        background: linear-gradient(135deg, #0B1120 0%, #E11D48 100%);
        z-index: 9999;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none;
        clip-path: polygon(100% 0, 100% 0, 100% 100%, 100% 100%);
        transition: clip-path .6s cubic-bezier(.86,0,.07,1);
    }
    #module-curtain.entering { clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%); }
    #module-curtain.exiting {
        clip-path: polygon(0 0, 0 0, 0 100%, 0 100%);
        transition: clip-path .5s cubic-bezier(.86,0,.07,1) .2s;
    }
    #module-curtain .curtain-brand {
        font-family: var(--font-hero);
        font-size: 4rem; letter-spacing: .25em;
        color: #FFFFFF;
        text-shadow: 0 0 20px rgba(255,255,255,0.5);
        opacity: 0; transform: scale(0.7);
        transition: opacity .4s .2s, transform .4s .2s;
    }
    #module-curtain.entering .curtain-brand { opacity:1; transform: scale(1); }
    
    .module-hero {
        min-height: 28vh;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center; padding: 4rem 1rem 3rem;
        position: relative; overflow: hidden;
    }
    
    .alert-success {
        background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10B981;
        border-radius: 12px; padding: 1.2rem 1.5rem;
        font-family: var(--font-body); color: #F8FAFC;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .alert-error {
        background: rgba(225, 29, 72, 0.15); border-left: 4px solid #E11D48;
        border-radius: 12px; padding: 1.2rem 1.5rem;
        font-family: var(--font-body); color: #F8FAFC;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    [data-testid="stMetricValue"] { font-family: var(--font-data) !important; font-size: 2.2rem !important; font-weight: 700; color: #F8FAFC; }
    [data-testid="stMetricLabel"] { font-family: var(--font-ui) !important; color: var(--aero-muted) !important; font-size: 0.9rem !important; text-transform: uppercase; letter-spacing: 0.05em; }
    [data-testid="stMetricDelta"] { font-family: var(--font-mono) !important; }
    </style>
    <div id="module-curtain"><span class="curtain-brand">AEROPOSTALE</span></div>
    """, unsafe_allow_html=True)

def load_css():
    """Carga todas las librerías y estilos globales de Aeropostale."""
    inject_css_libraries()
    inject_global_styles()

def show_header():
    """Header minimalista compatible con el nuevo diseño."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🏠 Inicio", use_container_width=True, key="__header_home__"):
            st.session_state.current_page = "Inicio"
            st.rerun()
    with col2:
        import html
        s_user = html.escape(str(st.session_state.get('user_name', '')))
        s_role = html.escape(str(st.session_state.get('role', '')))
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(225,29,72,0.2);'>
            <span style='color: var(--aero-red); font-weight: bold; font-family: var(--font-heading);'>{s_user}</span> 
            <span style='color: var(--aero-muted); font-size: 0.85rem;'> | {s_role}</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Salir", use_container_width=True, key="__header_logout__"):
            for key in ["authenticated", "username", "role", "user_name"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def show_module_header(title, subtitle):
    """Hero de módulo con animaciones Bebas Neue."""
    import html
    title_esc = html.escape(str(title))
    sub_esc = html.escape(str(subtitle))
    st.markdown(f"""
    <div class="module-hero">
        <div class="module-kicker">▸ MÓDULO ACTIVO</div>
        <h1 class="module-title">{title_esc}</h1>
        <div style="color: var(--aero-muted); font-family: var(--font-body); font-size: 1.1rem; max-width: 600px; margin: 0 auto;">{sub_esc}</div>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(col, titulo, valor, meta=None, unidad="", frecuencia=""):
    """Tarjeta KPI Aeropostale con glassmorphism y barra de progreso."""
    if meta and meta > 0:
        pct = (valor / meta) * 100
        color_val = "#10B981" if pct >= 95 else ("#F59E0B" if pct >= 80 else "var(--aero-red)")
        barra = f'<div style="height:3px;background:rgba(255,255,255,.1);border-radius:2px;margin-top:12px;"><div style="height:3px;width:{min(pct,100):.0f}%;background:{color_val};border-radius:2px;transition:width 1s ease;"></div></div>'
        meta_txt = f'<div style="font-family:var(--font-ui);font-size:.72rem;color:var(--aero-muted);margin-top:6px;">Meta: {meta:,.0f}{unidad} — {pct:.1f}%</div>'
    else:
        barra = ""
        meta_txt = ""

    import html
    t_esc = html.escape(str(titulo))
    f_esc = html.escape(str(frecuencia))
    u_esc = html.escape(str(unidad))
    col.markdown(f"""
    <div class="kpi-card">
        <div style="font-family:var(--font-ui);font-size:.75rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--aero-muted);margin-bottom:.5rem;">{t_esc}</div>
        <div style="font-family:var(--font-data);font-size:clamp(1.8rem,3vw,2.6rem);font-weight:700;color:#f8fafc;line-height:1;">{valor:,.1f}{u_esc}</div>
        {barra}
        {meta_txt}
        <div style="font-family:var(--font-ui);font-size:.68rem;color:var(--aero-muted);margin-top:8px;letter-spacing:.05em;">{f_esc}</div>
    </div>
    """, unsafe_allow_html=True)

def create_module_card(icon, title, description, module_key):
    """Tarjeta de acceso a módulo en la página principal (estilo legacy)."""
    import html
    i_esc = html.escape(str(icon))
    t_esc = html.escape(str(title))
    d_esc = html.escape(str(description))
    st.markdown(f"""
    <div class="kpi-card" style="height: 180px; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{i_esc}</div>
        <div style="font-family: var(--font-heading); font-size: 1.4rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem;">{t_esc}</div>
        <div style="font-family: var(--font-body); font-size: 0.85rem; color: var(--aero-muted); line-height: 1.3;">{d_esc}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"Entrar a {title}", key=f"btn_{module_key}", use_container_width=True):
        st.session_state.current_page = module_key
        st.rerun()

def add_back_button(key: str = "back"):
    """Botón para volver al inicio. Eliminado por petición del usuario."""
    pass

def apply_plotly_theme(fig):
    """Aplica el tema Aeropostale a un gráfico de Plotly."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Space Grotesk", color="#F8FAFC", size=13),
        colorway=["#E11D48","#2563EB","#10B981","#F59E0B","#8B5CF6","#38BDF8"],
        title_font=dict(family="Rajdhani", size=22, color="#F8FAFC", weight="bold"),
        legend=dict(bgcolor="rgba(15,23,42,0.6)", bordercolor="rgba(225,29,72,0.3)", borderwidth=1),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    )
    return fig
