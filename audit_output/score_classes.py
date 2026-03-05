import re

# All classes collected from the org queries - bodies and metadata
classes = []

# I'll define the scoring functions
def score_class(name, body, api_version):
    """Score an Apex class against the rubric"""
    scores = {
        "bulkification": 0,
        "security": 0,
        "testing": 0,
        "architecture": 0,
        "cleanCode": 0,
        "errorHandling": 0,
        "performance": 0,
        "documentation": 0
    }
    issues = []
    is_test = bool(re.search(r'@[Ii]s[Tt]est', body)) or name.endswith('Test') or name.endswith('TestUtils')
    is_interface = bool(re.search(r'\binterface\b', body))
    is_wrapper = 'wrapper' in name.lower() or (len(body) < 500 and '{get;set;}' in body.replace(' ', '').replace('\n',''))
    is_exception = 'extends Exception' in body
    is_abstract = 'abstract class' in body
    lines = body.split('\n')
    line_count = len(lines)

    # ========== BULKIFICATION (25pts) ==========
    soql_in_loop = False
    dml_in_loop = False
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
        scores["bulkification"] = 20  # N/A mostly
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

    # Check for collect-first patterns
    if re.search(r'List<.*>\s+\w+\s*=\s*new\s+List', body):
        scores["bulkification"] = min(25, scores["bulkification"] + 3)

    # ========== SECURITY (25pts) ==========
    has_with_sharing = 'with sharing' in body
    has_without_sharing = 'without sharing' in body
    has_security_enforced = 'SECURITY_ENFORCED' in body or 'USER_MODE' in body
    has_bind_vars = bool(re.search(r':\s*\w+', body) and 'SELECT' in body.upper())
    has_strip_inaccessible = 'stripInaccessible' in body
    has_is_accessible = 'isAccessible' in body or 'isCreateable' in body or 'isUpdateable' in body
    has_escape = 'escapeSingleQuotes' in body
    has_dynamic_soql_unsafe = bool(re.search(r"Database\.query\s*\(", body)) and not has_escape
    has_sosl_injection = bool(re.search(r"Search\.query\s*\(", body)) and not has_escape

    sec_score = 0
    if is_test or is_wrapper or is_exception or is_interface:
        sec_score = 18
    else:
        if has_with_sharing or has_without_sharing:
            sec_score += 6
        else:
            issues.append("Missing sharing declaration")
        if has_security_enforced or has_strip_inaccessible or has_is_accessible:
            sec_score += 8
        elif 'SELECT' in body.upper():
            issues.append("No CRUD/FLS enforcement on queries")
        else:
            sec_score += 5  # no queries = less concern
        if has_bind_vars or 'SELECT' not in body.upper():
            sec_score += 5
        if has_escape:
            sec_score += 3
        elif has_dynamic_soql_unsafe:
            issues.append("Dynamic SOQL without escapeSingleQuotes - possible injection")
        elif has_sosl_injection:
            issues.append("Dynamic SOSL without input sanitization")
        else:
            sec_score += 2
        if has_without_sharing and not is_test:
            issues.append("Uses 'without sharing' - verify intentional")
            sec_score = max(0, sec_score - 2)
    scores["security"] = min(25, sec_score)

    # ========== TESTING (25pts) ==========
    if is_test:
        test_score = 10  # base for being a test
        has_assert = bool(re.search(r'System\.(assert|assertEquals|assertNotEquals)\s*\(', body) or re.search(r'Assert\.\w+\s*\(', body))
        has_see_all = 'SeeAllData=true' in body
        has_test_setup = '@TestSetup' in body or '@testSetup' in body
        has_start_stop = 'Test.startTest()' in body

        if has_assert:
            test_score += 6
        else:
            issues.append("Test has no assertions")
        if has_see_all:
            issues.append("Uses SeeAllData=true - avoid")
            test_score -= 3
        if has_test_setup:
            test_score += 4
        if has_start_stop:
            test_score += 3
        # Check for meaningful test method count
        test_methods = len(re.findall(r'@[Ii]s[Tt]est|static\s+testMethod|@Test', body))
        if test_methods > 2:
            test_score += 2
        scores["testing"] = min(25, test_score)
    else:
        # Non-test class: check if naming suggests a test exists
        scores["testing"] = 15  # neutral - can't determine coverage from code alone

    # ========== ARCHITECTURE (20pts) ==========
    arch_score = 0
    if is_test or is_wrapper or is_exception or is_interface:
        arch_score = 14
    else:
        # Check for separation of concerns
        if is_abstract:
            arch_score += 5
        has_aura_enabled = '@AuraEnabled' in body
        has_soql = bool(re.search(r'\bSELECT\b', body, re.IGNORECASE))
        has_dml = bool(re.search(r'\b(insert|update|delete|upsert)\s', body))

        # Mixed concerns: controller doing data access
        if has_aura_enabled and has_soql and has_dml and line_count > 50:
            issues.append("Controller mixes presentation and data access layers")
            arch_score += 6
        elif has_aura_enabled and has_soql:
            arch_score += 10
        else:
            arch_score += 12

        # SOLID: Single responsibility
        method_count = len(re.findall(r'(public|private|global|protected)\s+(static\s+)?\w+\s+\w+\s*\(', body))
        if method_count > 10:
            issues.append(f"Class has {method_count} methods - consider splitting")
            arch_score = max(arch_score - 2, 0)

        # Check for dependency injection
        if 'interface' in body or 'implements' in body or 'virtual' in body:
            arch_score += 3

        # Trigger handler pattern
        if 'TriggerHandler' in body or 'Trigger.' in body:
            arch_score += 2

    scores["architecture"] = min(20, arch_score)

    # ========== CLEAN CODE (20pts) ==========
    cc_score = 0
    if is_wrapper or is_exception:
        cc_score = 16
    else:
        # Method length
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
                    if method_lines > 50:
                        long_methods += 1
                    in_method = False

        # Naming
        has_meaningful_names = not bool(re.search(r'\b[a-z]{1}\b\s*=', body))  # single char vars
        has_system_debug = body.count('System.debug')
        has_commented_code = body.count('//') > line_count * 0.15

        cc_score = 12
        if long_methods > 0:
            issues.append(f"{long_methods} method(s) exceed 50 lines")
            cc_score -= 3
        if not has_meaningful_names:
            cc_score -= 2
        if has_system_debug > 5:
            issues.append(f"Excessive System.debug statements ({has_system_debug})")
            cc_score -= 2
        if has_commented_code:
            issues.append("High ratio of commented-out code")
            cc_score -= 2

        # Bonus for clean patterns
        if line_count < 100 and method_count <= 3:
            cc_score += 4  # small focused class
        elif line_count < 200:
            cc_score += 2

    scores["cleanCode"] = min(20, max(0, cc_score))

    # ========== ERROR HANDLING (15pts) ==========
    eh_score = 0
    if is_test or is_wrapper or is_exception or is_interface:
        eh_score = 10
    else:
        has_try_catch = 'try {' in body or 'try{' in body
        has_empty_catch = bool(re.search(r'catch\s*\([^)]+\)\s*\{\s*\}', body.replace('\n', ' ')))
        has_specific_catch = bool(re.search(r'catch\s*\(\s*(DmlException|QueryException|AuraHandledException|CalloutException|JSONException)', body))
        has_aura_handled = 'AuraHandledException' in body
        catches_generic = bool(re.search(r'catch\s*\(\s*Exception\s', body))

        if has_try_catch:
            eh_score += 5
            if has_empty_catch:
                issues.append("Empty catch block found")
                eh_score -= 3
            if has_specific_catch:
                eh_score += 4
            elif catches_generic and has_aura_handled:
                eh_score += 3
            elif catches_generic:
                eh_score += 1
                issues.append("Only catches generic Exception")
            if has_aura_handled:
                eh_score += 3
        elif '@AuraEnabled' in body:
            issues.append("AuraEnabled methods without try-catch")
            eh_score += 2
        else:
            eh_score += 7  # simple class, no need

    scores["errorHandling"] = min(15, max(0, eh_score))

    # ========== PERFORMANCE (10pts) ==========
    perf_score = 0
    if is_test or is_wrapper or is_exception or is_interface:
        perf_score = 7
    else:
        has_cacheable = 'cacheable=true' in body
        has_caching = bool(re.search(r'(private\s+static\s+Map|Cache\.)', body))
        has_limits = 'Limits.' in body
        has_async = bool(re.search(r'(Queueable|Batchable|@future|Schedulable)', body))

        perf_score = 5  # baseline
        if has_cacheable:
            perf_score += 2
        if has_caching:
            perf_score += 2
        if has_limits:
            perf_score += 1
        if has_async:
            perf_score += 1

    scores["performance"] = min(10, perf_score)

    # ========== DOCUMENTATION (10pts) ==========
    doc_score = 0
    has_class_doc = bool(re.search(r'/\*\*[\s\S]*?\*/', body[:500]))  # ApexDoc at top
    has_method_doc = body.count('@description') + body.count('@param') + body.count('@return')
    has_inline_comments = body.count('//') > 2

    if is_wrapper or is_exception:
        doc_score = 6
    elif has_class_doc and has_method_doc > 2:
        doc_score = 9
    elif has_class_doc:
        doc_score = 6
    elif has_inline_comments:
        doc_score = 4
    else:
        issues.append("Missing ApexDoc documentation")
        doc_score = 2

    scores["documentation"] = min(10, doc_score)

    # API version check
    if api_version < 50:
        issues.append(f"Outdated API version {api_version}")

    total = sum(scores.values())
    pct = round(total / 150 * 100)

    return {
        "name": name,
        "score": total,
        "maxScore": 150,
        "pct": pct,
        "apiVersion": api_version,
        "issues": issues,
        "categories": scores
    }

# Process all classes from the JSON data files
results = []
print("Scoring engine ready")
