import json
import re
import os

outdir = "/home/user/skills/audit_output/intermediate/apex"

# All class data collected from queries (name, body, apiVersion)
all_classes = json.loads(open("/home/user/skills/audit_output/all_classes.json").read())

def score_class(name, body, api_version):
    scores = {"bulkification":0,"security":0,"testing":0,"architecture":0,"cleanCode":0,"errorHandling":0,"performance":0,"documentation":0}
    issues = []
    is_test = bool(re.search(r'@[Ii]s[Tt]est', body)) or name.endswith('Test') or name.endswith('TestUtils')
    is_interface = bool(re.search(r'^\s*public\s+interface\b', body, re.MULTILINE))
    body_nospace = body.replace(' ','').replace('\n','')
    is_wrapper = 'wrapper' in name.lower() or (len(body) < 800 and body_nospace.count('{get;set;}') >= 2 and 'SELECT' not in body.upper())
    is_exception = 'extends Exception' in body and len(body) < 200
    is_abstract = 'abstract class' in body
    lines = body.split('\n')
    line_count = len(lines)
    method_count = len(re.findall(r'(public|private|global|protected)\s+(static\s+)?(override\s+)?\w+[\w<>\[\], ]*\s+\w+\s*\(', body))

    # BULKIFICATION (25)
    soql_in_loop = dml_in_loop = False
    loop_depth = 0
    for line in lines:
        s = line.strip()
        if re.search(r'\b(for|while)\s*\(', s): loop_depth += 1
        if s == '}' and loop_depth > 0: loop_depth -= 1
        if loop_depth > 0:
            if re.search(r'\[.*SELECT\s', s, re.IGNORECASE) or 'Database.query' in s: soql_in_loop = True
            if re.search(r'\b(insert|update|delete|upsert|undelete)\s+\w', s) and not s.startswith('//'): dml_in_loop = True
    if is_test or is_wrapper or is_exception or is_interface: scores["bulkification"] = 20
    elif soql_in_loop and dml_in_loop: scores["bulkification"] = 5; issues += ["SOQL and DML inside loops"]
    elif soql_in_loop: scores["bulkification"] = 10; issues += ["SOQL inside loop"]
    elif dml_in_loop: scores["bulkification"] = 10; issues += ["DML inside loop"]
    else: scores["bulkification"] = 22
    if re.search(r'List<.*>\s+\w+\s*=\s*new\s+List', body): scores["bulkification"] = min(25, scores["bulkification"]+3)

    # SECURITY (25)
    has_sharing = 'with sharing' in body
    has_wo_sharing = 'without sharing' in body
    has_sec = 'SECURITY_ENFORCED' in body or 'USER_MODE' in body
    has_bind = bool(re.search(r':\s*\w+', body) and 'SELECT' in body.upper())
    has_fls = 'isAccessible' in body or 'isCreateable' in body or 'stripInaccessible' in body
    has_esc = 'escapeSingleQuotes' in body
    dyn_soql = bool(re.search(r"Database\.query\s*\(", body))
    sec = 0
    if is_test or is_wrapper or is_exception or is_interface: sec = 18
    else:
        if has_sharing or has_wo_sharing: sec += 6
        else: issues += ["Missing sharing declaration"]
        if has_sec or has_fls: sec += 8
        elif 'SELECT' in body.upper(): issues += ["No CRUD/FLS enforcement"]
        else: sec += 5
        if has_bind or 'SELECT' not in body.upper(): sec += 5
        if has_esc: sec += 3
        elif dyn_soql and not has_esc: issues += ["Dynamic SOQL without escapeSingleQuotes"]; sec += 0
        else: sec += 2
        if has_wo_sharing: issues += ["Uses without sharing"]; sec = max(0, sec-2)
    scores["security"] = min(25, sec)

    # TESTING (25)
    if is_test:
        ts = 10
        if re.search(r'(System\.(assert|assertEquals|assertNotEquals)|Assert\.)\s*\(', body): ts += 6
        else: issues += ["No assertions in test"]
        if 'SeeAllData=true' in body: issues += ["Uses SeeAllData=true"]; ts -= 3
        if '@TestSetup' in body or '@testSetup' in body: ts += 4
        if 'Test.startTest()' in body: ts += 3
        if len(re.findall(r'(static\s+(void\s+)?test|@[Ii]s[Tt]est\s+static)', body)) > 2: ts += 2
        scores["testing"] = min(25, ts)
    else:
        scores["testing"] = 15

    # ARCHITECTURE (20)
    ar = 0
    if is_test or is_wrapper or is_exception or is_interface: ar = 14
    else:
        has_aura = '@AuraEnabled' in body
        has_soql = bool(re.search(r'\bSELECT\b', body, re.IGNORECASE))
        has_dml = bool(re.search(r'\b(insert|update|delete|upsert)\s', body))
        if has_aura and has_soql and has_dml and line_count > 50: issues += ["Controller mixes data access"]; ar += 6
        elif has_aura and has_soql: ar += 10
        else: ar += 12
        if is_abstract or 'interface' in body or 'implements' in body or 'virtual' in body: ar += 3
        if method_count > 10: issues += [f"{method_count} methods - consider splitting"]; ar -= 2
        if 'Queueable' in body or 'Batchable' in body: ar += 2
    scores["architecture"] = min(20, max(0, ar))

    # CLEAN CODE (20)
    cc = 12
    if is_wrapper or is_exception: cc = 16
    else:
        if body.count('System.debug') > 5: issues += ["Excessive System.debug"]; cc -= 2
        commented_lines = sum(1 for l in lines if l.strip().startswith('//'))
        if commented_lines > line_count * 0.15 and commented_lines > 5: issues += ["High commented-out code ratio"]; cc -= 2
        if line_count < 100 and method_count <= 3: cc += 4
        elif line_count < 200: cc += 2
        if line_count > 500: cc -= 3; issues += ["Very large class (>500 lines)"]
    scores["cleanCode"] = min(20, max(0, cc))

    # ERROR HANDLING (15)
    eh = 0
    if is_test or is_wrapper or is_exception or is_interface: eh = 10
    else:
        has_try = 'try {' in body or 'try{' in body or 'try\n' in body
        has_empty = bool(re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', body.replace('\n',' ')))
        has_aura_ex = 'AuraHandledException' in body
        if has_try:
            eh += 5
            if has_empty: issues += ["Empty catch block"]; eh -= 3
            if has_aura_ex: eh += 4
            elif re.search(r'catch\s*\(\s*Exception\s', body): eh += 2; issues += ["Only catches generic Exception"]
            else: eh += 3
        elif '@AuraEnabled' in body: issues += ["AuraEnabled without try-catch"]; eh = 3
        else: eh = 8
    scores["errorHandling"] = min(15, max(0, eh))

    # PERFORMANCE (10)
    pf = 5
    if is_test or is_wrapper or is_exception or is_interface: pf = 7
    else:
        if 'cacheable=true' in body: pf += 2
        if re.search(r'private\s+static\s+Map', body) or 'Cache.' in body: pf += 2
        if 'Limits.' in body: pf += 1
    scores["performance"] = min(10, pf)

    # DOCUMENTATION (10)
    has_class_doc = bool(re.search(r'/\*\*[\s\S]*?\*/', body[:600]))
    method_docs = body.count('@description') + body.count('@param') + body.count('@return')
    if is_wrapper or is_exception: dc = 6
    elif has_class_doc and method_docs > 2: dc = 9
    elif has_class_doc: dc = 6
    elif body.count('//') > 3: dc = 4
    else: issues += ["Missing ApexDoc"]; dc = 2
    scores["documentation"] = min(10, dc)

    if api_version and api_version < 50: issues += [f"Outdated API v{api_version}"]
    total = sum(scores.values())
    pct = round(total/150*100)
    return {"name":name,"score":total,"maxScore":150,"pct":pct,"apiVersion":api_version,"issues":issues,"categories":scores}

results = []
for cls in all_classes:
    name = cls["Name"]
    body = cls["Body"]
    api_ver = cls.get("ApiVersion", 0)
    # Write file
    fpath = os.path.join(outdir, f"{name}.cls")
    with open(fpath, 'w') as f:
        f.write(body)
    # Score
    result = score_class(name, body, api_ver)
    results.append(result)

# Sort by score ascending (worst first)
results.sort(key=lambda x: x["pct"])

with open("/home/user/skills/audit_output/scoring_results.json", 'w') as f:
    json.dump(results, f, indent=2)

# Summary stats
deploy = sum(1 for r in results if r["pct"] >= 60)  # >= 90/150
review = sum(1 for r in results if 45 <= r["pct"] < 60)
block = sum(1 for r in results if r["pct"] < 45)
print(f"Scored {len(results)} classes")
print(f"Deploy (>=90): {sum(1 for r in results if r['score']>=90)}")
print(f"Review (67-89): {sum(1 for r in results if 67<=r['score']<90)}")
print(f"Block (<67): {sum(1 for r in results if r['score']<67)}")
