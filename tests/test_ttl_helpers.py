from datetime import datetime, timedelta, timezone

import pytest

from cubby_tool import commands


def test_parse_duration_units():
    assert commands._parse_duration("12h") == timedelta(hours=12)
    assert commands._parse_duration("30d") == timedelta(days=30)
    assert commands._parse_duration("2w") == timedelta(weeks=2)


@pytest.mark.parametrize("bad", ["", "0d", "-1d", "5m", "abc", "10", "d", "1.5d"])
def test_parse_duration_rejects_garbage(bad):
    with pytest.raises(ValueError):
        commands._parse_duration(bad)


def test_ttl_to_expires_is_in_the_future():
    expires = commands._ttl_to_expires("1d")
    when = datetime.fromisoformat(expires)
    assert when > datetime.now(timezone.utc)


def test_format_relative_future_and_past():
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    soon = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
    assert commands._format_relative(future) == "in 5 days"
    assert commands._format_relative(past) == "expired 3 days ago"
    assert commands._format_relative(soon) == "in 4 hours"


def test_is_expired():
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    assert commands._is_expired({"value": "x", "expires": past}) is True
    assert commands._is_expired({"value": "x", "expires": future}) is False
    assert commands._is_expired({"value": "x"}) is False
