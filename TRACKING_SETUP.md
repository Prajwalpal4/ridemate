# RideMate Tracking

Tracking is integrated into the existing RideMate app.
- Passenger: My Bookings -> Track Ride -> sees the latest driver GPS location.
- Driver: Track Ride -> allow browser location; GPS updates are saved to ride_locations.
- Map uses Leaflet + OpenStreetMap and OSRM for route/ETA.
- Existing Supabase database only needs database/migration_tracking_postgresql.sql once.
