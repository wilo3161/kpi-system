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
        items.append({
            "codigo": codigo,
            "estilo": estilo,
            "descripcion": descripcion,
            "cantidad_esperada": cantidad,
        })
    return items, total

@st.cache_data(ttl=300, show_spinner=False)
def extraer_datos_transferencia(url: str) -> dict:
    datos = {"numero_transferencia": "", "total_prendas": 0, "items": []}
    try:
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
    return {
        "evento": evento, "descripcion": descripcion, "usuario": usuario,
        "timestamp": datetime.now(TZ_QUITO).isoformat(), "modulo": modulo,
        "metadata": metadata or {}, "cambios_realizados": cambios or {},
    }

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
def generar_pdf_profesional(guia_data: dict) -> bytes:
    buffer = io.BytesIO()
    page_width, page_height = A4
    margen = 1.5 * cm
    doc = SimpleDocTemplate(buffer, pagesize=(page_width, page_height),
                            leftMargin=margen, rightMargin=margen,
                            topMargin=margen, bottomMargin=margen)
    styles = getSampleStyleSheet()
    c_primario, c_secundario, c_fondo, c_borde, c_acento = HexColor("#1E293B"), HexColor("#475569"), HexColor("#F1F5F9"), HexColor("#CBD5E1"), HexColor("#0033A0")
    def st_(name, **kw): return ParagraphStyle(name, parent=styles["Normal"], **kw)
    titulo_s = st_("T", fontName="Helvetica-Bold", fontSize=15, textColor=c_primario, alignment=TA_CENTER, spaceAfter=4, leading=18)
    seccion_s = st_("S", fontName="Helvetica-Bold", fontSize=11, textColor=c_acento, alignment=TA_CENTER, spaceBefore=4, spaceAfter=4)
    campo_s = st_("C", fontName="Helvetica", fontSize=9, textColor=c_secundario, alignment=TA_LEFT, spaceAfter=4, leading=11)
    destac_s = st_("D", fontName="Helvetica-Bold", fontSize=13, textColor=c_primario, alignment=TA_LEFT, spaceAfter=4)
    info_s = st_("I", fontName="Helvetica", fontSize=9, textColor=c_secundario, alignment=TA_LEFT, spaceAfter=3)
    firma_s = st_("F", fontName="Helvetica", fontSize=8, textColor=c_secundario, alignment=TA_CENTER, spaceBefore=12)
    qr_s = st_("Q", fontName="Helvetica-Bold", fontSize=9, textColor=c_primario, alignment=TA_CENTER, spaceBefore=3)
    pie_s = st_("P", fontSize=7, alignment=TA_CENTER, textColor=c_secundario)

    contenido = []
    tienda, marca = guia_data.get("tienda_destino", "Destino"), guia_data.get("marca", "")
    logo_bytes, qr_bytes = guia_data.get("logo_bytes"), guia_data.get("qr_bytes")
    logo_el = Image(io.BytesIO(logo_bytes), width=2.5*cm, height=2.5*cm) if logo_bytes else Paragraph("", campo_s)
    qr_el = Image(io.BytesIO(qr_bytes), width=3.0*cm, height=3.0*cm) if qr_bytes else Paragraph("", campo_s)
    titulo_cell = Paragraph(f"Guía de Remisión<br/>{tienda} — {marca}", titulo_s)
    header_tbl = Table([[logo_el, titulo_cell, qr_el]], colWidths=[3*cm, 11*cm, 4*cm])
    header_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ALIGN", (1,0), (1,0), "CENTER"),
                                    ("ALIGN", (2,0), (2,0), "RIGHT"), ("LEFTPADDING", (0,0), (-1,-1), 2),
                                    ("RIGHTPADDING", (0,0), (-1,-1), 2)]))
    contenido.append(header_tbl)
    if qr_bytes:
        contenido.append(Paragraph("Escanea para confirmar recepción", qr_s))
    contenido.append(Spacer(1, 0.5*cm))
    num_guia, num_trans, tot_prendas = guia_data.get("numero_guia", ""), guia_data.get("numero_transferencia", "No registrada"), guia_data.get("total_prendas", 0)
    contenido.append(Paragraph(f"N° Transferencia: <b>{num_trans}</b>", destac_s))
    contenido.append(Paragraph(f"Total Prendas: <b>{tot_prendas:,}</b>", destac_s))
    contenido.append(Spacer(1, 0.2*cm))
    contenido.append(Paragraph(f"N° Guía: {num_guia} &nbsp;&nbsp; Fecha: {guia_data.get('fecha_emision', '')}", info_s))
    contenido.append(Spacer(1, 0.6*cm))
    dest = guia_data.get("destinatario", {})
    if isinstance(dest, str):
        dest_nombre, dest_dir, dest_tel, dest_ciudad = dest, guia_data.get("direccion_destinatario", ""), guia_data.get("telefono_destinatario", ""), guia_data.get("ciudad", "")
    else:
        dest_nombre, dest_dir, dest_tel, dest_ciudad = dest.get("nombre", ""), dest.get("direccion", ""), dest.get("telefono", ""), dest.get("ciudad", "")
    rem_data = [[Paragraph("REMITENTE", seccion_s)],
                [Paragraph(f"<b>Empresa:</b> {MARCAS.get(marca, {}).get('remitente_empresa', marca)}", campo_s)],
                [Paragraph(f"<b>Dirección:</b> {DIRECCION_REMITENTE}", campo_s)],
                [Paragraph(f"<b>Teléfono:</b> {TELEFONO_REMITENTE}", campo_s)]]
    dest_data = [[Paragraph("DESTINATARIO", seccion_s)],
                 [Paragraph(f"<b>Contacto:</b> {dest_nombre}", campo_s)],
                 [Paragraph(f"<b>Dirección:</b> {dest_dir}", campo_s)],
                 [Paragraph(f"<b>Teléfono:</b> {dest_tel}", campo_s)],
                 [Paragraph(f"<b>Ciudad:</b> {dest_ciudad}", campo_s)]]
    while len(rem_data) < len(dest_data): rem_data.append([Paragraph("", campo_s)])
    tbl_rem, tbl_dest = Table(rem_data, colWidths=[8*cm]), Table(dest_data, colWidths=[8*cm])
    for t in (tbl_rem, tbl_dest):
        t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), c_fondo), ("ALIGN", (0,0), (-1,0), "CENTER"),
                               ("GRID", (0,0), (-1,-1), 0.5, c_borde), ("TOPPADDING", (0,0), (-1,-1), 5),
                               ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
    tbl_side = Table([[tbl_rem, tbl_dest]], colWidths=[8.5*cm, 8.5*cm])
    tbl_side.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    contenido.append(tbl_side)
    contenido.append(Spacer(1, 0.6*cm))
    bultos, peso = guia_data.get("bultos", 0), guia_data.get("peso", 0)
    if bultos or peso:
        contenido.append(Paragraph(f"<b>Bultos:</b> {bultos} &nbsp;&nbsp; <b>Peso:</b> {peso} kg", campo_s))
        contenido.append(Spacer(1, 0.3*cm))
    obs = guia_data.get("observaciones", "")
    if obs:
        contenido.append(Paragraph(f"<b>Observaciones:</b> {obs}", campo_s))
        contenido.append(Spacer(1, 0.5*cm))
    ai = guia_data.get("ai_analysis", {})
    if ai and ai.get("resumen_operacional"):
        contenido.append(Paragraph(f"<b>Análisis IA:</b> {ai['resumen_operacional']} — Riesgo: {ai.get('riesgo_detectado', 'N/A')}", campo_s))
        contenido.append(Spacer(1, 0.4*cm))
    usuario = guia_data.get("usuario_genera", "")
    firma_tbl = Table([[Paragraph("_________________________", campo_s), Paragraph("_________________________", campo_s)],
                       [Paragraph("Revisado por", firma_s), Paragraph(f"Generado por: {usuario}", firma_s)]], colWidths=[8.5*cm, 8.5*cm])
    firma_tbl.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER"), ("TOPPADDING", (0,0), (-1,-1), 10)]))
    contenido.append(firma_tbl)
    contenido.append(Spacer(1, 0.4*cm))
    contenido.append(Paragraph("Documento generado electrónicamente — Válido sin firma física", pie_s))
    doc.build(contenido)
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
# FUNCIÓN PRINCIPAL
# ============================================================================
def show_generar_guias():
    show_module_header("🚚 Guías de Remisión", "Sistema logístico con trazabilidad completa")
    set_module_background("guias")
    
    from utils.ui import inject_acumatica_css
    inject_acumatica_css()

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
        with st.container(border=True):
            components.html("""
            <script>
            const doc = window.parent.document;
            const setStyle = (el, prop, val) => el.style.setProperty(prop, val, "important");
            
            const markers = doc.querySelectorAll('.guia-marker-js');
            markers.forEach(marker => {
                let container = marker.closest('div[data-testid="stVerticalBlock"]');
                if (container) {
                    setStyle(container, "background-color", "rgba(241, 245, 249, 0.98)");
                    setStyle(container, "border-radius", "20px");
                    setStyle(container, "padding", "25px");
                    setStyle(container, "box-shadow", "0 20px 40px rgba(0,0,0,0.4)");
                    setStyle(container, "border", "2px solid rgba(255,255,255,0.8)");
                    
                    const texts = container.querySelectorAll('p, span, h3, h4, label, div[data-testid="stMarkdownContainer"]');
                    texts.forEach(el => { setStyle(el, "color", "#0F172A"); });
                    
                    const inputs = container.querySelectorAll('input, textarea');
                    inputs.forEach(el => {
                        setStyle(el, "background-color", "#FFFFFF");
                        setStyle(el, "color", "#0F172A");
                        setStyle(el, "border", "1px solid #94A3B8");
                        setStyle(el, "border-radius", "6px");
                        setStyle(el, "font-weight", "600");
                    });
                    
                    const selects = container.querySelectorAll('div[data-baseweb="select"] > div');
                    selects.forEach(el => {
                        setStyle(el, "background-color", "#FFFFFF");
                        setStyle(el, "border", "1px solid #94A3B8");
                        setStyle(el, "color", "#0F172A");
                    });
                    
                    const selectTexts = container.querySelectorAll('div[data-baseweb="select"] span');
                    selectTexts.forEach(el => {
                        setStyle(el, "color", "#0F172A");
                    });
                }
            });
            </script>
            """, height=0)
            
            st.markdown("<div class='guia-marker-js'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="text-align:center; margin-bottom: 20px; border-bottom: 2px solid #CBD5E1; padding-bottom:15px;">
                <h3 style="color: #0F172A; margin:0; font-family: 'Bebas Neue', sans-serif; letter-spacing: 1px; font-size: 2.2rem;">FORMULARIO DE NUEVA GUÍA</h3>
                <p style="color: #475569; margin:0; font-size: 0.95rem;">Completa los datos para emitir la guía de remisión.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_m, col_t = st.columns(2)
            with col_m:
                marca_sel = st.selectbox("Marca", list(MARCAS.keys()))
            logo_bytes = cargar_logo_local(marca_sel)
            tiendas_opciones = [t["Nombre de Tienda"] for t in TIENDAS_DATA]
            if not tiendas_opciones:
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
            
            url_transferencia = st.text_input("URL de transferencia", placeholder="https://...")
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
            usar_ia = st.checkbox("🤖 Generar análisis IA al guardar", value=True)
            nuevo_numero = obtener_proximo_numero_guia()
            st.info(f"Número de guía asignado: **{nuevo_numero}**")

        if st.button("💾 Guardar y Generar PDF", type="primary", use_container_width=True):
            if not destinatario or not direccion:
                st.error("Completa destinatario y dirección.")
            else:
                base_url = st.secrets.get("app", {}).get("url", "https://tu-app.streamlit.app")
                qr_url = f"{base_url}?modulo=recepcion&transferencia={numero_transferencia}&guia={nuevo_numero}"
                qr = qrcode.QRCode(box_size=5, border=2)
                qr.add_data(qr_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#0033A0", back_color="white")
                qr_buf = io.BytesIO()
                qr_img.save(qr_buf, format="PNG")
                qr_bytes = qr_buf.getvalue()
                doc_guia = construir_documento_guia(nuevo_numero, marca_sel, tienda_info, tienda_sel,
                                                    destinatario, direccion, telefono, ciudad, float(peso_kg),
                                                    int(bultos), observaciones, str(numero_transferencia),
                                                    int(total_prendas), url_transferencia, usuario_activo,
                                                    qr_url, items_extraidos)
                doc_guia["logo_bytes"] = logo_bytes
                doc_guia["qr_bytes"] = qr_bytes
                if usar_ia:
                    with st.spinner("Analizando con IA..."):
                        doc_guia["ai_analysis"] = _analizar_guia_con_ia(doc_guia)
                try:
                    # Inserción atómica de la guía y actualización del manifiesto
                    local_db.insert("guias", doc_guia)
                    local_db.update("manifiesto", {"_id": st.session_state.manifiesto_obj["_id"]},
                                    {"$push": {"guias": str(nuevo_numero)},
                                     "$inc": {"metricas.total_prendas": int(total_prendas),
                                              "metricas.total_bultos": int(bultos)}})
                    st.success(f"✅ Guía #{nuevo_numero} guardada.")
                except Exception as exc:
                    st.error(f"Error al guardar: {exc}")
                    return
                from core.event_bus import emitir
                emitir("GUIA_CREADA", {"guia": str(nuevo_numero), "tienda": tienda_sel,
                                       "transferencia": numero_transferencia, "prendas": total_prendas,
                                       "peso": peso_kg, "bultos": bultos})
                try:
                    bot = TelegramBot()
                    bot.enviar_mensaje(f"🚚 *NUEVA GUÍA EMITIDA*\n📄 Guía: `{nuevo_numero}`\n🏪 Tienda: {tienda_sel}\n🔄 Transferencia: {numero_transferencia}\n📦 Prendas: {total_prendas:,}\n👤 Usuario: {usuario_activo}")
                except Exception:
                    pass

                pdf_bytes = generar_pdf_profesional(doc_guia)
                st.image(qr_bytes, width=150, caption="QR de recepción")
                st.download_button("📥 Descargar Guía PDF", pdf_bytes, f"guia_{nuevo_numero}.pdf", "application/pdf")

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
                guias_man = local_db.find("guias", {"numero_guia": {"$in": [str(g) for g in guias_ids]}, "anulada": False})
                if guias_man:
                    cols_show = ["numero_guia", "tienda_destino", "fecha_emision", "estado", "bultos", "total_prendas", "usuario_genera"]
                    cols_avail = [c for c in cols_show if any(c in d for d in guias_man)]
                    df_man = pd.DataFrame(guias_man)[cols_avail]
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
        st.subheader("📈 Dashboard de Guías y Acumulado Semanal")
        query = {}
        if rol_activo == "Tienda":
            query["tienda_destino"] = st.session_state.get("assigned_store")
        elif rol_activo in ["Bodega", "Logística"]:
            query["usuario_genera"] = usuario_activo
        docs = local_db.find("guias", query, sort=[("fecha", -1)], limit=500)
        if not docs:
            st.info("No hay guías registradas.")
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
