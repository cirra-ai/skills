# Copilot Instructions

## Code review guidance

- `skills/` is the source of truth.
- `plugins/` contains **auto-generated mirror copies** of content from `skills/`.
- A post-merge CI workflow (`scripts/sync-plugin-skills.sh`) keeps `plugins/` in sync.
- In PR review, **do not request changes solely to make `plugins/` match `skills/`**. Review and request changes in `skills/` instead.
- If `plugins/` appears unexpectedly out of sync, flag the sync workflow/script rather than editing `plugins/` by hand.
