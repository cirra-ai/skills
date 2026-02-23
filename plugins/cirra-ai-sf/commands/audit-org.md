---
name: audit-org
description: Run a full Salesforce org audit across Apex, Flows, and LWC. Scores all components against quality rubrics and generates Word, Excel, and HTML reports.
---

Use the `cirra-ai-sf-audit` skill to run a complete Salesforce org audit.

The skill scores every Apex class, active Flow, and LWC component using the
rubrics from `cirra-ai-sf-apex`, `cirra-ai-sf-flow`, and `cirra-ai-sf-lwc`,
then generates Word, Excel, and HTML reports.

Call `cirra_ai_init()` first if not already done this session.
