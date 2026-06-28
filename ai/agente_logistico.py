# ai/agente_logistico.py
import json
import logging
from datetime import datetime
import google.generativeai as genai
from utils.secrets_helper import obtener_api_key_gemini

logger = logging.getLogger(__name__)

# =====================================================================
# BACKEND: FUNCIONES MATEMÁTICAS PURAS (NO IA)
# =====================================================================

# --- SPRINT 1 ---
def calcular_demanda_diaria(ventas_historicas_30dias: int) -> float:
    return ventas_historicas_30dias / 30.0

def calcular_wos(stock_actual: int, demanda_diaria: float) -> float:
    if demanda_diaria <= 0:
        return 999.0
    return stock_actual / (demanda_diaria * 7.0)

def calcular_rop(demanda_diaria: float, lead_time_dias: int, stock_seguridad_fijo: int = 10) -> float:
    return (demanda_diaria * lead_time_dias) + stock_seguridad_fijo

# --- SPRINT 2 ---
def calcular_dock_to_stock(fecha_ingreso_iso: str, fecha_disponible_iso: str) -> float:
    try:
        f_ingreso = datetime.fromisoformat(fecha_ingreso_iso)
        f_disponible = datetime.fromisoformat(fecha_disponible_iso)
        diff = f_disponible - f_ingreso
        return diff.total_seconds() / 3600.0  # horas
    except Exception:
        return 0.0

def calcular_tasa_devolucion(unidades_devueltas: int, despachadas: int) -> float:
    if despachadas == 0:
        return 0.0
    return (unidades_devueltas / float(despachadas)) * 100.0

# --- SPRINT 3 ---
def evaluar_desgaste_flota(odometro_actual: int, km_ultimo_mantenimiento: int, limite: int = 10000) -> int:
    return limite - (odometro_actual - km_ultimo_mantenimiento)

def calcular_otif(pedidos_entregados_ok: int, pedidos_totales_ruta: int) -> float:
    if pedidos_totales_ruta == 0:
        return 0.0
    return (pedidos_entregados_ok / float(pedidos_totales_ruta)) * 100.0


# =====================================================================
# TOOLS PARA EL LLM (ACCIONES SIMULADAS SAP/ERP)
# =====================================================================

def generar_alerta_sap(sku_id: str, cantidad_sugerida: int, motivo: str):
    """
    Invoca SAP para generar alerta de inventario.
    """
    return f"SAP_ALERT: Alerta generada para {sku_id}. Sugerido: {cantidad_sugerida}. Motivo: {motivo}"

def sugerir_markdown(sku_id: str, motivo: str):
    """
    Clasifica un SKU en SAP como Riesgo de Dead Stock.
    """
    return f"SAP_MARKDOWN: Liquidación sugerida para {sku_id}. Motivo: {motivo}"

def reporte_cuello_botella_rfid(lote_id: str, horas_transcurridas: float):
    """
    Genera reporte interno WMS por demoras Dock-to-Stock.
    """
    return f"WMS_REPORT: Cuello de botella en Recepción RFID. Lote: {lote_id}, Horas: {horas_transcurridas}"

def informar_problema_logistica_inversa(sucursal: str, categoria_falla: str, tasa_devolucion: float):
    """
    Cruza datos y alerta de fallas de fábrica o picking.
    """
    return f"ERP_REVERSE_LOG: Alerta en sucursal {sucursal}. Falla: {categoria_falla} (Tasa: {tasa_devolucion}%)"

def programar_mantenimiento_preventivo(id_vehiculo: str):
    """
    Envía comando a mantenimiento de flota.
    """
    return f"FLEET_MAINTENANCE: Mantenimiento programado para unidad {id_vehiculo}"

def solicitar_justificacion_ruta(id_vehiculo: str, otif: float):
    """
    Solicita justificación al equipo de transporte si OTIF cae.
    """
    return f"FLEET_OTIF_ALERT: Solicitud de justificación a {id_vehiculo}. OTIF bajo: {otif}%"

# Mapeo de herramientas para el orquestador
HERRAMIENTAS_LLM = [
    generar_alerta_sap,
    sugerir_markdown,
    reporte_cuello_botella_rfid,
    informar_problema_logistica_inversa,
    programar_mantenimiento_preventivo,
    solicitar_justificacion_ruta
]

# =====================================================================
# ORQUESTADOR (AGENT LOOP)
# =====================================================================

SYSTEM_PROMPT_MAESTRO = """Actúas como el Director Logístico de un CEDI Textil. Tu objetivo es mantener el flujo de Fast Fashion optimizado.
1. Consumes datos de los módulos de Abastecimiento, Operaciones y Flota a través del JSON procesado por backend.
2. NO calculas métricas por ti mismo; usas los valores calculados que se te proveen en el JSON.
3. Comparas los resultados con los OKRs establecidos.
4. Tu output debe ser siempre proactivo. No des solo datos estadísticos; emite comandos obligatoriamente llamando a tus tools pre-programadas.

Reglas por Módulo:
- SPRINT 1 (Abastecimiento): SI stock_actual <= rop, invoca generar_alerta_sap indicando 'Riesgo de Quiebre de Stock'. SI wos > 12, sugiere Markdown (sugerir_markdown) indicando 'Riesgo de Dead Stock'.
- SPRINT 2 (Operaciones): Analiza tiempo Dock-to-Stock. Si > 48h, invoca reporte_cuello_botella_rfid. Si la tasa_devolucion > 5%, cruza datos e invoca informar_problema_logistica_inversa.
- SPRINT 3 (Flotas): Si odometro remanente < 500 km, invoca programar_mantenimiento_preventivo. Si OTIF < 95%, invoca solicitar_justificacion_ruta.
"""

def procesar_datos_brutos(inputs_json: dict) -> dict:
    """Ejecuta los cálculos en backend y devuelve el JSON enriquecido."""
    resultados = {}
    
    # Sprint 1
    if "sprint1" in inputs_json:
        s1 = inputs_json["sprint1"]
        demanda = calcular_demanda_diaria(s1.get("ventas_historicas_30dias", 0))
        stock = s1.get("stock_actual", 0)
        lead = s1.get("lead_time_dias", 0)
        
        resultados["sprint1_calc"] = {
            "sku_id": s1.get("sku_id"),
            "stock_actual": stock,
            "demanda_diaria": round(demanda, 2),
            "wos": round(calcular_wos(stock, demanda), 2),
            "rop": round(calcular_rop(demanda, lead), 2)
        }
        
    # Sprint 2
    if "sprint2" in inputs_json:
        s2 = inputs_json["sprint2"]
        resultados["sprint2_calc"] = {
            "lote_id": s2.get("lote_id", "LOTE-DESC"),
            "dock_to_stock_horas": round(calcular_dock_to_stock(s2.get("fecha_ingreso_wms"), s2.get("fecha_disponible_venta")), 2),
            "sucursal": s2.get("sucursal", "N/A"),
            "categoria_falla": s2.get("categoria_falla", "N/A"),
            "tasa_devolucion": round(calcular_tasa_devolucion(s2.get("unidades_devueltas", 0), s2.get("unidades_despachadas", 0)), 2)
        }
        
    # Sprint 3
    if "sprint3" in inputs_json:
        s3 = inputs_json["sprint3"]
        resultados["sprint3_calc"] = {
            "id_vehiculo": s3.get("id_vehiculo", "V-00"),
            "odometro_remanente": evaluar_desgaste_flota(s3.get("odometro_actual", 0), s3.get("km_ultimo_mantenimiento", 0)),
            "otif_porcentaje": round(calcular_otif(s3.get("pedidos_entregados_ok", 0), s3.get("pedidos_totales_ruta", 0)), 2)
        }
        
    return resultados

def invocar_agente_logistico(inputs_json: dict) -> str:
    """
    Función principal que orquesta el Agent Loop.
    1. Calcula matemáticas en backend.
    2. Envía estado a Gemini.
    3. Gemini devuelve invocaciones de Tools.
    """
    datos_calculados = procesar_datos_brutos(inputs_json)
    estado_texto = json.dumps(datos_calculados, indent=2)
    
    api_key = obtener_api_key_gemini()
    if not api_key:
        return "Error: API Key de Gemini no configurada."
        
    genai.configure(api_key=api_key)
    
    modelo = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=HERRAMIENTAS_LLM,
        system_instruction=SYSTEM_PROMPT_MAESTRO
    )
    
    try:
        # Iniciar chat e invocar
        chat = modelo.start_chat(enable_automatic_function_calling=True)
        prompt_in = f"Evalúa los siguientes indicadores calculados y ejecuta las acciones necesarias usando tus tools pre-programadas:\n\n{estado_texto}"
        
        response = chat.send_message(prompt_in)
        
        # Recuperar historial para ver qué hizo la IA
        log_acciones = []
        for msg in chat.history:
            if msg.role == "model" and msg.parts:
                for part in msg.parts:
                    if part.function_call:
                        fc = part.function_call
                        args = {k: v for k, v in fc.args.items()}
                        log_acciones.append(f"🛠️ **{fc.name}** | Argumentos: {args}")
        
        respuesta_texto = response.text
        if log_acciones:
            respuesta_texto = "### Acciones de SAP/WMS Invocadas Automáticamente:\n" + "\n".join(log_acciones) + "\n\n### Análisis del Agente:\n" + respuesta_texto
            
        return respuesta_texto
        
    except Exception as e:
        logger.error("Error en Agente Logistico: %s", e)
        return f"Excepción durante Agent Loop: {str(e)}"
