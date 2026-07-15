# Credits

This skill was created by [Cirra AI](https://github.com/cirra-ai) (2026).

## Upstream standard

The skill audits against the
[**Security Benchmark for Salesforce (SBS)**](https://docs.securitybenchmark.org/),
a vendor-neutral compliance standard for Salesforce security posture.

- Source: https://github.com/Salesforce-Security-Benchmark/docs-site
- License: [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)

SBS is a community standard. This skill does not redistribute SBS control
prose, audit procedures, or remediation language — it links to the
upstream documentation instead. The structured control metadata (IDs,
risk levels, remediation scopes) that powers the dispatch table is
redistributed under CC BY-SA 4.0 in `references/sbs/`, with attribution
per the license.

The canonical attribution block in `references/sbs/ATTRIBUTION.txt` is
the source of truth that `SKILL.md` requires the LLM to render verbatim
at the end of every audit response. This is the skill's
license-compliance guardrail.

Per the SBS project's community naming guidance, this skill uses the SBS
name nominatively ("audit against SBS") and does not present itself as a
fork or modified version of SBS.

## Skill license

This skill (`SKILL.md`, `README.md`, `scripts/`, `tests/`) is licensed
under the MIT License — see `LICENSE`. The MIT license applies only to
the skill's own code and prose; the vendored SBS data subset in
`references/sbs/` is governed by CC BY-SA 4.0.
