# Dispatch Test Report — 2026-03-25

## Summary

| Skill | Tests | Phase 1 Pass | Phase 1 Fail | Phase 1 Warn |
| --- | --- | --- | --- | --- |
| sf-apex | 8 | 7 | 0 | 1 |
| sf-audit | 8 | 8 | 0 | 0 |
| sf-data | 9 | 9 | 0 | 0 |
| sf-diagram | 10 | 10 | 0 | 0 |
| sf-flow | 8 | 8 | 0 | 0 |
| sf-kugamon | 8 | 7 | 0 | 1 |
| sf-lwc | 8 | 8 | 0 | 0 |
| sf-metadata | 8 | 8 | 0 | 0 |
| sf-orders | 9 | 9 | 0 | 0 |
| sf-permissions | 12 | 12 | 0 | 0 |
| **TOTAL** | **88** | **86** | **0** | **2** |

**Pass rate**: 98% (86/88 pass, 0 fail, 2 non-blocking warnings)

Phase 2 (prompt simulation) was run on 5 representative test cases — all 5 passed. See "Phase 2 Results" below.

---

## Phase 1 Results (Static Analysis)

### Checks performed per test case

1. **Dispatch Table Coverage** — Dispatch value matches a workflow name in SKILL.md
2. **Argument-Hint Completeness** — first-word keyword appears in argument-hint
3. **Tool References** — First tool / Should call appear in matched workflow; Should NOT call absent
4. **Menu Options** — no-args menu matches SKILL.md
5. **Cross-References** — Follow-up skills exist; no stale `cirra-ai-sf-*` references

### Per-skill results

- **sf-apex**: 7 PASS, 1 WARN
- **sf-audit**: 8 PASS
- **sf-data**: 9 PASS
- **sf-diagram**: 10 PASS
- **sf-flow**: 8 PASS
- **sf-kugamon**: 7 PASS, 1 WARN
- **sf-lwc**: 8 PASS
- **sf-metadata**: 8 PASS
- **sf-orders**: 9 PASS
- **sf-permissions**: 12 PASS

---

## Warnings

### WARN: sf-apex / "ambiguous — just a class name" / 1.1 Dispatch Table Coverage

- **Test says**: `(ambiguous — could be validate, update, or describe)`
- **Issue**: SKILL.md lists only Create, Update, Validate workflows — no "Describe" workflow exists for sf-apex
- **Impact**: Low — the skill correctly asks the user. The test case comment is misleading but the test behavior (should ask user: yes) is correct.
- **Recommendation**: Update test case text to `(ambiguous — could be validate or update)`, removing the non-existent "describe" option.

### WARN: sf-kugamon / "edge case — kuga_sub package not installed" / 1.3 Tool References

- **Test says**: `Should NOT call: sobject_dml`
- **Issue**: SKILL.md uses `sobject_create` for quote creation in some paths and `sobject_dml` in others. The distinction between `sobject_create` and `sobject_dml` is unclear in the Kugamon SKILL.md.
- **Impact**: Low — the test validates the correct fallback behavior when the kuga_sub package is absent.
- **Recommendation**: Clarify in SKILL.md whether quote creation uses `sobject_create` or `sobject_dml` consistently.

---

## Phase 2 Results (Prompt Simulation)

5 representative test cases were run through model agents. Each agent received the full SKILL.md as system context plus the test input, and reported its dispatch decision, tool sequence, and user interaction plan.

| # | Skill | Test Case | Dispatch | Init | First Tool | Ask User | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | sf-metadata | describe PermissionSet | Describe Object | yes, before-workflow | `sobject_describe(sObject="PermissionSet")` | no | **PASS** |
| 2 | sf-metadata | (no arguments) | (none — menu) | no, deferred | (none) | yes — 4-option menu | **PASS** |
| 3 | sf-metadata | create currency field on Account | Create Metadata (fast) | yes, before-workflow | `sobject_describe(sObject="Account")` | no (FLS prompt after) | **PASS** |
| 4 | sf-data | raw SOQL query | Query Data (fast) | yes, before-workflow | `soql_query` with exact params | no | **PASS** |
| 5 | sf-permissions | analyze who can delete Account | Analyze → "Who has X?" | yes, before-workflow | `soql_query(ObjectPermissions, PermissionsDelete=true)` | no | **PASS** |

### Phase 2 Observations

1. **Init timing nuance confirmed**: Test #2 (no arguments) correctly deferred `cirra_ai_init()` until after the user picks a workflow. This validates the `Init timing: after-menu` field we added.

2. **Fast path detection works**: Test #3 and #4 both correctly identified the fast path for simple, unambiguous operations.

3. **Tool param precision**: Test #5 produced the exact `whereClause` (`SobjectType = 'Account' AND PermissionsDelete = true`) and identified the hex ID caveat from the SKILL.md.

4. **FLS post-action**: Test #3 correctly identified the mandatory Permission Set prompt after field creation.

---

## Cross-Skill Reference Validation

All follow-up skills referenced in test cases exist as directories:

| Skill | References | Valid |
| --- | --- | --- |
| sf-audit | sf-apex, sf-flow, sf-lwc, sf-metadata, sf-permissions | Yes |
| sf-data | sf-metadata | Yes |
| sf-diagram | sf-metadata, sf-permissions, sf-flow | Yes |
| sf-flow | sf-data, sf-metadata | Yes |
| sf-metadata | sf-data, sf-permissions, sf-diagram | Yes |
| sf-permissions | sf-data, sf-diagram, sf-metadata | Yes |

No stale `cirra-ai-sf-*` references found in any SKILL.md.

---

## Recommendations

### Test case fixes (low priority)

1. **sf-apex "ambiguous" test**: Remove "describe" from the list of possible workflows — sf-apex has no Describe workflow.
2. **sf-kugamon edge case**: Clarify `sobject_create` vs `sobject_dml` usage in the test notes.

### SKILL.md improvements (future)

1. **sf-kugamon**: Standardize DML tool usage (`sobject_dml` vs `sobject_create`) across all quote creation paths.
2. **sf-apex**: Consider adding a "Describe Apex" workflow (view class source without modifying) since it's a natural user intent when providing just a class name.

### Test coverage gaps (future)

1. **Phase 2 coverage**: Only 5 of 88 test cases were run through prompt simulation. Expand to all 88 for full validation.
2. **Error paths**: No test cases cover MCP tool failures (e.g., `cirra_ai_init()` fails, object doesn't exist, permission denied).
3. **Multi-turn**: All tests are single-turn. Consider adding tests for multi-turn workflows (user picks from menu, then provides details).

---

## Conclusion

All 10 skills pass Phase 1 static analysis with zero failures. The 2 warnings are documentation clarifications, not functional issues. Phase 2 prompt simulation confirms that models correctly interpret the SKILL.md dispatch tables and produce the expected tool sequences.

The skills are ready for production use.
