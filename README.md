# snipURlnk

A URL shortener built with Python, Flask, and SQLite. I'm building it as a learning project, one step at a time.

## Features

- Shorten any URL into a random 6-character code
- Redirect from the short link to the original URL
- Links are stored in SQLite, so they survive server restarts
- Collision-safe code generation: a taken code is never overwritten
- URL validation: only `http` and `https` links with a real domain are accepted
- Auto-fixes missing schemes (`example.com` becomes `https://example.com`)
- Every submission creates its own new link, even for a URL that was shortened before
- Simple web page for creating links
- Proper error responses: `400` for missing or invalid URLs, `404` for unknown codes

## How it works

1. You submit a URL.
2. The server cleans it up: it trims whitespace and adds `https://` if no scheme is given.
3. It validates the result. The scheme must be `http` or `https`, and the hostname must contain a dot. Anything else is rejected with a `400`.
4. The server generates a random code (letters and digits) and saves the pair `code -> URL` in a SQLite table. The `code` column is a primary key, so the database itself refuses duplicates, and the server retries with a new code if one is taken.
5. When someone visits `/<code>`, the server looks up the code and redirects to the original URL. Unknown codes return a `404`.

### Design decision: one link per submission

Submitting the same URL twice creates two different short links. This keeps each person's link independent, and it makes per-link features (like click counts) possible later.

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
| `/shorten?url=...` | Creates a short link and returns the code (`400` if the URL is missing or invalid) |
| `/<code>` | Redirects to the original URL (`404` if the code doesn't exist) |

## Project structure

```
snipurlnk/
├── app.py          # Flask routes
├── shorten.py      # URL normalizing/validation, code generation, SQLite storage
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
- [ ] Clear error messages on the page, and a clickable short link
- [ ] Copy button
- [ ] CSS styling
- [ ] Custom aliases
- [ ] Click counts, link expiry, rate limiting
- [ ] Deployment

## What I'm learning

Flask routing, HTTP status codes and redirects, SQL basics, input validation, error handling with try/except, and Git/GitHub workflow.