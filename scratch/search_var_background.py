import os
import re

search_dir = r"c:\Users\wilso\Downloads\kpi-system-main"
pattern = r"\bbackground\b"

for root, dirs, files in os.walk(search_dir):
    if any(x in root for x in [".git", "scratch", ".system_generated"]):
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        # skip comments and multi-line strings
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        matches = re.findall(pattern, line)
                        if matches:
                            # Print only if it doesn't look like a CSS string block unless it is a python code line
                            # Check if it has assignment or function call or parameter
                            # Let's print all matches to be safe and inspect
                            print(f"{file}:{i+1}: {stripped}")
            except Exception:
                pass
