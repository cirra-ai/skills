#!/usr/bin/env python3
"""MCP validation adapter for LWC metadata deployments.

Validates LightningComponentBundle payloads sent through metadata MCP tools and
returns a stable, machine-readable result for orchestration logic.
"""

from __future__ import annotations

import base64
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

_SCRIPT_DIR = str(Path(__file__).resolve().parent)

SUPPORTED_TOOLS = ("metadata_create", "metadata_update", "tooling_api_dml")
TARGET_METADATA_TYPE = "LightningComponentBundle"


def _parse_api_version(value: Any) -> float | None:
    """Parse an apiVersion value ('67.0', 67, 67.0) to float, None if absent/bad."""
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _maybe_b64decode(source: str) -> str:
    """Return the decoded text when `source` is Base64, the raw text otherwise.

    The MCP deploy format sends lwcResource sources Base64-encoded, but tests
    and some integrations pass plain text. Plain HTML/JS always contains
    characters outside the Base64 alphabet (e.g. '<', ';', whitespace), so a
    strict decode succeeding is a reliable signal.
    """
    stripped = source.strip()
    if not stripped or not re.fullmatch(r"[A-Za-z0-9+/=\s]+", stripped):
        return source
    try:
        decoded = base64.b64decode(stripped, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return source
    return decoded


def _extract_payload(tool: str, params: dict[str, Any]) -> tuple[str, str, str, str, float | None]:
    """Extract (metadata_type, content, full_name, js_content, api_version) from MCP params.

    api_version comes from the top-level metadata field (the MCP deploy format —
    the .js-meta.xml is generated server-side from it), falling back to a
    .js-meta.xml resource when one is included; None when neither is present.
    js_content joins the bundle's .js sources. Sources are Base64-decoded when
    encoded, per the MCP deploy format.
    """
    metadata_type = ""
    content = ""
    full_name = ""
    js_content = ""
    api_version: float | None = None

    if tool in ("metadata_create", "metadata_update"):
        metadata_type = params.get("type", "")
        metadata_list = params.get("metadata", [])
        if isinstance(metadata_list, list) and metadata_list:
            first = metadata_list[0]
            if isinstance(first, dict):
                full_name = first.get("fullName", "")
                api_version = _parse_api_version(first.get("apiVersion", first.get("ApiVersion")))
                # Most common representations for tests and integrations.
                content = first.get("content", "") or first.get("body", "") or first.get("html", "")

                resources_raw = first.get("lwcResources", [])
                # The MCP tool sends {"lwcResource": [...]} (dict), not a flat list.
                # Handle both formats for forward compatibility.
                if isinstance(resources_raw, dict):
                    resources = resources_raw.get("lwcResource", [])
                elif isinstance(resources_raw, list):
                    resources = resources_raw
                else:
                    resources = []
                if isinstance(resources, list):
                    html_sources = []
                    js_sources = []
                    for r in resources:
                        if not isinstance(r, dict):
                            continue
                        file_path = str(r.get("filePath", ""))
                        source = r.get("source", "")
                        if not source:
                            continue
                        source = _maybe_b64decode(source)
                        if file_path.endswith(".html"):
                            html_sources.append(source)
                        elif file_path.endswith(".js") and not file_path.endswith(".js-meta.xml"):
                            js_sources.append(source)
                        elif file_path.endswith(".js-meta.xml") and api_version is None:
                            m = re.search(r"<apiVersion>\s*([\d.]+)\s*</apiVersion>", source)
                            if m:
                                api_version = _parse_api_version(m.group(1))
                    if not content:
                        content = "\n".join(html_sources)
                    js_content = "\n".join(js_sources)

    elif tool == "tooling_api_dml":
        sobject = params.get("sObject", "")
        metadata_type = TARGET_METADATA_TYPE if sobject == TARGET_METADATA_TYPE else sobject
        record = params.get("record", {})
        if isinstance(record, dict):
            full_name = record.get("FullName", "") or record.get("DeveloperName", "")
            raw = record.get("Body", "") or record.get("Metadata", "")
            content = raw if isinstance(raw, str) else ""

    return metadata_type, content, full_name, js_content, api_version


# Features gated on the bundle's declared apiVersion. Floors follow the skill's
# reference docs (Spring '26 features require API 66.0+). Only flagged when the
# payload declares a version BELOW the floor — an undeclared version is not
# judged, since new components default to a current (>= floor) version.
_VERSION_GATED_FEATURES = (
    # (floor, where, compiled regex, feature label)
    (66.0, "html", re.compile(r"\blwc:on\b"), "lwc:on directive"),
    (66.0, "js", re.compile(r"\bexecuteMutation\b"), "GraphQL executeMutation"),
)


def _check_version_floors(html: str, js: str, api_version: float | None) -> list[dict[str, Any]]:
    """Flag version-gated features used below their required apiVersion."""
    if api_version is None:
        return []
    issues = []
    for floor, where, pattern, label in _VERSION_GATED_FEATURES:
        if api_version >= floor:
            continue
        haystack = html if where == "html" else js
        if haystack and pattern.search(haystack):
            issues.append(
                {
                    "severity": "CRITICAL",
                    "category": "api_version",
                    "message": (
                        f"{label} requires apiVersion {floor:g}+, "
                        f"but bundle declares {api_version:g}"
                    ),
                    "fix": f"Raise <apiVersion> in the .js-meta.xml to {floor:g} or later",
                }
            )
    return issues


class LWCMCPValidator:
    """Validate MCP deployment payloads for LightningComponentBundle."""

    def validate(self, input_data: dict[str, Any]) -> dict[str, Any]:
        tool = input_data.get("tool", "")
        params = input_data.get("params", {}) or {}

        base = {
            "tier": "metadata",
            "tool": tool,
            "metadata_type": "",
            "status": "error",
            "validator": "sf-lwc.mcp_validator",
        }

        if tool not in SUPPORTED_TOOLS:
            return {
                **base,
                "status": "error",
                "message": f"Unsupported tool '{tool}'",
            }

        metadata_type, content, full_name, js_content, api_version = _extract_payload(tool, params)
        base["metadata_type"] = metadata_type
        if full_name:
            base["full_name"] = full_name

        if metadata_type != TARGET_METADATA_TYPE:
            return {
                **base,
                "status": "skipped",
                "message": f"Metadata type '{metadata_type}' is not targeted by this validator",
            }

        if not str(content).strip():
            return {
                **base,
                "status": "error",
                "message": "Missing or empty LWC payload content",
            }

        try:
            if _SCRIPT_DIR not in sys.path:
                sys.path.insert(0, _SCRIPT_DIR)
            from template_validator import LWCTemplateValidator
            from validate_slds import SLDSValidator

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
                f.write(content)
                temp_path = f.name

            try:
                slds = SLDSValidator(temp_path).validate()
                template = LWCTemplateValidator(temp_path).validate()
            finally:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

            max_score = slds.get("max_score", 0) or 1
            base_score = slds.get("score", 0)
            all_issues = list(template.get("issues", []))
            all_issues.extend(_check_version_floors(content, js_content, api_version))
            critical = [i for i in all_issues if i.get("severity") == "CRITICAL"]
            warnings = [i for i in all_issues if i.get("severity") == "WARNING"]

            adjusted_score = max(0, base_score - (len(critical) * 3))

            return {
                **base,
                "status": "scored",
                "score": adjusted_score,
                "max_score": max_score,
                "critical_count": len(critical),
                "warning_count": len(warnings),
                "issues": all_issues,
            }
        except Exception as exc:  # pragma: no cover - safety fallback
            return {
                **base,
                "status": "error",
                "message": f"Validation failed: {exc}",
            }


__all__ = ["LWCMCPValidator"]
