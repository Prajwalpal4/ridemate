import os

from flask import Flask, render_template, session

from database import create_database
from helpers import csrf_token, verify_csrf
from routes.auth import auth
from routes.booking import booking, get_pending_booking_count
from routes.dashboard import dashboard
from routes.notifications import notifications
from routes.profile import profile
from routes.rides import rides
from routes.tracking import tracking

app = Flask(__name__)

# On Render the RENDER env var is always set. In production a real SECRET_KEY is mandatory,
# otherwise anyone could forge login sessions.
IS_PRODUCTION = bool(os.getenv("RENDER"))
secret = os.getenv("SECRET_KEY")
if IS_PRODUCTION and not secret:
    raise RuntimeError("SECRET_KEY environment variable is required in production.")
app.secret_key = secret or "dev-secret-change-me"

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,   # cookie only over HTTPS when deployed
)

create_database()

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(rides)
app.register_blueprint(booking)
app.register_blueprint(notifications)
app.register_blueprint(profile)
app.register_blueprint(tracking)


@app.before_request
def _check_csrf():
    verify_csrf()


@app.context_processor
def inject_globals():
    count = 0
    if session.get("role") == "Driver" and session.get("user_id"):
        count = get_pending_booking_count(session["user_id"])
    return {"pending_booking_count": count, "csrf_token": csrf_token}


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404,
                           message="The page you are looking for does not exist."), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400,
                           message=getattr(e, "description", "Bad request.")), 400


@app.errorhandler(500)
def server_error(_e):
    return render_template("error.html", code=500,
                           message="Something went wrong on our side. Please try again."), 500


@app.route("/health")
def health():
    """Uptime-monitor endpoint. It runs a tiny query so that BOTH the free Render
    service and the free Supabase database count as 'active' and do not pause."""
    try:
        from database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        return "ok", 200
    except Exception:
        return "database unavailable", 503


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
