#!/usr/bin/env python3
import os
import re
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeout

# UTF-8 terminal encoding
import io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

JIREHWEB_URL  = "https://fashion.sisconti.com/"
JIREHWEB_USER = os.getenv("JIREHWEB_USER", "wperez")
JIREHWEB_PASS = os.getenv("JIREHWEB_PASS", "Wilo3161*")

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

PROCESADAS_JSON = BASE_DIR / "guias_laar_procesadas.json"

# Import TIENDAS_DATA mapping
sys.path.append(str(BASE_DIR))
try:
    from tiendas_data import TIENDAS_DATA
except ImportError:
    TIENDAS_DATA = []

def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [LAAR_BOT] [{level}] {msg}", flush=True)

def clean_secuencial(sec: str) -> str:
    """Strip leading zeros from secuencial number."""
    sec = sec.strip()
    if sec.isdigit():
        return str(int(sec))
    return sec

def clean_cantidad(cant_str: str) -> int:
    """Clean decimal zeroes from quantity of garments (e.g. 1.000.000 -> 1, 39.000.000 -> 39)."""
    val = cant_str.strip()
    if "." in val:
        # split at the first dot, as all trailing portions are decimals
        val = val.split(".")[0]
    val = re.sub(r"[^\d]", "", val)
    return int(val) if val.isdigit() else 0

def clean_valor(cost_str: str) -> float:
    """Clean and parse cost value."""
    val = cost_str.replace(",", "").strip()
    try:
        return float(val)
    except ValueError:
        return 0.0

def load_procesadas() -> set[str]:
    if PROCESADAS_JSON.exists():
        try:
            with open(PROCESADAS_JSON, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_procesadas(procesadas: set[str]):
    try:
        with open(PROCESADAS_JSON, "w", encoding="utf-8") as f:
            json.dump(list(procesadas), f, indent=4, ensure_ascii=False)
    except Exception as e:
        log(f"Error guardando secuenciales procesados: {e}", "WARN")

def map_tienda_data(bodega_destino: str) -> dict:
    """Find store config in TIENDAS_DATA based on bodega_destino name or aliases."""
    name_upper = bodega_destino.upper().strip()
    
    # OIL mapping
    if name_upper in ["OIL", "OIL UNO", "OIL1", "OIL_UNO"]:
        name_upper = "PRICE CLUB - IBARRA"

    # Normalize name_upper to improve matches
    normalized_name = name_upper.replace("AEROPOSTALE", "").replace("PRICE CLUB", "").replace("-", "").strip()

    best_match = None
    for t in TIENDAS_DATA:
        t_name = t.get("Nombre de Tienda", "").upper()
        t_norm = t_name.replace("AEROPOSTALE", "").replace("PRICE CLUB", "").replace("-", "").strip()
        
        # Exact Normalized Match or Substring Match
        if normalized_name == t_norm or t_norm in normalized_name or normalized_name in t_norm:
            best_match = t
            break

    if best_match:
        return {
            "destinatario": best_match.get("Contacto", "Gerente de Tienda"),
            "direccion": best_match.get("Dirección", "Dirección de Tienda"),
            "telefono": best_match.get("Teléfono", "0999999999"),
            "ciudad": best_match.get("Destino", best_match.get("Ciudad", "Quito"))
        }

    # Fallback default values
    return {
        "destinatario": "Encargado " + bodega_destino,
        "direccion": "Dirección " + bodega_destino,
        "telefono": "0999999999",
        "ciudad": "QUITO"
    }

def run_extraction(headless: bool = True, fecha_inicio: str = None, fecha_fin: str = None, 
                   piezas: int = 1, peso: float = 1.0, contenido: str = "MERCADERIA", tamaño: str = "MEDIANO"):
    
    log("Iniciando extracción JirehWEB...")
    procesadas = load_procesadas()
    
    hoy_str = datetime.now().strftime("%Y-%m-%d")
    fecha_inicio = fecha_inicio or hoy_str
    fecha_fin = fecha_fin or hoy_str

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=500 if not headless else 0,
            args=["--start-maximized"]
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900}, accept_downloads=True)
        page = context.new_page()
        page.on("dialog", lambda d: d.accept())

        log(f"Conectando a {JIREHWEB_URL}...")
        page.goto(JIREHWEB_URL, wait_until="networkidle", timeout=30000)

        # Login
        if page.locator("input[name='user'], input[id='user']").count() > 0:
            log("Haciendo login...")
            page.fill("input[name='user']", JIREHWEB_USER)
            page.fill("input[name='pass']", JIREHWEB_PASS)
            page.keyboard.press("Enter")
            page.wait_for_timeout(6000)

        # Navegación del menú lateral
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
            browser.close()
            return []

        # Llenar filtros del reporte
        log("Llenando formulario de consulta...")
        try:
            content_frame = menu_frame.locator("iframe[name='divContenedorPrincipal']").content_frame
            page.wait_for_timeout(2000)

            content_frame.locator("#fecha_ini").click(timeout=10000)
            content_frame.locator("#fecha_ini").fill("")
            content_frame.locator("#fecha_ini").fill(fecha_inicio)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            content_frame.locator("#fecha_fin").click(timeout=10000)
            content_frame.locator("#fecha_fin").fill("")
            content_frame.locator("#fecha_fin").fill(fecha_fin)
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            content_frame.locator("#sucursal").select_option("1", timeout=10000) # MATRIZ
            page.wait_for_timeout(500)

            content_frame.get_by_text("Consultar").click(timeout=8000)
            log("Aguardando tabla de resultados...")
            page.wait_for_timeout(4000)
        except Exception as e:
            log(f"Error al llenar formulario de consulta: {e}", "ERROR")
            browser.close()
            return []

        # Parsear tabla de transferencias
        try:
            tabla_resultados = content_frame.locator("table:has-text('Bodega Destino')")
            tabla_resultados.locator("tbody tr").first.wait_for(timeout=10000)
        except Exception:
            log("No se encontraron resultados en la tabla (timeout o vacía).", "INFO")
            browser.close()
            return []

        rows = tabla_resultados.locator("tbody tr")
        total_rows = rows.count()
        log(f"Filas totales encontradas en la tabla: {total_rows}")

        registros_laar = []
        nuevas_procesadas = set()

        for idx in range(total_rows):
            row = rows.nth(idx)
            text_row = row.inner_text()
            if "N.-" in text_row or "TOTALES" in text_row:
                continue

            try:
                tds = row.locator("td")
                if tds.count() < 9:
                    continue

                # Columna 1: Índice fila
                n_val = tds.nth(0).inner_text().strip()
                if not n_val.isdigit():
                    continue

                # Columna 5: Secuencial
                secuencial_raw = tds.nth(4).inner_text().strip()
                secuencial = clean_secuencial(secuencial_raw)

                # Control de Duplicados
                if secuencial in procesadas:
                    log(f"Ignorando secuencial ya procesado: {secuencial}")
                    continue

                # Columna 6: Bodega Destino
                bodega_destino = tds.nth(5).inner_text().strip()
                if not bodega_destino or "TOTAL" in bodega_destino.upper():
                    continue

                # Columna 7: Cantidad de Prendas
                prendas_raw = tds.nth(6).inner_text().strip()
                prendas = clean_cantidad(prendas_raw)

                # Columna 8: Costo
                costo_raw = tds.nth(7).inner_text().strip()
                costo = clean_valor(costo_raw)

                # Resolver datos destinatario
                tienda_info = map_tienda_data(bodega_destino)

                # Construir registro formato Laar
                fecha_recoleccion = datetime.now().strftime("%d/%m/%Y")
                comentario = f"# Transferencia {secuencial} con {prendas} prendas"

                reg = {
                    "GUIA": "",
                    "NOMBRE DESTINATARIO": tienda_info["destinatario"],
                    "DIRECCION DESTINATARIO": tienda_info["direccion"],
                    "TELEFONO DESTINARIO 1": tienda_info["telefono"],
                    "TELEFONO DESTINARIO 2": "",
                    "CODIGOPD": "no llenar",
                    "CIUDAD DESTINATARIO": tienda_info["ciudad"],
                    "PIEZAS": piezas,
                    "PESO CLIENTE": peso,
                    "VALOR DECLARADO": costo,
                    "PRODUCTO": "MERCADERIA",
                    "CONTENIDO": contenido,
                    "COMENTARIO": comentario,
                    "TAMANIO": tamaño,
                    "NOMBRE REMITENTE": "CD MATRIZ",
                    "DIRECCION ORIGEN": "San Roque La Merced Calle santo Thomas",
                    "TELEFONO ORIGEN": 993052744,
                    "TELEFONO ORIGEN 2": "no llenar",
                    "CIUDAD ORIGEN": "San Roque",
                    "FECHARECOLECCION": fecha_recoleccion,
                    "ORDEN": "no llenar",
                    "VALOR PRODUCTO": costo,
                    "VALOR FLETE": "no llenar",
                    "LATITUD DESTINATARIO": "no llenar",
                    "LONGITUD DESTINATARIO": "no llenar"
                }

                registros_laar.append(reg)
                nuevas_procesadas.add(secuencial)
                log(f"Agregado transferencia {secuencial} hacia {bodega_destino} ({prendas} prendas)")

            except Exception as row_err:
                log(f"Error procesando fila {idx}: {row_err}", "WARN")

        browser.close()

        # Guardar secuenciales procesados si hay nuevos
        if nuevas_procesadas:
            procesadas.update(nuevas_procesadas)
            save_procesadas(procesadas)

        return registros_laar

def generate_excel(registros: list, output_filename: str = "guiaslaar_generadas.xlsx") -> Path:
    columns = [
        'GUIA', 'NOMBRE DESTINATARIO', 'DIRECCION DESTINATARIO', 'TELEFONO DESTINARIO 1', 
        'TELEFONO DESTINARIO 2', 'CODIGOPD', 'CIUDAD DESTINATARIO', 'PIEZAS', 'PESO CLIENTE', 
        'VALOR DECLARADO', 'PRODUCTO', 'CONTENIDO', 'COMENTARIO', 'TAMANIO', 'NOMBRE REMITENTE', 
        'DIRECCION ORIGEN', 'TELEFONO ORIGEN', 'TELEFONO ORIGEN 2', 'CIUDAD ORIGEN', 
        'FECHARECOLECCION', 'ORDEN', 'VALOR PRODUCTO', 'VALOR FLETE', 'LATITUD DESTINATARIO', 
        'LONGITUD DESTINATARIO'
    ]
    df = pd.DataFrame(registros, columns=columns)
    output_path = BASE_DIR / output_filename
    df.to_excel(output_path, index=False)
    log(f"Archivo Excel generado con éxito en: {output_path}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headful", action="store_true", help="Ejecutar de forma visible")
    parser.add_argument("--fecha-inicio", type=str, default=None)
    parser.add_argument("--fecha-fin", type=str, default=None)
    parser.add_argument("--piezas", type=int, default=1)
    parser.add_argument("--peso", type=float, default=1.0)
    parser.add_argument("--contenido", type=str, default="MERCADERIA")
    parser.add_argument("--tamanio", type=str, default="MEDIANO")
    args = parser.parse_args()

    regs = run_extraction(
        headless=not args.headful,
        fecha_inicio=args.fecha_inicio,
        fecha_fin=args.fecha_fin,
        piezas=args.piezas,
        peso=args.peso,
        contenido=args.contenido,
        tamaño=args.tamanio
    )
    if regs:
        generate_excel(regs)
    else:
        log("No se extrajeron nuevas transferencias válidas/pendientes para exportar.", "INFO")
