import os
import subprocess
import sys
from pathlib import Path

backend_dir = Path("D:/new idea project/tameerai/backend")
DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

env = os.environ.copy()
env["ISOLATED_POSTGRES_URL"] = DSN

print("Running complete backend test suite...")
cmd = [sys.executable, "-m", "pytest", "-v"]
res = subprocess.run(cmd, cwd=str(backend_dir), env=env)
sys.exit(res.returncode)

