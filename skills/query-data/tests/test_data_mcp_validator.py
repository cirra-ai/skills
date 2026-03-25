"""Tests for MCPDataValidator — MCP data operation parameter validation.

Covers:
  - soql_query parameter validation (required fields, syntax warnings)
  - sobject_dml parameter validation (operation types, record structure)
  - PII detection in DML records
  - Unsupported tool rejection
  - Result structure verification
"""

from conftest import load_script

mod = load_script("skills/query-data/scripts/mcp_validator.py")
MCPDataValidator = mod.MCPDataValidator


# ── helpers ──────────────────────────────────────────────────────────────────


def _validate(input_data: dict) -> dict:
    return MCPDataValidator().validate(input_data)


def _error_messages(result: dict) -> list[str]:
    return [e["message"] for e in result.get("errors", [])]


def _warning_messages(result: dict) -> list[str]:
    return [w["message"] for w in result.get("warnings", [])]


def _soql_query(sobject: str, **extra) -> dict:
    """Build a soql_query input with defaults."""
    params = {
        "sObject": sobject,
        "orderBy": "",
        "groupBy": "",
        "sf_user": "test@example.com",
    }
    params.update(extra)
    return {"tool": "soql_query", "params": params}


def _sobject_dml(sobject: str, operation: str, records: list, **extra) -> dict:
    """Build a sobject_dml input with defaults."""
    params = {
        "sObject": sobject,
        "operation": operation,
        "records": records,
        "sf_user": "test@example.com",
    }
    params.update(extra)
    return {"tool": "sobject_dml", "params": params}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. soql_query — VALID QUERIES PASS
# ═══════════════════════════════════════════════════════════════════════════════


class TestSoqlQueryValid:
    def test_minimal_valid_query_passes(self):
        """TC-MQ1: Minimal valid soql_query passes."""
        r = _validate(_soql_query("Account"))
        assert r["status"] == "pass"

    def test_query_with_where_passes(self):
        """TC-MQ2: Query with whereClause passes."""
        r = _validate(_soql_query("Account", whereClause="Name = 'Test'"))
        assert r["status"] == "pass"

    def test_query_with_all_params_passes(self):
        """TC-MQ3: Query with all parameters passes."""
        r = _validate(_soql_query(
            "Opportunity",
            whereClause="StageName = 'Prospecting'",
            orderBy="Amount DESC",
            groupBy="",
        ))
        assert r["status"] == "pass"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. soql_query — MISSING REQUIRED PARAMS FAIL, OPTIONAL PARAMS PASS
# ═══════════════════════════════════════════════════════════════════════════════


class TestSoqlQueryInvalid:
    def test_missing_sobject_fails(self):
        """TC-MQ4: Missing sObject fails."""
        r = _validate({"tool": "soql_query", "params": {"orderBy": "", "groupBy": ""}})
        assert r["status"] == "fail"
        assert any("sObject" in m for m in _error_messages(r))

    def test_missing_order_by_passes(self):
        """TC-MQ5: Missing orderBy is fine (optional param)."""
        r = _validate({"tool": "soql_query", "params": {"sObject": "Account", "groupBy": "", "sf_user": "t"}})
        assert r["status"] == "pass"

    def test_missing_group_by_passes(self):
        """TC-MQ6: Missing groupBy is fine (optional param)."""
        r = _validate({"tool": "soql_query", "params": {"sObject": "Account", "orderBy": "", "sf_user": "t"}})
        assert r["status"] == "pass"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. soql_query — WHERE CLAUSE SYNTAX WARNINGS
# ═══════════════════════════════════════════════════════════════════════════════


class TestSoqlQueryWhereWarnings:
    def test_double_equals_warned(self):
        """TC-MW1: == in whereClause triggers warning."""
        r = _validate(_soql_query("Account", whereClause="Name == 'Test'"))
        assert any("==" in m for m in _warning_messages(r))

    def test_double_quotes_warned(self):
        """TC-MW2: Double-quoted string in whereClause triggers warning."""
        r = _validate(_soql_query("Account", whereClause='Name = "Test"'))
        assert any("Double-quoted" in m or "single quotes" in m.lower() for m in _warning_messages(r))

    def test_unbalanced_parens_warned(self):
        """TC-MW3: Unbalanced parentheses in whereClause trigger warning."""
        r = _validate(_soql_query("Account", whereClause="(Name = 'Test'"))
        assert any("parenthes" in m.lower() for m in _warning_messages(r))

    def test_valid_where_no_syntax_warnings(self):
        """TC-MW4: Valid whereClause produces no syntax warnings."""
        r = _validate(_soql_query("Account", whereClause="Name = 'Test' AND Industry = 'Tech'"))
        syntax_warns = [m for m in _warning_messages(r) if "==" in m or "parenthes" in m.lower()]
        assert len(syntax_warns) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 4. sobject_dml — VALID OPERATIONS PASS
# ═══════════════════════════════════════════════════════════════════════════════


class TestDmlValid:
    def test_insert_passes(self):
        """TC-MD1: Valid insert passes."""
        r = _validate(_sobject_dml("Account", "insert", [{"Name": "Test"}]))
        assert r["status"] == "pass"

    def test_update_with_id_passes(self):
        """TC-MD2: Update with Id passes."""
        r = _validate(_sobject_dml("Account", "update", [{"Id": "001xx", "Name": "Updated"}]))
        assert r["status"] == "pass"

    def test_delete_with_record_ids_passes(self):
        """TC-MD3: Delete with recordIds passes."""
        r = _validate({
            "tool": "sobject_dml",
            "params": {
                "sObject": "Account",
                "operation": "delete",
                "recordIds": ["001xx", "001yy"],
                "sf_user": "test@example.com",
            },
        })
        assert r["status"] == "pass"

    def test_delete_with_records_passes_with_warning(self):
        """TC-MD3b: Delete with records (legacy) passes but warns."""
        r = _validate(_sobject_dml("Account", "delete", [{"Id": "001xx"}]))
        assert r["status"] == "pass"
        assert any("recordIds" in m for m in _warning_messages(r))

    def test_upsert_with_ext_id_passes(self):
        """TC-MD4: Upsert with externalIdField passes."""
        r = _validate(_sobject_dml(
            "Account", "upsert",
            [{"External_Id__c": "EXT-1", "Name": "Test"}],
            externalIdField="External_Id__c",
        ))
        assert r["status"] == "pass"

    def test_bulk_insert_passes(self):
        """TC-MD5: Bulk insert with consistent fields passes."""
        records = [{"Name": f"Acc {i}", "Industry": "Tech"} for i in range(10)]
        r = _validate(_sobject_dml("Account", "insert", records))
        assert r["status"] == "pass"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. sobject_dml — INVALID OPERATIONS FAIL
# ═══════════════════════════════════════════════════════════════════════════════


class TestDmlInvalid:
    def test_invalid_operation_fails(self):
        """TC-MD6: Invalid operation type fails."""
        r = _validate(_sobject_dml("Account", "merge", [{"Name": "Test"}]))
        assert r["status"] == "fail"
        assert any("operation" in m.lower() for m in _error_messages(r))

    def test_empty_records_fails(self):
        """TC-MD7: Empty records array fails."""
        r = _validate(_sobject_dml("Account", "insert", []))
        assert r["status"] == "fail"
        assert any("records" in m.lower() for m in _error_messages(r))

    def test_update_missing_id_fails(self):
        """TC-MD8: Update without Id fails."""
        r = _validate(_sobject_dml("Account", "update", [{"Name": "No Id"}]))
        assert r["status"] == "fail"
        assert any("Id" in m for m in _error_messages(r))

    def test_delete_missing_id_fails(self):
        """TC-MD9: Delete without recordIds or records with Id fails."""
        r = _validate({
            "tool": "sobject_dml",
            "params": {
                "sObject": "Account",
                "operation": "delete",
                "sf_user": "test@example.com",
            },
        })
        assert r["status"] == "fail"
        assert any("recordIds" in m.lower() or "Id" in m for m in _error_messages(r))

    def test_upsert_missing_ext_id_field_fails(self):
        """TC-MD10: Upsert without externalIdField fails."""
        r = _validate(_sobject_dml("Account", "upsert", [{"Name": "Test"}]))
        assert r["status"] == "fail"
        assert any("externalIdField" in m for m in _error_messages(r))

    def test_missing_sobject_fails(self):
        """TC-MD11: Missing sObject fails."""
        r = _validate({"tool": "sobject_dml", "params": {
            "operation": "insert", "records": [{"Name": "Test"}],
        }})
        assert r["status"] == "fail"
        assert any("sObject" in m for m in _error_messages(r))

    def test_insert_over_200_records_fails(self):
        """TC-MD12: Insert with > 200 records fails."""
        records = [{"Name": f"Acc {i}"} for i in range(201)]
        r = _validate(_sobject_dml("Account", "insert", records))
        assert r["status"] == "fail"
        assert any("200" in m for m in _error_messages(r))

    def test_insert_exactly_200_passes(self):
        """TC-MD13: Insert with exactly 200 records passes."""
        records = [{"Name": f"Acc {i}"} for i in range(200)]
        r = _validate(_sobject_dml("Account", "insert", records))
        assert r["status"] == "pass"

    def test_delete_over_200_record_ids_fails(self):
        """TC-MD14: Delete with > 200 recordIds fails."""
        r = _validate({
            "tool": "sobject_dml",
            "params": {
                "sObject": "Account",
                "operation": "delete",
                "recordIds": [f"001xx{i:04d}" for i in range(201)],
                "sf_user": "test@example.com",
            },
        })
        assert r["status"] == "fail"
        assert any("200" in m for m in _error_messages(r))

    def test_delete_legacy_records_over_200_fails(self):
        """TC-MD15: Delete with > 200 legacy records also fails."""
        records = [{"Id": f"001xx{i:04d}"} for i in range(201)]
        r = _validate(_sobject_dml("Account", "delete", records))
        assert r["status"] == "fail"
        assert any("200" in m for m in _error_messages(r))


# ═══════════════════════════════════════════════════════════════════════════════
# 6. sobject_dml — WARNINGS (non-blocking)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDmlWarnings:
    def test_inconsistent_fields_warned(self):
        """TC-DW1: Inconsistent fields across insert records triggers warning."""
        r = _validate(_sobject_dml("Account", "insert", [
            {"Name": "A", "Industry": "Tech"},
            {"Name": "B"},
        ]))
        assert r["status"] == "pass"
        assert any("inconsistent" in m.lower() for m in _warning_messages(r))

    def test_upsert_missing_ext_id_value_warned(self):
        """TC-DW2: Upsert records missing external ID value triggers warning."""
        r = _validate(_sobject_dml(
            "Account", "upsert",
            [{"Name": "Test"}],
            externalIdField="External_Id__c",
        ))
        assert any("External_Id__c" in m for m in _warning_messages(r))

    def test_no_sf_user_warned(self):
        """TC-DW3: Missing sf_user triggers warning."""
        r = _validate({"tool": "sobject_dml", "params": {
            "sObject": "Account", "operation": "insert",
            "records": [{"Name": "Test"}],
        }})
        assert any("sf_user" in m for m in _warning_messages(r))

    def test_invalid_sobject_name_warned(self):
        """TC-DW4: Invalid sObject name pattern triggers warning."""
        r = _validate(_sobject_dml("123Bad-Name!", "insert", [{"Name": "Test"}]))
        assert any("pattern" in m.lower() or "sObject" in m for m in _warning_messages(r))


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PII DETECTION — sensitive data caught before reaching org
# ═══════════════════════════════════════════════════════════════════════════════


class TestPiiDetection:
    def test_ssn_detected(self):
        """TC-PII1: SSN pattern in records triggers warning."""
        r = _validate(_sobject_dml("Contact", "insert", [
            {"LastName": "Test", "SSN__c": "123-45-6789"},
        ]))
        assert any("SSN" in m for m in _warning_messages(r))

    def test_credit_card_detected(self):
        """TC-PII2: Credit card pattern in records triggers warning."""
        r = _validate(_sobject_dml("Contact", "insert", [
            {"LastName": "Test", "Payment__c": "4111-1111-1111-1111"},
        ]))
        assert any("Credit card" in m for m in _warning_messages(r))

    def test_personal_email_detected(self):
        """TC-PII3: Personal email domain triggers warning."""
        r = _validate(_sobject_dml("Contact", "insert", [
            {"LastName": "Test", "Email": "john@gmail.com"},
        ]))
        assert any("email" in m.lower() for m in _warning_messages(r))

    def test_corporate_email_clean(self):
        """TC-PII4: Corporate email does not trigger PII warning."""
        r = _validate(_sobject_dml("Contact", "insert", [
            {"LastName": "Test", "Email": "john@acme.com"},
        ]))
        pii_warns = [m for m in _warning_messages(r)
                     if "email" in m.lower() and "pattern" in m.lower()]
        assert len(pii_warns) == 0

    def test_pii_in_multiple_records(self):
        """TC-PII5: PII across multiple records shows count."""
        r = _validate(_sobject_dml("Contact", "insert", [
            {"LastName": "A", "SSN__c": "111-22-3333"},
            {"LastName": "B", "SSN__c": "444-55-6666"},
        ]))
        ssn_warns = [m for m in _warning_messages(r) if "SSN" in m]
        assert len(ssn_warns) == 1  # consolidated into one warning
        assert "more" in ssn_warns[0]  # mentions additional occurrences


# ═══════════════════════════════════════════════════════════════════════════════
# 8. UNSUPPORTED TOOL REJECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnsupportedToolRejection:
    def test_metadata_create_rejected(self):
        """TC-UT1: metadata_create is not a data operation."""
        r = _validate({"tool": "metadata_create", "params": {"sObject": "Account"}})
        assert r["status"] == "fail"
        assert any("not a data operation" in m for m in _error_messages(r))

    def test_tooling_api_rejected(self):
        """TC-UT2: tooling_api_dml is not a data operation."""
        r = _validate({"tool": "tooling_api_dml", "params": {"sObject": "Account"}})
        assert r["status"] == "fail"

    def test_empty_tool_rejected(self):
        """TC-UT3: Empty tool name is rejected."""
        r = _validate({"tool": "", "params": {"sObject": "Account"}})
        assert r["status"] == "fail"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. RESULT STRUCTURE — validator returns usable metadata
# ═══════════════════════════════════════════════════════════════════════════════


class TestResultStructure:
    def test_result_has_required_keys(self):
        """TC-RS1: Result contains all required keys."""
        r = _validate(_soql_query("Account"))
        assert "tier" in r
        assert "tool" in r
        assert "status" in r
        assert "errors" in r
        assert "warnings" in r

    def test_tier_is_data_params(self):
        """TC-RS2: Tier is always 'data_params'."""
        r = _validate(_soql_query("Account"))
        assert r["tier"] == "data_params"

    def test_tool_name_preserved(self):
        """TC-RS3: Tool name is preserved in result."""
        r = _validate(_soql_query("Account"))
        assert r["tool"] == "soql_query"

    def test_dml_tool_name_preserved(self):
        """TC-RS4: DML tool name is preserved."""
        r = _validate(_sobject_dml("Account", "insert", [{"Name": "Test"}]))
        assert r["tool"] == "sobject_dml"

    def test_pass_status_no_errors(self):
        """TC-RS5: Pass status means zero errors."""
        r = _validate(_soql_query("Account"))
        assert r["status"] == "pass"
        assert len(r["errors"]) == 0

    def test_fail_status_has_errors(self):
        """TC-RS6: Fail status means at least one error."""
        r = _validate({"tool": "soql_query", "params": {}})
        assert r["status"] == "fail"
        assert len(r["errors"]) > 0
