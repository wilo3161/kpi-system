# modules/reconciliacion.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import tempfile
import io
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from database.manager import local_db, guardar_historico
from utils.common import normalizar_texto, procesar_subtotal, identificar_tipo_tienda, obtener_columna_piezas, obtener_columna_fecha
from utils.ui import add_back_button, show_module_header
from core.event_bus import emitir

# =============================================================================
# FUNCIONES DE NORMALIZACIÓN Y UTILIDADES (versiones mejoradas)
# =============================================================================



def identificar_tipo_tienda(nombre):
    """Identifica el tipo de tienda basado en el nombre normalizado"""
    try:
        if pd.isna(nombre) or nombre == "":
            return "DESCONOCIDO"
        nombre_upper = normalizar_texto(nombre)
        if "JOFRE" in nombre_upper and "SANTANA" in nombre_upper:
            return "VENTAS AL POR MAYOR"
        nombres_personales = ["ROCIO","ALEJANDRA","ANGELICA","DELGADO","CRUZ","LILIANA",
                              "SALAZAR","RICARDO","SANCHEZ","JAZMIN","ALVARADO","MELISSA",
                              "CHAVEZ","KARLA","SORIANO","ESTEFANIA","GUALPA","MARIA",
                              "JESSICA","PEREZ","LOYO"]
        palabras = nombre_upper.split()
        for palabra in palabras:
            if len(palabra) > 2 and palabra in nombres_personales:
                return "VENTA WEB"
        patrones_fisicas = ["LOCAL","AEROPOSTALE","MALL","PLAZA","SHOPPING","CENTRO",
                            "COMERCIAL","CC","C.C","TIENDA","SUCURSAL","PRICE","CLUB",
                            "DORADO","CIUDAD","RIOCENTRO","PASEO","PORTAL","SOL","CONDADO",
                            "CITY","CEIBOS","IBARRA","MATRIZ","BODEGA","FASHION","GYE",
                            "QUITO","MACHALA","PORTOVIEJO","BABAHOYO","MANTA","AMBATO",
                            "CUENCA","ALMACEN","PRATI"]
        for patron in patrones_fisicas:
            if patron in nombre_upper:
                return "TIENDA FÍSICA"
        if len(palabras) >= 3:
            return "TIENDA FÍSICA"
        elif any(len(p) > 3 for p in palabras):
            return "TIENDA FÍSICA"
        else:
            return "VENTA WEB"
    except Exception:
        return "DESCONOCIDO"



def obtener_columna_piezas(manifesto):
    posibles = ["PIEZAS","CANTIDAD","UNIDADES","QTY","CANT","PZS","BULTOS"]
    for col in manifesto.columns:
        col_upper = str(col).upper()
        for nombre in posibles:
            if nombre in col_upper:
                return col
    return None

def obtener_columna_fecha(manifesto):
    posibles = ["FECHA","FECHA ING","FECHA INGRESO","FECHA CREACION","FECHA_ING","FECHA_CREACION"]
    for col in manifesto.columns:
        col_upper = str(col).upper()
        for nombre in posibles:
            if nombre in col_upper:
                return col
    return None

# =============================================================================
# PROCESAMIENTO PRINCIPAL
# =============================================================================

def procesar_gastos(manifesto, facturas, config):
    """Procesa y valida gastos por tienda usando solo DESTINATARIO del MANIFIESTO"""
    try:
        # 1. PREPARAR MANIFIESTO
        st.info("📦 Procesando manifiesto...")
        columnas_manifesto = manifesto.columns.tolist()

        col_guia_m = config["guia_m"]
        if col_guia_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if "GUIA" in str(col).upper() or "GUÍA" in str(col).upper():
                    col_guia_m = col
                    break
            if col_guia_m not in columnas_manifesto:
                raise ValueError(f"No se encontró columna de guía en el manifiesto. Columnas: {columnas_manifesto}")

        col_subtotal_m = config.get("subtotal_m", "")
        if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if "SUBT" in str(col).upper() or "TOTAL" in str(col).upper() or "VALOR" in str(col).upper():
                    col_subtotal_m = col
                    break
            if not col_subtotal_m or col_subtotal_m not in columnas_manifesto:
                col_subtotal_m = columnas_manifesto[-1]

        col_ciudad_m = config.get("ciudad_destino", "")
        if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
            for col in columnas_manifesto:
                if "CIUDAD" in str(col).upper() or "DES" in str(col).upper() or "DESTINO" in str(col).upper():
                    col_ciudad_m = col
                    break
            if not col_ciudad_m or col_ciudad_m not in columnas_manifesto:
                col_ciudad_m = "CIUDAD"
                manifesto[col_ciudad_m] = "DESCONOCIDA"

        col_piezas_m = obtener_columna_piezas(manifesto)
        if col_piezas_m:
            st.info(f"✓ Columna de piezas detectada: {col_piezas_m}")
        else:
            st.warning("⚠ No se encontró columna de piezas. Se usará valor por defecto 1.")
            manifesto["PIEZAS"] = 1
            col_piezas_m = "PIEZAS"

        col_fecha_m = obtener_columna_fecha(manifesto)
        if col_fecha_m:
            st.info(f"✓ Columna de fecha detectada: {col_fecha_m}")
        else:
            st.warning("⚠ No se encontró columna de fecha. Se omitirá en reportes.")

        # Buscar destinatario en manifiesto
        col_destinatario_m = None
        posibles_dest = ["DESTINATARIO","CONSIGNATARIO","CLIENTE","NOMBRE","RAZON SOCIAL"]
        for col in posibles_dest:
            if col in columnas_manifesto:
                col_destinatario_m = col
                break
        if not col_destinatario_m:
            for col in columnas_manifesto:
                if any(p in str(col).upper() for p in ["DEST","CONSIG","CLIEN","NOMB","RAZON"]):
                    col_destinatario_m = col
                    break
        if not col_destinatario_m:
            manifesto["DESTINATARIO_MANIFIESTO"] = "TIENDA " + manifesto[col_ciudad_m].astype(str)
            col_destinatario_m = "DESTINATARIO_MANIFIESTO"

        # Otras columnas útiles
        otras_columnas = []
        for col in manifesto.columns:
            if any(p in str(col).upper() for p in ["FECHA","ORIGEN","SERVICIO","TRANSPORTE","PESO","FLETE"]):
                otras_columnas.append(col)

        columnas_seleccionadas = [col_guia_m, col_subtotal_m, col_ciudad_m, col_destinatario_m, col_piezas_m]
        if col_fecha_m:
            columnas_seleccionadas.append(col_fecha_m)
        columnas_seleccionadas += otras_columnas
        columnas_seleccionadas = list(dict.fromkeys(columnas_seleccionadas))

        df_m = manifesto[columnas_seleccionadas].copy()
        df_m["GUIA"] = df_m[col_guia_m].astype(str).str.strip()
        df_m["SUBTOTAL_MANIFIESTO"] = df_m[col_subtotal_m].apply(procesar_subtotal)
        df_m["CIUDAD_MANIFIESTO"] = df_m[col_ciudad_m].fillna("DESCONOCIDA").astype(str)
        df_m["DESTINATARIO_MANIFIESTO"] = df_m[col_destinatario_m].fillna("DESCONOCIDO").astype(str)
        df_m["PIEZAS_MANIFIESTO"] = pd.to_numeric(df_m[col_piezas_m], errors="coerce").fillna(1)
        if col_fecha_m:
            try:
                df_m["FECHA_MANIFIESTO"] = pd.to_datetime(df_m[col_fecha_m], errors="coerce")
            except:
                df_m["FECHA_MANIFIESTO"] = df_m[col_fecha_m].astype(str)
        df_m["GUIA_LIMPIA"] = df_m["GUIA"].str.upper()

        st.success(f"✓ Manifiesto procesado: {len(df_m):,} guías, {df_m['PIEZAS_MANIFIESTO'].sum():,.0f} piezas")

        # 2. PREPARAR FACTURAS
        st.info("🧾 Procesando facturas...")
        columnas_facturas = facturas.columns.tolist()
        col_guia_f = config["guia_f"]
        if col_guia_f not in columnas_facturas:
            for col in columnas_facturas:
                if "GUIA" in str(col).upper():
                    col_guia_f = col
                    break
            if col_guia_f not in columnas_facturas:
                raise ValueError(f"No se encontró columna de guía en facturas. Columnas: {columnas_facturas}")

        col_subtotal_f = config.get("subtotal", "")
        if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
            for col in columnas_facturas:
                if any(p in str(col).upper() for p in ["SUBTOTAL","TOTAL","IMPORTE","VALOR"]):
                    col_subtotal_f = col
                    break
            if not col_subtotal_f or col_subtotal_f not in columnas_facturas:
                col_subtotal_f = columnas_facturas[-1]

        df_f = facturas[[col_guia_f, col_subtotal_f]].copy()
        df_f["GUIA_FACTURA"] = df_f[col_guia_f].astype(str).str.strip()
        df_f["SUBTOTAL_FACTURA"] = df_f[col_subtotal_f].apply(procesar_subtotal)
        df_f["GUIA_LIMPIA"] = df_f["GUIA_FACTURA"].str.upper()
        st.success(f"✓ Facturas procesadas: {len(df_f):,} registros")

        # 3. UNIR DATOS
        st.info("🔗 Uniendo datos por guía...")
        df_completo = pd.merge(df_m, df_f[["GUIA_LIMPIA","SUBTOTAL_FACTURA"]], on="GUIA_LIMPIA", how="left")
        df_completo["DESTINATARIO"] = df_completo["DESTINATARIO_MANIFIESTO"]
        df_completo["CIUDAD"] = df_completo["CIUDAD_MANIFIESTO"]
        df_completo["PIEZAS"] = df_completo["PIEZAS_MANIFIESTO"]
        df_completo["ESTADO"] = df_completo["SUBTOTAL_FACTURA"].apply(lambda x: "FACTURADA" if pd.notna(x) and float(x)>0 else "ANULADA")
        df_completo["SUBTOTAL"] = df_completo["SUBTOTAL_FACTURA"].fillna(0)
        df_completo["DIFERENCIA"] = df_completo["SUBTOTAL_MANIFIESTO"] - df_completo["SUBTOTAL"]
        df_completo["TIPO"] = df_completo["DESTINATARIO"].apply(identificar_tipo_tienda)
        df_completo["NOMBRE_NORMALIZADO"] = df_completo["DESTINATARIO"].apply(normalizar_texto)

        def crear_grupo(fila):
            tipo = fila["TIPO"]
            nombre = fila["NOMBRE_NORMALIZADO"]
            ciudad = normalizar_texto(fila["CIUDAD"])
            if tipo == "VENTA WEB":
                palabras = nombre.split()
                if len(palabras) >= 2:
                    return f"VENTA WEB - {palabras[0]} {palabras[1]}"
                return f"VENTA WEB - {nombre}"
            elif tipo == "VENTAS AL POR MAYOR":
                return "VENTAS AL POR MAYOR - JOFRE SANTANA"
            elif tipo == "TIENDA FÍSICA":
                grupo_ciudad = f"{ciudad} - " if ciudad != "DESCONOCIDA" else ""
                palabras = nombre.split()
                if palabras:
                    nombre_grupo = " ".join(palabras[:min(3,len(palabras))])
                    return f"{grupo_ciudad}{nombre_grupo}"
                return f"{grupo_ciudad}TIENDA"
            else:
                return f"DESCONOCIDO - {nombre[:20]}"

        df_completo["GRUPO"] = df_completo.apply(crear_grupo, axis=1)
        guias_facturadas = df_completo[df_completo["ESTADO"]=="FACTURADA"].shape[0]
        guias_anuladas = df_completo[df_completo["ESTADO"]=="ANULADA"].shape[0]
        total_piezas = df_completo["PIEZAS"].sum()
        guias_anuladas_df = df_completo[df_completo["ESTADO"]=="ANULADA"].copy()
        st.success(f"✓ Datos unidos: {len(df_completo):,} registros (facturadas: {guias_facturadas:,}, anuladas: {guias_anuladas:,})")

        # 4. MÉTRICAS POR GRUPO (solo facturadas)
        st.info("📊 Calculando métricas por grupo...")
        df_facturadas = df_completo[df_completo["ESTADO"]=="FACTURADA"]
        metricas = df_facturadas.groupby("GRUPO").agg(
            GUIAS=("GUIA_LIMPIA","count"),
            PIEZAS=("PIEZAS","sum"),
            SUBTOTAL=("SUBTOTAL","sum"),
            SUBTOTAL_MANIFIESTO=("SUBTOTAL_MANIFIESTO","sum"),
            DIFERENCIA=("DIFERENCIA","sum"),
            DESTINATARIOS=("DESTINATARIO",lambda x: ", ".join(sorted(set(str(d) for d in x if pd.notna(d)))[:5])),
            CIUDADES=("CIUDAD",lambda x: ", ".join(sorted(set(str(c) for c in x if pd.notna(c)))[:3])),
            TIPO=("TIPO",lambda x: x.mode()[0] if not x.mode().empty else "DESCONOCIDO")
        ).reset_index()
        total_general = metricas["SUBTOTAL"].sum()
        if total_general>0:
            metricas["PORCENTAJE"] = (metricas["SUBTOTAL"]/total_general*100).round(2)
            metricas["PROMEDIO_POR_PIEZA"] = (metricas["SUBTOTAL"]/metricas["PIEZAS"]).round(2)
        else:
            metricas["PORCENTAJE"] = 0.0
            metricas["PROMEDIO_POR_PIEZA"] = 0.0
        metricas["PIEZAS_POR_GUIA"] = (metricas["PIEZAS"]/metricas["GUIAS"]).round(2)
        metricas = metricas.sort_values("SUBTOTAL", ascending=False)
        st.success(f"✓ {len(metricas)} grupos identificados")

        # 5. RESUMEN POR TIPO
        resumen = df_facturadas.groupby("TIPO").agg(
            TIENDAS=("GRUPO","nunique"),
            GUIAS=("GUIA_LIMPIA","count"),
            PIEZAS=("PIEZAS","sum"),
            SUBTOTAL=("SUBTOTAL","sum")
        ).reset_index()
        if total_general>0:
            resumen["PORCENTAJE"] = (resumen["SUBTOTAL"]/total_general*100).round(2)
        else:
            resumen["PORCENTAJE"] = 0.0
        resumen = resumen.sort_values("SUBTOTAL", ascending=False)

        # 6. VALIDACIÓN
        total_manifiesto = df_completo["SUBTOTAL_MANIFIESTO"].sum()
        total_facturas = df_completo["SUBTOTAL"].sum()
        validacion = {
            "total_manifiesto": total_manifiesto,
            "total_facturas": total_facturas,
            "diferencia": abs(total_manifiesto - total_facturas),
            "porcentaje": (abs(total_manifiesto - total_facturas)/total_manifiesto*100) if total_manifiesto>0 else 0,
            "coincide": abs(total_manifiesto - total_facturas) < 0.01,
            "guias_procesadas": len(df_completo),
            "guias_facturadas": guias_facturadas,
            "guias_anuladas": guias_anuladas,
            "piezas_totales": total_piezas,
            "grupos_identificados": len(metricas),
            "porcentaje_facturadas": (guias_facturadas/len(df_completo)*100) if len(df_completo)>0 else 0,
            "porcentaje_anuladas": (guias_anuladas/len(df_completo)*100) if len(df_completo)>0 else 0
        }
        st.success("✅ Validación completada")
        return df_completo, metricas, resumen, validacion, guias_anuladas_df
    except Exception as e:
        st.error(f"Error en procesamiento: {str(e)}")
        raise

# =============================================================================
# GENERACIÓN DE EXCEL CON FORMATO EXACTO
# =============================================================================

def generar_excel_con_formato_exacto(metricas_filt, resultado, guias_anuladas, manifesto_original, filtros_aplicados=None):
    try:
        output = BytesIO()
        wb = Workbook()
        # Hoja 1: Reporte
        ws1 = wb.active
        ws1.title = "Reporte"
        hoja1_data = metricas_filt[["GRUPO","SUBTOTAL"]].copy().sort_values("GRUPO")
        ws1.append(["",""])
        ws1.append(["",""])
        ws1.append(["Etiquetas de fila","Suma de SUBTOTAL"])
        for _,row in hoja1_data.iterrows():
            ws1.append([row["GRUPO"], row["SUBTOTAL"]])
        ws1.append(["Total general", hoja1_data["SUBTOTAL"].sum()])
        for row in ws1.iter_rows(min_row=3, max_row=ws1.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
        for cell in ws1[3]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(4, ws1.max_row+1):
            ws1.cell(row=row, column=2).number_format = "#,##0.00"
        ws1.column_dimensions["A"].width = 50
        ws1.column_dimensions["B"].width = 20

        # Hoja 2: Tiendas
        ws2 = wb.create_sheet(title="Tiendas")
        columnas = ["GRUPO","GUIAS","PIEZAS","SUBTOTAL","DESTINATARIOS","CIUDADES","TIPO","PORCENTAJE","PROMEDIO_POR_PIEZA","PIEZAS_POR_GUIA"]
        ws2.append(columnas)
        for _,row in metricas_filt.iterrows():
            ws2.append([row["GRUPO"], int(row["GUIAS"]), int(row["PIEZAS"]), row["SUBTOTAL"], row["DESTINATARIOS"], row["CIUDADES"], row["TIPO"], row["PORCENTAJE"], row["PROMEDIO_POR_PIEZA"], row["PIEZAS_POR_GUIA"]])
        ws2.append([""]*len(columnas))
        ult_fila = ws2.max_row - 1
        ws2.append(["Total general","","",f"=SUBTOTAL(109,D2:D{ult_fila})","","","","","",""])
        for row in ws2.iter_rows(min_row=1, max_row=ws2.max_row, min_col=1, max_col=len(columnas)):
            for cell in row:
                cell.border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
        for cell in ws2[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(2, ws2.max_row+1):
            ws2.cell(row=row, column=4).number_format = "#,##0.00"
            ws2.cell(row=row, column=8).number_format = "0.00"
            ws2.cell(row=row, column=9).number_format = "0.00"
            ws2.cell(row=row, column=10).number_format = "0.00"
        for cell in ws2[ws2.max_row]:
            cell.font = Font(bold=True)
        anchos = [40,10,10,15,50,20,20,15,20,20]
        for i,ancho in enumerate(anchos,1):
            ws2.column_dimensions[get_column_letter(i)].width = ancho

        # Hoja 3: Guías Anuladas
        if not guias_anuladas.empty:
            ws3 = wb.create_sheet(title="Guias Anuladas")
            cols_anuladas = ["FECHA_MANIFIESTO","GUIA","ORIGEN","GUIA2","DESTINATARIO_MANIFIESTO","SERVICIO","TRANSPORTE","PIEZAS_MANIFIESTO","PESO","FLETE","SUBTOTAL_MANIFIESTO","CIUDAD_MANIFIESTO","ESTADO"]
            cols_existentes = [c for c in cols_anuladas if c in guias_anuladas.columns]
            mapeo = {"FECHA_MANIFIESTO":"FECHA","DESTINATARIO_MANIFIESTO":"DESTINATARIO","PIEZAS_MANIFIESTO":"NUMERO DE PIEZAS","SUBTOTAL_MANIFIESTO":"SUBTOTAL","CIUDAD_MANIFIESTO":"CIUDAD"}
            col_nombres = [mapeo.get(c,c) for c in cols_existentes]
            ws3.append(col_nombres)
            for _,row in guias_anuladas.iterrows():
                fila = []
                for oc in cols_existentes:
                    val = row[oc]
                    if oc=="FECHA_MANIFIESTO" and pd.notna(val) and hasattr(val,"strftime"):
                        fila.append(val.strftime("%d/%m/%Y %H:%M"))
                    elif oc in ["PIEZAS_MANIFIESTO"]:
                        fila.append(int(val) if pd.notna(val) else 0)
                    elif oc in ["SUBTOTAL_MANIFIESTO"]:
                        fila.append(float(val) if pd.notna(val) else 0.0)
                    else:
                        fila.append(val if pd.notna(val) else "")
                ws3.append(fila)
            ws3.append([""]*len(col_nombres))
            fila_total = [""]*len(col_nombres)
            if "NUMERO DE PIEZAS" in col_nombres:
                idx = col_nombres.index("NUMERO DE PIEZAS")+1
                fila_total[idx-1] = f"=SUBTOTAL(109,{get_column_letter(idx)}2:{get_column_letter(idx)}{ws3.max_row-1})"
            if "SUBTOTAL" in col_nombres:
                idx = col_nombres.index("SUBTOTAL")+1
                fila_total[idx-1] = f"=SUBTOTAL(109,{get_column_letter(idx)}2:{get_column_letter(idx)}{ws3.max_row-1})"
            ws3.append(fila_total)
            for row in ws3.iter_rows(min_row=1, max_row=ws3.max_row, min_col=1, max_col=len(col_nombres)):
                for cell in row:
                    cell.border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
            for cell in ws3[1]:
                cell.fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")
            for row in range(2, ws3.max_row+1):
                if "NUMERO DE PIEZAS" in col_nombres:
                    idx = col_nombres.index("NUMERO DE PIEZAS")+1
                    ws3.cell(row=row, column=idx).number_format = "0"
                if "SUBTOTAL" in col_nombres:
                    idx = col_nombres.index("SUBTOTAL")+1
                    ws3.cell(row=row, column=idx).number_format = "#,##0.00"
            for i,ancho in enumerate([18,15,15,20,15,40,15,15,15,10,10,15,20,15][:len(col_nombres)]):
                ws3.column_dimensions[get_column_letter(i+1)].width = ancho

        # Hoja 4: Detalle
        ws4 = wb.create_sheet(title="Detalle")
        cols_detalle = []
        if "FECHA_MANIFIESTO" in resultado.columns:
            cols_detalle.append("FECHA_MANIFIESTO")
        cols_detalle += ["GUIA","ESTADO","GRUPO","DESTINATARIO","CIUDAD","PIEZAS","SUBTOTAL_MANIFIESTO","SUBTOTAL","DIFERENCIA","TIPO"]
        cols_detalle = [c for c in cols_detalle if c in resultado.columns]
        detalle_df = resultado[cols_detalle].copy()
        mapeo_det = {"FECHA_MANIFIESTO":"FECHA","GUIA":"GUIA","ESTADO":"ESTADO","GRUPO":"GRUPO","DESTINATARIO":"DESTINATARIO","CIUDAD":"CIUDAD","PIEZAS":"PIEZAS","SUBTOTAL_MANIFIESTO":"SUBTOTAL MANIFIESTO","SUBTOTAL":"SUBTOTAL FACTURA","DIFERENCIA":"DIFERENCIA","TIPO":"TIPO"}
        detalle_df = detalle_df.rename(columns={k:v for k,v in mapeo_det.items() if k in detalle_df.columns})
        ws4.append(list(detalle_df.columns))
        for _,row in detalle_df.iterrows():
            fila = []
            for col in detalle_df.columns:
                val = row[col]
                if col=="FECHA" and pd.notna(val) and hasattr(val,"strftime"):
                    fila.append(val.strftime("%d/%m/%Y %H:%M"))
                elif col=="PIEZAS":
                    fila.append(int(val) if pd.notna(val) else 0)
                elif col in ["SUBTOTAL MANIFIESTO","SUBTOTAL FACTURA","DIFERENCIA"]:
                    fila.append(float(val) if pd.notna(val) else 0.0)
                else:
                    fila.append(val if pd.notna(val) else "")
            ws4.append(fila)
        for row in ws4.iter_rows(min_row=1, max_row=ws4.max_row, min_col=1, max_col=len(detalle_df.columns)):
            for cell in row:
                cell.border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
        for cell in ws4[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(2, ws4.max_row+1):
            for i,col in enumerate(detalle_df.columns,1):
                if col=="PIEZAS":
                    ws4.cell(row=row, column=i).number_format = "0"
                elif col in ["SUBTOTAL MANIFIESTO","SUBTOTAL FACTURA","DIFERENCIA"]:
                    ws4.cell(row=row, column=i).number_format = "#,##0.00"
        anchos_det = [20,15,12,40,30,20,10,15,15,15,20]
        for i,ancho in enumerate(anchos_det[:len(detalle_df.columns)]):
            ws4.column_dimensions[get_column_letter(i+1)].width = ancho

        # Hoja 5: Filtros
        if filtros_aplicados:
            ws5 = wb.create_sheet(title="Filtros Aplicados")
            ws5.append(["Filtro","Valor"])
            for k,v in filtros_aplicados.items():
                ws5.append([k,str(v)])
            for row in ws5.iter_rows(min_row=1, max_row=ws5.max_row, min_col=1, max_col=2):
                for cell in row:
                    cell.border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
            for cell in ws5[1]:
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
                cell.alignment = Alignment(horizontal="center")
            ws5.column_dimensions["A"].width = 30
            ws5.column_dimensions["B"].width = 50

        wb.save(output)
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Error generando Excel: {str(e)}")
        return None

# =============================================================================
# GENERACIÓN DE PDF
# =============================================================================

def generar_pdf_reporte(metricas, resumen, validacion, filtros_aplicados=None):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import grey, whitesmoke, beige, black
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name

        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=16, spaceAfter=12, alignment=1)
        subtitle_style = ParagraphStyle("CustomSubtitle", parent=styles["Heading2"], fontSize=12, spaceAfter=6)
        normal_style = styles["Normal"]

        elements.append(Paragraph("REPORTE EJECUTIVO - GESTIÓN DE GASTOS POR TIENDA", title_style))
        elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
        elements.append(Spacer(1,12))

        elements.append(Paragraph("MÉTRICAS PRINCIPALES", subtitle_style))
        metricas_data = [
            ["Total Facturado", f"${validacion['total_facturas']:,.2f}"],
            ["Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}"],
            ["Diferencia", f"${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%)"],
            ["Guías Procesadas", f"{validacion['guias_procesadas']:,}"],
            ["Guías Facturadas", f"{validacion['guias_facturadas']:,} ({validacion['porcentaje_facturadas']:.1f}%)"],
            ["Guías Anuladas", f"{validacion['guias_anuladas']:,} ({validacion['porcentaje_anuladas']:.1f}%)"],
            ["Piezas Totales", f"{validacion['piezas_totales']:,}"],
            ["Grupos Identificados", f"{validacion['grupos_identificados']:,}"]
        ]
        metricas_table = Table(metricas_data, colWidths=[200,150])
        metricas_table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),grey), ("TEXTCOLOR",(0,0),(-1,0),whitesmoke),
            ("ALIGN",(0,0),(-1,-1),"CENTER"), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,0),12),
            ("BACKGROUND",(0,1),(-1,-1),beige), ("GRID",(0,0),(-1,-1),1,black)
        ]))
        elements.append(metricas_table)
        elements.append(Spacer(1,20))

        elements.append(Paragraph("RESUMEN POR TIPO DE TIENDA", subtitle_style))
        if not resumen.empty:
            resumen_data = [["TIPO","TIENDAS","GUÍAS","PIEZAS","SUBTOTAL","%"]]
            for _,row in resumen.iterrows():
                resumen_data.append([row["TIPO"], str(int(row["TIENDAS"])), str(int(row["GUIAS"])), str(int(row["PIEZAS"])), f"${row['SUBTOTAL']:,.2f}", f"{row['PORCENTAJE']:.2f}%"])
            resumen_table = Table(resumen_data, colWidths=[120,80,80,80,100,80])
            resumen_table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),grey), ("TEXTCOLOR",(0,0),(-1,0),whitesmoke),
                ("ALIGN",(0,0),(-1,-1),"CENTER"), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,0),12),
                ("BACKGROUND",(0,1),(-1,-1),beige), ("GRID",(0,0),(-1,-1),1,black)
            ]))
            elements.append(resumen_table)
        elements.append(Spacer(1,20))

        elements.append(Paragraph("TOP 15 GRUPOS POR GASTO", subtitle_style))
        if not metricas.empty:
            top15 = metricas.head(15)
            grupos_data = [["GRUPO","GUÍAS","PIEZAS","SUBTOTAL","%","PROM/PIEZA"]]
            for _,row in top15.iterrows():
                grupo = row["GRUPO"][:30] + "..." if len(row["GRUPO"])>30 else row["GRUPO"]
                grupos_data.append([grupo, str(int(row["GUIAS"])), str(int(row["PIEZAS"])), f"${row['SUBTOTAL']:,.2f}", f"{row['PORCENTAJE']:.2f}%", f"${row['PROMEDIO_POR_PIEZA']:,.2f}"])
            grupos_table = Table(grupos_data, colWidths=[150,60,60,90,60,80])
            grupos_table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),grey), ("TEXTCOLOR",(0,0),(-1,0),whitesmoke),
                ("ALIGN",(0,0),(-1,-1),"CENTER"), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,0),12),
                ("BACKGROUND",(0,1),(-1,-1),beige), ("GRID",(0,0),(-1,-1),1,black)
            ]))
            elements.append(grupos_table)

        elements.append(Spacer(1,20))
        elements.append(Paragraph("ANÁLISIS EJECUTIVO", subtitle_style))
        analisis = f"""
        <b>Validación:</b> {"✅ COINCIDENCIA EXACTA" if validacion["coincide"] else "⚠ CON DIFERENCIAS"}<br/>
        <b>Facturación:</b> {validacion["porcentaje_facturadas"]:.1f}% de guías facturadas ({validacion["guias_facturadas"]:,})<br/>
        <b>Anulaciones:</b> {validacion["porcentaje_anuladas"]:.1f}% de guías anuladas ({validacion["guias_anuladas"]:,})<br/>
        <b>Distribución:</b> {resumen.iloc[0]["TIPO"] if not resumen.empty else "N/A"} representa el {resumen.iloc[0]["PORCENTAJE"] if not resumen.empty else 0:.1f}%<br/>
        <b>Eficiencia:</b> Promedio de {validacion['piezas_totales']/validacion['guias_procesadas']:.1f} piezas/guía<br/>
        <b>Recomendación:</b> {"Revisar guías anuladas" if validacion["guias_anuladas"]>0 else "Proceso eficiente"}
        """
        elements.append(Paragraph(analisis, normal_style))
        doc.build(elements)
        return pdf_path
    except ImportError:
        st.warning("Librería 'reportlab' no instalada. No se puede generar PDF.")
        return None
    except Exception as e:
        st.error(f"Error generando PDF: {str(e)}")
        return None

# =============================================================================
# FUNCIONES DE CARGA Y EVENTOS
# =============================================================================

def cargar_archivo_local(file, nombre):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8')
        else:
            df = pd.read_excel(file, engine='openpyxl')
        st.markdown(f'<div class="alert-success">✓ {nombre} cargado exitosamente</div>', unsafe_allow_html=True)
        return df
    except Exception as e:
        st.markdown(f'<div class="alert-error">Error al cargar {nombre}: {str(e)}</div>', unsafe_allow_html=True)
        return None

def procesar_gastos_reconciliacion(manifesto, facturas, config):
    try:
        df_completo, metricas, resumen, validacion, guias_anuladas_df = procesar_gastos(manifesto, facturas, config)
        # Emitir evento de reconciliación completada
        try:
            emitir("RECONCILIACION_COMPLETADA", {
                "total_manifiesto": validacion["total_manifiesto"],
                "total_facturas": validacion["total_facturas"],
                "diferencia": validacion["diferencia"],
                "guias_procesadas": validacion["guias_procesadas"],
                "guias_facturadas": validacion["guias_facturadas"],
                "guias_anuladas": validacion["guias_anuladas"],
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            pass
        return df_completo, metricas, resumen, validacion, guias_anuladas_df
    except Exception as e:
        st.error(f"Error en el procesamiento: {str(e)}")
        raise

# =============================================================================
# INTERFAZ DE USUARIO (STREAMLIT)
# =============================================================================

def show_reconciliacion():
    add_back_button(key="back_reconciliacion")
    show_module_header("💰 Gestión de Gastos por Tienda", "Conciliación financiera y análisis de facturas")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Manifiesto de Envíos")
        manifesto_file = st.file_uploader("Subir manifiesto (Excel/CSV)", type=['xlsx','csv'], key="manifesto_reconciliacion")
    with col2:
        st.subheader("🧾 Facturas")
        facturas_file = st.file_uploader("Subir facturas (Excel/CSV)", type=['xlsx','csv'], key="facturas_reconciliacion")

    if manifesto_file and facturas_file:
        manifesto = cargar_archivo_local(manifesto_file, "Manifiesto")
        facturas = cargar_archivo_local(facturas_file, "Facturas")
        if manifesto is not None and facturas is not None:
            st.subheader("🔧 Configuración de columnas")
            col_guia_m = st.selectbox("Columna de Guía en Manifiesto", manifesto.columns, index=0 if "guia" in str(manifesto.columns[0]).lower() else 0)
            col_guia_f = st.selectbox("Columna de Guía en Facturas", facturas.columns, index=0 if "guia" in str(facturas.columns[0]).lower() else 0)
            config = {
                "guia_m": col_guia_m,
                "guia_f": col_guia_f,
                "subtotal_m": None,
                "subtotal": None,
                "ciudad_destino": None
            }
            if st.button("🚀 Procesar Conciliación", type="primary"):
                with st.spinner("Procesando datos..."):
                    try:
                        resultado, metricas, resumen, validacion, guias_anuladas = procesar_gastos_reconciliacion(manifesto, facturas, config)
                        st.session_state['reconciliacion_resultado'] = resultado
                        st.session_state['reconciliacion_metricas'] = metricas
                        st.session_state['reconciliacion_resumen'] = resumen
                        st.session_state['reconciliacion_validacion'] = validacion
                        st.session_state['reconciliacion_anuladas'] = guias_anuladas
                        st.session_state['reconciliacion_manifesto'] = manifesto
                        st.success("✅ Procesamiento completado")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    if 'reconciliacion_resultado' in st.session_state:
        resultado = st.session_state['reconciliacion_resultado']
        metricas = st.session_state['reconciliacion_metricas']
        resumen = st.session_state['reconciliacion_resumen']
        validacion = st.session_state['reconciliacion_validacion']
        guias_anuladas = st.session_state['reconciliacion_anuladas']
        manifesto_original = st.session_state['reconciliacion_manifesto']

        # Mostrar validación
        st.subheader("📊 Validación de Datos")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}")
        col2.metric("Total Facturas", f"${validacion['total_facturas']:,.2f}")
        col3.metric("Diferencia", f"${validacion['diferencia']:,.2f}", delta=f"{validacion['porcentaje']:.2f}%")
        col4.metric("Guías Anuladas", f"{validacion['guias_anuladas']:,}", delta=f"{validacion['porcentaje_anuladas']:.1f}%", delta_color="inverse")

        # Gráficos
        tab1, tab2, tab3 = st.tabs(["📈 Top Grupos", "🥧 Distribución por Tipo", "📅 Evolución Temporal"])
        with tab1:
            top_n = st.slider("Mostrar top N grupos", 5, 20, 10)
            fig_bar = px.bar(metricas.head(top_n), x="GRUPO", y="SUBTOTAL", title=f"Top {top_n} Grupos por Gasto", text_auto='.2s', color="TIPO")
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        with tab2:
            fig_pie = px.pie(resumen, values="SUBTOTAL", names="TIPO", title="Distribución de Gastos por Tipo de Tienda", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with tab3:
            if "FECHA_MANIFIESTO" in resultado.columns:
                fecha_agrup = resultado.groupby(resultado["FECHA_MANIFIESTO"].dt.date)["SUBTOTAL"].sum().reset_index()
                fig_line = px.line(fecha_agrup, x="FECHA_MANIFIESTO", y="SUBTOTAL", title="Evolución Temporal de Gastos")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No se encontró columna de fecha para evolución temporal.")

        # Descargas
        st.subheader("⬇️ Descargar Reportes")
        col_excel, col_pdf = st.columns(2)
        with col_excel:
            excel_data = generar_excel_con_formato_exacto(metricas, resultado, guias_anuladas, manifesto_original, {"Tipo":"Reconciliación"})
            if excel_data:
                st.download_button("📥 Descargar Excel", data=excel_data, file_name=f"reconciliacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="excel_download")
        with col_pdf:
            pdf_path = generar_pdf_reporte(metricas, resumen, validacion)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Descargar PDF", data=f, file_name=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf", key="pdf_download")

        # Mostrar tablas
        with st.expander("📋 Ver métricas detalladas por grupo"):
            st.dataframe(metricas.style.format({
                "SUBTOTAL": "${:,.2f}",
                "SUBTOTAL_MANIFIESTO": "${:,.2f}",
                "DIFERENCIA": "${:,.2f}",
                "PORCENTAJE": "{:.2f}%",
                "PROMEDIO_POR_PIEZA": "${:,.2f}",
                "PIEZAS_POR_GUIA": "{:.2f}"
            }))
        if not guias_anuladas.empty:
            with st.expander(f"⚠️ Guías Anuladas ({len(guias_anuladas)} registros)"):
                st.dataframe(guias_anuladas[["GUIA","DESTINATARIO","CIUDAD","SUBTOTAL_MANIFIESTO"]].head(100))

    st.markdown('</div>', unsafe_allow_html=True)

def show_reconciliacion_v8():
    show_reconciliacion()


# =============================================================================
# MÓDULO DE AUDITORÍA DE CORREOS
# =============================================================================
def show_auditoria_correos():
    """Panel de auditoría de correos y comunicaciones logísticas."""
    from utils.roles import can_access
    if not can_access("auditoria_correos"):
        st.error("⛔ No tienes permisos para acceder")
        return

    add_back_button(key="back_auditoria")
    show_module_header("📬 Auditoría de Correos", "Registro de comunicaciones y alertas automáticas")

    tab1, tab2 = st.tabs(["📬 Alertas Recientes", "📜 Historial Completo"])

    with tab1:
        st.markdown("### 🔔 Notificaciones y Alertas")
        notificaciones = local_db.find(
            "notificaciones",
            {"leida": False},
            sort=[("fecha", -1)],
            limit=30
        )
        if notificaciones:
            df_not = pd.DataFrame(notificaciones)
            cols_show = ["fecha", "mensaje", "modulo", "tipo"]
            cols_exist = [c for c in cols_show if c in df_not.columns]
            df_show = df_not[cols_exist].copy()
            if "fecha" in df_show.columns:
                df_show["fecha"] = df_show["fecha"].astype(str).str[:19]
            st.dataframe(df_show, use_container_width=True)

            if st.button("✅ Marcar todas como leídas"):
                local_db.update("notificaciones", {"leida": False}, {"$set": {"leida": True}})
                st.success("Todas las notificaciones marcadas como leídas")
                st.rerun()
        else:
            st.info("✅ No hay notificaciones pendientes")

    with tab2:
        st.markdown("### 📜 Registro de Auditoría")
        auditoria = local_db.find("auditoria", {}, sort=[("timestamp", -1)], limit=100)
        if auditoria:
            df_aud = pd.DataFrame(auditoria)
            cols_show = ["timestamp", "usuario", "accion", "modulo", "detalle"]
            cols_exist = [c for c in cols_show if c in df_aud.columns]
            df_show = df_aud[cols_exist].copy()
            if "timestamp" in df_show.columns:
                df_show["timestamp"] = df_show["timestamp"].astype(str).str[:19]
            st.dataframe(df_show, use_container_width=True)
            st.caption(f"Total: {len(auditoria)} registros de auditoría")
        else:
            st.info("No hay registros de auditoría aún")
