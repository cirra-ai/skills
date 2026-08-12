#!/usr/bin/env python3
"""Extract large ## sections from SKILL.md into references/ and leave stubs.

Usage:
  python3 scripts/extract_skill_sections.py skills/sf-flow \\
    --section "Workflow Design (5-Phase Pattern)" \\
    --out references/workflow-design.md \\
    --stub "See [Workflow Design](references/workflow-design.md) for the full 5-phase pattern."
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def find_section_range(lines: list[str], title: str) -> tuple[int, int]:
    """Return [start, end) line indexes for a ## section matching title."""
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and title in line:
            start = i
            break
    if start is None:
        raise SystemExit(f"Section not found: {title!r}")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return start, end


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--section", required=True, help="## section title to extract")
    parser.add_argument("--out", required=True, help="Path relative to skill dir")
    parser.add_argument("--stub", required=True, help="Replacement markdown stub")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    skill_dir = args.skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    raw = skill_md.read_text().splitlines()
    start, end = find_section_range(raw, args.section)

    extracted = "\n".join(raw[start:end]).rstrip() + "\n"
    out_path = skill_dir / args.out
    stub_block = args.stub.rstrip() + "\n\n"

    new_lines = raw[:start] + [stub_block.rstrip("\n"), ""] + raw[end:]
    # Collapse excessive blank lines around the stub
    body = "\n".join(new_lines)
    body = re.sub(r"\n{3,}", "\n\n", body)
    if not body.endswith("\n"):
        body += "\n"

    print(f"{skill_dir.name}: extract L{start+1}-L{end} ({end-start} lines) → {args.out}")
    if args.dry_run:
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        # Prepend extracted content under a separator if file already exists
        existing = out_path.read_text()
        out_path.write_text(existing.rstrip() + "\n\n---\n\n" + extracted)
    else:
        out_path.write_text(extracted)
    skill_md.write_text(body)
    print(f"  SKILL.md now {len(body.splitlines())} lines")


if __name__ == "__main__":
    main()
