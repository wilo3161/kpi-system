# automation/task_manager.py
"""
Gestión automática de tareas basadas en incidencias de recepción.
"""

import streamlit as st
from datetime import datetime, timedelta
from database.manager import local_db
from ai.supply_chain_ai import _ejecutar_prompt

TASK_COLLECTION = "tareas_automaticas"


def generar_tareas_desde_incidencias():
    """Busca guías con recepciones con novedad en los últimos 7 días y crea tareas."""
    desde = (datetime.now() - timedelta(days=7)).isoformat()

    # Intentar con find y luego filtrar manualmente para soportar el mock sin operadores complejos
    guias_con_novedad = []
    try:
        # MongoDB real
        guias_con_novedad = list(local_db.find("guias", {
            "recepcion.estado_recepcion": {"$in": ["CON_NOVEDAD", "PARCIAL"]},
            "recepcion.fecha_recepcion": {"$gte": desde}
        }))
    except Exception:
        # Fallback para mock: traer todas las guías del período y filtrar en Python
        guias = local_db.find("guias", {"recepcion.fecha_recepcion": {"$gte": desde}})
        guias_con_novedad = [
            g for g in guias
            if g.get("recepcion", {}).get("estado_recepcion") in ("CON_NOVEDAD", "PARCIAL")
        ]

    tareas_creadas = 0
    for guia in guias_con_novedad:
        numero_guia = guia.get("numero_guia")
        tienda = guia.get("tienda_destino")
        transferencia = guia.get("numero_transferencia")
        incidencias = guia.get("incidencias", [])

        # Evitar duplicados
        existente = local_db.find_one(TASK_COLLECTION, {
            "guia": numero_guia,
            "tipo": "recepcion_novedad"
        })
        if existente:
            continue

        descripcion = (
            f"Recepción con novedad en {tienda} (Transf. {transferencia}). "
            f"Incidencias: {len(incidencias)}"
        )
        tarea = {
            "tipo": "recepcion_novedad",
            "guia": numero_guia,
            "descripcion": descripcion,
            "estado": "pendiente",
            "fecha_creacion": datetime.now().isoformat(),
            "asignado_a": guia.get("usuario_genera", "admin"),  # el generador original
            "prioridad": "ALTA" if len(incidencias) > 2 else "MEDIA",
            "sugerencia_ia": None
        }
        local_db.insert(TASK_COLLECTION, tarea)
        tareas_creadas += 1

    return tareas_creadas


def generar_tarea_por_guia(numero_guia: str, motivo: str, prioridad: str = "MEDIA"):
    """Crea una tarea manual asociada a una guía, asignando al generador original."""
    guia = local_db.find_one("guias", {"numero_guia": str(numero_guia)})
    if not guia:
        return False

    tarea = {
        "tipo": "manual",
        "guia": str(numero_guia),
        "descripcion": motivo,
        "estado": "pendiente",
        "fecha_creacion": datetime.now().isoformat(),
        "asignado_a": guia.get("usuario_genera", st.session_state.get("user_name", "admin")),
        "prioridad": prioridad,
        "sugerencia_ia": None
    }
    local_db.insert(TASK_COLLECTION, tarea)
    return True


def obtener_tareas_pendientes():
    return local_db.find(
        TASK_COLLECTION,
        {"estado": "pendiente"},
        sort=[("prioridad", -1), ("fecha_creacion", -1)]
    )


def completar_tarea(tarea_id):
    local_db.update(
        TASK_COLLECTION,
        {"_id": tarea_id},
        {"estado": "completada", "fecha_completada": datetime.now().isoformat()}
    )


def generar_sugerencia_ia(tarea: dict) -> str:
    prompt = f"""
Eres un supervisor de logística de Aeropostale Ecuador. Ante la siguiente tarea pendiente:
"{tarea.get('descripcion')}"
Sugiere una acción concreta para resolverla (máx. 2 líneas).
"""
    sugerencia = _ejecutar_prompt(prompt, "Revisar manualmente.")
    local_db.update(
        TASK_COLLECTION,
        {"_id": tarea["_id"]},
        {"sugerencia_ia": sugerencia}
    )
    return sugerencia


def generar_recordatorio(tarea: dict) -> str:
    prompt = f"""
Redacta un mensaje de recordatorio profesional para {tarea.get('asignado_a')} sobre la tarea:
"{tarea.get('descripcion')}"
El tono debe ser cordial pero firme. Incluye la fecha actual ({datetime.now().strftime('%d/%m/%Y')}).
"""
    return _ejecutar_prompt(prompt, "Recordatorio no disponible.")
