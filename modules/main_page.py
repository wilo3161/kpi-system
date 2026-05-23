# modules/main_page.py
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
    st.session_state["_navigate_to"] = module_key

def create_module_card(icon, title, description, module_key, image_name=None):
    """
    Crea una tarjeta de módulo con fondo transparente y efecto hover.
    La imagen de fondo se escala para cubrir toda la tarjeta.
    """
    # Ruta de la imagen del módulo
    bg_image_base64 = None
    if image_name:
        png_path = Path(f"images/{image_name}.png")
        jpg_path = Path(f"images/{image_name}.jpg")
        if png_path.exists():
            with open(png_path, "rb") as f:
                bg_image_base64 = base64.b64encode(f.read()).decode()
        elif jpg_path.exists():
            with open(jpg_path, "rb") as f:
                bg_image_base64 = base64.b64encode(f.read()).decode()

    # Construir estilo de fondo con imagen escalada
    if bg_image_base64:
        bg_style = f"""
            background-image: url('data:image/png;base64,{bg_image_base64}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        """
    else:
        bg_style = "background: rgba(0,0,0,0.3); backdrop-filter: blur(4px);"

    card_html = f"""
    <div class="card-transparent" data-module="{module_key}" style="{bg_style}">
        <div class="card-overlay"></div>
        <div class="card-icon">{icon}</div>
        <div class="card-title">{title}</div>
        <div class="card-description">{description}</div>
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

    if st.session_state.get("_navigate_to"):
        target = st.session_state.pop("_navigate_to")
        st.session_state.current_page = target
        st.rerun()

    # Fondo general oscuro
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0A0A1A, #1A1A2E);
        background-size: cover;
        background-attachment: fixed;
    }
    .brand-title {
        font-family: 'Bebas Neue', 'Impact', sans-serif;
        font-size: 5rem;
        font-weight: 400;
        text-align: center;
        background: linear-gradient(135deg, #FFFFFF, #E0E0E0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 20px;
        letter-spacing: 2px;
        text-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .brand-subtitle {
        font-family: 'Inter', sans-serif;
        text-align: center;
        color: #CCCCCC;
        letter-spacing: 1px;
        margin-bottom: 40px;
        font-size: 1.2rem;
        font-weight: 400;
        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    /* Tarjeta transparente con imagen de fondo escalada */
    .card-transparent {
        position: relative;
        border-radius: 28px;
        padding: 25px 20px 20px;
        transition: all 0.4s cubic-bezier(0.2, 0.9, 0.4, 1.1);
        overflow: hidden;
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-height: 280px;
        cursor: pointer;
        background-color: rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    /* Overlay oscuro sobre la imagen para mejorar legibilidad */
    .card-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1;
        pointer-events: none;
        border-radius: 28px;
        transition: background 0.3s ease;
    }
    .card-transparent:hover .card-overlay {
        background: rgba(0, 0, 0, 0.7);
    }
    .card-icon, .card-title, .card-description {
        position: relative;
        z-index: 2;
    }
    .card-transparent:hover {
        transform: translateY(-8px) scale(1.02);
        border: 1px solid rgba(207, 10, 44, 0.6);
        box-shadow: 0 20px 30px -8px rgba(0, 0, 0, 0.5), 0 0 0 2px rgba(207,10,44,0.3);
        backdrop-filter: blur(12px);
    }
    .card-icon {
        font-size: 3.2rem;
        margin-bottom: 12px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        transition: all 0.3s ease;
        background: rgba(0,0,0,0.4);
        padding: 8px 16px;
        border-radius: 60px;
        backdrop-filter: blur(4px);
        color: #FFFFFF;
    }
    .card-transparent:hover .card-icon {
        transform: scale(1.1);
        background: rgba(0,0,0,0.6);
        color: #CF0A2C;
    }
    .card-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.5);
    }
    .card-description {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #E2E8F0;
        line-height: 1.5;
        margin-bottom: 10px;
        padding: 0 8px;
        text-shadow: 0 1px 2px rgba(0,0,0,0.4);
    }
    .footer-text {
        text-align: center;
        margin-top: 50px;
        color: #94A3B8;
        font-size: 0.8rem;
        font-family: 'Inter', sans-serif;
        border-top: 1px solid rgba(255,255,255,0.1);
        padding-top: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="fade-in">
        <div class="brand-title">AEROPOSTALE</div>
        <div class="brand-subtitle">Centro de Distribución Ecuador | ERP</div>
    </div>
    """, unsafe_allow_html=True)

    # Lista completa de módulos
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
        {"icon": "⚙️", "title": "Configuración",          "description": "Personalización del sistema ERP",            "key": "configuracion",      "image": "configuracion"},
    ]

    # Filtrar módulos según el rol del usuario
    rol_activo = st.session_state.get("role", "")
    filtered_modules = []
    
    for mod in all_modules:
        if rol_activo == "Administrador":
            filtered_modules.append(mod)
        elif rol_activo in ["Bodega", "Logística"]:
            # Equipo de trabajo: solo inventario, guías y logística
            if mod["key"] in ["inventario", "guias", "logistica"]:
                filtered_modules.append(mod)
        elif rol_activo == "Ventas":
            # Ventas: solo KPIs (Dashboard y Analytics)
            if mod["key"] in ["dashboard_kpis", "kpi_analytics"]:
                filtered_modules.append(mod)
        elif rol_activo == "Tienda":
            # Tiendas: solo recepción
            if mod["key"] == "recepcion":
                filtered_modules.append(mod)
        else:
            # Fallback para roles no definidos
            filtered_modules.append(mod)

    # Mostrar tarjetas en columnas de 3
    cols = st.columns(3)
    for idx, module in enumerate(filtered_modules):
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
