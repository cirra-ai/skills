#!/usr/bin/env python3
"""
Apex Validator for Cirra AI skills plugin.

Validates Salesforce Apex code (.cls, .trigger) for common anti-patterns
and best practice violations.

Scoring Categories (150 points total):
1. Bulkification (25 pts): SOQL/DML in loops
2. Security (25 pts): sharing settings, FLS, SOQL injection
3. Testing (25 pts): assertions, SeeAllData, Test.startTest, @TestSetup, bulk tests
4. Architecture (20 pts): class size, public surface, trigger logic, hardcoded IDs
5. Clean Code (20 pts): naming, complexity, comments
6. Error Handling (15 pts): try-catch, custom exceptions
7. Performance (10 pts): unbounded SOQL, getGlobalDescribe, @future, System.debug
8. Documentation (10 pts): ApexDoc, inline comments

Severity scale (single vocabulary shared by every sf-apex / sf-audit script,
ordered worst-first, matching Salesforce Code Analyzer):
    CRITICAL > HIGH > MODERATE > LOW > INFO
Legacy labels are normalised: WARNING -> MODERATE, ERROR -> HIGH, MEDIUM -> MODERATE.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Severity vocabulary — defined ONCE here; other scripts import or re-declare
# this list verbatim.
# ---------------------------------------------------------------------------

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MODERATE", "LOW", "INFO"]
SEVERITY_RANK = {name: rank for rank, name in enumerate(SEVERITY_ORDER)}
LEGACY_SEVERITY_MAP = {
    "WARNING": "MODERATE",
    "WARN": "MODERATE",
    "ERROR": "HIGH",
    "MEDIUM": "MODERATE",
    "MED": "MODERATE",
    "MINOR": "LOW",
    "MAJOR": "HIGH",
}
SEVERITY_ICONS = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MODERATE": "🟡",
    "LOW": "🔵",
    "INFO": "⚪",
}

MAX_SCORE = 150
# Percentage of MAX_SCORE below which deployment is blocked / a component
# needs review. Shared with validate_apex_cli.py, pre-mcp-validate.py and
# sf-audit/scripts/pre_score.py.
THRESHOLD_PCT = 70


def normalize_severity(value, default: str = "MODERATE") -> str:
    """Map any severity label (including legacy ones) onto SEVERITY_ORDER."""
    if value is None:
        return default
    label = str(value).strip().upper()
    if label in SEVERITY_RANK:
        return label
    return LEGACY_SEVERITY_MAP.get(label, default)


def severity_rank(value) -> int:
    """Sort key: 0 for CRITICAL ... 4 for INFO. Unknown labels sort last."""
    return SEVERITY_RANK[normalize_severity(value, "INFO")]


def severity_icon(value) -> str:
    return SEVERITY_ICONS.get(normalize_severity(value, "INFO"), "⚪")


# ---------------------------------------------------------------------------
# Source-text helpers
# ---------------------------------------------------------------------------

_STRING_LITERAL_RE = re.compile(r"'(?:[^'\\]|\\.)*'")


def _strip_comments(lines: list[str]) -> list[str]:
    """Return a copy of *lines* with // and /* */ comments blanked out.

    String literals are preserved (so `'http://x'` is not treated as a
    comment start) and line count/positions are kept stable.
    """
    out = []
    in_block = False
    for line in lines:
        buf = []
        i = 0
        in_str = False
        while i < len(line):
            ch = line[i]
            if in_block:
                if line.startswith("*/", i):
                    in_block = False
                    i += 2
                else:
                    i += 1
                continue
            if in_str:
                buf.append(ch)
                if ch == "\\" and i + 1 < len(line):
                    buf.append(line[i + 1])
                    i += 2
                    continue
                if ch == "'":
                    in_str = False
                i += 1
                continue
            if ch == "'":
                in_str = True
                buf.append(ch)
                i += 1
                continue
            if line.startswith("//", i):
                break
            if line.startswith("/*", i):
                in_block = True
                i += 2
                continue
            buf.append(ch)
            i += 1
        out.append("".join(buf))
    return out


def _strip_strings(line: str) -> str:
    return _STRING_LITERAL_RE.sub("''", line)


def _is_comment_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*")


# Method declaration on a single line: [annotations] [modifiers] ReturnType name(
_METHOD_RE = re.compile(
    r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*"
    r"((?:(?:public|private|protected|global|static|override|virtual|abstract|"
    r"testmethod|webservice|final)\s+)*)"
    r"([\w<>,.\[\] ]+?)\s+(\w+)\s*\(",
    re.IGNORECASE,
)
_NOT_METHOD_WORDS = {
    "if", "for", "while", "switch", "catch", "return", "new", "else", "throw",
    "case", "when", "do", "try", "finally", "class", "interface", "enum",
}
_DML_RE = re.compile(
    r"\b(insert|update|delete|upsert|undelete|merge)\s+|Database\.(insert|update|delete|upsert|undelete|merge)\s*\(",
    re.IGNORECASE,
)
_SOQL_RE = re.compile(r"\[\s*SELECT\b(.*?)\]", re.IGNORECASE | re.DOTALL)
_ASSERT_RE = re.compile(r"\bAssert\.\w+\s*\(|\bSystem\.assert\w*\s*\(", re.IGNORECASE)
_LEGACY_ASSERT_RE = re.compile(r"\bSystem\.assert(?:Equals|NotEquals)?\s*\(", re.IGNORECASE)
_ASYNC_CALL_RE = re.compile(
    r"\b(?:System\.enqueueJob|Database\.executeBatch|System\.schedule|System\.scheduleBatch)\s*\(",
    re.IGNORECASE,
)
_HARDCODED_ID_RE = re.compile(r"'([a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})'")
_NUMBER_RE = re.compile(r"(?<![\w.])(\d+)(?![\w.])")


class ApexValidator:
    """Validates Apex code for best practices."""

    def __init__(self, file_path: str, api_version: float | None = None):
        """
        Initialize the validator with an Apex file.

        Args:
            file_path: Path to .cls or .trigger file
            api_version: The ApiVersion the class is (or will be) deployed at.
                Version-sensitive checks (e.g. WITH SECURITY_ENFORCED, removed
                in API 67.0) scale their severity on this. None = unknown.
        """
        self.file_path = file_path
        self.api_version = float(api_version) if api_version is not None else None
        self.content = ""
        self.lines = []
        self.issues = []
        self.scores = {
            "bulkification": 25,
            "security": 25,
            "testing": 25,
            "architecture": 20,
            "clean_code": 20,
            "error_handling": 15,
            "performance": 10,
            "documentation": 10,
        }
        self.max_scores = dict(self.scores)

        # Read file content
        try:
            with open(file_path, encoding="utf-8") as f:
                self.content = f.read()
                self.lines = self.content.split("\n")
        except Exception as e:
            self.issues.append(
                {
                    "severity": "CRITICAL",
                    "category": "file",
                    "message": f"Cannot read file: {e}",
                    "line": 0,
                }
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self) -> dict:
        """
        Run all validations on the Apex file.

        Returns:
            Dictionary with validation results
        """
        if not self.content:
            return {
                "file": os.path.basename(self.file_path),
                "score": 0,
                "max_score": MAX_SCORE,
                "pct": 0.0,
                "threshold_pct": THRESHOLD_PCT,
                "rating": "CRITICAL",
                "issues": self.issues,
            }

        # Derived views of the source, built once and shared by the checks.
        self._code_lines = _strip_comments(self.lines)  # comments gone, strings kept
        self._bare_lines = [_strip_strings(ln) for ln in self._code_lines]  # both gone
        self._code_text = "\n".join(self._code_lines)
        self._is_test_class = bool(re.search(r"@istest\b", self.content, re.IGNORECASE))
        self._is_trigger = bool(
            re.search(r"^\s*trigger\s+\w+\s+on\s+\w+", self._code_text, re.IGNORECASE | re.MULTILINE)
        )
        self._loop_map = self._build_loop_line_map()
        self._methods = self._extract_methods()

        # Run all checks
        self._check_soql_in_loops()
        self._check_dml_in_loops()
        self._check_security_patterns()
        self._check_testing_patterns()
        self._check_architecture()
        self._check_performance()
        self._check_naming_conventions()
        self._check_error_handling()
        self._check_documentation()

        # A category can never go negative.
        for key, value in self.scores.items():
            self.scores[key] = max(0, value)

        total_score = sum(self.scores.values())
        pct = total_score / MAX_SCORE * 100

        # Determine rating
        if total_score >= 135:
            rating = "⭐⭐⭐⭐⭐ Excellent"
        elif total_score >= 112:
            rating = "⭐⭐⭐⭐ Very Good"
        elif total_score >= 90:
            rating = "⭐⭐⭐ Good"
        elif total_score >= 67:
            rating = "⭐⭐ Needs Work"
        else:
            rating = "⭐ Critical Issues"

        return {
            "file": os.path.basename(self.file_path),
            "score": total_score,
            "max_score": MAX_SCORE,
            "pct": round(pct, 1),
            "threshold_pct": THRESHOLD_PCT,
            "rating": rating,
            "scores": self.scores.copy(),
            "issues": self.issues,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_issue(self, severity, category, message, line, fix=None, deduct=0):
        issue = {
            "severity": normalize_severity(severity),
            "category": category,
            "message": message,
            "line": line,
        }
        if fix:
            issue["fix"] = fix
        self.issues.append(issue)
        if deduct and category in self.scores:
            self.scores[category] -= deduct

    def _line_of_offset(self, offset: int) -> int:
        return self._code_text.count("\n", 0, offset) + 1

    def _extract_methods(self) -> list[dict]:
        """Locate method declarations and their bodies (brace-matched)."""
        methods = []
        bare = self._bare_lines
        i = 0
        while i < len(bare):
            m = _METHOD_RE.match(bare[i])
            if not m:
                i += 1
                continue
            modifiers = m.group(1).lower()
            return_type = m.group(2).strip()
            name = m.group(3)
            type_words = {w.lower() for w in re.findall(r"\w+", return_type)}
            if (
                name.lower() in _NOT_METHOD_WORDS
                or type_words & _NOT_METHOD_WORDS
                or "=" in bare[i][: m.start(3)]
            ):
                i += 1
                continue

            # Annotations: same line before modifiers, plus preceding annotation lines.
            annotation_text = bare[i][: m.start(1)]
            j = i - 1
            while j >= 0 and j >= i - 4:
                s = bare[j].strip()
                if s.startswith("@") or s == "":
                    annotation_text += " " + s
                    j -= 1
                else:
                    break

            body_lines, end = self._method_body(i)
            methods.append(
                {
                    "name": name,
                    "line": i + 1,
                    "end_line": end + 1,
                    "modifiers": modifiers,
                    "is_public": bool(re.search(r"\b(public|global)\b", modifiers)),
                    "is_test": bool(re.search(r"@istest\b", annotation_text, re.IGNORECASE))
                    or "testmethod" in modifiers,
                    "is_setup": bool(re.search(r"@testsetup\b", annotation_text, re.IGNORECASE)),
                    "body": "\n".join(body_lines),
                }
            )
            i = max(end, i) + 1
        return methods

    def _method_body(self, start: int) -> tuple[list[str], int]:
        """Return (body lines, end index) for the method declared at *start*."""
        bare = self._bare_lines
        paren_depth = 0
        seen_paren = False
        brace_depth = 0
        in_body = False
        for idx in range(start, len(bare)):
            for ch in bare[idx]:
                if not in_body:
                    if ch == "(":
                        paren_depth += 1
                        seen_paren = True
                    elif ch == ")":
                        paren_depth = max(0, paren_depth - 1)
                    elif seen_paren and paren_depth == 0:
                        if ch == "{":
                            in_body = True
                            brace_depth = 1
                        elif ch == ";":
                            return [], idx  # abstract / interface method
                else:
                    if ch == "{":
                        brace_depth += 1
                    elif ch == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            return bare[start : idx + 1], idx
        return bare[start:], len(bare) - 1

    def _build_loop_line_map(self) -> list[tuple[bool, int, bool]]:
        """Build loop context for every line in the file.

        Returns a list (one entry per line, 1-based index → result[i-1]) of
        (in_loop, loop_start_line, outer_loop_active) tuples.

        Fixes the pending_loop leak that occurs with braceless single-statement
        loop bodies (e.g. ``for (...) doSomething();``): pending_loop is cleared
        when a semicolon is encountered at parenthesis depth 0, preventing the
        next unrelated opening brace from being mis-tagged as a loop body.
        """
        # for/while set pending_loop on the keyword line and wait for a {.
        # do is included here too — do { ... } while (...) — the { may be on the
        # next line, so we treat it like for/while rather than matching do\s*{ inline.
        loop_patterns = [r"\bfor\s*\(", r"\bwhile\s*\(", r"\bdo\b"]
        # do-while closing lines: K&R `} while (cond);` and Allman `while (cond);`
        # (brace already closed on the previous line). Prevent these from being
        # treated as new loop starts. The Allman alternative uses a non-backtracking
        # balanced-paren group anchored to end-of-line so it won't match a real
        # while loop with an inline body (e.g. `while (x) stmt;`).
        DO_WHILE_CLOSE_RE = re.compile(
            r"\}\s*while\s*\(|\bwhile\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*;\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        # Stack entries: ('loop', start_line) or ('other', start_line)
        brace_stack: list[tuple[str, int]] = []
        pending_loop = False
        loop_header_line = 0
        paren_depth = 0
        result = []

        for i, line in enumerate(self.lines, 1):
            is_comment = _is_comment_line(line)

            braceless_body_line = False  # set when ';' ends a braceless loop body
            loop_scope_opened_line = False  # set when a loop scope opens on this line
            # Capture outer loop context BEFORE this line potentially starts a new loop.
            # Used to distinguish a standalone for-each (outer_loop_active=False) from
            # one that is nested inside an enclosing loop (outer_loop_active=True).
            outer_loop_active = any(t == "loop" for t, _ in brace_stack)

            if not is_comment:
                # Strip string literals first so that // inside strings (e.g.
                # 'https://api.com') is not mis-treated as a comment marker.
                # Then strip inline comments so that } inside comments (e.g.
                # `for (...) { // }`) cannot prematurely pop brace_stack.
                line_for_patterns = _strip_strings(line)
                line_for_patterns = re.sub(r"//.*$", "", line_for_patterns)
                line_for_patterns = re.sub(r"/\*.*?\*/", "", line_for_patterns)
                if (not DO_WHILE_CLOSE_RE.search(line_for_patterns) and
                        any(re.search(p, line_for_patterns, re.IGNORECASE) for p in loop_patterns)):
                    pending_loop = True
                    loop_header_line = i
                    paren_depth = 0  # reset for this loop header

                for char in line_for_patterns:
                    if char == "(":
                        paren_depth += 1
                    elif char == ")":
                        paren_depth = max(0, paren_depth - 1)
                    elif char == "{":
                        if pending_loop:
                            brace_stack.append(("loop", loop_header_line))
                            loop_scope_opened_line = True
                            pending_loop = False
                        else:
                            brace_stack.append(("other", i))
                    elif char == "}":
                        if brace_stack:
                            brace_stack.pop()
                    elif char == ";" and paren_depth == 0 and pending_loop:
                        # Semicolon outside parens while waiting for loop body brace:
                        # braceless single-statement body — this line IS inside the loop.
                        braceless_body_line = True
                        pending_loop = False

            in_loop = (
                any(t == "loop" for t, _ in brace_stack)
                or braceless_body_line
                or loop_scope_opened_line
            )
            loop_start = next(
                (ln for t, ln in brace_stack if t == "loop"),
                loop_header_line if (braceless_body_line or loop_scope_opened_line) else 0,
            )
            result.append((in_loop, loop_start, outer_loop_active))

        return result

    # ------------------------------------------------------------------
    # Bulkification
    # ------------------------------------------------------------------

    def _check_soql_in_loops(self):
        """Check for SOQL queries inside loops (critical anti-pattern)."""
        soql_pattern = r"\[\s*SELECT\s+"
        # for-each over SOQL result: for (Type var : [SELECT...]) — the SOQL is the
        # iterable, not inside the body; this is the correct bulkified pattern.
        foreach_soql_pattern = r"\bfor\s*\([^:]+:\s*\["
        loop_map = self._loop_map

        for i, line in enumerate(self.lines, 1):
            if _is_comment_line(line):
                continue
            in_loop, loop_start, outer_loop_active = loop_map[i - 1]
            if in_loop and re.search(soql_pattern, line, re.IGNORECASE):
                # Exempt standalone for-each-over-SOQL only when NOT nested in an outer
                # loop. When outer_loop_active is True, the for-each is inside an
                # enclosing loop, so the SOQL IS executed per outer iteration — a real
                # governor-limit risk that must not be silently skipped.
                if re.search(foreach_soql_pattern, line, re.IGNORECASE) and not outer_loop_active:
                    continue
                self._add_issue(
                    "CRITICAL",
                    "bulkification",
                    f"SOQL query inside loop (loop started line {loop_start})",
                    i,
                    fix="Move SOQL before loop, query all needed records, filter in loop",
                    deduct=10,
                )

    def _check_dml_in_loops(self):
        """Check for DML operations inside loops (critical anti-pattern)."""
        dml_patterns = [
            r"\binsert\s+",
            r"\bupdate\s+",
            r"\bdelete\s+",
            r"\bupsert\s+",
            r"\bundelete\s+",
            r"Database\.(insert|update|delete|upsert)",
        ]
        loop_map = self._loop_map

        for i, line in enumerate(self.lines, 1):
            # Skip comment lines (avoids false positives from words like "update" in JavaDoc)
            if _is_comment_line(line):
                continue
            in_loop, loop_start, _outer = loop_map[i - 1]
            if in_loop:
                for dml_pattern in dml_patterns:
                    if re.search(dml_pattern, line, re.IGNORECASE):
                        self._add_issue(
                            "CRITICAL",
                            "bulkification",
                            f"DML inside loop (loop started line {loop_start})",
                            i,
                            fix="Collect records in loop, perform single DML after loop",
                            deduct=10,
                        )

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def _has_sharing_justification(self, line_num: int) -> bool:
        """True when a comment near the declaration explains the sharing choice."""
        window = self.lines[max(0, line_num - 6) : line_num]
        for text in window:
            stripped = text.strip()
            comment_part = ""
            if _is_comment_line(text):
                comment_part = stripped
            elif "//" in _strip_strings(text):
                comment_part = _strip_strings(text).split("//", 1)[1]
            if comment_part and re.search(r"sharing|system\s*mode", comment_part, re.IGNORECASE):
                return True
        return False

    def _check_security_patterns(self):
        """Check for security-related patterns."""
        # Pattern handles optional modifiers (e.g. "with sharing", "virtual", "abstract")
        # between the access modifier and the "class" keyword.
        class_decl_pattern = r"\b(public|private|global)\b.*?\bclass\s+\w+"
        sharing_pattern = r"\b(with\s+sharing|without\s+sharing|inherited\s+sharing)\b"

        # @IsTest classes run in system mode and do not require sharing declarations.
        is_test_class = self._is_test_class

        # Collect all class declarations: (line_num, has_sharing, is_without_sharing)
        class_declarations = []

        for i, line in enumerate(self.lines, 1):
            if _is_comment_line(line):
                continue
            if re.search(class_decl_pattern, line, re.IGNORECASE):
                has_sharing = bool(re.search(sharing_pattern, line, re.IGNORECASE))
                is_without = bool(re.search(r"\bwithout\s+sharing\b", line, re.IGNORECASE))
                class_declarations.append((i, has_sharing, is_without))

        if class_declarations:
            # Outer class (first declaration) must have an explicit sharing keyword
            # Exception: @IsTest classes run in system mode — sharing is irrelevant
            outer_line, outer_has_sharing, outer_is_without = class_declarations[0]
            if not outer_has_sharing and not is_test_class:
                self._add_issue(
                    "MODERATE",
                    "security",
                    "Class missing explicit sharing declaration",
                    outer_line,
                    fix='Add "with sharing" (recommended) or "inherited sharing" to class declaration',
                    deduct=5,
                )
            elif outer_is_without:
                self._flag_without_sharing(outer_line, inner=False)

            # Inner classes inherit sharing from the outer class — only flag "without sharing"
            for line_num, _has_sharing, is_without in class_declarations[1:]:
                if is_without:
                    self._flag_without_sharing(line_num, inner=True)

        # WITH SECURITY_ENFORCED is removed in API 67.0 (Summer '26): classes at
        # 67.0+ that use it do not compile. At <= 66.0 it still compiles, but
        # WITH USER_MODE (available since API 58.0) is the replacement either way.
        for i, line in enumerate(self.lines, 1):
            if _is_comment_line(line):
                continue
            if re.search(r"\bWITH\s+SECURITY_ENFORCED\b", line, re.IGNORECASE):
                if self.api_version is not None and self.api_version >= 67.0:
                    self._add_issue(
                        "CRITICAL",
                        "security",
                        f"WITH SECURITY_ENFORCED does not compile at API "
                        f"{self.api_version:g} (removed in 67.0)",
                        i,
                        fix="Replace with WITH USER_MODE",
                        deduct=10,
                    )
                elif self.api_version is not None:
                    self._add_issue(
                        "INFO",
                        "security",
                        f"WITH SECURITY_ENFORCED still compiles at API "
                        f"{self.api_version:g} but is removed in 67.0",
                        i,
                        fix="Migrate to WITH USER_MODE before raising ApiVersion to 67.0",
                    )
                else:
                    self._add_issue(
                        "MODERATE",
                        "security",
                        "WITH SECURITY_ENFORCED is removed in API 67.0 "
                        "(the default deploy version) - class will not compile there",
                        i,
                        fix="Replace with WITH USER_MODE, or pin ApiVersion <= 66.0 deliberately",
                        deduct=5,
                    )

        # Check for SOQL injection vulnerability
        dynamic_soql_pattern = r"Database\.query\s*\("
        for i, line in enumerate(self.lines, 1):
            if re.search(dynamic_soql_pattern, line):
                # Check if using String.escapeSingleQuotes
                if "escapeSingleQuotes" not in self.content:
                    self._add_issue(
                        "MODERATE",
                        "security",
                        "Dynamic SOQL without evident escape - potential injection risk",
                        i,
                        fix="Use String.escapeSingleQuotes() or bind variables",
                        deduct=5,
                    )

    def _flag_without_sharing(self, line_num: int, inner: bool):
        prefix = "Inner class" if inner else "Class"
        if self._has_sharing_justification(line_num):
            self._add_issue(
                "INFO",
                "security",
                f'{prefix} uses "without sharing" (justified in comment)',
                line_num,
            )
            return
        self._add_issue(
            "MODERATE",
            "security",
            f'{prefix} uses "without sharing" without a comment justifying it',
            line_num,
            fix='Use "with sharing" / "inherited sharing", or add a comment explaining why '
            "system-mode sharing is required",
            deduct=5,
        )

    # ------------------------------------------------------------------
    # Testing (applies to @IsTest classes only)
    # ------------------------------------------------------------------

    def _check_testing_patterns(self):
        """Score test classes on assertions, SeeAllData, start/stopTest, setup and bulk."""
        if not self._is_test_class:
            return

        test_methods = [m for m in self._methods if m["is_test"] and not m["is_setup"]]

        # 1. Every test method must assert something.
        for m in test_methods:
            if not _ASSERT_RE.search(m["body"]):
                self._add_issue(
                    "CRITICAL",
                    "testing",
                    f"Test method '{m['name']}' has no assertions",
                    m["line"],
                    fix="Add Assert.areEqual / Assert.isTrue with a failure message",
                    deduct=10,
                )

        # 2. Prefer the Assert class over legacy System.assert*.
        for i, line in enumerate(self._code_lines, 1):
            if _LEGACY_ASSERT_RE.search(line):
                self._add_issue(
                    "LOW",
                    "testing",
                    "System.assert* used - prefer the Assert class",
                    i,
                    fix="Use Assert.areEqual / Assert.isTrue / Assert.isNotNull (with a message)",
                    deduct=2,
                )
                break  # one finding per file

        # 3. SeeAllData=true couples tests to org data.
        for i, line in enumerate(self._code_lines, 1):
            if re.search(r"SeeAllData\s*=\s*true", line, re.IGNORECASE):
                self._add_issue(
                    "HIGH",
                    "testing",
                    "SeeAllData=true - test depends on org data",
                    i,
                    fix="Create test data in @TestSetup / a TestDataFactory instead",
                    deduct=10,
                )

        # 4. Async / limit-heavy code should run between Test.startTest/stopTest.
        for m in test_methods:
            if _ASYNC_CALL_RE.search(m["body"]) and not re.search(
                r"Test\.startTest\s*\(", m["body"], re.IGNORECASE
            ):
                self._add_issue(
                    "MODERATE",
                    "testing",
                    f"Test method '{m['name']}' runs async code without Test.startTest()/stopTest()",
                    m["line"],
                    fix="Wrap the async call in Test.startTest(); ... Test.stopTest(); so it executes "
                    "synchronously with fresh limits",
                    deduct=5,
                )

        # 5. Shared data creation belongs in @TestSetup.
        creating = [m for m in test_methods if _DML_RE.search(m["body"])]
        has_setup = any(m["is_setup"] for m in self._methods) or bool(
            re.search(r"@testsetup\b", self._code_text, re.IGNORECASE)
        )
        if len(creating) > 3 and not has_setup:
            self._add_issue(
                "LOW",
                "testing",
                f"{len(creating)} test methods create their own data - no @TestSetup method",
                creating[0]["line"],
                fix="Move shared record creation into an @TestSetup method",
                deduct=3,
            )

        # 6. Bulk test: some loop / factory call sized 200+.
        if test_methods:
            has_bulk = any(
                int(n) >= 200
                for line in self._bare_lines
                for n in _NUMBER_RE.findall(line)
            )
            if not has_bulk:
                self._add_issue(
                    "MODERATE",
                    "testing",
                    "No bulk test detected (no loop or factory call creating 200+ records)",
                    test_methods[0]["line"],
                    fix="Add a test that inserts 200+ records to prove bulk-safety",
                    deduct=5,
                )

    # ------------------------------------------------------------------
    # Architecture
    # ------------------------------------------------------------------

    def _check_architecture(self):
        """Class size, public surface, trigger logic and hardcoded IDs."""
        # 1. Very long classes
        line_count = len(self.lines)
        if line_count > 500:
            self._add_issue(
                "MODERATE",
                "architecture",
                f"Class has {line_count} lines (> 500) - split responsibilities",
                1,
                fix="Extract cohesive behaviour into separate service / selector / domain classes",
                deduct=5,
            )

        # 2. Wide public surface
        public_count = sum(1 for m in self._methods if m["is_public"])
        if public_count > 20:
            self._add_issue(
                "LOW",
                "architecture",
                f"Class exposes {public_count} public/global methods (> 20)",
                1,
                fix="Reduce the public API; group related operations into focused classes",
                deduct=3,
            )

        # 3. Logic inside a trigger body
        if self._is_trigger:
            header_seen = False
            logic_line = 0
            for i, line in enumerate(self._bare_lines, 1):
                if not header_seen:
                    if re.search(r"^\s*trigger\s+\w+\s+on\s+\w+", line, re.IGNORECASE):
                        header_seen = True
                    continue
                if (
                    re.search(r"\[\s*SELECT\b", line, re.IGNORECASE)
                    or _DML_RE.search(line)
                    or re.search(r"\b(for|while)\s*\(|\bdo\s*\{", line, re.IGNORECASE)
                ):
                    logic_line = i
                    break
            if logic_line:
                self._add_issue(
                    "HIGH",
                    "architecture",
                    "Trigger contains business logic (SOQL/DML/loops) instead of delegating to a handler",
                    logic_line,
                    fix="Keep the trigger body to a single handler call (Trigger Actions Framework "
                    "or a TriggerHandler class)",
                    deduct=10,
                )

        # 4. Hardcoded Salesforce record IDs
        for i, line in enumerate(self._code_lines, 1):
            for m in _HARDCODED_ID_RE.finditer(line):
                candidate = m.group(1)
                if not re.search(r"\d", candidate) or not re.search(r"[A-Za-z]", candidate):
                    continue  # plain words / pure numbers are not IDs
                self._add_issue(
                    "HIGH",
                    "architecture",
                    f"Hardcoded Salesforce ID '{candidate}'",
                    i,
                    fix="Query by DeveloperName / use Custom Metadata, Custom Labels or "
                    "Schema.SObjectType.X.getRecordTypeInfosByDeveloperName()",
                    deduct=10,
                )

    # ------------------------------------------------------------------
    # Performance
    # ------------------------------------------------------------------

    def _check_performance(self):
        """Unbounded SOQL, getGlobalDescribe, @future, System.debug."""
        # 1. SOQL with neither WHERE nor LIMIT (skip test classes - small data sets)
        if not self._is_test_class:
            for m in _SOQL_RE.finditer(self._code_text):
                query = m.group(1)
                if re.search(r"\bWHERE\b|\bLIMIT\b", query, re.IGNORECASE):
                    continue
                line_no = self._line_of_offset(m.start())
                line_text = self._code_lines[line_no - 1]
                if re.search(r"getQueryLocator", line_text, re.IGNORECASE):
                    continue  # batch start() legitimately scans the whole table
                self._add_issue(
                    "MODERATE",
                    "performance",
                    "SOQL query has neither WHERE nor LIMIT - unbounded result set",
                    line_no,
                    fix="Add a WHERE filter and/or LIMIT, or move to a Batch/Queueable with a cursor",
                    deduct=3,
                )

        # 2. Schema.getGlobalDescribe()
        for i, line in enumerate(self._code_lines, 1):
            if re.search(r"Schema\.getGlobalDescribe\s*\(", line, re.IGNORECASE):
                self._add_issue(
                    "MODERATE",
                    "performance",
                    "Schema.getGlobalDescribe() is expensive",
                    i,
                    fix="Use Schema.describeSObjects(), Type.forName() or SObjectType tokens",
                    deduct=3,
                )

        if self._is_test_class:
            return

        # 3. @future is legacy - Queueable + Finalizer is the 2026 guidance
        for i, line in enumerate(self._code_lines, 1):
            if re.search(r"@future\b", line, re.IGNORECASE):
                self._add_issue(
                    "MODERATE",
                    "performance",
                    "@future is legacy async - use Queueable with System.Finalizer",
                    i,
                    fix="Implement Queueable (with AsyncOptions for dedup/delay) and attach a Finalizer",
                    deduct=3,
                )

        # 4. System.debug on main code paths
        debug_lines = [
            i
            for i, line in enumerate(self._code_lines, 1)
            if re.search(r"\bSystem\.debug\s*\(", line, re.IGNORECASE)
        ]
        if debug_lines:
            count = len(debug_lines)
            suffix = f" ({count} occurrences)" if count > 1 else ""
            self._add_issue(
                "INFO",
                "performance",
                f"System.debug in non-test class{suffix}",
                debug_lines[0],
                fix="Remove debug statements or route through a logging framework",
                deduct=1,
            )

    # ------------------------------------------------------------------
    # Clean code / error handling / documentation
    # ------------------------------------------------------------------

    def _check_naming_conventions(self):
        """Check for naming convention violations."""
        # Class names should be PascalCase
        # Match actual class declarations (with optional modifiers), not "class" in comments
        class_pattern = r"^\s*(?:public|private|global|virtual|abstract|with\s+sharing|without\s+sharing|\s)*\s*class\s+(\w+)"
        for i, line in enumerate(self.lines, 1):
            if _is_comment_line(line):
                continue
            match = re.search(class_pattern, line, re.IGNORECASE)
            if match:
                class_name = match.group(1)
                if not class_name[0].isupper():
                    self._add_issue(
                        "INFO",
                        "clean_code",
                        f'Class name "{class_name}" should be PascalCase',
                        i,
                        deduct=2,
                    )

        # Method names should be camelCase
        method_pattern = r"(public|private|protected|global)\s+(static\s+)?(\w+)\s+(\w+)\s*\("
        class_names = [m.group(1) for m in re.finditer(class_pattern, self.content)]
        for i, line in enumerate(self.lines, 1):
            match = re.search(method_pattern, line)
            if match:
                method_name = match.group(4)
                # Skip constructors and test methods
                if method_name[0].isupper() and "@isTest" not in "\n".join(self.lines[:i - 1]):
                    if method_name not in class_names:
                        self._add_issue(
                            "INFO",
                            "clean_code",
                            f'Method name "{method_name}" should be camelCase',
                            i,
                            deduct=2,
                        )

    def _check_error_handling(self):
        """Check for error handling patterns."""
        # Check for empty catch blocks
        empty_catch_pattern = r"catch\s*\([^)]+\)\s*\{\s*\}"
        for i, line in enumerate(self.lines, 1):
            if re.search(empty_catch_pattern, line):
                self._add_issue(
                    "MODERATE",
                    "error_handling",
                    "Empty catch block - exceptions are silently swallowed",
                    i,
                    fix="Log the exception or handle it appropriately",
                    deduct=5,
                )

    def _check_documentation(self):
        """Check for documentation/comments."""
        # Check for ApexDoc on public methods
        public_method_pattern = r"public\s+(\w+)\s+(\w+)\s*\("

        for i, line in enumerate(self.lines, 1):
            if re.search(public_method_pattern, line):
                # Check if there's a comment/ApexDoc before this line
                has_doc = False
                if i > 1:
                    prev_lines = "\n".join(self.lines[max(0, i - 5) : i - 1])
                    if "/**" in prev_lines or "//" in prev_lines:
                        has_doc = True

                if not has_doc:
                    self._add_issue(
                        "INFO",
                        "documentation",
                        "Public method missing documentation",
                        i,
                        fix="Add ApexDoc comment: /** @description ... */",
                        deduct=2,
                    )


def main():
    """Command-line interface for Apex validation."""
    if len(sys.argv) < 2:
        print("Usage: python validate_apex.py <file.cls|file.trigger> [api_version]")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    api_version = None
    if len(sys.argv) > 2:
        try:
            api_version = float(sys.argv[2])
        except ValueError:
            print(f"Error: api_version must be a number, got: {sys.argv[2]}")
            sys.exit(1)

    validator = ApexValidator(file_path, api_version=api_version)
    results = validator.validate()

    # Print results
    print(f"\n🔍 Apex Validation: {results['file']}")
    print(f"Score: {results['score']}/{results['max_score']} {results['rating']}")
    print()

    if results["issues"]:
        print("Issues found:")
        for issue in sorted(results["issues"], key=lambda x: severity_rank(x.get("severity"))):
            print(
                f"  {severity_icon(issue['severity'])} [{issue['severity']}] "
                f"Line {issue['line']}: {issue['message']}"
            )
            if "fix" in issue:
                print(f"      Fix: {issue['fix']}")
    else:
        print("✅ No issues found!")

    # Return non-zero if critical issues
    critical_count = sum(1 for i in results["issues"] if i["severity"] == "CRITICAL")
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
