#!/usr/bin/env python3
"""Full Salesforce Org Audit - Score Apex classes from collected data."""
import json
import re
import os

def score_class(name, body, api_version):
    """Score an Apex class against the 150-point rubric."""
    scores = {
        "bulkification": 0, "security": 0, "testing": 0, "architecture": 0,
        "cleanCode": 0, "errorHandling": 0, "performance": 0, "documentation": 0
    }
    issues = []
    is_test = bool(re.search(r'@[Ii]s[Tt]est', body)) or name.endswith('Test') or name.endswith('TestUtils')
    is_interface = bool(re.search(r'\binterface\s+\w+', body))
    is_wrapper = 'wrapper' in name.lower() or (len(body) < 500 and '{get;set;}' in body.replace(' ', '').replace('\n',''))
    is_exception = 'extends Exception' in body or 'Exception' in name
    lines = body.split('\n')
    line_count = len(lines)

    # BULKIFICATION (25pts)
    soql_in_loop = dml_in_loop = False
    loop_depth = 0
    for line in lines:
        stripped = line.strip()
        if re.search(r'\b(for|while)\s*\(', stripped):
            loop_depth += 1
        if stripped == '}' and loop_depth > 0:
            loop_depth -= 1
        if loop_depth > 0:
            if re.search(r'\[.*SELECT\s', stripped, re.IGNORECASE) or 'Database.query' in stripped:
                soql_in_loop = True
            if re.search(r'\b(insert|update|delete|upsert|undelete)\s+\w', stripped) and not stripped.startswith('//'):
                dml_in_loop = True
    if is_test or is_wrapper or is_exception or is_interface:
        scores["bulkification"] = 20
    elif soql_in_loop and dml_in_loop:
        scores["bulkification"] = 5
        issues.append("SOQL and DML inside loops")
    elif soql_in_loop:
        scores["bulkification"] = 10
        issues.append("SOQL inside loop")
    elif dml_in_loop:
        scores["bulkification"] = 10
        issues.append("DML inside loop")
    else:
        scores["bulkification"] = 22
    if re.search(r'List<.*>\s+\w+\s*=\s*new\s+List', body):
        scores["bulkification"] = min(25, scores["bulkification"] + 3)

    # SECURITY (25pts)
    has_with_sharing = 'with sharing' in body
    has_without_sharing = 'without sharing' in body
    has_security_enforced = 'SECURITY_ENFORCED' in body or 'USER_MODE' in body
    has_bind_vars = bool(re.search(r':\s*\w+', body) and 'SELECT' in body.upper())
    has_strip = 'stripInaccessible' in body
    has_escape = 'escapeSingleQuotes' in body
    has_dynamic_soql = bool(re.search(r"Database\.query\s*\(", body)) and not has_escape

    sec_score = 0
    if is_test or is_wrapper or is_exception or is_interface:
        sec_score = 18
    else:
        if has_with_sharing or has_without_sharing:
            sec_score += 6
        else:
            issues.append("Missing sharing declaration")
        if has_security_enforced or has_strip:
            sec_score += 8
        elif 'SELECT' in body.upper():
            issues.append("No CRUD/FLS enforcement")
        else:
            sec_score += 5
        if has_bind_vars or 'SELECT' not in body.upper():
            sec_score += 5
        if has_dynamic_soql:
            issues.append("Dynamic SOQL without escapeSingleQuotes")
        else:
            sec_score += 3
        if has_without_sharing and not is_test:
            issues.append("Uses 'without sharing'")
            sec_score = max(0, sec_score - 2)
    scores["security"] = min(25, sec_score)

    # TESTING (25pts)
    if is_test:
        test_score = 10
        has_assert = bool(re.search(r'(System\.(assert|assertEquals)|Assert\.\w+)\s*\(', body))
        if has_assert: test_score += 6
        else: issues.append("Test has no assertions")
        if 'SeeAllData=true' in body:
            issues.append("Uses SeeAllData=true")
            test_score -= 3
        if '@TestSetup' in body or '@testSetup' in body: test_score += 4
        if 'Test.startTest()' in body: test_score += 3
        test_methods = len(re.findall(r'@[Ii]s[Tt]est|testMethod', body))
        if test_methods > 2: test_score += 2
        scores["testing"] = min(25, test_score)
    else:
        scores["testing"] = 15

    # ARCHITECTURE (20pts)
    if is_test or is_wrapper or is_exception or is_interface:
        scores["architecture"] = 14
    else:
        arch_score = 0
        has_aura = '@AuraEnabled' in body
        has_soql = bool(re.search(r'\bSELECT\b', body, re.IGNORECASE))
        has_dml = bool(re.search(r'\b(insert|update|delete|upsert)\s', body))
        if has_aura and has_soql and has_dml and line_count > 50:
            issues.append("Controller mixes presentation and data access")
            arch_score += 6
        elif has_aura and has_soql:
            arch_score += 10
        else:
            arch_score += 12
        method_count = len(re.findall(r'(public|private|global|protected)\s+(static\s+)?\w+\s+\w+\s*\(', body))
        if method_count > 10:
            issues.append(f"Class has {method_count} methods")
            arch_score = max(arch_score - 2, 0)
        if 'interface' in body or 'implements' in body or 'virtual' in body:
            arch_score += 3
        if 'TriggerHandler' in body or 'Trigger.' in body:
            arch_score += 2
        scores["architecture"] = min(20, arch_score)

    # CLEAN CODE (20pts)
    if is_wrapper or is_exception:
        scores["cleanCode"] = 16
    else:
        cc_score = 12
        long_methods = 0
        method_lines = 0
        in_method = False
        brace_count = 0
        for line in lines:
            if re.search(r'(public|private|global|protected)\s+(static\s+)?\w+\s+\w+\s*\(', line):
                in_method = True
                method_lines = 0
                brace_count = 0
            if in_method:
                method_lines += 1
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and method_lines > 1:
                    if method_lines > 50: long_methods += 1
                    in_method = False
        if long_methods > 0:
            issues.append(f"{long_methods} method(s) exceed 50 lines")
            cc_score -= 3
        if body.count('System.debug') > 5:
            issues.append(f"Excessive System.debug ({body.count('System.debug')})")
            cc_score -= 2
        if line_count < 100: cc_score += 4
        elif line_count < 200: cc_score += 2
        scores["cleanCode"] = min(20, max(0, cc_score))

    # ERROR HANDLING (15pts)
    if is_test or is_wrapper or is_exception or is_interface:
        scores["errorHandling"] = 10
    else:
        eh_score = 0
        has_try = 'try {' in body or 'try{' in body
        has_empty_catch = bool(re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', body.replace('\n', ' ')))
        has_specific = bool(re.search(r'catch\s*\(\s*(DmlException|QueryException|AuraHandledException)', body))
        has_aura_handled = 'AuraHandledException' in body
        if has_try:
            eh_score += 5
            if has_empty_catch:
                issues.append("Empty catch block")
                eh_score -= 3
            if has_specific: eh_score += 4
            if has_aura_handled: eh_score += 3
        elif '@AuraEnabled' in body:
            issues.append("AuraEnabled methods without try-catch")
            eh_score += 2
        else:
            eh_score += 7
        scores["errorHandling"] = min(15, max(0, eh_score))

    # PERFORMANCE (10pts)
    if is_test or is_wrapper or is_exception or is_interface:
        scores["performance"] = 7
    else:
        perf_score = 5
        if 'cacheable=true' in body: perf_score += 2
        if bool(re.search(r'(private\s+static\s+Map|Cache\.)', body)): perf_score += 2
        if 'Limits.' in body: perf_score += 1
        scores["performance"] = min(10, perf_score)

    # DOCUMENTATION (10pts)
    has_class_doc = bool(re.search(r'/\*\*[\s\S]*?\*/', body[:500]))
    has_method_doc = body.count('@description') + body.count('@param') + body.count('@return')
    if is_wrapper or is_exception:
        scores["documentation"] = 6
    elif has_class_doc and has_method_doc > 2:
        scores["documentation"] = 9
    elif has_class_doc:
        scores["documentation"] = 6
    elif body.count('//') > 2:
        scores["documentation"] = 4
    else:
        issues.append("Missing ApexDoc documentation")
        scores["documentation"] = 2

    if api_version < 50:
        issues.append(f"Outdated API version {api_version}")

    total = sum(scores.values())
    pct = round(total / 150 * 100)
    return {"name": name, "score": total, "maxScore": 150, "pct": pct,
            "apiVersion": api_version, "issues": issues[:8], "categories": scores}


def score_class_metadata_only(name, api_version, length):
    """Score a class based only on metadata when body isn't available."""
    scores = {"bulkification": 18, "security": 15, "testing": 15, "architecture": 12,
              "cleanCode": 14, "errorHandling": 8, "performance": 6, "documentation": 4}
    issues = []
    is_test = name.endswith('Test') or name.endswith('TestUtils')

    if is_test:
        scores["testing"] = 18
        scores["bulkification"] = 20

    if api_version < 50:
        issues.append(f"Outdated API version {api_version}")
        for k in scores: scores[k] = max(0, scores[k] - 1)
    elif api_version >= 60:
        scores["performance"] += 1

    if length > 50000:
        issues.append("Very large class - may violate SRP")
        scores["architecture"] = max(0, scores["architecture"] - 3)
    elif length > 20000:
        issues.append("Large class - review for SRP")
        scores["architecture"] = max(0, scores["architecture"] - 1)

    total = sum(scores.values())
    pct = round(total / 150 * 100)
    return {"name": name, "score": total, "maxScore": 150, "pct": pct,
            "apiVersion": api_version, "issues": issues, "categories": scores,
            "metadataOnly": True}


# Load collected class bodies
with open('/home/user/skills/audit_output/all_classes.json') as f:
    classes_with_bodies = json.load(f)

# Score classes with bodies
results = []
for cls in classes_with_bodies:
    name = cls['Name']
    body = cls.get('Body', '')
    api = cls.get('ApiVersion', 55)
    if body:
        # Write intermediate file
        os.makedirs('/home/user/skills/audit_output/intermediate/apex', exist_ok=True)
        with open(f'/home/user/skills/audit_output/intermediate/apex/{name}.cls', 'w') as f:
            f.write(body)
        result = score_class(name, body, api)
        results.append(result)

# Save scored results
with open('/home/user/skills/audit_output/apex_scores.json', 'w') as f:
    json.dump(results, f, indent=2)

# Summary stats
total_scored = len(results)
avg_score = sum(r['score'] for r in results) / max(total_scored, 1)
avg_pct = sum(r['pct'] for r in results) / max(total_scored, 1)
below_threshold = len([r for r in results if r['pct'] < 60])

print(f"Scored {total_scored} Apex classes with body data")
print(f"Average score: {avg_score:.1f}/150 ({avg_pct:.1f}%)")
print(f"Below 60% threshold: {below_threshold}")
print("Intermediate files written to audit_output/intermediate/apex/")

# Top issues
all_issues = {}
for r in results:
    for issue in r['issues']:
        all_issues[issue] = all_issues.get(issue, 0) + 1
print("\nTop issues:")
for issue, count in sorted(all_issues.items(), key=lambda x: -x[1])[:10]:
    print(f"  {count}x {issue}")
