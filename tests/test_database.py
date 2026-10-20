import random
import pytest
from shorten import add_report, expand, get_conn, get_user, init_db, record_click, shorten, upsert_user


def query(sql, params=()):
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def test_insert_and_read_back_ignores_case(db):
    with get_conn() as conn:
        conn.execute("INSERT INTO links (code, url) VALUES (%s, %s)", ("AbC123", "https://example.com"))
        row = conn.execute("SELECT code, url FROM links WHERE code = %s", ("abc123",)).fetchone()
    assert row == ("AbC123", "https://example.com")


def test_tables_start_empty(db):
    assert query("SELECT count(*) FROM links") == [(0,)]
    assert query("SELECT count(*) FROM reports") == [(0,)]


# ---- shorten ----

def test_shorten_with_alias_returns_the_alias(db):
    assert shorten("https://example.com", "MySite") == "MySite"
    assert expand("mysite") == "https://example.com"


def test_taken_alias_is_refused_even_in_another_case(db):
    shorten("https://example.com", "MySite")
    assert shorten("https://other.com", "mysite") is None
    assert expand("MySite") == "https://example.com"  # the original is untouched


def test_shorten_without_alias_makes_a_six_character_code(db):
    code = shorten("https://example.com")
    assert len(code) == 6
    assert code.isalnum()
    assert expand(code) == "https://example.com"


def test_same_url_twice_gives_two_different_codes(db):
    first = shorten("https://example.com")
    second = shorten("https://example.com")
    assert first != second


def test_random_code_retries_after_a_collision(db, monkeypatch):
    shorten("https://x.com", "aaaaaa")
    answers = iter([list("aaaaaa"), list("bbbbbb")])
    monkeypatch.setattr(random, "choices", lambda *args, **kwargs: next(answers))
    assert shorten("https://y.com") == "bbbbbb"
    assert expand("bbbbbb") == "https://y.com"


# ---- expand ----

def test_expand_unknown_code_returns_none(db):
    assert expand("nope123") is None


def test_expand_hides_removed_links(db):
    shorten("https://example.com", "abc123")
    with get_conn() as conn:
        conn.execute("UPDATE links SET removed = 1 WHERE code = %s", ("abc123",))
    assert expand("abc123") is None


# ---- record_click ----

def test_record_click_counts_each_visit_ignoring_case(db):
    shorten("https://example.com", "abc123")
    record_click("abc123")
    record_click("ABC123")
    assert query("SELECT clicks FROM links WHERE code = %s", ("abc123",)) == [(2,)]


def test_record_click_on_unknown_code_does_nothing(db):
    record_click("nope123")
    assert query("SELECT count(*) FROM links") == [(0,)]


# ---- add_report ----

def test_report_saves_under_the_stored_code(db):
    shorten("https://example.com", "MySite")
    assert add_report("http://127.0.0.1:5000/MYSITE", "spam") == "MySite"
    assert query("SELECT code, reason, status FROM reports") == [("MySite", "spam", "open")]


def test_report_for_unknown_or_removed_link_is_rejected(db):
    shorten("https://example.com", "gone123")
    with get_conn() as conn:
        conn.execute("UPDATE links SET removed = 1 WHERE code = %s", ("gone123",))
    assert add_report("gone123", "spam") is None
    assert add_report("nope123", "spam") is None
    assert query("SELECT count(*) FROM reports") == [(0,)]


def test_report_with_no_code_in_it_is_rejected(db):
    assert add_report("!!!", "spam") is None


def test_report_reason_is_cleaned_and_shortened(db):
    shorten("https://example.com", "abc123")
    add_report("abc123", "bad\x00reason\n")
    add_report("abc123", "x" * 300)
    reasons = [row[0] for row in query("SELECT reason FROM reports ORDER BY id")]
    assert reasons == ["badreason", "x" * 200]

def test_github_id_must_be_unique(db):
    import psycopg

    with get_conn() as conn:
        conn.execute("INSERT INTO users (github_id, username) VALUES (1, 'first')")
    with pytest.raises(psycopg.errors.UniqueViolation):
        with get_conn() as conn:
            conn.execute("INSERT INTO users (github_id, username) VALUES (1, 'second')")


def test_init_db_upgrades_an_old_links_table_without_losing_rows(db):
    # pretend this is the table from before accounts existed
    with get_conn() as conn:
        conn.execute("ALTER TABLE links DROP COLUMN IF EXISTS owner_id")
        conn.execute("ALTER TABLE links DROP COLUMN IF EXISTS created_at")
        conn.execute("INSERT INTO links (code, url) VALUES ('oldlink', 'https://old.example')")

    init_db()

    with get_conn() as conn:
        row = conn.execute("SELECT url, owner_id, created_at FROM links WHERE code = 'oldlink'").fetchone()
    assert row == ("https://old.example", None, None)  # kept, no owner, creation time unknown

    shorten("https://new.example", "newlink")
    with get_conn() as conn:
        created = conn.execute("SELECT created_at FROM links WHERE code = 'newlink'").fetchone()[0]
    assert created is not None  # new links do get a creation time

def test_upsert_user_creates_a_user_you_can_read_back(db):
    user_id = upsert_user(583231, "octocat")
    assert get_user(user_id) == (user_id, "octocat")


def test_logging_in_again_updates_the_username_and_keeps_the_same_user(db):
    first = upsert_user(583231, "octocat")
    second = upsert_user(583231, "renamed-cat")
    assert first == second
    assert query("SELECT count(*) FROM users") == [(1,)]
    assert get_user(first) == (first, "renamed-cat")


def test_get_user_returns_none_for_an_unknown_id(db):
    assert get_user(999999) is None


@pytest.mark.parametrize(
    "github_id, username",
    [
        (0, "octocat"),
        (-5, "octocat"),
        ("123", "octocat"),
        (True, "octocat"),
        (123, ""),
        (123, "has space"),
        (123, "x" * 40),
        (123, "semi;colon"),
        (123, None),
    ],
)
def test_upsert_user_rejects_bad_data_and_stores_nothing(db, github_id, username):
    with pytest.raises(ValueError):
        upsert_user(github_id, username)
    assert query("SELECT count(*) FROM users") == [(0,)]

def test_a_link_made_with_an_owner_records_the_owner_and_creation_time(db):
    user_id = upsert_user(583231, "octocat")
    random_code = shorten("https://example.com", None, user_id)
    custom_code = shorten("https://example.org", "mycustom", user_id)
    rows = query("SELECT code, owner_id, created_at IS NOT NULL FROM links")
    assert sorted(rows) == sorted([(random_code, user_id, True), (custom_code, user_id, True)])


def test_a_link_made_without_an_owner_has_no_owner_but_has_a_creation_time(db):
    code = shorten("https://example.com")
    assert query("SELECT owner_id, created_at IS NOT NULL FROM links WHERE code = %s", (code,)) == [(None, True)]