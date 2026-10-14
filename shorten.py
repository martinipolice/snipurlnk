import random
import string
import os
import re
from urllib.parse import urlparse
import psycopg

def get_conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(url, connect_timeout=15)

RESERVED_ALIASES = { # these are the reserved alias
       "undefined", "root", "report", "reports", "shorten", "static", "api", 
       "admin", "login", "logout", "signup", "register", "dashboard", "settings", 
       "account", "help", "support", "about", "contact", "terms", "privacy", 
       "home", "index", "null", "undefined", "root",
    }

def is_valid_alias(alias): # checks if there is consistency and no words from the reserved aliases
    good_pattern = re.fullmatch(r"[A-Za-z0-9_-]{3,30}", alias)
    not_reserved = alias.lower() not in RESERVED_ALIASES
    return bool(good_pattern) and not_reserved

def init_db():
    with get_conn() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS citext")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                code CITEXT PRIMARY KEY,
                url TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0,
                removed INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                code CITEXT NOT NULL,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)

init_db() # create the tables in Postgres if they don't exist yet

def shorten(url, alias=None):
    with get_conn() as conn:
        # if there is an alias, try it once
        if alias:
            try:
                conn.execute("INSERT INTO links (code, url) VALUES (%s, %s)", (alias, url))
                return alias
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return None

        # no alias
        characterPool = string.ascii_letters + string.digits # char pool of letters and nums
        while True:
            random_code = ''.join(random.choices(characterPool, k=6)) # generate a random 6-char code

            try:
                conn.execute("INSERT INTO links (code, url) VALUES (%s, %s)", (random_code, url))
                return random_code
            except psycopg.errors.UniqueViolation: # this ensures there is no dupes
                conn.rollback() # clear the failed transaction, then try a new code

def expand(code):
    with get_conn() as conn:
        result = conn.execute("SELECT url FROM links WHERE code = %s AND removed = 0", (code,)).fetchone()

    if result is not None:
        return result[0] # return the url
    

def is_valid_url(url):
    if len(url) > 2048 or not url.isprintable() or " " in url:
        return False
    try:
        parsed = urlparse(url)
        parsed.port  # raises ValueError on a bad port
    except ValueError:
        return False
    host = parsed.hostname
    return parsed.scheme in ("http", "https") and bool(host) and "." in host.strip(".")
    

def normalize_url(url): # this normalizes the url if it does not have http/https
    if url.lower().startswith(("http://", "https://")):
        return url

    return "https://" + url

def record_click(code): # this adds click count
    with get_conn() as conn:
        conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = %s", (code,))

def extract_code(text): # takes a short link or a bare code, and returns the code (or None)
    code = text.strip().split("?")[0].split("#")[0].rstrip("/").split("/")[-1]
    return code if re.fullmatch(r"[A-Za-z0-9_-]{3,30}", code) else None

def add_report(text, reason): # saves a report and returns the code, or None if there is no such live link
    code = extract_code(text)
    if code is None:
        return None

    reason = "".join(ch for ch in reason if ch.isprintable())[:200]

    with get_conn() as conn:
        row = conn.execute("SELECT code FROM links WHERE code = %s AND removed = 0", (code,)).fetchone()
        if row is None:
            return None
        conn.execute("INSERT INTO reports (code, reason) VALUES (%s, %s)", (row[0], reason))

    return row[0]