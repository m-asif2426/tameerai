import json

with open(r'C:\Users\muham\.gemini\antigravity\brain\85c7d051-a1b8-4814-8e24-56414fa9526c\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        content = data.get('content', '')
        if 'PHASE 03.1.3' in content and 'USER_INPUT' == data.get('type'):
            print(content)

