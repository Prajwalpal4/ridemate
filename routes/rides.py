from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session

from database import get_connection
from helpers import driver_required, login_required, now_ist, today_ist

rides = Blueprint("rides", __name__)

MAX_SEATS = 8


# -----------------------------
# FIND RIDES
# -----------------------------
@rides.route("/find-rides")
@login_required
def find_rides():
    conn = get_connection()
    cursor = conn.cursor()

    # Only upcoming rides with free seats (dates are stored as YYYY-MM-DD text, so a
    # plain string comparison is correct). Rides the logged-in user already booked or
    # owns are still listed; booking logic blocks the invalid cases with a message.
    cursor.execute(
        """
        SELECT *
        FROM rides
        WHERE status='Available'
        AND available_seats > 0
        AND ride_date >= %s
        ORDER BY ride_date ASC, ride_time ASC
        """,
        (today_ist(),),
    )
    rides_list = cursor.fetchall()
    conn.close()

    return render_template("find_rides.html", rides=rides_list)


# -----------------------------
# OFFER RIDE (drivers only)
# -----------------------------
@rides.route("/offer-ride", methods=["GET", "POST"])
@driver_required
def offer_ride():
    if request.method == "POST":
        from_location = request.form.get("from_location", "").strip()
        to_location = request.form.get("to_location", "").strip()
        ride_date = request.form.get("ride_date", "").strip()
        ride_time = request.form.get("ride_time", "").strip()
        vehicle_number = request.form.get("vehicle_number", "").strip().upper()

        error = None
        try:
            total_seats = int(request.form.get("seats", ""))
        except ValueError:
            total_seats = 0

        try:
            when = datetime.strptime(f"{ride_date} {ride_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            when = None

        if not (from_location and to_location and vehicle_number):
            error = "Please fill in all fields."
        elif from_location.lower() == to_location.lower():
            error = "Pickup and destination cannot be the same."
        elif when is None:
            error = "Please enter a valid date and time."
        elif when.replace(tzinfo=None) < now_ist().replace(tzinfo=None):
            error = "Ride date and time cannot be in the past."
        elif not 1 <= total_seats <= MAX_SEATS:
            error = f"Seats must be between 1 and {MAX_SEATS}."

        if error:
            flash(error)
            return redirect("/offer-ride")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rides (
                driver_id, driver_name,
                from_location, to_location,
                ride_date, ride_time,
                total_seats, available_seats,
                vehicle_number
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"], session["user_name"],
                from_location, to_location,
                ride_date, ride_time,
                total_seats, total_seats,
                vehicle_number,
            ),
        )
        conn.commit()
        conn.close()

        flash("Ride Posted Successfully!")
        return redirect("/offer-ride")

    return render_template("offer_ride.html")


# =========================================================
# MY RIDES (drivers)
# =========================================================
@rides.route("/my-rides")
@login_required
def my_rides():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, driver_name, from_location, to_location, ride_date, ride_time,
               total_seats, available_seats, vehicle_number, status
        FROM rides
        WHERE driver_id=%s
        ORDER BY id DESC
        """,
        (session["user_id"],),
    )
    my_rides_list = cursor.fetchall()
    conn.close()

    return render_template("my_rides.html", rides=my_rides_list)


# =========================================================
# CANCEL RIDE (driver cancels their own ride)
# =========================================================
@rides.route("/cancel-ride/<int:ride_id>", methods=["POST"])
@driver_required
def cancel_ride(ride_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # only the owner can cancel, and only if it is not already cancelled
        cursor.execute(
            """
            UPDATE rides SET status='Cancelled'
            WHERE id=%s AND driver_id=%s AND status<>'Cancelled'
            """,
            (ride_id, session["user_id"]),
        )
        if cursor.rowcount == 0:
            conn.rollback()
            flash("Ride not found or already cancelled.")
            return redirect("/my-rides")

        # tell every passenger with a live booking, then close those bookings
        cursor.execute(
            """
            SELECT users.email
            FROM bookings
            INNER JOIN users ON bookings.passenger_id = users.id
            WHERE bookings.ride_id=%s
            AND bookings.booking_status IN ('Pending', 'Accepted')
            """,
            (ride_id,),
        )
        for row in cursor.fetchall():
            cursor.execute(
                "INSERT INTO notifications (email, title, message, status) VALUES (%s, %s, %s, %s)",
                (row["email"], "Ride Cancelled",
                 "The driver has cancelled a ride you had booked.", "Unread"),
            )

        cursor.execute(
            """
            UPDATE bookings SET booking_status='Cancelled'
            WHERE ride_id=%s AND booking_status IN ('Pending', 'Accepted')
            """,
            (ride_id,),
        )
        conn.commit()
        flash("Ride cancelled. Passengers have been notified.")
    except Exception:
        conn.rollback()
        flash("Could not cancel the ride. Please try again.")
    finally:
        conn.close()

    return redirect("/my-rides")
