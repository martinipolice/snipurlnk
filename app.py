import os
from datetime import timedelta

import requests
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.flask_client import OAuth
from flask import Flask, request, redirect, render_template, abort, session, url_for, make_response
from shorten import shorten, expand, is_valid_url, normalize_url, is_valid_alias, record_click, add_report, init_db, upsert_user, get_user, list_links
from werkzeug.middleware.proxy_fix import ProxyFix
from safety import is_flagged

app = Flask(__name__)

# Render puts 3 proxy addresses in X-Forwarded-For. Trust exactly those 3, so a
# visitor can't fake their address by sending their own header.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3)

# --- login with GitHub ---
app.secret_key = os.environ.get("SECRET_KEY")  # signs the login cookie so it can't be edited
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # page scripts can't read the cookie
    SESSION_COOKIE_SAMESITE="Lax",  # other sites can't make your browser send it with a form post
    SESSION_COOKIE_SECURE=os.environ.get("RENDER") == "true",  # Render sets RENDER=true; plain http on your own computer can't use Secure cookies
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

oauth = OAuth(app)
oauth.register(
    name="github",
    client_id=os.environ.get("GITHUB_CLIENT_ID"),
    client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
)


def login_is_set_up():
    github = oauth.github
    return bool(app.secret_key and github.client_id and github.client_secret)

init_db() # make sure the tables exist before serving requests

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)

@app.route("/")
def home():
    return render_template("index.html")

@app.context_processor
def add_current_user():
    # makes `current_user` available in every template: (id, username), or None if nobody is logged in
    user_id = session.get("user_id")
    return {"current_user": get_user(user_id) if user_id else None}

@app.route("/shorten", methods=["POST"])
@limiter.limit("10 per minute")
@limiter.limit("100 per day")
def create_short_link():
    url = request.form.get("url", "").strip()
    alias = request.form.get("alias", "").strip()
    
    if not url:
        return "Missing url", 400

    url = normalize_url(url)
    
    if not is_valid_url(url):
        return "Invalid URL", 400

    if alias and not is_valid_alias(alias):  # the alias is not valid
        return "Invalid alias", 400

    if is_flagged(url):
        return "This link was flagged as unsafe by Google Safe Browsing, so it can't be shortened.", 400

    owner_id = None
    user_id = session.get("user_id")
    if user_id:
        user = get_user(user_id)  # the cookie could point at a user that no longer exists
        owner_id = user[0] if user else None

    result = shorten(url, alias or None, owner_id)

    if result is None:
        return "Alias already taken", 409

    return result


@app.route("/report")
def report_page():
    return render_template("report.html")

@app.route("/report", methods=["POST"])
@limiter.limit("5 per minute")
@limiter.limit("20 per day")
def submit_report():
    link = request.form.get("link", "").strip()
    reason = request.form.get("reason", "")

    if not link:
        return "Missing link", 400

    if add_report(link, reason) is None:
        return "Link not found", 404

    return "Thanks, we'll review it."

@app.route("/login")
def login():
    if not login_is_set_up():
        return "Login is not set up on this server.", 503
    return oauth.github.authorize_redirect(url_for("github_callback", _external=True))


@app.route("/login/github/callback")
def github_callback():
    if not login_is_set_up():
        return "Login is not set up on this server.", 503
    try:
        token = oauth.github.authorize_access_token()  # also checks the 'state' value, which blocks forged logins
        profile = oauth.github.get("user", token=token).json()
        user_id = upsert_user(profile.get("id"), profile.get("login"))
    except (OAuthError, requests.RequestException, ValueError, AttributeError):
        return "Login failed. Please go back and try again.", 400
    session.clear()  # start from a clean session, so nothing planted earlier survives the login
    session.permanent = True
    session["user_id"] = user_id
    return redirect("/")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/", code=303)

DASHBOARD_LIMIT = 200


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    user = get_user(user_id) if user_id else None
    if user is None:
        return redirect(url_for("login"))
    response = make_response(render_template("dashboard.html", links=list_links(user[0], DASHBOARD_LIMIT), limit=DASHBOARD_LIMIT))
    response.headers["Cache-Control"] = "private, no-store"  # a personal page: never keep a copy where someone else could see it
    return response

@app.route("/<code>")
def follow_link(code):
    
    link = expand(code) 
   
    if link is None:
        abort(404)

    record_click(code)
    return redirect(link)

@app.errorhandler(429)
def too_many_requests(error):
    return "Too many requests. Please wait a minute and try again.", 429

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run()