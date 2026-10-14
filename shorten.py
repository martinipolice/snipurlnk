import random
import string
import sqlite3
import os
import re
from urllib.parse import urlparse
import psycopg

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.db")

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

def init_db(): # this initialize an SQLite to store the code-url pair
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY COLLATE NOCASE,
            url TEXT NOT NULL,
            clicks INTEGER NOT NULL DEFAULT 0,
            removed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # an older links table has no "removed" column, and CREATE TABLE IF NOT EXISTS won't add it
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(links)")]
    if "removed" not in columns:
        cursor.execute("ALTER TABLE links ADD COLUMN removed INTEGER NOT NULL DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL COLLATE NOCASE,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

init_db() # initialize it

def init_pg_db():
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

def shorten(url, alias=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # if there is an alias, ...
    if alias:
            try:
                cursor.execute("INSERT INTO links (code, url) VALUES (?, ?)", (alias, url))
                conn.commit()
                conn.close()
                return alias            
            except sqlite3.IntegrityError:
                conn.close()
                return None             

    # no alias
    characterPool = string.ascii_letters + string.digits # char pool of letters and nums
    while True:
        random_code = ''.join(random.choices(characterPool, k=6)) # generate a random 6-char code

        try: # a try-catch to catch integrity error
            cursor.execute("INSERT INTO links (code, url) VALUES (?, ?)", (random_code, url))
            conn.commit()
            conn.close()
            return random_code
        
        except sqlite3.IntegrityError: # this ensures there is no dupes
            pass # pass if the code is alr a dupe, so it tries again

def expand(code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM links WHERE code = ? AND removed = 0", (code,)) # this get the url from that specific code
    result = cursor.fetchone() # this fetches that url
    
    conn.close()

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
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def extract_code(text): # takes a short link or a bare code, and returns the code (or None)
    code = text.strip().split("?")[0].split("#")[0].rstrip("/").split("/")[-1]
    return code if re.fullmatch(r"[A-Za-z0-9_-]{3,30}", code) else None

def add_report(text, reason): # saves a report and returns the code, or None if there is no such live link
    code = extract_code(text)
    if code is None:
        return None

    reason = "".join(ch for ch in reason if ch.isprintable())[:200]

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT code FROM links WHERE code = ? AND removed = 0", (code,)).fetchone()
    if row is None:
        conn.close()
        return None

    conn.execute("INSERT INTO reports (code, reason) VALUES (?, ?)", (row[0], reason))
    conn.commit()
    conn.close()
    return row[0]