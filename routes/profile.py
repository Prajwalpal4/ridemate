from flask import Blueprint, render_template, redirect, session, request, flash
from database import get_connection

profile = Blueprint("profile", __name__)


@profile.route("/profile", methods=["GET", "POST"])
def view_profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    # Update vehicle number
    if request.method == "POST":

        vehicle_number = request.form.get("vehicle_number", "").strip()

        cursor.execute(
            """
            UPDATE users
            SET vehicle_number=%s
            WHERE id=%s
            """,
            (
                vehicle_number,
                session["user_id"]
            )
        )

        conn.commit()

        # Update session if required
        session["vehicle_number"] = vehicle_number

        flash("Vehicle number updated successfully!")

    # Get current user
    cursor.execute(
        """
        SELECT
            id,
            full_name,
            email,
            department,
            role,
            vehicle_number
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    conn.close()

    if not user:
        return redirect("/login")

    return render_template(
        "profile.html",
        user=user
    )