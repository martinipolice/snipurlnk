import pytest

from shorten import is_valid_url

GOOD_URLS = [
    "https://example.com",
    "http://example.com",
    "https://sub.example.co.uk/path?x=1#frag",
    "https://example.com:8080/a",
    "HTTPS://EXAMPLE.COM",
    "https://example.com/" + "a" * 2028,  # exactly 2048 characters
]

BAD_URLS = [
    "",
    "example.com",
    "ftp://example.com",
    "javascript:alert(1)",
    "https://localhost",
    "https://",
    "https://exa mple.com",
    "https://example.com:99999",
    "https://example.com:abc",
    "https://example.com/\x00",
    "https://example.com/" + "a" * 2029,  # 2049 characters
]


@pytest.mark.parametrize("url", GOOD_URLS)
def test_good_urls_are_accepted(url):
    assert is_valid_url(url) is True


@pytest.mark.parametrize("url", BAD_URLS)
def test_bad_urls_are_rejected(url):
    assert is_valid_url(url) is False