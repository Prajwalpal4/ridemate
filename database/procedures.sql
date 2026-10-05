-- RideMate stored routines for the final-year database requirement.
-- Run this after schema.sql.

CREATE OR REPLACE FUNCTION create_ride(
    p_driver_id INTEGER,
    p_driver_name TEXT,
    p_from_location TEXT,
    p_to_location TEXT,
    p_ride_date TEXT,
    p_ride_time TEXT,
    p_total_seats INTEGER,
    p_vehicle_number TEXT
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_id INTEGER;
BEGIN
    IF p_total_seats <= 0 THEN
        RAISE EXCEPTION 'Total seats must be greater than zero';
    END IF;

    INSERT INTO rides(
        driver_id, driver_name, from_location, to_location,
        ride_date, ride_time, total_seats, available_seats, vehicle_number
    ) VALUES (
        p_driver_id, p_driver_name, p_from_location, p_to_location,
        p_ride_date, p_ride_time, p_total_seats, p_total_seats, p_vehicle_number
    ) RETURNING id INTO new_id;

    RETURN new_id;
END;
$$;

CREATE OR REPLACE FUNCTION create_booking(
    p_ride_id INTEGER,
    p_passenger_id INTEGER
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_id INTEGER;
    ride_driver INTEGER;
    seats INTEGER;
BEGIN
    SELECT driver_id, available_seats
      INTO ride_driver, seats
      FROM rides
     WHERE id = p_ride_id
     FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Ride not found';
    END IF;

    IF ride_driver = p_passenger_id THEN
        RAISE EXCEPTION 'Driver cannot book own ride';
    END IF;

    IF seats <= 0 THEN
        RAISE EXCEPTION 'This ride is full';
    END IF;

    IF EXISTS (
        SELECT 1 FROM bookings
        WHERE ride_id = p_ride_id AND passenger_id = p_passenger_id
    ) THEN
        RAISE EXCEPTION 'Passenger already booked this ride';
    END IF;

    INSERT INTO bookings(ride_id, passenger_id, booking_status)
    VALUES(p_ride_id, p_passenger_id, 'Pending')
    RETURNING id INTO new_id;

    RETURN new_id;
END;
$$;

CREATE OR REPLACE PROCEDURE accept_booking(
    p_booking_id INTEGER,
    p_driver_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_ride_id INTEGER;
    v_passenger_id INTEGER;
    v_status TEXT;
    v_seats INTEGER;
    v_email TEXT;
BEGIN
    SELECT b.ride_id, b.passenger_id, b.booking_status, r.available_seats
      INTO v_ride_id, v_passenger_id, v_status, v_seats
      FROM bookings b
      JOIN rides r ON r.id = b.ride_id
     WHERE b.id = p_booking_id
       AND r.driver_id = p_driver_id
     FOR UPDATE OF b, r;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found or driver not authorized';
    END IF;

    IF v_status <> 'Pending' THEN
        RAISE EXCEPTION 'Only pending bookings can be accepted';
    END IF;

    IF v_seats <= 0 THEN
        RAISE EXCEPTION 'No seats are available';
    END IF;

    UPDATE bookings SET booking_status = 'Accepted' WHERE id = p_booking_id;
    UPDATE rides SET available_seats = available_seats - 1 WHERE id = v_ride_id;

    SELECT email INTO v_email FROM users WHERE id = v_passenger_id;
    IF v_email IS NOT NULL THEN
        INSERT INTO notifications(email, title, message, status)
        VALUES(v_email, 'Ride Booking Accepted',
               'Your ride booking has been accepted by the driver.', 'Unread');
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE reject_booking(
    p_booking_id INTEGER,
    p_driver_id INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_passenger_id INTEGER;
    v_status TEXT;
    v_email TEXT;
BEGIN
    SELECT b.passenger_id, b.booking_status
      INTO v_passenger_id, v_status
      FROM bookings b
      JOIN rides r ON r.id = b.ride_id
     WHERE b.id = p_booking_id
       AND r.driver_id = p_driver_id
     FOR UPDATE OF b;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking not found or driver not authorized';
    END IF;

    IF v_status <> 'Pending' THEN
        RAISE EXCEPTION 'Only pending bookings can be rejected';
    END IF;

    UPDATE bookings SET booking_status = 'Rejected' WHERE id = p_booking_id;

    SELECT email INTO v_email FROM users WHERE id = v_passenger_id;
    IF v_email IS NOT NULL THEN
        INSERT INTO notifications(email, title, message, status)
        VALUES(v_email, 'Ride Booking Rejected',
               'Your ride booking request was rejected by the driver.', 'Unread');
    END IF;
END;
$$;
