import json

with open(r'C:\Users\muham\.gemini\antigravity\brain\85c7d051-a1b8-4814-8e24-56414fa9526c\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '3803875e' in line:
            obj = json.loads(line)
            print(f"Line {idx}: step_index={obj.get('step_index')}, type={obj.get('type')}, source={obj.get('source')}")

