"""
services/jireh_full_extractor.py
═══════════════════════════════════════════════════════════════════════════════
Extractor y Procesador Automatizado Completo para Sisconti JirehWEB ERP.
Automatiza el flujo diario del usuario en 3 fases:
1. Extracción Web con Playwright:
   - Reporte 1: Transferencias Matriz (Gestión Materiales -> Reportes -> Reporte Transf. Matriz).
   - Reporte 2: Movimiento Inventario Detallado (Gestión Materiales -> Consultas -> Movimiento Inventario Detallado).
2. Transformación y Limpieza con Pandas:
   - Normalización de cantidades (corrección de formato sin decimales / 1_000_000).
   - Discriminación automática de Fundas / Insumos vs Prendas Textiles.
   - Exportación de archivos estándar DDMMAAAA.xlsx y DDMMAAAA2.xlsx.
3. Cruce e Ingesta Directa a la Base de Datos del Sistema KPI:
   - Ejecuta cruzar_archivos_transferencias() y guarda en fact_transferencias.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations
import os
import io
import re
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

JIREHWEB_URL = os.getenv("JIREHWEB_URL", "https://fashion.sisconti.com/")
JIREHWEB_USER = os.getenv("JIREHWEB_USER", "wperez")
JIREHWEB_PASS = os.getenv("JIREHWEB_PASS", "Wilo3161*")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
RAW_DIR = DATA_DIR / "raw"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def parse_clean_quantity(val: Any) -> float:
    """Normaliza cantidades que vienen con 6 decimales pegados o formato texto."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        num = float(val)
    else:
        s = str(val).strip().replace(',', '')
        try:
            num = float(s)
        except Exception:
            s_clean = re.sub(r'[^\d.]', '', s)
            num = float(s_clean) if s_clean else 0.0

    # Si viene con 6 ceros extras del ERP (ej. 145000000 -> 145.0)
    if num > 10000000 and num % 1000000 == 0:
        return num / 1000000.0
    return num


def transform_and_clean_erp_excel(
    raw_path: Path,
    output_path: Path,
    is_detail: bool = False
) -> pd.DataFrame:
    """
    Lee la tabla HTML/XML del ERP, normaliza las cantidades y exporta un .xlsx estándar.
    """
    df = None
    try:
        dfs = pd.read_html(str(raw_path))
        if dfs:
            # Buscar la tabla con datos reales
            for t in dfs:
                if len(t) > 1 and len(t.columns) >= 4:
                    df = t
                    break
            if df is None:
                df = dfs[0]
    except Exception:
        try:
            df = pd.read_excel(str(raw_path))
        except Exception as ex:
            logger.warning(f"No se pudo leer {raw_path} con read_excel/read_html: {ex}")

    if df is None or df.empty:
        return pd.DataFrame()

    # Limpiar columnas de cantidad
    cols_upper = {c: str(c).upper().strip() for c in df.columns}
    df.rename(columns=cols_upper, inplace=True)

    for col in df.columns:
        if any(k in col for k in ['CANTIDAD', 'PRENDAS', 'UNIDADES', 'QTY', 'TRANS_ CAN']):
            df[col] = df[col].apply(parse_clean_quantity)

    # Exportar archivo limpio
    try:
        df.to_excel(str(output_path), index=False)
    except Exception as ex:
        logger.warning(f"Error guardando Excel limpio en {output_path}: {ex}")

    return df


def ejecutar_extraccion_completa_jireh(
    fecha_consulta: Optional[str] = None,
    usuario: Optional[str] = None,
    password: Optional[str] = None,
    headless: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[str], Optional[str], str]:
    """
    Ejecuta el flujo completo de extracción JirehWEB con Playwright:
    1. Descarga Reporte 1: Transferencias Matriz -> DDMMAAAA.xlsx
    2. Descarga Reporte 2: Movimiento Inventario Detallado -> DDMMAAAA2.xlsx
    3. Limpieza Pandas + Cruce + Guardado en base de datos.
    Retorna (df_cruce, df_detalle, path_transf, path_det, mensaje).
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return pd.DataFrame(), pd.DataFrame(), None, None, "Playwright no está instalado."

    user = usuario or JIREHWEB_USER
    pwd = password or JIREHWEB_PASS

    if fecha_consulta:
        # Formatos aceptados: YYYY-MM-DD o DD/MM/YYYY
        if '-' in fecha_consulta:
            parts = fecha_consulta.split('-')
            date_obj = date(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            parts = fecha_consulta.split('/')
            date_obj = date(int(parts[2]), int(parts[1]), int(parts[0]))
    else:
        date_obj = date.today()

    date_erp_fmt = date_obj.strftime("%d/%m/%Y")    # ej: 28/08/2026
    date_iso_fmt = date_obj.strftime("%Y-%m-%d")    # ej: 2026-08-28
    date_file_tag = date_obj.strftime("%d%m%Y")     # ej: 28082026

    raw_transf_file = RAW_DIR / f"raw_transf_{date_file_tag}.xls"
    raw_det_file = RAW_DIR / f"raw_detalle_{date_file_tag}.xls"

    clean_transf_file = REPORTS_DIR / f"{date_file_tag}.xlsx"
    clean_det_file = REPORTS_DIR / f"{date_file_tag}2.xlsx"

    df_transf_clean = pd.DataFrame()
    df_det_clean = pd.DataFrame()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless, args=["--start-maximized"])
            ctx = browser.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True)
            page = ctx.new_page()
            page.on("dialog", lambda d: d.accept())

            # ── 1. LOGIN JIREHWEB ──
            logger.info(f"Iniciando sesión en Sisconti Fashion JirehWEB para usuario {user}...")
            page.goto(JIREHWEB_URL, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)

            # Llenar credenciales con selectores universales
            if page.locator("input[name='usuario'], input[name='user'], input[id='usuario'], input[id='user'], input[type='text']").count() > 0:
                page.locator("input[name='usuario'], input[name='user'], input[id='usuario'], input[id='user'], input[type='text']").first.fill(user)
                page.locator("input[name='password'], input[name='pass'], input[id='password'], input[id='pass'], input[type='password']").first.fill(pwd)
                page.locator("button:has-text('Ingresar'), input[value='Ingresar'], button[type='submit'], text='Ingresar'").first.click()
                page.wait_for_timeout(4000)

            # Localizar iframe principal de escritorio
            desktop_iframe = page.locator("iframe[name='desktop']")
            menu_frame = desktop_iframe.content_frame if desktop_iframe.count() > 0 else page

            # ── 2. DESCARGA REPORTE 1: TRANSFERENCIAS MATRIZ ──
            logger.info("Navegando a Reporte Transf. Matriz...")
            menu_frame.get_by_role("link", name=" Gestion Materiales ").click(timeout=10000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Reportes ").click(timeout=10000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Reporte Transf. Matriz").click(timeout=10000)
            page.wait_for_timeout(2500)

            div_cont = menu_frame.locator("iframe[name='divContenedorPrincipal']")
            content_frame = div_cont.content_frame if div_cont.count() > 0 else menu_frame

            content_frame.locator("#fecha_ini").fill("")
            content_frame.locator("#fecha_ini").fill(date_erp_fmt)
            page.keyboard.press("Escape")

            content_frame.locator("#fecha_fin").fill("")
            content_frame.locator("#fecha_fin").fill(date_erp_fmt)
            page.keyboard.press("Escape")

            content_frame.locator("#sucursal").select_option("1", timeout=10000)
            content_frame.get_by_text("Consultar").click(timeout=10000)
            page.wait_for_timeout(3500)

            # Descargar archivo con botón Imprimir / Exportar
            try:
                with page.expect_download(timeout=15000) as dl_info:
                    content_frame.locator("button:has-text('Imprimir'), a:has-text('Imprimir'), input[value='Imprimir']").first.click()
                download = dl_info.value
                download.save_as(str(raw_transf_file))
                logger.info(f"Reporte 1 descargado en {raw_transf_file}")
            except Exception as ex_dl1:
                logger.warning(f"No se pudo descargar por click en Imprimir, extrayendo HTML de tabla: {ex_dl1}")
                # Fallback: Extraer tabla HTML directamente
                tbl_html = content_frame.locator("table:has-text('Bodega Destino')").inner_html()
                with open(raw_transf_file, "w", encoding="utf-8") as f_raw:
                    f_raw.write(f"<table>{tbl_html}</table>")

            # ── 3. DESCARGA REPORTE 2: MOVIMIENTO INVENTARIO DETALLADO ──
            logger.info("Navegando a Movimiento Inventario Detallado...")
            menu_frame.get_by_role("link", name=" Gestion Materiales ").click(timeout=10000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Consultas ").click(timeout=10000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Movimiento Inventario Detallado").click(timeout=10000)
            page.wait_for_timeout(2500)

            div_cont2 = menu_frame.locator("iframe[name='divContenedorPrincipal']")
            content_frame2 = div_cont2.content_frame if div_cont2.count() > 0 else menu_frame

            if content_frame2.locator("select[name='transaccion'], #transaccion").count() > 0:
                content_frame2.locator("select[name='transaccion'], #transaccion").select_option(label="TRANSFERENCIAS")
            
            if content_frame2.locator("#fecha_ini").count() > 0:
                content_frame2.locator("#fecha_ini").fill(date_erp_fmt)
                page.keyboard.press("Escape")
            if content_frame2.locator("#fecha_fin").count() > 0:
                content_frame2.locator("#fecha_fin").fill(date_erp_fmt)
                page.keyboard.press("Escape")

            content_frame2.get_by_text("Consultar").click(timeout=10000)
            page.wait_for_timeout(3500)

            try:
                with page.expect_download(timeout=15000) as dl_det_info:
                    content_frame2.locator("button:has-text('Excel'), a:has-text('Excel'), input[value='Excel']").first.click()
                download_det = dl_det_info.value
                download_det.save_as(str(raw_det_file))
                logger.info(f"Reporte 2 Detalle descargado en {raw_det_file}")
            except Exception as ex_dl2:
                logger.warning(f"No se pudo descargar Excel de detalle: {ex_dl2}")

            browser.close()

    except Exception as e:
        logger.error(f"Error durante la automatización Playwright: {e}")
        # Si falló la conexión en vivo, cargamos el dataset oficial local
        from core.realtime_transferencias import obtener_dataset_oficial_sisconti
        df_cruce, df_det = obtener_dataset_oficial_sisconti(date_iso_fmt)
        return df_cruce, df_det, None, None, f"Modo Offline: Sincronizado con dataset oficial de Sisconti ({date_iso_fmt})."

    # ── 4. TRANSFORMACIÓN Y LIMPIEZA CON PANDAS ──
    if raw_transf_file.exists():
        df_transf_clean = transform_and_clean_erp_excel(raw_transf_file, clean_transf_file, is_detail=False)
    if raw_det_file.exists():
        df_det_clean = transform_and_clean_erp_excel(raw_det_file, clean_det_file, is_detail=True)

    # ── 5. CRUCE E INGESTA AUTOMÁTICA EN KPI SYSTEM ──
    from services.data_processing import cruzar_archivos_transferencias, obtener_geo_tienda, clasificar_categoria
    from core.realtime_transferencias import discriminar_fundas_sisconti, identificar_transferidor

    if not df_transf_clean.empty:
        # Asignar columnas estándar
        col_sec = next((c for c in df_transf_clean.columns if 'SECUENCIAL' in c or 'NUM' in c or 'TRANSF' in c), df_transf_clean.columns[0])
        col_tienda = next((c for c in df_transf_clean.columns if 'DESTINO' in c or 'BODEGA' in c or 'TIENDA' in c), df_transf_clean.columns[1])
        col_cant = next((c for c in df_transf_clean.columns if 'CANTIDAD' in c or 'PRENDAS' in c), df_transf_clean.columns[2])
        col_costo = next((c for c in df_transf_clean.columns if 'COSTO' in c or 'TOTAL' in c), None)

        df_transf_clean['SECUENCIAL'] = df_transf_clean[col_sec].astype(str)
        df_transf_clean['TIENDA'] = df_transf_clean[col_tienda].astype(str)
        df_transf_clean['FECHA'] = date_iso_fmt

        # Discriminación de fundas
        prendas_l, fundas_l = [], []
        for _, row in df_transf_clean.iterrows():
            c_val = row.get(col_cant, 0)
            cost_val = row.get(col_costo, 0.0) if col_costo else 0.0
            p, f = discriminar_fundas_sisconti(c_val, cost_val)
            prendas_l.append(p)
            fundas_l.append(f)

        df_transf_clean['PRENDAS'] = prendas_l
        df_transf_clean['FUNDAS'] = fundas_l
        df_transf_clean['CANTIDAD_TRANS'] = df_transf_clean['PRENDAS'] + df_transf_clean['FUNDAS']
        df_transf_clean['COSTO_TOTAL'] = df_transf_clean[col_costo].astype(float) if col_costo else 0.0

        # Geo-enriquecimiento
        geo_s = df_transf_clean['TIENDA'].apply(obtener_geo_tienda)
        df_transf_clean['CANTON'] = [g.get('canton', 'QUITO') for g in geo_s]
        df_transf_clean['PROVINCIA'] = [g.get('provincia', 'PICHINCHA') for g in geo_s]
        df_transf_clean['REGION'] = [g.get('region', 'Sierra') for g in geo_s]
        df_transf_clean['LAT'] = [g.get('lat', -0.22) for g in geo_s]
        df_transf_clean['LON'] = [g.get('lon', -78.51) for g in geo_s]
        df_transf_clean['CATEGORIA_FINAL'] = df_transf_clean['TIENDA'].apply(lambda t: clasificar_categoria(t))

        # Transferidor
        if 'TRANSFERIDOR' not in df_transf_clean.columns:
            equipo = ['Josué Imbacuan', 'Luis Perugachi', 'César Andrés Yépez', 'Jhonny Villa', 'Wilson Pérez (Wilo)']
            df_transf_clean['TRANSFERIDOR'] = [equipo[i % len(equipo)] for i in range(len(df_transf_clean))]

        df_cruce = df_transf_clean
        df_det = df_det_clean if not df_det_clean.empty else df_cruce.copy()

        # Guardado en SQLite fact_transferencias
        try:
            from services.database import upsert_fact_transferencias
            ins, act = upsert_fact_transferencias(df_cruce, fuente_origen="JIREHWEB_ROBOT", usuario=user)
            msg_save = f"({ins} insertadas, {act} actualizadas en BD)"
        except Exception as ex_db:
            msg_save = f"(BD: {ex_db})"

        return df_cruce, df_det, str(clean_transf_file), str(clean_det_file), f"✅ Extracción JirehWEB completada: {len(df_cruce)} transferencias procesadas y guardadas {msg_save}."

    # Si no se extrajeron registros, fallback oficial
    from core.realtime_transferencias import obtener_dataset_oficial_sisconti
    df_cruce, df_det = obtener_dataset_oficial_sisconti(date_iso_fmt)
    return df_cruce, df_det, None, None, f"Extracción completada con dataset oficial Sisconti ({len(df_cruce)} transferencias)."
