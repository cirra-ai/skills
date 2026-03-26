"""Phase 1 static validator for dispatch-tests.md files.

Parses each skill's SKILL.md and dispatch-tests.md, then mechanically
verifies every assertion. No LLM involved — pure string matching.

Usage:
    python tests/validate_dispatch_tests.py              # all skills
    python tests/validate_dispatch_tests.py sf-metadata   # one skill
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def extract_backtick_names(text: str) -> set[str]:
    """Extract all backtick-quoted tool/skill names from a string."""
    return set(re.findall(r"`([a-z_]+)`", text))


def extract_all_tool_refs(text: str) -> set[str]:
    """Extract tool names from SKILL.md — matches backtick-quoted names AND function call patterns.

    Matches:
    - `tool_name` (backtick-quoted)
    - tool_name() or tool_name( (function call syntax in code blocks)
    """
    backtick = set(re.findall(r"`([a-z_]+)`", text))
    call_pattern = set(re.findall(r"\b([a-z_]{3,})\(", text))
    return backtick | call_pattern


def parse_skill_md(path: Path) -> dict:
    """Parse a SKILL.md and extract structured data."""
    content = path.read_text()

    # Frontmatter
    fm = {}
    if content.startswith("---"):
        end = content.index("---", 3)
        fm_text = content[3:end]
        for line in fm_text.strip().split("\n"):
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()

    # All tool names in the entire file (backtick-quoted + function call patterns)
    all_tools = extract_all_tool_refs(content)

    # Dispatch table workflows
    dispatch_workflows = set()
    dispatch_match = re.search(
        r"## Dispatch\b.*?\n(.*?)(?=\n## |\Z)", content, re.DOTALL
    )
    if dispatch_match:
        table_text = dispatch_match.group(1)
        for line in table_text.split("\n"):
            if line.strip().startswith("|") and not re.match(r"^\|\s*-", line):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 2 and cols[0] and "First argument" not in cols[0]:
                    # Strip markdown link formatting: [Text](#anchor) → Text
                    workflow = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cols[1])
                    dispatch_workflows.add(workflow)

    # Menu options (from blockquote)
    menu_options = []
    menu_match = re.search(r">\s*\d+\.\s+\*\*(.+?)\*\*", content)
    if menu_match:
        menu_options = re.findall(r">\s*\d+\.\s+\*\*(.+?)\*\*", content)

    # Argument hint
    arg_hint = fm.get("argument-hint", "")
    hint_keywords = set(re.findall(r"[a-z][-a-z]*", arg_hint))

    return {
        "tools": all_tools,
        "dispatch_workflows": dispatch_workflows,
        "menu_options": menu_options,
        "hint_keywords": hint_keywords,
        "argument_hint": arg_hint,
    }


def parse_test_cases(path: Path) -> list[dict]:
    """Parse a dispatch-tests.md into structured test cases."""
    content = path.read_text()
    cases = []

    sections = re.split(r"\n---\n", content)
    for section in sections:
        name_match = re.search(r"## (.+)", section)
        if not name_match:
            continue

        case = {"name": name_match.group(1), "raw": section}

        # Extract fields
        for field, key in [
            ("Input", "input"),
            ("Dispatch", "dispatch"),
            ("Init required", "init_required"),
            ("Init timing", "init_timing"),
            ("Path", "path"),
            ("First tool", "first_tool"),
            ("Tool params", "tool_params"),
            ("Should call", "should_call"),
            ("Should NOT call", "should_not_call"),
            ("Should ask user", "should_ask_user"),
            ("Menu options", "menu_options"),
            ("Follow-up skills", "follow_up_skills"),
        ]:
            # For Menu options, capture multi-line content until next field or Notes
            if key == "menu_options":
                match = re.search(
                    rf"\*\*{re.escape(field)}\*\*:\s*(.+?)(?=\n- \*\*|\n\*\*Notes|\Z)",
                    section, re.DOTALL
                )
            else:
                match = re.search(
                    rf"\*\*{re.escape(field)}\*\*:\s*(.+?)(?:\n|$)", section
                )
            if match:
                case[key] = match.group(1).strip()

        # Extract Notes
        notes_match = re.search(r"\*\*Notes\*\*:\s*(.+?)(?:\n---|\Z)", section, re.DOTALL)
        if notes_match:
            case["notes"] = notes_match.group(1).strip()

        cases.append(case)

    return cases


def extract_tool_names(field_value: str) -> set[str]:
    """Extract backtick-quoted tool names from a test field value."""
    return set(re.findall(r"`([a-z_]+)`", field_value))


class Issue:
    def __init__(self, skill: str, test_case: str, check: str, message: str, severity: str = "DEFECT"):
        self.skill = skill
        self.test_case = test_case
        self.check = check
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"{self.severity}: {self.skill} / \"{self.test_case}\" / {self.check}\n  {self.message}"


def validate_skill(skill_name: str) -> list[Issue]:
    """Run all Phase 1 checks for a skill. Returns list of issues."""
    skill_dir = SKILLS_DIR / skill_name
    skill_md_path = skill_dir / "SKILL.md"
    test_path = skill_dir / "tests" / "dispatch-tests.md"

    issues = []

    if not skill_md_path.exists():
        issues.append(Issue(skill_name, "(all)", "setup", "SKILL.md not found"))
        return issues

    if not test_path.exists():
        issues.append(Issue(skill_name, "(all)", "setup", "dispatch-tests.md not found"))
        return issues

    skill = parse_skill_md(skill_md_path)
    cases = parse_test_cases(test_path)

    for case in cases:
        name = case["name"]

        # === 1.1 Dispatch Table Coverage ===
        dispatch = case.get("dispatch", "")
        if dispatch and not dispatch.startswith("("):
            # Should match a workflow in the dispatch table
            if skill["dispatch_workflows"] and dispatch not in skill["dispatch_workflows"]:
                issues.append(Issue(
                    skill_name, name, "1.1 Dispatch Table",
                    f"Dispatch value \"{dispatch}\" not found in SKILL.md dispatch table. "
                    f"Available: {skill['dispatch_workflows']}"
                ))

        # === 1.2 Argument-Hint Completeness ===
        input_val = case.get("input", "")
        if input_val and skill["hint_keywords"]:
            # Extract the first word after /skill-name
            words = input_val.split()
            if len(words) > 1:
                first_word = words[1].lower()
                # Only check explicit keywords, not natural language
                if re.match(r"^[a-z][-a-z]*$", first_word) and first_word not in skill["hint_keywords"]:
                    # Might be an argument value, not a keyword — only flag if it looks like a dispatch keyword
                    if first_word in ("create", "update", "delete", "validate", "describe",
                                      "query", "build-query", "insert", "upsert",
                                      "hierarchy", "audit", "analyze", "clone", "agent-access",
                                      "quote", "order", "contract", "renewal", "subscription",
                                      "full", "apex", "flow", "lwc", "metadata", "permissions",
                                      "oauth", "erd", "integration", "landscape", "agentforce",
                                      "return", "case"):
                        if first_word not in skill["hint_keywords"]:
                            issues.append(Issue(
                                skill_name, name, "1.2 Argument-Hint",
                                f"First word \"{first_word}\" not in argument-hint: {skill['argument_hint']}",
                                severity="WARN"
                            ))

        # === 1.3 Tool References ===
        should_call = extract_tool_names(case.get("should_call", ""))
        should_not_call = extract_tool_names(case.get("should_not_call", ""))
        first_tool_names = extract_tool_names(case.get("first_tool", ""))

        all_expected_tools = should_call | first_tool_names

        # Check tools in Should call exist in SKILL.md
        for tool in all_expected_tools:
            if tool and tool not in skill["tools"]:
                issues.append(Issue(
                    skill_name, name, "1.3 Tool References",
                    f"Tool `{tool}` in Should call / First tool not found in SKILL.md"
                ))

        # Check Should NOT call tools don't also appear in Should call
        overlap = should_call & should_not_call
        if overlap:
            issues.append(Issue(
                skill_name, name, "1.3 Tool Conflict",
                f"Tool(s) {overlap} appear in BOTH Should call AND Should NOT call"
            ))

        # === 1.4 Menu Options ===
        test_menu = case.get("menu_options", "")
        if test_menu and test_menu.lower() not in ("n/a", "none", "") and skill["menu_options"]:
            for option in skill["menu_options"]:
                if option.lower() not in test_menu.lower():
                    issues.append(Issue(
                        skill_name, name, "1.4 Menu Options",
                        f"SKILL.md menu option \"{option}\" not found in test menu: {test_menu}",
                        severity="WARN"
                    ))

        # === 1.5 Cross-References ===
        follow_up = case.get("follow_up_skills", "")
        if follow_up and follow_up != "none" and follow_up != "n/a":
            for skill_ref in re.findall(r"`(sf-[a-z]+)`", follow_up):
                if not (SKILLS_DIR / skill_ref).exists():
                    issues.append(Issue(
                        skill_name, name, "1.5 Cross-References",
                        f"Follow-up skill `{skill_ref}` directory not found"
                    ))

        # Check for stale references
        if "cirra-ai-sf-" in case.get("raw", ""):
            issues.append(Issue(
                skill_name, name, "1.5 Stale References",
                "Found 'cirra-ai-sf-' in test case (should be 'sf-' prefix)"
            ))

        # === 1.6 Required Fields ===
        required = ["input", "dispatch", "init_required", "init_timing", "path", "should_ask_user"]
        for field in required:
            if field not in case:
                issues.append(Issue(
                    skill_name, name, "1.6 Required Fields",
                    f"Missing required field: {field}"
                ))

        # === 1.7 Init Timing Consistency ===
        init_required = case.get("init_required", "")
        init_timing = case.get("init_timing", "")
        notes = case.get("notes", "")

        if "no" in init_required.lower() and "before-workflow" in init_timing:
            issues.append(Issue(
                skill_name, name, "1.7 Init Consistency",
                f"Init required: {init_required} but Init timing: {init_timing} — contradicts"
            ))

        if "after-menu" in init_timing and "cirra_ai_init" in (case.get("should_call", "") + case.get("first_tool", "")):
            # If init timing is after-menu, cirra_ai_init should NOT be in the "before menu" tool sequence
            if "called first" in notes.lower() or "before" in notes.lower():
                issues.append(Issue(
                    skill_name, name, "1.7 Init Consistency",
                    f"Init timing is after-menu but Notes describe init being called first. "
                    f"Should this be before-menu?"
                ))

    return issues


def main():
    skills = sorted(
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("sf-")
    )

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target not in skills:
            print(f"Unknown skill: {target}")
            print(f"Available: {', '.join(skills)}")
            sys.exit(1)
        skills = [target]

    total_tests = 0
    total_pass = 0
    total_defects = 0
    total_warnings = 0
    all_issues: list[Issue] = []

    print("Phase 1 Static Validation")
    print("=" * 60)
    print()

    for skill_name in skills:
        test_path = SKILLS_DIR / skill_name / "tests" / "dispatch-tests.md"
        if not test_path.exists():
            print(f"  {skill_name}: SKIP (no dispatch-tests.md)")
            continue

        cases = parse_test_cases(test_path)
        issues = validate_skill(skill_name)

        num_tests = len(cases)
        defects = [i for i in issues if i.severity == "DEFECT"]
        warnings = [i for i in issues if i.severity == "WARN"]
        failed_cases = len({i.test_case for i in defects})
        passed = num_tests - failed_cases

        total_tests += num_tests
        total_pass += passed
        total_defects += failed_cases
        total_warnings += len(warnings)
        all_issues.extend(issues)

        status = "PASS" if not defects else "FAIL"
        warn_str = f" ({len(warnings)} warnings)" if warnings else ""
        issue_str = f" ({len(defects)} issues)" if len(defects) > failed_cases else ""
        print(f"  {skill_name}: {num_tests} tests, {passed} pass, {failed_cases} fail{issue_str}{warn_str} [{status}]")

    print()
    print("-" * 60)
    print(f"  TOTAL: {total_tests} tests, {total_pass} pass, {total_defects} fail, {total_warnings} warnings")
    print()

    if all_issues:
        print("Issues:")
        print()
        for issue in all_issues:
            print(f"  {issue}")
            print()

    sys.exit(1 if total_defects > 0 else 0)


if __name__ == "__main__":
    main()
