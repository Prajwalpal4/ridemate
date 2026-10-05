"""Loads demo accounts + upcoming rides so the project can be shown straight away.

Works on BOTH databases (SQLite locally, PostgreSQL when DATABASE_URL is set):

    python seed_demo.py

Safe to run more than once (existing accounts are left alone).
Demo password for every account: demo123
"""
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from database import create_database, get_connection
from helpers import IST

PASSWORD = "demo123"

USERS = [
    # full_name, student_id, email, role, vehicle
    ("Demo Driver One", "DEMO-D1", "driver1@demo.com", "Driver", "MH31AB1001"),
    ("Demo Driver Two", "DEMO-D2", "driver2@demo.com", "Driver", "MH31CD2002"),
    ("Demo Passenger One", "DEMO-P1", "passenger1@demo.com", "Passenger", None),
    ("Demo Passenger Two", "DEMO-P2", "passenger2@demo.com", "Passenger", None),
]

# (driver email, from, to, days from today, time, seats, vehicle)
RIDES = [
    ("driver1@demo.com", "G H Raisoni University", "Khapri Metro Station", 1, "08:30", 3, "MH31AB1001"),
    ("driver1@demo.com", "G H Raisoni University", "Nagpur Railway Station", 2, "17:15", 2, "MH31AB1001"),
    ("driver2@demo.com", "Wadi MIDC", "G H Raisoni University", 1, "09:00", 4, "MH31CD2002"),
    ("driver2@demo.com", "G H Raisoni University", "Sitabuldi", 3, "18:00", 1, "MH31CD2002"),
]


def main():
    create_database()
    conn = get_connection()
    cur = conn.cursor()
    pw = generate_password_hash(PASSWORD)

    for name, sid, email, role, vehicle in USERS:
        cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            continue
        cur.execute(
            """INSERT INTO users (full_name, student_id, email, department, year, role, password, vehicle_number)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (name, sid, email, "CSE", "4th Year", role, pw, vehicle),
        )
    conn.commit()

    today = datetime.now(IST)
    added = 0
    for email, frm, to, days, time_, seats, vehicle in RIDES:
        cur.execute("SELECT id, full_name FROM users WHERE email=%s", (email,))
        driver = cur.fetchone()
        date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT 1 FROM rides WHERE driver_id=%s AND from_location=%s AND to_location=%s AND ride_date=%s",
            (driver["id"], frm, to, date),
        )
        if cur.fetchone():
            continue
        cur.execute(
            """INSERT INTO rides (driver_id, driver_name, from_location, to_location, ride_date,
                                  ride_time, total_seats, available_seats, vehicle_number)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (driver["id"], driver["full_name"], frm, to, date, time_, seats, seats, vehicle),
        )
        added += 1
    conn.commit()
    conn.close()

    print(f"Done. {added} demo ride(s) added.")
    print(f"Demo logins (password '{PASSWORD}'): " + ", ".join(u[2] for u in USERS))


if __name__ == "__main__":
    main()
