"""
Gestión de estilos CSS personalizados
"""

import streamlit as st


def load_custom_css():
    """
    Carga los estilos CSS personalizados para la aplicación
    """
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700;800&display=swap');

.stApp {
    font-family: 'Montserrat', sans-serif;
    background-color: #0e1117;
    overflow: hidden;
}

.main-bg {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    z-index: -1;
}

/* Contenedor Ultra-Compacto */
.gallery-container {
    padding: 30px 5% 10px 5%;
    text-align: center;
    max-width: 1400px;
    margin: 0 auto;
}

.brand-title {
    color: white;
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: 15px;
    margin-bottom: 10px;
    text-transform: uppercase;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px rgba(96, 165, 250, 0.5); }
    to { text-shadow: 0 0 20px rgba(244, 114, 182, 0.8); }
}

.brand-subtitle {
    color: #94A3B8;
    font-size: 1rem;
    letter-spacing: 6px;
    margin-bottom: 40px;
    text-transform: uppercase;
    font-weight: 300;
}

/* Grid de módulos */
.modules-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 0 10px;
}

@media (max-width: 1024px) {
    .modules-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
    .modules-grid { grid-template-columns: 1fr; }
    .brand-title { font-size: 2.5rem; letter-spacing: 10px; }
}

/* Tarjetas Rectangulares Compactas */
.module-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    height: 180px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 20px;
    position: relative;
    cursor: pointer;
    overflow: hidden;
}

.module-card:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
}

.module-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.7s;
}

.module-card:hover::before {
    left: 100%;
}

.card-icon {
    font-size: 2.8rem;
    margin-bottom: 15px;
    transition: transform 0.3s ease;
}

.module-card:hover .card-icon {
    transform: scale(1.2) rotate(5deg);
}

.card-title {
    color: white;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    text-align: center;
}

.card-description {
    color: #94A3B8;
    font-size: 0.85rem;
    text-align: center;
    margin-top: 8px;
    opacity: 0.8;
    line-height: 1.3;
}

/* Contenido interno */
.internal-header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 2rem;
    border-left: 6px solid #60A5FA;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.5rem;
    background: linear-gradient(45deg, #60A5FA, #F472B6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-subtitle {
    font-size: 1rem;
    color: #94A3B8;
    font-weight: 400;
}

/* Tarjetas de estadísticas */
.stat-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    height: 100%;
}

.stat-card:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-3px);
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #60A5FA;
}

.stat-title {
    font-size: 0.9rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: white;
    margin: 0.5rem 0;
}

.stat-change {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
    background: rgba(34, 197, 94, 0.2);
    color: #4ADE80;
}

.stat-change.negative {
    background: rgba(239, 68, 68, 0.2);
    color: #F87171;
}

/* Grid para métricas */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

/* Tabs personalizados */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 0.8rem 1.5rem;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
    color: #94A3B8;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.08);
    border-color: #60A5FA;
    color: white;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(96, 165, 250, 0.2);
    color: #60A5FA;
    border-color: #60A5FA;
}

/* Botones */
.stButton > button {
    background: linear-gradient(45deg, #60A5FA, #8B5CF6) !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(96, 165, 250, 0.3) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
}

.sidebar-header {
    text-align: center;
    padding: 20px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
    color: white;
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 5px;
}

.sidebar-subtitle {
    color: #94A3B8;
    font-size: 0.8rem;
}

/* DataFrames */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

/* Scrollbar personalizado */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #60A5FA, #8B5CF6);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(45deg, #8B5CF6, #F472B6);
}

/* Footer */
.app-footer {
    text-align: center;
    padding: 2rem;
    margin-top: 3rem;
    color: #64748B;
    font-size: 0.9rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}
</style>

<div class="main-bg"></div>
""", unsafe_allow_html=True)
