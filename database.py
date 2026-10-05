import os
import sqlite3

# Production: set DATABASE_URL to a PostgreSQL connection string.
# Local development: if DATABASE_URL is not set, the original SQLite database is used.
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DATABASE = os.path.join(os.path.dirname(__file__), "database", "ridemate.db")


def is_postgres():
    return bool(DATABASE_URL)


class SQLiteCursorAdapter:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, params=None):
        sql = sql.replace("%s", "?")
        return self._cursor.execute(sql, params or ())

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self):
        return self._cursor.rowcount


class SQLiteConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorAdapter(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


class PostgresConnectionAdapter:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return self._conn.cursor(cursor_factory=RealDictCursor)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_connection():
    if is_postgres():
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return PostgresConnectionAdapter(conn)

    conn = sqlite3.connect(SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return SQLiteConnectionAdapter(conn)


INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_ride_passenger ON bookings(ride_id, passenger_id)",
    "CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings(passenger_id)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_email ON notifications(email)",
]


def create_database():
    conn = get_connection()

    if is_postgres():
        cursor = conn.cursor()
        schema = """
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            role TEXT NOT NULL,
            password TEXT NOT NULL,
            vehicle_number TEXT
        );

        CREATE TABLE IF NOT EXISTS rides(
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
        );

        CREATE TABLE IF NOT EXISTS bookings(
            id SERIAL PRIMARY KEY,
            ride_id INTEGER NOT NULL REFERENCES rides(id),
            passenger_id INTEGER NOT NULL REFERENCES users(id),
            booking_status TEXT DEFAULT 'Pending',
            booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notifications(
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Unread'
        );
        """
        cursor.execute(schema)
        procedures_path = os.path.join(os.path.dirname(__file__), "database", "procedures.sql")
        if os.path.exists(procedures_path):
            with open(procedures_path, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
        for stmt in INDEXES:
            cursor.execute(stmt)
        conn.commit()
        cursor.close()
        conn.close()
        return

    # SQLite local fallback
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
        password TEXT NOT NULL,
        vehicle_number TEXT
    )
    """)
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
    for stmt in INDEXES:
        cursor.execute(stmt)
    conn.commit()
    conn.close()
