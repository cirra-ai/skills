# CLAUDE.md

## General principles

- **Always fix pre-existing errors.** If you encounter failing tests, lint errors, or broken imports that existed before your change, fix them as part of your work. Do not dismiss them as "pre-existing" or "not related to my change."
- **Always reply to EVERY Copilot/BugBot review comment.** When addressing PR feedback, add a reply to every single Copilot or BugBot review comment confirming the fix or explaining the action taken. Do not skip any.

## Always reply to PR review comments

When a reviewer (human or bot, including Copilot) leaves a review comment on a
PR, **always post a reply** explaining what was done — even when:

- the comment was addressed in a follow-up commit,
- the comment was rejected with reasoning,
- the comment is a non-actionable nit and just needs acknowledgement,
- I can't resolve the thread myself.

A code change alone is not a reply. Use
`mcp__github__add_reply_to_pull_request_comment` (with the original comment's
ID) for every thread, before considering the review handled. Batch replies for
the same review into a single tool-call message when possible.

If a comment doesn't need code changes, still reply briefly stating why (e.g.
"intentional — see X", "out of scope for this PR, tracked in #N").

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
