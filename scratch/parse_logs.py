import json
import os

log_path = r"C:\Users\wilso\.gemini\antigravity\brain\4df29d22-188b-4eff-ba6c-1b93036a5c73\.system_generated\logs\transcript.jsonl"

if os.path.exists(log_path):
    print("Found transcript.jsonl")
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                # Check tool calls
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        if tc.get("name") == "run_command":
                            print(f"Step {data.get('step_index')}: {tc.get('args')}")
            except Exception as e:
                pass
else:
    print("transcript.jsonl not found at", log_path)
