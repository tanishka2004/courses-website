from flask import Flask, render_template
import json

app = Flask(__name__)

with open("config.json", "r") as f:
    params = json.load(f)


@app.route("/")
def index():
    return render_template("index.html", params=params)


app.run(debug=True)
