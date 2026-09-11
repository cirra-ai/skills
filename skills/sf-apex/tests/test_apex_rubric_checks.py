"""Tests for the testing / architecture / performance rubric checks and the
shared five-level severity scale in validate_apex.py."""

import os

from conftest import load_script

mod = load_script("skills/sf-apex/scripts/validate_apex.py")
ApexValidator = mod.ApexValidator

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _validate(tmp_path, code: str, name: str = "Tmp.cls", api_version=None) -> dict:
    path = tmp_path / name
    path.write_text(code, encoding="utf-8")
    return ApexValidator(str(path), api_version=api_version).validate()


def _issues(result, category=None, severity=None):
    out = result["issues"]
    if category:
        out = [i for i in out if i["category"] == category]
    if severity:
        out = [i for i in out if i["severity"] == severity]
    return out


def _messages(result, **kw):
    return [i["message"] for i in _issues(result, **kw)]


# ═══════════════════════════════════════════════════════════════════════════════
# Severity vocabulary
# ═══════════════════════════════════════════════════════════════════════════════


class TestSeverityScale:
    def test_order_is_code_analyzer_scale(self):
        assert mod.SEVERITY_ORDER == ["CRITICAL", "HIGH", "MODERATE", "LOW", "INFO"]

    def test_legacy_labels_normalised(self):
        assert mod.normalize_severity("WARNING") == "MODERATE"
        assert mod.normalize_severity("ERROR") == "HIGH"
        assert mod.normalize_severity("MEDIUM") == "MODERATE"
        assert mod.normalize_severity("critical") == "CRITICAL"
        assert mod.normalize_severity(None, "LOW") == "LOW"
        assert mod.normalize_severity("bogus", "INFO") == "INFO"

    def test_rank_sorts_worst_first(self):
        ranks = [mod.severity_rank(s) for s in mod.SEVERITY_ORDER]
        assert ranks == sorted(ranks)
        assert mod.severity_rank("WARNING") == mod.severity_rank("MODERATE")

    def test_every_emitted_severity_is_on_the_scale(self, tmp_path):
        code = """@IsTest
private class MessyTest {
    @IsTest
    static void noAssert() {
        Account a = new Account(Name = 'x');
        insert a;
        System.enqueueJob(new Object());
    }
    @IsTest(SeeAllData=true)
    static void legacy() {
        Id rt = '0125000000AbCdE';
        System.assert(true);
        Schema.getGlobalDescribe();
    }
}"""
        r = _validate(tmp_path, code, "MessyTest.cls")
        assert r["issues"]
        for issue in r["issues"]:
            assert issue["severity"] in mod.SEVERITY_ORDER

    def test_threshold_is_seventy_percent(self):
        assert mod.THRESHOLD_PCT == 70


# ═══════════════════════════════════════════════════════════════════════════════
# Testing category
# ═══════════════════════════════════════════════════════════════════════════════


GOOD_TEST = """@IsTest
private class AccountServiceTest {
    @TestSetup
    static void makeData() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accounts.add(new Account(Name = 'Bulk ' + i));
        }
        insert accounts;
    }

    @IsTest
    static void shouldTrimNames_WhenProcessed() {
        List<Account> accounts = [SELECT Id, Name FROM Account];
        Test.startTest();
        Integer touched = AccountService.process(accounts);
        Test.stopTest();
        Assert.areEqual(200, touched, 'All accounts should be touched');
    }
}"""


class TestTestingChecks:
    def test_good_test_class_keeps_full_testing_score(self, tmp_path):
        r = _validate(tmp_path, GOOD_TEST, "AccountServiceTest.cls")
        assert r["scores"]["testing"] == 25
        assert _issues(r, category="testing") == []

    def test_test_method_without_assert_is_critical(self, tmp_path):
        code = """@IsTest
private class NoAssertTest {
    @IsTest
    static void runsWithoutChecking() {
        for (Integer i = 0; i < 250; i++) {}
        AccountService.process(null);
    }
}"""
        r = _validate(tmp_path, code, "NoAssertTest.cls")
        crit = _messages(r, category="testing", severity="CRITICAL")
        assert any("no assertions" in m for m in crit)
        assert r["scores"]["testing"] < 25

    def test_testmethod_keyword_is_recognised(self, tmp_path):
        code = """@IsTest
private class LegacyTest {
    static testMethod void oldStyle() {
        for (Integer i = 0; i < 250; i++) {}
        AccountService.process(null);
    }
}"""
        r = _validate(tmp_path, code, "LegacyTest.cls")
        assert any("oldStyle" in m for m in _messages(r, category="testing", severity="CRITICAL"))

    def test_system_assert_is_low(self, tmp_path):
        code = """@IsTest
private class SysAssertTest {
    @IsTest
    static void checks() {
        for (Integer i = 0; i < 250; i++) {}
        System.assertEquals(1, 1);
    }
}"""
        r = _validate(tmp_path, code, "SysAssertTest.cls")
        assert any("Assert class" in m for m in _messages(r, category="testing", severity="LOW"))
        # It still counts as an assertion — no CRITICAL "no assertions" finding.
        assert not _issues(r, category="testing", severity="CRITICAL")

    def test_see_all_data_is_high(self, tmp_path):
        code = """@IsTest(SeeAllData=true)
private class OrgDataTest {
    @IsTest
    static void checks() {
        for (Integer i = 0; i < 250; i++) {}
        Assert.isTrue(true, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "OrgDataTest.cls")
        assert any("SeeAllData" in m for m in _messages(r, category="testing", severity="HIGH"))

    def test_async_without_start_stop_is_moderate(self, tmp_path):
        code = """@IsTest
private class AsyncTest {
    @IsTest
    static void enqueues() {
        for (Integer i = 0; i < 250; i++) {}
        System.enqueueJob(new MyQueueable());
        Assert.isTrue(true, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "AsyncTest.cls")
        assert any(
            "Test.startTest" in m for m in _messages(r, category="testing", severity="MODERATE")
        )

    def test_async_inside_start_stop_not_flagged(self, tmp_path):
        code = """@IsTest
private class AsyncOkTest {
    @IsTest
    static void enqueues() {
        for (Integer i = 0; i < 250; i++) {}
        Test.startTest();
        System.enqueueJob(new MyQueueable());
        Test.stopTest();
        Assert.isTrue(true, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "AsyncOkTest.cls")
        assert not any("Test.startTest" in m for m in _messages(r, category="testing"))

    def test_many_data_creating_methods_without_setup_is_low(self, tmp_path):
        method = """
    @IsTest
    static void t{n}() {{
        insert new Account(Name = 'a');
        Assert.isTrue(true, 'ok');
    }}"""
        code = "@IsTest\nprivate class SetupTest {\n    static final Integer BULK = 200;"
        code += "".join(method.format(n=n) for n in range(4)) + "\n}"
        r = _validate(tmp_path, code, "SetupTest.cls")
        assert any("@TestSetup" in m for m in _messages(r, category="testing", severity="LOW"))

    def test_missing_bulk_test_is_moderate(self, tmp_path):
        code = """@IsTest
private class SingleRecordTest {
    @IsTest
    static void one() {
        insert new Account(Name = 'a');
        Assert.isTrue(true, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "SingleRecordTest.cls")
        assert any("bulk" in m.lower() for m in _messages(r, category="testing", severity="MODERATE"))

    def test_incidental_large_number_is_not_a_bulk_test(self, tmp_path):
        """A year, an HTTP status or a timeout must not count as a bulk test."""
        code = """@IsTest
private class IncidentalNumbersTest {
    @IsTest
    static void one() {
        Integer statusCode = 200;
        Datetime stamp = Datetime.newInstance(2026, 1, 1);
        Integer timeoutMs = 120000;
        insert new Account(Name = 'a');
        Assert.areEqual(200, statusCode, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "IncidentalNumbersTest.cls")
        assert any("bulk" in m.lower() for m in _messages(r, category="testing", severity="MODERATE"))

    def test_loop_bound_counts_as_a_bulk_test(self, tmp_path):
        code = """@IsTest
private class BulkLoopTest {
    @IsTest
    static void many() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < 250; i++) {
            accounts.add(new Account(Name = 'a' + i));
        }
        insert accounts;
        Assert.areEqual(250, accounts.size(), 'ok');
    }
}"""
        r = _validate(tmp_path, code, "BulkLoopTest.cls")
        assert not any("bulk" in m.lower() for m in _messages(r, category="testing", severity="MODERATE"))

    def test_factory_call_with_count_counts_as_a_bulk_test(self, tmp_path):
        code = """@IsTest
private class BulkFactoryTest {
    @IsTest
    static void many() {
        List<Account> accounts = TestDataFactory.createAccounts(200);
        insert accounts;
        Assert.areEqual(200, accounts.size(), 'ok');
    }
}"""
        r = _validate(tmp_path, code, "BulkFactoryTest.cls")
        assert not any("bulk" in m.lower() for m in _messages(r, category="testing", severity="MODERATE"))

    def test_non_test_class_is_not_scored_on_testing(self, tmp_path):
        r = ApexValidator(os.path.join(FIXTURES_DIR, "perfect_service.cls")).validate()
        assert r["scores"]["testing"] == 25


# ═══════════════════════════════════════════════════════════════════════════════
# Architecture category
# ═══════════════════════════════════════════════════════════════════════════════


class TestArchitectureChecks:
    def test_long_class_is_moderate(self, tmp_path):
        body = "\n".join(f"    // filler {i}" for i in range(510))
        code = f"public with sharing class Huge {{\n{body}\n}}"
        r = _validate(tmp_path, code, "Huge.cls")
        assert any("> 500" in m for m in _messages(r, category="architecture", severity="MODERATE"))
        assert r["scores"]["architecture"] < 20

    def test_wide_public_surface_is_low(self, tmp_path):
        methods = "\n".join(
            f"    /** doc */\n    public void m{i}() {{}}" for i in range(21)
        )
        code = f"public with sharing class Wide {{\n{methods}\n}}"
        r = _validate(tmp_path, code, "Wide.cls")
        assert any("public/global methods" in m for m in _messages(r, category="architecture", severity="LOW"))

    def test_trigger_with_logic_is_high(self):
        r = ApexValidator(os.path.join(FIXTURES_DIR, "logic_in_trigger.trigger")).validate()
        assert any(
            "handler" in m.lower() for m in _messages(r, category="architecture", severity="HIGH")
        )
        assert r["scores"]["architecture"] <= 10

    def test_delegating_trigger_is_clean(self):
        r = ApexValidator(os.path.join(FIXTURES_DIR, "good_trigger.trigger")).validate()
        assert _issues(r, category="architecture") == []
        assert r["score"] == 150

    def test_hardcoded_id_is_high(self, tmp_path):
        code = """public with sharing class Ids {
    /** doc */
    public static Id recordType() {
        return '0125000000AbCdE';
    }
    /** doc */
    public static Id longForm() {
        return '0015000000XyZaBAAZ';
    }
}"""
        r = _validate(tmp_path, code, "Ids.cls")
        highs = _messages(r, category="architecture", severity="HIGH")
        assert len([m for m in highs if "Hardcoded Salesforce ID" in m]) == 2

    def test_plain_words_are_not_ids(self, tmp_path):
        code = """public with sharing class Words {
    /** doc */
    public static String label() {
        return 'AccountServiceX';
    }
    /** doc */
    public static String digits() {
        return '123456789012345';
    }
}"""
        r = _validate(tmp_path, code, "Words.cls")
        assert not any("Hardcoded Salesforce ID" in m for m in _messages(r))

    def test_hardcoded_id_in_comment_ignored(self, tmp_path):
        code = """public with sharing class Commented {
    // example: '0125000000AbCdE'
    /** doc */
    public static void run() {}
}"""
        r = _validate(tmp_path, code, "Commented.cls")
        assert not any("Hardcoded Salesforce ID" in m for m in _messages(r))

    def test_without_sharing_justified_by_comment_is_info(self, tmp_path):
        code = """// Runs without sharing: aggregates records across all users for the admin dashboard.
public without sharing class Aggregator {
    /** doc */
    public static void run() {}
}"""
        r = _validate(tmp_path, code, "Aggregator.cls")
        sharing = [i for i in r["issues"] if "without sharing" in i["message"]]
        assert sharing and sharing[0]["severity"] == "INFO"
        assert r["scores"]["security"] == 25

    def test_without_sharing_unjustified_is_moderate(self, tmp_path):
        code = """public without sharing class Risky {
    /** doc */
    public static void run() {}
}"""
        r = _validate(tmp_path, code, "Risky.cls")
        sharing = [i for i in r["issues"] if "without sharing" in i["message"]]
        assert sharing and sharing[0]["severity"] == "MODERATE"
        assert r["scores"]["security"] == 20


# ═══════════════════════════════════════════════════════════════════════════════
# Performance category
# ═══════════════════════════════════════════════════════════════════════════════


class TestPerformanceChecks:
    def test_istest_in_a_comment_does_not_exempt_a_production_class(self, tmp_path):
        """The test-class exemptions must key off the annotation in code only."""
        code = """/**
 * Account helper. Covered by AccountServiceTest (@IsTest).
 */
public with sharing class AccountService {
    /** All accounts. */
    public static List<Account> all() {
        String note = 'see @IsTest classes for coverage';
        System.debug(note);
        return [SELECT Id FROM Account];
    }
}"""
        r = _validate(tmp_path, code, "AccountService.cls")
        messages = _messages(r, category="performance")
        assert any("unbounded" in m.lower() for m in messages)
        assert any("system.debug" in m.lower() for m in messages)

    def test_real_test_class_keeps_its_performance_exemptions(self, tmp_path):
        code = """@IsTest
private class AccountServiceTest {
    @IsTest
    static void all() {
        List<Account> accounts = [SELECT Id FROM Account];
        System.debug(accounts);
        Assert.isNotNull(accounts, 'ok');
    }
}"""
        r = _validate(tmp_path, code, "AccountServiceTest.cls")
        messages = _messages(r, category="performance")
        assert not any("unbounded" in m.lower() for m in messages)
        assert not any("system.debug" in m.lower() for m in messages)

    def test_unbounded_soql_is_moderate(self, tmp_path):
        code = """public with sharing class Unbounded {
    /** doc */
    public static List<Account> all() {
        return [SELECT Id, Name
                FROM Account];
    }
}"""
        r = _validate(tmp_path, code, "Unbounded.cls")
        msgs = _messages(r, category="performance", severity="MODERATE")
        assert any("neither WHERE nor LIMIT" in m for m in msgs)

    def test_bounded_soql_not_flagged(self, tmp_path):
        code = """public with sharing class Bounded {
    /** doc */
    public static List<Account> some(Set<Id> ids) {
        return [SELECT Id FROM Account WHERE Id IN :ids];
    }
    /** doc */
    public static List<Account> top() {
        return [SELECT Id FROM Account LIMIT 10];
    }
}"""
        r = _validate(tmp_path, code, "Bounded.cls")
        assert not any("neither WHERE" in m for m in _messages(r))

    def test_batch_query_locator_exempt(self, tmp_path):
        code = """public with sharing class MyBatch implements Database.Batchable<SObject> {
    /** doc */
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account]);
    }
}"""
        r = _validate(tmp_path, code, "MyBatch.cls")
        assert not any("neither WHERE" in m for m in _messages(r))

    def test_global_describe_is_moderate(self, tmp_path):
        code = """public with sharing class Describe {
    /** doc */
    public static void run() {
        Map<String, Schema.SObjectType> gd = Schema.getGlobalDescribe();
    }
}"""
        r = _validate(tmp_path, code, "Describe.cls")
        assert any("getGlobalDescribe" in m for m in _messages(r, category="performance", severity="MODERATE"))

    def test_future_is_moderate_in_non_test_class(self, tmp_path):
        code = """public with sharing class Async {
    /** doc */
    @future(callout=true)
    public static void call() {}
}"""
        r = _validate(tmp_path, code, "Async.cls")
        assert any("Queueable" in m for m in _messages(r, category="performance", severity="MODERATE"))

    def test_system_debug_is_info(self, tmp_path):
        code = """public with sharing class Noisy {
    /** doc */
    public static void run() {
        System.debug('a');
        System.debug('b');
    }
}"""
        r = _validate(tmp_path, code, "Noisy.cls")
        infos = _messages(r, category="performance", severity="INFO")
        assert any("System.debug" in m and "2 occurrences" in m for m in infos)
        assert r["scores"]["performance"] == 9

    def test_debug_in_test_class_not_flagged(self, tmp_path):
        code = GOOD_TEST.replace("Test.startTest();", "Test.startTest();\n        System.debug('x');")
        r = _validate(tmp_path, code, "AccountServiceTest.cls")
        assert not any("System.debug" in m for m in _messages(r))


# ═══════════════════════════════════════════════════════════════════════════════
# Score bounds
# ═══════════════════════════════════════════════════════════════════════════════


class TestScoreBounds:
    def test_categories_never_go_negative(self, tmp_path):
        loops = "\n".join(
            f"        for (Account a{i} : accs) {{ insert a{i}; }}" for i in range(6)
        )
        ids = "\n".join(f"        Id x{i} = '0125000000AbCd{i}';" for i in range(4))
        code = f"""public class Awful {{
    public static void bad(List<Account> accs) {{
{loops}
{ids}
    }}
}}"""
        r = _validate(tmp_path, code, "Awful.cls")
        assert r["scores"]["bulkification"] == 0
        assert r["scores"]["architecture"] == 0
        assert all(v >= 0 for v in r["scores"].values())
        assert 0 <= r["score"] <= r["max_score"]

    def test_result_reports_pct_and_threshold(self, tmp_path):
        r = ApexValidator(os.path.join(FIXTURES_DIR, "perfect_service.cls")).validate()
        assert r["threshold_pct"] == 70
        assert r["pct"] == 100.0


# ═══════════════════════════════════════════════════════════════════════════════
# CLI verdict
# ═══════════════════════════════════════════════════════════════════════════════


class TestCliVerdict:
    cli = load_script("skills/sf-apex/scripts/validate_apex_cli.py")

    def test_cli_shares_vocabulary_and_threshold(self):
        assert self.cli.SEVERITY_ORDER == mod.SEVERITY_ORDER
        assert self.cli.THRESHOLD_PCT == 70

    def test_clean_file_passes(self):
        r = self.cli.run_validation(os.path.join(FIXTURES_DIR, "perfect_service.cls"))
        assert r["passed"] is True and r["blocking_count"] == 0
        assert "PASSED" in r["output"]

    def test_high_finding_blocks_even_above_threshold(self):
        r = self.cli.run_validation(os.path.join(FIXTURES_DIR, "logic_in_trigger.trigger"))
        assert r["pct"] >= 70
        assert r["blocking_count"] >= 1 and r["passed"] is False
        assert "CRITICAL/HIGH" in r["output"]

    def test_low_score_blocks(self, tmp_path):
        loops = "\n".join(
            f"        for (Account a{i} : accs) {{ insert a{i}; }}" for i in range(3)
        )
        ids = "\n".join(f"        Id x{i} = '0125000000AbCd{i}';" for i in range(2))
        queries = "\n".join(f"        List<Contact> c{i} = [SELECT Id FROM Contact];" for i in range(3))
        catches = "\n".join(
            f"        try {{ x{i}.run(); }} catch (Exception e{i}) {{}}" for i in range(3)
        )
        code = (
            "public class Awful {\n    public static void bad(List<Account> accs) {\n"
            f"{loops}\n{ids}\n{queries}\n{catches}\n    }}\n}}"
        )
        path = tmp_path / "Awful.cls"
        path.write_text(code, encoding="utf-8")
        r = self.cli.run_validation(str(path))
        assert r["pct"] < 70 and r["passed"] is False
        assert "BELOW THRESHOLD" in r["output"]
