from flask import Blueprint, render_template, redirect, session, request, flash
from database import get_connection

profile = Blueprint("profile", __name__)


@profile.route("/profile", methods=["GET", "POST"])
def view_profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()


    # =========================
    # UPDATE PROFILE
    # =========================

    if request.method == "POST":

        vehicle_number = request.form.get(
            "vehicle_number",
            ""
        ).strip()

        emergency_contact_name = request.form.get(
            "emergency_contact_name",
            ""
        ).strip()

        emergency_contact_phone = request.form.get(
            "emergency_contact_phone",
            ""
        ).strip()


        cursor.execute(
            """
            UPDATE users

            SET
                vehicle_number=%s,
                emergency_contact_name=%s,
                emergency_contact_phone=%s

            WHERE id=%s
            """,

            (
                vehicle_number,
                emergency_contact_name,
                emergency_contact_phone,
                session["user_id"]
            )
        )


        conn.commit()


        # Update session vehicle number
        session["vehicle_number"] = vehicle_number


        flash(
            "Profile updated successfully!"
        )


    # =========================
    # GET USER INFORMATION
    # =========================

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            email,
            department,
            role,
            vehicle_number,
            emergency_contact_name,
            emergency_contact_phone

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