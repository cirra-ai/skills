#!/usr/bin/env bash
set -euo pipefail

# Sync skills from the top-level skills/ directory into each plugin.
#
# The source of truth for skills is skills/ at the repo root. Each plugin
# contains a copy under plugins/<name>/skills/ so that marketplace installs
# (which clone the repo directly) can find them. This script keeps those
# copies in sync.
#
# Additionally, shared assets (icons from shared/assets/) and shared
# references (markdown from shared/references/) are copied into each
# skill's assets/ and references/ directories so they're available in
# Codex and other platforms that consume standalone skills.
#
# Skill-to-plugin matching (checked in order):
#   1. `plugin:` key in SKILL.md frontmatter (e.g. plugin: cirra-ai-sf)
#   2. Directory name prefix (e.g. sf-apex → plugins/cirra-ai-sf/)
#
# Usage:
#   scripts/sync-plugin-skills.sh           # sync all plugins
#   scripts/sync-plugin-skills.sh --check   # check if in sync (for CI)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SHARED_ASSETS="$REPO_ROOT/shared/assets"
SHARED_REFERENCES="$REPO_ROOT/shared/references"
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

# ── Copy shared references into each skill ───────────────────────────────────
# Markdown files from shared/references/ are copied into skills/<name>/references/
# so each skill can reference them (e.g. execution-modes.md, mcp-pagination.md).

REFS_SYNCED=0
REFS_STALE=0

if [[ -d "$SHARED_REFERENCES" ]]; then
  for skill_dir in "$REPO_ROOT"/skills/*/; do
    [[ -d "$skill_dir" ]] || continue
    skill_refs="$skill_dir/references"

    for ref in "$SHARED_REFERENCES"/*.md; do
      [[ -f "$ref" ]] || continue
      ref_name="$(basename "$ref")"
      dest="$skill_refs/$ref_name"

      if [[ -f "$dest" ]] && cmp -s "$ref" "$dest"; then
        continue
      fi

      if [[ $CHECK_ONLY -eq 1 ]]; then
        echo "  STALE REF: skills/$(basename "$skill_dir")/references/$ref_name"
        REFS_STALE=$((REFS_STALE + 1))
      else
        mkdir -p "$skill_refs"
        cp "$ref" "$dest"
        REFS_SYNCED=$((REFS_SYNCED + 1))
      fi
    done
  done
fi

if [[ $CHECK_ONLY -eq 0 ]] && [[ $REFS_SYNCED -gt 0 ]]; then
  echo "  Copied $REFS_SYNCED shared reference(s) into skills"
fi

# ── Sync skills into plugins ─────────────────────────────────────────────────
# Helper: read the `plugin:` key from a SKILL.md frontmatter block.
# Returns the value or empty string if not found.
read_plugin_key() {
  local skill_md="$1"
  [[ -f "$skill_md" ]] || return
  # Only look within the YAML frontmatter (between --- delimiters)
  awk '/^---$/{n++; next} n==1 && /^plugin:/{gsub(/^plugin:[[:space:]]*/, ""); print; exit}' "$skill_md"
}

SYNCED=0
STALE=0

# Plugin copies are Claude-only: exclude shared icons (Codex-only) and
# agents/ (OpenAI-only) when comparing and copying.
PLUGIN_EXCLUDES=(--exclude='.DS_Store' --exclude='icon-large.png' --exclude='icon-small.png' --exclude='agents' --exclude='tests')

for plugin_json in "$REPO_ROOT"/plugins/*/.claude-plugin/plugin.json; do
  [[ -f "$plugin_json" ]] || continue

  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  plugin_name="$(basename "$plugin_dir")"
  skills_dest="$plugin_dir/skills"

  # Collect skills belonging to this plugin from two sources:
  # 1. Skills with a `plugin:` frontmatter key matching this plugin name
  # 2. Skills whose directory name starts with the plugin name (legacy convention)
  skill_dirs=()
  for candidate in "$REPO_ROOT"/skills/*/; do
    [[ -d "$candidate" ]] || continue
    candidate_name="$(basename "$candidate")"

    # Check frontmatter `plugin:` key first
    fm_plugin="$(read_plugin_key "$candidate/SKILL.md")"
    if [[ "$fm_plugin" == "$plugin_name" ]]; then
      skill_dirs+=("$candidate")
      continue
    fi

    # Fall back to prefix convention
    if [[ "$candidate_name" == "${plugin_name}"-* ]]; then
      skill_dirs+=("$candidate")
    fi
  done

  for skill_dir in "${skill_dirs[@]}"; do
    skill_name="$(basename "$skill_dir")"
    dest="$skills_dest/$skill_name"

    if [[ -d "$dest" ]] && diff -rq "${PLUGIN_EXCLUDES[@]}" "$skill_dir" "$dest" >/dev/null 2>&1; then
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
      rsync -a "${PLUGIN_EXCLUDES[@]}" "$skill_dir/" "$dest/"
      echo "  Synced: $plugin_name/skills/$skill_name"
      SYNCED=$((SYNCED + 1))
    fi
  done
done

if [[ $CHECK_ONLY -eq 1 ]]; then
  total_stale=$((ASSETS_STALE + REFS_STALE + STALE))
  if [[ $total_stale -gt 0 ]]; then
    echo ""
    echo "$total_stale item(s) out of sync. Run 'scripts/sync-plugin-skills.sh' to fix."
    exit 1
  else
    echo "All plugin skills, shared assets, and shared references are in sync."
  fi
else
  if [[ $SYNCED -gt 0 ]]; then
    echo "  Synced $SYNCED skill(s) into plugin(s)."
  else
    echo "All plugin skills already in sync."
  fi
fi
