#!/usr/bin/env python3
"""
Apex MCP Deployment Validator
===============================

Validates Apex code being deployed via Cirra AI MCP metadata tools.

Handles metadata_create, metadata_update, and tooling_api_dml for
ApexClass and ApexTrigger metadata types. Extracts the code body from
the MCP params, writes to a temp file, and delegates to the local
ApexValidator (150-point scoring).

For data operation validation (soql_query, sobject_dml), use
cirra-ai-sf-data instead.

Input format:
{
  "tool": "metadata_create" | "metadata_update" | "tooling_api_dml",
  "params": { ... MCP tool parameters ... },
  "context": { "purpose": "optional description" }
}
"""

import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════

SUPPORTED_TOOLS = ("metadata_create", "metadata_update", "tooling_api_dml")
APEX_METADATA_TYPES = ("ApexClass", "ApexTrigger")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════
# Code body extraction
# ═══════════════════════════════════════════════════════════════════════

def _extract_code_body(tool: str, params: Dict[str, Any]) -> Tuple[str, str, str]:
    """Extract metadata type, code body, and fullName from tool params.

    Returns:
        (metadata_type, body, full_name) — any can be empty string if not found.
    """
    metadata_type = ""
    body = ""
    full_name = ""

    if tool in ("metadata_create", "metadata_update"):
        metadata_type = params.get("type", "")
        metadata_list = params.get("metadata", [])
        if isinstance(metadata_list, list) and len(metadata_list) > 0:
            first = metadata_list[0]
            if isinstance(first, dict):
                body = first.get("body", "")
                full_name = first.get("fullName", "")

    elif tool == "tooling_api_dml":
        sobject = params.get("sObject", "")
        record = params.get("record", {})

        tooling_type_map = {
            "ApexClass": "ApexClass",
            "ApexTrigger": "ApexTrigger",
        }
        metadata_type = tooling_type_map.get(sobject, sobject)

        if isinstance(record, dict):
            body = record.get("Body", record.get("body", ""))
            full_name = record.get("FullName", record.get("fullName", ""))

    return metadata_type, body, full_name


# ═══════════════════════════════════════════════════════════════════════
# ApexValidator delegation
# ═══════════════════════════════════════════════════════════════════════

def _run_apex_validator(file_path: str) -> Optional[Dict[str, Any]]:
    """Import and run the local ApexValidator. Returns None if import fails."""
    try:
        if _SCRIPT_DIR not in sys.path:
            sys.path.insert(0, _SCRIPT_DIR)
        from validate_apex import ApexValidator
        validator = ApexValidator(file_path)
        return validator.validate()
    except (ImportError, Exception):
        return None


def _basic_apex_check(body: str, full_name: str) -> Dict[str, Any]:
    """Fallback: basic structural checks if ApexValidator is not importable."""
    issues: List[Dict[str, Any]] = []
    score = 150  # Start from ApexValidator's max

    # Check sharing keyword
    if re.search(r"(public|global)\s+class", body, re.IGNORECASE):
        if not re.search(r"(with sharing|without sharing|inherited sharing)", body, re.IGNORECASE):
            issues.append({
                "severity": "WARNING",
                "category": "security",
                "message": "Class missing explicit sharing declaration",
                "line": 1,
            })
            score -= 5

    # Check SOQL in loops
    loop_depth = 0
    for i, line in enumerate(body.split("\n"), 1):
        if re.search(r"\bfor\s*\(|\bwhile\s*\(|\bdo\s*\{", line, re.IGNORECASE):
            loop_depth += 1
        loop_depth += line.count("{") - line.count("}")
        loop_depth = max(0, loop_depth)
        if loop_depth > 0 and re.search(r"\[\s*SELECT\s+", line, re.IGNORECASE):
            issues.append({
                "severity": "CRITICAL",
                "category": "bulkification",
                "message": f"SOQL query inside loop at line {i}",
                "line": i,
            })
            score -= 10

    # Check DML in loops
    loop_depth = 0
    dml_patterns = [
        r"\binsert\s+", r"\bupdate\s+", r"\bdelete\s+",
        r"\bupsert\s+", r"Database\.(insert|update|delete|upsert)",
    ]
    for i, line in enumerate(body.split("\n"), 1):
        if re.search(r"\bfor\s*\(|\bwhile\s*\(|\bdo\s*\{", line, re.IGNORECASE):
            loop_depth += 1
        loop_depth += line.count("{") - line.count("}")
        loop_depth = max(0, loop_depth)
        if loop_depth > 0:
            for dp in dml_patterns:
                if re.search(dp, line, re.IGNORECASE):
                    issues.append({
                        "severity": "CRITICAL",
                        "category": "bulkification",
                        "message": f"DML inside loop at line {i}",
                        "line": i,
                    })
                    score -= 10

    return {
        "file": full_name or "unnamed",
        "score": max(0, score),
        "max_score": 150,
        "rating": _rating(max(0, score), 150),
        "issues": issues,
        "note": "Basic fallback check — ApexValidator not available for full 150-point scoring",
    }


def _rating(score: int, max_score: int) -> str:
    """Simple rating string."""
    pct = (score / max_score * 100) if max_score > 0 else 0
    if pct >= 90:
        return "Excellent (5/5)"
    elif pct >= 80:
        return "Very Good (4/5)"
    elif pct >= 70:
        return "Good (3/5)"
    elif pct >= 60:
        return "Needs Work (2/5)"
    else:
        return "Critical Issues (1/5)"


# ═══════════════════════════════════════════════════════════════════════
# Main validation
# ═══════════════════════════════════════════════════════════════════════

def validate_apex_deployment(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Apex code being deployed via MCP metadata tools.

    Extracts the Apex body from the metadata payload, writes it to a temp
    file, and delegates to ApexValidator (150-pt scoring).

    Args:
        input_data: Dict with "tool", "params", and optional "context".

    Returns:
        {
            "tier": "code_deployment",
            "tool": "metadata_create" | ...,
            "metadata_type": "ApexClass" | "ApexTrigger",
            "validator": "ApexValidator" | "basic_apex_check",
            "status": "scored" | "skipped" | "error",
            ... validator result fields ...
        }
    """
    tool = input_data.get("tool", "")
    params = input_data.get("params", {})

    metadata_type, body, full_name = _extract_code_body(tool, params)

    base = {
        "tier": "code_deployment",
        "tool": tool,
        "metadata_type": metadata_type,
        "full_name": full_name,
    }

    if not metadata_type:
        return {
            **base,
            "validator": None,
            "status": "error",
            "message": "Could not determine metadata type from params",
        }

    # Not an Apex type — skip
    if metadata_type not in APEX_METADATA_TYPES:
        return {
            **base,
            "validator": None,
            "status": "skipped",
            "message": f"Not an Apex metadata type ('{metadata_type}'). "
                       f"Use cirra-ai-sf-flow for Flow validation.",
        }

    if not body or not body.strip():
        return {
            **base,
            "validator": None,
            "status": "error",
            "message": "No code body found in metadata payload",
        }

    # Write to temp file and validate
    ext = ".cls" if "class" in body.lower()[:200] else ".trigger"
    tmp_name = f"validate_{full_name or 'unnamed'}{ext}"
    tmp_path = os.path.join(tempfile.gettempdir(), tmp_name)

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(body)

        result = _run_apex_validator(tmp_path)
        if result is not None:
            return {**base, "validator": "ApexValidator", "status": "scored", **result}
        else:
            return {**base, "validator": "basic_apex_check", "status": "scored",
                    **_basic_apex_check(body, full_name)}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════
# Entry point class
# ═══════════════════════════════════════════════════════════════════════

class ApexMCPValidator:
    """Validates Apex code deployments via MCP metadata tools.

    Usage:
        validator = ApexMCPValidator()
        result = validator.validate({"tool": "metadata_create", "params": {...}})
    """

    def validate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Apex deployment parameters.

        Args:
            input_data: Dict with "tool", "params", optional "context".

        Returns:
            Scored validation result.
        """
        tool = input_data.get("tool", "")

        if tool not in SUPPORTED_TOOLS:
            return {
                "tier": "code_deployment",
                "tool": tool,
                "status": "error",
                "message": f"Tool '{tool}' is not a deployment tool. "
                           f"Expected one of: {', '.join(SUPPORTED_TOOLS)}. "
                           f"For data operations, use cirra-ai-sf-data.",
            }

        return validate_apex_deployment(input_data)
