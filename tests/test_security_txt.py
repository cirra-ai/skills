"""Tests for the RFC 9116 security.txt served at skills.cirra.ai.

The Cloudflare Pages deploy (`.github/workflows/package-plugins.yml`) publishes
the `docs/` directory as-is with `wrangler pages deploy docs`, so the file in
`docs/.well-known/` is exactly what is served at
https://skills.cirra.ai/.well-known/security.txt.
"""

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

SECURITY_TXT = Path(__file__).resolve().parent.parent / "docs" / ".well-known" / "security.txt"

# RFC 3339 date-time, as required for Expires by RFC 9116 section 2.5.5.
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def _fields():
    fields = {}
    for line in SECURITY_TXT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition(":")
        assert sep, f"malformed line in security.txt: {line!r}"
        fields.setdefault(name.strip().lower(), []).append(value.strip())
    return fields


def test_security_txt_exists():
    assert SECURITY_TXT.is_file(), f"missing {SECURITY_TXT}"


def test_security_txt_has_contact():
    contacts = _fields().get("contact", [])
    assert contacts, "security.txt must have at least one Contact field"
    for contact in contacts:
        assert contact.startswith(("mailto:", "https://", "tel:")), contact


def test_security_txt_expires_within_a_year():
    expires = _fields().get("expires", [])
    assert len(expires) == 1, "security.txt must have exactly one Expires field"
    value = expires[0]
    assert RFC3339.match(value), f"Expires is not RFC 3339: {value!r}"
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    now = datetime.now(UTC)
    assert when > now, f"security.txt expired on {value}; renew it"
    assert when <= now + timedelta(days=365), (
        f"Expires {value} is more than 365 days out (RFC 9116 recommends less than a year)"
    )


def test_security_txt_canonical_url():
    assert _fields().get("canonical") == ["https://skills.cirra.ai/.well-known/security.txt"]
