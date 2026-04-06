#!/usr/bin/env bash
# Builds a zip bundle containing the dispatch test runner, validation script,
# and all per-skill dispatch-tests.md files.
# The resulting zip is intended for running tests against installed skills
# (SKILL.md files are NOT included — they come from the installed plugins).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO_ROOT/tests/dispatch-test-bundle.zip"

cd "$REPO_ROOT"

rm -f "$OUT"

zip -r "$OUT" \
  tests/DISPATCH-TEST-RUNNER.md \
  tests/validate_dispatch_tests.py \
  skills/sf-*/tests/dispatch-tests.md

echo "Created $OUT ($(du -h "$OUT" | cut -f1) — $(zipinfo -1 "$OUT" | wc -l | tr -d ' ') files)"
