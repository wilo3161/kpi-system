#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
import io
import sys

# UTF-8 en terminal Windows
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

BASE_DIR   = Path(__file__).parent
LOGS_DIR   = BASE_DIR / "logs"
PYTHON     = sys.executable
ERP_URL    = os.getenv("ERP_URL", "https://aeropostale-kpi-2026.streamlit.app/")

LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [ORCH] [{level}] {msg}", flush=True)

def pedir_rango_fechas() -> tuple[str, str]:
    hoy = datetime.now().strftime("%Y-%m-%d")
    if not sys.stdin.isatty():
        return hoy, hoy
    print("\n--- Rango de fechas para Reporte Transf. Matriz ---")
    fi = input(f"  Fecha Inicio (AAAA-MM-DD) [Enter = hoy {hoy}]: ").strip() or hoy
    ff = input(f"  Fecha Final  (AAAA-MM-DD) [Enter = hoy {hoy}]: ").strip() or hoy
    return fi, ff

def run(headful: bool = True, dry_run: bool = False, limit: int = None, erp_url: str = None):
    inicio = datetime.now()
    log("=" * 60)
    log("BOT AUTOMATIZACIÓN AEROPOSTALE - INICIO")
    log("=" * 60)

    erp_url = erp_url or ERP_URL
    fecha_inicio, fecha_fin = pedir_rango_fechas()

    # FASE 1: JirehWEB
    log("\n--- FASE 1: Extracción JirehWEB ---")
    cmd_jireh = [PYTHON, str(BASE_DIR / "bot_jirehweb.py")]
    if headful: cmd_jireh.append("--headful")
    if dry_run: cmd_jireh.append("--dry-run")
    if limit: cmd_jireh.extend(["--limit", str(limit)])
    if fecha_inicio: cmd_jireh.extend(["--fecha-inicio", fecha_inicio])
    if fecha_fin: cmd_jireh.extend(["--fecha-fin", fecha_fin])

    subprocess.run(cmd_jireh, capture_output=False, text=True)
    
    json_path = BASE_DIR / "transferencias_listas.json"
    if not json_path.exists():
        log("No se genero transferencias_listas.json. Abortando.", "ERROR")
        return False

    transferencias = json.loads(json_path.read_text(encoding="utf-8"))
    
    # FASE 2: ERP
    if transferencias:
        log("\n--- FASE 2: Carga en ERP ---")
        cmd_erp = [PYTHON, str(BASE_DIR / "bot_erp.py"), "--erp-url", erp_url]
        if headful: cmd_erp.append("--headful")
        if limit: cmd_erp.extend(["--limit", str(limit)])
        subprocess.run(cmd_erp, capture_output=False, text=True)
    else:
        log("No hay transferencias para cargar en el ERP.")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--erp-url", type=str, default=None)
    args = parser.parse_args()
    ok = run(headful=args.headful, dry_run=args.dry_run, limit=args.limit, erp_url=args.erp_url)
    sys.exit(0 if ok else 1)
