"""Tests for SOQLValidator — SOQL syntax and pattern validation.

Covers:
  - Valid query detection (WHERE, LIMIT, ORDER BY, subqueries, relationships)
  - Syntax error detection (SELECT *, ==, unbalanced parens, missing FROM)
  - Hardcoded ID detection
  - Indexed field usage detection
  - Query complexity analysis
  - Optimization suggestions
"""

from conftest import load_script

mod = load_script("skills/sf-data/scripts/soql_validator.py")
SOQLValidator = mod.SOQLValidator


# ── helpers ──────────────────────────────────────────────────────────────────


def _validate(soql: str) -> dict:
    return SOQLValidator(soql).validate()


def _error_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", []) if i.get("severity") == "error"]


def _warning_messages(result: dict) -> list[str]:
    return [i["message"] for i in result.get("issues", []) if i.get("severity") == "warning"]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. VALID QUERY DETECTION — structural features correctly identified
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidQueryDetection:
    def test_simple_query_is_valid(self):
        """TC-Q1: Simple SELECT ... FROM query is valid."""
        r = _validate("SELECT Id, Name FROM Account")
        assert r["is_valid"]

    def test_where_clause_detected(self):
        """TC-Q2: WHERE clause is detected."""
        r = _validate("SELECT Id FROM Account WHERE Name = 'Test'")
        assert r["has_where_clause"]

    def test_no_where_clause_detected(self):
        """TC-Q3: Missing WHERE clause is detected."""
        r = _validate("SELECT Id FROM Account")
        assert not r["has_where_clause"]

    def test_limit_detected(self):
        """TC-Q4: LIMIT clause is detected."""
        r = _validate("SELECT Id FROM Account LIMIT 100")
        assert r["has_limit"]

    def test_no_limit_detected(self):
        """TC-Q5: Missing LIMIT clause is detected."""
        r = _validate("SELECT Id FROM Account")
        assert not r["has_limit"]

    def test_order_by_detected(self):
        """TC-Q6: ORDER BY clause is detected."""
        r = _validate("SELECT Id FROM Account ORDER BY Name ASC")
        assert r["has_order_by"]

    def test_subquery_detected(self):
        """TC-Q7: Subquery is detected."""
        r = _validate("SELECT Id, (SELECT Id FROM Contacts) FROM Account")
        assert r["has_subquery"]

    def test_no_subquery_detected(self):
        """TC-Q8: No subquery in simple query."""
        r = _validate("SELECT Id FROM Account")
        assert not r["has_subquery"]

    def test_relationship_detected(self):
        """TC-Q9: Relationship query (dot notation) is detected."""
        r = _validate("SELECT Id, Account.Name FROM Contact")
        assert r["has_relationship"]

    def test_custom_relationship_detected(self):
        """TC-Q10: Custom relationship (__r) is detected."""
        r = _validate("SELECT Id, Custom__r.Name FROM MyObject__c")
        assert r["has_relationship"]

    def test_indexed_field_in_where(self):
        """TC-Q11: Indexed field in WHERE is detected."""
        r = _validate("SELECT Id FROM Account WHERE CreatedDate = TODAY")
        assert r["uses_indexed_fields"]

    def test_non_indexed_field_in_where(self):
        """TC-Q12: Non-indexed field in WHERE is detected."""
        r = _validate("SELECT Id FROM Account WHERE Industry = 'Tech'")
        assert not r["uses_indexed_fields"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SYNTAX ERROR DETECTION — invalid SOQL is flagged
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyntaxErrorDetection:
    def test_select_star_flagged(self):
        """TC-S1: SELECT * is flagged as error."""
        r = _validate("SELECT * FROM Account")
        assert not r["is_valid"]
        assert any("SELECT *" in m for m in _error_messages(r))

    def test_double_equals_flagged(self):
        """TC-S2: == operator is flagged as error."""
        r = _validate("SELECT Id FROM Account WHERE Name == 'Test'")
        assert not r["is_valid"]
        assert any("==" in m for m in _error_messages(r))

    def test_missing_from_flagged(self):
        """TC-S3: SELECT without FROM is flagged as error."""
        r = _validate("SELECT Id, Name")
        assert not r["is_valid"]
        assert any("FROM" in m for m in _error_messages(r))

    def test_unbalanced_parens_flagged(self):
        """TC-S4: Unbalanced parentheses are flagged."""
        r = _validate("SELECT Id FROM Account WHERE (Name = 'Test'")
        assert not r["is_valid"]
        assert any("parenthes" in m.lower() for m in _error_messages(r))

    def test_typeof_without_end_flagged(self):
        """TC-S5: TYPEOF without END is flagged."""
        r = _validate("SELECT TYPEOF What WHEN Account THEN Name FROM Task")
        assert not r["is_valid"]
        assert any("TYPEOF" in m or "END" in m for m in _error_messages(r))

    def test_double_quotes_warned(self):
        """TC-S6: Double-quoted strings produce a warning."""
        r = _validate('SELECT Id FROM Account WHERE Name = "Test"')
        assert any("single quotes" in m.lower() for m in _warning_messages(r))

    def test_diamond_operator_warned(self):
        """TC-S7: <> operator produces a warning."""
        r = _validate("SELECT Id FROM Account WHERE Name <> 'Test'")
        assert any("!=" in m or "<>" in m for m in _warning_messages(r))

    def test_valid_not_equals_null_no_warning(self):
        """TC-S8: != null is valid and does not produce a <> warning."""
        r = _validate("SELECT Id FROM Contact WHERE Email != null")
        assert r["is_valid"]
        diamond_warns = [m for m in _warning_messages(r) if "<>" in m]
        assert len(diamond_warns) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. HARDCODED ID DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestHardcodedIdDetection:
    def test_15_char_id_detected(self):
        """TC-H1: 15-character Salesforce ID is detected."""
        r = _validate("SELECT Id FROM Account WHERE Id = '001000000000001'")
        assert r["has_hardcoded_ids"]

    def test_18_char_id_detected(self):
        """TC-H2: 18-character Salesforce ID is detected."""
        r = _validate("SELECT Id FROM Account WHERE Id = '001000000000001AAA'")
        assert r["has_hardcoded_ids"]

    def test_no_hardcoded_id_clean(self):
        """TC-H3: Query without hardcoded IDs is clean."""
        r = _validate("SELECT Id FROM Account WHERE Name = 'Acme'")
        assert not r["has_hardcoded_ids"]

    def test_hardcoded_id_recommendation(self):
        """TC-H4: Hardcoded ID triggers recommendation."""
        r = _validate("SELECT Id FROM Account WHERE OwnerId = '005000000000001'")
        assert any("hardcoded" in rec.lower() for rec in r["recommendations"])


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RECOMMENDATIONS — best practice guidance
# ═══════════════════════════════════════════════════════════════════════════════


class TestRecommendations:
    def test_missing_where_recommendation(self):
        """TC-R1: Missing WHERE triggers recommendation."""
        r = _validate("SELECT Id FROM Account")
        assert any("WHERE" in rec for rec in r["recommendations"])

    def test_missing_limit_recommendation(self):
        """TC-R2: Missing LIMIT triggers recommendation."""
        r = _validate("SELECT Id FROM Account")
        assert any("LIMIT" in rec for rec in r["recommendations"])

    def test_complete_query_no_warnings(self):
        """TC-R3: Complete query with WHERE + LIMIT has fewer recommendations."""
        r = _validate("SELECT Id FROM Account WHERE Name = 'Test' LIMIT 10")
        where_recs = [rec for rec in r["recommendations"] if "WHERE" in rec]
        limit_recs = [rec for rec in r["recommendations"] if "LIMIT" in rec]
        assert len(where_recs) == 0
        assert len(limit_recs) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. COMMENT HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


class TestCommentHandling:
    def test_single_line_comments_stripped(self):
        """TC-C1: Single-line comments are removed before validation."""
        soql = "-- this is a comment\nSELECT Id FROM Account"
        r = _validate(soql)
        assert r["is_valid"]

    def test_multi_line_comments_stripped(self):
        """TC-C2: Multi-line comments are removed before validation."""
        soql = "/* block comment */\nSELECT Id FROM Account"
        r = _validate(soql)
        assert r["is_valid"]

    def test_inline_comment_stripped(self):
        """TC-C3: Inline comments after query are stripped."""
        soql = "SELECT Id FROM Account -- get accounts"
        r = _validate(soql)
        assert r["is_valid"]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. QUERY COMPLEXITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════


class TestQueryComplexity:
    def test_simple_query_low_complexity(self):
        """TC-X1: Simple query has low complexity metrics."""
        v = SOQLValidator("")
        c = v.get_query_complexity("SELECT Id FROM Account")
        assert c["subqueries"] == 0
        assert c["aggregates"] == 0

    def test_subquery_counted(self):
        """TC-X2: Subqueries are counted in complexity."""
        v = SOQLValidator("")
        c = v.get_query_complexity(
            "SELECT Id, (SELECT Id FROM Contacts) FROM Account"
        )
        assert c["subqueries"] == 1

    def test_aggregate_counted(self):
        """TC-X3: Aggregate functions are counted."""
        v = SOQLValidator("")
        c = v.get_query_complexity(
            "SELECT COUNT(Id), SUM(Amount) FROM Opportunity"
        )
        assert c["aggregates"] == 2

    def test_where_conditions_counted(self):
        """TC-X4: WHERE conditions are counted."""
        v = SOQLValidator("")
        c = v.get_query_complexity(
            "SELECT Id FROM Account WHERE Name = 'X' AND Industry = 'Tech' OR Status = 'Active'"
        )
        assert c["where_conditions"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# 7. OPTIMIZATION SUGGESTIONS
# ═══════════════════════════════════════════════════════════════════════════════


class TestOptimizationSuggestions:
    def test_order_by_without_limit_flagged(self):
        """TC-O1: ORDER BY without LIMIT triggers suggestion."""
        v = SOQLValidator("")
        suggestions = v.suggest_optimizations(
            "SELECT Id FROM Account WHERE Name = 'Test' ORDER BY Name"
        )
        assert any("LIMIT" in s for s in suggestions)

    def test_many_fields_flagged(self):
        """TC-O2: Selecting 20+ fields triggers suggestion."""
        fields = ", ".join([f"Field{i}" for i in range(25)])
        v = SOQLValidator("")
        suggestions = v.suggest_optimizations(f"SELECT {fields} FROM Account")
        assert any("fields" in s.lower() for s in suggestions)

    def test_non_indexed_where_flagged(self):
        """TC-O3: WHERE clause without indexed field triggers suggestion."""
        v = SOQLValidator("")
        suggestions = v.suggest_optimizations(
            "SELECT Id FROM Account WHERE Industry = 'Tech'"
        )
        assert any("indexed" in s.lower() for s in suggestions)
