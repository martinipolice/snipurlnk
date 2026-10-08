import random
import string
import sqlite3
from urllib.parse import urlparse

DB_PATH = "links.db"

def init_db(): # this initialize an SQLite to store the code-url pair
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            url TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db() # initialize it

def shorten(url):
    characterPool = string.ascii_letters + string.digits # char pool of letters and nums
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()

    if result is not None:
        return result[0] # return the url
    

def is_valid_url(url):
    parsed = urlparse(url)

    return parsed.scheme in ("http","https") and bool(parsed.netloc)
    


