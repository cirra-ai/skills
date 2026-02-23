"""Tests for skills/cirra-ai-sf-data/scripts/mcp_validator.py"""

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-data/scripts/mcp_validator.py")
validate_data_params = mod.validate_data_params
MCPDataValidator = mod.MCPDataValidator


def _soql_input(**params_override):
    params = {"sObject": "Account", "orderBy": "", "groupBy": "", **params_override}
    return {"tool": "soql_query", "params": params}


def _dml_input(operation="insert", records=None, **params_override):
    params = {
        "sObject": "Account",
        "operation": operation,
        "records": records or [{"Name": "Acme"}],
        **params_override,
    }
    return {"tool": "sobject_dml", "params": params}


# ── soql_query ────────────────────────────────────────────────────────────────


def test_valid_soql_query_passes():
    result = validate_data_params(_soql_input())
    assert result["status"] == "pass"
    assert result["errors"] == []


def test_soql_missing_sobject_fails():
    result = validate_data_params({"tool": "soql_query", "params": {"orderBy": "", "groupBy": ""}})
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("sObject" in m for m in messages)


def test_soql_missing_order_by_fails():
    result = validate_data_params(_soql_input(orderBy=None))
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("orderBy" in m for m in messages)


def test_soql_missing_group_by_fails():
    result = validate_data_params(_soql_input(groupBy=None))
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("groupBy" in m for m in messages)


def test_soql_where_double_equals_warns():
    result = validate_data_params(_soql_input(whereClause="Name == 'Acme'"))
    assert result["status"] == "pass"  # warning, not error
    messages = [w["message"] for w in result["warnings"]]
    assert any("==" in m for m in messages)


def test_soql_where_double_quoted_string_warns():
    result = validate_data_params(_soql_input(whereClause='Name = "Acme"'))
    messages = [w["message"] for w in result["warnings"]]
    assert any("single quotes" in m.lower() for m in messages)


def test_soql_where_unbalanced_parens_warns():
    result = validate_data_params(_soql_input(whereClause="(Name = 'Acme'"))
    messages = [w["message"] for w in result["warnings"]]
    assert any("parentheses" in m.lower() for m in messages)


def test_no_sf_user_warns():
    result = validate_data_params(_soql_input())
    messages = [w["message"] for w in result["warnings"]]
    assert any("sf_user" in m for m in messages)


# ── sobject_dml ───────────────────────────────────────────────────────────────


def test_valid_insert_passes():
    result = validate_data_params(_dml_input("insert", [{"Name": "Acme"}]))
    assert result["status"] == "pass"


def test_valid_upsert_passes():
    result = validate_data_params(
        _dml_input("upsert", [{"ExternalId__c": "X1", "Name": "Acme"}], externalIdField="ExternalId__c")
    )
    assert result["status"] == "pass"


def test_invalid_operation_fails():
    result = validate_data_params(_dml_input("merge"))
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("Invalid operation" in m for m in messages)


def test_empty_records_fails():
    # Bypass helper — empty list is falsy and would be swapped for the default
    result = validate_data_params(
        {"tool": "sobject_dml", "params": {"sObject": "Account", "operation": "insert", "records": []}}
    )
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("records" in m.lower() for m in messages)


def test_update_missing_id_fails():
    result = validate_data_params(_dml_input("update", [{"Name": "Acme"}]))
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("Id" in m for m in messages)


def test_delete_missing_id_fails():
    result = validate_data_params(_dml_input("delete", [{"Name": "Acme"}]))
    assert result["status"] == "fail"


def test_upsert_missing_external_id_field_fails():
    result = validate_data_params(_dml_input("upsert", [{"ExternalId__c": "X1"}]))
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("externalIdField" in m for m in messages)


def test_upsert_record_missing_external_id_value_warns():
    result = validate_data_params(
        _dml_input("upsert", [{"Name": "Missing ext id"}], externalIdField="ExternalId__c")
    )
    messages = [w["message"] for w in result["warnings"]]
    assert any("ExternalId__c" in m for m in messages)


def test_inconsistent_insert_fields_warns():
    records = [{"Name": "A", "Phone": "123"}, {"Name": "B"}]
    result = validate_data_params(_dml_input("insert", records))
    messages = [w["message"] for w in result["warnings"]]
    assert any("Inconsistent" in m for m in messages)


# ── PII detection ─────────────────────────────────────────────────────────────


def test_ssn_in_records_warns():
    records = [{"SSN__c": "123-45-6789", "Name": "Test"}]
    result = validate_data_params(_dml_input("insert", records))
    messages = [w["message"] for w in result["warnings"]]
    assert any("SSN" in m for m in messages)


def test_credit_card_in_records_warns():
    records = [{"Card__c": "4111 1111 1111 1111", "Name": "Test"}]
    result = validate_data_params(_dml_input("insert", records))
    messages = [w["message"] for w in result["warnings"]]
    assert any("Credit card" in m for m in messages)


def test_personal_email_in_records_warns():
    records = [{"Email__c": "john@gmail.com", "Name": "Test"}]
    result = validate_data_params(_dml_input("insert", records))
    messages = [w["message"] for w in result["warnings"]]
    assert any("email" in m.lower() for m in messages)


def test_corporate_email_does_not_warn():
    records = [{"Email__c": "john@company.com", "Name": "Test"}]
    result = validate_data_params(_dml_input("insert", records))
    pii_warnings = [w for w in result["warnings"] if "email" in w["message"].lower()]
    assert pii_warnings == []


# ── Unknown tool ──────────────────────────────────────────────────────────────


def test_unknown_tool_fails():
    result = validate_data_params({"tool": "metadata_create", "params": {"sObject": "Account"}})
    assert result["status"] == "fail"
    messages = [e["message"] for e in result["errors"]]
    assert any("not a data operation" in m for m in messages)


# ── MCPDataValidator class ────────────────────────────────────────────────────


def test_class_interface_matches_function():
    validator = MCPDataValidator()
    func_result = validate_data_params(_soql_input())
    class_result = validator.validate(_soql_input())
    assert func_result == class_result
