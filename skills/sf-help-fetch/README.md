# sf-help-fetch

Read the body of a Salesforce Help article (`help.salesforce.com/s/articleView`) without a
browser. Those pages are a client-rendered Aura SPA, so a plain `curl`/`WebFetch` only returns
the "Loading…" shell — this skill fetches the real article text through Salesforce's own
anonymous Aura endpoint.

## Features

- **Both Help article kinds**, dispatched automatically by id shape:
  - `type=5` Help Docs topics (ids like `xcloud.remoteaccess_authenticate.htm`)
  - `type=1` numeric Knowledge Articles (ids like `005360285`)
- **One argument** — the article URL or id; no flags, retrieval strategy is fully automatic.
- **Self-maintaining** — scrapes the live `aura.context` and self-discovers the Salesforce
  release each run, so nothing is hardcoded.
- **Egress preflight** — if the host is unreachable, prompts to allowlist `*.salesforce.com`.
- **Clear out-of-scope messages** — Trailhead, Trailblazer Community, and
  `developer.salesforce.com` inputs return a pointer to the right approach instead of a vague
  error.
- **No dependencies** beyond `python3` and `curl`.

## Installation

For full installation instructions (various AI tools), see the [root README](../../README.md).

## Usage

Invoke the skill with a Salesforce Help article URL or a bare topic/article id:

```
/sf-help-fetch https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5
/sf-help-fetch xcloud.remoteaccess_authenticate
/sf-help-fetch https://help.salesforce.com/s/articleView?id=005360285&type=1
```

Or run the script directly:

```bash
python3 scripts/fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=005360285&type=1"
```

The readable article text is written to stdout; a one-line progress note goes to stderr.

See [SKILL.md](SKILL.md) for the full retrieval contract and design notes.
