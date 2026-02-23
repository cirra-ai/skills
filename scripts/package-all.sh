#!/usr/bin/env bash
set -euo pipefail

# Package all Cirra AI plugins and skills for distribution.
#
# Plugin zips are assembled by combining the plugin skeleton (from plugins/)
# with the relevant skills (from skills/) into a single zip.
# Skill zips are packaged individually from skills/.
#
# Usage:
#   scripts/package-all.sh          # warn on skill issues, fail on errors
#   scripts/package-all.sh --strict # also fail on skill warnings

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGINS_OUT_DIR="$REPO_ROOT/install/plugins"
STRICT=0

for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

rm -rf "$PLUGINS_OUT_DIR"
mkdir -p "$PLUGINS_OUT_DIR"

# ── Assemble shared content into target files ─────────────────────────────────
# Run before any packaging so both plugin and skill zips get assembled content.

echo "=== Assembling Shared Content ==="
echo ""
"$SCRIPT_DIR/assemble.sh"
echo ""

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

for plugin_json in "$REPO_ROOT"/plugins/*/.claude-plugin/plugin.json; do
  [[ -f "$plugin_json" ]] || continue

  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"

  # Skip directories with spaces — likely artifacts
  if [[ "$plugin_name" == *" "* ]]; then
    echo "  Skipping '$plugin_name' (contains spaces, likely artifact)"
    continue
  fi

  PLUGIN_COUNT=$((PLUGIN_COUNT + 1))

  echo "  Packaging $plugin_name..."

  # Assemble the full plugin in a temp directory:
  # 1. Copy the plugin skeleton
  # 2. Copy all skills into skills/ within the plugin
  tmp_dir="$(mktemp -d)"
  plugin_tmp="$tmp_dir/$plugin_name"

  cp -r "$plugin_dir" "$plugin_tmp"
  mkdir -p "$plugin_tmp/skills"

  # Copy all skills into the plugin
  for skill_dir in "$REPO_ROOT"/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    [[ "$skill_name" == *" "* ]] && continue
    cp -r "$skill_dir" "$plugin_tmp/skills/$skill_name"
  done

  (cd "$tmp_dir" && zip -r -q "$PLUGINS_OUT_DIR/$plugin_name.zip" "$plugin_name" $EXCLUDE_ARGS)

  rm -rf "$tmp_dir"
done

echo ""
echo "  Packaged $PLUGIN_COUNT individual plugins"
echo ""
echo "=== Done ==="
echo ""
echo "Output in $PLUGINS_OUT_DIR/:"
ls -lh "$PLUGINS_OUT_DIR"/*.zip

echo ""

# Package skills
skills_args=()
[[ $STRICT -eq 1 ]] && skills_args+=(--strict)
"$SCRIPT_DIR/package-skills.sh" ${skills_args[@]+"${skills_args[@]}"}
