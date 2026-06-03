# modules/inventario.py
# Versión mejorada y robusta + funcionalidades de busca_sku.py
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
import time
import math
from utils.ui import acu_metric
from database.manager import get_db_v2
from sklearn.linear_model import LinearRegression
import numpy as np

# ========== FUNCIONES AUXILIARES ==========
def detectar_columnas(df):
    """Detecta columnas clave: codigo, producto, tiendas, fecha"""
    columnas = list(df.columns)
    codigo_col, producto_col, fecha_col = None, None, None

    for col in columnas:
        col_low = col.lower()
        if not codigo_col and ('cod' in col_low or 'sku' in col_low):
            codigo_col = col
        if not producto_col and ('producto' in col_low or 'descrip' in col_low):
            producto_col = col
        if not fecha_col and ('fecha' in col_low or 'date' in col_low):
            fecha_col = col

    # Fallbacks
    if not codigo_col:
        codigo_col = columnas[0]
    if not producto_col:
        producto_col = columnas[1] if len(columnas) > 1 else codigo_col

    # Detectar tiendas (numéricas, excluyendo código y producto)
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    exclude = [codigo_col, producto_col]
    tiendas = [c for c in numeric_cols if c not in exclude]

    # Si no hay numéricas, intentar desde MATRIZ hasta TOTAL
    if not tiendas and 'MATRIZ' in columnas:
        try:
            idx_matriz = columnas.index('MATRIZ')
            idx_total = columnas.index('TOTAL') if 'TOTAL' in columnas else len(columnas)
            tiendas = columnas[idx_matriz:idx_total]
        except:
            pass

    return codigo_col, producto_col, tiendas, fecha_col

def calcular_dias_inventario(df, fecha_col):
    """Agrega columna de días en inventario si existe fecha_col"""
    if fecha_col and fecha_col in df.columns:
        df['FECHA_DT'] = pd.to_datetime(df[fecha_col], errors='coerce')
        df['DIAS_INVENTARIO'] = (datetime.now() - df['FECHA_DT']).dt.days
        return df, 'DIAS_INVENTARIO'
    return df, None

def mostrar_metricas_seguras(titulo, valor):
    """Evita errores con fechas o NaNs en st.metric"""
    try:
        val_str = str(valor)
        if isinstance(valor, float) and math.isnan(valor):
            val_str = "0"
        st.markdown(acu_metric(titulo, val_str, color="blue", icon="📊"), unsafe_allow_html=True)
    except Exception as e:
        st.markdown(acu_metric(titulo, "N/A", color="red", icon="⚠️"), unsafe_allow_html=True)

# ========== PÁGINA PRINCIPAL ==========
def show_control_inventario():
    from utils.ui import show_module_header, add_back_button
    from utils.backgrounds import set_module_background

    add_back_button(key="back_inventario")
    from utils.ui import inject_acumatica_css
    inject_acumatica_css()
    show_module_header("📦 Control de Inventario", "Gestión de stock en tiempo real")
    set_module_background("inventario")

    # Estado de sesión
    if 'df' not in st.session_state:
        st.session_state.df = None
        st.session_state.tiendas = []
        st.session_state.codigo_col = None
        st.session_state.producto_col = None
        st.session_state.fecha_col = None
        st.session_state.dias_col = None

    rol = st.session_state.get("role", "")
    puede_cargar = rol in ["Administrador", "Logística"]

    # ===== CARGA DE ARCHIVO =====
    if puede_cargar:
        st.subheader("📂 Ingesta de Datos (Diaria y Masiva)")
        tab_diaria, tab_masiva = st.tabs(["Carga Diaria", "Carga Masiva (Históricos)"])
        
        with tab_masiva:
            st.info("Sube múltiples archivos para construir el histórico. El sistema guardará la fecha que encuentre en el nombre del archivo (ej. stock_2024-05-10.xlsx) o la fecha actual.")
            archivos_masivos = st.file_uploader("Seleccionar múltiples archivos Excel", type=["xlsx", "xls"], accept_multiple_files=True, key="stock_upload_masivo")
            if st.button("Procesar Archivos Históricos", type="primary") and archivos_masivos:
                db = get_db_v2()
                with st.spinner(f"Procesando {len(archivos_masivos)} archivos..."):
                    import re
                    exitosos = 0
                    for arch in archivos_masivos:
                        try:
                            df_temp = pd.read_excel(arch, engine='openpyxl')
                            match = re.search(r'\d{4}-\d{2}-\d{2}', arch.name)
                            fecha_str = match.group() if match else datetime.now().strftime("%Y-%m-%d")
                            
                            data_to_save = df_temp.to_dict("records")
                            for row in data_to_save:
                                row["fecha_carga_diaria"] = fecha_str
                                
                            db.delete("stock_consolidado", {"fecha_carga_diaria": fecha_str})
                            db.insert_many("stock_consolidado", data_to_save)
                            exitosos += 1
                        except Exception as e:
                            st.error(f"Error procesando {arch.name}: {e}")
                    st.success(f"✅ Se guardaron {exitosos} archivos históricos en MongoDB exitosamente.")
        
        with tab_diaria:
            archivo = st.file_uploader("Seleccionar archivo Excel del día", type=["xlsx", "xls"], key="stock_upload")
            if archivo:
            try:
                with st.spinner("Cargando y procesando archivo..."):
                    time.sleep(0.5)  # simular progreso
                    df = pd.read_excel(archivo, engine='openpyxl')
                    codigo_col, producto_col, tiendas, fecha_col = detectar_columnas(df)
                    df, dias_col = calcular_dias_inventario(df, fecha_col)

                    # --- INTEGRACIÓN MONGODB E HISTÓRICO ---
                    db = get_db_v2()
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    # Guardar histórico del día actual
                    data_to_save = df.to_dict("records")
                    for row in data_to_save:
                        row["fecha_carga_diaria"] = today_str
                    
                    db.delete("stock_consolidado", {"fecha_carga_diaria": today_str})
                    db.insert_many("stock_consolidado", data_to_save)
                    
                    # Calcular Delta (Ventas) vs ayer
                    yesterday = datetime.now() - pd.Timedelta(days=1)
                    yesterday_str = yesterday.strftime("%Y-%m-%d")
                    
                    docs_ayer = db.find("stock_consolidado", {"fecha_carga_diaria": yesterday_str})
                    if docs_ayer:
                        df_ayer = pd.DataFrame(docs_ayer)
                        # Sumar totals si es posible
                        if codigo_col in df_ayer.columns:
                            # Aseguramos columnas numericas
                            df['TOTAL_INV'] = df[tiendas].sum(axis=1) if tiendas else 0
                            df_ayer['TOTAL_INV'] = df_ayer[tiendas].sum(axis=1) if tiendas else 0
                            
                            curr_grp = df.groupby(codigo_col)['TOTAL_INV'].sum().reset_index(name='T_CURR')
                            prev_grp = df_ayer.groupby(codigo_col)['TOTAL_INV'].sum().reset_index(name='T_PREV')
                            merged = pd.merge(curr_grp, prev_grp, on=codigo_col, how='left')
                            merged['T_PREV'] = merged['T_PREV'].fillna(merged['T_CURR'])
                            merged['DELTA_VENTAS'] = merged['T_PREV'] - merged['T_CURR']
                            
                            df = pd.merge(df, merged[[codigo_col, 'DELTA_VENTAS']], on=codigo_col, how='left')
                            df['DELTA_VENTAS'] = df['DELTA_VENTAS'].fillna(0)
                    else:
                        df['DELTA_VENTAS'] = 0

                    st.session_state.df = df
                    st.session_state.codigo_col = codigo_col
                    st.session_state.producto_col = producto_col
                    st.session_state.tiendas = tiendas
                    st.session_state.fecha_col = fecha_col
                    st.session_state.dias_col = dias_col

                st.success(f"✅ Archivo cargado: {df.shape[0]} SKUs, {len(tiendas)} tiendas")
                st.info(f"Código: **{codigo_col}** | Producto: **{producto_col}**")
                if fecha_col:
                    st.info(f"Columna de fecha detectada: **{fecha_col}**")
                st.dataframe(df.head())
            except Exception as e:
                st.error(f"❌ Error al leer archivo: {e}")
    else:
        st.info("Solo administradores y logística pueden cargar archivos. Si ya hay datos cargados, puedes consultar.")

    if st.session_state.df is None:
        if puede_cargar:
            st.info("Carga un archivo Excel para comenzar.")
        else:
            st.warning("Aún no hay datos de stock cargados. Contacta al administrador.")
        return

    df = st.session_state.df
    codigo_col = st.session_state.codigo_col
    producto_col = st.session_state.producto_col
    tiendas = st.session_state.tiendas
    dias_col = st.session_state.dias_col

    # ===== MÉTRICAS GENERALES =====
    st.markdown("### 📊 Resumen General")
    total_skus = df[codigo_col].nunique()
    total_stock = df[tiendas].sum().sum() if tiendas else 0
    avg_dias = df[dias_col].mean() if dias_col and dias_col in df.columns else None

    col1, col2, col3 = st.columns(3)
    col1.metric("Total SKUs", f"{total_skus:,}")
    col2.metric("Stock Total", f"{total_stock:,.0f}")
    if avg_dias and pd.notna(avg_dias):
        col3.metric("Días promedio en inventario", f"{avg_dias:.1f} días")
    else:
        col3.metric("Días promedio en inventario", "N/A")

    # ===== PESTAÑAS =====
    tab_sku, tab_atributo, tab_kpi = st.tabs(["🔍 Consulta por SKU", "🏷️ Consulta por Atributo", "📈 KPIs y Reportes"])

    # ---------- TAB SKU ----------
    with tab_sku:
        st.subheader(f"Buscar por {codigo_col} (SKU)")
        sku_input = st.text_input(f"Ingresa el {codigo_col} exacto", placeholder="Ej: 140020749")
        if st.button("Buscar SKU", type="primary"):
            if not sku_input.strip():
                st.warning("Ingresa un código.")
            else:
                sku_str = str(sku_input).strip()
                df_filt = df[df[codigo_col].astype(str).str.strip() == sku_str]
                if df_filt.empty:
                    st.error(f"No se encontró el {codigo_col}: {sku_input}")
                else:
                    row = df_filt.iloc[0]
                    st.markdown(f"### Producto: {row[producto_col]}")
                    # Atributos
                    for col in df.columns:
                        if col not in tiendas and col not in [codigo_col, producto_col]:
                            valor = row[col]
                            if pd.isna(valor):
                                continue
                            mostrar_metricas_seguras(col, valor)

                    # Stock por tienda
                    st.markdown("#### 📍 Stock por tienda (solo >0)")
                    stock_data = []
                    for t in tiendas:
                        qty = row[t]
                        if qty > 0:
                            stock_data.append({"Tienda": t, "Cantidad": int(qty)})
                    if stock_data:
                        df_stock = pd.DataFrame(stock_data)
                        st.dataframe(df_stock, use_container_width=True)
                        fig = px.bar(df_stock, x="Tienda", y="Cantidad", title="Distribución de stock", text="Cantidad")
                        fig.update_traces(textposition="outside")
                        fig.update_layout(template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No hay stock en ninguna tienda.")

    # ---------- TAB ATRIBUTO ----------
    with tab_atributo:
        st.subheader("Buscar por Atributo (Estilo, Color, Temporada, etc.)")
        columnas_texto = df.select_dtypes(include=['object']).columns.tolist()
        for excl in [codigo_col, producto_col]:
            if excl in columnas_texto:
                columnas_texto.remove(excl)
        if not columnas_texto:
            st.warning("No hay columnas de texto para filtrar.")
        else:
            atributo = st.selectbox("Selecciona el atributo", columnas_texto)
            valores = sorted([str(v) for v in df[atributo].dropna().unique()])
            valor_sel = st.selectbox(f"Valor de {atributo}", valores)
            if st.button("Consultar", type="primary"):
                df_filt = df[df[atributo].astype(str) == valor_sel]
                if df_filt.empty:
                    st.warning(f"No hay productos con {atributo} = {valor_sel}")
                else:
                    st.markdown(f"### Resultados para {atributo} = **{valor_sel}**")
                    st.markdown(acu_metric("SKUs encontrados", len(df_filt), color="green", icon="🔍"), unsafe_allow_html=True)
                    if tiendas:
                        stock_agg = df_filt[tiendas].sum()
                        stock_agg = stock_agg[stock_agg > 0]
                        if stock_agg.empty:
                            st.info("No hay stock en ninguna tienda.")
                        else:
                            df_agg = pd.DataFrame({"Tienda": stock_agg.index, "Cantidad": stock_agg.values})
                            st.dataframe(df_agg, use_container_width=True)
                            fig = px.bar(df_agg, x="Tienda", y="Cantidad",
                                         title=f"Stock agregado para {atributo}: {valor_sel}", text="Cantidad")
                            fig.update_traces(textposition="outside")
                            fig.update_layout(template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True)
                            csv = df_agg.to_csv(index=False).encode('utf-8')
                            st.download_button("📥 Exportar a CSV", csv, f"stock_{atributo}_{valor_sel}.csv", "text/csv")
                    else:
                        st.warning("No se detectaron columnas de tiendas.")

    # ---------- TAB KPI Y REPORTES (desde busca_sku.py) ----------
    with tab_kpi:
        st.subheader("📊 Indicadores Clave de Performance (KPIs)")

        if dias_col and dias_col in df.columns:
            # Productos lentos (>90 días)
            st.markdown("#### 🐢 Productos Lentos (más de 90 días en inventario)")
            slow = df[df[dias_col] > 90].copy()
            if slow.empty:
                st.success("✅ No hay productos con más de 90 días en inventario.")
            else:
                st.warning(f"⚠️ {len(slow)} productos superan los 90 días.")
                # Mostrar tabla resumida
                cols_mostrar = [codigo_col, producto_col, dias_col] + tiendas[:3]  # primeras 3 tiendas
                cols_mostrar = [c for c in cols_mostrar if c in slow.columns]
                st.dataframe(slow[cols_mostrar].head(20), use_container_width=True)

                # Exportar reporte completo
                csv_slow = slow.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Exportar reporte de productos lentos (CSV)", csv_slow,
                                   "productos_lentos.csv", "text/csv")

            # Productos agotados (stock total = 0)
            st.markdown("#### 🚫 Productos Agotados (stock total = 0)")
            df['STOCK_TOTAL'] = df[tiendas].sum(axis=1)
            agotados = df[df['STOCK_TOTAL'] == 0]
            if agotados.empty:
                st.success("✅ Todos los productos tienen stock positivo.")
            else:
                st.warning(f"⚠️ {len(agotados)} productos sin stock en ninguna tienda.")
                st.dataframe(agotados[[codigo_col, producto_col]].head(20), use_container_width=True)

            # Top 10 productos con más stock
            st.markdown("#### 🏆 Top 10 productos con mayor stock total")
            top_stock = df.nlargest(10, 'STOCK_TOTAL')[[codigo_col, producto_col, 'STOCK_TOTAL']]
            st.dataframe(top_stock, use_container_width=True)

            # Stock por tienda (gráfico de barras)
            if len(tiendas) > 0:
                st.markdown("#### 🏪 Stock total por tienda")
                stock_por_tienda = df[tiendas].sum().sort_values(ascending=False)
                df_tienda = pd.DataFrame({"Tienda": stock_por_tienda.index, "Stock": stock_por_tienda.values})
                fig = px.bar(df_tienda, x="Tienda", y="Stock", title="Stock consolidado por tienda",
                             text="Stock", color="Stock", color_continuous_scale="Blues")
                fig.update_traces(textposition="outside")
                fig.update_layout(template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
            # --- INTEGRACIÓN MACHINE LEARNING (Curvas de Tallas) ---
            st.markdown("---")
            st.markdown("#### 🤖 Machine Learning: Sugerencia Avanzada Multidimensional")
            
            # Verificar si existen columnas requeridas para agrupar
            col_estilo = next((c for c in df.columns if 'ESTILO' in c.upper()), None)
            col_color = next((c for c in df.columns if 'COLOR' in c.upper()), None)
            col_talla = next((c for c in df.columns if 'TALLA' in c.upper()), None)
            
            if 'DELTA_VENTAS' in df.columns and col_estilo and col_color and col_talla:
                matriz_cols = [c for c in tiendas if 'MATRIZ' in c.upper()]
                matriz_col = matriz_cols[0] if matriz_cols else None
                
                if matriz_col:
                    tienda_sel = st.selectbox("Seleccione Tienda Destino", [c for c in tiendas if c != matriz_col])
                    
                    if st.button("Generar Sugerencias por Talla (ML)", type="primary"):
                        with st.spinner("Analizando curvas de tallas y proyectando demanda..."):
                            df_ml = df[df['DELTA_VENTAS'] > 0].copy()
                            
                            # 1. Agrupar Delta por ESTILO y COLOR
                            df_estilo_color = df_ml.groupby([col_estilo, col_color])['DELTA_VENTAS'].sum().reset_index(name='DELTA_EC')
                            
                            # 2. Agrupar por ESTILO, COLOR, TALLA para la proporción histórica
                            df_tallas = df_ml.groupby([col_estilo, col_color, col_talla])['DELTA_VENTAS'].sum().reset_index(name='DELTA_TALLA')
                            df_tallas = pd.merge(df_tallas, df_estilo_color, on=[col_estilo, col_color], how='left')
                            df_tallas['PROPORCION_TALLA'] = df_tallas['DELTA_TALLA'] / df_tallas['DELTA_EC']
                            
                            resultados = []
                            # Evaluamos cada SKU a nivel talla
                            for _, row in df_ml.iterrows():
                                est = row[col_estilo]
                                col = row[col_color]
                                tal = row[col_talla]
                                
                                rot_ec_df = df_estilo_color[(df_estilo_color[col_estilo]==est) & (df_estilo_color[col_color]==col)]
                                rotacion_estilo_color = rot_ec_df['DELTA_EC'].sum() if not rot_ec_df.empty else 0
                                
                                prop_talla_df = df_tallas[(df_tallas[col_estilo]==est) & (df_tallas[col_color]==col) & (df_tallas[col_talla]==tal)]
                                proporcion_talla = prop_talla_df['PROPORCION_TALLA'].sum() if not prop_talla_df.empty else 0
                                
                                rotacion_esperada_talla = rotacion_estilo_color * proporcion_talla if proporcion_talla > 0 else row['DELTA_VENTAS']
                                
                                demanda_7d = rotacion_esperada_talla * 7
                                stock_tienda = row.get(tienda_sel, 0)
                                stock_matriz = row.get(matriz_col, 0)
                                
                                sugerencia = 0
                                if stock_tienda < demanda_7d:
                                    necesidad = math.ceil(demanda_7d - stock_tienda)
                                    sugerencia = min(necesidad, stock_matriz)
                                        
                                if sugerencia > 0:
                                    resultados.append({
                                        codigo_col: row[codigo_col],
                                        producto_col: row[producto_col],
                                        col_estilo: est,
                                        col_color: col,
                                        col_talla: tal,
                                        'Demanda_Proyectada_Talla': round(demanda_7d, 1),
                                        'Stock_Matriz': stock_matriz,
                                        'Transferencia_Sugerida': sugerencia
                                    })
                            
                            if resultados:
                                df_sug = pd.DataFrame(resultados).sort_values([col_estilo, col_color, 'Transferencia_Sugerida'], ascending=[True, True, False])
                                st.dataframe(df_sug, use_container_width=True)
                                csv_ml = df_sug.to_csv(index=False).encode('utf-8')
                                st.download_button("📥 Exportar Sugerencias con Curva de Tallas (CSV)", csv_ml, "sugerencias_tallas.csv", "text/csv")
                            else:
                                st.success("No hay sugerencias pendientes para esta tienda.")
                else:
                    st.info("No se encontró una columna 'MATRIZ'.")
            else:
                st.info("Aún no hay datos históricos suficientes o faltan columnas (ESTILO, COLOR, TALLA) para aplicar ML con curvas de tallas.")
        else:
            st.info("No se detectó una columna de fecha. No es posible calcular días en inventario ni productos lentos.")

    # ===== EXPORTAR DATOS COMPLETOS =====
    st.markdown("---")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv_full = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Exportar todo el stock a CSV", csv_full, "stock_completo.csv", "text/csv")
    with col_exp2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Stock")
        st.download_button("📥 Exportar todo el stock a Excel", output.getvalue(),
                           "stock_completo.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.expander("📋 Ver columnas de tiendas detectadas"):
        st.write(tiendas)
