import os

import pytest

from shorten import get_conn, init_db


@pytest.fixture
def db(monkeypatch):
    test_url = os.environ.get("TEST_DATABASE_URL")
    if not test_url:
        pytest.skip("TEST_DATABASE_URL is not set")
    if test_url == os.environ.get("DATABASE_URL"):
        pytest.fail("TEST_DATABASE_URL must not be the same as DATABASE_URL")

    # point the app's get_conn() at the test database, for this test only
    monkeypatch.setenv("DATABASE_URL", test_url)

    with get_conn() as conn:
        marked = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
            ("public", "i_am_a_test_database"),
        ).fetchone()[0]
    if marked == 0:
        pytest.fail("Refusing to wipe tables: this database is not marked as a test database")

    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM reports")
        conn.execute("DELETE FROM links")

@pytest.fixture(autouse=True)
def no_real_safe_browsing(monkeypatch):
    monkeypatch.delenv("SAFE_BROWSING_API_KEY", raising=False)