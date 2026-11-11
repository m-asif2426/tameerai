import os
import sys
from pathlib import Path
import json

backend_dir = Path("D:/new idea project/tameerai/backend")
frontend_dir = Path("D:/new idea project/tameerai/frontend")

print("=== 1. Backend Structure Audit ===")
for root, dirs, files in os.walk(backend_dir / "app"):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
    rel = Path(root).relative_to(backend_dir)
    py_files = [f for f in files if f.endswith(".py")]
    if py_files:
        print(f"{rel}: {len(py_files)} files -> {py_files}")

print("\n=== 2. Frontend Structure Audit ===")
for root, dirs, files in os.walk(frontend_dir / "src"):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", ".next")]
    rel = Path(root).relative_to(frontend_dir)
    code_files = [f for f in files if f.endswith((".tsx", ".ts", ".jsx", ".js"))]
    if code_files:
        print(f"{rel}: {len(code_files)} files -> {code_files}")

print("\n=== 3. Backend Test Suite Audit ===")
test_files = sorted([f.name for f in (backend_dir / "tests").glob("test_*.py")])
print(f"Total test files in backend/tests: {len(test_files)}")
for tf in test_files:
    print(f"  {tf}")

