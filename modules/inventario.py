# modules/inventario.py
"""
Módulo de Control de Inventario - Aeropostale ERP
- Admin carga archivo stock consolidado (Excel/CSV) → se guarda en MongoDB
- Usuarios realizan búsquedas sobre el archivo cargado
- Soporta búsqueda por código estilo, producto, color, talla, etc.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import io
from utils.ui import add_back_button, show_module_header
from utils.common import sanitize_for_mongo, normalizar_texto
from database.manager import local_db
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
TIPOS_ARCHIVO = [".xlsx", ".xls", ".csv"]

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def _identificar_columnas(df: pd.DataFrame) -> dict:
    """Identifica columnas clave en el DataFrame de inventario."""
    cols = {c: normalizar_texto(c) for c in df.columns}
    resultado = {
        "codigo_estilo": None,
        "codigo_barra": None,
        "producto": None,
        "color": None,
        "talla": None,
        "cantidad": None,
        "costo": None,
        "precio": None,
        "ubicacion": None,
        "categoria": None,
    }
    
    # Patrones de búsqueda
    patrones = {
        "codigo_estilo": ["CODIGO", "ESTILO", "SKU", "COD", "CÓDIGO", "STYLE", "COD_ESTILO", "CODART"],
        "codigo_barra": ["BARRA", "BARCODE", "EAN", "UPC", "COD_BARRA", "CÓDIGO BARRAS"],
        "producto": ["PRODUCTO", "DESCRIPCION", "DESCRIPCIÓN", "DESC", "NOMBRE", "ARTICULO", "ARTÍCULO", "ITEM"],
        "color": ["COLOR", "COLOUR"],
        "talla": ["TALLA", "SIZE", "TAMAÑO"],
        "cantidad": ["CANTIDAD", "STOCK", "EXISTENCIA", "INVENTARIO", "QTY", "CANT", "DISPONIBLE", "SALDO"],
        "costo": ["COSTO", "COST", "PRECIO COSTO", "VLR_UNIT"],
        "precio": ["PRECIO", "PRICE", "PVP", "VENTA", "PRECIO VENTA"],
        "ubicacion": ["UBICACION", "UBICACIÓN", "BODEGA", "LOCATION", "ALMACEN", "LOCAL"],
        "categoria": ["CATEGORIA", "CATEGORÍA", "CAT", "LINEA", "LÍNEA", "DEPARTAMENTO", "SECCION"],
    }

    for col_norm in cols.values():
        col_upper = col_norm.upper().strip()
        for clave, patrones_lista in patrones.items():
            for pat in patrones_lista:
                if pat.upper() in col_upper:
                    # Buscar columna original
                    col_orig = [c for c, n in cols.items() if n == col_norm]
                    if col_orig and resultado[clave] is None:
                        resultado[clave] = col_orig[0]
                    break

    return resultado


def _procesar_archivo_inventario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa y normaliza el DataFrame de inventario.
    Parsea producto → (base, color, talla) si no vienen separados.
    """
    cols = _identificar_columnas(df)
    
    # Copia de trabajo
    df_out = df.copy()
    
    # Normalizar nombres de columna para trabajar
    rename_map = {}
    for clave, col_orig in cols.items():
        if col_orig:
            rename_map[col_orig] = clave
    
    if rename_map:
        df_out = df_out.rename(columns=rename_map)
    
    # Si no hay columna de talla/color pero hay producto, intentar parsear
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
    
    # Generar SKU compuesto si hay código_estilo + talla + color
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
    
    # Generar código_estilo corto (primeras palabras antes de guión o espacio)
    df_out["codigo_corto"] = df_out["codigo_estilo"].apply(
        lambda x: x.split("-")[0].strip() if "-" in x else x.split()[0] if x.strip() else ""
    )
    
    # Clasificar tipo de prenda
    df_out["tipo_prenda"] = df_out["producto_base"].apply(
        lambda x: clasificar_tipo_prenda(x)[0] if x else "Otro"
    )
    df_out["tipo_abrev"] = df_out["producto_base"].apply(
        lambda x: clasificar_tipo_prenda(x)[1] if x else "OTRO"
    )
    df_out["genero"] = df_out["producto_base"].apply(
        lambda x: extraer_genero(x) if x else "UNISEX"
    )
    
    # Timestamp
    df_out["_procesado"] = datetime.utcnow().isoformat()
    
    return df_out


def _calcular_metricas(df: pd.DataFrame) -> dict:
    """Calcula métricas resumen del inventario cargado."""
    metricas = {
        "total_skus": int(len(df)),
        "total_unidades": int(df["cantidad"].sum()) if "cantidad" in df.columns else 0,
        "valor_total": float((df["cantidad"] * df["costo"]).sum()) if "costo" in df.columns else 0.0,
        "valor_venta": float((df["cantidad"] * df["precio"]).sum()) if "precio" in df.columns else 0.0,
        "skus_sin_stock": int((df["cantidad"] == 0).sum()) if "cantidad" in df.columns else 0,
        "tipo_prenda": df["tipo_prenda"].value_counts().to_dict() if "tipo_prenda" in df.columns else {},
        "genero": df["genero"].value_counts().to_dict() if "genero" in df.columns else {},
    }
    return metricas


# =============================================================================
# SECCIÓN: ADMIN - Carga de Archivo
# =============================================================================
def _seccion_carga_archivo():
    """Panel exclusivo para administradores: carga de archivo stock consolidado."""
    
    if st.session_state.get("role") != "Administrador":
        st.info("🔒 Solo el Administrador puede cargar archivos de inventario.")
        return
    
    st.markdown("### 📤 Cargar Archivo de Stock Consolidado")
    st.caption("Sube el archivo Excel/CSV con el inventario consolidado. El archivo se guardará en la base de datos "
               "para que todos los usuarios puedan consultarlo.")
    
    uploaded_file = st.file_uploader(
        "Selecciona archivo (Excel o CSV)",
        type=["xlsx", "xls", "csv"],
        key="inventario_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # Leer archivo
            file_ext = uploaded_file.name.split(".")[-1].lower()
            if file_ext == "csv":
                df_raw = pd.read_csv(uploaded_file, encoding="utf-8", low_memory=False)
            else:
                df_raw = pd.read_excel(uploaded_file, engine="openpyxl")
            
            st.success(f"✅ Archivo leído: {uploaded_file.name} ({len(df_raw)} filas, {len(df_raw.columns)} columnas)")
            
            with st.expander("👁️ Vista previa", expanded=False):
                st.dataframe(df_raw.head(20), use_container_width=True)
                st.caption(f"Columnas detectadas: {', '.join(df_raw.columns.tolist())}")
            
            # Identificar columnas
            cols_detectadas = _identificar_columnas(df_raw)
            columnas_encontradas = {k: v for k, v in cols_detectadas.items() if v}
            
            if columnas_encontradas:
                st.info(f"📋 Columnas reconocidas: {', '.join(f'**{k}** → `{v}`' for k, v in columnas_encontradas.items())}")
            else:
                st.warning("⚠️ No se pudieron reconocer columnas automáticamente. Se usará el archivo tal cual.")
            
            # Botón para procesar y guardar
            if st.button("📦 Procesar y Guardar en Base de Datos", type="primary", key="btn_guardar_inventario"):
                with st.spinner("Procesando archivo de inventario..."):
                    # Procesar
                    df_procesado = _procesar_archivo_inventario(df_raw)
                    
                    # Calcular métricas
                    metricas = _calcular_metricas(df_procesado)
                    
                    # Sanitizar para MongoDB
                    registros = sanitize_for_mongo(df_procesado.to_dict("records"))
                    
                    # Guardar metadatos de la carga
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
                    
                    # --- Transacción: eliminar carga activa anterior + insertar nueva ---
                    try:
                        # Marcar cargas anteriores como inactivas
                        local_db.update(
                            ARCHIVOS_CARGADOS_COL,
                            {"activo": True},
                            {"$set": {"activo": False}}
                        )
                        
                        # Insertar metadata de la nueva carga
                        carga_id = local_db.insert(ARCHIVOS_CARGADOS_COL, metadata)
                        
                        # Reemplazar registros de inventario (borrar anteriores + insertar nuevos)
                        local_db.delete(COLECCION_INVENTARIO, {"carga_activa": True})
                        
                        # Marcar todos los registros nuevos con carga_activa
                        batch_size = 500
                        total_insertados = 0
                        for i in range(0, len(registros), batch_size):
                            batch = registros[i:i + batch_size]
                            for reg in batch:
                                reg["carga_activa"] = True
                                reg["carga_id"] = str(carga_id)
                                local_db.insert(COLECCION_INVENTARIO, reg)
                            total_insertados += len(batch)
                        
                        # Guardar métricas como registro de historial
                        local_db.insert("historico", {
                            "modulo": "control_inventario",
                            "pestaña": "carga_archivo",
                            "archivo_nombre": uploaded_file.name,
                            "fecha_archivo": datetime.utcnow(),
                            "fecha_carga": datetime.utcnow(),
                            "usuario": st.session_state.get("username", "admin"),
                            "metricas": metricas,
                            "filas": len(registros),
                            "columnas": len(df_raw.columns),
                        })
                        
                        st.success(f"✅ **{total_insertados} registros** guardados en la base de datos.")
                        st.balloons()
                        
                        # Mostrar resumen
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("📦 SKUs", f"{metricas['total_skus']:,}")
                        c2.metric("📊 Unidades", f"{metricas['total_unidades']:,}")
                        c3.metric("💰 Valor Costo", f"${metricas['valor_total']:,.2f}")
                        c4.metric("🚫 Sin Stock", f"{metricas['skus_sin_stock']:,}")
                        
                    except Exception as e:
                        st.error(f"❌ Error al guardar en la base de datos: {e}")
            else:
                st.info("Presiona el botón para guardar el archivo en la base de datos.")
                
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")
            st.exception(e)


# =============================================================================
# SECCIÓN: Búsqueda de Inventario
# =============================================================================
def _seccion_busqueda():
    """Panel de búsqueda de inventario (accesible para todos los usuarios)."""
    
    st.markdown("### 🔍 Buscar en Inventario Consolidado")
    
    # Verificar si hay datos cargados
    try:
        total_registros = local_db.count(COLECCION_INVENTARIO, {"carga_activa": True})
    except:
        total_registros = 0
    
    if total_registros == 0:
        # Intentar desde el metadata
        carga = None
        try:
            cargas = local_db.find(ARCHIVOS_CARGADOS_COL, {"activo": True}, sort=[("fecha_carga", -1)], limit=1)
            if cargas:
                carga = cargas[0]
        except:
            pass
        
        if carga:
            st.info(f"📂 Última carga: **{carga.get('archivo_nombre', 'N/A')}** "
                    f"({carga.get('filas', 0):,} registros) el "
                    f"{carga.get('fecha_carga', 'N/A')}")
            
            # Botón para recargar datos a la colección
            st.warning("⚠️ Los datos no están disponibles para consulta directa. Contacta al administrador "
                       "para que recargue el archivo.")
        else:
            st.warning("⚠️ No hay inventario cargado en la base de datos.")
            st.info("Solicita al Administrador que cargue el archivo de stock consolidado.")
        return
    
    # Filtros de búsqueda
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Intentar obtener valores únicos para autocomplete
            try:
                muestra = local_db.find(COLECCION_INVENTARIO, {"carga_activa": True}, limit=20)
                codigos_ejemplo = sorted(set(
                    str(r.get("codigo_estilo", "")) for r in muestra if r.get("codigo_estilo")
                ))
            except:
                codigos_ejemplo = []
            
            busqueda = st.text_input(
                "🔎 Buscar por código estilo, producto, SKU o descripción",
                placeholder="Ej: 4AER22, CAMISETA, NEGRO, S, etc.",
                key="inventario_busqueda"
            )
        
        with col2:
            # Filtro por tipo de prenda
            try:
                tipos = local_db.find(COLECCION_INVENTARIO, {"carga_activa": True}, limit=1000)
                tipos_unicos = sorted(set(
                    str(r.get("tipo_prenda", "Otro")) for r in tipos if r.get("tipo_prenda")
                ))
            except:
                tipos_unicos = []
            
            tipo_filtro = st.selectbox(
                "Tipo de Prenda",
                ["Todos"] + tipos_unicos,
                key="inventario_tipo"
            )
        
        with col3:
            genero_filtro = st.selectbox(
                "Género",
                ["Todos", "GUYS", "GIRLS", "UNISEX"],
                key="inventario_genero"
            )
    
    # Botones de acción
    col_accion1, col_accion2, col_accion3 = st.columns([1, 1, 2])
    with col_accion1:
        buscar_btn = st.button("🔍 Buscar", type="primary", use_container_width=True)
    with col_accion2:
        limpiar_btn = st.button("🗑️ Limpiar", use_container_width=True)
    
    if limpiar_btn:
        st.session_state["inventario_busqueda"] = ""
        st.rerun()
    
    # Construir query
    query = {"carga_activa": True}
    
    if tipo_filtro and tipo_filtro != "Todos":
        query["tipo_prenda"] = {"$regex": tipo_filtro, "$options": "i"}
    
    if genero_filtro and genero_filtro != "Todos":
        query["genero"] = {"$regex": f"^{genero_filtro}$", "$options": "i"}
    
    # --- LÓGICA DE BÚSQUEDA ---
    resultados = []
    df_resultados = pd.DataFrame()
    
    if buscar_btn or busqueda:
        busqueda_texto = busqueda.strip()
        
        if busqueda_texto:
            # Búsqueda case-insensitive en múltiples campos
            termino = normalizar_texto(busqueda_texto)
            # También buscar sin normalizar para términos exactos
            termino_original = busqueda_texto
            
            # Query de búsqueda tipo "full-text search" con regex
            regex_query = {
                "$or": [
                    {"codigo_estilo": {"$regex": termino, "$options": "i"}},
                    {"codigo_corto": {"$regex": termino, "$options": "i"}},
                    {"codigo_barra": {"$regex": termino, "$options": "i"}},
                    {"producto_base": {"$regex": termino, "$options": "i"}},
                    {"producto": {"$regex": termino, "$options": "i"}},
                    {"sku_compuesto": {"$regex": termino, "$options": "i"}},
                    {"color": {"$regex": termino, "$options": "i"}},
                    {"talla": {"$regex": f"^{termino}$", "$options": "i"}},
                    {"tipo_prenda": {"$regex": termino, "$options": "i"}},
                    {"ubicacion": {"$regex": termino, "$options": "i"}},
                    {"categoria": {"$regex": termino, "$options": "i"}},
                ]
            }
            
            # Merge con filtros existentes
            query_merged = {"$and": [query, regex_query]}
        else:
            query_merged = query
        
        try:
            # Buscar en MongoDB
            resultados = local_db.find(
                COLECCION_INVENTARIO,
                query_merged,
                sort=[("codigo_estilo", 1)],
                limit=2000
            )
        except Exception as e:
            st.error(f"Error en búsqueda: {e}")
            resultados = []
        
        if resultados:
            # Convertir a DataFrame
            df_resultados = pd.DataFrame(resultados)
            
            # Columnas a mostrar
            columnas_visibles = [
                "codigo_estilo", "producto_base", "color", "talla",
                "cantidad", "costo", "precio", "tipo_prenda", "genero",
                "ubicacion", "sku_compuesto"
            ]
            columnas_existentes = [c for c in columnas_visibles if c in df_resultados.columns]
            columnas_renom = {
                "codigo_estilo": "Código Estilo",
                "producto_base": "Producto",
                "color": "Color",
                "talla": "Talla",
                "cantidad": "Stock",
                "costo": "Costo",
                "precio": "Precio",
                "tipo_prenda": "Tipo",
                "genero": "Género",
                "ubicacion": "Ubicación",
                "sku_compuesto": "SKU Compuesto",
            }
            
            # Mostrar métricas arriba
            total_sku_encontrados = len(df_resultados)
            total_stock = int(df_resultados["cantidad"].sum()) if "cantidad" in df_resultados.columns else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🎯 Resultados", f"{total_sku_encontrados:,}")
            c2.metric("📊 Unidades", f"{total_stock:,}")
            if total_registros > 0:
                c3.metric("📦 Total SKUs en BD", f"{total_registros:,}")
            
            # Dataframe con formato
            df_show = df_resultados[columnas_existentes].copy()
            
            # Formato moneda
            if "costo" in df_show.columns:
                df_show["costo"] = df_show["costo"].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
            if "precio" in df_show.columns:
                df_show["precio"] = df_show["precio"].apply(lambda x: f"${x:,.2f}" if x else "$0.00")
            
            df_show = df_show.rename(columns=columnas_renom)
            
            # Resaltar filas sin stock
            def _highlight_stock(val):
                """Resalta en rojo si stock es 0."""
                try:
                    num_val = int(str(val).replace(",", "").replace("$", ""))
                    if num_val == 0:
                        return 'background-color: rgba(207, 10, 44, 0.15); color: #FF6B6B'
                except:
                    pass
                return ''
            
            styled_df = df_show.style.applymap(
                _highlight_stock,
                subset=["Stock"] if "Stock" in df_show.columns else []
            )
            
            st.dataframe(styled_df, use_container_width=True, height=500)
            
            # Botón descarga
            st.download_button(
                label="📥 Descargar Resultados (Excel)",
                data=_to_excel_bytes(df_resultados[columnas_existentes]),
                file_name=f"inventario_busqueda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_inventario"
            )
            
            # --- Gráfico de distribución ---
            st.divider()
            st.markdown("### 📊 Distribución de Resultados")
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                if "tipo_prenda" in df_resultados.columns:
                    tipo_counts = df_resultados["tipo_prenda"].value_counts().reset_index()
                    tipo_counts.columns = ["Tipo", "Cantidad"]
                    fig = px.pie(
                        tipo_counts, values="Cantidad", names="Tipo",
                        title="Distribución por Tipo de Prenda",
                        color_discrete_sequence=px.colors.sequential.RdBu_r
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_graf2:
                if "color" in df_resultados.columns:
                    color_counts = df_resultados["color"].value_counts().head(15).reset_index()
                    color_counts.columns = ["Color", "Cantidad"]
                    fig = px.bar(
                        color_counts, x="Color", y="Cantidad",
                        title="Top 15 Colores",
                        color="Cantidad",
                        color_continuous_scale="Reds"
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            if busqueda:
                st.warning(f"❌ No se encontraron resultados para: **{busqueda}**")
            else:
                st.info("ℹ️ Ingresa un término de búsqueda y presiona **Buscar**.")
    else:
        # Vista inicial sin búsqueda
        try:
            muestra = local_db.find(
                COLECCION_INVENTARIO,
                {"carga_activa": True},
                limit=100,
                sort=[("cantidad", -1)]
            )
            if muestra:
                st.info(f"📦 **{total_registros:,}** registros disponibles. "
                        f"Usa el campo de búsqueda para filtrar.")
                
                # Top productos con más stock
                df_muestra = pd.DataFrame(muestra)
                if "producto_base" in df_muestra.columns and "cantidad" in df_muestra.columns:
                    top_stock = df_muestra.groupby("producto_base")["cantidad"].sum().nlargest(10).reset_index()
                    top_stock.columns = ["Producto", "Unidades"]
                    
                    fig = px.bar(
                        top_stock, x="Producto", y="Unidades",
                        title="📦 Top 10 Productos con Mayor Stock",
                        color="Unidades",
                        color_continuous_scale="Reds"
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#FFFFFF",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig, use_container_width=True)
        except:
            pass


# =============================================================================
# SECCIÓN: Historial de Cargas
# =============================================================================
def _seccion_historial():
    """Muestra el historial de cargas de archivos."""
    st.markdown("### 📜 Historial de Cargas")
    
    try:
        cargas = local_db.find(
            ARCHIVOS_CARGADOS_COL,
            {},
            sort=[("fecha_carga", -1)],
            limit=20
        )
        
        if cargas:
            df_cargas = pd.DataFrame(cargas)
            columnas_mostrar = ["archivo_nombre", "fecha_carga", "usuario", "filas", "activo"]
            cols_existentes = [c for c in columnas_mostrar if c in df_cargas.columns]
            
            renom = {
                "archivo_nombre": "Archivo",
                "fecha_carga": "Fecha Carga",
                "usuario": "Usuario",
                "filas": "Registros",
                "activo": "Activo",
            }
            
            df_show = df_cargas[cols_existentes].copy()
            if "fecha_carga" in df_show.columns:
                df_show["fecha_carga"] = df_show["fecha_carga"].astype(str)
            if "activo" in df_show.columns:
                df_show["activo"] = df_show["activo"].apply(lambda x: "✅ Sí" if x else "❌ No")
            
            df_show = df_show.rename(columns=renom)
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("No hay historial de cargas.")
            
    except Exception as e:
        st.info("No hay historial de cargas disponible.")


# =============================================================================
# FUNCIÓN AUXILIAR: Exportar a Excel
# =============================================================================
def _to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convierte DataFrame a bytes de Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================
def show_control_inventario():
    """Punto de entrada principal del módulo de control de inventario."""
    
    add_back_button(key="back_inventario")
    show_module_header("📦 Control de Inventario", "Gestión de stock consolidado y búsqueda de productos")
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["🔍 Buscar Inventario", "📤 Cargar Archivo (Admin)", "📜 Historial"])
    
    with tab1:
        _seccion_busqueda()
    
    with tab2:
        _seccion_carga_archivo()
    
    with tab3:
        _seccion_historial()
