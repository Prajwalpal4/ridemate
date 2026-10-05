from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_connection

auth = Blueprint("auth", __name__)


@auth.route("/")
def home():
    return render_template("index.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

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

        full_name = request.form["full_name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        department = request.form["department"]
        year = request.form["year"]
        role = request.form["role"]
        password = generate_password_hash(request.form["password"])

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (full_name, student_id, email, department, year, role, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                full_name,
                student_id,
                email,
                department,
                year,
                role,
                password
            ))

            conn.commit()

            flash("Registration Successful!")

            return redirect("/login")

        except:

            flash("Student ID or Email already exists!")

        finally:

            conn.close()

    return render_template("register.html")


@auth.route("/logout")
def logout():

    session.clear()

    return redirect("/")