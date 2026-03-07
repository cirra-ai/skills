"""Re-export load_script from the repo-root conftest for skill-local tests."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.parent
_ROOT_CONFTEST = REPO_ROOT / "tests" / "conftest.py"

_spec = importlib.util.spec_from_file_location("root_conftest", _ROOT_CONFTEST)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

load_script = _mod.load_script
