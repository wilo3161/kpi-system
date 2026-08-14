# modules/equipo.py
import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

TZ_GUAYAQUIL = ZoneInfo("America/Guayaquil")

def obtener_hora_ecuador():
    return datetime.now(TZ_GUAYAQUIL)
from database.manager import local_db
from utils.ui import add_back_button, show_module_header

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
            "⚙️ Administrar Personal",
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
        jefe = jefe_doc.get("nombre", "Sin Asignar") if jefe_doc else "Sin Asignar"

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
    # PESTAÑA 4 – REGISTRO DIARIO DE ACTIVIDADES
    # =====================================================================
    with tabs[3] if is_admin else tabs[2]:
        from datetime import timedelta
        from datetime import time as dt_time
        from utils.telegram_helper import enviar_mensaje_telegram

        st.markdown("""
        <style>
        .report-header-card {
            background: linear-gradient(135deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,0.9) 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .status-badge-ok {
            background: rgba(16,185,129,0.15);
            color: #10b981;
            border: 1px solid rgba(16,185,129,0.3);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-badge-pending {
            background: rgba(239,68,68,0.15);
            color: #ef4444;
            border: 1px solid rgba(239,68,68,0.3);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("### 📝 Registro Diario de Actividades")

        # Excluir a Wilson Perez (El Jefe) del reporte obligatorio
        miembros_completos = [m.get("nombre") for m in db_equipo if m.get("nombre")]
        miembros_ingreso = [
            m for m in miembros_completos 
            if "wilson" not in m.lower() or "perez" not in m.lower()
        ]

        # Hora actual en Ecuador y fecha de registro
        ahora = obtener_hora_ecuador()
        if ahora.hour >= 20:
            fecha_hoy = (ahora + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            fecha_hoy = ahora.strftime("%Y-%m-%d")

        # Consultar quienes han registrado hoy
        acts_hoy = local_db.find("actividades_diarias", {"fecha": fecha_hoy})
        registros_dict = {a.get("empleado"): a for a in acts_hoy if a.get("empleado")}
        empleados_con_registro = set(registros_dict.keys())

        # ────── DASHBOARD DE ESTADO DE REPORTES ──────
        st.markdown("#### 📊 Estado de Reportes del Equipo (Corte 20:00 PM)")
        total_esperados = len(miembros_ingreso)
        total_reportados = len(empleados_con_registro.intersection(set(miembros_ingreso)))
        total_pendientes = max(0, total_esperados - total_reportados)

        c_met1, c_met2, c_met3 = st.columns(3)
        c_met1.metric("👥 Personal Esperado", f"{total_esperados}")
        c_met2.metric("🟢 Han Reportado", f"{total_reportados}")
        c_met3.metric("🔴 Sin Reportar", f"{total_pendientes}")

        st.write("")
        col_ok, col_pending = st.columns(2)

        with col_ok:
            st.markdown("##### 🟢 Personal que ya reportó")
            if not empleados_con_registro:
                st.info("Aún nadie ha registrado actividades para este ciclo.")
            else:
                for emp in miembros_ingreso:
                    if emp in empleados_con_registro:
                        reg = registros_dict.get(emp, {})
                        hora_reg = reg.get("hora_registro", "Registrado")
                        st.markdown(f"""
                        <div style="background: rgba(16,185,129,0.06); border-left: 4px solid #10b981; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight:600; color:#e2e8f0;">{emp}</span>
                            <span class="status-badge-ok">🕒 {hora_reg}</span>
                        </div>
                        """, unsafe_allow_html=True)

        with col_pending:
            st.markdown("##### 🔴 Pendientes por reportar")
            pendientes = [m for m in miembros_ingreso if m not in empleados_con_registro]
            if not pendientes:
                st.success("🎉 ¡Excelente! Todo el equipo ha completado su reporte de hoy.")
            else:
                for emp in pendientes:
                    st.markdown(f"""
                    <div style="background: rgba(239,68,68,0.06); border-left: 4px solid #ef4444; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight:600; color:#e2e8f0;">{emp}</span>
                        <span class="status-badge-pending">⏳ Pendiente</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

        # ────── FORMULARIO DE INGRESO ──────
        col_form, col_info = st.columns([0.65, 0.35])

        with col_form:
            st.subheader("✍️ Ingresar tus Actividades del Día")
            hora_actual = ahora.time()
            hora_limite = dt_time(20, 0)

            if ahora.hour >= 20:
                st.info("🌙 Registro habilitado para el próximo turno de trabajo.")

            with st.form("form_actividades_diarias", clear_on_submit=True):
                empleado_sel = st.selectbox("Selecciona tu Nombre:", ["-- Selecciona tu nombre --"] + miembros_ingreso)
                actividades_txt = st.text_area(
                    "Describe tus actividades diarias (separa tareas por línea o categoría):",
                    placeholder="Ejemplo:\nTransferencias: Ejecución de transferencias de 2,000 prendas...\nProcesamiento: Realizó el 'pitado' y enfundado...",
                    height=180
                )
                btn_guardar = st.form_submit_button("📤 Enviar Mi Reporte Diario", type="primary", use_container_width=True)

                if btn_guardar:
                    if empleado_sel and empleado_sel != "-- Selecciona tu nombre --" and actividades_txt.strip():
                        # Guardar o actualizar registro del colaborador
                        local_db.insert("actividades_diarias", {
                            "fecha": fecha_hoy,
                            "empleado": empleado_sel,
                            "actividad": actividades_txt.strip(),
                            "hora_registro": obtener_hora_ecuador().strftime("%H:%M:%S")
                        })

                        # Extraer el primer nombre para la respuesta personalizada
                        primer_nombre = empleado_sel.strip().split()[0].title()
                        st.success(f"🎉 ¡Gracias {primer_nombre} por tu reporte de hoy! Tu actividad fue registrada con éxito.")
                        st.rerun()
                    else:
                        st.error("⚠️ Por favor selecciona tu nombre e ingresa el detalle de tus actividades.")

        with col_info:
            st.markdown("""
            <div class="report-header-card">
                <h4 style="color:#38bdf8; margin-top:0;">💡 Guía para el Registro</h4>
                <ul style="color:#94a3b8; font-size:0.9rem; padding-left:20px;">
                    <li><b>Horario de corte:</b> 20:00 PM (8:00 PM).</li>
                    <li><b>Formato sugerido:</b> Agrupa por áreas (<i>Transferencias, Procesamiento, Logística, etc.</i>).</li>
                    <li><b>Jefatura:</b> Wilson Pérez no realiza reporte diario.</li>
                    <li><b>Telegram:</b> El reporte consolidado se envía automáticamente al Telegram de Gerencia.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # ────── SECCIÓN ADMINISTRADOR / CONSOLIDADO ──────
        if is_admin:
            st.divider()
            st.subheader("🚀 Consolidación de Reportes Diarios y Envío a Telegram")
            
            f_sel = st.date_input("Fecha del reporte:", obtener_hora_ecuador().date())
            f_str = f_sel.strftime("%Y-%m-%d")

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                btn_generar = st.button("📋 Generar y Consolidar Reporte", type="primary", use_container_width=True)
            with col_b2:
                btn_telegram = st.button("✈️ Enviar Consolidado a Telegram", use_container_width=True)

            if btn_generar or btn_telegram:
                acts_registradas = local_db.find("actividades_diarias", {"fecha": f_str})
                
                # Nombres de meses en español
                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                fecha_fmt = f"{f_sel.day:02d} de {meses[f_sel.month]} de {f_sel.year}"

                # Mapear actividades por empleado
                dict_actividades = {}
                for a in acts_registradas:
                    emp = a.get("empleado")
                    txt = a.get("actividad", "").strip()
                    if emp and txt:
                        if emp not in dict_actividades:
                            dict_actividades[emp] = []
                        dict_actividades[emp].append(txt)

                # Construir el texto en el formato profesional exacto solicitado
                lineas_reporte = [f"*Reporte de actividades - {fecha_fmt}*\n"]

                # Primero agregar quienes sí reportaron
                for emp in miembros_ingreso:
                    if emp in dict_actividades:
                        lineas_reporte.append(f"*{emp}:*")
                        for act_block in dict_actividades[emp]:
                            for line in act_block.split("\n"):
                                if line.strip():
                                    lineas_reporte.append(line.strip())
                        lineas_reporte.append("") # Línea en blanco entre personas

                # Luego agregar a quienes NO reportaron
                for emp in miembros_ingreso:
                    if emp not in dict_actividades:
                        lineas_reporte.append(f"*{emp}:* No reportó sus actividades diarias.\n")

                reporte_consolidado = "\n".join(lineas_reporte).strip()

                # Mostrar vista previa profesional
                st.markdown("#### 📄 Vista Previa del Reporte Consolidado:")
                st.code(reporte_consolidado, language="text")

                # Enviar a Telegram si fue solicitado
                if btn_telegram:
                    with st.spinner("Enviando reporte a Telegram..."):
                        res_tg = enviar_mensaje_telegram(reporte_consolidado)
                        if res_tg.get("success"):
                            st.success("✈️ ¡Reporte consolidado enviado exitosamente a Telegram!")
                        else:
                            st.warning(f"⚠️ Nota de Telegram: {res_tg.get('message', 'No se pudo enviar. Verifica credenciales.')}")

    st.markdown('</div>', unsafe_allow_html=True)
