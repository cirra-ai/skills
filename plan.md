# Plan: Consolidate Hooks into Unified Dispatchers

## Goal

Replace the 4 separate `hooks/hooks.json` files (one per plugin) with a **single** `hooks/hooks.json` in `cirra-ai-sf/` that uses two dispatcher scripts to route validation to the correct domain sub-scripts. Start with **Apex and Flow** dispatching; Data and LWC can be added later.

---

## Current State

Each plugin has its own hooks:

| Plugin | PreToolUse | PostToolUse |
|--------|-----------|-------------|
| **cirra-ai-sf** (orchestrator) | — | — |
| **cirra-ai-sf-apex** | `pre-mcp-validate.py` → `ApexMCPValidator` | `post-tool-validate.py` → `.cls`/`.trigger` |
| **cirra-ai-sf-flow** | `pre-mcp-validate.py` → `FlowMCPValidator` | `post-tool-validate.py` → `.flow-meta.xml` |
| **cirra-ai-sf-data** | — | `post-write-validate.py` → `.apex`/`.soql`/`.csv`/`.json` |
| **cirra-ai-sf-lwc** | — | `post-tool-validate.py` → `.html`/`.css`/`.js` |

**Key insight**: The existing domain validators (`mcp_validator.py`, `validate_apex.py`, `validate_flow.py`) already self-filter — they return `status: "skipped"` for non-matching metadata types. The dispatchers just need to route to the right one.

---

## Target Structure

```
cirra-ai-sf/
├── hooks/
│   ├── hooks.json                          ← single unified config
│   └── scripts/
│       ├── pre_mcp_dispatch.py             ← NEW: PreToolUse dispatcher
│       ├── post_tool_dispatch.py           ← NEW: PostToolUse dispatcher
│       ├── audit_runner.py                 ← existing (unchanged)
│       ├── apex/                           ← MOVED from cirra-ai-sf-apex/hooks/scripts/
│       │   ├── mcp_validator.py            (ApexMCPValidator class)
│       │   ├── validate_apex.py            (ApexValidator - 150pt scoring)
│       │   ├── llm_pattern_validator.py    (LLM anti-pattern checks)
│       │   ├── mcp_validator_cli.py        (CLI wrapper, kept for standalone use)
│       │   └── validate_apex_cli.py        (CLI wrapper)
│       └── flow/                           ← MOVED from cirra-ai-sf-flow/hooks/scripts/
│           ├── mcp_validator.py            (FlowMCPValidator class)
│           ├── validate_flow.py            (EnhancedFlowValidator - 110pt scoring)
│           ├── validate_flow_cli.py        (CLI wrapper)
│           ├── simulate_flow.py            (Flow simulation)
│           └── mcp_validator_cli.py        (CLI wrapper)
```

---

## Implementation Steps

### Step 1: Create domain subdirectories and copy scripts

```
mkdir -p cirra-ai-sf/hooks/scripts/apex
mkdir -p cirra-ai-sf/hooks/scripts/flow
```

Copy from `cirra-ai-sf-apex/hooks/scripts/`:
- `mcp_validator.py` → `apex/mcp_validator.py`
- `validate_apex.py` → `apex/validate_apex.py`
- `llm_pattern_validator.py` → `apex/llm_pattern_validator.py`
- `mcp_validator_cli.py` → `apex/mcp_validator_cli.py`
- `validate_apex_cli.py` → `apex/validate_apex_cli.py`

Copy from `cirra-ai-sf-flow/hooks/scripts/`:
- `mcp_validator.py` → `flow/mcp_validator.py`
- `validate_flow.py` → `flow/validate_flow.py`
- `validate_flow_cli.py` → `flow/validate_flow_cli.py`
- `simulate_flow.py` → `flow/simulate_flow.py`
- `mcp_validator_cli.py` → `flow/mcp_validator_cli.py`

### Step 2: Write `pre_mcp_dispatch.py` (PreToolUse dispatcher)

This script:
1. Reads hook JSON from stdin
2. Strips MCP prefix to get base tool name (`metadata_create`, etc.)
3. Extracts `metadata_type` from the payload's `type` field (or `sObject` for tooling_api_dml)
4. Routes to domain validator:
   - `ApexClass`/`ApexTrigger` → `apex/mcp_validator.py::ApexMCPValidator`
   - `Flow`/`FlowDefinition` → `flow/mcp_validator.py::FlowMCPValidator`
   - Anything else → allow silently (future: route to other validators)
5. Processes the validator result (deny on CRITICAL/HIGH, warn below threshold, allow with score)

**Key design**: The decision logic (deny/allow/warn) stays in the dispatcher — the domain validators just return scored results. This avoids duplicating the decision logic between the current two `pre-mcp-validate.py` files.

### Step 3: Write `post_tool_dispatch.py` (PostToolUse dispatcher)

This script:
1. Reads hook JSON from stdin
2. Extracts `file_path` from `tool_input`
3. Routes by file extension:
   - `.cls` / `.trigger` → `apex/validate_apex.py::ApexValidator` (+ LLM pattern validator)
   - `.flow-meta.xml` → `flow/validate_flow.py::EnhancedFlowValidator`
   - Anything else → silently pass through (future: LWC, Data)
4. Formats and outputs the scored result

**Key design**: Each domain's format/output logic is inlined in the dispatcher for now (it's ~40 lines per domain). The domain validators return raw results; the dispatcher formats them.

### Step 4: Update `hooks.json`

Replace the empty `cirra-ai-sf/hooks/hooks.json` with:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*metadata_create|.*metadata_update|.*tooling_api_dml",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/pre_mcp_dispatch.py",
            "timeout": 60
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/post_tool_dispatch.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Step 5: Fix import paths in copied domain scripts

The domain validators use relative imports like `from validate_apex import ApexValidator`. Since they're now in subdirectories, we need to ensure `sys.path` points correctly. The `mcp_validator.py` files already use `_SCRIPT_DIR` — just verify that pattern still works when invoked from the parent dispatcher via `sys.path.insert(0, apex_dir)`.

### Step 6: Remove old hook configs

Delete `hooks/hooks.json` from the 4 sub-plugins (since they'll eventually be folded into `cirra-ai-sf`):
- `cirra-ai-sf-apex/hooks/hooks.json`
- `cirra-ai-sf-flow/hooks/hooks.json`
- `cirra-ai-sf-data/hooks/hooks.json`
- `cirra-ai-sf-lwc/hooks/hooks.json`

**Note**: The sub-plugin `hooks/scripts/` directories are NOT deleted yet — they stay as-is until the full plugin consolidation. The new dispatchers reference the *copied* scripts under `cirra-ai-sf/hooks/scripts/apex|flow/`.

---

## What stays unchanged (for now)

- **Data hooks** (`post-write-validate.py`): Legacy/advisory, low priority. Can add a `data/` subdirectory later.
- **LWC hooks** (`post-tool-validate.py`): Can add an `lwc/` subdirectory later.
- **`audit_runner.py`**: Already in `cirra-ai-sf/hooks/scripts/`, untouched.
- **All SKILL.md files, templates, docs, commands**: Separate concern from hooks.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Import paths break after moving scripts to subdirs | Each domain dir gets `sys.path.insert(0, domain_dir)` before import. Domain scripts already use `_SCRIPT_DIR` for relative imports. |
| Both Apex and Flow validators fire on every `metadata_create` | Already handled: validators check `metadata_type` and return `skipped` for non-matching types. Dispatcher checks status and allows silently. |
| Post-tool dispatcher fires on ALL Write/Edit | Already handled: dispatcher checks file extension and only validates matching files. Non-matching files pass through silently. |
| Old sub-plugin hooks fire alongside new dispatcher | Step 6 removes old `hooks.json` files. If sub-plugins are still installed separately, they won't have hooks anymore. |
