# modules/auditoria.py
# ============================================================================
# AUDITORÍA DE CORREOS - GESTIÓN DE BANDEJA Y ANÁLISIS CON IA
# Versión robustecida: manejo de errores, logs, validación de credenciales
# ============================================================================

import streamlit as st
import pandas as pd
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import logging
import traceback

from database.manager import local_db
from utils.ui import add_back_button, show_module_header
from services.notifications import GestorCorreo
from ai.supply_chain_ai import _ejecutar_prompt

logger = logging.getLogger(__name__)

def _listar_correos(gestor: GestorCorreo, carpeta: str = "INBOX", limite: int = 20):
    """Obtiene los últimos correos usando el gestor centralizado (robustecido)."""
    try:
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
                except Exception as e:
                    logger.warning(f"Error procesando correo {eid}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error en IMAP: {e}")
            correos.append({"id": "err", "asunto": f"Error: {e}"})
        finally:
            try:
                mail.close()
            except:
                pass
            try:
                mail.logout()
            except:
                pass

        return correos
    except Exception as e:
        logger.exception(e)
        return [{"id": "err", "asunto": f"Excepción: {e}"}]

    except Exception as e:
        logger.error(f"Error en análisis IA: {e}")
        return "Error al procesar la solicitud de IA."

def show_gestor_correos():
    try:
        add_back_button(key="back_correos")
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
            with st.spinner("Conectando al servidor de correo..."):
                st.session_state.correos_lista = _listar_correos(gestor, limite=25)
                if st.session_state.correos_lista and st.session_state.correos_lista[0].get("id") != "err":
                    st.success(f"Conectado — {len(st.session_state.correos_lista)} correos recientes")
                else:
                    st.error("No se pudo conectar al servidor IMAP.")
                st.rerun()

        tab1, tab2, tab3 = st.tabs(["📥 Bandeja", "✏️ Redactar", "🤖 Análisis IA"])

        with tab1:
            if st.session_state.correos_lista:
                col_lista, col_detalle = st.columns([1, 2])
                
                with col_lista:
                    st.subheader("Bandeja de Entrada")
                    for i, c in enumerate(st.session_state.correos_lista):
                        if c.get("id") == "err":
                            st.error(c["asunto"])
                        else:
                            # Botón tipo lista de correo
                            label = f"**{c.get('de', 'Desconocido')[:20]}**\n{c.get('asunto')[:30]}..."
                            if st.button(label, key=f"v_{i}", use_container_width=True):
                                st.session_state.correo_seleccionado = c
                
                with col_detalle:
                    sel = st.session_state.correo_seleccionado
                    if sel:
                        st.markdown(f"### 📨 {sel['asunto']}")
                        st.markdown(f"**De:** {sel['de']}")
                        st.markdown(f"**Fecha:** {sel['fecha']}")
                        st.divider()
                        st.text_area("Mensaje Original", sel['cuerpo'][:2000], height=200, disabled=True)
                        
                        st.divider()
                        except Exception as e:
                            st.error(f"Excepción al enviar: {e}")
                            logger.exception(e)

    except Exception as e:
        st.error(f"Error general en Gestión de Correos: {e}")
        logger.exception(e)
