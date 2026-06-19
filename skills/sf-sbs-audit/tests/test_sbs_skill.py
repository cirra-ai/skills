"""Tests for the sf-sbs-audit skill.

Asserts:
1. The vendored CC BY-SA 4.0 dataset is structurally sound and carries
   attribution metadata.
2. The LICENSE / NOTICE / SBS_VERSION / ATTRIBUTION.txt files exist and
   contain the required strings.
3. SKILL.md keeps the bulletproof-attribution guardrail in place — i.e.
   it still tells the LLM to render ATTRIBUTION.txt verbatim. The
   guardrail must not silently regress.
4. SKILL.md keeps the opt-in trigger guardrail and the
   no-paraphrase-SBS-prose guardrail.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "references" / "sbs"
SKILL_MD = SKILL_DIR / "SKILL.md"

CONTROL_ID_RE = re.compile(r"^SBS-[A-Z]+-\d+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")

CATEGORIES = {
    "ACS",
    "AUTH",
    "CODE",
    "CPORTAL",
    "DATA",
    "DEP",
    "FDNS",
    "FILE",
    "INT",
    "MON",
    "OAUTH",
    "SECCONF",
}


@pytest.fixture(scope="module")
def controls_doc() -> dict:
    return json.loads((DATA_DIR / "controls.json").read_text(encoding="utf-8"))


class TestVendoredDataset:
    def test_license_block_present(self, controls_doc: dict) -> None:
        lic = controls_doc["_license"]
        assert lic["license"] == "CC BY-SA 4.0"
        assert lic["license_uri"] == "https://creativecommons.org/licenses/by-sa/4.0/"
        assert lic["source"] == "https://github.com/Salesforce-Security-Benchmark/docs-site"
        assert SHA_RE.match(lic["upstream_commit"])
        assert "Security Benchmark for Salesforce" in lic["attribution"]

    def test_controls_array_non_empty(self, controls_doc: dict) -> None:
        assert isinstance(controls_doc["controls"], list)
        assert len(controls_doc["controls"]) > 0

    def test_every_control_has_expected_shape(self, controls_doc: dict) -> None:
        failures: list[str] = []
        for c in controls_doc["controls"]:
            if not CONTROL_ID_RE.match(c["control_id"]):
                failures.append(f"bad id: {c['control_id']}")
                continue
            if c["category"] not in CATEGORIES:
                failures.append(f"{c['control_id']}: unknown category {c['category']}")
            if c["remediation"]["scope"] not in {"org", "entity", "mechanism", "inventory"}:
                failures.append(f"{c['control_id']}: invalid scope")
            if c["remediation"]["scope"] == "entity":
                if not c["remediation"].get("entity_type"):
                    failures.append(f"{c['control_id']}: entity scope missing entity_type")
            elif "entity_type" in c["remediation"]:
                failures.append(f"{c['control_id']}: non-entity scope has entity_type")
            if c["risk_level"] is not None and c["risk_level"] not in {
                "Critical",
                "High",
                "Moderate",
            }:
                failures.append(f"{c['control_id']}: invalid risk_level {c['risk_level']}")
            if not c["doc_url"].startswith("https://docs.securitybenchmark.org/benchmark/"):
                failures.append(f"{c['control_id']}: bad doc_url")
            if f"#{c['control_id'].lower()}" not in c["doc_url"]:
                failures.append(f"{c['control_id']}: doc_url missing anchor")
        assert failures == []


class TestAttributionArtifacts:
    def test_license_file_carries_cc_by_sa(self) -> None:
        text = (DATA_DIR / "LICENSE").read_text(encoding="utf-8")
        assert "CC BY-SA 4.0" in text
        # Match the canonical CC license URI as a full line in the file
        # (rather than a bare-substring `in` check, which CodeQL's URL-
        # sanitization rule flags even in test code).
        assert re.search(
            r"^[ ]*License URI:\s+https://creativecommons\.org/licenses/by-sa/4\.0/\s*$",
            text,
            flags=re.MULTILINE,
        ), "LICENSE must contain the canonical CC BY-SA 4.0 URI line"

    def test_notice_file_states_modifications(self) -> None:
        text = (DATA_DIR / "NOTICE").read_text(encoding="utf-8")
        assert "Based on Security Benchmark for Salesforce" in text
        assert "modifications" in text.lower()

    def test_sbs_version_pins_a_sha(self) -> None:
        text = (DATA_DIR / "SBS_VERSION").read_text(encoding="utf-8")
        m = re.search(r"^upstream_sha:\s*([0-9a-f]{40})\b", text, flags=re.MULTILINE)
        assert m is not None, "SBS_VERSION must pin a 40-char SHA"

    def test_attribution_txt_canonical_shape(self) -> None:
        """ATTRIBUTION.txt is the source of truth the LLM is told to render
        verbatim. It MUST carry every CC BY-SA 4.0 element so paraphrasing
        cannot weaken it. Asserted as a set of full-line matches (rather
        than bare-substring URL checks, which CodeQL's URL-sanitization
        rule flags even in test code).
        """
        text = (DATA_DIR / "ATTRIBUTION.txt").read_text(encoding="utf-8")
        lines = set(text.splitlines())
        required_lines = {
            "Based on Security Benchmark for Salesforce (SBS) with modifications.",
            "Original work: https://github.com/Salesforce-Security-Benchmark/docs-site",
            "Documentation: https://docs.securitybenchmark.org/",
            "Licensed under CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/",
        }
        missing = required_lines - lines
        assert not missing, f"ATTRIBUTION.txt missing required canonical lines: {sorted(missing)}"
        assert re.search(r"^Upstream commit:\s+[0-9a-f]{40}\s*$", text, flags=re.MULTILINE), (
            "ATTRIBUTION.txt must include the pinned upstream commit SHA"
        )


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


class TestSkillGuardrails:
    """SKILL.md is the contract with the LLM. Each guardrail this skill
    relies on is asserted here so it cannot silently regress under future
    edits.
    """

    def test_opt_in_trigger_present(self, skill_text: str) -> None:
        assert "opt-in" in skill_text.lower()
        assert "do not" in skill_text.lower()
        assert "explicitly asks" in skill_text.lower()

    def test_no_paraphrase_sbs_prose_guardrail(self, skill_text: str) -> None:
        # Loose match: the rule must mention not paraphrasing/summarizing SBS prose.
        lower = skill_text.lower()
        assert "do not paraphrase" in lower
        assert "sbs" in lower
        assert "cc by-sa 4.0" in lower

    def test_bulletproof_attribution_rule_present(self, skill_text: str) -> None:
        """The single most important guardrail: LLM must include
        ATTRIBUTION.txt verbatim. If this assertion fails, the
        license-compliance posture has regressed and the change must NOT
        ship.
        """
        lower = skill_text.lower()
        assert "verbatim" in lower, "Bulletproof attribution rule removed"
        assert "attribution.txt" in lower, "ATTRIBUTION.txt reference removed"
        assert "do not paraphrase" in lower
        assert "do not omit" in lower

    def test_check_rubric_section_present(self, skill_text: str) -> None:
        assert "## Step 3" in skill_text or "Check rubric" in skill_text
        assert "not_implemented" in skill_text

    def test_no_enforcement_guardrail_present(self, skill_text: str) -> None:
        lower = skill_text.lower()
        assert "do not enforce" in lower or "does not enforce" in lower

    def test_frontmatter_version_format(self, skill_text: str) -> None:
        # Must have `metadata.version: X.Y.Z` in frontmatter
        m = re.search(r"^metadata:\s*$\s*version:\s*(\d+\.\d+\.\d+)\s*$", skill_text, flags=re.MULTILINE)
        assert m is not None, "SKILL.md frontmatter must declare metadata.version"
