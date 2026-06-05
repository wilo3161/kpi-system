# ai/supply_chain_ai.py
"""
Asistente de IA para Supply Chain con Gemini.
Centraliza toda la comunicación con la IA generativa.
"""

import streamlit as st
from datetime import datetime, timedelta
from database.manager import local_db
import json
import logging
import time

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False

# Modelos en orden de preferencia (el primero se intenta primero)
_MODELOS_PREFERENCIA = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]

# -----------------------------------------------------------------------------
# Singleton del modelo Gemini (Wilo IA)
# -----------------------------------------------------------------------------
_modelo_gemini = None
_modelo_nombre_activo = None

def _inicializar_modelo(model_name: str = None):
    """Configura Gemini y retorna el modelo listo para usar."""
    global _modelo_gemini, _modelo_nombre_activo

    if _modelo_gemini is not None and model_name is None:
        return _modelo_gemini

    if not _GEMINI_OK:
        return None

    from utils.secrets_helper import obtener_api_key_gemini
    api_key = obtener_api_key_gemini()

    if not api_key:
        logger.error("API Key de Gemini no configurada.")
        return None

    nombre = model_name or _MODELOS_PREFERENCIA[0]
    try:
        genai.configure(api_key=api_key)
        modelo = genai.GenerativeModel(
            model_name=nombre,
            system_instruction="Eres 'wilo IA', el asistente exclusivo de inteligencia artificial del ERP de Fashion Club Ecuador y Aeropostale. Nunca debes mencionar que eres de Google, Gemini o OpenAI, tu nombre es únicamente wilo IA."
        )
        _modelo_gemini = modelo
        _modelo_nombre_activo = nombre
        return _modelo_gemini
    except Exception as e:
        logger.error("Error configurando Gemini (%s): %s", nombre, e)
        return None

def _ejecutar_prompt(prompt: str, fallback: str = "⚠️ wilo IA no disponible.") -> str:
    """
    Ejecuta un prompt en Gemini con manejo de cuota (429) y retry automático.
    Prueba modelos en orden de preferencia si el actual falla por cuota.
    """
    global _modelo_gemini, _modelo_nombre_activo

    if not _GEMINI_OK:
        return fallback

    modelos_a_intentar = list(_MODELOS_PREFERENCIA)
    # Si ya hay un modelo activo, ponerlo primero
    if _modelo_nombre_activo and _modelo_nombre_activo in modelos_a_intentar:
        modelos_a_intentar.remove(_modelo_nombre_activo)
        modelos_a_intentar.insert(0, _modelo_nombre_activo)

    ultimo_error = None
    for nombre_modelo in modelos_a_intentar:
        modelo = _inicializar_modelo(nombre_modelo)
        if not modelo:
            continue

        # Intentar hasta 3 veces con backoff para errores 429
        for intento in range(3):
            try:
                response = modelo.generate_content(prompt)
                _modelo_nombre_activo = nombre_modelo  # guardar el que funcionó
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                ultimo_error = e
                if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                    if intento < 2:
                        wait = (intento + 1) * 3  # 3s, 6s
                        logger.warning("Cuota excedida en %s, reintentando en %ds...", nombre_modelo, wait)
                        time.sleep(wait)
                    else:
                        logger.warning("Cuota agotada en modelo %s, intentando siguiente...", nombre_modelo)
                        break  # probar siguiente modelo
                else:
                    logger.error("Error en wilo IA (%s): %s", nombre_modelo, e)
                    break  # error no relacionado con cuota, salir del retry

    # Si todos los modelos fallaron por cuota
    if ultimo_error and ("429" in str(ultimo_error) or "quota" in str(ultimo_error).lower()):
        return (
            "⚠️ **wilo IA alcanzó el límite de uso de la API por hoy.**\n\n"
            "El sistema tiene un límite diario de consultas de IA. "
            "Puedes:\n"
            "• Esperar unos minutos y volver a intentarlo\n"
            "• Copiar el texto de actividades manualmente\n"
            "• Intentarlo mañana cuando el cupo se renueve\n\n"
            f"_(Error técnico: {str(ultimo_error)[:120]})_"
        )
    return fallback if not ultimo_error else f"⚠️ Error IA: {str(ultimo_error)[:200]}"


def transcribir_audio(audio_bytes: bytes) -> str | None:
    """Para transcribir audio con Gemini 1.5 Flash se usa la API multimodal."""
    modelo = _inicializar_modelo()
    if not modelo:
        return "⚠️ Modelo no disponible para transcribir."
    try:
        response = modelo.generate_content([
            "Transcribe textualmente el siguiente audio en español:",
            {"mime_type": "audio/ogg", "data": audio_bytes}
        ])
        return response.text.strip()
    except Exception as e:
        logger.error("Error al transcribir con Gemini: %s", e)
        return None


# -----------------------------------------------------------------------------
# FUNCIONES PÚBLICAS (mantienen su comportamiento original)
# -----------------------------------------------------------------------------

def _obtener_contexto_operacional() -> dict:
    hoy = datetime.now()
    hace_30_dias = hoy - timedelta(days=30)

    guias_emitidas = local_db.count("guias", {"fecha": {"$gte": hace_30_dias.isoformat()}})
    recepciones = local_db.count("guias", {"recepcion.fecha_recepcion": {"$gte": hace_30_dias.isoformat()}})
    incidencias_totales = sum(
        len(g.get("incidencias", [])) for g in local_db.find("guias", {"incidencias.fecha": {"$gte": hace_30_dias.isoformat()}})
    )

    pipeline = [
        {"$unwind": "$incidencias"},
        {"$match": {"incidencias.fecha": {"$gte": hace_30_dias.isoformat()}}},
        {"$group": {"_id": "$tienda_destino", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    try:
        top_tiendas = list(local_db.db.guias.aggregate(pipeline))
    except Exception:
        top_tiendas = []

    return {
        "periodo": "últimos 30 días",
        "guias_emitidas": guias_emitidas,
        "recepciones_realizadas": recepciones,
        "incidencias_totales": incidencias_totales,
        "top_tiendas_incidencias": top_tiendas
    }


def generar_resumen_diario() -> str:
    hoy = datetime.now().strftime("%Y-%m-%d")
    total_emitidas = local_db.count("guias", {"fecha": {"$regex": f"^{hoy}"}})
    recepciones_hoy = local_db.count("guias", {"recepcion.fecha_recepcion": {"$regex": f"^{hoy}"}})
    incidencias_hoy = local_db.find("guias", {"incidencias.fecha": {"$regex": f"^{hoy}"}})
    total_inc = sum(len(g.get("incidencias", [])) for g in incidencias_hoy)

    prompt = f"""Eres 'wilo IA', asistente de supply chain de Aeropostale Ecuador. Genera un resumen ejecutivo breve (máx 5 líneas) para el día {hoy}.
Datos: Guías emitidas: {total_emitidas}, Recepciones: {recepciones_hoy}, Incidencias: {total_inc}.
Tono profesional, recomienda acciones si hay muchas incidencias."""
    return _ejecutar_prompt(prompt, "⚠️ No se pudo generar el resumen.")


def analizar_anomalias() -> str:
    pipeline = [
        {"$unwind": "$incidencias"},
        {"$group": {"_id": "$tienda_destino", "incidencias": {"$sum": 1}, "guias": {"$addToSet": "$numero_guia"}}},
        {"$project": {"tasa": {"$divide": ["$incidencias", {"$size": "$guias"}]}, "tienda": "$_id"}},
        {"$match": {"tasa": {"$gt": 0.3}}},
        {"$sort": {"tasa": -1}},
        {"$limit": 5}
    ]
    try:
        anomalias = list(local_db.db.guias.aggregate(pipeline))
    except Exception:
        return "⚠️ No se pudo completar el análisis."

    if not anomalias:
        return "✅ No se detectan anomalías significativas."

    tiendas = ", ".join([f"{a['tienda']} ({(a['tasa']*100):.0f}%)" for a in anomalias])
    prompt = f"Tiendas con alta tasa de incidencias: {tiendas}. Redacta una alerta ejecutiva para gerencia."
    return _ejecutar_prompt(prompt, "⚠️ No se pudo completar el análisis.")


def analizar_tendencia_incidencias() -> str:
    hoy = datetime.now()
    semana_actual = hoy - timedelta(days=7)
    semana_anterior = hoy - timedelta(days=14)

    inc_actual = sum(len(g.get("incidencias", [])) for g in local_db.find("guias", {"incidencias.fecha": {"$gte": semana_actual.isoformat()}}))
    inc_anterior = sum(len(g.get("incidencias", [])) for g in local_db.find("guias", {"incidencias.fecha": {"$gte": semana_anterior.isoformat(), "$lt": semana_actual.isoformat()}}))

    if inc_anterior == 0:
        return "No hay datos de la semana anterior para comparar."

    cambio = ((inc_actual - inc_anterior) / inc_anterior) * 100
    contexto = _obtener_contexto_operacional()
    prompt = f"""Analiza la tendencia de incidencias:
- Incidencias hace 7 días: {inc_anterior}
- Incidencias esta semana: {inc_actual}
- Cambio: {cambio:.1f}%
Contexto adicional: {json.dumps(contexto, default=str)}
Redacta un breve análisis (2-3 líneas) y recomienda acciones si el cambio es significativo."""
    return _ejecutar_prompt(prompt, "No se pudo analizar la tendencia.")


def recomendar_accion_correctiva(evento: str, datos: dict) -> str:
    prompt = f"""Eres un experto en supply chain. Ante el siguiente evento: '{evento}' con los datos {json.dumps(datos, default=str)},
recomienda una acción correctiva concreta y profesional (máx 3 líneas)."""
    return _ejecutar_prompt(prompt, "Revisar manualmente el evento.")


def generar_borrador_correo(asunto: str, contexto: dict, destinatario: str = "Gerencia") -> str:
    prompt = f"""Redacta un correo profesional para {destinatario} con asunto: "{asunto}".
Contexto: {json.dumps(contexto, default=str)}.
Incluye saludo, cuerpo conciso (máx 150 palabras) y firma de Wilson Pérez, Jefe de Logística Aeropostale Ecuador."""
    return _ejecutar_prompt(prompt, "No se pudo generar el borrador.")


def consulta_interactiva(pregunta: str) -> str:
    contexto = _obtener_contexto_operacional()
    prompt = f"""Eres 'wilo IA', asistente de supply chain de Aeropostale Ecuador. Con base en los siguientes datos actuales:
{json.dumps(contexto, default=str)}
Responde la siguiente pregunta de manera concisa: {pregunta}"""
    return _ejecutar_prompt(prompt, "No se pudo procesar la consulta.")


def predecir_riesgo_recepcion(guia_doc: dict) -> str:
    tienda = guia_doc.get("tienda_destino", "")
    total_prendas = guia_doc.get("total_prendas", 0)
    peso = guia_doc.get("peso", 0)
    transferencia = guia_doc.get("numero_transferencia", "")

    pipeline = [
        {"$match": {"tienda_destino": tienda}},
        {"$group": {
            "_id": None,
            "total_guias": {"$sum": 1},
            "guias_con_incidencias": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$size": {"$ifNull": ["$incidencias", []]}}, 0]},
                        1,
                        0
                    ]
                }
            }
        }}
    ]
    try:
        result = list(local_db.db.guias.aggregate(pipeline))
        if result and result[0]["total_guias"] > 0:
            tasa = (result[0]["guias_con_incidencias"] / result[0]["total_guias"]) * 100
        else:
            tasa = 0
    except Exception:
        tasa = 0

    prompt = f"""Eres un analista de riesgos logísticos. Evalúa el riesgo de incidencias en la siguiente recepción:
- Tienda: {tienda}
- Transferencia: {transferencia}
- Total prendas: {total_prendas}
- Peso: {peso} kg
- Tasa histórica de incidencias de la tienda: {tasa:.1f}%
Responde con una frase que indique el nivel de riesgo (BAJO/MEDIO/ALTO) y una justificación breve. Si la tasa es alta (>30%), sugiere medidas preventivas."""
    return _ejecutar_prompt(prompt, "Riesgo no evaluable.")


def evaluar_proveedor(transferencia: str) -> str:
    guias = local_db.find("guias", {"numero_transferencia": transferencia, "recepcion.estado_recepcion": {"$exists": True}})
    total = len(guias)
    if total == 0:
        return "No hay historial de recepciones para esta transferencia."

    incidencias = sum(1 for g in guias if g.get("recepcion", {}).get("estado_recepcion") != "CONFORME")
    tasa_inc = (incidencias / total) * 100

    prompt = f"""Evalúa el proveedor asociado a la transferencia {transferencia}:
- Recepciones totales: {total}
- Recepciones con incidencias: {incidencias} ({tasa_inc:.1f}%)
Con base en esto, emite una evaluación breve (1-2 líneas) y una recomendación."""
    return _ejecutar_prompt(prompt, "No se pudo evaluar el proveedor.")


def generar_reporte_semanal() -> str:
    hoy = datetime.now()
    inicio = hoy - timedelta(days=7)
    guias = local_db.count("guias", {"fecha": {"$gte": inicio.isoformat()}})
    recepciones = local_db.count("guias", {"recepcion.fecha_recepcion": {"$gte": inicio.isoformat()}})
    incidencias = sum(len(g.get("incidencias", [])) for g in local_db.find("guias", {"incidencias.fecha": {"$gte": inicio.isoformat()}}))

    contexto = _obtener_contexto_operacional()
    prompt = f"""Genera un reporte ejecutivo semanal (últimos 7 días) para Aeropostale Ecuador.
Datos: Guías emitidas: {guias}, Recepciones: {recepciones}, Incidencias: {incidencias}.
Contexto adicional: {json.dumps(contexto, default=str)}
El reporte debe incluir: resumen, puntos críticos, recomendaciones. Tono profesional."""
    return _ejecutar_prompt(prompt, "No se pudo generar el reporte.")
