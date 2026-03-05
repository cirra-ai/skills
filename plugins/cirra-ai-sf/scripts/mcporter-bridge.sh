#!/usr/bin/env bash
# MCPorter bridge for Cirra AI MCP Server
# Routes MCP tool calls through MCPorter when native MCP is unavailable (e.g., web sessions).
#
# Auth modes (checked in order):
#   1. CIRRA_AI_TOKEN env var set → uses header-based Bearer token (no browser needed)
#   2. Otherwise → falls back to MCPorter's OAuth flow (requires browser)
#
# Usage:
#   ./mcporter-bridge.sh <tool_name> '<json_params>'
#
# Examples:
#   ./mcporter-bridge.sh cirra_ai_init '{}'
#   ./mcporter-bridge.sh soql_query '{"sObject":"Account","fields":["Id","Name"],"limit":10,"sf_user":"prod"}'
#   ./mcporter-bridge.sh sobject_describe '{"sObject":"Account","sf_user":"prod"}'

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_NAME="cirra-ai"

TOOL_NAME="${1:?Usage: mcporter-bridge.sh <tool_name> '<json_params>'}"
JSON_PARAMS="${2:-{\}}"

# Select MCP config based on auth mode.
# If CIRRA_AI_TOKEN is set, use the token-based config (header auth, no browser).
# Otherwise, use the standard config (OAuth via browser).
if [ -n "${CIRRA_AI_TOKEN:-}" ]; then
  MCP_CONFIG="$PLUGIN_ROOT/scripts/mcporter-token.mcp.json"
else
  MCP_CONFIG="$PLUGIN_ROOT/.mcp.json"
fi

# Ensure mcporter is available
if command -v mcporter &>/dev/null; then
  MCPORTER="mcporter"
elif npx mcporter --version &>/dev/null 2>&1; then
  MCPORTER="npx mcporter"
else
  echo "Error: mcporter is not installed. Install with: npm install -g mcporter" >&2
  exit 1
fi

# Build the mcporter call expression from JSON params
# Converts {"key":"value","key2":123} -> key="value", key2=123
CALL_ARGS=$(python3 -c "
import json, sys
params = json.loads(sys.argv[1])
parts = []
for k, v in params.items():
    if isinstance(v, str):
        parts.append(f'{k}=\"{v}\"')
    elif isinstance(v, list):
        parts.append(f'{k}={json.dumps(v)}')
    elif isinstance(v, dict):
        parts.append(f'{k}={json.dumps(v)}')
    elif isinstance(v, bool):
        parts.append(f'{k}={str(v).lower()}')
    else:
        parts.append(f'{k}={v}')
print(', '.join(parts))
" "$JSON_PARAMS" 2>/dev/null) || CALL_ARGS=""

# Execute via mcporter
if [ -n "$CALL_ARGS" ]; then
  $MCPORTER call --config "$MCP_CONFIG" "${SERVER_NAME}.${TOOL_NAME}(${CALL_ARGS})"
else
  $MCPORTER call --config "$MCP_CONFIG" "${SERVER_NAME}.${TOOL_NAME}()"
fi
