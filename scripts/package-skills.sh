#!/usr/bin/env bash
set -euo pipefail

# Package Cirra AI skills as standalone zip files for distribution.
#
# Each skill zip contains all files from the skill directory, with SKILL.md
# processed to strip plugin-only frontmatter keys and append a License section.
# LICENSE falls back to the parent plugin or repo root if not present in the skill dir.
#
# Usage:
#   scripts/package-skills.sh          # warn on issues, fail on errors
#   scripts/package-skills.sh --strict # also fail on warnings
#
# Output: install/skills/<skill-name>-skill.zip
# The "-skill" suffix distinguishes these from the full plugin zips in install/plugins/.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/install/skills"
STRICT=0

for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# ── Validate all skills first ─────────────────────────────────────────────────

echo "=== Validating Skills ==="
echo ""

validate_args=()
[[ $STRICT -eq 1 ]] && validate_args+=(--strict)

if ! "$SCRIPT_DIR/validate-skills.sh" "${validate_args[@]}"; then
  echo ""
  echo "Packaging aborted due to validation failures." >&2
  exit 1
fi

echo ""

# ── Package ───────────────────────────────────────────────────────────────────

rm -rf "$SKILLS_DIR"
mkdir -p "$SKILLS_DIR"

# Base license section appended to SKILL.md so each skill is self-contained.
# A CREDITS line is appended conditionally below if CREDITS.md is present.
LICENSE_SECTION_BASE='---

## License

MIT License — see [LICENSE](LICENSE) for details.

This skill is designed for use with Cirra AI, a commercial product developed by Cirra AI, Inc.
The skill and its contents are provided independently and are not part of the Cirra AI product itself.
Use of Cirra AI is subject to its own separate terms and conditions.'

LICENSE_SECTION_CREDITS='
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

  # Copy everything from the skill directory into the tmp dir
  cp -r "$skill_dir/." "$tmp_dir/"

  # SKILL.md — strip frontmatter keys not allowed in standalone skills,
  # then append License section.
  # Allowed keys: name, description, license, allowed-tools, compatibility, metadata
  # Stripped keys: hooks (requires plugin infrastructure; invalid standalone)
  python3 - "$skill_md" "$tmp_dir/SKILL.md" <<'PYEOF'
import sys

ALLOWED = {'name', 'description', 'license', 'allowed-tools', 'compatibility', 'metadata'}

src, dst = sys.argv[1], sys.argv[2]
content = open(src).read()

if content.startswith('---\n'):
    end = content.index('\n---\n', 4)
    frontmatter_lines = content[4:end].split('\n')
    body = content[end + 5:]

    out_lines = []
    skip = False
    for line in frontmatter_lines:
        # Top-level key: non-indented, non-empty
        if line and not line[0].isspace():
            key = line.split(':')[0].strip()
            skip = key not in ALLOWED
            if skip:
                continue  # don't warn, just drop silently
        if not skip:
            out_lines.append(line)

    new_fm = '\n'.join(out_lines).strip()
    content = f'---\n{new_fm}\n---\n\n{body}'

open(dst, 'w').write(content)
PYEOF

  # LICENSE — use what's in the skill dir, fall back to plugin-level or repo root
  if [[ ! -f "$tmp_dir/LICENSE" ]]; then
    if [[ -f "$plugin_dir/LICENSE" ]]; then
      cp "$plugin_dir/LICENSE" "$tmp_dir/LICENSE"
    elif [[ -f "$REPO_ROOT/LICENSE" ]]; then
      cp "$REPO_ROOT/LICENSE" "$tmp_dir/LICENSE"
    fi
  fi

  # Append License section to SKILL.md
  if [[ -f "$tmp_dir/CREDITS.md" ]]; then
    printf '\n%s%s\n' "$LICENSE_SECTION_BASE" "$LICENSE_SECTION_CREDITS" >> "$tmp_dir/SKILL.md"
  else
    printf '\n%s\n' "$LICENSE_SECTION_BASE" >> "$tmp_dir/SKILL.md"
  fi

  # Zip contents (preserving subdirectory structure)
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
