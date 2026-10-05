from flask import Blueprint, redirect, render_template, session

from database import get_connection
from helpers import today_ist

dashboard = Blueprint("dashboard", __name__)


def _count(cursor, sql, params=()):
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return list(row.values())[0] if isinstance(row, dict) else row[0]


@dashboard.route("/dashboard")
def dashboard_page():

    if "user_name" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    # Real numbers from the database (these used to be hard-coded placeholders)
    stats = {
        "active_rides": _count(
            cursor,
            "SELECT COUNT(*) FROM rides WHERE status='Available' AND available_seats > 0 AND ride_date >= %s",
            (today_ist(),),
        ),
        "drivers": _count(cursor, "SELECT COUNT(*) FROM users WHERE role='Driver'"),
        "passengers": _count(cursor, "SELECT COUNT(*) FROM users WHERE role='Passenger'"),
        "bookings": _count(cursor, "SELECT COUNT(*) FROM bookings"),
    }
    conn.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        role=session["role"],
        stats=stats,
    )
