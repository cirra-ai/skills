"""Regression tests for parser/layout edge cases in formula safety checks."""

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-metadata/scripts/validate_metadata_operation.py")
analyze_formula_safety = mod.analyze_formula_safety


def test_single_line_braced_loop_detected():
    findings = analyze_formula_safety("for(i=0;i<1;i++){insert rec;}")
    assert any("single-line braced loop" in f for f in findings)


def test_braceless_loop_detected():
    findings = analyze_formula_safety("for(i=0;i<1;i++) insert rec;")
    assert any("braceless loop" in f for f in findings)


def test_comment_false_positive_is_ignored():
    findings = analyze_formula_safety("// for(i=0;i<1;i++){insert rec;}\nTRUE")
    assert findings == []


def test_do_while_style_detected():
    findings = analyze_formula_safety("do { update rec; } while(x > 1);")
    assert any("do/while" in f for f in findings)
