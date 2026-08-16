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
5. **Never write a bare `Object__c` / `Field__c` / `__r` / `__mdt` in Markdown prose or tables.**
   A pair of `__` is Markdown strong-emphasis, so `prettier --write` (which every push runs)
   rewrites `Amount__c to Invoice__c` into `Amount**c to Invoice**c` — the API name is now
   wrong and renders as bold. This is silent: prettier reports the file as merely reformatted,
   and it has already shipped broken API names in published docs more than once. Write API
   names one of two ways:
   - **Preferred: wrap in backticks** — `` `Invoice__c` ``. Emphasis does not apply inside a
     code span, so prettier leaves it alone and it renders as code, which is what an API name
     should look like anyway.
   - **Plain text: escape both pairs** — `Invoice\_\_c`, matching the existing tables.

   After editing, re-run `npx prettier --write <files>` and confirm nothing turned into `**`.
   To sweep the whole repo — expect hits only in `plugins/` (regenerated from `skills/` after
   merge), deliberate acronym bolding like `**S**ingle Responsibility` in `skills/sf-apex/`,
   and the counter-example quoted above:

   ```sh
   git ls-files -z | xargs -0 grep -nE '\*\*(c|r|mdt|x|e|b|kav|Share|History|Feed|Tag|ChangeEvent)\b'
   ```

## Before every push

Run the gates and fix any issues:

- `npm run lint` (prettier `--check` + `ruff check`)
- `pytest tests/ skills/*/tests/`
- `bash scripts/validate-skills.sh`
