#!/usr/bin/env bash
set -euo pipefail

# Sync skills from the top-level skills/ directory into each plugin.
#
# The source of truth for skills is skills/ at the repo root. Each plugin
# contains a copy under plugins/<name>/skills/ so that marketplace installs
# (which clone the repo directly) can find them. This script keeps those
# copies in sync.
#
# Additionally, shared assets (icons from shared/assets/) are copied into
# each skill's assets/ directory so they're available in Codex and other
# platforms that consume standalone skills.
#
# Matching convention: skills whose name starts with the plugin name are
# copied into that plugin. E.g. cirra-ai-sf-apex → plugins/cirra-ai-sf/skills/
#
# Usage:
#   scripts/sync-plugin-skills.sh           # sync all plugins
#   scripts/sync-plugin-skills.sh --check   # check if in sync (for CI)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SHARED_ASSETS="$REPO_ROOT/shared/assets"
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# ── Copy shared assets into each skill ────────────────────────────────────────
# Icons etc. from shared/assets/ are copied into skills/<name>/assets/ so each
# skill is self-contained for Codex and standalone distribution.

ASSETS_SYNCED=0
ASSETS_STALE=0

if [[ -d "$SHARED_ASSETS" ]]; then
  for skill_dir in "$REPO_ROOT"/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_assets="$skill_dir/assets"

    for asset in "$SHARED_ASSETS"/*; do
      [[ -f "$asset" ]] || continue
      asset_name="$(basename "$asset")"
      dest="$skill_assets/$asset_name"

      if [[ -f "$dest" ]] && cmp -s "$asset" "$dest"; then
        continue
      fi

      if [[ $CHECK_ONLY -eq 1 ]]; then
        echo "  STALE ASSET: skills/$(basename "$skill_dir")/assets/$asset_name"
        ASSETS_STALE=$((ASSETS_STALE + 1))
      else
        mkdir -p "$skill_assets"
        cp "$asset" "$dest"
        ASSETS_SYNCED=$((ASSETS_SYNCED + 1))
      fi
    done
  done
fi

if [[ $CHECK_ONLY -eq 0 ]] && [[ $ASSETS_SYNCED -gt 0 ]]; then
  echo "  Copied $ASSETS_SYNCED shared asset(s) into skills"
fi

# ── Sync skills into plugins ─────────────────────────────────────────────────

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

    # Plugin copies are Claude-only: exclude shared icons (Codex-only) and
    # agents/ (OpenAI-only) when comparing and copying.
    EXCLUDE_ARGS=(--exclude='.DS_Store' --exclude='icon-large.png' --exclude='icon-small.png' --exclude='agents')

    if [[ -d "$dest" ]] && diff -rq "${EXCLUDE_ARGS[@]}" "$skill_dir" "$dest" >/dev/null 2>&1; then
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
      rsync -a --exclude='.DS_Store' --exclude='icon-large.png' --exclude='icon-small.png' --exclude='agents' "$skill_dir/" "$dest/"
      echo "  Synced: $plugin_name/skills/$skill_name"
      SYNCED=$((SYNCED + 1))
    fi
  done
done

if [[ $CHECK_ONLY -eq 1 ]]; then
  total_stale=$((ASSETS_STALE + STALE))
  if [[ $total_stale -gt 0 ]]; then
    echo ""
    echo "$total_stale item(s) out of sync. Run 'scripts/sync-plugin-skills.sh' to fix."
    exit 1
  else
    echo "All plugin skills and shared assets are in sync."
  fi
else
  if [[ $SYNCED -gt 0 ]]; then
    echo "  Synced $SYNCED skill(s) into plugin(s)."
  else
    echo "All plugin skills already in sync."
  fi
fi
