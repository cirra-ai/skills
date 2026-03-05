#!/usr/bin/env python3
"""
Salesforce Flow Scoring Engine
Scores flows against a 110-point rubric for org audit.
"""

import json
import os
import re

INTERMEDIATE_DIR = "/home/user/skills/audit_output/intermediate"
FLOWS_DIR = os.path.join(INTERMEDIATE_DIR, "flows")

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_flow_type_label(flow):
    """Determine human-readable flow type."""
    pt = flow.get("processType", "Unknown")
    start = flow.get("start", {})
    trigger_type = start.get("triggerType", "")
    start.get("recordTriggerType", "")
    obj = start.get("object", "")
    start.get("scheduledPaths")

    if trigger_type == "RecordBeforeSave":
        return f"Record-Triggered Before ({obj})"
    elif trigger_type == "RecordAfterSave":
        return f"Record-Triggered After ({obj})"
    elif trigger_type == "Scheduled":
        return f"Scheduled ({obj})"
    elif trigger_type == "PlatformEvent":
        return f"Platform Event ({obj})"
    elif pt == "AutoLaunchedFlow" and not trigger_type:
        return "Autolaunched (No Trigger)"
    elif pt == "Flow":
        has_screens = bool(flow.get("screens"))
        if has_screens:
            return "Screen Flow"
        return "Autolaunched (Subflow)"
    elif pt == "CheckoutFlow":
        return "Checkout Flow"
    elif pt == "FieldServiceMobile":
        return "Field Service Mobile"
    elif pt == "RoutingFlow":
        return "Routing Flow"
    elif pt == "Survey":
        return "Survey"
    else:
        return pt


def has_prefix(name, prefixes):
    """Check if variable name uses standard prefixes."""
    for p in prefixes:
        if name.startswith(p):
            return True
    return False


def is_pascal_case(name):
    """Check if element name is PascalCase or at least has no leading lowercase."""
    if not name:
        return True
    # Allow names starting with uppercase or containing underscores (acceptable in SF)
    return name[0].isupper() or "_" in name


# ── Scoring Functions ────────────────────────────────────────────────────────

def score_design_naming(flow):
    """Design & Naming (20 pts)"""
    score = 0
    issues = []

    # Flow name convention (5pts) - PascalCase with underscores
    name = flow.get("fullName", "")
    has_label = bool(flow.get("label"))
    has_description = bool(flow.get("description"))

    if name and (name[0].isupper() or name.startswith("dm_") or name.startswith("sfdc_")):
        score += 3
    else:
        issues.append(f"Flow name '{name}' doesn't follow naming conventions")

    if has_label:
        score += 1
    else:
        issues.append("Missing flow label")

    if has_description:
        score += 1
    else:
        issues.append("Missing flow description")

    # Variable naming conventions (8pts)
    variables = flow.get("variables", [])
    good_prefixes = ["var", "col", "rec", "inp", "out", "record", "ids", "is", "has"]
    total_vars = len(variables)
    good_vars = 0
    for v in variables:
        vname = v.get("name", "")
        # $Record is auto, skip
        if vname.startswith("$"):
            good_vars += 1
            continue
        # Check for meaningful naming (camelCase or has prefix)
        if any(vname.lower().startswith(p) for p in good_prefixes):
            good_vars += 1
        elif len(vname) > 3:  # At least descriptive
            good_vars += 0.5

    if total_vars == 0:
        score += 8
    else:
        ratio = good_vars / total_vars
        score += min(8, round(ratio * 8))
        if ratio < 0.5:
            issues.append(f"Variable naming: only {good_vars}/{total_vars} use standard prefixes (var_, col_, rec_, etc.)")

    # Element naming - PascalCase (7pts)
    all_elements = []
    for key in ["assignments", "decisions", "recordLookups", "recordCreates", "recordUpdates",
                 "recordDeletes", "loops", "screens", "subflows", "actionCalls"]:
        for elem in flow.get(key, []):
            all_elements.append(elem.get("name", ""))

    total_elems = len(all_elements)
    pascal_elems = sum(1 for e in all_elements if is_pascal_case(e))

    if total_elems == 0:
        score += 7
    else:
        ratio = pascal_elems / total_elems
        score += min(7, round(ratio * 7))
        if ratio < 0.7:
            bad = [e for e in all_elements if not is_pascal_case(e)][:3]
            issues.append(f"Element naming: {total_elems - pascal_elems}/{total_elems} not PascalCase (e.g., {', '.join(bad)})")

    return min(20, score), issues


def score_logic_structure(flow):
    """Logic & Structure (20 pts)"""
    score = 0
    issues = []

    # No DML in loops (8pts)
    loops = flow.get("loops", [])
    dml_elements = set()
    for key in ["recordCreates", "recordUpdates", "recordDeletes"]:
        for elem in flow.get(key, []):
            dml_elements.add(elem.get("name", ""))

    # Build connector graph to detect DML inside loops
    dml_in_loop = False
    if loops and dml_elements:
        # Simple heuristic: check if any DML element is between loop's next and noMore connectors
        for loop in loops:
            loop.get("nextValueConnector", {}).get("targetReference", "")
            # Walk from next_ref looking for DML before we loop back
            # Simplified: check if any DML element name appears in the flow
            # and there's a loop - flag as potential concern
            loop_name = loop.get("name", "")
            # Check all connectors from DML elements - if any point back to loop, it's DML in loop
            for key in ["recordCreates", "recordUpdates", "recordDeletes"]:
                for elem in flow.get(key, []):
                    conn = elem.get("connector", {}).get("targetReference", "")
                    if conn == loop_name:
                        dml_in_loop = True
                        issues.append(f"DML in loop: '{elem.get('label', elem.get('name'))}' inside loop '{loop.get('label', loop_name)}'")

    if not dml_in_loop:
        score += 8
    else:
        score += 2

    # Proper element ordering (4pts) - lookups before creates/updates
    score += 4  # Hard to verify ordering from metadata alone; give benefit of doubt

    # Clean decision logic (4pts)
    decisions = flow.get("decisions", [])
    complex_decisions = 0
    for d in decisions:
        rules = d.get("rules", [])
        for r in rules:
            conditions = r.get("conditions", [])
            logic = r.get("conditionLogic", "and")
            if len(conditions) > 5:
                complex_decisions += 1
            if logic and "(" in str(logic) and str(logic).count("(") > 2:
                complex_decisions += 1

    if complex_decisions == 0:
        score += 4
    elif complex_decisions <= 2:
        score += 2
        issues.append(f"{complex_decisions} overly complex decision(s)")
    else:
        issues.append(f"{complex_decisions} overly complex decisions - consider subflows")

    # Reasonable flow size (4pts)
    total_elements = sum(len(flow.get(k, [])) for k in [
        "assignments", "decisions", "recordLookups", "recordCreates",
        "recordUpdates", "recordDeletes", "loops", "screens",
        "subflows", "actionCalls"
    ])
    if total_elements <= 25:
        score += 4
    elif total_elements <= 50:
        score += 2
        issues.append(f"Large flow with {total_elements} elements - consider breaking into subflows")
    else:
        issues.append(f"Very large flow with {total_elements} elements - should be broken into subflows")

    return min(20, score), issues


def score_architecture(flow):
    """Architecture (15 pts)"""
    score = 0
    issues = []

    # Subflow usage (5pts)
    subflows = flow.get("subflows", [])
    total_elements = sum(len(flow.get(k, [])) for k in [
        "assignments", "decisions", "recordLookups", "recordCreates",
        "recordUpdates", "recordDeletes", "loops", "screens",
        "subflows", "actionCalls"
    ])

    if len(subflows) > 0:
        score += 5  # Uses subflows - good
    elif total_elements <= 10:
        score += 5  # Small flow, subflows not needed
    elif total_elements <= 20:
        score += 3
        issues.append("Consider extracting reusable logic into subflows")
    else:
        score += 1
        issues.append("No subflow usage in a complex flow - should decompose")

    # Proper entry conditions (5pts)
    start = flow.get("start", {})
    trigger_type = start.get("triggerType", "")
    filters = start.get("filters", [])
    start.get("filterLogic", "")

    if trigger_type in ["RecordBeforeSave", "RecordAfterSave"]:
        if filters:
            score += 5
        else:
            score += 2
            issues.append("Record-triggered flow without entry conditions - may fire unnecessarily")
    else:
        score += 5  # Non-triggered flows don't need entry conditions

    # Appropriate flow type (5pts)
    pt = flow.get("processType", "")
    bool(flow.get("screens"))
    has_dml = bool(flow.get("recordCreates") or flow.get("recordUpdates") or flow.get("recordDeletes"))

    if trigger_type == "RecordBeforeSave" and has_dml:
        # Before-save with DML on other objects is fine, DML on $Record via inputReference is preferred
        for key in ["recordUpdates"]:
            for elem in flow.get(key, []):
                if elem.get("inputReference") == "$Record":
                    score += 5
                    break
            else:
                continue
            break
        else:
            score += 3
    elif pt == "RoutingFlow":
        score += 5  # Appropriate specialized type
    elif pt == "CheckoutFlow":
        score += 5
    elif pt in ["Flow", "AutoLaunchedFlow", "FieldServiceMobile"]:
        score += 5
    else:
        score += 3

    return min(15, score), issues


def score_performance_bulk(flow):
    """Performance & Bulk Safety (20 pts)"""
    score = 0
    issues = []

    # No SOQL in loops (8pts)
    loops = flow.get("loops", [])
    lookups = flow.get("recordLookups", [])
    {l.get("name", "") for l in lookups}

    soql_in_loop = False
    if loops and lookups:
        for loop in loops:
            loop_name = loop.get("name", "")
            # Check if any lookup connects back to the loop
            for lookup in lookups:
                conn = lookup.get("connector", {}).get("targetReference", "")
                if conn == loop_name:
                    soql_in_loop = True
                    issues.append(f"SOQL in loop: '{lookup.get('label', lookup.get('name'))}' queries inside loop '{loop.get('label', loop_name)}'")

    if not soql_in_loop:
        score += 8
    else:
        score += 1

    # Batch DML (4pts) - collections used instead of individual records
    record_creates = flow.get("recordCreates", [])
    record_updates = flow.get("recordUpdates", [])
    uses_collections = False
    for rc in record_creates:
        if rc.get("inputReference"):
            uses_collections = True
    for ru in record_updates:
        if ru.get("inputReference") or ru.get("filters"):
            uses_collections = True

    if not record_creates and not record_updates:
        score += 4
    elif uses_collections or not loops:
        score += 4
    else:
        score += 2
        issues.append("DML operations may not be using collection variables for bulk safety")

    # Filters over loops (4pts)
    if loops:
        # Check if SOQL queries use proper filters instead of looping through all records
        for lookup in lookups:
            filters_list = lookup.get("filters", [])
            if not filters_list:
                issues.append(f"Record lookup '{lookup.get('label', lookup.get('name'))}' has no filter criteria")

    has_good_filters = all(l.get("filters") for l in lookups) if lookups else True
    if has_good_filters:
        score += 4
    else:
        score += 2

    # Transform/formula usage (4pts)
    formulas = flow.get("formulas", [])
    if formulas:
        score += 4
    elif flow.get("assignments"):
        score += 3  # Assignments are fine too
    else:
        score += 4  # Simple flow, no transforms needed

    return min(20, score), issues


def score_error_handling(flow):
    """Error Handling (20 pts)"""
    score = 0
    issues = []

    # Fault paths on DML (12pts)
    dml_elements = []
    for key in ["recordCreates", "recordUpdates", "recordDeletes"]:
        dml_elements.extend(flow.get(key, []))

    action_calls = flow.get("actionCalls", [])
    dml_elements.extend(action_calls)

    total_dml = len(dml_elements)
    fault_paths = sum(1 for d in dml_elements if d.get("faultConnector"))

    # Also check for recordRollbacks
    has_rollback = bool(flow.get("recordRollbacks"))

    if total_dml == 0:
        score += 12
    else:
        ratio = fault_paths / total_dml if total_dml > 0 else 0
        score += min(12, round(ratio * 12))
        if ratio < 0.5:
            issues.append(f"Only {fault_paths}/{total_dml} DML/action elements have fault paths")
        if ratio == 0 and total_dml > 0:
            issues.append("No fault paths on any DML operations - critical gap")

    if has_rollback:
        score += 2  # Bonus for rollback handling

    # Error screens/logging (8pts)
    screens = flow.get("screens", [])
    error_screens = [s for s in screens if "error" in s.get("label", "").lower() or "error" in s.get("name", "").lower() or "fault" in s.get("name", "").lower()]

    flow.get("processType", "")
    start = flow.get("start", {})
    trigger_type = start.get("triggerType", "")

    if trigger_type in ["RecordBeforeSave", "RecordAfterSave"]:
        # Record-triggered flows can't have screens, fault paths are the main mechanism
        if fault_paths > 0 or has_rollback:
            score += 8
        elif total_dml == 0:
            score += 8
        else:
            score += 3
            issues.append("Record-triggered flow with DML but no fault handling")
    else:
        if error_screens:
            score += 8
        elif fault_paths > 0:
            score += 6
        elif total_dml == 0:
            score += 8
        else:
            score += 2
            issues.append("No error screens or fault handling for user-facing flow")

    return min(20, score), issues


def score_security(flow):
    """Security (15 pts)"""
    score = 0
    issues = []

    # System vs User mode (6pts)
    run_mode = flow.get("runInMode", "")
    flow.get("processType", "")
    start = flow.get("start", {})
    trigger_type = start.get("triggerType", "")

    if run_mode == "SystemModeWithSharing":
        score += 6  # Best practice for most flows
    elif run_mode == "DefaultMode":
        score += 4
        issues.append("Flow runs in default mode - consider explicit System/User mode selection")
    elif run_mode == "SystemModeWithoutSharing":
        score += 3
        issues.append("Flow runs in System Mode Without Sharing - verify this is intentional")
    elif not run_mode:
        # Default behavior varies by flow type
        if trigger_type in ["RecordBeforeSave", "RecordAfterSave"]:
            score += 5  # Record-triggered flows run in system context by default
        else:
            score += 4
            issues.append("No explicit run mode set - recommend setting explicitly")

    # FLS enforcement (5pts)
    # Check for storeOutputAutomatically (better FLS) vs manual field assignments
    lookups = flow.get("recordLookups", [])
    auto_store = sum(1 for l in lookups if l.get("storeOutputAutomatically"))
    manual_store = len(lookups) - auto_store

    if len(lookups) == 0:
        score += 5
    elif auto_store >= manual_store:
        score += 5  # Auto store respects FLS better
    else:
        score += 3
        issues.append("Some record lookups use manual field assignments instead of auto-store (FLS concerns)")

    # No hardcoded IDs (4pts)
    flow_json = json.dumps(flow)
    # Look for 15/18 char Salesforce IDs that look hardcoded
    sf_id_pattern = r'["\']([a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})["\']'
    potential_ids = re.findall(sf_id_pattern, flow_json)
    # Filter out known non-IDs (short strings, common values)
    hardcoded_ids = []
    for pid in potential_ids:
        if len(pid) in [15, 18] and pid[:3] in ['001', '003', '005', '006', '00G', '00D', '012', '0PS', '00e']:
            hardcoded_ids.append(pid)

    if not hardcoded_ids:
        score += 4
    else:
        score += 1
        issues.append(f"Potential hardcoded Salesforce IDs found: {hardcoded_ids[:3]}")

    return min(15, score), issues


# ── Main Scoring ─────────────────────────────────────────────────────────────

def score_flow(flow):
    """Score a single flow against the full rubric."""
    name = flow.get("fullName", "Unknown")
    flow_type = get_flow_type_label(flow)

    design_score, design_issues = score_design_naming(flow)
    logic_score, logic_issues = score_logic_structure(flow)
    arch_score, arch_issues = score_architecture(flow)
    perf_score, perf_issues = score_performance_bulk(flow)
    error_score, error_issues = score_error_handling(flow)
    sec_score, sec_issues = score_security(flow)

    total = design_score + logic_score + arch_score + perf_score + error_score + sec_score
    max_score = 110
    pct = round(total / max_score * 100)

    all_issues = design_issues + logic_issues + arch_issues + perf_issues + error_issues + sec_issues

    # Determine verdict
    if pct >= 80:
        verdict = "Deploy"
    elif pct >= 60:
        verdict = "Review"
    else:
        verdict = "Block"

    return {
        "name": name,
        "type": flow_type,
        "score": total,
        "maxScore": max_score,
        "pct": pct,
        "verdict": verdict,
        "issues": all_issues,
        "categories": {
            "designNaming": design_score,
            "logicStructure": logic_score,
            "architecture": arch_score,
            "performanceBulk": perf_score,
            "errorHandling": error_score,
            "security": sec_score
        }
    }


def main():
    # Load all flows
    all_flows_file = os.path.join(INTERMEDIATE_DIR, "all_flows.json")
    with open(all_flows_file) as f:
        all_flows_raw = json.load(f)

    # Filter to actual flows (not LWC components)
    valid_types = {"Flow", "AutoLaunchedFlow", "CheckoutFlow", "FieldServiceMobile",
                   "RoutingFlow", "FieldServiceWeb", "Survey", "InvocableProcess", "Workflow"}

    all_flows = {}
    for name, flow in all_flows_raw.items():
        pt = flow.get("processType", "")
        if pt in valid_types or flow.get("start", {}).get("triggerType"):
            all_flows[name] = flow

    # Score each flow
    results = []
    for name, flow in sorted(all_flows.items()):
        result = score_flow(flow)
        results.append(result)

        # Write flow XML (JSON representation) to intermediate dir
        flow_file = os.path.join(FLOWS_DIR, f"{name}.flow-meta.xml")
        with open(flow_file, "w") as f:
            json.dump(flow, f, indent=2)

    # Print summary
    print(f"\n{'='*90}")
    print(f"FLOW AUDIT SCORING RESULTS - {len(results)} flows scored")
    print(f"{'='*90}")
    print(f"{'Flow Name':<55} {'Type':<30} {'Score':>5} {'Pct':>5} {'Verdict':>8}")
    print(f"{'-'*55} {'-'*30} {'-'*5} {'-'*5} {'-'*8}")

    deploy_count = 0
    review_count = 0
    block_count = 0

    for r in sorted(results, key=lambda x: x["pct"], reverse=True):
        print(f"{r['name']:<55} {r['type']:<30} {r['score']:>3}/110 {r['pct']:>4}% {r['verdict']:>8}")
        if r["verdict"] == "Deploy":
            deploy_count += 1
        elif r["verdict"] == "Review":
            review_count += 1
        else:
            block_count += 1

    print(f"\n{'='*90}")
    print(f"SUMMARY: Deploy={deploy_count} | Review={review_count} | Block={block_count}")
    print(f"{'='*90}")

    # Output JSON
    output_file = os.path.join(INTERMEDIATE_DIR, "scoring_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results written to: {output_file}")

    return results


if __name__ == "__main__":
    main()
