# RideMate - PostgreSQL + Ride Tracking

## Production stack
- Flask
- PostgreSQL (Supabase recommended)
- Gunicorn
- Leaflet + OpenStreetMap for map display
- Browser Geolocation for GPS

## Render
Build:
`pip install -r requirements.txt`

Start:
`gunicorn app:app`

Required environment variables:
- `DATABASE_URL` = Supabase PostgreSQL connection string
- `SECRET_KEY` = a long random secret

## Existing Supabase project
If the core RideMate tables already exist, run:
`database/migration_tracking_postgresql.sql`

If this is a new database, run:
`database/schema_postgresql.sql`

The Flask app also calls `create_database()` at startup, so missing tables are created automatically.

## Important
The current tracking page uses the browser's GPS and OpenStreetMap/Leaflet. It does not require a Google Maps API key.
