"""
services/jireh_extractor.py
═══════════════════════════════════════════════════════════════════════════════
Extractor Oficial con Playwright para JirehWEB ERP (Sisconti Fashion).
- Automatiza el login en https://fashion.sisconti.com/
- Consulta 'Reporte Transf. Matriz' por rango de fechas (Día actual o Histórico).
- Extrae la tabla real de transferencias y la entrega como DataFrame de Pandas.
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import io
import re
import json
import logging
from datetime import datetime, date
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

JIREHWEB_URL = os.getenv("JIREHWEB_URL", "https://fashion.sisconti.com/")
JIREHWEB_USER = os.getenv("JIREHWEB_USER", "wperez")
JIREHWEB_PASS = os.getenv("JIREHWEB_PASS", "Wilo3161*")


def extraer_transferencias_jireh(
    fecha_inicio: str = None,
    fecha_fin: str = None,
    headless: bool = True,
    usuario: str = None,
    password: str = None
) -> tuple[pd.DataFrame, str]:
    """
    Ejecuta Playwright para extraer la tabla real de transferencias desde JirehWEB.
    Retorna (DataFrame con las transferencias reales, mensaje de estado).
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return pd.DataFrame(), "Playwright no está instalado en el entorno."

    user = usuario or JIREHWEB_USER
    pwd = password or JIREHWEB_PASS
    hoy_str = date.today().strftime("%Y-%m-%d")
    f_ini = fecha_inicio or hoy_str
    f_fin = fecha_fin or hoy_str

    registros = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless, args=["--start-maximized"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
            page = ctx.new_page()
            page.on("dialog", lambda d: d.accept())

            # 1. Login en JirehWEB
            page.goto(JIREHWEB_URL, wait_until="networkidle", timeout=35000)
            if page.locator("input[name='user'], input[id='user'], input[name='usuario']").count() > 0:
                page.get_by_role("textbox", name="Usuario / Identificacion").fill(user)
                page.get_by_role("textbox", name="Contraseña").fill(pwd)
                page.get_by_role("button", name=" Ingresar").click()
                page.wait_for_timeout(4000)

            # 2. Navegación en el menú
            menu_frame = page.locator("iframe[name='desktop']").content_frame
            menu_frame.get_by_role("link", name=" Gestion Materiales ").click(timeout=10000)
            page.wait_for_timeout(600)
            menu_frame.get_by_role("link", name=" Reportes ").click(timeout=10000)
            page.wait_for_timeout(600)
            menu_frame.get_by_role("link", name=" Reporte Transf. Matriz").click(timeout=10000)
            page.wait_for_timeout(2500)

            # 3. Llenar Formulario de Consulta
            content_frame = menu_frame.locator("iframe[name='divContenedorPrincipal']").content_frame
            page.wait_for_timeout(2000)

            content_frame.locator("#fecha_ini").click(timeout=15000)
            content_frame.locator("#fecha_ini").fill("")
            content_frame.locator("#fecha_ini").fill(f_ini)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            content_frame.locator("#fecha_fin").click(timeout=15000)
            content_frame.locator("#fecha_fin").fill("")
            content_frame.locator("#fecha_fin").fill(f_fin)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            content_frame.locator("#sucursal").select_option("1", timeout=15000)
            page.wait_for_timeout(500)

            content_frame.get_by_text("Consultar").click(timeout=10000)
            page.wait_for_timeout(4000)

            # 4. Extraer Tabla de Resultados
            tabla = content_frame.locator("table:has-text('Bodega Destino')")
            tabla.locator("tbody tr").first.wait_for(timeout=20000)

            rows = tabla.locator("tbody tr")
            count = rows.count()

            for idx in range(count):
                row = rows.nth(idx)
                row_text = row.inner_text().strip()
                if "N.-" in row_text or "TOTAL" in row_text.upper():
                    continue

                tds = row.locator("td")
                td_count = tds.count()
                if td_count >= 7:
                    n_val = tds.nth(0).inner_text().strip()
                    if not n_val.isdigit():
                        continue

                    # Extraer columnas exactas según la grilla de Sisconti Fashion
                    fecha_row = tds.nth(1).inner_text().strip().replace('/', '')
                    sucursal_orig = tds.nth(2).inner_text().strip()
                    sucursal_dest = tds.nth(3).inner_text().strip()
                    sec_transf = tds.nth(4).inner_text().strip()
                    bodega_destino = tds.nth(5).inner_text().strip() or sucursal_dest
                    cantidad_txt = tds.nth(6).inner_text().strip()
                    costo_txt = tds.nth(7).inner_text().strip() if td_count > 7 else "0"
                    estado_row = tds.nth(8).inner_text().strip() if td_count > 8 else "Pendiente"

                    # Parseo numérico preciso de flotante (ej. '145.000000' -> 145)
                    try:
                        cant_num = int(round(float(cantidad_txt.replace(',', ''))))
                    except Exception:
                        cant_num = 0

                    try:
                        costo_num = float(costo_txt.replace(',', ''))
                    except Exception:
                        costo_num = 0.0

                    # Discriminación de Fundas / Insumos vs Prendas
                    # 1. Bultos de bolsas plásticas (300 unidades por $7.78)
                    # 2. Insumos/fundas de tienda (9 o 10 unidades por $54 - $60)
                    es_funda = False
                    if cant_num == 300 and costo_num < 15.0:
                        es_funda = True
                    elif cant_num in (9, 10) and 50.0 <= costo_num <= 65.0:
                        es_funda = True

                    prendas_val = 0 if es_funda else cant_num
                    fundas_val = cant_num if es_funda else 0

                    registros.append({
                        "SECUENCIAL": sec_transf,
                        "FECHA": fecha_row or f_ini,
                        "ORIGEN": sucursal_orig,
                        "DESTINO": sucursal_dest,
                        "TIENDA": bodega_destino,
                        "PRENDAS": prendas_val,
                        "FUNDAS": fundas_val,
                        "CANTIDAD": cant_num,
                        "COSTO": costo_num,
                        "ESTADO": estado_row,
                        "TRANSFERIDOR": "Bodega Central",
                        "FUENTE": "SISCONTI_JIREHWEB"
                    })

            browser.close()

        if not registros:
            return pd.DataFrame(), f"No se encontraron transferencias para el rango {f_ini} al {f_fin}."

        df_res = pd.DataFrame(registros)
        return df_res, f"Extracción completada con éxito: {len(df_res)} transferencias extraídas de JirehWEB Sisconti."

    except Exception as e:
        logger.error(f"Error en extracción JirehWEB: {e}")
        return pd.DataFrame(), f"Error al extraer desde JirehWEB: {str(e)}"
