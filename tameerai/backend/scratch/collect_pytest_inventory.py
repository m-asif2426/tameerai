import os
import sys
import subprocess
import json

backend_dir = r"D:\new idea project\tameerai\backend"
python_exe = r"D:\new idea project\tameerai\backend\venv\Scripts\python.exe"

# Run pytest --collect-only -q
res = subprocess.run(
    [python_exe, "-m", "pytest", "--collect-only", "-q"],
    cwd=backend_dir,
    capture_output=True,
    text=True
)

lines = res.stdout.strip().split("\n")
module_counts = {}
for line in lines:
    if "::" in line:
        mod = line.split("::")[0].replace("\\", "/")
        module_counts[mod] = module_counts.get(mod, 0) + 1

print(f"Total modules: {len(module_counts)}")
total_tests = 0
for mod in sorted(module_counts.keys()):
    cnt = module_counts[mod]
    total_tests += cnt
    print(f"{mod:55}: {cnt}")

print("-" * 65)
print(f"GRAND TOTAL COLLECTED TESTS: {total_tests}")

with open(r"D:\new idea project\tameerai\backend\scratch\pytest_inventory.json", "w") as f:
    json.dump({"modules": module_counts, "total": total_tests}, f, indent=2)

