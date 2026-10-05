from flask import Blueprint, render_template, redirect, session, request, jsonify
from database import get_connection

tracking = Blueprint("tracking", __name__)


def _get_booking_for_user(booking_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            bookings.id AS booking_id,
            bookings.booking_status,
            bookings.passenger_id,
            rides.id AS ride_id,
            rides.driver_id,
            rides.driver_name,
            rides.from_location,
            rides.to_location,
            rides.ride_date,
            rides.ride_time,
            rides.vehicle_number,
            users.email AS passenger_email,
            users.full_name AS passenger_name
        FROM bookings
        INNER JOIN rides ON bookings.ride_id = rides.id
        INNER JOIN users ON bookings.passenger_id = users.id
        WHERE bookings.id=%s
        """,
        (booking_id,)
    )
    ride = cursor.fetchone()
    conn.close()

    if not ride:
        return None

    # Passenger can view their own accepted booking.
    # Driver can update/view location only for their own ride.
    if ride["passenger_id"] != user_id and ride["driver_id"] != user_id:
        return None

    if ride["booking_status"] != "Accepted":
        return None

    return ride


@tracking.route("/ride-tracking/<int:booking_id>")
def ride_tracking(booking_id):
    if "user_id" not in session:
        return redirect("/login")

    ride = _get_booking_for_user(booking_id, session["user_id"])

    if not ride:
        return redirect("/my-bookings")

    return render_template("ride_tracking.html", ride=ride)


@tracking.route("/api/ride-location/<int:booking_id>", methods=["GET"])
def get_ride_location(booking_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"}), 401

    ride = _get_booking_for_user(booking_id, session["user_id"])
    if not ride:
        return jsonify({"success": False, "message": "Ride not available"}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT latitude, longitude, accuracy, updated_at
        FROM ride_locations
        WHERE booking_id=%s
        """,
        (booking_id,)
    )
    location = cursor.fetchone()
    conn.close()

    if not location:
        return jsonify({"success": True, "location": None})

    return jsonify({
        "success": True,
        "location": dict(location)
    })


@tracking.route("/api/ride-location/<int:booking_id>", methods=["POST"])
def update_ride_location(booking_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"}), 401

    ride = _get_booking_for_user(booking_id, session["user_id"])
    if not ride:
        return jsonify({"success": False, "message": "Ride not available"}), 403

    # Only the driver assigned to this ride may publish GPS updates.
    if ride["driver_id"] != session["user_id"]:
        return jsonify({"success": False, "message": "Driver access required"}), 403

    data = request.get_json(silent=True) or {}
    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        accuracy = float(data.get("accuracy", 0)) if data.get("accuracy") is not None else None
    except (KeyError, TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid location"}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({"success": False, "message": "Invalid coordinates"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # PostgreSQL and SQLite-compatible upsert.
    # PostgreSQL uses ON CONFLICT; SQLite also supports it in modern versions.
    cursor.execute(
        """
        INSERT INTO ride_locations
            (booking_id, driver_id, latitude, longitude, accuracy, updated_at)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT(booking_id) DO UPDATE SET
            driver_id=excluded.driver_id,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            accuracy=excluded.accuracy,
            updated_at=CURRENT_TIMESTAMP
        """,
        (booking_id, session["user_id"], latitude, longitude, accuracy)
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@tracking.route("/send-sos", methods=["POST"])
def send_sos():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"}), 401

    data = request.get_json(silent=True) or {}
    try:
        booking_id = int(data["booking_id"])
        latitude = float(data["latitude"]) if data.get("latitude") is not None else None
        longitude = float(data["longitude"]) if data.get("longitude") is not None else None
    except (KeyError, TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid SOS data"}), 400

    ride = _get_booking_for_user(booking_id, session["user_id"])
    if not ride or ride["passenger_id"] != session["user_id"]:
        return jsonify({"success": False, "message": "Booking access denied"}), 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO emergency_alerts
            (booking_id, passenger_id, latitude, longitude, message)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            booking_id,
            session["user_id"],
            latitude,
            longitude,
            "Emergency SOS",
        )
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "SOS alert recorded"})


@tracking.route("/api/driver-booking/<int:booking_id>")
def driver_booking_status(booking_id):
    """Small endpoint used by the driver's tracking page/JS."""
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Login required"}), 401

    ride = _get_booking_for_user(booking_id, session["user_id"])
    if not ride or ride["driver_id"] != session["user_id"]:
        return jsonify({"success": False, "message": "Driver access required"}), 403

    return jsonify({"success": True, "booking_id": booking_id})
