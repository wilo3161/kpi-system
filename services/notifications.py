# services/notifications.py
"""
Servicio de notificaciones centralizadas: Telegram, Correo, WhatsApp.
Todas las credenciales se obtienen desde utils.secrets_helper.
"""

import streamlit as st
import requests
import imaplib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from database.manager import local_db
from utils.secrets_helper import obtener_credencial


# ---------------------------------------------------------------------------
# Centro de notificaciones en BD
# ---------------------------------------------------------------------------
class CentroNotificaciones:
    @staticmethod
    def crear(tipo, mensaje, canal="ui", usuario_destino=None):
        doc = {
            "tipo": tipo, "mensaje": mensaje, "canal": canal,
            "timestamp": datetime.utcnow(), "leida": False,
            "usuario_destino": usuario_destino
        }
        local_db.insert("notificaciones", doc)

    @staticmethod
    def no_leidas(usuario):
        return local_db.find("notificaciones", {"usuario_destino": usuario, "leida": False})

    @staticmethod
    def marcar_todas_leidas(usuario):
        local_db.update_many("notificaciones", {"usuario_destino": usuario}, {"leida": True})


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
class TelegramBot:
    def __init__(self):
        self.token = obtener_credencial("telegram", "TOKEN")
        self.chat_id = obtener_credencial("telegram", "CHAT_ID")
        self.connected = self.verificar_conexion() if self.token else False

    def verificar_conexion(self):
        try:
            url = f"https://api.telegram.org/bot{self.token}/getMe"
            resp = requests.get(url, timeout=5).json()
            return resp.get("ok", False)
        except Exception:
            return False

    def enviar_mensaje(self, texto, parse_mode="HTML", chat_id=None):
        """
        Envía un mensaje de Telegram. Si se proporciona chat_id, se usa ese destino;
        en caso contrario, el configurado por defecto.
        """
        if not self.token:
            return {"ok": False, "error": "Token no configurado"}

        target = chat_id or self.chat_id
        if not target:
            return {"ok": False, "error": "No hay chat_id disponible"}

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        resp = requests.post(url, json={"chat_id": target, "text": texto, "parse_mode": parse_mode}).json()

        if resp.get("ok"):
            local_db.insert("telegram_log", {
                "texto": texto, "chat_id": target,
                "timestamp": datetime.utcnow()
            })
        return resp

    def enviar_reporte_kpi(self, kpi_data):
        texto = (
            f"📊 <b>REPORTE DIARIO — AEROPOSTALE</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 Unidades transferidas: {kpi_data.get('total_unidades',0):,}\n"
            f"🏪 Tiendas activas: {kpi_data.get('tiendas_procesadas',0)}\n"
            f"💰 Valor procesado: ${kpi_data.get('total_facturado',0):,.2f}"
        )
        return self.enviar_mensaje(texto)


# ---------------------------------------------------------------------------
# Correo electrónico (IMAP + SMTP)
# ---------------------------------------------------------------------------
class GestorCorreo:
    def __init__(self):
        self.config = {
            "imap_server": obtener_credencial("email", "IMAP_SERVER") or "mail.fashionclub.com.ec",
            "imap_port": int(obtener_credencial("email", "IMAP_PORT") or 993),
            "smtp_server": obtener_credencial("email", "SMTP_SERVER") or "mail.fashionclub.com.ec",
            "smtp_port": int(obtener_credencial("email", "SMTP_PORT") or 587),
            "email_user": obtener_credencial("email", "SMTP_USER"),
            "email_password": obtener_credencial("email", "SMTP_PASS"),
        }

    def conectar_imap(self):
        """Retorna la conexión IMAP o None si falla."""
        try:
            mail = imaplib.IMAP4_SSL(self.config["imap_server"], self.config["imap_port"])
            mail.login(self.config["email_user"], self.config["email_password"])
            return mail
        except Exception:
            return None

    def enviar_correo(self, destinatarios, asunto, cuerpo_html, adjuntos=None, cc=None):
        """
        Envía un correo electrónico a una lista de destinatarios.
        Retorna True si se envió correctamente, False en caso de error.
        """
        try:
            # Sanitizar headers para evitar CRLF/Header Injection
            asunto_seguro = "".join(asunto.splitlines())
            dest_seguros = [d.replace('\r', '').replace('\n', '').strip() for d in destinatarios]
            
            msg = MIMEMultipart()
            msg['From'] = self.config["email_user"]
            msg['To'] = ", ".join(dest_seguros)
            msg['Subject'] = asunto_seguro
            if cc:
                cc_seguros = [c.replace('\r', '').replace('\n', '').strip() for c in cc]
                msg['Cc'] = ", ".join(cc_seguros)
            msg.attach(MIMEText(cuerpo_html, 'html'))

            if adjuntos:
                for adj in adjuntos:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(adj['data'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={adj['filename']}")
                    msg.attach(part)

            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                server.starttls()
                server.login(self.config["email_user"], self.config["email_password"])
                server.send_message(msg)
            return True
        except Exception as e:
            st.error(f"Error enviando correo: {e}")
            return False


# ---------------------------------------------------------------------------
# WhatsApp (pywhatkit + Twilio fallback)
# ---------------------------------------------------------------------------
class WhatsAppReporter:
    def __init__(self):
        self.metodo = obtener_credencial("whatsapp", "metodo") or "pywhatkit"

    def enviar_mensaje_programado(self, numero, texto, hora, minuto):
        try:
            import pywhatkit
            pywhatkit.sendwhatmsg(numero, texto, hora, minuto)
            return True
        except Exception:
            return False

    def enviar_mensaje_directo(self, numero, texto):
        """Intenta enviar un mensaje instantáneo vía pywhatkit, o Twilio como fallback."""
        try:
            import pywhatkit
            # sendwhatmsg_instantly no existe en todas las versiones, usamos alternativa
            # Enviar con hora actual + 2 minutos para evitar bloqueos
            from datetime import datetime, timedelta
            ahora = datetime.now() + timedelta(minutes=2)
            pywhatkit.sendwhatmsg(numero, texto, ahora.hour, ahora.minute, wait_time=15)
            return True
        except Exception:
            return self.enviar_via_twilio(numero, texto)

    def enviar_via_twilio(self, numero, texto):
        sid   = obtener_credencial("whatsapp", "twilio_sid")
        token = obtener_credencial("whatsapp", "twilio_token")
        from_ = obtener_credencial("whatsapp", "numero_origen")
        if sid and token and from_:
            try:
                from twilio.rest import Client
                client = Client(sid, token)
                client.messages.create(body=texto, from_=from_, to=f"whatsapp:{numero}")
                return True
            except Exception:
                return False
        return False
