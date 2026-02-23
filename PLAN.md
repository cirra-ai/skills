# Plan: Codex Audit Parity via Shared Content + Codex-Specific Skill

## Problem

The `audit-org` command works well in Claude Cowork/Code because it is a **command** (`.claude-plugin/commands/audit-org.md`) — a concept that only exists in the Claude plugin system. OpenAI Codex has no equivalent of commands; it only understands **skills** (SKILL.md files) and **agents** (openai.yaml). When a Codex user says "audit my salesforce org", none of the four existing skills trigger because none of them contain audit orchestration logic.

## Current Architecture

```
cirra-ai-sf/
├── .claude-plugin/plugin.json    ← Claude-only plugin manifest
├── commands/                     ← Claude-only slash commands
│   ├── audit-org.md              ← THE audit command (Claude only)
│   ├── validate-apex.md
│   ├── validate-flow.md
│   ├── validate-lwc.md
│   ├── create-*.md
│   ├── update-*.md
│   └── ...
├── skills/
│   ├── cirra-ai-sf-apex/
│   │   ├── SKILL.md              ← Large (~740 lines) - Apex generation + review
│   │   └── agents/openai.yaml   ← Codex agent config (just UI metadata)
│   ├── cirra-ai-sf-flow/
│   │   ├── SKILL.md              ← Large (~770 lines) - Flow generation + review
│   │   └── agents/openai.yaml
│   ├── cirra-ai-sf-data/
│   │   ├── SKILL.md              ← (~615 lines) - SOQL/DML operations
│   │   └── agents/openai.yaml
│   └── cirra-ai-sf-lwc/
│       ├── SKILL.md              ← Large (~740 lines) - LWC development
│       └── agents/openai.yaml
└── hooks/hooks.json              ← Claude-only PreToolUse hooks
```

**Key observation**: The `audit-org.md` command is ~115 lines of orchestration logic that references the scoring rubrics already defined in the three SKILL.md files. It doesn't define its own rubrics — it says "use the rubrics from the cirra-ai-sf-apex, cirra-ai-sf-flow, and cirra-ai-sf-lwc skills."

## Proposed Solution

### Strategy: Shared audit content + a new audit skill for Codex

Rather than duplicating the full audit-org.md content into each skill, create:

1. **A shared content file** (`cirra-ai-sf/shared/audit-phases.md`) containing the platform-agnostic audit workflow (phases 1-6)
2. **A new audit skill** (`cirra-ai-sf/skills/cirra-ai-sf-audit/`) that Codex can install and use
3. **Update the existing `audit-org.md` command** to include/reference the shared content instead of its own copy

This keeps a single source of truth for the audit logic while making it available on both platforms.

### File Changes

#### 1. Create shared audit content

**New file**: `cirra-ai-sf/shared/audit-phases.md`

Extract the platform-agnostic audit phases (1-6) from the current `audit-org.md` into this shared file. This is the reusable core — the phases for counting, collecting, scoring, and reporting across Apex, Flows, and LWC.

Content: The 6 phases from the current `audit-org.md` (phases 1-6), the routing reference table, and the build order section. Essentially everything after the Prerequisites section and before any platform-specific framing.

#### 2. Create the new audit skill

**New directory**: `cirra-ai-sf/skills/cirra-ai-sf-audit/`

```
cirra-ai-sf/skills/cirra-ai-sf-audit/
├── SKILL.md           ← Skill definition with audit orchestration
├── README.md          ← Brief description
├── CREDITS.md         ← Attribution
└── agents/
    └── openai.yaml    ← Codex agent interface config
```

**`SKILL.md`** contents:
- Frontmatter: name, description (triggers on "audit", "org audit", "review org", "score org" etc.)
- Brief intro explaining this is the org-wide audit orchestrator
- **Inline the shared audit phases** (the build system already processes SKILL.md at package time, so we can't use dynamic includes — just maintain the same content in both places, or better yet, have the `package-skills.sh` script assemble it)
- Scoring section that references the rubrics: "Score Apex using the 150-point rubric from cirra-ai-sf-apex, Flows using the 110-point rubric from cirra-ai-sf-flow, and LWC using the 165-point rubric from cirra-ai-sf-lwc"
- Cross-skill routing table
- Dependencies section listing the MCP tools needed

**`agents/openai.yaml`** contents:
```yaml
interface:
  display_name: "Cirra AI Salesforce Audit"
  short_description: "Run a full Salesforce org audit across Apex, Flows, and LWC"
  icon_small: "./assets/icon-small.png"
  icon_large: "./assets/icon-large.png"
  brand_color: "#4068EB"
  default_prompt: "Use $cirra-ai-sf-audit to audit a Salesforce org."
```

#### 3. Refactor `audit-org.md` to reference shared content

**Modified file**: `cirra-ai-sf/commands/audit-org.md`

Replace the inline phases with a brief note and then include/paste the shared content. Since Claude commands are markdown files loaded at runtime, we have two sub-options:

- **Option A (simpler)**: Keep `audit-org.md` as-is. Accept that the audit phases exist in two places (`audit-org.md` and `SKILL.md`), but factor the phases into `shared/audit-phases.md` and have the packaging script assemble both targets from the shared source.
- **Option B (simplest, recommended)**: Keep `audit-org.md` as-is and build the new `cirra-ai-sf-audit/SKILL.md` to contain the same audit workflow content, adapted for a skill context (no `/` command references, skill-appropriate framing). Accept that there are two "copies" but they serve different platforms and may drift slightly — which is fine since the core logic (phases, scoring thresholds, report formats) is the same.

**Recommendation: Option B.** The audit-org.md is only 115 lines, and the skill version needs different framing anyway (skills have frontmatter, different intro paragraphs, dependency declarations). Trying to share content via build scripts adds complexity without much benefit for such a small file. If/when the audit logic grows, we can revisit.

#### 4. Update packaging and validation

**Modified file**: `scripts/validate-skills.sh`

Add `cirra-ai-sf-audit` to the expected skills list if it uses one. The script auto-discovers skills via `*/skills/*/SKILL.md` glob, so no changes should be needed.

**Modified file**: `.claude-plugin/marketplace.json` — no changes needed (this lists plugins, not individual skills).

**Modified file**: `cirra-ai-sf/.claude-plugin/plugin.json` — no changes needed (the `"skills": "./skills"` path already picks up all subdirectories).

#### 5. Update README

**Modified file**: `README.md`

Add the new audit skill to the skills table:

```markdown
| [cirra-ai-sf-audit](cirra-ai-sf/skills/cirra-ai-sf-audit/README.md) | Full org audit across Apex, Flows, and LWC with scored reports |
```

## Summary of Changes

| File | Action | Purpose |
|------|--------|---------|
| `cirra-ai-sf/skills/cirra-ai-sf-audit/SKILL.md` | Create | Audit skill for Codex (and any skill-based client) |
| `cirra-ai-sf/skills/cirra-ai-sf-audit/README.md` | Create | Skill documentation |
| `cirra-ai-sf/skills/cirra-ai-sf-audit/CREDITS.md` | Create | Attribution |
| `cirra-ai-sf/skills/cirra-ai-sf-audit/agents/openai.yaml` | Create | Codex agent UI config |
| `README.md` | Modify | Add audit skill to table |

No changes to existing commands or skills — zero risk of breaking what already works.

## Open Questions

1. **Should the audit skill depend on the other three skills being installed?** In Codex, skills are loaded independently. The audit skill should reference the rubrics inline (summarized) so it works standalone, but note that the domain-specific skills provide deeper guidance for follow-up fixes.

2. **Should `audit-org.md` be left as-is or refactored?** Recommendation: leave as-is. It works perfectly in Claude. The new audit skill is the Codex-side addition.

3. **LWC scoring**: The current `audit-org.md` doesn't reference a specific LWC point rubric (it just says "Score using the rubric from cirra-ai-sf-lwc"). The LWC SKILL.md has a 165-point SLDS 2 scoring system. The audit skill should reference this explicitly.
