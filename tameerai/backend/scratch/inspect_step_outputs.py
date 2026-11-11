import json

with open(r'C:\Users\muham\.gemini\antigravity\brain\85c7d051-a1b8-4814-8e24-56414fa9526c\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        step = obj.get('step_index')
        if step in range(16720, 16737):
            print(f"=== STEP {step} ({obj.get('type')}) ===")
            content = obj.get('content') or ''
            if len(content) > 300:
                print(content[:300] + "... [TRUNCATED]")
            else:
                print(content)

