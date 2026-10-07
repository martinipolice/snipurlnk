from flask import Flask, request, redirect, render_template
from shorten import shorten, expand   # use YOUR filename instead of "shortener"

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/shorten")
def create_short_link():
    url = request.args.get("url", "").strip()
    
    if not url:
        return "Missing url", 400
    return shorten(url)

@app.route("/<code>")
def follow_link(code):
    
    link = expand(code)
   
    if link is None:
        return "Link not found", 404
    
    return redirect(link)

if __name__ == "__main__":
    app.run(debug=True)