"""Tests for scripts/check_md_api_names.py.

The point of this checker is to run in CI, so its false-positive behavior matters
more than its detection rate: a wrong hit turns someone's build red for a
legitimate document. Every benign construct that exists in this repo today is
pinned below, alongside the real corruptions the checker must catch.
"""

from pathlib import Path

from conftest import load_script

checker = load_script("scripts/check_md_api_names.py")

REPO_ROOT = Path(__file__).parent.parent


def findings(tmp_path: Path, content: str) -> list[tuple[int, str]]:
    md = tmp_path / "doc.md"
    md.write_text(content, encoding="utf-8")
    return checker.check_file(md)


# ── Real corruptions it must catch ───────────────────────────────────────────


def test_detects_corrupted_field_and_object(tmp_path):
    # The exact string Copilot flagged in skills/sf-metadata/README.md.
    assert findings(tmp_path, '"Add a Currency field called Amount**c to Invoice**c"')


def test_detects_namespaced_managed_package_object(tmp_path):
    # The exact shape found in skills/sf-diagram/assets/datamodel/fsl-erd.md.
    assert findings(tmp_path, "| FSL**Scheduling_Policy**c   | Optimization rules    |")


def test_detects_relationship_suffix(tmp_path):
    assert findings(tmp_path, "Traverse Account**r to reach the parent.")


def test_detects_custom_metadata_type_suffix(tmp_path):
    assert findings(tmp_path, "Read the Setting**mdt records first.")


def test_reports_line_number(tmp_path):
    result = findings(tmp_path, "clean line\nbroken Invoice**c here\n")
    assert [lineno for lineno, _ in result] == [2]


# ── Benign constructs it must never flag ─────────────────────────────────────


def test_ignores_acronym_bolding(tmp_path):
    # skills/sf-apex/references/solid-principles.md
    assert not findings(tmp_path, "| **S**ingle Responsibility | One reason to change |")


def test_ignores_pnb_acronym_bolding(tmp_path):
    # skills/sf-apex/SKILL.md
    assert not findings(tmp_path, "- **P**ositive — happy-path test\n- **B**ulk — 251+ records")


def test_ignores_ordinary_bold_words(tmp_path):
    assert not findings(tmp_path, "The record **Feed** and its **Tag** are **c**ompletely fine.")


def test_ignores_bold_label_followed_by_colon(tmp_path):
    # skills/sf-flow/scripts/doc_generator.py emits this shape into Markdown.
    assert not findings(tmp_path, "**Justification**: To be documented")


def test_ignores_inline_code_spans(tmp_path):
    # Emphasis does not apply inside a code span, so this is not the defect —
    # it is the recommended fix, and the counter-example quoted in AGENTS.md.
    assert not findings(tmp_path, "prettier rewrites `Amount__c` into `Amount**c to Invoice**c`")


def test_ignores_fenced_code_blocks(tmp_path):
    assert not findings(tmp_path, "```python\nmask = 2**32 - 1\nname = 'Invoice**c'\n```")


def test_ignores_tilde_fenced_code_blocks(tmp_path):
    assert not findings(tmp_path, "~~~\nInvoice**c\n~~~")


def test_reopens_detection_after_fence_closes(tmp_path):
    assert findings(tmp_path, "```\nInvoice**c\n```\nbroken Invoice**c in prose\n")


def test_ignores_properly_escaped_names(tmp_path):
    assert not findings(tmp_path, "| Create Object | Create Inspection\\_\\_c and Invoice\\_\\_c |")


def test_waiver_on_the_line_suppresses(tmp_path):
    assert not findings(tmp_path, "odd Invoice**c case <!-- md-api-names: allow -->")


def test_waiver_on_previous_line_suppresses(tmp_path):
    assert not findings(tmp_path, "<!-- md-api-names: allow -->\nodd Invoice**c case")


# ── The live repository must stay clean ──────────────────────────────────────


def test_skills_tree_is_clean():
    """The source of truth must pass — this is what CI enforces."""
    offenders = {
        str(md.relative_to(REPO_ROOT)): checker.check_file(md)
        for md in sorted((REPO_ROOT / "skills").rglob("*.md"))
        if checker.check_file(md)
    }
    assert offenders == {}


def test_root_policy_docs_are_clean():
    """AGENTS.md and CLAUDE.md quote the corrupted form as a counter-example.

    They are outside the scanned tree, but the counter-examples are inside
    backticks, so they would not trip the checker even if they were scanned.
    """
    for name in ("AGENTS.md", "CLAUDE.md"):
        assert checker.check_file(REPO_ROOT / name) == []
