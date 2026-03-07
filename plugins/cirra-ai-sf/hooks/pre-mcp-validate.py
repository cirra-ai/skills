#!/usr/bin/env python3
"""
Plugin-level PreToolUse hook dispatcher for cirra-ai-sf.

Reads the hook input from stdin, determines the metadata type, runs
JSON Schema validation on the metadata payload, then delegates to the
appropriate sub-skill validator script for deeper analysis.

Currently registered delegates:
  - cirra-ai-sf-apex: ApexClass, ApexTrigger
  - cirra-ai-sf-flow: Flow, FlowDefinition
"""

import json
import os
import subprocess
import sys

_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(os.path.dirname(_PLUGIN_ROOT))

# Map metadata types to their validator script (relative to _PLUGIN_ROOT).
# Add new entries here as sub-skills gain their own pre-deploy validators.
_DELEGATES: dict[str, str] = {
    "ApexClass":      "skills/cirra-ai-sf-apex/scripts/pre-mcp-validate.py",
    "ApexTrigger":    "skills/cirra-ai-sf-apex/scripts/pre-mcp-validate.py",
    "Flow":           "skills/cirra-ai-sf-flow/scripts/pre-mcp-validate.py",
    "FlowDefinition": "skills/cirra-ai-sf-flow/scripts/pre-mcp-validate.py",
}

# Map metadata types to their JSON Schema file (relative to _REPO_ROOT).
_SCHEMAS: dict[str, str] = {
    "CustomField":       "skills/cirra-ai-sf-metadata/references/customfield-metadata-schema.json",
    "CustomObject":      "skills/cirra-ai-sf-metadata/references/customobject-metadata-schema.json",
    "FlexiPage":         "skills/cirra-ai-sf-metadata/references/flexipage-metadata-schema.json",
    "Layout":            "skills/cirra-ai-sf-metadata/references/layout-metadata-schema.json",
    "QuickAction":       "skills/cirra-ai-sf-metadata/references/quickaction-metadata-schema.json",
    "RecordType":        "skills/cirra-ai-sf-metadata/references/recordtype-metadata-schema.json",
    "ValidationRule":    "skills/cirra-ai-sf-metadata/references/validationrule-metadata-schema.json",
    "PermissionSet":     "skills/cirra-ai-sf-permissions/references/permissionset-metadata-schema.json",
    "PermissionSetGroup": "skills/cirra-ai-sf-permissions/references/permissionsetgroup-metadata-schema.json",
    "Profile":           "skills/cirra-ai-sf-permissions/references/profile-metadata-schema.json",
    "SharingRules":      "skills/cirra-ai-sf-permissions/references/sharingrules-metadata-schema.json",
}
# Note: Flow and FlowDefinition are NOT in _SCHEMAS because they have
# delegate validators that provide richer feedback (110-point rubric).

# Cache loaded schemas to avoid re-reading per item.
_schema_cache: dict[str, dict] = {}


def _allow(context: str = "") -> dict:
    out: dict = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}
    if context:
        out["hookSpecificOutput"]["additionalContext"] = context
    return out


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _metadata_type(tool_name: str, tool_input: dict) -> str:
    """Extract the metadata type from hook input fields."""
    parts = tool_name.split("__", 2)
    base_tool = parts[2] if tool_name.startswith("mcp__") and len(parts) > 2 else tool_name

    if base_tool in ("metadata_create", "metadata_update"):
        return tool_input.get("type", "")
    if base_tool == "tooling_api_dml":
        return tool_input.get("sObject", "")
    return ""


def _load_schema(metadata_type: str) -> dict | None:
    """Load and cache the JSON Schema for a metadata type. Returns None if unavailable."""
    if metadata_type in _schema_cache:
        return _schema_cache[metadata_type]

    rel_path = _SCHEMAS.get(metadata_type)
    if not rel_path:
        return None

    schema_path = os.path.join(_REPO_ROOT, rel_path)
    if not os.path.isfile(schema_path):
        return None

    try:
        with open(schema_path) as f:
            schema = json.load(f)
        _schema_cache[metadata_type] = schema
        return schema
    except Exception:
        return None


def _extract_metadata_items(tool_input: dict) -> list[dict]:
    """Extract the metadata item dicts to validate from the tool input."""
    # metadata_create / metadata_update: params.metadata is a list of dicts
    metadata_list = tool_input.get("metadata")
    if isinstance(metadata_list, list) and metadata_list:
        return [m for m in metadata_list if isinstance(m, dict)]

    # tooling_api_dml: params.record is a single dict
    record = tool_input.get("record")
    if isinstance(record, dict):
        return [record]

    return []


def _resolve_schema_root(schema: dict) -> dict:
    """Resolve a local $ref root (for example #/$defs/RecordType) when present."""
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return schema

    node: dict | list = schema
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            return schema
        node = node[part]
    return node if isinstance(node, dict) else schema


def _basic_schema_validate(item: dict, schema: dict) -> list[str]:
    """Fallback validator when jsonschema is unavailable.

    Supports required field checks and simple primitive type checks used by tests.
    """
    errors: list[str] = []
    root = _resolve_schema_root(schema)
    required = root.get("required", []) if isinstance(root, dict) else []
    properties = root.get("properties", {}) if isinstance(root, dict) else {}

    for field in required:
        if field not in item:
            errors.append(f"(root): {field!r} is a required property")

    for field, rules in properties.items():
        if field not in item or not isinstance(rules, dict):
            continue
        expected = rules.get("type")
        value = item[field]
        if expected == "boolean" and not isinstance(value, bool):
            errors.append(f"{field}: {value!r} is not of type 'boolean'")
        elif expected == "string" and not isinstance(value, str):
            errors.append(f"{field}: {value!r} is not of type 'string'")
        elif expected == "array" and not isinstance(value, list):
            errors.append(f"{field}: {value!r} is not of type 'array'")
        elif expected == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            errors.append(f"{field}: {value!r} is not of type 'integer'")

    return errors


def _validate_schema(metadata_type: str, tool_input: dict) -> str | None:
    """Run JSON Schema validation on metadata items.

    Returns an error message string if validation fails, or None if it passes
    (or if no schema is available for the type).
    """
    try:
        import jsonschema
    except ImportError:
        jsonschema = None

    schema = _load_schema(metadata_type)
    if schema is None:
        return None

    items = _extract_metadata_items(tool_input)
    if not items:
        return None

    errors: list[str] = []
    for i, item in enumerate(items):
        name = item.get("fullName", item.get("FullName", f"item[{i}]"))
        if jsonschema is not None:
            try:
                jsonschema.validate(instance=item, schema=schema)
            except jsonschema.ValidationError as exc:
                path = " → ".join(str(p) for p in exc.absolute_path) if exc.absolute_path else "(root)"
                errors.append(f"'{name}' at {path}: {exc.message}")
        else:
            for err in _basic_schema_validate(item, schema):
                errors.append(f"'{name}' at {err}")

    if not errors:
        return None

    header = f"JSON Schema validation failed for {metadata_type}:\n"
    detail = "\n".join(f"• {e}" for e in errors[:5])
    if len(errors) > 5:
        detail += f"\n• ...and {len(errors) - 5} more errors"
    return header + detail


def main() -> int:
    try:
        raw = sys.stdin.buffer.read()
        hook_input = json.loads(raw)
    except Exception:
        print(json.dumps(_allow()))
        return 0

    tool_input = hook_input.get("tool_input", {})
    metadata_type = _metadata_type(hook_input.get("tool_name", ""), tool_input)

    if not metadata_type:
        print(json.dumps(_allow()))
        return 0

    # --- Delegate to sub-skill custom validator (takes priority) ---
    delegate_script = _DELEGATES.get(metadata_type)
    if delegate_script:
        script_path = os.path.join(_PLUGIN_ROOT, delegate_script)
        result = subprocess.run(
            [sys.executable, script_path],
            input=raw,
            capture_output=True,
        )

        output = result.stdout.strip()
        if output:
            print(output.decode("utf-8", errors="replace"))
        else:
            print(json.dumps(_allow()))
        return 0

    # --- JSON Schema validation (for types without a delegate) ---
    schema_error = _validate_schema(metadata_type, tool_input)
    if schema_error:
        print(json.dumps(_deny(schema_error)))
        return 0

    print(json.dumps(_allow()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
