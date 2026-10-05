from flask import Blueprint, render_template, redirect, session
from database import get_connection

notifications = Blueprint("notifications", __name__)


# =========================================================
# NOTIFICATIONS
# =========================================================

@notifications.route("/notifications")
def view_notifications():

    if "user_email" not in session:
        return redirect("/login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            message,
            status
        FROM notifications
        WHERE email=%s
        ORDER BY id DESC
        """,
        (
            session["user_email"],
        )
    )

    notification_list = cursor.fetchall()

    # Mark notifications as read
    cursor.execute(
        """
        UPDATE notifications
        SET status='Read'
        WHERE email=%s
        """,
        (
            session["user_email"],
        )
    )

    conn.commit()
    conn.close()

    return render_template(
        "notifications.html",
        notifications=notification_list
    )