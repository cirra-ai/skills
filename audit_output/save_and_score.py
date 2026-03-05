import json
import os
import re
import glob

APEX_DIR = "/home/user/skills/audit_output/intermediate/apex"
MANIFEST = "/home/user/skills/audit_output/class_manifest.json"

# Build ApiVersion lookup from manifest
with open(MANIFEST) as f:
    manifest = json.load(f)
api_lookup = {c["Name"]: c["ApiVersion"] for c in manifest}

def score_class(name, body, api_version):
    scores = {}
    issues = []
    body_lower = body.lower()
    lines = body.split('\n')
    line_count = len(lines)

    is_test = bool(re.search(r'@istest|testmethod', body_lower))
    is_interface = bool(re.search(r'^\s*(public|global|private)?\s+interface\s+', body, re.MULTILINE | re.IGNORECASE))
    bool(re.search(r'^\s*(public|global|private)?\s+abstract\s+class\s+', body, re.MULTILINE | re.IGNORECASE))
    line_count < 50 and body_lower.count('@auraenabled') >= 2 and 'soql' not in body_lower and 'select ' not in body_lower
    is_exception = bool(re.search(r'class\s+\w+\s+extends\s+exception', body_lower))
    is_enum = bool(re.search(r'^\s*(public|global|private)?\s+enum\s+', body, re.MULTILINE | re.IGNORECASE))
    is_trivial = is_interface or is_exception or is_enum or (line_count < 20)

    # 1. BULKIFICATION (25 pts)
    bulk_score = 25
    loop_pattern = re.compile(r'\b(for|while)\s*\(', re.IGNORECASE)
    soql_pattern = re.compile(r'\[\s*select\s+', re.IGNORECASE)
    dml_pattern = re.compile(r'\b(insert|update|delete|upsert|undelete)\s+', re.IGNORECASE)
    db_dml = re.compile(r'\bdatabase\.(insert|update|delete|upsert)', re.IGNORECASE)

    soql_in_loop = False
    dml_in_loop = False
    loop_depth = 0
    for line in lines:
        stripped = line.strip()
        if loop_pattern.search(stripped):
            loop_depth += 1
        if stripped.count('{') < stripped.count('}'):
            loop_depth = max(0, loop_depth - 1)
        if loop_depth > 0:
            if soql_pattern.search(stripped):
                soql_in_loop = True
            if dml_pattern.search(stripped) or db_dml.search(stripped):
                dml_in_loop = True

    if soql_in_loop and not is_test:
        bulk_score -= 15
        issues.append("SOQL inside loop")
    if dml_in_loop and not is_test:
        bulk_score -= 10
        issues.append("DML inside loop")

    soql_count = len(soql_pattern.findall(body))
    if soql_count > 10 and not is_test:
        bulk_score -= 3
        issues.append(f"High SOQL count ({soql_count})")

    scores["bulkification"] = max(0, bulk_score)

    # 2. SECURITY (25 pts)
    sec_score = 25
    has_sharing = bool(re.search(r'with sharing', body_lower))
    has_without_sharing = bool(re.search(r'without sharing', body_lower))
    has_inherited_sharing = bool(re.search(r'inherited sharing', body_lower))

    if not is_test and not is_interface and not is_exception and not is_enum:
        if not has_sharing and not has_without_sharing and not has_inherited_sharing:
            sec_score -= 8
            issues.append("No sharing declaration")
        elif has_without_sharing:
            sec_score -= 3
            issues.append("Uses without sharing")

    has_security_enforced = bool(re.search(r'with\s+security_enforced', body_lower))
    has_user_mode = bool(re.search(r'user_mode', body_lower))
    has_is_accessible = bool(re.search(r'isaccessible|iscreatable|isupdateable|isdeletable', body_lower))
    has_strip_inaccessible = bool(re.search(r'stripinaccessible|security\.stripinaccessible', body_lower))

    has_soql = bool(soql_pattern.search(body))
    has_dml = bool(dml_pattern.search(body)) or bool(db_dml.search(body))

    if has_soql and not is_test and not is_trivial:
        if not (has_security_enforced or has_user_mode or has_is_accessible or has_strip_inaccessible):
            sec_score -= 7
            issues.append("No CRUD/FLS enforcement")

    has_dynamic_soql = bool(re.search(r'database\.query\s*\(', body_lower))
    has_escape = bool(re.search(r'escapesinglequotes', body_lower))
    if has_dynamic_soql and not has_escape and not is_test:
        sec_score -= 5
        issues.append("Dynamic SOQL without escapeSingleQuotes")

    string_concat_soql = bool(re.search(r"'\s*\+\s*\w+.*\+\s*'.*select|select.*'\s*\+\s*\w+", body_lower))
    if string_concat_soql and not has_escape and not is_test:
        sec_score -= 5
        issues.append("Possible SOQL injection via string concatenation")

    scores["security"] = max(0, sec_score)

    # 3. TESTING (25 pts)
    test_score = 25
    if is_test:
        has_assert = bool(re.search(r'system\.assert|assert\.|system\.assertequals|system\.assertnotequals', body_lower))
        assert_count = len(re.findall(r'system\.assert|assert\.\w+|system\.assertequals|system\.assertnotequals', body_lower))
        has_see_all_data = bool(re.search(r'seealldata\s*=\s*true', body_lower))
        has_test_setup = bool(re.search(r'@testsetup', body_lower))
        has_start_stop = bool(re.search(r'test\.starttest|test\.stoptest', body_lower))

        if not has_assert:
            test_score -= 15
            issues.append("Test class without assertions")
        elif assert_count < 3:
            test_score -= 5
            issues.append(f"Low assertion count ({assert_count})")

        if has_see_all_data:
            test_score -= 8
            issues.append("Uses SeeAllData=true")

        if not has_test_setup and line_count > 50:
            test_score -= 3
            issues.append("No @TestSetup method")

        if not has_start_stop and line_count > 30:
            test_score -= 2
            issues.append("No Test.startTest/stopTest")
    else:
        test_score = 20  # Non-test classes get baseline
        if is_trivial:
            test_score = 25

    scores["testing"] = max(0, test_score)

    # 4. ARCHITECTURE (20 pts)
    arch_score = 20
    has_aura_enabled = bool(re.search(r'@auraenabled', body_lower))
    method_count = len(re.findall(r'(public|private|protected|global)\s+(static\s+)?\w+\s+\w+\s*\(', body))

    if has_aura_enabled and has_soql and has_dml and not is_test:
        if method_count > 5 and line_count > 200:
            arch_score -= 8
            issues.append("Mixed concerns: controller with direct SOQL+DML")
        elif method_count > 2:
            arch_score -= 4
            issues.append("Controller with direct data access")

    if method_count > 20:
        arch_score -= 5
        issues.append(f"Too many methods ({method_count})")

    if line_count > 500 and not is_test:
        arch_score -= 3
        issues.append(f"Large class ({line_count} lines)")
    if line_count > 1000 and not is_test:
        arch_score -= 4
        issues.append(f"Very large class ({line_count} lines)")

    scores["architecture"] = max(0, arch_score)

    # 5. CLEAN CODE (20 pts)
    clean_score = 20
    debug_count = len(re.findall(r'system\.debug', body_lower))
    if debug_count > 10:
        clean_score -= 5
        issues.append(f"Excessive System.debug ({debug_count})")
    elif debug_count > 5:
        clean_score -= 2
        issues.append(f"Multiple System.debug ({debug_count})")

    commented_lines = sum(1 for l in lines if l.strip().startswith('//'))
    if line_count > 20 and commented_lines / max(line_count, 1) > 0.3:
        clean_score -= 5
        issues.append("High ratio of commented-out code")

    if line_count > 800 and not is_test:
        clean_score -= 3

    # Check for magic numbers/hardcoded IDs
    hardcoded_ids = re.findall(r"'[a-zA-Z0-9]{15,18}'", body)
    sf_ids = [h for h in hardcoded_ids if re.match(r"'[a-zA-Z0-9]{15}'|'[a-zA-Z0-9]{18}'", h) and re.match(r"'[0-9][0-9a-zA-Z]", h)]
    if sf_ids and not is_test:
        clean_score -= 3
        issues.append("Hardcoded Salesforce IDs")

    scores["cleanCode"] = max(0, clean_score)

    # 6. ERROR HANDLING (15 pts)
    err_score = 15
    has_try_catch = bool(re.search(r'\btry\s*\{', body_lower))
    has_aura_handled = bool(re.search(r'aurahandledexception', body_lower))
    empty_catch = bool(re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', body, re.DOTALL))
    catch_debug_only = bool(re.search(r'catch\s*\([^)]*\)\s*\{\s*system\.debug\([^)]*\);\s*\}', body_lower, re.DOTALL))

    if has_aura_enabled and not has_try_catch and not is_test and not is_trivial and line_count > 10:
        err_score -= 7
        issues.append("AuraEnabled methods without try-catch")

    if empty_catch:
        err_score -= 5
        issues.append("Empty catch block")
    elif catch_debug_only and not is_test:
        err_score -= 3
        issues.append("Catch block only logs debug")

    if has_aura_enabled and has_try_catch and not has_aura_handled and not is_test:
        err_score -= 3
        issues.append("No AuraHandledException in controller")

    scores["errorHandling"] = max(0, err_score)

    # 7. PERFORMANCE (10 pts)
    perf_score = 10
    has_cacheable = bool(re.search(r'cacheable\s*=\s*true', body_lower))
    bool(re.search(r'static\s+map|static\s+list|if\s*\(\s*\w+\s*==\s*null\s*\)', body_lower))
    has_limits_check = bool(re.search(r'limits\.\w+', body_lower))

    if has_aura_enabled and not has_cacheable and has_soql and not has_dml and not is_test:
        perf_score -= 3
        issues.append("Read-only AuraEnabled without cacheable=true")

    if soql_count > 5 and not has_limits_check and not is_test and not is_trivial:
        perf_score -= 2
        issues.append("Multiple SOQL without Limits checking")

    scores["performance"] = max(0, perf_score)

    # 8. DOCUMENTATION (10 pts)
    doc_score = 10
    has_apexdoc = bool(re.search(r'/\*\*', body))
    apexdoc_count = len(re.findall(r'/\*\*', body))
    has_description = bool(re.search(r'@description', body_lower))
    has_param = bool(re.search(r'@param', body_lower))
    bool(re.search(r'@return', body_lower))

    if not is_trivial and line_count > 30:
        if not has_apexdoc:
            doc_score -= 5
            issues.append("No ApexDoc comments")
        elif not has_description and not has_param:
            doc_score -= 2
            issues.append("ApexDoc without @description/@param")

    if method_count > 5 and apexdoc_count < method_count / 2 and not is_test:
        doc_score -= 3
        issues.append("Many methods without ApexDoc")

    scores["documentation"] = max(0, doc_score)

    # API version check
    if api_version and api_version < 50:
        issues.append(f"Old API version ({api_version})")

    total = sum(scores.values())
    max_score = 150
    pct = round(total / max_score * 100)

    return {
        "name": name,
        "score": total,
        "maxScore": max_score,
        "pct": pct,
        "apiVersion": api_version,
        "issues": issues,
        "categories": scores
    }

# Score all .cls files
results = []
cls_files = sorted(glob.glob(os.path.join(APEX_DIR, "*.cls")))
print(f"Found {len(cls_files)} .cls files to score")

for fpath in cls_files:
    name = os.path.basename(fpath).replace('.cls', '')
    with open(fpath) as f:
        body = f.read()
    api_ver = api_lookup.get(name, 0)
    result = score_class(name, body, api_ver)
    results.append(result)

# Sort by score ascending
results.sort(key=lambda x: x["score"])

# Save
with open("/home/user/skills/audit_output/scoring_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Summary
deploy = sum(1 for r in results if r["pct"] >= 90)
review = sum(1 for r in results if 67 <= r["pct"] < 90)
block = sum(1 for r in results if r["pct"] < 67)
print(f"\nScored: {len(results)} classes")
print(f"Deploy (>=90%): {deploy}")
print(f"Review (67-89%): {review}")
print(f"Block (<67%): {block}")
print("\nLowest 5:")
for r in results[:5]:
    print(f"  {r['name']}: {r['score']}/{r['maxScore']} ({r['pct']}%) - {', '.join(r['issues'][:3])}")
print("\nHighest 5:")
for r in results[-5:]:
    print(f"  {r['name']}: {r['score']}/{r['maxScore']} ({r['pct']}%) - {', '.join(r['issues'][:2])}")
