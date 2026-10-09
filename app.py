from flask import Flask, request, redirect, render_template
from shorten import shorten, expand, is_valid_url, normalize_url, is_valid_alias   # use YOUR filename instead of "shortener"



app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/shorten")
def create_short_link():
    url = request.args.get("url", "").strip()
    alias = request.args.get("alias", "").strip()
    
    if not url:
        return "Missing url", 400

    url = normalize_url(url)
    
    if not is_valid_url(url):
        return "Invalid URL", 400

    if alias and not is_valid_alias(alias):  # the alias is not valid
        return "Invalid alias", 400

    result = shorten(url, alias or None)

    if result is None:
        return "Alias already taken", 409

    return result


@app.route("/<code>")
def follow_link(code):
    
    link = expand(code)
   
    if link is None:
        return "Link not found", 404
    
    return redirect(link)

if __name__ == "__main__":
    app.run(debug=True)