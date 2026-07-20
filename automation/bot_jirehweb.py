#!/usr/bin/env python3
import argparse
import io
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR      = Path(__file__).parent
LOGS_DIR      = BASE_DIR / "logs"
OUTPUT_JSON   = BASE_DIR / "transferencias_listas.json"
JIREHWEB_URL  = "https://fashion.sisconti.com/"
JIREHWEB_USER = "wperez"
JIREHWEB_PASS = "Wilo3161*"
TIMEOUT_MS    = 15000

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def screenshot(page, name):
    path = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(path))
    except: pass

def run(headless=True, dry_run=False, limit=None, fecha_inicio=None, fecha_fin=None):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    transferencias = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless, slow_mo=500 if not headless else 0, args=["--start-maximized"])
        ctx = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())

        # ── LOGIN ─────────────────────────────────────────────────────────────
        log(f"Abriendo {JIREHWEB_URL}")
        page.goto(JIREHWEB_URL, wait_until="networkidle", timeout=30000)
        
        if page.locator("input[name='user'], input[id='user'], input[name='usuario']").count() > 0:
            log("Haciendo login...")
            page.get_by_role("textbox", name="Usuario / Identificacion").fill(JIREHWEB_USER)
            page.get_by_role("textbox", name="Contraseña").fill(JIREHWEB_PASS)
            page.get_by_role("button", name=" Ingresar").click()
            page.wait_for_timeout(4000)
        
        # ── NAVEGACIÓN MENÚ ───────────────────────────────────────────────────
        log("Navegando menú...")
        try:
            menu_frame = page.locator("iframe[name='desktop']").content_frame
            menu_frame.get_by_role("link", name=" Gestion Materiales ").click(timeout=8000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Reportes ").click(timeout=8000)
            page.wait_for_timeout(500)
            menu_frame.get_by_role("link", name=" Reporte Transf. Matriz").click(timeout=8000)
            page.wait_for_timeout(2000)
        except Exception as e:
            log(f"Error en el menú: {e}", "ERROR")
            screenshot(page, "error_menu")
            browser.close()
            return []

        # ── FORMULARIO REPORTE ────────────────────────────────────────────────
        log("Llenando formulario...")
        try:
            content_frame = menu_frame.locator("iframe[name='divContenedorPrincipal']").content_frame
            # Esperar a que el frame interior cargue bien (importante si es lento)
            page.wait_for_timeout(3000)
            
            # Primero las fechas
            if fecha_inicio:
                content_frame.locator("#fecha_ini").click(timeout=15000)
                content_frame.locator("#fecha_ini").fill("")
                content_frame.locator("#fecha_ini").fill(fecha_inicio)
                page.keyboard.press("Escape")  # Cerrar cualquier calendario que se abra
                page.wait_for_timeout(500)
                log(f"Fecha Inicio colocada: {fecha_inicio}")
                
            if fecha_fin:
                content_frame.locator("#fecha_fin").click(timeout=15000)
                content_frame.locator("#fecha_fin").fill("")
                content_frame.locator("#fecha_fin").fill(fecha_fin)
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
                log(f"Fecha Final colocada: {fecha_fin}")
                
            # Luego Sucursal = MATRIZ (value="1")
            content_frame.locator("#sucursal").select_option("1", timeout=15000)
            page.wait_for_timeout(500)
            log("Sucursal MATRIZ seleccionada")
            
            # Y finalmente Consultar
            content_frame.get_by_text("Consultar").click(timeout=8000)
            log("Botón Consultar presionado. Esperando resultados...")
            page.wait_for_timeout(4000)
        except Exception as e:
            log(f"Error en el formulario: {e}", "ERROR")
            screenshot(page, "error_formulario")
            browser.close()
            return []

        # ── EXTRACCIÓN TABLA ──────────────────────────────────────────────────
        try:
            # Buscar específicamente la tabla de resultados
            tabla_resultados = content_frame.locator("table:has-text('Bodega Destino')")
            tabla_resultados.locator("tbody tr").first.wait_for(timeout=TIMEOUT_MS)
        except PWTimeout:
            log("No cargó la tabla (timeout).", "ERROR")
            screenshot(page, "error_tabla")
            browser.close()
            return []

        # Recorrer filas de la tabla correcta
        rows = tabla_resultados.locator("tbody tr")
        count = rows.count()
        log(f"Filas encontradas en tabla de resultados: {count}")
        
        filas_procesadas = 0
        for idx in range(count):
            row = rows.nth(idx)
            # Ignorar la fila si es el encabezado que contiene "N.-"
            if "N.-" in row.inner_text():
                continue

            try:
                tds = row.locator("td")
                if tds.count() < 10:
                    continue
                
                # Check if first column is numeric
                n_val = tds.nth(0).inner_text().strip()
                if not n_val.isdigit():
                    continue
                
                # Bodega Destino es la columna 6 (índice 5)
                bodega_destino = tds.nth(5).inner_text().strip()
                if not bodega_destino or "TOTAL" in bodega_destino.upper():
                    continue
                    
                # Extraer enlace del botón imprimir
                # Clickeamos EXACTAMENTE la imagen de imprimir de ESTA fila
                try:
                    with ctx.expect_page(timeout=10000) as popup_info:
                        row.get_by_role("img", name="Imprimir").first.click(timeout=2000)
                except Exception as click_e:
                    # Timeout en click, fila inválida o sin botón
                    continue
                
                popup = popup_info.value
                popup.wait_for_load_state("networkidle", timeout=12000)
                url_popup = popup.url
                popup.close()

                if url_popup and url_popup != "about:blank":
                    transferencias.append({
                        "idx": idx + 1,
                        "url_transferencia": url_popup,
                        "bodega_destino": bodega_destino,
                        "texto_fila": row.inner_text()
                    })
                    log(f"  OK: {bodega_destino} -> {url_popup[:60]}...")
                    filas_procesadas += 1
                    
                    if dry_run and filas_procesadas >= 1:
                        break
                    if limit and filas_procesadas >= limit:
                        break
            except Exception as e:
                bodega_ref = bodega_destino if 'bodega_destino' in locals() else '(desconocida)'
                log(f"  Error fila {idx+1} ({bodega_ref}): {e}", "WARN")

        browser.close()

    OUTPUT_JSON.write_text(json.dumps(transferencias, ensure_ascii=False, indent=2), encoding="utf-8")
    log("=" * 50)
    log(f"LISTO: {len(transferencias)} transferencias guardadas.")
    return transferencias

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--fecha-inicio", type=str, default=None)
    parser.add_argument("--fecha-fin", type=str, default=None)
    args = parser.parse_args()
    run(headless=not args.headful, dry_run=args.dry_run, limit=args.limit, fecha_inicio=args.fecha_inicio, fecha_fin=args.fecha_fin)
