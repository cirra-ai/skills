# Backend spec: resolve named JSON Patch paths for nested `add`

**Status:** Ready for `cloud-app` implementation  
**Date:** 2026-08-08  
**Repo:** `cirra-ai/cloud-app` (MCP metadata patch preprocessing)  
**Skills repo PR (investigation notes):** https://github.com/cirra-ai/skills/pull/146  
**Primary entrypoint:** shared `preprocessJSONPatch` (used by `metadata_update`, `permission_set_update`, `profile_update`; confirm Layout shares or forks)  
**Verified against:** Integration Test Org (Cirra int-test sandbox)

This is a **backend** change. Skills cannot fix the failure; they can only document workarounds until this ships.

---

## 1. Bug

### Symptom

`metadata_update` with Flow `patch` returns `OPERATION_PATH_CANNOT_ADD` when an intermediate array element is addressed by **name** and the op is `add` into a nested array:

```json
{
  "op": "add",
  "path": "/decisions/Route_By_Industry/rules/-",
  "value": { "name": "Industry_10", "...": "..." }
}
```

```json
{ "op": "add", "path": "/assignments/Set_Branch_09/assignmentItems/-", "value": { "...": "..." } }
```

### Controls that already work

| Case                                     | Path                                                      | Result  |
| ---------------------------------------- | --------------------------------------------------------- | ------- |
| Fully numeric nested add                 | `/decisions/2/rules/-`                                    | Success |
| Top-level array append                   | `/assignments/-`                                          | Success |
| Named replace/remove                     | `/assignments/Init_Counters/label`, `/formulas/fx_Pad_01` | Success |
| Named parent, replace whole nested array | `/decisions/Route_By_Industry/rules`                      | Success |

### Diagnostic signal

On failing `add`, the error’s `operation.path` still contains the unresolved name (`Route_By_Industry`).  
On failing nested-name `replace`, the error shows a **partially rewritten** path (`/decisions/2/rules/Industry_10/label`).

So name→index runs for some ops, but **not for `add` that navigates through a named intermediate**.

---

## 2. Out of scope for this ticket (already fixed)

The recent singleton / omitted-array preprocess work is **not** the bug. Live checks passed for:

- Permission Set: append to omitted `fieldPermissions` / `objectPermissions` via `/-`
- Permission Set: name-based replace/remove on `/fieldPermissions/{Field}/...`
- Profile: `fieldPermissions/-` add + name-based replace
- Layout: numeric `/layoutSections/0/layoutColumns/1/layoutItems/-` add
- Prototype-path rejection (keep covered by existing tests)

Do **not** regress that suite.

---

## 3. Required behavior

### 3.1 Contract

After `preprocessJSONPatch(document, operations)`:

1. Every operation `path` (and `from` for `move`/`copy`) is a JSON Pointer whose array segments are either:
   - decimal indices, or
   - `-` (RFC 6902 append), or
   - object property names on non-array parents.
2. No identity-key tokens (`name`, `field`, etc.) remain as array indices.
3. This holds for **all** ops: `add`, `remove`, `replace`, `move`, `copy`, `test`.
4. Especially for `add` whose final segment is `-` or `n` where `n === parentArray.length`.

### 3.2 Identity keys (existing)

Reuse the identity-key map already used by the singleton fix. Minimum:

| Parent array (examples)                                         | Identity property |
| --------------------------------------------------------------- | ----------------- |
| Flow `decisions`, `assignments`, `formulas`, `recordLookups`, … | `name`            |
| Permission Set / Profile `fieldPermissions`                     | `field`           |
| Other “default-name arrays” already handled                     | existing key      |

If multiple elements share the same identity value: fail with a clear ambiguity error (do not pick the first silently).

### 3.3 Nested identity (optional follow-up)

`/decisions/Route_By_Industry/rules/Industry_10/label` is **not** required for this ticket. Docs already say numeric indices below top-level named elements. Optional follow-up only.

---

## 4. Implementation

### 4.1 Preprocess pipeline (order matters)

Keep a single shared pipeline. Suggested order:

```text
1. Reject prototype-related segments (__proto__, constructor, prototype)
2. Normalize singleton children → arrays  (existing)
3. Initialize omitted arrays for add+/‑ targets  (existing)
4. Resolve identity-key path segments → numeric indices  (FIX: must run for add)
5. Apply fast-json-patch to (normalizedDocument, rewrittenOps)
```

Today step 4 effectively skips or short-circuits for `add` when the final segment does not already exist as a value path. That is the bug.

### 4.2 Name resolution algorithm

```ts
function rewritePointer(doc: unknown, pointer: string): string {
  const segments = parseJsonPointer(pointer); // RFC 6901 decode (~0/~1)
  let node: unknown = doc;
  const out: string[] = [];

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const isLast = i === segments.length - 1;

    if (Array.isArray(node)) {
      if (seg === '-' || isDecimalIndex(seg)) {
        out.push(seg);
        if (!isLast) {
          if (seg === '-') throw invalid("cannot traverse past '-'");
          node = node[Number(seg)];
        }
        continue;
      }

      // Identity-key lookup — REQUIRED even when remaining path is add into a child
      const key = identityKeyForArray(node /* parent path context */);
      const idx = node.findIndex((el) => isObject(el) && String(el[key]) === seg);
      if (idx < 0) {
        throw nameNotFound({ pointer, segment: seg, parentPath: '/' + out.join('/') });
      }
      const dup = node.filter((el) => isObject(el) && String(el[key]) === seg);
      if (dup.length > 1) {
        throw nameAmbiguous({ pointer, segment: seg, count: dup.length });
      }
      out.push(String(idx));
      if (!isLast) node = node[idx];
      continue;
    }

    // Object / primitive traversal
    if (!isObject(node) || !(seg in node)) {
      // For add into a missing *array* that omitted-array init should have created,
      // this should not happen. For true missing parents, fail clearly.
      if (!isLast) throw pathNotFound({ pointer, segment: seg });
      out.push(seg);
      continue;
    }
    out.push(seg);
    if (!isLast) node = (node as Record<string, unknown>)[seg];
  }

  return '/' + out.join('/');
}

function rewriteOperation(doc: unknown, op: Operation): Operation {
  const next = { ...op, path: rewritePointer(doc, op.path) };
  if ('from' in op && typeof op.from === 'string') {
    next.from = rewritePointer(doc, op.from);
  }
  return next;
}
```

Critical rules:

1. **Do not** require the full original path to already exist as a leaf before rewriting.  
   For `add /decisions/Route_By_Industry/rules/-`, only `/decisions/Route_By_Industry` must exist; `rules` must be an array (possibly empty / just initialized); `-` is the append token.
2. **Do** rewrite every non-numeric, non-`-` segment against an array parent, regardless of `op`.
3. **Do not** treat `-` as an identity name.
4. Rewrite `path` and `from` with the same function.
5. Run rewrite on the **normalized** document (after singleton + omitted-array steps).

### 4.3 Likely code fix locations (cloud-app)

Search / touch (names may vary slightly):

- `preprocessJSONPatch` (shared)
- Name-resolution helper (whatever converts `/decisions/My_Decision` → `/decisions/2`)
- Call sites in `metadata_update`, `permission_set_update`, `profile_update`

Look for gates such as:

- `if (op.op !== "add") resolveNames(...)`
- “resolve only if `getValueByPointer(doc, path)` succeeds”
- skipping rewrite when final segment is `-`

Remove those gates; keep prototype rejection and array normalization.

### 4.4 Errors

| Condition                              | Error code (suggested) | Message must include                       |
| -------------------------------------- | ---------------------- | ------------------------------------------ |
| Identity segment not found             | `NAME_PATH_NOT_FOUND`  | original pointer, segment, parent path     |
| Ambiguous identity                     | `NAME_PATH_AMBIGUOUS`  | original pointer, segment, match count     |
| Prototype segment                      | existing rejection     | unchanged                                  |
| Post-rewrite `fast-json-patch` failure | existing               | **rewritten** path (and original if cheap) |

Do not surface unresolved named paths to `fast-json-patch` (that produces opaque `OPERATION_PATH_CANNOT_ADD`).

---

## 5. Unit tests (cloud-app)

Place next to the existing singleton / omitted-array / prototype tests for `preprocessJSONPatch`.

### 5.1 Fixture (minimal Flow-like doc)

```json
{
  "decisions": [
    { "name": "Check_Account_Found", "rules": [{ "name": "Account_Found" }] },
    { "name": "Route_By_Industry", "rules": [{ "name": "Industry_01" }, { "name": "Industry_02" }] }
  ],
  "assignments": [
    {
      "name": "Set_Branch_09",
      "assignmentItems": [
        {
          "assignToReference": "var_BranchCode",
          "operator": "Assign",
          "value": { "stringValue": "BR09" }
        }
      ]
    }
  ]
}
```

### 5.2 Cases

| ID    | Input op                                                          | Expect rewritten path                     | Expect apply             |
| ----- | ----------------------------------------------------------------- | ----------------------------------------- | ------------------------ |
| BE-F1 | `add` `/decisions/Route_By_Industry/rules/-`                      | `/decisions/1/rules/-`                    | rule appended            |
| BE-F2 | `add` `/decisions/Route_By_Industry/rules/2`                      | `/decisions/1/rules/2`                    | append at end            |
| BE-F3 | `add` `/assignments/Set_Branch_09/assignmentItems/-`              | `/assignments/0/assignmentItems/-`        | item appended            |
| BE-F4 | `add` `/decisions/1/rules/-`                                      | unchanged numeric                         | still works              |
| BE-F5 | `replace` `/assignments/Set_Branch_09/label` value `"X"`          | `/assignments/0/label`                    | still works              |
| BE-F6 | `add` `/assignments/-`                                            | unchanged                                 | still works              |
| BE-F7 | `add` `/decisions/Missing/rules/-`                                | throws `NAME_PATH_NOT_FOUND` before apply | —                        |
| BE-F8 | `move` with named `from` + named `path` parent                    | both rewritten                            | works                    |
| BE-P1 | omitted `fieldPermissions` + `add /-`                             | array initialized + append                | still works (regression) |
| BE-P2 | singleton `fieldPermissions` object normalized, then name replace | index `0`                                 | still works (regression) |
| BE-S1 | path `/__proto__/x`                                               | rejected                                  | —                        |

### 5.3 Integration (optional but recommended)

Against int-test org harness (or recreate):

- Flow `CirraTest_LargeFlow_Patch`: BE-F1 style patch via MCP `metadata_update`
- Permission Set `CirraTest_PatchHarness`: omitted-array + name replace regression
- Layout `Account-CirraTest PatchHarness Layout`: numeric nested add regression

---

## 6. Acceptance criteria

- [ ] BE-F1…BE-F8 unit tests green
- [ ] Existing singleton / omitted-array / prototype tests still green
- [ ] Live MCP: `add /decisions/{Name}/rules/-` on a Draft Flow succeeds without full-array replace
- [ ] Live MCP: failing unknown name returns `NAME_PATH_NOT_FOUND` (or equivalent), not `OPERATION_PATH_CANNOT_ADD` with unresolved name in `path`
- [ ] No change required in skills for correctness; optional doc cleanup after ship

---

## 7. Workarounds until deploy

1. Fully numeric nested paths after `metadata_read` (`/decisions/2/rules/-`).
2. Or `replace` the entire nested collection under the named parent.
3. Top-level `/-` and named `replace`/`remove` remain safe.

---

## 8. Rollout

1. Implement + unit tests in `cloud-app`.
2. Deploy MCP.
3. Re-run live harness cases above.
4. Optionally update MCP tool text / `sf-flow` skill to drop the nested-add workaround (skills patch version bump only if skill files change).
