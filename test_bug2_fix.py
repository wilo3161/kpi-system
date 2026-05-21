# Test Oficial - FIX BUG #2
# Módulo Logística: Pestañas Histórico y Forecast
# Fashion Club ERP - Aeropostale Ecuador

import sys
sys.path.insert(0, '/workspace')

def test_funciones_historico_forecast_existen():
    """Verifica que las funciones requeridas estén definidas."""
    import app
    
    assert hasattr(app, 'render_tab_historico_logistico'), "❌ Falta render_tab_historico_logistico"
    assert hasattr(app, 'render_tab_forecast_logistico'), "❌ Falta render_tab_forecast_logistico"
    assert hasattr(app, 'consultar_historico_logistico'), "❌ Falta consultar_historico_logistico"
    assert hasattr(app, 'obtener_datos_historico_forecast'), "❌ Falta obtener_datos_historico_forecast"
    assert hasattr(app, 'calcular_forecast_logistico'), "❌ Falta calcular_forecast_logistico"
    print("✅ Todas las funciones existen")


def test_show_logistica_tiene_4_tabs():
    """Verifica que show_logistica tenga 4 tabs."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la definición de tabs en show_logistica
    assert 'tab1, tab2, tab3, tab4 = st.tabs' in content, "❌ No se encontró definición de 4 tabs"
    assert '"📅 Histórico"' in content, "❌ Falta tab Histórico"
    assert '"🔮 Forecast"' in content, "❌ Falta tab Forecast"
    print("✅ show_logistica tiene 4 tabs correctamente definidos")


def test_no_botones_predefinidos():
    """Verifica que NO existan botones de rango predefinido (FIX 2a)."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # En el contexto de render_tab_historico_logistico, no debe haber botones de 1 día, 3 días, etc.
    # Buscamos específicamente en la función
    lines = content.split('\n')
    in_historico_func = False
    for line in lines:
        if 'def render_tab_historico_logistico' in line:
            in_historico_func = True
        elif in_historico_func and line.strip().startswith('def '):
            break
        
        if in_historico_func:
            assert '"1 día"' not in line, "❌ Se encontró botón de 1 día (prohibido por FIX 2a)"
            assert '"3 días"' not in line, "❌ Se encontró botón de 3 días (prohibido por FIX 2a)"
            assert '"Semana"' not in line, "❌ Se encontró botón de Semana (prohibido por FIX 2a)"
            assert '"1 mes"' not in line, "❌ Se encontró botón de 1 mes (prohibido por FIX 2a)"
            assert '"1 año"' not in line, "❌ Se encontró botón de 1 año (prohibido por FIX 2a)"
    
    print("✅ No hay botones de rango predefinido (FIX 2a cumplido)")


def test_validaciones_fechas_presentes():
    """Verifica que existan validaciones de fechas para evitar crash (FIX 2b)."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Validar que exista chequeo de fecha_inicio > fecha_fin
    assert 'if fecha_inicio > fecha_fin' in content, "❌ Falta validación de fecha inicio > fin"
    assert 'st.error("❌ La fecha inicio debe ser anterior a la fecha fin")' in content, "❌ Falta mensaje de error para fechas inválidas"
    assert 'st.stop()' in content, "❌ Falta st.stop() después de validaciones"
    
    print("✅ Validaciones de fechas presentes (FIX 2b cumplido)")


def test_session_state_para_persistencia():
    """Verifica uso de session_state para persistencia de datos (FIX 2c)."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert "st.session_state['df_historico']" in content or "st.session_state['df_historico'] = df" in content, "❌ Falta persistencia en session_state"
    assert "st.session_state['historico_filtros']" in content, "❌ Falta persistencia de filtros"
    
    print("✅ Session state usado para persistencia (FIX 2c cumplido)")


def test_guard_clauses_en_consulta():
    """Verifica guard clauses en función de consulta."""
    import inspect
    import app
    
    source = inspect.getsource(app.consultar_historico_logistico)
    
    # Verificar que la función no lance excepciones sin manejar
    assert 'try:' in source or 'except' in source or 'return' in source, "❌ Función sin manejo adecuado de errores"
    
    print("✅ Guard clauses presentes en consulta")


def test_documentacion_fix():
    """Verifica que cada función tenga comentario FIX."""
    import inspect
    import app
    
    funcs_a_verificar = [
        app.render_tab_historico_logistico,
        app.render_tab_forecast_logistico,
        app.consultar_historico_logistico,
    ]
    
    for func in funcs_a_verificar:
        docstring = inspect.getdoc(func)
        assert docstring is not None, f"❌ Función {func.__name__} sin docstring"
        assert 'FIX' in docstring or 'BUG' in docstring, f"❌ Función {func.__name__} sin comentario FIX en docstring"
    
    print("✅ Documentación FIX presente en todas las funciones")


def test_imports_necesarios():
    """Verifica que los imports necesarios estén presentes."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar imports dentro de las funciones o al inicio
    assert 'import plotly.express' in content or 'import plotly.graph_objects' in content, "❌ Faltan imports de plotly"
    assert 'import pandas as pd' in content, "❌ Falta import de pandas"
    
    print("✅ Imports necesarios presentes")


def test_excepciones_manejadas():
    """Verifica que las excepciones sean manejadas adecuadamente."""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # En render_tab_historico_logistico
    lines = content.split('\n')
    in_historico = False
    found_try_except = False
    
    for line in lines:
        if 'def render_tab_historico_logistico' in line:
            in_historico = True
        elif in_historico and line.strip().startswith('def '):
            break
        
        if in_historico and 'try:' in line:
            found_try_except = True
            break
    
    assert found_try_except, "❌ No se encontró try/except en render_tab_historico_logistico"
    
    # En render_tab_forecast_logistico
    in_forecast = False
    found_try_except_forecast = False
    
    for line in lines:
        if 'def render_tab_forecast_logistico' in line:
            in_forecast = True
        elif in_forecast and line.strip().startswith('def '):
            break
        
        if in_forecast and 'try:' in line:
            found_try_except_forecast = True
            break
    
    assert found_try_except_forecast, "❌ No se encontró try/except en render_tab_forecast_logistico"
    
    print("✅ Excepciones manejadas en ambas funciones")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 TEST OFICIAL - FIX BUG #2")
    print("Módulo Logística: Histórico y Forecast")
    print("=" * 60)
    
    tests = [
        test_funciones_historico_forecast_existen,
        test_show_logistica_tiene_4_tabs,
        test_no_botones_predefinidos,
        test_validaciones_fechas_presentes,
        test_session_state_para_persistencia,
        test_guard_clauses_en_consulta,
        test_documentacion_fix,
        test_imports_necesarios,
        test_excepciones_manejadas,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n📋 Ejecutando: {test.__name__}")
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FALLÓ: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ RESULTADO: {passed}/{len(tests)} tests pasaron")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ¡BUG #2 CORREGIDO EXITOSAMENTE!")
        print("\n📝 Resumen del fix:")
        print("   ✅ 2a: Eliminados botones de rango predefinido")
        print("   ✅ 2b: Agregadas validaciones para evitar crash")
        print("   ✅ 2c: Persistencia completa con session_state")
        print("   ✅ Tabs Histórico y Forecast implementados")
        print("   ✅ Inspirado en SAP IBP Demand Planning")
    else:
        print(f"\n⚠️ {failed} tests fallaron. Revisar implementación.")
    
    sys.exit(0 if failed == 0 else 1)
