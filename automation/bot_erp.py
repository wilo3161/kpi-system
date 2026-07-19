#!/usr/bin/env python3
"""
bot_erp.py
==========
Fase 2 del bot: Lee el JSON de transferencias generado por bot_jirehweb.py
y las carga en el ERP local de Aeropostale (Streamlit).

Uso:
    python automation/bot_erp.py                     # procesa todo el JSON
    python automation/bot_erp.py --headful           # con navegador visible
    python automation/bot_erp.py --headful --test-url "https://..."
    python automation/bot_erp.py --headful --limit 2
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
LOGS_DIR     = BASE_DIR / "logs"
INPUT_JSON   = BASE_DIR / "transferencias_listas.json"
MAPEO_FILE   = BASE_DIR / "mapeo_tiendas.json"

ERP_URL      = os.getenv("ERP_URL", "http://localhost:8501")
ERP_USER     = os.getenv("ERP_USER", "admin")
ERP_PASS     = os.getenv("ERP_PASS", "wilo3161")
TIMEOUT_MS   = int(os.getenv("BOT_TIMEOUT_MS", "15000"))

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Cargar mapeo de tiendas estático (opcional, como fallback)
try:
    MAPEO_TIENDAS_ESTATICO: dict = json.loads(MAPEO_FILE.read_text(encoding="utf-8"))
except Exception:
    MAPEO_TIENDAS_ESTATICO = {}

try:
    from fuzzywuzzy import process
except ImportError:
    process = None



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
    return str(path)


# ─── Lógica principal ─────────────────────────────────────────────────────────
def run(headless: bool = True, test_url: str = None, limit: int = None):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    # Preparar lista de transferencias
    if test_url:
        transferencias = [{"url_transferencia": test_url, "bodega_destino": "", "idx": 1}]
        log(f"Modo test-url: {test_url}")
    elif INPUT_JSON.exists():
        transferencias = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
        log(f"Cargadas {len(transferencias)} transferencias desde {INPUT_JSON}")
    else:
        log(f"No se encontró {INPUT_JSON}. Ejecuta bot_jirehweb.py primero.", "ERROR")
        return []

    if limit:
        transferencias = transferencias[:limit]

    resultados = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()

        # Interceptar diálogos
        page.on("dialog", lambda d: (log(f"Dialog ERP: {d.message}", "INFO"), d.accept()))

        # ── LOGIN ERP ─────────────────────────────────────────────────────────
        log(f"Navegando al ERP: {ERP_URL}")
        page.goto(ERP_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # Detectar si hay formulario de login
        if page.locator("input[type='text'], input[placeholder*='user'], input[placeholder*='Usuario']").count() > 0:
            log("Formulario de login ERP detectado")
            # Intentar varias estrategias de llenado
            try:
                page.fill("input[placeholder*='Usuario'], input[placeholder*='user']", ERP_USER, timeout=4000)
            except Exception:
                page.locator("input[type='text']").first.fill(ERP_USER)
            try:
                page.fill("input[type='password']", ERP_PASS, timeout=4000)
            except Exception:
                page.locator("input[type='password']").first.fill(ERP_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
        else:
            log("ERP: sesión ya activa o login no requerido")

        screenshot(page, "erp_post_login")

        # ── NAVEGAR AL MÓDULO GUÍAS ───────────────────────────────────────────
        log("Buscando módulo Guías...")
        try:
            page.get_by_text(re.compile(r"guías|guias|remisión|remision", re.IGNORECASE)).first.click(timeout=8000)
            page.wait_for_timeout(2000)
        except Exception:
            log("No encontré el link de Guías en el sidebar, intentando navegar por URL...", "WARN")
            page.goto(f"{ERP_URL}?page=guias", wait_until="networkidle", timeout=10000)
            page.wait_for_timeout(2000)

        # Clic en pestaña "Nueva Guía" si es necesario
        try:
            page.get_by_text(re.compile(r"nueva guía|nueva guia|new guide", re.IGNORECASE)).first.click(timeout=5000)
            page.wait_for_timeout(1000)
        except Exception:
            pass

        # Clic en sub-pestaña "Individual"
        try:
            page.get_by_text(re.compile(r"^individual$", re.IGNORECASE)).first.click(timeout=5000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        screenshot(page, "erp_modulo_guias")

        # ── OBTENER OPCIONES DE TIENDA DINÁMICAMENTE ────────────────────────
        opciones_tiendas_erp = []
        try:
            # Buscar el dropdown de tienda
            tienda_sel = page.locator("div[data-testid='stSelectbox']").filter(has_text=re.compile(r"tienda|destino", re.IGNORECASE)).first
            
            # Click para abrir las opciones (necesario en Streamlit)
            tienda_sel.click(timeout=5000)
            page.wait_for_timeout(500)
            
            # Extraer las opciones del menú emergente de Streamlit
            options_elements = page.locator("ul[data-testid='stVirtualDropdown'] li, ul[role='listbox'] li").all()
            for opt in options_elements:
                 opciones_tiendas_erp.append(opt.inner_text().strip())
                 
            # Click fuera o presionar Escape para cerrar el menú
            page.keyboard.press("Escape")
            log(f"Opciones de tienda extraídas: {len(opciones_tiendas_erp)}")
        except Exception as e:
            log(f"No se pudieron extraer las opciones de tienda: {e}", "WARN")

        # ── PROCESAR CADA TRANSFERENCIA ───────────────────────────────────────
        for t in transferencias:
            url_trans = t.get("url_transferencia", "")
            bodega    = t.get("bodega_destino", "")
            idx       = t.get("idx", "?")

            log(f"\n{'─'*50}")
            log(f"Procesando transferencia #{idx}: {url_trans[:70]}...")

            resultado = {
                "idx": idx,
                "url": url_trans,
                "bodega": bodega,
                "estado": "pendiente",
                "error": None,
                "guia_generada": None,
                "screenshot_error": None,
            }

            # 1. Mapear bodega → tienda ERP
            tienda_erp = _mapear_tienda(bodega, opciones_tiendas_erp)
            if not tienda_erp and bodega:
                log(f"  Bodega '{bodega}' no mapeada → Saltando", "WARN")
                resultado["estado"] = "saltada"
                resultado["error"] = f"Bodega '{bodega}' no mapeada"
                resultados.append(resultado)
                continue

            # 2. Pegar URL en el campo de transferencia
            url_field = page.locator(
                "input[placeholder*='URL'], input[placeholder*='url'], input[placeholder*='transferencia']"
            ).first
            try:
                url_field.clear(timeout=3000)
                url_field.fill(url_trans, timeout=3000)
                url_field.press("Enter")
            except Exception as e:
                log(f"  No se pudo pegar la URL: {e}", "ERROR")
                resultado["estado"] = "error"
                resultado["error"] = f"No se pudo pegar URL: {e}"
                resultados.append(resultado)
                continue

            # 3. Esperar banner verde de confirmación (con reintento)
            banner_ok = False
            for intento in range(2):
                try:
                    page.wait_for_selector(
                        "div[data-testid='stSuccess'], .element-container .stAlert, [class*='success']",
                        timeout=8000
                    )
                    banner_ok = True
                    log(f"  Banner de éxito detectado (intento {intento+1})")
                    break
                except PWTimeout:
                    if intento == 0:
                        log(f"  Timeout en banner verde (intento 1/2). Reintentando...", "WARN")
                        url_field.clear(timeout=2000)
                        url_field.fill(url_trans, timeout=2000)
                        url_field.press("Enter")
                    else:
                        log(f"  Timeout definitivo en banner verde.", "WARN")

            # 4. Leer total de prendas extraídas
            total_prendas = 0
            try:
                info_text = page.locator("div[data-testid='stInfo'], [class*='info']").all_inner_texts()
                for txt in info_text:
                    m = re.search(r"(\d+[\d,\.]*)\s*(?:prendas|items|artículos)", txt, re.IGNORECASE)
                    if m:
                        total_prendas = int(re.sub(r"[,\.]", "", m.group(1)))
                        break
                log(f"  Total prendas extraídas: {total_prendas}")
            except Exception as e:
                log(f"  No se pudo leer total prendas: {e}", "WARN")

            # 5. Validar coherencia de prendas
            if total_prendas == 0:
                log(f"  ⚠️ Error de consistencia: total_prendas = 0. No se genera guía.", "WARN")
                resultado["estado"] = "error_prendas"
                resultado["error"] = "total_prendas = 0"
                resultados.append(resultado)
                continue

            # 6. Seleccionar tienda destino en el ERP
            if tienda_erp:
                try:
                    tienda_sel = page.locator(
                        "select, div[data-testid='stSelectbox']"
                    ).filter(has_text=re.compile(r"tienda|destino", re.IGNORECASE)).first
                    tienda_sel.select_option(label=tienda_erp, timeout=5000)
                    log(f"  Tienda seleccionada: {tienda_erp}")
                except Exception as e:
                    log(f"  No se pudo seleccionar tienda '{tienda_erp}': {e}", "WARN")
                    # Continuar de todas formas

            # 7. Hacer click en Guardar y Generar PDF
            log("  Guardando guía...")
            try:
                btn_guardar = page.get_by_role("button", name=re.compile(r"guardar|generar pdf|save", re.IGNORECASE)).first
                btn_guardar.click(timeout=5000)
            except Exception as e:
                log(f"  No se encontró botón Guardar: {e}", "ERROR")
                sc = screenshot(page, f"erp_sin_btn_guardar_{idx}")
                resultado["estado"] = "error"
                resultado["error"] = f"Botón Guardar no encontrado: {e}"
                resultado["screenshot_error"] = sc
                resultados.append(resultado)
                continue

            # 8. Validar banner de guía guardada exitosamente
            try:
                page.wait_for_selector(
                    "div[data-testid='stSuccess']:has-text('Guía'), [class*='success']:has-text('guardada')",
                    timeout=10000
                )
                # Extraer número de guía
                success_texts = page.locator("div[data-testid='stSuccess']").all_inner_texts()
                num_guia = None
                for st_text in success_texts:
                    m = re.search(r"Guía\s*#?\s*(\d+)", st_text, re.IGNORECASE)
                    if m:
                        num_guia = m.group(1)
                        break

                log(f"  ✅ Guía #{num_guia} generada correctamente")
                resultado["estado"] = "ok"
                resultado["guia_generada"] = num_guia

            except PWTimeout:
                log(f"  ❌ No se confirmó la guía guardada.", "ERROR")
                sc = screenshot(page, f"erp_guia_no_guardada_{idx}")
                resultado["estado"] = "error"
                resultado["error"] = "Guía no confirmada (timeout en banner éxito)"
                resultado["screenshot_error"] = sc

            resultados.append(resultado)
            page.wait_for_timeout(1000)

        # ── IMPRIMIR SI HAY 4 EN COLA ─────────────────────────────────────────
        guias_ok = [r for r in resultados if r["estado"] == "ok"]
        if len(guias_ok) >= 4:
            log("\nCola de 4 guías completa → Intentando imprimir...")
            try:
                page.get_by_role("button", name=re.compile(r"imprimir.*4|IMPRIMIR.*ETIQUETA", re.IGNORECASE)).first.click(timeout=5000)
                page.wait_for_timeout(2000)
                log("✅ Descarga A4 de 4 etiquetas iniciada")
            except Exception as e:
                log(f"No se pudo hacer clic en imprimir 4: {e}", "WARN")

        browser.close()

    # ── Reporte final ─────────────────────────────────────────────────────────
    ok    = sum(1 for r in resultados if r["estado"] == "ok")
    error = sum(1 for r in resultados if r["estado"] not in ("ok", "saltada"))
    salt  = sum(1 for r in resultados if r["estado"] == "saltada")

    log(f"\n{'='*60}")
    log(f"RESUMEN: ✅ {ok} OK | ❌ {error} errores | ⏭️ {salt} saltadas")
    log(f"{'='*60}")

    # Guardar resultados
    results_path = BASE_DIR / "resultados_bot.json"
    results_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Resultados guardados en {results_path}")

    return resultados


def _mapear_tienda(bodega: str, opciones_erp: list[str]) -> str:
    """Mapea el nombre de bodega de JirehWEB al nombre de tienda del ERP."""
    if not bodega:
        return ""
    bodega_upper = bodega.upper().strip()
    
    # 1. Fallback estático
    if bodega_upper in MAPEO_TIENDAS_ESTATICO:
        return MAPEO_TIENDAS_ESTATICO[bodega_upper]
    for k, v in MAPEO_TIENDAS_ESTATICO.items():
        if k in bodega_upper or bodega_upper in k:
            return v
            
    # 2. Fuzzy matching dinámico si hay opciones
    if opciones_erp and process:
        # Extraer palabras clave (ej: "AERO CC" -> "CC")
        bodega_clean = re.sub(r"AERO(?:POSTALE)?\s*[-–]*\s*", "", bodega_upper).strip()
        if not bodega_clean:
             bodega_clean = bodega_upper
             
        mejor_coincidencia, puntaje = process.extractOne(bodega_clean, opciones_erp)
        if puntaje >= 70:  # Umbral de confianza
            return mejor_coincidencia
            
    # 3. Búsqueda simple parcial
    for opcion in opciones_erp:
        if bodega_upper in opcion.upper() or opcion.upper() in bodega_upper:
            return opcion
            
    return ""


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot carga ERP Aeropostale")
    parser.add_argument("--headful", action="store_true", help="Mostrar navegador")
    parser.add_argument("--test-url", type=str, default=None, help="URL de prueba (1 transferencia)")
    parser.add_argument("--limit", type=int, default=None, help="Limitar número de transferencias")
    args = parser.parse_args()

    resultado = run(
        headless=not args.headful,
        test_url=args.test_url,
        limit=args.limit,
    )
    print(json.dumps({"ok": True, "resultados": resultado}, ensure_ascii=False))
    sys.exit(0)
