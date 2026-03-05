"""Tests for Flow deployment readiness — structural checks verified against live org.

These checks were derived from actual MCP metadata_create deployments to a
Salesforce sandbox (Master Demo Org 2, API 65.0). Flows that fail these checks
will deploy but end up as InvalidDraft (cannot be activated).

Findings from live deployment testing (2026-03-05):
  - Scheduled flows MUST have <triggerType>Scheduled</triggerType> in <start>
    or they become InvalidDraft despite having a <schedule> block.
  - <bulkSupport> was removed in API 60.0+ and should not be present.
  - Custom field references (e.g. Priority__c) are accepted in Draft but will
    fail activation if the field doesn't exist in the target org.
  - All 5 fixture flow types (before-save, after-save, screen, scheduled,
    complex multi-object) deployed successfully in one shot after fixes.
"""

import os
import sys

# Import runtime module from scripts/
SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"
)
sys.path.insert(0, SCRIPTS_DIR)

from deploy_readiness import (  # noqa: E402
    _has_bulk_support,
    _has_trigger_type,
    _parse_flow,
    check_deploy_readiness,
)


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


# =============================================================================
# 1. FIXTURE FLOWS — all must be deployment-ready
# =============================================================================


class TestFixtureDeployReadiness:
    """Every 'perfect' fixture must pass deployment-readiness checks.

    These fixtures were actually deployed to a live Salesforce sandbox via
    metadata_create and verified to achieve Draft status (not InvalidDraft).
    """

    def test_before_save_deploy_ready(self):
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "perfect_before_save.flow-meta.xml")
        )
        errors = [i for i in r["issues"] if i["severity"] == "ERROR"]
        assert r["ready"], f"Deploy issues: {errors}"

    def test_before_save_warns_custom_field(self):
        """Before-save fixture references TEST_Priority__c — should warn."""
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "perfect_before_save.flow-meta.xml")
        )
        checks = [i["check"] for i in r["issues"]]
        assert "custom_field_references" in checks
        # It's a warning, not an error — flow is still ready
        assert r["ready"]

    def test_after_save_deploy_ready(self):
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "perfect_after_save.flow-meta.xml")
        )
        errors = [i for i in r["issues"] if i["severity"] == "ERROR"]
        assert r["ready"], f"Deploy issues: {errors}"

    def test_screen_flow_deploy_ready(self):
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "screen_flow_simple.flow-meta.xml")
        )
        errors = [i for i in r["issues"] if i["severity"] == "ERROR"]
        assert r["ready"], f"Deploy issues: {errors}"

    def test_scheduled_flow_deploy_ready(self):
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "scheduled_flow.flow-meta.xml")
        )
        errors = [i for i in r["issues"] if i["severity"] == "ERROR"]
        assert r["ready"], f"Deploy issues: {errors}"

    def test_complex_multi_object_deploy_ready(self):
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "complex_multi_object.flow-meta.xml")
        )
        errors = [i for i in r["issues"] if i["severity"] == "ERROR"]
        assert r["ready"], f"Deploy issues: {errors}"


# =============================================================================
# 2. ASSET TEMPLATES — shipped templates must be deployment-ready
# =============================================================================


class TestAssetTemplateDeployReadiness:
    """Templates in assets/ are used to generate flows. They must not
    contain structural issues that would cause InvalidDraft on deployment.
    """

    def test_scheduled_template_has_trigger_type(self):
        root = _parse_flow(
            os.path.join(ASSETS_DIR, "scheduled-flow-template.xml")
        )
        assert _has_trigger_type(root, "Scheduled"), (
            "Scheduled flow template missing <triggerType>Scheduled</triggerType> "
            "in <start> — all generated scheduled flows will be InvalidDraft"
        )

    def test_scheduled_template_no_bulk_support(self):
        root = _parse_flow(
            os.path.join(ASSETS_DIR, "scheduled-flow-template.xml")
        )
        assert not _has_bulk_support(root), (
            "Scheduled flow template has deprecated <bulkSupport> — "
            "removed in API 60.0+"
        )

    def test_all_templates_no_bulk_support(self):
        """No template should use bulkSupport (deprecated API 60.0+)."""
        for name in sorted(os.listdir(ASSETS_DIR)):
            if not name.endswith(".xml"):
                continue
            path = os.path.join(ASSETS_DIR, name)
            root = _parse_flow(path)
            assert not _has_bulk_support(root), (
                f"Template {name} has deprecated <bulkSupport>"
            )

    def test_record_triggered_templates_have_trigger_type(self):
        """All record-triggered templates must have triggerType."""
        for name in sorted(os.listdir(ASSETS_DIR)):
            if not name.startswith("record-triggered") or not name.endswith(".xml"):
                continue
            path = os.path.join(ASSETS_DIR, name)
            root = _parse_flow(path)
            assert _has_trigger_type(root), (
                f"Template {name} missing <triggerType> in <start>"
            )


# =============================================================================
# 3. REGRESSION CHECKS — issues found during live deployment
# =============================================================================


class TestDeploymentRegressions:
    """Regression tests for specific issues found during MCP deployment testing."""

    def test_scheduled_flow_without_trigger_type_detected(self):
        """A scheduled flow missing triggerType must be flagged."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <label>Bad Scheduled Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <schedule>
            <frequency>Daily</frequency>
            <startDate>2025-01-01</startDate>
            <startTime>02:00:00.000Z</startTime>
        </schedule>
    </start>
    <status>Draft</status>
</Flow>"""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".flow-meta.xml", delete=False
        ) as f:
            f.write(xml)
            tmp = f.name
        try:
            r = check_deploy_readiness(tmp)
            assert not r["ready"]
            checks = [i["check"] for i in r["issues"]]
            assert "scheduled_trigger_type" in checks
        finally:
            os.unlink(tmp)

    def test_bulk_support_in_api_65_detected(self):
        """bulkSupport in API 65.0 flow must be flagged as ERROR."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <label>Flow With BulkSupport</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <bulkSupport>true</bulkSupport>
    </start>
    <status>Draft</status>
</Flow>"""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".flow-meta.xml", delete=False
        ) as f:
            f.write(xml)
            tmp = f.name
        try:
            r = check_deploy_readiness(tmp)
            assert not r["ready"]
            checks = [i["check"] for i in r["issues"]]
            assert "deprecated_bulk_support" in checks
        finally:
            os.unlink(tmp)

    def test_invalid_scheduled_flow_fixture_detected(self):
        """The invalid scheduled flow fixture (missing triggerType) must be flagged."""
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "scheduled_flow_missing_trigger_type.flow-meta.xml")
        )
        assert not r["ready"]
        checks = [i["check"] for i in r["issues"]]
        assert "scheduled_trigger_type" in checks

    def test_custom_field_ref_warned(self):
        """Custom field references should produce a warning (not error)."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <assignments>
        <name>Set_Field</name>
        <label>Set Field</label>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <assignmentItems>
            <assignToReference>$Record.Custom_Field__c</assignToReference>
            <operator>Assign</operator>
            <value><stringValue>test</stringValue></value>
        </assignmentItems>
    </assignments>
    <label>Custom Field Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <object>Account</object>
        <recordTriggerType>Create</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
        <connector>
            <targetReference>Set_Field</targetReference>
        </connector>
    </start>
    <status>Draft</status>
</Flow>"""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".flow-meta.xml", delete=False
        ) as f:
            f.write(xml)
            tmp = f.name
        try:
            r = check_deploy_readiness(tmp)
            # Custom fields are WARN, not ERROR — flow is still ready
            assert r["ready"]
            checks = [i["check"] for i in r["issues"]]
            assert "custom_field_references" in checks
        finally:
            os.unlink(tmp)

    def test_missing_field_detected_with_org_fields(self):
        """When org_fields is provided, missing custom fields become ERROR."""
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "before_save_missing_field.flow-meta.xml"),
            org_fields=["AnnualRevenue", "Name", "Status"],  # no TEST_Invalid__c
        )
        assert not r["ready"]
        checks = [i["check"] for i in r["issues"]]
        assert "missing_custom_fields" in checks
        # Verify the missing field name is in the message
        missing_issue = next(i for i in r["issues"] if i["check"] == "missing_custom_fields")
        assert "TEST_Invalid__c" in missing_issue["message"]

    def test_present_field_not_flagged_as_error(self):
        """When org_fields confirms a field exists, it should NOT be an error."""
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "perfect_before_save.flow-meta.xml"),
            org_fields=["TEST_Priority__c", "AnnualRevenue", "Name"],
        )
        assert r["ready"]
        checks = [i["check"] for i in r["issues"]]
        assert "missing_custom_fields" not in checks

    def test_missing_field_without_org_fields_is_warn(self):
        """Without org_fields, custom field refs are WARN only (not blocking)."""
        r = check_deploy_readiness(
            os.path.join(FIXTURES_DIR, "before_save_missing_field.flow-meta.xml"),
        )
        assert r["ready"]  # WARN doesn't block
        checks = [i["check"] for i in r["issues"]]
        assert "custom_field_references" in checks
