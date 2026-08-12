#!/usr/bin/env bash
set -euo pipefail

# Build a portable Agent Plugins 1.0 package under dist/agent-plugins/.
# Reuses the slim skill payloads from dist/openai/skills (build that first).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENAI_DIST="$REPO_ROOT/dist/openai"
OUT_DIR="$REPO_ROOT/dist/agent-plugins"
OUT_ZIP_DIR="$REPO_ROOT/install/agent-plugins"

if [[ ! -d "$OPENAI_DIST/skills" ]]; then
  echo "OpenAI dist missing — building it first..."
  "$SCRIPT_DIR/package-openai.sh"
fi

PLUGIN_VERSION=$(jq -r .version "$REPO_ROOT/plugins/cirra-ai-sf/.claude-plugin/plugin.json")
SOURCE_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD)

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/skills"

# Portable Agent Plugins manifest (root plugin.json)
cat > "$OUT_DIR/plugin.json" <<EOF
{
  "\$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "cirra-ai-sf",
  "version": "$PLUGIN_VERSION",
  "description": "Salesforce admin skills for use with the Cirra AI MCP Server.",
  "author": {
    "name": "Cirra AI",
    "email": "info@cirra.ai",
    "url": "https://github.com/cirra-ai"
  },
  "homepage": "https://skills.cirra.ai/",
  "repository": "https://github.com/cirra-ai/skills",
  "license": "MIT",
  "keywords": ["salesforce", "cirra-ai", "mcp", "apex", "flow"]
}
EOF

# Agent Plugins uses mcp.json (not .mcp.json). Transport type must be the
# schema enum value "streamable-http" (not camelCase).
cat > "$OUT_DIR/mcp.json" <<'EOF'
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "cirra-ai": {
      "type": "streamable-http",
      "url": "https://mcp.cirra.ai/mcp"
    }
  }
}
EOF

# Copy slim skills; keep agents/ under OpenAI extension namespace guidance.
# Agent Plugins allows extra files; clients ignore unknown skill files.
cp -a "$OPENAI_DIST/skills/." "$OUT_DIR/skills/"

# OpenAI-specific UI metadata lives under a client extension directory copy as well
mkdir -p "$OUT_DIR/com.openai.codex"
if [[ -f "$OPENAI_DIST/.codex-plugin/plugin.json" ]]; then
  mkdir -p "$OUT_DIR/com.openai.codex/.codex-plugin"
  cp "$OPENAI_DIST/.codex-plugin/plugin.json" "$OUT_DIR/com.openai.codex/.codex-plugin/plugin.json"
fi

# Provenance manifest (repo-level; not part of Agent Plugins core)
python3 - <<PY
import json
from pathlib import Path
root = Path("$OUT_DIR")
openai_manifest = json.loads(Path("$OPENAI_DIST/manifest.json").read_text())
manifest = {
    "formatVersion": 1,
    "sourceCommit": "$SOURCE_COMMIT",
    "format": "agent-plugins-1.0.0",
    "plugin": {"name": "cirra-ai-sf", "version": "$PLUGIN_VERSION"},
    "skills": openai_manifest.get("skills", {}),
}
(root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"  Wrote {root / 'manifest.json'}")
PY

rm -rf "$OUT_ZIP_DIR"
mkdir -p "$OUT_ZIP_DIR"
(
  cd "$REPO_ROOT/dist"
  zip -r -q "$OUT_ZIP_DIR/cirra-ai-sf-agent-plugins.zip" agent-plugins \
    -x "*.DS_Store" "*__pycache__*" "*.pyc"
)

echo ""
echo "=== Validating Agent Plugins distro ==="
python3 "$SCRIPT_DIR/validate_agent_plugins.py" --dist "$OUT_DIR"

echo ""
echo "=== Agent Plugins package ready ==="
echo "Tree: $OUT_DIR"
echo "Zip:  $OUT_ZIP_DIR/cirra-ai-sf-agent-plugins.zip"
ls -lh "$OUT_ZIP_DIR"/*.zip
