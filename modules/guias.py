"""
modules/guias.py — GENERACIÓN DE GUÍAS DE TRANSFERENCIA AEROPOSTALE
====================================================================
- Admin y Bodega (Andres, Luis, Jessica, Josue, Jhonny) crean guías
- Cada guía se registra en DB con tienda_destino, estado, items
- Automáticamente crea guía_pendiente en la colección guías_pendientes
- Permite ver guías creadas, filtrar por tienda, fecha
- Botón para Reemplazar (borrado controlado + nuevo insert) y Borrado Seguro (con auditoría)
- Solo usuarios con permiso "guias" pueden acceder
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import json

from utils.ui import add_back_button, show_module_header
from utils.roles import can_access, es_admin_o_bodega
from database.manager import local_db, registrar_auditoria, reemplazar_registro, borrado_seguro
from config.stores_data import TIENDAS_DATA

# =============================================================================
# CONSTANTES
# =============================================================================
COL_GUIAS = "guias"
COL_PENDIENTES = "guias_pendientes"

# =============================================================================
# GENERADOR DE NÚMERO DE GUÍA
# =============================================================================
def _generar_numero_guia(tienda_destino: str) -> str:
    """Genera número de guía incremental por tienda."""
    seq = local_db.find_one_and_update(
        "secuencia_guias",
        {"tienda": tienda_destino},
        {"$inc": {"secuencia": 1}},
        upsert=True
    )
    secuencia = seq.get("secuencia", 1) if seq else 1
    today = datetime.now().strftime("%Y%m%d")
    cod_tienda = tienda_destino[:3].upper()
    return f"FC-{today}-{cod_tienda}-{secuencia:04d}"


# =============================================================================
# SECCIÓN: CREAR NUEVA GUÍA
# =============================================================================
def _seccion_crear_guia():
    st.markdown("### ➕ Crear Nueva Guía de Transferencia")
    st.caption("Llena los datos para registrar una transferencia de productos a una tienda.")

    if not TIENDAS_DATA:
        st.warning("⚠️ No hay tiendas configuradas en stores_data.py")

    # Selector de tienda destino
    opciones_tienda = [t.get("Nombre de Tienda", t.get("nombre", "")) for t in TIENDAS_DATA]
    opciones_tienda = sorted([t for t in opciones_tienda if t])

    col1, col2 = st.columns(2)
    with col1:
        tienda_destino = st.selectbox("🏪 Tienda Destino", [""] + opciones_tienda, key="guia_tienda_destino")
    with col2:
        fecha_guia = st.date_input("📅 Fecha de Guía", value=date.today(), key="guia_fecha")

    # Items de la guía
    st.markdown("#### 🧾 Items de la Transferencia")
    st.caption("Agrega los productos con estilo, color, talla y cantidad.")

    if "guia_items" not in st.session_state:
        st.session_state.guia_items = []

    # Formulario de item
    with st.expander("✏️ Agregar Producto", expanded=True):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        with c1:
            producto = st.text_input("Producto / Estilo", key="guia_prod")
        with c2:
            color = st.text_input("Color", key="guia_color")
        with c3:
            talla = st.text_input("Talla", key="guia_talla")
        with c4:
            cantidad = st.number_input("Cant.", min_value=1, step=1, key="guia_cant")

        if st.button("➕ Agregar Item", key="btn_agregar_item_guia"):
            if producto and cantidad > 0:
                st.session_state.guia_items.append({
                    "producto": producto.strip(),
                    "color": color.strip(),
                    "talla": talla.strip() or "ÚNICA",
                    "cantidad": int(cantidad),
                })
                st.success(f"✅ {producto} ({color}) x {cantidad}")
                st.rerun()
            else:
                st.warning("⚠️ Producto y cantidad son obligatorios")

    # Mostrar items agregados
    if st.session_state.guia_items:
        df_items = pd.DataFrame(st.session_state.guia_items)
        st.dataframe(df_items, use_container_width=True)

        col_a, col_b = st.columns([1, 5])
        with col_a:
            if st.button("🗑️ Limpiar Items", key="btn_limpiar_items_guia"):
                st.session_state.guia_items = []
                st.rerun()

        # Botón final: guardar guía
        with col_b:
            if st.button("📦 Guardar Guía y Enviar a Tienda", type="primary", key="btn_guardar_guia"):
                if not tienda_destino:
                    st.error("❌ Selecciona una tienda destino")
                elif not st.session_state.guia_items:
                    st.error("❌ Agrega al menos un item")
                else:
                    _guardar_guia(tienda_destino, fecha_guia, st.session_state.guia_items)
                    st.session_state.guia_items = []
                    st.balloons()
                    st.rerun()
    else:
        st.info("ℹ️ No hay productos agregados aún.")


def _guardar_guia(tienda_destino: str, fecha_guia: date, items: list):
    """Guarda la guía en la BD y crea guía_pendiente para la tienda."""
    numero_guia = _generar_numero_guia(tienda_destino)
    usuario = st.session_state.get("username", "admin")
    now = datetime.now()

    total_prendas = sum(item["cantidad"] for item in items)

    guia_doc = {
        "numero_guia": numero_guia,
        "tienda_destino": tienda_destino,
        "fecha_guia": fecha_guia.isoformat(),
        "fecha_creacion": now.isoformat(),
        "usuario_creador": usuario,
        "items": items,
        "total_prendas": total_prendas,
        "estado": "PENDIENTE",  # Pendiente → Recibida (cuando tienda recibe)
        "fecha_recepcion": None,
        "usuario_recepcion": None,
        "notas": "",
    }

    guia_id = local_db.insert(COL_GUIAS, guia_doc)

    # Crear guía pendiente para recepción
    pendiente_doc = {
        "numero_guia": numero_guia,
        "guia_id": str(guia_id),
        "tienda_destino": tienda_destino,
        "fecha_creacion": now.isoformat(),
        "estado": "PENDIENTE_RECEPCION",
        "visible": True,
    }
    local_db.insert(COL_PENDIENTES, pendiente_doc)

    # Alerta de notificación
    local_db.insert("notificaciones", {
        "mensaje": f"📦 Nueva guía {numero_guia} para {tienda_destino} — {total_prendas} prendas",
        "fecha": now.isoformat(),
        "modulo": "guias",
        "tipo": "guia_creada",
        "leida": False,
    })

    registrar_auditoria("CREAR_GUIA", "guias",
                       f"Usuario {usuario} creó guía {numero_guia} para {tienda_destino} ({total_prendas} prendas)")

    st.success(f"✅ **Guía {numero_guia}** creada exitosamente para {tienda_destino}")
    st.info(f"📦 {total_prendas} prendas en {len(items)} items")


# =============================================================================
# SECCIÓN: VER GUÍAS CREADAS
# =============================================================================
def _seccion_ver_guias():
    st.markdown("### 📋 Guías de Transferencia")

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        estado_filter = st.selectbox("Estado", ["Todas", "PENDIENTE", "RECIBIDA"], key="guias_filtro_estado")
    with col2:
        opciones_tienda = [""] + sorted([t.get("Nombre de Tienda", t.get("nombre", "")) for t in TIENDAS_DATA if t.get("Nombre de Tienda", t.get("nombre", ""))])
        tienda_filter = st.selectbox("Tienda Destino", opciones_tienda, key="guias_filtro_tienda")
    with col3:
        busqueda = st.text_input("🔍 Buscar N° Guía", key="guias_buscar")

    # Construir query
    query = {}
    if estado_filter != "Todas":
        query["estado"] = estado_filter
    if tienda_filter:
        query["tienda_destino"] = tienda_filter
    if busqueda:
        query["numero_guia"] = {"$regex": busqueda, "$options": "i"}

    # Cargar guías (limit 200 para no saturar)
    guias = local_db.find(COL_GUIAS, query, sort=[("fecha_creacion", -1)], limit=200)

    if guias:
        df = pd.DataFrame(guias)
        cols_show = ["numero_guia", "tienda_destino", "fecha_guia", "estado", "total_prendas", "usuario_creador", "fecha_recepcion"]
        cols_exist = [c for c in cols_show if c in df.columns]

        rename_map = {
            "numero_guia": "N° Guía",
            "tienda_destino": "Tienda",
            "fecha_guia": "Fecha",
            "estado": "Estado",
            "total_prendas": "Prendas",
            "usuario_creador": "Creador",
            "fecha_recepcion": "Recibida",
        }
        df_show = df[cols_exist].copy()
        for col in ["fecha_guia", "fecha_recepcion", "fecha_creacion"]:
            if col in df_show.columns:
                df_show[col] = df_show[col].astype(str).str[:10]

        df_show = df_show.rename(columns=rename_map)
        st.dataframe(df_show, use_container_width=True)

        # Selección de guía para ver detalle
        if "_id" in df.columns:
            opciones_detalle = {str(i): row["numero_guia"] for i, row in df.iterrows()}
            selected = st.selectbox("🔍 Selecciona guía para ver detalle",
                                    options=list(opciones_detalle.keys()),
                                    format_func=lambda x: opciones_detalle[x],
                                    key="guias_select_detalle")
            if selected:
                idx = int(selected.split("_")[0]) if "_" in selected else int(selected)
                guia_idx = int(selected)
                if guia_idx < len(guias):
                    _mostrar_detalle_guia(guias[guia_idx])
    else:
        st.info("ℹ️ No hay guías registradas")


def _mostrar_detalle_guia(guia: dict):
    """Muestra detalle completo de una guía con acciones."""
    with st.expander(f"📄 Detalle: {guia.get('numero_guia', '')}", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**N° Guía:** {guia.get('numero_guia', 'N/A')}")
            st.markdown(f"**Tienda Destino:** {guia.get('tienda_destino', 'N/A')}")
            st.markdown(f"**Estado:** {'✅ RECIBIDA' if guia.get('estado') == 'RECIBIDA' else '⏳ PENDIENTE'}")
        with c2:
            st.markdown(f"**Fecha Guía:** {str(guia.get('fecha_guia', ''))[:10]}")
            st.markdown(f"**Creador:** {guia.get('usuario_creador', 'N/A')}")
            st.markdown(f"**Total Prendas:** {guia.get('total_prendas', 0)}")

        # Items
        items = guia.get("items", [])
        if items:
            st.markdown("#### 📦 Items")
            df_items = pd.DataFrame(items)
            st.dataframe(df_items, use_container_width=True)
        else:
            st.info("Sin items registrados")

        # Notas
        notas = guia.get("notas", "")
        if notas:
            st.markdown(f"**Notas:** {notas}")

        # Acciones: Reemplazar y Borrar (solo Admin/Bodega)
        if es_admin_o_bodega():
            st.markdown("---")
            st.markdown("#### ⚙️ Acciones Avanzadas")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Reemplazar Guía", key=f"reemplazar_{guia.get('numero_guia')}", type="secondary"):
                    # Marcar par reemplazo en sesión
                    st.session_state["guia_reemplazar"] = guia.get("numero_guia")
                    st.rerun()
            with col_b:
                if st.button("🗑️ Borrado Seguro", key=f"borrar_{guia.get('numero_guia')}", type="secondary"):
                    num_guia = guia.get("numero_guia", "")
                    borrado_seguro(COL_GUIAS, {"numero_guia": num_guia})
                    # También limpiar pendiente
                    local_db.delete(COL_PENDIENTES, {"numero_guia": num_guia})
                    st.success(f"🗑️ Guía {num_guia} eliminada (auditada)")
                    registrar_auditoria("BORRAR_GUIA_COMPLETA", "guias",
                                       f"Usuario {st.session_state.get('username')} borró guía {num_guia}")
                    st.rerun()


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_guias():
    """Punto de entrada del módulo Guías de Transferencia."""
    if not can_access("guias"):
        st.error("⛔ No tienes permisos para acceder a Guías")
        return

    add_back_button(key="back_guias")
    show_module_header("📦 Guías de Transferencia", "Generación y gestión de transferencias a tiendas")

    tab1, tab2 = st.tabs(["📝 Crear Guía", "📋 Ver Guías"])
    with tab1:
        _seccion_crear_guia()
    with tab2:
        _seccion_ver_guias()
