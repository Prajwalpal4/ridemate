# What was fixed / added in this version

## Bugs fixed
- Home page "Find Ride" buttons pointed to a missing page (404) -> now go to /find-rides.
- Dashboard numbers (12 / 18 / 31 / 5) were typed in by hand -> now real counts from the database.
- Registration accepted two different passwords -> server now checks match, length (6+), email format, valid role.
- Offer Ride crashed (500 error) on bad seats; accepted 0 seats and past dates -> proper validation (1-8 seats, future date/time in IST).
- Cancelling a PENDING booking wrongly gave a seat back (could cause overbooking) -> seats return only for ACCEPTED bookings.
- Two quick "Accept" clicks could overbook a ride -> seat check and update are now one atomic step.
- Duplicate booking could slip through a double-click -> UNIQUE index (ride_id, passenger_id).

## Security
- Accept / reject / cancel / book were plain links (GET) -> now POST forms with CSRF protection on every form.
- Passengers could open driver pages -> drivers-only pages are enforced on the server and hidden from the menu.
- App now refuses to start on Render without SECRET_KEY; secure, HttpOnly, SameSite cookies.
- Login is case-insensitive for email; session is reset at login.

## New features
- Driver can cancel a ride (passengers are notified, their bookings closed).
- Drivers get a notification when someone requests a seat.
- Past rides disappear from Find Rides; rides are sorted by date/time.
- Friendly error page (404 / 400 / 500).
- /health endpoint (keeps Render + Supabase awake with a free uptime monitor).
- seed_demo.py to load demo accounts and rides on SQLite or PostgreSQL.

## Deployment
- render.yaml: single gunicorn worker, health check, Python version, auto-generated SECRET_KEY.
- DEPLOYMENT.md rewritten: use Supabase POOLER connection string (IPv4 safe).
