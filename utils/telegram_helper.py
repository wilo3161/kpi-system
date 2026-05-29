# utils/telegram_helper.py
import requests
import logging
from utils.secrets_helper import obtener_credencial

logger = logging.getLogger(__name__)

def enviar_mensaje_telegram(mensaje: str, target_chat_id: str = None) -> dict:
    """
    Envía un mensaje a través del bot de Telegram usando las credenciales configuradas.
    Si se proporciona target_chat_id, lo usa en lugar del configurado por defecto.
    Retorna un diccionario con {'success': bool, 'message': str}.
    """
    token = obtener_credencial("telegram", "TOKEN")
    chat_id = target_chat_id if target_chat_id else obtener_credencial("telegram", "CHAT_ID")

    if not token or not chat_id:
        return {
            "success": False, 
            "message": "Faltan credenciales de Telegram o CHAT_ID destino."
        }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return {"success": True, "message": "Mensaje enviado por Telegram exitosamente."}
        else:
            logger.error("Error Telegram API: %s", response.text)
            return {"success": False, "message": f"Error al enviar: {response.status_code} - {response.text}"}
    except Exception as e:
        logger.error("Excepción Telegram API: %s", e)
        return {"success": False, "message": f"Error de conexión: {str(e)}"}
