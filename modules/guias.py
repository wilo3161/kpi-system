# modules/guias.py
# ============================================================================
# SISTEMA OPERATIVO LOGÍSTICO — GUÍAS DE REMISIÓN
# VERSIÓN ROBUSTECIDA: transacciones, validaciones, logging, cache, eliminación de botones redundantes
# ============================================================================

from __future__ import annotations

import io
import re
import json
import base64
import logging
import requests
import qrcode
import pandas as pd
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Optional, Any
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER

import streamlit as st
import streamlit.components.v1 as components

from utils.ui import add_back_button, show_module_header
from config.stores_data import TIENDAS_DATA
from services.notifications import TelegramBot
from database.manager import local_db
from ai.supply_chain_ai import _ejecutar_prompt
from utils.backgrounds import set_module_background

logger = logging.getLogger(__name__)
TZ_QUITO = ZoneInfo("America/Guayaquil")

def extraer_url_transferencia(url_str):
    """Extrae el link de transferencia de un parámetro query de URL si existe."""
    if not url_str:
        return url_str
    if not isinstance(url_str, str) or not url_str.startswith(("http://", "https://")):
        return url_str
    try:
        import urllib.parse as urlparse
        parsed_url = urlparse.urlparse(url_str)
        query_params = urlparse.parse_qs(parsed_url.query)
        for param_name, param_values in query_params.items():
            for val in param_values:
                if val.startswith(("http://", "https://")):
                    return val
    except Exception:
        pass
    return url_str

DIRECCION_REMITENTE = "Av. Santo Thomas y antigua via a Cotacachi"
CIUDAD_REMITENTE    = "San Roque"
TELEFONO_REMITENTE  = "0993052744"

MARCAS = {
    "Fashion Club": {
        "remitente_empresa": "FASHION CLUB - Centro de Distribución",
        "logo_filename": "Fashion.jpg",
    },
    "Tempo": {
        "remitente_empresa": "TEMPO - Centro de Distribución",
        "logo_filename": "Tempo.jpg",
    },
    "Aeropostale": {
        "remitente_empresa": "AEROPOSTALE - Centro de Distribución",
        "logo_filename": "Aeropostale.jpg",
    },
    "Price Club": {
        "remitente_empresa": "PRICE CLUB - Centro de Distribución",
        "logo_filename": "PriceClub.jpg",
    },
}

# ============================================================================
# MÁQUINA DE ESTADOS (sin cambios)
# ============================================================================
class EstadoGuia:
    BORRADOR            = "BORRADOR"
    VALIDADA            = "VALIDADA"
    EMITIDA             = "EMITIDA"
    EN_MANIFIESTO       = "EN_MANIFIESTO"
    DESPACHADA          = "DESPACHADA"
    EN_TRANSITO         = "EN_TRANSITO"
    RECEPCION_INICIADA  = "RECEPCION_INICIADA"
    RECEPCION_PARCIAL   = "RECEPCION_PARCIAL"
    RECIBIDA_CONFORME   = "RECIBIDA_CONFORME"
    RECIBIDA_NOVEDAD    = "RECIBIDA_CON_NOVEDAD"
    CONCILIADA          = "CONCILIADA"
    CERRADA             = "CERRADA"
    ANULADA             = "ANULADA"

TRANSICIONES_VALIDAS: dict[str, list[str]] = {
    EstadoGuia.BORRADOR:           [EstadoGuia.VALIDADA, EstadoGuia.ANULADA],
    EstadoGuia.VALIDADA:           [EstadoGuia.EMITIDA, EstadoGuia.ANULADA],
    EstadoGuia.EMITIDA:            [EstadoGuia.EN_MANIFIESTO, EstadoGuia.ANULADA],
    EstadoGuia.EN_MANIFIESTO:      [EstadoGuia.DESPACHADA, EstadoGuia.ANULADA],
    EstadoGuia.DESPACHADA:         [EstadoGuia.EN_TRANSITO],
    EstadoGuia.EN_TRANSITO:        [EstadoGuia.RECEPCION_INICIADA],
    EstadoGuia.RECEPCION_INICIADA: [EstadoGuia.RECEPCION_PARCIAL,
                                    EstadoGuia.RECIBIDA_CONFORME,
                                    EstadoGuia.RECIBIDA_NOVEDAD],
    EstadoGuia.RECEPCION_PARCIAL:  [EstadoGuia.RECIBIDA_CONFORME,
                                    EstadoGuia.RECIBIDA_NOVEDAD,
                                    EstadoGuia.CONCILIADA],
    EstadoGuia.RECIBIDA_CONFORME:  [EstadoGuia.CONCILIADA, EstadoGuia.CERRADA],
    EstadoGuia.RECIBIDA_NOVEDAD:   [EstadoGuia.CONCILIADA],
    EstadoGuia.CONCILIADA:         [EstadoGuia.CERRADA],
    EstadoGuia.CERRADA:            [],
    EstadoGuia.ANULADA:            [],
}

def transicion_valida(estado_actual: str, estado_nuevo: str) -> bool:
    return estado_nuevo in TRANSICIONES_VALIDAS.get(estado_actual, [])

def _guia_blindada(guia_doc: dict) -> bool:
    estados_blindaje = [
        EstadoGuia.EN_TRANSITO, EstadoGuia.RECEPCION_INICIADA,
        EstadoGuia.RECEPCION_PARCIAL, EstadoGuia.RECIBIDA_CONFORME,
        EstadoGuia.RECIBIDA_NOVEDAD, EstadoGuia.CONCILIADA, EstadoGuia.CERRADA
    ]
    return guia_doc.get("estado") in estados_blindaje

# ============================================================================
# NOTIFICACIONES INTERNAS
# ============================================================================
def _enviar_mensaje_interno(destinatario_username: str, asunto: str, contenido: str, remitente: str = "Sistema"):
    doc = {
        "para": destinatario_username,
        "asunto": asunto,
        "contenido": contenido,
        "remitente": remitente,
        "fecha": datetime.now(TZ_QUITO).isoformat(),
        "leido": False
    }
    try:
        local_db.insert("mensajes_internos", doc)
        st.toast(f"📬 Nuevo mensaje para {destinatario_username}: {asunto}", icon="💬")
    except Exception as e:
        logger.error(f"Error guardando mensaje interno: {e}")

def _mostrar_notificaciones_usuario(usuario_actual: str):
    mensajes = local_db.find("mensajes_internos", {"para": usuario_actual, "leido": False}, sort=[("fecha", -1)])
    if mensajes:
        with st.expander(f"📬 Notificaciones ({len(mensajes)} nuevas)"):
            for msg in mensajes:
                st.markdown(f"**📨 {msg['asunto']}**  \n{msg['contenido']}  \n*{msg['remitente']} - {msg['fecha'][:16]}*")
                local_db.update("mensajes_internos", {"_id": msg["_id"]}, {"leido": True})
    else:
        st.info("No tienes notificaciones nuevas.")

# ============================================================================
# PARSER DE TRANSFERENCIA (con validaciones mejoradas)
# ============================================================================
def _limpiar_codigo(codigo_str: str) -> str:
    return codigo_str.split('.')[0].strip()

def _es_producto_valido(codigo: str, descripcion: str) -> bool:
    if not codigo or not any(c.isdigit() for c in codigo):
        return False
    no_producto = ["PROVEEDOR", "TOTAL", "SUBTOTAL", "SUMA", "GENERAL"]
    desc_upper = descripcion.upper().strip()
    for palabra in no_producto:
        if desc_upper.startswith(palabra) or palabra in desc_upper:
            return False
    return True

@st.cache_data(ttl=300, show_spinner=False)
def extraer_items_desde_html(html_text: str) -> tuple[list[dict], int]:
    """Extrae items desde el HTML de la transferencia, con cache de 5 minutos."""
    soup = BeautifulSoup(html_text, 'html.parser')
    tabla = soup.find('table')
    if not tabla:
        tablas = soup.find_all('table')
        if tablas:
            tabla = tablas[0]
        else:
            return [], 0
    items = []
    total = 0
    filas = tabla.find_all('tr')[1:]
    for fila in filas:
        celdas = fila.find_all('td')
        if len(celdas) < 12:
            continue
        try:
            codigo_raw = celdas[2].get_text(strip=True)
            descripcion = celdas[3].get_text(strip=True)
            estilo = celdas[8].get_text(strip=True) if len(celdas) > 8 else ""
            cantidad_str = celdas[11].get_text(strip=True).replace(',', '.')
            cantidad = int(float(cantidad_str))
        except (ValueError, IndexError):
            continue
        codigo = _limpiar_codigo(codigo_raw)
        if not _es_producto_valido(codigo, descripcion):
            continue
        total += cantidad
        # Extraer talla y color de otras celdas si existen, o inferirlas de la descripción
        talla = celdas[6].get_text(strip=True) if len(celdas) > 6 else ""
        color = celdas[7].get_text(strip=True) if len(celdas) > 7 else ""
        
        # Si están vacías, intentar extraer de la descripción (ej: "CAMISETA ROJO S")
        if not talla and not color:
            partes = descripcion.split()
            if len(partes) >= 2:
                talla = partes[-1]
                color = partes[-2]
                
        items.append({
            "codigo": codigo,
            "estilo": estilo,
            "descripcion": descripcion,
            "talla": talla,
            "color": color,
            "cantidad_esperada": cantidad,
        })
    return items, total

@st.cache_data(ttl=300, show_spinner=False)
def extraer_datos_transferencia(url: str) -> dict:
    datos = {"numero_transferencia": "", "total_prendas": 0, "items": []}
    try:
        url = extraer_url_transferencia(url)
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Error al obtener URL: {url} - status {response.status_code}")
            return datos
        soup = BeautifulSoup(response.text, "html.parser")
        texto = soup.get_text()
        patrones = [
            r"N\.-\s*TRANSFERENCIAS?\s*0*(\d+)",
            r"TRANSFERENCIA\s*N?[°º]?\s*0*(\d+)",
            r"N[°º]\s*\.?\s*(\d+)",
            r"#\s*(\d+)",
        ]
        for patron in patrones:
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                datos["numero_transferencia"] = m.group(1)
                break
        if not datos["numero_transferencia"]:
            numeros = re.findall(r'\b\d{5,}\b', texto)
            if numeros:
                datos["numero_transferencia"] = numeros[0]
        items, total_calculado = extraer_items_desde_html(response.text)
        datos["items"] = items
        if total_calculado > 0:
            datos["total_prendas"] = total_calculado
        else:
            t = re.search(r"Total\s*[:\-\s]*([\d,.]+)", texto, re.IGNORECASE)
            if t:
                try:
                    datos["total_prendas"] = int(float(t.group(1).replace(",", "")))
                except ValueError:
                    pass
    except Exception as exc:
        logger.warning("No se pudo extraer datos de la URL: %s", exc)
    return datos

# ============================================================================
# MODELO DE DOCUMENTO Y CONSTRUCCIÓN
# ============================================================================
def _build_evento(evento: str, descripcion: str, usuario: str, modulo: str = "guias",
                  metadata: Optional[dict] = None, cambios: Optional[dict] = None) -> dict:
    import hashlib
    import json
    ts = datetime.now(TZ_QUITO).isoformat()
    ev_dict = {
        "evento": evento, "descripcion": descripcion, "usuario": usuario,
        "timestamp": ts, "modulo": modulo,
        "metadata": metadata or {}, "cambios_realizados": cambios or {},
    }
    data_str = json.dumps(ev_dict, sort_keys=True)
    ev_dict["firma_sha256"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    return ev_dict

def construir_documento_guia(
    numero_guia: int,
    marca: str,
    tienda_info: dict,
    tienda_nombre: str,
    destinatario: str,
    direccion: str,
    telefono: str,
    ciudad: str,
    peso: float,
    bultos: int,
    observaciones: str,
    numero_transferencia: str,
    total_prendas: int,
    url_transferencia: str,
    usuario: str,
    qr_url: str,
    items_expected: list = None,
) -> dict:
    ahora = datetime.now(TZ_QUITO)
    num_str = str(numero_guia)
    evento_inicial = _build_evento("GUIA_CREADA", f"Guía #{num_str} creada.", usuario, metadata={"numero_transferencia": numero_transferencia})
    return {
        "numero_guia": num_str, "numero": num_str, "tipo_documento": "GUIA_REMISION",
        "estado": EstadoGuia.EN_MANIFIESTO, "estado_operacional": "ACTIVA", "anulada": False,
        "header": {
            "fecha_emision": ahora.strftime("%d/%m/%Y %H:%M:%S"), "fecha_emision_iso": ahora.isoformat(),
            "fecha_despacho": None, "usuario_genera": usuario, "marca": marca,
            "remitente_empresa": MARCAS[marca]["remitente_empresa"], "remitente_direccion": DIRECCION_REMITENTE,
            "remitente_ciudad": CIUDAD_REMITENTE, "remitente_telefono": TELEFONO_REMITENTE,
            "origen": "BODEGA CENTRAL", "destino": ciudad, "numero_transferencia": numero_transferencia,
            "url_transferencia": url_transferencia, "prioridad": "NORMAL",
        },
        "marca": marca, "tienda_destino": tienda_nombre, "fecha_emision": ahora.strftime("%d/%m/%Y %H:%M:%S"),
        "fecha": ahora.isoformat(), "usuario_genera": usuario, "numero_transferencia": numero_transferencia,
        "total_prendas": total_prendas, "url_transferencia": url_transferencia, "peso": peso, "bultos": bultos,
        "observaciones": observaciones,
        "destinatario": {"nombre": destinatario, "direccion": direccion, "telefono": telefono, "ciudad": ciudad},
        "destinatario_nombre": destinatario, "direccion_destinatario": direccion,
        "telefono_destinatario": telefono, "ciudad": ciudad,
        "resumen_logistico": {"total_prendas": total_prendas, "total_items": 0, "peso": peso, "bultos": bultos, "volumen": None},
        "items_expected": items_expected or [],
        "recepcion": {"estado_recepcion": None, "fecha_recepcion": None, "usuario_recepcion": None,
                      "observaciones": None, "diferencias_detectadas": False, "items_received": [], "evidencias": []},
        "incidencias": [], "timeline": [evento_inicial],
        "ai_analysis": {"resumen_operacional": None, "riesgo_detectado": None, "acciones_sugeridas": [],
                        "correo_sugerido": None, "prioridad_operativa": "NORMAL"},
        "qr_payload": qr_url,
        "audit": {"created_at": ahora.isoformat(), "updated_at": ahora.isoformat(),
                  "created_by": usuario, "updated_by": usuario},
    }

# ============================================================================
# HELPERS DE SEGURIDAD Y TRANSICIONES
# ============================================================================
def _cambiar_estado(numero_guia: str, estado_nuevo: str, usuario: str,
                    descripcion: str = "", metadata: Optional[dict] = None) -> bool:
    doc = local_db.find_one("guias", {"numero_guia": str(numero_guia)})
    if not doc:
        logger.error(f"Guía {numero_guia} no encontrada para cambio de estado")
        return False
    if _guia_blindada(doc) and estado_nuevo not in [EstadoGuia.CERRADA, EstadoGuia.ANULADA]:
        logger.warning(f"Intento de modificar guía blindada {numero_guia} -> {estado_nuevo}")
        return False
    estado_actual = doc.get("estado", "")
    if not transicion_valida(estado_actual, estado_nuevo):
        logger.warning("Transición inválida %s → %s", estado_actual, estado_nuevo)
        return False
    ahora = datetime.now(TZ_QUITO).isoformat()
    evento = _build_evento(f"ESTADO_{estado_nuevo}", descripcion or f"Cambio: {estado_actual} → {estado_nuevo}",
                           usuario, metadata=metadata, cambios={"estado_anterior": estado_actual, "estado_nuevo": estado_nuevo})
    local_db.update("guias", {"numero_guia": str(numero_guia)},
                    {"$set": {"estado": estado_nuevo, "audit.updated_at": ahora, "audit.updated_by": usuario},
                     "$push": {"timeline": evento}})
    return True

def cargar_logo_local(marca: str) -> Optional[bytes]:
    logo_filename = MARCAS[marca]["logo_filename"]
    logo_path = Path("images") / logo_filename
    try:
        with open(logo_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"No se pudo cargar logo para {marca}: {e}")
        return None

def obtener_proximo_numero_guia() -> int:
    return local_db.obtener_siguiente_numero("numero_guia", 1)

def _eliminar_guia_permanente(numero_guia: str, usuario: str) -> bool:
    guia = local_db.find_one("guias", {"numero_guia": str(numero_guia)})
    if not guia:
        return False
    if _guia_blindada(guia):
        st.error("No se puede eliminar una guía blindada.")
        return False
    creador = guia.get("usuario_genera", "")
    if usuario != creador and st.session_state.get("role") != "Administrador":
        st.error("No tienes permiso.")
        return False
    # Quitar del manifiesto activo
    manifiesto = local_db.find_one("manifiesto", {"activo": True})
    if manifiesto and str(numero_guia) in [str(g) for g in manifiesto.get("guias", [])]:
        local_db.update("manifiesto", {"_id": manifiesto["_id"]},
                        {"$pull": {"guias": str(numero_guia)},
                         "$inc": {"metricas.total_prendas": -guia.get("total_prendas", 0),
                                  "metricas.total_bultos": -guia.get("bultos", 0)}})
    local_db.delete("guias", {"numero_guia": str(numero_guia)})
    return True

# ============================================================================
# AI ASSISTANT (solo análisis interno)
# ============================================================================
def _analizar_guia_con_ia(guia_data: dict) -> dict:
    fallback = {"resumen_operacional": None, "riesgo_detectado": "BAJO",
                "acciones_sugeridas": ["Confirmar recepción en tienda destino."],
                "correo_sugerido": None, "prioridad_operativa": "NORMAL"}
    prompt = f"""
Eres analista de logística de Aeropostale Ecuador. Analiza esta guía de remisión y responde SOLO en JSON válido.

Datos de la guía:
- Número: {guia_data.get('numero_guia')}
- Tienda destino: {guia_data.get('tienda_destino')}
- Transferencia: {guia_data.get('numero_transferencia')}
- Total prendas: {guia_data.get('total_prendas', 0)}
- Bultos: {guia_data.get('bultos', 1)}
- Peso: {guia_data.get('peso', 0)} kg
- Observaciones: {guia_data.get('observaciones', 'Ninguna')}
- Marca: {guia_data.get('marca')}

Responde con este JSON exacto:
{{
  "resumen_operacional": "resumen breve de 1 oración",
  "riesgo_detectado": "BAJO|MEDIO|ALTO",
  "acciones_sugeridas": ["acción1", "acción2"],
  "correo_sugerido": "asunto sugerido para correo de notificación",
  "prioridad_operativa": "NORMAL|ALTA|CRITICA"
}}
"""
    respuesta = _ejecutar_prompt(prompt, json.dumps(fallback))
    try:
        return json.loads(respuesta)
    except Exception:
        return fallback

# ============================================================================
# GENERACIÓN DE PDF PROFESIONAL
# ============================================================================
def _dibujar_etiqueta_en_canvas(c, guia_data: dict, label_width, label_height):
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    import io
    
    # Paleta de colores modernos
    color_fondo = HexColor("#0033A0") # Azul Corporativo
    color_texto = HexColor("#FFFFFF")
    color_gris = HexColor("#F1F5F9")
    color_oscuro = HexColor("#1E293B")
    color_borde = HexColor("#CBD5E1")
    
    tienda = str(guia_data.get("tienda_destino", "Destino")).upper()
    marca = str(guia_data.get("marca", ""))
    num_guia = str(guia_data.get("numero_guia", ""))
    num_trans = str(guia_data.get("numero_transferencia", "N/A"))
    tot_prendas = guia_data.get("total_prendas", 0)
    
    # 1. ENCABEZADO REDONDEADO (Top)
    c.setFillColor(color_fondo)
    c.roundRect(5*mm, label_height - 30*mm, label_width - 10*mm, 25*mm, 4*mm, stroke=0, fill=1)
    
    # Título del encabezado
    c.setFillColor(color_texto)
    c.setFont("Helvetica-Bold", 12) # Font un poco más pequeño para nombres largos
    # Acortar texto largo hasta 35 caracteres para que no se corte
    c.drawCentredString(label_width / 2.0, label_height - 13*mm, tienda[:35])
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(label_width / 2.0, label_height - 18*mm, f"Guía: {num_guia} | Trans: {num_trans}")
    
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(label_width / 2.0, label_height - 24*mm, f"{marca.upper()}")

    # 2. BLOQUE DE RESUMEN (Medio)
    y_medio = label_height - 55*mm
    c.setFillColor(color_gris)
    c.setStrokeColor(color_borde)
    c.setLineWidth(1)
    c.roundRect(5*mm, y_medio, label_width - 10*mm, 20*mm, 2*mm, stroke=1, fill=1)
    
    c.setFillColor(color_oscuro)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(label_width / 2.0, y_medio + 7*mm, f"{tot_prendas:,}")
    c.setFont("Helvetica", 8)
    c.drawCentredString(label_width / 2.0, y_medio + 2*mm, "TOTAL PRENDAS")

    # 3. CÓDIGO QR EN EL CENTRO
    qr_bytes = guia_data.get("qr_bytes")
    if qr_bytes:
        from reportlab.lib.utils import ImageReader
        try:
            import logging
            img = ImageReader(io.BytesIO(qr_bytes))
            qr_size = 40*mm
            c.drawImage(img, (label_width - qr_size)/2.0, y_medio - 45*mm, width=qr_size, height=qr_size)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(label_width / 2.0, y_medio - 49*mm, "ESCANEAR PARA RECEPCIÓN")
        except Exception as e:
            logging.error(f"Error drawing QR: {e}")

    # 4. DATOS ADICIONALES Y FIRMA (Abajo)
    y_footer = 12*mm
    dest = guia_data.get("destinatario", {})
    if isinstance(dest, str):
        dest_nombre = dest
        dest_dir = guia_data.get("direccion_destinatario", "")
        dest_tel = guia_data.get("telefono_destinatario", "")
    else:
        dest_nombre = dest.get("nombre", "")
        dest_dir = dest.get("direccion", "")
        dest_tel = dest.get("telefono", "")
        
    c.setFillColor(color_oscuro)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y_footer + 17*mm, f"Contacto:")
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y_footer + 17*mm, f"{dest_nombre[:35]}")
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y_footer + 13*mm, f"Telf:")
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y_footer + 13*mm, f"{dest_tel}")
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y_footer + 9*mm, f"Dir:")
    c.setFont("Helvetica", 7)
    c.drawString(20*mm, y_footer + 9*mm, f"{dest_dir[:55]}")
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5*mm, y_footer + 5*mm, f"Envío:")
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y_footer + 5*mm, f"{guia_data.get('bultos', 1)} bultos | {guia_data.get('peso', 0)} kg")
    
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(label_width / 2.0, 8*mm, "Documento Digital / Etiqueta Térmica 4x6\"")
    c.drawCentredString(label_width / 2.0, 5*mm, f"Generado por: {guia_data.get('usuario_genera', 'Sistema')}")

def generar_pdf_profesional(guia_data: dict) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    import io
    buffer = io.BytesIO()
    
    # Tamaño térmico 4x6" (100x150 mm)
    label_width, label_height = 100*mm, 150*mm
    c = canvas.Canvas(buffer, pagesize=(label_width, label_height))
    
    _dibujar_etiqueta_en_canvas(c, guia_data, label_width, label_height)
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def generar_pdf_a4_agrupado(guias_list: list) -> bytes:
    """Genera un PDF A4 con hasta 4 etiquetas (2x2 grid)."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    import io
    buffer = io.BytesIO()
    
    c = canvas.Canvas(buffer, pagesize=A4)
    a4_width, a4_height = A4
    
    # Tamaño de cada etiqueta en el A4 (ligeramente ajustado para dejar márgenes)
    # A4 = 210 x 297 mm
    # 2 etiquetas a lo ancho = 200mm. Dejamos 5mm margen izq/der.
    # 2 etiquetas a lo alto = 300mm (apretado). Hacemos un poco de padding.
    label_width, label_height = 98*mm, 142*mm 
    
    # Posiciones relativas (x, y) de la esquina inferior izquierda de cada etiqueta
    # El orden será: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    # Recordemos que (0,0) en ReportLab es la esquina INFERIOR IZQUIERDA del papel.
    
    margen_x = 5 * mm
    margen_y = 5 * mm
    
    posiciones = [
        (margen_x, a4_height - margen_y - label_height),                    # 0: Superior Izquierda
        (a4_width - margen_x - label_width, a4_height - margen_y - label_height), # 1: Superior Derecha
        (margen_x, a4_height - margen_y - 2*label_height - 2*mm),           # 2: Inferior Izquierda
        (a4_width - margen_x - label_width, a4_height - margen_y - 2*label_height - 2*mm) # 3: Inferior Derecha
    ]
    
    for idx, guia_data in enumerate(guias_list[:4]): # Max 4
        x, y = posiciones[idx]
        c.saveState()
        c.translate(x, y)
        
        # Opcional: Dibujar borde alrededor de cada etiqueta para ayudar a cortar
        from reportlab.lib.colors import HexColor
        c.setStrokeColor(HexColor("#CBD5E1"))
        c.setLineWidth(0.5)
        c.rect(0, 0, label_width, label_height)
        
        _dibujar_etiqueta_en_canvas(c, guia_data, label_width, label_height)
        
        c.restoreState()
        
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================================
# UI HELPERS
# ============================================================================
def _badge_estado(estado: str) -> str:
    colores = {EstadoGuia.EN_MANIFIESTO: "#3B82F6", EstadoGuia.DESPACHADA: "#8B5CF6",
               EstadoGuia.RECIBIDA_CONFORME: "#10B981", EstadoGuia.RECIBIDA_NOVEDAD: "#F59E0B",
               EstadoGuia.ANULADA: "#EF4444", EstadoGuia.CERRADA: "#6B7280"}
    color = colores.get(estado, "#64748B")
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.75rem;font-weight:600;">{estado}</span>'

def _render_timeline(timeline: list) -> None:
    if not timeline:
        st.info("Sin eventos registrados.")
        return
    for ev in reversed(timeline):
        ts = ev.get("timestamp", "")[:16].replace("T", " ")
        usr = ev.get("usuario", "sistema")
        evt = ev.get("evento", "")
        desc = ev.get("descripcion", "")
        st.markdown(f'<div style="border-left:3px solid #3B82F6;padding:4px 12px;margin:4px 0;">'
                    f'<small style="color:#94A3B8">{ts} — <b>{usr}</b></small><br/>'
                    f'<span style="font-weight:600">{evt}</span> — {desc}</div>', unsafe_allow_html=True)

# ============================================================================
# FUNCION BACKEND GUIA
# ============================================================================
def generar_guia_backend(tienda_sel, destinatario, direccion, telefono, ciudad, peso_kg, bultos, observaciones, numero_transferencia, total_prendas, url_transferencia, usuario_activo, items_extraidos, logo_bytes, marca_sel, tienda_info):
    import io
    import qrcode
    
    nuevo_numero = obtener_proximo_numero_guia()
    base_url = st.secrets.get("app", {}).get("url", "https://tu-app.streamlit.app")
    
    if url_transferencia:
        qr_url = url_transferencia
    else:
        qr_url = f"{base_url}?modulo=recepcion&transferencia={numero_transferencia}&guia={nuevo_numero}"
        
    qr = qrcode.QRCode(box_size=5, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0033A0", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_bytes = qr_buf.getvalue()
    
    doc_guia = construir_documento_guia(
        nuevo_numero, marca_sel, tienda_info, tienda_sel,
        destinatario, direccion, telefono, ciudad, float(peso_kg),
        int(bultos), observaciones, str(numero_transferencia),
        int(total_prendas), url_transferencia, usuario_activo,
        qr_url, items_extraidos
    )
    doc_guia["logo_bytes"] = logo_bytes
    doc_guia["qr_bytes"] = qr_bytes
    
    try:
        local_db.insert("guias", doc_guia)
        if "manifiesto_obj" in st.session_state:
            local_db.update("manifiesto", {"_id": st.session_state.manifiesto_obj["_id"]},
                            {"$push": {"guias": str(nuevo_numero)},
                             "$inc": {"metricas.total_prendas": int(total_prendas),
                                      "metricas.total_bultos": int(bultos)}})
    except Exception as exc:
        return False, f"Error BD: {exc}", None, None
        
    try:
        from core.event_bus import emitir
        emitir("GUIA_CREADA", {"guia": str(nuevo_numero), "tienda": tienda_sel,
                               "transferencia": numero_transferencia, "prendas": total_prendas,
                               "peso": peso_kg, "bultos": bultos})
    except: pass
    
    try:
        import threading
        bot = TelegramBot()
        msg_text = f"🚚 *NUEVA GUÍA EMITIDA*\\n📄 Guía: `{nuevo_numero}`\\n🏪 Tienda: {tienda_sel}\\n🔄 Transferencia: {numero_transferencia}\\n📦 Prendas: {total_prendas:,}\\n👤 Usuario: {usuario_activo}"
        threading.Thread(target=bot.enviar_mensaje, args=(msg_text,)).start()
    except: pass
    
    pdf_bytes = generar_pdf_profesional(doc_guia)
    return True, str(nuevo_numero), pdf_bytes, doc_guia

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def show_generar_guias():
    try:
        _show_generar_guias_impl()
    except Exception as e:
        raise e

def _show_generar_guias_impl():
    show_module_header("🚚 Guías de Remisión", "Sistema logístico con trazabilidad completa")
    set_module_background("guias")
    
    from utils.ui import inject_acumatica_css
    inject_acumatica_css()

    if "cola_impresion" not in st.session_state:
        st.session_state.cola_impresion = []

    # Mostrar notificaciones internas
    usuario_actual = st.session_state.get("username", "")
    if usuario_actual:
        _mostrar_notificaciones_usuario(usuario_actual)

    if "manifiesto_obj" not in st.session_state:
        manifiesto = local_db.find_one("manifiesto", {"activo": True})
        if not manifiesto:
            local_db.insert("manifiesto", {"activo": True, "guias": [],
                           "fecha_creacion": datetime.now(TZ_QUITO).isoformat(),
                           "metricas": {"total_bultos": 0, "total_prendas": 0}})
            manifiesto = local_db.find_one("manifiesto", {"activo": True})
        st.session_state.manifiesto_obj = manifiesto

    usuario_activo = st.session_state.get("user_name", "Usuario")
    rol_activo = st.session_state.get("role", "")

    tab_dash, tab_nueva, tab_man, tab_det = st.tabs(["📊 Dashboard", "📄 Nueva Guía", "📋 Manifiesto", "🔍 Detalle & Timeline"])

    # =========================================================================
    # TAB 1 — NUEVA GUÍA
    # =========================================================================
    with tab_nueva:
        sub_tab_ind, sub_tab_batch, sub_tab_laar = st.tabs(["📄 Individual", "🚀 Masiva (Batch)", "📦 Generar Excel Laar"])
        
        with sub_tab_laar:
            st.markdown("### 📦 Generador de Plantilla Excel Laar Courier")
            st.info("Este asistente se conecta a JirehWEB para extraer transferencias pendientes y estructurar el Excel de carga masiva de Laar Courier sin duplicados.")
            
            # Form configuration fields
            laar_col1, laar_col2 = st.columns(2)
            with laar_col1:
                fecha_ini_laar = st.date_input("Fecha Inicio Consulta:", datetime.now(TZ_QUITO), key="laar_fecha_ini")
                piezas_laar = st.number_input("Número de piezas por guía:", min_value=1, value=1, step=1, key="laar_piezas")
                contenido_laar = st.selectbox("Contenido de la guía:", ["MERCADERIA", "PUBLICIDAD", "MUEBLES", "MUESTRAS"], index=0, key="laar_contenido")
            with laar_col2:
                fecha_fin_laar = st.date_input("Fecha Fin Consulta:", datetime.now(TZ_QUITO), key="laar_fecha_fin")
                peso_laar = st.number_input("Peso por guía (kg):", min_value=0.1, value=1.0, step=0.1, key="laar_peso")
                tamanio_laar = st.selectbox("Tamaño del paquete:", ["MEDIANO", "PEQUEÑO", "GRANDE"], index=0, key="laar_tamanio")
                
            modo_bot_laar = st.radio("Modo de ejecución (Navegador):", ["Silencioso (Headless)", "Visual (Headful)"], key="laar_modo_bot")
            
            if st.button("🚀 Extraer y Descargar Excel Laar", type="primary", use_container_width=True):
                import subprocess
                import sys
                from pathlib import Path
                
                laar_script = Path("automation/guias_laar.py")
                if laar_script.exists():
                    st.info("Iniciando la extracción desde JirehWEB... Por favor espera.")
                    
                    cmd_laar = [
                        sys.executable, str(laar_script),
                        "--fecha-inicio", fecha_ini_laar.strftime("%Y-%m-%d"),
                        "--fecha-fin", fecha_fin_laar.strftime("%Y-%m-%d"),
                        "--piezas", str(int(piezas_laar)),
                        "--peso", f"{peso_laar:.1f}",
                        "--contenido", contenido_laar,
                        "--tamanio", tamanio_laar
                    ]
                    if modo_bot_laar == "Visual (Headful)":
                        cmd_laar.append("--headful")
                        
                    with st.spinner("🤖 El asistente está extrayendo y procesando transferencias..."):
                        try:
                            res_laar = subprocess.run(cmd_laar, capture_output=True, text=True, encoding="utf-8")
                            if res_laar.stdout:
                                st.text_area("Bitácora del proceso", res_laar.stdout, height=180)
                            
                            excel_path = Path("automation/guiaslaar_generadas.xlsx")
                            if excel_path.exists():
                                excel_data = excel_path.read_bytes()
                                st.success("✅ ¡Plantilla de Laar generada con éxito!")
                                st.download_button(
                                    label="📥 Descargar guiaslaar.xlsx",
                                    data=excel_data,
                                    file_name=f"guiaslaar_{fecha_ini_laar.strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True
                                )
                                # Eliminar archivo local temporal una vez cargado en memoria
                                try:
                                    os.remove(excel_path)
                                except:
                                    pass
                            else:
                                if "ya procesado" in res_laar.stdout or "No se extrajeron" in res_laar.stdout:
                                    st.warning("⚠️ No se encontraron nuevas transferencias pendientes en ese rango de fechas (o ya fueron procesadas anteriormente).")
                                else:
                                    st.error("⚠️ El proceso terminó pero no se generó el archivo Excel.")
                                    if res_laar.stderr:
                                        st.text_area("Detalles del Error", res_laar.stderr, height=100)
                        except Exception as e:
                            st.error(f"Error al ejecutar el script de Laar: {e}")
                else:
                    st.error("No se encontró el script `automation/guias_laar.py`.")
            st.divider()
        
        with sub_tab_batch:
            st.markdown("### 🚀 Generación Masiva de Guías")
            
            # --- INTEGRACIÓN DEL BOT AUTOMÁTICO ---
            with st.expander("🤖 Asistente de Automatización (JirehWEB)", expanded=True):
                st.info("Utiliza el bot para conectarse automáticamente a JirehWEB, extraer las transferencias pendientes de MATRIZ y generar las guías en lote sin copiar y pegar.")
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    modo_bot = st.radio("Modo de ejecución:", ["Visual (Headful)", "Silencioso (Headless)"])
                with c2:
                    st.write("")
                    st.write("")
                    if st.button("🤖 Extraer y Generar Automáticamente", type="primary", use_container_width=True):
                        import subprocess
                        import sys
                        from pathlib import Path
                        
                        script_path = Path("automation/orchestrator.py")
                        if script_path.exists():
                            st.info("Iniciando el bot... Por favor no cierres esta ventana.")
                            cmd = [sys.executable, str(script_path)]
                            if modo_bot == "Visual (Headful)":
                                cmd.append("--headful")
                                
                            with st.spinner("🤖 El bot está trabajando. Esto puede tomar un momento..."):
                                try:
                                    # Corremos el orquestador
                                    result = subprocess.run(cmd, capture_output=True, text=True)
                                    st.text_area("Log del Bot", result.stdout, height=300)
                                    if result.returncode == 0:
                                        st.success("✅ Proceso automatizado finalizado correctamente.")
                                    else:
                                        st.error(f"⚠️ El bot terminó con errores (Código {result.returncode})")
                                        st.text_area("Errores", result.stderr, height=150)
                                except Exception as e:
                                    st.error(f"Error al lanzar el bot: {e}")
                        else:
                            st.error("No se encontró el script de automatización.")

            st.divider()
            
            st.markdown("#### Ingreso Manual (Alternativo)")
            st.info("""
            **💡 Instrucciones para el modo manual:**
            1. **Prepara tus datos:** Necesitas dos datos clave por cada guía: el nombre exacto de la **Tienda Destino** y la **URL Transferencia**.
            2. **Usa la plantilla:** Puedes descargar el archivo de ejemplo abajo, llenarlo en Excel, y luego **copiar y pegar** las filas directamente en la tabla de esta pantalla.
            3. **Genera:** Una vez que la tabla tenga tus datos, haz clic en **'Generar Guías en Lote'**.
            """)
            
            buf_template = io.BytesIO()
            with pd.ExcelWriter(buf_template, engine="openpyxl") as w:
                pd.DataFrame({"Tienda Destino": ["Mall del Rio", "Scala Shopping"], "URL Transferencia": ["https://...", "https://..."]}).to_excel(w, index=False, sheet_name="Plantilla")
            st.download_button(
                "📥 Descargar Plantilla Excel", 
                buf_template.getvalue(), 
                "Plantilla_Guias_Batch.xlsx", 
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            if "batch_df" not in st.session_state:
                st.session_state.batch_df = pd.DataFrame({"Tienda Destino": [""], "URL Transferencia": [""]})
            
            edited_df = st.data_editor(st.session_state.batch_df, num_rows="dynamic", use_container_width=True)
            
            if st.button("🚀 Generar Guías en Lote", type="primary"):
                import zipfile
                valid_rows = edited_df[(edited_df["Tienda Destino"] != "") & (edited_df["URL Transferencia"] != "")]
                if valid_rows.empty:
                    st.warning("No hay filas válidas para procesar.")
                else:
                    zip_buffer = io.BytesIO()
                    exitosas = 0
                    fallidas = 0
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        progress = st.progress(0)
                        status_text = st.empty()
                        
                        for i, row in valid_rows.iterrows():
                            tienda_destino = str(row["Tienda Destino"]).strip()
                            url_t = str(row["URL Transferencia"]).strip()
                            status_text.text(f"Procesando: {tienda_destino}...")
                            
                            datos = extraer_datos_transferencia(url_t)
                            if not datos.get("numero_transferencia"):
                                fallidas += 1
                                continue
                                
                            marca_sel_batch = "Aeropostale"
                            logo_bytes_b = cargar_logo_local(marca_sel_batch)
                            tienda_info_b = next((t for t in TIENDAS_REGULARES + PRICE_CLUBS + VENTAS_POR_MAYOR if t == tienda_destino), TIENDAS_DATA.get("Tienda A"))
                            if isinstance(tienda_info_b, str):
                                tienda_info_b = TIENDAS_DATA.get(tienda_info_b, TIENDAS_DATA["Tienda A"])
                                
                            success, num_guia, pdf_bytes_b, doc_guia_b = generar_guia_backend(
                                tienda_sel=tienda_destino,
                                destinatario=tienda_info_b.get("encargado", "ND"),
                                direccion=tienda_info_b.get("direccion", "ND"),
                                telefono=tienda_info_b.get("telefono", "ND"),
                                ciudad=tienda_info_b.get("ciudad", "ND"),
                                peso_kg=0.0,
                                bultos=1,
                                observaciones="Generado en Batch",
                                numero_transferencia=datos["numero_transferencia"],
                                total_prendas=datos.get("total_prendas", 0),
                                url_transferencia=url_t,
                                usuario_activo=usuario_activo,
                                items_extraidos=datos.get("items", []),
                                logo_bytes=logo_bytes_b,
                                marca_sel=marca_sel_batch,
                                tienda_info=tienda_info_b
                            )
                            
                            if success:
                                exitosas += 1
                                zip_file.writestr(f"Guia_{num_guia}_{tienda_destino}.pdf", pdf_bytes_b)
                            else:
                                fallidas += 1
                                
                            progress.progress((i + 1) / len(valid_rows))
                            
                    status_text.empty()
                    progress.empty()
                    
                    if exitosas > 0:
                        st.success(f"✅ Se generaron {exitosas} guías. (❌ Fallidas: {fallidas})")
                        st.download_button("📥 Descargar ZIP con Guías", zip_buffer.getvalue(), "Guias_Batch.zip", "application/zip", type="primary", use_container_width=True)
                    else:
                        st.error("No se pudo generar ninguna guía. Verifica las URLs.")

        with sub_tab_ind:
            if st.session_state.get("cola_impresion"):
                col_info, col_clear = st.columns([3, 1])
                col_info.info(f"Tienes {len(st.session_state.cola_impresion)} etiquetas acumuladas listas para imprimir en A4.")
                if col_clear.button("🧹 Limpiar cola", key="btn_clear_cola"):
                    st.session_state.cola_impresion = []
                    st.rerun()
                    

            with st.container(border=True):
                st.markdown("""
                <div style="text-align:center; margin-bottom: 20px; border-bottom: 2px solid #CBD5E1; padding-bottom:15px;">
                    <h3 style="margin:0; font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; font-size: 2.2rem;">FORMULARIO DE NUEVA GUÍA</h3>
                    <p style="margin:0; font-size: 0.95rem;">Completa los datos para emitir la guía de remisión.</p>
                </div>
                """, unsafe_allow_html=True)
            
                col_m, col_t = st.columns(2)
                with col_m:
                    # Solo Tempo y Fashion Club como Empresas remitentes
                    marca_sel = st.selectbox("Empresa (Remitente)", ["Tempo", "Fashion Club"])
                logo_bytes = cargar_logo_local(marca_sel)
            
                if not TIENDAS_DATA:
                    from config.stores_data import reload_stores_data
                    reload_stores_data()
            
                tiendas_opciones = [t["Nombre de Tienda"] for t in TIENDAS_DATA]
                
                tienda_sel = st.selectbox("Tienda Destino", tiendas_opciones)
                tienda_info = next((t for t in TIENDAS_DATA if t["Nombre de Tienda"] == tienda_sel), {})
                dest_nombre = tienda_info.get("Contacto", "")
                dest_dir = tienda_info.get("Dirección", "")
                dest_tel = tienda_info.get("Teléfono", "")
                dest_ciudad = tienda_info.get("Destino", "")
                c1, c2 = st.columns(2)
                with c1:
                    destinatario = st.text_input("Contacto destinatario", value=dest_nombre)
                    telefono = st.text_input("Teléfono", value=dest_tel)
                with c2:
                    direccion = st.text_area("Dirección", value=dest_dir, height=100)
                    ciudad = st.text_input("Ciudad", value=dest_ciudad)
                c3, c4 = st.columns(2)
                with c3:
                    peso_kg = st.number_input("Peso (kg)", min_value=0.0, step=0.5, format="%.1f")
                with c4:
                    bultos = st.number_input("Bultos", min_value=1, step=1, value=1)
            
                st.markdown("<hr style='border-color: #CBD5E1;'>", unsafe_allow_html=True)
                st.markdown("<h4 style='color: #1E293B; margin-bottom:10px;'>Datos de Transferencia</h4>", unsafe_allow_html=True)
            
                # Intentar obtener la URL de transferencia desde los parámetros del navegador
                query_transferencia = st.query_params.get("transferencia", "")
                if not query_transferencia:
                    query_transferencia = st.query_params.get("url", "")
                
                url_transferencia_input = st.text_input("URL de transferencia", value=query_transferencia, placeholder="https://...")
                url_transferencia = extraer_url_transferencia(url_transferencia_input)
            
                if url_transferencia != url_transferencia_input:
                    st.info(f"🔗 URL de transferencia extraída: {url_transferencia}")
                
                numero_transferencia = ""
                total_prendas = 0
                items_extraidos = []
                if url_transferencia:
                    if not url_transferencia.startswith(("http://", "https://")):
                        url_transferencia = "https://" + url_transferencia
                    with st.spinner("Extrayendo datos..."):
                        datos = extraer_datos_transferencia(url_transferencia)
                    numero_transferencia = datos.get("numero_transferencia", "")
                    total_prendas = datos.get("total_prendas", 0)
                    items_extraidos = datos.get("items", [])
                    if not items_extraidos:
                        st.warning("⚠️ No se pudo extraer el detalle de productos. Puedes continuar manual.")
                    if numero_transferencia:
                        st.success(f"Transferencia: **{numero_transferencia}**")
                    else:
                        st.warning("No se pudo extraer el número de transferencia. Puedes ingresarlo manualmente.")
                    if total_prendas:
                        st.info(f"Total prendas extraídas: **{total_prendas:,}**")
                    else:
                        total_prendas = 0
                else:
                    total_prendas = 0
                    items_extraidos = []
            
                c5, c6 = st.columns(2)
                with c5:
                    total_prendas_manual = st.number_input("Total prendas (manual)", min_value=0, step=1, value=total_prendas)
                    if total_prendas_manual:
                        total_prendas = total_prendas_manual
                with c6:
                    if not numero_transferencia:
                        numero_transferencia = st.text_input("N° de transferencia (manual)", value=numero_transferencia)
            
                observaciones = st.text_area("Observaciones")
                st.info("El número secuencial de guía se asignará automáticamente al presionar Guardar.")

                if st.button("💾 Guardar y Generar PDF", type="primary", use_container_width=True):
                    if not destinatario or not direccion:
                        st.error("Completa destinatario y dirección.")
                    else:
                        success, nuevo_numero, pdf_bytes, doc_guia = generar_guia_backend(
                            tienda_sel, destinatario, direccion, telefono, ciudad, peso_kg, bultos, observaciones,
                            numero_transferencia, total_prendas, url_transferencia, usuario_activo, items_extraidos,
                            logo_bytes, marca_sel, tienda_info
                        )
                    
                        if success:
                            st.success(f"✅ Guía #{nuevo_numero} guardada.")
                            
                            st.session_state.cola_impresion.append(doc_guia)
                            st.image(doc_guia["qr_bytes"], width=150, caption="QR de recepción")
                        
                            # Store current PDF in session to render the download buttons
                            st.session_state.last_guia = nuevo_numero
                            st.session_state.last_pdf = pdf_bytes
                            st.session_state.last_qr = doc_guia.get("qr_payload", doc_guia.get("url_transferencia", ""))
                            st.session_state.last_transferencia = numero_transferencia
                            st.session_state.last_prendas = total_prendas
                            st.session_state.last_telefono = telefono
                            
                            # Notificación interna a la tienda destino
                            tienda_usuario = local_db.find_one("users", {"assigned_store": tienda_sel, "role": "Tienda"})
                            if tienda_usuario:
                                username_tienda = tienda_usuario.get("username")
                                mensaje_contenido = f"**Nueva guía de envío**\nN° Guía: {nuevo_numero}\nTransferencia: {numero_transferencia}\nTotal prendas: {total_prendas}\nPeso: {peso_kg} kg\nBultos: {bultos}\n\nPuedes ver el detalle en tu bandeja de recepción."
                                _enviar_mensaje_interno(username_tienda, f"Guía de remisión #{nuevo_numero}", mensaje_contenido, remitente=usuario_activo)
                            else:
                                logger.warning(f"No se encontró usuario para la tienda {tienda_sel}")
            
                            ai = doc_guia.get("ai_analysis", {})
                            if ai and ai.get("resumen_operacional"):
                                with st.expander("🤖 Análisis IA", expanded=True):
                                    st.info(ai["resumen_operacional"])
                                    st.markdown(f"**Riesgo:** {ai.get('riesgo_detectado', 'N/A')}")
                                    if ai.get("acciones_sugeridas"):
                                        st.markdown("**Acciones sugeridas:**")
                                        for a in ai["acciones_sugeridas"]:
                                            st.markdown(f"- {a}")
                        else:
                            st.error(nuevo_numero) # Here nuevo_numero is the error string
            
                # Show download buttons if there's a last generated guide
                if st.session_state.get("last_guia") and st.session_state.get("last_pdf"):
                    _guia_num = st.session_state.last_guia
                    _pdf_bytes = st.session_state.last_pdf
                    _qr_url = st.session_state.get("last_qr", "")
                    _num_trans = st.session_state.get("last_transferencia", "")
                    _tot_prendas = st.session_state.get("last_prendas", 0)
                    _telefono = st.session_state.get("last_telefono", "")

                    cola = st.session_state.cola_impresion
                    n_cola = len(cola)

                    # Indicador de progreso de la cola
                    st.info(f"🖨️ Cola de impresión: **{n_cola}/4** guías acumuladas. {'¡Lista para imprimir!' if n_cola >= 4 else f'Faltan {4 - n_cola} guía(s) para imprimir automáticamente.'}")

                    c_btn1, c_btn2, c_btn3 = st.columns(3)

                    with c_btn1:
                        if n_cola >= 4:
                            # Auto-imprimir las 4 guías
                            pdf_a4 = generar_pdf_a4_agrupado(cola[:4])
                            st.download_button(
                                "🖨️ IMPRIMIR 4 ETIQUETAS (A4)",
                                pdf_a4,
                                "etiquetas_agrupadas.pdf",
                                "application/pdf",
                                use_container_width=True,
                                type="primary",
                                key="btn_imprimir_4",
                                on_click=lambda: st.session_state.update({"cola_impresion": st.session_state.cola_impresion[4:]})
                            )
                            st.caption("✅ Al descargar, el contador se resetea a 0.")
                        else:
                            if cola:
                                pdf_a4 = generar_pdf_a4_agrupado(cola)
                                def _limpiar_cola():
                                    st.session_state.cola_impresion = []
                                st.download_button(
                                    f"🖨️ Imprimir acumuladas ({n_cola}) (A4)",
                                    pdf_a4,
                                    "etiquetas_agrupadas.pdf",
                                    "application/pdf",
                                    use_container_width=True,
                                    on_click=_limpiar_cola
                                )
                            else:
                                st.button("🖨️ Sin guías acumuladas", disabled=True, use_container_width=True)

                    with c_btn2:
                        st.download_button(
                            "📄 Descargar solo esta (Térmica)",
                            _pdf_bytes,
                            f"guia_{_guia_num}.pdf",
                            "application/pdf",
                            use_container_width=True
                        )

                    with c_btn3:
                        import urllib.parse
                        import re as _re
                        mensaje_wa = (
                            f"🚚 *NUEVA GUÍA EMITIDA*\n"
                            f"📄 Guía: {_guia_num}\n"
                            f"🔄 Transferencia: {_num_trans}\n"
                            f"📦 Prendas: {_tot_prendas:,}\n\n"
                            f"🔗 *URL Transferencia:*\n{_qr_url}"
                        )
                        tel_wa = ""
                        if _telefono and _telefono != "ND":
                            tel_limpio = _re.sub(r'\D', '', _telefono)
                            if tel_limpio.startswith('0'):
                                tel_wa = "593" + tel_limpio[1:]
                            else:
                                tel_wa = tel_limpio
                                
                        url_wa = f"https://wa.me/{tel_wa}?text={urllib.parse.quote(mensaje_wa)}"
                        st.markdown(f'<a href="{url_wa}" target="_blank" style="display:inline-block; width:100%; text-align:center; background-color:#25D366; color:white; padding:8px 0; border-radius:4px; text-decoration:none; font-weight:bold;">📲 Enviar por WhatsApp</a>', unsafe_allow_html=True)

    # =========================================================================
    # TAB 2 — MANIFIESTO (sin cambios)
    # =========================================================================
    with tab_man:
        st.subheader("📋 Manifiesto de Envíos")
        manifiesto = local_db.find_one("manifiesto", {"activo": True})
        if manifiesto:
            met = manifiesto.get("metricas", {})
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Prendas", f"{met.get('total_prendas', 0):,}")
            mc2.metric("Total Bultos", met.get("total_bultos", 0))
            mc3.metric("Guías en manifiesto", len(manifiesto.get("guias", [])))
            guias_ids = manifiesto.get("guias", [])
            if guias_ids:
                in_list = []
                for g in guias_ids:
                    in_list.append(str(g))
                    if str(g).isdigit():
                        in_list.append(int(g))
                guias_man = local_db.find("guias", {"numero_guia": {"$in": in_list}, "anulada": False})
                if guias_man:
                    # Eliminar duplicados si los hay (priorizar los que tienen recepción)
                    guias_unicas = {}
                    for d in guias_man:
                        num = str(d.get("numero_guia"))
                        if num not in guias_unicas or "recepcion" in d:
                            guias_unicas[num] = d
                    guias_man = list(guias_unicas.values())
                    
                    for d in guias_man:
                        d["observaciones_recepcion"] = d.get("recepcion", {}).get("observaciones", "")
                    cols_show = ["numero_guia", "numero_transferencia", "tienda_destino", "fecha_emision", "estado", "bultos", "total_prendas", "usuario_genera", "observaciones_recepcion"]
                    cols_avail = [c for c in cols_show if any(c in d for d in guias_man)]
                    df_man = pd.DataFrame(guias_man)[cols_avail]
                    df_man = df_man.rename(columns={"observaciones_recepcion": "observaciones de la recepcion"})
                    st.dataframe(df_man, use_container_width=True)
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as w:
                        df_man.to_excel(w, index=False, sheet_name="Manifiesto")
                    st.download_button("📥 Exportar Manifiesto Excel", buf.getvalue(), "manifiesto.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    pendientes = [d for d in guias_man if d.get("estado") not in
                                  (EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.CERRADA, EstadoGuia.CONCILIADA)]
                    if pendientes:
                        st.warning(f"⚠️ {len(pendientes)} guía(s) pendientes de recepción.")
                else:
                    st.info("El manifiesto está vacío.")
            else:
                st.info("Aún no hay guías en el manifiesto.")
        if rol_activo == "Administrador":
            st.divider()
            with st.expander("⚙️ Administración del Manifiesto"):
                if st.button("🧹 Limpiar Manifiesto", type="secondary"):
                    local_db.update("manifiesto", {"activo": True},
                                    {"$set": {"guias": [], "metricas": {"total_bultos": 0, "total_prendas": 0}}})
                    st.success("Manifiesto limpiado.")
                    st.rerun()

    # =========================================================================
    # TAB 3 — DASHBOARD SEMANAL Y DE GUÍAS
    # =========================================================================
    with tab_dash:
        st.subheader("📈 Dashboard Progresivo (Prendas Transferidas Hoy)")

        ahora_ec = datetime.now(TZ_QUITO)
        hora_ec = ahora_ec.hour
        today_str = ahora_ec.strftime("%d/%m/%Y")
        
        HORA_CIERRE = 19  # 7pm Ecuador
        
        if hora_ec >= HORA_CIERRE:
            # Jornada cerrada — mostrar el resumen final del día
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, rgba(30,41,59,0.9), rgba(15,23,42,1)); border: 2px solid #f59e0b; border-radius: 15px; padding: 25px; text-align: center; margin-bottom: 20px;">
                <div style="font-size: 3rem;">🌙</div>
                <h2 style="color: #f59e0b; margin: 8px 0;">Jornada Cerrada — {today_str}</h2>
                <p style="color: #94a3b8; margin: 0;">El dashboard se reiniciará automáticamente mañana al comenzar las operaciones.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar el resumen final de la jornada de hoy
            todas_las_guias = local_db.find("guias", sort=[("fecha", -1)], limit=1000)
            guias_hoy = [d for d in todas_las_guias if d.get("fecha_emision", "").startswith(today_str) and not d.get("anulada")]
            prendas_por_usuario = {}
            for d in guias_hoy:
                usr = d.get("usuario_genera", "Desconocido")
                prendas_por_usuario[usr] = prendas_por_usuario.get(usr, 0) + d.get("total_prendas", 0)
            
            if prendas_por_usuario:
                st.markdown("#### 📋 Cierre final del día:")
                usuarios_ordenados = sorted(prendas_por_usuario.items(), key=lambda x: x[1], reverse=True)
                cols_per_row = 3
                for i in range(0, len(usuarios_ordenados), cols_per_row):
                    row_users = usuarios_ordenados[i:i+cols_per_row]
                    cols = st.columns(cols_per_row)
                    for j, (usr, total_p) in enumerate(row_users):
                        with cols[j]:
                            st.markdown(f"""
                            <div style="background: linear-gradient(145deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9)); border: 1px solid #f59e0b; border-radius: 15px; padding: 25px 15px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.2);">
                                <div style="font-size: 2.5rem; margin-bottom: 5px;">🏆</div>
                                <h2 style="margin: 0; color: #f8fafc; font-size: 1.3rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{usr}</h2>
                                <h1 style="margin: 10px 0; color: #f59e0b; font-size: 3rem; font-weight: 800;">{total_p:,}</h1>
                                <p style="margin: 0; color: #94a3b8; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Total Final del Día</p>
                            </div>
                            """, unsafe_allow_html=True)
                    st.write("")
            else:
                st.info("No se registraron transferencias el día de hoy.")
        else:
            # Jornada abierta — mostrar progreso en tiempo real
            minutos_restantes = (HORA_CIERRE - hora_ec - 1) * 60 + (60 - ahora_ec.minute)
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(16,185,129,0.1); border: 1px solid #10b981; border-radius: 10px; padding: 12px 20px; margin-bottom: 20px;">
                <span style="color: #10b981; font-weight: 700; font-size: 1rem;">🟢 Jornada Activa — {today_str}</span>
                <span style="color: #94a3b8; font-size: 0.9rem;">⏰ Cierre en: {minutos_restantes // 60}h {minutos_restantes % 60}m (19:00)</span>
            </div>
            """, unsafe_allow_html=True)
            
            todas_las_guias = local_db.find("guias", sort=[("fecha", -1)], limit=1000)
            guias_hoy = [d for d in todas_las_guias if d.get("fecha_emision", "").startswith(today_str) and not d.get("anulada")]
            
            prendas_por_usuario = {}
            for d in guias_hoy:
                usr = d.get("usuario_genera", "Desconocido")
                prendas_por_usuario[usr] = prendas_por_usuario.get(usr, 0) + d.get("total_prendas", 0)
                
            if not prendas_por_usuario:
                st.info("Aún no hay transferencias registradas el día de hoy. Las guías irán apareciendo conforme se generen.")
            else:
                # Ordenar de mayor a menor
                usuarios_ordenados = sorted(prendas_por_usuario.items(), key=lambda x: x[1], reverse=True)
                cols_per_row = 3
                for i in range(0, len(usuarios_ordenados), cols_per_row):
                    row_users = usuarios_ordenados[i:i+cols_per_row]
                    cols = st.columns(cols_per_row)
                    for j, (usr, total_p) in enumerate(row_users):
                        with cols[j]:
                            st.markdown(f"""
                            <div style="background: linear-gradient(145deg, rgba(30,41,59,0.8), rgba(15,23,42,0.9)); border: 1px solid #38bdf8; border-radius: 15px; padding: 25px 15px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.2);">
                                <div style="font-size: 3rem; margin-bottom: 5px;">📦</div>
                                <h2 style="margin: 0; color: #f8fafc; font-size: 1.4rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{usr}</h2>
                                <h1 style="margin: 10px 0; color: #38bdf8; font-size: 3.2rem; font-weight: 800;">{total_p:,}</h1>
                                <p style="margin: 0; color: #94a3b8; font-weight: 600; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Prendas Hoy</p>
                            </div>
                            """, unsafe_allow_html=True)
                    st.write("")
                    st.write("")

        st.divider()
        st.markdown("#### 📊 Histórico de Transferencias (Últimos 7 días)")
        from datetime import timedelta
        
        # Generar los últimos 7 días
        fechas_7d = [(ahora_ec - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(6, -1, -1)]
        prendas_por_dia = {f: 0 for f in fechas_7d}
        
        # Usar todas_las_guias que ya se consultó arriba
        # Si no existe (caso de que se metan condicionales raros), hacer query rápido
        docs_chart = local_db.find("guias", sort=[("fecha", -1)], limit=1000)
        for d in docs_chart:
            f_emision = d.get("fecha_emision", "")[:10]
            if f_emision in prendas_por_dia and not d.get("anulada"):
                prendas_por_dia[f_emision] += d.get("total_prendas", 0)
                
        df_chart = pd.DataFrame(list(prendas_por_dia.items()), columns=["Fecha", "Prendas Transferidas"])
        df_chart.set_index("Fecha", inplace=True)
        st.bar_chart(df_chart, use_container_width=True)

        st.divider()
        st.subheader("📊 Resumen Histórico")
        query = {}
        if rol_activo == "Tienda":
            query["tienda_destino"] = st.session_state.get("assigned_store")
        elif rol_activo in ["Bodega", "Logística"]:
            query["usuario_genera"] = usuario_activo
        docs = local_db.find("guias", query, sort=[("fecha", -1)], limit=500)
        if not docs:
            st.info("No hay guías registradas en tu historial.")
        else:
            # Métricas Generales
            total = len(docs)
            activas = sum(1 for d in docs if not d.get("anulada"))
            recibidas = sum(1 for d in docs if d.get("estado") in (EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.RECIBIDA_NOVEDAD, EstadoGuia.CONCILIADA, EstadoGuia.CERRADA))
            pendientes = activas - recibidas
            
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(f"<div class='acu-kpi-card acu-bg-blue'><div class='acu-kpi-icon'>🏷️</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{total}</span><span class='acu-kpi-label'>Total Guías</span></div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='acu-kpi-card acu-bg-green'><div class='acu-kpi-icon'>⚡</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{activas}</span><span class='acu-kpi-label'>Activas</span></div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='acu-kpi-card acu-bg-yellow'><div class='acu-kpi-icon'>⏳</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{pendientes}</span><span class='acu-kpi-label'>Pendientes</span></div></div>", unsafe_allow_html=True)
            k4.markdown(f"<div class='acu-kpi-card acu-bg-red'><div class='acu-kpi-icon'>📦</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{recibidas}</span><span class='acu-kpi-label'>Recibidas</span></div></div>", unsafe_allow_html=True)
            st.write("")
            
            # Panel de Alertas de Recepción
            st.divider()
            st.subheader("🚨 Panel de Recepciones (Alertas)")
            query_rec = {"recepcion.estado_recepcion": {"$exists": True}}
            if rol_activo == "Tienda":
                query_rec["tienda_destino"] = st.session_state.get("assigned_store")
            elif rol_activo in ["Bodega", "Logística"]:
                query_rec["usuario_genera"] = usuario_activo
            recepciones = local_db.find("guias", query_rec, sort=[("recepcion.fecha_recepcion", -1)], limit=20)
            
            if not recepciones:
                st.info("No hay recepciones recientes.")
            else:
                st.markdown("""
                <style>
                .white-alert-panel {
                    background-color: rgba(241, 245, 249, 0.98);
                    border-radius: 16px;
                    padding: 15px 20px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                    border: 2px solid rgba(255,255,255,0.7);
                    margin-bottom: 15px;
                    color: #0F172A;
                }
                .white-alert-panel h4 { margin: 0 0 10px 0; color: #1E293B; font-weight: 800; border-bottom: 2px solid #CBD5E1; padding-bottom: 8px;}
                .white-alert-panel .kpi-row { display: flex; justify-content: space-between; text-align: center; }
                .white-alert-panel .kpi-box { background: #E2E8F0; border-radius: 8px; padding: 10px; width: 30%; border: 1px solid #CBD5E1;}
                .white-alert-panel .kpi-box span { display: block; font-size: 0.8rem; color: #64748B; font-weight: bold; text-transform: uppercase;}
                .white-alert-panel .kpi-box strong { font-size: 1.2rem; color: #0F172A; }
                .white-alert-panel .kpi-box.dif-rojo { background: #FEE2E2; border-color: #FCA5A5;}
                .white-alert-panel .kpi-box.dif-rojo strong { color: #DC2626; }
                </style>
                """, unsafe_allow_html=True)
                
                for doc in recepciones:
                    rec = doc.get("recepcion", {})
                    tienda = doc.get("tienda_destino", "Desconocida")
                    transf = doc.get("numero_transferencia", "N/A")
                    esperado = doc.get("total_prendas", 0)
                    recibido = rec.get("prendas_recibidas", 0)
                    dif = recibido - esperado
                    
                    estado = rec.get("estado_recepcion", "N/A")
                    color_icon = "✅" if estado == "CONFORME" else "⚠️"
                    dif_class = "dif-rojo" if dif != 0 else ""
                    
                    st.markdown(f"""
                    <div class="white-alert-panel">
                        <h4>{color_icon} {tienda} — Transf: {transf}</h4>
                        <div class="kpi-row">
                            <div class="kpi-box">
                                <span>Esperado</span>
                                <strong>{esperado}</strong>
                            </div>
                            <div class="kpi-box">
                                <span>Recibido</span>
                                <strong>{recibido}</strong>
                            </div>
                            <div class="kpi-box {dif_class}">
                                <span>Diferencia</span>
                                <strong>{dif}</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    incidencias = doc.get("incidencias", [])
                    if incidencias:
                        with st.expander(f"Ver incidencias ({len(incidencias)})"):
                            for inc in incidencias:
                                st.write(f"- **{inc.get('codigo_item', 'N/A')}**: {inc.get('descripcion', '')} ({inc.get('estado_reportado', '')})")
            
            st.divider()
            with st.expander("🗑️ Anular Guía"):
                no_anuladas = [d for d in docs if not d.get("anulada") and not _guia_blindada(d)]
                if no_anuladas:
                    opciones = {str(d["numero_guia"]): d for d in no_anuladas}
                    sel = st.selectbox("Guía a anular", list(opciones.keys()))
                    doc_sel = opciones.get(sel)
                    if doc_sel:
                        generador = doc_sel.get("usuario_genera", "") or doc_sel.get("header", {}).get("usuario_genera", "")
                        puede = (generador == usuario_activo or rol_activo == "Administrador")
                        if puede:
                            motivo = st.text_input("Motivo de anulación")
                            if st.button("❌ Confirmar Anulación", type="secondary"):
                                ok = _cambiar_estado(str(sel), EstadoGuia.ANULADA, usuario_activo,
                                                    descripcion=f"Guía anulada. Motivo: {motivo}",
                                                    metadata={"motivo": motivo})
                                if ok:
                                    local_db.update("guias", {"numero_guia": str(sel)}, {"$set": {"anulada": True}})
                                    st.success(f"Guía {sel} anulada.")
                                    st.rerun()
                                else:
                                    st.error("No se puede anular desde el estado actual.")
                        else:
                            st.warning("Solo el generador o Administrador puede anular.")
                else:
                    st.info("No hay guías activas y no blindadas para anular.")

    # =========================================================================
    # TAB 4 — DETALLE Y TIMELINE
    # =========================================================================
    with tab_det:
        st.subheader("🔍 Detalle y Timeline de Guía")
        docs_sel = local_db.find("guias", {}, sort=[("fecha", -1)], limit=100)
        if not docs_sel:
            st.info("No hay guías registradas.")
        else:
            opciones_det = {str(d["numero_guia"]): d for d in docs_sel}
            num_sel = st.selectbox("Selecciona guía", list(opciones_det.keys()), key="sel_detalle")
            doc_det = opciones_det.get(num_sel)
            if doc_det:
                if _guia_blindada(doc_det):
                    st.info("🔒 Esta guía está **blindada** (en tránsito o posterior). No se pueden modificar datos críticos.")
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f"**Tienda:** {doc_det.get('tienda_destino', '')}")
                    st.markdown(f"**Estado:** {_badge_estado(doc_det.get('estado', ''))}", unsafe_allow_html=True)
                    st.markdown(f"**Transferencia:** {doc_det.get('numero_transferencia', '')}")
                with d2:
                    st.markdown(f"**Total prendas:** {doc_det.get('total_prendas', 0):,}")
                    st.markdown(f"**Bultos:** {doc_det.get('bultos', 0)}")
                    st.markdown(f"**Generado por:** {doc_det.get('usuario_genera', '')}")
                ai = doc_det.get("ai_analysis", {})
                if ai and ai.get("resumen_operacional"):
                    with st.expander("🤖 Análisis IA"):
                        st.info(ai.get("resumen_operacional"))
                        st.markdown(f"Riesgo: **{ai.get('riesgo_detectado', 'N/A')}**")
                rec = doc_det.get("recepcion", {})
                if rec and rec.get("estado_recepcion"):
                    with st.expander("📦 Recepción"):
                        st.markdown(f"**Estado:** {rec.get('estado_recepcion')}")
                        st.markdown(f"**Fecha:** {str(rec.get('fecha_recepcion', ''))[:16]}")
                        st.markdown(f"**Receptor:** {rec.get('usuario_recepcion', '')}")
                        st.markdown(f"**Observaciones:** {rec.get('observaciones', '')}")
                incidencias = doc_det.get("incidencias", [])
                if incidencias:
                    with st.expander(f"⚠️ Incidencias ({len(incidencias)})"):
                        for inc in incidencias:
                            sev_color = {"ALTA": "🔴", "MEDIA": "🟡", "BAJA": "🟢"}.get(inc.get("severidad", ""), "⚪")
                            st.markdown(f"{sev_color} **{inc.get('tipo', '')}** — {inc.get('descripcion', '')} ({str(inc.get('fecha', ''))[:10]})")
                with st.expander("📅 Timeline Operacional", expanded=True):
                    _render_timeline(doc_det.get("timeline", []))
                if not _guia_blindada(doc_det):
                    st.divider()
                    if st.button("🗑️ Eliminar Guía (Permanente)", type="secondary"):
                        if st.checkbox("Confirmo eliminar permanentemente esta guía"):
                            if _eliminar_guia_permanente(num_sel, usuario_activo):
                                st.success("Guía eliminada correctamente.")
                                st.rerun()
                            else:
                                st.error("No se pudo eliminar la guía.")
                else:
                    st.info("No se puede eliminar una guía blindada.")
