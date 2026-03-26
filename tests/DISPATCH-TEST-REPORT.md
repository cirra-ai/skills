# Dispatch Test Report — 2026-03-26

## Pytest

```
111/111 passed (0.21s)
```

All unit tests in `tests/` pass: apex validator, data MCP validator, generate pages, metadata validator, pre-MCP validate, SOQL validator, template validator.

---

## Phase 1: Static SKILL.md Analysis

```
python3 tests/validate_dispatch_tests.py
```

| Skill          | Tests | Pass | Fail |
|----------------|-------|------|------|
| sf-apex        | 9     | 9    | 0    |
| sf-audit       | 8     | 8    | 0    |
| sf-data        | 9     | 9    | 0    |
| sf-diagram     | 9     | 9    | 0    |
| sf-flow        | 8     | 8    | 0    |
| sf-kugamon     | 7     | 7    | 0    |
| sf-lwc         | 8     | 8    | 0    |
| sf-metadata    | 7     | 7    | 0    |
| sf-orders      | 7     | 7    | 0    |
| sf-permissions | 12    | 12   | 0    |
| **TOTAL**      | **84**| **84**| **0**|

**Result: ALL PASS — 0 defects, 0 warnings.**

---

## Phase 2: Prompt Simulation

All 84 test cases were run through model agents (one agent per skill, Sonnet). Each agent received the full SKILL.md as system context plus all test inputs for that skill, and reported dispatch decisions, tool sequences, and user interaction plans.

### Phase 2 Summary

| Skill          | Tests | Phase 2 Pass | Phase 2 Fail | Phase 2 Warn |
|----------------|-------|-------------|-------------|-------------|
| sf-apex        | 9     | 9           | 0           | 0           |
| sf-audit       | 8     | 8           | 0           | 0           |
| sf-data        | 9     | 9           | 0           | 0           |
| sf-diagram     | 9     | 9           | 0           | 0           |
| sf-flow        | 8     | 8           | 0           | 0           |
| sf-kugamon     | 7     | 7           | 0           | 0           |
| sf-lwc         | 8     | 8           | 0           | 0           |
| sf-metadata    | 7     | 7           | 0           | 0           |
| sf-orders      | 7     | 7           | 0           | 0           |
| sf-permissions | 12    | 12          | 0           | 0           |
| **TOTAL**      | **84**| **84**      | **0**       | **0**       |

**Result: ALL PASS — 0 failures, 0 warnings.**

### Test Count Verification

File heading counts were cross-checked against agent-reported counts:

```
File counts:
  sf-apex:        9 tests    Agent: 9/9 PASS   ✓
  sf-audit:       8 tests    Agent: 8/8 PASS   ✓
  sf-data:        9 tests    Agent: 9/9 PASS   ✓
  sf-diagram:     9 tests    Agent: 9/9 PASS   ✓
  sf-flow:        8 tests    Agent: 8/8 PASS   ✓
  sf-kugamon:     7 tests    Agent: 7/7 PASS   ✓
  sf-lwc:         8 tests    Agent: 8/8 PASS   ✓
  sf-metadata:    7 tests    Agent: 7/7 PASS   ✓
  sf-orders:      7 tests    Agent: 7/7 PASS   ✓
  sf-permissions: 12 tests   Agent: 12/12 PASS ✓
  Total:          84 tests
```

Note: The sf-apex agent initially reported "8/8 PASS" in its summary line but actually tested all 9 cases (verified by reviewing all 9 individual case reports). The miscount was in the summary string only, not in coverage.

---

## Phase 2 Observations

1. **Init timing nuance confirmed**: No-argument tests across all skills correctly deferred `cirra_ai_init()` until after the user picks a workflow. This validates the `Init timing: after-menu` field.

2. **Fast path detection works**: Agents correctly identified fast path for simple, unambiguous operations (raw SOQL, single field creation, simple component scaffolding) and full path for complex operations (natural language queries, bulk operations, multi-step workflows).

3. **Tool param precision**: Agents produced exact `whereClause` values, correct `sObject` names, and identified known caveats from SKILL.md (hex ID resolution in sf-permissions, MALFORMED_ID risk in sf-orders, leading wildcard selectivity in sf-data).

4. **FLS post-action**: sf-metadata create field test correctly identified the mandatory Permission Set prompt after field creation.

5. **Destructive operation guards**: All delete/bulk-delete tests correctly required user confirmation before executing.

6. **Cross-skill routing**: sf-audit correctly delegated scoring to domain skills (sf-apex, sf-flow, sf-lwc, sf-metadata, sf-permissions) and gated deep-dive behind Phase B approval.

7. **Package detection**: sf-kugamon correctly gated `kuga_sub__*` field usage behind `sobject_describe` package detection, with clean fallback path when HAS_KUGA_SUB = false.

8. **Template-driven vs org-connected**: sf-diagram correctly identified OAuth/integration/landscape diagrams as template-driven (zero MCP calls) and ERD as the only type requiring `cirra_ai_init` + org queries.

---

## Cross-Skill Reference Validation

All follow-up skills referenced in test cases exist as directories:

| Skill          | References                                            | Valid |
|----------------|-------------------------------------------------------|-------|
| sf-audit       | sf-apex, sf-flow, sf-lwc, sf-metadata, sf-permissions | Yes   |
| sf-data        | sf-metadata                                           | Yes   |
| sf-diagram     | sf-metadata, sf-permissions, sf-flow                  | Yes   |
| sf-flow        | sf-data, sf-metadata                                  | Yes   |
| sf-metadata    | sf-data, sf-permissions, sf-diagram                   | Yes   |
| sf-permissions | sf-data, sf-diagram, sf-metadata                      | Yes   |

No stale `cirra-ai-sf-*` references found in any SKILL.md.

---

## Failure Details

None.

## Warnings

None.

---

## Recommendations

### Test coverage gaps (future)

1. **Error paths**: No test cases cover MCP tool failures (e.g., `cirra_ai_init()` fails, object doesn't exist, permission denied).
2. **Multi-turn**: All tests are single-turn. Consider adding tests for multi-turn workflows (user picks from menu, then provides details).
3. **Batch boundary testing**: sf-data bulk delete tests the 200-record batch concept but doesn't verify exact batching behavior at the boundary (200 vs 201 records).

---

## Conclusion

All 10 skills pass Phase 1 static analysis and Phase 2 prompt simulation with 84/84 tests passing. No defects or warnings.
