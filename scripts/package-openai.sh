#!/usr/bin/env bash
set -euo pipefail

# Build ChatGPT / Codex distribution under dist/openai/ and zip to install/openai/.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_ZIP_DIR="$REPO_ROOT/install/openai"

echo "=== Assembling shared content ==="
"$SCRIPT_DIR/assemble.sh"
echo ""

# Ensure SVG icon is present in shared assets and synced into skill assets for source.
if [[ ! -f "$REPO_ROOT/shared/assets/icon.svg" ]]; then
  echo "error: shared/assets/icon.svg is required" >&2
  exit 1
fi

# Copy icon.svg into each skill (source tree convenience; packaging also injects it)
for skill_dir in "$REPO_ROOT"/skills/*/; do
  [[ -f "$skill_dir/SKILL.md" ]] || continue
  mkdir -p "$skill_dir/assets"
  cp "$REPO_ROOT/shared/assets/icon.svg" "$skill_dir/assets/icon.svg"
done

python3 "$SCRIPT_DIR/package_openai.py"

echo ""
echo "=== Validating OpenAI distro ==="
python3 "$SCRIPT_DIR/validate_openai_dist.py"

rm -rf "$OUT_ZIP_DIR"
mkdir -p "$OUT_ZIP_DIR"
(
  cd "$REPO_ROOT/dist"
  zip -r -q "$OUT_ZIP_DIR/cirra-ai-sf-openai.zip" openai \
    -x "*.DS_Store" "*__pycache__*" "*.pyc"
)

echo ""
echo "=== Done ==="
echo "Tree: $REPO_ROOT/dist/openai"
echo "Zip:  $OUT_ZIP_DIR/cirra-ai-sf-openai.zip"
ls -lh "$OUT_ZIP_DIR"/*.zip
