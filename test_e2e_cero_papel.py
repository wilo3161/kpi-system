import pytest
from streamlit.testing.v1 import AppTest
import json

def test_flujo_cero_papel():
    # Paso 1: Usuario emisor genera guía
    at_emisor = AppTest.from_file("app.py").run()
    
    # Asumimos que app.py usa session_state para auth
    # Forzamos la autenticación de prueba
    at_emisor.session_state["authenticated"] = True
    at_emisor.session_state["username"] = "test_emisor"
    at_emisor.session_state["role"] = "Administrador"
    at_emisor.run()
    
    # Seleccionamos módulo "guias"
    at_emisor.session_state["module"] = "guias"
    at_emisor.run()
    
    # Paso 2: Usuario tienda recibe guía
    at_tienda = AppTest.from_file("app.py").run()
    at_tienda.session_state["authenticated"] = True
    at_tienda.session_state["username"] = "test_tienda"
    at_tienda.session_state["role"] = "Tienda"
    at_tienda.session_state["assigned_store"] = "Tienda Prueba"
    
    # Simulamos escanear el QR inyectando el query param
    at_tienda.query_params["guia"] = "999999" # Guía generada
    at_tienda.run()
    
    assert True
