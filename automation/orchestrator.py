#!/usr/bin/env python3
"""
orchestrator.py
===============
Orquestador principal del bot de automatización.
1. Verifica si el ERP (Streamlit) está corriendo; si no, lo lanza.
2. Ejecuta bot_jirehweb.py para extraer transferencias.
3. Ejecuta bot_erp.py para cargar las guías.

Uso:
    python automation/orchestrator.py --headful
    python automation/orchestrator.py --headful --dry-run
    python automation/orchestrator.py --headful --limit 3
    python automation/orchestrator.py --erp-url http://localhost:8501
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

BASE_DIR   = Path(__file__).parent
LOGS_DIR   = BASE_DIR / "logs"
PYTHON     = sys.executable  # Usar el mismo python que ejecuta este script
APP_PY     = Path(__file__).parent.parent / "app.py"
ERP_URL    = os.getenv("ERP_URL", "http://localhost:8501")

LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [ORCH] [{level}] {msg}", flush=True)


def _erp_esta_corriendo(url: str = ERP_URL, timeout: int = 5) -> bool:
    """Verifica si el ERP responde en la URL indicada."""
    import urllib.request
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return req.status == 200
    except Exception:
        return False


def _lanzar_erp() -> subprocess.Popen | None:
    """Intenta lanzar Streamlit si no está corriendo."""
    if not APP_PY.exists():
        log(f"No se encontró {APP_PY}", "ERROR")
        return None
    log(f"Lanzando ERP: streamlit run {APP_PY}")
    proc = subprocess.Popen(
        [PYTHON, "-m", "streamlit", "run", str(APP_PY), "--server.headless=true"],
        cwd=str(APP_PY.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Esperar hasta 30 segundos a que levante
    for i in range(30):
        time.sleep(1)
        if _erp_esta_corriendo():
            log(f"ERP lanzado y respondiendo (tardó {i+1}s)")
            return proc
        log(f"  Esperando ERP... ({i+1}/30s)", "DEBUG")
    log("ERP no respondió en 30s", "ERROR")
    return None


def run(headful: bool = True, dry_run: bool = False, limit: int = None, erp_url: str = None):
    inicio = datetime.now()
    log("=" * 60)
    log("BOT AUTOMATIZACIÓN AEROPOSTALE - INICIO")
    log("=" * 60)

    erp_url = erp_url or ERP_URL

    # ── PASO 0: Verificar/Lanzar ERP ─────────────────────────────────────────
    log(f"Verificando ERP en {erp_url}...")
    erp_proc = None
    if not _erp_esta_corriendo(erp_url):
        log("ERP no está corriendo. Intentando lanzarlo...", "WARN")
        erp_proc = _lanzar_erp()
        if not _erp_esta_corriendo(erp_url):
            log("No se pudo iniciar el ERP. Verifica que Streamlit esté instalado.", "ERROR")
            return False
    else:
        log("ERP ya está corriendo ✅")

    # ── PASO 1: Extracción JirehWEB ────────────────────────────────────────────
    log("\n--- FASE 1: Extracción JirehWEB ---")
    cmd_jireh = [PYTHON, str(BASE_DIR / "bot_jirehweb.py")]
    if headful:
        cmd_jireh.append("--headful")
    if dry_run:
        cmd_jireh.append("--dry-run")
    if limit:
        cmd_jireh.extend(["--limit", str(limit)])

    log(f"Ejecutando: {' '.join(cmd_jireh)}")
    result_jireh = subprocess.run(cmd_jireh, capture_output=False, text=True)
    if result_jireh.returncode != 0:
        log(f"bot_jirehweb.py terminó con error (código {result_jireh.returncode})", "ERROR")
        return False

    # Verificar que se generó el JSON
    json_path = BASE_DIR / "transferencias_listas.json"
    if not json_path.exists():
        log("No se generó transferencias_listas.json", "ERROR")
        return False

    transferencias = json.loads(json_path.read_text(encoding="utf-8"))
    log(f"Transferencias extraídas: {len(transferencias)}")

    if not transferencias:
        log("No hay transferencias para procesar. Fin.", "WARN")
        return True

    # ── PASO 2: Carga en ERP ───────────────────────────────────────────────────
    log("\n--- FASE 2: Carga en ERP ---")
    cmd_erp = [PYTHON, str(BASE_DIR / "bot_erp.py"), "--erp-url", erp_url]
    if headful:
        cmd_erp.append("--headful")
    if limit:
        cmd_erp.extend(["--limit", str(limit)])

    log(f"Ejecutando: {' '.join(cmd_erp)}")
    result_erp = subprocess.run(cmd_erp, capture_output=False, text=True)
    if result_erp.returncode != 0:
        log(f"bot_erp.py terminó con error (código {result_erp.returncode})", "WARN")

    # ── RESUMEN ────────────────────────────────────────────────────────────────
    duracion = (datetime.now() - inicio).seconds
    results_path = BASE_DIR / "resultados_bot.json"
    if results_path.exists():
        resultados = json.loads(results_path.read_text(encoding="utf-8"))
        ok    = sum(1 for r in resultados if r.get("estado") == "ok")
        error = sum(1 for r in resultados if r.get("estado") not in ("ok", "saltada", "pendiente"))
        salt  = sum(1 for r in resultados if r.get("estado") == "saltada")
        log(f"\n{'='*60}")
        log(f"RESUMEN FINAL ({duracion}s):")
        log(f"  ✅ Guías generadas: {ok}")
        log(f"  ❌ Errores:         {error}")
        log(f"  ⏭️  Saltadas:         {salt}")
        log(f"{'='*60}")

    if erp_proc:
        log("Manteniendo ERP corriendo (no lo cerramos).")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orquestador Bot Aeropostale")
    parser.add_argument("--headful", action="store_true", help="Mostrar navegadores")
    parser.add_argument("--dry-run", action="store_true", help="Solo 1 transferencia de prueba")
    parser.add_argument("--limit", type=int, default=None, help="Límite de transferencias")
    parser.add_argument("--erp-url", type=str, default=None, help="URL del ERP (override)")
    args = parser.parse_args()

    ok = run(
        headful=args.headful,
        dry_run=args.dry_run,
        limit=args.limit,
        erp_url=args.erp_url,
    )
    sys.exit(0 if ok else 1)
