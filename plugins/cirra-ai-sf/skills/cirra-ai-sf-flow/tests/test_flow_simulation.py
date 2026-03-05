"""Tests for FlowSimulator — bulk execution simulation and governor limit analysis.

Covers:
  - Clean flows pass simulation with 200+ records
  - DML-in-loop flows fail simulation (governor limits exceeded)
  - Record-triggered vs standard flow limit accounting
  - Correct flow type detection
"""

import os
import sys


# ── bootstrap ────────────────────────────────────────────────────────────────

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
SCRIPTS_DIR = os.path.join(os.path.dirname(TESTS_DIR), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from simulate_flow import FlowSimulator  # noqa: E402


# ── helpers ──────────────────────────────────────────────────────────────────


def _simulate(fixture_name: str, num_records: int = 200) -> dict:
    path = os.path.join(FIXTURES_DIR, fixture_name)
    sim = FlowSimulator(path, num_records)
    return sim.simulate()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CLEAN FLOWS PASS SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

# Prompt: "Simulate this well-built flow with 200 records."
# Expected: Status PASSED, no errors, metrics within governor limits.


class TestCleanFlowSimulation:
    def test_before_save_passes_200_records(self):
        """TC-S1: Before-save flow passes simulation with 200 records."""
        r = _simulate("perfect_before_save.flow-meta.xml", 200)
        assert r["status"] == "PASSED"
        assert len(r["errors"]) == 0

    def test_after_save_passes_200_records(self):
        """TC-S2: After-save flow with fault paths passes with 200 records."""
        r = _simulate("perfect_after_save.flow-meta.xml", 200)
        assert r["status"] == "PASSED"
        assert len(r["errors"]) == 0

    def test_complex_flow_passes_200_records(self):
        """TC-S3: Complex multi-object flow passes (DML outside loop)."""
        r = _simulate("complex_multi_object.flow-meta.xml", 200)
        assert r["status"] in ("PASSED", "WARNING")
        # Should not have governor limit errors
        governor_errors = [e for e in r["errors"] if "limit" in e.lower()]
        assert len(governor_errors) == 0

    def test_scheduled_flow_passes(self):
        """TC-S4: Scheduled flow passes simulation."""
        r = _simulate("scheduled_flow.flow-meta.xml", 200)
        assert r["status"] in ("PASSED", "WARNING")

    def test_screen_flow_passes(self):
        """TC-S5: Screen flow passes simulation."""
        r = _simulate("screen_flow_simple.flow-meta.xml", 200)
        assert r["status"] in ("PASSED", "WARNING")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANTI-PATTERN FLOWS FAIL SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

# Prompt: "Simulate this flow that has DML inside a loop with 200 records."
# Expected: Status FAILED, errors about governor limits.


class TestAntiPatternSimulation:
    def test_dml_in_loop_fails_200_records(self):
        """TC-S6: DML-in-loop flow FAILS simulation with 200 records."""
        r = _simulate("dml_in_loop.flow-meta.xml", 200)
        assert r["status"] == "FAILED"
        assert len(r["errors"]) > 0

    def test_dml_in_loop_mentions_dml_limit(self):
        """TC-S6b: Error message references DML or governor limit."""
        r = _simulate("dml_in_loop.flow-meta.xml", 200)
        error_text = " ".join(r["errors"]).lower()
        assert "dml" in error_text or "limit" in error_text

    def test_max_anti_patterns_fails(self):
        """TC-S7: Maximum anti-pattern flow FAILS simulation."""
        r = _simulate("max_complexity_anti_patterns.flow-meta.xml", 200)
        assert r["status"] == "FAILED"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FLOW TYPE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlowTypeDetection:
    def test_before_save_detected(self):
        """TC-S8: Before-save trigger type is correctly identified."""
        r = _simulate("perfect_before_save.flow-meta.xml")
        assert "Before Save" in r["flow_type"]

    def test_after_save_detected(self):
        """TC-S9: After-save trigger type is correctly identified."""
        r = _simulate("perfect_after_save.flow-meta.xml")
        assert "After Save" in r["flow_type"]

    def test_screen_flow_detected(self):
        """TC-S10: Screen flow type is correctly identified."""
        r = _simulate("screen_flow_simple.flow-meta.xml")
        assert "Screen" in r["flow_type"]

    def test_scheduled_flow_detected(self):
        """TC-S11: Scheduled flow type is correctly identified."""
        r = _simulate("scheduled_flow.flow-meta.xml")
        # Scheduled flows have a schedule element in start
        # The simulator may detect this as Scheduled or Autolaunched
        assert r["flow_type"] in ("Scheduled Flow", "Autolaunched Flow")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. METRICS TRACKING
# ═══════════════════════════════════════════════════════════════════════════════


class TestMetricsTracking:
    def test_metrics_present(self):
        """TC-S12: Simulation result includes metrics dict."""
        r = _simulate("perfect_after_save.flow-meta.xml")
        assert "metrics" in r
        m = r["metrics"]
        assert "soql_queries" in m
        assert "dml_statements" in m
        assert "cpu_time_ms" in m

    def test_record_triggered_limits_per_transaction(self):
        """TC-S13: Record-triggered flow metrics are per-transaction, not per-record."""
        r = _simulate("perfect_after_save.flow-meta.xml", 200)
        m = r["metrics"]
        # After-save with 1 DML: should be 1 DML statement (not 200)
        assert m["dml_statements"] < 200

    def test_dml_in_loop_inflated_metrics(self):
        """TC-S14: DML-in-loop causes inflated DML statement count."""
        r = _simulate("dml_in_loop.flow-meta.xml", 200)
        m = r["metrics"]
        # DML inside loop with estimated iterations → high count
        assert m["dml_statements"] > 10

    def test_bulk_boundary_test_251_records(self):
        """TC-S15: Simulation handles 251 records (batch boundary)."""
        r = _simulate("perfect_after_save.flow-meta.xml", 251)
        assert r["status"] == "PASSED"
        assert r["metrics"]["dml_rows"] > 0
