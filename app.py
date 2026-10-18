from flask import Flask, request, redirect, render_template
from shorten import shorten, expand, is_valid_url, normalize_url, is_valid_alias, record_click, add_report, init_db  
from werkzeug.middleware.proxy_fix import ProxyFix
from safety import is_flagged

app = Flask(__name__)

# Render puts 3 proxy addresses in X-Forwarded-For. Trust exactly those 3, so a
# visitor can't fake their address by sending their own header.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=3)

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

    result = shorten(url, alias or None)

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

@app.route("/<code>")
def follow_link(code):
    
    link = expand(code) 
   
    if link is None:
        return "Link not found", 404

    record_click(code)
    return redirect(link)

@app.errorhandler(429)
def too_many_requests(error):
    return "Too many requests. Please wait a minute and try again.", 429

if __name__ == "__main__":
    app.run()