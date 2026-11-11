"""
Runs the complete backend test suite with PostgreSQL 17 isolated URL active.
"""
import os
import subprocess
import sys
from pathlib import Path
import time

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_PORT = 5433
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
DSN = f"postgresql://postgres@127.0.0.1:{PG_PORT}/tameerai_isolated_test"

def main():
    pg_ctl = PG_BIN / "pg_ctl.exe"
    subprocess.run([str(pg_ctl), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", f"-p {PG_PORT}", "start"], check=False)
    time.sleep(2)

    env = os.environ.copy()
    env["ISOLATED_POSTGRES_URL"] = DSN

    print("Launching full regression test suite (pytest -q)...")
    res = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd="D:/new idea project/tameerai/backend", env=env)
    print(f"\nFinal Exit Code: {res.returncode}")

if __name__ == "__main__":
    main()

