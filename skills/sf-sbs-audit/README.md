# sf-sbs-audit

A Claude Code skill for auditing Salesforce orgs against the
[Security Benchmark for Salesforce (SBS)](https://docs.securitybenchmark.org/),
a vendor-neutral compliance standard licensed CC BY-SA 4.0.

The skill is **opt-in**: it triggers only on explicit user requests (e.g.
"audit against SBS", "check SBS-OAUTH-001"). It is **read-only** and never
blocks or mutates anything.

See `SKILL.md` for the dispatch table and result-handling guidance, and
`CREDITS.md` for attribution.

## Companion server tool

This skill wraps the `sbs_audit` MCP tool in the Cirra AI cloud-app
(`src/functions/sfdc/sbs.js`). The MCP tool reads a vendored, CC BY-SA 4.0
subset of the SBS control dataset (only structured metadata — no upstream
prose) and dispatches per-control checks.

Initial coverage is intentionally zero — every control returns
`not_implemented`; check coverage grows in follow-up PRs to the cloud-app.
