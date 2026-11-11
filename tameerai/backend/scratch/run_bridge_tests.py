import os
import sys

os.chdir(r"D:\new idea project\tameerai\backend")
sys.path.insert(0, r"D:\new idea project\tameerai\backend")

import pytest

if __name__ == "__main__":
    code = pytest.main(["tests/test_material_rate_ai_bridge.py", "-q"])
    sys.exit(code)
