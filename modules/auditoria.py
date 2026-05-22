# modules/auditoria.py
import streamlit as st
import pandas as pd
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from database.manager import local_db
from utils.ui import add_back_button, show_module_header
from services.notifications import GestorCorreo       # Clase centralizada
from ai.supply_chain_ai import _ejecutar_prompt       # IA centralizada


def _listar_correos(gestor: GestorCorreo, carpeta: str = "INBOX", limite: int = 20):
    """Obtiene los últimos correos usando el gestor centralizado."""
    mail = gestor.conectar_imap()
    if mail is None:
        return [{"id": "err", "asunto": "Error de conexión IMAP"}]

    correos = []
    try:
        mail.select(carpeta)
        _, data = mail.search(None, "ALL")
        ids = data[0].split()
        ids_recientes = ids[-limite:] if len(ids) >= limite else ids
        ids_recientes = list(reversed(ids_recientes))

        for eid in ids_recientes:
            try:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                asunto = email.header.decode_header(msg["Subject"] or "Sin asunto")
                asunto_str = asunto[0][0]
                if isinstance(asunto_str, bytes):
                    asunto_str = asunto_str.decode(asunto[0][1] or "utf-8", errors="replace")

                de = msg.get("From", "")
                fecha = msg.get("Date", "")
                cuerpo = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                cuerpo = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        cuerpo = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")

                correos.append({
                    "id": eid.decode(),
                    "asunto": str(asunto_str)[:80],
                    "de": str(de)[:60],
                    "fecha": str(fecha)[:30],
                    "cuerpo": str(cuerpo)[:3000]
                })
            except Exception:
                continue
    except Exception as e:
        correos.append({"id": "err", "asunto": f"Error: {e}"})
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    return correos


def _analizar_con_gemini(asunto: str, cuerpo: str, accion: str = "resumir") -> str:
    """Usa el servicio centralizado de IA para analizar o redactar respuesta."""
    if accion == "resumir":
        prompt = f"""Eres un asistente ejecutivo de Fashion Club Ecuador (Centro de Distribución Aeropostale).
Analiza este correo y proporciona:
1. Resumen en 2-3 líneas
2. Prioridad: ALTA / MEDIA / BAJA
3. Acción recomendada

Asunto: {asunto}
Contenido: {cuerpo[:1500]}"""
    elif accion == "responder":
        prompt = f"""Eres el asistente de Wilson Pérez, Jefe de Logística de Fashion Club Ecuador.
Redacta una respuesta profesional, cordial y concisa (máx 200 palabras) para este correo.
Firma como: Wilson Pérez | Jefe de Logística | Fashion Club Ecuador | wperez@fashionclub.com.ec

Asunto: {asunto}
Correo original: {cuerpo[:1500]}"""
    else:
        prompt = cuerpo[:2000]

    return _ejecutar_prompt(prompt, "No se pudo completar el análisis.")


def show_gestor_correos():
    add_back_button("back_correos")
    show_module_header("📧 Gestión de Correos", "Bandeja · Redactar · Análisis con IA")

    gestor = GestorCorreo()

    # Verificar que las credenciales estén configuradas
    if not gestor.config.get("email_user") or not gestor.config.get("email_password"):
        st.warning("Las credenciales de correo no están configuradas en secrets.toml o en la base de datos.")
        return

    if "correos_lista" not in st.session_state:
        st.session_state.correos_lista = []
    if "correo_seleccionado" not in st.session_state:
        st.session_state.correo_seleccionado = None

    # Botón de conexión
    if st.button("🔌 Conectar / Actualizar", use_container_width=True):
        st.session_state.correos_lista = _listar_correos(gestor, limite=25)
        if st.session_state.correos_lista and st.session_state.correos_lista[0].get("id") != "err":
            st.success(f"Conectado — {len(st.session_state.correos_lista)} correos recientes")
        else:
            st.error("No se pudo conectar al servidor IMAP.")
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📥 Bandeja", "✏️ Redactar", "🤖 Análisis IA"])

    with tab1:
        for i, c in enumerate(st.session_state.correos_lista):
            if st.button(f"👁 {c.get('asunto')}", key=f"v_{i}"):
                st.session_state.correo_seleccionado = c
        sel = st.session_state.correo_seleccionado
        if sel:
            st.markdown(f"### {sel['asunto']}")
            st.text(sel['cuerpo'][:2000])

    with tab2:
        with st.form("redactar"):
            para = st.text_input("Para")
            asunto = st.text_input("Asunto")
            cuerpo = st.text_area("Mensaje", height=200)
            if st.form_submit_button("📤 Enviar"):
                if not para or not asunto or not cuerpo:
                    st.error("Completa todos los campos.")
                else:
                    exito = gestor.enviar_correo([para], asunto, f"<div>{cuerpo}</div>")
                    if exito:
                        st.success("Correo enviado correctamente.")
                    else:
                        st.error("Error al enviar el correo.")

    with tab3:
        if st.session_state.correo_seleccionado:
            c = st.session_state.correo_seleccionado
            if st.button("🤖 Analizar seleccionado (resumen)"):
                with st.spinner("Analizando..."):
                    st.write(_analizar_con_gemini(c['asunto'], c['cuerpo'], "resumir"))
            if st.button("📝 Redactar respuesta sugerida"):
                with st.spinner("Redactando respuesta..."):
                    st.code(_analizar_con_gemini(c['asunto'], c['cuerpo'], "responder"), language="markdown")
        else:
            st.info("Selecciona un correo de la bandeja para analizarlo.")
