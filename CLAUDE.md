# CLAUDE.md

## General principles

- **Always fix pre-existing errors.** If you encounter failing tests, lint errors, or broken imports that existed before your change, fix them as part of your work. Do not dismiss them as "pre-existing" or "not related to my change."
- **Always reply to every PR review comment.** When addressing PR review feedback, you are NOT DONE until every single review comment has a reply on GitHub (via `add_reply_to_pull_request_comment`). Do not just fix the code — you must also post a reply to each comment explaining what you did or why no change is needed. Then resolve the threads if possible.
- **Always bump skill versions on any PR that modifies a skill.** Any PR that adds, removes, or changes files under `skills/<skill-name>/` MUST bump that skill's `metadata.version` in `skills/<skill-name>/SKILL.md` (patch bump by default; minor for new features; major for breaking changes). **Do not edit `plugins/cirra-ai-sf/skills/<skill-name>/SKILL.md` directly** — it is a generated mirror and `sync-plugins.yml` propagates the bump after merge. Do this on every skill the PR touches. The `publish-skill.yml` workflow is manual-only (`workflow_dispatch`) and does not run on PR merges, so it cannot be relied on to bump versions for routine PRs.

## Skill authoring — avoid these shipped-broken mistakes

These have broken published skills. Verify every one before pushing a skill change:

1. **`SKILL.md` `description` must be plain text — NO XML/HTML tags or angle brackets `<…>`.** The skill loader rejects a description containing `<…>` with the error "SKILL.md description cannot contain XML tags", and the downloads page then renders a blank description. Use `[…]` or `{…}` for placeholders in both `description` and `argument-hint` (e.g. `[article-url|topic-id]`), never `<…>`. Note: `scripts/validate-skills.sh` does NOT catch this today — check it by eye.
2. **Every new skill must be added to the top-level `README.md` skills table** (with a link to the skill's own `README.md`), and must ship a `skills/<skill-name>/README.md`. A skill missing from the README is effectively invisible to users.

(`AGENTS.md` carries the same authoring checklist for non-Claude agents — keep the two in sync.)

## Version bumping for PRs that modify skills

When a PR modifies one or more skills under `skills/`, before pushing:

1. For each modified skill, edit `skills/<skill-name>/SKILL.md` and bump `metadata.version` in the YAML frontmatter:
   - **Patch** (`2.0.2` → `2.0.3`) — bug fixes, validator improvements, documentation, new tests.
   - **Minor** (`2.0.2` → `2.1.0`) — new functionality, new workflows, new reference docs.
   - **Major** (`2.0.2` → `3.0.0`) — breaking changes to the public skill contract (renamed commands, removed features, incompatible input formats).
2. **Do not edit the plugin mirror** at `plugins/cirra-ai-sf/skills/<skill-name>/SKILL.md`. That tree is generated — the `sync-plugins.yml` workflow runs after merge to `main`, executes `scripts/sync-plugin-skills.sh`, and propagates the version bump (and any other source changes) into `plugins/` automatically. Direct edits will be overwritten and add noise to PR diffs.
3. Do **not** bump the top-level plugin version in `plugins/cirra-ai-sf/.claude-plugin/plugin.json` from a routine PR — that's owned by the manual `publish-skill.yml` / `publish-all.yml` workflows.

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
