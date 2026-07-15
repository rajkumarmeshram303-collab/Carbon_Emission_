from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import os
from flask import flash
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)
FILE_NAME = "carbon_data.csv"

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/result")
def result_page():
    return render_template("result.html")

@app.route("/save", methods=["POST"])
def save_data():
    data = request.get_json()

    df = pd.DataFrame([data])

    if os.path.exists(FILE_NAME):
        df.to_csv(FILE_NAME, mode="a", header=False, index=False)
    else:
        df.to_csv(FILE_NAME, index=False)

    print("Saved:", data)

    return jsonify({"message": "Saved successfully"})
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            credits INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

init_db()
@app.route("/add-credit", methods=["POST"])
def add_credit():

    if "user_id" not in session:
        return jsonify({"success": False})

    data = request.json
    credit = float(data.get("credit", 0))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT credits FROM users WHERE id = ?", (session["user_id"],))
    current = cursor.fetchone()[0]

    new_total = current + credit

    cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_total, session["user_id"]))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "totalCredits": new_total
    })
@app.route("/credits")
def get_credits():

    if "user_id" not in session:
        return jsonify({"loggedIn": False})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT credits FROM users WHERE id = ?", (session["user_id"],))
    credits = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "loggedIn": True,
        "credits": credits
    })


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]
        flash("Login Successful ✅")
        return redirect("/")
    else:
        flash("Invalid Username or Password ❌")
        return redirect("/login")

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Please fill all fields ❗")
        return redirect("/signup")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        flash("Signup Successful ✅ Please Login")
        return redirect("/login")

    except sqlite3.IntegrityError:
        conn.close()
        flash("Username already exists ❌")
        return redirect("/signup")

#========================================Regression model =================================
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib.pyplot as plt
@app.route("/analysis", methods=["POST"])
def analysis():
    data = request.get_json()
    distance = float(data["distance"])

    factors = {
        "car": 0.192,
        "bus": 0.082,
        "train": 0.020,
        "bike": 0.045,
        "metro": 0.040
    }

    predictions = {}
    for v in factors:
        predictions[v] = round(distance * factors[v], 2)

    best_vehicle = min(predictions, key=predictions.get)
    best_emission = predictions[best_vehicle]

    return jsonify({
        "predictions": predictions,
        "best_vehicle": best_vehicle,
        "best_emission": best_emission
    })

if __name__ == "__main__":
    app.run(debug=True)

