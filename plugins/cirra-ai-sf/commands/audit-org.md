---
name: audit-org
description: Run a full Salesforce org audit across Apex, Flows, LWC, Permissions, and Metadata. Scores components against quality rubrics, audits the permission model, evaluates the data model, and generates Word, Excel, and HTML reports.
---

Use the `cirra-ai-sf-audit` skill to run a complete Salesforce org audit.

The skill scores every Apex class, active Flow, and LWC component using the
rubrics from `cirra-ai-sf-apex`, `cirra-ai-sf-flow`, and `cirra-ai-sf-lwc`.
It audits the permission model using `cirra-ai-sf-permissions` to find
overly broad permissions, orphaned Permission Sets, and outdated Permission
Set Groups. It evaluates custom objects against the metadata rubric from
`cirra-ai-sf-metadata`. Results are compiled into Word, Excel, and HTML reports.

Call `cirra_ai_init()` first if not already done this session.
