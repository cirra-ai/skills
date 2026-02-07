#!/usr/bin/env python3
"""
MCP Operation Validator — Two-Tier Model
==========================================

Validates Cirra AI MCP tool call parameters with two distinct tiers:

Tier 1 — Data Parameter Checks (soql_query, sobject_dml)
  Lightweight pass/fail validation for interactive data operations.
  No scoring — just structural error/warning checks that catch things
  that would fail or leak data. Running an inefficient query interactively
  is fine; governor limits protect you.

Tier 2 — Code Deployment Scoring (metadata_create, metadata_update, tooling_api_dml)
  Full code-quality scoring when deploying Apex classes, triggers, or Flows.
  Extracts the code body, writes to a temp file, and delegates to the existing
  ApexValidator (150-pt) or EnhancedFlowValidator (110-pt).

Input format:
{
  "tool": "soql_query" | "sobject_dml" | "metadata_create" | "metadata_update" | "tooling_api_dml",
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
# Tier 1 — Lightweight Data Parameter Checks
# ═══════════════════════════════════════════════════════════════════════

VALID_DML_OPERATIONS = ("insert", "update", "delete", "upsert")
SOBJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(__c|__mdt|__e|__b|__x)?$")

PII_PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "Credit card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    "Personal email": re.compile(
        r"\b[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|aol)\.(com|net|org)\b",
        re.IGNORECASE,
    ),
}


def validate_data_params(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tier 1: Validate soql_query or sobject_dml parameters.

    Returns a simple pass/fail with lists of errors and warnings.
    No scoring — just binary checks for things that would fail or leak data.

    Args:
        input_data: Dict with keys "tool", "params", and optional "context".

    Returns:
        {
            "tier": "data_params",
            "tool": "soql_query" | "sobject_dml",
            "status": "pass" | "fail",
            "errors": [ {"message": "..."} ],
            "warnings": [ {"message": "..."} ]
        }
    """
    tool = input_data.get("tool", "")
    params = input_data.get("params", {})

    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    # ── Shared checks ───────────────────────────────────────────────
    if not params.get("sObject"):
        errors.append({"message": "Missing required 'sObject' parameter"})
    elif isinstance(params.get("sObject"), str) and not SOBJECT_NAME_PATTERN.match(params["sObject"]):
        warnings.append({"message": f"sObject name '{params['sObject']}' doesn't match expected pattern"})

    if not params.get("sf_user"):
        warnings.append({"message": "No 'sf_user' specified — will use default org connection"})

    # ── soql_query checks ───────────────────────────────────────────
    if tool == "soql_query":
        # Required string parameters per MCP schema
        for req_param in ("orderBy", "groupBy"):
            if req_param not in params or not isinstance(params[req_param], str):
                errors.append({
                    "message": f"Missing required '{req_param}' parameter "
                               f"(pass empty string if not needed)"
                })

        where = params.get("whereClause") or ""
        if where.strip():
            _check_where_syntax(where, warnings)

    # ── sobject_dml checks ──────────────────────────────────────────
    elif tool == "sobject_dml":
        operation = params.get("operation", "")
        records = params.get("records", [])
        ext_id_field = params.get("externalIdField")

        # Valid operation
        if operation not in VALID_DML_OPERATIONS:
            errors.append({
                "message": f"Invalid operation: '{operation}'. "
                           f"Expected one of: {', '.join(VALID_DML_OPERATIONS)}"
            })

        # Records array
        if not isinstance(records, list) or len(records) == 0:
            errors.append({"message": "Empty or missing records array"})
        else:
            # Update/delete must have Id
            if operation in ("update", "delete"):
                missing_id = [
                    i for i, r in enumerate(records)
                    if isinstance(r, dict) and "Id" not in r
                ]
                if missing_id:
                    errors.append({
                        "message": f"{len(missing_id)} record(s) missing 'Id' field "
                                   f"for {operation} operation"
                    })

            # Upsert requires externalIdField
            if operation == "upsert" and not ext_id_field:
                errors.append({
                    "message": "Upsert operation requires externalIdField parameter"
                })

            # Upsert records must contain the external ID field
            if operation == "upsert" and ext_id_field:
                missing_ext = [
                    i for i, r in enumerate(records)
                    if isinstance(r, dict) and ext_id_field not in r
                ]
                if missing_ext:
                    warnings.append({
                        "message": f"{len(missing_ext)} record(s) missing external "
                                   f"ID field '{ext_id_field}'"
                    })

            # Inconsistent fields across records
            if operation == "insert" and len(records) >= 2:
                field_sets = [
                    frozenset(r.keys()) for r in records if isinstance(r, dict)
                ]
                if field_sets and len(set(field_sets)) > 1:
                    warnings.append({
                        "message": "Inconsistent field names across records — "
                                   "some records have different fields"
                    })

            # PII detection
            _check_pii(records, warnings)

    else:
        errors.append({
            "message": f"Tier 1 does not handle tool '{tool}'. "
                       f"Expected 'soql_query' or 'sobject_dml'."
        })

    status = "fail" if errors else "pass"

    return {
        "tier": "data_params",
        "tool": tool,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }


def _check_where_syntax(where: str, warnings: List[Dict[str, str]]):
    """Check for common SOQL syntax mistakes in whereClause."""
    if re.search(r"==", where):
        warnings.append({
            "message": "Invalid '==' operator in whereClause — SOQL uses '='"
        })
    if re.search(r'=\s*"[^"]*"', where):
        warnings.append({
            "message": "Double-quoted string in whereClause — SOQL uses single quotes"
        })
    if where.count("(") != where.count(")"):
        warnings.append({
            "message": "Unbalanced parentheses in whereClause"
        })


def _check_pii(records: list, warnings: List[Dict[str, str]]):
    """Scan record values for PII patterns."""
    pii_found: Dict[str, List[str]] = {}

    for i, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for field, value in record.items():
            if not isinstance(value, str):
                continue
            for pii_type, pattern in PII_PATTERNS.items():
                if pattern.search(value):
                    if pii_type not in pii_found:
                        pii_found[pii_type] = []
                    pii_found[pii_type].append(f"record {i}, field '{field}'")
                    break  # one match per value is enough

    for pii_type, locations in pii_found.items():
        sample = locations[0]
        extra = f" (and {len(locations) - 1} more)" if len(locations) > 1 else ""
        warnings.append({
            "message": f"{pii_type} pattern detected in {sample}{extra} "
                       f"— use synthetic test data instead"
        })


# ═══════════════════════════════════════════════════════════════════════
# Tier 2 — Code Deployment Scoring
# ═══════════════════════════════════════════════════════════════════════

# Known validator paths — checked in order (relative to installed plugin, then absolute fallbacks)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

APEX_VALIDATOR_SEARCH_PATHS = [
    # Relative: when installed at .local-plugins/marketplaces/.../cirra-ai-sf-data/hooks/scripts
    os.path.join(_SCRIPT_DIR, "..", "..", "..", "..",
                 "local-desktop-app-uploads", "sf-apex-cirra-ai", "hooks", "scripts"),
    # Absolute: Cowork session known location
    "/sessions/eager-fervent-gauss/mnt/.local-plugins/marketplaces/local-desktop-app-uploads/sf-apex-cirra-ai/hooks/scripts",
]

FLOW_VALIDATOR_SEARCH_PATHS = [
    os.path.join(_SCRIPT_DIR, "..", "..", "..", "..",
                 "sf-skills", "sf-flow", "hooks", "scripts"),
    "/sessions/eager-fervent-gauss/mnt/.local-plugins/marketplaces/sf-skills/sf-flow/hooks/scripts",
]

FLOW_SHARED_SEARCH_PATHS = [
    os.path.join(_SCRIPT_DIR, "..", "..", "..", "..",
                 "sf-skills", "shared", "hooks", "scripts"),
    "/sessions/eager-fervent-gauss/mnt/.local-plugins/marketplaces/sf-skills/shared/hooks/scripts",
]


def _find_path(search_paths: List[str]) -> Optional[str]:
    """Return the first existing path from the search list."""
    for p in search_paths:
        resolved = os.path.realpath(p)
        if os.path.isdir(resolved):
            return resolved
    return None

# Metadata types that contain deployable code
APEX_METADATA_TYPES = ("ApexClass", "ApexTrigger")
FLOW_METADATA_TYPES = ("Flow", "FlowDefinition")


def validate_code_deployment(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Tier 2: Validate code being deployed via metadata_create / metadata_update / tooling_api_dml.

    Extracts the code body from the metadata payload, writes it to a temp file,
    and delegates to the appropriate validator:
      - ApexClass / ApexTrigger -> ApexValidator (150-pt)
      - Flow / FlowDefinition  -> EnhancedFlowValidator (110-pt)

    If the metadata type is not code (e.g. CustomObject, PermissionSet), the
    operation is passed through without validation.

    Args:
        input_data: Dict with "tool", "params", and optional "context".

    Returns:
        {
            "tier": "code_deployment",
            "tool": "metadata_create" | "metadata_update" | "tooling_api_dml",
            "metadata_type": "ApexClass" | "Flow" | ...,
            "validator": "ApexValidator" | "EnhancedFlowValidator" | null,
            "status": "scored" | "skipped" | "error",
            ... validator result fields ...
        }
    """
    tool = input_data.get("tool", "")
    params = input_data.get("params", {})

    # Determine metadata type and extract body
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

    # Non-code metadata — pass through
    if metadata_type not in APEX_METADATA_TYPES and metadata_type not in FLOW_METADATA_TYPES:
        return {
            **base,
            "validator": None,
            "status": "skipped",
            "message": f"No code validator for metadata type '{metadata_type}' — skipping",
        }

    if not body or not body.strip():
        return {
            **base,
            "validator": None,
            "status": "error",
            "message": "No code body found in metadata payload",
        }

    # ── Apex validation ─────────────────────────────────────────────
    if metadata_type in APEX_METADATA_TYPES:
        return _validate_apex_body(body, full_name, base)

    # ── Flow validation ─────────────────────────────────────────────
    if metadata_type in FLOW_METADATA_TYPES:
        return _validate_flow_body(body, full_name, base)

    # Shouldn't reach here
    return {**base, "validator": None, "status": "skipped"}


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
        # Tooling API uses sObject for type and record for payload
        sobject = params.get("sObject", "")
        record = params.get("record", {})

        # Map Tooling API sObject names to metadata types
        tooling_type_map = {
            "ApexClass": "ApexClass",
            "ApexTrigger": "ApexTrigger",
            "Flow": "Flow",
            "FlowDefinition": "FlowDefinition",
        }
        metadata_type = tooling_type_map.get(sobject, sobject)

        if isinstance(record, dict):
            body = record.get("Body", record.get("body", ""))
            full_name = record.get("FullName", record.get("fullName", ""))
            # For Tooling API, Metadata may be nested
            if not body:
                metadata_inner = record.get("Metadata", record.get("metadata", {}))
                if isinstance(metadata_inner, dict):
                    body = metadata_inner.get("body", "")

    return metadata_type, body, full_name


def _validate_apex_body(body: str, full_name: str, base: dict) -> Dict[str, Any]:
    """Validate Apex code body using ApexValidator."""
    ext = ".cls" if "class" in body.lower()[:200] else ".trigger"
    tmp_name = f"validate_{full_name or 'unnamed'}{ext}"

    try:
        # Write to temp file
        tmp_path = os.path.join(tempfile.gettempdir(), tmp_name)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(body)

        # Try to import ApexValidator
        result = _run_apex_validator(tmp_path)
        if result is not None:
            return {
                **base,
                "validator": "ApexValidator",
                "status": "scored",
                **result,
            }
        else:
            # Fallback: basic structural checks
            return {
                **base,
                "validator": "basic_apex_check",
                "status": "scored",
                **_basic_apex_check(body, full_name),
            }
    finally:
        # Clean up temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _run_apex_validator(file_path: str) -> Optional[Dict[str, Any]]:
    """Try to import and run ApexValidator. Returns None if import fails."""
    try:
        apex_dir = _find_path(APEX_VALIDATOR_SEARCH_PATHS)
        if not apex_dir:
            return None
        if apex_dir not in sys.path:
            sys.path.insert(0, apex_dir)
        from validate_apex import ApexValidator
        validator = ApexValidator(file_path)
        return validator.validate()
    except (ImportError, Exception):
        return None


def _basic_apex_check(body: str, full_name: str) -> Dict[str, Any]:
    """Fallback: basic structural checks if ApexValidator is not importable."""
    issues = []
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

    # Check DML in loops (simplified)
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
        "rating": _basic_rating(max(0, score), 150),
        "issues": issues,
        "note": "Basic fallback check — ApexValidator not available for full 150-point scoring",
    }


def _validate_flow_body(body: str, full_name: str, base: dict) -> Dict[str, Any]:
    """Validate Flow XML body using EnhancedFlowValidator."""
    tmp_name = f"validate_{full_name or 'unnamed'}.flow-meta.xml"

    try:
        tmp_path = os.path.join(tempfile.gettempdir(), tmp_name)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(body)

        result = _run_flow_validator(tmp_path)
        if result is not None:
            return {
                **base,
                "validator": "EnhancedFlowValidator",
                "status": "scored",
                **result,
            }
        else:
            return {
                **base,
                "validator": "basic_flow_check",
                "status": "scored",
                **_basic_flow_check(body, full_name),
            }
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def _run_flow_validator(file_path: str) -> Optional[Dict[str, Any]]:
    """Try to import and run EnhancedFlowValidator. Returns None if import fails."""
    try:
        # Flow validator needs shared modules on the path first
        shared_dir = _find_path(FLOW_SHARED_SEARCH_PATHS)
        if shared_dir and shared_dir not in sys.path:
            sys.path.insert(0, shared_dir)

        flow_dir = _find_path(FLOW_VALIDATOR_SEARCH_PATHS)
        if not flow_dir:
            return None
        if flow_dir not in sys.path:
            sys.path.insert(0, flow_dir)

        from validate_flow import EnhancedFlowValidator
        validator = EnhancedFlowValidator(file_path)
        return validator.validate()
    except (ImportError, Exception):
        return None


def _basic_flow_check(body: str, full_name: str) -> Dict[str, Any]:
    """Fallback: basic XML structural checks if EnhancedFlowValidator is not importable."""
    issues = []
    score = 110  # Start from Flow validator's max

    # Check for description
    if "<description>" not in body:
        issues.append({
            "severity": "INFO",
            "category": "design_naming",
            "message": "Flow missing description element",
        })
        score -= 5

    # Check for DML in loops (simple string heuristic)
    has_loops = "<loops>" in body
    has_dml = any(tag in body for tag in ["<recordCreates>", "<recordUpdates>", "<recordDeletes>"])
    if has_loops and has_dml:
        issues.append({
            "severity": "WARNING",
            "category": "performance",
            "message": "Flow has both loops and DML elements — verify DML is outside loops",
        })
        # Don't deduct — can't confirm without path tracing

    return {
        "flow_name": full_name or "unnamed",
        "score": max(0, score),
        "max_score": 110,
        "rating": _basic_rating(max(0, score), 110),
        "issues": issues,
        "note": "Basic fallback check — EnhancedFlowValidator not available for full 110-point scoring",
    }


def _basic_rating(score: int, max_score: int) -> str:
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
# Unified entry point
# ═══════════════════════════════════════════════════════════════════════

TIER1_TOOLS = ("soql_query", "sobject_dml")
TIER2_TOOLS = ("metadata_create", "metadata_update", "tooling_api_dml")


class MCPOperationValidator:
    """Unified validator that routes to the appropriate tier.

    Usage:
        validator = MCPOperationValidator()
        result = validator.validate({"tool": "soql_query", "params": {...}})
        result = validator.validate({"tool": "metadata_create", "params": {...}})
    """

    def validate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route to Tier 1 or Tier 2 based on tool type.

        Args:
            input_data: Dict with "tool", "params", optional "context".

        Returns:
            Tier 1 result (pass/fail) or Tier 2 result (scored report).
        """
        tool = input_data.get("tool", "")

        if tool in TIER1_TOOLS:
            return validate_data_params(input_data)
        elif tool in TIER2_TOOLS:
            return validate_code_deployment(input_data)
        else:
            return {
                "tier": "unknown",
                "tool": tool,
                "status": "error",
                "message": f"Unknown tool: '{tool}'. "
                           f"Expected one of: {', '.join(TIER1_TOOLS + TIER2_TOOLS)}",
                "errors": [{"message": f"Unknown tool: '{tool}'"}],
                "warnings": [],
            }
