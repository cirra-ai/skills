#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "${1:-}" == "--preview" ]]; then
  # Open a browser preview without touching docs/index.html
  python3 "$REPO_ROOT/scripts/generate-pages.py" "$REPO_ROOT" --preview "${@:2}"
else
  # CI: write to a temp file first (avoids clobbering the template before it is read),
  # then atomically replace docs/index.html.
  # All extra arguments (e.g. --dl-base=.) are passed through to the generator.
  TMP="$(mktemp)"
  python3 "$REPO_ROOT/scripts/generate-pages.py" "$REPO_ROOT" "$@" > "$TMP"
  mv "$TMP" "$REPO_ROOT/docs/index.html"
  echo "Generated docs/index.html"
fi
