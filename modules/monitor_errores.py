"""
Módulo de Monitoreo de Errores en Tiempo Real
===============================================
- Captura excepciones del sistema
- Las envía al DeepSeekAgent para análisis
- Muestra dashboard de errores
- Permite aplicar correcciones automáticas/manuales
"""

import streamlit as st
import sys
import traceback
from datetime import datetime
from utils.ui import add_back_button, show_module_header
from database.manager import local_db
from core.event_bus import emitir

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from services.ai_agent import DeepSeekAgent
        _agent = DeepSeekAgent()
    return _agent


def capturar_y_analizar(error: Exception, modulo: str = "desconocido"):
    """
    Captura una excepción, la analiza con DeepSeek y la registra.
    Se puede llamar desde cualquier módulo con try/except.
    
    Uso:
        try:
            ...
        except Exception as e:
            from modules.monitor_errores import capturar_y_analizar
            capturar_y_analizar(e, "guias")
    """
    agent = get_agent()
    tb = traceback.format_exc()
    analysis = agent.detectar_error(str(error), tb, modulo)
    
    try:
        local_db.insert("logs_errores", {
            "timestamp": datetime.now().isoformat(),
            "modulo": modulo,
            "error": str(error),
            "traceback": tb,
            "analisis": analysis,
            "resuelto": False
        })
    except:
        pass
    
    try:
        emitir("ERROR_DETECTADO", {
            "modulo": modulo,
            "error": str(error)[:200],
            "severidad": analysis.get("severidad", "medio")
        })
    except:
        pass
    
    if analysis.get("auto_fix_posible"):
        agent.auto_corregir(analysis)
    
    return analysis


def show_monitor():
    """Dashboard de monitoreo de errores."""
    add_back_button(key="back_monitor")
    show_module_header("🛡️ Monitor de IA", "Detección y corrección de errores en tiempo real con DeepSeek")
    
    agent = get_agent()
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Errores", "🧠 Consola IA", "⚙️ Configuración"])
    
    with tab1:
        st.subheader("📋 Últimos Errores Detectados")
        try:
            errores = local_db.find("logs_errores", {}, sort=[("timestamp", -1)], limit=50)
        except:
            errores = []
        
        if not errores:
            st.success("✅ No se han detectado errores en el sistema.")
        else:
            for err in errores[:10]:
                titulo = f"⚠️ {err.get('modulo', '?')} — {str(err.get('error', '?'))[:80]} [{str(err.get('timestamp',''))[:19]}]"
                with st.expander(titulo):
                    st.json(err.get("analisis", {}))
                    if err.get("analisis", {}).get("auto_fix_posible"):
                        if st.button(f"🛠️ Auto-Corregir", key=f"fix_{err.get('_id','')}"):
                            agent.auto_corregir(err.get("analisis", {}))
                            st.success("✅ Corrección aplicada")
                            st.rerun()
    
    with tab2:
        st.subheader("🧠 Consola de Análisis con DeepSeek")
        archivo = st.text_input("📁 Archivo a analizar", value="modules/guias.py")
        contexto = st.text_area("📝 Contexto adicional", 
                               "Busca bugs, mejoras de rendimiento y seguridad")
        if st.button("🔍 Analizar con DeepSeek"):
            with st.spinner("Analizando código con DeepSeek..."):
                resultado = agent.sugerir_mejora_codigo(archivo, contexto)
                st.markdown(resultado)
    
    with tab3:
        st.subheader("⚙️ Configuración del Agente IA")
        agent.auto_fix_enabled = st.toggle("🤖 Auto-corrección automática", 
                                           value=agent.auto_fix_enabled,
                                           help="Si está activo, el agente aplicará correcciones automáticamente")
        
        if st.button("📊 Generar Reporte de Errores"):
            with st.spinner("Generando reporte..."):
                reporte = agent.generar_reporte_errores()
                st.markdown(reporte)
