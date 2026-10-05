import re

from flask import Blueprint, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection

auth = Blueprint("auth", __name__)

VALID_ROLES = ("Driver", "Passenger")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth.route("/")
def home():
    return render_template("index.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email)=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()                      # drop any old session data / token
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_email"] = user["email"]
            session["role"] = user["role"]
            flash("Login Successful!")
            return redirect("/dashboard")

        flash("Invalid Email or Password")

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        student_id = request.form.get("student_id", "").strip()
        email = request.form.get("email", "").strip().lower()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # ---- server-side validation (browser checks can be bypassed)
        error = None
        if not all([full_name, student_id, email, department, year, role, password]):
            error = "Please fill in all fields."
        elif not EMAIL_RE.match(email):
            error = "Please enter a valid email address."
        elif role not in VALID_ROLES:
            error = "Please choose a valid role."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm:
            error = "Passwords do not match."

        if error:
            flash(error)
            return render_template("register.html")

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM users WHERE LOWER(email)=%s OR student_id=%s",
                (email, student_id),
            )
            if cursor.fetchone():
                flash("Student ID or Email already exists!")
            else:
                cursor.execute(
                    """
                    INSERT INTO users
                    (full_name, student_id, email, department, year, role, password)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (full_name, student_id, email, department, year, role,
                     generate_password_hash(password)),
                )
                conn.commit()
                flash("Registration Successful! Please log in.")
                return redirect("/login")
        except Exception:
            conn.rollback()
            flash("Could not register right now. Please try again.")
        finally:
            conn.close()

    return render_template("register.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
