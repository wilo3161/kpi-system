# modules/recepcion.py
# ============================================================================
# SISTEMA DE RECEPCIÓN LOGÍSTICA — VERSIÓN ROBUSTECIDA
# Mejoras: validaciones, logging, cacheo, transacciones, notificaciones internas
# ============================================================================

from __future__ import annotations
import io
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from database.manager import local_db
from services.notifications import TelegramBot
from utils.ui import load_css
from utils.backgrounds import set_module_background
from core.event_bus import emitir

# Opcional: Google Drive
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

logger = logging.getLogger(__name__)
TZ_QUITO = ZoneInfo("America/Guayaquil")

# ============================================================================
# ESTADOS (sin cambios)
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

ESTADOS_RECEPCIONABLES = {
    EstadoGuia.EN_MANIFIESTO,
    EstadoGuia.DESPACHADA,
    EstadoGuia.EN_TRANSITO,
    EstadoGuia.RECEPCION_INICIADA,
    EstadoGuia.RECEPCION_PARCIAL,
    "PENDIENTE_RECEPCION",
    "EMITIDA",
}

# ============================================================================
# HELPERS
# ============================================================================
def _ahora() -> str:
    return datetime.now(TZ_QUITO).isoformat()

def _build_evento(evento: str, descripcion: str, usuario: str,
                  modulo: str = "recepcion",
                  metadata: Optional[dict] = None,
                  cambios: Optional[dict] = None) -> dict:
    return {
        "evento": evento,
        "descripcion": descripcion,
        "usuario": usuario,
        "timestamp": _ahora(),
        "modulo": modulo,
        "metadata": metadata or {},
        "cambios_realizados": cambios or {},
    }

# ============================================================================
# NOTIFICACIONES INTERNAS
# ============================================================================
def _enviar_mensaje_interno(destinatario_username: str, asunto: str, contenido: str, remitente: str = "Sistema"):
    """Guarda un mensaje interno en la BD y muestra un toast."""
    doc = {
        "para": destinatario_username,
        "asunto": asunto,
        "contenido": contenido,
        "remitente": remitente,
        "fecha": _ahora(),
        "leido": False
    }
    try:
        local_db.insert("mensajes_internos", doc)
        st.toast(f"📬 Nuevo mensaje para {destinatario_username}: {asunto}", icon="💬")
    except Exception as e:
        logger.error(f"Error guardando mensaje interno: {e}")

def _mostrar_notificaciones_usuario(usuario_actual: str):
    """Muestra los mensajes no leídos del usuario actual."""
    mensajes = local_db.find("mensajes_internos", {"para": usuario_actual, "leido": False}, sort=[("fecha", -1)])
    if mensajes:
        with st.expander(f"📬 Notificaciones ({len(mensajes)} nuevas)"):
            for msg in mensajes:
                st.markdown(f"**📨 {msg['asunto']}**  \n{msg['contenido']}  \n*{msg['remitente']} - {msg['fecha'][:16]}*")
                local_db.update("mensajes_internos", {"_id": msg["_id"]}, {"leido": True})
    else:
        st.info("No tienes notificaciones nuevas.")

# ============================================================================
# ACTUALIZACIÓN DE GUÍA (versión robustecida)
# ============================================================================
@st.cache_data(ttl=60, show_spinner=False)
def _cargar_guia(numero_guia: str) -> Optional[dict]:
    """Carga una guía de forma cacheada."""
    return local_db.find_one("guias", {"numero_guia": str(numero_guia)})

def _actualizar_guia_recepcion(
    numero_guia: str,
    estado_nuevo: str,
    recepcion_data: dict,
    incidencias: list,
    evento: dict,
    usuario: str,
    diferencias_detalle: dict,
) -> bool:
    """
    Actualiza la guía usando transacciones implícitas (MongoDB).
    Valida que la guía exista y no esté ya recepcionada.
    """
    try:
        # 1. Validar estado previo
        guia_existente = local_db.find_one("guias", {"numero_guia": str(numero_guia)})
        if not guia_existente:
            logger.error(f"Guía {numero_guia} no encontrada")
            return False
        
        # Verificar que no esté ya recepcionada como conforme o cerrada
        estado_actual = guia_existente.get("estado")
        if estado_actual in (EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.CERRADA, EstadoGuia.CONCILIADA):
            logger.warning(f"Guía {numero_guia} ya está recepcionada (estado {estado_actual})")
            st.warning("Esta guía ya fue recepcionada anteriormente.")
            return False
        
        # 2. Actualizar guía principal
        ahora_str = _ahora()
        update_doc = {
            "estado": estado_nuevo,
            "recepcion": recepcion_data,
            "audit.updated_at": ahora_str,
            "audit.updated_by": usuario,
        }
        local_db.update("guias", {"numero_guia": str(numero_guia)}, update_doc)
        
        # Agregar timeline e incidencias
        local_db.update(
            "guias",
            {"numero_guia": str(numero_guia)},
            {"$push": {"timeline": evento, "incidencias": {"$each": incidencias}}}
        )
        
        # 3. Registrar faltantes / sobrantes / stock bloqueado (con insert_many para mejor rendimiento)
        docs_faltantes = []
        for falt in diferencias_detalle.get("faltantes", []):
            docs_faltantes.append({
                "numero_guia": numero_guia,
                "tipo": "FALTANTE",
                "codigo": falt.get("codigo"),
                "descripcion": falt.get("descripcion"),
                "cantidad": falt.get("faltante"),
                "fecha": ahora_str,
                "usuario": usuario,
                "estado": "PENDIENTE_RECLAMO"
            })
        if docs_faltantes:
            try: local_db.insert_many("discrepancias", docs_faltantes)
            except Exception as e: logger.error(f"Error insert_many faltantes: {e}")
        
        docs_sobrantes = []
        for sob in diferencias_detalle.get("sobrantes", []):
            docs_sobrantes.append({
                "numero_guia": numero_guia,
                "codigo": sob.get("codigo"),
                "descripcion": sob.get("descripcion"),
                "cantidad": sob.get("sobrante"),
                "fecha": ahora_str,
                "usuario": usuario,
                "estado": "PENDIENTE_AJUSTE"
            })
        if docs_sobrantes:
            try: local_db.insert_many("ingresos_no_esperados", docs_sobrantes)
            except Exception as e: logger.error(f"Error insert_many sobrantes: {e}")
        
        estados_bloqueo = ["DAÑADO", "MANCHA", "COSTURA", "ETIQUETA_INCORRECTA", "PRODUCTO_DIFERENTE"]
        docs_bloqueados = []
        for it in recepcion_data.get("items_received", []):
            if it.get("estado_item") in estados_bloqueo:
                docs_bloqueados.append({
                    "numero_guia": numero_guia,
                    "codigo": it.get("codigo"),
                    "descripcion": it.get("descripcion"),
                    "cantidad": it.get("cantidad_recibida"),
                    "motivo": it.get("estado_item"),
                    "fecha": ahora_str,
                    "usuario": usuario,
                    "estado": "BLOQUEADO"
                })
        if docs_bloqueados:
            try: local_db.insert_many("stock_bloqueado", docs_bloqueados)
            except Exception as e: logger.error(f"Error insert_many stock bloqueado: {e}")
        
        # Invalidar caché de la guía
        st.cache_data.clear()
        return True
        
    except Exception as exc:
        logger.error(f"Error crítico en actualización de recepción: {exc}", exc_info=True)
        return False

# ============================================================================
# CÁLCULO DE DIFERENCIAS (mejorado)
# ============================================================================
def _calcular_diferencias(items_expected: list, items_received: list) -> dict:
    """Calcula diferencias entre lo esperado y lo recibido, con validación de tipos."""
    def get_key(item):
        return item.get("codigo") or item.get("descripcion", f"item_{id(item)}")
    
    esperado_map = {get_key(it): it for it in items_expected if isinstance(it, dict)}
    recibido_map = {get_key(it): it for it in items_received if isinstance(it, dict)}
    
    total_esperado = sum(it.get("cantidad_esperada", 0) for it in items_expected if isinstance(it, dict))
    total_recibido = sum(it.get("cantidad_recibida", 0) for it in items_received if isinstance(it, dict))
    
    faltantes = []
    sobrantes = []
    
    for key, item_esp in esperado_map.items():
        cant_esp = item_esp.get("cantidad_esperada", 0)
        item_rec = recibido_map.get(key, {})
        cant_rec = item_rec.get("cantidad_recibida", 0)
        diff = cant_esp - cant_rec
        if diff > 0:
            faltantes.append({
                "codigo": key,
                "descripcion": item_esp.get("descripcion", ""),
                "faltante": diff
            })
        elif diff < 0:
            sobrantes.append({
                "codigo": key,
                "descripcion": item_esp.get("descripcion", ""),
                "sobrante": abs(diff)
            })
    
    # Ítems recibidos no esperados
    for key, item_rec in recibido_map.items():
        if key not in esperado_map:
            cant_rec = item_rec.get("cantidad_recibida", 0)
            sobrantes.append({
                "codigo": key,
                "descripcion": item_rec.get("descripcion", ""),
                "sobrante": cant_rec
            })
    
    return {
        "total_esperado": total_esperado,
        "total_recibido": total_recibido,
        "diferencia_neta": total_esperado - total_recibido,
        "faltantes": faltantes,
        "sobrantes": sobrantes,
        "tiene_diferencias": bool(faltantes or sobrantes),
    }

# ============================================================================
# GENERACIÓN DE INCIDENCIAS DETALLADAS
# ============================================================================
def _generar_incidencias_detalladas(items_received: list, observaciones: str, usuario: str) -> list:
    incidencias = []
    ahora = _ahora()
    for item in items_received:
        esperado = item.get("cantidad_esperada", 0)
        recibido = item.get("cantidad_recibida", 0)
        codigo = item.get("codigo", "")
        desc = item.get("descripcion", "")
        if recibido != esperado:
            diff = esperado - recibido
            if diff > 0:
                incidencias.append({
                    "tipo": "FALTANTE",
                    "descripcion": f"Faltante {diff} uds de {codigo} – {desc}",
                    "severidad": "ALTA" if diff > 5 else "MEDIA",
                    "usuario": usuario,
                    "fecha": ahora,
                })
            else:
                incidencias.append({
                    "tipo": "SOBRANTE",
                    "descripcion": f"Sobrante {abs(diff)} uds de {codigo} – {desc}",
                    "severidad": "BAJA",
                    "usuario": usuario,
                    "fecha": ahora,
                })
        estado = item.get("estado_item", "CONFORME")
        if estado == "DAÑADO":
            incidencias.append({
                "tipo": "DAÑADO",
                "descripcion": f"{codigo} – {desc} marcado como DAÑADO",
                "severidad": "ALTA",
                "usuario": usuario,
                "fecha": ahora,
            })
        elif estado == "MANCHA":
            incidencias.append({
                "tipo": "DEFECTO_CALIDAD",
                "descripcion": f"{codigo} – {desc} presenta MANCHA",
                "severidad": "MEDIA",
                "usuario": usuario,
                "fecha": ahora,
            })
        elif estado == "COSTURA":
            incidencias.append({
                "tipo": "DEFECTO_CALIDAD",
                "descripcion": f"{codigo} – {desc} defecto de COSTURA",
                "severidad": "MEDIA",
                "usuario": usuario,
                "fecha": ahora,
            })
        elif estado == "ETIQUETA_INCORRECTA":
            incidencias.append({
                "tipo": "DEFECTO_CALIDAD",
                "descripcion": f"{codigo} – {desc} ETIQUETA incorrecta",
                "severidad": "BAJA",
                "usuario": usuario,
                "fecha": ahora,
            })
        elif estado == "PRODUCTO_DIFERENTE":
            incidencias.append({
                "tipo": "PRODUCTO_DIFERENTE",
                "descripcion": f"{codigo} – {desc} producto diferente al esperado",
                "severidad": "ALTA",
                "usuario": usuario,
                "fecha": ahora,
            })
    if observaciones and observaciones.strip():
        incidencias.append({
            "tipo": "OBSERVACION",
            "descripcion": observaciones.strip(),
            "severidad": "BAJA",
            "usuario": usuario,
            "fecha": ahora,
        })
    return incidencias

# ============================================================================
# GENERACIÓN DE ACTA CON NOVEDADES DETALLADAS (Excel y PDF)
# ============================================================================
def generar_acta_recepcion_excel(guia_doc: dict, recepcion_data: dict, diferencias: dict,
                                 incidencias: list, items_received: list) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Resumen
        resumen = {
            "Número de Guía": guia_doc.get("numero_guia"),
            "Tienda Destino": guia_doc.get("tienda_destino"),
            "Transferencia": guia_doc.get("numero_transferencia"),
            "Fecha Recepción": recepcion_data.get("fecha_recepcion", ""),
            "Receptor": recepcion_data.get("usuario_recepcion", ""),
            "Estado Recepción": recepcion_data.get("estado_recepcion", ""),
            "Total Esperado": diferencias.get("total_esperado", 0),
            "Total Recibido": diferencias.get("total_recibido", 0),
            "Diferencia Neta": diferencias.get("diferencia_neta", 0),
            "Observaciones": recepcion_data.get("observaciones", ""),
        }
        df_resumen = pd.DataFrame([resumen])
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
        
        # Detalle de ítems recibidos
        if items_received:
            df_detalle = pd.DataFrame(items_received)
            columnas = {"codigo": "Código", "estilo": "Estilo", "descripcion": "Descripción",
                        "cantidad_esperada": "Esperado", "cantidad_recibida": "Recibido",
                        "estado_item": "Estado", "faltante": "Faltante", "sobrante": "Sobrante"}
            df_detalle = df_detalle.rename(columns={k: v for k, v in columnas.items() if k in df_detalle.columns})
            df_detalle.to_excel(writer, sheet_name="Detalle Ítems", index=False)
        
        # Incidencias
        if incidencias:
            df_inc = pd.DataFrame(incidencias)
            df_inc.to_excel(writer, sheet_name="Incidencias", index=False)
        
        # Novedades por producto
        novedades = []
        for it in items_received:
            esperado = it.get("cantidad_esperada", 0)
            recibido = it.get("cantidad_recibida", 0)
            estado = it.get("estado_item", "CONFORME")
            if esperado != recibido or estado != "CONFORME":
                novedades.append({
                    "Código": it.get("codigo", ""),
                    "Estilo": it.get("estilo", ""),
                    "Descripción": it.get("descripcion", ""),
                    "Esperado": esperado,
                    "Recibido": recibido,
                    "Diferencia": recibido - esperado,
                    "Estado": estado,
                    "Observación": f"Se esperaban {esperado}, se recibieron {recibido}. Estado: {estado}"
                })
        if novedades:
            df_novedades = pd.DataFrame(novedades)
            df_novedades.to_excel(writer, sheet_name="Novedades por Producto", index=False)
    
    output.seek(0)
    return output.getvalue()

def generar_acta_recepcion_pdf(guia_doc: dict, recepcion_data: dict, diferencias: dict,
                               incidencias: list, items_received: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, alignment=TA_CENTER, spaceAfter=20)
    style_heading = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=10)
    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=9, leading=12)
    
    story = []
    story.append(Paragraph("ACTA DE RECEPCIÓN DE MERCANCÍA", style_title))
    story.append(Spacer(1, 0.5*cm))
    
    # Datos generales
    data = [
        ["Número de Guía:", guia_doc.get("numero_guia")],
        ["Tienda Destino:", guia_doc.get("tienda_destino")],
        ["Transferencia:", guia_doc.get("numero_transferencia")],
        ["Fecha Recepción:", recepcion_data.get("fecha_recepcion", "")[:16]],
        ["Receptor:", recepcion_data.get("usuario_recepcion", "")],
        ["Estado:", recepcion_data.get("estado_recepcion", "")],
        ["Total Esperado:", str(diferencias.get("total_esperado", 0))],
        ["Total Recibido:", str(diferencias.get("total_recibido", 0))],
        ["Diferencia Neta:", str(diferencias.get("diferencia_neta", 0))],
        ["Observaciones:", recepcion_data.get("observaciones", "")],
    ]
    table = Table(data, colWidths=[4*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), HexColor('#E5E7EB')),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.7*cm))
    
    # Detalle de ítems
    if items_received:
        story.append(Paragraph("Detalle de productos recibidos", style_heading))
        headers = ["Código", "Estilo", "Descripción", "Esperado", "Recibido", "Estado"]
        tbl_data = [headers]
        for it in items_received:
            tbl_data.append([
                it.get("codigo", ""), it.get("estilo", ""), it.get("descripcion", ""),
                str(it.get("cantidad_esperada", 0)), str(it.get("cantidad_recibida", 0)),
                it.get("estado_item", "")
            ])
        t = Table(tbl_data, repeatRows=1, colWidths=[2.5*cm, 2.5*cm, 5*cm, 1.5*cm, 1.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), HexColor('#1E293B')), ('TEXTCOLOR', (0,0), (-1,0), HexColor('#FFFFFF')),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#CBD5E1')), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))
    
    # Novedades
    novedades = []
    for it in items_received:
        esperado = it.get("cantidad_esperada", 0)
        recibido = it.get("cantidad_recibida", 0)
        estado = it.get("estado_item", "CONFORME")
        if esperado != recibido or estado != "CONFORME":
            diff = recibido - esperado
            novedades.append(f"• {it.get('codigo')} - {it.get('descripcion')}: Esperado {esperado}, Recibido {recibido} ({'+' if diff>0 else ''}{diff} unidades). Estado: {estado}")
    if novedades:
        story.append(Paragraph("NOVEDADES POR PRODUCTO", style_heading))
        for n in novedades:
            story.append(Paragraph(n, style_normal))
        story.append(Spacer(1, 0.5*cm))
    
    # Incidencias
    if incidencias:
        story.append(Paragraph("Incidencias reportadas", style_heading))
        for inc in incidencias:
            story.append(Paragraph(f"• <b>{inc.get('tipo')}</b>: {inc.get('descripcion')} (severidad {inc.get('severidad')})", style_normal))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("Documento generado electrónicamente - Válido como acta de recepción", style_normal))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ============================================================================
# SUBIDA A GOOGLE DRIVE
# ============================================================================
def subir_a_google_drive(archivo_bytes: bytes, nombre_archivo: str, mime_type: str, carpeta_id: str = None) -> str:
    if not GOOGLE_DRIVE_AVAILABLE:
        raise ImportError("google-api-python-client no instalado")
    try:
        creds_json = st.secrets["gdrive_service_account"]
        import json
        creds_info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/drive.file'])
        service = build('drive', 'v3', credentials=credentials)
        media = MediaIoBaseUpload(io.BytesIO(archivo_bytes), mimetype=mime_type, resumable=True)
        file_metadata = {'name': nombre_archivo}
        if carpeta_id:
            file_metadata['parents'] = [carpeta_id]
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('webViewLink', '')
    except Exception as e:
        logger.error(f"Error subiendo a Drive: {e}")
        raise

# ============================================================================
# NOTIFICACIONES TELEGRAM
# ============================================================================
def _notificar_segun_incidencia(guia_doc: dict, estado_recepcion: str, incidencias: list, receptor: str, diferencias: dict):
    try:
        bot = TelegramBot()
        numero_guia = guia_doc.get('numero_guia')
        tienda = guia_doc.get('tienda_destino')
        if estado_recepcion == "CONFORME":
            msg = f"✅ RECEPCIÓN CONFORME\nGuía: {numero_guia}\nTienda: {tienda}\nReceptor: {receptor}"
            bot.enviar_mensaje(msg)
        else:
            msg = f"⚠️ RECEPCIÓN CON NOVEDADES\nGuía: {numero_guia}\nTienda: {tienda}\nReceptor: {receptor}\nIncidencias: {len(incidencias)}"
            bot.enviar_mensaje(msg)
    except Exception as e:
        logger.warning(f"Error en notificación: {e}")

# ============================================================================
# PROCESO PRINCIPAL DE RECEPCIÓN (con todas las validaciones)
# ============================================================================
def _proceso_recepcion_completo(guia_doc: dict) -> None:
    numero_guia = str(guia_doc.get("numero_guia", ""))
    usuario = st.session_state.get("user_name", "receptor")
    creador_guia = guia_doc.get("usuario_genera", "")
    
    # Validar que la tienda coincida (si el usuario es tipo Tienda)
    rol_actual = st.session_state.get("role", "")
    tienda_asignada = st.session_state.get("assigned_store", "")
    if rol_actual == "Tienda" and guia_doc.get("tienda_destino") != tienda_asignada:
        st.error(f"❌ Acceso denegado: Esta guía pertenece a {guia_doc.get('tienda_destino')} y tu tienda asignada es {tienda_asignada}.")
        return

    
    # Validar estado previo
    estado_actual = guia_doc.get("estado", "")
    if estado_actual in (EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.CERRADA, EstadoGuia.CONCILIADA):
        st.success("✅ Esta guía ya fue recepcionada.")
        return
    if estado_actual == EstadoGuia.ANULADA:
        st.error("❌ Guía anulada. No se puede recepcionar.")
        return
    if estado_actual not in ESTADOS_RECEPCIONABLES:
        st.warning(f"Estado {estado_actual} no permite recepción.")
        return
    
    # Cargar items esperados
    items_expected = guia_doc.get("items_expected", [])
    items_expected = [it for it in items_expected if str(it.get("codigo", "")).strip()]
    total_esperado = guia_doc.get("total_prendas", 0)
    
    st.subheader("📦 Mercadería Esperada")
    if items_expected:
        df_esp = pd.DataFrame(items_expected)[["codigo", "estilo", "descripcion", "cantidad_esperada"]]
        st.dataframe(df_esp, use_container_width=True)
    else:
        st.info(f"Total declarado: {total_esperado} prendas. Sin detalle por ítem.")
    
    st.subheader("📋 Registro de Recepción")
    
    if items_expected:
        # Usamos data_editor para evitar re-runs en cada cambio
        st.info("💡 Puedes modificar las cantidades recibidas y el estado directamente en la tabla.")
        df_edit = pd.DataFrame(items_expected)[["codigo", "estilo", "descripcion", "cantidad_esperada"]]
        df_edit["cantidad_recibida"] = df_edit["cantidad_esperada"]
        df_edit["estado_item"] = "CONFORME"
        
        # Configurar columnas para edición
        column_config = {
            "codigo": st.column_config.TextColumn("Código", disabled=True),
            "estilo": st.column_config.TextColumn("Estilo", disabled=True),
            "descripcion": st.column_config.TextColumn("Descripción", disabled=True),
            "cantidad_esperada": st.column_config.NumberColumn("Esperado", disabled=True),
            "cantidad_recibida": st.column_config.NumberColumn("Recibido", min_value=0, step=1),
            "estado_item": st.column_config.SelectboxColumn("Estado", options=["CONFORME", "FALTANTE", "SOBRANTE", "DAÑADO", "MANCHA", "COSTURA", "ETIQUETA_INCORRECTA", "PRODUCTO_DIFERENTE"])
        }
        
        edited_df = st.data_editor(df_edit, column_config=column_config, use_container_width=True, hide_index=True, key=f"editor_{numero_guia}")
        edicion_items = edited_df.to_dict('records')
        
        total_recibido = sum(it["cantidad_recibida"] for it in edicion_items)
        tiene_novedad = any(it["cantidad_recibida"] != it["cantidad_esperada"] or it["estado_item"] != "CONFORME" for it in edicion_items)

    else:
        tipo = st.radio("¿Cómo recibiste la mercadería?", ["✅ Todo completo", "⚠️ Con novedad"], key=f"tipo_{numero_guia}")
        tiene_novedad = tipo == "⚠️ Con novedad"
        total_recibido = st.number_input("Cantidad real recibida", min_value=0, value=total_esperado, step=1, key=f"total_rec_{numero_guia}") if tiene_novedad else total_esperado
        edicion_items = [{
            "codigo": "GENERAL", "descripcion": "Mercadería general",
            "cantidad_esperada": total_esperado, "cantidad_recibida": total_recibido,
            "estado_item": "CONFORME" if total_recibido == total_esperado else "FALTANTE",
        }]
    
    observaciones = st.text_area("Observaciones adicionales", key=f"obs_{numero_guia}")
    
    st.markdown("---")
    confirmacion = st.checkbox("Declaro que la información ingresada es correcta y procedo a confirmar la recepción.", key=f"chk_conf_{numero_guia}")
    
    if st.button("✅ Confirmar Recepción", type="primary", use_container_width=True, disabled=not confirmacion):
        items_received = edicion_items
        diferencias = _calcular_diferencias(items_expected, items_received)
        
        # Determinar estado final
        if tiene_novedad and any(it.get("estado_item") not in ["CONFORME", "FALTANTE", "SOBRANTE"] for it in items_received):
            estado_final = EstadoGuia.RECIBIDA_NOVEDAD
            estado_recepcion = "CON_NOVEDAD"
        elif tiene_novedad:
            estado_final = EstadoGuia.RECEPCION_PARCIAL
            estado_recepcion = "PARCIAL"
        else:
            estado_final = EstadoGuia.RECIBIDA_CONFORME
            estado_recepcion = "CONFORME"
        
        incidencias = _generar_incidencias_detalladas(items_received, observaciones, usuario)
        ahora_str = _ahora()
        recepcion_doc = {
            "estado_recepcion": estado_recepcion, "fecha_recepcion": ahora_str,
            "usuario_recepcion": usuario, "observaciones": observaciones,
            "diferencias_detectadas": diferencias.get("tiene_diferencias", False),
            "diferencias": diferencias, "items_received": items_received, "evidencias": [],
        }
        evento = _build_evento(
            evento=f"RECEPCION_{estado_recepcion}",
            descripcion=f"Recepción {estado_recepcion}: {diferencias.get('total_recibido', total_recibido)}/{diferencias.get('total_esperado', total_esperado)} prendas. {len(incidencias)} incidencias.",
            usuario=usuario, metadata={"total_esperado": diferencias.get("total_esperado"), "total_recibido": diferencias.get("total_recibido")}
        )
        
        ok = _actualizar_guia_recepcion(numero_guia, estado_final, recepcion_doc, incidencias, evento, usuario, diferencias)
        if not ok:
            st.error("❌ Error al guardar la recepción. Por favor contacte a soporte.")
            return
        
        st.success("✅ Recepción guardada exitosamente")
        st.balloons()
        
        # Envío de mensaje interno al creador de la guía
        novedades_texto = ""
        if diferencias.get("tiene_diferencias"):
            novedades_texto = "\n\n**Novedades detectadas:**\n"
            for it in items_received:
                esp = it.get("cantidad_esperada", 0)
                rec = it.get("cantidad_recibida", 0)
                est = it.get("estado_item", "CONFORME")
                if esp != rec or est != "CONFORME":
                    novedades_texto += f"- {it.get('codigo')} - {it.get('descripcion')}: Esperado {esp}, Recibido {rec} ({'faltante' if rec<esp else 'sobrante' if rec>esp else 'ok'}). Estado: {est}\n"
        else:
            novedades_texto = "\n\n✅ Todo conforme, sin novedades."
        contenido_mensaje = f"**Recepción de guía #{numero_guia}**\nTienda: {guia_doc.get('tienda_destino')}\nTotal esperado: {diferencias.get('total_esperado')}\nTotal recibido: {diferencias.get('total_recibido')}\nEstado: {estado_recepcion}{novedades_texto}"
        if creador_guia:
            _enviar_mensaje_interno(creador_guia, f"Recepción de guía #{numero_guia}", contenido_mensaje, remitente=usuario)
        
        # Disparar evento
        try:
            emitir("RECEPCION_CONFIRMADA", {
                "guia": numero_guia, "tienda": guia_doc.get("tienda_destino"),
                "incidencias": len(incidencias), "estado_recepcion": estado_recepcion,
                "usuario": usuario, "timestamp": _ahora()
            })
        except Exception as e:
            logger.warning(f"No se pudo emitir evento: {e}")
        
        # Generar acta
        excel_bytes = None
        pdf_bytes = None
        try:
            excel_bytes = generar_acta_recepcion_excel(guia_doc, recepcion_doc, diferencias, incidencias, items_received)
        except Exception as e:
            logger.error(f"Error al generar acta Excel: {e}")
            st.warning("⚠️ No se pudo generar el acta en Excel.")
            
        try:
            pdf_bytes = generar_acta_recepcion_pdf(guia_doc, recepcion_doc, diferencias, incidencias, items_received)
        except Exception as e:
            logger.error(f"Error al generar acta PDF: {e}")
            st.warning("⚠️ No se pudo generar el acta en PDF.")
        
        col1, col2 = st.columns(2)
        with col1:
            if excel_bytes:
                st.download_button("📥 Descargar Acta (Excel)", excel_bytes, f"acta_recepcion_{numero_guia}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            if pdf_bytes:
                st.download_button("📥 Descargar Acta (PDF)", pdf_bytes, f"acta_recepcion_{numero_guia}.pdf", "application/pdf")
        
        if GOOGLE_DRIVE_AVAILABLE and st.checkbox("📤 Subir acta a Google Drive", key=f"subir_drive_{numero_guia}"):
            try:
                link = subir_a_google_drive(excel_bytes, f"acta_recepcion_{numero_guia}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success(f"Acta subida a Drive: [Ver archivo]({link})")
            except Exception as e:
                st.error(f"Error al subir a Drive: {e}")
        
        _notificar_segun_incidencia(guia_doc, estado_recepcion, incidencias, usuario, diferencias)
        
        st.subheader("Resumen de la Recepción")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='acu-kpi-card acu-bg-blue'><div class='acu-kpi-icon'>📦</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{diferencias['total_esperado']}</span><span class='acu-kpi-label'>Esperado</span></div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='acu-kpi-card acu-bg-green'><div class='acu-kpi-icon'>✅</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{diferencias['total_recibido']}</span><span class='acu-kpi-label'>Recibido</span></div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='acu-kpi-card acu-bg-red'><div class='acu-kpi-icon'>⚠️</div><div class='acu-kpi-data'><span class='acu-kpi-number'>{diferencias['diferencia_neta']}</span><span class='acu-kpi-label'>Diferencia</span></div></div>", unsafe_allow_html=True)
        if incidencias:
            with st.expander("Ver incidencias"):
                for inc in incidencias:
                    st.markdown(f"• **{inc['tipo']}**: {inc['descripcion']}")

# ============================================================================
# PANELES DE BÚSQUEDA Y ADMIN
# ============================================================================
def _panel_busqueda_manual():
    st.subheader("🔍 Buscar Guía para Recepcionar")
    busqueda = st.text_input("N° de guía o transferencia", key="buscar_guia")
    if st.button("Buscar", key="btn_buscar"):
        guia = local_db.find_one("guias", {"numero_guia": busqueda.strip()}) or \
               local_db.find_one("guias", {"numero_transferencia": busqueda.strip()})
        if guia:
            _proceso_recepcion_completo(guia)
        else:
            st.warning("No encontrada")

def _panel_guias_pendientes():
    st.subheader("📋 Guías Pendientes")
    estados = list(ESTADOS_RECEPCIONABLES) + [EstadoGuia.RECEPCION_PARCIAL]
    query = {"estado": {"$in": estados}, "anulada": False}
    
    if st.session_state.get("role") == "Tienda":
        query["tienda_destino"] = st.session_state.get("assigned_store")
        
    guias = local_db.find("guias", query, sort=[("fecha", -1)], limit=50)
    if not guias:
        st.info("No hay guías pendientes")
        return
        
    st.markdown(f"### 🔔 Tienes {len(guias)} transferencias pendientes de recibir")
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    for g in guias:
        transferencia = g.get('numero_transferencia', 'N/A')
        guia_num = g.get('numero_guia', 'N/A')
        remitente = g.get('usuario_genera', 'Desconocido')
        
        with st.expander(f"📦 Transferencia: {transferencia} | Guía: {guia_num} | Remitente: {remitente}"):
            st.write(f"**Tienda Destino:** {g.get('tienda_destino')}")
            st.write(f"**Total Prendas Esperadas:** {g.get('total_prendas')}")
            if st.button("Iniciar Recepción", key=f"btn_init_{guia_num}", type="primary"):
                st.session_state["guia_activa_recepcion"] = g
                st.rerun()

def _panel_historial():
    st.subheader("📜 Historial de Recepciones")
    query = {"estado": {"$in": [EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.RECIBIDA_NOVEDAD, EstadoGuia.CONCILIADA, EstadoGuia.CERRADA]}}
    
    if st.session_state.get("role") == "Tienda":
        query["tienda_destino"] = st.session_state.get("assigned_store")
        
    guias = local_db.find("guias", query, sort=[("fecha", -1)], limit=100)
    if not guias:
        st.info("Sin recepciones")
        return
    data = []
    for g in guias:
        rec = g.get("recepcion", {})
        data.append({
            "Guía": g["numero_guia"], "Tienda": g["tienda_destino"],
            "Fecha": rec.get("fecha_recepcion", "")[:16], "Receptor": rec.get("usuario_recepcion"),
            "Estado": rec.get("estado_recepcion"), "Diferencias": "Sí" if rec.get("diferencias_detectadas") else "No"
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# ============================================================================
# ENTRY POINT
# ============================================================================
def show_recepcion_tienda():
    set_module_background("recepcion")
    try:
        load_css()
    except:
        pass
    
    from utils.ui import inject_acumatica_css
    inject_acumatica_css()
    
    st.markdown('<div style="text-align:center;"><h1>AEROPOSTALE</h1><p>Sistema de Recepción Logística</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Mostrar notificaciones internas
    usuario_actual = st.session_state.get("username", "")
    if usuario_actual:
        _mostrar_notificaciones_usuario(usuario_actual)
    
    if "guia_activa_recepcion" in st.session_state:
        if st.button("⬅️ Volver al listado"):
            del st.session_state["guia_activa_recepcion"]
            st.rerun()
        _proceso_recepcion_completo(st.session_state["guia_activa_recepcion"])
        return
    
    guia_qr = st.query_params.get("guia")
    if guia_qr:
        guia = local_db.find_one("guias", {"numero_guia": str(guia_qr)})
        if guia:
            _proceso_recepcion_completo(guia)
            return
            
    tab1, tab2, tab3 = st.tabs(["📋 Guías Pendientes", "🔍 Buscar", "📜 Historial"])
    with tab1:
        _panel_guias_pendientes()
    with tab2:
        _panel_busqueda_manual()
    with tab3:
        _panel_historial()
    
    if st.session_state.get("role") == "Administrador":
        st.divider()
        st.subheader("Panel Administrativo")
