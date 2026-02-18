#!/usr/bin/env bash
set -euo pipefail

# Package Cirra AI skills as standalone zip files for distribution.
#
# Each skill zip contains:
#   SKILL.md      — the skill file with a License section appended
#   LICENSE       — MIT license (copied from parent plugin, falls back to repo root)
#   CREDITS.md    — attribution file (copied from parent plugin, if present)
#
# Output: install/skills/<skill-name>-skill.zip
# The "-skill" suffix distinguishes these from the full plugin zips in install/plugins/.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/install/skills"

rm -rf "$SKILLS_DIR"
mkdir -p "$SKILLS_DIR"

# License section appended to SKILL.md so each skill is self-contained
LICENSE_SECTION='---

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc.
The skill and its contents are provided independently and are not part of the Cirra AI product itself.
Use of Cirra AI is subject to its own separate terms and conditions.

For credits and attribution see [CREDITS.md](CREDITS.md).'

echo "=== Packaging Cirra AI Skills ==="
echo ""

SKILL_COUNT=0

# Find all SKILL.md files at plugin/skills/skillname/SKILL.md
for skill_md in "$REPO_ROOT"/*/skills/*/SKILL.md; do
  [[ -f "$skill_md" ]] || continue

  skill_dir="$(dirname "$skill_md")"
  skill_name="$(basename "$skill_dir")"
  plugin_dir="$(dirname "$(dirname "$skill_dir")")"
  plugin_name="$(basename "$plugin_dir")"

  # Skip directories with spaces (e.g. "cirra-ai-sf-apex 2") — likely artifacts
  if [[ "$plugin_name" == *" "* ]]; then
    echo "  Skipping '$plugin_name' (contains spaces, likely artifact)"
    continue
  fi

  echo "  Packaging skill: $skill_name..."

  tmp_dir="$(mktemp -d)"

  # SKILL.md with License section appended
  cp "$skill_md" "$tmp_dir/SKILL.md"
  printf '\n%s\n' "$LICENSE_SECTION" >> "$tmp_dir/SKILL.md"

  # LICENSE — prefer plugin-level copy, fall back to repo root
  if [[ -f "$plugin_dir/LICENSE" ]]; then
    cp "$plugin_dir/LICENSE" "$tmp_dir/LICENSE"
  elif [[ -f "$REPO_ROOT/LICENSE" ]]; then
    cp "$REPO_ROOT/LICENSE" "$tmp_dir/LICENSE"
  fi

  # CREDITS.md — only present in some plugins
  if [[ -f "$plugin_dir/CREDITS.md" ]]; then
    cp "$plugin_dir/CREDITS.md" "$tmp_dir/CREDITS.md"
  fi

  # Zip contents flat (files at root, not in a subdirectory)
  (cd "$tmp_dir" && zip -r -q "$SKILLS_DIR/${skill_name}-skill.zip" .)

  rm -rf "$tmp_dir"
  SKILL_COUNT=$((SKILL_COUNT + 1))
done

echo ""
echo "  Packaged $SKILL_COUNT skills"
echo ""
echo "=== Done ==="
echo ""
echo "Output in $SKILLS_DIR/:"
ls -lh "$SKILLS_DIR"/*.zip 2>/dev/null || echo "  (none)"
