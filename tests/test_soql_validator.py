"""Tests for cirra-ai-sf-data/hooks/scripts/soql_validator.py"""

import pytest
from conftest import load_script

mod = load_script("cirra-ai-sf-data/hooks/scripts/soql_validator.py")
SOQLValidator = mod.SOQLValidator


# ── Validity ──────────────────────────────────────────────────────────────────


def test_valid_simple_query():
    result = SOQLValidator("SELECT Id, Name FROM Account WHERE Id = :recordId LIMIT 10").validate()
    assert result["is_valid"] is True
    assert result["has_where_clause"] is True
    assert result["has_limit"] is True
    errors = [i for i in result["issues"] if i["severity"] == "error"]
    assert errors == []


def test_select_star_is_error():
    result = SOQLValidator("SELECT * FROM Account").validate()
    assert result["is_valid"] is False
    messages = [i["message"] for i in result["issues"]]
    assert any("SELECT *" in m for m in messages)


def test_missing_from_clause_is_error():
    result = SOQLValidator("SELECT Id, Name").validate()
    assert result["is_valid"] is False
    messages = [i["message"] for i in result["issues"]]
    assert any("FROM" in m for m in messages)


def test_double_equals_operator_is_error():
    result = SOQLValidator("SELECT Id FROM Account WHERE Name == 'Acme'").validate()
    assert result["is_valid"] is False
    messages = [i["message"] for i in result["issues"]]
    assert any('==' in m for m in messages)


def test_unbalanced_parens_is_error():
    result = SOQLValidator("SELECT Id FROM Account WHERE (Name = 'Acme'").validate()
    assert result["is_valid"] is False
    messages = [i["message"] for i in result["issues"]]
    assert any("parentheses" in m.lower() for m in messages)


def test_double_quoted_string_is_warning():
    result = SOQLValidator('SELECT Id FROM Account WHERE Name = "Acme"').validate()
    severities = {i["severity"] for i in result["issues"]}
    # Should warn, not hard-error
    assert "warning" in severities
    assert "error" not in severities


# ── Hardcoded IDs ─────────────────────────────────────────────────────────────


def test_hardcoded_15_char_id():
    query = "SELECT Id FROM Account WHERE Id = '001000000000001'"
    result = SOQLValidator(query).validate()
    assert result["has_hardcoded_ids"] is True
    assert any("hardcoded" in r.lower() for r in result["recommendations"])


def test_hardcoded_18_char_id():
    query = "SELECT Id FROM Account WHERE Id = '001000000000001AAA'"
    result = SOQLValidator(query).validate()
    assert result["has_hardcoded_ids"] is True


def test_no_hardcoded_ids():
    result = SOQLValidator("SELECT Id FROM Account WHERE Id = :recordId").validate()
    assert result["has_hardcoded_ids"] is False


# ── WHERE / LIMIT recommendations ─────────────────────────────────────────────


def test_no_where_clause_triggers_recommendation():
    result = SOQLValidator("SELECT Id FROM Account").validate()
    assert result["has_where_clause"] is False
    assert any("WHERE" in r for r in result["recommendations"])


def test_no_limit_triggers_recommendation():
    result = SOQLValidator("SELECT Id FROM Account").validate()
    assert result["has_limit"] is False
    assert any("LIMIT" in r for r in result["recommendations"])


def test_has_where_and_limit_no_basic_recommendations():
    result = SOQLValidator("SELECT Id FROM Account WHERE Name = 'Acme' LIMIT 200").validate()
    assert result["has_where_clause"] is True
    assert result["has_limit"] is True
    # No WHERE/LIMIT recommendations
    assert not any("WHERE" in r for r in result["recommendations"])
    assert not any("LIMIT" in r for r in result["recommendations"])


# ── Indexed fields ────────────────────────────────────────────────────────────


def test_indexed_field_in_where():
    result = SOQLValidator("SELECT Id FROM Account WHERE OwnerId = :userId").validate()
    assert result["uses_indexed_fields"] is True


def test_non_indexed_field_in_where():
    result = SOQLValidator("SELECT Id FROM Account WHERE Phone = '555-1234'").validate()
    assert result["uses_indexed_fields"] is False


# ── Structural detection ──────────────────────────────────────────────────────


def test_subquery_detected():
    result = SOQLValidator("SELECT Id, (SELECT Id FROM Contacts) FROM Account").validate()
    assert result["has_subquery"] is True


def test_no_subquery():
    result = SOQLValidator("SELECT Id FROM Account").validate()
    assert result["has_subquery"] is False


def test_relationship_query_detected():
    result = SOQLValidator("SELECT Id, Account.Name FROM Contact").validate()
    assert result["has_relationship"] is True


def test_order_by_detected():
    result = SOQLValidator("SELECT Id FROM Account ORDER BY CreatedDate DESC").validate()
    assert result["has_order_by"] is True


# ── Comment stripping ─────────────────────────────────────────────────────────


def test_single_line_comment_ignored():
    # The == in the comment should not trigger the error
    query = "SELECT Id FROM Account -- WHERE Name == 'bad'"
    result = SOQLValidator(query).validate()
    assert result["is_valid"] is True


def test_block_comment_ignored():
    query = "SELECT Id FROM Account /* WHERE Name == 'bad' */"
    result = SOQLValidator(query).validate()
    assert result["is_valid"] is True


# ── TYPEOF ────────────────────────────────────────────────────────────────────


def test_typeof_without_end_is_error():
    query = "SELECT TYPEOF What WHEN Account THEN Name ELSE Subject FROM Event"
    result = SOQLValidator(query).validate()
    assert result["is_valid"] is False
    messages = [i["message"] for i in result["issues"]]
    assert any("TYPEOF" in m and "END" in m for m in messages)
