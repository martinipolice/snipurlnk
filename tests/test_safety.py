import io
import json
import socket
import urllib.error

import pytest

import safety


def fake_urlopen(reply, seen=None):
    """Stand in for urlopen: no real network. `reply` is a dict to return or an error to raise."""

    def _open(request, timeout=None):
        if seen is not None:
            seen.append(request)
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(json.dumps(reply).encode())

    return _open


@pytest.fixture
def with_key(monkeypatch):
    monkeypatch.setenv("SAFE_BROWSING_API_KEY", "test-key-123")


def test_flagged_url_is_reported(monkeypatch, with_key):
    reply = {"matches": [{"threatType": "MALWARE"}]}
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen(reply))
    assert safety.is_flagged("https://bad.example") is True


def test_clean_url_is_not_flagged(monkeypatch, with_key):
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen({}))
    assert safety.is_flagged("https://example.com") is False


def test_no_key_means_no_check(monkeypatch):
    monkeypatch.delenv("SAFE_BROWSING_API_KEY", raising=False)
    seen = []
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen({"matches": [1]}, seen))
    assert safety.is_flagged("https://bad.example") is False
    assert seen == []


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.URLError("no route"),
        urllib.error.HTTPError("https://x", 403, "Forbidden", {}, None),
        socket.timeout("timed out"),
        ValueError("not json"),
    ],
)
def test_google_trouble_lets_the_link_through(monkeypatch, with_key, error):
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen(error))
    assert safety.is_flagged("https://example.com") is False


def test_key_goes_in_a_header_not_in_the_url(monkeypatch, with_key):
    seen = []
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen({}, seen))
    safety.is_flagged("https://example.com/page")
    request = seen[0]
    assert "test-key-123" not in request.full_url
    assert "test-key-123" in dict(request.header_items()).values()
    assert json.loads(request.data)["threatInfo"]["threatEntries"] == [{"url": "https://example.com/page"}]


def test_failure_log_does_not_contain_the_key(monkeypatch, with_key, caplog):
    error = urllib.error.URLError("boom test-key-123")
    monkeypatch.setattr(safety.urllib.request, "urlopen", fake_urlopen(error))
    safety.is_flagged("https://example.com")
    assert "allowing the link" in caplog.text
    assert "test-key-123" not in caplog.text
