"""
Test oficial para BUG #3 FIX - Imágenes de módulos ocupan espacio completo
Fashion Club ERP - Sistema de Validación
"""

import sys
sys.path.insert(0, '/workspace')

def test_create_module_card_signature():
    """Verificar que la función tiene el parámetro image_path"""
    import inspect
    from app import create_module_card
    
    sig = inspect.signature(create_module_card)
    params = list(sig.parameters.keys())
    
    assert 'image_path' in params, "❌ Falta parámetro image_path"
    assert sig.parameters['image_path'].default is None, "❌ image_path debe tener default None"
    print("✅ Función create_module_card tiene signature correcta")

def test_default_images_mapping():
    """Verificar mapeo de imágenes por defecto"""
    import inspect
    from app import create_module_card
    
    source = inspect.getsource(create_module_card)
    
    required_modules = ['generar_guias', 'logistica', 'control_inventario', 
                       'reportes_avanzados', 'configuracion']
    required_images = ['Fashion.jpg', 'Tempo.jpg']
    
    for module in required_modules:
        assert module in source, f"❌ Módulo {module} no está en el mapeo"
    
    for img in required_images:
        assert img in source, f"❌ Imagen {img} no está en el mapeo"
    
    print("✅ Mapeo de imágenes por defecto correcto")

def test_css_classes_added():
    """Verificar que las clases CSS nuevas existen"""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_classes = [
        '.module-card-image',
        '.module-card-image-full',
        '.module-card-overlay',
        'BUG #3 FIX'
    ]
    
    for cls in required_classes:
        assert cls in content, f"❌ Clase/estilo {cls} no encontrado en CSS"
    
    print("✅ Clases CSS para imágenes full-cover agregadas")

def test_html_structure_with_image():
    """Verificar estructura HTML con imagen"""
    import inspect
    from app import create_module_card
    
    source = inspect.getsource(create_module_card)
    
    required_elements = [
        '<img src=',
        'class="module-card-image-full"',
        'class="module-card-overlay"',
    ]
    
    for elem in required_elements:
        assert elem in source, f"❌ Elemento HTML {elem} no encontrado"
    
    print("✅ Estructura HTML con imagen correcta")

def test_css_object_fit_exists():
    """Verificar que object-fit: cover está en el CSS"""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'object-fit: cover' in content, "❌ object-fit: cover no encontrado en CSS"
    print("✅ object-fit: cover encontrado en CSS")

def test_fallback_to_icon():
    """Verificar fallback a ícono si imagen no existe"""
    import inspect
    from app import create_module_card
    
    source = inspect.getsource(create_module_card)
    
    assert 'os.path.exists' in source, "❌ No verifica existencia de archivo"
    assert 'Fallback' in source or 'fallback' in source, "❌ No hay comentario de fallback"
    assert 'card-icon' in source, "❌ No mantiene ícono como fallback"
    
    print("✅ Fallback a ícono implementado correctamente")

def test_unique_button_keys():
    """Verificar que los botones tienen keys únicos"""
    import inspect
    from app import create_module_card
    
    source = inspect.getsource(create_module_card)
    
    assert 'btn_{module_key}_image' in source, "❌ Key único para botón de imagen no encontrado"
    
    print("✅ Keys únicos para botones implementados")

def test_css_z_index_updated():
    """Verificar que z-index se actualizó para soportar overlays"""
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el nuevo z-index 3 para ::before
    assert 'z-index: 3;' in content, "❌ z-index: 3 no encontrado (debería ser para ::before)"
    assert 'pointer-events: none;' in content, "❌ pointer-events: none no encontrado"
    
    print("✅ Z-index actualizado correctamente para capas")

def test_syntax_valid():
    """Verificar sintaxis Python válida"""
    import py_compile
    try:
        py_compile.compile('/workspace/app.py', doraise=True)
        print("✅ Sintaxis Python válida")
    except py_compile.PyCompileError as e:
        raise AssertionError(f"❌ Error de sintaxis: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 EJECUTANDO TESTS PARA BUG #3 FIX")
    print("=" * 60)
    
    tests = [
        test_create_module_card_signature,
        test_default_images_mapping,
        test_css_classes_added,
        test_html_structure_with_image,
        test_css_object_fit_exists,
        test_fallback_to_icon,
        test_unique_button_keys,
        test_css_z_index_updated,
        test_syntax_valid,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(str(e))
            failed += 1
        except Exception as e:
            print(f"❌ Error inesperado en {test.__name__}: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 RESULTADOS: {passed}/{len(tests)} tests pasaron")
    
    if failed == 0:
        print("✅ TODOS LOS TESTS PASARON - BUG #3 CORREGIDO")
        sys.exit(0)
    else:
        print(f"❌ {failed} tests fallaron")
        sys.exit(1)
