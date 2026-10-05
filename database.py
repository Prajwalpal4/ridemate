import os
import sqlite3

# RideMate supports PostgreSQL in production (Render/Supabase)
# and SQLite locally for easy development.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_DATABASE = os.getenv("SQLITE_DATABASE", "database/ridemate.db")


class CompatCursor:
    """Small compatibility wrapper so route files use PostgreSQL-style %s placeholders."""

    def __init__(self, cursor, postgres=False):
        self._cursor = cursor
        self.postgres = postgres

    def execute(self, sql, params=None):
        if not self.postgres:
            # Local SQLite uses ? placeholders.
            sql = sql.replace("%s", "?")
        if params is None:
            return self._cursor.execute(sql)
        return self._cursor.execute(sql, params)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class CompatConnection:
    def __init__(self, connection, postgres=False):
        self._connection = connection
        self.postgres = postgres

    def cursor(self):
        if self.postgres:
            from psycopg2.extras import RealDictCursor
            return CompatCursor(
                self._connection.cursor(cursor_factory=RealDictCursor),
                postgres=True
            )
        return CompatCursor(self._connection.cursor(), postgres=False)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _postgres_connection():
    import psycopg2

    # Supabase/Render may provide postgres://; psycopg2 accepts it,
    # but normalise it to postgresql:// for consistency.
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    return CompatConnection(
        psycopg2.connect(url),
        postgres=True
    )


def _sqlite_connection():
    conn = sqlite3.connect(SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    return CompatConnection(conn, postgres=False)


def get_connection():
    """Use PostgreSQL when DATABASE_URL is set; otherwise use local SQLite."""
    if DATABASE_URL:
        return _postgres_connection()
    return _sqlite_connection()


def _create_postgresql_database():
    conn = _postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            role TEXT NOT NULL,
            password TEXT NOT NULL,
            vehicle_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id SERIAL PRIMARY KEY,
            driver_id INTEGER NOT NULL REFERENCES users(id),
            driver_name TEXT NOT NULL,
            from_location TEXT NOT NULL,
            to_location TEXT NOT NULL,
            ride_date TEXT NOT NULL,
            ride_time TEXT NOT NULL,
            total_seats INTEGER NOT NULL,
            available_seats INTEGER NOT NULL,
            vehicle_number TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            ride_id INTEGER NOT NULL REFERENCES rides(id),
            passenger_id INTEGER NOT NULL REFERENCES users(id),
            booking_status TEXT DEFAULT 'Pending',
            booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Unread'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id SERIAL PRIMARY KEY,
            booking_id INTEGER UNIQUE NOT NULL REFERENCES bookings(id),
            ride_id INTEGER NOT NULL REFERENCES rides(id),
            passenger_id INTEGER NOT NULL REFERENCES users(id),
            driver_id INTEGER NOT NULL REFERENCES users(id),
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tracking / emergency location records.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_alerts (
            id SERIAL PRIMARY KEY,
            booking_id INTEGER NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            passenger_id INTEGER NOT NULL REFERENCES users(id),
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            message TEXT DEFAULT 'Emergency SOS',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Live driver location. One current record per booking.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ride_locations (
            id SERIAL PRIMARY KEY,
            booking_id INTEGER UNIQUE NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
            driver_id INTEGER NOT NULL REFERENCES users(id),
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            accuracy DOUBLE PRECISION,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_rides_driver_id
        ON rides(driver_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookings_ride_id
        ON bookings(ride_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookings_passenger_id
        ON bookings(passenger_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_email
        ON notifications(email)
    """)

    conn.commit()
    conn.close()


def _create_sqlite_database():
    conn = _sqlite_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        student_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL,
        role TEXT NOT NULL,
        password TEXT NOT NULL
    )
    """)

    for column, definition in (
        ("vehicle_number", "TEXT"),
        ("emergency_contact_name", "TEXT"),
        ("emergency_contact_phone", "TEXT"),
    ):
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rides(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        driver_name TEXT NOT NULL,
        from_location TEXT NOT NULL,
        to_location TEXT NOT NULL,
        ride_date TEXT NOT NULL,
        ride_time TEXT NOT NULL,
        total_seats INTEGER NOT NULL,
        available_seats INTEGER NOT NULL,
        vehicle_number TEXT NOT NULL,
        status TEXT DEFAULT 'Available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(driver_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ride_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        booking_status TEXT DEFAULT 'Pending',
        booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(ride_id) REFERENCES rides(id),
        FOREIGN KEY(passenger_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'Unread'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER UNIQUE NOT NULL,
        ride_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        driver_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(booking_id) REFERENCES bookings(id),
        FOREIGN KEY(ride_id) REFERENCES rides(id),
        FOREIGN KEY(passenger_id) REFERENCES users(id),
        FOREIGN KEY(driver_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emergency_alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        latitude REAL,
        longitude REAL,
        message TEXT DEFAULT 'Emergency SOS',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ride_locations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER UNIQUE NOT NULL,
        driver_id INTEGER NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        accuracy REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def create_database():
    """Create/migrate the application tables on startup."""
    if DATABASE_URL:
        _create_postgresql_database()
    else:
        _create_sqlite_database()
