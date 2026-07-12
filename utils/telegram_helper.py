import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.secrets_helper import obtener_credencial

logger = logging.getLogger(__name__)

class APIError(Exception):
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APIError, httpx.TimeoutException))
)
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

    timeout = httpx.Timeout(15.0)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                return {"success": True, "message": "Mensaje enviado por Telegram exitosamente."}
            else:
                logger.error("Error Telegram API: %s", response.text)
                raise APIError(f"Error al enviar: {response.status_code} - {response.text}")
    except httpx.TimeoutException as e:
        logger.error("Timeout Telegram API: %s", e)
        raise
    except Exception as e:
        if isinstance(e, APIError):
            raise
        logger.error("Excepción Telegram API: %s", e)
        return {"success": False, "message": f"Error de conexión: {str(e)}"}
