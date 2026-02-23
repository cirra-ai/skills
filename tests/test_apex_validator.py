"""Tests for skills/cirra-ai-sf-apex/scripts/validate_apex.py"""

import os
import tempfile

from conftest import load_script

mod = load_script(
    "skills/cirra-ai-sf-apex/scripts/validate_apex.py"
)
ApexValidator = mod.ApexValidator


def _validate(apex_code: str) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cls", delete=False) as f:
        f.write(apex_code)
        tmp = f.name
    try:
        return ApexValidator(tmp).validate()
    finally:
        os.unlink(tmp)


def _bulk_criticals(result):
    return [
        i
        for i in result["issues"]
        if i["severity"] == "CRITICAL" and i["category"] == "bulkification"
    ]


def _sharing_issues(result):
    return [i for i in result["issues"] if "sharing" in i["message"].lower()]


# ── DML in loops ──────────────────────────────────────────────────────────────


def test_dml_in_loop_is_flagged():
    result = _validate(
        """public with sharing class Bad {
    /** @description Bad */
    public static void bad(List<Account> accs) {
        for (Account a : accs) {
            insert a;
        }
    }
}"""
    )
    assert len(_bulk_criticals(result)) == 1
    assert "loop" in _bulk_criticals(result)[0]["message"].lower()


def test_dml_after_loop_not_flagged():
    """DML that appears *after* a loop closes must not be flagged."""
    result = _validate(
        """public with sharing class Good {
    /** @description Good */
    public static void good(List<Account> accs) {
        List<Account> toInsert = new List<Account>();
        for (Account a : accs) {
            toInsert.add(a);
        }
        insert toInsert;
    }
}"""
    )
    assert _bulk_criticals(result) == []


# ── insert as user / modern DML syntax (API 57+) ─────────────────────────────


def test_insert_as_user_not_flagged():
    """insert as user is valid DML and must not be flagged as DML-in-loop."""
    result = _validate(
        """public with sharing class Svc {
    /** @description Creates */
    public static void create(List<Account> accs) {
        insert as user accs;
    }
}"""
    )
    assert _bulk_criticals(result) == []


def test_update_as_user_not_flagged():
    result = _validate(
        """public with sharing class Svc {
    /** @description Updates */
    public static void upd(List<Account> accs) {
        update as user accs;
    }
}"""
    )
    assert _bulk_criticals(result) == []


def test_delete_as_user_not_flagged():
    result = _validate(
        """public with sharing class Svc {
    /** @description Deletes */
    public static void del(List<Account> toDelete) {
        delete as user toDelete;
    }
}"""
    )
    assert _bulk_criticals(result) == []


def test_upsert_as_user_not_flagged():
    result = _validate(
        """public with sharing class Svc {
    /** @description Upserts */
    public static void ups(List<Account> accs) {
        upsert as user accs;
    }
}"""
    )
    assert _bulk_criticals(result) == []


# ── Inline-comment keyword false positives ───────────────────────────────────


def test_inline_comment_do_keyword_not_flagged():
    """'do' inside an inline comment must not trigger the loop detector."""
    result = _validate(
        """public with sharing class Svc {
    /** @description Inserts */
    public static void ins(List<Account> accs) {
        insert accs; // do the insert
    }
}"""
    )
    assert _bulk_criticals(result) == []


def test_inline_comment_while_keyword_not_flagged():
    """'while' inside an inline comment must not trigger the loop detector."""
    result = _validate(
        """public with sharing class Svc {
    /** @description Processes */
    public static void process(List<Account> accs) {
        update accs; // update while iterating would be bad
    }
}"""
    )
    assert _bulk_criticals(result) == []


# ── Sharing declaration ───────────────────────────────────────────────────────


def test_with_sharing_outer_class_no_warning():
    """public with sharing class must not produce a missing-sharing warning."""
    result = _validate(
        """public with sharing class AccountService {
    /** @description Does work */
    public static void work() {}
}"""
    )
    assert _sharing_issues(result) == []


def test_without_sharing_outer_class_warns():
    result = _validate(
        """public without sharing class Risky {
    /** @description Does work */
    public static void work() {}
}"""
    )
    assert len(_sharing_issues(result)) >= 1


def test_no_sharing_outer_class_warns():
    result = _validate(
        """public class NoSharing {
    /** @description Does work */
    public static void work() {}
}"""
    )
    assert len(_sharing_issues(result)) >= 1


def test_inner_class_without_sharing_not_flagged_for_missing():
    """Inner classes inherit sharing from the outer class — missing declaration is fine."""
    result = _validate(
        """public with sharing class Outer {
    public class InnerException extends Exception {}

    /** @description Does work */
    public static void work() {}
}"""
    )
    assert _sharing_issues(result) == []


def test_inner_class_with_without_sharing_is_warned():
    """Inner class explicitly declared without sharing should still produce a warning."""
    result = _validate(
        """public with sharing class Outer {
    public without sharing class Inner {}

    /** @description Does work */
    public static void work() {}
}"""
    )
    assert len(_sharing_issues(result)) >= 1
