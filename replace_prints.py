import os
import re

directories = ['modules', 'utils', 'database', 'src']
for directory in directories:
    if not os.path.exists(directory): continue
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'print(' in content:
                    # Very naive replacement for simple print() calls
                    content = re.sub(r'\bprint\(', 'logger.info(', content)
                    
                    # Ensure logger is imported and defined
                    if 'import logging' not in content:
                        content = 'import logging\nlogger = logging.getLogger(__name__)\n\n' + content
                    elif 'logger = logging.getLogger' not in content:
                        content = content.replace('import logging', 'import logging\nlogger = logging.getLogger(__name__)')
                        
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
print("Prints replaced")
