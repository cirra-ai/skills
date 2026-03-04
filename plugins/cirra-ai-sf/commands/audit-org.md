---
name: audit-org
description: Run a comprehensive Salesforce org audit across Apex classes, triggers, Flows, Process Builders, Workflow Rules, LWC, custom objects, validation rules, Profiles, and Permission Sets. Generates Word, Excel, and HTML reports.
---

Use the `cirra-ai-sf-audit` skill to run a comprehensive Salesforce org audit.

The skill inventories and evaluates every major metadata category in the org:
Apex classes and triggers (scored via `cirra-ai-sf-apex`), Flows and Process
Builders (scored via `cirra-ai-sf-flow`), LWC components (scored via
`cirra-ai-sf-lwc`), custom objects and fields (scored via `cirra-ai-sf-metadata`),
validation rules, Workflow Rules, and Profiles and Permission Sets (audited via
`cirra-ai-sf-permissions`). Results are compiled into Word, Excel, and HTML reports.

Call `cirra_ai_init()` first if not already done this session.
