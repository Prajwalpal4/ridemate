from flask import Blueprint, render_template, redirect, session, request, jsonify
from database import get_connection

ride_complete = Blueprint("ride_complete", __name__)


@ride_complete.route("/ride-complete/<int:booking_id>")
def ride_completed(booking_id):

    if "user_email" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            bookings.id AS booking_id,
            bookings.booking_status,

            rides.id AS ride_id,
            rides.driver_id,
            rides.driver_name,
            rides.from_location,
            rides.to_location,
            rides.ride_date,
            rides.ride_time,
            rides.vehicle_number,

            users.id AS passenger_id,
            users.email AS passenger_email,
            users.full_name AS passenger_name

        FROM bookings

        INNER JOIN rides
            ON bookings.ride_id = rides.id

        INNER JOIN users
            ON bookings.passenger_id = users.id

        WHERE bookings.id=%s
        """,
        (booking_id,)
    )

    ride = cursor.fetchone()

    if not ride:
        conn.close()
        return redirect("/my-bookings")

    if ride["booking_status"] != "Accepted":
        conn.close()
        return redirect("/my-bookings")

    if ride["passenger_email"] != session["user_email"]:
        conn.close()
        return redirect("/my-bookings")

    # Check whether passenger already rated this ride
    cursor.execute(
        """
        SELECT rating
        FROM ratings
        WHERE booking_id=%s
        """,
        (booking_id,)
    )

    existing_rating = cursor.fetchone()

    conn.close()

    return render_template(
        "ride_complete.html",
        ride=ride,
        existing_rating=existing_rating
    )


@ride_complete.route("/submit-rating", methods=["POST"])
def submit_rating():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    booking_id = data.get("booking_id")
    rating = data.get("rating")

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid rating."
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5."
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Verify booking
    cursor.execute(
        """
        SELECT
            bookings.id,
            bookings.booking_status,
            bookings.passenger_id,
            rides.id AS ride_id,
            rides.driver_id
        FROM bookings
        INNER JOIN rides
            ON bookings.ride_id = rides.id
        WHERE bookings.id=%s
        """,
        (booking_id,)
    )

    booking = cursor.fetchone()

    if not booking:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Booking not found."
        }), 404

    # Make sure the logged-in passenger owns this booking
    if booking["passenger_id"] != session["user_id"]:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Unauthorized request."
        }), 403

    if booking["booking_status"] != "Accepted":
        conn.close()

        return jsonify({
            "success": False,
            "message": "This ride is not completed."
        }), 400

    # Prevent duplicate rating
    cursor.execute(
        """
        SELECT id
        FROM ratings
        WHERE booking_id=%s
        """,
        (booking_id,)
    )

    already_rated = cursor.fetchone()

    if already_rated:
        conn.close()

        return jsonify({
            "success": False,
            "message": "You have already rated this ride."
        }), 400

    # Save rating
    cursor.execute(
        """
        INSERT INTO ratings
        (
            booking_id,
            ride_id,
            passenger_id,
            driver_id,
            rating
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            booking_id,
            booking["ride_id"],
            booking["passenger_id"],
            booking["driver_id"],
            rating
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Rating submitted successfully!"
    })