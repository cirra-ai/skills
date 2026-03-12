# Copilot Instructions

## Code review scope

- The `plugins/` directory contains **auto-generated mirror copies** of files from `skills/`.
- A post-merge CI workflow (`scripts/sync-plugin-skills.sh`) keeps them in sync.
- When reviewing PRs, **do not flag differences between `skills/` and `plugins/`**. Only review changes in `skills/`.

## Excluded paths

- `plugins/**`
