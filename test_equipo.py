import sys
from pathlib import Path

try:
    import modules.equipo
    print("SUCCESS: Modules imported cleanly.")
except Exception as e:
    import traceback
    traceback.print_exc()
