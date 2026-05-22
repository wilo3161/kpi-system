import os

search_dir = r"c:\Users\wilso\Downloads\kpi-system-main"
pattern = "alerta"

for root, dirs, files in os.walk(search_dir):
    if any(x in root for x in [".git", "scratch", ".system_generated"]):
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if pattern in line.lower():
                            print(f"{file}:{i+1}: {line.strip()}")
            except Exception:
                pass
