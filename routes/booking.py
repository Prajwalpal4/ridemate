from flask import Blueprint, redirect, session, flash, render_template
from database import get_connection

booking = Blueprint("booking", __name__)


# =========================================================
# BOOK RIDE
# =========================================================

@booking.route("/book-ride/<int:ride_id>")
def book_ride(ride_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM rides
        WHERE id=%s
        """,
        (ride_id,)
    )

    ride = cursor.fetchone()

    if not ride:
        conn.close()
        flash("Ride not found.")
        return redirect("/find-rides")

    # Driver cannot book own ride
    if ride["driver_id"] == session["user_id"]:
        conn.close()
        flash("You cannot book your own ride.")
        return redirect("/find-rides")

    # Check available seats
    if ride["available_seats"] <= 0:
        conn.close()
        flash("This ride is full.")
        return redirect("/find-rides")

    # Check duplicate booking
    cursor.execute(
        """
        SELECT *
        FROM bookings
        WHERE ride_id=%s
        AND passenger_id=%s
        """,
        (
            ride_id,
            session["user_id"]
        )
    )

    existing_booking = cursor.fetchone()

    if existing_booking:
        conn.close()
        flash("You have already booked this ride.")
        return redirect("/find-rides")

    # Create booking
    cursor.execute(
        """
        INSERT INTO bookings
        (
            ride_id,
            passenger_id,
            booking_status
        )
        VALUES (%s, %s, %s)
        """,
        (
            ride_id,
            session["user_id"],
            "Pending"
        )
    )

    conn.commit()
    conn.close()

    flash("Ride booked successfully!")

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

@booking.route("/cancel-booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *

        FROM bookings

        WHERE id=%s
        AND passenger_id=%s
        """,
        (
            booking_id,
            session["user_id"]
        )
    )

    booking_record = cursor.fetchone()

    if not booking_record:
        conn.close()
        flash("Booking not found.")
        return redirect("/my-bookings")

    if booking_record["booking_status"] not in (
        "Pending",
        "Accepted"
    ):
        conn.close()
        flash("This booking cannot be cancelled.")
        return redirect("/my-bookings")

    ride_id = booking_record["ride_id"]

    # Delete booking
    cursor.execute(
        """
        DELETE FROM bookings
        WHERE id=%s
        """,
        (booking_id,)
    )

    # Restore seat
    cursor.execute(
        """
        UPDATE rides

        SET available_seats =
            CASE

                WHEN available_seats < total_seats
                THEN available_seats + 1

                ELSE total_seats

            END

        WHERE id=%s
        """,
        (ride_id,)
    )

    conn.commit()
    conn.close()

    flash("Booking cancelled successfully.")

    return redirect("/my-bookings")


# =========================================================
# DRIVER BOOKING REQUESTS
# =========================================================

@booking.route("/driver-requests")
def driver_requests():

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

@booking.route("/accept-booking/<int:booking_id>")
def accept_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            bookings.id,
            bookings.ride_id,
            bookings.booking_status,

            rides.driver_id,
            rides.available_seats

        FROM bookings

        INNER JOIN rides
        ON bookings.ride_id = rides.id

        WHERE bookings.id=%s
        """,
        (
            booking_id,
        )
    )

    record = cursor.fetchone()

    if not record:
        conn.close()
        flash("Booking request not found.")
        return redirect("/driver-requests")

    # Driver security check
    if record["driver_id"] != session["user_id"]:
        conn.close()
        flash("You are not authorized to manage this booking.")
        return redirect("/driver-requests")

    if record["booking_status"] == "Accepted":
        conn.close()
        flash("This booking is already accepted.")
        return redirect("/driver-requests")

    if record["booking_status"] == "Rejected":
        conn.close()
        flash("This booking has already been rejected.")
        return redirect("/driver-requests")

    if record["available_seats"] <= 0:
        conn.close()
        flash("No seats are available.")
        return redirect("/driver-requests")

    # Accept booking
    cursor.execute(
        """
        UPDATE bookings

        SET booking_status='Accepted'

        WHERE id=%s
        """,
        (
            booking_id,
        )
    )
    
    # Get passenger email
    cursor.execute(
        """
        SELECT users.email
        FROM bookings
        
        INNER JOIN users
        ON bookings.passenger_id = users.id
        
        WHERE bookings.id=%s
        """,
        (
           booking_id,
        )
    )
    

    passenger = cursor.fetchone()

    if passenger:

     cursor.execute(
        """
        INSERT INTO notifications
        (
            email,
            title,
            message,
            status
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            passenger["email"],
            "Ride Booking Accepted",
            "Your ride booking has been accepted by the driver.",
            "Unread"
        )
    )

    # Reduce available seats
    cursor.execute(
        """
        UPDATE rides

        SET available_seats = available_seats - 1

        WHERE id=%s
        AND available_seats > 0
        """,
        (
            record["ride_id"],
        )
    )

    conn.commit()
    conn.close()

    flash("Booking accepted successfully.")

    return redirect("/driver-requests")


# =========================================================
# REJECT BOOKING
# =========================================================

@booking.route("/reject-booking/<int:booking_id>")
def reject_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            bookings.id,
            bookings.booking_status,
            bookings.ride_id,

            rides.driver_id

        FROM bookings

        INNER JOIN rides
        ON bookings.ride_id = rides.id

        WHERE bookings.id=%s
        """,
        (
            booking_id,
        )
    )

    record = cursor.fetchone()

    if not record:
        conn.close()
        flash("Booking request not found.")
        return redirect("/driver-requests")

    # Driver security check
    if record["driver_id"] != session["user_id"]:
        conn.close()
        flash("You are not authorized to manage this booking.")
        return redirect("/driver-requests")

    if record["booking_status"] == "Accepted":
        conn.close()
        flash("An accepted booking cannot be rejected.")
        return redirect("/driver-requests")

    if record["booking_status"] == "Rejected":
        conn.close()
        flash("This booking is already rejected.")
        return redirect("/driver-requests")

    # Reject booking
    cursor.execute(
        """
        UPDATE bookings

        SET booking_status='Rejected'

        WHERE id=%s
        """,
        (
            booking_id,
        )
    )
    
    
    # Get passenger email
    cursor.execute(
    """
    SELECT users.email
    FROM bookings
    INNER JOIN users
        ON bookings.passenger_id = users.id
    WHERE bookings.id=%s
    """,
    
    (
        booking_id,
    )
    )
    
    passenger = cursor.fetchone()

    if passenger:
        

        cursor.execute(
        """
        INSERT INTO notifications
        (
            email,
            title,
            message,
            status
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            passenger["email"],
            "Ride Booking Rejected",
            "Your ride booking request was rejected by the driver.",
            "Unread"
        )
        )

    conn.commit()
    conn.close()

    flash("Booking rejected.")
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