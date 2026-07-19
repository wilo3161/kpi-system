import pytest
from database.manager import local_db
import pandas as pd
from modules.guias import generar_guia_backend

def test_batch_generacion_guias():
    # Insert required mock data for the test
    if not local_db.find_one("manifiesto", {"activo": True}):
        local_db.insert("manifiesto", {"activo": True, "guias": [], "metricas": {"total_bultos": 0, "total_prendas": 0}})

    # Using mock data
    tienda_sel = "Tienda A"
    destinatario = "Mock User"
    direccion = "Mock Address"
    telefono = "123456"
    ciudad = "Mock City"
    peso_kg = 1.0
    bultos = 1
    observaciones = "Test Batch"
    numero_transferencia = "001-123456"
    total_prendas = 10
    url_transferencia = "https://mock.url"
    usuario_activo = "test_user"
    items_extraidos = []
    logo_bytes = b"mock logo"
    marca_sel = "Tempo"
    tienda_info = {"encargado": destinatario, "direccion": direccion, "telefono": telefono, "ciudad": ciudad}
    
    success, num_guia, pdf_bytes, doc_guia = generar_guia_backend(
        tienda_sel, destinatario, direccion, telefono, ciudad, peso_kg, bultos, observaciones,
        numero_transferencia, total_prendas, url_transferencia, usuario_activo, items_extraidos,
        logo_bytes, marca_sel, tienda_info
    )
    
    assert success is True
    assert num_guia is not None
    assert doc_guia["numero_transferencia"] == numero_transferencia
    assert doc_guia["total_prendas"] == total_prendas
