```
--   ___ _  _ ___ ___ _   _ ___ _    _  _ _  __ ----
--  / __| \| |_ _| _ \ | | | _ \ |  | \| | |/ / ----
--  \__ \ .` || ||  _/ |_| |   / |__| .` | ' < ----
--  |___/_|\_|___|_|  \___/|_|_\____|_|\_|_|\_\ ----
--  ------------------------------------
```

A URL shortener built with Python, Flask, and Postgres (hosted on Neon). I'm building it as a learning project, one step at a time.

## Features

- Shorten any URL into a random 6-character code
- Optional custom aliases (3 to 30 characters: letters, digits, `-` and `_`), case-insensitive, with a list of reserved words
- Redirect from the short link to the original URL
- Links are stored in a hosted Postgres database, so they survive server restarts and redeploys
- Collision-safe code generation: a taken code is never overwritten
- URL validation: only `http` and `https` links with a real domain are accepted, and bad ports, spaces, control characters, and URLs over 2,048 characters are rejected
- Auto-fixes missing schemes (`example.com` becomes `https://example.com`)
- Every submission creates its own new link, even for a URL that was shortened before
- Web page with clear error messages, Copy and Go buttons, and Enter-to-submit
- Light and dark themes that follow the device setting
- Styled with [Puppertino](https://github.com/codedgar/Puppertino), loaded from the jsDelivr CDN
- Proper error responses: `400` for missing or invalid input, `404` for unknown codes, `409` for a taken alias
- Counts how many times each short link is visited (stored, not displayed yet)
- Rate limiting per visitor: 10 links per minute and 100 per day, 120 requests per minute elsewhere
- Report a link from the page, and review and remove reported links with admin commands

## How it works

1. You submit a URL, and optionally a custom alias.
2. The server cleans up the URL: it trims whitespace and adds `https://` if no scheme is given.
3. It validates the URL. The scheme must be `http` or `https`, the hostname must contain a dot, and the URL must be printable, free of spaces, have a valid port, and be at most 2,048 characters. Anything else is rejected with a `400`.
4. If an alias was given, it must match the allowed pattern and not be a reserved word (like `admin` or `login`), or the server returns a `400`.
5. The server saves the pair `code -> URL` in a Postgres table.
   - With an alias, it tries to insert that code once. If it's taken, the server returns a `409`.
   - Without one, it generates a random code and retries with a new one if there's a collision.
6. When someone visits `/<code>`, the server looks up the code, adds 1 to that link's click count, and redirects to the original URL. Unknown or removed codes return a `404` and change nothing.

### Design decisions

- **One link per submission:** submitting the same URL twice creates two different short links. This keeps each person's link independent, and it makes per-link features (like click counts) possible later.
- **Case-insensitive codes:** the `code` column uses Postgres's `citext` type, so `MySite` and `mysite` are the same link. This prevents lookalike links from being registered by different people.
- **Click counts include all redirects:** every successful visit to a short link adds 1, including automated ones like link previews and prefetches. Filtering these out is a possible later improvement.
- **Removed, not deleted:** removing a link sets a flag instead of deleting the row, so the code stays taken and the same alias can't be registered again.

## Getting started

**Requirements:** Python 3.

**Database:** create a free Postgres database at [Neon](https://neon.com), copy its connection string, and set it as `DATABASE_URL`. Never commit it, because it contains the database password.

- Windows PowerShell: `$env:DATABASE_URL = 'postgresql://...'`
- macOS or Linux: `export DATABASE_URL='postgresql://...'`

```bash
git clone https://github.com/martinipolice/snipurlnk.git
cd snipurlnk
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser. The tables are created automatically on first run. The first request after the database has been idle can take a few seconds while it wakes up. The page loads its stylesheet from a CDN, so it needs an internet connection to look styled.

**Auto-reload while developing:** debug mode is off by default. Turn it on before starting the server:

- Windows PowerShell: `$env:FLASK_DEBUG="1"`
- macOS or Linux: `export FLASK_DEBUG=1`

## Routes

| Route | Description |
|-------|-------------|
| `/` | Web page with the shortener form |
| `POST /shorten` | Creates a short link from the form fields `url` and optional `alias`, and returns the code. Returns `400` for a missing or invalid URL or alias, and `409` if the alias is taken |
| `GET /report` | Page with a form to report a short link |
| `POST /report` | Saves a report from the form fields `link` (a short link or code) and optional `reason`. Returns `404` if the link doesn't exist. Rate limited |
| `/<code>` | Redirects to the original URL (`404` if the code doesn't exist or was removed) |

## Admin commands

Run these from the project folder to review reports and remove links. There is no admin page on the site.

```bash
python admin.py reports          # list open reports, grouped by link
python admin.py remove <code>    # hide a link; visits show "Link not found"
python admin.py dismiss <code>   # clear reports for a link you decided to keep
```

Removed links stay in the database, so their codes can't be registered again.

## Project structure

```
snipurlnk/
├── app.py          # Flask routes
├── shorten.py      # URL and alias validation, code generation, Postgres storage
├── admin.py        # Review reports and remove links from the terminal
├── templates/
│   ├── index.html  # Front end and page script
│   └── report.html # Report form
├── static/
│   └── style.css   # Layout and theme tweaks on top of Puppertino
└── README.md
```

## Roadmap

- [x] Core shorten/expand logic with collision handling
- [x] Flask web server with redirect route
- [x] SQLite storage
- [x] Basic front end
- [x] URL validation
- [x] Auto-add `https://` to URLs without a scheme
- [x] Decide duplicate-URL behavior (new link per submission)
- [x] Clear error messages on the page, and a clickable short link
- [x] Copy and Go buttons
- [x] Custom aliases
- [x] CSS styling (light and dark themes)
- [x] Click counts (stored per link, no display yet)
- [x] Deployment prep: switch `/shorten` to POST and turn off `debug=True`
- [x] Rate limiting per visitor
- [x] Report and remove links
- [x] Move from SQLite to a free hosted database (Postgres)
- [ ] Deploy on a free host
- [ ] User accounts and a dashboard showing each person's links and click counts
- [ ] Link expiry

## What I'm learning

Flask routing, HTTP status codes and redirects, SQL basics, moving from SQLite to Postgres, environment variables and keeping secrets out of Git, input validation with regular expressions and `urlparse`, error handling with try/except, DOM scripting in JavaScript, CSS theming, and Git/GitHub workflow.