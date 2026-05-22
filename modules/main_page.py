import streamlit as st
from pathlib import Path
import base64
from utils.ui import load_css

def show_module_header(title_with_icon, subtitle):
    icon = title_with_icon[0] if title_with_icon else ""
    title_text = title_with_icon[1:].strip() if title_with_icon else ""
    st.markdown(f"""
    <div class="module-header fade-in">
        <h1 class="header-title">
            <span class="header-icon">{icon}</span> 
            <span class="header-text">{title_text}</span>
        </h1>
        <p class="header-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def navigate_to_module(module_key):
    st.session_state.current_page = module_key

def create_module_card(icon, title, description, module_key, image_name=None):
    """
    Crea una tarjeta de módulo con imagen de fondo completa, título, descripción y botón.
    - image_name: nombre del archivo de imagen (sin extensión) dentro de /images/
    """
    # Ruta de la imagen del módulo
    img_path = Path(f"images/{image_name}.png") if image_name else None
    if not img_path or not img_path.exists():
        img_path = Path(f"images/{image_name}.jpg") if image_name else None
        
    if img_path and img_path.exists():
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        img_html = f'<img src="data:image/png;base64,{img_base64}" class="card-img-full" alt="{title}">'
        overlay_html = '<div class="card-overlay"></div>'
    else:
        # Si no hay imagen, mostramos un fondo degradado oscuro
        img_html = ''
        overlay_html = '<div class="card-overlay-gradient"></div>'

    card_html = f"""
    <div class="card-modern fade-in" data-module="{module_key}">
        {img_html}
        {overlay_html}
        <div class="card-content-wrapper">
            <div class="card-icon-large">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-description">{description}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    st.button(
        f"Ingresar a {title}",
        key=f"btn_{module_key}",
        use_container_width=True,
        on_click=navigate_to_module,
        args=(module_key,)
    )

def show_main_page():
    load_css()

    # Fondo común de la página principal (puede ser el mismo de login o uno específico)
    image_path = Path("images/background_aeropostale.png")
    base64_image = ""
    if image_path.exists():
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
    <style>
    /* Importar tipografía profesional */
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,600;14..32,700&family=Bebas+Neue&display=swap');
    
    .stApp {{
        background: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(30,58,138,0.7)),
                    url(data:image/png;base64,{base64_image});
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .fade-in {{
        animation: fadeInUp 0.7s ease both;
    }}
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(40px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .brand-title {{
        font-family: 'Bebas Neue', 'Impact', sans-serif;
        font-size: 5rem;
        font-weight: 400;
        text-align: center;
        background: linear-gradient(135deg, #1E40AF, #3B82F6, #0EA5E9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 20px;
        letter-spacing: 2px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    .brand-subtitle {{
        font-family: 'Inter', sans-serif;
        text-align: center;
        color: #E2E8F0;
        letter-spacing: 1px;
        margin-bottom: 40px;
        font-size: 1.2rem;
        font-weight: 400;
        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }}
    .card-modern {{
        background: rgba(20, 30, 50, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 28px;
        padding: 25px 20px 20px;
        border: 1px solid rgba(59,130,246,0.3);
        transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        text-align: center;
        min-height: 280px;
    }}
    .card-modern::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(14,165,233,0.1));
        opacity: 0;
        transition: opacity 0.4s ease;
        z-index: 2;
    }}
    .card-modern:hover {{
        transform: translateY(-8px) scale(1.02);
        border-color: rgba(59,130,246,0.8);
        box-shadow: 0 25px 40px rgba(59,130,246,0.3);
    }}
    .card-modern:hover::before {{
        opacity: 1;
    }}
    .card-content-wrapper {{
        position: relative;
        z-index: 3;
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        pointer-events: none;
    }}
    .card-img-full {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        z-index: 0;
        transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1);
    }}
    .card-modern:hover .card-img-full {{
        transform: scale(1.08);
    }}
    .card-overlay {{
        position: absolute;
        inset: 0;
        background: linear-gradient(to top, rgba(15, 23, 42, 0.95) 40%, rgba(15, 23, 42, 0.6) 75%, rgba(15, 23, 42, 0.25) 100%);
        z-index: 1;
    }}
    .card-overlay-gradient {{
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 58, 138, 0.85));
        z-index: 1;
    }}
    .card-icon-large {{
        font-size: 3rem;
        margin-bottom: 12px;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        transition: transform 0.3s ease;
    }}
    .card-modern:hover .card-icon-large {{
        transform: scale(1.15) rotate(3deg);
    }}
    .card-title {{
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.45rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.6);
    }}
    .card-description {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #E2E8F0;
        line-height: 1.4;
        margin-bottom: 10px;
        padding: 0 8px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5);
    }}
    /* Botones profesionales en azul */
    .stButton > button {{
        background: linear-gradient(95deg, #1E3A8A, #2563EB) !important;
        border: none !important;
        border-radius: 40px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
        letter-spacing: 0.5px;
    }}
    .stButton > button:hover {{
        background: linear-gradient(95deg, #2563EB, #1E40AF) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 20px rgba(37,99,235,0.4) !important;
    }}
    .stButton > button:active {{
        transform: translateY(1px);
    }}
    .footer-text {{
        text-align: center;
        margin-top: 50px;
        color: #94A3B8;
        font-size: 0.8rem;
        font-family: 'Inter', sans-serif;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 25px;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="fade-in">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribución Ecuador | ERP</div>
    </div>
    """, unsafe_allow_html=True)

    # Lista de módulos con sus imágenes asociadas (nombre del archivo sin extensión)
    all_modules = [
        {"icon": "📊", "title": "Dashboard KPIs",        "description": "KPIs globales, IA y control nacional",        "key": "dashboard_kpis",   "image": "dashboard_kpis"},
        {"icon": "📈", "title": "KPI Analytics",         "description": "Indicadores detallados, predicciones y ABC", "key": "kpi_analytics",     "image": "kpi_analytics"},
        {"icon": "💰", "title": "Reconciliación",        "description": "Conciliación financiera y análisis de facturas", "key": "reconciliacion", "image": "reconciliacion"},
        {"icon": "📧", "title": "Auditoría de Correos",   "description": "Análisis inteligente de novedades por email", "key": "auditoria_correos", "image": "auditoria_correos"},
        {"icon": "📦", "title": "Dashboard Logístico",    "description": "Control de transferencias y distribución",    "key": "logistica",          "image": "logistica"},
        {"icon": "👥", "title": "Gestión de Equipo",      "description": "Administración del personal del centro",     "key": "equipo",             "image": "equipo"},
        {"icon": "🚚", "title": "Generar Guías",          "description": "Sistema de envíos con seguimiento QR",       "key": "guias",              "image": "guias"},
        {"icon": "📋", "title": "Control de Inventario",  "description": "Gestión de stock en tiempo real",           "key": "inventario",         "image": "inventario"},
        {"icon": "📥", "title": "Recepción",              "description": "Registro y gestión de mercancía entrante",   "key": "recepcion",          "image": "recepcion"},
        {"icon": "🏗️", "title": "Gestión de Almacén",     "description": "Layout de bodega, picking y conteo cíclico",   "key": "almacen",            "image": "almacen"},
        {"icon": "⚙️", "title": "Configuración",          "description": "Personalización del sistema ERP",            "key": "configuracion",      "image": "configuracion"},
    ]

    role = st.session_state.get("role", "Usuario")
    if role == "Bodega":
        modules = [m for m in all_modules if m["key"] in ["guias", "inventario", "recepcion", "almacen"]]
    else:
        modules = all_modules

    # Mostrar tarjetas en columnas de 3
    cols = st.columns(3)
    for idx, module in enumerate(modules):
        with cols[idx % 3]:
            create_module_card(
                icon=module["icon"],
                title=module["title"],
                description=module["description"],
                module_key=module["key"],
                image_name=module["image"]
            )

    st.markdown("""
    <div class="footer-text fade-in">
        <p><strong>Sistema ERP</strong> • Desarrollado por Wilson Pérez</p>
        <p style="font-size:12px;">© 2026 AEROPOSTALE Ecuador</p>
    </div>
    """, unsafe_allow_html=True)
