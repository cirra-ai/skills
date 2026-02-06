"""
Tier 1: parse_variables() helper tests.

Tests name=value parsing, typed variables, $Context prefixed names,
equals-in-value handling, multiple variables, whitespace stripping,
and invalid format rejection.

Points: 2
"""

import pytest
from agent_api_client import parse_variables


@pytest.mark.tier1
@pytest.mark.offline
class TestParseVariables:
    """parse_variables() behaviour."""

    def test_simple_name_value(self):
        """'name=value' produces type=Text by default."""
        result = parse_variables(["name=value"])

        assert len(result) == 1
        assert result[0] == {"name": "name", "type": "Text", "value": "value"}

    def test_typed_variable(self):
        """'name:Number=42' extracts the explicit type."""
        result = parse_variables(["name:Number=42"])

        assert result[0] == {"name": "name", "type": "Number", "value": "42"}

    def test_context_variable(self):
        """'$Context.AccountId=001XX' preserves the $Context prefix."""
        result = parse_variables(["$Context.AccountId=001XX"])

        assert result[0]["name"] == "$Context.AccountId"
        assert result[0]["type"] == "Text"
        assert result[0]["value"] == "001XX"

    def test_context_with_type(self):
        """'$Context.AccountId:Id=001XX' splits at last colon for type."""
        result = parse_variables(["$Context.AccountId:Id=001XX"])

        assert result[0]["name"] == "$Context.AccountId"
        assert result[0]["type"] == "Id"
        assert result[0]["value"] == "001XX"

    def test_equals_in_value(self):
        """'formula=a=b+c' keeps everything after first '=' as the value."""
        result = parse_variables(["formula=a=b+c"])

        assert result[0]["name"] == "formula"
        assert result[0]["value"] == "a=b+c"

    def test_multiple_variables(self):
        """A list of 3 variable strings produces 3 dicts."""
        result = parse_variables([
            "alpha=1",
            "beta:Number=2",
            "$Context.Gamma=3",
        ])

        assert len(result) == 3
        assert result[0]["name"] == "alpha"
        assert result[1]["name"] == "beta"
        assert result[2]["name"] == "$Context.Gamma"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace in name and value is stripped."""
        result = parse_variables(["  name = value  "])

        assert result[0]["name"] == "name"
        assert result[0]["value"] == "value"

    def test_no_equals_raises(self):
        """A string without '=' raises ValueError."""
        with pytest.raises(ValueError, match="Invalid variable format"):
            parse_variables(["invalid"])
