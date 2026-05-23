"""
utils/roles.py — Sistema de Roles y Permisos AEROPOSTALE ERP (v2)
====================================================================
- Control total por roles (Administrador, Bodega, Tienda, Ventas)
- Protección de visualización por tienda (solo ven sus guías)
- Bloqueo de accesos no autorizados
- Seed automático de usuarios desde stores_data y equipo_logistico
"""

import streamlit as st
from utils.common import hash_password
from config.stores_data import TIENDAS_DATA

# =============================================================================
# MATRIZ DE PERMISOS — ÚNICA FUENTE DE VERDAD
# =============================================================================
ROLE_PERMISSIONS = {
    "Administrador": [
        "dashboard_kpis", "kpi_analytics", "reconciliacion", "auditoria_correos",
        "logistica", "equipo", "guias", "inventario", "recepcion", "configuracion",
    ],
    "Bodega": [
        "guias", "inventario", "recepcion",
    ],
    "Ventas": [
        "dashboard_kpis", "kpi_analytics", "logistica",
    ],
    "Tienda": [
        "recepcion",
    ],
}

ROLES_VALIDOS = list(ROLE_PERMISSIONS.keys())

# =============================================================================
# HELPERS
# =============================================================================

def get_user_permissions() -> list:
    role = st.session_state.get("role", "Tienda")
    return ROLE_PERMISSIONS.get(role, [])


def can_access(module_key: str) -> bool:
    return module_key in get_user_permissions()


def navigate_to_module(module_key: str):
    if can_access(module_key):
        st.session_state.current_page = module_key
        st.rerun()
    else:
        st.error("⛔ No tienes permisos para acceder a este módulo")


def validar_permiso_tienda(guia_doc: dict) -> bool:
    """
    Valida que el usuario Tienda solo vea guías de su propia tienda.
    Admin y Bodega ven todo.
    """
    role = st.session_state.get("role")
    if role in ("Administrador", "Bodega"):
        return True

    tienda_usuario = st.session_state.get("assigned_store", "").strip()
    tienda_guia = str(guia_doc.get("tienda_destino", "")).strip()
    if not tienda_usuario:
        return False

    from utils.common import normalizar_texto
    return normalizar_texto(tienda_usuario) == normalizar_texto(tienda_guia)


def validar_permiso_tienda_stop(guia_doc: dict):
    """Valida permiso de tienda; si no pasa, detiene con st.stop()."""
    if not validar_permiso_tienda(guia_doc):
        st.error("⛔ No autorizado para visualizar esta guía")
        st.stop()


def get_user_store() -> str:
    return st.session_state.get("assigned_store", "")


def es_admin_o_bodega() -> bool:
    return st.session_state.get("role") in ("Administrador", "Bodega")


def es_admin() -> bool:
    return st.session_state.get("role") == "Administrador"


# =============================================================================
# SEED AUTOMÁTICO DE USUARIOS DE TIENDA
# =============================================================================
def get_tienda_users_from_stores() -> list[dict]:
    """
    Genera lista de usuarios Tienda basada en TIENDAS_DATA.
    Cada tienda → un usuario con:
    - username: nombre normalizado (ej: aeropostale_mall_del_rio)
    - password: "tienda123" (por defecto, cambiable luego)
    - role: "Tienda"
    - assigned_store: nombre exacto de la tienda
    - name: nombre comercial
    """
    users = []
    for tienda in TIENDAS_DATA:
        nombre_tienda = tienda.get("Nombre de Tienda", tienda.get("nombre", "")).strip()
        if not nombre_tienda:
            continue
        username = normalizar_username(nombre_tienda)
        users.append({
            "username": username,
            "password": hash_password("tienda123"),
            "role": "Tienda",
            "assigned_store": nombre_tienda,
            "name": nombre_tienda,
            "email": f"{username}@aeropostale.ec",
        })
    return users


def normalizar_username(nombre: str) -> str:
    """Convierte un nombre de tienda a username válido (ej: 'Mall del Río' → 'mall_del_rio')."""
    username = nombre.lower().replace(" ", "_").replace("-", "_")
    username = username.replace("á", "a").replace("é", "e").replace("í", "i")
    username = username.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    username = re.sub(r'[^a-z0-9_]', '', username) if 're' in dir() else username
    return username[:50]


def ensure_all_store_users():
    """
    Crea en la BD los usuarios de tienda que no existan.
    Llámese desde database/manager.py al iniciar.
    """
    from database.manager import local_db
    for user in get_tienda_users_from_stores():
        try:
            existe = local_db.find_one("users", {"username": user["username"]})
            if not existe:
                local_db.insert("users", user)
        except Exception:
            pass


import re
