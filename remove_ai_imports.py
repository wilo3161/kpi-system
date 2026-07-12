import os
import re

directory = '.'
pattern = re.compile(r'^(from ai\..*|import ai\..*)')

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.py') and 'venv' not in root and '.git' not in root:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = [line for line in lines if not pattern.match(line.strip())]
            
            if len(lines) != len(new_lines):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"Removed AI imports from {file_path}")

print("Done")
