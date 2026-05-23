"""
modules/inventario.py — CONTROL DE INVENTARIO AEROPOSTALE (v2)
=====================================================================
- 3 pestañas: Buscar, Cargar Archivo (Admin), Historial
- Búsqueda con filtros por código estilo, producto, color, talla, rango cantidad
- Admin carga archivo Excel/CSV → se procesa y guarda en MongoDB
- Procesamiento inteligente: parsea producto→(base, color, talla)
- Exportación a Excel
- Gráficos de distribución
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import io

from utils.ui import add_back_button, show_module_header
from utils.common import sanitize_for_mongo, normalizar_texto
from utils.roles import can_access
from database.manager import local_db, guardar_historico
from services.data_processing import (
    parse_producto_color_talla, normalizar_color, orden_talla,
    clasificar_tipo_prenda, extraer_genero
)
import plotly.express as px

# =============================================================================
# CONSTANTES
# =============================================================================
COLECCION_INVENTARIO = "inventario"
ARCHIVOS_CARGADOS_COL = "inventario_uploads"

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def _identificar_columnas(df: pd.DataFrame) -> dict:
    """Identifica columnas clave en el DataFrame de inventario."""
    cols = {c: normalizar_texto(c) for c in df.columns}
    resultado = {
        "codigo_estilo": None, "codigo_barra": None, "producto": None,
        "color": None, "talla": None, "cantidad": None,
        "costo": None, "precio": None, "ubicacion": None, "categoria": None,
    }
    patrones = {
        "codigo_estilo": ["CODIGO", "ESTILO", "SKU", "COD", "CÓDIGO", "STYLE", "CODART"],
        "codigo_barra": ["BARRA", "BARCODE", "EAN", "UPC", "COD_BARRA"],
        "producto": ["PRODUCTO", "DESCRIPCION", "DESCRIPCIÓN", "DESC", "NOMBRE", "ARTICULO", "ITEM"],
        "color": ["COLOR", "COLOUR"],
        "talla": ["TALLA", "SIZE", "TAMAÑO"],
        "cantidad": ["CANTIDAD", "STOCK", "EXISTENCIA", "INVENTARIO", "QTY", "DISPONIBLE", "SALDO"],
        "costo": ["COSTO", "COST", "PRECIO COSTO", "VLR_UNIT"],
        "precio": ["PRECIO", "PRICE", "PVP", "VENTA"],
        "ubicacion": ["UBICACION", "UBICACIÓN", "BODEGA", "LOCATION", "ALMACEN"],
        "categoria": ["CATEGORIA", "CATEGORÍA", "CAT", "LINEA", "LÍNEA", "DEPARTAMENTO"],
    }
    for col_norm in cols.values():
        col_upper = col_norm.upper().strip()
        for clave, patrones_lista in patrones.items():
            for pat in patrones_lista:
                if pat.upper() in col_upper:
                    col_orig = [c for c, n in cols.items() if n == col_norm]
                    if col_orig and resultado[clave] is None:
                        resultado[clave] = col_orig[0]
                    break
    return resultado


def _procesar_archivo_inventario(df: pd.DataFrame) -> pd.DataFrame:
    """Procesa y normaliza el DataFrame de inventario."""
    cols = _identificar_columnas(df)
    df_out = df.copy()

    rename_map = {}
    for clave, col_orig in cols.items():
        if col_orig:
            rename_map[col_orig] = clave
    if rename_map:
        df_out = df_out.rename(columns=rename_map)

    # Parsear producto si no hay talla/color separados
    if not cols["talla"] and not cols["color"] and cols["producto"]:
        parsed = df_out["producto"].astype(str).apply(parse_producto_color_talla)
        df_out["producto_base"] = parsed.apply(lambda x: x[0])
        df_out["color"] = parsed.apply(lambda x: x[1] if x[1] else "")
        df_out["talla"] = parsed.apply(lambda x: x[2] if x[2] else "ÚNICA")
    elif cols["producto"]:
        df_out["producto_base"] = df_out["producto"].astype(str)
    else:
        df_out["producto_base"] = ""

    # Normalizar talla
    if "talla" in df_out.columns:
        df_out["talla_orden"] = df_out["talla"].apply(
            lambda x: orden_talla(str(x).strip()) if pd.notna(x) else 99
        )
        df_out["talla"] = df_out["talla"].fillna("ÚNICA").astype(str).str.strip()

    # Normalizar color
    if "color" in df_out.columns:
        color_col = cols["color"] or "color"
        if color_col in df_out.columns:
            df_out["color"] = df_out[color_col].fillna("").astype(str).apply(
                lambda x: normalizar_color(x.strip()) if x.strip() else ""
            )
    else:
        df_out["color"] = ""

    # Asegurar cantidad numérica
    if "cantidad" in df_out.columns:
        df_out["cantidad"] = pd.to_numeric(df_out["cantidad"], errors="coerce").fillna(0).astype(int)
    else:
        df_out["cantidad"] = 0

    # Costo y precio
    for col in ["costo", "precio"]:
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").fillna(0.0)
        else:
            df_out[col] = 0.0

    # Generar SKU compuesto
    if cols["codigo_estilo"]:
        df_out["codigo_estilo"] = df_out["codigo_estilo"].astype(str).str.strip()
        if "talla" in df_out.columns and "color" in df_out.columns:
            df_out["sku_compuesto"] = (
                df_out["codigo_estilo"] + "-" +
                df_out["color"].str.upper().str.replace(" ", "_") + "-" +
                df_out["talla"].str.upper()
            )
        else:
            df_out["sku_compuesto"] = df_out["codigo_estilo"]
    else:
        df_out["codigo_estilo"] = ""
        df_out["sku_compuesto"] = df_out["producto_base"].astype(str)

    # Código corto
    df_out["codigo_corto"] = df_out["codigo_estilo"].apply(
        lambda x: x.split("-")[0].strip() if "-" in x else x.split()[0] if x.strip() else ""
    )

    # Clasificar
    df_out["tipo_prenda"] = df_out["producto_base"].apply(
        lambda x: clasificar_tipo_prenda(x)[0] if x else "Otro"
    )
    df_out["tipo_abrev"] = df_out["producto_base"].apply(
        lambda x: clasificar_tipo_prenda(x)[1] if x else "OTRO"
    )
    df_out["genero"] = df_out["producto_base"].apply(
        lambda x: extraer_genero(x) if x else "UNISEX"
    )

    df_out["_procesado"] = datetime.utcnow().isoformat()
    return df_out


def _calcular_metricas(df: pd.DataFrame) -> dict:
    """Calcula métricas resumen del inventario."""
    return {
        "total_skus": int(len(df)),
        "total_unidades": int(df["cantidad"].sum()) if "cantidad" in df.columns else 0,
        "valor_total": float((df["cantidad"] * df["costo"]).sum()) if "costo" in df.columns else 0.0,
        "valor_venta": float((df["cantidad"] * df["precio"]).sum()) if "precio" in df.columns else 0.0,
        "skus_sin_stock": int((df["cantidad"] == 0).sum()) if "cantidad" in df.columns else 0,
        "tipo_prenda": df["tipo_prenda"].value_counts().to_dict() if "tipo_prenda" in df.columns else {},
        "genero": df["genero"].value_counts().to_dict() if "genero" in df.columns else {},
    }


# =============================================================================
# SECCIÓN ADMIN: Carga de Archivo
# =============================================================================
def _seccion_carga_archivo():
    """Panel exclusivo para administradores: carga de archivo stock."""
    if st.session_state.get("role") != "Administrador":
        st.info("🔒 Solo el Administrador puede cargar archivos de inventario.")
        return

    st.markdown("### 📤 Cargar Archivo de Stock Consolidado")
    st.caption("Sube el archivo Excel/CSV. Se procesará y guardará en BD.")

    uploaded_file = st.file_uploader(
        "Selecciona archivo (Excel o CSV)",
        type=["xlsx", "xls", "csv"],
        key="inv_upload"
    )
    if uploaded_file is not None:
        try:
            file_ext = uploaded_file.name.split(".")[-1].lower()
            if file_ext == "csv":
                df_raw = pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
            else:
                df_raw = pd.read_excel(uploaded_file, engine="openpyxl")

            st.success(f"✅ Leído: {uploaded_file.name} ({len(df_raw)} filas, {len(df_raw.columns)} columnas)")

            with st.expander("👁️ Vista previa", expanded=False):
                st.dataframe(df_raw.head(20), use_container_width=True)
                st.caption(f"Columnas: {', '.join(df_raw.columns.tolist())}")

            cols_detectadas = _identificar_columnas(df_raw)
            columnas_encontradas = {k: v for k, v in cols_detectadas.items() if v}
            if columnas_encontradas:
                st.info(f"📋 Columnas reconocidas: {', '.join(f'**{k}** → `{v}`' for k, v in columnas_encontradas.items())}")
            else:
                st.warning("⚠️ No se pudieron reconocer columnas automáticamente.")

            if st.button("📦 Procesar y Guardar", type="primary", key="btn_guardar_inv"):
                with st.spinner("Procesando..."):
                    df_procesado = _procesar_archivo_inventario(df_raw)
                    metricas = _calcular_metricas(df_procesado)
                    registros = sanitize_for_mongo(df_procesado.to_dict("records"))

                    # Metadata de carga
                    metadata = {
                        "archivo_nombre": uploaded_file.name,
                        "fecha_carga": datetime.utcnow(),
                        "usuario": st.session_state.get("username", "admin"),
                        "filas": len(registros),
                        "columnas": len(df_raw.columns),
                        "columnas_detectadas": columnas_encontradas,
                        "metricas": metricas,
                        "activo": True,
                    }

                    # Marcar cargas anteriores como inactivas
                    local_db.update(ARCHIVOS_CARGADOS_COL, {"activo": True}, {"$set": {"activo": False}})
                    carga_id = local_db.insert(ARCHIVOS_CARGADOS_COL, metadata)

                    # Reemplazar inventario activo
                    local_db.delete(COLECCION_INVENTARIO, {"carga_activa": True})
                    batch_size = 500
                    total = 0
                    for i in range(0, len(registros), batch_size):
                        batch = registros[i:i + batch_size]
                        for reg in batch:
                            reg["carga_activa"] = True
                            reg["carga_id"] = str(carga_id)
                            local_db.insert(COLECCION_INVENTARIO, reg)
                        total += len(batch)

                    # Guardar histórico
                    guardar_historico(
                        "control_inventario", "carga_archivo",
                        df_procesado, metricas,
                        uploaded_file.name, datetime.utcnow(),
                        st.session_state.get("username", "admin")
                    )

                    st.success(f"✅ **{total} registros** guardados.")
                    st.balloons()

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("📦 SKUs", f"{metricas['total_skus']:,}")
                    c2.metric("📊 Unidades", f"{metricas['total_unidades']:,}")
                    c3.metric("💲 Costo Total", f"${metricas['valor_total']:,.0f}")
                    c4.metric("💰 Venta Total", f"${metricas['valor_venta']:,.0f}")
        except Exception as e:
            st.error(f"❌ Error al procesar: {str(e)}")


# =============================================================================
# SECCIÓN: Buscar Inventario
# =============================================================================
def _seccion_busqueda():
    st.markdown("### 🔍 Buscar en Inventario")
    st.caption("Busca productos cargados en la base de datos.")

    col1, col2 = st.columns(2)
    with col1:
        busqueda = st.text_input("🔍 Buscar (estilo, producto, color, talla)", key="inv_buscar_input")
    with col2:
        min_stock = st.number_input("Stock mínimo", min_value=0, value=0, key="inv_min_stock")

    # Obtener datos con carga_activa
    query = {"carga_activa": True}
    if busqueda:
        busq_upper = busqueda.upper().strip()
        query["$or"] = [
            {"codigo_estilo": {"$regex": busq_upper, "$options": "i"}},
            {"producto_base": {"$regex": busq_upper, "$options": "i"}},
            {"color": {"$regex": busq_upper, "$options": "i"}},
            {"talla": {"$regex": busq_upper, "$options": "i"}},
            {"sku_compuesto": {"$regex": busq_upper, "$options": "i"}},
        ]
    if min_stock > 0:
        query["cantidad"] = {"$gte": min_stock}

    registros = local_db.find(COLECCION_INVENTARIO, query, limit=500)

    if registros:
        df = pd.DataFrame(registros)

        # Filtrar columnas para mostrar
        cols_show = ["codigo_estilo", "producto_base", "color", "talla", "cantidad", "costo", "precio"]
        cols_exist = [c for c in cols_show if c in df.columns]

        rename_map = {
            "codigo_estilo": "Código", "producto_base": "Producto",
            "color": "Color", "talla": "Talla",
            "cantidad": "Stock", "costo": "Costo", "precio": "Precio",
        }
        df_show = df[cols_exist].copy()
        for col in df_show.columns:
            if df_show[col].dtype in (np.dtype('float64'),):
                df_show[col] = df_show[col].round(2)
        df_show = df_show.rename(columns=rename_map)
        st.dataframe(df_show, use_container_width=True)

        # Totales
        total_skus = len(df)
        total_stock = int(df["cantidad"].sum()) if "cantidad" in df.columns else 0
        st.caption(f"📊 {total_skus} SKUs encontrados | {total_stock} unidades totales")

        # Exportar
        if st.button("📥 Exportar a Excel", key="inv_exportar"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_show.to_excel(writer, index=False, sheet_name="Inventario")
            st.download_button(
                "⬇️ Descargar Excel",
                data=output.getvalue(),
                file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("ℹ️ No hay inventario cargado o no se encontraron resultados.")
        st.caption("Admin: sube un archivo en la pestaña 'Cargar Archivo'")


# =============================================================================
# SECCIÓN: Historial de Cargas
# =============================================================================
def _seccion_historial():
    st.markdown("### 📜 Historial de Cargas")
    try:
        cargas = local_db.find(
            ARCHIVOS_CARGADOS_COL, {},
            sort=[("fecha_carga", -1)], limit=20
        )
        if cargas:
            df = pd.DataFrame(cargas)
            cols_show = ["archivo_nombre", "fecha_carga", "usuario", "filas", "activo"]
            cols_exist = [c for c in cols_show if c in df.columns]
            rename_map = {
                "archivo_nombre": "Archivo", "fecha_carga": "Fecha",
                "usuario": "Usuario", "filas": "Registros", "activo": "Activo",
            }
            df_show = df[cols_exist].copy()
            if "fecha_carga" in df_show.columns:
                df_show["fecha_carga"] = df_show["fecha_carga"].astype(str)[:19]
            if "activo" in df_show.columns:
                df_show["activo"] = df_show["activo"].apply(lambda x: "✅ Sí" if x else "❌ No")
            df_show = df_show.rename(columns=rename_map)
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("No hay historial de cargas.")
    except Exception as e:
        st.info("No hay historial de cargas disponible.")


# =============================================================================
# FUNCION PRINCIPAL
# =============================================================================
def show_control_inventario():
    """Punto de entrada principal del módulo de inventario."""
    if not can_access("inventario"):
        st.error("⛔ No tienes permisos para acceder a Inventario")
        return

    add_back_button(key="back_inventario")
    show_module_header("📦 Control de Inventario", "Gestión de stock consolidado y búsqueda de productos")

    tab1, tab2, tab3 = st.tabs(["🔍 Buscar Inventario", "📤 Cargar Archivo (Admin)", "📜 Historial"])
    with tab1:
        _seccion_busqueda()
    with tab2:
        _seccion_carga_archivo()
    with tab3:
        _seccion_historial()
