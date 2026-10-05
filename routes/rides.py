from flask import Blueprint, render_template, request, redirect, session, flash
from database import get_connection

rides = Blueprint("rides", __name__)


# -----------------------------
# FIND RIDES
# -----------------------------
@rides.route("/find-rides")
def find_rides():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM rides
        WHERE status='Available'
        AND available_seats > 0
        ORDER BY id DESC
    """)

    rides_list = cursor.fetchall()

    conn.close()

    return render_template(
        "find_rides.html",
        rides=rides_list
    )


# -----------------------------
# OFFER RIDE
# -----------------------------
@rides.route("/offer-ride", methods=["GET", "POST"])
def offer_ride():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        from_location = request.form["from_location"]
        to_location = request.form["to_location"]
        ride_date = request.form["ride_date"]
        ride_time = request.form["ride_time"]

        total_seats = int(request.form["seats"])

        vehicle_number = request.form["vehicle_number"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO rides (

                driver_id,
                driver_name,

                from_location,
                to_location,

                ride_date,
                ride_time,

                total_seats,
                available_seats,

                vehicle_number

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)

        """, (

            session["user_id"],
            session["user_name"],

            from_location,
            to_location,

            ride_date,
            ride_time,

            total_seats,
            total_seats,

            vehicle_number

        ))

        conn.commit()

        conn.close()

        flash("Ride Posted Successfully!")

        return redirect("/offer-ride")

    return render_template("offer_ride.html")

# =========================================================
# MY RIDES
# =========================================================

@rides.route("/my-rides")
def my_rides():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            driver_name,
            from_location,
            to_location,
            ride_date,
            ride_time,
            total_seats,
            available_seats,
            vehicle_number,
            status

        FROM rides

        WHERE driver_id=%s

        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    )

    my_rides_list = cursor.fetchall()

    conn.close()

    return render_template(
        "my_rides.html",
        rides=my_rides_list
    )