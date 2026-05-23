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
    })();
    </script>
    """, unsafe_allow_html=True)

def inject_global_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Rajdhani:wght@500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --aero-red:       #CF0A2C;
        --aero-navy:      #002D62;
        --aero-blue:      #0033A0;
        --aero-dark:      #0F172A;
        --aero-panel:     #1E293B;
        --aero-muted:     #94A3B8;
        --aero-red-glow:  rgba(207,10,44,0.28);
        --aero-blue-glow: rgba(0,51,160,0.30);
        --font-hero:    'Bebas Neue', sans-serif;
        --font-heading: 'Rajdhani', sans-serif;
        --font-body:    'Outfit', sans-serif;
        --font-data:    'Space Grotesk', sans-serif;
        --font-mono:    'JetBrains Mono', monospace;
        --font-ui:      'Inter', sans-serif;
    }

    /* Fondo animado solo para páginas internas (no para login) */
    body:not(.login-page) .stApp {
        background: linear-gradient(135deg, #0A0A0A 0%, #1A1A24 45%, #001F3F 100%);
        background-size: 400% 400%;
        animation: bgShift 14s ease infinite;
    }
    @keyframes bgShift {
        0%   { background-position: 0% 50% }
        50%  { background-position: 100% 50% }
        100% { background-position: 0% 50% }
    }

    /* Sidebar glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(0,25,50,0.72) !important;
        backdrop-filter: blur(20px) saturate(180%);
        border-right: 1px solid rgba(207,10,44,0.25);
        box-shadow: 4px 0 24px rgba(207,10,44,0.10);
    }
    [data-testid="stSidebar"] * { font-family: var(--font-ui) !important; color: #FFFFFF !important; }

    /* Títulos de módulo */
    .module-title {
        font-family: var(--font-hero) !important;
        font-size: clamp(2.5rem, 6vw, 4.5rem);
        letter-spacing: .06em;
        text-align: center;
        background: linear-gradient(135deg, #FFFFFF 30%, #CF0A2C 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 20px var(--aero-red-glow));
        animation: titleReveal 1s cubic-bezier(.16,1,.3,1) both, titlePulse 4s ease-in-out 1s infinite;
        margin-bottom: .25rem;
    }
    @keyframes titleReveal {
        from { opacity:0; transform: translateY(40px) scale(.96); letter-spacing:.3em; }
        to   { opacity:1; transform: translateY(0) scale(1); letter-spacing:.06em; }
    }
    @keyframes titlePulse {
        0%,100% { filter: drop-shadow(0 0 20px rgba(207,10,44,.25)); }
        50%      { filter: drop-shadow(0 0 40px rgba(207,10,44,.55)); }
    }
    .module-kicker {
        font-family: var(--font-ui);
        font-size: .72rem;
        font-weight: 600;
        letter-spacing: .22em;
        text-transform: uppercase;
        color: #CF0A2C;
        text-align: center;
        margin-bottom: .5rem;
        animation: fadeUp .6s ease .15s both;
    }
    .section-heading {
        font-family: var(--font-heading) !important;
        font-size: 1.55rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: .04em;
        position: relative;
        display: inline-block;
        padding-bottom: 6px;
    }
    .section-heading::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0;
        height: 2px; width: 0%;
        background: linear-gradient(90deg, #CF0A2C, #0033A0);
        border-radius: 2px;
        animation: underlineGrow 1s cubic-bezier(.16,1,.3,1) .5s forwards;
    }
    @keyframes underlineGrow { to { width: 100% } }
    .kpi-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(207,10,44,0.20);
        border-radius: 16px;
        backdrop-filter: blur(16px);
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: transform .35s cubic-bezier(.34,1.56,.64,1), box-shadow .35s ease, border-color .35s ease;
        animation: cardEntrance .6s cubic-bezier(.16,1,.3,1) both;
        margin-bottom: 1rem;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, #CF0A2C, transparent);
        animation: scanLine 3s linear infinite;
    }
    @keyframes scanLine { to { left: 100% } }
    .kpi-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 20px 60px rgba(207,10,44,.20), 0 0 0 1px rgba(207,10,44,.35);
        border-color: rgba(207,10,44,.50);
    }
    @keyframes cardEntrance {
        from { opacity:0; transform: translateY(30px) rotateX(8deg); }
        to   { opacity:1; transform: translateY(0) rotateX(0); }
    }

    /* =========================================== */
    /* ESTILO ÚNICO PARA BOTONES (AZUL)            */
    /* =========================================== */
    .stButton > button {
        font-family: var(--font-ui) !important;
        font-weight: 600 !important;
        letter-spacing: .05em !important;
        text-transform: uppercase !important;
        background: linear-gradient(95deg, #1E3A8A, #2563EB) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        transition: transform .2s ease, box-shadow .2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(95deg, #2563EB, #1E40AF) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 20px rgba(37,99,235,0.4) !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Botón de login (se mantiene rojo, pues es una pantalla separada) */
    div[data-testid="stFormSubmitButton"] > button {
        background: #A52030 !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        letter-spacing: .18em !important;
        height: 52px !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background: #CF0A2C !important;
        transform: none !important;
        box-shadow: 0 6px 24px rgba(207,10,44,0.35) !important;
    }

    /* Tablas y otros componentes... */
    .stDataFrame tbody tr {
        animation: rowFadeIn .4s ease both;
        font-family: var(--font-data);
        font-size: .85rem;
    }
    .stDataFrame tbody tr:nth-child(1)  { animation-delay:.05s }
    .stDataFrame tbody tr:nth-child(2)  { animation-delay:.10s }
    .stDataFrame tbody tr:nth-child(3)  { animation-delay:.15s }
    .stDataFrame tbody tr:nth-child(4)  { animation-delay:.20s }
    .stDataFrame tbody tr:nth-child(5)  { animation-delay:.25s }
    .stDataFrame tbody tr:nth-child(n+6){ animation-delay:.30s }
    @keyframes rowFadeIn {
        from { opacity:0; transform: translateX(-16px); }
        to   { opacity:1; transform: translateX(0); }
    }
    .stDataFrame thead { font-family: var(--font-heading); letter-spacing:.05em; color: #CF0A2C !important; }
    .stDataFrame tbody tr:nth-child(even) { background: rgba(255,255,255,.02); }
    .stDataFrame tbody tr:hover { background: rgba(207,10,44,.08); }
    [data-testid="stPlotlyChart"] {
        animation: chartReveal .9s cubic-bezier(.16,1,.3,1) .2s both;
        border-radius: 12px; overflow: hidden;
    }
    @keyframes chartReveal {
        from { opacity:0; transform: translateY(20px) scale(.98); }
        to   { opacity:1; transform: translateY(0) scale(1); }
    }
    .plasma-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #CF0A2C 30%, #0033A0 70%, transparent);
        margin: 2rem 0;
        animation: plasmaPulse 3s ease infinite;
    }
    @keyframes plasmaPulse {
        0%,100% { opacity:.5; }
        50% { opacity:1; box-shadow: 0 0 12px rgba(207,10,44,.5); }
    }
    #module-curtain {
        position: fixed; top:0; left:0; width:100%; height:100%;
        background: linear-gradient(135deg, #CF0A2C 0%, #0F172A 60%, #002D62 100%);
        z-index: 9999;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none;
        clip-path: polygon(100% 0, 100% 0, 100% 100%, 100% 100%);
        transition: clip-path .55s cubic-bezier(.86,0,.07,1);
    }
    #module-curtain.entering { clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%); }
    #module-curtain.exiting {
        clip-path: polygon(0 0, 0 0, 0 100%, 0 100%);
        transition: clip-path .45s cubic-bezier(.86,0,.07,1) .15s;
    }
    #module-curtain .curtain-brand {
        font-family: var(--font-hero);
        font-size: 3rem; letter-spacing:.2em;
        color: rgba(255,255,255,.90);
        opacity: 0; transform: scale(.8);
        transition: opacity .3s .2s, transform .3s .2s;
    }
    #module-curtain.entering .curtain-brand { opacity:1; transform: scale(1); }
    .module-content { animation: moduleEnter .6s cubic-bezier(.16,1,.3,1) both; }
    @keyframes moduleEnter {
        from { opacity:0; transform: scale(.97) translateY(12px); }
        to   { opacity:1; transform: scale(1) translateY(0); }
    }
    .module-hero {
        min-height: 28vh;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        text-align: center; padding: 3rem 1rem 2rem;
        position: relative; overflow: hidden;
    }
    .module-hero::before {
        content: '';
        position: absolute; inset: 0;
        background: radial-gradient(ellipse 80% 60% at 50% 50%, rgba(207,10,44,.12) 0%, transparent 70%);
        animation: heroPulse 6s ease-in-out infinite;
        pointer-events: none;
    }
    @keyframes heroPulse {
        0%,100% { transform: scale(1); opacity:.7; }
        50%      { transform: scale(1.15); opacity:1; }
    }
    .alert-success {
        background: rgba(5,150,105,.12); border-left: 3px solid #059669;
        border-radius: 8px; padding: 1rem 1.25rem;
        font-family: var(--font-body);
        animation: slideInRight .4s cubic-bezier(.16,1,.3,1) both;
        margin-bottom: 1rem;
    }
    .alert-error {
        background: rgba(207,10,44,.12); border-left: 3px solid #CF0A2C;
        border-radius: 8px; padding: 1rem 1.25rem;
        animation: slideInRight .4s cubic-bezier(.16,1,.3,1) both;
        margin-bottom: 1rem;
    }
    @keyframes slideInRight {
        from { opacity:0; transform: translateX(30px); }
        to   { opacity:1; transform: translateX(0); }
    }
    @keyframes fadeUp {
        from { opacity:0; transform: translateY(12px); }
        to   { opacity:1; transform: translateY(0); }
    }
    .stSelectbox > div, .stTextInput > div > input, .stNumberInput > div > input {
        background: rgba(255,255,255,.06) !important;
        border: 1px solid rgba(207,10,44,.20) !important;
        border-radius: 8px !important;
        color: #f8fafc !important;
        font-family: var(--font-body) !important;
        backdrop-filter: blur(8px);
    }
    .stSelectbox > div:focus-within, .stTextInput > div > input:focus {
        border-color: rgba(207,10,44,.60) !important;
        box-shadow: 0 0 0 3px rgba(207,10,44,.12) !important;
    }
    /* Inputs del login (panel negro) sobreescriben los globales via auth.py */
    div[data-testid="column"]:first-child .stTextInput > div > div > input {
        background: #1A1A1A !important;
        border: 1.5px solid #333333 !important;
        border-radius: 6px !important;
        color: #CCCCCC !important;
        padding: 13px 18px 13px 18px !important;
        font-size: 0.95rem !important;
        height: 52px !important;
        backdrop-filter: none !important;
        box-shadow: none !important;
    }
    div[data-testid="column"]:first-child .stTextInput > div > div > input:focus {
        border-color: #CF0A2C !important;
        box-shadow: 0 0 0 2px rgba(207,10,44,0.12) !important;
    }
    [data-testid="stMetric"] { font-family: var(--font-data) !important; }
    [data-testid="stMetricValue"] { font-family: var(--font-data) !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { font-family: var(--font-ui) !important; color: var(--aero-muted) !important; }
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
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(207,10,44,0.1);'>
            <span style='color: #CF0A2C; font-weight: bold; font-family: var(--font-heading);'>{st.session_state.user_name}</span> 
            <span style='color: #94A3B8; font-size: 0.85rem;'> | {st.session_state.role}</span>
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
    st.markdown(f"""
    <div class="module-hero">
        <div class="module-kicker">▸ MÓDULO ACTIVO</div>
        <h1 class="module-title">{title}</h1>
        <div style="color: var(--aero-muted); font-family: var(--font-body); font-size: 1.1rem; max-width: 600px; margin: 0 auto;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def kpi_card(col, titulo, valor, meta=None, unidad="", frecuencia=""):
    """Tarjeta KPI Aeropostale con glassmorphism y barra de progreso."""
    if meta and meta > 0:
        pct = (valor / meta) * 100
        color_val = "#059669" if pct >= 95 else ("#f59e0b" if pct >= 80 else "#CF0A2C")
        barra = f'<div style="height:3px;background:rgba(255,255,255,.1);border-radius:2px;margin-top:12px;"><div style="height:3px;width:{min(pct,100):.0f}%;background:{color_val};border-radius:2px;transition:width 1s ease;"></div></div>'
        meta_txt = f'<div style="font-family:var(--font-ui);font-size:.72rem;color:var(--aero-muted);margin-top:6px;">Meta: {meta:,.0f}{unidad} — {pct:.1f}%</div>'
    else:
        barra = ""
        meta_txt = ""

    col.markdown(f"""
    <div class="kpi-card">
        <div style="font-family:var(--font-ui);font-size:.75rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--aero-muted);margin-bottom:.5rem;">{titulo}</div>
        <div style="font-family:var(--font-data);font-size:clamp(1.8rem,3vw,2.6rem);font-weight:700;color:#f8fafc;line-height:1;">{valor:,.1f}{unidad}</div>
        {barra}
        {meta_txt}
        <div style="font-family:var(--font-ui);font-size:.68rem;color:var(--aero-muted);margin-top:8px;letter-spacing:.05em;">{frecuencia}</div>
    </div>
    """, unsafe_allow_html=True)

def create_module_card(icon, title, description, module_key):
    """Tarjeta de acceso a módulo en la página principal (estilo legacy)."""
    st.markdown(f"""
    <div class="kpi-card" style="height: 180px; display: flex; flex-direction: column; justify-content: center;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-family: var(--font-heading); font-size: 1.4rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem;">{title}</div>
        <div style="font-family: var(--font-body); font-size: 0.85rem; color: var(--aero-muted); line-height: 1.3;">{description}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"Entrar a {title}", key=f"btn_{module_key}", use_container_width=True):
        st.session_state.current_page = module_key
        st.rerun()

def add_back_button(key: str = "back"):
    """Botón para volver al inicio. Acepta un parámetro 'key' para identificar el botón."""
    if st.button("⬅️ VOLVER AL INICIO", key=key):
        st.session_state.current_page = "Inicio"
        st.rerun()

def apply_plotly_theme(fig):
    """Aplica el tema Aeropostale a un gráfico de Plotly."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(15,23,42,0)",
        plot_bgcolor="rgba(30,41,59,0.5)",
        font=dict(family="Space Grotesk", color="#f8fafc", size=12),
        colorway=["#CF0A2C","#0033A0","#002D62","#94A3B8","#1E3A5F","#38bdf8"],
        title_font=dict(family="Rajdhani", size=20, color="#f8fafc"),
        legend=dict(bgcolor="rgba(15,23,42,0.5)", bordercolor="rgba(207,10,44,.2)", borderwidth=1),
        xaxis=dict(gridcolor="rgba(255,255,255,.05)", linecolor="rgba(255,255,255,.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,.05)", linecolor="rgba(255,255,255,.1)"),
    )
    return fig
