#!/usr/bin/env python3
"""Detect Salesforce API names corrupted by Markdown strong-emphasis.

A pair of ``__`` is Markdown strong-emphasis, so a bare ``Amount__c to Invoice__c``
written in prose is rewritten by ``prettier --write`` (which every push runs) into
``Amount**c to Invoice**c``. The API name is now wrong and renders as bold, and
prettier reports the file as merely reformatted — so the corruption is silent and
has shipped in published docs more than once.

The fix is to write API names inside backticks (emphasis does not apply inside a
code span, so prettier leaves them alone) or, in plain text, to escape both pairs
as ``Invoice\\_\\_c``.

Usage:
    python3 scripts/check_md_api_names.py [PATH ...]

PATH may be a Markdown file or a directory (searched recursively for ``*.md``).
Defaults to the ``skills/`` tree. Exits 1 if any corrupted name is found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Salesforce API-name suffixes that follow a `__` separator. A corrupted name is
# therefore "<word chars>**<suffix><end of token>".
SUFFIXES = [
    "ChangeEvent",
    "History",
    "Share",
    "Feed",
    "Tag",
    "kav",
    "mdt",
    "pc",
    "pr",
    "c",
    "r",
    "e",
    "b",
    "x",
]

# Require a word character immediately BEFORE the `**` so ordinary bold markup
# (`**Feed**`, `- **P**ositive`) can never match — those have whitespace or
# punctuation there. Require a word boundary immediately AFTER the suffix so
# acronym bolding (`**S**ingle`, `**B**ulk`) can never match either: there the
# text after `**` continues into a longer word.
PATTERN = re.compile(r"[A-Za-z0-9_]\*\*(?:" + "|".join(SUFFIXES) + r")\b")

# Escape hatch for a deliberate case the pattern misreads. Put it on the offending
# line (or the line above) and the check skips it.
WAIVER = "md-api-names: allow"

FENCE_RE = re.compile(r"^\s*(```|~~~)")
# Inline code spans. A match inside one cannot be this defect: prettier does not
# apply emphasis inside a code span, so a corrupted name can only appear in prose.
CODE_SPAN_RE = re.compile(r"`[^`]*`")


def scrub(line: str) -> str:
    """Blank out inline code spans so their contents are not matched."""
    return CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)), line)


def check_file(path: Path) -> list[tuple[int, str]]:
    """Return [(line_number, line_text)] for each corrupted API name in *path*."""
    findings: list[tuple[int, str]] = []
    in_fence = False
    previous = ""

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            previous = raw
            continue
        # Fenced blocks are literal text — prettier does not reformat their
        # contents, so `2**32` and pasted output are not defects.
        if in_fence:
            previous = raw
            continue
        if WAIVER in raw or WAIVER in previous:
            previous = raw
            continue
        if PATTERN.search(scrub(raw)):
            findings.append((lineno, raw.strip()))
        previous = raw

    return findings


def iter_markdown(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md":
            files.append(p)
    return files


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] or [repo_root / "skills"]

    total = 0
    for md in iter_markdown(targets):
        for lineno, text in check_file(md):
            rel = md.relative_to(repo_root) if md.is_relative_to(repo_root) else md
            print(f"{rel}:{lineno}: API name corrupted by Markdown emphasis: {text}")
            total += 1

    if total:
        print(
            f"\n{total} corrupted API name(s). A `__` pair is strong-emphasis, so prettier\n"
            "rewrote `Object__c` into `Object**c`. Fix by wrapping the name in backticks\n"
            "(`Invoice__c`) or escaping both pairs in plain text (Invoice\\_\\_c), then\n"
            f"re-run prettier. For a deliberate case, add `{WAIVER}` to the line.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
