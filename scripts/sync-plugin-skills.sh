#!/usr/bin/env bash
set -euo pipefail

# Sync skills from the top-level skills/ directory into each plugin.
#
# The source of truth for skills is skills/ at the repo root. Each plugin
# contains a copy under plugins/<name>/skills/ so that marketplace installs
# (which clone the repo directly) can find them. This script keeps those
# copies in sync.
#
# Matching convention: skills whose name starts with the plugin name are
# copied into that plugin. E.g. cirra-ai-sf-apex → plugins/cirra-ai-sf/skills/
#
# Usage:
#   scripts/sync-plugin-skills.sh           # sync all plugins
#   scripts/sync-plugin-skills.sh --check   # check if in sync (for CI)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

SYNCED=0
STALE=0

for plugin_json in "$REPO_ROOT"/plugins/*/.claude-plugin/plugin.json; do
  [[ -f "$plugin_json" ]] || continue

  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"
  skills_dest="$plugin_dir/skills"

  for skill_dir in "$REPO_ROOT"/skills/"${plugin_name}"-*; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    dest="$skills_dest/$skill_name"

    # Compare using diff (ignoring .DS_Store etc.)
    if [[ -d "$dest" ]] && diff -rq --exclude='.DS_Store' "$skill_dir" "$dest" >/dev/null 2>&1; then
      continue
    fi

    if [[ $CHECK_ONLY -eq 1 ]]; then
      if [[ -d "$dest" ]]; then
        echo "  STALE: $plugin_name/skills/$skill_name (differs from skills/$skill_name)"
      else
        echo "  MISSING: $plugin_name/skills/$skill_name"
      fi
      STALE=$((STALE + 1))
    else
      rm -rf "$dest"
      cp -R "$skill_dir" "$dest"
      echo "  Synced: $plugin_name/skills/$skill_name"
      SYNCED=$((SYNCED + 1))
    fi
  done
done

if [[ $CHECK_ONLY -eq 1 ]]; then
  if [[ $STALE -gt 0 ]]; then
    echo ""
    echo "$STALE skill(s) out of sync. Run 'scripts/sync-plugin-skills.sh' to fix."
    exit 1
  else
    echo "All plugin skills are in sync."
  fi
else
  if [[ $SYNCED -gt 0 ]]; then
    echo "Synced $SYNCED skill(s)."
  else
    echo "All plugin skills already in sync."
  fi
fi
