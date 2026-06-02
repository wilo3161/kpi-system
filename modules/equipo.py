# modules/equipo.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def obtener_hora_ecuador():
    # Ecuador está en UTC-5
    return datetime.utcnow() - timedelta(hours=5)
from database.manager import local_db
from utils.ui import add_back_button, show_module_header
from ai.supply_chain_ai import _ejecutar_prompt  # wilo IA (OpenAI)

# ------------------------------------------------------------------------------
# DATOS INICIALES DEL EQUIPO (fuente única de verdad)
# ------------------------------------------------------------------------------
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
_private_data_path = BASE_DIR / "config" / "private_data.json"

if _private_data_path.exists():
    with open(_private_data_path, "r", encoding="utf-8-sig") as f:
        try:
            _private_data = json.load(f)
            EQUIPO_INICIAL = _private_data.get("equipo", [])
        except Exception:
            EQUIPO_INICIAL = []
else:
    EQUIPO_INICIAL = []

def seed_equipo_if_empty():
    """Inserta los datos del equipo si la colección está vacía."""
    if local_db.count("equipo_logistico") == 0:
        for m in EQUIPO_INICIAL:
            local_db.insert("equipo_logistico", m)


# ------------------------------------------------------------------------------
# ASISTENTE IA (wilo IA)
# ------------------------------------------------------------------------------
def llamar_asistente_ia(prompt_usuario: str, contexto_equipo: dict) -> str:
    """
    Prepara un prompt con el contexto del equipo y la consulta del usuario,
    y lo envía a wilo IA a través del servicio centralizado.
    """
    # Construir descripción textual del equipo
    equipo_txt = "EQUIPO DE TRABAJO DEL CENTRO DE DISTRIBUCIÓN AEROPOSTALE:\n"
    for area, miembros in contexto_equipo.items():
        equipo_txt += f"\nÁrea: {area}\n"
        for m in miembros:
            wa = m.get("whatsapp", "no registrado")
            em = m.get("email", "no registrado")
            equipo_txt += (
                f"  - {m['nombre']} | Cargo: {m['cargo']} | "
                f"WhatsApp: {wa} | Email: {em}\n"
            )

    system_prompt = f"""Eres el asistente inteligente de Wilson Pérez, Jefe de Logística del Centro de Distribución de Aeropostale Ecuador. Su jefe superior es Miguel.

{equipo_txt}

Tu función principal es ayudar a Wilson con la comunicación hacia su equipo:
- Redactar mensajes para enviar por WhatsApp o Email a miembros concretos o grupos.
- Generar reportes breves que se puedan reenviar a Miguel.
- Cuando Wilson pida “enviar un mensaje a…” o “comunicar…”, debes:
    1. Identificar al destinatario exacto (nombre o grupo).
    2. Redactar el texto del mensaje de forma profesional, clara y directa.
    3. Indicar el canal recomendado (WhatsApp si hay número, Email si hay correo).
    4. Mostrar el texto listo para que Wilson lo copie y envíe manualmente.
    5. Si tienes un número de WhatsApp, incluir también un enlace wa.me con el mensaje codificado.
- Si Wilson hace preguntas generales sobre logística, el equipo o las operaciones, responde con información útil y concisa.
- Responde siempre en español formal pero directo. Sé proactivo.
Fecha y hora actual: {obtener_hora_ecuador().strftime('%d/%m/%Y %H:%M')}"""

    prompt_completo = f"{system_prompt}\n\nPregunta del usuario: {prompt_usuario}"
    return _ejecutar_prompt(prompt_completo, "Lo siento, el asistente no está disponible en este momento.")


# ------------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# ------------------------------------------------------------------------------
def show_gestion_equipo():
    add_back_button(key="back_equipo")
    show_module_header("👥 Gestión de Equipo", "Directorio del equipo y asistente inteligente para comunicaciones")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    # Asegurar que los datos del equipo existen (función local recién agregada)
    seed_equipo_if_empty()

    # Cargar datos desde la base de datos
    db_equipo = local_db.find("equipo_logistico")
    EQUIPO_LOGISTICO = {}
    for m in db_equipo:
        area = m.get("area", "Otras Áreas")
        if area not in EQUIPO_LOGISTICO:
            EQUIPO_LOGISTICO[area] = []
        EQUIPO_LOGISTICO[area].append(m)

    # Estado de sesión para el chat
    if "chat_gemini" not in st.session_state:
        st.session_state.chat_gemini = []
    if "prompt_rapido" not in st.session_state:
        st.session_state.prompt_rapido = ""

    # ───────────── PESTAÑAS ─────────────
    is_admin = st.session_state.get("role") == "Administrador"
    if is_admin:
        tabs = st.tabs([
            "📇 Directorio del Equipo", "🌳 Organigrama",
            "⚙️ Administrar Personal", "🤖 Asistente IA",
            "📝 Registro Diario"
        ])
    else:
        tabs = st.tabs(["📇 Directorio del Equipo", "🌳 Organigrama", "📝 Registro Diario"])

    # =====================================================================
    # PESTAÑA 1 – DIRECTORIO DEL EQUIPO
    # =====================================================================
    with tabs[0]:
        st.markdown("### 📋 Directorio de Contactos")
        total_personas = sum(len(miembros) for miembros in EQUIPO_LOGISTICO.values())
        total_areas = len(EQUIPO_LOGISTICO)
        jefe_doc = local_db.find_one("equipo_logistico", {"area": "Liderazgo"})
        jefe = jefe_doc["nombre"] if jefe_doc else "Sin Asignar"

        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total colaboradores", total_personas)
        col2.metric("📂 Áreas funcionales", total_areas)
        col3.metric("👑 Jefe de Logística", jefe)

        # Estilos para las tarjetas (idénticos a tu versión anterior)
        st.markdown("""
        <style>
        .contact-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 10px;
            transition: box-shadow 0.2s;
        }
        .contact-card:hover { box-shadow: 0 4px 20px rgba(56,189,248,0.2); }
        .contact-name { font-size: 1.05em; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
        .contact-role { font-size: 0.82em; color: #94a3b8; margin-bottom: 10px; }
        .contact-badge {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 20px;
            font-size: 0.78em;
            margin: 2px 2px 2px 0;
            font-weight: 500;
            cursor: pointer;
        }
        .badge-wa  { background: rgba(37,211,102,0.15); color: #25d366; border: 1px solid rgba(37,211,102,0.3); }
        .badge-tg  { background: rgba(41,182,246,0.15); color: #29b6f6; border: 1px solid rgba(41,182,246,0.3); }
        .badge-em  { background: rgba(251,146,60,0.15);  color: #fb923c; border: 1px solid rgba(251,146,60,0.3); }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("---")

        area_emojis = {
            "Liderazgo": "👔",
            "Transferencias": "🔄",
            "Distribución": "📦",
            "Empaque": "📮",
            "Ventas Mayoristas": "💰",
            "Cuarentena": "🔍",
        }

        for area_nombre, miembros in EQUIPO_LOGISTICO.items():
            emoji = area_emojis.get(area_nombre, "👤")
            with st.expander(f"{emoji} {area_nombre}  ·  {len(miembros)} persona{'s' if len(miembros) != 1 else ''}", expanded=True):
                n_cols = min(len(miembros), 3)
                if n_cols > 0:
                    cols = st.columns(n_cols)
                    for idx, persona in enumerate(miembros):
                        with cols[idx % n_cols]:
                            wa    = persona.get("whatsapp", "")
                            tg    = persona.get("telegram", wa)
                            email = persona.get("email", "")

                            wa_badge    = f"<span class='contact-badge badge-wa' title='WhatsApp'>📱 {wa}</span>" if wa else ""
                            tg_badge    = f"<span class='contact-badge badge-tg' title='Telegram'>✈️ {tg}</span>" if tg else ""
                            email_badge = f"<span class='contact-badge badge-em' title='Email'>📧 {email}</span>" if email else ""

                            st.markdown(f"""
                            <div class='contact-card'>
                                <div class='contact-name'>{persona.get('nombre','')}</div>
                                <div class='contact-role'>{persona.get('cargo','')}</div>
                                {wa_badge}
                                {tg_badge}
                                {email_badge}
                            </div>
                            """, unsafe_allow_html=True)

    # =====================================================================
    # PESTAÑA 2 – ORGANIGRAMA
    # =====================================================================
    with tabs[1]:
        st.markdown("### 🌳 Organigrama del Centro de Distribución")
        
        org_css = """
        <style>
        .org-tree { display: flex; flex-direction: column; align-items: center; font-family: 'Inter', sans-serif; margin-top: 20px;}
        .org-node { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; margin: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(10px); min-width: 180px;}
        .org-node.lider { border-top: 4px solid #38bdf8; background: rgba(56, 189, 248, 0.1); }
        .org-node.area { border-top: 4px solid #f472b6; background: rgba(244, 114, 182, 0.05); margin-top: 0;}
        .org-node.miembro { border-left: 3px solid #10b981; padding: 8px; margin: 5px 0; background: rgba(16, 185, 129, 0.05); font-size: 0.9em;}
        .org-name { font-weight: bold; color: #e2e8f0; font-size: 1.1em; margin-bottom: 5px;}
        .org-title { font-size: 0.85em; color: #94a3b8; }
        .org-connector-v { width: 2px; height: 30px; background: rgba(255,255,255,0.2); margin: 0 auto;}
        .org-branches { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 20px;}
        .org-branch { display: flex; flex-direction: column; align-items: center; }
        </style>
        """
        
        lideres = EQUIPO_LOGISTICO.get("Liderazgo", [])
        lider_html = ""
        if lideres:
            l = lideres[0]
            lider_html = f"<div class='org-node lider'><div class='org-name'>👔 {l.get('nombre','')}</div><div class='org-title'>{l.get('cargo','')}</div></div>"
        
        branches_html = "<div class='org-branches'>"
        for area, miembros in EQUIPO_LOGISTICO.items():
            if area == "Liderazgo" or not miembros:
                continue
            miembros_html = "".join([f"<div class='org-node miembro'><div class='org-name'>{m.get('nombre','')}</div><div class='org-title'>{m.get('cargo','')}</div></div>" for m in miembros])
            branch = f"""
            <div class='org-branch'>
                <div class='org-connector-v'></div>
                <div class='org-node area'>
                    <div class='org-name'>📁 {area}</div>
                    <div class='org-title'>{len(miembros)} personas</div>
                    <div style='margin-top:10px;'>{miembros_html}</div>
                </div>
            </div>
            """
            branches_html += branch
        branches_html += "</div>"
        
        full_html = f"{org_css}<div class='org-tree'>{lider_html}<div class='org-connector-v'></div>{branches_html}</div>"
        import streamlit.components.v1 as components
        components.html(full_html, height=860, scrolling=True)

    # =====================================================================
    # PESTAÑA 3 – ADMINISTRAR PERSONAL
    # =====================================================================
    if is_admin:
        with tabs[2]:
            st.markdown("### ⚙️ Administrar Personal")
            col_form, col_list = st.columns([1, 1])
            with col_form:
                st.subheader("➕ Añadir Miembro")
                with st.form("form_add_miembro"):
                    new_nombre = st.text_input("Nombre Completo")
                    new_area = st.selectbox("Área", ["Liderazgo", "Transferencias", "Distribución", "Empaque", "Ventas Mayoristas", "Cuarentena", "Otras Áreas"])
                    new_cargo = st.text_input("Cargo")
                    new_email = st.text_input("Email", placeholder="ejemplo@fashionclub.com.ec")
                    new_whatsapp = st.text_input("WhatsApp", placeholder="09XXXXXXXX")
                    new_telegram = st.text_input("Telegram ID", placeholder="Ej: 123456789 (Opcional)")
                    
                    if st.form_submit_button("Guardar Miembro", use_container_width=True):
                        if new_nombre and new_cargo:
                            local_db.insert("equipo_logistico", {
                                "nombre": new_nombre.strip(),
                                "area": new_area,
                                "cargo": new_cargo.strip(),
                                "email": new_email.strip(),
                                "whatsapp": new_whatsapp.strip(),
                                "telegram_id": new_telegram.strip()
                            })
                            st.success(f"✅ {new_nombre} añadido correctamente.")
                            st.rerun()
                        else:
                            st.error("El nombre y el cargo son obligatorios.")
                            
            with col_list:
                st.subheader("🗑️ Eliminar Miembro")
                for area, miembros in EQUIPO_LOGISTICO.items():
                    if miembros:
                        st.markdown(f"**{area}**")
                        for m in miembros:
                            col_name, col_btn = st.columns([3, 1])
                            col_name.write(m.get("nombre",""))
                            if col_btn.button("Eliminar", key=f"del_{m.get('_id', m.get('nombre'))}"):
                                # Para MockLocalDBFallback (si existe el atributo data)
                                if hasattr(local_db, 'data') and 'equipo_logistico' in local_db.data:
                                    local_db.data["equipo_logistico"] = [x for x in local_db.data["equipo_logistico"] if x.get("nombre") != m.get("nombre")]
                                else:
                                    local_db.delete("equipo_logistico", {"nombre": m.get("nombre")})
                                st.rerun()
                        st.divider()

    # =====================================================================
    # PESTAÑA 4 – ASISTENTE IA (wilo IA)
    # =====================================================================
    if is_admin:
        with tabs[3]:
            st.markdown("### 🤖 Asistente Inteligente — wilo IA")
            if len(st.session_state.chat_gemini) == 0:
                st.session_state.chat_gemini.append({"role": "assistant", "content": "¡Hola! Soy wilo IA. ¿En qué puedo ayudarte a gestionar el equipo hoy?"})

            col_izq, col_der = st.columns([0.3, 0.7])
            with col_izq:
                st.subheader("⚡ Acciones rápidas")
                if st.button("📋 Solicitar actividades diarias al equipo", use_container_width=True):
                    st.session_state.prompt_rapido = "Envía un mensaje a todo mi equipo pidiéndoles un resumen de las actividades realizadas hoy."
                    st.rerun()
                if st.button("🗑️ Limpiar conversación", use_container_width=True):
                    st.session_state.chat_gemini = []
                    st.session_state.prompt_rapido = ""
                    st.rerun()
            
                st.divider()
                st.markdown("#### 💬 Enviar por WhatsApp")
                miembros_wa = {"Grupal / Elegir en la app": ""}
                for area, miembros in EQUIPO_LOGISTICO.items():
                    for m in miembros:
                        wa_num = m.get("whatsapp", "").strip()
                        if wa_num:
                            miembros_wa[m["nombre"]] = wa_num
            
                destinatario = st.selectbox("Seleccionar Destinatario:", list(miembros_wa.keys()))
                ultimo_mensaje = next((m["content"] for m in reversed(st.session_state.chat_gemini) if m["role"] == "assistant"), "")
            
                if ultimo_mensaje and "¡Hola! Soy wilo IA" not in ultimo_mensaje:
                    import urllib.parse
                    texto_url = urllib.parse.quote(ultimo_mensaje)
                    num = miembros_wa[destinatario]
                    if num:
                        # Si empieza con 0, lo quitamos y agregamos el 593 (Ecuador)
                        if num.startswith("0"):
                            num = "593" + num[1:]
                        wa_link = f"https://wa.me/{num}?text={texto_url}"
                    else:
                        wa_link = f"https://wa.me/?text={texto_url}"
                
                    st.link_button(f"📲 Abrir WhatsApp", wa_link, type="primary", use_container_width=True)
                else:
                    st.warning("No hay mensaje generado para enviar.")

                st.divider()
                st.markdown("#### ✈️ Enviar a Telegram")
                miembros_tg = {"Mi Telegram Principal": None}
                for area, miembros in EQUIPO_LOGISTICO.items():
                    for m in miembros:
                        tg_id = m.get("telegram_id", "").strip()
                        if tg_id:
                            miembros_tg[m["nombre"]] = tg_id
                        
                destinatario_tg = st.selectbox("Destinatario Telegram:", list(miembros_tg.keys()))
            
                if st.button("Enviar último mensaje por Telegram", use_container_width=True):
                    # Evitar enviar el saludo inicial
                    if ultimo_mensaje and "¡Hola! Soy wilo IA" not in ultimo_mensaje:
                        from utils.telegram_helper import enviar_mensaje_telegram
                        with st.spinner("Enviando a Telegram..."):
                            target_id = miembros_tg[destinatario_tg]
                            res = enviar_mensaje_telegram(ultimo_mensaje, target_chat_id=target_id)
                        if res["success"]:
                            st.success(res["message"])
                        else:
                            st.error(res["message"])
                    else:
                        st.warning("No hay mensaje generado para enviar.")

            with col_der:
                chat_container = st.container(height=400)
                with chat_container:
                    for msg in st.session_state.chat_gemini:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

                # Procesar prompt rápido si existe
                if st.session_state.prompt_rapido:
                    prompt = st.session_state.prompt_rapido
                    st.session_state.prompt_rapido = ""
                    st.session_state.chat_gemini.append({"role": "user", "content": prompt})
                    with st.spinner("🤖 Pensando..."):
                        respuesta = llamar_asistente_ia(prompt, EQUIPO_LOGISTICO)
                    st.session_state.chat_gemini.append({"role": "assistant", "content": respuesta})
                    st.rerun()

                user_input = st.chat_input("Escribe tu mensaje o comando...")
                if user_input:
                    st.session_state.chat_gemini.append({"role": "user", "content": user_input})
                    with st.spinner("🤖 Pensando..."):
                        respuesta = llamar_asistente_ia(user_input, EQUIPO_LOGISTICO)
                    st.session_state.chat_gemini.append({"role": "assistant", "content": respuesta})
                    st.rerun()

                st.info("📋 **Nota:** Los mensajes generados son texto listo para copiar y pegar en WhatsApp o correo. Si hay número registrado, se incluye un enlace wa.me.")

    # =====================================================================
    # PESTAÑA 5 – REGISTRO DIARIO DE ACTIVIDADES
    # =====================================================================
    with tabs[4] if is_admin else tabs[2]:
        st.markdown("### 📝 Registro de Actividades Diarias")
        
        # Filtrar a Wilson Perez y obtener todos los miembros
        miembros_completos = [m.get("nombre") for m in db_equipo if m.get("nombre")]
        miembros_ingreso = [m for m in miembros_completos if m.lower() != "wilson perez"]
        
        from datetime import timedelta
        from datetime import time as dt_time
        
        # Fecha de registro (el corte es a las 20:00, a partir de ahí cuenta para el día siguiente)
        ahora = obtener_hora_ecuador()
        if ahora.hour >= 20:
            fecha_hoy = (ahora + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            fecha_hoy = ahora.strftime("%Y-%m-%d")
        
        # Consultar quiénes ya han registrado para la fecha en curso
        acts_hoy = local_db.find("actividades_diarias", {"fecha": fecha_hoy})
        empleados_con_registro = {a.get("empleado") for a in acts_hoy if a.get("empleado")}
        
        col_form, col_status = st.columns([0.65, 0.35])
        
        with col_status:
            st.markdown("#### 📌 Estado de Ingresos Hoy")
            estado_html = "<div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);'>"
            for emp in miembros_ingreso:
                if emp in empleados_con_registro:
                    estado_html += f"<div style='margin-bottom: 5px; font-weight: 500; color: #10b981;'>🟢 {emp}</div>"
                else:
                    estado_html += f"<div style='margin-bottom: 5px; color: #ef4444;'>🔴 {emp}</div>"
            estado_html += "</div>"
            st.markdown(estado_html, unsafe_allow_html=True)
        
        with col_form:
            now = obtener_hora_ecuador()
            hora_actual = now.time()
            hora_limite = dt_time(20, 0)
            
            # Consultar última emisión del reporte
            estado_cierre = local_db.find_one("estado_sistema", {"id": "cierre_reporte"})
            if not estado_cierre:
                ultima_emision_dt = datetime(1970, 1, 1)
            else:
                ultima_emision_dt = datetime.fromisoformat(estado_cierre.get("ultima_emision", "1970-01-01T00:00:00"))
            
            bloqueado = False
            if not is_admin:
                if hora_actual >= hora_limite:
                    limite_hoy = datetime.combine(now.date(), hora_limite)
                    # Si ya son pasadas las 20:00 y no se ha emitido el reporte después de las 20:00 de hoy
                    if ultima_emision_dt < limite_hoy:
                        bloqueado = True
            
            if bloqueado:
                st.error("⏰ El horario de registro ha finalizado (corte a las 20:00). Estará habilitado nuevamente una vez que el Administrador emita el reporte de hoy.")
            else:
                if ahora.hour >= 20:
                    st.info("🌙 Registro habilitado para el día de MAÑANA.")
                    
                with st.form("form_actividades"):
                    st.subheader("Ingresar Actividad")
                    empleado = st.selectbox("Selecciona tu nombre", [""] + miembros_ingreso)
                    actividad = st.text_area("Describe tus actividades (ej. Transferencias: Ejecución de transferencias de 2,000 prendas...)", height=150)
                    
                    if st.form_submit_button("Guardar Información", use_container_width=True):
                        if empleado and actividad:
                            local_db.insert("actividades_diarias", {
                                "fecha": fecha_hoy,
                                "empleado": empleado,
                                "actividad": actividad,
                                "hora_registro": obtener_hora_ecuador().strftime("%H:%M:%S")
                            })
                            st.success(f"✅ Información guardada correctamente para {empleado}.")
                            st.rerun()
                        else:
                            st.error("Por favor, selecciona tu nombre y describe la actividad.")
        
        # SECCIÓN EXCLUSIVA PARA EL ADMINISTRADOR
        if is_admin:
            st.divider()
            st.subheader("📊 Reporte Consolidado (Administrador)")
            
            fecha_consulta = st.date_input("Consultar registros por fecha:", obtener_hora_ecuador().date())
            fecha_str = fecha_consulta.strftime("%Y-%m-%d")
            
            if st.button("Generar Registro", type="primary", use_container_width=True):
                # Registrar que se emitió el reporte para habilitar la plataforma
                now_str = obtener_hora_ecuador().isoformat()
                estado_cierre = local_db.find_one("estado_sistema", {"id": "cierre_reporte"})
                if estado_cierre:
                    # Usar delete sobre data para TinyDB/mock local_db, de forma segura
                    if hasattr(local_db, 'data') and 'estado_sistema' in local_db.data:
                        local_db.data["estado_sistema"] = [x for x in local_db.data["estado_sistema"] if x.get("id") != "cierre_reporte"]
                    else:
                        local_db.delete("estado_sistema", {"id": "cierre_reporte"})
                local_db.insert("estado_sistema", {"id": "cierre_reporte", "ultima_emision": now_str})
                
                acts_consulta = local_db.find("actividades_diarias", {"fecha": fecha_str})
                if acts_consulta:
                    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                    fecha_formateada = f"{fecha_consulta.day:02d} de {meses[fecha_consulta.month]} de {fecha_consulta.year}"
                    
                    reporte = f"Reporte de actividades - {fecha_formateada}\n\n"
                    
                    # Agrupar por empleado para mantener todo en un solo bloque por persona
                    acts_por_emp = {}
                    for a in acts_consulta:
                        emp = a.get("empleado", "Desconocido")
                        if emp not in acts_por_emp:
                            acts_por_emp[emp] = []
                        acts_por_emp[emp].append(a.get("actividad", ""))
                    
                    for emp, textos in acts_por_emp.items():
                        reporte += f"{emp}:\n\n"
                        for t in textos:
                            reporte += f"{t}\n\n"
                    
                    st.code(reporte, language="text")
                else:
                    st.warning(f"Aún no hay actividades registradas para la fecha: {fecha_str}.")

    st.markdown('</div>', unsafe_allow_html=True)
