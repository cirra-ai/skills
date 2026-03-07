#!/usr/bin/env python3
"""Salesforce metadata payload validator with lightweight 120-point scoring."""

from __future__ import annotations

import re
from typing import Any

MAX_SCORE = 120
CATEGORIES = {
    "schema": 20,
    "naming": 20,
    "security": 20,
    "documentation": 20,
    "deployability": 20,
    "maintainability": 20,
}

SUPPORTED_METADATA_TYPES = {
    "CustomObject",
    "CustomField",
    "ValidationRule",
    "RecordType",
    "PermissionSet",
}


class MetadataOperationValidator:
    """Score a single Salesforce metadata payload."""

    def __init__(self, metadata_type: str, payload: dict[str, Any]):
        self.metadata_type = metadata_type
        self.payload = payload
        self.categories = {k: {"max": v, "score": v, "issues": []} for k, v in CATEGORIES.items()}
        self.issues: list[dict[str, Any]] = []

    def validate(self) -> dict[str, Any]:
        if self.metadata_type not in SUPPORTED_METADATA_TYPES:
            self._deduct("schema", 20, f"Unsupported metadata type: {self.metadata_type}", "critical")
            return self._result()

        if not isinstance(self.payload, dict) or not self.payload:
            self._deduct("schema", 20, "Metadata payload is missing or empty", "critical")
            return self._result()

        self._check_required_fields()
        self._check_naming()
        self._check_security()
        self._check_documentation()
        self._check_deployability()
        self._check_maintainability()

        return self._result()

    def _check_required_fields(self):
        required_by_type = {
            "CustomObject": ("fullName", "label", "nameField", "deploymentStatus", "sharingModel"),
            "CustomField": ("fullName", "label", "type"),
            "ValidationRule": ("fullName", "active", "errorConditionFormula", "errorMessage"),
            "RecordType": ("fullName", "label", "active"),
            "PermissionSet": ("fullName", "label"),
        }
        for key in required_by_type.get(self.metadata_type, ()):
            if key not in self.payload:
                self._deduct("schema", 5, f"Missing required field '{key}'", "critical")

    def _check_naming(self):
        full_name = str(self.payload.get("fullName", ""))
        if not full_name:
            return

        if self.metadata_type in {"CustomObject", "CustomField"} and "__" not in full_name:
            self._deduct("naming", 8, "Custom metadata fullName should use Salesforce suffixes (for example __c)", "warning")

        if re.search(r"\s", full_name):
            self._deduct("naming", 6, "fullName should not contain whitespace", "critical")

    def _check_security(self):
        # ValidationRule formula scanning for fragile syntax patterns.
        formula = str(self.payload.get("errorConditionFormula", ""))
        formula_findings = analyze_formula_safety(formula)
        for finding in formula_findings:
            self._deduct("security", 5, finding, "warning")

        # PermissionSet should avoid granting ModifyAllData by default.
        if self.metadata_type == "PermissionSet":
            if self.payload.get("hasModifyAllData") is True:
                self._deduct("security", 10, "PermissionSet grants ModifyAllData; verify least-privilege intent", "critical")

    def _check_documentation(self):
        description = self.payload.get("description")
        if not isinstance(description, str) or not description.strip():
            self._deduct("documentation", 4, "Description is missing or empty", "warning")

    def _check_deployability(self):
        if self.metadata_type == "CustomObject":
            if self.payload.get("deploymentStatus") not in {"Deployed", "InDevelopment"}:
                self._deduct("deployability", 8, "deploymentStatus should be Deployed or InDevelopment", "critical")

    def _check_maintainability(self):
        if self.metadata_type == "ValidationRule":
            formula = str(self.payload.get("errorConditionFormula", ""))
            if len(formula) > 250:
                self._deduct("maintainability", 6, "Validation rule formula is long; consider splitting logic", "warning")

    def _deduct(self, category: str, points: int, message: str, severity: str):
        cat = self.categories[category]
        cat["score"] = max(0, cat["score"] - points)
        cat["issues"].append(message)
        self.issues.append({"category": category, "severity": severity, "message": message, "points": points})

    def _result(self) -> dict[str, Any]:
        total = sum(info["score"] for info in self.categories.values())
        if any(issue["severity"] == "critical" for issue in self.issues):
            status = "critical"
        elif total >= 96:
            status = "pass"
        elif total >= 72:
            status = "needs_attention"
        else:
            status = "critical"
        return {
            "metadata_type": self.metadata_type,
            "overall_score": total,
            "max_score": MAX_SCORE,
            "status": status,
            "categories": self.categories,
            "issues": self.issues,
            "required_keys_present": all(k in self.payload for k in ("fullName",)),
        }


def analyze_formula_safety(formula: str) -> list[str]:
    """Detect parser edge-case patterns likely to break regex/line scanners."""
    if not formula:
        return []

    findings: list[str] = []
    scrubbed = _strip_line_comments(formula)

    if re.search(r"for\s*\([^)]*\)\s*\{[^}]*\}", scrubbed, re.IGNORECASE):
        findings.append("single-line braced loop syntax found")
    if re.search(r"for\s*\([^)]*\)\s*[^\s{]", scrubbed, re.IGNORECASE):
        findings.append("braceless loop syntax found")
    if re.search(r"do\s*\{[\s\S]*?\}\s*while\s*\([^)]*\)", scrubbed, re.IGNORECASE):
        findings.append("do/while loop style found")
    if "==" in scrubbed:
        findings.append("double equals operator found")

    return findings


def _strip_line_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines() or [text]:
        lines.append(line.split("//", 1)[0])
    return "\n".join(lines)
