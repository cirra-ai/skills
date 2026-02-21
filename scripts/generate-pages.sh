#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 "$REPO_ROOT/scripts/generate-pages.py" "$REPO_ROOT" > "$REPO_ROOT/docs/index.html"

echo "Generated docs/index.html"
