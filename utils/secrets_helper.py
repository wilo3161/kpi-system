# utils/secrets_helper.py
"""
Helper único para obtener credenciales y configuraciones sensibles.
Busca en:
    1. st.secrets con la clave exacta (ej: secrets["telegram"]["TOKEN"])
    2. st.secrets con la clave en minúscula (ej: secrets["telegram"]["token"])
    3. Colección 'config' de la base de datos (usando la clave normalizada)
    4. Valor por defecto opcional.
"""

import streamlit as st
from typing import Optional, Any

# La importación de local_db es diferida para evitar dependencias circulares
_local_db = None

def _get_db():
    global _local_db
    if _local_db is None:
        try:
            from database.manager import local_db
            _local_db = local_db
        except Exception:
            _local_db = None
    return _local_db

def obtener_credencial(servicio: str, clave: str, default: Any = None) -> Any:
    """
    Obtiene una credencial para un servicio.
    """
    # 1. Intentar desde st.secrets con la clave exacta
    try:
        secrets_dict = st.secrets.get(servicio, {})
        if clave in secrets_dict and secrets_dict[clave]:
            return secrets_dict[clave]
    except (KeyError, AttributeError, TypeError):
        pass

    # 2. Intentar desde st.secrets con la clave en minúscula
    try:
        secrets_dict = st.secrets.get(servicio, {})
        clave_lower = clave.lower()
        if clave_lower in secrets_dict and secrets_dict[clave_lower]:
            return secrets_dict[clave_lower]
    except (KeyError, AttributeError, TypeError):
        pass

    # 3. Intentar desde la base de datos (colección 'config')
    db = _get_db()
    if db is not None:
        config_key = f"{servicio.lower()}_{clave.lower()}"
        try:
            valor = db.leer_config(config_key)
            if valor is not None:
                return valor
        except Exception:
            pass

    return default

def obtener_api_key_gemini() -> Optional[str]:
    """
    Helper específico para la API key de Gemini, intenta varios nombres comunes.
    """
    for key_name in ("api_key", "API_KEY", "api_key_gemini", "GEMINI_API_KEY"):
        val = obtener_credencial("gemini", key_name)
        if val:
            return val
    import os
    return os.environ.get("GEMINI_API_KEY")
