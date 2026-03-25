"""Tests for Flow XML schema validation — syntactic validity.

Verifies that:
  - All test fixture flows are schema-valid (deployable XML)
  - All asset templates shipped with the skill are schema-valid
  - All subflow templates are schema-valid
  - Invalid XML is correctly rejected (bad processType, missing label, etc.)
  - Malformed XML is caught before schema validation

This is separate from the anti-pattern validator (validate_flow.py) which
checks best practices. Schema validation ensures the XML itself would be
accepted by Salesforce's Metadata API.
"""

import os
import tempfile

from conftest import load_script

mod = load_script("skills/sf-flow/scripts/validate_flow_schema.py")
FlowSchemaValidator = mod.FlowSchemaValidator

SKILL_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")
SUBFLOWS_DIR = os.path.join(ASSETS_DIR, "subflows")


# ── helpers ──────────────────────────────────────────────────────────────────


def _validate_file(path: str) -> dict:
    return FlowSchemaValidator(path).validate()


def _validate_xml(xml: str) -> dict:
    """Write XML to a temp file and validate."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".flow-meta.xml", delete=False
    ) as f:
        f.write(xml)
        tmp = f.name
    try:
        return FlowSchemaValidator(tmp).validate()
    finally:
        os.unlink(tmp)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TEST FIXTURES — all flows used in tests must be schema-valid
# ═══════════════════════════════════════════════════════════════════════════════


class TestFixtureSchemaValidity:
    """Every test fixture must be syntactically valid Flow XML.

    These are the flows the skill's validator is scored against. If a fixture
    is schema-invalid, the tests are testing against unrealistic input.
    """

    def test_perfect_before_save_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "perfect_before_save.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_perfect_after_save_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "perfect_after_save.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_screen_flow_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "screen_flow_simple.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_scheduled_flow_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "scheduled_flow.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_complex_multi_object_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "complex_multi_object.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_dml_in_loop_valid(self):
        """Even anti-pattern fixtures must be valid XML (bad practice != invalid XML)."""
        r = _validate_file(os.path.join(FIXTURES_DIR, "dml_in_loop.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_hardcoded_ids_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "hardcoded_ids.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_max_complexity_valid(self):
        r = _validate_file(
            os.path.join(FIXTURES_DIR, "max_complexity_anti_patterns.flow-meta.xml")
        )
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_missing_fault_paths_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "missing_fault_paths.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_old_api_version_valid(self):
        r = _validate_file(os.path.join(FIXTURES_DIR, "old_api_version.flow-meta.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_all_fixtures_valid(self):
        """Catch-all: every .xml in fixtures/ must be schema-valid."""
        for name in sorted(os.listdir(FIXTURES_DIR)):
            if not name.endswith(".xml"):
                continue
            path = os.path.join(FIXTURES_DIR, name)
            r = _validate_file(path)
            assert r["valid"], f"{name}: {r['errors']}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ASSET TEMPLATES — shipped templates must be deployable
# ═══════════════════════════════════════════════════════════════════════════════


class TestAssetTemplateValidity:
    """Templates in assets/ are what the skill uses to generate flows.

    If a template is schema-invalid, every flow generated from it will be
    invalid too — this is the "one-shot" requirement.
    """

    def test_record_triggered_after_save(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "record-triggered-after-save.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_record_triggered_before_save(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "record-triggered-before-save.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_record_triggered_before_delete(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "record-triggered-before-delete.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_screen_flow_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "screen-flow-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_screen_flow_with_lwc(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "screen-flow-with-lwc.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_autolaunched_flow_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "autolaunched-flow-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_scheduled_flow_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "scheduled-flow-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_platform_event_flow_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "platform-event-flow-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_apex_action_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "apex-action-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"

    def test_wait_template(self):
        r = _validate_file(os.path.join(ASSETS_DIR, "wait-template.xml"))
        assert r["valid"], f"Schema errors: {r['errors']}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SUBFLOW TEMPLATES — reusable building blocks
# ═══════════════════════════════════════════════════════════════════════════════


class TestSubflowTemplateValidity:
    """Subflow templates are referenced by generated flows.

    If a subflow template is invalid, any flow that includes it will fail
    deployment.
    """

    def test_all_subflows_valid(self):
        """Every .xml in assets/subflows/ must be schema-valid."""
        if not os.path.isdir(SUBFLOWS_DIR):
            return
        for name in sorted(os.listdir(SUBFLOWS_DIR)):
            if not name.endswith(".xml"):
                continue
            path = os.path.join(SUBFLOWS_DIR, name)
            r = _validate_file(path)
            assert r["valid"], f"Subflow {name}: {r['errors']}"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. INVALID XML REJECTION — schema validator catches real errors
# ═══════════════════════════════════════════════════════════════════════════════


class TestInvalidXmlRejection:
    def test_invalid_process_type_rejected(self):
        """Invalid processType enum value is rejected."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <label>Bad Flow</label>
    <processType>NotARealType</processType>
    <status>Draft</status>
    <start><locationX>0</locationX><locationY>0</locationY></start>
</Flow>"""
        r = _validate_xml(xml)
        assert not r["valid"]
        assert any("processType" in e["path"] or "NotARealType" in e["message"] for e in r["errors"])

    def test_missing_label_rejected(self):
        """Missing required 'label' field is rejected."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <processType>AutoLaunchedFlow</processType>
    <status>Draft</status>
</Flow>"""
        r = _validate_xml(xml)
        assert not r["valid"]
        assert any("label" in e["message"] for e in r["errors"])

    def test_malformed_xml_rejected(self):
        """Malformed XML (unclosed tags) is rejected."""
        xml = "<Flow><unclosed>"
        r = _validate_xml(xml)
        assert not r["valid"]
        assert any("parse error" in e["message"].lower() or "XML" in e["message"] for e in r["errors"])

    def test_wrong_root_element_rejected(self):
        """Non-Flow root element is rejected."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Not a flow</label>
</CustomObject>"""
        r = _validate_xml(xml)
        assert not r["valid"]
        assert any("root" in e["message"].lower() or "Flow" in e["message"] for e in r["errors"])

    def test_invalid_status_rejected(self):
        """Invalid status enum value is rejected."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <label>Bad Status</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Published</status>
</Flow>"""
        r = _validate_xml(xml)
        assert not r["valid"]
        assert any("status" in e["path"] or "Published" in e["message"] for e in r["errors"])

    def test_valid_minimal_flow_accepted(self):
        """Minimal valid flow passes schema validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>65.0</apiVersion>
    <label>Minimal Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Draft</status>
</Flow>"""
        r = _validate_xml(xml)
        assert r["valid"], f"Schema errors: {r['errors']}"
