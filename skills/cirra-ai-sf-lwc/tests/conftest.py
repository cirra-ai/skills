"""Skill-local pytest helpers for cirra-ai-sf-lwc."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ROOT_CONFTEST = _REPO_ROOT / "tests" / "conftest.py"
_spec = importlib.util.spec_from_file_location("root_test_conftest", _ROOT_CONFTEST)
_module = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_module)

load_script = _module.load_script
