"""Tests for pre_score.py — the pre-scoring orchestrator."""

import json

from conftest import load_script

pre_score_mod = load_script("skills/cirra-ai-sf-audit/scripts/pre_score.py")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_APEX = """\
public with sharing class SimpleService {
    public static List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account LIMIT 100];
    }
}
"""

BAD_APEX = """\
public class BadService {
    public static void doStuff(List<Account> accs) {
        for (Account a : accs) {
            update a;
        }
    }
}
"""

SIMPLE_TRIGGER = """\
trigger AccountTrigger on Account (before insert) {
    AccountTriggerHandler.handle(Trigger.new);
}
"""

SIMPLE_FLOW = """\
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <label>Simple_Flow</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Active</status>
    <start>
        <locationX>50</locationX>
        <locationY>50</locationY>
    </start>
</Flow>
"""

SIMPLE_LWC_HTML = """\
<template>
    <lightning-card title="Hello">
        <p class="slds-p-around_medium">Hello World</p>
    </lightning-card>
</template>
"""

SIMPLE_LWC_JS = """\
import { LightningElement } from 'lwc';

export default class HelloWorld extends LightningElement {}
"""


def _setup_intermediate(tmp_path):
    """Create a minimal intermediate directory structure."""
    inter = tmp_path / "intermediate"

    apex_dir = inter / "apex"
    apex_dir.mkdir(parents=True)
    (apex_dir / "SimpleService.cls").write_text(SIMPLE_APEX)
    (apex_dir / "BadService.cls").write_text(BAD_APEX)

    trigger_dir = inter / "triggers"
    trigger_dir.mkdir(parents=True)
    (trigger_dir / "AccountTrigger.trigger").write_text(SIMPLE_TRIGGER)

    flow_dir = inter / "flows"
    flow_dir.mkdir(parents=True)
    (flow_dir / "Simple_Flow.flow-meta.xml").write_text(SIMPLE_FLOW)

    lwc_dir = inter / "lwc" / "helloWorld"
    lwc_dir.mkdir(parents=True)
    (lwc_dir / "helloWorld.html").write_text(SIMPLE_LWC_HTML)
    (lwc_dir / "helloWorld.js").write_text(SIMPLE_LWC_JS)

    return inter


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pre_score_produces_json_files(tmp_path):
    """All expected JSON score files are created."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    for expected in (
        "apex_scores.json",
        "trigger_findings.json",
        "flow_scores.json",
        "lwc_scores.json",
        "pre_score_summary.json",
    ):
        assert (output / expected).exists(), f"Missing {expected}"


def test_apex_scores_schema(tmp_path):
    """apex_scores.json entries have required keys."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    scores = json.loads((output / "apex_scores.json").read_text())
    assert len(scores) == 2  # SimpleService + BadService
    for entry in scores:
        assert "name" in entry
        assert "score" in entry
        assert "max_score" in entry
        assert entry["max_score"] == 150
        assert "issues" in entry
        assert isinstance(entry["issues"], list)


def test_trigger_findings_schema(tmp_path):
    """trigger_findings.json entries have required keys."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    findings = json.loads((output / "trigger_findings.json").read_text())
    assert len(findings) == 1
    entry = findings[0]
    assert entry["name"] == "AccountTrigger"
    assert "findings" in entry


def test_flow_scores_schema(tmp_path):
    """flow_scores.json entries have required keys."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    scores = json.loads((output / "flow_scores.json").read_text())
    assert len(scores) == 1
    entry = scores[0]
    assert "name" in entry
    assert "score" in entry
    assert entry["max_score"] == 110


def test_lwc_scores_schema(tmp_path):
    """lwc_scores.json entries have required keys."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    scores = json.loads((output / "lwc_scores.json").read_text())
    assert len(scores) == 1
    entry = scores[0]
    assert entry["name"] == "helloWorld"
    assert "score" in entry
    assert entry["max_score"] == 165


def test_summary_contains_all_domains(tmp_path):
    """pre_score_summary.json has all domain keys."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    summary = pre_score_mod.pre_score(inter, output)

    for domain in ("apex", "triggers", "flows", "lwc"):
        assert domain in summary
        assert "scored" in summary[domain]
        assert "below_threshold" in summary[domain]

    assert "needs_llm_review" in summary
    assert isinstance(summary["needs_llm_review"], list)


def test_threshold_flags_low_scorers(tmp_path):
    """Components below threshold appear in needs_llm_review."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    # Use 100% threshold so everything is flagged
    summary = pre_score_mod.pre_score(inter, output, threshold_pct=100)

    review_names = {r["name"] for r in summary["needs_llm_review"]}
    # At 100% threshold, most components should be flagged
    assert len(summary["needs_llm_review"]) > 0
    # BadService with DML in loop should definitely be flagged
    assert "BadService" in review_names


def test_empty_intermediate_dir(tmp_path):
    """Handles empty/missing intermediate subdirectories gracefully."""
    inter = tmp_path / "intermediate"
    inter.mkdir()
    output = tmp_path / "output"

    summary = pre_score_mod.pre_score(inter, output)

    assert summary["apex"]["scored"] == 0
    assert summary["flows"]["scored"] == 0
    assert summary["lwc"]["scored"] == 0


def test_malformed_file_does_not_crash(tmp_path):
    """A file that can't be parsed still produces a score entry."""
    inter = tmp_path / "intermediate"
    apex_dir = inter / "apex"
    apex_dir.mkdir(parents=True)
    (apex_dir / "Broken.cls").write_text("")  # empty file

    output = tmp_path / "output"
    pre_score_mod.pre_score(inter, output)

    scores = json.loads((output / "apex_scores.json").read_text())
    assert len(scores) == 1
    assert scores[0]["name"] == "Broken"


def test_summary_written_to_disk(tmp_path):
    """pre_score_summary.json is written and parseable."""
    inter = _setup_intermediate(tmp_path)
    output = tmp_path / "output"

    pre_score_mod.pre_score(inter, output)

    summary_path = output / "pre_score_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text())
    assert summary["threshold_pct"] == 70
