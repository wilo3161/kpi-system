import sys

file_path = "modules/inventario.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Indent lines 126 to 181 (index 125 to 180)
for i in range(125, 181):
    lines[i] = "    " + lines[i]

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Fixed indentation.")
