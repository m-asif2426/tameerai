import os
import sys
import time

backend_dir = r"D:\new idea project\tameerai\backend"
cutoff = time.time() - (24 * 3600)  # last 24 hours

modified_files = []
for root, dirs, files in os.walk(backend_dir):
    # skip venv, .pytest_cache, __pycache__
    if any(p in root for p in ["venv", ".pytest_cache", "__pycache__", "pgdata17"]):
        continue
    for f in files:
        full_path = os.path.join(root, f)
        try:
            mtime = os.path.getmtime(full_path)
            if mtime > cutoff:
                rel = os.path.relpath(full_path, backend_dir)
                modified_files.append((rel, mtime))
        except Exception:
            pass

modified_files.sort(key=lambda x: x[1], reverse=True)
print(f"Files modified in the last 24h ({len(modified_files)}):")
for f, m in modified_files:
    print(f"  - {f}")

