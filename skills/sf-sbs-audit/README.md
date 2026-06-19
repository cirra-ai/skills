# sf-sbs-audit

A Claude Code skill for auditing Salesforce orgs against the
[Security Benchmark for Salesforce (SBS)](https://docs.securitybenchmark.org/),
a vendor-neutral compliance standard licensed CC BY-SA 4.0.

## Architecture: skills-only

This skill is self-contained. It reads its own vendored control dataset
(`references/sbs/controls.json`) and orchestrates per-control checks by
calling **existing** Cirra AI MCP tools (`sobject_describe`,
`tooling_api_query`, `profile_describe`, `metadata_read`, etc.) — no
dedicated server-side tool is required.

The skill is **opt-in**: it triggers only on explicit user requests
("audit against SBS", "check SBS-OAUTH-001"). It is **read-only** and
never blocks or mutates anything.

## Layout

- `SKILL.md` — dispatch table, check rubric, response shape, attribution rules
- `references/sbs/controls.json` — vendored SBS dataset (54 controls), CC BY-SA 4.0
- `references/sbs/{LICENSE,NOTICE,SBS_VERSION,ATTRIBUTION.txt}` — license + attribution
- `scripts/fetch_sbs.py` — regenerates the dataset from the upstream repo at a pinned commit
- `tests/` — pytest suite

Initial coverage is intentionally zero — every control returns
`not_implemented`. Each follow-up PR adds one row to the Check rubric in
`SKILL.md`, naming the existing MCP tool(s) and the pass/fail criterion.

## Refreshing the dataset

```bash
python3 skills/sf-sbs-audit/scripts/fetch_sbs.py --latest
```

A weekly GitHub Actions workflow runs the same command and opens a draft
PR if upstream has moved.

## License posture

- The skill itself is MIT-licensed (`LICENSE`)
- The benchmark standard is CC BY-SA 4.0 — see `CREDITS.md` and
  `references/sbs/LICENSE`
- Attribution is rendered into every audit response via the verbatim
  inclusion of `references/sbs/ATTRIBUTION.txt`, per `SKILL.md`'s
  "Bulletproof attribution" rules
