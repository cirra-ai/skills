# Cirra AI Salesforce Skills — Downloads

AI skills for Salesforce development in Claude Code and Claude Cowork, powered by the Cirra AI MCP Server.

> **Not sure what to download?** Grab the [All-in-One Plugin Bundle](#all-in-one-plugin-bundle) — it installs all four skills at once.

---

## Plugin Packages (Recommended)

Full packages with skills, commands, hooks, templates, and MCP server configuration.

### All-in-One Plugin Bundle

**[⬇ Download cirra-ai-sf-skills.zip](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-skills.zip)**

All four Salesforce plugins in one zip — Apex, Flow, Data, and the Orchestrator.

---

### Individual Plugins

| Plugin | Description | Download |
|--------|-------------|----------|
| **cirra-ai-sf-apex** v2.0 | Apex code generation & review — 150-point scoring, TAF patterns, test generation | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-apex.zip) |
| **cirra-ai-sf-flow** v2.1 | Flow creation & validation — 110-point scoring, Winter '26 best practices | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-flow.zip) |
| **cirra-ai-sf-data** v3.0 | Data operations expert — SOQL, bulk ops, test data, 130-point scoring | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-data.zip) |
| **cirra-ai-sf** v1.0 | Orchestrator — routes requests to the right specialist plugin | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf.zip) |

---

## Skill-Only Files (Lightweight)

Just the `SKILL.md` instruction file, plus `LICENSE` and `CREDITS.md`. Use these if you only
want the AI instructions without hooks, commands, or templates.

| Skill | Description | Download |
|-------|-------------|----------|
| **cirra-ai-sf-apex** skill | Apex generation instructions, guardrails, scoring rubric | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-apex-skill.zip) |
| **cirra-ai-sf-flow** skill | Flow creation instructions, decision matrix, best practices | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-flow-skill.zip) |
| **cirra-ai-sf-data** skill | Data operations instructions, SOQL patterns, MCP tool mapping | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-data-skill.zip) |
| **cirra-ai-sf** skill | Orchestrator instructions | [⬇ Download](https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-skill.zip) |

---

## How to Install

### Claude Cowork (browser)

1. Download a plugin zip above
2. Open Claude Cowork → **Plugins** in the left sidebar
3. Click **Upload Plugin** and select the downloaded zip
4. The plugin activates immediately in your current session

### Claude Code (CLI)

```bash
# Install a downloaded zip
/plugin install path/to/cirra-ai-sf-apex.zip

# Or install from the marketplace directly
/plugin marketplace add cirra-ai/skills
/plugin install cirra-ai-sf-apex@cirra-ai
```

### Skill-Only Files

1. Download a skill zip and extract it
2. Place `SKILL.md` in your project's `.claude/skills/` directory
3. Claude will pick up the skill automatically in that project

---

## Requirements

- Claude Code or Claude Cowork with plugin support
- [Cirra AI MCP Server](https://cirra.ai) — connects Claude to your Salesforce org
- Target Salesforce org

---

## All Releases

See [GitHub Releases](https://github.com/cirra-ai/skills/releases) for version history and changelogs.

---

© 2026 [Cirra AI, Inc.](https://cirra.ai) — [MIT License](https://github.com/cirra-ai/skills/blob/main/LICENSE)
