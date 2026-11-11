import json

with open(r"C:\Users\muham\.gemini\antigravity\brain\85c7d051-a1b8-4814-8e24-56414fa9526c\.system_generated\logs\transcript.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT" and "PHASE 03.1" in obj.get("content", ""):
            lines = obj.get("content", "").split("\n")
            for i, l in enumerate(lines):
                if 40 <= i <= 240:
                    print(f"{i}: {l}")
            break
