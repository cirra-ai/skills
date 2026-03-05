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
import xml.etree.ElementTree as ET


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

_SF_NS = "http://soap.sforce.com/2006/04/metadata"
_NS = {"sf": _SF_NS}


# -- helpers ------------------------------------------------------------------


def _parse_flow(path: str) -> ET.Element:
    return ET.parse(path).getroot()


def _find(root: ET.Element, xpath: str) -> list[ET.Element]:
    return root.findall(xpath, _NS)


def _get_text(root: ET.Element, xpath: str) -> str | None:
    el = root.find(xpath, _NS)
    return el.text.strip() if el is not None and el.text else None


def _has_schedule(root: ET.Element) -> bool:
    return root.find(".//sf:start/sf:schedule", _NS) is not None


def _has_trigger_type(root: ET.Element, expected: str | None = None) -> bool:
    tt = root.find(".//sf:start/sf:triggerType", _NS)
    if tt is None:
        return False
    if expected:
        return tt.text and tt.text.strip() == expected
    return True


def _has_bulk_support(root: ET.Element) -> bool:
    return root.find(".//sf:bulkSupport", _NS) is not None


def _get_api_version(root: ET.Element) -> float:
    v = _get_text(root, "sf:apiVersion")
    return float(v) if v else 0.0


def _get_custom_field_refs(root: ET.Element) -> list[str]:
    """Find all references to custom fields (__c) in assignments and filters."""
    refs = []
    for el in root.iter():
        if el.text and "__c" in el.text:
            refs.append(el.text.strip())
    return refs


def _get_trigger_object(root: ET.Element) -> str | None:
    """Extract the trigger object from a record-triggered flow."""
    start = root.find("sf:start", _NS)
    if start is not None:
        obj = start.find("sf:object", _NS)
        if obj is not None and obj.text:
            return obj.text.strip()
    return None


def _extract_field_names_from_refs(refs: list[str]) -> list[str]:
    """Extract bare field API names from $Record.Field__c style references."""
    fields = []
    for ref in refs:
        # Handle $Record.Field__c pattern
        if "." in ref:
            field = ref.rsplit(".", 1)[-1]
        else:
            field = ref
        if field.endswith("__c") and field not in fields:
            fields.append(field)
    return fields


# -- deployment readiness checks (derived from live MCP testing) --------------


def check_deploy_readiness(path: str, org_fields: list[str] | None = None) -> dict:
    """Run deployment-readiness checks against a flow XML file.

    Args:
        path: Path to a .flow-meta.xml file.
        org_fields: Optional list of field API names that exist on the trigger
            object in the target org.  When provided, custom field references
            are checked against this list — missing fields are promoted from
            WARN to ERROR.

    Returns dict with:
      - ready: bool (True = will deploy as Draft, not InvalidDraft)
      - issues: list of issue dicts with severity and message
    """
    root = _parse_flow(path)
    issues = []

    # Check 1: Scheduled flows must have triggerType=Scheduled
    if _has_schedule(root) and not _has_trigger_type(root, "Scheduled"):
        issues.append({
            "severity": "ERROR",
            "check": "scheduled_trigger_type",
            "message": (
                "Flow has <schedule> in <start> but missing "
                "<triggerType>Scheduled</triggerType>. "
                "This causes InvalidDraft status — flow cannot be activated."
            ),
        })

    # Check 2: No bulkSupport (removed in API 60.0+)
    api_version = _get_api_version(root)
    if _has_bulk_support(root):
        issues.append({
            "severity": "ERROR" if api_version >= 60.0 else "WARN",
            "check": "deprecated_bulk_support",
            "message": (
                "<bulkSupport> was removed in API 60.0+. "
                "Remove it to avoid deployment issues."
            ),
        })

    # Check 3: Custom field references — warn or error depending on org_fields
    custom_refs = _get_custom_field_refs(root)
    if custom_refs:
        field_names = _extract_field_names_from_refs(custom_refs)
        if org_fields is not None:
            org_fields_set = set(org_fields)
            missing = [f for f in field_names if f not in org_fields_set]
            present = [f for f in field_names if f in org_fields_set]
            if missing:
                issues.append({
                    "severity": "ERROR",
                    "check": "missing_custom_fields",
                    "message": (
                        f"Flow references custom fields that do NOT exist "
                        f"on the target object: {missing}. "
                        "Create these fields before deploying the flow."
                    ),
                })
            if present:
                issues.append({
                    "severity": "INFO",
                    "check": "custom_field_references",
                    "message": (
                        f"Flow references custom fields (verified present): "
                        f"{present}."
                    ),
                })
        else:
            issues.append({
                "severity": "WARN",
                "check": "custom_field_references",
                "message": (
                    f"Flow references custom fields: {custom_refs}. "
                    "These must exist in the target org or activation will fail."
                ),
            })

    # Check 4: Record-triggered flows must have triggerType
    start = root.find("sf:start", _NS)
    if start is not None:
        has_object = start.find("sf:object", _NS) is not None
        has_record_trigger = start.find("sf:recordTriggerType", _NS) is not None
        if has_object and has_record_trigger and not _has_trigger_type(root):
            issues.append({
                "severity": "ERROR",
                "check": "record_trigger_type",
                "message": (
                    "Record-triggered flow has <object> and <recordTriggerType> "
                    "but missing <triggerType>. This causes InvalidDraft status."
                ),
            })

    errors = [i for i in issues if i["severity"] == "ERROR"]
    return {"ready": len(errors) == 0, "issues": issues}


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
