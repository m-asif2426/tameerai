"""
Runner to execute PostgreSQL 17 integration tests in pytest with isolated server running.
"""
import os
import subprocess
import sys
from pathlib import Path
import time
import asyncpg

PG_BIN = Path("D:/new idea project/tameerai/backend/pgsql/pgsql/bin")
PG_DATA = Path("D:/new idea project/tameerai/backend/pgdata17")
PG_PORT = 5433
PG_LOG = Path("D:/new idea project/tameerai/backend/pg17.log")
DSN = f"postgresql://postgres@127.0.0.1:{PG_PORT}/tameerai_isolated_test"

def main():
    pg_ctl = PG_BIN / "pg_ctl.exe"
    print(f"Starting PostgreSQL 17 on port {PG_PORT}...")
    subprocess.run([str(pg_ctl), "-D", str(PG_DATA), "-l", str(PG_LOG), "-o", f"-p {PG_PORT}", "start"], check=False)

    time.sleep(2)

    env = os.environ.copy()
    env["ISOLATED_POSTGRES_URL"] = DSN

    target_tests = [
        "tests/test_material_rate_models_and_schema.py",
        "tests/test_material_rate_immutability_and_security.py",
        "tests/test_material_rate_safety_hardening.py",
        "tests/test_material_rate_collection_engine.py",
        "tests/test_material_rate_adapters.py",
        "tests/test_material_rate_orchestration.py",
        "tests/test_material_rate_verification.py",
        "tests/test_material_rate_dealer_subsystem.py",
        "tests/test_material_rate_canonical_and_history.py",
        "tests/test_material_rate_apis.py",
    ]

    print(f"Running pytest against PostgreSQL 17 with ISOLATED_POSTGRES_URL={DSN}...")
    cmd = [sys.executable, "-m", "pytest", "-v"] + target_tests
    res = subprocess.run(cmd, cwd="D:/new idea project/tameerai/backend", env=env)
    
    print(f"Pytest exited with return code: {res.returncode}")

if __name__ == "__main__":
    main()
