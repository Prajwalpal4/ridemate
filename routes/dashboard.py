from flask import Blueprint, render_template, session, redirect

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def dashboard_page():

    if "user_name" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        role=session["role"]
    )