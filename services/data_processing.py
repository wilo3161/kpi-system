import pandas as pd
import re
import unicodedata
from typing import Optional, Tuple
import streamlit as st

TALLAS_VALIDAS = {
    'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'ÚNICA',
    'XSMALL', 'SMALL', 'MEDIUM', 'LARGE', 'XLARGE', 'XXLARGE',
    'EXTRA SMALL', 'EXTRA LARGE'
}
TALLAS_EXTRA = {
    'XSMALL': 'XS', 'SMALL': 'S', 'MEDIUM': 'M', 'LARGE': 'L',
    'XLARGE': 'XL', 'XXLARGE': 'XXL', 'EXTRA SMALL': 'XS', 'EXTRA LARGE': 'XL'
}
COLOR_ALIASES = {
    'DARK BLACK': 'Negro', 'BLEACH': 'Blanco Bleach', 'CADET NAVY': 'Azul Navy',
    'EARTH RED': 'Rojo Tierra', 'EGRET': 'Blanco Egret', 'BIRCH': 'Beige',
    'CHARCOAL HEATHER GREY': 'Gris Carbón', 'LIGHT HEATHER GREY': 'Gris Claro',
    'HOT CHOCOLATE': 'Marrón Chocolate', 'GREEN GABLES': 'Verde',
    'KENTUCKY BLUE': 'Azul Kentucky', 'PORT ROYALE': 'Morado', 'POPCORN': 'Amarillo',
    'PRIMROSE PINK': 'Rosa', 'TRUE RED': 'Rojo', 'SURF SPRAY': 'Azul Claro',
    'FLINT': 'Gris Flint', 'OLIVINE': 'Verde Oliva', 'CORE DENIM': 'Denim',
    'SUEDE BLUE': 'Azul Suede',
}

def normalizar_para_mapeo(texto):
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def _extraer_digitos(valor):
    if pd.isna(valor): return ""
    s = str(valor).strip()
    try:
        flt = float(s)
        return str(int(round(flt)))
    except ValueError:
        return re.sub(r'\D', '', s)

def extraer_entero(val):
    if pd.isna(val): return 0
    if isinstance(val, (int, float)): return int(round(val))
    s = str(val).strip()
    try:
        s_norm = s.replace(',', '.')
        parts = s_norm.split('.')
        if len(parts) > 2:
            s_norm = ''.join(parts[:-1]) + '.' + parts[-1]
        flt = float(s_norm)
        return int(round(flt))
    except ValueError:
        s_digits = re.sub(r'\D', '', s)
        return int(s_digits) if s_digits else 0

def parse_producto_color_talla(descripcion):
    """Separa una descripción de producto en (producto, color, talla)."""
    original = descripcion.strip()
    texto = original.upper()
    tokens = texto.split()
    talla_raw = 'ÚNICA'
    color_raw = ''
    
    # Buscar secuencia de palabras que coincida con una talla válida, de atrás hacia adelante
    for i in range(len(tokens) - 1, -1, -1):
        for j in range(i + 1, len(tokens) + 1):
            sub = ' '.join(tokens[i:j])
            if sub in TALLAS_VALIDAS:
                talla_raw = sub
                color_raw = tokens[i - 1] if i > 0 else ''
                producto = ' '.join(tokens[:i - 1]) if i > 0 else ' '.join(tokens[:i])
                break
        if talla_raw != 'ÚNICA':
            break
    else:
        producto = original

    talla = TALLAS_EXTRA.get(talla_raw, talla_raw)
    color = normalizar_color(color_raw) if color_raw else ''
    return producto, color, talla

def extraer_talla(producto):
    return parse_producto_color_talla(producto)[2]

def extraer_color(producto):
    return parse_producto_color_talla(producto)[1]

def normalizar_color(color):
    c = str(color).strip().upper()
    for key, val in COLOR_ALIASES.items():
        if c == key.upper():
            return val
    return c

def orden_talla(talla):
    orden = {'XS':1, 'S':2, 'M':3, 'L':4, 'XL':5, 'XXL':6, 'XXXL':7, 'ÚNICA':99}
    return orden.get(talla, 99)

def clasificar_tipo_prenda(producto):
    p = str(producto).upper()
    mapeo = [
        ('TRACK JACKETS', 'Chaqueta Track', 'JACKET'), ('WOVEN SHIRTS', 'Camisa Tejida', 'SHIRT'),
        ('WOVEN PANTS', 'Pantalón Tejido', 'PANTS'), ('KNIT PANTS', 'Pantalón Knit', 'PANTS'),
        ('SS TEES', 'Camiseta M/C', 'TEE'), ('LS TEES', 'Camiseta M/L', 'TEE'),
        ('TEES', 'Camiseta', 'TEE'), ('SS SOLID POLO', 'Polo', 'POLO'),
        ('POLO', 'Polo', 'POLO'), ('HOODIE', 'Hoodie', 'HOODIE'), ('FLEECE', 'Fleece', 'FLEECE'),
        ('SHIRTS', 'Camisa', 'SHIRT'), ('PANTS', 'Pantalón', 'PANTS'), ('JACKET', 'Chaqueta', 'JACKET'),
        ('SHORTS', 'Shorts', 'SHORTS'), ('LEGGING', 'Legging', 'LEGGING'), ('DRESS', 'Vestido', 'DRESS'),
        ('SKIRT', 'Falda', 'SKIRT'), ('FUNDA', 'Funda', 'FUNDA'), ('BAG', 'Funda', 'FUNDA'), ('PLASTIG', 'Funda', 'FUNDA'), ('PLASTIC', 'Funda', 'FUNDA'),
    ]
    for pattern, nombre, abrev in mapeo:
        if pattern in p:
            return nombre, abrev
    return ('Accesorio', 'ACC')

def extraer_genero(producto):
    p = str(producto).upper()
    if 'GUYS' in p: return 'GUYS'
    if 'GIRLS' in p: return 'GIRLS'
    return 'UNISEX'

_MAPEO_DIRECTO = {
    'AERO CCI': 'Tiendas', 'AERO DAULE': 'Tiendas', 'AERO LAGO AGRIO': 'Tiendas', 'AERO PLAYAS': 'Tiendas',
    'AEROPOSTALE 6 DE DICIEMBRE': 'Tiendas', 'BOMBOLI': 'Tiendas', 'AEROPOSTALE CAYAMBE': 'Tiendas',
    'AEROPOSTALE EL COCA': 'Tiendas', 'AEROPOSTALE PEDERNALES': 'Tiendas', 'AMBATO': 'Tiendas',
    'BABAHOYO': 'Tiendas', 'BAHIA DE CARAQUEZ': 'Tiendas', 'CARAPUNGO': 'Tiendas', 'LOS CEIBOS': 'Tiendas',
    'CONDADO SHOPPING': 'Tiendas', 'CUENCA': 'Tiendas', 'CUENCA CENTRO HISTORICO': 'Tiendas',
    'DURAN': 'Tiendas', 'LA PLAZA': 'Tiendas', 'MACHALA': 'Tiendas', 'MALL DEL SUR': 'Tiendas',
    'MALL DEL PACIFICO': 'Tiendas', 'MALL DEL SOL': 'Tiendas', 'MANTA': 'Tiendas', 'MILAGRO': 'Tiendas',
    'MULTIPLAZA RIOBAMBA': 'Tiendas', 'PASEO AMBATO': 'Tiendas', 'PENINSULA': 'Tiendas',
    'PORTOVIEJO': 'Tiendas', 'QUEVEDO': 'Tiendas', 'RIOBAMBA': 'Tiendas', 'RIOCENTRO EL DORADO': 'Tiendas',
    'RIO CENTRO NORTE': 'Tiendas', 'SAN LUIS': 'Tiendas', 'SANTO DOMINGO': 'Tiendas',
    'AEROPOSTALE BOMBOLI': 'Tiendas', 'AEROPOSTALE PASAJE': 'Tiendas', 'AEROPOSTALE MALL DEL RIO GYE': 'Tiendas',
    'OIL UNO': 'Price Club', 'PRICE CLUB CITY MALL': 'Price Club', 'PRICE CLUB GUAYAQUIL': 'Price Club',
    'PRICE CLUB MACHALA': 'Price Club', 'PRICE CLUB MATRIZ': 'Price Club', 'PRICE PORTOVIEJO': 'Price Club',
    'VENTAS POR MAYOR': 'Ventas por Mayor', 'TIENDA MOVIL - WEB': 'Tienda Web', 'BODEGA FALLAS': 'Fallas',
}
_MAPEO_DIRECTO_NORM = {normalizar_para_mapeo(k): v for k, v in _MAPEO_DIRECTO.items()}

def clasificar_categoria(bodega_destino, categoria_detalle="", grupo=""):
    cat_det = str(categoria_detalle).upper() if not pd.isna(categoria_detalle) else ""
    grp = str(grupo).upper() if not pd.isna(grupo) else ""
    if 'FUNDA' in cat_det or 'BAG' in cat_det or 'FUNDA' in grp or 'BAG' in grp or 'PLASTIC' in grp: 
        return 'Fundas'
    if 'ACCESORIOS PRICE CLUB' in cat_det: 
        return 'Price Club'
        
    bodega_norm = normalizar_para_mapeo(bodega_destino)
    if any(p in bodega_norm for p in ['PRICE', 'OIL']): return 'Price Club'
    if any(p in bodega_norm for p in ['VENTAS POR MAYOR', 'MAYORISTA']): return 'Ventas por Mayor'
    if any(p in bodega_norm for p in ['TIENDA WEB', 'MOVIL', 'WEB']): return 'Tienda Web'
    if 'FALLAS' in bodega_norm: return 'Fallas'
    if 'AERO' in bodega_norm: return 'Tiendas'
    if bodega_norm in _MAPEO_DIRECTO_NORM: return _MAPEO_DIRECTO_NORM[bodega_norm]
    return 'Tiendas'

def clean_corrupted_quantity(val):
    num = extraer_entero(val)
    if num > 10000000 and num % 1000000 == 0:
        return int(num / 1000000)
    return num

def _safe_numeric_int(series):
    return series.apply(clean_corrupted_quantity)

def extraer_float(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).strip().replace(' ', '')
    s = s.replace('.', '')
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        s = re.sub(r'[^\d.]', '', s)
        return float(s) if s else 0.0

def _safe_numeric_conversion(series):
    return series.apply(extraer_float)

def _is_true_quantity(df, col_name):
    try:
        sample = df[col_name].dropna().head(100)
        for val in sample:
            num = extraer_entero(val)
            if num > 10000000:
                if num % 1000000 != 0:
                    return False
        return True
    except:
        return False

def _find_true_quantity_col(df, cols_dict):
    for exact in ['CANTIDAD', 'TOTAL PRENDAS', 'CANT_PRENDA', 'CANTIDAD TOTAL', 'CANTIDAD TRANSFERIDA', 'UNIDADES', 'PRENDAS', 'CANT', 'QTY']:
        col = cols_dict.get(exact)
        if col and _is_true_quantity(df, col):
            return col
    for k, col in cols_dict.items():
        if any(x in k for x in ['CANTIDAD', 'CANT', 'TOTAL', 'PRENDA', 'UNIDAD', 'UNID', 'QTY']) and 'BARRA' not in k and 'CODIGO' not in k and 'PRECIO' not in k:
            if _is_true_quantity(df, col):
                return col
    for k, col in cols_dict.items():
        if not any(x in k for x in ['BARRA', 'CODIGO', 'PRECIO', 'SECUENCIAL', 'NUMERO', 'RUC', 'FECHA', 'TIENDA', 'BODEGA']):
            if _is_true_quantity(df, col):
                return col
    return None

@st.cache_data(show_spinner=False)
def procesar_archivos(df_transferencias, df_detalle):
    # --- Detalle ---
    det_cols = {normalizar_para_mapeo(c): c for c in df_detalle.columns}
    sec_col = det_cols.get('SECUENCIAL') or det_cols.get('SECUENCIAL FACTURA') or next((det_cols[k] for k in det_cols if any(x in k for x in ['SECUENCIAL', 'TRANSFERENCIA', 'NUMERO', 'FACTURA', 'GUIA', 'DOCUMENTO', 'SEC', 'NRO'])), None)
    cant_col = _find_true_quantity_col(df_detalle, det_cols)
    
    # Priorizar coincidencias exactas para producto para evitar confundir 'Codigo Producto' con 'Producto'
    prod_col = det_cols.get('PRODUCTO') or det_cols.get('DESCRIPCION') or det_cols.get('ITEM') or det_cols.get('NOMBRE')
    if not prod_col:
        prod_col = next((det_cols[k] for k in det_cols if any(x in k for x in ['PRODUCTO', 'DESCRIPCION', 'ITEM', 'ARTICULO', 'NOMBRE', 'PROD', 'DETALLE']) and not any(y in k for y in ['CODIGO', 'COD', 'BARRA', 'ID'])), None)
        
    cat_col = det_cols.get('CATEGORIA') or next((det_cols[k] for k in det_cols if 'CATEGORIA' in k or 'CAT' in k), None)
    grupo_col = det_cols.get('GRUPO') or next((det_cols[k] for k in det_cols if 'GRUPO' in k or 'GRP' in k), None)
    costo_col = det_cols.get('COSTO') or next((det_cols[k] for k in det_cols if 'COSTO' in k or 'PRECIO' in k or 'VALOR' in k), None)
    bodega_recibe_col = det_cols.get('BODEGA RECIBE') or next((det_cols[k] for k in det_cols if any(x in k for x in ['BODEGA RECIBE', 'BODEGA', 'DESTINO', 'TIENDA', 'SUCURSAL'])), None)
    
    if not all([sec_col, cant_col, prod_col]):
        missing = []
        if not sec_col: missing.append("Secuencial/Transferencia")
        if not cant_col: missing.append("Cantidad")
        if not prod_col: missing.append("Producto/Descripción")
        raise ValueError(f"El archivo de detalle debe tener al menos: {', '.join(missing)}.")

    df_det = df_detalle.copy()
    df_det['SECUENCIAL'] = df_det[sec_col].apply(_extraer_digitos).astype(str)
    df_det = df_det[df_det['SECUENCIAL'] != '']
    df_det['CANTIDAD'] = _safe_numeric_int(df_det[cant_col])
    df_det['PRODUCTO_ORIGINAL'] = df_det[prod_col].astype(str)
    
    parsed = df_det['PRODUCTO_ORIGINAL'].apply(parse_producto_color_talla)
    df_det['PRODUCTO_BASE'] = parsed.apply(lambda x: x[0])
    df_det['COLOR_NORM'] = parsed.apply(lambda x: x[1])
    df_det['TALLA'] = parsed.apply(lambda x: x[2])
    df_det['TALLA_ORDEN'] = df_det['TALLA'].apply(orden_talla)
    df_det[['TIPO_PRENDA_ES', 'TIPO_ABREV']] = df_det['PRODUCTO_BASE'].apply(
        lambda x: pd.Series(clasificar_tipo_prenda(x))
    )
    df_det['GENERO'] = df_det['PRODUCTO_BASE'].apply(extraer_genero)
    df_det['GRUPO'] = df_det[grupo_col].astype(str) if grupo_col else ''
    df_det['CATEGORIA'] = df_det[cat_col].astype(str) if cat_col else ''
    df_det['TIENDA'] = df_det[bodega_recibe_col].astype(str) if bodega_recibe_col else ''
    
    if costo_col:
        df_det['COSTO'] = _safe_numeric_conversion(df_det[costo_col])
    else:
        df_det['COSTO'] = 0.0
        
    cond_funda = (
        df_det['CATEGORIA'].str.upper().str.contains('FUNDA', na=False) |
        df_det['CATEGORIA'].str.upper().str.contains('BAG', na=False) |
        df_det['PRODUCTO_ORIGINAL'].str.upper().str.startswith('FUNDA LENTES DE SOL', na=False) |
        df_det['PRODUCTO_ORIGINAL'].str.upper().str.startswith('AERO PLASTIC BAG', na=False) |
        df_det['PRODUCTO_ORIGINAL'].str.upper().str.contains('FUNDA', na=False) |
        df_det['PRODUCTO_ORIGINAL'].str.upper().str.contains('BAG', na=False) |
        df_det['PRODUCTO_ORIGINAL'].str.upper().str.contains('PLASTIC', na=False)
    )
    df_det['ES_FUNDA'] = cond_funda

    # Pre-calculamos para evitar lambdas complejas en groupby
    df_det['CANT_PRENDA'] = df_det['CANTIDAD'].where(~df_det['ES_FUNDA'], 0)
    df_det['CANT_FUNDA'] = df_det['CANTIDAD'].where(df_det['ES_FUNDA'], 0)

    grupo_det = df_det.groupby('SECUENCIAL').agg(
        CANTIDAD_TOTAL_DETALLE=('CANTIDAD', 'sum'),
        PRENDAS=('CANT_PRENDA', 'sum'),
        FUNDAS=('CANT_FUNDA', 'sum'),
        COSTO_TOTAL=('COSTO', 'sum'),
        CATEGORIA_DET=('CATEGORIA', 'first'),
        GRUPO=('GRUPO', 'first'),
    ).reset_index()

    # --- Transferencias ---
    trans_cols = {normalizar_para_mapeo(c): c for c in df_transferencias.columns}
    sec_col_t = next((trans_cols[k] for k in trans_cols if any(x in k for x in ['SECUENCIAL', 'TRANSFERENCIA', 'NUMERO', 'FACTURA', 'GUIA', 'DOCUMENTO', 'SEC', 'NRO'])), None)
    cant_col_t = _find_true_quantity_col(df_transferencias, trans_cols)
    
    # Preferir BODEGA DESTINO o BODEGA RECIBE sobre SUCURSAL DESTINO
    tienda_col = None
    for exact in ['BODEGA DESTINO', 'BODEGA RECIBE', 'DESTINO']:
        if exact in trans_cols:
            tienda_col = trans_cols[exact]
            break
    if not tienda_col:
        tienda_col = next((trans_cols[k] for k in trans_cols if any(x in k for x in ['SUCURSAL DESTINO', 'BODEGA', 'TIENDA', 'SUCURSAL', 'RECIBE'])), None)
        
    fecha_col_t = next((trans_cols[k] for k in trans_cols if 'FECHA' in k), None)

    if not all([sec_col_t, cant_col_t, tienda_col]):
        missing_t = []
        if not sec_col_t: missing_t.append("Secuencial/Transferencia")
        if not cant_col_t: missing_t.append("Cantidad")
        if not tienda_col: missing_t.append("Bodega/Sucursal Destino")
        raise ValueError(f"El archivo de transferencias debe tener al menos: {', '.join(missing_t)}.")

    df_trans = df_transferencias.copy()
    df_trans['SECUENCIAL'] = df_trans[sec_col_t].apply(_extraer_digitos).astype(str)
    df_trans = df_trans[df_trans['SECUENCIAL'] != '']
    df_trans['CANTIDAD_TRANS'] = df_trans[cant_col_t].apply(extraer_entero)
    df_trans['TIENDA'] = df_trans[tienda_col].astype(str)
    if fecha_col_t:
        df_trans['FECHA'] = pd.to_datetime(df_trans[fecha_col_t], errors='coerce').dt.date
    else:
        df_trans['FECHA'] = pd.Timestamp.today().date()

    df_cruce = df_trans.merge(grupo_det, on='SECUENCIAL', how='left')
    import numpy as np
    df_cruce['CANTIDAD_TOTAL_DETALLE'] = df_cruce['CANTIDAD_TOTAL_DETALLE'].replace(0, np.nan).fillna(df_cruce['CANTIDAD_TRANS'])
    # Si prendas es 0 pero hay fundas, no sobreescribir prendas con la cantidad de la transferencia.
    df_cruce['FUNDAS'] = df_cruce['FUNDAS'].fillna(0).astype(int)
    mask_reemplazo = (df_cruce['PRENDAS'] == 0) & (df_cruce['FUNDAS'] == 0)
    df_cruce.loc[mask_reemplazo, 'PRENDAS'] = df_cruce.loc[mask_reemplazo, 'CANTIDAD_TRANS']
    df_cruce['PRENDAS'] = df_cruce['PRENDAS'].fillna(df_cruce['CANTIDAD_TRANS']).astype(int)
    df_cruce['COSTO_TOTAL'] = df_cruce['COSTO_TOTAL'].fillna(0)
    df_cruce['CATEGORIA_DET'] = df_cruce['CATEGORIA_DET'].fillna('')
    df_cruce['GRUPO'] = df_cruce['GRUPO'].fillna('')
    df_cruce['CATEGORIA_FINAL'] = df_cruce.apply(
        lambda r: clasificar_categoria(r['TIENDA'], r['CATEGORIA_DET'], r['GRUPO']), axis=1
    )
    
    if 'TIENDA' in df_det.columns:
        df_det.drop(columns='TIENDA', inplace=True)
    df_det = df_det.merge(df_cruce[['SECUENCIAL', 'CATEGORIA_FINAL', 'TIENDA']], on='SECUENCIAL', how='left')
    
    return df_cruce, df_det
