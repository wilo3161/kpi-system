#!/usr/bin/env python3
"""
bot_jirehweb.py
===============
Fase 1 del bot de automatización: Extrae las transferencias pendientes
desde JirehWEB (fashion.siconti.com) y las guarda en un JSON para
que bot_erp.py las procese.

Uso:
    python automation/bot_jirehweb.py               # headless
    python automation/bot_jirehweb.py --headful     # con navegador visible
    python automation/bot_jirehweb.py --headful --dry-run  # solo 1 transferencia (prueba)
    python automation/bot_jirehweb.py --headful --limit 3  # primeras 3
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv opcional

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
LOGS_DIR      = BASE_DIR / "logs"
OUTPUT_JSON   = BASE_DIR / "transferencias_listas.json"

JIREHWEB_URL  = os.getenv("JIREHWEB_URL", "https://fashion.siconti.com/")
JIREHWEB_USER = os.getenv("JIREHWEB_USER", "wperez")
JIREHWEB_PASS = os.getenv("JIREHWEB_PASS", "Wilo3161*")
TIMEOUT_MS    = int(os.getenv("BOT_TIMEOUT_MS", "15000"))

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Regex de validación de URL de transferencia
URL_REGEX = re.compile(r"https?://[^\s]+(?:codigo|sesionid|idemp|vista_previa)[^\s]*", re.IGNORECASE)

# ─── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)


def screenshot(page, name: str):
    path = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(path))
        log(f"Screenshot guardado: {path}", "DEBUG")
    except Exception as e:
        log(f"No se pudo guardar screenshot: {e}", "WARN")


# ─── Lógica principal ─────────────────────────────────────────────────────────
def run(headless: bool = True, dry_run: bool = False, limit: int = None):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    transferencias = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            accept_downloads=True,
        )
        page = ctx.new_page()

        # ── Interceptar diálogos nativos (sesión duplicada) ───────────────────
        page.on("dialog", lambda d: (log(f"Popup detectado: {d.message} → Aceptando", "INFO"), d.accept()))

        # ── LOGIN ─────────────────────────────────────────────────────────────
        log(f"Navegando a {JIREHWEB_URL}")
        page.goto(JIREHWEB_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        # Detectar si ya hay formulario de login o si redirigió al dashboard
        if page.locator("input[name='usuario'], input[type='text']").count() > 0:
            log("Formulario de login detectado")
            try:
                page.fill("input[name='usuario']", JIREHWEB_USER, timeout=5000)
            except Exception:
                page.locator("input[type='text']").first.fill(JIREHWEB_USER)
            try:
                page.fill("input[name='clave']", JIREHWEB_PASS, timeout=5000)
            except Exception:
                page.locator("input[type='password']").first.fill(JIREHWEB_PASS)

            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            # Popup de sesión duplicada puede aparecer aquí (manejado por el listener)
            page.wait_for_timeout(1500)
        else:
            log("Ya hay sesión activa en JirehWEB")

        screenshot(page, "jirehweb_post_login")
        log("Login JirehWEB OK")

        # ── NAVEGACIÓN: Gestión Materiales → Reportes → Reporte Transf. Matriz ─
        log("Navegando a Gestión Materiales > Reportes > Reporte Transf. Matriz")

        # Intentar click en menú. Los selectores pueden variar; probamos varios.
        try:
            page.get_by_text("Gestión Materiales", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            log("Menú 'Gestión Materiales' no encontrado, buscando alternativas...", "WARN")
            # Intentar navegar directamente si hay URL conocida de la sección
            pass

        try:
            page.get_by_text("Reportes", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            log("Sub-menú 'Reportes' no encontrado", "WARN")

        try:
            page.get_by_text("Reporte Transf. Matriz", exact=False).first.click(timeout=5000)
            page.wait_for_timeout(1000)
        except Exception:
            log("'Reporte Transf. Matriz' no encontrado. Intentando URL directa...", "WARN")
            screenshot(page, "jirehweb_menu_error")

        screenshot(page, "jirehweb_reporte_form")

        # ── FILTRO: Sucursal Origen = MATRIZ ──────────────────────────────────
        log("Configurando filtro Sucursal Origen: MATRIZ")
        try:
            # Buscar select de sucursal/origen
            sel = page.locator("select").filter(has_text="MATRIZ")
            if sel.count() == 0:
                # Intentar por label
                page.select_option("select[name*='sucursal'], select[name*='origen'], select", label="MATRIZ", timeout=5000)
            else:
                sel.first.select_option(label="MATRIZ")
        except Exception as e:
            log(f"No se pudo seleccionar MATRIZ: {e}. Continuando...", "WARN")

        # Click en Consultar
        log("Ejecutando Consultar...")
        try:
            page.get_by_role("button", name=re.compile(r"consultar|buscar|search", re.IGNORECASE)).first.click(timeout=5000)
        except Exception:
            try:
                page.get_by_text(re.compile(r"Consultar|Buscar", re.IGNORECASE)).first.click(timeout=5000)
            except Exception as e:
                log(f"No se pudo hacer click en Consultar: {e}", "WARN")

        # Esperar tabla de resultados (hasta 15s, con retry si expira)
        tabla_cargada = False
        for intento in range(2):
            try:
                page.wait_for_selector("table tr, .tabla-resultado, .resultado", timeout=TIMEOUT_MS)
                tabla_cargada = True
                log("Tabla de transferencias cargada")
                break
            except PWTimeout:
                log(f"Timeout esperando tabla (intento {intento+1}/2). Recargando...", "WARN")
                page.reload(wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(2000)

        if not tabla_cargada:
            log("No se pudo cargar la tabla de transferencias.", "ERROR")
            screenshot(page, "jirehweb_tabla_timeout")
            browser.close()
            return []

        screenshot(page, "jirehweb_tabla_ok")

        # ── EXTRACCIÓN DE TRANSFERENCIAS ──────────────────────────────────────
        # Buscar filas de la tabla con enlaces clicables
        filas = page.locator("table tbody tr").all()
        log(f"Se encontraron {len(filas)} filas en la tabla")

        if limit:
            filas = filas[:limit]
        if dry_run:
            filas = filas[:1]
            log("Modo dry-run: procesando solo 1 fila")

        for idx, fila in enumerate(filas):
            log(f"Procesando fila {idx+1}/{len(filas)}...")

            try:
                # Leer texto de la fila para obtener Bodega Destino
                texto_fila = fila.inner_text()
                log(f"  Texto fila: {texto_fila[:120]}")

                # Detectar bodega destino en el texto
                bodega_destino = _extraer_bodega(texto_fila)
                log(f"  Bodega Destino: {bodega_destino or '(no detectada)'}")

                # Click en el enlace/botón de detalle
                enlace = fila.locator("a, button").first
                with ctx.expect_page(timeout=8000) as popup_info:
                    enlace.click()
                popup = popup_info.value
                popup.wait_for_load_state("networkidle", timeout=12000)

                url_popup = popup.url
                log(f"  URL popup: {url_popup}")

                # Validar que la URL tenga parámetros esperados
                if not _es_url_valida(url_popup):
                    log(f"  URL inválida o sin parámetros clave → Saltando", "WARN")
                    screenshot(popup, f"popup_url_invalida_{idx}")
                    popup.close()
                    continue

                # También intentar extraer URL desde el contenido del popup
                # (en caso de que el popup muestre un iframe o document con la URL real)
                url_final = url_popup
                try:
                    # Buscar si hay un iframe con la URL real
                    iframe_src = popup.locator("iframe").first.get_attribute("src", timeout=3000)
                    if iframe_src and _es_url_valida(iframe_src):
                        url_final = iframe_src
                        log(f"  URL en iframe: {url_final}")
                except Exception:
                    pass

                popup.close()

                entrada = {
                    "idx": idx + 1,
                    "url_transferencia": url_final,
                    "bodega_destino": bodega_destino or "",
                    "texto_fila": texto_fila[:300],
                    "timestamp": datetime.now().isoformat(),
                }
                transferencias.append(entrada)
                log(f"  ✅ Transferencia {idx+1} extraída: {url_final[:60]}...")

            except PWTimeout:
                log(f"  Timeout en fila {idx+1} → Saltando", "WARN")
                screenshot(page, f"jirehweb_fila_timeout_{idx}")
            except Exception as e:
                log(f"  Error en fila {idx+1}: {e} → Saltando", "WARN")
                screenshot(page, f"jirehweb_fila_error_{idx}")

        browser.close()

    # ── Guardar JSON ──────────────────────────────────────────────────────────
    OUTPUT_JSON.write_text(json.dumps(transferencias, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"\n{'='*60}")
    log(f"EXTRACCIÓN COMPLETA: {len(transferencias)} transferencias guardadas en {OUTPUT_JSON}")
    log(f"{'='*60}")

    return transferencias


def _extraer_bodega(texto: str) -> str:
    """Extrae el nombre de la bodega destino del texto de la fila."""
    patrones = [
        r"AERO\s+[\w\s]+(?:CC|DAULE|LAGO\s*AGRO|SCALA|MALLDELRIO|QUICENTRO|PORTOVIEJO|MANTA|MACHALA|IBARRA|PATIO)",
        r"AEROPOSTALE\s*[-–]\s*[\w\s]+",
    ]
    for pat in patrones:
        m = re.search(pat, texto.upper())
        if m:
            return m.group(0).strip()
    # Fallback: extraer palabra AERO... si existe
    m = re.search(r"AERO\s*\w+", texto.upper())
    return m.group(0).strip() if m else ""


def _es_url_valida(url: str) -> bool:
    """Verifica que la URL tenga parámetros mínimos de una transferencia."""
    if not url or url == "about:blank":
        return False
    # Debe ser http/https y tener al menos un parámetro relevante
    claves = ["codigo", "sesionid", "idemp", "vista_previa", "transferencia", "reporte"]
    url_lower = url.lower()
    return url_lower.startswith("http") and any(c in url_lower for c in claves)


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot extracción JirehWEB")
    parser.add_argument("--headful", action="store_true", help="Mostrar navegador")
    parser.add_argument("--dry-run", action="store_true", help="Solo procesar 1 fila (prueba)")
    parser.add_argument("--limit", type=int, default=None, help="Limitar número de filas")
    args = parser.parse_args()

    resultado = run(
        headless=not args.headful,
        dry_run=args.dry_run,
        limit=args.limit,
    )
    # Output JSON para que Streamlit lo lea si se llama como subprocess
    print(json.dumps({"ok": True, "total": len(resultado)}, ensure_ascii=False))
    sys.exit(0)
