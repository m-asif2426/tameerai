import importlib.util
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.db.base import Base


def test_alembic_config_load():
    """Verify that alembic.ini can be loaded and script directory found."""
    backend_root = Path(__file__).resolve().parent.parent
    ini_path = backend_root / "alembic.ini"
    assert ini_path.exists(), "alembic.ini must exist in backend root"

    config = Config(str(ini_path))
    script_dir = ScriptDirectory.from_config(config)
    assert script_dir is not None
    assert (backend_root / "alembic" / "versions").exists()


def test_alembic_target_metadata_configured():
    """Verify that alembic/env.py imports Base and configures target_metadata."""
    backend_root = Path(__file__).resolve().parent.parent
    env_path = backend_root / "alembic" / "env.py"
    assert env_path.exists(), "alembic/env.py must exist"

    # Read and inspect env.py source to ensure it wires Base.metadata
    content = env_path.read_text(encoding="utf-8")
    assert "from app.db.base import Base" in content
    assert "target_metadata = Base.metadata" in content
    assert Base.metadata is not None
