# modules/recepcion.py
# ============================================================================
# SISTEMA DE RECEPCIÓN LOGÍSTICA — MODELO TRANSACCIONAL SAP MM / MIGO
# Con gestión de discrepancias, stock bloqueado, ingresos no esperados y ACID
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

from database.manager import local_db
from services.notifications import TelegramBot
from utils.ui import load_css
from ai.supply_chain_ai import _ejecutar_prompt
from utils.backgrounds import set_module_background

logger = logging.getLogger(__name__)
TZ_QUITO = ZoneInfo("America/Bogota")

# ============================================================================
# ESTADOS Y MÁQUINA (coherentes con guias.py)
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
        "evento":             evento,
        "descripcion":        descripcion,
        "usuario":            usuario,
        "timestamp":          _ahora(),
        "modulo":             modulo,
        "metadata":           metadata or {},
        "cambios_realizados": cambios or {},
    }


def _actualizar_guia_recepcion_transactional(
    numero_guia: str,
    estado_nuevo: str,
    recepcion_data: dict,
    incidencias: list,
    evento: dict,
    usuario: str,
    diferencias_detalle: dict,
    session=None
) -> bool:
    """
    Versión transaccional (ACID) usando sesión de MongoDB.
    Si session es None, opera sin transacción (fallback).
    """
    ahora_str = _ahora()
    try:
        # 1. Actualizar guía
        local_db.update(
            "guias",
            {"numero_guia": str(numero_guia)},
            {
                "$set": {
                    "estado":           estado_nuevo,
                    "recepcion":        recepcion_data,
                    "audit.updated_at": ahora_str,
                    "audit.updated_by": usuario,
                },
                "$push": {
                    "timeline":    evento,
                    "incidencias": {"$each": incidencias},
                },
            },
            session=session
        )

        # 2. Procesar diferencias: generar documentos de discrepancia, ingresos no esperados, stock bloqueado
        if diferencias_detalle.get("faltantes"):
            for falt in diferencias_detalle["faltantes"]:
                doc_discrepancia = {
                    "numero_guia": numero_guia,
                    "tipo": "FALTANTE",
                    "codigo": falt["codigo"],
                    "descripcion": falt.get("descripcion", ""),
                    "cantidad": falt["faltante"],
                    "fecha": ahora_str,
                    "usuario": usuario,
                    "estado": "PENDIENTE_RECLAMO"
                }
                local_db.insert("discrepancias", doc_discrepancia, session=session)

        if diferencias_detalle.get("sobrantes"):
            for sob in diferencias_detalle["sobrantes"]:
                ingreso_no_esperado = {
                    "numero_guia": numero_guia,
                    "codigo": sob["codigo"],
                    "descripcion": sob.get("descripcion", ""),
                    "cantidad": sob["sobrante"],
                    "fecha": ahora_str,
                    "usuario": usuario,
                    "estado": "PENDIENTE_AJUSTE"
                }
                local_db.insert("ingresos_no_esperados", ingreso_no_esperado, session=session)

        # 3. Procesar ítems con estado dañado o subclasificación de averías
        items_received = recepcion_data.get("items_received", [])
        for it in items_received:
            estado_item = it.get("estado_item", "")
            if estado_item in ["DAÑADO", "MANCHA", "COSTURA", "ETIQUETA_INCORRECTA", "PRODUCTO_DIFERENTE"]:
                stock_bloq = {
                    "numero_guia": numero_guia,
                    "codigo": it.get("codigo"),
                    "descripcion": it.get("descripcion"),
                    "cantidad": it.get("cantidad_recibida", 0),
                    "motivo": estado_item,
                    "fecha": ahora_str,
                    "usuario": usuario,
                    "estado": "BLOQUEADO"
                }
                local_db.insert("stock_bloqueado", stock_bloq, session=session)

        return True
    except Exception as exc:
        logger.error("Error en actualización transaccional: %s", exc)
        return False


def _calcular_diferencias(items_expected: list, items_received: list) -> dict:
    esperado_map = {it.get("codigo", it.get("descripcion", i)): it
                    for i, it in enumerate(items_expected)}
    recibido_map = {it.get("codigo", it.get("descripcion", i)): it
                    for i, it in enumerate(items_received)}

    total_esperado = sum(it.get("cantidad_esperada", 0) for it in items_expected)
    total_recibido = sum(it.get("cantidad_recibida", 0) for it in items_received)
    faltantes = []
    sobrantes = []

    for codigo, item_esp in esperado_map.items():
        cant_esp = item_esp.get("cantidad_esperada", 0)
        item_rec = recibido_map.get(codigo, {})
        cant_rec = item_rec.get("cantidad_recibida", 0)
        diff = cant_esp - cant_rec
        if diff > 0:
            faltantes.append({"codigo": codigo, "descripcion": item_esp.get("descripcion", ""),
                              "faltante": diff})
        elif diff < 0:
            sobrantes.append({"codigo": codigo, "descripcion": item_esp.get("descripcion", ""),
                              "sobrante": abs(diff)})

    return {
        "total_esperado": total_esperado,
        "total_recibido": total_recibido,
        "diferencia_neta": total_esperado - total_recibido,
        "faltantes": faltantes,
        "sobrantes": sobrantes,
        "tiene_diferencias": bool(faltantes or sobrantes),
    }


def _generar_incidencias_detalladas(items_received: list, observaciones: str, usuario: str) -> list:
    """
    Genera incidencias con subclasificación de averías.
    """
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
        # Mapeo de estados de calidad
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
# IA — ANÁLISIS DE RECEPCIÓN (con sugerencia de aceptación/rechazo)
# ============================================================================

def _analizar_recepcion_con_ia(guia_doc: dict, diferencias: dict, observaciones: str, estado_recepcion: str) -> dict:
    fallback = {
        "resumen_operacional": f"Recepción {estado_recepcion} para guía {guia_doc.get('numero_guia')}.",
        "riesgo_detectado": "MEDIO" if diferencias.get("tiene_diferencias") else "BAJO",
        "acciones_sugeridas": [],
        "correo_sugerido": None,
        "prioridad_operativa": "NORMAL",
        "sugerencia_aceptacion": "ACEPTAR_PARCIAL"  # ACEPTAR_PARCIAL, RECHAZAR_CAMION, ACEPTAR_TOTAL
    }

    total_esperado = diferencias.get('total_esperado', guia_doc.get('total_prendas', 0))
    total_recibido = diferencias.get('total_recibido', 0)
    porcentaje_error = 0
    if total_esperado > 0:
        porcentaje_error = abs(total_esperado - total_recibido) / total_esperado * 100

    prompt = f"""
Eres analista de logística de Aeropostale Ecuador. Analiza esta recepción y responde SOLO en JSON válido.

Datos:
- Guía: {guia_doc.get('numero_guia')}
- Tienda: {guia_doc.get('tienda_destino')}
- Transferencia: {guia_doc.get('numero_transferencia')}
- Estado recepción: {estado_recepcion}
- Total esperado: {total_esperado}
- Total recibido: {total_recibido}
- Porcentaje de error: {porcentaje_error:.2f}%
- Diferencia neta: {diferencias.get('diferencia_neta', 0)}
- Faltantes: {json.dumps(diferencias.get('faltantes', []))}
- Sobrantes: {json.dumps(diferencias.get('sobrantes', []))}
- Observaciones: {observaciones or 'Ninguna'}

Responde EXACTAMENTE con este JSON (sin backticks ni texto extra):
{{
  "resumen_operacional": "resumen ejecutivo de 1-2 oraciones",
  "riesgo_detectado": "BAJO|MEDIO|ALTO",
  "acciones_sugeridas": ["acción 1", "acción 2"],
  "correo_sugerido": "asunto del correo de notificación a gerencia",
  "prioridad_operativa": "NORMAL|ALTA|CRITICA",
  "sugerencia_aceptacion": "ACEPTAR_TOTAL|ACEPTAR_PARCIAL|RECHAZAR_CAMION"
}}

Reglas para sugerencia_aceptacion:
- ACEPTAR_TOTAL si error < 2%
- ACEPTAR_PARCIAL si error entre 2% y 10%
- RECHAZAR_CAMION si error > 10% o si hay daños graves (>20% de los ítems dañados)
"""
    respuesta = _ejecutar_prompt(prompt, json.dumps(fallback))
    try:
        return json.loads(respuesta)
    except Exception:
        logger.warning("No se pudo parsear la respuesta de IA, usando fallback.")
        return fallback


# ============================================================================
# NOTIFICACIONES DIFERENCIADAS (Tabla NAST simulada)
# ============================================================================

def _notificar_segun_incidencia(guia_doc: dict, estado_recepcion: str, incidencias: list, receptor: str, diferencias: dict):
    """Envía alertas específicas según el tipo y severidad de la incidencia."""
    try:
        bot = TelegramBot()
        numero_guia = guia_doc.get('numero_guia')
        tienda = guia_doc.get('tienda_destino')

        # Alerta general
        if estado_recepcion == "CONFORME":
            msg = f"✅ *RECEPCIÓN CONFORME*\nGuía: {numero_guia}\nTienda: {tienda}\nReceptor: {receptor}"
            bot.enviar_mensaje(msg)
        else:
            # Notificar al jefe de logística si faltante > 5%
            total_esperado = diferencias.get('total_esperado', 0)
            total_recibido = diferencias.get('total_recibido', 0)
            if total_esperado > 0:
                porcentaje_faltante = (total_esperado - total_recibido) / total_esperado * 100
                if porcentaje_faltante > 5:
                    msg_jefe = (
                        f"🚨 *ALERTA LOGÍSTICA* 🚨\n"
                        f"Faltante >5% en recepción\n"
                        f"Guía: {numero_guia}\n"
                        f"Tienda: {tienda}\n"
                        f"Esperado: {total_esperado}\n"
                        f"Recibido: {total_recibido}\n"
                        f"Diferencia: {diferencias.get('diferencia_neta', 0)}"
                    )
                    # Enviar a chat_id específico del jefe (configurable)
                    bot.enviar_mensaje(msg_jefe, chat_id="WILSON_PEREZ_CHAT_ID")

            # Notificar al encargado de reprocesado si hay ítems dañados
            danados = [inc for inc in incidencias if inc['tipo'] in ['DAÑADO', 'DEFECTO_CALIDAD', 'MANCHA', 'COSTURA']]
            if danados:
                msg_repro = (
                    f"🛠️ *ÍTEMS PARA REPROCESADO*\n"
                    f"Guía: {numero_guia}\n"
                    f"Tienda: {tienda}\n"
                    f"Cantidad de ítems con defectos: {len(danados)}\n"
                    f"Detalle: {', '.join([d['descripcion'][:50] for d in danados])}"
                )
                bot.enviar_mensaje(msg_repro, chat_id="REPROCESADO_CHAT_ID")

    except Exception as e:
        logger.warning(f"Error enviando notificaciones: {e}")


# ============================================================================
# COMPONENTES DE UI
# ============================================================================

def _badge(texto: str, color: str = "#3B82F6") -> str:
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:0.75rem;font-weight:600;">{texto}</span>')


def _render_alerta_guia(guia_doc: dict) -> None:
    estado = guia_doc.get("estado", "")
    color_map = {
        EstadoGuia.RECIBIDA_CONFORME: "#10B981",
        EstadoGuia.RECIBIDA_NOVEDAD:  "#F59E0B",
        EstadoGuia.ANULADA:           "#EF4444",
    }
    color = color_map.get(estado, "#3B82F6")

    st.markdown(
        f'<div style="border:1px solid {color};border-radius:8px;padding:12px 16px;'
        f'background:{color}15;margin-bottom:12px;">'
        f'<b>Guía #{guia_doc.get("numero_guia")}</b> &nbsp;'
        f'{_badge(estado, color)}<br/>'
        f'<small>Tienda: <b>{guia_doc.get("tienda_destino", "")}</b> &nbsp;|&nbsp; '
        f'Transferencia: <b>{guia_doc.get("numero_transferencia", "")}</b> &nbsp;|&nbsp; '
        f'Prendas esperadas: <b>{guia_doc.get("total_prendas", 0):,}</b></small>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_timeline_mini(timeline: list, max_items: int = 5) -> None:
    for ev in list(reversed(timeline))[:max_items]:
        ts = ev.get("timestamp", "")[:16].replace("T", " ")
        evt = ev.get("evento", "")
        desc = ev.get("descripcion", "")
        st.markdown(
            f'<div style="border-left:3px solid #3B82F6;padding:3px 10px;margin:3px 0;">'
            f'<small style="color:#94A3B8">{ts}</small> '
            f'<span style="font-weight:600">{evt}</span>: {desc}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================================
# PANEL ADMINISTRATIVO
# ============================================================================

def _panel_admin() -> None:
    st.subheader("🛡️ Panel Administrativo de Recepciones")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tienda_filter = st.selectbox(
            "Tienda",
            ["Todas"] + sorted(set(
                g.get("tienda_destino", "") for g in local_db.find("guias", {})
            )),
            key="adm_tienda"
        )
    with col_f2:
        estado_filter = st.selectbox(
            "Estado recepción",
            ["Todos", "CONFORME", "CON_NOVEDAD", "PARCIAL"],
            key="adm_estado"
        )
    with col_f3:
        usuario_filter = st.text_input("Usuario generador", key="adm_usuario")

    query = {}
    if tienda_filter != "Todas":
        query["tienda_destino"] = tienda_filter
    if usuario_filter:
        query["usuario_genera"] = usuario_filter
    guias = local_db.find("guias", query, sort=[("fecha", -1)], limit=200)

    if estado_filter != "Todos":
        guias = [g for g in guias if g.get("recepcion", {}).get("estado_recepcion") == estado_filter]

    total_recep = sum(1 for g in guias if g.get("recepcion", {}).get("estado_recepcion"))
    conformes = sum(1 for g in guias if g.get("recepcion", {}).get("estado_recepcion") == "CONFORME")
    con_novedad = total_recep - conformes

    m1, m2, m3 = st.columns(3)
    m1.metric("Recepcionadas", total_recep)
    m2.metric("Conformes", conformes)
    m3.metric("Con novedad", con_novedad)

    data = []
    for g in guias:
        rec = g.get("recepcion", {})
        data.append({
            "Guía": str(g.get("numero_guia")),
            "Transferencia": g.get("numero_transferencia"),
            "Tienda": g.get("tienda_destino"),
            "Estado recepción": rec.get("estado_recepcion", "Pendiente"),
            "Generador": g.get("usuario_genera"),
            "Receptor": rec.get("usuario_recepcion"),
            "Diferencias": "Sí" if rec.get("diferencias_detectadas") else "No",
            "Fecha": str(rec.get("fecha_recepcion", ""))[:16]
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="AdminRecepciones")
    st.download_button("📥 Exportar a Excel", buf.getvalue(), "recepciones_admin.xlsx")


# ============================================================================
# FLUJO PRINCIPAL DE RECEPCIÓN (con soporte transaccional)
# ============================================================================

def _proceso_recepcion_completo(guia_doc: dict) -> None:
    numero_guia = str(guia_doc.get("numero_guia", ""))
    usuario = st.session_state.get("user_name", "receptor")

    _render_alerta_guia(guia_doc)

    estado_actual = guia_doc.get("estado", "")

    if estado_actual == EstadoGuia.ANULADA:
        st.error("❌ Esta guía está ANULADA. No se puede recepcionar.")
        return
    if estado_actual in (EstadoGuia.RECIBIDA_CONFORME, EstadoGuia.CERRADA, EstadoGuia.CONCILIADA):
        st.success("✅ Esta guía ya fue recepcionada y conciliada.")
        rec = guia_doc.get("recepcion", {})
        if rec:
            st.markdown(f"**Fecha recepción:** {str(rec.get('fecha_recepcion', ''))[:16]}")
            st.markdown(f"**Receptor:** {rec.get('usuario_recepcion', '')}")
            st.markdown(f"**Observaciones:** {rec.get('observaciones', '')}")
        return
    if estado_actual == EstadoGuia.RECIBIDA_NOVEDAD:
        st.warning("⚠️ Esta guía fue recibida CON NOVEDADES. Puede agregar más información.")
    if estado_actual not in ESTADOS_RECEPCIONABLES:
        st.warning(f"La guía está en estado **{estado_actual}** y no está disponible para recepción.")
        return

    # Análisis de riesgo pre-recepción
    if st.button("🔮 Analizar riesgo de esta recepción", key=f"riesgo_rec_{numero_guia}"):
        from ai.supply_chain_ai import predecir_riesgo_recepcion
        riesgo = predecir_riesgo_recepcion(guia_doc)
        st.info(f"🛡️ Riesgo estimado: {riesgo}")

    # Leer items_expected y filtrar productos basura
    items_expected = guia_doc.get("items_expected", [])
    items_expected = [
        it for it in items_expected
        if str(it.get("codigo", "")).strip()
        and not any(p in str(it.get("descripcion", "")).upper()
                    for p in ["PROVEEDOR", "TOTAL", "SUBTOTAL"])
    ]
    total_esperado = guia_doc.get("total_prendas", 0)

    # ── Mercadería esperada ──────────────────────────────────────────────
    st.subheader("📦 Mercadería Esperada")
    if items_expected:
        cols_mostrar = ["codigo", "estilo", "descripcion", "cantidad_esperada"]
        cols_exist = [c for c in cols_mostrar if any(c in item for item in items_expected)]
        if cols_exist:
            df_esp = pd.DataFrame(items_expected)[cols_exist]
            st.dataframe(df_esp, use_container_width=True)
        else:
            st.info("Detalle de productos disponible pero sin columnas predefinidas.")
    else:
        st.info(f"Sin detalle por ítem. Total declarado: **{total_esperado:,} prendas**.")

    # ── Formulario de recepción con clasificación avanzada ─────────────────
    st.subheader("📋 Registro de Recepción")
    edicion_items = []
    tiene_novedad = False

    if items_expected:
        st.caption("Ingrese la cantidad recibida y marque el estado de cada producto.")
        hdr_cols = st.columns([2, 2, 3, 1, 1, 1.5])
        hdr_cols[0].markdown("**Código**")
        hdr_cols[1].markdown("**Estilo**")
        hdr_cols[2].markdown("**Descripción**")
        hdr_cols[3].markdown("**Esperado**")
        hdr_cols[4].markdown("**Recibido**")
        hdr_cols[5].markdown("**Estado**")

        for i, item in enumerate(items_expected):
            cols = st.columns([2, 2, 3, 1, 1, 1.5])
            codigo = item.get("codigo", "")
            estilo = item.get("estilo", "")
            desc = item.get("descripcion", "")
            esperado = item.get("cantidad_esperada", 0)

            with cols[0]:
                st.markdown(f"**{codigo}**")
            with cols[1]:
                st.markdown(f"{estilo}")
            with cols[2]:
                st.markdown(f"{desc}")
            with cols[3]:
                st.markdown(f"{esperado}")
            with cols[4]:
                recibido = st.number_input(
                    "Recibido", min_value=0, value=esperado, step=1,
                    key=f"rec_{numero_guia}_{i}",
                    label_visibility="collapsed"
                )
            with cols[5]:
                # Estados ampliados con subclasificación de averías
                estado = st.selectbox(
                    "Estado",
                    ["CONFORME", "FALTANTE", "SOBRANTE", "DAÑADO", "MANCHA", "COSTURA", "ETIQUETA_INCORRECTA", "PRODUCTO_DIFERENTE"],
                    key=f"est_{numero_guia}_{i}",
                    label_visibility="collapsed"
                )
            edicion_items.append({
                "codigo": codigo,
                "estilo": estilo,
                "descripcion": desc,
                "cantidad_esperada": esperado,
                "cantidad_recibida": recibido,
                "estado_item": estado,
                "faltante": max(0, esperado - recibido),
                "sobrante": max(0, recibido - esperado),
            })

        total_recibido = sum(it["cantidad_recibida"] for it in edicion_items)
        tiene_novedad = any(
            it["cantidad_recibida"] != it["cantidad_esperada"] or it["estado_item"] != "CONFORME"
            for it in edicion_items
        )
    else:
        tipo = st.radio(
            "¿Cómo recibiste la mercadería?",
            ["✅ Todo completo y conforme", "⚠️ Con novedad"],
            key=f"tipo_rec_{numero_guia}"
        )
        tiene_novedad = tipo != "✅ Todo completo y conforme"
        if tiene_novedad:
            total_recibido = st.number_input(
                "Cantidad real recibida", min_value=0, value=total_esperado, step=1,
                key=f"cant_rec_{numero_guia}"
            )
        else:
            total_recibido = total_esperado

    observaciones = st.text_area("Observaciones adicionales", key=f"obs_{numero_guia}")

    confirmar = st.button(
        "✅ Confirmar Recepción" if not tiene_novedad else "⚠️ Confirmar Recepción con Novedad",
        type="primary", use_container_width=True,
        key=f"btn_confirmar_{numero_guia}"
    )

    if not confirmar:
        return

    # Procesamiento con transacción ACID
    ahora_str = _ahora()
    if not items_expected:
        items_received = [{
            "codigo": "GENERAL",
            "descripcion": "Mercadería general",
            "cantidad_esperada": total_esperado,
            "cantidad_recibida": total_recibido,
            "faltante": max(0, total_esperado - total_recibido),
            "sobrante": max(0, total_recibido - total_esperado),
            "estado_item": "CONFORME" if total_recibido == total_esperado else "FALTANTE",
        }]
        edicion_items = items_received
        diferencias = _calcular_diferencias(
            [{"cantidad_esperada": total_esperado}], items_received
        )
    else:
        items_received = edicion_items
        diferencias = _calcular_diferencias(items_expected, items_received)

    estado_final = EstadoGuia.RECIBIDA_CONFORME
    estado_recepcion = "CONFORME"
    if tiene_novedad:
        if any(it.get("estado_item") in ["FALTANTE", "SOBRANTE", "DAÑADO", "MANCHA", "COSTURA", "ETIQUETA_INCORRECTA", "PRODUCTO_DIFERENTE"] for it in items_received):
            estado_final = EstadoGuia.RECIBIDA_NOVEDAD
            estado_recepcion = "CON_NOVEDAD"
        else:
            estado_final = EstadoGuia.RECEPCION_PARCIAL
            estado_recepcion = "PARCIAL"

    incidencias = _generar_incidencias_detalladas(items_received, observaciones, usuario)

    ai_result = {}
    usar_ia = st.checkbox("🤖 Generar análisis IA", value=True, key=f"ia_{numero_guia}")
    if usar_ia:
        with st.spinner("Analizando con IA..."):
            ai_result = _analizar_recepcion_con_ia(guia_doc, diferencias, observaciones, estado_recepcion)
            # Mostrar sugerencia de aceptación/rechazo
            sugerencia = ai_result.get("sugerencia_aceptacion", "ACEPTAR_PARCIAL")
            if sugerencia == "RECHAZAR_CAMION":
                st.error("🚨 La IA recomienda RECHAZAR EL CAMIÓN completo debido al alto porcentaje de error o daños graves.")
                if not st.checkbox("Forzar recepción a pesar de la recomendación"):
                    return
            elif sugerencia == "ACEPTAR_PARCIAL":
                st.warning("⚠️ La IA recomienda ACEPTAR PARCIALMENTE la recepción. Revise las incidencias.")
            else:
                st.success("✅ La IA recomienda ACEPTAR TOTALMENTE la recepción.")

    recepcion_doc = {
        "estado_recepcion": estado_recepcion,
        "fecha_recepcion": ahora_str,
        "usuario_recepcion": usuario,
        "observaciones": observaciones,
        "diferencias_detectadas": diferencias.get("tiene_diferencias", False),
        "diferencias": diferencias,
        "items_received": items_received,
        "tipo_reporte": "DETALLADO" if items_expected else "GENERAL",
        "evidencias": [],
    }

    evento = _build_evento(
        evento=f"RECEPCION_{estado_recepcion}",
        descripcion=(
            f"Recepción {estado_recepcion}: "
            f"{diferencias.get('total_recibido', total_recibido)}/{diferencias.get('total_esperado', total_esperado)} prendas. "
            f"{len(incidencias)} incidencia(s)."
        ),
        usuario=usuario,
        modulo="recepcion",
        metadata={
            "total_esperado": diferencias.get("total_esperado", total_esperado),
            "total_recibido": diferencias.get("total_recibido", total_recibido),
            "diferencia_neta": diferencias.get("diferencia_neta", 0),
            "ai_riesgo": ai_result.get("riesgo_detectado", "N/A"),
            "ai_sugerencia": ai_result.get("sugerencia_aceptacion", "N/A")
        },
        cambios={
            "estado_anterior": guia_doc.get("estado", ""),
            "estado_nuevo": estado_final,
        },
    )

    # --- TRANSACCIÓN ACID ---
    # Iniciar sesión de MongoDB (requiere replica set habilitado)
    session = None
    try:
        # Si la base de datos soporta transacciones, iniciar sesión
        if local_db.client is not None:
            session = local_db.client.start_session()
            session.start_transaction()
    except Exception:
        session = None  # Fallback a operaciones no transaccionales

    ok = _actualizar_guia_recepcion_transactional(
        numero_guia, estado_final, recepcion_doc, incidencias, evento, usuario,
        diferencias, session=session
    )

    if not ok:
        if session:
            session.abort_transaction()
        st.error("❌ Error al guardar la recepción. Se ha cancelado la operación.")
        return

    # Confirmar transacción
    if session:
        session.commit_transaction()
        session.end_session()

    # Emitir evento
    from core.event_bus import emitir
    emitir("RECEPCION_CONFIRMADA", {
        "guia": numero_guia,
        "tienda": guia_doc.get("tienda_destino"),
        "estado": estado_recepcion,
        "incidencias": len(incidencias)
    })

    # Generar tarea automática si hay incidencias
    if incidencias:
        from automation.task_manager import generar_tarea_por_guia
        generar_tarea_por_guia(
            numero_guia,
            f"Recepción con novedad: {len(incidencias)} incidencia(s) en {guia_doc.get('tienda_destino')}",
            prioridad="ALTA" if len(incidencias) > 2 else "MEDIA"
        )

    # Notificaciones diferenciadas
    _notificar_segun_incidencia(guia_doc, estado_recepcion, incidencias, usuario, diferencias)

    # También notificar al generador original
    from modules.recepcion_legacy import _notificar_generador  # import temporal
    _notificar_generador(guia_doc, estado_recepcion, incidencias, usuario)

    if estado_recepcion == "CONFORME":
        st.success("✅ Recepción confirmada – Todo conforme")
    else:
        st.warning(f"⚠️ Recepción {estado_recepcion}")
    st.balloons()

    # Acciones correctivas post-recepción
    if estado_recepcion != "CONFORME":
        if st.button("🧠 Recomendar acción correctiva", key=f"accion_{numero_guia}"):
            from ai.supply_chain_ai import recomendar_accion_correctiva
            accion = recomendar_accion_correctiva(
                f"Recepción {estado_recepcion}",
                {
                    "tienda": guia_doc.get("tienda_destino"),
                    "transferencia": guia_doc.get("numero_transferencia"),
                    "esperado": diferencias.get("total_esperado"),
                    "recibido": diferencias.get("total_recibido"),
                    "incidencias": len(incidencias)
                }
            )
            st.info(f"🤖 Recomendación IA: {accion}")

        if incidencias:
            if st.button("✉️ Generar borrador de correo", key=f"correo_{numero_guia}"):
                from ai.supply_chain_ai import generar_borrador_correo
                borrador = generar_borrador_correo(
                    f"Incidencia en recepción {guia_doc.get('numero_transferencia')}",
                    {"tienda": guia_doc.get("tienda_destino"), "incidencias": incidencias}
                )
                st.code(borrador, language="markdown")

    c1, c2, c3 = st.columns(3)
    c1.metric("Esperado", diferencias["total_esperado"])
    c2.metric("Recibido", diferencias["total_recibido"])
    c3.metric("Diferencia", diferencias["diferencia_neta"])

    if incidencias:
        st.subheader("Incidencias")
        for inc in incidencias:
            st.markdown(f"• {inc['tipo']}: {inc['descripcion']}")

    if ai_result and ai_result.get("resumen_operacional"):
        with st.expander("🤖 Análisis IA de la Recepción"):
            st.info(ai_result["resumen_operacional"])
            st.markdown(f"**Riesgo:** {ai_result.get('riesgo_detectado', 'N/A')}")
            st.markdown(f"**Sugerencia:** {ai_result.get('sugerencia_aceptacion', 'N/A')}")
            if ai_result.get("acciones_sugeridas"):
                st.markdown("**Acciones sugeridas:**")
                for a in ai_result["acciones_sugeridas"]:
                    st.markdown(f"- {a}")
            if ai_result.get("correo_sugerido"):
                st.info(f"📧 Asunto sugerido para correo: **{ai_result['correo_sugerido']}**")


# ============================================================================
# PANEL INTERNO DE RECEPCIÓN (buscar, pendientes, historial)
# ============================================================================

def _panel_busqueda_manual() -> None:
    st.subheader("🔍 Buscar Guía para Recepcionar")
    col_s, col_b = st.columns([3, 1])
    with col_s:
        busqueda = st.text_input("N° de guía o N° de transferencia",
                                 placeholder="Ej: 1001 o 85640",
                                 key="busqueda_guia")
    with col_b:
        buscar = st.button("Buscar", use_container_width=True, key="btn_buscar")
    if not buscar or not busqueda:
        return

    guia_doc = local_db.find_one("guias", {"numero_guia": busqueda.strip()})
    if not guia_doc:
        guia_doc = local_db.find_one("guias", {"numero_transferencia": busqueda.strip()})
    if not guia_doc:
        try:
            guia_doc = local_db.find_one("guias", {"numero_guia": int(busqueda.strip())})
        except ValueError:
            pass
    if guia_doc:
        if isinstance(guia_doc.get("numero_guia"), int):
            guia_doc["numero_guia"] = str(guia_doc["numero_guia"])
        _proceso_recepcion_completo(guia_doc)
    else:
        st.warning(f"No se encontró ninguna guía con el valor: **{busqueda}**")


def _panel_guias_pendientes() -> None:
    st.subheader("📋 Guías Pendientes de Recepción")
    estados_pendientes = list(ESTADOS_RECEPCIONABLES) + [EstadoGuia.RECEPCION_PARCIAL]
    guias = local_db.find("guias",
                          {"estado": {"$in": estados_pendientes}, "anulada": False},
                          sort=[("fecha", -1)], limit=50)
    if not guias:
        st.info("✅ No hay guías pendientes de recepción.")
        return

    for g in guias:
        if isinstance(g.get("numero_guia"), int):
            g["numero_guia"] = str(g["numero_guia"])

    cols = ["numero_guia", "tienda_destino", "fecha_emision",
            "estado", "total_prendas", "usuario_genera"]
    data = [{c: g.get(c, "") for c in cols} for g in guias]
    df_pend = pd.DataFrame(data)

    m1, m2, m3 = st.columns(3)
    m1.metric("Pendientes", len(guias))
    m2.metric("Total prendas", f"{sum(g.get('total_prendas', 0) for g in guias):,}")
    m3.metric("Tiendas involucradas",
              len(set(g.get("tienda_destino", "") for g in guias)))

    st.dataframe(df_pend, use_container_width=True)

    st.divider()
    st.subheader("Iniciar Recepción")
    opciones = {g["numero_guia"]: g for g in guias}
    sel_guia = st.selectbox("Selecciona guía", list(opciones.keys()),
                             key="sel_pendiente")
    if sel_guia and st.button("📦 Iniciar Proceso de Recepción",
                              type="primary", use_container_width=True,
                              key="btn_iniciar_rec"):
        st.session_state["guia_recepcion_activa"] = sel_guia

    if "guia_recepcion_activa" in st.session_state:
        doc = opciones.get(st.session_state["guia_recepcion_activa"])
        if doc:
            st.divider()
            _proceso_recepcion_completo(doc)


def _panel_historial() -> None:
    st.subheader("📜 Historial de Recepciones")
    
    all_users = local_db.db.guias.distinct("usuario_genera")
    all_users = [u for u in all_users if u]
    all_users.sort()
    user_filter = st.selectbox("Filtrar por usuario generador", 
                               options=["Todos"] + all_users,
                               key="hist_user_filter")
    
    estados_completados = [
        EstadoGuia.RECIBIDA_CONFORME,
        EstadoGuia.RECIBIDA_NOVEDAD,
        EstadoGuia.CONCILIADA,
        EstadoGuia.CERRADA,
    ]
    query = {"estado": {"$in": estados_completados}}
    if user_filter != "Todos":
        query["usuario_genera"] = user_filter
        
    guias = local_db.find("guias", query, sort=[("fecha", -1)], limit=100)
    if not guias:
        st.info("No hay recepciones completadas con el filtro seleccionado.")
        return

    conformes  = sum(1 for g in guias if g.get("estado") == EstadoGuia.RECIBIDA_CONFORME)
    con_novedad = len(guias) - conformes

    k1, k2, k3 = st.columns(3)
    k1.metric("Total recepcionadas", len(guias))
    k2.metric("Conformes", conformes,
              delta=f"{conformes/len(guias)*100:.0f}%" if guias else "0%")
    k3.metric("Con novedad", con_novedad)

    data = []
    for g in guias:
        rec = g.get("recepcion", {})
        diffs = rec.get("diferencias", {})
        diferencia_neta = diffs.get("diferencia_neta", 0)
        if diferencia_neta > 0:
            dif_str = f"-{diferencia_neta}"
        elif diferencia_neta < 0:
            dif_str = f"+{abs(diferencia_neta)}"
        else:
            dif_str = "0"
        data.append({
            "N° Guía":        str(g.get("numero_guia", "")),
            "Tienda":         g.get("tienda_destino", ""),
            "Estado":         g.get("estado", ""),
            "Fecha Recep.":   str(rec.get("fecha_recepcion", ""))[:16],
            "Receptor":       rec.get("usuario_recepcion", ""),
            "Diferencias":    "Sí" if rec.get("diferencias_detectadas") else "No",
            "Diferencia neta": dif_str,
            "Total prendas":  g.get("total_prendas", 0),
        })
    df_principal = pd.DataFrame(data)
    st.dataframe(df_principal, use_container_width=True)

    # Exportación a Excel con dos hojas
    rows_detalle = []
    for g in guias:
        numero_guia = str(g.get("numero_guia", ""))
        tienda = g.get("tienda_destino", "")
        rec = g.get("recepcion", {})
        items_rec = rec.get("items_received", [])
        if not items_rec:
            rows_detalle.append({
                "N° Guía": numero_guia,
                "Tienda": tienda,
                "Código": "SIN_DETALLE",
                "Descripción": "No se registró detalle por ítem",
                "Estilo": "",
                "Esperado": g.get("total_prendas", 0),
                "Recibido": rec.get("diferencias", {}).get("total_recibido", 0),
                "Diferencia": rec.get("diferencias", {}).get("diferencia_neta", 0),
                "Estado Item": "",
            })
        else:
            for it in items_rec:
                esperado = it.get("cantidad_esperada", 0)
                recibido = it.get("cantidad_recibida", 0)
                diferencia = recibido - esperado
                rows_detalle.append({
                    "N° Guía": numero_guia,
                    "Tienda": tienda,
                    "Código": it.get("codigo", ""),
                    "Descripción": it.get("descripcion", ""),
                    "Estilo": it.get("estilo", ""),
                    "Esperado": esperado,
                    "Recibido": recibido,
                    "Diferencia": diferencia,
                    "Estado Item": it.get("estado_item", ""),
                })
    df_detalle = pd.DataFrame(rows_detalle)
    
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_principal.to_excel(w, index=False, sheet_name="Resumen")
        if not df_detalle.empty:
            df_detalle.to_excel(w, index=False, sheet_name="Detalle_Items")
    st.download_button(
        "📥 Exportar Historial Excel",
        buf.getvalue(),
        "historial_recepciones.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.divider()
    st.subheader("Detalle de Recepción")
    opciones_hist = {str(g.get("numero_guia", "")): g for g in guias}
    sel_h = st.selectbox("Ver detalle de guía", list(opciones_hist.keys()),
                         key="sel_historial")
    doc_h = opciones_hist.get(sel_h)
    if doc_h:
        rec_h = doc_h.get("recepcion", {})
        st.markdown(f"**Estado:** {doc_h.get('estado')}")
        st.markdown(f"**Fecha recepción:** {str(rec_h.get('fecha_recepcion', ''))[:16]}")
        st.markdown(f"**Receptor:** {rec_h.get('usuario_recepcion', '')}")
        st.markdown(f"**Observaciones:** {rec_h.get('observaciones', 'Ninguna')}")

        diffs = rec_h.get("diferencias", {})
        if diffs and diffs.get("tiene_diferencias"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Esperado", diffs.get("total_esperado", 0))
            c2.metric("Recibido", diffs.get("total_recibido", 0))
            c3.metric("Diferencia", diffs.get("diferencia_neta", 0))

        items_recibidos = rec_h.get("items_received", [])
        if items_recibidos:
            st.markdown("**Detalle de productos recibidos:**")
            detalle_rows = []
            for it in items_recibidos:
                esperado = it.get("cantidad_esperada", 0)
                recibido = it.get("cantidad_recibida", 0)
                diferencia = recibido - esperado
                detalle_rows.append({
                    "Código": it.get("codigo", ""),
                    "Estilo": it.get("estilo", ""),
                    "Descripción": it.get("descripcion", ""),
                    "Esperado": esperado,
                    "Recibido": recibido,
                    "Diferencia": f"{diferencia:+d}" if diferencia != 0 else "0",
                    "Estado": it.get("estado_item", ""),
                })
            df_detalle_rec = pd.DataFrame(detalle_rows)
            st.dataframe(df_detalle_rec, use_container_width=True)
        else:
            st.info("No hay detalle de ítems registrado para esta recepción.")

        inc_h = doc_h.get("incidencias", [])
        if inc_h:
            st.markdown("**Incidencias:**")
            for inc in inc_h:
                sev = {"ALTA": "🔴", "MEDIA": "🟡", "BAJA": "🟢"}.get(inc.get("severidad", ""), "⚪")
                st.markdown(f"{sev} **{inc.get('tipo')}** — {inc.get('descripcion')}")

        with st.expander("📅 Timeline"):
            _render_timeline_mini(doc_h.get("timeline", []), max_items=10)


# ============================================================================
# ENTRY POINT
# ============================================================================

def show_recepcion_tienda():
    set_module_background("recepcion")
    try:
        load_css()
    except Exception:
        pass

    st.markdown(
        '<div style="text-align:center;">'
        '<div style="font-size:2rem;font-weight:800;color:#0033A0;">AEROPOSTALE</div>'
        '<div style="font-size:1rem;color:#475569;">Sistema de Recepción Logística</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    guia_str  = st.query_params.get("guia", "")
    trans_str = st.query_params.get("transferencia", "")

    if guia_str:
        guia_doc = local_db.find_one("guias", {"numero_guia": str(guia_str)})
        if not guia_doc:
            try:
                guia_doc = local_db.find_one("guias", {"numero_guia": int(guia_str)})
            except (ValueError, TypeError):
                pass
        if guia_doc:
            if isinstance(guia_doc.get("numero_guia"), int):
                guia_doc["numero_guia"] = str(guia_doc["numero_guia"])
            if trans_str:
                st.caption(f"Transferencia detectada en QR: **{trans_str}**")
            _proceso_recepcion_completo(guia_doc)
        else:
            st.error(f"La guía **{guia_str}** no fue encontrada en el sistema.")
        return

    tab1, tab2, tab3 = st.tabs([
        "📋 Pendientes",
        "🔍 Buscar Guía",
        "📜 Historial",
    ])

    with tab1:
        _panel_guias_pendientes()
    with tab2:
        _panel_busqueda_manual()
    with tab3:
        _panel_historial()

    if st.session_state.get("role") == "Administrador":
        st.divider()
        _panel_admin()
