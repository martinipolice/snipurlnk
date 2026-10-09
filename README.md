# snipURlnk

A URL shortener built with Python, Flask, and SQLite. I'm building it as a learning project, one step at a time.

## Features

- Shorten any URL into a random 6-character code
- Optional custom aliases (3 to 30 characters: letters, digits, `-` and `_`), case-insensitive, with a list of reserved words
- Redirect from the short link to the original URL
- Links are stored in SQLite, so they survive server restarts
- Collision-safe code generation: a taken code is never overwritten
- URL validation: only `http` and `https` links with a real domain are accepted
- Auto-fixes missing schemes (`example.com` becomes `https://example.com`)
- Every submission creates its own new link, even for a URL that was shortened before
- Simple web page with clear error messages, plus Copy and Go buttons next to the short link
- Proper error responses: `400` for missing or invalid input, `404` for unknown codes, `409` for a taken alias

## How it works

1. You submit a URL, and optionally a custom alias.
2. The server cleans up the URL: it trims whitespace and adds `https://` if no scheme is given.
3. It validates the URL. The scheme must be `http` or `https`, and the hostname must contain a dot. Anything else is rejected with a `400`.
4. If an alias was given, it must match the allowed pattern and not be a reserved word (like `admin` or `login`), or the server returns a `400`.
5. The server saves the pair `code -> URL` in a SQLite table.
   - With an alias, it tries to insert that code once. If it's taken, the server returns a `409`.
   - Without one, it generates a random code and retries with a new one if there's a collision.
6. When someone visits `/<code>`, the server looks up the code and redirects to the original URL. Unknown codes return a `404`.

### Design decisions

- **One link per submission:** submitting the same URL twice creates two different short links. This keeps each person's link independent, and it makes per-link features (like click counts) possible later.
- **Case-insensitive codes:** the `code` column uses `COLLATE NOCASE`, so `MySite` and `mysite` are the same link. This prevents lookalike links from being registered by different people.

## Getting started

**Requirements:** Python 3.

```bash
git clone https://github.com/martinipolice/snipurlnk.git
cd snipurlnk
pip install flask
python app.py
```

Then open http://127.0.0.1:5000 in your browser. The database file (`links.db`) is created automatically on first run.

## Routes

| Route | Description |
|-------|-------------|
| `/` | Web page with the shortener form |
| `/shorten?url=...&alias=...` | Creates a short link and returns the code. `alias` is optional. Returns `400` for a missing or invalid URL or alias, and `409` if the alias is taken |
| `/<code>` | Redirects to the original URL (`404` if the code doesn't exist) |

## Project structure

```
snipurlnk/
├── app.py          # Flask routes
├── shorten.py      # URL and alias validation, code generation, SQLite storage
├── templates/
│   └── index.html  # Front end
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
- [ ] CSS styling
- [ ] Click counts, link expiry, rate limiting
- [ ] Deployment

## What I'm learning

Flask routing, HTTP status codes and redirects, SQL basics, input validation with regular expressions, error handling with try/except, DOM scripting in JavaScript, and Git/GitHub workflow.