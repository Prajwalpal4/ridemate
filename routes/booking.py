from flask import Blueprint, redirect, session, flash, render_template
from database import get_connection
from helpers import driver_required, login_required

booking = Blueprint("booking", __name__)


# =========================================================
# BOOK RIDE
# =========================================================

@booking.route("/book-ride/<int:ride_id>", methods=["POST"])
@login_required
def book_ride(ride_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rides WHERE id=%s", (ride_id,))
    ride = cursor.fetchone()

    if not ride or ride["status"] != "Available":
        conn.close()
        flash("Ride not found or no longer available.")
        return redirect("/find-rides")

    if ride["driver_id"] == session["user_id"]:
        conn.close()
        flash("You cannot book your own ride.")
        return redirect("/find-rides")

    if ride["available_seats"] <= 0:
        conn.close()
        flash("This ride is full.")
        return redirect("/find-rides")

    cursor.execute(
        "SELECT 1 FROM bookings WHERE ride_id=%s AND passenger_id=%s",
        (ride_id, session["user_id"]),
    )
    if cursor.fetchone():
        conn.close()
        flash("You have already booked this ride.")
        return redirect("/find-rides")

    try:
        cursor.execute(
            "INSERT INTO bookings (ride_id, passenger_id, booking_status) VALUES (%s, %s, %s)",
            (ride_id, session["user_id"], "Pending"),
        )

        # let the driver know there is a new request
        cursor.execute("SELECT email FROM users WHERE id=%s", (ride["driver_id"],))
        driver = cursor.fetchone()
        if driver:
            cursor.execute(
                "INSERT INTO notifications (email, title, message, status) VALUES (%s, %s, %s, %s)",
                (driver["email"], "New Booking Request",
                 session["user_name"] + " requested a seat on your ride to " + ride["to_location"] + ".",
                 "Unread"),
            )
        conn.commit()
        flash("Ride booked successfully! Waiting for the driver to accept.")
    except Exception:
        # the unique index rejects a duplicate booking even if two clicks race
        conn.rollback()
        flash("You have already booked this ride.")
    finally:
        conn.close()

    return redirect("/find-rides")


# =========================================================
# MY BOOKINGS
# =========================================================

@booking.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            bookings.id AS booking_id,
            bookings.booking_status,

            rides.id AS ride_id,
            rides.driver_name,
            rides.from_location,
            rides.to_location,
            rides.ride_date,
            rides.ride_time,
            rides.vehicle_number

        FROM bookings

        INNER JOIN rides
        ON bookings.ride_id = rides.id

        WHERE bookings.passenger_id=%s

        ORDER BY bookings.id DESC
        """,
        (
            session["user_id"],
        )
    )

    bookings = cursor.fetchall()

    conn.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# =========================================================
# CANCEL BOOKING
# =========================================================

@booking.route("/cancel-booking/<int:booking_id>", methods=["POST"])
@login_required
def cancel_booking(booking_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT ride_id, booking_status FROM bookings WHERE id=%s AND passenger_id=%s",
            (booking_id, session["user_id"]),
        )
        record = cursor.fetchone()

        if not record:
            flash("Booking not found.")
        elif record["booking_status"] not in ("Pending", "Accepted"):
            flash("This booking cannot be cancelled.")
        else:
            was_accepted = record["booking_status"] == "Accepted"

            cursor.execute(
                "DELETE FROM bookings WHERE id=%s AND passenger_id=%s AND booking_status IN ('Pending', 'Accepted')",
                (booking_id, session["user_id"]),
            )

            # A seat is only taken when the driver ACCEPTS, so only an accepted
            # booking gives a seat back. (Pending bookings never reduced seats.)
            if was_accepted and cursor.rowcount == 1:
                cursor.execute(
                    """
                    UPDATE rides
                    SET available_seats = available_seats + 1
                    WHERE id=%s AND available_seats < total_seats
                    """,
                    (record["ride_id"],),
                )
            conn.commit()
            flash("Booking cancelled successfully.")
    except Exception:
        conn.rollback()
        flash("Could not cancel the booking. Please try again.")
    finally:
        conn.close()

    return redirect("/my-bookings")


# =========================================================
# DRIVER BOOKING REQUESTS
# =========================================================

@booking.route("/driver-requests")
@driver_required
def driver_requests():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            bookings.id AS booking_id,
            bookings.booking_status,

            rides.id AS ride_id,
            rides.from_location,
            rides.to_location,
            rides.ride_date,
            rides.ride_time,
            rides.vehicle_number,

            users.id AS passenger_id,
            users.full_name AS passenger_name

        FROM bookings

        INNER JOIN rides
        ON bookings.ride_id = rides.id

        INNER JOIN users
        ON bookings.passenger_id = users.id

        WHERE rides.driver_id=%s

        ORDER BY bookings.id DESC
        """,
        (
            session["user_id"],
        )
    )

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "driver_requests.html",
        requests=requests
    )


# =========================================================
# ACCEPT BOOKING
# =========================================================

@booking.route("/accept-booking/<int:booking_id>", methods=["POST"])
@driver_required
def accept_booking(booking_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT bookings.ride_id, bookings.booking_status, bookings.passenger_id,
                   rides.driver_id, rides.to_location
            FROM bookings
            INNER JOIN rides ON bookings.ride_id = rides.id
            WHERE bookings.id=%s
            """,
            (booking_id,),
        )
        record = cursor.fetchone()

        if not record:
            flash("Booking request not found.")
        elif record["driver_id"] != session["user_id"]:
            flash("You are not authorized to manage this booking.")
        elif record["booking_status"] != "Pending":
            flash("Only pending requests can be accepted.")
        else:
            # Step 1: take a seat ONLY if one is still free. Doing the check inside the
            # UPDATE itself makes it atomic, so two quick accepts can never overbook.
            cursor.execute(
                """
                UPDATE rides SET available_seats = available_seats - 1
                WHERE id=%s AND available_seats > 0 AND status='Available'
                """,
                (record["ride_id"],),
            )
            if cursor.rowcount == 0:
                conn.rollback()
                flash("No seats are available.")
            else:
                # Step 2: mark the booking accepted (only if it is still Pending)
                cursor.execute(
                    "UPDATE bookings SET booking_status='Accepted' WHERE id=%s AND booking_status='Pending'",
                    (booking_id,),
                )
                if cursor.rowcount == 0:
                    conn.rollback()
                    flash("This request was already handled.")
                else:
                    cursor.execute("SELECT email FROM users WHERE id=%s", (record["passenger_id"],))
                    passenger = cursor.fetchone()
                    if passenger:
                        cursor.execute(
                            "INSERT INTO notifications (email, title, message, status) VALUES (%s, %s, %s, %s)",
                            (passenger["email"], "Ride Booking Accepted",
                             "Your ride booking has been accepted by the driver.", "Unread"),
                        )
                    conn.commit()
                    flash("Booking accepted successfully.")
    except Exception:
        conn.rollback()
        flash("Could not accept the booking. Please try again.")
    finally:
        conn.close()

    return redirect("/driver-requests")


# =========================================================
# REJECT BOOKING
# =========================================================

@booking.route("/reject-booking/<int:booking_id>", methods=["POST"])
@driver_required
def reject_booking(booking_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT bookings.booking_status, bookings.passenger_id, rides.driver_id
            FROM bookings
            INNER JOIN rides ON bookings.ride_id = rides.id
            WHERE bookings.id=%s
            """,
            (booking_id,),
        )
        record = cursor.fetchone()

        if not record:
            flash("Booking request not found.")
        elif record["driver_id"] != session["user_id"]:
            flash("You are not authorized to manage this booking.")
        elif record["booking_status"] != "Pending":
            flash("Only pending requests can be rejected.")
        else:
            cursor.execute(
                "UPDATE bookings SET booking_status='Rejected' WHERE id=%s AND booking_status='Pending'",
                (booking_id,),
            )
            if cursor.rowcount == 0:
                conn.rollback()
                flash("This request was already handled.")
            else:
                cursor.execute("SELECT email FROM users WHERE id=%s", (record["passenger_id"],))
                passenger = cursor.fetchone()
                if passenger:
                    cursor.execute(
                        "INSERT INTO notifications (email, title, message, status) VALUES (%s, %s, %s, %s)",
                        (passenger["email"], "Ride Booking Rejected",
                         "Your ride booking request was rejected by the driver.", "Unread"),
                    )
                conn.commit()
                flash("Booking rejected.")
    except Exception:
        conn.rollback()
        flash("Could not reject the booking. Please try again.")
    finally:
        conn.close()

    return redirect("/driver-requests")


# =========================================================
# GET PENDING BOOKING COUNT
# =========================================================

def get_pending_booking_count(driver_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS pending_count

        FROM bookings

        INNER JOIN rides
        ON bookings.ride_id = rides.id

        WHERE rides.driver_id=%s
        AND bookings.booking_status='Pending'
        """,
        (
            driver_id,
        )
    )

    result = cursor.fetchone()

    conn.close()

    return result["pending_count"]