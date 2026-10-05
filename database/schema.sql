-- RideMate PostgreSQL schema
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

-- Indexes (also created automatically by the app on startup)
CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_ride_passenger ON bookings(ride_id, passenger_id);
CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id);
CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings(passenger_id);
CREATE INDEX IF NOT EXISTS idx_notifications_email ON notifications(email);
