# modules/equipo.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database.manager import local_db
from utils.ui import add_back_button, show_module_header
from ai.supply_chain_ai import _ejecutar_prompt  # Gemini centralizado

# ------------------------------------------------------------------------------
# DATOS INICIALES DEL EQUIPO (fuente única de verdad)
# ------------------------------------------------------------------------------
EQUIPO_INICIAL = [
    {"nombre": "Wilson Pérez", "cargo": "Jefe de Logística / Centro de Distribución", "area": "Liderazgo", "email": "wperez@fashionclub.com.ec", "whatsapp": "0993052744", "telegram": "0993052744"},
    {"nombre": "Andrés Yépez", "cargo": "Transferencias Fashion", "area": "Transferencias", "email": "cyepez@fashionclub.com.ec", "whatsapp": "0995529505", "telegram": "0995529505"},
    {"nombre": "Luis Perugachi", "cargo": "Pivote de Transferencias y Distribución", "area": "Transferencias", "email": "lperugachi@fashionclub.com.ec", "whatsapp": "0993012238", "telegram": "0993012238"},
    {"nombre": "Josué Imbacúan", "cargo": "Transferencias Tempo", "area": "Transferencias", "email": "jimbacuan@fashionclub.com.ec", "whatsapp": "0988856682", "telegram": "0988856682"},
    {"nombre": "Jessica Suarez", "cargo": "Distribución", "area": "Distribución", "email": "jsuarez@fashionclub.com.ec", "whatsapp": "0981951052", "telegram": "0981951052"},
    {"nombre": "Jhonny Villa", "cargo": "Encargado de Empaque y Gestión de Guías", "area": "Empaque", "email": "jvilla@fashionclub.com.ec", "whatsapp": "0968491147", "telegram": "0968491147"},
    {"nombre": "Simón Vera", "cargo": "Apoyo en Guías y Envíos", "area": "Empaque", "email": "bodega@fashionclub.com.ec", "whatsapp": "0969341528", "telegram": "0969341528"},
    {"nombre": "Jhonny Guadalupe", "cargo": "Ventas al Por Mayor", "area": "Ventas Mayoristas", "email": "jguadalupe@fashionclub.com.ec", "whatsapp": "0985603835", "telegram": "0985603835"},
    {"nombre": "Rocio Cadena", "cargo": "Ventas al Por Mayor", "area": "Ventas Mayoristas", "email": "jcadena@fashionclub.com.ec", "whatsapp": "0992062862", "telegram": "0992062862"},
    {"nombre": "Diana García", "cargo": "Reprocesado de Prendas en Cuarentena", "area": "Cuarentena", "email": "dgarcia@fashionclub.com.ec", "whatsapp": "0980837688", "telegram": "0980837688"},
]

def seed_equipo_if_empty():
    """Inserta los datos del equipo si la colección está vacía."""
    if local_db.count("equipo_logistico") == 0:
        for m in EQUIPO_INICIAL:
            local_db.insert("equipo_logistico", m)


# ------------------------------------------------------------------------------
# ASISTENTE IA (Gemini, usando el módulo centralizado)
# ------------------------------------------------------------------------------
def llamar_asistente_ia(prompt_usuario: str, contexto_equipo: dict) -> str:
    """
    Prepara un prompt con el contexto del equipo y la consulta del usuario,
    y lo envía a Gemini a través del servicio centralizado de IA.
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
Fecha y hora actual: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""

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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📇 Directorio del Equipo", "🌳 Organigrama",
        "⚙️ Administrar Personal", "🤖 Asistente IA"
    ])

    # =====================================================================
    # PESTAÑA 1 – DIRECTORIO DEL EQUIPO
    # =====================================================================
    with tab1:
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
            "Liderazgo": "👑",
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
    with tab2:
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
            lider_html = f"<div class='org-node lider'><div class='org-name'>👑 {l.get('nombre','')}</div><div class='org-title'>{l.get('cargo','')}</div></div>"
        
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
    with tab3:
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
                
                if st.form_submit_button("Guardar Miembro", use_container_width=True):
                    if new_nombre and new_cargo:
                        local_db.insert("equipo_logistico", {
                            "nombre": new_nombre.strip(),
                            "area": new_area,
                            "cargo": new_cargo.strip(),
                            "email": new_email.strip(),
                            "whatsapp": new_whatsapp.strip()
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
    # PESTAÑA 4 – ASISTENTE IA (Gemini)
    # =====================================================================
    with tab4:
        st.markdown("### 🤖 Asistente Inteligente — Gemini")
        if len(st.session_state.chat_gemini) == 0:
            st.session_state.chat_gemini.append({"role": "assistant", "content": "¡Hola! Soy tu asistente IA. ¿En qué puedo ayudarte a gestionar el equipo hoy?"})

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

    st.markdown('</div>', unsafe_allow_html=True)
