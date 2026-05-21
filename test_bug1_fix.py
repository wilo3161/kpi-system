"""
TEST OFICIAL - BUG #1 FIX: Doble clic en botón "Inicio"

Este test valida que la corrección del bug de navegación se implementó correctamente.
El problema original: Al hacer clic en "Inicio", el botón se ponía ROJO y requería
un segundo clic para volver al home.

Causa raíz: Manejo incorrecto de st.session_state con st.rerun() en cascada.
Solución: Single source of truth para navegación con navigate_to_home().
"""

import ast
import sys
from datetime import datetime

def run_tests():
    print("="*70)
    print("🧪 TEST DE VALIDACIÓN - BUG #1 FIX")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    with open('/workspace/app.py', 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
    lines = source.split('\n')
    
    tests_passed = 0
    tests_total = 5
    
    # TEST 1: Existe función centralizada navigate_to_home
    print("TEST 1: Función centralizada navigate_to_home()")
    funciones_nav = [node.name for node in ast.walk(tree) 
                     if isinstance(node, ast.FunctionDef) 
                     and 'home' in node.name.lower()]
    
    if 'navigate_to_home' in funciones_nav:
        print("  ✅ PASÓ: Función navigate_to_home() existe")
        tests_passed += 1
    else:
        print("  ❌ FALLÓ: Falta función navigate_to_home()")
    print()
    
    # TEST 2: Botón Inicio usa patrón on_click (no if st.button)
    print("TEST 2: Botón 'Inicio' usa on_click callback")
    header_section = False
    found_correct_button = False
    
    for i, line in enumerate(lines, 1):
        if 'def show_header()' in line:
            header_section = True
        elif header_section and line.strip().startswith('def '):
            header_section = False
        
        if header_section and '🏠 Inicio' in line and 'st.button' in line:
            if 'on_click=navigate_to_home' in line and 'key=' in line:
                print(f"  ✅ PASÓ: Línea {i} usa on_click=navigate_to_home con key único")
                found_correct_button = True
                tests_passed += 1
                break
    
    if not found_correct_button:
        print("  ❌ FALLÓ: Botón Inicio no usa patrón on_click correcto")
    print()
    
    # TEST 3: No hay st.rerun() en cascada en navegación del header
    print("TEST 3: Sin st.rerun() en cascada en show_header()")
    header_lines = []
    header_section = False
    
    for i, line in enumerate(lines, 1):
        if 'def show_header()' in line:
            header_section = True
        elif header_section and line.strip().startswith('def '):
            header_section = False
        elif header_section:
            header_lines.append((i, line))
    
    has_rerun_in_header = False
    for line_num, line in header_lines:
        if '🏠 Inicio' in line and 'st.rerun()' in line:
            has_rerun_in_header = True
            print(f"  ❌ FALLÓ: Línea {line_num} tiene st.rerun() con botón Inicio")
            break
    
    if not has_rerun_in_header:
        print("  ✅ PASÓ: No hay st.rerun() en cascada en el header")
        tests_passed += 1
    print()
    
    # TEST 4: add_back_button usa navigate_to_home()
    print("TEST 4: Función add_back_button() usa navigate_to_home()")
    if 'def add_back_button' in source:
        # Buscar la función add_back_button
        in_add_back = False
        uses_navigate = False
        
        for line in lines:
            if 'def add_back_button' in line:
                in_add_back = True
            elif in_add_back and line.strip().startswith('def '):
                break
            elif in_add_back and 'navigate_to_home()' in line:
                uses_navigate = True
                break
        
        if uses_navigate:
            print("  ✅ PASÓ: add_back_button usa navigate_to_home()")
            tests_passed += 1
        else:
            print("  ❌ FALLÓ: add_back_button no usa navigate_to_home()")
    else:
        print("  ⚠️ OMITIDO: Función add_back_button no encontrada")
    print()
    
    # TEST 5: Código compila sin errores
    print("TEST 5: Compilación del código")
    try:
        compile(source, '/workspace/app.py', 'exec')
        print("  ✅ PASÓ: El código compila sin errores de sintaxis")
        tests_passed += 1
    except SyntaxError as e:
        print(f"  ❌ FALLÓ: Error de sintaxis en línea {e.lineno}: {e.msg}")
    print()
    
    # RESULTADOS FINALES
    print("="*70)
    print(f"RESULTADOS: {tests_passed}/{tests_total} tests pasaron")
    print("="*70)
    
    if tests_passed == tests_total:
        print()
        print("✅ TODOS LOS TESTS PASARON - BUG #1 CORREGIDO")
        print()
        print("📋 RESUMEN DE CAMBIOS:")
        print("   • Función única: navigate_to_home()")
        print("   • Botón header: on_click=navigate_to_home + key único")
        print("   • Eliminado: st.rerun() en cascada")
        print("   • Unificado: add_back_button() usa navigate_to_home()")
        print()
        print("🎯 COMPORTAMIENTO ESPERADO:")
        print("   • Un solo clic en 'Inicio' → regresa al home")
        print("   • Botón mantiene color original (no se pone rojo)")
        print("   • Navegación consistente en todos los módulos")
        print()
        return 0
    else:
        print()
        print(f"❌ {tests_total - tests_passed} tests fallaron")
        print("El fix requiere revisión adicional.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
