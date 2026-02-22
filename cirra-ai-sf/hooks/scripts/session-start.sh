#!/usr/bin/env bash
# SessionStart hook for cirra-ai-sf plugin
# Detects whether native MCP is available. If not (web session), sets up
# MCPorter as a bridge to the Cirra AI MCP Server.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check if mcporter is available (installed globally or via npx)
mcporter_available() {
  command -v mcporter &>/dev/null || npx mcporter --version &>/dev/null 2>&1
}

# Check if native MCP tools are likely available by looking at the environment.
# Web sessions typically lack the native MCP transport. We use the absence
# of CLAUDE_MCP_TRANSPORT as a heuristic — when running in CLI/desktop,
# Claude Code sets this when MCP servers connect.
native_mcp_likely() {
  [ -n "${CLAUDE_MCP_TRANSPORT:-}" ]
}

if native_mcp_likely; then
  # CLI/desktop session — native MCP handles everything
  exit 0
fi

# Web session detected — set up MCPorter bridge
echo "Native MCP transport not detected (web session)."
echo ""

if mcporter_available; then
  echo "MCPorter is available. Cirra AI MCP tools can be called via the mcporter-bridge."
else
  echo "MCPorter is not installed. Installing..."
  if npm install -g mcporter &>/dev/null 2>&1; then
    echo "MCPorter installed successfully."
  else
    echo "Could not install mcporter globally. Falling back to npx (slower first run)."
    echo "To speed up future calls: npm install -g mcporter"
  fi
fi

echo ""
echo "IMPORTANT: When native MCP tools (mcp__*) are unavailable, use the Bash tool"
echo "with the mcporter-bridge script to call Cirra AI MCP Server tools:"
echo ""
echo "  ${PLUGIN_ROOT}/scripts/mcporter-bridge.sh <tool_name> '<json_params>'"
echo ""
echo "On first use, MCPorter will open a browser for OAuth authentication."
echo "Tokens are cached under ~/.mcporter/cirra-ai/ for subsequent calls."
echo ""
echo "See the cirra-ai-mcp-bridge skill for the full tool reference."
