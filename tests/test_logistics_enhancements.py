"""
tests/test_logistics_enhancements.py
═══════════════════════════════════════════════════════════════════════════════
Suite de Pruebas: Mejoras en Dashboard Logístico (Ubicación & Transferidores)
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
from datetime import date
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.data_processing import procesar_archivos, obtener_geo_tienda


def test_obtener_geo_tienda():
    """1. Verifica el mapeo geográfico de tiendas a cantones y coordenadas."""
    geo_gye = obtener_geo_tienda("MALL DEL SOL")
    assert geo_gye['canton'] == 'GUAYAQUIL'
    assert geo_gye['provincia'] == 'GUAYAS'

    geo_uio = obtener_geo_tienda("AEROPOSTALE 6 DE DICIEMBRE")
    assert geo_uio['canton'] == 'QUITO'
    assert geo_uio['provincia'] == 'PICHINCHA'

    geo_cue = obtener_geo_tienda("CUENCA")
    assert geo_cue['canton'] == 'CUENCA'
    print("  ✅ [Test 1] obtener_geo_tienda(): OK -> Mapeos cantonales correctos")


def test_procesar_archivos_con_transferidor_y_geo():
    """2. Verifica que procesar_archivos extraiga cantón, provincia y transferidor."""
    df_t = pd.DataFrame([
        {"SECUENCIAL": "501", "BODEGA DESTINO": "MALL DEL SOL", "CANTIDAD": 120, "TRANSFERIDOR": "Wilson Perez", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "502", "BODEGA DESTINO": "AMBATO", "CANTIDAD": 80, "TRANSFERIDOR": "Juan Tipan", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "503", "BODEGA DESTINO": "AEROPOSTALE 6 DE DICIEMBRE", "CANTIDAD": 100, "TRANSFERIDOR": "Wilson Perez", "FECHA": "2026-08-24"}
    ])
    df_d = pd.DataFrame([
        {"SECUENCIAL": "501", "PRODUCTO": "AERO GUYS TEES BLACK M", "CANTIDAD": 115, "COSTO": 12.0, "CATEGORIA": "TEES"},
        {"SECUENCIAL": "501", "PRODUCTO": "AERO PLASTIC BAG MEDIUM", "CANTIDAD": 5, "COSTO": 0.2, "CATEGORIA": "FUNDAS"},
        {"SECUENCIAL": "502", "PRODUCTO": "AERO GIRLS HOODIE RED S", "CANTIDAD": 80, "COSTO": 22.0, "CATEGORIA": "HOODIES"},
        {"SECUENCIAL": "503", "PRODUCTO": "AERO GUYS JEANS DENIM 32", "CANTIDAD": 100, "COSTO": 25.0, "CATEGORIA": "JEANS"}
    ])

    df_cruce, df_det = procesar_archivos(df_t, df_d)
    assert df_cruce is not None
    assert 'CANTON' in df_cruce.columns
    assert 'PROVINCIA' in df_cruce.columns
    assert 'TRANSFERIDOR' in df_cruce.columns

    # Validar transferidores
    assert df_cruce[df_cruce['SECUENCIAL'] == '501']['TRANSFERIDOR'].iloc[0] == "Wilson Perez"
    assert df_cruce[df_cruce['SECUENCIAL'] == '502']['TRANSFERIDOR'].iloc[0] == "Juan Tipan"

    # Validar cantones
    assert df_cruce[df_cruce['SECUENCIAL'] == '501']['CANTON'].iloc[0] == "GUAYAQUIL"
    assert df_cruce[df_cruce['SECUENCIAL'] == '502']['CANTON'].iloc[0] == "AMBATO"
    assert df_cruce[df_cruce['SECUENCIAL'] == '503']['CANTON'].iloc[0] == "QUITO"

    print("  ✅ [Test 2] procesar_archivos(): OK -> Cruce de datos, Transferidor y Geografía validados")


def test_metricas_transferidores():
    """3. Calcula métricas agregadas por transferidor."""
    df_t = pd.DataFrame([
        {"SECUENCIAL": "1", "BODEGA DESTINO": "MALL DEL SOL", "CANTIDAD": 500, "TRANSFERIDOR": "Wilson Perez", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "2", "BODEGA DESTINO": "AEROPOSTALE 6 DE DICIEMBRE", "CANTIDAD": 300, "TRANSFERIDOR": "Wilson Perez", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "3", "BODEGA DESTINO": "AMBATO", "CANTIDAD": 200, "TRANSFERIDOR": "Juan Tipan", "FECHA": "2026-08-24"}
    ])
    df_d = pd.DataFrame([
        {"SECUENCIAL": "1", "PRODUCTO": "TEES", "CANTIDAD": 500, "COSTO": 10.0, "CATEGORIA": "TEES"},
        {"SECUENCIAL": "2", "PRODUCTO": "POLOS", "CANTIDAD": 300, "COSTO": 15.0, "CATEGORIA": "POLOS"},
        {"SECUENCIAL": "3", "PRODUCTO": "JEANS", "CANTIDAD": 200, "COSTO": 20.0, "CATEGORIA": "JEANS"}
    ])

    df_cruce, _ = procesar_archivos(df_t, df_d)
    tot = df_cruce['PRENDAS'].sum() + df_cruce['FUNDAS'].sum()
    assert tot == 1000

    wp = df_cruce[df_cruce['TRANSFERIDOR'] == 'Wilson Perez']
    assert wp['SECUENCIAL'].nunique() == 2
    assert (wp['PRENDAS'].sum() + wp['FUNDAS'].sum()) == 800
    assert ((wp['PRENDAS'].sum() + wp['FUNDAS'].sum()) / tot) * 100 == 80.0

    print("  ✅ [Test 3] Metricas Transferidores: OK -> Wilson Perez: 80% del volumen total")


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════════")
    print("🧪 PRUEBAS UNITARIAS: MÓDULO LOGÍSTICO Y TRANSFERENCIAS")
    print("═══════════════════════════════════════════════════════════════")
    test_obtener_geo_tienda()
    test_procesar_archivos_con_transferidor_y_geo()
    test_metricas_transferidores()
    print("═══════════════════════════════════════════════════════════════")
    print("🎉 TODAS LAS PRUEBAS DEL DASHBOARD LOGÍSTICO PASARON (100% PASS) 🎉")
    print("═══════════════════════════════════════════════════════════════")
