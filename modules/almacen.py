# MODIFIED: 2026-05-21 - Módulo de Gestión de Almacén/Bodega
"""
Módulo de Gestión de Almacén - Aeropostale ERP
- Layout visual de bodega (zonas A, B, C)
- Asignación de ubicaciones a productos
- Picking list para preparación de pedidos
- Conteo cíclico calendarizado
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
from database.manager import local_db
from utils.ui import add_back_button, show_module_header
import random

# =============================================================================
# CONSTANTES
# =============================================================================
COLECCION_UBICACIONES = "ubicaciones_bodega"
COLECCION_CONTEO = "conteo_ciclico"
COLECCION_PICKING = "picking_list"

ZONAS_BODEGA = {
    "A": {"nombre": "Zona A - Alta Rotación", "color": "#CF0A2C", "desc": "Productos con mayor salida, cerca del área de despacho"},
    "B": {"nombre": "Zona B - Rotación Media", "color": "#f59e0b", "desc": "Productos con rotación moderada"},
    "C": {"nombre": "Zona C - Baja Rotación", "color": "#10b981", "desc": "Productos de baja rotación, stock de seguridad"},
}

PASILLOS = {"A": 4, "B": 3, "C": 3}
ESTANTES = {"A": 6, "B": 4, "C": 4}
NIVELES = {"A": 4, "B": 3, "C": 2}


def _generar_ubicaciones_ejemplo():
    """Genera ubicaciones de ejemplo si no existen."""
    if local_db.count(COLECCION_UBICACIONES) > 0:
        return
    ubicaciones = []
    for zona in ["A", "B", "C"]:
        for pasillo in range(1, PASILLOS[zona] + 1):
            for estante in range(1, ESTANTES[zona] + 1):
                for nivel in range(1, NIVELES[zona] + 1):
                    codigo = f"{zona}-{pasillo:02d}-{estante:02d}-{nivel:02d}"
                    ubicaciones.append({
                        "codigo_ubicacion": codigo,
                        "zona": zona,
                        "pasillo": pasillo,
                        "estante": estante,
                        "nivel": nivel,
                        "ocupada": False,
                        "producto_asignado": None,
                        "codigo_estilo": None,
                        "capacidad_max": random.choice([50, 100, 200, 500]),
                        "stock_actual": 0,
                    })
    local_db.insert(COLECCION_UBICACIONES, {"_batch": True, "ubicaciones": ubicaciones})
    # Insert individual
    for u in ubicaciones:
        local_db.insert(COLECCION_UBICACIONES, u)


def _layout_bodega():
    """Muestra el layout visual de la bodega."""
    st.markdown("### 🏗️ Layout de Bodega")

    # Resumen por zona
    cols = st.columns(3)
    for i, (zona, info) in enumerate(ZONAS_BODEGA.items()):
        with cols[i]:
            ubi_zona = local_db.find(COLECCION_UBICACIONES, {"zona": zona})
            total = len(ubi_zona)
            ocupadas = sum(1 for u in ubi_zona if u.get("ocupada"))
            pct_ocup = (ocupadas / total * 100) if total > 0 else 0
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-left:4px solid {info['color']};border-radius:10px;padding:16px;margin-bottom:10px;">
                <div style="font-size:1.1rem;font-weight:700;color:{info['color']};">{info['nombre']}</div>
                <div style="font-size:.8rem;color:#94a3b8;margin:4px 0;">{info['desc']}</div>
                <div style="font-size:1.5rem;font-weight:700;color:#f8fafc;">{ocupadas}/{total}</div>
                <div style="font-size:.8rem;color:#94a3b8;">Ubicaciones ocupadas ({pct_ocup:.0f}%)</div>
                <div style="height:4px;background:rgba(255,255,255,.1);border-radius:2px;margin-top:8px;">
                    <div style="height:4px;width:{pct_ocup:.0f}%;background:{info['color']};border-radius:2px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### 🗺️ Mapa de la Bodega")
    zona_seleccionada = st.selectbox("Seleccionar zona", list(ZONAS_BODEGA.keys()), format_func=lambda z: ZONAS_BODEGA[z]["nombre"])
    if zona_seleccionada:
        ubi_zona = local_db.find(COLECCION_UBICACIONES, {"zona": zona_seleccionada})
        if not ubi_zona:
            st.info("No hay ubicaciones configuradas para esta zona.")
            return

        df_zona = pd.DataFrame(ubi_zona)
        pasillos_disponibles = sorted(df_zona["pasillo"].unique())

        for pasillo in pasillos_disponibles:
            st.markdown(f"**Pasillo {pasillo}**")
            df_pasillo = df_zona[df_zona["pasillo"] == pasillo].sort_values(["estante", "nivel"])
            cols_pasillo = st.columns(ESTANTES[zona_seleccionada])
            for estante in sorted(df_pasillo["estante"].unique()):
                with cols_pasillo[estante - 1]:
                    df_est = df_pasillo[df_pasillo["estante"] == estante]
                    niveles_html = ""
                    for _, row in df_est.iterrows():
                        ocupado = row.get("ocupada", False)
                        color = ZONAS_BODEGA[zona_seleccionada]["color"] if ocupado else "#334155"
                        label = row["codigo_ubicacion"]
                        niveles_html += f'<div style="background:{color}30;border:1px solid {color};border-radius:4px;padding:2px 4px;margin:1px 0;font-size:.65rem;color:#e2e8f0;text-align:center;">{label}</div>'
                    st.markdown(f'<div style="background:rgba(255,255,255,.03);border-radius:8px;padding:6px;text-align:center;"><div style="font-size:.7rem;color:#94a3b8;margin-bottom:2px;">Estante {estante}</div>{niveles_html}</div>', unsafe_allow_html=True)


def _asignar_ubicacion():
    """Asigna un producto a una ubicación de bodega."""
    st.markdown("### 📦 Asignar Producto a Ubicación")

    ubicaciones_libres = local_db.find(COLECCION_UBICACIONES, {"ocupada": False})
    inventario = local_db.find("inventario", {"carga_activa": True})

    if not ubicaciones_libres:
        st.warning("No hay ubicaciones libres disponibles.")
        return

    if not inventario:
        st.warning("No hay inventario activo. Carga un archivo en Control de Inventario primero.")
        return

    col1, col2 = st.columns(2)
    with col1:
        # Seleccionar producto
        df_inv = pd.DataFrame(inventario)
        if "codigo_estilo" in df_inv.columns and "producto" in df_inv.columns:
            df_inv["display"] = df_inv["codigo_estilo"].astype(str) + " - " + df_inv["producto"].astype(str)
        elif "codigo_estilo" in df_inv.columns:
            df_inv["display"] = df_inv["codigo_estilo"].astype(str)
        else:
            df_inv["display"] = df_inv.index.astype(str)

        producto_sel = st.selectbox("Seleccionar producto", df_inv["display"].tolist(), key="asignar_producto")
        producto_row = df_inv[df_inv["display"] == producto_sel].iloc[0]

    with col2:
        # Seleccionar ubicación
        df_ubi = pd.DataFrame(ubicaciones_libres)
        df_ubi["display"] = df_ubi["codigo_ubicacion"] + " (Cap: " + df_ubi["capacidad_max"].astype(str) + ")"
        ubi_sel = st.selectbox("Seleccionar ubicación", df_ubi["display"].tolist(), key="asignar_ubi")
        ubi_row = df_ubi[df_ubi["display"] == ubi_sel].iloc[0]

    cantidad = st.number_input("Cantidad a almacenar", min_value=1, max_value=int(ubi_row["capacidad_max"]), value=min(50, int(ubi_row["capacidad_max"])))

    if st.button("✅ Asignar Ubicación", type="primary"):
        # Actualizar ubicación
        local_db.update(COLECCION_UBICACIONES,
            {"codigo_ubicacion": ubi_row["codigo_ubicacion"]},
            {
                "ocupada": True,
                "producto_asignado": producto_row.get("producto", producto_row.get("codigo_estilo", "")),
                "codigo_estilo": producto_row.get("codigo_estilo", ""),
                "stock_actual": cantidad,
            }
        )
        st.success(f"✅ Producto asignado a {ubi_row['codigo_ubicacion']}")
        st.rerun()

    # Productos ya asignados
    st.markdown("### 📋 Productos Asignados")
    asignados = local_db.find(COLECCION_UBICACIONES, {"ocupada": True})
    if asignados:
        df_asig = pd.DataFrame(asignados)
        cols_show = ["codigo_ubicacion", "zona", "producto_asignado", "stock_actual", "capacidad_max"]
        cols_show = [c for c in cols_show if c in df_asig.columns]
        st.dataframe(df_asig[cols_show], use_container_width=True)
    else:
        st.info("No hay productos asignados aún.")


def _generar_picking_list():
    """Genera lista de picking para preparación de pedidos."""
    st.markdown("### 📋 Picking List - Preparación de Pedidos")

    guias_pendientes = local_db.find("guias", {"estado": {"$ne": "DESPACHADA"}, "anulada": {"$ne": True}})
    if not guias_pendientes:
        st.info("No hay guías pendientes de preparación.")
        return

    df_guias = pd.DataFrame(guias_pendientes)
    st.dataframe(df_guias[["numero_guia", "tienda_destino", "fecha", "estado"]], use_container_width=True)

    guia_sel = st.selectbox("Seleccionar guía para picking", df_guias["numero_guia"].tolist() if "numero_guia" in df_guias.columns else df_guias.index.tolist())
    if st.button("🔄 Generar Picking List", type="primary"):
        with st.spinner("Generando lista de picking..."):
            picking_items = []
            # Buscar productos asignados en bodega
            ubicaciones = local_db.find(COLECCION_UBICACIONES, {"ocupada": True})
            for u in ubicaciones:
                if u.get("stock_actual", 0) > 0:
                    picking_items.append({
                        "codigo_ubicacion": u["codigo_ubicacion"],
                        "zona": u["zona"],
                        "producto": u.get("producto_asignado", ""),
                        "codigo_estilo": u.get("codigo_estilo", ""),
                        "stock_disponible": u.get("stock_actual", 0),
                        "cantidad_picar": min(u.get("stock_actual", 0), random.randint(1, 10)),
                        "estado": "PENDIENTE",
                    })

            if picking_items:
                df_picking = pd.DataFrame(picking_items)
                st.success(f"✅ Lista de picking generada con {len(picking_items)} items")
                st.dataframe(df_picking, use_container_width=True)

                # Orden de picking por zonas (priorizar Zona A primero)
                st.markdown("### 🗺️ Ruta Óptima de Picking")
                df_picking["zona_order"] = df_picking["zona"].map({"A": 0, "B": 1, "C": 2})
                df_picking = df_picking.sort_values(["zona_order", "codigo_ubicacion"])
                for _, row in df_picking.iterrows():
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:8px 12px;margin:4px 0;display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#e2e8f0;font-size:.9rem;">📍 {row['codigo_ubicacion']}</span>
                        <span style="color:#94a3b8;font-size:.8rem;">{row['producto'][:40]}</span>
                        <span style="color:#f8fafc;font-weight:700;">{row['cantidad_picar']} uds</span>
                    </div>
                    """, unsafe_allow_html=True)

                # Exportar
                csv = df_picking.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Picking List CSV", csv, "picking_list.csv", "text/csv")
            else:
                st.warning("No hay stock disponible en bodega para preparar pedidos.")


def _conteo_ciclico():
    """Calendarización y registro de conteos cíclicos."""
    st.markdown("### 📅 Conteo Cíclico Calendarizado")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Nuevo Conteo Programado**")
        with st.form("form_conteo"):
            zona = st.selectbox("Zona", list(ZONAS_BODEGA.keys()), format_func=lambda z: ZONAS_BODEGA[z]["nombre"])
            fecha_programada = st.date_input("Fecha programada", date.today() + timedelta(days=1))
            responsable = st.text_input("Responsable", value=st.session_state.get("username", ""))
            submit = st.form_submit_button("📅 Programar Conteo", type="primary")
            if submit:
                doc = {
                    "zona": zona,
                    "fecha_programada": fecha_programada.isoformat(),
                    "fecha_creacion": datetime.utcnow(),
                    "responsable": responsable,
                    "estado": "PENDIENTE",
                    "resultados": None,
                }
                local_db.insert(COLECCION_CONTEO, doc)
                st.success(f"✅ Conteo programado para Zona {zona} el {fecha_programada}")
                st.rerun()

    with col2:
        st.markdown("**Registrar Resultado de Conteo**")
        conteos_pendientes = local_db.find(COLECCION_CONTEO, {"estado": "PENDIENTE"})
        if not conteos_pendientes:
            st.info("No hay conteos pendientes.")
        else:
            conteo_sel = st.selectbox("Conteo pendiente", [f"{c.get('zona','?')} - {c.get('fecha_programada','?')} - {c.get('responsable','?')}" for c in conteos_pendientes])
            idx = [f"{c.get('zona','?')} - {c.get('fecha_programada','?')} - {c.get('responsable','?')}" for c in conteos_pendientes].index(conteo_sel)
            conteo = conteos_pendientes[idx]

            with st.form("form_resultado"):
                stock_fisico = st.number_input("Stock físico encontrado", min_value=0, value=0)
                stock_sistema = st.number_input("Stock en sistema", min_value=0, value=0)
                observaciones = st.text_area("Observaciones")
                if st.form_submit_button("✅ Registrar Resultado", type="primary"):
                    diferencia = stock_fisico - stock_sistema
                    local_db.update(COLECCION_CONTEO,
                        {"_id": conteo["_id"]},
                        {"$set": {
                            "estado": "COMPLETADO",
                            "resultados": {
                                "stock_fisico": stock_fisico,
                                "stock_sistema": stock_sistema,
                                "diferencia": diferencia,
                                "observaciones": observaciones,
                                "fecha_conteo": datetime.utcnow(),
                            }
                        }}
                    )
                    st.success(f"✅ Conteo registrado. Diferencia: {diferencia:+d} unidades")
                    st.rerun()

    # Historial de conteos
    st.markdown("### 📊 Historial de Conteos")
    todos_conteos = local_db.find(COLECCION_CONTEO, sort=[("fecha_creacion", -1)], limit=20)
    if todos_conteos:
        df_hist = pd.DataFrame(todos_conteos)
        st.dataframe(df_hist, use_container_width=True)

        # Gráfico de diferencias
        completados = [c for c in todos_conteos if c.get("estado") == "COMPLETADO" and c.get("resultados")]
        if completados:
            df_comp = pd.DataFrame([{
                "zona": c["zona"],
                "diferencia": c["resultados"].get("diferencia", 0),
            } for c in completados])
            fig = px.bar(df_comp, x="zona", y="diferencia", title="Diferencias por Zona (Conteo vs Sistema)",
                        color="diferencia", color_continuous_scale=["#10b981", "#f59e0b", "#ef4444"])
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(15,23,42,0)", plot_bgcolor="rgba(30,41,59,0.5)")
            st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_almacen():
    add_back_button(key="back_almacen")
    show_module_header("🏗️ Gestión de Almacén", "Layout de bodega, ubicaciones, picking y conteo cíclico")

    # Inicializar datos de ejemplo si no existen
    _generar_ubicaciones_ejemplo()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Layout de Bodega",
        "📦 Asignar Ubicaciones",
        "📋 Picking List",
        "📅 Conteo Cíclico",
    ])

    with tab1:
        _layout_bodega()

    with tab2:
        _asignar_ubicacion()

    with tab3:
        _generar_picking_list()

    with tab4:
        _conteo_ciclico()
