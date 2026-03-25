"""Tests for the LWC post-tool validation hook script."""

from __future__ import annotations

import io
import json

from conftest import load_script

mod = load_script("skills/cirra-ai-sf-lwc/scripts/post-tool-validate.py")


def test_is_lwc_file_supports_expected_extensions():
    assert mod.is_lwc_file("component.html")
    assert mod.is_lwc_file("component.js")
    assert mod.is_lwc_file("component.css")
    assert not mod.is_lwc_file("component.xml")


def test_main_skips_when_tool_response_failed(monkeypatch, capsys):
    payload = {"tool_input": {"file_path": "component.html"}, "tool_response": {"success": False}}
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(json.dumps(payload)))

    rc = mod.main()
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out == {"continue": True}


def test_main_uses_validator_for_lwc_files(monkeypatch, capsys):
    payload = {"tool_input": {"file_path": "component.html"}, "tool_response": {"success": True}}
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(mod, "validate_lwc_file", lambda _path: {"continue": True, "output": "ok"})

    rc = mod.main()
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["continue"] is True
    assert out["output"] == "ok"


def test_main_non_lwc_file_returns_continue(monkeypatch, capsys):
    payload = {"tool_input": {"file_path": "component.xml"}, "tool_response": {"success": True}}
    monkeypatch.setattr(mod.sys, "stdin", io.StringIO(json.dumps(payload)))

    rc = mod.main()
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out == {"continue": True}
