# CLAUDE.md

## General principles

- **Always fix pre-existing errors.** If you encounter failing tests, lint errors, or broken imports that existed before your change, fix them as part of your work. Do not dismiss them as "pre-existing" or "not related to my change."

## Setup

Before running tests, ensure Python dev dependencies from `requirements-dev.txt` are installed:

```sh
python3 -m pip install -r requirements-dev.txt
uv tool install pytest --with jsonschema   # alternative: adds pytest to PATH via uv
```

## Repository structure

- `skills/` — **Source of truth** for all skill code (scripts, assets, references, tests).
- `plugins/` — **Generated copies** of skills packaged for distribution. Do NOT edit files here directly; changes will be overwritten. Always edit in `skills/` and let the build step copy to `plugins/`.
- `tests/` — Repo-root test directory for cross-skill tests (conftest.py lives here).
- `skills/<skill-name>/tests/` — Skill-specific tests. These import `conftest.load_script()` from the repo root.

## Before every push

1. Run `npm run lint` and fix any issues (`npx prettier --write <files>` / `ruff check --fix .`)
2. Run `pytest tests/ -v` and `pytest skills/*/tests/ -v` and ensure all tests pass
