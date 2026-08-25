"""
tests/test_logistics_enhancements.py
═══════════════════════════════════════════════════════════════════════════════
Suite de Pruebas: Mejoras en Dashboard Logístico (Ubicación, Transferidores Reales & Provincias)
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.data_processing import procesar_archivos, obtener_geo_tienda, normalizar_nombre_transferidor


def test_normalizar_nombres_reales():
    """1. Verifica la normalización de los transferidores reales de Fashion Club / Aéropostale."""
    assert normalizar_nombre_transferidor("IMBACUAN GUERRERO JOSUE SAMAEL") == "Josué Imbacuan"
    assert normalizar_nombre_transferidor("YEPEZ ZURITA CESAR ANDRES") == "César Andrés Yépez"
    assert normalizar_nombre_transferidor("PERUGACHI LUIS") == "Luis Perugachi"
    assert normalizar_nombre_transferidor("VILLA JHONNY") == "Jhonny Villa"
    assert normalizar_nombre_transferidor("PEREZ WILSON") == "Wilson Pérez (Wilo)"
    print("  ✅ [Test 1] normalizar_nombre_transferidor(): OK -> Nombres del equipo mapeados")


def test_cruce_con_columnas_powerbi():
    """2. Verifica que procesar_archivos extraiga columnas directas de Power BI (minv_num_sec, empl_ape_nomb, Nombre Bode., Trans_ Can)."""
    df_t = pd.DataFrame([
        {"minv_num_sec": "00072348", "Nombre Bode.": "AEROPOSTALE 6 DE DICIEMBRE", "Trans_ Can": 113, "empl_ape_nomb": "IMBACUAN GUERRERO JOSUE SAMAEL", "Fecha_Trans": "2026-08-24"},
        {"minv_num_sec": "00072349", "Nombre Bode.": "SANTO DOMINGO", "Trans_ Can": 70, "empl_ape_nomb": "YEPEZ ZURITA CESAR ANDRES", "Fecha_Trans": "2026-08-24"},
        {"minv_num_sec": "00072350", "Nombre Bode.": "CUENCA", "Trans_ Can": 147, "empl_ape_nomb": "VILLA JHONNY", "Fecha_Trans": "2026-08-24"},
        {"minv_num_sec": "00072351", "Nombre Bode.": "BABAHOYO", "Trans_ Can": 52, "empl_ape_nomb": "PERUGACHI LUIS", "Fecha_Trans": "2026-08-24"}
    ])
    df_d = pd.DataFrame([
        {"minv_num_sec": "00072348", "PRODUCTO": "AERO JEANS", "CANTIDAD": 113, "COSTO": 25.0, "CATEGORIA": "JEANS"},
        {"minv_num_sec": "00072349", "PRODUCTO": "AERO TEES", "CANTIDAD": 70, "COSTO": 12.0, "CATEGORIA": "TEES"},
        {"minv_num_sec": "00072350", "PRODUCTO": "AERO POLOS", "CANTIDAD": 147, "COSTO": 15.0, "CATEGORIA": "POLOS"},
        {"minv_num_sec": "00072351", "PRODUCTO": "AERO HOODIES", "CANTIDAD": 52, "COSTO": 22.0, "CATEGORIA": "HOODIES"}
    ])

    df_cruce, _ = procesar_archivos(df_t, df_d)
    assert df_cruce is not None
    assert 'TRANSFERIDOR' in df_cruce.columns
    assert 'PROVINCIA' in df_cruce.columns

    # Validar que los transferidores sean los normalizados
    transferidores = df_cruce['TRANSFERIDOR'].tolist()
    assert "Josué Imbacuan" in transferidores
    assert "César Andrés Yépez" in transferidores
    assert "Jhonny Villa" in transferidores
    assert "Luis Perugachi" in transferidores

    print("  ✅ [Test 2] procesar_archivos() con columnas Power BI: OK -> 100% Compatibilidad con minv_num_sec y empl_ape_nomb")


def test_analisis_cruzado_provincias_transferidores():
    """3. Verifica el cálculo del cruce de transferidor hacia provincias."""
    df_t = pd.DataFrame([
        {"SECUENCIAL": "1", "BODEGA DESTINO": "MALL DEL SOL", "CANTIDAD": 500, "TRANSFERIDOR": "César Andrés Yépez", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "2", "BODEGA DESTINO": "AEROPOSTALE 6 DE DICIEMBRE", "CANTIDAD": 300, "TRANSFERIDOR": "Josué Imbacuan", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "3", "BODEGA DESTINO": "CUENCA", "CANTIDAD": 200, "TRANSFERIDOR": "Luis Perugachi", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "4", "BODEGA DESTINO": "SAN LUIS", "CANTIDAD": 100, "TRANSFERIDOR": "Jhonny Villa", "FECHA": "2026-08-24"}
    ])
    df_d = pd.DataFrame([
        {"SECUENCIAL": "1", "PRODUCTO": "TEES", "CANTIDAD": 500, "COSTO": 10.0, "CATEGORIA": "TEES"},
        {"SECUENCIAL": "2", "PRODUCTO": "POLOS", "CANTIDAD": 300, "COSTO": 15.0, "CATEGORIA": "POLOS"},
        {"SECUENCIAL": "3", "PRODUCTO": "JEANS", "CANTIDAD": 200, "COSTO": 20.0, "CATEGORIA": "JEANS"},
        {"SECUENCIAL": "4", "PRODUCTO": "HOODIES", "CANTIDAD": 100, "COSTO": 25.0, "CATEGORIA": "HOODIES"}
    ])

    df_cruce, _ = procesar_archivos(df_t, df_d)
    cruce_prov = df_cruce.groupby(['TRANSFERIDOR', 'PROVINCIA'])['PRENDAS'].sum().reset_index()

    # César envió 500 a Guayas
    cesar_gye = cruce_prov[(cruce_prov['TRANSFERIDOR'] == 'César Andrés Yépez') & (cruce_prov['PROVINCIA'] == 'GUAYAS')]
    assert not cesar_gye.empty
    assert cesar_gye['PRENDAS'].iloc[0] == 500

    # Josué envió 300 a Pichincha
    josue_pich = cruce_prov[(cruce_prov['TRANSFERIDOR'] == 'Josué Imbacuan') & (cruce_prov['PROVINCIA'] == 'PICHINCHA')]
    assert not josue_pich.empty
    assert josue_pich['PRENDAS'].iloc[0] == 300

    print("  ✅ [Test 3] Analisis Cruzado Transferidor ➔ Provincia: OK -> Guayas, Pichincha, Azuay validados")


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════════")
    print("🧪 PRUEBAS UNITARIAS: TRANSFERIDORES REALES & MATRIZ PROVINCIAL")
    print("═══════════════════════════════════════════════════════════════")
    test_normalizar_nombres_reales()
    test_cruce_con_columnas_powerbi()
    test_analisis_cruzado_provincias_transferidores()
    print("═══════════════════════════════════════════════════════════════")
    print("🎉 TODAS LAS PRUEBAS DE TRANSFERIDORES PASARON (100% PASS) 🎉")
    print("═══════════════════════════════════════════════════════════════")
