from flask import Flask, render_template
import json
import mysql.connector

app = Flask(__name__)

with open("config.json", "r") as f:
    params = json.load(f)

mysql_config = {
    'host': params["db_url"],
    'user': "root",
    'password': "",
    'database': params["db_name"],
}

conn = mysql.connector.connect(**mysql_config)


@app.route("/")
def index():
    # Create a cursor
    cursor = conn.cursor()
    query = "SELECT * FROM courses ORDER BY entry_date"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return render_template("index.html", params=params, data=results)


@app.route("/contact_us")
def contact_us():
    return render_template("contact_us.html", params=params)


if __name__ == "__main__":
    app.run(debug=True)
