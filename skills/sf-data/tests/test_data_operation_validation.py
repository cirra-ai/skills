"""Tests for DataOperationValidator — 130-point file-based scoring.

Covers:
  - SOQL file validation (query efficiency, documentation)
  - Apex factory file validation (bulk safety, cleanup, documentation)
  - CSV import file validation (data integrity, PII detection)
  - JSON tree file validation (structure, referenceIds)
  - Score arithmetic (category totals, no negatives, no overflows)

Uses existing asset files as test fixtures where possible.
"""

import os
import tempfile

from conftest import load_script

mod = load_script("skills/sf-data/scripts/validate_data_operation.py")
DataOperationValidator = mod.DataOperationValidator

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(SKILL_ROOT, "assets")


# ── helpers ──────────────────────────────────────────────────────────────────


def _validate_file(rel_path: str) -> dict:
    """Validate a file relative to the assets/ directory."""
    path = os.path.join(ASSETS_DIR, rel_path)
    return DataOperationValidator(path).validate()


def _validate_content(content: str, suffix: str) -> dict:
    """Write content to a temp file and validate."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp = f.name
    try:
        return DataOperationValidator(tmp).validate()
    finally:
        os.unlink(tmp)


def _issue_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", [])]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SOQL FILE VALIDATION — query efficiency and documentation
# ═══════════════════════════════════════════════════════════════════════════════


class TestSoqlFileValidation:
    def test_basic_queries_scored(self):
        """TC-SF1: Basic SOQL queries file is scored."""
        r = _validate_file("soql/basic-queries.soql")
        assert r is not None
        assert r["score"] > 0

    def test_optimization_patterns_scored(self):
        """TC-SF2: Optimization patterns file is scored."""
        r = _validate_file("soql/optimization-patterns.soql")
        assert r is not None
        assert r["score"] > 0

    def test_soql_without_where_deducted(self):
        """TC-SF3: SOQL without WHERE loses points."""
        r = _validate_content("-- comment\nSELECT Id FROM Account", ".soql")
        assert r is not None
        assert r["categories"]["Query Efficiency"]["score"] < r["categories"]["Query Efficiency"]["max"]

    def test_soql_without_limit_deducted(self):
        """TC-SF4: SOQL without LIMIT loses points."""
        r = _validate_content(
            "-- comment\nSELECT Id FROM Account WHERE Name = 'Test'",
            ".soql",
        )
        assert r is not None
        qe = r["categories"]["Query Efficiency"]
        assert qe["score"] < qe["max"]

    def test_soql_with_where_and_limit_full_score(self):
        """TC-SF5: SOQL with WHERE + LIMIT gets full query efficiency score."""
        r = _validate_content(
            "-- comment\nSELECT Id FROM Account WHERE Name = 'Test' LIMIT 1",
            ".soql",
        )
        assert r is not None
        qe = r["categories"]["Query Efficiency"]
        assert qe["score"] == qe["max"]

    def test_undocumented_soql_deducted(self):
        """TC-SF6: SOQL without documentation comment loses points."""
        r = _validate_content("SELECT Id FROM Account LIMIT 10", ".soql")
        assert r is not None
        doc = r["categories"]["Documentation"]
        assert doc["score"] < doc["max"]

    def test_documented_soql_full_doc_score(self):
        """TC-SF7: SOQL with leading comment gets documentation credit."""
        r = _validate_content(
            "-- Get active accounts\nSELECT Id FROM Account WHERE Name = 'Test' LIMIT 10",
            ".soql",
        )
        assert r is not None
        doc = r["categories"]["Documentation"]
        assert doc["score"] == doc["max"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. APEX FACTORY FILE VALIDATION — bulk safety, cleanup, docs
# ═══════════════════════════════════════════════════════════════════════════════


class TestApexFileValidation:
    def test_account_factory_scored(self):
        """TC-AF1: Account factory file is scored."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        assert r["score"] > 0

    def test_bulk_insert_scored(self):
        """TC-AF2: Bulk insert template is scored."""
        r = _validate_file("bulk/bulk-insert-200.apex")
        assert r is not None
        assert r["score"] > 0

    def test_cleanup_template_scored(self):
        """TC-AF3: Cleanup template is scored."""
        r = _validate_file("cleanup/delete-test-data.apex")
        assert r is not None
        assert r["score"] > 0

    def test_dml_in_loop_deducted(self):
        """TC-AF4: DML inside for loop loses bulk safety points."""
        apex = """/**
 * Bad pattern
 */
for (Account acc : accounts) {
    update acc;
}
"""
        r = _validate_content(apex, ".apex")
        assert r is not None
        bs = r["categories"]["Bulk Safety"]
        assert bs["score"] < bs["max"]

    def test_soql_in_loop_deducted(self):
        """TC-AF5: SOQL inside for loop loses query efficiency points."""
        apex = """/**
 * Bad pattern
 */
for (Contact c : contacts) {
    Account a = [SELECT Name FROM Account WHERE Id = :c.AccountId];
}
"""
        r = _validate_content(apex, ".apex")
        assert r is not None
        qe = r["categories"]["Query Efficiency"]
        assert qe["score"] < qe["max"]

    def test_pii_in_apex_deducted(self):
        """TC-AF6: PII pattern in Apex loses security points."""
        apex = """/**
 * Test data with PII
 */
String ssn = '123-45-6789';
"""
        r = _validate_content(apex, ".apex")
        assert r is not None
        sec = r["categories"]["Security & FLS"]
        assert sec["score"] < sec["max"]


# ═══════════════════════════════════════════════════════════════════════════════
# 3. CSV FILE VALIDATION — data integrity and PII
# ═══════════════════════════════════════════════════════════════════════════════


class TestCsvFileValidation:
    def test_account_import_scored(self):
        """TC-CV1: Account import CSV is scored."""
        r = _validate_file("csv/account-import.csv")
        assert r is not None
        assert r["score"] > 0

    def test_empty_csv_deducted(self):
        """TC-CV2: CSV with only header (no data rows) loses points."""
        r = _validate_content("Name,Industry,Type", ".csv")
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_inconsistent_columns_deducted(self):
        """TC-CV3: CSV with inconsistent column counts loses points."""
        csv = "Name,Industry,Type\nTest,Tech,Customer\nBad,NoType"
        r = _validate_content(csv, ".csv")
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_ssn_in_csv_deducted(self):
        """TC-CV4: SSN pattern in CSV loses security points."""
        csv = "Name,SSN\nJohn,123-45-6789"
        r = _validate_content(csv, ".csv")
        assert r is not None
        sec = r["categories"]["Security & FLS"]
        assert sec["score"] < sec["max"]

    def test_credit_card_in_csv_deducted(self):
        """TC-CV5: Credit card in CSV loses security points."""
        csv = "Name,Card\nJohn,4111 1111 1111 1111"
        r = _validate_content(csv, ".csv")
        assert r is not None
        sec = r["categories"]["Security & FLS"]
        assert sec["score"] < sec["max"]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. JSON TREE FILE VALIDATION — structure and referenceIds
# ═══════════════════════════════════════════════════════════════════════════════


class TestJsonFileValidation:
    def test_account_contact_tree_scored(self):
        """TC-JF1: Account-contact tree JSON is scored."""
        r = _validate_file("json/account-contact-tree.json")
        assert r is not None
        assert r["score"] > 0

    def test_invalid_json_deducted(self):
        """TC-JF2: Invalid JSON loses all data integrity points."""
        r = _validate_content("{bad json", ".json")
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] == 0

    def test_missing_records_array_deducted(self):
        """TC-JF3: JSON without 'records' array loses points."""
        r = _validate_content('{"data": []}', ".json")
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_missing_attributes_deducted(self):
        """TC-JF4: Records missing 'attributes' lose points."""
        r = _validate_content(
            '{"records": [{"Name": "Test"}]}',
            ".json",
        )
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_missing_type_deducted(self):
        """TC-JF5: Record attributes missing 'type' loses points."""
        r = _validate_content(
            '{"records": [{"attributes": {"referenceId": "Ref1"}, "Name": "Test"}]}',
            ".json",
        )
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_missing_reference_id_deducted(self):
        """TC-JF6: Record attributes missing 'referenceId' loses points."""
        r = _validate_content(
            '{"records": [{"attributes": {"type": "Account"}, "Name": "Test"}]}',
            ".json",
        )
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] < di["max"]

    def test_valid_tree_full_integrity(self):
        """TC-JF7: Valid tree structure gets full data integrity score."""
        tree = '''{
  "records": [{
    "attributes": {"type": "Account", "referenceId": "Ref1"},
    "Name": "Test"
  }]
}'''
        r = _validate_content(tree, ".json")
        assert r is not None
        di = r["categories"]["Data Integrity"]
        assert di["score"] == di["max"]


# ═══════════════════════════════════════════════════════════════════════════════
# 5. UNSUPPORTED FILE TYPES — gracefully skipped
# ═══════════════════════════════════════════════════════════════════════════════


class TestUnsupportedFileTypes:
    def test_txt_returns_none(self):
        """TC-UF1: .txt file returns None (unsupported)."""
        r = _validate_content("some text", ".txt")
        assert r is None

    def test_xml_returns_none(self):
        """TC-UF2: .xml file returns None (unsupported)."""
        r = _validate_content("<root/>", ".xml")
        assert r is None

    def test_nonexistent_file_returns_none(self):
        """TC-UF3: Non-existent file returns None."""
        r = DataOperationValidator("/nonexistent/file.apex").validate()
        assert r is None


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SCORE ARITHMETIC — category totals are correct
# ═══════════════════════════════════════════════════════════════════════════════


class TestScoreArithmetic:
    def test_total_max_is_130(self):
        """TC-SA1: All categories sum to 130 max."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        assert r["max_score"] == 130

    def test_seven_categories_present(self):
        """TC-SA2: Result contains exactly 7 scoring categories."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        expected = {
            "Query Efficiency",
            "Bulk Safety",
            "Data Integrity",
            "Security & FLS",
            "Test Patterns",
            "Cleanup & Isolation",
            "Documentation",
        }
        assert set(r["categories"].keys()) == expected

    def test_category_max_scores(self):
        """TC-SA3: Category max scores match the documented breakdown."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        expected_maxes = {
            "Query Efficiency": 25,
            "Bulk Safety": 25,
            "Data Integrity": 20,
            "Security & FLS": 20,
            "Test Patterns": 15,
            "Cleanup & Isolation": 15,
            "Documentation": 10,
        }
        for cat, expected_max in expected_maxes.items():
            assert r["categories"][cat]["max"] == expected_max, f"{cat} max mismatch"

    def test_no_category_exceeds_max(self):
        """TC-SA4: No category score exceeds its maximum."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        for cat, data in r["categories"].items():
            assert data["score"] <= data["max"], f"{cat} score {data['score']} > max {data['max']}"

    def test_no_category_below_zero(self):
        """TC-SA5: No category score goes below zero even with many issues."""
        # Apex with multiple PII patterns to push security score down
        apex = """/**
 * PII-heavy file
 */
String ssn1 = '111-22-3333';
String ssn2 = '444-55-6666';
String cc = '4111 1111 1111 1111';
String email = 'test@gmail.com';
"""
        r = _validate_content(apex, ".apex")
        assert r is not None
        for cat, data in r["categories"].items():
            assert data["score"] >= 0, f"{cat} went negative: {data['score']}"

    def test_score_equals_category_sum(self):
        """TC-SA6: Total score equals sum of all category scores."""
        r = _validate_file("factories/account-factory.apex")
        assert r is not None
        cat_sum = sum(data["score"] for data in r["categories"].values())
        assert r["score"] == cat_sum

    def test_clean_file_scores_higher_than_flawed(self):
        """TC-SA7: Clean file scores higher than file with issues."""
        clean = _validate_file("factories/account-factory.apex")
        flawed = _validate_content("SELECT * FROM Account", ".soql")
        assert clean is not None and flawed is not None
        assert clean["score"] > flawed["score"]
