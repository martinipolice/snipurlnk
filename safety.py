import json
import logging
import os
import urllib.request

ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
TIMEOUT_SECONDS = 3

log = logging.getLogger(__name__)


def is_flagged(url):
    """Return True only if Google Safe Browsing says this URL is dangerous.

    It returns False when the URL is clean, when there is no API key, and when
    Google can't be reached (we chose to allow links through during an outage).
    """
    key = os.environ.get("SAFE_BROWSING_API_KEY")
    if not key:
        log.warning("SAFE_BROWSING_API_KEY is not set, so links are not being checked")
        return False

    body = {
        "client": {"clientId": "snipurlnk", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.load(response)
    except Exception as error:
        # Only the error type is logged, never the request, so the key can't leak.
        log.warning("Safe Browsing check failed (%s), allowing the link", type(error).__name__)
        return False
    return bool(data.get("matches"))
