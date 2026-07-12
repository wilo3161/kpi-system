import os
import sys

# 1. Clean inventario.py
file_path = 'modules/inventario.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix tabs definition
content = content.replace(', "🤖 Agente CEDI"', '')
content = content.replace('tab_sku, tab_atributo, tab_kpi, tab_agente =', 'tab_sku, tab_atributo, tab_kpi =')

lines = content.split('\n')
idx = -1
for i, line in enumerate(lines):
    if '# ---------- TAB AGENTE CEDI ----------' in line:
        idx = i
        break

if idx != -1:
    lines = lines[:idx]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Inventario cleaned')

# 2. Clean requirements.txt
req_path = 'requirements.txt'
with open(req_path, 'r', encoding='utf-8') as f:
    reqs = f.readlines()
reqs = [r for r in reqs if 'google-generativeai' not in r]
with open(req_path, 'w', encoding='utf-8') as f:
    f.writelines(reqs)
print('Requirements cleaned')

# 3. Clean equipo.py (remove IA tab)
eq_path = 'modules/equipo.py'
with open(eq_path, 'r', encoding='utf-8') as f:
    eq_content = f.read()

# Replace tab definition
eq_content = eq_content.replace(', "🤖 Asistente IA"', '')
eq_content = eq_content.replace('"🤖 Asistente IA", ', '')

eq_lines = eq_content.split('\n')
start_ia = -1
end_ia = -1

for i, line in enumerate(eq_lines):
    if 'PESTAÑA 4 – ASISTENTE IA' in line:
        start_ia = i - 1
    if 'PESTAÑA 5 – REGISTRO DIARIO' in line:
        end_ia = i - 1

if start_ia != -1 and end_ia != -1:
    eq_lines = eq_lines[:start_ia] + eq_lines[end_ia:]

with open(eq_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(eq_lines))
print('Equipo cleaned')

# 4. Clean auditoria.py
aud_path = 'modules/auditoria.py'
with open(aud_path, 'r', encoding='utf-8') as f:
    aud_content = f.read()

# We need to remove _analizar_con_gemini and calls to it
# Let's just remove the function and the columns that use it. This might be tricky via script.
