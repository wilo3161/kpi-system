import os
import sys

aud_path = 'modules/auditoria.py'
with open(aud_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'def _analizar_con_gemini' in line:
        skip = True
    if skip and line.strip() == '' and len(new_lines) > 0 and 'def ' in ''.join(lines[lines.index(line)+1:lines.index(line)+3]):
        # End of function roughly
        pass
    
    if 'st.session_state.sugerencia_wilo = None' in line:
        continue
        
    if '🤖 Análisis y Respuesta de wilo IA' in line:
        skip = True
    
    if skip and 'else:' in line and 'Selecciona un correo de la lista' in line:
        skip = False
        new_lines.append(line)
        continue

    if 'with tab3:' in line:
        skip = True
        
    if skip and 'except Exception as e:' in line:
        skip = False

    if not skip:
        new_lines.append(line)

with open(aud_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Also fix the tabs in auditoria
with open(aud_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('tab1, tab2, tab3 = st.tabs(["📥 Bandeja de Entrada", "📤 Redactar Correo", "🤖 wilo IA - Asistente"])', 'tab1, tab2 = st.tabs(["📥 Bandeja de Entrada", "📤 Redactar Correo"])')

# Remove the whole _analizar_con_gemini function manually using string manipulation to be safe
start_idx = content.find('def _analizar_con_gemini')
if start_idx != -1:
    end_idx = content.find('def show_gestor_correos', start_idx)
    if end_idx != -1:
        content = content[:start_idx] + content[end_idx:]

with open(aud_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Auditoria cleaned')
