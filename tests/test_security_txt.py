"""Tests for the RFC 9116 security.txt served at skills.cirra.ai.

The Cloudflare Pages deploy (`.github/workflows/package-plugins.yml`) publishes
the `docs/` directory as-is with `wrangler pages deploy docs`, so the file in
`docs/.well-known/` is exactly what is served at
https://skills.cirra.ai/.well-known/security.txt.
"""

import calendar
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

SECURITY_TXT = Path(__file__).resolve().parent.parent / "docs" / ".well-known" / "security.txt"

_MAILTO_ADDR = re.compile(r"^[^@/?#]+@[^@/?#]+\.[^@/?#]+$")
_TEL_NUMBER = re.compile(r"^\+?[0-9][0-9().-]*$")
_BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
_RFC3339 = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(\.\d+)?"
    r"([Zz]|([+-])(\d{2}):(\d{2}))$"
)


def is_valid_contact(value):
    """Contact values are URIs (RFC 9116 section 2.5.3).

    Parse each one and check the parts its scheme needs, rather than matching a
    prefix.
    """
    if re.search(r"\s", value):
        return False
    try:
        url = urlsplit(value)
    except ValueError:
        return False
    scheme = url.scheme.lower()
    if scheme == "mailto":
        if _BAD_PERCENT.search(url.path):
            return False  # malformed percent-encoding
        try:
            addr = unquote(url.path, errors="strict")
        except UnicodeDecodeError:
            return False
        return bool(_MAILTO_ADDR.match(addr))
    if scheme == "https":
        try:
            host = url.hostname
        except ValueError:
            return False
        return bool(host) and "." in host
    if scheme == "tel":
        return bool(_TEL_NUMBER.match(url.path))
    return False


def parse_rfc3339(value):
    """Parse an RFC 3339 date-time (RFC 9116 section 2.5.5) to an aware datetime.

    Checks the syntax and the calendar ranges first so impossible dates such as
    Feb 30 are rejected rather than rolled over. Returns None when invalid.
    """
    m = _RFC3339.match(value)
    if not m:
        return None
    y, mo, d, h, mi, sec, frac, _, sign, oh, om = m.groups()
    year, month, day = int(y), int(mo), int(d)
    hour, minute, second = int(h), int(mi), int(sec)
    if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(year, month)[1]:
        return None
    if hour > 23 or minute > 59 or second > 60:
        return None
    if sign and (int(oh) > 23 or int(om) > 59):
        return None
    offset = timedelta(hours=int(oh), minutes=int(om)) if sign else timedelta(0)
    if sign == "-":
        offset = -offset
    micro = round(float(f"0{frac}") * 1_000_000) if frac else 0
    micro = min(micro, 999_999)
    # A leap second (:60) counts as the last millisecond of the minute.
    if second == 60:
        second, micro = 59, 999_000
    try:
        return datetime(year, month, day, hour, minute, second, micro, tzinfo=UTC) - offset
    except (ValueError, OverflowError):
        return None  # year 0000, or an offset that moves it outside datetime's range


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
        assert is_valid_contact(contact), (
            f"Contact is not a valid mailto:, https: or tel: URI: {contact}"
        )


def test_security_txt_expires_within_a_year():
    expires = _fields().get("expires", [])
    assert len(expires) == 1, "security.txt must have exactly one Expires field"
    value = expires[0]
    when = parse_rfc3339(value)
    assert when is not None, f"Expires is not an RFC 3339 date-time: {value!r}"
    now = datetime.now(UTC)
    assert when > now, f"security.txt expired on {value}; renew it"
    assert when <= now + timedelta(days=365), (
        f"Expires {value} is more than 365 days out (RFC 9116 recommends less than a year)"
    )


def test_security_txt_canonical_url():
    assert _fields().get("canonical") == ["https://skills.cirra.ai/.well-known/security.txt"]


@pytest.mark.parametrize(
    "value",
    [
        "mailto:security@cirra.ai",
        "mailto:security%40cirra.ai",
        "https://cirra.ai/security",
        "tel:+1-555-0100",
    ],
)
def test_is_valid_contact_accepts(value):
    assert is_valid_contact(value)


@pytest.mark.parametrize(
    "value",
    [
        "mailto:",
        "mailto:security",
        "mailto:security@localhost",
        "mailto:a%zz@cirra.ai",
        "mailto:a%ff@cirra.ai",
        "mailto: security@cirra.ai",
        "https://",
        "https://localhost/",
        "http://cirra.ai/security",
        "tel:call-me",
        "security@cirra.ai",
        "ftp://cirra.ai",
    ],
)
def test_is_valid_contact_rejects(value):
    assert not is_valid_contact(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2027-09-28T00:00:00.000Z", datetime(2027, 9, 28, tzinfo=UTC)),
        ("2027-09-28t02:00:00+02:00", datetime(2027, 9, 28, tzinfo=UTC)),
        ("2027-09-27T19:30:00-04:30", datetime(2027, 9, 28, tzinfo=UTC)),
        ("2028-02-29T12:00:00Z", datetime(2028, 2, 29, 12, tzinfo=UTC)),
        ("2027-12-31T23:59:60Z", datetime(2027, 12, 31, 23, 59, 59, 999_000, tzinfo=UTC)),
    ],
)
def test_parse_rfc3339_accepts(value, expected):
    assert parse_rfc3339(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "2027-02-30T00:00:00Z",
        "2027-02-29T00:00:00Z",
        "2027-13-01T00:00:00Z",
        "2027-00-10T00:00:00Z",
        "2027-09-28T24:00:00Z",
        "2027-09-28T00:60:00Z",
        "2027-09-28T00:00:61Z",
        "2027-09-28T00:00:00+24:00",
        "0000-01-01T00:00:00Z",
        "2027-09-28T00:00:00",
        "2027-09-28 00:00:00Z",
        "2027-09-28",
        "Tue, 28 Sep 2027 00:00:00 GMT",
    ],
)
def test_parse_rfc3339_rejects(value):
    assert parse_rfc3339(value) is None
