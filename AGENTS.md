# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, and others) working in this repo. Claude
Code also reads [CLAUDE.md](CLAUDE.md), which contains the full policy; keep the two in sync.

## Skill authoring — avoid these shipped-broken mistakes

These have broken published skills. Verify every one before pushing a skill change:

1. **`SKILL.md` `description` must be plain text — NO XML/HTML tags or angle brackets `<…>`.**
   The skill loader rejects a description containing `<…>` with the error "SKILL.md description
   cannot contain XML tags", and the downloads page then renders a blank description. Use `[…]`
   or `{…}` for placeholders in both `description` and `argument-hint` (e.g.
   `[article-url|topic-id]`), never `<…>`. Note: `scripts/validate-skills.sh` does NOT catch
   this today — check it by eye.
2. **Every new skill must be added to the top-level [`README.md`](README.md) skills table**
   (with a link to the skill's own `README.md`), and must ship a `skills/<skill-name>/README.md`.
   A skill missing from the README is effectively invisible to users.
3. **Bump `metadata.version`** in `skills/<skill-name>/SKILL.md` on any change to that skill.
4. **Do not edit `plugins/`** — it is generated from `skills/` by `sync-plugins.yml` after merge.

## Before every push

Run the gates and fix any issues:

- `npm run lint` (prettier `--check` + `ruff check`)
- `pytest tests/ skills/*/tests/`
- `bash scripts/validate-skills.sh`
