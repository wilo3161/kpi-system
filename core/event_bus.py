# core/event_bus.py
"""
Bus de eventos central del ERP Aeropostale.
Cualquier módulo puede emitir un evento, y aquí se procesan las reacciones
automáticas (tareas, notificaciones, invalidación de cachés).
"""

from datetime import datetime
from database.manager import local_db
import logging

logger = logging.getLogger(__name__)


def emitir(evento: str, payload: dict, metadata: dict = None) -> None:
    """
    Emite un evento al bus y lo persiste en MongoDB.

    Parámetros
    ----------
    evento : str
        Nombre identificador del evento (ej. "GUIA_CREADA", "RECEPCION_CONFIRMADA").
    payload : dict
        Datos relevantes al evento (número de guía, tienda, incidencias, etc.).
    metadata : dict, opcional
        Información adicional de contexto.
    """
    doc = {
        "evento": evento,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
        "metadata": metadata or {},
    }
    # Persistir el evento (si falla, no detenemos la ejecución principal)
    try:
        local_db.insert("eventos", doc)
    except Exception as e:
        logger.warning("No se pudo guardar el evento '%s' en MongoDB: %s", evento, e)

    # Procesar reacciones automáticas
    _procesar_evento(doc)


def _procesar_evento(evento_doc: dict) -> None:
    """
    Reacciona ante un evento disparando las acciones automáticas correspondientes.
    """
    e = evento_doc["evento"]
    payload = evento_doc.get("payload", {})

    if e == "RECEPCION_CONFIRMADA":
        # Actualizar último registro de recepción (usado por algunos módulos)
        try:
            local_db.update(
                "kpi_cache",
                {"clave": "ultima_recepcion"},
                {"$set": {"valor": payload.get("guia")}},
                upsert=True,
            )
        except Exception as ex:
            logger.warning("Error actualizando kpi_cache en RECEPCION_CONFIRMADA: %s", ex)

        # Si hay incidencias, generar tarea automática
        incidencias = payload.get("incidencias", 0)
        if incidencias > 0:
            try:
                from automation.task_manager import generar_tarea_por_guia
                generar_tarea_por_guia(
                    payload["guia"],
                    f"Recepción con novedad: {incidencias} incidencia(s) en {payload.get('tienda')}",
                    prioridad="ALTA" if incidencias > 2 else "MEDIA",
                )
            except ImportError:
                logger.warning("automation.task_manager no está disponible para generar tarea")
            except Exception as ex:
                logger.error("Error al generar tarea desde evento RECEPCION_CONFIRMADA: %s", ex)

        # Invalidar caché del motor de KPIs para reflejar cambios al instante
        try:
            from core.kpi_engine import KPIEngine
            kpi = KPIEngine()
            kpi.invalidate_cache()
        except ImportError:
            logger.warning("core.kpi_engine no está disponible para invalidar caché")
        except Exception as ex:
            logger.error("Error al invalidar caché de KPIs: %s", ex)

    elif e == "GUIA_CREADA":
        # Aquí se podrían añadir en el futuro notificaciones, actualizaciones de dashboards, etc.
        # Por ahora mantenemos el punto de extensión.
        pass

    # Se pueden añadir más casos según las necesidades futuras.
