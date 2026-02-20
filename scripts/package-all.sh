#!/usr/bin/env bash
set -euo pipefail

# Package all Cirra AI plugins and skills for distribution.
# Outputs individual plugin zips to install/plugins/ and skill zips to install/skills/.
#
# Usage:
#   scripts/package-all.sh          # warn on skill issues, fail on errors
#   scripts/package-all.sh --strict # also fail on skill warnings

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGINS_DIR="$REPO_ROOT/install/plugins"
STRICT=0

for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

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

for plugin_json in "$REPO_ROOT"/*/.claude-plugin/plugin.json; do
  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"

  # Skip directories with spaces (e.g. "cirra-ai-sf-data 2") — likely artifacts
  if [[ "$plugin_name" == *" "* ]]; then
    echo "  Skipping '$plugin_name' (contains spaces, likely artifact)"
    continue
  fi

  PLUGIN_COUNT=$((PLUGIN_COUNT + 1))

  echo "  Packaging $plugin_name..."
  (cd "$REPO_ROOT" && zip -r -q "$PLUGINS_DIR/$plugin_name.zip" "$plugin_name" $EXCLUDE_ARGS)
done

echo ""
echo "  Packaged $PLUGIN_COUNT individual plugins"
echo ""
echo "=== Done ==="
echo ""
echo "Output in $PLUGINS_DIR/:"
ls -lh "$PLUGINS_DIR"/*.zip

echo ""

# Package skills
skills_args=()
[[ $STRICT -eq 1 ]] && skills_args+=(--strict)
"$SCRIPT_DIR/package-skills.sh" "${skills_args[@]}"
