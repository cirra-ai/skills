# Plan: Codex Audit Parity via Shared Content + Build Assembly

## Problem

The `audit-org` command works well in Claude Cowork/Code because it is a **command** (`commands/audit-org.md`) — a concept that only exists in the Claude plugin system. OpenAI Codex has no equivalent of commands; it only understands **skills** (SKILL.md files) and **agents** (openai.yaml). When a Codex user says "audit my salesforce org", none of the four existing skills trigger because none of them contain audit orchestration logic.

## Current Architecture

```
cirra-ai-sf/
├── .claude-plugin/plugin.json    ← Claude-only plugin manifest
├── commands/                     ← Claude-only slash commands
│   ├── audit-org.md              ← THE audit command (Claude only)
│   ├── validate-*.md, create-*.md, update-*.md, ...
├── skills/
│   ├── cirra-ai-sf-apex/         ← SKILL.md + agents/openai.yaml
│   ├── cirra-ai-sf-flow/
│   ├── cirra-ai-sf-data/
│   └── cirra-ai-sf-lwc/
└── hooks/hooks.json              ← Claude-only PreToolUse hooks
```

**Key observation**: `audit-org.md` is ~115 lines of orchestration logic that references scoring rubrics defined in the three domain SKILL.md files. It doesn't define its own rubrics.

## Solution: Single Source + Build Assembly

One shared file contains the audit workflow. Both the Claude command and the new Codex skill are assembled from it — one source of truth, no drift.

### Target Architecture

```
cirra-ai-sf/
├── shared/
│   └── audit-phases.md               ← SINGLE SOURCE OF TRUTH for audit workflow
├── commands/
│   └── audit-org.md                   ← Refactored: frontmatter + preamble + {{include:shared/audit-phases.md}}
├── skills/
│   ├── cirra-ai-sf-audit/             ← NEW
│   │   ├── SKILL.md.template          ← Frontmatter + skill intro + {{include:../../shared/audit-phases.md}}
│   │   ├── README.md
│   │   ├── CREDITS.md
│   │   └── agents/
│   │       └── openai.yaml
│   ├── cirra-ai-sf-apex/
│   ├── cirra-ai-sf-flow/
│   ├── cirra-ai-sf-data/
│   └── cirra-ai-sf-lwc/
```

### How the include works

At dev time, the source files use a simple marker:

```markdown
{{include:../../shared/audit-phases.md}}
```

The `package-skills.sh` script (and a new sibling for commands) resolves these markers at build time, inlining the shared content into the final SKILL.md and audit-org.md. For local development/testing, a pre-commit hook or a `scripts/assemble.sh` script can also resolve them.

**Claude commands note**: Claude loads commands from the raw `.md` files at runtime — it doesn't go through the packaging pipeline. So `audit-org.md` needs to work as-is. Two options:

- **Option 1**: `audit-org.md` is a generated file (checked into git, rebuilt by `scripts/assemble.sh`). The source of truth is `commands/audit-org.md.template`.
- **Option 2**: `audit-org.md` stays as a plain file and the shared content is inlined into it by the assemble script, with a comment marker like `<!-- AUTO-GENERATED FROM shared/audit-phases.md — DO NOT EDIT BELOW THIS LINE -->`.

**Recommendation: Option 2.** The command file stays a valid `.md` that Claude can load directly. The assemble script updates the section below the marker. Developers run `scripts/assemble.sh` after editing `shared/audit-phases.md`, and CI validates the files are in sync.

## Detailed File Changes

### 1. Create `shared/audit-phases.md`

Extract phases 1–6, the routing table, and the build-order section from the current `audit-org.md` into this file. This is pure audit workflow — no platform-specific framing, no frontmatter.

Contents (~90 lines):

- Phase 1: Count components (tooling API queries)
- Phase 2: Collect and score Apex (150-point rubric from cirra-ai-sf-apex)
- Phase 3: Collect and score Flows (110-point rubric from cirra-ai-sf-flow)
- Phase 4: Collect and score LWC (165-point rubric from cirra-ai-sf-lwc)
- Phase 5: Generate reports (Word, Excel, HTML)
- Phase 6: Summarise
- Routing reference table
- Build order for fixing issues

### 2. Create `skills/cirra-ai-sf-audit/`

| File                 | Contents                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `SKILL.md`           | Frontmatter (name, description targeting "audit" triggers) + skill intro + shared phases (inlined at build time or checked in) |
| `README.md`          | Brief description of the audit skill                                                                                           |
| `CREDITS.md`         | Attribution (Cirra AI)                                                                                                         |
| `agents/openai.yaml` | Codex agent UI config (display_name, icon, default_prompt)                                                                     |

The `SKILL.md` description should trigger on prompts like: "audit my salesforce org", "review my org", "score my org", "org health check", "audit apex flows and lwc".

### 3. Refactor `commands/audit-org.md`

Replace the body (everything after the Prerequisites section) with:

```markdown
<!-- AUTO-GENERATED FROM shared/audit-phases.md — DO NOT EDIT BELOW THIS LINE -->

{contents of shared/audit-phases.md}
```

The file remains a valid markdown command that Claude loads directly.

### 4. Create `scripts/assemble.sh`

A simple script that:

1. Finds all `.md` files containing `{{include:...}}` markers OR `<!-- AUTO-GENERATED FROM ... -->` markers
2. Resolves includes by inlining the referenced file content
3. Writes the result back

This runs:

- Manually after editing `shared/audit-phases.md`
- In CI (the `validate-skills.sh` step can check that assembled files are up to date)
- Before packaging (`package-skills.sh` calls it)

### 5. Update `scripts/package-skills.sh`

Add a call to `scripts/assemble.sh` before the packaging loop, so SKILL.md files are assembled before being zipped.

### 6. Update `README.md`

Add the new audit skill to the skills table:

```markdown
| [cirra-ai-sf-audit](skills/cirra-ai-sf-audit/README.md) | Full org audit across Apex, Flows, and LWC with scored reports |
```

## Summary of Changes

| File                                          | Action     | Purpose                                                   |
| --------------------------------------------- | ---------- | --------------------------------------------------------- |
| `cirra-ai-sf/shared/audit-phases.md`          | **Create** | Single source of truth for audit workflow                 |
| `skills/cirra-ai-sf-audit/SKILL.md`           | **Create** | Audit skill for Codex (assembled from shared content)     |
| `skills/cirra-ai-sf-audit/README.md`          | **Create** | Skill documentation                                       |
| `skills/cirra-ai-sf-audit/CREDITS.md`         | **Create** | Attribution                                               |
| `skills/cirra-ai-sf-audit/agents/openai.yaml` | **Create** | Codex agent UI config                                     |
| `cirra-ai-sf/commands/audit-org.md`           | **Modify** | Refactor to use shared content with auto-generated marker |
| `scripts/assemble.sh`                         | **Create** | Build script to inline shared content                     |
| `scripts/package-skills.sh`                   | **Modify** | Call assemble.sh before packaging                         |
| `README.md`                                   | **Modify** | Add audit skill to skills table                           |

## Risks & Mitigations

| Risk                                              | Mitigation                                                                |
| ------------------------------------------------- | ------------------------------------------------------------------------- |
| Shared content gets edited but assemble isn't run | CI check validates assembled files match source                           |
| Claude command breaks if marker format changes    | Marker is a plain HTML comment — invisible to Claude's markdown parser    |
| New skill doesn't trigger in Codex                | Write a rich description with multiple trigger phrases; test with Codex   |
| Packaging misses the new skill                    | Auto-discovered by existing `*/skills/*/SKILL.md` glob — no config needed |

## Non-Goals

- No changes to existing domain skills (apex, flow, data, lwc)
- No changes to hooks or plugin.json
- No changes to the MCP server configuration
