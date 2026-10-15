from shorten import get_conn


def test_insert_and_read_back_ignores_case(db):
    with get_conn() as conn:
        conn.execute("INSERT INTO links (code, url) VALUES (%s, %s)", ("AbC123", "https://example.com"))
        row = conn.execute("SELECT code, url FROM links WHERE code = %s", ("abc123",)).fetchone()
    assert row == ("AbC123", "https://example.com")


def test_tables_start_empty(db):
    with get_conn() as conn:
        links = conn.execute("SELECT count(*) FROM links").fetchone()[0]
        reports = conn.execute("SELECT count(*) FROM reports").fetchone()[0]
    assert links == 0
    assert reports == 0