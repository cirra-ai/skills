#!/usr/bin/env bash
set -euo pipefail

# Assemble markdown files by inlining shared content.
#
# Finds all .md files under plugin and skill directories that contain an
# auto-generated marker comment, then replaces everything below the marker
# with the contents of the referenced shared file.
#
# Marker format (HTML comment, invisible to markdown renderers):
#   <!-- AUTO-GENERATED FROM shared/audit-phases.md — DO NOT EDIT BELOW THIS LINE -->
#
# The path after "AUTO-GENERATED FROM" is resolved relative to the plugin
# directory containing the target file. For files under skills/, the path is
# resolved relative to the skill directory itself.
#
# Usage:
#   scripts/assemble.sh           # assemble all files
#   scripts/assemble.sh --check   # check that files are up to date (for CI)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHECK_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

MARKER_PATTERN='<!-- AUTO-GENERATED FROM '
UPDATED=0
STALE=0

# Search .md files in plugin commands and in skill directories
for md_file in $(grep -rl "$MARKER_PATTERN" \
    "$REPO_ROOT"/plugins/*/commands/*.md \
    "$REPO_ROOT"/skills/*/SKILL.md \
    2>/dev/null); do
  [[ -f "$md_file" ]] || continue

  # Extract the shared file path from the marker line
  marker_line=$(grep "$MARKER_PATTERN" "$md_file")
  # Parse: <!-- AUTO-GENERATED FROM shared/audit-phases.md — DO NOT EDIT BELOW THIS LINE -->
  shared_rel=$(echo "$marker_line" | sed 's/.*AUTO-GENERATED FROM \(.*\) —.*/\1/')

  if [[ -z "$shared_rel" ]]; then
    echo "  WARNING: Could not parse shared file path from marker in $md_file" >&2
    continue
  fi

  # Determine the base directory for resolving the shared path.
  # Plugin commands: plugins/cirra-ai-sf/commands/foo.md → base is plugins/cirra-ai-sf
  # Skills: skills/cirra-ai-sf-audit/SKILL.md → base is skills/cirra-ai-sf-audit
  md_dir="$(dirname "$md_file")"
  if [[ "$(basename "$md_dir")" == "commands" ]]; then
    base_dir="$(dirname "$md_dir")"
  else
    # SKILL.md sits directly in the skill directory
    base_dir="$md_dir"
  fi

  shared_file="$base_dir/$shared_rel"

  if [[ ! -f "$shared_file" ]]; then
    echo "  ERROR: Shared file not found: $shared_file (referenced from $md_file)" >&2
    exit 1
  fi

  # Build the expected content: everything before and including the marker,
  # then the shared file contents.
  before_and_marker=$(sed "/$MARKER_PATTERN/q" "$md_file")
  shared_content=$(cat "$shared_file")
  expected="${before_and_marker}
${shared_content}"

  current=$(cat "$md_file")

  if [[ "$current" != "$expected" ]]; then
    if [[ $CHECK_ONLY -eq 1 ]]; then
      echo "  STALE: $md_file (run scripts/assemble.sh to update)"
      STALE=$((STALE + 1))
    else
      printf '%s\n' "$expected" > "$md_file"
      echo "  Updated: $md_file"
      UPDATED=$((UPDATED + 1))
    fi
  fi
done

if [[ $CHECK_ONLY -eq 1 ]]; then
  if [[ $STALE -gt 0 ]]; then
    echo ""
    echo "$STALE file(s) are out of date. Run 'scripts/assemble.sh' to fix."
    exit 1
  else
    echo "All assembled files are up to date."
  fi
else
  if [[ $UPDATED -gt 0 ]]; then
    echo ""
    echo "Assembled $UPDATED file(s)."
  else
    echo "All files already up to date."
  fi
fi
