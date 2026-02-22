#!/usr/bin/env bash
# Validate agent skill directories using skills-ref.
#
# Usage:
#   scripts/validate-skills.sh           # validate all skills
#   scripts/validate-skills.sh --staged  # validate only skills with staged changes (pre-commit)
#   scripts/validate-skills.sh --strict  # treat warnings as errors

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
SKILLS_REF_PKG="git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
MIN_PYTHON_MINOR=11  # skills-ref requires Python >= 3.11
STAGED_ONLY=0
STRICT=0

for arg in "$@"; do
  case "$arg" in
    --staged) STAGED_ONLY=1 ;;
    --strict) STRICT=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# ── Check Python version ─────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
  echo "error: python3 is required (>= 3.${MIN_PYTHON_MINOR}) but not found" >&2
  echo "  Install from https://python.org or via your package manager" >&2
  exit 1
fi

python_minor=$(python3 -c 'import sys; print(sys.version_info.minor)')
python_major=$(python3 -c 'import sys; print(sys.version_info.major)')

if [[ $python_major -lt 3 || ($python_major -eq 3 && $python_minor -lt $MIN_PYTHON_MINOR) ]]; then
  python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  echo "error: python3 >= 3.${MIN_PYTHON_MINOR} required, found ${python_version}" >&2
  exit 1
fi

# ── Locate or install skills-ref ─────────────────────────────────────────────

find_skills_ref() {
  if command -v skills-ref &>/dev/null; then
    command -v skills-ref
    return 0
  fi
  if [[ -x "$REPO_ROOT/.venv/bin/skills-ref" ]]; then
    echo "$REPO_ROOT/.venv/bin/skills-ref"
    return 0
  fi
  return 1
}

install_skills_ref() {
  echo "skills-ref not found — installing into .venv ..."

  if command -v uv &>/dev/null; then
    if uv tool install "$SKILLS_REF_PKG" &>/dev/null; then
      if command -v skills-ref &>/dev/null; then
        command -v skills-ref; return 0
      fi
    fi
  fi

  [[ -x "$REPO_ROOT/.venv/bin/python" ]] || python3 -m venv "$REPO_ROOT/.venv"
  "$REPO_ROOT/.venv/bin/pip" install --quiet "$SKILLS_REF_PKG" || {
    echo "error: could not install skills-ref" >&2
    echo "  python3 -m venv .venv && .venv/bin/pip install '$SKILLS_REF_PKG'" >&2
    return 1
  }
  echo "$REPO_ROOT/.venv/bin/skills-ref"
}

SKILLS_REF="$(find_skills_ref || install_skills_ref)" || exit 1

# ── Find skill directories ────────────────────────────────────────────────────

# All skill dirs: parent of every SKILL.md matching */skills/*/SKILL.md
all_skill_dirs=()
while IFS= read -r skill_md; do
  all_skill_dirs+=("$(dirname "$skill_md")")
done < <(find "$REPO_ROOT"/cirra-ai-* -path "*/.git" -prune -o -path "*/skills/*/SKILL.md" -print 2>/dev/null | sort)

if [[ $STAGED_ONLY -eq 1 ]]; then
  # Only validate dirs that contain staged files
  skill_dirs=()
  while IFS= read -r staged_file; do
    staged_path="$REPO_ROOT/$staged_file"
    for dir in "${all_skill_dirs[@]}"; do
      if [[ "$staged_path" == "$dir"/* || "$staged_path" == "$dir" ]]; then
        skill_dirs+=("$dir")
        break
      fi
    done
  done < <(git diff --cached --name-only)
  # Deduplicate
  if [[ ${#skill_dirs[@]} -gt 0 ]]; then
    IFS=$'\n' read -r -d '' -a skill_dirs < <(printf '%s\n' "${skill_dirs[@]}" | sort -u && printf '\0') || true
  fi
else
  skill_dirs=("${all_skill_dirs[@]}")
fi

[[ ${#skill_dirs[@]} -eq 0 ]] && exit 0

# ── Custom checks ─────────────────────────────────────────────────────────────

# Returns warnings for a skill dir (one per line, no trailing newline).
custom_checks() {
  local dir="$1"
  local skill_md="$dir/SKILL.md"

  # Missing LICENSE
  if [[ ! -f "$dir/LICENSE" ]]; then
    echo "missing LICENSE file"
  fi

  # Hooks in SKILL.md frontmatter — hooks belong in the plugin's hooks/hooks.json,
  # not in individual skill files, so they work correctly when installed standalone.
  if python3 - "$skill_md" <<'PYEOF' 2>/dev/null; then
import sys
content = open(sys.argv[1]).read()
if content.startswith('---\n'):
    end = content.index('\n---\n', 4)
    keys = [l.split(':')[0].strip() for l in content[4:end].split('\n')
            if l and not l[0].isspace()]
    sys.exit(0 if 'hooks' not in keys else 1)
PYEOF
    :
  else
    echo "hooks key in SKILL.md frontmatter (move to plugin hooks/hooks.json)"
  fi
}

# ── Validate ─────────────────────────────────────────────────────────────────

errors=0
warnings=0

for dir in "${skill_dirs[@]}"; do
  rel="${dir#"$REPO_ROOT"/}"

  # Run skills-ref validator
  ref_output=$("$SKILLS_REF" validate "$dir" 2>&1)
  ref_rc=$?

  ref_errors=""
  if [[ $ref_rc -ne 0 ]]; then
    ref_errors=$(printf '%s\n' "$ref_output" | grep "^  - ")
  fi

  # Run custom checks
  skill_warnings=$(custom_checks "$dir")

  if [[ -z "$ref_errors" && -z "$skill_warnings" ]]; then
    echo "✓  $rel"
    continue
  fi

  echo "✗  $rel"

  if [[ -n "$ref_errors" ]]; then
    printf '%s\n' "$ref_errors" | sed 's/^  - /   error: /'
    errors=$((errors + 1))
  fi

  if [[ -n "$skill_warnings" ]]; then
    printf '%s\n' "$skill_warnings" | sed 's/^/   warn:  /'
    warnings=$((warnings + 1))
  fi
done

if [[ $warnings -gt 0 ]]; then
  echo ""
  echo "  $warnings skill(s) with warnings"
fi

if [[ $errors -gt 0 ]]; then
  echo ""
  echo "  $errors skill(s) with errors"
fi

if [[ $errors -gt 0 ]]; then
  exit 1
fi

if [[ $STRICT -eq 1 && $warnings -gt 0 ]]; then
  exit 1
fi

exit 0
