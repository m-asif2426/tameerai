import json

with open(r"C:\Users\muham\.gemini\antigravity\brain\85c7d051-a1b8-4814-8e24-56414fa9526c\.system_generated\logs\transcript_full.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT" and "PHASE 03.1" in obj.get("content", ""):
            content = obj.get("content", "")
            with open("scratch/full_prompt10.txt", "w", encoding="utf-8") as out:
                out.write(content)
            print("Wrote full prompt 10 to scratch/full_prompt10.txt, length:", len(content))
            break

