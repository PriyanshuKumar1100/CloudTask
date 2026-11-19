import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "cloudtask-development-secret"

DATABASE = os.environ.get("DATABASE_PATH", "cloudtask.db")


# Database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# Login protection
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# Home page
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or len(password) < 6:
            flash("Enter a username and password of at least 6 characters.")
            return redirect(url_for("register"))

        conn = get_db()

        try:
            hashed = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
        finally:
            conn.close()

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)


# Add task
@app.route("/add", methods=["POST"])
@login_required
def add_task():
    title = request.form["title"].strip()
    description = request.form.get("description", "").strip()

    if title:
        conn = get_db()
        conn.execute(
            "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
            (session["user_id"], title, description)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("dashboard"))


# Update task status
@app.route("/update/<int:task_id>", methods=["POST"])
@login_required
def update_task(task_id):
    status = request.form["status"]

    if status not in ["Pending", "In Progress", "Completed"]:
        return "Invalid status", 400

    conn = get_db()
    conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?",
        (status, task_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# Delete task
@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Initialize database when application starts
init_db()


if __name__ == "__main__":
    app.run(debug=True)
