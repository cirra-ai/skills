#!/usr/bin/env python3
"""
MCP Operation Validator
========================

Validates Cirra AI MCP tool call parameters against the 130-point scoring system.
Designed for pre-flight validation in Claude Cowork mode — run this BEFORE
executing sobject_dml or soql_query calls.

Scoring categories (130 points total):
- Query Efficiency (25 points)
- Bulk Safety (25 points)
- Data Integrity (20 points)
- Security & FLS (20 points)
- Test Patterns (15 points)
- Cleanup & Isolation (15 points)
- Documentation (10 points)

Input format:
{
  "tool": "soql_query" | "sobject_dml",
  "params": { ... MCP tool parameters ... },
  "context": {
    "purpose": "optional description",
    "cleanup_planned": true
  }
}
"""

import re
from typing import Any


class MCPOperationValidator:
    """Validates MCP tool call parameters before execution."""

    VALID_DML_OPERATIONS = ("insert", "update", "delete", "upsert")
    VALID_TOOLS = ("soql_query", "sobject_dml")

    INDEXED_FIELDS = (
        "Id", "Name", "OwnerId", "CreatedDate",
        "LastModifiedDate", "SystemModstamp", "RecordTypeId",
    )

    SOBJECT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(__c|__mdt|__e|__b|__x)?$")

    PII_PATTERNS = {
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "Credit card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "Personal email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|aol)\.(com|net|org)\b",
            re.IGNORECASE,
        ),
    }

    CATEGORIES = {
        "query_efficiency": {"name": "Query Efficiency", "max": 25},
        "bulk_safety": {"name": "Bulk Safety", "max": 25},
        "data_integrity": {"name": "Data Integrity", "max": 20},
        "security_fls": {"name": "Security & FLS", "max": 20},
        "test_patterns": {"name": "Test Patterns", "max": 15},
        "cleanup_isolation": {"name": "Cleanup & Isolation", "max": 15},
        "documentation": {"name": "Documentation", "max": 10},
    }

    def __init__(self):
        self.issues: list[dict[str, Any]] = []
        self.recommendations: list[str] = []
        self.categories: dict[str, dict[str, Any]] = {}
        self._reset()

    def _reset(self):
        """Reset state for a fresh validation run."""
        self.issues = []
        self.recommendations = []
        self.categories = {
            key: {"name": val["name"], "max": val["max"], "score": val["max"], "issues": []}
            for key, val in self.CATEGORIES.items()
        }

    def validate(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Validate MCP tool call parameters and return a scored report.

        Args:
            input_data: Dict with keys "tool", "params", and optional "context".

        Returns:
            Validation report dict with score, categories, issues, recommendations.
        """
        self._reset()

        tool = input_data.get("tool", "")
        params = input_data.get("params", {})
        context = input_data.get("context", {})

        if tool not in self.VALID_TOOLS:
            self._deduct(
                "data_integrity", 10,
                f"Unknown tool: '{tool}'. Expected one of: {', '.join(self.VALID_TOOLS)}"
            )
            return self._build_report(tool)

        # Shared checks
        self._check_data_integrity_shared(params)
        self._check_documentation(context)

        # Tool-specific checks
        if tool == "soql_query":
            self._validate_soql_query(params)
        elif tool == "sobject_dml":
            self._validate_sobject_dml(params, context)

        return self._build_report(tool)

    # ── soql_query validation ──────────────────────────────────────────

    def _validate_soql_query(self, params: dict[str, Any]):
        """Run all checks for soql_query parameters."""
        self._check_query_efficiency(params)

    def _check_query_efficiency(self, params: dict[str, Any]):
        """Query Efficiency (25 pts): whereClause, limit, indexed fields,
        hardcoded IDs, field selectivity, SOQL syntax."""
        where = params.get("whereClause") or ""
        limit_val = params.get("limit")
        fields = params.get("fields")

        # WHERE clause
        if not where.strip():
            self._deduct("query_efficiency", 5, "No whereClause — query will scan all records")
            self.recommendations.append(
                "Add a whereClause to filter results and improve selectivity"
            )
        else:
            # Hardcoded Salesforce IDs
            if re.search(r"'[a-zA-Z0-9]{15}'|'[a-zA-Z0-9]{18}'", where):
                self._deduct("query_efficiency", 5, "Hardcoded Salesforce IDs in whereClause")
                self.recommendations.append(
                    "Use dynamic references instead of hardcoded record IDs"
                )

            # Indexed fields
            uses_indexed = any(
                re.search(rf"\b{field}\b", where, re.IGNORECASE)
                for field in self.INDEXED_FIELDS
            )
            if not uses_indexed:
                self._deduct(
                    "query_efficiency", 3,
                    "whereClause does not reference indexed fields "
                    "(Id, Name, CreatedDate, OwnerId, RecordTypeId, etc.)"
                )
                self.recommendations.append(
                    "Filter on an indexed field for better query performance"
                )

            # SOQL syntax
            self._check_where_syntax(where)

        # LIMIT
        if limit_val is None:
            self._deduct(
                "query_efficiency", 3,
                "No limit specified — large result sets may cause issues"
            )
            self.recommendations.append(
                "Add a limit to prevent unexpected large result sets"
            )
        elif isinstance(limit_val, (int, float)) and limit_val > 50000:
            self._deduct(
                "query_efficiency", 5,
                f"Excessive limit ({limit_val}) — may exceed governor limits"
            )

        # Field selectivity
        if fields is None or (isinstance(fields, list) and len(fields) == 0):
            self._deduct(
                "query_efficiency", 2,
                "No fields specified — selecting all fields"
            )
            self.recommendations.append(
                "Specify only the fields you need for better performance"
            )

    def _check_where_syntax(self, where: str):
        """Check for common SOQL syntax mistakes in the whereClause string."""
        if re.search(r"==", where):
            self._deduct(
                "query_efficiency", 5,
                "Invalid '==' operator in whereClause — SOQL uses '='"
            )

        if re.search(r'=\s*"[^"]*"', where):
            self._deduct(
                "query_efficiency", 2,
                "Double-quoted string in whereClause — SOQL uses single quotes"
            )

        if where.count("(") != where.count(")"):
            self._deduct("query_efficiency", 5, "Unbalanced parentheses in whereClause")

    # ── sobject_dml validation ─────────────────────────────────────────

    def _validate_sobject_dml(self, params: dict[str, Any], context: dict[str, Any]):
        """Run all checks for sobject_dml parameters."""
        self._check_bulk_safety(params)
        self._check_data_integrity_dml(params)
        self._check_security(params)
        self._check_test_patterns(params)
        self._check_cleanup_isolation(params, context)

    def _check_bulk_safety(self, params: dict[str, Any]):
        """Bulk Safety (25 pts): operation validity, records array,
        batch size, upsert requirements."""
        operation = params.get("operation", "")
        records = params.get("records", [])
        ext_id_field = params.get("externalIdField")

        # Valid operation
        if operation not in self.VALID_DML_OPERATIONS:
            self._deduct(
                "bulk_safety", 10,
                f"Invalid operation: '{operation}'. "
                f"Expected one of: {', '.join(self.VALID_DML_OPERATIONS)}"
            )

        # Records array
        if not isinstance(records, list) or len(records) == 0:
            self._deduct("bulk_safety", 10, "Empty or missing records array")
        elif len(records) > 10000:
            self._deduct(
                "bulk_safety", 5,
                f"Record count ({len(records)}) exceeds 10,000 — "
                "may hit governor limits in a single transaction"
            )
            self.recommendations.append(
                "Break into batches of 200 records for large operations"
            )

        # Upsert requires externalIdField
        if operation == "upsert" and not ext_id_field:
            self._deduct(
                "bulk_safety", 10,
                "Upsert operation requires externalIdField parameter"
            )

    def _check_data_integrity_dml(self, params: dict[str, Any]):
        """Data Integrity checks specific to sobject_dml."""
        operation = params.get("operation", "")
        records = params.get("records", [])
        ext_id_field = params.get("externalIdField")

        if not isinstance(records, list) or len(records) == 0:
            return  # Already flagged in bulk_safety

        # Update/delete must have Id
        if operation in ("update", "delete"):
            missing_id = [
                i for i, r in enumerate(records)
                if isinstance(r, dict) and "Id" not in r
            ]
            if missing_id:
                count = len(missing_id)
                self._deduct(
                    "data_integrity", 10,
                    f"{count} record(s) missing 'Id' field for {operation} operation"
                )

        # Upsert records must contain the external ID field
        if operation == "upsert" and ext_id_field:
            missing_ext = [
                i for i, r in enumerate(records)
                if isinstance(r, dict) and ext_id_field not in r
            ]
            if missing_ext:
                count = len(missing_ext)
                self._deduct(
                    "data_integrity", 5,
                    f"{count} record(s) missing external ID field '{ext_id_field}'"
                )

        # Inconsistent fields across records (insert only)
        if operation == "insert" and len(records) >= 2:
            field_sets = [
                frozenset(r.keys()) for r in records if isinstance(r, dict)
            ]
            if field_sets and len(set(field_sets)) > 1:
                self._deduct(
                    "data_integrity", 3,
                    "Inconsistent field names across records — "
                    "some records have different fields"
                )

    def _check_security(self, params: dict[str, Any]):
        """Security & FLS (20 pts): PII detection in record values."""
        records = params.get("records", [])
        if not isinstance(records, list):
            return

        pii_found: dict[str, list[str]] = {}

        for i, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            for field, value in record.items():
                if not isinstance(value, str):
                    continue
                for pii_type, pattern in self.PII_PATTERNS.items():
                    if pattern.search(value):
                        if pii_type not in pii_found:
                            pii_found[pii_type] = []
                        pii_found[pii_type].append(f"record {i}, field '{field}'")
                        break  # one PII match per value is enough

        for pii_type, locations in pii_found.items():
            points = 10 if pii_type != "Personal email" else 5
            sample = locations[0]
            extra = f" (and {len(locations) - 1} more)" if len(locations) > 1 else ""
            self._deduct(
                "security_fls", points,
                f"{pii_type} pattern detected in {sample}{extra}"
            )
            self.recommendations.append(
                f"Remove {pii_type} data — use synthetic test data instead"
            )

    def _check_test_patterns(self, params: dict[str, Any]):
        """Test Patterns (15 pts): record count, data variety, realistic naming."""
        operation = params.get("operation", "")
        records = params.get("records", [])

        if operation != "insert" or not isinstance(records, list) or len(records) == 0:
            return  # Only applicable to inserts

        # Bulk test threshold (201+ crosses batch boundary)
        if len(records) < 201:
            self._deduct(
                "test_patterns", 5,
                f"Only {len(records)} records — consider 201+ to cross "
                "the 200-record batch boundary"
            )

        # Data variety — check if all records are identical (excluding Name with counters)
        if len(records) >= 2:
            value_sets = []
            for r in records:
                if not isinstance(r, dict):
                    continue
                vals = frozenset(
                    (k, str(v)) for k, v in r.items()
                    if k not in ("Id", "Name", "name")
                )
                value_sets.append(vals)

            if value_sets and len(set(value_sets)) == 1:
                self._deduct(
                    "test_patterns", 3,
                    "All records have identical field values — "
                    "add variety for realistic testing"
                )
                self.recommendations.append(
                    "Vary field values (e.g., mix of Industries, Types, Ratings) "
                    "for better test coverage"
                )

        # All Names identical
        names = [
            r.get("Name") for r in records
            if isinstance(r, dict) and "Name" in r
        ]
        if names and len(set(names)) == 1 and len(names) > 1:
            self._deduct("test_patterns", 2, "All records have the same Name value")

    def _check_cleanup_isolation(self, params: dict[str, Any], context: dict[str, Any]):
        """Cleanup & Isolation (15 pts): queryable naming, cleanup plan."""
        operation = params.get("operation", "")
        records = params.get("records", [])

        if operation not in ("insert", "upsert"):
            return  # Only applies to record creation

        # Cleanup-friendly naming pattern
        if isinstance(records, list) and len(records) > 0:
            has_cleanup_name = False
            for r in records:
                if not isinstance(r, dict):
                    continue
                name = r.get("Name", "")
                if isinstance(name, str) and re.search(
                    r"(?i)^test|^tmp|^seed|^demo|^sample", name
                ):
                    has_cleanup_name = True
                    break

            if not has_cleanup_name:
                self._deduct(
                    "cleanup_isolation", 5,
                    "No records use a cleanup-friendly Name pattern "
                    "(e.g., 'Test ...', 'Tmp ...', 'Demo ...')"
                )
                self.recommendations.append(
                    "Prefix record Names with 'Test' so they can be queried "
                    "and deleted later"
                )

        # Cleanup planned
        if not context or not context.get("cleanup_planned"):
            self._deduct(
                "cleanup_isolation", 5,
                "No cleanup plan indicated in context"
            )
            self.recommendations.append(
                "Set context.cleanup_planned = true and plan a DELETE query "
                "after testing"
            )

    # ── Shared checks ──────────────────────────────────────────────────

    def _check_data_integrity_shared(self, params: dict[str, Any]):
        """Data Integrity checks that apply to all tools."""
        sobject = params.get("sObject")
        if not sobject:
            self._deduct(
                "data_integrity", 10, "Missing required 'sObject' parameter"
            )
        elif isinstance(sobject, str) and not self.SOBJECT_NAME_PATTERN.match(sobject):
            self._deduct(
                "data_integrity", 2,
                f"sObject name '{sobject}' doesn't match expected pattern"
            )

        if not params.get("sf_user"):
            self._deduct(
                "data_integrity", 5,
                "Missing 'sf_user' parameter — required for org connection"
            )

    def _check_documentation(self, context: dict[str, Any]):
        """Documentation (10 pts): purpose and context presence."""
        if not context:
            self._deduct(
                "documentation", 5,
                "No context provided — add purpose and cleanup plan"
            )
            self._deduct(
                "documentation", 5,
                "No operation purpose documented"
            )
            return

        if not context.get("purpose"):
            self._deduct(
                "documentation", 5,
                "No operation purpose documented in context"
            )
            self.recommendations.append(
                "Add context.purpose to explain why this operation is being run"
            )

    # ── Deduction & report helpers ─────────────────────────────────────

    def _deduct(self, category: str, points: int, message: str):
        """Deduct points from a category and record the issue."""
        if category not in self.categories:
            return

        cat = self.categories[category]
        cat["score"] = max(0, cat["score"] - points)
        cat["issues"].append(message)

        self.issues.append({
            "category": cat["name"],
            "severity": "error" if points >= 10 else "warning",
            "message": message,
            "points": points,
        })

    def _build_report(self, tool: str) -> dict[str, Any]:
        """Build the final validation report."""
        total_score = sum(cat["score"] for cat in self.categories.values())
        max_score = sum(cat["max"] for cat in self.categories.values())

        return {
            "tool": tool,
            "score": total_score,
            "max_score": max_score,
            "rating": self._get_rating(total_score),
            "status": self._get_status(total_score),
            "categories": {
                cat["name"]: {
                    "score": cat["score"],
                    "max": cat["max"],
                    "issues": cat["issues"],
                }
                for cat in self.categories.values()
            },
            "issues": self.issues,
            "recommendations": self.recommendations,
        }

    @staticmethod
    def _get_rating(score: int) -> str:
        """Star rating based on score thresholds."""
        if score >= 117:
            return "Excellent (5/5)"
        elif score >= 104:
            return "Very Good (4/5)"
        elif score >= 91:
            return "Good (3/5)"
        elif score >= 78:
            return "Needs Work (2/5)"
        else:
            return "Critical Issues (1/5)"

    @staticmethod
    def _get_status(score: int) -> str:
        """Pass/fail status."""
        if score >= 117:
            return "PASSED"
        elif score >= 91:
            return "PASSED — review recommended"
        elif score >= 78:
            return "PASSED — address warnings"
        else:
            return "BLOCKED — fix critical issues before executing"
