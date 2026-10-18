import pytest

from shorten import get_conn


@pytest.fixture
def client(db):
    # imported late on purpose: importing app connects to the database, and the
    # `db` fixture has already pointed DATABASE_URL at the test branch by now
    from app import app, limiter

    limiter.reset()  # every test starts with fresh rate-limit counters
    app.config["TESTING"] = True
    return app.test_client()


def query(sql, params=()):
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def text(response):
    return response.get_data(as_text=True)


# ---- pages ----

def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "snipURlnk" in text(response)


def test_report_page_loads(client):
    response = client.get("/report")
    assert response.status_code == 200
    assert "Report a link" in text(response)


# ---- POST /shorten ----

@pytest.mark.parametrize("data, status, message", [
    ({}, 400, "Missing url"),
    ({"url": "   "}, 400, "Missing url"),
    ({"url": "not a url"}, 400, "Invalid URL"),
    ({"url": "ftp://example.com"}, 400, "Invalid URL"),
    ({"url": "example.com", "alias": "ab"}, 400, "Invalid alias"),
    ({"url": "example.com", "alias": "admin"}, 400, "Invalid alias"),
])
def test_shorten_rejects_bad_input(client, data, status, message):
    response = client.post("/shorten", data=data)
    assert response.status_code == status
    assert text(response) == message
    assert query("SELECT count(*) FROM links") == [(0,)]


def test_shorten_creates_a_link_that_redirects(client):
    response = client.post("/shorten", data={"url": "example.com"})
    code = text(response)
    assert response.status_code == 200
    assert len(code) == 6

    visit = client.get("/" + code)
    assert visit.status_code == 302
    assert visit.headers["Location"] == "https://example.com"


def test_alias_taken_in_another_case_is_409(client):
    first = client.post("/shorten", data={"url": "example.com", "alias": "MySite"})
    assert (first.status_code, text(first)) == (200, "MySite")

    second = client.post("/shorten", data={"url": "other.com", "alias": "mysite"})
    assert (second.status_code, text(second)) == (409, "Alias already taken")


def test_get_shorten_does_not_create_anything(client):
    response = client.get("/shorten")
    assert response.status_code == 404
    assert query("SELECT count(*) FROM links") == [(0,)]


# ---- following links ----

def test_unknown_code_is_404(client):
    response = client.get("/nope123")
    assert response.status_code == 404
    assert b"Link not found" in response.data


def test_visit_redirects_and_counts_a_click_ignoring_case(client):
    client.post("/shorten", data={"url": "example.com", "alias": "MySite"})
    response = client.get("/MYSITE")
    assert response.status_code == 302
    assert query("SELECT clicks FROM links WHERE code = %s", ("mysite",)) == [(1,)]


def test_removed_link_is_404_and_not_counted(client):
    client.post("/shorten", data={"url": "example.com", "alias": "MySite"})
    with get_conn() as conn:
        conn.execute("UPDATE links SET removed = 1 WHERE code = %s", ("mysite",))
    response = client.get("/MySite")
    assert response.status_code == 404
    assert query("SELECT clicks FROM links WHERE code = %s", ("mysite",)) == [(0,)]


# ---- reports ----

def test_report_needs_a_link(client):
    response = client.post("/report", data={})
    assert (response.status_code, text(response)) == (400, "Missing link")


def test_report_for_unknown_link_is_404(client):
    response = client.post("/report", data={"link": "nope123"})
    assert (response.status_code, text(response)) == (404, "Link not found")


def test_report_is_saved(client):
    client.post("/shorten", data={"url": "example.com", "alias": "MySite"})
    response = client.post("/report", data={"link": "http://127.0.0.1:5000/mysite", "reason": "spam"})
    assert (response.status_code, text(response)) == (200, "Thanks, we'll review it.")
    assert query("SELECT code, reason, status FROM reports") == [("MySite", "spam", "open")]


# ---- rate limits ----
# These send empty requests. They are refused with a 400 before touching the
# database, but the limiter still counts them, so the tests stay fast.

def test_shorten_is_limited_to_ten_a_minute(client):
    statuses = [client.post("/shorten", data={}).status_code for _ in range(11)]
    assert statuses == [400] * 10 + [429]


def test_report_is_limited_to_five_a_minute(client):
    statuses = [client.post("/report", data={}).status_code for _ in range(6)]
    assert statuses == [400] * 5 + [429]


def test_limit_message_is_friendly(client):
    for _ in range(10):
        client.post("/shorten", data={})
    response = client.post("/shorten", data={})
    assert text(response) == "Too many requests. Please wait a minute and try again."

    # ---- the visitor's address behind Render's proxies ----
# Render adds 3 addresses to the end of X-Forwarded-For, and the app trusts those 3.
# Anything a visitor sends is further left, so it can't change who the limiter sees.

def post_empty(client, forwarded_for):
    return client.post("/shorten", data={}, headers={"X-Forwarded-For": forwarded_for})


def test_each_visitor_gets_their_own_limit(client):
    for _ in range(10):
        post_empty(client, "9.9.9.1, 10.0.0.1, 10.0.0.2")
    assert post_empty(client, "9.9.9.1, 10.0.0.1, 10.0.0.2").status_code == 429
    assert post_empty(client, "9.9.9.2, 10.0.0.1, 10.0.0.2").status_code == 400


def test_a_faked_forwarded_header_cannot_dodge_the_limit(client):
    for i in range(10):
        post_empty(client, f"1.1.1.{i}, 9.9.9.1, 10.0.0.1, 10.0.0.2")
    assert post_empty(client, "1.1.1.99, 9.9.9.1, 10.0.0.1, 10.0.0.2").status_code == 429

# ---- the Safe Browsing check ----

def test_flagged_url_is_refused_and_not_stored(client, monkeypatch):
    monkeypatch.setattr("app.is_flagged", lambda url: True)

    def must_not_run(*args, **kwargs):
        raise AssertionError("shorten() was called for a flagged URL")

    monkeypatch.setattr("app.shorten", must_not_run)
    response = client.post("/shorten", data={"url": "https://bad.example"})
    assert response.status_code == 400
    assert b"unsafe" in response.data


def test_safe_browsing_sees_the_cleaned_up_url(client, monkeypatch):
    seen = []
    monkeypatch.setattr("app.is_flagged", lambda url: seen.append(url) or False)
    client.post("/shorten", data={"url": "  example.com  "})
    assert seen == ["https://example.com"]


def test_invalid_input_never_reaches_safe_browsing(client, monkeypatch):
    seen = []
    monkeypatch.setattr("app.is_flagged", lambda url: seen.append(url) or False)
    client.post("/shorten", data={"url": "https://localhost"})
    client.post("/shorten", data={"url": "https://example.com", "alias": "a b"})
    assert seen == []

# ---- the custom 404 page ----

def test_unknown_code_shows_the_friendly_404_page(client):
    response = client.get("/doesnotexist")
    assert response.status_code == 404
    assert b"Link not found" in response.data
    assert b'href="/report"' in response.data
    assert b'href="/"' in response.data


def test_unknown_page_also_gets_the_friendly_404(client):
    response = client.get("/some/made/up/path")
    assert response.status_code == 404
    assert b"Link not found" in response.data