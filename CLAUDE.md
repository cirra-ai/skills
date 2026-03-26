# CLAUDE.md

## Repository structure

- `skills/` — **Source of truth** for all skill code (scripts, assets, references, tests).
- `plugins/` — **Generated copies** of skills packaged for distribution. Do NOT edit files here directly; changes will be overwritten. Always edit in `skills/` and let the build step copy to `plugins/`.
- `tests/` — Repo-root test directory for cross-skill tests (conftest.py lives here).
- `skills/<skill-name>/tests/` — Skill-specific tests. These import `conftest.load_script()` from the repo root.

## Important: Environment awareness

- This repo is developed on macOS. The Claude Code web/cloud environment is a sandboxed Linux VM — it does NOT have access to the user's full local filesystem.
- **Never claim local files or settings don't exist** just because they aren't visible from the sandbox. Say "I cannot see/access XYZ from this environment" instead.
- Key paths on the user's Mac that you cannot access from here:
  - `~/Library/Application Support/Claude/` — Claude desktop app data, including cached plugin skills under `local-agent-mode-sessions/skills-plugin/`
  - `~/Library/Application Support/Claude/` settings and session data
- The user may reference paths, UI states, or behaviors from their local machine or Claude Cowork. Always answer from **their perspective**, not the sandbox's.

## Before every push

1. Run `npm run lint` and fix any issues (`npx prettier --write <files>` / `ruff check --fix .`)
2. Run `pytest tests/ -v` and `pytest skills/*/tests/ -v` and ensure all tests pass
