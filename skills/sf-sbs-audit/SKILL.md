---
name: sf-sbs-audit
plugin: cirra-ai-sf
argument-hint: '[control SBS-XXX-NNN|category ACS|AUTH|...|risk Critical|High|Moderate|all] ...'
metadata:
  version: 2.0.1
description: >
  Audit a Salesforce org against the Security Benchmark for Salesforce (SBS), a
  vendor-neutral compliance standard for Salesforce security posture
  (https://docs.securitybenchmark.org/, CC BY-SA 4.0). Read-only, opt-in: invoke
  ONLY when the user explicitly asks for an SBS audit, SBS compliance check, or
  asks a question that clearly maps to one or more SBS controls. The skill reads
  its own vendored control dataset and orchestrates per-control checks by
  calling existing Cirra AI MCP tools (sobject_describe, tooling_api_query,
  profile_describe, metadata_read, etc.). No dedicated server tool required.
  Usage: /sf-sbs-audit [control SBS-XXX-NNN|category ACS|AUTH|...|risk Critical|High|Moderate|all] ...
---

# Security Benchmark for Salesforce (SBS) Audit

Run a read-only audit of a Salesforce org against the
[Security Benchmark for Salesforce (SBS)](https://docs.securitybenchmark.org/) —
a vendor-neutral compliance standard for Salesforce security, licensed
CC BY-SA 4.0. The skill reads its own vendored dataset
(`references/sbs/controls.json`) and orchestrates checks via existing Cirra AI
MCP tools.

**When to use this skill** — only when the user explicitly asks for an SBS
audit ("audit against SBS", "is this org SBS-compliant?", "check SBS-AUTH-001",
"sweep all Critical SBS controls"). **Do not** invoke as a side effect of
routine metadata work, prototyping, or legacy artifact management. SBS auditing
is opt-in by design.

**What this skill is not** — it is not an enforcement layer. The audit never
blocks, modifies, or mutates anything. It reports findings; remediation is the
user's call.

## Step 1: Dispatch

Parse `$ARGUMENTS` to determine the audit scope:

| First argument or intent                               | Selection                                       |
| ------------------------------------------------------ | ----------------------------------------------- |
| `control SBS-XXX-NNN` or a bare `SBS-XXX-NNN` ID       | The single control with that ID                 |
| `category <code>` or one of `ACS`/`AUTH`/.../`SECCONF` | Every control whose `category` matches          |
| `risk Critical`/`High`/`Moderate`                      | Every control whose `risk_level` matches        |
| `all` or no argument                                   | Every control in `references/sbs/controls.json` |

Filters compose. `category OAUTH risk Critical` selects every control where
`category == "OAUTH"` AND `risk_level == "Critical"`.

When the intent is missing or unclear, **use `AskUserQuestion`** before
running:

```
AskUserQuestion(question="What scope should I audit?\n\n1. **One control** — SBS-XXX-NNN\n2. **A category** — Access Controls, Authentication, OAuth, etc.\n3. **A risk band** — Critical / High / Moderate only\n4. **Everything** — sweep every control in the benchmark")
```

## Step 2: Load the dataset

Read `references/sbs/controls.json`. It contains:

- `_license` — attribution metadata (SBS source, upstream commit, CC BY-SA 4.0 URI). Surface this as part of your audit response.
- `schema_version` — bump-on-breaking-change indicator
- `controls[]` — array of `{ control_id, category, category_name, risk_level, remediation: { scope, entity_type? }, doc_url, task? }`

Apply the dispatch filter from Step 1 to produce the selected control set.

## Step 3: Evaluate each selected control

Consult the **Check rubric** below. If the rubric has no entry for the
control, report `status: "not_implemented"` with the upstream `doc_url`. If
the rubric has an entry, follow it exactly — call the named Cirra AI MCP
tools with the named arguments, then apply the named pass/fail criterion.

### Check rubric

| control_id  | Status            | How to evaluate                             |
| ----------- | ----------------- | ------------------------------------------- |
| _(default)_ | `not_implemented` | Link `doc_url`. Do not attempt to evaluate. |

Initial coverage is intentionally zero. Every control returns
`not_implemented` until a follow-up PR adds a rubric row above. Each new
row identifies (1) which Cirra AI MCP tool(s) to call, (2) what to extract
from the response, (3) the pass/fail criterion, and (4) what to put in
`findings` on failure.

## Step 4: Render the response

Emit a structured summary as JSON inside a fenced block, followed by a
prose summary. The JSON shape:

```json
{
  "selected": <count>,
  "counts": { "pass": <n>, "fail": <n>, "not_implemented": <n> },
  "coverage": { "controls_total": <total in dataset>, "checks_implemented": <rubric rows above> },
  "results": [
    {
      "control_id": "SBS-...",
      "category": "...",
      "risk_level": "...",
      "status": "pass|fail|not_implemented",
      "doc_url": "https://docs.securitybenchmark.org/...",
      "findings": [...]
    }
  ]
}
```

### Reporting rules

1. **Headline**: one line — how many `fail` / `pass` / `not_implemented` out
   of `selected`, plus a reminder that `not_implemented` means "the rubric
   does not yet cover this control" — not "this is fine".
2. **List `fail` first**, sorted Critical → High → Moderate, with `doc_url`
   so the user can read the upstream audit procedure and remediation.
3. **Group `not_implemented` by category** in a single short list — do not
   reproduce each entry in detail.
4. **Append the verbatim attribution block at the very end.** See "Bulletproof
   attribution" below.

## Bulletproof attribution (CC BY-SA 4.0 — non-negotiable)

CC BY-SA 4.0 obligates this skill to credit SBS, link the license, and
indicate modifications on every response that derives from the dataset.

**MUST**: at the end of every audit response, include the **verbatim**
contents of `references/sbs/ATTRIBUTION.txt`. Do not paraphrase. Do not
summarize. Do not omit. Do not move it to the top. Do not abbreviate the
URL. If the user asks for "just the findings", still include the
attribution block — it is a license requirement, not a stylistic choice.

```
<<< include the exact bytes of references/sbs/ATTRIBUTION.txt here >>>
```

The file is single source of truth and is regenerated by
`scripts/fetch_sbs.py` whenever the dataset is refreshed.

## What NOT to do

- **Do not paraphrase, summarize, or quote SBS control descriptions, audit
  procedures, or remediation language.** The benchmark prose is CC BY-SA 4.0
  and lives upstream. Link to `doc_url` for the details.
- **Do not invent control IDs.** If the user names a control that does not
  appear in `references/sbs/controls.json`, report it as unknown (do not
  fabricate findings).
- **Do not edit the vendored files in `references/sbs/`.** They are
  CC BY-SA 4.0 and are regenerated by `scripts/fetch_sbs.py`. Submit
  upstream PRs at the source repo if the standard itself needs to change.
- **Do not enforce or block other operations** based on findings. This skill
  reports; it does not gate.
- **Do not skip the attribution block.** See "Bulletproof attribution" above.

## How to add a new check (for contributors)

A new check is a single new row in the Check rubric table above. Each row
must specify:

1. **Tool calls** — exact MCP tool name(s) and arguments (e.g.
   `tooling_api_query` with `q: "SELECT Id, Name FROM ConnectedApplication"`)
2. **Extraction** — what field(s) to read out of the response
3. **Criterion** — the explicit boolean condition that decides pass vs fail
4. **Findings shape** — what entities/values to put in `findings` on fail

Follow-up PRs add one row at a time, each with its own test fixture under
`tests/fixtures/`.
