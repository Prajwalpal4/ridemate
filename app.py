import os
from flask import Flask, session, jsonify
from routes.rides import rides
from database import create_database
from routes.booking import booking, get_pending_booking_count
from routes.auth import auth
from routes.dashboard import dashboard
from routes.notifications import notifications
from routes.profile import profile
from routes.tracking import tracking
from routes.ride_complete import ride_complete
from routes.charity import charity

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-this-secret-key")

create_database()

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(rides)
app.register_blueprint(booking)
app.register_blueprint(notifications)
app.register_blueprint(profile)
app.register_blueprint(tracking)
app.register_blueprint(ride_complete)
app.register_blueprint(charity)

@app.context_processor
def inject_pending_booking_count():

    count = 0

    if session.get("role") == "Driver" and session.get("user_id"):

        count = get_pending_booking_count(
            session["user_id"]
        )

    return {
        "pending_booking_count": count
    }


if __name__ == "__main__":
    app.run(debug=True)

@app.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "RideMate"})
