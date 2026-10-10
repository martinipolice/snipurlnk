import random
import string
import sqlite3
import re
from urllib.parse import urlparse

DB_PATH = "links.db"

RESERVED_ALIASES = { # these are the reserved alias
       "shorten", "static", "api", "admin", "login", "logout", "signup",
       "register", "dashboard", "settings", "account", "help", "support",
       "about", "contact", "terms", "privacy", "home", "index", "null",
       "undefined", "root",
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
            url TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db() # initialize it

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

    cursor.execute("SELECT url FROM links WHERE code = ?", (code,)) # this get the url from that specific code
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
