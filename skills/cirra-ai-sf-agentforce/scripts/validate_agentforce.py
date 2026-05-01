#!/usr/bin/env python3
"""Salesforce Agentforce metadata validator with 100-point scoring."""

from __future__ import annotations

import re
from typing import Any

CATEGORIES = {
    "agent_configuration": 20,
    "topic_action_design": 25,
    "metadata_quality": 20,
    "integration_patterns": 15,
    "prompt_template_usage": 10,
    "deployment_readiness": 10,
}
MAX_SCORE = sum(CATEGORIES.values())

SUPPORTED_METADATA_TYPES = {
    "GenAiFunction",
    "GenAiPlugin",
    "PromptTemplate",
}


class AgentforceValidator:
    """Score a single Agentforce metadata payload."""

    def __init__(self, metadata_type: str, payload: dict[str, Any]):
        self.metadata_type = metadata_type
        self.payload = payload
        self.categories = {k: {"max": v, "score": v, "issues": []} for k, v in CATEGORIES.items()}
        self.issues: list[dict[str, Any]] = []

    def validate(self) -> dict[str, Any]:
        if self.metadata_type not in SUPPORTED_METADATA_TYPES:
            self._deduct("agent_configuration", 20, f"Unsupported metadata type: {self.metadata_type}", "critical")
            return self._result()

        if not isinstance(self.payload, dict) or not self.payload:
            self._deduct("metadata_quality", 20, "Metadata payload is missing or empty", "critical")
            return self._result()

        self._check_required_fields()
        self._check_naming()
        self._check_description_quality()
        self._check_capabilities()
        self._check_inputs_outputs()
        self._check_integration()
        self._check_deployment()

        return self._result()

    def _check_required_fields(self):
        required_by_type = {
            "GenAiFunction": ("apiName", "description", "invocationTarget", "invocationTargetType"),
            "GenAiPlugin": ("apiName", "description"),
            "PromptTemplate": ("name", "templateType"),
        }
        for key in required_by_type.get(self.metadata_type, ()):
            if key not in self.payload:
                self._deduct("metadata_quality", 5, f"Missing required field '{key}'", "critical")

    def _check_naming(self):
        api_name = str(self.payload.get("apiName", self.payload.get("name", "")))
        if not api_name:
            return

        if re.search(r"\s", api_name):
            self._deduct("metadata_quality", 5, "apiName should not contain whitespace", "critical")

        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", api_name):
            self._deduct("metadata_quality", 3, "apiName should use alphanumeric characters and underscores only", "warning")

    def _check_description_quality(self):
        description = self.payload.get("description", "")
        if not isinstance(description, str) or not description.strip():
            self._deduct("topic_action_design", 8, "Description is missing or empty", "critical")
        elif len(description.strip()) < 20:
            self._deduct("topic_action_design", 4, "Description is too short; provide clear guidance for the agent", "warning")

    def _check_capabilities(self):
        if self.metadata_type == "GenAiFunction":
            capabilities = self.payload.get("capabilities", [])
            if not capabilities:
                self._deduct("agent_configuration", 5, "No capabilities defined; function may not be discoverable by agents", "warning")

        if self.metadata_type == "GenAiPlugin":
            functions = self.payload.get("genAiFunctions", [])
            if not functions:
                self._deduct("agent_configuration", 8, "GenAiPlugin has no functions listed", "critical")

    def _check_inputs_outputs(self):
        if self.metadata_type != "GenAiFunction":
            return

        inputs = self.payload.get("inputs", [])
        if not inputs:
            self._deduct("topic_action_design", 5, "No inputs defined for GenAiFunction", "warning")

        outputs = self.payload.get("outputs", [])
        if not outputs:
            self._deduct("topic_action_design", 4, "No outputs defined for GenAiFunction", "warning")

        for inp in inputs:
            if isinstance(inp, dict) and not inp.get("description"):
                self._deduct("topic_action_design", 2, f"Input '{inp.get('name', '?')}' lacks a description", "warning")

    def _check_integration(self):
        if self.metadata_type == "GenAiFunction":
            target = self.payload.get("invocationTarget", "")
            target_type = self.payload.get("invocationTargetType", "")
            normalized_target_type = target_type.lower() if isinstance(target_type, str) else ""
            requires_qualified_apex_reference = "apex" in normalized_target_type
            if (
                requires_qualified_apex_reference
                and isinstance(target, str)
                and target
                and "." not in target
            ):
                self._deduct("integration_patterns", 3, "invocationTarget may be incomplete for an Apex target; expected a qualified class.method reference", "warning")

        if self.metadata_type == "PromptTemplate":
            template_type = self.payload.get("templateType", "")
            valid_types = {"flexPrompt", "salesGeneration", "fieldCompletion", "recordSummary"}
            if template_type and template_type not in valid_types:
                self._deduct("prompt_template_usage", 5, f"Unknown templateType '{template_type}'", "warning")

    def _check_deployment(self):
        if self.metadata_type == "GenAiFunction":
            target = self.payload.get("invocationTarget", "")
            if not target:
                self._deduct("deployment_readiness", 5, "No invocationTarget; function cannot be deployed", "critical")

        if self.metadata_type == "PromptTemplate":
            if not self.payload.get("name"):
                self._deduct("deployment_readiness", 5, "PromptTemplate has no name; cannot be deployed", "critical")

    def _deduct(self, category: str, points: int, message: str, severity: str):
        cat = self.categories[category]
        cat["score"] = max(0, cat["score"] - points)
        cat["issues"].append(message)
        self.issues.append({"category": category, "severity": severity, "message": message, "points": points})

    def _result(self) -> dict[str, Any]:
        total = sum(info["score"] for info in self.categories.values())
        if any(issue["severity"] == "critical" for issue in self.issues):
            status = "critical"
        elif total >= MAX_SCORE * 0.8:
            status = "pass"
        elif total >= MAX_SCORE * 0.6:
            status = "needs_attention"
        else:
            status = "fail"
        return {
            "metadata_type": self.metadata_type,
            "overall_score": total,
            "max_score": MAX_SCORE,
            "status": status,
            "categories": self.categories,
            "issues": self.issues,
        }
