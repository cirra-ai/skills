#!/usr/bin/env bash
set -euo pipefail

# Package Cirra AI plugins as zip files for distribution.
# Outputs individual plugin zips + an all-in-one bundle to install/plugins/.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/install/plugins"

rm -rf "$PLUGINS_DIR"
mkdir -p "$PLUGINS_DIR"

# Directories to exclude from zips
EXCLUDE_PATTERNS=(
  "*.DS_Store"
  "*__MACOSX*"
  "*.pyc"
  "*__pycache__*"
  "*.ruff_cache*"
)

build_exclude_args() {
  local args=()
  for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    args+=(-x "$pattern")
  done
  echo "${args[@]}"
}

EXCLUDE_ARGS=$(build_exclude_args)

echo "=== Packaging Cirra AI Plugins ==="
echo ""

# Find all plugin directories (contain .claude-plugin/plugin.json)
PLUGIN_COUNT=0
PLUGIN_DIRS=()

for plugin_json in "$REPO_ROOT"/*/.claude-plugin/plugin.json; do
  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"

  # Skip directories with spaces (e.g. "cirra-ai-sf-data 2") — likely artifacts
  if [[ "$plugin_name" == *" "* ]]; then
    echo "  Skipping '$plugin_name' (contains spaces, likely artifact)"
    continue
  fi

  PLUGIN_DIRS+=("$plugin_dir")
  PLUGIN_COUNT=$((PLUGIN_COUNT + 1))

  echo "  Packaging $plugin_name..."
  (cd "$REPO_ROOT" && zip -r -q "$PLUGINS_DIR/$plugin_name.zip" "$plugin_name" $EXCLUDE_ARGS)
done

echo ""
echo "  Packaged $PLUGIN_COUNT individual plugins"

# Create all-in-one bundle
echo ""
echo "  Packaging cirra-ai-sf-skills.zip (all-in-one bundle)..."

BUNDLE_ARGS=()
for plugin_dir in "${PLUGIN_DIRS[@]}"; do
  BUNDLE_ARGS+=("$(basename "$plugin_dir")")
done
# Include the root marketplace.json
BUNDLE_ARGS+=(".claude-plugin")

(cd "$REPO_ROOT" && zip -r -q "$PLUGINS_DIR/cirra-ai-sf-skills.zip" "${BUNDLE_ARGS[@]}" $EXCLUDE_ARGS)

echo ""
echo "=== Done ==="
echo ""
echo "Output in $PLUGINS_DIR/:"
ls -lh "$PLUGINS_DIR"/*.zip
