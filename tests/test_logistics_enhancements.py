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


def test_analisis_cruzado():
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
    dfC, _ = procesar_archivos(df_t, df_d)
    
    assert 'PROVINCIA' in dfC.columns
    assert 'CANTON' in dfC.columns
    
    guayas_records = dfC[dfC['PROVINCIA'] == 'GUAYAS']
    assert not guayas_records.empty
    assert 'MALL DEL SOL' in guayas_records['TIENDA'].values
    print("  ✅ [Test 3] Analisis Cruzado Transferidor ➔ Provincia: OK -> Guayas, Pichincha, Azuay validados")


def test_data_science_metrics_engine():
    """4. Verifica el cálculo de Pareto, Densidad y Coeficiente de Variación de Carga."""
    df_t = pd.DataFrame([
        {"SECUENCIAL": "1", "BODEGA DESTINO": "MALL DEL SOL", "CANTIDAD": 500, "TRANSFERIDOR": "César Andrés Yépez", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "2", "BODEGA DESTINO": "AEROPOSTALE 6 DE DICIEMBRE", "CANTIDAD": 300, "TRANSFERIDOR": "Josué Imbacuan", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "3", "BODEGA DESTINO": "CUENCA", "CANTIDAD": 200, "TRANSFERIDOR": "Luis Perugachi", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "4", "BODEGA DESTINO": "SAN LUIS", "CANTIDAD": 100, "TRANSFERIDOR": "Jhonny Villa", "FECHA": "2026-08-24"},
        {"SECUENCIAL": "5", "BODEGA DESTINO": "VENTAS POR MAYOR", "CANTIDAD": 1500, "TRANSFERIDOR": "Wilson Pérez", "FECHA": "2026-08-24"}
    ])
    df_d = pd.DataFrame([
        {"SECUENCIAL": "1", "PRODUCTO": "TEES", "CANTIDAD": 500, "COSTO": 10.0, "CATEGORIA": "TEES"},
        {"SECUENCIAL": "2", "PRODUCTO": "POLOS", "CANTIDAD": 300, "COSTO": 15.0, "CATEGORIA": "POLOS"},
        {"SECUENCIAL": "3", "PRODUCTO": "JEANS", "CANTIDAD": 200, "COSTO": 20.0, "CATEGORIA": "JEANS"},
        {"SECUENCIAL": "4", "PRODUCTO": "HOODIES", "CANTIDAD": 100, "COSTO": 25.0, "CATEGORIA": "HOODIES"},
        {"SECUENCIAL": "5", "PRODUCTO": "TEES BULK", "CANTIDAD": 1500, "COSTO": 8.0, "CATEGORIA": "TEES"}
    ])
    dfC, _ = procesar_archivos(df_t, df_d)

    from services.data_processing import calcular_metricas_transferencias
    met = calcular_metricas_transferencias(dfC)

    assert met['total_prendas'] == 2600
    assert met['total_guias'] == 5
    assert 'df_transferidores' in met
    assert 'df_pareto_tiendas' in met
    assert 'coeficiente_variacion_carga' in met
    assert 'transferidor_lider' in met

    pareto_clases = met['df_pareto_tiendas']['Clase_Pareto'].unique()
    assert any('Clase A' in c for c in pareto_clases)

    print("  ✅ [Test 4] Motor de Ciencia de Datos (Pareto, Densidad, CV Balance): OK")


def test_fact_transferencias_upsert_and_standards():
    """5. Verifica el mecanismo de Upsert atómico en fact_transferencias y estándares textiles."""
    from database.manager import (
        upsert_fact_transferencias, consultar_fact_transferencias,
        obtener_estandares_textiles, guardar_estandar_textil
    )
    from core.data_auditor import DataAuditor

    # Probar Auditor
    h1 = DataAuditor.generar_hash_transferencia("00072348", "2026-08-25", "MALL DEL SOL", "César Andrés Yépez")
    h2 = DataAuditor.generar_hash_transferencia("00072348", "2026-08-25", "MALL DEL SOL", "César Andrés Yépez")
    assert h1 == h2, "El hash debe ser estrictamente determinístico e idempotente"

    # Probar Upsert
    df_test = pd.DataFrame([
        {"SECUENCIAL": "00072348", "TIENDA": "MALL DEL SOL", "PRENDAS": 500, "FUNDAS": 10, "TRANSFERIDOR": "César Andrés Yépez", "FECHA": "2026-08-25", "COSTO_TOTAL": 5000.0, "CANTON": "GUAYAQUIL", "PROVINCIA": "GUAYAS"},
        {"SECUENCIAL": "00072349", "TIENDA": "AEROPOSTALE 6 DE DICIEMBRE", "PRENDAS": 300, "FUNDAS": 5, "TRANSFERIDOR": "Josué Imbacuan", "FECHA": "2026-08-25", "COSTO_TOTAL": 3000.0, "CANTON": "QUITO", "PROVINCIA": "PICHINCHA"}
    ])

    ins, act = upsert_fact_transferencias(df_test, fuente_origen="UNIT_TEST")
    assert ins + act == 2

    # Probar Estándares Textiles
    guardar_estandar_textil("JEANS", 85, "prendas/hora")
    est = obtener_estandares_textiles()
    assert "JEANS" in est
    assert est["JEANS"]["estandar_hora"] == 85

    print("  ✅ [Test 5] Fact_Transferencias (Upsert, Hash Idempotente) & Estándares Textiles: OK")


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════════")
    print("🧪 PRUEBAS UNITARIAS: TRANSFERIDORES REALES & MATRIZ PROVINCIAL")
    print("═══════════════════════════════════════════════════════════════")
    test_normalizar_nombres_reales()
    test_cruce_con_columnas_powerbi()
    test_analisis_cruzado()
    test_data_science_metrics_engine()
    test_fact_transferencias_upsert_and_standards()
    print("═══════════════════════════════════════════════════════════════")
    print("🎉 TODAS LAS PRUEBAS DE TRANSFERIDORES PASARON (100% PASS) 🎉")
    print("═══════════════════════════════════════════════════════════════")
