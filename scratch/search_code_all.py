import os

search_dir = r"c:\Users\wilso\Downloads\kpi-system-main"
pattern = "verificar_guias_vencidas"

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if pattern in line:
                            print(f"{path}:{i+1}: {line.strip()}")
            except Exception:
                pass
