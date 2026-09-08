"""Tests for scripts/check_mcp_signatures.py.

The checker runs in CI via scripts/validate-skills.sh, so false positives matter
as much as detection. Benign shapes that exist in the skills today are pinned
below next to the real mistakes the checker must catch.
"""

from pathlib import Path

from conftest import load_script

checker = load_script("scripts/check_mcp_signatures.py")

REPO_ROOT = Path(__file__).parent.parent


def messages(tmp_path: Path, content: str) -> list[str]:
    md = tmp_path / "doc.md"
    md.write_text(content, encoding="utf-8")
    return [f.message for f in checker.check_file(md)]


def fenced(code: str) -> str:
    return f"```\n{code}\n```\n"


# ── Real mistakes it must catch ───────────────────────────────────────────────


def test_query_parameter_is_rejected(tmp_path):
    out = messages(tmp_path, fenced('soql_query(query="SELECT Id FROM Account")'))
    assert any("no `query=`" in m for m in out)


def test_missing_fields_and_where(tmp_path):
    out = messages(tmp_path, fenced('tooling_api_query(sObject="ApexClass")'))
    assert any("`fields=`" in m for m in out)
    assert any("`whereClause=`" in m for m in out)


def test_delete_with_records(tmp_path):
    out = messages(tmp_path, fenced('sobject_dml(operation="delete", sObject="Account", records=[{"Id": "001"}])'))
    assert any("recordIds" in m for m in out)


def test_sobjecttype_and_orgalias(tmp_path):
    out = messages(
        tmp_path,
        fenced('sobject_dml(operation="insert", sobjectType="Account", records=[{"Name": "x"}], orgAlias="dev")'),
    )
    assert any("sobjectType" in m for m in out)
    assert any("orgAlias" in m for m in out)


def test_create_operation(tmp_path):
    out = messages(tmp_path, fenced('sobject_dml(operation="create", sObject="Account", records=[])'))
    assert any("`insert`" in m for m in out)


def test_order_by_inside_where(tmp_path):
    out = messages(
        tmp_path,
        fenced(
            'soql_query(sObject="Account", fields=["Id"], whereClause="Name != null ORDER BY CreatedDate DESC LIMIT 5")'
        ),
    )
    assert any("orderBy" in m for m in out)


def test_inline_code_span_is_scanned(tmp_path):
    out = messages(tmp_path, 'Use `soql_query(sObject="Account")` to list accounts.')
    assert out


# ── Benign shapes it must accept ──────────────────────────────────────────────


def test_complete_query_call_passes(tmp_path):
    code = """soql_query(
  sObject="Account",
  fields=["Id", "Name", "Owner.Name"],
  whereClause="Industry = 'Technology'",
  orderBy="CreatedDate DESC",
  limit=50
)"""
    assert messages(tmp_path, fenced(code)) == []


def test_delete_with_record_ids_passes(tmp_path):
    assert messages(tmp_path, fenced('sobject_dml(operation="delete", sObject="Account", recordIds=["001"])')) == []


def test_keys_inside_record_literals_are_not_kwargs(tmp_path):
    code = 'sobject_dml(operation="update", sObject="Account", records=[{"Id": "001", "query": "x", "sobjectType": "y"}])'
    assert messages(tmp_path, fenced(code)) == []


def test_prose_mentions_are_ignored(tmp_path):
    assert messages(tmp_path, "Call soql_query(query) as described above.") == []


def test_allow_marker_suppresses(tmp_path):
    content = "<!-- mcp-signatures: allow -->\n" + fenced('soql_query(query="SELECT Id FROM Account")')
    assert messages(tmp_path, content) == []


def test_tool_names_in_other_tools_are_ignored(tmp_path):
    # bulk_query has an optional whereClause; it is not checked.
    assert messages(tmp_path, fenced('bulk_query(sObject="Account", fields=["Id"])')) == []


# ── The repo itself must be clean ─────────────────────────────────────────────


def test_skills_tree_is_clean():
    found = []
    for md in sorted((REPO_ROOT / "skills").rglob("*.md")):
        if "__pycache__" in md.parts:
            continue
        found.extend(str(f) for f in checker.check_file(md))
    assert not found, "\n".join(found)
