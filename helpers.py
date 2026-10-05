"""Small shared helpers: IST date handling, CSRF token, login/role guards."""
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import abort, flash, redirect, request, session

# India Standard Time. Render servers run in UTC, so "today" must be computed in IST,
# otherwise a ride posted late evening in India would be rejected as "past".
IST = timezone(timedelta(hours=5, minutes=30))


def today_ist():
    return datetime.now(IST).strftime("%Y-%m-%d")


def now_ist():
    return datetime.now(IST)


# ---------------------------------------------------------------- CSRF
def csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_hex(16)
        session["_csrf"] = token
    return token


def verify_csrf():
    """Call from before_request. Rejects any POST without the right token."""
    if request.method != "POST":
        return
    sent = request.form.get("csrf_token", "")
    expected = session.get("_csrf", "")
    if not expected or not hmac.compare_digest(sent, expected):
        abort(400, "Invalid or missing security token. Please go back, refresh the page and try again.")


# ---------------------------------------------------------------- guards
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped


def driver_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        if session.get("role") != "Driver":
            flash("Only registered drivers can use that page.")
            return redirect("/dashboard")
        return view(*args, **kwargs)
    return wrapped
