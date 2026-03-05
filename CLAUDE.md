# CLAUDE.md

## Repository structure

- `skills/` — **Source of truth** for all skill code (scripts, assets, references, tests).
- `plugins/` — **Generated copies** of skills packaged for distribution. Do NOT edit files here directly; changes will be overwritten. Always edit in `skills/` and let the build step copy to `plugins/`.
- `tests/` — Repo-root test directory for cross-skill tests (conftest.py lives here).
- `skills/<skill-name>/tests/` — Skill-specific tests. These import `conftest.load_script()` from the repo root.

## Before every push

1. Run `npm run lint` and fix any issues (`npx prettier --write <files>` / `ruff check --fix .`)
2. Run `pytest tests/ -v` and `pytest skills/*/tests/ -v` and ensure all tests pass
