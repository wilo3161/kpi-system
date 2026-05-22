import json
import os

log_path = r"C:\Users\wilso\.gemini\antigravity\brain\4df29d22-188b-4eff-ba6c-1b93036a5c73\.system_generated\logs\transcript.jsonl"
out_path = r"c:\Users\wilso\Downloads\kpi-system-main\scratch\search_all_logs.txt"

if os.path.exists(log_path):
    print("Found transcript.jsonl")
    with open(log_path, "r", encoding="utf-8") as f:
        with open(out_path, "w", encoding="utf-8") as out:
            for line in f:
                try:
                    data = json.loads(line)
                    # We look for planner responses or anything
                    content = data.get("content", "")
                    # Also look inside tool calls, planner responses, etc.
                    for keyword in ["sap", "mejora", "guias", "recepcion", "logistica", "alerta"]:
                        if keyword in content.lower():
                            out.write(f"Step {data.get('step_index')} ({data.get('type')}): {content[:300].replace('\n', ' ')}...\n")
                            break
                except Exception as e:
                    pass
    print("Saved results to", out_path)
else:
    print("Log not found")
