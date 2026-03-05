"""Tests for plugins/cirra-ai-sf/hooks/pre-mcp-validate.py — JSON Schema validation."""

from conftest import load_script

mod = load_script("plugins/cirra-ai-sf/hooks/pre-mcp-validate.py")


def _hook_output(tool_name: str, tool_input: dict) -> dict:
    """Run schema validation via the module helper and return the hook decision."""
    metadata_type = mod._metadata_type(tool_name, tool_input)
    error = mod._validate_schema(metadata_type, tool_input)
    if error:
        return mod._deny(error)
    return mod._allow()


def _decision(output: dict) -> str:
    return output["hookSpecificOutput"]["permissionDecision"]


# ── Schema validation: valid payload passes ──────────────────────────────────


def test_valid_recordtype_passes():
    output = _hook_output(
        "mcp__cirra_ai__metadata_create",
        {
            "type": "RecordType",
            "metadata": [
                {
                    "fullName": "Account.Enterprise",
                    "active": True,
                    "label": "Enterprise",
                }
            ],
        },
    )
    assert _decision(output) == "allow"


# ── Schema validation: invalid payload denied ────────────────────────────────


def test_missing_required_field_denied():
    output = _hook_output(
        "mcp__cirra_ai__metadata_create",
        {
            "type": "RecordType",
            "metadata": [
                {
                    "fullName": "Account.Enterprise",
                    # missing required 'active' and 'label'
                }
            ],
        },
    )
    assert _decision(output) == "deny"
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "RecordType" in reason


def test_wrong_field_type_denied():
    output = _hook_output(
        "mcp__cirra_ai__metadata_create",
        {
            "type": "RecordType",
            "metadata": [
                {
                    "fullName": "Account.Enterprise",
                    "active": "not_a_boolean",  # should be bool
                    "label": "Enterprise",
                }
            ],
        },
    )
    assert _decision(output) == "deny"
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "active" in reason


# ── No schema available → allow through ──────────────────────────────────────


def test_unknown_type_allows():
    output = _hook_output(
        "mcp__cirra_ai__metadata_create",
        {"type": "SomeUnknownType", "metadata": [{"fullName": "Foo"}]},
    )
    assert _decision(output) == "allow"


# ── Empty metadata list → allow ──────────────────────────────────────────────


def test_empty_metadata_allows():
    output = _hook_output(
        "mcp__cirra_ai__metadata_create",
        {"type": "RecordType", "metadata": []},
    )
    assert _decision(output) == "allow"


# ── tooling_api_dml path ─────────────────────────────────────────────────────


def test_tooling_api_dml_invalid_denied():
    output = _hook_output(
        "mcp__cirra_ai__tooling_api_dml",
        {
            "sObject": "RecordType",
            "record": {
                "FullName": "Account.Enterprise",
                # missing required 'active' and 'label'
            },
        },
    )
    assert _decision(output) == "deny"


# ── metadata_type extraction ─────────────────────────────────────────────────


def test_metadata_type_from_mcp_prefixed_create():
    assert mod._metadata_type("mcp__cirra_ai__metadata_create", {"type": "CustomField"}) == "CustomField"


def test_metadata_type_from_tooling():
    assert mod._metadata_type("mcp__cirra_ai__tooling_api_dml", {"sObject": "Flow"}) == "Flow"


def test_metadata_type_unknown_tool():
    assert mod._metadata_type("mcp__cirra_ai__soql_query", {"query": "SELECT Id FROM Account"}) == ""
