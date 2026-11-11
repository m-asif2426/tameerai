import os
import subprocess
import sys
from pathlib import Path

backend_dir = Path("D:/new idea project/tameerai/backend")
DSN = "postgresql://postgres@127.0.0.1:5433/tameerai_isolated_test"

env = os.environ.copy()
env["ISOLATED_POSTGRES_URL"] = DSN

targets = [
    "tests/test_material_rate_adapters.py::test_pg17_adapters_live_persistence",
    "tests/test_material_rate_adapters.py::test_pg17_real_extracted_records_persistence",
    "tests/test_material_rate_collection_engine.py::TestPostgreSqlCollectionIntegration::test_15_pg17_collection_run_append_only_and_deduplication",
    "tests/test_material_rate_safety_hardening.py::TestPostgreSqlSafetyHardeningIntegration::test_09_statement_level_truncate_trigger_blocks_truncate",
    "tests/test_material_rate_safety_hardening.py::TestPostgreSqlSafetyHardeningIntegration::test_10_statement_level_truncate_trigger_blocks_truncate_cascade",
]

print(f"Executing pytest for PostgreSQL 17 test nodes with ISOLATED_POSTGRES_URL={DSN}...")
cmd = [sys.executable, "-m", "pytest", "-v"] + targets
res = subprocess.run(cmd, cwd=str(backend_dir), env=env)
sys.exit(res.returncode)

