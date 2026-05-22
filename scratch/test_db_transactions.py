import sys
import os
from datetime import datetime, date

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Streamlit elements before importing anything that uses them
import streamlit as st

# Mock st.secrets by overriding the secrets attribute on streamlit
class MockSecrets(dict):
    def __getattr__(self, name):
        return self.get(name, None)
    def __getitem__(self, name):
        return self.get(name, None)

st.secrets = MockSecrets()

# Mock st.session_state
if 'session_state' not in dir(st):
    st.session_state = {}
else:
    try:
        st.session_state['username'] = 'TestRunner'
    except Exception:
        # If it's the real SessionStateProxy, mock it by replacing it
        class MockSessionState(dict):
            pass
        st.session_state = MockSessionState()
        st.session_state['username'] = 'TestRunner'

from database.manager import guardar_operacion_logistica, get_db_v2

def run_tests():
    print("=== INICIANDO PRUEBAS DE TRANSACCIONES Y VALIDACIÓN EN DB ===")
    
    db = get_db_v2()
    print(f"Base de datos activa: {'MongoDB Atlas (Real)' if hasattr(db, 'client') and db.client else 'Mock Local DB'}")
    print(f"Estado de conexión: {db.connected}")
    
    # Caso 1: Datos válidos
    data_valida = {
        "fecha": date.today(),
        "tipo_operacion": "Prueba Transaccional",
        "cantidad": 150,
        "responsable": "TestRunner",
        "archivo_nombre": "test_upload.xlsx",
        "por_categoria": {"Tiendas": 100, "Price Club": 50}
    }
    
    print("\n[Test 1] Guardar datos válidos...")
    res = guardar_operacion_logistica(data_valida)
    print(f"Resultado: {res}")
    assert res is True, "Test 1 Falló: Debería haber guardado exitosamente."
    
    # Verificar inserción
    docs = db.find("historico", {"pestaña": "Prueba Transaccional"})
    print(f"Registros encontrados en DB para la prueba: {len(docs)}")
    assert len(docs) > 0, "Test 1 Falló: No se encontró el registro guardado."
    doc = docs[0]
    print(f"Detalle del registro: {doc}")
    assert doc["usuario"] == "TestRunner", "Test 1 Falló: El responsable no coincide."
    assert doc["metricas"]["total_unidades"] == 150, "Test 1 Falló: Las unidades no coinciden."
    
    # Caso 2: Parámetros inválidos (Cantidad negativa)
    data_invalida_cant = data_valida.copy()
    data_invalida_cant["cantidad"] = -50
    print("\n[Test 2] Intentar guardar con cantidad negativa...")
    res = guardar_operacion_logistica(data_invalida_cant)
    print(f"Resultado: {res}")
    assert res is False, "Test 2 Falló: Debería haber fallado por cantidad negativa."
    
    # Caso 3: Parámetros inválidos (Falta responsable)
    data_invalida_resp = data_valida.copy()
    data_invalida_resp["responsable"] = ""
    print("\n[Test 3] Intentar guardar con responsable vacío...")
    res = guardar_operacion_logistica(data_invalida_resp)
    print(f"Resultado: {res}")
    assert res is False, "Test 3 Falló: Debería haber fallado por responsable vacío."
    
    # Caso 4: Parámetros inválidos (Fecha inválida)
    data_invalida_fecha = data_valida.copy()
    data_invalida_fecha["fecha"] = "fecha-incorrecta"
    print("\n[Test 4] Intentar guardar con fecha inválida...")
    res = guardar_operacion_logistica(data_invalida_fecha)
    print(f"Resultado: {res}")
    assert res is False, "Test 4 Falló: Debería haber fallado por fecha inválida."
    
    # Limpieza
    print("\nLimpiando registros de prueba...")
    db.delete("historico", {"pestaña": "Prueba Transaccional"})
    docs_clean = db.find("historico", {"pestaña": "Prueba Transaccional"})
    print(f"Registros después de limpieza: {len(docs_clean)}")
    assert len(docs_clean) == 0, "Limpieza Falló: No se eliminaron los registros de prueba."
    
    print("\n=== ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE! ===")

if __name__ == "__main__":
    run_tests()
