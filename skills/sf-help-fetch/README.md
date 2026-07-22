# sf-help-fetch

Read the full text of a Salesforce documentation page — both Salesforce Help
(`help.salesforce.com`) and the developer docs (`developer.salesforce.com`) — without a
browser. These pages render their content with JavaScript, so a plain `curl`/`WebFetch` only
returns the "Loading…" shell; this skill pulls the real article body through Salesforce's own
anonymous content APIs, picking the right one by host.

## Features

- **Both doc surfaces**, routed automatically by host:
  - `help.salesforce.com/s/articleView` — via the anonymous Aura endpoint, covering both
    `type=5` Help Docs topics (ids like `xcloud.remoteaccess_authenticate.htm`) and `type=1`
    numeric Knowledge Articles (ids like `005360285`).
  - `developer.salesforce.com/docs/...` — via the anonymous "Atlas" JSON content API.
- **One argument** — the page URL (or a bare Help topic id); no flags, retrieval is fully
  automatic.
- **Self-maintaining** — scrapes the live `aura.context` and self-discovers the Salesforce
  release each run (Help), and reads the deliverable version from the manifest (dev docs), so
  nothing is hardcoded.
- **Egress preflight** — if the host is unreachable, prompts to allowlist `*.salesforce.com`.
- **Clear out-of-scope messages** — Trailhead and Trailblazer Community inputs return a pointer
  to the right approach instead of a vague error.
- **No dependencies** beyond `python3` and `curl`.

## Installation

For full installation instructions (various AI tools), see the [root README](../../README.md).

## Usage

Invoke the skill with a Salesforce Help / developer-docs URL or a bare Help topic/article id:

```
/sf-help-fetch https://help.salesforce.com/s/articleView?id=xcloud.remoteaccess_authenticate.htm&type=5
/sf-help-fetch xcloud.remoteaccess_authenticate
/sf-help-fetch https://help.salesforce.com/s/articleView?id=005360285&type=1
/sf-help-fetch https://developer.salesforce.com/docs/atlas.en-us.uiapi.meta/uiapi/ui_api_features_list_views.htm
```

Or run the script directly:

```bash
python3 scripts/fetch_sf_help.py "https://help.salesforce.com/s/articleView?id=005360285&type=1"
```

The readable article text is written to stdout; a one-line progress note goes to stderr.

See [SKILL.md](SKILL.md) for the full retrieval contract and design notes.
