"""Tests for FlowMCPValidator — MCP deployment validation efficiency.

Verifies that:
  - Valid flows pass through MCP validation in a single call (no back-and-forth)
  - Anti-pattern flows are blocked with actionable error messages
  - Non-Flow metadata types are skipped efficiently
  - Score thresholds match deployment gates (80% = 88/110)
  - The validator handles edge cases (empty body, missing type, etc.)

Each test simulates a single MCP tool call and checks the response — the goal
is to validate that the LLM + MCP interaction requires minimal round-trips.
"""

import os

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-flow/scripts/mcp_validator.py")
FlowMCPValidator = mod.FlowMCPValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


# ── helpers ──────────────────────────────────────────────────────────────────


def _read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as f:
        return f.read()


def _mcp_create(full_name: str, xml_body: str) -> dict:
    """Simulate a metadata_create call and return the validator result."""
    return FlowMCPValidator().validate(
        {
            "tool": "metadata_create",
            "params": {
                "type": "Flow",
                "metadata": [{"fullName": full_name, "content": xml_body}],
            },
        }
    )


def _mcp_tooling_dml(sobject: str, body: str, full_name: str = "TestFlow") -> dict:
    """Simulate a tooling_api_dml call."""
    return FlowMCPValidator().validate(
        {
            "tool": "tooling_api_dml",
            "params": {
                "sObject": sobject,
                "record": {"FullName": full_name, "Body": body},
            },
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SINGLE-CALL DEPLOYMENT — valid flows pass in one shot
# ═══════════════════════════════════════════════════════════════════════════════


class TestSingleCallDeployment:
    def test_valid_before_save_passes(self):
        """TC-M1: Valid before-save flow passes MCP validation in one call."""
        body = _read_fixture("perfect_before_save.flow-meta.xml")
        r = _mcp_create("Before_Lead_Priority", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88

    def test_valid_after_save_passes(self):
        """TC-M2: Valid after-save flow passes MCP validation in one call."""
        body = _read_fixture("perfect_after_save.flow-meta.xml")
        r = _mcp_create("Auto_Opportunity_Task", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88

    def test_complex_flow_passes(self):
        """TC-M3: Complex multi-object flow passes in one call."""
        body = _read_fixture("complex_multi_object.flow-meta.xml")
        r = _mcp_create("Auto_Account_Address_Sync", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88

    def test_screen_flow_passes(self):
        """TC-M4: Screen flow passes in one call."""
        body = _read_fixture("screen_flow_simple.flow-meta.xml")
        r = _mcp_create("Screen_Case_Intake", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88

    def test_scheduled_flow_passes(self):
        """TC-M5: Scheduled flow passes in one call."""
        body = _read_fixture("scheduled_flow.flow-meta.xml")
        r = _mcp_create("Sched_Stale_Opp_Cleanup", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANTI-PATTERN BLOCKING — bad flows are caught before deployment
# ═══════════════════════════════════════════════════════════════════════════════


class TestAntiPatternBlocking:
    def test_dml_in_loop_low_score(self):
        """TC-M6: DML-in-loop flow gets score below deploy threshold."""
        body = _read_fixture("dml_in_loop.flow-meta.xml")
        r = _mcp_create("Auto_Contact_Sync_Bad", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score < 88

    def test_max_anti_patterns_very_low(self):
        """TC-M7: Maximally flawed flow gets very low score."""
        body = _read_fixture("max_complexity_anti_patterns.flow-meta.xml")
        r = _mcp_create("Bad_Flow", body)
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score <= 50

    def test_missing_faults_flagged(self):
        """TC-M8: Missing fault paths are included in result."""
        body = _read_fixture("missing_fault_paths.flow-meta.xml")
        r = _mcp_create("Auto_Case_Escalation", body)
        assert r["status"] == "scored"
        warnings = r.get("warnings", [])
        assert len(warnings) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. EFFICIENT SKIPPING — non-Flow types skip without overhead
# ═══════════════════════════════════════════════════════════════════════════════


class TestEfficientSkipping:
    def test_non_flow_type_skipped(self):
        """TC-M9: Non-Flow metadata type is skipped immediately."""
        r = FlowMCPValidator().validate(
            {
                "tool": "metadata_create",
                "params": {
                    "type": "CustomObject",
                    "metadata": [{"fullName": "MyObj__c", "content": "<xml/>"}],
                },
            }
        )
        assert r["status"] == "skipped"

    def test_unsupported_tool_errors(self):
        """TC-M10: Non-deployment tool returns error immediately."""
        r = FlowMCPValidator().validate(
            {
                "tool": "soql_query",
                "params": {"query": "SELECT Id FROM Account"},
            }
        )
        assert r["status"] == "error"

    def test_empty_body_errors(self):
        """TC-M11: Empty Flow body returns error (no wasted validation)."""
        r = _mcp_create("Empty_Flow", "")
        assert r["status"] == "error"

    def test_missing_type_errors(self):
        """TC-M12: Missing metadata type returns error."""
        r = FlowMCPValidator().validate(
            {
                "tool": "metadata_create",
                "params": {"metadata": [{"fullName": "X", "content": "<Flow/>"}]},
            }
        )
        assert r["status"] == "error"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TOOLING API PATH — alternative deployment mechanism
# ═══════════════════════════════════════════════════════════════════════════════


class TestToolingApiPath:
    def test_tooling_dml_flow_scored(self):
        """TC-M13: Flow deployed via tooling_api_dml is also validated."""
        body = _read_fixture("perfect_before_save.flow-meta.xml")
        r = _mcp_tooling_dml("Flow", body, "Before_Lead_Priority")
        assert r["status"] == "scored"
        score = r.get("overall_score", r.get("score", 0))
        assert score >= 88

    def test_tooling_dml_non_flow_skipped(self):
        """TC-M14: Non-Flow sObject via tooling_api_dml is skipped."""
        r = _mcp_tooling_dml("ApexClass", "<xml/>", "MyClass")
        assert r["status"] == "skipped"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. RESULT STRUCTURE — validator returns usable metadata
# ═══════════════════════════════════════════════════════════════════════════════


class TestResultStructure:
    def test_result_has_required_keys(self):
        """TC-M15: Scored result contains all keys needed for LLM decision-making."""
        body = _read_fixture("perfect_before_save.flow-meta.xml")
        r = _mcp_create("Test_Flow", body)
        assert "tier" in r
        assert "tool" in r
        assert "metadata_type" in r
        assert "status" in r
        assert "validator" in r

    def test_full_name_preserved(self):
        """TC-M16: fullName from MCP params is preserved in result."""
        body = _read_fixture("perfect_before_save.flow-meta.xml")
        r = _mcp_create("My_Custom_Flow_Name", body)
        assert r.get("full_name") == "My_Custom_Flow_Name"

    def test_metadata_type_is_flow(self):
        """TC-M17: metadata_type is correctly set to 'Flow'."""
        body = _read_fixture("perfect_before_save.flow-meta.xml")
        r = _mcp_create("Test_Flow", body)
        assert r["metadata_type"] == "Flow"
