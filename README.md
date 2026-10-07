# snipURlnk

A URL shortener built with Python, Flask, and SQLite. I'm building it as a learning project, one step at a time.

## Features

- Shorten any URL into a random 6-character code
- Redirect from the short link to the original URL
- Links are stored in SQLite, so they survive server restarts
- Collision-safe code generation: a taken code is never overwritten
- Simple web page for creating links
- Rejects empty URLs, and returns proper 400 and 404 responses

## How it works

1. You submit a long URL.
2. The server generates a random code (letters and digits) and saves the pair `code -> URL` in a SQLite table. The `code` column is a primary key, so the database itself refuses duplicates, and the server retries with a new code if one is taken.
3. When someone visits `/<code>`, the server looks up the code and sends back a redirect to the original URL. Unknown codes return a 404.

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
| `/shorten?url=...` | Creates a short link and returns the code |
| `/<code>` | Redirects to the original URL |

## Project structure

```
snipurlnk/
├── app.py          # Flask routes
├── shorten.py      # Code generation and SQLite storage
├── templates/
│   └── index.html  # Front end
└── README.md
```

## Roadmap

- [x] Core shorten/expand logic with collision handling
- [x] Flask web server with redirect route
- [x] SQLite storage
- [x] Basic front end
- [ ] URL validation (require http/https, handle bad input)
- [ ] Custom aliases
- [ ] Reuse the existing code when the same URL is submitted again
- [ ] Click counts, link expiry, rate limiting
- [ ] Deployment

## What I'm learning

Flask routing, HTTP status codes and redirects, SQL basics, error handling with try/except, and Git/GitHub workflow.