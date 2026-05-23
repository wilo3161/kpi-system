"""
modules/recepcion.py — RECEPCIÓN DE GUÍAS POR TIENDA AEROPOSTALE
====================================================================
- Tienda ve SOLO sus guías pendientes (protegido por validar_permiso_tienda)
- Admin y Bodega ven todas las guías pendientes
- Al recibir: cambia estado a RECIBIDA, registra fecha/hora/usuario
- Lanza alerta automática al recibir
- Carga optimizada con paginación (lazy)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

from utils.ui import add_back_button, show_module_header
from utils.roles import can_access, validar_permiso_tienda, get_user_store, es_admin_o_bodega
from database.manager import local_db, registrar_auditoria

# =============================================================================
# CONSTANTES
# =============================================================================
COL_GUIAS = "guias"
COL_PENDIENTES = "guias_pendientes"
COL_NOTIFICACIONES = "notificaciones"

# =============================================================================
# SECCIÓN PRINCIPAL: Guías Pendientes de Recepción
# =============================================================================
def _seccion_guias_pendientes():
    st.markdown("### 📬 Guías Pendientes de Recepción")
    st.caption("Selecciona una guía para recibir sus productos en tu tienda.")

    usuario = st.session_state.get("username", "")
    role = st.session_state.get("role", "Tienda")
    tienda_usuario = get_user_store()

    # Query base
    if es_admin_o_bodega():
        # Admin/Bodega ven todas las pendientes
        guias_pendientes = local_db.find(
            COL_PENDIENTES,
            {"estado": "PENDIENTE_RECEPCION", "visible": True},
            sort=[("fecha_creacion", -1)]
        )
    else:
        # Tienda solo ve sus pendientes
        guias_pendientes = local_db.find(
            COL_PENDIENTES,
            {"tienda_destino": tienda_usuario, "estado": "PENDIENTE_RECEPCION", "visible": True},
            sort=[("fecha_creacion", -1)]
        )

    if not guias_pendientes:
        st.info("✅ No hay guías pendientes de recepción.")
        return

    # Mostrar tabla de pendientes
    df_pend = pd.DataFrame(guias_pendientes)
    cols_show = ["numero_guia", "tienda_destino", "fecha_creacion"]
    cols_exist = [c for c in cols_show if c in df_pend.columns]

    rename_map = {
        "numero_guia": "N° Guía",
        "tienda_destino": "Tienda Destino",
        "fecha_creacion": "Fecha Creación",
    }
    df_show = df_pend[cols_exist].copy()
    if "fecha_creacion" in df_show.columns:
        df_show["fecha_creacion"] = df_show["fecha_creacion"].astype(str).str[:19]
    df_show = df_show.rename(columns=rename_map)
    st.dataframe(df_show, use_container_width=True)

    # Seleccionar guía para recibir
    st.markdown("#### 🔍 Selecciona guía para procesar recepción")
    opciones = {str(i): p.get("numero_guia", f"Guía #{i}") for i, p in enumerate(guias_pendientes)}
    selected = st.selectbox("", options=list(opciones.keys()), format_func=lambda x: opciones[x],
                            key="recepcion_select")
    if selected:
        idx = int(selected)
        if idx < len(guias_pendientes):
            _mostrar_detalle_recepcion(guias_pendientes[idx])


def _mostrar_detalle_recepcion(pendiente: dict):
    """Muestra detalle de la guía pendiente y permite recibir."""
    num_guia = pendiente.get("numero_guia", "N/A")
    guia_id = pendiente.get("guia_id", "")

    # Obtener guía completa
    guia_doc = None
    if guia_id:
        from bson import ObjectId
        try:
            guia_doc = local_db.find_one(COL_GUIAS, {"_id": ObjectId(guia_id)})
        except Exception:
            guia_doc = local_db.find_one(COL_GUIAS, {"numero_guia": num_guia})
    else:
        guia_doc = local_db.find_one(COL_GUIAS, {"numero_guia": num_guia})

    if not guia_doc:
        st.warning("⚠️ No se encontró la guía completa. Contacta al administrador.")
        return

    # Validar permiso de tienda
    if not es_admin_o_bodega():
        if not validar_permiso_tienda(guia_doc):
            st.error("⛔ No autorizado: esta guía no pertenece a tu tienda")
            return

    st.markdown(f"#### 📄 Detalle: {num_guia}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🏪 Tienda", guia_doc.get("tienda_destino", "N/A"))
    with c2:
        st.metric("📦 Prendas", guia_doc.get("total_prendas", 0))
    with c3:
        st.metric("📅 Fecha", str(guia_doc.get("fecha_guia", ""))[:10])

    # Mostrar items
    items = guia_doc.get("items", [])
    if items:
        st.markdown("#### 📦 Items de la Transferencia")
        df_items = pd.DataFrame(items)
        st.dataframe(df_items, use_container_width=True)
        total = sum(item.get("cantidad", 0) for item in items)
        st.caption(f"**Total prendas a recibir: {total}**")
    else:
        st.info("No hay items en esta guía")

    # Control de calidad / notas
    notas = st.text_area("📝 Notas de recepción (opcional)", key="notas_recepcion",
                         placeholder="Ej: 2 prendas con etiqueta dañada, 1 cambio de talla")

    # Botón para recibir
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("✅ Recibir Guía Completa", type="primary", key=f"recibir_{num_guia}"):
            _procesar_recepcion(guia_doc, pendiente, notas, "COMPLETA")
    with col_b:
        if st.button("⚠️ Recibir con Discrepancias", type="secondary", key=f"recibir_parcial_{num_guia}"):
            _procesar_recepcion(guia_doc, pendiente, notas, "PARCIAL")


def _procesar_recepcion(guia_doc: dict, pendiente: dict, notas: str, tipo_recepcion: str):
    """Procesa la recepción: actualiza estado, registra alerta, notifica."""
    num_guia = guia_doc.get("numero_guia", "N/A")
    usuario = st.session_state.get("username", "desconocido")
    tienda = guia_doc.get("tienda_destino", "N/A")
    now = datetime.now()

    # 1. Actualizar guía principal
    local_db.update(COL_GUIAS,
        {"numero_guia": num_guia},
        {
            "$set": {
                "estado": "RECIBIDA",
                "fecha_recepcion": now.isoformat(),
                "usuario_recepcion": usuario,
                "notas": notas,
                "tipo_recepcion": tipo_recepcion,
            }
        }
    )

    # 2. Marcar pendiente como recibida
    local_db.update(COL_PENDIENTES,
        {"numero_guia": num_guia},
        {
            "$set": {
                "estado": "RECIBIDA",
                "fecha_recepcion": now.isoformat(),
                "usuario_recepcion": usuario,
                "visible": False,
            }
        }
    )

    # 3. Lanzar alerta / notificación
    mensaje = (
        f"✅ Guía {num_guia} recepcionada por {usuario} en {tienda}"
        + (f" — Notas: {notas}" if notas else "")
        + (f" — ⚠️ Recepción parcial" if tipo_recepcion == "PARCIAL" else "")
    )
    local_db.insert(COL_NOTIFICACIONES, {
        "mensaje": mensaje,
        "fecha": now.isoformat(),
        "modulo": "recepcion",
        "tipo": "recepcion_completada",
        "leida": False,
        "numero_guia": num_guia,
        "tienda": tienda,
    })

    # 4. Auditoría
    registrar_auditoria("RECEPCION_GUIA", "recepcion",
                       f"Usuario {usuario} recibió guía {num_guia} en {tienda} ({tipo_recepcion})")

    st.success(f"✅ **Guía {num_guia} recibida exitosamente** en {tienda}")
    if tipo_recepcion == "PARCIAL":
        st.warning("⚠️ Se registró como recepción parcial. El admin debe revisar.")
    st.balloons()


# =============================================================================
# HISTORIAL DE RECEPCIONES
# =============================================================================
def _seccion_historial_recepciones():
    st.markdown("### 📜 Historial de Recepciones")
    st.caption("Guías que ya fueron recibidas.")

    tienda_usuario = get_user_store()
    es_admin = es_admin_o_bodega()

    if es_admin:
        guias_recibidas = local_db.find(
            COL_GUIAS,
            {"estado": "RECIBIDA"},
            sort=[("fecha_recepcion", -1)],
            limit=200
        )
    else:
        guias_recibidas = local_db.find(
            COL_GUIAS,
            {"tienda_destino": tienda_usuario, "estado": "RECIBIDA"},
            sort=[("fecha_recepcion", -1)],
            limit=200
        )

    if guias_recibidas:
        df = pd.DataFrame(guias_recibidas)
        cols_show = ["numero_guia", "tienda_destino", "fecha_guia", "total_prendas", "usuario_recepcion", "fecha_recepcion", "tipo_recepcion"]
        cols_exist = [c for c in cols_show if c in df.columns]

        rename_map = {
            "numero_guia": "N° Guía",
            "tienda_destino": "Tienda",
            "fecha_guia": "Fecha",
            "total_prendas": "Prendas",
            "usuario_recepcion": "Recibido por",
            "fecha_recepcion": "Recibida el",
            "tipo_recepcion": "Tipo",
        }
        df_show = df[cols_exist].copy()
        for col in ["fecha_guia", "fecha_recepcion"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].astype(str).str[:19]
        df_show = df_show.rename(columns=rename_map)
        st.dataframe(df_show, use_container_width=True)

        # Mostrar totales
        total_recibidas = len(guias_recibidas)
        total_prendas = sum(g.get("total_prendas", 0) for g in guias_recibidas)
        st.caption(f"📊 Total: {total_recibidas} guías recibidas, {total_prendas} prendas")
    else:
        st.info("ℹ️ No hay guías recibidas aún")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_recepcion():
    """Punto de entrada del módulo de Recepción."""
    if not can_access("recepcion"):
        st.error("⛔ No tienes permisos para acceder a Recepción")
        return

    add_back_button(key="back_recepcion")
    show_module_header("📬 Recepción de Guías", "Recibir y confirmar transferencias de productos")

    tab1, tab2 = st.tabs(["📬 Pendientes", "📜 Historial"])
    with tab1:
        _seccion_guias_pendientes()
    with tab2:
        _seccion_historial_recepciones()
