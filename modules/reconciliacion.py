# modules/reconciliacion.py
# ==============================================================================
# MÓDULO DE RECONCILIACIÓN FINANCIERA - VERSIÓN CORREGIDA (CRUCE DE GUÍAS)
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
import tempfile
import re
import unicodedata
import logging
from typing import Optional
from io import BytesIO

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import grey, whitesmoke, beige, black

from openpyxl import Workbook
from openpyxl.styles import Border, Side, PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

from database.manager import local_db
from utils.ui import add_back_button, show_module_header

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# CONSTANTES Y DATOS DE TIENDAS
# ------------------------------------------------------------------------------
TIENDAS_DATA = [
    {"Nombre de Tienda": "Aeropostale - (Cuenca) Mall del Rio", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "CUENCA", "Contacto": "Marco Eras", "Dirección": "Av. Felipe II y Autopista Sur - CC Mall del Rio", "Teléfono": "994570933"},
    {"Nombre de Tienda": "Aeropostale - 6 de Diciembre", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "QUITO", "Contacto": "Micaela Yépez", "Dirección": "Av. 6 de Diciembre y Thomas de Berlanga CC Riocentro UIO", "Teléfono": "987883889"},
    {"Nombre de Tienda": "Aeropostale - Paseo Ambato", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "AMBATO", "Contacto": "Franco Torres", "Dirección": "Manuelita Saenz y Pio Baroja, cerca al parque de las Flores CC Paseo Shopping", "Teléfono": "984951515"},
    {"Nombre de Tienda": "Price Club - Ibarra", "Empresa": "Aeropostale", "Origen": "MATRIZ", "Destino": "IBARRA", "Contacto": "Silvia Urcuango", "Dirección": "Av. Victor Gómez Jurado y Rodrigo Miño junto a la cancha La Bombonera", "Teléfono": "982649058"},
]

PRICE_CLUBS = ["Price Club - Portoviejo", "Price Club - Machala", "Price Club - Guayaquil", "Price Club - Ibarra", "Price Club - Cuenca"]
TIENDAS_REGULARES = ['AERO CCI', 'AERO DAULE', 'AERO LAGO AGRIO', 'AERO MALL DEL RIO GYE', 'AERO PLAYAS', 'AEROPOSTALE 6 DE DICIEMBRE', 'AEROPOSTALE BOMBOLI', 'AEROPOSTALE CAYAMBE', 'AEROPOSTALE EL COCA', 'AEROPOSTALE PASAJE', 'AEROPOSTALE PEDERNALES', 'AMBATO', 'BABAHOYO', 'BAHIA DE CARAQUEZ', 'CARAPUNGO', 'CEIBOS', 'CONDADO SHOPPING', 'CUENCA', 'DURAN', 'LA PLAZA SHOPPING', 'MACHALA', 'MAL DEL SUR', 'MALL DEL PACIFICO', 'MALL DEL SOL', 'MANTA', 'MILAGRO', 'MULTIPLAZA RIOBAMBA', 'PASEO AMBATO', 'PENINSULA', 'PORTOVIEJO', 'QUEVEDO', 'RIOBAMBA', 'RIOCENTRO EL DORADO', 'RIOCENTRO NORTE', 'SAN LUIS', 'SANTO DOMINGO']
VENTAS_POR_MAYOR = ["VENTAS POR MAYOR", "MAYORISTA"]
TIENDA_WEB = ["TIENDA WEB", "WEB", "TIENDA MOVIL", "MOVIL"]
FALLAS = ["FALLAS"]
COLORS = {
    'PRICE CLUB': '#0033A0',
    'TIENDAS AEROPOSTALE': '#E4002B',
    'VENTAS POR MAYOR': '#10B981',
    'TIENDA WEB': '#8B5CF6',
    'FALLAS': '#F59E0B',
    'FUNDAS': '#EC4899'
}

# ------------------------------------------------------------------------------
# FUNCIONES AUXILIARES (CORREGIDAS)
# ------------------------------------------------------------------------------
def normalizar_texto(texto) -> str:
    if pd.isna(texto) or texto == "": return ""
    texto = str(texto)
    try:
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    except Exception:
        texto = texto.upper()
    texto = re.sub(r"[^A-Za-z0-9\s]", " ", texto.upper())
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def procesar_subtotal(valor) -> float:
    """Convierte a float cualquier valor de subtotal, manejando comas y puntos."""
    if pd.isna(valor): return 0.0
    try:
        if isinstance(valor, (int, float, np.number)): return float(valor)
        valor_str = str(valor).strip()
        # Reemplazar coma decimal por punto (si es el último separador)
        if ',' in valor_str and '.' in valor_str:
            if valor_str.rfind(',') > valor_str.rfind('.'):
                valor_str = valor_str.replace('.', '').replace(',', '.')
            else:
                valor_str = valor_str.replace(',', '')
        elif ',' in valor_str:
            valor_str = valor_str.replace(',', '.')
        # Eliminar cualquier caracter no numérico excepto punto y signo menos
        valor_str = re.sub(r"[^\d.-]", "", valor_str)
        return float(valor_str) if valor_str else 0.0
    except Exception:
        return 0.0

def limpiar_guia(valor) -> str:
    """
    Limpia el número de guía:
    - Convierte a string sin decimales (elimina .0 final)
    - Elimina espacios y caracteres no alfanuméricos
    - Convierte a mayúsculas
    """
    if pd.isna(valor):
        return ""
    # Convertir a string y eliminar posibles .0 de números enteros leídos como float
    s = str(valor).strip()
    if s.endswith('.0'):
        s = s[:-2]
    # Eliminar caracteres no alfanuméricos (incluyendo espacios, guiones, puntos, etc.)
    s = re.sub(r"[^A-Za-z0-9]", "", s)
    return s.upper()

def obtener_columna_piezas(df: pd.DataFrame) -> Optional[str]:
    posibles = ["PIEZAS", "CANTIDAD", "UNIDADES", "QTY", "CANT", "PZS", "BULTOS", "PIEZA"]
    for col in df.columns:
        if any(p in str(col).upper() for p in posibles):
            return col
    return None

def obtener_columna_fecha(df: pd.DataFrame) -> Optional[str]:
    posibles = ["FECHA", "FECHA ING", "FECHA INGRESO", "FECHA CREACION", "FECHA_ING", "FECHA_CREACION"]
    for col in df.columns:
        if any(p in str(col).upper() for p in posibles):
            return col
    return None

def identificar_tipo_tienda(nombre) -> str:
    if pd.isna(nombre) or nombre == "": return "DESCONOCIDO"
    nombre_upper = normalizar_texto(nombre)
    if "JOFRE" in nombre_upper and "SANTANA" in nombre_upper:
        return "VENTAS AL POR MAYOR"
    nombres_personales = ["ROCIO","ALEJANDRA","ANGELICA","DELGADO","CRUZ","LILIANA",
                          "SALAZAR","RICARDO","SANCHEZ","JAZMIN","ALVARADO","MELISSA",
                          "CHAVEZ","KARLA","SORIANO","ESTEFANIA","GUALPA","MARIA",
                          "JESSICA","PEREZ","LOYO"]
    palabras = nombre_upper.split()
    for p in palabras:
        if len(p) > 2 and p in nombres_personales:
            return "VENTA WEB"
    patrones_fisicas = ["LOCAL","AEROPOSTALE","MALL","PLAZA","SHOPPING","CENTRO COMERCIAL",
                        "CC","C.C","TIENDA","SUCURSAL","PRICE","CLUB","DORADO","CIUDAD",
                        "RIOCENTRO","PASEO","PORTAL","SOL","CONDADO","CITY","CEIBOS",
                        "IBARRA","MATRIZ","BODEGA","FASHION","GYE","QUITO","MACHALA",
                        "PORTOVIEJO","BABAHOYO","MANTA","AMBATO","CUENCA","ALMACEN","PRATI"]
    for patron in patrones_fisicas:
        if patron in nombre_upper:
            return "TIENDA FÍSICA"
    if len(palabras) >= 3 or any(len(p) > 3 for p in palabras):
        return "TIENDA FÍSICA"
    return "VENTA WEB"

def cargar_archivo_local(uploaded_file, nombre):
    if uploaded_file is None:
        return None
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error al cargar {nombre}: {str(e)}")
        return None

# ------------------------------------------------------------------------------
# PROCESAMIENTO PRINCIPAL CON DEPURACIÓN
# ------------------------------------------------------------------------------
def procesar_gastos_reconciliacion(manifesto, facturas, config):
    """
    Procesa manifiesto y facturas, cruza por guía después de limpieza mejorada.
    """
    # 1. Preparar manifiesto
    st.info("📦 Procesando manifiesto...")
    col_guia_m = config["guia_m"]
    col_subtotal_m = config["subtotal_m"]
    col_ciudad_m = config.get("ciudad_destino", None)
    col_piezas_m = obtener_columna_piezas(manifesto)
    col_fecha_m = obtener_columna_fecha(manifesto)

    df_m = manifesto.copy()
    # Limpieza mejorada de guías
    df_m["GUIA_ORIGINAL"] = df_m[col_guia_m].astype(str).str.strip()
    df_m["GUIA_LIMPIA"] = df_m["GUIA_ORIGINAL"].apply(limpiar_guia)
    df_m["SUBTOTAL_MANIFIESTO"] = df_m[col_subtotal_m].apply(procesar_subtotal)
    
    if col_ciudad_m and col_ciudad_m in df_m.columns:
        df_m["CIUDAD"] = df_m[col_ciudad_m].fillna("DESCONOCIDA").astype(str)
    else:
        df_m["CIUDAD"] = "DESCONOCIDA"
    
    if col_piezas_m:
        df_m["PIEZAS"] = pd.to_numeric(df_m[col_piezas_m], errors="coerce").fillna(1)
    else:
        df_m["PIEZAS"] = 1
    
    if col_fecha_m:
        try:
            df_m["FECHA"] = pd.to_datetime(df_m[col_fecha_m], errors="coerce")
        except:
            df_m["FECHA"] = None
    
    # Destinatario
    col_dest_m = None
    for posible in ["DESTINATARIO", "CONSIGNATARIO", "CLIENTE", "NOMBRE", "RAZON SOCIAL", "DESTINO"]:
        if posible in df_m.columns:
            col_dest_m = posible
            break
    if not col_dest_m:
        for col in df_m.columns:
            if any(p in str(col).upper() for p in ["DEST", "CONSIG", "CLIEN", "NOMB", "RAZON"]):
                col_dest_m = col
                break
    if col_dest_m:
        df_m["DESTINATARIO"] = df_m[col_dest_m].fillna("DESCONOCIDO").astype(str)
    else:
        df_m["DESTINATARIO"] = "TIENDA " + df_m["CIUDAD"]
    
    total_manifiesto_calc = df_m["SUBTOTAL_MANIFIESTO"].sum()
    st.success(f"Manifiesto: {len(df_m)} registros, piezas: {df_m['PIEZAS'].sum():,.0f}, total manifiesto: ${total_manifiesto_calc:,.2f}")
    
    # 2. Procesar facturas
    st.info("🧾 Procesando facturas...")
    col_guia_f = config["guia_f"]
    col_subtotal_f = config["subtotal"]
    df_f = facturas.copy()
    df_f["GUIA_ORIGINAL"] = df_f[col_guia_f].astype(str).str.strip()
    df_f["GUIA_LIMPIA"] = df_f["GUIA_ORIGINAL"].apply(limpiar_guia)
    df_f["SUBTOTAL_FACTURA"] = df_f[col_subtotal_f].apply(procesar_subtotal)
    # Agrupar por guía (por si hay varias líneas)
    df_f = df_f.groupby("GUIA_LIMPIA", as_index=False)["SUBTOTAL_FACTURA"].sum()
    total_facturas_calc = df_f["SUBTOTAL_FACTURA"].sum()
    st.success(f"Facturas: {len(df_f)} registros, total facturado: ${total_facturas_calc:,.2f}")
    
    # --- DEPURACIÓN DETALLADA ---
    with st.expander("🔍 Verificar coincidencia de guías (muestras)", expanded=False):
        st.write("**Primeras 10 guías del manifiesto (original vs limpia):**")
        muestras_m = df_m[["GUIA_ORIGINAL", "GUIA_LIMPIA"]].drop_duplicates().head(10)
        st.dataframe(muestras_m)
        
        st.write("**Primeras 10 guías de facturas (original vs limpia):**")
        # Facturas: necesitamos mantener original, pero agrupamos, así que recuperamos original de facturas sin agrupar
        df_f_original = facturas.copy()
        df_f_original["GUIA_ORIGINAL"] = df_f_original[col_guia_f].astype(str).str.strip()
        df_f_original["GUIA_LIMPIA"] = df_f_original["GUIA_ORIGINAL"].apply(limpiar_guia)
        muestras_f = df_f_original[["GUIA_ORIGINAL", "GUIA_LIMPIA"]].drop_duplicates().head(10)
        st.dataframe(muestras_f)
        
        # Contar guías vacías después de limpiar
        guias_m_vacias = df_m[df_m["GUIA_LIMPIA"] == ""].shape[0]
        guias_f_vacias = df_f_original[df_f_original["GUIA_LIMPIA"] == ""].shape[0]
        st.write(f"**Guías vacías en manifiesto después de limpiar:** {guias_m_vacias}")
        st.write(f"**Guías vacías en facturas después de limpiar:** {guias_f_vacias}")
        
        guias_m_set = set(df_m["GUIA_LIMPIA"].dropna().unique())
        guias_f_set = set(df_f["GUIA_LIMPIA"].dropna().unique())
        comunes = guias_m_set.intersection(guias_f_set)
        st.write(f"**Guías únicas en manifiesto (limpias):** {len(guias_m_set)}")
        st.write(f"**Guías únicas en facturas (limpias):** {len(guias_f_set)}")
        st.write(f"**Guías coincidentes:** {len(comunes)}")
        
        if len(comunes) == 0:
            st.error("❌ No hay ninguna guía en común. Revisa las muestras para ver si las guías limpias coinciden.")
            st.stop()
    
    # 3. Unir datos
    st.info("🔗 Uniendo datos por guía limpia...")
    df_completo = pd.merge(df_m, df_f, on="GUIA_LIMPIA", how="left")
    df_completo["ESTADO"] = df_completo["SUBTOTAL_FACTURA"].apply(
        lambda x: "FACTURADA" if pd.notna(x) and x > 0 else "ANULADA"
    )
    df_completo["SUBTOTAL"] = df_completo["SUBTOTAL_FACTURA"].fillna(0)
    df_completo["DIFERENCIA"] = df_completo["SUBTOTAL_MANIFIESTO"] - df_completo["SUBTOTAL"]
    df_completo["TIPO"] = df_completo["DESTINATARIO"].apply(identificar_tipo_tienda)
    df_completo["NOMBRE_NORMALIZADO"] = df_completo["DESTINATARIO"].apply(normalizar_texto)
    
    # Crear grupo para agregación
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
                return f"{grupo_ciudad}{' '.join(palabras[:3])}"
            return f"{grupo_ciudad}TIENDA"
        else:
            return f"DESCONOCIDO - {nombre[:20]}"
    df_completo["GRUPO"] = df_completo.apply(crear_grupo, axis=1)
    
    guias_facturadas = df_completo[df_completo["ESTADO"] == "FACTURADA"].shape[0]
    guias_anuladas = df_completo[df_completo["ESTADO"] == "ANULADA"].shape[0]
    st.success(f"Unión completada: {len(df_completo)} registros (Facturadas: {guias_facturadas}, Anuladas: {guias_anuladas})")
    
    # 4. Métricas por grupo (solo facturadas)
    st.info("📊 Calculando métricas por grupo...")
    df_facturadas = df_completo[df_completo["ESTADO"] == "FACTURADA"]
    if df_facturadas.empty:
        st.warning("No hay guías facturadas. Verifica la depuración de coincidencia de guías.")
        metricas = pd.DataFrame(columns=["GRUPO","GUIAS","PIEZAS","SUBTOTAL","SUBTOTAL_MANIFIESTO","DIFERENCIA","DESTINATARIOS","CIUDADES","TIPO","PORCENTAJE","PROMEDIO_POR_PIEZA","PIEZAS_POR_GUIA"])
        resumen = pd.DataFrame(columns=["TIPO","TIENDAS","GUIAS","PIEZAS","SUBTOTAL","PORCENTAJE"])
    else:
        metricas = df_facturadas.groupby("GRUPO").agg(
            GUIAS=("GUIA_LIMPIA","count"),
            PIEZAS=("PIEZAS","sum"),
            SUBTOTAL=("SUBTOTAL","sum"),
            SUBTOTAL_MANIFIESTO=("SUBTOTAL_MANIFIESTO","sum"),
            DIFERENCIA=("DIFERENCIA","sum"),
            DESTINATARIOS=("DESTINATARIO", lambda x: ", ".join(sorted(set(str(d) for d in x if pd.notna(d)))[:5])),
            CIUDADES=("CIUDAD", lambda x: ", ".join(sorted(set(str(c) for c in x if pd.notna(c)))[:3])),
            TIPO=("TIPO", lambda x: x.mode()[0] if not x.mode().empty else "DESCONOCIDO")
        ).reset_index()
        total_general = metricas["SUBTOTAL"].sum()
        if total_general > 0:
            metricas["PORCENTAJE"] = (metricas["SUBTOTAL"] / total_general * 100).round(2)
            metricas["PROMEDIO_POR_PIEZA"] = (metricas["SUBTOTAL"] / metricas["PIEZAS"]).round(2)
        else:
            metricas["PORCENTAJE"] = 0.0
            metricas["PROMEDIO_POR_PIEZA"] = 0.0
        metricas["PIEZAS_POR_GUIA"] = (metricas["PIEZAS"] / metricas["GUIAS"]).round(2)
        metricas = metricas.sort_values("SUBTOTAL", ascending=False)
        
        # Resumen por tipo
        resumen = df_facturadas.groupby("TIPO").agg(
            TIENDAS=("GRUPO","nunique"),
            GUIAS=("GUIA_LIMPIA","count"),
            PIEZAS=("PIEZAS","sum"),
            SUBTOTAL=("SUBTOTAL","sum")
        ).reset_index()
        if total_general > 0:
            resumen["PORCENTAJE"] = (resumen["SUBTOTAL"] / total_general * 100).round(2)
        else:
            resumen["PORCENTAJE"] = 0.0
        resumen = resumen.sort_values("SUBTOTAL", ascending=False)
    
    # 5. Validación
    total_manifiesto = df_completo["SUBTOTAL_MANIFIESTO"].sum()
    total_facturas = df_completo["SUBTOTAL"].sum()
    validacion = {
        "total_manifiesto": total_manifiesto,
        "total_facturas": total_facturas,
        "diferencia": abs(total_manifiesto - total_facturas),
        "porcentaje": (abs(total_manifiesto - total_facturas)/total_manifiesto*100) if total_manifiesto > 0 else 0,
        "coincide": abs(total_manifiesto - total_facturas) < 0.01,
        "guias_procesadas": len(df_completo),
        "guias_facturadas": guias_facturadas,
        "guias_anuladas": guias_anuladas,
        "piezas_totales": df_completo["PIEZAS"].sum(),
        "grupos_identificados": len(metricas) if not metricas.empty else 0,
        "porcentaje_facturadas": (guias_facturadas/len(df_completo)*100) if len(df_completo)>0 else 0,
        "porcentaje_anuladas": (guias_anuladas/len(df_completo)*100) if len(df_completo)>0 else 0,
    }
    
    guias_anuladas_df = df_completo[df_completo["ESTADO"] == "ANULADA"].copy()
    return df_completo, metricas, resumen, validacion, guias_anuladas_df

# ------------------------------------------------------------------------------
# GENERACIÓN DE EXCEL Y PDF (sin cambios, pero los incluyo por completitud)
# ------------------------------------------------------------------------------
def generar_excel_con_formato_exacto(metricas_filt, resultado, guias_anuladas, manifesto_original, filtros_aplicados=None):
    try:
        output = BytesIO()
        wb = Workbook()
        ws1 = wb.active
        ws1.title = "Reporte"
        hoja1_data = metricas_filt[['GRUPO', 'SUBTOTAL']].copy().sort_values('GRUPO') if not metricas_filt.empty else pd.DataFrame()
        ws1.append(["", ""])
        ws1.append(["", ""])
        ws1.append(["Etiquetas de fila", "Suma de SUBTOTAL"])
        for _, row in hoja1_data.iterrows():
            ws1.append([row['GRUPO'], row['SUBTOTAL']])
        ws1.append(["Total general", hoja1_data['SUBTOTAL'].sum() if not hoja1_data.empty else 0])
        for row in ws1.iter_rows(min_row=3, max_row=ws1.max_row, min_col=1, max_col=2):
            for cell in row:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for cell in ws1[3]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(4, ws1.max_row + 1):
            ws1.cell(row=row, column=2).number_format = '#,##0.00'
        ws1.column_dimensions['A'].width = 50
        ws1.column_dimensions['B'].width = 20

        ws2 = wb.create_sheet(title="Tiendas")
        columnas = ["GRUPO", "GUIAS", "PIEZAS", "SUBTOTAL", "DESTINATARIOS", "CIUDADES", "TIPO", "PORCENTAJE", "PROMEDIO_POR_PIEZA", "PIEZAS_POR_GUIA"]
        ws2.append(columnas)
        if not metricas_filt.empty:
            for _, row in metricas_filt.iterrows():
                ws2.append([row['GRUPO'], int(row['GUIAS']), int(row['PIEZAS']), row['SUBTOTAL'],
                            row['DESTINATARIOS'], row['CIUDADES'], row['TIPO'], row['PORCENTAJE'],
                            row['PROMEDIO_POR_PIEZA'], row['PIEZAS_POR_GUIA']])
        ws2.append(["" for _ in range(len(columnas))])
        ult_fila = ws2.max_row - 1
        total_row = ["" for _ in range(len(columnas))]
        total_row[0] = "Total general"
        total_row[3] = f"=SUBTOTAL(109,D2:D{ult_fila})"
        ws2.append(total_row)
        for row in ws2.iter_rows(min_row=1, max_row=ws2.max_row, min_col=1, max_col=len(columnas)):
            for cell in row:
                cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
        for cell in ws2[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in range(2, ws2.max_row + 1):
            ws2.cell(row=row, column=4).number_format = '#,##0.00'
            ws2.cell(row=row, column=8).number_format = '0.00'
            ws2.cell(row=row, column=9).number_format = '0.00'
            ws2.cell(row=row, column=10).number_format = '0.00'
        for cell in ws2[ws2.max_row]:
            cell.font = Font(bold=True)
        anchos = [40,10,10,15,50,20,20,15,20,20]
        for i, ancho in enumerate(anchos,1):
            ws2.column_dimensions[get_column_letter(i)].width = ancho

        if not guias_anuladas.empty:
            ws3 = wb.create_sheet(title="Guias Anuladas")
            cols_mostrar = ['GUIA_LIMPIA', 'DESTINATARIO', 'CIUDAD', 'SUBTOTAL_MANIFIESTO', 'PIEZAS']
            cols_existentes = [c for c in cols_mostrar if c in guias_anuladas.columns]
            ws3.append(cols_existentes)
            for _, row in guias_anuladas.iterrows():
                ws3.append([row.get(c, '') for c in cols_existentes])
            for cell in ws3[1]:
                cell.fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)

        ws4 = wb.create_sheet(title="Detalle")
        cols_detalle = ['GUIA_LIMPIA', 'ESTADO', 'GRUPO', 'DESTINATARIO', 'CIUDAD', 'PIEZAS', 'SUBTOTAL_MANIFIESTO', 'SUBTOTAL', 'DIFERENCIA', 'TIPO']
        cols_detalle = [c for c in cols_detalle if c in resultado.columns]
        ws4.append(cols_detalle)
        for _, row in resultado.iterrows():
            ws4.append([row.get(c, '') for c in cols_detalle])
        for cell in ws4[1]:
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        for row in range(2, ws4.max_row + 1):
            for i, col in enumerate(cols_detalle, 1):
                if col in ['SUBTOTAL_MANIFIESTO', 'SUBTOTAL', 'DIFERENCIA']:
                    ws4.cell(row=row, column=i).number_format = '#,##0.00'
        wb.save(output)
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Error generando Excel: {e}")
        return None

def generar_pdf_reporte(metricas, resumen, validacion):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf_path = tmp.name
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=12, alignment=1)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
        normal_style = styles['Normal']
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

        if not resumen.empty:
            elements.append(Paragraph("RESUMEN POR TIPO DE TIENDA", subtitle_style))
            resumen_data = [["TIPO","TIENDAS","GUÍAS","PIEZAS","SUBTOTAL","%"]]
            for _,row in resumen.iterrows():
                resumen_data.append([row['TIPO'], str(int(row['TIENDAS'])), str(int(row['GUIAS'])), str(int(row['PIEZAS'])), f"${row['SUBTOTAL']:,.2f}", f"{row['PORCENTAJE']:.2f}%"])
            resumen_table = Table(resumen_data, colWidths=[120,80,80,80,100,80])
            resumen_table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),grey), ("TEXTCOLOR",(0,0),(-1,0),whitesmoke),
                ("ALIGN",(0,0),(-1,-1),"CENTER"), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,0),12),
                ("BACKGROUND",(0,1),(-1,-1),beige), ("GRID",(0,0),(-1,-1),1,black)
            ]))
            elements.append(resumen_table)
            elements.append(Spacer(1,20))

        elements.append(Paragraph("ANÁLISIS EJECUTIVO", subtitle_style))
        analisis = f"""
        <b>Validación:</b> {"✅ COINCIDENCIA EXACTA" if validacion["coincide"] else "⚠ CON DIFERENCIAS"}<br/>
        <b>Facturación:</b> {validacion["porcentaje_facturadas"]:.1f}% de guías facturadas<br/>
        <b>Anulaciones:</b> {validacion["porcentaje_anuladas"]:.1f}%<br/>
        <b>Recomendación:</b> {"Revisar guías anuladas" if validacion["guias_anuladas"]>0 else "Proceso eficiente"}
        """
        elements.append(Paragraph(analisis, normal_style))
        doc.build(elements)
        return pdf_path
    except Exception as e:
        st.error(f"Error PDF: {e}")
        return None

# ------------------------------------------------------------------------------
# INTERFAZ PRINCIPAL DE STREAMLIT
# ------------------------------------------------------------------------------
def show_reconciliacion_v8():
    add_back_button(key="back_reconciliacion")
    show_module_header("💰 Gestión de Gastos por Tienda", "Conciliación financiera y análisis de facturas")
    st.markdown('<div class="module-content">', unsafe_allow_html=True)

    if 'gastos_datos' not in st.session_state:
        st.session_state.gastos_datos = {
            'manifesto': None, 'facturas': None, 'resultado': None,
            'metricas': None, 'resumen': None, 'validacion': None,
            'guias_anuladas': None, 'procesado': False
        }

    with st.sidebar:
        st.header("📁 Carga de Archivos")
        st.markdown("**Formatos soportados:** Excel (.xlsx, .xls) y CSV")
        uploaded_manifesto = st.file_uploader("Manifiesto (con GUIA y SUBTOTAL)", type=["csv", "xlsx", "xls"], key="manifesto_upload")
        uploaded_facturas = st.file_uploader("Facturas (con GUIA y VALOR)", type=["csv", "xlsx", "xls"], key="facturas_upload")
        if uploaded_manifesto and uploaded_facturas:
            if st.button("📥 Cargar Archivos", type="primary", use_container_width=True):
                with st.spinner("Cargando..."):
                    manifesto = cargar_archivo_local(uploaded_manifesto, "Manifiesto")
                    facturas = cargar_archivo_local(uploaded_facturas, "Facturas")
                    if manifesto is not None and facturas is not None:
                        st.session_state.gastos_datos["manifesto"] = manifesto
                        st.session_state.gastos_datos["facturas"] = facturas
                        st.rerun()

    if st.session_state.gastos_datos["manifesto"] is not None:
        manifesto = st.session_state.gastos_datos["manifesto"]
        facturas = st.session_state.gastos_datos["facturas"]
        st.header("⚙️ Configuración de Procesamiento")
        st.subheader("🔍 Selecciona las columnas correctas")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Manifiesto**")
            guia_candidates = [c for c in manifesto.columns if "GUIA" in str(c).upper() or "GUÍA" in str(c).upper()]
            if not guia_candidates:
                guia_candidates = manifesto.columns.tolist()
            guia_m = st.selectbox("Columna Guía (Manifiesto)", guia_candidates, index=0)
            subtotal_candidates = [c for c in manifesto.columns if any(p in str(c).upper() for p in ["SUBTOTAL", "TOTAL", "VALOR", "FLETE"])]
            if not subtotal_candidates:
                subtotal_candidates = manifesto.columns.tolist()
            subtotal_m = st.selectbox("Columna Subtotal/Valor (Manifiesto)", subtotal_candidates, index=0)
            ciudad_candidates = [c for c in manifesto.columns if "CIUDAD" in str(c).upper() or "DESTINO" in str(c).upper()]
            ciudad_destino = st.selectbox("Columna Ciudad (opcional)", ["(No usar)"] + ciudad_candidates, index=0)
            if ciudad_destino == "(No usar)":
                ciudad_destino = None
        with col2:
            st.write("**Facturas**")
            guia_f_candidates = [c for c in facturas.columns if "GUIA" in str(c).upper() or "GUÍA" in str(c).upper()]
            if not guia_f_candidates:
                guia_f_candidates = facturas.columns.tolist()
            guia_f = st.selectbox("Columna Guía (Facturas)", guia_f_candidates, index=0)
            subtotal_f_candidates = [c for c in facturas.columns if any(p in str(c).upper() for p in ["SUBTOTAL", "TOTAL", "IMPORTE", "VALOR"])]
            if not subtotal_f_candidates:
                subtotal_f_candidates = facturas.columns.tolist()
            subtotal_f = st.selectbox("Columna Subtotal/Valor (Facturas)", subtotal_f_candidates, index=0)

        config = {
            "guia_m": guia_m, "subtotal_m": subtotal_m,
            "ciudad_destino": ciudad_destino if ciudad_destino else None,
            "guia_f": guia_f, "subtotal": subtotal_f
        }
        if st.button("🚀 Procesar Conciliación", type="primary", use_container_width=True):
            with st.spinner("Procesando..."):
                try:
                    resultado, metricas, resumen, validacion, guias_anuladas = procesar_gastos_reconciliacion(manifesto, facturas, config)
                    st.session_state.gastos_datos["resultado"] = resultado
                    st.session_state.gastos_datos["metricas"] = metricas
                    st.session_state.gastos_datos["resumen"] = resumen
                    st.session_state.gastos_datos["validacion"] = validacion
                    st.session_state.gastos_datos["guias_anuladas"] = guias_anuladas
                    st.session_state.gastos_datos["procesado"] = True
                    st.success("✅ Procesamiento completado")
                    if validacion["guias_facturadas"] == 0:
                        st.error("⚠️ No se encontraron coincidencias. Revisa la expansión 'Verificar coincidencia de guías' para depurar.")
                    else:
                        st.info(f"📊 Total facturado: ${validacion['total_facturas']:,.2f} | Guías facturadas: {validacion['guias_facturadas']} | Anuladas: {validacion['guias_anuladas']}")
                except Exception as e:
                    st.error(f"Error en el procesamiento: {str(e)}")
                    logger.exception(e)

    if st.session_state.gastos_datos["procesado"]:
        resultado = st.session_state.gastos_datos["resultado"]
        metricas = st.session_state.gastos_datos["metricas"]
        resumen = st.session_state.gastos_datos["resumen"]
        validacion = st.session_state.gastos_datos["validacion"]
        guias_anuladas = st.session_state.gastos_datos["guias_anuladas"]
        manifesto_original = st.session_state.gastos_datos["manifesto"]

        tabs = st.tabs(["📊 Resumen", "✅ Validación", "🏪 Todas las Tiendas", "🚫 Guías Anuladas", "🌎 Geografía", "📋 Datos", "💾 Exportar", "📄 Reporte PDF"])

        with tabs[0]:
            st.header("📊 Resumen Ejecutivo")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Grupos de Tiendas", f"{validacion['grupos_identificados']:,}")
            col2.metric("Total Guías", f"{validacion['guias_procesadas']:,}")
            col3.metric("Guías Facturadas", f"{validacion['guias_facturadas']:,}")
            col4.metric("Guías Anuladas", f"{validacion['guias_anuladas']:,}")
            col5.metric("Total Facturado", f"${validacion['total_facturas']:,.2f}")
            st.subheader("Distribución por Tipo de Tienda")
            if not resumen.empty:
                fig = px.pie(resumen, values="SUBTOTAL", names="TIPO", title="Distribución de Gastos por Tipo", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos facturados para mostrar.")
            st.subheader("Resumen por Tipo de Tienda")
            if not resumen.empty:
                st.dataframe(resumen.style.format({"SUBTOTAL": "${:,.2f}", "PORCENTAJE": "{:.2f}%"}), use_container_width=True)

        with tabs[1]:
            st.header("✅ Validación de Totales")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Manifiesto", f"${validacion['total_manifiesto']:,.2f}")
            col2.metric("Total Facturas", f"${validacion['total_facturas']:,.2f}")
            col3.metric("Diferencia", f"${validacion['diferencia']:,.2f}")
            col4.metric("% Diferencia", f"{validacion['porcentaje']:.2f}%")
            if validacion['coincide']:
                st.success("✅ Los totales coinciden dentro del margen aceptable.")
            else:
                st.warning(f"⚠️ Diferencia de ${validacion['diferencia']:,.2f} ({validacion['porcentaje']:.2f}%). Revisar guías anuladas.")

        with tabs[2]:
            st.header("🏪 Gastos por Tienda/Grupo")
            if not metricas.empty:
                st.dataframe(metricas.style.format({
                    "SUBTOTAL": "${:,.2f}", "PORCENTAJE": "{:.2f}%",
                    "PROMEDIO_POR_PIEZA": "${:,.2f}", "PIEZAS_POR_GUIA": "{:.2f}"
                }), use_container_width=True)
            else:
                st.warning("No hay métricas para mostrar (todas las guías están anuladas).")

        with tabs[3]:
            st.header("🚫 Guías Anuladas")
            if not guias_anuladas.empty:
                st.dataframe(guias_anuladas[["GUIA_LIMPIA","DESTINATARIO","CIUDAD","SUBTOTAL_MANIFIESTO","PIEZAS"]], use_container_width=True)
                st.download_button("Descargar anuladas CSV", data=guias_anuladas.to_csv(index=False), file_name="anuladas.csv", mime="text/csv")
            else:
                st.success("✅ No hay guías anuladas.")

        with tabs[4]:
            st.header("🌎 Distribución Geográfica")
            if 'CIUDAD' in resultado.columns and not resultado.empty:
                ciudad_data = resultado[resultado["ESTADO"]=="FACTURADA"].groupby("CIUDAD")["SUBTOTAL"].sum().reset_index().sort_values("SUBTOTAL", ascending=False)
                if not ciudad_data.empty:
                    fig = px.bar(ciudad_data.head(15), x="SUBTOTAL", y="CIUDAD", orientation='h', title="Top Ciudades por Gasto")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos geográficos disponibles.")

        with tabs[5]:
            st.header("📋 Datos Detallados")
            st.dataframe(resultado.head(100), use_container_width=True)

        with tabs[6]:
            st.header("💾 Exportar Resultados")
            excel_data = generar_excel_con_formato_exacto(metricas, resultado, guias_anuladas, manifesto_original)
            if excel_data:
                st.download_button("📥 Descargar Excel", data=excel_data, file_name=f"reconciliacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            pdf_path = generar_pdf_reporte(metricas, resumen, validacion)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 Descargar PDF", data=f, file_name=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")

        with tabs[7]:
            st.header("📄 Reporte PDF")
            st.info("Usa la pestaña Exportar para generar el PDF.")

    else:
        st.info("👆 Carga los archivos desde el panel lateral y selecciona las columnas correctas.")

    st.markdown('</div>', unsafe_allow_html=True)
