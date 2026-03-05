"""Tests for skills/cirra-ai-sf-lwc/scripts/template_validator.py"""

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-lwc/scripts/template_validator.py")
LWCTemplateValidator = mod.LWCTemplateValidator


def validator_for(tmp_path, html: str) -> LWCTemplateValidator:
    """Write html to a temp file and return a validator for it."""
    f = tmp_path / "myComponent.html"
    f.write_text(html, encoding="utf-8")
    return LWCTemplateValidator(str(f))


def issues_of(tmp_path, html: str) -> list:
    return validator_for(tmp_path, html).validate()["issues"]


# ── Clean template ────────────────────────────────────────────────────────────


def test_clean_template_has_no_issues(tmp_path):
    html = "<template><p>{greeting}</p></template>"
    assert issues_of(tmp_path, html) == []


# ── Inline expressions ────────────────────────────────────────────────────────


def test_arithmetic_expression_flagged(tmp_path):
    html = "<template><p>{price * quantity}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("Arithmetic" in i["message"] for i in issues)
    assert all(i["severity"] == "CRITICAL" for i in issues)


def test_ternary_expression_flagged(tmp_path):
    html = "<template><p>{isActive ? 'Yes' : 'No'}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("Ternary" in i["message"] for i in issues)


def test_string_concatenation_flagged(tmp_path):
    html = "<template><p>{'Hello ' + name}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("concatenation" in i["message"].lower() for i in issues)


# ── Method calls ──────────────────────────────────────────────────────────────


def test_length_property_flagged(tmp_path):
    html = "<template><p>{items.length}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("length" in i["message"].lower() for i in issues)


def test_filter_method_flagged(tmp_path):
    html = "<template><p>{items.filter(i => i.active)}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("filter" in i["message"].lower() for i in issues)


def test_map_method_flagged(tmp_path):
    html = "<template><p>{items.map(i => i.name)}</p></template>"
    issues = issues_of(tmp_path, html)
    assert any("map" in i["message"].lower() for i in issues)


# ── Comparisons in conditionals ───────────────────────────────────────────────


def test_comparison_in_if_true_flagged(tmp_path):
    html = "<template><div if:true={count > 0}>Show</div></template>"
    issues = issues_of(tmp_path, html)
    assert any("Comparison" in i["message"] for i in issues)


def test_logical_and_in_if_true_flagged(tmp_path):
    html = "<template><div if:true={isActive && isVisible}>Show</div></template>"
    issues = issues_of(tmp_path, html)
    assert any("AND" in i["message"] for i in issues)


def test_negation_in_if_true_flagged(tmp_path):
    html = "<template><div if:true={!isHidden}>Show</div></template>"
    issues = issues_of(tmp_path, html)
    assert any("Negation" in i["message"] for i in issues)


# ── Framework syntax mistakes ─────────────────────────────────────────────────


def test_vue_v_for_flagged(tmp_path):
    html = '<template><li v-for="item in items">{{item}}</li></template>'
    issues = issues_of(tmp_path, html)
    assert any("v-for" in i["message"] for i in issues)


def test_vue_v_if_flagged(tmp_path):
    html = '<template><div v-if="isActive">content</div></template>'
    issues = issues_of(tmp_path, html)
    assert any("v-if" in i["message"] for i in issues)


def test_react_classname_flagged(tmp_path):
    html = '<template><div className="my-class">content</div></template>'
    issues = issues_of(tmp_path, html)
    assert any("className" in i["message"] for i in issues)


def test_angular_ng_if_flagged(tmp_path):
    html = '<template><div *ngIf="isActive">content</div></template>'
    issues = issues_of(tmp_path, html)
    assert any("ngIf" in i["message"] for i in issues)


# ── Event handler mistakes ────────────────────────────────────────────────────


def test_event_handler_with_args_flagged(tmp_path):
    html = "<template><button onclick={handleClick(item)}>Click</button></template>"
    issues = issues_of(tmp_path, html)
    assert any("Event handler" in i["message"] for i in issues)
    # Advisory — should be WARNING not CRITICAL
    assert all(i["severity"] == "WARNING" for i in issues if "Event handler" in i["message"])


# ── Comments ──────────────────────────────────────────────────────────────────


def test_commented_out_patterns_not_flagged(tmp_path):
    # A bad pattern on a commented line should be ignored
    html = "<!-- {items.length} -->\n<template><p>{greeting}</p></template>"
    issues = issues_of(tmp_path, html)
    assert issues == []


# ── Missing iteration key ─────────────────────────────────────────────────────


def test_for_each_without_key_warns(tmp_path):
    html = (
        "<template>"
        '  <ul for:each={items} for:item="item">\n'
        "    <li>{item.name}</li>\n"
        "  </ul>"
        "</template>"
    )
    issues = issues_of(tmp_path, html)
    assert any("key" in i["message"].lower() for i in issues)


def test_for_each_with_key_no_warning(tmp_path):
    html = (
        "<template>"
        '  <ul for:each={items} for:item="item">\n'
        "    <li key={item.id}>{item.name}</li>\n"
        "  </ul>"
        "</template>"
    )
    issues = issues_of(tmp_path, html)
    key_issues = [i for i in issues if "key" in i["message"].lower()]
    assert key_issues == []


# ── File errors ───────────────────────────────────────────────────────────────


def test_nonexistent_file_reports_error():
    v = LWCTemplateValidator("/nonexistent/path/component.html")
    result = v.validate()
    assert result["issue_count"] > 0
    assert any("Cannot read file" in i["message"] for i in result["issues"])


def test_result_includes_filename(tmp_path):
    html = "<template><p>{greeting}</p></template>"
    result = validator_for(tmp_path, html).validate()
    assert result["file"] == "myComponent.html"
