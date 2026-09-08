#!/usr/bin/env python3
"""Flag MCP tool calls in skill Markdown that do not match the Cirra AI MCP Server schemas.

Checks (all inside Markdown under the given roots, default ``skills/``):

1. ``soql_query`` / ``tooling_api_query`` called with a ``query=`` argument.
   Both tools take ``sObject``, ``fields`` and ``whereClause`` (all required);
   there is no ``query`` parameter.
2. ``soql_query(...)`` / ``tooling_api_query(...)`` calls that omit ``fields`` or
   ``whereClause``.
3. ``sobject_dml(...)`` delete calls that pass ``records`` instead of ``recordIds``.
4. ``sobject_dml`` / ``soql_query`` / ``tooling_api_query`` called with ``sobjectType=``
   (the parameter is ``sObject``).
5. ``sobject_dml(...)`` with ``operation="create"`` (the enum is ``insert``).
6. ``whereClause`` values that smuggle ``ORDER BY`` / ``LIMIT`` / ``GROUP BY`` in; those
   belong in ``orderBy=`` / ``limit=`` / ``groupBy=``.
7. Any of the three tools called with ``orgAlias=`` (the connection selector is ``sf_user=``).

Only fenced code blocks and inline code spans are scanned, since prose never
carries a literal call. Put ``<!-- mcp-signatures: allow -->`` on the line
above a call (or above the opening fence, for the first call in a block) to opt
out, e.g. for an example that shows the *wrong* call on purpose.

Exit status is 1 when any finding is reported, so the script doubles as a CI check.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

QUERY_TOOLS = ("soql_query", "tooling_api_query")
ALLOW_MARKER = "mcp-signatures: allow"

FENCE_RE = re.compile(r"^(```|~~~)")
CALL_RE = re.compile(r"\b(soql_query|tooling_api_query|sobject_dml)\s*\(")
KWARG_RE = re.compile(r"(?<![\w.])(\w+)\s*=")


class Finding:
    def __init__(self, path: Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _code_regions(text: str) -> list[tuple[int, str]]:
    """Return (start_line_number, code_text) for every fenced block and inline span."""
    regions: list[tuple[int, str]] = []
    lines = text.split("\n")
    in_fence = False
    fence_start = 0
    buf: list[str] = []
    for i, line in enumerate(lines, start=1):
        if FENCE_RE.match(line.strip()):
            if in_fence:
                regions.append((fence_start, "\n".join(buf)))
                buf = []
                in_fence = False
            else:
                in_fence = True
                fence_start = i + 1
            continue
        if in_fence:
            buf.append(line)
        else:
            for m in re.finditer(r"`([^`\n]+)`", line):
                regions.append((i, m.group(1)))
    if in_fence and buf:
        regions.append((fence_start, "\n".join(buf)))
    return regions


def _extract_call(code: str, start: int) -> tuple[str, int] | None:
    """Given index of the opening paren, return (argument text, end index)."""
    depth = 0
    i = start
    while i < len(code):
        ch = code[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return code[start + 1 : i], i
        i += 1
    return None


def _kwargs(args: str) -> set[str]:
    """Return the top-level keyword-argument names in a call's argument text.

    Skips anything inside quoted strings (so `whereClause="Name LIKE '%query=%'"`
    does not yield a `query` kwarg) and inside dict/list literals (so record
    keys are not mistaken for kwargs).
    """
    flat: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    for ch in args:
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            flat.append(" ")  # keep token boundaries intact
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif depth == 0:
            flat.append(ch)
    return {m.group(1) for m in KWARG_RE.finditer("".join(flat))}


def _allowed(lines: list[str], line_no: int) -> bool:
    # The marker may sit on the call's line, the line above it, or the line above
    # the opening fence of the block that holds it (two lines up for the first
    # statement in a fenced block).
    for n in (line_no, line_no - 1, line_no - 2):
        if 1 <= n <= len(lines) and ALLOW_MARKER in lines[n - 1]:
            return True
    return False


def check_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    findings: list[Finding] = []
    for region_start, code in _code_regions(text):
        for m in CALL_RE.finditer(code):
            tool = m.group(1)
            extracted = _extract_call(code, m.end() - 1)
            if extracted is None:
                continue
            args, _ = extracted
            line_no = region_start + code.count("\n", 0, m.start())
            if _allowed(lines, line_no):
                continue
            kw = _kwargs(args)
            if "orgAlias" in kw:
                findings.append(Finding(path, line_no, f"{tool}: no `orgAlias=` parameter; use `sf_user=`"))
            where = re.search(r"whereClause\s*=\s*(['\"])(.*?)\1", args, re.S)
            if where and re.search(r"\b(ORDER BY|LIMIT|GROUP BY)\b", where.group(2), re.I):
                findings.append(
                    Finding(path, line_no, f"{tool}: ORDER BY/LIMIT/GROUP BY belong in orderBy=/limit=/groupBy=, not whereClause")
                )
            if "sobjectType" in kw:
                findings.append(Finding(path, line_no, f"{tool}: use `sObject=`, not `sobjectType=`"))
            if tool in QUERY_TOOLS:
                if "query" in kw:
                    findings.append(
                        Finding(path, line_no, f"{tool}: no `query=` parameter; use sObject/fields/whereClause")
                    )
                    continue
                for required in ("sObject", "fields", "whereClause"):
                    if required not in kw:
                        findings.append(Finding(path, line_no, f"{tool}: missing required `{required}=`"))
            elif tool == "sobject_dml":
                op = re.search(r"operation\s*=\s*['\"](\w+)['\"]", args)
                if op and op.group(1) == "delete" and "records" in kw:
                    findings.append(Finding(path, line_no, "sobject_dml delete: use `recordIds=`, not `records=`"))
                if op and op.group(1) == "create":
                    findings.append(Finding(path, line_no, "sobject_dml: operation is `insert`, not `create`"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("roots", nargs="*", default=["skills"], help="directories or files to scan")
    ns = parser.parse_args(argv)

    findings: list[Finding] = []
    for root in ns.roots:
        p = Path(root)
        files = [p] if p.is_file() else sorted(f for f in p.rglob("*.md") if "__pycache__" not in f.parts)
        for f in files:
            findings.extend(check_file(f))

    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} MCP signature problem(s) found", file=sys.stderr)
        return 1
    print("MCP signatures OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
