import pytest

from shorten import extract_code, is_valid_alias, is_valid_url, normalize_url


@pytest.mark.parametrize("raw, expected", [
    ("example.com", "https://example.com"),
    ("www.example.com/path", "https://www.example.com/path"),
    ("https://example.com", "https://example.com"),
    ("http://example.com", "http://example.com"),
    ("HTTPS://EXAMPLE.COM", "HTTPS://EXAMPLE.COM"),
])
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


@pytest.mark.parametrize("raw", [
    "ftp://example.com",
    "javascript:alert(1)",
])
def test_normalizing_never_makes_a_bad_scheme_valid(raw):
    assert is_valid_url(normalize_url(raw)) is False


@pytest.mark.parametrize("alias", [
    "abc",
    "a" * 30,
    "My-Site_1",
    "ABC123",
])
def test_good_aliases(alias):
    assert is_valid_alias(alias) is True


@pytest.mark.parametrize("alias", [
    "",
    "ab",
    "a" * 31,
    "my site",
    "my.site",
    "my/site",
    "h\u00e9llo",
    "abc\n",
    "admin",
    "ADMIN",
    "Report",
])
def test_bad_aliases(alias):
    assert is_valid_alias(alias) is False


@pytest.mark.parametrize("text, expected", [
    ("abc123", "abc123"),
    ("MySite", "MySite"),
    ("  abc123  ", "abc123"),
    ("http://127.0.0.1:5000/abc123", "abc123"),
    ("https://snip.example/abc123/", "abc123"),
    ("https://snip.example/abc123?utm=1", "abc123"),
    ("https://snip.example/abc123#top", "abc123"),
    ("https://example.com/a/b/abc123", "abc123"),
])
def test_extract_code_finds_the_code(text, expected):
    assert extract_code(text) == expected


@pytest.mark.parametrize("text", [
    "",
    "ab",
    "a b c",
    "!!!",
    "https://snip.example/",
])
def test_extract_code_returns_none_when_there_is_no_code(text):
    assert extract_code(text) is None