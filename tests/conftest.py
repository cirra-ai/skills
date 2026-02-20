"""Shared test helpers for loading hook scripts by file path.

Hook scripts live in various plugin subdirectories and aren't packaged,
so we import them directly rather than adding every hooks/scripts dir to sys.path
(which would cause name collisions between the multiple mcp_validator.py files).
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def load_script(rel_path: str):
    """Load a Python script from a repo-relative path and return its module."""
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
