import io
import re
import unicodedata
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==============================================================================
# 1. NORMALIZACIÓN Y HELPERS
# ==============================================================================

def normalizar_texto_transporte(val) -> str:
    """Normaliza texto para cruce seguro: mayúsculas, sin tildes ni espacios extras."""
    if pd.isna(val) or val is None:
        return ""
    texto = str(val).strip()
    try:
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    except Exception:
        pass
    texto = re.sub(r"\s+", " ", texto.upper()).strip()
    return texto

def limpiar_numero_guia(val) -> str:
    """Limpia el número de guía eliminando .0 y caracteres invisibles."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    # Quitar comillas o espacios
    s = re.sub(r"[\s\'\"]", "", s).upper()
    return s

def es_guia_valida(guia: str) -> bool:
    """Valida que la guía tenga formato de guía real y no sea fila de cierre."""
    if not guia:
        return False
    g = guia.strip().upper()
    # Descartar palabras clave de pie de página de manifiesto
    palabras_invalidas = [
        "TOTAL", "ENTREGADO", "FIRMA", "DESPACHADO", "RECOLECCION", 
        "FECHA", "RECIBE", "MANIFIESTO", "SUBTOTAL", "OBSERVACION"
    ]
    if any(p in g for p in palabras_invalidas):
        return False
    # Validar formato: debe contener dígitos o prefijos típicos (LC, G, etc.)
    if re.match(r"^(LC\d+|G\d+|\d+|[A-Z0-9\-]{5,})$", g):
        return True
    # Si tiene al menos 4 dígitos, es válida
    if len(re.sub(r"\D", "", g)) >= 4:
        return True
    return False

def parse_float_seguro(val) -> float:
    """Convierte valor monetario a float."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float, np.number)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(re.sub(r"[^\d.-]", "", s))
    except Exception:
        return 0.0

# ==============================================================================
# 2. CLASIFICADOR DE CONTENIDO
# ==============================================================================

def clasificar_contenido_transporte(contenido_raw: str, producto_raw: str = "") -> str:
    """
    Clasificador según las 10 reglas estrictas del centro de distribución:
    1. DOCUMENTOS
    2. SIN ESPECIFICAR
    3. PUBLICIDAD
    4. VENTA WEB
    5. DEVOLUCIÓN
    6. MERCADERÍA
    7. ACCESORIOS / PRENDAS
    8. MOBILIARIO / EQUIPOS
    9. INSUMOS / ADMINISTRATIVO
    10. OTROS
    """
    cont = normalizar_texto_transporte(contenido_raw)
    prod = normalizar_texto_transporte(producto_raw)
    
    # 1. DOCUMENTOS
    if prod == "DOCUMENTOS_SERV" or any(w in cont for w in ["DOC", "DOCS", "DOCUMENTO", "DOCUMENTOS", "SOBRE"]):
        return "DOCUMENTOS"
    
    # 2. SIN ESPECIFICAR
    if not cont or cont in ["", "NAN", "NONE", "NULL", "-"]:
        return "SIN ESPECIFICAR"
    
    # 3. PUBLICIDAD
    if "PUBLICID" in cont or "BANNER" in cont or "POP" in cont:
        return "PUBLICIDAD"
    
    # 4. VENTA WEB
    if "WEB" in cont or "ECOMMERCE" in cont or "E-COMMERCE" in cont:
        return "VENTA WEB"
    
    # 5. DEVOLUCIÓN
    if "DEVOLU" in cont or "CAMBIO" in cont:
        return "DEVOLUCIÓN"
    
    # 6. MERCADERÍA
    if "MERCADER" in cont or cont == "CARGA" or cont == "PRENDAS":
        return "MERCADERÍA"
    
    # 7. ACCESORIOS / PRENDAS
    accesorios_keywords = [
        "GAFA", "GORRA", "FUNDA", "MANIQUI", "PERFUME", "SANDALIA", 
        "ZANDALIA", "PRENDA", "UNIFORME", "ZAPATO", "CAMISETA", "JEAN", "ROPA", "POLO"
    ]
    if any(k in cont for k in accesorios_keywords):
        return "ACCESORIOS / PRENDAS"
    
    # 8. MOBILIARIO / EQUIPOS
    mobiliario_keywords = ["MUEBLE", "PLANCHA", "EQUIPO", "COMPUTADORA", "IMPRESORA", "SILLA", "MESA"]
    if any(k in cont for k in mobiliario_keywords):
        return "MOBILIARIO / EQUIPOS"
    
    # 9. INSUMOS / ADMINISTRATIVO
    insumos_keywords = [
        "CINTA", "ROLLO", "CARTON", "TABLA", "FACTURA", "REPORTE", 
        "FICHA", "MEDICINA", "TRABAJO SOCIAL", "UPC", "CABLE", "LONA", "PAPEL", "ETIQUETA"
    ]
    if any(k in cont for k in insumos_keywords):
        return "INSUMOS / ADMINISTRATIVO"
    
    # 10. OTROS
    return "OTROS"

# ==============================================================================
# 3. PARSERS DE ARCHIVOS
# ==============================================================================

def cargar_y_limpiar_manifiesto(file_or_bytes) -> pd.DataFrame:
    """Carga el archivo de manifiesto detectando encabezado y filtrando filas basura."""
    excel_file = pd.ExcelFile(file_or_bytes)
    sheet_name = "Guias" if "Guias" in excel_file.sheet_names else excel_file.sheet_names[0]
    
    df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
    
    header_idx = 1
    for idx, row in df_raw.head(10).iterrows():
        row_str = " ".join([str(c).upper() for c in row.values if pd.notna(c)])
        if "GUIA" in row_str and ("DESTINO" in row_str or "DESTINATARIO" in row_str or "ORIGEN" in row_str):
            header_idx = idx
            break
            
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_idx)
    
    col_map = {}
    for c in df.columns:
        c_norm = normalizar_texto_transporte(c)
        if "GUIA" in c_norm: col_map[c] = "GUIA"
        elif "CIUDAD ORIGEN" in c_norm or ("CIUDAD" in c_norm and "ORI" in c_norm) or c_norm == "ORIGEN": col_map[c] = "CIUDAD ORIGEN"
        elif "CIUDAD DESTINO" in c_norm or ("CIUDAD" in c_norm and "DES" in c_norm) or c_norm == "DESTINO": col_map[c] = "CIUDAD DESTINO"
        elif "DESTINATARIO" in c_norm or "CLIENTE" in c_norm: col_map[c] = "DESTINATARIO"
        elif "TELEFONO" in c_norm or "TEL" in c_norm: col_map[c] = "TELEFONO"
        elif "DIRECCION" in c_norm or "DIR" in c_norm: col_map[c] = "DIRECCION DESTINATARIO"
        elif "CONTENIDO" in c_norm or "DETALLE" in c_norm: col_map[c] = "CONTENIDO"
        elif "PRODUCTO" in c_norm or "SERVICIO" in c_norm: col_map[c] = "PRODUCTO"
        elif "VALOR DECLARADO" in c_norm or "VAL. DEC" in c_norm: col_map[c] = "VALOR DECLARADO"
        elif "PESO" in c_norm: col_map[c] = "PESO"
        elif "ESTADO" in c_norm: col_map[c] = "ESTADO"
        elif "FECHA ENTREGA" in c_norm: col_map[c] = "FECHA ENTREGA"
        elif "RECIBE" in c_norm: col_map[c] = "RECIBE"
        elif "FECHA CREACION" in c_norm or "FECHA EMISION" in c_norm or "FECHA" in c_norm: col_map[c] = "FECHA CREACION"
        elif "COSTO FLETE" in c_norm or "FLETE" in c_norm: col_map[c] = "COSTO FLETE"
        
    df = df.rename(columns=col_map)
    
    if "GUIA" not in df.columns:
        raise ValueError("El manifiesto no contiene una columna 'GUIA' identificable.")
        
    df["GUIA"] = df["GUIA"].apply(limpiar_numero_guia)
    df = df[df["GUIA"].apply(es_guia_valida)].copy()
    
    if "CIUDAD ORIGEN" in df.columns:
        df["CIUDAD ORIGEN"] = df["CIUDAD ORIGEN"].apply(normalizar_texto_transporte)
    else:
        df["CIUDAD ORIGEN"] = "IBARRA"
        
    if "CIUDAD DESTINO" in df.columns:
        df["CIUDAD DESTINO"] = df["CIUDAD DESTINO"].apply(normalizar_texto_transporte)
    else:
        df["CIUDAD DESTINO"] = ""
        
    for col in ["DESTINATARIO", "TELEFONO", "DIRECCION DESTINATARIO", "CONTENIDO", "PRODUCTO", "ESTADO", "RECIBE"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str).str.strip()
            
    if "VALOR DECLARADO" in df.columns:
        df["VALOR DECLARADO"] = df["VALOR DECLARADO"].apply(parse_float_seguro)
    else:
        df["VALOR DECLARADO"] = 0.0
        
    if "PESO" in df.columns:
        df["PESO"] = df["PESO"].apply(parse_float_seguro)
    else:
        df["PESO"] = 0.0

    return df

def cargar_y_limpiar_factura(file_or_bytes) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carga y clasifica las 3 pestañas de la factura del Courier:
    - Documentos (DOC)
    - Carga (CAR)
    - Seguro
    Elimina la última fila de total de cada pestaña.
    """
    excel_file = pd.ExcelFile(file_or_bytes)
    sheet_names = excel_file.sheet_names
    
    df_doc = pd.DataFrame()
    df_car = pd.DataFrame()
    df_seg = pd.DataFrame()
    
    for sheet in sheet_names:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet, header=None)
        header_idx = 1
        for idx, row in df_raw.head(8).iterrows():
            row_str = " ".join([str(c).upper() for c in row.values if pd.notna(c)])
            if "GUIA" in row_str and ("FLETE" in row_str or "SUBT" in row_str or "SEGURO" in row_str or "SER" in row_str):
                header_idx = idx
                break
                
        df_sheet = pd.read_excel(excel_file, sheet_name=sheet, header=header_idx)
        
        if len(df_sheet) > 0:
            last_row_str = " ".join([str(v).upper() for v in df_sheet.iloc[-1].values if pd.notna(v)])
            if "TOTAL" in last_row_str or len(df_sheet) > 1:
                val_guia = str(df_sheet.iloc[-1].get("GUIA", df_sheet.iloc[-1, 1] if len(df_sheet.columns)>1 else ""))
                if "TOTAL" in last_row_str or not es_guia_valida(limpiar_numero_guia(val_guia)):
                    df_sheet = df_sheet.iloc[:-1].copy()
                    
        col_map = {}
        for c in df_sheet.columns:
            cn = normalizar_texto_transporte(c)
            if "GUIA" in cn: col_map[c] = "GUIA"
            elif "FECH" in cn and "REM" in cn: col_map[c] = "FECHA REM"
            elif "FECHA" in cn: col_map[c] = "FECHA"
            elif "CIU" in cn and "ORI" in cn: col_map[c] = "CIUDAD ORIGEN"
            elif "CIU" in cn and "DES" in cn: col_map[c] = "CIUDAD DESTINO"
            elif cn in ["ORIGEN", "CIUDAD ORIGEN"]: col_map[c] = "CIUDAD ORIGEN"
            elif cn in ["DESTINO", "CIUDAD DESTINO"]: col_map[c] = "CIUDAD DESTINO"
            elif cn in ["SER.", "SER", "SERVICIO"]: col_map[c] = "SERVICIO"
            elif cn in ["TRA.", "TRA", "TRAYECTO"]: col_map[c] = "TRAYECTO"
            elif cn in ["PIE.", "PIE", "PIEZAS"]: col_map[c] = "PIEZAS"
            elif cn in ["PES.", "PES", "PESO"]: col_map[c] = "PESO"
            elif cn in ["FLETE", "COSTO FLETE"]: col_map[c] = "FLETE"
            elif cn in ["DESC.", "DESC", "DESCUENTO"]: col_map[c] = "DESCUENTO"
            elif cn in ["SUBT.", "SUBT", "SUBTOTAL"]: col_map[c] = "SUBTOTAL"
            elif "VAL" in cn and "DEC" in cn: col_map[c] = "VALOR DECLARADO"
            elif "SEGURO" in cn: col_map[c] = "SEGURO_TASA" if "TASA" in cn or "%" in cn else "SEGURO"
            
        df_sheet = df_sheet.rename(columns=col_map)
        
        if "GUIA" not in df_sheet.columns:
            continue
            
        df_sheet["GUIA"] = df_sheet["GUIA"].apply(limpiar_numero_guia)
        df_sheet = df_sheet[df_sheet["GUIA"].apply(es_guia_valida)].copy()
        
        sheet_upper = sheet.upper()
        cols_upper = [str(c).upper() for c in df_sheet.columns]
        
        es_seguro = "SEGURO" in sheet_upper or "SEGURO" in cols_upper or "VALOR DECLARADO" in df_sheet.columns
        es_doc = "DOC" in sheet_upper or ("SERVICIO" in df_sheet.columns and df_sheet["SERVICIO"].astype(str).str.upper().str.contains("DOC").any())
        es_car = "CAR" in sheet_upper or "CARGA" in sheet_upper or ("SERVICIO" in df_sheet.columns and df_sheet["SERVICIO"].astype(str).str.upper().str.contains("CAR").any())
        
        if es_seguro and df_seg.empty:
            df_seg = df_sheet
        elif es_doc and df_doc.empty:
            df_doc = df_sheet
        elif es_car and df_car.empty:
            df_car = df_sheet
        else:
            if "SEGURO" in cols_upper and df_seg.empty:
                df_seg = df_sheet
            elif df_car.empty:
                df_car = df_sheet
            elif df_doc.empty:
                df_doc = df_sheet
                
    for df_curr in [df_car, df_doc, df_seg]:
        if not df_curr.empty:
            if "FLETE" in df_curr.columns:
                df_curr["FLETE"] = df_curr["FLETE"].apply(parse_float_seguro)
            if "SUBTOTAL" in df_curr.columns:
                df_curr["SUBTOTAL"] = df_curr["SUBTOTAL"].apply(parse_float_seguro)
            if "PIEZAS" in df_curr.columns:
                df_curr["PIEZAS"] = pd.to_numeric(df_curr["PIEZAS"], errors="coerce").fillna(1).astype(int)
            if "PESO" in df_curr.columns:
                df_curr["PESO"] = df_curr["PESO"].apply(parse_float_seguro)
            if "CIUDAD ORIGEN" in df_curr.columns:
                df_curr["CIUDAD ORIGEN"] = df_curr["CIUDAD ORIGEN"].apply(normalizar_texto_transporte)
            if "CIUDAD DESTINO" in df_curr.columns:
                df_curr["CIUDAD DESTINO"] = df_curr["CIUDAD DESTINO"].apply(normalizar_texto_transporte)
                
    return df_car, df_doc, df_seg

# ==============================================================================
# 4. MOTOR DE CRUCE Y CONCILIACIÓN
# ==============================================================================

def procesar_costos_transporte(df_manifiesto: pd.DataFrame, df_carga: pd.DataFrame, df_doc: pd.DataFrame, df_seguro: pd.DataFrame) -> Dict[str, Any]:
    """
    Ejecuta el cruce completo de punta a punta:
    - Cruce Factura Carga + Manifiesto + Seguro
    - Cruce Factura Documentos + Manifiesto
    - Identificación de Guías Anuladas / No Facturadas
    - Cálculo de métricas ejecutivas, ciudad-ciudad y contenido
    """
    mapa_seguro = {}
    if not df_seguro.empty and "GUIA" in df_seguro.columns:
        col_costo_seg = "SUBTOTAL" if "SUBTOTAL" in df_seguro.columns else ("SEGURO" if "SEGURO" in df_seguro.columns else df_seguro.columns[-1])
        for _, row in df_seguro.iterrows():
            g = row["GUIA"]
            val_seg = parse_float_seguro(row.get(col_costo_seg, 0.0))
            mapa_seguro[g] = val_seg

    mapa_manifiesto = {}
    if not df_manifiesto.empty and "GUIA" in df_manifiesto.columns:
        for _, row in df_manifiesto.iterrows():
            g = row["GUIA"]
            mapa_manifiesto[g] = row.to_dict()

    guias_manifiesto_set = set(df_manifiesto["GUIA"].unique()) if not df_manifiesto.empty else set()
    guias_facturadas_set = set()

    # 3. Procesar Carga Facturada
    detalle_carga_list = []
    if not df_carga.empty:
        for _, row in df_carga.iterrows():
            guia = row["GUIA"]
            guias_facturadas_set.add(guia)
            
            ciu_ori = row.get("CIUDAD ORIGEN", "IBARRA")
            ciu_des = row.get("CIUDAD DESTINO", "")
            tipo_mov = "DESDE CD IBARRA" if ciu_ori == "IBARRA" else "CIUDAD-CIUDAD"
            
            flete = parse_float_seguro(row.get("FLETE", row.get("SUBTOTAL", 0.0)))
            seguro = mapa_seguro.get(guia, 0.0)
            costo_total = flete + seguro
            
            manif_data = mapa_manifiesto.get(guia, {})
            contenido = manif_data.get("CONTENIDO", "")
            producto = manif_data.get("PRODUCTO", "")
            categoria = clasificar_contenido_transporte(contenido, producto)
            
            detalle_carga_list.append({
                "GUIA": guia,
                "FECHA ENVIO": row.get("FECHA REM", row.get("FECHA", manif_data.get("FECHA CREACION", ""))),
                "CIUDAD ORIGEN": ciu_ori,
                "CIUDAD DESTINO": ciu_des if ciu_des else manif_data.get("CIUDAD DESTINO", ""),
                "TIPO MOVIMIENTO": tipo_mov,
                "DESTINATARIO": manif_data.get("DESTINATARIO", ""),
                "TELEFONO": manif_data.get("TELEFONO", ""),
                "DIRECCION": manif_data.get("DIRECCION DESTINATARIO", ""),
                "CONTENIDO": contenido,
                "CATEGORIA": categoria,
                "TRAYECTO": row.get("TRAYECTO", ""),
                "PIEZAS": row.get("PIEZAS", 1),
                "PESO": row.get("PESO", manif_data.get("PESO", 0.0)),
                "FLETE": flete,
                "SEGURO": seguro,
                "COSTO TOTAL": costo_total,
                "VALOR DECLARADO": manif_data.get("VALOR DECLARADO", 0.0),
                "ESTADO ENTREGA": manif_data.get("ESTADO", "FACTURADO"),
                "FECHA ENTREGA": manif_data.get("FECHA ENTREGA", ""),
                "RECIBE": manif_data.get("RECIBE", ""),
                "TIPO_SERVICIO": "CARGA"
            })
            
    df_det_carga = pd.DataFrame(detalle_carga_list)

    # 4. Procesar Documentos Facturados
    detalle_doc_list = []
    if not df_doc.empty:
        for _, row in df_doc.iterrows():
            guia = row["GUIA"]
            guias_facturadas_set.add(guia)
            
            ciu_ori = row.get("CIUDAD ORIGEN", "IBARRA")
            ciu_des = row.get("CIUDAD DESTINO", "")
            tipo_mov = "DESDE CD IBARRA" if ciu_ori == "IBARRA" else "CIUDAD-CIUDAD"
            
            flete = parse_float_seguro(row.get("FLETE", row.get("SUBTOTAL", 0.0)))
            seguro = 0.0
            costo_total = flete
            
            manif_data = mapa_manifiesto.get(guia, {})
            contenido = manif_data.get("CONTENIDO", "DOCUMENTOS")
            producto = manif_data.get("PRODUCTO", "DOCUMENTOS_SERV")
            categoria = "DOCUMENTOS"
            
            detalle_doc_list.append({
                "GUIA": guia,
                "FECHA ENVIO": row.get("FECHA REM", row.get("FECHA", manif_data.get("FECHA CREACION", ""))),
                "CIUDAD ORIGEN": ciu_ori,
                "CIUDAD DESTINO": ciu_des if ciu_des else manif_data.get("CIUDAD DESTINO", ""),
                "TIPO MOVIMIENTO": tipo_mov,
                "DESTINATARIO": manif_data.get("DESTINATARIO", ""),
                "TELEFONO": manif_data.get("TELEFONO", ""),
                "DIRECCION": manif_data.get("DIRECCION DESTINATARIO", ""),
                "CONTENIDO": contenido,
                "CATEGORIA": categoria,
                "TRAYECTO": row.get("TRAYECTO", ""),
                "PIEZAS": row.get("PIEZAS", 1),
                "PESO": row.get("PESO", 0.0),
                "FLETE": flete,
                "SEGURO": seguro,
                "COSTO TOTAL": costo_total,
                "VALOR DECLARADO": 0.0,
                "ESTADO ENTREGA": manif_data.get("ESTADO", "FACTURADO"),
                "FECHA ENTREGA": manif_data.get("FECHA ENTREGA", ""),
                "RECIBE": manif_data.get("RECIBE", ""),
                "TIPO_SERVICIO": "DOCUMENTOS"
            })
            
    df_det_doc = pd.DataFrame(detalle_doc_list)

    # 5. Procesar Detalle Seguro
    detalle_seg_list = []
    if not df_seguro.empty:
        col_costo_seg = "SUBTOTAL" if "SUBTOTAL" in df_seguro.columns else ("SEGURO" if "SEGURO" in df_seguro.columns else df_seguro.columns[-1])
        for _, row in df_seguro.iterrows():
            guia = row["GUIA"]
            manif_data = mapa_manifiesto.get(guia, {})
            costo_seg = parse_float_seguro(row.get(col_costo_seg, 0.0))
            
            flete_asoc = 0.0
            if not df_det_carga.empty:
                match_c = df_det_carga[df_det_carga["GUIA"] == guia]
                if not match_c.empty:
                    flete_asoc = match_c.iloc[0]["FLETE"]
                    
            detalle_seg_list.append({
                "GUIA": guia,
                "FECHA/HORA POLIZA": row.get("FECHA", ""),
                "ORIGEN": row.get("CIUDAD ORIGEN", row.get("ORIGEN", "IBARRA")),
                "DESTINO": row.get("CIUDAD DESTINO", row.get("DESTINO", "")),
                "TRAYECTO": row.get("TRAYECTO", ""),
                "VALOR DECLARADO": parse_float_seguro(row.get("VALOR DECLARADO", row.get("VAL. DEC.", manif_data.get("VALOR DECLARADO", 0.0)))),
                "TASA SEGURO": row.get("SEGURO_TASA", row.get("SEGURO", "0.00%")),
                "COSTO SEGURO": costo_seg,
                "FLETE ASOCIADO": flete_asoc,
                "COSTO TOTAL GUIA": costo_seg + flete_asoc,
                "DESTINATARIO": manif_data.get("DESTINATARIO", ""),
                "CONTENIDO": manif_data.get("CONTENIDO", ""),
                "CATEGORIA": clasificar_contenido_transporte(manif_data.get("CONTENIDO", ""), manif_data.get("PRODUCTO", "")),
                "ESTADO": manif_data.get("ESTADO", "ASEGURADO")
            })
    df_det_seg = pd.DataFrame(detalle_seg_list)

    # 6. Guías Anuladas / No Facturadas
    guias_anuladas_list = []
    for guia in guias_manifiesto_set:
        if guia not in guias_facturadas_set:
            manif_data = mapa_manifiesto.get(guia, {})
            estado = normalizar_texto_transporte(manif_data.get("ESTADO", ""))
            
            if "NO MOVILIZADO" in estado or "NO RECOLECTADO" in estado or "ANULADO" in estado:
                motivo = "No movilizado por el courier (no se generó recolección) - correctamente excluido de factura"
                nivel_alerta = "NORMAL"
            elif any(e in estado for e in ["ENTREGADO", "CON NOVEDAD", "DEVOLUCION", "ENTREGA"]):
                motivo = "Entregada pero NO incluida en esta factura - revisar con courier (posible corte de periodo o guía omitida)"
                nivel_alerta = "REVISION_URGENTE"
            else:
                motivo = "Requiere revisión manual con el courier"
                nivel_alerta = "ATENCION"
                
            ciu_ori = manif_data.get("CIUDAD ORIGEN", "IBARRA")
            tipo_mov = "DESDE CD IBARRA" if ciu_ori == "IBARRA" else "CIUDAD-CIUDAD"
            
            guias_anuladas_list.append({
                "GUIA": guia,
                "TIPO GUIA": "CARGA" if manif_data.get("PRODUCTO") != "DOCUMENTOS_SERV" else "DOCUMENTO",
                "TIPO MOVIMIENTO": tipo_mov,
                "CIUDAD ORIGEN": ciu_ori,
                "CIUDAD DESTINO": manif_data.get("CIUDAD DESTINO", ""),
                "DESTINATARIO": manif_data.get("DESTINATARIO", ""),
                "CONTENIDO": manif_data.get("CONTENIDO", ""),
                "CATEGORIA": clasificar_contenido_transporte(manif_data.get("CONTENIDO", ""), manif_data.get("PRODUCTO", "")),
                "VALOR DECLARADO": manif_data.get("VALOR DECLARADO", 0.0),
                "ESTADO EN MANIFIESTO": manif_data.get("ESTADO", "NO FACTURADO"),
                "FECHA CREACION": manif_data.get("FECHA CREACION", ""),
                "FECHA ENTREGA": manif_data.get("FECHA ENTREGA", ""),
                "MOTIVO": motivo,
                "NIVEL_ALERTA": nivel_alerta
            })
            
    df_guias_anuladas = pd.DataFrame(guias_anuladas_list)

    df_todas_facturadas = pd.concat([df_det_carga, df_det_doc], ignore_index=True) if (not df_det_carga.empty or not df_det_doc.empty) else pd.DataFrame()

    total_manifiesto = len(df_manifiesto)
    total_carga = len(df_det_carga)
    total_doc = len(df_det_doc)
    total_seg = len(df_det_seg)
    total_anuladas = len(df_guias_anuladas)
    pct_anulacion = (total_anuladas / total_manifiesto * 100) if total_manifiesto > 0 else 0.0
    
    costo_flete_carga = df_det_carga["FLETE"].sum() if not df_det_carga.empty else 0.0
    costo_flete_doc = df_det_doc["FLETE"].sum() if not df_det_doc.empty else 0.0
    costo_seguro_total = df_det_carga["SEGURO"].sum() if not df_det_carga.empty else (df_det_seg["COSTO SEGURO"].sum() if not df_det_seg.empty else 0.0)
    costo_total_periodo = costo_flete_carga + costo_flete_doc + costo_seguro_total
    costo_promedio_guia = (costo_total_periodo / (total_carga + total_doc)) if (total_carga + total_doc) > 0 else 0.0

    resumen_movimiento = []
    if not df_todas_facturadas.empty:
        for tipo in ["DESDE CD IBARRA", "CIUDAD-CIUDAD"]:
            sub = df_todas_facturadas[df_todas_facturadas["TIPO MOVIMIENTO"] == tipo]
            n_g = len(sub)
            c_tot = sub["COSTO TOTAL"].sum()
            pct_c = (c_tot / costo_total_periodo * 100) if costo_total_periodo > 0 else 0.0
            resumen_movimiento.append({
                "TIPO DE MOVIMIENTO": tipo,
                "N° GUIAS": n_g,
                "COSTO TOTAL (USD)": c_tot,
                "% DEL COSTO TOTAL": pct_c
            })
    df_resumen_mov = pd.DataFrame(resumen_movimiento)

    df_top_ciudades = pd.DataFrame()
    if not df_todas_facturadas.empty and "CIUDAD DESTINO" in df_todas_facturadas.columns:
        top_c = df_todas_facturadas.groupby("CIUDAD DESTINO").agg(
            N_GUIAS=("GUIA", "count"),
            COSTO_TOTAL=("COSTO TOTAL", "sum")
        ).reset_index()
        top_c["PCT_COSTO_TOTAL"] = (top_c["COSTO_TOTAL"] / costo_total_periodo * 100) if costo_total_periodo > 0 else 0.0
        df_top_ciudades = top_c.sort_values("COSTO_TOTAL", ascending=False).head(15).copy()

    df_resumen_contenido = pd.DataFrame()
    if not df_todas_facturadas.empty and "CATEGORIA" in df_todas_facturadas.columns:
        cont_c = df_todas_facturadas.groupby("CATEGORIA").agg(
            N_GUIAS=("GUIA", "count"),
            COSTO_TOTAL=("COSTO TOTAL", "sum")
        ).reset_index()
        tot_g = len(df_todas_facturadas)
        cont_c["PCT_GUIAS"] = (cont_c["N_GUIAS"] / tot_g * 100) if tot_g > 0 else 0.0
        cont_c["PCT_COSTO"] = (cont_c["COSTO_TOTAL"] / costo_total_periodo * 100) if costo_total_periodo > 0 else 0.0
        df_resumen_contenido = cont_c.sort_values("COSTO_TOTAL", ascending=False).copy()

    df_pares_rutas = pd.DataFrame()
    if not df_todas_facturadas.empty:
        pares = df_todas_facturadas.groupby(["CIUDAD ORIGEN", "CIUDAD DESTINO", "TIPO MOVIMIENTO"]).agg(
            N_GUIAS=("GUIA", "count"),
            COSTO_TOTAL=("COSTO TOTAL", "sum")
        ).reset_index()
        pares["COSTO PROMEDIO"] = pares["COSTO_TOTAL"] / pares["N_GUIAS"]
        df_pares_rutas = pares.sort_values("COSTO_TOTAL", ascending=False)

    return {
        "kpis": {
            "guias_manifiesto": total_manifiesto,
            "guias_carga": total_carga,
            "guias_doc": total_doc,
            "guias_seguro": total_seg,
            "guias_anuladas": total_anuladas,
            "pct_anulacion": pct_anulacion,
            "costo_flete_carga": costo_flete_carga,
            "costo_flete_doc": costo_flete_doc,
            "costo_seguro_total": costo_seguro_total,
            "costo_total_periodo": costo_total_periodo,
            "costo_promedio_guia": costo_promedio_guia,
        },
        "df_det_carga": df_det_carga,
        "df_det_doc": df_det_doc,
        "df_det_seg": df_det_seg,
        "df_guias_anuladas": df_guias_anuladas,
        "df_resumen_mov": df_resumen_mov,
        "df_top_ciudades": df_top_ciudades,
        "df_resumen_contenido": df_resumen_contenido,
        "df_pares_rutas": df_pares_rutas
    }

# ==============================================================================
# 5. GENERADOR OFICIAL DE EXCEL (OPENPYXL CON FÓRMULAS VIVAS Y ESTILOS)
# ==============================================================================

def generar_excel_costos_transporte(datos_cruce: Dict[str, Any], mes_nombre: str = "PERIODO", anio: str = "2026") -> bytes:
    """
    Genera el libro oficial .xlsx con 7 pestañas, fórmulas vivas de Excel y estilos corporativos:
    1. Resumen Ejecutivo
    2. Analisis Ciudad-Ciudad
    3. Analisis Contenido
    4. Detalle Carga
    5. Detalle Documentos
    6. Detalle Seguro
    7. Guias Anuladas
    """
    wb = openpyxl.Workbook()
    
    NAVY_FILL = PatternFill(start_color="002D62", end_color="002D62", fill_type="solid")
    RED_FILL = PatternFill(start_color="CF0A2C", end_color="CF0A2C", fill_type="solid")
    LIGHT_GRAY_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    TOTAL_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    ALERT_FILL = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    
    FONT_HEADER = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    FONT_TITLE = Font(name="Arial", size=13, bold=True, color="002D62")
    FONT_SUBTITLE = Font(name="Arial", size=10, italic=True, color="555555")
    FONT_BOLD = Font(name="Arial", size=10, bold=True)
    FONT_TOTAL = Font(name="Arial", size=11, bold=True, color="991B1B")
    
    BORDER_THIN = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB")
    )
    BORDER_TOTAL = Border(
        top=Side(style="thin", color="000000"),
        bottom=Side(style="double", color="000000")
    )

    df_carga = datos_cruce["df_det_carga"]
    df_doc = datos_cruce["df_det_doc"]
    df_seg = datos_cruce["df_det_seg"]
    df_anul = datos_cruce["df_guias_anuladas"]

    # --------------------------------------------------------------------------
    # PESTAÑA 4: Detalle Carga
    # --------------------------------------------------------------------------
    ws_carga = wb.create_sheet(title="Detalle Carga")
    headers_carga = [
        "GUIA", "FECHA ENVIO", "CIUDAD ORIGEN", "CIUDAD DESTINO", "TIPO MOVIMIENTO", 
        "DESTINATARIO", "TELEFONO", "DIRECCION", "CONTENIDO", "CATEGORIA", 
        "TRAYECTO", "PIEZAS", "PESO", "FLETE", "SEGURO", "COSTO TOTAL", 
        "VALOR DECLARADO", "ESTADO ENTREGA", "FECHA ENTREGA", "RECIBE"
    ]
    ws_carga.append(headers_carga)
    for col_idx in range(1, len(headers_carga) + 1):
        cell = ws_carga.cell(row=1, column=col_idx)
        cell.fill = NAVY_FILL
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    num_rows_carga = len(df_carga)
    for r_idx, row in df_carga.iterrows():
        r = r_idx + 2
        ws_carga.append([
            row["GUIA"], str(row["FECHA ENVIO"])[:10], row["CIUDAD ORIGEN"], row["CIUDAD DESTINO"],
            f'=IF(C{r}="IBARRA","DESDE CD IBARRA","CIUDAD-CIUDAD")',
            row["DESTINATARIO"], str(row["TELEFONO"]), row["DIRECCION"], row["CONTENIDO"], row["CATEGORIA"],
            row["TRAYECTO"], row["PIEZAS"], row["PESO"], row["FLETE"],
            f'=IFERROR(INDEX(\'Detalle Seguro\'!$H:$H,MATCH(A{r},\'Detalle Seguro\'!$A:$A,0)),0)',
            f'=N{r}+O{r}',
            row["VALOR DECLARADO"], row["ESTADO ENTREGA"], str(row["FECHA ENTREGA"])[:10], row["RECIBE"]
        ])
        
        ws_carga.cell(row=r, column=12).number_format = '#,##0'
        ws_carga.cell(row=r, column=13).number_format = '#,##0.00'
        ws_carga.cell(row=r, column=14).number_format = '$#,##0.00'
        ws_carga.cell(row=r, column=15).number_format = '$#,##0.00'
        ws_carga.cell(row=r, column=16).number_format = '$#,##0.00'
        ws_carga.cell(row=r, column=17).number_format = '$#,##0.00'
        
        if r % 2 == 0:
            for c_i in range(1, len(headers_carga) + 1):
                ws_carga.cell(row=r, column=c_i).fill = LIGHT_GRAY_FILL
                
    if num_rows_carga > 0:
        tot_r_c = num_rows_carga + 2
        ws_carga.cell(row=tot_r_c, column=1, value="TOTAL").font = FONT_TOTAL
        ws_carga.cell(row=tot_r_c, column=12, value=f'=SUM(L2:L{tot_r_c-1})').number_format = '#,##0'
        ws_carga.cell(row=tot_r_c, column=13, value=f'=SUM(M2:M{tot_r_c-1})').number_format = '#,##0.00'
        ws_carga.cell(row=tot_r_c, column=14, value=f'=SUM(N2:N{tot_r_c-1})').number_format = '$#,##0.00'
        ws_carga.cell(row=tot_r_c, column=15, value=f'=SUM(O2:O{tot_r_c-1})').number_format = '$#,##0.00'
        ws_carga.cell(row=tot_r_c, column=16, value=f'=SUM(P2:P{tot_r_c-1})').number_format = '$#,##0.00'
        ws_carga.cell(row=tot_r_c, column=17, value=f'=SUM(Q2:Q{tot_r_c-1})').number_format = '$#,##0.00'
        for c_i in range(1, len(headers_carga) + 1):
            cell = ws_carga.cell(row=tot_r_c, column=c_i)
            cell.font = FONT_TOTAL
            cell.border = BORDER_TOTAL
            cell.fill = TOTAL_FILL
            
    ws_carga.freeze_panes = "A2"

    # --------------------------------------------------------------------------
    # PESTAÑA 5: Detalle Documentos
    # --------------------------------------------------------------------------
    ws_doc = wb.create_sheet(title="Detalle Documentos")
    ws_doc.append(headers_carga)
    for col_idx in range(1, len(headers_carga) + 1):
        cell = ws_doc.cell(row=1, column=col_idx)
        cell.fill = NAVY_FILL
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    num_rows_doc = len(df_doc)
    for r_idx, row in df_doc.iterrows():
        r = r_idx + 2
        ws_doc.append([
            row["GUIA"], str(row["FECHA ENVIO"])[:10], row["CIUDAD ORIGEN"], row["CIUDAD DESTINO"],
            f'=IF(C{r}="IBARRA","DESDE CD IBARRA","CIUDAD-CIUDAD")',
            row["DESTINATARIO"], str(row["TELEFONO"]), row["DIRECCION"], row["CONTENIDO"], row["CATEGORIA"],
            row["TRAYECTO"], row["PIEZAS"], row["PESO"], row["FLETE"],
            0.0, f'=N{r}+O{r}',
            0.0, row["ESTADO ENTREGA"], str(row["FECHA ENTREGA"])[:10], row["RECIBE"]
        ])
        ws_doc.cell(row=r, column=12).number_format = '#,##0'
        ws_doc.cell(row=r, column=13).number_format = '#,##0.00'
        ws_doc.cell(row=r, column=14).number_format = '$#,##0.00'
        ws_doc.cell(row=r, column=15).number_format = '$#,##0.00'
        ws_doc.cell(row=r, column=16).number_format = '$#,##0.00'
        ws_doc.cell(row=r, column=17).number_format = '$#,##0.00'
        if r % 2 == 0:
            for c_i in range(1, len(headers_carga) + 1):
                ws_doc.cell(row=r, column=c_i).fill = LIGHT_GRAY_FILL
                
    if num_rows_doc > 0:
        tot_r_d = num_rows_doc + 2
        ws_doc.cell(row=tot_r_d, column=1, value="TOTAL").font = FONT_TOTAL
        ws_doc.cell(row=tot_r_d, column=12, value=f'=SUM(L2:L{tot_r_d-1})').number_format = '#,##0'
        ws_doc.cell(row=tot_r_d, column=14, value=f'=SUM(N2:N{tot_r_d-1})').number_format = '$#,##0.00'
        ws_doc.cell(row=tot_r_d, column=16, value=f'=SUM(P2:P{tot_r_d-1})').number_format = '$#,##0.00'
        for c_i in range(1, len(headers_carga) + 1):
            cell = ws_doc.cell(row=tot_r_d, column=c_i)
            cell.font = FONT_TOTAL
            cell.border = BORDER_TOTAL
            cell.fill = TOTAL_FILL
            
    ws_doc.freeze_panes = "A2"

    # --------------------------------------------------------------------------
    # PESTAÑA 6: Detalle Seguro
    # --------------------------------------------------------------------------
    ws_seg = wb.create_sheet(title="Detalle Seguro")
    headers_seg = [
        "GUIA", "FECHA/HORA POLIZA", "ORIGEN", "DESTINO", "TRAYECTO", 
        "VALOR DECLARADO", "TASA SEGURO", "COSTO SEGURO", "FLETE ASOCIADO", 
        "COSTO TOTAL GUIA", "DESTINATARIO", "CONTENIDO", "CATEGORIA", "ESTADO"
    ]
    ws_seg.append(headers_seg)
    for col_idx in range(1, len(headers_seg) + 1):
        cell = ws_seg.cell(row=1, column=col_idx)
        cell.fill = RED_FILL
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    num_rows_seg = len(df_seg)
    for r_idx, row in df_seg.iterrows():
        r = r_idx + 2
        ws_seg.append([
            row["GUIA"], str(row["FECHA/HORA POLIZA"])[:19], row["ORIGEN"], row["DESTINO"], row["TRAYECTO"],
            row["VALOR DECLARADO"], row["TASA SEGURO"], row["COSTO SEGURO"],
            f'=IFERROR(INDEX(\'Detalle Carga\'!$N:$N,MATCH(A{r},\'Detalle Carga\'!$A:$A,0)),0)',
            f'=H{r}+I{r}',
            row["DESTINATARIO"], row["CONTENIDO"], row["CATEGORIA"], row["ESTADO"]
        ])
        ws_seg.cell(row=r, column=6).number_format = '$#,##0.00'
        ws_seg.cell(row=r, column=8).number_format = '$#,##0.00'
        ws_seg.cell(row=r, column=9).number_format = '$#,##0.00'
        ws_seg.cell(row=r, column=10).number_format = '$#,##0.00'
        if r % 2 == 0:
            for c_i in range(1, len(headers_seg) + 1):
                ws_seg.cell(row=r, column=c_i).fill = LIGHT_GRAY_FILL
                
    if num_rows_seg > 0:
        tot_r_s = num_rows_seg + 2
        ws_seg.cell(row=tot_r_s, column=1, value="TOTAL").font = FONT_TOTAL
        ws_seg.cell(row=tot_r_s, column=6, value=f'=SUM(F2:F{tot_r_s-1})').number_format = '$#,##0.00'
        ws_seg.cell(row=tot_r_s, column=8, value=f'=SUM(H2:H{tot_r_s-1})').number_format = '$#,##0.00'
        ws_seg.cell(row=tot_r_s, column=9, value=f'=SUM(I2:I{tot_r_s-1})').number_format = '$#,##0.00'
        ws_seg.cell(row=tot_r_s, column=10, value=f'=SUM(J2:J{tot_r_s-1})').number_format = '$#,##0.00'
        for c_i in range(1, len(headers_seg) + 1):
            cell = ws_seg.cell(row=tot_r_s, column=c_i)
            cell.font = FONT_TOTAL
            cell.border = BORDER_TOTAL
            cell.fill = TOTAL_FILL
            
    ws_seg.freeze_panes = "A2"

    # --------------------------------------------------------------------------
    # PESTAÑA 7: Guias Anuladas
    # --------------------------------------------------------------------------
    ws_anul = wb.create_sheet(title="Guias Anuladas")
    headers_anul = [
        "GUIA", "TIPO GUIA", "TIPO MOVIMIENTO", "CIUDAD ORIGEN", "CIUDAD DESTINO", 
        "DESTINATARIO", "CONTENIDO", "CATEGORIA", "VALOR DECLARADO", 
        "ESTADO EN MANIFIESTO", "FECHA CREACION", "FECHA ENTREGA", "MOTIVO"
    ]
    ws_anul.append(headers_anul)
    for col_idx in range(1, len(headers_anul) + 1):
        cell = ws_anul.cell(row=1, column=col_idx)
        cell.fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    for r_idx, row in df_anul.iterrows():
        r = r_idx + 2
        ws_anul.append([
            row["GUIA"], row["TIPO GUIA"], row["TIPO MOVIMIENTO"], row["CIUDAD ORIGEN"], row["CIUDAD DESTINO"],
            row["DESTINATARIO"], row["CONTENIDO"], row["CATEGORIA"], row["VALOR DECLARADO"],
            row["ESTADO EN MANIFIESTO"], str(row["FECHA CREACION"])[:10], str(row["FECHA ENTREGA"])[:10], row["MOTIVO"]
        ])
        ws_anul.cell(row=r, column=9).number_format = '$#,##0.00'
        if row.get("NIVEL_ALERTA") == "REVISION_URGENTE":
            for c_i in range(1, len(headers_anul) + 1):
                ws_anul.cell(row=r, column=c_i).fill = ALERT_FILL
                ws_anul.cell(row=r, column=c_i).font = Font(name="Arial", size=10, bold=True, color="991B1B")
        elif r % 2 == 0:
            for c_i in range(1, len(headers_anul) + 1):
                ws_anul.cell(row=r, column=c_i).fill = LIGHT_GRAY_FILL
                
    ws_anul.freeze_panes = "A2"

    # --------------------------------------------------------------------------
    # PESTAÑA 2: Analisis Ciudad-Ciudad
    # --------------------------------------------------------------------------
    ws_cc = wb.create_sheet(title="Analisis Ciudad-Ciudad")
    ws_cc["A1"] = "ANÁLISIS CIUDAD-CIUDAD vs. DESDE CD IBARRA"
    ws_cc["A1"].font = FONT_TITLE
    
    headers_cc1 = ["TIPO DE MOVIMIENTO", "N° GUÍAS", "COSTO TOTAL (USD)", "% DEL COSTO TOTAL"]
    ws_cc.append([])
    ws_cc.append(headers_cc1)
    row_h_cc1 = 3
    for c_i in range(1, 5):
        cell = ws_cc.cell(row=row_h_cc1, column=c_i)
        cell.fill = RED_FILL
        cell.font = FONT_HEADER
        
    max_c = max(2, num_rows_carga + 1)
    max_d = max(2, num_rows_doc + 1)
    
    ws_cc.append([
        "DESDE CD IBARRA",
        f'=COUNTIFS(\'Detalle Carga\'!$E$2:$E${max_c},"DESDE CD IBARRA")+COUNTIFS(\'Detalle Documentos\'!$E$2:$E${max_d},"DESDE CD IBARRA")',
        f'=SUMIFS(\'Detalle Carga\'!$P$2:$P${max_c},\'Detalle Carga\'!$E$2:$E${max_c},"DESDE CD IBARRA")+SUMIFS(\'Detalle Documentos\'!$P$2:$P${max_d},\'Detalle Documentos\'!$E$2:$E${max_d},"DESDE CD IBARRA")',
        '=C4/$C$6'
    ])
    ws_cc.append([
        "CIUDAD-CIUDAD",
        f'=COUNTIFS(\'Detalle Carga\'!$E$2:$E${max_c},"CIUDAD-CIUDAD")+COUNTIFS(\'Detalle Documentos\'!$E$2:$E${max_d},"CIUDAD-CIUDAD")',
        f'=SUMIFS(\'Detalle Carga\'!$P$2:$P${max_c},\'Detalle Carga\'!$E$2:$E${max_c},"CIUDAD-CIUDAD")+SUMIFS(\'Detalle Documentos\'!$P$2:$P${max_d},\'Detalle Documentos\'!$E$2:$E${max_d},"CIUDAD-CIUDAD")',
        '=C5/$C$6'
    ])
    ws_cc.append(["TOTAL", '=SUM(B4:B5)', '=SUM(C4:C5)', '=SUM(D4:D5)'])
    
    for r in range(4, 7):
        ws_cc.cell(row=r, column=2).number_format = '#,##0'
        ws_cc.cell(row=r, column=3).number_format = '$#,##0.00'
        ws_cc.cell(row=r, column=4).number_format = '0.0%'
        if r == 6:
            for c_i in range(1, 5):
                ws_cc.cell(row=r, column=c_i).font = FONT_TOTAL
                ws_cc.cell(row=r, column=c_i).fill = TOTAL_FILL
                ws_cc.cell(row=r, column=c_i).border = BORDER_TOTAL

    ws_cc.append([])
    ws_cc.append(["DETALLE POR RUTAS Y PARES (ORIGEN -> DESTINO)"])
    ws_cc.cell(row=ws_cc.max_row, column=1).font = FONT_TITLE
    headers_rutas = ["CIUDAD ORIGEN", "CIUDAD DESTINO", "TIPO MOVIMIENTO", "N° GUÍAS", "COSTO TOTAL (USD)", "COSTO PROMEDIO"]
    ws_cc.append(headers_rutas)
    r_rutas_h = ws_cc.max_row
    for c_i in range(1, len(headers_rutas) + 1):
        cell = ws_cc.cell(row=r_rutas_h, column=c_i)
        cell.fill = NAVY_FILL
        cell.font = FONT_HEADER
        
    df_pares = datos_cruce["df_pares_rutas"]
    for r_idx, row in df_pares.iterrows():
        curr_r = ws_cc.max_row + 1
        ws_cc.append([
            row["CIUDAD ORIGEN"], row["CIUDAD DESTINO"], row["TIPO MOVIMIENTO"],
            row["N_GUIAS"], row["COSTO_TOTAL"], row["COSTO PROMEDIO"]
        ])
        ws_cc.cell(row=curr_r, column=4).number_format = '#,##0'
        ws_cc.cell(row=curr_r, column=5).number_format = '$#,##0.00'
        ws_cc.cell(row=curr_r, column=6).number_format = '$#,##0.00'

    # --------------------------------------------------------------------------
    # PESTAÑA 3: Analisis Contenido
    # --------------------------------------------------------------------------
    ws_cont = wb.create_sheet(title="Analisis Contenido")
    ws_cont["A1"] = "ANÁLISIS DE COSTOS POR CATEGORÍA DE CONTENIDO"
    ws_cont["A1"].font = FONT_TITLE
    
    headers_cont = ["CATEGORÍA", "N° GUÍAS", "COSTO TOTAL (USD)", "% GUÍAS", "% COSTO"]
    ws_cont.append([])
    ws_cont.append(headers_cont)
    r_cont_h = 3
    for c_i in range(1, len(headers_cont) + 1):
        cell = ws_cont.cell(row=r_cont_h, column=c_i)
        cell.fill = RED_FILL
        cell.font = FONT_HEADER
        
    categorias_lista = [
        "DOCUMENTOS", "MERCADERÍA", "ACCESORIOS / PRENDAS", "VENTA WEB", 
        "DEVOLUCIÓN", "PUBLICIDAD", "MOBILIARIO / EQUIPOS", "INSUMOS / ADMINISTRATIVO", 
        "SIN ESPECIFICAR", "OTROS"
    ]
    
    start_r_cont = 4
    for idx, cat in enumerate(categorias_lista):
        r = start_r_cont + idx
        ws_cont.append([
            cat,
            f'=COUNTIFS(\'Detalle Carga\'!$J$2:$J${max_c},"{cat}")+COUNTIFS(\'Detalle Documentos\'!$J$2:$J${max_d},"{cat}")',
            f'=SUMIFS(\'Detalle Carga\'!$P$2:$P${max_c},\'Detalle Carga\'!$J$2:$J${max_c},"{cat}")+SUMIFS(\'Detalle Documentos\'!$P$2:$P${max_d},\'Detalle Documentos\'!$J$2:$J${max_d},"{cat}")',
            f'=B{r}/$B${start_r_cont+len(categorias_lista)}',
            f'=C{r}/$C${start_r_cont+len(categorias_lista)}'
        ])
        ws_cont.cell(row=r, column=2).number_format = '#,##0'
        ws_cont.cell(row=r, column=3).number_format = '$#,##0.00'
        ws_cont.cell(row=r, column=4).number_format = '0.0%'
        ws_cont.cell(row=r, column=5).number_format = '0.0%'
        if r % 2 == 0:
            for c_i in range(1, 6):
                ws_cont.cell(row=r, column=c_i).fill = LIGHT_GRAY_FILL
                
    tot_r_cont = start_r_cont + len(categorias_lista)
    ws_cont.append([
        "TOTAL",
        f'=SUM(B4:B{tot_r_cont-1})',
        f'=SUM(C4:C{tot_r_cont-1})',
        f'=SUM(D4:D{tot_r_cont-1})',
        f'=SUM(E4:E{tot_r_cont-1})'
    ])
    ws_cont.cell(row=tot_r_cont, column=2).number_format = '#,##0'
    ws_cont.cell(row=tot_r_cont, column=3).number_format = '$#,##0.00'
    ws_cont.cell(row=tot_r_cont, column=4).number_format = '0.0%'
    ws_cont.cell(row=tot_r_cont, column=5).number_format = '0.0%'
    for c_i in range(1, 6):
        cell = ws_cont.cell(row=tot_r_cont, column=c_i)
        cell.font = FONT_TOTAL
        cell.border = BORDER_TOTAL
        cell.fill = TOTAL_FILL

    # --------------------------------------------------------------------------
    # PESTAÑA 1: Resumen Ejecutivo
    # --------------------------------------------------------------------------
    ws_resumen = wb.create_sheet(title="Resumen Ejecutivo", index=0)
    
    ws_resumen.merge_cells("A1:D1")
    ws_resumen["A1"] = f"RESUMEN EJECUTIVO DE COSTOS DE TRANSPORTE - FASHION CLUB (AEROPOSTALE)"
    ws_resumen["A1"].font = Font(name="Arial", size=13, bold=True, color="FFFFFF")
    ws_resumen["A1"].fill = NAVY_FILL
    ws_resumen["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws_resumen.merge_cells("A2:D2")
    ws_resumen["A2"] = f"Centro de Distribución Ibarra. Cruce Manifiesto de Recolección vs. Factura del Courier (Carga + Documentos + Seguro). Período: {mes_nombre} {anio}"
    ws_resumen["A2"].font = FONT_SUBTITLE
    ws_resumen["A2"].alignment = Alignment(horizontal="center", vertical="center")

    # 1. INDICADORES DE GESTIÓN (KPI)
    ws_resumen["A4"] = "1. INDICADORES DE GESTION (KPI)"
    ws_resumen["A4"].font = FONT_TITLE
    
    kpis_tabla = [
        ("Guías en el Manifiesto (total del mes)", f'=COUNTA(\'Detalle Carga\'!$A$2:$A${max_c})+COUNTA(\'Detalle Documentos\'!$A$2:$A${max_d})+COUNTA(\'Guias Anuladas\'!$A$2:$A${max(2, len(df_anul)+1)})', '#,##0'),
        ("Guías facturadas - Carga", f'=COUNTA(\'Detalle Carga\'!$A$2:$A${max_c})', '#,##0'),
        ("Guías facturadas - Documentos", f'=COUNTA(\'Detalle Documentos\'!$A$2:$A${max_d})', '#,##0'),
        ("Guías con Seguro contratado", f'=COUNTA(\'Detalle Seguro\'!$A$2:$A${max(2, num_rows_seg+1)})', '#,##0'),
        ("Guías ANULADAS / no facturadas", f'=COUNTA(\'Guias Anuladas\'!$A$2:$A${max(2, len(df_anul)+1)})', '#,##0'),
        ("% de Anulación sobre el Manifiesto", '=B9/B5', '0.0%'),
    ]
    for idx, (label, formula, num_fmt) in enumerate(kpis_tabla):
        r = 5 + idx
        ws_resumen.cell(row=r, column=1, value=label).font = FONT_BOLD
        c_val = ws_resumen.cell(row=r, column=2, value=formula)
        c_val.font = Font(name="Arial", size=11, bold=True, color="991B1B")
        c_val.number_format = num_fmt
        c_val.alignment = Alignment(horizontal="right")
        ws_resumen.cell(row=r, column=1).border = BORDER_THIN
        ws_resumen.cell(row=r, column=2).border = BORDER_THIN

    # 2. COSTOS DEL PERIODO (USD)
    ws_resumen["A12"] = "2. COSTOS DEL PERIODO (USD)"
    ws_resumen["A12"].font = FONT_TITLE
    
    costos_tabla = [
        ("Costo Flete - Carga", f'=\'Detalle Carga\'!N{num_rows_carga+2}' if num_rows_carga>0 else 0.0),
        ("Costo Flete - Documentos", f'=\'Detalle Documentos\'!N{num_rows_doc+2}' if num_rows_doc>0 else 0.0),
        ("Costo Seguro (todas las guías)", f'=\'Detalle Carga\'!O{num_rows_carga+2}' if num_rows_carga>0 else (f'=\'Detalle Seguro\'!H{num_rows_seg+2}' if num_rows_seg>0 else 0.0)),
        ("COSTO TOTAL DEL PERIODO", '=SUM(B13:B15)'),
        ("Costo promedio por guía facturada", '=B16/(B6+B7)'),
    ]
    for idx, (label, formula) in enumerate(costos_tabla):
        r = 13 + idx
        ws_resumen.cell(row=r, column=1, value=label).font = FONT_BOLD
        c_val = ws_resumen.cell(row=r, column=2, value=formula)
        c_val.font = Font(name="Arial", size=11, bold=True, color="991B1B" if r!=16 else "002D62")
        c_val.number_format = '$#,##0.00'
        c_val.alignment = Alignment(horizontal="right")
        if r == 16:
            ws_resumen.cell(row=r, column=1).fill = TOTAL_FILL
            ws_resumen.cell(row=r, column=2).fill = TOTAL_FILL
            ws_resumen.cell(row=r, column=1).border = BORDER_TOTAL
            ws_resumen.cell(row=r, column=2).border = BORDER_TOTAL
        else:
            ws_resumen.cell(row=r, column=1).border = BORDER_THIN
            ws_resumen.cell(row=r, column=2).border = BORDER_THIN

    # 3. CIUDAD-CIUDAD vs. DESDE CD IBARRA
    ws_resumen["A19"] = "3. CIUDAD-CIUDAD vs. DESDE CD IBARRA"
    ws_resumen["A19"].font = FONT_TITLE
    
    headers_res_mov = ["TIPO DE MOVIMIENTO", "N° GUÍAS", "COSTO TOTAL (USD)", "% DEL COSTO TOTAL"]
    ws_resumen.append([])
    ws_resumen.append(headers_res_mov)
    r_h_m = 21
    for c_i in range(1, 5):
        cell = ws_resumen.cell(row=r_h_m, column=c_i)
        cell.fill = RED_FILL
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center")
        
    ws_resumen.append(["DESDE CD IBARRA", "='Analisis Ciudad-Ciudad'!B4", "='Analisis Ciudad-Ciudad'!C4", "='Analisis Ciudad-Ciudad'!D4"])
    ws_resumen.append(["CIUDAD-CIUDAD", "='Analisis Ciudad-Ciudad'!B5", "='Analisis Ciudad-Ciudad'!C5", "='Analisis Ciudad-Ciudad'!D5"])
    for r in [22, 23]:
        ws_resumen.cell(row=r, column=1).border = BORDER_THIN
        ws_resumen.cell(row=r, column=2).border = BORDER_THIN
        ws_resumen.cell(row=r, column=3).border = BORDER_THIN
        ws_resumen.cell(row=r, column=4).border = BORDER_THIN
        ws_resumen.cell(row=r, column=2).number_format = '#,##0'
        ws_resumen.cell(row=r, column=3).number_format = '$#,##0.00'
        ws_resumen.cell(row=r, column=4).number_format = '0.0%'

    # 4. TOP 15 CIUDADES DESTINO POR COSTO
    ws_resumen["A25"] = "4. TOP 15 CIUDADES DESTINO POR COSTO"
    ws_resumen["A25"].font = FONT_TITLE
    
    headers_top_c = ["CIUDAD DESTINO", "N° GUÍAS", "COSTO TOTAL (USD)", "% DEL COSTO TOTAL"]
    ws_resumen.append([])
    ws_resumen.append(headers_top_c)
    r_h_top = 27
    for c_i in range(1, 5):
        cell = ws_resumen.cell(row=r_h_top, column=c_i)
        cell.fill = RED_FILL
        cell.font = FONT_HEADER
        cell.alignment = Alignment(horizontal="center")
        
    df_top15 = datos_cruce["df_top_ciudades"]
    for idx, row in df_top15.iterrows():
        curr_r = 28 + idx
        n_g_val = row.get("N_GUIAS", row.get("N° GUIAS", row.get("N° GUÍAS", 0)))
        c_t_val = row.get("COSTO_TOTAL", row.get("COSTO TOTAL (USD)", 0.0))
        pct_t_val = row.get("PCT_COSTO_TOTAL", row.get("% DEL COSTO TOTAL", 0.0))
        ws_resumen.append([row.get("CIUDAD DESTINO", ""), n_g_val, c_t_val, pct_t_val / 100.0])
        ws_resumen.cell(row=curr_r, column=1).border = BORDER_THIN
        ws_resumen.cell(row=curr_r, column=2).border = BORDER_THIN
        ws_resumen.cell(row=curr_r, column=3).border = BORDER_THIN
        ws_resumen.cell(row=curr_r, column=4).border = BORDER_THIN
        ws_resumen.cell(row=curr_r, column=2).number_format = '#,##0'
        ws_resumen.cell(row=curr_r, column=3).number_format = '$#,##0.00'
        ws_resumen.cell(row=curr_r, column=4).number_format = '0.0%'
        if curr_r % 2 == 0:
            for c_i in range(1, 5):
                ws_resumen.cell(row=curr_r, column=c_i).fill = LIGHT_GRAY_FILL

    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = cell.value
                if val:
                    val_str = str(val)
                    if val_str.startswith("="):
                        val_str = "1234567.89"
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
