import pandas as pd
import re
import unicodedata
from typing import Optional, Tuple

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
    s = str(valor) if not pd.isna(valor) else ""
    return re.sub(r'\D', '', s)

def extraer_entero(val):
    if pd.isna(val): return 0
    s = str(val).replace(',', '')
    match = re.search(r'\d+', s)
    return int(match.group()) if match else 0

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
                # CORREGIDO: validar que i > 0 antes de acceder a tokens[i-1]
                if i > 0:
                    color_raw = tokens[i - 1]
                    producto_base = tokens[:i - 1]
                else:
                    color_raw = ''
                    producto_base = tokens[:i]
                producto = ' '.join(producto_base)
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
        ('SKIRT', 'Falda', 'SKIRT'), ('FUNDA', 'Funda', 'FUNDA'),
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

def clasificar_categoria(bodega_destino, categoria_detalle, grupo):
    cat_det = str(categoria_detalle).upper() if not pd.isna(categoria_detalle) else ""
    if 'FUNDA' in cat_det: return 'Fundas'
    if 'ACCESORIOS PRICE CLUB' in cat_det: return 'Price Club'
    bodega_norm = normalizar_para_mapeo(bodega_destino)
    if bodega_norm in _MAPEO_DIRECTO_NORM: return _MAPEO_DIRECTO_NORM[bodega_norm]
    if any(p in bodega_norm for p in ['PRICE', 'OIL']): return 'Price Club'
    if any(p in bodega_norm for p in ['VENTAS POR MAYOR', 'MAYORISTA']): return 'Ventas por Mayor'
    if any(p in bodega_norm for p in ['TIENDA WEB', 'MOVIL', 'WEB']): return 'Tienda Web'
    if 'FALLAS' in bodega_norm: return 'Fallas'
    return 'Tiendas'

def _safe_numeric_conversion(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def procesar_archivos(df_transferencias, df_detalle):
    # --- Detalle ---
    det_cols = {normalizar_para_mapeo(c): c for c in df_detalle.columns}
    sec_col = next((det_cols[k] for k in det_cols if 'SECUENCIAL' in k), None)
    cant_col = next((det_cols[k] for k in det_cols if 'CANTIDAD' in k), None)
    prod_col = next((det_cols[k] for k in det_cols if 'PRODUCTO' in k), None)
    cat_col = next((det_cols[k] for k in det_cols if 'CATEGORIA' in k), None)
    grupo_col = next((det_cols[k] for k in det_cols if 'GRUPO' in k), None)
    costo_col = next((det_cols[k] for k in det_cols if 'COSTO' in k), None)
    bodega_recibe_col = next((det_cols[k] for k in det_cols if 'BODEGA RECIBE' in k or 'BODEGA' in k), None)
    
    if not all([sec_col, cant_col, prod_col]):
        raise ValueError("El archivo de detalle debe tener al menos: Secuencial, Cantidad, Producto.")

    df_det = df_detalle.copy()
    df_det['SECUENCIAL'] = df_det[sec_col].apply(_extraer_digitos).astype(str)
    df_det = df_det[df_det['SECUENCIAL'] != '']
    df_det['CANTIDAD'] = _safe_numeric_conversion(df_det[cant_col])
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
        
    df_det['ES_FUNDA'] = df_det['CATEGORIA'].str.upper().str.contains('FUNDA', na=False)

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
    sec_col_t = next((trans_cols[k] for k in trans_cols if 'SECUENCIAL' in k), None)
    cant_col_t = next((trans_cols[k] for k in trans_cols if 'CANTIDAD' in k), None)
    tienda_col = next((trans_cols[k] for k in trans_cols if 'BODEGA DESTINO' in k or 'SUCURSAL DESTINO' in k), None)
    fecha_col_t = next((trans_cols[k] for k in trans_cols if 'FECHA' in k), None)

    if not all([sec_col_t, cant_col_t, tienda_col]):
        raise ValueError("El archivo de transferencias debe tener: Secuencial, Cantidad, Bodega/Sucursal Destino.")

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
    df_cruce['CANTIDAD_TOTAL_DETALLE'] = df_cruce['CANTIDAD_TOTAL_DETALLE'].fillna(df_cruce['CANTIDAD_TRANS'])
    df_cruce['PRENDAS'] = df_cruce['PRENDAS'].fillna(df_cruce['CANTIDAD_TRANS']).astype(int) 
    df_cruce['FUNDAS'] = df_cruce['FUNDAS'].fillna(0).astype(int)
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
